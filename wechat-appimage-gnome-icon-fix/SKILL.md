---
name: wechat-appimage-gnome-icon-fix
description: Diagnose and fix WeChat AppImage windows showing a generic AppImage icon in the GNOME Dock while the application-menu icon is correct. Use for GNOME/XWayland launcher-to-window matching problems after AppImage integration or reinstallation; do not use for missing menu entries, launch failures, or Flatpak packaging issues.
---

# 微信 AppImage GNOME 图标匹配修复

修复“应用菜单里的微信图标正常，但打开后 GNOME Dock、任务切换器或窗口使用通用 AppImage 图标”的问题。核心是让当前用户的 `.desktop` 启动器匹配运行窗口实际报告的 `WM_CLASS`。

## 安全边界

- 用户只要求诊断时保持只读；获得修复授权后才修改启动器。
- 只修改 `~/.local/share/applications/` 中已确认对应当前 AppImage 的用户级 `.desktop`，不修改 AppImage 内部文件或 `/usr/share/applications/`。
- 不根据 AppImage 文件名、窗口标题或旧安装记录猜测 `StartupWMClass`。
- 重装或重新集成 AppImage 后必须重新发现 `.desktop` 文件；安装器可能改变文件名或去掉先前修复。
- 多个候选启动器无法与 `Exec=` 和当前进程唯一对应时，停止并让用户选择。
- 不为刷新图标强制结束微信；提醒用户先确认无未保存内容并正常退出。在 GNOME Wayland 会话中不要建议 `Alt+F2` → `r`。

## 只读诊断

先确认桌面会话、AppImage、用户启动器和依赖：

```bash
printf 'session=%s desktop=%s display=%s\n' "$XDG_SESSION_TYPE" "$XDG_CURRENT_DESKTOP" "$DISPLAY"
command -v xprop
command -v desktop-file-edit
find "$HOME/.local/share/applications" -maxdepth 1 -type f \
  \( -iname '*wechat*.desktop' -o -iname '*weixin*.desktop' \) -print
find "$HOME/.local/bin" "$HOME/Applications" "$HOME/Downloads" -maxdepth 2 -type f \
  \( -iname '*wechat*.AppImage' -o -iname '*weixin*.AppImage' \) -print 2>/dev/null
```

逐个读取候选启动器的关键字段：

```bash
grep -E '^(Name|Exec|TryExec|Icon|StartupWMClass)=' /path/to/current-wechat.desktop
```

用 `Exec=` / `TryExec=` 与实际 AppImage 路径和运行进程对应。菜单图标正常通常说明 `Icon=` 已能解析，不要先替换图标文件。

让用户打开微信后，读取 XWayland 窗口实际属性：

```bash
for window_id in $(xprop -root _NET_CLIENT_LIST 2>/dev/null | grep -oE '0x[0-9a-f]+'); do
  xprop -id "$window_id" WM_CLASS _NET_WM_NAME 2>/dev/null | tr '\n' ' '
  printf '\n'
done | grep -iE 'wechat|weixin|微信'
```

实测微信 4.1.1 AppImage 输出：

```text
WM_CLASS(STRING) = "wechat", "wechat"
```

第一个字符串是 instance，第二个是 class。这里两者相同；一般应使用已验证能代表主窗口的 class 值，而不是窗口标题“微信”。如果没有窗口结果，先确认微信主窗口已打开且该 AppImage 运行于 XWayland；不要猜值。

## 根因判定

满足以下证据时，可判定为启动器与窗口匹配失败：

- 应用菜单能显示正确微信图标；
- 运行窗口显示通用 AppImage 图标或形成第二个 Dock 项；
- 当前 `.desktop` 的 `Icon=` 正常；
- `.desktop` 缺少 `StartupWMClass`，或其值与实际 `WM_CLASS` 不同。

AppImage 文件名、`.desktop` 文件名和 `WM_CLASS` 不需要相同。GNOME 依靠桌面启动器标识及窗口属性进行分组；缺少可匹配的 `StartupWMClass` 才是本故障的关键。

## 修复

将下面路径替换为本轮动态发现并核对过的当前启动器，将值替换为实测 class：

```bash
desktop_file="$HOME/.local/share/applications/current-wechat.desktop"
desktop-file-edit \
  --set-key=StartupWMClass \
  --set-value=wechat \
  "$desktop_file"
desktop-file-validate "$desktop_file"
update-desktop-database "$HOME/.local/share/applications"
```

`desktop-file-edit` 只设置目标键并保留其他字段。不要把旧安装中的文件名（例如带 `(1)` 的名称）硬编码到新安装。

## 验证

先做静态验证：

```bash
grep '^StartupWMClass=' "$desktop_file"
desktop-file-validate "$desktop_file"
```

然后让用户正常退出微信，从应用菜单重新打开，并检查：

- Dock 与任务切换器显示菜单中相同的微信图标；
- 打开窗口不会生成额外的通用 AppImage Dock 项；
- 原有 `Exec=`、`TryExec=` 和 `Icon=` 没有被改动。

若仍显示旧项，先取消固定旧的通用图标，再从应用菜单启动当前微信并重新固定。仅当重新登录后仍失败，才重新读取当前窗口 `WM_CLASS` 与启动器内容，检查是否选错启动器或 AppImage 集成器再次生成了文件。

## 依赖与已验证环境

- `xprop`（Arch/CachyOS 通常由 `xorg-xprop` 提供）用于读取 XWayland 窗口类。
- `desktop-file-edit`、`desktop-file-validate` 和 `update-desktop-database` 由 `desktop-file-utils` 提供。
- 已验证环境：CachyOS/Arch、GNOME Wayland 会话、XWayland、微信 4.1.1 AppImage。
- 修复只涉及用户级 `.desktop`，不需要 sudo、网络访问或修改系统图标主题。
