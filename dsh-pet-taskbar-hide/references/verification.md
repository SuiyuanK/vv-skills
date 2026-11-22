# Verification and rollback checklist

Reference for [SKILL.md](../SKILL.md).

## Verify

```bash
pgrep -af 'runtime/electron-helper/main.js'   # helper running, note the PID
python3 scripts/find_pet_window.py            # want SKIP_TASKBAR=on
xprop -root _NET_CLIENT_LIST                  # cross-check the same window id
busctl --user call org.kde.StatusNotifierWatcher /StatusNotifierWatcher \
  org.freedesktop.DBus.Properties Get ss \
  org.kde.StatusNotifierWatcher RegisteredStatusNotifierItems
```

| Surface | Pass condition |
| --- | --- |
| Window hint | `_NET_WM_STATE = _NET_WM_STATE_SKIP_TASKBAR, _NET_WM_STATE_ABOVE` |
| Tray | a StatusNotifierItem owned by the current helper PID is listed; menu opens |
| Pet | still visible, animated, click-through intact |
| Dock/Dash | no pet entry — **ask the user**, do not infer from properties |
| Logs | `<dsh-home>/dsh-pet/logs.txt` has no crash after restart |

## Restart the helper

```bash
kill "$(pgrep -f 'runtime/electron-helper/main.js' | head -1)"   # host respawns it
sleep 8
python3 scripts/find_pet_window.py
```

Restarting `dsh web` itself is not required and drops sessions.

## Rollback

| Scope | Command |
| --- | --- |
| Runtime only | `export DSH_PET_TASKBAR_FIX=0` in the environment that starts `dsh web`, then restart the helper |
| Files | `python3 scripts/install_pet_taskbar_patch.py --profile web --revert --apply` |
| After an upgrade | patch is gone with `node_modules`; rerun the installer, then verify |

## Verify the installer itself (no pet window touched)

```bash
# 1. apply to a throwaway copy of an unpatched main.js
cp main.js ./tmp-sandbox/main.js
python3 scripts/install_pet_taskbar_patch.py --helper-dir ./tmp-sandbox --apply
diff main.js ./tmp-sandbox/main.js        # exactly 2 blocks of 2 lines
node --check ./tmp-sandbox/main.js

# 2. revert without a backup -> byte-exact
rm ./tmp-sandbox/main.js.bak-taskbar-patch
python3 scripts/install_pet_taskbar_patch.py --helper-dir ./tmp-sandbox --revert --apply
cmp main.js ./tmp-sandbox/main.js && echo identical

# 3. revert with a backup -> byte-exact
```

`cmp` must print nothing and the revert must not print `warning:`. A
`warning: expected 4 patch lines ... removed 8` means the anchors stopped
matching whole lines (the injected `require` line contains
`'./pet-taskbar-suppress.js'` itself) — fix the script, do not relax the check.

## Known limits

- Requires `python3` with `python-xlib` on every launch; without it the patch
  is a silent no-op (pet unaffected).
- If the WM/Shell ignores `_NET_WM_STATE_SKIP_TASKBAR` for the pet, the only
  remaining route is a GNOME Shell extension — out of scope; stop and report.
- Wayland-native Electron windows have no X11 handle; this patch does nothing
  there (`DISPLAY` unset).
