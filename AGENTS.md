# Repository Guidelines

## Project Structure & Module Organization

This repository is a deployable overlay for Recalbox, not a conventional Python package. Preserve the target layout under `recalbox/share/`: copy its contents to `/recalbox/share/` on the device.

- `recalbox/share/userscripts/`: event-driven Python scripts. The filename suffix selects the EmulationStation event, for example `game_stats[rungame].py` or `save_profile[endgame].py`.
- `recalbox/share/profiles/<profile>/`: per-player configuration (`profile_config.json`) and generated statistics (`game_time.json`). Do not commit real RetroAchievements credentials.
- `recalbox/share/roms/profiles/`, `system/`, and `themes/`: profile selector ROMs, the custom system definition, and Recalbox Next theme integration.
- `images_store/`: source visual assets. `archive_script/` contains historical utilities, not active runtime code.
- `README.md`, `README_EN.md`, and `CHANGELOG.md`: user-facing French/English documentation and release notes.

## Development & Validation

There is no build system or automated test suite. Validate changes before deployment:

```powershell
git diff --check
python3 -m py_compile "recalbox/share/userscripts/game_stats[rungame].py"
```

Run Python validation on a Recalbox/Linux host when possible; scripts rely on `/recalbox/share/` and `/tmp/es_state.inf`. Test the complete event flow manually: select a profile, launch a game, exit it, then inspect the profile’s saves, `game_time.json`, and `current_profile.json`.

## Coding Style & Naming Conventions

Use Python 3, four-space indentation, `snake_case` functions and constants in `UPPER_SNAKE_CASE`. Keep scripts self-contained and standard-library only. Read EmulationStation state through `STATE_FILE`; always ignore the `profiles` system in scripts that process actual games. Write JSON defensively and preserve existing keys in `current_profile.json`. Name event scripts as `<purpose>[<event>].py`; use lower-case JSON keys matching Recalbox conventions, such as `timeplayed`, `playcount`, and `lastplayed`.

## Configuration & Safety

`profile_config.json` is the extensible source of per-profile settings. Put RetroAchievements values under `retroachievements` and feature toggles under their own section (for example, `stats.enabled`). Do not log passwords or overwrite unrelated `recalbox.conf` entries.

## Commits & Pull Requests

Follow the history’s Conventional Commit style: `feat:`, `fix:`, `docs:`, or `refactor:` followed by a concise French description. Keep commits focused. PRs should explain the Recalbox event flow affected, list updated deployment files, update both READMEs and `CHANGELOG.md` for user-visible features, and include screenshots only for theme/UI changes.
