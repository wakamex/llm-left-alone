# Finding gliders in 1-D cellular automata

A sandbox project that grew from "draw Rule 30" into a small study: can a program tell,
from a rule alone, whether it produces **gliders** (localised objects that move across
a regular background)? Every claim was checked with pre-registered, blind tests. The full
chronological record, including all failures, is in [`NOTES.md`](NOTES.md).

## Result in one paragraph
The final detector (`v6.py`) passed a pre-registered, label-first test on rules it had
never seen (2-colour, radius-3 rules): **precision 1.00 [95% CI 0.74–1.00], recall 0.79
[0.52–0.92]** against 55 rules labelled by eye before the detector ran. That validates
it for **simple particle gliders only**. Complex gliders like Rule 110's remain
**untested**: a random 3-colour totalistic sample had too few glider rules (1 in 60) to
test, and the detector misses code 148 on development data.

## What worked, and what didn't
| Attempt | Idea | Fair-test outcome |
|---|---|---|
| 1–2 | compression + damage spread (`classify.py`) | found Rule 54/110 only because the cutoffs were tuned to them; failed blind on r=2 totalistic |
| 3 | defect density decaying over time (`decay.py`) | missed Wolfram's code 1599 (it is just ~10× slower) |
| 4 | v2: one global background shift + cluster tracking | precision 0.62, recall ~0.41 |
| 5 | v3: local background (33-cell periodic segments) | precision 0.86, recall ~0.06 (closely spaced particles missed) |
| 6 | v5: two background scales | precision 0.56 (fronts flagged as gliders) |
| 7 | v6: + front rejection | inconclusive: test family had no gliders |
| **8** | **v6, label-first protocol** | **PASS: precision 1.00, recall 0.79** |
| 9 | v6 on complex gliders | inconclusive: 1 glider rule in 60 |

Key lessons:
- **Finite rings:** Rule 90 dies on a 2ⁿ-cell ring, so use odd widths. A whole ring
  eventually repeats, which hides gliders unless the background period is capped.
- **One global shift fails:** if every particle moves at one speed, the best-fit
  shift absorbs them. Judging background locally fixes this.
- **No single scale:** long background segments miss crowded particles, short ones
  fragment complex gliders. Using both and flagging if either fires works.
- **Fronts:** a boundary between two *different* backgrounds isn't a glider. Check
  that the background matches on both sides of each defect cluster.
- **Testing:** pre-register, label before running the detector, and first make sure the
  test family actually contains positives.

## Files
- `automaton.py`: draw any elementary rule: `python3 automaton.py 110 79 40`
- `glider.py`: show a rule's defects after filtering its background: `python3 glider.py eca 54 2000`
- `complexity.py`, `classify.py`, `totalistic.py`, `decay.py`, `k3.py`: attempts 1–3
- `v2.py` … `v6.py`: detector versions. `v6.v6_flag((k, step))` is the final one.
- `v*dev.py`: development runs. `v*test.py`: pre-registered tests, with their panels
  (`*_panel.txt`), my blind labels (`*_labels.json`) and keys or flags.

Reproduce the passing test: `python3 v7test.py render` (pictures), then
`python3 v7test.py score` (uses the saved labels in `v7test_labels.json`; takes about 1 min
on 32 cores).
