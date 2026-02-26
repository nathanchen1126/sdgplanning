import pandas as pd
import statsmodels.api as sm

# ==========================================
# 1. 基础设置与数据读取
# ==========================================
input_file = r"D:\1sdgplanning\1data\sdg统计数据匹配.xlsx"
output_file = r"D:\1sdgplanning\1data\regression_Stepwise_NoFixedEffects.xlsx"

df = pd.read_excel(input_file, sheet_name='data')
y_col = 'total'

# 定义四个层级的变量（对应不同维度的驱动机制）
# Spec I: 基础发展水平 (Development Levels)
vars_spec1 = ['gdp', 'population']

# Spec II: 政策优先级与投入 (Policy Priority & Public Services)
vars_spec2 = vars_spec1 + ['expenditure', 'education', 'hospital', 'library', 'property']

# Spec III: 空间与地理属性 (Spatial Factors)
vars_spec3 = vars_spec2 + ['coastal', 'yangtze_river', 'yellow_river', 'hu_line']

# Spec IV: 行政级别与国家战略 (Administrative & Strategic Factors)
vars_spec4 = vars_spec3 + ['pro_capital', 'big_city', 'eco']

# 提取核心数据，清理缺失值
all_vars = vars_spec4
df_clean = df.dropna(subset=[y_col] + all_vars).copy()

# 提取因变量
y = df_clean[y_col]

# ==========================================
# 2. 辅助函数：格式化输出
# ==========================================
def get_significance_stars(p_value):
    if p_value < 0.001: return '***'
    elif p_value < 0.01: return '**'
    elif p_value < 0.05: return '*'
    else: return ''

def run_spec_model(x_vars, model_name):
    """运行带有稳健标准误的OLS模型(不含固定效应)，并格式化输出"""
    # 提取自变量并加入常数项
    X = df_clean[x_vars]
    X = sm.add_constant(X)
    
    # 拟合 OLS 模型 (使用 HC3 稳健标准误处理异方差)
    model = sm.OLS(y, X).fit(cov_type='HC3')
    
    # 提取结果
    res = {}
    for var in ['const'] + all_vars:
        if var in model.params:
            coef = model.params[var]
            pval = model.pvalues[var]
            res[var] = f"{coef:.4f}{get_significance_stars(pval)}"
        else:
            res[var] = "" # 如果该模型没用到这个变量，留空
            
    # 补充模型统计量
    res['Observations'] = str(int(model.nobs))
    res['R-squared'] = f"{model.rsquared:.4f}"
    res['Adj. R-squared'] = f"{model.rsquared_adj:.4f}"
    
    return res

# ==========================================
# 3. 运行四个逐步递进模型
# ==========================================
results_dict = {}
results_dict['Spec I (基础发展)'] = run_spec_model(vars_spec1, 'Spec I')
results_dict['Spec II (+政策投入)'] = run_spec_model(vars_spec2, 'Spec II')
results_dict['Spec III (+空间地理)'] = run_spec_model(vars_spec3, 'Spec III')
results_dict['Spec IV (+行政战略)'] = run_spec_model(vars_spec4, 'Spec IV')

# ==========================================
# 4. 整理表格并导出
# ==========================================
results_df = pd.DataFrame(results_dict)

# 强制规范行的排序顺序，让表格符合学术阅读习惯s
row_order = ['const'] + all_vars + ['Observations', 'R-squared', 'Adj. R-squared']
results_df = results_df.reindex(row_order)

# 导出至Excel
results_df.to_excel(output_file, index_label='Variables')

print(f"不包含省份固定效应的逐步回归机制分析已完成！\n结果表格已保存至：\n{output_file}")