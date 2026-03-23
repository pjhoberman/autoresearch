# Autoresearch Lessons Learned

Findings from two rounds of autoresearch on a production hybrid search system (Django/pgvector/Cohere embeddings/Claude Haiku metadata extraction). These inform how future autoresearch experiments should be designed.

## Round 1: Ranking Logic Optimization (utils.py)

**Setup:** 44 iterations optimizing keyword re-ranking weights, scoring formulas, normalization, and candidate pool sizes. Metric: 0.8 × Precision@12 + 0.2 × MRR. 20 queries with hand-labeled expected results.

**Result:** +0.027 composite (0.693 → 0.720). 3 changes kept, 41 reverted.

### What worked

1. **Higher base weights scaled by query type.** Location 5x, Activity 3x, General 2x. The system was under-weighting keyword signals relative to embedding similarity. Biggest single gain.

2. **Exponential scoring formula.** `(1-d) * exp(boost*0.3)` instead of `(1-d) * (1+boost)`. Better separation between boosted and unboosted items. Also fixed the one query where MRR wasn't perfect.

3. **Query-type-specific weight tuning.** Different queries need different signal emphasis — location queries need location keywords weighted heavily; general queries need broad keyword matching.

### What didn't work (and why — often more valuable)

- **Larger candidate pools (100→150, 100→200):** Expected articles were already in the top 100 by vector distance. The problem was ranking, not recall. Lesson: check whether your bottleneck is recall or ranking *before* running autoresearch on ranking.

- **Title matching as a signal:** Noisy — irrelevant articles also have query terms in titles. Net negative.

- **Disabling adaptive weighting:** The correlation shrinkage (reduce keyword weight when correlated with embedding similarity) was genuinely preventing double-counting. Removing it caused regressions. Lesson: don't assume complex-looking code is over-engineered.

- **Keyword density scoring (normalize by article length):** Shorter articles aren't more relevant. Length normalization hurts.

- **Body keyword damping formula variations:** Whether `log1p(count) * 0.5` or `log1p(count) * 0.3` or `min(count, 3)` — scores barely moved. The exact damping formula is not where the signal is.

### Key insight

93% of experiments failed. The value of autoresearch is as much in the 41 eliminated dead ends as the 3 improvements found. Manual tuning would have tried 3-4 things and stopped with uncertainty. The agent proved definitively what doesn't matter.

---

## Round 2: Query Metadata Prompt Optimization (embedding_service.py)

**Setup:** 16 iterations optimizing the Claude Haiku prompt that extracts search metadata (dense query rewrite, location/activity/keyword lists). Same test set and metric as Round 1. Round 1's ranking changes frozen.

**Result:** No improvement. 0.705 → 0.705. Zero changes kept.

### Critical discovery: Redis caching

`get_query_metadata()` caches results by `hash(query)`, not `hash(query + prompt)`. Prompt changes had ZERO effect until the cache was manually cleared. First 2 iterations showed false improvements because they were reading stale cached data.

**Lesson for all future autoresearch:** If the system under test has any caching layer, verify that the cache key includes everything that could change between iterations. Add `cache.clear()` to the eval script if needed, or include a prompt version hash in the cache key.

### What we learned

1. **Co-optimization trap.** Round 1 tuned the ranking math to work with the specific metadata distribution the original prompt produces. Freezing the ranking and changing the prompt is like tuning a guitar string by string — changing one detunes the others. Every prompt change that improved location queries degraded activity queries. The Round 1 weights were calibrated to the original prompt's output.

   **Lesson:** Sequential round optimization (tune A → freeze A → tune B) has a lower ceiling than co-optimizing A and B together. If you must go sequential, expect Round 2 to find less.

2. **Dense field is highest-leverage and most fragile.** The `dense` rewrite gets embedded and drives the initial candidate pool (top 500). Any change to the dense output changes which articles are candidates, causing large unpredictable score swings. Changes that improved one query type consistently degraded another — the original was at a Pareto boundary.

   **Lesson:** If your system has a component whose output determines the candidate set, that component has outsized influence and is hard to optimize incrementally. Small changes cascade.

3. **Keywords don't matter (in this system).** With identical dense embeddings (0 cache misses), keyword/location/activity list changes produced ZERO score change. The adaptive weighting + z-score normalization makes the ranking so robust to keyword variation that the keyword pipeline is essentially decorative.

   **Lesson:** Before running autoresearch on a component, verify that component actually influences the metric. A quick test: manually set the component's output to garbage and see if the score changes. If it doesn't, don't waste iterations on it.

4. **Temperature >0 kills autoresearch signal.** Three runs with identical prompt at temp=0.4 gave scores of 0.678, 0.705, 0.695 — a 0.027 range. The original "baseline" of 0.718 was from one lucky temperature sample. At temp=0, scores stabilized.

   **Lesson:** Any LLM in the eval path must run at temperature=0 for autoresearch to produce reliable signal. The improvement you're looking for (~0.01-0.03 per iteration) is smaller than temperature noise.

---

## General Lessons

### On eval design

- **Cache everything that doesn't change between iterations.** API calls that depend on the query (not the constrained file) should be pre-computed and monkey-patched in. This took eval time from 6 minutes to 30 seconds.

- **Composite metrics with guardrails work well.** `0.8 * precision + 0.2 * MRR` let the agent optimize precision (where there was room) while MRR acted as a guardrail against top-1 regressions. A warning at MRR < 0.90 caught real regressions without blocking small trade-offs.

- **Test data labeling is the hardest part.** We ran each query, reviewed top 50 results, and hand-labeled relevant ones. 20 queries × 50 results = ~1,000 relevance judgments. This took longer than setting up the entire autoresearch harness. LLM-assisted labeling (have Claude evaluate relevance) can bootstrap this but introduces noise.

- **Minimum 15-20 test cases** to get stable aggregate metrics. Fewer and individual query variance dominates.

### On the autoresearch pattern

- **The "what didn't work" section of the log is the most valuable output.** It maps the boundary of what's optimizable within the current architecture. "You can stop tuning this" is an underrated finding.

- **Diminishing returns are fast.** Most gains came in iterations 10-20 out of 44. The last 14 iterations moved the score by 0.000. If the score plateaus for 5+ iterations, the ceiling is architectural.

- **The pattern is for tuning, not for design.** Autoresearch finds the optimal configuration of an existing system. It can't redesign the system. If the agent's final report says "the next improvement requires [architectural change]," believe it.

- **30 iterations is a good default.** Enough to explore the space; not so many that you waste compute on a plateaued score. 44 was overkill for Round 1 — the gains were done by iteration 30.

### On multi-round experiments

- **Same test data across rounds** provides continuity. Different test data makes rounds incomparable.

- **Read the Round N log before designing Round N+1.** The "recommended next steps" section tells you exactly what to target and what constraints to change.

- **Sequential rounds have a co-optimization ceiling.** Round 1 overfits to the current state of frozen components. Round 2 can't improve those components without undoing Round 1's gains. If you need to optimize two coupled components, either co-optimize them in one round (constrain both files, let the agent edit either) or accept a lower ceiling.
