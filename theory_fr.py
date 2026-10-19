"""Page 'Theorie du modele' : texte francais, partie 1 (statut, cible, fondations macro, cadre BAM, passerelle)."""
from theory_common import eq, sym, call, tbl

KICKER = "Théorie du modèle"
TITLE = "La théorie derrière le modèle d'anticipation"
LEAD = ("Tout ce sur quoi repose le modèle, expliqué depuis zéro : l'économie de la raison pour laquelle une banque centrale bouge son taux, "
        "la statistique nécessaire pour en faire une probabilité, et la validation nécessaire pour savoir si ça marche. "
        "Chaque symbole est défini avant d'être utilisé.")


def part1():
    out = []

    out.append(("status", "Statut et mode de lecture", (
        call("warn", "À lire en premier",
             "Cette page est la <b>conception théorique</b> du modèle d'anticipation. <b>Aucun modèle n'a encore été estimé ni backtesté.</b> "
             "Tout ce qui suit décrit ce qui sera construit, pourquoi, et comment il sera jugé. Les résultats ne seront ajoutés qu'après un vrai test walk-forward (section 11). "
             "Les nombres marqués <i>illustratif</i> sont inventés pour enseigner un calcul et ne sont pas des résultats.")
        + call("note", "Qui a écrit ceci et comment",
               "Ce site est construit avec l'aide de Claude (IA), utilisé comme coach et facilitateur technique. L'auteur apprend les statistiques et ne prétend pas les maîtriser ; "
               "cette page fait partie de cet apprentissage et est écrite pour être vérifiée, pas crue sur parole. Toutes les formules sont standard et les références en fin de page permettent de les vérifier.")
        + "<p>La page suit l'ordre dans lequel un modèle se construit réellement : <b>la question</b> (ce qu'on prédit), <b>l'économie</b> (pourquoi le taux bouge), "
          "<b>la passerelle</b> (de la théorie aux variables), <b>la statistique</b> (probabilités, inférence, séries temporelles), <b>le modèle</b> (régression logistique), "
          "<b>les correctifs petit échantillon</b>, <b>les inputs</b>, <b>la validation</b>, un <b>exemple chiffré</b> et les <b>limites</b>. Les boutons ci-dessus permettent de sauter à une section.</p>"
    )))

    out.append(("question", "1. La question et la cible", (
        "<p>Bank Al-Maghrib (BAM) fixe son taux directeur lors de réunions programmées de son Conseil, quatre fois par an. "
        "La question : <b>avant une réunion donnée, quelle est la probabilité que le Conseil change le taux, et dans quel sens ?</b></p>"
        "<h4>1.1 Définir la variable cible</h4>"
        "<p>Pour la réunion <i>t</i>, soit <i>i<sub>t</sub></i> le taux directeur après la réunion. La variation est :</p>"
        + eq("&Delta;i<sub>t</sub> = i<sub>t</sub> &minus; i<sub>t&minus;1</sub>      (en points de base ; 1 pb = 0,01 point de pourcentage)")
        + "<p>On peut en tirer trois types de cible :</p>"
        + tbl(["Cible", "Définition", "Type", "Événements dans les données"], [
            ["A. Mouvement vs statu quo", "1 si &Delta;i<sub>t</sub> &ne; 0, sinon 0", "binaire", "@@MOVES@@ mouvements"],
            ["B. Baisse vs pas de baisse", "1 si &Delta;i<sub>t</sub> &lt; 0, sinon 0", "binaire", "@@CUTS@@ baisses"],
            ["C. Hausse / statu quo / baisse", "trois classes ordonnées", "ordinale", "@@HIKES@@ hausses, @@HOLDS@@ statu quo, @@CUTS@@ baisses"],
        ])
        + "<h4>1.2 À quoi ressemble l'historique</h4>"
          "<p>Le fichier de décisions couvre les réunions jusqu'au @@LAST@@. Il contient <b>@@N@@ réunions</b> : <b>@@HOLDS@@ statu quo</b> (@@HOLDPCT@@ %), <b>@@CUTS@@ baisses</b> et <b>@@HIKES@@ hausses</b>. "
          "Trois faits de ce tableau pilotent toute la conception :</p>"
          "<ul>"
          "<li><b>Un modèle qui répond toujours « statu quo » a raison @@HOLDPCT@@ % du temps.</b> C'est la référence que tout modèle doit battre ; la simple exactitude n'a aucun sens ici.</li>"
          "<li><b>Seulement @@HIKES@@ hausses</b> (une en 2008, trois en 2022-2023). Un modèle à trois classes ne peut pas être estimé honnêtement. Les cibles réalistes sont A ou B.</li>"
          "<li><b>Les mouvements viennent par séries</b> (deux baisses en 2014, deux en 2020, trois hausses en 2022-2023, trois baisses en 2024). Ce ne sont pas des tirages indépendants, donc l'échantillon effectif est plus petit que le décompte.</li>"
          "</ul>"
        + "<h4>1.3 La règle d'horodatage (point-in-time)</h4>"
          "<p>Une prédiction faite « avant la réunion <i>t</i> » ne peut utiliser que l'information <b>publique avant cette réunion</b>. Concrètement, chaque input est lu à la fin du mois précédent, jamais le mois de la réunion, "
          "et les séries trimestrielles ne sont utilisées qu'après leur date de publication. Violer cette règle s'appelle le biais d'anticipation (look-ahead) et gonfle silencieusement tous les chiffres de performance (sections 7 et 11).</p>"
        + call("key", "Le sens est une question distincte, plus facile",
               "Sur les @@PAIRS@@ paires de mouvements consécutifs de l'historique, le taux est reparti <b>dans le même sens que le mouvement précédent @@SAME@@ fois (@@SAMEPCT@@ %)</b>. "
               "Les cycles sont persistants, donc un modèle de « sens » peut être très simple (mouvement précédent plus inflation). Le plus difficile est la première question : <i>si</i> le Conseil bouge. "
               "D'où une conception en deux étapes : P(mouvement), puis P(sens | mouvement).")
    )))

    out.append(("macro", "2. Fondations macroéconomiques : pourquoi une banque centrale bouge son taux", (
        "<h4>2.1 Le mandat et l'instrument</h4>"
        "<p>L'objectif statutaire principal de BAM est la <b>stabilité des prix</b>. Son instrument principal est le taux directeur : le taux auquel elle prête aux banques ou leur emprunte. "
        "Le bouger oriente les taux courts du marché monétaire (au Maroc le taux MONIA au jour le jour), qui se transmettent ensuite aux taux débiteurs et créditeurs, au taux de change, aux prix d'actifs et aux anticipations. "
        "Ces variations modifient les dépenses, donc l'inflation. La chaîne est lente : la littérature place généralement l'effet maximal d'un changement de taux sur l'inflation autour de <b>12 à 24 mois</b> plus tard, "
        "si bien que le Conseil fixe le taux d'aujourd'hui pour l'inflation qu'il prévoit à peu près deux ans plus loin. C'est pourquoi le Dispositif informationnel suivi sur ce site porte sur des prévisions et des indicateurs avancés, pas seulement sur l'inflation courante.</p>"
        "<h4>2.2 La théorie quantitative de la monnaie (et pourquoi les banques centrales l'ont quittée)</h4>"
        "<p>Le lien le plus ancien entre monnaie et prix est une identité comptable :</p>"
        + eq("M &middot; V = P &middot; Y")
        + sym([("M", "masse monétaire (dans Data Lab : M3)"), ("V", "vitesse de circulation : combien de fois une unité de monnaie est dépensée par période"),
               ("P", "niveau des prix"), ("Y", "production réelle (PIB réel)")])
        + "<p>En taux de croissance (petites variations), cela donne : <b>inflation &asymp; croissance de la monnaie &minus; croissance de la production réelle + variation de la vitesse</b>. "
          "Les monétaristes (Friedman) en ont conclu que si la vitesse V est stable, la monnaie devrait croître au même rythme que la production réelle, sinon les prix montent : la « règle des k % ». "
          "Plusieurs pays ont ciblé la croissance monétaire dans les années 1970, mais la vitesse s'est révélée instable : le lien monnaie-inflation était peu fiable et le délai, selon la formule de Friedman, « long et variable ». "
          "Les banques centrales sont donc passées au ciblage direct de l'inflation via un taux d'intérêt. La croissance de M3 reste dans le modèle comme input de <b>diagnostic</b>, pas comme moteur.</p>"
        "<h4>2.3 Anticipations et ancrage</h4>"
        "<p>Ce que ménages, entreprises et négociateurs de salaires <b>anticipent</b> comme inflation influence ce qu'elle devient : les entreprises fixent leurs prix et les salariés leurs revendications avec ces anticipations. "
        "Les anticipations sont <b>ancrées</b> quand les agents croient que la banque centrale ramènera l'inflation vers son objectif, si bien qu'un choc temporaire ne change pas leur comportement. "
        "Quand elles sont ancrées, la banque centrale peut tolérer un pic passager ; sinon elle doit réagir plus fort. "
        "Les anticipations sont l'input le plus important du cadre officiel que Data Lab ne peut pas encore fournir (l'enquête trimestrielle de BAM auprès des experts n'a pas de série téléchargeable).</p>"
        "<h4>2.4 Le noyau à trois équations (néo-keynésien)</h4>"
        "<p>Les banques centrales modernes à cible d'inflation raisonnent avec trois relations. Chacune est simplifiée ici à sa logique essentielle.</p>"
        "<p><b>(1) La demande : la courbe IS.</b> La production relative à son potentiel dépend de son passé récent, du taux d'intérêt réel par rapport au neutre, et de la demande étrangère :</p>"
        + eq("y<sub>t</sub> = a<sub>1</sub>&middot;y<sub>t&minus;1</sub> &minus; a<sub>2</sub>&middot;( r<sub>t</sub> &minus; r* ) + a<sub>3</sub>&middot;y<sup>étranger</sup><sub>t</sub> + choc")
        + "<p><b>(2) L'inflation : la courbe de Phillips.</b> L'inflation dépend de son passé (inertie), de l'inflation anticipée, de la marge de capacité inutilisée et des prix importés :</p>"
        + eq("&pi;<sub>t</sub> = b<sub>1</sub>&middot;&pi;<sub>t&minus;1</sub> + b<sub>2</sub>&middot;E[&pi;<sub>t+1</sub>] + b<sub>3</sub>&middot;y<sub>t</sub> + b<sub>4</sub>&middot;(variation des prix importés)<sub>t</sub> + choc")
        + "<p><b>(3) La politique : la fonction de réaction (règle de type Taylor).</b> La banque centrale fixe le taux en réponse à l'écart d'inflation et à l'écart de production, en bougeant graduellement :</p>"
        + eq("i<sub>t</sub> = &rho;&middot;i<sub>t&minus;1</sub> + (1 &minus; &rho;)&middot;[ r* + &pi;* + &phi;<sub>&pi;</sub>&middot;(&pi;<sub>t</sub> &minus; &pi;*) + &phi;<sub>y</sub>&middot;y<sub>t</sub> ]")
        + sym([("y<sub>t</sub>", "écart de production (output gap) : PIB effectif moins PIB potentiel, en % du potentiel (le potentiel n'est pas observable, seulement estimé)"),
               ("r<sub>t</sub>", "taux d'intérêt réel = taux nominal moins inflation"),
               ("r*", "taux réel neutre : le taux réel qui ne stimule ni ne refroidit l'économie (non observé également)"),
               ("&pi;<sub>t</sub>, &pi;*", "inflation, et objectif d'inflation"),
               ("E[&pi;<sub>t+1</sub>]", "inflation anticipée pour la période suivante"),
               ("i<sub>t</sub>", "taux directeur nominal"),
               ("&phi;<sub>&pi;</sub>, &phi;<sub>y</sub>", "intensité de la réaction de la banque à l'écart d'inflation et à l'écart de production"),
               ("&rho;", "lissage, entre 0 et 1 : combien le taux d'aujourd'hui s'appuie sur celui de la réunion précédente (les banques centrales bougent graduellement)"),
               ("a<sub>1..3</sub>, b<sub>1..4</sub>", "poids estimés sur les données"),
               ("choc", "tout ce que les autres termes n'expliquent pas")])
        + "<p>L'illustration originale de Taylor (1993) pour les États-Unis fixait les poids de réaction à un demi chacun : <i>i = &pi; + 0,5y + 0,5(&pi; &minus; 2) + 2</i>. Les chiffres comptent moins que la logique : <b>une inflation au-dessus de l'objectif, ou une économie au-dessus de son potentiel, appelle un taux plus haut ; l'inverse appelle un taux plus bas.</b></p>"
        "<h4>2.5 Le taux d'intérêt réel</h4>"
        "<p>Ce qui compte pour les dépenses est le coût de l'argent après inflation. La relation de Fisher dit taux nominal &asymp; taux réel + inflation anticipée, donc :</p>"
        + eq("taux réel = taux nominal &minus; inflation")
        + "<p>Un taux réel élevé rend l'emprunt cher et l'épargne rémunératrice, ce qui <b>réduit</b> la demande (politique restrictive). Un taux réel bas ou négatif fait l'inverse (politique accommodante). "
          "Dans Data Lab, la série de taux réel est le taux directeur de BAM moins l'inflation <b>sous-jacente</b> (hors alimentaire et énergie volatils), la variable que BAM nomme elle-même dans son bloc de politique monétaire. "
          "Elle est tombée à environ &minus;6 points début 2023, ce qui signifie que la politique restait stimulante en termes réels alors même que le taux nominal était relevé : le taux nominal seul aurait raconté la mauvaise histoire.</p>"
        "<h4>2.6 Ce qui est propre au Maroc</h4>"
        "<ul>"
        "<li><b>Régime de change.</b> Le dirham suit un panier encadré (euro et dollar) avec une bande de fluctuation. Cela limite l'ajustement par le change, donc les taux des partenaires (BCE, Fed) et l'écart de taux avec eux comptent pour les flux de capitaux et la marge de manœuvre de BAM.</li>"
        "<li><b>Inflation importée et d'offre.</b> L'énergie (Brent), le blé et les prix alimentaires alimentent l'inflation intérieure. Les chocs d'offre font monter les prix sans excès de demande ; une banque centrale peut les « regarder à travers », d'où le suivi de l'inflation sous-jacente et de l'écart global-sous-jacent.</li>"
        "<li><b>Agriculture.</b> La pluviométrie et la production céréalière font osciller la croissance du PIB et les prix alimentaires d'une année à l'autre : elles sont une source de bruit dans l'écart de production.</li>"
        "<li><b>Peu de décisions.</b> Quatre réunions par an donnent quelques dizaines de décisions par décennie, ce qui rend délicates les statistiques des sections 5 à 9.</li>"
        "</ul>"
    )))

    out.append(("bam", "3. Le cadre de BAM : le modèle semi-structurel", (
        "<p>BAM décrit son dispositif de prévision comme un <b>modèle central semi-structurel</b> appuyé par des modèles satellites (finances publiques, comptes extérieurs, sphère monétaire), avec une fonction de réaction de la politique monétaire endogène. "
        "La description officielle énumère quatre blocs interconnectés : <b>croissance, inflation, secteur extérieur</b> (traité comme exogène, c'est-à-dire donné de l'extérieur) et <b>politique monétaire</b>. "
        "Source : la page « Dispositif de prévision » sur bkam.ma (citée sur la page La démarche).</p>"
        "<h4>3.1 Ce que « semi-structurel » veut dire</h4>"
        "<ul>"
        "<li><b>Structurel</b> : les équations viennent de la théorie économique (les trois relations de la section 2.4), donc chaque coefficient a un sens économique et le modèle peut expliquer <i>pourquoi</i> une prévision change.</li>"
        "<li><b>Semi</b> : les coefficients sont estimés sur les données, et toutes les relations ne sont pas dérivées de principes premiers. C'est une voie médiane entre théorie pure et statistique pure.</li>"
        "<li>Cette famille est le standard des banques à cible d'inflation. Une description publique bien connue de cette famille de modèles est celle de Berg, Karam et Laxton (2006, FMI).</li>"
        "</ul>"
        "<h4>3.2 Ce que BAM fait et que ce projet ne peut pas faire</h4>"
        "<p>Le modèle de BAM produit des <b>trajectoires de prévision</b> d'inflation et de croissance sur plusieurs trimestres. Dans les grandes lignes, le Conseil compare ensuite l'inflation prévue à l'horizon pertinent avec la stabilité des prix et fixe le taux, en ajoutant un jugement sur les risques. "
        "Cela demande des dizaines d'observations par équation, un apport d'experts important et de l'information interne non publique. Avec @@N@@ décisions de taux, le reproduire est impossible, et ce projet ne prétend pas le faire.</p>"
        + call("key", "Ce que fait ce projet à la place",
               "Il estime seulement la troisième équation : une <b>fonction de réaction statistique</b> donnant la probabilité que BAM bouge, avec des variables choisies parce que les équations structurelles disent qu'elles comptent. "
               "Le cadre de BAM dit à la statistique quels inputs regarder et avec quel signe ; les données disent ensuite avec quelle force.")
    )))

    out.append(("bridge", "4. La passerelle : de la théorie structurelle au modèle statistique", (
        "<h4>4.1 Pourquoi la théorie est nécessaire</h4>"
        "<p>Avec environ une à deux variables utilisables, les données seules ne peuvent pas départager des dizaines d'inputs candidats : une variable peut sembler prédictive par pur hasard (section 6). "
        "La théorie joue le rôle d'<b>information a priori</b>. Elle réduit la recherche de « n'importe laquelle de 60 séries » à « une par bloc de l'économie, avec un signe attendu connu ».</p>"
        "<h4>4.2 Correspondance entre les blocs de BAM et les séries de Data Lab</h4>"
        + tbl(["Bloc / rôle", "Variable théorique", "Séries Data Lab (exemples)", "Effet attendu sur une hausse de taux"], [
            ["Écart d'inflation", "&pi; &minus; &pi;*", "inflation globale et sous-jacente", "inflation plus haute : hausse plus probable"],
            ["Marge de capacité / demande", "output gap y", "reconstructions de l'output gap, PIB, chômage, production industrielle, climat des affaires", "écart positif : hausse plus probable"],
            ["Orientation réelle de la politique", "r &minus; r*", "taux réel (taux directeur moins inflation sous-jacente)", "taux réel très haut : marge pour baisser ; très bas : pression pour monter"],
            ["Secteur extérieur", "demande étrangère, prix importés", "taux BCE et Fed, EUR/USD, Brent, prix alimentaires", "taux partenaires et pétrole plus hauts : pression pour monter"],
            ["Anticipations", "E[&pi;<sub>t+1</sub>]", "<i>pas encore disponible</i> (enquête d'experts de BAM)", "inflation anticipée plus haute : hausse plus probable"],
            ["Liquidité et crédit", "canal monétaire et du crédit", "M3, taux débiteurs, MONIA", "crédit/M3 rapide : pression pour monter"],
            ["Persistance", "lissage &rho;", "décision précédente", "un mouvement récent rend un autre plus probable"],
        ])
        + "<h4>4.3 Règles de conception qui découlent de la théorie</h4>"
          "<ol>"
          "<li><b>Des écarts et des taux réels, pas des niveaux bruts.</b> Une banque centrale réagit à des écarts par rapport à l'objectif et au neutre, pas à des niveaux.</li>"
          "<li><b>Fixer le signe attendu avant d'estimer.</b> Un coefficient de mauvais signe est un avertissement que le modèle ajuste du bruit.</li>"
          "<li><b>Inclure la persistance</b> (la décision précédente), parce que les mouvements viennent par séries.</li>"
          "<li><b>Au plus un input par bloc</b>, ce qui respecte aussi le budget d'événements (section 9).</li>"
          "<li><b>Admettre les inobservables.</b> Le PIB potentiel et le taux neutre sont estimés, pas mesurés ; les pages d'output gap du site montrent à quel point les méthodes divergent.</li>"
          "</ol>"
        + call("warn", "Un vrai problème de conception : les signes et la cible « mouvement »",
               "La théorie donne des signes <i>directionnels</i> (inflation en hausse : relèvement). Mais la cible A (« mouvement vs statu quo ») mélange hausses et baisses, donc un signe unique ne s'applique plus. "
               "Options : (a) utiliser la cible B (baisse vs pas de baisse, @@CUTS@@ événements) où les signes sont clairs ; (b) garder la cible A mais lui fournir des écarts <i>absolus</i> comme |inflation &minus; objectif| ; (c) la conception en deux étapes de la section 1. "
               "Ce choix est ouvert et sera fixé <b>avant</b> de regarder le moindre résultat, pour éviter de choisir la cible qui score le mieux.")
        + "<h4>4.4 Pourquoi une règle de Taylor stricte n'est pas utilisée comme prévisionniste</h4>"
          "<p>Ajustée comme une formule rigide, la règle explique mal le comportement réel des banques centrales : elles réagissent à des <i>prévisions</i> plutôt qu'aux données courantes, font appel au jugement, pèsent d'autres objectifs et lissent. "
          "Les recherches appliquées sur les décisions de taux trouvent en général que les modèles à choix discret (logit, logit ordonné ou probit) collent mieux aux décisions réelles qu'une règle de Taylor continue. "
          "La règle fournit donc la <b>logique de choix des inputs</b> ; un modèle de probabilité fournit la <b>prévision</b>.</p>"
    )))
    return out
