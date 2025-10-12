"""
约束定义模块：定义所有约束

本模块包含 Pyomo 模型的所有约束定义，按照功能分组
"""
import pyomo.environ as pyo
from typing import Dict, Any


def define_all_constraints(model, params_data: Dict[str, Any]):
    """
    定义所有约束
    
    Args:
        model: Pyomo ConcreteModel 实例
        params_data: 参数数据字典
    """
    print("  正在添加约束...")
    
    add_material_balance_constraints(model)
    add_cdu_constraints(model)
    add_process_unit_constraints(model)
    add_mixer_constraints(model)
    add_splitter_constraints(model)
    add_blender_constraints(model)
    add_capacity_constraints(model)
    add_bound_constraints(model)
    add_inventory_constraints(model, params_data)


def add_material_balance_constraints(model):
    """
    物料平衡约束
    """
    # ========== 批次求和约束 - 输入流 ==========
    def batch_sum_input_rule(model, u, s, t):
        r"""
        批次输入流求和约束
        
        LaTeX: $FVI_{s,t} = \sum_{m \in M: (u,m,s) \in IM} FVM_{u,m,s,t}$
        
        作用：将单元 u 的输入流 s 的总流量分解为各批次的流量之和
        r"""
        if (u, s) not in model.IU:
            return pyo.Constraint.Skip
        batches = [(uu, mm, ss) for (uu, mm, ss) in model.IM if uu == u and ss == s]
        if not batches:
            return model.FVI[s, t] == 0
        return model.FVI[s, t] == sum(model.FVM[uu, mm, ss, t] for (uu, mm, ss) in batches)
    
    model.batch_sum_input = pyo.Constraint(model.U, model.S, model.T, rule=batch_sum_input_rule)
    
    # ========== 批次求和约束 - 输出流 ==========
    def batch_sum_output_rule(model, u, s, t):
        r"""
        批次输出流求和约束
        
        LaTeX: $FVO_{s,t} = \sum_{m \in M: (u,m,s) \in OM} FVM_{u,m,s,t}$
        
        作用：将单元 u 的输出流 s 的总流量分解为各批次的流量之和
        r"""
        if (u, s) not in model.OU:
            return pyo.Constraint.Skip
        batches = [(uu, mm, ss) for (uu, mm, ss) in model.OM if uu == u and ss == s]
        if not batches:
            return model.FVO[s, t] == 0
        return model.FVO[s, t] == sum(model.FVM[uu, mm, ss, t] for (uu, mm, ss) in batches)
    
    model.batch_sum_output = pyo.Constraint(model.U, model.S, model.T, rule=batch_sum_output_rule)
    
    # ========== 混合器物料平衡 ==========
    def mixer_balance_rule(model, u, m_idx, t):
        r"""
        混合器批次物料平衡约束
        
        LaTeX: $\sum_{s \in S: (u,m,s) \in IM} FVM_{u,m,s,t} = \sum_{s \in S: (u,m,s) \in OM} FVM_{u,m,s,t}$
        
        作用：确保混合器每个批次的输入总流量等于输出总流量
        r"""
        if u not in model.UMIX:
            return pyo.Constraint.Skip
        inputs = [(uu, mm, ss) for (uu, mm, ss) in model.IM if uu == u and mm == m_idx]
        outputs = [(uu, mm, ss) for (uu, mm, ss) in model.OM if uu == u and mm == m_idx]
        if not inputs or not outputs:
            return pyo.Constraint.Skip
        return sum(model.FVM[i, t] for i in inputs) == sum(model.FVM[o, t] for o in outputs)
    
    model.mixer_balance = pyo.Constraint(model.UMIX, model.M, model.T, rule=mixer_balance_rule)
    
    # ========== 分流器和调合器物料平衡 ==========
    def splitter_blender_balance_rule(model, u, t):
        r"""
        分流器和调合器物料平衡约束
        
        LaTeX: $\sum_{s \in S: (u,s) \in IU} FVI_{s,t} = \sum_{s \in S: (u,s) \in OU} FVO_{s,t}$
        
        作用：确保分流器和调合器的输入总流量等于输出总流量
        r"""
        if u not in (model.USPL | model.UBLD):
            return pyo.Constraint.Skip
        inputs = [s for (uu, s) in model.IU if uu == u]
        outputs = [s for (uu, s) in model.OU if uu == u]
        if not inputs or not outputs:
            return pyo.Constraint.Skip
        return sum(model.FVI[s, t] for s in inputs) == sum(model.FVO[s, t] for s in outputs)
    
    model.splitter_blender_balance = pyo.Constraint(model.U, model.T, rule=splitter_blender_balance_rule)


