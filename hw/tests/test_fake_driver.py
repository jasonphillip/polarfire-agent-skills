"""Host-only runner checks. No UIO, DMA device, or network is used."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time


def model_bytes(preset=0):
    data = bytearray(80)
    struct.pack_into("<4I", data, 0, 0xF1267B05, preset, 1, 1)
    struct.pack_into("<2I", data, 36, 80, 80)
    struct.pack_into("<I", data, 76, 0x1ABE11ED)
    return data


def main(runner):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        model = root / "model.vnnx"
        data = root / "input.bin"
        output = root / "output.bin"
        metadata = root / "result.json"
        model.write_bytes(model_bytes())
        data.write_bytes(bytes(range(12)))

        def run(scenario, expected, timeout=100, repeat=1):
            start = time.monotonic()
            result = subprocess.run(
                [runner, "--model", str(model), "--input", str(data),
                 "--output", str(output), "--json", str(metadata),
                 "--timeout-ms", str(timeout), "--repeat", str(repeat)],
                env={**os.environ, "VBX_RUN_SCENARIO": scenario},
                capture_output=True, text=True, timeout=3,
            )
            elapsed = time.monotonic() - start
            assert result.returncode == expected, (scenario, result.stderr)
            report = json.loads(metadata.read_text())
            assert report["exit_code"] == expected, (scenario, report)
            assert "control_word" in report and "npu_error" in report, report
            print(f"{scenario}: exit {expected}; json fields ok")
            return elapsed, report

        elapsed, report = run("ok", 0, repeat=2)
        assert output.read_bytes() == bytes(range(1, 5)) + bytes(range(5, 9)) + bytes(range(9, 13))
        assert report["samples"] == 3 and report["completed"] == 6
        assert len(report["wall_ms"]) == 6
        assert [len(times) for times in report["sample_wall_ms"]] == [2, 2, 2]
        assert report["wall_ms_min"] <= report["wall_ms_median"] <= report["wall_ms_max"]
        for scenario in ("never_completes", "start_blocks"):
            elapsed, report = run(scenario, 4)
            assert elapsed < 1.5, (scenario, elapsed)
        elapsed, report = run("error_register", 5)
        assert report["npu_error"] == 9
        run("init_fails", 3)
        model.write_bytes(model_bytes(1))
        run("init_fails", 2)
        print("v500_preflight: exit 2 before fake init")
        model.write_bytes(model_bytes())
        data.write_bytes(bytes(range(5)))
        run("ok", 2)
        print("bad_input_size: exit 2")


if __name__ == "__main__":
    main(sys.argv[1])
