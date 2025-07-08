import pandas as pd
import os

# 文件路径
csv_path = r"D:\1sdgplanning\1data\1分省批复\吉林\吉林.csv"
output_dir = r"D:\1sdgplanning\1data\1分省批复\吉林"

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)

# 读取CSV文件
try:
    df = pd.read_csv(csv_path, encoding='utf-8')
    
    # 检查是否包含所需的列
    if '地区' not in df.columns or '内容' not in df.columns:
        raise ValueError("CSV文件中必须包含'地区'和'内容'两列")
    
    # 遍历每一行
    for index, row in df.iterrows():
        # 获取地区和内容
        region = str(row['地区']).strip()  # 去除前后空格
        content = str(row['内容'])
        
        # 创建txt文件名
        txt_filename = f"{region}.txt"
        txt_path = os.path.join(output_dir, txt_filename)
        
        # 写入文件
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    print(f"成功创建了{len(df)}个txt文件")
    
except FileNotFoundError:
    print(f"错误：找不到CSV文件 {csv_path}")
except Exception as e:
    print(f"发生错误: {str(e)}")