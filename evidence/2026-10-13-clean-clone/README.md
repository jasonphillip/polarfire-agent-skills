# Outside-developer reproduction from a clean clone, 2026-10-13

Follow-up D of the release-readiness pass. A fresh clone of branch `improve/release-readiness-2026-10-13` at `fdbd981` (cloned from the maintainer checkout, because the branch was not yet pushed), in a new directory, with a new environment. Each step ran in order; times are wall clock.

| step | command | result | time |
|---|---|---|---|
| environment | `make env` (Python 3.11 venv, pinned packages, `pfkit deps fetch`) | exit 0 | 45 s (warm pip cache) |
| host tests | `.venv/bin/python -m pytest -m host -q -rs` | 67 passed, 10 deselected | 1 s |
| ML smoke tests | `.venv/bin/python -m pytest -m ml -q -rs` | 10 passed, 67 deselected | 17 s |
| fake driver | `make -C hw test` | 9 scenarios, expected exits | 1 s |
| inspect | `pfkit example run signal-freq --until inspect` | exit 0, `blocking_flags` empty | 6 s |
| full route, no runner binary | `pfkit example run signal-freq --until compare --samples 64 ...` | exit 1 at infer: `scp` of `hw/vbx_run` failed (exit 255) after compile and sim | 23 s |
| full route, runner built | same command, `hw/vbx_run` from runner commit `5fe1239` | exit 0; compare passed, complete, 64 samples, sim_vs_hw 0 LSB exact; hw.bin sha256 f3e1261b… equal to 2026-10-12 | 24 s |

Finding: without the separately built runner (`hw/vbx_run`, see `docs/hardware.md`, Runner), the route failed late with a bare `scp` error. The review fix commit `84e9b7c` adds a preflight that stops before any remote stage with `runner not found: hw/vbx_run; build it on the tools host (docs/hardware.md, Runner)`.

Not covered: a clone from the public GitHub URL (the branch was unpushed), a cold pip cache, and a machine other than the maintainer's. The tools host and kit configs were the maintainer's.
