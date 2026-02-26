<<<<<<< HEAD
import os
import random
import requests
import json
import time
import pandas as pd

# --- 1. 配置参数 ---

# DeepSeek API 配置
API_KEY = "sk-6e8113f768cd42768058ce6dc6ef3401" # 您的DeepSeek API密钥
API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_NAME = "deepseek-chat"
TEMPERATURE = 0.5

# 数据和实验配置
PLANNING_TEXTS_DIR = r"D:\1sdgplanning\1data\1全部批复"
SCORE_FILE_PATH = r"D:\1sdgplanning\1data\similarity_total.xlsx"
NUM_TRIPLETS_TO_TEST = 20
OUTPUT_EXCEL_FILE = "verification_results.xlsx"

# --- 2. 核心功能函数 ---

def load_scores(filepath: str) -> dict:
    """从Excel加载预计算的分数到字典中。"""
    print(f"正在从 '{filepath}' 加载分数...")
    try:
        df = pd.read_excel(filepath)
        # 确保列名正确
        if 'city' not in df.columns or 'total' not in df.columns:
            print(f"错误：Excel文件中必须包含 'city' 和 'total' 列。")
            return None
        # 创建字典，key为city，value为total score
        score_dict = pd.Series(df.total.values, index=df.city).to_dict()
        print(f"成功加载 {len(score_dict)} 个地区的分数。")
        return score_dict
    except FileNotFoundError:
        print(f"错误：分数文件 '{filepath}' 未找到。")
        return None
    except Exception as e:
        print(f"加载Excel文件时出错: {e}")
        return None

# (get_all_text_files, read_text_content, compare_texts_with_llm 函数与之前版本相同)
def get_all_text_files(directory: str) -> list:
    if not os.path.isdir(directory): return []
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.txt')]

def read_text_content(filepath: str) -> str:
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return f.read()
    except Exception: return None

def compare_texts_with_llm(text_a: str, text_b: str) -> str:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    prompt = f"请判断以下“文本A”和“文本B”哪一份更符合联合国可持续发展目标（SDGs）。你的回答必须且只能是单个字母：“A”或“B”。\n\n文本A:\n{text_a[:1500]}\n\n文本B:\n{text_b[:1500]}"
    payload = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}], "temperature": TEMPERATURE, "max_tokens": 5}
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=60)
        response.raise_for_status()
        result = response.json()['choices'][0]['message']['content'].strip().upper()
        return result if result in ['A', 'B'] else "Error"
    except Exception: return "Error"


# --- 3. 主逻辑 ---