def add_cdu_constraints(model):
    """
    CDU（常减压蒸馏）约束
    """
    # ========== CDU 产量约束（简化版本） ==========
    def cdu_yield_rule(model, u, m_idx, s, t):
        r"""
        CDU 收率约束（简化 swing-cut 模型）
        
        LaTeX: $FVM_{u,m,s_{out},t} = \sum_{s_{in} \in S: (u,m,s_{in}) \in IM} y_{u,m,s_{in},s_{out}} \cdot FVM_{u,m,s_{in},t}$
        
        作用：根据收率系数计算 CDU 各馏分的产量
        注意：本实现为简化版本，完整的 swing-cut 模型见论文 Eq. 6-10
        r"""
        if u not in model.UCDU or (u, m_idx, s) not in model.OM:
            return pyo.Constraint.Skip
        
        inputs = [(uu, mm, ss) for (uu, mm, ss) in model.IM if uu == u and mm == m_idx]
        if not inputs:
            return pyo.Constraint.Skip
        
        # 基本收率计算（简化，忽略 swing-cut）
        return model.FVM[u, m_idx, s, t] == sum(
            model.y[u, m_idx, s_in, s] * model.FVM[u, m_idx, s_in, t]
            for (_, _, s_in) in inputs
        )
    
    model.cdu_yield = pyo.Constraint(model.UCDU, model.M, model.S, model.T, rule=cdu_yield_rule)


def add_process_unit_constraints(model):
    """
    工艺单元约束（固定收率和 Delta-base 收率）
    """
    # ========== 固定收率工艺单元 ==========
    def fixed_yield_rule(model, u, m_idx, s, t):
        r"""
        固定收率工艺单元约束
        
        LaTeX: $FVM_{u,m,s,t} \cdot \sum_{s' \in S} \gamma_{u,m,s'} = \gamma_{u,m,s} \cdot \sum_{s_{in} \in S: (u,m,s_{in}) \in IM} FVM_{u,m,s_{in},t}$
        
        作用：根据固定收率系数 γ 计算工艺单元的产量分配
        适用单元：催化重整、加氢裂化、加氢精制等固定操作条件的工艺单元
        r"""
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
    
    model.fixed_yield = pyo.Constraint(model.UPF, model.M, model.S, model.T, rule=fixed_yield_rule)
    
    # ========== Delta-base 收率计算 ==========
    def delta_base_gamma_rule(model, u, m_idx, s, t):
        r"""
        Delta-base 收率系数计算约束
        
        LaTeX: $\Gamma_{u,m,s,t} = \gamma_{u,m,s} + \sum_{(u,m,s',q) \in DBSQ} \frac{\delta_{u,m,s,s',q}}{\Delta_{u,m,s',q}} \cdot (FQ_{s',q,t} - B_{u,m,s',q})$
        
        作用：根据进料性质偏差计算实际收率系数 Γ
        适用单元：催化裂化（FCC）等收率受进料性质显著影响的工艺单元
        r"""
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
    
    model.delta_base_gamma = pyo.Constraint(model.UPD, model.M, model.S, model.T, rule=delta_base_gamma_rule)
    
    # ========== Delta-base 产量约束 ==========
    def delta_base_yield_rule(model, u, m_idx, s, t):
        r"""
        Delta-base 产量约束
        
        LaTeX: $FVM_{u,m,s,t} \cdot \sum_{s' \in S} \Gamma_{u,m,s',t} = \Gamma_{u,m,s,t} \cdot \sum_{s_{in} \in S: (u,m,s_{in}) \in IM} FVM_{u,m,s_{in},t}$
        
        作用：根据实际收率系数 Γ 计算工艺单元的产量分配
        r"""
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
    
    model.delta_base_yield = pyo.Constraint(model.UPD, model.M, model.S, model.T, rule=delta_base_yield_rule)
    
    # ========== 性质传递 ==========
    def property_transfer_rule(model, s, s_out, q, t):
        r"""
        性质传递约束
        
        LaTeX: $FQ_{s_{out},q,t} = \alpha_{s,s_{out},q} \cdot FQ_{s,q,t}$
        
        作用：通过传递系数 α 将一个流的性质传递给另一个流
        r"""
        if (s, s_out, q) not in model.QT:
            return pyo.Constraint.Skip
        if (s, q) in model.FIX or (s_out, q) in model.FIX:
            return pyo.Constraint.Skip
        if (s, q) not in model.SQ or (s_out, q) not in model.SQ:
            return pyo.Constraint.Skip
        
        alpha_val = model.alpha[s, s_out, q]
        return model.FQ[s_out, q, t] == alpha_val * model.FQ[s, q, t]
    
    model.property_transfer = pyo.Constraint(model.S, model.S, model.Q, model.T, rule=property_transfer_rule)


