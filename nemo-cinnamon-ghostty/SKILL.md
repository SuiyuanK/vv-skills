---
name: nemo-cinnamon-ghostty
description: Diagnose and safely fix Linux Cinnamon/Nemo “Open in Terminal” launches that open Ghostty in an existing terminal’s working directory instead of the selected folder. Use for Nemo right-click terminal launches, Ghostty GTK single-instance reuse, Cinnamon terminal gsettings, user-local terminal wrappers, verification, and rollback.
---

# Nemo/Cinnamon Ghostty “Open in Terminal” Repair

## Purpose and scope

Use this skill when Nemo’s **Open in Terminal** does not open the selected folder in Ghostty, especially when the result changes according to an already open or focused Ghostty window:

| State before the Nemo action | Typical incorrect result |
| --- | --- |
| No Ghostty window exists | The selected folder appears correct. |
| Ghostty is focused in `~` | The new window appears to work because it opens in `~`. |
| Ghostty is focused in another directory | The new window opens in that existing window’s directory rather than the selected Nemo folder. |

This runbook is specific to Linux Cinnamon/Nemo with Ghostty. It preserves ordinary Ghostty launch behavior while configuring **Nemo’s** configured terminal command to use a dedicated user-local wrapper.

## Non-negotiable safety rules

- Start read-only. Do not change terminal settings merely because `xdg-terminal-exec` or a desktop-entry selector reports an unexpected terminal: Nemo may use Cinnamon’s direct terminal executable setting instead.
- Never modify `/usr/share/applications/com.mitchellh.ghostty.desktop`, system-wide Ghostty configuration, or other system-provided desktop files for this issue.
- Treat `~/.local/bin/nemo-ghostty` as user-owned. Before creating or replacing it, inspect its type, ownership, contents, and hash. Stop if it is a symlink, not a regular file, or has unknown content.
- Never forward Cinnamon’s terminal `exec-arg` such as `-e` into the wrapper. In Ghostty, that changes the request into a command-execution launch rather than a plain terminal window.
- Before any write, show the exact target, existing setting and file content/hash, proposed wrapper content, backup location, rollback command, and affected `gsettings` key. Obtain the user’s explicit approval.
- Do not reset, clean, or broadly stage unrelated changes when this skill itself is synchronized to its source repository.

## 1. Diagnose without changing anything

### Confirm components and active terminal setting

```bash
nemo --version
ghostty --version
gsettings get org.cinnamon.desktop.default-applications.terminal exec
gsettings get org.cinnamon.desktop.default-applications.terminal exec-arg
printf 'XDG_CURRENT_DESKTOP=%s\n' "$XDG_CURRENT_DESKTOP"
```

Nemo’s relevant setting is normally `org.cinnamon.desktop.default-applications.terminal exec`. Do not assume `exec-arg` is honored by Nemo; inspect the actual behavior before designing a wrapper.

### Inspect effective Ghostty behavior and desktop integration

```bash
ghostty +show-config | grep -E '^(working-directory|window-inherit-working-directory|gtk-single-instance)[[:space:]]*='
grep -nE '^(Exec|X-TerminalArgDir)=' /usr/share/applications/com.mitchellh.ghostty.desktop
ps -eo pid,ppid,args | grep '[g]hostty'
```

A Ghostty desktop entry can request GTK single-instance behavior. In that mode, a new launch may be handled by an existing Ghostty process. If Ghostty inherits the previously focused window’s directory, that can override the directory Nemo supplied as the child process cwd.

`window-inherit-working-directory=false` is **not** the repair for this situation. It disables prior-window inheritance but can fall back to Ghostty’s home/default directory rather than retaining Nemo’s selected directory.

### Inspect the proposed wrapper target before touching it

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

Only a regular file with the known wrapper content below may be replaced by this skill. If it is a symlink, belongs to another account, or has custom/unknown logic, stop and ask the user how to preserve it.

### Treat xdg terminal selectors as diagnostic evidence only

```bash
for file in \
  "$HOME/.config/X-Cinnamon-xdg-terminals.list" \
  "$HOME/.config/xdg-terminals.list" \
  "$HOME/.config/ubuntu-xdg-terminals.list"; do
  [ -r "$file" ] && { printf '\n--- %s ---\n' "$file"; cat "$file"; }
done
DEBUG=1 xdg-terminal-exec 2>&1 | head -n 80
```

These selector files and `xdg-terminal-exec` can explain desktop-launch behavior, but do **not** overwrite them unless diagnostics establish that the affected Nemo version actually uses them. For the direct Cinnamon path, the `gsettings` `exec` value is the repair target.

