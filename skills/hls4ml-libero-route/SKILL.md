---
name: hls4ml-libero-route
description: Choose the short Dense-only hls4ml Libero route when fabric inference fits.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# hls4ml Libero route

Choose this route for a small Dense-only network that should reside in fabric.
Use the VectorBlox path for the V250 runtime and its INT8 TFLite to VNNX flow.
The hls4ml Libero backend uses SmartHLS. The tutorial dates release v1.3.0 to 2026-03-20.
The tutorial calls PR #1240 an initial implementation. This pack has not run it.

Source: `docs/model-to-v250.md`

The tutorial says the backend handles Dense layers only. Check the model layer list before choosing this route.

Source: `docs/model-to-v250.md`

This route builds network logic in fabric. The V250 route compiles TFLite into a runtime model.

Source: `docs/model-to-v250.md`

Keep conversion, synthesis, and kit inference as separate checks. A successful conversion is not a kit result.

Source: `docs/model-to-v250.md`

Record the hls4ml release and generated project path with the build output.

Source: `docs/model-to-v250.md`

Verify backend support with the installed release before claiming a build.

Source: `docs/model-to-v250.md`

## Checks

- Read Dense-only layers from the model inspection output.
- Read the installed hls4ml version and selected Libero backend from tool output.
- Read a completed conversion and generated project path from tool output.
- Read synthesis and kit output before claiming a deployed fabric model.
