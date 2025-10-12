import datetime
from typing import Any, Dict, List

import streamlit as st
from openai.types.chat import ChatCompletionMessageParam

from arcana.utils.diff import generate_inline_diff_html, generate_version_diff_html
from arcana.utils.response import openai_api_call


def editor_page():
    """
    A Streamlit page that provides an AI-powered document editor.
    Users can paste text, provide an editing instruction, and see a diff
    of the changes proposed by the AI.
    """

    st.title("✍️ AI Document Editor")
    st.write("Paste your text below, provide an editing instruction, and let the Arcana AI assist you.")

    # Initialize session state for editor variables
    if "editor_text" not in st.session_state:
        st.session_state.editor_text = "Paste your original text here to get started."
    if "edited_text" not in st.session_state:
        st.session_state.edited_text = ""
    if "diff_html" not in st.session_state:
        st.session_state.diff_html = ""
    if "version_history" not in st.session_state:
        st.session_state.version_history = []
    if "pending_revert" not in st.session_state:
        st.session_state.pending_revert = None

    # --- History Tab ---
    with st.expander("📚 Version History", expanded=False):
        if st.session_state.version_history:
            st.write(f"**Total versions:** {len(st.session_state.version_history)}")

            for i, version in enumerate(reversed(st.session_state.version_history)):
                version_num = len(st.session_state.version_history) - i
                st.markdown(f"### Version {version_num}")
                st.caption(f"Created: {version['timestamp']} | Instruction: {version['instruction']}")

                # Generate diff between current text and this version
                diff_html = generate_version_diff_html(st.session_state.editor_text, version["text"])
                st.markdown(diff_html, unsafe_allow_html=True)

                # Revert button with confirmation
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button(f"⏪ Revert", key=f"revert_{version_num}"):
                        st.session_state.pending_revert = {
                            "version_num": version_num,
                            "text": version["text"],
                            "current_backup": st.session_state.editor_text,
                        }
                        st.rerun()

                st.markdown("---")
        else:
            st.info("No version history yet. Make some edits to see versions here!")

    # Handle revert confirmation
    if st.session_state.pending_revert:
        st.warning("⚠️ **Confirm Revert Action**")
        st.write(f"Are you sure you want to revert to Version {st.session_state.pending_revert['version_num']}?")
        st.info("💡 You will be able to revert back to your current version at any time.")

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✅ Yes, Revert", type="primary"):
                # Save current version before reverting
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                backup_version = {
                    "text": st.session_state.pending_revert["current_backup"],
                    "timestamp": current_time,
                    "instruction": f"Backup before reverting to Version {st.session_state.pending_revert['version_num']}",
                }
                st.session_state.version_history.append(backup_version)

                # Apply the revert
                st.session_state.editor_text = st.session_state.pending_revert["text"]
                st.session_state.pending_revert = None
                st.session_state.edited_text = ""
                st.session_state.diff_html = ""
                st.success(
                    "Changes applied to the document!"
                )
                st.rerun()
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.pending_revert = None
                st.rerun()

    # --- Main UI Layout ---

    col1, col2 = st.columns(2)

    # Column 1: Original Text Area
    with col1:
        st.subheader("Your Document")
        st.session_state.editor_text = st.text_area(
            "Original Text",
            value=st.session_state.editor_text,
            height=500,
            label_visibility="collapsed",
        )

    # Column 2: AI Controls and Edited Output
    with col2:
        st.subheader("AI Assistant")
        edit_prompt = st.text_input(
            "Editing Instruction",
            placeholder="e.g., 'Fix spelling and grammar mistakes.'",
        )

        # Disable button if there's no text or no prompt
        is_disabled = not st.session_state.editor_text.strip() or not edit_prompt.strip()

        if st.button("🚀 Run AI Edit", type="primary", disabled=is_disabled):
            with st.spinner("AI is editing your document... Please wait."):
                # Construct messages for the API call with the correct type hint
                messages: List[ChatCompletionMessageParam] = [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert editor. You will be given a piece of text and an instruction."
                            " Your task is to rewrite the text based *only* on the instruction. Return nothing but the"
                            " fully rewritten text, without any introductory phrases like 'Here is the revised text.'"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Instruction: {edit_prompt}\n\nText to edit:\n---\n{st.session_state.editor_text}"
                        ),
                    },
                ]

                # The API call returns a generator, so we iterate to get the full response
                try:
                    response_generator = openai_api_call(messages, "Normal")  # type: ignore[arg-type]
                    full_response = "".join(list(response_generator))
                    st.session_state.edited_text = full_response

                    # Generate and store the inline diff HTML
                    diff_html = generate_inline_diff_html(
                        st.session_state.editor_text, full_response
                    )
                    st.session_state.diff_html = diff_html
                except Exception as e:  # pylint: disable=broad-except
                    st.error(f"An error occurred during editing: {e}")

        if st.session_state.edited_text:
            st.info("Review the proposed changes below. Use the buttons at the bottom to apply or revert them.")

    st.markdown("---")

    # --- Display Diff ---
    if st.session_state.diff_html:
        st.subheader("Proposed Changes")
        st.markdown(st.session_state.diff_html, unsafe_allow_html=True)

        # --- Apply / Revert Controls ---
        col_apply, col_revert = st.columns([1, 1])
        with col_apply:
            if st.button("✅ Apply Changes"):
                # Save current version to history before applying changes
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                version_entry: Dict[str, Any] = {
                    "text": st.session_state.editor_text,
                    "timestamp": current_time,
                    "instruction": edit_prompt if "edit_prompt" in locals() else "Unknown instruction",
                }
                st.session_state.version_history.append(version_entry)

                # Apply the changes
                st.session_state.editor_text = st.session_state.edited_text
                st.session_state.edited_text = ""
                st.session_state.diff_html = ""
                st.success("Changes applied to the document!")
                st.rerun()
        with col_revert:
            if st.button("↩️ Revert Changes"):
                # Simply discard the proposed edits
                st.session_state.edited_text = ""
                st.session_state.diff_html = ""
                st.info("Proposed changes were discarded.")
                st.rerun()

