from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from engine.paths import data_dir, prefix_dir, wine_binary


@dataclass
class Check:
    name: str
    status: str  # PASS | FAIL | WARN
    detail: str
    hint: str = ""


def _run(cmd: list[str], timeout: int = 15) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return 127, str(e)


def check_linux() -> Check:
    uname = platform.uname()
    if uname.system != "Linux":
        return Check(
            "Linux",
            "FAIL",
            f"Detected {uname.system}",
            "MyOffice is designed for Linux (Mint/Ubuntu).",
        )
    return Check("Linux", "PASS", uname.version)


def check_arch() -> Check:
    machine = platform.machine()
    if machine in ("x86_64", "amd64"):
        return Check("Architecture", "PASS", machine)
    return Check(
        "Architecture",
        "FAIL",
        machine,
        "A 64-bit PC (x86_64) is required.",
    )


def check_disk() -> Check:
    need_gb = 15
    try:
        usage = shutil.disk_usage(data_dir())
        free_gb = usage.free / (1024**3)
        if free_gb >= need_gb:
            return Check("Free disk space", "PASS", f"{free_gb:.1f} GB free")
        return Check(
            "Free disk space",
            "FAIL",
            f"{free_gb:.1f} GB free",
            f"At least {need_gb} GB free space is recommended.",
        )
    except OSError as e:
        return Check("Free disk space", "WARN", str(e))


def check_network() -> Check:
    try:
        socket.getaddrinfo("www.microsoft.com", 443)
        return Check("Internet", "PASS", "Can reach Microsoft services")
    except OSError:
        return Check(
            "Internet",
            "FAIL",
            "Cannot reach www.microsoft.com",
            "Connect to the internet for installation, or use an offline installer file.",
        )


def check_wine() -> Check:
    wine = wine_binary()
    if not wine.is_file():
        return Check(
            "Office support runtime",
            "WARN",
            "Not installed yet",
            "Complete setup to download required components.",
        )
    code, out = _run([str(wine), "--version"])
    if code != 0:
        return Check("Office support runtime", "FAIL", out or "wine --version failed")
    return Check("Office support runtime", "PASS", out.splitlines()[0] if out else "OK")


def check_prefix() -> Check:
    prefix = prefix_dir()
    if not (prefix / "system.reg").is_file():
        return Check(
            "Office installation",
            "WARN",
            "Not installed yet",
            "Run setup to install Word, Excel, and PowerPoint.",
        )
    apps = [
        prefix / "drive_c/Program Files/Microsoft Office/root/Office16/WINWORD.EXE",
        prefix / "drive_c/Program Files/Microsoft Office/Office16/WINWORD.EXE",
    ]
    for app in apps:
        if app.is_file():
            return Check("Office installation", "PASS", "Word found")
    return Check(
        "Office installation",
        "WARN",
        "Prefix exists but Word was not found",
        "Try Repair Office from Settings.",
    )


def check_session() -> Check:
    session = os.environ.get("XDG_SESSION_TYPE", "unknown")
    return Check("Desktop session", "PASS" if session else "WARN", session or "unknown")


def check_vulkan() -> Check:
    code, _ = _run(["vulkaninfo", "--summary"], timeout=8)
    if code == 0:
        return Check("Graphics (Vulkan)", "PASS", "Available")
    if (Path("/usr/share/vulkan") / "icd.d").exists() or Path("/etc/vulkan/icd.d").exists():
        return Check("Graphics (Vulkan)", "WARN", "Tools missing; drivers may still work")
    return Check(
        "Graphics (Vulkan)",
        "WARN",
        "Not detected",
        "Office will use basic graphics; this is usually fine.",
    )


def check_sandbox() -> Check:
    if not shutil.which("bwrap"):
        return Check(
            "Optional isolation",
            "WARN",
            "bubblewrap not installed",
            "Install bubblewrap for extra isolation, or continue without it.",
        )
    code, out = _run(
        [
            "bwrap",
            "--ro-bind",
            "/",
            "/",
            "--dev",
            "/dev",
            "--proc",
            "/proc",
            "true",
        ],
        timeout=5,
    )
    if code == 0:
        return Check("Optional isolation", "PASS", "bubblewrap works")
    return Check(
        "Optional isolation",
        "WARN",
        out[:200] if out else "bwrap test failed",
        "On some Ubuntu versions, isolation is limited; Office can still run.",
    )


def run_all_checks() -> list[Check]:
    return [
        check_linux(),
        check_arch(),
        check_disk(),
        check_network(),
        check_session(),
        check_vulkan(),
        check_sandbox(),
        check_wine(),
        check_prefix(),
    ]


def format_report(checks: list[Check] | None = None) -> str:
    checks = checks or run_all_checks()
    lines = [
        "MyOffice diagnostic",
        "─" * 40,
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Data: {data_dir()}",
        "",
    ]
    overall = "READY"
    for c in checks:
        lines.append(f"{c.name:<24} {c.status}")
        if c.detail:
            lines.append(f"  {c.detail}")
        if c.status == "FAIL":
            overall = "NOT READY"
        elif c.status == "WARN" and overall == "READY":
            overall = "READY (warnings)"
        if c.hint and c.status != "PASS":
            lines.append(f"  → {c.hint}")
        lines.append("")
    lines.append(f"Overall: {overall}")
    return "\n".join(lines)


def save_report(path: Path | None = None) -> Path:
    data_dir().mkdir(parents=True, exist_ok=True)
    default = data_dir() / "last-diagnostic.txt"
    target = path or default
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(format_report(), encoding="utf-8")
    return target


def main_cli() -> int:
    report = format_report()
    print(report)
    save_report()
    return 0 if "NOT READY" not in report else 1


if __name__ == "__main__":
    sys.exit(main_cli())
