#!/usr/bin/env python3
"""
Script de swap de profil pour Recalbox
Détecte quand une ROM du système "profiles" est lancée et met à jour le profil courant.
Événement : rungame
"""

import os
import json
import subprocess
from datetime import datetime

# Fichier généré par EmulationStation indiquant l'état (lancement/fin de jeu)
STATE_FILE = "/tmp/es_state.inf"

# Fichier du profil courant
CURRENT_PROFILE_FILE = "/recalbox/share/profiles/current_profile.json"

# Dossier des profils disponibles
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
    Exemple de contenu :
        Action=StartGame
        SystemId=profiles
        Game=Guest
        GamePath: /recalbox/share/roms/profiles_swap/Guest.zip
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


def get_profile_name_from_game(game_name, game_path):
    """
    Extrait le nom du profil à partir du nom du jeu ou du chemin du fichier.
    Exemples:
        - game_name = "Guest" -> "Guest"
        - game_path = "/recalbox/share/roms/profiles_swap/Profil1.zip" -> "Profil1"
    """
    # D'abord essayer d'extraire du game_path (sans extension)
    if game_path:
        filename = os.path.basename(game_path)
        profile_name = os.path.splitext(filename)[0]
        return profile_name

    # Sinon utiliser le game_name
    return game_name


def profile_exists(profile_name):
    """
    Vérifie si le dossier du profil existe.
    """
    profile_path = os.path.join(PROFILES_DIR, profile_name)
    return os.path.isdir(profile_path)


def update_current_profile(profile_name):
    """
    Met à jour le fichier current_profile.json avec le nouveau profil.
    """
    profile_data = {"profile": profile_name}
    
    try:
        with open(CURRENT_PROFILE_FILE, "w") as f:
            json.dump(profile_data, f)
        return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour du profil: {e}")
        return False


def kill_game():
    """
    Termine le jeu en cours (puisque c'est juste un sélecteur de profil).
    """
    try:
        # Utiliser 'killall' ou 'pkill' pour terminer le processus du jeu
        subprocess.run(["pkill", "-f", "retroarch"], timeout=5)
    except Exception as e:
        print(f"Erreur lors de la terminaison du jeu: {e}")


def main():
    info = read_state_file()
    
    # Récupérer le SystemId (peut être "profiles" ou autre)
    system_id = info.get("SystemId", "").lower()
    
    # Vérifier si c'est le système de profils
    if system_id != "profiles":
        return
    
    # Récupérer le nom du jeu et le chemin
    game_name = info.get("Game", "")
    game_path = info.get("GamePath", "")
    
    if not game_name and not game_path:
        return
    
    # Extraire le nom du profil
    profile_name = get_profile_name_from_game(game_name, game_path)
    
    # Vérifier que le profil existe
    if not profile_exists(profile_name):
        print(f"Profil '{profile_name}' non trouvé dans {PROFILES_DIR}")
        return
    
    # Mettre à jour le profil courant
    if update_current_profile(profile_name):
        print(f"Profil changé en: {profile_name}")
        # Logger l'événement de changement de profil
        log_event("system", system_id, "ProfileSwap", profile_name)
    
    # Terminer le jeu (qui n'est qu'un sélecteur)
    kill_game()


if __name__ == "__main__":
    main()
