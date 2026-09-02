# GNOME default terminal on CachyOS/Arch

Use this reference only after confirming an active GNOME session. It covers switching the default terminal to Ghostty, binding `Ctrl+Alt+T`, and safely removing an old terminal. The verified environment is CachyOS/Arch with GNOME and Ptyxis or Alacritty being replaced by Ghostty.

## Preconditions and safety

- Require `XDG_CURRENT_DESKTOP` or equivalent session evidence to identify GNOME.
- Change only the relevant `gsettings` keys. Do not modify pacman configuration.
- Before uninstalling a terminal, launch Ghostty and verify the shortcut so the user is not left without a working terminal.
- Commands requiring `sudo` are run by the user in an interactive terminal.

## Inspect current state

```bash
pacman -Qq | grep -i -E "ptyxis|alacritty|kitty|konsole|gnome-terminal|xterm|wezterm|st$|foot"
printf 'DESKTOP=%s\n' "$XDG_CURRENT_DESKTOP"
gsettings get org.gnome.desktop.default-applications.terminal exec
gsettings get org.gnome.desktop.default-applications.terminal exec-arg
gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings
```

Confirm `ghostty` resolves to the intended executable before proposing changes.

## Configure Ghostty

Set the GNOME default terminal:

```bash
gsettings set org.gnome.desktop.default-applications.terminal exec 'ghostty'
gsettings set org.gnome.desktop.default-applications.terminal exec-arg ''
```

GNOME installations using Ptyxis may not expose the older `panel-terminal` key. Use a custom media-key binding for `Ctrl+Alt+T`:

```bash
gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/terminal0/']"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/terminal0/ name "Open Terminal"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/terminal0/ command "ghostty"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/terminal0/ binding "<Ctrl><Alt>t"
```

Before writing, preserve the existing default-terminal and custom-keybinding values so they can be restored. If `terminal0` already contains unrelated user configuration, do not overwrite it; choose an unused entry with the user.

## Verify

Press `Ctrl+Alt+T` and require a Ghostty window. Then inspect:

```bash
gsettings get org.gnome.desktop.default-applications.terminal exec
gsettings get org.gnome.desktop.default-applications.terminal exec-arg
gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings
```

If the shortcut does not refresh, log out and back in. Do not assume `Alt+F2` followed by `r` works on a Wayland GNOME session.

For a file-manager action, invoke **Open in Terminal** and confirm it opens Ghostty in the selected location.

## Optionally remove old terminals

Only after Ghostty and the shortcut have passed verification, inspect reverse dependencies and show the exact packages to be removed. With explicit authorization, the user may run, for example:

```bash
sudo pacman -Rns ptyxis alacritty
```

Do not include a package that is not installed, still required, or not explicitly selected for removal.

`xdg-terminal-exec` is not required for this GNOME configuration path. Its absence does not invalidate the `gsettings` result.
