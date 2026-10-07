#!/usr/bin/env python3
"""Exec helper: optional bwrap wrap then replace process with Wine."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.sandbox import build_bwrap_argv, sandbox_available  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        sys.stderr.write("usage: myoffice-exec-wine.py wine binary [args...]\n")
        sys.exit(2)
    wine_cmd = sys.argv[1:]
    use_bwrap = os.environ.get("MYOFFICE_USE_BWRAP", "1") == "1"
    if use_bwrap and sandbox_available():
        os.execvp("bwrap", build_bwrap_argv(wine_cmd))
    os.execvp(wine_cmd[0], wine_cmd)


if __name__ == "__main__":
    main()
