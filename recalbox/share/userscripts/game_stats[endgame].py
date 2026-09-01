#!/usr/bin/env python3
"""Finalise le temps de jeu de la session active du profil courant.

Événement Recalbox : endgame
"""

import json
import os
import tempfile
import time
from datetime import datetime

CURRENT_PROFILE_FILE = "/recalbox/share/profiles/current_profile.json"
PROFILES_DIR = "/recalbox/share/profiles"
STATS_FILE_NAME = "game_time.json"


def read_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as json_file:
            return json.load(json_file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Erreur de lecture de {path}: {error}")
        return default


def write_json_atomic(path, data):
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
        print(f"Erreur d'écriture de {path}: {error}")
        try:
            os.unlink(temporary_path)
        except OSError:
            pass
        return False


def main():
    current_profile = read_json(CURRENT_PROFILE_FILE, {})
    profile_name = current_profile.get("profile")
    active_game = current_profile.get("active_game")

    if not profile_name or not isinstance(active_game, dict):
        return

    system_id = active_game.get("system")
    game_name = active_game.get("game")
    started_at = active_game.get("started_at_timestamp")
    if not system_id or not game_name or not isinstance(started_at, (int, float)):
        print("Session de jeu incomplète : statistiques non mises à jour")
        return

    elapsed_seconds = max(0, int(time.time() - started_at))
    lastplayed = datetime.now().strftime("%Y%m%dT%H%M%S")
    stats_path = os.path.join(PROFILES_DIR, profile_name, STATS_FILE_NAME)
    stats = read_json(stats_path, {})
    game_stats = stats.setdefault(system_id, {}).setdefault(game_name, {
        "timeplayed": 0,
        "playcount": 0,
        "lastplayed": lastplayed,
    })
    game_stats["timeplayed"] = int(game_stats.get("timeplayed", 0)) + elapsed_seconds
    game_stats.setdefault("playcount", 0)
    game_stats["lastplayed"] = lastplayed

    if not write_json_atomic(stats_path, stats):
        return

    # Le retrait après l'écriture des statistiques rend endgame idempotent.
    current_profile.pop("active_game", None)
    if write_json_atomic(CURRENT_PROFILE_FILE, current_profile):
        print(f"Temps ajouté pour {game_name}: {elapsed_seconds} seconde(s)")


if __name__ == "__main__":
    main()
