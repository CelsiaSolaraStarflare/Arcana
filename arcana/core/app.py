import streamlit as st
import openai  # Ensure you have this package installed
import uuid
import socket
import nltk
import os

from arcana.pages.finder import files_page
from arcana.pages.chatbot import chatbot_page
from arcana.pages.settings import settings_page
from arcana.pages.mixup import mixup_page
from arcana.pages.longresponse import longresponse_page
from arcana.pages.editor import editor_page
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
    "Mixup": mixup_page,
    "Editor": editor_page,
    "Long Response": longresponse_page,
    "Settings": settings_page
}

# --- Main App Execution ---

# Initialize the application
initialize_app()

# Add analytics
add_google_analytics()

# Sidebar navigation
st.sidebar.title("Navigation")

# --- Page Selection Logic ---
# The page functions are defined in their respective files and imported.
# We use session state to keep track of the selected page across reruns.

# Define the pages
main_pages = ["Introduction", "Files", "Citations", "Chatbot"]
advanced_pages = ["Mixup", "Editor", "Long Response"]

# Display main page buttons
for page in main_pages:
    if st.sidebar.button(page, key=f"btn_{page}"):
        st.session_state.selected_page = page
        st.rerun()

# Display advanced tools in an expander
with st.sidebar.expander("Advanced Tools"):
    for page in advanced_pages:
        if st.button(page, key=f"btn_{page}"):
            st.session_state.selected_page = page
            st.rerun()

# Display settings button separately at the bottom
if st.sidebar.button("Settings", key="btn_settings"):
    st.session_state.selected_page = "Settings"
    st.rerun()

# Default to Introduction page if no page is selected
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Introduction"

# Display the selected page
pages[st.session_state.selected_page]()
