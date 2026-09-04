# VV Skills

这个仓库保存个人可复用的 agent skills、经过审核的第三方 skill 镜像与配套自动化工作流。它同时是 Linux 上 CC Switch 的规范 skill 目录和 GitHub 仓库 [`SuiyuanK/vv-skills`](https://github.com/SuiyuanK/vv-skills) 的本地工作副本。

所有 active skill 保持为顶层目录，便于 CC Switch 发现并部署到 Codex、Claude、opencode 等 Agent。每个 skill 的入口是目录内的 `SKILL.md`；详细操作、风险边界和按需参考资料以该目录为准。

## Skill 索引

以下区块由 `catalog.json` 生成，请勿手工编辑表格内容。

<!-- catalog:start -->

当前收录 **17 个 active skills**：**14 个个人**、**3 个第三方**。

### AI 与开发工具

| Skill | 类型 | 平台 | 用途 | 依赖摘要 |
| --- | --- | --- | --- | --- |
| [`chatgpt-arch-deb-updater`](./chatgpt-arch-deb-updater/SKILL.md) | 个人 | Arch/CachyOS、Linux x86_64 | 把 OpenAI 官方 ChatGPT/Codex Desktop amd64 deb 构建为可验证的 Arch/CachyOS 软件包。 | bash、curl、libarchive/bsdtar、pacman/makepkg |
| [`codex-history-recovery`](./codex-history-recovery/SKILL.md) | 个人 | Windows | 安全恢复、合并和修复 Windows Codex Desktop 本地历史、SQLite 元数据与项目记录。 | PowerShell、Python |
| [`codex-html-mime-fix`](./codex-html-mime-fix/SKILL.md) | 个人 | Ubuntu/Linux | 修复 Linux Codex/ChatGPT Desktop 启动后抢占 text/html 默认程序的问题。 | Google Chrome、xdg-utils、desktop-file-utils |
| [`codex-windows-fast-patch`](./codex-windows-fast-patch-skill/SKILL.md) | 第三方 | Windows | 修复 Windows Codex Desktop 升级后的 Fast Mode、插件、浏览器、Computer Use 与模型功能漂移。 | PowerShell、Windows Store/MSIX Codex、可选 Python/Rust/MSVC |
| [`opencode-wl-clipboard-copy-fix`](./opencode-wl-clipboard-copy-fix/SKILL.md) | 个人 | Arch/CachyOS、Wayland | 修复 opencode 等终端程序在 Wayland 下提示复制成功但剪贴板未更新的问题。 | wl-clipboard、可选 xclip |

### EDA/FPGA

| Skill | 类型 | 平台 | 用途 | 依赖摘要 |
| --- | --- | --- | --- | --- |
| [`matlab-cachyos-fix`](./matlab-cachyos-fix/SKILL.md) | 个人 | Arch/CachyOS、GNOME、Linux x86_64 | 修复 MATLAB R2025b 在 CachyOS/Arch 上的安装器、GCC 13、MEX、GNOME 菜单/Dock 图标、外部浏览器及新版 glibc 退出崩溃问题。 | binutils/systemd 诊断工具、xorg-xprop、desktop-file-utils、util-linux、可选 devtools/GCC 13/gperftools |
| [`synopsys-eda-fix`](./synopsys-eda-fix/SKILL.md) | 个人 | Arch/CachyOS、Ubuntu/Linux、Linux x86_64 | 诊断并修复 Synopsys X-2025.06 工具链在新 glibc 与 Linux 7.x 上的兼容问题。 | tcsh/csh、bc、time、numactl、libselinux、可选 GCC 13 |
| [`update-verible`](./update-verible/SKILL.md) | 个人 | Linux x86_64 | 从 chipsalliance/verible 官方 Releases 选择、安装、回退和清理 Linux x86_64 版本。 | bash、curl、git、tar、findutils |
| [`vivado-ubuntu26-ncurses-fix`](./vivado-ubuntu26-ncurses-fix/SKILL.md) | 个人 | Ubuntu/Linux、Linux x86_64 | 修复 Vivado/Vitis 2025.2.1 在 Ubuntu 26.04 上因 ncurses 搜索路径导致的安装卡死。 | Vivado/Vitis 2025.2.1 自带兼容库、bash |
| [`windows-vivado-clean-uninstall`](./windows-vivado-clean-uninstall/SKILL.md) | 个人 | Windows | 为 Windows Vivado/Xilinx 卸载残留提供只读审计、确认门控和可回滚清理流程。 | PowerShell |
| [`xilinx-vitis-desktop-launch-fix`](./xilinx-vitis-desktop-launch-fix/SKILL.md) | 个人 | Arch/CachyOS、GNOME、Linux x86_64 | 修复 Vitis CLI 菜单启动后立即退出，以及 Model Composer 只启动后台 MATLAB 而不显示窗口的问题。 | desktop-file-utils、util-linux/script、GNOME、可用终端模拟器 |

### Linux 桌面与应用

| Skill | 类型 | 平台 | 用途 | 依赖摘要 |
| --- | --- | --- | --- | --- |
| [`ghostty-desktop-integration`](./ghostty-desktop-integration/SKILL.md) | 个人 | Arch/CachyOS、GNOME、Cinnamon/Nemo | 配置和修复 GNOME 或 Cinnamon/Nemo 环境中的 Ghostty 默认终端与工作目录集成。 | Ghostty、gsettings、GNOME 或 Cinnamon/Nemo |
| [`gnome-xwayland-dock-icon-fix`](./gnome-xwayland-dock-icon-fix/SKILL.md) | 个人 | GNOME、Wayland、Linux | 按实测 WM_CLASS 修复 GNOME XWayland 应用图标和分组，并处理自动生成启动项反复覆盖修复的问题。 | xorg-xprop、desktop-file-utils |
| [`qqmusic-linux-fix`](./qqmusic-linux-fix/SKILL.md) | 个人 | Ubuntu/Linux、Linux x86_64 | 诊断并修复官方 QQ 音乐 Electron 客户端在 Ubuntu 26.04 图形栈上的启动闪退。 | 官方 QQ 音乐客户端、可选 desktop-file-utils |

### 系统恢复

| Skill | 类型 | 平台 | 用途 | 依赖摘要 |
| --- | --- | --- | --- | --- |
| [`linux-ext4-superblock-recovery`](./linux-ext4-superblock-recovery/SKILL.md) | 个人 | Linux | 安全诊断和恢复 EXT4 超级块校验、备用超级块和无法启动问题。 | e2fsprogs、util-linux |

### 研究与内容创作

| Skill | 类型 | 平台 | 用途 | 依赖摘要 |
| --- | --- | --- | --- | --- |
| [`ppt-master`](./ppt-master/SKILL.md) | 第三方 | 跨平台 | 生成、重建、编辑和验证可编辑 PowerPoint，支持模板、原生对象、动画与旁白。 | Python 3.10+、requirements.txt、可选 Playwright/FFmpeg/Pandoc |
| [`research-writing-assistant`](./research-writing-skill/SKILL.md) | 第三方 | 跨平台 | 提供论文头脑风暴、文献综述、章节写作、LaTeX、统计分析、图表与审稿工作流。 | Python、requests/PyMuPDF、可选科研计算与 LaTeX 环境 |

<!-- catalog:end -->

## 使用方式

- 通过 Agent 的 skill 发现机制按名称或任务语义调用。
- CC Switch 负责选择哪些 skill 暴露给各 Agent；不要直接修改 Agent 自身的 skill 目录或软连接。
- 不同 skill 可能限定操作系统、发行版、桌面环境、产品版本或硬件架构，执行前读取对应 `SKILL.md` 并重新核验当前环境。
- 需要 Python 环境的第三方套件使用各自目录中的依赖说明；本地 `.venv/`、缓存和生成产物不进入 Git。

## 维护入口

- [第三方来源、同步基线与本地调整](./docs/THIRD_PARTY.md)
- [目录、更新、归档、验证与发布流程](./docs/MAINTENANCE.md)
- 机器可读目录：[catalog.json](./catalog.json)

更新目录或 README 索引：

```bash
python scripts/catalog.py --render
python scripts/catalog.py --check
```

## 仓库结构

```text
skill-name/
├── SKILL.md
├── scripts/       # 可选：确定性工具
├── references/    # 可选：按场景加载的详细说明
└── assets/        # 可选：输出所需资源

catalog.json       # 目录元数据源
scripts/catalog.py # 目录校验与 README 索引生成
docs/              # 第三方与维护文档
```
