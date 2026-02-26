"""
=============================================================================
主要功能：
1. 读取主表(1统计数据匹配.xlsx - raw)与2022年城市统计数据辅表。
2. 数据清洗：将主表的 'code' 和辅表的 '市代码' 统一转换为字符串并去首尾空格，确保Join键格式一致。
3. 数据匹配：以主表为基准(Left Join)，依据城市代码将10项关键城市统计指标合并到主表中。
4. 结果保存：将匹配好的数据写回原始路径的Excel文件中，覆盖原有的raw sheet，不影响其他sheet。
5. 匹配情况统计：打印主表总行数、成功匹配到统计数据的行数以及缺失提示。
=============================================================================
"""

import pandas as pd
import os

def city_stats_matching_process():
    # ==================== 1. 定义文件路径 ====================
    main_file = r"D:\1sdgplanning\1data\1统计数据匹配.xlsx"
    stats_file = r"D:\1sdgplanning\1data\城市统计数据2022.xlsx"

    # ==================== 2. 定义需要提取的列 ====================
    # 包含连接键 '市代码' 以及 10 项待匹配指标
    cols_to_keep = [
        '市代码',
        '水资源总量_万立方米_全市',
        '建成区面积_平方公里_市辖区',
        '建成区绿化覆盖率_百分比_市辖区',
        '第三产业占地区生产总值的比重_全市',
        '第二产业占地区生产总值的比重_全市',
        '第一产业占地区生产总值的比重_全市',
        '科学技术支出_万元_全市',
        '教育支出_万元_全市',
        '货物出口额_万元_全市',
        '高速公路里程_公里_全市'
    ]

    print("开始加载并处理数据...")
    try:
        # ==================== 3. 读取数据 ====================
        df_raw = pd.read_excel(main_file, sheet_name="raw")
        # 仅读取需要的列，降低内存占用
        df_stats = pd.read_excel(stats_file, usecols=cols_to_keep)

        # ==================== 4. 数据清洗(统一连接键类型) ====================
        # 假设主表的城市代码列名仍为 'code'
        if 'code' not in df_raw.columns:
            raise ValueError("主表(raw)中未找到名为 'code' 的列，请核对主表的连接键名称。")
            
        df_raw['code'] = df_raw['code'].astype(str).str.strip()
        df_stats['市代码'] = df_stats['市代码'].astype(str).str.strip()

        # 处理可能存在的重复代码记录，保留第一条（防止Merge后数据行数膨胀）
        df_stats.drop_duplicates(subset=['市代码'], keep='first', inplace=True)

        # ==================== 5. 数据合并 (Left Join) ====================
        df_merged = pd.merge(df_raw, df_stats, left_on='code', right_on='市代码', how='left')
        
        # 删掉多余的 '市代码' 列
        df_merged.drop(columns=['市代码'], inplace=True, errors='ignore')

        # ==================== 6. 覆盖保存原有Excel文档 ====================
        print("\n正在保存数据到主文件...")
        with pd.ExcelWriter(main_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_merged.to_excel(writer, sheet_name='raw', index=False)
        print(f"保存成功！文件路径: {main_file}")

        # ==================== 7. 输出匹配情况报告 ====================
        total_rows = len(df_raw)
        
        # 选取一个指标作为基准，判断是否匹配成功（假设如果匹配上了，建成区面积一般不会为空）
        # 这里使用 '建成区面积_平方公里_市辖区' 来核算匹配数量
        matched_count = df_merged['建成区面积_平方公里_市辖区'].notna().sum()
        
        print("\n" + "="*50)
        print(" 2022城市统计数据匹配情况报告")
        print("="*50)
        print(f"主表(raw)总行数: {total_rows} 行")
        print(f"成功匹配到数据的记录: {matched_count} 行")
        print(f"整体匹配率: {matched_count/total_rows:.2%}")
        
        if matched_count < total_rows:
            missing = total_rows - matched_count
            print(f"⚠️ 提示：有 {missing} 行未能从2022统计数据表中找到对应记录，相关指标已填充为 NaN。")
        print("="*50)

    except FileNotFoundError as e:
        print(f"\n❌ 文件读取错误: 未找到文件，请检查路径及文件名是否完全正确。\n{e}")
    except ValueError as e:
        print(f"\n❌ 数据值/列名错误: {e}")
    except Exception as e:
        print(f"\n❌ 发生未知错误: {e}")

if __name__ == "__main__":
    city_stats_matching_process()