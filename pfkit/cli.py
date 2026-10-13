"""Command line entry points for reproducible pipeline stages."""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from .pipeline import ROOT


def _run_dir(args):
    if not args.run_dir:
        raise ValueError("--run-dir is required for this stage")
    return Path(args.run_dir)


def parser():
    p = argparse.ArgumentParser(prog="pfkit")
    sub = p.add_subparsers(dest="command", required=True)
    deps = sub.add_parser("deps")
    deps_sub = deps.add_subparsers(dest="deps_command", required=True)
    fetch = deps_sub.add_parser("fetch")
    fetch.add_argument("--dry-run", action="store_true")
    for name in ("data", "train", "eval", "export"):
        stage = sub.add_parser(name)
        stage.add_argument("example")
        stage.add_argument("--run-dir", required=True)
        if name in ("data", "train"):
            stage.add_argument("--full", action="store_true")
        if name == "data":
            stage.add_argument("--import", dest="import_path")
        if name == "train":
            stage.add_argument("--epochs", type=int)
        if name == "export":
            stage.add_argument("--form", choices=("conv1x1", "fc"), default="conv1x1")
    inspect = sub.add_parser("inspect")
    inspect.add_argument("model")
    inspect.add_argument("--run-dir")
    inspect.add_argument("--sdk-root", help="VectorBlox SDK checkout containing docs/OPS.md")
    inspect.add_argument("--allow-fc-chain", action="store_true", help="allow measured SDK 2.0.3 simulator failure")
    compile_p = sub.add_parser("compile")
    compile_p.add_argument("model")
    compile_p.add_argument("--output", required=True)
    compile_p.add_argument("--config", default=str(ROOT / "toolshost.yaml"))
    compile_p.add_argument("--run-dir")
    compile_p.add_argument("--dry-run", action="store_true")
    sim = sub.add_parser("sim")
    sim.add_argument("model")
    sim.add_argument("--input", required=True)
    sim.add_argument("--output", required=True)
    sim.add_argument("--config", default=str(ROOT / "toolshost.yaml"))
    sim.add_argument("--run-dir")
    sim.add_argument("--dry-run", action="store_true")
    infer = sub.add_parser("infer")
    infer.add_argument("model")
    infer.add_argument("--input", required=True)
    infer.add_argument("--output", required=True)
    infer.add_argument("--json", required=True)
    infer.add_argument("--runner", default=str(ROOT / "hw" / "vbx_run"))
    infer.add_argument("--config", default=str(ROOT / "kit.yaml"))
    infer.add_argument("--timeout-ms", type=int, default=5000)
    infer.add_argument("--run-dir")
    infer.add_argument("--dry-run", action="store_true")
    compare = sub.add_parser("compare")
    compare.add_argument("example")
    compare.add_argument("--run-dir", required=True)
    compare.add_argument("--inputs")
    compare.add_argument("--sim")
    compare.add_argument("--hw")
    compare.add_argument("--lsb-tolerance", type=int, default=0)
    compare.add_argument("--scope", choices=("requested", "full"), default="requested")
    report = sub.add_parser("report")
    report.add_argument("--run-dir", required=True)
    example = sub.add_parser("example")
    example_sub = example.add_subparsers(dest="example_command", required=True)
    run = example_sub.add_parser("run")
    run.add_argument("name")
    run.add_argument("--until", choices=("data", "train", "eval", "export", "inspect", "compile", "sim", "infer", "compare"), default="inspect")
    run.add_argument("--run-dir")
    run.add_argument("--toolshost", default=str(ROOT / "toolshost.yaml"), help="tools host config for compile and sim")
    run.add_argument("--kit", default=str(ROOT / "kit.yaml"), help="kit config for infer")
    run.add_argument("--full", action="store_true")
    run.add_argument("--sdk-root", help="VectorBlox SDK checkout containing docs/OPS.md")
    run.add_argument("--form", choices=("conv1x1", "fc"), default="conv1x1")
    run.add_argument("--allow-fc-chain", action="store_true", help="allow measured SDK 2.0.3 simulator failure")
    return p


def _deps_fetch(dry):
    import shlex
    import subprocess
    import yaml
    records = []
    lock = yaml.safe_load((ROOT / "deps.lock").read_text())
    for item in lock["repositories"]:
        dest = ROOT / "deps" / item["name"]
        commands = ([] if dest.exists() else [["git", "clone", item["url"], str(dest)]]) + [
                    ["git", "-C", str(dest), "checkout", "--detach", str(item["commit"])]]
        for cmd in commands:
            print(shlex.join(cmd))
            if not dry:
                subprocess.run(cmd, check=True)
    workers = ROOT / "deps" / "tychon-quantum-sensing" / "workers"
    for name in ("nv-sensor-sim", "odmr-edge-ml"):
        cmd = [sys.executable, "-m", "pip", "install", "-e", str(workers / name)]
        print(shlex.join(cmd))
        if not dry:
            subprocess.run(cmd, check=True)


