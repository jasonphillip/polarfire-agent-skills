# Assistant-driven 64-sample run, 2026-10-13

Follow-up C of the release-readiness pass: an AI coding assistant, given only this plugin, runs the signal-freq example end to end on the tools host and the kit.

Setup: a clean clone of branch `improve/release-readiness-2026-10-13` at `fdbd981`, its environment built with `make env`, the runner `hw/vbx_run` built from commit `5fe1239`. Claude Code ran headless (`claude -p`, model `claude-sonnet-5-5`) with the plugin loaded from the clone (`--plugin-dir`). Its Bash tool was limited to `.venv/bin/python -m pfkit ...` and read-only listing commands. Prompt, in short: use the `polarfire-bringup` agent instructions and the plugin's skills to run signal-freq end to end with the 64-sample held-out batch, with the given tools host and kit configs and a new run directory; do not program, reboot or power-cycle the kit; report `compare.json` and `attempt.json` fields, quoting the files.

What the assistant did (`transcript.md`): loaded the `kit-run-inference` and `claim-log` skills, read `adapt-your-model`, ran one command, `pfkit example run signal-freq --until compare --samples 64 ...`, and read back `compare.json` and `attempt.json`. 8 turns, 47 s.

| field | value |
|---|---|
| compare status / complete / samples | passed / true / 64 |
| sim_vs_hw | 0 LSB, exact |
| tflite_vs_sim | 0 LSB, exact |
| attempt_id / kit_revision / dirty | 20261013-144412-46d5d372 / fdbd981 / false |
| completed / npu_error | 64 / 0 |
| wall_ms median / max | 0.024 / 0.025 |
| hw.bin | byte-identical to `evidence/2026-10-12-hardware/batch64/signal-freq/hw.bin` (sha256 f3e1261b…) |

Scope: one assistant (Claude Code), one example, one run. The assistant followed the skills and called the documented CLI route; it did not use the `polarfire-bringup` agent as a subagent. Codex was not tested for this route, because its sandbox has no network access.

Files: `transcript.md` (prompt context, every tool call, truncated tool results and the final answer; machine names, addresses and local paths replaced with `<tools-host>`, `<tools-host-home>`, `<kit>`, `<kit-root>`, `<scratch>` and `<config>`), and `signal-freq/` with the run's records and outputs, scrubbed the same way.
