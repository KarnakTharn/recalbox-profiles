#!/usr/bin/env python3
import os
import shutil
import json

# Nom du profil à activer.
# Ce script est prévu pour être dupliqué ou appelé avec un nom de profil différent.
PROFILE_NAME = "ProfileName"  # Remplacer par le nom du profil souhaité

# Répertoire principal de Recalbox (stockage persistant)
BASE_DIR = "/recalbox/share"

# Dossier contenant les sauvegardes propres au profil sélectionné
PROFILE_DIR = f"{BASE_DIR}/profiles/{PROFILE_NAME}"

# Dossier utilisé par Recalbox pour stocker les sauvegardes actives
SAVES_DIR = f"{BASE_DIR}/saves"

# Fichier JSON indiquant quel profil est actuellement actif
CONFIG_FILE = f"{BASE_DIR}/profiles/current_profile.json"


def ensure_dirs():
    """
    Crée les dossiers nécessaires si ils n'existent pas déjà :
    - Le dossier du profil (où sont stockées ses sauvegardes)
    - Le dossier des sauvegardes Recalbox
    """
    os.makedirs(PROFILE_DIR, exist_ok=True)
    os.makedirs(SAVES_DIR, exist_ok=True)


def clean_recalbox_saves():
    """
    Supprime toutes les sauvegardes actuellement présentes dans /saves.
    Cela permet de repartir d'un dossier totalement vide avant de restaurer
    les sauvegardes du profil sélectionné.
    """
    for root, dirs, files in os.walk(SAVES_DIR):
        # Suppression des fichiers
        for f in files:
            os.remove(os.path.join(root, f))
        # Suppression des dossiers (ex : dossiers par émulateur)
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def restore_profile_saves():
    """
    Copie les sauvegardes du profil sélectionné vers le dossier /saves.
    - Les dossiers sont copiés récursivement.
    - Les fichiers individuels sont copiés tels quels.
    Si le profil n'a pas encore de sauvegardes, la fonction ne fait rien.
    """
    if not os.path.exists(PROFILE_DIR):
        return

    for item in os.listdir(PROFILE_DIR):
        src = os.path.join(PROFILE_DIR, item)
        dst = os.path.join(SAVES_DIR, item)

        # Copie récursive si c'est un dossier
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            # Copie simple si c'est un fichier
            shutil.copy2(src, dst)


def save_current_profile():
    """
    Enregistre le profil actif dans current_profile.json.
    Ce fichier est utilisé par les scripts automatiques (ex : backup à EndGame)
    pour savoir dans quel dossier sauvegarder les fichiers.
    """
    with open(CONFIG_FILE, "w") as f:
        json.dump({"profile": PROFILE_NAME}, f)


def main():
    """
    Processus complet :
    1. Vérifie/crée les dossiers nécessaires
    2. Nettoie les sauvegardes actuelles de Recalbox
    3. Restaure les sauvegardes du profil sélectionné
    4. Enregistre le profil comme actif
    """
    ensure_dirs()
    clean_recalbox_saves()
    restore_profile_saves()
    save_current_profile()

    print(f"Switched to {PROFILE_NAME} profile successfully.")


if __name__ == "__main__":
    main()
