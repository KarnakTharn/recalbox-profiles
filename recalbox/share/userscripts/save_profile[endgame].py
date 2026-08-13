#!/usr/bin/env python3
"""
Script de sauvegarde des saves à la fin d'un jeu
Copie intelligemment les saves de /recalbox/share/saves vers le dossier du profil courant
Ne copie que les fichiers qui ont été modifiés après leur dernière copie
Événement : endgame
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime

# Fichier généré par EmulationStation indiquant l'état (fin de jeu)
STATE_FILE = "/tmp/es_state.inf"

# Fichier du profil courant
CURRENT_PROFILE_FILE = "/recalbox/share/profiles/current_profile.json"

# Dossiers des saves
SHARES_SAVES_DIR = "/recalbox/share/saves"

# Dossier des profils
PROFILES_DIR = "/recalbox/share/profiles"

# Fichier de manifest pour tracker les dates de synchronisation
SYNC_MANIFEST_FILE = "/recalbox/share/profiles/.sync_manifest.json"

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


def load_sync_manifest():
    """
    Charge le manifest de synchronisation (suivi des dates de copie).
    """
    if os.path.exists(SYNC_MANIFEST_FILE):
        try:
            with open(SYNC_MANIFEST_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur lors de la lecture du manifest: {e}")
    
    return {}


def save_sync_manifest(manifest):
    """
    Sauvegarde le manifest de synchronisation.
    """
    os.makedirs(PROFILES_DIR, exist_ok=True)
    try:
        with open(SYNC_MANIFEST_FILE, "w") as f:
            json.dump(manifest, f, indent=2)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du manifest: {e}")


def file_modified_after(source_path, sync_timestamp):
    """
    Vérifie si le fichier source a été modifié après la dernière synchronisation.
    """
    if not os.path.exists(source_path):
        return False
    
    file_mtime = os.path.getmtime(source_path)
    
    # Si pas de timestamp de sync, copier le fichier
    if not sync_timestamp:
        return True
    
    # Comparer les timestamps
    return file_mtime > sync_timestamp


def find_save_files(system_id, game_name):
    """
    Cherche les fichiers de saves du jeu dans /recalbox/share/saves.
    Exemple: /recalbox/share/saves/gba/Breath of Fire.*
    
    Retourne une liste de chemins complets vers les fichiers de saves.
    """
    save_files = []
    
    system_save_dir = os.path.join(SHARES_SAVES_DIR, system_id)
    
    if not os.path.isdir(system_save_dir):
        return save_files
    
    # Chercher tous les fichiers qui commencent par le nom du jeu
    for filename in os.listdir(system_save_dir):
        if filename.startswith(game_name + "."):
            file_path = os.path.join(system_save_dir, filename)
            if os.path.isfile(file_path):
                save_files.append(file_path)
    
    return save_files


def copy_save_file(source_path, profile_name, system_id, game_name):
    """
    Copie un fichier de save vers le dossier du profil.
    Crée les répertoires s'il le faut.
    """
    # Créer le répertoire cible s'il n'existe pas
    target_dir = os.path.join(PROFILES_DIR, profile_name, system_id)
    os.makedirs(target_dir, exist_ok=True)
    
    # Récupérer le nom du fichier avec son extension
    filename = os.path.basename(source_path)
    
    # Chemin cible
    target_path = os.path.join(target_dir, filename)
    
    try:
        shutil.copy2(source_path, target_path)
        print(f"Save copiée: {filename}")
        return True
    except Exception as e:
        print(f"Erreur lors de la copie de {filename}: {e}")
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
    
    # Charger le manifest de synchronisation
    manifest = load_sync_manifest()
    
    # Chercher les saves
    save_files = find_save_files(system_id, game_name)
    
    if not save_files:
        # Pas de saves trouvées, c'est normal
        return
    
    print(f"Sauvegarde des saves pour {game_name} ({system_id}) vers profil {profile_name}")
    
    # Copier les saves modifiées
    current_time = datetime.now().timestamp()
    
    for save_file in save_files:
        # Créer une clé unique pour ce fichier dans le manifest
        manifest_key = f"{profile_name}:{system_id}:{os.path.basename(save_file)}"
        
        # Récupérer le timestamp de la dernière synchro
        last_sync = manifest.get(manifest_key, None)
        
        # Vérifier si le fichier a été modifié
        if file_modified_after(save_file, last_sync):
            if copy_save_file(save_file, profile_name, system_id, game_name):
                # Mettre à jour le manifest avec le nouveau timestamp
                manifest[manifest_key] = current_time
    
    # Sauvegarder le manifest mis à jour
    save_sync_manifest(manifest)
    
    # Logger l'événement de fin du jeu
    log_event(profile_name, system_id, "GameEnd", game_name)



if __name__ == "__main__":
    main()
