# Codex Skills

这个仓库收录两个面向 Windows 的个人 Codex skill，重点强调只读诊断、备份和确认门控。

## Skills

### `codex-history-recovery`

安全诊断、恢复、合并和修复 Codex Desktop 本地历史，包括会话、归档、SQLite 元数据、已保存项目与侧边栏标题。

主要安全边界：

- 备份始终按只读来源处理。
- 不覆盖当前账号、配置、新任务或用户主动删除的内容。
- 修改前创建回滚快照，并在数据库操作前后执行完整性检查。
- 不从备份整体恢复 `auth.json`、`config.toml` 等敏感配置。

### `windows-vivado-clean-uninstall`

为 Windows 上的 Vivado/Xilinx 卸载残留诊断和清理规划提供安全工作流。

主要安全边界：

- 默认仅进行只读检查并输出分阶段计划。
- 未经明确授权，不卸载 Vivado、不删除目录、不修改注册表、服务或环境变量。
- 执行任何清理前，先列出精确目标并准备备份。

## 安装

将所需 skill 目录复制到 Codex skills 目录：

```powershell
Copy-Item -Recurse .\codex-history-recovery "$env:USERPROFILE\.codex\skills\codex-history-recovery"
Copy-Item -Recurse .\windows-vivado-clean-uninstall "$env:USERPROFILE\.codex\skills\windows-vivado-clean-uninstall"
```

重新启动 Codex，或开启一个新任务以重新加载 skill。

## 使用说明

每个 skill 的入口是各自目录下的 `SKILL.md`。配套脚本和参考资料分别位于 `scripts/` 与 `references/`。

这些工具可能涉及本地历史数据库或软件卸载规划。执行任何写入、删除或系统配置变更前，请先核对目标和备份。
