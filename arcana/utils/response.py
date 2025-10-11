from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, List, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam


client = OpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="sk-e8dfa404853d43e9870570c6c98c9516",
)

online = True
search_mode = 1


@dataclass
class ResponseStream:
    """Wrapper around the streaming API response.

    This class keeps track of streamed content chunks as well as any
    "reasoning" tokens emitted by compatible models while still behaving like
    an iterable of string chunks.
    """

    stream_factory: Callable[[], Iterator]
    reasoning_chunks: List[str] = field(default_factory=list)
    error: Optional[str] = None
    _consumed: bool = False

    def __iter__(self) -> Iterator[str]:
        if self._consumed:
            # Generators returned by ``stream_factory`` are one-shot. If the
            # caller attempts to iterate again we simply yield nothing to avoid
            # re-triggering the API call.
            return iter(())

        self._consumed = True

        def iterator() -> Iterator[str]:
            try:
                stream = self.stream_factory()
                for chunk in stream:
                    if not chunk.choices:
                        continue

                    delta = chunk.choices[0].delta

                    reasoning_piece = getattr(delta, "reasoning_content", None)
                    if reasoning_piece:
                        self.reasoning_chunks.append(reasoning_piece)

                    content_piece = getattr(delta, "content", None)
                    if content_piece:
                        yield content_piece
            except Exception as exc:  # pragma: no cover - network dependent
                self.error = str(exc)
                yield f"An error occurred: {self.error}"

        return iterator()

    @property
    def reasoning(self) -> str:
        """Full reasoning text emitted by the model, if any."""

        return "".join(self.reasoning_chunks).strip()

    def has_reasoning(self) -> bool:
        return bool(self.reasoning)


def openai_api_call(
    messages: Iterable[ChatCompletionMessageParam],
    mode: str = "Normal",
) -> ResponseStream:
    """
    Calls the OpenAI-compatible API with the given messages and streams the
    response.

    Parameters
    ----------
    messages:
        An iterable of chat completion message payloads.
    mode:
        The reasoning mode that should be used. Determines which underlying
        model (and optional extra parameters) are utilised.
    """

    normalized_mode = mode.title()
    model_map = {
        "Normal": "qwen-plus",
        "Math": "llama-4-maverick-17b-128e-instruct",
        "Long Text": "qwen-long",
        "Idx": "qwen-turbo",
        "Reasoning": "qwen-plus-2025-04-28",
    }

    model = model_map.get(normalized_mode, "qwen-turbo")
    messages_list = list(messages)

    extra_body = {}
    if normalized_mode == "Reasoning":
        extra_body["enable_thinking"] = True

    def factory() -> Iterator:
        return client.chat.completions.create(
            model=model,
            messages=messages_list,
            stream=True,
            **({"extra_body": extra_body} if extra_body else {}),
        )

    return ResponseStream(stream_factory=factory)
