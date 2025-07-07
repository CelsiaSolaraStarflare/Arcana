import streamlit as st

def apply_theme():
    """
    Applies the selected theme by injecting custom CSS.
    """
    if "theme" not in st.session_state:
        st.session_state.theme = "Light"

    if st.session_state.theme == "Dark":
        dark_mode_css = """
        <style>
        .stApp {
            background-color: #1a1a1a;
            color: #ffffff;
        }
        [data-testid="stSidebar"] {
            background-color: #2e2e2e;
        }
        .stButton>button {
            background-color: #4f4f4f;
            color: #ffffff;
            border: 1px solid #4f4f4f;
        }
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            background-color: #2e2e2e;
            color: #ffffff;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff;
        }
        </style>
        """
        st.markdown(dark_mode_css, unsafe_allow_html=True) 