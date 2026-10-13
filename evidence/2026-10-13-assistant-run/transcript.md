# Assistant-driven run transcript (scrubbed)

Model: `claude-sonnet-5-5`. Client: Claude Code, headless (`claude -p`). Plugin loaded from the clean clone with `--plugin-dir`.

**Tool call `Skill`:**

```json
{
 "skill": "polarfire-agent-skills:kit-run-inference"
}
```

**Tool result:**

```
Launching skill: polarfire-agent-skills:kit-run-inference
```

**Tool call `Skill`:**

```json
{
 "skill": "polarfire-agent-skills:claim-log"
}
```

**Tool result:**

```
Launching skill: polarfire-agent-skills:claim-log
```

**Tool call `Bash`:**

```json
{
 "command": "pwd && git rev-parse --show-toplevel && ls && cat skills/adapt-your-model/SKILL.md && ls reports | tail -5 && .venv/bin/python -m pfkit example run --help"
}
```

**Tool result:**

```
<kit-root>
<kit-root>
agents
deps
deps.lock
docs
evidence
examples
hw
kit.yaml
LICENSE
Makefile
NOTICE
pfkit
pfkit.egg-info
plugin.json
probes
pyproject.toml
pytest.ini
README.md
reports
skills
SOURCES.md
tests
tools
toolshost.yaml
---
name: adapt-your-model
description: Adapt a user model to the pfkit INT8 export and inspection gates.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Adapt your model

Read `docs/contracts.md`, `docs/adapters.md`, and `docs/claims.md`.
Use `dataset-and-training` to create a valid example and checkpoint.
Keep a single graph input and a fixed batch of one for export.
Check that the model input layout and preprocessing match its dataset.

## Adaptation checklist

1. Add `examples/<name>/example.yaml` and its named Python module.
2. Choose `mlp` or `conv2d_1k` from the actual Torch graph.
3. Set shape, layout, dtype, units, normalization, and target scale.
4. Provide train, validation, and test arrays with the contract keys.
5. Choose a calibration split, count, and seed that cover normal inputs.
6. Set float output and raw INT8 simulator tolerances in YAML.
7. Run the small data and training mode before spending the ful
[... truncated ...]
status and any `not run` stages from `compare.json`.
- Read file hashes and command records from `artifacts.json` and `commands.jsonl`.
repro-cli64
repro-cli64-norunner
repro-inspect
usage: pfkit example run [-h]
                         [--until {data,train,eval,export,inspect,compile,sim,infer,compare}]
                         [--run-dir RUN_DIR] [--toolshost TOOLSHOST]
                         [--kit KIT] [--full] [--samples SAMPLES]
                         [--selection {first,random}] [--seed SEED]
                         [--sdk-root SDK_ROOT] [--form {conv1x1,fc}]
                         [--allow-fc-chain]
                         name

positional arguments:
  name

options:
  -h, --help            show this help message and exit
  --until {data,train,eval,export,inspect,compile,sim,infer,compare}
  --run-dir RUN_DIR
  --toolshost TOOLSHOST
                        tools host config for compile and sim
  --kit KIT             kit config for infer
  --full
  --samples SAMPLES
  --selection {first,random}
  --seed SEED
  --sdk-root SDK_ROOT   VectorBlox SDK checkout containing docs/OPS.md
  --form {conv1x1,fc}
  --allow-fc-chain      allow measured SDK 2.0.3 simulator failure
```

**Tool call `Bash`:**

```json
{
 "command": ".venv/bin/python -m pfkit example run signal-freq --until compare --samples 64 --run-dir reports/20261013-104359-signal-freq-assistant --toolshost <config>/toolshost.yaml --kit <config>/kit.yaml > /tmp/pfkit-run-104359.log 2>&1; echo exit=$?; tail -30 /tmp/pfkit-run-104359.log",
 "timeout": 600000
}
```

**Tool result:**

