"""
Streamlit Theta Demo - Comprehensive demonstration of all visual editors
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
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for all editors
if 'slide_data' not in st.session_state:
    st.session_state.slide_data = [
        {
            "id": "slide_1",
            "title": "Welcome Slide",
            "elements": [
                {
                    "type": "text",
                    "id": "text_1",
                    "content": "Welcome to Streamlit Theta",
                    "x": 50, "y": 100,
                    "width": 500, "height": 80,
                    "fontSize": 36, "fontFamily": "Arial",
                    "color": "#000000", "bold": True
                }
            ],
            "background": "#ffffff"
        }
    ]

if 'document_content' not in st.session_state:
    st.session_state.document_content = """
    <h1>Sample Document</h1>
    <p>This is a <strong>rich text document</strong> with formatting.</p>
    <ul>
        <li>Bullet point 1</li>
        <li>Bullet point 2</li>
    </ul>
    """

if 'spreadsheet_data' not in st.session_state:
    st.session_state.spreadsheet_data = [
        ["Product", "Price", "Quantity", "Total"],
        ["Widget A", "10.50", "5", "=B2*C2"],
        ["Widget B", "15.75", "3", "=B3*C3"],
        ["TOTAL", "", "", "=SUM(D2:D3)"]
    ]

if 'csv_data' not in st.session_state:
    st.session_state.csv_data = [
        ["Name", "Age", "City"],
        ["Alice", "25", "New York"],
        ["Bob", "30", "Los Angeles"],
        ["Charlie", "35", "Chicago"]
    ]

if 'csv_headers' not in st.session_state:
    st.session_state.csv_headers = ["Name", "Age", "City"]

# Sidebar navigation
st.sidebar.markdown("## 🎨 Streamlit Theta")
st.sidebar.markdown("Open source visual editors for Streamlit")

page = st.sidebar.selectbox(
    "Choose an Editor:",
    ["🏠 Home", "🎨 Slide Editor", "📝 Document Editor", "📊 Spreadsheet Editor", 
     "📋 CSV Editor", "🎵 Audio Editor", "🎬 Video Editor", "📈 Chart Editor",
     "🖼️ Image Editor", "📝 Form Builder", "🧠 Mind Map Editor", 
     "📐 Diagram Editor", "📧 Newsletter Editor", "ℹ️ About"]
)

# Main content
if page == "🏠 Home":
    st.markdown('<div class="main-header"><h1>🎨 Streamlit Theta</h1><p>Open Source Visual Editors Suite for Streamlit</p></div>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Welcome to Streamlit Theta!
    
    Streamlit Theta is a comprehensive suite of visual editors that enhance your Streamlit applications with professional-grade editing capabilities.
    
    **Key Features:**
    - 🎨 **Slide Editor**: Create beautiful presentations with drag-and-drop interface
    - 📝 **Document Editor**: Rich text editing with formatting tools
    - 📊 **Spreadsheet Editor**: Excel-like grid interface with formulas
    - 📋 **CSV Editor**: Data table editing with import/export
    - 🎵 **Audio Editor**: Audio playback with effects and controls
    - 🎬 **Video Editor**: Video player with filters and timeline
    - 📈 **Chart Editor**: Interactive chart and graph creation
    - 🖼️ **Image Editor**: Image manipulation and editing suite
    - 📝 **Form Builder**: Drag-and-drop form creation tool
    - 🧠 **Mind Map Editor**: Visual mind mapping and brainstorming
    - 📐 **Diagram Editor**: Flowchart and diagram creation
    - 📧 **Newsletter Editor**: Email and newsletter design tool
    
    **Why Streamlit Theta?**
    - 🚀 **Open Source**: Completely free and open source
    - 🔧 **Easy Integration**: Simple import and use in any Streamlit app
    - 🎯 **Professional Quality**: Production-ready editors with modern UI
    - 📦 **Modular Design**: Use only what you need
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚀 Quick Start")
        st.code("""
import streamlit as st
import streamlit_theta

