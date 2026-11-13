# 第三方 Skills

`vv-skills` 将第三方 skill 作为经过审核的镜像保存。`catalog.json` 是上游仓库、跟踪分支和同步基线的机器可读来源；本文件记录同步边界与必须保留的本地调整。

## 当前基线

本表与 `catalog.json` 的 `upstream` 字段一致；根 README 的第三方基线表由 `scripts/catalog.py --render` 生成，不手工编辑。

| Skill | 上游 | 分支 | 当前基线 | 版本 | 许可证 |
| --- | --- | --- | --- | --- | --- |
| `codex-windows-fast-patch-skill` | [chen0416ccc-cpu/codex-windows-fast-patch-skill](https://github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill) | `main` | [`762c170`](https://github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill/commit/762c170bf5bf9dce1c15363472cf80cc5e4c3ae5) | 上游未单独标记 | 上游未提供 LICENSE（本地自用，再分发前需核实授权） |
| `ppt-master` | [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) | `main` | [`01fe549`](https://github.com/hugohe3/ppt-master/commit/01fe549371b98f44be22cd337bbc911013452f09) | `6.9.0` | MIT |
| `research-writing-skill` | [Norman-bury/research-writing-skill](https://github.com/Norman-bury/research-writing-skill) | `main` | [`6f79595`](https://github.com/Norman-bury/research-writing-skill/commit/6f7959554b4614d879d79cb4ece9ed04a7c8a88c) | `3.1.0` | MIT |

这些目录是上游内容在 `vv-skills` 中的镜像，不替代或冒充上游仓库。

## `codex-windows-fast-patch-skill`

- 同步上游可安装 skill 文件集：`SKILL.md`、`agents/`、`scripts/`、`references/` 和 `assets/`。
- 不引入上游仓库级 `AGENTS.md`、README、SECURITY 或 Git 配置，也不运行上游就地更新器。
- 上游仓库未提供 LICENSE；本仓库仅作本地镜像使用，不对外分发，再分发前需与上游确认授权。
- 保留本机验证后的安全调整：Provider History 等数据层修复由用户手动关闭和重新打开 Codex，不自动停止或拉起应用。
- 本地 `SKILL.md` 用 `## Update Policy` 取代上游 `## Self-Update Preflight`；受 CC Switch 管理的副本不自更新，统一按 `vv-skills` 流程更新。
- 此前基线新增 dots、executor runtime、post-update 验证、project/archive state、remote review 等 references，以及 codex-after-update、model experience repair 等 scripts；新增工具以 PowerShell 与 Node.js 为主，Python 诊断脚本可选。
- 基线 `762c170`：同步 Windows 10 helper 精确哈希档案 `58FFF5E2`（issue #94）、package-backed CUA runtime 诊断、core strict trusted parent 覆盖测试；新增 `scripts/test-node-repl-trusted-coverage.ps1`，同步 2 个 references 与 CUA patch/test 脚本。
- 每次同步后重新检查 Update Policy、Provider History 安全调整、PowerShell/Node 脚本语法、MSIX dry-run 路由和敏感信息。
- 主要依赖 Windows PowerShell、Store/MSIX Codex 与 Node.js；原生远控构建才额外需要 Python、Rust、MSVC 或 Windows SDK。

## `ppt-master`

- 只同步上游 `skills/ppt-master/` 可安装目录并保留其 MIT `LICENSE`。
- 不复制上游网站、示例演示文稿或项目工作区。
- 不覆盖或提交 `.venv`、缓存、生成的项目、预览或临时产物。
- Python 3.10+ 依赖以 `ppt-master/requirements.txt` 为准；Playwright、FFmpeg 和 Pandoc 只用于对应的可选能力。
- 当前基线 v6.9.0；`requirements.txt` 新增可选 OCR 依赖（`rapidocr`、`onnxruntime`），默认注释、不自动安装。
- 基线 `01fe549`：同步 `scripts/source_to_md/web_to_md.py` 的 Windows 图片链接修复（Markdown 链接改用正斜杠；上游 #349）。
- 上游历史曾改写；旧基线 `b87f5f5` 已不可达。比较更新时必须从 `catalog.json` 的当前可达基线开始，不猜测提交祖先关系。

## `research-writing-skill`

- 保留上游 MIT 许可证、README、多平台配置、模块、脚本和子 skills，并在更新后确认 CC Switch 仍能暴露子 skills。
- 上游 `hooks/hooks.json` 曾把 SessionStart 指向 Windows 批处理 `hooks/run-hook.cmd`。Linux 本地修复改为通过 Bash 调用 `hooks/session-start`。
- SessionStart 自动注入当前保持禁用：文件名为 `hooks/hooks.json.disabled`。除非用户明确要求，不恢复自动注入。
- 若上游已正式修复跨平台 hook，采用上游实现并移除过时的本地补丁说明；无论上游是否修复，默认仍保持 SessionStart 禁用。
- 基础脚本使用 Python、`requests` 和 PyMuPDF；科研计算、Jupyter 与 LaTeX 环境按实际工作流选装。

## 更新要求

第三方更新必须遵循 [维护流程](./MAINTENANCE.md)：先读取 `catalog.json` 的基线，在调用工作区的 `./tmp/` 获取上游并逐项比较许可证、文件、依赖、本地修复与敏感信息，验证后同时更新目录、基线和本文件；根 README 基线表由 `scripts/catalog.py --render` 生成。

第三方镜像按上游原样保存：上游文件固有的行尾空白、patch 内容中的空格或文件末尾空行不视为本仓库问题，不为此改写；`git diff --cached --check` 对这类文件告警时，在提交说明中记录例外即可。
