import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import scipy.stats as stats
import os
import warnings
from statsmodels.tools.sm_exceptions import ConvergenceWarning

# 忽略模型拟合时的收敛警告
warnings.simplefilter('ignore', ConvergenceWarning)

# =================================================================
# 1. 变量配置区 (仅保留 Level-2 省级变量)
# =================================================================
# 连续变量（需取对数）
level2_continuous = ['gdp_pro', 'pop_pro', 'exp_pro', 'bua_pro']
# 类别/虚拟变量
level2_categorical = ['region_pro', 'yz']

# =================================================================
# 2. 数据加载与处理
# =================================================================
input_path = r'D:\1sdgplanning\1data\1HLM_data.xlsx'
output_dir = r'D:\1sdgplanning\1data\HLM'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print("正在加载数据并处理省级 Level-2 变量...")
df = pd.read_excel(input_path)

if '省' in df.columns:
    df.rename(columns={'省': 'Province'}, inplace=True)

# 处理省级连续变量的自然对数
level2_predictors = []
for var in level2_continuous:
    new_col = f'ln_{var}'
    if var in df.columns:
        df[new_col] = np.log1p(df[var])
        level2_predictors.append(new_col)
    else:
        print(f"⚠️ 警告: 未找到省级变量 '{var}'")

# 合并类别变量
level2_predictors.extend([v for v in level2_categorical if v in df.columns])

# =================================================================
# 3. 定义模型计算函数 (严格复刻文献 Table 4 格式)
# =================================================================
def get_stars(pval):
    if pd.isna(pval): return ""
    if pval < 0.01: return "***"
    elif pval < 0.05: return "**"
    elif pval < 0.1: return "*"
    else: return ""

def fit_level2_only_model(data, target_col, group_col, l2_preds):
    valid_preds = [p for p in l2_preds if p in data.columns]
    
    # 构建公式，处理 region 类别变量
    formula_terms = []
    for p in valid_preds:
        if p == 'region':
            formula_terms.append(f"C({p})")
        else:
            formula_terms.append(p)
            
    # 清理含缺失值的行
    model_data = data[[target_col, group_col] + valid_preds].dropna()
    formula = f"{target_col} ~ " + " + ".join(formula_terms)
    
    # 拟合仅含省级变量的模型 (Model 2 in HLM)
    model = smf.mixedlm(formula, model_data, groups=model_data[group_col])
    result = model.fit(reml=False)
    
    # 拟合零模型 (Null Model)
    null_model = smf.mixedlm(f"{target_col} ~ 1", model_data, groups=model_data[group_col])
    null_result = null_model.fit(reml=False)
    
    col_dict = {}
    
    # 1. Intercept
    intercept_coef = result.fe_params['Intercept']
    intercept_p = result.pvalues['Intercept']
    col_dict['Intercept'] = f"{intercept_coef:.3f}{get_stars(intercept_p)}"
    
    # 2. 提取变量系数
    for var in valid_preds:
        if var == 'region':
            col_dict[var] = "Categorical" # 类别变量通常在正文中描述，防止表格变宽
            continue
            
        coef = result.fe_params.get(var, np.nan)
        pval = result.pvalues.get(var, np.nan)
        if not pd.isna(coef):
            col_dict[var] = f"{coef:.3f}{get_stars(pval)}"
        else:
            col_dict[var] = "n.s."
            
    # 3. Chi-square (卡方)
    llf_model = result.llf
    llf_null = null_result.llf
    chi2_stat = max(0, 2 * (llf_model - llf_null))
    df_diff = len(result.fe_params) - 1
    chi2_p = stats.chi2.sf(chi2_stat, df_diff)
    col_dict['Chi-square'] = f"{chi2_stat:.3f}{get_stars(chi2_p)}"
    
    # 4. sigma2 (组内个体方差) & tau (组间截距方差)
    col_dict['sigma2'] = f"{result.scale:.3f}"
    tau_model = result.cov_re.iloc[0, 0]
    col_dict['tau'] = f"{tau_model:.3f}"
    
    # 5. R2_province (省级解释力)
    tau_null = null_result.cov_re.iloc[0, 0]
    r2_prov = (tau_null - tau_model) / tau_null if tau_null > 0 else 0
    # 防止因精度浮动出现极微小的负数或略大于1的数值
    r2_prov = max(0, min(1, r2_prov))
    col_dict['R2_province'] = f"{r2_prov:.3f}"
    
    return col_dict

# =================================================================
# 4. 批量执行并导出
# =================================================================
results_all = {}
print("\n" + "="*50)
print("🚀 开始拟合截距作为结果模型 (仅纳入 Level-2 变量) ...")

for i in range(1, 18):
    sdg_col = f'sdg{i}'
    if sdg_col in df.columns:
        print(f"正在计算 {sdg_col}...")
        try:
            results_all[sdg_col] = fit_level2_only_model(df, sdg_col, 'Province', level2_predictors)
        except Exception as e:
            print(f"⚠️ {sdg_col} 计算失败: {e}")

# 转换为 DataFrame
table4_df = pd.DataFrame(results_all)
row_order = ['Intercept'] + level2_predictors + ['Chi-square', 'sigma2', 'tau', 'R2_province']
table4_df = table4_df.reindex([r for r in row_order if r in table4_df.index])

table4_df.reset_index(inplace=True)
table4_df.rename(columns={'index': 'Variable'}, inplace=True)

output_file = os.path.join(output_dir, 'Table4_Level2_Only_Model.csv')
table4_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print("\n" + "="*50)
print(f"✅ HLM Table 4 (截距作为结果模型) 生成完成！")
print(f"表格已保存至: {output_file}")
print("="*50)