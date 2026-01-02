from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

from arcana.core.config import DATA_DIR
from arcana.utils.auth import decrypt_bytes, encrypt_bytes


def _get_session_value(name: str) -> Optional[object]:
    if st is None:
        return None
    return st.session_state.get(name)


def get_user_data_dir() -> Path:
    user_dir = _get_session_value("user_data_dir")
    if user_dir:
        path = Path(user_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def get_auth_key() -> Optional[bytes]:
    key = _get_session_value("auth_key")
    if isinstance(key, bytes):
        return key
    return None


def get_index_file_path() -> Path:
    return DATA_DIR / "arcana_index.csv"


def index_file_exists() -> bool:
    return get_index_file_path().exists()


def load_dbms(dbms) -> None:
    path = get_index_file_path()
    if not path.exists():
        raise FileNotFoundError(path)
    dbms.load_from_file(str(path))


def save_dbms(dbms) -> None:
    path = get_index_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    dbms.save(str(path))
