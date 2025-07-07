import os
import streamlit as st
import shutil
from indexing import indexing
from config import CACHE_DIR, INDEX_FILE
from fiber import FiberDBMS

def move_file(current_path, item, selected_folder, new_folder_name=""):
    """
    Moves a file to a specified folder, creating the folder if necessary.
    """
    source_path = os.path.join(current_path, item)
    target_dir = ""

    if selected_folder == "Create new folder":
        if not new_folder_name.strip():
            st.error("Please enter a valid folder name.")
            return False
        target_dir = os.path.join(current_path, new_folder_name.strip())
        os.makedirs(target_dir, exist_ok=True)
    elif selected_folder != "Select folder":
        target_dir = os.path.join(current_path, selected_folder)
    else:
        st.error("Please select a valid folder.")
        return False

    target_path = os.path.join(target_dir, item)
    try:
        # Using shutil.move to allow moving across different drives or file systems
        shutil.move(source_path, target_path)
        st.success(f"Moved '{item}' to '{os.path.basename(target_dir)}'.")
        return True
    except OSError as e:
        st.error(f"Error moving file: {e}")
        return False

def delete_item(path: str) -> bool:
    """Delete a file or folder at the given path.

    Args:
        path (str): Absolute path to the file or directory.

    Returns:
        bool: True if deletion succeeded, False otherwise.
    """
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        st.success(f"Deleted '{os.path.basename(path)}'.")
        return True
    except Exception as e:
        st.error(f"Error deleting item: {e}")
        return False

def rename_item(current_path: str, old_name: str, new_name: str) -> bool:
    """Renames a file or directory."""
    if not new_name.strip():
        st.error("New name cannot be empty.")
        return False
    old_path = os.path.join(current_path, old_name)
    new_path = os.path.join(current_path, new_name.strip())
    
    if os.path.exists(new_path):
        st.error(f"'{new_name}' already exists.")
        return False

    try:
        os.rename(old_path, new_path)
        st.success(f"Renamed '{old_name}' to '{new_name}'.")
        # Clear the rename state from session_state
        if f"rename_mode_{old_name}" in st.session_state:
            del st.session_state[f"rename_mode_{old_name}"]
        return True
    except OSError as e:
        st.error(f"Error renaming: {e}")
        return False

def create_folder(current_path: str, folder_name: str) -> bool:
    """Creates a new folder in the specified path."""
    if not folder_name.strip():
        st.error("Folder name cannot be empty.")
        return False
    try:
        os.makedirs(os.path.join(current_path, folder_name.strip()), exist_ok=False)
        st.success(f"Folder '{folder_name}' created successfully.")
        return True
    except OSError as e:
        st.error(f"Error creating folder: {e}")
        return False

def _display_item(col, item: str, current_path: str, directories: list):
    """Displays a single file or folder item in a grid."""
    full_path = os.path.join(current_path, item)

    with col, st.container(border=True):
        # RENAME UI
        if st.session_state.get(f"rename_mode_{item}", False):
            new_name = st.text_input("New name:", value=item, key=f"rename_input_{item}")
            c1, c2 = st.columns(2)
            if c1.button("✅ Save", key=f"save_rename_{item}"):
                if rename_item(current_path, item, new_name):
                    st.rerun()
            if c2.button("❌ Cancel", key=f"cancel_rename_{item}"):
                st.session_state[f"rename_mode_{item}"] = False
                st.rerun()
            return

        # ITEM DISPLAY UI
        is_dir = os.path.isdir(full_path)
        icon = "📁" if is_dir else "📄"
        st.markdown(f"{icon} **{item}**")

        if is_dir:
            c1, c2, c3 = st.columns([1, 1, 0.5])
            if c1.button("Open", key=f"open_{item}", use_container_width=True):
                st.session_state.current_path = full_path
                st.rerun()
            if c2.button("Rename", key=f"rename_dir_{item}", use_container_width=True):
                st.session_state[f"rename_mode_{item}"] = True
                st.rerun()
            if c3.button("🗑️", key=f"delete_dir_{item}", use_container_width=True):
                if delete_item(full_path):
                    st.rerun()
        else: # Is a file
            with st.expander("Move to..."):
                options = ["Select folder"] + directories + ["Create new folder"]
                selected = st.selectbox("Destination", options, key=f"select_{item}", label_visibility="collapsed")
                new_folder = ""
                if selected == "Create new folder":
                    new_folder = st.text_input("New folder name", key=f"new_folder_input_{item}")
                
                if st.button("Confirm Move", key=f"move_{item}"):
                    if move_file(current_path, item, selected, new_folder):
                        st.rerun()
            
            c1, c2 = st.columns([1, 0.5])
            if c1.button("Rename", key=f"rename_file_{item}", use_container_width=True):
                st.session_state[f"rename_mode_{item}"] = True
                st.rerun()
            if c2.button("🗑️", key=f"delete_file_{item}", use_container_width=True):
                if delete_item(full_path):
                    st.rerun()

