"""
Streamlit Theta - Multi-Page Demo Application
A comprehensive demonstration of all visual editors in the streamlit-theta package
"""

import streamlit as st
import streamlit_theta
import json

# Configure the page
st.set_page_config(
    page_title="Streamlit Theta Demo",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .editor-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        margin-bottom: 1rem;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        color: #155724;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("🎨 Streamlit Theta")
st.sidebar.markdown("**Visual Editors Suite v1.0.0**")

# Navigation menu
page = st.sidebar.selectbox(
    "Choose an Editor",
    [
        "🏠 Home",
        "🎯 Slide Editor", 
        "📝 Word Editor",
        "📊 Excel Editor", 
        "📋 CSV Editor",
        "🎵 Audio Editor",
        "🎬 Video Editor",
        "ℹ️ About"
    ]
)

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown("### 📖 Quick Info")
st.sidebar.info(
    "Each editor provides professional-grade functionality "
    "similar to Microsoft Office applications, but embedded "
    "directly in your Streamlit app!"
)

st.sidebar.markdown("### 🔗 Features")
st.sidebar.markdown("""
- **Drag & Drop** interfaces
- **Real-time** editing
- **Professional** layouts  
- **Export** capabilities
- **Responsive** design
""")

# Main content area
if page == "🏠 Home":
    # Home page
    st.markdown("""
    <div class="main-header">
        <h1>🎨 Streamlit Theta - Visual Editors Suite</h1>
        <p>Transform your Streamlit applications with professional visual editors</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("## Welcome to Streamlit Theta!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ✨ What's Included?
        
        **Six powerful visual editors:**
        - 🎯 **Slide Editor** - PowerPoint/Keynote style presentations
        - 📝 **Word Editor** - Rich text documents with formatting
        - 📊 **Excel Editor** - Spreadsheets with formulas
        - 📋 **CSV Editor** - Data tables with import/export
        - 🎵 **Audio Editor** - Audio playback and effects
        - 🎬 **Video Editor** - Video player with filters
        """)
    
    with col2:
        st.markdown("""
        ### 🚀 Key Benefits
        
        **Professional functionality:**
        - Intuitive drag-and-drop interfaces
        - Real-time visual feedback
        - Modern, responsive designs
        - Export to various formats
        - Seamless Streamlit integration
        - Mobile-friendly layouts
        """)
    
    st.markdown("---")
    
    # Feature showcase
    st.markdown("## 📊 Feature Comparison")
    
    feature_data = {
        "Editor": ["Slide", "Word", "Excel", "CSV", "Audio", "Video"],
        "Drag & Drop": ["✅", "✅", "✅", "✅", "➖", "➖"],
        "File Import": ["➖", "➖", "➖", "✅", "✅", "✅"],
        "Export": ["✅", "✅", "✅", "✅", "✅", "✅"],
        "Real-time Edit": ["✅", "✅", "✅", "✅", "✅", "✅"],
        "Effects/Filters": ["➖", "✅", "✅", "➖", "✅", "✅"]
    }
    
    st.dataframe(feature_data, use_container_width=True)
    
    # Getting started
    st.markdown("## 🏁 Getting Started")
    
    st.code("""
# Install the package
pip install streamlit-theta

# Import in your Streamlit app
import streamlit_theta

# Use any editor
slides = streamlit_theta.slide_editor(slides=data, width=900, height=600)
document = streamlit_theta.word_editor(content="<h1>Hello World</h1>")
spreadsheet = streamlit_theta.excel_editor(data=[["A", "B"], ["1", "2"]])
    """, language="python")

elif page == "🎯 Slide Editor":
    st.title("🎯 Slide Editor Demo")
    st.markdown("Create PowerPoint/Keynote-style presentations with drag-and-drop editing.")
    
    # Sample slide data
    if 'slide_data' not in st.session_state:
        st.session_state.slide_data = [
            {
                "elements": [
                    {
                        "id": "title1",
                        "type": "text",
                        "content": "Welcome to Streamlit Theta",
                        "x": 50, "y": 100, "width": 500, "height": 80,
                        "fontSize": "36px", "fontWeight": "bold", "color": "#2c3e50"
                    },
                    {
                        "id": "subtitle1", 
                        "type": "text",
                        "content": "Professional presentations made easy with drag-and-drop editing",
                        "x": 50, "y": 200, "width": 600, "height": 50,
                        "fontSize": "20px", "color": "#7f8c8d"
                    },
                    {
                        "id": "bullet1",
                        "type": "text", 
                        "content": "• Interactive slide creation\n• Real-time visual feedback\n• Professional layouts",
                        "x": 50, "y": 300, "width": 400, "height": 120,
                        "fontSize": "16px", "color": "#34495e"
                    }
                ]
            },
            {
                "elements": [
                    {
                        "id": "title2",
                        "type": "text",
                        "content": "Key Features",
                        "x": 50, "y": 100, "width": 400, "height": 60,
                        "fontSize": "32px", "fontWeight": "bold", "color": "#27ae60"
                    },
                    {
                        "id": "features",
                        "type": "text",
                        "content": "✅ Drag and drop elements\n✅ Real-time editing\n✅ Multiple slide support\n✅ Professional themes",
                        "x": 50, "y": 200, "width": 500, "height": 200,
                        "fontSize": "18px", "color": "#2c3e50"
                    }
                ]
            }
        ]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🎨 Interactive Editor")
        # Note: Component doesn't return data due to Streamlit version compatibility
        streamlit_theta.slide_editor(
            slides=st.session_state.slide_data,
            width=800,
            height=500
        )
        
        st.info("💡 The editor is running! Use the toolbar to add elements and click 'Save Changes' to download your presentation as a JSON file.")
    
    with col2:
        st.markdown("### 📋 Current Data")
        if isinstance(st.session_state.slide_data, list):
            st.json({
                "total_slides": len(st.session_state.slide_data),
                "total_elements": sum(len(slide.get("elements", [])) for slide in st.session_state.slide_data)
            })
        else:
            st.warning("Slide data is not in expected format")
        
        if st.button("🔄 Reset to Default", key="reset_slides"):
            del st.session_state.slide_data
            st.rerun()
        
        with st.expander("📄 View Raw Data"):
            st.json(st.session_state.slide_data)

elif page == "📝 Word Editor":
    st.title("📝 Word Editor Demo")
    st.markdown("Rich text document editing with professional formatting tools.")
    
    if 'document_content' not in st.session_state:
        st.session_state.document_content = """
        <h1>Sample Document</h1>
        <p>This is a <strong>sample document</strong> created with the Theta Word Editor. You can:</p>
        <ul>
            <li>Format text with <em>bold</em>, <em>italic</em>, and <u>underline</u></li>
            <li>Change fonts and sizes</li>
            <li>Adjust paragraph alignment</li>
            <li>Create professional documents</li>
        </ul>
        <p>The editor provides a Microsoft Word-like experience directly in your Streamlit app!</p>
        """
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 📝 Document Editor")
        # Note: Component doesn't return data due to Streamlit version compatibility
        streamlit_theta.word_editor(
            content=st.session_state.document_content,
            width=800,
            height=600
        )
        
        st.info("💡 The editor is running! Use the formatting tools to edit and click 'Save Document' to download as HTML.")
    
    with col2:
        st.markdown("### 📊 Document Stats")
        if isinstance(st.session_state.document_content, str) and st.session_state.document_content:
            import re
            text_only = re.sub('<[^<]+?>', '', st.session_state.document_content)
            word_count = len(text_only.split())
            char_count = len(text_only)
            
            st.metric("Words", word_count)
            st.metric("Characters", char_count)
        else:
            st.warning("Document content is not in expected format")
        
        if st.button("🔄 Reset Content", key="reset_document"):
            del st.session_state.document_content
            st.rerun()
        
        with st.expander("🔍 View HTML Source"):
            st.code(st.session_state.document_content, language="html")

elif page == "📊 Excel Editor":
    st.title("📊 Excel Editor Demo")
    st.markdown("Full-featured spreadsheet editor with cell navigation and formulas.")
    
    if 'excel_data' not in st.session_state:
        st.session_state.excel_data = [
            ["Product", "Price", "Quantity", "Total", "Category"],
            ["Widget A", "10.50", "5", "52.50", "Electronics"],
            ["Widget B", "15.75", "3", "47.25", "Electronics"],
            ["Widget C", "8.25", "8", "66.00", "Hardware"],
            ["Widget D", "22.00", "2", "44.00", "Software"],
            ["", "", "", "", ""],
            ["TOTAL", "", "", "=SUM(D2:D5)", ""]
        ]
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 📈 Spreadsheet Editor")
        # Note: Component doesn't return data due to Streamlit version compatibility
        streamlit_theta.excel_editor(
            data=st.session_state.excel_data,
            width=900,
            height=500
        )
        
        st.info("💡 The editor is running! Navigate with arrow keys and click 'Save Changes' to download as CSV.")
    
    with col2:
        st.markdown("### 📋 Sheet Info")
        if isinstance(st.session_state.excel_data, list) and st.session_state.excel_data:
            rows = len(st.session_state.excel_data)
            cols = len(st.session_state.excel_data[0]) if st.session_state.excel_data else 0
            
            st.metric("Rows", rows)
            st.metric("Columns", cols)
            st.metric("Cells", rows * cols)
        else:
            st.warning("Excel data is not in expected format")
        
        if st.button("🔄 Reset Data", key="reset_excel"):
            del st.session_state.excel_data
            st.rerun()
        
        with st.expander("📄 View Data"):
            st.dataframe(st.session_state.excel_data)

elif page == "📋 CSV Editor":
    st.title("📋 CSV Editor Demo")
    st.markdown("Data table editor with import/export functionality.")
    
    if 'csv_data' not in st.session_state:
        st.session_state.csv_data = [
            ["Name", "Age", "City", "Occupation", "Salary"],
            ["Alice Johnson", "28", "New York", "Engineer", "75000"],
            ["Bob Smith", "35", "Los Angeles", "Designer", "65000"],
            ["Carol Davis", "42", "Chicago", "Manager", "85000"],
            ["David Wilson", "31", "Houston", "Developer", "70000"],
            ["Eve Brown", "29", "Phoenix", "Analyst", "60000"]
        ]
        st.session_state.csv_headers = ["Name", "Age", "City", "Occupation", "Salary"]
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 📊 Data Editor")
        # Note: Component doesn't return data due to Streamlit version compatibility
        streamlit_theta.csv_editor(
            data=st.session_state.csv_data,
            headers=st.session_state.csv_headers,
            width=900,
            height=500
        )
        
        st.info("💡 The editor is running! Edit cells, add rows/columns, and use import/export.")
    
    with col2:
        st.markdown("### 📈 Data Summary")
        if isinstance(st.session_state.csv_data, list) and isinstance(st.session_state.csv_headers, list):
            rows = len(st.session_state.csv_data)
            cols = len(st.session_state.csv_headers)
        else:
            rows = 0
            cols = 0
            st.warning("CSV data is not in expected format")
        
        st.metric("Records", rows - 1)  # Subtract header row
        st.metric("Fields", cols)
        
        if st.button("📥 Download CSV", key="download_csv"):
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(st.session_state.csv_headers)
            writer.writerows(st.session_state.csv_data[1:])  # Skip header row
            
            st.download_button(
                label="💾 Save as CSV",
                data=output.getvalue(),
                file_name="theta_data.csv",
                mime="text/csv"
            )
        
        if st.button("🔄 Reset Data", key="reset_csv"):
            del st.session_state.csv_data
            del st.session_state.csv_headers
            st.rerun()

elif page == "🎵 Audio Editor":
    st.title("🎵 Audio Editor Demo")
    st.markdown("Audio player with playback controls and basic effects.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 🎧 Audio Player")
        st.info("📁 Upload an audio file using the 'Load Audio File' button in the editor below.")
        
        # Note: Component doesn't return data due to Streamlit version compatibility
        streamlit_theta.audio_editor(
            width=800,
            height=450
        )
        
        st.info("💡 Upload an audio file and use the controls to play and adjust settings.")
    
    with col2:
        st.markdown("### 🎛️ Features")
        st.markdown("""
        **Supported formats:**
        - MP3, WAV, OGG
        - M4A, FLAC
        
        **Controls:**
        - Play/Pause/Stop
        - Volume adjustment
        - Speed control
        - Pitch shifting
        - Waveform display
        
        **Effects:**
        - Real-time processing
        - Timeline scrubbing
        """)

elif page == "🎬 Video Editor":
    st.title("🎬 Video Editor Demo")
    st.markdown("Video player with filters, effects, and playback controls.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 🎥 Video Player")
        st.info("📁 Upload a video file using the 'Load Video File' button in the editor below.")
        
        # Note: Component doesn't return data due to Streamlit version compatibility
        streamlit_theta.video_editor(
            width=900,
            height=600
        )
        
        st.info("💡 Upload a video file and use the controls to play and apply effects.")
    
    with col2:
        st.markdown("### 🎬 Features")
        st.markdown("""
        **Supported formats:**
        - MP4, WebM, OGV
        - AVI, MOV
        
        **Controls:**
        - Play/Pause/Stop
        - Timeline seeking
        - Volume control
        - Playback speed
        
        **Effects:**
        - Brightness/Contrast
        - Saturation
        - Color filters
        - Visual effects
        """)

elif page == "ℹ️ About":
    st.title("ℹ️ About Streamlit Theta")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 Project Overview
        
        Streamlit Theta is a comprehensive suite of visual editors designed specifically for Streamlit applications. It brings professional-grade editing capabilities directly into your web apps.
        
        ### 🏗️ Architecture
        
        - **Modern HTML5/CSS3/JavaScript** components
        - **Streamlit Components API** integration
        - **Responsive design** for all screen sizes
        - **Type-safe Python** interfaces
        - **Apache 2.0 License** for commercial use
        """)
    
    with col2:
        st.markdown("""
        ### 📦 Package Info
        
        **Version:** 1.0.0  
        **License:** Apache 2.0  
        **Python:** 3.7+  
        **Streamlit:** 1.0+  
        
        ### 👥 Credits
        
        Built with ❤️ by the **Arcana Team**
        
        ### 🔗 Links
        
        - 📧 **Support:** support@arcana.team
        - 🐛 **Issues:** GitHub Issues
        - 📖 **Docs:** Documentation
        """)
    
    st.markdown("---")
    
    st.markdown("### 🚀 Quick Start Code")
    
    tab1, tab2, tab3 = st.tabs(["Installation", "Basic Usage", "Advanced"])
    
    with tab1:
        st.code("""
# Install via pip
pip install streamlit-theta

# Or from source
git clone https://github.com/arcana/streamlit-theta
cd streamlit-theta
pip install -e .
        """, language="bash")
    
    with tab2:
        st.code("""
import streamlit as st
import streamlit_theta

st.title("My App with Visual Editors")

# Slide editor
slides = streamlit_theta.slide_editor(
    slides=[],
    width=800,
    height=600
)

# Word editor
document = streamlit_theta.word_editor(
    content="<h1>Hello World</h1>",
    width=800,
    height=600
)
        """, language="python")
    
    with tab3:
        st.code("""
# Custom configuration
slides = streamlit_theta.slide_editor(
    slides=initial_data,
    width=1200,
    height=800,
    key="custom_slides"
)

# Handle returned data
if slides:
    st.session_state.presentation = slides
    st.success("Slides updated!")
    
    # Export or process the data
    process_slides(slides)
        """, language="python")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 2rem;'>"
    "🎨 <strong>Streamlit Theta v1.0.0</strong> - Built with ❤️ by the Arcana Team"
    "</div>", 
    unsafe_allow_html=True
) 