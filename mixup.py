import streamlit as st
import os
import datetime
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from docx import Document
from docx.shared import Pt as DocxPt, RGBColor as DocxRGBColor

from response import openai_api_call
from fiber import FiberDBMS
from config import GENERATED_FILES_DIR
from openai.types.chat import ChatCompletionMessageParam

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
        return "No usable keywords found in the topic. Please try a more descriptive topic."

    results = dbms.query(" ".join(keywords), top_n=10)
    
    if not results:
        return "I could not find any relevant information in your documents for this topic."

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

# --- Document Generation ---

def create_presentation_from_content(presentation_content, topic):
    """Creates a PowerPoint presentation from a list of slide content."""
    prs = Presentation()
    
    # Use 'Title and Content' layout (index 1) or fallback to the first layout
    try:
        slide_layout = prs.slide_layouts[1]
    except IndexError:
        slide_layout = prs.slide_layouts[0]

    for slide_data in presentation_content:
        slide = prs.slides.add_slide(slide_layout)

        # Set title
        if slide.shapes.title:
            slide.shapes.title.text = slide_data['title']

        # Find a suitable placeholder for content
        content_placeholder = None
        for shape in slide.placeholders:
            # Find a placeholder that is not the title (idx=0)
            if shape.placeholder_format.idx != 0:
                content_placeholder = shape
                break
        
        if content_placeholder:
            tf = content_placeholder.text_frame  # type: ignore[attr-defined]
            tf.text = slide_data['content']
        else:
            # If only a title placeholder exists, add a new textbox for content
            if slide.shapes.title:
                left, top, width, height = Inches(1), Inches(2), Inches(8), Inches(5.5)
                textbox = slide.shapes.add_textbox(left, top, width, height)
                textbox.text_frame.text = slide_data['content']  # type: ignore[attr-defined]
                textbox.text_frame.word_wrap = True  # type: ignore[attr-defined]

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
        doc.add_paragraph(slide_data['content'])
        doc.add_paragraph() # Add some space

    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '_')).rstrip()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Document_{safe_topic}_{timestamp}.docx"
    
    os.makedirs(GENERATED_FILES_DIR, exist_ok=True)
    file_path = os.path.join(GENERATED_FILES_DIR, filename)
    doc.save(file_path)
    return file_path

# --- UI for Modes ---

def render_presentation_mode(dbms):
    st.header("✨ Presentation Generator")
    init_presentation_state()

    # STEP 1: Get topic and generate outline
    if st.session_state.presentation_step == "initial":
        st.subheader("Step 1: Choose a Topic")
        topic = st.text_input("What is your presentation about?", key="ppt_topic_input")
        if st.button("Generate Outline", type="primary") and topic:
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
        st.subheader("Step 2: Review and Edit the Outline")
        st.info("Review the generated outline below. You can make any changes before generating the full content.")
        
        edited_outline = st.text_area(
            "Presentation Outline:",
            value=st.session_state.presentation_outline,
            height=400,
            key="outline_editor"
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("✅ Generate Full Presentation Content", type="primary"):
                st.session_state.presentation_outline = edited_outline
                parsed_slides = parse_outline_to_slides(edited_outline)
                
                if not parsed_slides:
                    st.error("The outline is empty or in an invalid format. Please ensure it follows the '#### Title' and '- Point' structure.")
                else:
                    content_progress_bar = st.progress(0, text="Generating content for slide 1...")
                    generated_content = []
                    context = get_context_for_topic(dbms, st.session_state.presentation_topic)

                    for i, slide in enumerate(parsed_slides):
                        progress_text = f"Generating content for slide {i + 1} of {len(parsed_slides)}: '{slide['title']}'"
                        content_progress_bar.progress((i + 1) / len(parsed_slides), text=progress_text)
                        
                        points = '\n'.join([f'- {p}' for p in slide['points']])
                        prompt = (f"Write the detailed content for a presentation slide titled '{slide['title']}'. "
                                  f"Cover these points:\n{points}\n\n"
                                  f"Base your answer *only* on the provided context below. Be comprehensive and clear.\n\n"
                                  f"Context:\n{context}")
                        
                        slide_messages: list[ChatCompletionMessageParam] = [
                            {"role": "system", "content": "You are an AI assistant that writes slide content based on a provided outline and context."},
                            {"role": "user", "content": prompt}
                        ]
                        
                        slide_content = "".join(list(openai_api_call(slide_messages, "Normal")))
                        generated_content.append({"title": slide['title'], "content": slide_content})

                    st.session_state.presentation_content = generated_content
                    st.session_state.presentation_step = "content_generated"
                    st.rerun()
        with col2:
            if st.button("Start Over"):
                init_presentation_state(force_reset=True)
                st.rerun()

    # STEP 3: Download final presentation
    elif st.session_state.presentation_step == "content_generated":
        st.subheader("Step 3: Your Presentation Is Ready!")
        st.success("The content for your presentation has been successfully generated.")

        with st.expander("Preview Generated Content", expanded=False):
            for slide in st.session_state.presentation_content:
                st.markdown(f"**{slide['title']}**")
                st.markdown(slide['content'])
                st.markdown("---")

        topic = st.session_state.presentation_topic
        
        col1, col2 = st.columns(2)
        with col1:
            ppt_path = create_presentation_from_content(st.session_state.presentation_content, topic)
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

    if 'dbms' not in st.session_state or not isinstance(st.session_state.dbms, FiberDBMS):
        st.warning("The database is not initialized. Please go to the 'Files' page and index your files first.")
        st.stop()

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
