import streamlit as st
import openai  # Ensure you have this package installed
from finder import *
from chatbot import * 
from settings import *





# Intro page function
def intro_page():
    with open('README.md', mode='r') as file:
        content = file.read()
        st.markdown(content)

# Page mapping
pages = {
    "Introduction": intro_page,
    "Files": files_page,
    "Chatbot": chatbot_page
}

# Main app logic
st.sidebar.title("Navigation")

selection = st.sidebar.radio("Go to", list(pages.keys()))
 
# Display the selected page
pages[selection]()

