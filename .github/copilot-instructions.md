# Copilot Instructions

## 仓库目的与架构

本仓库实现炼厂-石化联合体生产规划基准（来自 arXiv:2503.22057），提供**双模型实现**：

1. **GAMS 原始实现** (`case*/case*.gms`, `.gdx` 数据)：论文基准，使用 BARON/ANTIGONE 求解
2. **Pyomo 重构实现** (`pyomo_models/`)：开源替代方案，使用 SCIP 求解器，完全基于 Excel 数据文件

### 目录结构

```
case1/, case2/, case3/           # 三个案例的数据集
├── all_sets.txt/.gdx/.xlsx      # 集合：S(流), U(单元), Q(性质), 关系集合
├── all_parameters.txt/.gdx/.xlsx # 参数：收率、价格、容量、性质界限
├── case*.gms                     # GAMS 模型（自动生成，勿手编）
└── solution_*.gdx                # BARON/ANTIGONE 参考解

pyomo_models/
├── data_reader.py                # Excel → Python 数据加载器
├── refinery_model.py             # 完整 MINLP Pyomo 模型（1068行，对应论文公式）
└── __init__.py

arXiv-2503.22057v1/RPBM.tex       # 论文源码：案例定义、命名约定、基准求解结果
```

## 案例差异（影响模型复杂度）

| 案例   | 类型    | CDU | 工艺单元 | 产品 | 变量数  | 二元变量 | 关键特性           |
| ------ | ------- | --- | -------- | ---- | ------- | -------- | ------------------ |
| Case 1 | NLP     | 2   | 25       | 24   | 3573    | 0        | 单周期，无库存     |
| Case 2 | MINLP   | 3   | 51       | 44   | 7157    | 56       | 单周期，有库存管理 |
| Case 3 | MINLP   | 3   | 51       | 44   | 21469   | 168      | 三周期 (T=1,2,3)   |

**数据约定**：空缺的上界参数（如 `FQMax`, `FVMax`）表示**无约束**，而非零值（GAMS 会默认赋 0，需手动处理）。

## 双模型工作流

### GAMS 工作流（原始基准）

```bash
# 求解并验证 BARON 基准
gams case1/case1.gms lo=3 solver=baron

# 检查结果（利润在变量列表末尾，如 x3573）
gdxdump case1/solution_baron.gdx
```

- **数据编辑**：修改 `all_sets.txt` / `all_parameters.txt` → 用 GAMS 工具重新生成 `.gdx`
- **GDXXRW 导出**：执行 `all_*_export.yaml` 生成 Excel 视图（路径需改相对路径）
- **勿提交** `.lst` 日志文件

### Pyomo 工作流（开源实现）

**依赖安装**：
```bash
pip install pyomo pandas openpyxl pyscipopt
```

**快速测试**（验证数据读取和模型构建）：
```bash
python test_basic.py  # 检查 34 个集合、30+ 参数能否正确读取
```

**构建模型不求解**（查看变量/约束统计）：
```python
from pyomo_models.refinery_model import RefineryPlanningModel
model = RefineryPlanningModel('case1')
model.build_model()
model.print_summary()  # 显示变量数、约束数、集合大小
```

**命令行求解**：
```bash
python solve_refinery.py 1 --solver scip --time-limit 3600 --output result.txt
```

**Python 脚本求解**：
```python
model = RefineryPlanningModel('case2')
model.build_model()
results = model.solve(solver_name='scip', time_limit=18000)
```

## Pyomo 模型技术细节

### 数据读取器 (`data_reader.py`)

- **输入**：`case*/all_sets_export.xlsx` 和 `all_parameters_export.xlsx`
- **集合类型**：
  - 单列集合 → Python `list`（如 `S`, `U`, `Q`）
  - 多列集合 → `list[tuple]`（如 `IU:(u,s)`, `IM:(u,m,s)`, `SQ:(s,q)`）
- **参数索引**：根据列数自动推断，支持 1-5 索引结构
- **访问接口**：`sets['S']`, `params['FVMax'][(s,t)]`

### 模型构建 (`refinery_model.py`)

**核心约束对应论文公式**：

