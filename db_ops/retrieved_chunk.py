from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    rank: int
    score: float
    document: str
    hierarchy: str
    major: str
    minor: str
    body: str
    terms_used: list[str] | None = None


class Definition(BaseModel):
    term: str
    defintion: str
    source: str