def add_mixer_constraints(model):
    """
    混合器约束
    """
    # ========== 体积-质量关系（通过比重） ==========
    def mixer_volume_mass_rule(model, u, m_idx, s, t):
        r"""
        混合器体积-质量转换约束
        
        LaTeX: $VM_{u,m,s,t} \cdot FQ_{s,q_{spg},t} = FVM_{u,m,s,t}$
        
        作用：通过比重性质将体积流量转换为质量流量
        r"""
        if u not in model.UMIX or (u, m_idx, s) not in (model.IM | model.OM):
            return pyo.Constraint.Skip
        
        # 查找比重性质
        spg_props = [q for q in model.SPG if (s, q) in model.SQ]
        if not spg_props:
            return pyo.Constraint.Skip
        
        q_spg = spg_props[0]  # 使用第一个比重性质
        
        # VM * FQ = FVM （体积 * 密度 = 质量）
        return model.VM[u, m_idx, s, t] * model.FQ[s, q_spg, t] == model.FVM[u, m_idx, s, t]
    
    model.mixer_volume_mass = pyo.Constraint(model.UMIX, model.M, model.S, model.T, rule=mixer_volume_mass_rule)
    
    # ========== 混合器体积平衡 ==========
    def mixer_volume_balance_rule(model, u, m_idx, s, t):
        r"""
        混合器体积守恒约束
        
        LaTeX: $VM_{u,m,s_{out},t} = \sum_{s_{in} \in S: (u,m,s_{in}) \in IM} VM_{u,m,s_{in},t}$
        
        作用：确保混合器的输出体积流量等于输入体积流量之和
        r"""
        if u not in model.UMIX or (u, m_idx, s) not in model.OM:
            return pyo.Constraint.Skip
        
        inputs = [(uu, mm, ss) for (uu, mm, ss) in model.IM if uu == u and mm == m_idx]
        if not inputs:
            return pyo.Constraint.Skip
        
        return model.VM[u, m_idx, s, t] == sum(
            model.VM[uu, mm, ss, t] for (uu, mm, ss) in inputs
        )
    
    model.mixer_volume_balance = pyo.Constraint(model.UMIX, model.M, model.S, model.T, rule=mixer_volume_balance_rule)
    
    # ========== 混合器体积基性质混合 ==========
    def mixer_volume_property_rule(model, u, m_idx, s, q, t):
        r"""
        混合器体积基性质混合约束
        
        LaTeX: $VM_{u,m,s_{out},t} \cdot FQ_{s_{out},q,t} = \sum_{s_{in} \in S: (u,m,s_{in}) \in IM} VM_{u,m,s_{in},t} \cdot FQ_{s_{in},q,t}$
        
        作用：计算混合后流的体积基性质值（如辛烷值）
        r"""
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
    
    model.mixer_volume_property = pyo.Constraint(model.UMIX, model.M, model.S, model.Q, model.T, rule=mixer_volume_property_rule)
    
    # ========== 混合器质量基性质混合 ==========
    def mixer_mass_property_rule(model, u, m_idx, s, q, t):
        r"""
        混合器质量基性质混合约束
        
        LaTeX: $FVM_{u,m,s_{out},t} \cdot FQ_{s_{out},q,t} = \sum_{s_{in} \in S: (u,m,s_{in}) \in IM} FVM_{u,m,s_{in},t} \cdot FQ_{s_{in},q,t}$
        
        作用：计算混合后流的质量基性质值（如硫含量）
        r"""
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
    
    model.mixer_mass_property = pyo.Constraint(model.UMIX, model.M, model.S, model.Q, model.T, rule=mixer_mass_property_rule)


