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
# 1. 变量配置区 (严格按照您的三组变量排列)
# =================================================================
group1_vars = [
    'population', 'gdp', 'ln_buildup'
]

group2_vars = [
    'ln_high_way', 'elevation_mean', 'slope_mean', 'ln_water', 'rain', 
    'yangtze_river', 'yellow_river', 'hu_line', 'coastal'
]

group3_vars = [
    'ln_sci_expend', 'ln_edu_expend', 'pro_capital', 'big_city', 'pilot_eco', 
    'pilot_fdi', 'pilot_ecosupervison', 'pilot_inno', 'pilot_urban', 
    'pilot_resilience', 'pilot_15min'
]

# 合并所有进入模型的最终变量名
level1_predictors = group1_vars + group2_vars + group3_vars

# =================================================================
# 2. 数据加载与智能对数转换
# =================================================================
input_path = r'D:\1sdgplanning\1data\1HLM_data.xlsx'
output_dir = r'D:\1sdgplanning\1data\HLM'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print("正在加载数据并处理变量...")
df = pd.read_excel(input_path)

if '省' in df.columns:
    df.rename(columns={'省': 'Province'}, inplace=True)

# 智能处理：如果变量名以 ln_ 开头，且数据集中只有原始变量，则自动进行 log1p 转换
for var in level1_predictors:
    if var.startswith('ln_') and var not in df.columns:
        raw_var = var[3:]  # 截取去掉 'ln_' 后的原始变量名
        if raw_var in df.columns:
            df[var] = np.log1p(df[raw_var])
            print(f"已生成对数变量: {var} (来自 {raw_var})")
        else:
            print(f"⚠️ 警告: 数据集中未找到原始变量 '{raw_var}'，无法生成 '{var}'。")
    elif var not in df.columns:
        print(f"⚠️ 警告: 数据集中未找到变量 '{var}'，已跳过。")

# =================================================================
# 3. 定义显著性星号生成与模型计算函数
# =================================================================
def get_stars(pval):
    if pd.isna(pval): return ""
    if pval < 0.01: return "***"
    elif pval < 0.05: return "**"
    elif pval < 0.1: return "*"
    else: return ""

def fit_hlm_for_table(data, target_col, group_col, predictors):
    # 仅保留存在于 dataframe 中的 predictors 以防报错
    valid_preds = [p for p in predictors if p in data.columns]
    model_data = data[[target_col, group_col] + valid_preds].dropna()
    
    formula = f"{target_col} ~ " + " + ".join(valid_preds)
    
    # 使用 reml=False 以支持 LRT 检验
    model = smf.mixedlm(formula, model_data, groups=model_data[group_col])
    result = model.fit(reml=False)
    
    null_model = smf.mixedlm(f"{target_col} ~ 1", model_data, groups=model_data[group_col])
    null_result = null_model.fit(reml=False)
    
    col_dict = {}
    
    # 提取截距
    intercept_coef = result.fe_params['Intercept']
    intercept_p = result.pvalues['Intercept']
    col_dict['Intercept'] = f"{intercept_coef:.3f}{get_stars(intercept_p)}"
    
    # 提取自变量系数
    for var in predictors:
        if var in valid_preds:
            coef = result.fe_params.get(var, np.nan)
            pval = result.pvalues.get(var, np.nan)
            if not pd.isna(coef):
                col_dict[var] = f"{coef:.3f}{get_stars(pval)}"
            else:
                col_dict[var] = "n.s."
        else:
            col_dict[var] = "n.s."
            
    # 计算 Chi-square
    llf_model = result.llf
    llf_null = null_result.llf
    chi2_stat = max(0, 2 * (llf_model - llf_null))
    chi2_p = stats.chi2.sf(chi2_stat, len(valid_preds))
    col_dict['Chi-square'] = f"{chi2_stat:.3f}{get_stars(chi2_p)}"
    
    # 提取方差与解释力
    col_dict['sigma2'] = f"{result.scale:.3f}"
    col_dict['tau'] = f"{result.cov_re.iloc[0, 0]:.3f}"
    
    sigma2_null = null_result.scale
    r2_ind = (sigma2_null - result.scale) / sigma2_null if sigma2_null > 0 else 0
    col_dict['R2_individual'] = f"{max(0, r2_ind):.3f}"
    
    return col_dict

# =================================================================
# 4. 批量执行并组装最终表格
# =================================================================
results_all = {}
print("\n" + "="*50)
print("🚀 开始批量拟合模型并按三组变量顺序生成学术表格...")

for i in range(1, 18):
    sdg_col = f'sdg{i}'
    if sdg_col in df.columns:
        print(f"正在计算 {sdg_col}...")
        try:
            results_all[sdg_col] = fit_hlm_for_table(df, sdg_col, 'Province', level1_predictors)
        except Exception as e:
            print(f"⚠️ {sdg_col} 计算失败: {e}")

# 转换为 DataFrame 并严格控制行顺序
table3_df = pd.DataFrame(results_all)
row_order = ['Intercept'] + level1_predictors + ['Chi-square', 'sigma2', 'tau', 'R2_individual']
table3_df = table3_df.reindex([r for r in row_order if r in table3_df.index])

table3_df.reset_index(inplace=True)
table3_df.rename(columns={'index': 'Variable'}, inplace=True)

output_file = os.path.join(output_dir, 'Table3_Random_Intercept_Model.csv')
table3_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print("\n" + "="*50)
print(f"✅ HLM 随机截距模型学术表格生成完成！")
print(f"表格已保存至: {output_file}")
print("注: *** p<0.01; ** p<0.05; * p<0.1")
print("="*50)