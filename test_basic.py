"""
快速测试脚本：验证数据读取和基本模型结构
"""
import sys
sys.path.insert(0, '.')

from pyomo_models.data_reader import RefineryDataReader
import pyomo.environ as pyo

def test_data_reading():
    """测试数据读取"""
    print("="*80)
    print("测试数据读取")
    print("="*80)
    
    for case_num in [1, 2, 3]:
        print(f"\nCase {case_num}:")
        reader = RefineryDataReader(f'case{case_num}')
        sets, params = reader.read_all_data()
        
        print(f"  集合数量: {len(sets)}")
        print(f"  参数数量: {len(params)}")
        print(f"  流 (S): {len(sets['S'])}")
        print(f"  单元 (U): {len(sets['U'])}")
        print(f"  时间周期 (T): {len(sets['T'])}")
        print(f"  产品 (S_P): {len(sets['S_P'])}")
        print(f"  原料 (S_M): {len(sets['S_M'])}")

def test_basic_model():
    """测试基本模型结构"""
    print("\n" + "="*80)
    print("测试基本 Pyomo 模型结构（Case 1）")
    print("="*80)
    
    reader = RefineryDataReader('case1')
    sets, params = reader.read_all_data()
    
    # 创建简单模型测试集合
    m = pyo.ConcreteModel()
    m.T = pyo.Set(initialize=sets['T'])
    m.S = pyo.Set(initialize=sets['S'])
    m.U = pyo.Set(initialize=sets['U'])
    m.S_P = pyo.Set(initialize=sets['S_P'])
    m.S_M = pyo.Set(initialize=sets['S_M'])
    
    print(f"  模型名称: {m.name}")
    print(f"  集合 T 大小: {len(m.T)}")
    print(f"  集合 S 大小: {len(m.S)}")
    print(f"  集合 U 大小: {len(m.U)}")
    
    # 测试变量定义
    m.FVI = pyo.Var(m.S, m.T, domain=pyo.NonNegativeReals)
    m.FVO = pyo.Var(m.S, m.T, domain=pyo.NonNegativeReals)
    
    print(f"  变量 FVI 数量: {len(m.FVI)}")
    print(f"  变量 FVO 数量: {len(m.FVO)}")
    
    # 测试参数
    c_P_data = params.get('c_P', {})
    m.c_P = pyo.Param(m.S_P, initialize=c_P_data, default=0.0)
    print(f"  参数 c_P 非零值数量: {sum(1 for v in m.c_P.values() if v != 0)}")
    
    # 测试简单约束
    def simple_bound_rule(model, s, t):
        if s in model.S_P:
            return model.FVI[s, t] >= 0
        return pyo.Constraint.Skip
    
    m.simple_bound = pyo.Constraint(m.S, m.T, rule=simple_bound_rule)
    
    active_constraints = sum(1 for c in m.simple_bound.values() if c.active)
    print(f"  活跃约束数量: {active_constraints}")
    
    print("\n基本模型结构测试成功！")

if __name__ == '__main__':
    test_data_reading()
    test_basic_model()
    print("\n" + "="*80)
    print("所有测试通过！")
    print("="*80)
