# Game of Life soup census

Question: what do random 16x16 soups (density 0.5) settle into, and how often do gliders
appear? Checked against Catagolue (catagolue.hatsya.com, b3s23/C1, ~3.4e14 soups).

## v1 (census.py): fixed 1500 gens on a 256x256 torus
Same ranking as Catagolue, but counts 0.44-0.63x too low (gliders 0.85/soup vs 1.92).
Causes: (1) gliders wrap around the torus and crash into debris; (2) objects within 2 cells
were merged into one "object" (traffic light, honey farm, bi-blocks...).

## v2 (census2.py): fixes
- spaceships reaching a 12-cell edge band are counted and deleted
- run until settled (state == state 60 gens earlier), max 6000; median ~600 gens, 10/2000 unsettled
- split each cluster into 8-connected pieces if evolving them separately for 60 gens
  gives the same result as evolving them together (pseudo-object test)

## Result (2000 soups) vs Catagolue
    object      mine/soup  Catagolue   diff   ±1σ (Poisson)
    block           6.654      6.748   -1.4%   0.9%
    blinker         6.121      6.267   -2.3%   0.9%
    beehive         3.450      3.576   -3.5%   1.2%
    glider          1.855      1.921   -3.4%   1.6%
    loaf            1.024      1.055   -2.9%   2.2%
    boat            0.932      0.974   -4.3%   2.3%
    ship            0.667      0.672   -0.7%   2.7%
    tub             0.196      0.212   -8.0%   5.1%
    long boat       0.064      0.068   -7.2%   8.9%
    toad            0.041      0.048  -15.3%  11.1%
Agreement within a few percent. There is a small, consistent shortfall of about 1-4%,
2-3σ for the commonest objects. A likely contributor is that 0.054 objects/soup stay
unresolved (didn't repeat within 30 gens) and 10 soups never settled, but I haven't
checked this.
