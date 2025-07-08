#合并全部文件，检查是否所有的关键词都出现了
import os

# 定义目录路径和输出文件路径
input_dir = r"D:\1sdgplanning\3result\top50%"
output_file = r"D:\1sdgplanning\3result\merged_output.txt"

def merge_txt_files(input_dir, output_file):
    # 获取目录下所有txt文件
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    
    if not txt_files:
        print("目录中没有找到txt文件")
        return
    
    # 按文件名排序（可选）
    txt_files.sort()
    
    # 合并文件
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for filename in txt_files:
            filepath = os.path.join(input_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as infile:
                    # 写入文件名作为分隔（可选）
                    outfile.write(f"\n\n=== 文件: {filename} ===\n\n")
                    # 写入文件内容
                    outfile.write(infile.read())
                print(f"已合并: {filename}")
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {str(e)}")
    
    print(f"\n所有文件已成功合并到: {output_file}")

# 调用函数
merge_txt_files(input_dir, output_file)