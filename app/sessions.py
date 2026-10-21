from cachetools import TTLCache
from pydantic_ai import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from app.models import ConversationStep, UserPrompt
from core.sectors import SECTOR_LABELS

CONVERSATIONS = TTLCache[str, list[ConversationStep]](maxsize=1000, ttl=3600)

SECTORS_PROMPT_START = (
    "The user has indicated the following sectors are relevant to their prompt:\n\n"
)

SECTORS_PROMPT_END = "\n\nYour response should be tailored to answer the question from the perspective of someone working in these sectors"


def to_message_history(steps: list[ConversationStep]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for step in steps:
        messages.append(ModelRequest(parts=[UserPromptPart(content=step.user_prompt)]))
        messages.append(ModelResponse(parts=[TextPart(content=step.agent_response)]))
    return messages


def build_sectors_prompt(sectors: tuple[str, ...]) -> str:
    if not sectors:
        return ""
    sectors_readable: list[str] = [SECTOR_LABELS[s] for s in sectors]
    sector_list_as_served = "\n".join(f"- {txt}" for txt in sectors_readable)
    return "\n\n" + SECTORS_PROMPT_START + sector_list_as_served + SECTORS_PROMPT_END


def build_prompt_with_sectors(user_prompt: UserPrompt) -> str:
    return user_prompt.prompt + build_sectors_prompt(user_prompt.sectors)
