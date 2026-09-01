#!/usr/bin/env python3
"""
recalbox_favorites.py
Gestion des favoris EmulationStation / Recalbox via les fichiers gamelist.xml

Fonctionnalités :
  - Export des favoris vers un fichier JSON ou texte
  - Application d'un fichier JSON de favoris sur une arborescence de ROMs
  - Ajout de favoris depuis un fichier texte (liste de noms de jeux)
  - Comparaison de noms avec seuil flou (difflib.SequenceMatcher)
  - Logging fichier + console verbose
  - Mode dry-run : simule toutes les opérations sans écrire sur disque

Structure gamelist.xml (EmulationStation) :
  <gameList>
    <game>
      <path>./rom_file.zip</path>
      <name>Nom du jeu</name>
      <favorite>1</favorite>   ← balise ciblée (v9)
      ...
    </game>
  </gameList>

Le champ <favorite> n'existe pas toujours : on le crée si absent.

Compatibilité Recalbox v10 :
  À partir de la v10, Recalbox stocke les données utilisateur (favoris,
  temps de jeu, etc.) dans un fichier gamelist-userdata.ini placé dans le
  même répertoire que gamelist.xml. Le fichier gamelist.xml n'est pas modifié.

  Format gamelist-userdata.ini :
    <chemin_rom>:<champ1>=<valeur1>[,<champ2>=<valeur2>...]

  Exemples :
    galaga.zip:favorite=true
    rtype.zip:timeplayed=138,lastplayed=20260608T191434,playcount=1,favorite=true
    mame0274/xybots.zip:favorite=true

  Le chemin ROM est le champ <path> du gamelist.xml sans le préfixe './'.
  Par défaut, ce script lit et écrit uniquement gamelist-userdata.ini ;
  gamelist.xml est utilisé en lecture seule pour identifier les jeux.
  Utiliser --v9 pour gérer les favoris au format Recalbox v9 (gamelist.xml).
"""

import argparse
import json
import logging
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET

# Regex qui détecte un '&' non suivi d'une référence d'entité XML valide :
#   &name;   (entité nommée : &amp; &lt; &gt; …)
#   &#nnn;   (entité décimale)
#   &#xHH;   (entité hexadécimale)
_BARE_AMP_RE = re.compile(r"&(?!(?:[a-zA-Z][a-zA-Z0-9]*|#[0-9]+|#x[0-9a-fA-F]+);)")

# Ordre des champs dans gamelist-userdata.ini (identique au format Recalbox)
_INI_FIELD_ORDER = ("timeplayed", "lastplayed", "playcount", "favorite")


# ---------------------------------------------------------------------------
# Dictionnaire de noms de systèmes
# ---------------------------------------------------------------------------
#
# Structure : nom_court (= nom du dossier Recalbox) → nom long affiché.
#
# Pour l'export texte  : system_key → SYSTEM_DISPLAY_NAMES[system_key]
#                        (fallback : system_key tel quel si absent)
# Pour l'import texte  : on consulte SYSTEM_ALIASES, qui mappe tout alias
#                        connu (en minuscules) → system_key.
#                        SYSTEM_ALIASES est généré automatiquement depuis
#                        SYSTEM_DISPLAY_NAMES (nom long inclus) puis complété
#                        par EXTRA_ALIASES pour les variantes orthographiques.
#
# Ajouter un système  : une entrée dans SYSTEM_DISPLAY_NAMES suffit.
# Ajouter un alias    : une entrée dans EXTRA_ALIASES (clé en minuscules).

