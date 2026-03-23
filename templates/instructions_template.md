# Autoresearch Instructions — [TODO: Round N: Description]

> [TODO: If this is Round 2+, summarize what previous rounds found and why this round targets what it does]

## Goal

You are an autonomous research agent. Your job is to **[TODO: improve X by iterating on Y]**. You will:

1. Read the current state of the code
2. Form a hypothesis about what might improve results
3. Make a change to **the allowed file only**
4. Run the eval script
5. If the score improved: **keep the change and commit**
6. If the score did not improve: **revert and try something different**
7. Repeat

## System Context

[TODO: 3-5 sentences describing what the system does, the architecture, and how the constrained file fits into it]

## Rules — READ THESE FIRST

### What you CAN modify
- `[TODO: exact/path/to/file.py]` — this is the ONLY file you may edit.

Specifically, these are the tunable levers:
1. [TODO: List each specific thing the agent can change]
2. [TODO: Be precise — "base weight dicts" not "the code"]
3. [TODO: Include current values where helpful]

[TODO: If there are things in the file the agent should NOT remove (debug prints, timing code), say so explicitly]

### What you CANNOT modify
- `[TODO: eval script name]` — the evaluation script is sacred. Never touch it.
- `[TODO: test data file]` — the test set is fixed. Never touch it.
- `[TODO: cache file if applicable]` — cached API results. Deleting this costs time/money.
- [TODO: List other frozen files with one-line reasons why]
- Do NOT add external API calls or new dependencies
- Do NOT change how [TODO: main function] is called (signature and return type must stay the same)

### Commit discipline
- **Commit after every improvement** with a message: `autoresearch: [description] | score: X.XXX -> Y.YYY | [TODO: key metrics]`
- **Revert failed experiments** cleanly: `git checkout -- [TODO: path/to/constrained/file]`
- Keep a running log in `autoresearch_log[TODO: _N].md` — one line per experiment: iteration number, what you tried, score, kept/discarded

### Iteration budget
- Run **30 iterations** unless told otherwise
- Each iteration should take under [TODO: N] minutes. If longer, something is wrong — stop and report.
- After every 10 iterations, write a summary to `autoresearch_log[TODO: _N].md`

## Eval

```bash
[TODO: exact eval command, e.g. uv run manage.py run_autoresearch_eval]
```

[TODO: Describe the metric(s). What SCORE means, how it's computed, what the guardrails are. Example:]

**SCORE = [TODO: metric formula, e.g. 0.8 × Precision@12 + 0.2 × MRR]**

- [TODO: Primary metric description — what it measures, higher/lower is better]
- [TODO: Secondary metric / guardrail — what threshold triggers a warning]
- Baseline (before any changes): **[TODO: run eval once and record starting score]**

### Caching (if applicable)
[TODO: Describe what's cached, what runs fresh, and why. Warn about deleting cache files. Mention any cache-clearing needed (e.g., Redis). Delete this section if no caching.]

## The [TODO: System/Logic/Pipeline] (what you're optimizing)

[TODO: Describe the processing pipeline in numbered steps. Mark each step as (frozen) or (tunable). Example:]

1. **Step 1** (frozen): User input → preprocessing → structured data
2. **Step 2** (tunable): Structured data → scoring function → ranked results
3. **Step 3** (tunable): Ranked results → final formula → output score

## Strategy Guidance

### Quick wins (iterations 1-5)
- [TODO: Low-hanging fruit specific to this codebase]
- [TODO: Parameter sensitivity checks — double/halve key values]

### Main optimization (iterations 6-20)
- [TODO: Deeper changes to try — formula shapes, scoring approaches]
- [TODO: What the system's known weaknesses are]

### Experimental (iterations 21-30)
- [TODO: Combine best ideas, try unconventional approaches]
- [TODO: If plateaued, document why and what needs upstream changes]

### Do NOT:
- [TODO: Codebase-specific things that would break stuff]
- Rewrite the entire [TODO: component] from scratch in one iteration
- Spend more than 3 consecutive iterations on the same approach if it's not moving the score

## When You're Done

Write a final summary to `autoresearch_log[TODO: _N].md`:

1. **Starting score** and **final score**
2. **Top 3 changes** that had the biggest impact (with specific numbers)
3. **What didn't work** and why
4. **Diminishing returns:** where did the score plateau? What's the likely ceiling?
5. **Recommended upstream changes** — what would require a different approach

Then stop. Do not start a new round without human review.
