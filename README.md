<!-- Badges -->
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![GitHub release](https://img.shields.io/github/v/release/KarnakTharn/recalbox-profiles)](https://github.com/KarnakTharn/recalbox-profiles/releases)
![GitHub all releases](https://img.shields.io/github/downloads/KarnakTharn/recalbox-profiles/total)
![GitHub issues](https://img.shields.io/github/issues/KarnakTharn/recalbox-profiles)
![GitHub stars](https://img.shields.io/github/stars/KarnakTharn/recalbox-profiles)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/KarnakTharn/recalbox-profiles)


# Recalbox Profiles    
Gestion avancée des profils de sauvegarde pour Recalbox, avec sélection automatique de profil, restauration intelligente des saves, synchronisation optimisée et configuration indépendante des RetroAchievements.

![img-systems](img-systems.png)  
![img-gameslist](img-gameslist.jpg)  

---

## 🎯 Objectif

Ce projet permet d’utiliser **plusieurs profils indépendants** dans Recalbox, chacun possédant :

- ses propres sauvegardes (`saves/`)  
- sa propre configuration RetroAchievements (RA)  
- son propre état de synchronisation  
- son propre compte RA (username/password)  
- son propre mode RA (normal / hardcore)

Le profil actif est sélectionné via un système custom dans EmulationStation.  
Les saves sont automatiquement restaurées au lancement d’un jeu et synchronisées à la fin.

---

## 📁 Structure attendue

```text
recalbox/
  share/
    profiles/
      current_profile.json
      profiles.log
      .sync_manifest.json

      Guest/
        profile_config.json
        megadrive/
          Aladdin.state

      Profil1/
        profile_config.json
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

## ⚙️ Configuration Recalbox

### 1. Création du fichier `systemlist.xml` local

```bash
cp -r /recalbox/share_init/system/.emulationstation/systemlist.xml \
      /recalbox/share/system/.emulationstation/
```

### 2. Ajout du système custom `profiles`

Dans `/recalbox/share/system/.emulationstation/systemlist.xml` :

```xml
  <!-- Profiles - system custom -->
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
  <!-- Profiles - system custom -->
```

**Notes :**

- L’UUID doit être **unique**.  
- Le `path` doit pointer vers `%ROOT%/profiles`.  
- Le thème doit contenir un fichier `profiles.xml`.

---

## 🎮 ROMs de sélection de profil

Dans `recalbox/share/roms/profiles/` :

- `Guest.zip`  
- `Profil1.zip`  
- `gamelist.xml`

Les `.zip` sont **vides** : ils servent uniquement de déclencheurs pour changer de profil.

> Pour éviter les messages d’erreur RetroArch, utiliser une ROM SNES valide dans le zip.

---

## 🎨 Intégration dans le thème Recalbox Next

### Option A — Copier le thème dans `share/themes`

1. Copier `recalbox-next` depuis :  
   `/recalbox/share_init/system/.emulationstation/themes/`
2. Le renommer (ex. `recalbox-next-profiles`)
3. Ajouter `profiles.xml` dans `_systems/`
4. Modifier `theme.xml` pour inclure le système `profiles`

### Option B — Modifier le thème d’origine

Nécessite un accès en écriture à la partition système.

---

## 🧠 Fonctionnement des scripts

### `swap_profile[rungame].py`  
**Événement : `rungame`**

- Détecte le lancement d’une ROM du système `profiles`
- Extrait le nom du profil
- Met à jour `current_profile.json`
- Termine RetroArch pour revenir à EmulationStation
- Log l’événement dans `profiles.log`
- Met à jour la gamelist (`region` ou images)
- **Applique automatiquement la configuration RetroAchievements du profil dans `recalbox.conf`**

---

### `load_saves[rungame].py`  
**Événement : `rungame`**

- Lit le profil actif  
- Copie les saves du profil vers `share/saves/`  
- Ignore le système `profiles`  
- Log le début de jeu  

---

### `load_saves[gamelistbrowsing].py`  
**Événement : `gamelistbrowsing`**

- Même logique que `load_saves[rungame].py`  
- Utilisé pour la prévisualisation des save states  

---

### `save_profile[endgame].py`  
**Événement : `endgame`**

- Lit le profil actif  
- Détecte les saves modifiées  
- Synchronise uniquement les fichiers modifiés  
- Met à jour `.sync_manifest.json`  
- Log la fin de jeu  

---

### `game_stats[rungame].py` et `game_stats[endgame].py`

Ces scripts indépendants suivent le temps de jeu, quel que soit l’événement choisi par l’utilisateur pour charger les sauvegardes.

- `game_stats[rungame].py` crée une session temporaire dans `current_profile.json` et incrémente `playcount`.
- `game_stats[endgame].py` calcule la durée de la session, l’ajoute à `timeplayed`, met à jour `lastplayed`, puis supprime la session temporaire.
- Le système `profiles` est ignoré et les événements répétés ne sont pas comptés deux fois.

---

## 🏆 Gestion automatique des RetroAchievements (RA)

Chaque profil peut contenir un fichier :

```
/recalbox/share/profiles/<profil>/profile_config.json
```

Ce fichier définit les paramètres RA propres au profil :

- `0` = désactivé  
- `1` = activé  

```json
{
  "stats": {"enabled": 1},
  "retroachievements": {
    "global.retroachievements=": "1",
    "global.retroachievements.hardcore=": "0",
    "global.retroachievements.username=": "username_ra",
    "global.retroachievements.password=": "password_ra"
  }
}
```

### ✔ Application automatique dans Recalbox

Lorsqu’un profil est sélectionné :

- Le script lit la section `retroachievements` de `profile_config.json`
- Les valeurs sont appliquées automatiquement dans :

```
/recalbox/share/system/recalbox.conf
```

Les lignes suivantes sont mises à jour :

```
global.retroachievements=
global.retroachievements.hardcore=
global.retroachievements.username=
global.retroachievements.password=
```

### ✔ Avantages

- Comptes RA indépendants par profil  
- Mode Hardcore configurable par profil  
- Aucun besoin de modifier `recalbox.conf` manuellement  
- `profile_config.json` reste la source unique des paramètres RA et des options du profil

NB : Les informations du compte RA sont bien appliquées même si le changement n'est pas pas visible dans le menu/option sur Recalbox (demande un reboot), cependant si nous regardons le compte RA dans le Recalbox Manager (Web), la modification est bien réalisée.

---

## ⏱️ Statistiques de jeu par profil

La section `stats` de `profile_config.json` active ou désactive le suivi pour un profil :

```json
"stats": {"enabled": 1}
```

- `1` : le suivi est activé ;
- `0` : aucun lancement ni temps de jeu n’est enregistré.

Les statistiques sont enregistrées dans :

```
/recalbox/share/profiles/<profil>/game_time.json
```

Exemple :

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

- `timeplayed` : temps total en secondes ;
- `playcount` : nombre de lancements du jeu ;
- `lastplayed` : date et heure du dernier lancement, au format Recalbox `YYYYMMDDTHHMMSS`.

Pendant une partie, `current_profile.json` contient temporairement `active_game` avec le jeu et son heure de début. Cette entrée est supprimée par l’événement `endgame` après l’enregistrement du temps.

---

## 📌 Chemins clés

- Profil actif : `share/profiles/current_profile.json`  
- Log : `share/profiles/profiles.log`  
- Manifest : `share/profiles/.sync_manifest.json`  
- Statistiques : `share/profiles/<profil>/game_time.json`
- ROMs de sélection : `share/roms/profiles/`  
- Gamelist du système : `share/roms/profiles/gamelist.xml`  
- Config Recalbox : `share/system/recalbox.conf`  

---

## 📥 Installation

1. Copier les scripts dans `share/userscripts/`  
2. Ajouter le système `profiles` dans `systemlist.xml`  
3. Créer les dossiers de profils dans `share/profiles/`  
4. Créer les ROMs de sélection dans `share/roms/profiles/`  
5. Ajouter `profiles.xml` dans le thème  

---

## 🕹️ Utilisation

### Changer de profil  
- Lancer `Guest.zip` ou `Profil1.zip`  
- RetroArch se ferme automatiquement  
- EmulationStation recharge le profil actif  

### Lancer un jeu  
- Les saves du profil actif sont restaurées automatiquement  

### Fin d’un jeu  
- Les saves modifiées sont synchronisées dans le profil actif  

---

## 📝 Exemple de log

```text
[system] | [2026-08-11 12:00:00] | profiles | ProfileSwap | Guest
[Guest]  | [2026-08-11 12:05:00] | snes     | GameStart   | Super Mario World
[Guest]  | [2026-08-11 12:45:00] | snes     | GameEnd     | Super Mario World
```

---

## 🔧 Scripts manuels (optionnel)

Dans `share/userscripts/manual/` :

- `Guest(sync).py` / `Profil1(sync).py`  
  - Charger manuellement un profil  
  - Initialiser un profil  
  - Dépannage  

- `Save_profile(sync).py`  
  - Sauvegarder manuellement les saves actuelles  
  - Forcer une synchronisation complète  

---

## 🛡️ Remarques

- Les scripts utilisent `/recalbox/share/` et `/tmp/es_state.inf`  
- Le système `profiles` doit être ignoré dans les scripts de save/load  
- `current_profile.json` doit exister et être valide  
- Vérifier les permissions d’écriture sur `share/profiles/` et `share/saves/`  

License: GPLv3
