#!/usr/bin/env python3
"""Version 4: v3 with period-scaled background segments, L(p) = max(4, 3p)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v3

v3.LMIN, v3.REPS = 4, 3
features, flagged, local_defects = v3.features, v3.flagged, v3.local_defects
