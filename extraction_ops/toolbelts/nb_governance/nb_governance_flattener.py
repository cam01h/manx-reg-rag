from extraction_ops.toolbelts.shared_funcs import replace_section

# Appendix 1 is a two-column table of bodies and their websites. pymupdf4llm merges the IoD
# and OECD rows into one cell, splits the Combined Code note off the FRC row and runs the
# ECGI paragraph down the first column, so it is rewritten by hand
_APPENDIX_1_FLAT = """[Editors note: the below is a flattened table]

Standard-setting and professional bodies:

- ACCA: Association of Chartered Certified Accountants - www.acca.co.uk
- FCA: Financial Conduct Authority - www.fca.org.uk
- FRC: Financial Reporting Council - www.frc.org.uk (Combined Code - Derived from the Cadbury and Greenbury Reports)
- ICSA: Institute of Chartered Secretaries and Administrators - www.icsa.org.uk
- ICAEW: Institute of Chartered Accountants in England and Wales - www.icaew.com
- IoD: Institute of Directors - www.iod.com
- OECD: Organisation for Economic Co-operation & Development - www.oecd.org

Reports on Corporate Governance:

- European Confederation of Directors' Associations - www.ecoda.org
- The European Corporate Governance Institute (www.ecgi.org) has available on its site an Index of Codes page which includes the main reports on corporate governance published worldwide (listed by country). The UK list includes amongst other entries:

"""


def flatten_appendix_1_table(text: str) -> str:
    return replace_section(
        text,
        "## **Standard-setting and professional bodies",
        "- Cadbury (1993",
        _APPENDIX_1_FLAT,
    )
