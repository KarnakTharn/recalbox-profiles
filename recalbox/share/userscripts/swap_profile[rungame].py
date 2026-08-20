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
import signal
import time
import xml.etree.ElementTree as ET
from shutil import copy2
import tempfile

# Fichier généré par EmulationStation indiquant l'état (lancement/fin de jeu)
STATE_FILE = "/tmp/es_state.inf"

# Fichier du profil courant
CURRENT_PROFILE_FILE = "/recalbox/share/profiles/current_profile.json"

# Dossier des profils disponibles
PROFILES_DIR = "/recalbox/share/profiles"

# Fichier de log unique
LOG_FILE = "/recalbox/share/profiles/profiles.log"

# Fichier gamelist.xml pour les profils
GL_PATH = "/recalbox/share/roms/profiles/gamelist.xml"
BACKUP_PATH = GL_PATH + ".bak"
REGION_SELECTED = "fr"
REGION_OTHER = "eu"

# Fichier de configuration de Recalbox
RECALBOX_CONF  = "/recalbox/share/system/recalbox.conf"


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


def find_retroarch_pid():
    """
    Retourne le PID du processus retroarch s'il existe,
    sinon None.
    """
    try:
        # pgrep retourne le PID directement
        pid = subprocess.check_output(["pgrep", "retroarch"]).decode().strip()
        return int(pid)
    except subprocess.CalledProcessError:
        # pgrep retourne un code d'erreur si rien n'est trouvé
        return None

def quit_retroarch(pid):
    """
    Envoie un signal SIGINT au processus RetroArch.
    """
    try:
        os.kill(pid, signal.SIGINT)
        print(f"Signal SIGINT envoyé au processus {pid}.")
    except ProcessLookupError:
        print("Le processus RetroArch n'existe plus.")
    except PermissionError:
        print("Permission refusée pour envoyer le signal.")


def kill_game():
    """
    Termine le jeu en cours (puisque c'est juste un sélecteur de profil).
    """
    pid = find_retroarch_pid()

    if pid is None:
        print("Aucun jeu RetroArch en cours n'a été trouvé.")
    else:
        print(f"Jeu en cours trouvé avec PID : {pid}")
        quit_retroarch(pid)

# Changement visuel de sélection de profil dans EmulationStation
## Changement de la region dans le fichier gamelist.xml ne fonctionne pas. Exemple region fr -> profil sélectionné et eu -> profil non sélectionné. CF archive_script/modif_xml.py
## Changement du fichier image du profil. Exemple image en gris ou noir et blanc pour profil non sélectionné et image en couleur pour profil sélectionné.
def update_gamelist_xml(profile_name):
    """
    Met à jour uniquement le tag <region> dans /recalbox/share/roms/profiles/gamelist.xml.
    - profile_name : nom du profil à marquer en 'fr'
    - les autres jeux auront 'eu'
    Retourne True si OK, False sinon.
    """

    if not os.path.exists(GL_PATH):
        print(f"[update_gamelist_region_only] gamelist introuvable: {GL_PATH}")
        return False

    try:
        tree = ET.parse(GL_PATH)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"[update_gamelist_region_only] erreur parse XML: {e}")
        return False
    except Exception as e:
        print(f"[update_gamelist_region_only] erreur lecture: {e}")
        return False

    changed = False
    for game in root.findall("game"):
        name_el = game.find("name")
        if name_el is None or not name_el.text:
            continue
        name = name_el.text.strip()
        desired_region = REGION_SELECTED if name == profile_name else REGION_OTHER

        region_el = game.find("region")
        if region_el is None:
            # insérer region avant image si possible, sinon à la fin du game
            region_el = ET.Element("region")
            image_el = game.find("image")
            if image_el is not None:
                idx = list(game).index(image_el)
                game.insert(idx, region_el)
            else:
                game.append(region_el)
            region_el.text = desired_region
            changed = True
        else:
            current_region = (region_el.text or "").strip()
            if current_region != desired_region:
                region_el.text = desired_region
                changed = True

    if not changed:
        print("[update_gamelist_region_only] aucune modification nécessaire")
        return True

    # backup et écriture atomique
    try:
        copy2(GL_PATH, BACKUP_PATH)
    except Exception as e:
        print(f"[update_gamelist_region_only] impossible de créer la sauvegarde: {e}")

    try:
        dirpath = os.path.dirname(GL_PATH)
        fd, tmp_path = tempfile.mkstemp(dir=dirpath, prefix="gamelist.", suffix=".xml")
        os.close(fd)
        tree.write(tmp_path, encoding="utf-8", xml_declaration=True)
        os.replace(tmp_path, GL_PATH)
        print(f"[update_gamelist_region_only] gamelist mis à jour pour profil '{profile_name}'")
        return True
    except Exception as e:
        print(f"[update_gamelist_region_only] erreur écriture: {e}")
        # tentative de restauration depuis backup
        try:
            if os.path.exists(BACKUP_PATH):
                copy2(BACKUP_PATH, GL_PATH)
        except Exception:
            pass
        return False

def load_RA_config(profile_name):
    """
    Charge les valeurs RA depuis RA_config.json du profil.
    """
    ra_config_path = os.path.join(PROFILES_DIR, profile_name, "RA_config.json")

    with open(ra_config_path) as f:
        return json.load(f)

def update_recalbox_conf(recalbox_conf, mapping):
    """
    Met à jour recalbox.conf avec les valeurs RA provenant de RA_config.json.
    """
    with open(recalbox_conf) as f:
        lignes = f.readlines()

    with open(recalbox_conf, "w") as f:
        for ligne in lignes:
            for cle, valeur in mapping.items():
                if ligne.startswith(cle):
                    ligne = f"{cle}{valeur}\n"
                    break
            f.write(ligne)


def apply_RA_settings(profile_name):
    """
    Applique les paramètres RA du profil dans recalbox.conf.
    """
    mapping = load_RA_config(profile_name)
    update_recalbox_conf(RECALBOX_CONF, mapping)
    print(f"RetroAchievements mis à jour dans recalbox.conf pour le profil : {profile_name}")
    

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
    time.sleep(5)  # Attendre un peu pour s'assurer que le jeu est bien lancé avant de le tuer
    kill_game()

    # Mettre à jour le fichier gamelist.xml pour refléter le changement de profil (optionnel)
    ## Changement de la region dans le fichier gamelist.xml ne fonctionne pas. Exemple region fr -> profil sélectionné et eu -> profil non sélectionné. CF archive_script/modif_xml.py
    ## Changement du fichier image du profil. Exemple image en gris ou noir et blanc pour profil non sélectionné et image en couleur pour profil sélectionné.
    time.sleep(2)  # Attendre un peu pour s'assurer que le jeu est bien terminé avant de modifier le gamelist.xml
    apply_RA_settings(profile_name)
    update_gamelist_xml(profile_name)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erreur lors de l'exécution du script: {e}")