from extraction_ops.models import ToolBelt
from extraction_ops.toolbelts.aml_code import AmlCode
from extraction_ops.toolbelts.aml_handbook.aml_handbook import AmlHandbook
from extraction_ops.toolbelts.anti_terrorism import AntiTerror
from extraction_ops.toolbelts.dbroa15 import Dbroa
from extraction_ops.toolbelts.exemptions import Exemptions
from extraction_ops.toolbelts.fiu_act import FiuAct
from extraction_ops.toolbelts.fsa08 import Fsa08
from extraction_ops.toolbelts.poca_2008 import Poca
from extraction_ops.toolbelts.regulated_activities_order import Rao
from extraction_ops.toolbelts.rule_book.rule_book import RuleBook
from extraction_ops.toolbelts.sanctions_act import Sanctions
from extraction_ops.toolbelts.supplemental_information_document import (
    SupplementalInformation,
)
from extraction_ops.toolbelts.terror_financial_restrictions import FinancialRestrictions
from extraction_ops.toolbelts.terrorism_civ_pen import TerrorCivPen

ALL_TOOLBELTS: list[ToolBelt] = [
    AmlCode,
    AmlHandbook,
    SupplementalInformation,
    Poca,
    FiuAct,
    TerrorCivPen,
    AntiTerror,
    Rao,
    FinancialRestrictions,
    Dbroa,
    Sanctions,
    Fsa08,
    RuleBook,
    Exemptions,
]

TOOLBELT_REGISTRY: dict[str, ToolBelt] = {
    "code": AmlCode,
    "handbook": AmlHandbook,
    "supplemental": SupplementalInformation,
    "poca": Poca,
    "fiu": FiuAct,
    "tcivpen": TerrorCivPen,
    "antiterror": AntiTerror,
    "rao": Rao,
    "terrorfr": FinancialRestrictions,
    "dbroa": Dbroa,
    "sanctions": Sanctions,
    "fsa": Fsa08,
    "rule_book": RuleBook,
    "exemptions": Exemptions,
}
