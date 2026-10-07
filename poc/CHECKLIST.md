# Wizard automation checklist (fill after PoC runs)

Mark each step once `engine/install.py` implements it.

- [ ] Create WoW64 prefix at `$DATA/prefixes/office`
- [ ] Set `winemenubuilder.exe=disabled` in prefix
- [ ] Apply DLL overrides (document list from PoC)
- [ ] Import registry fragments (paths in `config/registry/`)
- [ ] Run ODT with `config/odt/configuration.xml`
- [ ] Verify WINWORD.EXE, EXCEL.EXE, POWERPNT.EXE paths
- [ ] Record cold-start time (seconds): ___
- [ ] M365 sign-in works: yes / no
- [ ] Notes:
