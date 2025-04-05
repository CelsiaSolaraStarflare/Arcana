from openai import OpenAI
import streamlit as st

client = OpenAI(
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key=st.secrets["openai"]["api_key"],
)

online = True
search_mode=1
def openai_api_call(messages, mode='Normal'):
    print(messages)
    if mode == 'Normal':
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="qwen-turbo",
        )
    elif mode == 'Reasoning':
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="qwq-32b",
            stream=True
        )
    elif mode == 'Long Text':
        completion = client.chat.completions.create(
            model="qwen-long",
            messages=messages,
            stream=True,
            stream_options={"include_usage": True}
        )
                
        full_content = ""
        for chunk in completion:
             if chunk.choices and chunk.choices[0].delta.content:
                 full_content += chunk.choices[0].delta.content
                
    else:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="qwen-turbo"
        )
    print(chat_completion)
    if chat_completion:
        if mode == 'Long Text':
            return full_content
        return chat_completion.choices[0].message.content