```
exit=0
{"adapter": "mlp", "calibration": {"indices": [336, 226, 469, 271, 81, 444, 75, 135, 27, 402, 28, 475, 434, 137, 1, 254, 397, 433, 317, 248, 98, 478, 179, 180, 5, 435, 49, 438, 308, 164, 201, 169, 229, 407, 126, 13, 113, 239, 379, 428, 218, 337, 51, 287, 97, 365, 33, 480, 158, 324, 234, 338, 325, 86, 212, 414, 350, 19, 31, 330, 107, 477, 398, 376], "samples": 64, "seed": 451, "split": "train"}, "converter_quantization": {"StatefulPartitionedCall:0": {"quantized_dimension": 0, "scales": [0.004028
inspect: signal-freq
{"blocking_flags": [], "flags": ["per-channel quantization tensor 4", "per-channel quantization tensor 5", "per-channel quantization tensor 6", "per-channel quantization tensor 7"], "limit_violations": [], "operators": [{"index": 0, "inputs": [0, 7, 6], "operator": "CONV_2D", "options": {"DilationHFactor": 1, "DilationWFactor": 1, "FusedActivationFunction": 1, "Padding": 1, "QuantizedBiasType": 0, "StrideH": 1, "StrideW": 1}, "options_type": "Conv2DOptions", "outputs": [8], "sdk_limits": {"Fused
compile: signal-freq
2026-10-13 10:44:19.561652: I tensorflow/core/util/port.cc:113] oneDNN custom operations are on. You may see slightly different numerical results due
[... truncated ...]
it/20261013-144412-46d5d372/hw.bin reports/20261013-104359-signal-freq-assistant/hw.bin
scp root@<kit>:/tmp/pfkit/20261013-144412-46d5d372/hw.json reports/20261013-104359-signal-freq-assistant/hw.json
{"attempt_id": "20261013-144412-46d5d372", "commands": [{"argv": ["ssh", "root@<kit>", "mkdir -p /tmp/pfkit/20261013-144412-46d5d372"], "command": "ssh root@<kit> 'mkdir -p /tmp/pfkit/20261013-144412-46d5d372'", "error": null, "executed": true, "exit_code": 0, "finished_utc": "2026-10-13T14:44:31.579699+00:00", "started_utc": "2026-10-13T14:44:30.785729+00:00", "stderr": "", "stdout": ""}, {"argv": ["scp", "<scratch>
compare: signal-freq
{"attempt_id": "20261013-144412-46d5d372", "checks_failed": [], "checks_not_run": [], "checks_passed": ["float_vs_tflite", "tflite_vs_sim", "sim_vs_hw"], "checks_run": ["float_vs_tflite", "tflite_vs_sim", "sim_vs_hw"], "complete": true, "float_vs_tflite": {"exact": false, "max_abs": 0.041380882263183594, "pass": true, "status": "passed", "tolerance": 2.0}, "inputs": {"model_sha256": "975fba72e20e275c41fefa5d8656093ee4bd3902afcbc60f7718fe3ab869f755", "payload_sha256": "56b5c46c63d03e2cb4f69c19c4c
reports/20261013-104359-signal-freq-assistant/summary.md
```

**Tool call `Bash`:**

```json
{
 "command": "cd <kit-root>/reports/20261013-104359-signal-freq-assistant && cat compare.json; echo; cat attempt.json; echo; git -C ../.. status --short | head"
}
```

**Tool result:**

