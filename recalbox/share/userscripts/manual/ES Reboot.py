# le script ES Reboot.sh avec la commande "es restart" freeze après le reboot sur la page de chargement de EmulationStation. Ce script permet de contourner ce problème en rebootant le système après un délai de 5 secondes.

import subprocess

subprocess.run(["es", "restart"])