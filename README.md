# World Data — plateforme de données

Plateforme de visualisation : chaque indicateur = un **graphique interactif** + un panneau de
**statistiques descriptives** + une **analyse écrite**. Données récupérées en direct (FRED, API HCP,
API FMI) + fichiers locaux (BAM). Un seul fichier HTML autonome est généré, servi comme un site.

## Structure

```
build.py            générateur : fetch → stats → rend public/index.html
stats.py            statistiques descriptives (moyenne, volatilité, par année)
narratives.py       les analyses écrites (une par indicateur)
data/               fichiers locaux (MONIA, inflation, IPAI, output gap)
compute/            scripts de calcul de l'output gap (3 méthodes)
public/index.html   le site généré (servi par Vercel)
requirements.txt    dépendances Python
vercel.json         config d'hébergement (Vercel sert public/)
.github/workflows/  refresh quotidien automatique
```

## Lancer en local

```bash
cd ~/world-data
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python build.py          # → public/index.html
open public/index.html
```

La clé FRED est lue depuis la variable d'environnement `FRED_API_KEY`, sinon depuis
`config_api_fred.py` en local (ce fichier est **gitignoré**, jamais publié).

## Déployer (une seule fois)

1. **GitHub** — créer un dépôt (privé conseillé) et pousser :
   ```bash
   git remote add origin https://github.com/<toi>/world-data.git
   git branch -M main
   git push -u origin main
   ```
2. **Secret GitHub** — dépôt → Settings → Secrets and variables → Actions → New secret :
   `FRED_API_KEY` = ta clé FRED.
3. **Vercel** — vercel.com → Add New → Project → importer le dépôt →
   Framework Preset **Other**, Output Directory **public**, Build Command **vide** → Deploy.
   → tu obtiens une URL publique (ouvrable sur téléphone, partageable).

## Refresh quotidien (automatique)

Le workflow `.github/workflows/refresh.yml` s'exécute chaque jour (~07:30 Maroc) :
il relance `build.py` (données FRED/HCP/IMF fraîches) et committe `public/`. Vercel redéploie
tout seul au commit. **Aucune dépendance à ton Mac.** Tu peux aussi le lancer à la main :
onglet Actions → Refresh data → Run workflow.

Les fichiers BAM (`data/*.xlsx`) n'ont pas d'API : re-déposer le fichier et committer quand BAM
en publie un nouveau (mensuel/trimestriel).

## Ajouter une donnée

1. Ajouter l'entrée dans `build.py` (série FRED/HCP) ou déposer un fichier dans `data/`.
2. Écrire son analyse dans `narratives.py`.
3. `python build.py` → vérifier → committer.

## Sécurité

- Les clés API ne sont **jamais** dans le dépôt (`config_api_*.py` gitignorés ; en prod, secrets
  GitHub/Vercel).
- Le site est public (données économiques publiques). Pour le protéger : Vercel → Settings →
  Deployment Protection (mot de passe).
