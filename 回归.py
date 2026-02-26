import pandas as pd
import statsmodels.api as sm

# ==========================================
# 1. 基础设置与数据读取
# ==========================================
input_file = r"D:\1sdgplanning\1data\1统计数据匹配.xlsx"
output_file = r"D:\1sdgplanning\1data\回归结果\regression_Stepwise_Mechanism_Analysis.xlsx"

df = pd.read_excel(input_file, sheet_name='data')
y_col = 'total'

# --- 变量分组定义 (42个变量归类) ---

# Spec I: 经济与产业基准 (Economic & Industrial Baseline)
# 解释：最基础的资源禀赋与经济结构
vars_spec1 = [
    'gdp', 'population', 'pro_capital', 'big_city', 
    'primary_industry', 'secondary_sector', 'tertiary_sectory'
]

# Spec II: 政策优先级与公共服务 (Policy Priority & Public Services)
# 解释：政府的主观投入与服务水平 (回应审稿人 "Policy Priority")
vars_spec2 = vars_spec1 + [
    'expenditure', 'sci_expend', 'edu_expend', 'education', 
    'hospital', 'library', 'property', 'export', 'high_way'
]

# Spec III: 自然地理与空间约束 (Physical Geography & Spatial Constraints)
# 解释：不可改变的自然地理特征 (回应审稿人 "How spatial certain SDGs are")
vars_spec3 = vars_spec2 + [
    'elevation_mean', 'elevation_sd', 'slope_mean', 'slope_sd', 'rain',
    'coastal', 'yangtze_river', 'yellow_river', 'hu_line', 'eco',
    'buildup', 'water', 'greening'
]

# Spec IV: 国家战略试点 (Strategic Policy Pilots)
# 解释：更高级别的制度性干扰
vars_spec4 = vars_spec3 + [
    'pilot_eco', 'pilot_fdi', 'pilot_ecosupervison', 'pilot_inno', 
    'pilot_urban', 'pilot_resilience', 'pilot_15min'
]

# 汇总所有涉及的自变量用于表格排序（包括那些没在Spec里但你在列表里的极值变量）
# 这里补充上 elevation_min 等剩余变量，确保表格行完整
all_potential_vars = vars_spec4 + [
    'elevation_min', 'elevation_max', 'elevation_range', 
    'slope_min', 'slope_max', 'slope_range'
]

# 清理缺失值
df_clean = df.dropna(subset=[y_col] + vars_spec4).copy()
y = df_clean[y_col]

# ==========================================
# 2. 辅助函数
# ==========================================
def get_significance_stars(p_value):
    if p_value < 0.001: return '***'
    elif p_value < 0.01: return '**'
    elif p_value < 0.05: return '*'
    else: return ''

def run_spec_model(x_vars):
    X = sm.add_constant(df_clean[x_vars])
    # 稳健标准误回归
    model = sm.OLS(y, X).fit(cov_type='HC3')
    
    res = {}
    for var in ['const'] + all_potential_vars:
        if var in model.params:
            coef = model.params[var]
            pval = model.pvalues[var]
            res[var] = f"{coef:.4f}{get_significance_stars(pval)}"
        else:
            res[var] = ""
            
    res['Observations'] = str(int(model.nobs))
    res['R-squared'] = f"{model.rsquared:.4f}"
    res['Adj. R-squared'] = f"{model.rsquared_adj:.4f}"
    return res

# ==========================================
# 3. 执行回归
# ==========================================
results_dict = {
    'Spec I (经济基准)': run_spec_model(vars_spec1),
    'Spec II (+政策投入)': run_spec_model(vars_spec2),
    'Spec III (+空间地理)': run_spec_model(vars_spec3),
    'Spec IV (+战略试点)': run_spec_model(vars_spec4)
}

# ==========================================
# 4. 导出
# ==========================================
results_df = pd.DataFrame(results_dict)

# 定义表格行顺序
row_order = ['const'] + all_potential_vars + ['Observations', 'R-squared', 'Adj. R-squared']
results_df = results_df.reindex(row_order)

results_df.to_excel(output_file, index_label='Variables')

print(f"阶梯式回归分析已完成！请查看：\n{output_file}")