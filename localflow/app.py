"""localflow CLI entry point.

Currently a stub — M0 wires up hotkey → mic → dummy STT → clipboard paste.
"""
from __future__ import annotations

import sys

import click

from localflow import __version__


@click.command()
@click.version_option(__version__)
@click.option("--config", "-c", type=click.Path(), help="Path to config.yaml")
def main(config: str | None) -> int:
    click.echo(f"localflow {__version__} — pre-alpha, M0 not yet implemented.")
    click.echo("See SESSION.md for roadmap.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
