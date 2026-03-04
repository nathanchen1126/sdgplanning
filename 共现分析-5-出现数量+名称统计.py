import pandas as pd

# 1. 设置输入和输出路径
input_file = r"D:\1sdgplanning\1data\sdg_statistical_edges_top3.xlsx"
output_file = r"D:\1sdgplanning\1data\sdg_共现结果+名称总结_summary.xlsx"

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
    
    # --- 计算协同关系 ---
    # 筛选严格基于统计阈值的显著协同关系边 (OI > 0.1 且 P < 0.05)
    synergy_edges = sdg_edges[
        (sdg_edges['Overlap_Index(OI)'] > 0.1) & 
        (sdg_edges['P_Value'] < 0.05)
    ]
    
    synergy_sdgs = []
    # 遍历协同边，找到与当前 sdg 相连接的另一个节点
    for _, row in synergy_edges.iterrows():
        other_node = row['Target'] if row['Source'] == sdg else row['Source']
        synergy_sdgs.append(other_node.upper())
        
    synergy_count = len(synergy_sdgs)
    synergy_str = ", ".join(synergy_sdgs) # 将列表转为逗号分隔的字符串
    
    # --- 计算权衡关系 ---
    # 筛选严格基于统计阈值的显著权衡关系边 (OI < -0.1 且 P < 0.05)
    tradeoff_edges = sdg_edges[
        (sdg_edges['Overlap_Index(OI)'] < -0.1) & 
        (sdg_edges['P_Value'] < 0.05)
    ]
    
    tradeoff_sdgs = []
    # 遍历权衡边，找到与当前 sdg 相连接的另一个节点
    for _, row in tradeoff_edges.iterrows():
        other_node = row['Target'] if row['Source'] == sdg else row['Source']
        tradeoff_sdgs.append(other_node.upper())
        
    tradeoff_count = len(tradeoff_sdgs)
    tradeoff_str = ", ".join(tradeoff_sdgs) # 将列表转为逗号分隔的字符串
    
    # 保存当前 SDG 的所有计算结果
    results.append({
        'SDG': sdg.upper(), # 统一转换为大写，如 SDG11
        '总共现频次 (Total Co-occurrences)': total_co_occur,
        '显著协同数量 (Synergies: OI>0.1, P<0.05)': synergy_count,
        '协同关系对应SDG (Synergy SDGs)': synergy_str,
        '显著权衡数量 (Trade-offs: OI<-0.1, P<0.05)': tradeoff_count,
        '权衡关系对应SDG (Trade-off SDGs)': tradeoff_str
    })

# 5. 转换为 DataFrame 并按总共现频次降序排列
summary_df = pd.DataFrame(results)
summary_df = summary_df.sort_values(by='总共现频次 (Total Co-occurrences)', ascending=False).reset_index(drop=True)

# 6. 保存计算结果
summary_df.to_excel(output_file, index=False)
print(f"计算完成，结果已保存至：{output_file}")
print("\nSDG 共现网络结构统计概览：")
print(summary_df.head(10))  # 打印前10行查看效果