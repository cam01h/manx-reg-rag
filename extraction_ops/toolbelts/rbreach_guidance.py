from core.sectors import RAO_CLASSES
from extraction_ops.models import ChunkSplitters, ToolBelt
from extraction_ops.toolbelts.shared_funcs import (
    base_text_cleaner,
    build_pdf_path,
    build_simple_markers,
    fixed_sectors,
    replace_from_dict,
    replace_section,
    split_on_paragraph,
    split_on_paragraph_not_list,
    starts_with,
    strip_footnote_bullets,
)

# the two columns are separate lists rather than matched pairs, so they are kept as lists.
# footnote 2 sits on the heading and is moved into the intro line
_FACTORS_TABLE_FLAT = """[Editors note: the below is a flattened table]

Table 1 - examples of mitigating and aggravating factors (the list is illustrative and not exhaustive).

Mitigating factors:
- Genuine error
- Generally adequate procedures and controls, for example other similar matters handled correctly
- Little or no impact on customers
- Force majeure - circumstances wholly or partly outside the control of the licenceholder
- Little or no additional AML/CFT risk
- Little or no financial crime risk
- Breach identified by licenceholder
- Prompt and effective remedial action

Aggravating factors:
- Deliberate or negligent breach
- Lacking or inadequate procedures or controls
- Adverse impact upon customers, e.g. actual or potential financial loss
- Within the licenceholder's control - possibly senior staff involved
- Increased AML/CFT risk
- Increased risk of financial crime
- Breach not identified by the licenceholder
- Slow and/or inadequate response to the problem
- Indications of lack of competence
- Increased risk of financial failure
- Repetition of the same breach
- Numerous breaches of different types, which could indicate weak controls or poor compliance
- Possible damage to the reputation of the jurisdiction

"""

_REPLACEMENT_DICT = {
    "regulatory requirements[1] .": 'regulatory requirements [Footnote: The use of "the regulatory requirements" in rule 8.17 is based on a defined term in rule 8.1.].',
    "mitigating and aggravating factors**[2]": "mitigating and aggravating factors**",
}


def _text_cleaner(text: str) -> str:
    text = base_text_cleaner(text)
    text = replace_section(
        text, "|**Mitigating factors**|", "> 2 The list in Table 1", _FACTORS_TABLE_FLAT
    )
    text = replace_from_dict(text, _REPLACEMENT_DICT)
    text = strip_footnote_bullets(text)
    return text


_Trimmer = build_simple_markers(
    "## **Status of guidance", "- Possible damage to the reputation of the jurisdiction"
)

_Splitters = ChunkSplitters(
    primary=split_on_paragraph_not_list, fallback=split_on_paragraph
)


def _is_sub_section(line: str) -> bool:
    # "## Breach identified by licenceholder" / "## Breach identified by the Authority"
    return line.startswith("## ") and not line.startswith("## **")


# rule 8.17 applies to all licenceholders
RbreachGuidance = ToolBelt(
    document="Guidance Note - Rule 8.17 - Breaches of Regulatory Requirements",
    hierarchy="guidance",
    sectors=fixed_sectors(RAO_CLASSES),
    input_url="https://www.iomfsa.im/media/1542/rulebreaches814.pdf",
    pdf_path=build_pdf_path("rbreach_guidance"),
    use_ocr=False,
    trimmer=_Trimmer,
    header_matchers=[starts_with(["## **"]), _is_sub_section],
    clean_text=_text_cleaner,
    re_pack_splitters=_Splitters,
)
