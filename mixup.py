# mypy: skip-file
# flake8: noqa
import streamlit as st
import os
import datetime
import re
import io
import requests
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

import dashscope
from dashscope import Generation

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
from pptx.dml.color import RGBColor
from docx import Document
from docx.shared import Pt as DocxPt, RGBColor as DocxRGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH  # type: ignore

from response import openai_api_call
from fiber import FiberDBMS
from config import GENERATED_FILES_DIR
from openai.types.chat import ChatCompletionMessageParam

# Import our custom slide editor
try:
    from streamlit_theta.editor.slide import*  # type: ignore
    THETA_AVAILABLE = True
except ImportError:
    THETA_AVAILABLE = False

# --- State Management ---

def init_presentation_state(force_reset=False):
    """Initializes or resets the session state for the presentation generator."""
    if force_reset:
        st.session_state.presentation_step = "initial"
        st.session_state.presentation_topic = ""
        st.session_state.presentation_outline = ""
        st.session_state.presentation_content = []
        return

    if 'presentation_step' not in st.session_state:
        st.session_state.presentation_step = "initial"
    if 'presentation_topic' not in st.session_state:
        st.session_state.presentation_topic = ""
    if 'presentation_outline' not in st.session_state:
        st.session_state.presentation_outline = ""
    if 'presentation_content' not in st.session_state:
        st.session_state.presentation_content = []

# --- Helper Functions ---

def get_context_for_topic(dbms, topic):
    """Extracts keywords from a topic and queries the database for relevant context."""
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(topic)
    keywords = [word for word in words if word.lower() not in stop_words and word.isalpha()]
    
    if not keywords:
        return "" # Return empty string if no keywords are found

    results = dbms.query(" ".join(keywords), top_n=10)
    
    if not results:
        return "" # Return empty string if no context is found

    context = "Here is some relevant information from your documents:\n\n"
    for result in results:
        context += f"--- Start of content from {result['name']} ---\n"
        context += f"{result['content']}\n"
        context += f"--- End of content from {result['name']} ---\n\n"
    return context

def parse_outline_to_slides(outline_text):
    """Parses a markdown-formatted outline into a list of slide dictionaries."""
    slides = []
    current_slide = None
    for line in outline_text.splitlines():
        line = line.strip()
        if line.startswith("####"):
            if current_slide:
                slides.append(current_slide)
            current_slide = {"title": line.lstrip("# ").strip(), "points": []}
        elif line.startswith("-") and current_slide is not None:
            current_slide["points"].append(line.lstrip("- ").strip())
    if current_slide:
        slides.append(current_slide)
    return slides

def generate_image_from_prompt(api_key: str, prompt: str) -> io.BytesIO | None:
    """Generates an image using Dashscope's API and returns it as a BytesIO object."""
    dashscope.api_key = api_key
    try:
        response_generator = Generation.call(
            model='wanx-v1',
            prompt=prompt,
            n=1,
            size='1024*1024'
        )
        # The response is a generator, so we iterate through it
        for response in response_generator:
            # The API can yield a string on error, so we must check the type
            if not hasattr(response, 'status_code'):
                st.warning(f"Image generation API returned an unexpected response: {response}")
                return None

            if response.status_code == 200 and response.output and response.output.results:
                image_url = response.output.results[0].url
                # Download the image from the URL
                image_response = requests.get(image_url, stream=True)
                image_response.raise_for_status()
                return io.BytesIO(image_response.content)
            else:
                st.warning(f"Image generation failed. Status: {response.status_code}, Message: {response.message}")
                return None
    except Exception as e:
        st.error(f"An unexpected error occurred during the image generation process: {e}")
        return None

