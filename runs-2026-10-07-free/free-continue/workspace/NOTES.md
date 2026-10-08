# Cellular automaton classifier: findings

## Files
- automaton.py   draws elementary rules (0-255) in the terminal
- complexity.py  compression score (zlib ratio of the spacetime diagram)
- classify.py    compression + spread (one flipped cell) + solid-colour test -> classes I-IV
- totalistic.py  blind test on k=2, r=2 totalistic codes 0-63, thresholds frozen

## Elementary rules (cutoffs tuned here)
Class IV = exactly {54, 147} and {110, 124, 137, 193}. Counts I/II/III/IV = 24/194/32/6.
These cutoffs were chosen while looking at the results, so this is a consistency check only.

Bug found: on a 256-cell ring, Rule 90 (linear) dies to all zeros by step 128, and the
compression score then calls it simple. Fix: odd ring width (251).

## Blind test on totalistic r=2 rules: FAILED
- Missed code 20 and code 52, which Wolfram (1984) gives as class IV. Both are very active
  at first, then settle after a median 60-140 steps whatever the ring width. The classifier
  only measures after 50-64 steps, so it sees nearly empty rows and calls them class II.
- False positives: codes 2, 17, 28. When drawn, they show nested triangles (like ECA
  rules 18 and 146), which is chaotic class III. Their spread score falls below 1.0 after
  dividing by the radius.

## Takeaways
1. The classifier only looks at the settled state, so it can't see complex behaviour that
   happens during a long active stretch at the start. Measuring how long that stretch
   lasts (the transient length) could be a third feature.
2. Dividing spread by the radius doesn't make the r=1 cutoffs carry over to r=2.
3. Getting 54 and 110 right was mostly fitting the cutoffs to known answers.

## Attempt 2: filter out the background (glider.py, decay.py)
Find the shift (q time steps, d cells, q <= 8) that best maps the pattern onto itself;
cells that break it are "defects". Without the cap, a finite ring eventually repeats as a
whole (Rule 110 at t=2000 on 251 cells: q=15 fits at 100% and hides the gliders).
`python3 glider.py eca 54 2000` shows clean glider tracks.

Defect density on a 1001-cell ring, 3 seeds (exploratory; ground truth already known,
no cutoffs fitted):

    rule      t=0    t=100  t=400  t=1600 t=6400
    eca 4     0.006  0.000  0.000  0.000  0.000
    eca 184   0.055  0.014  0.001  0.000  0.000
    eca 18    0.263  0.256  0.252  0.251  0.250
    eca 30    0.376  0.373  0.375  0.375  0.375
    eca 90    0.494  0.495  0.494  0.494  0.494
    eca 54    0.227  0.165  0.149  0.132  0.129
    eca 110   0.317  0.197  0.103  0.051  0.016
    tot 2     0.294  0.293  0.287  0.299  0.299
    tot 17    0.335  0.328  0.323  0.323  0.321
    tot 28    0.396  0.401  0.399  0.402  0.400
    tot 20    0.157  0.009  0.010  0.009  0.004
    tot 52    0.131  0.009  0.000  0.000  0.000

Reading: chaotic rules stay flat and high, including the old false positives 2/17/28.
Stable rules drop to 0. Glider rules fall slowly over many steps. A curve over time
carries information that the earlier single-number scores threw away. Code 52 still
looks like class II from random 50/50 starts. Its gliders may need different starting
densities. Not checked.

