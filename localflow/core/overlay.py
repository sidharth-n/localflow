"""Recording overlay — small pill at bottom-center of screen.

Tkinter-based (no extra deps). Works on X11 and macOS.
Thread-safe: show/hide from any thread; UI updates are marshalled to the
Tk main thread via after_idle().
"""
from __future__ import annotations

import logging
import tkinter as tk

log = logging.getLogger(__name__)


class Overlay:
    W = 180
    H = 44
    BG = "#151515"
    DOT_R = 7
    DOT_ACTIVE = "#ff3b30"
    DOT_DIM = "#4a0f0c"
    DOT_PROCESSING = "#ffc400"
    TEXT_COLOR = "#f0f0f0"
    PULSE_MS = 450
    BOTTOM_MARGIN = 80

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("localflow")
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)
        self.root.configure(bg=self.BG)

        self.canvas = tk.Canvas(
            self.root,
            width=self.W,
            height=self.H,
            bg=self.BG,
            bd=0,
            highlightthickness=0,
        )
        self.canvas.pack()

        cx = 22
        cy = self.H // 2
        self.dot = self.canvas.create_oval(
            cx - self.DOT_R, cy - self.DOT_R,
            cx + self.DOT_R, cy + self.DOT_R,
            fill=self.DOT_ACTIVE,
            outline="",
        )
        self.label = self.canvas.create_text(
            44, cy,
            anchor="w",
            text="Recording",
            fill=self.TEXT_COLOR,
            font=("Helvetica", 12, "bold"),
        )

        self._position()
        self._pulse_bright = True
        self._pulse_after: str | None = None

    def _position(self) -> None:
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - self.W) // 2
        y = sh - self.H - self.BOTTOM_MARGIN
        self.root.geometry(f"{self.W}x{self.H}+{x}+{y}")

    def _tick_pulse(self) -> None:
        color = self.DOT_ACTIVE if self._pulse_bright else self.DOT_DIM
        self.canvas.itemconfigure(self.dot, fill=color)
        self._pulse_bright = not self._pulse_bright
        self._pulse_after = self.root.after(self.PULSE_MS, self._tick_pulse)

    def _stop_pulse(self) -> None:
        if self._pulse_after is not None:
            self.root.after_cancel(self._pulse_after)
            self._pulse_after = None

    def _show_recording(self) -> None:
        self._stop_pulse()
        self.canvas.itemconfigure(self.dot, fill=self.DOT_ACTIVE)
        self.canvas.itemconfigure(self.label, text="Recording")
        self.root.deiconify()
        self.root.lift()
        self._pulse_bright = False
        self._tick_pulse()

    def _show_processing(self) -> None:
        self._stop_pulse()
        self.canvas.itemconfigure(self.dot, fill=self.DOT_PROCESSING)
        self.canvas.itemconfigure(self.label, text="Processing…")

    def _hide(self) -> None:
        self._stop_pulse()
        self.root.withdraw()

    # Thread-safe entry points. Safe to call from the pynput listener thread.
    def show_recording(self) -> None:
        self.root.after_idle(self._show_recording)

    def show_processing(self) -> None:
        self.root.after_idle(self._show_processing)

    def hide(self) -> None:
        self.root.after_idle(self._hide)

    def quit(self) -> None:
        self.root.after_idle(self.root.quit)

    def mainloop(self) -> None:
        self.root.mainloop()
