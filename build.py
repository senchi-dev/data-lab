"""Genere un dashboard HTML autonome (World_Data_Dashboard.html) a partir des series FRED.
- Sidebar cliquable (une donnee = une entree)
- Graphique SVG interactif fait main (zero dependance externe)
- Granularite Mensuel / Trimestriel / Annuel (agregation cote client)
- Tooltip au survol : date + valeur exacte du point
Donnees mensuelles calees sur 2006 (debut des decisions BAM), embarquees en JSON.
"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from stats import compute_stats
from narratives import NARRATIVES

# Cle FRED : variable d'environnement (Vercel / GitHub Actions) sinon config locale (dev, gitignoree).
API_KEY = os.environ.get("FRED_API_KEY")
if not API_KEY:
    from config_api_fred import API_KEY  # dev local uniquement

ROOT = Path(__file__).resolve().parent
DATADIR = ROOT / "data"
MONIA_FILE = DATADIR / "MONIA.xlsx"
INFLATION_FILE = DATADIR / "Inflation_BAM.xlsx"
IPAI_FILE = DATADIR / "IPAI_BAM.xlsx"
OUTPUT_GAP_FILE = DATADIR / "Output_gap.csv"
DEPOTS_FILE = DATADIR / "Depots_terme.csv"
TAUX_DEB_FILE = DATADIR / "Taux_debiteurs.xlsx"   # ancien fichier 2010-2017
ICM_FILE = DATADIR / "ICM_HCP.csv"
DECISIONS_FILE = DATADIR / "Decisions_BAM.csv"
EMC_FILE = DATADIR / "EMC_series.xlsx"
IPIEM_FILE = DATADIR / "IPIEM_base2015.csv"
FIN_PUB_FILE = DATADIR / "Finances_publiques.csv"
# Exports recents (un ou plusieurs) : tout data/Taux_debiteurs_*.csv est fusionne automatiquement.

OBS = "https://api.stlouisfed.org/fred/series/observations"
DEBUT = "2006-01-01"

DEST = ROOT / "public"
FICHIER = DEST / "index.html"

BLEU, ORANGE, VERT = "#123e8b", "#e07b39", "#2e9e6b"   # BLEU = bleu BMCE Capital
ROUGE, VIOLET = "#c0392b", "#7c5cbf"

# id -> (nom, SECTION, groupe, unite, decimales, agg, courbes)
#   SECTION = grande categorie (bloc depliable de la sidebar). Pour ajouter d'autres
#   grandes categories (Sources nationales, Marches...), tagguer les nouvelles series
#   avec un nouveau nom de section : elles apparaitront dans leur propre bloc.
#   groupe  = sous-theme a l'interieur de la section.
#   agg     = "eop" (niveau fin de periode, pour les taux directeurs) ou "avg" (moyenne).
#   courbe  = (label, [ids FRED a raccorder], units, couleur).
INTL = "Environnement international"
CONFIG = [
    ("bce", "Taux directeur BCE", INTL, "Taux directeurs", "%", 2, "eop",
     [("Refi", ["ECBMRRFR"], "lin", BLEU), ("Depot", ["ECBDFR"], "lin", ORANGE)]),
    ("fed", "Taux directeur FED (cible)", INTL, "Taux directeurs", "%", 2, "eop",
     [("Cible Fed", ["DFEDTAR", "DFEDTARU"], "lin", BLEU)]),  # cible unique ->2008, puis fourchette haute
    ("infl_us", "Inflation US", INTL, "Inflation", "% sur 12 mois", 2, "avg",
     [("Inflation US", ["CPIAUCSL"], "pc1", BLEU)]),
    ("infl_ze", "Inflation zone euro", INTL, "Inflation", "% sur 12 mois", 2, "avg",
     [("Inflation ZE", ["CP0000EZ19M086NEST"], "pc1", BLEU)]),
    ("eurusd", "Change EUR / USD", INTL, "Marche & matieres premieres", "USD pour 1 EUR", 4, "avg",
     [("EUR/USD", ["DEXUSEU"], "lin", BLEU)]),
    ("brent", "Petrole Brent", INTL, "Marche & matieres premieres", "USD / baril", 1, "avg",
     [("Brent", ["POILBREUSDM"], "lin", BLEU)]),
    ("food", "Indice prix alimentaires mondiaux", INTL, "Marche & matieres premieres", "indice (2016=100)", 1, "avg",
     [("FAO/FMI", ["PFOODINDEXM"], "lin", BLEU)]),
    ("gepu", "Incertitude politique eco mondiale", INTL, "Risque", "indice GEPU", 0, "avg",
     [("GEPU", ["GEPUCURRENT"], "lin", BLEU)]),
]


def observations(series_id, units, agg):
    r = requests.get(OBS, params={
        "series_id": series_id, "api_key": API_KEY, "file_type": "json",
        "units": units, "frequency": "m", "aggregation_method": agg,
        "observation_start": DEBUT,
    }, timeout=30)
    r.raise_for_status()
    pts = {}
    for o in r.json()["observations"]:
        if o["value"] != ".":
            pts[o["date"][:7]] = round(float(o["value"]), 6)  # cle "YYYY-MM"
    return pts


def stitch(ids, units, agg):
    """Raccorde plusieurs series FRED en une seule (la derniere prime en cas de recouvrement)."""
    merged = {}
    for fid in ids:
        merged.update(observations(fid, units, agg))
    return merged


def load_monia():
    """MONIA quotidien (fichier BAM) -> moyenne mensuelle, en %. Cle 'YYYY-MM'."""
    df = pd.read_excel(MONIA_FILE)[["Date", "MONIA"]].dropna()
    df["ym"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m")
    moy = df.groupby("ym")["MONIA"].mean() * 100        # fraction -> pourcentage
    return {k: round(float(v), 6) for k, v in moy.items()}


def _num_fr(v):
    """Convertit un nombre ou une chaine FR ('\xa00,4') en float ; None si vide."""
    if pd.isna(v):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace("\xa0", "").replace(" ", "").replace(",", ".").strip()
    return float(s) if s else None


def load_output_gap():
    """Output gap construit (3 methodes BAM), CSV annuel -> {AAAA-07: valeur}."""
    import csv
    hp, fdp, mss = {}, {}, {}
    with open(OUTPUT_GAP_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ym = f"{row['annee']}-07"          # point place au milieu de l'annee
            if row.get("gap_hp"):
                hp[ym] = round(float(row["gap_hp"]), 2)
            if row.get("gap_fdp"):
                fdp[ym] = round(float(row["gap_fdp"]), 2)
            if row.get("gap_mss"):
                mss[ym] = round(float(row["gap_mss"]), 2)
    return hp, fdp, mss


def _hp_trend(y, lam):
    y = np.asarray(y, float); n = len(y)
    D = np.zeros((n - 2, n))
    for i in range(n - 2):
        D[i, i], D[i, i + 1], D[i, i + 2] = 1.0, -2.0, 1.0
    return np.linalg.solve(np.eye(n) + lam * D.T @ D, y)


def load_output_gap_q():
    """Output gap TRIMESTRIEL par filtre HP (lambda=1600) sur le PIB reel trimestriel (I4276, mod 725)."""
    j = requests.get("https://bds.hcp.ma/api/v1/indicators/I4276", timeout=20).json()
    def qidx(p):
        y, q = p.split("T"); return int(y) * 4 + int(q)
    lvl = {}
    for p in j["periods"]:
        cell = j["data"].get(f"725_{p}")
        if cell and cell["value"] not in (None, ""):
            lvl[p] = float(str(cell["value"]).replace("\xa0", "").replace(",", "."))
    order = sorted(lvl, key=qidx)
    logY = np.log([lvl[p] for p in order])
    gap = 100 * (logY - _hp_trend(logY, 1600))
    mq = {"1": "02", "2": "05", "3": "08", "4": "11"}
    out = {}
    for i, p in enumerate(order):
        y, q = p.split("T")
        out[f"{y}-{mq[q]}"] = round(float(gap[i]), 2)
    return out


def load_ipai():
    """Indice des prix des actifs immobiliers (fichier BAM/ANCFCC), trimestriel, base 100=T1 2006.
    Renvoie (global, residentiel) : dicts 'YYYY-MM' (trimestre au mois median)."""
    import re
    df = pd.read_excel(IPAI_FILE, sheet_name="Global", header=1)
    df.columns = [str(c).strip() for c in df.columns]   # noms de colonnes avec espaces parasites
    df = df.rename(columns={df.columns[0]: "Trim"})
    mq = {1: "02", 2: "05", 3: "08", 4: "11"}
    glob, resid = {}, {}
    for _, r in df.iterrows():
        m = re.match(r"\s*T\s*([1-4])[-\s]*(\d{4})", str(r["Trim"]))
        if not m:
            continue
        q, y = int(m.group(1)), int(m.group(2))
        ym = f"{y}-{mq[q]}"
        if pd.notna(r.get("Global")):
            glob[ym] = round(float(r["Global"]), 2)
        if pd.notna(r.get("Résidentiel")):
            resid[ym] = round(float(r["Résidentiel"]), 2)
    return glob, resid


def load_hcp_pib():
    """PIB reel trimestriel (HCP API, I4276, modalite 725) -> croissance en glissement annuel (%).
    Cle de sortie 'YYYY-MM' (trimestre place a son mois median)."""
    j = requests.get("https://bds.hcp.ma/api/v1/indicators/I4276", timeout=20).json()
    niv = {}
    for p in j["periods"]:                       # p = 'YYYYTQ'
        cell = j["data"].get(f"725_{p}")
        if cell and cell["value"] not in (None, ""):
            niv[p] = float(str(cell["value"]).replace("\xa0", "").replace(",", "."))
    mois_q = {"1": "02", "2": "05", "3": "08", "4": "11"}   # milieu de trimestre
    croissance = {}
    for p in niv:
        y, q = p.split("T")
        prev = f"{int(y) - 1}T{q}"               # meme trimestre, annee precedente
        if prev in niv and niv[prev]:
            g = (niv[p] / niv[prev] - 1) * 100
            croissance[f"{y}-{mois_q[q]}"] = round(g, 2)
    return croissance


def load_inflation_bam():
    """Inflation globale et sous-jacente (fichier BAM), mensuel, deja en % YoY."""
    df = pd.read_excel(INFLATION_FILE)
    df.columns = ["Mois", "glob", "core"]
    df["ym"] = pd.to_datetime(df["Mois"]).dt.strftime("%Y-%m")
    glob, core = {}, {}
    for r in df.itertuples():
        g, c = _num_fr(r.glob), _num_fr(r.core)
        if g is not None:
            glob[r.ym] = round(g, 3)
        if c is not None:
            core[r.ym] = round(c, 3)
    return glob, core


_MOIS_FR = {"janvier": "01", "février": "02", "fevrier": "02", "mars": "03", "avril": "04",
            "mai": "05", "juin": "06", "juillet": "07", "août": "08", "aout": "08",
            "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12", "decembre": "12"}


def load_depots():
    """Taux moyens ponderes des depots a terme (fichier BAM), mensuel, en %.
    Renvoie (6 mois, 12 mois) : dicts 'YYYY-MM'. Fichier separateur ';', mois FR, valeurs '2,51 %'."""
    import csv
    d6, d12 = {}, {}
    with open(DEPOTS_FILE, encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter=";"))
    for row in rows:
        if len(row) < 3 or "-" not in row[0]:      # saute titre et en-tete
            continue
        mois, an = row[0].split("-")
        mm = _MOIS_FR.get(mois.strip().lower())
        if not mm:
            continue
        ym = f"{an.strip()}-{mm}"
        v6 = _num_fr(row[1].replace("%", ""))
        v12 = _num_fr(row[2].replace("%", ""))
        if v6 is not None:
            d6[ym] = round(v6, 2)
        if v12 is not None:
            d12[ym] = round(v12, 2)
    return d6, d12


def load_icm():
    """Indice de Confiance des Menages (HCP, Enquete Nationale de Conjoncture aupres des Menages).
    Fichier de donnees officiel HCP (2008 T1 -> 2025 T2) + 4 trimestres recents des notes trimestrielles.
    Trimestriel, echelle 0-200 (100 = neutre). Cle 'YYYY-MM' au mois median du trimestre."""
    import csv, re
    mq = {"1": "02", "2": "05", "3": "08", "4": "11"}
    out = {}
    with open(ICM_FILE, encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 5:
                continue
            m = re.match(r"\s*([1-4])T\s*(\d{4})", row[3])   # "1T 2008"
            if not m:
                continue
            v = _num_fr(row[4])
            if v is not None:
                out[f"{m.group(2)}-{mq[m.group(1)]}"] = round(v, 1)
    # Trimestres posterieurs au fichier officiel, releves dans les communiques trimestriels HCP :
    recents = {"2025-08": 53.6, "2025-11": 57.6, "2026-02": 64.4, "2026-05": 60.1}
    out.update(recents)
    return out


def load_emc():
    """Enquete mensuelle de conjoncture industrie (BAM). Fichier de series propre (soldes d'opinion).
    Renvoie (tuc, soldes) : tuc = {'YYYY-MM': taux}, soldes = {cle: {'YYYY-MM': solde}} pour la branche Global.
    Mensuel 2010-01 -> 2026-06."""
    tuc_df = pd.read_excel(EMC_FILE, sheet_name="TUC")
    tuc_df.columns = ["Mois", "TUC"]
    tuc_df = tuc_df.dropna()
    tuc = {pd.to_datetime(r.Mois).strftime("%Y-%m"): round(float(r.TUC), 1) for r in tuc_df.itertuples()}

    df = pd.read_excel(EMC_FILE, sheet_name="indicateur par branche")
    df.columns = ["Mois", "Branche", "Indicateur", "Solde"]
    g = df[df["Branche"] == "Global"].dropna(subset=["Indicateur", "Solde"])
    libelles = {
        "prod":   "Evolution de la production par rapport au mois précédent",
        "ventes": "Evolution des ventes par rapport au mois précédent",
        "cmd":    "Niveau des carnets de commandes par rapport au mois précédent",
        "prix":   "Evolution des prix des produits finis par rapport au mois précédent",
    }
    soldes = {}
    for cle, lab in libelles.items():
        sub = g[g["Indicateur"] == lab]
        soldes[cle] = {pd.to_datetime(r.Mois).strftime("%Y-%m"): round(float(r.Solde), 1) for r in sub.itertuples()}
    return tuc, soldes


def _hcp_num(v):
    return float(str(v).replace("\xa0", "").replace(" ", "").replace(",", "."))


def load_finances_publiques():
    """Finances publiques du Trésor (HCP Annuaires statistiques, assemblés), annuel 2006-2024, en milliards DH.
    Renvoie {cle_metrique: {'YYYY-07': valeur}} pour recettes, depenses, deficit, dette."""
    import csv
    out = {"recettes": {}, "depenses": {}, "deficit": {}, "dette": {}}
    with open(FIN_PUB_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ym = f"{row['annee']}-07"
            for k in out:
                if row.get(k) not in (None, ""):
                    out[k][ym] = round(float(row[k]), 1)
    return out


def load_ipiem():
    """Indice de la production industrielle, energetique et miniere (IPIEM, HCP, base 2015), trimestriel.
    Assemble a partir des notes trimestrielles HCP (docx). 3 secteurs. Cle 'YYYY-MM' (mois median du trimestre).
    Renvoie {label: {cle: valeur}}."""
    import csv
    out = {"Manufacturières": {}, "Électricité": {}, "Extractives": {}}
    with open(IPIEM_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            p = row["periode"]
            if row.get("manufacturieres"):
                out["Manufacturières"][p] = round(float(row["manufacturieres"]), 1)
            if row.get("electricite"):
                out["Électricité"][p] = round(float(row["electricite"]), 1)
            if row.get("extractives"):
                out["Extractives"][p] = round(float(row["extractives"]), 1)
    return out


def load_ipp():
    """Indice des prix a la production industrielle (IPP, HCP I1418, base 2010), annuel 1998-2021.
    4 secteurs agreges. Cle 'YYYY-07' (mi-annee). Renvoie {label: {cle: valeur}}."""
    j = requests.get("https://bds.hcp.ma/api/v1/indicators/I1418", timeout=25).json()
    secteurs = {"Manufacturières": "758", "Électricité": "759",
                "Extractives": "757", "Eau": "760"}
    out = {lab: {} for lab in secteurs}
    for p in j["periods"]:                       # 'YYYY'
        for lab, mid in secteurs.items():
            c = j["data"].get(f"{mid}_{p}")
            if c and c["value"] not in (None, ""):
                out[lab][f"{p}-07"] = round(_hcp_num(c["value"]), 1)
    return out


def load_directeur():
    """Taux directeur BAM (Historique des decisions du Conseil). CSV date,taux -> serie mensuelle en escalier
    (le taux prevaut jusqu'a la decision suivante), calee jusqu'au mois courant. Cle 'YYYY-MM'."""
    import csv
    from datetime import datetime
    dec_by_ym = {}
    with open(DECISIONS_FILE, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            dec_by_ym[r["date"][:7]] = float(r["taux"])   # derniere decision du mois si plusieurs
    first = min(dec_by_ym)
    now = datetime.now()
    y, m = int(first[:4]), int(first[5:7])
    cur, out = None, {}
    while (y, m) <= (now.year, now.month):
        ym = f"{y:04d}-{m:02d}"
        if ym in dec_by_ym:
            cur = dec_by_ym[ym]
        if cur is not None:
            out[ym] = round(cur, 2)
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def load_marche_travail():
    """Taux de chomage (I4249) et taux d'activite (I4250), agregat National/Ensemble, trimestriel 2006-2025 (HCP, ENE).
    Cle 'YYYY-MM' au mois median du trimestre."""
    mq = {"1": "02", "2": "05", "3": "08", "4": "11"}
    def qserie(code, key):
        j = requests.get(f"https://bds.hcp.ma/api/v1/indicators/{code}", timeout=25).json()
        out = {}
        for p in j["periods"]:                     # 'YYYYTQ'
            c = j["data"].get(f"{key}_{p}")
            if c and c["value"] not in (None, ""):
                y, q = p.split("T")
                out[f"{y}-{mq[q]}"] = round(_hcp_num(c["value"]), 1)
        return out
    return qserie("I4249", "173.176"), qserie("I4250", "181.184")   # chomage, activite (age Ensemble . milieu National)


def load_commerce_ext():
    """Exports (I4183/1370) et imports (I4185/1380), Total, mensuel 2014-2025, source Office des Changes.
    Convertis en milliards de DH. Renvoie (exports, imports, solde commercial)."""
    def total(code, mid):
        j = requests.get(f"https://bds.hcp.ma/api/v1/indicators/{code}", timeout=25).json()
        out = {}
        for p in j["periods"]:                     # 'YYYYMn'
            c = j["data"].get(f"{mid}_{p}")
            if c and c["value"] not in (None, ""):
                y, m = p.split("M")
                out[f"{y}-{int(m):02d}"] = round(_hcp_num(c["value"]) / 1000, 2)   # millions -> milliards
        return out
    exp, imp = total("I4183", "1370"), total("I4185", "1380")
    solde = {k: round(exp[k] - imp[k], 2) for k in exp if k in imp}
    return exp, imp, solde


def load_cereales():
    """Production cerealiere nationale (I3824, Min. Agriculture), par campagne annuelle, en millions de quintaux.
    Region nationale = 4690. Cle 'YYYY-05' (annee de recolte, 2e annee de la campagne)."""
    j = requests.get("https://bds.hcp.ma/api/v1/indicators/I3824", timeout=25).json()
    types = {"Total": "4617", "Blé dur": "4613", "Blé tendre": "4614", "Orge": "4615"}
    out = {lab: {} for lab in types}
    for p in j["periods"]:                          # '2015-2016'
        an2 = p.split("-")[1]
        for lab, cid in types.items():
            c = j["data"].get(f"{cid}.4690_{p}")
            if c and c["value"] not in (None, ""):
                out[lab][f"{an2}-05"] = round(_hcp_num(c["value"]) / 1000, 1)   # milliers -> millions quintaux
    return out


_DEB_MQ = {"T1": "02", "T2": "05", "T3": "08", "T4": "11"}   # trimestre -> mois median
_DEB_LIGNES = {                                # libelle fichier -> cle serie (les 2 formats)
    "Taux global": "global", "Taux débiteur": "global",
    "Comptes débiteurs et crédits de trésorerie": "tresorerie",
    "Crédits à l'équipement": "equipement",
    "Crédits immobiliers": "immobilier",
    "Crédits à la consommation": "consommation",
}


def _load_deb_xlsx():
    """Ancien fichier BAM (xlsx), trimestriel 2010-2017, layout horizontal."""
    df = pd.read_excel(TAUX_DEB_FILE, header=None)
    annees = pd.to_numeric(df.iloc[8, 1:], errors="coerce").ffill()   # 2010 sur T1, propage sur T2-T4
    trims = df.iloc[9, 1:]
    out = {v: {} for v in set(_DEB_LIGNES.values())}
    for i in range(10, df.shape[0]):
        key = _DEB_LIGNES.get(str(df.iloc[i, 0]).strip())
        if not key:
            continue
        for c in range(1, df.shape[1]):
            an, tr = annees.get(c), trims.get(c)
            if pd.isna(an) or pd.isna(tr) or str(tr).strip() not in _DEB_MQ:
                continue
            if pd.notna(df.iloc[i, c]):
                out[key][f"{int(an)}-{_DEB_MQ[str(tr).strip()]}"] = round(float(df.iloc[i, c]), 2)
    return out


def _load_deb_recent(path):
    """Export BAM recent (csv, sep ';'), trimestriel, layout horizontal. Derniere colonne = delta, ignoree."""
    import csv
    with open(path, encoding="utf-8") as f:
        rows = [r for r in csv.reader(f, delimiter=";") if any(x.strip() for x in r)]
    # rows[0]=titre, rows[1]=sous-titre, rows[2]=annees, rows[3]=trimestres, rows[4:]=data
    annees, prev = [], None
    for cell in rows[2]:
        prev = cell.strip() or prev
        annees.append(prev)
    trims = [c.strip() for c in rows[3]]
    out = {v: {} for v in set(_DEB_LIGNES.values())}
    for r in rows[4:]:
        key = _DEB_LIGNES.get(r[0].strip().strip('"'))
        if not key:
            continue
        for c in range(1, len(r)):
            if c >= len(trims) or trims[c] not in _DEB_MQ or not annees[c]:
                continue
            v = _num_fr(r[c])
            if v is not None:
                out[key][f"{annees[c]}-{_DEB_MQ[trims[c]]}"] = round(v, 2)
    return out


def load_taux_debiteurs():
    """Taux debiteurs (enquete trimestrielle BAM). Fusionne l'ancien fichier (2010-2017) et tous les
    exports recents data/Taux_debiteurs_*.csv (chronologie assemblee). Renvoie {cle_serie: {'YYYY-MM': taux}}."""
    out = _load_deb_xlsx()
    for csv_path in sorted(DATADIR.glob("Taux_debiteurs_*.csv")):
        for k, serie in _load_deb_recent(csv_path).items():
            out.setdefault(k, {}).update(serie)          # les exports recents priment sur recouvrement
    return out


# Note affichee sous chaque graphe, specifique a la serie.
NOTES = {
    "directeur": "Taux directeur de Bank Al-Maghrib, le taux auquel elle prête aux banques : c'est l'instrument de la politique monétaire et la variable que le modèle cherche à anticiper. Série en escalier reconstruite depuis l'historique des décisions du Conseil (une réunion par trimestre) ; entre deux décisions, le taux reste inchangé. La décision se lit dans les variations : hausse, baisse, ou statu quo.",
    "bce": "Taux directeur BCE, niveau en fin de période (décision réelle, pas de 0,25 %). Refi (haut) vs dépôt (bas, devenu le vrai pilote depuis 2014).",
    "fed": "Cible de la Fed en fin de période. Cible unique jusqu'à déc. 2008, puis borne haute de la fourchette.",
    "infl_us": "Inflation US en glissement annuel (variation sur 12 mois de l'IPC).",
    "infl_ze": "Inflation de la zone euro en glissement annuel (indice HICP).",
    "eurusd": "Taux de change EUR/USD (dollars pour 1 euro), moyenne du mois.",
    "brent": "Prix du baril de Brent en dollars, moyenne du mois. Référence de la facture pétrolière marocaine.",
    "food": "Indice FMI des prix alimentaires mondiaux (2016 = 100), moyenne du mois.",
    "gepu": "Indice mondial d'incertitude de politique économique (GEPU), moyenne du mois. Proxy du critère « incertitude internationale » de BAM.",
    "monia": "Taux interbancaire marocain au jour le jour, moyenne du mois. Il reste collé au taux directeur BAM ; ses écarts signalent des tensions de liquidité.",
    "inflation": "Inflation marocaine en glissement annuel. Globale (tout le panier) vs sous-jacente (hors alimentaire et énergie volatils = la tendance de fond).",
    "pib": "Croissance du PIB réel marocain en glissement annuel (volume chaîné, corrigé des variations saisonnières).",
    "output_gap": "Écart entre PIB observé et potentiel, estimé par les 3 méthodes de BAM (HP, fonction de production, semi-structurel). Estimation, pas mesure : fiez-vous au signe et à la direction, pas au niveau exact ; les derniers points sont incertains (biais de fin d'échantillon).",
    "output_gap_q": "Output gap trimestriel par filtre HP (λ=1600) sur le PIB réel. Plus réactif que la version annuelle, mais fortement révisé sur les tout derniers trimestres.",
    "ipai": "Indice des prix des actifs immobiliers (base 100 = T1 2006). Global vs résidentiel. Quasi plat sur 20 ans → prix réels en baisse.",
    "m3": "Agrégats monétaires M1/M2/M3 en milliards de dirhams (annuel). M3 (masse monétaire large) est le plus suivi ; une croissance excessive précède l'inflation à moyen terme.",
    "capi": "Capitalisation boursière totale de la Bourse de Casablanca (annuel, milliards DH). Valeur du marché actions et canal d'effet de richesse.",
    "depots": "Taux moyen pondéré des dépôts à terme (comptes et bons de caisse) à 6 et 12 mois, mensuel. Taux créditeurs offerts aux épargnants ; ils suivent le taux directeur BAM avec retard et mesurent la transmission de la politique monétaire au passif des banques.",
    "debiteurs": "Taux débiteurs (enquête trimestrielle BAM) : le taux que les banques facturent sur les nouveaux crédits, taux global et par usage (trésorerie, équipement, immobilier, consommation). Cœur de la transmission de la politique monétaire à l'économie réelle. Couverture trimestrielle continue 2010 à 2026 (plusieurs exports BAM assemblés).",
    "icm": "Indice de Confiance des Ménages (HCP, enquête nationale de conjoncture). Moyenne des soldes d'opinion des ménages sur leur niveau de vie, leurs finances, le chômage et l'opportunité d'achat. Échelle 0 à 200, où 100 = neutre : en dessous, le pessimisme domine. Source : fichier de données HCP (depuis 2008) prolongé par les communiqués trimestriels.",
    "travail": "Taux de chômage et taux d'activité au niveau national, ensemble des âges (HCP, Enquête Nationale sur l'Emploi), trimestriel. Le taux d'activité est la part de la population en âge de travailler qui est active (occupée ou au chômage) ; il baisse structurellement au Maroc. Le chômage est fortement saisonnier et sensible aux campagnes agricoles.",
    "commerce": "Exportations, importations et solde commercial (biens uniquement), mensuel, en milliards de dirhams (source Office des Changes via API HCP). C'est la balance commerciale, principale composante des comptes extérieurs. Le solde est structurellement déficitaire ; il ne couvre pas les services, transferts MRE et flux financiers de la balance des paiements complète.",
    "cereales": "Production céréalière nationale par campagne agricole (Ministère de l'Agriculture via API HCP), en millions de quintaux. Total et par type (blé tendre, blé dur, orge). Extrêmement volatile selon la pluviométrie : une mauvaise campagne fait plonger la croissance du PIB agricole, donc du PIB global. La composante hors céréalière n'est pas publiée séparément.",
    "tuc": "Taux d'utilisation des capacités de production dans l'industrie (enquête mensuelle de conjoncture BAM), mensuel. Part des capacités effectivement utilisées : plus il est haut, plus l'appareil productif tourne à plein. Baromètre d'activité réelle très suivi, proxy des tensions sur l'offre et de l'écart de production.",
    "conj_ind": "Soldes d'opinion de l'enquête mensuelle de conjoncture BAM (industrie, branche Global). Un solde = % d'entreprises signalant une hausse moins % signalant une baisse : positif = expansion, négatif = contraction. Production, ventes et carnets de commandes mesurent l'activité ; les prix des produits finis sont un signal avancé d'inflation côté offre.",
    "ipp": "Indice des prix à la production industrielle, énergétique et minière (IPP, HCP, base 100 = 2010), annuel, par secteur. Mesure le prix de sortie d'usine, un signal d'inflation en amont (les prix producteurs précèdent souvent les prix à la consommation). Série disponible de 1998 à 2021 sur cette base ; pour un suivi frais et mensuel, voir l'IPP base 2018 (mensuel, jusqu'en 2026) non intégré ici.",
    "ipiem": "Indice de la production industrielle, énergétique et minière (IPIEM, HCP, base 100 = 2015), trimestriel, par secteur (manufacturières, électricité, extractives). Mesure le VOLUME produit, pas les prix. Assemblé à partir des notes trimestrielles HCP ; couverture continue T1 2020 à T3 2025. À ne pas confondre avec l'IPP (prix). Baromètre d'activité industrielle réelle, utile pour lire le cycle et l'écart de production.",
    "finances": "Recettes et dépenses ordinaires du Trésor (source Ministère des Finances), annuel en milliards de DH. Les recettes ordinaires (fiscales + non fiscales) financent le fonctionnement de l'État ; leur écart avec les dépenses donne le solde ordinaire. Série 2006-2023 assemblée depuis les annuaires HCP, 2024 et 2025 tirés du bulletin réalisé de la TGR (le 2024 provisoire des annuaires a été corrigé par le réalisé).",
    "deficit": "Déficit budgétaire global du Trésor et charge de la dette (intérêts), annuel en milliards de DH. Le déficit global inclut les dépenses d'investissement et les comptes spéciaux, il ne se résume donc pas à recettes moins dépenses ordinaires. C'est l'indicateur clé du besoin d'emprunt de l'État. Source : annuaires HCP (2006-2023) et bulletin réalisé de la TGR (2024-2025).",
}


def _hcp(code):
    return requests.get(f"https://bds.hcp.ma/api/v1/indicators/{code}", timeout=20).json()


def _hcp_annual_series(j, mid, div=1.0, dec=1):
    """Extrait une modalite d'un indicateur HCP annuel -> {'AAAA-07': valeur} (mid-year)."""
    out = {}
    for p in j["periods"]:                       # p = 'AAAA'
        cell = j["data"].get(f"{mid}_{p}")
        if cell and cell["value"] not in (None, ""):
            v = float(str(cell["value"]).replace("\xa0", "").replace(",", ".")) / div
            out[f"{p}-07"] = round(v, dec)
    return out


def load_hcp_aggregates():
    """Agregats monetaires M1/M2/M3 (HCP I1450, source BAM), annuel, en milliards de DH."""
    j = _hcp("I1450")
    return (_hcp_annual_series(j, 1432, 1000, 0),   # M1
            _hcp_annual_series(j, 1434, 1000, 0),   # M2
            _hcp_annual_series(j, 1436, 1000, 0))   # M3


def load_hcp_market_cap():
    """Capitalisation boursiere totale (HCP I1887, Bourse de Casablanca), annuel, milliards de DH."""
    return _hcp_annual_series(_hcp("I1887"), 1496, 1000, 0)


def build_data():
    data = {}
    for sid, nom, section, groupe, unite, dec, agg, courbes in CONFIG:
        lignes = []
        for label, fids, units, couleur in courbes:
            pts = stitch(fids, units, agg)
            lignes.append({"label": label, "color": couleur, "points": pts})
            print(f"{nom:<30} {label:<12} {len(pts)} mois  ({'+'.join(fids)}, {agg})")
        data[sid] = {"name": nom, "section": section, "group": groupe, "unit": unite,
                     "decimals": dec, "agg": agg, "freq": "M", "lines": lignes}

    # --- Cible : taux directeur / decisions BAM ---
    directeur = load_directeur()
    data["directeur"] = {"name": "Taux directeur BAM (décisions du Conseil)", "section": "Décision de politique monétaire",
                         "group": "Cible", "unit": "%", "decimals": 2, "agg": "eop", "freq": "M",
                         "lines": [{"label": "Taux directeur", "color": ROUGE, "points": directeur}]}
    print(f"{'Taux directeur BAM':<30} {'directeur':<12} {len(directeur)} mois  (Historique des décisions BAM)")

    # --- Sources nationales (fichiers locaux BAM) ---
    monia = load_monia()
    data["monia"] = {"name": "MONIA (interbancaire j/j)", "section": "Sources nationales",
                     "group": "Marché monétaire", "unit": "%", "decimals": 2, "agg": "avg", "freq": "M",
                     "lines": [{"label": "MONIA", "color": BLEU, "points": monia}]}
    print(f"{'MONIA (interbancaire)':<30} {'MONIA':<12} {len(monia)} mois  (fichier BAM, avg)")

    glob, core = load_inflation_bam()
    data["inflation"] = {"name": "Inflation globale & sous-jacente", "section": "Données économiques nationales",
                         "group": "Prix", "unit": "% sur 12 mois", "decimals": 2, "agg": "avg", "freq": "M",
                         "lines": [{"label": "Inflation globale", "color": BLEU, "points": glob},
                                   {"label": "Sous-jacente (core)", "color": ORANGE, "points": core}]}
    print(f"{'Inflation globale + core':<30} {'2 series':<12} {len(glob)}/{len(core)} mois  (fichier BAM, avg)")

    pib = load_hcp_pib()
    data["pib"] = {"name": "Croissance du PIB (g.a.)", "section": "Données économiques nationales",
                   "group": "Comptes nationaux", "unit": "% sur un an", "decimals": 1, "agg": "avg", "freq": "Q",
                   "lines": [{"label": "PIB réel (volume, CVS)", "color": BLEU, "points": pib}]}
    print(f"{'Croissance PIB (HCP)':<30} {'PIB':<12} {len(pib)} trim.  (API HCP I4276, g.a.)")

    hp, fdp, mss = load_output_gap()
    data["output_gap"] = {"name": "Output gap (3 méthodes)", "section": "Données économiques nationales",
                          "group": "Comptes nationaux", "unit": "% du PIB potentiel", "decimals": 1, "agg": "avg", "freq": "A",
                          "lines": [{"label": "Filtre HP", "color": BLEU, "points": hp},
                                    {"label": "Fonction de production", "color": ORANGE, "points": fdp},
                                    {"label": "Semi-structurel", "color": VERT, "points": mss}]}
    print(f"{'Output gap construit':<30} {'3 series':<12} {len(hp)}/{len(fdp)}/{len(mss)} ans  (HP + FDP + semi-structurel)")

    ipai_g, ipai_r = load_ipai()
    data["ipai"] = {"name": "Prix des actifs immobiliers (IPAI)", "section": "Données économiques nationales",
                    "group": "Marché immobilier", "unit": "indice (T1 2006 = 100)", "decimals": 1, "agg": "avg", "freq": "Q",
                    "lines": [{"label": "IPAI global", "color": BLEU, "points": ipai_g},
                              {"label": "Résidentiel", "color": ORANGE, "points": ipai_r}]}
    print(f"{'IPAI immobilier':<30} {'2 series':<12} {len(ipai_g)} trim.  (fichier BAM/ANCFCC)")

    gapq = load_output_gap_q()
    data["output_gap_q"] = {"name": "Output gap trimestriel (HP)", "section": "Données économiques nationales",
                            "group": "Comptes nationaux", "unit": "% du PIB potentiel", "decimals": 1, "agg": "avg", "freq": "Q",
                            "lines": [{"label": "HP trimestriel (λ=1600)", "color": BLEU, "points": gapq}]}
    print(f"{'Output gap trimestriel':<30} {'HP':<12} {len(gapq)} trim.  (I4276, lambda=1600)")

    m1, m2, m3 = load_hcp_aggregates()
    data["m3"] = {"name": "Agrégats monétaires (M1, M2, M3)", "section": "Données monétaires et financières nationales",
                  "group": "Statistiques monétaires", "unit": "milliards DH", "decimals": 0, "agg": "avg", "freq": "A",
                  "lines": [{"label": "M3", "color": VERT, "points": m3},
                            {"label": "M2", "color": ORANGE, "points": m2},
                            {"label": "M1", "color": BLEU, "points": m1}]}
    print(f"{'Agrégats M1/M2/M3 (HCP)':<30} {'3 series':<12} {len(m3)} ans  (API HCP I1450)")

    capi = load_hcp_market_cap()
    data["capi"] = {"name": "Capitalisation boursière (total)", "section": "Données monétaires et financières nationales",
                    "group": "Marchés des capitaux", "unit": "milliards DH", "decimals": 0, "agg": "avg", "freq": "A",
                    "lines": [{"label": "Capitalisation", "color": BLEU, "points": capi}]}
    print(f"{'Capitalisation boursière (HCP)':<30} {'total':<12} {len(capi)} ans  (API HCP I1887)")

    d6, d12 = load_depots()
    data["depots"] = {"name": "Taux des dépôts à terme (6 et 12 mois)", "section": "Données monétaires et financières nationales",
                      "group": "Taux créditeurs", "unit": "%", "decimals": 2, "agg": "avg", "freq": "M",
                      "lines": [{"label": "Dépôts à 12 mois", "color": BLEU, "points": d12},
                                {"label": "Dépôts à 6 mois", "color": ORANGE, "points": d6}]}
    print(f"{'Dépôts à terme (BAM)':<30} {'2 series':<12} {len(d6)}/{len(d12)} mois  (fichier BAM, avg)")

    td = load_taux_debiteurs()
    data["debiteurs"] = {"name": "Taux débiteurs (par type de crédit)", "section": "Données monétaires et financières nationales",
                         "group": "Taux débiteurs", "unit": "%", "decimals": 2, "agg": "avg", "freq": "Q",
                         "lines": [{"label": "Taux global", "color": BLEU, "points": td["global"]},
                                   {"label": "Trésorerie", "color": ORANGE, "points": td["tresorerie"]},
                                   {"label": "Équipement", "color": VERT, "points": td["equipement"]},
                                   {"label": "Immobilier", "color": VIOLET, "points": td["immobilier"]},
                                   {"label": "Consommation", "color": ROUGE, "points": td["consommation"]}]}
    print(f"{'Taux débiteurs (BAM)':<30} {'5 series':<12} {len(td['global'])} trim.  (enquête trim. BAM, 2010-2026 continu)")

    icm = load_icm()
    data["icm"] = {"name": "Confiance des ménages (ICM)", "section": "Données économiques nationales",
                   "group": "Enquêtes de conjoncture", "unit": "indice (100 = neutre)", "decimals": 1, "agg": "avg", "freq": "Q",
                   "lines": [{"label": "ICM", "color": BLEU, "points": icm}]}
    print(f"{'Confiance ménages (ICM)':<30} {'ICM':<12} {len(icm)} trim.  (fichier HCP + notes trim.)")

    chom, act = load_marche_travail()
    data["travail"] = {"name": "Marché du travail (chômage & activité)", "section": "Données économiques nationales",
                       "group": "Marché du travail", "unit": "% de la population", "decimals": 1, "agg": "avg", "freq": "Q",
                       "lines": [{"label": "Taux de chômage", "color": ROUGE, "points": chom},
                                 {"label": "Taux d'activité", "color": BLEU, "points": act}]}
    print(f"{'Marché du travail (HCP)':<30} {'2 series':<12} {len(chom)} trim.  (API HCP I4249/I4250)")

    exp, imp, solde = load_commerce_ext()
    data["commerce"] = {"name": "Commerce extérieur (biens)", "section": "Données économiques nationales",
                        "group": "Comptes extérieurs", "unit": "milliards DH / mois", "decimals": 1, "agg": "avg", "freq": "M",
                        "lines": [{"label": "Solde commercial", "color": ROUGE, "points": solde},
                                  {"label": "Exportations", "color": VERT, "points": exp},
                                  {"label": "Importations", "color": ORANGE, "points": imp}]}
    print(f"{'Commerce extérieur (HCP)':<30} {'3 series':<12} {len(exp)} mois  (API HCP I4183/I4185, Office des Changes)")

    cer = load_cereales()
    data["cereales"] = {"name": "Production céréalière", "section": "Données économiques nationales",
                        "group": "Agriculture", "unit": "millions de quintaux", "decimals": 1, "agg": "avg", "freq": "A",
                        "lines": [{"label": "Total céréales", "color": BLEU, "points": cer["Total"]},
                                  {"label": "Blé tendre", "color": ORANGE, "points": cer["Blé tendre"]},
                                  {"label": "Blé dur", "color": VERT, "points": cer["Blé dur"]},
                                  {"label": "Orge", "color": ROUGE, "points": cer["Orge"]}]}
    print(f"{'Production céréalière (HCP)':<30} {'4 series':<12} {len(cer['Total'])} camp.  (API HCP I3824, Min. Agriculture)")

    tuc, soldes = load_emc()
    data["tuc"] = {"name": "Taux d'utilisation des capacités (TUC)", "section": "Données économiques nationales",
                   "group": "Conjoncture industrielle", "unit": "% des capacités", "decimals": 1, "agg": "avg", "freq": "M",
                   "lines": [{"label": "TUC industrie", "color": BLEU, "points": tuc}]}
    print(f"{'TUC industrie (BAM EMC)':<30} {'TUC':<12} {len(tuc)} mois  (fichier BAM EMC)")

    data["conj_ind"] = {"name": "Conjoncture industrielle (soldes d'opinion)", "section": "Données économiques nationales",
                        "group": "Conjoncture industrielle", "unit": "solde d'opinion", "decimals": 1, "agg": "avg", "freq": "M",
                        "lines": [{"label": "Production", "color": BLEU, "points": soldes["prod"]},
                                  {"label": "Ventes", "color": ORANGE, "points": soldes["ventes"]},
                                  {"label": "Carnets de commandes", "color": VERT, "points": soldes["cmd"]},
                                  {"label": "Prix des produits finis", "color": ROUGE, "points": soldes["prix"]}]}
    print(f"{'Conjoncture industrielle (EMC)':<30} {'4 series':<12} {len(soldes['prod'])} mois  (fichier BAM EMC, soldes)")

    ipp = load_ipp()
    data["ipp"] = {"name": "Prix à la production industrielle (IPP)", "section": "Données économiques nationales",
                   "group": "Prix", "unit": "indice (base 100 = 2010)", "decimals": 1, "agg": "avg", "freq": "A",
                   "lines": [{"label": "Manufacturières", "color": BLEU, "points": ipp["Manufacturières"]},
                             {"label": "Électricité", "color": ORANGE, "points": ipp["Électricité"]},
                             {"label": "Extractives", "color": VERT, "points": ipp["Extractives"]},
                             {"label": "Eau", "color": ROUGE, "points": ipp["Eau"]}]}
    print(f"{'IPP prix production (HCP)':<30} {'4 series':<12} {len(ipp['Manufacturières'])} ans  (API HCP I1418, base 2010)")

    ipiem = load_ipiem()
    data["ipiem"] = {"name": "Production industrielle (IPIEM, volume)", "section": "Données économiques nationales",
                     "group": "Conjoncture industrielle", "unit": "indice (base 100 = 2015)", "decimals": 1, "agg": "avg", "freq": "Q",
                     "lines": [{"label": "Manufacturières", "color": BLEU, "points": ipiem["Manufacturières"]},
                               {"label": "Électricité", "color": ORANGE, "points": ipiem["Électricité"]},
                               {"label": "Extractives", "color": VERT, "points": ipiem["Extractives"]}]}
    print(f"{'IPIEM production (HCP)':<30} {'3 series':<12} {len(ipiem['Manufacturières'])} trim.  (notes HCP, base 2015)")

    fp = load_finances_publiques()
    data["finances"] = {"name": "Finances publiques (recettes & dépenses)", "section": "Données économiques nationales",
                        "group": "Finances publiques", "unit": "milliards DH / an", "decimals": 1, "agg": "avg", "freq": "A",
                        "lines": [{"label": "Recettes ordinaires", "color": VERT, "points": fp["recettes"]},
                                  {"label": "Dépenses ordinaires", "color": ORANGE, "points": fp["depenses"]}]}
    print(f"{'Finances publiques (HCP)':<30} {'2 series':<12} {len(fp['recettes'])} ans  (annuaires HCP + TGR, 2006-2025)")

    data["deficit"] = {"name": "Déficit du Trésor & charge de la dette", "section": "Données économiques nationales",
                       "group": "Finances publiques", "unit": "milliards DH / an", "decimals": 1, "agg": "avg", "freq": "A",
                       "lines": [{"label": "Déficit budgétaire global", "color": ROUGE, "points": fp["deficit"]},
                                 {"label": "Charge de la dette (intérêts)", "color": BLEU, "points": fp["dette"]}]}
    print(f"{'Déficit Trésor (HCP)':<30} {'2 series':<12} {len(fp['deficit'])} ans  (annuaires HCP + TGR, 2006-2025)")

    for k in data:
        data[k]["note"] = NOTES.get(k, "Survole la courbe pour lire la date et la valeur exacte.")
        # Stats descriptives calculees sur la courbe la plus longue (frequence native).
        main = max(data[k]["lines"], key=lambda L: len(L["points"]))
        st = compute_stats(main["points"])
        if st is not None:
            st["main_label"] = main["label"] if len(data[k]["lines"]) > 1 else None
        data[k]["stats"] = st
        data[k]["narrative"] = NARRATIVES.get(k, "")
    return data


# Dispositif informationnel BAM : 3 grandes categories -> rubriques (chacune sa source).
# "ids" = datasets deja disponibles (voir DATA). Rubrique sans ids = a collecter (placeholder).
TAXONOMY = [
    {"section": "Décision de politique monétaire (la cible)", "topics": [
        {"name": "Taux directeur et décisions du Conseil",
         "source": "Bank Al-Maghrib · Historique des décisions de politique monétaire", "ids": ["directeur"]},
    ]},
    {"section": "Environnement international", "topics": [
        {"name": "Environnement international (croissance, emploi, inflation, marchés financiers, matières premières, décisions des banques centrales)",
         "source": "Réseau GPMN · FMI · Banque Mondiale · BRI · OCDE · FED · BCE · BoE",
         "ids": ["bce", "fed", "infl_us", "infl_ze", "eurusd", "brent", "food", "gepu"]},
    ]},
    {"section": "Données monétaires et financières nationales", "topics": [
        {"name": "Statistiques monétaires (agrégats, crédit, dépôts)",
         "source": "Bank Al-Maghrib (via API HCP, I1450)", "ids": ["m3"]},
        {"name": "Marchés monétaires et de change (taux, TMP, change, adjudications)",
         "source": "BAM", "ids": ["monia"]},
        {"name": "Marchés des capitaux",
         "source": "Bourse de Casablanca (via API HCP, I1887)", "ids": ["capi"]},
        {"name": "Taux créditeurs (dépôts à terme 6 et 12 mois)",
         "source": "Bank Al-Maghrib (taux moyen pondéré des comptes et bons de caisse)", "ids": ["depots"]},
        {"name": "Taux débiteurs (par type de crédit)",
         "source": "Enquête trimestrielle BAM sur les taux débiteurs (2010-2026, continu)", "ids": ["debiteurs"]},
        {"name": "Conditions d'octroi du crédit bancaire",
         "source": "Enquête trimestrielle BAM auprès du système bancaire", "ids": []},
    ]},
    {"section": "Données économiques nationales", "topics": [
        {"name": "Activité, climat des affaires et coûts de production (industrie)",
         "source": "Enquête mensuelle de conjoncture BAM (soldes d'opinion + TUC, fichier de séries)", "ids": ["tuc", "conj_ind"]},
        {"name": "Anticipations d'inflation",
         "source": "Enquête trimestrielle BAM auprès des experts du système financier", "ids": []},
        {"name": "Confiance des ménages (ICM)",
         "source": "HCP · Enquête nationale de conjoncture auprès des ménages", "ids": ["icm"]},
        {"name": "Marché immobilier (transactions, prix, indice IPAI)",
         "source": "ANCFCC (Conservation Foncière) · Bank Al-Maghrib", "ids": ["ipai"]},
        {"name": "Comptes nationaux (croissance, PIB, investissement, consommation)",
         "source": "HCP · Direction de la comptabilité nationale (API BDS, I4276)", "ids": ["pib"]},
        {"name": "Output gap (construit, 3 méthodes de BAM)",
         "source": "Construit : filtre HP + fonction de production + semi-structurel · données FMI/WEO & HCP · méthode Chafik/BAM 2017", "ids": ["output_gap", "output_gap_q"]},
        {"name": "Marché du travail (emploi, chômage, taux d'activité)",
         "source": "HCP · Enquête Nationale sur l'Emploi (API BDS, I4249/I4250)", "ids": ["travail"]},
        {"name": "Prix à la consommation, inflation globale, prix à la production",
         "source": "HCP (inflation globale, IPP) · Bank Al-Maghrib (inflation sous-jacente)", "ids": ["inflation", "ipp"]},
        {"name": "Production industrielle, énergétique et minière (IPIEM, volume)",
         "source": "HCP · notes trimestrielles IPIEM base 2015 (assemblées, T1 2020 à T3 2025)", "ids": ["ipiem"]},
        {"name": "Finances publiques et loi de finances",
         "source": "HCP · Annuaires statistiques (2006-2023) + TGR bulletin réalisé (2024-2025) · source Ministère des Finances", "ids": ["finances", "deficit"]},
        {"name": "Pluviométrie et couvert végétal (production céréalière)",
         "source": "Direction de la Météorologie Nationale · Centre Royal de Télédétection Spatiale", "ids": []},
        {"name": "Production agricole (céréalière et hors céréalière)",
         "source": "Ministère de l'Agriculture (céréalière via API HCP, I3824) · hors céréalière non publiée séparément", "ids": ["cereales"]},
        {"name": "Comptes extérieurs (balance des paiements)",
         "source": "Office des Changes (biens, via API HCP I4183/I4185) · balance des paiements complète non couverte", "ids": ["commerce"]},
    ]},
]


HTML = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Data Lab · BMCE Capital Markets</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%23123e8b'/%3E%3Ctext x='16' y='22' font-family='Arial,sans-serif' font-size='16' font-weight='bold' fill='white' text-anchor='middle'%3EB%3C/text%3E%3C/svg%3E">
<meta name="theme-color" content="#123e8b">
<style>
  :root{
    --bg:#f6f7f9; --panel:#ffffff; --ink:#1a1d21; --muted:#6b7280;
    --line:#e6e8eb; --accent:#123e8b; --accent-soft:#e9eef8;
    --bmce:#123e8b; --bmce-grey:#7e8184;
  }
  @media (prefers-color-scheme: dark){
    :root{ --bg:#14171b; --panel:#1c2026; --ink:#e8eaed; --muted:#9aa2ad;
           --line:#2b3038; --accent:#5e8ed6; --accent-soft:#1b2740;
           --bmce:#7ea3e0; --bmce-grey:#9aa2ad; }
  }
  *{ box-sizing:border-box; }
  body{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
        background:var(--bg); color:var(--ink); }
  .app{ display:grid; grid-template-columns:288px 1fr; height:100vh; }
  aside{ background:var(--panel); border-right:1px solid var(--line); padding:22px 16px;
         overflow-y:auto; min-height:0; }
  .brand{ margin:0 4px 14px; }
  .brand-mark{ display:flex; align-items:center; gap:9px; }
  .b-txt{ display:flex; flex-direction:column; line-height:1; }
  .b-bmce{ font-size:17px; font-weight:800; letter-spacing:.005em; color:var(--bmce); }
  .b-mkt{ font-size:9.5px; font-weight:600; letter-spacing:.34em; color:var(--bmce-grey);
        align-self:flex-end; margin-top:4px; margin-right:1px; }
  .b-sphere{ width:22px; height:22px; border-radius:50%; flex:0 0 auto; position:relative; overflow:hidden;
        background:radial-gradient(circle at 34% 28%, #ffffff 0%, #dbe2ec 46%, #a9b4c4 100%); }
  .b-sphere::after{ content:""; position:absolute; right:-6px; bottom:-8px; width:20px; height:20px;
        border-radius:50%; background:var(--bmce); transform:rotate(18deg); }
  .brand-product{ margin-top:11px; font-size:15px; font-weight:700; letter-spacing:.01em; color:var(--ink);
        border-top:1px solid var(--line); padding-top:11px; }
  aside .sub{ font-size:11.5px; color:var(--muted); margin:6px 4px 18px; }
  .section-hd{ display:flex; align-items:center; gap:8px; width:100%; border:0; cursor:pointer;
        background:transparent; color:var(--ink); font-size:12.5px; font-weight:700;
        letter-spacing:.03em; text-transform:uppercase; padding:11px 8px; border-radius:9px;
        margin-top:8px; }
  .section-hd:hover{ background:var(--accent-soft); }
  .chev{ transition:transform .15s; font-size:10px; color:var(--muted); }
  .section.collapsed .chev{ transform:rotate(-90deg); }
  .section.collapsed .section-body{ display:none; }
  .navcat{ font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.07em;
         color:var(--muted); margin:14px 8px 4px; }
  .navcat.soon{ margin-top:16px; }
  .item{ display:flex; align-items:flex-start; gap:9px; width:100%; text-align:left; border:0;
         background:transparent; color:var(--ink); padding:7px 11px; border-radius:9px;
         font-size:13px; cursor:pointer; transition:background .12s; line-height:1.4; }
  .item:hover{ background:var(--accent-soft); }
  .item.active{ background:var(--accent); color:#fff; font-weight:600; }
  .item.home{ font-weight:600; margin-bottom:10px; }
  .item.home .ilab{ margin-left:2px; }
  .dotstat{ width:7px; height:7px; border-radius:50%; flex:0 0 auto; margin-top:6px; }
  .dotstat.on{ background:var(--accent); }
  .dotstat.off{ border:1.5px solid var(--muted); }
  .item.active .dotstat.on{ background:#fff; }
  .ilab{ flex:1; }
  #source{ color:var(--muted); font-size:11.5px; margin-top:5px; }
  /* Accueil : la mission / l'exercice */
  #mission{ display:none; max-width:860px; }
  #corrpage{ display:none; max-width:900px; }
  .ct-wrap{ overflow-x:auto; border:1px solid var(--line); border-radius:12px; margin:6px 0 20px; }
  table.ct{ width:100%; border-collapse:collapse; font-size:13px; }
  table.ct th, table.ct td{ padding:9px 12px; text-align:right; white-space:nowrap; }
  table.ct th:first-child, table.ct td:first-child, table.ct th:nth-child(3), table.ct td:nth-child(3){ text-align:left; }
  table.ct thead th{ background:var(--panel); color:var(--muted); font-weight:600; border-bottom:1px solid var(--line); }
  table.ct tbody tr:nth-child(even){ background:var(--accent-soft); }
  table.ct td.ct-rho{ font-weight:800; color:var(--accent); }
  table.ct td.ct-name{ font-weight:600; color:var(--ink); }
  .ct-rank{ color:var(--muted); font-weight:700; }
  .m-kicker{ font-size:11px; font-weight:700; letter-spacing:.14em; text-transform:uppercase;
        color:var(--accent); margin:18px 0 10px; }
  .m-title{ font-size:27px; line-height:1.2; margin:0 0 12px; color:var(--ink); }
  .m-lead{ font-size:15px; line-height:1.6; color:var(--muted); margin:0 0 26px; max-width:680px; }
  .m-steps{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:24px; }
  .m-step{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:18px 18px 16px; }
  .m-num{ display:inline-block; font-size:13px; font-weight:800; color:var(--accent);
        background:var(--accent-soft); border-radius:7px; padding:3px 9px; margin-bottom:10px; }
  .m-step b{ display:block; font-size:15px; color:var(--ink); margin-bottom:6px; }
  .m-step p{ font-size:13px; line-height:1.55; color:var(--muted); margin:0; }
  .m-source{ background:var(--accent-soft); border-left:3px solid var(--accent);
        border-radius:0 12px 12px 0; padding:16px 18px; margin-bottom:18px; }
  .m-source-hd{ font-size:11px; font-weight:700; letter-spacing:.1em; text-transform:uppercase;
        color:var(--accent); margin-bottom:6px; }
  .m-source p{ font-size:13.5px; line-height:1.6; color:var(--ink); margin:0; }
  .m-source b, .m-step b b{ color:var(--ink); }
  .m-doc{ display:flex; align-items:center; gap:14px; text-decoration:none;
        background:var(--panel); border:1.5px solid var(--accent); border-radius:14px;
        padding:14px 18px; margin-bottom:22px; transition:box-shadow .15s, transform .1s; }
  .m-doc:hover{ box-shadow:0 4px 16px rgba(37,99,168,.18); transform:translateY(-1px); }
  .m-doc-ico{ flex:0 0 auto; font-size:12px; font-weight:800; letter-spacing:.05em;
        color:#fff; background:var(--accent); border-radius:8px; padding:9px 11px; }
  .m-doc-txt{ flex:1; display:flex; flex-direction:column; gap:2px; }
  .m-doc-txt b{ font-size:14.5px; color:var(--ink); }
  .m-doc-txt span{ font-size:12.5px; color:var(--muted); }
  .m-doc-cta{ flex:0 0 auto; font-size:13px; font-weight:700; color:var(--accent); }
  .m-notes{ border-top:1px solid var(--line); padding-top:16px; margin-bottom:18px; }
  .m-notes-hd{ font-size:11px; font-weight:700; letter-spacing:.1em; text-transform:uppercase;
        color:var(--muted); margin-bottom:10px; }
  .m-notes ul{ margin:0; padding-left:18px; }
  .m-notes li{ font-size:13px; line-height:1.6; color:var(--ink); margin-bottom:10px; }
  .m-notes li b{ color:var(--ink); }
  .m-notes a{ color:var(--accent); }
  .m-hint{ font-size:12.5px; color:var(--muted); font-style:italic; margin:0; }
  .m-credit{ margin-top:26px; padding-top:14px; border-top:1px solid var(--line);
        font-size:12px; color:var(--muted); }
  .m-credit .b-bmce{ font-size:12px; font-weight:800; }
  .m-credit .b-mkt2{ font-size:10px; font-weight:600; letter-spacing:.2em; color:var(--bmce-grey); }
  @media (max-width:760px){ .m-steps{ grid-template-columns:1fr; } }
  /* Définition (avant le graphe) */
  #definition{ background:var(--accent-soft); border-radius:12px; padding:4px 18px 14px; margin:16px 0 4px; }
  #definition .sec-hd{ margin:14px 0 6px; }
  #definition p{ font-size:13.5px; line-height:1.6; color:var(--ink); margin:0; max-width:760px; }
  main{ padding:26px 30px; overflow-y:auto; min-height:0; }
  .head{ display:flex; align-items:baseline; justify-content:space-between; gap:16px; flex-wrap:wrap; }
  .head h2{ margin:0; font-size:21px; }
  .unit{ color:var(--muted); font-size:13px; }
  .controls{ display:flex; gap:6px; margin:18px 0 10px; flex-wrap:wrap; align-items:center; }
  #cmpbar{ margin:2px 0 14px; }
  .ctl-lab{ font-size:11.5px; color:var(--muted); margin-left:6px; }
  .sel{ border:1px solid var(--line); background:var(--panel); color:var(--ink); border-radius:10px;
        padding:6px 10px; font-size:13px; cursor:pointer; max-width:220px; }
  .corr{ font-size:12.5px; color:var(--accent); font-weight:600; margin-left:4px; }
  .seg{ display:inline-flex; background:var(--panel); border:1px solid var(--line);
        border-radius:10px; overflow:hidden; }
  .seg button{ border:0; background:transparent; color:var(--muted); padding:7px 15px;
        font-size:13px; cursor:pointer; }
  .seg button.on{ background:var(--accent); color:#fff; font-weight:600; }
  .btn{ border:1px solid var(--line); background:var(--panel); color:var(--ink); border-radius:10px;
        padding:7px 13px; font-size:13px; cursor:pointer; transition:background .12s;
        text-decoration:none; display:inline-flex; align-items:center; }
  .btn:hover{ background:var(--accent-soft); }
  .card{ background:var(--panel); border:1px solid var(--line); border-radius:14px;
         padding:14px 8px 6px; position:relative; }
  svg{ display:block; width:100%; height:auto; }
  .legend{ display:flex; gap:18px; padding:4px 14px 12px; font-size:12.5px; color:var(--muted); }
  .legend span{ display:inline-flex; align-items:center; gap:7px; }
  .dot{ width:11px; height:3px; border-radius:2px; display:inline-block; }
  .stats{ display:flex; gap:26px; margin-top:16px; flex-wrap:wrap; }
  .stat{ font-size:12.5px; color:var(--muted); }
  .stat b{ display:block; font-size:18px; color:var(--ink); font-weight:650; margin-top:2px; }
  #tip{ position:fixed; pointer-events:none; background:var(--ink); color:var(--bg);
        padding:8px 11px; border-radius:9px; font-size:12.5px; line-height:1.5;
        opacity:0; transition:opacity .08s; white-space:nowrap; z-index:9;
        box-shadow:0 6px 20px rgba(0,0,0,.25); }
  #tip .d{ opacity:.7; font-size:11px; }
  .foot{ color:var(--muted); font-size:11.5px; margin-top:20px; }
  .sec-hd{ font-size:13px; font-weight:700; letter-spacing:.02em; margin:28px 0 2px; color:var(--ink); }
  .statstable{ margin-top:12px; }
  .tbl-note{ font-size:11.5px; color:var(--muted); margin-bottom:6px; }
  .tbl-wrap{ max-height:230px; overflow:auto; border:1px solid var(--line); border-radius:10px; }
  .statstable table{ width:100%; border-collapse:collapse; font-size:12.5px; }
  .statstable th, .statstable td{ padding:6px 12px; text-align:right; white-space:nowrap; }
  .statstable th:first-child, .statstable td:first-child{ text-align:left; }
  .statstable thead th{ position:sticky; top:0; background:var(--panel); color:var(--muted);
        font-weight:600; border-bottom:1px solid var(--line); }
  .statstable tbody tr:nth-child(even){ background:var(--accent-soft); }
  #analysis{ margin-top:8px; max-width:760px; }
  #analysis .auto{ background:var(--accent-soft); border-left:3px solid var(--accent);
        border-radius:0 9px 9px 0; padding:11px 14px; font-size:13px; margin-bottom:12px; }
  #analysis .prose p{ font-size:13.5px; line-height:1.62; color:var(--ink); margin:0 0 10px; }
</style>
</head>
<body>
<div class="app">
  <aside>
    <div class="brand">
      <div class="brand-mark">
        <span class="b-txt"><span class="b-bmce">BMCE CAPITAL</span><span class="b-mkt">MARKETS</span></span>
        <span class="b-sphere"></span>
      </div>
      <div class="brand-product">Data Lab</div>
    </div>
    <p class="sub">Les inputs de la décision de Bank Al-Maghrib · définitions, statistiques et analyse des mouvements</p>
    <nav id="nav"></nav>
  </aside>
  <main>
    <div class="head">
      <div>
        <h2 id="title"></h2>
        <div id="source"></div>
      </div>
      <span class="unit" id="unit"></span>
    </div>
    <div id="definition">
      <h3 class="sec-hd">Définition</h3>
      <p id="def-text"></p>
    </div>
    <section id="mission">
      <div class="m-kicker">L'exercice</div>
      <h2 class="m-title">Les inputs de la décision de politique monétaire de Bank Al-Maghrib</h2>
      <p class="m-lead">Construire la base de données qui alimente un modèle d'anticipation des décisions de taux de BAM (hausse, baisse ou statu quo). Trois étapes.</p>
      <div class="m-steps">
        <div class="m-step"><span class="m-num">01</span><b>Choisir les inputs</b><p>Sélectionner les indicateurs qui pèsent réellement sur la décision : ceux qui causent ou anticipent l'inflation à deux ans, et les canaux externes qui la pilotent au Maroc.</p></div>
        <div class="m-step"><span class="m-num">02</span><b>Chercher la data</b><p>Sourcer chaque input sur des sources primaires. Le périmètre suit le <b>Dispositif informationnel de Bank Al-Maghrib</b>, le document officiel qui recense les sources que la Banque utilise pour élaborer ses prévisions.</p></div>
        <div class="m-step"><span class="m-num">03</span><b>Analyser les mouvements</b><p>Pour chaque série : une définition complète, des statistiques descriptives, puis un commentaire des grands mouvements et de ce qui s'est passé dans le monde pour les provoquer.</p></div>
      </div>
      <div class="m-source">
        <div class="m-source-hd">Le fil conducteur</div>
        <p>Chaque rubrique de ce tableau de bord correspond à une ligne du <b>Dispositif informationnel de BAM</b>, organisé en trois blocs : environnement international, données monétaires et financières nationales, données économiques nationales. Ce document a servi à décider quoi chercher.</p>
      </div>
      <a class="m-doc" href="dispositif-informationnel-bam.pdf" target="_blank" rel="noopener">
        <span class="m-doc-ico">PDF</span>
        <span class="m-doc-txt">
          <b>Dispositif informationnel de Bank Al-Maghrib</b>
          <span>Le document officiel qui recense les sources utilisées par BAM. Cliquez pour l'ouvrir ou le télécharger.</span>
        </span>
        <span class="m-doc-cta">Ouvrir ▸</span>
      </a>
      <div class="m-notes">
        <div class="m-notes-hd">Notes de méthode et limites</div>
        <ul>
          <li><b>Output gap reconstruit.</b> L'output gap n'est pas publié pour le Maroc. Je l'ai reconstruit selon les <b>trois méthodes du document de travail de Bank Al-Maghrib</b> (<a href="ref-output-gap-chafik-bam-2017.pdf" target="_blank" rel="noopener">Chafik, 2017</a>) : le filtre de Hodrick-Prescott, la fonction de production de Cobb-Douglas, et le modèle semi-structurel de Blagrave et al. (2015). Deux études marocaines détaillent chacune une de ces méthodes : le filtre HP (<a href="ref-output-gap-hp.pdf" target="_blank" rel="noopener">Bassite &amp; El Khattab</a>) et la fonction de production (<a href="ref-output-gap-fonction-production.pdf" target="_blank" rel="noopener">Hefnaoui &amp; Charfi, 2024</a>). C'est une estimation, pas une mesure directe.</li>
          <li><b>Le choix des inputs reste à consolider.</b> La sélection s'appuie pour l'instant sur une logique économique (retenir ce qui cause ou anticipe l'inflation à deux ans, écarter ce qui confirme trop tard ou fait doublon). Ce que je veux surtout comprendre, c'est comment Bank Al-Maghrib elle-même sélectionne et hiérarchise ses propres inputs.</li>
          <li><b>Sourcing primaire.</b> Chaque donnée a été récupérée directement à la source citée dans le Dispositif informationnel de BAM (HCP, Office des Changes, Bank Al-Maghrib, TGR, ainsi que FRED et le FMI pour l'environnement international), et non via des agrégateurs tiers.</li>
        </ul>
      </div>
      <p class="m-hint">Choisis une donnée dans le menu de gauche pour voir sa définition, ses statistiques et l'analyse de ses mouvements.</p>
      <div class="m-credit"><span class="b-bmce">BMCE CAPITAL</span> <span class="b-mkt2">MARKETS</span> · Data Lab</div>
    </section>
    <section id="corrpage">
      <div class="m-kicker">Analyse</div>
      <h2 class="m-title">Ce qui discrimine les décisions de BAM</h2>
      <p class="m-lead" id="corr-lead"></p>
      <div id="corr-table"></div>
      <div class="m-source">
        <div class="m-source-hd">Méthode</div>
        <p>Chaque input est échantillonné à la date de chaque réunion du Conseil, en prenant sa valeur du <b>mois précédent</b> (point-in-time : on n'utilise que ce qui était connu à la décision). On teste le niveau et la variation sur 12 mois, on garde la transformation la plus discriminante, et on mesure la <b>corrélation de Spearman</b> avec la décision signée (hausse +1, statu quo 0, baisse -1). Les trois dernières colonnes donnent la valeur moyenne de l'input selon la décision effectivement prise : un bon input a des moyennes bien séparées entre hausse et baisse.</p>
      </div>
      <div class="m-notes">
        <div class="m-notes-hd">Limites</div>
        <ul>
          <li>C'est un <b>filtre</b>, pas le modèle : une corrélation élevée ne prouve pas la causalité et ne suffit pas à prédire.</li>
          <li><b>Petit échantillon</b> : seulement <span id="corr-nmoves"></span> mouvements sur la période. Les corrélations sont instables, surtout pour les séries à faible n (colonne n).</li>
          <li>Deux inputs peuvent être corrélés à la décision <b>et entre eux</b> (ex. inflation globale et sous-jacente) : dans un modèle, ils ne comptent qu'une fois.</li>
          <li>Le signe doit être cohérent avec la théorie (inflation ou choc externe en hausse va avec les hausses de taux). Un signe inversé est suspect.</li>
        </ul>
      </div>
    </section>
    <div class="controls" id="controls">
      <div class="seg" id="gran"></div>
      <button class="btn" id="exp-series" title="Télécharger cette série en CSV">CSV série</button>
      <a class="btn" id="exp-matrix" href="features.csv" download="data-lab-features.csv" title="Télécharger la matrice de features alignée au mensuel">Matrice (features)</a>
    </div>
    <div class="controls" id="cmpbar">
      <span class="ctl-lab">Transformer</span>
      <div class="seg" id="tf">
        <button data-t="level" class="on">Niveau</button>
        <button data-t="yoy">Δ 1 an</button>
        <button data-t="base100">Base 100</button>
        <button data-t="zscore">Z-score</button>
      </div>
      <span class="ctl-lab">Comparer</span>
      <select id="cmp" class="sel"></select>
      <div class="seg" id="cmpmode" style="display:none">
        <button data-m="overlay" class="on">Superposer</button>
        <button data-m="spread">Écart</button>
      </div>
      <span id="corr" class="corr"></span>
    </div>
    <div class="card" id="card">
      <svg id="chart" viewBox="0 0 960 440" preserveAspectRatio="none"></svg>
      <div class="legend" id="legend"></div>
    </div>
    <h3 class="sec-hd" id="stats-hd">Statistiques descriptives</h3>
    <div class="stats" id="stats"></div>
    <div class="statstable" id="statstable"></div>
    <h3 class="sec-hd" id="ana-hd">Analyse</h3>
    <div id="analysis"></div>
    <p class="foot" id="foot">Survole la courbe pour lire la date et la valeur exacte. Taux directeurs = niveau en fin de période (la décision réelle, en pas de 0,25 %). Prix, inflation et indices = moyenne de la période.</p>
  </main>
</div>
<div id="tip"></div>

<script>
const DATA = __DATA__;
const TAXO = __TAXO__;
const CORR = __CORR__;
const NS = "http://www.w3.org/2000/svg";
const M = {l:58, r:22, t:22, b:34}, W=960, H=440;
const state = { id:Object.keys(DATA)[0], gran:"M", source:"", transform:"level", compareId:null, compareMode:"overlay" };
const CMP_COLOR = "#8b5cf6";

/* ---------- agregation ---------- */
const MONTHS = ["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."];
function tOf(key){ // "YYYY-MM" -> ms
  const [y,m]=key.split("-").map(Number); return Date.UTC(y,m-1,1);
}
function aggregate(points, gran, agg){
  const keys = Object.keys(points).sort();
  if(gran==="M"){
    return keys.map(k=>{const [y,m]=k.split("-").map(Number);
      return {t:tOf(k), v:points[k], label:MONTHS[m-1]+" "+y};});
  }
  const buckets = {};
  for(const k of keys){                       // keys triees ascendantes
    const [y,m]=k.split("-").map(Number);
    let bk, lab, t;
    if(gran==="Y"){ bk=""+y; lab=""+y; t=Date.UTC(y,6,1); }
    else { const q=Math.floor((m-1)/3)+1; bk=y+"-Q"+q; lab="T"+q+" "+y; t=Date.UTC(y,(q-1)*3+1,1); }
    (buckets[bk]=buckets[bk]||{sum:0,n:0,last:null,lab,t});
    buckets[bk].sum+=points[k]; buckets[bk].n++; buckets[bk].last=points[k]; // last = dernier mois du bucket
  }
  return Object.values(buckets).sort((a,b)=>a.t-b.t)
      .map(b=>({t:b.t, v: agg==="eop" ? b.last : b.sum/b.n, label:b.lab}));
}

/* ---------- helpers ---------- */
function niceTicks(min,max,n){
  const span=max-min||1, step0=span/n, mag=Math.pow(10,Math.floor(Math.log10(step0)));
  const norm=step0/mag, step=(norm>=5?10:norm>=2?5:norm>=1?2:1)*mag/ (norm>=5?2:1);
  const s=(norm>=5?5:norm>=2?2:norm>=1?1:0.5)*mag;
  const lo=Math.floor(min/s)*s, hi=Math.ceil(max/s)*s, out=[];
  for(let v=lo; v<=hi+1e-9; v+=s) out.push(+v.toFixed(6));
  return out;
}
function fmt(v){ const d=DATA[state.id].decimals; return v.toLocaleString("fr-FR",{minimumFractionDigits:d,maximumFractionDigits:d}); }

/* ---------- rendu ---------- */
let RENDER = null;
/* ---------- transformations & comparaison ---------- */
function applyTransform(pts, mode){
  if(!pts.length || mode==="level") return pts;
  if(mode==="yoy"){
    const k=({M:12,Q:4,Y:1})[state.gran]||12; const out=[];
    for(let i=k;i<pts.length;i++) out.push({t:pts[i].t, v:pts[i].v-pts[i-k].v, label:pts[i].label});
    return out;
  }
  if(mode==="base100"){
    const b=pts[0].v; if(!b) return pts; return pts.map(p=>({t:p.t, v:p.v/b*100, label:p.label}));
  }
  if(mode==="zscore"){
    const vs=pts.map(p=>p.v), m=vs.reduce((a,b)=>a+b,0)/vs.length;
    const sd=Math.sqrt(vs.reduce((a,b)=>a+(b-m)*(b-m),0)/vs.length)||1;
    return pts.map(p=>({t:p.t, v:(p.v-m)/sd, label:p.label}));
  }
  return pts;
}
function cmpMainPts(cm){
  const L=cm.lines.reduce((a,b)=>Object.keys(b.points).length>Object.keys(a.points).length?b:a);
  return applyTransform(aggregate(L.points, state.gran, cm.agg), state.transform);
}
function alignPairs(a,b){ const mb=new Map(b.map(p=>[p.t,p.v])); const o=[];
  for(const p of a) if(mb.has(p.t)) o.push([p.v, mb.get(p.t)]); return o; }
function spreadPts(a,b){ const mb=new Map(b.map(p=>[p.t,p.v])); const o=[];
  for(const p of a) if(mb.has(p.t)) o.push({t:p.t, v:p.v-mb.get(p.t), label:p.label}); return o; }
function pearson(pairs){ const n=pairs.length; if(n<3) return null;
  let sx=0,sy=0,sxx=0,syy=0,sxy=0;
  for(const [x,y] of pairs){ sx+=x; sy+=y; sxx+=x*x; syy+=y*y; sxy+=x*y; }
  const cov=sxy-sx*sy/n, vx=sxx-sx*sx/n, vy=syy-sy*sy/n, d=Math.sqrt(vx*vy);
  return d ? cov/d : null; }
function renderCorr(r){
  const el=document.getElementById("corr");
  el.textContent = (r==null) ? "" : "corrélation r = " + r.toLocaleString("fr-FR",{minimumFractionDigits:2,maximumFractionDigits:2});
}

function draw(){
  const meta=DATA[state.id];
  let series=meta.lines.map(L=>({label:L.label,color:L.color,pts:applyTransform(aggregate(L.points,state.gran,meta.agg),state.transform)}));
  // Comparaison a une 2e serie
  let corr=null;
  const cmpId=(state.compareId && state.compareId!==state.id && DATA[state.compareId]) ? state.compareId : null;
  if(cmpId){
    const cm=DATA[cmpId], cmPts=cmpMainPts(cm);
    const prMain=series.reduce((a,b)=>b.pts.length>a.pts.length?b:a);
    corr=pearson(alignPairs(prMain.pts, cmPts));
    if(state.compareMode==="spread"){
      series=[{label:"Écart (" + meta.name + " moins " + cm.name + ")", color:CMP_COLOR, pts:spreadPts(prMain.pts, cmPts)}];
    } else {
      series=series.concat([{label:cm.name, color:CMP_COLOR, pts:cmPts, dashed:true}]);
    }
  }
  renderCorr(corr);
  const allV=series.flatMap(s=>s.pts.map(p=>p.v));
  const allT=series.flatMap(s=>s.pts.map(p=>p.t));
  let ymin=Math.min(...allV), ymax=Math.max(...allV);
  const pad=(ymax-ymin)*0.08||1; ymin-=pad; ymax+=pad;
  if(ymin>0 && ymin<pad*2) ymin=Math.min(0,ymin);
  const tmin=Math.min(...allT), tmax=Math.max(...allT);
  const yticks=niceTicks(ymin,ymax,5);
  ymin=Math.min(ymin,yticks[0]); ymax=Math.max(ymax,yticks[yticks.length-1]);
  const X=t=> M.l+(t-tmin)/(tmax-tmin)*(W-M.l-M.r);
  const Y=v=> H-M.b-(v-ymin)/(ymax-ymin)*(H-M.t-M.b);

  const svg=document.getElementById("chart"); svg.innerHTML="";
  const add=(tag,attrs)=>{const e=document.createElementNS(NS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);svg.appendChild(e);return e;};

  // gridlines + y labels
  for(const v of yticks){
    add("line",{x1:M.l,x2:W-M.r,y1:Y(v),y2:Y(v),stroke:"var(--line)","stroke-width":1});
    const tx=add("text",{x:M.l-9,y:Y(v)+4,"text-anchor":"end","font-size":11,fill:"var(--muted)"});
    tx.textContent=fmt(v);
  }
  // x labels (annees)
  const y0=new Date(tmin).getUTCFullYear(), y1=new Date(tmax).getUTCFullYear();
  const stepY=(y1-y0)>16?4:2;
  for(let y=Math.ceil(y0/stepY)*stepY; y<=y1; y+=stepY){
    const t=Date.UTC(y,0,1); if(t<tmin||t>tmax) continue;
    add("line",{x1:X(t),x2:X(t),y1:M.t,y2:H-M.b,stroke:"var(--line)","stroke-width":1,"stroke-dasharray":"2 4"});
    const tx=add("text",{x:X(t),y:H-M.b+18,"text-anchor":"middle","font-size":11,fill:"var(--muted)"});
    tx.textContent=y;
  }
  // zero line
  if(ymin<0&&ymax>0) add("line",{x1:M.l,x2:W-M.r,y1:Y(0),y2:Y(0),stroke:"var(--muted)","stroke-width":1});

  // lines
  for(const s of series){
    const d=s.pts.map((p,i)=>(i?"L":"M")+X(p.t).toFixed(1)+" "+Y(p.v).toFixed(1)).join(" ");
    const at={d,fill:"none",stroke:s.color,"stroke-width":2,"stroke-linejoin":"round","stroke-linecap":"round"};
    if(s.dashed) at["stroke-dasharray"]="5 4";
    add("path",at);
  }
  // hover layer
  const hov=add("g",{id:"hov"});
  const overlay=add("rect",{x:M.l,y:M.t,width:W-M.l-M.r,height:H-M.t-M.b,fill:"transparent"});

  RENDER={series,X,Y,tmin,tmax,svg,hov,meta};
  buildLegend(series);
}

function buildLegend(series){
  document.getElementById("legend").innerHTML = series.length>1
    ? series.map(s=>`<span><i class="dot" style="background:${s.color}"></i>${s.label}</span>`).join("")
    : "";
}
function labelOf(key){
  const [y,m]=key.split("-").map(Number);
  const f=DATA[state.id].freq;
  if(f==="A") return ""+y;
  if(f==="Q") return ({2:"T1",5:"T2",8:"T3",11:"T4"}[m]||"")+" "+y;
  return MONTHS[m-1]+" "+y;
}
function fmtd(v,extra){ const d=DATA[state.id].decimals+(extra||0);
  let x=Number(v); if(Math.round(x*Math.pow(10,d))===0) x=0;   // évite l'affichage "-0,0"
  return x.toLocaleString("fr-FR",{minimumFractionDigits:d,maximumFractionDigits:d}); }
// Panneau de stats descriptives (calculees au build, frequence native ; independantes du toggle).
function renderStats(){
  const st=DATA[state.id].stats;
  const statsEl=document.getElementById("stats"), tblEl=document.getElementById("statstable");
  if(!st){ statsEl.innerHTML=""; tblEl.innerHTML=""; return; }
  const tile=(lab,val,sub)=>`<div class="stat">${lab}<b>${val}</b>${sub||""}</div>`;
  statsEl.innerHTML =
    tile("Dernier point", fmtd(st.last.value), labelOf(st.last.key))+
    tile("Moyenne", fmtd(st.mean), "sur la période")+
    tile("Médiane", fmtd(st.median), "")+
    tile("Écart-type", fmtd(st.std,1), "niveau")+
    tile("Min", fmtd(st.min), "")+
    tile("Max", fmtd(st.max), "")+
    tile("Volatilité", fmtd(st.vol,1), "variations")+
    tile("Observations", st.n, "points");
  const rows=st.by_period.map(p=>
    `<tr><td>${p.period}</td><td>${p.n}</td><td>${fmtd(p.mean)}</td><td>${fmtd(p.min)}</td><td>${fmtd(p.max)}</td><td>${fmtd(p.vol,1)}</td></tr>`).join("");
  const table=`<div class="tbl-wrap"><table><thead><tr><th>Année</th><th>n</th><th>Moyenne</th><th>Min</th><th>Max</th><th>Volatilité</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  tblEl.innerHTML=(st.main_label?`<div class="tbl-note">Calculées sur : <b>${st.main_label}</b></div>`:"")+table;
}
function esc(s){ return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
function mdBold(s){ return esc(s).replace(/\*\*(.+?)\*\*/g,"<b>$1</b>"); }
// Section Analyse : phrase "lecture actuelle" auto (depuis les stats) + narratif redige a la main.
function renderAnalysis(){
  const m=DATA[state.id], st=m.stats, el=document.getElementById("analysis");
  if(!st){ el.innerHTML=""; return; }
  const pos = st.last.value>=st.mean ? "au-dessus" : "en dessous";
  const freqLab = ({M:"mensuels",Q:"trimestriels",A:"annuels"})[m.freq]||"points";
  const auto = `Lecture actuelle : dernier point à <b>${fmtd(st.last.value)}</b> (${labelOf(st.last.key)}), `
    + `${pos} de sa moyenne de ${fmtd(st.mean)} ; amplitude ${fmtd(st.min)} à ${fmtd(st.max)} sur ${st.n} points ${freqLab}.`;
  const prose = m.narrative
    ? `<div class="prose">`+m.narrative.split(/\n\s*\n/).map(p=>`<p>${mdBold(p)}</p>`).join("")+`</div>`
    : "";
  el.innerHTML = `<div class="auto">${auto}</div>${prose}`;
}

/* ---------- interaction ---------- */
const tip=document.getElementById("tip");
function nearestByTime(pts,t){
  let lo=0; for(let i=1;i<pts.length;i++){ if(Math.abs(pts[i].t-t)<Math.abs(pts[lo].t-t)) lo=i; } return pts[lo];
}
function onMove(e){
  if(!RENDER) return;
  const {series,X,Y,tmin,tmax,svg,hov,meta}=RENDER;
  const rect=svg.getBoundingClientRect();
  const px=(e.clientX-rect.left)*(W/rect.width);
  if(px<M.l||px>W-M.r){ onLeave(); return; }
  const tCur=tmin+(px-M.l)/(W-M.l-M.r)*(tmax-tmin);
  // grille de reference = serie la plus longue (les series peuvent differer en longueur)
  const grid=series.reduce((a,b)=>b.pts.length>a.pts.length?b:a).pts;
  const ref=nearestByTime(grid,tCur); const t=ref.t, label=ref.label;
  hov.innerHTML="";
  const mk=(tag,a)=>{const el=document.createElementNS(NS,tag);for(const k in a)el.setAttribute(k,a[k]);hov.appendChild(el);};
  mk("line",{x1:X(t),x2:X(t),y1:M.t,y2:H-M.b,stroke:"var(--accent)","stroke-width":1});
  let rows="";
  for(const s of series){
    const p=nearestByTime(s.pts,t); if(!p) continue;
    mk("circle",{cx:X(p.t),cy:Y(p.v),r:4.5,fill:s.color,stroke:"#fff","stroke-width":1.5});
    rows+=`<div><i class="dot" style="background:${s.color};display:inline-block;margin-right:6px"></i>${s.label} : <b>${fmt(p.v)}</b> ${meta.unit.split(" ")[0]}</div>`;
  }
  tip.innerHTML=`<div class="d">${label}</div>${rows}`;
  tip.style.opacity=1;
  let tx=e.clientX+14, ty=e.clientY-10;
  if(tx+180>window.innerWidth) tx=e.clientX-180;
  tip.style.left=tx+"px"; tip.style.top=ty+"px";
}
function onLeave(){ tip.style.opacity=0; if(RENDER) RENDER.hov.innerHTML=""; }

/* ---------- nav ---------- */
/* ---------- export CSV ---------- */
function csvEsc(s){ s=String(s); return /[",\n;]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s; }
function download(name, text){
  const blob=new Blob(["﻿"+text], {type:"text/csv;charset=utf-8"});
  const url=URL.createObjectURL(blob);
  const a=document.createElement("a"); a.href=url; a.download=name; document.body.appendChild(a); a.click();
  a.remove(); setTimeout(()=>URL.revokeObjectURL(url), 1000);
}
function exportSeries(){
  const m=DATA[state.id];
  const keys=[...new Set(m.lines.flatMap(L=>Object.keys(L.points)))].sort();
  const head=["Date", ...m.lines.map(L=>L.label)];
  const rows=[head.map(csvEsc).join(",")];
  for(const k of keys) rows.push([k, ...m.lines.map(L=>L.points[k]??"")].map(csvEsc).join(","));
  download((state.id||"serie")+".csv", rows.join("\n"));
}
function buildNav(){
  const nav=document.getElementById("nav"); nav.innerHTML="";
  // Accueil : la demarche / l'exercice
  const home=document.createElement("button"); home.className="item home"; home.id="nav-home";
  home.innerHTML=`<span class="ilab">La démarche</span>`;
  home.onclick=()=>selectMission();
  nav.appendChild(home);
  const corr=document.createElement("button"); corr.className="item home"; corr.id="nav-corr";
  corr.innerHTML=`<span class="ilab">Ce qui prédit les décisions</span>`;
  corr.onclick=()=>selectCorr();
  nav.appendChild(corr);
  // Sections du dispositif informationnel : uniquement les donnees disponibles
  for(const sec of TAXO){
    const wrap=document.createElement("div"); wrap.className="section";
    const hd=document.createElement("button"); hd.className="section-hd";
    hd.innerHTML=`<span class="chev">▼</span><span>${sec.section}</span>`;
    hd.onclick=()=>wrap.classList.toggle("collapsed");
    const body=document.createElement("div"); body.className="section-body";
    const seen=new Set();
    for(const topic of sec.topics){
      if(!(topic.ids && topic.ids.length)) continue;
      for(const id of topic.ids){
        if(seen.has(id)) continue; seen.add(id);
        const b=document.createElement("button"); b.className="item"; b.dataset.id=id;
        b.innerHTML=`<span class="dotstat on"></span><span class="ilab">${DATA[id].name}</span>`;
        b.onclick=()=>selectSeries(id, topic.source);
        body.appendChild(b);
      }
    }
    if(body.children.length){ wrap.appendChild(hd); wrap.appendChild(body); nav.appendChild(wrap); }
  }
}
function syncNav(){
  document.querySelectorAll(".item[data-id]").forEach(b=>b.classList.toggle("active", b.dataset.id===state.id && state.id!=null));
  const home=document.getElementById("nav-home"); if(home) home.classList.toggle("active", state.view==="mission");
  const corr=document.getElementById("nav-corr"); if(corr) corr.classList.toggle("active", state.view==="corr");
}
function showView(view){   // "mission" | "corr" | "series"
  document.getElementById("mission").style.display = view==="mission"?"block":"none";
  document.getElementById("corrpage").style.display = view==="corr"?"block":"none";
  for(const el of ["definition","controls","cmpbar","card","stats-hd","stats","statstable","ana-hd","analysis","foot"]) document.getElementById(el).style.display = view==="series"?"":"none";
}
function selectSeries(id, source){ state.id=id; state.source=source; state.view="series"; syncNav(); refresh(); }
function selectMission(){
  state.id=null; state.view="mission"; syncNav();
  document.getElementById("title").textContent="";
  document.getElementById("unit").textContent="";
  document.getElementById("source").textContent="";
  showView("mission");
}
function selectCorr(){
  state.id=null; state.view="corr"; syncNav();
  document.getElementById("title").textContent="";
  document.getElementById("unit").textContent="";
  document.getElementById("source").textContent="";
  renderCorrPage();
  showView("corr");
}
function renderCorrPage(){
  const nf=(x,d)=>x==null?"n.d.":x.toLocaleString("fr-FR",{minimumFractionDigits:d,maximumFractionDigits:d});
  document.getElementById("corr-lead").textContent =
    `Classement des inputs par leur pouvoir à discriminer les décisions du Conseil (${CORR.n_meetings} réunions depuis 2006, dont ${CORR.n_moves} mouvements). Plus la corrélation est forte et plus les moyennes conditionnelles sont séparées, plus l'input accompagne les décisions.`;
  document.getElementById("corr-nmoves").textContent = CORR.n_moves;
  const rows=CORR.rows.map((r,i)=>{
    const d = r.decimals;
    return `<tr>
      <td class="ct-rank">${i+1}</td>
      <td class="ct-name">${r.name}</td>
      <td>${r.transform}</td>
      <td class="ct-rho">${nf(r.rho,2)}</td>
      <td>${r.n}</td>
      <td>${nf(r.hausse,d)}</td>
      <td>${nf(r.statuquo,d)}</td>
      <td>${nf(r.baisse,d)}</td>
    </tr>`;
  }).join("");
  document.getElementById("corr-table").innerHTML =
    `<div class="ct-wrap"><table class="ct"><thead><tr>
      <th>#</th><th>Input</th><th>Transformation</th><th>ρ Spearman</th><th>n</th>
      <th>Moy. si hausse</th><th>Moy. si statu quo</th><th>Moy. si baisse</th>
    </tr></thead><tbody>${rows}</tbody></table></div>`;
}
// Granularites autorisees selon la frequence NATIVE de la serie
const GRAN_LABEL = {M:"Mensuel", Q:"Trimestriel", Y:"Annuel"};
const FREQ_GRANS = { M:["M","Q","Y"], Q:["Q","Y"], A:["Y"] };
function buildGran(){
  const allowed = FREQ_GRANS[DATA[state.id].freq] || ["M","Q","Y"];
  if(!allowed.includes(state.gran)) state.gran = allowed[0];   // retombe sur la vue la plus fine dispo
  document.getElementById("gran").innerHTML =
    allowed.map(g=>`<button data-g="${g}" class="${g===state.gran?'on':''}">${GRAN_LABEL[g]}</button>`).join("");
  // un seul choix (serie annuelle) : on masque le toggle, inutile
  document.getElementById("gran").style.display = allowed.length>1 ? "" : "none";
}
function refresh(){
  const m=DATA[state.id];
  document.getElementById("title").textContent=m.name;
  document.getElementById("unit").textContent=m.unit;
  document.getElementById("source").textContent = state.source ? ("Source : "+state.source) : "";
  document.getElementById("def-text").textContent = m.note || "";
  document.getElementById("foot").textContent = "Survole un point pour lire la date et la valeur exacte.";
  showView("series");
  buildGran();
  draw();
  renderStats();
  renderAnalysis();
}

document.getElementById("gran").addEventListener("click",e=>{
  const b=e.target.closest("button[data-g]"); if(!b) return;
  state.gran=b.dataset.g;
  document.querySelectorAll("#gran button").forEach(x=>x.classList.toggle("on",x.dataset.g===state.gran));
  draw();
});
document.getElementById("exp-series").onclick=exportSeries;
// Menu Comparer : peuplé avec toutes les séries disponibles
(function(){
  let html='<option value="">Comparer à…</option>';
  for(const id in DATA) html+=`<option value="${id}">${DATA[id].name}</option>`;
  document.getElementById("cmp").innerHTML=html;
})();
document.getElementById("tf").addEventListener("click",e=>{
  const b=e.target.closest("button[data-t]"); if(!b) return;
  state.transform=b.dataset.t;
  document.querySelectorAll("#tf button").forEach(x=>x.classList.toggle("on",x.dataset.t===state.transform));
  draw();
});
document.getElementById("cmp").addEventListener("change",e=>{
  state.compareId=e.target.value||null;
  document.getElementById("cmpmode").style.display = state.compareId ? "" : "none";
  draw();
});
document.getElementById("cmpmode").addEventListener("click",e=>{
  const b=e.target.closest("button[data-m]"); if(!b) return;
  state.compareMode=b.dataset.m;
  document.querySelectorAll("#cmpmode button").forEach(x=>x.classList.toggle("on",x.dataset.m===state.compareMode));
  draw();
});
const chart=document.getElementById("chart");
chart.addEventListener("pointermove",onMove);
chart.addEventListener("pointerleave",onLeave);
window.addEventListener("resize",()=>RENDER&&draw());

buildNav(); selectMission();   // on ouvre sur la page "La démarche"
</script>
</body>
</html>
"""


def write_features(data):
    """Matrice de features alignee au mensuel (forward-fill des series moins frequentes) -> public/features.csv.
    Note : simple forward-fill (valeur connue des la periode) ; l'ajustement point-in-time
    (decalage par date de publication) viendra plus tard."""
    import csv as _csv

    def idx(ym):
        y, m = ym.split("-"); return int(y) * 12 + int(m) - 1

    cols = []  # (nom_colonne, points)
    for d in data.values():
        for L in d["lines"]:
            nm = d["name"] + (f" ({L['label']})" if len(d["lines"]) > 1 else "")
            cols.append((nm, L["points"]))

    allk = [k for _, pts in cols for k in pts]
    lo, hi = min(map(idx, allk)), max(map(idx, allk))
    months = [f"{(lo + i)//12:04d}-{((lo + i) % 12) + 1:02d}" for i in range(hi - lo + 1)]

    aligned = {}
    for nm, pts in cols:
        keys = sorted(pts, key=idx)
        first, last = idx(keys[0]), idx(keys[-1])
        col, ptr, cur = [], 0, None
        for i in range(lo, hi + 1):
            if i < first or i > last:
                col.append(""); continue
            while ptr < len(keys) and idx(keys[ptr]) <= i:
                cur = pts[keys[ptr]]; ptr += 1
            col.append(cur if cur is not None else "")
        aligned[nm] = col

    with open(DEST / "features.csv", "w", newline="", encoding="utf-8") as f:
        w = _csv.writer(f)
        w.writerow(["Date"] + [nm for nm, _ in cols])
        for i, ym in enumerate(months):
            w.writerow([ym] + [aligned[nm][i] for nm, _ in cols])
    print(f"features.csv : {len(months)} mois x {len(cols)} colonnes")


# Inputs classes dans l'analyse de discrimination des decisions : (id dataset, label de courbe ou None)
CORR_INPUTS = [
    ("inflation", "Inflation globale"), ("inflation", "Sous-jacente (core)"), ("pib", None),
    ("output_gap_q", None), ("tuc", None), ("monia", None), ("m3", "M3"), ("brent", None),
    ("eurusd", None), ("bce", "Depot"), ("fed", None), ("infl_ze", None), ("infl_us", None),
    ("food", None), ("gepu", None), ("commerce", "Solde commercial"),
    ("travail", "Taux de chômage"), ("debiteurs", "Taux global"), ("capi", None),
]


def analyze_decisions(data):
    """Classe les inputs par pouvoir de discrimination des decisions BAM. Pour chaque input, echantillonne
    a la date de reunion (valeur du mois precedent = point-in-time), teste niveau et variation sur 12 mois,
    garde la meilleure transformation, corrige de Spearman avec la decision signee (+1 hausse, 0 statu quo,
    -1 baisse), et donne la moyenne conditionnelle par type de decision."""
    import csv as _csv
    import math
    rows = [(r["date"], float(r["taux"])) for r in _csv.DictReader(open(DECISIONS_FILE, encoding="utf-8"))]
    rows.sort()
    meetings = [(rows[i][0][:7], int(np.sign(rows[i][1] - rows[i - 1][1]))) for i in range(1, len(rows))]
    dec = [d for _, d in meetings]

    def monthly_ff(points):
        s = pd.Series({pd.Period(k, "M"): v for k, v in points.items()}).sort_index()
        idx = pd.period_range(s.index.min(), s.index.max(), freq="M")
        return s.reindex(idx).ffill()

    def val_at(s, ym, lag=1):
        return s.get(pd.Period(ym, "M") - lag, np.nan)

    def spear(a, b):
        a, b = pd.Series(a), pd.Series(b)
        m = a.notna() & b.notna()
        if m.sum() < 8:
            return float("nan"), int(m.sum())
        # Spearman = Pearson sur les rangs (evite la dependance scipy)
        return round(float(a[m].rank().corr(b[m].rank())), 2), int(m.sum())

    out = []
    for did, lab in CORR_INPUTS:
        ds = data.get(did)
        if not ds:
            continue
        line = (next((L for L in ds["lines"] if L["label"] == lab), None) if lab
                else max(ds["lines"], key=lambda L: len(L["points"])))
        if not line:
            continue
        s = monthly_ff(line["points"])
        lvl = [val_at(s, ym) for ym, _ in meetings]
        dlt = [val_at(s, ym) - val_at(s, ym, 13) for ym, _ in meetings]
        r_lvl, n = spear(lvl, dec)
        r_dlt, _ = spear(dlt, dec)
        if not math.isnan(r_dlt) and (math.isnan(r_lvl) or abs(r_dlt) >= abs(r_lvl)):
            tname, r, vals = "Δ 1 an", r_dlt, dlt
        else:
            tname, r, vals = "Niveau", r_lvl, lvl
        if math.isnan(r):
            continue
        dfc = pd.DataFrame({"v": vals, "d": dec}).dropna()
        cond = lambda k: (round(float(dfc[dfc.d == k].v.mean()), 2) if (dfc.d == k).any() else None)
        out.append({"name": ds["name"] + (f" ({lab})" if lab else ""), "transform": tname,
                    "rho": r, "n": n, "hausse": cond(1), "statuquo": cond(0), "baisse": cond(-1),
                    "unit": ds["unit"], "decimals": ds["decimals"]})
    out.sort(key=lambda x: abs(x["rho"]), reverse=True)
    n_moves = sum(1 for _, d in meetings if d != 0)
    return {"rows": out, "n_meetings": len(meetings), "n_moves": n_moves}


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    data = build_data()
    html = (HTML
            .replace("__DATA__", json.dumps(data, ensure_ascii=False))
            .replace("__TAXO__", json.dumps(TAXONOMY, ensure_ascii=False))
            .replace("__CORR__", json.dumps(analyze_decisions(data), ensure_ascii=False)))
    FICHIER.write_text(html, encoding="utf-8")
    write_features(data)
    # Documents servis en telechargement depuis la page "La demarche".
    docs = {
        "Dispositif_informationnel_BAM.pdf": "dispositif-informationnel-bam.pdf",
        "ref_output_gap_hp.pdf": "ref-output-gap-hp.pdf",
        "ref_output_gap_fonction_production.pdf": "ref-output-gap-fonction-production.pdf",
        "ref_output_gap_chafik2017.pdf": "ref-output-gap-chafik-bam-2017.pdf",
    }
    for src_name, dest_name in docs.items():
        src = DATADIR / src_name
        if src.exists():
            shutil.copy(src, DEST / dest_name)
    print(f"\nOK -> {FICHIER}")


if __name__ == "__main__":
    main()
