"""
模型定义模块：定义集合、参数和变量

本模块包含 Pyomo 模型的所有集合、参数和变量定义
"""
import pyomo.environ as pyo
from typing import Dict, Any


def define_sets(model, sets_data: Dict[str, Any]):
    """
    定义所有集合
    
    Args:
        model: Pyomo ConcreteModel 实例
        sets_data: 从数据读取器获取的集合数据字典
    """
    # ========== 基础集合 ==========
    model.T = pyo.Set(initialize=sets_data.get('T', ['1']))  # 时间周期集合
    model.S = pyo.Set(initialize=sets_data['S'])  # 所有流集合（包括产品流、原料流、中间流等）
    model.U = pyo.Set(initialize=sets_data['U'])  # 所有单元集合（包括 CDU、工艺单元、混合器、分流器、调合器等）
    model.M = pyo.Set(initialize=sets_data['M'])  # 所有批次集合（用于批次操作模式的单元）
    model.Q = pyo.Set(initialize=sets_data['Q'])  # 所有性质集合（如比重、硫含量、辛烷值等）
    model.C = pyo.Set(initialize=sets_data['C'])  # 容量索引集合（用于容量约束）
    
    # ========== 流的子集 ==========
    model.S_P = pyo.Set(initialize=sets_data.get('S_P', []))  # 产品流集合
    model.S_M = pyo.Set(initialize=sets_data.get('S_M', []))  # 原料流集合
    
    # ========== 单元的子集 ==========
    model.UCDU = pyo.Set(initialize=sets_data.get('UCDU', []))  # CDU（常减压蒸馏）单元集合
    model.UPF = pyo.Set(initialize=sets_data.get('UPF', []))  # 固定收率工艺单元集合（如催化重整、加氢裂化等）
    model.UPD = pyo.Set(initialize=sets_data.get('UPD', []))  # Delta-base 工艺单元集合（收率受进料性质影响）
    model.UMIX = pyo.Set(initialize=sets_data.get('UMIX', []))  # 混合器单元集合
    model.USPL = pyo.Set(initialize=sets_data.get('USPL', []))  # 分流器单元集合
    model.UBLD = pyo.Set(initialize=sets_data.get('UBLD', []))  # 调合器单元集合
    
    # ========== 性质的子集 ==========
    model.SPG = pyo.Set(initialize=sets_data.get('SPG', []))  # 比重性质集合（用于体积-质量转换）
    model.Qv = pyo.Set(initialize=sets_data.get('Qv', []))  # 体积基性质集合（混合按体积加权）
    model.Qw = pyo.Set(initialize=sets_data.get('Qw', []))  # 质量基性质集合（混合按质量加权）
    model.Qp = pyo.Set(initialize=sets_data.get('Qp', []))  # 组分比例性质集合
    
    # ========== 关系集合（二元、三元、多元） ==========
    model.IU = pyo.Set(initialize=sets_data.get('IU', []), dimen=2)  # (单元, 输入流) 对集合
    model.OU = pyo.Set(initialize=sets_data.get('OU', []), dimen=2)  # (单元, 输出流) 对集合
    model.IM = pyo.Set(initialize=sets_data.get('IM', []), dimen=3)  # (单元, 批次, 输入流) 三元组集合
    model.OM = pyo.Set(initialize=sets_data.get('OM', []), dimen=3)  # (单元, 批次, 输出流) 三元组集合
    model.SC = pyo.Set(initialize=sets_data.get('SC', []), dimen=None)  # Swing-cut 对集合（CDU 中侧线产品的灵活切割）
    model.SQ = pyo.Set(initialize=sets_data.get('SQ', []), dimen=2)  # (流, 性质) 对集合（流 s 具有性质 q）
    model.FIX = pyo.Set(initialize=sets_data.get('FIX', []), dimen=2)  # 固定性质集合（(流, 性质) 对，其性质值固定）
    model.QT = pyo.Set(initialize=sets_data.get('QT', []), dimen=3)  # 性质传递集合（(流1, 流2, 性质) 三元组）
    model.VMQ = pyo.Set(initialize=sets_data.get('VMQ', []), dimen=None)  # 虚拟批次性质集合
    model.DBSQ = pyo.Set(initialize=sets_data.get('DBSQ', []), dimen=None)  # Delta-base 流性质对集合
    model.CAPIN = pyo.Set(initialize=sets_data.get('CAPIN', []))  # 输入容量索引集合
    model.CAPOUT = pyo.Set(initialize=sets_data.get('CAPOUT', []))  # 输出容量索引集合
    model.CAPS = pyo.Set(initialize=sets_data.get('CAPS', []), dimen=2)  # 容量-流对集合
    model.CDUMQ = pyo.Set(initialize=sets_data.get('CDUMQ', []), dimen=None)  # CDU 批次性质约束集合
    model.CRU = pyo.Set(initialize=sets_data.get('CRU', []))  # 原油性质约束集合
    model.RB = pyo.Set(initialize=sets_data.get('RB', []))  # 比例调合单元集合


