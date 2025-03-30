import streamlit as st
import openai  # Ensure you have this package installed
from finder import *
from cahtbot import *
from settings import *

# Function for the intro page
def intro_page():
    with open('README.md', mode='r') as file:
        content = file.read()
        st.markdown(content)  # Render the content as Markdown

# Page mapping
pages = {
    "Introduction": intro_page,
    "Files": files_page,
    "Chatbot": chatbot_page,
    "Settings": settings_page
}

# Sidebar for navigation
st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(pages.keys()))

# Display the selected page
pages[selection]()

