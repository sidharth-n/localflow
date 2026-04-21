"""Clipboard-paste injection on X11.

Copy text to the clipboard, fire Ctrl+V via xdotool, restore the previous
clipboard contents after a delay so the user's prior copy isn't destroyed.
"""
from __future__ import annotations

import logging
import subprocess
import time

import pyperclip

log = logging.getLogger(__name__)


def paste(text: str, restore_after_ms: int = 500) -> None:
    prev: str | None
    try:
        prev = pyperclip.paste()
    except pyperclip.PyperclipException as e:
        log.debug("could not read previous clipboard: %s", e)
        prev = None

    pyperclip.copy(text)
    _send_ctrl_v()

    if prev is not None:
        time.sleep(restore_after_ms / 1000)
        try:
            pyperclip.copy(prev)
        except pyperclip.PyperclipException as e:
            log.debug("could not restore previous clipboard: %s", e)


def _send_ctrl_v() -> None:
    subprocess.run(
        ["xdotool", "key", "--clearmodifiers", "ctrl+v"],
        check=True,
    )
