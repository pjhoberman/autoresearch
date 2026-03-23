# Autoresearch — Claude Code Skill

A Claude Code skill for running Karpathy-style autonomous experiment loops on any codebase with a measurable metric.

**The pattern:** one file, one metric, one loop. An agent edits a constrained file, runs an eval, keeps improvements, reverts failures, and repeats — unattended.

Based on [Andrej Karpathy's autoresearch concept](https://karpathy.ai/), generalized beyond ML training to any code with a measurable outcome.

## What it does

When you invoke `/autoresearch` in Claude Code, the skill:

1. Analyzes your codebase to identify tunable levers and a measurable metric
2. Generates a complete experiment harness: `instructions.md`, eval script, test data template, and launch prompt
3. (Optional) Runs validation to confirm the eval produces a stable score
4. Hands off to an autonomous Claude Code agent to run N iterations overnight

## When to use it

- Optimizing a scoring, ranking, or search function
- Tuning weights, thresholds, or parameters
- Improving a prompt template's downstream effect on a metric
- Any code with a measurable quality metric where you want autonomous iteration

## When NOT to use it

- The problem requires a refactor, not tuning
- There's no clear numerical metric to optimize
- The eval is noisy or non-deterministic (network calls, random seeds, timing)
- The fix is obvious and doesn't need iterative search

## Installation

Copy `SKILL.md` into your Claude Code skills directory, or add it to your project's `.claude/skills/` folder.

The skill reads the templates in `templates/` at runtime, so keep them alongside `SKILL.md`.

## Repository structure

```
SKILL.md                        # Skill definition — Claude Code reads this
templates/
  instructions_template.md      # Template for the agent's instructions.md
  eval_template.py              # Template for the eval script
  launch_prompt.md              # Template for the Claude Code launch prompt
references/
  lessons.md                    # Real-world findings from two production autoresearch runs
```

## Quick start

In Claude Code, with your codebase open:

```
/autoresearch
```

The skill will ask about your target function, metric, and test data, then generate the experiment harness tailored to your codebase.

Once generated, paste the contents of `launch_prompt.md` into a new Claude Code session to start the autonomous loop.

## Templates

The `templates/` directory contains starter templates. **Do not use them as-is** — the skill adapts them heavily to your specific codebase. They define the structure and required sections.

### `instructions_template.md`

The agent's operating manual. Covers:
- What file it can edit (and what levers exist)
- What it cannot touch (eval script, test data, frozen modules)
- Exact eval command and metric definition
- Strategy guidance: quick wins → main optimization → experimental
- Commit discipline and log format

### `eval_template.py`

Eval script with:
- Metric functions: MRR, Precision@k, Hit Rate, Pass Rate
- Caching pattern for expensive API calls that don't change between iterations
- Standalone and Django management command entry points
- Output format: must print `SCORE: X.XXXX` on its own line

### `launch_prompt.md`

Short prompt to paste into Claude Code. Points the agent at `instructions.md`, establishes baseline, starts the loop.

## Lessons learned

`references/lessons.md` documents findings from two rounds of autoresearch on a production hybrid search system (Django/pgvector/Cohere/Claude). Covers:

- What worked and what didn't (with specific numbers)
- The Redis caching trap that invalidated an entire round
- Why temperature > 0 kills autoresearch signal
- The co-optimization ceiling in sequential rounds
- When to stop (diminishing returns arrive fast)

Read this before designing your first experiment — it will save iterations.

## Key design principles

**One file.** The constrained file discipline is what makes autonomous iteration safe. The agent can't break things it can't touch.

**Fast evals.** Target < 60 seconds per iteration. Cache everything that doesn't change when the constrained file changes. At 30 iterations, a 6-minute eval is 3 hours; a 30-second eval is 15 minutes.

**The failures are the output.** 93% of experiments fail. The value is as much in the definitively eliminated dead ends as in the improvements found. The "what didn't work" section of the final log is often more useful than the score improvement.

**30 iterations is the default.** Most gains come in iterations 10-20. If the score plateaus for 5+ consecutive iterations, the ceiling is architectural, not parametric.
