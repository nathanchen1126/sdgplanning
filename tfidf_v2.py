# -利用deepseek API提取关键词，并计算TF-IDF值，生成关键词表*
import os
import math
import jieba
import requests
import pandas as pd
from collections import defaultdict

# ===================== 配置参数 =====================
BASE_PATH = r"D:/1sdgplanning/3result/"
STOPWORDS_PATH = r"D:\1sdgplanning\1data\custom_stop.txt"

# DeepSeek API配置
API_KEY = "sk-6e8113f768cd42768058ce6dc6ef3401"
API_URL = "https://api.deepseek.com/v1/chat/completions"
SYSTEM_PROMPT = """我准备创建一个关于“国土空间规划文本”的分词表，要求：
1. 你帮我提取其中的工作内容相关的专有名词，帮助我更精确地提取"国土空间规划"相关的词汇。你只需要返回词汇即可，不应该回答任何专有词汇之外的其他内容
2. 保持专有名词完整（如"生态保护修复""城乡融合"不拆分）
3. 拆分可分解的复合词（如"城乡融合发展试验区"拆为"城乡融合 发展 试验区"）
4. 专有名词不拆解（如人与自然和谐共生 是一个专有名词，无法拆分，因此不拆分，输出 人与自然和谐共生）
5. 只需返回词汇，用空格分隔，不要解释"""

# ===================== 核心功能 =====================
class TFIDFProcessor:
    def __init__(self):
        self.stopwords = self.load_stopwords()
        self.api_called = False  # 避免重复调用API

    def load_stopwords(self):
        """加载停用词表"""
        try:
            with open(STOPWORDS_PATH, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f if line.strip())
        except FileNotFoundError:
            print("未找到停用词文件，将继续处理但不使用停用词过滤")
            return set()

    def extract_terms_from_text(self, text):
        """调用API提取专有名词"""
        if not text.strip() or self.api_called:
            return set()
            
        try:
            response = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": text}
                    ],
                    "temperature": 1.0
                },
                timeout=30
            )
            response.raise_for_status()
            terms = response.json()['choices'][0]['message']['content'].split()
            self.api_called = True
            return set(term for term in terms if term not in self.stopwords)
        except Exception as e:
            print(f"API调用失败: {e}")
            return set()

    def process_corpus(self, corpus_dir, keywords_file, output_file):
        """完整处理流程"""
        # 1. 合并语料库文本
        combined_text = self.read_all_texts(corpus_dir)
        if not combined_text:
            print(f"语料库目录 {corpus_dir} 无有效文本")
            return

        # 2. 提取专有名词并添加到jieba
        custom_terms = self.extract_terms_from_text(combined_text)
        for term in custom_terms:
            jieba.add_word(term, freq=1000)  # 设置较高词频确保能正确切分
        print(f"已添加 {len(custom_terms)} 个专有名词到分词器")

        # 3. 加载关键词
        keywords = self.load_keywords(keywords_file)
        if not keywords:
            print("无有效关键词，终止处理")
            return

        # 4. 分词处理
        corpus = []
        for filename in os.listdir(corpus_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(corpus_dir, filename), 'r', encoding='utf-8') as f:
                    words = [w for w in jieba.cut(f.read()) if w not in self.stopwords]
                    corpus.append(words)

        # 5. 计算TF-IDF
        tfidf_results = self.calculate_tfidf(keywords, corpus)
        
        # 6. 保存结果
        pd.DataFrame([
            {"Keyword": k, "TF-IDF": v[0], "IDF": v[1]} 
            for k, v in tfidf_results.items()
        ]).to_excel(output_file, index=False)
        print(f"结果已保存到 {output_file}")

    def read_all_texts(self, dir_path):
        """读取目录下所有文本内容"""
        combined = ""
        try:
            for filename in os.listdir(dir_path):
                if filename.endswith(".txt"):
                    with open(os.path.join(dir_path, filename), 'r', encoding='utf-8') as f:
                        combined += f.read() + "\n"
            return combined
        except Exception as e:
            print(f"读取语料库出错: {e}")
            return ""

    def load_keywords(self, filepath):
        """加载关键词文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return list(set(word.strip() for line in f for word in line.split(',') if word.strip()))
        except FileNotFoundError:
            print(f"关键词文件 {filepath} 未找到")
            return []

    def calculate_tfidf(self, keywords, corpus):
        """计算TF-IDF值"""
        # 文档频率计算
        doc_freq = defaultdict(int)
        total_docs = len(corpus)
        
        for doc in corpus:
            unique_words = set(doc)
            for word in keywords:
                if word in unique_words:
                    doc_freq[word] += 1

        # TF-IDF计算
        results = {}
        for word in keywords:
            idf = math.log(total_docs / (doc_freq.get(word, 0.5)))  # 平滑处理
            total_tfidf = sum(doc.count(word)/len(doc)*idf for doc in corpus if doc)
            avg_tfidf = total_tfidf / total_docs if total_docs else 0
            results[word] = (avg_tfidf, idf)
        
        return results

# ===================== 主程序 =====================
if __name__ == "__main__":
    processor = TFIDFProcessor()
    
    # 处理bottom50%
    print("\n" + "="*30 + " 处理bottom50%数据 " + "="*30)
    processor.process_corpus(
        corpus_dir=os.path.join(BASE_PATH, "bottom50%"),
        keywords_file=os.path.join(BASE_PATH, "bottom50%_keywords.txt"),
        output_file=os.path.join(BASE_PATH, "bottom50_tfidf.xlsx")
    )
    
    # 处理top50%
    print("\n" + "="*30 + " 处理top50%数据 " + "="*30)
    processor.process_corpus(
        corpus_dir=os.path.join(BASE_PATH, "top50%"),
        keywords_file=os.path.join(BASE_PATH, "top50%_keywords.txt"),
        output_file=os.path.join(BASE_PATH, "top50_tfidf.xlsx")
    )
    
    print("\n处理完成！")