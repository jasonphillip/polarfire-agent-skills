# Validation record, 2026-10-12

This record separates orchestration, tools-host, and hardware results.
The clean-checkout logs are to be added under `evidence/2026-10-12-clean-checkout/` by the main session.
That evidence path is reserved here; this document does not claim the logs are already present.

| Stage | Host | Result | Evidence path |
|---|---|---|---|
| Environment and inspect | Clean Linux aarch64, Python 3.11.17 | `make env` completed in 33 seconds with a warm pip cache. `pfkit example run signal-freq --until inspect` exited 0. Inspect showed three `CONV_2D` operators and `RESHAPE`; flags were informational per-channel notes only. | `evidence/2026-10-12-clean-checkout/` (logs forthcoming) |
| Guard negatives and tests | Clean Linux aarch64 | `pfkit inspect` exited 1 for a SHAPE model with unsupported `SHAPE`. It exited 1 for a PACK model with a blocking flag. `PFKIT_SDK_ROOT=/nonexistent` reported `VectorBlox operator table missing` and suggested `pfkit deps fetch`. `pytest -q` passed 10 tests. | `evidence/2026-10-12-clean-checkout/` (logs forthcoming) |
| Environment and inspect | Clean macOS 27.0.1 arm64, Homebrew Python 3.11.14 | The first `make env` failed on `torch==2.11.0+cpu`, a Linux-only local tag. After the pin changed to `torch==2.11.0` in commit `c28adbe`, `make env` succeeded and fetched three pinned dependencies. `pfkit example run signal-freq --until inspect` exited 0 with the same operators and flags. | `evidence/2026-10-12-clean-checkout/` (logs forthcoming) |
| Tests | Clean macOS arm64 | `pytest -q` passed 9 tests and failed `test_examples_through_inspect[odmr-mlp]`. Importing the case-study simulator reached `simos`, whose `utils/exporter.py` imported `tkinter`. Homebrew Python lacked `_tkinter`. `brew install python-tk@3.11` is the proposed fix; it was not verified in that run. | `evidence/2026-10-12-clean-checkout/` (logs forthcoming) |
| Compile, simulate, compare | x86 Windows tools host with WSL Ubuntu, VectorBlox SDK 2.0.3 | Both examples compiled and simulated. Each simulator output differed from TFLite by 0 LSB. | `evidence/2026-10-12-sim-runs/signal-freq/compare.json`; `evidence/2026-10-12-sim-runs/odmr-mlp/compare.json` |
| Runner cross-build | x86 Windows tools host | `hw/vbx_run` cross-compiled with SmartHLS RISC-V GCC 10.2.0. The MSYS shell lacked `make`; the direct GCC line from `hw/Makefile` succeeded. SmartHLS supplies `mingw32-make` as an alternative. | `evidence/2026-10-12-toolshost/runner-build.txt` |
| Hardware inference and `sim_vs_hw` | Icicle Kit | Not run. The kit was powered off. | No hardware run; both `evidence/2026-10-12-sim-runs/*/compare.json` files report `sim_vs_hw: "not run"` |

For the clean orchestration path, the measured commands were `make env`,
`pfkit example run signal-freq --until inspect`, and `pytest -q`.
The guard checks used `pfkit inspect` on separate SHAPE and PACK models.
The missing-SDK check set `PFKIT_SDK_ROOT=/nonexistent` for `pfkit inspect`.
See `docs/hardware.md` for the direct runner GCC command.

Hardware inference and the simulator-to-hardware comparison still need a kit window.
Plan about one hour with the kit powered, on the LAN, and a working login.
