"""Page 'Theorie du modele' : texte francais, partie 2 (probabilites, inference, series temporelles, modele logistique)."""
from theory_common import eq, sym, call, tbl


def part2():
    out = []

    out.append(("prob", "5. Fondations en probabilités", (
        "<p>La sortie du modèle est une probabilité, il faut donc savoir exactement ce qu'est une probabilité.</p>"
        "<h4>5.1 Variables aléatoires et lois</h4>"
        "<p>Une <b>variable aléatoire</b> est une quantité dont la valeur n'est pas connue à l'avance, comme la prochaine décision. Sa <b>loi</b> liste les valeurs possibles et la vraisemblance de chacune. "
        "Une probabilité P(A) est un nombre de 0 (impossible) à 1 (certain). L'historique donne une loi grossière : statu quo @@HOLDPCT@@ %, baisses et hausses se partageant le reste.</p>"
        "<h4>5.2 Bernoulli et binomiale</h4>"
        "<p>Une variable de <b>Bernoulli</b> est un essai oui/non de probabilité de succès <i>p</i> : une réunion se termine par un mouvement (1) ou non (0). "
        "Une loi <b>binomiale</b> compte les succès sur <i>n</i> essais indépendants ; la probabilité d'avoir exactement <i>k</i> mouvements sur <i>n</i> réunions est :</p>"
        + eq("P(K = k) = C(n, k) &middot; p<sup>k</sup> &middot; (1 &minus; p)<sup>n&minus;k</sup>      avec C(n, k) = n! / ( k! &middot; (n &minus; k)! )")
        + "<p>Ici n! (factorielle de n) vaut n &times; (n&minus;1) &times; ... &times; 1. La binomiale suppose des essais indépendants ; les mouvements viennent par séries, c'est donc une approximation, mais utile pour dimensionner l'incertitude.</p>"
        "<h4>5.3 Espérance, variance, écart-type</h4>"
        + eq("E[X] = &Sigma; x &middot; P(X = x)            Var(X) = E[ (X &minus; E[X])<sup>2</sup> ]            &sigma; = &radic;Var(X)")
        + sym([("&Sigma;", "somme sur toutes les valeurs possibles"), ("E[X]", "espérance : la moyenne de long terme de X"),
               ("Var(X)", "variance : carré moyen de l'écart à la moyenne"), ("&sigma;", "écart-type : écart typique à la moyenne, dans les unités de X")])
        + "<p>Pour une variable de Bernoulli : E = p et Var = p(1 &minus; p). Avec p = @@MOVES@@/@@N@@, l'oscillation typique d'un résultat oui/non est grande par rapport à sa moyenne : c'est ce que « événement rare » veut dire.</p>"
        "<h4>5.4 Probabilité conditionnelle, indépendance, Bayes</h4>"
        + eq("P(A | B) = P(A et B) / P(B)")
        + "<p>Lire P(A | B) comme « la probabilité de A une fois qu'on sait que B est vrai ». La sortie d'un modèle est exactement cela : <i>P(baisse | ce que l'on sait avant la réunion)</i>. "
          "A et B sont <b>indépendants</b> si savoir B n'apprend rien sur A. Les décisions de taux ne sont pas indépendantes entre elles (un mouvement rend un autre plus probable), et cela compte en section 7.</p>"
          "<p>Le <b>théorème de Bayes</b> retourne une probabilité conditionnelle et exprime comment actualiser une croyance avec une preuve :</p>"
        + eq("P(A | B) = P(B | A) &middot; P(A) / P(B)")
        + sym([("P(A)", "a priori : croyance avant la preuve (par exemple le taux de base d'une baisse)"), ("P(B | A)", "vraisemblance : fréquence de la preuve quand A est vrai"),
               ("P(A | B)", "a posteriori : la croyance actualisée")])
        + call("note", "Illustratif", "Supposons que les baisses surviennent au taux de base de 13 %, et qu'une inflation sous-jacente faible soit observée avant 80 % des baisses mais avant seulement 30 % des autres réunions. "
               "P(faible) = 0,80&times;0,13 + 0,30&times;0,87 = 0,365, donc P(baisse | faible) = 0,80&times;0,13 / 0,365 &asymp; <b>28 %</b>. La preuve fait plus que doubler la probabilité, et pourtant une baisse reste moins probable que le contraire. Les probabilités d'événements rares restent modestes même avec de bonnes preuves.")
    )))

    out.append(("infer", "6. Inférence statistique et corrélation", (
        "<h4>6.1 Estimer à partir d'un échantillon</h4>"
        "<p>Les @@N@@ réunions sont un <b>échantillon</b> d'un processus sous-jacent. Tout nombre calculé dessus (une moyenne, une corrélation, un coefficient) est une <b>estimation</b> qui changerait avec un autre échantillon. "
        "Quantifier cette oscillation est le travail de l'inférence.</p>"
        + eq("x&#772; = (1/n) &middot; &Sigma; x<sub>i</sub>            s<sup>2</sup> = (1/(n &minus; 1)) &middot; &Sigma; (x<sub>i</sub> &minus; x&#772;)<sup>2</sup>            ES(p&#770;) = &radic;( p&#770;(1 &minus; p&#770;) / n )")
        + sym([("x&#772;", "moyenne de l'échantillon"), ("s<sup>2</sup>", "variance de l'échantillon (division par n&minus;1 et non n pour éviter de la sous-estimer)"),
               ("p&#770;", "proportion estimée ; le chapeau signifie « estimé à partir des données »"), ("ES", "erreur standard : taille typique de l'oscillation de l'estimation d'un échantillon à l'autre")])
        + "<h4>6.2 Intervalles de confiance</h4>"
          "<p>Un intervalle de confiance à 95 % est une plage construite pour que, sur des échantillons répétés, 95 % de ces plages contiennent la vraie valeur. La version simple est estimation &plusmn; 1,96 &times; ES. "
          "Pour de petits effectifs, on utilise l'intervalle exact (Clopper-Pearson). <b>Exemple :</b> si un modèle repère 6 des 14 vrais mouvements, le rappel est de 43 %, mais l'intervalle exact à 95 % va d'environ <b>18 % à 71 %</b>. "
          "Avec si peu d'événements, <i>l'intervalle est le résultat</i> ; l'estimation seule est trompeuse.</p>"
          "<h4>6.3 Tests d'hypothèse et p-valeurs</h4>"
          "<p>Un test part d'une <b>hypothèse nulle</b> (il ne se passe rien, par exemple « cet input n'a aucun lien avec la décision ») et demande à quel point les données seraient surprenantes si elle était vraie. "
          "La <b>p-valeur</b> est cette probabilité. Une p-valeur petite (sous 0,05 par convention) signifie « surprenant sous l'hypothèse nulle ». Ce n'est <b>pas</b> la probabilité que le modèle ait raison, et elle ne mesure ni la taille ni l'utilité d'un effet.</p>"
          "<h4>6.4 Corrélation de Pearson</h4>"
        + eq("r = &Sigma; (x<sub>i</sub> &minus; x&#772;)(y<sub>i</sub> &minus; y&#772;) / &radic;( &Sigma; (x<sub>i</sub> &minus; x&#772;)<sup>2</sup> &middot; &Sigma; (y<sub>i</sub> &minus; y&#772;)<sup>2</sup> )")
        + "<p>r va de &minus;1 (mouvement exactement opposé) à +1 (mouvement exactement identique) et mesure <b>uniquement la co-variation linéaire</b>. C'est ce que montre la page Corrélation. Trois précautions :</p>"
          "<ul>"
          "<li><b>Taille d'échantillon.</b> Pour se distinguer de zéro au seuil de 5 %, |r| doit dépasser environ <b>0,35 pour n = 32</b> (la série d'inflation) et environ <b>0,23 pour n = 76</b>. Un r modeste sur une série courte est facilement du bruit.</li>"
          "<li><b>Tests multiples.</b> Tester m inputs au seuil de 5 % produit environ 0,05 &times; m fausses découvertes par hasard. Le correctif de Bonferroni teste chacun à 0,05/m. La meilleure ligne d'un classement est la plus susceptible d'être un hasard.</li>"
          "<li><b>Corrélation n'est pas causalité.</b> Deux séries peuvent évoluer ensemble à cause d'un troisième facteur ou d'une tendance commune (section 7). C'est la théorie (sections 2 à 4), pas r, qui justifie d'inclure une variable.</li>"
          "</ul>"
        + call("key", "Conséquence pour ce projet",
               "La page Corrélation est un <b>outil d'exploration</b>. L'utiliser pour choisir les inputs finaux puis tester le modèle sur le même historique est circulaire. La sélection doit être refaite à l'intérieur de chaque fenêtre d'apprentissage (section 11).")
    )))

    out.append(("ts", "7. Séries temporelles : stationnarité, décalages et fuite d'information", (
        "<p>Les données économiques ont de la mémoire, ce qui crée des pièges que la statistique ordinaire ne signale pas.</p>"
        "<h4>7.1 Stationnarité</h4>"
        "<p>Une série est <b>stationnaire</b> si sa moyenne et sa dispersion ne dérivent pas dans le temps. Les niveaux de prix ont une tendance haussière (non stationnaires) ; leurs <i>variations</i> souvent non. "
        "Le test de <b>Dickey-Fuller augmenté</b> recherche une <b>racine unitaire</b>, un comportement d'errance sans rappel vers une moyenne :</p>"
        + eq("&Delta;y<sub>t</sub> = &alpha; + &gamma;&middot;y<sub>t&minus;1</sub> + &Sigma;<sub>k</sub> &delta;<sub>k</sub>&middot;&Delta;y<sub>t&minus;k</sub> + &epsilon;<sub>t</sub>            hypothèse nulle : &gamma; = 0 (racine unitaire)")
        + "<p>Si la statistique de test est plus négative que la valeur critique (environ &minus;1,95 à 5 % sans constante), la racine unitaire est rejetée et la série est stationnaire. "
          "Une série qui devient stationnaire après une différenciation (&Delta;y<sub>t</sub> = y<sub>t</sub> &minus; y<sub>t&minus;1</sub>) est dite <b>intégrée d'ordre 1, I(1)</b> ; une série déjà stationnaire est I(0).</p>"
          "<h4>7.2 Régression fallacieuse</h4>"
          "<p>Deux séries sans rapport qui ont toutes deux une tendance montrent une forte corrélation, simplement parce que les deux montent. Régresser l'une sur l'autre produit une relation « significative » qui n'existe pas. "
          "Le remède est de travailler avec des variations, des glissements annuels ou des écarts, c'est pourquoi le site propose la transformation de variation sur 1 an et pourquoi le modèle utilise des écarts et des taux réels plutôt que des niveaux.</p>"
          "<h4>7.3 Décalages et VAR</h4>"
          "<p>Un <b>modèle vectoriel autorégressif</b> (VAR) modélise plusieurs séries ensemble, chacune dépendant de son propre passé et de celui des autres. Dans sa forme la plus simple, avec un décalage et deux séries :</p>"
        + eq("IPC<sub>t</sub> = 0,5&middot;IPC<sub>t&minus;1</sub> + 0,10&middot;M<sub>t&minus;1</sub>            M<sub>t</sub> = 0,05&middot;IPC<sub>t&minus;1</sub> + 0,80&middot;M<sub>t&minus;1</sub>")
        + "<p>Une <b>fonction de réponse impulsionnelle</b> (IRF) répond à « combien de temps avant qu'un choc n'arrive ? » : on injecte un choc d'une unité dans M à la date 0 (tout le reste à son niveau normal), puis on applique les équations de façon répétée. Avec des coefficients <i>illustratifs</i> :</p>"
        + tbl(["Trimestre après le choc", "0", "1", "2", "3", "4", "5"], [["Effet sur l'IPC", "0", "0,10", "0,13", "0,130", "0,117", "0,101"]])
        + "<p>L'effet est nul à l'impact, culmine vers le trimestre 2, puis s'estompe. Les vraies études VAR sur monnaie et inflation au Maroc utilisent la même boucle avec cinq variables et plusieurs décalages. "
          "C'est un précieux outil <b>explicatif</b> pour le délai, mais un VAR exige bien plus d'observations que ne fournissent les décisions de taux : c'est un complément ici, pas le moteur de prévision.</p>"
          "<h4>7.4 Fuite d'information et biais d'anticipation</h4>"
          "<p>Toute étape qui laisse entrer dans la prédiction de l'information postérieure à sa date est une <b>fuite</b>. Sources propres à ce projet :</p>"
          "<ul>"
          "<li><b>Révisions de données.</b> Le PIB et l'inflation sont révisés ; la valeur stockée est la valeur finale, qui n'était pas connue à l'époque.</li>"
          "<li><b>Filtres centrés.</b> L'output gap de Hodrick-Prescott utilise des données des deux côtés de chaque date, donc l'écart à une date « connaît » en partie le futur.</li>"
          "<li><b>Délais de publication.</b> Un PIB trimestriel publié six semaines après la fin du trimestre ne peut pas être utilisé à la fin du trimestre.</li>"
          "<li><b>Normalisation sur tout l'échantillon.</b> Standardiser avec la moyenne de tout l'historique utilise le futur (section 10).</li>"
          "</ul>"
          "<h4>7.5 Autocorrélation et ruptures structurelles</h4>"
          "<p>Quand chaque observation dépend de la précédente, les erreurs standard sont sous-estimées et les découpages aléatoires apprentissage/test sont invalides. Les relations changent aussi avec le temps (2008, la pandémie de 2020, le pic d'inflation de 2022), si bien qu'un coefficient unique pour 2006-2026 peut ne décrire correctement aucune période. "
          "Ce sont deux raisons de ne tester qu'en avançant dans le temps (section 11).</p>"
    )))

    out.append(("logit", "8. Le modèle : la régression logistique", (
        "<p>La régression linéaire prédit un nombre, mais une décision est une catégorie, et une droite peut sortir des valeurs hors de 0 à 1. La régression logistique corrige cela en prédisant une <b>probabilité</b>.</p>"
        "<h4>8.1 Les cotes (odds) et le logit</h4>"
        + eq("cote = p / (1 &minus; p)            logit(p) = ln( p / (1 &minus; p) )")
        + "<p>Si p = 0,2, la cote est 0,25 (un contre quatre). ln est le logarithme népérien, l'inverse de e<sup>x</sup> où e &asymp; 2,718. Le logit envoie toute probabilité sur la droite des réels entière, ce qui permet de le modéliser par une somme pondérée.</p>"
          "<h4>8.2 Le modèle</h4>"
        + eq("z = &beta;<sub>0</sub> + &beta;<sub>1</sub>x<sub>1</sub> + &beta;<sub>2</sub>x<sub>2</sub> + ...            p = 1 / (1 + e<sup>&minus;z</sup>)")
        + sym([("x<sub>1</sub>, x<sub>2</sub>...", "inputs pour une réunion donnée (écart d'inflation, taux réel, ...)"), ("&beta;<sub>0</sub>", "constante : fixe la probabilité de base"),
               ("&beta;<sub>j</sub>", "poids de l'input j, estimé sur les données"), ("z", "le score (log-cote)"),
               ("p", "probabilité prédite, toujours entre 0 et 1 (la fonction sigmoïde en S)")])
        + "<h4>8.3 Lire un coefficient</h4>"
          "<p>Une hausse d'une unité de x<sub>j</sub> ajoute &beta;<sub>j</sub> à la log-cote, c'est-à-dire multiplie la <b>cote</b> par e<sup>&beta;<sub>j</sub></sup> (l'<b>odds ratio</b>). "
          "L'effet sur la probabilité elle-même est &part;p/&part;x<sub>j</sub> = &beta;<sub>j</sub> &middot; p(1 &minus; p), maximal près de p = 0,5 et faible pour les événements rares. "
          "Un &beta; positif signifie que l'input augmente la chance de l'événement. Comparer le signe à l'attendu de la théorie (section 4) est le premier contrôle de cohérence.</p>"
          "<h4>8.4 Estimation par maximum de vraisemblance</h4>"
          "<p>Avec un résultat oui/non, il n'y a pas d'« erreur » naturelle à mettre au carré. On choisit plutôt les &beta; qui rendent l'<b>historique observé le plus probable</b>. Pour la réunion i, de résultat y<sub>i</sub> (1 = événement, 0 = pas d'événement) et de probabilité modélisée p<sub>i</sub> :</p>"
        + eq("&#8467;(&beta;) = &Sigma;<sub>i</sub> [ y<sub>i</sub>&middot;ln(p<sub>i</sub>) + (1 &minus; y<sub>i</sub>)&middot;ln(1 &minus; p<sub>i</sub>) ]            log-loss = &minus; &#8467; / n")
        + "<p>&#8467; est la <b>log-vraisemblance</b> ; le meilleur &beta; la maximise (de façon équivalente, minimise la log-loss). Intuition : une réunion avec y = 1 contribue ln(p), donc donner une forte probabilité à l'événement réel rapporte ; attribuer 1 % à ce qui arrive ensuite coûte ln(0,01) = &minus;4,6, une lourde pénalité. "
          "Il n'y a pas de formule fermée, le logiciel itère donc (Newton-Raphson, aussi appelé moindres carrés repondérés itérativement) :</p>"
        + eq("&beta;<sub>nouveau</sub> = &beta; + ( X&prime;WX )<sup>&minus;1</sup> &middot; X&prime;( y &minus; p )            W = matrice diagonale d'entrées p<sub>i</sub>(1 &minus; p<sub>i</sub>)")
        + sym([("X", "tableau des inputs, une ligne par réunion (plus une colonne de 1)"), ("X&prime;", "sa transposée (lignes et colonnes échangées)"),
               ("I(&beta;) = X&prime;WX", "information de Fisher : précision avec laquelle les données fixent chaque &beta;"), ("ES(&beta;<sub>j</sub>)", "racine du j-ième terme diagonal de I(&beta;)<sup>&minus;1</sup>")])
        + "<p>La statistique z de Wald z = &beta;<sub>j</sub> / ES(&beta;<sub>j</sub>) teste si un coefficient diffère de zéro ; un test du rapport de vraisemblance compare deux modèles emboîtés. "
          "Un résumé d'ajustement est le pseudo-R<sup>2</sup> de McFadden = 1 &minus; &#8467;<sub>modèle</sub> / &#8467;<sub>nul</sub>, où le modèle nul n'utilise que la constante.</p>"
          "<h4>8.5 De la probabilité à la décision</h4>"
          "<p>Le modèle donne une probabilité ; l'appeler « mouvement » ou « statu quo » demande un seuil. 0,5 est faux quand seulement 18 % des cas sont des mouvements. Le seuil devrait refléter les coûts : rater un mouvement contre une fausse alerte. "
          "Pour un résultat de recherche, publier la probabilité et sa calibration (section 11) vaut mieux que forcer un oui/non.</p>"
          "<h4>8.6 Extensions</h4>"
          "<ul>"
          "<li><b>Logit ordonné</b> pour hausse/statu quo/baisse : P(y &le; k) = 1 / (1 + e<sup>&minus;(&theta;<sub>k</sub> &minus; x&prime;&beta;)</sup>), un seul jeu de &beta; partagé avec des seuils &theta;<sub>k</sub>. Standard pour les fonctions de réaction de banques centrales, mais il faut assez d'événements dans chaque classe, ce que les hausses n'ont pas.</li>"
          "<li><b>Logit multinomial</b> : un &beta; distinct par classe, encore plus gourmand en données.</li>"
          "<li><b>En deux étapes (hurdle)</b> : P(mouvement) par un logit, puis P(sens | mouvement), comme en section 1.</li>"
          "</ul>"
    )))
    return out
