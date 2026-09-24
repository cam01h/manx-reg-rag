import dataclasses
from collections.abc import Callable
from typing import Any


@dataclasses.dataclass(frozen=True)
class Stage:
    suffix: str
    consumes: str | None
    operation: Callable[[str, Any], Any]
    test_golden: Callable[[str, Any], None]
    to_text: Callable[[Any], str] | None
