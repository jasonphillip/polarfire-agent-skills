# Install and invoke

Use a local checkout of this kit.
Set `KIT_ROOT` to its absolute path.
The agent definitions and skills are in `agents/` and `skills/`.
The Python pipeline runs from the same checkout.

## Client versions recorded on 2026-10-12

These versions come from the main session's recorded client inventory.

| Client | Recorded version | Local check |
|---|---|---|
| Claude Code | 2.1.296 | Headless plugin load listed one agent and ten original skills. |
| Codex CLI | 0.157.1 | Installation and invocation not yet tested. |
| Cursor | Recorded as not installed in the client inventory. | Manifest present; loading not tested. |

The main session loaded the Claude Code plugin headlessly on 2026-10-12.
It listed `polarfire-bringup` and the ten skills present at that time.
It did not run a skill or validate the two new skills in this revision.

## Claude Code

Once this repository is public, install it from the marketplace:

```text
/plugin install polarfire-agent-skills --marketplace jasonphillip/polarfire-agent-skills
```

For a local clone, start Claude Code with the plugin directory:

```sh
claude --plugin-dir /absolute/path/to/polarfire-agent-skills
```

Enter this request in the client:

```text
Use the polarfire-bringup agent to run the signal-freq example through inspect.
```

The marketplace command is an install instruction, not a tested install result.
The local headless check established plugin discovery only.
No model stage, tools host stage, or kit stage was tested through the client.

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

The Codex manifest and folder method have not yet been tested with Codex CLI 0.157.1.
No Codex plugin install command is claimed here.
After loading, ask Codex to use the `adapt-your-model` skill for an inspect run.
Agent discovery through the Codex manifest has not been tested.

## Cursor

The `.cursor-plugin/` manifest is retained for future testing.
The client inventory recorded Cursor as not installed on 2026-10-12.
Its plugin load, agent discovery, and skill invocation are untested.
Use the Cursor documentation for the installed version before invoking this pack.

## Pipeline setup

Create the kit environment from the checkout:

```sh
KIT_ROOT=/absolute/path/to/polarfire-agent-skills
make -C "$KIT_ROOT" env
"$KIT_ROOT/.venv/bin/python" -m pfkit example run signal-freq --until inspect --run-dir "$KIT_ROOT/reports/signal-inspect"
```

This command shows the intended CLI route.
Read `docs/pipeline.md` for stage outputs and remote configuration.
Read `docs/hardware.md` before tools host or kit work.
