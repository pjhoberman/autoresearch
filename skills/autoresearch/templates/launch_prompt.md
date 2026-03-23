# Claude Code Launch Prompt — [TODO: Round N]

[TODO: Copy and paste this into Claude Code after filling in the blanks]

```
Read instructions[TODO: _N].md to understand the autoresearch experiment setup.

1. Read [TODO: path/to/constrained/file] to understand the current logic.
[TODO: Optional — 1b. Read [other file] to understand how the constrained file's output is used.]
2. Run `[TODO: eval command] --verbose` to establish the baseline score.
3. Run the eval 2 more times (3 total) with no changes to confirm baseline stability. Record all 3 scores.
4. Write the config header to autoresearch.jsonl:
   {"type": "config", "constrained_file": "[TODO]", "eval_command": "[TODO]", "metric": "[TODO]", "guard_metric": "[TODO or null]", "guard_threshold": [TODO or null], "baseline": [TODO], "min_delta": [TODO]}
5. Record the baseline in autoresearch_dashboard.md.
6. Start the autoresearch loop: form a hypothesis, edit only [TODO: constrained file], run eval, keep improvements (commit with score delta), revert failures. Log every iteration as a JSON line in autoresearch.jsonl. Update autoresearch_dashboard.md after each iteration.
7. Run [TODO: 30] iterations. Write a final report when done.

IMPORTANT: If you lose context or are resuming, read autoresearch.jsonl and autoresearch_dashboard.md to recover state. The JSONL has every iteration result and the config header has all parameters. Continue from the last iteration number.
```

## If baseline is already known

[TODO: Fill in the baseline from a previous run and use this shorter version:]

```
Read instructions[TODO: _N].md. Baseline SCORE is [TODO: X.XXXX] ([TODO: key metrics]). Start the autoresearch loop. Run [TODO: 30] iterations. Log to autoresearch.jsonl, update autoresearch_dashboard.md after each iteration. When done, write the final report.

IMPORTANT: If you lose context or are resuming, read autoresearch.jsonl and autoresearch_dashboard.md to recover state. Continue from the last iteration number.
```
