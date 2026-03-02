import ollama
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import pandas as pd
import time
from itertools import combinations
from collections import Counter
from scipy.stats import hypergeom

#######################################
#           可配置路径设置             #
#######################################

# 批复文件夹路径（请替换为你的实际路径）
PIFU_FOLDER = r"C:\Users\DELL\Desktop\sdgplanning\1data\1全部批复"

# SDG文件夹路径（请替换为你的实际路径）
SDG_FOLDER = r"C:\Users\DELL\Desktop\sdgplanning\1data\sdg"

# 停用词文件路径
STOPWORD_FILE = r"C:\Users\DELL\Desktop\sdgplanning\1data\hit_stop.txt"
CUSTOM_STOPWORD_FILE = r"C:\Users\DELL\Desktop\sdgplanning\1data\custom_stop.txt"

# 结果输出文件名
OUTPUT_STATISTICAL_EDGES = "sdg_statistical_edges_topk.xlsx"

# 分块设置
CHUNK_SIZE = 100  # 每个分块的大致字符数
OVERLAP_SIZE = 0  # 分块之间的重叠字符数

# ★ 核心参数：Top-K 提取法 ★
TOP_K_SDGS = 2          # 每个文本块最多提取的最相关 SDG 数量（建议设为2，代表一对核心共现）
BASE_THRESHOLD = 0.30   # 极低的安全底线，仅用于过滤与任何SDG都毫无关系的废话文本块

#######################################
#           基础功能代码               #
#######################################

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def load_stopwords(stopword_file, custom_stopword_file):
    stopwords = set()
    if os.path.exists(stopword_file):
        with open(stopword_file, 'r', encoding='utf-8') as f:
            stopwords.update(line.strip() for line in f if line.strip())
    if os.path.exists(custom_stopword_file):
        with open(custom_stopword_file, 'r', encoding='utf-8') as f:
            stopwords.update(line.strip() for line in f if line.strip())
    return stopwords

def remove_stopwords(text, stopwords):
    if not stopwords:
        return text
    words = text.split()
    filtered_words = [word for word in words if word not in stopwords]
    return ' '.join(filtered_words)

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap_size=OVERLAP_SIZE):
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
    retry_count = 0
    while retry_count < max_retries:
        try:
            vector = ollama.embeddings(model="bge-m3", prompt=chunk)
            if 'embedding' in vector and len(vector['embedding']) > 0:
                embedding_array = np.array(vector['embedding'])
                if not np.isnan(embedding_array).any():
                    # 归一化
                    normalized_embedding = embedding_array / np.linalg.norm(embedding_array)
                    return normalized_embedding
        except Exception as e:
            pass # 静默重试
        retry_count += 1
        if retry_count < max_retries:
            time.sleep(2)
    raise ValueError(f"无法生成分块的嵌入向量")

def load_sdg_embeddings(sdg_folder, stopwords):
    """加载所有SDG文本并生成基准嵌入向量"""
    sdg_embeddings = {}
    for filename in os.listdir(sdg_folder):
        if filename.startswith("sdg - 副本 (") and filename.endswith(".txt"):
            try:
                sdg_num = filename.split("(")[1].split(")")[0]
                sdg_key = f"sdg{sdg_num}"
                filepath = os.path.join(sdg_folder, filename)
                
                sdg_text = read_file(filepath)
                sdg_text = remove_stopwords(sdg_text, stopwords)
                
                chunks = chunk_text(sdg_text, CHUNK_SIZE, OVERLAP_SIZE)
                chunk_embs = [get_embedding_for_chunk(c) for c in chunks]
                avg_emb = np.mean(chunk_embs, axis=0)
                avg_emb_normalized = avg_emb / np.linalg.norm(avg_emb)
                
                sdg_embeddings[sdg_key] = avg_emb_normalized.reshape(1, -1)
                print(f"已加载 {sdg_key} 基准向量")
            except Exception as e:
                print(f"处理SDG文件 {filename} 时出错: {str(e)}")
    return sdg_embeddings

