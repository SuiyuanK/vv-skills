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

### `vivado-ubuntu26-ncurses-fix`

修复 Xilinx Vivado/Vitis 2025.2.1 在 Ubuntu 26.04（及任何 `ldlibpath.sh` 未识别的发行版）上安装时卡在 "Generating installed device list" 的问题。

- 根因：`ldlibpath.sh` 只识别 Ubuntu 18/20/22/24，26.04 匹配不到，导致 `libncurses.so.5`/`libtinfo.so.5`（存放在 `lib/lnx64.o/Ubuntu/24/`）永远不会进入动态库搜索路径，安装器最后一步的 Vivado 批处理子进程死锁。
- `scripts/vivado_fix_ncurses.sh`：幂等修复脚本，复制库到三个产品的 `lib/lnx64.o/` 根级 + 安装器目录根级（防重装卡死），并在器件列表缺失时自动重新生成。
- `references/diagnosis.md`：完整排查过程记录（症状、根因、诊断命令、验证方法）。

### `linux-ext4-superblock-recovery`

安全诊断和恢复无法启动或无法识别的 EXT4 文件系统，覆盖 dracut UUID 超时、超级块校验失败、备用超级块验证，以及 DiskGenius 修改卷标后未同步更新 `metadata_csum` 的实证案例。

主要安全边界：

- 每次启动后按型号、容量、偏移、UUID 和 PARTUUID 重新确认目标；不把 `/dev/nvme0n1p3` 等设备名当作稳定身份。
- 默认只读检查，禁止将 `mkfs`、`e2fsck -y`、`ntfsfix` 或 Windows 分区修复工具用于尚未确认的文件系统。
- 仅在多个超级块结构一致、错误局限于校验和且目录可读时，才允许带撤销文件的最小 `debugfs` 写入。
- 正式修复后必须再次执行 `dumpe2fs`、只读 `e2fsck` 和启动后日志验证。

### `codex-windows-fast-patch-skill`

诊断和修复 Windows Codex Desktop 的 Fast Mode、插件、浏览器、Computer Use、模型可见性、Provider 会话历史与升级后功能漂移。

- 上游来源：[chen0416ccc-cpu/codex-windows-fast-patch-skill](https://github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill)
- 当前同步基线：上游 `main` 提交 [`5a48446`](https://github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill/commit/5a484467c15df2055f9fc1828b349cde31160a1b)
- 本目录是上游内容在 `vv-skills` 中的已审核镜像，不替代或冒充上游仓库。
- `vv-skills` 保留本机验证后的安全调整：Provider 历史等数据层修复必须由用户手动关闭和重新打开 Codex，不自动停止或拉起应用。

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

### `ppt-master`

将 PDF、DOCX、URL、Markdown 等资料转换为可编辑的 PowerPoint，支持原生形状、图表、表格、模板、演讲者备注、动画和音频旁白工作流。

- 上游来源：[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)
- 当前镜像基线：上游 `main` 提交 [`4343bd8b`](https://github.com/hugohe3/ppt-master/commit/4343bd8bfc91e79dfb9680681a378476cc38a280)
- 本目录镜像上游的 `skills/ppt-master/` 可安装 skill，并附带上游 MIT `LICENSE`；不复制网站、示例演示文稿和项目工作区。
- Python 3.10+ 依赖记录在 `ppt-master/requirements.txt`，应安装到实际执行 skill 脚本的 Python 解释器。

## 安装

将所需 skill 目录复制到 Codex skills 目录：

```powershell
Copy-Item -Recurse .\codex-history-recovery "$env:USERPROFILE\.codex\skills\codex-history-recovery"
Copy-Item -Recurse .\windows-vivado-clean-uninstall "$env:USERPROFILE\.codex\skills\windows-vivado-clean-uninstall"
Copy-Item -Recurse .\vivado-ubuntu26-ncurses-fix "$env:USERPROFILE\.codex\skills\vivado-ubuntu26-ncurses-fix"
Copy-Item -Recurse .\linux-ext4-superblock-recovery "$env:USERPROFILE\.codex\skills\linux-ext4-superblock-recovery"
Copy-Item -Recurse .\codex-windows-fast-patch-skill "$env:USERPROFILE\.codex\skills\codex-windows-fast-patch-skill"
Copy-Item -Recurse .\research-writing-skill "$env:USERPROFILE\.codex\skills\research-writing-skill"
Copy-Item -Recurse .\ppt-master "$env:USERPROFILE\.codex\skills\ppt-master"
```

安装 `ppt-master` 的 Python 依赖：

```powershell
python -m pip install -r "$env:USERPROFILE\.codex\skills\ppt-master\requirements.txt"
```

`research-writing-skill` 是多 skill 套件。安装后还需将其子 skills 暴露给 Codex：

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
New-Item -ItemType Junction `
  -Path "$env:USERPROFILE\.agents\skills\research-writing" `
  -Target "$env:USERPROFILE\.codex\skills\research-writing-skill\skills"
```

重新启动 Codex，或开启一个新任务以重新加载 skill。

## `codex-windows-fast-patch-skill` 更新顺序

仅在明确有更新意图时同步该第三方 skill，固定顺序如下：

1. 从[上游仓库](https://github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill)获取新版到 `.codex/vvwork/upstream-sync/codex-windows-fast-patch-skill/`，不要直接覆盖本机已安装副本。
2. 对比上游与 `vv-skills/codex-windows-fast-patch-skill/`，检查敏感信息、文件范围、脚本变化及本仓库的安全调整。
3. 将确认后的上游内容同步到本仓库，重新应用并验证 Provider 历史修复的手动关闭/重开规则，再提交、审核并合并进 `main`。
4. 仅从已合并的 `vv-skills/main/codex-windows-fast-patch-skill/` 更新 `%USERPROFILE%\.codex\skills\codex-windows-fast-patch-skill`。
5. 在新任务中确认 skill 可被发现，并检查上游基线、仓库副本和本机安装副本一致。

不要采用“上游仓库直接覆盖本机、但不更新 `vv-skills`”的路径；`vv-skills/main` 应作为后续本地更新的已审核来源。

## `ppt-master` 更新顺序

仅在明确有更新意图时同步该第三方 skill，固定顺序如下：

1. 从[上游仓库](https://github.com/hugohe3/ppt-master)获取新版到 `.codex/vvwork/upstream-sync/ppt-master/`，不要直接覆盖本机已安装副本。
2. 对比上游 `skills/ppt-master/` 与 `vv-skills/ppt-master/`，检查许可证、敏感信息、文件范围、依赖清单和 skill 结构。
3. 将确认后的 skill 内容及上游 `LICENSE` 同步到本仓库，验证后提交、审核并合并进 `main`。
4. 使用已合并的 `vv-skills/main/ppt-master/requirements.txt` 更新实际执行脚本的 Python 环境。
5. 仅从已合并的 `vv-skills/main/ppt-master/` 更新本机安装目录，并在新任务中验证发现结果和核心脚本。

不要采用“上游仓库直接覆盖本机、但不更新 `vv-skills`”的路径；`vv-skills/main` 应作为后续本地更新的已审核来源。

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
