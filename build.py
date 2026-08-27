"""Genere un dashboard HTML autonome (World_Data_Dashboard.html) a partir des series FRED.
- Sidebar cliquable (une donnee = une entree)
- Graphique SVG interactif fait main (zero dependance externe)
- Granularite Mensuel / Trimestriel / Annuel (agregation cote client)
- Tooltip au survol : date + valeur exacte du point
Donnees mensuelles calees sur 2006 (debut des decisions BAM), embarquees en JSON.
"""
import json
import os
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
# Exports recents (un ou plusieurs) : tout data/Taux_debiteurs_*.csv est fusionne automatiquement.

OBS = "https://api.stlouisfed.org/fred/series/observations"
DEBUT = "2006-01-01"

DEST = ROOT / "public"
FICHIER = DEST / "index.html"

BLEU, ORANGE, VERT = "#2563a8", "#e07b39", "#2e9e6b"
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
         "source": "Enquête mensuelle BAM (400 entreprises industrielles)", "ids": []},
        {"name": "Anticipations d'inflation",
         "source": "Enquête trimestrielle BAM auprès des experts du système financier", "ids": []},
        {"name": "Marché immobilier (transactions, prix, indice IPAI)",
         "source": "ANCFCC (Conservation Foncière) · Bank Al-Maghrib", "ids": ["ipai"]},
        {"name": "Comptes nationaux (croissance, PIB, investissement, consommation)",
         "source": "HCP · Direction de la comptabilité nationale (API BDS, I4276)", "ids": ["pib"]},
        {"name": "Output gap (construit, 3 méthodes de BAM)",
         "source": "Construit : filtre HP + fonction de production + semi-structurel · données FMI/WEO & HCP · méthode Chafik/BAM 2017", "ids": ["output_gap", "output_gap_q"]},
        {"name": "Marché du travail (emploi, chômage, taux d'activité)",
         "source": "HCP", "ids": []},
        {"name": "Prix à la consommation, inflation globale, prix à la production",
         "source": "HCP (inflation globale) · Bank Al-Maghrib (inflation sous-jacente)", "ids": ["inflation"]},
        {"name": "Production industrielle, énergétique et minière",
         "source": "HCP", "ids": []},
        {"name": "Indice de confiance des ménages",
         "source": "HCP", "ids": []},
        {"name": "Finances publiques et loi de finances",
         "source": "Ministère de l'Économie et des Finances", "ids": []},
        {"name": "Pluviométrie et couvert végétal (production céréalière)",
         "source": "Direction de la Météorologie Nationale · Centre Royal de Télédétection Spatiale", "ids": []},
        {"name": "Production agricole (céréalière et hors céréalière)",
         "source": "Ministère de l'Agriculture", "ids": []},
        {"name": "Comptes extérieurs (balance des paiements)",
         "source": "Office des Changes", "ids": []},
    ]},
]


