from pathlib import Path
import httpx
from .models import ToolBelt
import logging


logger = logging.getLogger(__name__)


def get_pdf_from_url(doc: str, url: str, path: Path) -> None:
    logger.info("downloading [%s]", doc)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        }
        response = httpx.get(
            url=url, timeout=20, follow_redirects=True, headers=headers
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("failed httpx request for [%s]", doc)
        raise
    if not response.content.startswith(b"%PDF"):
        logger.critical("[%s] did not return a pdf", doc)
        raise ValueError(f"{doc} did not return a pdf")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(response.content)
    except Exception:
        logger.exception("failed to write pdf to [%s]", path)
        raise


def apply_pdf_handlers(tools: ToolBelt) -> None:
    if tools.pdf_handlers is not None:
        for i, handler in enumerate(tools.pdf_handlers):
            try:
                handler(tools.pdf_path)
            except Exception:
                logger.critical("failed to complete pdf_handler idx[%d]", i)
                raise
