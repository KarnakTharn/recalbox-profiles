#!/usr/bin/env python3
"""Finalise le temps de jeu de la session active du profil courant.

Événement Recalbox : endgame
"""

import json
import os
import sys
import tempfile
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from others.recalbox_logging import get_logger

CURRENT_PROFILE_FILE = "/recalbox/share/profiles/current_profile.json"
PROFILES_DIR = "/recalbox/share/profiles"
STATS_FILE_NAME = "game_time.json"
PROFILE_CONFIG_FILE_NAME = "profile_config.json"
LOGGER = get_logger("recalbox_profiles")


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


def stats_enabled(profile_name):
    """Indique si le suivi est activé dans la configuration du profil."""
    config_path = os.path.join(PROFILES_DIR, profile_name, PROFILE_CONFIG_FILE_NAME)
    config = read_json(config_path, {})
    return config.get("stats", {}).get("enabled", 1) == 1


def main():
    """Ajoute la durée de la session active puis la retire du profil courant."""
    current_profile = read_json(CURRENT_PROFILE_FILE, {})
    profile_name = current_profile.get("profile")
    active_game = current_profile.get("active_game")

    if not profile_name or not isinstance(active_game, dict):
        return

    # Une désactivation pendant une session annule son enregistrement et évite
    # qu'une ancienne session soit reprise au lancement suivant.
    if not stats_enabled(profile_name):
        current_profile.pop("active_game", None)
        write_json_atomic(CURRENT_PROFILE_FILE, current_profile)
        return

    system_id = active_game.get("system")
    game_name = active_game.get("game")
    started_at = active_game.get("started_at_timestamp")
    if not system_id or not game_name or not isinstance(started_at, (int, float)):
        LOGGER.warning("Session de jeu incomplète : statistiques non mises à jour")
        return

    elapsed_seconds = max(0, int(time.time() - started_at))
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
    game_stats["timeplayed"] = int(game_stats.get("timeplayed", 0)) + elapsed_seconds
    game_stats.setdefault("playcount", 0)
    game_stats["lastplayed"] = lastplayed

    if not write_json_atomic(stats_path, stats):
        return

    # Le retrait après l'écriture des statistiques rend endgame idempotent.
    current_profile.pop("active_game", None)
    if write_json_atomic(CURRENT_PROFILE_FILE, current_profile):
        LOGGER.info("Temps ajouté pour %s : %s seconde(s)", game_name, elapsed_seconds)


if __name__ == "__main__":
    main()
