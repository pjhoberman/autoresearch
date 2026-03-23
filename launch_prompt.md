# Claude Code Launch Prompt — [TODO: Round N]

[TODO: Copy and paste this into Claude Code after filling in the blanks]

```
Read instructions[TODO: _N].md to understand the autoresearch experiment setup.

1. Read [TODO: path/to/constrained/file] to understand the current logic.
[TODO: Optional — 2. Read [other file] to understand how the constrained file's output is used.]
2. Run `[TODO: eval command] --verbose` to establish the baseline score.
3. Record the baseline in instructions[TODO: _N].md and autoresearch_log[TODO: _N].md.
4. Start the autoresearch loop: form a hypothesis, edit only [TODO: constrained file], run eval, keep improvements (commit with score delta), revert failures. Log every iteration to autoresearch_log[TODO: _N].md.
5. Run [TODO: 30] iterations. Summarize every 10. Write a final report when done.
```

## If baseline is already known

[TODO: Fill in the baseline from a previous run and use this shorter version:]

```
Read instructions[TODO: _N].md. Baseline SCORE is [TODO: X.XXXX] ([TODO: key metrics]). Start the autoresearch loop. Run [TODO: 30] iterations. Log everything to autoresearch_log[TODO: _N].md. When done, write the final report.
```
