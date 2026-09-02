# 第三方 Skills

`vv-skills` 将第三方 skill 作为经过审核的镜像保存。`catalog.json` 是上游仓库、跟踪分支和同步基线的机器可读来源；本文件记录同步边界与必须保留的本地调整。

## 当前基线

| Skill | 上游 | 分支 | 当前基线 | 版本 |
| --- | --- | --- | --- | --- |
| `codex-windows-fast-patch-skill` | [chen0416ccc-cpu/codex-windows-fast-patch-skill](https://github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill) | `main` | [`33a88f5`](https://github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill/commit/33a88f5063ac138bf2eedc687263ad56c59b055d) | 上游未单独标记 |
| `ppt-master` | [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) | `main` | [`4e6fdc5`](https://github.com/hugohe3/ppt-master/commit/4e6fdc50136c3aea64a746f6bb4adf1c3305ec87) | `6.1.0` |
| `research-writing-skill` | [Norman-bury/research-writing-skill](https://github.com/Norman-bury/research-writing-skill) | `main` | [`6f79595`](https://github.com/Norman-bury/research-writing-skill/commit/6f7959554b4614d879d79cb4ece9ed04a7c8a88c) | `3.1.0` |

这些目录是上游内容在 `vv-skills` 中的镜像，不替代或冒充上游仓库。

## `codex-windows-fast-patch-skill`

- 同步上游可安装 skill 文件集：`SKILL.md`、`agents/`、`scripts/`、`references/` 和 `assets/`。
- 不引入上游仓库级 `AGENTS.md`、README、SECURITY 或 Git 配置，也不运行上游就地更新器。
- 保留本机验证后的安全调整：Provider History 等数据层修复由用户手动关闭和重新打开 Codex，不自动停止或拉起应用。
- 每次同步后重新检查 Provider History 安全调整、PowerShell 脚本语法、MSIX dry-run 路由和敏感信息。
- 主要依赖 Windows PowerShell 与 Store/MSIX Codex；原生远控构建才额外需要 Python、Rust、MSVC 或 Windows SDK。

## `ppt-master`

- 只同步上游 `skills/ppt-master/` 可安装目录并保留其 MIT `LICENSE`。
- 不复制上游网站、示例演示文稿或项目工作区。
- 不覆盖或提交 `.venv`、缓存、生成的项目、预览或临时产物。
- Python 3.10+ 依赖以 `ppt-master/requirements.txt` 为准；Playwright、FFmpeg 和 Pandoc 只用于对应的可选能力。
- 上游历史曾改写；旧基线 `b87f5f5` 已不可达。比较更新时必须从 `catalog.json` 的当前可达基线开始，不猜测提交祖先关系。

## `research-writing-skill`

- 保留上游许可证、README、多平台配置、模块、脚本和子 skills，并在更新后确认 CC Switch 仍能暴露子 skills。
- 上游 `hooks/hooks.json` 曾把 SessionStart 指向 Windows 批处理 `hooks/run-hook.cmd`。Linux 本地修复改为通过 Bash 调用 `hooks/session-start`。
- SessionStart 自动注入当前保持禁用：文件名为 `hooks/hooks.json.disabled`。除非用户明确要求，不恢复自动注入。
- 若上游已正式修复跨平台 hook，采用上游实现并移除过时的本地补丁说明；无论上游是否修复，默认仍保持 SessionStart 禁用。
- 基础脚本使用 Python、`requests` 和 PyMuPDF；科研计算、Jupyter 与 LaTeX 环境按实际工作流选装。

## 更新要求

第三方更新必须遵循 [维护流程](./MAINTENANCE.md)：先读取 `catalog.json` 的基线，在调用工作区的 `./tmp/` 获取上游并逐项比较许可证、文件、依赖、本地修复与敏感信息，验证后同时更新目录、基线、本文件和根 README 索引。
