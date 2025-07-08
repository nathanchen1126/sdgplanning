# -*- coding: utf-8 -*-
import os
import pdfplumber
import docx
import win32com.client as win32
import time


# --- 配置区 ---
# 源文件夹路径，存放pdf, doc, docx文件的位置
source_folder = r"D:\国空txt"
# 输出文件夹路径，用于存放转换后的txt文件
output_folder = r"D:\国空txt\txt"
# --- 配置区结束 ---

def convert_pdf_to_txt(file_path, output_path):
    """
    使用 pdfplumber 将 PDF 文件转换为 TXT 文件。
    """
    try:
        full_text = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)
        
        with open(output_path, "w", encoding='utf-8') as f:
            f.write("\n".join(full_text))
        print(f"✅ 成功转换 PDF: {os.path.basename(file_path)}")
        return True
    except Exception as e:
        print(f"❌ 转换 PDF 失败: {os.path.basename(file_path)}。原因: {e}")
        return False

def convert_docx_to_txt(file_path, output_path):
    """
    使用 python-docx 将 DOCX 文件转换为 TXT 文件。
    """
    try:
        doc = docx.Document(file_path)
        full_text = [para.text for para in doc.paragraphs]
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(full_text))
        print(f"✅ 成功转换 DOCX: {os.path.basename(file_path)}")
        return True
    except Exception as e:
        print(f"❌ 转换 DOCX 失败: {os.path.basename(file_path)}。原因: {e}")
        return False

def convert_doc_to_txt(file_path, output_path):
    """
    使用 win32com 调用 Word 程序将 DOC 文件转换为 TXT 文件。
    注意：此功能需要 Windows 环境和安装 Microsoft Word。
    """
    word_app = None
    doc = None
    try:
        # 使用绝对路径
        abs_file_path = os.path.abspath(file_path)
        abs_output_path = os.path.abspath(output_path)

        # 启动 Word 应用程序
        word_app = win32.Dispatch("Word.Application")
        word_app.Visible = False # 不显示Word界面

        # 打开 .doc 文件
        doc = word_app.Documents.Open(abs_file_path)

        # 另存为TXT，使用UTF-8编码 (65001)
        # 7 对应 wdFormatEncodedText
        doc.SaveAs2(abs_output_path, FileFormat=7, Encoding=65001)
        
        print(f"✅ 成功转换 DOC: {os.path.basename(file_path)}")
        return True
    except Exception as e:
        print(f"❌ 转换 DOC 失败: {os.path.basename(file_path)}。原因: {e}")
        return False
    finally:
        # 确保关闭文档和Word程序
        if doc:
            doc.Close(False) # False表示不保存更改
        if word_app:
            word_app.Quit()
        # 等待一小段时间确保进程完全退出
        time.sleep(0.5)


def process_files():
    """
    主处理函数，遍历源文件夹并执行转换。
    """
    # 1. 检查并创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"创建输出文件夹: {output_folder}")

    # 2. 遍历源文件夹中的所有文件
    print("-" * 50)
    print(f"开始扫描文件夹: {source_folder}")
    
    # 支持的文件扩展名
    supported_extensions = {
        '.pdf': convert_pdf_to_txt,
        '.docx': convert_docx_to_txt,
        '.doc': convert_doc_to_txt
    }
    
    # 统计转换结果
    success_count = 0
    fail_count = 0
    skipped_count = 0

    for filename in os.listdir(source_folder):
        file_path = os.path.join(source_folder, filename)
        
        # 检查是否是文件
        if not os.path.isfile(file_path):
            continue

        # 获取文件名和扩展名
        base_name, extension = os.path.splitext(filename)
        extension = extension.lower() # 转换为小写以匹配

        if extension in supported_extensions:
            # 定义输出文件路径
            output_txt_path = os.path.join(output_folder, f"{base_name}.txt")
            
            # 如果文件已存在，则跳过
            if os.path.exists(output_txt_path):
                print(f"🟡 文件已存在，跳过: {filename}")
                skipped_count += 1
                continue
            
            # 调用对应的转换函数
            converter_function = supported_extensions[extension]
            if converter_function(file_path, output_txt_path):
                success_count += 1
            else:
                fail_count += 1
        
    print("-" * 50)
    print("转换任务完成！")
    print(f"总计: 成功 {success_count} 个, 失败 {fail_count} 个, 跳过 {skipped_count} 个。")
    print(f"转换后的文件已保存至: {output_folder}")
    print("-" * 50)


if __name__ == '__main__':
    process_files()

