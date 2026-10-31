from pydantic import BaseModel


class ToolCall(BaseModel):
    tool_name: str
    data: str
