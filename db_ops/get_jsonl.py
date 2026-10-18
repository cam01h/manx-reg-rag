import logging
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter, ValidationError

logger = logging.getLogger(__name__)


def load_jsonl_dir(path: Path, model: type) -> list[Any]:
    jsonl_files = sorted(path.glob("*.jsonl"))
    if not jsonl_files:
        logger.error("no jsonl file found at [%s]", path)
        raise FileNotFoundError(f"no jsonl files found at [{path}]")
    objects = []
    adapter = TypeAdapter(model)
    for f in jsonl_files:
        try:
            lines = f.read_text().splitlines()
            objects.extend(
                adapter.validate_json(line) for line in lines if line.strip()
            )
        except (OSError, ValidationError):
            logger.exception("failed to load/validate objects in [%s]", f)
            raise
    return objects
