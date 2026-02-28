"""
================================================================================
非参数机器学习与高级SHAP可视化脚本
================================================================================
工作内容：
    1. 继承原始数据处理、随机森林训练及VIF、Group Importance计算逻辑。
    2. 整合参考绘图代码，创建一个自定义的组合可视化图表（玫瑰图+条形图+蜂群图）。
    3. 将结果保存至指定路径 D:\1sdgplanning\5fig

工程师：[Your Name/Role as an experienced Python Engineer]
日期：2023-x-x (基于当前请求)
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
import matplotlib.ticker as ticker
import matplotlib.colors as mcolors
from matplotlib.cm import ScalarMappable
import os
import warnings

# 忽略shap计算时的一些不必要警告
warnings.filterwarnings("ignore", category=UserWarning)

# ==========================================
# 0. 全局设置 (Matplotlib & Paths)
# ==========================================
# 防止中文字体显示报错，尝试匹配系统中存在的中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Microsoft YaHei', 'DejaVu Sans'] 
plt.rcParams['axes.unicode_minus'] = False
# 设置全局字体大小，使其更清晰
plt.rcParams['font.size'] = 12


# 路径设置
input_file = r"D:\1sdgplanning\1data\1统计数据匹配.xlsx"
# 原始回归结果保留目录
output_dir_data = r"D:\1sdgplanning\1data\回归结果"
# **用户指定的新图像保存目录**
output_dir_fig = r"D:\1sdgplanning\5fig"

# 确保目录存在
for d in [output_dir_data, output_dir_fig]:
    if not os.path.exists(d):
        os.makedirs(d)

print(f"系统就绪。数据输入: {input_file}")
print(f"数据结果输出: {output_dir_data}")
print(f"图像结果输出: {output_dir_fig}")

# ==========================================
# 1. 数据准备 (继承原始代码)
# ==========================================
print("\n" + "="*30)
print(" 步骤 1: 数据加载与预处理")
print("="*30)

df = pd.read_excel(input_file, sheet_name='data')
y_col = 'total'

# --- 变量分组与对数化处理 ---
vars_to_log = [
    'population', 'education', 'hospital', 'library', 'property', 'gdp', 
    'expenditure', 'buildup', 'water', 'sci_expend', 'edu_expend', 'export', 'high_way'
]

# 执行对数化，但【不删除】原变量
for v in vars_to_log:
    if v in df.columns:
        df[f'ln_{v}'] = np.log(df[v] + 1)

# 将全量指标系统地分配到三大维度中
layer1_baseline = ['population', 'gdp',  'ln_buildup']
layer2_spatial = ['ln_high_way', 'elevation_mean', 'slope_mean', 'ln_water', 'rain', 'yangtze_river', 'yellow_river', 'hu_line', 'coastal']
layer3_policy = ['ln_sci_expend', 'ln_edu_expend', 'pro_capital', 'big_city', 'pilot_eco', 'pilot_fdi', 'pilot_ecosupervison', 'pilot_inno', 'pilot_urban', 'pilot_resilience', 'pilot_15min']

# 创建特征名称到组名的映射字典，用于绘图配色
feature_group_map = {}
for feat in layer1_baseline: feature_group_map[feat] = 'Baseline'
for feat in layer2_spatial: feature_group_map[feat] = 'Spatial'
for feat in layer3_policy: feature_group_map[feat] = 'Policy'

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
# 2. 多重共线性诊断 (VIF) (继承原始代码)
# ==========================================
print("\n" + "="*30)
print(" 步骤 2: 多重共线性诊断 (VIF)")
print("="*30)

X_vif = sm.add_constant(X)
vif_data = pd.DataFrame()
vif_data["Variable"] = X_vif.columns
vif_data["VIF"] = [variance_inflation_factor(X_vif.values, i) for i in range(X_vif.shape[1])]

vif_data = vif_data[vif_data["Variable"] != "const"].sort_values(by="VIF", ascending=False)
vif_output_path = os.path.join(output_dir_data, "VIF_Results_Full.xlsx")
vif_data.to_excel(vif_output_path, index=False)
print(f"-> VIF 结果 (Top 5):\n{vif_data.head(5)}")
print(f"-> 全变量 VIF 结果已保存至: {vif_output_path}")

# ==========================================
# 3. 训练模型与精度评估 (继承原始代码)
# ==========================================
print("\n" + "="*30)
print(" 步骤 3: 训练随机森林模型")
print("="*30)
print(f" 有效样本量: {len(df_clean)} | 纳入特征总数: {len(all_features)}")

# 参考绘图代码建议，添加 n_jobs=-1 加速计算
rf_model = RandomForestRegressor(n_estimators=1000, max_depth=15, min_samples_leaf=2, random_state=42, oob_score=True, n_jobs=-1)
rf_model.fit(X, y)

y_pred = rf_model.predict(X)
oob_r2 = rf_model.oob_score_
print(f"-> 模型训练完成。OOB R²: {oob_r2:.4f}, 训练集 R²: {r2_score(y, y_pred):.4f}")

# ==========================================
# 4. 计算 SHAP 值 (继承原始代码)
# ==========================================
print("\n" + "="*30)
print(" 步骤 4: 计算 SHAP 值")
print("="*30)
explainer = shap.TreeExplainer(rf_model)
# 注意：直接传入标准化后的X
shap_values_array = explainer.shap_values(X)
# 创建 Explanation 对象，用于 summary_plot
shap_explanation = explainer(X)

# ==========================================
# 5. 计算维度贡献度 (继承/修正原始代码逻辑)
# ==========================================
print("\n" + "="*30)
print(" 步骤 5: 计算相对重要性与维度贡献")
print("="*30)

# 计算单个变量的 Mean(|SHAP|)
shap_abs_mean = np.mean(np.abs(shap_values_array), axis=0)
importance_df = pd.DataFrame({'Variable': X.columns, 'Importance': shap_abs_mean})
total_global_impact = importance_df['Importance'].sum()

# 构建分组导出列表
group_results = []
groups_data = [
    ('1_Baseline Development', layer1_baseline), 
    ('2_Spatial & Natural', layer2_spatial), 
    ('3_Policy & Intervention', layer3_policy)
]

for group_name, group_vars in groups_data:
    valid_vars = [v for v in group_vars if v in X.columns]
    group_imp = importance_df[importance_df['Variable'].isin(valid_vars)]['Importance'].sum()
    group_pct = (group_imp / total_global_impact) * 100
    
    group_results.append({
        'Group_Name': group_name,
        'Total_Importance': group_imp,
        'Contribution_Percentage(%)': group_pct,
        'Variables': valid_vars # 保留列表供绘图使用
    })

# --- 打印并导出组别结论 ---
print(" 🏆 三大维度驱动力占比:")
for res in group_results:
    print(f" - {res['Group_Name']}: {res['Contribution_Percentage(%)']:.2f}%")

group_df = pd.DataFrame(group_results)
group_df_export = group_df.copy()
group_df_export['Included_Variables'] = group_df_export['Variables'].apply(lambda x: ", ".join(x))
group_output_path = os.path.join(output_dir_data, "Group_Importance_Results.xlsx")
group_df_export.drop(columns=['Variables']).to_excel(group_output_path, index=False)

# --- 导出所有单个变量的贡献结果 ---
importance_df['Contribution_Percentage(%)'] = (importance_df['Importance'] / total_global_impact) * 100
importance_df = importance_df.sort_values(by='Importance', ascending=False)
importance_output_path = os.path.join(output_dir_data, "SHAP_Importance_Results_Full.xlsx")
importance_df.to_excel(importance_output_path, index=False)


# ==========================================
# 6. 高级组合绘图 (参考绘图代码实现)
# ==========================================
print("\n" + "="*30)
print(" 步骤 6: 绘制 SHAP 组合图 (参考参考代码布局)")
print("="*30)

# 绘图配置 (参考代码设定)
SELECTED_COLOR_SCHEME = 'coolwarm' # 选择 coolwarm 配色
CMAP_BASE = plt.cm.get_cmap(SELECTED_COLOR_SCHEME)
MAX_DISPLAY = 15 # 图中展示前15个变量，避免拥挤

# 定义组别的固定配色 (用于条形图和玫瑰图内部)
group_colors_map = {
    'Baseline': '#4e79a7', # 莫兰迪蓝
    'Spatial': '#59a14f',  # 莫兰迪绿
    'Policy': '#edc948'   # 莫兰迪黄
}

def plot_shap_combined(X_df, shap_values, explanation, importance_df, group_results, feature_group_map, save_path):
    """
    创建一个复杂的自定义组合图：左侧嵌入玫瑰图的条形图，右侧对齐的蜂群图。
    """
    # 1. 数据准备 (用于条形图和蜂群图排序)
    top_df = importance_df.head(MAX_DISPLAY).copy()
    sorted_features = top_df['Variable'].tolist()
    sorted_idx = [X_df.columns.get_loc(f) for f in sorted_features]
    
    # 准备条形图颜色 (根据变量所在组)
    bar_colors = [group_colors_map[feature_group_map[f]] for f in sorted_features]
    
    # 2. 创建画布
    fig = plt.figure(figsize=(22, 12)) # 宽幅画布

    # 全局坐标参数 (Normalized 0-1)
    plot_bottom = 0.1
    plot_height = 0.8
    space_between = 0.04
    
    # 3. 计算坐标轴位置 (精细控制)
    # [left, bottom, width, height]
    # A. 中央条形图 (Bar Plot) - 作为核心基准
    bar_width = 0.25
    bar_left = 0.38 
    ax_bar = fig.add_axes([bar_left, plot_bottom, bar_width, plot_height])
    
    # B. 嵌入式玫瑰图 (Radial Inset) - 放在条形图左侧偏下的位置
    radial_size = 0.32 # 稍微大一点
    radial_left = bar_left - radial_size + 0.05
    radial_bottom = plot_bottom + 0.05
    # 创建极坐标系轴
    ax_radial = fig.add_axes([radial_left, radial_bottom, radial_size, radial_size], projection='polar')

    # C. 右侧蜂窝图 (Beeswarm Plot)
    beeswarm_left = bar_left + bar_width + space_between
    beeswarm_width = 0.32
    ax_beeswarm = fig.add_axes([beeswarm_left, plot_bottom, beeswarm_width, plot_height])

    # D. Colorbar for Beeswarm
    cbar_width = 0.01
    cbar_left = beeswarm_left + beeswarm_width + 0.01
    ax_cbar = fig.add_axes([cbar_left, plot_bottom + plot_height*0.2, cbar_width, plot_height*0.6])

    # ---绘图开始---

    print(" -> 绘制中央条形图与维度配色...")
    # --- A. 中央条形图 (ax_bar) ---
    y_pos = np.arange(len(sorted_features))
    ax_bar.barh(y_pos, top_df['Importance'], color=bar_colors, height=0.7, edgecolor='none', alpha=0.9)
    
    # 设置条形图样式 (参考代码要求)
    ax_bar.set_yticks(y_pos)
    ax_bar.set_yticklabels(sorted_features, fontsize=16)
    ax_bar.invert_yaxis() # 顶部显示最重要的
    ax_bar.set_xlabel('Mean(|SHAP Value|) - Relative Importance', fontsize=18, labelpad=10)
    
    # 修改边框粗细 (参考代码 linewidth=3)
    ax_bar.spines['left'].set_visible(False)
    ax_bar.spines['top'].set_visible(False)
    ax_bar.spines['right'].set_linewidth(3)
    ax_bar.spines['bottom'].set_linewidth(3)
    ax_bar.tick_params(axis='x', labelsize=16, direction='in', length=6, width=2)
    ax_bar.tick_params(axis='y', length=0) # 隐藏y轴刻度线，保留标签
    
    # 添加网格线
    ax_bar.grid(axis='x', linestyle='--', alpha=0.5)

    print(" -> 绘制嵌入式维度玫瑰图...")
    # --- B. 嵌入式玫瑰图 (ax_radial) ---
    num_groups = len(group_results)
    # 计算角度 (N启, 顺时针)
    angles = np.linspace(0, 2 * np.pi, num_groups, endpoint=False)
    widths = np.diff(angles, append=2*np.pi) # 每个扇形的宽度
    
    percentages = [res['Contribution_Percentage(%)'] for res in group_results]
    # 清简组名供显示
    group_labels_clean = [res['Group_Name'].split('_')[-1] for res in group_results]
    # 玫瑰图内部配色 (与条形图组别一致)
    radial_inner_colors = [group_colors_map[res['Group_Name'].split('_')[-1].split(' ')[0]] for res in group_results]

    # 绘制基础环 (高度代表百分比)
    bars = ax_radial.bar(angles, percentages, width=widths, bottom=0.0, 
                          color=radial_inner_colors, alpha=0.8, edgecolor='white', linewidth=2, align='edge')
    
    # 设置极坐标系样式
    ax_radial.set_theta_zero_location('N') # 北点为0
    ax_radial.set_theta_direction(-1)      # 顺时针
    ax_radial.set_yticklabels([])          # 隐藏径向刻度
    ax_radial.set_xticklabels([])          # 隐藏角度刻度
    ax_radial.spines['polar'].set_visible(False) # 隐藏外圈
    ax_radial.grid(False)
    
    # 玫瑰图中心添加标题
    ax_radial.text(0, 0, 'Dimension\nContrib.', ha='center', va='center', fontsize=14, fontweight='bold')

    # 添加百分比和组名标签
    for angle, p, label, w, res in zip(angles, percentages, group_labels_clean, widths, group_results):
        # 计算标签位置 (扇形中间)
        label_angle = angle + w/2
        # 放置百分比
        ax_radial.text(label_angle, p + 5, f'{p:.1f}%', ha='center', va='center', fontsize=14, fontweight='bold')
        # 放置组名 (稍微远一点)
        ax_radial.text(label_angle, p + 25, label, ha='center', va='center', fontsize=13, color='black')

    # 添加玫瑰图标题
    ax_bar.text(-0.8, 0.45, 'Dimension Driver\nContribution (Rose Plot)', transform=ax_bar.transAxes, 
                fontsize=16, fontweight='bold', ha='center', va='center', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

    print(" -> 绘制右侧SHAP蜂群图...")
    # --- C. 右侧蜂窝图 (ax_beeswarm) ---
    plt.sca(ax_beeswarm) # 切换当前Axes
    
    # 必须对 एक्सप्लेनेशन 数据进行排序，使其与条形图y轴对齐
    # 提取排序后的SHAP值矩阵和数据矩阵
    shap_values_sorted = shap_values[:, sorted_idx]
    X_data_sorted = X_df.iloc[:, sorted_idx]
    
    # 使用 shap 自带函数绘制，show=False
 # 使用 shap 自带函数绘制，show=False
    shap.summary_plot(
        shap_values_sorted, 
        X_data_sorted, 
        plot_type="dot", 
        cmap=CMAP_BASE,     # 【修正1】点图使用 cmap 而不是 color
        max_display=MAX_DISPLAY, 
        show=False, 
        plot_size=None,     # 由 axes 控制
        color_bar=False     # 【修正2】改为带下划线的 color_bar
    )
 
    # 设置蜂群图样式
    ax_beeswarm.set_yticklabels([]) # 隐藏y轴标签（已在条形图显示）
    ax_beeswarm.set_ylabel('')
    ax_beeswarm.set_xlabel("SHAP Value (Impact on SDG total)", fontsize=18, labelpad=10)
    ax_beeswarm.invert_yaxis() # 必须反转，与条形图对齐
    
    ax_beeswarm.spines['left'].set_visible(False)
    ax_beeswarm.spines['top'].set_visible(False)
    ax_beeswarm.spines['right'].set_visible(False)
    ax_beeswarm.spines['bottom'].set_linewidth(3)
    ax_beeswarm.tick_params(axis='x', labelsize=16, direction='in', length=6, width=2)
    ax_beeswarm.set_xlim(ax_beeswarm.get_xlim()) # 锁定xlim

    # --- D. 手动添加 Colorbar ---
    m = ScalarMappable(cmap=CMAP_BASE)
    m.set_array([0, 1]) # 归一化特征值
    cb = fig.colorbar(m, cax=ax_cbar, ticks=[0, 1])
    cb.set_label('Feature Value', size=16, labelpad=-10)
    cb.ax.set_yticklabels(['Low', 'High'], fontsize=14)
    cb.outline.set_visible(False) # 隐藏Colorbar边框

    # --- 组合图大标题 ---
    fig.suptitle('Drivers of SDG Heterogeneity: Group Contribution & Feature Impact', 
                 fontsize=26, fontweight='bold', y=0.96)

    # 保存图形
    print(f" -> 正在保存组合图至: {save_path} ...")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

# 执行绘图
final_fig_path = os.path.join(output_dir_fig, "shap组合图.jpg")
plot_shap_combined(X, shap_values_array, shap_explanation, importance_df, group_results, feature_group_map, final_fig_path)

print("\n🏆 工作完成！")
print(f"✅ 相对重要性数据结果保存在: {output_dir_data}")
print(f"✅ 高级SHAP组合图保存在: {final_fig_path}")