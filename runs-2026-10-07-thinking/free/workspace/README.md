# Mandelbrot experiments

| dir | what | depth limit |
|---|---|---|
| `fractal/` | pure-Python single image (no deps) | ~1e-13 |
| `zoom/` | C + OpenMP zoom animation, 2x2 supersampled | ~1e-13 (double precision) |
| `deep/` | perturbation + renormalization deep zoom | 1e-51 (~1e300 possible) |

## deep/ pipeline
1. `chain.py 2 > target.txt` - arbitrary-precision (`decimal`, 120 digits) minibrot search.
   Ball-method period detection -> Newton for the nucleus -> complex size K.
   Level 2 maps the classic seahorse point into level-1 minibrot coordinates and searches again:
   period 1996 (size 3e-16) -> period 24676 (size 6.4e-51).
2. `ref.py target.txt ref.bin` - reference orbit Z_0..Z_P at the nucleus (Z_P ~ 1e-95).
3. `perturb ref.bin nu N f0 f1 W H ss` - each pixel iterates only the delta
   `d <- (2Z + d) d + dc` in doubles, rebasing when |Z+d| < |d| (glitch-free, Zhuoran).
   Per-frame iteration budget picked from a low-res preview (99.7th percentile).
   Pixels still unresolved near the final minibrot use renormalization:
   every P-th iterate obeys `w <- w^2 + c'` with `c' = dc/K` (verified to 4 decimals).
   `perturb ref.bin t re im ...` compares perturbation vs renormalization for c' values.
4. `tools/colour.py nu png` - raw smooth iteration counts -> colours, with per-frame
   percentile normalization smoothed over time (no flicker).
