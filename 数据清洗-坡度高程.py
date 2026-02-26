"""
=============================================================================
主要功能：
1. 读取主表(raw)与两个辅表(高程、坡度数据)。
2. 数据清洗：统一将连接键(code 和 市代码)转换为字符串格式，并去除首尾空格，防止因格式不同导致匹配失败。
3. 数据匹配：以主表为主(Left Join)，依据城市代码将高程和坡度的10项统计指标合并到主表中。
4. 结果保存：将匹配好的完整数据写回原始路径的Excel文件中，覆盖原有的raw sheet。
5. 匹配情况统计：在控制台打印原始数据行数、成功匹配到高程和坡度数据的行数，以及缺失提示。
=============================================================================
"""

import pandas as pd
import os

def data_matching_process():
    # ==================== 1. 定义文件路径 ====================
    main_file = r"D:\1sdgplanning\1data\sdg统计数据匹配.xlsx"
    elevation_file = r"D:\1sdgplanning\1data\城市高程数据.xlsx"
    slope_file = r"D:\1sdgplanning\1data\城市坡度数据.xlsx"

    # ==================== 2. 定义需要提取的列 ====================
    # 注意：这里的列名必须与你Excel表中的实际列名完全一致，如果原表叫别的名字请在此修改
    ele_cols_to_keep = ['市代码', '最小高程', '最大高程', '高程极差', '平均高程', '高程标准差']
    slope_cols_to_keep = ['市代码', '最小坡度', '最大坡度', '坡度极差', '平均坡度', '坡度标准差']

    print("开始加载数据...")
    try:
        # ==================== 3. 读取数据 ====================
        # 读取主表
        df_raw = pd.read_excel(main_file, sheet_name="raw")
        
        # 读取高程数据和坡度数据（只读取需要的列）
        df_ele = pd.read_excel(elevation_file, usecols=ele_cols_to_keep)
        df_slope = pd.read_excel(slope_file, usecols=slope_cols_to_keep)

        # ==================== 4. 数据清洗(统一连接键类型) ====================
        # 转换为字符串并去除前后多余空格，避免 '110000' 和 110000 或 '110000 ' 匹配不上的情况
        df_raw['code'] = df_raw['code'].astype(str).str.strip()
        df_ele['市代码'] = df_ele['市代码'].astype(str).str.strip()
        df_slope['市代码'] = df_slope['市代码'].astype(str).str.strip()

        # ==================== 5. 数据合并 (Left Join) ====================
        # 第一步：合并高程数据
        df_merged = pd.merge(df_raw, df_ele, left_on='code', right_on='市代码', how='left')
        # 合并后会多出一个 '市代码' 列，我们把它删掉，保持表格干净
        df_merged.drop(columns=['市代码'], inplace=True, errors='ignore')

        # 第二步：合并坡度数据
        df_merged = pd.merge(df_merged, df_slope, left_on='code', right_on='市代码', how='left')
        df_merged.drop(columns=['市代码'], inplace=True, errors='ignore')

        # ==================== 6. 覆盖保存原有Excel文档 ====================
        print("\n正在保存数据到原文件...")
        # 使用 ExcelWriter 覆盖更新原文件中的 'raw' sheet，保留其他可能的 sheet
        with pd.ExcelWriter(main_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_merged.to_excel(writer, sheet_name='raw', index=False)
        print("保存成功！")

        # ==================== 7. 输出匹配情况报告 ====================
        total_rows = len(df_raw)
        
        # 检查成功匹配的行数（以“平均高程”和“平均坡度”是否有非空值来判断）
        ele_matched = df_merged['平均高程'].notna().sum()
        slope_matched = df_merged['平均坡度'].notna().sum()
        
        print("\n" + "="*40)
        print(" 数据匹配情况报告")
        print("="*40)
        print(f"主表(raw)总行数: {total_rows} 行")
        print(f"成功匹配到【高程】数据的记录: {ele_matched} 行 (匹配率: {ele_matched/total_rows:.2%})")
        print(f"成功匹配到【坡度】数据的记录: {slope_matched} 行 (匹配率: {slope_matched/total_rows:.2%})")
        
        if ele_matched < total_rows:
            missing = total_rows - ele_matched
            print(f"⚠️ 提示：有 {missing} 行未能匹配到高程数据。")
        if slope_matched < total_rows:
            missing = total_rows - slope_matched
            print(f"⚠️ 提示：有 {missing} 行未能匹配到坡度数据。")
        print("="*40)

    except FileNotFoundError as e:
        print(f"\n❌ 文件读取错误: 未找到文件。请检查路径是否正确。\n详细信息: {e}")
    except ValueError as e:
        print(f"\n❌ 列名匹配错误: 请检查Excel文件中是否包含代码里要求提取的列名。\n详细信息: {e}")
    except Exception as e:
        print(f"\n❌ 发生未知错误: {e}")

if __name__ == "__main__":
    data_matching_process()