#######################################
#     Top-K 共现提取核心代码            #
#######################################

def get_chunk_sdg_occurrences_topk(chunk, sdg_embeddings, top_k=TOP_K_SDGS, base_threshold=BASE_THRESHOLD):
    """
    不依赖硬性高阈值，提取当前文本块中最相关的 Top-K 个 SDG。
    """
    try:
        chunk_embedding = get_embedding_for_chunk(chunk).reshape(1, -1)
        similarity_scores = {}
        
        for sdg_name, sdg_embedding in sdg_embeddings.items():
            sim = cosine_similarity(chunk_embedding, sdg_embedding)[0][0]
            similarity_scores[sdg_name] = sim
            
        # 1. 剔除绝对无相关性的噪音（极低的基准线）
        valid_scores = {k: v for k, v in similarity_scores.items() if v >= base_threshold}
        
        if not valid_scores:
            return []
            
        # 2. 按相似度从大到小排序
        sorted_sdgs = sorted(valid_scores.items(), key=lambda item: item[1], reverse=True)
        
        # 3. 提取排名前 K 个的 SDG
        top_sdgs = [item[0] for item in sorted_sdgs[:top_k]]
        return top_sdgs
        
    except Exception as e:
        return []

def process_corpus_for_cooccurrences(pifu_folder, sdg_embeddings, stopwords):
    """
    处理整个语料库，提取所有分块中的SDG共现记录，并计算切分的总块数
    """
    all_valid_occurrences = [] # 存储所有命中了至少1个SDG的分块记录
    total_chunks = 0           # 整体样本量 N
    
    for filename in os.listdir(pifu_folder):
        if filename.endswith('.txt'):
            filepath = os.path.join(pifu_folder, filename)
            print(f"正在扫描文件: {filename} 中的共现特征...")
            try:
                pifu_text = read_file(filepath)
                if not pifu_text:
                    continue
                pifu_text = remove_stopwords(pifu_text, stopwords)
                chunks = chunk_text(pifu_text, CHUNK_SIZE, OVERLAP_SIZE)
                total_chunks += len(chunks) # 累加总分块数
                
                for i, chunk in enumerate(chunks, 1):
                    # 使用 Top-K 提取法
                    occurred_sdgs = get_chunk_sdg_occurrences_topk(chunk, sdg_embeddings)
                    # 只有命中至少1个SDG时，才记录
                    if len(occurred_sdgs) > 0:
                        all_valid_occurrences.append(occurred_sdgs)
                            
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {str(e)}")
                
    print(f"\n扫描完成！共扫描 {total_chunks} 个文本块，其中 {len(all_valid_occurrences)} 个文本块蕴含有效语义。")
    return all_valid_occurrences, total_chunks

#######################################
#     超几何分布检验与OI计算代码        #
#######################################

