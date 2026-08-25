"""Statistiques descriptives d'une serie temporelle {période: valeur}.
Calculees au build (sur la frequence native), embarquees dans le HTML.
Reprend la logique de l'analyse MONIA : niveau + volatilite (ecart-type des variations) + par annee.
"""
import numpy as np


def _year(key):
    return key.split("-")[0]


def compute_stats(points):
    """points : dict {'YYYY-MM': valeur}. Renvoie un bloc de stats, ou None si vide."""
    keys = sorted(points)
    if not keys:
        return None
    vals = np.array([points[k] for k in keys], dtype=float)
    diffs = np.diff(vals)

    block = {
        "n": int(len(vals)),
        "mean": float(np.mean(vals)),
        "median": float(np.median(vals)),
        "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
        "min": float(np.min(vals)),
        "max": float(np.max(vals)),
        "range": float(vals.max() - vals.min()),
        "vol": float(np.std(diffs, ddof=1)) if len(diffs) > 1 else 0.0,
        "last": {"value": float(vals[-1]), "key": keys[-1]},
        "first_key": keys[0],
    }

    # decomposition par annee
    by = {}
    for k, v in zip(keys, vals):
        by.setdefault(_year(k), []).append(v)
    per = []
    for y in sorted(by):
        arr = np.array(by[y], dtype=float)
        d = np.diff(arr)
        per.append({
            "period": y,
            "n": int(len(arr)),
            "mean": float(np.mean(arr)),
            "min": float(arr.min()),
            "max": float(arr.max()),
            "vol": float(np.std(d, ddof=1)) if len(d) > 1 else 0.0,
        })
    block["by_period"] = per
    return block
