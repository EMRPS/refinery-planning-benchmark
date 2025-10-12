"""
炼厂规划 Pyomo 模型实现

基于论文 "A production planning benchmark for real-world refinery-petrochemical complexes"
实现了包含 CDU、工艺单元、混合器、分流器、调合器等的完整 MINLP 模型
"""
import pyomo.environ as pyo
from pyomo.opt import SolverFactory
from typing import Dict, Any
import time
import os
import sys

# 添加当前目录到路径以支持直接运行
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from data_reader import RefineryDataReader
else:
    from .data_reader import RefineryDataReader


class RefineryPlanningModel:
    """炼厂规划 Pyomo 模型"""
    
    def __init__(self, case_folder: str):
        """
        初始化模型
        
        Args:
            case_folder: 案例文件夹路径
        """
        self.case_folder = case_folder
        self.reader = RefineryDataReader(case_folder)
        self.sets, self.params = self.reader.read_all_data()
        self.model = None
        
    def build_model(self):
        """构建完整的 Pyomo 模型"""
        print(f"正在构建 {self.case_folder} 的 Pyomo 模型...")
        start_time = time.time()
        
        self.model = pyo.ConcreteModel(name=f"RefineryPlanning_{self.case_folder}")
        
        # 定义集合
        self._define_sets()
        
        # 定义参数
        self._define_parameters()
        
        # 定义变量
        self._define_variables()
        
        # 定义约束
        self._define_constraints()
        
        # 定义目标函数
        self._define_objective()
        
        build_time = time.time() - start_time
        print(f"模型构建完成，耗时 {build_time:.2f} 秒")
        
        return self.model
    
    def _define_sets(self):
        """定义所有集合"""
        m = self.model
        
        # 基础集合
        m.T = pyo.Set(initialize=self.sets.get('T', ['1']))  # 时间周期
        m.S = pyo.Set(initialize=self.sets['S'])  # 所有流
        m.U = pyo.Set(initialize=self.sets['U'])  # 所有单元
        m.M = pyo.Set(initialize=self.sets['M'])  # 所有批次
        m.Q = pyo.Set(initialize=self.sets['Q'])  # 所有性质
        m.C = pyo.Set(initialize=self.sets['C'])  # 容量索引
        
        # 子集
        m.S_P = pyo.Set(initialize=self.sets.get('S_P', []))  # 产品流
        m.S_M = pyo.Set(initialize=self.sets.get('S_M', []))  # 原料流
        m.UCDU = pyo.Set(initialize=self.sets.get('UCDU', []))  # CDU 单元
        m.UPF = pyo.Set(initialize=self.sets.get('UPF', []))  # 固定收率工艺单元
        m.UPD = pyo.Set(initialize=self.sets.get('UPD', []))  # Delta-base 工艺单元
        m.UMIX = pyo.Set(initialize=self.sets.get('UMIX', []))  # 混合器
        m.USPL = pyo.Set(initialize=self.sets.get('USPL', []))  # 分流器
        m.UBLD = pyo.Set(initialize=self.sets.get('UBLD', []))  # 调合器
        
        # 性质子集
        m.SPG = pyo.Set(initialize=self.sets.get('SPG', []))  # 比重性质
        m.Qv = pyo.Set(initialize=self.sets.get('Qv', []))  # 体积基性质
        m.Qw = pyo.Set(initialize=self.sets.get('Qw', []))  # 质量基性质
        m.Qp = pyo.Set(initialize=self.sets.get('Qp', []))  # 组分比例性质
        
        # 二元/多元集合
        m.IU = pyo.Set(initialize=self.sets.get('IU', []), dimen=2)  # (单元, 输入流)
        m.OU = pyo.Set(initialize=self.sets.get('OU', []), dimen=2)  # (单元, 输出流)
        m.IM = pyo.Set(initialize=self.sets.get('IM', []), dimen=3)  # (单元, 批次, 输入流)
        m.OM = pyo.Set(initialize=self.sets.get('OM', []), dimen=3)  # (单元, 批次, 输出流)
        m.SC = pyo.Set(initialize=self.sets.get('SC', []), dimen=None)  # Swing-cut 对
        m.SQ = pyo.Set(initialize=self.sets.get('SQ', []), dimen=2)  # (流, 性质) 对
        m.FIX = pyo.Set(initialize=self.sets.get('FIX', []), dimen=2)  # 固定性质
        m.QT = pyo.Set(initialize=self.sets.get('QT', []), dimen=3)  # 性质传递
        m.VMQ = pyo.Set(initialize=self.sets.get('VMQ', []), dimen=None)  # 虚拟批次性质
        m.DBSQ = pyo.Set(initialize=self.sets.get('DBSQ', []), dimen=None)  # Delta-base 流性质对
        m.CAPIN = pyo.Set(initialize=self.sets.get('CAPIN', []))  # 输入容量索引
        m.CAPOUT = pyo.Set(initialize=self.sets.get('CAPOUT', []))  # 输出容量索引
        m.CAPS = pyo.Set(initialize=self.sets.get('CAPS', []), dimen=2)  # 容量-流对
        m.CDUMQ = pyo.Set(initialize=self.sets.get('CDUMQ', []), dimen=None)  # CDU 批次性质约束
        m.CRU = pyo.Set(initialize=self.sets.get('CRU', []))  # 原油性质约束
        m.RB = pyo.Set(initialize=self.sets.get('RB', []))  # 比例调合单元
        
    def _define_parameters(self):
        """定义所有参数"""
        m = self.model
        
        # 价格参数
        c_P = self.params.get('c_P', {})
        c_M = self.params.get('c_M', {})
        ci_P = self.params.get('ci_P', {})
        ci_M = self.params.get('ci_M', {})
        
        m.c_P = pyo.Param(m.S_P, initialize=c_P, default=0.0, mutable=True)
        m.c_M = pyo.Param(m.S_M, initialize=c_M, default=0.0, mutable=True)
        m.ci_P = pyo.Param(m.S_P, initialize=ci_P, default=0.0, mutable=True)
        m.ci_M = pyo.Param(m.S_M, initialize=ci_M, default=0.0, mutable=True)
        
        # 流量边界参数
        FVMin_data = self.params.get('FVMin', {})
        FVMax_data = self.params.get('FVMax', {})
        
        def FVMin_init(model, s, t):
            return FVMin_data.get((s, t), 0.0)
        
        def FVMax_init(model, s, t):
            return FVMax_data.get((s, t), 1e8)  # 大数作为无界
        
        m.FVMin = pyo.Param(m.S, m.T, initialize=FVMin_init, default=0.0)
        m.FVMax = pyo.Param(m.S, m.T, initialize=FVMax_init, default=1e8)
        
        # 性质参数
        FQ0_data = self.params.get('FQ0', {})
        FQMin_data = self.params.get('FQMin', {})
        FQMax_data = self.params.get('FQMax', {})
        
        def FQ0_init(model, s, q):
            return FQ0_data.get((s, q), None)
        
        def FQMin_init(model, s, q):
            return FQMin_data.get((s, q), -1e8)
        
        def FQMax_init(model, s, q):
            return FQMax_data.get((s, q), 1e8)
        
        m.FQ0 = pyo.Param(m.SQ, initialize=FQ0_init, default=None)
        m.FQMin = pyo.Param(m.SQ, initialize=FQMin_init, default=-1e8)
        m.FQMax = pyo.Param(m.SQ, initialize=FQMax_init, default=1e8)
        
        # CDU 参数
        y_data = self.params.get('y', {})
        phi_data = self.params.get('phi', {})
        FQcut_data = self.params.get('FQcut', {})
        FQcrd_data = self.params.get('FQcrd', {})
        
        # y(u, m, s_in, s_out) - 4 索引
        m.y = pyo.Param(m.U, m.M, m.S, m.S, initialize=y_data, default=0.0, mutable=True)
        m.phi = pyo.Param(m.U, m.M, m.S, m.S, initialize=phi_data, default=0.0, mutable=True)
        
        # FQcut(u, m, s_in, s, q) - 5 索引
        def FQcut_init(model, u, mm, s_in, s, q):
            return FQcut_data.get((u, mm, s_in, s, q), 1.0)
        m.FQcut = pyo.Param(m.U, m.M, m.S, m.S, m.Q, initialize=FQcut_init, default=1.0, mutable=True)
        
        # FQcrd(u, m, s, q) - 4 索引  
        def FQcrd_init(model, u, mm, s, q):
            return FQcrd_data.get((u, mm, s, q), 1.0)
        m.FQcrd = pyo.Param(m.U, m.M, m.S, m.Q, initialize=FQcrd_init, default=1.0, mutable=True)
        
        # 工艺单元参数
        gamma_data = self.params.get('gamma', {})
        B_data = self.params.get('B', {})
        delta_data = self.params.get('delta', {})
        Del_data = self.params.get('Del', {})
        alpha_data = self.params.get('alpha', {})
        w_data = self.params.get('w', {})
        
        # gamma(u, m, s) - 3 索引
        def gamma_init(model, u, mm, s):
            return gamma_data.get((u, mm, s), 0.0)
        m.gamma = pyo.Param(m.U, m.M, m.S, initialize=gamma_init, default=0.0, mutable=True)
        
        # B, delta, Del - 基于 DBSQ
        def B_init(model, u, mm, s, q):
            return B_data.get((u, mm, s, q), 0.0)
        m.B = pyo.Param(m.U, m.M, m.S, m.Q, initialize=B_init, default=0.0, mutable=True)
        
        def delta_init(model, u, mm, s, ss, qq):
            return delta_data.get((u, mm, s, ss, qq), 0.0)
        m.delta = pyo.Param(m.U, m.M, m.S, m.S, m.Q, initialize=delta_init, default=0.0, mutable=True)
        
        def Del_init(model, u, mm, s, q):
            return Del_data.get((u, mm, s, q), 1.0)
        m.Del = pyo.Param(m.U, m.M, m.S, m.Q, initialize=Del_init, default=1.0, mutable=True)
        
        # alpha(s, s_out, q) - 3 索引
        def alpha_init(model, s, s_out, q):
            return alpha_data.get((s, s_out, q), 1.0)
        m.alpha = pyo.Param(m.S, m.S, m.Q, initialize=alpha_init, default=1.0, mutable=True)
        
        # w 参数 - 基于 VMQ
        def w_init(model, u, mm, s, q):
            return w_data.get((u, mm, s, q), 0.0)
        m.w = pyo.Param(m.U, m.M, m.S, m.Q, initialize=w_init, default=0.0, mutable=True)
        
        # 容量参数
        FVCMin_data = self.params.get('FVCMin', {})
        FVCMax_data = self.params.get('FVCMax', {})
        
        def FVCMin_init(model, c, t):
            return FVCMin_data.get((c, t), 0.0)
        
        def FVCMax_init(model, c, t):
            return FVCMax_data.get((c, t), 1e8)
        
        m.FVCMin = pyo.Param(m.C, m.T, initialize=FVCMin_init, default=0.0)
        m.FVCMax = pyo.Param(m.C, m.T, initialize=FVCMax_init, default=1e8)
        
        # 调合参数
        FQBMin_data = self.params.get('FQBMin', {})
        FQBMax_data = self.params.get('FQBMax', {})
        
        m.FQBMin = pyo.Param(m.UBLD, m.Q, initialize=FQBMin_data, default=-1e8, mutable=True)
        m.FQBMax = pyo.Param(m.UBLD, m.Q, initialize=FQBMax_data, default=1e8, mutable=True)
        
        # 混合器性质约束参数
        FQVMin_data = self.params.get('FQVMin', {})
        FQVMax_data = self.params.get('FQVMax', {})
        
        m.FQVMin = pyo.Param(m.UMIX, m.M, m.Q, initialize=FQVMin_data, default=-1e8, mutable=True)
        m.FQVMax = pyo.Param(m.UMIX, m.M, m.Q, initialize=FQVMax_data, default=1e8, mutable=True)
        
        # 库存参数
        LMin_data = self.params.get('LMin', {})
        LMax_data = self.params.get('LMax', {})
        L0_data = self.params.get('L0', {})
        
        def LMin_init(model, s, t):
            return LMin_data.get((s, t), 0.0)
        
        def LMax_init(model, s, t):
            return LMax_data.get((s, t), 0.0)  # 默认无库存
        
        m.LMin = pyo.Param(m.S, m.T, initialize=LMin_init, default=0.0)
        m.LMax = pyo.Param(m.S, m.T, initialize=LMax_init, default=0.0)
        m.L0 = pyo.Param(m.S, initialize=L0_data, default=0.0)
        
        # 原油总性质约束参数
        MFQMin_data = self.params.get('MFQMin', {})
        MFQMax_data = self.params.get('MFQMax', {})
        
        m.MFQMin = pyo.Param(m.Q, initialize=MFQMin_data, default=-1e8, mutable=True)
        m.MFQMax = pyo.Param(m.Q, initialize=MFQMax_data, default=1e8, mutable=True)
        
    def _define_variables(self):
        """定义所有变量"""
        m = self.model
        
        # 流变量
        m.FVI = pyo.Var(m.S, m.T, domain=pyo.NonNegativeReals, bounds=(0, None))
        m.FVO = pyo.Var(m.S, m.T, domain=pyo.NonNegativeReals, bounds=(0, None))
        
        # FVM(u, m, s, t) 批次流量变量
        def FVM_index_set(model):
            for t in model.T:
                for (u, mm, s) in model.IM:
                    yield (u, mm, s, t)
                for (u, mm, s) in model.OM:
                    yield (u, mm, s, t)
        m.FVM_index = pyo.Set(initialize=FVM_index_set, dimen=4)
        m.FVM = pyo.Var(m.FVM_index, domain=pyo.NonNegativeReals, bounds=(0, None))
        
        # 性质变量
        m.FQ = pyo.Var(m.SQ, m.T, domain=pyo.Reals, bounds=(None, None))
        
        # 体积流变量（用于调合和混合）
        m.V = pyo.Var(m.S, m.T, domain=pyo.NonNegativeReals, bounds=(0, None))
        
        # VM(u, m, s, t) 批次体积流量变量
        m.VM = pyo.Var(m.FVM_index, domain=pyo.NonNegativeReals, bounds=(0, None))
        
        # Delta-base 收率变量 Gamma(u, m, s, t)
        def Gamma_index_set(model):
            for t in model.T:
                for (u, mm, s) in model.OM:
                    yield (u, mm, s, t)
                for (u, mm, s) in model.IM:
                    yield (u, mm, s, t)
        m.Gamma_index = pyo.Set(initialize=Gamma_index_set, dimen=4)
        m.Gamma = pyo.Var(m.Gamma_index, domain=pyo.Reals, bounds=(None, None))
        
        # 库存变量
        m.L = pyo.Var(m.S, m.T, domain=pyo.NonNegativeReals, bounds=(0, None))
        m.FVLI = pyo.Var(m.S, m.T, domain=pyo.NonNegativeReals, bounds=(0, None))
        m.FVLO = pyo.Var(m.S, m.T, domain=pyo.NonNegativeReals, bounds=(0, None))
        
        # 库存二元变量（仅对有库存的案例）
        has_inventory = any(self.params.get('LMax', {}).values())
        if has_inventory:
            m.X = pyo.Var(m.S, m.T, domain=pyo.Binary)
        
    def _define_constraints(self):
        """定义所有约束"""
        print("  正在添加约束...")
        
        self._add_material_balance_constraints()
        self._add_cdu_constraints()
        self._add_process_unit_constraints()
        self._add_mixer_constraints()
        self._add_splitter_constraints()
        self._add_blender_constraints()
        self._add_capacity_constraints()
        self._add_bound_constraints()
        self._add_inventory_constraints()
        
    def _add_material_balance_constraints(self):
        """物料平衡约束 (Eq. 2 in paper)"""
        m = self.model
        
        # 批次求和约束 - 输入流
        def batch_sum_input_rule(model, u, s, t):
            if (u, s) not in model.IU:
                return pyo.Constraint.Skip
            batches = [(uu, mm, ss) for (uu, mm, ss) in model.IM if uu == u and ss == s]
            if not batches:
                return model.FVI[s, t] == 0
            return model.FVI[s, t] == sum(model.FVM[uu, mm, ss, t] for (uu, mm, ss) in batches)
        
        m.batch_sum_input = pyo.Constraint(m.U, m.S, m.T, rule=batch_sum_input_rule)
        
        # 批次求和约束 - 输出流
        def batch_sum_output_rule(model, u, s, t):
            if (u, s) not in model.OU:
                return pyo.Constraint.Skip
            batches = [(uu, mm, ss) for (uu, mm, ss) in model.OM if uu == u and ss == s]
            if not batches:
                return model.FVO[s, t] == 0
            return model.FVO[s, t] == sum(model.FVM[uu, mm, ss, t] for (uu, mm, ss) in batches)
        
        m.batch_sum_output = pyo.Constraint(m.U, m.S, m.T, rule=batch_sum_output_rule)
        
        # 混合器物料平衡
        def mixer_balance_rule(model, u, m_idx, t):
            if u not in model.UMIX:
                return pyo.Constraint.Skip
            inputs = [(uu, mm, ss) for (uu, mm, ss) in model.IM if uu == u and mm == m_idx]
            outputs = [(uu, mm, ss) for (uu, mm, ss) in model.OM if uu == u and mm == m_idx]
            if not inputs or not outputs:
                return pyo.Constraint.Skip
            return sum(model.FVM[i, t] for i in inputs) == sum(model.FVM[o, t] for o in outputs)
        
        m.mixer_balance = pyo.Constraint(m.UMIX, m.M, m.T, rule=mixer_balance_rule)
        
        # 分流器和调合器物料平衡
        def splitter_blender_balance_rule(model, u, t):
            if u not in (model.USPL | model.UBLD):
                return pyo.Constraint.Skip
            inputs = [s for (uu, s) in model.IU if uu == u]
            outputs = [s for (uu, s) in model.OU if uu == u]
            if not inputs or not outputs:
                return pyo.Constraint.Skip
            return sum(model.FVI[s, t] for s in inputs) == sum(model.FVO[s, t] for s in outputs)
        
        m.splitter_blender_balance = pyo.Constraint(m.U, m.T, rule=splitter_blender_balance_rule)
        
    def _add_cdu_constraints(self):
        """CDU 约束 (Swing-cut model)"""
        m = self.model
        
        # CDU 产量约束 - 简化版本（忽略 swing-cut 以简化模型）
        def cdu_yield_rule(model, u, m_idx, s, t):
            if u not in model.UCDU or (u, m_idx, s) not in model.OM:
                return pyo.Constraint.Skip
            
            inputs = [(uu, mm, ss) for (uu, mm, ss) in model.IM if uu == u and mm == m_idx]
            if not inputs:
                return pyo.Constraint.Skip
            
            # 基本收率计算（简化，忽略 swing-cut）
            # FVM[u, m, s_out, t] = sum(y[u, m, s_in, s_out] * FVM[u, m, s_in, t])
            return model.FVM[u, m_idx, s, t] == sum(
                model.y[u, m_idx, s_in, s] * model.FVM[u, m_idx, s_in, t]
                for (_, _, s_in) in inputs
            )
        
        m.cdu_yield = pyo.Constraint(m.UCDU, m.M, m.S, m.T, rule=cdu_yield_rule)
        
    def _add_process_unit_constraints(self):
        """工艺单元约束"""
        m = self.model
        
        # 固定收率工艺单元 (Eq. 11 in paper)
        def fixed_yield_rule(model, u, m_idx, s, t):
            if u not in model.UPF or (u, m_idx, s) not in (model.IM | model.OM):
                return pyo.Constraint.Skip
            
            inputs = [(uu, mm, ss) for (uu, mm, ss) in model.IM if uu == u and mm == m_idx]
            all_streams = [(uu, mm, ss) for (uu, mm, ss) in (model.IM | model.OM) if uu == u and mm == m_idx]
            
            if not inputs or not all_streams:
                return pyo.Constraint.Skip
            
            gamma_sum = sum(model.gamma[uu, mm, ss] for (uu, mm, ss) in all_streams)
            
            # 避免除零
            if pyo.value(gamma_sum) == 0:
                return pyo.Constraint.Skip
            
            return model.FVM[u, m_idx, s, t] * gamma_sum == (
                model.gamma[u, m_idx, s] * 
                sum(model.FVM[u, m_idx, s_in, t] for (_, _, s_in) in inputs)
            )
        
        m.fixed_yield = pyo.Constraint(m.UPF, m.M, m.S, m.T, rule=fixed_yield_rule)
        
        # Delta-base 收率计算 (Eq. 12 in paper)
        def delta_base_gamma_rule(model, u, m_idx, s, t):
            if u not in model.UPD or (u, m_idx, s) not in (model.IM | model.OM):
                return pyo.Constraint.Skip
            
            gamma_base = model.gamma[u, m_idx, s]
            
            # 收集影响收率的性质
            delta_terms = []
            for (uu, mm, ss, qq) in model.DBSQ:
                if uu == u and mm == m_idx and (ss, qq) in model.SQ:
                    B_val = model.B[u, m_idx, ss, qq]
                    Delta_val = model.Del[u, m_idx, ss, qq]
                    delta_val = model.delta[u, m_idx, s, ss, qq]
                    
                    if pyo.value(Delta_val) != 0:
                        delta_terms.append(
                            (model.FQ[ss, qq, t] - B_val) * delta_val / Delta_val
                        )
            
            if not delta_terms:
                return model.Gamma[u, m_idx, s, t] == gamma_base
            
            return model.Gamma[u, m_idx, s, t] == gamma_base + sum(delta_terms)
        
        m.delta_base_gamma = pyo.Constraint(m.UPD, m.M, m.S, m.T, rule=delta_base_gamma_rule)
        
        # Delta-base 产量约束 (Eq. 13 in paper)
        def delta_base_yield_rule(model, u, m_idx, s, t):
            if u not in model.UPD or (u, m_idx, s) not in (model.IM | model.OM):
                return pyo.Constraint.Skip
            
            inputs = [(uu, mm, ss) for (uu, mm, ss) in model.IM if uu == u and mm == m_idx]
            all_streams = [(uu, mm, ss) for (uu, mm, ss) in (model.IM | model.OM) if uu == u and mm == m_idx]
            
            if not inputs or not all_streams:
                return pyo.Constraint.Skip
            
            gamma_sum = sum(model.Gamma[uu, mm, ss, t] for (uu, mm, ss) in all_streams)
            
            # 使用双线性形式避免除法
            return model.FVM[u, m_idx, s, t] * gamma_sum == (
                model.Gamma[u, m_idx, s, t] * 
                sum(model.FVM[u, m_idx, s_in, t] for (_, _, s_in) in inputs)
            )
        
        m.delta_base_yield = pyo.Constraint(m.UPD, m.M, m.S, m.T, rule=delta_base_yield_rule)
        
        # 性质传递 (Eq. 14 in paper)
        def property_transfer_rule(model, s, s_out, q, t):
            if (s, s_out, q) not in model.QT:
                return pyo.Constraint.Skip
            if (s, q) in model.FIX or (s_out, q) in model.FIX:
                return pyo.Constraint.Skip
            if (s, q) not in model.SQ or (s_out, q) not in model.SQ:
                return pyo.Constraint.Skip
            
            alpha_val = model.alpha[s, s_out, q]
            return model.FQ[s_out, q, t] == alpha_val * model.FQ[s, q, t]
        
        m.property_transfer = pyo.Constraint(m.S, m.S, m.Q, m.T, rule=property_transfer_rule)
        
    def _add_mixer_constraints(self):
        """混合器约束"""
        m = self.model
        
        # 体积-质量关系（通过比重） (Eq. 15 in paper)
        def mixer_volume_mass_rule(model, u, m_idx, s, t):
            if u not in model.UMIX or (u, m_idx, s) not in (model.IM | model.OM):
                return pyo.Constraint.Skip
            
            # 查找比重性质
            spg_props = [q for q in model.SPG if (s, q) in model.SQ]
            if not spg_props:
                return pyo.Constraint.Skip
            
            q_spg = spg_props[0]  # 使用第一个比重性质
            
            # VM * FQ = FVM （体积 * 密度 = 质量）
            return model.VM[u, m_idx, s, t] * model.FQ[s, q_spg, t] == model.FVM[u, m_idx, s, t]
        
        m.mixer_volume_mass = pyo.Constraint(m.UMIX, m.M, m.S, m.T, rule=mixer_volume_mass_rule)
        
        # 混合器体积平衡
        def mixer_volume_balance_rule(model, u, m_idx, s, t):
            if u not in model.UMIX or (u, m_idx, s) not in model.OM:
                return pyo.Constraint.Skip
            
            inputs = [(uu, mm, ss) for (uu, mm, ss) in model.IM if uu == u and mm == m_idx]
            if not inputs:
                return pyo.Constraint.Skip
            
            return model.VM[u, m_idx, s, t] == sum(
                model.VM[uu, mm, ss, t] for (uu, mm, ss) in inputs
            )
        
        m.mixer_volume_balance = pyo.Constraint(m.UMIX, m.M, m.S, m.T, rule=mixer_volume_balance_rule)
        
        # 混合器体积基性质混合 (Eq. 16b in paper)
        def mixer_volume_property_rule(model, u, m_idx, s, q, t):
            if u not in model.UMIX or (u, m_idx, s) not in model.OM:
                return pyo.Constraint.Skip
            if q not in model.Qv or (s, q) in model.FIX:
                return pyo.Constraint.Skip
            if (s, q) not in model.SQ:
                return pyo.Constraint.Skip
            
            inputs = [(uu, mm, ss) for (uu, mm, ss) in model.IM if uu == u and mm == m_idx and (ss, q) in model.SQ]
            if not inputs:
                return pyo.Constraint.Skip
            
            return model.VM[u, m_idx, s, t] * model.FQ[s, q, t] == sum(
                model.VM[uu, mm, ss, t] * model.FQ[ss, q, t] for (uu, mm, ss) in inputs
            )
        
        m.mixer_volume_property = pyo.Constraint(m.UMIX, m.M, m.S, m.Q, m.T, rule=mixer_volume_property_rule)
        
        # 混合器质量基性质混合 (Eq. 16c in paper)
        def mixer_mass_property_rule(model, u, m_idx, s, q, t):
            if u not in model.UMIX or (u, m_idx, s) not in model.OM:
                return pyo.Constraint.Skip
            if q not in model.Qw or (s, q) in model.FIX:
                return pyo.Constraint.Skip
            if (s, q) not in model.SQ:
                return pyo.Constraint.Skip
            
            inputs = [(uu, mm, ss) for (uu, mm, ss) in model.IM if uu == u and mm == m_idx and (ss, q) in model.SQ]
            if not inputs:
                return pyo.Constraint.Skip
            
            return model.FVM[u, m_idx, s, t] * model.FQ[s, q, t] == sum(
                model.FVM[uu, mm, ss, t] * model.FQ[ss, q, t] for (uu, mm, ss) in inputs
            )
        
        m.mixer_mass_property = pyo.Constraint(m.UMIX, m.M, m.S, m.Q, m.T, rule=mixer_mass_property_rule)
        
    def _add_splitter_constraints(self):
        """分流器约束"""
        m = self.model
        
        # 分流器性质传递 (Eq. 20 in paper)
        def splitter_property_rule(model, u, s_in, s_out, q, t):
            if u not in model.USPL:
                return pyo.Constraint.Skip
            if (u, s_in) not in model.IU or (u, s_out) not in model.OU:
                return pyo.Constraint.Skip
            if (s_in, q) not in model.SQ or (s_out, q) not in model.SQ:
                return pyo.Constraint.Skip
            
            return model.FQ[s_out, q, t] == model.FQ[s_in, q, t]
        
        m.splitter_property = pyo.Constraint(m.USPL, m.S, m.S, m.Q, m.T, rule=splitter_property_rule)
        
    def _add_blender_constraints(self):
        """调合器约束"""
        m = self.model
        
        # 体积-质量关系 (Eq. 21 in paper)
        def blender_volume_mass_rule(model, u, s, t):
            if u not in model.UBLD or (u, s) not in model.IU:
                return pyo.Constraint.Skip
            
            # 查找比重性质
            spg_props = [q for q in model.SPG if (s, q) in model.SQ]
            if not spg_props:
                return pyo.Constraint.Skip
            
            q_spg = spg_props[0]
            return model.V[s, t] * model.FQ[s, q_spg, t] == model.FVI[s, t]
        
        m.blender_volume_mass = pyo.Constraint(m.UBLD, m.S, m.T, rule=blender_volume_mass_rule)
        
        # 调合性质约束 - 比重 (Eq. 22a in paper)
        def blender_spg_rule(model, u, q, t):
            if u not in model.UBLD or q not in model.SPG:
                return pyo.Constraint.Skip
            
            inputs = [(uu, ss) for (uu, ss) in model.IU if uu == u and (ss, q) in model.SQ]
            if not inputs:
                return pyo.Constraint.Skip
            
            min_val = model.FQBMin.get((u, q), -1e8)
            max_val = model.FQBMax.get((u, q), 1e8)
            
            if abs(min_val) < 1e7:
                lhs = min_val * sum(model.V[ss, t] for (_, ss) in inputs)
                rhs = sum(model.FVI[ss, t] for (_, ss) in inputs)
                yield (lhs, rhs, None)
            
            if abs(max_val) < 1e7:
                lhs = sum(model.FVI[ss, t] for (_, ss) in inputs)
                rhs = max_val * sum(model.V[ss, t] for (_, ss) in inputs)
                yield (None, lhs, rhs)
        
        m.blender_spg = pyo.Constraint(m.UBLD, m.Q, m.T, rule=blender_spg_rule)
        
        # 调合性质约束 - 体积基 (Eq. 22b in paper)
        def blender_volume_property_rule(model, u, q, t):
            if u not in model.UBLD or q not in model.Qv:
                return pyo.Constraint.Skip
            
            inputs = [(uu, ss) for (uu, ss) in model.IU if uu == u and (ss, q) in model.SQ]
            if not inputs:
                return pyo.Constraint.Skip
            
            min_val = model.FQBMin.get((u, q), -1e8)
            max_val = model.FQBMax.get((u, q), 1e8)
            
            if abs(min_val) < 1e7:
                lhs = min_val * sum(model.V[ss, t] for (_, ss) in inputs)
                rhs = sum(model.V[ss, t] * model.FQ[ss, q, t] for (_, ss) in inputs)
                yield (lhs, rhs, None)
            
            if abs(max_val) < 1e7:
                lhs = sum(model.V[ss, t] * model.FQ[ss, q, t] for (_, ss) in inputs)
                rhs = max_val * sum(model.V[ss, t] for (_, ss) in inputs)
                yield (None, lhs, rhs)
        
        m.blender_volume_property = pyo.Constraint(m.UBLD, m.Q, m.T, rule=blender_volume_property_rule)
        
        # 调合性质约束 - 质量基 (Eq. 22c in paper)
        def blender_mass_property_rule(model, u, q, t):
            if u not in model.UBLD or q not in model.Qw:
                return pyo.Constraint.Skip
            
            inputs = [(uu, ss) for (uu, ss) in model.IU if uu == u and (ss, q) in model.SQ]
            if not inputs:
                return pyo.Constraint.Skip
            
            min_val = model.FQBMin.get((u, q), -1e8)
            max_val = model.FQBMax.get((u, q), 1e8)
            
            if abs(min_val) < 1e7:
                lhs = min_val * sum(model.FVI[ss, t] for (_, ss) in inputs)
                rhs = sum(model.FVI[ss, t] * model.FQ[ss, q, t] for (_, ss) in inputs)
                yield (lhs, rhs, None)
            
            if abs(max_val) < 1e7:
                lhs = sum(model.FVI[ss, t] * model.FQ[ss, q, t] for (_, ss) in inputs)
                rhs = max_val * sum(model.FVI[ss, t] for (_, ss) in inputs)
                yield (None, lhs, rhs)
        
        m.blender_mass_property = pyo.Constraint(m.UBLD, m.Q, m.T, rule=blender_mass_property_rule)
        
    def _add_capacity_constraints(self):
        """容量约束"""
        m = self.model
        
        # 输入容量约束 (Eq. 24 in paper)
        def capacity_input_rule(model, c, t):
            if c not in model.CAPIN:
                return pyo.Constraint.Skip
            
            streams = [s for (cc, s) in model.CAPS if cc == c]
            if not streams:
                return pyo.Constraint.Skip
            
            min_val = model.FVCMin[c, t]
            max_val = model.FVCMax[c, t]
            
            total_flow = sum(model.FVI[s, t] for s in streams)
            
            return (min_val, total_flow, max_val)
        
        m.capacity_input = pyo.Constraint(m.CAPIN, m.T, rule=capacity_input_rule)
        
        # 输出容量约束 (Eq. 25 in paper)
        def capacity_output_rule(model, c, t):
            if c not in model.CAPOUT:
                return pyo.Constraint.Skip
            
            streams = [s for (cc, s) in model.CAPS if cc == c]
            if not streams:
                return pyo.Constraint.Skip
            
            min_val = model.FVCMin[c, t]
            max_val = model.FVCMax[c, t]
            
            total_flow = sum(model.FVO[s, t] for s in streams)
            
            return (min_val, total_flow, max_val)
        
        m.capacity_output = pyo.Constraint(m.CAPOUT, m.T, rule=capacity_output_rule)
        
    def _add_bound_constraints(self):
        """边界约束"""
        m = self.model
        
        # 性质边界约束 (Eq. 26-27 in paper)
        def property_bounds_rule(model, s, q, t):
            if (s, q) not in model.SQ:
                return pyo.Constraint.Skip
            if (s, q) in model.FIX:
                # 固定性质
                fixed_val = model.FQ0[s, q]
                if fixed_val is not None:
                    return model.FQ[s, q, t] == fixed_val
                return pyo.Constraint.Skip
            else:
                # 可变性质
                min_val = model.FQMin[s, q]
                max_val = model.FQMax[s, q]
                if abs(min_val) < 1e7 or abs(max_val) < 1e7:
                    return (min_val, model.FQ[s, q, t], max_val)
                return pyo.Constraint.Skip
        
        m.property_bounds = pyo.Constraint(m.SQ, m.T, rule=property_bounds_rule)
        
        # 原料流量边界 (Eq. 29 in paper)
        def material_flow_bounds_rule(model, s, t):
            if s not in model.S_M:
                return pyo.Constraint.Skip
            min_val = model.FVMin[s, t]
            max_val = model.FVMax[s, t]
            return (min_val, model.FVO[s, t], max_val)
        
        m.material_flow_bounds = pyo.Constraint(m.S_M, m.T, rule=material_flow_bounds_rule)
        
        # 产品流量边界 (Eq. 30 in paper)
        def product_flow_bounds_rule(model, s, t):
            if s not in model.S_P:
                return pyo.Constraint.Skip
            min_val = model.FVMin[s, t]
            max_val = model.FVMax[s, t]
            return (min_val, model.FVI[s, t], max_val)
        
        m.product_flow_bounds = pyo.Constraint(m.S_P, m.T, rule=product_flow_bounds_rule)
        
    def _add_inventory_constraints(self):
        """库存约束"""
        m = self.model
        
        # 检查是否有库存
        has_inventory = any(self.params.get('LMax', {}).values())
        if not has_inventory:
            return
        
        # 库存平衡 (Eq. 23 in paper)
        def inventory_balance_rule(model, s, t):
            return model.FVO[s, t] + model.FVLO[s, t] == model.FVI[s, t] + model.FVLI[s, t]
        
        m.inventory_balance = pyo.Constraint(m.S, m.T, rule=inventory_balance_rule)
        
        # 库存水平 (Eq. 24 in paper)
        def inventory_level_rule(model, s, t):
            if t == model.T.first():
                return model.L[s, t] == model.L0[s] + model.FVLI[s, t] - model.FVLO[s, t]
            else:
                t_prev = model.T.prev(t)
                return model.L[s, t] == model.L[s, t_prev] + model.FVLI[s, t] - model.FVLO[s, t]
        
        m.inventory_level = pyo.Constraint(m.S, m.T, rule=inventory_level_rule)
        
        # 库存边界
        def inventory_bounds_rule(model, s, t):
            min_val = model.LMin[s, t]
            max_val = model.LMax[s, t]
            return (min_val, model.L[s, t], max_val)
        
        m.inventory_bounds = pyo.Constraint(m.S, m.T, rule=inventory_bounds_rule)
        
        # 库存波动互斥约束 (Eq. 26-27 in paper)
        if hasattr(m, 'X'):
            def inventory_out_flag_rule(model, s, t):
                max_val = model.LMax[s, t]
                return model.FVLO[s, t] <= model.X[s, t] * max_val
            
            m.inventory_out_flag = pyo.Constraint(m.S, m.T, rule=inventory_out_flag_rule)
            
            def inventory_in_flag_rule(model, s, t):
                max_val = model.LMax[s, t]
                return model.FVLI[s, t] <= (1 - model.X[s, t]) * max_val
            
            m.inventory_in_flag = pyo.Constraint(m.S, m.T, rule=inventory_in_flag_rule)
        
    def _define_objective(self):
        """定义目标函数 (Eq. 31 in paper)"""
        m = self.model
        
        def objective_rule(model):
            # 产品销售收入
            product_revenue = sum(
                model.c_P[s] * model.FVI[s, t]
                for s in model.S_P for t in model.T
            )
            
            # 原料采购成本
            material_cost = sum(
                model.c_M[s] * model.FVO[s, t]
                for s in model.S_M for t in model.T
            )
            
            # 库存收益/成本
            inventory_profit = 0
            if any(self.params.get('LMax', {}).values()):
                # 产品库存收益
                inventory_profit += sum(
                    model.ci_P[s] * model.FVLI[s, t] - model.ci_M[s] * model.FVLO[s, t]
                    for s in model.S_P for t in model.T
                )
                # 原料库存成本
                inventory_profit -= sum(
                    model.ci_M[s] * model.FVLO[s, t] - model.ci_P[s] * model.FVLI[s, t]
                    for s in model.S_M for t in model.T
                )
            
            return product_revenue - material_cost + inventory_profit
        
        m.profit = pyo.Objective(rule=objective_rule, sense=pyo.maximize)
        
    def solve(self, solver_name='scip', time_limit=18000, options=None):
        """
        求解模型
        
        Args:
            solver_name: 求解器名称，默认为 'scip'
            time_limit: 时间限制（秒）
            options: 求解器选项字典
        
        Returns:
            求解结果
        """
        if self.model is None:
            raise ValueError("模型尚未构建，请先调用 build_model()")
        
        print(f"\n使用 {solver_name.upper()} 求解器求解模型...")
        print(f"时间限制: {time_limit} 秒")
        
        solver = SolverFactory(solver_name)
        
        # 设置求解器选项
        if options is None:
            options = {}
        
        # 设置时间限制
        if solver_name == 'scip':
            solver.options['limits/time'] = time_limit
            solver.options['limits/gap'] = 0.0001  # 0.01% 相对间隙
        elif solver_name == 'ipopt':
            solver.options['max_cpu_time'] = time_limit
        
        # 应用用户选项
        for key, value in options.items():
            solver.options[key] = value
        
        # 求解
        start_time = time.time()
        results = solver.solve(self.model, tee=True)
        solve_time = time.time() - start_time
        
        # 打印结果
        print(f"\n求解完成，耗时 {solve_time:.2f} 秒")
        print(f"求解器状态: {results.solver.status}")
        print(f"终止条件: {results.solver.termination_condition}")
        
        if results.solver.termination_condition == pyo.TerminationCondition.optimal or \
           results.solver.termination_condition == pyo.TerminationCondition.feasible:
            print(f"目标函数值: {pyo.value(self.model.profit):,.2f}")
        
        return results
    
    def print_summary(self):
        """打印模型统计信息"""
        if self.model is None:
            print("模型尚未构建")
            return
        
        m = self.model
        
        print("\n" + "="*60)
        print(f"模型统计信息: {self.case_folder}")
        print("="*60)
        
        # 统计变量数量
        n_vars = sum(1 for _ in m.component_data_objects(pyo.Var))
        n_binary = sum(1 for v in m.component_data_objects(pyo.Var) if v.is_binary())
        n_continuous = n_vars - n_binary
        
        print(f"变量总数: {n_vars}")
        print(f"  连续变量: {n_continuous}")
        print(f"  二元变量: {n_binary}")
        
        # 统计约束数量
        n_constraints = sum(1 for _ in m.component_data_objects(pyo.Constraint, active=True))
        print(f"约束总数: {n_constraints}")
        
        # 统计非线性项（近似）
        print(f"\n集合大小:")
        print(f"  时间周期 (T): {len(m.T)}")
        print(f"  流 (S): {len(m.S)}")
        print(f"  单元 (U): {len(m.U)}")
        print(f"  批次 (M): {len(m.M)}")
        print(f"  性质 (Q): {len(m.Q)}")
        print(f"  产品流 (S_P): {len(m.S_P)}")
        print(f"  原料流 (S_M): {len(m.S_M)}")
        
        print("="*60 + "\n")


def create_case_model(case_number: int):
    """
    创建指定案例的模型
    
    Args:
        case_number: 案例编号 (1, 2, 或 3)
    
    Returns:
        RefineryPlanningModel 实例
    """
    case_folder = f"case{case_number}"
    model = RefineryPlanningModel(case_folder)
    return model


if __name__ == '__main__':
    # 测试：构建 Case 1 模型
    print("测试 Case 1 模型构建...")
    model1 = create_case_model(1)
    model1.build_model()
    model1.print_summary()
