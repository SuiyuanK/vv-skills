---
name: latex-output
description: Use when user requests LaTeX format output or has provided school/journal LaTeX templates
---

# LaTeX 输出

负责将论文内容输出为 LaTeX 格式，支持用户提供的学校或期刊模板。

## 使用场景

1. 用户明确要求 LaTeX 输出
2. 用户提供了 LaTeX 模板
3. 目标期刊/学校要求 LaTeX 格式

## LaTeX 模板目录

用户可将模板文件放入 `latex-templates/` 目录：

```
latex-templates/
├── README.md              # 使用说明
├── template.cls           # 模板类文件
├── template.sty           # 模板样式文件
└── main-template.tex      # 模板主文件示例
```

## Checklist

- [ ] 检查 latex-templates/ 是否有用户模板
- [ ] 询问用户是否使用该模板
- [ ] 解析模板结构（章节命令、格式要求）
- [ ] 根据模板创建 .tex 章节文件
- [ ] 创建 main.tex 主文件
- [ ] 创建 references.bib 参考文献文件
- [ ] 验证可编译性

## 模板解析

### 识别章节命令

常见的章节命令：

```latex
\chapter{章节名}      % 章
\section{节名}        % 节
\subsection{小节名}   % 小节
\subsubsection{小小节} % 小小节
```

### 识别特殊环境

```latex
\begin{abstract}...\end{abstract}  % 摘要
\begin{keywords}...\end{keywords}  % 关键词
\begin{figure}...\end{figure}      % 图片
\begin{table}...\end{table}        % 表格
\begin{equation}...\end{equation}  % 公式
```

## 输出结构

### 使用模板时

```
论文项目/
├── latex-templates/        # 原始模板（保持不动）
├── chapters/               # 章节内容（.tex）
│   ├── 00-abstract.tex
│   ├── 01-introduction.tex
│   ├── 02-literature.tex
│   └── ...
├── figures/                # 图片文件
├── main.tex                # 主文件
├── references.bib          # 参考文献
└── plan/                   # 项目计划
```

### main.tex 模板

```latex
\documentclass{template}  % 或用户模板类

% 导入用户模板的样式
\usepackage{template}

% 基本设置
\title{论文题目}
\author{作者}
\date{\today}

\begin{document}

\maketitle

% 摘要
\input{chapters/00-abstract}

% 目录
\tableofcontents

% 正文章节
\input{chapters/01-introduction}
\input{chapters/02-literature}
\input{chapters/03-methods}
\input{chapters/04-results}
\input{chapters/05-discussion}
\input{chapters/06-conclusion}

% 参考文献
\bibliographystyle{gbt7714-numerical}  % 或其他样式
\bibliography{references}

\end{document}
```

## 章节文件格式

### .tex 章节文件示例

```latex
% chapters/01-introduction.tex
% 绪论

\chapter{绪论}

\section{研究背景}

随着...技术的发展，...领域面临着...的挑战。
本文针对...问题，提出...方法。

\section{研究目的与意义}

本研究旨在...

\subsection{理论意义}

...

\subsection{实践意义}

...

\section{研究内容与方法}

本文的研究内容主要包括：

\begin{enumerate}
    \item 第一部分...
    \item 第二部分...
    \item 第三部分...
\end{enumerate}

\section{论文结构}

本文共分为X章，各章内容安排如下：

第一章为绪论，介绍...
第二章为文献综述，综述...
...
```

## 参考文献（BibTeX）

### references.bib 格式

```bibtex
@article{author2023title,
    author = {张三 and 李四},
    title = {论文标题},
    journal = {期刊名称},
    year = {2023},
    volume = {10},
    number = {2},
    pages = {100-110},
}

@book{author2022book,
    author = {王五},
    title = {书籍名称},
    publisher = {出版社},
    year = {2022},
    address = {出版地},
}

@inproceedings{author2021conf,
    author = {赵六},
    title = {会议论文标题},
    booktitle = {会议名称},
    year = {2021},
    pages = {50-55},
}
```

## 常见模板适配

### 清华大学模板 (ThuThesis)

```latex
\documentclass[degree=master]{thuthesis}
```

特殊命令：
- `\thusetup{...}` 设置论文信息
- `\makecover` 生成封面
- `\frontmatter` 前言部分
- `\mainmatter` 正文部分
- `\backmatter` 附录部分

### 国科大模板 (ucasthesis)

```latex
\documentclass{ucasthesis}
```

### 期刊模板

不同期刊格式各异，需根据用户提供的模板解析。

## 编译说明

在 plan/notes.md 中记录编译命令：

```markdown
## LaTeX 编译

### 推荐工具
- TeXLive (跨平台)
- MacTeX (macOS)
- MiKTeX (Windows)

### 编译命令
```bash
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

### 一键编译
```bash
latexmk -xelatex main.tex
```
```

## 与 Markdown 的转换

### 从 Markdown 转 LaTeX

如果用户已有 Markdown 内容，可以转换：

1. 标题：`# 标题` → `\chapter{标题}`
2. 加粗：`**文字**` → `\textbf{文字}`
3. 引用：`> 引用` → `\begin{quote}引用\end{quote}`
4. 代码：`` `代码` `` → `\texttt{代码}`
5. 列表：`- 项目` → `\begin{itemize}\item 项目\end{itemize}`

### 注意事项

- LaTeX 特殊字符需转义：`# $ % & _ { } ~ ^`
- 中文需使用 XeLaTeX 编译
- 图片路径使用相对路径

## 错误处理

### 如果没有模板

> "未检测到 LaTeX 模板。请选择：
> 1. 提供模板文件（放入 latex-templates/）
> 2. 使用默认 article 类
> 3. 使用 ctexart 类（中文）
> 4. 继续使用 Markdown 格式"

### 如果模板不完整

> "检测到模板文件，但缺少 [文件名]。
> 请补充完整模板，或使用默认设置。"
