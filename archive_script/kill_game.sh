#!/bin/bash
# Script pour quitter un jeu en cours sur EmulationStation via SSH

# Chercher le processus RetroArch
GAME_PROCESS=$(pgrep retroarch)

if [ -z "$GAME_PROCESS" ]; then
    echo "Aucun jeu RetroArch en cours n'a été trouvé."
else
    echo "Jeu en cours trouvé avec PID: $GAME_PROCESS"
    # Envoyer le signal de fermeture propre à RetroArch
    kill -s INT $GAME_PROCESS
    echo "Signal de fermeture envoyé."
fi