def build_statistical_cooccurrence_outputs(all_occurrences, total_chunks, output_folder):
    """
    基于所有出现记录，计算超几何分布的 P值 和 重叠指数(OI)，
    并分类为 协同(Synergy)、权衡(Tension) 或 随机(Random)
    """
    sdg_counts = Counter()          # 统计单个SDG的出现总频次
    co_occurrence_counts = Counter() # 统计SDG两两共现的频次
    
    # 遍历所有分块的命中记录
    for sdg_list in all_occurrences:
        # 单次出现统计
        for sdg in sdg_list:
            sdg_counts[sdg] += 1
            
        # 提取两两组合进行统计（排序防止(A,B)和(B,A)重复）
        sdg_list_sorted = sorted(sdg_list, key=lambda x: int(x.replace('sdg', '')))
        for pair in combinations(sdg_list_sorted, 2):
            co_occurrence_counts[pair] += 1

    all_sdgs = sorted(list(sdg_counts.keys()), key=lambda x: int(x.replace('sdg', '')))
    edges_data = []
    
    N = total_chunks # 总体样本量：所有切分的文本块总数
    
    # 遍历所有可能的SDG两两组合进行统计学检验
    for sdg_a, sdg_b in combinations(all_sdgs, 2):
        K = sdg_counts.get(sdg_a, 0)
        n = sdg_counts.get(sdg_b, 0)
        k = co_occurrence_counts.get((sdg_a, sdg_b), 0) # 实际观测共现次数
        
        if K == 0 or n == 0:
            continue
            
        # 1. 预期共现次数 (Expected value)
        E = (K * n) / N
        
        # 2. 重叠指数 (Overlap Index, OI)
        if k >= E:
            max_possible = min(K, n)
            denominator = max_possible - E
            OI = (k - E) / denominator if denominator > 0 else 0.0
        else:
            denominator = E
            OI = (k - E) / denominator if denominator > 0 else 0.0
            
        # 3. 超几何分布 P 值计算
        if k >= E:
            # 实际大于预期：右尾概率 P(X >= k)
            p_val = hypergeom.sf(k - 1, N, K, n)
        else:
            # 实际小于预期：左尾概率 P(X <= k)
            p_val = hypergeom.cdf(k, N, K, n)
            
        # 4. 判定类别 (Synergy / Tension / Neutral)
        relationship = "Neutral (Random)"
        if p_val < 0.05:
            if OI > 0.1:
                relationship = "Synergy (协同/捆绑)"
            elif OI < -0.1:
                relationship = "Tension (张力/权衡)"
        
        edges_data.append({
            'Source': sdg_a,
            'Target': sdg_b,
            'Observed_Co_occur(k)': k,
            'Expected_Co_occur(E)': round(E, 2),
            'Overlap_Index(OI)': round(OI, 4),
            'P_Value': format(p_val, '.4e'), # 科学计数法格式化
            'Relationship': relationship
        })
    
    # 输出保存
    edges_df = pd.DataFrame(edges_data)
    
    # 按关系类型和 OI 绝对值大小排序，最显著的关系排最前面
    if not edges_df.empty:
        edges_df['Abs_OI'] = edges_df['Overlap_Index(OI)'].abs()
        # 确保包含列后正常排序
        edges_df = edges_df.sort_values(by=['Relationship', 'Abs_OI'], ascending=[True, False])
        edges_df = edges_df.drop(columns=['Abs_OI'])
        
    edges_path = os.path.join(output_folder, OUTPUT_STATISTICAL_EDGES)
    edges_df.to_excel(edges_path, index=False)
    
    print(f"\n==========================================")
    print(f"统计检验完成！结果已保存至: {edges_path}")
    print("关系类型统计：")
    print(edges_df['Relationship'].value_counts() if not edges_df.empty else "无结果")
    print(f"==========================================\n")

#######################################
#               主程序                 #
#######################################

def main():
    try:
        # 1. 加载停用词
        print("正在加载停用词表...")
        stopwords = load_stopwords(STOPWORD_FILE, CUSTOM_STOPWORD_FILE)
        
        # 2. 加载SDG基准向量
        print("\n正在生成SDG基准嵌入向量...")
        sdg_embeddings = load_sdg_embeddings(SDG_FOLDER, stopwords)
        if not sdg_embeddings:
            raise ValueError("没有可用的SDG嵌入向量，请检查路径。")
            
        # 3. 处理语料库，提取分块共现特征并统计总切块数
        print(f"\n开始扫描城市规划文本... (采用 Top-{TOP_K_SDGS} 动态特征提取)")
        all_occurrences, total_chunks = process_corpus_for_cooccurrences(PIFU_FOLDER, sdg_embeddings, stopwords)
        
        # 4. 生成超几何检验统计网络并保存
        if total_chunks > 0 and len(all_occurrences) > 0:
            print(f"\n开始进行超几何分布检验 (总文本块 N = {total_chunks})...")
            build_statistical_cooccurrence_outputs(all_occurrences, total_chunks, PIFU_FOLDER)
        else:
            print("\n未能提取到任何SDG命中记录或文本块为0。请检查数据。")
            
    except Exception as e:
        print(f"程序运行出错: {str(e)}")

if __name__ == '__main__':
    main()