"""
================================================================================
研究目的：回应审稿人关于“异质性解释不足”的质疑，通过实证模型识别驱动SDG分布的关键机制。
主要功能：
    1. 采用分层回归（Hierarchical Regression）策略，量化空间约束与政策干预的边际贡献。
    2. 对数化处理：对规模变量进行ln(x+1)转换，捕捉非线性弹性关系并提升统计显著性。
    3. 标准化系数：通过Z-score标准化，使不同量纲的变量（如GDP与试点虚拟变量）具有可比性。
    4. 稳健性保障：使用HC3稳健标准误纠正异方差，确保在保留极端值情况下的推断可靠性。

模型逻辑说明 (Responding to Reviewer Comment 2):
    - Spec I (基础指标): 验证城市规模与基础公共服务（人口、经济、教育、医疗）的底层解释力。
    - Spec II (+空间地理): 引入自然地理约束（长江、胡线、沿海），分析SDG分布的“空间属性”强弱。
    - Spec III (+政策取向): 引入行政能级与国家战略试点，论证“政策优先级”对SDG表现的净驱动效应。
    - Δ R-squared: 衡量每一层因素对异质性解释的额外贡献率，直接回答“谁更重要”的问题。
================================================================================
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler

# ==========================================
# 1. 基础设置与手动变量配置
# ==========================================
input_file = r"D:\1sdgplanning\1data\1统计数据匹配.xlsx"
output_file = r"D:\1sdgplanning\1data\回归结果\Manual_3Layer_LogTransformed_Analysis.xlsx"

df = pd.read_excel(input_file, sheet_name='data')
y_col = 'total'

# --- 规模变量取对数处理 ---
# 定义需要取对数的规模变量
scale_vars = ['population', 'gdp', 'education', 'hospital']

# 执行对数转换 (ln(x+1))，创建新列名
for v in scale_vars:
    if v in df.columns:
        df[f'ln_{v}'] = np.log(df[v] + 1)

# --- 更新三层回归变量列表 ---

# 第一层：基础发展（已取对数）
vars_layer1 = ['ln_population', 'ln_gdp', 'ln_education', 'ln_hospital']

# 第二层：空间地理约束
vars_layer2 = vars_layer1 + ['yangtze_river', 'hu_line', 'coastal']

# 第三层：城市能级与战略政策
vars_layer3 = vars_layer2 + ['pro_capital', 'big_city', 'pilot_fdi', 'pilot_urban']

all_selected_vars = list(dict.fromkeys(vars_layer3))

# ==========================================
# 2. 数据清洗与标准化处理 (不去除极端值)
# ==========================================
# 1. 剔除缺失值
df_clean = df.dropna(subset=[y_col] + all_selected_vars).copy()

# 2. 标准化处理 (Z-score)
# 虽然取了对数，但量纲仍不同（如对数后的GDP vs 0-1变量），标准化有助于对比系数
scaler = StandardScaler()
df_clean[all_selected_vars] = scaler.fit_transform(df_clean[all_selected_vars])

y = df_clean[y_col]

print(f"数据处理完成。使用样本量: {len(df_clean)} (对数化处理，未剔除极端值)")

# ==========================================
# 3. 辅助函数与回归运行
# ==========================================
def get_stars(p):
    if p < 0.001: return '***'
    elif p < 0.01: return '**'
    elif p < 0.05: return '*'
    else: return ''

def run_regression(x_vars):
    X = sm.add_constant(df_clean[x_vars])
    # 使用稳健标准误 HC3
    model = sm.OLS(y, X).fit(cov_type='HC3')
    
    res = {}
    for var in ['const'] + all_selected_vars:
        if var in model.params:
            coef = model.params[var]
            pval = model.pvalues[var]
            res[var] = f"{coef:.4f}{get_stars(pval)}"
        else:
            res[var] = ""
            
    res['Observations'] = int(model.nobs)
    res['R-squared'] = model.rsquared
    res['Adj. R-squared'] = model.rsquared_adj
    return res

# 运行三层模型
results_dict = {
    'Spec I (基础指标)': run_regression(vars_layer1),
    'Spec II (+空间地理)': run_regression(vars_layer2),
    'Spec III (+政策取向)': run_regression(vars_layer3)
}

# ==========================================
# 4. 整理结果并导出
# ==========================================
results_df = pd.DataFrame(results_dict)

# 计算 R-squared 增量
r2_vals = results_df.loc['R-squared'].astype(float).values
delta_r2 = [r2_vals[0], r2_vals[1]-r2_vals[0], r2_vals[2]-r2_vals[1]]

results_df.loc['Δ R-squared'] = [f"{val:.4f}" for val in delta_r2]
results_df.loc['R-squared'] = [f"{val:.4f}" for val in r2_vals]
results_df.loc['Adj. R-squared'] = results_df.loc['Adj. R-squared'].apply(lambda x: f"{float(x):.4f}")

# 排序并导出
row_order = ['const'] + all_selected_vars + ['Observations', 'R-squared', 'Adj. R-squared', 'Δ R-squared']
results_df = results_df.reindex(row_order)

results_df.to_excel(output_file, index_label='Variables')

print(f"对数化阶梯回归已完成！结果保存至：\n{output_file}")