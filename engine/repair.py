from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from engine import install
from engine.paths import prefix_dir, user_state_dir

ProgressFn = Callable[[float, str], None]

# Irreducible user state (disposable prefix model)
USER_STATE_GLOBS = [
    "Normal.dotm",
    "Custom.dic",
    "**/Microsoft/Office/**/*.xml",
]


def backup_user_state(on_progress: ProgressFn | None = None) -> Path:
    if on_progress:
        on_progress(0.1, "Saving your templates and settings…")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = user_state_dir() / stamp
    backup.mkdir(parents=True, exist_ok=True)

    prefix = prefix_dir()
    search_roots = [
        prefix / "drive_c/users",
        prefix / "drive_c/Users",
    ]
    copied = 0
    for root in search_roots:
        if not root.is_dir():
            continue
        for user_dir in root.iterdir():
            if not user_dir.is_dir():
                continue
            for name in ("Normal.dotm", "Custom.dic"):
                for hit in user_dir.rglob(name):
                    rel = hit.relative_to(prefix)
                    dest = backup / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(hit, dest)
                    copied += 1
    if on_progress:
        on_progress(0.25, f"Saved {copied} item(s).")
    return backup


def restore_user_state(backup: Path, on_progress: ProgressFn | None = None) -> None:
    if not backup.is_dir():
        return
    if on_progress:
        on_progress(0.85, "Restoring your templates and settings…")
    prefix = prefix_dir()
    for src in backup.rglob("*"):
        if src.is_file():
            rel = src.relative_to(backup)
            dest = prefix / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def rebuild_prefix(on_progress: ProgressFn | None = None) -> None:
    backup = backup_user_state(on_progress)
    prefix = prefix_dir()
    if on_progress:
        on_progress(0.4, "Repairing Office installation…")
    if prefix.exists():
        shutil.rmtree(prefix)
    install.create_prefix(on_progress)
    install.install_office_odt(on_progress=on_progress)
    restore_user_state(backup, on_progress)
    if on_progress:
        on_progress(1.0, "Repair complete.")