HTML = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Data Lab</title>
<style>
  :root{
    --bg:#f6f7f9; --panel:#ffffff; --ink:#1a1d21; --muted:#6b7280;
    --line:#e6e8eb; --accent:#2563a8; --accent-soft:#eaf1f9;
  }
  @media (prefers-color-scheme: dark){
    :root{ --bg:#14171b; --panel:#1c2026; --ink:#e8eaed; --muted:#9aa2ad;
           --line:#2b3038; --accent:#5b9bd5; --accent-soft:#22303f; }
  }
  *{ box-sizing:border-box; }
  body{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
        background:var(--bg); color:var(--ink); }
  .app{ display:grid; grid-template-columns:288px 1fr; height:100vh; }
  aside{ background:var(--panel); border-right:1px solid var(--line); padding:22px 16px;
         overflow-y:auto; min-height:0; }
  aside h1{ font-size:15px; letter-spacing:.02em; margin:0 4px 4px; }
  aside .sub{ font-size:11.5px; color:var(--muted); margin:0 4px 18px; }
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
  .item.pending{ color:var(--muted); }
  .dotstat{ width:7px; height:7px; border-radius:50%; flex:0 0 auto; margin-top:6px; }
  .dotstat.on{ background:var(--accent); }
  .dotstat.off{ border:1.5px solid var(--muted); }
  .item.active .dotstat.on{ background:#fff; }
  .ilab{ flex:1; }
  #source{ color:var(--muted); font-size:11.5px; margin-top:5px; }
  #placeholder{ display:none; background:var(--panel); border:1px dashed var(--line);
        border-radius:14px; padding:40px 28px; text-align:center; color:var(--muted); margin-top:12px; }
  #placeholder .big{ font-size:15px; color:var(--ink); margin-bottom:8px; }
  #placeholder .src2{ font-size:13px; margin-top:14px; }
  #placeholder b{ color:var(--ink); }
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
    <h1>Data Lab</h1>
    <p class="sub">Données macro &amp; marchés · graphiques, statistiques et analyses</p>
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
    <div id="placeholder">
      <div class="big">Donnée pas encore collectée</div>
      <div>Cette rubrique fait partie du dispositif informationnel de BAM, mais nous ne l'avons pas encore intégrée au dashboard.</div>
      <div class="src2">Source officielle : <b id="ph-src"></b></div>
    </div>
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
  for(const sec of TAXO){
    const wrap=document.createElement("div"); wrap.className="section";
    const hd=document.createElement("button"); hd.className="section-hd";
    hd.innerHTML=`<span class="chev">▼</span><span>${sec.section}</span>`;
    hd.onclick=()=>wrap.classList.toggle("collapsed");
    const body=document.createElement("div"); body.className="section-body";

    // On separe les rubriques Disponibles (avec donnees) des rubriques A venir.
    const avail=[], soon=[];
    for(const topic of sec.topics){ (topic.ids && topic.ids.length ? avail : soon).push(topic); }

    if(avail.length){
      const h=document.createElement("div"); h.className="navcat"; h.textContent="Disponibles"; body.appendChild(h);
      for(const topic of avail) for(const id of topic.ids){
        const b=document.createElement("button"); b.className="item"; b.dataset.id=id;
        b.innerHTML=`<span class="dotstat on"></span><span class="ilab">${DATA[id].name}</span>`;
        b.onclick=()=>selectSeries(id, topic.source);
        body.appendChild(b);
      }
    }
    if(soon.length){
      const h=document.createElement("div"); h.className="navcat soon"; h.textContent="À venir"; body.appendChild(h);
      for(const topic of soon){
        const b=document.createElement("button"); b.className="item pending"; b.dataset.ph=topic.name;
        b.innerHTML=`<span class="dotstat off"></span><span class="ilab">${topic.name}</span>`;
        b.onclick=()=>selectPlaceholder(topic);
        body.appendChild(b);
      }
    }
    wrap.appendChild(hd); wrap.appendChild(body); nav.appendChild(wrap);
  }
}
function syncNav(){
  document.querySelectorAll(".item").forEach(b=>b.classList.toggle("active", b.dataset.id===state.id && state.id!=null));
}
function showChartUI(on){
  for(const el of ["controls","cmpbar","card","stats-hd","stats","statstable","ana-hd","analysis","foot"]) document.getElementById(el).style.display = on?"":"none";
  document.getElementById("placeholder").style.display = on?"none":"block";
}
function selectSeries(id, source){ state.id=id; state.source=source; syncNav(); refresh(); }
function selectPlaceholder(topic){
  state.id=null; syncNav();
  document.getElementById("title").textContent=topic.name;
  document.getElementById("unit").textContent="";
  document.getElementById("source").textContent="Source : "+topic.source;
  document.getElementById("ph-src").textContent=topic.source;
  showChartUI(false);
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
  document.getElementById("foot").textContent = "Survole un point pour la date et la valeur exacte. " + (m.note || "");
  showChartUI(true);
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

state.source = TAXO[0].topics[0].source;   // source de la 1re rubrique (international)
buildNav(); syncNav(); refresh();
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


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    data = build_data()
    html = (HTML
            .replace("__DATA__", json.dumps(data, ensure_ascii=False))
            .replace("__TAXO__", json.dumps(TAXONOMY, ensure_ascii=False)))
    FICHIER.write_text(html, encoding="utf-8")
    write_features(data)
    print(f"\nOK -> {FICHIER}")


if __name__ == "__main__":
    main()
