#!/usr/bin/env python3
"""GTK3 setup wizard for non-technical users."""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MYOFFICE_ROOT", str(ROOT))

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

from engine import install
from engine.diagnostics import run_all_checks
from integration.desktop import copy_placeholder_icons, install_desktop_entries, install_mime_associations


class SetupWizard(Gtk.Assistant):
    def __init__(self) -> None:
        super().__init__()
        self.set_title("MyOffice Setup")
        self.set_default_size(560, 420)
        self.set_wmclass("myoffice-setup", "MyOffice Setup")
        self.odt_path: Path | None = None
        self.checks_ok = False

        pages = [
            (self._page_welcome(), "Welcome"),
            (self._page_check(), "Check"),
            (self._page_account(), "Account"),
            (self._page_install(), "Install"),
            (self._page_done(), "Done"),
        ]
        for widget, title in pages:
            self.append_page(widget)
            self.set_page_title(widget, title)

        self.set_page_complete(self.get_nth_page(0), True)

    def _page_welcome(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin=24)
        title = Gtk.Label()
        title.set_markup("<big><b>Set up Word, Excel, and PowerPoint</b></big>")
        title.set_halign(Gtk.Align.START)
        body = Gtk.Label(
            label=(
                "This guide installs Microsoft Office on your Linux computer.\n"
                "You will sign in with your Microsoft account when Word opens."
            ),
            xalign=0,
            wrap=True,
        )
        box.pack_start(title, False, False, 0)
        box.pack_start(body, False, False, 0)
        return box

    def _page_check(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin=24)
        box.pack_start(Gtk.Label(label="Checking your computer…", xalign=0), False, False, 0)
        self.check_list = Gtk.ListBox()
        self.check_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(self.check_list)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        box.pack_start(scrolled, True, True, 0)
        self.check_summary = Gtk.Label(label="", xalign=0, wrap=True)
        box.pack_start(self.check_summary, False, False, 0)
        return box

    def _page_account(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin=24)
        box.pack_start(
            Gtk.Label(
                label="When Word opens, sign in with your work, school, or personal Microsoft account.",
                wrap=True,
                xalign=0,
            ),
            False,
            False,
            0,
        )
        link = Gtk.LinkButton(uri="https://www.microsoft.com/microsoft-365", label="About Microsoft 365")
        link.set_halign(Gtk.Align.START)
        box.pack_start(link, False, False, 0)

        offline_btn = Gtk.Button(label="Browse for Office installer file (offline)")
        offline_btn.connect("clicked", self._on_browse_odt)
        box.pack_start(offline_btn, False, False, 0)
        self.odt_label = Gtk.Label(label="Using online installation when available.", xalign=0)
        box.pack_start(self.odt_label, False, False, 0)
        return box

    def _page_install(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin=24)
        box.pack_start(
            Gtk.Label(
                label="Installing Office components.\nThis may take 20–40 minutes on slower computers.",
                wrap=True,
                xalign=0,
            ),
            False,
            False,
            0,
        )
        self.progress = Gtk.ProgressBar()
        self.progress.set_fraction(0.0)
        box.pack_start(self.progress, False, False, 0)
        self.install_status = Gtk.Label(label="Waiting to start…", xalign=0)
        box.pack_start(self.install_status, False, False, 0)
        return box

    def _page_done(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin=24)
        box.pack_start(
            Gtk.Label(
                label="Setup finished. Word, Excel, and PowerPoint are in your applications menu.",
                wrap=True,
                xalign=0,
            ),
            False,
            False,
            0,
        )
        open_btn = Gtk.Button(label="Open Word")
        open_btn.connect("clicked", self._on_open_word)
        box.pack_start(open_btn, False, False, 0)
        return box

    def _on_browse_odt(self, _btn: Gtk.Button) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Select Office installer (setup.exe)",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        if dialog.run() == Gtk.ResponseType.OK:
            self.odt_path = Path(dialog.get_filename())
            self.odt_label.set_text(f"Selected: {self.odt_path.name}")
        dialog.destroy()

    def _on_open_word(self, _btn: Gtk.Button) -> None:
        launch = ROOT / "bin" / "myoffice-launch"
        os.execv(str(launch), [str(launch), "word"])

    def prepare(self, _page: Gtk.Widget) -> None:
        index = self.get_current_page()
        if index == 1:
            self._run_checks()
        elif index == 3:
            self.set_page_complete(self.get_nth_page(3), False)
            threading.Thread(target=self._run_install, daemon=True).start()

    def _run_checks(self) -> None:
        for row in self.check_list.get_children():
            self.check_list.remove(row)
        checks = run_all_checks()
        fails = 0
        for c in checks:
            row = Gtk.ListBoxRow()
            mark = {"PASS": "✓", "WARN": "!", "FAIL": "✗"}.get(c.status, "?")
            row.add(Gtk.Label(label=f"{mark} {c.name}: {c.detail}", xalign=0, wrap=True))
            self.check_list.add(row)
            if c.status == "FAIL":
                fails += 1
        self.check_list.show_all()
        self.checks_ok = fails == 0
        if fails:
            self.check_summary.set_text("Some checks failed. You can continue, but setup may not succeed.")
        else:
            self.check_summary.set_text("Your computer looks ready.")
        self.set_page_complete(self.get_nth_page(1), True)

    def _run_install(self) -> None:
        def on_progress(fraction: float, message: str) -> None:
            GLib.idle_add(self._update_progress, fraction, message)

        try:
            install.run_full_install(odt_setup=self.odt_path, on_progress=on_progress)
            GLib.idle_add(self._finish_install)
        except Exception as e:
            GLib.idle_add(self._install_error, str(e))

    def _update_progress(self, fraction: float, message: str) -> None:
        self.progress.set_fraction(min(max(fraction, 0.0), 1.0))
        self.install_status.set_text(message)

    def _finish_install(self) -> None:
        copy_placeholder_icons()
        install_desktop_entries()
        install_mime_associations()
        self.set_page_complete(self.get_nth_page(3), True)
        self.next_page()

    def _install_error(self, msg: str) -> None:
        self.install_status.set_text(msg)
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Setup could not finish",
        )
        dialog.format_secondary_text(
            f"{msg}\n\nOpen MyOffice Settings later to save a diagnostic report, or run:\n"
            f"{ROOT / 'bin' / 'myoffice-doctor'}"
        )
        dialog.run()
        dialog.destroy()
        self.set_page_complete(self.get_nth_page(3), False)


def main() -> int:
    app = SetupWizard()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
