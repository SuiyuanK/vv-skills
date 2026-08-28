# VV Skills

这个仓库用于收录个人可复用的 agent skills、第三方 skill 镜像与自动化工作流，不限定只能用于 Codex。Windows 维护类 skills 重点强调只读诊断、备份和确认门控。

## 个人 Skills

### update-verible

从官方 chipsalliance/verible GitHub Releases 读取全部版本，交互选择 Release，核对实际 Linux x86_64 资产名称，并将 Verible 安装到 ~/.local/bin。

- scripts/update-verible.sh：提供全交互菜单，完成 Release 列举、资产校验、下载、升级、同版本重装、旧版本备份和备份清理。
- 旧的 verible-* 命令在覆盖前备份到 ~/.local/share/verible-backups；清理时输入保留数量、显示删除目标并要求确认。
- 仅支持 Linux x86_64，依赖 bash、curl、git、tar、find 和常用 GNU 工具；网络只访问官方 GitHub 仓库。
- 以普通用户运行，不使用 sudo；临时下载和解压内容写入 /home/vv/TMP/tmp。

### codex-html-mime-fix

诊断并修复 Linux Codex/ChatGPT Desktop 启动后把 text/html 默认程序从 Google Chrome 改成 chatgpt.desktop 的问题。

- scripts/setup-codex-html-fix.sh：安装用户级启动包装器和 ~/.local/share/applications/chatgpt.desktop 覆盖。
- 启动 Codex 后监测 MIME 关联 15 秒，发现变化就恢复为 google-chrome.desktop。
- 依赖 Debian/Ubuntu 的 chatgpt 包布局、Google Chrome、xdg-mime 和 update-desktop-database。
- 只修改用户目录，不使用 sudo；APT 重装或升级通常不会覆盖该用户级修复。

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

### `synopsys-eda-fix`

诊断并修复 Synopsys X-2025.06 EDA 工具在 Linux Mint 22.3（Ubuntu 24.04 基础、glibc 2.39）与 Linux kernel 7.0.0 上的兼容问题，覆盖 VCS、Verdi、Design Compiler、Library Compiler、SpyGlass 和 SCL 2025.03。

主要修复范围：

- 把 Synopsys vendor 脚本的 shebang 统一改为 `#!/bin/bash -h`（230 个 `#!/bin/sh -h` + 39 个实际用 bash 特性的 `#!/bin/sh` 脚本；`/bin/sh` 保持系统默认 dash），并补装 `csh` 前置依赖。
- 为 VCS 链接补充 `--no-as-needed`，修复 `vfs_fopen`、`snps_mem_*` 等 undefined reference。
- 补全 SpyGlass 对 `Linux-7*` 的平台识别，并提供备份、修改和验证脚本。
- 为 Library Compiler 在 glibc 2.39 上的退出阶段崩溃提供结果校验与包装脚本。
- 覆盖 Verdi supplementary post-install 失败以及 FlexLM `lmgrd`/`snpslmd` 的 `/usr/tmp`、CRLF、端口和 systemd 配置问题。
- 严格限定已验证的系统和产品版本；其他发行版、内核或 Synopsys 版本不得直接套用。

### `qqmusic-linux-fix`

诊断并修复官方 QQ 音乐 Electron 客户端在 Ubuntu 26.04、x86_64、Linux kernel 7 环境中启动闪退的问题。

主要安全边界：

- 先通过终端输出区分动态库缺失与 GPU compositor 崩溃，只对已确认的图形栈问题应用启动参数。
- 逐项验证 `--disable-gpu-sandbox` 等候选参数，不把登录或网络告警误判为闪退根因。
- 优先创建用户级 `.desktop` 覆盖，不直接修改系统启动器，使修复可回滚并避免被软件包更新覆盖。

### `nemo-cinnamon-ghostty`

诊断并修复 Cinnamon/Nemo 的“在终端中打开”被现有 Ghostty 窗口工作目录覆盖的问题。

主要安全边界：

- 先核对 Cinnamon terminal 设置、Ghostty single-instance 行为和 wrapper 目标，不把 `xdg-terminal-exec` 的结果直接当作修复依据。
- 仅在目标文件不存在或内容已知时创建、替换用户级 wrapper，并在写入前展示内容、备份与回滚方案。
- wrapper 显式保留 Nemo 传入的当前目录并禁用 Ghostty GTK single-instance；不修改系统 desktop 文件，也不转发不兼容的 `exec-arg`。

### `opencode-wl-clipboard-copy-fix`

诊断并修复 opencode TUI 在 Wayland（CachyOS/Arch，Ptyxis 等 GTK/Qt 终端）下复制失效的问题：界面提示"复制成功"，但系统剪贴板始终没有内容。

