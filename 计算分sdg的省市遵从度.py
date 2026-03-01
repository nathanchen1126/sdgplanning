import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import scipy.stats as stats

# =================================================================
# 1. 加载数据 (遵循您的本地路径)
# =================================================================
input_path = r'D:\1sdgplanning\1data\1sdg省市匹配.xlsx'
df = pd.read_excel(input_path)

# 将“省”重命名为 Province 以便公式解析
df.rename(columns={'省': 'Province'}, inplace=True)

# =================================================================
# 2. 定义计算函数 (增加显著性 LRT 检验)
# =================================================================
def calculate_with_significance(data, target_col, group_col):
    """
    计算 ICC1, ICC2 并通过似然比检验 (LRT) 计算随机效应显著性
    """
    # a. 构建混合线性模型 (包含省级随机截距)
    # 使用 reml=False (MLE) 以便进行 LRT 比较
    mixed_model = smf.mixedlm(f"{target_col} ~ 1", data, groups=data[group_col])
    mixed_result = mixed_model.fit(reml=False)
    
    # b. 构建普通线性模型 (Null OLS 模型，不含随机效应)
    ols_model = smf.ols(f"{target_col} ~ 1", data)
    ols_result = ols_model.fit()
    
    # c. 提取方差分量 [cite: 2213]
    tau_00 = mixed_result.cov_re.iloc[0, 0]  # 组间方差
    sigma_sq = mixed_result.scale            # 组内方差
    
    # d. 计算 ICC 指标 [cite: 2013]
    icc1 = tau_00 / (tau_00 + sigma_sq) if (tau_00 + sigma_sq) > 0 else 0
    n_j = data.groupby(group_col).size().mean()
    icc2 = (n_j * tau_00) / (n_j * tau_00 + sigma_sq) if (n_j * tau_00 + sigma_sq) > 0 else 0
    
    # e. 似然比检验 (LRT) 计算 p 值
    # 检验随机方差分量是否显著大于 0
    lrt_stat = 2 * (mixed_result.llf - ols_result.llf)
    # 使用混合卡方分布检验 (50% point mass at 0 + 50% chi2(1))
    p_val = 0.5 * (1 - stats.chi2.cdf(lrt_stat, 1)) if lrt_stat > 0 else 1.0
    
    return {
        'Between_group_Var_tau00': tau_00,
        'Within_group_Var_sigma2': sigma_sq,
        'ICC1': icc1,
        'ICC2': icc2,
        'LRT_p_value': p_val
    }

# =================================================================
# 3. 批量运行 17 个 SDG 指标
# =================================================================
final_results = []

for i in range(1, 18):
    sdg_col = f'sdg{i}'
    if sdg_col in df.columns:
        print(f"正在分析 {sdg_col}...")
        try:
            metrics = calculate_with_significance(df, sdg_col, 'Province')
            metrics['SDG_Indicator'] = f'SDG{i}'
            final_results.append(metrics)
        except Exception as e:
            print(f"⚠️ {sdg_col} 计算异常: {e}")

# =================================================================
# 4. 结果整理与导出
# =================================================================
res_df = pd.DataFrame(final_results)
# 按 ICC1 排序，呈现从“强省级统筹”到“强地方自主”的梯度 [cite: 2213]
res_df = res_df[['SDG_Indicator', 'Between_group_Var_tau00', 
                 'Within_group_Var_sigma2', 'ICC1', 'ICC2', 'LRT_p_value']]
res_df = res_df.sort_values(by='ICC1', ascending=False)

output_path = r'D:\1sdgplanning\1data\SDG_HLM_Full_Analysis.csv'
res_df.to_csv(output_path, index=False, encoding='utf-8-sig')

print("\n" + "="*50)
print(f"✅ HLM 显著性分析完成！")
print("="*50)
print(res_df.to_string(index=False))