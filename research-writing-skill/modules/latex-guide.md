# LaTeX模板与格式指南

本模块提供学术论文LaTeX排版的模板和规范。

---

## 一、LaTeX基础

### 1.1 文档结构

```latex
\documentclass[12pt,a4paper]{article}

% 导言区：加载宏包、设置格式
\usepackage{...}

\begin{document}

% 正文区
\title{论文标题}
\author{作者}
\maketitle

\begin{abstract}
摘要内容
\end{abstract}

\section{引言}
正文内容...

\end{document}
```

### 1.2 常用宏包

```latex
% 中文支持
\usepackage[UTF8]{ctex}

% 数学公式
\usepackage{amsmath,amssymb,amsthm}

% 图表
\usepackage{graphicx}
\usepackage{booktabs}  % 三线表
\usepackage{multirow}  % 合并单元格

% 引用
\usepackage{hyperref}
\usepackage{cite}

% 代码
\usepackage{listings}

% 算法
\usepackage{algorithm}
\usepackage{algorithmic}

% 页面设置
\usepackage{geometry}
\geometry{left=2.5cm,right=2.5cm,top=2.5cm,bottom=2.5cm}

% 行距
\usepackage{setspace}
\onehalfspacing  % 1.5倍行距
```

---

## 二、中文学位论文模板

### 2.1 基本模板

```latex
\documentclass[12pt,a4paper,oneside]{ctexbook}

% 页面设置
\usepackage{geometry}
\geometry{left=3cm,right=2.5cm,top=2.5cm,bottom=2.5cm}

% 行距
\usepackage{setspace}
\onehalfspacing

% 数学
\usepackage{amsmath,amssymb}

% 图表
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{caption}
\captionsetup{font=small,labelfont=bf}

% 引用
\usepackage[numbers,sort&compress]{natbib}

% 超链接
\usepackage{hyperref}
\hypersetup{
    colorlinks=true,
    linkcolor=black,
    citecolor=blue,
    urlcolor=blue
}

% 页眉页脚
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[C]{\leftmark}
\fancyfoot[C]{\thepage}

\begin{document}

% 封面
\begin{titlepage}
\centering
\vspace*{2cm}
{\LARGE\bfseries 学校名称\\[0.5cm]}
{\Large 硕士学位论文\\[2cm]}
{\huge\bfseries 论文题目\\[2cm]}
{\Large
\begin{tabular}{rl}
作者姓名： & XXX \\
指导教师： & XXX 教授 \\
学科专业： & XXX \\
研究方向： & XXX \\
\end{tabular}
\\[2cm]}
{\Large \today}
\end{titlepage}

% 摘要
\chapter*{摘要}
\addcontentsline{toc}{chapter}{摘要}
摘要内容...

\textbf{关键词：} 关键词1；关键词2；关键词3

\chapter*{Abstract}
\addcontentsline{toc}{chapter}{Abstract}
Abstract content...

\textbf{Keywords:} keyword1; keyword2; keyword3

% 目录
\tableofcontents
\newpage

% 正文
\chapter{绪论}
\section{研究背景}
\section{研究现状}
\section{研究内容}

\chapter{相关理论}

\chapter{研究方法}

\chapter{实验与分析}

\chapter{结论与展望}

% 参考文献
\bibliographystyle{gbt7714-numerical}
\bibliography{references}

% 致谢
\chapter*{致谢}
\addcontentsline{toc}{chapter}{致谢}
致谢内容...

\end{document}
```

### 2.2 图片插入

```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.8\textwidth]{figures/example.png}
    \caption{图片标题}
    \label{fig:example}
\end{figure}

% 引用：如图\ref{fig:example}所示
```

### 2.3 三线表

```latex
\begin{table}[htbp]
    \centering
    \caption{表格标题}
    \label{tab:example}
    \begin{tabular}{lccc}
        \toprule
        方法 & 准确率 & 召回率 & F1值 \\
        \midrule
        方法A & 0.85 & 0.82 & 0.83 \\
        方法B & 0.88 & 0.86 & 0.87 \\
        本文方法 & \textbf{0.92} & \textbf{0.90} & \textbf{0.91} \\
        \bottomrule
    \end{tabular}
\end{table}
```

### 2.4 公式

```latex
% 行内公式
这是行内公式 $E=mc^2$。

% 独立公式（带编号）
\begin{equation}
    f(x) = \int_{-\infty}^{\infty} e^{-x^2} dx
    \label{eq:gaussian}
\end{equation}

% 多行公式
\begin{align}
    a &= b + c \\
    d &= e + f
\end{align}

% 无编号公式
\begin{equation*}
    y = ax + b
\end{equation*}
```

---

## 三、英文期刊模板

### 3.1 IEEE格式

```latex
\documentclass[conference]{IEEEtran}

\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{cite}

\begin{document}

\title{Paper Title}

\author{
    \IEEEauthorblockN{First Author}
    \IEEEauthorblockA{Affiliation\\
    Email: author@example.com}
    \and
    \IEEEauthorblockN{Second Author}
    \IEEEauthorblockA{Affiliation\\
    Email: author2@example.com}
}

\maketitle

\begin{abstract}
Abstract text (150-200 words)...
\end{abstract}

\begin{IEEEkeywords}
keyword1, keyword2, keyword3
\end{IEEEkeywords}

\section{Introduction}

\section{Related Work}

\section{Methodology}

\section{Experiments}

\section{Conclusion}

\bibliographystyle{IEEEtran}
\bibliography{references}

\end{document}
```

