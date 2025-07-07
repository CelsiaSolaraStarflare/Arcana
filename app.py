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

# Import the main application components
from arcana.core.app import initialize_app, add_google_analytics

# Initialize the application
initialize_app()

# Add analytics
add_google_analytics()

# Import page functions
from arcana.pages.finder import files_page
from arcana.pages.chatbot import chatbot_page
from arcana.pages.settings import settings_page
from arcana.pages.mixup import mixup_page
from arcana.pages.longresponse import longresponse_page
from arcana.pages.editor import editor_page

# Import configurations
from arcana.core.config import APP_TITLE, CACHE_DIR, INDEX_FILE
from arcana.utils.fiber import FiberDBMS

# --- Navigation Setup ---

# Sidebar navigation
st.sidebar.title("Navigation")

# --- Page Selection Logic ---
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
    """)
    
    # Show system information if requested
    if st.button("Show System Information"):
        import socket
        import uuid
        from arcana.core.app import get_mac_address, get_ip_address
        
        st.subheader("System Information")
        st.write(f"**IP Address:** {get_ip_address()}")
        st.write(f"**MAC Address:** {get_mac_address()}")
        st.write(f"**Session ID:** {str(uuid.uuid4())}")


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

# Default to Introduction page if no page is selected
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Introduction"

# Display the selected page
pages[st.session_state.selected_page]()