<!-- Badges -->
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![GitHub release](https://img.shields.io/github/v/release/KarnakTharn/recalbox-profiles)](https://github.com/KarnakTharn/recalbox-profiles/releases)
![GitHub all releases](https://img.shields.io/github/downloads/KarnakTharn/recalbox-profiles/total)
![GitHub issues](https://img.shields.io/github/issues/KarnakTharn/recalbox-profiles)
![GitHub stars](https://img.shields.io/github/stars/KarnakTharn/recalbox-profiles)

<!--Langue-->
<img src="https://cdn.jsdelivr.net/gh/lipis/flag-icons@6.6.6/flags/4x3/fr.svg" alt="FR" width="24"> **Français** · <a href="README_EN.md"><img src="https://cdn.jsdelivr.net/gh/lipis/flag-icons@6.6.6/flags/4x3/gb.svg" alt="GB" width="24"> **English**</a>

# Recalbox Profiles 
  
Compatible  
[![Recalbox](https://img.shields.io/badge/Recalbox-10.1-purple)](https://www.recalbox.com/fr/)  

Gestion avancée des profils de sauvegarde pour Recalbox, avec sélection automatique de profil, restauration intelligente des saves, synchronisation optimisée et configuration indépendante des RetroAchievements.

![img-systems](img-systems.png)  
![img-gameslist](img-gameslist.jpg)  

---

## 🎯 Objectif

Ce projet permet d’utiliser **plusieurs profils indépendants** dans Recalbox, chacun possédant :

- ses propres sauvegardes (`saves/`)  
- sa propre configuration RetroAchievements (RA)
- son propre compte Patreon (clé privée)  
- son propre état de synchronisation  
- son propre compte RA (username/password)  
- son propre mode RA (normal / hardcore)
- ses propres captures d'écran (`screenshots/`)

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
      dashboard.html

      Guest/
        profile_config.json
        screenshots/
        saves/
          megadrive/
            Aladdin.state


      Profil1/
        profile_config.json
        screenshots/
        saves/
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
- Met à jour `profiles-fr.txt` et `profiles-en.txt` avec le nom du profil actif, dans le thème défini par `current_theme.json`
- Gère les captures d'écran : sauvegarde les screenshots du profil actuel, vide le dossier global, et charge ceux du nouveau profil
- Termine RetroArch pour revenir à EmulationStation
- Log l’événement dans `profiles.log`
- Met à jour la gamelist (`region` ou images)
- **Applique automatiquement les configurations RetroAchievements et Patreon du profil dans recalbox.conf**

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

- `game_stats[rungame].py` crée une session temporaire dans `current_profile.json`.
- `game_stats[endgame].py` calcule la durée de la session. Si elle est **supérieure ou égale à 5 minutes**, elle est ajoutée à `timeplayed` et le `playcount` est incrémenté.
- Les systèmes `profiles` et `imageviewer` sont ignorés.
- Les événements répétés ne sont pas comptés deux fois.

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
  "favorites": {"enabled": 1},
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

## 💎 Gestion du compte Patreon

Le système permet également de gérer la clé privée Patreon par profil.

### ✔ Application automatique

Lorsqu’un profil est sélectionné, le script met à jour la ligne suivante dans `/recalbox/share/system/recalbox.conf` :
`patron.privatekey=<cle>`

### 🛠️ Récupération manuelle de la clé (Première installation)

La première fois, vous devez récupérer votre clé manuellement pour l'ajouter à vos profils :

1. Sur Recalbox, associez votre compte Patreon à la console (consultez le tuto "Challenge" sur le site officiel de Recalbox).
2. Récupérez la clé générée dans le fichier `/recalbox/share/system/recalbox.conf` à la ligne `patron.privatekey`.
3. Ajoutez cette clé dans le fichier `profile_config.json` de votre profil :

```json
{
  "patreon": {
    "enabled": 1,
    "privatekey": "VOTRE_CLE_RECUPEREE"
  }
}
```

Une fois cette étape réalisée, le changement de clé sera automatique lors de la sélection du profil.

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
- Screenshots : `share/profiles/<profil>/screenshots/`  
- Statistiques : `share/profiles/<profil>/game_time.json`
- Dashboard : `share/profiles/dashboard.html`
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
2026-09-01 14:20:15 [DEBUG] swap_profile_rungame: Détection du système 'profiles'
2026-09-01 14:20:15 [DEBUG] swap_profile_rungame: Profil détecté : Guest
2026-09-01 14:20:15 [INFO] swap_profile_rungame: Profil changé en: Guest
2026-09-01 14:20:15 [DEBUG] swap_profile_rungame: RetroArch trouvé (PID: 1234)
2026-09-01 14:20:15 [DEBUG] swap_profile_rungame: Signal SIGINT envoyé au processus 1234
2026-09-01 14:20:17 [DEBUG] swap_profile_rungame: gamelist mis à jour pour profil 'Guest'
2026-09-01 14:20:17 [INFO] swap_profile_rungame: RetroAchievements mis à jour dans recalbox.conf pour le profil : Guest
2026-09-01 14:20:17 [INFO] swap_profile_rungame: Retrait de tous les favoris...
2026-09-01 14:20:20 [INFO] swap_profile_rungame: Favoris retirés avec succès
2026-09-01 14:20:20 [INFO] swap_profile_rungame: Application des favoris pour le profil 'Guest'...
2026-09-01 14:20:25 [INFO] swap_profile_rungame: Favoris appliqués avec succès pour le profil 'Guest'
2026-09-01 14:20:25 [INFO] swap_profile_rungame: EmulationStation redémarré avec succès
2026-09-01 14:20:30 [INFO] load_saves_rungame: Profil 'Guest' chargé
2026-09-01 14:20:30 [INFO] load_saves_rungame: Restauration des saves pour 'snes'...
2026-09-01 14:20:31 [INFO] load_saves_rungame: Jeu lancé : Super Mario World (snes)
2026-09-01 14:45:00 [INFO] game_stats_endgame: Session terminée pour Super Mario World
2026-09-01 14:45:00 [INFO] game_stats_endgame: Temps de jeu : 1500 secondes (25 min)
2026-09-01 14:45:00 [INFO] save_profile_endgame: Synchronisation des saves du profil 'Guest'
2026-09-01 14:45:02 [INFO] save_profile_endgame: 1 fichier(s) modifié(s) synchronisé(s)
```

---

## 🎯 Gestion des Favoris par profil

Chaque profil peut gérer ses propres favoris EmulationStation de manière indépendante.

### Configuration

La section `favorites` de `profile_config.json` active ou désactive le suivi :

```json
{
  "favorites": {"enabled": 1}
}
```

- `1` : gestion active des favoris pour ce profil
- `0` : gestion désactivée, les favoris existants ne sont pas modifiés

### Comportement lors du changement de profil

#### ✅ `favorites.enabled = 1` (Actif)

**Cas 1 : Fichier `favorites.json` n'est pas vide (Profil1)**
- Tous les favoris actuels sont retirés (nettoyage)
- Les favoris du profil sont appliqués depuis `profiles/<profil>/favorites.json`
- EmulationStation redémarre pour recharger la liste

**Cas 2 : Fichier `favorites.json` est vide (Guest)**
- Tous les favoris actuels sont retirés (réinitialisation)
- Aucun nouveau favoris n'est appliqué
- EmulationStation redémarre

#### ❌ `favorites.enabled = 0` (Inactif)

- Aucune action n'est effectuée
- Les favoris existants sont conservés
- Pas de redémarrage d'EmulationStation
- Utile pour les profils temporaires ou invité

### Fichier `favorites.json`

Le fichier `profiles/<profil>/favorites.json` contient la liste des favoris à appliquer :

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

### Scripts associés

- **Export** : `Favorites export(sync).py` — exporte les favoris actuels vers `favorites.json`
- **Apply** : `swap_profile[rungame].py` — applique automatiquement les favoris lors du changement de profil
- **Utility** : `recalbox_favorites.py` — utilitaire utilisé en arrière-plan (provient du projet [recalbox-rom-list-manager](https://github.com/jffella/recalbox-rom-list-manager) de jffella)

### Procédure de gestion des favoris

**Étape 1 : Prérequis**
- Vous devez être sur le bon profil
- Effectuez votre sélection de favoris (ou passez à l'étape 2 si elle est déjà effectuée)

**Étape 2 : Sauvegarder les favoris**
> La sauvegarde manuelle des favoris est recommandée car elle n'est pas une action quotidienne, ce qui évite les appels répétitifs sans créer de redondance inutile.

- Utilisez le script `ES Reboot` (Menu → Avancé → Scripts utilisateur) pour redémarrer EmulationStation uniquement, ou effectuez un redémarrage normal de Recalbox
- Après le redémarrage, utilisez le script `Favorites export` (Menu → Avancé → Scripts utilisateur)
- Le fichier JSON sera créé dans le dossier `profiles/`, les favoris seront chargés et EmulationStation redémarrera automatiquement

**Étape 3 : Changer de profil**
- Changez de profil
- Répétez les étapes 1 et 2

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

- `Favorites export(sync).py`
  - Exporte les favoris EmulationStation du profil actif vers
    `profiles/<profil>/favorites.json`
  - L'export est effectué seulement lorsque `favorites.enabled` vaut `1`


## 📊 Dashboard des statistiques

Le script `share/userscripts/manual/generate_dashboard.py` génère un tableau de bord HTML à partir des fichiers `game_time.json` de tous les profils. Il inclut :

- le temps de jeu total, le nombre de jeux uniques, le système le plus joué et le profil le plus actif ;
- un onglet par profil avec le temps total, les lancements, les favoris et la répartition par système ;
- les jeux les plus joués, avec recherche et tri par nom, système, durée ou nombre de lancements ;
- un thème sombre ou clair mémorisé dans le navigateur.

Un profil est pris en compte lorsqu'il contient `profile_config.json`. Les statistiques affichées proviennent de `game_time.json` et sont produites par les scripts `game_stats[rungame].py` et `game_stats[endgame].py`. Le fichier est généré par défaut ici :

```text
/recalbox/share/profiles/dashboard.html
```

Pour le générer sur Recalbox :

```bash
python3 /recalbox/share/userscripts/manual/generate_dashboard.py
```

Des chemins personnalisés peuvent être utilisés pour un test ou une prévisualisation :

```bash
python3 /recalbox/share/userscripts/manual/generate_dashboard.py \
  --profiles-dir /recalbox/share/profiles \
  --output /recalbox/share/profiles/dashboard.html
```

Ouvrir ensuite `dashboard.html` dans un navigateur. Le générateur ne modifie pas les statistiques ni la configuration des profils.

---

## 🛡️ Remarques

- Les scripts utilisent `/recalbox/share/` et `/tmp/es_state.inf`  
- Le système `profiles` doit être ignoré dans les scripts de save/load  
- `current_profile.json` doit exister et être valide  
- Vérifier les permissions d’écriture sur `share/profiles/` et `share/saves/`  

License: GPLv3
