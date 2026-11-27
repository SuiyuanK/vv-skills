---
name: gnome51-bibata-cursor-fix
description: Diagnose and repair Bibata cursor themes reverting to Adwaita on GNOME 51 desktop, top bar, or system surfaces while third-party apps retain the selected theme. Builds a user-local SVG companion from official Bibata artwork while retaining legacy Xcursors. Not for mouse input failure or unrelated desktop environments.
---

# GNOME 51 Bibata 指针兼容修复

适用于“第三方应用指针正常，桌面/顶部栏却变回默认”的样式问题。先区分指针样式与鼠标移动、点击失效；后者不使用本流程。

## 先确认原因

读取会话类型、GNOME Shell 版本、已选主题和主题目录：

```bash
printenv XDG_CURRENT_DESKTOP XDG_SESSION_TYPE
gnome-shell --version
gsettings get org.gnome.desktop.interface cursor-theme
gsettings get org.gnome.desktop.interface cursor-size
journalctl -b _COMM=gnome-shell --no-pager -n 150
```

检查实际主题的 `cursors/` 和 `cursors_scalable/`，以及 `default`、`wait`、`no-drop` 等文件。GNOME 51 的 Shell 使用 SVG 指针；只有旧 Xcursor 文件的主题会出现桌面回退，而仍使用旧格式的客户端正常。日志可能出现 `Could not load cursor 'default': No file found`。主题设置正确且文件存在时，不要反复切换主题、修改 `/usr/share/icons/default` 或先归因于 DING 扩展。

此结论已在 CachyOS、GNOME Shell 51.0、Mutter 51.0、Wayland、Bibata 2.0.7 环境中获得版本、目录和日志支持。对其他版本重新核验；若已经有有效的 `cursors_scalable`，继续查主题搜索路径/渲染错误，不套用此转换。

## 依赖与来源

需要 Python 3.11+（标准库 tomllib）、`rsvg-convert`（librsvg，用于逐帧验证）、`gsettings`，以及获取官方图稿的 HTTPS 网络。无需 npm、yarn、图稿生成模型或额外 Python 包。缺少依赖时说明用途、影响和安装方法，未经用户确认不安装。

这是个人排障 skill，不是第三方 skill 镜像。生成的主题使用 GPL-3.0 的官方 Bibata 图稿，必须携带许可证与来源记录：

- 上游：[ful1e5/Bibata_Cursor](https://github.com/ful1e5/Bibata_Cursor)，跟踪分支 `main`。
- 本流程复现基线：`v2.0.7`，提交 `35ccfe209a808e40d6c2ca60a46cbe4faf68b690`。
- [Bibata SVG 兼容问题 #188](https://github.com/ful1e5/Bibata_Cursor/issues/188)。
- [GNOME 51 SVG 指针加载代码](https://github.com/GNOME/gnome-shell/blob/51.0/src/st/st-cursor.c)与[元数据样例](https://github.com/GNOME/gnome-shell/blob/51.0/data/cursor-theme/icons/Adwaita/cursors_scalable/default/metadata.json)。

优先检查上游是否已提供与现有样式一致的双格式版本；若有，核验来源与文件后使用。否则按下面的已验证基线构建。升级基线前比较配置、图稿结构与热点，不直接用最新 main 覆盖用户主题。

## 获取并构建

把会话起始工作目录作为工作区根，所有下载、解压、缓存、日志和预览放在其 `tmp/` 的本次专用目录中。用完整提交获取官方 codeload 压缩包，使用 Python `tarfile.extractall(..., filter="data")` 安全解压，不执行下载的上游脚本。保存压缩包 SHA-256 供溯源；它本身不是官方签名证明。

脚本接受已解压源码和现有旧格式主题，不联网、不安装、不修改桌面设置。将下列路径替换为本次实测绝对路径：

```bash
python -B /home/vv/.cc-switch/skills/gnome51-bibata-cursor-fix/scripts/build_bibata_svg.py   --source-root /WORKSPACE/tmp/TASK/Bibata_Cursor-35ccfe209a808e40d6c2ca60a46cbe4faf68b690   --legacy-theme /usr/share/icons/Bibata-Modern-Classic   --workspace-root /WORKSPACE   --variant Bibata-Modern-Classic   --commit 35ccfe209a808e40d6c2ca60a46cbe4faf68b690 --ref v2.0.7
```

脚本读取 `render.json` 的颜色替换和 `configs/normal/x.build.toml` 的热点、别名与帧延迟，生成 `Bibata-Modern-Classic-GNOME51`。当前脚本限定 Modern Classic/Ice/Amber；Original 和 Right 版本需另行核验配置，不能随意替换参数。

关键格式：每种指针放在 `cursors_scalable/名称/`，`metadata.json` 是帧数组，含 filename、hotspot_x/y、nominal_size、delay。256×256 原稿的 nominal_size 是 256，GNOME 按用户指针大小缩放；不要把它误写成 24。保留上游 40ms 动画延迟。Bibata 动画目录可能是软链接，`Path.rglob()` 默认不递归这些目录；直接在 `svg/modern/wait`、`left_ptr_watch` 中 `glob()`。补齐 `all-resize -> move`，复制旧 `cursors/` 保持旧客户端兼容。

## 安装、验证与回滚

记录原主题名和大小。构建成功后，检查脚本报告和 SOURCE.json；仅在用户的修复请求已授权范围内，将产物复制到 `~/.local/share/icons/产物名称` 并应用：

```bash
gsettings set org.gnome.desktop.interface cursor-theme 'Bibata-Modern-Classic-GNOME51'
gsettings get org.gnome.desktop.interface cursor-theme
```

目标目录已存在时先比较，不覆盖未知内容。安装时保留相对软链接，不修改系统主题、不手动改 Agent skill 目录。正常无需注销；不要在 Wayland 强制重启 Shell。

脚本会用本机 librsvg 渲染所有帧并检查 36 种所需形状、别名、元数据和热点范围；基线为 162 帧、146 个名称/别名。再查看应用时刻之后的 GNOME Shell 日志，检查新的指针加载错误。请用户将指针移到桌面、顶部栏、窗口边缘和应用中，并验证点击位置、等待动画。配置读回与渲染成功仅证明静态验证，不能替代真实桌面视觉确认；尚未确认时如实说明。

回滚只需将 cursor-theme 设回记录的原名称（本案例为 `Bibata-Modern-Classic`），原主题未被修改。若要清理，只删除确认为本次创建的兼容主题和临时目录；未获删除请求时保留。
