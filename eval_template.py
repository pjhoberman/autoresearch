"""
Autoresearch eval script — [TODO: Round N description]

Runs test cases against the target function and outputs a single SCORE line.

[TODO: Choose one]
- Standalone script: `python eval.py`
- Django management command: `uv run manage.py run_autoresearch_eval`

CACHING: [TODO: Describe caching strategy or delete this section]
- First run computes [TODO: what] and saves to [TODO: cache file]
- Subsequent runs load from cache, skipping [TODO: expensive calls]
- Delete cache file to recompute: [TODO: filename]

DO NOT MODIFY THIS FILE DURING AUTORESEARCH RUNS.
"""

import json
import sys
import time
from pathlib import Path

# [TODO: Framework-specific imports]
# For Django management command, uncomment:
# from django.core.management.base import BaseCommand
# from unittest.mock import patch

# ============================================================
# Configuration
# ============================================================

DEFAULT_TEST_DATA_PATH = "test_queries.json"  # [TODO: adjust filename]
CACHE_PATH = ".autoresearch_cache.json"  # [TODO: adjust or remove]


# ============================================================
# Metric functions — pick what fits your use case
# ============================================================

def precision_at_k(retrieved: list[str], expected: list[str], k: int = 10) -> float:
    """What fraction of the top-k results are in the expected set?"""
    retrieved_k = retrieved[:k]
    if not retrieved_k:
        return 0.0
    hits = sum(1 for r in retrieved_k if r in expected)
    return hits / len(retrieved_k)


def hit_rate(retrieved: list[str], expected: list[str], k: int = 10) -> float:
    """Did at least one expected result appear in the top-k?"""
    retrieved_k = set(retrieved[:k])
    return 1.0 if retrieved_k & set(expected) else 0.0


def reciprocal_rank(retrieved: list[str], expected: list[str]) -> float:
    """1/rank of the first expected result found. 0 if none found."""
    expected_set = set(expected)
    for i, r in enumerate(retrieved, 1):
        if r in expected_set:
            return 1.0 / i
    return 0.0


def pass_rate(results: list[bool]) -> float:
    """Fraction of test cases that passed."""
    if not results:
        return 0.0
    return sum(results) / len(results)


# ============================================================
# Caching — adapt or remove based on your setup
# ============================================================

def load_cache():
    """Load cached data from disk."""
    cache_file = Path(CACHE_PATH)
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    """Save cache to disk."""
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def build_cache(test_cases):
    """
    Pre-compute expensive operations that don't change between iterations.

    [TODO: Implement for your use case. Examples:]
    - API calls for embeddings that depend on the query, not the constrained file
    - LLM metadata extraction that's frozen for this round
    - Database lookups for test fixtures
    """
    cache = {}
    for i, item in enumerate(test_cases):
        key = item["query"]  # [TODO: adjust cache key]
        print(f"  Caching {i+1}/{len(test_cases)}: \"{key}\"")

        # [TODO: Replace with actual expensive calls to cache]
        # Example:
        # cache[key] = {
        #     "metadata": get_query_metadata(key),
        #     "embedding": get_embedding(key),
        # }

    return cache


# ============================================================
# Main eval logic
# ============================================================

def run_eval(test_data_path: str = DEFAULT_TEST_DATA_PATH, k: int = 10, verbose: bool = False):
    """
    Run all test cases and compute aggregate metrics.

    [TODO: Adapt this function to your specific setup]
    """
    with open(test_data_path) as f:
        test_cases = json.load(f)

    if not test_cases:
        print("ERROR: test data is empty", file=sys.stderr)
        sys.exit(1)

    # [TODO: Load or build cache if applicable]
    # cache = load_cache()
    # if not cache:
    #     cache = build_cache(test_cases)
    #     save_cache(cache)

    rrs = []
    precisions = []
    hits = []
    times = []

    for i, item in enumerate(test_cases):
        query = item["query"]  # [TODO: adjust field names]
        expected = set(item["expected"])  # [TODO: adjust]

        start = time.monotonic()
        try:
            # [TODO: Replace with your actual function call]
            # Example with caching + monkey-patching:
            # cached = cache[query]
            # with patch("module.expensive_func", return_value=cached["value"]):
            #     results = your_function(query)
            # retrieved = [str(r.id) for r in results]

            retrieved = []  # [TODO: Replace]
            expected_str = {str(e) for e in expected}
        except Exception as e:
            print(f"  ERROR on '{query}': {e}", file=sys.stderr)
            rrs.append(0.0)
            precisions.append(0.0)
            hits.append(0.0)
            times.append(0.0)
            continue

        elapsed = time.monotonic() - start
        times.append(elapsed)

        rr = reciprocal_rank(retrieved, list(expected_str))
        p = precision_at_k(retrieved, list(expected_str), k)
        h = hit_rate(retrieved, list(expected_str), k)

        rrs.append(rr)
        precisions.append(p)
        hits.append(h)

        if verbose:
            status = "HIT" if rr > 0 else "MISS"
            print(f"  [{status}] Q{i+1}: \"{query}\" | RR={rr:.3f} | P@{k}={p:.3f} | {elapsed:.2f}s")
            if rr == 0:
                print(f"         Expected: {expected_str} | Got top 3: {retrieved[:3]}")

    # Aggregate
    n = len(test_cases)
    mrr = sum(rrs) / n
    mean_precision = sum(precisions) / n
    hit_rate_avg = sum(hits) / n
    avg_time = sum(times) / n
    total_time = sum(times)

    # ============================================================
    # SCORE — customize this to your needs
    # ============================================================

    # [TODO: Pick one or define your own composite]

    # Option A: Single metric
    # score = mrr

    # Option B: Composite with guardrail
    # score = 0.8 * mean_precision + 0.2 * mrr

    # Option C: Pass rate (for boolean test cases)
    # score = pass_rate(results)

    score = mean_precision  # [TODO: Replace with your chosen metric]

    # ============================================================
    # Output — SCORE line must be present and parseable
    # ============================================================

    print()
    print("=== EVAL RESULTS ===")
    print(f"  MRR:            {mrr:.4f}")
    print(f"  Precision@{k}:   {mean_precision:.4f}")
    print(f"  Hit Rate@{k}:    {hit_rate_avg:.4f}")
    print(f"  Queries:        {n}")
    print(f"  Avg time/query: {avg_time:.2f}s")
    print(f"  Total time:     {total_time:.1f}s")
    print("========================")
    print(f"\nSCORE: {score:.4f}")

    # [TODO: Optional guardrail warning]
    # if mrr < 0.90:
    #     print(f"  ⚠️  MRR dropped to {mrr:.4f} — investigate")


# ============================================================
# Entry point — choose standalone or Django management command
# ============================================================

# --- Standalone script ---
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", default=DEFAULT_TEST_DATA_PATH)
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()
    run_eval(args.queries, args.k, args.verbose)

# --- Django management command (uncomment and adapt) ---
# class Command(BaseCommand):
#     help = "Run autoresearch evaluation"
#
#     def add_arguments(self, parser):
#         parser.add_argument("--queries", default=DEFAULT_TEST_DATA_PATH)
#         parser.add_argument("--verbose", action="store_true")
#         parser.add_argument("--k", type=int, default=10)
#
#     def handle(self, *args, **options):
#         run_eval(options["queries"], options["k"], options["verbose"])
