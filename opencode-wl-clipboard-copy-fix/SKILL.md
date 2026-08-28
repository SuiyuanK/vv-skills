---
name: opencode-wl-clipboard-copy-fix
description: Fix opencode TUI and other CLI programs silently failing to write to the system clipboard on Wayland (CachyOS/Arch, Ptyxis terminal). Use when opencode shows a "copied" toast but pasting yields nothing, clipboard contents never change, or wl-copy/wl-paste are not installed. Covers diagnosis, installation, restart, and verification.
---

# opencode Wayland Clipboard Fix

opencode's TUI reports "copied" but the system clipboard never gets the text. On Wayland, clipboard content is held by a helper process; opencode shells out to `wl-copy` (from the `wl-clipboard` package) to write it. If `wl-clipboard` is missing, the copy silently fails while the UI still shows success.

## Preconditions and safety

- Target system: CachyOS / Arch Linux with Wayland session (Ptyxis or other GTK/Qt terminal).
- Requires `pacman` and an authenticated sudo.
- No source changes; installing one small package is the only state change.

## Diagnose

Check whether the clipboard tools exist and what the clipboard currently holds:

~~~bash
command -v wl-copy wl-paste; echo $?
wl-paste 2>&1 | head -c 200
~~~

Expect `wl-copy`/`wl-paste` found at `/usr/bin` and some content in the clipboard (a previous copy). If `command -v` prints nothing and the system has never had the tools, opencode writes nowhere even though the UI says "copied".

Optional deeper read (needs `xclip`): confirm the contents of the X11 and Wayland clipboards are identical (the compositor bridges them), which proves the compositor is healthy and the failure is inside the app:

~~~bash
DISPLAY=:0 xclip -selection clipboard -o 2>&1 | head -c 200
echo "=== WL ==="
wl-paste 2>&1 | head -c 200
~~~

Note: `strings /usr/bin/opencode | grep wl-copy` returns nothing; opencode invokes the tool at runtime, so absence from the binary is expected and not evidence of a different mechanism.

## Fix

Install the clipboard toolkit (Arch/CachyOS):

~~~bash
sudo pacman -S wl-clipboard
~~~

Then **restart opencode** - it initializes clipboard support once at start-up, so it must be relaunched after the package is installed.

Do not uninstall `wl-clipboard` afterwards: other CLI programs (tmux, vim plugins, etc.) also rely on `wl-copy` under Wayland.

## Verify

1. Copy some text inside opencode (select text and press the copy key/gesture).
2. In Ptyxis run:

~~~bash
wl-paste | head -c 200
ps aux | grep '[w]l-copy'
~~~

Expect the pasted text to be the text you copied from opencode, and a background `wl-copy` process holding the clipboard (this is normal Wayland clipboard ownership).

## Notes

- `wl-paste` is read-only viewing; `wl-copy` is write; both come from the `wl-clipboard` package.
- `xclip` is optional and only useful for diagnosing X11-side state; it is not required by opencode.

## Middle-click paste does not work

After the fix, opencode copies work with Ctrl+V but **middle-click paste is still empty**. Root cause: opencode only writes the CLIPBOARD selection, while middle-click paste reads the PRIMARY selection. Regular GNOME/GTK apps write both, which is why middle-click works everywhere else.

Fix: install a `wl-copy` wrapper in `~/.local/bin` (ahead of `/usr/bin` in PATH) that writes both selections:

~~~bash
cat > ~/.local/bin/wl-copy <<'EOF'
#!/bin/bash
# wl-copy wrapper: write both CLIPBOARD and PRIMARY
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
cat > "$tmp"
/usr/bin/wl-copy < "$tmp" || exit 1
/usr/bin/wl-copy --primary < "$tmp" || exit 1
EOF
chmod +x ~/.local/bin/wl-copy
~~~

Verify both selections:

~~~bash
echo "TEST" | /home/vv/.local/bin/wl-copy
wl-paste | head -c 50
wl-paste --primary | head -c 50
~~~

Note that `wl-copy` holds the clipboard by staying alive, so a terminal command using the wrapper may not return until the clipboard changes; this is normal Wayland behavior, not a hang.

If opencode was started before the wrapper was created, restart it so it picks up the new PATH resolution.
