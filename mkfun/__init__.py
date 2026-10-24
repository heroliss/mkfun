"""从两份嵌套样例编译数据重组规则，不执行生成的源代码。"""
from .core import (
    MappingError, MappingPlan, StructureError, OutputError,
    ReverseValidationError, compile_mapping, flatten, mkfun,
)

__version__ = "5.0.0"
__all__ = [
    "MappingError", "MappingPlan", "StructureError", "OutputError",
    "ReverseValidationError", "compile_mapping", "flatten", "mkfun",
]
