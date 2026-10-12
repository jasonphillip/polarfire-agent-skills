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
    inspect = sub.add_parser("inspect")
    inspect.add_argument("model")
    inspect.add_argument("--run-dir")
    inspect.add_argument("--sdk-root", help="VectorBlox SDK checkout containing docs/OPS.md")
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
    report = sub.add_parser("report")
    report.add_argument("--run-dir", required=True)
    example = sub.add_parser("example")
    example_sub = example.add_subparsers(dest="example_command", required=True)
    run = example_sub.add_parser("run")
    run.add_argument("name")
    run.add_argument("--until", choices=("data", "train", "eval", "export", "inspect", "compile", "sim", "infer", "compare"), default="inspect")
    run.add_argument("--run-dir")
    run.add_argument("--full", action="store_true")
    run.add_argument("--sdk-root", help="VectorBlox SDK checkout containing docs/OPS.md")
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
        return steps.export(args.example, _run_dir(args))
    if args.command == "inspect":
        from .inspect import inspect_model, print_inspection
        result = inspect_model(args.model, args.sdk_root)
        print_inspection(result)
        if args.run_dir:
            steps.write_json(Path(args.run_dir) / "inspect.json", result)
        if result["unsupported"] or result["limit_violations"]:
            raise ValueError(f"Unsupported TFLite operators or options: {result['unsupported']}, {result['limit_violations']}")
        return result
    if args.command in ("compile", "sim", "infer"):
        from .remote_ops import compile_plan, sim_plan, infer_plan, run_plan
        from .pipeline import sha256, write_json
        if args.command == "compile":
            commands = compile_plan(args.model, args.output, args.config)
        elif args.command == "sim":
            commands = sim_plan(args.model, args.input, args.output, args.config)
        else:
            commands = infer_plan(args.model, args.input, args.output, args.json, args.runner, args.config, args.timeout_ms)
        records = run_plan(commands, args.dry_run)
        if args.run_dir:
            result = {"commands": records, "status": "not run" if args.dry_run else "completed"}
            if not args.dry_run:
                result["output"] = {"path": args.output, "size_bytes": Path(args.output).stat().st_size,
                                    "sha256": sha256(args.output)}
            write_json(Path(args.run_dir) / f"{args.command}.json", result)
        return None
    if args.command == "compare":
        result = steps.compare(args.example, args.run_dir, args.inputs, args.sim, args.hw, args.lsb_tolerance)
        if not result["pass"]:
            raise ValueError("Comparison tolerance violated")
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
        for stage in sequence[:sequence.index(args.until)+1]:
            print(f"{stage}: {args.name}", flush=True)
            if stage == "data": result = steps.data(args.name, run_dir, args.full)
            elif stage == "train": result = steps.train(args.name, run_dir, args.full)
            elif stage == "eval": result = steps.evaluate(args.name, run_dir)
            elif stage == "export": result = steps.export(args.name, run_dir)
            elif stage == "inspect":
                from .inspect import inspect_model
                result = inspect_model(run_dir / "model.tflite", args.sdk_root)
                steps.write_json(run_dir / "inspect.json", result)
                if result["unsupported"] or result["limit_violations"]: raise ValueError(f"Unsupported operators or options: {result['unsupported']}, {result['limit_violations']}")
            elif stage == "compile":
                from .remote_ops import compile_plan, run_plan
                records = run_plan(compile_plan(run_dir / "model.tflite", run_dir / "model.vnnx", ROOT / "toolshost.yaml"))
                steps.write_json(run_dir / "compile.json", {"commands": records, "sha256": steps.sha256(run_dir / "model.vnnx"), "size_bytes": (run_dir / "model.vnnx").stat().st_size})
                result = None
            elif stage == "sim":
                from .remote_ops import sim_plan, run_plan
                _prepare_quantized_input(args.name, run_dir)
                records = run_plan(sim_plan(run_dir / "model.vnnx", run_dir / "input.int8.npy", run_dir / "sim.npz", ROOT / "toolshost.yaml"))
                steps.write_json(run_dir / "sim.json", {"commands": records, "sha256": steps.sha256(run_dir / "sim.npz")})
                result = None
            elif stage == "infer":
                from .remote_ops import infer_plan, run_plan
                records = run_plan(infer_plan(run_dir / "model.vnnx", run_dir / "input.int8.bin", run_dir / "hw.bin", run_dir / "hw.json", ROOT / "hw" / "vbx_run", ROOT / "kit.yaml", 5000))
                steps.write_json(run_dir / "infer.json", {"commands": records, "sha256": steps.sha256(run_dir / "hw.bin")})
                result = None
            else:
                result = steps.compare(args.name, run_dir, sim=run_dir / "sim.npz", hw=run_dir / "hw.bin")
                if not result["pass"]: raise ValueError("Comparison tolerance violated")
            if result is not None: print(json.dumps(result, sort_keys=True)[:500])
            append_log(run_dir, f"pfkit {stage} {args.name} --run-dir {run_dir}", 0)
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
