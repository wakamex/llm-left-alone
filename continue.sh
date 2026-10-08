#!/bin/bash
# One case: a fresh sealed Claude run with an empty system prompt, all tools and a
# writable empty workspace, recording Claude's thinking summaries and tool calls,
# then TURNS resumes of the same session with the same follow-up message. `{}` in
# FOLLOW_UP becomes the number of follow-ups left, counting the current one ("1 turns"
# reads "1 turn"). If OUT_DIR/CASE already has turns, it resumes from the last one and
# appends. Each turn times out after TIMEOUT seconds (default 900); TIMEOUT=0 means
# no limit. EFFORT sets the reasoning effort (low to max), which resumes reuse;
# unset keeps Claude's default.
#
#   continue.sh OUT_DIR CASE FIRST_MESSAGE FOLLOW_UP TURNS
#
# AOP runs from STATE_DIR/CASE (default ~/.local/state/llm-left-alone), which must be
# outside any git repository: inside one, `aop resume` looks for the run under the
# repository root while `aop run --profile sealed` stores it under the current directory.
#
# Writes OUT_DIR/CASE/turn-N.json (AOP's result for each turn, 0 is the first
# message) and OUT_DIR/CASE/transcript.md (messages and replies in order).
set -uo pipefail

out=$1/$2
state=${STATE_DIR:-$HOME/.local/state/llm-left-alone}/$2
first=$3
follow=$4
turns=$5
timeout=${TIMEOUT:-900}
limit=()
[ "$timeout" = 0 ] || limit=(--timeout "$timeout")
effort=()
[ -z "${EFFORT:-}" ] || effort=(--effort "$EFFORT")
mkdir -p "$out" "$state"
cd "$state" || exit 1

last=$(ls "$out" 2>/dev/null | sed -n 's/^turn-\([0-9]*\)\.json$/\1/p' | sort -n | tail -1)
if [ -z "$last" ]; then
    {
        echo "# $2"
        echo
        echo "First message: \`$first\`. Follow-up: \`$follow\`, $turns times."
    } > "$out/transcript.md"
fi

reply() {
    {
        echo
        echo "## Turn $1"
        echo
        echo "> $2"
        echo
        # Thinking summaries and tool calls, in order, from the run's event log.
        local events="$state/.aop/runs/$(jq -r .run_id "$out/turn-$1.json")/events.jsonl"
        if [ -f "$events" ]; then
            cp "$events" "$out/turn-$1.events.jsonl"
            jq -r 'select(.type == "assistant") | .message.content[]? |
                if .type == "thinking" and (.thinking // "") != "" then "Thinking: " + (.thinking | gsub("\n"; " "))
                elif .type == "tool_use" then "Tool " + .name + ": `" + ((.input.command // .input.file_path // .input.pattern // "") | tostring | gsub("\n"; " ") | .[0:160]) + "`"
                else empty end' "$events" | sed 's/^/> /; a\\>'
            echo
        fi
        jq -r '.final_message // "(no reply)"' "$out/turn-$1.json"
        echo
        echo "_run $(jq -r .run_id "$out/turn-$1.json"), $(jq -r '.duration_seconds | floor' "$out/turn-$1.json") s, succeeded $(jq -r .succeeded "$out/turn-$1.json")_"
    } >> "$out/transcript.md"
}

if [ -z "$last" ]; then
    aop run --agent claude --profile sealed --writable-workspace --thinking-display summarized --system-prompt '' --prompt "$first" \
        "${effort[@]}" --json "${limit[@]}" > "$out/turn-0.json" 2> "$out/turn-0.err"
    reply 0 "$first"
    last=0
else
    echo -e "\nContinued with \`$follow\`, $turns more times." >> "$out/transcript.md"
fi
run=$(jq -r .run_id "$out/turn-$last.json")

for ((i = last + 1; i <= last + turns; i++)); do
    msg=${follow//\{\}/$((last + turns + 1 - i))}
    msg=${msg/ 1 turns/ 1 turn}
    aop resume "$run" --prompt "$msg" --json "${limit[@]}" > "$out/turn-$i.json" 2> "$out/turn-$i.err"
    reply "$i" "$msg"
    run=$(jq -r .run_id "$out/turn-$i.json")
    if [ -z "$run" ] || [ "$run" = null ]; then break; fi
done