def define_parameters(model, params_data: Dict[str, Any]):
    """
    定义所有参数
    
    Args:
        model: Pyomo ConcreteModel 实例
        params_data: 从数据读取器获取的参数数据字典
    """
    # ========== 价格参数 ==========
    c_P = params_data.get('c_P', {})
    c_M = params_data.get('c_M', {})
    ci_P = params_data.get('ci_P', {})
    ci_M = params_data.get('ci_M', {})
    
    model.c_P = pyo.Param(model.S_P, initialize=c_P, default=0.0, mutable=True)  # 产品销售价格 ($/ton)
    model.c_M = pyo.Param(model.S_M, initialize=c_M, default=0.0, mutable=True)  # 原料采购价格 ($/ton)
    model.ci_P = pyo.Param(model.S_P, initialize=ci_P, default=0.0, mutable=True)  # 产品库存价格 ($/ton)
    model.ci_M = pyo.Param(model.S_M, initialize=ci_M, default=0.0, mutable=True)  # 原料库存价格 ($/ton)
    
    # ========== 流量边界参数 ==========
    FVMin_data = params_data.get('FVMin', {})
    FVMax_data = params_data.get('FVMax', {})
    
    def FVMin_init(model, s, t):
        return FVMin_data.get((s, t), 0.0)
    
    def FVMax_init(model, s, t):
        return FVMax_data.get((s, t), 1e8)  # 大数作为无界
    
    model.FVMin = pyo.Param(model.S, model.T, initialize=FVMin_init, default=0.0)  # 流量下界 (ton)
    model.FVMax = pyo.Param(model.S, model.T, initialize=FVMax_init, default=1e8)  # 流量上界 (ton)
    
    # ========== 性质参数 ==========
    FQ0_data = params_data.get('FQ0', {})
    FQMin_data = params_data.get('FQMin', {})
    FQMax_data = params_data.get('FQMax', {})
    
    def FQ0_init(model, s, q):
        return FQ0_data.get((s, q), None)
    
    def FQMin_init(model, s, q):
        return FQMin_data.get((s, q), -1e8)
    
    def FQMax_init(model, s, q):
        return FQMax_data.get((s, q), 1e8)
    
    model.FQ0 = pyo.Param(model.SQ, initialize=FQ0_init, default=None)  # 固定性质值（对于固定流的性质）
    model.FQMin = pyo.Param(model.SQ, initialize=FQMin_init, default=-1e8)  # 性质下界
    model.FQMax = pyo.Param(model.SQ, initialize=FQMax_init, default=1e8)  # 性质上界
    
    # ========== CDU 参数 ==========
    y_data = params_data.get('y', {})
    phi_data = params_data.get('phi', {})
    FQcut_data = params_data.get('FQcut', {})
    FQcrd_data = params_data.get('FQcrd', {})
    
    model.y = pyo.Param(model.U, model.M, model.S, model.S, initialize=y_data, default=0.0, mutable=True)  # CDU 收率系数 y(u,m,s_in,s_out)
    model.phi = pyo.Param(model.U, model.M, model.S, model.S, initialize=phi_data, default=0.0, mutable=True)  # CDU swing-cut 系数 φ(u,m,s_in,s_out)
    
    def FQcut_init(model, u, mm, s_in, s, q):
        return FQcut_data.get((u, mm, s_in, s, q), 1.0)
    model.FQcut = pyo.Param(model.U, model.M, model.S, model.S, model.Q, initialize=FQcut_init, default=1.0, mutable=True)  # CDU 侧线产品性质切割系数
    
    def FQcrd_init(model, u, mm, s, q):
        return FQcrd_data.get((u, mm, s, q), 1.0)
    model.FQcrd = pyo.Param(model.U, model.M, model.S, model.Q, initialize=FQcrd_init, default=1.0, mutable=True)  # CDU 原油性质
    
    # ========== 工艺单元参数 ==========
    gamma_data = params_data.get('gamma', {})
    B_data = params_data.get('B', {})
    delta_data = params_data.get('delta', {})
    Del_data = params_data.get('Del', {})
    alpha_data = params_data.get('alpha', {})
    w_data = params_data.get('w', {})
    
    def gamma_init(model, u, mm, s):
        return gamma_data.get((u, mm, s), 0.0)
    model.gamma = pyo.Param(model.U, model.M, model.S, initialize=gamma_init, default=0.0, mutable=True)  # 固定收率系数 γ(u,m,s)
    
    def B_init(model, u, mm, s, q):
        return B_data.get((u, mm, s, q), 0.0)
    model.B = pyo.Param(model.U, model.M, model.S, model.Q, initialize=B_init, default=0.0, mutable=True)  # Delta-base 基准性质值 B(u,m,s,q)
    
    def delta_init(model, u, mm, s, ss, qq):
        return delta_data.get((u, mm, s, ss, qq), 0.0)
    model.delta = pyo.Param(model.U, model.M, model.S, model.S, model.Q, initialize=delta_init, default=0.0, mutable=True)  # Delta-base 收率灵敏度系数 δ(u,m,s,s',q)
    
    def Del_init(model, u, mm, s, q):
        return Del_data.get((u, mm, s, q), 1.0)
    model.Del = pyo.Param(model.U, model.M, model.S, model.Q, initialize=Del_init, default=1.0, mutable=True)  # Delta-base 归一化系数 Δ(u,m,s,q)
    
    def alpha_init(model, s, s_out, q):
        return alpha_data.get((s, s_out, q), 1.0)
    model.alpha = pyo.Param(model.S, model.S, model.Q, initialize=alpha_init, default=1.0, mutable=True)  # 性质传递系数 α(s,s_out,q)
    
    def w_init(model, u, mm, s, q):
        return w_data.get((u, mm, s, q), 0.0)
    model.w = pyo.Param(model.U, model.M, model.S, model.Q, initialize=w_init, default=0.0, mutable=True)  # 虚拟批次性质权重 w(u,m,s,q)
    
    # ========== 容量参数 ==========
    FVCMin_data = params_data.get('FVCMin', {})
    FVCMax_data = params_data.get('FVCMax', {})
    
    def FVCMin_init(model, c, t):
        return FVCMin_data.get((c, t), 0.0)
    
    def FVCMax_init(model, c, t):
        return FVCMax_data.get((c, t), 1e8)
    
    model.FVCMin = pyo.Param(model.C, model.T, initialize=FVCMin_init, default=0.0)  # 容量下界 (ton)
    model.FVCMax = pyo.Param(model.C, model.T, initialize=FVCMax_init, default=1e8)  # 容量上界 (ton)
    
    # ========== 调合参数 ==========
    FQBMin_data = params_data.get('FQBMin', {})
    FQBMax_data = params_data.get('FQBMax', {})
    
    model.FQBMin = pyo.Param(model.UBLD, model.Q, initialize=FQBMin_data, default=-1e8, mutable=True)  # 调合产品性质下界
    model.FQBMax = pyo.Param(model.UBLD, model.Q, initialize=FQBMax_data, default=1e8, mutable=True)  # 调合产品性质上界
    
    # ========== 混合器性质约束参数 ==========
    FQVMin_data = params_data.get('FQVMin', {})
    FQVMax_data = params_data.get('FQVMax', {})
    
    model.FQVMin = pyo.Param(model.UMIX, model.M, model.Q, initialize=FQVMin_data, default=-1e8, mutable=True)  # 混合器输出性质下界
    model.FQVMax = pyo.Param(model.UMIX, model.M, model.Q, initialize=FQVMax_data, default=1e8, mutable=True)  # 混合器输出性质上界
    
    # ========== 库存参数 ==========
    LMin_data = params_data.get('LMin', {})
    LMax_data = params_data.get('LMax', {})
    L0_data = params_data.get('L0', {})
    
    def LMin_init(model, s, t):
        return LMin_data.get((s, t), 0.0)
    
    def LMax_init(model, s, t):
        return LMax_data.get((s, t), 0.0)  # 默认无库存
    
    model.LMin = pyo.Param(model.S, model.T, initialize=LMin_init, default=0.0)  # 库存下界 (ton)
    model.LMax = pyo.Param(model.S, model.T, initialize=LMax_init, default=0.0)  # 库存上界 (ton)
    model.L0 = pyo.Param(model.S, initialize=L0_data, default=0.0)  # 初始库存 (ton)
    
    # ========== 原油总性质约束参数 ==========
    MFQMin_data = params_data.get('MFQMin', {})
    MFQMax_data = params_data.get('MFQMax', {})
    
    model.MFQMin = pyo.Param(model.Q, initialize=MFQMin_data, default=-1e8, mutable=True)  # 原油混合总性质下界
    model.MFQMax = pyo.Param(model.Q, initialize=MFQMax_data, default=1e8, mutable=True)  # 原油混合总性质上界


