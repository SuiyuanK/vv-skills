#!/usr/bin/env python3
"""Add or remove _NET_WM_STATE_SKIP_TASKBAR on the dsh-pet window (one-shot, reversible)."""

from __future__ import annotations

import argparse
import sys
import time

import _x11_probe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--add", action="store_true", help="hide the pet from the taskbar/Dock")
    group.add_argument("--remove", action="store_true", help="show it again")
    parser.add_argument("--match", default=_x11_probe.NAME_MATCH, help="window-title substring to match")
    args = parser.parse_args()

    display, root = _x11_probe.connect()
    windows = _x11_probe.find_pet_windows(display, root, args.match)
    if not windows:
        print(f"no window matching {args.match!r} on $DISPLAY")
        return 1

    for window in windows:
        changed = _x11_probe.set_skip_taskbar(display, root, window, add=args.add)
        time.sleep(0.2)
        state = _x11_probe.read_state(display, window)
        print(
            f"id=0x{window.id:x} {'changed' if changed else 'unchanged'} state={state}"
        )
    print("note: this is a one-shot hint; it is lost when the window is remapped (helper restart).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
