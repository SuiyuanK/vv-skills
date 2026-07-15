# 模块调用指引（执行门禁版）

本文档用于保证 AI 在论文任务里“先对齐、再计划、后执行、可追踪”。

## 一、任务前门禁（重中之重）

### 1.1 先讨论后执行

任何实质任务开始前，先确认：
1. 本轮目标是什么。
2. 输出文件是什么。
3. 截止时间和格式约束是什么。

### 1.2 自动处理 plan（用户不提也要做）

1. 若 `plan/` 不存在：立即创建并初始化模板文件。
2. 若已存在：先读取 `project-overview.md`、`progress.md`、`notes.md`、`stage-gates.md`。
3. 执行前写入本轮任务卡，执行后回写结果。
4. 自动初始化命令按系统选择：
- macOS/Linux：`bash research-writing-skill/scripts/init_plan.sh`
- Windows PowerShell：`powershell -ExecutionPolicy Bypass -File research-writing-skill/scripts/init_plan.ps1`

### 1.3 例外场景

仅当用户是“一次性简短问答”（例如术语解释）时可不建 plan。

## 二、快速决策树

```text
用户需求
    │
    ├─ 是一次性小问题？
    │   └─ 是 → 直接回答
    │
    ├─ 是持续写作/修改/翻译/画图任务？
    │   └─ 是 → 先执行门禁（讨论 + plan）
    │
    ├─ 需要全流程规划、阶段推进或投稿准备？
    │   └─ workflow-lifecycle（先更新 stage-gates）
    │
    ├─ 需要写正文？
    │   ├─ 工科/理科 → writing-core + figures-python（按需）
    │   ├─ 文科/社科 → writing-core + writing-humanities
    │   ├─ 医学/生物 → writing-core + writing-medical
    │   └─ 法学 → writing-core + writing-law
    │
    ├─ 需要文献综述？
    │   └─ literature-review
    │
    ├─ 需要翻译/润色/去AI化？
    │   └─ prompts-collection
    │
    ├─ 需要自查或投稿前检查？
    │   └─ peer-review
    │
    ├─ 需要统计分析？
    │   └─ statistical-analysis
    │
    ├─ 需要画图？
    │   ├─ 数据图 → figures-python
    │   └─ 流程图/结构图 → figures-diagram
    │
    └─ 需要安装/修复Python环境？
        └─ environment-setup（必须先做系统识别）
```

## 三、模块组合建议

### 场景0：整篇论文从选题做到投稿

1. `workflow-lifecycle.md`
2. `writing-core.md`
3. 学科专项模块（按学科）
4. `literature-review.md` + `peer-review.md`（按阶段调用）

### 场景1：本科论文持续写作

1. `writing-core.md`
2. 学科专项模块（如 `writing-humanities.md`）
3. `literature-review.md`（按需）
4. `peer-review.md`（定期自查）

### 场景2：用户要求“帮我画图”

1. `environment-setup.md`（先确保环境）
2. `figures-python.md`
3. 回写 `plan/progress.md`

### 场景3：投稿前总审

1. `writing-core.md`
2. `prompts-collection.md`
3. `peer-review.md`

## 四、执行完成判定

满足以下条件才算完成一轮任务：
1. 目标输出已生成。
2. 输出符合排版与去AI化规则。
3. `plan/progress.md` 已更新。
4. 关键约束或偏好已写入 `plan/notes.md`。
5. `plan/stage-gates.md` 已更新。

## 五、常见失效点

1. 只回答内容，不更新 plan。
2. 直接开始长篇生成，未先确认任务边界。
3. 没有区分系统就给安装命令。
4. 正文中出现大量加粗和列表。

遇到上述情况，优先回到“任务前门禁”重新执行。