def main():
    """主执行函数"""
    print("--- 开始验证：预计算分数 vs. LLM直接判断 ---")
    
    scores = load_scores(SCORE_FILE_PATH)
    if not scores:
        return

    all_files = get_all_text_files(PLANNING_TEXTS_DIR)
    if len(all_files) < 3:
        print("文本文件不足3个，无法测试。")
        return

    results_data = []
    tested_count = 0
    seen_triplets = set()

    while tested_count < NUM_TRIPLETS_TO_TEST:
        sampled_files = random.sample(all_files, 3)
        sampled_files.sort()
        triplet_id = tuple(sampled_files)

        if triplet_id in seen_triplets: continue
        seen_triplets.add(triplet_id)

        file_a, file_b, file_c = triplet_id
        base_a, base_b, base_c = os.path.basename(file_a).replace('.txt', ''), os.path.basename(file_b).replace('.txt', ''), os.path.basename(file_c).replace('.txt', '')
        
        # 检查所有城市的得分是否存在
        try:
            score_a, score_b, score_c = scores[base_a], scores[base_b], scores[base_c]
        except KeyError as e:
            print(f"警告：在分数文件中找不到城市 {e} 的得分，跳过此三元组。")
            continue

        content_a, content_b, content_c = read_text_content(file_a), read_text_content(file_b), read_text_content(file_c)
        if not all([content_a, content_b, content_c]): continue

        tested_count += 1
        print(f"\n--- 正在测试第 {tested_count}/{NUM_TRIPLETS_TO_TEST} 组 ---")
        print(f"A: {base_a} (得分: {score_a}), B: {base_b} (得分: {score_b}), C: {base_c} (得分: {score_c})")
        
        # --- 进行三次独立的验证 ---
        comparisons = [('A', 'B', content_a, content_b, score_a, score_b),
                       ('B', 'C', content_b, content_c, score_b, score_c),
                       ('A', 'C', content_a, content_c, score_a, score_c)]
        
        row_data = {"文本A": base_a, "得分A": score_a, "文本B": base_b, "得分B": score_b, "文本C": base_c, "得分C": score_c}
        total_matches = 0

        for comp in comparisons:
            name1, name2, text1, text2, s1, s2 = comp
            pair_name = f"{name1} vs {name2}"
            
            # 1. 分数排序
            if s1 > s2: score_rank = f"{name1} > {name2}"
            elif s2 > s1: score_rank = f"{name2} > {name1}"
            else: score_rank = f"{name1} = {name2}"

            # 2. LLM判断
            time.sleep(1) # API礼貌性延迟
            llm_result = compare_texts_with_llm(text1, text2)
            
            if llm_result == "Error":
                llm_rank = "API Error"
                match_status = "Error"
            else:
                # 注意：API返回'A'代表第一个参数获胜，'B'代表第二个参数获胜
                llm_rank = f"{name1} > {name2}" if llm_result == 'A' else f"{name2} > {name1}"
                # 3. 验证是否匹配
                match_status = 1 if score_rank == llm_rank else 0
                if match_status == 1:
                    total_matches += 1
            
            print(f"验证 {pair_name}: 分数排序='{score_rank}', LLM判断='{llm_rank}' -> 匹配状态: {match_status}")

            # 填充行数据
            row_data[f"得分排序 ({pair_name})"] = score_rank
            row_data[f"LLM判断 ({pair_name})"] = llm_rank
            row_data[f"是否匹配 ({pair_name})"] = match_status

        row_data["三组匹配总数"] = total_matches
        results_data.append(row_data)

    # --- 4. 结果汇总与文件生成 ---
    if not results_data:
        print("\n没有生成任何结果，无法创建Excel文件。")
        return

    print(f"\n\n--- 所有测试完成，正在生成验证报告 ---")
    
    df = pd.DataFrame(results_data)
    # 调整列顺序，使其更具可读性
    column_order = [
        "文本A", "得分A", "文本B", "得分B",
        "得分排序 (A vs B)", "LLM判断 (A vs B)", "是否匹配 (A vs B)",
        "文本C", "得分C",
        "得分排序 (B vs C)", "LLM判断 (B vs C)", "是否匹配 (B vs C)",
        "得分排序 (A vs C)", "LLM判断 (A vs C)", "是否匹配 (A vs C)",
        "三组匹配总数"
    ]
    # 过滤掉不存在的列（以防万一），然后重新索引
    df = df.reindex(columns=[col for col in column_order if col in df.columns])

    try:
        df.to_excel(OUTPUT_EXCEL_FILE, index=False)
        print(f"✔ 成功！验证结果已保存到文件: '{OUTPUT_EXCEL_FILE}'")
    except Exception as e:
        print(f"❌ 错误：保存Excel文件失败。原因: {e}")

    # 计算总体匹配率
    match_cols = [col for col in df.columns if '是否匹配' in str(col)]
    total_comparisons = df[match_cols].notna().sum().sum()
    total_success_matches = df[match_cols].sum().sum()
    
    if total_comparisons > 0:
        overall_match_rate = (total_success_matches / total_comparisons) * 100
        print("\n========================================")
        print("             验证结果总览")
        print("========================================")
        print(f"总共进行的有效配对比较次数: {total_comparisons}")
        print(f"分数排序与LLM判断一致的次数: {total_success_matches}")
        print(f"总体匹配率: {overall_match_rate:.2f}%")
        print("========================================")


if __name__ == "__main__":
=======
import os
import random
import requests
import json
import time
import pandas as pd

