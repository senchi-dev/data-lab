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
        "MONIA (Moroccan Overnight Index Average) est le taux auquel les banques marocaines se "
        "prêtent entre elles au jour le jour. Sa règle de vie est simple : il reste **collé au taux "
        "directeur de Bank Al-Maghrib**. Ses grands mouvements ne sont donc pas du hasard, ce sont "
        "les décisions du Conseil.\n\n"
        "**La détente Covid (2020).** BAM abaisse le directeur de 2,25 % à **2,00 % en mars 2020**, "
        "puis à **1,50 % en juin 2020** (une coupe de 50 points de base, exceptionnelle). MONIA "
        "plonge avec, jusqu'aux alentours de 1,4 %.\n\n"
        "**Le plateau 2021.** Statu quo à 1,50 %, MONIA reste plat : l'inflation d'alors est jugée "
        "surtout importée et temporaire.\n\n"
        "**Le resserrement 2022-2023.** Face à l'inflation, BAM remonte le directeur pour la première "
        "fois depuis 2008 : de 1,50 % à **2,00 % en septembre 2022**, **2,50 % en décembre 2022**, "
        "puis **3,00 % en mars 2023**. MONIA suit chaque marche et culmine autour de 3 %.\n\n"
        "**L'assouplissement 2024-2025.** L'inflation retombée, BAM enclenche des baisses : à partir "
        "de **septembre 2024**, trois coupes de 25 points de base ramènent le directeur de 3,00 % à "
        "**2,25 % en mars 2025**, niveau tenu depuis. MONIA redescend vers 2,2 %.\n\n"
        "**Le reste du temps**, MONIA ne bouge que de quelques points de base. Ses petits écarts au "
        "directeur sont le vrai signal à surveiller : ils trahissent des tensions de liquidité dans "
        "le système bancaire (déficit structurel que BAM comble par ses injections).",
    "inflation":
        "L'inflation marocaine se lit sur deux courbes : l'inflation **globale** (tout le panier) et "
        "l'inflation **sous-jacente** (core), qui retire les produits volatils (alimentaire frais, "
        "énergie, prix administrés) pour montrer la tendance de fond. Au Maroc, l'alimentaire pèse "
        "très lourd dans le panier, ce qui rend la globale bien plus nerveuse que la core.\n\n"
        "**Avant 2022**, l'inflation était faible et calme, souvent entre 0 et 2 %, avec des mois "
        "proches de zéro voire négatifs. La core restait remarquablement stable, signe d'une demande "
        "interne sans surchauffe.\n\n"
        "**Le choc 2022-2023.** La globale s'envole à **+6,6 % en moyenne en 2022**, puis atteint un "
        "**pic de 10,1 % en février 2023**, du jamais-vu depuis les années 1990. Le moteur est "
        "importé : flambée du blé et de l'énergie après l'invasion de l'Ukraine, doublée d'une "
        "sécheresse locale qui renchérit les produits frais. La core grimpe elle aussi, jusqu'à "
        "**5,9 % en 2023** : le choc, au départ alimentaire, s'était partiellement diffusé au reste "
        "des prix.\n\n"
        "**La désinflation 2024-2025.** Le reflux est brutal : la globale retombe à **+0,9 % en 2024** "
        "puis **+0,8 % en 2025**, et la core redescend à **+2,4 % en 2024**. Attention au piège : "
        "désinflation n'est pas déflation. Les prix ne baissent pas, ils montent seulement moins "
        "vite ; le niveau atteint en 2022-2023 reste en place, donc le pouvoir d'achat ne se "
        "reconstitue pas.\n\n"
        "**Pour BAM**, l'écart entre globale et core a servi à jauger la part temporaire du choc ; "
        "c'est la core, la tendance de fond, que le Conseil cherche à ramener vers 2 %. Son reflux a "
        "ouvert la voie au cycle de baisse des taux entamé en septembre 2024.",
    "pib":
        "La croissance du PIB réel en glissement annuel mesure le rythme de l'économie marocaine. Sa "
        "particularité : une forte dépendance à l'**agriculture**, elle-même dépendante de la "
        "**pluie**. Une bonne campagne gonfle la croissance, une sécheresse la plombe, "
        "indépendamment de la santé du reste de l'économie.\n\n"
        "**Avant 2020**, la croissance oscille autour de **3 à 4 %**, mais en dents de scie au gré "
        "des campagnes céréalières.\n\n"
        "**Le choc Covid (2020-2021).** Le confinement provoque un effondrement historique, jusqu'à "
        "**environ -14 % au 2e trimestre 2020**. Un an plus tard, l'économie rebondit mécaniquement "
        "à **environ +14 % au 2e trimestre 2021**, par simple effet de base (on compare à un point "
        "très bas). Ce grand V domine visuellement la courbe.\n\n"
        "**Depuis 2022**, retour à une croissance plus ordinaire, autour de **3 %**, mais bridée par "
        "des **sécheresses répétées** qui pèsent sur la valeur ajoutée agricole. Le non-agricole, "
        "lui, est plus stable.\n\n"
        "**Pour lire l'activité**, c'est le **PIB non-agricole** qu'il faut regarder : il reflète la "
        "vraie dynamique de la demande interne, celle qui crée des pressions inflationnistes, alors "
        "que la partie agricole n'est que du bruit météo pour la politique monétaire.",
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
