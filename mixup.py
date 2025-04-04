import streamlit as st
import reveal_slides as rs
from pptx import Presentation
from pptx.util import Inches, Pt
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from response import openai_api_call  # Custom function for OpenAI API calls
from fiber import FiberDBMS  # Custom FiberDBMS class

# Download NLTK data
nltk.download("punkt")
nltk.download("stopwords")

# Function to extract keywords from user input
def extract_keywords(user_input):
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(user_input)
    return [word for word in words if word.lower() not in stop_words and word.isalpha()]

# Function to create PowerPoint presentation
def create_ppt(bot_response):
    presentation = Presentation()
    blank_layout = presentation.slide_layouts[6]  # Blank slide layout

    slides = bot_response.split('---')[1:-1]
    for slide_data in slides:
        slide_data = slide_data.strip()
        if not slide_data:
            continue

        # Extract title and content
        lines = slide_data.split("\n")
        title_text = ""
        content_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith("###"):
                title_text = line.strip("#").strip("**")
            elif line.startswith("-"):
                content_lines.append(line.strip("-").strip())

        # Add a new slide
        slide = presentation.slides.add_slide(blank_layout)
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(9), Inches(1))
        title_box.text = title_text
        content_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(9), Inches(5))
        content_text_frame = content_box.text_frame
        content_text_frame.clear()

        for line in content_lines:
            p = content_text_frame.add_paragraph()
            p.text = line
            p.font.size = Pt(20)

    ppt_file = "generated_presentation.pptx"
    presentation.save(ppt_file)
    return ppt_file

# Function to display PowerPoint as a downloadable file in Streamlit
def display_ppt_in_streamlit(ppt_file):
    with open(ppt_file, "rb") as f:
        st.download_button("Download PowerPoint Presentation", f, file_name=ppt_file)

# Function to show inline reveal.js slides
def display_reveal_slides(bot_response):
    rs.slides(bot_response, 
              height=600, 
              theme="black", 
              config={
                  "transition": "slide",
                  "width": 900,
                  "height": 700,
                  "margin": 0.1,
                  "center": True,
                  "plugins": ["highlight", "search", "zoom"]
              }, 
              markdown_props={"data-separator-vertical": "^--$"}, 
              key="presentation")

# Function to generate assistant reply from database results
def generate_reply(results):
    if results:
        reply = "Here are the top results I found in the Indexademics Database Search:\n"
        for idx, result in enumerate(results, 1):
            reply += f"**Result {idx}**\n"
            reply += f"Name: {result['name']}\n"
            reply += f"Content: {result['content']}\n"
            reply += f"Tags: {result['tags']}\n\n"
    else:
        reply = "Sorry, I couldn't find anything relevant in the database."
    return reply

# Main Streamlit application
def mixup_page():
    st.title('Arcana Mixup')
    st.write('Backend powered by NST Department | StandardCAS™')

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "bot_response" not in st.session_state:
        st.session_state.bot_response = ""  # Store bot response to avoid re-querying

    # User input
    user_input = st.text_input("Enter something:")

    if user_input and st.button("Send"):  # Only query when "Send" button is clicked
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Initialize database
        dbms = FiberDBMS()
        dbms.load_or_create("temp_database.txt")

        # Query database
        keywords = extract_keywords(user_input)
        results = dbms.query(" ".join(keywords), top_n=20)

        # Generate assistant reply
        assistant_reply = generate_reply(results)
        st.session_state.messages.append({"role": "system", "content": assistant_reply})

        # Call OpenAI API for the bot's response
        bot_response = openai_api_call(st.session_state.messages, "response_type")
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        st.session_state.bot_response = bot_response  # Save the bot's response to state

    # Display bot response if available
    if st.session_state.bot_response:
        st.text_area("Automated Canvas:", value=st.session_state.bot_response, height=300)

        # Generate and display presentation
        if "powerpoint" in st.session_state.bot_response.lower():
            ppt_file = create_ppt(st.session_state.bot_response)  # Create PPTX file
            display_ppt_in_streamlit(ppt_file)  # Add download button
            display_reveal_slides(st.session_state.bot_response)  # Show inline reveal.js presentation

