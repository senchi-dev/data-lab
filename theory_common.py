"""Petits helpers HTML partages par theory_fr.py et theory_en.py (page "Theorie du modele")."""


def eq(s):
    return f'<div class="th-eq">{s}</div>'


def sym(items):
    """Liste de symboles : [(symbole, sens), ...] -> grille a deux colonnes."""
    rows = "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in items)
    return f'<dl class="th-sym">{rows}</dl>'


def call(kind, title, text):
    """Encadre : kind in {note, warn, key}."""
    return f'<div class="th-call th-{kind}"><b>{title}</b><p>{text}</p></div>'


def tbl(headers, rows):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="th-tbl"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def fill(html, c):
    """Remplace les jetons @@X@@ par les comptes reels calcules depuis Decisions_BAM.csv."""
    for k, v in c.items():
        html = html.replace(f"@@{k}@@", str(v))
    return html
