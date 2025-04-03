import streamlit as st
import openai  # Ensure you have this package installed
from finder import *
from chatbot import * 
from settings import *

import uuid

def get_mac_address():
    return ':'.join(f'{b:02x}' for b in uuid.getnode().to_bytes(6, 'big'))

# Intro page function
def intro_page():
    with open('README.md', mode='r') as file:
        content = file.read()
        st.markdown(content)
    
    if st.button("Show MAC Address"):
        st.write(f"MAC Address: {get_mac_address()}")

# Page mapping
pages = {
    "Introduction": intro_page,
    "Files": files_page,
    "Chatbot": chatbot_page,
    "Get MAC Address": get_mac_address()
}

# Main app logic
st.sidebar.title("Navigation")

# Button-based navigation
selected_page = None
for page_name in pages.keys():
    if st.sidebar.button(page_name):
        selected_page = page_name

# Display the selected page (default to first page if none selected)
if selected_page:
    pages[selected_page]()
else:
    intro_page()
