from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator, List, Optional

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


def _extract_message_content(message: ChatCompletionMessageParam) -> Any:
    """Return the ``content`` payload from a chat message param."""

    if isinstance(message, Mapping):
        return message.get("content")

    # Fallback for objects that expose ``content`` as an attribute.
    return getattr(message, "content", None)


def _message_contains_image(message: ChatCompletionMessageParam) -> bool:
    """Determine whether the given message contains an image payload."""

    content = _extract_message_content(message)

    if isinstance(content, list):
        for part in content:
            if isinstance(part, Mapping):
                part_type = part.get("type")
                if part_type in {"image_url", "input_image"}:
                    return True
                if "image_url" in part and isinstance(part["image_url"], Mapping):
                    return True

    return False


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

    messages_list = list(messages)
    contains_image = any(_message_contains_image(msg) for msg in messages_list)

    model = "qwen3-vl-plus" if contains_image else model_map.get(normalized_mode, "qwen-turbo")

    extra_body: dict[str, Any] = {}
    if normalized_mode == "Reasoning" or contains_image:
        extra_body["enable_thinking"] = True
        extra_body["thinking_budget"] = 81920

    def factory() -> Iterator:
        return client.chat.completions.create(
            model=model,
            messages=messages_list,
            stream=True,
            **({"extra_body": extra_body} if extra_body else {}),
        )

    return ResponseStream(stream_factory=factory)
