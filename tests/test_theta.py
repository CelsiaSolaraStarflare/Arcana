"""
Test application for streamlit-theta visual slide editor
"""

import streamlit as st

# Try to import theta editor
try:
    from streamlit_theta import theta_slide_editor
    THETA_AVAILABLE = True
except ImportError:
    THETA_AVAILABLE = False

def main():
    st.set_page_config(
        page_title="Streamlit Theta Demo",
        page_icon="🎨",
        layout="wide"
    )
    
    st.title("🎨 Streamlit Theta Demo")
    st.markdown("**PowerPoint/Keynote-style Visual Slide Editor for Streamlit**")
    
    if not THETA_AVAILABLE:
        st.error("❌ Streamlit Theta not installed!")
        st.markdown("**Install it with:**")
        st.code("python utils/build_and_install.py")
        st.markdown("**Or manually:**")
        st.code("pip install build && python -m build && pip install dist/streamlit_theta-1.0.0-py3-none-any.whl")
        return
    
    st.success("✅ Streamlit Theta is installed and ready!")
    
    # Sample slide data
    if "demo_slides" not in st.session_state:
        st.session_state.demo_slides = [
            {
                "id": "slide_1",
                "title": "Welcome to Theta",
                "elements": [
                    {
                        "type": "text",
                        "id": "title_text",
                        "content": "Welcome to Streamlit Theta!",
                        "x": 50,
                        "y": 50,
                        "width": 400,
                        "height": 60,
                        "fontSize": 24,
                        "fontFamily": "Arial",
                        "color": "#2D3748",
                        "bold": True,
                        "italic": False,
                        "underline": False
                    },
                    {
                        "type": "text", 
                        "id": "subtitle_text",
                        "content": "The PowerPoint/Keynote-style editor for Streamlit applications.",
                        "x": 50,
                        "y": 130,
                        "width": 400,
                        "height": 80,
                        "fontSize": 16,
                        "fontFamily": "Arial",
                        "color": "#4A5568",
                        "bold": False,
                        "italic": True,
                        "underline": False
                    }
                ],
                "background": "#F7FAFC"
            },
            {
                "id": "slide_2", 
                "title": "Features",
                "elements": [
                    {
                        "type": "text",
                        "id": "features_title",
                        "content": "Amazing Features",
                        "x": 50,
                        "y": 30,
                        "width": 300,
                        "height": 50,
                        "fontSize": 20,
                        "fontFamily": "Arial",
                        "color": "#2D3748",
                        "bold": True,
                        "italic": False,
                        "underline": False
                    },
                    {
                        "type": "text",
                        "id": "features_list",
                        "content": "• Drag-and-drop editing\n• Real-time formatting\n• Visual slide thumbnails\n• Property panels\n• Export capabilities",
                        "x": 50,
                        "y": 100,
                        "width": 400,
                        "height": 200,
                        "fontSize": 14,
                        "fontFamily": "Arial", 
                        "color": "#2D3748",
                        "bold": False,
                        "italic": False,
                        "underline": False
                    }
                ],
                "background": "#FFFFFF"
            }
        ]
    
    st.markdown("---")
    
    # Display the theta editor
    st.markdown("### 🎨 Visual Slide Editor")
    st.markdown("Try editing the slides below - drag elements, change text, adjust properties!")
    
    updated_slides = theta_slide_editor(
        slides=st.session_state.demo_slides,
        width=900,
        height=600,
        key="demo_editor"
    )
    
    # Update session state if slides were modified
    if updated_slides:
        st.session_state.demo_slides = updated_slides
        st.success("🎉 Slides updated!")
    
    # Display slide data
    st.markdown("---")
    st.markdown("### 📊 Slide Data")
    with st.expander("View slide data JSON"):
        st.json(st.session_state.demo_slides)
    
    # Instructions
    st.markdown("---")
    st.markdown("### 📖 How to Use")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🖱️ Editing:**")
        st.markdown("• Click elements to select them")
        st.markdown("• Drag elements to move them")  
        st.markdown("• Use resize handles to change size")
        st.markdown("• Edit text by clicking and typing")
        
    with col2:
        st.markdown("**🎨 Toolbar:**")
        st.markdown("• **T** - Add text element")
        st.markdown("• **📷** - Add image (coming soon)")
        st.markdown("• **⬜** - Add shape (coming soon)")
        st.markdown("• **🗑️** - Delete selected element")
        st.markdown("• **Save Changes** - Apply edits")
    
    st.markdown("---")
    st.markdown("### 🚀 Integration")
    st.markdown("**Use in your Streamlit apps:**")
    
    code_example = '''
from streamlit_theta import theta_slide_editor

# Create slide data
slides = [
    {
        "id": "slide_1",
        "title": "My Slide",
        "elements": [
            {
                "type": "text",
                "id": "text_1", 
                "content": "Hello World!",
                "x": 50, "y": 50,
                "width": 200, "height": 50,
                "fontSize": 18,
                "fontFamily": "Arial",
                "color": "#000000",
                "bold": False,
                "italic": False,
                "underline": False
            }
        ],
        "background": "#ffffff"
    }
]

# Display editor
updated_slides = theta_slide_editor(
    slides=slides,
    width=800,
    height=600,
    key="my_editor"
)
'''
    
    st.code(code_example, language="python")

if __name__ == "__main__":
    main() 