import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# ==
# 0. 全局字体设置 (关键步骤)
# ==
# 设置全局字体为 Times New Roman (Nature系列常用)
plt.rcParams['font.family'] = 'arial'
plt.rcParams['font.size'] = 12  # 全局基础字号

# 1. 读取数据
df = pd.read_csv(r'C:\Users\zgy\Desktop\18.csv')
df_numeric = df.select_dtypes(include=[np.number])

# ==
# 图 1: 绝对强度图 (Map A)
# ==

# 自定义柔和色系
colors = ["#ffffff", "#fee5d9", "#fcae91", "#fb6a4a", "#de2d26", "#a50f15"]
nodes = [0.0, 0.45, 0.6, 0.75, 0.9, 1.0]
custom_cmap = mcolors.LinearSegmentedColormap.from_list("soft_reds", list(zip(nodes, colors)))

corr_abs = df_numeric.corr()

plt.figure(figsize=(11, 9))
ax = sns.heatmap(
    corr_abs,
    cmap=custom_cmap,
    annot=True,
    fmt=".2f",
    vmin=0.5, vmax=1.0,
    center=None,
    square=True,
    linewidths=.5,
    cbar_kws={"label": "Pearson Correlation ($r$)"},
    mask=np.triu(np.ones_like(corr_abs, dtype=bool)),

    # 【字体调整 1】格子里的数值字体
    annot_kws={"size": 10, "fontfamily": "arial"}
)

# 【字体调整 2】标题字体
plt.title("Map A: Absolute Integration Intensity (Universal Synergy)",
          fontsize=16, fontweight='bold', fontfamily='arial', pad=20)

# 【字体调整 3】坐标轴标签字体
plt.xticks(fontsize=12, fontfamily='arial', rotation=45, ha='right')
plt.yticks(fontsize=12, fontfamily='arial', rotation=0)

# 【字体调整 4】Colorbar (图例) 字体
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=10)  # 刻度字体
cbar.set_label("Pearson Correlation ($r$)", fontsize=12, fontfamily='arial')  # 标签字体

plt.tight_layout()
plt.savefig("Map_A_Soft_Font.pdf", dpi=300)
plt.show()

# ==
# 图 2: 相对比例图 (Map B)
# ==

df_percent = df_numeric.div(df_numeric.sum(axis=1), axis=0)
corr_rel = df_percent.corr()

plt.figure(figsize=(11, 9))
ax = sns.heatmap(
    corr_rel,
    cmap='RdBu_r',
    annot=True,
    fmt=".2f",
    center=0,
    vmin=-0.6, vmax=0.6,
    square=True,
    linewidths=.5,
    cbar_kws={"label": "Relative Correlation ($r_{rel}$)"},
    mask=np.triu(np.ones_like(corr_rel, dtype=bool)),

    # 【字体调整 1】格子里的数值字体
    annot_kws={"size": 10, "fontfamily": "arial"}
)

# 【字体调整 2】标题字体
plt.title("Map B: Relative Strategic Priority (Hidden Trade-offs)",
          fontsize=16, fontweight='bold', fontfamily='arial', pad=20)

# 【字体调整 3】坐标轴标签字体
plt.xticks(fontsize=12, fontfamily='arial', rotation=45, ha='right')
plt.yticks(fontsize=12, fontfamily='arial', rotation=0)

# 【字体调整 4】Colorbar (图例) 字体
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=10)
cbar.set_label("Relative Correlation ($r_{rel}$)", fontsize=12, fontfamily='arial')

plt.tight_layout()
plt.savefig("Map_B_Tradeoffs_Font.pdf", dpi=300)
plt.show()