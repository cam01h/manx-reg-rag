from extraction_ops.models import ToolBelt
from extraction_ops.toolbelts.aml_handbook.aml_handbook import AmlHandbook
from extraction_ops.toolbelts.aml_code import AmlCode

ALL_TOOLBELTS: list[ToolBelt] = [AmlCode, AmlHandbook]

TOOLBELT_REGISTRY: dict[str, ToolBelt] = {"code": AmlCode, "handbook": AmlHandbook}
