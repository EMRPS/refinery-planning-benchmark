"""
模型构建模块：主模型类和求解器接口

本模块提供炼厂规划模型的主类，负责协调各个模块进行模型构建和求解
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
    from model_sets_params_vars import define_sets, define_parameters, define_variables
    from model_constraints import define_all_constraints
    from model_objective import define_objective
else:
    from .data_reader import RefineryDataReader
    from .model_sets_params_vars import define_sets, define_parameters, define_variables
    from .model_constraints import define_all_constraints
    from .model_objective import define_objective


class RefineryPlanningModel:
    """
    炼厂规划 Pyomo 模型
    
    基于论文 "A production planning benchmark for real-world refinery-petrochemical complexes"
    实现了包含 CDU、工艺单元、混合器、分流器、调合器等的完整 MINLP 模型
    
    主要功能：
    1. 读取 Excel 数据文件
    2. 构建 Pyomo 优化模型
    3. 调用求解器求解
    4. 输出求解结果
    """
    
    def __init__(self, case_folder: str):
        """
        初始化模型
        
        Args:
            case_folder: 案例文件夹路径（如 'case1', 'case2', 'case3'）
                        会自动处理 data/ 前缀
        """
        self.case_folder = case_folder
        self.reader = RefineryDataReader(case_folder)
        self.sets, self.params = self.reader.read_all_data()
        self.model = None
        
    def build_model(self):
        """
        构建完整的 Pyomo 模型
        
        流程：
        1. 创建 ConcreteModel 实例
        2. 定义集合
        3. 定义参数
        4. 定义变量
        5. 定义约束
        6. 定义目标函数
        
        Returns:
            构建完成的 Pyomo 模型
        """
        print(f"正在构建 {self.case_folder} 的 Pyomo 模型...")
        start_time = time.time()
        
        # 创建模型实例
        self.model = pyo.ConcreteModel(name=f"RefineryPlanning_{self.case_folder}")
        
        # 定义集合
        print("  正在定义集合...")
        define_sets(self.model, self.sets)
        
        # 定义参数
        print("  正在定义参数...")
        define_parameters(self.model, self.params)
        
        # 定义变量
        print("  正在定义变量...")
        define_variables(self.model, self.params)
        
        # 定义约束
        define_all_constraints(self.model, self.params)
        
        # 定义目标函数
        print("  正在定义目标函数...")
        define_objective(self.model, self.params)
        
        build_time = time.time() - start_time
        print(f"模型构建完成，耗时 {build_time:.2f} 秒")
        
        return self.model
    
    def solve(self, solver_name='scip', time_limit=18000, options=None):
        """
        求解模型
        
        Args:
            solver_name: 求解器名称，默认为 'scip'
                        可选：'scip', 'ipopt', 'baron', 'antigone' 等
            time_limit: 时间限制（秒），默认 18000 秒（5 小时）
            options: 求解器选项字典，如 {'limits/gap': 0.01}
        
        Returns:
            求解结果对象
            
        求解器配置说明：
        - SCIP: 开源 MINLP 求解器，适用于所有案例
        - IPOPT: 开源 NLP 求解器，仅适用于 Case 1（无二元变量）
        - BARON/ANTIGONE: 商业全局优化求解器，可获得更优解
        """
        if self.model is None:
            raise ValueError("模型尚未构建，请先调用 build_model()")
        
        print(f"\n使用 {solver_name.upper()} 求解器求解模型...")
        print(f"时间限制: {time_limit} 秒")
        
        solver = SolverFactory(solver_name)
        
        # 设置求解器选项
        if options is None:
            options = {}
        
        # 设置时间限制（根据不同求解器）
        if solver_name == 'scip':
            solver.options['limits/time'] = time_limit
            solver.options['limits/gap'] = 0.0001  # 0.01% 相对间隙
        elif solver_name == 'ipopt':
            solver.options['max_cpu_time'] = time_limit
        elif solver_name in ['baron', 'antigone']:
            solver.options['MaxTime'] = time_limit
        
        # 应用用户自定义选项（会覆盖默认选项）
        for key, value in options.items():
            solver.options[key] = value
        
        # 求解模型
        start_time = time.time()
        results = solver.solve(self.model, tee=True)  # tee=True 显示求解过程
        solve_time = time.time() - start_time
        
        # 打印求解结果
        print(f"\n求解完成，耗时 {solve_time:.2f} 秒")
        print(f"求解器状态: {results.solver.status}")
        print(f"终止条件: {results.solver.termination_condition}")
        
        # 如果求解成功，打印目标函数值
        if results.solver.termination_condition == pyo.TerminationCondition.optimal or \
           results.solver.termination_condition == pyo.TerminationCondition.feasible:
            print(f"目标函数值（利润）: ${pyo.value(self.model.profit):,.2f}")
        
        return results
    
    def print_summary(self):
        """
        打印模型统计信息
        
        输出内容：
        - 变量总数（连续变量 + 二元变量）
        - 约束总数
        - 集合大小统计
        """
        if self.model is None:
            print("模型尚未构建")
            return
        
        m = self.model
        
        print("\n" + "="*60)
        print(f"模型统计信息: {self.case_folder}")
        print("="*60)
        
        # ========== 统计变量数量 ==========
        n_vars = sum(1 for _ in m.component_data_objects(pyo.Var))
        n_binary = sum(1 for v in m.component_data_objects(pyo.Var) if v.is_binary())
        n_continuous = n_vars - n_binary
        
        print(f"变量总数: {n_vars}")
        print(f"  连续变量: {n_continuous}")
        print(f"  二元变量: {n_binary}")
        
        # ========== 统计约束数量 ==========
        n_constraints = sum(1 for _ in m.component_data_objects(pyo.Constraint, active=True))
        print(f"约束总数: {n_constraints}")
        
        # ========== 统计集合大小 ==========
        print(f"\n集合大小:")
        print(f"  时间周期 (T): {len(m.T)}")
        print(f"  流 (S): {len(m.S)}")
        print(f"  单元 (U): {len(m.U)}")
        print(f"  批次 (M): {len(m.M)}")
        print(f"  性质 (Q): {len(m.Q)}")
        print(f"  产品流 (S_P): {len(m.S_P)}")
        print(f"  原料流 (S_M): {len(m.S_M)}")
        
        # ========== 单元类型统计 ==========
        print(f"\n单元类型:")
        print(f"  CDU 单元 (UCDU): {len(m.UCDU)}")
        print(f"  固定收率工艺单元 (UPF): {len(m.UPF)}")
        print(f"  Delta-base 工艺单元 (UPD): {len(m.UPD)}")
        print(f"  混合器 (UMIX): {len(m.UMIX)}")
        print(f"  分流器 (USPL): {len(m.USPL)}")
        print(f"  调合器 (UBLD): {len(m.UBLD)}")
        
        print("="*60 + "\n")


def create_case_model(case_number: int):
    """
    创建指定案例的模型（便捷函数）
    
    Args:
        case_number: 案例编号 (1, 2, 或 3)
    
    Returns:
        RefineryPlanningModel 实例
        
    示例：
        >>> model = create_case_model(1)
        >>> model.build_model()
        >>> results = model.solve()
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
