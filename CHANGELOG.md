# Changelog

## [2.5.1] - 2026-09-07

### Modification
- Architecture : modification du chemin des sauvegardes par profil de `profiles/<profile>/roms/` vers `profiles/<profile>/saves/` pour plus de cohérence avec Recalbox.
- Statistiques : ajout d'un seuil minimal de 5 minutes pour comptabiliser le temps de jeu (`timeplayed`) et le nombre de lancements (`playcount`).
- Statistiques : exclusion des systèmes `profiles` et `imageviewer` du suivi.
- Correction de bugs : résolution d'erreurs d'imports et de fonctions non définies dans `save_profile[endgame].py`.
- Sauvegardes : suppression des fichiers résiduels d'un jeu lors du changement de profil, notamment les sauvegardes d'état numérotées (`game.state1`, `game.state1.jpg`).
- Thème : mise à jour des descriptions française et anglaise avec le nom du profil actif lors d'un changement de profil, selon le chemin défini dans `current_theme.json`.

## [2.5.0] - 2026-09-06

### Ajout
- Gestion des comptes Patreon par profil : injection automatique de la clé privée dans `recalbox.conf` lors du changement de profil.
- Procédure de récupération manuelle de la clé Patreon pour la première installation.
- Compatibilité avec Recalbox 10.1 (testée et vérifiée après migration depuis la version 10.0.8).

## [2.4.0] - 2026-09-06

### Ajout
- Gestion des captures d'écran par profil : sauvegarde automatique des screenshots du dossier global vers le dossier du profil.
- Nettoyage automatique du dossier de screenshots du profil avant chaque sauvegarde pour éviter les fichiers obsolètes.

## [2.3.0] - 2026-09-01

### Ajout
- Gestion des favoris EmulationStation par profil via la section `favorites` de `profile_config.json`.
- Export manuel des favoris du profil actif vers `profiles/<profil>/favorites.json`.
- Application automatique des favoris du profil lors de sa sélection : retrait des favoris actifs, application du fichier JSON, puis redémarrage d'EmulationStation.
- Générateur de dashboard HTML via `generate_dashboard.py`, avec synthèse globale, onglets par profil, répartition par système, recherche et tri des jeux.
- Refonte du système de log.

### Modification
- Ajout de la documentation française et anglaise du flux de sauvegarde et de restauration des favoris.

## [2.2.0] - 2026-09-01

### Ajout
- Suivi des statistiques de jeu par profil via `game_stats[rungame].py` et `game_stats[endgame].py`.
- Enregistrement de `timeplayed` (en secondes), `playcount` et `lastplayed` dans `profiles/<profil>/game_time.json`.
- État temporaire `active_game` dans `current_profile.json` pour calculer la durée entre les événements `rungame` et `endgame`.
- Option `stats.enabled` dans la configuration du profil pour activer ou désactiver le suivi des statistiques.

### Modification
- Remplacement de `RA_config.json` par `profile_config.json`, une configuration générique par profil.
- Déplacement des paramètres RetroAchievements dans la section `retroachievements` de `profile_config.json`.
- Mise à jour des README français et anglais pour documenter la configuration et les statistiques.

## [2.1.0] - 2026-08-20

### Ajout
- Gestion des compte RetroAchievements (RA) en fonction du profil.


## [2.0.0] - 2026-08-14

### Ajout
- Documentation technique complète dans `v2.md` couvrant la configuration de Recalbox Next.
- Images d'exemple dans le README montrant l'affichage du système `profiles` et de la gamelist.
- Thème Recalbox Next supporté pour le système `profiles`.
- Configuration détaillée du système custom `profiles` avec UUID unique.
- Sélecteurs de profil (`Guest.zip`, `Profil1.zip`) affichés dans EmulationStation.

### Modification
- Path corrigé pour le système `profiles` : `%ROOT%/profiles` (au lieu de `%ROOT%/profiles_swap`).
- Theme corrigé : `profiles` (au lieu de `profiles_swap`) pour correspondre au fichier de thème Recalbox Next.
- Documentation README mise à jour avec étapes de configuration détaillées.
- Format de log unifié entre tous les scripts.

### Détails techniques
- **systemlist.xml** : Ajout du système custom avec UUID `21b8873a-a93e-409c-ad0c-8bb6d682bef8`.
- **Thème Recalbox Next** : Support du système `profiles` via `recalbox/share/themes/recalbox-next/_views/_partials/systems/profiles.xml`.
- **ROMs de sélection** : Archive ZIP vides utilisées pour sélectionner les profils.
- **Manifest de synchronisation** : Tracking intelligent des modifications avec `.sync_manifest.json`.


## [1.0.1] - 2026-08-02
### Modification
- script synchrone, bloque ES jusqu'à la fin de l'exécution du script.


## [1.0.0] - 2026-08-02

### Ajout
- Gestion des profils de sauvegarde pour Recalbox.
- Chargement d’un profil :
  - suppression des sauvegardes actuelles dans `recalbox/share/saves/`,
  - copie des sauvegardes depuis `recalbox/share/profiles/<profil>/` vers `recalbox/share/saves/`,
  - création ou mise à jour de `recalbox/share/profiles/current_profile.json`.
- Sauvegarde du profil actif :
  - copie des fichiers de `recalbox/share/saves/` vers `recalbox/share/profiles/<profil>/`.
