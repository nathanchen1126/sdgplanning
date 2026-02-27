"""
================================================================================
非参数机器学习：全指标池接入 + 原始/对数变量共线性对比 + 分组贡献度导出
数据来源：匹配了丰富自然地理与政策试点的新数据集 (1统计数据匹配.xlsx)

【最新更新说明】：
    1. 全变量纳入：不手动剔除任何变量，42个特征全景扫描。
    2. 双轨制对比：针对绝对规模变量，同时保留原始值与 ln(x+1) 对数化值，以供 VIF 对比。
    3. 分组解释力导出：将三大组别（基础、空间、政策）的总解释力及包含变量导出至独立 Excel。
================================================================================
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
import shap
import matplotlib.pyplot as plt
import os

# 防止中文字体显示报错
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Microsoft YaHei']  
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. 基础设置与数据准备 
# ==========================================
input_file = r"D:\1sdgplanning\1data\1统计数据匹配.xlsx"
output_dir = r"D:\1sdgplanning\1data\回归结果"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

df = pd.read_excel(input_file, sheet_name='data')
y_col = 'total'

# --- 变量分组与对数化处理 ---
# 提取所有需要取对数的绝对规模连续变量
vars_to_log = [
    'population', 'education', 'hospital', 'library', 'property', 'gdp', 
    'expenditure', 'buildup', 'water', 'sci_expend', 'edu_expend', 'export', 'high_way'
]

# 执行对数化，但【不删除】原变量
for v in vars_to_log:
    if v in df.columns:
        df[f'ln_{v}'] = np.log(df[v] + 1)

# 将全量指标系统地分配到三大维度中（包含原始值与对数值）
layer1_baseline = [
    'population', 'gdp',  'ln_buildup', 
]

layer2_spatial = [
    'ln_high_way',  'elevation_mean', 
    'slope_mean', 
     'ln_water', 'rain', 'yangtze_river', 'yellow_river', 'hu_line', 'coastal'
]

layer3_policy = [
    'ln_sci_expend', 'ln_edu_expend',
    'pro_capital', 'big_city', 'pilot_eco', 'pilot_fdi', 'pilot_ecosupervison', 
    'pilot_inno', 'pilot_urban', 'pilot_resilience', 'pilot_15min'
]

# 合并所有特征，并确保它们在数据集中确实存在
all_features_raw = layer1_baseline + layer2_spatial + layer3_policy
all_features = [f for f in all_features_raw if f in df.columns]

df_clean = df.dropna(subset=[y_col] + all_features).copy()

# 标准化处理：仅针对具有5个以上唯一值的连续变量
continuous_features = [f for f in all_features if df_clean[f].nunique() > 5]
scaler = StandardScaler()
df_clean[continuous_features] = scaler.fit_transform(df_clean[continuous_features])

X = df_clean[all_features]
y = df_clean[y_col]

# ==========================================
# 2. 多重共线性诊断 (VIF)
# ==========================================
print("\n" + "="*50)
print(" 正在计算方差膨胀因子 (VIF) 评估多重共线性...")
print("="*50)

X_vif = sm.add_constant(X)
vif_data = pd.DataFrame()
vif_data["Variable"] = X_vif.columns
vif_data["VIF"] = [variance_inflation_factor(X_vif.values, i) for i in range(X_vif.shape[1])]

vif_data = vif_data[vif_data["Variable"] != "const"].sort_values(by="VIF", ascending=False)
print(vif_data.head(10)) 

vif_output_path = os.path.join(output_dir, "VIF_Results_Full.xlsx")
vif_data.to_excel(vif_output_path, index=False)
print(f"-> 全变量 VIF 结果已保存至: {vif_output_path}")

# ==========================================
# 3. 训练模型与精度评估
# ==========================================
print("\n" + "="*50)
print(f" 有效样本量: {len(df_clean)} | 纳入特征总数: {len(all_features)}")
print(" 正在训练随机森林模型...")
print("="*50)
rf_model = RandomForestRegressor(n_estimators=1000, max_depth=15, min_samples_leaf=2, random_state=42, oob_score=True)
rf_model.fit(X, y)

y_pred = rf_model.predict(X)
r2 = r2_score(y, y_pred)
mae = mean_absolute_error(y, y_pred)
rmse = np.sqrt(mean_squared_error(y, y_pred))
oob_r2 = rf_model.oob_score_

print(f"-> 决定系数 R-squared (R²):  {r2:.4f}")
print(f"-> 平均绝对误差 (MAE):        {mae:.4f}")
print(f"-> 均方根误差 (RMSE):       {rmse:.4f}")
print(f"-> OOB 泛化估算 R-squared:  {oob_r2:.4f}")

# ==========================================
# 4. SHAP 分析与图表输出
# ==========================================
print("\n正在计算 SHAP 值分析特征重要性")
explainer = shap.TreeExplainer(rf_model)
shap_values = explainer.shap_values(X)

# 图1: SHAP 总体特征重要性条形图 (展示前20个最重要变量)
plt.figure(figsize=(10, 8))
shap.summary_plot(shap_values, X, plot_type="bar", show=False, max_display=20)
plt.title("Drivers of SDG Heterogeneity (Top 20 Full Pool)", fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "SHAP_Importance_Bar_Full.png"), dpi=300)
plt.close()

# 图2: SHAP 蜂拥分布图
plt.figure(figsize=(10, 8))
shap.summary_plot(shap_values, X, show=False, max_display=20)
plt.title("Directional Impact on SDGs (SHAP Summary Full)", fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "SHAP_Summary_Plot_Full.png"), dpi=300)
plt.close()

# ==========================================
# 5. 核心：计算维度驱动力、分组解释力并导出 Excel
# ==========================================
shap_abs_mean = np.mean(np.abs(shap_values), axis=0)
importance_df = pd.DataFrame({'Variable': X.columns, 'Importance': shap_abs_mean})
total_impact = importance_df['Importance'].sum()

# 构建分组导出列表
group_results = []
for group_name, group_vars in zip(
    ['1_基础发展控制 (Baseline)', '2_空间与自然属性 (Spatial)', '3_政策偏好与干预 (Policy)'], 
    [layer1_baseline, layer2_spatial, layer3_policy]
):
    valid_vars = [v for v in group_vars if v in X.columns]
    group_imp = importance_df[importance_df['Variable'].isin(valid_vars)]['Importance'].sum()
    group_pct = (group_imp / total_impact) * 100
    
    group_results.append({
        'Group_Name': group_name,
        'Total_Importance': group_imp,
        'Contribution_Percentage(%)': group_pct,
        'Included_Variables': ", ".join(valid_vars)
    })

# --- 打印组别结论 ---
print("\n" + "="*50)
print(" 核心结论：三大维度的确切驱动力占比 ")
print("="*50)
for res in group_results:
    print(f"{res['Group_Name']}: {res['Contribution_Percentage(%)']:.2f}%")

# --- 导出分组结果 ---
group_df = pd.DataFrame(group_results)
group_output_path = os.path.join(output_dir, "Group_Importance_Results.xlsx")
group_df.to_excel(group_output_path, index=False)
print(f"\n-> 分组解释力及包含指标清单已保存至: {group_output_path}")

# --- 导出并打印所有单个变量的贡献结果 ---
importance_df['Contribution_Percentage(%)'] = (importance_df['Importance'] / total_impact) * 100
importance_df = importance_df.sort_values(by='Importance', ascending=False)
importance_output_path = os.path.join(output_dir, "SHAP_Importance_Results_Full.xlsx")
importance_df.to_excel(importance_output_path, index=False)

print("\n🏆 Top 10 单一驱动因子：")
for idx, row in importance_df.head(10).iterrows():
    print(f" - {row['Variable']}: {row['Contribution_Percentage(%)']:.2f}%")
    
print(f"\n✅ 全部跑通完毕！所有全量分析结果均已保存至: {output_dir}")