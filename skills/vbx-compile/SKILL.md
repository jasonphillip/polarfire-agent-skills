---
name: vbx-compile
description: Route V250 compilation to the pfkit tools host stage.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# V250 compile entry

Use `kit-run-inference` for the canonical compile and simulator commands.
This skill keeps the earlier compile name available.
It does not call the compiler through a second path.

## Inputs

Name the example and its run directory.
Read `model.tflite`, `export.manifest.json`, and `inspect.json`.
The inspect result must have empty failure lists.
Read `toolshost.yaml` and confirm the tools host configuration.
The tools host needs the pinned SDK environment.
The target for this kit is V250.
Read `docs/scope.md` for the tested SDK and IP pairing.

## Execution

Follow `kit-run-inference` at its compile stage.
It calls the pfkit remote plan and writes `model.vnnx`.
Use a dry run first when reviewing SSH and file paths.
A dry run records `status: not run` in `compile.json`.
It does not prove that the compiler accepted the model.
After an actual run, inspect the command records and artifact hash.
Stop on any nonzero exit or compiler error.

## Evidence

Keep the TFLite input hash with the VNNX output hash.
Keep the SDK version with the compile record.
Do not compare hashes across different input models.
Do not infer simulator or kit behavior from a compile result.
Use the simulator stage before reporting output agreement.
Use hardware output before reporting kit behavior.

The case study describes compiler flags for its own model.
The kit's current compile command is owned by pfkit.
Do not copy model-specific flags or filenames from the case study.
See `docs/pipeline.md` for the current remote command contract.

## Checks

- Read an inspect pass from `inspect.json` before compiling.
- Read command exit codes and status from `compile.json`.
- Read the VNNX output size and hash from the run directory record.
- Read SDK version from the tools host output before naming a pairing.
