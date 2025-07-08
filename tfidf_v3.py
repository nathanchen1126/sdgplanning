# 直接把关键词添加到分词器
import os
import math
import jieba
import pandas as pd
from collections import defaultdict

class TFIDFProcessor:
    def __init__(self, config):
        """
        初始化处理器
        :param config: 包含所有配置参数的字典
        """
        self.config = config
        self.stopwords = self._load_stopwords()
        
    def _load_stopwords(self):
        """加载停用词表"""
        if not os.path.exists(self.config['stopwords_path']):
            print(f"未找到停用词文件 {self.config['stopwords_path']}，将继续处理但不使用停用词过滤")
            return set()
            
        with open(self.config['stopwords_path'], 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())

    def _load_keywords_to_jieba(self, keyword_file):
        """加载关键词文件到jieba分词器"""
        if not os.path.exists(keyword_file):
            raise FileNotFoundError(f"关键词文件不存在: {keyword_file}")
            
        loaded_words = set()
        with open(keyword_file, 'r', encoding='utf-8') as f:
            for line in f:
                for word in line.replace(',', ' ').split():
                    word = word.strip()
                    if word and word not in loaded_words:
                        jieba.add_word(word, freq=self.config.get('term_freq', 1000))
                        loaded_words.add(word)
        print(f"已从 {os.path.basename(keyword_file)} 加载 {len(loaded_words)} 个词语到分词器")
        return loaded_words

    def process_single(self, keyword_file, corpus_dir, output_file):
        """处理单个数据集（top或bottom）"""
        # 1. 加载关键词到jieba
        keywords = self._load_keywords_to_jieba(keyword_file)
        
        # 2. 检查语料库目录
        if not os.path.exists(corpus_dir):
            raise FileNotFoundError(f"语料库目录不存在: {corpus_dir}")

        # 3. 分词处理
        corpus = []
        for filename in os.listdir(corpus_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(corpus_dir, filename), 'r', encoding='utf-8') as f:
                    words = [w for w in jieba.cut(f.read()) 
                            if w not in self.stopwords and w.strip()]
                    corpus.append(words)

        # 4. 计算TF-IDF
        tfidf_results = self._calculate_tfidf(keywords, corpus)
        
        # 5. 保存结果
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        pd.DataFrame([
            {"Keyword": k, "TF-IDF": v[0], "IDF": v[1]} 
            for k, v in tfidf_results.items()
        ]).to_excel(output_file, index=False)
        print(f"结果已保存到 {os.path.abspath(output_file)}")

    def _calculate_tfidf(self, keywords, corpus):
        """计算TF-IDF值"""
        doc_freq = defaultdict(int)
        total_docs = len(corpus)
        
        # 计算文档频率
        for doc in corpus:
            unique_words = set(doc)
            for word in keywords:
                if word in unique_words:
                    doc_freq[word] += 1

        # 计算TF-IDF
        results = {}
        for word in keywords:
            idf = math.log((total_docs + 1) / (doc_freq.get(word, 0) + 0.5))  # 平滑处理
            total_tfidf = sum(doc.count(word)/len(doc)*idf for doc in corpus if doc)
            avg_tfidf = total_tfidf / total_docs if total_docs else 0
            results[word] = (avg_tfidf, idf)
        
        return results

    def process_all(self):
        """处理所有数据集（top和bottom）"""
        print("="*50)
        print("开始处理bottom50%数据...")
        self.process_single(
            keyword_file=self.config['bottom_keywords_file'],
            corpus_dir=self.config['bottom_corpus_dir'],
            output_file=self.config['bottom_output_file']
        )
        
        print("\n" + "="*50)
        print("开始处理top50%数据...")
        self.process_single(
            keyword_file=self.config['top_keywords_file'],
            corpus_dir=self.config['top_corpus_dir'],
            output_file=self.config['top_output_file']
        )
        
        print("\n所有处理完成！")

# ===================== 使用示例 =====================
if __name__ == "__main__":
    # 配置参数
    config = {
        # 文件路径配置
        'bottom_keywords_file': r"D:/1sdgplanning/3result/bottom50%_keywords.txt",
        'bottom_corpus_dir': r"D:/1sdgplanning/3result/bottom50%",
        'bottom_output_file': r"D:/1sdgplanning/3result/bottom50_tfidf.xlsx",
        
        'top_keywords_file': r"D:/1sdgplanning/3result/top50%_keywords.txt",
        'top_corpus_dir': r"D:/1sdgplanning/3result/top50%",
        'top_output_file': r"D:/1sdgplanning/3result/top50_tfidf.xlsx",
        
        # 可选参数
        'stopwords_path': r"D:\1sdgplanning\1data\custom_stop.txt",
        'term_freq': 1000,  # 添加词语到jieba的词频
    }

    # 执行处理
    try:
        processor = TFIDFProcessor(config)
        processor.process_all()
    except Exception as e:
        print(f"处理失败: {str(e)}")