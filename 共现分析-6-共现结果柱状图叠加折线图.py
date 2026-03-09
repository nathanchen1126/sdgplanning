# -*- coding: utf-8 -*-
"""
柱状图(共现频次 Total Co-occurrences) + 折线图(Synergies / Trade-offs)；
按 Total Co-occurrences 从大到小排序的 SDG 作为 x 轴；
Total Co-occurrences 数值跨度大 -> 采用“断轴”(broken y-axis)避免柱子差距过大。
输出图片保存到 D:\1sdgplanning\5fig

运行环境若不是 Windows：请把 input_path 改成实际可访问路径（例如 /mnt/data/sdg_共现结果总结_summary.xlsx）。
"""

import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# 路径配置
# -----------------------------
input_path = r"D:\1sdgplanning\1data\sdg_共现结果总结_summary.xlsx"
# 如果你在类似 Linux/Jupyter 环境运行，可能文件实际在这里（按需启用）
fallback_input_path = r"/mnt/data/sdg_共现结果总结_summary.xlsx"

out_dir = r"D:\1sdgplanning\5fig"
out_name = "SDG_TotalCooccurrences_bar_with_Synergies_Tradeoffs_lines_broken_axis.png"
out_path = os.path.join(out_dir, out_name)

os.makedirs(out_dir, exist_ok=True)

if not os.path.exists(input_path):
    if os.path.exists(fallback_input_path):
        input_path = fallback_input_path
    else:
        raise FileNotFoundError(f"未找到输入文件：{input_path}（也未找到：{fallback_input_path}）")

# -----------------------------
# 读取数据
# -----------------------------
df = pd.read_excel(input_path)

# -----------------------------
# 自动识别列名（更鲁棒）
# 期望列：SDG, Total Co-occurrences, Synergies, Trade-offs
# -----------------------------
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().lower()

cols = list(df.columns)
norm_map = {_norm(c): c for c in cols}

def pick_col(candidates):
    """
    candidates: list of (must_contain_substrings: list[str])
    按优先级从 candidates 里匹配列名
    """
    norm_cols = list(norm_map.keys())
    for musts in candidates:
        for nc in norm_cols:
            ok = True
            for m in musts:
                if m not in nc:
                    ok = False
                    break
            if ok:
                return norm_map[nc]
    return None

sdg_col = pick_col([
    ["sdg"],
    ["目标"],        # 可能是中文
    ["goal"],
])

total_col = pick_col([
    ["total", "co"],
    ["total", "occ"],
    ["co-occ"],     # co-occurrences
    ["coocc"],
    ["共现", "总"],  # 中文可能：总共现
    ["共现", "频"],  # 共现频次
    ["共现"],       # 最后兜底：只要包含“共现”
])

syn_col = pick_col([
    ["synergies"],
    ["synergy"],
    ["协同"],       # 中文可能
])

trade_col = pick_col([
    ["trade-offs"],
    ["tradeoffs"],
    ["trade", "off"],
    ["权衡"],       # 中文可能
])

missing = [("SDG", sdg_col), ("Total Co-occurrences", total_col),
           ("Synergies", syn_col), ("Trade-offs", trade_col)]
missing = [name for name, col in missing if col is None]
if missing:
    raise ValueError(
        "无法自动识别以下必要列名："
        + ", ".join(missing)
        + "\n当前表头为："
        + ", ".join(map(str, df.columns))
        + "\n请手动把上面变量 sdg_col/total_col/syn_col/trade_col 改成正确列名。"
    )

# 只保留需要列，清洗数值
plot_df = df[[sdg_col, total_col, syn_col, trade_col]].copy()
plot_df = plot_df.rename(columns={
    sdg_col: "SDG",
    total_col: "Total Co-occurrences",
    syn_col: "Synergies",
    trade_col: "Trade-offs"
})

for c in ["Total Co-occurrences", "Synergies", "Trade-offs"]:
    plot_df[c] = pd.to_numeric(plot_df[c], errors="coerce")

plot_df = plot_df.dropna(subset=["SDG", "Total Co-occurrences", "Synergies", "Trade-offs"])
plot_df["SDG"] = plot_df["SDG"].astype(str)

# 排序：Total Co-occurrences 从大到小
plot_df = plot_df.sort_values("Total Co-occurrences", ascending=False).reset_index(drop=True)

x = np.arange(len(plot_df))
sdg_labels = plot_df["SDG"].tolist()
total_vals = plot_df["Total Co-occurrences"].to_numpy(dtype=float)
syn_vals = plot_df["Synergies"].to_numpy(dtype=float)
trade_vals = plot_df["Trade-offs"].to_numpy(dtype=float)

