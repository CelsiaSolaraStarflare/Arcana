import streamlit as st
import openai 
from response import openai_api_call  # Assuming this function handles the OpenAI API call
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
 
# Download required NLTK data
nltk.download("punkt")
nltk.download("stopwords")
nltk.download('punkt_tab')
 
from fiber import *  # Import your FiberDBMS class/module

# Function for the chatbot page
def chatbot_page():
    st.title("ChatApp Interface")
  
    # Add button to clear all messages
    if st.button("Clear All Messages"):
        st.session_state.messages = []
        st.experimental_rerun()  # Rerun to reset everything and clear the chat

    # Initialize conversation history in session_state if it's empty
    if "messages" not in st.session_state or len(st.session_state.messages) == 0:
        # Include an initial system message to define the assistant's behavior
        st.session_state.messages = [{"role":"assistant","content":"Hey, I'm Arcana, your Indexademics AI assistant. Ask me anything about the SHSID high school curriculum! "},{'role':'system','content':'Cite the name of the document where you received the results at the end of each response.'}]

    # Display existing conversation (exclude system messages from being displayed)
    for message in st.session_state.messages:
        # Only display user and assistant messages, not system messages
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input box for user messages
    user_input = st.chat_input("Type your message...")

    # Dropdown to select the response type
    response_type = st.selectbox(
        "Choose a response type:",
        ["Normal", "IDX", "Reasoning", "Long Text"]
    )

    if user_input:
        # Add user message to session state
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Tokenize and filter out stop words to get keywords
        stop_words = set(stopwords.words('english'))
        words = word_tokenize(user_input)
        keywords = [word for word in words if word.lower() not in stop_words and word.isalpha()]  # Keep only relevant words

        dbms = FiberDBMS()
        # Load or create the database
        dbms.load_or_create("temp_database.txt")
        # Query the database using the extracted keywords
        results = dbms.query(" ".join(keywords), top_n=20)  # Combine keywords for a relevant search query
        
        # Create assistant reply based on database search results
        assistant_reply = ""
        if results:
            assistant_reply += "Here are the top results I found in the Indexademics Database Search:\n"
            for idx, result in enumerate(results, 1):
                assistant_reply += f"**Result {idx}**\n"
                assistant_reply += f"Name: {result['name']}\n"
                assistant_reply += f"Content: {result['content']}\n"
                assistant_reply += f"Tags: {result['tags']}\n\n"
        else:
            assistant_reply = "Sorry, I couldn't find anything relevant in the database."
    
        # Add assistant message to session state
        st.session_state.messages.append({"role": "system", "content": assistant_reply})

        # Modify the system prompt based on the response type
        system_prompt = st.session_state.messages[0]["content"]
        if response_type == "IDX":
            system_prompt = "You are an expert who provides information specifically from Indexademics Database. Cite the result's file name at the end of each query. "
        else:
            system_prompt = "You may see that there is already content provided by the Indexademics Database search, however, in this default chat mode, you do not need to explain the concept based on them. Of course, if there is the proper definition provided, please cite. Or else you do not need to reference under this mode. Cite the result's file name at the end of each query. "
        
        # Update the system message in session state
        st.session_state.messages[0]["content"] = system_prompt

        # Fetch response from OpenAI's API
        try:
            bot_response = openai_api_call(st.session_state.messages, response_type)  # Pass the conversation history
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            with st.chat_message("assistant"):
                st.markdown(bot_response)
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": "An error occurred."})
            with st.chat_message("assistant"):
                st.markdown(f"An error occurred: {e}")
