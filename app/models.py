from pydantic import BaseModel


class UserPrompt(BaseModel):
    prompt: str


class Citation(BaseModel):
    chunk_id: str
    relevance: str


class AgentResponse(BaseModel):
    answer: str
    citations: list[Citation]
