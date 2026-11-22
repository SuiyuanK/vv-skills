#!/usr/bin/env python3
"""Shared X11 helpers: find the dsh-pet window and read/set _NET_WM_STATE_SKIP_TASKBAR.

Imported by find_pet_window.py and toggle_skip_taskbar.py. Requires python-xlib.
The window is always resolved by its title, never by a cached id or PID.
"""

from __future__ import annotations

import sys
from typing import Iterable

try:
    import Xlib.display
    import Xlib.X as X
    from Xlib.protocol import event as E
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "error: python-xlib is required (CachyOS/Arch: sudo pacman -S python-xlib)\n"
    )
    raise SystemExit(2)

NAME_MATCH = "dsh-pet"


def connect():
    display = Xlib.display.Display()
    root = display.screen().root
    return display, root


def _prop_text(display, window, atom: str) -> str:
    try:
        prop = window.get_full_property(display.intern_atom(atom), X.AnyPropertyType)
        if not prop:
            return ""
        raw = prop.value
        return raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
    except Exception:
        return ""


def _name_of(display, window) -> str:
    """Window title; comments, chat windows and editors often contain 'dsh-pet' too."""
    return _prop_text(display, window, "_NET_WM_NAME")


def _class_of(display, window) -> str:
    return _prop_text(display, window, "WM_CLASS")


def iter_windows(display, window) -> Iterable:
    """Depth-first walk; property failures on transient windows are ignored."""
    try:
        children = window.query_tree().children
    except Exception:
        return
    for child in children:
        yield child
        yield from iter_windows(display, child)


def is_pet_window(display, window, match: str = NAME_MATCH) -> bool:
    """A pet window has the title AND the generic Electron WM_CLASS.

    Without the WM_CLASS guard, any window whose title mentions dsh-pet (a code
    editor, a browser tab, a comment) would be a target.
    """
    return match in _name_of(display, window) and "electron" in _class_of(display, window).lower()


def find_pet_windows(display, root, match: str = NAME_MATCH):
    return [w for w in iter_windows(display, root) if is_pet_window(display, w, match)]


def read_state(display, window) -> list[str]:
    prop = window.get_full_property(display.intern_atom("_NET_WM_STATE"), X.AnyPropertyType)
    if not prop:
        return []
    return [display.get_atom_name(atom) for atom in prop.value]


def set_skip_taskbar(display, root, window, add: bool) -> bool:
    """Send the EWMH action (1=add, 0=remove) to the root; return whether it was needed."""
    state = display.intern_atom("_NET_WM_STATE")
    skip = display.intern_atom("_NET_WM_STATE_SKIP_TASKBAR")
    prop = window.get_full_property(state, X.AnyPropertyType)
    present = skip in (prop.value if prop else [])
    if present == add:
        return False
    event = E.ClientMessage(
        window=window,
        client_type=state,
        # data[3] 是 source indication：1（pager）在 GNOME 下移除常被忽略，用 0（unspecified）
        data=(32, [1 if add else 0, skip, 0, 0, 0]),
    )
    root.send_event(event, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    display.flush()
    return True
