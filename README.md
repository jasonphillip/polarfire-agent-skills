# PolarFire Agent Skills

Train a small machine-learning model, prepare it for a Microchip PolarFire
FPGA, and compare the board's answers with a simulator's answers.
An FPGA is a chip with configurable circuitry.

The `pfkit` command-line tool runs the steps. The included agent skills guide
an AI coding assistant through the same workflow and help it report what
was actually tested.

**Train → Convert → Check compatibility → Compile → Simulate → Run on the board → Compare**

Start with an example on your computer. Board deployment targets the
**PolarFire SoC Icicle Kit (MPFS250T), with the CoreVectorBlox V250 accelerator**.
Model support is limited to the [documented adapters](docs/adapters.md).

## Choose where to start

| What you want to do | Start here |
|---|---|
| Try an example without an FPGA | [First local run](#first-local-run-no-board-needed) |
| Ask an AI assistant to guide you | [Use an AI coding assistant](#use-an-ai-coding-assistant) |
| Run a model on an Icicle Kit | [Continue to the board](#continue-to-the-board) |
| Adapt your own model | [Supported model types](docs/adapters.md) and [data and result formats](docs/contracts.md) |

## First local run: no board needed

This example generates signal data, trains a small model, converts it to
8-bit integer TFLite, and checks its compatibility with the supported toolchain.
It stops before compilation, simulation, or hardware access.

You need:

- Python **3.11**, including `venv` and pip.
- Git, `make`, and internet access to download packages and source dependencies.
- A supported computer: the full local example has been tested on Linux
  aarch64 and Apple silicon macOS. See the [platform details](docs/scope.md).

You do not need an FPGA, an AI subscription, or an installed Microchip
compiler for this first run.

Choose a new folder for the checkout, then run these commands in a terminal:

```sh
KIT_ROOT="$HOME/polarfire-agent-skills"
git clone https://github.com/jasonphillip/polarfire-agent-skills.git "$KIT_ROOT"
make -C "$KIT_ROOT" env
"$KIT_ROOT/.venv/bin/python" -m pfkit example run signal-freq \
  --until inspect \
  --run-dir "$KIT_ROOT/reports/signal-inspect"
```

Already have a checkout? Set `KIT_ROOT` to its full path and skip `git clone`.
For another run, choose a new, empty `--run-dir`.

`make env` creates an isolated Python environment in `.venv`. It installs
the Python dependencies and fetches the pinned source repositories. These
include VectorBlox SDK source for the compatibility table; this does not
install the vendor compiler on your computer.

### What success looks like

The command finishes without an error and prints an inspection result with
`"blocking_flags": []`. Open `reports/signal-inspect/` inside your checkout:

| File | What it tells you |
|---|---|
| `model.tflite` | The converted model, ready for the next stage. |
| `eval.json` | How the trained model performed on the test data. |
| `inspect.json` | Compatibility checks and any blocking findings. |

A passing inspection is an early check. Compilation and board tests still
need to run before you can claim the model works on hardware.
See [the step-by-step guide](docs/getting-started.md) and
[troubleshooting](docs/faq.md) for more help.

## Examples

| Example | Task | Start with it when… |
|---|---|---|
| `signal-freq` | Estimate the frequency of a generated signal. | You want the simplest first run. |
| `odmr-mlp` | Estimate a magnetic field from simulated quantum-sensing data. | You want to follow the original sensing case study. |
| `odmr-fcnn` | Run the case study's ODMR FCNN on the `odmr-mlp` data. | Hardware parity: kit = simulator = INT8 TFLite, 0 LSB, on both images. Conversion accuracy: the largest per-sample float-to-INT8 prediction difference was 29.8 µT against 5.0 µT; one of 64 samples exceeded it, and the mean difference was 2.39 µT. This is not an error against ground truth. Overall result: failed. See `evidence/2026-10-13-kit-built-image/README.md`. |

All use generated data. The ODMR examples also need Tk when using
Homebrew Python 3.11 on macOS; see [installation requirements](docs/install.md).

## Use an AI coding assistant

The assistant follows the included instructions and runs `pfkit` commands.
You still need the environment above and, for remote stages, access to your
tools computer and board.

For Claude Code, load the checkout you prepared above:

```sh
claude --plugin-dir "$KIT_ROOT"
```

Then ask:

```text
Use the polarfire-bringup agent instructions to run signal-freq through
inspect. Use a new run directory. Explain the result and show the saved files.
```

The [installation guide](docs/install.md) covers marketplace installation,
Codex instructions, and the tested status of each client. Claude Code has a
recorded full `signal-freq` board run. Codex has a recorded local inspection
run; its plugin installation and remote workflow remain untested. Cursor
loading and execution remain untested.

## Continue to the board

The later stages use three machine roles:

| Machine | Its job |
|---|---|
| Your computer | Prepare data, train and convert models, run commands, and read reports. |
| Tools computer | Run the Microchip compiler and VectorBlox simulator. |
| Icicle Kit | Run the compiled model on its V250 accelerator. |

The tested tools computer uses Libero SoC 2025.2 and SmartHLS 2025.2 on
x86 Windows, with VectorBlox SDK 2.0.3 in WSL Ubuntu. The board runs Linux
with CoreVectorBlox IP 2.0.1 at V250. See the [supported setup](docs/scope.md)
for exact requirements.

Configure your connections using the [pipeline guide](docs/pipeline.md).
Build the `hw/vbx_run` board program and prepare the board using the
[hardware guide](docs/hardware.md). Building an FPGA image and programming
the board are separate steps.

Once that setup is ready, the documented example route can run 64 selected
test inputs through compilation, simulation, board inference, and comparison.
Use the [full-run instructions](docs/getting-started.md#later-stages) to
check the saved results. Optional PID control and watchdog integration are
separate from basic inference.

## What has been tested

These are recorded results for the supported setup, as of **2026-10-13**.

| Check | Recorded result |
|---|---|
| Local setup and inspection | Passed on Linux aarch64 and Apple silicon macOS. |
| `signal-freq` and `odmr-mlp` on the board | Each completed 64 test inputs. Integer outputs matched the simulator exactly, reported as **0 LSB difference**. |
| `odmr-fcnn` on the board | On 2026-10-13, all 64 inputs completed on both images with NPU error 0. Hardware parity: kit = simulator = INT8 TFLite, 0 LSB. Conversion accuracy: the largest per-sample float-to-INT8 prediction difference was 29.8 µT against a 5.0 µT tolerance. One of 64 samples exceeded it; the mean difference was 2.39 µT. This is not an error against ground truth. Overall result: failed. See `evidence/2026-10-13-kit-built-image/README.md`. |
| Assistant-guided board run | Claude Code completed one full `signal-freq` run. |
| Toolkit's FPGA build | Built and met timing. On 2026-10-13, the kit-built image was programmed and tested on the kit. Both 64-sample examples passed; their outputs were byte-identical to the case-study-image runs. See `evidence/2026-10-13-kit-built-image/README.md`. |

Board results now cover the case-study and kit-built images. Model support is
bounded: the `mlp` adapter has the passing board examples. The `conv2d_1k`
model had exact hardware parity on both images. Its float-to-INT8 conversion
missed tolerance, so it failed (`evidence/2026-10-13-kit-built-image/README.md`). Other
boards, accelerator sizes, and SDK 3.x are outside the validated path.

See the [validation record](docs/validation.md),
[64-input board results](evidence/2026-10-13-hardware-cli-route/README.md),
and [release notes](docs/release-notes.md) for evidence and remaining limits.

## Reference and related work

- [Model adapters](docs/adapters.md): supported layers and how to add an adapter.
- [Data and result formats](docs/contracts.md): input bytes, run identity, and comparison status.
- [Compatibility findings](docs/claims.md): measured compiler and simulator limitations.
- [Agent instructions](agents/polarfire-bringup.md): workflow guidance for coding assistants.

This toolkit integrates the VectorBlox workflow for PolarFire and records
evidence at each stage. It builds on the
[Tychon quantum-sensing case study](https://github.com/jasonphillip/tychon-quantum-sensing).
Related work includes [FINN's end-to-end flow](https://finn-dev.readthedocs.io/en/latest/end_to_end_flow.html),
[FINN's verification methods](https://finn.readthedocs.io/en/latest/verification.html),
and the [hls4ml Libero contribution](https://github.com/fastmachinelearning/hls4ml/pull/1578).

## License

Copyright 2026 Jason Phillip, Tychon AI. Licensed under [Apache-2.0](LICENSE).
Microchip tools, Linux images, and precompiled VNNX models are not bundled.
See [dependency licenses](docs/scope.md#7-external-dependencies-pinned-by-the-kit)
for the source dependencies and their terms.
