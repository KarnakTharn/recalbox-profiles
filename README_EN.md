# recalbox-profiles  
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

      Guest/
        RA_config.json
        megadrive/
          Aladdin.state

      Profil1/
        RA_config.json
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

## 🏆 Automatic RetroAchievements (RA) Management

Each profile may contain:

```
/recalbox/share/profiles/<profile>/RA_config.json
```

This file defines the RA settings for that profile:

- `0` = disabled  
- `1` = enabled  

```json
{
    "global.retroachievements=": "1",
    "global.retroachievements.hardcore=": "0",
    "global.retroachievements.username=": "username_ra",
    "global.retroachievements.password=": "password_ra"
}
```

### ✔ Automatic application inside Recalbox

When a profile is selected:

- The script reads `RA_config.json`
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
- `RA_config.json` is the **single source of truth**  

---

## 📌 Key Paths

- Active profile: `share/profiles/current_profile.json`  
- Log file: `share/profiles/profiles.log`  
- Sync manifest: `share/profiles/.sync_manifest.json`  
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
[system] | [2026-08-11 12:00:00] | profiles | ProfileSwap | Guest
[Guest]  | [2026-08-11 12:05:00] | snes     | GameStart   | Super Mario World
[Guest]  | [2026-08-11 12:45:00] | snes     | GameEnd     | Super Mario World
```

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

---

## 🛡️ Notes

- Scripts rely on `/recalbox/share/` and `/tmp/es_state.inf`  
- The `profiles` system must be ignored by save/load scripts  
- `current_profile.json` must exist and be valid  
- Ensure write permissions on `share/profiles/` and `share/saves/`  