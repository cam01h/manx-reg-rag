import dataclasses
from collections.abc import Callable


@dataclasses.dataclass(frozen=True)
class Stage:
    stage_description: str
    suffix: str
    loader: Callable
    operation: Callable
    test_golden: Callable
