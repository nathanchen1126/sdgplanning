import os
from collections import OrderedDict

# ===== 参数配置区域 =====
# 输入目录路径，包含要处理的txt文件
TOP_INPUT_DIR = r"D:\1sdgplanning\3result\top50%_processed"
BOTTOM_INPUT_DIR = r"D:\1sdgplanning\3result\bottom50%_processed"

# 原始文本文件夹路径，用于验证关键词是否完整出现
TOP_SOURCE_DIR = r"D:\1sdgplanning\3result\top50%"
BOTTOM_SOURCE_DIR = r"D:\1sdgplanning\3result\bottom50%"

# 输出文件路径
TOP_OUTPUT_PATH = r"D:\1sdgplanning\3result\top50%_keywords.txt"
BOTTOM_OUTPUT_PATH = r"D:\1sdgplanning\3result\bottom50%_keywords.txt"

# 文件编码格式（如果遇到编码错误可以尝试改为'gbk'或其他编码）
FILE_ENCODING = 'utf-8'

# 是否保留原始大小写（True-区分大小写排序，False-不区分大小写排序）
CASE_SENSITIVE_SORT = False
# ===== 参数配置结束 =====

def load_source_texts(source_dir, encoding='utf-8'):
    """
    加载原始文本内容，用于验证关键词是否完整出现
    
    参数:
        source_dir: 原始文本文件夹路径
        encoding: 文件编码格式
    
    返回:
        字典 {文件名: 文件内容}
    """
    source_texts = {}
    for filename in os.listdir(source_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(source_dir, filename)
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    source_texts[filename] = file.read()
            except UnicodeDecodeError:
                print(f"警告: 原始文件 {filename} 使用指定编码({encoding})读取失败，跳过该文件")
                continue
    return source_texts

def is_keyword_valid(keyword, source_texts):
    """
    检查关键词是否在所有原始文本中至少完整出现一次
    
    参数:
        keyword: 要检查的关键词
        source_texts: 原始文本字典 {文件名: 文件内容}
    
    返回:
        bool: 关键词是否有效
    """
    for text in source_texts.values():
        if keyword in text:
            return True
    return False

def process_keyword_files(input_dir, output_path, source_dir, encoding='utf-8', case_sensitive=False):
    """
    处理关键词文件：读取、排序、去重并保存
    
    参数:
        input_dir: 输入目录路径，包含要处理的txt文件
        output_path: 输出文件路径
        source_dir: 原始文本文件夹路径
        encoding: 文件编码格式
        case_sensitive: 是否区分大小写排序
    """
    # 加载原始文本内容
    source_texts = load_source_texts(source_dir, encoding)
    if not source_texts:
        print(f"错误: 无法加载任何原始文本文件({source_dir})，请检查路径和编码设置")
        return
    
    # 存储所有关键词
    all_keywords = set()
    removed_keywords = set()
    
    # 第一步：读取所有txt文件内容
    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(input_dir, filename)
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    # 按行读取并去除空白字符
                    keywords = [line.strip() for line in file if line.strip()]
                    for keyword in keywords:
                        # 检查关键词是否在原始文本中完整出现
                        if is_keyword_valid(keyword, source_texts):
                            all_keywords.add(keyword)
                        else:
                            removed_keywords.add(keyword)
            except UnicodeDecodeError:
                print(f"警告: 文件 {filename} 使用指定编码({encoding})读取失败，尝试跳过")
                continue
    
    # 打印被移除的关键词信息
    if removed_keywords:
        print(f"\n以下关键词因未在原始文本中完整出现而被移除({input_dir}):")
        for kw in sorted(removed_keywords, key=lambda x: x.lower()):
            print(f"- {kw}")
        print(f"共移除 {len(removed_keywords)} 个关键词")
    
    # 第二步：按字母排序
    if case_sensitive:
        sorted_keywords = sorted(all_keywords)
    else:
        sorted_keywords = sorted(all_keywords, key=lambda x: x.lower())
    
    # 第三步：保存结果
    with open(output_path, 'w', encoding=encoding) as output_file:
        output_file.write('\n'.join(sorted_keywords))
    
    print(f"\n处理完成！共提取 {len(sorted_keywords)} 个有效关键词，已保存到 {output_path}")

if __name__ == "__main__":
    # 处理top50%数据
    print("="*50)
    print("开始处理top50%数据...")
    process_keyword_files(
        input_dir=TOP_INPUT_DIR,
        output_path=TOP_OUTPUT_PATH,
        source_dir=TOP_SOURCE_DIR,
        encoding=FILE_ENCODING,
        case_sensitive=CASE_SENSITIVE_SORT
    )
    
    # 处理bottom50%数据
    print("\n" + "="*50)
    print("开始处理bottom50%数据...")
    process_keyword_files(
        input_dir=BOTTOM_INPUT_DIR,
        output_path=BOTTOM_OUTPUT_PATH,
        source_dir=BOTTOM_SOURCE_DIR,
        encoding=FILE_ENCODING,
        case_sensitive=CASE_SENSITIVE_SORT
    )
    
    print("\n所有处理完成！")