def add_formatted_text_to_shape(shape, text):
    """
    Parses HTML content and converts it to PowerPoint formatted text.
    This handles both custom formatting tags and basic HTML.
    """
    text_frame = shape.text_frame
    text_frame.clear()  # Clear existing content and paragraphs

    # Convert HTML to a more readable format for PowerPoint
    # Remove HTML tags but preserve line breaks and basic formatting
    import html
    
    # Basic HTML to text conversion
    text = text.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
    text = text.replace('<p>', '').replace('</p>', '\n')
    text = text.replace('<div>', '').replace('</div>', '\n')
    text = text.replace('<ul>', '').replace('</ul>', '')
    text = text.replace('<ol>', '').replace('</ol>', '')
    text = text.replace('<li>', '• ').replace('</li>', '\n')
    
    # Handle bold, italic, underline
    text = re.sub(r'<strong>(.*?)</strong>', r'[font bold=true]\1[/font]', text)
    text = re.sub(r'<b>(.*?)</b>', r'[font bold=true]\1[/font]', text)
    text = re.sub(r'<em>(.*?)</em>', r'[font italic=true]\1[/font]', text)
    text = re.sub(r'<i>(.*?)</i>', r'[font italic=true]\1[/font]', text)
    text = re.sub(r'<u>(.*?)</u>', r'[font underline=true]\1[/font]', text)
    
    # Remove any remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    
    # Clean up multiple newlines
    text = re.sub(r'\n\s*\n', '\n', text)
    text = text.strip()

    # Set default paragraph styling
    if not text_frame.paragraphs:
        p = text_frame.add_paragraph()
    else:
        p = text_frame.paragraphs[0]
    p.font.name = 'Calibri'
    p.font.size = Pt(18)
    
    # --- Alignment State ---
    # Start with default alignment. This will be updated by block tags.
    current_alignment = PP_ALIGN.LEFT

    # Process each line of the converted content
    for line in text.splitlines():
        
        # Check for block-level alignment tags on their own lines
        align_open_match = re.match(r"^\s*\[align=(center|right|left|justify)\]\s*$", line, re.I)
        align_close_match = re.match(r"^\s*\[/align\]\s*$", line, re.I)

        if align_open_match:
            # Set the current alignment for subsequent paragraphs
            alignment_str = align_open_match.group(1).upper()
            current_alignment = getattr(PP_ALIGN, alignment_str, PP_ALIGN.LEFT)
            continue # Don't print this line
        
        if align_close_match:
            # Reset alignment to default
            current_alignment = PP_ALIGN.LEFT
            continue # Don't print this line
        
        # --- Create and Align Paragraph ---
        # Add a new paragraph for the content line
        p = text_frame.add_paragraph()
        p.alignment = current_alignment

        # --- Inline Formatting ---
        # Parts are split by font tags. The text between tags gets styled.
        parts = re.split(r"(\[font[^\]]*\]|\[/font\])", line)
        style_stack = [{
            'bold': False, 'italic': False, 'underline': False,
            'name': 'Calibri', 'size': 18, 'color': RGBColor(0, 0, 0)
        }]

        for part in parts:
            if not part:
                continue

            # --- Handle Tags ---
            if part.startswith('[font'):
                # New, more robust parsing logic
                attrs = {}
                # Isolate the attribute string, e.g., "size=24 bold=true"
                attr_string = part[part.find(' '):-1].strip()
                
                # Use findall to get key-value pairs
                pairs = re.findall(r'(\w+)=(".*?"|\'.*?\'|[^\s\']*)', attr_string)
                
                for key, value in pairs:
                    # Remove quotes from the value if they exist
                    attrs[key.lower()] = value.strip("'\"")

                # Apply the parsed styles
                new_style = style_stack[-1].copy()
                if 'bold' in attrs: new_style['bold'] = attrs['bold'].lower() == 'true'
                if 'italic' in attrs: new_style['italic'] = attrs['italic'].lower() == 'true'
                if 'underline' in attrs: new_style['underline'] = attrs['underline'].lower() == 'true'
                if 'name' in attrs: new_style['name'] = attrs['name']
                if 'size' in attrs:
                    try:
                        new_style['size'] = int(attrs['size'])
                    except ValueError:
                        print(f"Warning: Could not parse font size '{attrs['size']}'. Using default.")
                if 'color' in attrs:
                    try:
                        new_style['color'] = RGBColor.from_string(attrs['color'].lstrip('#'))
                    except (ValueError, KeyError):
                         print(f"Warning: Could not parse color '{attrs['color']}'. Using default.")

                style_stack.append(new_style)

            elif part == '[/font]':
                # End of a style block, pop from the stack to revert to the previous style
                if len(style_stack) > 1:
                    style_stack.pop()

            # --- Handle Text ---
            else:
                # This is plain text, apply the current style from the top of the stack
                run = p.add_run()
                run.text = part
                
                current_style = style_stack[-1]
                font = run.font
                font.name = current_style['name']
                font.size = Pt(current_style['size'])
                font.bold = current_style['bold']
                font.italic = current_style['italic']
                font.underline = current_style['underline']
                font.color.rgb = current_style['color']

