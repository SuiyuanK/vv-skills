---
name: figures-python
description: Use when creating data visualizations for papers - generates publication-quality plots with top-journal color schemes
---

# Python 数据图表

本技能指导使用 Python 生成科研论文级别的数据图表。

## Checklist

- [ ] 确认 conda 环境已激活（research）
- [ ] 确认图表类型和数据
- [ ] 记录数据清单（data manifest）
- [ ] 若使用 mock/synthetic 数据，明确标注为 planning data
- [ ] 使用顶刊配色方案
- [ ] 设置 450 DPI 分辨率
- [ ] 同时输出 PNG 和 SVG
- [ ] 检查中文字体显示
- [ ] 保存到 figures/ 目录

## 一、环境要求

### 1.1 conda 环境

**默认环境名**：`research`

**激活命令**：
```bash
conda activate research
```

**必需库**：
```bash
pip install matplotlib seaborn numpy pandas
```

如环境未配置，调用 `environment-setup` 技能。

## 二、图表规范

### 2.0 数据清单与 mock 数据边界

任何数据图都必须先有数据文件和数据清单（data manifest）。默认路径：

```text
figures/data-manifest.md
figures/data/<figure-name>.csv
figures/<section>/<figure-name>.py
figures/<section>/<figure-name>.png
figures/<section>/<figure-name>.svg
```

`figures/data-manifest.md` 至少记录：

| Figure | Data file | Real/mock | Source | Script | Outputs |
|---|---|---|---|---|---|

mock 或 synthetic 数据只允许用于规划版图表。文件名必须以 `mock_` 或 `synthetic_` 开头，并在图表、表格或章节草稿中保留 `[待真实实验替换]`。不得把 mock 数据写成“实验结果表明”。

### 2.1 分辨率要求

| 用途 | DPI | 说明 |
|------|-----|------|
| 期刊投稿 | 300-600 | 大多数期刊要求 |
| 顶刊投稿 | 450+ | Nature/Science等 |
| 屏幕展示 | 150 | PPT/网页 |

**本技能默认使用 450 DPI**

### 2.2 输出格式

每张图同时输出两种格式：
- **PNG**：位图，适合网页和PPT
- **SVG**：矢量图，适合期刊投稿

### 2.3 图表尺寸

| 类型 | 宽度（英寸） | 适用场景 |
|------|-------------|----------|
| 单栏图 | 3.5 | 期刊单栏 |
| 双栏图 | 7.0 | 期刊双栏/全宽 |
| PPT图 | 10.0 | 演示文稿 |

## 三、顶刊配色方案

### 3.1 Nature/Science 风格

```python
NATURE_COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#95C623']
```

### 3.2 Cell 风格

```python
CELL_COLORS = ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F', '#EDC948']
```

### 3.3 色盲友好配色

```python
COLORBLIND_SAFE = ['#0077BB', '#33BBEE', '#009988', '#EE7733', '#CC3311', '#EE3377']
```

### 3.4 配色原则

- ❌ 禁止使用 matplotlib 默认颜色
- ❌ 禁止使用纯红、纯蓝、纯绿等基础色
- ✅ 同一图中颜色数量控制在 5 种以内
- ✅ 确保色盲友好

## 四、代码模板

```python
"""
Figure X: [图表标题]
论文章节: [所属章节]
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path

# 中文字体配置
CHINESE_FONT = None
font_candidates = [
    '/System/Library/Fonts/STHeiti Light.ttc',
    '/System/Library/Fonts/PingFang.ttc',
]
for fp in font_candidates:
    if Path(fp).exists():
        CHINESE_FONT = fm.FontProperties(fname=fp)
        break

plt.rcParams['axes.unicode_minus'] = False

# 顶刊配色
COLORS = ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F']

def setup_plot_style():
    plt.rcParams.update({
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'legend.frameon': False,
        'savefig.dpi': 450,
        'savefig.bbox': 'tight',
    })

def main():
    setup_plot_style()
    
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # === 绑定代码 ===
    x = np.linspace(0, 10, 100)
    ax.plot(x, np.sin(x), color=COLORS[0], label='Model A')
    ax.plot(x, np.cos(x), color=COLORS[1], label='Model B')
    
    if CHINESE_FONT:
        ax.set_xlabel('时间 (s)', fontproperties=CHINESE_FONT)
        ax.set_ylabel('幅值', fontproperties=CHINESE_FONT)
    else:
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Amplitude')
    
    ax.legend()
    # === 绑定代码结束 ===
    
    # 保存
    output_dir = Path(__file__).parent
    fig_name = Path(__file__).stem
    plt.savefig(output_dir / f'{fig_name}.png', dpi=450)
    plt.savefig(output_dir / f'{fig_name}.svg')
    plt.show()

if __name__ == '__main__':
    main()
```

## 五、常用图表类型

### 折线图
```python
ax.plot(x, y, color=COLORS[0], linewidth=1.5, marker='o', markersize=4)
```

### 柱状图
```python
ax.bar(x_pos, values, color=COLORS[:len(values)], edgecolor='white')
```

### 热力图
```python
im = ax.imshow(matrix, cmap='RdBu_r', aspect='auto')
plt.colorbar(im, ax=ax)
```

### 箱线图
```python
bp = ax.boxplot(data_list, patch_artist=True)
for patch, color in zip(bp['boxes'], COLORS):
    patch.set_facecolor(color)
```

### 散点图
```python
ax.scatter(x, y, c=colors, s=sizes, alpha=0.6, cmap='viridis')
```

## 六、文件管理

### 目录结构

```
figures/
├── chapter1/
│   ├── fig1_overview.py
│   ├── fig1_overview.png
│   └── fig1_overview.svg
├── chapter2/
└── chapter3/
```

### 命名规范

- 文件名格式：`fig{序号}_{描述}.py`
- 示例：`fig1_model_architecture.py`

## 七、质量检查

### 图表内容
- [ ] 数据准确无误
- [ ] 坐标轴标签完整（含单位）
- [ ] 图例清晰可读

### 视觉效果
- [ ] 使用顶刊配色
- [ ] 分辨率达到 450 DPI
- [ ] 字体大小适中

### 文件输出
- [ ] PNG 格式已生成
- [ ] SVG 格式已生成
- [ ] 文件命名规范

## 八、常见问题

### Q1：中文显示为方块

```python
from matplotlib.font_manager import FontProperties
font = FontProperties(fname='/System/Library/Fonts/STHeiti Light.ttc')
ax.set_xlabel('中文标签', fontproperties=font)
```

### Q2：图片模糊

```python
plt.savefig('figure.png', dpi=450, bbox_inches='tight')
```

### Q3：图例遮挡数据

```python
ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
```
