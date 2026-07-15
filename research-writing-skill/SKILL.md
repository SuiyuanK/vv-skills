---
name: research-writing-assistant
description: Use when writing academic papers, theses, or research articles - supports brainstorming, chapter writing, literature review, and LaTeX output
allowed-tools: Read Write Edit Bash WebSearch
---

# 科研写作助手 (Research Writing Assistant)

面向本科与研究生论文写作的执行型 Skill。

## 哲学原则

- **流程优于即兴** — 头脑风暴先行，结构确认再写作
- **证据优于声称** — 引用可追溯，绝不编造文献
- **简洁优于复杂** — 去AI化写作，拒绝机械表达
- **确认优于假设** — 每章用户确认，避免返工

## 新架构（v3.0）

本 Skill 已升级为模块化技能架构，支持多平台：

| 平台 | 配置 |
|------|------|
| Claude Code | `.claude-plugin/plugin.json` |
| Cursor | `.cursor-plugin/plugin.json` |
| Codex | `.codex/INSTALL.md` |
| OpenCode | `.opencode/INSTALL.md` |
| Gemini CLI | `GEMINI.md` |

## 技能列表

### 核心流程技能

| 技能 | 路径 | 说明 |
|------|------|------|
| using-research-writing | `skills/using-research-writing/` | 入口技能，规则和路由 |
| paper-orchestration | `skills/paper-orchestration/` | 中型/整篇任务编排 |
| brainstorming-research | `skills/brainstorming-research/` | 头脑风暴，7轮问答 |
| writing-chapters | `skills/writing-chapters/` | 章节写作 |
| latex-output | `skills/latex-output/` | LaTeX 输出 |

### 写作支持技能

| 技能 | 路径 | 说明 |
|------|------|------|
| writing-core | `skills/writing-core/` | 核心写作规范 |
| writing-humanities | `skills/writing-humanities/` | 文科写作 |
| writing-medical | `skills/writing-medical/` | 医学写作 |
| writing-law | `skills/writing-law/` | 法学写作 |
| literature-review | `skills/literature-review/` | 文献综述 |
| evidence-driven-writing | `skills/evidence-driven-writing/` | 文献驱动引言/相关工作 |
| experiment-results-planning | `skills/experiment-results-planning/` | 实验、结果和 mock 数据规划 |

### 工具技能

| 技能 | 路径 | 说明 |
|------|------|------|
| verification | `skills/verification/` | 验证机制，确保完成声称有证据 |
| figures-python | `skills/figures-python/` | Python 数据图表 |
| figures-diagram | `skills/figures-diagram/` | 流程图/架构图 |
| peer-review | `skills/peer-review/` | 自审检查 |
| statistical-analysis | `skills/statistical-analysis/` | 统计分析 |
| prompts-collection | `skills/prompts-collection/` | 提示词集合 |
| environment-setup | `skills/environment-setup/` | 环境配置 |

## Red Flags（停止并检查）

### 流程类 Red Flags

| AI的想法 | 正确做法 |
|----------|----------|
| "用户说得很清楚了，直接开始写" | 必须先完成 brainstorming-research |
| "这只是修改一小段" | 检查是否有 plan/，没有则先创建 |
| "先写一段看看效果" | 必须先确认论文类型和章节结构 |
| "用户很着急，跳过讨论" | 流程可以加速，但不能跳过关键确认 |
| "这是简单任务，不需要 plan" | 任何写作任务都需要 plan 记录 |
| "我知道怎么写论文" | 必须按用户选择的类型和结构写 |
| "先把内容写完再说格式" | 格式在 brainstorming 阶段确定 |
| "这章内容很简单，不用确认" | 每章写完都必须让用户确认 |

### 文献类 Red Flags

| AI的想法 | 正确做法 |
|----------|----------|
| "文献我可以补充一些" | 绝不编造文献，必须可追溯 |
| "我记得这个技能的内容" | 技能会更新，必须重新读取当前版本 |
| "这个引用看起来很合理" | 没有来源的引用一律不写 |
| "用户应该知道这个领域" | 不假设用户知识，问清楚再写 |

### 验证类 Red Flags（来自 verification 技能）

| AI的想法 | 正确做法 |
|----------|----------|
| "应该写完了" | 运行验证命令确认 |
| "章节看起来完整" | 执行字数统计和结构检查 |
| "引用应该是真的" | 调用 CrossRef API 或搜索验证 |
| "格式应该没问题" | 运行格式检查脚本 |
| "搜索完成" | 检查结果数量和 DOI 列表 |
| "我很确信" | 确信 ≠ 证据，运行验证 |
| "就这一次跳过验证" | 没有例外 |

