# Evals And Replay

`EvalCase` defines event input and expected decision effect. `EvalRunner` runs cases through a kernel. `ReplayEngine` replays historical event dictionaries and can diff against baseline decisions.

Use cases:

- validate rule changes before enabling them
- detect regression from historical traces
- keep shadow rule reports separate from active policy decisions

The current report format is JSON-friendly and intentionally small.
