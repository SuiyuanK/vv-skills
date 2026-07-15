# 科研写作助手 (Research Writing Assistant)

本项目包含科研论文写作技能集。当用户提出与论文写作相关的任务时，请调用相应技能。

## 技能列表

| 技能名称 | 路径 | 用途 |
|----------|------|------|
| using-research-writing | skills/using-research-writing/SKILL.md | 入口技能，定义规则和路由 |
| paper-orchestration | skills/paper-orchestration/SKILL.md | 中型/整篇任务编排、任务包和能力使用审计 |
| brainstorming-research | skills/brainstorming-research/SKILL.md | 头脑风暴，确定论文类型和结构 |
| evidence-driven-writing | skills/evidence-driven-writing/SKILL.md | 文献驱动的引言、相关工作和背景段落 |
| writing-chapters | skills/writing-chapters/SKILL.md | 章节写作 |
| experiment-results-planning | skills/experiment-results-planning/SKILL.md | 实验协议、结果表格、mock 数据边界 |
| latex-output | skills/latex-output/SKILL.md | LaTeX 输出 |
| literature-review | skills/literature-review/SKILL.md | 文献综述 |
| figures-python | skills/figures-python/SKILL.md | Python 图表 |
| peer-review | skills/peer-review/SKILL.md | 自审检查 |

## 使用方式

1. 用户提出论文写作任务
2. 调用 `using-research-writing` 技能确定流程
3. 中型或整篇任务先调用 `paper-orchestration`
4. 按技能指引完成头脑风暴、证据映射、章节写作和验证

## 核心规则

- 任何写作任务前必须完成头脑风暴
- 中型任务必须有任务包、两阶段 review 和 capability-use audit
- 引言和相关工作必须先完成 evidence map
- skill 改造后运行 `scripts/check_skill_integrity.ps1`
- 稿件交付前运行 `scripts/research_quality_gate.ps1 -ProjectPath <paper-project>`
- 必须创建 plan/ 目录记录项目信息
- 每章写完必须让用户确认
- 绝不编造文献
