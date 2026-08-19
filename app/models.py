from pydantic import BaseModel


class UserPrompt(BaseModel):
    prompt: str
    session_id: str


class Citation(BaseModel):
    chunk_id: str
    relevance: str


class AgentResponse(BaseModel):
    answer: str
    citations: list[Citation]


class ConversationStep(BaseModel):
    user_prompt: str
    agent_response: str
