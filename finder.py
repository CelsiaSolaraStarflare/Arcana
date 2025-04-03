import os
import streamlit as st
from indexing import *

# Base directory for file storage
LOCAL_CACHE_DIR = "local_cache"
USER_TMP_DB = "user_tmp_db"

# Load user temp database path from the file
if os.path.exists('tmpdb.censored'):
    with open('tmpdb.censored', mode='r') as file:
        user_tmp_path = file.read().strip()
        if user_tmp_path:
            USER_TMP_DB = user_tmp_path

# Ensure directories exist
os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)
os.makedirs(USER_TMP_DB, exist_ok=True)

def store_uploaded_files(uploaded_files, target_dir):
    stored_files = []
    for file in uploaded_files:
        file_path = os.path.join(target_dir, file.name)
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
        stored_files.append(file_path)
    return stored_files

def display_cached_files(base_dirs):
    st.subheader("Finder – Merged View")
    
    all_items = []
    for base_dir in base_dirs:
        for item in os.listdir(base_dir):
            full_path = os.path.join(base_dir, item)
            all_items.append((item, full_path, os.path.isdir(full_path)))
    
    # Sort directories first, then files
    all_items.sort(key=lambda x: (not x[2], x[0]))
    
    num_cols = 4
    for i in range(0, len(all_items), num_cols):
        cols = st.columns(num_cols)
        for j, (item, full_item_path, is_dir) in enumerate(all_items[i : i + num_cols]):
            with cols[j]:
                if is_dir:
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 10px; text-align: center;">
                        📁 <b>{item}</b>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 10px; text-align: center;">
                        📄 <b>{item}</b>
                    </div>
                    """, unsafe_allow_html=True)

def files_page():
    st.title("File Management")

    uploaded_files = st.file_uploader("Upload files", type=["txt", "pdf", "csv", "docx"], accept_multiple_files=True)
    if uploaded_files:
        target_dir = USER_TMP_DB  # Store in the user temp db
        stored_files = store_uploaded_files(uploaded_files, target_dir)
        st.success(f"{len(stored_files)} files uploaded and stored successfully!")
        st.rerun()

    display_cached_files([LOCAL_CACHE_DIR, USER_TMP_DB])

    if st.button("Index All to Database"):
        indexing(LOCAL_CACHE_DIR)
        indexing(USER_TMP_DB)
        st.success("All files indexed!")

if __name__ == "__main__":
    files_page()
