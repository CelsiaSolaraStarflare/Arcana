"""Streamlit widgets for managing reusable style guides."""

from __future__ import annotations

from typing import List

import streamlit as st

from arcana.utils.style_guides import (
    ensure_style_guide_dir,
    list_style_guides,
    load_style_guide,
    save_style_guide,
    save_uploaded_style_guide,
)


def render_style_guide_controls(
    *,
    selection_key: str = "active_style_guides",
    context_key: str = "global",
    expanded: bool = False,
) -> List[str]:
    """Render selection and management controls for style guides."""

    ensure_style_guide_dir()
    available = list_style_guides()

    current_selection: List[str] = st.session_state.get(selection_key, [])
    current_selection = [name for name in current_selection if name in available]
    st.session_state[selection_key] = current_selection

    upload_key = f"{context_key}_style_guide_upload"
    name_key = f"{context_key}_style_guide_name"
    content_key = f"{context_key}_style_guide_content"
    preview_key = f"{context_key}_style_guide_preview"
    save_key = f"{context_key}_style_guide_save"

    with st.expander("Style guides", expanded=expanded):
        st.caption(
            "Select one or more guides to enforce their rules. Upload existing files or author new guides below."
        )

        selected = st.multiselect(
            "Active style guides",
            options=available,
            default=current_selection,
            key=selection_key,
            help="Guides apply to both rewrite generation and quality checks.",
        )

        uploaded = st.file_uploader(
            "Upload guide (.txt or .md)",
            type=["txt", "md", "markdown"],
            key=upload_key,
        )
        if uploaded is not None:
            try:
                save_uploaded_style_guide(uploaded.name, uploaded.getvalue())
                st.success(f"Saved '{uploaded.name}' to the style guide library.")
                st.session_state.pop(upload_key, None)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

        name_value = st.text_input(
            "New guide name",
            value=st.session_state.get(name_key, ""),
            key=name_key,
            placeholder="e.g., Marketing voice",
        )
        content_value = st.text_area(
            "Guide rules",
            value=st.session_state.get(content_key, ""),
            key=content_key,
            height=150,
        )
        if st.button("Save style guide", key=save_key):
            try:
                save_style_guide(name_value, content_value)
            except ValueError as exc:  # Name or content validation failed
                st.error(str(exc))
            else:
                st.success(f"Saved style guide '{name_value}'.")
                st.session_state.pop(name_key, None)
                st.session_state.pop(content_key, None)
                st.rerun()

        if available:
            preview_options = ["(Select a guide)"] + available
            preview_choice = st.selectbox(
                "Preview a guide",
                options=preview_options,
                key=preview_key,
            )
            if preview_choice and preview_choice != "(Select a guide)":
                try:
                    st.code(load_style_guide(preview_choice), language="markdown")
                except FileNotFoundError:
                    st.warning("Selected style guide could not be loaded.")

        return selected