def display_cached_files():
    """
    Displays the file browser UI, allowing users to navigate directories,
    move files, and trigger the indexing process.
    """
    if "current_path" not in st.session_state:
        st.session_state.current_path = CACHE_DIR

    current_path = st.session_state.current_path
    
    if st.button("⟲ Refresh"):
        st.rerun()

    relative_path = os.path.relpath(current_path, CACHE_DIR)
    st.subheader(f"Finder – {relative_path if relative_path != '.' else 'Base'}")

    if os.path.abspath(current_path) != os.path.abspath(CACHE_DIR):
        if st.button("⬅️ Back"):
            st.session_state.current_path = os.path.dirname(current_path)
            st.rerun()
    
    with st.expander("Actions"):
        new_folder_name = st.text_input("Folder Name", placeholder="Create a new folder here...")
        if st.button("Create Folder"):
            if create_folder(current_path, new_folder_name):
                st.rerun()
    
    st.markdown("---")
    
    try:
        items = os.listdir(current_path)
        directories = sorted([d for d in items if os.path.isdir(os.path.join(current_path, d))])
        files = sorted([f for f in items if not os.path.isdir(os.path.join(current_path, f))])
    except FileNotFoundError:
        st.error("The selected directory does not exist. Going back to base.")
        st.session_state.current_path = CACHE_DIR
        st.rerun()
        return

    num_cols = 4
    all_items = directories + files
    for i in range(0, len(all_items), num_cols):
        cols = st.columns(num_cols)
        for j, item in enumerate(all_items[i:i + num_cols]):
            _display_item(cols[j], item, current_path, directories)

def files_page():
    st.title("File Management")

    with st.expander("Upload New Files", expanded=True):
        uploaded_files = st.file_uploader(
            "Upload documents, PDFs, or other supported files.",
            type=["txt", "pdf", "csv", "docx"],
            accept_multiple_files=True
        )
        if uploaded_files:
            for file in uploaded_files:
                file_path = os.path.join(CACHE_DIR, file.name)
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())
            st.success(f"{len(uploaded_files)} files uploaded successfully!")
            st.rerun()

    display_cached_files()

    st.markdown("---")
    st.header("Database Indexing")
    st.info("Re-indexing is required after moving, renaming, or uploading files to ensure the chatbot can find them.")
    if st.button("Re-Index All Files", help="Click here to process all files in the Finder and update the search database. This can take a moment."):
        with st.spinner("Indexing in progress... Please wait."):
            entry_count = indexing(CACHE_DIR)
            
            # Use the existing dbms instance from session_state to reload the data
            if 'dbms' in st.session_state and isinstance(st.session_state.dbms, FiberDBMS):
                st.session_state.dbms.load_from_file(INDEX_FILE)
            else:
                # Fallback for safety, though it shouldn't be needed
                dbms = FiberDBMS()
                dbms.load_from_file(INDEX_FILE)
                st.session_state.dbms = dbms

            st.success(f"Indexing complete! 🎉 {entry_count} entries were processed.")
            st.toast("Database updated successfully!")

if __name__ == "__main__":
    files_page()
