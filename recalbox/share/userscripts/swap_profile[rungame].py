#!/usr/bin/env python3
"""
Script de swap de profil pour Recalbox
Détecte quand une ROM du système "profiles" est lancée et met à jour le profil courant.
Événement : rungame
"""

import os
import sys
import json
import subprocess
import signal
import time
import xml.etree.ElementTree as ET
from shutil import copy2
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from others.recalbox_logging import get_logger

LOGGER = get_logger("recalbox_profiles")

# Fichier généré par EmulationStation indiquant l'état (lancement/fin de jeu)
STATE_FILE = "/tmp/es_state.inf"

# Fichier du profil courant
CURRENT_PROFILE_FILE = "/recalbox/share/profiles/current_profile.json"

# Dossier des profils disponibles
PROFILES_DIR = "/recalbox/share/profiles"

# Fichier gamelist.xml pour les profils
GL_PATH = "/recalbox/share/roms/profiles/gamelist.xml"
BACKUP_PATH = GL_PATH + ".bak"
REGION_SELECTED = "fr"
REGION_OTHER = "eu"

# Fichier de configuration de Recalbox
RECALBOX_CONF = "/recalbox/share/system/recalbox.conf"


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
        LOGGER.error("Erreur lors de la mise à jour du profil: %s", e)
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
        LOGGER.debug("Signal SIGINT envoyé au processus %s", pid)
    except ProcessLookupError:
        LOGGER.debug("Le processus RetroArch n'existe plus")
    except PermissionError:
        LOGGER.warning("Permission refusée pour envoyer le signal")


def kill_game():
    """
    Termine le jeu en cours (puisque c'est juste un sélecteur de profil).
    """
    pid = find_retroarch_pid()

    if pid is None:
        LOGGER.debug("Aucun jeu RetroArch en cours n'a été trouvé")
    else:
        LOGGER.debug("Jeu en cours trouvé avec PID : %s", pid)
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
        LOGGER.error("[update_gamelist_region_only] gamelist introuvable: %s", GL_PATH)
        return False

    try:
        tree = ET.parse(GL_PATH)
        root = tree.getroot()
    except ET.ParseError as e:
        LOGGER.error("[update_gamelist_region_only] erreur parse XML: %s", e)
        return False
    except Exception as e:
        LOGGER.error("[update_gamelist_region_only] erreur lecture: %s", e)
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
        LOGGER.debug("[update_gamelist_region_only] aucune modification nécessaire")
        return True

    # backup et écriture atomique
    try:
        copy2(GL_PATH, BACKUP_PATH)
    except Exception as e:
        LOGGER.error(
            "[update_gamelist_region_only] impossible de créer la sauvegarde: %s", e
        )

    try:
        dirpath = os.path.dirname(GL_PATH)
        fd, tmp_path = tempfile.mkstemp(dir=dirpath, prefix="gamelist.", suffix=".xml")
        os.close(fd)
        tree.write(tmp_path, encoding="utf-8", xml_declaration=True)
        os.replace(tmp_path, GL_PATH)
        LOGGER.debug(
            "[update_gamelist_region_only] gamelist mis à jour pour profil '%s'",
            profile_name,
        )
        return True
    except Exception as e:
        LOGGER.error("[update_gamelist_region_only] erreur écriture: %s", e)
        # tentative de restauration depuis backup
        try:
            if os.path.exists(BACKUP_PATH):
                copy2(BACKUP_PATH, GL_PATH)
        except Exception:
            pass
        return False


def load_profile_config(profile_name):
    """
    Charge la configuration générique du profil.
    """
    config_path = os.path.join(PROFILES_DIR, profile_name, "profile_config.json")

    with open(config_path) as f:
        return json.load(f)


