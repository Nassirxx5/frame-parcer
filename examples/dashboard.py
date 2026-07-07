# examples/dashboard.py
import os
import sys
import streamlit as st
import psycopg2
# Inclusion automatique du dossier src pour le chargement des fonctions de base
dossier_actuel = os.path.dirname(os.path.abspath(__file__))
chemin_src = os.path.abspath(os.path.join(dossier_actuel, "..", "src"))
if chemin_src not in sys.path:
    sys.path.append(chemin_src)

from template import parser_trame_gprs, reconstruire_trame_propre

# Configuration de l'application en mode plein écran
st.set_page_config(page_title="Omnitech Central GPRS", layout="wide")

st.title("📡 Centre de Traitement GPRS - Version Standard avec Compteurs")
st.markdown("Cette interface décode les entrées analogiques (4-20mA), numériques (TOR) et gère désormais les compteurs d'impulsions industriels.")
st.divider()

# ==============================================================================
# --- BARRE LATÉRALE DE CONFIGURATION (SIDEBAR) ---
# ==============================================================================
st.sidebar.header("⚙️ Configuration Générale")

nb_entrees = int(st.sidebar.number_input("Nombre d'entrées TOR", min_value=1, max_value=12, value=9, step=1))

st.sidebar.divider()

# Configuration des étiquettes personnalisées pour les TOR
st.sidebar.subheader("✏️ Noms des entrées TOR")
noms_tor = {}
for i in range(1, nb_entrees + 1):
    noms_tor[i] = st.sidebar.text_input(f"Nom pour E{i} :", value=f"Entrée Numérique {i}", key=f"sb_tor_{i}")

st.sidebar.divider()

# Configuration des étiquettes pour les Compteurs (U)
st.sidebar.subheader("🔢 Noms des Compteurs (U)")
nb_compteurs_max = 3
noms_compteurs = {}
for i in range(1, nb_compteurs_max + 1):
    noms_compteurs[i] = st.sidebar.text_input(f"Nom du Compteur {i} :", value=f"Compteur Général {i}", key=f"sb_compteur_{i}")


# ==============================================================================
# --- ZONE PRINCIPALE : ACCUEIL ET EXÉCUTION ---
# ==============================================================================
conn = psycopg2.connect(
            host="localhost",
            database="omnitech_db",   # La base de données qu'on vient de créer
            user="postgres",          # L'utilisateur administrateur
            password="123"       # ⚠️ Mets ici le mot de passe exact que tu as tapé dans pgAdmin !2
        )
# Exemple de trame réelle incluant le bloc compteur $U:
# Le compteur 1 vaut '12345678' en brut (qui devra décoder 78563412 en décimal)
exemple_trame = (
    "22:51:42;05/07/2026;$ADC8C275C5B856D003EA1002900000000FFFFFFFFFFFFFFFFFFFF%"
    "$ENTREES:309122300300300300FFFFFF11111100%"
    "$U:12345678AABBCCDD01020304%-1"
)

st.subheader("📥 Saisie de la trame brute")
trame_brute = st.text_area("Collez le log industriel reçu ici :", value=exemple_trame, height=75)

st.divider()

# Helper : Fonction de décodage Little-Endian demandée pour les compteurs
def decoder_bloc_compteur(hex_8_lettres):
    if len(hex_8_lettres) != 8:
        return None
    # Règle demandée : inversion 2 par 2 de droite à gauche
    hex_inverse = hex_8_lettres[6:8] + hex_8_lettres[4:6] + hex_8_lettres[2:4] + hex_8_lettres[0:2]
    # Conversion finale en base 10 (décimal)
    valeur_decimale = int(hex_inverse, 16)
    return hex_inverse, valeur_decimale