SYSTEM_DISPLAY_NAMES: dict[str, str] = {
    # --- Nintendo ---
    "nes":           "Nintendo NES",
    "fds":           "Famicom Disk System",
    "snes":          "Super Nintendo",
    "n64":           "Nintendo 64",
    "gc":            "Nintendo GameCube",
    "wii":           "Nintendo Wii",
    "wiiu":          "Nintendo Wii U",
    "switch":        "Nintendo Switch",
    "gb":            "Game Boy",
    "gbc":           "Game Boy Color",
    "gba":           "Game Boy Advance",
    "nds":           "Nintendo DS",
    "3ds":           "Nintendo 3DS",
    "virtualboy":    "Virtual Boy",
    "pokemini":      "Pokemon Mini",
    # --- Sega ---
    "mastersystem":  "Sega Master System",
    "megadrive":     "Sega Mega Drive",
    "segacd":        "Sega CD",
    "sega32x":       "Sega 32X",
    "saturn":        "Sega Saturn",
    "dreamcast":     "Sega Dreamcast",
    "gamegear":      "Sega Game Gear",
    "sg1000":        "Sega SG-1000",
    # --- Sony ---
    "psx":           "PlayStation",
    "ps2":           "PlayStation 2",
    "ps3":           "PlayStation 3",
    "psp":           "PlayStation Portable",
    "psvita":        "PlayStation Vita",
    # --- Microsoft ---
    "xbox":          "Xbox",
    "xbox360":       "Xbox 360",
    # --- NEC ---
    "pcengine":      "PC Engine",
    "pcenginecd":    "PC Engine CD",
    "pc88":          "NEC PC-88",
    "pc98":          "NEC PC-98",
    # --- SNK ---
    "neogeo":        "Neo Geo",
    "neogeocd":      "Neo Geo CD",
    "ngp":           "Neo Geo Pocket",
    "ngpc":          "Neo Geo Pocket Color",
    # --- Atari ---
    "atari2600":     "Atari 2600",
    "atari5200":     "Atari 5200",
    "atari7800":     "Atari 7800",
    "atarist":       "Atari ST",
    "jaguar":        "Atari Jaguar",
    "jaguarcd":      "Atari Jaguar CD",
    "lynx":          "Atari Lynx",
    # --- Amstrad / Sinclair / Commodore ---
    "amstradcpc":    "Amstrad CPC",
    "zxspectrum":    "ZX Spectrum",
    "c64":           "Commodore 64",
    "c128":          "Commodore 128",
    "amiga":         "Amiga",
    "amigacd32":     "Amiga CD32",
    "vic20":         "Commodore VIC-20",
    # --- Arcade ---
    "mame":          "MAME",
    "fba":           "FinalBurn Alpha",
    "fbneo":         "FinalBurn Neo",
    "cave":          "Cave",
    "naomi":         "Sega NAOMI",
    "atomiswave":    "Atomiswave",
    # --- Ordinateurs ---
    "dos":           "DOS",
    "scummvm":       "ScummVM",
    "x68000":        "Sharp X68000",
    "msx":           "MSX",
    "msx2":          "MSX2",
    "x1":            "Sharp X1",
    "colecovision":  "ColecoVision",
    "intellivision": "Intellivision",
    "vectrex":       "Vectrex",
    "o2em":          "Magnavox Odyssey 2",
    "gw":            "Game & Watch",
    "supervision":   "Watara Supervision",
    "wonderswan":    "WonderSwan",
    "wonderswancolor": "WonderSwan Color",
    # --- Multi-systèmes / émulateurs génériques ---
    "ports":         "Ports",
    "imageviewer":   "Image Viewer",
    "kodi":          "Kodi",
}

# Aliases supplémentaires : variantes orthographiques, noms régionaux,
# abréviations courantes. Clés toujours en minuscules.
EXTRA_ALIASES: dict[str, str] = {
    "famicom":              "nes",
    "nintendo entertainment system": "nes",
    "super nes":            "snes",
    "super famicom":        "snes",
    "super nintendo":       "snes",
    "super nintendo entertainment system": "snes",
    "nintendo64":           "n64",
    "nintendo 64":          "n64",
    "genesis":              "megadrive",
    "sega genesis":         "megadrive",
    "sega mega drive":      "megadrive",
    "mega drive":           "megadrive",
    "sms":                  "mastersystem",
    "sega master system":   "mastersystem",
    "mark iii":             "mastersystem",
    "mega cd":              "segacd",
    "mega-cd":              "segacd",
    "sega saturn":          "saturn",
    "sega dreamcast":       "dreamcast",
    "sega game gear":       "gamegear",
    "playstation":          "psx",
    "ps1":                  "psx",
    "psone":                "psx",
    "playstation 1":        "psx",
    "playstation 2":        "ps2",
    "playstation portable": "psp",
    "turbografx":           "pcengine",
    "turbografx-16":        "pcengine",
    "tg16":                 "pcengine",
    "pc engine cd":         "pcenginecd",
    "turbo cd":             "pcenginecd",
    "neo-geo":              "neogeo",
    "neo geo aes":          "neogeo",
    "neo geo mvs":          "neogeo",
    "gameboy advance":      "gba",
    "game boy advance":     "gba",
    "gameboy color":        "gbc",
    "game boy color":       "gbc",
    "gameboy":              "gb",
    "game boy":             "gb",
    "nintendo ds":          "nds",
    "nintendo 3ds":         "3ds",
    "atari":                "atari2600",
    "commodore amiga":      "amiga",
    "spectrum":             "zxspectrum",
    "sinclair spectrum":    "zxspectrum",
    "cpc":                  "amstradcpc",
    "amstrad":              "amstradcpc",
    "commodore 64":         "c64",
    "commodore64":          "c64",
    "msx 2":                "msx2",
    "finalburn alpha":      "fba",
    "finalburn neo":        "fbneo",
    "fb neo":               "fbneo",
    "scumm":                "scummvm",
    "ms-dos":               "dos",
    "msdos":                "dos",
}

# Index global alias → clé courte, généré une fois au chargement du module.
_ALIAS_INDEX: dict[str, str] = {}
for _key, _long in SYSTEM_DISPLAY_NAMES.items():
    _ALIAS_INDEX[_key.lower()] = _key
    _ALIAS_INDEX[_long.lower()] = _key
for _alias, _key in EXTRA_ALIASES.items():
    _ALIAS_INDEX[_alias.lower()] = _key


def system_display_name(system_key: str) -> str:
    """Retourne le nom long d'un système, ou system_key si inconnu."""
    return SYSTEM_DISPLAY_NAMES.get(system_key, system_key)


