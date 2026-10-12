# FAQ

## Why use VectorBlox SDK v2.0.3 with CoreVectorBlox IP v2.0.1?

That is the paired tool and IP combination in the worked source. A different SDK can change compile output or runtime compatibility. Record both versions and stop on mismatch.

## Why does a FLOAT32 model fail?

The deployed path compiles a fully INT8 TFLite model. Check input and output dtypes, static shapes, and all operations. The source guard rejects dynamic-shape operations including SHAPE, STRIDED_SLICE, and PACK.

## Which fixed-point type does SmartHLS use?

Use `hls::ap_fixpt<W,I>`. The source testbench and HLS code use that type. Check width and overflow behavior in simulation before synthesis.

## How does headless Tcl work?

Libero accepts a `SCRIPT:` argument. The source has an ordered console flow and separate headless closure scripts. Review project paths and report destinations in each Tcl file before running it. Stage 05 needs a placed design and valid VCD.

## Does a watchdog trip prove actuator fallback?

No. Record both the timeout edge and the next controller output. The source design needs a controller start to compute a new output. A stopped process can leave the last actuator value in place.
