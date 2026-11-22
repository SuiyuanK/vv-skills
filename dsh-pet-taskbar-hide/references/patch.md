# What the dsh-pet taskbar patch is

Reference for [SKILL.md](../SKILL.md). Read before hand-editing the helper.

## Paths (Linux)

| Item | Path |
| --- | --- |
| Helper entry | `<dsh-home>/profiles/<profile>/node_modules/dsh-pet/runtime/electron-helper/main.js` |
| Window creation | `.../electron-helper/main/windows.js` (`windowOptions`, `createPetWindow`, `reassertTaskbar`) |
| Taskbar watchdog | `.../electron-helper/taskbar-watchdog.js` (Windows-only by design) |
| Tray | `.../electron-helper/main/tray.js`, `tray-platform.js` |
| Pet config | `<dsh-home>/dsh-pet/main-config.jsonc` (`trayEnabled`, `pets[]`) |
| Helper log | `<dsh-home>/dsh-pet/logs.txt` |

`<dsh-home>` defaults to `~/.dsh`. The helper runs as
`electron --ozone-platform=x11 .../electron-helper/main.js`, so the pet is an
XWayland window even in a Wayland session, with
`WM_CLASS=electron/electron` and a title such as `dsh-pet 桌宠（桌面模式）`.

## Patch content

`pet-taskbar-suppress.js` (new file, no Electron imports):

- `enabled()` — requires `DISPLAY` and `DSH_PET_TASKBAR_FIX !== '0'`.
- `SCRIPT` — an inline python-xlib program that walks the window tree, matches
  windows whose title contains `dsh-pet` **and** whose `WM_CLASS` contains
  `electron`, and sends a root-directed `_NET_WM_STATE` ClientMessage
  (`action=1, atom=_NET_WM_STATE_SKIP_TASKBAR`) only to windows that do not
  already carry the atom.
- `suppressTaskbar()` — runs that program through `execFile('python3', ...)`
  with an 8 s timeout and ignores every error.
- `attach()` — calls `suppressTaskbar()` immediately and then every 1000 ms;
  the returned timer is `unref()`ed so it cannot keep Electron alive.

`main.js` (two marked lines):

1. after `const { createWindows } = require('./main/windows.js');`
   ```js
   // [local-patch] ...升级 dsh-pet 会覆盖本文件，补丁随之失效
   const { attach: attachTaskbarSuppress } = require('./pet-taskbar-suppress.js');
   ```
2. after the `createWindows({ ... });` call
   ```js
   // [local-patch] 窗口显示后补一次「跳过任务栏」提示（Linux 上 Electron 的 skipTaskbar 不够用）
   attachTaskbarSuppress();
   ```

The installer also leaves `main.js.bak-taskbar-patch` next to `main.js` so
`--revert` can restore the original byte-for-byte.

Both revert paths are byte-exact, and the sandbox round trip (apply → revert →
`cmp`) is part of the verification in
[verification.md](verification.md):

- **with backup** — copy `main.js.bak-taskbar-patch` over `main.js`, then
  delete the backup and the module.
- **without backup** (an upgrade kept the markers but dropped the backup) —
  `strip_patch()` deletes each `// [local-patch]` line together with the
  single code line that follows it, by index, and nothing else. It reports
  `removed`; anything other than 4 prints a warning to review the file by hand.
  The two anchors are matched as whole lines, never as substrings, because the
  injected `require` line itself contains `'./pet-taskbar-suppress.js'`.

## Design notes / pitfalls

- **No `require('electron')` in the module.** A module that imports Electron
  throws `Cannot find module 'electron'` when loaded by plain Node, which makes
  it impossible to sanity-check outside the helper and risks a startup crash if
  the import is ever wrong. Interval polling needs no Electron API.
- **Poll instead of tracking window events.** The window is remapped on display
  or workspace changes and the id changes on every helper restart; a 1 s probe
  that exits immediately on an already-marked window costs a few milliseconds.
- **Root-directed ClientMessage only.** Sending the event directly to the pet
  window (`window.send_event`) produced no effect on GNOME Shell; send to the
  root with `SubstructureRedirectMask | SubstructureNotifyMask`, then
  `display.flush()`.
- **Title alone is not enough — always AND with `WM_CLASS`.** A title-only
  match hit the Chrome window whose tab was titled `隐藏 dsh-pet 图标保留托盘图标
  — DeepSeek Harness`: that browser lost its Dock icon *and* could no longer be
  minimised (`SKIP_TASKBAR` removes the taskbar button, so there is nothing to
  click and the Tab switcher no longer lists it). Confirmed on this machine.
- **Removing the atom again needs `source_indication=0`**, i.e.
  `data=(32, [0, SKIP, 0, 0, 0])`. A remove message with `1` (pager/WM source)
  is silently ignored by GNOME Shell, and `window.send_event(...)` without the
  root redirect never takes effect. Use `toggle_skip_taskbar.py --remove`.
- **Editing the module needs a helper restart.** The inline `SCRIPT` string is
  read once when the helper starts; until it is restarted the old title-only
  logic keeps re-applying the atom 1x/s, so a manual cleanup appears to undo
  itself. Restart, then clear leftover atoms from already-open windows.
- **Never match on PID.** PIDs and window ids are fresh per launch; match the
  title substring and confirm with `xprop`.
- **Do not trust the atom as proof for the user.** GNOME Shell may still draw
  something; only the user can confirm the Dock/Dash lost the icon.
- **The tray is independent.** `new Tray(...)` uses StatusNotifierItem through
  the AppIndicator extension; patching windows does not touch it. Verify the
  `RegisteredStatusNotifierItems` list mentions the new helper PID.
