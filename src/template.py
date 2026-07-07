# src/template.py
import re


def convert_analog_value(v):
    """Applique la formule d'étalonnage par paliers (C# convertie en Python)"""
    if v >= 182: return 20.0
    elif v >= 177: return (v - 177) / 5.0 + 19.0
    elif v >= 171: return (v - 171) / 6.0 + 18.0
    elif v >= 164: return (v - 164) / 7.0 + 17.0
    elif v >= 157: return (v - 157) / 7.0 + 16.0
    elif v >= 149: return (v - 149) / 8.0 + 15.0
    elif v >= 140: return (v - 140) / 9.0 + 14.0
    elif v >= 131: return (v - 131) / 9.0 + 13.0
    elif v >= 121: return (v - 121) / 10.0 + 12.0
    elif v >= 112: return (v - 112) / 9.0 + 11.0
    elif v >= 101: return (v - 101) / 11.0 + 10.0
    elif v >= 91:  return (v - 91) / 10.0 + 9.0
    elif v >= 81:  return (v - 81) / 10.0 + 8.0
    elif v >= 71:  return (v - 71) / 10.0 + 7.0
    elif v >= 60:  return (v - 60) / 11.0 + 6.0
    elif v >= 50:  return (v - 50) / 10.0 + 5.0
    elif v < 40:   return 4.0
    else:          return (v - 40) / 10.0 + 4.0


def decoder_carte_tor(triplet_hex, nb_entrees):
    """
    Prend un triplet hexadécimal, le transcode en binaire,
    lit de droite à gauche selon le nombre d'entrées et élimine le reste.
    """
    val_dec = int(triplet_hex, 16)
    bin_str = bin(val_dec)[2:].zfill(12)  # 3 hex = 12 bits théoriques
    bits_ordonnes = bin_str[::-1]         # Lecture de droite à gauche (LSB à l'index 0)
    bits_utiles = bits_ordonnes[:nb_entrees] # On garde uniquement le nombre d'entrées
    
    return [bit == '1' for bit in bits_utiles]


def parser_trame_gprs(texte_brut, nb_entrees_par_carte=9):
    """
    Analyse le log brut et extrait la date, l'heure, 
    les listes brutes décodées des valeurs analogiques et TOR.
    """
    meta_match = re.search(r"(\d{2}:\d{2}:\d{2});(\d{2}/\d{2}/\d{4});.*\$ADC", texte_brut)
    heure = meta_match.group(1) if meta_match else "Inconnue"
    date = meta_match.group(2) if meta_match else "Inconnue"
    
    # Extraction Analogique
    adc_match = re.search(r"\$ADC([0-9A-Fa-f]+)%", texte_brut)
    analogiques = []
    if adc_match:
        chaine_adc = adc_match.group(1)
        for i in range(0, len(chaine_adc), 2):
            hextet = chaine_adc[i:i+2]
            if len(hextet) == 2:
                analogiques.append(convert_analog_value(int(hextet, 16)))
                
    # Extraction TOR
    entrees_match = re.search(r"\$ENTREES:([0-9A-Fa-f]+)%", texte_brut)
    tor_cartes = []
    cartes_defectueuses = []  # Numéros (1-indexés) des cartes en défaut (valeur FFF)
    if entrees_match:
        chaine_entrees = entrees_match.group(1)
        for i in range(0, len(chaine_entrees), 3):
            triplet = chaine_entrees[i:i+3]
            if triplet and len(triplet) == 3:
                numero_carte = len(tor_cartes) + 1
                if triplet.upper() == "FFF":
                    cartes_defectueuses.append(numero_carte)
                    tor_cartes.append(None)  # Pas de données fiables à décoder pour cette carte
                else:
                    etats_carte = decoder_carte_tor(triplet, nb_entrees_par_carte)
                    tor_cartes.append(etats_carte)

    return {
        "date": date,
        "heure": heure,
        "analogiques": analogiques,
        "tor_cartes": tor_cartes,
        "cartes_defectueuses": cartes_defectueuses
    }


def reconstruire_trame_propre(texte_brut, nb_entrees_par_carte=9, separateur_tor="|"):
    """
    Prend la trame brute, la nettoie, applique les règles de formatage demandées :
    - Un ';' après chaque valeur analogique.
    - Le séparateur choisi après chaque bit TOR.
    - Un '#' à la fin absolue de la trame.
    """
    donnees = parser_trame_gprs(texte_brut, nb_entrees_par_carte)
    
    if donnees["date"] == "Inconnue":
        return "ERREUR : Trame invalide ou impossible à décoder."

    # Début de la trame adéquate : DATE;HEURE;
    nouvelle_trame = f"{donnees['date']};{donnees['heure']};"
    
    # Ajout des valeurs analogiques suivies de ';'
    for val_ana in donnees["analogiques"]:
        nouvelle_trame += f"{val_ana:.2f};"
        
    # Ajout des valeurs TOR suivies du séparateur
    for carte in donnees["tor_cartes"]:
        if carte is None:
            # Carte en défaut (FFF) : pas de données fiables, on écrit des zéros
            for _ in range(nb_entrees_par_carte):
                nouvelle_trame += f"0{separateur_tor}"
        else:
            for bit in carte:
                val_bit = "1" if bit else "0"
                nouvelle_trame += f"{val_bit}{separateur_tor}"
            
    # Ajout du symbole '#' à la fin
    nouvelle_trame += "#"
    
    return nouvelle_trame
