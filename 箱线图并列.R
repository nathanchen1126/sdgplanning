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

# --- 设置SDG_Indicator的因子水平顺序 ---
expected_sdg_order <- paste0("SDG", 1:16)
plot_data_long$SDG_Indicator <- factor(plot_data_long$SDG_Indicator, levels = expected_sdg_order)

# --- 为 facet_grid 创建行和列变量 ---
sdg_map <- tibble(
  SDG_Indicator = factor(expected_sdg_order, levels = expected_sdg_order),
  facet_row = factor(rep(1:4, each = 4)), 
  facet_col = factor(rep(1:4, times = 4)) 
)

plot_data_long <- plot_data_long %>%
  left_join(sdg_map, by = "SDG_Indicator")

# 4. 定义字体和字体大小参数
font_family_to_use <- "serif"
axis_title_font_size <- 10
axis_text_font_size  <- 10
plot_title_font_size <- 10
legend_text_font_size<- 10
sdg_label_in_plot_font_size_pt <- 8

# --- 为图内SDG标签准备数据 ---
cluster_levels_for_plot <- levels(plot_data_long$cluster)
first_cluster_level_for_text <- cluster_levels_for_plot[1]

sdg_labels_data <- plot_data_long %>%
  dplyr::distinct(SDG_Indicator, facet_row, facet_col) %>% 
  dplyr::mutate(
    label = as.character(SDG_Indicator),
    cluster_text_pos = factor(first_cluster_level_for_text, levels = cluster_levels_for_plot),
    value_text_pos = 0.44 
  )

# 5. 定义绘图主题
mytheme <- theme_prism() +
  theme(
    plot.title = element_text(size = plot_title_font_size, family = font_family_to_use, hjust = 0.5),
    strip.text = element_blank(),
    strip.background = element_blank(),
    axis.title = element_text(color = "black", size = axis_title_font_size, family = font_family_to_use),
    axis.text.y = element_text(color = "black", size = axis_text_font_size, family = font_family_to_use),
    axis.text.x = element_text(color = "black", size = axis_text_font_size, family = font_family_to_use,
                               angle = 0, hjust = 0.5, vjust = 1),
    legend.text = element_text(size = legend_text_font_size, family = font_family_to_use),
    legend.title = element_text(size = axis_title_font_size, family = font_family_to_use),
    axis.line = element_line(color = "black", linewidth = 0.1),
    axis.ticks = element_line(color = "black", linewidth = 0.1),
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(linewidth = 0.2, color = "#e5e5e5"),
    legend.position = "none",
    panel.border = element_rect(colour = "black", fill = NA, linewidth = 0.5),
    panel.spacing = unit(0.2, "lines") 
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
               width = 0.75,
               outlier.shape = NA,
               aes(group = cluster)) +
  geom_point(aes(fill = cluster, color = cluster),
             pch = 21,
             size = 0.5,
             position = position_jitterdodge(jitter.width = 0.2, dodge.width = 0.75)) +
  
  geom_text(
    data = sdg_labels_data,
    aes(x = cluster_text_pos, y = value_text_pos, label = label),
    family = font_family_to_use,
    size = sdg_label_in_plot_font_size_pt * 0.352778, 
    hjust = 0,
    vjust = 1,
    color = "black",
    inherit.aes = FALSE
  ) +
  
  facet_grid(rows = vars(facet_row), cols = vars(facet_col), scales = "free_y") +
  
  coord_cartesian(ylim = c(0.25, 0.45)) + 
  
  scale_x_discrete(guide = "prism_bracket") +
  scale_y_continuous(guide = "prism_offset_minor", breaks = c(0.25, 0.35, 0.45)) + # Y轴刻度明确指定
  
  scale_fill_manual(values = color_palette) +
  scale_color_manual(values = color_palette) +
  labs(x = "Cluster", y = "SDGs Similarity") +
  mytheme

# 8. 显示图像
print(p)

# 9. 保存图像
output_directory <- "D:/1sdgplanning/5fig/出图"

if (!dir.exists(output_directory)) {
  dir.create(output_directory, recursive = TRUE, showWarnings = FALSE)
  message(paste("Created directory:", output_directory))
} else {
  message(paste("Directory already exists:", output_directory))
}

plot_filename_jpg <- file.path(output_directory, "sdg_cluster_analysis.jpg") # 更新文件名

ggsave(filename = plot_filename_jpg,
       plot = p,
       width = 14, 
       height = 14,
       units = "cm",
       dpi = 600,
       bg = "white")

message(paste("Plot saved as jpg:", plot_filename_jpg))