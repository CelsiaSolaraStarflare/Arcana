#get response
from openai import OpenAI

client = OpenAI(
    base_url='https://api.openai-proxy.org/v1',
    api_key='sk-h5dnvEJsWlA4YY868M7LC0hGGtD6mmubhSeg7zQ2dFDMehbw',
)

online = True
search_mode=1
def openai_api_call(messages):
    print(messages)
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-3.5-turbo",
    )
    print(chat_completion)
    return chat_completion.choices[0].message.content
