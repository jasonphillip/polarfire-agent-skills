"""Small, explicit SSH and SCP command plans."""
from __future__ import annotations
import hashlib
import json
import shlex
import subprocess
from pathlib import Path
import yaml
from .pipeline import write_json, sha256


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


def compile_plan(model, output, config):
    cfg = load_config(config)
    target = cfg["ssh_target"]
    transfer = cfg.get("transfer_dir", cfg["remote_work_dir"])
    work = cfg["remote_work_dir"]
    name = Path(model).name
    out = Path(output).name
    cmds = [_ssh(target, f"mkdir -p {shlex.quote(transfer)}"),
            ["scp", str(model), f"{target}:{transfer}/{name}"],
            _ssh(target, tools_command(cfg, _q(["vnnx_compile", "-c", cfg["size_config"], "-t", f"{work}/{name}", "-o", f"{work}/{out}"]))),
            ["scp", f"{target}:{transfer}/{out}", str(output)]]
    return cmds


def sim_plan(model, input_file, output, config):
    cfg = load_config(config)
    target = cfg["ssh_target"]
    transfer = cfg.get("transfer_dir", cfg["remote_work_dir"])
    work = cfg["remote_work_dir"]
    script = Path(__file__).parent / "remote" / "vbx_sim_run.py"
    cmds = [_ssh(target, f"mkdir -p {shlex.quote(transfer)}"),
            ["scp", str(model), str(input_file), str(script), f"{target}:{transfer}/"],
            _ssh(target, tools_command(cfg, _q(["python", f"{work}/vbx_sim_run.py", "--model", f"{work}/{Path(model).name}",
                                       "--input", f"{work}/{Path(input_file).name}", "--output", f"{work}/{Path(output).name}"]))),
            ["scp", f"{target}:{transfer}/{Path(output).name}", str(output)]]
    return cmds


def infer_plan(model, input_file, output, metadata, runner, config, timeout_ms):
    cfg = load_config(config)
    target, directory = cfg["ssh_target"], cfg["remote_dir"]
    paths = [Path(runner), Path(model), Path(input_file)]
    commands = [_ssh(target, f"mkdir -p {shlex.quote(directory)}"),
                ["scp", *map(str, paths), f"{target}:{directory}/"],
                _ssh(target, _q([f"{directory}/{Path(runner).name}", "--model", f"{directory}/{Path(model).name}",
                                 "--input", f"{directory}/{Path(input_file).name}", "--output", f"{directory}/{Path(output).name}",
                                 "--timeout-ms", str(timeout_ms), "--json", f"{directory}/{Path(metadata).name}"])),
                ["scp", f"{target}:{directory}/{Path(output).name}", str(output)],
                ["scp", f"{target}:{directory}/{Path(metadata).name}", str(metadata)]]
    return commands


def run_plan(commands, dry_run=False, manifest=None):
    records = []
    for argv in commands:
        print(_q(argv))
        if dry_run:
            records.append({"command": _q(argv), "exit_code": "not run"})
            continue
        result = subprocess.run(argv, text=True, capture_output=True)
        records.append({"command": _q(argv), "exit_code": result.returncode,
                        "stdout": result.stdout, "stderr": result.stderr})
        if result.stdout: print(result.stdout, end="")
        if result.stderr: print(result.stderr, end="", file=__import__("sys").stderr)
        if result.returncode:
            if manifest: write_json(manifest, {"commands": records})
            raise RuntimeError(f"Command failed with exit {result.returncode}: {_q(argv)}")
    if manifest:
        write_json(manifest, {"commands": records})
    return records
