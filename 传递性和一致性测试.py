<<<<<<< HEAD
import os
import random
import requests
import json
import time
import pandas as pd

# --- 1. 配置参数 ---

# 路径设置
PLANNING_TEXTS_DIR = r"D:\1sdgplanning\1data\1全部批复"
SCORE_FILE_PATH = r"D:\1sdgplanning\1data\similarity_total.xlsx"
STOPWORD_FILE = r"D:\1sdgplanning\1data\hit_stop.txt"
CUSTOM_STOPWORD_FILE = r"D:\1sdgplanning\1data\custom_stop.txt"
SDG_DEFINITIONS_PATH = r"D:\1sdgplanning\1data\sdg.txt"

# API与实验配置
API_KEY = "sk-6e8113f768cd42768058ce6dc6ef3401" # 您的DeepSeek API密钥
API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_NAME = "deepseek-chat"
TEMPERATURE = 0.1

# 核心修改：为两项测试分别设置样本量
NUM_PAIRS_FOR_VALIDATION = 20    # 分数验证的随机配对数量
NUM_TRIPLETS_FOR_CONSISTENCY = 20 # 内部一致性测试的三元组数量

OUTPUT_EXCEL_FILE = "final_split_report.xlsx" # 新的输出文件名

# --- 2. 功能函数 (此部分无需修改) ---

def read_text_content(filepath: str) -> str:
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return f.read()
    except Exception as e:
        print(f"读取文件 '{filepath}' 时出错: {e}")
        return None

def load_scores(filepath: str) -> dict:
    print(f"正在从 '{filepath}' 加载分数...")
    try:
        df = pd.read_excel(filepath)
        if 'city' not in df.columns or 'total' not in df.columns: return None
        return pd.Series(df.total.values, index=df.city).to_dict()
    except Exception as e:
        print(f"加载分数文件时出错: {e}")
        return None

def load_stopwords(stopword_file, custom_stopword_file):
    stopwords = set()
    try:
        if os.path.exists(stopword_file):
            with open(stopword_file, 'r', encoding='utf-8') as f:
                stopwords.update(line.strip() for line in f if line.strip())
        if os.path.exists(custom_stopword_file):
            with open(custom_stopword_file, 'r', encoding='utf-8') as f:
                stopwords.update(line.strip() for line in f if line.strip())
    except Exception as e:
        print(f"加载停用词时出错: {e}")
    return stopwords

def remove_stopwords(text, stopwords):
    if not stopwords or not text: return text
    return ' '.join([word for word in text.split() if word not in stopwords])

def get_all_text_files(directory: str) -> list:
    if not os.path.isdir(directory): return []
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.txt')]

def compare_texts_with_llm(text_a: str, text_b: str, sdg_criteria: str) -> str:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    prompt = f"你是一名严格的评估专家。你的唯一任务是根据下面提供的“评估标准文档”，判断“文本A”和“文本B”哪一个更符合该标准。\n\n--- 评估标准文档 ---\n{sdg_criteria}\n---\n\n--- 待评估文本 ---\n文本A:\n{text_a[:4000]}\n\n文本B:\n{text_b[:4000]}\n---\n\n问题：严格依据上述“评估标准文档”，哪一份文本（A或B）展示了更优的符合度？你的回答必须且只能是单个英文字母：“A”或“B”。"
    payload = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}], "temperature": TEMPERATURE, "max_tokens": 5}
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=90)
        response.raise_for_status()
        result = response.json()['choices'][0]['message']['content'].strip().upper()
        return result if result in ['A', 'B'] else "Error"
    except Exception as e:
        print(f"API请求失败: {e}")
        return "Error"

# --- 3. 主逻辑 (重构为两个独立的测试) ---

