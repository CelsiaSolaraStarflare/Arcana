import streamlit as st
import openai  # Ensure you have this package installed
from finder import *
from chatbot import * 
from settings import *
from mixup import *
from longresponse import *

import uuid
import socket

def get_mac_address():
    return ':'.join(f'{b:02x}' for b in uuid.getnode().to_bytes(6, 'big'))

def get_ip_address():
    try:
        return socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        return "Unable to retrieve IP address"

# Intro page function
def intro_page():
    with open('README.md', mode='r') as file:
        content = file.read()
        st.markdown(content)
    
    if st.button("Show MAC & IP Address"):
        st.write(f"MAC Address: {get_mac_address()}")
        st.write(f"IP Address: {get_ip_address()}")


# Page mapping
pages = {
    "Introduction": intro_page,
    "Files": files_page,
    "Chatbot": chatbot_page,
    "Mixup": mixup_page,
    "Analysis": longresponse_page
}

# Ensure session state has a default value for 'selected_page'
if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = "Introduction"

# Sidebar navigation
st.sidebar.title("Navigation")
for page_name in pages.keys():
    if st.sidebar.button(page_name):
        st.session_state["selected_page"] = page_name

# Display the selected page
selected_page = st.session_state["selected_page"]
pages[selected_page]()
