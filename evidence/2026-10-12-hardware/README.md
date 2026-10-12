# Hardware evidence, 2026-10-12

One Icicle Kit (facts in kit-facts.txt), running the case study's image with its overlay (uio node vbx@60030000). Runner: hw/vbx_run.c at commit 5faeb74, cross-built on the tools host (sha256 in kit-facts.txt).

| example | hw.json | compare.json |
|---|---|---|
| signal-freq | completed 1 npu_error 0 median_ms 0.020999 | sim_vs_hw 0 tflite_vs_sim 0 pass True |
| odmr-mlp | completed 1 npu_error 0 median_ms 0.032 | sim_vs_hw 0 tflite_vs_sim 0 pass True |

negatives/ (run by hand over SSH with the odmr-mlp model, 100-byte input): n1 wrong size (32 bytes) exit 2; n3 missing model exit 3; n4 --repeat 200 timing; n5 V500-compiled signal-freq model refused, exit 2, control word 0, completed 0; n6 V250 rerun, completed 1, output byte-identical to the pfkit run. --timeout-ms 0 is rejected as a bad argument (exit 2); a real timeout was not forced.
