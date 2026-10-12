---
name: hls4ml-libero-route
description: Assess the optional Dense-only hls4ml fabric route.
license: Apache-2.0
metadata:
  author: Jason Phillip
  version: 2026.10.0
---

# hls4ml Libero route

This is an optional fabric route for a small Dense-only network.
The kit's main model path uses pfkit and the V250 runtime.
Read `docs/scope.md` before choosing a target.
The case study tutorial describes an early hls4ml Libero backend.
This pack has not run that route.

## Selection

Inspect the model layers before choosing this route.
Require Dense-only compute layers under the backend's current rules.
Do not infer support for a convolution or branch from Dense support.
Read the installed hls4ml release and backend capabilities.
Read the SmartHLS and Libero versions from the tools host.
Record the selected target device and design configuration.

## Stages

Keep conversion, software test, synthesis, and kit output separate.
A converted project is evidence of conversion only.
A synthesized design is evidence of synthesis only.
A kit run needs a programmed image and actual output.
Use a new report directory for each model and tool version.
Keep generated project files with conversion logs.
Keep synthesis and timing reports with the build identity.

## Relationship to pfkit

Use `dataset-and-training` when the input data follows the kit contract.
Use `adapt-your-model` for the canonical V250 INT8 route.
Use this skill only for the optional fabric route.
Do not label hls4ml output as a pfkit VNNX result.
Do not compare raw numbers across routes without matched inputs.
For a V250 run, use the pfkit compare stage and its YAML tolerances.

## Evidence

The case study tutorial is a route description.
It does not establish that this kit compiled or ran a fabric model.
Keep the installed backend output as the primary source.
Record errors as failed stages rather than skipping them.
Use `claim-log` for result rows and evidence classes.

## Checks

- Read Dense-only layers from the model inspection output.
- Read the installed hls4ml version and backend from tool output.
- Read conversion output and generated project path before naming a conversion.
- Read synthesis and kit output before claiming deployed behavior.
