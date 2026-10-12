#!/usr/bin/env python3
"""Compare guard policy with SDK operator listings; mappings are explicit."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "deps/tychon-quantum-sensing/workers/odmr-edge-ml/src"
SDK = ROOT / "deps/vectorblox-sdk"
sys.path.insert(0, str(SRC))

from odmr_edge_ml.validation.ops_guard import VECTORBLOX_ALLOWED_OPS, VECTORBLOX_BANNED_OPS
from odmr_edge_ml.validation.tflite_ops import BANNED_TFLITE_OPS

# Direct ATen-to-TFLite mappings only. Other lowerings need graph-specific proof.
MAPPING = {
    "aten.linear": "FULLY_CONNECTED", "aten.conv2d": "CONV_2D",
    "aten.relu": "RELU", "aten.relu6": "RELU6", "aten.hardtanh": "RELU6",
    "aten.add": "ADD", "aten.mean": "MEAN", "aten.adaptive_avg_pool2d": "AVERAGE_POOL_2D",
    "aten.reshape": "RESHAPE", "aten.view": "RESHAPE", "aten.flatten": "RESHAPE",
    "aten.permute": "TRANSPOSE", "aten.unsqueeze": "EXPAND_DIMS", "aten.squeeze": "SQUEEZE",
    "aten.sigmoid": "LOGISTIC", "aten.tanh": "TANH", "aten.gelu": "GELU",
    "aten.silu": "SILU", "aten.softmax": "SOFTMAX", "aten.log_softmax": "LOG_SOFTMAX",
    "aten.max_pool2d": "MAX_POOL_2D", "aten.mul": "MUL",
}


def main():
    table = SDK / "docs/OPS.md"
    ops_doc = set(re.findall(r"^\|([A-Z][A-Z_0-9]*)\|", table.read_text(), re.MULTILINE))
    ops_json = set(json.loads((SDK / "python/vbx/vbx/generate/supported_ops.json").read_text()))
    print(f"SDK OPS.md={len(ops_doc)}; supported_ops.json={len(ops_json)}")
    for name, listing in (("OPS.md", ops_doc), ("supported_ops.json", ops_json)):
        banned = sorted(f"{op} -> {MAPPING[op]}" for op in VECTORBLOX_BANNED_OPS if MAPPING.get(op) in listing)
        banned += sorted(f"TFLite {op}" for op in BANNED_TFLITE_OPS if op in listing)
        allowed_absent = sorted(f"{op} -> {MAPPING[op]}" for op in VECTORBLOX_ALLOWED_OPS if op in MAPPING and MAPPING[op] not in listing)
        unmapped = sorted(op for op in VECTORBLOX_ALLOWED_OPS if op not in MAPPING)
        print(f"{name} lists, guard bans: {', '.join(banned) or '(none)'}")
        print(f"guard allows, {name} omits: {', '.join(allowed_absent) or '(none)'}")
        print(f"allowed ATen ops without direct mapping: {', '.join(unmapped) or '(none)'}")
    print("A listed op is documentation evidence, not proof that every shape or graph compiles.")


if __name__ == "__main__":
    main()