def main():
    # --- 启动和加载阶段 ---
    print("--- 开始双重测试流程 ---")
    stopwords = load_stopwords(STOPWORD_FILE, CUSTOM_STOPWORD_FILE)
    scores = load_scores(SCORE_FILE_PATH)
    sdg_definitions_raw = read_text_content(SDG_DEFINITIONS_PATH)
    sdg_definitions_clean = remove_stopwords(sdg_definitions_raw, stopwords)
    all_files = get_all_text_files(PLANNING_TEXTS_DIR)
    
    if not all([scores, sdg_definitions_clean, len(all_files) >= 3]):
        print("错误：缺少必要文件（分数、SDG定义或规划文本），程序终止。")
        return

    # --- 测试1: 分数验证 (60组随机配对) ---
    print(f"\n\n--- [测试 1/2] 开始分数验证（随机抽取 {NUM_PAIRS_FOR_VALIDATION} 组配对）---")
    validation_results = []
    seen_pairs = set()
    tested_pairs_count = 0
    while tested_pairs_count < NUM_PAIRS_FOR_VALIDATION and len(seen_pairs) < len(all_files) * (len(all_files) - 1) / 2:
        file1, file2 = random.sample(all_files, 2)
        # 规范化配对，避免(A,B)和(B,A)重复测试
        pair_id = tuple(sorted((file1, file2)))
        if pair_id in seen_pairs: continue
        seen_pairs.add(pair_id)

        base1, base2 = os.path.basename(file1).replace('.txt', ''), os.path.basename(file2).replace('.txt', '')
        try:
            score1, score2 = scores[base1], scores[base2]
        except KeyError as e:
            print(f"警告：找不到城市 {e} 的得分，跳过此配对。")
            continue

        content1, content2 = read_text_content(file1), read_text_content(file2)
        if not content1 or not content2: continue
        
        clean1, clean2 = remove_stopwords(content1, stopwords), remove_stopwords(content2, stopwords)
        
        tested_pairs_count += 1
        print(f"\n正在验证第 {tested_pairs_count}/{NUM_PAIRS_FOR_VALIDATION} 组: {base1} vs {base2}")

        score_rank = f"{base1}>{base2}" if score1 > score2 else (f"{base2}>{base1}" if score2 > score1 else f"{base1}={base2}")
        llm_result = compare_texts_with_llm(clean1, clean2, sdg_definitions_clean)
        
        if llm_result == "Error":
            llm_rank, is_match = "API Error", "Error"
        else:
            llm_rank = f"{base1}>{base2}" if llm_result == 'A' else f"{base2}>{base1}"
            is_match = 1 if score_rank == llm_rank else 0
        
        print(f"--> 分数排序='{score_rank}', LLM判断='{llm_rank}' -> 匹配: {is_match}")
        validation_results.append({
            "文本A": base1, "得分A": score1, "文本B": base2, "得分B": score2,
            "得分排序": score_rank, "LLM判断": llm_rank, "是否匹配 (1=是, 0=否)": is_match
        })
        time.sleep(1)

    # --- 测试2: 内部一致性测试 (20个三元组) ---
    print(f"\n\n--- [测试 2/2] 开始内部一致性测试（随机抽取 {NUM_TRIPLETS_FOR_CONSISTENCY} 组三元组）---")
    consistency_results = []
    seen_triplets = set()
    tested_triplets_count = 0
    while tested_triplets_count < NUM_TRIPLETS_FOR_CONSISTENCY:
        try:
            file_a, file_b, file_c = random.sample(all_files, 3)
            triplet_id = tuple(sorted((file_a, file_b, file_c)))
            if triplet_id in seen_triplets: continue
            seen_triplets.add(triplet_id)
        except ValueError: break

        base_a, base_b, base_c = os.path.basename(file_a).replace('.txt',''), os.path.basename(file_b).replace('.txt',''), os.path.basename(file_c).replace('.txt','')
        content_a, content_b, content_c = read_text_content(file_a), read_text_content(file_b), read_text_content(file_c)
        if not all([content_a, content_b, content_c]): continue
        
        tested_triplets_count += 1
        print(f"\n正在测试第 {tested_triplets_count}/{NUM_TRIPLETS_FOR_CONSISTENCY} 组: ({base_a}, {base_b}, {base_c})")

        clean_a, clean_b, clean_c = remove_stopwords(content_a, stopwords), remove_stopwords(content_b, stopwords), remove_stopwords(content_c, stopwords)
        result_ab = compare_texts_with_llm(clean_a, clean_b, sdg_definitions_clean)
        time.sleep(1)
        result_bc = compare_texts_with_llm(clean_b, clean_c, sdg_definitions_clean)
        time.sleep(1)
        result_ac = compare_texts_with_llm(clean_a, clean_c, sdg_definitions_clean)

        row_data = {"文本A": base_a, "文本B": base_b, "文本C": base_c}
        if "Error" in [result_ab, result_bc, result_ac]:
            row_data.update({"比较结果 (A vs B)": "Error", "比较结果 (B vs C)": "Error", "比较结果 (A vs C)": "Error", "是否内部一致 (1=是, 0=否)": "Error"})
        else:
            wins = {'A': 0, 'B': 0, 'C': 0}
            if result_ab == 'A': wins['A'] += 1; 
            else: wins['B'] += 1
            if result_bc == 'A': wins['B'] += 1; 
            else: wins['C'] += 1
            if result_ac == 'A': wins['A'] += 1; 
            else: wins['C'] += 1
            is_consistent = not (wins['A'] == 1 and wins['B'] == 1 and wins['C'] == 1)
            row_data.update({
                "比较结果 (A vs B)": "A>B" if result_ab == 'A' else "B>A",
                "比较结果 (B vs C)": "B>C" if result_bc == 'A' else "C>B",
                "比较结果 (A vs C)": "A>C" if result_ac == 'A' else "C>A",
                "是否内部一致 (1=是, 0=否)": 1 if is_consistent else 0
            })
        consistency_results.append(row_data)

    # --- 4. 结果汇总与文件生成 (多工作表) ---
    print("\n\n--- 所有测试完成，正在生成多工作表Excel报告 ---")
    
    try:
        with pd.ExcelWriter(OUTPUT_EXCEL_FILE, engine='openpyxl') as writer:
            # 写入第一个工作表
            df_validation = pd.DataFrame(validation_results)
            df_validation.to_excel(writer, sheet_name='分数验证结果', index=False)
            
            # 写入第二个工作表
            df_consistency = pd.DataFrame(consistency_results)
            df_consistency.to_excel(writer, sheet_name='内部一致性测试', index=False)
        print(f"✔ 成功！综合报告已保存到: '{OUTPUT_EXCEL_FILE}'")
    except Exception as e:
        print(f"❌ 错误：保存Excel文件失败。原因: {e}")

    # 打印双重总结
    print("\n========================================")
    print("         分数验证 (外部一致性) 总结")
    print("========================================")
    if validation_results:
        df_val = pd.DataFrame(validation_results)
        valid_comps = df_val[df_val["是否匹配 (1=是, 0=否)"].isin([0, 1])]
        if not valid_comps.empty:
            match_rate = valid_comps["是否匹配 (1=是, 0=否)"].mean() * 100
            print(f"总有效配对比较次数: {len(valid_comps)}")
            print(f"分数与LLM判断一致次数: {int(valid_comps['是否匹配 (1=是, 0=否)'].sum())}")
            print(f"总体匹配率: {match_rate:.2f}%")

    print("\n========================================")
    print("         传递性 (内部一致性) 总结")
    print("========================================")
    if consistency_results:
        df_con = pd.DataFrame(consistency_results)
        valid_triplets = df_con[df_con["是否内部一致 (1=是, 0=否)"].isin([0, 1])]
        if not valid_triplets.empty:
            consistency_rate = valid_triplets["是否内部一致 (1=是, 0=否)"].mean() * 100
            print(f"总有效测试三元组: {len(valid_triplets)}")
            print(f"内部一致的三元组数: {int(valid_triplets['是否内部一致 (1=是, 0=否)'].sum())}")
            print(f"内部一致性比率: {consistency_rate:.2f}%")
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

