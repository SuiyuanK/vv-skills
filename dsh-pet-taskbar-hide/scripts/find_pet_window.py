#!/usr/bin/env python3
"""Print dsh-pet windows with id, name and _NET_WM_STATE (read-only)."""

from __future__ import annotations

import sys

import _x11_probe


def main() -> int:
    display, root = _x11_probe.connect()
    windows = _x11_probe.find_pet_windows(display, root)
    if not windows:
        print("no dsh-pet window found on $DISPLAY (is the pet running? is this an XWayland session?)")
        return 1
    if len(windows) > 1:
        print(f"warning: {len(windows)} candidate pet windows; confirm by tooltip before changing anything")
    for window in windows:
        state = _x11_probe.read_state(display, window)
        flag = "SKIP_TASKBAR=on" if "_NET_WM_STATE_SKIP_TASKBAR" in state else "SKIP_TASKBAR=off"
        print(f"id=0x{window.id:x} {flag} state={state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
