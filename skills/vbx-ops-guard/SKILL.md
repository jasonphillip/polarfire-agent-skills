---
name: vbx-ops-guard
description: Route graph and TFLite operator checks to the pfkit inspect gate.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Operator guard entry

Use `adapt-your-model` for the canonical export and inspect steps.
This name remains for users who ask for an operation guard.
The kit's inspect result is the gate before compile.
Read `docs/adapters.md` for graph acceptance rules.
Read `docs/claims.md` for the measured probe limits.

## Before export

Check the example contract's input shape and batch dimension.
Check whether the graph has one input and one output.
Select `mlp` or `conv2d_1k` from the graph structure.
The MLP adapter handles Linear, ReLU, ReLU6, and Flatten.
The convolution adapter handles the stated `(1,k)` graph subset.
Branches, extra inputs, dynamic shapes, and unsupported modules fail.
Do not treat an SDK operator table as a graph acceptance result.

## Inspect gate

Follow `adapt-your-model` to export and inspect the model.
The inspect result lists operators and tensors.
The command fails when it finds unsupported operators or limits.
Save `inspect.json` beside the exported TFLite file.
Use the SDK checkout option when its operator table is available.
Compare model identity and hash before using an older report.

Some dynamic shape operators appear in the pinned SDK table.
The kit still uses fixed shapes for its supported exports.
The source probes did not establish compilation for every listed operator.
Likewise, a graph may compile and still produce wrong simulator output.
Qualify any new graph with compile and simulator output.

## Stop conditions

Stop when the adapter rejects a graph node.
Stop when inspect reports unsupported operators.
Stop when inspect reports a tensor or shape limit violation.
Do not report kit compatibility from inspection alone.
Keep the failed output and exact model identity in the run record.

## Checks

- Read the selected adapter from `example.yaml` and `export.manifest.json`.
- Read the graph and tensor lists from `inspect.json`.
- Read empty unsupported and limit violation lists from `inspect.json`.
- Read compiler and simulator files before claiming behavior beyond inspection.