| 约束组             | 论文公式      | 实现方法                      | 关键集合         |
| ------------------ | ------------- | ----------------------------- | ---------------- |
| 批次物料平衡       | Eq.2-5        | `batch_balance_*` 约束        | `IM`, `OM`       |
| CDU 约束           | Eq.6-10       | 简化 swing-cut 模型           | `UCDU`, `CDUMQ`  |
| 固定收率工艺单元   | Eq.11         | `pf_yield_*` 约束             | `UPF`, `gamma`   |
| Delta-base 工艺    | Eq.12-14      | `pd_yield_*`, `Gamma` 变量    | `UPD`, `delta`   |
| 混合器             | Eq.15-19      | 体积/质量守恒，性质混合       | `UMIX`, `Qv/Qw`  |
| 分流器             | Eq.20         | 性质传递 `FQ[s_out] = FQ[s_in]` | `USPL`         |
| 调合器             | Eq.21-23      | 比重转换，性质界限            | `UBLD`, `FQBMin` |
| 库存管理(Case 2/3) | Eq.24-30      | 二元变量 `X` 互斥进出库       | `L`, `FVLI/O`    |
| 目标函数           | Eq.31         | 利润最大化                    | `c_P`, `c_M`     |

**变量命名规则**：

- `FVI/FVO`: 流的输入/输出质量流量 (`S × T`)
- `FVM`: 批次质量流量 (`U × M × S × T`, 4-索引)
- `FQ`: 流性质值 (`SQ × T`, 仅有效 (s,q) 对)
- `Gamma`: Delta-base 收率系数（影响产量的进料性质偏差）
- `X`: 库存波动二元标志（1=出库，0=入库）

**简化与限制**：

- CDU 使用**简化 swing-cut**（完整公式过于复杂，见 `RPBM.tex` Eq.6-10）
- 组分比例性质 (`Qp`) 未实现复杂混合规则
- 假设所有 `delta`, `Del`, `alpha` 参数有效（需验证数据完整性）

### 求解器配置

**SCIP 默认选项**（`refinery_model.py::solve()`）：

```python
solver.options['limits/time'] = time_limit
solver.options['limits/gap'] = 0.0001  # 0.01% 相对间隙
```

**性能预期**（基于 SCIP）：

- Case 1: ~1小时可达良好解（NLP，无二元变量）
- Case 2/3: 5-10小时获取可行解（MINLP，全局最优难保证）

## 数据文件编辑规范

### GAMS 文本格式 (`all_*.txt`)

```gams
parameter_name(index1, index2)
/
key1.key2=value1, key3.key4=value2
/
```

- **斜杠**标记节区，**逗号**分隔项
- **点号**连接多索引（如 `s1.t2=100`）
- 编辑后必须用 GAMS 工具重新生成 `.gdx`

### Excel 数据格式

- **集合表**：列标题为第一个元素，后续行为其余元素
- **参数表**：前 N 列为索引，最后一列为数值
- 修改 Excel 后需确保 `.gdx` 和 `.txt` 同步（Pyomo 只读 Excel）

## 调试与验证技巧

**数据读取验证**：
```python
reader = RefineryDataReader('case1')
sets, params = reader.read_all_data()
print(f"关系集合 IM: {len(sets['IM'])} 个 (u,m,s) 三元组")
print(f"FVMax 上界: {len(params.get('FVMax', {}))} 项")
```

**约束检查**（跳过 `Constraint.Skip` 的原因）：

- 用 `model.model.<constraint_name>.pprint()` 查看生成的约束
- 检查集合交集：如 `(s,q) in model.SQ` 是否存在

**行为验证**：对比 GAMS 和 Pyomo 的变量值（同一求解器下）

**常见错误**：

- `KeyError` → Excel 表缺失或列名不匹配 → 检查 `data_reader.py::read_parameters()`
- 无可行解 → 检查容量/性质界限是否过紧 → 对比 `all_parameters.txt`
- 约束全跳过 → 集合关系未正确加载 → 验证 `IU/OU/IM/OM` 是否非空

## 贡献指南

**添加新案例**：

1. 复制 `case1/` → `case4/`
2. 修改 `all_sets.txt` / `all_parameters.txt`（调整单元数、周期数）
3. 重新生成 `.gdx` 和 Excel
4. 更新 `README.md` 表格和 `RPBM.tex` §Case Studies

**修改 Pyomo 模型**：

- 在 `refinery_model.py` 中定位对应论文公式的约束方法（如 `_add_cdu_constraints`）
- 遵循现有模式：先检查集合成员性 → 返回 `Constraint.Skip` 或有效表达式
- 测试三个案例都能构建：`python test_basic.py`

**性能优化**：

- 预计算稀疏索引集（如 `FVM_index`）避免无效变量
- 紧化界限（如 CDU 容量范围）减少搜索空间
- 考虑分解策略（先固定二元变量，再求解 NLP）

**LaTeX 编译**：
```bash
cd arXiv-2503.22057v1
pdflatex RPBM && bibtex RPBM && pdflatex RPBM && pdflatex RPBM
```

---

**语言约定**：所有回复使用简体中文

