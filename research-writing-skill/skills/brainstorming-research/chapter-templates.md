# 章节结构模板

本文件提供各种论文类型的默认章节结构模板。

## 中文毕业论文（本科/硕士/博士）

```
chapters/
├── 00-abstract.md        # 摘要（中英文）
├── 01-introduction.md    # 绪论（研究背景、意义、目的、内容）
├── 02-literature.md      # 文献综述
├── 03-methods.md         # 研究方法
├── 04-results.md         # 结果分析
├── 05-discussion.md      # 讨论
├── 06-conclusion.md      # 结论（总结、创新点、展望）
└── 07-references.md      # 参考文献
```

### 各章内容说明

| 章节 | 内容要点 | 建议字数（硕士） |
|------|----------|------------------|
| 摘要 | 背景、目的、方法、结果、结论 | 500-800字 |
| 绪论 | 研究背景、问题、目的、意义、内容、结构 | 3000-5000字 |
| 文献综述 | 国内外研究现状、理论基础、研究空白 | 5000-8000字 |
| 研究方法 | 研究设计、数据来源、分析方法 | 3000-5000字 |
| 结果分析 | 数据呈现、结果描述、初步分析 | 5000-10000字 |
| 讨论 | 结果解释、与文献对比、局限性 | 3000-5000字 |
| 结论 | 主要结论、创新点、未来方向 | 1500-2500字 |

## SCI 论文（IMRaD 结构）

```
chapters/
├── 00-abstract.md        # Abstract
├── 01-introduction.md    # Introduction
├── 02-methods.md         # Methods/Materials
├── 03-results.md         # Results
├── 04-discussion.md      # Discussion
└── 05-conclusion.md      # Conclusion（部分期刊合并到Discussion）
```

### 各章内容说明

| Section | Content | Typical Length |
|---------|---------|----------------|
| Abstract | Background, Objective, Methods, Results, Conclusions | 150-300 words |
| Introduction | Context, Gap, Purpose | 500-800 words |
| Methods | Study design, Data, Analysis | 800-1500 words |
| Results | Findings, Tables, Figures | 1000-2000 words |
| Discussion | Interpretation, Comparison, Limitations | 1000-1500 words |
| Conclusion | Summary, Implications | 200-400 words |

## 中文核心期刊

```
chapters/
├── 00-abstract.md        # 摘要
├── 01-introduction.md    # 引言
├── 02-main-body.md       # 正文（可根据需要拆分）
├── 03-conclusion.md      # 结论
└── 04-references.md      # 参考文献
```

### 正文拆分建议

根据具体内容，正文可以拆分为：
- 02a-theoretical-framework.md（理论框架）
- 02b-research-design.md（研究设计）
- 02c-analysis.md（分析与讨论）

## 会议论文

```
chapters/
├── 00-abstract.md        # Abstract
├── 01-introduction.md    # Introduction
├── 02-related-work.md    # Related Work
├── 03-methodology.md     # Methodology/Approach
├── 04-experiments.md     # Experiments
├── 05-conclusion.md      # Conclusion
└── 06-references.md      # References
```

## 课程论文/报告

```
chapters/
├── 00-abstract.md        # 摘要（可选）
├── 01-introduction.md    # 引言
├── 02-main-body.md       # 正文
├── 03-conclusion.md      # 结论
└── 04-references.md      # 参考文献
```

## 文件命名规范

- 使用英文命名，避免中文导致路径问题
- 使用两位数字前缀确保排序正确
- 使用连字符分隔单词
- 扩展名统一为 `.md`（Markdown）或 `.tex`（LaTeX）

## 章节调整说明

用户可以：
1. 增加章节：例如添加"案例分析"章节
2. 删除章节：例如合并"讨论"和"结论"
3. 调整顺序：根据研究需要调整
4. 修改名称：使用更符合研究内容的章节名
5. 拆分章节：将一个章节拆分为多个子章节

调整后的章节结构需要记录到 `plan/outline.md`。
