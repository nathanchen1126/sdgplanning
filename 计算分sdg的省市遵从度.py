import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from scipy.stats import pearsonr
import os
import warnings

warnings.filterwarnings('ignore')

def calculate_sdg_level_compliance():
    # 1. 设置输入输出路径
    input_file = r"D:\1sdgplanning\1data\1sdg省市匹配.xlsx"
    output_dir = r"D:\1sdgplanning\1data"
    output_file = os.path.join(output_dir, "各SDG目标_省级遵从度计算结果.xlsx")
    
    print("正在读取省市匹配数据，请稍候...")
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        print(f"读取文件失败，请检查路径: {e}")
        return
        
    results = []
    
    print("正在逐个计算 SDG1 到 SDG17 在全国所有地级市的平均遵从度指标...")
    
    # 2. 循环遍历 17 个 SDG 目标
    for i in range(1, 18):
        sdg_name = f'SDG{i}'
        city_col = f'sdg{i}'
        pro_col = f'sdg{i}_pro'
        
        if city_col not in df.columns or pro_col not in df.columns:
            print(f"警告：找不到列 {city_col} 或 {pro_col}，已跳过。")
            continue
            
        # 提取当前维度的市级和省级数据，并剔除缺失值 (NaN)
        valid_data = df[[city_col, pro_col]].dropna()
        y_city = valid_data[city_col].values
        y_pro = valid_data[pro_col].values
        n_valid = len(valid_data)
        
        if n_valid > 1:
            # 测度 1：绝对偏离度 (MAE 与 RMSE)
            # MAE 越大，说明在这个目标上，地市级与省级文本得分的绝对差异越大（地方裁量权大）
            rmse = np.sqrt(mean_squared_error(y_pro, y_city))
            mae = mean_absolute_error(y_pro, y_city)
            
            # 测度 2：市级得分在全样本的方差 (Variance)
            # 方差越大，说明各地级市在这个目标上的做法五花八门，分化严重
            city_variance = np.var(y_city)
            
            # 测度 3：绝对拟合优度 (Sklearn R2)
            try:
                sklearn_r2 = r2_score(y_true=y_pro, y_pred=y_city)
            except:
                sklearn_r2 = np.nan
                
            # 测度 4：趋势一致性 (Pearson r 及 Pearson R2)
            try:
                if np.std(y_city) == 0 or np.std(y_pro) == 0:
                    r = np.nan
                else:
                    r, p_value = pearsonr(y_city, y_pro)
                pearson_r2 = r ** 2 if not np.isnan(r) else np.nan
            except:
                r = np.nan
                pearson_r2 = np.nan
                
        else:
            rmse, mae, city_variance, sklearn_r2, r, pearson_r2 = np.nan, np.nan, np.nan, np.nan, np.nan, np.nan
            
        # 记录当前 SDG 维度的计算结果
        results.append({
            'SDG_Goal': sdg_name,
            'Valid_Cities_Count': n_valid,
            'City_Level_Variance (方差)': city_variance,
            'Absolute_Compliance_R2 (Sklearn)': sklearn_r2,
            'Trend_Compliance_R2 (Pearson_R2)': pearson_r2,
            'Trend_Correlation_r': r,
            'Absolute_Error_RMSE': rmse,
            'Absolute_Error_MAE': mae
        })
        
    # 3. 转换为 DataFrame
    res_df = pd.DataFrame(results)
    
    # 按照 MAE (绝对误差) 升序排列
    # 排在前面的：误差小，属于强约束、死命令的 SDG
    # 排在后面的：误差大，属于地方自由发挥的 SDG
    res_df = res_df.sort_values(by='Absolute_Error_MAE', ascending=True)
    
    res_df.to_excel(output_file, index=False)
    
    print("\n" + "=" * 55)
    print("✅ 计算已全部完成！")
    print(f"📁 结果已成功保存至:\n   {output_file}")
    print("=" * 55)

if __name__ == "__main__":
    calculate_sdg_level_compliance()