# --- Document Generation ---

def create_presentation_from_content(presentation_content, topic, api_key):
    """Creates a PowerPoint presentation from a list of slide content, including images."""
    # Load template if available (located in plugin/templates/template.pptx)
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'template.pptx')
    if os.path.exists(template_path):
        prs = Presentation(template_path)
    else:
        prs = Presentation()
    # Use built-in Title and Content slide layout for consistent formatting
    content_slide_layout = prs.slide_layouts[1]

    # Create slides using the selected layout
    for idx, slide_data in enumerate(presentation_content, start=1):
        slide = prs.slides.add_slide(content_slide_layout)
        # Set slide title
        slide.shapes.title.text = slide_data['title']  # type: ignore
        title_p = slide.shapes.title.text_frame.paragraphs[0]  # type: ignore
        title_p.font.bold = True
        title_p.font.size = Pt(32)
        title_p.alignment = PP_ALIGN.CENTER

        # Prepare and add main content
        content_lines = [l for l in slide_data['content'].splitlines() if not l.startswith('[image')]
        text_content = "\n".join(content_lines)
        if text_content.strip():
            # Use placeholder for content and clear existing content
            content_shape = slide.shapes.placeholders[1]  # type: ignore
            content_shape.text_frame.clear()  # type: ignore
            content_shape.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE  # type: ignore
            add_formatted_text_to_shape(content_shape, text_content)

    # Add slide numbers to each slide
    for num, slide in enumerate(prs.slides, start=1):
        number_box = slide.shapes.add_textbox(
            prs.slide_width - Inches(1.0),  # type: ignore
            prs.slide_height - Inches(0.5),  # type: ignore
            Inches(1.0),
            Inches(0.5)
        )
        num_tf = number_box.text_frame
        p = num_tf.paragraphs[0]
        p.text = str(num)
        p.font.size = Pt(12)
        p.alignment = PP_ALIGN.RIGHT

    # Save presentation
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '_')).rstrip()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Presentation_{safe_topic}_{timestamp}.pptx"
    
    os.makedirs(GENERATED_FILES_DIR, exist_ok=True)
    file_path = os.path.join(GENERATED_FILES_DIR, filename)
    prs.save(file_path)
    return file_path

def create_document_from_content(presentation_content, topic):
    """Creates a Word document from a list of slide content."""
    doc = Document()
    doc.add_heading(f"Report on: {topic}", level=0)
    for slide_data in presentation_content:
        doc.add_heading(slide_data['title'], level=1)
        # Use the new formatter for the document content
        add_formatted_text_to_document(doc, slide_data['content'])
        doc.add_paragraph() # Add some space

    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '_')).rstrip()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Document_{safe_topic}_{timestamp}.docx"
    
    os.makedirs(GENERATED_FILES_DIR, exist_ok=True)
    file_path = os.path.join(GENERATED_FILES_DIR, filename)
    doc.save(file_path)
    return file_path