def _prepare_quantized_input(name, run_dir):
    import numpy as np
    import tensorflow as tf
    from .pipeline import load_data
    data = load_data(run_dir)["test_x"][:1]
    model = tf.lite.Interpreter(model_path=str(run_dir / "model.tflite"), num_threads=1)
    model.allocate_tensors()
    detail = model.get_input_details()[0]
    scale, zero = detail["quantization"]
    if scale <= 0:
        raise ValueError("TFLite input has no quantization scale")
    value = np.clip(np.rint(data / scale + zero), -128, 127).astype(np.int8)
    np.save(run_dir / "input.int8.npy", value)
    value.tofile(run_dir / "input.int8.bin")


def _remote_stage(stage, model, output, config, run_dir=None, dry_run=False,
                  input_file=None, metadata=None, runner=None, timeout_ms=5000):
    from .errors import RemoteCommandError
    from .pipeline import sha256, write_json
    from .remote_ops import compile_plan, infer_plan, load_config, run_plan, sim_plan

    manifest = Path(run_dir) / f"{stage}.json" if run_dir else None
    if manifest:
        manifest.parent.mkdir(parents=True, exist_ok=True)
    cfg = load_config(config)
    result = {"status": "not run", "commands": [], "error": None,
              "config": {"path": str(config), "values": cfg},
              "local_python": "pip-freeze.txt describes the local Python environment, not the tools host"}
    if stage == "infer":
        runner_path = Path(runner)
        result["runner_sha256"] = sha256(runner_path) if runner_path.is_file() else None
    try:
        if stage == "compile":
            commands = compile_plan(model, output, config)
        elif stage == "sim":
            commands = sim_plan(model, input_file, output, config)
        else:
            commands = infer_plan(model, input_file, output, metadata, runner, config, timeout_ms)
        result["commands"] = run_plan(commands, dry_run=dry_run, manifest=manifest)
        if not dry_run:
            if not Path(output).is_file():
                raise ValueError("output missing after transfer")
            if stage == "infer":
                if not Path(metadata).is_file():
                    raise ValueError("runner JSON missing after transfer")
                details = json.loads(Path(metadata).read_text())
                samples, completed = details["samples"], details["completed"]
                npu_error, exit_code = details["npu_error"], details["exit_code"]
                if completed != samples or npu_error != 0 or exit_code != 0:
                    raise ValueError(f"runner completed {completed} of {samples}, npu_error {npu_error}, exit {exit_code}")
            result["output"] = {"path": str(output), "size_bytes": Path(output).stat().st_size,
                                "sha256": sha256(output)}
            result["status"] = "completed"
    except Exception as error:
        result["status"] = "failed"
        result["error"] = str(error)
        if isinstance(error, RemoteCommandError):
            result["commands"] = list(error.records)
            if stage == "infer":
                target, directory = cfg["ssh_target"], cfg["remote_dir"]
                transfer = ["scp", f"{target}:{directory}/{Path(metadata).name}", str(metadata)]
                retrieval = {"attempted": True, "path": str(metadata), "exit_code": "not run"}
                try:
                    retrieved = run_plan([transfer])
                    result["commands"].extend(retrieved)
                    retrieval["exit_code"] = retrieved[0]["exit_code"]
                except RemoteCommandError as retrieval_error:
                    result["commands"].extend(retrieval_error.records)
                    retrieval["exit_code"] = retrieval_error.records[-1]["exit_code"]
                    retrieval["error"] = str(retrieval_error)
                result["retrieval"] = retrieval
        error.records = result["commands"]
        if manifest:
            write_json(manifest, result)
        raise
    if manifest:
        write_json(manifest, result)
    return result


