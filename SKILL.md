---
name: autoresearch
description: "Set up and run Karpathy-style autoresearch experiments on any codebase with a measurable metric. Use this skill whenever the user wants to autonomously optimize code by running iterative experiments — tuning search ranking, scoring functions, prompt templates, weight parameters, algorithm configurations, or any logic where changes can be evaluated against a numerical metric. Also trigger when the user mentions 'autoresearch', 'overnight optimization', 'autonomous experiments', 'autoresearch loop', 'Karpathy loop', or wants to 'let Claude Code optimize this while I sleep'. This skill generates the full experiment harness: instructions.md, eval script, test data template, and launch prompt — scoped to their specific codebase."
---

# Autoresearch Skill

Set up autonomous experiment loops on any codebase. The pattern: **one file, one metric, one loop.** An agent edits the constrained file, runs the eval, keeps improvements, reverts failures, repeats.

Based on Karpathy's autoresearch pattern, generalized beyond ML training to any code with a measurable outcome.

## When to use this

- User wants to optimize a scoring/ranking/search function
- User wants to tune weights, thresholds, or parameters in a function
- User wants to improve a prompt template's downstream effect on a metric
- User has code with a measurable quality metric and wants autonomous iteration
- User says "autoresearch", "optimize this overnight", "run experiments on this"

## When NOT to use this

- The problem is architectural (needs a refactor, not tuning)
- There's no clear numerical metric to optimize
- The eval would be noisy/non-deterministic (network calls, timing-dependent)
- The fix is obvious and doesn't need iterative search

## Process

### Phase 1: Analyze the codebase

Before generating any files, understand what you're working with:

1. **Read the target code.** Identify:
   - What does the function/system do?
   - What are the tunable levers? (weights, thresholds, formulas, parameters, prompt text)
   - What's the constrained file — the ONE file the agent should edit?
   - What should be frozen? (APIs, data sources, schema, other modules)

2. **Identify the metric.** Ask the user:
   - What does "better" mean? (accuracy, precision, recall, speed, score, pass rate)
   - Is there existing test data, or do we need to create it?
   - Can the eval run without external API calls? If not, what can be cached?

3. **Check for eval speed.** The loop needs fast iterations:
   - If eval takes >30s, identify what can be cached between iterations
   - API calls that don't change when the constrained file changes should be cached
   - Database queries that depend on the constrained file must run fresh
   - Target: <60s per iteration, ideally <10s

### Phase 2: Generate the experiment harness

Generate four files, customized to the user's codebase. Use the templates in `templates/` as starting points, but adapt heavily — every autoresearch setup is different.

#### 1. `instructions.md`

Read `templates/instructions_template.md` for the full structure. Key sections to customize:

- **System Context**: Brief description of what the code does and how it works
- **Constrained file**: Exact path. List the specific tunable levers.
- **Frozen files**: Everything the agent must not touch, and why.
- **Eval command**: Exact command to run (e.g., `uv run manage.py run_autoresearch_eval`)
- **Metric definition**: What SCORE means, how it's computed, what baseline is.
- **Strategy guidance**: Ordered list of what to try, specific to the levers identified in Phase 1. Group into phases (quick wins → main optimization → experimental).
- **Do NOT list**: Specific to this codebase — what would break things.

Important details often missed:
- If the codebase has debug/timing prints, tell the agent not to remove them
- If there are multiple pool sizes or candidate counts, clarify which are tunable
- If there's caching (Redis, file-based), warn the agent about stale data
- Specify the exact revert command for the constrained file

#### 2. Eval script

Read `templates/eval_template.py` for the structure. Key decisions:

**Metric choice:**
- MRR — when top-1 ranking matters most
- Precision@k — when the quality of the full result set matters
- Hit Rate — binary, did we find anything relevant
- Composite — when multiple metrics matter at different weights (e.g., `0.8 * precision + 0.2 * mrr`)
- Custom — pass rate, wall-clock time, F1, whatever the domain requires

**Caching strategy:**
- If the eval calls external APIs that don't depend on the constrained file, cache them on first run
- Use monkey-patching (`unittest.mock.patch`) to intercept API calls and return cached values
- Cache files should be in `.gitignore` and the instructions should warn the agent not to delete them
- Key the cache on the input that triggers the API call, not on the constrained file contents

