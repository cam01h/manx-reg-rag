import logging

from extraction_ops.definitions import build_term_variants
from extraction_ops.models import Definition

from .models import Stage
from .utils import make_md_golden_test

logger = logging.getLogger(__name__)

_STAGE = "variants"


def _opperation(doc: str, input: list[Definition]) -> dict[str, list[str]]:
    return build_term_variants([d.term for d in input])


def _to_text(variants_by_term: dict[str, list[str]]) -> str:
    md = []
    for i, (term, variants) in enumerate(variants_by_term.items()):
        md.append(f'## Term {i + 1}: "{term}"')
        md.extend(
            [
                f'Variant {variant_i + 1}: "{variant}"'
                for variant_i, variant in enumerate(variants)
            ]
        )
        md.extend(["", "---", ""])
    return "\n".join(md)


Variants = Stage(
    suffix="md",
    consumes="definitions",
    operation=_opperation,
    test_golden=make_md_golden_test(_STAGE, _to_text),
    to_text=_to_text,
)
