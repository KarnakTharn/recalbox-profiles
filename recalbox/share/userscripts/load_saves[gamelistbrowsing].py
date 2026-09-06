"""Restaure les sauvegardes du profil actif pour l'aperçu des save states.

Événement Recalbox : gamelistbrowsing.
"""

import os
import sys
import json
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from others.recalbox_logging import get_logger

# Fichier généré par EmulationStation contenant les infos du jeu en cours
STATE_FILE = "/tmp/es_state.inf"

# Fichier indiquant quel profil est actuellement sélectionné
CURRENT_PROFILE_FILE = "/recalbox/share/profiles/current_profile.json"

# Dossier global où Recalbox stocke les saves
SHARES_SAVES_DIR = "/recalbox/share/saves"

# Dossier contenant les profils et leurs saves
PROFILES_DIR = "/recalbox/share/profiles"

LOGGER = get_logger("recalbox_profiles")


def read_state_file():
    """
    Lit /tmp/es_state.inf et retourne un dictionnaire contenant :
    - SystemId
    - GamePath
    - etc.
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
    Lit le fichier JSON du profil courant.
    Retourne le nom du profil (ex : "Guest", "Player1").
    """
    if not os.path.exists(CURRENT_PROFILE_FILE):
        return None

    try:
        with open(CURRENT_PROFILE_FILE, "r") as f:
            data = json.load(f)
            return data.get("profile", None)
    except Exception as e:
        LOGGER.error("Erreur lors de la lecture du profil courant: %s", e)
        return None


def get_game_name_from_path(game_path):
    """
    Extrait le nom du jeu depuis le chemin de la ROM.
    Exemple :
    /recalbox/share/roms/gba/Breath of Fire.zip → Breath of Fire
    """
    if not game_path:
        return None
    filename = os.path.basename(game_path)
    return os.path.splitext(filename)[0]


def find_save_files(profile_name, system_id, game_name):
    """
    Cherche les saves du profil pour ce jeu :
    /recalbox/share/profiles/<profil>/saves/<system>/<jeu>.*

    Retourne une liste de fichiers trouvés.
    """
    save_files = []
    profile_game_dir = os.path.join(PROFILES_DIR, profile_name, "saves", system_id)

    if not os.path.isdir(profile_game_dir):
        return save_files

    # On récupère tous les fichiers qui commencent par "<jeu>."
    for filename in os.listdir(profile_game_dir):
        if filename.startswith(game_name + "."):
            file_path = os.path.join(profile_game_dir, filename)
            if os.path.isfile(file_path):
                save_files.append(file_path)

    return save_files


def files_are_different(src, dst):
    """
    Compare deux fichiers :
    - Si dst n'existe pas → True (différent)
    - Si tailles différentes → True
    - Sinon comparaison binaire → True si contenu différent
    """
    if not os.path.exists(dst):
        return True

    if os.path.getsize(src) != os.path.getsize(dst):
        return True

    with open(src, "rb") as f1, open(dst, "rb") as f2:
        return f1.read() != f2.read()


def restore_save_file(profile_save_path, system_id):
    """
    Copie une save du profil vers /share/saves/<system>/,
    mais uniquement si elle est différente.
    """
    target_dir = os.path.join(SHARES_SAVES_DIR, system_id)
    os.makedirs(target_dir, exist_ok=True)

    filename = os.path.basename(profile_save_path)
    target_path = os.path.join(target_dir, filename)

    try:
        # Copie uniquement si le fichier diffère
        if files_are_different(profile_save_path, target_path):
            shutil.copy2(profile_save_path, target_path)
            LOGGER.debug("Save copiée (différente) : %s", filename)
            return True
        else:
            LOGGER.debug("Save identique, pas de copie : %s", filename)
            return False

    except Exception as e:
        LOGGER.error("Erreur lors de la restauration de %s: %s", filename, e)
        return False


def cleanup_extra_saves(system_id, game_name, profile_save_files):
    """
    Supprime les saves dans /share/saves/<system>/ qui ne font pas partie
    de la liste des saves du profil actuel.
    """
    target_dir = os.path.join(SHARES_SAVES_DIR, system_id)

    if not os.path.isdir(target_dir):
        return

    # Noms de fichiers attendus pour le profil actuel
    expected_filenames = {os.path.basename(f) for f in profile_save_files}

    for filename in os.listdir(target_dir):
        if filename.startswith(game_name + ".") and filename not in expected_filenames:
            file_path = os.path.join(target_dir, filename)
            try:
                os.remove(file_path)
                LOGGER.debug("Save résiduelle supprimée : %s", filename)
            except Exception as e:
                LOGGER.error("Erreur lors de la suppression de %s: %s", filename, e)


def main():
    """
    Fonction principale :
    1. Lit l'état du jeu
    2. Lit le profil courant
    3. Détermine le nom du jeu
    4. Synchronise les saves :
       - copie si différentes
       - supprime si aucune save dans le profil
    5. Log l'événement
    """
    info = read_state_file()
    system_id = info.get("SystemId", "").lower()

    # On ignore le système "profiles"
    if system_id == "profiles":
        return

    profile_name = read_current_profile()
    if not profile_name:
        LOGGER.warning("Aucun profil courant défini")
        return

    game_path = info.get("GamePath", "")
    game_name = get_game_name_from_path(game_path)
    if not game_name:
        return

    # Récupère les saves du profil
    save_files = find_save_files(profile_name, system_id, game_name)

    # Supprime les saves qui n'appartiennent pas au profil actuel
    cleanup_extra_saves(system_id, game_name, save_files)

    if save_files:
        # Copie des saves du profil vers /share/saves
        LOGGER.info(
            "Restauration des saves pour %s (%s) depuis profil %s",
            game_name,
            system_id,
            profile_name,
        )
        for save_file in save_files:
            restore_save_file(save_file, system_id)
    else:
        LOGGER.info("Aucune save dans le profil pour %s", game_name)


if __name__ == "__main__":
    main()
