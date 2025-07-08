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
PIFU_FOLDER = r"C:\Users\DELL\Desktop\sdgplanning\1data\1全部批复"

# SDG文件夹路径
SDG_FOLDER = r"C:\Users\DELL\Desktop\sdgplanning\1data\sdg"

# 主SDG文件路径
MAIN_SDG_PATH = os.path.join(SDG_FOLDER, "sdg.txt")

# 停用词文件路径
STOPWORD_FILE = r"C:\Users\DELL\Desktop\sdgplanning\1data\hit_stop.txt"

# 自定义停用词文件路径
CUSTOM_STOPWORD_FILE = r"C:\Users\DELL\Desktop\sdgplanning\1data\custom_stop.txt"

# 结果输出Excel文件名
OUTPUT_EXCEL = "similarity_result0427_100chunk.xlsx"

# 分块设置
CHUNK_SIZE = 100  # 每个分块的大致字符数
OVERLAP_SIZE = 0  # 分块之间的重叠字符数

#######################################
#           功能代码               #
#######################################

def read_file(filepath):
    """读取文件内容"""
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def load_stopwords(stopword_file, custom_stopword_file):
    """加载停用词表"""
    stopwords = set()
    
    # 从原始停用词文件加载停用词
    if os.path.exists(stopword_file):
        with open(stopword_file, 'r', encoding='utf-8') as f:
            stopwords.update(line.strip() for line in f if line.strip())
    
    # 从自定义停用词文件加载停用词
    if os.path.exists(custom_stopword_file):
        with open(custom_stopword_file, 'r', encoding='utf-8') as f:
            stopwords.update(line.strip() for line in f if line.strip())
    
    return stopwords

def remove_stopwords(text, stopwords):
    """去除停用词"""
    if not stopwords:
        return text
    
    words = text.split()
    filtered_words = [word for word in words if word not in stopwords]
    return ' '.join(filtered_words)

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap_size=OVERLAP_SIZE):
    """分块处理文本，带有重叠"""
    chunks = []
    start = 0
    end = chunk_size
    text_length = len(text)
    
    while start < text_length:
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap_size
        end = start + chunk_size
    
    return chunks

def get_embedding_for_chunk(chunk, max_retries=3):
    """获取单个分块的嵌入向量，带有重试机制"""
    retry_count = 0
    while retry_count < max_retries:
        try:
            vector = ollama.embeddings(model="bge-m3", prompt=chunk)
            if 'embedding' in vector and len(vector['embedding']) > 0:
                embedding_array = np.array(vector['embedding'])
                if not np.isnan(embedding_array).any():
                    # 对嵌入向量进行L2归一化
                    normalized_embedding = embedding_array / np.linalg.norm(embedding_array)
                    return normalized_embedding
        except Exception as e:
            print(f"处理分块时出错: {str(e)} (尝试 {retry_count+1}/{max_retries})")
        
        retry_count += 1
        if retry_count < max_retries:
            time.sleep(2)
    
    raise ValueError(f"无法生成分块的嵌入向量（所有尝试均失败）")

def get_document_embedding(text, chunk_size=CHUNK_SIZE, overlap_size=OVERLAP_SIZE):
    """获取文档的嵌入向量（所有分块的平均）"""
    chunks = chunk_text(text, chunk_size, overlap_size)
    embeddings = []
    
    for i, chunk in enumerate(chunks, 1):
        print(f"正在处理分块 {i}/{len(chunks)} (大小: {len(chunk)}字符)...")
        try:
            embedding = get_embedding_for_chunk(chunk)
            embeddings.append(embedding)
        except Exception as e:
            print(f"跳过无法处理的分块 {i}: {str(e)}")
            continue
    
    if not embeddings:
        raise ValueError("无法生成任何有效的嵌入向量")
    
    # 计算所有分块嵌入向量的平均值并归一化
    avg_embedding = np.mean(embeddings, axis=0)
    avg_embedding_normalized = avg_embedding / np.linalg.norm(avg_embedding)
    return avg_embedding_normalized.reshape(1, -1), len(embeddings)

def calculate_chunked_similarity(pifu_text, sdg_embedding, chunk_size=CHUNK_SIZE, overlap_size=OVERLAP_SIZE):
    """计算分块相似度并取平均"""
    chunks = chunk_text(pifu_text, chunk_size, overlap_size)
    similarities = []
    
    for i, chunk in enumerate(chunks, 1):
        print(f"正在计算分块 {i}/{len(chunks)} 的相似度...")
        try:
            chunk_embedding = get_embedding_for_chunk(chunk)
            similarity = cosine_similarity(chunk_embedding.reshape(1, -1), sdg_embedding)[0][0]
            similarities.append(similarity)
        except Exception as e:
            print(f"跳过无法计算相似度的分块 {i}: {str(e)}")
            continue
    
    if not similarities:
        return 0.0, 0
    
    avg_similarity = np.mean(similarities)
    return avg_similarity, len(similarities)

