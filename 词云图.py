#-------------------------------------------------------------------------------#
                                # Packages #
#-------------------------------------------------------------------------------#
import os
import random
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud

#-------------------------------------------------------------------------------#
                        # Load Excel and Setup Paths #
#-------------------------------------------------------------------------------#
file_path = r"D:\1sdgplanning\1data\词云.xlsx"
output_dir = r"D:\1sdgplanning\5fig\出图"
os.makedirs(output_dir, exist_ok=True)

df = pd.read_excel(file_path)

#-------------------------------------------------------------------------------#
                   # Prepare word list and frequency #
#-------------------------------------------------------------------------------#
keywords_list = df['Keywords'].dropna().astype(str).tolist()
chinese_list = df['Original text in Chinese'].dropna().astype(str).tolist()

def make_uniform_dict(word_list):
    return {word: 1 for word in word_list}

keywords_freq = make_uniform_dict(keywords_list)
chinese_freq = make_uniform_dict(chinese_list)

#-------------------------------------------------------------------------------#
                # Nature-style low-saturation color scheme #
#-------------------------------------------------------------------------------#
def nature_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    palette = [
        "rgb(0, 114, 178)",     # 蓝
        "rgb(213, 94, 0)",      # 橙
        "rgb(204, 121, 167)",   # 紫
        "rgb(86, 180, 233)",    # 浅蓝
        "rgb(230, 159, 0)",     # 金黄
        "rgb(0, 158, 115)",     # 绿
    ]
    return random.choice(palette)

#-------------------------------------------------------------------------------#
                 # Word Cloud Generation Function #
#-------------------------------------------------------------------------------#
def generate_wordcloud_from_dict(frequencies, font_path, output_filename):
    width_cm = 10
    height_cm = 7
    width_in = width_cm / 2.54
    height_in = height_cm / 2.54

    wc = WordCloud(
        width=800,
        height=560,
        background_color='white',
        font_path=font_path,
        color_func=nature_color_func,
        collocations=False,
        prefer_horizontal=1.0,
        include_numbers=False,
        normalize_plurals=False,
        max_words=200,
        max_font_size=38,
        min_font_size=25,
        margin=0                # 去除词语间默认空隙
    ).generate_from_frequencies(frequencies)

    plt.figure(figsize=(width_in, height_in))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)

    output_path = os.path.join(output_dir, output_filename)
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except PermissionError:
            print(f"⚠ 文件被占用，无法覆盖：{output_path}")
            return

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ 词云图已保存完成：{output_path}")

#-------------------------------------------------------------------------------#
                        # Generate Word Clouds #
#-------------------------------------------------------------------------------#
generate_wordcloud_from_dict(
    keywords_freq,
    font_path="C:/Windows/Fonts/arial.ttf",
    output_filename="keywords_wordcloud_nature.png"
)

generate_wordcloud_from_dict(
    chinese_freq,
    font_path="C:/Windows/Fonts/simhei.ttf",
    output_filename="chinese_wordcloud_nature.png"
)