def _dispatch(args):
    from . import pipeline as steps
    if args.command == "deps":
        return _deps_fetch(args.dry_run)
    if args.command == "data":
        return steps.data(args.example, _run_dir(args), args.full, args.import_path)
    if args.command == "train":
        return steps.train(args.example, _run_dir(args), args.full, args.epochs)
    if args.command == "eval":
        return steps.evaluate(args.example, _run_dir(args))
    if args.command == "export":
        return steps.export(args.example, _run_dir(args), args.form)
    if args.command == "inspect":
        from .inspect import inspect_model, print_inspection
        result = inspect_model(args.model, args.sdk_root)
        print_inspection(result)
        if args.run_dir:
            steps.write_json(Path(args.run_dir) / "inspect.json", result)
        blocking = [flag for flag in result["blocking_flags"] if not (args.allow_fc_chain and flag.startswith("fc_chain_fused_activation"))]
        if result["unsupported"] or result["limit_violations"] or blocking:
            raise ValueError(f"Unsupported TFLite operators or options: {result['unsupported']}, {result['limit_violations']}, {blocking}")
        return result
    if args.command in ("compile", "sim", "infer"):
        _remote_stage(args.command, args.model, args.output, args.config, args.run_dir, args.dry_run,
                      input_file=getattr(args, "input", None), metadata=getattr(args, "json", None),
                      runner=getattr(args, "runner", None), timeout_ms=getattr(args, "timeout_ms", 5000))
        return None
    if args.command == "compare":
        result = steps.compare(args.example, args.run_dir, args.inputs, args.sim, args.hw,
                               args.lsb_tolerance, scope=args.scope)
        if not result["pass"]:
            raise ValueError(f"Comparison {result['status']}: failed={result['checks_failed']} "
                             f"missing={[name for name in result['required'] if name not in result['checks_run']]}")
        return result
    if args.command == "report":
        from .reporting import report
        return report(args.run_dir)
    if args.command == "example":
        from .reporting import report
        run_dir = Path(args.run_dir) if args.run_dir else ROOT / "reports" / (datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + args.name)
        run_dir.mkdir(parents=True, exist_ok=True)
        sequence = ("data", "train", "eval", "export", "inspect", "compile", "sim", "infer", "compare")
        from .reporting import append_log
        stage = "not run"
        try:
            for stage in sequence[:sequence.index(args.until)+1]:
                print(f"{stage}: {args.name}", flush=True)
                if stage == "data": result = steps.data(args.name, run_dir, args.full)
                elif stage == "train": result = steps.train(args.name, run_dir, args.full)
                elif stage == "eval": result = steps.evaluate(args.name, run_dir)
                elif stage == "export": result = steps.export(args.name, run_dir, args.form)
                elif stage == "inspect":
                    from .inspect import inspect_model
                    result = inspect_model(run_dir / "model.tflite", args.sdk_root)
                    steps.write_json(run_dir / "inspect.json", result)
                    blocking = [flag for flag in result["blocking_flags"] if not (args.allow_fc_chain and flag.startswith("fc_chain_fused_activation"))]
                    if result["unsupported"] or result["limit_violations"] or blocking:
                        raise ValueError(f"Unsupported operators or options: {result['unsupported']}, {result['limit_violations']}, {blocking}")
                elif stage == "compile":
                    result = _remote_stage(stage, run_dir / "model.tflite", run_dir / "model.vnnx", args.toolshost, run_dir)
                elif stage == "sim":
                    _prepare_quantized_input(args.name, run_dir)
                    result = _remote_stage(stage, run_dir / "model.vnnx", run_dir / "sim.npz", args.toolshost,
                                           run_dir, input_file=run_dir / "input.int8.npy")
                elif stage == "infer":
                    result = _remote_stage(stage, run_dir / "model.vnnx", run_dir / "hw.bin", args.kit,
                                           run_dir, input_file=run_dir / "input.int8.npy",
                                           metadata=run_dir / "hw.json", runner=ROOT / "hw" / "vbx_run")
                else:
                    result = steps.compare(args.name, run_dir, sim=run_dir / "sim.npz",
                                           hw=run_dir / "hw.bin", scope="full")
                    if not result["pass"]:
                        raise ValueError(f"Comparison {result['status']}: failed={result['checks_failed']} "
                                         f"missing={[name for name in result['required'] if name not in result['checks_run']]}")
                if result is not None:
                    print(json.dumps(result, sort_keys=True)[:500])
                append_log(run_dir, f"pfkit {stage} {args.name} --run-dir {run_dir}", 0)
        except Exception as error:
            failure = {"stage": stage, "error": str(error), "attempt_id": None,
                       "records": getattr(error, "records", [])}
            steps.write_json(run_dir / "failure.json", failure)
            append_log(run_dir, f"pfkit {stage} {args.name} --run-dir {run_dir}", 1)
            try:
                report(run_dir)
            except Exception as report_error:
                failure["report_error"] = str(report_error)
                steps.write_json(run_dir / "failure.json", failure)
            raise
        print(report(run_dir))
        return None


def main(argv=None):
    args = parser().parse_args(argv)
    from .reporting import append_log
    try:
        result = _dispatch(args)
        if args.command != "example" and result is not None:
            print(json.dumps(result, sort_keys=True) if isinstance(result, dict) else result)
        code = 0
    except Exception as error:
        print(f"pfkit: {error}", file=sys.stderr)
        code = 1
    if getattr(args, "run_dir", None):
        append_log(args.run_dir, "pfkit " + " ".join(sys.argv[1:] if argv is None else argv), code)
        if code == 0 and args.command in ("example", "report"):
            from .reporting import report
            report(args.run_dir)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
