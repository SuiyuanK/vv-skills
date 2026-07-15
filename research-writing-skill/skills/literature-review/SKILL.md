---
name: literature-review
description: Use when writing literature review sections - guides searching, organizing, and synthesizing academic sources
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch
---

# 文献综述

本技能指导文献搜索、整理和综述写作。

<EXTREMELY-IMPORTANT>
## 核心原则：绝不编造文献

这是最重要的原则，必须严格遵守：

1. **英文文献**：可通过网络搜索获取，但必须验证真实性
2. **中文文献**：明确告知用户去知网（CNKI）搜索，AI提供搜索建议
3. **所有引用必须可追溯、可验证**
4. **不确定的文献信息，宁可不写也不编造**
</EXTREMELY-IMPORTANT>

<MCP-INTEGRATION>
## 文献工具脚本

本技能内置了多个文献处理脚本：

### 1. 文献搜索 (scholar_search.py)

**脚本位置**：`scripts/scholar_search.py`

**支持的数据库**：PubMed, CrossRef, Semantic Scholar, arXiv

**支持的输出格式**：
- `json` - JSON 格式（默认）
- `bibtex` - BibTeX 格式，可直接用于 LaTeX
- `ris` - RIS 格式，用于 EndNote/Zotero
- `apa` - APA 引用格式
- `mla` - MLA 引用格式
- `chicago` - Chicago 引用格式
- `vancouver` - Vancouver 引用格式

### 使用方法

```bash
# 基本搜索
python scripts/scholar_search.py "deep learning transformer"

# 指定数据库
python scripts/scholar_search.py "neural network" --sources pubmed,crossref

# 年份过滤（当前是2026年，建议使用近年范围）
python scripts/scholar_search.py "machine learning" --year 2023-2026

# 输出 BibTeX 格式（用于 LaTeX 论文）
python scripts/scholar_search.py "landslide detection" --format bibtex -o refs.bib

# 输出 APA 引用格式
python scripts/scholar_search.py "attention mechanism" --format apa --limit 5

# JSON 输出（用于程序处理）
python scripts/scholar_search.py "quantum computing" --format json -o results.json
```

### 输出格式示例

**BibTeX 格式**（用于 LaTeX）：
```bibtex
@article{xu2024,
  title = {CAS Landslide Dataset: A Large-Scale and Multisensor Dataset},
  author = {Yulin Xu and Chaojun Ouyang and Qingsong Xu},
  journal = {Scientific Data},
  year = {2024},
  doi = {10.1038/s41597-023-02847-z},
}
```

**APA 格式**（用于正文引用）：
```
Yulin Xu and Chaojun Ouyang (2024). CAS Landslide Dataset...
```

### 各数据库特点

| 数据库 | 速率限制 | 摘要 | 引用数 | 适用领域 |
|--------|----------|------|--------|----------|
| CrossRef | 高 | 部分 | 是 | 全学科 |
| PubMed | 中 | 需额外请求 | 否 | 生物医学 |
| Semantic Scholar | 低* | 是 | 是 | 全学科 |
| arXiv | 低 | 是 | 否 | CS/物理/数学 |

\* Semantic Scholar 建议配置 API Key 以获得更高限额。
</MCP-INTEGRATION>

## Checklist

- [ ] 确认综述主题和范围
- [ ] 生成搜索关键词（中英文）
- [ ] 英文文献：执行搜索并整理结果
- [ ] 中文文献：提供搜索策略，等待用户提供
- [ ] 按主题分类整理文献
- [ ] 生成证据-论点映射（evidence-claim map）
- [ ] 标注每条文献的引用位置（citation slot）
- [ ] 撰写综述初稿
- [ ] 检查所有引用的真实性
- [ ] 更新 plan/progress.md

## 0. 文献到正文的硬门控

文献检索不是交付终点。写 Introduction、Related Work、研究现状前，必须把文献转成证据-论点映射：

```markdown
| Source ID | Citation | Abstract-level finding | Usable fact | Supported claim | 引用位置 / citation slot | Risk |
|---|---|---|---|---|---|---|
```

要求：

1. `Supported claim` 必须是可写进正文的一句话，不是“这篇文献很相关”。
2. `引用位置 / citation slot` 必须具体到段落角色，如“Introduction-P2 方法谱系”或“RelatedWork-P3 FL-IDS 局限”。
3. 每个核心论点至少有 1 条强支撑文献；关键研究空白应由 2 条以上文献共同支撑。
4. 只允许使用题名、摘要、DOI 元数据、用户提供摘录或已读取全文中的信息。

如果没有 evidence-claim map，不得声称文献综述已完成。

## 一、文献搜索指南

### 1.0 脚本搜索（推荐）

**使用 `scripts/scholar_search.py` 进行多数据库并行搜索。**

#### 基本用法

