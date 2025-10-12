"""
炼厂规划 Pyomo 模型包

本包提供炼厂规划模型的完整实现，包括：
- 数据读取器：从 Excel 文件读取集合和参数
- 模型构建器：构建和求解 Pyomo 优化模型
- 模块化约束定义：集合、参数、变量、约束、目标函数分离定义
"""
from .data_reader import RefineryDataReader
from .model_builder import RefineryPlanningModel, create_case_model

__all__ = ['RefineryDataReader', 'RefineryPlanningModel', 'create_case_model']
