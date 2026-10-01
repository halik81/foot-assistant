import urllib.request
import urllib.parse
import urllib.error
import os
import sys

# 🔗 Lien RAW GitHub du script (mise à jour automatique)
URL_GITHUB_RAW = "https://raw.githubusercontent.com/halik81/foot-assistant/main/assistant_foot.py"


def verifier_mise_a_jour():
    print("🔍 Vérification des mises à jour sur GitHub...")
    try:
        req = urllib.request.Request(URL_GITHUB_RAW, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            code_distant = response.read().decode('utf-8')
    except Exception as e:
        print(f"⚠️ Impossible de récupérer la mise à jour ({e}). Lancement du script local...")
        return

    try:
        nom_fichier_local = os.path.abspath(sys.argv[0])

        if os.path.exists(nom_fichier_local):
            with open(nom_fichier_local, 'r', encoding='utf-8') as f:
                code_actuel = f.read()
        else:
            code_actuel = ""

        if code_distant.strip() == code_actuel.strip():
            print("✨ Ton script est déjà à jour !")
            return

        # Sécurité : on vérifie que le code téléchargé est valide avant d'écraser le fichier local
        try:
            compile(code_distant, "assistant_foot_distant", "exec")
        except SyntaxError as e:
            print(f"⚠️ La version GitHub contient une erreur de syntaxe (ligne {e.lineno}). Mise à jour annulée, lancement du script local...")
            return

        print("🚀 Nouvelle version détectée ! Mise à jour du script...")
        with open(nom_fichier_local, 'w', encoding='utf-8') as f:
            f.write(code_distant)
        print("✅ Script mis à jour avec succès ! Relancement...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        print(f"⚠️ Erreur lors de la mise à jour locale : {e}")


# Exécution de la vérification au démarrage
verifier_mise_a_jour()

# =========================================================
# CODE DE L'ASSISTANT D'ANALYSE SPORTIVE (INTERACTIF + IA)
# =========================================================
import re
import json
import time
import difflib
import unicodedata
import warnings
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

warnings.filterwarnings('ignore')

dossier_download = os.environ.get("FOOT_DOSSIER", '/storage/emulated/0/Download/')

aujourdhui = datetime.now().date()
# Saison en cours : de juillet à juin (ex. octobre 2026 -> saison 2026/2027)
annee_saison = aujourdhui.year if aujourdhui.month >= 7 else aujourdhui.year - 1


def code_saison(y):
    return f"{y % 100:02d}{(y + 1) % 100:02d}"


saisons_historique = [code_saison(y) for y in range(2012, annee_saison)]
saison_courante = code_saison(annee_saison)

TEST_FIABILITE = True   # mets False pour accélérer le démarrage (saute le test sur les matchs récents)
N_FORME = 5             # nombre de matchs pris en compte pour la forme
AF_PAUSE = 6.5          # secondes entre deux requêtes API-Football (plan gratuit : 10 requêtes/minute)


# ---------------------------------------------------------
# Clés API : jamais écrites dans le code (le dépôt GitHub est public)
# Ordre de recherche : variable d'environnement -> fichier local -> saisie
# ---------------------------------------------------------
def charger_cle(nom_env, nom_fichier, libelle, optionnelle=False):
    cle = os.environ.get(nom_env, "").strip()
    if cle:
        return cle

    chemin = os.path.join(dossier_download, nom_fichier)
    if os.path.exists(chemin):
        try:
            with open(chemin, 'r', encoding='utf-8') as f:
                cle = f.read().strip()
        except Exception:
            cle = ""
        if cle == "AUCUNE":
            return ""
        if cle:
            return cle

    print(f"\n🔑 Aucune clé {libelle} trouvée.")
    if optionnelle:
        print("   (Entrée pour ignorer : les blessures/compos seront désactivées.)")
    while True:
        cle = input("   Colle ta clé ici : ").strip()
        if not cle and optionnelle:
            break
        if not cle:
            print("   ⚠️ Cette clé est nécessaire.")
            continue
        if len(cle) != 32:
            rep = input(f"   ⚠️ {len(cle)} caractères (32 en général). L'utiliser quand même ? (o/n) : ").strip().lower()
            if rep != 'o':
                continue
        break

    try:
        with open(chemin, 'w', encoding='utf-8') as f:
            f.write(cle if cle else "AUCUNE")
        if cle:
            print(f"   ✅ Clé enregistrée dans {chemin} (elle ne sera pas publiée sur GitHub).")
        else:
            print(f"   ℹ️ Fonction désactivée. Supprime {chemin} pour la réactiver.")
    except Exception:
        print("   ⚠️ Impossible d'enregistrer la clé, elle sera redemandée au prochain lancement.")
    return cle


API_KEY = charger_cle("ODDS_API_KEY", "odds_api_key.txt", "The Odds API")
AF_KEY = charger_cle("APIFOOTBALL_KEY", "apifootball_key.txt", "API-Football", optionnelle=True)

CHAMPIONNATS = {
    "1": {"nom": "La Liga (Espagne)", "code_api": "soccer_spain_la_liga", "code_csv": "SP1"},
    "2": {"nom": "Premier League (Angleterre)", "code_api": "soccer_epl", "code_csv": "E0"},
    "3": {"nom": "Serie A (Italie)", "code_api": "soccer_italy_serie_a", "code_csv": "I1"},
    "4": {"nom": "Ligue 1 (France)", "code_api": "soccer_france_ligue_one", "code_csv": "F1"},
    "5": {"nom": "Bundesliga (Allemagne)", "code_api": "soccer_germany_bundesliga", "code_csv": "D1"}
}

# Identifiants des ligues chez API-Football
LIGUES_AF = {
    "soccer_spain_la_liga": 140,
    "soccer_epl": 39,
    "soccer_italy_serie_a": 135,
    "soccer_france_ligue_one": 61,
    "soccer_germany_bundesliga": 78,
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

date_cible = aujourdhui if choix_jour == "2" else (aujourdhui + timedelta(days=1) if choix_jour == "3" else None)

# ---------------------------------------------------------
# Chargement des données historiques
# - saisons terminées : mises en cache dans Download (un fichier par championnat et par saison en cours)
# - saison en cours : retéléchargée à chaque lancement, pour avoir la forme à jour
# ---------------------------------------------------------
cols_utiles = ['Date', 'HomeTeam', 'AwayTeam', 'FTR', 'FTHG', 'FTAG', 'HS', 'AS', 'HST', 'AST', 'HC', 'AC', 'B365H', 'B365D', 'B365A']


def telecharger_saisons(code_csv, liste_saisons):
    dfs = []
    for s in liste_saisons:
        url = f"https://www.football-data.co.uk/mmz4281/{s}/{code_csv}.csv"
        try:
            temp_df = pd.read_csv(url)
            cols_pres = [c for c in cols_utiles if c in temp_df.columns]
            dfs.append(temp_df[cols_pres])
        except Exception:
            pass
    return pd.concat(dfs, ignore_index=True) if dfs else None


dfs_tous = []
for config in champs_selectionnes:
    code_csv = config['code_csv']
    fichier_combine = os.path.join(dossier_download, f"BIG_DATA_{code_csv}_{annee_saison}.csv")

    hist = None
    if os.path.exists(fichier_combine):
        try:
            hist = pd.read_csv(fichier_combine)
        except Exception:
            hist = None
    if hist is None:
        print(f"🌐 Téléchargement de l'historique pour {config['nom']}...")
        hist = telecharger_saisons(code_csv, saisons_historique)
        if hist is not None:
            try:
                hist.to_csv(fichier_combine, index=False)
            except Exception:
                pass

    print(f"🌐 Saison en cours ({config['nom']})...")
    courante = telecharger_saisons(code_csv, [saison_courante])

    morceaux = [x for x in (hist, courante) if x is not None]
    if morceaux:
        dfs_tous.append(pd.concat(morceaux, ignore_index=True))

if not dfs_tous:
    print("❌ Aucune donnée historique chargée.")
    sys.exit()


def parse_date(serie):
    s = serie.astype(str)
    d = pd.to_datetime(s, format='%d/%m/%Y', errors='coerce')
    manque = d.isna()
    if manque.any():
        d[manque] = pd.to_datetime(s[manque], format='%d/%m/%y', errors='coerce')
    return d


df = pd.concat(dfs_tous, ignore_index=True)
df['Date'] = parse_date(df['Date'])
df = df.dropna(subset=['Date', 'HomeTeam', 'AwayTeam', 'FTR', 'FTHG', 'FTAG'])
df = df.sort_values('Date', kind='stable').reset_index(drop=True)

df['Target_1X'] = (df['FTR'].isin(['H', 'D'])).astype(int)
df['Target_X2'] = (df['FTR'].isin(['A', 'D'])).astype(int)
df['Total_Goals'] = df['FTHG'] + df['FTAG']
df['Target_Over15'] = (df['Total_Goals'] > 1.5).astype(int)

# ---------------------------------------------------------
# FORME RÉCENTE : moyenne sur les N derniers matchs de chaque équipe (domicile + extérieur)
# Pour l'entraînement, on n'utilise que ce qui était connu AVANT le match (décalage d'un match).
# ---------------------------------------------------------
STATS = ['GF', 'GA', 'Pts', 'S', 'ST', 'C']          # buts pour/contre, points, tirs, tirs cadrés, corners
RCOLS = ['R_' + c for c in STATS]
PCOLS = ['P_' + c for c in STATS]


def construire_forme(data):
    data = data.copy()
    data['_id'] = np.arange(len(data))
    pts_h = np.where(data['FTR'] == 'H', 3, np.where(data['FTR'] == 'D', 1, 0))
    pts_a = np.where(data['FTR'] == 'A', 3, np.where(data['FTR'] == 'D', 1, 0))

    dom = pd.DataFrame({'_id': data['_id'], 'Date': data['Date'], 'Team': data['HomeTeam'], 'side': 'H',
                        'GF': data['FTHG'], 'GA': data['FTAG'], 'Pts': pts_h,
                        'S': data['HS'], 'ST': data['HST'], 'C': data['HC']})
    ext = pd.DataFrame({'_id': data['_id'], 'Date': data['Date'], 'Team': data['AwayTeam'], 'side': 'A',
                        'GF': data['FTAG'], 'GA': data['FTHG'], 'Pts': pts_a,
                        'S': data['AS'], 'ST': data['AST'], 'C': data['AC']})
    long = pd.concat([dom, ext], ignore_index=True)
    long = long.sort_values(['Team', 'Date', '_id'], kind='stable').reset_index(drop=True)

    roll = long.groupby('Team')[STATS].transform(lambda s: s.rolling(N_FORME, min_periods=3).mean())
    roll.columns = RCOLS
    long = pd.concat([long, roll], axis=1)

    avant = long.groupby('Team')[RCOLS].shift(1)
    avant.columns = PCOLS
    long = pd.concat([long, avant], axis=1)

    for cote_, prefixe in (('H', 'H_'), ('A', 'A_')):
        sub = long[long['side'] == cote_].set_index('_id')[PCOLS].copy()
        sub.columns = [prefixe + c for c in STATS]
        data = data.join(sub, on='_id')

    derniere_ligne = long.groupby('Team').tail(1).set_index('Team')[['Date'] + RCOLS]
    return data, derniere_ligne


df, derniere = construire_forme(df)
moyenne_forme = derniere[RCOLS].mean()

FORM_FEATS = ['H_' + c for c in STATS] + ['A_' + c for c in STATS]
features = FORM_FEATS + ['B365H', 'B365D', 'B365A']
TARGETS = ['Target_1X', 'Target_X2', 'Target_Over15']
df_clean = df[features + TARGETS].dropna()
X = df_clean[features]

# ---------------------------------------------------------
# RAPPROCHEMENT DES NOMS D'ÉQUIPES (The Odds API / API-Football  ->  football-data.co.uk)
# ---------------------------------------------------------
MOTS_VIDES = {'fc', 'cf', 'ac', 'as', 'rc', 'afc', 'sc', 'ssc', 'us', 'ud', 'cd', 'ca', 'rcd',
              'vfl', 'vfb', 'fsv', 'tsg', 'sv', 'fk', 'the', 'og', 'ogc', '1', '04', '05', '09', '96'}


def norm(nom):
    n = unicodedata.normalize('NFKD', str(nom)).encode('ascii', 'ignore').decode().lower()
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    return " ".join(m for m in n.split() if m not in MOTS_VIDES)


ALIAS = {
    "Brighton and Hove Albion": "Brighton", "Brighton & Hove Albion": "Brighton",
    "Manchester United": "Man United", "Manchester City": "Man City",
    "Newcastle United": "Newcastle", "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham", "Wolverhampton Wanderers": "Wolves",
    "Nottingham Forest": "Nott'm Forest", "Leeds United": "Leeds",
    "Leicester City": "Leicester", "Ipswich Town": "Ipswich", "Norwich City": "Norwich",
    "Luton Town": "Luton", "Sheffield United": "Sheffield United",
    "Atletico Madrid": "Ath Madrid", "Athletic Bilbao": "Ath Bilbao", "Athletic Club": "Ath Bilbao",
    "Real Betis": "Betis", "Real Sociedad": "Sociedad", "Celta Vigo": "Celta",
    "Rayo Vallecano": "Vallecano", "Deportivo Alaves": "Alaves", "Espanyol": "Espanol",
    "Real Valladolid": "Valladolid", "Real Oviedo": "Oviedo", "Sporting Gijon": "Sp Gijon",
    "Inter Milan": "Inter", "Internazionale": "Inter", "AC Milan": "Milan", "Hellas Verona": "Verona",
    "Paris Saint Germain": "Paris SG", "Paris Saint-Germain": "Paris SG",
    "Olympique Marseille": "Marseille", "Olympique Lyonnais": "Lyon", "Saint-Etienne": "St Etienne",
    "Borussia Dortmund": "Dortmund", "Bayer Leverkusen": "Leverkusen", "Bayer 04 Leverkusen": "Leverkusen",
    "Borussia Monchengladbach": "M'gladbach", "Borussia Mönchengladbach": "M'gladbach",
    "Eintracht Frankfurt": "Ein Frankfurt", "1. FC Köln": "FC Koln", "FC Koln": "FC Koln",
    "FC St. Pauli": "St Pauli", "Hamburger SV": "Hamburg", "1. FC Heidenheim": "Heidenheim",
    "1. FC Union Berlin": "Union Berlin", "FSV Mainz 05": "Mainz", "SC Freiburg": "Freiburg",
    "VfB Stuttgart": "Stuttgart", "VfL Wolfsburg": "Wolfsburg", "VfL Bochum": "Bochum",
    "TSG Hoffenheim": "Hoffenheim", "FC Augsburg": "Augsburg",
}
ALIAS_NORM = {norm(k): norm(v) for k, v in ALIAS.items()}

equipes_connues = set(df['HomeTeam'].dropna().unique()) | set(df['AwayTeam'].dropna().unique())
norm_vers_nom = {norm(t): t for t in equipes_connues}
_cache_noms = {}


def trouver_equipe(nom):
    """Retrouve le nom football-data.co.uk d'une équipe (None si introuvable)."""
    if nom in _cache_noms:
        return _cache_noms[nom]
    res = None
    if nom in equipes_connues:
        res = nom
    else:
        nn = norm(nom)
        nn = ALIAS_NORM.get(nn, nn)
        if nn in norm_vers_nom:
            res = norm_vers_nom[nn]
        else:
            sn = set(nn.split())
            cands = []
            for k in norm_vers_nom:
                sk = set(k.split())
                if sk and sn and (sk <= sn or sn <= sk):
                    cands.append(k)
            if cands:
                res = norm_vers_nom[min(cands, key=lambda k: abs(len(k) - len(nn)))]
            else:
                proche = difflib.get_close_matches(nn, list(norm_vers_nom), n=1, cutoff=0.78)
                if proche:
                    res = norm_vers_nom[proche[0]]
    _cache_noms[nom] = res
    return res


def similarite(a, b):
    na, nb = norm(a), norm(b)
    na = ALIAS_NORM.get(na, na)
    nb = ALIAS_NORM.get(nb, nb)
    if na == nb:
        return 1.0
    sa, sb = set(na.split()), set(nb.split())
    if sa and sb and (sa <= sb or sb <= sa):
        return 0.9
    return difflib.SequenceMatcher(None, na, nb).ratio()


equipes_inconnues = set()
equipes_signalees = set()


def info_forme(nom):
    """Retourne (valeurs de forme, connue?). Si l'équipe est inconnue : moyenne générale."""
    cle = trouver_equipe(nom)
    if cle is not None and cle in derniere.index:
        ligne = derniere.loc[cle]
        if (aujourdhui - ligne['Date'].date()).days <= 150 and ligne[RCOLS].notna().all():
            return ligne, True
    equipes_inconnues.add(nom)
    return moyenne_forme, False


# ---------------------------------------------------------
# ENTRAÎNEMENT
# ---------------------------------------------------------
print(f"\n🧠 Entraînement du modèle sur {len(df_clean)} matchs...")

if TEST_FIABILITE and len(df_clean) > 2000:
    coupe = int(len(df_clean) * 0.85)
    X_tr, X_te = X.iloc[:coupe], X.iloc[coupe:]
    y_tr, y_te = df_clean['Target_1X'].iloc[:coupe], df_clean['Target_1X'].iloc[coupe:]
    m_test = GradientBoostingClassifier(n_estimators=180, learning_rate=0.03, max_depth=4, random_state=42).fit(X_tr, y_tr)
    p_te = m_test.predict_proba(X_te)[:, 1]
    print(f"\n📏 Test sur les 15% de matchs les plus récents ({len(X_te)} matchs, jamais vus à l'entraînement) :")
    print(f"   Référence : 1X réussit dans {y_te.mean() * 100:.1f}% des matchs")
    for seuil in (0.55, 0.65, 0.75):
        masque = (p_te >= seuil)
        if masque.sum() >= 20:
            print(f"   Quand le modèle annonce ≥ {seuil * 100:.0f}% : {int(masque.sum())} matchs, réussite réelle {y_te[masque].mean() * 100:.1f}%")
    print("   (plus la réussite réelle est proche de la confiance annoncée, plus le modèle est fiable)")

model_1X = GradientBoostingClassifier(n_estimators=180, learning_rate=0.03, max_depth=4, random_state=42).fit(X, df_clean['Target_1X'])
model_X2 = GradientBoostingClassifier(n_estimators=180, learning_rate=0.03, max_depth=4, random_state=42).fit(X, df_clean['Target_X2'])
model_O15 = GradientBoostingClassifier(n_estimators=180, learning_rate=0.03, max_depth=4, random_state=42).fit(X, df_clean['Target_Over15'])
print("✅ Modèle prêt !")


# ---------------------------------------------------------
# API-FOOTBALL : blessures et compositions (optionnel)
# ---------------------------------------------------------
AF_BASE = "https://v3.football.api-sports.io"
cache_af = {}
_derniere_req_af = [0.0]
af_restant = [None]


def af_get(endpoint, params, cache=True):
    if not AF_KEY:
        return None
    url = f"{AF_BASE}/{endpoint}" + (("?" + urllib.parse.urlencode(params)) if params else "")
    if cache and url in cache_af:
        return cache_af[url]

    attente = AF_PAUSE - (time.time() - _derniere_req_af[0])
    if attente > 0:
        time.sleep(attente)
    _derniere_req_af[0] = time.time()

    req = urllib.request.Request(url, headers={'x-apisports-key': AF_KEY, 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            restant = r.headers.get('x-ratelimit-requests-remaining')
            if restant is not None:
                af_restant[0] = restant
            data = json.loads(r.read().decode('utf-8'))
    except Exception as e:
        print(f"   ⚠️ API-Football : {e}")
        return None

    if data.get('errors'):
        print(f"   ⚠️ API-Football : {data['errors']}")
        return None
    rep = data.get('response', [])
    if cache:
        cache_af[url] = rep
    return rep


def af_trouver_fixture(m):
    """Retrouve le match chez API-Football (une seule requête par ligue, mise en cache)."""
    ligue = LIGUES_AF.get(m['code_api'])
    if not ligue or not m.get('date'): ret