# 路径设置
PLANNING_TEXTS_DIR = r"D:\1sdgplanning\1data\1全部批复"
SCORE_FILE_PATH = r"D:\1sdgplanning\1data\similarity_total.xlsx"
STOPWORD_FILE = r"D:\1sdgplanning\1data\hit_stop.txt"
CUSTOM_STOPWORD_FILE = r"D:\1sdgplanning\1data\custom_stop.txt"
SDG_DEFINITIONS_PATH = r"D:\1sdgplanning\1data\sdg.txt"

# API与实验配置
API_KEY = "sk-6e8113f768cd42768058ce6dc6ef3401" # 您的DeepSeek API密钥
API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_NAME = "deepseek-chat"
TEMPERATURE = 0.1

# 核心修改：为两项测试分别设置样本量
NUM_PAIRS_FOR_VALIDATION = 20    # 分数验证的随机配对数量
NUM_TRIPLETS_FOR_CONSISTENCY = 20 # 内部一致性测试的三元组数量

OUTPUT_EXCEL_FILE = "final_split_report.xlsx" # 新的输出文件名

# --- 2. 功能函数 (此部分无需修改) ---

def read_text_content(filepath: str) -> str:
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return f.read()
    except Exception as e:
        print(f"读取文件 '{filepath}' 时出错: {e}")
        return None

