"""
目标函数定义模块

本模块定义炼厂规划模型的目标函数（利润最大化）
"""
import pyomo.environ as pyo
from typing import Dict, Any


def define_objective(model, params_data: Dict[str, Any]):
    """
    定义目标函数
    
    Args:
        model: Pyomo ConcreteModel 实例
        params_data: 参数数据字典
    """
    def objective_rule(model):
        r"""
        利润最大化目标函数
        
        LaTeX: 
        $\max \text{Profit} = \sum_{s \in S_P, t \in T} c_P[s] \cdot FVI_{s,t} 
                            - \sum_{s \in S_M, t \in T} c_M[s] \cdot FVO_{s,t}
                            + \text{库存收益}$
        
        其中库存收益（仅对 Case 2 和 Case 3）：
        $\text{库存收益} = \sum_{s \in S_P, t \in T} (ci_P[s] \cdot FVLI_{s,t} - ci_M[s] \cdot FVLO_{s,t})
                         - \sum_{s \in S_M, t \in T} (ci_M[s] \cdot FVLO_{s,t} - ci_P[s] \cdot FVLI_{s,t})$
        
        作用：最大化销售收入减去原料成本和库存成本
        
        组成部分：
        1. 产品销售收入：产品价格 × 产品生产量
        2. 原料采购成本：原料价格 × 原料采购量
        3. 库存收益：入库和出库的价值变化
        r"""
        # ========== 产品销售收入 ==========
        # 计算所有时间周期内产品的销售总收入
        product_revenue = sum(
            model.c_P[s] * model.FVI[s, t]  # 产品价格 × 产品生产量
            for s in model.S_P for t in model.T
        )
        
        # ========== 原料采购成本 ==========
        # 计算所有时间周期内原料的采购总成本
        material_cost = sum(
            model.c_M[s] * model.FVO[s, t]  # 原料价格 × 原料采购量
            for s in model.S_M for t in model.T
        )
        
        # ========== 库存收益/成本（仅对有库存的案例） ==========
        inventory_profit = 0
        if any(params_data.get('LMax', {}).values()):
            # 产品库存收益：入库按库存价格计算收益，出库按库存价格计算成本
            inventory_profit += sum(
                model.ci_P[s] * model.FVLI[s, t] - model.ci_M[s] * model.FVLO[s, t]
                for s in model.S_P for t in model.T
            )
            # 原料库存成本：出库按库存价格计算成本，入库按库存价格计算收益
            inventory_profit -= sum(
                model.ci_M[s] * model.FVLO[s, t] - model.ci_P[s] * model.FVLI[s, t]
                for s in model.S_M for t in model.T
            )
        
        # ========== 总利润 ==========
        return product_revenue - material_cost + inventory_profit
    
    model.profit = pyo.Objective(rule=objective_rule, sense=pyo.maximize)  # 最大化利润目标函数