- 根因：Wayland 下剪贴板内容由持有者进程实时提供，opencode 通过调用 `wl-copy`（来自 `wl-clipboard` 包）写入剪贴板；系统缺少该工具时复制静默失败，但 TUI 仍显示成功提示。
- 修复：安装 `wl-clipboard` 后**重启 opencode**（剪贴板支持仅在启动时初始化）；`xclip` 仅作 X11 侧诊断可选，opencode 不依赖它。
- 中键粘贴补充：opencode 只写 CLIPBOARD 不写 PRIMARY，中键粘贴需在 `~/.local/bin` 安装 `wl-copy` 双写包装脚本（见 skill 内 `Middle-click paste does not work` 一节）。
- 验证：`wl-paste` 应输出刚复制的文本，`ps aux | grep wl-copy` 应有持有剪贴板的进程（Wayland 正常机制）。
- 依赖：archlinux/cachyos 的 `pacman`；仅安装一个小型包，无源码改动。

### `linux-ext4-superblock-recovery`

安全诊断和恢复无法启动或无法识别的 EXT4 文件系统，覆盖 dracut UUID 超时、超级块校验失败、备用超级块验证，以及 DiskGenius 修改卷标后未同步更新 `metadata_csum` 的实证案例。

主要安全边界：

- 每次启动后按型号、容量、偏移、UUID 和 PARTUUID 重新确认目标；不把 `/dev/nvme0n1p3` 等设备名当作稳定身份。
- 默认只读检查，禁止将 `mkfs`、`e2fsck -y`、`ntfsfix` 或 Windows 分区修复工具用于尚未确认的文件系统。
- 仅在多个超级块结构一致、错误局限于校验和且目录可读时，才允许带撤销文件的最小 `debugfs` 写入。
- 正式修复后必须再次执行 `dumpe2fs`、只读 `e2fsck` 和启动后日志验证。

## 第三方 Skills

### `codex-windows-fast-patch-skill`

诊断和修复 Windows Codex Desktop 的 Fast Mode、插件、浏览器、Computer Use、模型可见性、Provider 会话历史与升级后功能漂移。

