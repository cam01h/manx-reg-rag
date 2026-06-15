from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    chunk_id: str
    rank: int
    score: float
    document: str
    hierarchy: str
    headers: list[str]
    body: str
    terms_used: list[str] | None = None
    citation: str | None = None


class Definition(BaseModel):
    term: str
    definition: str
    source: str
