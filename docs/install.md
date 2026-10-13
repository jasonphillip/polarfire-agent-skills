# Install and invoke

Use a local checkout of this kit.
Set `KIT_ROOT` to its absolute path.
The agent definitions and skills are in `agents/` and `skills/`.
The Python pipeline runs from the same checkout.

## Client versions recorded on 2026-10-12

These versions are recorded in the client evidence.

| Client | Recorded version | Local check |
|---|---|---|
| Claude Code | 2.1.296 | Local plugin workflow reached inspect with exit 0. |
| Codex CLI | 0.157.1 | Direct use of checkout skill files reached inspect with exit 0. Plugin install not tested. |
| Cursor | Not installed in the client inventory. | Manifest present; loading not tested. |

The measured client workflows used a clean clone or checkout.
See `evidence/2026-10-12-agent-clients/claude-code.md` and
`evidence/2026-10-12-agent-clients/codex.md`.

## Claude Code

The repository is public (since 2026-10-12). Install it from the marketplace:

```text
/plugin install polarfire-agent-skills --marketplace jasonphillip/polarfire-agent-skills
```

Marketplace install: tested 2026-10-12 (user-scope install and uninstall,
version 2026.10.0, Claude Code 2.1.296).

For a local clone, start Claude Code with the plugin directory:

```sh
claude --plugin-dir /absolute/path/to/polarfire-agent-skills
```

Enter this request in the client:

```text
Use the polarfire-bringup agent to run the signal-freq example through inspect.
```

The recorded Claude Code workflow used a local plugin on a clean clone:

- Installation: the marketplace install and uninstall above succeeded.
- Skill loading: `dataset-and-training` and `polarfire-bringup` loaded locally.
- Local execution: `signal-freq` reached inspect with exit 0 and reported operators, flags, and eval MAE.
- Remote execution: compile, simulation, and kit inference were not run through this client workflow.

The recorded Claude Code and Codex workflows reached inspect. No assistant-driven
compile, simulation, or kit run is recorded in the 2026-10-12 client evidence.

## Codex CLI

The checked `.codex-plugin/plugin.json` points `skills` at `./skills/`.
A user can place each skill folder in the configured Codex skills directory.
Set `CODEX_SKILLS_DIR` to the absolute skills directory for your Codex setup.
Consult the Codex documentation for your version to confirm that directory.

```sh
KIT_ROOT=/absolute/path/to/polarfire-agent-skills
CODEX_SKILLS_DIR=/absolute/path/to/codex-skills
mkdir -p "$CODEX_SKILLS_DIR"
for skill in "$KIT_ROOT"/skills/*; do ln -s "$skill" "$CODEX_SKILLS_DIR/$(basename "$skill")"; done
```

Codex CLI 0.157.1 read the skill and agent files directly from this checkout.
It ran `signal-freq` through inspect with exit 0 and reported the expected
operators, flags, and eval MAE. The symlink method above and Codex plugin
installation were not tested. Agent discovery through the Codex manifest was
not tested. Ask Codex to read the checkout's `adapt-your-model` skill and
`polarfire-bringup` agent for an inspect run.

## Cursor

The `.cursor-plugin/` manifest is retained for future testing.
The client inventory recorded Cursor as not installed on 2026-10-12.
Its plugin load, agent discovery, and skill invocation are untested.
Use the Cursor documentation for the installed version before invoking this pack.

## Pipeline setup

Prerequisites: Python 3.11 with this kit's pinned packages; SSH key access
to the tools host and kit for remote stages; and Tk for the ODMR example on
Homebrew Python. Inspect needs the VectorBlox SDK source checkout for
`docs/OPS.md` (`pfkit deps fetch` or `--sdk-root`). The tools host needs
Libero SoC 2025.2, SmartHLS 2025.2, and their licences. The kit needs a
compatible image with `generic-uio` and the `udmabuf` DMA pool. This repo is
Apache-2.0; vendor tools and SDK sources have separate licence terms.

Create the kit environment from the checkout:

```sh
KIT_ROOT=/absolute/path/to/polarfire-agent-skills
make -C "$KIT_ROOT" env
"$KIT_ROOT/.venv/bin/python" -m pfkit example run signal-freq --until inspect --run-dir "$KIT_ROOT/reports/signal-inspect"
```

This command shows the intended CLI route.
The `torch==2.11.0` pin works on both tested platforms. The earlier
`torch==2.11.0+cpu` pin used a Linux-only local version tag and failed on macOS.
The `odmr-mlp` example imports the case-study simulator, which imports `simos` and Tk.
Homebrew Python 3.11 on macOS needs `brew install python-tk@3.11` for that example.
The Tk fix was verified in the clean macOS run: 11 tests passed and
`odmr-mlp` reached inspect. `signal-freq` needs neither dependency.
Read `docs/pipeline.md` for stage outputs and remote configuration.
Read `docs/hardware.md` before tools host or kit work.
