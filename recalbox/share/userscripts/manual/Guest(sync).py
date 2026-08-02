#!/usr/bin/env python3
import os
import shutil
import json

# Nom du profil à activer. Ici "Guest", mais peut être remplacé par n'importe quel profil.
PROFILE_NAME = "Guest"

# Répertoire principal de Recalbox (stockage persistant)
BASE_DIR = "/recalbox/share"

# Dossier où sont stockées les sauvegardes du profil sélectionné
PROFILE_DIR = f"{BASE_DIR}/profiles/{PROFILE_NAME}"

# Dossier des sauvegardes utilisées par Recalbox pendant le jeu
SAVES_DIR = f"{BASE_DIR}/saves"

# Fichier JSON indiquant quel profil est actuellement actif
CONFIG_FILE = f"{BASE_DIR}/profiles/current_profile.json"


def ensure_dirs():
    """
    Crée les dossiers nécessaires si ils n'existent pas déjà :
    - Le dossier du profil
    - Le dossier des sauvegardes Recalbox
    """
    os.makedirs(PROFILE_DIR, exist_ok=True)
    os.makedirs(SAVES_DIR, exist_ok=True)


def clean_recalbox_saves():
    """
    Supprime toutes les sauvegardes actuellement présentes dans /saves.
    Cela permet de repartir d'un dossier vide avant de restaurer les sauvegardes du profil.
    """
    for root, dirs, files in os.walk(SAVES_DIR):
        # Suppression des fichiers
        for f in files:
            os.remove(os.path.join(root, f))
        # Suppression des dossiers (ex: dossiers par émulateur)
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def restore_profile_saves():
    """
    Copie les sauvegardes du profil sélectionné vers le dossier /saves.
    - Les dossiers sont copiés récursivement.
    - Les fichiers individuels sont copiés tels quels.
    """
    if not os.path.exists(PROFILE_DIR):
        return

    for item in os.listdir(PROFILE_DIR):
        src = os.path.join(PROFILE_DIR, item)
        dst = os.path.join(SAVES_DIR, item)

        # Si c'est un dossier, copie complète
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            # Sinon copie simple du fichier
            shutil.copy2(src, dst)


def save_current_profile():
    """
    Enregistre le profil actif dans current_profile.json.
    Ce fichier est utilisé par les scripts de sauvegarde automatique (ex: EndGame).
    """
    with open(CONFIG_FILE, "w") as f:
        json.dump({"profile": PROFILE_NAME}, f)


def main():
    """
    Processus complet :
    1. Vérifie/crée les dossiers nécessaires
    2. Nettoie les sauvegardes actuelles
    3. Restaure les sauvegardes du profil choisi
    4. Enregistre le profil comme actif
    """
    ensure_dirs()
    clean_recalbox_saves()
    restore_profile_saves()
    save_current_profile()

    print(f"Switched to {PROFILE_NAME} profile successfully.")


if __name__ == "__main__":
    main()
