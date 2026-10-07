from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from engine.paths import data_dir, install_root, prefix_dir, wine_binary

APP_IDS = {
    "word": ("Word", "WINWORD.EXE", "myoffice-word"),
    "excel": ("Excel", "EXCEL.EXE", "myoffice-excel"),
    "powerpoint": ("PowerPoint", "POWERPNT.EXE", "myoffice-powerpoint"),
}

MIME_ASSOCIATIONS = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "word",
    "application/msword": "word",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "excel",
    "application/vnd.ms-excel": "excel",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "powerpoint",
    "application/vnd.ms-powerpoint": "powerpoint",
}


def _launcher_path() -> Path:
    return install_root() / "bin" / "myoffice-launch"


def _icons_dir() -> Path:
    d = data_dir() / "icons"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _applications_dir() -> Path:
    d = Path.home() / ".local" / "share" / "applications"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _mimeapps_path() -> Path:
    d = Path.home() / ".config"
    d.mkdir(parents=True, exist_ok=True)
    return d / "mimeapps.list"


def disable_winemenubuilder() -> None:
    prefix = prefix_dir()
    if not (prefix / "system.reg").is_file():
        return
    wine = wine_binary()
    if not wine.is_file():
        return
    env = os.environ.copy()
    env["WINEPREFIX"] = str(prefix)
    env["WINEDEBUG"] = "-all"
    subprocess.run(
        [str(wine), "reg", "add", r"HKCU\Software\Wine", "/v", "ShowWineMenuSync", "/d", "0", "/f"],
        env=env,
        capture_output=True,
    )


def _render_desktop(app_id: str, title: str, wm_class: str) -> str:
    launch = _launcher_path()
    icon = _icons_dir() / f"{app_id}.png"
    icon_line = f"Icon={icon}\n" if icon.is_file() else ""
    return f"""[Desktop Entry]
Type=Application
Name={title}
Comment=Open {title}
Exec={launch} {app_id} %F
Terminal=false
Categories=Office;WordProcessor;
StartupWMClass={wm_class}
MimeType=
{icon_line}"""


def install_desktop_entries() -> list[Path]:
    disable_winemenubuilder()
    written: list[Path] = []
    apps = _applications_dir()
    for app_id, (title, _exe, wm_class) in APP_IDS.items():
        content = _render_desktop(app_id, title, wm_class)
        path = apps / f"myoffice-{app_id}.desktop"
        path.write_text(content, encoding="utf-8")
        os.chmod(path, 0o755)
        written.append(path)

    settings_path = apps / "myoffice-settings.desktop"
    settings_path.write_text(
        f"""[Desktop Entry]
Type=Application
Name=MyOffice Settings
Comment=Repair Office and save diagnostic reports
Exec={install_root() / "bin" / "myoffice-settings"}
Terminal=false
Categories=Settings;
""",
        encoding="utf-8",
    )
    os.chmod(settings_path, 0o755)
    written.append(settings_path)
    return written


def install_mime_associations() -> None:
    mime_path = _mimeapps_path()
    existing = mime_path.read_text(encoding="utf-8") if mime_path.is_file() else ""
    lines = existing.splitlines()
    if "[Default Applications]" not in existing:
        lines.extend(["", "[Default Applications]"])
    defaults = {line.split("=")[0]: line for line in lines if "=" in line and not line.startswith("[")}

    section_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "[Default Applications]":
            section_idx = i
            break

    new_defaults: dict[str, str] = {}
    for mime, app_id in MIME_ASSOCIATIONS.items():
        new_defaults[mime] = f"myoffice-{app_id}.desktop"

    if section_idx is not None:
        # Append missing mime defaults after section header
        insert_at = section_idx + 1
        for mime, desktop in new_defaults.items():
            entry = f"{mime}={desktop}"
            if entry not in lines and mime not in str(defaults):
                lines.insert(insert_at, entry)
                insert_at += 1
    mime_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_placeholder_icons() -> None:
    """Copy bundled icons if present."""
    src = install_root() / "integration" / "icons"
    if not src.is_dir():
        return
    for png in src.glob("*.png"):
        shutil.copy(png, _icons_dir() / png.name)
