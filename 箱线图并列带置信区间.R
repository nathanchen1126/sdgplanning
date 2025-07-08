# 1. 加载必要的库
library(tidyverse) # 用于数据处理和ggplot2绘图
library(readxl)    # 用于读取Excel文件
library(ggprism)   # 用于Graphpad Prism风格的主题和标尺
library(showtext)  # 加载showtext以便管理字体，如果需要的话
library(ggpmisc)   # <--- 新增: 用于 stat_poly_eq 函数

# 2. 读取Excel数据
file_path <- "D:\\1sdgplanning\\1data\\xiangxian.xlsx" # 请确保文件路径正确
sheet_name <- "data"
plot_data <- read_excel(file_path, sheet = sheet_name)

# 3. 数据准备
plot_data$cluster <- factor(plot_data$cluster) # 将cluster列转换为因子类型
plot_data_long <- plot_data %>%
  pivot_longer(cols = starts_with("SDG"),    # 将以"SDG"开头的列转换为长格式
               names_to = "SDG_Indicator",   # 新的指标名称列
               values_to = "Value")          # 新的指标值列

# --- 设置SDG_Indicator的因子水平顺序 ---
expected_sdg_order <- paste0("SDG", 1:16) # 定义期望的SDG顺序
plot_data_long$SDG_Indicator <- factor(plot_data_long$SDG_Indicator, levels = expected_sdg_order) # 应用因子水平顺序

# --- 为 facet_grid 创建行和列变量 ---
sdg_map <- tibble(
  SDG_Indicator = factor(expected_sdg_order, levels = expected_sdg_order), # SDG指标
  facet_row = factor(rep(1:4, each = 4)),  # 定义分面网格的行变量 (4行)
  facet_col = factor(rep(1:4, times = 4))  # 定义分面网格的列变量 (4列)
)

plot_data_long <- plot_data_long %>%
  left_join(sdg_map, by = "SDG_Indicator") # 将分面映射信息合并到主数据

# 4. 定义字体和字体大小参数
font_family_to_use <- "serif" # 设置要使用的字体族
axis_title_font_size <- 10    # 坐标轴标题字体大小
axis_text_font_size  <- 10    # 坐标轴刻度文字体大小
plot_title_font_size <- 10    # 图表标题字体大小
legend_text_font_size<- 10    # 图例文字字体大小
sdg_label_in_plot_font_size_pt <- 8 # 图内SDG标签的字体大小 (磅)

# --- 为图内SDG标签准备数据 ---
cluster_levels_for_plot <- levels(plot_data_long$cluster) # 获取cluster的因子水平
first_cluster_level_for_text <- cluster_levels_for_plot[1] # 获取第一个cluster水平，用于文本定位

sdg_labels_data <- plot_data_long %>%
  dplyr::distinct(SDG_Indicator, facet_row, facet_col) %>%  # 获取每个SDG指标及其分面位置的唯一组合
  dplyr::mutate(
    label = as.character(SDG_Indicator), # SDG指标的文本标签
    cluster_text_pos = factor(first_cluster_level_for_text, levels = cluster_levels_for_plot), # 文本标签在x轴的位置 (第一个cluster)
    value_text_pos = 0.44  # 文本标签在y轴的绝对位置
  )

# 5. 定义绘图主题
mytheme <- theme_prism() + # 使用ggprism预设主题
  theme(
    plot.title = element_text(size = plot_title_font_size, family = font_family_to_use, hjust = 0.5), # 图表标题设置
    strip.text = element_blank(), # 隐藏分面标签的文本
    strip.background = element_blank(), # 隐藏分面标签的背景
    axis.title = element_text(color = "black", size = axis_title_font_size, family = font_family_to_use), # 坐标轴标题设置
    axis.text.y = element_text(color = "black", size = axis_text_font_size, family = font_family_to_use), # Y轴刻度文字设置
    axis.text.x = element_text(color = "black", size = axis_text_font_size, family = font_family_to_use, # X轴刻度文字设置
                               angle = 0, hjust = 0.5, vjust = 1), # X轴刻度文字旋转角度和对齐
    legend.text = element_text(size = legend_text_font_size, family = font_family_to_use), # 图例文字设置
    legend.title = element_text(size = axis_title_font_size, family = font_family_to_use), # 图例标题设置
    axis.line = element_line(color = "black", linewidth = 0.1), # 坐标轴线设置
    axis.ticks = element_line(color = "black", linewidth = 0.1), # 坐标轴刻度线设置
    panel.grid.minor = element_blank(), # 移除次要网格线
    panel.grid.major = element_line(linewidth = 0.2, color = "#e5e5e5"), # 主要网格线设置
    legend.position = "none", # 移除图例
    panel.border = element_rect(colour = "black", fill = NA, linewidth = 0.5), # 面板边框设置
    panel.spacing = unit(0.2, "lines")  # 分面之间的间距
  )

