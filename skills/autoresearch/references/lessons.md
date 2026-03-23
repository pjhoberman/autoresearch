# Autoresearch Lessons Learned

Findings from real autoresearch experiments on production systems. These inform how experiments should be designed and what pitfalls to expect.

## Case Study: Hybrid Search Ranking Optimization

A production hybrid search system (Django/pgvector/Cohere embeddings/Claude Haiku metadata extraction) was optimized across two rounds.

### Round 1: Ranking Logic — 44 iterations

**Setup:** Optimizing keyword re-ranking weights, scoring formulas, normalization, and candidate pool sizes. Metric: 0.8 × Precision@12 + 0.2 × MRR. 20 queries with hand-labeled expected results.

**Result:** +0.027 composite (0.693 → 0.720). 3 changes kept, 41 reverted.

**What worked:**
- Higher base weights scaled by query type — the system was under-weighting keyword signals relative to embedding similarity. Biggest single gain.
- Exponential scoring formula — better separation between boosted and unboosted items.
- Query-type-specific weight tuning — different queries need different signal emphasis.

**What didn't work (often more valuable):**
- **Larger candidate pools:** Expected results were already in the top-K by vector distance. The bottleneck was ranking, not recall. *Check whether your bottleneck is recall or ranking before optimizing ranking.*
- **Title matching as a signal:** Too noisy — irrelevant items also matched. Net negative.
- **Removing adaptive weighting:** Complex-looking correlation shrinkage was genuinely preventing double-counting. *Don't assume complex code is over-engineered.*
- **Length normalization:** Shorter documents aren't more relevant.
- **Damping formula variations:** Scores barely moved. The exact formula wasn't where the signal was.

**Key insight:** 93% of experiments failed. The value is as much in the 41 eliminated dead ends as the 3 improvements. Manual tuning would have tried 3-4 things and stopped with uncertainty. Autoresearch proved definitively what doesn't matter.

### Round 2: LLM Prompt Optimization — 16 iterations

**Setup:** Optimizing the Claude Haiku prompt that extracts search metadata. Same test set and metric. Round 1's ranking changes frozen.

**Result:** No improvement. Zero changes kept.

**Critical discovery — caching invalidation:** The metadata function cached results by query hash, not by query + prompt hash. Prompt changes had ZERO effect until the cache was manually cleared. First 2 iterations showed false improvements from stale cached data.

**What we learned:**
1. **Co-optimization trap.** Round 1 tuned ranking math to work with the specific metadata distribution the original prompt produced. Changing the prompt while freezing ranking is like tuning a guitar string by string — changing one detunes the others.
2. **Candidate-set components are fragile.** The component whose output determines the candidate set has outsized influence and is hard to optimize incrementally. Small changes cascade unpredictably.
3. **Verify component influence first.** Keyword list changes produced ZERO score change because adaptive weighting made ranking robust to keyword variation. *Before optimizing a component, set its output to garbage and check if the score changes. If it doesn't, don't waste iterations.*
4. **Temperature >0 kills signal.** Three runs with identical prompt at temp=0.4 gave a 0.027 score range. The expected per-iteration improvement (~0.01-0.03) is smaller than temperature noise. *Any LLM in the eval path must run at temperature=0.*

---

## General Lessons

### Eval Design

- **Invalidate caches between iterations.** If the system has any caching layer, verify the cache key includes everything that could change between iterations. Add cache-clearing to the eval script if needed.

- **Cache everything that doesn't change.** API calls that depend only on the input (not the code being optimized) should be pre-computed. This can cut eval time from minutes to seconds.

- **Composite metrics with guardrails work well.** A weighted composite (e.g., 0.8 × primary + 0.2 × secondary) lets the agent optimize where there's room while the secondary metric catches regressions.

- **Test data labeling is the hardest part.** Hand-labeling expected results takes longer than setting up the entire autoresearch harness. LLM-assisted labeling can bootstrap this but introduces noise.

- **Minimum 15-20 test cases** for stable aggregate metrics. Fewer and individual case variance dominates.

### The Autoresearch Pattern

- **The "what didn't work" log is the most valuable output.** It maps the boundary of what's optimizable within the current architecture. "You can stop tuning this" is an underrated finding.

- **Diminishing returns are fast.** Most gains came in iterations 10-20 out of 44. The last 14 iterations moved the score by 0.000. If the score plateaus for 5+ iterations, the ceiling is architectural.

- **The pattern is for tuning, not for design.** Autoresearch finds the optimal configuration of an existing system. It can't redesign the system. If the agent's final report says "the next improvement requires [architectural change]," believe it.

- **30 iterations is a good default.** Enough to explore the space; not so many that you waste compute on a plateaued score.

### Multi-Round Experiments

- **Same test data across rounds** provides continuity. Different test data makes rounds incomparable.

- **Read the Round N log before designing Round N+1.** The "recommended next steps" section tells you exactly what to target and what constraints to change.

- **Sequential rounds have a co-optimization ceiling.** Round 1 overfits to the current state of frozen components. Round 2 can't improve without undoing Round 1's gains. If you need to optimize two coupled components, either co-optimize them in one round (constrain both files, let the agent edit either) or accept a lower ceiling.
