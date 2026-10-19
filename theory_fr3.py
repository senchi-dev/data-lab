"""Page 'Theorie du modele' : texte francais, partie 3 (peu d'evenements, inputs, backtest, exemple, limites, glossaire, references)."""
from theory_common import eq, sym, call, tbl


def part3():
    out = []

    out.append(("rare", "9. Peu d'événements : EPV, biais, Firth et ridge", (
        "<p>Cette section distingue ce projet d'un tutoriel standard : il n'y a que @@MOVES@@ mouvements (@@CUTS@@ baisses, @@HIKES@@ hausses) sur @@N@@ réunions.</p>"
        "<h4>9.1 Surapprentissage et règle du nombre d'événements par variable</h4>"
        "<p>Un modèle avec trop d'inputs mémorise le bruit de l'historique : quasi parfait sur le passé, mauvais sur tout ce qui est nouveau. Un repère courant est l'<b>EPV</b> (events per variable) :</p>"
        + eq("EPV = (événements dans la classe la plus rare) / (nombre d'inputs candidats)            repère : EPV &ge; 10")
        + "<p>Ce repère vient de travaux de simulation (Peduzzi et al., 1996). Des travaux plus récents (van Smeden et al., 2019) montrent que c'est une règle grossière et que la taille d'échantillon requise dépend d'autres choses, mais personne ne soutient que @@MOVES@@ événements supportent cinq inputs libres. "
          "À EPV = 10, @@MOVES@@ événements permettent environ <b>un à deux</b> inputs (un pour la cible baisse avec @@CUTS@@ événements).</p>"
          "<h4>9.2 Pourquoi les événements rares biaisent la régression logistique ordinaire</h4>"
          "<p>Le maximum de vraisemblance n'est qu'approximativement sans biais sur de grands échantillons. Avec peu d'événements, il <b>sous-estime</b> la probabilité du résultat rare et gonfle les coefficients (King et Zeng, 2001). "
          "Pire, la <b>séparation</b> : si un input sépare par hasard parfaitement les rares événements, la vraisemblance continue de monter quand le coefficient grandit, l'estimation part donc vers l'infini et le résultat n'a aucun sens.</p>"
          "<h4>9.3 La vraisemblance pénalisée de Firth</h4>"
        + eq("&#8467;*(&beta;) = &#8467;(&beta;) + &frac12; &middot; ln det I(&beta;)")
        + "<p>Le terme ajouté (une pénalité de type loi a priori de Jeffreys) supprime le biais de petit échantillon du premier ordre et garde les estimations finies même en cas de séparation (Firth, 1993). C'est le principal candidat d'estimateur pour ce projet.</p>"
          "<h4>9.4 Ridge et lasso</h4>"
        + eq("ridge :  minimiser  &minus;&#8467;(&beta;) + &lambda; &middot; &Sigma; &beta;<sub>j</sub><sup>2</sup>            lasso :  minimiser  &minus;&#8467;(&beta;) + &lambda; &middot; &Sigma; |&beta;<sub>j</sub>|")
        + "<p>&lambda; (lambda) fixe la sévérité de la pénalité sur les gros coefficients. Un &lambda; plus grand donne des &beta; plus petits et plus prudents ; ridge les réduit tous, lasso peut en annuler certains exactement. "
          "&lambda; se choisit par une validation qui respecte l'ordre du temps (section 11). Une version bayésienne à lois a priori faiblement informatives (Gelman et al., 2008) est une proche cousine.</p>"
          "<h4>9.5 Le compromis biais-variance</h4>"
          "<p>L'erreur de prédiction se décompose en <b>biais</b> (le modèle est trop simple pour saisir la structure) et <b>variance</b> (le modèle change beaucoup avec un autre échantillon). "
          "Les modèles flexibles réduisent le biais et augmentent la variance. Avec @@MOVES@@ événements la variance domine, d'où le choix délibéré d'un modèle simple et rétréci.</p>"
        + call("key", "Alternatives honnêtes",
               "Un scorecard transparent (quelques indicateurs standardisés additionnés avec des signes fixés par la théorie), ou un indice composite, est un rival légitime de tout modèle statistique à cette taille d'échantillon, et souvent difficile à battre. "
               "Tout modèle ajusté devrait être présenté à côté de tels repères simples.")
    )))

    out.append(("inputs", "10. Choisir et préparer les inputs", (
        "<h4>10.1 Sélection</h4>"
        "<p>La sélection suit les sections 4 et 9 : un input par bloc de l'économie, signe fixé à l'avance par la théorie, un budget d'événements, et aucun recours aux résultats sur tout l'échantillon pour choisir. "
        "Les candidats sont tout ce qui figure dans le menu ; le tableau de corrélation n'est qu'une aide de tri.</p>"
        "<h4>10.2 Transformations</h4>"
        "<ul>"
        "<li><b>Écarts</b> : déviation par rapport à un objectif ou à une tendance (inflation moins objectif ; output gap).</li>"
        "<li><b>Variations et glissements annuels</b> plutôt que niveaux, pour traiter les tendances (section 7).</li>"
        "<li><b>Taux réel</b> = taux directeur moins inflation sous-jacente.</li>"
        "<li><b>Décalages</b> : la valeur de la fin du mois précédent, jamais celle du mois de la réunion.</li>"
        "<li><b>Standardisation</b> : z = (x &minus; &mu;) / &sigma;, pour que les inputs partagent une échelle et que les coefficients soient comparables. &mu; et &sigma; doivent venir de la <b>seule fenêtre d'apprentissage</b>.</li>"
        "</ul>"
        "<h4>10.3 Colinéarité</h4>"
        "<p>Des inputs qui bougent ensemble (par exemple inflation globale et sous-jacente, ou taux BCE et Fed) rendent les coefficients instables parce que le modèle ne peut pas les distinguer. "
        "Le facteur d'inflation de la variance VIF<sub>j</sub> = 1 / (1 &minus; R<sub>j</sub><sup>2</sup>), où R<sub>j</sub><sup>2</sup> est le R-carré de la régression de l'input j sur les autres, le signale ; des valeurs au-dessus de 5 à 10 environ sont un avertissement. "
        "Un input par bloc est le remède structurel.</p>"
        "<h4>10.4 Alignement et dates de publication</h4>"
        "<p>Les séries arrivent à des fréquences différentes (quotidienne, mensuelle, trimestrielle, annuelle). Chacune est alignée sur une grille mensuelle et une série plus lente n'est reportée vers l'avant que <b>après sa date de publication</b>. "
        "Quand c'est possible, la première valeur publiée est utilisée, pas la valeur révisée.</p>"
    )))

    out.append(("backtest", "11. Validation et backtesting", (
        "<p>Un backtest répond à une seule question : <b>si ce modèle avait été utilisé dans le passé, avec seulement ce qui était connu alors, qu'aurait-il donné ?</b> Mal fait, il est pire que rien, car il fabrique une fausse confiance.</p>"
        "<h4>11.1 Pourquoi pas un découpage aléatoire apprentissage/test</h4>"
        "<p>Affecter les réunions au hasard à l'apprentissage et au test met de l'information du futur dans les données d'apprentissage : le modèle est testé sur des cas qu'il a de fait déjà vus. L'ordre du temps doit être préservé.</p>"
        "<h4>11.2 La validation walk-forward</h4>"
        "<ol>"
        "<li>Choisir une période de rodage (par exemple les 30 premières réunions) servant uniquement à ajuster.</li>"
        "<li>Ajuster le modèle, <b>y compris la sélection des inputs et le choix de &lambda;</b>, sur les réunions 1 à t.</li>"
        "<li>Prédire la réunion t+1 et enregistrer la probabilité.</li>"
        "<li>Avancer d'une réunion et recommencer.</li>"
        "</ol>"
        "<p>Chaque prédiction enregistrée est réellement hors échantillon. Une <b>fenêtre extensible</b> garde toutes les réunions antérieures ; une <b>fenêtre glissante</b> ne garde que les k dernières, utile si les relations dérivent. "
        "Si une étiquette dépend d'une période qui chevauche l'apprentissage suivant, un <b>embargo</b> supprime le chevauchement (López de Prado, 2018). Le rodage coûte des données dont le projet se passerait bien, ce qui est en soi à signaler.</p>"
        "<h4>11.3 Comment on se trompe soi-même</h4>"
        "<ul>"
        "<li><b>Fuite par la sélection.</b> Choisir les inputs en regardant tout l'historique, puis backtester sur ce même historique, est circulaire. Toute la procédure de sélection doit vivre à l'intérieur de chaque fenêtre d'apprentissage.</li>"
        "<li><b>Surapprentissage du backtest.</b> Chaque fois qu'un modèle est retouché et relancé, un peu d'honnêteté hors échantillon est dépensée. Le nombre de variantes essayées doit être consigné et publié (Bailey et al.).</li>"
        "<li><b>Révisions, délais de publication, filtres centrés</b> (section 7.4).</li>"
        "<li><b>Un seul épisode chanceux.</b> Un bon score dû aux seules baisses d'urgence de 2020 n'est pas un bon modèle.</li>"
        "</ul>"
        "<h4>11.4 Des métriques qui résistent aux événements rares</h4>"
        + tbl(["Métrique", "Formule", "Se lit comme"], [
            ["Matrice de confusion", "comptes de VP, FP, FN, VN", "vrais/faux positifs et négatifs face aux résultats réels"],
            ["Précision", "VP / (VP + FP)", "quand il dit « mouvement », combien de fois il a raison"],
            ["Rappel", "VP / (VP + FN)", "parmi les vrais mouvements, combien il en a repérés"],
            ["F1", "2PR / (P + R)", "équilibre unique de la précision (P) et du rappel (R)"],
            ["Score de Brier", "(1/n) &Sigma; (p<sub>i</sub> &minus; y<sub>i</sub>)<sup>2</sup>", "exactitude des probabilités ; plus bas est meilleur"],
            ["Log-loss", "&minus;(1/n) &Sigma; [y ln p + (1&minus;y) ln(1&minus;p)]", "punit les erreurs confiantes ; plus bas est meilleur"],
            ["Calibration", "fréquence réelle par tranche de probabilité", "un « 30 % » devrait arriver environ 30 % du temps"],
        ])
        + "<p>L'exactitude n'est pas dans la liste : elle récompense le fait de toujours répondre « statu quo ». Des <b>références</b> sont obligatoires : (a) toujours statu quo, (b) répéter la décision précédente, (c) une pièce pondérée par le taux de base. Un modèle qui ne les bat pas n'est pas un modèle.</p>"
          "<h4>11.5 L'incertitude sur le résultat</h4>"
          "<p>Avec @@MOVES@@ événements, chaque métrique a un intervalle très large (section 6.2). Deux outils : l'intervalle binomial exact pour les taux de réussite, et un <b>test de permutation</b> : mélanger de nombreuses fois les résultats réels, recalculer la métrique à chaque fois, et regarder à quelle fréquence le pur hasard égale le score réel. "
          "Les groupes de calibration sont minuscules et doivent être montrés avec leurs effectifs.</p>"
          "<h4>11.6 Ce que contient un rapport complet</h4>"
          "<ul><li>Données utilisées, période, nombre d'événements et définition de la cible choisie à l'avance.</li><li>La procédure walk-forward exacte, le rodage et le type de fenêtre.</li>"
          "<li>Les résultats <b>à côté des références</b>, avec les intervalles.</li><li>Le nombre de variantes de modèle essayées.</li><li>Les faiblesses connues.</li></ul>"
    )))

    out.append(("example", "12. Un exemple chiffré (nombres illustratifs)", (
        call("warn", "Ces nombres sont inventés", "Les coefficients et les cinq réunions ci-dessous sont fabriqués pour montrer l'arithmétique. Ce ne sont ni des estimations ni des preuves.")
        + "<h4>12.1 Calculer une probabilité</h4>"
          "<p>Cible : baisse vs pas de baisse. Probabilité de base 13 %, donc &beta;<sub>0</sub> = logit(0,13) = ln(0,13/0,87) &asymp; &minus;1,90. Deux inputs standardisés : l'inflation sous-jacente (z<sub>1</sub>) avec &beta;<sub>1</sub> = &minus;0,9 (une inflation plus basse augmente la chance de baisse), et le taux réel (z<sub>2</sub>) avec &beta;<sub>2</sub> = +0,6 (une orientation réelle plus serrée l'augmente).</p>"
          "<p>Scénario : inflation sous-jacente d'un écart-type <i>sous</i> la normale (z<sub>1</sub> = &minus;1) et taux réel d'un écart-type au-dessus (z<sub>2</sub> = +1) :</p>"
        + eq("z = &minus;1,90 + (&minus;0,9)(&minus;1) + (0,6)(+1) = &minus;0,40            p = 1 / (1 + e<sup>0,40</sup>) = 1 / (1 + 1,492) &asymp; 0,40")
        + "<p>La cote est passée de 0,149 (13 %) à 0,670 (40 %), une multiplication par e<sup>1,5</sup> &asymp; 4,5, somme des deux effets (0,9 + 0,6) sur l'échelle de la log-cote.</p>"
          "<h4>12.2 Noter cinq prédictions</h4>"
        + tbl(["Réunion", "p prédite", "Réel (1 = baisse)", "Erreur au carré"], [
            ["1", "0,40", "1", "0,360"], ["2", "0,10", "0", "0,010"], ["3", "0,15", "0", "0,023"], ["4", "0,60", "1", "0,160"], ["5", "0,20", "1", "0,640"]])
        + "<p><b>Score de Brier</b> = (0,360 + 0,010 + 0,023 + 0,160 + 0,640) / 5 &asymp; <b>0,24</b>. Un prévisionniste annonçant toujours 13 % obtient environ 0,46 : ce modèle jouet fait donc mieux, et sa <b>log-loss</b> est d'environ 0,66 contre 1,28.</p>"
          "<p>Avec un seuil à 0,30 : les réunions 1 et 4 sont signalées et ce sont toutes deux des baisses (VP = 2, FP = 0) ; la réunion 5 est une baisse ratée (FN = 1) ; les réunions 2 et 3 sont des rejets corrects (VN = 2). Précision = 2/2 = 100 %, rappel = 2/3 &asymp; 67 %.</p>"
        + call("note", "Pourquoi ce n'est qu'un jouet", "Cinq cas ne permettent pas de distinguer compétence et chance : l'intervalle à 95 % d'un rappel de 2 sur 3 va d'environ 9 % à 99 %. Un vrai backtest rencontre le même problème avec @@MOVES@@ événements, c'est pourquoi les intervalles et les références passent en premier.")
    )))

    out.append(("limits", "13. Limites, risques et ce qui me ferait changer d'avis", (
        "<ul>"
        "<li><b>Échantillon minuscule et groupé.</b> @@MOVES@@ mouvements par séries ; l'information indépendante effective est encore plus petite.</li>"
        "<li><b>Changements de régime.</b> La fonction de réaction elle-même change quand le régime de politique change (critique de Lucas) : des coefficients estimés sur une époque peuvent ne pas tenir sur la suivante.</li>"
        "<li><b>Inobservables.</b> Le PIB potentiel et le taux neutre sont estimés ; des méthodes différentes donnent des output gaps différents.</li>"
        "<li><b>Information manquante.</b> Les anticipations de marché (la courbe monétaire), les prévisions et la communication propres à BAM et l'enquête sur les anticipations d'inflation ne sont pas dans les données et sont probablement les meilleurs prédicteurs réels.</li>"
        "<li><b>Les décisions s'arrêtent au @@LAST@@.</b> Les réunions suivantes doivent être ajoutées au fichier de décisions avant qu'un test ait un sens.</li>"
        "<li><b>Aucune affirmation causale.</b> Le modèle prévoit ; il ne prouve pas pourquoi BAM bouge.</li>"
        "</ul>"
        + call("key", "Une règle d'arrêt fixée à l'avance",
               "Le succès est défini d'avance : battre « toujours statu quo » et « répéter la dernière décision » sur un test walk-forward, avec les intervalles publiés. "
               "Si ce n'est pas le cas, la bonne conclusion est « ces données ne permettent pas une anticipation fiable », ce qui est un résultat légitime et utile, pas un échec à cacher.")
    )))

    out.append(("glossary", "14. Glossaire et aide-mémoire des formules", (
        "<h4>Termes</h4>"
        + sym([("Point de base (pb)", "0,01 point de pourcentage ; une baisse de 25 pb fait passer de 3,00 % à 2,75 %"),
               ("Taux directeur", "taux de politique monétaire de BAM"), ("Output gap", "PIB effectif moins PIB potentiel, en % du potentiel"),
               ("Taux neutre r*", "taux réel compatible avec une inflation stable et le plein usage des capacités"), ("Anticipations ancrées", "croyance que l'inflation reviendra à l'objectif"),
               ("Biais d'anticipation", "utiliser une information pas encore disponible à la date de prédiction"), ("Walk-forward", "ajuster sur le passé, prédire le pas suivant, avancer, recommencer"),
               ("EPV", "événements par variable"), ("Séparation", "un input sépare parfaitement les événements, la vraisemblance n'a alors pas de maximum fini"),
               ("Calibration", "accord entre probabilités prédites et fréquences observées")])
        + "<h4>Formules</h4>"
        + tbl(["Nom", "Formule"], [
            ["Moyenne", "x&#772; = (1/n) &Sigma; x<sub>i</sub>"],
            ["Variance d'échantillon", "s<sup>2</sup> = &Sigma; (x<sub>i</sub> &minus; x&#772;)<sup>2</sup> / (n &minus; 1)"],
            ["Erreur standard d'une proportion", "&radic;( p&#770;(1 &minus; p&#770;) / n )"],
            ["Corrélation de Pearson", "&Sigma; (x&minus;x&#772;)(y&minus;y&#772;) / &radic;( &Sigma;(x&minus;x&#772;)<sup>2</sup> &Sigma;(y&minus;y&#772;)<sup>2</sup> )"],
            ["Bayes", "P(A|B) = P(B|A) P(A) / P(B)"],
            ["Identité quantitative", "M V = P Y"],
            ["Fonction de réaction", "i = &rho; i<sub>préc</sub> + (1&minus;&rho;)[ r* + &pi;* + &phi;<sub>&pi;</sub>(&pi;&minus;&pi;*) + &phi;<sub>y</sub> y ]"],
            ["Taux réel", "r = i &minus; &pi;"],
            ["Cote / logit", "p/(1&minus;p) ;  ln( p/(1&minus;p) )"],
            ["Modèle logistique", "p = 1 / (1 + e<sup>&minus;z</sup>),  z = &beta;<sub>0</sub> + &Sigma; &beta;<sub>j</sub> x<sub>j</sub>"],
            ["Log-vraisemblance", "&Sigma; [ y ln p + (1&minus;y) ln(1&minus;p) ]"],
            ["Firth", "&#8467;(&beta;) + &frac12; ln det I(&beta;)"],
            ["Ridge", "&minus;&#8467;(&beta;) + &lambda; &Sigma; &beta;<sub>j</sub><sup>2</sup>"],
            ["EPV", "événements de la classe rare / inputs candidats"],
            ["Précision, rappel, F1", "VP/(VP+FP) ; VP/(VP+FN) ; 2PR/(P+R)"],
            ["Score de Brier", "(1/n) &Sigma; (p<sub>i</sub> &minus; y<sub>i</sub>)<sup>2</sup>"],
        ])
    )))

    out.append(("refs", "15. Références", (
        "<ul>"
        "<li>Bank Al-Maghrib. <i>Dispositif de prévision</i>, bkam.ma, rubrique Politique monétaire.</li>"
        "<li>Taylor, J. B. (1993). Discretion versus policy rules in practice. <i>Carnegie-Rochester Conference Series on Public Policy</i>.</li>"
        "<li>Clarida, R., Galí, J. et Gertler, M. (1999). The science of monetary policy: a New Keynesian perspective. <i>Journal of Economic Literature</i>.</li>"
        "<li>Berg, A., Karam, P. et Laxton, D. (2006). A practical model-based approach to monetary policy analysis. Document de travail du FMI.</li>"
        "<li>Friedman, M. (1968). The role of monetary policy. <i>American Economic Review</i>.</li>"
        "<li>Peduzzi, P. et al. (1996). A simulation study of the number of events per variable in logistic regression analysis. <i>Journal of Clinical Epidemiology</i>.</li>"
        "<li>van Smeden, M. et al. (2019). Sample size for binary logistic prediction models: beyond events per variable. <i>Statistical Methods in Medical Research</i>.</li>"
        "<li>King, G. et Zeng, L. (2001). Logistic regression in rare events data. <i>Political Analysis</i>.</li>"
        "<li>Firth, D. (1993). Bias reduction of maximum likelihood estimates. <i>Biometrika</i>.</li>"
        "<li>Gelman, A. et al. (2008). A weakly informative default prior distribution for logistic and other regression models. <i>Annals of Applied Statistics</i>.</li>"
        "<li>López de Prado, M. (2018). <i>Advances in Financial Machine Learning</i>, chapitre 7 (validation croisée en finance).</li>"
        "<li>Bailey, D., Borwein, J., López de Prado, M. et Zhu, Q. (2014, 2017). Pseudo-mathematics and financial charlatanism ; The probability of backtest overfitting.</li>"
        "<li>Hyndman, R. et Athanasopoulos, G. <i>Forecasting: Principles and Practice</i> (3e éd., gratuit en ligne).</li>"
        "<li>James, G., Witten, D., Hastie, T. et Tibshirani, R. <i>An Introduction to Statistical Learning</i> (PDF gratuit).</li>"
        "</ul>"
        "<p class='th-small'>Les références sont listées de mémoire par l'auteur pour vérification ; contrôler les titres et années exacts à la source avant de les citer dans un travail formel.</p>"
    )))
    return out
