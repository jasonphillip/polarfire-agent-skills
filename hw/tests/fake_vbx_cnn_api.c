#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "graph_version.h"
#include "vbx_cnn_api.h"

#ifndef VBX_RUN_FAKE_DRIVER
#error Fake driver must be built with VBX_RUN_FAKE_DRIVER=1
#endif

static volatile uint32_t registers[16];
static const char *scenario(void)
{
    const char *value = getenv("VBX_RUN_SCENARIO");
    return value ? value : "ok";
}

vbx_cnn_t *vbx_cnn_init(void *address)
{
    (void)address;
    if (!strcmp(scenario(), "init_fails")) return NULL;
    vbx_cnn_t *vbx = calloc(1, sizeof(*vbx));
    if (!vbx) return NULL;
    registers[0] = registers[1] = 0;
    registers[10] = 0x20000000;
    vbx->ctrl_reg = registers;
    vbx->initialized = 1;
    vbx->io_buffers = calloc(MAX_IO_BUFFERS, sizeof(*vbx->io_buffers));
    return vbx;
}

void *vbx_allocate_dma_buffer(vbx_cnn_t *vbx, size_t size, size_t alignment)
{
    (void)vbx;
    (void)alignment;
    return calloc(1, size);
}

vbx_cnn_state_e vbx_cnn_get_state(vbx_cnn_t *vbx)
{
    (void)vbx;
    return READY;
}

int vbx_cnn_model_start(vbx_cnn_t *vbx, model_t *model, vbx_cnn_io_ptr_t io[])
{
    (void)vbx;
    (void)model;
    if (!strcmp(scenario(), "start_blocks")) {
        struct timespec pause = {0, 100000000};
        for (;;) nanosleep(&pause, NULL);
    }
    const int8_t *input = (const int8_t *)(uintptr_t)io[0];
    int8_t *output = (int8_t *)(uintptr_t)io[1];
    for (int i = 0; i < 4; i++) output[i] = (int8_t)(input[i] + 1);
    registers[0] = 2;
    return 0;
}

int vbx_cnn_model_poll(vbx_cnn_t *vbx)
{
    (void)vbx;
    if (!strcmp(scenario(), "error_register")) {
        registers[1] = 9;
        return -1;
    }
    if (!strcmp(scenario(), "never_completes")) return 1;
    registers[0] = 8;
    return 0;
}

vbx_cnn_err_e vbx_cnn_get_error_val(vbx_cnn_t *vbx)
{
    (void)vbx;
    return (vbx_cnn_err_e)registers[1];
}

int model_check_sanity(const model_t *model)
{
    const vnnx_graph_t *g = (const vnnx_graph_t *)model;
    return g->magic == 0x1ABE11ED && g->version == VNNX_GRAPH_VERSION ? 0 : -1;
}
size_t model_get_data_bytes(const model_t *m) { return ((const vnnx_graph_t *)m)->data_bytes; }
size_t model_get_allocate_bytes(const model_t *m) { return ((const vnnx_graph_t *)m)->allocate_bytes; }
vbx_cnn_size_conf_e model_get_size_conf(const model_t *m) { return (vbx_cnn_size_conf_e)((const vnnx_graph_t *)m)->vbx_nn_preset; }
size_t model_get_num_inputs(const model_t *m) { return ((const vnnx_graph_t *)m)->num_inputs; }
size_t model_get_num_outputs(const model_t *m) { return ((const vnnx_graph_t *)m)->num_outputs; }
vbx_cnn_calc_type_e model_get_input_datatype(const model_t *m, int i) { (void)m; (void)i; return VBX_CNN_CALC_TYPE_INT8; }
vbx_cnn_calc_type_e model_get_output_datatype(const model_t *m, int i) { (void)m; (void)i; return VBX_CNN_CALC_TYPE_INT8; }
size_t model_get_input_length(const model_t *m, int i) { (void)m; (void)i; return 4; }
size_t model_get_output_length(const model_t *m, int i) { (void)m; (void)i; return 4; }
float model_get_input_scale_value(const model_t *m, int i) { (void)m; (void)i; return 1.0f; }
float model_get_output_scale_value(const model_t *m, int i) { (void)m; (void)i; return 1.0f; }
int model_get_input_zeropoint(const model_t *m, int i) { (void)m; (void)i; return 0; }
int model_get_output_zeropoint(const model_t *m, int i) { (void)m; (void)i; return 0; }
