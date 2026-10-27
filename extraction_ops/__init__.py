from extraction_ops.models import ToolBelt
from extraction_ops.toolbelts.aml_code import AmlCode
from extraction_ops.toolbelts.aml_handbook.aml_handbook import AmlHandbook
from extraction_ops.toolbelts.anti_terrorism import AntiTerror
from extraction_ops.toolbelts.business_plan.business_plan import BusinessPlan
from extraction_ops.toolbelts.change_ownership import ChangeOwnership
from extraction_ops.toolbelts.civ_pen_regs import CivPenRegs
from extraction_ops.toolbelts.conflicts import Conflicts
from extraction_ops.toolbelts.cp_guidance.cp_guidance import CpGuidance
from extraction_ops.toolbelts.cyber_security.cyber_security import CyberSecurity
from extraction_ops.toolbelts.dbroa15 import Dbroa
from extraction_ops.toolbelts.directors_trustees import DirectorsTrustees
from extraction_ops.toolbelts.exemptions.exemptions import Exemptions
from extraction_ops.toolbelts.f_and_p.f_and_p import FAndP
from extraction_ops.toolbelts.fiu_act import FiuAct
from extraction_ops.toolbelts.fsa08 import Fsa08
from extraction_ops.toolbelts.inspections_guidance import InspectionsGuidance
from extraction_ops.toolbelts.insurance import Insurance
from extraction_ops.toolbelts.insurance_civ_pen_regs import InsuranceCivPenRegs
from extraction_ops.toolbelts.insurance_regs import InsuranceRegs
from extraction_ops.toolbelts.nb_governance.nb_governance import NbGovernance
from extraction_ops.toolbelts.nra.banking_nra import BankingNra
from extraction_ops.toolbelts.nra.lpa_nra import LpaNra
from extraction_ops.toolbelts.nra.ml_nra import MlNra
from extraction_ops.toolbelts.nra.pf_nra import PfNra
from extraction_ops.toolbelts.nra.tcsp_nra import TcspNra
from extraction_ops.toolbelts.nra.tf_nra import TfNra
from extraction_ops.toolbelts.nra.vasp_nra import VaspNra
from extraction_ops.toolbelts.outsourcing import Outsourcing
from extraction_ops.toolbelts.poca_2008 import Poca
from extraction_ops.toolbelts.rbook_guidance.rbook_guidance import RbookGuidance
from extraction_ops.toolbelts.rbreach_guidance import RbreachGuidance
from extraction_ops.toolbelts.regulated_activities_order import Rao
from extraction_ops.toolbelts.rule_book.rule_book import RuleBook
from extraction_ops.toolbelts.rule_summaries.consent_notify import ConsentNotify
from extraction_ops.toolbelts.rule_summaries.policies import Policies
from extraction_ops.toolbelts.rule_summaries.record_keeping import RecordKeeping
from extraction_ops.toolbelts.rule_summaries.registers import Registers
from extraction_ops.toolbelts.sanctions_act import Sanctions
from extraction_ops.toolbelts.subordinated_loans import SubordinatedLoans
from extraction_ops.toolbelts.supplemental_information_document import (
    SupplementalInformation,
)
from extraction_ops.toolbelts.terror_financial_restrictions import FinancialRestrictions
from extraction_ops.toolbelts.terrorism_civ_pen import TerrorCivPen
from extraction_ops.toolbelts.tsp_guidance import TspGuidance

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
    Conflicts,
    BusinessPlan,
    RbookGuidance,
    ChangeOwnership,
    InspectionsGuidance,
    NbGovernance,
    CyberSecurity,
    DirectorsTrustees,
    CpGuidance,
    CivPenRegs,
    TspGuidance,
    RbreachGuidance,
    Outsourcing,
    FAndP,
    SubordinatedLoans,
    RecordKeeping,
    ConsentNotify,
    Registers,
    Policies,
    InsuranceCivPenRegs,
    InsuranceRegs,
    Insurance,
    MlNra,
    TfNra,
    PfNra,
    BankingNra,
    LpaNra,
    TcspNra,
    VaspNra,
]

TOOLBELT_REGISTRY: dict[str, ToolBelt] = {
    # AML/CFT Legislation
    "poca": Poca,
    "fiu": FiuAct,
    "code": AmlCode,
    "antiterror": AntiTerror,
    "terrorfr": FinancialRestrictions,
    "tcivpen": TerrorCivPen,
    "sanctions": Sanctions,
    # AML/CFT Guidance
    "handbook": AmlHandbook,
    "supplemental": SupplementalInformation,
    # FSA08 Legislation
    "rao": Rao,
    "exemptions": Exemptions,
    "dbroa": Dbroa,
    "fsa": Fsa08,
    "rule_book": RuleBook,
    "civ_pen_regs": CivPenRegs,
    # FSA08 Guidnace
    "conflicts": Conflicts,
    "business_plan": BusinessPlan,
    "rbook_guidance": RbookGuidance,
    "change_ownership": ChangeOwnership,
    "nb_governance": NbGovernance,
    "cyber_security": CyberSecurity,
    "directors_trustees": DirectorsTrustees,
    "tsp_guidance": TspGuidance,
    "rbreach_guidance": RbreachGuidance,
    "outsourcing": Outsourcing,
    "f_and_p": FAndP,
    "subordinated_loans": SubordinatedLoans,
    "record_keeping": RecordKeeping,
    "consent_notify": ConsentNotify,
    "registers": Registers,
    "policies": Policies,
    "insurance_civ_pen_regs": InsuranceCivPenRegs,
    "insurance_regs": InsuranceRegs,
    "insurance": Insurance,
    # Supervision
    "inspections_guidance": InspectionsGuidance,
    "cp_guidance": CpGuidance,
    # National Risk Assessments
    "ml_nra": MlNra,
    "tf_nra": TfNra,
    "pf_nra": PfNra,
    "banking_nra": BankingNra,
    "lpa_nra": LpaNra,
    "tcsp_nra": TcspNra,
    "vasp_nra": VaspNra,
}
