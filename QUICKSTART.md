# 快速入门指南

## 1. 安装依赖

```bash
pip install pyomo pandas openpyxl pyscipopt
```

## 2. 验证安装

运行基本测试以确保一切正常：

```bash
python test_basic.py
```

期望输出：
```
================================================================================
测试数据读取
================================================================================

Case 1:
  集合数量: 34
  参数数量: 30
  流 (S): 364
  单元 (U): 132
  时间周期 (T): 1
  产品 (S_P): 37
  原料 (S_M): 31
  
...

================================================================================
所有测试通过！
================================================================================
```

## 3. 查看使用示例

```bash
python example_usage.py
```

这将展示如何：
- 构建模型
- 访问数据
- 准备求解

## 4. 求解模型

### Case 1（单周期炼厂，NLP）

最简单的案例，推荐先尝试这个：

```bash
# 求解 1 小时
python solve_refinery.py 1 --solver scip --time-limit 3600 --output case1_result.txt
```

### Case 2（单周期炼化一体化，MINLP）

更复杂，包含库存和二元变量：

```bash
# 求解 5 小时
python solve_refinery.py 2 --solver scip --time-limit 18000 --output case2_result.txt
```

### Case 3（三周期炼化一体化，MINLP）

最复杂的案例：

```bash
# 求解 5 小时
python solve_refinery.py 3 --solver scip --time-limit 18000 --output case3_result.txt
```

## 5. 在 Python 中使用

```python
from pyomo_models.refinery_model import RefineryPlanningModel

# 创建模型
model = RefineryPlanningModel('case1')

# 构建模型
model.build_model()

# 查看模型统计
model.print_summary()

# 求解（注意：这可能需要很长时间）
# results = model.solve(solver_name='scip', time_limit=3600)

# 查看结果
# import pyomo.environ as pyo
# if results.solver.termination_condition == pyo.TerminationCondition.optimal:
#     print(f"最优利润: {pyo.value(model.model.profit):,.2f}")
```

## 6. 访问数据

```python
from pyomo_models.data_reader import RefineryDataReader

# 读取数据
reader = RefineryDataReader('case1')
sets, params = reader.read_all_data()

# 查看产品价格
product_prices = params['c_P']
print("产品价格:")
for product, price in list(product_prices.items())[:5]:
    print(f"  {product}: {price:,.0f}")

# 查看原料成本
material_costs = params['c_M']
print("\n原料成本:")
for material, cost in list(material_costs.items())[:5]:
    print(f"  {material}: {cost:,.0f}")
```

## 7. 理解模型结构

阅读文档以深入了解：

- **README_PYOMO.md**: 完整的用户指南
- **IMPLEMENTATION_SUMMARY.md**: 实现细节和技术说明
- **arXiv-2503.22057v1/RPBM.tex**: 原始论文（数学公式）

## 8. 常见问题

### Q: 模型构建很慢？
A: 这是正常的。模型有数千个变量和约束，构建可能需要几分钟。

### Q: 求解器报错？
A: 确保已安装 SCIP 求解器和 pyscipopt 包。可以尝试其他求解器如 IPOPT。

### Q: 如何查看详细的求解日志？
A: 求解脚本会输出详细日志到终端。也可以检查生成的结果文件。

### Q: 能保证找到全局最优解吗？
A: 不能。这些是非凸 MINLP 问题。论文中的商业求解器在 5 小时内也未找到全局最优。

## 9. 下一步

- 阅读完整文档了解模型细节
- 尝试调整求解器参数
- 分析求解结果
- 根据需要修改模型

## 需要帮助？

查看文档或提交 GitHub Issue。
