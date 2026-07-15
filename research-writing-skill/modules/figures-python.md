# Python数据图表模块

本模块指导使用Python生成科研论文级别的数据图表。

---

## 一、环境要求

### 1.1 conda环境

**默认环境名**：`research`

**激活命令**：
```bash
conda activate research
```

**必需库**：
```bash
pip install matplotlib seaborn numpy pandas scikit-learn
```

**可选库**：
```bash
pip install plotly scipy statsmodels
```

### 1.2 环境配置

详见 `modules/environment-setup.md` 获取完整的环境配置指南。

---

## 二、图表规范

### 2.1 分辨率要求

| 用途 | DPI | 说明 |
|------|-----|------|
| 期刊投稿 | 300-600 | 大多数期刊要求 |
| 顶刊投稿 | 450+ | Nature/Science等 |
| 屏幕展示 | 150 | PPT/网页 |
| 打印海报 | 300 | A0/A1海报 |

**本模块默认使用 450 DPI**

### 2.2 输出格式

每张图同时输出两种格式：
- **PNG**：位图，适合网页和PPT
- **SVG**：矢量图，适合期刊投稿和后期编辑

### 2.3 图表尺寸

| 类型 | 宽度（英寸） | 适用场景 |
|------|-------------|----------|
| 单栏图 | 3.5 | 期刊单栏 |
| 双栏图 | 7.0 | 期刊双栏/全宽 |
| PPT图 | 10.0 | 演示文稿 |

---

## 三、顶刊配色方案

### 3.1 Nature/Science 风格

```python
NATURE_COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#95C623']
```

| 颜色 | 色值 | 用途 |
|------|------|------|
| 深蓝 | #2E86AB | 主色调 |
| 玫红 | #A23B72 | 对比色 |
| 橙色 | #F18F01 | 强调色 |
| 砖红 | #C73E1D | 警示色 |
| 黄绿 | #95C623 | 辅助色 |

### 3.2 Cell 风格

```python
CELL_COLORS = ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F', '#EDC948']
```

### 3.3 渐变色系

```python
# 蓝色渐变（适合热力图）
BLUE_GRADIENT = ['#A8DADC', '#6DAEDB', '#457B9D', '#2C5F7C', '#1D3557']

# 红蓝对比（适合正负值）
DIVERGING_COLORS = {
    'cold': ['#2166AC', '#4393C3', '#92C5DE', '#D1E5F0'],
    'neutral': '#F7F7F7',
    'warm': ['#FDDBC7', '#F4A582', '#D6604D', '#B2182B'],
}
```

### 3.4 色盲友好配色

```python
COLORBLIND_SAFE = ['#0077BB', '#33BBEE', '#009988', '#EE7733', '#CC3311', '#EE3377']
```

### 3.5 配色原则

- ❌ 禁止使用matplotlib默认颜色
- ❌ 禁止使用纯红、纯蓝、纯绿等基础色
- ✅ 同一图中颜色数量控制在5种以内
- ✅ 确保色盲友好（避免红绿直接对比）
- ✅ 使用渐变色表示连续变量

---

## 四、代码模板

### 4.1 基础模板

```python
"""
Figure X: [图表标题]
论文章节: [所属章节]
描述: [图表内容描述]
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path

# ============================================================
# 中文字体配置（macOS系统）
# ============================================================
CHINESE_FONT = None
font_candidates = [
    '/System/Library/Fonts/STHeiti Light.ttc',
    '/System/Library/Fonts/Supplemental/Songti.ttc',
    '/Library/Fonts/Songti.ttc',
    '/System/Library/Fonts/PingFang.ttc',
]
for fp in font_candidates:
    if Path(fp).exists():
        CHINESE_FONT = fm.FontProperties(fname=fp)
        break

if CHINESE_FONT is None:
    plt.rcParams['font.sans-serif'] = ['Heiti TC', 'STHeiti', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 顶刊配色
# ============================================================
COLORS = ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F', '#EDC948']

# ============================================================
# 全局样式设置
# ============================================================
def setup_plot_style():
    """配置全局绑定样式"""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'lines.linewidth': 1.5,
        'lines.markersize': 6,
        'axes.linewidth': 1.0,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.linewidth': 0.5,
        'legend.frameon': False,
        'savefig.dpi': 450,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
    })

# ============================================================
# 主绑定代码
# ============================================================
def main():
    setup_plot_style()
    
    # === 在此处编写具体绑定代码 ===
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # 示例数据
    x = np.linspace(0, 10, 100)
    ax.plot(x, np.sin(x), color=COLORS[0], label='Model A')
    ax.plot(x, np.cos(x), color=COLORS[1], label='Model B')
    
    # 标签设置（中文使用FontProperties）
    if CHINESE_FONT:
        ax.set_xlabel('时间 (s)', fontproperties=CHINESE_FONT)
        ax.set_ylabel('幅值', fontproperties=CHINESE_FONT)
        ax.set_title('模型对比', fontproperties=CHINESE_FONT)
        ax.legend(prop=CHINESE_FONT)
    else:
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Amplitude')
        ax.set_title('Model Comparison')
        ax.legend()
    
    # === 绑定代码结束 ===
    
    # 保存图片
    output_dir = Path(__file__).parent
    fig_name = Path(__file__).stem
    
    plt.savefig(output_dir / f'{fig_name}.png', dpi=450, format='png')
    plt.savefig(output_dir / f'{fig_name}.svg', format='svg')
    
    plt.show()
    print(f"图片已保存至: {output_dir}")

if __name__ == '__main__':
    main()
```

