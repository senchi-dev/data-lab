"""Output gap — 3e methode de BAM : modele semi-structurel (filtre multivarie de Blagrave/FMI).
Filtre de Kalman + lisseur RTS, parametres estimes par BAM (Chafik 2017, Annexe II, Tableau 6).
Etats : [ybar (PIB potentiel), g (croissance tendancielle), gap (output gap), Ubar (NAIRU)].
Observations : PIB (identite Y=ybar+gap), courbe de Phillips (inflation), loi d'Okun (chomage).
Sources : PIB reel, inflation, chomage = FMI/WEO.
"""
import csv
import json
from pathlib import Path

import numpy as np

WEO = "/private/tmp/claude-501/-Users-mwn-Documents-Claude-Workspace/1cb7f1a3-2d76-4ebe-80e3-7a4559945b90/scratchpad/weo_mss.json"
CSV = Path("/Users/mwn/Documents/Modèle anticipation décisions BAM/Output_gap.csv")

# --- parametres estimes par BAM (annuel, Tableau 6) ---
THETA, GSS = 0.019, 4.0        # croissance potentielle : retour vers 4%
PHI = 0.169                    # persistance de l'output gap
LAM, BETA = 0.253, 0.125       # courbe de Phillips (poids forward + pente)
TAU1 = 0.128                   # loi d'Okun (pente)
S_YBAR, S_G, S_GAP, S_UBAR = 0.200, 0.204, 1.010, 0.098   # ecarts-types des chocs d'etat
S_PI, S_U = 1.065, 0.501       # ecarts-types de mesure (Phillips, Okun)
S_Y = 1e-3                     # identite PIB quasi-exacte


def load_weo():
    d = json.load(open(WEO))["data"]
    times = [v["value"] for v in d["structures"][0]["dimensions"]["observation"][0]["values"]]
    sd = d["structures"][0]["dimensions"]["series"]
    ip = [i for i, x in enumerate(sd) if x["id"] == "INDICATOR"][0]
    iv = [v["id"] for v in sd[ip]["values"]]
    out = {}
    for k, s in d["dataSets"][0]["series"].items():
        code = iv[int(k.split(":")[ip])]
        out[code] = {int(times[int(i)]): float(o[0]) for i, o in s["observations"].items() if o[0] is not None}
    return out


def main():
    w = load_weo()
    yrs = [y for y in sorted(set(w["NGDP_R"]) & set(w["PCPIPCH"])) if y <= 2025]
    gdp = np.array([w["NGDP_R"][y] for y in yrs])
    pi = np.array([w["PCPIPCH"][y] for y in yrs])
    lur = w["LUR"]

    yy = 100 * (np.log(gdp) - np.log(gdp[0]))     # PIB en log x100 (demarre a 0)
    n = len(yrs)

    # matrices de transition
    T = np.array([[1, 1, 0, 0],
                  [0, 1 - THETA, 0, 0],
                  [0, 0, PHI, 0],
                  [0, 0, 0, 1.0]])
    c = np.array([0, THETA * GSS, 0, 0.0])
    Q = np.diag([S_YBAR**2, S_G**2, S_GAP**2, S_UBAR**2])

    # observations par periode : (vecteur z, matrice Z, matrice R)
    def obs_t(t):
        z, Zr, r = [yy[t]], [[1, 0, 1, 0]], [S_Y**2]                        # PIB
        if 0 < t < n - 1:                                                    # Phillips (forward-looking)
            zt = pi[t] - LAM * pi[t + 1] - (1 - LAM) * pi[t - 1]
            z.append(zt); Zr.append([0, 0, BETA, 0]); r.append(S_PI**2)
        if yrs[t] in lur:                                                    # Okun
            z.append(lur[yrs[t]]); Zr.append([0, 0, -TAU1, 1]); r.append(S_U**2)
        return np.array(z), np.array(Zr, float), np.diag(r)

    # etat initial
    a = np.array([0.0, GSS, 0.0, lur.get(yrs[0], 10.0)])
    P = np.diag([1.0, 4.0, 25.0, 9.0])

    # --- filtre de Kalman (avant) ---
    ap, Pp, af, Pf = [], [], [], []
    for t in range(n):
        a_pred = T @ a + c
        P_pred = T @ P @ T.T + Q
        ap.append(a_pred); Pp.append(P_pred)
        z, Z, R = obs_t(t)
        S = Z @ P_pred @ Z.T + R
        K = P_pred @ Z.T @ np.linalg.inv(S)
        a = a_pred + K @ (z - Z @ a_pred)
        P = (np.eye(4) - K @ Z) @ P_pred
        af.append(a); Pf.append(P)

    # --- lisseur RTS (arriere) ---
    aS = [None] * n; aS[-1] = af[-1]
    PS = [None] * n; PS[-1] = Pf[-1]
    for t in range(n - 2, -1, -1):
        C = Pf[t] @ T.T @ np.linalg.inv(Pp[t + 1])
        aS[t] = af[t] + C @ (aS[t + 1] - ap[t + 1])
        PS[t] = Pf[t] + C @ (PS[t + 1] - Pp[t + 1]) @ C.T

    gap_mss = np.array([aS[t][2] for t in range(n)])

    # comparer aux 2 autres methodes (lues dans le CSV existant)
    hp, fdp = {}, {}
    for row in csv.DictReader(open(CSV)):
        y = int(row["annee"])
        if row.get("gap_hp"): hp[y] = float(row["gap_hp"])
        if row.get("gap_fdp"): fdp[y] = float(row["gap_fdp"])

    print(f"{'Annee':6}{'HP':>8}{'FDP':>8}{'MSS':>8}")
    for t, y in enumerate(yrs):
        print(f"{y:6}{hp.get(y,float('nan')):8.2f}{fdp.get(y,float('nan')):8.2f}{gap_mss[t]:8.2f}")

    comm = [y for y in yrs if y in hp and y in fdp]
    g_mss = np.array([gap_mss[yrs.index(y)] for y in comm])
    g_hp = np.array([hp[y] for y in comm]); g_fdp = np.array([fdp[y] for y in comm])
    print(f"\n--- Convergence (3 methodes, {comm[0]}-{comm[-1]}) ---")
    print(f"corr MSS-HP : {np.corrcoef(g_mss,g_hp)[0,1]:.3f} | corr MSS-FDP : {np.corrcoef(g_mss,g_fdp)[0,1]:.3f} | corr HP-FDP : {np.corrcoef(g_hp,g_fdp)[0,1]:.3f}")

    # reecrire le CSV avec la 3e colonne
    mss = {y: gap_mss[t] for t, y in enumerate(yrs)}
    allyrs = sorted(set(hp) | set(fdp) | set(mss))
    lines = ["annee,gap_hp,gap_fdp,gap_mss"]
    for y in allyrs:
        lines.append(f"{y},{hp.get(y,'')},{fdp.get(y,'')},{('%.3f'%mss[y]) if y in mss else ''}")
    # conserver les valeurs hp/fdp au format d'origine
    CSV.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nCSV mis a jour (3 colonnes) -> {CSV}")


if __name__ == "__main__":
    main()
