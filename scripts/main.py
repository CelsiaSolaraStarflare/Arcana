#!/usr/bin/env python3
"""
Arcana Main Entry Point
Refactored version with organized module structure
"""

import os
import sys

# Add the parent directory to Python path so we can import from arcana package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main application from the refactored structure
from arcana.core.app import *

if __name__ == "__main__":
    # Run the application
    pass