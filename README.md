# PolarFire Agent Skills

This pack gives a coding agent a staged workflow and evidence rules for model deployment on the Microchip PolarFire SoC.
It targets the MPFS250T kit and CoreVectorBlox V250.
Optional skills cover fabric control and programming.

## Quick Start

Read `docs/install.md` for client setup and tested discovery claims.
Create the kit environment and run the small local inspect path:

```sh
KIT_ROOT=/absolute/path/to/polarfire-agent-skills
make -C "$KIT_ROOT" env
"$KIT_ROOT/.venv/bin/python" -m pfkit example run signal-freq --until inspect --run-dir "$KIT_ROOT/reports/signal-inspect"
```

The inspect stage needs the Python environment and example inputs.
Compile and sim need a configured tools host.
Infer needs a configured kit and built `hw/vbx_run`.
Each stage writes evidence in its run directory.

Validated: see `docs/validation.md` and `evidence/2026-10-12-toolshost/`,
`evidence/2026-10-12-sim-runs/`, and `evidence/2026-10-12-clean-checkout/`.
Not yet: hardware inference and simulator-to-hardware comparison.

Read `docs/scope.md` for the supported profile.
Read `docs/pipeline.md` for commands and outputs.
Read `docs/hardware.md` for the fabric and runner path.
Read `docs/claims.md` for probe results and limits.
Use `agents/polarfire-bringup.md` as the portable entry point.

The pack does not ship Microchip tools, a Linux image, or a VNNX model.
The case study's hardware results came from its own setup.
Rerun checks before quoting them for another kit.

Copyright 2026 Jason Phillip, Tychon AI. Licensed under Apache-2.0.
