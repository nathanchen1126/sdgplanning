"""
================================================================================
优化版分层回归模型 (Optimized Hierarchical Regression)
新增功能：
    1. 修正标准化逻辑：仅对连续规模变量进行Z-score标准化，保留虚拟变量的0-1特征，确保系数可解释。
    2. 显著性检验：增加嵌套模型的 F 检验，验证 ΔR-squared 是否具有统计学显著性。
    3. 稳健性检验：增加 VIF (方差膨胀因子) 检验，排查多重共线性风险。
================================================================================
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor

# ==========================================
# 1. 基础设置与变量配置
# ==========================================
input_file = r"D:\1sdgplanning\1data\1统计数据匹配.xlsx"
output_file = r"D:\1sdgplanning\1data\回归结果\Optimized_3Layer_Analysis.xlsx"

df = pd.read_excel(input_file, sheet_name='data')
y_col = 'total'

# 区分连续变量和虚拟变量
scale_vars = ['population', 'gdp', 'education', 'hospital']
dummy_vars_layer2 = ['yangtze_river', 'hu_line', 'coastal']
dummy_vars_layer3 = ['pro_capital', 'big_city', 'pilot_fdi', 'pilot_urban']

# 对连续变量执行对数转换 (ln(x+1))
log_scale_vars = []
for v in scale_vars:
    if v in df.columns:
        new_col = f'ln_{v}'
        df[new_col] = np.log(df[v] + 1)
        log_scale_vars.append(new_col)

# 定义三层回归的变量列表
vars_layer1 = log_scale_vars.copy()
vars_layer2 = vars_layer1 + dummy_vars_layer2
vars_layer3 = vars_layer2 + dummy_vars_layer3

all_selected_vars = list(dict.fromkeys(vars_layer3))

# ==========================================
# 2. 数据清洗与选择性标准化
# ==========================================
df_clean = df.dropna(subset=[y_col] + all_selected_vars).copy()

# 【关键修正】仅对连续变量进行标准化，不改变虚拟变量的0-1分布
scaler = StandardScaler()
df_clean[log_scale_vars] = scaler.fit_transform(df_clean[log_scale_vars])

y = df_clean[y_col]
print(f"数据处理完成。使用样本量: {len(df_clean)}")

# ==========================================
# 3. 辅助函数
# ==========================================
def get_stars(p):
    if p < 0.001: return '***'
    elif p < 0.01: return '**'
    elif p < 0.05: return '*'
    elif p < 0.1: return '.' # 有时候加上0.1的显著性也很有用
    else: return ''

def check_vif(X_df):
    """计算 VIF 以检查多重共线性"""
    X_with_const = sm.add_constant(X_df)
    vif_data = pd.DataFrame()
    vif_data["Variable"] = X_with_const.columns
    vif_data["VIF"] = [variance_inflation_factor(X_with_const.values, i) for i in range(X_with_const.shape[1])]
    return vif_data[vif_data['Variable'] != 'const']

# ==========================================
# 4. 运行回归与嵌套检验
# ==========================================
models = {}
for name, vars_list in zip(
    ['Spec I (Baseline)', 'Spec II (+Spatial)', 'Spec III (+Policy)'], 
    [vars_layer1, vars_layer2, vars_layer3]
):
    X = sm.add_constant(df_clean[vars_list])
    # 拟合模型，使用 HC3 稳健标准误
    models[name] = sm.OLS(y, X).fit(cov_type='HC3')

# 提取结果的函数
def extract_results(model_dict, all_vars):
    res_df = pd.DataFrame(index=['const'] + all_vars)
    
    r2_list = []
    adj_r2_list = []
    obs_list = []
    
    for name, model in model_dict.items():
        # 提取系数和显著性星号
        coef_series = model.params
        pval_series = model.pvalues
        
        formatted_coefs = []
        for var in res_df.index:
            if var in coef_series:
                coef = coef_series[var]
                pval = pval_series[var]
                # 在系数下方可以加上标准误，这里保持简单，只输出系数和星号
                formatted_coefs.append(f"{coef:.4f}{get_stars(pval)}")
            else:
                formatted_coefs.append("")
        res_df[name] = formatted_coefs
        
        r2_list.append(model.rsquared)
        adj_r2_list.append(model.rsquared_adj)
        obs_list.append(int(model.nobs))
        
    # 添加统计量行
    res_df.loc['Observations'] = obs_list
    res_df.loc['R-squared'] = [f"{x:.4f}" for x in r2_list]
    res_df.loc['Adj. R-squared'] = [f"{x:.4f}" for x in adj_r2_list]
    
    # 计算并测试 Delta R-squared
    delta_r2 = [r2_list[0], r2_list[1] - r2_list[0], r2_list[2] - r2_list[1]]
    res_df.loc['Δ R-squared'] = [f"{x:.4f}" for x in delta_r2]
    
    # 进行嵌套模型的 F 检验 (比较 Model 2 vs 1, Model 3 vs 2)
    f_test_pvals = ["-"]
    
    # 比较 Model 1 和 Model 2
    f_test_1_2 = models['Spec II (+Spatial)'].compare_f_test(models['Spec I (Baseline)'])
    f_test_pvals.append(f"p={f_test_1_2[1]:.4f}{get_stars(f_test_1_2[1])}")
    
    # 比较 Model 2 和 Model 3
    f_test_2_3 = models['Spec III (+Policy)'].compare_f_test(models['Spec II (+Spatial)'])
    f_test_pvals.append(f"p={f_test_2_3[1]:.4f}{get_stars(f_test_2_3[1])}")
    
    res_df.loc['Δ R² F-test P-value'] = f_test_pvals
    
    return res_df

# ==========================================
# 5. 导出结果与 VIF 检查
# ==========================================
final_results = extract_results(models, all_selected_vars)

# 打印最复杂模型(Layer 3)的 VIF
print("\n=== Model III 多重共线性检查 (VIF) ===")
vif_df = check_vif(df_clean[vars_layer3])
print(vif_df)
if any(vif_df['VIF'] > 10):
    print("⚠️ 警告：存在 VIF > 10 的变量，可能存在严重的多重共线性！")
else:
    print("✅ VIF 检查通过，无严重多重共线性。")

final_results.to_excel(output_file, index_label='Variables')
print(f"\n✅ 优化版对数化阶梯回归已完成！结果保存至：\n{output_file}")