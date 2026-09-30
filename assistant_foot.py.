import urllib.request
import os
import sys

# 🔗 Ton lien RAW GitHub (s'adapte au nom de ton dépôt)
URL_GITHUB_RAW = "https://raw.githubusercontent.com/halik81/assistant-de-pied/main/assistant_foot.py"

def verifier_mise_a_jour():
    print("🔍 Vérification des mises à jour sur GitHub...")
    try:
        req = urllib.request.Request(URL_GITHUB_RAW, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            code_distant = response.read().decode('utf-8')
            
        nom_fichier_local = sys.argv[0]
        
        # Lecture du code local
        if os.path.exists(nom_fichier_local):
            with open(nom_fichier_local, 'r', encoding='utf-8') as f:
                code_actuel = f.read()
        else:
            code_actuel = ""
            
        # Mise à jour si le code sur GitHub est plus récent/différent
        if code_distant.strip() != code_actuel.strip():
            print("🚀 Nouvelle version détectée ! Mise à jour du script en cours...")
            with open(nom_fichier_local, 'w', encoding='utf-8') as f:
                f.write(code_distant)
            print("✅ Script mis à jour avec succès ! Relancement automatique...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            print("✨ Ton script est déjà à jour !")
    except Exception as e:
        print(f"⚠️ Impossible de vérifier la mise à jour (connexion ou lien invalide) : {e}")

# Exécution de l'auto-update au démarrage
verifier_mise_a_jour()

# =========================================================
# CODE DE L'ASSISTANT D'ANALYSE SPORTIVE (INTERACTIF + IA)
# =========================================================
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingClassifier
import warnings
warnings.filterwarnings('ignore')

API_KEY = "1b5b01361ce9bb88c9f59c85a7a38bc2"

CHAMPIONNATS = {
    "1": {"nom": "La Liga (Espagne)", "code_api": "soccer_spain_la_liga", "code_csv": "SP1"},
    "2": {"nom": "Premier League (Angleterre)", "code_api": "soccer_epl", "code_csv": "E0"},
    "3": {"nom": "Serie A (Italie)", "code_api": "soccer_italy_serie_a", "code_csv": "I1"},
    "4": {"nom": "Ligue 1 (France)", "code_api": "soccer_france_ligue_one", "code_csv": "F1"},
    "5": {"nom": "Bundesliga (Allemagne)", "code_api": "soccer_germany_bundesliga", "code_csv": "D1"}
}

print("\n=== ASSISTANT D'ANALYSE SPORTIVE INTERACTIF ===")
print("0. TOUS LES CHAMPIONNATS")
for cle, val in CHAMPIONNATS.items():
    print(f"{cle}. {val['nom']}")

choix_champ_input = input("\n1. Choisis les championnats (ex: 1,2,3) ou '0' pour TOUS : ").strip()
saisie_champs = [c.strip() for c in choix_champ_input.split(",") if c.strip() in CHAMPIONNATS]

if "0" in choix_champ_input or not saisie_champs:
    champs_selectionnes = list(CHAMPIONNATS.values())
else:
    champs_selectionnes = [CHAMPIONNATS[c] for c in saisie_champs]

print("\n--- MODE DE RECHERCHE ---")
print("1. Choisir moi-même la cote et la confiance")
print("0. 🤖 Laisser l'IA choisir automatiquement les MEILLEURES opportunités")
choix_mode = input("Ton choix (1 ou 0) : ").strip()

mode_auto_ia = False
if choix_mode == "0":
    mode_auto_ia = True
    cote_min_input = 1.30
    seuil_confiance = 0.55
    print("\n🤖 Mode IA Auto-Pilote activé : Scan intelligent des meilleurs ratios Valeur/Sécurité...")
else:
    try:
        cote_min_input = float(input("\n2. Saisis la cote minimale souhaitée (ex: 1.30 ou 1.5) : ").strip().replace(',', '.'))
    except ValueError:
        cote_min_input = 1.20

    try:
        conf_input = float(input("3. Niveau de confiance minimal en % (ex: 60, 70, 75) : ").strip().replace(',', '.'))
        seuil_confiance = conf_input / 100.0
    except ValueError:
        seuil_confiance = 0.65

print("\n4. Pour quel jour veux-tu les prédictions ?")
print("   1. Tous les prochains matchs")
print("   2. Aujourd'hui")
print("   3. Demain")
choix_jour = input("   Ton choix (1, 2 ou 3) : ").strip()

aujourdhui = datetime.now().date()
date_cible = aujourdhui if choix_jour == "2" else (aujourdhui + timedelta(days=1) if choix_jour == "3" else None)

# Chargement & Entraînement
saisons = [f"{y:02d}{(y+1)%100:02d}" for y in range(12, 26)]
dossier_download = '/storage/emulated/0/Download/'

dfs_tous = []
cols_utiles = ['HomeTeam', 'AwayTeam', 'FTR', 'FTHG', 'FTAG', 'HS', 'AS', 'HST', 'AST', 'HC', 'AC', 'B365H', 'B365D', 'B365A']

for config in champs_selectionnes:
    code_csv = config['code_csv']
    fichier_combine = os.path.join(dossier_download, f"BIG_DATA_{code_csv}.csv")
    
    if os.path.exists(fichier_combine):
        df_champ = pd.read_csv(fichier_combine)
    else:
        print(f"🌐 Téléchargement des matchs pour {config['nom']}...")
        dfs = []
        for s in saisons:
            url = f"https://www.football-data.co.uk/mmz4281/{s}/{code_csv}.csv"
            try:
                temp_df = pd.read_csv(url)
                cols_pres = [c for c in cols_utiles if c in temp_df.columns]
                dfs.append(temp_df[cols_pres])
            except Exception:
                pass
        if dfs:
            df_champ = pd.concat(dfs, ignore_index=True)
            try:
                df_champ.to_csv(fichier_combine, index=False)
            except Exception:
                pass
        else:
            continue
    dfs_tous.append(df_champ)

if not dfs_tous:
    print("❌ Aucune donnée historique chargée.")
    exit()

df = pd.concat(dfs_tous, ignore_index=True)

df['Target_1X'] = (df['FTR'].isin(['H', 'D'])).astype(int)
df['Target_X2'] = (df['FTR'].isin(['A', 'D'])).astype(int)
df['Total_Goals'] = df['FTHG'] + df['FTAG']
df['Target_Over15'] = (df['Total_Goals'] > 1.5).astype(int)

stats_equipes = {}
for eq in df['HomeTeam'].dropna().unique():
    df_eq_h = df[df['HomeTeam'] == eq]
    df_eq_a = df[df['AwayTeam'] == eq]
    total_m = len(df_eq_h) + len(df_eq_a) + 1e-5
    hs = (df_eq_h['HS'].sum() + df_eq_a['AS'].sum()) / total_m
    hst = (df_eq_h['HST'].sum() + df_eq_a['AST'].sum()) / total_m
    hc = (df_eq_h['HC'].sum() + df_eq_a['AC'].sum()) / total_m
    stats_equipes[eq] = {'HS': hs, 'HST': hst, 'HC': hc}

features = ['HS', 'AS', 'HST', 'AST', 'HC', 'AC', 'B365H', 'B365D', 'B365A']
df_clean = df[features + ['Target_1X', 'Target_X2', 'Target_Over15']].dropna()
X = df_clean[features]

print(f"\n🧠 Entraînement du modèle sur {len(df_clean)} matchs...")
model_1X = GradientBoostingClassifier(n_estimators=180, learning_rate=0.03, max_depth=4, random_state=42).fit(X, df_clean['Target_1X'])
model_X2 = GradientBoostingClassifier(n_estimators=180, learning_rate=0.03, max_depth=4, random_state=42).fit(X, df_clean['Target_X2'])
model_O15 = GradientBoostingClassifier(n_estimators=180, learning_rate=0.03, max_depth=4, random_state=42).fit(X, df_clean['Target_Over15'])
print("✅ Modèle prêt !")

def analyser_matchs(c_min, c_conf, d_cible, auto_ia=False):
    resultats = []
    for config in champs_selectionnes:
        sport_api = config['code_api']
        url_api = f"https://api.the-odds-api.com/v4/sports/{sport_api}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h"
        try:
            req = urllib.request.Request(url_api, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                matchs_api = json.loads(response.read().decode('utf-8'))

                for match in matchs_api:
                    commence_a = match.get('commence_time')
                    if d_cible and commence_a:
                        date_match = datetime.strptime(commence_a[:10], "%Y-%m-%d").date()
                        if date_match != d_cible:
                            continue

                    h_team = match['home_team']
                    a_team = match['away_team']

                    b365h, b365d, b365a = 2.0, 3.2, 3.5
                    if match.get('bookmakers'):
                        for m in match['bookmakers'][0].get('markets', []):
                            if m['key'] == 'h2h':
                                for c in m['outcomes']:
                                    if c['name'] == h_team: b365h = c['price']
                                    elif c['name'] == a_team: b365a = c['price']
                                    elif c['name'] == 'Draw': b365d = c['price']

                    cote_1X = round(1 / ((1 / b365h) + (1 / b365d)), 2) if b365h and b365d else 1.25
                    cote_X2 = round(1 / ((1 / b365a) + (1 / b365d)), 2) if b365a and b365d else 1.25
                    cote_1X_O15 = round(cote_1X * 1.30, 2)
                    cote_X2_O15 = round(cote_X2 * 1.30, 2)

                    hs_h = stats_equipes.get(h_team, {}).get('HS', df['HS'].mean())
                    hst_h = stats_equipes.get(h_team, {}).get('HST', df['HST'].mean())
                    hc_h = stats_equipes.get(h_team, {}).get('HC', df['HC'].mean())

                    as_a = stats_equipes.get(a_team, {}).get('HS', df['AS'].mean())
                    ast_a = stats_equipes.get(a_team, {}).get('HST', df['AST'].mean())
                    ac_a = stats_equipes.get(a_team, {}).get('HC', df['AC'].mean())

                    input_data = pd.DataFrame([{
                        'HS': hs_h, 'AS': as_a, 'HST': hst_h, 'AST': ast_a,
                        'HC': hc_h, 'AC': ac_a, 'B365H': b365h, 'B365D': b365d, 'B365A': b365a
                    }])

                    p_1X = model_1X.predict_proba(input_data)[0][1]
                    p_X2 = model_X2.predict_proba(input_data)[0][1]
                    p_O15 = model_O15.predict_proba(input_data)[0][1]

                    p_1X_O15 = p_1X * p_O15
                    p_X2_O15 = p_X2 * p_O15

                    lignes_prop = []
                    score_valeur = 0

                    if p_1X_O15 >= c_conf and cote_1X_O15 >= c_min:
                        lignes_prop.append(f"   🔥 COMBO BOOSTÉ : 1X & +1.5 Buts | Cote ~{cote_1X_O15} | Confiance : {p_1X_O15*100:.1f}%")
                        score_valeur = max(score_valeur, p_1X_O15 * cote_1X_O15)
                    elif p_X2_O15 >= c_conf and cote_X2_O15 >= c_min:
                        lignes_prop.append(f"   🔥 COMBO BOOSTÉ : X2 & +1.5 Buts | Cote ~{cote_X2_O15} | Confiance : {p_X2_O15*100:.1f}%")
                        score_valeur = max(score_valeur, p_X2_O15 * cote_X2_O15)

                    if p_1X >= c_conf and cote_1X >= c_min:
                        lignes_prop.append(f"   🛡️ SÉCURITÉ : 1X (Dom ou Nul) | Cote ~{cote_1X} | Confiance : {p_1X*100:.1f}%")
                        score_valeur = max(score_valeur, p_1X * cote_1X)
                    elif p_X2 >= c_conf and cote_X2 >= c_min:
                        lignes_prop.append(f"   🛡️ SÉCURITÉ : X2 (Nul ou Ext) | Cote ~{cote_X2} | Confiance : {p_X2*100:.1f}%")
                        score_valeur = max(score_valeur, p_X2 * cote_X2)

                    if lignes_prop:
                        date_str = commence_a[:10] if commence_a else ""
                        resultats.append({
                            'champ': config['nom'].split(' ')[0],
                            'match': f"{h_team} vs {a_team}",
                            'date': date_str,
                            'props': lignes_prop,
                            'p_1X': p_1X,
                            'p_X2': p_X2,
                            'score_ia': score_valeur
                        })
        except Exception:
            pass
            
    if auto_ia:
        resultats = sorted(resultats, key=lambda x: x['score_ia'], reverse=True)[:8]
        
    return resultats

derniers_resultats = analyser_matchs(cote_min_input, seuil_confiance, date_cible, auto_ia=mode_auto_ia)

def afficher_resultats(liste, est_ia=False):
    titre = "   🤖 SÉLECTION IA AUTO-PILOTE (TOP OPPORTUNITÉS)" if est_ia else f"   PRÉDICTIONS TROUVÉES ({len(liste)} MATCHS)"
    print("\n==================================================")
    print(titre)
    print("==================================================")
    if not liste:
        print("Aucun match ne correspond aux filtres actuels.")
    else:
        for idx, item in enumerate(liste, 1):
            tag_ia = " ⭐ [TOP IA]" if est_ia else ""
            print(f"[{idx}] ⚽ [{item['champ']}] {item['match']} ({item['date']}){tag_ia}")
            for line in item['props']:
                print(line)
            print("-" * 50)

afficher_resultats(derniers_resultats, est_ia=mode_auto_ia)

# Boucle interactive
while True:
    print("\n💬 QUE SOUHAITES-TU FAIRE MAINTENANT ?")
    print("0. 🤖 Laisser l'IA sélectionner les meilleures opportunités")
    print("1. Ajuster manuellement la cote minimale et la confiance")
    print("2. Filtrer par un championnat précis")
    print("3. Analyse détaillée d'un match (saisir le numéro)")
    print("4. Relancer un scan complet")
    print("5. Quitter")
    
    choix_action = input("\n👉 Ton choix (0-5) : ").strip()

    if choix_action == "0":
        print("\n🤖 Analyse IA en cours...")
        derniers_resultats = analyser_matchs(1.30, 0.55, date_cible, auto_ia=True)
        afficher_resultats(derniers_resultats, est_ia=True)

    elif choix_action == "1":
        try:
            cote_min_input = float(input("   Nouvelle cote min (ex: 1.4) : ").strip().replace(',', '.'))
            conf_input = float(input("   Nouveau niveau de confiance en % (ex: 65) : ").strip().replace(',', '.'))
            seuil_confiance = conf_input / 100.0
            print("🔄 Recalcul...")
            derniers_resultats = analyser_matchs(cote_min_input, seuil_confiance, date_cible, auto_ia=False)
            afficher_resultats(derniers_resultats, est_ia=False)
        except ValueError:
            print("⚠️️ Valeur invalide.")

    elif choix_action == "2":
        nom_f = input("   Nom du championnat (ex: Premier, La, Serie, Ligue, Bundesliga) : ").strip().lower()
        filtres = [m for m in derniers_resultats if nom_f in m['champ'].lower()]
        afficher_resultats(filtres, est_ia=False)

    elif choix_action == "3":
        if not derniers_resultats:
            print("⚠️ Aucun match disponible.")
            continue
        try:
            num_m = int(input(f"   Numéro du match (1 à {len(derniers_resultats)}) : ").strip())
            if 1 <= num_m <= len(derniers_resultats):
                m_sel = derniers_resultats[num_m - 1]
                print(f"\n📊 ANALYSE DÉTAILLÉE : {m_sel['match']}")
                print(f"   • Championnat : {m_sel['champ']}")
                print(f"   • Date : {m_sel['date']}")
                print(f"   • Probabilité 1X : {m_sel['p_1X']*100:.1f}%")
                print(f"   • Probabilité X2 : {m_sel['p_X2']*100:.1f}%")
                print(f"   • Score d'Efficacité IA : {m_sel['score_ia']:.2f}")
            else:
                print("⚠️ Numéro invalide.")
        except ValueError:
            print("⚠ Entrée invalide.")

    elif choix_action == "4":
        print("🔄 Relancement...")
        derniers_resultats = analyser_matchs(cote_min_input, seuil_confiance, date_cible, auto_ia=False)
        afficher_resultats(derniers_resultats, est_ia=False)

    elif choix_action == "5":
        print("\n👋 À bientôt !")
        break
