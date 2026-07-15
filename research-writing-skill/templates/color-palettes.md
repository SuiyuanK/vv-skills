# 顶刊级科学图表配色方案

## Nature 风格配色

```python
NATURE_COLORS = {
    'blue': '#2E86AB',
    'magenta': '#A23B72',
    'orange': '#F18F01',
    'brick': '#C73E1D',
    'purple': '#3B1F2B',
    'lime': '#95C623',
}

# 列表形式
NATURE_LIST = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#95C623']
```

## Science 风格配色

```python
SCIENCE_COLORS = {
    'blue': '#4E79A7',
    'orange': '#F28E2B',
    'red': '#E15759',
    'teal': '#76B7B2',
    'green': '#59A14F',
    'yellow': '#EDC948',
    'purple': '#B07AA1',
    'pink': '#FF9DA7',
    'brown': '#9C755F',
    'gray': '#BAB0AC',
}

# 列表形式
SCIENCE_LIST = ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F', '#EDC948']
```

## Cell 风格配色

```python
CELL_COLORS = {
    'dark_blue': '#1F77B4',
    'orange': '#FF7F0E',
    'green': '#2CA02C',
    'red': '#D62728',
    'purple': '#9467BD',
    'brown': '#8C564B',
    'pink': '#E377C2',
    'gray': '#7F7F7F',
}

# 列表形式
CELL_LIST = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B']
```

## 渐变色系

### 蓝色渐变（适合热力图、连续数据）

```python
BLUE_GRADIENT = ['#A8DADC', '#6DAEDB', '#457B9D', '#2C5F7C', '#1D3557']
```

### 红蓝对比（适合正负值对比）

```python
DIVERGING = {
    'cold': ['#2166AC', '#4393C3', '#92C5DE', '#D1E5F0'],
    'neutral': '#F7F7F7',
    'warm': ['#FDDBC7', '#F4A582', '#D6604D', '#B2182B'],
}

# 完整列表（从冷到暖）
DIVERGING_LIST = ['#2166AC', '#4393C3', '#92C5DE', '#D1E5F0', '#F7F7F7', 
                  '#FDDBC7', '#F4A582', '#D6604D', '#B2182B']
```

### 绿色渐变

```python
GREEN_GRADIENT = ['#E5F5E0', '#A1D99B', '#74C476', '#31A354', '#006D2C']
```

### 紫色渐变

```python
PURPLE_GRADIENT = ['#EFEDF5', '#BCBDDC', '#9E9AC8', '#756BB1', '#54278F']
```

## 色盲友好配色

```python
COLORBLIND_SAFE = {
    'blue': '#0077BB',
    'cyan': '#33BBEE',
    'teal': '#009988',
    'orange': '#EE7733',
    'red': '#CC3311',
    'magenta': '#EE3377',
    'gray': '#BBBBBB',
}

# 列表形式
COLORBLIND_LIST = ['#0077BB', '#33BBEE', '#009988', '#EE7733', '#CC3311', '#EE3377']
```

## 使用示例

### 方式1：直接使用列表

```python
import matplotlib.pyplot as plt

colors = ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F']
plt.bar(x, y, color=colors[:len(x)])
```

### 方式2：创建自定义colormap

```python
from matplotlib.colors import LinearSegmentedColormap

# 蓝色渐变colormap
blue_cmap = LinearSegmentedColormap.from_list('blue_grad', 
    ['#A8DADC', '#457B9D', '#1D3557'])
plt.imshow(data, cmap=blue_cmap)

# 红蓝对比colormap
diverging_cmap = LinearSegmentedColormap.from_list('diverging',
    ['#2166AC', '#F7F7F7', '#B2182B'])
plt.imshow(data, cmap=diverging_cmap)
```

### 方式3：循环使用

```python
colors = ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F']
for i, (label, value) in enumerate(data.items()):
    plt.plot(x, value, color=colors[i % len(colors)], label=label)
```

### 方式4：设置为默认配色

```python
import matplotlib.pyplot as plt

colors = ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F', '#EDC948']
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=colors)

# 之后的所有图表自动使用这套配色
plt.plot(x, y1)  # 自动使用第一个颜色
plt.plot(x, y2)  # 自动使用第二个颜色
```

## 配色原则

1. **单图颜色数量控制在5种以内**
2. **主要数据使用饱和度较高的颜色**
3. **次要/背景数据使用灰色或低饱和度颜色**
4. **避免红绿直接对比（色盲不友好）**
5. **连续数据使用渐变色，分类数据使用离散色**
6. **禁止使用matplotlib默认颜色**
7. **禁止使用纯红、纯蓝、纯绿等基础色**

## 快速复制

### Nature风格
```python
colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#95C623']
```

### Science风格
```python
colors = ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F']
```

### 渐变蓝
```python
colors = ['#A8DADC', '#457B9D', '#1D3557']
```

### 色盲友好
```python
colors = ['#0077BB', '#33BBEE', '#009988', '#EE7733', '#CC3311']
```

---

## 流程图/结构图配色建议

用于生成流程图提示词时的配色参考：

| 元素类型 | 推荐颜色 | 色值 |
|----------|----------|------|
| 输入/输出 | 蓝色 | #4E79A7 |
| 核心处理 | 橙色 | #F28E2B |
| 数据存储 | 绿色 | #59A14F |
| 决策判断 | 黄色 | #EDC948 |
| 错误/警告 | 红色 | #E15759 |
| 辅助说明 | 灰色 | #6C757D |
| 创新标注 | 红色虚线 | #CC3311 |

### 流程图配色示例

```
绘制流程图时使用以下配色：
- 蓝色(#4E79A7)：数据输入/输出步骤
- 橙色(#F28E2B)：核心算法步骤（加粗边框）
- 绿色(#59A14F)：结果/完成步骤
- 灰色(#6C757D)：辅助说明文字
- 红色虚线(#CC3311)：创新点标注
```
