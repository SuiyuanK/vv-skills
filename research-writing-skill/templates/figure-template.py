"""
Figure Template - 科学图表生成模板
使用方法：复制此文件到对应章节文件夹，修改main()函数中的绑定代码
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path

# ============================================================
# 中文字体配置
# ============================================================
CHINESE_FONT = None

# macOS字体路径
font_candidates_mac = [
    '/System/Library/Fonts/STHeiti Light.ttc',
    '/System/Library/Fonts/Supplemental/Songti.ttc',
    '/Library/Fonts/Songti.ttc',
    '/System/Library/Fonts/PingFang.ttc',
]

# Windows字体路径
font_candidates_win = [
    'C:/Windows/Fonts/simhei.ttf',
    'C:/Windows/Fonts/msyh.ttc',
]

# 尝试加载字体
for fp in font_candidates_mac + font_candidates_win:
    if Path(fp).exists():
        CHINESE_FONT = fm.FontProperties(fname=fp)
        break

# 备用方案
if CHINESE_FONT is None:
    plt.rcParams['font.sans-serif'] = ['Heiti TC', 'STHeiti', 'SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 顶刊级配色方案
# ============================================================

# Nature/Science 风格配色
COLORS_NATURE = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#95C623']

# Cell 风格配色
COLORS_CELL = ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F', '#EDC948']

# 渐变色（热力图用）
BLUE_GRADIENT = ['#A8DADC', '#6DAEDB', '#457B9D', '#2C5F7C', '#1D3557']

# 色盲友好配色
COLORS_COLORBLIND = ['#0077BB', '#33BBEE', '#009988', '#EE7733', '#CC3311', '#EE3377']

# 默认使用Cell风格
COLORS = COLORS_CELL

# ============================================================
# 全局样式设置
# ============================================================

def setup_plot_style():
    """配置全局绑定样式 - 450 DPI，学术风格"""
    plt.rcParams.update({
        # 字体设置
        'font.family': 'sans-serif',
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        
        # 线条和标记
        'lines.linewidth': 1.5,
        'lines.markersize': 6,
        
        # 坐标轴
        'axes.linewidth': 1.0,
        'axes.spines.top': False,
        'axes.spines.right': False,
        
        # 网格
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.linewidth': 0.5,
        
        # 图例
        'legend.frameon': False,
        'legend.loc': 'best',
        
        # 保存设置
        'savefig.dpi': 450,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
    })


def save_figure(fig, output_dir, fig_name):
    """保存图片为PNG和SVG格式"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # PNG格式（450 DPI）
    fig.savefig(output_dir / f'{fig_name}.png', dpi=450, format='png', 
                facecolor='white', edgecolor='none')
    
    # SVG格式（矢量图）
    fig.savefig(output_dir / f'{fig_name}.svg', format='svg',
                facecolor='white', edgecolor='none')
    
    print(f"✓ 图片已保存:")
    print(f"  - {output_dir / f'{fig_name}.png'}")
    print(f"  - {output_dir / f'{fig_name}.svg'}")


# ============================================================
# 示例绑定函数
# ============================================================

def plot_line_chart(ax, x, y_dict, xlabel='X轴', ylabel='Y轴', title=None):
    """绑制折线图"""
    for i, (label, y) in enumerate(y_dict.items()):
        ax.plot(x, y, color=COLORS[i % len(COLORS)], label=label, 
                linewidth=1.5, marker='o', markersize=4)
    
    if CHINESE_FONT:
        ax.set_xlabel(xlabel, fontproperties=CHINESE_FONT)
        ax.set_ylabel(ylabel, fontproperties=CHINESE_FONT)
        if title:
            ax.set_title(title, fontproperties=CHINESE_FONT)
        ax.legend(prop=CHINESE_FONT)
    else:
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title)
        ax.legend()


def plot_bar_chart(ax, categories, values, xlabel='类别', ylabel='数值', title=None):
    """绘制条形图"""
    colors = COLORS[:len(categories)]
    x_pos = np.arange(len(categories))
    bars = ax.bar(x_pos, values, color=colors, edgecolor='white', linewidth=0.5)
    
    ax.set_xticks(x_pos)
    if CHINESE_FONT:
        ax.set_xticklabels(categories, fontproperties=CHINESE_FONT)
        ax.set_xlabel(xlabel, fontproperties=CHINESE_FONT)
        ax.set_ylabel(ylabel, fontproperties=CHINESE_FONT)
        if title:
            ax.set_title(title, fontproperties=CHINESE_FONT)
    else:
        ax.set_xticklabels(categories)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title)
    
    return bars


def plot_heatmap(ax, data, xlabel='X轴', ylabel='Y轴', title=None, cmap=None):
    """绘制热力图"""
    if cmap is None:
        from matplotlib.colors import LinearSegmentedColormap
        cmap = LinearSegmentedColormap.from_list('custom', BLUE_GRADIENT)
    
    im = ax.imshow(data, cmap=cmap, aspect='auto')
    plt.colorbar(im, ax=ax)
    
    if CHINESE_FONT:
        ax.set_xlabel(xlabel, fontproperties=CHINESE_FONT)
        ax.set_ylabel(ylabel, fontproperties=CHINESE_FONT)
        if title:
            ax.set_title(title, fontproperties=CHINESE_FONT)
    else:
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title)
    
    return im


# ============================================================
# 主函数
# ============================================================

def main():
    setup_plot_style()
    
    # ========== 在此处编写具体绑定代码 ==========
    
    # 示例：创建一个简单的折线图
    fig, ax = plt.subplots(figsize=(7, 5))
    
    x = np.linspace(0, 10, 50)
    y_dict = {
        '模型A': np.sin(x) + np.random.normal(0, 0.1, len(x)),
        '模型B': np.cos(x) + np.random.normal(0, 0.1, len(x)),
        '模型C': np.sin(x) * 0.5 + 0.5 + np.random.normal(0, 0.1, len(x)),
    }
    
    plot_line_chart(ax, x, y_dict, xlabel='时间 (s)', ylabel='幅值', title='模型性能对比')
    
    # ========== 绑定代码结束 ==========
    
    # 保存图片
    output_dir = Path(__file__).parent
    fig_name = Path(__file__).stem
    save_figure(fig, output_dir, fig_name)
    
    plt.show()


if __name__ == '__main__':
    main()
