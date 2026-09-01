#!/usr/bin/env python3
"""Enregistre le lancement d'un jeu dans les statistiques du profil actif.

Événement Recalbox : rungame
"""

import json
import os
import sys
import tempfile
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from others.recalbox_logging import get_logger

LOGGER = get_logger("recalbox_profiles")


STATE_FILE = "/tmp/es_state.inf"
CURRENT_PROFILE_FILE = "/recalbox/share/profiles/current_profile.json"
PROFILES_DIR = "/recalbox/share/profiles"
STATS_FILE_NAME = "game_time.json"
PROFILE_CONFIG_FILE_NAME = "profile_config.json"


def read_state_file():
    """Retourne les clés/valeurs fournies par EmulationStation pour le jeu lancé."""
    info = {}
    if not os.path.exists(STATE_FILE):
        return info

    with open(STATE_FILE, "r") as state_file:
        for line in state_file:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                info[key] = value
    return info


def read_json(path, default):
    """Lit un JSON ou renvoie ``default`` si le fichier est absent ou invalide."""
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as json_file:
            return json.load(json_file)
    except (OSError, json.JSONDecodeError) as error:
        LOGGER.error("Erreur de lecture de %s : %s", path, error)
        return default


def write_json_atomic(path, data):
    """Écrit un JSON via un fichier temporaire pour éviter un fichier partiel."""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    file_descriptor, temporary_path = tempfile.mkstemp(dir=directory, prefix=".tmp_")
    try:
        with os.fdopen(file_descriptor, "w") as json_file:
            json.dump(data, json_file, indent=2)
            json_file.write("\n")
        os.replace(temporary_path, path)
        return True
    except OSError as error:
        LOGGER.error("Erreur d'écriture de %s : %s", path, error)
        try:
            os.unlink(temporary_path)
        except OSError:
            pass
        return False


def get_game_name(game_path):
    """Extrait le nom de jeu du chemin de ROM, sans son extension."""
    if not game_path:
        return None
    return os.path.splitext(os.path.basename(game_path))[0]


def stats_enabled(profile_name):
    """Indique si le suivi est activé dans la configuration du profil."""
    config_path = os.path.join(PROFILES_DIR, profile_name, PROFILE_CONFIG_FILE_NAME)
    config = read_json(config_path, {})
    return config.get("stats", {}).get("enabled", 1) == 1


def main():
    """Crée la session de jeu et incrémente son compteur de lancements."""
    state = read_state_file()
    system_id = state.get("SystemId", "").lower()
    game_path = state.get("GamePath", "")
    game_name = get_game_name(game_path)

    # Le système profiles est uniquement un sélecteur de profil.
    if system_id == "profiles" or not system_id or not game_name:
        return

    current_profile = read_json(CURRENT_PROFILE_FILE, {})
    profile_name = current_profile.get("profile")
    if not profile_name:
        LOGGER.warning("Aucun profil courant défini")
        return

    if not stats_enabled(profile_name):
        return

    active_game = current_profile.get("active_game", {})
    # Évite de compter deux fois le même lancement si Recalbox renvoie rungame.
    if (
        active_game.get("system") == system_id
        and active_game.get("game_path") == game_path
    ):
        LOGGER.debug("Session déjà démarrée pour %s", game_name)
        return

    now = time.time()
    lastplayed = datetime.now().strftime("%Y%m%dT%H%M%S")
    stats_path = os.path.join(PROFILES_DIR, profile_name, STATS_FILE_NAME)
    stats = read_json(stats_path, {})
    game_stats = stats.setdefault(system_id, {}).setdefault(
        game_name,
        {
            "timeplayed": 0,
            "playcount": 0,
            "lastplayed": lastplayed,
        },
    )
    game_stats["playcount"] = int(game_stats.get("playcount", 0)) + 1
    game_stats.setdefault("timeplayed", 0)
    game_stats["lastplayed"] = lastplayed

    if not write_json_atomic(stats_path, stats):
        return

    current_profile["active_game"] = {
        "system": system_id,
        "game": game_name,
        "game_path": game_path,
        "started_at": lastplayed,
        "started_at_timestamp": now,
    }
    if write_json_atomic(CURRENT_PROFILE_FILE, current_profile):
        LOGGER.info("Statistiques démarrées pour %s (%s)", game_name, profile_name)


if __name__ == "__main__":
    main()
