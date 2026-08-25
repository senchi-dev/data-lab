"""Narratifs d'analyse rédigés à la main, un par indicateur (partie « hybride »).
Expliquent les mouvements historiques réels. La phrase « lecture actuelle » et les
statistiques, elles, sont générées automatiquement (voir stats.py + le rendu).
Marqueur **gras** supporté ; paragraphes séparés par une ligne vide.
"""
NARRATIVES = {
    "bce":
        "Le taux directeur de la BCE raconte deux régimes. De mars 2016 à juillet 2022, le refi "
        "est resté collé à **0 %**, avec un taux de dépôt carrément **négatif** jusqu'à −0,50 %, "
        "l'ère des taux zéro née de la crise de la dette et d'une inflation trop basse. Puis le choc "
        "inflationniste post-Covid et la guerre en Ukraine ont déclenché, à partir de juillet 2022, "
        "la remontée la plus rapide de son histoire. Depuis 2014, c'est le **taux de dépôt** (et non "
        "le refi) qui pilote réellement les conditions monétaires de la zone euro.",
    "fed":
        "La cible de la Fed matérialise le cycle monétaire américain. Le pic d'avant-crise à 5,25 % "
        "(2006-2007) laisse place à la descente à 0-0,25 % en 2008, un long plancher, puis une brève "
        "normalisation avortée par le Covid (retour à zéro en 2020). Le resserrement 2022-2023, le "
        "plus violent depuis les années 1980, l'a hissée jusqu'à **5,50 %** pour casser l'inflation. "
        "Ce que fait la Fed déborde sur le Maroc via le change et les flux de capitaux.",
    "infl_us":
        "L'inflation américaine en glissement annuel. Sage autour de 2 % durant la décennie 2010, "
        "elle explose à **~9 % à l'été 2022** (relance budgétaire massive, chocs d'offre post-Covid, "
        "énergie), un sommet de 40 ans qui a déclenché le resserrement de la Fed. Son reflux "
        "progressif conditionne le rythme des baisses de taux à venir.",
    "infl_ze":
        "L'inflation de la zone euro (indice HICP). Longtemps trop basse, sous la cible, d'où les "
        "taux zéro de la BCE, elle bondit **au-delà de 10 % fin 2022** sous l'effet du choc "
        "énergétique lié à la guerre en Ukraine. Sa décrue pilote le calendrier d'assouplissement de "
        "la BCE, et donc indirectement la contrainte de change qui pèse sur BAM.",
    "eurusd":
        "La parité euro-dollar. Elle compte doublement pour le Maroc : le dirham est arrimé à un "
        "panier **~60 % euro / 40 % dollar**, et le pétrole se facture en dollars. Un dollar fort "
        "(euro faible) renchérit donc la facture énergétique marocaine même à baril inchangé. "
        "À croiser systématiquement avec le Brent pour lire l'inflation importée.",
    "brent":
        "Le prix du baril de Brent, référence de la facture pétrolière marocaine (importée). Ses "
        "flambées (2008, 2011-2014, 2022) se transmettent directement à l'inflation via l'énergie, "
        "les transports et les engrais. Le Maroc étant importateur net d'énergie, c'est l'un des "
        "principaux canaux d'**inflation subie**, que la politique monétaire ne contrôle pas.",
    "food":
        "L'indice FMI des prix alimentaires mondiaux. Le Maroc importe blé, huiles et sucre ; ses "
        "flambées (2008, 2011, et surtout **2022** avec la guerre en Ukraine) alimentent l'inflation "
        "alimentaire, un poste au poids très lourd dans le panier marocain. D'où le fait que "
        "l'inflation globale peut s'envoler alors que la sous-jacente reste sage.",
    "gepu":
        "L'indice mondial d'incertitude de politique économique. Il bondit à chaque choc majeur "
        "(2008, Brexit, guerre commerciale, Covid, Ukraine). C'est un proxy chiffré du critère "
        "**« incertitude internationale »** que BAM cite dans presque chaque communiqué et qu'aucune "
        "règle mécanique ne capture : une incertitude élevée pousse le Conseil au statu quo.",
    "monia":
        "Le taux interbancaire marocain au jour le jour. Il reste **collé au taux directeur de BAM** : "
        "ses cinq plus fortes variations correspondent exactement aux cinq décisions du Conseil "
        "(baisses Covid 2020, remontée 2022-2023). Le reste du temps il ne bouge que de quelques "
        "points de base ; ses écarts au directeur signalent des tensions de liquidité bancaire.",
    "inflation":
        "L'inflation marocaine, globale et sous-jacente. Longtemps faible (~1-2 %), la globale "
        "s'envole à **~10 % en 2022-2023**, tirée par l'alimentaire et l'énergie importés, pendant "
        "que la sous-jacente (core) monte moins fort. L'écart entre les deux mesure la part "
        "temporaire du choc ; c'est la **core** qui dit si l'inflation s'installe, la variable-reine "
        "que BAM cherche à ramener vers 2 %.",
    "pib":
        "La croissance du PIB réel marocain en glissement annuel. Le **« V » du Covid** domine : "
        "effondrement à −14 % au 2ᵉ trimestre 2020, rebond mécanique à +14 % un an plus tard. Hors "
        "ce choc, la croissance oscille autour de 3-4 %, avec une forte dépendance à la pluviométrie "
        "via l'agriculture. C'est le signal d'activité des pressions internes (Famille 2).",
    "output_gap":
        "L'écart entre le PIB observé et son potentiel, reconstruit par les **trois méthodes de BAM** "
        "(filtre HP, fonction de production, semi-structurel). À prendre comme un faisceau, pas comme "
        "une mesure : on se fie à sa direction (surchauffe si positif) et à la convergence des trois "
        "courbes, pas au niveau exact. Les tout derniers points sont incertains (biais de fin "
        "d'échantillon), la limite même de l'outil.",
    "output_gap_q":
        "La version trimestrielle de l'output gap, par simple filtre HP sur le PIB réel. Plus "
        "réactive que le trio annuel, donc plus utile pour anticiper une décision trimestrielle, "
        "mais aussi plus fragile : les derniers trimestres sont **fortement révisés** à mesure que "
        "de nouvelles données arrivent.",
    "ipai":
        "L'indice des prix des actifs immobiliers (base 100 en 2006). Le fait marquant : sur près de "
        "vingt ans il n'a **quasiment pas bougé en nominal** (~100-114), donc en termes réels, "
        "corrigés de l'inflation, les prix ont baissé. Conséquence pour la politique monétaire : le "
        "canal « effet de richesse immobilier » est faible au Maroc.",
    "m3":
        "Les agrégats monétaires mesurent la monnaie en circulation. **M3** (masse monétaire "
        "large) est passé d'environ 700 milliards de dirhams au milieu des années 2000 à plus de "
        "**2 000 milliards** aujourd'hui, une progression continue. En théorie monétaire, une "
        "croissance excessive de M3 précède l'inflation à moyen terme, ce que BAM surveille. Donnée "
        "annuelle, donc lente : un signal de fond, pas un timing.",
    "capi":
        "La capitalisation boursière totale de la Bourse de Casablanca, c'est la valeur de marché "
        "de toutes les actions cotées. Elle reflète l'appétit pour le risque et alimente un canal "
        "d'effet de richesse. Le marché marocain reste **étroit et concentré** (banques, télécoms "
        "et immobilier dominent), donc ce canal joue moins qu'ailleurs. Donnée annuelle.",
}
