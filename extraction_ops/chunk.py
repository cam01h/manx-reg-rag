from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    document: str
    hierarchy: str
    headers: list[str]
    body: str
    terms_used: list[str] | None = None
