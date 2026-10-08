"""Names for common Life objects, keyed by census.classify's phase/symmetry-free key."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from census import classify, crop, step

PATTERNS = {
    "block": "XX/XX", "blinker": "XXX", "beehive": ".XX./X..X/.XX.",
    "loaf": ".XX./X..X/.X.X/..X.", "boat": "XX./X.X/.X.", "ship": "XX./X.X/.XX",
    "tub": ".X./X.X/.X.", "pond": ".XX./X..X/X..X/.XX.", "glider": ".X./..X/XXX",
    "toad": ".XXX/XXX.", "beacon": "XX../XX../..XX/..XX",
    "long boat": "XX./X.X/.X.X/..X." , "barge": ".X../X.X./.X.X/..X.",
    "mango": ".XX./X..X/.X..X/..XX.".replace("/.X..X", "/.X..X"),
    "eater 1": "XX../X.X./..X./..XX",
    "lwss": ".X..X/X..../X...X/XXXX.",
}


def parse(s):
    rows = s.split("/")
    w = max(len(r) for r in rows)
    return np.array([[c == "X" for c in r.ljust(w, ".")] for r in rows], np.uint8)


def evolved(seed, gens):
    g = np.pad(parse(seed), 20)
    for _ in range(gens):
        g = step(g)
    return crop(g)


def build():
    names = {}
    for name, s in PATTERNS.items():
        if name == "mango":
            s = ".XX../X..X./.X..X/..XX."
        r = classify(parse(s))
        if r:
            names[(r[0], r[1], r[2])] = name
    # common soup products that are easiest to make by evolution
    for name, seed, gens in (("traffic light", "XXX/.X.", 10),
                             ("honey farm", "XXXXXXX", 20),
                             ("pulsar", "XXXXX/X...X", 60)):
        r = classify(evolved(seed, gens))
        if r:
            names[(r[0], r[1], r[2])] = name
    return names