<EXTREMELY-IMPORTANT>
任何论文写作任务开始前，必须先调用 `skills/using-research-writing/` 确定流程。
不允许跳过头脑风暴直接写作。
</EXTREMELY-IMPORTANT>

### 标准流程

1. **入口路由** → 调用 `using-research-writing`
   - 中型/整篇任务先转入 `paper-orchestration`
   - 简单章节任务继续检查 plan/ 与章节状态

2. **中型任务编排** → 调用 `paper-orchestration`
   - 多章节、文献驱动、实验图表或质量返工任务必须先生成任务包
   - 完成后记录 capability-use audit（能力使用审计）

3. **头脑风暴** → 调用 `brainstorming-research`
   - 确认论文类型（7种）
   - 确认学科领域
   - 确认题目、研究背景、方法
   - 确认章节结构
   - 检测 LaTeX 模板
   - 创建 plan/ 和 chapters/

4. **章节写作** → 调用 `writing-chapters`
   - 每章独立文件
   - 两阶段 Review（见下方）
   - 用户确认后继续

5. **LaTeX 输出**（可选）→ 调用 `latex-output`
   - 用户提供模板
   - 输出 .tex 文件
   - 可直接编译

4. **两阶段 Review**（每章完成后）
   - **阶段一：规范合规** — 检查字数、结构、引用格式是否满足要求
   - **阶段二:质量检查** — 检查去AI化、语言流畅度、学术表达

## 模块兼容（向后兼容）

## 两阶段 Review 机制

每章写作完成后，执行两阶段检查：

**阶段一：规范合规检查**
- 字数是否符合要求
- 章节结构是否完整
- 引用格式是否正确
- 小节标题是否清晰

**阶段二：质量检查**
- 去 AI 化：无机械过渡词、无空壳强调句
- 语言流畅：无重复表达、无冗余
- 学术表达：使用"本文"、"本研究"等客观表述
- 段落结构：优先连贯段落，不使用列表堆砌

## 模块兼容（向后兼容）

原有 `modules/` 目录仍然保留，可通过以下方式使用：

| 场景 | 模块 |
|------|------|
| 通用写作 | `modules/writing-core.md` |
| 文科写作 | `modules/writing-humanities.md` |
| 医学写作 | `modules/writing-medical.md` |
| 法学写作 | `modules/writing-law.md` |
| 文献综述 | `modules/literature-review.md` |
| 文献驱动写作 | `skills/evidence-driven-writing/` |
| 论文工作流编排 | `skills/paper-orchestration/` |
| 实验结果规划 | `skills/experiment-results-planning/` |
| 翻译润色 | `modules/prompts-collection.md` |
| 自审检查 | `modules/peer-review.md` |
| Python图表 | `modules/figures-python.md` |
| 流程图 | `modules/figures-diagram.md` |
| 环境配置 | `modules/environment-setup.md` |
| LaTeX指南 | `modules/latex-guide.md` |

## 输出规范

### 去 AI 化
- 禁用机械过渡词：首先、其次、最后、此外
- 禁用空壳强调句：值得注意的是、需要指出的是
- 语气客观，使用"本文"、"本研究"

### 格式规范
- 段落之间空一行
- 正文不使用加粗
- 论文正文优先连贯段落，不使用列表堆砌

### 引用规范
- 绝不编造文献
- 引用必须可追溯

## 文献与事实规则

1. 绝不编造文献。
2. 英文文献可检索后引用，中文文献优先让用户提供来源。
3. 任何引用必须可追溯（作者、年份、出处至少完整两项）。

## 版本信息

- **版本**：3.1.0
- **更新日期**：2026-05-10
- **维护目标**：可执行、可追踪、流程化、多平台适配

### v3.1 更新内容

1. **哲学原则** — 明确核心价值观
2. **CSO优化** — 所有技能 description 使用 "Use when..." 格式
3. **增强 Red Flags** — 从10条扩展到12条
4. **两阶段 Review** — 规范合规 + 质量检查
5. **语言默认规则** — 毕业论文默认中文，期刊根据要求
6. **结构模板** — 7种论文类型的默认结构模板
7. **交互优化** — 让用户少做选择，多做确认
