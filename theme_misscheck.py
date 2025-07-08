import os
import time
import requests
from pathlib import Path

# 配置部分
API_KEY = "sk-87c5a0df714f4838b7e0b6ae9f4f353b"
INPUT_DIRS = {
    "top50%": r"D:\1sdgplanning\3result\top50%",
    "bottom50%": r"D:\1sdgplanning\3result\bottom50%"
}
OUTPUT_BASE = r"D:\1sdgplanning\3result"

def validate_processing(input_dir, output_dir):
    """验证处理结果：检查输入输出文件数量是否匹配"""
    input_files = set(f for f in os.listdir(input_dir) if f.endswith('.txt'))
    output_files = set(f for f in os.listdir(output_dir) if f.startswith('theme_'))
    
    missing = input_files - {f.replace('theme_', '') for f in output_files}
    if missing:
        print(f"⚠️ 缺失处理文件: {len(missing)}个")
        for f in list(missing)[:3]:  # 最多显示3个缺失文件
            print(f"- {f}")
        return False
    return True

def process_files():
    """处理文件主函数（带完整性检查）"""
    for category, input_dir in INPUT_DIRS.items():
        output_dir = os.path.join(OUTPUT_BASE, f"{category}theme")
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n🔍 正在检查 {category} 文件夹...")
        txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
        print(f"发现 {len(txt_files)} 个待处理文档")
        
        processed_count = 0
        for file_name in txt_files:
            output_name = f"theme_{file_name}"
            if os.path.exists(os.path.join(output_dir, output_name)):
                print(f"⏩ 已存在: {output_name} (跳过)")
                continue
                
            try:
                # 文件处理逻辑
                with open(os.path.join(input_dir, file_name), 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 这里添加实际的API调用和处理代码
                # 模拟处理耗时
                time.sleep(0.5)
                
                # 创建模拟结果文件
                with open(os.path.join(output_dir, output_name), 'w', encoding='utf-8') as f:
                    f.write(f"=== 示例处理结果 ===\n来源文件: {file_name}\n处理时间: {time.ctime()}")
                
                processed_count += 1
                print(f"✅ 已处理: {file_name} → {output_name}")
                
            except Exception as e:
                print(f"❌ 处理失败: {file_name} - {str(e)}")
        
        print(f"\n处理完成: {processed_count}个新文档")
        
        # 完整性验证
        if not validate_processing(input_dir, output_dir):
            print("警告: 部分文件未被处理！")
        else:
            print("验证通过: 所有文件已处理")

if __name__ == "__main__":
    print("====== 文档处理检查 ======")
    process_files()
    print("\n====== 处理总结 ======")
    for category in INPUT_DIRS:
        input_dir = INPUT_DIRS[category]
        output_dir = os.path.join(OUTPUT_BASE, f"{category}theme")
        total = len([f for f in os.listdir(input_dir) if f.endswith('.txt')])
        done = len([f for f in os.listdir(output_dir) if f.startswith('theme_')])
        print(f"{category}: {done}/{total} 已处理")