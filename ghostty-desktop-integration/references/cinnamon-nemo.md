# Cinnamon/Nemo Open in Terminal repair

Use this reference only when Cinnamon/Nemo's **Open in Terminal** opens Ghostty in an existing window's working directory instead of the selected folder. It preserves normal Ghostty launches and configures Nemo's terminal command through a dedicated user-local wrapper.

## Recognize the failure

The known failure depends on existing Ghostty state:

| State before the Nemo action | Typical result |
| --- | --- |
| No Ghostty window exists | The selected folder appears correct. |
| Ghostty is focused in `~` | The launch appears correct only because the inherited directory is `~`. |
| Ghostty is focused elsewhere | The new window opens in the existing window's directory. |

## Non-negotiable safety rules

- Start read-only. Nemo may use Cinnamon's direct terminal executable setting, so an unexpected `xdg-terminal-exec` result alone does not authorize a change.
- Never modify `/usr/share/applications/com.mitchellh.ghostty.desktop`, system-wide Ghostty configuration, or another system desktop file.
- Treat `~/.local/bin/nemo-ghostty` as user-owned. Stop if it is a symlink, not a regular file, owned by another account, or contains unknown logic.
- Never forward Cinnamon's `exec-arg` such as `-e` into the wrapper; Ghostty interprets that as command execution rather than a plain terminal launch.
- Before writing, show the existing settings and wrapper evidence, exact proposed content, backup path, rollback, and affected key. Obtain explicit approval.

## Diagnose without changing anything

Confirm components and the active terminal setting:

```bash
nemo --version
ghostty --version
gsettings get org.cinnamon.desktop.default-applications.terminal exec
gsettings get org.cinnamon.desktop.default-applications.terminal exec-arg
printf 'XDG_CURRENT_DESKTOP=%s\n' "$XDG_CURRENT_DESKTOP"
```

Inspect Ghostty behavior and desktop integration:

```bash
ghostty +show-config | grep -E '^(working-directory|window-inherit-working-directory|gtk-single-instance)[[:space:]]*='
grep -nE '^(Exec|X-TerminalArgDir)=' /usr/share/applications/com.mitchellh.ghostty.desktop
ps -eo pid,ppid,args | grep '[g]hostty'
```

GTK single-instance reuse can let an existing process replace Nemo's child-process working directory. Setting `window-inherit-working-directory=false` is not the repair: it can fall back to the home/default directory rather than preserve Nemo's selected location.

Inspect the proposed wrapper target:

```bash
wrapper="$HOME/.local/bin/nemo-ghostty"
if [ -e "$wrapper" ] || [ -L "$wrapper" ]; then
  stat -c '%F %U:%G %A %n' "$wrapper"
  readlink -f "$wrapper"
  sha256sum "$wrapper"
  printf '%s\n' '--- current wrapper ---'
  cat "$wrapper"
else
  printf 'Wrapper does not exist: %s\n' "$wrapper"
fi
```

Treat selector files as supporting evidence only:

```bash
for file in \
  "$HOME/.config/X-Cinnamon-xdg-terminals.list" \
  "$HOME/.config/xdg-terminals.list" \
  "$HOME/.config/ubuntu-xdg-terminals.list"; do
  [ -r "$file" ] && { printf '\n--- %s ---\n' "$file"; cat "$file"; }
done
DEBUG=1 xdg-terminal-exec 2>&1 | head -n 80
```

Do not overwrite selector files unless evidence establishes that the affected Nemo version uses them. For the direct Cinnamon path, the repair target is `org.cinnamon.desktop.default-applications.terminal exec`.

## Decide whether the known wrapper applies

Use it only when all conditions hold:

1. An existing Ghostty window changes Nemo's resulting working directory.
2. The intended Ghostty executable is confirmed, normally `/usr/bin/ghostty`.
3. Cinnamon's `exec` is `ghostty` or an already verified known wrapper.
4. The wrapper target is absent or is a regular user-owned file containing the known logic.
5. The user accepts a separate Ghostty GTK instance for Nemo launches.

Proposed wrapper:

```sh
#!/bin/sh
# Nemo starts this command with the selected folder as its working directory.
exec /usr/bin/ghostty \
  --gtk-single-instance=false \
  --working-directory="$PWD"
```

## Confirmation and repair

Before changing anything, report the current settings, wrapper evidence, exact proposed content, timestamped backup path, new `exec` value, and exact rollback value. Wait for explicit approval.

After approval, set a real timestamped backup path and apply:

```bash
set -eu
wrapper="$HOME/.local/bin/nemo-ghostty"
backup="$HOME/.local/bin/nemo-ghostty.bak-YYYYMMDD-HHMMSS"
old_exec="$(gsettings get org.cinnamon.desktop.default-applications.terminal exec)"

install -d -m 700 "$HOME/.local/bin"
if [ -e "$wrapper" ]; then
  cp --preserve=mode,ownership,timestamps "$wrapper" "$backup"
fi

cat >"$wrapper" <<'EOF'
#!/bin/sh
# Nemo starts this command with the selected folder as its working directory.
exec /usr/bin/ghostty \
  --gtk-single-instance=false \
  --working-directory="$PWD"
EOF
chmod 755 "$wrapper"
gsettings set org.cinnamon.desktop.default-applications.terminal exec "$wrapper"

printf 'Previous terminal exec: %s\n' "$old_exec"
printf 'Current terminal exec:  '
gsettings get org.cinnamon.desktop.default-applications.terminal exec
```

Do not overwrite an unknown target to make the block succeed.

## Verify end to end

Create two distinct test directories while Ghostty is open in a third:

```bash
mkdir -p "$HOME/tmp/nemo-ghostty-test-a" "$HOME/tmp/nemo-ghostty-test-b"
(cd "$HOME/tmp/nemo-ghostty-test-a" && "$HOME/.local/bin/nemo-ghostty")
(cd "$HOME/tmp/nemo-ghostty-test-b" && "$HOME/.local/bin/nemo-ghostty")
gsettings get org.cinnamon.desktop.default-applications.terminal exec
```

Run `pwd` in each new terminal and require the corresponding test directory. Then repeat through Nemo's **Open in Terminal** action. Also verify a normal global terminal shortcut still uses its ordinary default-directory behavior. Report observed paths rather than inferring success from process arguments.

## Roll back safely

Restore the captured pre-change value:

```bash
gsettings set org.cinnamon.desktop.default-applications.terminal exec 'PREVIOUS_EXEC_VALUE'
```

Restore a timestamped backup only after inspecting it:

```bash
stat -c '%F %U:%G %A %n' "$HOME/.local/bin/nemo-ghostty.bak-YYYYMMDD-HHMMSS"
cat "$HOME/.local/bin/nemo-ghostty.bak-YYYYMMDD-HHMMSS"
mv "$HOME/.local/bin/nemo-ghostty.bak-YYYYMMDD-HHMMSS" "$HOME/.local/bin/nemo-ghostty"
```

If this repair created a previously absent wrapper, remove only that exact regular file after rechecking its path and contents. Never delete an unknown, replaced, or symlinked wrapper.
