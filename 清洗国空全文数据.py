import os
import shutil
from collections import defaultdict

# 设置原始路径和新路径
original_root = r'D:\国空文本'
new_root = r'D:\国空文本\重命名'

# 创建新的根目录（如果不存在）
os.makedirs(new_root, exist_ok=True)

# 用于记录每个城市名称的文件计数
file_counters = defaultdict(int)

# 遍历原始目录结构
for root, dirs, files in os.walk(original_root):
    # 只处理有文件的目录
    if not files:
        continue
    
    # 确保我们在城市级目录（路径深度至少为2级）
    if root.count(os.sep) < original_root.count(os.sep) + 2:
        continue
    
    # 获取城市名称（最后一级目录名）
    city_name = os.path.basename(root)
    
    # 处理当前目录中的每个文件
    for filename in files:
        # 获取文件扩展名
        file_ext = os.path.splitext(filename)[1]
        
        # 增加该城市的文件计数器
        file_counters[city_name] += 1
        count = file_counters[city_name]
        
        # 创建新文件名
        if count == 1:
            new_filename = f"{city_name}{file_ext}"
        else:
            new_filename = f"{city_name}{count}{file_ext}"
        
        # 构建完整路径
        original_file = os.path.join(root, filename)
        new_file = os.path.join(new_root, new_filename)
        
        try:
            # 复制文件到新位置并重命名
            shutil.copy2(original_file, new_file)
            print(f"已复制: {os.path.join(os.path.basename(os.path.dirname(root)), city_name, filename)}")
            print(f"      → {new_filename} (在 {new_root})")
            print("-" * 50)
        except Exception as e:
            print(f"复制失败: {original_file} -> {new_file} - {str(e)}")

print("\n操作完成！所有文件已复制并重命名到:", new_root)