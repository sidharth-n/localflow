"""localflow CLI entry point.

M0.4: hotkey (Right-Ctrl, hold) → mic capture → Moonshine ONNX STT → clipboard paste.
"""
from __future__ import annotations

import logging
import sys
import time

import click

from localflow import __version__
from localflow.core.capture import Capture
from localflow.core.hotkey import HotkeyListener, Mode
from localflow.core.inject import linux_x11
from localflow.core.stt.moonshine_onnx import MoonshineSTT

log = logging.getLogger("localflow")


def _run() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    capture = Capture()
    stt = MoonshineSTT()

    def on_start() -> None:
        log.info("recording")
        capture.start()

    def on_stop() -> None:
        t0 = time.monotonic()
        audio = capture.stop()
        t_capture = time.monotonic()
        text = stt.transcribe(audio, sample_rate=capture.sample_rate)
        t_stt = time.monotonic()
        linux_x11.paste(text)
        t_paste = time.monotonic()
        log.info(
            "pipeline: %d samples | capture-drain %.0f ms | stt %.0f ms | paste %.0f ms | text=%r",
            len(audio),
            (t_capture - t0) * 1000,
            (t_stt - t_capture) * 1000,
            (t_paste - t_stt) * 1000,
            text,
        )

    listener = HotkeyListener(
        key="<ctrl_r>",
        mode=Mode.PUSH_TO_TALK,
        on_start=on_start,
        on_stop=on_stop,
    )
    listener.start()
    log.info("localflow %s ready — hold Right-Ctrl to dictate. Ctrl-C to quit.", __version__)
    try:
        listener.join()
    except KeyboardInterrupt:
        listener.stop()
        log.info("bye")
    return 0


@click.command()
@click.version_option(__version__)
@click.option("--config", "-c", type=click.Path(), help="Path to config.yaml (unused at M0.3)")
def main(config: str | None) -> int:  # noqa: ARG001
    return _run()


if __name__ == "__main__":
    sys.exit(main())
