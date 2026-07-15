# Changelog

所有重要更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

## [3.1.0] - 2026-05-10

### 新增

- 添加 `paper-orchestration`，用于中型/整篇论文任务的任务包、两阶段 review 和 capability-use audit。
- 添加 `evidence-driven-writing`，强制引言、相关工作和背景段落先形成 evidence map 与段落蓝图。
- 添加 `experiment-results-planning`，区分真实结果与 mock planning data，并要求实验协议、表格 schema 和图表 data manifest。
- 添加 `scripts/check_skill_integrity.ps1` 和 `scripts/research_quality_gate.ps1`，用于 skill 完整性和稿件质量门验证。
- README 增加 Python 本地图表、Gemini 提示词图示和科研写作讨论群入口。

### 变更

- 更新 `writing-chapters`、`literature-review`、`figures-python`、`verification` 和入口路由，使文献、方法、实验、图表和验证形成闭环。
- 更新 plan 模板，加入 task-packets、chapter-blueprints、review、evidence-map、table-schema 和 data-manifest 约定。
- 修复 `style_check.ps1` 的 UTF-8 读取问题，并增加正文污染检测。
- README 补充去 AI 化写作边界和 Pandoc 转 Word 的可选说明。

## [3.0.0] - 2026-03-19

### 新增

#### 多平台适配
- 添加 `.claude-plugin/plugin.json` - Claude Code 插件配置
- 添加 `.cursor-plugin/plugin.json` - Cursor 插件配置
- 添加 `.codex/INSTALL.md` - Codex 安装指南
- 添加 `.opencode/INSTALL.md` - OpenCode 安装指南
- 添加 `GEMINI.md` - Gemini CLI 配置
- 添加 `AGENTS.md` - 通用代理配置

#### Hooks 机制
- 添加 `hooks/session-start` - 会话启动脚本
- 添加 `hooks/hooks.json` - Claude Code hooks 配置
- 添加 `hooks/hooks-cursor.json` - Cursor hooks 配置
- 添加 `hooks/run-hook.cmd` - Windows 兼容脚本

#### 核心技能（新架构）
- `skills/using-research-writing/SKILL.md` - 入口技能，定义规则和路由
- `skills/brainstorming-research/SKILL.md` - 科研头脑风暴，多轮问答确认论文信息
- `skills/writing-chapters/SKILL.md` - 章节写作，逐章输出
- `skills/latex-output/SKILL.md` - LaTeX 模板支持

#### LaTeX 功能
- 添加 `latex-templates/` 目录 - 用户放置学校/期刊模板
- 添加 `latex-templates/README.md` - 模板使用说明
- 支持解析用户模板结构并生成对应 .tex 文件

#### AI 约束强化
- 使用 `<EXTREMELY-IMPORTANT>` 标签强调关键规则
- 使用 `<HARD-GATE>` 标签设置强制门禁
- 添加 Red Flags 表格防止 AI 跳过流程
- 每个技能添加 Checklist 追踪

### 变更

#### 架构重构
- 将 `modules/` 下的模块重构为 `skills/` 格式
- 每个技能独立目录，包含 `SKILL.md`
- 添加 YAML frontmatter（name, description）

#### 头脑风暴流程
- 新增 7 轮问答流程：
  1. 论文类型确认
  2. 学科领域确认
  3. 论文题目确认
  4. 研究背景与目的
  5. 研究方法/技术路线
  6. 章节结构确认
  7. 汇总确认

#### 输出结构
- 章节输出到 `chapters/` 目录
- 每章一个独立 .md 或 .tex 文件
- 文件名使用英文避免路径问题

### 技能列表（共 15 个）

| 技能名称 | 描述 |
|----------|------|
| using-research-writing | 入口技能 |
| brainstorming-research | 头脑风暴 |
| writing-chapters | 章节写作 |
| latex-output | LaTeX 输出 |
| literature-review | 文献综述 |
| figures-python | Python 图表 |
| figures-diagram | 流程图/结构图 |
| peer-review | 自审检查 |
| statistical-analysis | 统计分析 |
| environment-setup | 环境配置 |
| prompts-collection | 提示词集 |
| writing-core | 核心写作规范 |
| writing-humanities | 文科写作 |
| writing-medical | 医学写作 |
| writing-law | 法学写作 |

## [2.5.0] - 2026-03-04

### 变更
- 更新版本号和日期
- 修复模板通用性问题

## [2.0.0] - 2026-02-26

### 新增
- 初始版本
- 基础模块：writing-core, literature-review, figures-python 等
- plan-template 目录结构
- scripts 目录（init_plan, style_check）
