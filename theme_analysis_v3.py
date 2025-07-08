import os
import time
import requests

# 配置部分，分文件夹保存
API_KEY = "sk-6e8113f768cd42768058ce6dc6ef3401"  # 实际API密钥
API_URL = "https://api.deepseek.com/v1/chat/completions"
TEMPERATURE = 1.0
STOPWORDS_PATH = r"D:\1sdgplanning\1data\custom_stop.txt"  # 停用词文件路径

INPUT_DIRS = {
    "top50%": r"D:\1sdgplanning\3result\top50%",
    "bottom50%": r"D:\1sdgplanning\3result\bottom50%"
}

OUTPUT_BASE = r"D:\1sdgplanning\3result"
SYSTEM_PROMPT = """您是一位专业的规划文本分析师。请按照以下步骤完成任务：

1.提取文本中明确关于"可持续发展目标"的段落：[相关的段落]
2.从[相关的段落]中提取与"可持续发展目标"相关的最常出现的关键词:[关键词]

请用以下格式返回结果，不需要返回相关的段落：
[换行分隔的关键词列表]
"""

def load_stopwords(stopwords_path):
    """加载停用词列表"""
    stopwords = set()
    try:
        with open(stopwords_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:  # 确保不是空行
                    stopwords.add(word)
        print(f"已加载 {len(stopwords)} 个停用词")
        return stopwords
    except Exception as e:
        print(f"加载停用词文件失败: {e}")
        return stopwords  # 返回空集合

def filter_stopwords(text, stopwords):
    """过滤文本中的停用词"""
    if not stopwords:
        return text
    
    # 简单的停用词过滤，可根据需要调整
    words = text.split()
    filtered_words = [word for word in words if word not in stopwords]
    return ' '.join(filtered_words)

def create_output_structure(base_dir):
    """创建完整的输出文件夹结构"""
    try:
        # 创建主文件夹
        os.makedirs(base_dir, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建文件夹结构失败: {e}")
        return False

def filter_keywords(keywords, original_text):
    """过滤关键词，只保留在原始文本中完整出现的关键词"""
    filtered_keywords = []
    for keyword in keywords:
        # 去除可能的空白字符
        keyword = keyword.strip()
        if not keyword:
            continue
        
        # 检查关键词是否在原始文本中完整出现
        if keyword in original_text:
            filtered_keywords.append(keyword)
        else:
            print(f"移除未完整出现的关键词: '{keyword}'")
    
    return filtered_keywords

def process_all_files():
    """处理所有文件"""
    # 加载停用词
    stopwords = load_stopwords(STOPWORDS_PATH)
    
    for category, input_dir in INPUT_DIRS.items():
        output_dir = os.path.join(OUTPUT_BASE, f"{category}_processed")
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                print(f"无法创建输出目录 {output_dir}: {e}")
                continue
        
        print(f"\n处理 {category} 文件...")
        
        for file_name in os.listdir(input_dir):
            if not file_name.endswith('.txt'):
                continue
                
            file_path = os.path.join(input_dir, file_name)
            output_path = os.path.join(output_dir, file_name)
            print(f"正在处理: {file_name}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                # 预处理：过滤停用词
                filtered_content = filter_stopwords(original_content, stopwords)
                
                # 调用API
                headers = {"Authorization": f"Bearer {API_KEY}"}
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": filtered_content}
                    ],
                    "temperature": TEMPERATURE
                }
                
                response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                
                # 获取API返回的关键词列表
                api_response = response.json()['choices'][0]['message']['content']
                keywords = [k.strip() for k in api_response.split('\n') if k.strip()]
                
                # 过滤关键词，只保留在原始文本中完整出现的关键词
                filtered_keywords = filter_keywords(keywords, original_content)
                
                # 保存过滤后的关键词
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(filtered_keywords))
                
                time.sleep(1)
                
            except Exception as e:
                print(f"处理 {file_name} 时出错: {e}")

if __name__ == "__main__":
    if API_KEY == "your-deepseek-api-key":
        print("请替换为您的真实DeepSeek API密钥")
        exit()
    
    process_all_files()
    print("\n处理完成! 结果保存在各分类的输出文件夹中")