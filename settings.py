import streamlit as st

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

    # Apply the selected theme
    apply_theme()

