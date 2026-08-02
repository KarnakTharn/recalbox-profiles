# recalbox-profiles

Gestion des sauvegardes avec profils utilisateur pour Recalbox.


## Objectif

Permettre la gestion de plusieurs profils de sauvegarde Recalbox en isolant les fichiers de chaque profil.

> Fonction basique : copier et remplace l'intégralité des dossiers/fichiers save pour les profiles.

- `recalbox/share/profiles/<Profil>/` : sauvegardes spécifiques à un profil.
- `recalbox/share/saves/` : sauvegardes actives utilisées par Recalbox pendant le jeu.
- `recalbox/share/profiles/current_profile.json` : fichier qui contient le profil actuellement actif.

Scripts fournis :

- `Guest.py` : exemple de profil prêt à l’emploi.
- `ProfileName.py` : modèle à copier pour créer un nouveau profil.
- `Save_profile.py` : sauvegarde les fichiers du profil actif.

## Structure exemple final attendu

```text
recalbox/
  share/
    profiles/
      current_profile.json
      Guest/
        megadrive/
          Aladdin.state
          Alex Kidd in the Enchanted Castle.state
      ProfileName/
        gb/
        megadrive/
          Alex Kidd in the Enchanted Castle.state
    saves/
      megadrive/
        Aladdin.state
        Alex Kidd in the Enchanted Castle.state
    userscripts/
      manual/
        Guest.py
        ProfileName.py
        Save_profile.py
```

## Format du profil actif

Le fichier `recalbox/share/profiles/current_profile.json` contient le nom du profil actif :

```json
{"profile": "Guest"}
```

## Installation

1. Copier le dossier `/recalbox/share/userscripts` avec les scripts.
2. Les dossiers `recalbox/share/profiles`, `recalbox/share/saves`, et `tmp` sont des exemples et présent pour les test.

## Utilisation

### Activer/Créer un profil

1. Dupliquer `ProfileName.py` et renommer le fichier selon le profil souhaité.
2. Modifier `PROFILE_NAME = "ProfileName"` pour le nom du profil.
3. Lancer le script depuis Recalbox :
   > `START` → `Paramètres avancés` → `Scripts utilisateur`

Le script :
- crée `recalbox/share/profiles/<Profil>/` si nécessaire,
- vide `recalbox/share/saves/`,
- copie le contenu du profil vers `recalbox/share/saves/`,
- met à jour `recalbox/share/profiles/current_profile.json`.

### Sauvegarder les fichiers de jeu

1. Utiliser `Save_profile.py` pour copier les sauvegardes présentes dans `recalbox/share/saves/` vers le dossier du profil actif.
2. Ce script lit `recalbox/share/profiles/current_profile.json` pour déterminer le profil actif.
3. Lancer le script depuis le menu de Recalbox
    > `START` → `Paramètres avancés` → `Scripts utilisateur`  
4. Si aucun profil n’est défini, le script ne fera rien.


## Détails des scripts

### `Guest.py`

- Active le profil `Guest`.
- Vide le dossier `saves/` pour repartir d’un état propre.
- Copie toutes les sauvegardes du profil `Guest` dans `saves/`.
- Met à jour `current_profile.json`.

### `ProfileName.py`

- Modèle de script pour créer un nouveau profil.
- Remplacer `PROFILE_NAME = "ProfileName"` par le nom du profil souhaité.

### `Save_profile.py`

- Sauvegarde le contenu de `saves/` vers le dossier du profil actif.
- Conserve les sous-dossiers d’émulateur.
- Supprime l’ancienne version des sauvegardes du même dossier avant copie.

## Remarques

- Les scripts sont conçus pour fonctionner sur une installation Recalbox où le chemin `/recalbox/share` est accessible.
- Vérifier les permissions d’écriture dans les dossiers `profiles/` et `saves/`.
- Garder le fichier `current_profile.json` à jour pour garantir que les sauvegardes sont correctement associées au profil.