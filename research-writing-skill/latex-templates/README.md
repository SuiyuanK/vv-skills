# LaTeX 模板目录

将你的学校或期刊 LaTeX 模板文件放在此目录下。

## 支持的文件类型

- `.cls` - 文档类文件
- `.sty` - 样式包文件
- `.tex` - 模板主文件
- `.bst` - 参考文献样式文件

## 使用方法

1. 将模板文件复制到此目录
2. 在开始写作时，告诉 AI "使用 LaTeX 模板"
3. AI 会自动解析模板结构并生成对应格式的章节文件

## 常见模板来源

### 高校模板

- [清华大学 ThuThesis](https://github.com/tuna/thuthesis)
- [中国科学院大学 ucasthesis](https://github.com/mohuangrui/ucasthesis)
- [北京大学 PKUThesis](https://github.com/CasperVector/pkuthss)
- [浙江大学 ZJUThesis](https://github.com/TheNetAdmin/zjuthesis)
- [上海交通大学 SJTUThesis](https://github.com/sjtug/SJTUThesis)

### 期刊模板

- IEEE: [IEEEtran](https://www.ieee.org/conferences/publishing/templates.html)
- Elsevier: [elsarticle](https://www.elsevier.com/authors/policies-and-guidelines/latex-instructions)
- Springer: [svjour3](https://www.springer.com/gp/authors-editors/book-authors-editors/resources-guidelines/book-manuscript-guidelines/manuscript-preparation/5636)

## 目录结构示例

```
latex-templates/
├── README.md           # 本文件
├── mythesis.cls        # 学校论文模板类
├── mythesis.sty        # 附加样式
├── gbt7714.bst         # 国标参考文献样式
└── logo.pdf            # 学校logo（如需要）
```

## 注意事项

1. 确保模板文件完整（所有依赖文件都包含）
2. 中文模板通常需要 XeLaTeX 编译
3. 部分模板可能需要特定的字体，请参考模板文档
