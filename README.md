# Autoresearch — Claude Code Plugin

93% of experiments fail. The value is in the 41 dead ends you eliminated, not only the 3 improvements you found.

This is a Claude Code plugin for running autonomous experiment loops on any codebase with a measurable metric. **The pattern:** one file, one metric, one loop. An agent edits a constrained file, runs an eval, keeps improvements, reverts failures, and repeats — unattended.

Based on [Karpathy's autoresearch](https://github.com/karpathy/autoresearch), generalized beyond ML training to any code with a measurable outcome.

## Skills

### `/autoresearch-discover [path/to/directory]`

Don't know where to start? This skill scans your codebase for autoresearch candidates — files with tunable parameters, magic numbers, scoring logic, or prompt templates that could be optimized against a metric. It outputs a ranked list with suggested metrics and eval difficulty, so you can pick a target and run `/autoresearch` on it.

### `/autoresearch path/to/file.py`

The main skill. Once you know what to optimize:

1. Reads the constrained file to identify tunable levers, then asks about your metric
2. Generates a complete experiment harness: `instructions.md`, eval script, test data template, and launch prompt
3. (Optional) Runs validation to confirm the eval produces a stable score
4. Hands off to an autonomous Claude Code agent to run N iterations overnight

## When to use it

- **Discover:** You have a codebase and want to know what's optimizable
- **Autoresearch:** You have a specific file with tunable code and a measurable metric

## When NOT to use it

- The problem requires a refactor, not tuning
- There's no clear numerical metric to optimize
- The eval is noisy or non-deterministic (network calls, random seeds, timing)
- The fix is obvious and doesn't need iterative search

## Installation

### As a plugin (recommended)

```
/plugin marketplace add pjhoberman/autoresearch
/plugin install autoresearch@autoresearch-marketplace
```

After installation, invoke with `/autoresearch:autoresearch path/to/file.py`.

### Updating

```
/plugin marketplace update autoresearch-marketplace
```

### Manual

Copy the `skills/autoresearch/` and `skills/autoresearch-discover/` directories into your project's `.claude/skills/` folder. This gives you `/autoresearch` and `/autoresearch-discover` directly.

### Local development

```bash
claude --plugin-dir /path/to/this/repo
```

## Repository structure

```
.claude-plugin/
  plugin.json                   # Plugin manifest
  marketplace.json              # Marketplace catalog for distribution
skills/
  autoresearch-discover/
    SKILL.md                    # Codebase scanner — find optimization candidates
  autoresearch/
    SKILL.md                    # Main skill — generate experiment harness
    templates/
      instructions_template.md  # Template for the agent's instructions.md
      eval_template.py          # Template for the eval script
      launch_prompt.md          # Template for the Claude Code launch prompt
    references/
      lessons.md                # Real-world findings from production autoresearch runs
```

## Quick start

In Claude Code, with your codebase open:

```
# Step 1: Find optimization candidates
/autoresearch-discover

# Step 2: Pick a target and run autoresearch
/autoresearch path/to/scoring.py
```

If installed as a plugin, prefix with the plugin name: `/autoresearch:autoresearch-discover` and `/autoresearch:autoresearch path/to/scoring.py`.

The discover skill scans for tunable code and suggests metrics. Pick a candidate, then pass the file path to `/autoresearch` — it reads the file, identifies tunable levers, asks about your metric, generates the experiment harness, and hands off to an autonomous loop.

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

`references/lessons.md` documents findings from 60 iterations across two rounds on a production hybrid search system (Django/pgvector/Cohere/Claude Haiku). This is what separates this plugin from other autoresearch tools — real production data, not theory. Covers:

- What worked and what didn't (with specific numbers)
- The Redis caching trap that invalidated an entire round
- Why temperature > 0 kills autoresearch signal
- The co-optimization ceiling in sequential rounds
- When to stop (diminishing returns arrive fast)

Read this before designing your first experiment — it will save you an entire wasted round.

## Key design principles

**One file.** The constrained file discipline is what makes autonomous iteration safe. The agent can't break things it can't touch.

**Fast evals.** Target < 60 seconds per iteration. Cache everything that doesn't change when the constrained file changes. At 30 iterations, a 6-minute eval is 3 hours; a 30-second eval is 15 minutes.

**The failures are the output.** 93% of experiments fail. The value is as much in the definitively eliminated dead ends as in the improvements found. The "what didn't work" section of the final log is often more useful than the score improvement.

**30 iterations is the default.** Most gains come in iterations 10-20. If the score plateaus for 5+ consecutive iterations, the ceiling is architectural, not parametric.

**Guard what matters.** Optional guard metrics prevent the agent from improving one metric at the expense of another. Optimize precision while guarding MRR. Optimize speed while guarding accuracy.

**Survive compaction.** The JSONL state file lets the agent recover after context window compaction — critical for 30+ iteration overnight runs.

**Noise-aware.** Baseline stability checks and min-delta thresholds prevent the agent from chasing variance instead of signal.

## Examples

### Discovery output

Running `/autoresearch-discover` on a Django search backend might return something like this:

```
Autoresearch Discovery Report — 6 candidates found
Ranked by: eval feasibility × impact × isolation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RANK 1 — search/geocoding.py                          ★★★ START HERE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tunable parameters: 8
  - NEARBY_RADIUS_KM (currently 25)
  - CITY_POPULATION_TIERS = [10_000, 50_000, 250_000, 1_000_000]
  - FALLBACK_RADIUS_MULTIPLIER (currently 2.5)
  + 2 more distance/tier thresholds

Suggested metric: address match accuracy on labeled dataset
Eval difficulty: LOW — validation tools already exist, ~200 labeled examples in fixtures/
Notes: Best eval infrastructure already in place. Self-contained with no shared state.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RANK 2 — search/scoring.py                            ★★ HIGH BUSINESS IMPACT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tunable parameters: 5
  - QUALITY_WEIGHTS = {completeness: 0.4, popularity: 0.3, recency: 0.2, verified: 0.1}
  - MIN_SCORE_TO_INDEX (currently 0.45)

Suggested metric: MRR@10 or NDCG@10 on search query log
Eval difficulty: MEDIUM — need to build eval harness, but labeled data exists
Notes: Controls what surfaces to users. Most business-critical. Interacts with RANK 3.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RANK 3 — search/promotion.py                          ★★ HIGH BUSINESS IMPACT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tunable parameters: 3
  - DISTANCE_DECAY_COEFFICIENT (currently 0.8)
  - MIN_REVIEWS_TO_PROMOTE (currently 5)
  - MIN_UNIQUE_USERS_TO_PROMOTE (currently 3)

Suggested metric: precision@5 on promoted-result audit set
Eval difficulty: MEDIUM
Notes: Gate for surfacing results to wider audiences. Optimize after RANK 2 — they interact.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RANK 4 — matching/similarity.py                       ★ MODERATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tunable parameters: 4
  - EMBEDDING_SIMILARITY_THRESHOLD (currently 0.82)
  - EXACT_MATCH_BOOST (currently 1.5)
  - FUZZY_MATCH_MIN_RATIO (currently 0.7)
  - DEDUP_OVERLAP_THRESHOLD (currently 0.9)

Suggested metric: duplicate detection F1 on labeled pairs
Eval difficulty: MEDIUM — labeled pairs dataset needs curation (~2h work)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RANK 5 — display/snippet.py                           ★ MODERATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tunable parameters: 4
  - MAX_SNIPPET_LENGTH (currently 160)
  - CONTEXT_WINDOW_CHARS (currently 80)
  - HIGHLIGHT_MAX_TERMS (currently 3)
  - TRUNCATE_AT_SENTENCE_BOUNDARY (currently True)

Suggested metric: human preference score or click-through rate proxy
Eval difficulty: HIGH — no ground truth; needs LLM-as-judge or user study

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RANK 6 — taxonomy/tag_linker.py                       ★ LOW PRIORITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tunable parameters: 3
  - TAG_CONFIDENCE_THRESHOLD (currently 0.6)
  - MAX_TAGS_PER_ITEM (currently 8)
  - PARENT_TAG_BOOST (currently 1.2)

Suggested metric: taxonomy coverage on labeled item set
Eval difficulty: HIGH — limited labeled data; tag ontology changes frequently

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDATION: Start with search/geocoding.py (RANK 1).
It has the best eval infrastructure already in place. Once you have a
working eval loop, RANK 2 + 3 are higher impact but require harness setup.
Avoid RANK 5 and 6 until you have a reliable automated metric.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

From here, run `/autoresearch search/geocoding.py` — it reads the file, confirms the metric with you, generates the eval harness, and hands off to the autonomous loop.

## Prior art

- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — The original. 630-line script, single GPU, ML training optimization. 42K+ stars.
- [SkyPilot: Scaling Autoresearch](https://blog.skypilot.co/scaling-autoresearch/) — 16 GPUs, 910 experiments in 8 hours. Showed that parallelism changes what the agent can discover.
- [Tobi Lütke / Shopify](https://x.com/tobi) — First non-ML application. 53% faster Liquid template rendering from ~120 automated experiments.
- [uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) — Domain-agnostic Claude skill with subcommands.
- [pi-autoresearch](https://github.com/davebcn87/pi-autoresearch) — Autoresearch extension for the Pi editor.
