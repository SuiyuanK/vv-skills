---
name: dsh-pet-taskbar-hide
description: >-
  Hide the dsh-pet desktop pet window from the GNOME/other Linux taskbar, Dock
  or Dash while keeping the tray icon, the pet rendering and click-through, and
  make that fix survive GNOME ignoring Electron's skipTaskbar hint. Use when the
  dsh-pet pet shows a stray dock/taskbar button (tooltip like "dsh-pet 桌宠（桌面模式）"),
  when the user wants only the tray icon, when the fix was lost after upgrading
  or reinstalling dsh-pet, or when another Electron app on XWayland keeps a
  taskbar entry despite skipTaskbar: true. Do not use for missing menu entries,
  for DSH web launcher/tray setup, or for apps without an Electron/X11 handle.
---

# Hide the dsh-pet pet window from the taskbar

The goal is one visible surface per control: the pet on the desktop, the tray
icon for menu and exit. The taskbar/Dock entry is a leftover WM hint, not a
launcher problem.

## Why the plain setting is not enough

- `dsh-pet` runs an Electron helper that creates the pet window with
  `skipTaskbar: true` (`runtime/electron-helper/main/windows.js`,
  `windowOptions`).
- Electron maps `skipTaskbar` to the EWMH `_NET_WM_STATE_SKIP_TASKBAR` hint on
  Linux, but only once. GNOME Shell appends the Dock entry when the window is
  mapped, and `showInactive()` can land after the hint was consumed.
- The bundled watchdog `taskbarWatchdogEnabled` is Windows-only:
  `shouldRunTaskbarWatchdog(platform) = enabled && platform === 'win32'`, so
  nothing re-asserts the hint on Linux.
- GNOME has no KWin-style window rules, no per-app "hide from dock" setting, and
  `favorite-apps` is unrelated. Do not chase `.desktop` files or
  `StartupWMClass` for this symptom; the Dock entry comes from the live window.

Therefore the durable fix re-asserts `_NET_WM_STATE_SKIP_TASKBAR` from inside
the helper, after the window is mapped.

## Rules

- Diagnose read-only first (Step 1). Only patch after the user confirms the
  problem window is the pet (the tooltip/title `dsh-pet 桌宠（桌面模式）` is the
  proof) and agrees to a local patch.
- Never hard-code an X11 window id or PID: the pet window id changes on every
  helper restart.
- Never modify `~/.dsh/AGENTS.md`, the pet config (`~/.dsh/dsh-pet/main-config.jsonc`)
  or DSH desktop preferences for this fix; the config layer has no taskbar key.
- `~/.dsh/profiles/<profile>/node_modules/dsh-pet/` is **replaced on upgrade or
  reinstall**. Say so when patching, and keep the restore path one command long.
- Do not restart `dsh web` if killing the helper is enough; the helper respawns.

## Step 1 — Identify the window (read-only)

The pet is forced onto XWayland (`electron --ozone-platform=x11 ... electron-helper/main.js`):

```bash
pgrep -af 'runtime/electron-helper/main.js'          # helper PID
xprop -root _NET_CLIENT_LIST                        # all X11 client windows
```

For each id, look for the pet by name, then read its state:

```bash
for w in $(xprop -root _NET_CLIENT_LIST | grep -o '0x[0-9a-f]*'); do
  n=$(xprop -id "$w" _NET_WM_NAME 2>/dev/null)
  case "$n" in *dsh-pet*) echo "$w $n"; xprop -id "$w" _NET_WM_STATE _NET_WM_WINDOW_TYPE ;; esac
done
```

Expected when the fix is missing: `_NET_WM_STATE(ATOM) = _NET_WM_STATE_ABOVE`.
Expected when it works: `_NET_WM_STATE_SKIP_TASKBAR, _NET_WM_STATE_ABOVE`.

The bundled scripts do this for you:

```bash
python3 scripts/find_pet_window.py                    # prints id/name/state
python3 scripts/toggle_skip_taskbar.py --add          # one-shot hint, reversible
python3 scripts/toggle_skip_taskbar.py --remove       # undo a one-shot test
```

## Step 2 — Confirm the symptom (one-shot, reversible)

Before patching, prove that the hint actually removes the Dock entry on this
distro/WM pair:

1. `python3 scripts/toggle_skip_taskbar.py --add`
2. Ask the user to look at the Dock/Dash and answer.
3. If the icon is gone, keep going; if it is still there, stop and report that
   the WM/Shell ignores the hint — the remaining option is a Shell extension,
   which is out of scope here.
4. Only after confirming, install the persistent patch (Step 3). `--remove`
   reverts the one-shot test.

## Step 3 — Install the persistent patch

```bash
python3 scripts/install_pet_taskbar_patch.py --profile web          # dry run, prints the plan
python3 scripts/install_pet_taskbar_patch.py --profile web --apply  # writes + syntax check
```

It is idempotent: it never overwrites an existing `pet-taskbar-suppress.js`,
and it skips a `main.js` that already carries the `[local-patch]` markers.
Details of what is written: [references/patch.md](references/patch.md).

Why this shape:

- The module deliberately uses **no Electron API** — only
  `node:child_process` — so it can be syntax-checked and activated outside
  Electron, and a missing `require('electron')` can never break helper startup.
- It runs the X11 probe on a 1 s interval and exits immediately when the pet
  already carries the atom (a few ms, no output). This covers window remap,
  display/workspace rebuilds and helper restarts without tracking window state.
- Every failure (no `DISPLAY`, no `python3`, no `python-xlib`, bad X state) is
  silent by design: the pet must keep working even if the fix cannot apply.
- The probe requires **both** the title `dsh-pet` and `WM_CLASS` containing
  `electron`. A title-only match also hits any browser, editor or chat window
  whose title mentions dsh-pet — confirmed in practice, and it silently marked
  an unrelated window.

## Step 4 — Restart and verify

```bash
kill "$(pgrep -f 'runtime/electron-helper/main.js' | head -1)"   # host respawns it
sleep 8
python3 scripts/find_pet_window.py                              # want SKIP_TASKBAR
```

Then verify all four surfaces:

- [ ] `_NET_WM_STATE` of the pet contains `_NET_WM_STATE_SKIP_TASKBAR`
- [ ] tray icon still present: `busctl --user call org.kde.StatusNotifierWatcher
      /StatusNotifierWatcher org.freedesktop.DBus.Properties Get ss
      org.kde.StatusNotifierWatcher RegisteredStatusNotifierItems` lists an item
      owned by the new helper PID (or the tray menu still opens)
- [ ] pet still renders and animates on the desktop
- [ ] Dock/Dash has no pet entry — **the user must confirm; X11 properties cannot
      prove what GNOME Shell draws**

Do not claim the Dock is fixed on the strength of the atom alone.

## Step 5 — Disable, restore, or re-apply after an upgrade

```bash
DSH_PET_TASKBAR_FIX=0   # export in the environment that launches `dsh web`, then restart the helper
python3 scripts/install_pet_taskbar_patch.py --profile web --revert   # remove patch + markers
```

Upgrade/reinstall of `dsh-pet` wipes `node_modules`, so after upgrading run
Step 1 (expect the atom to be gone) and then Step 3 + Step 4 again.

## Applying the same trick to another Electron app

The symptom generalises: any XWayland Electron window whose `skipTaskbar: true`
is ignored by the Shell. Replace the `'dsh-pet' in name` match in the probe with
the app's window title substring or `WM_CLASS`, and keep the rest of the shape.
Do not run the probe against every window on the display — match narrowly, and
never send state changes to unrelated clients.
