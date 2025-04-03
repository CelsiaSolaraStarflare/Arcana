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

    # Add a section for image upload
    with st.expander("Upload an Image for Inspection", expanded=False):
        uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            # Display the uploaded image
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
            # Example: Add custom processing logic for the uploaded image
            st.write("Image uploaded successfully. Add your analysis here.")

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
        with st.chat_message("assistant"):
            st.markdown(assistant_reply)

        # Modify the system prompt based on the response type
        system_prompt = st.session_state.messages[0]["content"]
        if response_type == "IDX":
            system_prompt = "You are an expert who provides information specifically from Indexademics Database."
        elif response_type == "Reasoning":
            system_prompt = "You are a logical assistant who focuses on providing detailed reasoning."
        elif response_type == "Long Text":
            system_prompt = "You are an assistant who can solve very long questions or generate text contents."
        
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
