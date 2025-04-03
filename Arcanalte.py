import streamlit as st
import openai  # Ensure you have this package installed
from finder import *
from chatbot import * 
from settings import *

# Mock database for simplicity
users_db = {
    "admin": "password123"
}

# Sign-up function
def sign_up():
    st.title("Sign-Up")
    username = st.text_input("Enter a username")
    email = st.text_input("Enter an Email(You will not be asked to authenticate")
    password = st.text_input("Enter a password", type="password")
    confirm_password = st.text_input("Confirm password", type="password")
    if st.button("Sign Up"):
        if username in users_db and users_db[username] == password:
            login(username, password)
        if username in users_db:
            st.error("Username already exists! Please choose another.")
        elif password != confirm_password:
            st.error("Passwords do not match!")
        else:
            users_db[username] = password
            st.success("Sign-up successful! Please log in.")

# Login function
def login(user, passwords):
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if user or passwords:
        username = user
        password = passwords
        
    if st.button("Login"):
        if username in users_db and users_db[username] == password:
            st.success(f"Welcome back, {username}!")
            return True
        else:
            st.error("Invalid username or password.")
    return False

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
auth = st.sidebar.radio("Authentication", ["Sign Up", "Login", "App"])
if auth == "Sign Up":
    sign_up()
elif auth == "Login":
    if login():
        selection = st.sidebar.radio("Go to", list(pages.keys()))
        pages[selection]()
else:
    st.info("Please log in or sign up to access the application.")
