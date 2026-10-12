# Getting started

Read `docs/install.md` for client setup and tested installation claims.
Read `docs/scope.md` for the supported board and software profile.
Read `docs/contracts.md` and `docs/adapters.md` before adding a model.
Read `docs/pipeline.md` for stage outputs and remote configuration.
Read `docs/hardware.md` before any tools host or kit step.
Read `docs/claims.md` before making an operator or quantization claim.

## First local run

Set `KIT_ROOT` to the absolute checkout path.
Create the Python environment.
Use a new run directory for the local inspect path.

```sh
KIT_ROOT=/absolute/path/to/polarfire-agent-skills
make -C "$KIT_ROOT" env
"$KIT_ROOT/.venv/bin/python" -m pfkit example run signal-freq --until inspect --run-dir "$KIT_ROOT/reports/signal-inspect"
```

Check `dataset.manifest.json`, `training.json`, `eval.json`, and `export.manifest.json`.
Check `inspect.json` for empty unsupported and limit violation lists.
Check `commands.jsonl` for the run command and exit code.
Do not report an unrun remote stage as a pass.

## Later stages

Configure `toolshost.yaml` before compile or sim.
Build `hw/vbx_run` and configure `kit.yaml` before infer.
Use `polarfire-bringup` for the acceptance table and stage choices.
Use the individual pfkit commands in the skills to continue one run directory.
A fresh `example run` starts again at data.
Keep its generated report files with the model and input identity.
