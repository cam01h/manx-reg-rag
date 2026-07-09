import re
from config import project_root
from .specs import DocSpecs
from .shared_funcs import replace_from_dict

GLUED_WORD_FIXES = {
    "moneyor apayment": "money or a payment",
    "defray,the considerationpayable": "defray, the consideration payable",
    "for,a debenture": "for, a debenture",
    "meaningas in the Act": "meaning as in the Act",
    "ageneralpartner": "a general partner",
    "byexclusion": "by exclusion",
    "meaningas electronic money": "meaning as electronic money",
    "territoryoutside": "territory outside",
    "orallyor evidenced": "orally or evidenced",
    "thegovernment of the Island": "the government of the Island",
    "anycountryor territory": "any country or territory",
    "securityor an insurancepolicy": "security or an insurance policy",
    "propertyof anydescription": "property of any description",
    "aparticipator": "a participator",
    "undertake ant regulated": "undertake any regulated",
    "includepureprotection": "include pure protection",
    "thepayee": "the payee",
    "beneficiallyowned byotherpersons": "beneficially owned by other persons",
    "Island;and (b)": "Island; and (b)",
    "apayment": "a payment",
    "Services(Exemption)Regulations": "Services (Exemption) Regulations",
    "thegoods": "the goods",
    "capacityof apayer orpayee,or both": "capacity of a payer or payee, or both",
    "thepayer andpayee": "the payer and payee",
    "n includes any body": "includes any body",
    "agreements,havingor capable": "agreements, having or capable",
    "thepublic": "the public",
    "eachparticular transaction": "each particular transaction",
    "prises determined": "prices determined",
    "ceasingto complywith(a)or(b)of this definition": "ceasing to comply with (a) or (b) of this definition",
    "anybenefits(in the form ofpensions": "any benefits (in the form of pensions",
    "Authorityunder section 18": "Authority under section 18",
    "share,includingstock,in the share": "share, including stock, in the share",
    "1988,whether such relationshipwas created": "1988, whether such relationship was created",
    "moneyof that trust": "money of that trust",
    "for,agovernment security": "for, a government security",
    "agovernment": "a government",
    "currencyof": "currency of",
    "apublic": "a public",
    "convertingthose": "converting those",
    "<br>": " ",
    "|\n": "\n",
    "\n|": '\n"',
    "|": '" ',
    '"units (in relation to a collective investment scheme)"': '"units" (in relation to a collective investment scheme)',
    '"connected individuals (in relation to a disposal or inquisition of shares in a company)"': '"connected individuals" (in relation to a disposal or inquisition of shares in a company)',
    '"administration services (in relation to company)"': '"administration services" (in relation to company)',
}


def re_steps(text: str) -> str:
    text = re.sub(
        r"## \*\*(\d+[A-Z]?)\*\*\s*\n\s*## \*\*([^\n*]+)\*\*",
        r"## **\1 \2**",
        text,
    )
    text = re.sub(
        r"^(?:> ?\d+ .*|\d+\s+[IVXLCDM]+\s+p\.\d+)\s*$\n?",
        "",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(r"\*\*\d+\*\*", "", text)
    text = re.sub(r"\b((?:18|19|20)\d{2})\d{1,2}(?=[a-z])", r"\1 ", text)
    text = re.sub(r"\b((?:18|19|20)\d{2})\d{1,2}\b", r"\1", text)
    text = re.sub(
        r"^\d+\s+(?:\d{4}\s*c\.\d+|SD\d+/\d+.*)\s*$\n?",
        "",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(r"\**\[\d+\]\**", "", text)
    text = text.replace(  # cannot be in the dict as needs to run before flattening
        "||means a legal relationship", "|trust|means a legal relationship"
    )
    # flatten definitions table
    text = re.sub(r"\|\n{2,}\|\|", " ", text)
    text = re.sub(r"^\|-+\|-+\|\s*\n?", "", text, flags=re.MULTILINE)
    text = text.replace("|**Expression**|**Definition**|\n", "")
    text = replace_from_dict(text, GLUED_WORD_FIXES)
    return text


RegulatedActivitiesOrder = DocSpecs(
    document="The Regulated Activities Order 2011",
    input_url="https://www.legislation.gov.im/cms/images/LEGISLATION/SUBORDINATE/2011/2011-0884/2011-0884_5.pdf",
    hierarchy="secondary legislation",
    input_path=project_root / "data/raw/custom/regulated_activities_order.pdf",
    major_name="part",
    minor_name="paragraph",
    start_line=16,
    end_line=1042,
    has_definition_section=True,
    definitions_start=882,
    definitions_end=952,
    re_steps=re_steps,
    header_matchers=[
        lambda line: line.startswith("## **SCHEDULE"),
        lambda line: line.startswith("## **CLASS"),
        lambda line: "## **Regulated activit" in line or "## **Exclusion" in line,
        lambda line: (
            line.startswith("## _")
            or line.startswith("_")
            or line.startswith("## **")
            and line[5].isdigit()
        ),
    ],
    # TODO: there are nested definitions, correctly attach to the right chunks by chance, confirm when doc is updated that this still holds
    is_definition_line=lambda line: line.startswith('"'),
    is_double_def_line=lambda segs: len(segs) == 5 and segs[2].strip() in ("or", "and"),
    is_false_dub_def=lambda segs: len(segs) == 5 and segs[2].strip() != "or",
    re_pack_splitter=lambda text: re.split(r"\n(?=- )", text),
    strip_md=lambda line: (
        line.replace("## **", "")
        .replace("**", "")
        .replace("##", "")
        .replace("_", "")
        .strip()
    ),
    h_strip_md=lambda line: (
        line.replace("- **", "")
        .replace("##", "")
        .replace("**", "")
        .replace(" — ", " ")
        .replace("_", "")
        .strip()
    ),
)
