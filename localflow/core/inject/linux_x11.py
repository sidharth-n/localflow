"""Clipboard-paste injection on X11.

Copy text to the clipboard, fire the paste shortcut via xdotool, restore the
previous clipboard contents after a delay. The shortcut is Ctrl+Shift+V in
terminals (Ctrl+V is SIGINT there) and Ctrl+V everywhere else — we detect by
WM_CLASS.
"""
from __future__ import annotations

import logging
import subprocess
import time

import pyperclip

log = logging.getLogger(__name__)

# Substrings (lowercased) that identify a terminal window via WM_CLASS.
_TERMINAL_CLASSES: tuple[str, ...] = (
    "terminal", "konsole", "xterm", "alacritty", "kitty", "tilix",
    "foot", "urxvt", "rxvt", "yakuake", "hyper", "wezterm", "warp",
    "terminator", "tmux",
)


def paste(text: str, restore_after_ms: int = 500) -> None:
    prev: str | None
    try:
        prev = pyperclip.paste()
    except pyperclip.PyperclipException as e:
        log.debug("could not read previous clipboard: %s", e)
        prev = None

    pyperclip.copy(text)
    _send_paste_shortcut()

    if prev is not None:
        time.sleep(restore_after_ms / 1000)
        try:
            pyperclip.copy(prev)
        except pyperclip.PyperclipException as e:
            log.debug("could not restore previous clipboard: %s", e)


def _active_window_class() -> str:
    # getwindowfocus uses XGetInputFocus — more reliable than getactivewindow,
    # which depends on the WM setting _NET_ACTIVE_WINDOW.
    try:
        wid = subprocess.check_output(
            ["xdotool", "getwindowfocus"],
            text=True, timeout=0.3, stderr=subprocess.DEVNULL,
        ).strip()
        if not wid:
            return ""
        # xprop output: WM_CLASS(STRING) = "instance", "class"
        prop = subprocess.check_output(
            ["xprop", "-id", wid, "WM_CLASS"],
            text=True, timeout=0.3, stderr=subprocess.DEVNULL,
        ).strip().lower()
        return prop
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def _send_paste_shortcut() -> None:
    cls = _active_window_class()
    is_term = any(t in cls for t in _TERMINAL_CLASSES)
    combo = "ctrl+shift+v" if is_term else "ctrl+v"
    log.debug("paste combo=%s (window class=%r)", combo, cls)
    subprocess.run(
        ["xdotool", "key", "--clearmodifiers", combo],
        check=True,
    )
