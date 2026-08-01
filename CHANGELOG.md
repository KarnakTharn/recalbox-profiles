# Changelog

Toutes les modifications importantes du projet sont documentées ici.

## [1.0.0] - 2026-08-02

### Ajout
- Gestion des profils de sauvegarde pour Recalbox.
- Chargement d’un profil :
  - suppression des sauvegardes actuelles dans `recalbox/share/saves/`,
  - copie des sauvegardes depuis `recalbox/share/profiles/<profil>/` vers `recalbox/share/saves/`,
  - création ou mise à jour de `recalbox/share/profiles/current_profile.json`.
- Sauvegarde du profil actif :
  - copie des fichiers de `recalbox/share/saves/` vers `recalbox/share/profiles/<profil>/`.
