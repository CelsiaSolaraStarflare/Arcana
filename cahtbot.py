import streamlit as st
import openai 
from response import openai_api_call  # Assuming this function handles the OpenAI API call

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
        ["Default", "From IDX", "Reasoning", "Creative"]
    )
    if user_input:
        # Add user message to session state
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Modify the system prompt based on the response type
        system_prompt = st.session_state.messages[0]["content"]
        if response_type == "From IDX":
            system_prompt = "You are an expert who provides information specifically from Indexademics Database. Now you will always query the Finder or Database for files that can explain the content to the user. You may want to find exact defintiions and or quotes to support and to back up your answer."
        elif response_type == "Reasoning":
            system_prompt = "You are a logical assistant who focuses on providing detailed reasoning. From here you will be triggered with a deep thinking phrase and then you should cover and then think about all aspects provided in the <think> phrase. "
        elif response_type == "Creative":
            system_prompt = "You are a creative assistant who crafts imaginative and inspiring responses."
        
        # Update the system message in session state
        st.session_state.messages[0]["content"] = system_prompt

        # Fetch response from OpenAI's API
        try:
            bot_response = openai_api_call(st.session_state.messages)  # Pass the conversation history
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            with st.chat_message("assistant"):
                st.markdown(bot_response)
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": "An error occurred."})
            with st.chat_message("assistant"):
                st.markdown(f"An error occurred: {e}")
