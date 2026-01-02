#!/usr/bin/env python3
"""
Arcana Streamlit App
Refactored version with organized module structure
"""

import os
import sys
import streamlit as st

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.')

# Import only the essential functions we need from the refactored structure
from arcana.pages.finder import files_page
from arcana.pages.chatbot import chatbot_page
from arcana.pages.settings import settings_page
from arcana.pages.mixup import mixup_page
from arcana.pages.longresponse import longresponse_page
from arcana.pages.textual_refiner import textual_refiner_page

# Import configurations
from arcana.core.config import APP_TITLE, CACHE_DIR, INDEX_FILE
from arcana.utils.fiber import FiberDBMS
from arcana.utils.kai import KaiInstantDBMS, KaiThinkDBMS

DBMS_ALGORITHM = os.environ.get("ARCANA_DBMS_ALGO", "fiber").strip().lower()

# --- Application Setup ---

def initialize_app():
    """
    Sets up the application on its first run, including downloading necessary
    NLTK data, creating directories, and initializing the database.
    """
    import nltk
    
    # 1. Set page config
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide"
    )

    # 2. Download NLTK data if not present (basic version without caching)
    def download_nltk_data():
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download("punkt")
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download("stopwords")
        return True

    # Only download if not already done in session
    if 'nltk_data_downloaded' not in st.session_state:
        download_nltk_data()
        st.session_state.nltk_data_downloaded = True

    # 3. Ensure necessary directories exist
    os.makedirs(CACHE_DIR, exist_ok=True)

    # 4. Initialize or load the database into session state
    if 'dbms' not in st.session_state:
        if DBMS_ALGORITHM in {"kai-instant", "instant"}:
            dbms = KaiInstantDBMS()
            st.session_state.dbms_mode = "kai-instant"
        elif DBMS_ALGORITHM in {"kai-think", "think", "kai"}:
            dbms = KaiThinkDBMS()
            st.session_state.dbms_mode = "kai-think"
        else:
            dbms = FiberDBMS()
            st.session_state.dbms_mode = "fiber"
        if os.path.exists(INDEX_FILE):
            print(f"Loading existing database from {INDEX_FILE}...")
            dbms.load_from_file(INDEX_FILE)
        else:
            print("No existing database found. Initializing a new one.")
        st.session_state.dbms = dbms

    # 5. Initialize session state for page navigation and chat
    if "selected_page" not in st.session_state:
        st.session_state.selected_page = "Introduction"
    if "messages" not in st.session_state:
        st.session_state.messages = []

# Initialize the application
initialize_app()

# --- Navigation Setup ---

# Sidebar navigation
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background: #f8fafc;
        border-right: 1px solid rgba(15, 23, 42, 0.08);
    }
    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.35rem;
    }
    [data-testid="stSidebar"] .stRadio label {
        padding: 0.35rem 0.25rem;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("## Arcana")
st.sidebar.caption("Navigate")

primary_pages = ["Introduction", "Chatbot", "Settings"]
app_pages = ["Files", "Citations", "Textual Refiner", "Mixup", "Long Response"]
nav_icons = {
    "Introduction": "🏠",
    "Chatbot": "💬",
    "Files": "📁",
    "Citations": "🧾",
    "Textual Refiner": "✍️",
    "Mixup": "🧪",
    "Long Response": "🧵",
    "Settings": "⚙️",
}

def _format_nav_page(page: str) -> str:
    return f"{nav_icons.get(page, '•')} {page}"

def _set_page_from_primary() -> None:
    st.session_state.selected_page = st.session_state.primary_nav

def _set_page_from_apps() -> None:
    st.session_state.selected_page = st.session_state.apps_nav

primary_index = (
    primary_pages.index(st.session_state.selected_page)
    if st.session_state.selected_page in primary_pages
    else 0
)
st.sidebar.radio(
    "Primary",
    primary_pages,
    index=primary_index,
    format_func=_format_nav_page,
    label_visibility="collapsed",
    key="primary_nav",
    on_change=_set_page_from_primary,
)

with st.sidebar.expander("Apps", expanded=False):
    apps_index = (
        app_pages.index(st.session_state.selected_page)
        if st.session_state.selected_page in app_pages
        else 0
    )
    st.radio(
        "Apps",
        app_pages,
        index=apps_index,
        format_func=_format_nav_page,
        label_visibility="collapsed",
        key="apps_nav",
        on_change=_set_page_from_apps,
    )

# --- Page Functions ---

def intro_page():
    """
    Display the project README as the introduction page and optionally show
    system information.
    """
    with open("README.md", "r", encoding="utf-8") as f:
        st.markdown(f.read())

    if st.button("Show System Information", key="show_sys_info"):
        import socket
        import uuid

        def get_ip_address():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                return "127.0.0.1"

        def get_mac_address():
            return ':'.join([f'{(uuid.getnode() >> i) & 0xff:02x}' for i in range(0, 48, 8)][::-1])

        st.subheader("System Information")
        st.write(f"**IP Address:** {get_ip_address()}")
        st.write(f"**MAC Address:** {get_mac_address()}")
        st.write(f"**Session ID:** {str(uuid.uuid4())}")
        st.write(f"**Database Status:** {'Loaded' if os.path.exists(INDEX_FILE) else 'Empty'}")


def citations_page():
    """
    Render the project's citation information from the citations markdown file.
    """
    with open("citations.md", "r", encoding="utf-8") as f:
        st.markdown(f.read())

# Page mapping
pages = {
    "Introduction": intro_page,
    "Files": files_page,
    "Citations": citations_page,
    "Chatbot": chatbot_page,
    "Mixup": mixup_page,
    "Textual Refiner": textual_refiner_page,
    "Long Response": longresponse_page,
    "Settings": settings_page
}

# --- Main App Execution ---

# Display the selected page
pages[st.session_state.selected_page]()