# --- 1. 配置参数 ---

# DeepSeek API 配置
API_KEY = "sk-6e8113f768cd42768058ce6dc6ef3401" # 您的DeepSeek API密钥
API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_NAME = "deepseek-chat"
TEMPERATURE = 0.5

# 数据和实验配置
PLANNING_TEXTS_DIR = r"D:\1sdgplanning\1data\1全部批复"
SCORE_FILE_PATH = r"D:\1sdgplanning\1data\similarity_total.xlsx"
NUM_TRIPLETS_TO_TEST = 20
OUTPUT_EXCEL_FILE = "verification_results.xlsx"

# --- 2. 核心功能函数 ---

def load_scores(filepath: str) -> dict:
    """从Excel加载预计算的分数到字典中。"""
    print(f"正在从 '{filepath}' 加载分数...")
    try:
        df = pd.read_excel(filepath)
        # 确保列名正确
        if 'city' not in df.columns or 'total' not in df.columns:
            print(f"错误：Excel文件中必须包含 'city' 和 'total' 列。")
            return None
        # 创建字典，key为city，value为total score
        score_dict = pd.Series(df.total.values, index=df.city).to_dict()
        print(f"成功加载 {len(score_dict)} 个地区的分数。")
        return score_dict
    except FileNotFoundError:
        print(f"错误：分数文件 '{filepath}' 未找到。")
        return None
    except Exception as e:
        print(f"加载Excel文件时出错: {e}")
        return None

# (get_all_text_files, read_text_content, compare_texts_with_llm 函数与之前版本相同)
def get_all_text_files(directory: str) -> list:
    if not os.path.isdir(directory): return []
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.txt')]

def read_text_content(filepath: str) -> str:
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return f.read()
    except Exception: return None

def compare_texts_with_llm(text_a: str, text_b: str) -> str:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    prompt = f"请判断以下“文本A”和“文本B”哪一份更符合联合国可持续发展目标（SDGs）。你的回答必须且只能是单个字母：“A”或“B”。\n\n文本A:\n{text_a[:1500]}\n\n文本B:\n{text_b[:1500]}"
    payload = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}], "temperature": TEMPERATURE, "max_tokens": 5}
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=60)
        response.raise_for_status()
        result = response.json()['choices'][0]['message']['content'].strip().upper()
        return result if result in ['A', 'B'] else "Error"
    except Exception: return "Error"


# --- 3. 主逻辑 ---

