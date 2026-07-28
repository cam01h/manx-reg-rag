import argparse
from config import PROJECT_ROOT, setup_logging
from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.load_to_md import get_pdf_from_url
import logging

logger = logging.getLogger("__name__")


def diagnostic_pdf_retrieval() -> None:
    parser = argparse.ArgumentParser(description="Retrieve PDF for a doc")
    parser.add_argument(
        "doc", choices=TOOLBELT_REGISTRY.keys(), help="which document to retreive"
    )
    args = parser.parse_args()
    tools = TOOLBELT_REGISTRY[args.doc]
    path = (
        PROJECT_ROOT / f"tests/extraction_ops/diagnostics/data/{tools.document}raw.pdf"
    )
    get_pdf_from_url(tools.document, tools.input_url, path)


if __name__ == "__main__":
    setup_logging("diagnostics")
    diagnostic_pdf_retrieval()
