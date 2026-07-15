---
name: prompts-collection
description: Use for translation, polishing, or de-AI-ification of academic text - provides ready-to-use prompt templates
---

# 写作提示词集合

本技能整合了顶尖研究机构和高校研究员日常使用的论文写作提示词。

## 一、翻译类

### 1.1 中文转英文（学术翻译）

```markdown
# Role
你是一位兼具顶尖科研写作专家与资深会议审稿人双重身份的助手。

# Task
请将我提供的【中文草稿】翻译并润色为【英文学术论文片段】。

# Constraints
1. 不使用加粗、斜体或引号
2. 逻辑严谨，用词准确，使用常见单词
3. 不使用\item列表，使用连贯段落
4. 去除"AI味"，行文自然

# Output
- Part 1 [LaTeX]：翻译后的英文
- Part 2 [Translation]：对应中文直译
```

### 1.2 英文转中文（快速理解）

```markdown
# Role
你是一位资深的计算机科学领域的学术翻译官。

# Task
请将【英文LaTeX代码片段】翻译为流畅、易读的【中文文本】。

# Constraints
1. 删除所有\cite{}、\ref{}等命令
2. 严格直译，不进行润色
3. 只输出纯中文文本段落
```

## 二、润色类

### 2.1 英文论文润色

```markdown
# Role
你是计算机科学领域的资深学术编辑。

# Task
请对【英文LaTeX代码片段】进行深度润色与重写。

# Constraints
1. 调整句式结构，增强正式性与逻辑连贯性
2. 彻底修正所有语法错误
3. 使用标准学术书面语，禁用缩写形式
4. 保留原文LaTeX命令

# Output
- Part 1 [LaTeX]：润色后的英文
- Part 2 [Translation]：对应中文直译
- Part 3 [Modification Log]：修改说明
```

### 2.2 中文论文润色

```markdown
# Role
你是专注于计算机科学领域的资深中文学术编辑。

# Task
请对【中文论文段落】进行专业审视与润色。

# Constraints
1. 仅修正口语化表达、语法错误、逻辑断层
2. 原文已清晰则保留原样
3. 使用中文全角标点

# Output
- Part 1 [Refined Text]：重写后的中文段落
- Part 2 [Review Comments]：修改说明
```

## 三、去AI化

### 3.1 去AI味（英文）

```markdown
# Role
你是计算机科学领域的资深学术编辑，专注于提升论文自然度。

# Task
请对【英文LaTeX代码片段】进行"去AI化"重写。

# Constraints
1. 避免使用被滥用的词汇（leverage, delve into, tapestry等）
2. 将item内容转化为连贯段落
3. 删除机械连接词（First and foremost等）
4. 原文已自然则保留

# Output
- Part 1 [LaTeX]：重写后的代码
- Part 2 [Translation]：对应中文直译
- Part 3 [Modification Log]：调整说明或"[检测通过]"
```

### 3.2 AI味浓厚词汇表（避免使用）

| 避免使用 | 推荐替换 |
|----------|----------|
| leverage | use, employ |
| delve into | investigate, examine |
| tapestry | context, framework |
| underscore | highlight, show |
| pivotal | important, key |
| nuanced | detailed, subtle |
| foster | encourage, support |
| elucidate | explain, clarify |
| intricate | complex, detailed |
| paramount | important, critical |

### 3.3 去AI味（中文期刊论文，信息保留版）

