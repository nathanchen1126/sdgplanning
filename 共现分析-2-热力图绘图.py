import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap

# ==========================================
# 1. 全局参数与路径设置
# ==========================================
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.weight'] = 'normal'
plt.rcParams['axes.labelweight'] = 'normal'

input_file = r"D:\1sdgplanning\1data\sdg_statistical_edges_top3.xlsx"
output_folder = r"D:\1sdgplanning\5fig"
os.makedirs(output_folder, exist_ok=True)

# ==========================================
# 2. 读取与处理数据
# ==========================================
df = pd.read_excel(input_file)

sdgs = set(df['Source']).union(set(df['Target']))
sdg_order = sorted(list(sdgs), key=lambda x: int(x.replace('sdg', '')))
n = len(sdg_order)

oi_mat = pd.DataFrame(np.nan, index=sdg_order, columns=sdg_order)
p_mat = pd.DataFrame(1.0, index=sdg_order, columns=sdg_order)
k_mat = pd.DataFrame(np.nan, index=sdg_order, columns=sdg_order)

for _, row in df.iterrows():
    s, t = row['Source'], row['Target']
    oi, p, k = row['Overlap_Index(OI)'], row['P_Value'], row['Observed_Co_occur(k)']
    oi_mat.loc[s, t] = oi
    oi_mat.loc[t, s] = oi
    p_mat.loc[s, t] = p
    p_mat.loc[t, s] = p
    k_mat.loc[s, t] = k
    k_mat.loc[t, s] = k

# ==========================================
# 3. 构建偏差矩阵（红白蓝配色）
# ==========================================
dev_mat = oi_mat   # 偏差 = overlap index（如你需要可换成其他矩阵）

max_abs = np.nanmax(np.abs(dev_mat.values))
if max_abs == 0 or np.isnan(max_abs):
    max_abs = 1e-6  # 防止全 0 情况

vmax = max_abs
vmin = -max_abs

# 黄 = 预期以下；白 = 无偏差；蓝 = 预期以上
rwb_colors = ["#e5c796", "#ffffff", "#4c98a3"] 
rwb_cmap = LinearSegmentedColormap.from_list("rwb_cmap", rwb_colors, N=256)
rwb_cmap.set_bad(color="white")

mask = np.triu(np.ones_like(dev_mat, dtype=bool))

# ==========================================
# 4. 绘制下三角热力图
# ==========================================
fig, ax = plt.subplots(figsize=(12, 10))

# 1. 先关闭自动 colorbar
hm = sns.heatmap(
    dev_mat,
    mask=mask,
    cmap=rwb_cmap,
    vmin=vmin,
    vmax=vmax,
    center=0,
    annot=k_mat,
    fmt='g',
    annot_kws={'size': 11, 'family': 'Arial'},
    linewidths=0,
    cbar=False,  # ← 关闭自动 colorbar
    square=True,
    ax=ax
)

# 2. 手动添加 colorbar 并精确控制位置与宽度
# [left, bottom, width, height]
# left = 0.35 和 width = 0.30 保证了它居中占全图宽度的30% (0.35 + 0.30/2 = 0.5)
# bottom = 0.05 将其放在全图最下方
cax = fig.add_axes([0.35, 0.05, 0.30, 0.02]) 

cbar = fig.colorbar(
    hm.collections[0], 
    cax=cax, 
    orientation='horizontal' # ← 设置为横向
)
cbar.set_label('Overlap Index', fontsize=12)
cbar.ax.tick_params(labelsize=11)

ax.set_facecolor("white")

# ==========================================
# 5. 在下三角加入浅灰网格 + 黑框 + 斜线
# ==========================================
for i in range(n):
    for j in range(n):
        if i <= j:
            continue

        val_oi = oi_mat.iloc[i, j]
        val_p = p_mat.iloc[i, j]

        # 浅灰网格
        rect_light = patches.Rectangle(
            (j, i), 1, 1,
            fill=False, edgecolor='0.85', linewidth=0.5
        )
        ax.add_patch(rect_light)

        # 强偏差关系：黑色边框
        if not pd.isna(val_oi) and abs(val_oi) > 0.1:
            rect = patches.Rectangle(
                (j, i), 1, 1,
                fill=False, edgecolor='black', linewidth=3.5
            )
            ax.add_patch(rect)

        # 不显著：画斜线
        if not pd.isna(val_p) and val_p >= 0.05:
            ax.plot([j, j + 1], [i, i + 1], color='dimgray', lw=1.5)

# ==========================================
# 6. 美化外观并保存
# ==========================================
plt.xticks(rotation=45, ha='right', fontsize=12)
plt.yticks(rotation=0, fontsize=12)
ax.set_xlabel("")
ax.set_ylabel("")

# （已删除原始代码中冗余的 cbar 设置逻辑）

# 调整主图布局，为底部的横向图例腾出空间
# rect=[left, bottom, right, top]，让主图底部从全图高度的 12% 处开始，防止与图例重叠
plt.tight_layout(rect=[0, 0.12, 1, 1])

output_path = os.path.join(output_folder, 'sdg_cooccurrence_heatmap_henxiang.eps')
plt.savefig(output_path, dpi=300, bbox_inches='tight')

print("==================================================")
print(f"✅ 完整热力图已生成：\n {output_path}")
print("==================================================")

plt.show()