# 6. 定义颜色
color_palette <- c("#db6968", "#4d97cd", "#f8984e", "#459943", "#8a60b0") # 定义颜色板

# 7. 创建ggplot对象
p <- ggplot(plot_data_long, aes(x = cluster, y = Value)) + # 主ggplot对象，设置x和y轴映射
  stat_boxplot(geom = "errorbar", # 添加误差棒 (代表箱线图的须)
               position = position_dodge(width = 0.75), # 位置调整，避免重叠
               width = 0.2, # 误差棒的宽度
               color = "black",
               aes(group = cluster)) + # 按cluster分组，确保误差棒正确绘制
  geom_boxplot(fill = "white", # 添加箱线图主体
               color = "black", # 箱线图边框颜色
               position = position_dodge(width = 0.75), # 位置调整
               width = 0.75, # 箱线图的宽度
               outlier.shape = NA, # 不显示异常值点 (因为下面用geom_point绘制)
               aes(group = cluster)) + # 按cluster分组
  geom_point(aes(fill = cluster, color = cluster), # 添加抖动散点
             pch = 21, # 点的形状 (可填充)
             size = 0.5, # 点的大小
             position = position_jitterdodge(jitter.width = 0.2, dodge.width = 0.75)) + # 添加抖动和闪避，避免点重叠
  
  # --- 新增: 拟合曲线 ---
  geom_smooth(aes(x = as.numeric(cluster), y = Value, group = 1), # group=1 表示每个分面绘制一条拟合线
              method = "lm",  # 使用线性模型进行拟合
              color = "#ee4f4f", # 拟合曲线颜色
              level = 0.95, # 置信区间水平 (95%)
              formula = y ~ poly(x, 3, raw = TRUE), # 二次多项式回归: y = a*x^2 + b*x + c
              linetype = 2, # 拟合曲线的线型
              alpha = 0.30, # 置信区间填充的透明度
              linewidth = 0.2, # 拟合曲线的线宽
              se = TRUE) + # 显示置信区间 (se = standard error)

  
  geom_text( # 添加SDG指标标签到图内
    data = sdg_labels_data, # 使用预处理好的SDG标签数据
    aes(x = cluster_text_pos, y = value_text_pos, label = label), # 标签的位置和内容
    family = font_family_to_use, # 字体
    size = sdg_label_in_plot_font_size_pt * 0.352778, # 字体大小 (pt转换为ggplot单位)
    hjust = 0, # 文本左对齐
    vjust = 1, # 文本的顶部与设定的y位置对齐
    color = "black", # 文本颜色
    inherit.aes = FALSE # 不继承主ggplot的aes映射
  ) +
  
  facet_grid(rows = vars(facet_row), cols = vars(facet_col), scales = "free_y") + # 创建分面网格，y轴自由缩放
  
  coord_cartesian(ylim = c(0.25, 0.45)) +  # 设置y轴的显示范围 (可能会裁剪部分超出范围的图形元素)
  
  scale_x_discrete(guide = "prism_bracket") + # X轴使用prism风格的括号指南
  scale_y_continuous(guide = "prism_offset_minor", breaks = c(0.25, 0.35, 0.45)) + # Y轴刻度明确指定，并使用prism风格
  
  scale_fill_manual(values = color_palette) + # 手动设置填充颜色
  scale_color_manual(values = color_palette) + # 手动设置边框/点颜色
  labs(x = "Cluster", y = "SDGs Similarity") + # 设置坐标轴标签
  mytheme # 应用自定义主题

# 8. 显示图像
print(p)

# 9. 保存图像
output_directory <- "D:/1sdgplanning/5fig/出图" # 定义输出目录

if (!dir.exists(output_directory)) { # 如果目录不存在
  dir.create(output_directory, recursive = TRUE, showWarnings = FALSE) # 创建目录 (recursive=TRUE允许创建多级目录)
  message(paste("已创建目录:", output_directory))
} else {
  message(paste("目录已存在:", output_directory))
}

plot_filename_jpg <- file.path(output_directory, "sdg_cluster_analysis.jpg") # 更新文件名

ggsave(filename = plot_filename_jpg, # 保存的文件名
       plot = p, # 要保存的ggplot对象
       width = 14,  # 图像宽度 (单位: cm)
       height = 14, # 图像高度 (单位: cm)
       units = "cm", # 宽高单位
       dpi = 600, # 图像分辨率 (dots per inch)
       bg = "white") # 图像背景色

message(paste("图像已保存为 jpg:", plot_filename_jpg))