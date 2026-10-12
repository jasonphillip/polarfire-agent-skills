# Kit reference-design build, 2026-10-12 (executed on the tools host, Libero SoC 2025.2)

Command (from the kit root copied to the tools host): `WORK_DIR=<work> LIBERO=<libero.exe> bash hw/build_reference_design.sh` with defaults DEVICE=MPFS250T, VBX_SIZE=V250, CORE_VERSION=2.0.1, PIN_VLNV=Actel:DirectCore:COREAXI4INTERCONNECT=2.9.100 (kit commit bb493d2).

- First attempt (no pin map): failed in 18 s; the unpinned COREAXI4INTERCONNECT resolved to 3.0.130 and the v2026.04 component script failed with 'Parameter DWC_ADDR_FIFO_DEPTH_CEILING not found'.
- Second attempt (pin map): script exit 0 after 40 min 25 s; synthesis, place-and-route, the reference design's own seed sweep (iteration 1 of up to 20 met timing: 0 violations, worst slack 1.049 ns), timing verification and bitstream export.
- Generated CoreVectorBlox component (core_vectorblox_C0.cxf): version 2.0.1, PRESET 0 (V250); vectorblox_axi_resize ID_WIDTH:4.
- Programming job: Vectorblox_FD0AEBB95776A726D3D.job, 12,127,080 bytes, sha256 6d5cae6c30053ed5d16325f9cc03e57eb706e6ab3f3f9306d741cad02d711c6c (kept on the tools host; not committed: it carries Microchip IP bitstreams). Bitstream digests from the log: fabric c4307ea9..., sNVM 49d5c5c9..., entire 48a03a99.... eNVM: not generated (no configuration file), a warning in the reference flow.
- Post-synthesis resources (compile_netlist_resources.rpt): 4LUT 61,659 of 254,196 (24.3 %), DFF 61,744 (24.3 %), uSRAM 381 of 2,352, LSRAM 119 of 812, Math 84 of 784.
- The kit was NOT programmed with this image; the board keeps the case study's image. Programming is a separate approval.

Files here: libero.log (paths replaced), compile_netlist_resources.rpt, iteration_summary.rpt, max_timing_multi_corner.xml, max_timing_violations_multi_corner.xml.
