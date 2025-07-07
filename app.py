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
from arcana.pages.editor import editor_page

# Import configurations
from arcana.core.config import APP_TITLE, CACHE_DIR, INDEX_FILE
from arcana.utils.fiber import FiberDBMS

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
    if "messages" not in st.session_state:
        st.session_state.messages = []

# Initialize the application
initialize_app()

# --- Navigation Setup ---

# Sidebar navigation
st.sidebar.title("Navigation")

# --- Page Selection Logic ---
# Define the pages
main_pages = ["Introduction", "Files", "Citations", "Chatbot"]
advanced_pages = ["Mixup", "Editor", "Long Response"]

# Display main page buttons
for page in main_pages:
    if st.sidebar.button(page, key=f"main_btn_{page}"):
        st.session_state.selected_page = page
        st.rerun()

# Display advanced tools in an expander
with st.sidebar.expander("Advanced Tools"):
    for page in advanced_pages:
        if st.button(page, key=f"adv_btn_{page}"):
            st.session_state.selected_page = page
            st.rerun()

# Display settings button separately at the bottom
if st.sidebar.button("Settings", key="settings_btn"):
    st.session_state.selected_page = "Settings"
    st.rerun()

# --- Page Functions ---

def intro_page():
    """
    Introduction/Welcome page with system information and overview.
    """
    st.title(f"Welcome to {APP_TITLE}")
    st.markdown("""
    ## 🌟 Your AI-Powered Assistant
    
    Arcana is your intelligent assistant for creating documents, presentations, 
    and study materials. Upload files, build a knowledge base, and interact 
    with your data through our advanced AI chatbot.
    
    ### 🚀 Getting Started
    1. **Files**: Upload and organize your documents
    2. **Chatbot**: Ask questions and get AI-powered responses
    3. **Mixup**: Generate presentations and study guides
    4. **Editor**: AI-assisted document editing
    
    ### 🔧 Advanced Features
    - **Long Response**: Deep analysis of lengthy documents
    - **Citations**: Manage your academic references
    - **Multiple Languages**: Interface available in several languages
    
    ### 📊 System Status
    """)
    
    # Show system information if requested
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
            import uuid
            return ':'.join([f'{(uuid.getnode() >> i) & 0xff:02x}' for i in range(0, 48, 8)][::-1])
        
        st.subheader("System Information")
        st.write(f"**IP Address:** {get_ip_address()}")
        st.write(f"**MAC Address:** {get_mac_address()}")
        st.write(f"**Session ID:** {str(uuid.uuid4())}")
        st.write(f"**Database Status:** {'Loaded' if os.path.exists(INDEX_FILE) else 'Empty'}")


def citations_page():
    """
    Citations page for managing academic references.
    """
    st.title("📚 Academic & Resource Citations")
    st.markdown("""
    ## How to Cite Arcana
    
    ### For Academic Papers:
    ```
    Arcana AI Assistant. (2024). Arcana: AI-Powered Document Processing System. 
    Version 1.0.0. Retrieved from https://github.com/CelsiaSolaraStarflare/Arcana
    ```
    
    ### For Presentations:
    ```
    Arcana AI Assistant (2024). Arcana v1.0.0. 
    AI-powered document processing and chatbot system.
    ```
    
    ### Development Team:
    - **Osmond G11**: Base algorithm coding, DBMS designing, API functions
    - **Celsia G11**: UI Coding and platform conditioning  
    - **Brian G10**: Debugging and mirroring platform
    - **Pete G10**: Database arrangement and testing
    
    ### Technologies Used:
    - **Streamlit**: Web application framework
    - **OpenAI API**: AI language models
    - **NLTK**: Natural language processing
    - **Python**: Core programming language
    
    ### License Information:
    This project is licensed under CC-BY-ND-SA by Indexademics.
    - ❌ No derivatives
    - ❌ No unauthorized redistribution  
    - ✅ Attribution required
    - ✅ Sharing with proper credit allowed
    """)

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

# Display the selected page
pages[st.session_state.selected_page]()