def load_sdg_embeddings(sdg_folder, stopwords, chunk_size=CHUNK_SIZE, overlap_size=OVERLAP_SIZE):
    """加载所有SDG文本并生成嵌入向量"""
    sdg_embeddings = {}
    
    # 首先处理主SDG文件
    main_sdg_path = os.path.join(sdg_folder, "sdg.txt")
    if os.path.exists(main_sdg_path):
        print("正在读取主SDG文档...")
        main_sdg_text = read_file(main_sdg_path)
        main_sdg_text = remove_stopwords(main_sdg_text, stopwords)
        print("正在生成主SDG文档的嵌入向量...")
        sdg_embeddings['total'], num_chunks = get_document_embedding(main_sdg_text, chunk_size, overlap_size)
        print(f"主SDG文档分为 {num_chunks} 个分块处理")
    
    # 然后处理其他SDG副本文件
    for filename in os.listdir(sdg_folder):
        if filename.startswith("sdg - 副本 (") and filename.endswith(".txt"):
            try:
                # 提取SDG编号 (1, 2, 3...)
                sdg_num = filename.split("(")[1].split(")")[0]
                sdg_key = f"sdg{sdg_num}"
                
                filepath = os.path.join(sdg_folder, filename)
                print(f"正在读取SDG文档: {filename}...")
                sdg_text = read_file(filepath)
                sdg_text = remove_stopwords(sdg_text, stopwords)
                print(f"正在生成{filename}的嵌入向量...")
                sdg_embeddings[sdg_key], num_chunks = get_document_embedding(sdg_text, chunk_size, overlap_size)
                print(f"{filename} 分为 {num_chunks} 个分块处理")
            except Exception as e:
                print(f"处理SDG文件 {filename} 时出错: {str(e)}")
                continue
    
    return sdg_embeddings

def process_pifu_files(pifu_folder, sdg_embeddings, stopwords, chunk_size=CHUNK_SIZE, overlap_size=OVERLAP_SIZE):
    """处理批复文件夹中的所有文件，与所有SDG文件计算分块相似度"""
    results = []
    
    for filename in os.listdir(pifu_folder):
        if filename.endswith('.txt'):
            filepath = os.path.join(pifu_folder, filename)
            try:
                print(f"\n正在处理文件: {filename}")
                pifu_text = read_file(filepath)
                if not pifu_text:
                    print(f"警告: {filename} 内容为空，跳过")
                    continue
                
                pifu_text = remove_stopwords(pifu_text, stopwords)
                
                # 初始化结果字典
                result = {'city': os.path.splitext(filename)[0]}
                chunk_counts = {}
                
                # 计算与每个SDG的分块相似度
                for sdg_name, sdg_embedding in sdg_embeddings.items():
                    print(f"计算与 {sdg_name} 的相似度...")
                    similarity, num_chunks = calculate_chunked_similarity(pifu_text, sdg_embedding, chunk_size, overlap_size)
                    result[sdg_name] = similarity
                    chunk_counts[sdg_name] = num_chunks
                    print(f"{filename} 与 {sdg_name} 的平均相似度: {similarity:.4f} (基于 {num_chunks} 个分块)")
                
                # 添加分块计数信息
                result['chunk_info'] = str(chunk_counts)
                results.append(result)
                
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {str(e)}")
                continue
    
    return results

def save_to_excel(results, output_folder, output_filename):
    """将结果保存为Excel文件"""
    # 确保列的顺序：city, total, sdg1, sdg2, ...
    columns = ['city']
    if results:
        # 获取所有可能的sdg列名并按数字排序
        sdg_columns = [col for col in results[0].keys() if col not in ['city', 'chunk_info']]
        # 确保total在最前面
        if 'total' in sdg_columns:
            columns.append('total')
            sdg_columns.remove('total')
        # 对其他sdg列按数字排序
        sdg_columns_sorted = sorted(sdg_columns, key=lambda x: int(x[3:])) if sdg_columns else []
        columns.extend(sdg_columns_sorted)
        columns.append('chunk_info')  # 添加分块信息列
    
    df = pd.DataFrame(results)[columns]
    output_path = os.path.join(output_folder, output_filename)
    df.to_excel(output_path, index=False)
    print(f"\n结果已保存到: {output_path}")

def main():
    try:
        # 加载停用词
        print("正在加载停用词表...")
        stopwords = load_stopwords(STOPWORD_FILE, CUSTOM_STOPWORD_FILE)
        print(f"已加载 {len(stopwords)} 个停用词")
        
        # 加载所有SDG嵌入向量
        print("\n正在加载SDG文档...")
        sdg_embeddings = load_sdg_embeddings(SDG_FOLDER, stopwords, CHUNK_SIZE, OVERLAP_SIZE)
        if not sdg_embeddings:
            raise ValueError("没有可用的SDG嵌入向量")
        
        print("\n可用的SDG嵌入向量:")
        for sdg_name in sdg_embeddings.keys():
            print(f"- {sdg_name}")
        
        # 处理所有批复文件
        results = process_pifu_files(PIFU_FOLDER, sdg_embeddings, stopwords, CHUNK_SIZE, OVERLAP_SIZE)
        
        if not results:
            print("没有有效的处理结果")
            return
        
        # 保存结果到Excel
        save_to_excel(results, PIFU_FOLDER, OUTPUT_EXCEL)
    
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")

if __name__ == '__main__':
    main()