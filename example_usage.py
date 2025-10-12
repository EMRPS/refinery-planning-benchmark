"""
示例：如何使用 Pyomo 模型
"""
import sys
sys.path.insert(0, '.')

from pyomo_models.refinery_model import RefineryPlanningModel
import pyomo.environ as pyo


def example_build_model():
    """示例：构建模型"""
    print("示例 1: 构建 Case 1 模型")
    print("="*60)
    
    model = RefineryPlanningModel('case1')
    model.build_model()
    model.print_summary()


def example_solve_with_scip():
    """示例：使用 SCIP 求解器"""
    print("\n示例 2: 使用 SCIP 求解 Case 1（演示，不实际求解）")
    print("="*60)
    
    model = RefineryPlanningModel('case1')
    model.build_model()
    
    print("\n提示：实际求解需要大量时间。")
    print("要求解模型，请取消下面代码的注释：")
    print()
    print("# results = model.solve(solver_name='scip', time_limit=3600)")
    print("# if results.solver.termination_condition == pyo.TerminationCondition.optimal:")
    print("#     print(f'最优利润: {pyo.value(model.model.profit):,.2f}')")


def example_access_data():
    """示例：访问数据"""
    print("\n示例 3: 访问数据")
    print("="*60)
    
    model = RefineryPlanningModel('case1')
    sets, params = model.reader.read_all_data()
    
    print(f"产品流: {len(sets['S_P'])} 个")
    print(f"原料流: {len(sets['S_M'])} 个")
    
    print("\n前 5 个产品及其价格:")
    c_P = params['c_P']
    for i, (s, price) in enumerate(list(c_P.items())[:5]):
        print(f"  {s}: {price:,.0f}")
    
    print("\n前 5 个原料及其成本:")
    c_M = params['c_M']
    for i, (s, cost) in enumerate(list(c_M.items())[:5]):
        print(f"  {s}: {cost:,.0f}")


if __name__ == '__main__':
    example_build_model()
    example_solve_with_scip()
    example_access_data()
    
    print("\n" + "="*60)
    print("示例完成！")
    print("="*60)
    print("\n提示：")
    print("1. 使用 'python solve_refinery.py 1' 求解 Case 1")
    print("2. 使用 'python solve_refinery.py 2' 求解 Case 2")
    print("3. 使用 'python solve_refinery.py 3' 求解 Case 3")
    print("4. 添加 '--help' 查看完整选项")
