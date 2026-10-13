# Validation record, 2026-10-12

## Test routes

Run host checks with `.venv/bin/python -m pytest -m host -q -rs`.
Run the Python 3.11 ML smoke tests with `.venv/bin/python -m pytest -m ml -q -rs`.
Build and check the fake driver with `make -C hw test`.
Vendor-tool and hardware checks require manual runs on the tools host and kit; CI does not run them.
Pytest reports skipped ML tests with their reason when torch or TensorFlow is unavailable.

Each result names the machine role and the evidence available in this checkout. The Libero build is still running.

| Stage | Host | Result | Evidence path |
|---|---|---|---|
| Clean environment and inspect | Linux aarch64, Python 3.11.17 | `make env` and `signal-freq` through inspect exited 0. Inspect found three `CONV_2D` operators and `RESHAPE`, with no blocking flags. | `evidence/2026-10-12-clean-checkout/linux-aarch64.txt` |
| Guard checks and tests | Linux aarch64 | SHAPE and PACK negative models exited 1. A missing SDK operator table produced a specific error. Ten tests passed. | `evidence/2026-10-12-clean-checkout/linux-aarch64.txt` |
| Clean environment and inspect | macOS arm64, Homebrew Python 3.11.14 | The first environment attempt failed on the Linux-only `torch==2.11.0+cpu` pin. With `torch==2.11.0`, environment setup and `signal-freq` inspect passed. | `evidence/2026-10-12-clean-checkout/macos-arm64-run1.txt`; `evidence/2026-10-12-clean-checkout/macos-arm64-run2.txt` |
| Tk and tests | macOS arm64, Homebrew Python 3.11.14 | After `python-tk@3.11` was installed, 11 tests passed and `odmr-mlp` ran through inspect. | `evidence/2026-10-12-clean-checkout/macos-arm64-run3-tk.txt` |
| Claude Code client workflow | Clean clone, Claude Code 2.1.296 | The plugin loaded the `dataset-and-training` skill and `polarfire-bringup` agent instructions. The `signal-freq` workflow reached inspect with exit 0 and reported the correct operators, flags, and eval MAE. | `evidence/2026-10-12-agent-clients/claude-code.md` |
| Codex CLI client workflow | Checkout, Codex CLI 0.157.1 | Codex read the skill and agent files directly. The same workflow reached inspect with exit 0. A plugin install was not exercised. | `evidence/2026-10-12-agent-clients/codex.md` |
| Train, export, compile, simulate, compare | Orchestration host and x86 Windows tools host with WSL Ubuntu, SDK 2.0.3 | Both examples compiled and simulated for V250. TFLite versus simulator differed by 0 LSB. | `evidence/2026-10-12-sim-runs/signal-freq/`; `evidence/2026-10-12-sim-runs/odmr-mlp/` |
| Runner cross-build | x86 Windows tools host | SmartHLS RISC-V GCC 10.2.0 built the earlier runner with exit 0. The hardened runner was also cross-built for the kit run below. | `evidence/2026-10-12-toolshost/runner-build.txt`; `evidence/2026-10-12-hardware/batch64/README.md` |
| First kit inference and negative paths | Icicle Kit, MPFS250T, case-study V250 image | Both examples completed with 0 LSB simulator versus hardware difference. The earlier runner refused V500 with exit 2 after SDK init. Wrong input size exited 2; missing model exited 3. | `evidence/2026-10-12-hardware/README.md`; `evidence/2026-10-12-hardware/negatives/` |
| Hardened runner failure paths | Linux host, fake driver | `make -C hw test` passed nine scenarios. The whole-operation watchdog returned exit 4 for `never_completes` and `start_blocks`; the error register returned 5; init failure returned 3; V500 preflight and bad input size returned 2. Model and input validation ran before SDK init. | `hw/tests/test_fake_driver.py`; `hw/tests/fake_vbx_cnn_api.c` |
| Hardened runner preflight and inference | Icicle Kit, same V250 image | The cross-built hardened runner refused V500 with exit 2 before SDK init, then completed a V250 run. | `evidence/2026-10-12-hardware/batch64/README.md` |
| Held-out batch and timing | Tools-host simulator and Icicle Kit | For each example, 64 held-out samples gave 0 LSB for simulator versus hardware and TFLite versus simulator. Float versus TFLite max error was 0.0414 Hz for `signal-freq` and 1.6713 microtesla for `odmr-mlp`, within tolerance. One-sample medians over 200 repeats were 0.024 ms and 0.034 ms, respectively. | `evidence/2026-10-12-hardware/batch64/README.md`; `evidence/2026-10-12-hardware/batch64/signal-freq/`; `evidence/2026-10-12-hardware/batch64/odmr-mlp/` |
| 64-sample route through `example run --samples 64` | tools host and kit | Not run on hardware as of this commit; the 2026-10-12 batch used a separate procedure. | `evidence/2026-10-12-hardware/batch64/README.md` |
| Kit reference-design build | x86 Windows tools host, Libero SoC 2025.2 | Done 2026-10-12: `hw/build_reference_design.sh` (PIN_VLNV COREAXI4INTERCONNECT=2.9.100) exit 0 in 40 min 25 s; timing met (0 violations, worst slack 1.049 ns); job exported, sha256 6d5cae6c...; core 2.0.1 PRESET 0 confirmed in the generated component. First attempt without the pin failed on COREAXI4INTERCONNECT 3.0.130. Not programmed. | `evidence/2026-10-12-libero-build/` |
| Secret scan | Release checkout | Scan reported hash false positives only, with no key, token, or password finding. | `evidence/2026-10-12-secret-scan.md` |

Libero build result (2026-10-12): the second attempt, with the COREAXI4INTERCONNECT 2.9.100 pin, completed in 40 min 25 s with script exit 0: timing met on seed 1 (0 violations, worst slack 1.049 ns), bitstream exported (job sha256 6d5cae6c...), generated core 2.0.1 PRESET 0. Evidence: `evidence/2026-10-12-libero-build/`. The kit was not programmed with it.

## Limits

- No co-simulation was run.
- The Libero build result is pending.
- A kit-built image has not been programmed. Programming needs separate approval.
- A forced NPU timeout was tested with the fake driver only, not on hardware.
- A Codex plugin install and Cursor loading were not tested.
- The `odmr-mlp` example needs Tk with Homebrew Python 3.11 on macOS. Installing `python-tk@3.11` resolved this in the clean-checkout run.
