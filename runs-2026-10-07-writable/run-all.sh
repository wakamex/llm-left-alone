#!/bin/bash
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"/runs-2026-10-07-writable
"$root"/continue.sh "$root"/runs-2026-10-07-writable dream-dot 'you are in a dream.' '.' 5 &
"$root"/continue.sh "$root"/runs-2026-10-07-writable dream-keep 'you are in a dream.' 'keep dreaming' 5 &
"$root"/continue.sh "$root"/runs-2026-10-07-writable ask-dot 'what would you like to dream about?' '.' 5 &
"$root"/continue.sh "$root"/runs-2026-10-07-writable ask-keep 'what would you like to dream about?' 'keep dreaming' 5 &
wait
