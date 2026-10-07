#!/usr/bin/env python3
"""MyOffice Settings: Repair and diagnostics for non-technical users."""
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

from engine.diagnostics import save_report
from engine import repair


class SettingsWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="MyOffice Settings")
        self.set_default_size(480, 320)
        self.set_border_width(16)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(box)

        box.pack_start(Gtk.Label(label="Repair Office or save a diagnostic report for your helper.", wrap=True, xalign=0), False, False, 0)

        repair_btn = Gtk.Button(label="Repair Office")
        repair_btn.connect("clicked", self._on_repair)
        box.pack_start(repair_btn, False, False, 0)

        diag_btn = Gtk.Button(label="Save diagnostic report…")
        diag_btn.connect("clicked", self._on_save_report)
        box.pack_start(diag_btn, False, False, 0)

        grant_hint = Gtk.Label(
            label="To allow opening files from extra folders, ask your helper to add paths to granted-folders in MyOffice settings data.",
            wrap=True,
            xalign=0,
        )
        box.pack_start(grant_hint, False, False, 0)

        self.status = Gtk.Label(label="", xalign=0, wrap=True)
        box.pack_start(self.status, True, True, 0)

        self.progress = Gtk.ProgressBar()
        self.progress.set_fraction(0.0)
        box.pack_start(self.progress, False, False, 0)

    def _on_save_report(self, _btn: Gtk.Button) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Save diagnostic report",
            parent=self,
            action=Gtk.FileChooserAction.SAVE,
        )
        dialog.set_current_name("MyOffice-diagnostic.txt")
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        if dialog.run() == Gtk.ResponseType.OK:
            path = Path(dialog.get_filename())
            save_report(path)
            self.status.set_text(f"Report saved to {path}")
        dialog.destroy()

    def _on_repair(self, _btn: Gtk.Button) -> None:
        confirm = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Repair Office?",
        )
        confirm.format_secondary_text(
            "This rebuilds the Office installation and restores your templates and dictionaries."
        )
        if confirm.run() != Gtk.ResponseType.OK:
            confirm.destroy()
            return
        confirm.destroy()
        threading.Thread(target=self._run_repair, daemon=True).start()

    def _run_repair(self) -> None:
        def on_progress(f: float, m: str) -> None:
            GLib.idle_add(self._update, f, m)

        try:
            repair.rebuild_prefix(on_progress)
            GLib.idle_add(self.status.set_text, "Repair finished successfully.")
        except Exception as e:
            GLib.idle_add(self.status.set_text, f"Repair failed: {e}")

    def _update(self, fraction: float, message: str) -> None:
        self.progress.set_fraction(min(max(fraction, 0.0), 1.0))
        self.status.set_text(message)


def main() -> int:
    win = SettingsWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