# Use any editor
streamlit_theta.slide_editor()
streamlit_theta.document_editor()
streamlit_theta.chart_editor()
streamlit_theta.form_builder()
        """)
    
    with col2:
        st.markdown("### 📦 Installation")
        st.code("pip install streamlit-theta")

elif page == "🎨 Slide Editor":
    st.title("🎨 Slide Editor")
    st.markdown("Create beautiful presentations with drag-and-drop interface")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        slides_result = streamlit_theta.slide_editor(
            slides=st.session_state.slide_data,
            width=800,
            height=600
        )
        
        if slides_result:
            st.session_state.slide_data = slides_result
    
    with col2:
        st.markdown("### Features")
        st.markdown("""
        - **Drag & Drop**: Move elements around
        - **Text Editing**: Rich text formatting
        - **Multiple Slides**: Create presentations
        - **Professional Output**: Export as JSON
        """)
        
        if st.button("Download Slides"):
            st.download_button(
                label="📥 Download Presentation",
                data=json.dumps(st.session_state.slide_data, indent=2),
                file_name="presentation.json",
                mime="application/json"
            )

elif page == "📝 Document Editor":
    st.title("📝 Document Editor")
    st.markdown("Rich text editing with professional formatting")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        document_result = streamlit_theta.document_editor(
            content=st.session_state.document_content,
            width=800,
            height=600
        )
        
        if document_result:
            st.session_state.document_content = document_result
    
    with col2:
        st.markdown("### Features")
        st.markdown("""
        - **WYSIWYG Editing**: What you see is what you get
        - **Rich Formatting**: Bold, italic, lists, headers
        - **Professional Layout**: A4 page format
        - **Export Ready**: Download as HTML
        """)

elif page == "📊 Spreadsheet Editor":
    st.title("📊 Spreadsheet Editor")
    st.markdown("Excel-like spreadsheet with formulas and functions")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        spreadsheet_result = streamlit_theta.spreadsheet_editor(
            data=st.session_state.spreadsheet_data,
            width=900,
            height=500
        )
        
        if spreadsheet_result:
            st.session_state.spreadsheet_data = spreadsheet_result
    
    with col2:
        st.markdown("### Features")
        st.markdown("""
        - **Formula Support**: Excel-like formulas
        - **Cell Navigation**: Arrow key support
        - **Add/Remove**: Dynamic rows and columns
        - **Export**: Download as CSV
        """)

elif page == "📋 CSV Editor":
    st.title("📋 CSV Editor")
    st.markdown("Data table editor with import/export functionality")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        csv_result = streamlit_theta.csv_editor(
            data=st.session_state.csv_data,
            headers=st.session_state.csv_headers,
            width=900,
            height=500
        )
        
        if csv_result:
            st.session_state.csv_data = csv_result.get('data', [])
            st.session_state.csv_headers = csv_result.get('headers', [])
    
    with col2:
        st.markdown("### Features")
        st.markdown("""
        - **Editable Cells**: Direct data editing
        - **Header Management**: Customize column names
        - **Import/Export**: CSV file support
        - **Data Validation**: Clean data formatting
        """)

elif page == "🎵 Audio Editor":
    st.title("🎵 Audio Editor")
    st.markdown("Audio player with effects and playback controls")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        audio_result = streamlit_theta.audio_editor(
            width=800,
            height=400
        )
    
    with col2:
        st.markdown("### Features")
        st.markdown("""
        - **File Upload**: Support for MP3, WAV, OGG
        - **Playback Controls**: Play, pause, seek
        - **Audio Effects**: Volume, speed, pitch
        - **Waveform**: Visual audio representation
        """)

elif page == "🎬 Video Editor":
    st.title("🎬 Video Editor")
    st.markdown("Video player with filters and timeline controls")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        video_result = streamlit_theta.video_editor(
            width=900,
            height=600
        )
    
    with col2:
        st.markdown("### Features")
        st.markdown("""
        - **Video Upload**: MP4, WebM support
        - **Timeline Controls**: Scrubbing and seeking
        - **Visual Effects**: Brightness, contrast, filters
        - **Color Filters**: Grayscale, sepia, blur
        """)

elif page == "📈 Chart Editor":
    st.title("📈 Chart Editor")
    st.markdown("Interactive chart and graph creation tool")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        chart_result = streamlit_theta.chart_editor(
            width=900,
            height=600
        )
    
    with col2:
        st.markdown("### Features")
        st.markdown("""
        - **Multiple Chart Types**: Line, bar, pie, scatter
        - **Interactive Data Input**: Real-time editing
        - **Customizable Styling**: Colors, labels, legends
        - **Export Options**: Chart data and configuration
        """)

elif page == "🖼️ Image Editor":
    st.title("🖼️ Image Editor")
    st.markdown("Comprehensive image manipulation and editing suite")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        image_result = streamlit_theta.image_editor(
            width=800,
            height=600
        )
    
    with col2:
        st.markdown("### Features")
        st.markdown("""
        - **Image Upload**: Support for common formats
        - **Basic Editing**: Crop, resize, rotate
        - **Filters & Effects**: Brightness, contrast, saturation
        - **Drawing Tools**: Annotations and markup
        """)

elif page == "📝 Form Builder":
    st.title("📝 Form Builder")
    st.markdown("Drag-and-drop form creation tool")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        form_result = streamlit_theta.form_builder(
            width=900,
            height=700
        )
    
    with col2:
        st.markdown("### Features")
        st.markdown("""
        - **Drag & Drop Elements**: Input, select, checkbox, radio
        - **Real-time Preview**: Live form rendering
        - **Validation Rules**: Field validation setup
        - **Custom Styling**: Theme and appearance options
        """)

elif page == "🧠 Mind Map Editor":
    st.title("🧠 Mind Map Editor")
    st.markdown("Visual mind mapping and brainstorming tool")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        mindmap_result = streamlit_theta.mindmap_editor(
            width=1000,
            height=700
        )
    
    with col2:
        st.markdown("### Features")
        st.markdown("""
        - **Interactive Nodes**: Create and edit ideas
        - **Hierarchical Structure**: Parent-child relationships
        - **Customizable Styling**: Colors, shapes, fonts
        - **Zoom & Pan**: Navigate large mind maps
        """)

elif page == "📐 Diagram Editor":
    st.title("📐 Diagram Editor")
    st.markdown("Professional flowchart and diagram creation tool")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        diagram_result = streamlit_theta.diagram_editor(
            width=1000,
            height=700
        )
    
    with col2:
        st.markdown("### Features")
        st.markdown("""
        - **Flowchart Shapes**: Standard diagram elements
        - **Connectors**: Link shapes with arrows
        - **Multiple Templates**: Org chart, network, process
        - **Auto-layout**: Alignment and spacing tools
        """)

elif page == "📧 Newsletter Editor":
    st.title("📧 Newsletter Editor")
    st.markdown("Email and newsletter design tool with professional templates")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        newsletter_result = streamlit_theta.newsletter_editor(
            width=900,
            height=800
        )
    
    with col2:
        st.markdown("### Features")
        st.markdown("""
        - **Professional Templates**: Ready-to-use designs
        - **Drag & Drop Blocks**: Content elements
        - **Rich Text Editing**: Formatted content
        - **Mobile Responsive**: Optimized for all devices
        """)

elif page == "ℹ️ About":
    st.title("ℹ️ About Streamlit Theta")
    
    st.markdown("""
    ### 🎯 Mission
    
    Streamlit Theta aims to provide professional-grade visual editing capabilities to the Streamlit ecosystem, making it easier for developers to create rich, interactive applications.
    
    ### ✨ Features Overview
    
    Our suite includes **12 comprehensive editors**:
    
    1. **🎨 Slide Editor** - PowerPoint-style presentations
    2. **📝 Document Editor** - Word-style document editing  
    3. **📊 Spreadsheet Editor** - Excel-like spreadsheet functionality
    4. **📋 CSV Editor** - Data table manipulation
    5. **🎵 Audio Editor** - Audio playback and effects
    6. **🎬 Video Editor** - Video player with filters
    7. **📈 Chart Editor** - Interactive data visualization
    8. **🖼️ Image Editor** - Image manipulation tools
    9. **📝 Form Builder** - Dynamic form creation
    10. **🧠 Mind Map Editor** - Visual brainstorming
    11. **📐 Diagram Editor** - Flowcharts and diagrams
    12. **📧 Newsletter Editor** - Email template design
    
    ### 🚀 Why Choose Streamlit Theta?
    
    - **🔓 Open Source**: Completely free and open source
    - **🎯 Production Ready**: Tested and reliable
    - **🔧 Easy Integration**: Simple pip install
    - **📱 Responsive**: Works on all devices
    - **💾 Export Functionality**: Download your work
    - **🎨 Professional UI**: Modern and intuitive design
    
    ### 📦 Installation
    
    ```bash
    pip install streamlit-theta
    ```
    
    ### 🤝 Contributing
    
    We welcome contributions! Visit our GitHub repository to get started.
    
    ### 📄 License
    
    This project is licensed under the Apache License 2.0.
    """)

# Footer
st.markdown("---")
st.markdown("**Streamlit Theta** - Professional Visual Editors for Streamlit | Open Source | Apache 2.0 License")
