# 炼厂规划 Pyomo 模型

这个目录包含使用 Pyomo 重新实现的炼厂规划基准模型，基于论文 "A production planning benchmark for real-world refinery-petrochemical complexes"。

## 模型说明

模型实现了完整的炼厂-石化综合体生产规划问题，包括：

- **Case 1**: 单周期炼厂规划（NLP问题）
  - 2个CDU，25个二次加工单元，24种产品
  - 3573个变量，3428个约束
  - 无库存管理，无二元变量

- **Case 2**: 单周期炼化一体化规划（MINLP问题）
  - 3个CDU，51个二次加工单元，44种产品
  - 7157个变量（56个二元变量），8156个约束
  - 包含库存管理

- **Case 3**: 三周期炼化一体化规划（MINLP问题）
  - 3个CDU，51个二次加工单元，44种产品，3个时间周期
  - 21469个变量（168个二元变量），24466个约束
  - 包含库存管理

## 模块化结构

Pyomo 模型采用模块化设计，便于理解和维护：

```
pyomo_models/
├── data_reader.py              # 数据读取模块：从 Excel 文件读取集合和参数
├── model_sets_params_vars.py   # 集合、参数和变量定义（含中文注释）
├── model_constraints.py        # 约束定义（含 LaTeX 公式和作用说明）
├── model_objective.py          # 目标函数定义
├── model_builder.py            # 主模型构建器和求解器接口
└── __init__.py                 # 包初始化文件
```

**特点**：

- 所有集合、参数、变量都有详细的中文注释说明其含义和单位
- 所有约束都包含 LaTeX 数学公式和作用说明
- 代码结构清晰，便于学习和二次开发

## 安装依赖

```bash
pip install pyomo pandas openpyxl pyscipopt
```

## 使用方法

### 1. 构建模型（不求解）

```python
from pyomo_models import create_case_model

# 创建 Case 1 模型（便捷方式）
model = create_case_model(1)
model.build_model()
model.print_summary()
```

或者使用完整类名：

```python
from pyomo_models import RefineryPlanningModel

# 创建模型
model = RefineryPlanningModel('case1')  # 或 'data/case1'
model.build_model()
model.print_summary()
```

### 2. 使用命令行求解

```bash
# 求解 Case 1，时间限制 1 小时
python solve_refinery.py 1 --solver scip --time-limit 3600 --output case1_result.txt

# 求解 Case 2，时间限制 5 小时
python solve_refinery.py 2 --solver scip --time-limit 18000 --output case2_result.txt

# 求解 Case 3，时间限制 5 小时
python solve_refinery.py 3 --solver scip --time-limit 18000 --output case3_result.txt
```

### 3. 在 Python 脚本中求解

```python
from pyomo_models import create_case_model
import pyomo.environ as pyo

# 创建并构建模型
model = create_case_model(1)
model.build_model()

# 使用 SCIP 求解器求解
results = model.solve(solver_name='scip', time_limit=3600)

# 查看结果
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    print(f"最优利润: ${pyo.value(model.model.profit):,.2f}")
```

```

## 模型特点

### 数学模型

模型实现了论文中描述的完整 MINLP 公式，包括：

1. **物料平衡约束** (Eqs. 2-5)
   - 批次物料平衡
   - 混合器、分流器、调合器物料平衡

2. **CDU 约束** (Eqs. 6-10)
   - Swing-cut 模型（简化版）
   - 原油性质约束
   - 产品收率计算

3. **工艺单元约束** (Eqs. 11-14)
   - 固定收率模型
   - Delta-base 模型（考虑进料性质对收率的影响）
   - 性质传递

4. **混合器约束** (Eqs. 15-19)
   - 体积-质量关系（通过比重）
   - 体积基性质混合
   - 质量基性质混合
   - 虚拟批次性质约束

5. **分流器约束** (Eq. 20)
   - 性质保持

6. **调合器约束** (Eqs. 21-23)
   - 产品规格约束
   - 比例调合

7. **容量约束** (Eqs. 24-25)
   - 装置输入容量
   - 装置输出容量

8. **边界约束** (Eqs. 26-30)
   - 性质边界
   - 流量边界
   - 库存边界

9. **库存管理** (Case 2/3)
   - 库存平衡
   - 库存水平
   - 库存波动互斥约束（二元变量）

10. **目标函数** (Eq. 31)
    - 最大化总利润
    - 包括产品销售收入、原料成本、库存收益/成本

### 非线性项

模型包含以下非线性项：

- 双线性项：流量×性质（调合、混合）
- 双线性项：收率×流量（Delta-base 模型）
- 混合逻辑：库存波动二元变量（Case 2/3）

## 数据文件

模型从以下文件读取数据：

- `case*/all_sets_export.xlsx`: 集合定义
- `case*/all_parameters_export.xlsx`: 参数值
- `case*/all_sets.txt`: 集合描述（可选，用于理解）
- `case*/all_parameters.txt`: 参数描述（可选，用于理解）

## 求解器

推荐使用 SCIP 求解器（开源全局优化求解器）：

- SCIP 8.0 或更高版本
- 通过 pyscipopt 接口调用

其他支持的求解器：

- IPOPT（局部优化，适用于 NLP 问题如 Case 1）
- BARON（商业全局优化求解器）
- Gurobi（需要处理非线性约束）

## 计算性能

根据论文的结果，这些问题在计算上非常具有挑战性：

| Case | 变量数 | 约束数 | BARON 5小时 | ANTIGONE 5小时 |
|------|--------|--------|-------------|----------------|
| 1    | 3,573  | 3,428  | 34,167,968  | 34,167,968    |
| 2    | 7,157  | 8,156  | 67,303,190  | N/A (不可行)   |
| 3    | 21,469 | 24,466 | 125,250,466 | N/A (不可行)   |

**注意**:

- 这些是大规模非凸 MINLP 问题
- 求解时间可能很长（数小时到数天）
- 不保证找到全局最优解
- SCIP 的性能可能与 BARON 不同

## 代码结构

```

pyomo_models/
├── **init**.py           # 包初始化
├── data_reader.py        # 数据读取模块
└── refinery_model.py     # Pyomo 模型实现

solve_refinery.py         # 求解脚本
README_PYOMO.md           # 本文档

```

## 主要类

### RefineryDataReader

从 Excel 文件读取集合和参数数据。

```python
from pyomo_models.data_reader import RefineryDataReader

reader = RefineryDataReader('case1')
sets, params = reader.read_all_data()

# 获取特定集合
streams = reader.get_set('S')

# 获取特定参数
product_prices = reader.get_parameter('c_P')
```

### RefineryPlanningModel

构建和求解 Pyomo 模型。

```python
from pyomo_models.model_builder import RefineryPlanningModel

model = RefineryPlanningModel('case1')
model.build_model()         # 构建模型
model.print_summary()       # 打印统计信息
results = model.solve()     # 求解模型
```

## 参考文献

W. Du, C. Wang, C. Fan, Z. Li, Y. Zhong, T. Kang, Z. Liang, M. Yang, F. Qian, and X. Dai.
"A production planning benchmark for real-world refinery-petrochemical complexes."
arXiv preprint arXiv:2503.22057, 2025.

## 许可证

与主仓库相同的许可证。

## 贡献

如有问题或改进建议，请在 GitHub 仓库提交 Issue 或 Pull Request。
