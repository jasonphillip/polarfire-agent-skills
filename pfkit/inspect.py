"""Read TFLite operators and compare them with the SDK 2.0.3 table."""
from __future__ import annotations

import json
import re
from pathlib import Path
from importlib.resources import files


def ops_table():
    source = files("pfkit").joinpath("data/ops_2.0.3.md").read_text()
    return {m.group(1): m.group(2) for line in source.splitlines()
            if (m := re.match(r"^\|([A-Z][A-Z0-9_]*)\|(.*?)\|$", line))}


def supported_ops():
    return set(ops_table())


def _enum_name(enum, value):
    return next((key for key, val in vars(enum).items() if not key.startswith("_") and isinstance(val, int) and val == value), str(value))


def inspect_model(path):
    from tensorflow.lite.python import schema_py_generated as schema
    model = schema.Model.GetRootAsModel(Path(path).read_bytes(), 0)
    operators, tensors, flags = [], [], []
    table = ops_table()
    for sg_index in range(model.SubgraphsLength()):
        sg = model.Subgraphs(sg_index)
        tensor_base = len(tensors)
        for i in range(sg.TensorsLength()):
            t = sg.Tensors(i)
            q = t.Quantization()
            shape = list(t.ShapeAsNumpy()) if t.ShapeLength() else []
            signature = list(t.ShapeSignatureAsNumpy()) if t.ShapeSignatureLength() else shape
            item = {"subgraph": sg_index, "index": i, "name": t.Name().decode() if t.Name() else "",
                    "shape": [int(v) for v in shape], "shape_signature": [int(v) for v in signature],
                    "dtype": _enum_name(schema.TensorType, t.Type()),
                    "quantization": {"scales": [float(q.Scale(j)) for j in range(q.ScaleLength())] if q else [],
                                     "zero_points": [int(q.ZeroPoint(j)) for j in range(q.ZeroPointLength())] if q else [],
                                     "quantized_dimension": int(q.QuantizedDimension()) if q else 0},
                    "buffer": int(t.Buffer())}
            if any(v < 0 for v in signature) or any(v <= 0 for v in shape):
                flags.append(f"dynamic shape tensor {i}")
            if item["dtype"].startswith("FLOAT"):
                flags.append(f"float tensor {i} ({item['name']})")
            if len(item["quantization"]["scales"]) > 1:
                flags.append(f"per-channel quantization tensor {i}")
            tensors.append(item)
        for role, length, indexer in (("input", sg.InputsLength(), sg.Inputs), ("output", sg.OutputsLength(), sg.Outputs)):
            for j in range(length):
                idx = indexer(j)
                if not tensors[tensor_base + idx]["shape"] or tensors[tensor_base + idx]["shape"][0] != 1:
                    flags.append(f"batch dimension not 1 on {role} {idx} in subgraph {sg_index}")
        for i in range(sg.OperatorsLength()):
            op = sg.Operators(i)
            code = model.OperatorCodes(op.OpcodeIndex())
            name = _enum_name(schema.BuiltinOperator, code.BuiltinCode())
            options_name = _enum_name(schema.BuiltinOptions, op.BuiltinOptionsType())
            options = {}
            if options_name not in ("NONE", "0") and hasattr(schema, options_name) and op.BuiltinOptions():
                cls = getattr(schema, options_name)
                obj = cls()
                tab = op.BuiltinOptions()
                obj.Init(tab.Bytes, tab.Pos)
                for method in dir(obj):
                    if method[0].isupper() and callable(getattr(obj, method)) and not method.endswith("AsNumpy"):
                        try:
                            val = getattr(obj, method)()
                            if isinstance(val, (int, float, str, bool, bytes)):
                                options[method] = val.decode() if isinstance(val, bytes) else val
                        except TypeError:
                            pass
            item = {"subgraph": sg_index, "index": i, "operator": name, "options_type": options_name,
                    "options": options, "inputs": [int(op.Inputs(k)) for k in range(op.InputsLength())],
                    "outputs": [int(op.Outputs(k)) for k in range(op.OutputsLength())],
                    "supported": name in table}
            if not item["supported"]:
                flags.append(f"unsupported operator {name} at {i}")
            else:
                limits = dict(re.findall(r"\*\*(.*?)\*\*\s*=\s*\[([^]]+)\]", table[name]))
                item["sdk_limits"] = limits
                for label, option, enum in (("Fused activation function", "FusedActivationFunction", schema.ActivationFunctionType),
                                            ("Padding", "Padding", schema.Padding)):
                    if label in limits and option in options:
                        allowed = {v.strip() for v in limits[label].split(",")}
                        value = options[option]
                        if str(value) not in allowed and _enum_name(enum, value) not in allowed:
                            flags.append(f"unsupported {label} {value} for {name} at {i}")
            if name == "SHAPE":
                flags.append(f"SHAPE operator at {i}")
            if name in ("RESHAPE", "TRANSPOSE", "SPLIT") and len(item["inputs"]) > 1:
                shape_idx = item["inputs"][1]
                if shape_idx >= 0:
                    buf = model.Buffers(sg.Tensors(shape_idx).Buffer())
                    if not buf or buf.DataLength() == 0:
                        flags.append(f"non-constant shape tensor {shape_idx} at {i}")
            operators.append(item)
    return {"operators": operators, "tensors": tensors, "flags": flags,
            "unsupported": [o["operator"] for o in operators if not o["supported"]],
            "limit_violations": [f for f in flags if f.startswith("unsupported ") and not f.startswith("unsupported operator ")]}


def print_inspection(result):
    print(json.dumps(result, indent=2, sort_keys=True))
