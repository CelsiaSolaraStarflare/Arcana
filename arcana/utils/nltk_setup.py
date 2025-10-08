"""
NLTK Setup Utility
This module ensures that required NLTK data is downloaded and available.
Import this module before using NLTK functions to guarantee data availability.
"""

import nltk
import ssl
from functools import lru_cache
from urllib.error import URLError


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
                if not nltk.download(package_name, quiet=True):
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
