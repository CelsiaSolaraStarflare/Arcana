from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key='your-secure-api-key',  # Ensure the API key is securely stored
)

def openai_api_call(messages, mode='Normal'):
    print(messages)  # Log the messages for debugging
    
    # Initialize an empty response variable
    response_content = ""

    try:
        # Handle different modes
        if mode == 'Normal':
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="qwen-turbo",
            )
            # Full response handling for 'Normal' mode
            response_content = chat_completion.choices[0].message.content
        
        elif mode == 'Reasoning':
            # Streaming mode
            stream_response = client.chat.completions.create(
                messages=messages,
                model="qwq-32b",
                stream=True
            )
            # Collect tokens from the stream
            for chunk in stream_response:
                if "content" in chunk.choices[0].delta:
                    token = chunk.choices[0].delta["content"]
                    response_content += token  # Append streamed tokens
                    print(token, end="")  # Optional: log in real time
        
        elif mode == 'Long Text':
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="qwen-turbo"
            )
            response_content = chat_completion.choices[0].message.content
        
        else:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="qwen-turbo"
            )
            response_content = chat_completion.choices[0].message.content

    except Exception as e:
        # Handle errors gracefully
        print(f"Error occurred: {e}")
        response_content = "An error occurred while processing your request."
    
    # Return the assembled response content
    return response_content
