---
name: gnome-default-terminal-ghostty
description: Configure and diagnose the default terminal on a CachyOS/Arch system running the GNOME desktop, including switching the default terminal to Ghostty, binding Ctrl+Alt+T to open it via a custom keybinding, and uninstalling other terminals (Ptyxis, Alacritty) safely. Use when the user wants to change the default terminal app, the terminal shortcut opens the wrong app, or they ask to remove unused terminal packages.
---

# GNOME 默认终端切换 (CachyOS/Arch)

CachyOS 装有 GNOME 桌面时，终端由几个独立的配置点控制，需全部修改才能彻底切换。本项目实际验证环境：CachyOS + GNOME 会话 + Ptyxis → Ghostty。

## Preconditions and safety

- 目标是 Arch 系 (CachyOS) + GNOME 会话；确认 `echo $XDG_CURRENT_DESKTOP` 输出 `GNOME`。
- 只改 gsettings；不修改 pacman 配置。
- 卸载终端前先确认新终端可用，避免无终端可用。
- 需要 sudo 的命令由用户在终端执行，不通过网络或无 tty 环境运行。

## 现状检查

列出已安装的终端与当前配置：

~~~bash
pacman -Qq | grep -i -E "ptyxis|alacritty|kitty|konsole|gnome-terminal|xterm|wezterm|st$|foot"
echo "DESKTOP=$XDG_CURRENT_DESKTOP"
gsettings get org.gnome.desktop.default-applications.terminal exec
gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings
~~~

## 切换默认终端到 Ghostty

1. GNOME 默认终端：

~~~bash
gsettings set org.gnome.desktop.default-applications.terminal exec 'ghostty'
gsettings set org.gnome.desktop.default-applications.terminal exec-arg ''
~~~

2. 绑定 Ctrl+Alt+T 快捷打开（GNOME 的 `panel-terminal` 键只在 GNOME Terminal/GNOME Console 下存在；桌面装有 Ptyxis 时该键不存在，所以用自定义键绑定更通用）：

~~~bash
gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/terminal0/']"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/terminal0/ name "Open Terminal"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/terminal0/ command "ghostty"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/terminal0/ binding "<Ctrl><Alt>t"
~~~

## 验证

先按 `Ctrl+Alt+T`（打开的是 Ghostty 即生效；若无效重启 GNOME shell：`Alt+F2` → 输入 `r` → 回车，或重新登录），再确认：

~~~bash
gsettings get org.gnome.desktop.default-applications.terminal exec   # 期望 'ghostty'
gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings
~~~

## 卸载其他终端

确认剩一个可用终端后：

~~~bash
sudo pacman -Rns ptyxis alacritty
~~~

- `-Rns`：删除包、孤儿依赖与配置文件；不会影响 ghostty。
- 先跑 `ghostty` 确认可用，再执行卸载。

## 注意事项

- `xdg-terminal-exec`（Ptyxis 特有）不提供，缺失是正常的，不影响 gsettings 开关。
- GNOME 下普通"打开终端"请求（如文件管理器中"在终端中打开"）走 `org.gnome.desktop.default-applications.terminal`，第一步生效后即切换。
