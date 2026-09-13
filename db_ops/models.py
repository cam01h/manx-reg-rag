from pydantic import BaseModel, ConfigDict


class HashableBaseModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    def __hash__(self) -> int:
        return hash(tuple(self.__dict__.values()))


class Payload(BaseModel):
    model_config = ConfigDict(frozen=True)
    chunk_id: str
    document: str
    hierarchy: str
    headers: list[str]
    body: str
    terms_used: list[str] | None = None
    score: float
    rank: int | None = None


class ServedPayload(BaseModel):
    model_config = ConfigDict(frozen=True)
    title: str
    hierarchy: str
    body: str


class DefinitionRecord(HashableBaseModel):
    model_config = ConfigDict(frozen=True)
    document: str
    term: str
    definition: str
