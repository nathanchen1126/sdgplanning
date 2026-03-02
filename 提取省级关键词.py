import os
import time
import requests
from collections import Counter

# ==========================================
# 配置区
# ==========================================
API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-6e8113f768cd42768058ce6dc6ef3401")
API_URL = "https://api.deepseek.com/v1/chat/completions"
TEMPERATURE = 0.8

INPUT_DIR = r"D:\省级国空批复txt"
OUTPUT_FILE = os.path.join(INPUT_DIR, "全局Top10关键词.txt")

SYSTEM_PROMPT = """您是一位专业的规划文本分析师。

请从文本中提取与“可持续发展目标”相关的最重要关键词。
仅返回关键词列表。
每行一个关键词。
不要解释。
"""


# ==========================================
# 调用 API 提取关键词
# ==========================================
def extract_keywords(text):
    headers = {"Authorization": f"Bearer {API_KEY}"}

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": TEMPERATURE,
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    api_response = response.json()["choices"][0]["message"]["content"]
    keywords = [k.strip() for k in api_response.split("\n") if k.strip()]
    return keywords


# ==========================================
# 主程序
# ==========================================
def main():
    if API_KEY == "your-deepseek-api-key":
        print("请设置你的 API KEY")
        return

    all_keywords = []

    txt_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".txt")]

    if not txt_files:
        print("未找到 txt 文件")
        return

    print(f"共发现 {len(txt_files)} 个文件，开始提取关键词...\n")

    for file_name in txt_files:
        file_path = os.path.join(INPUT_DIR, file_name)
        print(f"处理: {file_name}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            keywords = extract_keywords(content)
            all_keywords.extend(keywords)

            time.sleep(1)

        except Exception as e:
            print(f"出错: {e}")

    # ======================================
    # 统计频率并取 Top 10
    # ======================================
    counter = Counter(all_keywords)
    top10 = counter.most_common(11)

    # 保存结果
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("全局最关键的10个关键词：\n\n")
        for word, freq in top10:
            f.write(f"{word}  （出现 {freq} 次）\n")

    print("\n处理完成！")
    print(f"结果已保存至: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()