# Changelog

Toutes les modifications importantes du projet sont documentées ici.

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
