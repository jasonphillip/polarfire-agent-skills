# Build on the tools host with SmartHLS's glibc RISC-V GCC.
# NOTICE: Build flags and SDK-by-path linkage follow the Apache-2.0 case study:
# deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/firmware/linux/Makefile.
# Its GCC is a Cygwin build. Put both directories on PATH before make:
# SHLS=<SmartHLS installation>
# export PATH="$SHLS/swtools/binutils/riscv-gnu-toolchain/bin:$SHLS/dependencies/lib/cygwin:$PATH"
# make -C hw CROSS=riscv64-unknown-linux-gnu- VBX_SDK=<absolute SDK path>

CROSS ?= riscv64-unknown-linux-gnu-
CC := $(CROSS)gcc
NATIVE_CC ?= gcc
THIS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
ROOT_DIR := $(abspath $(THIS_DIR)/..)
VBX_SDK ?= $(ROOT_DIR)/deps/vectorblox-sdk
VBX_DRV := $(VBX_SDK)/drivers/vectorblox
VBX_RT := $(VBX_DRV)/vbx_cnn_api.c $(VBX_DRV)/vbx_cnn_model.c
CFLAGS ?= -O2
FLAGS := $(CFLAGS) -std=c11 -Wall -Wextra -DVBX_SOC_DRIVER -DMSS_DDR -DUSE_INTERRUPTS=0 -I$(VBX_DRV)
LIBS := -lm -lpthread

all: vbx_run

vbx_run: $(THIS_DIR)/vbx_run.c $(VBX_RT)
	$(CC) $(FLAGS) $^ -o $(THIS_DIR)/$@ $(LIBS)

native: $(THIS_DIR)/vbx_run.c $(VBX_RT)
	$(NATIVE_CC) $(FLAGS) $^ -o $(THIS_DIR)/vbx_run.native $(LIBS)

clean:
	rm -f vbx_run vbx_run.native

.PHONY: all native clean
