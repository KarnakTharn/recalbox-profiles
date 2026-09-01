#!/usr/bin/env python3
"""Enregistre le lancement d'un jeu dans les statistiques du profil actif.

Événement Recalbox : rungame
"""

import json
import os
import tempfile
import time
from datetime import datetime

STATE_FILE = "/tmp/es_state.inf"
CURRENT_PROFILE_FILE = "/recalbox/share/profiles/current_profile.json"
PROFILES_DIR = "/recalbox/share/profiles"
STATS_FILE_NAME = "game_time.json"


def read_state_file():
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


def get_game_name(game_path):
    if not game_path:
        return None
    return os.path.splitext(os.path.basename(game_path))[0]


def main():
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
        print("Aucun profil courant défini")
        return

    active_game = current_profile.get("active_game", {})
    # Évite de compter deux fois le même lancement si Recalbox renvoie rungame.
    if (active_game.get("system") == system_id and
            active_game.get("game_path") == game_path):
        print(f"Session déjà démarrée pour {game_name}")
        return

    now = time.time()
    lastplayed = datetime.now().strftime("%Y%m%dT%H%M%S")
    stats_path = os.path.join(PROFILES_DIR, profile_name, STATS_FILE_NAME)
    stats = read_json(stats_path, {})
    game_stats = stats.setdefault(system_id, {}).setdefault(game_name, {
        "timeplayed": 0,
        "playcount": 0,
        "lastplayed": lastplayed,
    })
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
        print(f"Statistiques démarrées pour {game_name} ({profile_name})")


if __name__ == "__main__":
    main()
