"""Assemble la page "Theorie du modele" (FR + EN) a partir des modules de texte."""
import theory_en, theory_en2, theory_en3, theory_fr, theory_fr2, theory_fr3
from theory_common import fill


def _pack(head, parts, counts):
    secs = []
    for part in parts:
        for sid, title, html in part():
            secs.append({"id": sid, "title": title, "html": fill(html, counts)})
    return {"kicker": head.KICKER, "title": head.TITLE, "lead": head.LEAD, "sections": secs}


def build_theory(counts):
    return {
        "fr": _pack(theory_fr, [theory_fr.part1, theory_fr2.part2, theory_fr3.part3], counts),
        "en": _pack(theory_en, [theory_en.part1, theory_en2.part2, theory_en3.part3], counts),
    }
