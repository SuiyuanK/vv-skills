# LaTeX 模板解析指南

本文件提供 LaTeX 模板解析的详细指导。

## 解析流程

```
1. 扫描 latex-templates/ 目录
2. 识别模板类型（学校/期刊/通用）
3. 解析模板结构
4. 提取章节命令和格式要求
5. 生成对应的章节文件
```

## 模板类型识别

### 学校论文模板

常见特征：
- 包含 `thesis`、`dissertation` 等关键词
- 有 `\degree`、`\school`、`\major` 等命令
- 包含封面、声明、致谢等特殊章节

### 期刊模板

常见特征：
- 期刊名称缩写（如 `ieee`、`elsevier`）
- 包含 `\journal`、`\volume`、`\doi` 等命令
- 通常没有封面页

### 通用模板

常见特征：
- 基于 `article`、`report`、`book` 类
- 使用 `ctex` 或 `ctexart` 支持中文

## 关键文件解析

### .cls 文件（文档类）

```latex
% 识别文档类型
\ProvidesClass{mythesis}

% 识别章节命令
\newcommand{\chapter}...
\newcommand{\section}...

% 识别特殊环境
\newenvironment{abstract}...
\newenvironment{acknowledgement}...
```

### .sty 文件（样式包）

```latex
% 识别宏包依赖
\RequirePackage{...}

% 识别自定义命令
\newcommand{\keyword}[1]{...}
\newcommand{\email}[1]{...}
```

### main.tex 文件（主文件）

```latex
% 识别文档类
\documentclass{mythesis}

% 识别章节结构
\chapter{绪论}
\chapter{文献综述}
...

% 识别参考文献样式
\bibliographystyle{gbt7714-numerical}
```

## 常见学校模板解析

### 清华大学（ThuThesis）

```latex
% 文档类
\documentclass[degree=master]{thuthesis}

% 元信息设置
\thusetup{
  title = {论文题目},
  degree-name = {硕士},
  department = {计算机系},
  ...
}

% 特殊命令
\makecover          % 生成封面
\frontmatter        % 前言部分
\mainmatter         % 正文部分
\backmatter         % 附录部分
```

**生成对应结构**：
```
chapters/
├── cover.tex           # 封面（自动生成）
├── 00-abstract.tex     # 摘要
├── 01-introduction.tex
├── ...
├── acknowledgements.tex # 致谢
└── appendix.tex        # 附录
```

### 北京大学（PKUThesis）

```latex
\documentclass{pkuthss}

\pkusetup{
  ...
}
```

### 浙江大学（ZJUThesis）

```latex
\documentclass{zjuthesis}
```

### 中国科学院（ucasthesis）

```latex
\documentclass{ucasthesis}
```

## 期刊模板解析

### IEEE 模板

```latex
\documentclass[conference]{IEEEtran}

% 常用命令
\IEEEauthorblockN{Author Name}
\IEEEauthorblockA{Affiliation}
```

### Elsevier 模板

```latex
\documentclass[review]{elsarticle}

% 常用命令
\journal{Journal Name}
\begin{highlights}...\end{highlights}
```

## 章节命令映射

| LaTeX 命令 | 对应层级 | 生成文件示例 |
|------------|----------|--------------|
| `\chapter{...}` | 章 | `01-xxx.tex` |
| `\section{...}` | 节 | 在章文件内 |
| `\subsection{...}` | 小节 | 在章文件内 |
| `\subsubsection{...}` | 小小节 | 在章文件内 |

## 特殊环境处理

### 摘要环境

```latex
% 模板定义
\begin{abstract}
...
\end{abstract}

% 生成对应文件
chapters/00-abstract.tex
```

### 关键词

```latex
% 常见格式
\begin{keywords}
关键词1；关键词2；关键词3
\end{keywords}

% 或
\keywords{关键词1, 关键词2, 关键词3}
```

### 致谢

```latex
% 常见格式
\begin{acknowledgement}
...
\end{acknowledgement}

% 或
\chapter*{致谢}
```

## 参考文献处理

### BibTeX 方式

```latex
\bibliographystyle{gbt7714-numerical}  % 样式
\bibliography{references}               % 文件名
```

生成 `references.bib` 文件。

### BibLaTeX 方式

```latex
\usepackage[backend=biber,style=gb7714-2015]{biblatex}
\addbibresource{references.bib}
```

## 错误处理

### 模板不完整

缺失关键文件时，提示用户补充：
```
检测到模板缺少以下文件：
- [ ] 模板类文件 (.cls)
- [ ] 主文件示例 (main.tex)

请补充完整后继续。
```

### 编码问题

检测文件编码，建议使用 UTF-8：
```
检测到模板文件使用 GBK 编码，建议转换为 UTF-8。
```

### 不支持的模板

遇到无法解析的模板：
```
该模板结构较为特殊，建议：
1. 手动参考模板示例编写
2. 使用通用 article/ctexart 类
3. 联系模板作者获取使用说明
```
