from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    document: str
    hierarchy: str
    major: str
    minor: str
    body: str
    terms_used: list[str] | None = None