def add_splitter_constraints(model):
    """
    分流器约束
    """
    # ========== 分流器性质传递 ==========
    def splitter_property_rule(model, u, s_in, s_out, q, t):
        r"""
        分流器性质传递约束
        
        LaTeX: $FQ_{s_{out},q,t} = FQ_{s_{in},q,t}$
        
        作用：确保分流器所有输出流的性质与输入流相同
        r"""
        if u not in model.USPL:
            return pyo.Constraint.Skip
        if (u, s_in) not in model.IU or (u, s_out) not in model.OU:
            return pyo.Constraint.Skip
        if (s_in, q) not in model.SQ or (s_out, q) not in model.SQ:
            return pyo.Constraint.Skip
        
        return model.FQ[s_out, q, t] == model.FQ[s_in, q, t]
    
    model.splitter_property = pyo.Constraint(model.USPL, model.S, model.S, model.Q, model.T, rule=splitter_property_rule)


def add_blender_constraints(model):
    """
    调合器约束
    """
    # ========== 体积-质量关系 ==========
    def blender_volume_mass_rule(model, u, s, t):
        r"""
        调合器体积-质量转换约束
        
        LaTeX: $V_{s,t} \cdot FQ_{s,q_{spg},t} = FVI_{s,t}$
        
        作用：通过比重性质将体积流量转换为质量流量
        r"""
        if u not in model.UBLD or (u, s) not in model.IU:
            return pyo.Constraint.Skip
        
        # 查找比重性质
        spg_props = [q for q in model.SPG if (s, q) in model.SQ]
        if not spg_props:
            return pyo.Constraint.Skip
        
        q_spg = spg_props[0]
        return model.V[s, t] * model.FQ[s, q_spg, t] == model.FVI[s, t]
    
    model.blender_volume_mass = pyo.Constraint(model.UBLD, model.S, model.T, rule=blender_volume_mass_rule)
    
    # ========== 调合性质约束 - 比重 ==========
    def blender_spg_rule(model, u, q, t):
        r"""
        调合器比重性质约束
        
        LaTeX: $FQBMin_{u,q} \cdot \sum_{s \in S: (u,s) \in IU} V_{s,t} \leq \sum_{s \in S: (u,s) \in IU} FVI_{s,t} \leq FQBMax_{u,q} \cdot \sum_{s \in S: (u,s) \in IU} V_{s,t}$
        
        作用：确保调合产品的比重在规定范围内
        r"""
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
    
    model.blender_spg = pyo.Constraint(model.UBLD, model.Q, model.T, rule=blender_spg_rule)
    
    # ========== 调合性质约束 - 体积基 ==========
    def blender_volume_property_rule(model, u, q, t):
        r"""
        调合器体积基性质约束
        
        LaTeX: $FQBMin_{u,q} \cdot \sum_{s \in S: (u,s) \in IU} V_{s,t} \leq \sum_{s \in S: (u,s) \in IU} V_{s,t} \cdot FQ_{s,q,t} \leq FQBMax_{u,q} \cdot \sum_{s \in S: (u,s) \in IU} V_{s,t}$
        
        作用：确保调合产品的体积基性质（如辛烷值）在规定范围内
        r"""
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
    
    model.blender_volume_property = pyo.Constraint(model.UBLD, model.Q, model.T, rule=blender_volume_property_rule)
    
    # ========== 调合性质约束 - 质量基 ==========
    def blender_mass_property_rule(model, u, q, t):
        r"""
        调合器质量基性质约束
        
        LaTeX: $FQBMin_{u,q} \cdot \sum_{s \in S: (u,s) \in IU} FVI_{s,t} \leq \sum_{s \in S: (u,s) \in IU} FVI_{s,t} \cdot FQ_{s,q,t} \leq FQBMax_{u,q} \cdot \sum_{s \in S: (u,s) \in IU} FVI_{s,t}$
        
        作用：确保调合产品的质量基性质（如硫含量）在规定范围内
        r"""
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
    
    model.blender_mass_property = pyo.Constraint(model.UBLD, model.Q, model.T, rule=blender_mass_property_rule)


