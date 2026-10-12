# Clean-checkout validation, 2026-10-12

| host | python | make env | quick start | pytest | note |
|---|---|---|---|---|---|
| Linux aarch64 (DGX Spark), kit commit 2441511 | 3.11.17 | exit 0, 33 s | exit 0, CONV_2D x3 + RESHAPE, no blocking flag | 10 passed | negatives: SHAPE model exit 1, PACK model exit 1, missing SDK table named with the fix |
| macOS 27.0.1 arm64 (MacBook Air M4), kit commit 313411c | 3.11.14 (Homebrew) | FAILED: torch==2.11.0+cpu has no macOS wheel | not run | not run | fixed in c28adbe |
| macOS 27.0.1 arm64, kit commit c28adbe | 3.11.14 (Homebrew) | exit 0 | exit 0, same ops and flags | 9 passed, 1 failed | odmr-mlp test needs Tk (simos imports tkinter); signal-freq unaffected |
| macOS 27.0.1 arm64, kit commit af9f4d5 plus python-tk@3.11 from Homebrew | 3.11.14 (Homebrew) | reused | odmr-mlp through inspect exit 0 | 11 passed | Tk requirement confirmed and resolved; log macos-arm64-run3-tk.txt |

Logs in this folder: linux-aarch64.txt, macos-arm64-run1.txt (first macOS run), macos-arm64-run2.txt (second macOS run). Paths and user names replaced with placeholders.