# --- TRAITEMENT ET AFFICHAGE DES RÉSULTATS ---
if st.button("🚀 Lancer le traitement complet", type="primary"):
    
    # Extraction des sous-chaînes brutes
    chaine_adc = trame_brute.split("$ADC")[1].split("%")[0] if "$ADC" in trame_brute else ""
    chaine_entrees = trame_brute.split("$ENTREES:")[1].split("%")[0] if "$ENTREES:" in trame_brute else ""
    chaine_u = trame_brute.split("$U:")[1].split("%")[0] if "$U:" in trame_brute else ""
    
    # Analyse de base pour l'horodatage
    res_analyse = parser_trame_gprs(trame_brute, nb_entrees_par_carte=nb_entrees)
    
    if res_analyse["date"] == "Inconnue":
        st.error("⚠️ Erreur critique : Structure de trame corrompue ou illisible.")
    else:
        st.success("Décodage et conversion effectués avec succès !")
        
        # 1. Génération de la trame nettoyée (On ajoute la date et l'heure)
        # On ne passe plus le paramètre separateur_tor, il prendra sa valeur par défaut dans template.py
        trame_propre_csv = reconstruire_trame_propre(trame_brute, nb_entrees_par_carte=nb_entrees)
        
        st.subheader("💎 Nouvelle trame adéquate générée (Normalisée)")
        st.info("Trame nettoyée exploitable en base de données :")
        st.code(trame_propre_csv, language="text")
        
        st.divider()
        
        # 2. Métriques globales temporelles
        st.subheader("📊 Tableau de Bord d'Analyse Visuelle")
        col_t1, col_t2 = st.columns(2)
        col_t1.metric("📅 Date du relevé", res_analyse["date"])
        col_t2.metric("🕒 Heure du relevé", res_analyse["heure"])
        
        st.divider()
        
        # --- BLOC ANALOGIQUE (4-20 mA) ---
        st.markdown("#### 📈 Entrées Analogiques (4-20 mA)")
        if res_analyse["analogiques"]:
            cols_ana = st.columns(6)
            for idx, val in enumerate(res_analyse["analogiques"]):
                with cols_ana[idx % 6]:
                    st.metric(label=f"Voie {idx+1:02d}", value=f"{val:.2f} mA")
        else:
            st.info("Aucune donnée analogique détectée.")
            
        st.divider()
        
        # --- NOUVEAU BLOC : LES COMPTEURS DYNAMIQUES (U) ---
        st.markdown("#### 🔢 Entrées Compteurs ($U - Décodage 32-bit Little-Endian)")
        
        if chaine_u:
            # Découpage par bloc de 8 caractères hexadécimaux
            liste_compteurs_bruts = [chaine_u[i:i+8] for i in range(0, len(chaine_u), 8) if len(chaine_u[i:i+8]) == 8]
            
            if liste_compteurs_bruts:
                cols_compteurs = st.columns(len(liste_compteurs_bruts))
                
                for id_c, hex_brut in enumerate(liste_compteurs_bruts):
                    num_index = id_c + 1
                    nom_final_compteur = noms_compteurs.get(num_index, f"Compteur {num_index}")
                    
                    # Application de ta règle de retournement et décodage
                    hex_retourne, valeur_decimale = decoder_bloc_compteur(hex_brut)
                    
                    with cols_compteurs[id_c]:
                        # On affiche la valeur décimale finale et un sous-texte d'explication de la permutation
                        st.metric(label=nom_final_compteur, value=f"{valeur_decimale:,} tr/min".replace(",", " "))
                        st.caption(f"Brut: `{hex_brut}` ➔ Inversé: `{hex_retourne}`")
            else:
                st.warning("Le bloc $U existe mais ne contient pas de chaînes valides de 8 caractères.")
        else:
            st.info("Aucun bloc de compteurs ($U) détecté dans cette trame.")
            
        st.divider()
        
        # --- BLOC NUMÉRIQUE (TOR) ---
        st.markdown(f"#### 💡 Entrées Numériques ({nb_entrees} entrées configurées)")
        for id_carte, carte_bits in enumerate(res_analyse["tor_cartes"]):
            with st.expander(f"📦 Carte d'extension N°{id_carte + 1}", expanded=True):
                
                # --- SÉCURITÉ AJOUTÉE ICI : On vérification que la carte n'est pas vide ---
                if carte_bits is not None:
                    cols_tor = st.columns(len(carte_bits))
                    for id_bit, etat in enumerate(carte_bits):
                        numero_entree_physique = id_bit + 1
                        with cols_tor[id_bit]:
                            # Extraction du libellé personnalisé depuis le menu de gauche
                            nom_affiche = noms_tor.get(numero_entree_physique, f"Entrée {numero_entree_physique}")
                            badge = "🟢 ON" if etat else "🔴 OFF"
                            st.markdown(f"**{nom_affiche}**\n\n{badge}")
                else:
                    # Message de secours si la fonction de base n'a pas pu décoder ce bloc
                    st.warning("⚠️ Les données de cette carte TOR n'ont pas pu être lues (Format de trame incompatible).")
