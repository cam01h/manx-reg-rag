from dataclasses import asdict
import json
import httpx

from extraction_ops.load_to_md import load_clean_md
from .models import ToolBelt
from .chunking import extract_to_chunks, normalise_chunk_size
from .definitions import extract_to_definitions, attach_definitions
from config import (
    CHUNKS_JSONL_PATH,
    DEFINITIONS_JSONL_PATH,
    setup_logging,
)
import logging

logger = logging.getLogger(__name__)


def get_pdf_from_url(tools: ToolBelt) -> None:
    logger.info("downloading [%s]", tools.document)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        }
        response = httpx.get(
            url=tools.input_url, timeout=20, follow_redirects=True, headers=headers
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("failed httpx request for [%s]", tools.document)
        raise
    if not response.content.startswith(b"%PDF"):
        logger.critical("[%s] did not return a pdf", tools.document)
        raise ValueError(f"{tools.document} did not return a pdf")
    try:
        with open(tools.pdf_path, "wb") as f:
            f.write(response.content)
    except Exception:
        logger.exception("failed to write pdf to [%s]", tools.pdf_path)
        raise


if __name__ == "__main__":
    setup_logging("ingest")
    docs = [
        AmlCode,
        AmlHandbook,
        SupplementalInformation,
        Poca,
        TerrorismAndCrime,
        FiuAct,
        RegulatedActivitiesOrder,
        Dbroa,
        FinancialRestrictionsAct,
        SanctionsAct,
    ]
    all_chunks = []
    all_definitions = []
    for doc in docs:
        get_pdf_from_url(doc)
        md = load_clean_md(doc)
        chunks = extract_to_chunks(doc, md.chunk_lines)
        chunks = normalise_chunk_size(chunks, doc)
        logger.info("[%d] normalised chunks", len(chunks))
        definitions = extract_to_definitions(doc, md.definition_lines)
        chunks = attach_definitions(chunks, definitions)
        all_definitions[doc.document] = definitions
        all_chunks.extend(chunks)
    try:
        with CHUNKS_JSONL_PATH.open("w") as f:
            for c in all_chunks:
                f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
        logger.info("[%d] chunks written to [%s]", len(all_chunks), CHUNKS_JSONL_PATH)
    except Exception:
        logger.exception("failed to write chunks to [%s]", CHUNKS_JSONL_PATH)
        raise
    try:
        with DEFINITIONS_JSONL_PATH.open("w") as f:
            json.dump(all_definitions, f, ensure_ascii=False, indent=2)
        total_definitions = sum(len(defs) for defs in all_definitions.values())
        logger.info(
            "[%d] definitions written to [%s]",
            total_definitions,
            DEFINITIONS_JSONL_PATH,
        )
    except Exception:
        logger.exception("failed to write definitions to [%s]", DEFINITIONS_JSONL_PATH)
        raise
