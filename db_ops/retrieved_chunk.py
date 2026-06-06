from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    chunk_id: str
    rank: int
    score: float
    document: str
    hierarchy: str
    major: str
    minor: str
    body: str
    terms_used: list[str] | None = None
    citation: str | None = None


class Definition(BaseModel):
    term: str
    defintion: str
    source: str
