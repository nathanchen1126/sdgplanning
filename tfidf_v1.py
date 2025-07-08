# -*- coding: utf-8 -*-
import os
import math
import jieba
import pandas as pd
from collections import defaultdict

# ===================== 可配置参数 =====================
base_path = r"D:/1sdgplanning/3result/"
bottom_keywords_path = os.path.join(base_path, "bottom50%_keywords.txt")  # 单个关键词文件
top_keywords_path = os.path.join(base_path, "top50%_keywords.txt")       # 单个关键词文件
bottom_paragraphs_path = os.path.join(base_path, "bottom50%")           # 语料库目录
top_paragraphs_path = os.path.join(base_path, "top50%")                 # 语料库目录
stopwords_path = r"D:\1sdgplanning\1data\custom_stop.txt"
output_path = base_path

bottom_output_filename = "bottom50_tfidf.xlsx"
top_output_filename = "top50_tfidf.xlsx"
# =====================================================

def load_stopwords(stopwords_file):
    """加载停用词列表"""
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        stopwords = [line.strip() for line in f if line.strip()]
    return set(stopwords)

def load_keywords(keywords_file, stopwords=None):
    """从单个文件加载关键词（整合并去重）"""
    keywords = set()
    try:
        with open(keywords_file, 'r', encoding='utf-8') as f:
            for line in f:
                # 假设关键词以逗号分隔，或者每行一个关键词
                for word in line.strip().split(','):
                    word = word.strip()
                    if word and (stopwords is None or word not in stopwords):
                        keywords.add(word)
        return list(keywords)
    except FileNotFoundError:
        print(f"关键词文件 {keywords_file} 未找到，请检查路径")
        return []

def load_corpus(paragraphs_dir, stopwords=None):
    """加载语料库文档"""
    corpus = []
    try:
        for filename in os.listdir(paragraphs_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(paragraphs_dir, filename), 'r', encoding='utf-8') as f:
                    text = f.read()
                    words = list(jieba.cut(text))
                    if stopwords:
                        words = [word for word in words if word not in stopwords]
                    corpus.append(words)
        return corpus
    except FileNotFoundError:
        print(f"语料库目录 {paragraphs_dir} 未找到，请检查路径")
        return []

def check_keyword_presence(keywords, corpus):
    """检查关键词是否出现在语料库中"""
    present_keywords = set()
    absent_keywords = set()
    
    # 构建语料库中所有词的集合
    all_corpus_words = set()
    for doc in corpus:
        all_corpus_words.update(doc)
    
    # 检查每个关键词
    for word in keywords:
        if word in all_corpus_words:
            present_keywords.add(word)
        else:
            absent_keywords.add(word)
    
    return present_keywords, absent_keywords

def calculate_tfidf(keywords, corpus):
    """计算TF-IDF值"""
    # 首先检查哪些关键词实际出现在语料库中
    present_keywords, absent_keywords = check_keyword_presence(keywords, corpus)
    
    print("\n关键词检查结果:")
    print(f"总关键词数量: {len(keywords)}")
    print(f"出现在语料库中的关键词数量: {len(present_keywords)}")
    print(f"未出现在语料库中的关键词数量: {len(absent_keywords)}")
    
    if len(absent_keywords) > 0:
        print("\n未出现在语料库中的关键词示例(最多显示10个):")
        print(list(absent_keywords)[:10])
    
    # 只计算实际出现的关键词
    valid_keywords = list(present_keywords)
    
    # 计算文档频率
    doc_freq = defaultdict(int)
    total_docs = len(corpus)
    
    for doc in corpus:
        unique_words_in_doc = set(doc)
        for word in valid_keywords:
            if word in unique_words_in_doc:
                doc_freq[word] += 1
    
    # 计算TF-IDF
    tfidf_results = {}
    
    for word in valid_keywords:
        idf = math.log(total_docs / (1 + doc_freq.get(word, 0)))
        
        total_tfidf = 0
        for doc in corpus:
            tf = doc.count(word) / len(doc) if len(doc) > 0 else 0
            total_tfidf += tf * idf
        
        avg_tfidf = total_tfidf / total_docs if total_docs > 0 else 0
        tfidf_results[word] = {
            'TF-IDF': avg_tfidf,
            'IDF': idf
        }
    
    return tfidf_results

def save_results(tfidf_dict, output_file):
    """保存结果到文件"""
    data = []
    for word, metrics in tfidf_dict.items():
        data.append({
            'Keyword': word,
            'TF-IDF': metrics['TF-IDF'],
            'IDF': metrics['IDF']
        })
    
    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False)
    print(f"结果已保存到 {output_file}")

def main():
    # 加载停用词
    try:
        stopwords = load_stopwords(stopwords_path)
        print(f"已加载 {len(stopwords)} 个停用词")
    except FileNotFoundError:
        print("未找到停用词文件，将继续处理但不使用停用词过滤")
        stopwords = None
    
    # 处理bottom50%
    print("\n正在处理bottom50%数据...")
    bottom_keywords = load_keywords(bottom_keywords_path, stopwords)
    if not bottom_keywords:
        print("无法加载bottom50%关键词，跳过处理")
    else:
        bottom_corpus = load_corpus(bottom_paragraphs_path, stopwords)
        if bottom_corpus:
            bottom_tfidf = calculate_tfidf(bottom_keywords, bottom_corpus)
            save_results(bottom_tfidf, os.path.join(output_path, bottom_output_filename))
        else:
            print("无法加载bottom50%语料库，跳过处理")
    
    # 处理top50%
    print("\n正在处理top50%数据...")
    top_keywords = load_keywords(top_keywords_path, stopwords)
    if not top_keywords:
        print("无法加载top50%关键词，跳过处理")
    else:
        top_corpus = load_corpus(top_paragraphs_path, stopwords)
        if top_corpus:
            top_tfidf = calculate_tfidf(top_keywords, top_corpus)
            save_results(top_tfidf, os.path.join(output_path, top_output_filename))
        else:
            print("无法加载top50%语料库，跳过处理")
    
    print("\n所有处理任务已完成!")

if __name__ == "__main__":
    main()