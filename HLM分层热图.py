import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os

# ==========================================
# 1. 路径与环境配置
# ==========================================
input_path = r"D:\1sdgplanning\1data\HLM\HLM_Grouped_Results.csv"
output_dir = r"D:\1sdgplanning\5fig"
os.makedirs(output_dir, exist_ok=True)

# 设置字体，防止某些系统下中文乱码
plt.rcParams['font.sans-serif'] = ['Arial'] 
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 2. 读取数据并解析嵌套结构
# ==========================================
df_raw = pd.read_csv(input_path)
sdg_cols = [col for col in df_raw.columns if 'SDG' in str(col).upper()]

parsed_rows = []
current_layer = "City Level" 
current_category = "Unknown" 

for idx, row in df_raw.iterrows():
    col0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
    col1 = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
    
    # 识别大层级表头
    if ("Level" in col0 or "Provincial" in col0) and col1 == "" and pd.isna(row.get(sdg_cols[0], np.nan)):
        current_layer = col0
        continue
        
    # 识别截距或统计量行
    if col0 != "" and col1 == "":
        parsed_rows.append({
            'Layer': current_layer,
            'Category': 'Stats',
            'Variable': col0,
            **{col: row[col] for col in sdg_cols}
        })
        continue

    # 正常的变量行，识别类别
    if col0 != "": 
        current_category = col0
        
    if col1 != "": # 确保有变量名才记录
        parsed_rows.append({
            'Layer': current_layer,
            'Category': current_category,
            'Variable': col1,
            **{col: row[col] for col in sdg_cols}
        })

df = pd.DataFrame(parsed_rows)
# 过滤掉截距和统计量行，只保留变量
df_vars = df[df['Category'] != 'Stats'].copy()

# ==========================================
# 3. 数据清洗函数
# ==========================================
def extract_num(val):
    if pd.isna(val) or str(val).strip() == "": return np.nan
    val_str = str(val).strip()
    num_str = re.sub(r'[^\d\.\-]', '', val_str)
    try:
        return float(num_str) if num_str else np.nan
    except ValueError:
        return np.nan

def extract_stars(val):
    if pd.isna(val): return ""
    return "".join(re.findall(r'\*', str(val)))

# ==========================================
# 4. 构建用于绘图的矩阵
# ==========================================
variables_list = df_vars['Variable'].tolist()
data_matrix = np.zeros((len(df_vars), len(sdg_cols)))
annot_matrix = np.empty((len(df_vars), len(sdg_cols)), dtype=object)

for i, (idx, row) in enumerate(df_vars.iterrows()):
    for j, col in enumerate(sdg_cols):
        raw_val = row[col]
        num = extract_num(raw_val)
        stars = extract_stars(raw_val)
        
        data_matrix[i, j] = num if pd.notna(num) else np.nan
        if pd.notna(num):
            annot_matrix[i, j] = f"{num:.3f}\n{stars}" if stars else f"{num:.3f}"
        else:
            annot_matrix[i, j] = ""

# ==========================================
# 5. 绘制组合分层热图
# ==========================================
fig, ax = plt.subplots(figsize=(18, 16)) # 增加图幅高度以适应所有变量
cmap = sns.diverging_palette(240, 10, as_cmap=True)

sns.heatmap(data_matrix, cmap=cmap, center=0, 
            annot=annot_matrix, fmt="", annot_kws={"size": 9},
            xticklabels=sdg_cols, yticklabels=variables_list,
            linewidths=0.5, linecolor='lightgray', 
            cbar_kws={'label': 'Coefficient Value', 'shrink': 0.7, 'pad': 0.02},
            robust=True, ax=ax)

# ==========================================
# 6. 添加左侧嵌套分组线和标签 (双重分组)
# ==========================================
current_y = 0
layer_bounds = {}
cat_bounds = {}

# 计算层级和分类的边界索引
for layer, group_layer in df_vars.groupby('Layer', sort=False):
    layer_start = current_y
    for cat, group_cat in group_layer.groupby('Category', sort=False):
        cat_start = current_y
        cat_len = len(group_cat)
        current_y += cat_len
        cat_bounds[(layer, cat)] = (cat_start, current_y)
    layer_bounds[layer] = (layer_start, current_y)

# 绘制 Category（子类）级别的分割线和文字
for (layer, cat), (start, end) in cat_bounds.items():
    if start > 0 and start not in [v[0] for v in layer_bounds.values()]:
        # 画子类的细灰色分割线
        ax.axhline(start, color='gray', linewidth=1, linestyle='--')
    center = (start + end) / 2
    # 添加子类文字（在 Y 轴左侧）
    ax.text(-0.5, center, cat, va='center', ha='right', fontsize=12, clip_on=False)

# 绘制 Layer（大类）级别的分割线和文字
for layer, (start, end) in layer_bounds.items():
    if start > 0:
        # 画大类的粗黑色分割线
        ax.axhline(start, color='black', linewidth=2.5)
    center = (start + end) / 2
    # 添加大类文字（在更左侧）
    ax.text(-2.5, center, layer, va='center', ha='right', fontsize=14, fontweight='bold', clip_on=False)

# ==========================================
# 7. 图表修饰与输出保存
# ==========================================
plt.title('Estimated Coefficients across SDGs (City & Provincial Levels)', fontsize=18, pad=20, fontweight='bold')
plt.xlabel('Sustainable Development Goals (SDGs)', fontsize=14, labelpad=10)
plt.ylabel('') 
plt.xticks(rotation=45, ha='right', fontsize=11)
plt.yticks(fontsize=11)

# 调整左侧边缘距，给两层分组文本留出充足空间
plt.subplots_adjust(left=0.28, bottom=0.1) 

output_file = os.path.join(output_dir, "Heatmap_Combined_Hierarchical.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()

print(f"组合分层热图已成功生成并保存：{output_file}")