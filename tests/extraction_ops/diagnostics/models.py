import dataclasses
from collections.abc import Callable


@dataclasses.dataclass(frozen=True)
class Stage:
    suffix: str
    consumes: str
    operation: Callable
    test_golden: Callable
    to_text: Callable
