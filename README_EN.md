<!-- Badges -->
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![GitHub release](https://img.shields.io/github/v/release/KarnakTharn/recalbox-profiles)](https://github.com/KarnakTharn/recalbox-profiles/releases)
![GitHub all releases](https://img.shields.io/github/downloads/KarnakTharn/recalbox-profiles/total)
![GitHub issues](https://img.shields.io/github/issues/KarnakTharn/recalbox-profiles)
![GitHub stars](https://img.shields.io/github/stars/KarnakTharn/recalbox-profiles)

# Recalbox Profiles 
  
Compatible  
[![Recalbox](https://img.shields.io/badge/Recalbox-10.0.8-purple)](https://www.recalbox.com/fr/)  

Advanced multi‑profile save management for Recalbox, featuring automatic profile switching, intelligent save restoration, optimized synchronization, and per‑profile RetroAchievements configuration.

![img-systems](img-systems.png)  
![img-gameslist](img-gameslist.jpg)  

---

## 🎯 Purpose

This project enables **multiple independent save profiles** on Recalbox.  
Each profile has:

- its own save files  
- its own RetroAchievements (RA) account configuration  
- its own RA mode (normal / hardcore)  
- its own synchronization manifest  
- its own identity inside EmulationStation  
- its own screenshots (`screenshots/`)  

The active profile is selected through a custom system in EmulationStation.  
Save files are automatically restored when launching a game and synchronized when exiting.

---

## 📁 Expected Directory Structure

```text
recalbox/
  share/
    profiles/
      current_profile.json
      profiles.log
      .sync_manifest.json
      dashboard.html

      Guest/
        profile_config.json
        screenshots/
        roms/
          megadrive/
            Aladdin.state

      Profil1/
        profile_config.json
        screenshots/
        roms/
          gba/
            Breath of Fire.srm

    saves/
      megadrive/
        Aladdin.state
      gba/
        Breath of Fire.srm

    roms/
      profiles/
        Guest.zip
        Profil1.zip
        gamelist.xml

    system/.emulationstation/
      systemlist.xml

    userscripts/
      swap_profile[rungame].py
      load_saves[rungame].py
      load_saves[gamelistbrowsing].py
      save_profile[endgame].py
```

---

## ⚙️ Recalbox Configuration

### 1. Create a local `systemlist.xml`

```bash
cp -r /recalbox/share_init/system/.emulationstation/systemlist.xml \
      /recalbox/share/system/.emulationstation/
```

### 2. Add the custom `profiles` system

Insert into `/recalbox/share/system/.emulationstation/systemlist.xml`:

```xml
  <!-- Profiles - custom system -->
  <system uuid="21b8873a-a93e-409c-ad0c-8bb6d682bef8" name="profiles" fullname="Profiles">
    <descriptor path="%ROOT%/profiles" theme="profiles" extensions=".zip .7z"/>
    <scraper screenscraper=""/>
    <properties type="console" pad="mandatory" keyboard="no" mouse="optional" lightgun="optional" releasedate="1990-11" retroachievements="1"/>
    <emulatorList>
      <emulator name="libretro">
        <core name="snes9x" priority="1" extensions=".zip! .7z!" />
      </emulator>
    </emulatorList>
  </system>
  <!-- Profiles - custom system -->
```

**Important notes:**

- The UUID must be **unique**.  
- The `path` must point to `%ROOT%/profiles`.  
- The theme must contain a `profiles.xml` file.

---

## 🎮 Profile Selection ROMs

Inside `recalbox/share/roms/profiles/`:

- `Guest.zip`  
- `Profil1.zip`  
- `gamelist.xml`

These `.zip` files are **empty** and serve only as triggers to switch profiles.

> To avoid RetroArch error messages, you may include a valid SNES ROM inside the zip.

---

## 🎨 Theme Integration (Recalbox Next)

### Option A — Copy the theme into `share/themes`

1. Copy `recalbox-next` from:  
   `/recalbox/share_init/system/.emulationstation/themes/`
2. Rename it (e.g., `recalbox-next-profiles`)
3. Add `profiles.xml` inside `_systems/`
4. Edit `theme.xml` to include the `profiles` system

### Option B — Modify the original theme

Requires write access to the system partition.

---

## 🧠 Script Behavior

### `swap_profile[rungame].py`  
**Event: `rungame`**

- Detects when a ROM from the `profiles` system is launched  
- Extracts the profile name  
- Updates `current_profile.json`  
- Manages screenshots: backs up current profile's captures, clears global folder, and loads new profile's captures  
- Terminates RetroArch to return to EmulationStation  
- Logs the profile switch  
- Updates the gamelist (region or images)  
- **Applies the profile’s RetroAchievements configuration to `recalbox.conf`**

---

### `load_saves[rungame].py`  
**Event: `rungame`**

- Reads the active profile  
- Copies the profile’s saves into `share/saves/`  
- Ignores the `profiles` system  
- Logs game start  

---

### `load_saves[gamelistbrowsing].py`  
**Event: `gamelistbrowsing`**

- Same logic as `load_saves[rungame].py`  
- Used for save‑state preview  

---

### `save_profile[endgame].py`  
**Event: `endgame`**

- Reads the active profile  
- Detects modified save files  
- Synchronizes only changed files  
- Updates `.sync_manifest.json`  
- Logs game end  

---

### `game_stats[rungame].py` and `game_stats[endgame].py`

These independent scripts track play time regardless of which save-loading event the user chooses.

- `game_stats[rungame].py` creates a temporary session in `current_profile.json` and increments `playcount`.
- `game_stats[endgame].py` calculates the session duration, adds it to `timeplayed`, updates `lastplayed`, then removes the temporary session.
- The `profiles` system is ignored, and repeated events are not counted twice.

---

## 🏆 Automatic RetroAchievements (RA) Management

Each profile may contain:

```
/recalbox/share/profiles/<profile>/profile_config.json
```

This file defines the RA settings for that profile:

- `0` = disabled  
- `1` = enabled  

```json
{
  "stats": {"enabled": 1},
  "favorites": {"enabled": 1},
  "retroachievements": {
    "global.retroachievements=": "1",
    "global.retroachievements.hardcore=": "0",
    "global.retroachievements.username=": "username_ra",
    "global.retroachievements.password=": "password_ra"
  }
}
```

### ✔ Automatic application inside Recalbox

When a profile is selected:

- The script reads the `retroachievements` section from `profile_config.json`
- The values are automatically written into:

```
/recalbox/share/system/recalbox.conf
```

The following lines are updated:

```
global.retroachievements=
global.retroachievements.hardcore=
global.retroachievements.username=
global.retroachievements.password=
```

### ✔ Benefits

- Independent RA accounts per profile  
- Hardcore mode configurable per profile  
- No manual editing of `recalbox.conf`  
- `profile_config.json` is the **single source of truth** for RA settings and profile options

NB: The information from the RA account is correctly applied even if the change is not visible in the menu/option on Recalbox (request a reboot), however if we look at the RA account in the Recalbox Manager (Web), the change has been made.

---

## ⏱️ Per-profile game statistics

The `stats` section in `profile_config.json` enables or disables tracking for a profile:

```json
"stats": {"enabled": 1}
```

- `1`: tracking is enabled;
- `0`: no launches or play time are recorded.

Statistics are stored in:

```
/recalbox/share/profiles/<profile>/game_time.json
```

Example:

```json
{
  "megadrive": {
    "Aladdin": {
      "timeplayed": 5423,
      "playcount": 12,
      "lastplayed": "20260901T142000"
    }
  }
}
```

- `timeplayed`: total time in seconds;
- `playcount`: number of game launches;
- `lastplayed`: date and time of the last launch, using the Recalbox `YYYYMMDDTHHMMSS` format.

While a game is running, `current_profile.json` temporarily contains `active_game` with the game and its start time. This entry is removed by the `endgame` event after the duration is recorded.

---

## 📌 Key Paths

- Active profile: `share/profiles/current_profile.json`  
- Log file: `share/profiles/profiles.log`  
- Sync manifest: `share/profiles/.sync_manifest.json`  
- Screenshots: `share/profiles/<profile>/screenshots/`  
- Statistics: `share/profiles/<profile>/game_time.json`
- Dashboard: `share/profiles/dashboard.html`
- Profile ROMs: `share/roms/profiles/`  
- Gamelist: `share/roms/profiles/gamelist.xml`  
- Recalbox configuration: `share/system/recalbox.conf`  

---

## 📥 Installation

1. Copy the scripts into `share/userscripts/`  
2. Add the `profiles` system to `systemlist.xml`  
3. Create profile folders inside `share/profiles/`  
4. Create selection ROMs inside `share/roms/profiles/`  
5. Add `profiles.xml` to your theme  

---

## 🕹️ Usage

### Switching profiles  
- Launch `Guest.zip` or `Profil1.zip`  
- RetroArch closes automatically  
- EmulationStation reloads the active profile  

### Launching a game  
- The active profile’s saves are restored automatically  

### Exiting a game  
- Modified saves are synchronized back into the profile  

---

## 📝 Example Log

```text
2026-09-01 14:20:15 [DEBUG] swap_profile_rungame: Detection of 'profiles' system
2026-09-01 14:20:15 [DEBUG] swap_profile_rungame: Profile detected: Guest
2026-09-01 14:20:15 [INFO] swap_profile_rungame: Profile changed to: Guest
2026-09-01 14:20:15 [DEBUG] swap_profile_rungame: RetroArch found (PID: 1234)
2026-09-01 14:20:15 [DEBUG] swap_profile_rungame: SIGINT signal sent to process 1234
2026-09-01 14:20:17 [DEBUG] swap_profile_rungame: gamelist updated for profile 'Guest'
2026-09-01 14:20:17 [INFO] swap_profile_rungame: RetroAchievements updated in recalbox.conf for profile: Guest
2026-09-01 14:20:17 [INFO] swap_profile_rungame: Removing all favorites...
2026-09-01 14:20:20 [INFO] swap_profile_rungame: Favorites removed successfully
2026-09-01 14:20:20 [INFO] swap_profile_rungame: Applying favorites for profile 'Guest'...
2026-09-01 14:20:25 [INFO] swap_profile_rungame: Favorites applied successfully for profile 'Guest'
2026-09-01 14:20:25 [INFO] swap_profile_rungame: EmulationStation restarted successfully
2026-09-01 14:20:30 [INFO] load_saves_rungame: Profile 'Guest' loaded
2026-09-01 14:20:30 [INFO] load_saves_rungame: Restoring saves for 'snes'...
2026-09-01 14:20:31 [INFO] load_saves_rungame: Game launched: Super Mario World (snes)
2026-09-01 14:45:00 [INFO] game_stats_endgame: Session ended for Super Mario World
2026-09-01 14:45:00 [INFO] game_stats_endgame: Play time: 1500 seconds (25 min)
2026-09-01 14:45:00 [INFO] save_profile_endgame: Synchronizing saves for profile 'Guest'
2026-09-01 14:45:02 [INFO] save_profile_endgame: 1 file(s) modified and synchronized
```

---

## 🎯 Per-profile Favorites Management

Each profile can independently manage its own EmulationStation favorites.

### Configuration

The `favorites` section in `profile_config.json` enables or disables this feature:

```json
{
  "favorites": {"enabled": 1}
}
```

- `1`: favorites management is active for this profile
- `0`: favorites management is disabled; existing favorites are not modified

### Behavior when switching profiles

#### ✅ `favorites.enabled = 1` (Active)

**Case 1: `favorites.json` file is not empty (Profil1)**
- All current favorites are removed (cleanup)
- Profile favorites are applied from `profiles/<profile>/favorites.json`
- EmulationStation restarts to reload the list

**Case 2: `favorites.json` file is empty (Guest)**
- All current favorites are removed (reset)
- No new favorites are applied
- EmulationStation restarts

#### ❌ `favorites.enabled = 0` (Inactive)

- No action is taken
- Existing favorites are preserved
- No EmulationStation restart
- Useful for temporary or guest profiles

### `favorites.json` file

The `profiles/<profile>/favorites.json` file contains the list of favorites to apply:

```json
{
  "snes": [
    "Super Mario World",
    "The Legend of Zelda: A Link to the Past"
  ],
  "megadrive": [
    "Sonic The Hedgehog 2"
  ]
}
```

### Associated scripts

- **Export**: `Favorites export(sync).py` — exports current favorites to `favorites.json`
- **Apply**: `swap_profile[rungame].py` — automatically applies favorites when switching profiles
- **Utility**: `recalbox_favorites.py` — background utility (sourced from jffella's [recalbox-rom-list-manager](https://github.com/jffella/recalbox-rom-list-manager) project)

### Favorites Management Procedure

**Step 1: Prerequisites**
- You must be on the correct profile
- Make your favorites selection (or proceed to Step 2 if already done)

**Step 2: Save favorites**
> Manual favorites saving is recommended because it is not a daily action, which avoids redundant calls without creating unnecessary duplication.

- Use the `ES Reboot` script (Menu → Advanced → User Scripts) to restart EmulationStation only, or perform a normal Recalbox reboot
- After the reboot, use the `Favorites export` script (Menu → Advanced → User Scripts)
- The JSON file will be created in the `profiles/` folder, favorites will be loaded, and EmulationStation will restart automatically

**Step 3: Switch profiles**
- Switch to a different profile
- Repeat Steps 1 and 2

---

## 🔧 Optional Manual Scripts

Inside `share/userscripts/manual/`:

- `Guest(sync).py` / `Profil1(sync).py`  
  - Manually load a profile  
  - Initialize a profile  
  - Troubleshooting  

- `Save_profile(sync).py`  
  - Manually save current files  
  - Force a full synchronization  

- `Favorites export(sync).py`
  - Exports the active profile's EmulationStation favorites to
    `profiles/<profile>/favorites.json`
  - Export runs only when `favorites.enabled` is set to `1`

## 📊 Statistics Dashboard

The `share/userscripts/manual/generate_dashboard.py` script generates an HTML dashboard from every profile's `game_time.json` file. It includes:

- total play time, unique game count, most-played system, and most active profile;
- one tab per profile with total time, launches, favorites, and system distribution;
- the most-played games, with search and sorting by name, system, duration, or launch count;
- a dark or light theme remembered by the browser.

A profile is included when it contains `profile_config.json`. The displayed statistics come from `game_time.json`, which is produced by `game_stats[rungame].py` and `game_stats[endgame].py`. The default output file is:

```text
/recalbox/share/profiles/dashboard.html
```

Generate it on Recalbox with:

```bash
python3 /recalbox/share/userscripts/manual/generate_dashboard.py
```

Custom paths can be supplied for testing or previewing:

```bash
python3 /recalbox/share/userscripts/manual/generate_dashboard.py \
  --profiles-dir /recalbox/share/profiles \
  --output /recalbox/share/profiles/dashboard.html
```

Open `dashboard.html` in a browser afterward. The generator does not modify profile statistics or profile configuration.

---

## 🛡️ Notes

- Scripts rely on `/recalbox/share/` and `/tmp/es_state.inf`  
- The `profiles` system must be ignored by save/load scripts  
- `current_profile.json` must exist and be valid  
- Ensure write permissions on `share/profiles/` and `share/saves/`

License: GPLv3
