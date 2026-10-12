---
name: claim-log
description: Tie each hardware claim to a report file and its primary output.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# Claim log

Create a demonstrated-state table. Give every row a scope, result, evidence file path, and evidence class. Distinguish simulation, synthesis, software test, and kit measurement. Do not promote a design target to a measured result.

Source: `README.md`

Use tool output, raw logs, and generated reports as primary evidence. If a claim is inferred, label it and state the missing check. Preserve the exact command, tool version, input hash, timestamp, and exit code beside each result.

Source: `workers/polarfire-hybrid-control/AGENTS.md`

Audit a copied Libero report directory in strict mode.

```bash
python3 tools/audit_libero_reports.py --strict <report-dir>
```
Source: `workers/polarfire-hybrid-control/Makefile`

`<report-dir>` replaces the Makefile variable `$(REPORT_DIRS)`. Supply the report directory under review.

The audit checks positive slack, retained PID hierarchy and resources, and critical pruning markers. Record its output and exit code. Do not call a missing or unparseable bundle a pass.

Source: `workers/polarfire-hybrid-control/tools/audit_libero_reports.py`

Keep one row per measured result. Name the model, bitstream, kit run, and source report in each row.

Source: `workers/polarfire-hybrid-control/AGENTS.md`

Mark software simulation, synthesis, and kit output as separate evidence classes. Do not merge their limits.

Source: `docs/model-to-v250.md`

Keep failed checks in the log. A missing or unparseable report remains an unresolved result.

Source: `workers/polarfire-hybrid-control/tools/audit_libero_reports.py`

## Checks

- Read a primary report path beside every result row.
- Read the command, tool version, input hash, and exit code beside each row.
- Read a successful strict audit result before reporting timing closure.
