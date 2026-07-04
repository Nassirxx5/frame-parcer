trame_recue = "1023,512,1,0#"

# 1. Nettoyer la trame (enlever le #)
trame_propre = trame_recue.replace("#", "")

# 2. Découper (Split)
valeurs = trame_propre.split(",")

# 3. Assigner et convertir (2 analogiques, 2 TOR)
if len(valeurs) == 4:
    ana_1 = int(valeurs[0]) # 1023
    ana_2 = int(valeurs[1]) # 512
    tor_1 = bool(int(valeurs[2])) # True (1)
    tor_2 = bool(int(valeurs[3])) # False (0)
    
    print(f"Analogiques: {ana_1}, {ana_2} | TOR: {tor_1}, {tor_2}")