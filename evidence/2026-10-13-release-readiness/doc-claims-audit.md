# Documentation claim audit, Run B

This audit records changed claims against the old checkout lines. It is a
documentation review, not a new hardware run. The requested novelty grep
(`only (kit|toolkit|pack)|no other|first (public|open)|unique|novel|sensor-to-actuator|latency|guarantee|worst`)
found only `worst slack` in the build records; that is a timing-report metric,
not a claim of worst-case inference latency. No firstness claim was present.

| Old location and claim | New location and claim | Supporting file |
|---|---|---|
| `README.md:25-26`: Libero build in progress | `README.md`: build completed; job exported; new image unprogrammed | `evidence/2026-10-12-libero-build/README.md` |
| `README.md:23-24`: broad kit validation | `README.md`: old batch results separate from unrun new CLI route | `evidence/2026-10-12-hardware/batch64/README.md`; `evidence/2026-10-13-release-readiness/payload-regeneration.md` |
| `README.md`: no prior-art boundary | `README.md`: PolarFire-specific integration with FINN and hls4ml prior art | FINN end-to-end and verification URLs in `README.md`; `skills/hls4ml-libero-route/SKILL.md` |
| `docs/scope.md:5`: all claims dated 2026-10-12 | `docs/scope.md`: claims cite recorded runs; newer host result can be described | `evidence/2026-10-13-release-readiness/payload-regeneration.md` |
| `docs/scope.md:19`: model path unbounded | `docs/scope.md`: `mlp` and `conv2d_1k`; convolution route simulator only | `docs/adapters.md`; `docs/claims.md` |
| `docs/install.md:30,32,46`: duplicate marketplace install status | `docs/install.md`: four distinct checks: installation, skill loading, inspect, remote execution | Run B plan Task 7 records user-scope install and uninstall; `evidence/2026-10-12-agent-clients/claude-code.md` records local loading and inspect. Raw marketplace install log is not in this checkout. |
| `docs/install.md:49-52`: client workflow through inspect | `docs/install.md`: no assistant-driven compile, sim or kit run recorded | `evidence/2026-10-12-agent-clients/claude-code.md`; `evidence/2026-10-12-agent-clients/codex.md` |
| `docs/install.md:77-98`: setup details spread across sections | `docs/install.md`: explicit Python, SSH, Tk, SDK, vendor, image and licence prerequisites | `docs/scope.md`; `docs/hardware.md`; `docs/pipeline.md`; `deps.lock` |
| `docs/validation.md:9,36`: build still running or pending | `docs/validation.md`: completed build row retained, stale status removed | `evidence/2026-10-12-libero-build/README.md` |
| `docs/validation.md:38`: fake-driver-only timeout | `docs/validation.md`: names `hw/tests/fake_vbx_cnn_api.c`; NPU timeout unrun | `hw/tests/test_fake_driver.py`; `hw/tests/fake_vbx_cnn_api.c` |
| `docs/hardware.md:116-118`: case-study timing and build only | `docs/hardware.md`: separate 0.032/0.032, 0.034/0.072 and 0.034/0.060001 ms ODMR records with runner revisions | `evidence/2026-10-12-hardware/odmr-mlp/hw.json`; `evidence/2026-10-12-hardware/batch64/odmr-mlp/hw.json`; `evidence/2026-10-12-hardware/batch64/odmr-mlp/timing-200.json`; batch README |
| `docs/hardware.md:116-118`: no kit timing boundary | `docs/hardware.md`: ready/start/poll window excludes input copy, output write, process and control path | `hw/vbx_run.c` around the sample loop and poll |
| `docs/release-notes.md:22-32`: client and hardware results without new route boundary | `docs/release-notes.md`: inspect-only client workflows and new route unrun on kit | 2026-10-12 client evidence; `evidence/2026-10-13-release-readiness/payload-regeneration.md` |
| `docs/contracts.md:25-29`: tolerance rules without aggregate status meaning | `docs/contracts.md`: row `exact`, top-level `status`, `complete`, attempt identity | `pfkit/pipeline.py` `compare_arrays` and `compare`; `pfkit/attempt.py` |
| `docs/pipeline.md:40-46`: inspect gate without result boundary | `docs/pipeline.md`: inspect finds known incompatibilities only | `pfkit/inspect.py`; `docs/claims.md` |
| `docs/pipeline.md:20,31-35`: no batch selection in sequence | `docs/pipeline.md`: `--samples`, `prepare-input`, payload and attempt status | `pfkit/cli.py`; `pfkit/pipeline.py`; `pfkit/payload.py`; 2026-10-13 payload record |
| `docs/claims.md:1-5`: probes without adapter and inspect boundary | `docs/claims.md`: adapter scope and simulator-only convolution evidence | `docs/adapters.md`; probe sections in `docs/claims.md` |
| `agents/polarfire-bringup.md:52-76`: stage sequence without sample selection | `agents/polarfire-bringup.md`: sample selection, manifest and attempt identity | `pfkit/cli.py`; `pfkit/pipeline.py`; `pfkit/attempt.py` |
| `skills/vbx-ops-guard/SKILL.md:28-48`: inspect gate | Skill now states compiler and kit limits of inspect | `pfkit/inspect.py`; `docs/claims.md` |
| `skills/kit-run-inference/SKILL.md:47-70`: comparison without complete/attempt language | Skill now distinguishes row exactness, complete status and unrun new route | `pfkit/pipeline.py`; 2026-10-13 payload record |
| `skills/kit-program/SKILL.md:10-15`, `skills/libero-build/SKILL.md:10-20`: build and programming instructions | Both skills identify completed build and unprogrammed image | `evidence/2026-10-12-libero-build/README.md` |
| `skills/claim-log/SKILL.md:44-54`: result-file citation without attempt boundary | Skill requires numbers from the current attempt's run directory | `pfkit/attempt.py`; `pfkit/reporting.py` |

The FINN URLs and the hls4ml PR date are prior-art context from the approved
Run B plan. This offline run did not verify their current web state.
