import os
import shutil

# 源文件夹路径
source_folder = r"D:\1sdgplanning\1data\1分省批复"
# 目标文件夹路径
target_folder = r"D:\1sdgplanning\1data\1全部批复"

# 确保目标文件夹存在
os.makedirs(target_folder, exist_ok=True)

# 遍历源文件夹及其所有子文件夹
for root, dirs, files in os.walk(source_folder):
    for filename in files:
        # 检查文件是否是txt文件
        if filename.endswith(".txt"):
            # 构建完整的源文件路径
            source_file = os.path.join(root, filename)
            # 构建目标文件路径（直接放在目标文件夹，不保留原目录结构）
            target_file = os.path.join(target_folder, filename)
            
            # 处理同名文件（避免覆盖）
            if os.path.exists(target_file):
                # 如果目标文件已存在，添加 (1), (2) 等后缀
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(target_file):
                    target_file = os.path.join(target_folder, f"{base} ({counter}){ext}")
                    counter += 1
            
            # 复制文件
            shutil.copy2(source_file, target_file)
            print(f"已复制: {source_file} → {target_file}")

print("所有txt文件复制完成！")