```
{
  "attempt_id": "20261013-144412-46d5d372",
  "checks_failed": [],
  "checks_not_run": [],
  "checks_passed": [
    "float_vs_tflite",
    "tflite_vs_sim",
    "sim_vs_hw"
  ],
  "checks_run": [
    "float_vs_tflite",
    "tflite_vs_sim",
    "sim_vs_hw"
  ],
  "complete": true,
  "float_vs_tflite": {
    "exact": false,
    "max_abs": 0.041380882263183594,
    "pass": true,
    "status": "passed",
    "tolerance": 2.0
  },
  "inputs": {
    "model_sha256": "975fba72e20e275c41fefa5d8656093ee4bd3902afcbc60f7718fe3ab869f755",
    "payload_sha256": "56b5c46c63d03e2cb4f69c19c4c5c4a786a662a3f006796de0b56ec83e3a549a"
  },
  "pass": true,
  "payload_sha256": "56b5c46c63d03e2cb4f69c19c4c5c4a786a662a3f006796de0b56ec83e3a549a",
  "required": [
    "float_vs_tflite",
    "tflite_vs_sim",
    "sim_vs_hw"
  ],
  "samples": 64,
  "selection": {
    "indices": [
      0,
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      19,
      20,
      21,
      22,
      23,
      24,
      25,
      26,
      27,
      28,
      29,
      30,
      31,
      32,
      33,
      34,
      35,
      36,
      37,
      38,
      39,
      40,
      41,
      42,
      43,
      44,
      45,
      46,
      47,
      48,
      49,
      50,
      51,
      52,
      53,
      54,
      55,
      56,
      57,
      58,
      59,
      60,
      61,
      62,
      63
    ],
    "method": "first",
    "seed": null,
    "split": "test"
  },
  "sim_vs_hw": {
    "exact": true,
    "max_abs_lsb": 0,
    "pass": true,
    "status": "passed",
    "tolerance_lsb": 0
  },
  "split": "test",
  "status": "passed",
  "tflite_vs_sim": {
    "exact": true,
    "max_abs_lsb": 0,
    "pass": true,
    "status": "passed",
    "tolerance_lsb": 1
  },
  "tolerances": {
    "float_tflite_abs": 2.0,
    "sim_hw_lsb": 0,
    "tflite_sim_lsb": 1
  },
  "units": "hertz"
}

{
  "argv": [
    "example",
    "run",
    "signal-freq",
    "--until",
    "compare",
    "--samples",
    "64",
    "--run-dir",
    "reports/20261013-104359-signal-freq-assistant",
    "--toolshost",
    "<config>/toolshost.yaml",
    "--kit",
    "<config>/kit.yaml"
  ],
  "attempt_id": "20261013-144412-46d5d372",
  "dirty": false,
  "kit_revision": "fdbd98133c215067c1530a23c57ae1025d01d89c",
  "started_utc": "2026-10-13T14:44:12.864717+00:00",
  "worktree": false
}
```

**Assistant:**

The signal-freq example ran end to end on the 64-sample held-out batch, and the comparison passed.

The single command `example run signal-freq --until compare --samples 64` ran the train, export, inspect, compile, sim, infer and compare stages and exited 0. The simulator run and the kit run both happened. I did not program, reboot or power-cycle the kit, and I did not push. I did not run `git status` on the repository after the run, so I haven't checked whether anything outside the run directory changed.

**`reports/20261013-104359-signal-freq-assistant/compare.json`**
- `status`: `"passed"`
- `complete`: `true`
- `samples`: `64`
- `sim_vs_hw`: `{"exact": true, "max_abs_lsb": 0, "pass": true, "status": "passed", "tolerance_lsb": 0}`

**`reports/20261013-104359-signal-freq-assistant/attempt.json`**
- `attempt_id`: `"20261013-144412-46d5d372"`

Other fields in `compare.json`:
- **`float_vs_tflite`:** passed, `max_abs` 0.0414 hertz against a tolerance of 2.0, `exact: false`.
- **`tflite_vs_sim`:** passed, `exact: true`, 0 LSB against a tolerance of 1 LSB.
- **Checks:** `checks_failed` and `checks_not_run` are both empty.
- **Selection:** the test split, method `first`, indices 0 to 63.
- **Payload hash:** `payload_sha256` is `56b5c46c63d03e2cb4f69c19c4c5c4a786a662a3f006796de0b56ec83e3a549a`.

`attempt.json` records `dirty: false` and `kit_revision` `fdbd98133c215067c1530a23c57ae1025d01d89c`. I did not open `hw.json`, `inspect.json` or `infer.json`, so I'm not reporting timing or runner metadata. The inspect and infer results above come only from the run's console output and the passing compare. The full console log is at `/tmp/pfkit-run-104359.log`.

Result: `success`, 8 turns, 43 s.
