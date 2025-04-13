import streamlit as st
import openai  # Ensure you have this package installed
from finder import *
from chatbot import * 
from settings import *
from mixup import *
from longresponse import *

import uuid
import socket

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

# Now call this function at the start of your Streamlit app
add_google_analytics()
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
        with open('rt.arcana',mode'r') as file2:
            times = file.read()
        st.markdown("Arcana has resolved "+times+" issues since launch!")
        st.markdown(content)
    
    if st.button("Show MAC & IP Address"):
        st.write(f"MAC Address: {get_mac_address()}")
        st.write(f"IP Address: {get_ip_address()}")
        
def citations_page():
    with open('citations.md', mode='r') as file:
        content = file.read()
        st.markdown(content)

# Page mapping
pages = {
    "Introduction": intro_page,
    "Files": files_page,
    "Citations": citations_page, 
    "Chatbot": chatbot_page,
    "Mixup": mixup_page
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
