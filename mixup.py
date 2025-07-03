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

from response import openai_api_call
from fiber import FiberDBMS
from config import GENERATED_FILES_DIR
from openai.types.chat import ChatCompletionMessageParam
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.text import MSO_AUTO_SIZE
from docx import Document
from docx.shared import Pt as DocxPt, RGBColor as DocxRGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH  # type: ignore

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

def add_formatted_text_to_shape(shape, text: str):
    """
    Parses text with formatting tags and adds bullet points and alignment.
    """
    tf = shape.text_frame
    tf.clear()
    current_alignment = PP_ALIGN.LEFT
    default_size = Pt(18)
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Alignment tags
        if stripped.lower() == '[align=center]':
            current_alignment = PP_ALIGN.CENTER
            continue
        if stripped.lower() == '[/align]':
            current_alignment = PP_ALIGN.LEFT
            continue
        # Font size tags
        size_match = re.match(r"\[font size=(\d+)\]", stripped, re.I)
        if size_match:
            default_size = Pt(int(size_match.group(1)))
            continue
        # Clean tags
        clean_line = re.sub(r"\[[^\]]+\]", '', stripped)
        p = tf.add_paragraph()
        if clean_line.startswith('- '):
            p.text = clean_line[2:]
            p.level = 1
        else:
            p.text = clean_line
        p.alignment = current_alignment
        p.font.size = default_size
    return

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

        # Parse and separate main content and speaker notes
        content_lines, notes_lines = split_content_and_notes(slide_data['content'], slide_data['title'])
        # Remove duplicate title lines
        content_lines = [l for l in content_lines if l.strip() and l.strip() != slide_data['title']]
        # Remove image tags
        content_lines = [l for l in content_lines if not l.startswith('[image]')]
        text_content = "\n".join(content_lines)
        if text_content.strip():
            # Use placeholder for content and clear existing content
            content_shape = slide.shapes.placeholders[1]  # type: ignore
            content_shape.text_frame.clear()  # type: ignore
            content_shape.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE  # type: ignore
            add_formatted_text_to_shape(content_shape, text_content)
        # Add speaker notes if present
        if notes_lines:
            notes_slide = slide.notes_slide  # type: ignore
            notes_tf = notes_slide.notes_text_frame
            notes_tf.clear()
            for note_line in notes_lines:
                notes_tf.add_paragraph().text = note_line

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

def split_content_and_notes(raw_content: str, title: str) -> tuple[list[str], list[str]]:
    """
    Splits raw slide content into main content lines and speaker notes.
    Lines after 'Speaker Notes:' or 'Notes:' are treated as notes.
    """
    content_lines = []
    notes_lines = []
    notes_section = False
    for line in raw_content.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith('speaker notes:') or stripped.lower().startswith('notes:'):
            notes_section = True
            continue
        if notes_section:
            notes_lines.append(line)
        else:
            content_lines.append(line)
    return content_lines, notes_lines

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
                
                outline = "".join(list(openai_api_call(outline_messages, "Idx")))
                st.session_state.presentation_outline = outline
                st.session_state.presentation_step = "outline_generated"
                st.rerun()

    # STEP 2: Review and edit outline
    elif st.session_state.presentation_step == "outline_generated":
        st.subheader("Step 2: Edit Outline")
        outline = st.text_area("Edit the Markdown outline", value=st.session_state.presentation_outline, height=300)
        if st.button("Confirm Outline"):
            st.session_state.presentation_outline = outline
            parsed = parse_outline_to_slides(outline)
            # initialize content list and start page-by-page generation
            st.session_state.generated_content = []
            st.session_state.total_slides = len(parsed)
            st.session_state.parsed_slides = parsed
            st.session_state.slide_gen_index = 0
            st.session_state.presentation_step = "generating_slide_content"
            st.rerun()

    # STEP 3: Auto-generate all slide content
    elif st.session_state.presentation_step == "generating_slide_content":
        parsed = st.session_state.parsed_slides
        total = len(parsed)
        generated = []
        st.subheader(f"Step 3: Generating {total} slides...")
        progress = st.progress(0)
        with st.spinner("Generating slide content..."):
            for i, slide_info in enumerate(parsed):
                # Enhanced prompt: include formatting and centering instructions
                prompt = (
                    f"Write detailed speaker notes and bullet points for a slide titled '{slide_info['title']}'. "
                    f"Use '[align=center]' tags to center the slide title and bullet points prefixed with '- '. "
                    f"Include font size tags (e.g., '[font size=18]') where appropriate. "
                    f"Points: {', '.join(slide_info['points'])}."
                )
                messages = [
                    {"role": "system", "content": "You are an AI assistant that outputs slide content using custom formatting tags."},
                    {"role": "user", "content": prompt}
                ]
                content = "".join(openai_api_call(messages, "Idx"))
                generated.append({"title": slide_info['title'], "content": content})
                progress.progress(int((i+1)/total * 100))
        # Persist generated content and move to review
        st.session_state.presentation_content = generated
        st.session_state.presentation_step = "content_generated"
        # Clean up temporary state
        for key in ('generated_content','parsed_slides','total_slides','slide_gen_index'):
            st.session_state.pop(key, None)
        st.rerun()

    # STEP 4: Review & Edit Final Slide Content
    elif st.session_state.presentation_step == "content_generated":
        st.subheader("Step 4: Edit Slide Content")
        new_content = []
        for idx, slide in enumerate(st.session_state.presentation_content):
            st.markdown(f"**Slide {idx+1}: {slide['title']}**")
            content = st.text_area(f"Content for slide {idx+1}", value=slide['content'], key=f"slide_{idx}_content", height=200)
            new_content.append({"title": slide['title'], "content": content})
        if st.button("Generate Presentation"):
            st.session_state.presentation_content = new_content
            st.session_state.presentation_step = "export"
            st.rerun()

    # STEP 5: Export Presentation
    elif st.session_state.presentation_step == "export":
        st.subheader("Export Presentation")
        topic = st.session_state.presentation_topic
        col1, col2 = st.columns(2)
        with col1:
            ppt_path = create_presentation_from_content(st.session_state.presentation_content, topic, os.getenv("DASHSCOPE_API_KEY", ""))
            with open(ppt_path, "rb") as f:
                st.download_button("⬇️ Download PowerPoint", f, file_name=os.path.basename(ppt_path), mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
        with col2:
            doc_path = create_document_from_content(st.session_state.presentation_content, topic)
            with open(doc_path, "rb") as f:
                st.download_button("⬇️ Download Word Document", f, file_name=os.path.basename(doc_path), mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

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
