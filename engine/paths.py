from __future__ import annotations

import os
from pathlib import Path


def install_root() -> Path:
    env = os.environ.get("MYOFFICE_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    env = os.environ.get("MYOFFICE_DATA")
    if env:
        return Path(env).expanduser().resolve()
    return Path.home() / ".local" / "share" / "myoffice"


def prefix_dir() -> Path:
    env = os.environ.get("MYOFFICE_PREFIX")
    if env:
        return Path(env).expanduser().resolve()
    return data_dir() / "prefixes" / "office"


def wine_binary() -> Path:
    env = os.environ.get("MYOFFICE_WINE")
    if env:
        return Path(env).expanduser().resolve()
    return data_dir() / "runtimes" / "current" / "bin" / "wine"


def logs_dir() -> Path:
    return data_dir() / "logs"


def user_state_dir() -> Path:
    return data_dir() / "user-state"


def config_dir() -> Path:
    return data_dir() / "config"


def launch_env_path() -> Path:
    return config_dir() / "launch.env"


def granted_folders_path() -> Path:
    return config_dir() / "granted-folders.txt"
