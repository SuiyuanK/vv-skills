---
name: statistical-analysis
description: Use when planning or reporting statistical analysis - provides test selection, execution code, and APA format guidelines
---

# 统计分析指南

本技能提供学术论文中统计分析的选择、执行和报告指南。

## 一、统计检验选择

### 比较两组

| 数据特征 | 推荐检验 |
|----------|----------|
| 独立、连续、正态 | 独立样本t检验 |
| 独立、连续、非正态 | Mann-Whitney U检验 |
| 配对、连续、正态 | 配对样本t检验 |
| 配对、连续、非正态 | Wilcoxon符号秩检验 |
| 二分类结果 | 卡方检验或Fisher精确检验 |

### 比较三组及以上

| 数据特征 | 推荐检验 |
|----------|----------|
| 独立、连续、正态 | 单因素方差分析 |
| 独立、连续、非正态 | Kruskal-Wallis检验 |
| 配对、连续、正态 | 重复测量方差分析 |
| 配对、连续、非正态 | Friedman检验 |

### 关系分析

| 分析目标 | 推荐方法 |
|----------|----------|
| 两个连续变量关系 | Pearson相关（正态）或Spearman相关（非正态） |
| 连续结果与预测变量 | 线性回归 |
| 二分类结果与预测变量 | 逻辑回归 |

## 二、假设检验

### 正态性检验

```python
from scipy import stats

# Shapiro-Wilk检验（样本量<5000）
stat, p_value = stats.shapiro(data)
print(f"Shapiro-Wilk检验: W={stat:.4f}, p={p_value:.4f}")

if p_value > 0.05:
    print("数据符合正态分布假设")
else:
    print("数据不符合正态分布，考虑使用非参数检验")
```

### 方差齐性检验

```python
from scipy import stats

# Levene检验
stat, p_value = stats.levene(group1, group2)
print(f"Levene检验: F={stat:.4f}, p={p_value:.4f}")

if p_value > 0.05:
    print("方差齐性假设满足")
else:
    print("方差不齐，使用Welch's t检验")
```

## 三、效应量

### 常用效应量参考

| 检验 | 效应量 | 小 | 中 | 大 |
|------|--------|-----|-----|-----|
| t检验 | Cohen's d | 0.20 | 0.50 | 0.80 |
| ANOVA | η²_p | 0.01 | 0.06 | 0.14 |
| 相关 | r | 0.10 | 0.30 | 0.50 |
| 回归 | R² | 0.02 | 0.13 | 0.26 |

### Python计算效应量

```python
import pingouin as pg

# t检验返回Cohen's d
result = pg.ttest(group1, group2)
d = result['cohen-d'].values[0]
print(f"Cohen's d = {d:.2f}")

# ANOVA返回偏η²
aov = pg.anova(dv='score', between='group', data=df)
eta_p2 = aov['np2'].values[0]
print(f"Partial η² = {eta_p2:.3f}")
```

## 四、APA格式报告

### 独立样本t检验

```
A组（n = 48, M = 75.2, SD = 8.5）得分显著高于B组
（n = 52, M = 68.3, SD = 9.2），t(98) = 3.82, p < .001, 
d = 0.77, 95% CI [0.36, 1.18]。
```

### 单因素方差分析

```
单因素方差分析显示处理条件对测试分数有显著主效应，
F(2, 147) = 8.45, p < .001, η²_p = .10。事后比较使用
Tukey HSD表明，条件A（M = 78.2, SD = 7.3）得分显著
高于条件B（M = 71.5, SD = 8.1, p = .002）。
```

### 多元回归

```
多元线性回归预测考试成绩，整体模型显著，
F(3, 146) = 45.2, p < .001, R² = .48。学习时间
（β = .35, p < .001）和先前GPA（β = .28, p < .001）
是显著预测变量。
```

## 五、常见统计陷阱

<HARD-GATE>
必须避免以下错误：
</HARD-GATE>

1. **P-hacking**：不要测试多种方式直到出现显著性
2. **HARKing**：不要将探索性发现呈现为验证性
3. **忽视假设**：检查并报告违反情况
4. **混淆显著性与重要性**：p < .05 ≠ 有意义的效应
5. **不报告效应量**：对解释至关重要
6. **挑选结果**：报告所有计划的分析
7. **多重比较**：适当时校正族错误率
8. **过度解释非显著结果**：无证据 ≠ 无效应的证据

## 六、Python示例

### 完整t检验流程

```python
import numpy as np
import pingouin as pg
from scipy import stats

# 数据
group_a = np.array([75, 82, 68, 79, 85, 72, 88, 76])
group_b = np.array([65, 70, 62, 68, 75, 60, 72, 66])

# 1. 描述统计
print(f"A组: M={group_a.mean():.2f}, SD={group_a.std():.2f}")
print(f"B组: M={group_b.mean():.2f}, SD={group_b.std():.2f}")

# 2. 正态性检验
_, p_a = stats.shapiro(group_a)
_, p_b = stats.shapiro(group_b)
print(f"正态性: A组 p={p_a:.3f}, B组 p={p_b:.3f}")

# 3. t检验
result = pg.ttest(group_a, group_b)
print(f"t = {result['T'].values[0]:.2f}")
print(f"p = {result['p-val'].values[0]:.4f}")
print(f"Cohen's d = {result['cohen-d'].values[0]:.2f}")
```

## 七、统计分析检查清单

- [ ] 定义研究问题和假设
- [ ] 确定适当的统计检验
- [ ] 进行功效分析确定样本量
- [ ] 检查缺失数据和异常值
- [ ] 验证假设（正态性、方差齐性）
- [ ] 运行主要分析
- [ ] 计算效应量和置信区间
- [ ] 进行事后检验（如需要）
- [ ] 按APA格式撰写结果

## 八、推荐资源

### Python库
- **scipy.stats**：核心统计检验
- **statsmodels**：高级回归和诊断
- **pingouin**：用户友好的统计检验，带效应量
