from extraction_ops.models import ToolBelt
from extraction_ops.toolbelts.aml_handbook.aml_handbook import AmlHandbook
from extraction_ops.toolbelts.aml_code import AmlCode
from extraction_ops.toolbelts.poca_2008 import Poca
from extraction_ops.toolbelts.supplemental_information_document import (
    SupplementalInformation,
)

ALL_TOOLBELTS: list[ToolBelt] = [AmlCode, AmlHandbook, SupplementalInformation, Poca]

TOOLBELT_REGISTRY: dict[str, ToolBelt] = {
    "code": AmlCode,
    "handbook": AmlHandbook,
    "supplemental": SupplementalInformation,
    "poca": Poca,
}
