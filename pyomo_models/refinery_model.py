"""
炼厂规划 Pyomo 模型实现

⚠️ 已弃用警告 (DEPRECATED WARNING)
本文件已被模块化重构。请使用新的模块化结构：
- model_sets_params_vars.py: 集合、参数、变量定义
- model_constraints.py: 约束定义
- model_objective.py: 目标函数定义  
- model_builder.py: 主模型构建器

为保持向后兼容，本文件仍导出 RefineryPlanningModel 类。
建议更新 import 语句为：
    from pyomo_models import RefineryPlanningModel
或：
    from pyomo_models.model_builder import RefineryPlanningModel
"""

# 为保持向后兼容，从新模块导入主类
import warnings
from .model_builder import RefineryPlanningModel

# 显示弃用警告
warnings.warn(
    "直接从 'pyomo_models.refinery_model' 导入已弃用。"
    "请改用 'from pyomo_models import RefineryPlanningModel' "
    "或 'from pyomo_models.model_builder import RefineryPlanningModel'。",
    DeprecationWarning,
    stacklevel=2
)

