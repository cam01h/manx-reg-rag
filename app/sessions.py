from cachetools import TTLCache
from pydantic_ai import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from app.models import ConversationStep


CONVERSATIONS = TTLCache[str, list[ConversationStep]](maxsize=1000, ttl=3600)


def to_message_history(steps: list[ConversationStep]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for step in steps:
        messages.append(ModelRequest(parts=[UserPromptPart(content=step.user_prompt)]))
        messages.append(ModelResponse(parts=[TextPart(content=step.agent_response)]))
    return messages
