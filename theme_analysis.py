import os
import time
from pathlib import Path
import requests

# 配置部分
API_KEY = "sk-6e8113f768cd42768058ce6dc6ef3401"  # 实际API密钥
API_URL = "https://api.deepseek.com/v1/chat/completions"
TEMPERATURE = 0.1

INPUT_DIRS = {
    "top50%": r"D:\1sdgplanning\3result\top50%",
    "bottom50%": r"D:\1sdgplanning\3result\bottom50%"
}

OUTPUT_BASE = r"D:\1sdgplanning\3result"
SYSTEM_PROMPT = """您是一位专业的规划文本分析师。"可持续发展目标"包括：
消除贫困
消除饥饿，实现粮食安全
确保健康的生活方式
确保优质教育
实现性别平等
提供水和环境卫生
提供可持续的现代能源
促进持久、包容和可持续经济增长
建设强大、包容和可持续的基础设施
减少不平等
使城市和人类居住地可持续发展
保护和可持续利用地球上的自然资源
采取紧急行动，应对气候变化及其影响
保护海洋和海洋资源
保护陆地生态系统
促进和平与公正
加强全球伙伴关系，实现可持续发展
请完成以下任务：

1. 提取文本中明确关于"可持续发展目标"的段落：[相关的段落]
2. 从这些段落中提取与"可持续发展目标"相关的最常出现的关键词:[关键词]
3. 从这些关键词中提取最相关的一个"可持续发展目标"：[可持续发展目标]

请用以下格式返回结果：
=== 相关段落 ===
[找到的相关段落，每段用引号标注]
=== 关键词 ===
[逗号分隔的关键词列表]
=== 相关可持续发展目标 ===
[找到的相关可持续发展目标]
"""

def process_to_txt(api_response, output_path):
    """将API响应转换为TXT格式并保存"""
    try:
        content = api_response['choices'][0]['message']['content']
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"保存结果失败: {e}")
        return False

def process_all_files():
    """处理所有文件(TXT输出版)"""
    for category, input_dir in INPUT_DIRS.items():
        output_dir = os.path.join(OUTPUT_BASE, f"{category}theme")
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n处理 {category} 文件...")
        
        for file_name in os.listdir(input_dir):
            if not file_name.endswith('.txt'):
                continue
                
            file_path = os.path.join(input_dir, file_name)
            print(f"正在处理: {file_name}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 调用API
                headers = {"Authorization": f"Bearer {API_KEY}"}
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": content}
                    ],
                    "temperature": TEMPERATURE
                }
                
                response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                
                # 保存TXT结果
                output_file = os.path.join(output_dir, f"theme_{file_name}")
                if process_to_txt(response.json(), output_file):
                    print(f"已保存: {output_file}")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"处理 {file_name} 时出错: {e}")

if __name__ == "__main__":
    if API_KEY == "your-deepseek-api-key":
        print("请替换为您的真实DeepSeek API密钥")
        exit()
    
    process_all_files()
    print("\n处理完成! 结果保存在*theme文件夹中")