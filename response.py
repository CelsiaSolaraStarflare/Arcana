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
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="qwen-turbo"
        )
    else:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="qwen-turbo"
        )
    print(chat_completion)
    if chat_completion:
        return chat_completion.choices[0].message.content
