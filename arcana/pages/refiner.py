import datetime
import json
from typing import Any, Dict, List

import streamlit as st

from arcana.utils.response import openai_api_call


def _ensure_refiner_state() -> None:
    """Initialize session state keys used by the grammar refiner page."""

    if "refiner_raw_text" not in st.session_state:
        st.session_state.refiner_raw_text = "Paste or draft your text here for grammar refinement."
    if "refiner_structured_issues" not in st.session_state:
        st.session_state.refiner_structured_issues: List[Dict[str, Any]] = []
    if "refiner_refined_drafts" not in st.session_state:
        st.session_state.refiner_refined_drafts: List[str] = []
    if "refiner_history" not in st.session_state:
        st.session_state.refiner_history: List[Dict[str, Any]] = []


def _parse_refiner_response(payload: str) -> Dict[str, Any]:
    """Parse the JSON payload returned by the language model."""

    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return {
            "issues": [
                {
                    "issue": "Unable to parse model response",
                    "details": payload.strip() or "The model returned an empty response.",
                }
            ],
            "refined_text": "",
        }

    issues = parsed.get("issues", [])
    if not isinstance(issues, list):
        issues = []

    refined_text = parsed.get("refined_text", "")
    if not isinstance(refined_text, str):
        refined_text = ""

    return {"issues": issues, "refined_text": refined_text}


def grammar_refiner_page() -> None:
    """Render the grammar refinement interface."""

    st.title("🪄 Grammar Refiner")
    st.write(
        "Highlight grammar issues, get structured feedback, and iterate on refined drafts without losing your history."
    )

    _ensure_refiner_state()

    tab_input, tab_issues, tab_history = st.tabs([
        "Draft Input",
        "Grammar Issues",
        "Refinement History",
    ])

    with tab_input:
        st.caption("Update your draft and run the grammar assistant to review improvements side-by-side.")
        col_draft, col_refined = st.columns([3, 2])

        with col_draft:
            st.session_state.refiner_raw_text = st.text_area(
                "Draft Text",
                value=st.session_state.refiner_raw_text,
                height=420,
                placeholder="Enter the passage you would like Arcana to refine.",
            )

        latest_refined = st.session_state.refiner_refined_drafts[0] if st.session_state.refiner_refined_drafts else ""
        with col_refined:
            st.text_area(
                "Latest Refined Draft",
                value=latest_refined,
                height=420,
                key="refiner_latest_preview",
                disabled=True,
            )

        focus_prompt = st.text_input(
            "Optional focus (tone, style, audience, etc.)",
            placeholder="e.g., 'Keep the tone formal and highlight sentence clarity.'",
        )

        col_actions = st.columns([1, 1, 1])
        run_disabled = not st.session_state.refiner_raw_text.strip()
        with col_actions[0]:
            if st.button("🚀 Analyze & Refine", type="primary", disabled=run_disabled):
                with st.spinner("Reviewing grammar and drafting improvements..."):
                    focus_suffix = (
                        f"\nFocus areas: {focus_prompt.strip()}" if focus_prompt and focus_prompt.strip() else ""
                    )
                    messages = [
                        {
                            "role": "system",
                            "content": (
                                "You are an expert copy editor. Analyse the provided text, identify grammar-related issues, "
                                "and provide a refined rewrite. Respond strictly in JSON with keys 'issues' (a list of objects "
                                "containing 'issue' and 'details') and 'refined_text' (the improved draft)."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                "Here is the text for review:\n" f"{st.session_state.refiner_raw_text}" f"{focus_suffix}"
                            ),
                        },
                    ]

                    try:
                        response_generator = openai_api_call(messages, "Normal")
                        response_payload = "".join(list(response_generator))
                        parsed = _parse_refiner_response(response_payload)

                        issues = parsed.get("issues", [])
                        refined_text = parsed.get("refined_text", "")

                        st.session_state.refiner_structured_issues = issues
                        if refined_text:
                            st.session_state.refiner_refined_drafts.insert(0, refined_text)
                            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            history_entry = {
                                "timestamp": timestamp,
                                "focus": focus_prompt,
                                "issues": issues,
                                "refined_text": refined_text,
                                "original_text": st.session_state.refiner_raw_text,
                            }
                            st.session_state.refiner_history.insert(0, history_entry)
                        st.success("Grammar review complete! Check the issues and refined draft tabs.")
                    except Exception as exc:
                        st.error(f"Unable to refine the text: {exc}")

        with col_actions[1]:
            if st.button("✅ Use Refined Draft", disabled=not latest_refined):
                st.session_state.refiner_raw_text = latest_refined
                st.success("Replaced your draft with the latest refined version.")
                st.rerun()

        with col_actions[2]:
            if st.button("🧹 Clear History"):
                st.session_state.refiner_structured_issues = []
                st.session_state.refiner_refined_drafts = []
                st.session_state.refiner_history = []
                st.session_state.refiner_raw_text = ""
                st.info("Cleared refiner state. Start with a fresh draft.")
                st.rerun()

    with tab_issues:
        st.subheader("Identified Grammar Issues")
        issues = st.session_state.refiner_structured_issues
        if not issues:
            st.info("Run the refiner to see grammar feedback here.")
        else:
            for idx, issue in enumerate(issues, start=1):
                with st.expander(f"Issue {idx}: {issue.get('issue', 'Details')}", expanded=False):
                    st.write(issue.get("details", "No additional information provided."))

    with tab_history:
        st.subheader("Refinement History")
        if not st.session_state.refiner_history:
            st.info("No refinements yet. Your history will appear after you run the assistant.")
        else:
            for entry in st.session_state.refiner_history:
                with st.expander(f"{entry['timestamp']} — {entry.get('focus') or 'General review'}"):
                    st.markdown("**Original Draft**")
                    st.write(entry.get("original_text", ""))
                    st.markdown("**Refined Draft**")
                    st.write(entry.get("refined_text", ""))
                    if entry.get("issues"):
                        st.markdown("**Issues Addressed**")
                        for idx, issue in enumerate(entry["issues"], start=1):
                            st.write(f"{idx}. {issue.get('issue', 'Issue')} - {issue.get('details', '')}")
