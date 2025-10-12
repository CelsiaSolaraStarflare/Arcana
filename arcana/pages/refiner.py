"""Interactive rewrite assistant page."""

from __future__ import annotations

import datetime
import re
import uuid
from typing import Any, Dict, List, Optional

import streamlit as st
from openai.types.chat import ChatCompletionMessageParam

from arcana.utils.diff import generate_inline_diff_html
from arcana.utils.response import openai_api_call


REWRITE_PRESETS: List[Dict[str, str]] = [
    {
        "key": "formal",
        "label": "Formalize grammar",
        "instruction": "Polish grammar, eliminate errors, and deliver the message with a professional tone.",
    },
    {
        "key": "shorten",
        "label": "Shorten",
        "instruction": "Condense the passage by removing redundancy while preserving the essential ideas.",
    },
    {
        "key": "expand",
        "label": "Expand",
        "instruction": "Elaborate on the core ideas with more detail and helpful transitions without changing the intent.",
    },
    {
        "key": "tone",
        "label": "Adjust tone",
        "instruction": "Rephrase the text with a friendly, approachable tone that still sounds confident and clear.",
    },
    {
        "key": "bulletize",
        "label": "Bulletize",
        "instruction": "Rewrite the content as a concise, well-structured bulleted list summarizing the main points.",
    },
]


def _ensure_refiner_state() -> None:
    """Initialize session state keys used by the rewrite refiner page."""

    if "refiner_raw_text" not in st.session_state:
        st.session_state.refiner_raw_text = "Paste or draft your text here for refinement."
    if "refiner_candidates" not in st.session_state:
        st.session_state.refiner_candidates: List[Dict[str, Any]] = []
    if "refiner_history" not in st.session_state:
        st.session_state.refiner_history: List[Dict[str, Any]] = []
    if "refiner_snippet_text" not in st.session_state:
        st.session_state.refiner_snippet_text = ""
    if "refiner_merge_text" not in st.session_state:
        st.session_state.refiner_merge_text = ""
    if "refiner_merge_origin" not in st.session_state:
        st.session_state.refiner_merge_origin = ""
    if "refiner_merge_sources" not in st.session_state:
        st.session_state.refiner_merge_sources: List[str] = []
    if "refiner_focus_prompt" not in st.session_state:
        st.session_state.refiner_focus_prompt = ""
    if "refiner_feedback" not in st.session_state:
        st.session_state.refiner_feedback = ""


def _get_preset(preset_key: str) -> Optional[Dict[str, str]]:
    for preset in REWRITE_PRESETS:
        if preset["key"] == preset_key:
            return preset
    return None


def _split_sentences(text: str) -> List[str]:
    stripped = text.strip()
    if not stripped:
        return []
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", stripped) if s.strip()]
    if not sentences:
        return [stripped]
    return sentences


def _append_history(source_text: str, rewritten_text: str, label: str, focus: str = "") -> None:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "label": label,
        "focus": focus,
        "source_text": source_text,
        "rewritten_text": rewritten_text,
    }
    st.session_state.refiner_history.insert(0, entry)


def _find_candidate(candidate_id: str) -> Optional[Dict[str, Any]]:
    for candidate in st.session_state.refiner_candidates:
        if candidate["id"] == candidate_id:
            return candidate
    return None


def _build_messages(source_text: str, preset: Dict[str, str], focus_prompt: str) -> List[ChatCompletionMessageParam]:
    focus_suffix = f"\nAdditional guidance: {focus_prompt.strip()}" if focus_prompt and focus_prompt.strip() else ""
    user_content = (
        "Rewrite the following text according to the goal. Provide only the rewritten passage without commentary."
        f"\n\nGoal: {preset['instruction']}{focus_suffix}\n\nText:\n{source_text}"
    )
    return [
        {
            "role": "system",
            "content": (
                "You are an expert writing assistant who rewrites content to match a requested style."
                " Respond only with the fully rewritten text."
            ),
        },
        {"role": "user", "content": user_content},
    ]