```bash
# 搜索所有数据库，输出 JSON
python scripts/scholar_search.py "your query" --format json -o results.json

# 指定数据库和年份
python scripts/scholar_search.py "deep learning" --sources crossref,semanticscholar --year 2023-2026

# 仅搜索 PubMed（生物医学）
python scripts/scholar_search.py "hippocampus memory" --sources pubmed --limit 20
```

#### BibTeX 输出（用于 LaTeX 论文）

```bash
# 输出 BibTeX 格式
python scripts/scholar_search.py "landslide detection" --format bibtex -o refs.bib

# 直接输出到控制台
python scripts/scholar_search.py "transformer attention" --format bibtex --limit 5
```

**BibTeX 输出示例**：
```bibtex
@article{xu2024,
  title = {CAS Landslide Dataset: A Large-Scale and Multisensor Dataset},
  author = {Yulin Xu and Chaojun Ouyang and Qingsong Xu},
  journal = {Scientific Data},
  year = {2024},
  doi = {10.1038/s41597-023-02847-z},
  url = {https://doi.org/10.1038/s41597-023-02847-z}
}
```

#### 文本引用格式

```bash
# APA 格式
python scripts/scholar_search.py "neural network" --format apa --limit 3

# MLA 格式
python scripts/scholar_search.py "machine learning" --format mla --limit 3

# Chicago 格式
python scripts/scholar_search.py "attention mechanism" --format chicago --limit 3
```

**APA 输出示例**：
```
Yulin Xu and Chaojun Ouyang (2024). CAS Landslide Dataset: A Large-Scale
and Multisensor Dataset for Deep Learning-Based Landslide Detection.
Scientific Data. 10.1038/s41597-023-02847-z
```

#### 搜索策略建议

1. **开始搜索**：使用 CrossRef（速度快、结果多、有引用数）
2. **精确搜索**：添加年份范围过滤
3. **领域搜索**：
   - 生物医学 → PubMed
   - 计算机/物理/数学 → arXiv
   - 需要 AI 推荐相关文献 → Semantic Scholar

#### JSON 输出示例

```json
[
  {
    "title": "Attention Is All You Need",
    "authors": ["Ashish Vaswani", "Noam Shazeer", "..."],
    "year": 2017,
    "journal": "Advances in neural information processing systems",
    "doi": "10.48550/arXiv.1706.03762",
    "citations": 100000,
    "url": "https://doi.org/10.48550/arXiv.1706.03762",
    "_source": "crossref"
  }
]
```

### 1.1 WebSearch 搜索（备选）

**当脚本不可用时，使用 WebSearch 进行搜索。**

**可用数据库：**

| 数据库 | 特点 | 适用领域 |
|--------|------|----------|
| Google Scholar | 综合性最强 | 全学科 |
| PubMed | 生物医学权威 | 医学、生物 |
| IEEE Xplore | 工程技术 | 计算机、电子 |
| arXiv | 预印本 | 物理、数学、CS |
| Semantic Scholar | AI增强搜索 | 全学科 |

**搜索策略：**

1. 确定核心关键词（英文）
2. 使用布尔运算符：AND, OR, NOT
3. 使用引号精确匹配："deep learning"
4. 限定时间范围：近5年优先
5. 按引用量排序找高影响力文献

### 1.2 中文文献搜索

<HARD-GATE>
AI无法直接搜索中文学术数据库，必须让用户配合。
</HARD-GATE>

**推荐数据库：**
- **知网（CNKI）**：最全面的中文学术数据库
- **万方数据**：学位论文丰富
- **维普**：期刊论文
- **百度学术**：综合搜索

**AI提供的帮助：**

1. **生成搜索关键词**
2. **提供搜索策略建议**
3. **用户提供摘要后，AI帮助整理**

## 二、文献整理

### 2.1 文献信息记录

每篇文献记录以下信息：

```markdown
## 文献1
- **标题**：
- **作者**：
- **年份**：
- **期刊/会议**：
- **DOI/链接**：
- **核心观点**：
- **研究方法**：
- **主要结论**：
- **与本研究关系**：
```

### 2.2 文献分类

按主题而非按文献组织：

```
文献综述/
├── 理论基础/
├── 方法技术/
├── 应用研究/
└── 综述文章/
```

## 三、综述写作

### 3.1 综述结构

```
一、引言
   - 研究背景
   - 综述目的和范围

二、研究现状
   2.1 主题一
   2.2 主题二
   2.3 主题三

三、研究评述
   - 已有研究的贡献
   - 存在的不足
   - 研究趋势

四、研究空白与本研究定位
```

### 3.2 写作要点

**综合而非罗列**
- ❌ 张三（2020）研究了A。李四（2021）研究了B。
- ✅ 关于X问题，学界主要从三个角度展开研究：张三（2020）从A角度出发...；而李四（2021）则关注B方面...

**批判性分析**
- 不仅介绍研究内容，还要评价其贡献和局限
- 指出不同研究之间的关系（支持、补充、矛盾）

### 3.3 综述写作模板

