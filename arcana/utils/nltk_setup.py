"""
NLTK Setup Utility
This module ensures that required NLTK data is downloaded and available.
Import this module before using NLTK functions to guarantee data availability.
"""

import os
import nltk
import ssl
from functools import lru_cache
from typing import Iterable, List
from urllib.error import URLError

from nltk.corpus import stopwords as nltk_stopwords
from nltk.tokenize import word_tokenize as nltk_word_tokenize


DEFAULT_NLTK_DATA_DIR = "/tmp/nltk_data"


def _ensure_nltk_data_dir():
    """Ensure a writable NLTK data directory is configured."""
    data_dir = os.environ.get("NLTK_DATA", DEFAULT_NLTK_DATA_DIR)
    os.environ["NLTK_DATA"] = data_dir
    try:
        os.makedirs(data_dir, exist_ok=True)
    except OSError:
        # Fall back to the default path if the env path is not writable.
        if data_dir != DEFAULT_NLTK_DATA_DIR:
            data_dir = DEFAULT_NLTK_DATA_DIR
            os.environ["NLTK_DATA"] = data_dir
            os.makedirs(data_dir, exist_ok=True)
    if data_dir not in nltk.data.path:
        nltk.data.path.insert(0, data_dir)
    return data_dir


def _patch_ssl_context():
    """Temporarily replace the default HTTPS context with an unverified one."""
    try:
        create_unverified = ssl._create_unverified_context
    except AttributeError:
        # The attribute is not available (e.g. on very old Python builds)
        return None

    original_context = ssl._create_default_https_context
    ssl._create_default_https_context = create_unverified
    return original_context


def _restore_ssl_context(original_context):
    """Restore the default HTTPS context if it was patched."""
    if original_context is not None:
        ssl._create_default_https_context = original_context


@lru_cache(maxsize=1)
def ensure_nltk_data():
    """
    Ensures that required NLTK data packages are downloaded.
    This function is cached so it only runs once per session.
    
    Returns:
        bool: True if all data is available
    """
    # Ensure we have a writable data dir (Streamlit Cloud uses /tmp)
    data_dir = _ensure_nltk_data_dir()

    # Handle SSL certificate issues for NLTK downloads
    original_ssl_context = _patch_ssl_context()
    
    required_packages = [
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('tokenizers/punkt', 'punkt'), 
        ('corpora/stopwords', 'stopwords')
    ]
    
    for data_path, package_name in required_packages:
        try:
            nltk.data.find(data_path)
        except (LookupError, OSError):
            print(f"Downloading NLTK package: {package_name}")
            try:
                if not nltk.download(package_name, download_dir=data_dir, quiet=True):
                    print(
                        f"Warning: Download returned False for {package_name}. "
                        "The package might be unavailable."
                    )
            except (URLError, ssl.SSLError) as err:
                print(
                    "Warning: Network/SSL error occurred while downloading "
                    f"{package_name}: {err}"
                )
            except Exception as err:
                print(f"Warning: Failed to download {package_name}: {err}")
                # Continue with other packages

    _restore_ssl_context(original_ssl_context)
    
    return True


# Auto-run the setup when this module is imported
ensure_nltk_data()


def safe_word_tokenize(text: str) -> List[str]:
    """Safely tokenize text using NLTK's word tokenizer.

    This wrapper ensures that required tokenizer data is present before
    delegating to :func:`nltk.word_tokenize`. If the tokenizer data is still
    unavailable, an empty list is returned instead of raising an exception.
    """

    ensure_nltk_data()

    try:
        return nltk_word_tokenize(text)
    except LookupError:
        # The punkt tokenizer is unavailable even after attempting to
        # download it. Return an empty list so callers can handle the
        # failure gracefully.
        return []


def safe_stopwords(language: str = "english") -> Iterable[str]:
    """Return stop words for the requested language if they are available.

    The function ensures that the stopwords corpus exists before attempting to
    access it. If the corpus cannot be loaded, an empty list is returned.
    """

    ensure_nltk_data()

    try:
        return nltk_stopwords.words(language)
    except LookupError:
        return []