# -----------------------------
# 自动选择断轴阈值（基于“最大相邻落差”）
# 适合 SDG 类别数不多（~17）且头部很大、尾部很小的情况
# -----------------------------
sorted_vals = total_vals.copy()
# total_vals 已经降序了
eps = 1e-9
ratios = (sorted_vals[:-1] + eps) / (sorted_vals[1:] + eps)
if len(ratios) > 0:
    idx = int(np.argmax(ratios))  # 在 idx 和 idx+1 之间断开
    # 如果并没有明显断层，仍给一个合理阈值
    if ratios[idx] < 3:  # 落差不够大就不强行断轴（改用温和阈值）
        break_low = np.percentile(sorted_vals, 60)
    else:
        break_low = sorted_vals[idx + 1]  # 下段最大值
else:
    break_low = np.max(sorted_vals) * 0.3

# 给上下段留出边距
low_max = max(break_low, np.min(sorted_vals))
high_min = low_max

max_total = float(np.max(total_vals))
min_total = float(np.min(total_vals))

# 下段 ylim：0 ~ low_max*(1+margin)
low_ylim_top = low_max * 1.15 if low_max > 0 else 1.0
# 上段 ylim：high_min*(1-margin) ~ max_total*(1+margin)
high_ylim_bottom = max(high_min * 0.85, low_ylim_top * 1.05)  # 确保上下段不重叠
high_ylim_top = max_total * 1.05

# 如果自动阈值导致不合理（例如 low 段过大），做个兜底
if high_ylim_bottom >= high_ylim_top:
    high_ylim_bottom = max_total * 0.6
if low_ylim_top >= high_ylim_bottom:
    low_ylim_top = high_ylim_bottom * 0.4

# -----------------------------
# 绘图（断轴：上下两个子图共享 x）
# -----------------------------
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig = plt.figure(figsize=(16, 8))
gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.2], hspace=0.05)

ax_top = fig.add_subplot(gs[0, 0])
ax_bot = fig.add_subplot(gs[1, 0], sharex=ax_top)

bar_width = 0.75

# 柱状图：两个轴都画（这样看起来是“断开的同一组柱子”）
ax_top.bar(x, total_vals, width=bar_width)
ax_bot.bar(x, total_vals, width=bar_width)

# 断轴 y 范围
ax_top.set_ylim(high_ylim_bottom, high_ylim_top)
ax_bot.set_ylim(0, low_ylim_top)

# 折线：右轴（为了断轴效果一致，两边都画线；但只在下图显示右轴刻度）
ax_top_r = ax_top.twinx()
ax_bot_r = ax_bot.twinx()

# 右轴范围
max_right = float(np.max([np.max(syn_vals), np.max(trade_vals)]))
ax_top_r.set_ylim(0, max_right * 1.15 if max_right > 0 else 1.0)
ax_bot_r.set_ylim(0, max_right * 1.15 if max_right > 0 else 1.0)

# 折线（不指定颜色，让 matplotlib 自动分配）
ax_top_r.plot(x, syn_vals, marker="o", linewidth=2, label="Synergies")
ax_top_r.plot(x, trade_vals, marker="o", linewidth=2, label="Trade-offs")

ax_bot_r.plot(x, syn_vals, marker="o", linewidth=2, label="Synergies")
ax_bot_r.plot(x, trade_vals, marker="o", linewidth=2, label="Trade-offs")

# 只显示下图右轴刻度/标签，避免重复
ax_top_r.tick_params(labelright=False, right=False)
ax_top_r.spines["right"].set_visible(False)

# 隐藏上图 x 轴刻度标签
plt.setp(ax_top.get_xticklabels(), visible=False)

# x 轴标签
ax_bot.set_xticks(x)
ax_bot.set_xticklabels(sdg_labels, rotation=45, ha="right")

# 轴标签
ax_bot.set_xlabel("SDG (sorted by Total Co-occurrences)")
ax_bot.set_ylabel("Total Co-occurrences (count)")
ax_bot_r.set_ylabel("Synergies / Trade-offs (count)")

# 断轴标记（斜杠）
d = 0.008  # size of diagonal lines
kwargs = dict(transform=ax_top.transAxes, color="k", clip_on=False, linewidth=1.2)
ax_top.plot((-d, +d), (-d, +d), **kwargs)        # top-left
ax_top.plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right

kwargs.update(transform=ax_bot.transAxes)
ax_bot.plot((-d, +d), (1 - d, 1 + d), **kwargs)        # bottom-left
ax_bot.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right

# 标题
fig.suptitle("SDG Co-occurrences (bar) with Synergies & Trade-offs (lines) — Broken Y-axis", y=0.98)

# 图例（放在下图右轴，合并两条线）
handles, labels = ax_bot_r.get_legend_handles_labels()
ax_bot_r.legend(handles, labels, loc="upper right", frameon=True)

# 网格（可选：只对柱状轴加水平网格）
ax_top.grid(True, axis="y", linestyle="--", alpha=0.3)
ax_bot.grid(True, axis="y", linestyle="--", alpha=0.3)

# 边距
fig.tight_layout(rect=[0, 0, 1, 0.96])

# 保存
fig.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close(fig)

print(f"已保存：{out_path}")