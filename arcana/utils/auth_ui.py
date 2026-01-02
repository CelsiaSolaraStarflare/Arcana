from __future__ import annotations

import streamlit as st

from arcana.core.config import DATA_DIR
from arcana.utils.auth import (
    create_user,
    crypto_available,
    password_login_enabled,
    reset_user_password,
    verify_user,
)
from arcana.utils.emailer import send_welcome_email


def _set_user_session(user_id: str, email: str, key: bytes) -> None:
    user_dir = DATA_DIR / "users" / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    st.session_state.auth_mode = "user"
    st.session_state.auth_user_id = user_id
    st.session_state.auth_email = email
    st.session_state.auth_key = key
    st.session_state.user_data_dir = str(user_dir)


def _set_guest_session() -> None:
    guest_dir = DATA_DIR / "guest"
    guest_dir.mkdir(parents=True, exist_ok=True)
    st.session_state.auth_mode = "guest"
    st.session_state.auth_user_id = "guest"
    st.session_state.auth_email = None
    st.session_state.auth_key = None
    st.session_state.user_data_dir = str(guest_dir)


def enforce_login() -> bool:
    if not password_login_enabled():
        return True

    if st.session_state.get("auth_mode") in {"user", "guest"}:
        return True

    if not crypto_available():
        st.error("Password login requires the 'cryptography' package.")
        st.stop()

    st.title("Welcome to Arcana")
    st.caption("Sign in to continue, create an account, or use guest mode.")

    login_tab, signup_tab, reset_tab, guest_tab = st.tabs(["Login", "Sign Up", "Reset", "Guest"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")
            if submitted:
                try:
                    result = verify_user(email, password)
                except Exception as exc:
                    st.error(str(exc))
                    result = None
                if not result:
                    st.error("Invalid email or password.")
                else:
                    user_id, key = result
                    _set_user_session(user_id, email, key)
                    st.success("Logged in.")
                    st.rerun()

    with signup_tab:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
            submitted = st.form_submit_button("Create account")
            if submitted:
                if not email or not password:
                    st.error("Email and password are required.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                else:
                    try:
                        user_id, key = create_user(email, password)
                        send_welcome_email(email)
                        _set_user_session(user_id, email, key)
                        st.success("Account created.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

    with guest_tab:
        st.write("Continue without saving or encrypting your data.")
        if st.button("Continue as guest"):
            _set_guest_session()
            st.rerun()

    with reset_tab:
        with st.form("reset_form"):
            email = st.text_input("Email", key="reset_email")
            new_password = st.text_input("New password", type="password", key="reset_password")
            confirm = st.text_input("Confirm new password", type="password", key="reset_confirm")
            submitted = st.form_submit_button("Reset password")
            if submitted:
                if not email or not new_password:
                    st.error("Email and new password are required.")
                elif new_password != confirm:
                    st.error("Passwords do not match.")
                else:
                    try:
                        user_id, key = reset_user_password(email, new_password)
                        _set_user_session(user_id, email, key)
                        st.success("Password updated.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

    st.stop()


def logout() -> None:
    for key in (
        "auth_mode",
        "auth_user_id",
        "auth_email",
        "auth_key",
        "user_data_dir",
        "dbms",
        "messages",
    ):
        if key in st.session_state:
            del st.session_state[key]