def add_formatted_text_to_document(doc, text):
    """
    Parses a custom-formatted string and adds it to a Word document,
    preserving formatting like bold, italics, underline, color, and alignment.
    """
    current_alignment = WD_ALIGN_PARAGRAPH.LEFT

    for line in text.splitlines():
        # Skip image tags and empty lines
        if line.startswith('[image') or not line.strip():
            continue

        align_open_match = re.match(r"^\s*\[align=(center|right|left|justify)\]\s*$", line, re.I)
        align_close_match = re.match(r"^\s*\[/align\]\s*$", line, re.I)

        if align_open_match:
            alignment_str = align_open_match.group(1).upper()
            if alignment_str == 'LEFT': current_alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif alignment_str == 'CENTER': current_alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif alignment_str == 'RIGHT': current_alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif alignment_str == 'JUSTIFY': current_alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            continue
        
        if align_close_match:
            current_alignment = WD_ALIGN_PARAGRAPH.LEFT
            continue

        p = doc.add_paragraph()
        p.alignment = current_alignment

        parts = re.split(r"(\[font[^\]]*\]|\[/font\])", line)
        style_stack = [{'bold': None, 'italic': None, 'underline': None, 'name': None, 'size': None, 'color': None}]

        for part in parts:
            if not part: continue

            if part.startswith('[font'):
                new_style = style_stack[-1].copy()
                attrs = {}
                attr_string = part[part.find(' '):-1].strip()
                pairs = re.findall(r'(\w+)=(".*?"|\'.*?\'|[^\s\']*)', attr_string)
                for key, value in pairs:
                    attrs[key.lower()] = value.strip("'\"")

                if 'bold' in attrs: new_style['bold'] = attrs['bold'].lower() == 'true'
                if 'italic' in attrs: new_style['italic'] = attrs['italic'].lower() == 'true'
                if 'underline' in attrs: new_style['underline'] = attrs['underline'].lower() == 'true'
                if 'name' in attrs: new_style['name'] = attrs['name']
                if 'size' in attrs:
                    try: new_style['size'] = DocxPt(int(attrs['size']))  # type: ignore
                    except ValueError: pass
                if 'color' in attrs:
                    try: new_style['color'] = DocxRGBColor.from_string(attrs['color'].replace("#", ""))  # type: ignore
                    except (ValueError, KeyError): pass
                style_stack.append(new_style)

            elif part == '[/font]':
                if len(style_stack) > 1:
                    style_stack.pop()

            else:
                run = p.add_run()
                run.text = part
                current_style = style_stack[-1]
                font = run.font
                if current_style['bold'] is not None: font.bold = current_style['bold']
                if current_style['italic'] is not None: font.italic = current_style['italic']
                if current_style['underline'] is not None: font.underline = current_style['underline']
                if current_style['name'] is not None: font.name = current_style['name']
                if current_style['size'] is not None: font.size = current_style['size']  # type: ignore
                if current_style['color'] is not None: font.color.rgb = current_style['color']  # type: ignore

# --- Streamlit Theta Helper Functions ---

def convert_to_theta_format(presentation_content):
    """Convert presentation content to streamlit-theta format."""
    theta_slides = []
    for i, slide in enumerate(presentation_content):
        # Parse the content to extract formatted text elements
        elements = parse_slide_content_to_elements(slide['content'], i)
        
        theta_slide = {
            "id": f"slide_{i+1}",
            "title": slide['title'],
            "elements": elements,
            "background": "#ffffff",
            "layout": "content"
        }
        theta_slides.append(theta_slide)
    return theta_slides

def parse_slide_content_to_elements(content, slide_index):
    """Parse slide content and convert to theta elements."""
    elements = []
    
    # Remove image tags and clean content
    lines = [line for line in content.splitlines() if not line.startswith('[image')]
    text_content = "\n".join(lines)
    
    # Create a main text element
    if text_content.strip():
        element = {
            "type": "text",
            "id": f"content_{slide_index}",
            "content": text_content,
            "x": 50,
            "y": 120,
            "width": 600,
            "height": 350,
            "fontSize": 18,
            "fontFamily": "Arial",
            "color": "#000000",
            "bold": False,
            "italic": False,
            "underline": False,
            "alignment": "left"
        }
        elements.append(element)
    
    return elements

def create_blank_theta_slide(slide_number):
    """Create a blank slide in theta format."""
    return {
        "id": f"slide_{slide_number}",
        "title": f"New Slide {slide_number}",
        "elements": [
            {
                "type": "text",
                "id": f"content_{slide_number}",
                "content": "Click to edit this text...",
                "x": 50,
                "y": 120,
                "width": 600,
                "height": 350,
                "fontSize": 18,
                "fontFamily": "Arial",
                "color": "#000000",
                "bold": False,
                "italic": False,
                "underline": False,
                "alignment": "left"
            }
        ],
        "background": "#ffffff",
        "layout": "content"
    }

