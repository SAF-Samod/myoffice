# Internal PoC (developer only)

Hand-run gate before shipping the wizard. Not included in `MyOffice-Setup.run`.

## Prerequisites

- x86_64 Linux (Mint/Ubuntu target)
- ~15 GB free disk
- Network for ODT / Office download
- Wine WoW64-capable runner at `../runtimes/current/` or set `MYOFFICE_WINE`

## Steps

```bash
cd poc
./poc-install-office.sh
./poc-launch-word.sh
```

Capture timings and any manual registry/DLL steps in `CHECKLIST.md` after each successful run.
