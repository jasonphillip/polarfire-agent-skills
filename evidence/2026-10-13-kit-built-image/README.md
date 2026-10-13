# Kit-built image on the kit (2026-10-13)

The kit was programmed with the image this repository's build script made on the tools host (`evidence/2026-10-12-libero-build/`), replacing the case study's seed7 V250 image. Every result here is on the new image. Results on the case-study image stay in their own folders.

- Image: `Vectorblox_FD0AEBB95776A726D3D.job`, sha256 `6d5cae6c30053ed5d16325f9cc03e57eb706e6ab3f3f9306d741cad02d711c6c`, CoreVectorBlox 2.0.1 V250, programmed 2026-10-13 16:18:06 UTC (`image.json`, `program.log`). The programmed fabric digest equals the build record.
- Boot: the kit reset itself after programming and answered SSH 31 s after programming finished; `vbx@60030000` and the DMA buffers were present (`boot-checks.md`).
- Configuration used for every run, the overlay check and the audit of the old PID node: `test-configuration.md`.
- Before programming: `identity-before.md`; gate baseline: `baseline.txt`.

## Results, 64 test samples each, `example run --until compare`

| example | overall | kit vs simulator | TFLite vs simulator | float vs INT8 TFLite (max diff / tolerance) | kit completed, NPU error | wall ms median / max | `hw.bin` vs case-study image |
|---|---|---|---|---|---|---|---|
| `signal-freq` | passed | 0 LSB, exact | 0 LSB | 0.041 / 2.0 | 64, 0 | 0.024 / 0.067 | identical to the 2026-10-12 batch |
| `odmr-mlp` | passed | 0 LSB, exact | 0 LSB | 1.671 / 5.0 µT | 64, 0 | 0.034 / 0.035 | identical to the 2026-10-12 batch |
| `odmr-fcnn` | **failed** | 0 LSB, exact | 0 LSB | 29.806 / 5.0 µT | 64, 0 | 0.038 / 0.039 | identical to its case-study-image run (`evidence/2026-10-13-odmr-fcnn/`) |

Wall times are a quiet-board sample, not a worst-case bound. On the case-study image the 2026-10-12 batch had medians 0.024 and 0.034 ms.

Batch replay: the committed 2026-10-12 inputs (`evidence/2026-10-12-hardware/batch64/*/input.int8.npy`) through `pfkit infer` on the new image gave `hw.bin` byte-identical to the 2026-10-12 outputs for both examples (`replay/`).

## odmr-fcnn: hardware parity and conversion accuracy, separately

`odmr-fcnn/accuracy.json`, computed from the run's own files (same code path as `compare`; its maximum equals `compare.json`'s).

| question | odmr-fcnn | odmr-mlp (reference) |
|---|---|---|
| Hardware parity: kit output vs INT8 TFLite output | equal on all 64 samples, 0 LSB | equal, 0 LSB |
| Conversion: float prediction vs INT8 prediction, max | 29.8 µT | 1.67 µT |
| Conversion: mean / median / 90th percentile | 2.39 / 2.01 / 3.06 µT | 0.32 / 0.23 / 0.74 µT |
| Conversion: samples over the 5.0 µT tolerance | 1 of 64 | 0 of 64 |
| Ground truth: float model MAE / max error | 14.0 / 39.2 µT | 12.0 / 25.9 µT |
| Ground truth: INT8 model MAE / max error | 13.9 / 37.9 µT | 12.0 / 25.5 µT |

The 29.8 µT figure is the largest difference between the float and INT8 predictions for one sample; it is not an error against ground truth. One sample exceeds the tolerance, so `odmr-fcnn` stays **failed**; the tolerance was not changed. The kit reproduces the INT8 model exactly.

## Files

`<example>/`: the run's records (scrubbed by `tools/record_evidence.py`) and `image.json`; `odmr-fcnn/accuracy.json` and `odmr-mlp/accuracy.json`; `replay/<example>/`: the replay records and `image.json`.
