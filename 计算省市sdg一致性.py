import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from scipy.stats import pearsonr
import os
import warnings

# 忽略计算皮尔逊相关系数时可能出现的除零警告
warnings.filterwarnings('ignore')

def calculate_city_level_compliance():
    # 1. 设置输入输出路径 (请确保路径与你本地一致)
    input_file = r"D:\1sdgplanning\1data\1sdg省市匹配.xlsx"
    output_dir = r"D:\1sdgplanning\1data"
    output_file = os.path.join(output_dir, "地级市SDG省级遵从度计算结果.xlsx")
    
    print("正在读取省市匹配数据，请稍候...")
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        print(f"读取文件失败，请检查路径: {e}")
        return
        
    results = []
    
    # 构建所需的列名列表 (SDG1 到 SDG17)
    sdg_cols = [f'sdg{i}' for i in range(1, 18)]
    pro_cols = [f'sdg{i}_pro' for i in range(1, 18)]
    
    print("正在逐个地级市计算 17 个 SDG 维度的遵从度指标...")
    
    # 2. 循环遍历每一行（每一个地级市）
    for index, row in df.iterrows():
        # --- 修正：将提取省份的键值改为真实的列名 '省' ---
        city_name = row.get('city', row.get('City', f'City_Row_{index}'))
        city_id   = row.get('id', row.get('ID', np.nan))
        city_code = row.get('code', row.get('Code', np.nan))
        region    = row.get('region', row.get('Region', 'Unknown'))
        province_name = row.get('省', 'Unknown')  # 这里改成了找 '省'
        # ---------------------------------------------
        
        # 提取当前城市的市级向量和省级向量
        try:
            y_city = row[sdg_cols].astype(float).values
            y_pro = row[pro_cols].astype(float).values
        except KeyError as e:
            print(f"行 {index} 缺少必要的 SDG 列，请检查表格字段名。缺失报错: {e}")
            break
            
        # 剔除在这一对数据中存在缺失值 (NaN) 的维度
        mask = ~np.isnan(y_city) & ~np.isnan(y_pro)
        y_city_clean = y_city[mask]
        y_pro_clean = y_pro[mask]
        n_valid = len(y_city_clean)
        
        # 至少需要 2 个有效点才能计算相关性和误差
        if n_valid > 1:
            # 测度 1：绝对偏离度 (RMSE 和 MAE)
            rmse = np.sqrt(mean_squared_error(y_pro_clean, y_city_clean))
            mae = mean_absolute_error(y_pro_clean, y_city_clean)
            
            # 测度 2：绝对拟合优度 (Sklearn R2)
            try:
                sklearn_r2 = r2_score(y_true=y_pro_clean, y_pred=y_city_clean)
            except:
                sklearn_r2 = np.nan
                
            # 测度 3：趋势一致性 (Pearson r 及 Pearson R2)
            try:
                if np.std(y_city_clean) == 0 or np.std(y_pro_clean) == 0:
                    r = np.nan
                else:
                    r, p_value = pearsonr(y_city_clean, y_pro_clean)
                pearson_r2 = r ** 2 if not np.isnan(r) else np.nan
            except:
                r = np.nan
                pearson_r2 = np.nan
                
        else:
            rmse, mae, sklearn_r2, r, pearson_r2 = np.nan, np.nan, np.nan, np.nan, np.nan
            
        # 将保留的基础字段加入到最终的输出字典中
        results.append({
            'city': city_name,
            'id': city_id,
            'code': city_code,
            'region': region,
            'province': province_name,  # 这里的省份名称现在可以正确匹配上了
            'Valid_SDGs_Count': n_valid,
            'Absolute_Compliance_R2 (Sklearn)': sklearn_r2,
            'Trend_Compliance_R2 (Pearson_R2)': pearson_r2,
            'Trend_Correlation_r': r,
            'Absolute_Error_RMSE': rmse,
            'Absolute_Error_MAE': mae
        })
        
    # 3. 将结果转换为 DataFrame 并保存为新的 Excel
    res_df = pd.DataFrame(results)
    
    # 按照 Pearson R2 (趋势遵从度) 进行降序排列
    res_df = res_df.sort_values(by='Trend_Compliance_R2 (Pearson_R2)', ascending=False)
    
    res_df.to_excel(output_file, index=False)
    
    print("\n" + "=" * 55)
    print(f"✅ 成功计算了 {len(res_df)} 个地级市的指标！")
    print(f"📁 结果已成功保存至:\n   {output_file}")
    print("=" * 55)

if __name__ == "__main__":
    calculate_city_level_compliance()