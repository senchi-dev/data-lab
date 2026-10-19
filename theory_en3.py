"""Page 'Model theory' : English text, part 3 (few events, inputs, backtesting, example, limits, glossary, references)."""
from theory_common import eq, sym, call, tbl


def part3():
    out = []

    out.append(("rare", "9. Few events: EPV, bias, Firth and ridge", (
        "<p>This section is what separates this project from a standard tutorial: there are only @@MOVES@@ moves (@@CUTS@@ cuts, @@HIKES@@ hikes) in @@N@@ meetings.</p>"
        "<h4>9.1 Overfitting and the events-per-variable rule</h4>"
        "<p>A model with too many inputs memorises the noise in the history: near-perfect on the past, poor on anything new. A common guide is <b>EPV</b> (events per variable):</p>"
        + eq("EPV = (events in the rarer class) / (number of candidate input variables)            guideline: EPV &ge; 10")
        + "<p>The guideline comes from simulation work (Peduzzi et al., 1996). Later work (van Smeden et al., 2019) shows it is a crude rule and that required sample size depends on other things, but nobody argues that @@MOVES@@ events support five free inputs. "
          "At EPV = 10, @@MOVES@@ events allow about <b>one to two</b> inputs (one for the cut target with @@CUTS@@ events).</p>"
          "<h4>9.2 Why rare events bias ordinary logistic regression</h4>"
          "<p>Maximum likelihood is only approximately unbiased in large samples. With few events it <b>underestimates</b> the probability of the rare outcome and inflates coefficients (King and Zeng, 2001). "
          "Worse is <b>separation</b>: if an input happens to split the few events perfectly, the likelihood keeps rising as the coefficient grows, so the estimate heads to infinity and the output is meaningless.</p>"
          "<h4>9.3 Firth's penalised likelihood</h4>"
        + eq("&#8467;*(&beta;) = &#8467;(&beta;) + &frac12; &middot; ln det I(&beta;)")
        + "<p>The extra term (a Jeffreys-prior penalty) removes the first-order small-sample bias and keeps the estimates finite even under separation (Firth, 1993). It is the main candidate estimator for this project.</p>"
          "<h4>9.4 Ridge and lasso</h4>"
        + eq("ridge:  minimise  &minus;&#8467;(&beta;) + &lambda; &middot; &Sigma; &beta;<sub>j</sub><sup>2</sup>            lasso:  minimise  &minus;&#8467;(&beta;) + &lambda; &middot; &Sigma; |&beta;<sub>j</sub>|")
        + "<p>&lambda; (lambda) sets how strongly large coefficients are punished. Bigger &lambda; means smaller, more cautious &beta;; ridge shrinks all, lasso can set some exactly to zero. "
          "&lambda; is chosen by validation that respects time order (section 11). A Bayesian version with weakly informative priors (Gelman et al., 2008) is a close cousin.</p>"
          "<h4>9.5 The bias-variance trade-off</h4>"
          "<p>Prediction error splits into <b>bias</b> (the model is too simple to capture the pattern) and <b>variance</b> (the model changes a lot with a different sample). "
          "Flexible models reduce bias and raise variance. With @@MOVES@@ events, variance dominates, so the deliberate choice is a simple, shrunk model.</p>"
        + call("key", "Honest alternatives",
               "A transparent scorecard (a few standardised indicators added with fixed theory-given signs), or one composite index, is a legitimate rival to any statistical model at this sample size, and often hard to beat. "
               "Any fitted model should be reported next to such simple benchmarks.")
    )))

    out.append(("inputs", "10. Choosing and preparing inputs", (
        "<h4>10.1 Selection</h4>"
        "<p>Selection follows sections 4 and 9: one input per block of the economy, sign fixed by theory beforehand, an event budget, and no use of the full-sample results to choose. "
        "Candidates are everything in the menu; the correlation table is a screening aid only.</p>"
        "<h4>10.2 Transformations</h4>"
        "<ul>"
        "<li><b>Gaps</b>: deviation from a goal or trend (inflation minus goal; output gap).</li>"
        "<li><b>Changes and year-on-year rates</b> instead of levels, to deal with trends (section 7).</li>"
        "<li><b>Real rate</b> = key rate minus core inflation.</li>"
        "<li><b>Lags</b>: the value at the previous month-end, never the meeting month.</li>"
        "<li><b>Standardisation</b>: z = (x &minus; &mu;) / &sigma;, so inputs share a scale and coefficients are comparable. &mu; and &sigma; must come from the <b>training window only</b>.</li>"
        "</ul>"
        "<h4>10.3 Collinearity</h4>"
        "<p>Inputs that move together (for example headline and core inflation, or ECB and Fed rates) make coefficients unstable because the model cannot tell them apart. "
        "The variance inflation factor VIF<sub>j</sub> = 1 / (1 &minus; R<sub>j</sub><sup>2</sup>), where R<sub>j</sub><sup>2</sup> is the R-squared from regressing input j on the other inputs, flags it; values above about 5 to 10 are a warning. "
        "One input per block is the structural cure.</p>"
        "<h4>10.4 Alignment and release dates</h4>"
        "<p>Series arrive at different frequencies (daily, monthly, quarterly, annual). Each is aligned to a monthly grid and a slower series is carried forward only <b>after its publication date</b>. "
        "Where possible the first-published value is used, not the revised one.</p>"
    )))

    out.append(("backtest", "11. Validation and backtesting", (
        "<p>A backtest answers one question: <b>if this model had been used in the past, with only what was known then, how would it have done?</b> Done badly it is worse than none, because it manufactures false confidence.</p>"
        "<h4>11.1 Why not a random train/test split</h4>"
        "<p>Randomly assigning meetings to training and test sets puts future information in the training data, so the model is tested on cases it effectively already saw. Time order must be preserved.</p>"
        "<h4>11.2 Walk-forward validation</h4>"
        "<ol>"
        "<li>Choose a burn-in period (for example the first 30 meetings) used only for fitting.</li>"
        "<li>Fit the model, <b>including input selection and choice of &lambda;</b>, on meetings 1 to t.</li>"
        "<li>Predict meeting t+1 and store the probability.</li>"
        "<li>Advance by one meeting and repeat.</li>"
        "</ol>"
        "<p>Every stored prediction is genuinely out of sample. An <b>expanding window</b> keeps all earlier meetings; a <b>rolling window</b> keeps only the last k, useful if relations drift. "
        "If a label depends on a period overlapping the next training set, an <b>embargo</b> removes the overlap (López de Prado, 2018). The burn-in costs data the project can ill afford, which is itself something to report.</p>"
        "<h4>11.3 How people fool themselves</h4>"
        "<ul>"
        "<li><b>Selection leakage.</b> Picking inputs by looking at the full history, then backtesting on the same history, is circular. The whole selection procedure must live inside each training window.</li>"
        "<li><b>Overfitting the backtest.</b> Each time a model is tweaked and re-run, some out-of-sample honesty is spent. The number of variants tried must be recorded and reported (Bailey et al.).</li>"
        "<li><b>Revisions, publication lags, centred filters</b> (section 7.4).</li>"
        "<li><b>One lucky episode.</b> A good score driven by the 2020 emergency cuts alone is not a good model.</li>"
        "</ul>"
        "<h4>11.4 Metrics that survive rare events</h4>"
        + tbl(["Metric", "Formula", "Reads as"], [
            ["Confusion matrix", "counts of TP, FP, FN, TN", "true/false positives and negatives against actual outcomes"],
            ["Precision", "TP / (TP + FP)", "when it says 'move', how often right"],
            ["Recall", "TP / (TP + FN)", "of the real moves, how many it caught"],
            ["F1", "2PR / (P + R)", "single balance of precision (P) and recall (R)"],
            ["Brier score", "(1/n) &Sigma; (p<sub>i</sub> &minus; y<sub>i</sub>)<sup>2</sup>", "accuracy of the probabilities; lower is better"],
            ["Log-loss", "&minus;(1/n) &Sigma; [y ln p + (1&minus;y) ln(1&minus;p)]", "punishes confident errors; lower is better"],
            ["Calibration", "actual frequency inside probability bands", "a '30%' should happen about 30% of the time"],
        ])
        + "<p>Accuracy is not on the list: it rewards always saying 'hold'. <b>Baselines</b> are mandatory: (a) always hold, (b) repeat the previous decision, (c) a coin weighted by the base rate. A model that does not beat them is not a model.</p>"
          "<h4>11.5 Uncertainty about the result</h4>"
          "<p>With @@MOVES@@ events every metric has a very wide interval (section 6.2). Two tools: the exact binomial interval for hit rates, and a <b>permutation test</b>: shuffle the actual outcomes many times, recompute the metric each time, and see how often pure chance matches the real score. "
          "Calibration groups are tiny and should be shown with their counts.</p>"
          "<h4>11.6 What a complete report contains</h4>"
          "<ul><li>Data used, period, number of events and the target definition chosen in advance.</li><li>The exact walk-forward procedure, burn-in and window type.</li>"
          "<li>Results <b>next to the baselines</b>, with intervals.</li><li>The number of model variants tried.</li><li>Known weaknesses.</li></ul>"
    )))

    out.append(("example", "12. A worked example (illustrative numbers)", (
        call("warn", "These numbers are invented", "The coefficients and the five meetings below are made up to show the arithmetic. They are not estimates and not evidence.")
        + "<h4>12.1 Computing a probability</h4>"
          "<p>Target: cut vs not cut. Baseline probability 13%, so &beta;<sub>0</sub> = logit(0.13) = ln(0.13/0.87) &asymp; &minus;1.90. Two standardised inputs: core inflation (z<sub>1</sub>) with &beta;<sub>1</sub> = &minus;0.9 (lower inflation raises the cut chance), and the real rate (z<sub>2</sub>) with &beta;<sub>2</sub> = +0.6 (a tighter real stance raises it).</p>"
          "<p>Scenario: core inflation one standard deviation <i>below</i> normal (z<sub>1</sub> = &minus;1) and the real rate one above (z<sub>2</sub> = +1):</p>"
        + eq("z = &minus;1.90 + (&minus;0.9)(&minus;1) + (0.6)(+1) = &minus;0.40            p = 1 / (1 + e<sup>0.40</sup>) = 1 / (1 + 1.492) &asymp; 0.40")
        + "<p>Odds went from 0.149 (13%) to 0.670 (40%), a multiplication by e<sup>1.5</sup> &asymp; 4.5, which is the sum of the two effects (0.9 + 0.6) on the log-odds scale.</p>"
          "<h4>12.2 Scoring five predictions</h4>"
        + tbl(["Meeting", "Predicted p", "Actual (1 = cut)", "Squared error"], [
            ["1", "0.40", "1", "0.360"], ["2", "0.10", "0", "0.010"], ["3", "0.15", "0", "0.023"], ["4", "0.60", "1", "0.160"], ["5", "0.20", "1", "0.640"]])
        + "<p><b>Brier score</b> = (0.360 + 0.010 + 0.023 + 0.160 + 0.640) / 5 &asymp; <b>0.24</b>. A forecaster always saying 13% scores about 0.46, so this toy model looks better, and its <b>log-loss</b> is about 0.66 against 1.28.</p>"
          "<p>With a 0.30 threshold: meetings 1 and 4 are flagged and both are cuts (TP = 2, FP = 0); meeting 5 is a cut that was missed (FN = 1); meetings 2 and 3 are correct rejections (TN = 2). Precision = 2/2 = 100%, recall = 2/3 &asymp; 67%.</p>"
        + call("note", "Why this is only a toy", "Five cases cannot distinguish skill from luck: the 95% interval on a recall of 2 out of 3 runs from about 9% to 99%. A real backtest faces the same problem with @@MOVES@@ events, which is why intervals and baselines come first.")
    )))

    out.append(("limits", "13. Limits, risks and what would change my mind", (
        "<ul>"
        "<li><b>Tiny, clustered sample.</b> @@MOVES@@ moves in streaks; effective independent information is smaller still.</li>"
        "<li><b>Regime changes.</b> The reaction function itself changes when the policy regime does (the Lucas critique): coefficients estimated on one era may not hold in the next.</li>"
        "<li><b>Unobservables.</b> Potential output and the neutral rate are estimated; different methods give different output gaps.</li>"
        "<li><b>Missing information.</b> Market-implied expectations (the money-market curve), BAM's own forecasts and communication, and the inflation-expectations survey are not in the data and are probably the best real-world predictors.</li>"
        "<li><b>Decision data ends at @@LAST@@.</b> Later meetings must be added to the decision file before any test is meaningful.</li>"
        "<li><b>No causal claim.</b> The model forecasts; it does not prove why BAM moves.</li>"
        "</ul>"
        + call("key", "A pre-committed stopping rule",
               "Success is defined in advance: beating 'always hold' and 'repeat the last decision' on a walk-forward test, with the intervals reported. "
               "If it does not, the correct conclusion is 'these data do not allow reliable anticipation', which is a legitimate and useful finding, not a failure to be hidden.")
    )))

    out.append(("glossary", "14. Glossary and formula sheet", (
        "<h4>Terms</h4>"
        + sym([("Basis point (bp)", "0.01 percentage point; a 25 bp cut takes 3.00% to 2.75%"),
               ("Key rate", "BAM's policy rate (taux directeur)"), ("Output gap", "actual minus potential GDP, in % of potential"),
               ("Neutral rate r*", "real rate consistent with stable inflation and full use of capacity"), ("Anchored expectations", "belief that inflation will return to goal"),
               ("Look-ahead bias", "using information not yet available at the prediction date"), ("Walk-forward", "fit on the past, predict the next step, advance, repeat"),
               ("EPV", "events per variable"), ("Separation", "an input perfectly splits the events, so the likelihood has no finite maximum"),
               ("Calibration", "agreement between predicted probabilities and observed frequencies")])
        + "<h4>Formulas</h4>"
        + tbl(["Name", "Formula"], [
            ["Mean", "x&#772; = (1/n) &Sigma; x<sub>i</sub>"],
            ["Sample variance", "s<sup>2</sup> = &Sigma; (x<sub>i</sub> &minus; x&#772;)<sup>2</sup> / (n &minus; 1)"],
            ["Std error of a proportion", "&radic;( p&#770;(1 &minus; p&#770;) / n )"],
            ["Pearson correlation", "&Sigma; (x&minus;x&#772;)(y&minus;y&#772;) / &radic;( &Sigma;(x&minus;x&#772;)<sup>2</sup> &Sigma;(y&minus;y&#772;)<sup>2</sup> )"],
            ["Bayes", "P(A|B) = P(B|A) P(A) / P(B)"],
            ["Quantity identity", "M V = P Y"],
            ["Reaction function", "i = &rho; i<sub>prev</sub> + (1&minus;&rho;)[ r* + &pi;* + &phi;<sub>&pi;</sub>(&pi;&minus;&pi;*) + &phi;<sub>y</sub> y ]"],
            ["Real rate", "r = i &minus; &pi;"],
            ["Odds / logit", "p/(1&minus;p) ;  ln( p/(1&minus;p) )"],
            ["Logistic model", "p = 1 / (1 + e<sup>&minus;z</sup>),  z = &beta;<sub>0</sub> + &Sigma; &beta;<sub>j</sub> x<sub>j</sub>"],
            ["Log-likelihood", "&Sigma; [ y ln p + (1&minus;y) ln(1&minus;p) ]"],
            ["Firth", "&#8467;(&beta;) + &frac12; ln det I(&beta;)"],
            ["Ridge", "&minus;&#8467;(&beta;) + &lambda; &Sigma; &beta;<sub>j</sub><sup>2</sup>"],
            ["EPV", "events in rarer class / candidate inputs"],
            ["Precision, recall, F1", "TP/(TP+FP) ; TP/(TP+FN) ; 2PR/(P+R)"],
            ["Brier score", "(1/n) &Sigma; (p<sub>i</sub> &minus; y<sub>i</sub>)<sup>2</sup>"],
        ])
    )))

    out.append(("refs", "15. References", (
        "<ul>"
        "<li>Bank Al-Maghrib. <i>Dispositif de prévision</i> (forecasting framework), bkam.ma, section Politique monétaire.</li>"
        "<li>Taylor, J. B. (1993). Discretion versus policy rules in practice. <i>Carnegie-Rochester Conference Series on Public Policy</i>.</li>"
        "<li>Clarida, R., Galí, J. and Gertler, M. (1999). The science of monetary policy: a New Keynesian perspective. <i>Journal of Economic Literature</i>.</li>"
        "<li>Berg, A., Karam, P. and Laxton, D. (2006). A practical model-based approach to monetary policy analysis. IMF Working Paper.</li>"
        "<li>Friedman, M. (1968). The role of monetary policy. <i>American Economic Review</i>.</li>"
        "<li>Peduzzi, P. et al. (1996). A simulation study of the number of events per variable in logistic regression analysis. <i>Journal of Clinical Epidemiology</i>.</li>"
        "<li>van Smeden, M. et al. (2019). Sample size for binary logistic prediction models: beyond events per variable. <i>Statistical Methods in Medical Research</i>.</li>"
        "<li>King, G. and Zeng, L. (2001). Logistic regression in rare events data. <i>Political Analysis</i>.</li>"
        "<li>Firth, D. (1993). Bias reduction of maximum likelihood estimates. <i>Biometrika</i>.</li>"
        "<li>Gelman, A. et al. (2008). A weakly informative default prior distribution for logistic and other regression models. <i>Annals of Applied Statistics</i>.</li>"
        "<li>López de Prado, M. (2018). <i>Advances in Financial Machine Learning</i>, chapter 7 (cross-validation in finance).</li>"
        "<li>Bailey, D., Borwein, J., López de Prado, M. and Zhu, Q. (2014, 2017). Pseudo-mathematics and financial charlatanism; The probability of backtest overfitting.</li>"
        "<li>Hyndman, R. and Athanasopoulos, G. <i>Forecasting: Principles and Practice</i> (3rd ed., free online).</li>"
        "<li>James, G., Witten, D., Hastie, T. and Tibshirani, R. <i>An Introduction to Statistical Learning</i> (free PDF).</li>"
        "</ul>"
        "<p class='th-small'>References were listed from the author's knowledge for verification; check the exact titles and years at the source before citing them in formal work.</p>"
    )))
    return out
