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
PLANNING_TEXTS_DIR = r"D:\1sdgplanning\1data\1全部批复" # 规划文本存放目录
NUM_TRIPLETS_TO_TEST = 20 # 需要测试的三元组数量
OUTPUT_EXCEL_FILE = "consistency_check_results_v2.xlsx" # 输出的Excel文件名

# --- 2. 核心功能函数 (无变化) ---

def get_all_text_files(directory: str) -> list:
    """获取指定目录下所有txt文件的完整路径。"""
    if not os.path.isdir(directory):
        print(f"错误：目录 '{directory}' 不存在。")
        return []
    
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.txt')]
    print(f"在 '{directory}' 中找到 {len(files)} 个txt文件。")
    return files

def read_text_content(filepath: str) -> str:
    """读取文本文件的内容。"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文件 '{filepath}' 时出错: {e}")
        return None

def compare_texts_with_llm(text_a: str, text_b: str, filename_a: str, filename_b: str) -> str:
    """使用DeepSeek API比较两个文本哪个更符合SDG。返回 'A', 'B', 或 'Error'。"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    请你扮演一位可持续发展领域的专家。下面是两份规划文本，名为“文本A”和“文本B”。
    你的任务是判断哪一份文本更全面、更深入、更具体地体现了联合国可持续发展目标（SDGs）。
    你的回答必须且只能是单个英文字母：“A”或“B”。

    ---
    文本A（来自文件: {filename_a}）:
    {text_a[:2000]}

    ---
    文本B（来自文件: {filename_b}）:
    {text_b[:2000]}
    ---

    请判断哪一份文本更符合SDGs？请仅回答 'A' 或 'B'。
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens": 5
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=60)
        response.raise_for_status()
        result_content = response.json()['choices'][0]['message']['content'].strip().upper()
        
        if result_content in ['A', 'B']:
            return result_content
        else:
            print(f"警告：API返回了意外的内容: '{result_content}'")
            return "Error"
            
    except requests.exceptions.RequestException as e:
        print(f"API请求失败: {e}")
        return "Error"
    except (KeyError, IndexError) as e:
        print(f"解析API响应失败: {e}")
        return "Error"

# --- 3. 主逻辑 (一致性判断已更新) ---

