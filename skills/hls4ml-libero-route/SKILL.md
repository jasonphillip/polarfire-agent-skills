---
name: hls4ml-libero-route
description: Choose the short Dense-only hls4ml Libero route when fabric inference fits.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# hls4ml Libero route

Choose this route for a small Dense-only network that should reside in fabric. Use the VectorBlox path for the V250 runtime and its INT8 TFLite to VNNX flow. The hls4ml Libero backend uses SmartHLS. The user brief dates PR #1240's merge to 2026-01-22 and release v1.3.0 to 2026-03-20. The PR described the backend as draft. This pack has not run it.

Source: `docs/model-to-v250.md`

Set `backend='Libero'` in the hls4ml configuration. Verify current backend support and output with the installed hls4ml release before claiming a build.

Source: `docs/model-to-v250.md`
