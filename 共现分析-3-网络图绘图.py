import os
import glob
import itertools
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx

plt.rcParams["font.sans-serif"] = ["Arial", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

# ==========================================
# 关键词映射
# ==========================================
keyword_mapping = {
    "安全发展": "Safe Development",
    "安全韧性": "Security Resilience",
    "城乡融合": "Urban-Rural Integration",
    "高质量发展": "High-Quality Development",
    "国土空间安全韧性": "Territorial Spatial Security and Resilience",
    "空间布局": "Spatial Layout",
    "空间底线": "Spatial Baseline",
    "空间规划": "Spatial Planning",
    "空间蓝图": "Spatial Blueprint",
    "绿色低碳": "Green and Low-Carbon",
    "绿色发展": "Green Development",
    "绿色食品": "Green Food",
    "人与自然和谐共生": "Harmonious Coexistence",
    "生态安全": "Ecological Security",
    "生态保护": "Ecological Protection",
    "生态保护修复": "Ecological Protection and Restoration",
    "生态文明": "Ecological Civilization",
    "生态系统": "Ecosystem",
    "统筹发展": "Coordinated Development",
    "文化保护": "Cultural Preservation",
    "优化资源配置": "Optimized Resource Allocation",
    "长江经济带": "Yangtze Economic Belt",
}

cn_keywords = list(keyword_mapping.keys())
en_keywords = list(keyword_mapping.values())
cn2en = keyword_mapping

# ==========================================
# 读取txt统计
# ==========================================
data_dir = r"D:\1sdgplanning\1data\1全部批复"
txt_files = sorted(glob.glob(os.path.join(data_dir, "*.txt")))

def read_text_safely(fp):
    for enc in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
        try:
            with open(fp, "r", encoding=enc) as f:
                return f.read()
        except:
            continue
    with open(fp, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

word_counts_cn = Counter()
doc_counts_cn = Counter()
co_doc_counts_cn = Counter()

for fp in txt_files:
    text = read_text_safely(fp)
    present = []
    for kw in cn_keywords:
        c = text.count(kw)
        if c > 0:
            word_counts_cn[kw] += c
            doc_counts_cn[kw] += 1
            present.append(kw)

    for u, v in itertools.combinations(sorted(set(present)), 2):
        co_doc_counts_cn[(u, v)] += 1

word_counts = {cn2en[k]: word_counts_cn[k] for k in cn_keywords}
doc_counts  = {cn2en[k]: doc_counts_cn[k]  for k in cn_keywords}
co_occurrence_counts = {(cn2en[u], cn2en[v]): c for (u, v), c in co_doc_counts_cn.items()}

# ==========================================
# 构建网络
# ==========================================
G = nx.Graph()
for kw in en_keywords:
    if word_counts[kw] > 0:
        G.add_node(kw, abs_count=word_counts[kw], doc_count=doc_counts[kw])

for (u, v), c in co_occurrence_counts.items():
    if u in G and v in G:
        G.add_edge(u, v, weight=c)

# ==========================================
# 节点大小（绝对次数五档）
# ==========================================
abs_vals = np.array([G.nodes[n]["abs_count"] for n in G.nodes()])
abs_thresholds = np.percentile(abs_vals, [20, 40, 60, 80])
size_levels = [160, 360, 650, 1000, 1400]

def abs_level(x):
    if x <= abs_thresholds[0]: return 0
    if x <= abs_thresholds[1]: return 1
    if x <= abs_thresholds[2]: return 2
    if x <= abs_thresholds[3]: return 3
    return 4

node_sizes = [size_levels[abs_level(G.nodes[n]["abs_count"])] for n in G.nodes()]

# ==========================================
# 文档数量颜色（与热力图rwb协调）
# ==========================================
doc_vals = np.array([G.nodes[n]["doc_count"] for n in G.nodes()])
doc_thresholds = np.percentile(doc_vals, [20, 40, 60, 80])

doc_color_palette = [
    "#e5c796",
    "#f1e3c6",
    "#ffffff",
    "#9cc9cf",
    "#4c98a3",
]

def doc_level(x):
    if x <= doc_thresholds[0]: return 0
    if x <= doc_thresholds[1]: return 1
    if x <= doc_thresholds[2]: return 2
    if x <= doc_thresholds[3]: return 3
    return 4

node_colors = [doc_color_palette[doc_level(G.nodes[n]["doc_count"])] for n in G.nodes()]

# ==========================================
# 边（更紧凑）
# ==========================================
edge_weights = np.array([G[u][v]["weight"] for u, v in G.edges()])
median_w = np.median(edge_weights) if len(edge_weights)>0 else 0
thin_w, thick_w = 0.6, 2.3

weak_edges = [(u, v) for u, v in G.edges() if G[u][v]["weight"] < median_w]
strong_edges = [(u, v) for u, v in G.edges() if G[u][v]["weight"] >= median_w]

# ==========================================
# 绘图（更紧凑布局）
# ==========================================
fig, ax = plt.subplots(figsize=(14, 10), dpi=300)
plt.subplots_adjust(right=0.78)
ax.axis("off")

# 🔥 关键：降低k值，让网络更紧凑
# ====== 1) 换布局：Kamada-Kawai（核心更稳定）======
pos = nx.kamada_kawai_layout(G, weight="weight")

# ====== 2) 只收缩外围：按中心度（closeness）控制收缩强度 ======
# closeness 越大越“中心”，越小越“外围”
clo = nx.closeness_centrality(G)  # {node: 0~1}

# 设定：中心节点几乎不动，外围收缩更明显
# shrink_min: 中心节点的最小收缩（接近1表示基本不动）
# shrink_max: 外围节点的最大收缩（越小越靠近中心）
shrink_min = 0.98
shrink_max = 0.68

# 把中心度归一化到[0,1]（避免极端图导致缩放失真）
vals = np.array(list(clo.values()), dtype=float)
vmin, vmax = vals.min(), vals.max()
den = (vmax - vmin) if (vmax - vmin) > 1e-12 else 1.0

for n in G.nodes():
    t = (clo[n] - vmin) / den      # t越大越中心
    s = shrink_max + (shrink_min - shrink_max) * t  # 中心->接近shrink_min，外围->接近shrink_max
    x, y = pos[n]
    pos[n] = (x * s, y * s)

nx.draw_networkx_edges(G, pos, edgelist=weak_edges, width=thin_w,
                       edge_color="#8C8C8C", alpha=0.4, ax=ax)
nx.draw_networkx_edges(G, pos, edgelist=strong_edges, width=thick_w,
                       edge_color="#8C8C8C", alpha=0.7, ax=ax)

nx.draw_networkx_nodes(G, pos,
                       node_size=node_sizes,
                       node_color=node_colors,
                       edgecolors="#444444",
                       linewidths=0.8,
                       ax=ax)

nx.draw_networkx_labels(G, pos,
                        font_size=10,
                        font_color="#2d2d2d",
                        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", pad=0.3),
                        ax=ax)

# ==========================================
# 图例
# ==========================================

# 1. 大小图例
size_handles = []
for i in range(5):
    ms = np.sqrt(size_levels[i]) * 0.9
    size_handles.append(
        Line2D([0],[0], marker='o', color='w',
               markerfacecolor="#bfbfbf",
               markeredgecolor="white",
               markersize=ms,
               label=f"Level {i+1}")
    )

leg1 = ax.legend(handles=size_handles,
                 title="Absolute Occurrences",
                 loc="upper left",
                 bbox_to_anchor=(0.95,0.90),
                 frameon=False)
ax.add_artist(leg1)

# 2. 颜色图例（改为圆圈！）
color_handles = []
for i in range(5):
    color_handles.append(
        Line2D([0],[0], marker='o', color='w',
               markerfacecolor=doc_color_palette[i],
               markeredgecolor="#444444",
               markersize=10,
               label=f"Level {i+1}")
    )

leg2 = ax.legend(handles=color_handles,
                 title="Document Count",
                 loc="upper left",
                 bbox_to_anchor=(0.95,0.65),
                 frameon=False)
ax.add_artist(leg2)

# 3. 线条图例
edge_handles = [
    Line2D([0],[0], color="#b0b0b0", lw=thick_w,
           label="Strong Co-occurrence"),
    Line2D([0],[0], color="#cfcfcf", lw=thin_w,
           label="Weak Co-occurrence"),
]

leg3 = ax.legend(handles=edge_handles,
                 title="Co-occurrence Strength",
                 loc="upper left",
                 bbox_to_anchor=(0.95,0.45),
                 frameon=False)
ax.add_artist(leg3)

plt.savefig(r"D:\1sdgplanning\5fig\Network_Nature_RWB.eps",
            dpi=300,
            bbox_inches="tight",
            bbox_extra_artists=(leg1,leg2,leg3))