**引入某一研究领域：**
```
[领域名称]是近年来[学科]研究的热点之一。自[开创性工作]以来，
该领域经历了快速发展，主要研究集中在[方向1]、[方向2]和[方向3]等方面。
```

**介绍代表性研究：**
```
[作者]（[年份]）提出了[方法/理论]，该研究[主要贡献]。
实验结果表明，[主要发现]。然而，该方法存在[局限性]。
```

**指出研究空白：**
```
尽管已有研究在[方面]取得了显著进展，但在[具体问题]方面仍存在不足。
具体而言，[问题1]尚未得到充分探讨，[问题2]缺乏系统性研究。
```

## 四、引用格式

### 中文（GB/T 7714-2015）

```
[1] 作者. 文章题目[J]. 期刊名, 年份, 卷(期): 页码.
[2] 作者. 书名[M]. 出版地: 出版社, 年份: 页码.
```

### 英文（APA 7th）

```
Author, A. A., & Author, B. B. (Year). Title. Journal, Volume(Issue), pages.
```

## 五、对话模板

### 场景0：使用脚本搜索文献（推荐）

**执行搜索命令**：

```bash
python scripts/scholar_search.py "搜索关键词" --sources crossref,semanticscholar --year 2020-2024 --limit 20 --format json
```

**输出示例**：

> "我来使用学术搜索脚本帮你查找文献。
>
> **搜索查询**：`[关键词]`
> **数据源**：CrossRef, Semantic Scholar
> **年份范围**：2020-2024
>
> **搜索结果**（按引用数排序）：
>
> | # | 标题 | 作者 | 年份 | 期刊 | 引用数 | DOI |
> |---|------|------|------|------|--------|-----|
> | 1 | [...] | [...] | 2023 | [...] | 156 | [DOI] |
> | 2 | [...] | [...] | 2022 | [...] | 89 | [DOI] |
>
> 需要我进一步获取某篇文献的详细信息吗？"

### 场景1：用户需要英文文献（WebSearch 方式）

> "我来帮你搜索相关英文文献。
>
> **搜索关键词**：[生成的关键词]
>
> **搜索结果**：
> 1. [文献标题] - [作者] ([年份])
>    - 期刊：[期刊名]
>    - 核心内容：[简要描述]
>    - DOI：[链接]
>
> **建议**：这些文献中，[文献X]与你的研究最相关。"

### 场景2：用户需要中文文献

> "中文学术文献需要你在知网（CNKI）等数据库搜索，我来帮你准备搜索策略。
>
> **建议搜索关键词**：
> - 主题词：[关键词1]、[关键词2]
> - 组合搜索：[关键词1] AND [关键词2]
>
> **搜索步骤**：
> 1. 访问 https://www.cnki.net/
> 2. 选择"高级搜索"
> 3. 输入上述关键词
> 4. 筛选条件：核心期刊/CSSCI，近5年
>
> **请将搜索到的文献摘要粘贴给我**，我帮你整理和分析。"

### 场景3：用户提供了文献摘要

> "收到，我来帮你整理这些文献。
>
> **文献整理**：
>
> | 序号 | 作者 | 年份 | 核心观点 | 与本研究关系 |
> |------|------|------|----------|--------------|
> | 1 | [作者] | [年份] | [观点] | [关系] |
>
> **综述建议**：
> 这些文献可以从以下角度组织...
>
> 需要我帮你起草综述段落吗？"

## 六、引用检查与验证

### 6.1 引用验证（必须）

**使用 `verification` 技能进行严格验证：**

| 声称 | 验证方式 | 不充分 |
|------|----------|--------|
| 引用存在 | CrossRef API 确认 DOI | "看起来正确" |
| 引用格式正确 | 运行格式检查脚本 | 目测检查 |
| 作者信息准确 | 搜索原始来源 | "应该没错" |

**验证脚本**：
```bash
# 验证 DOI 是否存在
curl -s "https://api.crossref.org/works/10.1000/doi123"

# 验证 BibTeX 文件
python scripts/scholar_search.py "your query" --format bibtex --output refs.bib
```

### 6.2 PDF 文献解析

**当用户提供 PDF 文件时，使用 `scripts/pdf_parser.py` 提取内容：**

```bash
# 提取 PDF 文本
python scripts/pdf_parser.py paper.pdf --output paper_text.txt

# 提取结构和摘要
python scripts/pdf_parser.py paper.pdf --sections --abstract --json paper_info.json

# 总结 PDF 内容
python scripts/pdf_parser.py paper.pdf --summarize
```

**输出内容**：
- 元数据（标题、作者、页数）
- 摘要
- IMRaD 章节（引言、方法、结果、讨论）
- 自动摘要

### 6.3 引用检查清单

**必须检查：**
- [ ] 所有引用的文献都真实存在（通过 DOI 验证）
- [ ] 作者、年份、标题信息准确
- [ ] 引用格式统一
- [ ] 正文引用与参考文献列表一一对应
- [ ] 每个引用都有上下文说明其与本研究的关系
