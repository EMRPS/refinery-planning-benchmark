"""
数据读取模块：从 Excel 和 txt 文件中读取炼厂规划模型的集合和参数
"""
import pandas as pd
import os
from typing import Dict, List, Set, Tuple, Any


class RefineryDataReader:
    """炼厂规划数据读取器"""
    
    def __init__(self, case_folder: str):
        """
        初始化数据读取器
        
        Args:
            case_folder: 案例文件夹路径 (如 'case1', 'case2', 'case3')
        """
        self.case_folder = case_folder
        self.sets = {}
        self.parameters = {}
        
    def read_sets(self) -> Dict[str, Any]:
        """
        从 Excel 文件读取所有集合
        
        Returns:
            包含所有集合的字典
        """
        excel_file = os.path.join(self.case_folder, 'all_sets_export.xlsx')
        
        if not os.path.exists(excel_file):
            raise FileNotFoundError(f"找不到文件: {excel_file}")
        
        xl_file = pd.ExcelFile(excel_file)
        
        for sheet_name in xl_file.sheet_names:
            df = pd.read_excel(xl_file, sheet_name=sheet_name)
            
            # 单列集合
            if df.shape[1] == 1:
                # 获取列名作为第一个元素
                first_elem = df.columns[0]
                # 获取列中的所有元素
                elements = [first_elem] + df.iloc[:, 0].tolist()
                self.sets[sheet_name] = elements
            
            # 多列集合（对偶或三元组）
            elif df.shape[1] >= 2:
                if sheet_name in ['IM', 'OM', 'IU', 'OU', 'SC']:
                    # 这些是二元组集合: (u, s) 或 (u, m, s)
                    tuples = []
                    for _, row in df.iterrows():
                        if df.shape[1] == 2:
                            tuples.append((row.iloc[0], row.iloc[1]))
                        else:
                            tuples.append(tuple(row.values))
                    self.sets[sheet_name] = tuples
                elif sheet_name in ['SQ', 'QT', 'VMQ', 'DBSQ', 'CAPS', 'CDUMQ']:
                    # 这些是二元组或三元组集合
                    tuples = []
                    for _, row in df.iterrows():
                        tuples.append(tuple(row.values))
                    self.sets[sheet_name] = tuples
                else:
                    # 默认作为二元组处理
                    tuples = []
                    for _, row in df.iterrows():
                        tuples.append(tuple(row.values))
                    self.sets[sheet_name] = tuples
            
            # 空集合
            else:
                self.sets[sheet_name] = []
        
        return self.sets
    
    def read_parameters(self) -> Dict[str, Any]:
        """
        从 Excel 文件读取所有参数
        
        Returns:
            包含所有参数的字典
        """
        excel_file = os.path.join(self.case_folder, 'all_parameters_export.xlsx')
        
        if not os.path.exists(excel_file):
            raise FileNotFoundError(f"找不到文件: {excel_file}")
        
        xl_file = pd.ExcelFile(excel_file)
        
        for sheet_name in xl_file.sheet_names:
            df = pd.read_excel(xl_file, sheet_name=sheet_name)
            
            # 跳过空表
            if df.empty:
                self.parameters[sheet_name] = {}
                continue
            
            param_dict = {}
            
            # 处理不同格式的参数
            # 最后一列是值，前面的列是索引
            if df.shape[1] >= 2:
                for _, row in df.iterrows():
                    if df.shape[1] == 2:
                        # 单索引参数
                        key = row.iloc[0]
                    else:
                        # 多索引参数
                        key = tuple(row.iloc[:-1].values)
                    value = row.iloc[-1]
                    param_dict[key] = value
            
            self.parameters[sheet_name] = param_dict
        
        return self.parameters
    
    def read_all_data(self) -> Tuple[Dict, Dict]:
        """
        读取所有集合和参数
        
        Returns:
            (sets, parameters) 元组
        """
        self.read_sets()
        self.read_parameters()
        return self.sets, self.parameters
    
    def get_set(self, set_name: str) -> Any:
        """获取指定集合"""
        if set_name not in self.sets:
            raise KeyError(f"集合 {set_name} 不存在")
        return self.sets[set_name]
    
    def get_parameter(self, param_name: str) -> Dict:
        """获取指定参数"""
        if param_name not in self.parameters:
            raise KeyError(f"参数 {param_name} 不存在")
        return self.parameters[param_name]
    
    def has_parameter(self, param_name: str, key: Any) -> bool:
        """检查参数是否存在某个键"""
        if param_name not in self.parameters:
            return False
        return key in self.parameters[param_name]
    
    def get_parameter_value(self, param_name: str, key: Any, default: Any = 0.0) -> Any:
        """获取参数值，如果不存在返回默认值"""
        if not self.has_parameter(param_name, key):
            return default
        return self.parameters[param_name][key]


def test_data_reader():
    """测试数据读取器"""
    print("测试 Case 1 数据读取器...")
    reader = RefineryDataReader('case1')
    sets, params = reader.read_all_data()
    
    print(f"\n读取到 {len(sets)} 个集合:")
    for name in sorted(sets.keys())[:10]:
        print(f"  {name}: {len(sets[name])} 个元素")
    
    print(f"\n读取到 {len(params)} 个参数:")
    for name in sorted(params.keys())[:10]:
        print(f"  {name}: {len(params[name])} 个值")
    
    # 测试一些关键集合
    print(f"\n集合 S (streams) 包含 {len(sets['S'])} 个流")
    print(f"集合 U (units) 包含 {len(sets['U'])} 个单元")
    print(f"集合 T (periods) 包含 {len(sets['T'])} 个周期")
    
    # 测试一些关键参数
    print(f"\n参数 c_P (product price) 包含 {len(params['c_P'])} 个值")
    print(f"参数 c_M (material cost) 包含 {len(params['c_M'])} 个值")


if __name__ == '__main__':
    test_data_reader()
