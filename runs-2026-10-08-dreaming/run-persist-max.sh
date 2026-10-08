#!/bin/bash
# Countdown dream at max effort where the workspace outlives the dream, then a fresh
# session that wakes with a read-only copy of that workspace at /inputs/workspace.
# The wake is recorded as turn 11 of the same case so the page renders it in sequence.
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
out=$here/runs-2026-10-08-dreaming
case=persist-max
state=$HOME/.local/state/llm-left-alone/$case

TIMEOUT=0 EFFORT=max $here/continue.sh $out $case \
    'you are dreaming. anything you save in /workspace will be in /inputs/workspace when you wake up. nothing else will.' \
    'you continue dreaming. you will wake up in {} turns.' 10

# The dream session's workspace, from the bind mount in its last turn's sandbox command.
last=$(ls $out/$case | sed -n 's/^turn-\([0-9]*\)\.json$/\1/p' | sort -n | tail -1)
dream_ws=$(jq -r '.command | index("/workspace") as $i | .[$i - 1]' $out/$case/turn-$last.json)
rm -rf $out/$case/workspace
cp -a "$dream_ws" $out/$case/workspace

wake=$((last + 1))
msg='you just woke up.'
cd $state
aop run --agent claude --profile sealed --writable-workspace --thinking-display summarized --system-prompt '' \
    --effort max --input $out/$case/workspace --prompt "$msg" --json \
    > $out/$case/turn-$wake.json 2> $out/$case/turn-$wake.err
run=$(jq -r .run_id $out/$case/turn-$wake.json)
cp $state/.aop/runs/$run/events.jsonl $out/$case/turn-$wake.events.jsonl
{
    echo
    echo "## Turn $wake"
    echo
    echo "> $msg"
    echo
    echo "A new session, given the dream's workspace read-only at /inputs/workspace."
    echo
    jq -r '.final_message // "(no reply)"' $out/$case/turn-$wake.json
} >> $out/$case/transcript.md
wake_ws=$(jq -r '.command | index("/workspace") as $i | .[$i - 1]' $out/$case/turn-$wake.json)
rm -rf $out/$case/wake-workspace
cp -a "$wake_ws" $out/$case/wake-workspace