def update_presentation_content_from_theta(presentation_content, theta_slides, slide_index):
    """Update presentation content from theta slide data."""
    if slide_index < len(theta_slides) and slide_index < len(presentation_content):
        theta_slide = theta_slides[slide_index]
        
        # Update title
        presentation_content[slide_index]["title"] = theta_slide.get("title", "")
        
        # Extract text content from elements
        content_parts = []
        for element in theta_slide.get("elements", []):
            if element["type"] == "text" and element.get("content"):
                content_parts.append(element["content"])
        
        # Update content
        presentation_content[slide_index]["content"] = "\n".join(content_parts)

def apply_theme_to_slides(theta_slides, theme):
    """Apply a color theme to all slides."""
    theme_colors = {
        "Default": {"background": "#ffffff", "text": "#000000"},
        "Dark": {"background": "#2b2b2b", "text": "#ffffff"},
        "Blue": {"background": "#e3f2fd", "text": "#0d47a1"},
        "Green": {"background": "#e8f5e8", "text": "#1b5e20"},
        "Purple": {"background": "#f3e5f5", "text": "#4a148c"}
    }
    
    colors = theme_colors.get(theme, theme_colors["Default"])
    
    for slide in theta_slides:
        slide["background"] = colors["background"]
        for element in slide.get("elements", []):
            if element["type"] == "text":
                element["color"] = colors["text"]

def apply_global_font_settings(theta_slides, font_family, font_size):
    """Apply global font settings to all text elements."""
    for slide in theta_slides:
        for element in slide.get("elements", []):
            if element["type"] == "text":
                element["fontFamily"] = font_family
                element["fontSize"] = font_size

# --- UI for Modes ---

