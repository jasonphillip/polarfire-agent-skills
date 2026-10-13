# Run A report: code tasks 0 to 6 and 8, review fixes, hardware follow-ups, 2026-10-13

Branch `improve/release-readiness-2026-10-13` from `bbdb68c`. Not pushed. Each task ran as its own Codex job; the orchestrator checked that the task's new tests failed on the previous commit, ran the full gate and committed. The docs task (Run B) has its own report, `run-B-report.md`.

## 1. Changes and why

| commit | change | why |
|---|---|---|
| 0e67fa3 | baseline gate output | a reference point before any change |
| 904d402 | compare reports `status`, `complete`, `exact` per check; malformed input refused | a comparison with checks missing used to read as a pass |
| 5a4ba48 | stage records written after every command; `failure.json` on any stage error; runner hash recorded | a failed remote stage lost its commands and its error |
| dfb9863 | one int8 payload contract (`input.int8.npy`, `.bin`, `input.manifest.json` with the payload hash); simulator takes model layout only | sim, kit and compare could see different bytes; the simulator's NHWC transpose was a bug |
| 858ee66 | `attempt.json` per run; remote work in `<base>/<attempt_id>`; compare refuses stale records; worktree revision lookup | results from an older attempt or another model could be compared as current |
| 9c49196 | dry runs write nothing; remote paths quoted in `ssh` scripts; config keys validated; per-stage timeouts | a dry run changed files; a bad config failed late |
| e0d126e | `pfkit prepare-input` and `--samples K` carry one selection through sim, infer and compare | the 64-sample batch existed only as a separate procedure |
| ac3de19 | dated marketplace-install status checked; dynamic or float model IO blocks inspect; `--sdk-root` forwarded; pytest markers; host CI | maintenance checks the brief asked for |
| f06742e | CI is host-only | the fake-driver build needs the user-fetched VectorBlox SDK headers, which CI does not fetch (no licence file) |
| 84e9b7c | review fixes F1 to F7 (below) | whole-branch review |

Review fixes in `84e9b7c`: `scp` targets carry the raw remote path (OpenSSH 9 uses SFTP, where shell quotes become part of the path; confirmed on the kit); compare binds its input to the manifest and to every stage record it uses; any compare error overwrites `compare.json` with a non-pass record; infer checks `hw.bin` size against samples times the per-sample output bytes; dry runs leave the run directory untouched; a missing runner binary stops the route before any remote stage; the inference skill states the `.bin` size as K times the input bytes.

## 2. Tests and environment

Environment: Python 3.11.17, numpy 1.26.4, torch 2.11.0+cpu, tensorflow 2.15.1, PyYAML 6.0.3, pytest 9.1.1.

Gate before every commit:

```sh
.venv/bin/python tools/check_pack.py --source deps/tychon-quantum-sensing
.venv/bin/python -m pytest -q
make -C hw test
claude plugin validate .
```

Final result at `84e9b7c`: pack check PASS; 95 passed, 0 skipped; fake driver 9 scenarios with expected exits; plugin validation passed. Baseline at `bbdb68c`: 13 passed. `pytest -m host`: 67 passed; `pytest -m ml`: 10 passed. The plan's gate line `claude plugin validate` needs a path argument; `.` was used.

CI was simulated on a clean clone with a Python 3.11 venv holding only numpy, PyYAML and pytest: dependency clone, pack check and `pytest -m host` passed. GitHub Actions itself has not run, because the branch is not pushed.

## 3. Evidence

- `evidence/2026-10-13-release-readiness/baseline.txt`: gate output before the pass.
- `evidence/2026-10-13-release-readiness/payload-regeneration.md`: `prepare-input` regenerates both 2026-10-12 batch payloads byte for byte.
- `evidence/2026-10-13-hardware-cli-route/`: the 64-sample CLI route on the kit, both examples, before and after the review fixes; `hw.bin` byte-identical to the 2026-10-12 batch every time.
- `evidence/2026-10-13-assistant-run/`: Claude Code with only this plugin ran the route end to end; compare passed.
- `evidence/2026-10-13-clean-clone/`: clean-clone reproduction.

No file under a 2026-10-12 folder changed.

## 4. Remaining issues

Confirmed and open:
- The kit-built image is built but not programmed (follow-up B).
- `model.vnnx` files compiled today differ in sha256 from the 2026-10-12 builds while their outputs are byte-identical; the cause was not investigated.

Untested:
- GitHub Actions on GitHub (simulated locally only).
- A forced timeout of the real NPU (the fake driver covers the stuck-call path).
- Codex and Cursor driving the remote route; the Codex sandbox has no network.
- A clean clone from the public URL, on another machine, with a cold package cache.

Optional improvements, not done:
- `pyproject.toml` still has a `[tool.pytest.ini_options]` table that `pytest.ini` now shadows.
- The simulator no longer accepts the `(64, 1, 1, C)` arrays stored in the 2026-10-12 batch folders; replaying them needs `prepare-input` or a reshape.
- CI could fetch the SDK driver headers to run the fake-driver test, if the SDK's terms allow it.

## 5. Release announcement draft (for review, not posted)

> polarfire-agent-skills: release-readiness update. The pipeline now records what ran and refuses to call a partial or stale result a pass: every comparison reports its status, completeness and exactness per check, every run carries an attempt identity, and one int8 payload with a recorded hash travels through the simulator, the kit and the comparison. The new `--samples 64` route ran on a PolarFire SoC Icicle Kit for both examples with zero LSB difference between the VectorBlox simulator and the hardware, and its kit outputs are byte-identical to the earlier 64-sample batch. An AI coding assistant given only this plugin ran the same route end to end. Evidence for every figure is in the repository's `evidence/2026-10-13-*` folders.

## 6. Follow-up procedures

| item | state |
|---|---|
| A. 64-sample CLI route on the current image | done 2026-10-13, passed (`evidence/2026-10-13-hardware-cli-route/`) |
| B. Program the kit-built image, then rerun A | open; needs the maintainer's yes before programming |
| C. Assistant-driven full run | done 2026-10-13 for Claude Code (`evidence/2026-10-13-assistant-run/`) |
| D. Outside-developer reproduction checklist | done 2026-10-13 from a local clean clone (`evidence/2026-10-13-clean-clone/`) |
