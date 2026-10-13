# Run B: Task 7 documentation reconciliation

## 1. Changes and why

- `README.md`: replace the stale build status; separate earlier kit results from the unrun 64-sample CLI route; name prior art.
- `docs/install.md`: separate marketplace installation, local skill loading, inspect execution and unrun remote client execution; list prerequisites.
- `docs/validation.md`: remove the pending-build claim; name the fake driver; record host-only payload regeneration and the unrun kit route.
- `docs/hardware.md`: cite three exact ODMR timing records, their runner revisions and the measured code boundary.
- `docs/release-notes.md`: distinguish recorded inspect workflows from a full assistant deployment and from host-only payload regeneration.
- `docs/scope.md`: bound model support to the two adapters and add prior art.
- `docs/claims.md`: bound probe and inspect claims to their evidence class.
- `docs/contracts.md`: explain comparison status, completeness, exactness and attempt identity.
- `docs/pipeline.md`: document the staged payload selection, inspect limit and comparison status.
- `agents/polarfire-bringup.md`: add `--samples`, the payload manifest and attempt checks.
- `skills/vbx-ops-guard/SKILL.md`: state what passing inspect establishes.
- `skills/kit-run-inference/SKILL.md`: require complete and exact comparison reading.
- `skills/kit-program/SKILL.md`: identify the unprogrammed image.
- `skills/libero-build/SKILL.md`: identify the completed build and separate image.
- `skills/claim-log/SKILL.md`: bind every number to the current attempt.
- `evidence/2026-10-13-release-readiness/doc-claims-audit.md`: map old claims to replacements and supporting files.
- This report: record the Run B gate and remaining hardware checks.

## 2. Commands, outcomes and environment

Run B made prose-only changes, so the plan has no failing-test step. The
pre-edit review did find `docs/validation.md` saying the build was still
running and pending; those claims conflicted with the completed build record.

| Command | Outcome |
|---|---|
| `.venv/bin/python --version` | Python 3.11.17 |
| `.venv/bin/python -m pip freeze \| rg '^(numpy\|torch\|tensorflow)'` | `numpy==1.26.4`, `torch==2.11.0+cpu`, `tensorflow==2.15.1`, `tensorflow-cpu-aws==2.15.1`, `tensorflow-estimator==2.15.0`, `tensorflow-io-gcs-filesystem==0.37.1` |
| `.venv/bin/python tools/check_pack.py --source deps/tychon-quantum-sensing` | PASS: 12 skills, 6 JSON files, source paths and public text |
| `.venv/bin/python -m pytest -q` | 77 passed, 5 warnings |
| `make -C hw test` | All nine printed fake-driver scenarios completed with expected results |
| `if rg -n -i 'Libero build (is\|result is) (in progress\|still running\|pending)\|marketplace install: not yet tested\|29 ?(µs\|microseconds)\|68 ?(µs\|microseconds)\|assistant-driven (compile\|simulation\|kit run) (was\|is) recorded' README.md docs agents skills; then exit 1; else printf 'PASS: no superseded claim found\n'; fi` | PASS: no superseded claim found |
| `git diff --check` | PASS |

The pytest warnings were four TensorFlow quantization-statistics warnings and
one optional matplotlib warning from qutip. There were no pytest skips.
Vendor compilation, simulation, kit inference, image programming, and a live
client deployment were skipped because Run B is an offline documentation task.
`claude plugin validate` was not run; the orchestrator runs it separately.

## 3. New evidence paths

- `evidence/2026-10-13-release-readiness/doc-claims-audit.md`: claim mapping.
- `evidence/2026-10-13-release-readiness/run-B-report.md`: this handoff.
- `evidence/2026-10-13-release-readiness/payload-regeneration.md`: existing host-only byte-identity result used by these docs.

No file in a 2026-10-12 evidence folder changed.

## 4. Remaining issues

- Confirmed documentation defect addressed: the build-pending statements contradicted the completed Libero build record.
- Untested: the new 64-sample CLI route on the kit, the kit-built image on hardware, forced real-NPU timeout, and a full assistant-driven remote workflow.
- Untested: current web state of hls4ml PR 1578 and the FINN pages in this offline run.
- Optional improvement: commit the raw marketplace install and uninstall transcript. The approved plan records the result, but that raw log is not in this checkout.

## 5. Release announcement draft for Jason's review — not posted

The PolarFire Agent Skills kit now documents its staged input, comparison and
attempt records. Earlier 64-sample signal and ODMR kit batches matched their
simulator outputs at 0 LSB on the case-study V250 image. The kit's separate
Libero build met timing and exported a job, but that image has not been
programmed. The new `--samples 64` CLI route regenerated both historical
input payloads byte for byte on the host; it has not run on the kit. Recorded
Claude Code and Codex workflows reached inspect, not remote deployment.

## 6. Follow-up procedures

1. On the current image, run each example through `example run --until compare --samples 64` with private tools host and kit configs. Use fresh run directories. Confirm `compare.json` has `status: passed`, `complete: true`, `samples: 64`, and `sim_vs_hw` maximum 0 LSB. Confirm `attempt.json` matches each stage. Compare `hw.bin` hashes with the 2026-10-12 batch only when using the same first 64 test samples. Save the new files under a new dated hardware evidence folder, then update `docs/validation.md`.
2. Before programming the kit-built image, obtain Jason's approval for the exact job and target. Record the existing rollback job hash, new job hash, device IDCODE and FlashPro log. After programming, reboot, check the V250 UIO and DMA nodes, and rerun step 1. Keep those results separate from the earlier image's measurements.
3. For an assistant-driven full run, save the actual Claude Code or Codex transcript and run directory. Require the assistant to execute compile, sim, infer and compare, then inspect `attempt.json` and all stage records. Do not infer this from an inspect-only transcript.
4. For outside-developer or third-model reproduction, use a clean clone and pinned Python 3.11 environment. Run `pfkit deps fetch`, `pytest -m host`, `pytest -m ml`, `make -C hw test`, and `pfkit example run signal-freq --until inspect`. With the developer's own remote configs and kit, run `--until compare --samples 64`. Return `compare.json`, `attempt.json`, stage records, model and payload hashes, board-image identity and any skipped checks.
