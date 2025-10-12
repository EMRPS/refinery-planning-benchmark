# A production planning benchmark for real-world refinery-petrochemical complexes

This repository contains the sets and parameters required for constructing the benchmark presented in the paper "**A production planning benchmark for real-world refinery-petrochemical complexes**" by W. Du, C. Wang, C. Fan, Z. Li, Y. Zhong, T. Kang, Z. Liang, M. Yang, F. Qian, and X. Dai. Computational results were obtained from global optimization solvers ANTIGONE and BARON implemented in GAMS 45.5.0 on a desktop equipped with an Inter(R) Core(TM) i7-8700 CPU 3.20 GHz and 16 GB of RAM. You can view the full paper [here](https://arxiv.org/abs/2503.22057).

Please read the **Notes** before using these datas.

## Notes

- Please cite as "Wenli Du, Chuan Wang, Chen Fan, Zhi Li, Yeke Zhong, Tianao Kang, Ziting Liang, Minglei Yang, Feng Qian, Xin Dai. A production planning benchmark for real-world refinery-petrochemical complexes. _arXiv preprint arXiv:2503.22057_, 2025."
- For these following upper bound parameters, the absence of an entry in the provided list for a specific set of indice indicates that **no** upper bound constraint exists for the corresponding combination of indice: **FQMax, FVMax, FQVMax, FQBMax**.  
  e.g. If no entry for FQMax(s1,SPG) is found in the parameter list, this implies that no upper bound constraint is applied to the specific gravity of stream s1. (_Note that certain modeling platforms, such as GAMS, may assign a value of zero to FQMax(s1,SPG) in ths case._)
- As the global optimum cannot be guaranteed for any instance, variations in computational performance and final solutions may arise due to differences in solver versions and computational platforms.

## Repository structure

```text
.
├── README.md              # Repository overview and structure
├── README_PYOMO.md        # Pyomo implementation documentation
├── data/                  # Data folder containing all case files
│   ├── case1/             # Case 1: NLP problem (2 CDU, 25 units, 24 products)
│   │   ├── all_sets.gdx
│   │   ├── all_sets.txt
│   │   ├── all_sets_export.xlsx
│   │   ├── all_parameters.gdx
│   │   ├── all_parameters.txt
│   │   ├── all_parameters_export.xlsx
│   │   ├── case1.gms       # Executable GAMS code in scalar form
│   │   ├── log_antigone.log
│   │   ├── solution_antigone.gdx
│   │   ├── log_baron.log
│   │   └── solution_baron.gdx
│   ├── case2/             # Case 2: MINLP with inventory (3 CDU, 51 units, 44 products)
│   │   └── ... 
│   └── case3/             # Case 3: Multi-period MINLP (3 periods)
│       └── ... 
├── pyomo_models/          # Pyomo implementation (modular structure)
│   ├── data_reader.py           # Excel data reader
│   ├── model_sets_params_vars.py # Sets, parameters, and variables definitions
│   ├── model_constraints.py     # Constraint definitions with LaTeX formulas
│   ├── model_objective.py       # Objective function definition
│   ├── model_builder.py         # Main model builder and solver interface
│   └── __init__.py
├── test_basic.py          # Basic functionality tests
├── example_usage.py       # Usage examples
└── solve_refinery.py      # Command-line solver script
```
