# A production planning benchmark for real-world refinery-petrochemical complexes

This repository contains the sets and parameters required for constructing the benchmark presented in the paper "**A production planning benchmark for real-world refinery-petrochemical complexes**" by W. Du, C. Wang, C. Fan, Z. Li, Y. Zhong, T. Kang, Z. Liang, M. Yang, F. Qian, and X. Dai. Computational results were obtained from global optimization solvers ANTIGONE and BARON implemented in GAMS 45.5.0 on a desktop equipped with an Inter(R) Core(TM) i7-8700 CPU 3.20 GHz and 16 GB of RAM. You can view the full paper [here](https://arxiv.org/abs/2503.22057).

Please read the **Notes** before using these datas.

## Notes
- Please cite as "Wenli Du, Chuan Wang, Chen Fan, Zhi Li, Yeke Zhong, Tianao Kang, Ziting Liang, Minglei Yang, Feng Qian, Xin Dai. A production planning benchmark for real-world refinery-petrochemical complexes. _arXiv preprint arXiv:2503.22057_, 2025."
- For these following upper bound parameters, the absence of an entry in the provided list for a specific set of indice indicates that **no** upper bound constraint exists for the corresponding combination of indice: **FQMax, FVMax, FQVMax, FQBMax**.  
  e.g. If no entry for FQMax(s1,SPG) is found in the parameter list, this implies that no upper bound constraint is applied to the specific gravity of stream s1. (*Note that certain modeling platforms, such as GAMS, may assign a value of zero to FQMax(s1,SPG) in ths case.*)
- As the global optimum cannot be guaranteed for any instance, variations in computational performance and final solutions may arise due to differences in solver versions and computational platforms.

## Repository structure

```
.
├── README.md           # Repository overview and structure
├── case1               # Folder containing the sets, parameters, and computational results for case 1
|   ├── all_sets.gdx
|   ├── all_sets.txt
|   ├── all_parameters.gdx
|   ├── all_parameters.txt
|   ├── case1.gms       # Executable GAMS code in scalar form
|   ├── log_antigone.log
|   ├── solution_antigone.gdx
|   ├── log_baron.log
|   └── solution_baron.gdx
├── case2               # Folder containing the sets, parameters, and computational results for case 2
|   └── ... 
└── case3               # Folder containing the sets, parameters, and computational results for case 3
    └── ... 
```
