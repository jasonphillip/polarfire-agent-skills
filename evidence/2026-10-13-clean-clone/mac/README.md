# Public-repository install on a second machine (2026-10-13)

Machine role: a second developer machine, macOS 27.0.1 on arm64 (Apple silicon), Homebrew Python 3.11.17, Apple clang 17.0.0. It had no earlier checkout of this repository. Paths below are replaced: `<home>`.

## Steps and results

| step | command (in the clone) | result |
|---|---|---|
| clone | `git clone https://github.com/jasonphillip/polarfire-agent-skills <home>/pfkit-repro-2026-10-13` | HEAD `203f5da` (`main` after pull request 2) |
| environment | `make env` (Homebrew `/opt/homebrew/bin` first on `PATH`) | exit 0 in 33 s; installs the pinned dependencies and the case study's `odmr-edge-ml` package in editable mode. The pip download cache was not cleared first, so 33 s is not a cold-cache time. |
| host route | `.venv/bin/python -m pytest -m host -q -rs` | 77 passed, 18 deselected, no skips |
| ML route | `.venv/bin/python -m pytest -m ml -q -rs` | 18 passed, 77 deselected, no skips; both examples reach inspect (`test_examples_through_inspect[signal-freq]`, `[odmr-mlp]`) |
| fake driver | `make -C hw test` | **fails to compile** (exit 2), see below |
| inspect | `.venv/bin/python -m pfkit example run signal-freq --until inspect --run-dir reports/mac-inspect` | exit 0; `blocking_flags` `[]`; four per-channel quantization notes, no limit violations |

The ML route needs no Tk on this machine: no test skipped, and the ODMR example's data, training, export and inspect steps ran.

## Fake-driver build on macOS: two errors

`make -C hw test` compiles `hw/vbx_run.c` with the host compiler and `-Werror`. Apple clang reports:

```
deps/vectorblox-sdk/drivers/vectorblox/vnnx-types.h:123:5: error: expected identifier
  123 |     ARG_MAX = 56,
.../MacOSX.sdk/usr/include/sys/syslimits.h:74:27: note: expanded from macro 'ARG_MAX'
hw/vbx_run.c:243:5: error: call to undeclared function 'pthread_condattr_setclock'
```

1. The SDK's operator enum has a member `ARG_MAX`; macOS's `<sys/syslimits.h>` defines `ARG_MAX` as a macro, so the enum does not parse.
2. macOS has no `pthread_condattr_setclock`; the runner's timeout uses a monotonic-clock condition variable, which is a Linux (glibc) interface.

The runner targets the kit's Linux; the fake-driver test therefore needs a Linux host (glibc). The runner source was not changed for macOS: it is the hardware-validated source. On Linux the same test passes (this repository's gate).

## Remote stages from this machine: not run

| host | check | result |
|---|---|---|
| tools host | `ssh -o BatchMode=yes -o ConnectTimeout=6 <tools-host> hostname` | connection timed out (private network route) |
| kit | `ssh -o BatchMode=yes -o ConnectTimeout=6 root@<kit> uptime` | host key verification failed (the machine has never connected to the kit) |

Compile and inference need both hosts, so the hardware route was not run from this machine. This record covers the install, the host and ML test routes, and inspect.
