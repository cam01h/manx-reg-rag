import fitz
import hashlib
from pathlib import Path


def _get_pdf_contents(path: Path) -> str:
    text_lines = []
    with fitz.open(path) as doc:
        for page in doc:
            text_lines.append(page.get_text())
    return "".join(text_lines)


def _hash_string(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_text_hash(path: Path) -> str:
    text = _get_pdf_contents(path)
    return _hash_string(text)
