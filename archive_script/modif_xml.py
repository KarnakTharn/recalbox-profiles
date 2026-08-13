import json 

import xml.etree.ElementTree as ET

# Fonction pour lire le fichier JSON et extraitre le nom du profil actif
def get_active_profile_name(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data.get('profile', None)

# Fonction pour modifier le fichier XML avec le nom du profil actif
def modify_xml_with_profile(xml_file, profile_name):
    """
    Fonction pour modifier le fichier XML avec le nom du profil actif.
    Le fichier utilisera une racine <gameList> contenant des éléments <game>.
    """
    # Charger le fichier xml
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Parcourir tous les éléments <game> dans le document
    for game in root.findall('.//game'):
        name_element = game.find('name')
        if name_element is None or name_element.text is None:
            continue

        name = name_element.text.strip()
        region = game.find('region')

        if name == profile_name:
            if region is not None:
                region.text = 'fr'  # Mettre à jour la région à France
            else:
                # Si l'élément <region> n'existe pas, le créer
                region = ET.SubElement(game, 'region')
                region.text = 'fr'
        else:
            if region is not None:
                region.text = 'eu'  # Mettre à jour la région à Europe
            else:
                # Si l'élément <region> n'existe pas, le créer
                region = ET.SubElement(game, 'region')
                region.text = 'eu'

    # Sauvegarder les modifications dans le fichier xml
    tree.write(xml_file, encoding='utf-8', xml_declaration=True)


# Exemple d'utilisation
if __name__ == "__main__":
    json_file_path = '/recalbox/share/profiles/current_profile.json'  # Remplacez par le chemin réel de votre fichier JSON
    xml_file_path = '/recalbox/share/roms/profiles_swap/gamelist.xml'    # Remplacez par le chemin réel de votre fichier XML

    active_profile_name = get_active_profile_name(json_file_path)
    if active_profile_name:
        modify_xml_with_profile(xml_file_path, active_profile_name)
        print(f"Le fichier XML a été mis à jour avec le profil actif: {active_profile_name}")
    else:
        print("Aucun profil actif trouvé dans le fichier JSON.")
