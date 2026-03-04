import pandas as pd

# 1. 设置输入和输出路径
input_file = r"D:\1sdgplanning\1data\sdg_statistical_edges_top3.xlsx"
output_file = r"D:\1sdgplanning\1data\sdg_共现结果总结_summary.xlsx"

# 2. 读取数据
df = pd.read_excel(input_file)

# 3. 提取所有唯一的 SDG 节点
unique_sdgs = pd.concat([df['Source'], df['Target']]).unique()

# 4. 遍历每个 SDG 并结合显著性条件计算指标
results = []
for sdg in unique_sdgs:
    # 筛选包含当前 SDG 的所有边（Source 或 Target 包含该 SDG）
    sdg_edges = df[(df['Source'] == sdg) | (df['Target'] == sdg)]
    
    # 指标 1：总共现次数
    total_co_occur = sdg_edges['Observed_Co_occur(k)'].sum()
    
    # 指标 2：严格基于统计阈值的显著协同关系数量 (OI > 0.1 且 P < 0.05)
    synergy_count = sdg_edges[
        (sdg_edges['Overlap_Index(OI)'] > 0.1) & 
        (sdg_edges['P_Value'] < 0.05)
    ].shape[0]
    
    # 指标 3：严格基于统计阈值的显著权衡关系数量 (OI < -0.1 且 P < 0.05)
    tradeoff_count = sdg_edges[
        (sdg_edges['Overlap_Index(OI)'] < -0.1) & 
        (sdg_edges['P_Value'] < 0.05)
    ].shape[0]
    
    results.append({
        'SDG': sdg.upper(), # 统一转换为大写，如 SDG11
        '总共现频次 (Total Co-occurrences)': total_co_occur,
        '显著协同数量 (Synergies: OI>0.1, P<0.05)': synergy_count,
        '显著权衡数量 (Trade-offs: OI<-0.1, P<0.05)': tradeoff_count
    })

# 5. 转换为 DataFrame 并按总共现频次降序排列
summary_df = pd.DataFrame(results)
summary_df = summary_df.sort_values(by='总共现频次 (Total Co-occurrences)', ascending=False).reset_index(drop=True)

# 6. 保存计算结果
summary_df.to_excel(output_file, index=False)
print(f"计算完成，结果已保存至：{output_file}")
print("\nSDG 共现网络结构统计概览：")
print(summary_df)