def update_recalbox_conf(recalbox_conf, mapping):
    """
    Met à jour recalbox.conf avec les valeurs RetroAchievements du profil.
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
    profile_config = load_profile_config(profile_name)
    mapping = profile_config.get("retroachievements", {})
    update_recalbox_conf(RECALBOX_CONF, mapping)
    LOGGER.info(
        "RetroAchievements mis à jour dans recalbox.conf pour le profil : %s",
        profile_name,
    )


def apply_favorites_settings(profile_name):
    """
    Si les favoris sont activés dans le profil, lance recalbox_favorites.py
    pour unmark tous les favoris puis applique le fichier favorites.json du profil.
    """
    try:
        profile_config = load_profile_config(profile_name)
        favorites_config = profile_config.get("favorites", {})

        if not favorites_config.get("enabled"):
            LOGGER.debug("Favoris désactivés pour le profil '%s'", profile_name)
            return

        profile_path = os.path.join(PROFILES_DIR, profile_name)
        favorites_json = os.path.join(profile_path, "favorites.json")

        if not os.path.exists(favorites_json):
            LOGGER.warning(
                "Fichier favorites.json non trouvé pour le profil '%s'", profile_name
            )
            return

        # Répertoire ROMS de Recalbox
        roms_path = "/recalbox/share/roms"

        # Script recalbox_favorites.py
        script_path = "/recalbox/share/userscripts/others/recalbox_favorites.py"

        if not os.path.exists(script_path):
            LOGGER.error("Script recalbox_favorites.py non trouvé: %s", script_path)
            return

        # Étape 1: unmark tous les favoris
        LOGGER.info("Retrait de tous les favoris...")
        unmark_cmd = [
            "python3",
            script_path,
            "--log",
            "/recalbox/share/system/logs/recalbox_profiles.log",
            roms_path,
            "unmark",
        ]
        result = subprocess.run(unmark_cmd, capture_output=True, timeout=300)
        if result.returncode != 0:
            LOGGER.error("Erreur lors du unmark: %s", result.stderr.decode())
            return

        LOGGER.info("Favoris retirés avec succès")

        # Étape 2: appliquer les favoris du profil
        LOGGER.info("Application des favoris pour le profil '%s'...", profile_name)
        apply_cmd = [
            "python3",
            script_path,
            "--log",
            "/recalbox/share/system/logs/recalbox_profiles.log",
            roms_path,
            "apply",
            favorites_json,
        ]
        result = subprocess.run(apply_cmd, capture_output=True, timeout=300)
        if result.returncode != 0:
            LOGGER.error(
                "Erreur lors de l'application des favoris: %s", result.stderr.decode()
            )
            return

        LOGGER.info("Favoris appliqués avec succès pour le profil '%s'", profile_name)

    except Exception as e:
        LOGGER.error("Erreur lors de la gestion des favoris: %s", e)

    # Redémarrer EmulationStation
    try:
        subprocess.run(["es", "restart"], timeout=30)
        LOGGER.info("EmulationStation redémarré avec succès")
    except Exception as e:
        LOGGER.error("Erreur lors du redémarrage d'EmulationStation: %s", e)


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
        LOGGER.error("Profil '%s' non trouvé dans %s", profile_name, PROFILES_DIR)
        return

    # Mettre à jour le profil courant
    if update_current_profile(profile_name):
        LOGGER.info("Profil changé en: %s", profile_name)

    # Terminer le jeu (qui n'est qu'un sélecteur)
    time.sleep(
        5
    )  # Attendre un peu pour s'assurer que le jeu est bien lancé avant de le tuer
    kill_game()

    # Mettre à jour le fichier gamelist.xml pour refléter le changement de profil (optionnel)
    ## Changement de la region dans le fichier gamelist.xml ne fonctionne pas. Exemple region fr -> profil sélectionné et eu -> profil non sélectionné. CF archive_script/modif_xml.py
    ## Changement du fichier image du profil. Exemple image en gris ou noir et blanc pour profil non sélectionné et image en couleur pour profil sélectionné.
    time.sleep(
        2
    )  # Attendre un peu pour s'assurer que le jeu est bien terminé avant de modifier le gamelist.xml
    apply_RA_settings(profile_name)
    update_gamelist_xml(profile_name)
    time.sleep(
        5
    )  # Attendre un peu pour s'assurer que le gamelist.xml est bien mis à jour avant d'appliquer les favoris
    apply_favorites_settings(profile_name)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        LOGGER.exception("Erreur lors de l'exécution du script: %s", e)
