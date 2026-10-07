from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable

from engine.paths import (
    config_dir,
    data_dir,
    install_root,
    launch_env_path,
    logs_dir,
    prefix_dir,
    wine_binary,
)
from engine.recipe import load_recipe
from engine.runner_fetch import download_runner

ProgressFn = Callable[[float, str], None]


def _log_path() -> Path:
    logs_dir().mkdir(parents=True, exist_ok=True)
    return logs_dir() / "install.log"


def _append_log(line: str) -> None:
    with _log_path().open("a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")


def _run_wine(args: list[str], env: dict[str, str]) -> None:
    wine = wine_binary()
    if not wine.is_file():
        raise RuntimeError("Support runtime is missing. Run system check again.")
    cmd = [str(wine), *args]
    _append_log("$ " + " ".join(cmd))
    p = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if p.stdout:
        _append_log(p.stdout)
    if p.stderr:
        _append_log(p.stderr)
    if p.returncode != 0:
        raise RuntimeError(f"Setup step failed (code {p.returncode}). See install.log.")


def ensure_layout(on_progress: ProgressFn | None = None) -> None:
    def prog(f: float, m: str) -> None:
        if on_progress:
            on_progress(f, m)

    prog(0.05, "Preparing folders…")
    for d in (data_dir(), prefix_dir(), config_dir(), data_dir() / "cache" / "odt"):
        d.mkdir(parents=True, exist_ok=True)

    example = install_root() / "config" / "launch.env.example"
    if example.is_file() and not launch_env_path().is_file():
        shutil.copy(example, launch_env_path())


def ensure_runner(on_progress: ProgressFn | None = None) -> None:
    def prog(f: float, m: str) -> None:
        if on_progress:
            on_progress(f, m)

    if wine_binary().is_file():
        prog(0.25, "Support files already present.")
        return

    def msg(m: str) -> None:
        prog(0.15, m)

    download_runner(on_progress=msg)
    prog(0.3, "Support files ready.")


def create_prefix(on_progress: ProgressFn | None = None) -> None:
    def prog(f: float, m: str) -> None:
        if on_progress:
            on_progress(f, m)

    prefix = prefix_dir()
    env = os.environ.copy()
    env["WINEPREFIX"] = str(prefix)
    env["WINEDEBUG"] = "-all"
    env["WINEDLLOVERRIDES"] = "mscoree,mshtml=;winemenubuilder.exe=d"

    if (prefix / "system.reg").is_file():
        prog(0.4, "Using existing installation folder.")
        return

    prog(0.35, "Creating application environment…")
    env["WINEARCH"] = "win64"
    _run_wine(["wineboot", "--init"], env)
    _run_wine(["reg", "add", r"HKCU\Software\Wine", "/v", "ShowWineMenuSync", "/d", "0", "/f"], env)
    prog(0.45, "Application environment ready.")


def install_office_odt(
    odt_setup: Path | None = None,
    on_progress: ProgressFn | None = None,
) -> None:
    def prog(f: float, m: str) -> None:
        if on_progress:
            on_progress(f, m)

    odt_dir = data_dir() / "cache" / "odt"
    setup = odt_setup or (odt_dir / "setup.exe")
    try:
        recipe = load_recipe()
        rel = recipe.get("media", {}).get("odt_configuration", "config/odt/configuration.xml")
        config_src = install_root() / rel
    except FileNotFoundError:
        config_src = install_root() / "config" / "odt" / "configuration.xml"

    if not setup.is_file():
        raise RuntimeError(
            "Office installer not found. Use “Browse for installer” or complete ODT download first."
        )

    shutil.copy(config_src, odt_dir / "configuration.xml")
    env = os.environ.copy()
    env["WINEPREFIX"] = str(prefix_dir())
    env["WINEDEBUG"] = "-all"
    env["WINEDLLOVERRIDES"] = "mscoree,mshtml=;winemenubuilder.exe=d"

    prog(0.5, "Installing Microsoft Office (this may take 20–40 minutes)…")
    wine = wine_binary()
    cmd = [str(wine), str(setup), "/configure", "configuration.xml"]
    _append_log("$ " + " ".join(cmd))
    p = subprocess.Popen(
        cmd,
        cwd=str(odt_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert p.stdout is not None
    for line in p.stdout:
        _append_log(line)
    code = p.wait()
    if code != 0:
        raise RuntimeError("Office installation failed. See install.log.")
    prog(0.9, "Office installation finished.")


def run_full_install(
    odt_setup: Path | None = None,
    on_progress: ProgressFn | None = None,
) -> None:
    ensure_layout(on_progress)
    ensure_runner(on_progress)
    create_prefix(on_progress)
    install_office_odt(odt_setup, on_progress)
    if on_progress:
        on_progress(1.0, "Setup complete.")
