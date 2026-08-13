# recalbox-profiles  
Advanced multi‑profile save management for Recalbox, featuring automatic profile selection, intelligent save restoration, and optimized synchronization.

---

## 🎯 Purpose  
This project enables **multiple independent save profiles** on Recalbox:

- Each profile stores its own save files.
- The active profile is selected through a custom EmulationStation system.
- Saves are automatically restored when launching a game and synchronized when exiting.

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
        megadrive/
          Aladdin.state
      Profil1/
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
The file does not exist by default. Copy it from the system partition:

```bash
cp -r /recalbox/share_init/system/.emulationstation/systemlist.xml \
      /recalbox/share/system/.emulationstation/
```

### 2. Add the custom `profiles` system

Insert the following block into  
`/recalbox/share/system/.emulationstation/systemlist.xml`:

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
- The `path` must point to `%ROOT%/profiles` (ROM directory).
- The `theme="profiles"` must match the theme file you will add.

---

## 🎮 Profile Selection ROMs

Inside `recalbox/share/roms/profiles/` create:

- `Guest.zip`
- `Profil1.zip`
- `gamelist.xml`

The `.zip` files are **empty archives** used as profile selectors.  
Launching them triggers RetroArch, which fails immediately → EmulationStation returns to the gamelist → the profile is switched.

>Tips : To avoid error messages, it is advisable to use an authentic SNES rom in the zip format.

---

## 🎨 Theme Integration (Recalbox Next)

Two possible approaches:

### Option A — Copy the theme into `share/themes`
1. Copy `recalbox-next` from:  
   `/recalbox/share_init/system/.emulationstation/themes/`
2. Rename it (e.g., `recalbox-next-profiles`)
3. Add `profiles.xml` inside `_systems/`
4. Update `theme.xml` to include the new system

### Option B — Modify the original theme  
Requires write access to the system partition.  
Copy only the necessary files (`profiles.xml`, images, etc.).

---

## 🧠 Script Overview

### `swap_profile[rungame].py`  
**Event:** `rungame`

- Detects ROM launch inside the `profiles` system  
- Extracts the profile name  
- Updates `current_profile.json`  
- Terminates RetroArch to return to EmulationStation  
- Logs the event in `profiles.log`

### `load_saves[rungame].py`  
**Event:** `rungame`

- Reads the active profile  
- Restores the corresponding saves into `share/saves/`  
- Ignores the `profiles` system  
- Logs game start

### `load_saves[gamelistbrowsing].py`  
**Event:** `gamelistbrowsing`

- Same logic as `load_saves[rungame].py`  
- Used when save‑state preview is enabled

### `save_profile[endgame].py`  
**Event:** `endgame`

- Reads the active profile  
- Detects modified save files  
- Synchronizes only changed files  
- Updates `.sync_manifest.json`  
- Logs game end

---

## 📌 Key Paths

- Active profile: `share/profiles/current_profile.json`
- Unified log: `share/profiles/profiles.log`
- Sync manifest: `share/profiles/.sync_manifest.json`
- Profile selector ROMs: `share/roms/profiles/`
- Gamelist: `share/roms/profiles/gamelist.xml`

---

## 📥 Installation Steps

1. Copy the scripts into `share/userscripts/`
2. Add the `profiles` system to `systemlist.xml`
3. Create profile directories under `share/profiles/`
4. Create the selector ROMs in `share/roms/profiles/`
5. Add theme support for the `profiles` system

---

## 🕹️ Usage

### Switching profiles
- Launch `Guest.zip` or `Profil1.zip`
- RetroArch closes automatically
- EmulationStation reloads with the new active profile

### Launching a game
- Saves for the active profile are restored automatically

### Ending a game
- Modified saves are synchronized back to the profile directory

---

## 📝 Example Log Output

```text
[system] | [2026-08-11 12:00:00] | profiles | ProfileSwap | Guest
[Guest]  | [2026-08-11 12:05:00] | snes     | GameStart   | Super Mario World
[Guest]  | [2026-08-11 12:45:00] | snes     | GameEnd     | Super Mario World
```

---

## 🔧 Optional Manual Scripts

Located in `share/userscripts/manual/`:

- **`Guest(sync).py` / `Profil1(sync).py`**  
  - Manually load a profile  
  - Initialize a profile  
  - Troubleshooting

- **`Save_profile(sync).py`**  
  - Manually save current game data  
  - Force a full synchronization

These scripts are **optional** and not used during normal operation.

---

## 🛡️ Notes & Requirements

- Scripts rely on `/recalbox/share/` and `/tmp/es_state.inf`
- The `profiles` system must be ignored by save/load scripts
- `current_profile.json` must exist and contain a valid profile name
- Ensure write permissions on `share/profiles/` and `share/saves/`