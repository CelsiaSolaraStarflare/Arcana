from __future__ import annotations

import base64
import json
import os
import re
import secrets
from pathlib import Path
from typing import Dict, Optional, Tuple

from arcana.core.config import APP_SETTINGS_FILE, DATA_DIR, DEFAULT_PASSWORD_LOGIN

try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:  # pragma: no cover - runtime dependency
    hashes = None
    AESGCM = None
    PBKDF2HMAC = None


USERS_FILE = DATA_DIR / "users.json"
KDF_ITERATIONS = 390_000
KEY_LENGTH = 32
NONCE_LENGTH = 12


def load_app_settings() -> Dict[str, object]:
    if not APP_SETTINGS_FILE.exists():
        return {"password_login_enabled": DEFAULT_PASSWORD_LOGIN}
    try:
        data = json.loads(APP_SETTINGS_FILE.read_text(encoding="utf-8"))
        if "password_login_enabled" not in data:
            data["password_login_enabled"] = DEFAULT_PASSWORD_LOGIN
        return data
    except Exception:
        return {"password_login_enabled": DEFAULT_PASSWORD_LOGIN}


def save_app_settings(settings: Dict[str, object]) -> None:
    APP_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    APP_SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def password_login_enabled() -> bool:
    settings = load_app_settings()
    return bool(settings.get("password_login_enabled", DEFAULT_PASSWORD_LOGIN))


def crypto_available() -> bool:
    return AESGCM is not None and PBKDF2HMAC is not None and hashes is not None


def _require_crypto() -> None:
    if AESGCM is None or PBKDF2HMAC is None or hashes is None:
        raise RuntimeError("cryptography is required for password login")


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "user"


def _derive_key(password: str, salt: bytes) -> bytes:
    _require_crypto()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def _hash_password(password: str, salt: bytes) -> bytes:
    return _derive_key(password, salt)


def _load_users() -> Dict[str, Dict[str, str]]:
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_users(users: Dict[str, Dict[str, str]]) -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def get_user_dir(user_id: str) -> Path:
    return DATA_DIR / "users" / user_id


def create_user(email: str, password: str) -> Tuple[str, bytes]:
    _require_crypto()
    users = _load_users()
    user_id = _slugify(email)
    if user_id in users:
        raise ValueError("User already exists.")

    salt = secrets.token_bytes(16)
    password_hash = _hash_password(password, salt)
    users[user_id] = {
        "email": email,
        "salt": base64.b64encode(salt).decode("utf-8"),
        "password_hash": base64.b64encode(password_hash).decode("utf-8"),
    }
    _save_users(users)

    user_dir = get_user_dir(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_id, _derive_key(password, salt)


def verify_user(email: str, password: str) -> Optional[Tuple[str, bytes]]:
    _require_crypto()
    users = _load_users()
    user_id = _slugify(email)
    record = users.get(user_id)
    if not record:
        return None
    try:
        salt = base64.b64decode(record.get("salt", ""))
        stored_hash = base64.b64decode(record.get("password_hash", ""))
    except Exception:
        return None
    try:
        candidate = _hash_password(password, salt)
    except Exception:
        return None
    if not secrets.compare_digest(candidate, stored_hash):
        return None
    return user_id, _derive_key(password, salt)


def reset_user_password(email: str, new_password: str) -> Tuple[str, bytes]:
    _require_crypto()
    users = _load_users()
    user_id = _slugify(email)
    record = users.get(user_id)
    if not record:
        raise ValueError("User not found.")

    salt = secrets.token_bytes(16)
    password_hash = _hash_password(new_password, salt)
    record["salt"] = base64.b64encode(salt).decode("utf-8")
    record["password_hash"] = base64.b64encode(password_hash).decode("utf-8")
    users[user_id] = record
    _save_users(users)
    return user_id, _derive_key(new_password, salt)


def encrypt_bytes(key: bytes, plaintext: bytes) -> bytes:
    _require_crypto()
    nonce = secrets.token_bytes(NONCE_LENGTH)
    aes = AESGCM(key)
    ciphertext = aes.encrypt(nonce, plaintext, None)
    return nonce + ciphertext


def decrypt_bytes(key: bytes, payload: bytes) -> bytes:
    _require_crypto()
    nonce = payload[:NONCE_LENGTH]
    ciphertext = payload[NONCE_LENGTH:]
    aes = AESGCM(key)
    return aes.decrypt(nonce, ciphertext, None)


def encrypt_json_to_file(path: Path, data: Dict[str, object], key: bytes) -> None:
    plaintext = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    encrypted = encrypt_bytes(key, plaintext)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encrypted)


def decrypt_json_from_file(path: Path, key: bytes) -> Dict[str, object]:
    payload = path.read_bytes()
    plaintext = decrypt_bytes(key, payload)
    return json.loads(plaintext.decode("utf-8"))
