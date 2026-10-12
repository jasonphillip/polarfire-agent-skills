# Probe C8: FULLY_CONNECTED chains in SDK 2.0.3 simulator (tools host, 2026-10-12)

Variants built with TensorFlow 2.15.1 (INT8 PTQ, batch 1, same random weights), compiled with vnnx_compile -c V250 (release-v2.0.3), run with vbx.sim.Model on the same int8 inputs as tf.lite.Interpreter. Scripts: make_variants*.py, sim_variants*.sh (in this folder).

```
c8-results.log: A_2d vnnx input_shape [[1, 64]] dtypes [dtype('int8')] out shape [[1, 1]] in scale/zp [0.007840954698622227] [0]
c8-results.log:   asis: sim_raw=[-128, -128, -128, -128] tflite_raw=[43, 5, 6, -60] maxdiff=171
c8-results.log:   nchw: sim_raw=[-128, -128, -128, -128] tflite_raw=[43, 5, 6, -60] maxdiff=171
c8-results.log: B_4d_dense vnnx input_shape [[1, 64, 1, 1]] dtypes [dtype('int8')] out shape [[1, 1, 1, 1]] in scale/zp [0.007840954698622227] [0]
c8-results.log:   asis: sim_raw=[-128, -128, -128, -128] tflite_raw=[43, 5, 6, -60] maxdiff=171
c8-results.log:   nchw: sim_raw=[-128, -128, -128, -128] tflite_raw=[43, 5, 6, -60] maxdiff=171
c8-results.log: C_4d_reshape vnnx input_shape [[1, 64, 1, 1]] dtypes [dtype('int8')] out shape [[1, 1]] in scale/zp [0.007840954698622227] [0]
c8-results.log:   asis: sim_raw=[-128, -128, -128, -128] tflite_raw=[43, 5, 6, -60] maxdiff=171
c8-results.log:   nchw: sim_raw=[-128, -128, -128, -128] tflite_raw=[43, 5, 6, -60] maxdiff=171
c9-results.log: D_conv1x1 compile_exit=0
c9-results.log:   D_conv1x1 vnnx in [[1, 64, 1, 1]] out [[1, 1, 1, 1]]
c9-results.log:    sim_raw(first vals) [[44], [7], [7], [-61]]
c9-results.log:    tflite_raw(first vals) [[44], [7], [7], [-61]]
c9-results.log:    maxdiff 0
c9-results.log: E_single_dense compile_exit=0
c9-results.log:   E_single_dense vnnx in [[1, 64]] out [[1, 1]]
c9-results.log:    sim_raw(first vals) [[-40], [-31], [-72], [-4]]
c9-results.log:    tflite_raw(first vals) [[-40], [-31], [-72], [-4]]
c9-results.log:    maxdiff 0
c9-results.log: F_dense_relu compile_exit=0
c9-results.log:   F_dense_relu vnnx in [[1, 64]] out [[1, 32]]
c9-results.log:    sim_raw(first vals) [[-128, -69, -77], [-128, -75, -128], [-128, -67, -45], [-128, -86, -123]]
c9-results.log:    tflite_raw(first vals) [[-128, -69, -77], [-128, -75, -128], [-128, -67, -45], [-128, -86, -123]]
c9-results.log:    maxdiff 0
c9-results.log: == SDK own embedded-input check on A_2d
c9-results.log: A_i compile_exit=0
c9-results.log: input array 0 doesn't match ([ 1 64] != (4, 64))
c9-results.log: DATA_BYTES = 0.01 MB
c9-results.log: ALLOCATE_BYTES = 0.01 MB
c9-results.log: DMA_BYTES = 73
c9-results.log: INSTR_CYCLES = 6
c9-results.log: CHECKSUM = 00000000
c10-results.log: G_fc_relu_fc compile_exit=0
c10-results.log:   G_fc_relu_fc vnnx in [[1, 64]] out [[1, 1]]
c10-results.log:    sim_raw(first vals) [[-128], [-128], [-128], [-128]]
c10-results.log:    tflite_raw(first vals) [[-8], [7], [-90], [-3]]
c10-results.log:    maxdiff 135
c10-results.log: H_fc_fc compile_exit=0
c10-results.log:   H_fc_fc vnnx in [[1, 64]] out [[1, 1]]
c10-results.log:    sim_raw(first vals) [[23], [0], [-68], [45]]
c10-results.log:    tflite_raw(first vals) [[23], [0], [-68], [45]]
c10-results.log:    maxdiff 0
```

Reading: A_2d, B_4d_dense, C_4d_reshape (three Dense layers, fused ReLU on the first two) and G_fc_relu_fc return a constant -128 in the simulator. E_single_dense, F_dense_relu (single layer, ReLU on the output layer) and H_fc_fc (two Dense, no activation) match TFLite exactly. D_conv1x1 (the same three-layer network as 1x1 Conv2D with fused ReLU) matches exactly. Conclusion: a FULLY_CONNECTED with a fused activation whose output feeds another layer is mishandled in SDK 2.0.3's compiler or simulator; the 1x1-convolution form is correct and is the form the case study ran on hardware.
