import streamlit as st
import openai  # Ensure you have this package installed
import uuid
import socket
import nltk
import os
from arcana.utils.nltk_setup import ensure_nltk_data

from arcana.pages.finder import files_page
from arcana.pages.chatbot import chatbot_page
from arcana.pages.settings import settings_page
from arcana.pages.mixup import mixup_page
from arcana.pages.longresponse import longresponse_page
from arcana.pages.textual_refiner import textual_refiner_page
from arcana.core.config import APP_TITLE, CACHE_DIR, INDEX_FILE
from arcana.utils.fiber import FiberDBMS

# --- Application Setup ---

def initialize_app():
    """
    Sets up the application on its first run, including downloading necessary
    NLTK data, creating directories, and initializing the database.
    """
    # 1. Set page config
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide"
    )

    # 2. Download NLTK data if not present (uses a writable data dir)
    if 'nltk_data_downloaded' not in st.session_state:
        ensure_nltk_data()
        st.session_state.nltk_data_downloaded = True

    # 3. Ensure necessary directories exist
    os.makedirs(CACHE_DIR, exist_ok=True)

    # 4. Initialize or load the database into session state
    if 'dbms' not in st.session_state:
        dbms = FiberDBMS()
        if os.path.exists(INDEX_FILE):
            print(f"Loading existing database from {INDEX_FILE}...")
            dbms.load_from_file(INDEX_FILE)
        else:
            print("No existing database found. Initializing a new one.")
        st.session_state.dbms = dbms

    # 5. Initialize session state for page navigation and chat
    if "selected_page" not in st.session_state:
        st.session_state.selected_page = "Introduction"

# Inject Google Analytics gtag.js
def add_google_analytics():
    google_analytics_code = """
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-95R15DPBEG"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-95R15DPBEG');
    </script>
    """
    st.markdown(google_analytics_code, unsafe_allow_html=True)

def get_mac_address():
    return ':'.join(f'{b:02x}' for b in uuid.getnode().to_bytes(6, 'big'))

def get_ip_address():
    try:
        return socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        return "Unable to retrieve IP address"

# Intro page function
def intro_page():
    from pathlib import Path
    import streamlit.components.v1 as components

    intro_path = Path(__file__).resolve().parents[1] / "pages" / "intro.html"
    try:
        html = intro_path.read_text(encoding="utf-8")
    except OSError:
        html = "<p>Intro page unavailable.</p>"
    components.html(html, height=2200, scrolling=False)
    if st.button("Show MAC & IP Address"):
        st.write(f"MAC Address: {get_mac_address()}")
        st.write(f"IP Address: {get_ip_address()}")

def citations_page():
    with open('citations.md', 'r', encoding='utf-8') as file:
        st.markdown(file.read())

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

# Initialize the application
initialize_app()

# Add analytics
add_google_analytics()

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

# Default to Introduction page if no page is selected
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Introduction"

# Display the selected page
pages[st.session_state.selected_page]()
