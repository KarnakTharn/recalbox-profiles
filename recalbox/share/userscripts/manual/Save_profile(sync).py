#!/usr/bin/env python3
import os
import shutil
import json
import sys

# Répertoire principal de Recalbox (partage réseau / stockage persistant)
BASE_DIR = "/recalbox/share"

# Fichier contenant le profil actuellement sélectionné
CONFIG_FILE = f"{BASE_DIR}/profiles/current_profile.json"

# Fichier généré par EmulationStation indiquant l'état (lancement/fin de jeu)
STATE_FILE = "/tmp/es_state.inf"

# Répertoire où Recalbox stocke les sauvegardes des émulateurs
SAVES_DIR = f"{BASE_DIR}/saves"


def load_current_profile():
    """
    Charge le profil actuellement actif depuis current_profile.json.
    Retourne le nom du profil ou None si le fichier n'existe pas.
    """
    if not os.path.exists(CONFIG_FILE):
        return None

    with open(CONFIG_FILE) as f:
        data = json.load(f)
        return data.get("profile")


def parse_state_file():
    """
    Lit le fichier es_state.inf généré par EmulationStation.
    Ce fichier contient des lignes du type 'Action=EndGame', 'SystemId': 'megadrive', 'Game': 'Aladdin'.
    On retourne un dictionnaire clé/valeur.
    """
    info = {}

    if not os.path.exists(STATE_FILE):
        return info

    with open(STATE_FILE) as f:
        for line in f:
            if "=" in line:
                print(line.strip())  # Affiche la ligne pour debug
                k, v = line.strip().split("=", 1)
                info[k] = v

    return info


def backup_saves(profile):
    """
    Sauvegarde les fichiers de sauvegarde du dossier /saves
    vers le dossier du profil sélectionné.
    - Si un dossier existe déjà dans le profil, il est supprimé avant copie.
    - Les fichiers individuels sont copiés tels quels.
    """
    profile_dir = f"{BASE_DIR}/profiles/{profile}"

    # Crée le dossier du profil s'il n'existe pas
    os.makedirs(profile_dir, exist_ok=True)

    # Parcourt tous les éléments du dossier saves
    for item in os.listdir(SAVES_DIR):
        src = os.path.join(SAVES_DIR, item)
        dst = os.path.join(profile_dir, item)
        print(f"Copie de {src} vers {dst}")  # Affiche ce qui est copié pour debug

        # Si c'est un dossier (ex: un émulateur), on copie récursivement
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)  # On supprime l'ancienne version
            shutil.copytree(src, dst)
        else:
            # Fichier simple → copie directe
            shutil.copy2(src, dst)


def main():
    """
    Fonction principale :
    - Charge le profil actif
    - Lit l'état d'EmulationStation
    - Sauvegarde les saves si un profil est actif
    """
    profile = load_current_profile()

    # Si aucun profil n'est défini, on ne fait rien
    if not profile:
        sys.exit(0)

    state = parse_state_file()

    ## Exemple de contenu de state pour debug :
    # state = {'Version': '2.0',
    #         'Action': 'gamelistbrowsing', 
    #         'ActionData': '/recalbox/share/roms/megadrive/Aladdin.zip', 
    #         'System': 'Sega Megadrive', 
    #         'SystemId': 'megadrive', 
    #         'Game': 'Aladdin', 
    #         'GamePath': '/recalbox/share/roms/megadrive/Aladdin.zip', 
    #         'ImagePath': '/recalbox/share/roms/megadrive/downloaded_images/Aladdin-image.png', 
    #         'IsFolder': '0', 
    #         'ThumbnailPath': '', 
    #         'VideoPath': '', 
    #         'Developer': 'Virgin', 
    #         'Publisher': 'Sega - Virgin', 
    #         'Players': '1', 
    #         'Region': '', 
    #         'Genre': 'Plateforme', 
    #         'GenreId': '0', 
    #         'Favorite': '0', 
    #         'Hidden': '0', 
    #         'Adult': '0', 
    #         'Emulator': 'libretro', 
    #         'Core': 'picodrive', 
    #         'DefaultEmulator': 'libretro', 
    #         'DefaultCore': 'picodrive', 
    #         'State': 'selected'}

    # Si tu veux activer la sauvegarde uniquement à la fin d'un jeu,
    # décommente les lignes ci-dessous :
    #
    # action = state.get("Action", "").lower()
    # if action != "endgame":
    #     sys.exit(0)

    # Lance la sauvegarde
    backup_saves(profile)
    print(f"Sauvegardes copiées pour le profil : {profile}")


if __name__ == "__main__":
    main()
