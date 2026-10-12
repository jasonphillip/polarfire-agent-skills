# Codex workflow exercise, 2026-10-12

Client: codex-cli 0.157.1 through the local companion (gpt-6-sol, low effort) in the kit checkout at commit de115e5. No plugin manifest was consumed: Codex read skills/*/SKILL.md and agents/polarfire-bringup.md directly from the repo, as the prompt allowed. That is the tested claim for Codex: it can follow the skill files from the checkout; a plugin install was not tested.

Report (verbatim, paths replaced):

# Signal frequency example through inspect

## Outcome

- Working directory: `<kit-root>`.
- Exact run command: `.venv/bin/pfkit example run signal-freq --until inspect --run-dir reports/codex-exercise-1791842416`.
- Exit code: **0**, observed from the command process and recorded in `reports/codex-exercise-1791842416/commands.jsonl:6`.
- Operators, in order: `CONV_2D`, `CONV_2D`, `CONV_2D`, `RESHAPE`. Each has `supported: true` (`reports/codex-exercise-1791842416/inspect.json:18,37,46,65,74,93,101,109`).
- Flags: `per-channel quantization tensor 4`, `per-channel quantization tensor 5`, `per-channel quantization tensor 6`, `per-channel quantization tensor 7` (`reports/codex-exercise-1791842416/inspect.json:3-8`). `blocking_flags`, `limit_violations`, and `unsupported` are empty (`inspect.json:2,9,666`).
- Evaluation: MAE **0.6749171018600464 hertz**, RMSE **0.8896375894546509 hertz**, 128 test samples (`reports/codex-exercise-1791842416/eval.json:2-5`).
- Compile, simulation, inference, and comparison are `not run` (`reports/codex-exercise-1791842416/summary.md:10-13`). Inspection is a local gate, not a compile or kit result.

## Files read

Read the agent `agents/polarfire-bringup.md` and these complete skill files: `skills/adapt-your-model/SKILL.md`, `skills/claim-log/SKILL.md`, `skills/dataset-and-training/SKILL.md`, `skills/fabric-watchdog-fallback/SKILL.md`, `skills/hls4ml-libero-route/SKILL.md`, `skills/kit-program/SKILL.md`, `skills/kit-run-inference/SKILL.md`, `skills/libero-build/SKILL.md`, `skills/smarthls-fixed-point/SKILL.md`, `skills/vbx-compile/SKILL.md`, `skills/vbx-export-int8/SKILL.md`, and `skills/vbx-ops-guard/SKILL.md`. Also read the referenced `docs/contracts.md`, `docs/adapters.md`, `docs/claims.md`, and `examples/signal-freq/example.yaml`.

## Action transcript

1. Ran `pwd; rg --files skills agents | sort` (exit 0). It identified the kit root, one agent, and the 12 skill files named above.
2. Ran `for f in skills/*/SKILL.md agents/polarfire-bringup.md; do printf '\\n=== %s ===\\n' "$f"; cat "$f"; done` (exit 0). Read all listed instructions.
3. Ran `for f in docs/contracts.md docs/adapters.md docs/claims.md examples/signal-freq/example.yaml; do printf '\\n=== %s ===\\n' "$f"; cat "$f"; done` (exit 0). The example contract selects `mlp`, 64 input samples, default 512/128/128 splits, and 60 epochs.
4. Ran `ls -ld reports/codex-exercise-1791842416 .venv/bin/pfkit` (exit 2). The run directory did not exist; `.venv/bin/pfkit` existed and was executable. This was a preflight check, not a failed run.
5. Ran the exact run command above (exit 0). Displayed stages: `data`, `train`, `eval`, `export`, `inspect`; then `reports/codex-exercise-1791842416/summary.md`. The CLI displayed data shapes, 60 training epochs, the evaluation metrics above, export metadata, and an inspect excerpt. TensorFlow printed converter warnings and informational lines. The full result is in the run files. `commands.jsonl:1-6` records each stage with exit code 0.
6. Ran `nl -ba reports/codex-exercise-1791842416/inspect.json | head -80; nl -ba reports/codex-exercise-1791842416/eval.json; nl -ba reports/codex-exercise-1791842416/commands.jsonl; nl -ba reports/codex-exercise-1791842416/summary.md | head -80` (exit 0). The first `head` caused the expected `nl: write error: Broken pipe` while truncating display; it did not affect the completed run. This read confirmed the metrics, stage exit codes, and unrun stages.
7. Ran `.venv/bin/python -c 'import json; p="reports/codex-exercise-1791842416/inspect.json"; d=json.load(open(p)); print("operators:", [(x["index"],x["operator"],x["supported"]) for x in d["operators"]]); print("flags:",d["flags"]); print("blocking_flags:",d["blocking_flags"]); print("limit_violations:",d["limit_violations"]); print("unsupported:",d.get("unsupported_operators"))'` (exit 0). It returned the four operators and four flags above; the queried `unsupported_operators` key returned `None`, so the actual `unsupported` field was checked next.
8. Ran `rg -n '"operator"|"supported"|"unsupported"|"blocking_flags"|"limit_violations"|"flags"' reports/codex-exercise-1791842416/inspect.json` (exit 0). It confirmed all operator line positions and `"unsupported": []` at line 666.
9. Ran `mkdir -p /tmp/codex-task` (exit 0), then wrote this requested report file. No git command was run. The pfkit command wrote its outputs within `reports/codex-exercise-1791842416`; this report is the sole requested write outside `reports/`.

## Changes and verification

The run created the requested run directory and its data, checkpoint, export, inspection, and summary artifacts. No source, skill, agent, or configuration file was changed. The process exit code and `commands.jsonl:1-6` verify the staged command succeeded. The saved `inspect.json` and `eval.json` provide the reported values. Network, compiler, simulator, and hardware were not used.
