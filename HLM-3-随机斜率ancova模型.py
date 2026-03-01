import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import scipy.stats as stats
import os
import warnings
from statsmodels.tools.sm_exceptions import ConvergenceWarning

# 忽略收敛警告
warnings.simplefilter('ignore', ConvergenceWarning)

# =================================================================
# 1. 变量配置区 (全量纳入市级变量)
# =================================================================
# 【核心调节目标】市级空间扩张
target_l1_var = 'ln_buildup'  

# 【市级控制变量】(共22个)
l1_controls = [
    'population', 'gdp', 'ln_high_way', 'elevation_mean', 'slope_mean', 
    'ln_water', 'rain', 'yangtze_river', 'yellow_river', 'hu_line', 'coastal', 
    'ln_sci_expend', 'ln_edu_expend', 'pro_capital', 'big_city', 'pilot_eco', 
    'pilot_fdi', 'pilot_ecosupervison', 'pilot_inno', 'pilot_urban', 
    'pilot_resilience', 'pilot_15min'
]

# 【省级调节变量】(原变量名)
l2_continuous = ['pop_pro', 'exp_pro']
l2_categorical = ['region_pro']

# =================================================================
# 2. 数据加载与精确的对数处理 (修复了 KeyError)
# =================================================================
input_path = r'D:\1sdgplanning\1data\1HLM_data.xlsx'
output_dir = r'D:\1sdgplanning\1data\HLM'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print("正在加载数据并准备全变量版随机 ANCOVA 模型...")
df = pd.read_excel(input_path)

if '省' in df.columns:
    df.rename(columns={'省': 'Province'}, inplace=True)

# 修复点 1：处理 Level-1 变量对数 (如果带有 ln_ 前缀但在数据中没有，则从原变量生成)
for var in [target_l1_var] + l1_controls:
    if var.startswith('ln_') and var not in df.columns:
        raw_var = var[3:]
        if raw_var in df.columns:
            df[var] = np.log1p(df[raw_var])
            print(f"已生成市级对数变量: {var}")
        else:
            print(f"⚠️ 警告: 数据中找不到市级原始变量 '{raw_var}'")

# 修复点 2：明确为省级连续变量生成带 ln_ 的新列
for var in l2_continuous:
    ln_var = f"ln_{var}"
    if ln_var not in df.columns:
        if var in df.columns:
            df[ln_var] = np.log1p(df[var])
            print(f"已生成省级对数变量: {ln_var}")
        else:
            print(f"⚠️ 警告: 数据中找不到省级原始变量 '{var}'")

# 准备进入模型的 Level-2 变量名公式 (带有 ln_ 和 C())
l2_formulas = [f"ln_{v}" for v in l2_continuous]
l2_formulas.extend([f"C({v})" for v in l2_categorical])

# =================================================================
# 3. 定义模型计算函数
# =================================================================
def get_stars(pval):
    if pd.isna(pval): return ""
    if pval < 0.01: return "***"
    elif pval < 0.05: return "**"
    elif pval < 0.1: return "*"
    else: return ""

