import streamlit as st
from response import openai_api_call
import difflib
from openai.types.chat import ChatCompletionMessageParam
from typing import List, Dict, Any

def editor_page():
    """
    A Streamlit page that provides an AI-powered document editor.
    Users can paste text, provide an editing instruction, and see a diff
    of the changes proposed by the AI.
    """
    st.title("✍️ AI Document Editor")
    st.write("Paste your text below, provide an editing instruction, and let the AI assist you.")
    
    # Initialize session state for editor variables
    if "editor_text" not in st.session_state:
        st.session_state.editor_text = "Paste your original text here to get started."
    if "edited_text" not in st.session_state:
        st.session_state.edited_text = ""
    if "diff_html" not in st.session_state:
        st.session_state.diff_html = ""

    # --- Main UI Layout ---
    
    col1, col2 = st.columns(2)
    
    # Column 1: Original Text Area
    with col1:
        st.subheader("Your Document")
        st.session_state.editor_text = st.text_area(
            "Original Text", 
            value=st.session_state.editor_text, 
            height=500,
            label_visibility="collapsed"
        )
        
    # Column 2: AI Controls and Edited Output
    with col2:
        st.subheader("AI Assistant")
        edit_prompt = st.text_input(
            "Editing Instruction", 
            placeholder="e.g., 'Fix spelling and grammar mistakes.'"
        )
        
        # Disable button if there's no text or no prompt
        is_disabled = not st.session_state.editor_text.strip() or not edit_prompt.strip()
        
        if st.button("🚀 Run AI Edit", type="primary", disabled=is_disabled):
            with st.spinner("AI is editing your document... Please wait."):
                # Construct messages for the API call with the correct type hint
                messages: List[ChatCompletionMessageParam] = [
                    {"role": "system", "content": "You are an expert editor. You will be given a piece of text and an instruction. Your task is to rewrite the text based *only* on the instruction. Return nothing but the fully rewritten text, without any introductory phrases like 'Here is the revised text.'"},
                    {"role": "user", "content": f"Instruction: {edit_prompt}\\n\\nText to edit:\\n---\\n{st.session_state.editor_text}"}
                ]
                
                # The API call returns a generator, so we iterate to get the full response
                try:
                    response_generator = openai_api_call(messages, "Normal") # type: ignore
                    full_response = "".join(list(response_generator))
                    st.session_state.edited_text = full_response
                    
                    # Generate and store the diff
                    diff = difflib.HtmlDiff(wrapcolumn=80).make_table(
                        st.session_state.editor_text.splitlines(),
                        full_response.splitlines(),
                        fromdesc='Original Text',
                        todesc='AI Edited Text'
                    )
                    st.session_state.diff_html = diff
                except Exception as e:
                    st.error(f"An error occurred during editing: {e}")
        
        if st.session_state.edited_text:
            st.info("Review the proposed changes below. You can accept them or modify the original text and try again.")
            if st.button("✅ Accept Changes"):
                st.session_state.editor_text = st.session_state.edited_text
                st.session_state.edited_text = ""
                st.session_state.diff_html = ""
                st.rerun()

    st.markdown("---")

    # --- Display Diff ---
    if st.session_state.diff_html:
        st.subheader("Proposed Changes (Diff View)")
        st.markdown(st.session_state.diff_html, unsafe_allow_html=True) 