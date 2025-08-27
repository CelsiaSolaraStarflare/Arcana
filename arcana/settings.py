import streamlit as st
from .translation import t, render_language_selector, init_language_state

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

# Function for the settings page
def settings_page():
    st.title("Settings")
    st.write("Customize your chatbot experience.")

    # Store the selected theme in session_state
    if "theme" not in st.session_state:
        st.session_state.theme = "Light"

    # Dropdown for theme selection
    theme = st.selectbox("Choose a theme:", ["Light", "Dark"], index=["Light", "Dark"].index(st.session_state.theme))

    # Update the theme in session_state when a new theme is selected
    if theme != st.session_state.theme:
        st.session_state.theme = theme
        st.rerun()  # Rerun the app to apply the theme change

    st.write(f"Selected theme: {st.session_state.theme}")

    # --- Update Log ---
    with st.expander("View Update Log"):
        changelog = None
        if "changelog_content" not in st.session_state:
            try:
                with open('CHANGELOG.md', 'r', encoding='utf-8') as log_file:
                    changelog = log_file.read()
                st.session_state.changelog_content = changelog
            except FileNotFoundError:
                st.session_state.changelog_content = None
        else:
            changelog = st.session_state.changelog_content
        if changelog:
            # Inject CSS to constrain height and add scrolling for long changelogs
            st.markdown(
                """
                <style>
                .changelog-box {
                    max-height: 450px;
                    overflow-y: auto;
                    padding-right: 1rem;
                    border: 1px solid var(--secondary-background-color, #444);
                    border-radius: 6px;
                    /* Inherit background so it works in both light and dark modes */
                }
                .changelog-box h1 {
                    font-size: 1.5rem;
                }
                .changelog-box h2 {
                    font-size: 1.25rem;
                }
                .changelog-box h3 {
                    font-size: 1.1rem;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            # Render the markdown inside a styled div for scrolling
            st.markdown(f"<div class='changelog-box'>{changelog}</div>", unsafe_allow_html=True)
        else:
            st.info("No changelog available yet.")

    # The call to apply_theme() has been removed as it was causing a NameError.
    # To change the theme, please use the built-in Streamlit settings menu
    # (click the three dots in the top-right corner).
    # apply_theme()