def fit_ancova_model_full(data, target_col, group_col, target_l1, l1_ctrl, l2_forms):
    # 筛选所需列并清理缺失值
    raw_l2_cols = [v.replace('C(', '').replace(')', '') for v in l2_forms]
    required_cols = [target_col, group_col, target_l1] + l1_ctrl + raw_l2_cols
    
    # 二次验证：确保变量都在数据框中，防止报错
    valid_l1_ctrl = [v for v in l1_ctrl if v in data.columns]
    valid_required_cols = [c for c in required_cols if c in data.columns]
    
    model_data = data[valid_required_cols].copy().dropna()
    
    # 构建固定效应公式
    fe_terms = valid_l1_ctrl + [target_l1] + l2_forms
    interaction_terms = [f"{target_l1}:{l2}" for l2 in l2_forms]
    fe_formula = f"{target_col} ~ " + " + ".join(fe_terms) + " + " + " + ".join(interaction_terms)
    
    # 构建随机效应公式 (市级建成区扩张随机斜率)
    re_formula = f"~ {target_l1}"
    
    col_dict = {}
    try:
        model = smf.mixedlm(fe_formula, model_data, groups=model_data[group_col], re_formula=re_formula)
        result = model.fit(reml=False)
        
        null_model = smf.mixedlm(f"{target_col} ~ 1", model_data, groups=model_data[group_col])
        null_result = null_model.fit(reml=False)
    except Exception as e:
        return {"Error": f"模型未收敛"}

    # ---------------- 格式排版 ----------------
    col_dict['For intercept'] = ""
    col_dict['Intercept_int'] = f"{result.fe_params.get('Intercept', np.nan):.3f}{get_stars(result.pvalues.get('Intercept', np.nan))}"
    
    for l2 in l2_forms:
        if 'C(' in l2:
            col_dict[f'{l2}_int'] = "Categorical"
        else:
            coef = result.fe_params.get(l2, np.nan)
            pval = result.pvalues.get(l2, np.nan)
            col_dict[f'{l2}_int'] = f"{coef:.3f}{get_stars(pval)}" if not pd.isna(coef) else "n.s."
            
    col_dict[f'For {target_l1} slope'] = ""
    col_dict['Intercept_slope'] = f"{result.fe_params.get(target_l1, np.nan):.3f}{get_stars(result.pvalues.get(target_l1, np.nan))}"
    
    for l2 in l2_forms:
        inter_key = f"{target_l1}:{l2}"
        if 'C(' in l2:
            col_dict[f'{l2}_slope'] = "Categorical"
        else:
            coef = result.fe_params.get(inter_key, np.nan)
            pval = result.pvalues.get(inter_key, np.nan)
            col_dict[f'{l2}_slope'] = f"{coef:.3f}{get_stars(pval)}" if not pd.isna(coef) else "n.s."

    for ctrl in valid_l1_ctrl:
        coef = result.fe_params.get(ctrl, np.nan)
        pval = result.pvalues.get(ctrl, np.nan)
        col_dict[f'For {ctrl} slope'] = f"{coef:.3f}{get_stars(pval)}" if not pd.isna(coef) else "n.s."

    llf_model = result.llf
    llf_null = null_result.llf
    chi2_stat = max(0, 2 * (llf_model - llf_null))
    df_diff = len(result.fe_params) - 1
    col_dict['Chi-square'] = f"{chi2_stat:.3f}{get_stars(stats.chi2.sf(chi2_stat, df_diff))}"
    
    sigma2 = result.scale
    sigma2_null = null_result.scale
    col_dict['sigma2'] = f"{sigma2:.3f}"
    
    try:
        tau_int = result.cov_re.iloc[0, 0]
        col_dict['tau'] = f"{tau_int:.3f}"
    except:
        tau_int = np.nan
        col_dict['tau'] = "n.s."
    
    tau_null = null_result.cov_re.iloc[0, 0]
    r2_prov = (tau_null - tau_int) / tau_null if (tau_null > 0 and not pd.isna(tau_int)) else 0
    col_dict['R2_province'] = f"{max(0, min(1, r2_prov)):.3f}"
    
    r2_ind = (sigma2_null - sigma2) / sigma2_null if sigma2_null > 0 else 0
    col_dict['R2_individual'] = f"{max(0, min(1, r2_ind)):.3f}"
    
    return col_dict

# =================================================================
# 4. 批量执行并导出
# =================================================================
results_all = {}
print("\n" + "="*50)
print(f"🚀 开始拟合全变量版随机 ANCOVA 模型...")

for i in range(1, 18):
    sdg_col = f'sdg{i}'
    if sdg_col in df.columns:
        print(f"正在计算 {sdg_col}...")
        res = fit_ancova_model_full(df, sdg_col, 'Province', target_l1_var, l1_controls, l2_formulas)
        if "Error" not in res:
            results_all[sdg_col] = res
        else:
            print(f"   ❌ {sdg_col} {res['Error']}，已跳过。")

if not results_all:
    print("\n🚨 所有指标均未收敛！多层模型极易因为变量过多导致自由度耗尽而崩溃。")
    print("👉 建议退回使用‘精简版’市级变量 (只保留 GDP, population 等最核心变量) 重新运行。")
else:
    table5_df = pd.DataFrame(results_all)

    # 动态构建行顺序，避免不存在的控制变量引发重排错误
    valid_l1_ctrls = [c for c in l1_controls if f'For {c} slope' in table5_df.index]
    
    row_order = ['For intercept', 'Intercept_int'] + [f"{l2}_int" for l2 in l2_formulas] + \
                [f'For {target_l1_var} slope', 'Intercept_slope'] + [f"{l2}_slope" for l2 in l2_formulas] + \
                [f'For {ctrl} slope' for ctrl in valid_l1_ctrls] + \
                ['Chi-square', 'sigma2', 'tau', 'R2_province', 'R2_individual']

    table5_df = table5_df.reindex([r for r in row_order if r in table5_df.index])

    rename_mapping = {
        'Intercept_int': 'Intercept',
        'Intercept_slope': 'Intercept'
    }
    for l2 in l2_formulas:
        clean_name = l2.replace('C(', '').replace(')', '')
        rename_mapping[f'{l2}_int'] = clean_name
        rename_mapping[f'{l2}_slope'] = clean_name

    table5_df.rename(index=rename_mapping, inplace=True)
    table5_df.reset_index(inplace=True)
    table5_df.rename(columns={'index': 'Variable'}, inplace=True)

    output_file = os.path.join(output_dir, 'Table5_Random_ANCOVA_Model_Full.csv')
    table5_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print("\n" + "="*50)
    print(f"✅ 全变量版 HLM Table 5 (随机 ANCOVA 模型) 生成完成！")
    print(f"表格已保存至: {output_file}")
    print("="*50)