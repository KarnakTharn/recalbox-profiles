import os

def rotate_guest_files(base):
    """
    base = nom du profil, ex: "Profil1"
    Le script applique le cycle de renommage :
    unselect -> normal -> select -> unselect
    """

    A = f"{base}_unselect.png"
    B = f"{base}_select.png"
    C = f"{base}.png"
    TMP = f"{base}_tmp.png"

    # Vérification des fichiers
    for f in [A, B, C]:
        if not os.path.exists(f):
            print(f"Fichier manquant : {f}")
            return

    # Cycle :
    # A -> TMP
    os.rename(A, TMP)

    # B -> A
    os.rename(B, A)

    # C -> B
    os.rename(C, B)

    # TMP -> C
    os.rename(TMP, C)

    print(f"Cycle effectué pour {base}")

# Exemple d'utilisation :
rotate_guest_files("Profil1")
