"""Microphone capture.

Start/stop recorder over the default input device. start() opens an
InputStream; stop() closes it and returns the full int16 mono buffer.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import sounddevice as sd

log = logging.getLogger(__name__)


@dataclass
class Capture:
    sample_rate: int = 16000
    channels: int = 1
    chunk_ms: int = 30

    _stream: sd.InputStream | None = field(init=False, default=None, repr=False)
    _buffers: list[np.ndarray] = field(init=False, default_factory=list, repr=False)

    @property
    def blocksize(self) -> int:
        return self.sample_rate * self.chunk_ms // 1000

    def _callback(self, indata, frames, time_info, status) -> None:  # noqa: ARG002
        if status:
            log.warning("input stream status: %s", status)
        self._buffers.append(indata.copy())

    def start(self) -> None:
        if self._stream is not None:
            return
        self._buffers.clear()
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            blocksize=self.blocksize,
            callback=self._callback,
        )
        self._stream.start()
        log.info(
            "capture started: %d Hz, %d ch, %d ms chunks",
            self.sample_rate, self.channels, self.chunk_ms,
        )

    def stop(self) -> np.ndarray:
        if self._stream is None:
            return np.zeros(0, dtype=np.int16)
        self._stream.stop()
        self._stream.close()
        self._stream = None
        if not self._buffers:
            return np.zeros(0, dtype=np.int16)
        audio = np.concatenate(self._buffers, axis=0)
        if self.channels == 1:
            audio = audio.reshape(-1)
        self._buffers.clear()
        return audio


def _demo() -> None:
    """Hold Right-Ctrl to record; releases write /tmp/localflow-capture.wav."""
    import os
    import tempfile
    import time
    import wave

    from localflow.core.hotkey import HotkeyListener, Mode

    cap = Capture()
    out_path = os.path.join(tempfile.gettempdir(), "localflow-capture.wav")

    def on_start() -> None:
        print(f"[{time.strftime('%H:%M:%S')}] recording…")
        cap.start()

    def on_stop() -> None:
        audio = cap.stop()
        secs = len(audio) / cap.sample_rate
        print(
            f"[{time.strftime('%H:%M:%S')}] captured {len(audio)} samples ({secs:.2f} s)"
        )
        with wave.open(out_path, "wb") as w:
            w.setnchannels(cap.channels)
            w.setsampwidth(2)
            w.setframerate(cap.sample_rate)
            w.writeframes(audio.tobytes())
        print(f"wrote {out_path}")

    listener = HotkeyListener(
        key="<ctrl_r>",
        mode=Mode.PUSH_TO_TALK,
        on_start=on_start,
        on_stop=on_stop,
    )
    print("Hold Right-Ctrl to record. Ctrl-C to quit.")
    listener.start()
    try:
        listener.join()
    except KeyboardInterrupt:
        listener.stop()


if __name__ == "__main__":
    _demo()