def add_capacity_constraints(model):
    """
    容量约束
    """
    # ========== 输入容量约束 ==========
    def capacity_input_rule(model, c, t):
        r"""
        输入容量约束
        
        LaTeX: $FVCMin_{c,t} \leq \sum_{s \in S: (c,s) \in CAPS} FVI_{s,t} \leq FVCMax_{c,t}$
        
        作用：限制装置的总输入流量在容量范围内
        r"""
        if c not in model.CAPIN:
            return pyo.Constraint.Skip
        
        streams = [s for (cc, s) in model.CAPS if cc == c]
        if not streams:
            return pyo.Constraint.Skip
        
        min_val = model.FVCMin[c, t]
        max_val = model.FVCMax[c, t]
        
        total_flow = sum(model.FVI[s, t] for s in streams)
        
        return (min_val, total_flow, max_val)
    
    model.capacity_input = pyo.Constraint(model.CAPIN, model.T, rule=capacity_input_rule)
    
    # ========== 输出容量约束 ==========
    def capacity_output_rule(model, c, t):
        r"""
        输出容量约束
        
        LaTeX: $FVCMin_{c,t} \leq \sum_{s \in S: (c,s) \in CAPS} FVO_{s,t} \leq FVCMax_{c,t}$
        
        作用：限制装置的总输出流量在容量范围内
        r"""
        if c not in model.CAPOUT:
            return pyo.Constraint.Skip
        
        streams = [s for (cc, s) in model.CAPS if cc == c]
        if not streams:
            return pyo.Constraint.Skip
        
        min_val = model.FVCMin[c, t]
        max_val = model.FVCMax[c, t]
        
        total_flow = sum(model.FVO[s, t] for s in streams)
        
        return (min_val, total_flow, max_val)
    
    model.capacity_output = pyo.Constraint(model.CAPOUT, model.T, rule=capacity_output_rule)


def add_bound_constraints(model):
    """
    边界约束
    """
    # ========== 性质边界约束 ==========
    def property_bounds_rule(model, s, q, t):
        r"""
        性质边界约束
        
        LaTeX: 
        - 固定性质: $FQ_{s,q,t} = FQ0_{s,q}$
        - 可变性质: $FQMin_{s,q} \leq FQ_{s,q,t} \leq FQMax_{s,q}$
        
        作用：限制流的性质值在允许范围内，或固定特定流的性质值
        r"""
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
    
    model.property_bounds = pyo.Constraint(model.SQ, model.T, rule=property_bounds_rule)
    
    # ========== 原料流量边界 ==========
    def material_flow_bounds_rule(model, s, t):
        r"""
        原料流量边界约束
        
        LaTeX: $FVMin_{s,t} \leq FVO_{s,t} \leq FVMax_{s,t}$
        
        作用：限制原料的采购量在供应范围内
        r"""
        if s not in model.S_M:
            return pyo.Constraint.Skip
        min_val = model.FVMin[s, t]
        max_val = model.FVMax[s, t]
        return (min_val, model.FVO[s, t], max_val)
    
    model.material_flow_bounds = pyo.Constraint(model.S_M, model.T, rule=material_flow_bounds_rule)
    
    # ========== 产品流量边界 ==========
    def product_flow_bounds_rule(model, s, t):
        r"""
        产品流量边界约束
        
        LaTeX: $FVMin_{s,t} \leq FVI_{s,t} \leq FVMax_{s,t}$
        
        作用：限制产品的生产量在需求范围内
        r"""
        if s not in model.S_P:
            return pyo.Constraint.Skip
        min_val = model.FVMin[s, t]
        max_val = model.FVMax[s, t]
        return (min_val, model.FVI[s, t], max_val)
    
    model.product_flow_bounds = pyo.Constraint(model.S_P, model.T, rule=product_flow_bounds_rule)