def load_scores(filepath: str) -> dict:
    print(f"正在从 '{filepath}' 加载分数...")
    try:
        df = pd.read_excel(filepath)
        if 'city' not in df.columns or 'total' not in df.columns: return None
        return pd.Series(df.total.values, index=df.city).to_dict()
    except Exception as e:
        print(f"加载分数文件时出错: {e}")
        return None

def load_stopwords(stopword_file, custom_stopword_file):
    stopwords = set()
    try:
        if os.path.exists(stopword_file):
            with open(stopword_file, 'r', encoding='utf-8') as f:
                stopwords.update(line.strip() for line in f if line.strip())
        if os.path.exists(custom_stopword_file):
            with open(custom_stopword_file, 'r', encoding='utf-8') as f:
                stopwords.update(line.strip() for line in f if line.strip())
    except Exception as e:
        print(f"加载停用词时出错: {e}")
    return stopwords

def remove_stopwords(text, stopwords):
    if not stopwords or not text: return text
    return ' '.join([word for word in text.split() if word not in stopwords])

def get_all_text_files(directory: str) -> list:
    if not os.path.isdir(directory): return []
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.txt')]

def compare_texts_with_llm(text_a: str, text_b: str, sdg_criteria: str) -> str:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    prompt = f"你是一名严格的评估专家。你的唯一任务是根据下面提供的“评估标准文档”，判断“文本A”和“文本B”哪一个更符合该标准。\n\n--- 评估标准文档 ---\n{sdg_criteria}\n---\n\n--- 待评估文本 ---\n文本A:\n{text_a[:4000]}\n\n文本B:\n{text_b[:4000]}\n---\n\n问题：严格依据上述“评估标准文档”，哪一份文本（A或B）展示了更优的符合度？你的回答必须且只能是单个英文字母：“A”或“B”。"
    payload = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}], "temperature": TEMPERATURE, "max_tokens": 5}
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=90)
        response.raise_for_status()
        result = response.json()['choices'][0]['message']['content'].strip().upper()
        return result if result in ['A', 'B'] else "Error"
    except Exception as e:
        print(f"API请求失败: {e}")
        return "Error"

# --- 3. 主逻辑 (重构为两个独立的测试) ---

