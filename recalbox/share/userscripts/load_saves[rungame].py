#!/usr/bin/env python3
"""
Script de chargement des saves au lancement d'un jeu
Restaure les saves de l'utilisateur depuis le profil courant vers /recalbox/share/saves
Événement : rungame
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime

# Fichier généré par EmulationStation indiquant l'état (lancement/fin de jeu)
STATE_FILE = "/tmp/es_state.inf"

# Fichier du profil courant
CURRENT_PROFILE_FILE = "/recalbox/share/profiles/current_profile.json"

# Dossiers des saves
SHARES_SAVES_DIR = "/recalbox/share/saves"

# Dossier des profils
PROFILES_DIR = "/recalbox/share/profiles"

# Fichier de log unique
LOG_FILE = "/recalbox/share/profiles/profiles.log"


def log_event(log_type, system_id, action, profile):
    """
    Log au format :
    [system] - [YYYY-MM-DD HH:MM:SS] - profiles - ProfileSwap - nom_du_profil
    """
    os.makedirs(PROFILES_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = f"[{log_type}] | [{timestamp}] | {system_id} | {action} | {profile}"

    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"Erreur lors de l'écriture dans le log: {e}")


def read_state_file():
    """
    Lit le fichier es_state.inf et retourne un dictionnaire clé/valeur.
    """
    info = {}

    if not os.path.exists(STATE_FILE):
        return info

    with open(STATE_FILE, "r") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                info[key] = value

    return info


def read_current_profile():
    """
    Lit le fichier current_profile.json et retourne le nom du profil.
    """
    if not os.path.exists(CURRENT_PROFILE_FILE):
        return None

    try:
        with open(CURRENT_PROFILE_FILE, "r") as f:
            data = json.load(f)
            return data.get("profile", None)
    except Exception as e:
        print(f"Erreur lors de la lecture du profil courant: {e}")
        return None


def get_game_name_from_path(game_path):
    """
    Extrait le nom du jeu depuis le chemin du fichier (sans extension).
    Exemple: "/recalbox/share/roms/gba/Breath of Fire.zip" -> "Breath of Fire"
    """
    if not game_path:
        return None
    
    filename = os.path.basename(game_path)
    game_name = os.path.splitext(filename)[0]
    return game_name


def find_save_files(profile_name, system_id, game_name):
    """
    Cherche les fichiers de saves du jeu dans le dossier du profil.
    Exemple: /recalbox/share/profiles/Guest/gba/Breath of Fire.*
    
    Retourne une liste de chemins complets vers les fichiers de saves.
    """
    save_files = []
    
    profile_game_dir = os.path.join(PROFILES_DIR, profile_name, system_id)
    
    if not os.path.isdir(profile_game_dir):
        return save_files
    
    # Chercher tous les fichiers qui commencent par le nom du jeu
    for filename in os.listdir(profile_game_dir):
        if filename.startswith(game_name + "."):
            file_path = os.path.join(profile_game_dir, filename)
            if os.path.isfile(file_path):
                save_files.append(file_path)
    
    return save_files


def restore_save_file(profile_save_path, system_id, game_name):
    """
    Copie un fichier de save du profil vers le dossier share/saves.
    """
    # Créer le répertoire cible s'il n'existe pas
    target_dir = os.path.join(SHARES_SAVES_DIR, system_id)
    os.makedirs(target_dir, exist_ok=True)
    
    # Récupérer le nom du fichier avec son extension
    filename = os.path.basename(profile_save_path)
    
    # Chemin cible
    target_path = os.path.join(target_dir, filename)
    
    try:
        shutil.copy2(profile_save_path, target_path)
        print(f"Save restaurée: {filename}")
        return True
    except Exception as e:
        print(f"Erreur lors de la restauration de {filename}: {e}")
        return False


def main():
    # Ne pas traiter le système "profiles"
    info = read_state_file()
    system_id = info.get("SystemId", "").lower()
    
    if system_id == "profiles":
        return
    
    # Récupérer le profil courant
    profile_name = read_current_profile()
    
    if not profile_name:
        print("Aucun profil courant défini")
        return
    
    # Récupérer les infos du jeu
    game_path = info.get("GamePath", "")
    game_name = get_game_name_from_path(game_path)
    
    if not game_name:
        return
    
    # Chercher et restaurer les saves
    save_files = find_save_files(profile_name, system_id, game_name)
    
    if not save_files:
        # Pas de saves trouvées, c'est normal
        pass
    else:
        print(f"Restauration des saves pour {game_name} ({system_id}) depuis profil {profile_name}")
        
        for save_file in save_files:
            restore_save_file(save_file, system_id, game_name)
    
    # Logger l'événement de lancement du jeu
    log_event(profile_name, system_id, "GameStart", game_name)



if __name__ == "__main__":
    main()
