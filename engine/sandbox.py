from __future__ import annotations

import os
import shutil
from pathlib import Path

from engine.paths import data_dir, granted_folders_path, prefix_dir, wine_binary


def sandbox_available() -> bool:
    if not shutil.which("bwrap"):
        return False
    import subprocess

    try:
        p = subprocess.run(
            ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "true"],
            capture_output=True,
            timeout=5,
        )
        return p.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _granted_folders() -> list[Path]:
    path = granted_folders_path()
    if not path.is_file():
        defaults = [
            Path.home() / "Documents",
            Path.home() / "Downloads",
            Path.home() / "Desktop",
            Path.home() / "Pictures",
        ]
        return [p for p in defaults if p.is_dir()]
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[Path] = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(Path(line).expanduser())
    return out


def build_bwrap_argv(wine_cmd: list[str]) -> list[str]:
    """Wrap wine_cmd with bubblewrap allowlist. See config/granted-folders policy."""
    prefix = prefix_dir()
    runtime = wine_binary().parent.parent
    data = data_dir()
    xdg = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))

    argv = [
        "bwrap",
        "--unshare-all",
        "--die-with-parent",
        "--ro-bind",
        "/usr",
        "/usr",
        "--ro-bind",
        "/lib",
        "/lib",
        "--ro-bind",
        "/lib64",
        "/lib64",
        "--ro-bind",
        "/bin",
        "/bin",
        "--ro-bind",
        "/sbin",
        "/sbin",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--setenv",
        "TMPDIR",
        "/tmp",
        "--ro-bind",
        str(runtime),
        str(runtime),
        "--bind",
        str(prefix),
        str(prefix),
        "--bind",
        str(data / "cache"),
        str(data / "cache"),
    ]

    if xdg.is_dir():
        argv.extend(["--bind", str(xdg), str(xdg)])

    for folder in _granted_folders():
        if folder.is_dir():
            argv.extend(["--bind", str(folder), str(folder)])

    argv.append("--")
    argv.extend(wine_cmd)
    return argv
