# recalbox-profiles

Gestion des profils de sauvegarde pour Recalbox avec sélection automatique de profil, restauration de saves et synchronisation intelligente.

## Objectif

Permettre la gestion de plusieurs profils de sauvegarde Recalbox en isolant les fichiers de chaque profil et en les chargeant automatiquement au lancement d'un jeu.

- `recalbox/share/profiles/<Profil>/` : sauvegardes spécifiques à un profil.
- `recalbox/share/saves/` : sauvegardes actives utilisées par Recalbox pendant le jeu.
- `recalbox/share/profiles/current_profile.json` : profil actuellement actif.
- `recalbox/share/profiles/profiles.log` : log des changements de profil et des évènements de jeu.
- `recalbox/share/profiles/.sync_manifest.json` : manifest de synchronisation pour ne copier que les saves modifiées.

## Structure attendue

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

## Configuration Recalbox

### Custom system `profiles`

Ajouter une entrée dans `/recalbox/share/system/.emulationstation/systemlist.xml` :

```xml
  <!-- Profiles - system custom -->
  <system uuid="21b8873a-a93e-409c-ad0c-8bb6d682bef8" name="profiles" fullname="Profiles">
    <descriptor path="%ROOT%/profiles" theme="profiles" extensions=".smc .sfc .mgd .zip .7z"/>
    <scraper screenscraper=""/>
    <properties type="console" pad="mandatory" keyboard="no" mouse="optional" lightgun="optional" releasedate="1990-11" retroachievements="1"/>
    <emulatorList>
      <emulator name="libretro">
        <core name="snes9x" priority="1" extensions=".bs .fig .gd3 .sfc .smc .swc .zip! .7z!" netplay="0" softpatching="1" compatibility="high" speed="high" crt.available="1" video.backend="default"/>
        <core name="mesen_s" priority="2" extensions=".bs .bsx .sfc .smc .zip! .7z!" netplay="0" softpatching="0" compatibility="high" speed="high" crt.available="0" video.backend="default"/>
        <core name="bsnes" priority="3" extensions=".bs .bsx .sfc .smc .zip! .7z!" netplay="0" softpatching="1" compatibility="high" speed="high" crt.available="1" video.backend="default"/>
        <core name="bsneshd" priority="4" extensions=".bs .bsx .sfc .smc .zip! .7z!" netplay="0" softpatching="0" compatibility="high" speed="high" crt.available="0" video.backend="default"/>
      </emulator>
    </emulatorList>
  </system>
  <!-- Profiles - system custom -->
```

- Vérifier que l'UUID soit unique dans le `systemlist.xml`.
- Le `theme` doit correspondre au théme disponible pour Recalbox Next (`profiles`).

## Scripts principaux

### `swap_profile[rungame].py`

évènement: `rungame`

- Détecte le lancement d'une ROM dans le système `profiles`
- Extrait le nom du profil depuis le nom du fichier ou le chemin de la ROM
- Vérifie que le profil existe dans `/recalbox/share/profiles/`
- Met à jour `current_profile.json`
- Termine RetroArch pour revenir à EmulationStation
- Log l'évènement dans `recalbox/share/profiles/profiles.log`

> Utilisation : lancer `Guest.zip` ou `Profil1.zip` depuis le système `profiles` pour changer de profil.

### `load_saves[rungame].py`

évènement: `rungame`

- Chargement classique des saves au lancement d'un jeu
- Lit le profil actif dans `current_profile.json`
- Recherche les saves correspondantes dans `/recalbox/share/profiles/<profil>/<system>/<game>.*`
- Copie les fichiers vers `/recalbox/share/saves/<system>/`
- Ignore le système `profiles`
- Log l'évènement de début de jeu

### `load_saves[gamelistbrowsing].py`

évènement: `gamelistbrowsing`

- Utilisé lorsque l'option d'affichage des save states au démarrage du jeu est activée
- Comporte la même logique que `load_saves[rungame].py`
- Permet de restaurer les saves même lors de la navigation et de la prévisualisation des jeux

### `save_profile[endgame].py`

évènement: `endgame`

- Lit le profil actif dans `current_profile.json`
- Recherche les saves modifiées dans `/recalbox/share/saves/<system>/<game>.*`
- Synchronise uniquement les fichiers modifiés vers `/recalbox/share/profiles/<profil>/<system>/`
- Met à jour le manifest `/recalbox/share/profiles/.sync_manifest.json`
- Log l'évènement de fin de jeu

## Chemins clés

- `recalbox/share/profiles/current_profile.json` : profil actif
- `recalbox/share/profiles/profiles.log` : log unifié
- `recalbox/share/profiles/.sync_manifest.json` : manifest de synchronisation
- `recalbox/share/roms/profiles/` : ROMs de sélection de profil
- `recalbox/share/roms/profiles/gamelist.xml` : gamelist du système `profiles`

## Installation

1. Copier les scripts dans `recalbox/share/userscripts/`.
2. Ajouter la définition du système `profiles` dans `recalbox/share/system/.emulationstation/systemlist.xml`.
3. Créer les dossiers de profils sous `recalbox/share/profiles/`.
4. Créer le système de sélection dans `recalbox/share/roms/profiles/` :
   - `Guest.zip`
   - `Profil1.zip`
   - `gamelist.xml`
5. Vérifier que le thème Recalbox Next prend en charge le systéme `profiles`.

## Utilisation

### Changer de profil

- Lancer une ROM du système `profiles` depuis EmulationStation.
- Le script `swap_profile[rungame].py` met à jour `current_profile.json` et ferme RetroArch.
- Retourner dans EmulationStation, le profil actif est maintenant pris en compte.

### Lancer un jeu

- Au démarrage d'un jeu normal, `load_saves[rungame].py` restaure les saves du profil actif.
- Si l'option de save state preview est activée, `load_saves[gamelistbrowsing].py` effectue le même chargement lors de la navigation.

### Fin d'un jeu

- À la fin d'une partie, `save_profile[endgame].py` synchronise les saves modifiées vers le dossier du profil actif.
- Seuls les fichiers modifiés sont copiés grâce à `.sync_manifest.json`.

## Exemple de log

```text
[system] | [2026-08-11 12:00:00] | profiles | ProfileSwap | Guest
[Guest] | [2026-08-11 12:05:00] | snes | GameStart | Super Mario World
[Guest] | [2026-08-11 12:45:00] | snes | GameEnd | Super Mario World
```

## Remarques

- Les scripts reposent sur les chemins `/recalbox/share/` et `/tmp/es_state.inf`.
- Pour que le profil soit bien chargé, le système `profiles` doit être ignoré dans les scripts de save/load.
- Le `current_profile.json` doit exister et contenir un profil valide.
- Vérifier les permissions d'ecriture sur `recalbox/share/profiles/` et `recalbox/share/saves/`.
