from pydantic import BaseModel, Field, field_validator

from core.sectors import ALL_SECTORS


class UserPrompt(BaseModel):
    sectors: tuple[str, ...] = ()
    prompt: str
    session_id: str

    @field_validator("sectors", mode="after")
    @classmethod
    def check_sectors(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        unknown = [s for s in value if s not in ALL_SECTORS]
        if unknown:
            raise ValueError(f"unknown sectors: {unknown}")
        return value


class Citation(BaseModel):
    ref: str = Field(description="The ref of a chunk you were shown, e.g. C001")
    relevance: str


class UiCitation(BaseModel):
    document: str
    headers: list[str]
    url: str
    relevance: str


class AgentResponse(BaseModel):
    answer: str
    citations: list[Citation]


class UiResponse(BaseModel):
    answer: str
    citations: list[UiCitation]


class DocumentInfo(BaseModel):
    name: str
    hierarchy: str


class ConversationStep(BaseModel):
    user_prompt: str
    agent_response: str
