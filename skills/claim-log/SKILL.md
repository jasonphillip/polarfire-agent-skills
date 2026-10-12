---
name: claim-log
description: Tie every model and hardware result to a run directory file.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Claim log

Use `docs/contracts.md` and `docs/claims.md` for evidence boundaries.
Read the current run directory before writing a result row.
Run the canonical report command in `adapt-your-model` after the last completed stage.
The report records package versions, revisions, command history, and file hashes.
It does not turn a missing stage into a completed stage.

## Row format

Keep one row for each check and evidence class.
Name the example, input, model, and run directory.
Name the exact result file beside the measured value.
Name the command and its exit code when available.
Label the evidence class as local test, compile, simulation, synthesis, or kit.
Use `not run` for stages without output.
Do not copy a measurement from a different model, kit, or image.
Keep failed checks visible in the table.
Mark an inference as an inference and state its missing check.

## Model evidence

`dataset.manifest.json` records data shape and hash.
`training.json` records epochs and checkpoint hash.
`eval.json` records test error and units.
`export.manifest.json` records TFLite identity and calibration.
`inspect.json` records graph and tensor acceptance.
`compare.json` records each numerical comparison and its tolerance.

## Remote evidence

`compile.json`, `sim.json`, and `infer.json` record remote commands.
`hw.json` is the runner's hardware metadata.
`commands.jsonl` records command times and exit codes.
`artifacts.json` records hashes of files in the run directory.
`summary.md` lists recorded and unrun stages.
A compiler pass is an artifact result.
A simulator pass is a simulation result.
A kit pass needs actual kit output.
A timing claim needs the current timing report.

## Reporting rule

Never write a number that was not read from tool output.
Every result row cites a run directory file.
For hardware build results, cite the raw report outside the model run as well.
Keep the original output when a parser fails.
Do not mark an unparseable result as a pass.

## Checks

- Read a run directory file path beside each result row.
- Read the command exit code and artifact identity for each completed stage.
- Read `not run` explicitly for each absent stage.
- Read raw hardware output before reporting timing or kit behavior.
