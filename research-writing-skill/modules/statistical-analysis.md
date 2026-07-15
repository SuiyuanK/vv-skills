# 统计分析指南

本模块提供学术论文中统计分析的选择、执行和报告指南。

---

## 一、统计检验选择

### 快速参考：选择正确的检验

#### 比较两组
| 数据特征 | 推荐检验 |
|----------|----------|
| 独立、连续、正态 | 独立样本t检验 |
| 独立、连续、非正态 | Mann-Whitney U检验 |
| 配对、连续、正态 | 配对样本t检验 |
| 配对、连续、非正态 | Wilcoxon符号秩检验 |
| 二分类结果 | 卡方检验或Fisher精确检验 |

#### 比较三组及以上
| 数据特征 | 推荐检验 |
|----------|----------|
| 独立、连续、正态 | 单因素方差分析 |
| 独立、连续、非正态 | Kruskal-Wallis检验 |
| 配对、连续、正态 | 重复测量方差分析 |
| 配对、连续、非正态 | Friedman检验 |

#### 关系分析
| 分析目标 | 推荐方法 |
|----------|----------|
| 两个连续变量关系 | Pearson相关（正态）或Spearman相关（非正态） |
| 连续结果与预测变量 | 线性回归 |
| 二分类结果与预测变量 | 逻辑回归 |

---

## 二、假设检验

### 系统性假设验证

**在解释检验结果之前，必须检查假设。**

### 正态性检验

```python
from scipy import stats
import numpy as np

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
    print("方差不齐，使用Welch's t检验或Welch's ANOVA")
```

### 假设违反时的处理

**正态性违反**：
- 轻微违反 + n > 30 → 继续使用参数检验（稳健）
- 中度违反 → 使用非参数替代
- 严重违反 → 数据转换或使用非参数检验

**方差齐性违反**：
- t检验 → 使用Welch's t检验
- ANOVA → 使用Welch's ANOVA或Brown-Forsythe ANOVA
- 回归 → 使用稳健标准误或加权最小二乘

---

## 三、效应量

### 为什么需要效应量

**效应量量化效应的大小，而p值只表明效应是否存在。**

### 常用效应量参考

| 检验 | 效应量 | 小 | 中 | 大 |
|------|--------|-----|-----|-----|
| t检验 | Cohen's d | 0.20 | 0.50 | 0.80 |
| ANOVA | η²_p | 0.01 | 0.06 | 0.14 |
| 相关 | r | 0.10 | 0.30 | 0.50 |
| 回归 | R² | 0.02 | 0.13 | 0.26 |
| 卡方 | Cramér's V | 0.07 | 0.21 | 0.35 |

**重要**：这些基准是指导性的，具体情境很重要！

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

# 相关：r本身就是效应量
corr = pg.corr(x, y)
r = corr['r'].values[0]
print(f"r = {r:.2f}")
```

---

## 四、功效分析

### 事前功效分析（研究规划）

在数据收集前确定所需样本量：

```python
from statsmodels.stats.power import tt_ind_solve_power, FTestAnovaPower

# t检验：检测d=0.5需要多少样本？
n_required = tt_ind_solve_power(
    effect_size=0.5,
    alpha=0.05,
    power=0.80,
    ratio=1.0,
    alternative='two-sided'
)
print(f"每组所需样本量: {n_required:.0f}")

# ANOVA：检测f=0.25需要多少样本？
anova_power = FTestAnovaPower()
n_per_group = anova_power.solve_power(
    effect_size=0.25,
    ngroups=3,
    alpha=0.05,
    power=0.80
)
print(f"每组所需样本量: {n_per_group:.0f}")
```

### 敏感性分析（研究后）

确定能检测到的效应量：

```python
# 每组n=50，能检测到什么效应？
detectable_d = tt_ind_solve_power(
    effect_size=None,
    nobs1=50,
    alpha=0.05,
    power=0.80,
    ratio=1.0,
    alternative='two-sided'
)
print(f"研究能检测到 d ≥ {detectable_d:.2f}")
```

**注意**：事后功效分析（研究后计算功效）通常不推荐。使用敏感性分析代替。

---

## 五、APA格式报告

### 必要报告元素

1. **描述统计**：所有组/变量的M、SD、n
2. **检验统计量**：检验名称、统计量、df、精确p值
3. **效应量**：带置信区间
4. **假设检验**：进行了哪些检验、结果、采取的措施
5. **所有计划分析**：包括非显著发现

### 报告模板

#### 独立样本t检验

```
A组（n = 48, M = 75.2, SD = 8.5）得分显著高于B组
（n = 52, M = 68.3, SD = 9.2），t(98) = 3.82, p < .001, 
d = 0.77, 95% CI [0.36, 1.18]，双尾检验。正态性假设
（Shapiro-Wilk: A组 W = 0.97, p = .18; B组 W = 0.96, 
p = .12）和方差齐性假设（Levene's F(1, 98) = 1.23, 
p = .27）均满足。
```

#### 单因素方差分析

```
单因素方差分析显示处理条件对测试分数有显著主效应，
F(2, 147) = 8.45, p < .001, η²_p = .10。事后比较使用
Tukey HSD表明，条件A（M = 78.2, SD = 7.3）得分显著
高于条件B（M = 71.5, SD = 8.1, p = .002, d = 0.87）
和条件C（M = 70.1, SD = 7.9, p < .001, d = 1.07）。
条件B和C无显著差异（p = .52, d = 0.18）。
```

#### 多元回归

```
进行多元线性回归以预测考试成绩，预测变量为学习时间、
先前GPA和出勤率。整体模型显著，F(3, 146) = 45.2, 
p < .001, R² = .48, 调整后R² = .47。学习时间
（B = 1.80, SE = 0.31, β = .35, t = 5.78, p < .001, 
95% CI [1.18, 2.42]）和先前GPA（B = 8.52, SE = 1.95, 
β = .28, t = 4.37, p < .001, 95% CI [4.66, 12.38]）
是显著预测变量，而出勤率不显著（B = 0.15, SE = 0.12, 
β = .08, t = 1.25, p = .21, 95% CI [-0.09, 0.39]）。
多重共线性不是问题（所有VIF < 1.5）。
```

---

## 六、常见统计陷阱

### 必须避免的错误

1. **P-hacking**：不要测试多种方式直到出现显著性
2. **HARKing**：不要将探索性发现呈现为验证性
3. **忽视假设**：检查并报告违反情况
4. **混淆显著性与重要性**：p < .05 ≠ 有意义的效应
5. **不报告效应量**：对解释至关重要
6. **挑选结果**：报告所有计划的分析
7. **误解p值**：它们不是假设为真的概率
8. **多重比较**：适当时校正族错误率
9. **忽视缺失数据**：理解机制（MCAR、MAR、MNAR）
10. **过度解释非显著结果**：无证据 ≠ 无效应的证据

---

## 七、Python统计分析示例

### 完整t检验流程

```python
import numpy as np
import pandas as pd
import pingouin as pg
from scipy import stats

