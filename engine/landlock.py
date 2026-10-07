"""
v0.2: Landlock LSM fallback when bubblewrap/user namespaces are blocked (e.g. Ubuntu 24.04+).

Not used in v0 — launcher runs without sandbox if bwrap fails. Implement apply_landlock(rules)
and integrate from engine.sandbox when doctor reports bwrap FAIL and kernel >= 5.13.
"""

from __future__ import annotations


def landlock_available() -> bool:
    return False


def apply_landlock_read_write(allowed_paths: list[str]) -> None:
    raise NotImplementedError("Landlock backend planned for v0.2")