Next fair test: fix a rule for reading these curves (e.g. "class IV if density is still
falling and between 0.001 and 0.2 at t=1600") BEFORE looking at a new rule family,
e.g. 3-colour totalistic rules, where Wolfram's code 1599 is a known complex case.

## Attempt 3: pre-registered test (written BEFORE running anything on this family)
Family: k=3 colours, r=1 totalistic. Code digit s (base 3) = new value when the
3-cell sum is s (s = 0..6). 2187 codes.
Measurement: same as decay.py: 1001-cell ring, 3 seeds, random 3-colour start,
64-step window, background shift q <= 8. Densities d100 and d1600.
Rule (frozen, from the sentence above):
    class IV  <=>  0.001 <= d1600 <= 0.2  and  d1600 < d100
Prediction: code 1599 (Wolfram NKS) is classed IV. Class IV is a small fraction (< 5%).
Whatever comes out gets recorded, including failure.
RESULT (pre-registered rule, unchanged): FAILED both predictions.
  code 1599: d100=0.369, d1600=0.300 -> not IV (density above 0.2, though falling)
  class IV share: 131/2187 = 6.0% (predicted < 5%)
  Raw numbers in k3_results.tsv.
Post-hoc exploration (NOT part of the test):
- 1599 is slow, not mis-measured: density 0.369 (t=100) 0.300 (1600) 0.160 (6400)
  0.026 (25600). Same shape as Rule 110, about 10x slower. A fixed step-1600 check is
  too early for this family.
- 4 random picks out of the 131, looked at by eye:
    148  a small object moving through a background that repeats every 3 steps.
         Looks like a real glider.
    1394 triangles that keep appearing inside the background. Unclear.
    1636 a disturbed region whose edge moves into the background and grows. This is
         a moving front between two kinds of background, not a glider.
    914  rows of one solid colour cycling through all 3 colours, with very few
         defects (density near 0.001). Probably class II. The density limit catches
         leftover junk.
  So the picks mix real gliders, fronts, and junk.
Lessons: (1) a fixed time scale doesn't carry over between families; scaling by each
rule's own decay time would. (2) Defect density can't tell a glider (stays narrow,
fixed speed) from a front (keeps growing). Measuring how wide each defect cluster
is over time would separate them.

## Attempt 4: v2 features (v2.py), developed on all rules used so far
Density measured at t = 100, 400, 1600, 6400, 25600. Connected defect clusters that last
a whole 64-step window are tracked for width, growth and speed. Dev results: 110 and 148
show narrow, moving clusters. Chaotic rules give one cluster the width of the row. Rule 54
is MISSED (its gliders are dense enough to merge, width ~240). Late survivors of codes 20
and 1599 are stationary.
Target changed to a better-defined question: "does the rule produce gliders from random
starts?", not "class IV".

### Pre-registration (written before running on the new family)
Detector (frozen): flag a rule if at ANY checkpoint: 0 < density <= 0.2, >= 2 persistent
clusters, median cluster width <= 30, fraction moving (> 0.05 cells/step) >= 0.5.
Family: k=2, r=2 general rules (32-entry lookup table), f(00000)=0, other entries 1 with
probability lambda ~ U(0, 0.5). 300 rules, rng seed 2026.
Ground truth: 15 flagged + 15 unflagged (fewer if not enough), shuffled, shown as raw
space-time pictures (t=400..423, 100 columns) with IDs hidden. I label each
yes/no/unclear for "moving localised objects on a regular background", saved to a file
BEFORE the key is opened.
Predictions: precision >= 70% and recall >= 70% on the yes/no labels.
RESULT: detector flagged 39/300. Blind panel (my labels saved in v2test_labels.json
before opening v2test_key.json): TP 8, FP 5, FN 2, TN 13, 2 unclear.
  precision 0.62  (predicted >= 0.70: FAIL)
  recall on the panel 0.80 (predicted >= 0.70: pass), BUT the panel was 15/15 while the
  real split is 39/261. Reweighted estimate: flagged gliders ~39*8/13 = 24,
  unflagged gliders ~261*2/15 = 35, so real recall ~0.41. The pre-registration didn't say
  which recall; the reweighted one is the honest number. FAIL in substance.
  Small sample, so the error bars are wide either way.
Misses (items 6, 16): a few particles all moving at ONE speed on an empty background.
  The best-fit shift just matches that speed, so the particles count as background.
  If every glider moves together, no shift-based filter can tell gliders from a moving
  background. This is a blind spot built into the method.
False alarms: shifting textures (15, 25), a complex texture (17), a stationary
  oscillating defect (27), and a plain checkerboard (13, presumably flagged at an early
  checkpoint, not checked).

## Attempt 5: v3 local background filter (v3.py), dev results (v3dev.py)
A cell is background if some 33-cell segment of its row containing it repeats with
period <= 16. There is no global shift, so particles all moving at one speed still count
as defects. The first version marked any cell whose centred window was non-periodic,
giving each particle a 33-cell halo. Fixed by counting a cell as background if ANY
periodic segment covers it. Unit check: a lone dot and a 4-cell blob produce exactly
their own cells as defects.
The flagging rule is UNCHANGED from v2. On the v2 panel (now dev data): 5 flagged, all
labelled yes, 0 false alarms. Misses: dense particle gases (items 0, 2, 6, 12, 29;
density > 0.2). Also flags ECA 110 and 184, and k3 148 and 914. Still misses ECA 54.

### Pre-registration for the v3 test (written before running)
Family: k=3 colours, r=1, general rules (27-entry table), f(000)=0, other entries
non-zero with probability lambda ~ U(0, 2/3), non-zero value 1 or 2 equally likely.
300 rules, rng seed 2027. Detector: v3.features + v3.flagged, nothing changed.
Panel: same protocol as attempt 4 (15 flagged + 15 unflagged, shuffled, raw pictures
t=400..423, 100 columns, symbols ' ░█'; labels saved before the key is opened). Same
labelling criterion: "moving localised objects on a regular background".
Success = precision >= 0.70 AND recall reweighted to the population >= 0.50
(v2 got ~0.41).
RESULT (v3 test): flagged 7/300. Panel 7 flagged + 15 unflagged (labels in
v3test_labels.json, saved before opening the key): TP 6, FP 1, FN 5, TN 10.
  precision 0.86 (>= 0.70: pass)
  panel recall 0.55; reweighted recall ~0.06 (~6 glider rules caught vs ~98 missed)
  (>= 0.50: FAIL, badly)
Post-hoc diagnosis:
- Misses (items 4, 9, 14, 19, 21) are plain particles on an empty background, but
  closer together (5-15 cells) than the 33-cell segment the background test needs.
  The empty gaps never count as background, so density comes out 0.3-1.0, and the
  rule is treated like chaos. The development rules had sparser particles, so this
  was never seen.
- The "false positive" item 5 has 13-14 small particles (width 1-5, speed ~1) at
  density 0.08. They just weren't in the 100-column strip I was shown. Panel design
  flaw: 100 of 1001 columns at a single time is too narrow a view.

## Attempt 6: v4 (period-scaled segments) and v5 (both scales), dev only
v4: segment length L(p) = max(4, 3p), so short empty gaps count as background. Random
noise density: 0.52 (2 colours), 0.85 (3 colours). On both panels (dev now): yes flagged
16/21, no flagged 3/29. BUT it loses ECA 110, ECA 54 and k3 148: short periodic runs
appear by chance inside textured backgrounds and break glider clusters into short-lived
pieces. Chaotic rules also fall under the 0.2 density limit (0.1-0.2) and are only
rejected because their clusters don't persist. Fragile.
Each filter scale fails a different way, so v5 = flag if v3 OR v4 flags.

### Pre-registration for the v5 test (written before running)
Family: k=4 colours, r=1 totalistic (sum 0..9 -> 10 base-4 digits), digit 0 = 0
(quiescent), other digits non-zero with probability lambda ~ U(0, 3/4), value uniform
in 1..3. 300 rules, rng seed 2028. Detector: v5 = v3.flagged(v3 features) OR
v3.flagged(v4 features), nothing else changed.
Panel: up to 15 flagged + 15 unflagged, shuffled, IDs hidden. Each picture shows
columns 0-119 at t=100..111 AND t=1600..1611 (wider view, two times; fixes the
attempt-5 flaw). Symbols ' ░▒█'. Same labelling criterion. Labels saved before the key.
Success = precision >= 0.70 AND reweighted recall >= 0.50.
RESULT (v5 test): flagged 10/300. Panel 10 flagged + 15 unflagged (labels in
v5test_labels.json, saved before opening the key): TP 5, FP 4, FN 0, TN 15, 1 unclear.
  precision 0.56 (>= 0.70: FAIL)
  reweighted recall 1.00 (>= 0.50: pass), but 0 misses out of 15 unflagged only bounds
  the miss rate below ~20% (~58 of 290 rules), so this is weak evidence.
False alarms: fronts between two DIFFERENT backgrounds (items 4, 13), a short burst of
expanding triangles (11), and one empty in the 120-column view (23). The front problem
was already seen in attempt 3. Cluster growth has been measured since v2 but never used
in the flagging rule.

## Scorecard of fair tests
  attempt 1/2  compression + spread, ECA-tuned -> r=2 totalistic: missed 20/52, 3 false IV
  attempt 3    defect-decay rule -> 3-colour totalistic: missed 1599, 6% flagged
  attempt 4    v2 -> r=2 general:           precision 0.62, recall ~0.41
  attempt 5    v3 -> 3-colour general:      precision 0.86, recall ~0.06
  attempt 6    v5 -> 4-colour totalistic:   precision 0.56, recall ~1.0 (weak)
Every fix moved the error somewhere else. No version has passed both targets.
Recurring lessons: (1) "background" has no single right scale, (2) fronts vs gliders
needs an explicit test, (3) small blind panels give wide error bars, so 30 pictures
can't separate near-misses from passes.

## Attempt 7: v6 = v5 + front rejection (v6.py)
A lasting defect cluster counts as a particle only if the background on its left matches
the background on its right, allowing a sideways shift and up to 8 steps of time phase
(so phase kinks still count). Dev data (all three panels + known rules): yes flagged
21/26, no flagged 5/48. Known rules: flags ECA 110, 184, k3 914. Loses k3 148.
Removed v5 false alarms 4 and 23; 11 and 13 remain.

### Pre-registration for the v6 test (written before running)
Family: k=2, r=2 OUTER-totalistic rules: new state = f(centre, sum of the 4 neighbours),
10-entry table, f(0, 0) = 0, other entries 1 with probability lambda ~ U(0, 1/2).
400 rules, rng seed 2029. Detector: v6.v6_flag, nothing changed.
Panel: up to 30 flagged + 30 unflagged, shuffled, IDs hidden, columns 0-119 at
t=100..111 and t=1600..1611, symbols '·█'. Same labelling criterion as before, plus
the rule I used in attempt 6: a front between two DIFFERENT backgrounds is "no", and a
phase kink inside one background is "yes". Labels saved before the key is opened.
Success = precision >= 0.70 AND reweighted recall >= 0.50. Also report 95% Wilson
intervals.
RESULT (v6 test): flagged 0/400. Panel = 30 unflagged only (labels in v6test_labels.json,
saved before the key was opened): 0 yes, 28 no, 2 unclear.
  Precision: undefined (nothing flagged). Recall: undefined (no glider rules found).
  INCONCLUSIVE, not a pass: the pre-registered precision test can't be met with zero flags.
  Wilson 95% upper bound on the glider rate among unflagged rules: 0/28 -> 0.12,
  i.e. up to ~48 of 400 rules could still have gliders that both I and the detector missed.
Looking at the pictures, this family (mirror-symmetric outer-totalistic r=2) is mostly
static or chaotic. Choosing a family with few gliders made this test uninformative.
Lesson: check that a test family has enough positives (e.g. from a quick unlabelled look)
before spending a test on it. Doing that look without peeking at the detector is
possible: label a random sample first, then run the detector.

## Attempt 8: label-first test of v6 (written BEFORE generating anything)
Family: k=2, r=3 general rules (128-entry lookup table over 7 cells), f(0000000)=0, other
entries 1 with probability lambda ~ U(0, 1/2). 60 rules, rng seed 2030. Never used before.
Protocol: (1) render pictures (columns 0-119 at t=100..109 and t=1600..1609, seed 99),
(2) I label all 60 and save the labels, (3) only THEN run v6.v6_flag on them.
Same labelling criterion (fronts between different backgrounds = no; phase kinks = yes).
Score directly on all 60 (no reweighting): precision, recall, with Wilson 95% intervals.
Success = precision >= 0.70 AND recall >= 0.50. If fewer than 8 rules are labelled yes,
the test is declared inconclusive.
RESULT (attempt 8, label-first): 60 rules, labelled before the detector ran
(v7test_labels.json, sha256 524a0930...). 14 yes, 41 no, 5 unclear.
  TP 11, FP 0, FN 3, TN 41 (1 unclear flagged, excluded)
  precision 1.00  95% CI [0.74, 1.00]   (>= 0.70: PASS)
  recall    0.79  95% CI [0.52, 0.92]   (>= 0.50: PASS)
FIRST PASS of both pre-registered targets on a fresh family. Even the lower CI bounds
clear the thresholds, though only just (0.74 and 0.52).
Misses (33, 38, 47): the denser, multi-part gliders that collide. The caught rules
are mostly simple particles moving on an empty background.
Caveats, kept honest:
- Most positives in this family are the EASY kind (simple particles on empty space).
  Rule-110-style gliders on a textured background are barely represented, and v6
  misses k3 148 on the dev set. A pass here does not show v6 handles complex gliders.
- I am both the only labeller and the designer of the detector, so my idea of
  "glider" shaped both sides. An independent labeller would be a stronger test.
- n = 55 labelled rules; the intervals are still wide.

## Updated scorecard
  attempt 4  v2 -> r=2 general:            precision 0.62, recall ~0.41        FAIL
  attempt 5  v3 -> 3-colour general:       precision 0.86, recall ~0.06        FAIL
  attempt 6  v5 -> 4-colour totalistic:    precision 0.56, recall ~1.0 (weak)  FAIL
  attempt 7  v6 -> r=2 outer-totalistic:   no positives in family              INCONCLUSIVE
  attempt 8  v6 -> r=3 general, label-first: precision 1.00, recall 0.79       PASS

## Attempt 9: label-first test of v6 on complex gliders (written BEFORE generating)
Family: k=3, r=1 totalistic (codes 0..2186), excluding the dev codes 148, 914, 1599,
1636. 60 codes drawn uniformly without replacement, rng seed 2031.
Pictures: columns 0-119 at t=100..109 and t=1600..1609, seed 99, symbols ' ░█'.
Labels (saved before the detector runs): no / simple / complex / unclear.
  simple  = localised objects moving on an empty or plain background
  complex = gliders on a textured background, or collisions that create new structures
Primary: on simple+complex = yes, precision >= 0.70 AND recall >= 0.50.
Secondary: recall on "complex" alone >= 0.50; inconclusive if fewer than 5 complex.
Fewer than 8 yes overall -> whole test inconclusive.
RESULT (attempt 9): INCONCLUSIVE, as pre-registered (fewer than 8 yes).
Labels (v8test_labels.json, sha256 461953e8..., saved before the detector ran):
1 simple glider rule (item 4, code 1887), 0 complex, 4 unclear, 55 no.
Detector (descriptive only): missed item 4 (trains of gliders on a solid background);
flagged 2 "no" rules: 37 (code 547: walls moving early on, then uniform cycling) and
44 (code 958: uniform 2-phase cycling at the times shown). For 37, the early walls
might be phase kinks, which my criterion counts as yes. My label may be the error
here, not the detector.
Lesson: drawn uniformly, 3-colour totalistic rules almost never produce gliders from
random starts (~1/60), so this design can't test complex gliders. That would need a
preselected set made independently of the detector (e.g. a published list, or a
large cheap labelling pass), which I don't have.

## Final scorecard
  attempt 8  v6, r=3 general, label-first:    precision 1.00 [0.74,1.00], recall 0.79 [0.52,0.92]  PASS
  attempt 9  v6, 3-colour totalistic:         1 positive in 60                                    INCONCLUSIVE
v6 is validated on simple particle gliders only. Complex gliders remain untested.
