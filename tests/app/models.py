from dataclasses import dataclass
from pydantic import BaseModel


# ===== test definition =====


@dataclass(frozen=True)
class Anchor:
    document: str
    text: str


@dataclass(frozen=True)
class AgentTest:
    question: str
    anchors: tuple[Anchor, ...]
    expect_abstention: bool = False


# ===== judge outputs =====


class AnchorJudgement(BaseModel):
    reasoning: str
    content_present: bool


class GroundingJudgement(BaseModel):
    reasoning: str
    grounded: bool
    unsupported_claims: list[str]


# ===== per-run records =====


@dataclass(frozen=True)
class ToolCallRecord:
    tool_name: str
    query: str
    chunk_ids: tuple[str, ...]


@dataclass(frozen=True)
class AnchorResult:
    document: str
    text: str
    retrieved: bool
    content_present: bool | None
    reasoning: str | None

    def classification(self) -> str:
        if self.retrieved and self.content_present:
            return "pass"
        if self.retrieved and not self.content_present:
            return "writer_failure"
        if not self.retrieved and self.content_present:
            return "unsourced"
        return "retrieval_failure"


@dataclass(frozen=True)
class RunResult:
    question: str
    run_index: int
    answer: str
    anchors: tuple[AnchorResult, ...]
    grounding: GroundingJudgement
    tool_calls: tuple[ToolCallRecord, ...]
    input_tokens: int
    output_tokens: int
    elapsed: float