def system_key_from_label(label: str) -> Optional[str]:
    """
    Résout un label (nom long, alias, ou clé courte) vers la clé courte.
    Retourne None si aucun alias ne correspond.
    """
    return _ALIAS_INDEX.get(label.strip().lower())


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(log_file: Path, verbose: bool) -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG if verbose else logging.WARNING)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


# ---------------------------------------------------------------------------
# Comparaison de noms
# ---------------------------------------------------------------------------

def normalize(name: str) -> str:
    """Retire les espaces en début/fin et met en minuscules."""
    return name.strip().lower()


def similarity(a: str, b: str) -> float:
    """Ratio de similarité entre deux chaînes (0.0 → 1.0)."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def matches(game_name: str, query: str, threshold: float) -> bool:
    """Retourne True si la similarité dépasse le seuil (0.0–1.0)."""
    return similarity(game_name, query) >= threshold


# ---------------------------------------------------------------------------
# Lecture / écriture gamelist.xml
# ---------------------------------------------------------------------------

def parse_gamelist(xml_path: Path) -> Optional[ET.ElementTree]:
    """
    Parse un fichier gamelist.xml et retourne l'ElementTree.

    Corrige les '&' littéraux non échappés avant parsing.
    Retourne None si le fichier est invalide ou absent.
    """
    if not xml_path.is_file():
        logging.warning("Fichier introuvable : %s", xml_path)
        return None
    try:
        raw = xml_path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        fixed = _BARE_AMP_RE.sub("&amp;", text)
        if fixed != text:
            logging.debug("'&' non échappé(s) corrigé(s) dans %s", xml_path)
        return ET.ElementTree(ET.fromstring(fixed))
    except ET.ParseError as exc:
        logging.error("XML invalide (%s) : %s", xml_path, exc)
        return None


def get_game_elements(tree: ET.ElementTree) -> list[ET.Element]:
    """Retourne la liste de tous les éléments <game> du gameList."""
    return tree.getroot().findall("game")


def get_field(game: ET.Element, tag: str) -> str:
    """Lit le texte d'un sous-élément ou retourne '' s'il est absent."""
    el = game.find(tag)
    return (el.text or "").strip() if el is not None else ""


def _is_favorite(game: ET.Element) -> bool:
    """Retourne True si le jeu est marqué favori (v9 : <favorite>1</favorite>)."""
    return get_field(game, "favorite") == "1"


def set_field(game: ET.Element, tag: str, value: str) -> None:
    """Écrit la valeur dans le sous-élément <tag>, le crée si absent."""
    el = game.find(tag)
    if el is None:
        el = ET.SubElement(game, tag)
    el.text = value


def write_gamelist(tree: ET.ElementTree, xml_path: Path, dry_run: bool = False) -> None:
    """
    Sérialise l'arbre XML vers le fichier (v9 uniquement).

    ET.indent (Python >= 3.9) ajoute une indentation lisible en place.
    short_empty_elements=False force <tag></tag> plutôt que <tag/>.
    En mode dry_run, aucun fichier n'est écrit.
    """
    ET.indent(tree, space="  ")
    if dry_run:
        logging.info("[DRY-RUN] gamelist.xml NON écrit : %s", xml_path)
        return
    tree.write(
        xml_path,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=False,
    )
    logging.debug("gamelist.xml mis à jour : %s", xml_path)


# ---------------------------------------------------------------------------
# Gestion du fichier gamelist-userdata.ini (Recalbox v10)
# ---------------------------------------------------------------------------

def _userdata_path(xml_path: Path) -> Path:
    """Retourne le chemin du gamelist-userdata.ini voisin du gamelist.xml."""
    return xml_path.parent / "gamelist-userdata.ini"


def _rom_key(path_field: str) -> str:
    """
    Dérive la clé INI depuis le champ <path> du gamelist.
    Supprime le préfixe './' : './mame0274/galaga.zip' → 'mame0274/galaga.zip'.
    """
    s = path_field.strip()
    if s.startswith("./"):
        s = s[2:]
    return s


def _read_userdata(ini_path: Path) -> dict[str, dict[str, str]]:
    """
    Parse un fichier gamelist-userdata.ini.

    Retourne un dict : rom_key → {champ: valeur}.
    Retourne {} si le fichier n'existe pas.

    Format :
        rom.zip:favorite=true
        subdir/rom.zip:timeplayed=190,lastplayed=20260608T193111,playcount=1,favorite=true
    """
    if not ini_path.is_file():
        return {}
    data: dict[str, dict[str, str]] = {}
    for line in ini_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        rom_key, _, fields_str = line.partition(":")
        fields: dict[str, str] = {}
        for field in fields_str.split(","):
            if "=" in field:
                k, _, v = field.partition("=")
                fields[k.strip()] = v.strip()
        if fields:
            data[rom_key.strip()] = fields
    return data


def _write_userdata(
    ini_path: Path,
    data: dict[str, dict[str, str]],
    dry_run: bool = False,
) -> None:
    """
    Écrit un fichier gamelist-userdata.ini.

    Les champs sont ordonnés : timeplayed, lastplayed, playcount, favorite,
    puis les champs inconnus par ordre alphabétique.
    Les entrées sans champ sont omises.
    En mode dry_run, aucun fichier n'est écrit.
    """
    lines: list[str] = []
    for rom_key in sorted(data.keys()):
        fields = data[rom_key]
        if not fields:
            continue
        ordered: list[str] = []
        for k in _INI_FIELD_ORDER:
            if k in fields:
                ordered.append(f"{k}={fields[k]}")
        for k in sorted(fields):
            if k not in _INI_FIELD_ORDER:
                ordered.append(f"{k}={fields[k]}")
        lines.append(f"{rom_key}:{','.join(ordered)}")
    content = "\n".join(lines) + "\n" if lines else ""

    if dry_run:
        logging.info("[DRY-RUN] gamelist-userdata.ini NON écrit : %s", ini_path)
        return
    ini_path.write_text(content, encoding="utf-8")
    logging.debug("gamelist-userdata.ini mis à jour : %s", ini_path)


# ---------------------------------------------------------------------------
# Collecte des gamelists
# ---------------------------------------------------------------------------

def find_gamelists(root: Path) -> list[Path]:
    """
    Parcourt récursivement root et retourne tous les gamelist.xml trouvés.
    Path.rglob utilise os.scandir : efficace, pas de chargement en mémoire.
    """
    return sorted(root.rglob("gamelist.xml"))


def _collect_gamelists(source: Path, force_v10: bool = False) -> list[Path]:
    """
    Retourne la liste des gamelist.xml à traiter selon que 'source' est
    un répertoire ou un fichier gamelist.xml directement.

    Toujours gamelist.xml : en v10, le gamelist.xml sert à identifier les
    jeux ; seul gamelist-userdata.ini est modifié.
    """
    if source.is_dir():
        gl = find_gamelists(source)
        logging.info("%d gamelist trouvé(s) sous %s", len(gl), source)
        return gl
    elif source.is_file() and source.name == "gamelist.xml":
        return [source]
    else:
        logging.error(
            "Source invalide (doit être un dossier ou un gamelist.xml) : %s", source
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Export des favoris
# ---------------------------------------------------------------------------

def _collect_favorites(source: Path, force_v10: bool = False) -> list[dict]:
    """
    Parcourt tous les gamelists sous *source* et retourne les jeux favoris.

    Mode v9 : lit <favorite>1</favorite> dans gamelist.xml.
    Mode v10 : lit favorite=true dans gamelist-userdata.ini ; gamelist.xml
               est utilisé uniquement pour retrouver le <name> du jeu.

    Chaque entrée : {"name", "path", "system", "gamelist"}.
    """
    gamelists = _collect_gamelists(source, force_v10)
    favorites: list[dict] = []

    for xml_path in gamelists:
        tree = parse_gamelist(xml_path)
        if tree is None:
            continue
        system = (
            xml_path.relative_to(source).parts[0]
            if source.is_dir()
            else xml_path.parent.name
        )
        if force_v10:
            userdata = _read_userdata(_userdata_path(xml_path))
            fav_keys = {
                k for k, v in userdata.items()
                if v.get("favorite", "").lower() == "true"
            }
            for game in get_game_elements(tree):
                path_field = get_field(game, "path")
                if _rom_key(path_field) in fav_keys:
                    entry = {
                        "name": get_field(game, "name"),
                        "path": path_field,
                        "system": system,
                        "gamelist": str(xml_path),
                    }
                    favorites.append(entry)
                    logging.debug("Favori v10 : [%s] %s", system, entry["name"])
        else:
            for game in get_game_elements(tree):
                if _is_favorite(game):
                    entry = {
                        "name": get_field(game, "name"),
                        "path": get_field(game, "path"),
                        "system": system,
                        "gamelist": str(xml_path),
                    }
                    favorites.append(entry)
                    logging.debug("Favori v9 : [%s] %s", system, entry["name"])

    return favorites


def export_favorites(source: Path, out_json: Path, dry_run: bool = False, force_v10: bool = False) -> None:
    """
    Exporte tous les jeux favoris dans un fichier JSON.

    Structure JSON :
    [{"name": "...", "path": "./rom.zip", "system": "snes", "gamelist": "/..."}]
    """
    favorites = _collect_favorites(source, force_v10)

    if dry_run:
        logging.info("[DRY-RUN] JSON NON écrit : %s (%d entrée(s))", out_json, len(favorites))
        print(f"[DRY-RUN] {len(favorites)} favori(s) trouvé(s) — fichier NON écrit : {out_json}")
        return

    out_json.write_text(
        json.dumps(favorites, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logging.info("%d favori(s) exporté(s) vers %s", len(favorites), out_json)
    print(f"✔  {len(favorites)} favori(s) exporté(s) → {out_json}")


def export_favorites_text(source: Path, out_txt: Path, dry_run: bool = False, force_v10: bool = False) -> None:
    """
    Exporte les favoris dans un fichier texte lisible, regroupés par système.

    Format :
        [Super Nintendo]
        Super Mario World

        [MAME]
        Galaga
    """
    favorites = _collect_favorites(source, force_v10)

    by_system: dict[str, list[str]] = {}
    for entry in favorites:
        by_system.setdefault(entry["system"], []).append(entry["name"])

    blocks: list[str] = []
    for system, names in by_system.items():
        header = f"[{system_display_name(system)}]"
        blocks.append("\n".join([header] + names))
    content = "\n\n".join(blocks) + "\n"

    total = sum(len(v) for v in by_system.values())

    if dry_run:
        logging.info(
            "[DRY-RUN] TXT NON écrit : %s (%d système(s), %d entrée(s))",
            out_txt, len(by_system), total,
        )
        print(f"[DRY-RUN] {total} favori(s) dans {len(by_system)} système(s) — fichier NON écrit : {out_txt}")
        print("\n--- Aperçu ---")
        print(content)
        return

    out_txt.write_text(content, encoding="utf-8")
    logging.info("%d favori(s) dans %d système(s) exporté(s) vers %s", total, len(by_system), out_txt)
    print(f"✔  {total} favori(s) / {len(by_system)} système(s) exporté(s) → {out_txt}")


# ---------------------------------------------------------------------------
# Application des favoris
# ---------------------------------------------------------------------------

def apply_favorites(
    source: Path,
    favorites_json: Path,
    threshold: float,
    dry_run: bool = False,
    force_v10: bool = False,
) -> None:
    """
    Pour chaque entrée du JSON, cherche le jeu correspondant dans les
    gamelists et active le favori.

    Mode v9 : écrit <favorite>1</favorite> dans gamelist.xml.
    Mode v10 : écrit favorite=true dans gamelist-userdata.ini ;
               gamelist.xml n'est jamais modifié.

    Algorithme :
      1. Pour chaque favori JSON, localiser le jeu (chemin exact ou nom flou).
      2. v9 : marquer dans l'arbre XML en mémoire, réécrire les XML dirty.
         v10 : collecter les rom_keys par fichier INI, lire/fusionner/écrire.
    """
    if not favorites_json.is_file():
        logging.error("Fichier JSON introuvable : %s", favorites_json)
        sys.exit(1)

    entries = json.loads(favorites_json.read_text(encoding="utf-8"))
    gamelists = _collect_gamelists(source, force_v10)

    trees: dict[Path, Optional[ET.ElementTree]] = {}
    dirty_xml: set[Path] = set()
    # v10 : ini_path → set de rom_keys à marquer
    dirty_ini: dict[Path, set[str]] = {}
    # v10 : cache des INI déjà lus (pour détection doublons sans double lecture)
    ini_cache: dict[Path, dict[str, dict[str, str]]] = {}

    found_count = 0
    already_count = 0
    not_found: list[tuple[str, str]] = []

    for entry in entries:
        name_query: str = entry.get("name", "")
        path_query: str = entry.get("path", "")
        gamelist_hint: Optional[Path] = None

        if entry.get("gamelist"):
            candidate = Path(entry["gamelist"])
            if candidate.is_file():
                gamelist_hint = candidate

        if gamelist_hint and source.is_dir():
            try:
                system_label = gamelist_hint.relative_to(source).parts[0]
            except ValueError:
                system_label = gamelist_hint.parent.name
        elif gamelist_hint:
            system_label = gamelist_hint.parent.name
        else:
            system_label = "tous systèmes"

        match_rom: bool = entry.get("match_rom", False)
        located = _locate_game(
            name_query=name_query,
            path_query=path_query,
            gamelist_hint=gamelist_hint,
            gamelists=gamelists,
            trees=trees,
            threshold=threshold,
            restrict_to_hint=entry.get("restrict", False),
            match_rom=match_rom,
        )

        if located is None:
            label_suffix = " (ROM)" if match_rom else ""
            msg = f"[NON TROUVÉ] [{system_label}] '{name_query}'{label_suffix}"
            logging.warning(msg)
            not_found.append((system_label, name_query + label_suffix))
            print(f"  ⚠  {msg}")
        else:
            xml_path, game_el = located
            if force_v10:
                path_field = get_field(game_el, "path")
                ini = _userdata_path(xml_path)
                rk = _rom_key(path_field)
                if ini not in ini_cache:
                    ini_cache[ini] = _read_userdata(ini)
                if ini_cache[ini].get(rk, {}).get("favorite", "").lower() == "true":
                    logging.debug("Déjà favori (v10) : [%s] %s", xml_path.parent.name, name_query)
                    already_count += 1
                    continue
                dirty_ini.setdefault(ini, set()).add(rk)
            else:
                if _is_favorite(game_el):
                    logging.debug("Déjà favori (v9) : [%s] %s", xml_path.parent.name, name_query)
                    already_count += 1
                    continue
                set_field(game_el, "favorite", "1")
                dirty_xml.add(xml_path)
            found_count += 1
            action = "[DRY-RUN] trouverait" if dry_run else "Favori appliqué"
            logging.debug("%s : [%s] %s", action, xml_path.parent.name, name_query)

    # Écriture v9 : réécriture des gamelist.xml modifiés
    for xml_path in dirty_xml:
        write_gamelist(trees[xml_path], xml_path, dry_run=dry_run)  # type: ignore[arg-type]

    # Écriture v10 : lecture + fusion + écriture des gamelist-userdata.ini
    for ini_path, rom_keys in dirty_ini.items():
        userdata = _read_userdata(ini_path)
        for rk in rom_keys:
            userdata.setdefault(rk, {})["favorite"] = "true"
        if dry_run:
            logging.info(
                "[DRY-RUN] gamelist-userdata.ini NON écrit : %s (%d entrée(s))",
                ini_path, len(rom_keys),
            )
            print(f"  [DRY-RUN] INI : {ini_path}  ({len(rom_keys)} favori(s))")
        else:
            _write_userdata(ini_path, userdata)
            print(f"  ✔  INI mis à jour : {ini_path}")

    dry_tag = "[DRY-RUN] " if dry_run else ""
    verb = "seraient appliqués" if dry_run else "appliqué(s)"
    logging.info("%s%d favori(s) %s, %d déjà présent(s), %d non trouvé(s)", dry_tag, found_count, verb, already_count, len(not_found))
    print(f"\n{'[DRY-RUN] ' if dry_run else '✔  '}{found_count} favori(s) {verb}, {already_count} déjà présent(s), {len(not_found)} non trouvé(s)")
    if not_found:
        print("Jeux non trouvés :")
        for sys_lbl, name in not_found:
            print(f"   • [{sys_lbl}] {name}")


def _locate_game(
    name_query: str,
    path_query: str,
    gamelist_hint: Optional[Path],
    gamelists: list[Path],
    trees: dict[Path, Optional[ET.ElementTree]],
    threshold: float,
    restrict_to_hint: bool = False,
    match_rom: bool = False,
) -> Optional[tuple[Path, ET.Element]]:
    """
    Cherche un jeu par son chemin exact (prioritaire) ou par son nom (flou).

    Retourne (xml_path, element) ou None.
    xml_path est toujours un gamelist.xml.

    Ordre de recherche (sans restrict_to_hint) :
      1. gamelist_hint + path/stem exact
      2. gamelist_hint + nom flou
      3. tous gamelists + path/stem exact
      4. tous gamelists + nom flou

    Avec restrict_to_hint=True : recherche limitée au seul gamelist_hint.
    Avec match_rom=True : correspondance exacte sur le stem du champ <path>.
    """
    if restrict_to_hint and gamelist_hint:
        search_order: list[Path] = [gamelist_hint]
    else:
        search_order = []
        if gamelist_hint:
            search_order.append(gamelist_hint)
        for p in gamelists:
            if p not in search_order:
                search_order.append(p)

    if match_rom:
        query_stem = name_query.strip().lower()
        for xml_path in search_order:
            _ensure_loaded(xml_path, trees)
            tree = trees.get(xml_path)
            if tree is None:
                continue
            for game in get_game_elements(tree):
                if Path(get_field(game, "path")).stem.lower() == query_stem:
                    return xml_path, game
        return None  # pas de fallback flou en mode ROM

    # Passe 1 : correspondance exacte sur le champ <path>
    if path_query:
        for xml_path in search_order:
            _ensure_loaded(xml_path, trees)
            tree = trees.get(xml_path)
            if tree is None:
                continue
            for game in get_game_elements(tree):
                if get_field(game, "path") == path_query:
                    return xml_path, game

    # Passe 2 : correspondance floue sur le nom
    best_ratio = 0.0
    best_result: Optional[tuple[Path, ET.Element]] = None

    for xml_path in search_order:
        _ensure_loaded(xml_path, trees)
        tree = trees.get(xml_path)
        if tree is None:
            continue
        for game in get_game_elements(tree):
            ratio = similarity(get_field(game, "name"), name_query)
            if ratio >= threshold and ratio > best_ratio:
                best_ratio = ratio
                best_result = (xml_path, game)

    return best_result


def _ensure_loaded(xml_path: Path, trees: dict[Path, Optional[ET.ElementTree]]) -> None:
    """Parse le fichier si pas encore en cache, y compris les échecs (None)."""
    if xml_path not in trees:
        trees[xml_path] = parse_gamelist(xml_path)


# ---------------------------------------------------------------------------
# Suppression de tous les favoris
# ---------------------------------------------------------------------------

def unmark_all_favorites(source: Path, dry_run: bool = False, force_v10: bool = False) -> None:
    """
    Retire la marque favorite de tous les jeux trouvés sous source.

    Mode v9 : met <favorite>0</favorite> dans gamelist.xml.
    Mode v10 : supprime le champ favorite dans gamelist-userdata.ini.
               Les entrées dont il ne reste aucun autre champ sont supprimées.
               Les fichiers gamelist-userdata.ini vides sont supprimés.
    """
    if force_v10:
        if source.is_dir():
            ini_files = sorted(source.rglob("gamelist-userdata.ini"))
        elif source.is_file() and source.name == "gamelist.xml":
            ini_files = [_userdata_path(source)]
        else:
            logging.warning("unmark v10 : aucune cible trouvée pour %s", source)
            ini_files = []

        total_removed = 0
        for ini_path in ini_files:
            userdata = _read_userdata(ini_path)
            new_data: dict[str, dict[str, str]] = {}
            changed = False
            for rk, fields in userdata.items():
                if "favorite" in fields:
                    fields = {k: v for k, v in fields.items() if k != "favorite"}
                    changed = True
                    total_removed += 1
                if fields:
                    new_data[rk] = fields
                # entrée sans champ restant : supprimée
            if not changed:
                continue
            system = (
                ini_path.parent.relative_to(source).parts[0]
                if source.is_dir()
                else ini_path.parent.name
            )
            if dry_run:
                logging.info("[DRY-RUN] gamelist-userdata.ini NON modifié : %s", ini_path)
                print(f"  [DRY-RUN] INI : {ini_path}")
            else:
                if new_data:
                    _write_userdata(ini_path, new_data)
                else:
                    ini_path.unlink()
                    logging.info("Supprimé (vide après unmark) : %s", ini_path)
                logging.info("Favoris retirés (v10) : [%s] %s", system, ini_path)
                print(f"  ✔  Favoris retirés : {ini_path}")

        dry_tag = "[DRY-RUN] " if dry_run else ""
        verb = "seraient retirés" if dry_run else "retiré(s)"
        logging.info("%s%d favori(s) %s dans gamelist-userdata.ini", dry_tag, total_removed, verb)
        print(f"\n{'[DRY-RUN] ' if dry_run else '✔  '}{total_removed} favori(s) {verb}")
        return

    # Mode v9 : mise à 0 de <favorite> dans gamelist.xml
    gamelists = _collect_gamelists(source, force_v10)
    trees: dict[Path, Optional[ET.ElementTree]] = {}
    dirty: set[Path] = set()
    total = 0

    for xml_path in gamelists:
        _ensure_loaded(xml_path, trees)
        tree = trees.get(xml_path)
        if tree is None:
            continue
        for game in get_game_elements(tree):
            if _is_favorite(game):
                set_field(game, "favorite", "0")
                dirty.add(xml_path)
                total += 1
                logging.debug(
                    "Favori retiré : [%s] %s",
                    xml_path.relative_to(source).parts[0] if source.is_dir() else xml_path.parent.name,
                    get_field(game, "name"),
                )

    for xml_path in dirty:
        write_gamelist(trees[xml_path], xml_path, dry_run=dry_run)  # type: ignore[arg-type]

    dry_tag = "[DRY-RUN] " if dry_run else ""
    verb = "seraient retirés" if dry_run else "retiré(s)"
    logging.info("%s%d favori(s) %s dans %d fichier(s)", dry_tag, total, verb, len(dirty))
    print(f"\n{'[DRY-RUN] ' if dry_run else '✔  '}{total} favori(s) {verb} ({len(dirty)} fichier(s) modifié(s))")


# ---------------------------------------------------------------------------
# Marquage depuis un fichier texte
# ---------------------------------------------------------------------------

def _parse_text_favorites(
    text_file: Path,
    source: Path,
    by_rom: bool = False,
    force_v10: bool = False,
) -> list[dict]:
    """
    Parse un fichier texte de favoris au format sectionné et retourne une
    liste d'entrées compatibles avec apply_favorites.

    Format attendu :
        # commentaire ignoré
        [snes]
        Super Mario World

        [megadrive]
        Sonic The Hedgehog

    Règles :
      - "[texte]" → section système (insensible à la casse)
      - Fichier sans section → recherche globale
      - Système inconnu → section ignorée (None ≠ "")
    """
    lines = text_file.read_text(encoding="utf-8").splitlines()

    first_content = next(
        (l.strip() for l in lines if l.strip() and not l.strip().startswith("#")),
        None,
    )
    is_sectioned = (
        first_content is not None
        and first_content.startswith("[")
        and first_content.endswith("]")
    )

    # Index système → gamelist.xml (toujours gamelist.xml, même en v10)
    system_index: dict[str, Path] = {}
    if source.is_dir():
        for gl in source.rglob("gamelist.xml"):
            system_name = gl.relative_to(source).parts[0]
            system_index.setdefault(system_name.lower(), gl)

    entries: list[dict] = []
    current_gamelist: Optional[str] = None if is_sectioned else ""

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("[") and line.endswith("]"):
            label = line[1:-1].strip()
            resolved_key = system_key_from_label(label)

            gl_path: Optional[Path] = None
            if resolved_key is not None:
                gl_path = system_index.get(resolved_key.lower())
            if gl_path is None:
                gl_path = system_index.get(label.lower())

            if gl_path is not None:
                current_gamelist = str(gl_path)
                logging.debug("Section système : [%s] → %s", resolved_key or label, gl_path)
            else:
                current_gamelist = None
                logging.warning(
                    "Système '%s' introuvable sous %s — section ignorée", label, source
                )
            continue

        if current_gamelist is None:
            logging.debug("Jeu ignoré (système introuvable) : %s", line)
            continue

        entries.append({
            "name": line,
            "path": "",
            "gamelist": current_gamelist,
            "restrict": current_gamelist != "",
            "match_rom": by_rom,
        })

    return entries


def mark_from_text(
    source: Path,
    text_file: Path,
    threshold: float,
    dry_run: bool = False,
    by_rom: bool = False,
    force_v10: bool = False,
) -> None:
    """
    Lit un fichier texte au format sectionné et active les favoris.

    Délègue à apply_favorites via un JSON temporaire.
    """
    import tempfile
    import os

    if not text_file.is_file():
        logging.error("Fichier texte introuvable : %s", text_file)
        sys.exit(1)

    entries = _parse_text_favorites(text_file, source, by_rom=by_rom, force_v10=force_v10)
    mode_label = "ROM(s)" if by_rom else "nom(s) de jeux"
    logging.info("%d %s chargé(s) depuis %s", len(entries), mode_label, text_file)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        json.dump(entries, tmp, ensure_ascii=False)
        tmp_path = Path(tmp.name)

    try:
        apply_favorites(source, tmp_path, threshold, dry_run=dry_run, force_v10=force_v10)
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="recalbox_favorites",
        description="Gestion des favoris EmulationStation/Recalbox",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    p.add_argument(
        "source",
        type=Path,
        help="Chemin vers ROMS_PATH (dossier) ou un gamelist.xml",
    )
    p.add_argument(
        "--log",
        type=Path,
        default=Path("recalbox_favorites.log"),
        metavar="FILE",
        help="Fichier de log (défaut: recalbox_favorites.log)",
    )
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Affiche les messages DEBUG dans la console",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=100.0,
        metavar="PCT",
        help=(
            "Seuil de similarité en %% pour la correspondance de noms "
            "(défaut: 100 = correspondance exacte)"
        ),
    )
    p.add_argument(
        "-n", "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Simule toutes les opérations sans écrire sur le disque.",
    )
    p.add_argument(
        "--v9",
        action="store_true",
        dest="v9",
        default=False,
        help=(
            "Mode Recalbox v9 (legacy) : lit et écrit les favoris dans "
            "gamelist.xml au lieu de gamelist-userdata.ini."
        ),
    )

    sub = p.add_subparsers(dest="command", required=True)

    exp = sub.add_parser("export", help="Exporte les favoris vers un fichier JSON")
    exp.add_argument("output", type=Path, metavar="OUTPUT_JSON")

    ext = sub.add_parser("export-text", help="Exporte les favoris vers un fichier texte")
    ext.add_argument("output", type=Path, metavar="OUTPUT_TXT")

    apl = sub.add_parser("apply", help="Applique un fichier JSON de favoris")
    apl.add_argument("favorites_json", type=Path, metavar="FAVORITES_JSON")

    mrk = sub.add_parser("mark", help="Marque comme favoris les jeux d'un fichier texte")
    mrk.add_argument("text_file", type=Path, metavar="TEXT_FILE")
    mrk.add_argument(
        "--by-rom",
        action="store_true",
        dest="by_rom",
        default=False,
        help=(
            "La liste contient des noms de fichiers ROM (sans extension). "
            "Correspondance exacte sur le stem du champ <path>."
        ),
    )

    sub.add_parser("unmark", help="Retire la marque favori de tous les jeux")

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not 0.0 <= args.threshold <= 100.0:
        parser.error("--threshold doit être entre 0 et 100")
    threshold = args.threshold / 100.0

    setup_logging(args.log, args.verbose)
    force_v10 = not args.v9

    logging.info(
        "=== recalbox_favorites démarré | commande=%s source=%s seuil=%.0f%%%s%s ===",
        args.command,
        args.source,
        args.threshold,
        " | DRY-RUN" if args.dry_run else "",
        " | V9" if args.v9 else "",
    )
    if args.dry_run:
        print("⚙  Mode DRY-RUN activé — aucun fichier ne sera modifié.\n")
    if args.v9:
        print("⚙  Mode V9 (legacy) activé — gamelist.xml utilisé.\n")

    if args.command == "export":
        export_favorites(args.source, args.output, dry_run=args.dry_run, force_v10=force_v10)

    elif args.command == "export-text":
        export_favorites_text(args.source, args.output, dry_run=args.dry_run, force_v10=force_v10)

    elif args.command == "apply":
        apply_favorites(args.source, args.favorites_json, threshold, dry_run=args.dry_run, force_v10=force_v10)

    elif args.command == "mark":
        mark_from_text(args.source, args.text_file, threshold, dry_run=args.dry_run, by_rom=args.by_rom, force_v10=force_v10)

    elif args.command == "unmark":
        if not args.dry_run:
            try:
                answer = input(
                    "⚠  Cette opération va retirer TOUS les favoris sous "
                    f"{args.source}.\n   Confirmer ? [o/N] "
                )
            except EOFError:
                answer = ""
            if answer.strip().lower() not in ("o", "oui", "y", "yes"):
                print("Annulé.")
                return
        unmark_all_favorites(args.source, dry_run=args.dry_run, force_v10=force_v10)

    logging.info("=== terminé ===")


if __name__ == "__main__":
    main()