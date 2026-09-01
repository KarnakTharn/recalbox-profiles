"""Configuration commune des journaux des scripts Recalbox Profiles."""

import logging
import sys
from pathlib import Path

LOG_DIR = Path("/recalbox/share/system/logs")
LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(log_name):
    """Retourne le logger dédié à *log_name* et crée son fichier si nécessaire."""
    logger = logging.getLogger(f"recalbox_profiles.{log_name}")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            LOG_DIR / f"{log_name}.log", encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as error:
        fallback_handler = logging.StreamHandler(sys.stdout)
        fallback_handler.setLevel(logging.ERROR)
        fallback_handler.setFormatter(formatter)
        logger.addHandler(fallback_handler)
        logger.error("Impossible d'initialiser le fichier de log : %s", error)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger
