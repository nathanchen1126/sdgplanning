import ollama
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import pandas as pd
import time

#######################################
#           可配置路径设置             #
#######################################

# 批复文件夹路径
PIFU_FOLDER = r"D:\1sdgplanning\1data\1全部批复"

# SDG文件路径
SDG_PATH = r"D:\1sdgplanning\1data\sdg.txt"

# 停用词文件路径
STOPWORD_FILE = r"D:\1sdgplanning\1data\hit_stop.txt"

# 结果输出Excel文件名
OUTPUT_EXCEL = "similarity_result0426.xlsx"

# 自定义停用词列表
CUSTOM_STOPWORDS = [
    "原则同意",
    "各类开发保护建设活动的基本依据，请认真组织实施",
    "发展",
    "建设",
    "保护",
    "利用",
    "安全",
    "区域",
    "城市",
    "人民",
    "关于",
    "全面",
    "目标",
    "加强",
    "完善",
    "实施",
    "推进",
    "提升",
    "各类",
    "基本",
    "必须",
    "严格执行",
    "不得随意",
    "违规变更",
    "按照",
    "要求",
    "健全",
    "各级",
    "监测",
    "评估",
    "预警",
    "机制",
    "依据",
    "核发",
    "许可",
    "运用",
    "完善配套",
    "政策措施",
    "明确",
    "责任分工",
    "组织领导",
    "协同",
    "指导",
    "监督",
    "评估",
    "确保",
    "实现",
    "目标任务",
    "重大事项",
    "及时",
    "请示报告"
]

#######################################
#           功能代码               #
#######################################

def read_file(filepath):
    """读取文件内容"""
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def load_stopwords(stopword_file, custom_stopwords=None):
    """加载停用词表"""
    stopwords = set()
    
    # 从文件加载停用词
    if os.path.exists(stopword_file):
        with open(stopword_file, 'r', encoding='utf-8') as f:
            stopwords.update(line.strip() for line in f if line.strip())
    
    # 添加自定义停用词
    if custom_stopwords:
        stopwords.update(custom_stopwords)
    
    return stopwords

def remove_stopwords(text, stopwords):
    """去除停用词"""
    if not stopwords:
        return text
    
    words = text.split()
    filtered_words = [word for word in words if word not in stopwords]
    return ' '.join(filtered_words)

def chunk_text(text, max_tokens=8192):
    """简单分块处理（按字符分割）"""
    chunk_size = max_tokens * 1  # 粗略估计中文字符与token比例
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def get_document_embedding_with_retry(text, max_retries=3):
    """获取文档嵌入向量，带有重试机制"""
    chunks = chunk_text(text)
    embeddings = []
    
    for chunk in chunks:
        retry_count = 0
        while retry_count < max_retries:
            try:
                vector = ollama.embeddings(model="bge-m3", prompt=chunk)
                if 'embedding' in vector and len(vector['embedding']) > 0:
                    embedding_array = np.array(vector['embedding'])
                    if not np.isnan(embedding_array).any():
                        # 对每个块的嵌入向量进行L2归一化
                        normalized_embedding = embedding_array / np.linalg.norm(embedding_array)
                        embeddings.append(normalized_embedding)
                        break  # 成功则跳出重试循环
                
                retry_count += 1
                if retry_count < max_retries:
                    print(f"块处理失败，重试 {retry_count}/{max_retries}...")
                    time.sleep(2)  # 等待2秒再重试
                    
            except Exception as e:
                retry_count += 1
                print(f"处理块时出错: {str(e)} (尝试 {retry_count}/{max_retries})")
                if retry_count < max_retries:
                    time.sleep(2)
                continue
    
    if not embeddings:
        raise ValueError("无法生成有效的嵌入向量（所有尝试均失败）")
    
    # 计算嵌入向量归一化
    avg_embedding = np.mean(embeddings, axis=0)
    avg_embedding_normalized = avg_embedding / np.linalg.norm(avg_embedding)
    return avg_embedding_normalized.reshape(1, -1)

def process_pifu_files(pifu_folder, sdg_path, stopwords):
    """处理批复文件夹中的所有文件，与SDG文件计算相似度"""
    # 读取SDG文件
    print("正在读取SDG文档...")
    sdg_text = read_file(sdg_path)
    if not sdg_text:
        raise ValueError("SDG文件内容为空")
    
    # 去除停用词
    sdg_text = remove_stopwords(sdg_text, stopwords)
    
    print("正在生成SDG文档的嵌入向量...")
    try:
        sdg_embedding = get_document_embedding_with_retry(sdg_text)
    except Exception as e:
        print(f"生成SDG嵌入向量失败: {str(e)}")
        return None
    
    # 准备结果列表
    results = []
    
    # 遍历批复文件夹中的所有txt文件
    for filename in os.listdir(pifu_folder):
        if filename.endswith('.txt'):
            filepath = os.path.join(pifu_folder, filename)
            try:
                print(f"\n正在处理文件: {filename}")
                pifu_text = read_file(filepath)
                if not pifu_text:
                    print(f"警告: {filename} 内容为空，跳过")
                    continue
                
                # 去除停用词
                pifu_text = remove_stopwords(pifu_text, stopwords)
                
                print(f"正在生成 {filename} 的嵌入向量...")
                pifu_embedding = get_document_embedding_with_retry(pifu_text)
                
                # 计算余弦相似度
                similarity = cosine_similarity(pifu_embedding, sdg_embedding)[0][0]
                print(f"{filename} 与SDG的余弦相似度为: {similarity:.4f}")
                
                # 添加到结果列表
                results.append({
                    'city': os.path.splitext(filename)[0],
                    'similarity': similarity
                })
                
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {str(e)}")
                continue
    
    return results

def save_to_excel(results, output_folder, output_filename):
    """将结果保存为Excel文件"""
    df = pd.DataFrame(results)
    output_path = os.path.join(output_folder, output_filename)
    df.to_excel(output_path, index=False)
    print(f"\n结果已保存到: {output_path}")

def main():
    try:
        # 加载停用词
        print("正在加载停用词表...")
        stopwords = load_stopwords(STOPWORD_FILE, CUSTOM_STOPWORDS)
        print(f"已加载 {len(stopwords)} 个停用词")
        
        # 处理所有批复文件
        results = process_pifu_files(PIFU_FOLDER, SDG_PATH, stopwords)
        
        if results is None:
            return  # 前面已经打印了错误信息
        
        if not results:
            print("没有有效的处理结果")
            return
        
        # 保存结果到Excel
        save_to_excel(results, PIFU_FOLDER, OUTPUT_EXCEL)
    
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")

if __name__ == '__main__':
    main()