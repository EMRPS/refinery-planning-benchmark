"""
炼厂规划模型求解脚本

使用 SCIP 求解器求解三个案例的炼厂规划模型
"""
import sys
import os
import time
import argparse

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyomo_models.refinery_model import RefineryPlanningModel
import pyomo.environ as pyo


def solve_case(case_number, solver='scip', time_limit=18000, output_file=None):
    """
    求解指定案例
    
    Args:
        case_number: 案例编号 (1, 2, 或 3)
        solver: 求解器名称
        time_limit: 时间限制（秒）
        output_file: 输出文件路径
    """
    print("="*80)
    print(f"求解 Case {case_number}")
    print("="*80)
    
    case_folder = f"case{case_number}"
    
    # 创建模型
    model = RefineryPlanningModel(case_folder)
    
    # 构建模型
    try:
        model.build_model()
        model.print_summary()
    except Exception as e:
        print(f"错误：构建模型时出错: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # 求解模型
    try:
        results = model.solve(solver_name=solver, time_limit=time_limit)
        
        # 保存结果
        if output_file:
            with open(output_file, 'w') as f:
                f.write(f"Case {case_number} 求解结果\n")
                f.write("="*80 + "\n")
                f.write(f"求解器状态: {results.solver.status}\n")
                f.write(f"终止条件: {results.solver.termination_condition}\n")
                
                if results.solver.termination_condition == pyo.TerminationCondition.optimal or \
                   results.solver.termination_condition == pyo.TerminationCondition.feasible:
                    profit = pyo.value(model.model.profit)
                    f.write(f"目标函数值 (利润): {profit:,.2f}\n")
                    
                    # 写入一些关键变量
                    f.write("\n关键变量值：\n")
                    f.write("-"*80 + "\n")
                    
                    # 产品流量
                    f.write("\n产品流量 (前10个):\n")
                    count = 0
                    for s in model.model.S_P:
                        for t in model.model.T:
                            fvi_val = pyo.value(model.model.FVI[s, t])
                            if fvi_val > 0.01:
                                f.write(f"  FVI[{s},{t}] = {fvi_val:.4f}\n")
                                count += 1
                                if count >= 10:
                                    break
                        if count >= 10:
                            break
                    
                    # 原料流量
                    f.write("\n原料流量 (前10个):\n")
                    count = 0
                    for s in model.model.S_M:
                        for t in model.model.T:
                            fvo_val = pyo.value(model.model.FVO[s, t])
                            if fvo_val > 0.01:
                                f.write(f"  FVO[{s},{t}] = {fvo_val:.4f}\n")
                                count += 1
                                if count >= 10:
                                    break
                        if count >= 10:
                            break
                else:
                    f.write("未找到可行解\n")
            
            print(f"结果已保存到 {output_file}")
        
        return results
        
    except Exception as e:
        print(f"错误：求解模型时出错: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description='求解炼厂规划模型')
    parser.add_argument('case', type=int, choices=[1, 2, 3],
                        help='案例编号 (1, 2, 或 3)')
    parser.add_argument('--solver', type=str, default='scip',
                        help='求解器名称 (默认: scip)')
    parser.add_argument('--time-limit', type=int, default=18000,
                        help='时间限制（秒，默认: 18000）')
    parser.add_argument('--output', type=str, default=None,
                        help='输出文件路径')
    
    args = parser.parse_args()
    
    # 设置默认输出文件
    if args.output is None:
        args.output = f"case{args.case}_solution.txt"
    
    # 求解
    solve_case(args.case, solver=args.solver, 
               time_limit=args.time_limit, output_file=args.output)


if __name__ == '__main__':
    # 如果没有命令行参数，运行测试
    if len(sys.argv) == 1:
        print("测试模式：构建 Case 1 模型（不求解）")
        print("提示：使用命令行参数求解模型，例如：")
        print("  python solve_refinery.py 1 --solver scip --time-limit 3600")
        print()
        
        model = RefineryPlanningModel("case1")
        try:
            model.build_model()
            model.print_summary()
            print("\n模型构建成功！")
            print("注意：实际求解需要大量时间和计算资源。")
        except Exception as e:
            print(f"错误：{e}")
            import traceback
            traceback.print_exc()
    else:
        main()