### 3.2 ACM格式

```latex
\documentclass[sigconf]{acmart}

\begin{document}

\title{Paper Title}

\author{First Author}
\affiliation{
    \institution{University}
    \city{City}
    \country{Country}
}
\email{author@example.com}

\begin{abstract}
Abstract text...
\end{abstract}

\begin{CCSXML}
% ACM分类代码
\end{CCSXML}

\keywords{keyword1, keyword2}

\maketitle

\section{Introduction}

\bibliographystyle{ACM-Reference-Format}
\bibliography{references}

\end{document}
```

### 3.3 NeurIPS/ICML格式

```latex
\documentclass{article}
\usepackage{neurips_2024}  % 或 icml2024

\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}

\title{Paper Title}

\author{
    Author Name \\
    Affiliation \\
    \texttt{email@example.com}
}

\begin{document}

\maketitle

\begin{abstract}
Abstract (4-6 sentences)...
\end{abstract}

\section{Introduction}

\section{Related Work}

\section{Method}

\section{Experiments}

\section{Conclusion}

\bibliography{references}
\bibliographystyle{plainnat}

\end{document}
```

---

## 四、参考文献管理

### 4.1 BibTeX格式

```bibtex
% 期刊论文
@article{author2023title,
    author = {Author, First and Author, Second},
    title = {Paper Title},
    journal = {Journal Name},
    year = {2023},
    volume = {10},
    number = {2},
    pages = {100--120},
    doi = {10.1000/example}
}

% 会议论文
@inproceedings{author2023conf,
    author = {Author, First},
    title = {Paper Title},
    booktitle = {Proceedings of Conference},
    year = {2023},
    pages = {1--10}
}

% 书籍
@book{author2023book,
    author = {Author, First},
    title = {Book Title},
    publisher = {Publisher},
    year = {2023},
    edition = {2nd}
}

% 预印本
@article{author2023arxiv,
    author = {Author, First},
    title = {Paper Title},
    journal = {arXiv preprint arXiv:2301.00000},
    year = {2023}
}
```

### 4.2 中文参考文献（GB/T 7714）

```bibtex
% 使用 gbt7714 宏包
\usepackage{gbt7714}
\bibliographystyle{gbt7714-numerical}  % 顺序编码
% 或
\bibliographystyle{gbt7714-author-year}  % 著者-出版年
```

### 4.3 引用命令

```latex
% 基本引用
\cite{author2023title}           % [1]
\citep{author2023title}          % (Author, 2023)
\citet{author2023title}          % Author (2023)

% 多篇引用
\cite{ref1,ref2,ref3}            % [1-3] 或 [1,2,3]
```

---

## 五、常见格式要求

### 5.1 页面设置对照

| 类型 | 页边距 | 字号 | 行距 |
|------|--------|------|------|
| 中文学位论文 | 左3cm，其他2.5cm | 小四/12pt | 1.5倍 |
| IEEE | 默认 | 10pt | 单倍 |
| ACM | 默认 | 9pt | 单倍 |
| NeurIPS/ICML | 默认 | 10pt | 单倍 |

### 5.2 字体设置

```latex
% 中文字体（ctex自动处理）
% 英文字体
\usepackage{times}  % Times New Roman
% 或
\usepackage{mathptmx}  % 数学公式也用Times
```

### 5.3 图表编号

```latex
% 按章节编号（如 图1.1, 图1.2, 图2.1）
\usepackage{chngcntr}
\counterwithin{figure}{chapter}
\counterwithin{table}{chapter}
\counterwithin{equation}{chapter}
```

---

## 六、常见问题

### 6.1 中文显示问题

```latex
% 使用 ctex 宏包
\documentclass[UTF8]{ctexart}  % 或 ctexbook, ctexrep

% 或在英文文档类中
\usepackage[UTF8]{ctex}
```

### 6.2 图片路径

```latex
% 设置图片搜索路径
\graphicspath{{figures/}{images/}}

% 然后可以直接用文件名
\includegraphics{example.png}
```

### 6.3 编译顺序

```bash
# 有参考文献时
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

### 6.4 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| Undefined control sequence | 命令未定义 | 检查宏包是否加载 |
| Missing $ inserted | 数学符号在文本模式 | 用$...$包围 |
| File not found | 文件路径错误 | 检查路径和文件名 |
| Package clash | 宏包冲突 | 调整加载顺序 |

---

## 七、推荐工具

### 7.1 在线编辑器
- **Overleaf**: https://www.overleaf.com/ （推荐，支持协作）
- **TeXPage**: https://www.texpage.com/ （国内访问快）

### 7.2 本地编辑器
- **TeXstudio**: 跨平台，功能全面
- **VS Code + LaTeX Workshop**: 现代化体验
- **TeXShop**: macOS原生

### 7.3 参考文献管理
- **Zotero**: 免费，支持BibTeX导出
- **Mendeley**: 免费，PDF管理
- **JabRef**: 专门的BibTeX管理

---

## 八、模板获取

### 8.1 学位论文模板
- 各高校研究生院官网
- GitHub搜索"[学校名] thesis template"
- CTAN: https://ctan.org/

### 8.2 期刊/会议模板
- IEEE: https://www.ieee.org/conferences/publishing/templates.html
- ACM: https://www.acm.org/publications/proceedings-template
- NeurIPS/ICML: 官网提供
- Springer/Elsevier: 各期刊投稿页面

### 8.3 中文模板
- CTeX: https://github.com/CTeX-org
- 各高校开源模板（GitHub搜索）
