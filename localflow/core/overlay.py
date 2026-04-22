"""Recording overlay — rounded pill at bottom-center with reactive waveform.

Tkinter-based. Uses the X11 Shape extension (python-xlib) to clip the window
to a true rounded-pill shape on Linux; falls back to a rectangular window
elsewhere. Thread-safe: show/hide/mode changes from any thread are marshalled
to the Tk main thread via after_idle().
"""
from __future__ import annotations

import logging
import math
import time
import tkinter as tk
from typing import Callable, Optional

log = logging.getLogger(__name__)


class Overlay:
    W = 140
    H = 40
    BG = "#141414"
    BAR_REC = "#ff3b30"
    BAR_PROC = "#ffc400"
    BOTTOM_MARGIN = 80
    FRAME_MS = 33  # ~30 fps

    N_BARS = 11
    BAR_W = 3
    BAR_GAP = 4
    BAR_MIN_H = 3
    BAR_MAX_H = 24

    def __init__(self, level_fn: Optional[Callable[[], float]] = None) -> None:
        self._level_fn = level_fn or (lambda: 0.0)

        self.root = tk.Tk()
        self.root.title("localflow")
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.configure(bg=self.BG)

        self.canvas = tk.Canvas(
            self.root,
            width=self.W, height=self.H,
            bg=self.BG, bd=0, highlightthickness=0,
        )
        self.canvas.pack()

        self._create_bars()
        self._position()
        self._apply_rounded_shape()

        self._mode = "hidden"  # recording | processing | hidden
        self._after_id: Optional[str] = None
        self._smoothed = [0.0] * self.N_BARS
        self._t_start = time.monotonic()

    def _create_bars(self) -> None:
        self.bars = []
        total_w = self.N_BARS * self.BAR_W + (self.N_BARS - 1) * self.BAR_GAP
        x0 = (self.W - total_w) // 2
        cy = self.H // 2
        for i in range(self.N_BARS):
            x = x0 + i * (self.BAR_W + self.BAR_GAP)
            bar = self.canvas.create_rectangle(
                x, cy - self.BAR_MIN_H // 2,
                x + self.BAR_W, cy + self.BAR_MIN_H // 2,
                fill=self.BAR_REC, outline="",
            )
            self.bars.append(bar)

    def _position(self) -> None:
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - self.W) // 2
        y = sh - self.H - self.BOTTOM_MARGIN
        self.root.geometry(f"{self.W}x{self.H}+{x}+{y}")
        self.root.update_idletasks()

    def _apply_rounded_shape(self) -> None:
        """Clip the window to a rounded-pill shape using the X11 Shape extension.

        Pure Python via python-xlib. Silently no-ops on non-X11 platforms or
        if the extension is unavailable — in that case the window stays
        rectangular but still looks OK.
        """
        try:
            from Xlib import display as _display
            from Xlib.ext import shape as _shape
        except Exception as e:
            log.info("python-xlib unavailable, skipping rounded shape: %s", e)
            return
        try:
            wid = self.root.winfo_id()
            d = _display.Display()
            win = d.create_resource_object("window", wid)
            W, H = self.W, self.H
            r = H // 2  # full semicircle caps → proper pill
            pix = win.create_pixmap(W, H, 1)
            gc = pix.create_gc(foreground=0, background=0)
            # Clear to 0 (transparent).
            pix.fill_rectangle(gc, 0, 0, W, H)
            # Draw rounded rect = horizontal band + vertical band + 4 corner disks.
            gc.change(foreground=1)
            pix.fill_rectangle(gc, r, 0, W - 2 * r, H)
            pix.fill_rectangle(gc, 0, r, W, H - 2 * r)
            full = 360 * 64
            pix.fill_arc(gc, 0, 0, 2 * r, 2 * r, 0, full)
            pix.fill_arc(gc, W - 2 * r, 0, 2 * r, 2 * r, 0, full)
            pix.fill_arc(gc, 0, H - 2 * r, 2 * r, 2 * r, 0, full)
            pix.fill_arc(gc, W - 2 * r, H - 2 * r, 2 * r, 2 * r, 0, full)
            win.shape_mask(_shape.SO.Set, _shape.SK.Bounding, 0, 0, pix)
            d.sync()
            pix.free()
            d.close()
            log.info("overlay: applied rounded shape %dx%d r=%d", W, H, r)
        except Exception as e:
            log.warning("overlay: failed to apply rounded shape: %s", e)

    def _set_bar_height(self, bar: int, h: float) -> None:
        cy = self.H // 2
        x0, _, x1, _ = self.canvas.coords(bar)
        h = max(self.BAR_MIN_H, min(self.BAR_MAX_H, h))
        self.canvas.coords(bar, x0, cy - h / 2, x1, cy + h / 2)

    def _render_recording(self) -> None:
        level = max(0.0, min(1.0, self._level_fn()))
        level = min(1.0, level * 1.8)  # boost — normal speech peaks ~0.3
        t = time.monotonic() - self._t_start
        half = (self.N_BARS - 1) / 2
        idle = 0.10 + 0.05 * math.sin(t * 2.2)
        effective = max(level, idle)
        for i, bar in enumerate(self.bars):
            w = 1.0 - abs(i - half) / half
            weight = 0.45 + 0.55 * w
            jitter = 0.55 + 0.45 * math.sin(t * 9.5 + i * 0.7)
            target = effective * weight * jitter
            cur = self._smoothed[i]
            k = 0.55 if target > cur else 0.22
            cur = cur + (target - cur) * k
            self._smoothed[i] = cur
            h = self.BAR_MIN_H + (self.BAR_MAX_H - self.BAR_MIN_H) * cur
            self._set_bar_height(bar, h)

    def _render_processing(self) -> None:
        t = time.monotonic() - self._t_start
        half = (self.N_BARS - 1) / 2
        for i, bar in enumerate(self.bars):
            phase = t * 4.8 - i * 0.55
            amp = 0.5 + 0.5 * math.sin(phase)
            w = 1.0 - abs(i - half) / half
            weight = 0.55 + 0.45 * w
            h = self.BAR_MIN_H + (self.BAR_MAX_H - self.BAR_MIN_H) * amp * weight
            self._set_bar_height(bar, h)

    def _tick(self) -> None:
        if self._mode == "recording":
            self._render_recording()
        elif self._mode == "processing":
            self._render_processing()
        if self._mode != "hidden":
            self._after_id = self.root.after(self.FRAME_MS, self._tick)

    def _cancel(self) -> None:
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None

    def _apply_mode(self, mode: str) -> None:
        self._cancel()
        self._mode = mode
        if mode == "hidden":
            self.root.withdraw()
            return
        color = self.BAR_REC if mode == "recording" else self.BAR_PROC
        for b in self.bars:
            self.canvas.itemconfigure(b, fill=color)
        if mode == "recording":
            self._smoothed = [0.0] * self.N_BARS
        self._t_start = time.monotonic()
        self.root.deiconify()
        self.root.lift()
        self._tick()

    def show_recording(self) -> None:
        self.root.after_idle(lambda: self._apply_mode("recording"))

    def show_processing(self) -> None:
        self.root.after_idle(lambda: self._apply_mode("processing"))

    def hide(self) -> None:
        self.root.after_idle(lambda: self._apply_mode("hidden"))

    def quit(self) -> None:
        self.root.after_idle(self.root.quit)

    def mainloop(self) -> None:
        self.root.mainloop()
