def extraire_donnees(trame_brute, nb_ana, nb_tor, separateur=",", fin="#"):
    """
    Décode une trame en fonction des paramètres fournis par l'utilisateur.
    """
    try:
        trame_nettoyee = trame_brute.replace(fin, "").strip()
        valeurs = trame_nettoyee.split(separateur)
        
        total_attendu = nb_ana + nb_tor
        if len(valeurs) != total_attendu:
            return {"erreur": f"Trame invalide. Attendu: {total_attendu}, Reçu: {len(valeurs)}"}
        
        donnees = {"analogiques": [], "tor": []}
        
        for i in range(nb_ana):
            donnees["analogiques"].append(float(valeurs[i]))
            
        for i in range(nb_ana, total_attendu):
            donnees["tor"].append(bool(int(valeurs[i])))
            
        return donnees

    except Exception as e:
        return {"erreur": f"Erreur de décodage : {e}"}
