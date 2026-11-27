---
name: codex-html-mime-fix
description: Diagnose and repair the Linux Codex or ChatGPT desktop app changing the default handler for text/html from Google Chrome to chatgpt.desktop after launch or reboot. Use when HTML files unexpectedly open in Codex, xdg-mime keeps reverting after Codex starts, or the user wants a persistent user-level launcher workaround that survives package reinstall and upgrade.
---

# Codex HTML MIME Fix

Diagnose the MIME association first, then apply the bundled user-level launcher workaround when the installed package matches the expected layout.

## Preconditions and safety

- Run as the logged-in desktop user. Never use sudo.
- Require /usr/bin/chatgpt and /usr/share/applications/chatgpt.desktop.
- Require xdg-mime, update-desktop-database, and google-chrome.desktop.
- Write only to the user's .local directories and /home/vv/TMP/tmp.
- Back up an existing unmanaged user-level chatgpt.desktop before replacement.
- Do not stop, reinstall, or upgrade Codex while it is running unless the user explicitly requests that separate action.

## Diagnose

Run read-only checks:

~~~bash
dpkg-query -W chatgpt 2>/dev/null || true
xdg-mime query default text/html
ls -l /usr/bin/chatgpt /usr/share/applications/chatgpt.desktop
ls -l ~/.local/bin/chatgpt-html-fix ~/.local/share/applications/chatgpt.desktop 2>/dev/null || true
~~~

Confirm the symptom occurs after launching Codex rather than changing unrelated MIME handlers.

## Apply the workaround

Run:

~~~bash
bash scripts/setup-codex-html-fix.sh
~~~

The script creates a wrapper that watches text/html for 15 seconds after Codex starts and restores google-chrome.desktop if Codex changes it. It also installs a user-level chatgpt.desktop that shadows the package-owned launcher.

After setup, tell the user to unpin the old taskbar icon, launch Codex from the application menu, and pin the refreshed icon.

## Verify

Launch Codex from the refreshed application icon, wait at least 15 seconds, then run:

~~~bash
xdg-mime query default text/html
awk -F= '/^Exec=/{print substr($0, 6); exit}' ~/.local/share/applications/chatgpt.desktop
~~~

Expect google-chrome.desktop and an Exec line pointing to ~/.local/bin/chatgpt-html-fix.

APT reinstall or upgrade normally leaves these user-level files intact. Reapply or revise the skill only if a future package changes the launcher path, desktop filename, or registration behavior.

## Bundled resource

- scripts/setup-codex-html-fix.sh: idempotent installer for the wrapper and user-level desktop override.