```markdown
# Role
你是一位熟悉中文期刊论文写法的科研写作编辑，能够在不改变技术含义和数据口径的前提下，降低中文论文段落中的AI腔、翻译腔和模板化表达。

# Task
请改写【中文论文段落或草稿】，使其更接近中文期刊论文中自然、稳妥、可提交的正文表达。

# Constraints
1. 去AI化不等于压缩。除非我明确要求缩写，不要主动删减事实、数据、限定条件和解释句。
2. 必须保留研究对象、数据范围、样本口径、方法条件、指标含义、实验边界、结论限制和专有名词。
3. 使用连续段落，不使用项目符号，不使用加粗、斜体。
4. 避免"首先、其次、最后、此外、另外、接下来、总之"等机械连接词，改用语义自然的承接。
5. 避免"值得注意的是、需要指出的是、重要的是、必须强调的是"等空壳句式。
6. 减少英文直译式语序，不把每句话都改成"对象-动作-结论"的机械短句。
7. 避免审稿回复式表达。正文中不要写成"该指标反映的是""不能理解为""用于避免口径悬空"，应改为自然叙述。
8. 保持判断克制。涉及效果、提升、贡献或应用意义时，优先使用具体指标、现象和边界支撑，不写空泛拔高。
9. 如果原文虽然略显啰嗦但信息完整、语序自然，可以只做轻微调整；不要为了显得精炼而压掉必要信息。

# Output
- Part 1 [Refined Text]：改写后的中文正文
- Part 2 [Modification Log]：说明主要改动，特别标出是否处理了翻译腔、模板腔、审稿回复口吻或空泛判断；若原文已自然，输出"[检测通过]"
- Part 3 [Information Check]：确认是否保留了关键对象、数据、方法、指标和边界；如存在信息缺失风险，明确指出
```

## 四、扩写与缩写

### 4.1 缩写（压缩字数）

```markdown
# Task
请将【英文LaTeX代码片段】进行微幅缩减（减少约5-15个单词）。

# Constraints
1. 保留所有核心信息
2. 句法压缩：从句转短语，被动转主动
3. 剔除冗余填充词

# Output
- Part 1 [LaTeX]：缩减后的代码
- Part 2 [Translation]：对应中文直译
- Part 3 [Modification Log]：调整说明
```

### 4.2 扩写（增加内容）

```markdown
# Task
请将【英文LaTeX代码片段】进行微幅扩写（增加约5-15个单词）。

# Constraints
1. 不添加无意义形容词
2. 挖掘隐含的结论、前提或因果关系
3. 增加必要的连接词明确句间关系

# Output
- Part 1 [LaTeX]：扩写后的代码
- Part 2 [Translation]：对应中文直译
- Part 3 [Modification Log]：调整说明
```

## 五、逻辑检查

### 5.1 终稿逻辑检查

```markdown
# Task
请对【英文LaTeX代码片段】进行最后的一致性与逻辑核对。

# Constraints
1. 预设草稿质量较高
2. 仅报告致命逻辑、术语不一致、严重语病
3. 忽略"可改可不改"的问题

# Output
- 无问题：[检测通过，无实质性问题]
- 有问题：中文分点简要指出
```

## 六、图表相关

### 6.1 生成图标题（Figure Caption）

```markdown
# Task
请将【中文描述】转化为【英文图标题】。

# Constraints
1. 名词性短语用Title Case，完整句子用Sentence case
2. 去除"The figure shows"等冗余开头
3. 只输出标题文本，不含"Figure 1:"前缀
```

### 6.2 生成表标题（Table Caption）

```markdown
# Task
请将【中文描述】转化为【英文表标题】。

# Constraints
1. 推荐使用：Comparison with, Ablation study on, Results on
2. 避免：showcase, depict，改用show, compare, present
```

## 七、审稿视角

### 7.1 Reviewer视角审视论文

```markdown
# Role
你是一位严苛的资深学术审稿人。

# Task
请对【PDF论文文件】撰写审稿报告。

# Output
Part 1 [Review Report]：
- Summary: 一句话总结
- Strengths: 1-2点贡献
- Weaknesses (Critical): 3-5个致命问题
- Rating: 1-10分

Part 2 [Strategic Advice]：
- 解释问题原因
- 具体改进建议
```

## 八、使用建议

1. **复制即用**：以上提示词可直接复制使用
2. **按需选择**：根据当前任务选择对应提示词
3. **保持完整**：完整复制以获得最佳效果
4. **替换输入**：将示例部分替换为实际内容