def main():
    """主执行函数"""
    print("--- 开始内部一致性评估 (V2逻辑) ---")
    
    all_files = get_all_text_files(PLANNING_TEXTS_DIR)
    
    if len(all_files) < 3:
        print("错误：文本文件不足3个，无法构成三元组进行测试。")
        return

    results_data = []
    tested_triplets_count = 0
    seen_triplets = set()

    print(f"\n准备随机抽取 {NUM_TRIPLETS_TO_TEST} 组三元组进行测试...")
    
    while tested_triplets_count < NUM_TRIPLETS_TO_TEST:
        try:
            sampled_files = random.sample(all_files, 3)
            sampled_files.sort()
            triplet_id = tuple(sampled_files)

            if triplet_id in seen_triplets:
                continue
            
            seen_triplets.add(triplet_id)
            
        except ValueError:
            print("警告：可用文件数量不足以继续抽取新的三元组。")
            break

        file_a, file_b, file_c = triplet_id
        
        content_a = read_text_content(file_a)
        content_b = read_text_content(file_b)
        content_c = read_text_content(file_c)

        if not all([content_a, content_b, content_c]):
            print(f"跳过三元组 {triplet_id} 因为其中一个文件读取失败。")
            continue
        
        current_triplet_num = tested_triplets_count + 1
        print(f"\n--- 正在测试第 {current_triplet_num}/{NUM_TRIPLETS_TO_TEST} 组三元组 ---")
        base_a, base_b, base_c = os.path.basename(file_a), os.path.basename(file_b), os.path.basename(file_c)
        print(f"A: {base_a}, B: {base_b}, C: {base_c}")

        time.sleep(1)
        result_ab = compare_texts_with_llm(content_a, content_b, base_a, base_b)
        print(f"比较 A vs B... 结果: {result_ab}")
        
        time.sleep(1)
        result_bc = compare_texts_with_llm(content_b, content_c, base_b, base_c)
        print(f"比较 B vs C... 结果: {result_bc}")

        time.sleep(1)
        result_ac = compare_texts_with_llm(content_a, content_c, base_a, base_c)
        print(f"比较 A vs C... 结果: {result_ac}")

        row_data = {
            "文本A": base_a,
            "文本B": base_b,
            "文本C": base_c,
            "比较结果 (A vs B)": "Error",
            "比较结果 (B vs C)": "Error",
            "比较结果 (A vs C)": "Error",
            "是否一致 (1=是, 0=否)": "Error"
        }

        if 'Error' not in [result_ab, result_bc, result_ac]:
            comp_ab_str = "A > B" if result_ab == 'A' else "B > A"
            comp_bc_str = "B > C" if result_bc == 'A' else "C > B"
            comp_ac_str = "A > C" if result_ac == 'A' else "C > A"
            
            row_data.update({
                "比较结果 (A vs B)": comp_ab_str,
                "比较结果 (B vs C)": comp_bc_str,
                "比较结果 (A vs C)": comp_ac_str
            })

            # ############################################################# #
            # ###            V2 核心一致性判断逻辑 (计分板法)           ### #
            # ############################################################# #
            
            wins = {'A': 0, 'B': 0, 'C': 0}

            # 统计 A vs B 的胜者
            if result_ab == 'A': wins['A'] += 1
            else: wins['B'] += 1
            
            # 统计 B vs C 的胜者 ('A'代表第一个参数B获胜)
            if result_bc == 'A': wins['B'] += 1
            else: wins['C'] += 1

            # 统计 A vs C 的胜者 ('A'代表第一个参数A获胜)
            if result_ac == 'A': wins['A'] += 1
            else: wins['C'] += 1
            
            # 检查得分是否为 (1, 1, 1)，这是唯一不一致的情况
            if wins['A'] == 1 and wins['B'] == 1 and wins['C'] == 1:
                is_consistent = False
                print("--> 结果：不一致。出现循环偏好（得分1,1,1）。")
            else:
                is_consistent = True
                print(f"--> 结果：一致。比较结果可形成稳定排序（得分为{wins['A']},{wins['B']},{wins['C']}）。")
            
            consistency_flag = 1 if is_consistent else 0
            row_data["是否一致 (1=是, 0=否)"] = consistency_flag
        else:
            print("--> 结果：由于API错误，此三元组测试无效。")

        results_data.append(row_data)
        tested_triplets_count += 1

    # --- 4. 结果汇总与文件生成 (无变化) ---
    if not results_data:
        print("\n没有生成任何结果，无法创建Excel文件。")
        return

    print(f"\n\n--- 所有测试完成，正在生成Excel报告 ---")
    
    df = pd.DataFrame(results_data)
    df = df[[
        "文本A", "文本B", "文本C",
        "比较结果 (A vs B)", "比较结果 (B vs C)", "比较结果 (A vs C)",
        "是否一致 (1=是, 0=否)"
    ]]
    
    try:
        df.to_excel(OUTPUT_EXCEL_FILE, index=False)
        print(f"✔ 成功！结果已保存到文件: '{OUTPUT_EXCEL_FILE}'")
    except Exception as e:
        print(f"❌ 错误：保存Excel文件失败。原因: {e}")
        
    valid_results = df[df["是否一致 (1=是, 0=否)"].isin([0, 1])]
    consistent_count = len(valid_results[valid_results["是否一致 (1=是, 0=否)"] == 1])
    inconsistent_count = len(valid_results[valid_results["是否一致 (1=是, 0=否)"] == 0])
    total_valid = len(valid_results)
    
    print("\n========================================")
    print("         内部一致性评估总结 (V2)")
    print("========================================")
    print(f"总共测试的三元组数量: {tested_triplets_count}")
    if total_valid > 0:
        consistency_rate = (consistent_count / total_valid) * 100
        print(f"有效测试: {total_valid} (一致: {consistent_count}, 不一致: {inconsistent_count})")
        print(f"内部一致性比率: {consistency_rate:.2f}%")
    else:
        print("没有完成任何有效测试，无法计算一致性比率。")
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
PLANNING_TEXTS_DIR = r"D:\1sdgplanning\1data\1全部批复" # 规划文本存放目录
NUM_TRIPLETS_TO_TEST = 20 # 需要测试的三元组数量
OUTPUT_EXCEL_FILE = "consistency_check_results_v2.xlsx" # 输出的Excel文件名

