#!/usr/bin/env python3
"""
Build and install streamlit-theta package locally
"""

import subprocess
import sys
import os
import shutil

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False

def main():
    print("🚀 Building and installing streamlit-theta v1.0.0")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("streamlit_theta"):
        print("❌ Error: streamlit_theta directory not found!")
        print("   Make sure you're running this from the project root.")
        sys.exit(1)
    
    # Clean previous builds
    print("\n🧹 Cleaning previous builds...")
    dirs_to_clean = ["build", "dist", "streamlit_theta.egg-info"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")
    
    # Install build dependencies
    if not run_command("pip install build twine", "Installing build dependencies"):
        sys.exit(1)
    
    # Build the package
    if not run_command("python -m build", "Building package"):
        sys.exit(1)
    
    # Install the package locally
    if not run_command("pip install dist/streamlit_theta-1.0.0-py3-none-any.whl --force-reinstall", 
                      "Installing streamlit-theta locally"):
        sys.exit(1)
    
    print("\n✅ Successfully built and installed streamlit-theta v1.0.0!")
    print("\n📦 Package contents:")
    print("   - PowerPoint/Keynote-style visual editor")
    print("   - Drag-and-drop text elements")
    print("   - Real-time formatting controls") 
    print("   - Slide thumbnails and navigation")
    print("   - Property panels for styling")
    
    print("\n💡 Usage example:")
    print("   from streamlit_theta import theta_slide_editor")
    print("   slides = theta_slide_editor(slides=data, width=800, height=600)")
    
    print("\n🎉 Ready to use in your Streamlit apps!")

if __name__ == "__main__":
    main() 