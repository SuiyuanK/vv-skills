# VV Skills

这个仓库保存个人可复用的 agent skills、经过审核的第三方 skill 镜像与配套自动化工作流。它同时是 Linux 上 CC Switch 的规范 skill 目录和 GitHub 仓库 [`SuiyuanK/vv-skills`](https://github.com/SuiyuanK/vv-skills) 的本地工作副本。

所有 active skill 以仓库顶层目录存放，便于 CC Switch 识别、启用并部署到 Codex、Claude Code、opencode、DSH 等 Agent；实际部署范围以 CC Switch 的配置为准。每个 skill 的入口是所在目录下的 `SKILL.md`，其中声明 `name`、`description` 与主流程；详细操作、风险边界和按需加载的参考资料以 skill 目录内的其他文件为准。

## Skill 索引

以下区块由 `catalog.json` 生成，请勿手工编辑表格内容。

<!-- catalog:start -->

当前收录 **17 个 active skills**：**14 个个人**、**3 个第三方**。

### AI 与开发工具

| Skill | 类型 | 平台 | 用途 | 依赖摘要 |
| --- | --- | --- | --- | --- |
| [`codex-history-recovery`](./codex-history-recovery/SKILL.md) | 个人 | Windows | 安全恢复、合并和修复 Windows Codex Desktop 本地历史、SQLite 元数据与项目记录。 | PowerShell、Python |
| [`codex-windows-fast-patch`](./codex-windows-fast-patch-skill/SKILL.md) | 第三方 | Windows | 修复 Windows Codex Desktop 升级后的 Fast Mode、插件、浏览器、Computer Use、模型功能漂移及 Provider 历史/项目归档状态异常。 | PowerShell、Windows Store/MSIX Codex、Node.js、可选 Python/Rust/MSVC/Windows SDK |
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
| [`dsh-desktop-tray-integration`](./dsh-desktop-tray-integration/SKILL.md) | 个人 | Arch/CachyOS、GNOME、Wayland | 为 dsh web 创建 GNOME 桌面快捷方式与顶栏托盘图标：固定端口 launcher、Python Gio SNI/DBusMenu 托盘（双击打开、右键 打开/重启/退出）、symbolic 图标、托盘随服务启停，含验证与回滚。 | DSH 0.2.x（dsh web）、GNOME Shell + AppIndicator 扩展、python3 + PyGObject（gi）、notify-send/xdg-open/ss/gtk-update-icon-cache、ImageMagick 或其他图标缩放工具 |
| [`dsh-pet-taskbar-hide`](./dsh-pet-taskbar-hide/SKILL.md) | 个人 | Arch/CachyOS、GNOME、Wayland | 隐藏 dsh-pet 桌宠的任务栏/仪表盘图标、只保留托盘图标：诊断 XWayland 窗口、一次性验证 _NET_WM_STATE_SKIP_TASKBAR、安装 helper 本地补丁（含语法检查与备份）、升级后重装、回滚，含可复用脚本。 | dsh-pet（Electron 桌面宠物插件，profiles/<profile>/node_modules/dsh-pet）、python3 + python-xlib、xorg-xprop、node（仅用于补丁语法检查）、GNOME Shell + AppIndicator 扩展（保留托盘图标时必需） |
| [`dualboot-vm-launch`](./dualboot-vm-launch/SKILL.md) | 个人 | Arch/CachyOS、GNOME、Linux x86_64、Windows | 默认只读启动另一块实体盘上的双系统，每次只读启动新建写入层。已验证 Arch/CachyOS 宿主用 QEMU/KVM 启动 Windows，以及 Windows 宿主用 QEMU/WHPX 启动 CachyOS。 | Linux：QEMU/KVM、edk2-ovmf、swtpm、UDisks2、util-linux、Linux GNOME 启动器：Zenity、Python 3、PyGObject；剪贴板需 Windows SPICE Guest Tools、Windows：QEMU/WHPX、EDK2 UEFI、Windows PowerShell、Python 3；桌面选择器需 Tkinter，实体盘访问需管理员权限 |
| [`gnome-xwayland-dock-icon-fix`](./gnome-xwayland-dock-icon-fix/SKILL.md) | 个人 | GNOME、Wayland、Linux | 按实测 WM_CLASS 修复 GNOME XWayland 运行图标、重复菜单项和分组，并处理自动生成启动项覆盖修复的问题。 | xorg-xprop、desktop-file-utils |

### 系统恢复

| Skill | 类型 | 平台 | 用途 | 依赖摘要 |
| --- | --- | --- | --- | --- |
| [`linux-ext4-superblock-recovery`](./linux-ext4-superblock-recovery/SKILL.md) | 个人 | Linux | 安全诊断和恢复 EXT4 超级块校验、备用超级块和无法启动问题。 | e2fsprogs、util-linux |
| [`windows-store-service-registration-fix`](./windows-store-service-registration-fix/SKILL.md) | 个人 | Windows | 诊断商城/MSIX 的 0x80073CF6、windows.service 注册拒绝访问与旧版服务残留；按证据备份、条件式清理并验证，案例最终修复待验证。 | Windows PowerShell 5.1 / Appx、sc.exe、reg.exe、系统范围查询和修复需管理员权限 |

### 研究与内容创作

| Skill | 类型 | 平台 | 用途 | 依赖摘要 |
| --- | --- | --- | --- | --- |
| [`ppt-master`](./ppt-master/SKILL.md) | 第三方 | 跨平台 | 生成、重建、编辑和验证可编辑 PowerPoint，支持模板、原生对象、动画、旁白，以及图片生成/OCR 与图片转 PPT 工作流。 | Python 3.10+、requirements.txt、可选 Playwright/FFmpeg/Pandoc、可选 OCR: rapidocr/onnxruntime |
| [`research-writing-assistant`](./research-writing-skill/SKILL.md) | 第三方 | 跨平台 | 提供论文头脑风暴、文献综述、章节写作、LaTeX、统计分析、图表与审稿工作流。 | Python、requests/PyMuPDF、可选科研计算与 LaTeX 环境 |

<!-- catalog:end -->

## 过时归档

以下个人 skill 已按用户要求移入 `archive/`，状态为 `archived`，保留历史记录。

- 2026-11-17 · [`chatgpt-linux-sigchld-fix`](./archive/chatgpt-linux-sigchld-fix/SKILL.md) 和 [`codex-wayland-image-input-fix`](./archive/codex-wayland-image-input-fix/SKILL.md)。记录早期 SIGCHLD 启动包装及图片输入兼容排查。本机对应修复已撤销，当前版本适用性未验证。
- 2026-11-27 · [`ghostty-desktop-integration`](./archive/ghostty-desktop-integration/SKILL.md)。记录 GNOME 旧默认终端设置的撤销、快捷键和 Cinnamon/Nemo 工作目录修复。
- 2026-11-27 · [`qqmusic-linux-fix`](./archive/qqmusic-linux-fix/SKILL.md)。保留 Ubuntu 26.04 官方 QQ 音乐客户端启动闪退的排查和临时启动方案。
- 2026-11-27 · [`gnome51-bibata-cursor-fix`](./archive/gnome51-bibata-cursor-fix/SKILL.md)。保留 GNOME 51.0 的 Bibata SVG 兼容方案。Mutter 51.1 恢复 Xcursor 回退后，本机已切回原版主题。
- 2026-11-27 · [`chatgpt-arch-deb-updater`](./archive/chatgpt-arch-deb-updater/SKILL.md)。保留将官方 ChatGPT/Codex Desktop amd64 deb 构建成 Arch/CachyOS 软件包的流程。
- 2026-11-27 · [`codex-html-mime-fix`](./archive/codex-html-mime-fix/SKILL.md)。保留通过用户级启动器监测并恢复 HTML 默认打开程序的方案。

归档后的停用与部署清理由 CC Switch 管理，不手工修改 Agent 目录或部署链接。

## 第三方上游基线

以下表格由 `catalog.json` 生成，请勿手工编辑；`Skill` 为 catalog 名称，`目录` 为实际 skill 目录。

<!-- third-party:start -->

| Skill | 目录 | 上游 | 分支 | 当前基线 | 版本 | 许可证 |
| --- | --- | --- | --- | --- | --- | --- |
| `codex-windows-fast-patch` | `codex-windows-fast-patch-skill` | [github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill](https://github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill) | `main` | [`14f1875`](https://github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill/commit/14f18754a5323d61a337c877c9ae7dbae85d1675) | 上游未单独标记 | 上游未提供 LICENSE（本地自用；再分发前需核实授权） |
| `ppt-master` | `ppt-master` | [github.com/hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) | `main` | [`63a0367`](https://github.com/hugohe3/ppt-master/commit/63a03673d5c3c928e7f52983a2c8ec65bac30002) | 6.10.0 | MIT |
| `research-writing-assistant` | `research-writing-skill` | [github.com/Norman-bury/research-writing-skill](https://github.com/Norman-bury/research-writing-skill) | `main` | [`6f79595`](https://github.com/Norman-bury/research-writing-skill/commit/6f7959554b4614d879d79cb4ece9ed04a7c8a88c) | 3.1.0 | MIT |

<!-- third-party:end -->

完整同步边界和必须保留的本地调整见 [第三方 Skills](./docs/THIRD_PARTY.md)。

## 收录与维护边界

仓库收录个人 skill 和用户选定的第三方 skill，可限定 Agent、平台或产品版本，不要求全部跨平台。Agent 内置或私有 skill 由官方机制维护，不自动纳入或复制；归属按实际来源判断。

普通读取与使用不触发维护、同步或推送。修改仓库时遵循[维护流程](./docs/MAINTENANCE.md)，同一时间仅一个 Agent 写入；部署通过 CC Switch，不手工复制或建链。跨平台支持按实际验证范围登记，不可访问的设备或部署明确标为未验证。

## 使用方式

- 通过 Agent 的 skill 发现机制按名称或任务语义调用。
- CC Switch 负责选择哪些 skill 暴露给各 Agent；不要直接修改 Agent 自身的 skill 目录或软连接。
- 不同 skill 可能限定操作系统、发行版、桌面环境、产品版本或硬件架构，执行前读取对应 `SKILL.md` 并重新核验当前环境。
- 需要 Python 环境的第三方套件使用各自目录中的依赖说明；本地 `.venv/`、缓存和生成产物不进入 Git。

## 维护入口

- [第三方来源、同步基线与本地调整](./docs/THIRD_PARTY.md)
- [目录、更新、归档、验证与发布流程](./docs/MAINTENANCE.md)
- 机器可读目录：[catalog.json](./catalog.json)，历史目录/入口名称差异通过 `naming_exception` 登记，不自动改名。

更新目录、README 索引与第三方基线表：

```bash
python3 scripts/catalog.py --render
python3 scripts/catalog.py --check
python3 scripts/validate_skills.py
```

Windows 使用 PowerShell，将示例中的 `python3` 替换为 `py -3` 或 `python`。`catalog.py` 仅依赖 Python 标准库；`validate_skills.py` 在未安装 PyYAML 时自动降级为最小 frontmatter 校验。

## 仓库结构

```text
skill-name/
├── SKILL.md
├── agents/            # 可选：Agent 元数据（如 openai.yaml）
├── scripts/           # 可选：确定性工具
├── references/        # 可选：按场景加载的详细说明
├── assets/            # 可选：输出所需资源
├── LICENSE            # 第三方按需保留上游许可证
└── requirements.txt   # 可选：Python 依赖

catalog.json              # 目录元数据源
scripts/catalog.py        # 目录校验、README 索引与第三方基线生成
scripts/validate_skills.py  # frontmatter 校验
docs/                     # 第三方与维护文档
.github/workflows/        # CI：Linux 与 Windows 校验
```