def main():
    # --- 启动和加载阶段 ---
    print("--- 开始双重测试流程 ---")
    stopwords = load_stopwords(STOPWORD_FILE, CUSTOM_STOPWORD_FILE)
    scores = load_scores(SCORE_FILE_PATH)
    sdg_definitions_raw = read_text_content(SDG_DEFINITIONS_PATH)
    sdg_definitions_clean = remove_stopwords(sdg_definitions_raw, stopwords)
    all_files = get_all_text_files(PLANNING_TEXTS_DIR)
    
    if not all([scores, sdg_definitions_clean, len(all_files) >= 3]):
        print("错误：缺少必要文件（分数、SDG定义或规划文本），程序终止。")
        return

    # --- 测试1: 分数验证 (60组随机配对) ---
    print(f"\n\n--- [测试 1/2] 开始分数验证（随机抽取 {NUM_PAIRS_FOR_VALIDATION} 组配对）---")
    validation_results = []
    seen_pairs = set()
    tested_pairs_count = 0
    while tested_pairs_count < NUM_PAIRS_FOR_VALIDATION and len(seen_pairs) < len(all_files) * (len(all_files) - 1) / 2:
        file1, file2 = random.sample(all_files, 2)
        # 规范化配对，避免(A,B)和(B,A)重复测试
        pair_id = tuple(sorted((file1, file2)))
        if pair_id in seen_pairs: continue
        seen_pairs.add(pair_id)

        base1, base2 = os.path.basename(file1).replace('.txt', ''), os.path.basename(file2).replace('.txt', '')
        try:
            score1, score2 = scores[base1], scores[base2]
        except KeyError as e:
            print(f"警告：找不到城市 {e} 的得分，跳过此配对。")
            continue

        content1, content2 = read_text_content(file1), read_text_content(file2)
        if not content1 or not content2: continue
        
        clean1, clean2 = remove_stopwords(content1, stopwords), remove_stopwords(content2, stopwords)
        
        tested_pairs_count += 1
        print(f"\n正在验证第 {tested_pairs_count}/{NUM_PAIRS_FOR_VALIDATION} 组: {base1} vs {base2}")

        score_rank = f"{base1}>{base2}" if score1 > score2 else (f"{base2}>{base1}" if score2 > score1 else f"{base1}={base2}")
        llm_result = compare_texts_with_llm(clean1, clean2, sdg_definitions_clean)
        
        if llm_result == "Error":
            llm_rank, is_match = "API Error", "Error"
        else:
            llm_rank = f"{base1}>{base2}" if llm_result == 'A' else f"{base2}>{base1}"
            is_match = 1 if score_rank == llm_rank else 0
        
        print(f"--> 分数排序='{score_rank}', LLM判断='{llm_rank}' -> 匹配: {is_match}")
        validation_results.append({
            "文本A": base1, "得分A": score1, "文本B": base2, "得分B": score2,
            "得分排序": score_rank, "LLM判断": llm_rank, "是否匹配 (1=是, 0=否)": is_match
        })
        time.sleep(1)

    # --- 测试2: 内部一致性测试 (20个三元组) ---
    print(f"\n\n--- [测试 2/2] 开始内部一致性测试（随机抽取 {NUM_TRIPLETS_FOR_CONSISTENCY} 组三元组）---")
    consistency_results = []
    seen_triplets = set()
    tested_triplets_count = 0
    while tested_triplets_count < NUM_TRIPLETS_FOR_CONSISTENCY:
        try:
            file_a, file_b, file_c = random.sample(all_files, 3)
            triplet_id = tuple(sorted((file_a, file_b, file_c)))
            if triplet_id in seen_triplets: continue
            seen_triplets.add(triplet_id)
        except ValueError: break

        base_a, base_b, base_c = os.path.basename(file_a).replace('.txt',''), os.path.basename(file_b).replace('.txt',''), os.path.basename(file_c).replace('.txt','')
        content_a, content_b, content_c = read_text_content(file_a), read_text_content(file_b), read_text_content(file_c)
        if not all([content_a, content_b, content_c]): continue
        
        tested_triplets_count += 1
        print(f"\n正在测试第 {tested_triplets_count}/{NUM_TRIPLETS_FOR_CONSISTENCY} 组: ({base_a}, {base_b}, {base_c})")

        clean_a, clean_b, clean_c = remove_stopwords(content_a, stopwords), remove_stopwords(content_b, stopwords), remove_stopwords(content_c, stopwords)
        result_ab = compare_texts_with_llm(clean_a, clean_b, sdg_definitions_clean)
        time.sleep(1)
        result_bc = compare_texts_with_llm(clean_b, clean_c, sdg_definitions_clean)
        time.sleep(1)
        result_ac = compare_texts_with_llm(clean_a, clean_c, sdg_definitions_clean)

        row_data = {"文本A": base_a, "文本B": base_b, "文本C": base_c}
        if "Error" in [result_ab, result_bc, result_ac]:
            row_data.update({"比较结果 (A vs B)": "Error", "比较结果 (B vs C)": "Error", "比较结果 (A vs C)": "Error", "是否内部一致 (1=是, 0=否)": "Error"})
        else:
            wins = {'A': 0, 'B': 0, 'C': 0}
            if result_ab == 'A': wins['A'] += 1; 
            else: wins['B'] += 1
            if result_bc == 'A': wins['B'] += 1; 
            else: wins['C'] += 1
            if result_ac == 'A': wins['A'] += 1; 
            else: wins['C'] += 1
            is_consistent = not (wins['A'] == 1 and wins['B'] == 1 and wins['C'] == 1)
            row_data.update({
                "比较结果 (A vs B)": "A>B" if result_ab == 'A' else "B>A",
                "比较结果 (B vs C)": "B>C" if result_bc == 'A' else "C>B",
                "比较结果 (A vs C)": "A>C" if result_ac == 'A' else "C>A",
                "是否内部一致 (1=是, 0=否)": 1 if is_consistent else 0
            })
        consistency_results.append(row_data)

    # --- 4. 结果汇总与文件生成 (多工作表) ---
    print("\n\n--- 所有测试完成，正在生成多工作表Excel报告 ---")
    
    try:
        with pd.ExcelWriter(OUTPUT_EXCEL_FILE, engine='openpyxl') as writer:
            # 写入第一个工作表
            df_validation = pd.DataFrame(validation_results)
            df_validation.to_excel(writer, sheet_name='分数验证结果', index=False)
            
            # 写入第二个工作表
            df_consistency = pd.DataFrame(consistency_results)
            df_consistency.to_excel(writer, sheet_name='内部一致性测试', index=False)
        print(f"✔ 成功！综合报告已保存到: '{OUTPUT_EXCEL_FILE}'")
    except Exception as e:
        print(f"❌ 错误：保存Excel文件失败。原因: {e}")

    # 打印双重总结
    print("\n========================================")
    print("         分数验证 (外部一致性) 总结")
    print("========================================")
    if validation_results:
        df_val = pd.DataFrame(validation_results)
        valid_comps = df_val[df_val["是否匹配 (1=是, 0=否)"].isin([0, 1])]
        if not valid_comps.empty:
            match_rate = valid_comps["是否匹配 (1=是, 0=否)"].mean() * 100
            print(f"总有效配对比较次数: {len(valid_comps)}")
            print(f"分数与LLM判断一致次数: {int(valid_comps['是否匹配 (1=是, 0=否)'].sum())}")
            print(f"总体匹配率: {match_rate:.2f}%")

    print("\n========================================")
    print("         传递性 (内部一致性) 总结")
    print("========================================")
    if consistency_results:
        df_con = pd.DataFrame(consistency_results)
        valid_triplets = df_con[df_con["是否内部一致 (1=是, 0=否)"].isin([0, 1])]
        if not valid_triplets.empty:
            consistency_rate = valid_triplets["是否内部一致 (1=是, 0=否)"].mean() * 100
            print(f"总有效测试三元组: {len(valid_triplets)}")
            print(f"内部一致的三元组数: {int(valid_triplets['是否内部一致 (1=是, 0=否)'].sum())}")
            print(f"内部一致性比率: {consistency_rate:.2f}%")
    print("========================================")

if __name__ == "__main__":
>>>>>>> e50b95b2529049900b3f37abd3dcf41a8db0f27e
    main()