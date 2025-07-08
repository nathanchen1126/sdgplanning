import pandas as pd

def calculate_province_hhi(file_path, sheet_name='data', pro_col='pro', cluster_col='cluster'):
    """
    从 Excel 文件加载数据，并计算每个省份的 HHI 指数。

    参数:
        file_path (str): Excel 文件的路径。
        sheet_name (str): 包含数据的表名，默认为 'data'。
        pro_col (str): 代表省份的列名，默认为 'pro'。
        cluster_col (str): 代表聚类的列名，默认为 'cluster'。

    返回:
        pandas.Series: 以省份代码为索引，HHI 值为内容的 Series，
                       如果发生错误则返回 None。
    """
    try:
        # 1. 加载数据
        print(f"正在读取文件: {file_path}, 表: {sheet_name}...")
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        print("文件读取成功！")

        # 2. 检查必需的列是否存在
        if pro_col not in df.columns or cluster_col not in df.columns:
            print(f"错误：文件中必须包含 '{pro_col}' 和 '{cluster_col}' 列。")
            print(f"找到的列有: {df.columns.tolist()}")
            return None

        # 3. 定义 HHI 计算函数
        def hhi_func(group):
            n_total = len(group)
            if n_total == 0:
                return 0.0 # 如果省份没有数据，HHI 为 0

            # 计算每个聚类的比例
            proportions = group[cluster_col].value_counts() / n_total

            # 计算 HHI：比例的平方和
            hhi = (proportions ** 2).sum()
            return hhi

        # 4. 按省份分组并应用 HHI 计算函数
        print("正在按省份计算 HHI 指数...")
        hhi_results = df.groupby(pro_col).apply(hhi_func)
        print("HHI 指数计算完成！")

        return hhi_results

    except FileNotFoundError:
        print(f"错误：找不到文件 '{file_path}'。请确认文件路径是否正确，并且您有权限访问它。")
        return None
    except Exception as e:
        print(f"处理文件时发生未知错误： {e}")
        return None

# --- 用户需要确认的部分 ---
# 请确保这里的路径与您文件的实际位置完全一致。
# 在 Windows 系统中，建议使用 'r' 前缀或双反斜杠 '\\' 来处理路径。
excel_file_path = r"D:\1sdgplanning\5fig\数据\聚类结果.xlsx"
output_csv_path = "province_hhi_results.csv" # (可选) 定义保存结果的文件名

# --- 执行计算 ---
hhi_values = calculate_province_hhi(excel_file_path)

# --- 显示并保存结果 ---
if hhi_values is not None:
    print("\n--- 各省份 HHI 指数计算结果 ---")
    print(hhi_values)

    # (可选) 将结果保存到 CSV 文件，方便后续使用
    try:
        hhi_values.to_csv(output_csv_path, header=['HHI'])
        print(f"\n结果已成功保存到文件: {output_csv_path}")
    except Exception as e:
        print(f"\n保存文件时发生错误: {e}")