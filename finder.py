import os
import streamlit as st

# Base directory for file storage
LOCAL_CACHE_DIR = "local_cache"
os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)

def store_uploaded_files(uploaded_files):
    stored_files = []
    for file in uploaded_files:
        file_path = os.path.join(LOCAL_CACHE_DIR, file.name)
        # Write the uploaded file's contents to the local directory
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
        stored_files.append(file_path)
    return stored_files

def display_cached_files():
    # Initialize the session state for navigation if not already set
    if "current_path" not in st.session_state:
        st.session_state.current_path = LOCAL_CACHE_DIR

    current_path = st.session_state.current_path

    # Add a refresh button
    if st.button("Refresh File List"):
        st.rerun()  # Replaces st.experimental_rerun()

    # Display the current folder (relative to the base)
    relative_path = os.path.relpath(current_path, LOCAL_CACHE_DIR)
    st.subheader(f"Finder – {relative_path if relative_path != '.' else 'Base'}")
    
    # Show a Back button if we are not at the base directory.
    if os.path.abspath(current_path) != os.path.abspath(LOCAL_CACHE_DIR):
        if st.button("Back"):
            st.session_state.current_path = os.path.dirname(current_path)
            st.rerun()  # Replaces st.experimental_rerun()

    # Get a listing of items (directories and files) in the current folder.
    items = os.listdir(current_path)
    directories = sorted([item for item in items if os.path.isdir(os.path.join(current_path, item))])
    files = sorted([item for item in items if not os.path.isdir(os.path.join(current_path, item))])
    all_items = directories + files

    # Display items in a grid layout (four per row)
    num_cols = 4
    for i in range(0, len(all_items), num_cols):
        cols = st.columns(num_cols)
        for j, item in enumerate(all_items[i : i + num_cols]):
            full_item_path = os.path.join(current_path, item)
            with cols[j]:
                # If the item is a directory, show a folder icon and an 'Open' button.
                if os.path.isdir(full_item_path):
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; border-radius: 8px;
                                padding: 10px; text-align: center;">
                        📁 <b>{item}</b>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Open", key=f"open_{item}"):
                        st.session_state.current_path = full_item_path
                        st.rerun()  # Replaces st.experimental_rerun()
                # If the item is a file, show a file icon and a move‑to‑folder selector.
                else:
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; border-radius: 8px;
                                padding: 10px; text-align: center;">
                        📄 <b>{item}</b>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Build the selectbox options:
                    # List current subdirectories in the current folder, plus the option to create a new folder.
                    move_options = ["Select folder"] + directories + ["Create new folder"]
                    selected_folder = st.selectbox(f"Move '{item}' to:", move_options, key=f"select_{item}")
                    new_folder = ""
                    # If user chooses to create a new folder, provide a text input for the folder name.
                    if selected_folder == "Create new folder":
                        new_folder = st.text_input("New folder name:", key=f"new_{item}")
                    
                    if st.button("Move", key=f"move_{item}"):
                        file_source = os.path.join(current_path, item)
                        # Check the selection and perform the move.
                        if selected_folder == "Select folder":
                            st.error("Please select a valid folder.")
                        elif selected_folder == "Create new folder":
                            if new_folder.strip():
                                target_folder = os.path.join(current_path, new_folder.strip())
                                os.makedirs(target_folder, exist_ok=True)
                                target_path = os.path.join(target_folder, item)
                                os.rename(file_source, target_path)
                                st.success(f"Moved '{item}' to '{new_folder.strip()}'.")
                                st.rerun()  # Replaces st.experimental_rerun()
                            else:
                                st.error("Please enter a valid folder name.")
                        else:
                            target_folder = os.path.join(current_path, selected_folder)
                            target_path = os.path.join(target_folder, item)
                            os.rename(file_source, target_path)
                            st.success(f"Moved '{item}' to '{selected_folder}'.")
                            st.rerun()  # Replaces st.experimental_rerun()

def files_page():
    st.title("File Management")

    # File uploader to accept multiple files.
    uploaded_files = st.file_uploader("Upload files", type=["txt", "pdf", "csv", "docx"], accept_multiple_files=True)
    if uploaded_files:
        stored_files = store_uploaded_files(uploaded_files)
        st.success(f"{len(stored_files)} files uploaded and stored successfully!")
        st.rerun()  # Automatically refresh after uploading

    display_cached_files()

if __name__ == "__main__":
    files_page()
