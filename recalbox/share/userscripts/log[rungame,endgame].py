#!/usr/bin/env python3
import os
from datetime import datetime

# Fichier généré par EmulationStation indiquant l'état (lancement/fin de jeu)
STATE_FILE = "/tmp/es_state.inf"

# Fichier log où seront enregistrées les infos
LOG_FILE = "/recalbox/share/profiles/es_state.log"


def read_state_file():
    """
    Lit le fichier es_state.inf et retourne un dictionnaire clé/valeur.
    Exemple de contenu :
        Action=StartGame
        SystemId=snes
        Game=Super Mario World
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


def write_log(info):
    """
    Écrit les informations dans le fichier log avec la date et l'heure.
    Chaque entrée est séparée par une ligne '---'.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a") as log:
        log.write(f"[{timestamp}]\n")
        for key, value in info.items():
            log.write(f"{key}: {value}\n")
        log.write("---\n")  # ligne de séparation


def main():
    info = read_state_file()

    # Si aucune info, on ne log rien
    if not info:
        return

    write_log(info)


if __name__ == "__main__":
    main()
