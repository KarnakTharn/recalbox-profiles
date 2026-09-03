#!/usr/bin/env python3
"""Exporte manuellement les favoris du profil Recalbox actuellement sélectionné.

Ce script correspond à l'étape d'export manuel décrite dans ``2.3.0.md``.
Il vérifie que le profil courant existe et que les favoris y sont activés, puis
enregistre les favoris présents dans les gamelists dans ``favorites.json`` du
profil. Il ne modifie pas les favoris d'EmulationStation.
"""

import json
import os
import sys
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from others.recalbox_logging import get_logger

# Fichier qui contient le nom du profil actuellement sélectionné.
CURRENT_PROFILE_FILE = "/recalbox/share/profiles/current_profile.json"

# Répertoire racine des profils et des fichiers exportés.
PROFILES_DIR = "/recalbox/share/profiles"
PROFILE_CONFIG_FILE_NAME = "profile_config.json"
FAVORITES_SCRIPT = "/recalbox/share/userscripts/others/recalbox_favorites.py"
ROMS_DIR = "/recalbox/share/roms"

LOGGER = get_logger("recalbox_profiles_manual")


def profile_exists(profile_name):
    """Retourne ``True`` si *profile_name* désigne un profil local valide."""
    if not isinstance(profile_name, str) or not profile_name:
        return False
    if profile_name != os.path.basename(profile_name):
        return False

    profile_path = os.path.join(PROFILES_DIR, profile_name)
    return os.path.isdir(profile_path)


def load_favorites_config(profile_name):
    """Charge la section ``favorites`` de la configuration du profil.

    Une configuration absente ou invalide désactive l'export par sécurité.
    """
    config_path = os.path.join(PROFILES_DIR, profile_name, PROFILE_CONFIG_FILE_NAME)

    try:
        with open(config_path, encoding="utf-8") as config_file:
            data = json.load(config_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as error:
        LOGGER.error(
            "[load_favorites_config] Lecture impossible de %s: %s", config_path, error
        )
        return {}

    if not isinstance(data, dict):
        LOGGER.error(
            "[load_favorites_config] Configuration invalide dans %s.", config_path
        )
        return {}

    favorites_config = data.get("favorites", {})
    return favorites_config if isinstance(favorites_config, dict) else {}


def main():
    """Exécute l'export si les favoris sont activés pour le profil courant."""
    # Lire le profil sélectionné par le sélecteur de profils.
    try:
        with open(CURRENT_PROFILE_FILE, encoding="utf-8") as current_profile_file:
            current_profile_data = json.load(current_profile_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as error:
        LOGGER.error("Lecture impossible de %s: %s", CURRENT_PROFILE_FILE, error)
        return

    if not isinstance(current_profile_data, dict):
        LOGGER.error("Configuration invalide dans %s.", CURRENT_PROFILE_FILE)
        return

    current_profile_name = current_profile_data.get("profile")

    if not profile_exists(current_profile_name):
        LOGGER.error(
            "Profil courant invalide ou introuvable : %s", current_profile_name
        )
        return

    favorites_config = load_favorites_config(current_profile_name)
    if favorites_config.get("enabled") not in (1, True):
        LOGGER.info(
            "Export ignoré : favoris désactivés pour le profil %s.",
            current_profile_name,
        )
        return

    output_file = os.path.join(PROFILES_DIR, current_profile_name, "favorites.json")
    LOGGER.info(
        "Export des favoris du profil %s vers %s.", current_profile_name, output_file
    )
    subprocess.run(
        [
            "python3",
            FAVORITES_SCRIPT,
            "--log",
            "/recalbox/share/system/logs/recalbox_profiles_manual.log",
            ROMS_DIR,
            "export",
            output_file,
        ],
        check=True,
    )


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as error:
        LOGGER.exception("Erreur lors de l'export des favoris : %s", error)
