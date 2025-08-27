import streamlit as st
from openai import OpenAI, APIStatusError, APITimeoutError
from openai.types.chat import ChatCompletionMessageParam
from config import QWEN_API_KEY, QWEN_BASE_URL  # Import from config

# --- Helper Functions ---

def get_qwen_client():
    """Initializes and returns the OpenAI client for the Qwen model."""
    if not QWEN_API_KEY or not QWEN_BASE_URL:
        st.error("The Qwen API key or base URL is not configured. Please set them in `config.py`.")
        st.stop()
    return OpenAI(
        base_url=QWEN_BASE_URL,
        api_key=QWEN_API_KEY,
    )

def generate_qwen_prompt(mode: str, article: str) -> list[ChatCompletionMessageParam]:
    """Generates the appropriate prompt for the selected analysis mode."""
    prompts = {
        "Summary": "Summarize the key points of the following article concisely.",
        "Key Takeaways": "Extract the main takeaways from this article as a bulleted list.",
        "Pros and Cons": "Analyze the following text and list the primary pros and cons discussed.",
        "Explain Like I'm 5": "Explain the core concepts of this article in a very simple and easy-to-understand way, as if for a five-year-old."
    }
    system_prompt = "You are a highly skilled AI assistant specializing in text analysis and summarization. Your goal is to provide clear, accurate, and helpful responses based on the user's request."
    
    return [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': f"{prompts[mode]}\n\n--- ARTICLE ---\n{article}"}
    ]

# --- Main Page Function ---

def longresponse_page():
    """
    A Streamlit page for analyzing long-form text using the Qwen model.
    """
    st.title("📜 Long-Form Text Analyzer")
    st.markdown("Use the power of advanced AI to analyze long articles, reports, or documents. Paste your text below, choose an analysis mode, and let Arcana do the rest.")

    # Initialize client and session state
    client = get_qwen_client()
    if 'long_response' not in st.session_state:
        st.session_state.long_response = ""

    with st.form("long_response_form"):
        article_content = st.text_area(
            "Paste your article here:", 
            height=350, 
            placeholder="Paste the full text of the article, document, or report you want to analyze..."
        )
        
        analysis_mode = st.selectbox(
            "Choose Analysis Mode:",
            ["Summary", "Key Takeaways", "Pros and Cons", "Explain Like I'm 5"],
            help="Select the type of analysis you want to perform on the text."
        )
        
        submitted = st.form_submit_button("Analyze Text")

    if submitted and article_content:
        st.session_state.long_response = "" # Clear previous response
        messages = generate_qwen_prompt(analysis_mode, article_content)
        
        try:
            with st.spinner("Arcana is analyzing the document... This may take a moment."):
                stream = client.chat.completions.create(
                    model="qwen-long",
                    messages=messages,
                    stream=True
                )
                
                # Stream the response directly to the page
                st.subheader("Analysis Result")
                response_container = st.empty()
                
                full_response = ""
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        response_container.markdown(full_response + "▌")
                
                response_container.markdown(full_response)
                st.session_state.long_response = full_response

        except APITimeoutError:
            st.error("The request timed out. The server may be busy. Please try again later.")
        except APIStatusError as e:
            error_message = "An unknown API error occurred."
            if isinstance(e.body, dict) and 'message' in e.body:
                error_message = e.body['message']
            st.error(f"An API error occurred: {error_message}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            
    elif submitted:
        st.warning("Please paste some text into the article box before analyzing.")
        
    elif st.session_state.long_response:
        # Display the last response if the page re-runs
        st.subheader("Analysis Result")
        st.markdown(st.session_state.long_response)

if __name__ == "__main__":
    longresponse_page()