## 2. Decide whether the known wrapper repair applies

Use the repair only when all points below are true:

1. Nemo’s right-click launch is affected by an existing Ghostty window’s working directory.
2. Ghostty is installed at `/usr/bin/ghostty` (or the intended absolute executable is confirmed).
3. Cinnamon’s terminal `exec` is either `ghostty` or an already verified known `nemo-ghostty` wrapper.
4. The wrapper target does not exist, or is a regular user-owned file containing the known wrapper logic.
5. The user accepts that Nemo launches will start a separate Ghostty GTK instance so their specified directory is honored.

The intended wrapper is:

```sh
#!/bin/sh
# Nemo starts this command with the selected folder as its working directory.
exec /usr/bin/ghostty \
  --gtk-single-instance=false \
  --working-directory="$PWD"
```

Nemo starts its configured terminal program with the selected folder as its cwd. The wrapper preserves that cwd explicitly and forces a separate Ghostty GTK instance, so a currently focused Ghostty window cannot replace it with its own directory.

## 3. Confirmation gate for repair

Before modifying anything, report all of the following and wait for an explicit confirmation:

- Current `gsettings` values for `exec` and `exec-arg`.
- Wrapper path, type, owner, permissions, current hash, and current contents (or that it is absent).
- The exact wrapper content above.
- The proposed backup path: `~/.local/bin/nemo-ghostty.bak-YYYYMMDD-HHMMSS` when replacing a known wrapper.
- The exact new setting: `org.cinnamon.desktop.default-applications.terminal exec = ~/.local/bin/nemo-ghostty`.
- The rollback setting and whether removing/restoring the wrapper will be appropriate.

Do not apply the command block below until approval is received.

## 4. Apply the verified repair

Set `backup` to a real timestamp before running the block. This command intentionally does not use the Cinnamon `exec-arg` value.

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
printf 'Current terminal exec:  '; gsettings get org.cinnamon.desktop.default-applications.terminal exec
```

Do not overwrite an unknown target merely to make this block succeed. Re-run diagnosis and adapt the plan with the user instead.

## 5. Verify end-to-end

Create or identify two non-home directories, then test the wrapper from each directory while Ghostty is already open in a third directory:

```bash
mkdir -p "$HOME/tmp/nemo-ghostty-test-a" "$HOME/tmp/nemo-ghostty-test-b"
(cd "$HOME/tmp/nemo-ghostty-test-a" && "$HOME/.local/bin/nemo-ghostty")
(cd "$HOME/tmp/nemo-ghostty-test-b" && "$HOME/.local/bin/nemo-ghostty")
gsettings get org.cinnamon.desktop.default-applications.terminal exec
```

In each opened terminal, run:

```bash
pwd
```

It must report the corresponding test directory, not the existing Ghostty window’s directory and not `~`.

Then perform the user-visible test:

1. Leave one Ghostty window in a third directory such as `~/TMP`.
2. In Nemo, select `nemo-ghostty-test-a` and choose **Open in Terminal**.
3. Run `pwd` in the new terminal; require `~/tmp/nemo-ghostty-test-a`.
4. Repeat for `nemo-ghostty-test-b`.
5. Start a normal terminal from the global shortcut and confirm it retains its normal default directory behavior.

If process reuse makes results ambiguous, fully close all Ghostty windows/processes, start one Ghostty window in the third directory, and repeat. Report the observed `pwd` values rather than assuming success from process arguments alone.

## 6. Roll back safely

Restore the pre-change Cinnamon terminal executable captured during the apply step:

```bash
gsettings set org.cinnamon.desktop.default-applications.terminal exec 'PREVIOUS_EXEC_VALUE'
```

If this run created a timestamped backup for a known wrapper, restore it only after reviewing it:

```bash
stat -c '%F %U:%G %A %n' "$HOME/.local/bin/nemo-ghostty.bak-YYYYMMDD-HHMMSS"
cat "$HOME/.local/bin/nemo-ghostty.bak-YYYYMMDD-HHMMSS"
mv "$HOME/.local/bin/nemo-ghostty.bak-YYYYMMDD-HHMMSS" "$HOME/.local/bin/nemo-ghostty"
```

If this run created the wrapper and no pre-existing wrapper existed, remove only that exact regular file after confirming its contents and path:

```bash
rm -- "$HOME/.local/bin/nemo-ghostty"
```

Do not delete an unknown wrapper, a symlink, or a wrapper that was modified after this repair.
