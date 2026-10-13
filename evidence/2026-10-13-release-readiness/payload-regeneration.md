# Payload regeneration against the 2026-10-12 batch inputs (2026-10-13)

Question: does the new `prepare-input` route reproduce the exact int8 payload that the 2026-10-12 64-sample batch sent to the simulator and the kit?

Method: at commit e0d126e, copy `dataset.npz`, `model.tflite`, `model.pt` and `export.manifest.json` from each 2026-10-12 batch run directory into a fresh directory (the originals are not touched), then run:

```sh
python -m pfkit prepare-input <example> --run-dir <copy> --samples 64 --selection first
```

Compare the new `input.int8.bin` with `np.load("evidence/2026-10-12-hardware/batch64/<example>/input.int8.npy").tobytes()` and with the original run's `input.int8.bin`.

| example | bytes | payload sha256 | equal to committed .npy bytes | equal to original .bin |
|---|---|---|---|---|
| signal-freq | 4096 | 56b5c46c63d03e2cb4f69c19c4c5c4a786a662a3f006796de0b56ec83e3a549a | yes | yes |
| odmr-mlp | 6400 | 85f113c7d5d3145634538586f2bf9a1db06eeff7d55b34ced457b4ba82f1b23a | yes | yes |

Scope: host only. This shows the payload contract and selection are byte-identical to the 2026-10-12 inputs. It does not run the simulator or the kit; the 64-sample CLI route on hardware is a separate check.
