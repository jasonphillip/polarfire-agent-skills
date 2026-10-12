# Getting started

1. Install this local clone as a plugin in your agent client. Load `polarfire-bringup` or a named skill.
2. Confirm the tools host has Libero SoC, SmartHLS, and VectorBlox SDK v2.0.3. Confirm the design uses CoreVectorBlox IP v2.0.1.
3. Use a local checkout of the worked source repository. Read its current scripts before running any source command.
4. Check the model graph and TFLite operator list. Use a fixed input shape and INT8 input and output.
5. Compile the TFLite on the tools host. Save byte size, SHA-256, SDK version, and compiler output.
6. Run the SmartHLS testbench. Build and audit the Libero reports. Keep the exact reports.
7. Read the kit IDCODE. Review the job and rollback image before programming.
8. Run the inference smoke on kit Linux. Match its model, image, DMA pool, and input layout.
9. Run the control loop with replayed input. Save output and watchdog status to a report file.
10. Create a demonstrated-state table. Link each row to its raw report.

A programming step changes persistent hardware state. Get operator approval for the exact image first. Stop on a failed check. Do not infer a measured result from an earlier report or from a different board.

The source commands assume a checkout of the source repository. The skill files name their source directly below each command. Replace model filenames only after checking the target script's inputs.

Tutorial: https://github.com/jasonphillip/tychon-quantum-sensing/blob/main/docs/model-to-v250.md

Local source: `docs/model-to-v250.md` in the source checkout.
