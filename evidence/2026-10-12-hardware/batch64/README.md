# 64-sample held-out batch and per-model timing, 2026-10-12

Inputs: the first 64 test-split spectra of each example's own dataset (seeded), quantized with the TFLite input scale and zero point, sent as one 64-sample file to the simulator (tools host) and to the kit (runner with K-sample support, commit 5fe1239).

| example | samples | sim_vs_hw max LSB | tflite_vs_sim max LSB | float_vs_tflite max abs | batch median ms per sample | timing-200 (one sample, 200 repeats) |
|---|---|---|---|---|---|---|
| signal-freq | 64 | 0 | 0 | 0.0414 | 0.024 | min 0.023 median 0.024 max 0.055001 ms |
| odmr-mlp | 64 | 0 | 0 | 1.6713 | 0.034 | min 0.034 median 0.034 max 0.060001 ms |
