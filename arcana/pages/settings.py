import os
import streamlit as st

from arcana.utils import storage
from arcana.utils.fiber import FiberDBMS
from arcana.utils.kai import KaiInstantDBMS, KaiThinkDBMS
from arcana.utils.web_search import search_web
from arcana.utils.auth import load_app_settings, save_app_settings
from arcana.utils.emailer import send_welcome_email


def _inject_css(css: str) -> None:
    html = f"<style>{css}</style>"
    html_fn = getattr(st, "html", None)
    if callable(html_fn):
        html_fn(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def apply_theme():
    """Apply the selected theme by injecting custom CSS."""

    if "theme" not in st.session_state:
        st.session_state.theme = "Light"
    if "textual_refiner_enable_diagnostics" not in st.session_state:
        st.session_state.textual_refiner_enable_diagnostics = st.session_state.get(
            "refiner_enable_diagnostics", True
        )
    if "textual_refiner_enable_quality_checks" not in st.session_state:
        st.session_state.textual_refiner_enable_quality_checks = st.session_state.get(
            "refiner_enable_quality_checks", True
        )

    theme = st.session_state.theme
    base_css = """
    .stApp {
        transition: background 0.2s ease, color 0.2s ease;
    }
    """

    if theme == "Dark":
        theme_css = """
        .stApp {
            background-color: #101010;
            color: #f7f7f7;
        }
        [data-testid="stSidebar"] {
            background-color: #1f1f1f;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        .stButton>button {
            background-color: #2b2b2b;
            color: #f7f7f7;
            border: 1px solid #3a3a3a;
        }
        .stTextInput>div>div>input,
        .stTextArea>div>div>textarea,
        .stSelectbox>div>div>div {
            background-color: #1f1f1f;
            color: #f7f7f7;
            border-color: #3a3a3a;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff;
        }
        """
    elif theme == "Glass":
        theme_css = """
        .stApp {
            background: linear-gradient(135deg, rgba(20, 24, 35, 0.85), rgba(33, 45, 62, 0.75)),
                        url('https://images.unsplash.com/photo-1527443224154-dcc76ee9bc02?auto=format&fit=crop&w=1350&q=80') center/cover fixed;
            color: #f0f4ff;
        }
        [data-testid="stSidebar"],
        .stApp header,
        .stApp section,
        .stApp footer {
            background: rgba(15, 20, 30, 0.35);
            backdrop-filter: blur(18px);
        }
        .stButton>button,
        .stSelectbox>div>div,
        .stTextInput>div>div>input,
        .stTextArea>div>div>textarea {
            background: rgba(255, 255, 255, 0.12);
            color: #f6fbff;
            border: 1px solid rgba(255, 255, 255, 0.35);
        }
        .stButton>button svg,
        .stSidebar .stButton>button svg,
        .stSidebar [data-testid="stMarkdownContainer"] svg {
            opacity: 0.65;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #f6fbff;
            text-shadow: 0 4px 16px rgba(0, 0, 0, 0.45);
        }
        """
    else:
        theme_css = """
        .stApp {
            background: #f5f5f8;
            color: #1f1f1f;
        }
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid rgba(0, 0, 0, 0.08);
        }
        .stButton>button,
        .stSelectbox>div>div {
            color: #1f1f1f;
        }
        """

    _inject_css(base_css + theme_css)

# Function for the settings page
def settings_page():
    if "theme" not in st.session_state:
        st.session_state.theme = "Light"
    if "dbms_mode" not in st.session_state:
        st.session_state.dbms_mode = "fiber"

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

    st.markdown("---")
    st.subheader("Security")
    app_settings = load_app_settings()
    login_enabled = st.checkbox(
        "Require password login",
        value=bool(app_settings.get("password_login_enabled", False)),
        help="When enabled, users must log in or use guest mode before accessing the app.",
    )
    if login_enabled != app_settings.get("password_login_enabled", False):
        app_settings["password_login_enabled"] = login_enabled
        save_app_settings(app_settings)
        st.success("Login setting saved. Refresh the app to apply.")
    if st.session_state.get("auth_email"):
        if st.button("Send demo email to my login address"):
            result = send_welcome_email(st.session_state.get("auth_email", ""))
            if result:
                st.success("Demo email sent.")
            elif result is False:
                st.error("Email failed to send. Check RESEND_API_KEY and RESEND_FROM.")
            else:
                st.info("Email not configured. Set RESEND_API_KEY and RESEND_FROM.")

    st.markdown("---")
    st.subheader("Textual Refiner")
    st.caption(
        "Control diagnostics, quality reports, and AI tooling for the unified Textual Refiner workspace."
    )
    st.checkbox(
        "Enable diagnostics panel",
        key="textual_refiner_enable_diagnostics",
        help="Toggle the quality metrics view in the Textual Refiner workspace.",
    )
    st.checkbox(
        "Allow AI quality checks",
        key="textual_refiner_enable_quality_checks",
        help="When enabled, Arcana can run AI-powered grammar and style diagnostics on your draft.",
    )

    st.markdown("---")
    st.subheader("DBMS Search")
    st.caption("Choose the search engine and test the same prompt across modes.")

    dbms_options = {
        "Fiber (legacy)": "fiber",
        "Kai-Instant (fast)": "kai-instant",
        "Kai-Think (quality)": "kai-think",
    }
    current_label = next(
        (label for label, value in dbms_options.items() if value == st.session_state.dbms_mode),
        "Fiber (legacy)",
    )
    selected_label = st.selectbox(
        "Search mode",
        list(dbms_options.keys()),
        index=list(dbms_options.keys()).index(current_label),
        help="Kai-Instant prioritizes speed; Kai-Think uses a larger candidate pool and reranks.",
    )
    selected_mode = dbms_options[selected_label]

    if selected_mode != st.session_state.dbms_mode:
        if selected_mode == "kai-instant":
            dbms = KaiInstantDBMS()
        elif selected_mode == "kai-think":
            dbms = KaiThinkDBMS()
        else:
            dbms = FiberDBMS()

        if storage.index_file_exists():
            storage.load_dbms(dbms)
        st.session_state.dbms = dbms
        st.session_state.dbms_mode = selected_mode
        st.success(f"Switched DBMS to {selected_label}.")
        rerun = getattr(st, "rerun", None)
        if callable(rerun):
            rerun()
        else:
            st.experimental_rerun()

    query_text = st.text_input(
        "Test query",
        placeholder="Try the same prompt here to compare results",
        key="dbms_test_query",
    )
    top_n = st.slider("Results to show", min_value=1, max_value=10, value=5, key="dbms_test_top_n")
    if st.button("Run test search", key="dbms_test_run") and query_text:
        dbms = st.session_state.get("dbms")
        if dbms is None:
            st.warning("DBMS is not initialized yet.")
        else:
            results = dbms.query(query_text, top_n)
            if results:
                for idx, result in enumerate(results, 1):
                    st.markdown(f"**Result {idx}:** {result['name']}")
                    st.write(result["content"])
                    st.caption(f"Tags: {result['tags']}")
            else:
                st.info("No results found.")

    st.markdown("---")
    st.subheader("Web Search Demo")
    st.caption("Preview supplemental web results (Brave Search API) for a test query.")

    web_query = st.text_input(
        "Web search query",
        placeholder="Ask something that needs current context",
        key="web_search_query",
    )
    web_results_count = st.slider(
        "Web results",
        min_value=1,
        max_value=8,
        value=3,
        key="web_search_count",
    )
    if st.button("Run web search", key="web_search_run") and web_query:
        results = search_web(web_query, max_results=web_results_count)
        if results:
            for idx, result in enumerate(results, 1):
                st.markdown(f"**Result {idx}:** {result.get('title', 'Untitled')}")
                if result.get("snippet"):
                    st.write(result["snippet"])
                if result.get("link"):
                    st.caption(result["link"])
        else:
            st.info("No web results found.")

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

