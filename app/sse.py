from pydantic import BaseModel


class ToolCall(BaseModel):
    tool_name: str
    data: str


class SearchProgress(BaseModel):
    term: str


class ReadProgress(BaseModel):
    document: str
    headers: str
