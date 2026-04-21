"""Hotkey listener.

Wraps pynput so the rest of the pipeline just sees on_start / on_stop callbacks.
Supports push-to-talk (hold) and toggle (tap) modes.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from pynput import keyboard

log = logging.getLogger(__name__)


class Mode(str, Enum):
    PUSH_TO_TALK = "push_to_talk"
    TOGGLE = "toggle"


def _promote(parsed: keyboard.KeyCode) -> keyboard.Key | keyboard.KeyCode:
    # HotKey.parse("<ctrl_r>") returns a bare KeyCode, but the Listener delivers
    # Key.ctrl_r; the two compare unequal because of an internal _symbol field.
    # Swap in the Key enum member when one shares vk+char.
    for k in keyboard.Key:
        v = k.value
        if v.vk == parsed.vk and v.char == parsed.char:
            return k
    return parsed


@dataclass
class HotkeyListener:
    key: str
    mode: Mode
    on_start: Callable[[], None]
    on_stop: Callable[[], None]

    _target: keyboard.Key | keyboard.KeyCode = field(init=False)
    _pressed: bool = field(init=False, default=False)
    _active: bool = field(init=False, default=False)
    _listener: keyboard.Listener | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        parsed = keyboard.HotKey.parse(self.key)
        if len(parsed) != 1:
            raise ValueError(
                f"hotkey must be a single key, got {self.key!r} -> {parsed!r}"
            )
        self._target = _promote(parsed[0])

    def _matches(self, key: keyboard.Key | keyboard.KeyCode | None) -> bool:
        return key is not None and key == self._target

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if not self._matches(key):
            return
        if self.mode is Mode.PUSH_TO_TALK:
            if self._pressed:
                return  # swallow OS key auto-repeat
            self._pressed = True
            self.on_start()
        else:
            self._active = not self._active
            (self.on_start if self._active else self.on_stop)()

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if not self._matches(key):
            return
        if self.mode is Mode.PUSH_TO_TALK and self._pressed:
            self._pressed = False
            self.on_stop()

    def start(self) -> None:
        if self._listener is not None:
            return
        self._listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        )
        self._listener.start()
        log.info("hotkey listener started: key=%s mode=%s", self.key, self.mode.value)

    def stop(self) -> None:
        if self._listener is None:
            return
        self._listener.stop()
        self._listener = None

    def join(self) -> None:
        if self._listener is not None:
            self._listener.join()


def _demo() -> None:
    """Hold the hotkey; press/release timings print to stdout."""
    import time

    t_down: list[float] = []

    def on_start() -> None:
        t_down.append(time.monotonic())
        print(f"[{time.strftime('%H:%M:%S')}] key down")

    def on_stop() -> None:
        held_ms = (time.monotonic() - t_down.pop()) * 1000 if t_down else 0.0
        print(f"[{time.strftime('%H:%M:%S')}] key up   (held {held_ms:.0f} ms)")

    listener = HotkeyListener(
        key="<ctrl_r>",
        mode=Mode.PUSH_TO_TALK,
        on_start=on_start,
        on_stop=on_stop,
    )
    print("Hold Right-Ctrl to trigger; Ctrl-C to quit.")
    listener.start()
    try:
        listener.join()
    except KeyboardInterrupt:
        listener.stop()


if __name__ == "__main__":
    _demo()
