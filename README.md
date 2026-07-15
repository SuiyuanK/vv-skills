# VV Skills

这个仓库用于收录个人可复用的 agent skills、第三方 skill 镜像与自动化工作流，不限定只能用于 Codex。Windows 维护类 skills 重点强调只读诊断、备份和确认门控。

## Skills

### `codex-history-recovery`

安全诊断、恢复、合并和修复 Codex Desktop 本地历史，包括会话、归档、SQLite 元数据、已保存项目与侧边栏标题。

主要安全边界：

- 备份始终按只读来源处理。
- 不覆盖当前账号、配置、新任务或用户主动删除的内容。
- 修改前创建回滚快照，并在数据库操作前后执行完整性检查。
- 不从备份整体恢复 `auth.json`、`config.toml` 等敏感配置。
- 数据修复前由用户手动关闭 Codex，验证完成后由用户手动重新打开；脚本不自动结束或拉起 Desktop。

### `windows-vivado-clean-uninstall`

为 Windows 上的 Vivado/Xilinx 卸载残留诊断和清理规划提供安全工作流。

主要安全边界：

- 默认仅进行只读检查并输出分阶段计划。
- 未经明确授权，不卸载 Vivado、不删除目录、不修改注册表、服务或环境变量。
- 执行任何清理前，先列出精确目标并准备备份。

### `codex-windows-fast-patch-skill`

诊断和修复 Windows Codex Desktop 的 Fast Mode、插件、浏览器、Computer Use、模型可见性、Provider 会话历史与升级后功能漂移。

主要安全边界：

- 优先执行只读检查和 `-DryRun`，根据证据选择最小修复路径。
- 修改配置、历史数据库或应用包前创建备份，并验证修复后的状态。
- Provider 会话同步不修改 `config.toml`，同时对 SQLite 与会话 JSONL 元数据进行一致性修复。
- Provider 历史等数据层修复由用户手动关闭和重新打开 Codex，不依赖进程路径筛选或自动 AppX 拉起。

### `research-writing-skill`

面向论文、学位论文和研究文章的模块化科研写作 skill 套件，包含头脑风暴、文献综述、证据驱动写作、章节写作、实验结果规划、LaTeX、统计分析、图表和审稿流程。

- 上游来源：[Norman-bury/research-writing-skill](https://github.com/Norman-bury/research-writing-skill)
- 首次镜像基线：上游 `main` 提交 [`6f79595`](https://github.com/Norman-bury/research-writing-skill/commit/6f7959554b4614d879d79cb4ece9ed04a7c8a88c)
- 本目录是上游内容在 `vv-skills` 中的镜像，不替代或冒充上游仓库。
- 保留上游的 `LICENSE`、README、多平台配置、模块、脚本和子 skills。

## 安装

将所需 skill 目录复制到 Codex skills 目录：

```powershell
Copy-Item -Recurse .\codex-history-recovery "$env:USERPROFILE\.codex\skills\codex-history-recovery"
Copy-Item -Recurse .\windows-vivado-clean-uninstall "$env:USERPROFILE\.codex\skills\windows-vivado-clean-uninstall"
Copy-Item -Recurse .\codex-windows-fast-patch-skill "$env:USERPROFILE\.codex\skills\codex-windows-fast-patch-skill"
Copy-Item -Recurse .\research-writing-skill "$env:USERPROFILE\.codex\skills\research-writing-skill"
```

`research-writing-skill` 是多 skill 套件。安装后还需将其子 skills 暴露给 Codex：

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
New-Item -ItemType Junction `
  -Path "$env:USERPROFILE\.agents\skills\research-writing" `
  -Target "$env:USERPROFILE\.codex\skills\research-writing-skill\skills"
```

重新启动 Codex，或开启一个新任务以重新加载 skill。

## `research-writing-skill` 更新顺序

仅在明确有更新意图时同步该第三方套件，固定顺序如下：

1. 从[上游仓库](https://github.com/Norman-bury/research-writing-skill)获取新版到 `.codex/vvwork/upstream-sync/research-writing-skill/`，不要直接覆盖本机已安装副本。
2. 对比上游与 `vv-skills/research-writing-skill/`，检查许可证、敏感信息、文件范围和 skill 结构。
3. 将确认后的上游内容复制到本仓库的 `research-writing-skill/`，提交、审核并合并进 `main`。
4. 仅从已合并的 `vv-skills/main/research-writing-skill/` 更新 `%USERPROFILE%\.codex\skills\research-writing-skill`。
5. 保持 `%USERPROFILE%\.agents\skills\research-writing` 指向本机安装目录的 `skills` 子目录，并在新任务中验证发现结果。

不要采用“上游仓库直接覆盖本机、但不更新 `vv-skills`”的路径；`vv-skills/main` 应作为后续本地更新的已审核来源。

## 使用说明

每个 skill 的入口是各自目录下的 `SKILL.md`。配套脚本和参考资料分别位于 `scripts/` 与 `references/`。

这些工具可能涉及本地历史数据库或软件卸载规划。执行任何写入、删除或系统配置变更前，请先核对目标和备份。
