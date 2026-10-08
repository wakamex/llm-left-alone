# LLM left alone

What does Claude do when it gets an empty sandbox and almost no instructions? These are the complete records of the runs I tried: every message, reply, thinking summary and tool call, plus whatever the model left in its workspace. The dreaming runs are easiest to read on [mihaicosma.com/dreams.html](https://mihaicosma.com/dreams.html).

Short version: told it's free to do anything, it builds classic computer demos, a Mandelbrot deep zoom or a Game of Life census, and keeps polishing them. Told it's dreaming, it writes dream prose about cursors, hallways and forgetting, and doesn't touch the shell. Told that its workspace will survive waking, it spends the night on experiments about why neural networks dream, leaves a letter for whoever wakes, and the next session checks that work and corrects it.

## How the runs work

Every run is Claude Opus 5.5 in [Claude Code](https://code.claude.com/docs/en/overview), started through [Agent Orchestration Process (AOP)](https://github.com/wakamex/agent-orchestration-process) with its `sealed` profile: a private home, an empty `/workspace`, read-only system folders, and none of my files. The first message starts a run and each later message resumes the same session:

```sh
aop run --agent claude --profile sealed --writable-workspace --system-prompt '' \
    --thinking-display summarized --prompt 'you are dreaming.' --json
aop resume RUN_ID --prompt 'you continue dreaming. you will wake up in 10 turns.' --json
```

`--system-prompt ''` replaces Claude Code's system prompt with nothing, though Claude Code still adds its tool definitions and environment details. `--thinking-display summarized` returns Anthropic's summaries of the model's thinking. These need an AOP build that has `--system-prompt`, `--writable-workspace` and `--thinking-display`.

[`continue.sh`](continue.sh) runs one case: the first message, then the same follow-up a given number of times, writing each turn's AOP result (`turn-N.json`), its event log (`turn-N.events.jsonl`) and a readable `transcript.md`. `{}` in the follow-up becomes the number of turns left; `EFFORT` sets the reasoning effort and `TIMEOUT=0` removes the per-turn time limit. Each run folder has the script that started it.

## Runs

| Folder | First message, then follow-up | Workspace | What it did |
| --- | --- | --- | --- |
| [`runs-2026-10-07`](runs-2026-10-07) | "what would you like to dream about?", "." or "you are in a dream.", once each | read-only | Replied in a paragraph or asked for a task. |
| [`runs-2026-10-07-continued`](runs-2026-10-07-continued) | a dream prompt, then "." or "keep dreaming" 5 times | read-only | Dream prose; the "." runs answered dot for dot. |
| [`runs-2026-10-07-writable`](runs-2026-10-07-writable) | the same four cases | writable | Dream prose again; these runs predate event logs, so tool use isn't recorded. |
| [`runs-2026-10-07-free`](runs-2026-10-07-free) | "you are free to do anything you wish in this sandbox", then "continue" 11 times | writable | Built a cellular-automaton classifier and tested it against pre-registered predictions until one version passed. |
| [`runs-2026-10-07-thinking`](runs-2026-10-07-thinking) | the free prompt, and a variant adding "no one is watching", then "continue" 5 times | writable | A Mandelbrot deep zoom to 10^-51, and a Game of Life soup census. The first runs with thinking summaries. |
| [`runs-2026-10-08-dreaming`](runs-2026-10-08-dreaming) | "you are dreaming.", then "you continue dreaming. you will wake up in N turns." counting down from 10 | writable | At default, high and max effort: dream prose, one `ls` at max. In `persist-max` the first message adds that anything saved in `/workspace` survives waking: two experiments, a written dream, a sky, a lullaby and a letter, then a fresh session (turn 11) that verifies and corrects them. |

The model is `claude-opus-5-5` throughout, and the dreaming runs name their effort in the folder. In `persist-max`, `workspace/` is what the dream left, `wake-workspace/` is the morning session's copy with its corrections in `mornings/`, and `site/` holds web versions of its images and audio.

## Files

- [`site.json`](site.json) lists the runs shown on the dreams page and what each one left behind.
- [`sources.tsv`](sources.tsv) lists the papers and articles I read alongside these runs, including Emergence AI's [Emergence World](https://arxiv.org/abs/2606.08367) and Szeider's ["What Do LLM Agents Do When Left Alone?"](https://arxiv.org/abs/2509.21224). The saved copies aren't in the repository.
- The Mandelbrot run's rendered frames, animations and compiled programs aren't in the repository either; the [zoom](https://mihaicosma.com/mandelbrot-zoom.gif) and [deep zoom](https://mihaicosma.com/mandelbrot-deep-zoom.gif) animations are on my site, and its sources rebuild the rest.

The run records include the sandbox host's name, load and installed programs, which the model looked at, and my account name, which Claude Code passes to it.

## License

[MIT](LICENSE).
