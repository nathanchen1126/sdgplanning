import os
import shutil
import pandas as pd
from pathlib import Path

def sample_cities_and_copy_files():
    """主函数：抽样城市并复制对应文件"""
    # ========== 配置部分 ==========
    # 输入文件路径
    excel_path = r"D:\1sdgplanning\3result\similarity_result0427_8192chunk.xlsx"
    source_dir = r"D:\1sdgplanning\1data\1全部批复"
    
    # 输出配置
    output_base = r"D:\1sdgplanning\3result"
    top_dir = os.path.join(output_base, "top50%")
    bottom_dir = os.path.join(output_base, "bottom50%")
    sampled_excel = os.path.join(output_base, "sampled_cities.xlsx")
    
    # ========== 1. 城市抽样 ==========
    print("开始城市抽样...")
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_path)
        
        # 检查必要列是否存在
        if 'city' not in df.columns or 'TOTAL' not in df.columns:
            raise ValueError("Excel文件中必须包含'city'和'TOTAL'列")
        
        # 按TOTAL值排序并分割
        df_sorted = df.sort_values(by='TOTAL', ascending=False).reset_index(drop=True)
        split_point = len(df_sorted) // 2
        top_50 = df_sorted.iloc[:split_point]
        bottom_50 = df_sorted.iloc[split_point:]
        
        # 随机抽样（各10个）
        sample_size = 10
        top_sample = top_50.sample(n=min(sample_size, len(top_50)), random_state=42)
        bottom_sample = bottom_50.sample(n=min(sample_size, len(bottom_50)), random_state=42)
        
        # 保存抽样结果
        with pd.ExcelWriter(sampled_excel) as writer:
            top_sample.to_excel(writer, sheet_name='Top_50_percent', index=False)
            bottom_sample.to_excel(writer, sheet_name='Bottom_50_percent', index=False)
        print(f"城市抽样完成，结果已保存到: {sampled_excel}")
        
    except Exception as e:
        print(f"城市抽样失败: {e}")
        return
    
    # ========== 2. 文件复制 ==========
    def copy_files(sample_df, target_dir):
        """复制文件到目标目录"""
        os.makedirs(target_dir, exist_ok=True)
        copied = 0
        missing = []
        
        for city in sample_df['city']:
            # 处理可能的NaN值
            if pd.isna(city):
                continue
                
            # 构建文件名（处理特殊字符）
            city_name = str(city).strip()
            file_name = f"{city_name}.txt"
            src_path = os.path.join(source_dir, file_name)
            
            if os.path.exists(src_path):
                shutil.copy2(src_path, target_dir)
                copied += 1
            else:
                missing.append(city_name)
        
        return copied, missing
    
    print("\n开始复制文件...")
    try:
        # 复制top50%文件
        print("处理top50%城市...")
        top_copied, top_missing = copy_files(top_sample, top_dir)
        print(f"成功复制: {top_copied}/{len(top_sample)}")
        if top_missing:
            print(f"未找到文件的城市: {', '.join(top_missing[:5])}" + 
                  ("..." if len(top_missing)>5 else ""))
        
        # 复制bottom50%文件
        print("\n处理bottom50%城市...")
        bottom_copied, bottom_missing = copy_files(bottom_sample, bottom_dir)
        print(f"成功复制: {bottom_copied}/{len(bottom_sample)}")
        if bottom_missing:
            print(f"未找到文件的城市: {', '.join(bottom_missing[:5])}" + 
                  ("..." if len(bottom_missing)>5 else ""))
        
        print("\n文件复制完成!")
        print(f"top50%文件保存在: {top_dir}")
        print(f"bottom50%文件保存在: {bottom_dir}")
        
    except Exception as e:
        print(f"文件复制过程中出错: {e}")

if __name__ == "__main__":
    # 检查必要库
    try:
        import pandas as pd
    except ImportError:
        print("请先安装pandas库: pip install pandas openpyxl")
        exit()
    
    sample_cities_and_copy_files()