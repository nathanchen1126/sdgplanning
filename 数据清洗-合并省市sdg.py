import pandas as pd
import os

def merge_excel_data():
    # 1. 定义输入文件路径
    file1_path = r"D:\1sdgplanning\3result\similarity.xls"
    file2_path = r"D:\1sdgplanning\3result\similarity_result_province.xlsx"
    
    # --- 修改的部分：定义新的输出路径 ---
    output_dir = r"D:\1sdgplanning\1data"
    output_path = os.path.join(output_dir, "1sdg省市匹配.xlsx")
    
    # 确保输出文件夹存在，如果不存在则自动创建
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已创建文件夹: {output_dir}")

    print("正在读取数据，请稍候...")
    # 2. 读取Excel文件
    try:
        df1 = pd.read_excel(file1_path)
        df2 = pd.read_excel(file2_path)
    except FileNotFoundError as e:
        print(f"找不到文件，请检查路径是否正确: {e}")
        return

    # 3. 定义需要从表2中提取的列（必须包含匹配键 '省'）
    columns_to_merge = [
        '省', 'total_pro', 'sdg1_pro', 'sdg2_pro', 'sdg3_pro', 'sdg4_pro', 
        'sdg5_pro', 'sdg6_pro', 'sdg7_pro', 'sdg8_pro', 'sdg9_pro', 
        'sdg10_pro', 'sdg11_pro', 'sdg12_pro', 'sdg13_pro', 'sdg14_pro', 
        'sdg15_pro', 'sdg16_pro', 'sdg17_pro'
    ]

    # 检查表2中是否包含所有需要的列
    missing_cols = [col for col in columns_to_merge if col not in df2.columns]
    if missing_cols:
        print(f"警告: similarity_result_province.xlsx 中缺少以下列: {missing_cols}")
        return

    # 从表2中仅截取我们需要的列
    df2_subset = df2[columns_to_merge]

    # 4. 去重处理（确保表2每个省只有一条数据）
    df2_subset = df2_subset.drop_duplicates(subset=['省'])

    # 5. 合并数据 (Left Join)
    merged_df = pd.merge(df1, df2_subset, on='省', how='left')

    # 6. 保存结果到新文件 (保存为 .xlsx 格式)
    print("正在保存文件...")
    merged_df.to_excel(output_path, index=False)
    
    # 7. 计算并输出匹配统计信息
    original_len = len(df1)
    matched_count = merged_df['total_pro'].notna().sum()
    unmatched_count = original_len - matched_count

    print("-" * 40)
    print(f"合并处理完成！结果已成功保存至:\n{output_path}")
    print("-" * 40)
    print(f"【匹配结果统计】")
    print(f"原始文件 similarity.xls 总行数: {original_len} 行")
    print(f"成功匹配上并填充数据的行数: {matched_count} 行")
    print(f"未匹配上的行数 (留空): {unmatched_count} 行")
    print("-" * 40)

if __name__ == "__main__":
    merge_excel_data()