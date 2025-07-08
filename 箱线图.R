# 1. 加载必要的库
library(tidyverse) # 用于数据处理和ggplot2绘图
library(readxl)    # 用于读取Excel文件
library(ggprism)   # 用于Graphpad Prism风格的主题和标尺
library(showtext)  # 加载showtext以便管理字体，如果需要的话


# 2. 读取Excel数据
file_path <- "D:\\1sdgplanning\\1data\\xiangxian.xlsx"
sheet_name <- "data"
plot_data <- read_excel(file_path, sheet = sheet_name)

# 3. 数据准备
plot_data$cluster <- factor(plot_data$cluster)
plot_data_long <- plot_data %>%
  pivot_longer(cols = starts_with("SDG"),
               names_to = "SDG_Indicator",
               values_to = "Value")

# --- 新增代码：设置SDG_Indicator的因子水平顺序 ---
# 创建期望的SDG指标顺序
# (例如 SDG1, SDG2, ..., SDG9, SDG10, ..., SDG16)
# 确保这里的名称与您数据中的SDG列名完全一致
expected_sdg_order <- paste0("SDG", 1:16)

# 将SDG_Indicator列转换为因子，并指定其水平顺序
plot_data_long$SDG_Indicator <- factor(plot_data_long$SDG_Indicator, levels = expected_sdg_order)
# ----------------------------------------------------

# 4. 定义字体和字体大小参数
font_family_to_use <- "serif" # 使用通用serif字体族

axis_title_font_size <- 10
axis_text_font_size  <- 10
strip_text_font_size <- 10
plot_title_font_size <- 10
legend_text_font_size<- 10

# 5. 定义绘图主题
# 5. 定义绘图主题
mytheme <- theme_prism() +  # theme_prism() 本身可能已对刻度线有默认设置
  theme(
    plot.title = element_text(size = plot_title_font_size, family = font_family_to_use, hjust = 0.5),
    strip.text = element_text(size = strip_text_font_size, family = font_family_to_use),
    axis.title = element_text(color = "black", size = axis_title_font_size, family = font_family_to_use),
    axis.text.y = element_text(color = "black", size = axis_text_font_size, family = font_family_to_use),
    axis.text.x = element_text(color = "black", size = axis_text_font_size, family = font_family_to_use,
                               angle = 0,
                               hjust = 0.5,
                               vjust = 1),
    legend.text = element_text(size = legend_text_font_size, family = font_family_to_use),
    legend.title = element_text(size = axis_title_font_size, family = font_family_to_use),
    
    # --- 修改刻度线粗细在这里 ---
    axis.line = element_line(color = "black", linewidth = 0.1), # 这是坐标轴本身的线
    axis.ticks = element_line(color = "black", linewidth = 0.1), # 控制所有刻度线 (X和Y轴)

    
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(linewidth = 0.2, color = "#e5e5e5"),
    legend.position = "none"
  )

# 6. 定义颜色
color_palette <- c("#db6968", "#4d97cd", "#f8984e", "#459943", "#8a60b0")

# 7. 创建ggplot对象
p <- ggplot(plot_data_long, aes(x = cluster, y = Value)) +
  stat_boxplot(geom = "errorbar",
               position = position_dodge(width = 0.75),
               width = 0.2,
               color = "black",
               aes(group = cluster)) +
  geom_boxplot(fill = "white",
               color = "black",
               position = position_dodge(width = 0.75),
               width = 0.75,   #修改箱体宽度
               outlier.shape = NA,
               aes(group = cluster)) +
  geom_point(aes(fill = cluster, color = cluster), # <--- 修改这里：同时将 color 映射到 cluster
             pch = 21,
             size = 0.5,
             position = position_jitterdodge(jitter.width = 0.2, dodge.width = 0.75)) +
  facet_wrap(~SDG_Indicator, nrow = 4, ncol = 4, scales = "free_y") +
  scale_x_discrete(guide = "prism_bracket") +
  scale_y_continuous(guide = "prism_offset_minor") +
  scale_fill_manual(values = color_palette) + # 用于点的填充色
  scale_color_manual(values = color_palette) + # <--- 新增：用于点的轮廓色，使用相同的调色板
  labs(x = "Cluster", y = "SDGs Similarity") +
  mytheme

# 8. 显示图像
print(p)

output_directory <- "D:/1sdgplanning/5fig/出图" 

# 检查目录是否存在，如果不存在则创建 (recursive = TRUE 会创建所有必需的父目录)
if (!dir.exists(output_directory)) {
  dir.create(output_directory, recursive = TRUE, showWarnings = FALSE)
  message(paste("Created directory:", output_directory))
} else {
  message(paste("Directory already exists:", output_directory))
}

# 定义文件名
# 您可以根据需要修改文件名
plot_filename_jpg <- file.path(output_directory, "sdg_cluster_analysis_plot.jpg")

# 保存为PNG格式
ggsave(filename = plot_filename_jpg,
       plot = p,
       width = 14,        
       height = 14,
       units = "cm",
       dpi = 600,         # 分辨率
       bg = "white")      # 背景

message(paste("Plot saved as jpg:", plot_filename_jpg))