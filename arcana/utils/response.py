from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from typing import Generator, List, Dict, Any, Iterable

client = OpenAI(
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    api_key="sk-e8dfa404853d43e9870570c6c98c9516",
)

online = True
search_mode=1
def openai_api_call(messages: Iterable[ChatCompletionMessageParam], mode: str = 'Normal') -> Generator[str, None, None]:
    """
    Calls the OpenAI-compatible API with the given messages and streams the response.
    This function is a generator that yields the content chunks.
    """
    model_map = {
        'Normal': 'qwen-plus',
        'Math': 'llama-4-maverick-17b-128e-instruct',
        'Long Text': 'qwen-long',
        'Idx': 'qwen-turbo'
    }
    model = model_map.get(mode.title(), 'qwen-turbo')

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"An error occurred: {str(e)}"
