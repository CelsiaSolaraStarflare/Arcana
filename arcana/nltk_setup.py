"""
NLTK Setup Utility
This module ensures that required NLTK data is downloaded and available.
Import this module before using NLTK functions to guarantee data availability.
"""

import nltk
import ssl
import os
from functools import lru_cache


@lru_cache(maxsize=1)
def ensure_nltk_data():
    """
    Ensures that required NLTK data packages are downloaded.
    This function is cached so it only runs once per session.
    
    Returns:
        bool: True if all data is available
    """
    # Handle SSL certificate issues for NLTK downloads
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    
    # Set NLTK data path to user directory
    nltk_data_dir = '/Users/osmond/nltk_data'
    if nltk_data_dir not in nltk.data.path:
        nltk.data.path.append(nltk_data_dir)

    required_packages = [
        ('tokenizers/punkt', 'punkt'),
        ('corpora/stopwords', 'stopwords')
    ]

    for data_path, package_name in required_packages:
        try:
            nltk.data.find(data_path)
        except LookupError:
            print(f"Downloading NLTK package: {package_name}")
            try:
                nltk.download(package_name, download_dir=nltk_data_dir, quiet=True)
            except Exception as e:
                print(f"Warning: Failed to download {package_name}: {e}")
                # Continue with other packages
    return True


# Auto-run the setup when this module is imported
ensure_nltk_data()
