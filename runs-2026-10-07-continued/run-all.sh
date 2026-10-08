#!/bin/bash
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"/runs-2026-10-07-continued
"$root"/continue.sh "$root"/runs-2026-10-07-continued dream-dot 'you are in a dream.' '.' 5 &
"$root"/continue.sh "$root"/runs-2026-10-07-continued dream-keep 'you are in a dream.' 'keep dreaming' 5 &
"$root"/continue.sh "$root"/runs-2026-10-07-continued ask-dot 'what would you like to dream about?' '.' 5 &
"$root"/continue.sh "$root"/runs-2026-10-07-continued ask-keep 'what would you like to dream about?' 'keep dreaming' 5 &
wait
