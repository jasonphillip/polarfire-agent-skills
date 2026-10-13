"""Small, explicit SSH and SCP command plans."""
from __future__ import annotations
import hashlib
import json
import secrets
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import yaml
from .pipeline import write_json, sha256
from .errors import RemoteCommandError


def _q(parts):
    return shlex.join([str(p) for p in parts])


def load_config(path):
    return yaml.safe_load(Path(path).read_text())


def _ssh(target, script):
    return ["ssh", target, script]


def tools_command(cfg, script):
    prefix = shlex.split(cfg.get("command_prefix", ""))
    activate = cfg.get("venv_activate", "")
    inner = (f"source {activate} && " if activate else "") + script
    return _q(prefix + ["bash", "-lc", inner]) if prefix else _q(["bash", "-lc", inner])


def _plan_attempt_id(attempt_id):
    return attempt_id or datetime.now(timezone.utc).strftime("manual-%Y%m%d-%H%M%S-") + secrets.token_hex(4)


def compile_plan(model, output, config, attempt_id=None):
    cfg = load_config(config)
    target = cfg["ssh_target"]
    attempt_id = _plan_attempt_id(attempt_id)
    transfer = f"{cfg.get('transfer_dir', cfg['remote_work_dir'])}/{attempt_id}"
    work = f"{cfg['remote_work_dir']}/{attempt_id}"
    name = Path(model).name
    out = Path(output).name
    cmds = [_ssh(target, f"mkdir -p {shlex.quote(transfer)}"),
            ["scp", str(model), f"{target}:{transfer}/{name}"],
            _ssh(target, tools_command(cfg, _q(["vnnx_compile", "-c", cfg["size_config"], "-t", f"{work}/{name}", "-o", f"{work}/{out}"]))),
            ["scp", f"{target}:{transfer}/{out}", str(output)]]
    return cmds


def sim_plan(model, input_file, output, config, attempt_id=None):
    cfg = load_config(config)
    target = cfg["ssh_target"]
    attempt_id = _plan_attempt_id(attempt_id)
    transfer = f"{cfg.get('transfer_dir', cfg['remote_work_dir'])}/{attempt_id}"
    work = f"{cfg['remote_work_dir']}/{attempt_id}"
    script = Path(__file__).parent / "remote" / "vbx_sim_run.py"
    cmds = [_ssh(target, f"mkdir -p {shlex.quote(transfer)}"),
            ["scp", str(model), str(input_file), str(script), f"{target}:{transfer}/"],
            _ssh(target, tools_command(cfg, _q(["python", f"{work}/vbx_sim_run.py", "--model", f"{work}/{Path(model).name}",
                                       "--input", f"{work}/{Path(input_file).name}", "--output", f"{work}/{Path(output).name}"]))),
            ["scp", f"{target}:{transfer}/{Path(output).name}", str(output)]]
    return cmds


def infer_plan(model, input_file, output, metadata, runner, config, timeout_ms, attempt_id=None):
    input_file = Path(input_file)
    if input_file.suffix == ".npy":
        import numpy as np
        samples = np.load(input_file, allow_pickle=False)
        if samples.dtype != np.int8 or samples.ndim < 2 or samples.shape[0] < 1:
            raise ValueError("inference input .npy must contain K >= 1 int8 samples")
        binary = input_file.with_suffix(".bin")
        np.ascontiguousarray(samples).tofile(binary)
        input_file = binary
    cfg = load_config(config)
    attempt_id = _plan_attempt_id(attempt_id)
    target, directory = cfg["ssh_target"], f"{cfg['remote_dir']}/{attempt_id}"
    paths = [Path(runner), Path(model), Path(input_file)]
    commands = [_ssh(target, f"mkdir -p {shlex.quote(directory)}"),
                ["scp", *map(str, paths), f"{target}:{directory}/"],
                _ssh(target, _q([f"{directory}/{Path(runner).name}", "--model", f"{directory}/{Path(model).name}",
                                 "--input", f"{directory}/{Path(input_file).name}", "--output", f"{directory}/{Path(output).name}",
                                 "--timeout-ms", str(timeout_ms), "--json", f"{directory}/{Path(metadata).name}"])),
                ["scp", f"{target}:{directory}/{Path(output).name}", str(output)],
                ["scp", f"{target}:{directory}/{Path(metadata).name}", str(metadata)]]
    return commands


def run_plan(commands, dry_run=False, manifest=None, timeout_s=None):
    records = []

    def output_text(value):
        if isinstance(value, bytes):
            return value.decode(errors="replace")
        return value or ""

    def flush():
        if manifest:
            snapshot = json.loads(Path(manifest).read_text()) if Path(manifest).is_file() else {}
            snapshot["commands"] = records
            write_json(manifest, snapshot)

    for argv in commands:
        argv = [str(arg) for arg in argv]
        print(_q(argv))
        record = {"argv": argv, "command": _q(argv), "executed": False,
                  "started_utc": None, "finished_utc": None, "exit_code": "not run",
                  "stdout": "", "stderr": "", "error": None}
        records.append(record)
        if dry_run:
            flush()
            continue
        record["started_utc"] = datetime.now(timezone.utc).isoformat()
        try:
            result = subprocess.run(argv, text=True, capture_output=True, timeout=timeout_s)
            record.update(executed=True, exit_code=result.returncode,
                          stdout=result.stdout, stderr=result.stderr)
        except subprocess.TimeoutExpired as expired:
            record.update(executed=True, exit_code="timeout",
                          stdout=output_text(expired.stdout), stderr=output_text(expired.stderr),
                          error=f"timed out after {timeout_s} s")
        except OSError as error:
            record.update(exit_code="not run", error=str(error))
        record["finished_utc"] = datetime.now(timezone.utc).isoformat()
        flush()
        if record["stdout"]:
            print(record["stdout"], end="")
        if record["stderr"]:
            print(record["stderr"], end="", file=sys.stderr)
        if record["exit_code"] != 0:
            detail = (f"Command could not start: {record['error']}" if not record["executed"] else
                      f"Command failed with exit {record['exit_code']}: {_q(argv)}")
            raise RemoteCommandError(detail, records)
    return records