# --- 2. 核心功能函数 (无变化) ---

def get_all_text_files(directory: str) -> list:
    """获取指定目录下所有txt文件的完整路径。"""
    if not os.path.isdir(directory):
        print(f"错误：目录 '{directory}' 不存在。")
        return []
    
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.txt')]
    print(f"在 '{directory}' 中找到 {len(files)} 个txt文件。")
    return files

def read_text_content(filepath: str) -> str:
    """读取文本文件的内容。"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文件 '{filepath}' 时出错: {e}")
        return None

def compare_texts_with_llm(text_a: str, text_b: str, filename_a: str, filename_b: str) -> str:
    """使用DeepSeek API比较两个文本哪个更符合SDG。返回 'A', 'B', 或 'Error'。"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    请你扮演一位可持续发展领域的专家。下面是两份规划文本，名为“文本A”和“文本B”。
    你的任务是判断哪一份文本更全面、更深入、更具体地体现了联合国可持续发展目标（SDGs）。
    你的回答必须且只能是单个英文字母：“A”或“B”。

    ---
    文本A（来自文件: {filename_a}）:
    {text_a[:2000]}

    ---
    文本B（来自文件: {filename_b}）:
    {text_b[:2000]}
    ---

    请判断哪一份文本更符合SDGs？请仅回答 'A' 或 'B'。
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens": 5
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=60)
        response.raise_for_status()
        result_content = response.json()['choices'][0]['message']['content'].strip().upper()
        
        if result_content in ['A', 'B']:
            return result_content
        else:
            print(f"警告：API返回了意外的内容: '{result_content}'")
            return "Error"
            
    except requests.exceptions.RequestException as e:
        print(f"API请求失败: {e}")
        return "Error"
    except (KeyError, IndexError) as e:
        print(f"解析API响应失败: {e}")
        return "Error"

# --- 3. 主逻辑 (一致性判断已更新) ---