def main():
    """主执行函数"""
    print("--- 开始验证：预计算分数 vs. LLM直接判断 ---")
    
    scores = load_scores(SCORE_FILE_PATH)
    if not scores:
        return

    all_files = get_all_text_files(PLANNING_TEXTS_DIR)
    if len(all_files) < 3:
        print("文本文件不足3个，无法测试。")
        return

    results_data = []
    tested_count = 0
    seen_triplets = set()

    while tested_count < NUM_TRIPLETS_TO_TEST:
        sampled_files = random.sample(all_files, 3)
        sampled_files.sort()
        triplet_id = tuple(sampled_files)

        if triplet_id in seen_triplets: continue
        seen_triplets.add(triplet_id)

        file_a, file_b, file_c = triplet_id
        base_a, base_b, base_c = os.path.basename(file_a).replace('.txt', ''), os.path.basename(file_b).replace('.txt', ''), os.path.basename(file_c).replace('.txt', '')
        
        # 检查所有城市的得分是否存在
        try:
            score_a, score_b, score_c = scores[base_a], scores[base_b], scores[base_c]
        except KeyError as e:
            print(f"警告：在分数文件中找不到城市 {e} 的得分，跳过此三元组。")
            continue

        content_a, content_b, content_c = read_text_content(file_a), read_text_content(file_b), read_text_content(file_c)
        if not all([content_a, content_b, content_c]): continue

        tested_count += 1
        print(f"\n--- 正在测试第 {tested_count}/{NUM_TRIPLETS_TO_TEST} 组 ---")
        print(f"A: {base_a} (得分: {score_a}), B: {base_b} (得分: {score_b}), C: {base_c} (得分: {score_c})")
        
        # --- 进行三次独立的验证 ---
        comparisons = [('A', 'B', content_a, content_b, score_a, score_b),
                       ('B', 'C', content_b, content_c, score_b, score_c),
                       ('A', 'C', content_a, content_c, score_a, score_c)]
        
        row_data = {"文本A": base_a, "得分A": score_a, "文本B": base_b, "得分B": score_b, "文本C": base_c, "得分C": score_c}
        total_matches = 0

        for comp in comparisons:
            name1, name2, text1, text2, s1, s2 = comp
            pair_name = f"{name1} vs {name2}"
            
            # 1. 分数排序
            if s1 > s2: score_rank = f"{name1} > {name2}"
            elif s2 > s1: score_rank = f"{name2} > {name1}"
            else: score_rank = f"{name1} = {name2}"

            # 2. LLM判断
            time.sleep(1) # API礼貌性延迟
            llm_result = compare_texts_with_llm(text1, text2)
            
            if llm_result == "Error":
                llm_rank = "API Error"
                match_status = "Error"
            else:
                # 注意：API返回'A'代表第一个参数获胜，'B'代表第二个参数获胜
                llm_rank = f"{name1} > {name2}" if llm_result == 'A' else f"{name2} > {name1}"
                # 3. 验证是否匹配
                match_status = 1 if score_rank == llm_rank else 0
                if match_status == 1:
                    total_matches += 1
            
            print(f"验证 {pair_name}: 分数排序='{score_rank}', LLM判断='{llm_rank}' -> 匹配状态: {match_status}")

            # 填充行数据
            row_data[f"得分排序 ({pair_name})"] = score_rank
            row_data[f"LLM判断 ({pair_name})"] = llm_rank
            row_data[f"是否匹配 ({pair_name})"] = match_status

        row_data["三组匹配总数"] = total_matches
        results_data.append(row_data)

    # --- 4. 结果汇总与文件生成 ---
    if not results_data:
        print("\n没有生成任何结果，无法创建Excel文件。")
        return

    print(f"\n\n--- 所有测试完成，正在生成验证报告 ---")
    
    df = pd.DataFrame(results_data)
    # 调整列顺序，使其更具可读性
    column_order = [
        "文本A", "得分A", "文本B", "得分B",
        "得分排序 (A vs B)", "LLM判断 (A vs B)", "是否匹配 (A vs B)",
        "文本C", "得分C",
        "得分排序 (B vs C)", "LLM判断 (B vs C)", "是否匹配 (B vs C)",
        "得分排序 (A vs C)", "LLM判断 (A vs C)", "是否匹配 (A vs C)",
        "三组匹配总数"
    ]
    # 过滤掉不存在的列（以防万一），然后重新索引
    df = df.reindex(columns=[col for col in column_order if col in df.columns])

    try:
        df.to_excel(OUTPUT_EXCEL_FILE, index=False)
        print(f"✔ 成功！验证结果已保存到文件: '{OUTPUT_EXCEL_FILE}'")
    except Exception as e:
        print(f"❌ 错误：保存Excel文件失败。原因: {e}")

    # 计算总体匹配率
    match_cols = [col for col in df.columns if '是否匹配' in str(col)]
    total_comparisons = df[match_cols].notna().sum().sum()
    total_success_matches = df[match_cols].sum().sum()
    
    if total_comparisons > 0:
        overall_match_rate = (total_success_matches / total_comparisons) * 100
        print("\n========================================")
        print("             验证结果总览")
        print("========================================")
        print(f"总共进行的有效配对比较次数: {total_comparisons}")
        print(f"分数排序与LLM判断一致的次数: {total_success_matches}")
        print(f"总体匹配率: {overall_match_rate:.2f}%")
        print("========================================")


if __name__ == "__main__":
>>>>>>> e50b95b2529049900b3f37abd3dcf41a8db0f27e
    main()