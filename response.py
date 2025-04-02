#get response
from openai import OpenAI

client = OpenAI(
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key='sk-e8dfa404853d43e9870570c6c98c9516',
)

online = True
search_mode=1
def openai_api_call(messages):
    print(messages)
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="qwen-turbo",
    )
    print(chat_completion)
    return chat_completion.choices[0].message.content
