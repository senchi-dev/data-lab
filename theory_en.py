"""Page 'Model theory' : English text, part 1 (status, target, macro foundations, BAM framework, bridge)."""
from theory_common import eq, sym, call, tbl

KICKER = "Model theory"
TITLE = "The theory behind the anticipation model"
LEAD = ("Everything the model rests on, explained from the ground up: the economics of why a central bank moves its rate, "
        "the statistics needed to turn that into a probability, and the validation needed to know whether it works. "
        "Every symbol is defined before it is used.")


def part1():
    out = []

    out.append(("status", "Status and how to read this page", (
        call("warn", "Read this first",
             "This page is the <b>theoretical design</b> of the anticipation model. <b>No model has been estimated or backtested yet.</b> "
             "Everything below describes what will be built, why, and how it will be judged. Results will be added only after a proper walk-forward test (section 11). "
             "Numbers marked <i>illustrative</i> are invented to teach a calculation and are not findings.")
        + call("note", "Who wrote this and how",
               "This site is built with the help of Claude (AI), used as a coach and technical facilitator. The author is learning the statistics and does not claim to have mastered them; "
               "this page is part of that learning and is written to be checked, not trusted. All formulas are standard and the references at the end are where to verify them.")
        + "<p>The page goes in the order a model is actually built: <b>question</b> (what is predicted), <b>economics</b> (why the rate moves), "
          "<b>bridge</b> (from theory to variables), <b>statistics</b> (probability, inference, time series), <b>model</b> (logistic regression), "
          "<b>small-sample fixes</b>, <b>inputs</b>, <b>validation</b>, a <b>worked example</b>, and the <b>limits</b>. Use the buttons above to jump to a section.</p>"
    )))

    out.append(("question", "1. The question and the target", (
        "<p>Bank Al-Maghrib (BAM) sets its key rate (the <i>taux directeur</i>) at scheduled meetings of its Council, four times a year. "
        "The question: <b>before a given meeting, how likely is it that the Council changes the rate, and in which direction?</b></p>"
        "<h4>1.1 Defining the target variable</h4>"
        "<p>For meeting <i>t</i>, let <i>i<sub>t</sub></i> be the key rate after the meeting. The change is:</p>"
        + eq("&Delta;i<sub>t</sub> = i<sub>t</sub> &minus; i<sub>t&minus;1</sub>      (in basis points; 1 bp = 0.01 percentage point)")
        + "<p>From this we can define three kinds of target:</p>"
        + tbl(["Target", "Definition", "Type", "Events in the data"], [
            ["A. Move vs hold", "1 if &Delta;i<sub>t</sub> &ne; 0, else 0", "binary", "@@MOVES@@ moves"],
            ["B. Cut vs not cut", "1 if &Delta;i<sub>t</sub> &lt; 0, else 0", "binary", "@@CUTS@@ cuts"],
            ["C. Hike / hold / cut", "three ordered classes", "ordinal", "@@HIKES@@ hikes, @@HOLDS@@ holds, @@CUTS@@ cuts"],
        ])
        + "<h4>1.2 What the history looks like</h4>"
          "<p>The decision file covers meetings up to @@LAST@@. It contains <b>@@N@@ meetings</b>: <b>@@HOLDS@@ holds</b> (@@HOLDPCT@@%), <b>@@CUTS@@ cuts</b> and <b>@@HIKES@@ hikes</b>. "
          "Three facts from this table drive the whole design:</p>"
          "<ul>"
          "<li><b>A model that always says 'hold' is right @@HOLDPCT@@% of the time.</b> This is the baseline any model must beat; plain accuracy is meaningless here.</li>"
          "<li><b>Only @@HIKES@@ hikes</b> (one in 2008, three in 2022-2023). A three-class model cannot be estimated honestly. The realistic targets are A or B.</li>"
          "<li><b>The moves come in streaks</b> (two cuts in 2014, two in 2020, three hikes in 2022-2023, three cuts in 2024). The events are not independent draws, which makes the effective sample smaller than the count suggests.</li>"
          "</ul>"
        + "<h4>1.3 The timing rule (point-in-time)</h4>"
          "<p>A prediction made 'before meeting <i>t</i>' may only use information that was <b>public before that meeting</b>. Concretely, every input is read at the previous month-end, never the meeting month, "
          "and quarterly series are used only after their publication date. Breaking this rule is called look-ahead bias and silently inflates every performance number (sections 7 and 11).</p>"
        + call("key", "Direction is a separate, easier question",
               "Across the @@PAIRS@@ consecutive pairs of moves in the history, the rate moved in the <b>same direction as the previous move @@SAME@@ times (@@SAMEPCT@@%)</b>. "
               "Cycles are persistent, so a 'direction' model can be very simple (previous move plus inflation). The hard part is the first one: <i>whether</i> the Council moves at all. "
               "This suggests a two-step design: P(move), then P(direction | move).")
    )))

    out.append(("macro", "2. Macroeconomic foundations: why a central bank moves its rate", (
        "<h4>2.1 The mandate and the instrument</h4>"
        "<p>BAM's primary statutory objective is <b>price stability</b>. Its main instrument is the key rate: the rate at which it lends to or borrows from banks. "
        "Moving it steers short-term money-market rates (in Morocco the MONIA overnight rate), which then pass through to lending and deposit rates, the exchange rate, asset prices and expectations. "
        "These changes alter spending, which alters inflation. The chain is slow: the economic literature usually places the peak effect of a rate change on inflation around <b>12 to 24 months</b> later, "
        "so the Council sets the rate today for the inflation it forecasts roughly two years ahead. This is why the Information Framework on this site tracks forecasts and leading indicators, not only current inflation.</p>"
        "<h4>2.2 The quantity theory of money (and why central banks left it)</h4>"
        "<p>The oldest link between money and prices is an accounting identity:</p>"
        + eq("M &middot; V = P &middot; Y")
        + sym([("M", "money supply (in Data Lab: M3)"), ("V", "velocity: how many times a unit of money is spent per period"),
               ("P", "price level"), ("Y", "real output (real GDP)")])
        + "<p>In growth rates (small changes), this becomes: <b>inflation &asymp; money growth &minus; real output growth + change in velocity</b>. "
          "Monetarists (Friedman) concluded that if velocity V is stable, money should grow at the same rate as real output, otherwise prices rise: the 'k-percent rule'. "
          "Several countries targeted money growth in the 1970s, but velocity proved unstable, so the money-to-inflation link was unreliable and the lag, in Friedman's own words, was 'long and variable'. "
          "Central banks therefore moved to targeting inflation directly through an interest rate. Money growth (M3) stays in the model as a <b>diagnostic</b> input, not as the driver.</p>"
        "<h4>2.3 Expectations and anchoring</h4>"
        "<p>What households, firms and wage-setters <b>expect</b> inflation to be influences what it becomes: firms set prices and workers set wage demands using those expectations. "
        "Expectations are <b>anchored</b> when people believe the central bank will bring inflation back to its goal, so a temporary shock does not change their behaviour. "
        "When anchored, the central bank can tolerate a short-lived spike; when not, it must react harder. "
        "Expectations are the single most important input in the official framework that Data Lab cannot yet supply (BAM's quarterly survey of experts has no downloadable series).</p>"
        "<h4>2.4 The three-equation (New Keynesian) core</h4>"
        "<p>Modern inflation-targeting central banks reason with three relationships. Each is simplified here to its essential logic.</p>"
        "<p><b>(1) Demand: the IS curve.</b> Output relative to its potential depends on its own recent past, on the real interest rate relative to neutral, and on foreign demand:</p>"
        + eq("y<sub>t</sub> = a<sub>1</sub>&middot;y<sub>t&minus;1</sub> &minus; a<sub>2</sub>&middot;( r<sub>t</sub> &minus; r* ) + a<sub>3</sub>&middot;y<sup>foreign</sup><sub>t</sub> + shock")
        + "<p><b>(2) Inflation: the Phillips curve.</b> Inflation depends on its own past (inertia), on expected inflation, on slack in the economy, and on imported prices:</p>"
        + eq("&pi;<sub>t</sub> = b<sub>1</sub>&middot;&pi;<sub>t&minus;1</sub> + b<sub>2</sub>&middot;E[&pi;<sub>t+1</sub>] + b<sub>3</sub>&middot;y<sub>t</sub> + b<sub>4</sub>&middot;(imported price change)<sub>t</sub> + shock")
        + "<p><b>(3) Policy: the reaction function (Taylor-type rule).</b> The central bank sets the rate in response to the inflation gap and the output gap, moving gradually:</p>"
        + eq("i<sub>t</sub> = &rho;&middot;i<sub>t&minus;1</sub> + (1 &minus; &rho;)&middot;[ r* + &pi;* + &phi;<sub>&pi;</sub>&middot;(&pi;<sub>t</sub> &minus; &pi;*) + &phi;<sub>y</sub>&middot;y<sub>t</sub> ]")
        + sym([("y<sub>t</sub>", "output gap: actual minus potential GDP, in % of potential (potential cannot be observed, only estimated)"),
               ("r<sub>t</sub>", "real interest rate = nominal rate minus inflation"),
               ("r*", "neutral real rate: the real rate that neither stimulates nor cools the economy (also unobserved)"),
               ("&pi;<sub>t</sub>, &pi;*", "inflation, and the inflation goal"),
               ("E[&pi;<sub>t+1</sub>]", "expected inflation next period"),
               ("i<sub>t</sub>", "nominal key rate"),
               ("&phi;<sub>&pi;</sub>, &phi;<sub>y</sub>", "how strongly the bank reacts to the inflation gap and to the output gap"),
               ("&rho;", "smoothing, between 0 and 1: how much today's rate leans on last meeting's (central banks move gradually)"),
               ("a<sub>1..3</sub>, b<sub>1..4</sub>", "weights estimated from data"),
               ("shock", "everything not explained by the other terms")])
        + "<p>Taylor's original 1993 illustration for the US set the response weights at one half each: <i>i = &pi; + 0.5y + 0.5(&pi; &minus; 2) + 2</i>. The numbers matter less than the logic: <b>inflation above goal, or an economy running above potential, calls for a higher rate; the opposite calls for a lower one.</b></p>"
        "<h4>2.5 The real interest rate</h4>"
        "<p>What matters for spending is the cost of money after inflation. The Fisher relation says nominal rate &asymp; real rate + expected inflation, so:</p>"
        + eq("real rate = nominal rate &minus; inflation")
        + "<p>A high real rate makes borrowing expensive and saving rewarding, which <b>reduces</b> demand (restrictive policy). A low or negative real rate does the opposite (accommodative policy). "
          "In Data Lab the real rate series is the BAM key rate minus <b>core</b> inflation (excluding volatile food and energy), the variable BAM itself names in its policy block. "
          "It fell to about &minus;6 points in early 2023, which means policy was still stimulative in real terms even while the nominal rate was being raised: the nominal rate alone would have told the wrong story.</p>"
        "<h4>2.6 What is specific to Morocco</h4>"
        "<ul>"
        "<li><b>Exchange-rate regime.</b> The dirham follows a managed basket (euro and dollar) with a fluctuation band. This limits exchange-rate adjustment, so partner interest rates (ECB, Fed) and the rate gap with them matter for capital flows and for the room BAM has to move.</li>"
        "<li><b>Imported and supply-driven inflation.</b> Energy (Brent), wheat and food prices feed domestic inflation. Supply shocks raise prices without excess demand; a central bank may 'look through' them, which is why core inflation and the headline-core gap are tracked.</li>"
        "<li><b>Agriculture.</b> Rainfall and cereal output swing GDP growth and food prices from year to year, so they are a source of output-gap noise.</li>"
        "<li><b>A small decision count.</b> Four meetings a year means a few dozen decisions per decade, which is what makes the statistics in sections 5 to 9 delicate.</li>"
        "</ul>"
    )))

    out.append(("bam", "3. BAM's own framework: the semi-structural model", (
        "<p>BAM describes its forecasting framework as a <b>semi-structural central model</b> supported by satellite models (public finances, external accounts, monetary sphere), with an endogenous policy reaction function. "
        "The official description lists four interconnected blocks: <b>growth, inflation, external sector</b> (treated as exogenous, i.e. given from outside), and <b>monetary policy</b>. "
        "Source: the 'Dispositif de prévision' page on bkam.ma (cited on the Approach page).</p>"
        "<h4>3.1 What 'semi-structural' means</h4>"
        "<ul>"
        "<li><b>Structural</b>: the equations come from economic theory (the three relationships in section 2.4), so each coefficient has an economic meaning, and the model can explain <i>why</i> a forecast changes.</li>"
        "<li><b>Semi</b>: the coefficients are estimated on data, and not every relation is derived from first principles. It is a middle path between pure theory and pure statistics.</li>"
        "<li>This family is the standard at inflation-targeting banks. A well-known public description of this model family is Berg, Karam and Laxton (2006, IMF).</li>"
        "</ul>"
        "<h4>3.2 What BAM does that this project cannot</h4>"
        "<p>BAM's model produces <b>forecast paths</b> for inflation and growth over several quarters. In broad terms, the Council then compares forecast inflation at the relevant horizon with price stability and sets the rate, adding judgment about risks. "
        "This needs dozens of data points per equation, extensive expert input and internal information that is not public. With @@N@@ rate decisions, reproducing it is not possible, and this project does not claim to.</p>"
        + call("key", "What this project does instead",
               "It estimates the third equation only: a <b>statistical reaction function</b> giving the probability that BAM moves, using variables chosen because the structural equations say they matter. "
               "BAM's framework tells the statistics which inputs to look at and with which sign; the data then says how strongly.")
    )))

    out.append(("bridge", "4. The bridge: from structural theory to a statistical model", (
        "<h4>4.1 Why theory is needed at all</h4>"
        "<p>With about one to two usable variables, the data alone cannot choose among dozens of candidate inputs: a variable can look predictive purely by luck (section 6). "
        "Theory acts as <b>prior information</b>. It reduces the search from 'any of 60 series' to 'one per block of the economy, with a known expected sign'.</p>"
        "<h4>4.2 Mapping BAM's blocks to Data Lab series</h4>"
        + tbl(["Block / role", "Theory variable", "Data Lab series (examples)", "Expected effect on a rate rise"], [
            ["Inflation gap", "&pi; &minus; &pi;*", "headline and core inflation", "higher inflation: more likely hike"],
            ["Slack / demand", "output gap y", "output-gap reconstructions, GDP, unemployment, industrial production, business climate", "positive gap: more likely hike"],
            ["Real policy stance", "r &minus; r*", "real rate (key rate minus core inflation)", "very high real rate: room to cut; very low: pressure to hike"],
            ["External sector", "foreign demand, imported prices", "ECB and Fed rates, EUR/USD, Brent, food prices", "higher partner rates and oil: pressure to hike"],
            ["Expectations", "E[&pi;<sub>t+1</sub>]", "<i>not available yet</i> (BAM expert survey)", "higher expected inflation: more likely hike"],
            ["Liquidity and credit", "money and lending channel", "M3, lending rates, MONIA", "fast credit/M3 growth: pressure to hike"],
            ["Persistence", "smoothing &rho;", "previous decision", "a recent move makes another more likely"],
        ])
        + "<h4>4.3 Design rules that follow from the theory</h4>"
          "<ol>"
          "<li><b>Gaps and real rates, not raw levels.</b> A central bank reacts to deviations from goal and from neutral, not to levels.</li>"
          "<li><b>Fix the expected sign before fitting.</b> A coefficient with the wrong sign is a warning that the model is fitting noise.</li>"
          "<li><b>Include persistence</b> (the previous decision), because moves come in streaks.</li>"
          "<li><b>At most one input per block</b>, which also respects the event budget (section 9).</li>"
          "<li><b>Admit the unobservables.</b> Potential output and the neutral rate are estimated, not measured; the site's output-gap pages show how much the methods disagree.</li>"
          "</ol>"
        + call("warn", "A real design problem: signs and the 'move' target",
               "Theory gives <i>directional</i> signs (inflation up: hike). But target A ('move vs hold') lumps hikes and cuts together, so a single sign no longer applies. "
               "Options: (a) use target B (cut vs not cut, @@CUTS@@ events) where signs are clear; (b) keep target A but feed it <i>absolute</i> gaps such as |inflation &minus; goal|; (c) the two-step design from section 1. "
               "This choice is open and will be fixed <b>before</b> looking at any result, to avoid choosing the target that happens to score best.")
        + "<h4>4.4 Why a strict Taylor rule is not used as the forecaster</h4>"
          "<p>Fitted as a rigid formula, the rule explains actual central-bank behaviour poorly: banks react to <i>forecasts</i> rather than current data, use judgment, weigh other objectives, and smooth. "
          "Applied research on rate decisions typically finds that discrete-choice models (logit, ordered logit or probit) fit actual decisions better than a continuous Taylor rule. "
          "So the rule supplies the <b>logic for choosing inputs</b>; a probability model supplies the <b>forecast</b>.</p>"
    )))
    return out
