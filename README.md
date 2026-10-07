# MyOffice

User-friendly Microsoft Office setup for Linux (Mint/Ubuntu): one setup wizard, menu icons, hidden Wine launcher.

## For end users

1. Download `MyOffice-Setup.run` (built on a Linux machine).
2. Double-click or run: `bash MyOffice-Setup.run`
3. Follow the on-screen steps (no terminal required).
4. Open Word from your applications menu; sign in with Microsoft when prompted.
5. **MyOffice Settings** — Repair Office or **Save diagnostic report** if you need help.

## For developers

### Layout

- `wizard/` — GTK3 setup wizard and Settings
- `engine/` — install, diagnostics, repair, sandbox, recipes
- `bin/` — launchers (users should not need these directly)
- `integration/` — `.desktop` and MIME
- `installer/` — build self-extracting bundle
- `poc/` — internal PoC scripts (not shipped in Setup)

### Dependencies (target Linux)

- Python 3.10+
- GTK 3 (`python3-gi`, `gir1.2-gtk-3.0`)
- Optional: `bubblewrap`, `zenity`, `vulkaninfo`

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 bubblewrap zenity
```

Python extras (only if `< 3.11`):

```bash
pip install -r requirements.txt
```

### Internal PoC gate

```bash
cd poc
chmod +x *.sh ../bin/*
export MYOFFICE_WINE=/path/to/wine
./poc-install-office.sh
```

Fill in [poc/CHECKLIST.md](poc/CHECKLIST.md) after a successful run.

### Build installer

On Linux:

```bash
chmod +x installer/build-setup.sh installer/post-install.sh bin/*
./installer/build-setup.sh
# Output: dist/MyOffice-Setup.run
```

Set release runner URL and hash:

```bash
export MYOFFICE_RUNNER_URL=https://github.com/you/wine-runner/releases/download/v1/runner.tar.xz
export MYOFFICE_RUNNER_SHA256=...
```

### CLI fallback (support)

```bash
export PYTHONPATH="$(pwd)"
./bin/myoffice-doctor
```

## v0.2 roadmap (in repo)

- Signed TOML recipes (`engine/recipe.py`, `manifests/*.sig.json`)
- Landlock fallback (`engine/landlock.py`)
- Custom Wine CI runtime when prebuilt runners are insufficient

## Data directory

`~/.local/share/myoffice/` — prefixes, runtimes, logs, install copy.
