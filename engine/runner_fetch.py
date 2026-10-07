from __future__ import annotations

import hashlib
import os
import shutil
import tarfile
import urllib.request
from pathlib import Path
from typing import Callable

from engine.paths import data_dir

# Pin your runner on GitHub Releases or another HTTPS host.
DEFAULT_RUNNER_URL = os.environ.get(
    "MYOFFICE_RUNNER_URL",
    "https://example.com/myoffice/wine-runner-placeholder.tar.xz",
)
DEFAULT_RUNNER_SHA256 = os.environ.get("MYOFFICE_RUNNER_SHA256", "")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_runner(
    url: str = DEFAULT_RUNNER_URL,
    expected_sha256: str = DEFAULT_RUNNER_SHA256,
    on_progress: Callable[[str], None] | None = None,
) -> Path:
    cache = data_dir() / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / "wine-runner.tar.xz"

    def log(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    log("Downloading Office components support files…")
    req = urllib.request.Request(url, headers={"User-Agent": "MyOffice-Setup/1.0"})
    with urllib.request.urlopen(req, timeout=600) as resp, dest.open("wb") as out:
        shutil.copyfileobj(resp, out)

    if expected_sha256:
        digest = sha256_file(dest)
        if digest.lower() != expected_sha256.lower():
            dest.unlink(missing_ok=True)
            raise RuntimeError(
                "Download verification failed. The file may be corrupted or tampered with."
            )

    runtimes = data_dir() / "runtimes"
    runtimes.mkdir(parents=True, exist_ok=True)
    version_dir = runtimes / "pinned"
    if version_dir.exists():
        shutil.rmtree(version_dir)
    version_dir.mkdir(parents=True)

    log("Extracting support files…")
    with tarfile.open(dest, "r:*") as tf:
        tf.extractall(version_dir, filter="data")

    # Expect tarball with top-level bin/wine or single directory.
    wine_candidates = list(version_dir.rglob("bin/wine"))
    if not wine_candidates:
        raise RuntimeError("Runner archive did not contain bin/wine.")

    root = wine_candidates[0].parent.parent
    current = runtimes / "current"
    if current.is_symlink() or current.exists():
        if current.is_symlink():
            current.unlink()
        elif current.is_dir():
            shutil.rmtree(current)
        else:
            current.unlink()
    current.symlink_to(root.resolve())
    return wine_candidates[0]
