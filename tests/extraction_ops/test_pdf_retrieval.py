import httpx
import pytest
from pathlib import Path

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.pdf_ops import get_pdf_from_url
from tests.extraction_ops.diagnostics.retrieve_pdf import get_text_hash


@pytest.mark.live
@pytest.mark.parametrize("doc_key, tools", TOOLBELT_REGISTRY.items())
def test_document_url_and_hash(doc_key: str, tools):

    response = httpx.head(tools.input_url, timeout=10, follow_redirects=True)
    assert response.status_code == 200, (
        f"URL for {doc_key} is dead! Status: {response.status_code}"
    )

    test_path = Path(
        f"tests/extraction_ops/diagnostics/data/raw_pdf/{doc_key}_test.pdf"
    )
    test_path.parent.mkdir(parents=True, exist_ok=True)
    get_pdf_from_url(tools.document, tools.input_url, test_path)

    current_hash = get_text_hash(test_path)
    golden_hash_path = Path(
        f"tests/extraction_ops/diagnostics/data/raw_pdf/{doc_key}_golden_hash.txt"
    )

    assert golden_hash_path.exists(), (
        f"No golden hash found for {doc_key}. "
        "Run your diagnostic script with --save-golden first!"
    )

    golden_hash = golden_hash_path.read_text().strip()

    assert current_hash == golden_hash, (
        f"Hash mismatch for {doc_key}! The source document at the URL has changed."
    )
