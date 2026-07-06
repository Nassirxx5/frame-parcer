# exemples/exemple_dashboard.py
import sys
import streamlit as st

# Importation de votre moteur (Template)
sys.path.append('../src')
from parser_omnitech import parser_trame

# 1. Configuration de la page
st.set_page_config(page_title="Omnitech IoT Dashboard", layout="centered")
st.title("🎛️ Dashboard de Supervision IoT")
st.markdown("Ce dashboard teste le parseur générique pour SIM800L et OPC.")
st.divider()

# 2. Zone de configuration (Sidebar)
st.sidebar.header("Configuration de la Trame")
nb_ana = st.sidebar.number_input("Nombre de variables Analogiques", min_value=1, value=2)
nb_tor = st.sidebar.number_input("Nombre de variables TOR", min_value=1, value=2)

# 3. Zone d'entrée de la donnée brute
trame_brute = st.text_input("Entrez la trame GPRS/OPC reçue :", value="25.5,1013,1,0#")

# 4. Traitement et Affichage
if st.button("Décoder et Afficher"):
    try:
        # Appel de VOTRE fonction
        resultats = parser_trame(trame_brute, nb_ana, nb_tor)
        
        st.success("Trame décodée avec succès !")
        
        # Affichage des valeurs Analogiques
        st.subheader("📊 Valeurs Analogiques")
        colonnes_ana = st.columns(nb_ana)
        for i in range(nb_ana):
            with colonnes_ana[i]:
                st.metric(label=f"Capteur {i+1}", value=resultats["analogiques"][i])
                
        # Affichage des valeurs TOR (Tout Ou Rien)
        st.subheader("💡 Valeurs Digitales (TOR)")
        colonnes_tor = st.columns(nb_tor)
        for i in range(nb_tor):
            etat = "🟢 ON" if resultats["tor"][i] else "🔴 OFF"
            with colonnes_tor[i]:
                st.info(f"État Sortie {i+1} : **{etat}**")
                
    except Exception as e:
        st.error(f"Erreur lors du décodage. Vérifiez que la trame correspond à la configuration. (Détail: {e})")
