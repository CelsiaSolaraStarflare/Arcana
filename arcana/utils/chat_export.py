from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from fpdf import FPDF

from arcana.utils import storage
from arcana.utils.auth import decrypt_json_from_file
from arcana.utils.response import openai_api_call


def _message_to_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        fragments: List[str] = []
        for part in content:
            if isinstance(part, dict):
                part_type = part.get("type")
                if part_type == "text":
                    fragments.append(part.get("text", ""))
                elif part_type in {"image_url", "input_image"}:
                    fragments.append("[image]")
            else:
                fragments.append(str(part))
        return " ".join(frag for frag in fragments if frag).strip()
    return str(content)


def _load_chat_file(path: Path, key: Optional[bytes]) -> Dict[str, object]:
    if path.suffix == ".enc" and key:
        return decrypt_json_from_file(path, key)
    return json.loads(path.read_text(encoding="utf-8"))


def load_chats_for_export() -> List[Dict[str, object]]:
    chat_dir = Path(storage.get_user_data_dir()) / "chat_histories"
    if not chat_dir.exists():
        return []
    key = storage.get_auth_key()
    chats: List[Dict[str, object]] = []
    for file_name in sorted(chat_dir.iterdir()):
        if file_name.suffix not in {".json", ".enc"}:
            continue
        if file_name.suffix == ".enc" and not key:
            continue
        if file_name.suffix == ".json" and key:
            continue
        try:
            chat_data = _load_chat_file(file_name, key)
            chat_data["__path"] = str(file_name)
            chats.append(chat_data)
        except Exception:
            continue
    return chats


def build_chat_summary(chats: Iterable[Dict[str, object]]) -> Tuple[str, str]:
    lines = []
    html_parts = [
        "<h2>Arcana Chat Archive</h2>",
        "<p>Summary of your recent chats:</p>",
        "<ul>",
    ]
    for chat in chats:
        name = chat.get("session_name") or "Untitled chat"
        tagline = chat.get("tagline") or ""
        timestamp = chat.get("timestamp") or "Unknown date"
        message_count = len(chat.get("messages", []))
        summary_text, keywords = generate_chat_insights(chat.get("messages", []))
        summary_line = f"- {name} ({timestamp}) — {message_count} messages"
        if summary_text:
            summary_line += f" — {summary_text}"
        if keywords:
            summary_line += f" — Keywords: {keywords}"
        lines.append(summary_line)
        html_parts.append(
            f"<li><strong>{name}</strong> ({timestamp}) — {message_count} messages"
            + (f" — {summary_text}" if summary_text else "")
            + (f" — Keywords: {keywords}" if keywords else "")
            + "</li>"
        )
    html_parts.append("</ul>")
    return "\n".join(lines), "\n".join(html_parts)


def generate_chat_insights(messages: Iterable[Dict[str, object]]) -> Tuple[str, str]:
    content = " ".join(
        _message_to_text(msg.get("content"))
        for msg in messages
        if msg.get("role") == "user"
    ).strip()
    if not content:
        return "", ""

    prompt = [
        {
            "role": "system",
            "content": (
                "You summarize chats. Respond in two lines:\n"
                "Summary: <one sentence>\n"
                "Keywords: <20 comma-separated keywords>\n"
                "No extra text."
            ),
        },
        {"role": "user", "content": content[:1200]},
    ]
    try:
        stream = openai_api_call(prompt, "Normal")
        response_text = "".join(chunk for chunk in stream).strip()
    except Exception:
        return "", ""

    summary = ""
    keywords = ""
    for line in response_text.splitlines():
        if line.lower().startswith("summary:"):
            summary = line.split(":", 1)[1].strip()
        elif line.lower().startswith("keywords:"):
            keywords = line.split(":", 1)[1].strip()
    if summary:
        summary = summary.rstrip(".")
    return summary, keywords


def build_chat_transcript_pdf(chats: Iterable[Dict[str, object]]) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, "Arcana Chat Archive")
    pdf.ln(2)

    max_width = pdf.w - pdf.l_margin - pdf.r_margin

    for chat in chats:
        name = chat.get("session_name") or "Untitled chat"
        timestamp = chat.get("timestamp") or "Unknown date"
        pdf.set_font("Helvetica", "B", 11)
        header = f"{name} ({timestamp})"
        pdf.multi_cell(0, 7, header.encode("latin-1", "ignore").decode("latin-1"))
        pdf.set_font("Helvetica", size=10)

        for message in chat.get("messages", []):
            role = message.get("role", "unknown").title()
            text = _message_to_text(message.get("content"))
            if not text:
                continue
            rendered = f"{role}: {text}"
            safe_text = rendered.encode("latin-1", "ignore").decode("latin-1")
            if pdf.get_string_width(safe_text) > max_width:
                pdf.multi_cell(0, 6, safe_text)
            else:
                pdf.cell(0, 6, safe_text, ln=1)
        pdf.ln(2)

    return bytes(pdf.output(dest="S"))