def _generate_rewrites(selected_keys: List[str], focus_prompt: str) -> None:
    source_text = st.session_state.refiner_raw_text
    st.session_state.refiner_candidates = []
    st.session_state.refiner_merge_origin = source_text
    st.session_state.refiner_merge_sources = []

    for preset_key in selected_keys:
        preset = _get_preset(preset_key)
        if not preset:
            continue

        container = st.container()
        container.markdown(f"#### {preset['label']} (generating…)")
        stream_placeholder = container.empty()

        try:
            messages = _build_messages(source_text, preset, focus_prompt)
            response_generator = openai_api_call(messages, "Normal")  # type: ignore[arg-type]
            collected_response = ""
            for chunk in response_generator:
                collected_response += chunk
                stream_placeholder.markdown(f"**{preset['label']}**\n\n{collected_response}")

            candidate_text = collected_response.strip()
            if candidate_text:
                candidate = {
                    "id": str(uuid.uuid4()),
                    "key": preset_key,
                    "label": preset["label"],
                    "text": candidate_text,
                    "source": source_text,
                    "focus": focus_prompt.strip(),
                    "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                st.session_state.refiner_candidates.append(candidate)
                stream_placeholder.markdown(f"**{preset['label']}**\n\n{candidate_text}")
            else:
                stream_placeholder.warning("The model did not return any rewritten text.")
        except Exception as exc:  # pylint: disable=broad-except
            stream_placeholder.error(f"Unable to generate rewrite: {exc}")


def _add_sentences_to_merge(candidate_id: str, selection_key: str) -> None:
    candidate = _find_candidate(candidate_id)
    if not candidate:
        return
    selected_sentences = st.session_state.get(selection_key, [])
    if not selected_sentences:
        return

    additions = "\n".join(selected_sentences)
    existing = st.session_state.refiner_merge_text.strip()
    st.session_state.refiner_merge_text = f"{existing}\n{additions}".strip() if existing else additions

    if not st.session_state.refiner_merge_origin:
        st.session_state.refiner_merge_origin = candidate["source"]
    if candidate["label"] not in st.session_state.refiner_merge_sources:
        st.session_state.refiner_merge_sources.append(candidate["label"])

    st.session_state[selection_key] = []


def _clear_merge_workspace() -> None:
    st.session_state.refiner_merge_text = ""
    st.session_state.refiner_merge_sources = []
    st.session_state.refiner_merge_origin = st.session_state.refiner_raw_text


def _finalize_merge() -> None:
    merged_text = st.session_state.refiner_merge_text.strip()
    if not merged_text:
        return

    source_text = st.session_state.refiner_merge_origin or st.session_state.refiner_raw_text
    sources = ", ".join(st.session_state.refiner_merge_sources)
    label = "Merged selection" if not sources else f"Merged selection ({sources})"

    _append_history(source_text, merged_text, label)
    st.session_state.refiner_raw_text = merged_text
    st.session_state.refiner_feedback = "Merged rewrite applied to the draft."
    _clear_merge_workspace()
    st.rerun()


def _accept_candidate(candidate_id: str) -> None:
    candidate = _find_candidate(candidate_id)
    if not candidate:
        return

    _append_history(candidate["source"], candidate["text"], candidate["label"], candidate.get("focus", ""))
    st.session_state.refiner_raw_text = candidate["text"]
    st.session_state.refiner_feedback = f"Applied {candidate['label']} rewrite to the draft."
    _clear_merge_workspace()
    st.rerun()


def grammar_refiner_page() -> None:
    """Render the rewrite refiner interface."""

    st.title("🪄 Rewrite Refiner")
    st.write(
        "Generate multiple rewrite candidates, review diffs beside your draft, and build custom merges before saving them"
        " to your session history."
    )

    _ensure_refiner_state()

    if st.session_state.refiner_feedback:
        st.success(st.session_state.refiner_feedback)
        st.session_state.refiner_feedback = ""

    if not st.session_state.refiner_merge_text:
        st.session_state.refiner_merge_origin = st.session_state.refiner_raw_text

    tab_studio, tab_history = st.tabs(["Rewrite studio", "History"])

    with tab_studio:
        col_main, col_side = st.columns([3, 2])

        with col_main:
            st.session_state.refiner_raw_text = st.text_area(
                "Draft text",
                value=st.session_state.refiner_raw_text,
                height=360,
                placeholder="Enter the passage you would like Arcana to refine.",
            )

            st.session_state.refiner_focus_prompt = st.text_input(
                "Optional context (tone, audience, key details)",
                value=st.session_state.refiner_focus_prompt,
                placeholder="e.g., 'Aim for a confident but friendly voice.'",
            )

            preset_options = [preset["key"] for preset in REWRITE_PRESETS]
            selected_keys = st.multiselect(
                "Select rewrite styles",
                options=preset_options,
                format_func=lambda key: _get_preset(key)["label"] if _get_preset(key) else key,
                help="Choose one or more presets to generate multiple candidates at once.",
            )

            run_disabled = not st.session_state.refiner_raw_text.strip() or not selected_keys
            if st.button("🚀 Generate rewrites", type="primary", disabled=run_disabled):
                with st.spinner("Streaming rewrites from Arcana…"):
                    _generate_rewrites(selected_keys, st.session_state.refiner_focus_prompt)

        with col_side:
            st.subheader("Snippet clipboard")
            st.caption("Collect snippets from candidates or jot down your own notes to copy later.")
            st.text_area(
                "Snippet clipboard",
                key="refiner_snippet_text",
                height=150,
            )

            st.subheader("Merge workspace")
            if st.session_state.refiner_merge_sources:
                st.caption(
                    "Sources: " + ", ".join(dict.fromkeys(st.session_state.refiner_merge_sources))
                )
            st.text_area(
                "Merge workspace",
                key="refiner_merge_text",
                height=210,
                help="Add sentences from candidates or type custom edits, then finalize the merge.",
            )

            merge_cols = st.columns(2)
            with merge_cols[0]:
                st.button(
                    "✅ Finalize merge",
                    key="finalize_merge_button",
                    disabled=not st.session_state.refiner_merge_text.strip(),
                    on_click=_finalize_merge,
                )
            with merge_cols[1]:
                st.button("🧹 Clear merge", on_click=_clear_merge_workspace)

        st.markdown("---")

        st.subheader("Candidate rewrites")
        if not st.session_state.refiner_candidates:
            st.info("Select a rewrite style and generate suggestions to compare against your draft.")
        else:
            for candidate in st.session_state.refiner_candidates:
                preset = _get_preset(candidate["key"])
                with st.container():
                    st.markdown(f"#### {candidate['label']}")
                    if preset:
                        st.caption(preset["instruction"])
                    if candidate.get("focus"):
                        st.caption(f"Focus: {candidate['focus']}")
                    st.markdown(
                        generate_inline_diff_html(candidate["source"], candidate["text"]),
                        unsafe_allow_html=True,
                    )
                    st.text_area(
                        "Candidate text",
                        value=candidate["text"],
                        key=f"candidate_text_{candidate['id']}",
                        height=220,
                    )

                    sentences = _split_sentences(candidate["text"])
                    selection_key = f"merge_select_{candidate['id']}"
                    if sentences:
                        st.multiselect(
                            "Select sentences to add to the merge workspace",
                            options=sentences,
                            key=selection_key,
                        )

                    action_cols = st.columns(3)
                    with action_cols[0]:
                        st.button(
                            "✅ Accept rewrite",
                            key=f"accept_{candidate['id']}",
                            on_click=_accept_candidate,
                            args=(candidate["id"],),
                        )
                    with action_cols[1]:
                        if st.button(
                            "📋 To clipboard",
                            key=f"snippet_{candidate['id']}",
                        ):
                            st.session_state.refiner_snippet_text = candidate["text"]
                            st.session_state.refiner_feedback = "Rewrite copied to the snippet clipboard."
                            st.rerun()
                    with action_cols[2]:
                        if sentences and st.button(
                            "➕ Add to merge",
                            key=f"merge_{candidate['id']}",
                        ):
                            _add_sentences_to_merge(candidate["id"], selection_key)
                            st.session_state.refiner_feedback = "Selected sentences added to the merge workspace."
                            st.rerun()

    with tab_history:
        st.subheader("Accepted rewrites")
        if not st.session_state.refiner_history:
            st.info("Accept a rewrite or finalize a merge to build your history.")
        else:
            for entry in st.session_state.refiner_history:
                title = f"{entry['timestamp']} — {entry['label']}"
                with st.expander(title, expanded=False):
                    if entry.get("focus"):
                        st.caption(f"Focus: {entry['focus']}")
                    st.markdown("**Diff vs. original**")
                    st.markdown(
                        generate_inline_diff_html(entry["source_text"], entry["rewritten_text"]),
                        unsafe_allow_html=True,
                    )
                    st.markdown("**Rewritten text**")
                    st.write(entry["rewritten_text"])
                    st.markdown("**Original text**")
                    st.write(entry["source_text"])

