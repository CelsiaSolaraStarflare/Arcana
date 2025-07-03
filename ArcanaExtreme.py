import streamlit as st
import openai  # Ensure you have this package installed
import uuid
import socket
import nltk
import os
import time
from dotenv import load_dotenv

from finder import files_page
from chatbot import chatbot_page
from settings import settings_page
from mixup import mixup_page
from longresponse import longresponse_page
from editor import editor_page
from speech_to_text import speech_to_text_page
from config import APP_TITLE, CACHE_DIR, INDEX_FILE
from fiber import FiberDBMS
from theme import apply_theme

# --- Application Setup ---

def initialize_app():
    """
    Sets up the application on its first run, including downloading necessary
    NLTK data, creating directories, and initializing the database.
    """
    # 1. Load environment variables from .env file
    load_dotenv()

    # 2. Set page config
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide"
    )

    # 2. Initialize theme
    if "theme" not in st.session_state:
        st.session_state.theme = "Light"

    # 3. Download NLTK data if not present
    @st.cache_resource
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

    download_nltk_data()

    # 4. Ensure necessary directories exist
    os.makedirs(CACHE_DIR, exist_ok=True)

    # 4b. Build initial index if it does not exist yet
    if not os.path.exists(INDEX_FILE):
        from indexing import indexing as build_index  # local import to avoid circular
        with st.spinner("First-time setup: building document index… this may take a while"):
            build_index(CACHE_DIR)
            st.success("Initial indexing complete!")

    # 5. Initialize or load the database into session state
    if 'dbms' not in st.session_state:
        dbms = FiberDBMS()
        if os.path.exists(INDEX_FILE):
            print(f"Loading existing database from {INDEX_FILE}...")
            dbms.load_from_file(INDEX_FILE)
        else:
            print("No existing database found. Initializing a new one.")
        st.session_state.dbms = dbms

    # 6. Initialize session state for page navigation and chat
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
    with open('README.md', 'r', encoding='utf-8') as file:
        st.markdown(file.read())
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
    "Speech to Text": speech_to_text_page,
    "Mixup": mixup_page,
    "Editor": editor_page,
    "Long Response": longresponse_page,
    "Settings": settings_page
}

# --- Main App Execution ---

# Initialize the application
initialize_app()

# Apply theme. This needs to be defined in settings.py
apply_theme()

# Add analytics
add_google_analytics()

# ------------------- Boot Animation -------------------

# Show boot animation once per session
def show_boot_animation():
    """Displays a simple fade-out Arcana logo splash screen."""
    boot_css = """
    <style>
    #arcana-boot-overlay{
        position:fixed;
        inset:0;
        background:#111;
        display:flex;
        align-items:center;
        justify-content:center;
        z-index:9999;
        animation:bootFade 1.2s ease 1.8s forwards;
    }
    @keyframes bootFade{to{opacity:0;visibility:hidden;}}
    #arcana-boot-logo{
        font-size:64px;
        font-weight:700;
        color:#ffffff;
        font-family: 'Trebuchet MS', sans-serif;
        animation:popIn 1.8s ease;
    }
    @keyframes popIn{
        0%{opacity:0;transform:scale(0.3);}
        60%{opacity:1;transform:scale(1.1);}
        100%{opacity:1;transform:scale(1);}    
    }
    </style>
    <div id='arcana-boot-overlay'><div id='arcana-boot-logo'>Arcana Extreme</div></div>
    """
    st.markdown(boot_css, unsafe_allow_html=True)

# Display boot screen on first run
if not st.session_state.get("boot_shown", False):
    show_boot_animation()
    time.sleep(2.0)
    st.session_state.boot_shown = True
    st.rerun()

# ------------------- Page Transition Fade-In -------------------


# Icon (emoji) for each page
page_icons = {
    "Introduction": "🏠",
    "Files": "📂",
    "Citations": "📚",
    "Chatbot": "💬",
    "Speech to Text": "🎙️",
    "Mixup": "🔀",
    "Editor": "📝",
    "Long Response": "🗒️",
    "Settings": "⚙️",
}

# A simple color palette for the icon borders / background
page_colors = {
    "Introduction": "#ff6b6b",   # red-ish
    "Files": "#ffa94d",          # orange
    "Citations": "#ffd43b",      # yellow
    "Chatbot": "#69db7c",        # green
    "Speech to Text": "#38d9a9", # teal
    "Mixup": "#4dabf7",          # blue
    "Editor": "#9775fa",         # purple
    "Long Response": "#e599f7",   # violet
    "Settings": "#868e96",        # gray
}

# Helper to render the icon grid and handle navigation
def render_icon_navigation():
    st.markdown("## Arcana Extreme")

    # ---------- Dynamic CSS for colored icon buttons ----------
    base_css = """
        /* Make the button look like an app icon */
        div[data-testid="stButton"] button {
            height: 90px;
            width: 90px;
            border-radius: 20px;
            font-size: 40px; /* bigger emoji */
            padding: 0;
            background-color: transparent; /* contour style */
            border: 2px solid #cccccc;
            display: block;
            margin: 0; /* align left */
        }
        /* Remove default focus outline for cleaner look */
        div[data-testid="stButton"] button:focus {
            outline: none;
            box-shadow: none;
        }
        /* Center the emoji inside */
        div[data-testid="stButton"] button p {
            margin: 0;
            line-height: 90px;
        }
    """

    per_button_css = "\n".join(
        f"div[key='icon_{page}'] button {{ border-color: {color}; color: {color}; }}" for page, color in page_colors.items()
    )

    st.markdown(f"<style>{base_css}{per_button_css}</style>", unsafe_allow_html=True)

    icons_per_row = 4  # Adjust to change number of icons per row
    pages_list = list(page_icons.keys())

    # Break pages into rows
    rows = [pages_list[i : i + icons_per_row] for i in range(0, len(pages_list), icons_per_row)]

    for row in rows:
        cols = st.columns(icons_per_row)
        for idx, page_name in enumerate(row):
            with cols[idx]:
                if st.button(page_icons[page_name], key=f"icon_{page_name}"):
                    st.session_state.selected_page = page_name
                    st.session_state.show_icon_menu = False  # hide menu
                    st.rerun()

                # Tagline label underneath the icon
                st.markdown(
                    f"<div style='width:90px;margin:6px 0 0 0;text-align:left;font-size:14px;color:{page_colors[page_name]} !important;font-weight:600;'>{page_name}</div>",
                    unsafe_allow_html=True,
                )

# Ensure we have a selected page in session state
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Introduction"

# ------------------- Page / Menu display logic -------------------

# Initialize flag controlling whether menu is shown
if "show_icon_menu" not in st.session_state:
    st.session_state.show_icon_menu = True

if st.session_state.show_icon_menu:
    # Show icon grid menu
    render_icon_navigation()
else:
    # Show back button (upper left)
    back_col, _ = st.columns([1, 9])
    with back_col:
        if st.button("← Menu", key="btn_back_to_menu"):
            st.session_state.show_icon_menu = True
            st.rerun()

    # Render the selected page content
    pages[st.session_state.selected_page]()