def add_inventory_constraints(model, params_data: Dict[str, Any]):
    """
    库存约束（仅对 Case 2 和 Case 3）
    """
    # 检查是否有库存
    has_inventory = any(params_data.get('LMax', {}).values())
    if not has_inventory:
        return
    
    # ========== 库存平衡 ==========
    def inventory_balance_rule(model, s, t):
        r"""
        库存物料平衡约束
        
        LaTeX: $FVO_{s,t} + FVLO_{s,t} = FVI_{s,t} + FVLI_{s,t}$
        
        作用：确保炼厂输出流量加上出库流量等于炼厂输入流量加上入库流量
        r"""
        return model.FVO[s, t] + model.FVLO[s, t] == model.FVI[s, t] + model.FVLI[s, t]
    
    model.inventory_balance = pyo.Constraint(model.S, model.T, rule=inventory_balance_rule)
    
    # ========== 库存水平 ==========
    def inventory_level_rule(model, s, t):
        r"""
        库存水平计算约束
        
        LaTeX: 
        - $t=1$: $L_{s,t} = L0_{s} + FVLI_{s,t} - FVLO_{s,t}$
        - $t>1$: $L_{s,t} = L_{s,t-1} + FVLI_{s,t} - FVLO_{s,t}$
        
        作用：根据初始库存和出入库流量计算每个时间周期的库存水平
        r"""
        if t == model.T.first():
            return model.L[s, t] == model.L0[s] + model.FVLI[s, t] - model.FVLO[s, t]
        else:
            t_prev = model.T.prev(t)
            return model.L[s, t] == model.L[s, t_prev] + model.FVLI[s, t] - model.FVLO[s, t]
    
    model.inventory_level = pyo.Constraint(model.S, model.T, rule=inventory_level_rule)
    
    # ========== 库存边界 ==========
    def inventory_bounds_rule(model, s, t):
        r"""
        库存容量边界约束
        
        LaTeX: $LMin_{s,t} \leq L_{s,t} \leq LMax_{s,t}$
        
        作用：限制库存量在库容范围内
        r"""
        min_val = model.LMin[s, t]
        max_val = model.LMax[s, t]
        return (min_val, model.L[s, t], max_val)
    
    model.inventory_bounds = pyo.Constraint(model.S, model.T, rule=inventory_bounds_rule)
    
    # ========== 库存波动互斥约束 ==========
    if hasattr(model, 'X'):
        def inventory_out_flag_rule(model, s, t):
            r"""
            出库标志约束
            
            LaTeX: $FVLO_{s,t} \leq X_{s,t} \cdot LMax_{s,t}$
            
            作用：当 X=1 时允许出库，X=0 时禁止出库（用于避免同时入库和出库）
            r"""
            max_val = model.LMax[s, t]
            return model.FVLO[s, t] <= model.X[s, t] * max_val
        
        model.inventory_out_flag = pyo.Constraint(model.S, model.T, rule=inventory_out_flag_rule)
        
        def inventory_in_flag_rule(model, s, t):
            r"""
            入库标志约束
            
            LaTeX: $FVLI_{s,t} \leq (1 - X_{s,t}) \cdot LMax_{s,t}$
            
            作用：当 X=0 时允许入库，X=1 时禁止入库（用于避免同时入库和出库）
            r"""
            max_val = model.LMax[s, t]
            return model.FVLI[s, t] <= (1 - model.X[s, t]) * max_val
        
        model.inventory_in_flag = pyo.Constraint(model.S, model.T, rule=inventory_in_flag_rule)