def define_variables(model, params_data: Dict[str, Any]):
    """
    定义所有变量
    
    Args:
        model: Pyomo ConcreteModel 实例
        params_data: 参数数据字典（用于判断是否需要库存变量）
    """
    # ========== 流变量 ==========
    model.FVI = pyo.Var(model.S, model.T, domain=pyo.NonNegativeReals, bounds=(0, None))  # 流 s 在时间 t 的输入质量流量 (ton)
    model.FVO = pyo.Var(model.S, model.T, domain=pyo.NonNegativeReals, bounds=(0, None))  # 流 s 在时间 t 的输出质量流量 (ton)
    
    # ========== 批次流量变量 ==========
    # FVM(u, m, s, t) - 单元 u 的批次 m 中流 s 在时间 t 的质量流量
    def FVM_index_set(model):
        for t in model.T:
            for (u, mm, s) in model.IM:
                yield (u, mm, s, t)
            for (u, mm, s) in model.OM:
                yield (u, mm, s, t)
    model.FVM_index = pyo.Set(initialize=FVM_index_set, dimen=4)  # FVM 变量的索引集合
    model.FVM = pyo.Var(model.FVM_index, domain=pyo.NonNegativeReals, bounds=(0, None))  # 批次质量流量变量 (ton)
    
    # ========== 性质变量 ==========
    model.FQ = pyo.Var(model.SQ, model.T, domain=pyo.Reals, bounds=(None, None))  # 流 s 的性质 q 在时间 t 的值
    
    # ========== 体积流变量（用于调合和混合） ==========
    model.V = pyo.Var(model.S, model.T, domain=pyo.NonNegativeReals, bounds=(0, None))  # 流 s 在时间 t 的体积流量 (m³)
    
    # ========== 批次体积流量变量 ==========
    model.VM = pyo.Var(model.FVM_index, domain=pyo.NonNegativeReals, bounds=(0, None))  # 批次体积流量 VM(u,m,s,t) (m³)
    
    # ========== Delta-base 收率变量 ==========
    # Gamma(u, m, s, t) - 单元 u 批次 m 中流 s 在时间 t 的实际收率系数（受进料性质影响）
    def Gamma_index_set(model):
        for t in model.T:
            for (u, mm, s) in model.OM:
                yield (u, mm, s, t)
            for (u, mm, s) in model.IM:
                yield (u, mm, s, t)
    model.Gamma_index = pyo.Set(initialize=Gamma_index_set, dimen=4)  # Gamma 变量的索引集合
    model.Gamma = pyo.Var(model.Gamma_index, domain=pyo.Reals, bounds=(None, None))  # Delta-base 收率变量
    
    # ========== 库存变量 ==========
    model.L = pyo.Var(model.S, model.T, domain=pyo.NonNegativeReals, bounds=(0, None))  # 流 s 在时间 t 的库存量 (ton)
    model.FVLI = pyo.Var(model.S, model.T, domain=pyo.NonNegativeReals, bounds=(0, None))  # 流 s 在时间 t 的入库流量 (ton)
    model.FVLO = pyo.Var(model.S, model.T, domain=pyo.NonNegativeReals, bounds=(0, None))  # 流 s 在时间 t 的出库流量 (ton)
    
    # ========== 库存二元变量（仅对有库存的案例） ==========
    has_inventory = any(params_data.get('LMax', {}).values())
    if has_inventory:
        model.X = pyo.Var(model.S, model.T, domain=pyo.Binary)  # 库存操作二元变量（1=出库，0=入库）