def main():
    """主执行函数"""
    print("--- 开始内部一致性评估 (V2逻辑) ---")
    
    all_files = get_all_text_files(PLANNING_TEXTS_DIR)
    
    if len(all_files) < 3:
        print("错误：文本文件不足3个，无法构成三元组进行测试。")
        return

    results_data = []
    tested_triplets_count = 0
    seen_triplets = set()

    print(f"\n准备随机抽取 {NUM_TRIPLETS_TO_TEST} 组三元组进行测试...")
    
    while tested_triplets_count < NUM_TRIPLETS_TO_TEST:
        try:
            sampled_files = random.sample(all_files, 3)
            sampled_files.sort()
            triplet_id = tuple(sampled_files)

            if triplet_id in seen_triplets:
                continue
            
            seen_triplets.add(triplet_id)
            
        except ValueError:
            print("警告：可用文件数量不足以继续抽取新的三元组。")
            break

        file_a, file_b, file_c = triplet_id
        
        content_a = read_text_content(file_a)
        content_b = read_text_content(file_b)
        content_c = read_text_content(file_c)

        if not all([content_a, content_b, content_c]):
            print(f"跳过三元组 {triplet_id} 因为其中一个文件读取失败。")
            continue
        
        current_triplet_num = tested_triplets_count + 1
        print(f"\n--- 正在测试第 {current_triplet_num}/{NUM_TRIPLETS_TO_TEST} 组三元组 ---")
        base_a, base_b, base_c = os.path.basename(file_a), os.path.basename(file_b), os.path.basename(file_c)
        print(f"A: {base_a}, B: {base_b}, C: {base_c}")

        time.sleep(1)
        result_ab = compare_texts_with_llm(content_a, content_b, base_a, base_b)
        print(f"比较 A vs B... 结果: {result_ab}")
        
        time.sleep(1)
        result_bc = compare_texts_with_llm(content_b, content_c, base_b, base_c)
        print(f"比较 B vs C... 结果: {result_bc}")

        time.sleep(1)
        result_ac = compare_texts_with_llm(content_a, content_c, base_a, base_c)
        print(f"比较 A vs C... 结果: {result_ac}")

        row_data = {
            "文本A": base_a,
            "文本B": base_b,
            "文本C": base_c,
            "比较结果 (A vs B)": "Error",
            "比较结果 (B vs C)": "Error",
            "比较结果 (A vs C)": "Error",
            "是否一致 (1=是, 0=否)": "Error"
        }

        if 'Error' not in [result_ab, result_bc, result_ac]:
            comp_ab_str = "A > B" if result_ab == 'A' else "B > A"
            comp_bc_str = "B > C" if result_bc == 'A' else "C > B"
            comp_ac_str = "A > C" if result_ac == 'A' else "C > A"
            
            row_data.update({
                "比较结果 (A vs B)": comp_ab_str,
                "比较结果 (B vs C)": comp_bc_str,
                "比较结果 (A vs C)": comp_ac_str
            })

            # ############################################################# #
            # ###            V2 核心一致性判断逻辑 (计分板法)           ### #
            # ############################################################# #
            
            wins = {'A': 0, 'B': 0, 'C': 0}

            # 统计 A vs B 的胜者
            if result_ab == 'A': wins['A'] += 1
            else: wins['B'] += 1
            
            # 统计 B vs C 的胜者 ('A'代表第一个参数B获胜)
            if result_bc == 'A': wins['B'] += 1
            else: wins['C'] += 1

            # 统计 A vs C 的胜者 ('A'代表第一个参数A获胜)
            if result_ac == 'A': wins['A'] += 1
            else: wins['C'] += 1
            
            # 检查得分是否为 (1, 1, 1)，这是唯一不一致的情况
            if wins['A'] == 1 and wins['B'] == 1 and wins['C'] == 1:
                is_consistent = False
                print("--> 结果：不一致。出现循环偏好（得分1,1,1）。")
            else:
                is_consistent = True
                print(f"--> 结果：一致。比较结果可形成稳定排序（得分为{wins['A']},{wins['B']},{wins['C']}）。")
            
            consistency_flag = 1 if is_consistent else 0
            row_data["是否一致 (1=是, 0=否)"] = consistency_flag
        else:
            print("--> 结果：由于API错误，此三元组测试无效。")

        results_data.append(row_data)
        tested_triplets_count += 1

    # --- 4. 结果汇总与文件生成 (无变化) ---
    if not results_data:
        print("\n没有生成任何结果，无法创建Excel文件。")
        return

    print(f"\n\n--- 所有测试完成，正在生成Excel报告 ---")
    
    df = pd.DataFrame(results_data)
    df = df[[
        "文本A", "文本B", "文本C",
        "比较结果 (A vs B)", "比较结果 (B vs C)", "比较结果 (A vs C)",
        "是否一致 (1=是, 0=否)"
    ]]
    
    try:
        df.to_excel(OUTPUT_EXCEL_FILE, index=False)
        print(f"✔ 成功！结果已保存到文件: '{OUTPUT_EXCEL_FILE}'")
    except Exception as e:
        print(f"❌ 错误：保存Excel文件失败。原因: {e}")
        
    valid_results = df[df["是否一致 (1=是, 0=否)"].isin([0, 1])]
    consistent_count = len(valid_results[valid_results["是否一致 (1=是, 0=否)"] == 1])
    inconsistent_count = len(valid_results[valid_results["是否一致 (1=是, 0=否)"] == 0])
    total_valid = len(valid_results)
    
    print("\n========================================")
    print("         内部一致性评估总结 (V2)")
    print("========================================")
    print(f"总共测试的三元组数量: {tested_triplets_count}")
    if total_valid > 0:
        consistency_rate = (consistent_count / total_valid) * 100
        print(f"有效测试: {total_valid} (一致: {consistent_count}, 不一致: {inconsistent_count})")
        print(f"内部一致性比率: {consistency_rate:.2f}%")
    else:
        print("没有完成任何有效测试，无法计算一致性比率。")
    print("========================================")

if __name__ == "__main__":
>>>>>>> e50b95b2529049900b3f37abd3dcf41a8db0f27e
    main()