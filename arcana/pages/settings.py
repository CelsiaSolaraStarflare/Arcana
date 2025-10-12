import streamlit as st


def apply_theme():
    """Apply the selected theme by injecting custom CSS and toggling attributes."""

    if "theme" not in st.session_state:
        st.session_state.theme = "Light"

    theme_css = """
    <style>
    html[data-theme="Light"] .stApp {
        background: #f5f5f8;
        color: #1f1f1f;
    }
    html[data-theme="Light"] [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid rgba(0, 0, 0, 0.08);
    }
    html[data-theme="Light"] .stButton>button,
    html[data-theme="Light"] .stSelectbox>div>div {
        color: #1f1f1f;
    }

    html[data-theme="Dark"] .stApp {
        background-color: #101010;
        color: #f7f7f7;
    }
    html[data-theme="Dark"] [data-testid="stSidebar"] {
        background-color: #1f1f1f;
    }
    html[data-theme="Dark"] .stButton>button {
        background-color: #2b2b2b;
        color: #f7f7f7;
        border: 1px solid #3a3a3a;
    }
    html[data-theme="Dark"] .stTextInput>div>div>input,
    html[data-theme="Dark"] .stTextArea>div>div>textarea,
    html[data-theme="Dark"] .stSelectbox>div>div>div {
        background-color: #1f1f1f;
        color: #f7f7f7;
        border-color: #3a3a3a;
    }
    html[data-theme="Dark"] h1,
    html[data-theme="Dark"] h2,
    html[data-theme="Dark"] h3,
    html[data-theme="Dark"] h4,
    html[data-theme="Dark"] h5,
    html[data-theme="Dark"] h6 {
        color: #ffffff;
    }

    html[data-theme="Glass"] .stApp {
        background: linear-gradient(135deg, rgba(20, 24, 35, 0.85), rgba(33, 45, 62, 0.75)),
                    url('https://images.unsplash.com/photo-1527443224154-dcc76ee9bc02?auto=format&fit=crop&w=1350&q=80') center/cover fixed;
        color: #f0f4ff;
    }
    html[data-theme="Glass"] [data-testid="stSidebar"],
    html[data-theme="Glass"] .stApp header,
    html[data-theme="Glass"] .stApp section,
    html[data-theme="Glass"] .stApp footer {
        background: rgba(15, 20, 30, 0.35);
        backdrop-filter: blur(18px);
    }
    html[data-theme="Glass"] .stButton>button,
    html[data-theme="Glass"] .stSelectbox>div>div,
    html[data-theme="Glass"] .stTextInput>div>div>input,
    html[data-theme="Glass"] .stTextArea>div>div>textarea {
        background: rgba(255, 255, 255, 0.12);
        color: #f6fbff;
        border: 1px solid rgba(255, 255, 255, 0.35);
    }
    html[data-theme="Glass"] .stButton>button svg,
    html[data-theme="Glass"] .stSidebar .stButton>button svg,
    html[data-theme="Glass"] .stSidebar [data-testid="stMarkdownContainer"] svg {
        opacity: 0.65;
    }
    html[data-theme="Glass"] h1,
    html[data-theme="Glass"] h2,
    html[data-theme="Glass"] h3,
    html[data-theme="Glass"] h4,
    html[data-theme="Glass"] h5,
    html[data-theme="Glass"] h6 {
        color: #f6fbff;
        text-shadow: 0 4px 16px rgba(0, 0, 0, 0.45);
    }
    </style>
    """

    st.markdown(theme_css, unsafe_allow_html=True)
    st.markdown(
        f"""
        <script>
        const root = window.parent.document.documentElement;
        if (root) {{
            root.setAttribute('data-theme', '{st.session_state.theme}');
        }}
        </script>
        """,
        unsafe_allow_html=True,
    )

# Function for the settings page
def settings_page():
    if "theme" not in st.session_state:
        st.session_state.theme = "Light"

    apply_theme()

    st.title("Settings")
    st.write("Customize your chatbot experience.")

    theme_options = ["Light", "Dark", "Glass"]
    theme = st.selectbox(
        "Choose a theme:",
        theme_options,
        index=theme_options.index(st.session_state.theme),
        help="Select between a classic light interface, a dark night mode, or the deluxe glass aesthetic.",
    )

    if theme != st.session_state.theme:
        st.session_state.theme = theme
        rerun = getattr(st, "rerun", None)
        if callable(rerun):
            rerun()
        else:
            st.experimental_rerun()

    descriptions = {
        "Light": "Bright day mode with crisp contrast for maximum readability.",
        "Dark": "Night mode with deep blacks designed for low-light environments.",
        "Glass": "Glassmorphism-inspired mode with translucent panels and glowing typography.",
    }
    st.info(descriptions.get(st.session_state.theme, ""))

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