# 数据
group_a = np.array([75, 82, 68, 79, 85, 72, 88, 76])
group_b = np.array([65, 70, 62, 68, 75, 60, 72, 66])

# 1. 描述统计
print("描述统计:")
print(f"A组: M={group_a.mean():.2f}, SD={group_a.std():.2f}, n={len(group_a)}")
print(f"B组: M={group_b.mean():.2f}, SD={group_b.std():.2f}, n={len(group_b)}")

# 2. 假设检验
# 正态性
_, p_a = stats.shapiro(group_a)
_, p_b = stats.shapiro(group_b)
print(f"\n正态性检验: A组 p={p_a:.3f}, B组 p={p_b:.3f}")

# 方差齐性
_, p_levene = stats.levene(group_a, group_b)
print(f"Levene检验: p={p_levene:.3f}")

# 3. t检验
result = pg.ttest(group_a, group_b, correction='auto')
print(f"\nt检验结果:")
print(f"t({result['dof'].values[0]:.0f}) = {result['T'].values[0]:.2f}")
print(f"p = {result['p-val'].values[0]:.4f}")
print(f"Cohen's d = {result['cohen-d'].values[0]:.2f}")
```

### 完整ANOVA流程

```python
import pingouin as pg
import pandas as pd

# 创建数据
df = pd.DataFrame({
    'score': [85, 82, 88, 79, 75, 72, 78, 70, 65, 68, 62, 60],
    'group': ['A']*4 + ['B']*4 + ['C']*4
})

# 1. 描述统计
print(df.groupby('group')['score'].agg(['mean', 'std', 'count']))

# 2. 方差分析
aov = pg.anova(dv='score', between='group', data=df, detailed=True)
print("\nANOVA结果:")
print(aov)

# 3. 事后检验（如果显著）
if aov['p-unc'].values[0] < 0.05:
    posthoc = pg.pairwise_tukey(dv='score', between='group', data=df)
    print("\n事后比较 (Tukey HSD):")
    print(posthoc)
```

### 相关与回归

```python
import numpy as np
import pandas as pd
import pingouin as pg
import statsmodels.api as sm

# 数据
np.random.seed(42)
x = np.random.randn(100)
y = 2*x + np.random.randn(100)*0.5

# 相关分析
corr = pg.corr(x, y)
print("相关分析:")
print(f"r = {corr['r'].values[0]:.3f}")
print(f"p = {corr['p-val'].values[0]:.4f}")
print(f"95% CI = [{corr['CI95%'].values[0][0]:.3f}, {corr['CI95%'].values[0][1]:.3f}]")

# 线性回归
X = sm.add_constant(x)
model = sm.OLS(y, X).fit()
print("\n回归分析:")
print(model.summary())
```

---

## 八、统计分析检查清单

开始统计分析时：

- [ ] 定义研究问题和假设
- [ ] 确定适当的统计检验
- [ ] 进行功效分析确定样本量
- [ ] 加载并检查数据
- [ ] 检查缺失数据和异常值
- [ ] 验证假设
- [ ] 运行主要分析
- [ ] 计算效应量和置信区间
- [ ] 进行事后检验（如需要，带校正）
- [ ] 创建可视化
- [ ] 按APA格式撰写结果
- [ ] 进行敏感性分析
- [ ] 共享数据和代码

---

## 九、推荐资源

### Python库

- **scipy.stats**：核心统计检验
- **statsmodels**：高级回归和诊断
- **pingouin**：用户友好的统计检验，带效应量
- **numpy/pandas**：数据处理

### 参考教材

- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences*
- Field, A. (2013). *Discovering Statistics Using IBM SPSS Statistics*
- Gelman, A., & Hill, J. (2006). *Data Analysis Using Regression*

### 在线资源

- APA Style Guide: https://apastyle.apa.org/
- Cross Validated: stats.stackexchange.com
