from __future__ import annotations

import os
from typing import Optional

import requests
from dotenv import load_dotenv


RESEND_API_URL = "https://api.resend.com/emails"


def send_welcome_email(to_email: str) -> Optional[bool]:
    load_dotenv()
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key or not to_email:
        return None

    sender_email = os.environ.get("RESEND_FROM", "onboarding@standardcas.org")
    sender_name = os.environ.get("RESEND_FROM_NAME", "Indexademics Arcana Team")
    sender = f"{sender_name} <{sender_email}>"
    subject = "Welcome to Arcana — your workspace is ready"
    html_body = (
        "<div style='font-family: Arial, Helvetica, sans-serif; line-height: 1.6; color: #0f172a;'>"
        "<h2 style='margin-bottom: 0;'>Hi</h2>"
        "<p style='margin-top: 6px;'>Your Arcana workspace is ready. Below is a quick, detailed guide to get you started.</p>"
        "<h3 style='margin-bottom: 6px;'>What you can do right now</h3>"
        "<ul>"
        "<li><strong>Upload documents</strong> (PDF, DOCX, PPTX, CSV, TXT) and chat with them instantly.</li>"
        "<li><strong>Index your library</strong> so Arcana can retrieve snippets with citations.</li>"
        "<li><strong>Use assistant modes</strong> like Normal, Discrete, Math, and Reasoning for different tasks.</li>"
        "<li><strong>Enable web supplements</strong> (Brave) when you need current or external context.</li>"
        "<li><strong>Resume chats</strong> with auto‑saved history and quick taglines.</li>"
        "</ul>"
        "<h3 style='margin-bottom: 6px;'>Tips for best results</h3>"
        "<ul>"
        "<li>Ask specific questions and include keywords likely to appear in your documents.</li>"
        "<li>Upload source files before asking to ensure the chatbot prioritizes them.</li>"
        "<li>Use Discrete mode for a more explicit audit trail of which files were searched.</li>"
        "</ul>"
        "<h3 style='margin-bottom: 6px;'>Need help?</h3>"
        "<p>Reply to this email and we’ll help you get set up.</p>"
        "<p style='margin-top: 24px;'>— The Arcana Team</p>"
        "</div>"
    )

    try:
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": sender,
                "to": to_email,
                "subject": subject,
                "html": html_body,
            },
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception:
        return False
