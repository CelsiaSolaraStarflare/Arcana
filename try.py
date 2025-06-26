from openai import OpenAI

client = OpenAI(
    base_url='https://api.openai-proxy.org/v1',
    api_key='sk-h5dnvEJsWlA4YY868M7LC0hGGtD6mmubhSeg7zQ2dFDMehbw',
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Say hi",
        }
    ],
    model="gpt-3.5-turbo",
)