### 4.2 常用图表类型

#### 折线图
```python
fig, ax = plt.subplots(figsize=(7, 5))
for i, (label, data) in enumerate(datasets.items()):
    ax.plot(x, data, color=COLORS[i], label=label, linewidth=1.5, marker='o', markersize=4)
ax.set_xlabel('Epoch')
ax.set_ylabel('Accuracy (%)')
ax.legend()
```

#### 柱状图
```python
fig, ax = plt.subplots(figsize=(7, 5))
x_pos = np.arange(len(categories))
bars = ax.bar(x_pos, values, color=COLORS[:len(categories)], edgecolor='white', linewidth=0.5)
ax.set_xticks(x_pos)
ax.set_xticklabels(categories)
ax.set_ylabel('Performance')
```

#### 分组柱状图
```python
fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(categories))
width = 0.25

for i, (label, values) in enumerate(groups.items()):
    ax.bar(x + i * width, values, width, label=label, color=COLORS[i])

ax.set_xticks(x + width)
ax.set_xticklabels(categories)
ax.legend()
```

#### 热力图
```python
fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(matrix, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
plt.colorbar(im, ax=ax, label='Correlation')
ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, rotation=45, ha='right')
ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels)
```

#### 箱线图
```python
fig, ax = plt.subplots(figsize=(7, 5))
bp = ax.boxplot(data_list, labels=labels, patch_artist=True)
for patch, color in zip(bp['boxes'], COLORS):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
```

#### 散点图
```python
fig, ax = plt.subplots(figsize=(7, 5))
scatter = ax.scatter(x, y, c=colors, s=sizes, alpha=0.6, cmap='viridis')
plt.colorbar(scatter, ax=ax, label='Value')
ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
```

---

## 五、文件管理

### 5.1 目录结构

```
项目目录/
├── figures/
│   ├── chapter1_introduction/
│   │   ├── fig1_overview.py
│   │   ├── fig1_overview.png
│   │   └── fig1_overview.svg
│   ├── chapter2_method/
│   │   └── ...
│   ├── chapter3_results/
│   │   └── ...
│   └── chapter4_discussion/
│       └── ...
```

### 5.2 命名规范

- 文件名格式：`fig{序号}_{描述}.py`
- 示例：`fig1_model_architecture.py`, `fig5_accuracy_comparison.py`
- 输出图片与代码同名，仅扩展名不同

---

## 六、执行流程

### 6.1 标准流程

1. **确认conda环境已激活**
   ```bash
   conda activate research
   ```

2. **创建/编辑Python脚本**
   - 使用上述模板
   - 修改数据和绑定代码

3. **运行脚本**
   ```bash
   python figures/chapter1/fig1_xxx.py
   ```

4. **检查输出**
   - 确认PNG和SVG都已生成
   - 检查图表质量

5. **如有错误，修复后重新运行**

### 6.2 缺失库处理

```bash
# 使用pip安装
pip install [package_name]

# 或使用conda安装
conda install [package_name]
```

---

## 七、质量检查清单

### 图表内容
- [ ] 数据准确无误
- [ ] 坐标轴标签完整（含单位）
- [ ] 图例清晰可读
- [ ] 标题简洁明了

### 视觉效果
- [ ] 使用顶刊配色方案
- [ ] 分辨率达到450 DPI
- [ ] 字体大小适中（可读）
- [ ] 无多余的网格线或边框

### 文件输出
- [ ] PNG格式已生成
- [ ] SVG格式已生成
- [ ] 文件命名规范
- [ ] 存放在正确目录

---

## 八、常见问题

### Q1：中文显示为方块

**解决方案**：
```python
# 方法1：指定字体文件
from matplotlib.font_manager import FontProperties
font = FontProperties(fname='/System/Library/Fonts/STHeiti Light.ttc')
ax.set_xlabel('中文标签', fontproperties=font)

# 方法2：全局设置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Heiti TC', 'STHeiti']
plt.rcParams['axes.unicode_minus'] = False
```

### Q2：图片模糊

**解决方案**：
```python
plt.savefig('figure.png', dpi=450, bbox_inches='tight')
```

### Q3：颜色不够用

**解决方案**：
```python
# 使用colormap生成更多颜色
import matplotlib.cm as cm
colors = cm.viridis(np.linspace(0, 1, n_colors))
```

### Q4：图例遮挡数据

**解决方案**：
```python
ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
plt.tight_layout()
```