- 上游来源：[chen0416ccc-cpu/codex-windows-fast-patch-skill](https://github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill)
- 跟踪分支：上游 `main`
- 当前同步基线：提交 [`c455fc5`](https://github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill/commit/c455fc593d98c72bc6bdb33f928a49e58a857b82)
- 本目录是上游内容在 `vv-skills` 中的已审核镜像，不替代或冒充上游仓库。
- 基线从 `e7f8573` 更新到 `c455fc5`（2026-08-27），覆盖 sky 0.6.16/0.6.17 Computer Use helper 支持、Chrome native-host v2 桌面托管 app-server 条目、Desktop 26.814/26.818 网关匹配、未安装（package-gated）Computer Use 时的续打补丁、本地 marketplace JSON 去除 UTF-8 BOM、staged 包所有权与版本选择、保留本地 skill overlay 的 self-update、0.149 的 reserved marketplace source 策略等变更。
- `vv-skills` 保留本机验证后的安全调整：Provider 历史等数据层修复必须由用户手动关闭和重新打开 Codex，不自动停止或拉起应用；该调整已随本次基线更新重新应用。

主要安全边界：

- 优先执行只读检查和 `-DryRun`，根据证据选择最小修复路径。
- 修改配置、历史数据库或应用包前创建备份，并验证修复后的状态。
- Provider 会话同步不修改 `config.toml`，同时对 SQLite 与会话 JSONL 元数据进行一致性修复。
- Provider 历史等数据层修复由用户手动关闭和重新打开 Codex，不依赖进程路径筛选或自动 AppX 拉起。

### `research-writing-skill`

面向论文、学位论文和研究文章的模块化科研写作 skill 套件，包含头脑风暴、文献综述、证据驱动写作、章节写作、实验结果规划、LaTeX、统计分析、图表和审稿流程。

- 上游来源：[Norman-bury/research-writing-skill](https://github.com/Norman-bury/research-writing-skill)
- 跟踪分支：上游 `main`
- 当前同步基线：提交 [`6f79595`](https://github.com/Norman-bury/research-writing-skill/commit/6f7959554b4614d879d79cb4ece9ed04a7c8a88c)
- 本目录是上游内容在 `vv-skills` 中的镜像，不替代或冒充上游仓库。
- 保留上游的 `LICENSE`、README、多平台配置、模块、脚本和子 skills。

本地修复：

- `hooks/hooks.json` 的 SessionStart 钩子在上游被指向 Windows 批处理 `hooks/run-hook.cmd`（首行 `@echo off`），Linux 下 shell 无法解析，导致每次启动会话报错 `@echo: 未找到命令` 且上下文注入失败。本仓库改为通过 `bash` 显式调用 Bash 脚本 `hooks/session-start` 并赋予其可执行权限；Cursor 版 `hooks-cursor.json` 上游本就用该脚本，不受影响。
- 自 2026-08-18 起 SessionStart 钩子整体禁用：`hooks/hooks.json` 重命名为 `hooks/hooks.json.disabled`（文件保留，bash 修复仍然有效）。原因：该钩子在每次会话启动、`/clear` 和上下文压缩时无条件向上下文注入约 6.4KB 的强制路由指令（`skills/using-research-writing/SKILL.md` 全文），与实际任务无关，并导致小模型（如 deepseek-v4-flash）指令遵循崩溃、输出中英混杂。套件内全部子 skills 及入口 skill 仍可通过 Skill 工具按需调用，功能不受影响。如需恢复自动注入，将文件名改回 `hooks.json` 即可。

### `ppt-master`

将 PDF、DOCX、URL、Markdown 等资料转换为可编辑的 PowerPoint，支持原生形状、图表、表格、模板、演讲者备注、动画和音频旁白工作流。

- 上游来源：[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)
- 跟踪分支：上游 `main`
- 当前同步基线：提交 [`ebd74d1`](https://github.com/hugohe3/ppt-master/commit/ebd74d1f1d61a686f0f80e10abde5029fc4beeca)
- 注意：上游历史已被改写，旧基线 `b87f5f5` 已不可达；本次升级为文件级整目录同步（无法做提交级 diff），当前上游版本为 5.0.0。
- 本目录镜像上游的 `skills/ppt-master/` 可安装 skill，并附带上游 MIT `LICENSE`；不复制网站、示例演示文稿和项目工作区。
- 上游新增了 `.env.example` 配置模板；`requirements.txt` 增加 `PyYAML>=6.0`（模板注册前端解析设计说明时的可选依赖）。
- Python 3.10+ 依赖记录在 `ppt-master/requirements.txt`，应安装到实际执行 skill 脚本的 Python 解释器。

## 本地管理

CC Switch 的规范 skill 目录同时是 `vv-skills` 的本地 Git 工作副本，不需要把 skill 再复制到另一份本地仓库。Linux 下该目录为 `/home/vv/.cc-switch/skills`；Windows 或其他系统应以 CC Switch 的实际配置为准。

Claude、Codex、Cursor、Gemini 等 Agent 使用的 skill 目录及软连接由 CC Switch 管理，不要直接在这些 Agent 目录中新增、修改、删除或重建 skill 和软连接。skill 变更后，通过 CC Switch 刷新配置，并在新任务中确认相应 skill 可以被发现。

`ppt-master` 的 Python 依赖记录在 `ppt-master/requirements.txt`。确认实际执行脚本的 Python 环境后，可在仓库根目录安装：

```shell
python -m pip install -r ./ppt-master/requirements.txt
```

`research-writing-skill` 是包含多个子 skills 的套件，其子目录暴露方式由 CC Switch 配置管理，不要直接修改 Agent 目录中的软连接。

## 第三方 Skill 更新流程

仅在用户明确要求检查或更新第三方 skill 时执行：

1. 在 CC Switch 规范目录检查当前分支、未提交改动以及本地 `main` 与远程 `main` 的同步状态；本地仅落后时先执行 `git pull --ff-only`。
2. 从根目录 `README.md` 读取目标 skill 的上游仓库、跟踪分支和当前同步基线。
3. 将上游内容获取到本次任务工作区的 `./tmp/`，不得写入系统 `/tmp`、`/var/tmp` 或 Agent skill 目录。
4. 比较当前版本与上游版本，检查许可证、敏感信息、文件增删、依赖和本仓库保留的本地调整；不得未经比较直接覆盖。
5. 在 CC Switch 规范目录中完成更新或合并，运行适用的结构验证、脚本测试和核心功能检查。
6. 同步更新本 README 中的用途、依赖、跟踪分支和当前版本标签或提交哈希。
7. 只暂存本次相关文件，提交并直接推送 `main`；推送后再次检查本地、远程、README 和上游基线是否一致。

各第三方 skill 的附加要求：

- `codex-windows-fast-patch-skill`：同步上游可安装 skill 文件集（`SKILL.md`、`agents/`、`scripts/`、`references/` 和 `assets/`），不引入上游仓库级 `AGENTS.md`、README、SECURITY 或 Git 配置文件；不自动调用上游的就地更新脚本，统一通过本节流程审查上游。更新后重新应用和验证 Provider History 安全调整；数据层修复必须由用户手动关闭和重新打开 Codex，不得自动停止或拉起应用。
- `ppt-master`：只同步上游的 `skills/ppt-master/`，保留该目录内的许可证，不复制上游网站、示例项目或其他工作区内容；不得覆盖或提交本机 `.venv`、缓存和生成产物。
- `research-writing-skill`：保留上游许可证、README、多平台配置、模块、脚本和子 skills，并确认 CC Switch 对子 skills 的暴露配置仍然有效。每次更新时检查上游 `hooks/hooks.json` 的 SessionStart 钩子：若上游仍未修复（仍指向 `hooks/run-hook.cmd`），更新后重新应用本仓库的本地修复（见该条目下的"本地修复"说明）；若上游已修复，直接采用上游版本，并移除该条目下对应的"本地修复"说明。无论上游是否修复，更新后都应保持 SessionStart 钩子处于禁用状态（`hooks.json` 保持重命名为 `hooks.json.disabled`），除非用户明确要求恢复自动注入。

## 使用说明

每个 skill 的入口是各自目录下的 `SKILL.md`。配套脚本和参考资料分别位于 `scripts/` 与 `references/`。

这些工具可能涉及本地历史数据库或软件卸载规划。执行任何写入、删除或系统配置变更前，请先核对目标和备份。