def render_presentation_mode(dbms):
    st.header("✨ Presentation Generator")
    init_presentation_state()

    # STEP 1: Get topic and generate outline
    if st.session_state.presentation_step == "initial":
        st.subheader("Step 1: Choose a Topic")
        topic = st.text_input("What is your presentation about?", key="ppt_topic_input")
        if st.button("Generate Outline") and topic:
            st.session_state.presentation_topic = topic
            with st.spinner("Analyzing your documents and creating an outline..."):
                context = get_context_for_topic(dbms, topic)
                prompt = (f"Generate a slide-by-slide outline for a presentation on '{topic}'. "
                          f"Format it in markdown with each slide title starting with '#### ' and bullet points with '- '. "
                          f"Base the outline on the following information from my documents:\n\n{context}")
                
                # Using a placeholder for the system message
                outline_messages: list[ChatCompletionMessageParam] = [
                    {"role": "system", "content": "You are an AI assistant that creates presentation outlines."},
                    {"role": "user", "content": prompt}
                ]
                
                outline = "".join(list(openai_api_call(outline_messages, "Normal")))
                st.session_state.presentation_outline = outline
                st.session_state.presentation_step = "outline_generated"
                st.rerun()

    # STEP 2: Review and edit outline
    elif st.session_state.presentation_step == "outline_generated":
        st.subheader("Step 2: Edit Outline Visually")
        # Convert markdown outline to theta format slides
        parsed = parse_outline_to_slides(st.session_state.presentation_outline)
        theta_slides = [
            {
                "id": f"slide_{i+1}",
                "title": s['title'],
                "elements": [
                    {
                        "type": "text",
                        "id": f"outline_{i}",
                        "content": "\n".join(s['points']),
                        "x": 50, "y": 100,
                        "width": 600, "height": 350,
                        "fontSize": 18,
                        "fontFamily": "Arial",
                        "color": "#000000"
                    }
                ],
                "background": "#ffffff",
                "layout": "content"
            }
            for i, s in enumerate(parsed)
        ]
        # Visual outline editor
        st.markdown(
            '<div style="width:100%; max-width:900px; margin:auto; overflow-x:auto;">',
            unsafe_allow_html=True
        )
        edited_theta = theta_slide_editor(
            slides=theta_slides,
            width=900,
            height=600,
            key="theta_outline_editor"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Generate Full Slide Content", key="generate_content_button"):
            if edited_theta:
                # Convert edited theta slides back to outline and content placeholders
                new_content = []
                new_outline = ""
                for slide in edited_theta:
                    title = slide.get('title', '')
                    new_outline += f"#### {title}\n"
                    points = []
                    # extract bullet points from text elements
                    for el in slide.get('elements', []):
                        if el['type'] == 'text':
                            for line in el['content'].split('\n'):
                                points.append(line)
                                new_outline += f"- {line}\n"
                    new_outline += "\n"
                    new_content.append({"title": title, "content": ""})
                # Persist edited outline and placeholder content
                st.session_state.presentation_outline = new_outline
                st.session_state.presentation_content = new_content
                st.session_state.theta_slides = edited_theta
                st.session_state.presentation_step = "content_generated"
                st.rerun()

    # STEP 3: Review & Edit Final Slide Content
    elif st.session_state.presentation_step == "content_generated":
        st.subheader("Step 3: Finalize Slides Visually")
        # Ensure theta_slides is initialized
        if 'theta_slides' not in st.session_state or not st.session_state.theta_slides:
            st.session_state.theta_slides = convert_to_theta_format(st.session_state.presentation_content)
        # Full-slide visual editor
        st.markdown(
            '<div style="width:100%; max-width:900px; margin:auto; overflow-x:auto;">',
            unsafe_allow_html=True
        )
        updated_slides = theta_slide_editor(
            slides=st.session_state.theta_slides,
            width=900,
            height=600,
            key="theta_final_editor"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        if updated_slides:
            # Update session state with edits
            st.session_state.theta_slides = updated_slides
            # Sync edited slides back to presentation_content
            new_content = []
            for slide in updated_slides:
                # combine all text elements content
                text_elems = [el['content'] for el in slide.get('elements', []) if el['type']=='text']
                new_content.append({'title': slide.get('title',''), 'content': '\n'.join(text_elems)})
            st.session_state.presentation_content = new_content
        # After editing, proceed to export
        st.markdown("---")
    
        topic = st.session_state.presentation_topic
        col1, col2 = st.columns(2)
        with col1:
            api_key = os.getenv("DASHSCOPE_API_KEY") or ""
            if not api_key and any("[image query" in s['content'] for s in st.session_state.presentation_content):
                st.warning("An image was requested but no Dashscope API key was found. The PPT will be generated without images. Set DASHSCOPE_API_KEY to enable images.")
            
            ppt_path = create_presentation_from_content(st.session_state.presentation_content, topic, api_key)
            with open(ppt_path, "rb") as f:
                st.download_button(
                    "⬇️ Download PowerPoint",
                    f,
                    file_name=os.path.basename(ppt_path),
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                )
        with col2:
            doc_path = create_document_from_content(st.session_state.presentation_content, topic)
            with open(doc_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Word Document",
                    f,
                    file_name=os.path.basename(doc_path),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

        if st.button("✨ Create Another Presentation"):
            init_presentation_state(force_reset=True)
            st.rerun()

def render_study_guide_mode():
    st.header("📚 Study Guide Generator")
    st.info("This feature is coming soon! It will help you create detailed study guides from your documents.")

def render_flashcard_mode():
    st.header("📇 Q&A Flashcard Generator")
    st.info("This feature is coming soon! It will extract question-answer pairs from your files to help you study.")

def mixup_page():
    st.title('Arcana Mixup')
    st.write("Your intelligent assistant for creating documents, presentations, and study materials.")

    # Check if the database is uninitialized or has no indexed entries.
    if 'dbms' not in st.session_state or not isinstance(st.session_state.dbms, FiberDBMS) or st.session_state.dbms.is_empty():
        st.info("No indexed files found. Content will be generated from general knowledge. To use your own documents as context, please go to the 'Files' page and index them first.")
        # If the dbms object doesn't exist at all, create an empty one to prevent errors.
        if 'dbms' not in st.session_state or not isinstance(st.session_state.dbms, FiberDBMS):
            st.session_state.dbms = FiberDBMS()

    dbms = st.session_state.dbms

    mode = st.radio(
        "Choose a generation mode:",
        ["Presentation", "Study Guide", "Q&A Flashcards"],
        key='mixup_mode_selector',
        horizontal=True,
    )
    
    st.markdown("---")

    if mode == "Presentation":
        render_presentation_mode(dbms)
    elif mode == "Study Guide":
        render_study_guide_mode()
    elif mode == "Q&A Flashcards":
        render_flashcard_mode()

if __name__ == "__main__":
    mixup_page()
