# Source map

The kit's current command contracts are in `pfkit/cli.py`, `docs/pipeline.md`, and `docs/hardware.md`.
The model contracts are in `docs/contracts.md` and `docs/adapters.md`.
The limits on operator and quantization claims are in `docs/claims.md`.
The agent and canonical skills use those kit files.

| Skill | Current kit source |
|---|---|
| `dataset-and-training` | `pfkit/cli.py`, `pfkit/pipeline.py`, `docs/contracts.md` |
| `adapt-your-model` | `pfkit/cli.py`, `pfkit/adapters.py`, `pfkit/inspect.py`, `docs/claims.md` |
| `kit-run-inference` | `pfkit/cli.py`, `pfkit/remote_ops.py`, `docs/hardware.md` |
| `claim-log` | `pfkit/reporting.py`, `docs/contracts.md` |
| `vbx-ops-guard`, `vbx-export-int8`, `vbx-compile` | Thin entries that route to the canonical skills above. |
| `libero-build`, `kit-program` | `docs/hardware.md`, `hw/` |
| `fabric-watchdog-fallback`, `smarthls-fixed-point`, `hls4ml-libero-route` | Optional case study paths; no kit runtime claim. |

The worked source repository is:

```text
https://github.com/jasonphillip/tychon-quantum-sensing
```

The `smarthls-fixed-point` skill quotes its case study test command.
Its `Source:` lines identify the case study README and Makefile.
Other skills use the kit commands instead of copying case study commands.