**For Django projects:** Write as a management command, not a standalone script.

**Output format:** Must print `SCORE: X.XXXX` on its own line — this is what the agent parses.

#### 3. Test data (`test_queries.json` or equivalent)

The hardest part. Options:

- **Manual labeling**: User runs queries, reviews results, picks the good ones. Most reliable. Time-consuming.
- **LLM-assisted labeling**: Run queries, have Claude evaluate relevance of each result. Fast but introduces noise. Best used to generate candidates that the user then validates.
- **Existing ground truth**: If there are logs, A/B test results, or user feedback data, use those.
- **Bootstrapped**: Run the current system, treat top results as pseudo-ground-truth, optimize to match or beat. Fastest but has a ceiling — can't discover results the current system misses.

Minimum 15 test cases. 20-30 is better. Cover the variety of inputs the system handles.

#### 4. Claude Code launch prompt

Short — the instructions.md does the heavy lifting. Include:
- Read instructions.md
- Read the constrained file to understand current state
- Establish or confirm baseline
- Start the loop, N iterations
- Log everything to `autoresearch_log.md`
- Write final report when done

### Phase 3: Validate before launch

Before handing off to Claude Code:

1. **Run the eval once** and confirm it produces a SCORE
2. **Verify the constrained file path** and revert command work
3. **Check cache behavior** — run eval twice, confirm second run is faster
4. **Review test data** with the user — bad labels will send the agent in wrong directions
5. **Estimate iteration time** — multiply by 30 to set expectations for total runtime

### Phase 4: Multi-round experiments

After Round 1 completes, read the log. The "what didn't work" and "recommended next steps" sections tell you what Round 2 should target.

Common patterns:
- **Round 1: ranking/scoring logic** → Round 2: upstream data quality (prompts, feature extraction)
- **Round 1: parameters/weights** → Round 2: formula shape (additive vs multiplicative vs exponential)
- **Round 1: single component** → Round 2: co-optimize two components (requires unfreezing Round 1's file)

For each new round:
- New instructions (`instructions_2.md`)
- New eval script if caching strategy changes (`run_autoresearch_eval_2.py`)
- Same test data (consistency across rounds)
- New log (`autoresearch_log_2.md`)

### Common pitfalls

1. **Caching masks changes.** If the system caches results (Redis, file cache, Django cache), the eval must clear or bypass the cache. Otherwise prompt/logic changes have zero effect.

2. **Non-deterministic evals.** LLM calls with temperature >0, network timing, random seeds — all add noise. Set temperature=0 for any LLM in the eval path if possible. Run baseline 3x to measure variance. If variance > expected improvement, the experiment won't produce signal.

3. **Co-optimization trap.** If Round 1 tunes component A to work with component B's current output, Round 2 can't improve B without re-tuning A. Either co-optimize both simultaneously or accept that sequential optimization has a lower ceiling.

4. **Metric gaming.** The agent will optimize exactly what you measure. If your metric doesn't capture what you care about, the agent will find exploits. Composite metrics with guardrails (e.g., "optimize precision but warn if MRR drops below 0.9") help.

5. **Diminishing returns.** Most gains come in the first 10-15 iterations. If the score plateaus for 5+ consecutive iterations, the ceiling is likely architectural, not parametric. The agent's final report should say this.

## Templates

The `templates/` directory contains starter templates. **Do not use these as-is** — they must be adapted to the specific codebase. They exist to show the structure and remind you of sections to include.

- `templates/instructions_template.md` — Full instructions.md structure with TODOs
- `templates/eval_template.py` — Eval script with multiple metric functions and caching pattern
- `templates/launch_prompt.md` — Claude Code launch prompt template

## References

- `references/lessons.md` — Detailed findings from two rounds of autoresearch on a production search system. Read this before designing a new experiment — it covers caching pitfalls, co-optimization traps, eval design, and when to stop. Especially useful sections: "What didn't work" (saves iteration budget), "General Lessons: On eval design" (caching, metrics, test data), and "On multi-round experiments" (how to plan Round 2).
