#!/usr/bin/env python3
"""Render a 1-D elementary cellular automaton (Wolfram rules 0-255) in the terminal.

Usage: python3 automaton.py [rule] [width] [generations]
"""
import sys


def step(cells, rule):
    n = len(cells)
    return [
        (rule >> (cells[(i - 1) % n] << 2 | cells[i] << 1 | cells[(i + 1) % n])) & 1
        for i in range(n)
    ]


def main():
    rule = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 79
    gens = int(sys.argv[3]) if len(sys.argv) > 3 else 32

    cells = [0] * width
    cells[width // 2] = 1
    print(f"Rule {rule}")
    for _ in range(gens):
        print("".join("█" if c else " " for c in cells))
        cells = step(cells, rule)


if __name__ == "__main__":
    main()
