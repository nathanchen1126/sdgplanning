"""
=============================================================================
主要功能：
1. 读取主表(1统计数据匹配.xlsx - raw)与降水辅表(地级市逐月平均降水.xlsx)。
2. 数据清洗：将两表的 'code' 字段统一转换为字符串格式并去除首尾空格，确保严格匹配。
3. 去重保护：针对辅表中的 'code' 进行去重处理，防止因辅表存在多条同城数据导致主表行数膨胀。
4. 数据合并：以主表为基准(Left Join)，依据 'code' 将 '降水' 指标合并到主表中。
5. 结果保存：将匹配好的完整数据写回原始路径的Excel文件中，安全覆盖原有的 raw sheet。
6. 匹配情况统计：输出主表行数、成功匹配到降水数据的行数及匹配率。
=============================================================================
"""

import pandas as pd
import os

def precipitation_data_matching():
    # ==================== 1. 定义文件路径 ====================
    main_file = r"D:\1sdgplanning\1data\1统计数据匹配.xlsx"
    precip_file = r"D:\资源\地级市逐月平均降水.xlsx"

    # ==================== 2. 定义需要提取的列 ====================
    cols_to_load = ['code', '降水']

    print("开始加载降水数据...")
    try:
        # ==================== 3. 读取数据 ====================
        df_raw = pd.read_excel(main_file, sheet_name="raw")
        
        # 只读取 code 和 降水 两列，提高读取速度和降低内存
        df_precip = pd.read_excel(precip_file, usecols=cols_to_load)

        # 检查主表是否存在 code 列
        if 'code' not in df_raw.columns:
            raise ValueError("主表(raw)中未找到名为 'code' 的列。")

        # ==================== 4. 数据清洗 (统一连接键格式) ====================
        df_raw['code'] = df_raw['code'].astype(str).str.strip()
        df_precip['code'] = df_precip['code'].astype(str).str.strip()

        # ==================== 5. 去重保护 ====================
        # 考虑到辅表名包含“逐月”，若数据为长面板格式(同一个code有多行)，Merge会导致主表行数暴增
        # 这里默认保留第一条出现的记录。如果需要求均值或求和，需要在这里先做 groupby 处理
        initial_precip_rows = len(df_precip)
        df_precip.drop_duplicates(subset=['code'], keep='first', inplace=True)
        dropped_rows = initial_precip_rows - len(df_precip)
        if dropped_rows > 0:
            print(f"⚠️ 提示：在降水表中发现了 {dropped_rows} 条重复的 code 记录，已保留第一条以防数据膨胀。")

        # ==================== 6. 数据合并 (Left Join) ====================
        df_merged = pd.merge(df_raw, df_precip, on='code', how='left')

        # ==================== 7. 覆盖保存原有Excel文档 ====================
        print("\n正在保存处理后的数据到主文件...")
        with pd.ExcelWriter(main_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_merged.to_excel(writer, sheet_name='raw', index=False)
        print(f"保存成功！文件路径: {main_file}")

        # ==================== 8. 输出匹配情况报告 ====================
        total_rows = len(df_raw)
        matched_count = df_merged['降水'].notna().sum()
        
        print("\n" + "="*50)
        print(" 降水数据匹配情况报告")
        print("="*50)
        print(f"主表(raw)总行数: {total_rows} 行")
        print(f"成功匹配到[降水]数据的记录: {matched_count} 行 (匹配率: {matched_count/total_rows:.2%})")
        
        if matched_count < total_rows:
            missing = total_rows - matched_count
            print(f"⚠️ 提示：有 {missing} 行未能匹配到降水数据，这些行的降水指标目前显示为空值(NaN)。")
        print("="*50)

    except FileNotFoundError as e:
        print(f"\n❌ 文件读取错误: 未找到文件。\n{e}")
    except ValueError as e:
        print(f"\n❌ 列名异常: 请确认降水表里确切有一列的名字叫 '降水' (不能是 '降水量' 或 '某月降水')。\n{e}")
    except Exception as e:
        print(f"\n❌ 发生未知错误: {e}")

if __name__ == "__main__":
    precipitation_data_matching()