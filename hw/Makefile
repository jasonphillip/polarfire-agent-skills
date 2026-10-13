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
PYTHON ?= $(ROOT_DIR)/.venv/bin/python
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

test:
	@$(NATIVE_CC) $(FLAGS) -Werror -DVBX_RUN_FAKE_DRIVER=1 $(THIS_DIR)/vbx_run.c $(THIS_DIR)/tests/fake_vbx_cnn_api.c -o $(THIS_DIR)/tests/vbx_run.fake $(LIBS)
	@$(PYTHON) $(THIS_DIR)/tests/test_fake_driver.py $(THIS_DIR)/tests/vbx_run.fake

clean:
	rm -f vbx_run vbx_run.native tests/vbx_run.fake

.PHONY: all native clean test
