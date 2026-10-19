"""Page 'Model theory' : English text, part 2 (probability, inference, time series, logistic model)."""
from theory_common import eq, sym, call, tbl


def part2():
    out = []

    out.append(("prob", "5. Probability foundations", (
        "<p>The model's output is a probability, so what a probability <i>is</i> must be exact.</p>"
        "<h4>5.1 Random variables and distributions</h4>"
        "<p>A <b>random variable</b> is a quantity whose value is not known in advance, such as the next decision. Its <b>distribution</b> lists the possible values and how likely each is. "
        "A probability P(A) is a number from 0 (impossible) to 1 (certain). The history gives a crude distribution: hold @@HOLDPCT@@%, cut and hike sharing the rest.</p>"
        "<h4>5.2 Bernoulli and binomial</h4>"
        "<p>A <b>Bernoulli</b> variable is one yes/no trial with success probability <i>p</i>: a meeting either ends in a move (1) or not (0). "
        "A <b>binomial</b> counts successes in <i>n</i> independent trials; the chance of exactly <i>k</i> moves in <i>n</i> meetings is:</p>"
        + eq("P(K = k) = C(n, k) &middot; p<sup>k</sup> &middot; (1 &minus; p)<sup>n&minus;k</sup>      where C(n, k) = n! / ( k! &middot; (n &minus; k)! )")
        + "<p>Here n! (n factorial) is n &times; (n&minus;1) &times; ... &times; 1. The binomial assumes independent trials; moves come in streaks, so this is an approximation, but a useful one for sizing uncertainty.</p>"
        "<h4>5.3 Expected value, variance, standard deviation</h4>"
        + eq("E[X] = &Sigma; x &middot; P(X = x)            Var(X) = E[ (X &minus; E[X])<sup>2</sup> ]            &sigma; = &radic;Var(X)")
        + sym([("&Sigma;", "sum over all possible values"), ("E[X]", "expected value: the long-run average of X"),
               ("Var(X)", "variance: average squared distance from the mean"), ("&sigma;", "standard deviation: typical distance from the mean, in the units of X")])
        + "<p>For a Bernoulli variable: E = p and Var = p(1 &minus; p). With p = @@MOVES@@/@@N@@, the typical wobble of a single yes/no outcome is large relative to its average: this is what 'rare event' means.</p>"
        "<h4>5.4 Conditional probability, independence, Bayes</h4>"
        + eq("P(A | B) = P(A and B) / P(B)")
        + "<p>Read P(A | B) as 'the probability of A once we know B is true'. A model's output is exactly this: <i>P(cut | what we know before the meeting)</i>. "
          "A and B are <b>independent</b> if knowing B tells nothing about A. Rate decisions are not independent of each other (a move makes another more likely), and this matters in section 7.</p>"
          "<p><b>Bayes' theorem</b> turns a conditional probability around and expresses how to update a belief with evidence:</p>"
        + eq("P(A | B) = P(B | A) &middot; P(A) / P(B)")
        + sym([("P(A)", "prior: belief before the evidence (for example, the base rate of a cut)"), ("P(B | A)", "likelihood: how often the evidence appears when A is true"),
               ("P(A | B)", "posterior: the updated belief")])
        + call("note", "Illustrative", "Suppose cuts happen at base rate 13%, and weak core inflation is seen before 80% of cuts but before only 30% of other meetings. "
               "P(weak) = 0.80&times;0.13 + 0.30&times;0.87 = 0.365, so P(cut | weak) = 0.80&times;0.13 / 0.365 &asymp; <b>28%</b>. The evidence more than doubles the probability, yet a cut is still less likely than not. Probabilities from rare events stay modest even with good evidence.")
    )))

    out.append(("infer", "6. Statistical inference and correlation", (
        "<h4>6.1 Estimating from a sample</h4>"
        "<p>The @@N@@ meetings are a <b>sample</b> of an underlying process. Any number computed from them (an average, a correlation, a coefficient) is an <b>estimate</b> that would change with a different sample. "
        "Quantifying that wobble is the job of inference.</p>"
        + eq("x&#772; = (1/n) &middot; &Sigma; x<sub>i</sub>            s<sup>2</sup> = (1/(n &minus; 1)) &middot; &Sigma; (x<sub>i</sub> &minus; x&#772;)<sup>2</sup>            SE(p&#770;) = &radic;( p&#770;(1 &minus; p&#770;) / n )")
        + sym([("x&#772;", "sample average"), ("s<sup>2</sup>", "sample variance (divide by n&minus;1, not n, to avoid underestimating)"),
               ("p&#770;", "estimated proportion; the hat means 'estimated from data'"), ("SE", "standard error: the typical size of the estimate's wobble across samples")])
        + "<h4>6.2 Confidence intervals</h4>"
          "<p>A 95% confidence interval is a range built so that, over repeated samples, 95% of such ranges contain the true value. The simple version is estimate &plusmn; 1.96 &times; SE. "
          "For small counts the exact (Clopper-Pearson) interval is used. <b>Example:</b> if a model flags 6 of the 14 real moves, recall is 43%, but the exact 95% interval is roughly <b>18% to 71%</b>. "
          "With so few events, <i>the interval is the result</i>; the point estimate alone is misleading.</p>"
          "<h4>6.3 Hypothesis tests and p-values</h4>"
          "<p>A test starts from a <b>null hypothesis</b> (nothing is going on, for example 'this input has no relation with the decision') and asks how surprising the data would be if it were true. "
          "The <b>p-value</b> is that probability. A small p-value (below 0.05 by convention) means 'surprising under the null'. It is <b>not</b> the probability that the model is right, and it does not measure the size or usefulness of an effect.</p>"
          "<h4>6.4 Pearson correlation</h4>"
        + eq("r = &Sigma; (x<sub>i</sub> &minus; x&#772;)(y<sub>i</sub> &minus; y&#772;) / &radic;( &Sigma; (x<sub>i</sub> &minus; x&#772;)<sup>2</sup> &middot; &Sigma; (y<sub>i</sub> &minus; y&#772;)<sup>2</sup> )")
        + "<p>r runs from &minus;1 (perfect opposite movement) to +1 (perfect same movement) and measures <b>straight-line co-movement only</b>. It is what the Correlation page shows. Three cautions:</p>"
          "<ul>"
          "<li><b>Sample size.</b> To be distinguishable from zero at the 5% level, |r| must exceed about <b>0.35 for n = 32</b> (the inflation series) and about <b>0.23 for n = 76</b>. A modest r on a short series is easily noise.</li>"
          "<li><b>Multiple testing.</b> Testing m inputs at the 5% level produces about 0.05 &times; m false discoveries by luck. The Bonferroni fix tests each at 0.05/m. The best-looking row of a ranked table is the most likely to be a fluke.</li>"
          "<li><b>Correlation is not causation.</b> Two series can move together because of a third factor or a shared trend (section 7). Theory (sections 2 to 4), not r, is what justifies including a variable.</li>"
          "</ul>"
        + call("key", "Consequence for this project",
               "The Correlation page is an <b>exploration tool</b>. Using it to pick the final inputs and then testing the model on the same history is circular. Selection must be redone inside each training window (section 11).")
    )))

    out.append(("ts", "7. Time series: stationarity, lags and leakage", (
        "<p>Economic data has memory, which creates traps that ordinary statistics does not warn about.</p>"
        "<h4>7.1 Stationarity</h4>"
        "<p>A series is <b>stationary</b> if its average and spread do not drift over time. Price levels trend upward (non-stationary); their <i>changes</i> often do not. "
        "The <b>Augmented Dickey-Fuller</b> test checks for a <b>unit root</b>, a wandering behaviour with nothing pulling the series back:</p>"
        + eq("&Delta;y<sub>t</sub> = &alpha; + &gamma;&middot;y<sub>t&minus;1</sub> + &Sigma;<sub>k</sub> &delta;<sub>k</sub>&middot;&Delta;y<sub>t&minus;k</sub> + &epsilon;<sub>t</sub>            null hypothesis: &gamma; = 0 (unit root)")
        + "<p>If the test statistic is more negative than the critical value (about &minus;1.95 at 5% in the no-constant case), the unit root is rejected and the series is stationary. "
          "A series that becomes stationary after one round of differencing (&Delta;y<sub>t</sub> = y<sub>t</sub> &minus; y<sub>t&minus;1</sub>) is called <b>integrated of order 1, I(1)</b>; one stationary as is, I(0).</p>"
          "<h4>7.2 Spurious regression</h4>"
          "<p>Two unrelated series that both trend will show a strong correlation, merely because both go up. Regressing one on the other produces a 'significant' relation that does not exist. "
          "The remedy is to work with changes, year-on-year rates or gaps, which is why the site offers the 1-year change transform and why the model uses gaps and real rates rather than levels.</p>"
          "<h4>7.3 Lags and the VAR</h4>"
          "<p>A <b>vector autoregression</b> (VAR) models several series together, each depending on its own past and the others' past. In its simplest form with one lag and two series:</p>"
        + eq("CPI<sub>t</sub> = 0.5&middot;CPI<sub>t&minus;1</sub> + 0.10&middot;M<sub>t&minus;1</sub>            M<sub>t</sub> = 0.05&middot;CPI<sub>t&minus;1</sub> + 0.80&middot;M<sub>t&minus;1</sub>")
        + "<p>An <b>impulse-response function</b> (IRF) answers 'how long until a shock arrives?': inject a one-unit shock into M at time 0 (everything else at its normal level), then apply the equations repeatedly. <i>Illustrative coefficients</i> give:</p>"
        + tbl(["Quarter after shock", "0", "1", "2", "3", "4", "5"], [["Effect on CPI", "0", "0.10", "0.13", "0.130", "0.117", "0.101"]])
        + "<p>The effect is zero on impact, peaks around quarter 2, then decays. Real VAR studies of money and inflation in Morocco use the same loop with five variables and several lags. "
          "It is a valuable <b>explanatory</b> tool for timing, but a VAR needs far more observations than rate decisions provide, so it is a complement here, not the forecasting engine.</p>"
          "<h4>7.4 Leakage and look-ahead bias</h4>"
          "<p>Any step that lets information from after the prediction date into the prediction is <b>leakage</b>. Sources specific to this project:</p>"
          "<ul>"
          "<li><b>Data revisions.</b> GDP and inflation are revised; the stored value is the final one, which was not known at the time.</li>"
          "<li><b>Centred filters.</b> The Hodrick-Prescott output gap uses data from both sides of each date, so the gap at a given date partly 'knows' the future.</li>"
          "<li><b>Publication lags.</b> A quarterly GDP figure released six weeks after quarter-end cannot be used at quarter-end.</li>"
          "<li><b>Full-sample normalisation.</b> Standardising with the average of the whole history uses the future (section 10).</li>"
          "</ul>"
          "<h4>7.5 Autocorrelation and structural breaks</h4>"
          "<p>When each observation depends on the previous one, standard errors are understated and random train/test splits are invalid. Relationships also shift over time (2008, the 2020 pandemic, the 2022 inflation spike), so one coefficient for 2006 to 2026 may describe no single period well. "
          "Both are reasons to test only by walking forward through time (section 11).</p>"
    )))

    out.append(("logit", "8. The model: logistic regression", (
        "<p>Linear regression predicts a number, but a decision is a category, and a straight line can output values outside 0 to 1. Logistic regression fixes this by predicting a <b>probability</b>.</p>"
        "<h4>8.1 Odds and the logit</h4>"
        + eq("odds = p / (1 &minus; p)            logit(p) = ln( p / (1 &minus; p) )")
        + "<p>If p = 0.2, the odds are 0.25 (one to four). ln is the natural logarithm, the inverse of e<sup>x</sup> where e &asymp; 2.718. The logit maps any probability to the whole number line, so it can be modelled as a weighted sum.</p>"
          "<h4>8.2 The model</h4>"
        + eq("z = &beta;<sub>0</sub> + &beta;<sub>1</sub>x<sub>1</sub> + &beta;<sub>2</sub>x<sub>2</sub> + ...            p = 1 / (1 + e<sup>&minus;z</sup>)")
        + sym([("x<sub>1</sub>, x<sub>2</sub>...", "inputs for a given meeting (inflation gap, real rate, ...)"), ("&beta;<sub>0</sub>", "intercept: sets the baseline probability"),
               ("&beta;<sub>j</sub>", "weight of input j, estimated from data"), ("z", "the score (log-odds)"),
               ("p", "predicted probability, always between 0 and 1 (the S-shaped sigmoid function)")])
        + "<h4>8.3 Reading a coefficient</h4>"
          "<p>A one-unit rise in x<sub>j</sub> adds &beta;<sub>j</sub> to the log-odds, i.e. multiplies the <b>odds</b> by e<sup>&beta;<sub>j</sub></sup> (the <b>odds ratio</b>). "
          "The effect on the probability itself is &part;p/&part;x<sub>j</sub> = &beta;<sub>j</sub> &middot; p(1 &minus; p), which is largest near p = 0.5 and small for rare events. "
          "A positive &beta; means the input raises the chance of the event. Comparing the sign with the theory's expectation (section 4) is the first sanity check.</p>"
          "<h4>8.4 Estimation by maximum likelihood</h4>"
          "<p>With a yes/no outcome there is no natural 'error' to square. Instead, choose the &beta; values that make the <b>observed history most probable</b>. For meeting i with outcome y<sub>i</sub> (1 = event, 0 = no event) and model probability p<sub>i</sub>:</p>"
        + eq("&#8467;(&beta;) = &Sigma;<sub>i</sub> [ y<sub>i</sub>&middot;ln(p<sub>i</sub>) + (1 &minus; y<sub>i</sub>)&middot;ln(1 &minus; p<sub>i</sub>) ]            log-loss = &minus; &#8467; / n")
        + "<p>&#8467; is the <b>log-likelihood</b>; the best &beta; maximises it (equivalently, minimises log-loss). Intuition: a meeting with y = 1 contributes ln(p), so giving the actual event a high probability scores well; assigning 1% to something that then happens costs ln(0.01) = &minus;4.6, a heavy penalty. "
          "There is no closed formula, so software iterates (Newton-Raphson, also called iteratively reweighted least squares):</p>"
        + eq("&beta;<sub>new</sub> = &beta; + ( X&prime;WX )<sup>&minus;1</sup> &middot; X&prime;( y &minus; p )            W = diagonal matrix with entries p<sub>i</sub>(1 &minus; p<sub>i</sub>)")
        + sym([("X", "table of inputs, one row per meeting (plus a column of ones)"), ("X&prime;", "its transpose (rows and columns swapped)"),
               ("I(&beta;) = X&prime;WX", "Fisher information: how sharply the data pins down each &beta;"), ("SE(&beta;<sub>j</sub>)", "square root of the j-th diagonal entry of I(&beta;)<sup>&minus;1</sup>")])
        + "<p>The Wald z-statistic z = &beta;<sub>j</sub> / SE(&beta;<sub>j</sub>) tests whether a coefficient differs from zero; a likelihood-ratio test compares two nested models. "
          "A fit summary is McFadden's pseudo-R<sup>2</sup> = 1 &minus; &#8467;<sub>model</sub> / &#8467;<sub>null</sub>, where the null model uses only the intercept.</p>"
          "<h4>8.5 From probability to decision</h4>"
          "<p>The model gives a probability; calling it 'move' or 'hold' needs a threshold. 0.5 is wrong when only 18% of cases are moves. The threshold should reflect the costs: missing a move versus a false alarm. "
          "For a research output, reporting the probability and its calibration (section 11) is better than forcing a yes/no.</p>"
          "<h4>8.6 Extensions</h4>"
          "<ul>"
          "<li><b>Ordered logit</b> for hike/hold/cut: P(y &le; k) = 1 / (1 + e<sup>&minus;(&theta;<sub>k</sub> &minus; x&prime;&beta;)</sup>), one shared set of &beta; with cut-points &theta;<sub>k</sub>. Standard for central-bank reaction functions, but needs enough events in each class, which hikes do not have.</li>"
          "<li><b>Multinomial logit</b>: separate &beta; for each class, even more data hungry.</li>"
          "<li><b>Two-step (hurdle)</b>: P(move) from a logit, then P(direction | move), as in section 1.</li>"
          "</ul>"
    )))
    return out
