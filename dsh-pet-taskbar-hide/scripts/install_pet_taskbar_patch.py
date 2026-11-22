#!/usr/bin/env python3
"""Install (or revert) the local dsh-pet patch that keeps the pet off the taskbar.

Writes <dsh-pet>/runtime/electron-helper/pet-taskbar-suppress.js and adds two
marked lines to main.js. Dry run by default; --apply writes, --revert restores.
Idempotent: existing patch files are never overwritten.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MODULE_NAME = "pet-taskbar-suppress.js"
MARK = "// [local-patch]"
MARK_COMMENT_RE = re.compile(r"^\s*" + re.escape("// [local-patch]"))
REQUIRE_COMMENT = MARK + " 宠物窗口在 GNOME/XWayland 下隐藏任务栏按钮；升级 dsh-pet 会覆盖本文件，补丁随之失效"
REQUIRE_CODE = "const { attach: attachTaskbarSuppress } = require('./pet-taskbar-suppress.js');"
ATTACH_COMMENT = MARK + " 窗口显示后补一次「跳过任务栏」提示（Linux 上 Electron 的 skipTaskbar 不够用）"
ATTACH_CODE = "attachTaskbarSuppress();"

MODULE_SOURCE = r'''/**
 * [local-patch] 让桌面宠物窗口不在任务栏/仪表盘里占位（GNOME Wayland + XWayland）。
 *
 * 背景：Electron 的 skipTaskbar 在 Linux 上只是一次 WM 提示，宠物窗口 map 之后 GNOME Shell
 * 仍然给它排了任务栏按钮；GNOME 又没有 KWin 那种窗口规则可以外部补救。所以这里在窗口
 * 显示之后直接经 X11（python-xlib）发 _NET_WM_STATE 客户端消息，加上 _NET_WM_STATE_SKIP_TASKBAR。
 *
 * 只在 X11/XWayland 且系统有 python3 + python-xlib 时生效；任何失败都静默放弃，
 * 保证宠物本身不受影响。取消：环境变量 DSH_PET_TASKBAR_FIX=0。
 * 删掉本文件与 main.js 里对应的 require / attach 两行即恢复原状。
 * @module dsh-pet/runtime/electron-helper/pet-taskbar-suppress
 */

'use strict';

const { execFile } = require('node:child_process');

/** 会话/开关判定：没有 DISPLAY（纯 Wayland 原生）或显式关闭时不做任何事。 */
function enabled() {
  return Boolean(process.env.DISPLAY) && process.env.DSH_PET_TASKBAR_FIX !== '0';
}

const SCRIPT = [
  'import Xlib.display, Xlib.X as X',
  'from Xlib.protocol import event as E',
  'd = Xlib.display.Display()',
  "NET = d.intern_atom('_NET_WM_NAME')",
  "UTF8 = d.intern_atom('UTF8_STRING')",
  "STATE = d.intern_atom('_NET_WM_STATE')",
  "SKIP = d.intern_atom('_NET_WM_STATE_SKIP_TASKBAR')",
  'root = d.screen().root',
  'def walk(w):',
  '    for c in w.query_tree().children:',
  '        try:',
  '            p = c.get_full_property(NET, UTF8)',
  "            name = p.value.decode('utf8', 'replace') if p else ''",
  '        except Exception:',
  "            name = ''",
  "        if 'dsh-pet' in name:",
  '            st = c.get_full_property(STATE, X.AnyPropertyType)',
  '            atoms = list(st.value) if st else []',
  '            if SKIP not in atoms:',
  '                ev = E.ClientMessage(window=c, client_type=STATE, data=(32, [1, SKIP, 0, 1, 0]))',
  '                root.send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)',
  '        walk(c)',
  'walk(root)',
  'd.flush()',
  '',
].join('\n');

/** 对当前已存在的宠物窗口重申一次「跳过任务栏」；异步、失败静默。 */
function suppressTaskbar() {
  if (!enabled()) return;
  execFile('python3', ['-c', SCRIPT], { timeout: 8000 }, () => {});
}

/** 定时补刀：窗口 map 之后（以及显示器/工作区变化重建窗口后）再给一次提示。 */
function attach() {
  if (!enabled()) return;
  const tick = setInterval(suppressTaskbar, 1000);
  tick.unref?.();
  suppressTaskbar();
}

module.exports = { suppressTaskbar, attach };
'''


def helper_dir(args) -> Path:
    if args.helper_dir:
        return Path(args.helper_dir).expanduser()
    home = Path(os.environ.get("HOME") or Path.home())
    return home / ".dsh" / "profiles" / args.profile / "node_modules" / "dsh-pet" / "runtime" / "electron-helper"


def strip_patch(text: str):
    """Remove each injected comment and the single code line that follows it.

    Returns (new_text, removed_count). Removal is index-based so it never
    depends on the order the injected lines happen to appear in.
    """
    lines = text.splitlines(keepends=True)
    drop: set[int] = set()
    for i, line in enumerate(lines):
        if not MARK_COMMENT_RE.match(line):
            continue
        drop.add(i)
        if i + 1 < len(lines):
            drop.add(i + 1)
    for i, line in enumerate(lines):
        if i not in drop and ("pet-taskbar-suppress" in line or "attachTaskbarSuppress" in line):
            drop.add(i)
    kept = [line for i, line in enumerate(lines) if i not in drop]
    return "".join(kept), len(drop)


def node_check(path: Path) -> bool:
    node = shutil.which("node")
    if not node:
        print("  ! node not found; skipped syntax check")
        return True
    result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr.strip())
        return False
    return True


def apply(target: Path, dry: bool) -> int:
    helper = target
    module = helper / MODULE_NAME
    main_js = helper / "main.js"
    if not main_js.is_file():
        print(f"error: {main_js} not found (wrong profile or dsh-pet not installed)")
        return 1

    text = main_js.read_text(encoding="utf-8")
    has_require = "require('./pet-taskbar-suppress.js')" in text
    has_attach = "attachTaskbarSuppress();" in text

    print(f"helper dir : {helper}")
    print(f"module     : {module} ({'exists, kept' if module.exists() else 'to be created'})")
    print(f"main.js    : require={'present' if has_require else 'to add'} attach={'present' if has_attach else 'to add'}")
    if dry:
        print("dry run; add --apply to write")
        return 0

    backup = helper / "main.js.bak-taskbar-patch"
    if not module.exists():
        module.write_text(MODULE_SOURCE, encoding="utf-8")
        if not node_check(module):
            print("error: module failed syntax check; removing it")
            module.unlink()
            return 1

    if not (has_require and has_attach):
        if not backup.exists():
            shutil.copy2(main_js, backup)
            print(f"backup     : {backup}")
        lines = text.splitlines(keepends=True)
        # Insert bottom-up so earlier indices stay valid; insert AFTER the index.
        if not has_attach:
            marker = "const petWindows = createWindows({"
            pos = next((i for i, l in enumerate(lines) if l.startswith(marker)), -1)
            if pos < 0:
                print("error: createWindows(...) call not found; apply manually")
                return 1
            close = next((i for i in range(pos, len(lines)) if lines[i].rstrip("\r\n") == "});"), -1)
            if close < 0:
                print("error: end of createWindows(...) call not found; apply manually")
                return 1
            lines[close + 1 : close + 1] = [ATTACH_COMMENT + "\n", ATTACH_CODE + "\n"]
        if not has_require:
            want = "const { createWindows } = require('./main/windows.js');"
            pos = next((i for i, l in enumerate(lines) if l.rstrip("\r\n") == want), -1)
            if pos < 0:
                print("error: anchor for the require line not found; main.js layout changed, apply manually")
                return 1
            lines[pos : pos] = [REQUIRE_COMMENT + "\n", REQUIRE_CODE + "\n"]
        new = "".join(lines)
        main_js.write_text(new, encoding="utf-8")
        if not node_check(main_js):
            print("error: main.js failed syntax check; restored main.js from the backup")
            shutil.copy2(backup, main_js)
            return 1

    print("patched. restart the helper, then verify with find_pet_window.py")
    return 0


def revert(target: Path, dry: bool) -> int:
    helper = target
    module = helper / MODULE_NAME
    main_js = helper / "main.js"
    backup = helper / "main.js.bak-taskbar-patch"
    for path in (module, main_js, backup):
        print(f"{'rm  ' if not dry else 'would rm '}{path}")
    if dry:
        print("dry run; add --apply to delete")
        return 0
    if module.exists():
        module.unlink()
    if backup.exists():
        shutil.copy2(backup, main_js)
        backup.unlink()
    else:
        text = main_js.read_text(encoding="utf-8") if main_js.exists() else ""
        stripped, removed = strip_patch(text)
        if removed != 4:
            print(f"warning: expected 4 patch lines in main.js, removed {removed}; review the file by hand")
        main_js.write_text(stripped, encoding="utf-8")
        if not node_check(main_js):
            print("error: main.js failed syntax check after manual revert; review it by hand")
            return 1
    print("reverted. restart the helper to drop the patch")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="web", help="DSH profile name under ~/.dsh/profiles (default: web)")
    parser.add_argument("--helper-dir", help="explicit electron-helper directory (overrides --profile)")
    parser.add_argument("--apply", action="store_true", help="write changes (default is a dry run)")
    parser.add_argument("--revert", action="store_true", help="remove the patch and restore main.js")
    args = parser.parse_args()

    target = helper_dir(args)
    if args.revert:
        return revert(target, dry=not args.apply)
    return apply(target, dry=not args.apply)


if __name__ == "__main__":
    sys.exit(main())
