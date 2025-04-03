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

    # Initialize conversation history in session_state
    if "messages" not in st.session_state:
        # Include an initial system message to define the assistant's behavior
        st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant."}]

    # Display existing conversation
    for message in st.session_state.messages:
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
        results = dbms.query(" ".join(keywords), top_n=5)  # Combine keywords for a relevant search query
        
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
        st.session_state.messages.append({"role": "system", "content": 'Here are sources that you may use, if you do, please cite and quote at all times'+assistant_reply})
        with st.chat_message("assistant"):
            st.markdown(assistant_reply)

        ###
        # Modify the system prompt based on the response type
        system_prompt = st.session_state.messages[0]["content"]
        if response_type == "IDX":
            system_prompt = "You are an expert who provides information specifically from Indexademics Database. Now you will always query the Finder or Database for files that can explain the content to the user. You may want to find exact defintiions and or quotes to support and to back up your answer."
        elif response_type == "Reasoning":
            system_prompt = "You are a logical assistant who focuses on providing detailed reasoning. From here you will be triggered with a deep thinking phrase and then you should cover and then think about all aspects provided in the <think> phrase. "
        elif response_type == "Long Text":
            system_prompt = "You are an assistant who can solve very long questions or generate text contents."
        
        # Update the system message in session state
        st.session_state.messages[0]["content"] = system_prompt

        # Fetch response from OpenAI's API
        try:
            bot_response = openai_api_call(st.session_state.messages,response_type)  # Pass the conversation history
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            with st.chat_message("assistant"):
                st.markdown(bot_response)
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": "An error occurred."})
            with st.chat_message("assistant"):
                st.markdown(f"An error occurred: {e}")
