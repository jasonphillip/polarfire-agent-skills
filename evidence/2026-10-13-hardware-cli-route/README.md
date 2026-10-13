# 64-sample CLI route on the kit, 2026-10-13

Follow-up A of the release-readiness pass: the new `--samples 64` route of `pfkit example run`, end to end, on the current kit image (case-study image, overlay `seed7`, no programming).

Kit revision `db95a26`, clean tree (`attempt.json`: `dirty` false). Runner `hw/vbx_run` from commit `5fe1239`, the same runner as the 2026-10-12 batch.

```sh
python -m pfkit example run signal-freq --until compare --samples 64 --toolshost <config>/toolshost.yaml --kit <config>/kit.yaml --run-dir reports/<stamp>-signal-freq-cli64
python -m pfkit example run odmr-mlp    --until compare --samples 64 --toolshost <config>/toolshost.yaml --kit <config>/kit.yaml --run-dir reports/<stamp>-odmr-mlp-cli64
```

Each run trained, exported, compiled on the tools host, simulated on the tools host, ran on the kit and compared, in about 25 s. Both exited 0.

| example | compare status | complete | samples | float_vs_tflite max abs (tolerance) | tflite_vs_sim max LSB | sim_vs_hw max LSB | completed / npu_error | wall_ms median / max |
|---|---|---|---|---|---|---|---|---|
| signal-freq | passed | true | 64 | 0.0414 (2.0) | 0, exact | 0, exact | 64 / 0 | 0.024 / 0.061 |
| odmr-mlp | passed | true | 64 | 1.6713 (5.0) | 0, exact | 0, exact | 64 / 0 | 0.034 / 0.035001 |

Identity with the 2026-10-12 batch (`evidence/2026-10-12-hardware/batch64/`):

| example | payload sha256 (input bytes) | hw.bin sha256 | hw.bin equal to 2026-10-12 | sim outputs equal to 2026-10-12 |
|---|---|---|---|---|
| signal-freq | 56b5c46c63d03e2cb4f69c19c4c5c4a786a662a3f006796de0b56ec83e3a549a | f3e1261b53f12fd8016237e18dd15164b6c6ea250c4367f635d96914492ad40d | yes | yes |
| odmr-mlp | 85f113c7d5d3145634538586f2bf9a1db06eeff7d55b34ced457b4ba82f1b23a | 88261c057812c6196ea9bb3b652a79b38ebf231fe69f0e0956d1a8a076cac367 | yes | yes |

The `model.vnnx` files of these runs have different sha256 values from the 2026-10-12 runs, while the simulator and kit outputs are byte-identical. The cause of the file difference was not investigated; the outputs, not the container bytes, are what this record compares.

Timing: `wall_ms` is the runner's own measurement (see `docs/hardware.md`), a sample of a quiet board, not a worst-case bound.

Files per example: `attempt.json`, `input.manifest.json`, `input.int8.npy`, `compile.json`, `sim.json`, `sim.npz`, `infer.json`, `hw.json`, `hw.bin`, `compare.json`, `summary.md`. Machine names, addresses and home paths are replaced with `<tools-host>`, `<tools-host-home>`, `<kit>`, `<kit-root>` and `<config>`.

## Re-run after the review fixes (same day, kit revision 84e9b7c, clean tree)

The review fix commit `84e9b7c` changed remote transfers (raw SFTP targets), the `hw.bin` size check and compare's payload binding, so the route was run again on the kit.

| run | kit remote_dir | compare status / complete / samples | sim_vs_hw | infer | hw.bin sha256 | equal to 2026-10-12 |
|---|---|---|---|---|---|---|
| `post-fix-spaced-remote-dir/signal-freq` | `/tmp/pf kit` (contains a space) | passed / true / 64 | 0 LSB, exact | completed | f3e1261b53f12fd8… | yes |
| `post-fix/odmr-mlp` | default | passed / true / 64 | 0 LSB, exact | completed | 88261c057812c619… | yes |

The spaced run shows the remote-path handling end to end: `scp` targets carry the raw path (OpenSSH 9.6 uses SFTP; a shell-quoted target failed with "No such file or directory" in a separate live probe) and the `ssh` scripts quote it. Each run took about 27 s.
