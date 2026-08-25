"""Output gap marocain — 2 approches de BAM (Chafik 2017), en annuel.
  1) Filtre HP sur le PIB reel (lambda=100).
  2) Fonction de production Cobb-Douglas : gap = (1-a)*(travail - travail potentiel) + (PGF - PGF tendance).
     Capital actuel (il s'annule entre Y et Y*), travail potentiel = pop x participation tendancielle x (1-NAIRU).
Sources : PIB reel, investissement, population, chomage = FMI/WEO ; taux d'activite = HCP (API BDS).
"""
import json
import numpy as np
import requests

ALPHA = 0.35
DELTA = 0.10
LAMBDA = 100
WEO = "/private/tmp/claude-501/-Users-mwn-Documents-Claude-Workspace/1cb7f1a3-2d76-4ebe-80e3-7a4559945b90/scratchpad/weo_mar.json"
HCP = "https://bds.hcp.ma/api/v1/indicators"


def num(v):
    if v in (None, ""):
        return None
    return float(str(v).replace("\xa0", "").replace(" ", "").replace(",", "."))


def load_weo():
    d = json.load(open(WEO))["data"]
    st = d["structures"][0]
    times = [v["value"] for v in st["dimensions"]["observation"][0]["values"]]
    sdims = st["dimensions"]["series"]
    ipos = [i for i, dd in enumerate(sdims) if dd["id"] == "INDICATOR"][0]
    ivals = [v["id"] for v in sdims[ipos]["values"]]
    out = {}
    for key, s in d["dataSets"][0]["series"].items():
        code = ivals[int(key.split(":")[ipos])]
        out[code] = {int(times[int(i)]): float(o[0]) for i, o in s["observations"].items() if o[0] is not None}
    return out


def hcp_series(code, key_fn):
    j = requests.get(f"{HCP}/{code}", timeout=20).json()
    out = {}
    for p in j["periods"]:
        try:
            y = int(p)
        except ValueError:
            continue
        cell = j["data"].get(key_fn(p))
        if cell and num(cell["value"]) is not None:
            out[y] = num(cell["value"])
    return out


def hp_trend(y, lam=LAMBDA):
    y = np.asarray(y, float)
    n = len(y)
    D = np.zeros((n - 2, n))
    for i in range(n - 2):
        D[i, i], D[i, i + 1], D[i, i + 2] = 1.0, -2.0, 1.0
    return np.linalg.solve(np.eye(n) + lam * D.T @ D, y)


def main():
    w = load_weo()
    gdp_r, gdp_n, defl = w["NGDP_R"], w["NGDP"], w["NGDP_D"]
    inv_sh, lur, pop = w["NID_NGDP"], w["LUR"], w["LP"]
    act = hcp_series("I40", lambda p: f"24.27_{p}")     # taux d'activite national, total (%)
    print("Annees taux d'activite (I40):", sorted(act))

    # ================= PHASE 1 : filtre HP sur tout le PIB reel =================
    yrs_hp = sorted(y for y in gdp_r if y <= 2025)
    Yf = np.array([gdp_r[y] for y in yrs_hp])
    gap_hp_full = 100 * (np.log(Yf) - hp_trend(np.log(Yf)))
    print(f"\n[PHASE 1 - HP] {yrs_hp[0]}-{yrs_hp[-1]} ({len(yrs_hp)} ans) | gap 2025 = {gap_hp_full[-1]:.2f}%")

    # ================= PHASE 2 : fonction de production =================
    yrs = [y for y in sorted(set(gdp_r) & set(gdp_n) & set(defl) & set(inv_sh) & set(lur) & set(pop) & set(act)) if y <= 2025]
    print(f"[PHASE 2 - FDP] echantillon commun : {yrs[0]}-{yrs[-1]} ({len(yrs)} ans)")

    Y = np.array([gdp_r[y] for y in yrs])
    I = np.array([inv_sh[y] / 100 * gdp_n[y] for y in yrs]) / (np.array([defl[y] for y in yrs]) / 100)
    u = np.array([lur[y] / 100 for y in yrs])
    P = np.array([pop[y] for y in yrs])
    a = np.array([act[y] / 100 for y in yrs])

    # capital (inventaire perpetuel)
    g = np.mean(np.diff(np.log(Y)))
    K = np.empty(len(yrs)); K[0] = I[0] / (g + DELTA)
    for t in range(1, len(yrs)):
        K[t] = (1 - DELTA) * K[t - 1] + I[t]

    # travail actuel vs potentiel (participation tendancielle + NAIRU)
    L = P * a * (1 - u)
    a_star = hp_trend(a); u_star = hp_trend(u)
    L_star = P * a_star * (1 - u_star)

    # PGF (residu de Solow) et sa tendance
    logA = np.log(Y) - ALPHA * np.log(K) - (1 - ALPHA) * np.log(L)
    logA_star = hp_trend(logA)

    # PIB potentiel : capital ACTUEL, travail potentiel, PGF tendancielle
    logY_star = ALPHA * np.log(K) + (1 - ALPHA) * np.log(L_star) + logA_star
    gap_fdp = 100 * (np.log(Y) - logY_star)

    # HP sur la meme fenetre pour comparer
    gap_hp = 100 * (np.log(Y) - hp_trend(np.log(Y)))

    print(f"\n{'Annee':6} {'Gap HP':>9} {'Gap FDP':>9}")
    for i, y in enumerate(yrs):
        print(f"{y:6} {gap_hp[i]:9.2f} {gap_fdp[i]:9.2f}")

    corr = np.corrcoef(gap_hp, gap_fdp)[0, 1]
    mad = np.mean(np.abs(gap_hp - gap_fdp))
    print(f"\n--- Convergence ---\nCorrelation HP vs FDP : {corr:.3f}\nEcart absolu moyen    : {mad:.2f} points")

    # sauvegarde CSV pour le dashboard : HP (echantillon complet) + FDP (1998+)
    from pathlib import Path
    fdp = {y: gap_fdp[i] for i, y in enumerate(yrs)}
    dest = Path("/Users/mwn/Documents/Modèle anticipation décisions BAM/Output_gap.csv")
    lignes = ["annee,gap_hp,gap_fdp"]
    for i, y in enumerate(yrs_hp):
        lignes.append(f"{y},{gap_hp_full[i]:.3f},{fdp[y]:.3f}" if y in fdp else f"{y},{gap_hp_full[i]:.3f},")
    dest.write_text("\n".join(lignes), encoding="utf-8")
    print(f"\nCSV -> {dest}")


if __name__ == "__main__":
    main()
