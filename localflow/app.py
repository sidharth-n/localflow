"""localflow CLI entry point.

M2: hotkey → capture → Moonshine STT → polish LLM → clipboard paste.
"""
from __future__ import annotations

import logging
import sys
import time

import click

from localflow import __version__
from localflow.core import config as cfg
from localflow.core.capture import Capture
from localflow.core.hotkey import HotkeyListener, Mode
from localflow.core.inject import linux_x11
from localflow.core.polish.dictionary import looks_clean, pre_polish
from localflow.core.stt.moonshine_onnx import MoonshineSTT

log = logging.getLogger("localflow")


def _run() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    c = cfg.load()

    capture = Capture(
        sample_rate=c["audio"]["sample_rate"],
        channels=c["audio"]["channels"],
        chunk_ms=c["audio"]["chunk_ms"],
    )
    stt = MoonshineSTT(model=c["stt"]["model"])

    polish = None
    if c["polish"]["enabled"]:
        from localflow.core.polish.llamacpp import QwenPolish

        polish = QwenPolish(
            model_path=c["polish"]["model_path"],
            system_prompt=c["polish"]["system_prompt"],
            max_tokens=c["polish"]["max_tokens"],
            temperature=c["polish"]["temperature"],
        )

    restore_ms = c["inject"]["restore_clipboard_after_ms"]

    def on_start() -> None:
        log.info("recording")
        capture.start()

    def on_stop() -> None:
        t0 = time.monotonic()
        audio = capture.stop()
        t_cap = time.monotonic()
        raw = stt.transcribe(audio, sample_rate=capture.sample_rate)
        t_stt = time.monotonic()

        pre = pre_polish(raw) if raw else raw
        t_pre = time.monotonic()

        final = pre
        skipped = False
        if polish and pre:
            if looks_clean(pre):
                skipped = True
            else:
                try:
                    final = polish.polish(pre)
                except Exception as e:
                    log.warning("polish failed, pasting pre-polished transcript: %s", e)
                    final = pre
        t_pol = time.monotonic()

        linux_x11.paste(final, restore_after_ms=restore_ms)
        t_paste = time.monotonic()

        log.info(
            "pipeline: %d samples | cap %.0f | stt %.0f | pre %.0f | llm %s | paste %.0f (ms)",
            len(audio),
            (t_cap - t0) * 1000,
            (t_stt - t_cap) * 1000,
            (t_pre - t_stt) * 1000,
            "SKIP" if skipped else f"{(t_pol - t_pre) * 1000:.0f}",
            (t_paste - t_pol) * 1000,
        )
        if raw != final:
            log.info("  raw : %r", raw)
            if pre != raw and pre != final:
                log.info("  pre : %r", pre)
            log.info("  out : %r", final)
        else:
            log.info("  text: %r", final)

    listener = HotkeyListener(
        key=c["hotkey"]["key"],
        mode=Mode(c["hotkey"]["mode"]),
        on_start=on_start,
        on_stop=on_stop,
    )
    listener.start()
    log.info(
        "localflow %s ready — hold %s to dictate. Ctrl-C to quit.",
        __version__,
        c["hotkey"]["key"],
    )
    try:
        listener.join()
    except KeyboardInterrupt:
        listener.stop()
        log.info("bye")
    return 0


@click.command()
@click.version_option(__version__)
@click.option("--config", "-c", type=click.Path(), help="Path to config.yaml (unused until M4)")
def main(config: str | None) -> int:  # noqa: ARG001
    return _run()


if __name__ == "__main__":
    sys.exit(main())
