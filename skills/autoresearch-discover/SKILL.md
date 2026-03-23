---
name: autoresearch-discover
description: "Scan a codebase to find files and functions where autoresearch could be applied — code with tunable parameters, magic numbers, scoring logic, or prompt templates that could be optimized against a measurable metric. Use when the user wants to find optimization candidates, asks 'where could I use autoresearch?', 'what can I tune?', 'find tunable code', or wants to discover what's optimizable before running /autoresearch."
args: "[path/to/directory] — optional directory to scope the scan (defaults to current working directory)"
---

# Autoresearch Discover

Scan a codebase to find where autoresearch experiments would be most valuable. Outputs a ranked list of candidates with suggested metrics, so the user can pick one and run `/autoresearch <file>`.

## What to scan for

Search the codebase for these patterns, roughly in order of how likely they are to benefit from autoresearch:

### High-value targets

1. **Scoring/ranking logic** — functions that compute scores, rank items, or sort results. Look for:
   - Weighted sums, linear combinations, composite scores
   - Sort keys or comparators with tunable logic
   - Re-ranking or boosting after an initial retrieval

2. **Magic numbers and thresholds** — hardcoded numeric values that control behavior:
   - Weight multipliers, scaling factors, coefficients
   - Thresholds for filtering, cutoffs, limits
   - Retry counts, batch sizes, pool sizes, top-K values
   - Timeout values, rate limits, backoff multipliers

3. **LLM prompts with downstream metrics** — prompt templates where output quality is measurable:
   - System prompts for classification, extraction, or generation
   - Few-shot examples that could be swapped or reordered
   - Temperature, top-p, and other generation parameters
   - Prompt structure (XML tags vs markdown, ordering of instructions)

4. **Algorithm parameters** — configuration that controls algorithm behavior:
   - Similarity thresholds (cosine, Jaccard, edit distance cutoffs)
   - Normalization strategies (L2, min-max, z-score)
   - Decay functions (linear, exponential, logarithmic)
   - Aggregation methods (mean, median, weighted, harmonic)

### Medium-value targets

5. **Regex patterns and parsing rules** — patterns that extract or match data:
   - Regular expressions that could be more or less permissive
   - String matching strategies (exact, fuzzy, stemmed, n-gram)
   - Tokenization or splitting logic

6. **Feature engineering** — code that transforms raw data into signals:
   - Feature selection (which signals to include)
   - Feature weighting (how much each signal matters)
   - Feature combination (how signals interact — additive vs multiplicative)

7. **Filtering and selection logic** — code that decides what to include/exclude:
   - Candidate generation (how many items to consider)
   - Pre-filtering rules (what gets eliminated early)
   - Deduplication thresholds

### Lower-value (but still worth flagging)

8. **Cache TTLs and expiration policies** — if there's a metric for cache effectiveness
9. **Rate limiting parameters** — if throughput is measurable
10. **UI/UX parameters** — pagination sizes, debounce intervals, animation durations — if there's user engagement data

## What to skip

- **Configuration that's environment-specific** (database URLs, API keys, port numbers)
- **Business logic that's definitional** (tax rates, pricing tiers — these are decisions, not tunables)
- **Code that lacks a measurable outcome** (pure CRUD, simple getters/setters, migrations)
- **Code where the "right answer" is obvious** (a threshold should clearly be 0 or 1, not 0.73)
- **Test files** (unless the user specifically asks)

## Process

### Step 1: Broad scan

Search the codebase for tunable patterns. Use a combination of:

- **Grep for numeric literals** in non-test, non-config files — especially floats (0.5, 0.8, 1.5) and small integers used as parameters
- **Grep for common tunable patterns**: `weight`, `threshold`, `score`, `boost`, `penalty`, `factor`, `coefficient`, `alpha`, `beta`, `gamma`, `lambda`, `decay`, `damping`, `scaling`, `top_k`, `top_n`, `max_`, `min_`, `num_`, `temperature`, `prompt`
- **Look at function signatures** for parameters with default values that look tunable
- **Check config files** (YAML, JSON, TOML, .env) for numeric parameters that feed into logic

### Step 2: Evaluate each candidate

For each candidate file/region, assess:

1. **What's tunable?** List the specific levers (e.g., "3 weight parameters in the scoring function")
2. **What metric could you optimize?** Be specific — not just "accuracy" but "precision@10 of search results against labeled test queries"
3. **Does an eval exist?** Check for existing test suites, benchmarks, or evaluation scripts that could be adapted
4. **Eval feasibility** — how hard would it be to build an eval if one doesn't exist?
   - Easy: existing tests + clear metric, just needs a scoring wrapper
   - Medium: need to create test data but metric is obvious
   - Hard: need to define what "better" means and create labeled data from scratch
5. **Estimated impact** — how much room for improvement is there?
   - Look at whether current values seem arbitrary (round numbers, TODO comments) vs carefully tuned
   - Code with comments like "arbitrary", "magic number", "tune this", "good enough" → high potential
   - Code that's been stable for a long time with no complaints → lower potential

### Step 3: Output the report

Present findings as a ranked list. For each candidate:

```
### Candidate N: [short description]

**File:** `path/to/file.py` (lines X-Y)
**Tunables:** [list of specific parameters/logic that could be optimized]
**Suggested metric:** [specific, measurable metric]
**Eval exists:** Yes / Partial / No
**Eval difficulty:** Easy / Medium / Hard
**Potential:** High / Medium / Low
**Why:** [1-2 sentences on why this is a good autoresearch target]

To run: `/autoresearch path/to/file.py`
```

Rank by: (eval feasibility × potential impact). A high-potential target with no eval path is less actionable than a medium-potential target where you can start tonight.

### Step 4: Recommend a starting point

After the list, recommend which candidate to start with and why. Prefer:
1. Highest impact where an eval already exists or is easy to build
2. Targets where the user can label test data quickly (or it already exists)
3. Targets where the tunables are concentrated in one file (easier to constrain)

If nothing looks like a good autoresearch target, say so. Not every codebase has tunable code — some are pure CRUD, some have already been well-optimized, some need architectural changes rather than parameter tuning.
