import pandas as pd
import numpy as np

# 1. 定义文件路径
excel_path = r"D:\1sdgplanning\1data\sdg统计数据匹配.xlsx"
csv_path = r"D:\1sdgplanning\1data\市级国家重点生态功能区.csv"

def merge_ecological_zones():
    try:
        # 2. 读取数据 (指定CSV编码，通常中文系统CSV可能是gbk或utf-8)
        print("正在读取 Excel 和 CSV 数据...")
        df_excel = pd.read_excel(excel_path)
        
        # 尝试使用 utf-8 读取，如果报错则退化为 gbk
        try:
            df_csv = pd.read_csv(csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            df_csv = pd.read_csv(csv_path, encoding='gbk')

        # 3. 字段预处理与对齐
        print("正在进行字段预处理...")
        
        # 确定 Excel 中表示城市代码的列名（兼容叫 'code' 或 'city_code' 的情况）
        excel_code_col = 'code' if 'code' in df_excel.columns else 'city_code'
        
        # 清洗主表 (Excel) 的匹配键
        df_excel['city_clean'] = df_excel['city'].astype(str).str.strip()
        df_excel['code_clean'] = df_excel[excel_code_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        
        # 清洗附表 (CSV) 的匹配键
        df_csv['city_clean'] = df_csv['city'].astype(str).str.strip()
        df_csv['code_clean'] = df_csv['city_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        # 4. 执行双键左连接 (Left Join)
        print("正在匹配合并数据...")
        # 提取CSV中需要的列进行合并，避免引入多余列
        csv_subset = df_csv[['city_clean', 'code_clean', '重点功能区']].drop_duplicates(subset=['city_clean', 'code_clean'])
        
        df_merged = pd.merge(
            df_excel,
            csv_subset,
            how='left',
            on=['city_clean', 'code_clean']
        )

        # 5. 生成目标列：“国家重点生态功能区”
        # 逻辑：如果匹配过来的 '重点功能区' 有值（非空），则视为 1，否则为 0
        df_merged['国家重点生态功能区'] = np.where(df_merged['重点功能区'].notna(), 1, 0)

        # 清理过程产生的辅助列和冗余列
        df_merged.drop(columns=['city_clean', 'code_clean', '重点功能区'], inplace=True, errors='ignore')

        # 6. 保存覆盖原文件
        print("正在保存更新后的数据...")
        df_merged.to_excel(excel_path, index=False)

        # 7. 统计 1 和 0 的数量
        count_1 = (df_merged['国家重点生态功能区'] == 1).sum()
        count_0 = (df_merged['国家重点生态功能区'] == 0).sum()
        
        print("-" * 40)
        print(f"✅ 处理成功！数据已覆盖保存至: {excel_path}")
        print(f"📊 统计结果：")
        print(f"  - 匹配成功并标记为 1 的城市有: {count_1} 个")
        print(f"  - 未匹配到并标记为 0 的城市有: {count_0} 个")
        print("-" * 40)

    except FileNotFoundError as e:
        print(f"❌ 找不到文件，请确认路径是否正确: {e.filename}")
    except KeyError as e:
        print(f"❌ 找不到指定的列名，请确认CSV文件中是否包含该列: {e}")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")

if __name__ == "__main__":
    merge_ecological_zones()