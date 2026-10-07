from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

from engine.paths import install_root


def load_recipe(name: str = "office365") -> dict[str, Any]:
    path = install_root() / "manifests" / f"{name}.toml"
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("rb") as f:
        return tomllib.load(f)


def verify_recipe_signature(recipe_path: Path, sig_path: Path, public_key_path: Path) -> bool:
    """
    v0.2: verify minisign/ed25519 signature. Placeholder returns True if no sig file.
    """
    if not sig_path.is_file():
        return True
    if not public_key_path.is_file():
        return False
    digest = hashlib.sha256(recipe_path.read_bytes()).hexdigest()
    meta = json.loads(sig_path.read_text(encoding="utf-8"))
    return meta.get("sha256") == digest


def landlock_fallback_note() -> str:
    return (
        "If bubblewrap is blocked on your system, a future update will use kernel "
        "Landlock rules instead. Office can run without sandbox until then."
    )
