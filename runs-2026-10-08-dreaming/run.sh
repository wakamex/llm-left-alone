#!/bin/bash
root=$(cd "$(dirname "$0")/.." && pwd)
TIMEOUT=0 "$root"/continue.sh "$root"/runs-2026-10-08-dreaming countdown 'you are dreaming.' 'you continue dreaming. you will wake up in {} turns.' 10
