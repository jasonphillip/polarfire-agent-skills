/*
 * Standalone Linux inference runner. Runtime and model parser come from the
 * user's VectorBlox SDK checkout; no SDK source is distributed with this file.
 * The preflight is needed because SDK 2.0.3 vbx_cnn_init does not check failed
 * UIO and udmabuf opens before it maps them.
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <limits.h>
#include <pthread.h>
#include <stdint.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
#include "graph_version.h"
#include "vbx_cnn_api.h"

enum { EXIT_USAGE = 2, EXIT_DEVICE = 3, EXIT_TIMEOUT = 4, EXIT_NPU = 5 };
/* SDK driver word indices: vbx_cnn_api.c; VERSION is used by vbx_probe.c. */
enum { CTRL_WORD = 0, VERSION_WORD = 10 };
enum { MAX_REPEAT = 10000 };

typedef struct {
    const char *model_path, *input_path, *output_path, *json_path, *uio_name;
    unsigned timeout_ms, repeat;
} options_t;

typedef struct {
    size_t elements, bytes, offset;
    vbx_cnn_calc_type_e type;
    double scale;
    int zero_point;
    void *dma;
} desc_t;

typedef struct {
    int code, poll_result;
    uint32_t control, version;
    int error;
    size_t nin, nout, samples, repeat, completed;
    desc_t input, outputs[MAX_IO_BUFFERS - 1];
    double *times_ms;
} result_t;

static int parse_positive(const char *s, unsigned max, unsigned *out)
{
    char *end;
    unsigned long value;
    errno = 0;
    value = strtoul(s, &end, 10);
    if (errno || !s[0] || *end || value == 0 || value > max) return -1;
    *out = (unsigned)value;
    return 0;
}

static int parse_args(int argc, char **argv, options_t *o)
{
    memset(o, 0, sizeof(*o));
    o->uio_name = "vbx";
    o->repeat = 1;
    for (int i = 1; i < argc; i++) {
        if (i + 1 >= argc) return -1;
        const char *key = argv[i], *val = argv[++i];
        if (!strcmp(key, "--model")) o->model_path = val;
        else if (!strcmp(key, "--input")) o->input_path = val;
        else if (!strcmp(key, "--output")) o->output_path = val;
        else if (!strcmp(key, "--json")) o->json_path = val;
        else if (!strcmp(key, "--uio-name")) o->uio_name = val;
        else if (!strcmp(key, "--timeout-ms")) {
            if (parse_positive(val, 600000, &o->timeout_ms)) return -1;
        } else if (!strcmp(key, "--repeat")) {
            if (parse_positive(val, MAX_REPEAT, &o->repeat)) return -1;
        } else return -1;
    }
    return (!o->model_path || !o->input_path || !o->output_path || !o->timeout_ms) ? -1 : 0;
}

#ifndef VBX_RUN_FAKE_DRIVER
static int read_text(const char *path, char *buf, size_t cap)
{
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    if (!fgets(buf, (int)cap, f)) { fclose(f); return -1; }
    fclose(f);
    buf[strcspn(buf, "\r\n")] = 0;
    return 0;
}
#endif

static int preflight(const char *name)
{
#ifdef VBX_RUN_FAKE_DRIVER
    (void)name;
    return 0;
#else
    char path[160], value[80];
    int found = 0;
    /* This SDK release searches for the literal name "vbx". */
    if (strcmp(name, "vbx")) {
        fprintf(stderr, "SDK 2.0.3 requires --uio-name vbx\n");
        return -1;
    }
    for (unsigned n = 0; n < 256; n++) {
        snprintf(path, sizeof(path), "/sys/class/uio/uio%u/name", n);
        /* The SDK matches the name prefix (strncmp), so "vbx@60030000" from a generic-uio node also matches. */
        if (read_text(path, value, sizeof(value)) || strncmp(value, name, strlen(name))) continue;
        snprintf(path, sizeof(path), "/sys/class/uio/uio%u/maps/map0/addr", n);
        if (read_text(path, value, sizeof(value)) || strtoull(value, NULL, 0) != 0x60030000ULL) {
            fprintf(stderr, "first vbx UIO has an unexpected control address\n");
            return -1;
        }
        snprintf(path, sizeof(path), "/dev/uio%u", n);
        int fd = open(path, O_RDWR);
        if (fd >= 0) { close(fd); found = 1; }
        break; /* The SDK uses the first name that starts with "vbx". */
    }
    if (!found) { fprintf(stderr, "vbx UIO control page is unavailable\n"); return -1; }
    int dma_fd = open("/dev/udmabuf-ddr-nc0", O_RDWR);
    if (dma_fd >= 0) close(dma_fd);
    if (dma_fd < 0 ||
        read_text("/sys/class/u-dma-buf/udmabuf-ddr-nc0/size", value, sizeof(value)) ||
        strtoull(value, NULL, 10) == 0 ||
        read_text("/sys/class/u-dma-buf/udmabuf-ddr-nc0/phys_addr", value, sizeof(value))) {
        fprintf(stderr, "non-cached udmabuf is unavailable\n");
        return -1;
    }
    return 0;
#endif
}

static int read_binary(const char *path, uint8_t **data, size_t *length)
{
    struct stat st;
    FILE *f;
    if (stat(path, &st) || st.st_size <= 0 || (uintmax_t)st.st_size > SIZE_MAX) return -1;
    *length = (size_t)st.st_size;
    *data = malloc(*length);
    if (!*data) return -1;
    f = fopen(path, "rb");
    if (!f) return -1;
    size_t got = fread(*data, 1, *length, f);
    int extra = fgetc(f);
    fclose(f);
    return (got == *length && extra == EOF) ? 0 : -1;
}

static size_t type_bytes(vbx_cnn_calc_type_e type)
{
    switch (type) {
    case VBX_CNN_CALC_TYPE_UINT8: case VBX_CNN_CALC_TYPE_INT8: return 1;
    case VBX_CNN_CALC_TYPE_INT16: return 2;
    case VBX_CNN_CALC_TYPE_INT32: return 4;
    default: return 0;
    }
}

static const char *type_name(vbx_cnn_calc_type_e type)
{
    switch (type) {
    case VBX_CNN_CALC_TYPE_UINT8: return "uint8";
    case VBX_CNN_CALC_TYPE_INT8: return "int8";
    case VBX_CNN_CALC_TYPE_INT16: return "int16";
    case VBX_CNN_CALC_TYPE_INT32: return "int32";
    default: return "unknown";
    }
}

static double monotonic_ms(void)
{
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts)) return -1;
    return (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / 1000000.0;
}

typedef struct {
    pthread_mutex_t mutex;
    pthread_cond_t cond;
    struct timespec deadline;
    const char *json_path;
    size_t samples;
    atomic_uintptr_t control_registers;
    int stopped;
} watchdog_t;

static int deadline_expired(const watchdog_t *w)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now)) return 1;
    return now.tv_sec > w->deadline.tv_sec ||
           (now.tv_sec == w->deadline.tv_sec && now.tv_nsec >= w->deadline.tv_nsec);
}

static void *watchdog_run(void *arg)
{
    watchdog_t *w = arg;
    pthread_mutex_lock(&w->mutex);
    int status = 0;
    while (!w->stopped && status != ETIMEDOUT)
        status = pthread_cond_timedwait(&w->cond, &w->mutex, &w->deadline);
    if (!w->stopped) {
        volatile uint32_t *registers = (volatile uint32_t *)atomic_load(&w->control_registers);
        uint32_t control = registers ? registers[CTRL_WORD] : 0;
        uint32_t error = registers ? registers[1] : 0;
        if (w->json_path) {
            FILE *f = fopen(w->json_path, "w");
            if (f) {
                fprintf(f, "{\"exit_code\":4,\"control_word\":\"0x%08" PRIx32
                        "\",\"npu_error\":%" PRIu32 ",\"samples\":%zu,\"watchdog\":true}\n",
                        control, error, w->samples);
                fclose(f);
            }
        }
        fprintf(stderr, "NPU operation deadline expired; NPU state is unknown\n");
        _Exit(EXIT_TIMEOUT);
    }
    pthread_mutex_unlock(&w->mutex);
    return NULL;
}

static int watchdog_start(watchdog_t *w, const char *json_path, unsigned timeout_ms, size_t samples,
                          pthread_t *thread)
{
    memset(w, 0, sizeof(*w));
    w->json_path = json_path;
    w->samples = samples;
    atomic_init(&w->control_registers, (uintptr_t)0);
    if (clock_gettime(CLOCK_MONOTONIC, &w->deadline)) return -1;
    w->deadline.tv_sec += timeout_ms / 1000;
    w->deadline.tv_nsec += (long)(timeout_ms % 1000) * 1000000L;
    if (w->deadline.tv_nsec >= 1000000000L) {
        w->deadline.tv_sec++;
        w->deadline.tv_nsec -= 1000000000L;
    }
    pthread_mutex_init(&w->mutex, NULL);
    pthread_condattr_t attr;
    pthread_condattr_init(&attr);
    pthread_condattr_setclock(&attr, CLOCK_MONOTONIC);
    pthread_cond_init(&w->cond, &attr);
    pthread_condattr_destroy(&attr);
    if (pthread_create(thread, NULL, watchdog_run, w)) {
        pthread_cond_destroy(&w->cond);
        pthread_mutex_destroy(&w->mutex);
        return -1;
    }
    return 0;
}

static void watchdog_stop(watchdog_t *w, pthread_t thread)
{
    pthread_mutex_lock(&w->mutex);
    w->stopped = 1;
    pthread_cond_signal(&w->cond);
    pthread_mutex_unlock(&w->mutex);
    pthread_join(thread, NULL);
    pthread_cond_destroy(&w->cond);
    pthread_mutex_destroy(&w->mutex);
}

static int compare_double(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

static void print_desc(FILE *f, const desc_t *d, size_t index)
{
    fprintf(f, "{\"index\":%zu,\"elements\":%zu,\"bytes\":%zu,"
            "\"dtype\":\"%s\",\"scale\":%.9g,\"zero_point\":%d,\"offset\":%zu}",
            index, d->elements, d->bytes, type_name(d->type), d->scale, d->zero_point, d->offset);
}

static int write_json(const char *path, const result_t *r)
{
    FILE *f;
    if (!path) return 0;
    f = fopen(path, "w");
    if (!f) return -1;
    fprintf(f, "{\"exit_code\":%d,\"core_version_word\":\"0x%08" PRIx32
            "\",\"vnnx_graph_version\":\"0x%08x\",\"control_word\":\"0x%08" PRIx32 "\",\"npu_error\":%d,"
            "\"poll_result\":%d,\"input_count\":%zu,\"output_count\":%zu,"
            "\"samples\":%zu,\"completed\":%zu,\"inputs\":[", r->code, r->version, VNNX_GRAPH_VERSION, r->control,
            r->error, r->poll_result, r->nin, r->nout, r->samples, r->completed);
    if (r->nin) print_desc(f, &r->input, 0);
    fputs("],\"outputs\":[", f);
    for (size_t i = 0; i < r->nout; i++) {
        if (i) fputc(',', f);
        print_desc(f, &r->outputs[i], i);
    }
    fputs("],\"wall_ms\":[", f);
    for (size_t i = 0; i < r->completed; i++)
        fprintf(f, "%s%.6f", i ? "," : "", r->times_ms[i]);
    fputs("],\"sample_wall_ms\":[", f);
    for (size_t sample = 0; sample < r->samples; sample++) {
        if (sample) fputc(',', f);
        fputc('[', f);
        for (size_t run = 0; run < r->repeat && sample * r->repeat + run < r->completed; run++)
            fprintf(f, "%s%.6f", run ? "," : "", r->times_ms[sample * r->repeat + run]);
        fputc(']', f);
    }
    fputs("],\"wall_ms_min\":", f);
    if (r->completed) {
        double *sorted = malloc(r->completed * sizeof(*sorted));
        if (!sorted) { fclose(f); return -1; }
        memcpy(sorted, r->times_ms, r->completed * sizeof(*sorted));
        qsort(sorted, r->completed, sizeof(*sorted), compare_double);
        fprintf(f, "%.6f,\"wall_ms_median\":%.6f,\"wall_ms_max\":%.6f",
                sorted[0], (sorted[(r->completed - 1) / 2] + sorted[r->completed / 2]) / 2.0,
                sorted[r->completed - 1]);
        free(sorted);
    } else fputs("null,\"wall_ms_median\":null,\"wall_ms_max\":null", f);
    fputs("}\n", f);
    int bad = ferror(f);
    if (fclose(f)) bad = 1;
    return bad ? -1 : 0;
}

int main(int argc, char **argv)
{
    options_t o;
    result_t r = {0};
    vbx_cnn_t *vbx = NULL;
    model_t *model = NULL;
    uint8_t *host_model = NULL, *host_input = NULL;
    size_t model_size = 0, input_size = 0;
    size_t allocation = 0, total_output = 0;
    vbx_cnn_io_ptr_t io[MAX_IO_BUFFERS] = {0};
    watchdog_t watchdog;
    pthread_t watchdog_thread;
    int watchdog_started = 0;
    if (parse_args(argc, argv, &o)) {
        fprintf(stderr, "usage: vbx_run --model m.vnnx --input in.bin --output out.bin "
                "--timeout-ms N [--json meta.json] [--uio-name vbx] [--repeat K]\n");
        return EXIT_USAGE;
    }
    r.repeat = o.repeat;
    /* SDK init maps UIO and DMA memory, clears DMA memory, then writes SOFT_RESET
     * and zero to the control register (vbx_cnn_api.c). Validate file data first. */
    r.code = EXIT_DEVICE;
    if (read_binary(o.model_path, &host_model, &model_size) || model_size < sizeof(vnnx_graph_t)) {
        fprintf(stderr, "model read failed\n"); goto done;
    }
    model_t *parsed = (model_t *)host_model;
    r.code = EXIT_USAGE;
    if (model_check_sanity(parsed) || model_get_data_bytes(parsed) != model_size ||
        model_get_allocate_bytes(parsed) < model_size) {
        fprintf(stderr, "invalid model\n"); goto done;
    }
    if (model_get_size_conf(parsed) != VBX_CNN_SIZE_CONF_V250 ||
        model_get_num_inputs(parsed) != 1 || model_get_num_outputs(parsed) == 0 ||
        model_get_num_outputs(parsed) > MAX_IO_BUFFERS - 1) {
        fprintf(stderr, "unsupported model size or IO count\n");
        goto done;
    }
    allocation = model_get_allocate_bytes(parsed);
    r.nin = 1;
    r.nout = model_get_num_outputs(parsed);
    r.input.type = model_get_input_datatype(parsed, 0);
    r.input.elements = model_get_input_length(parsed, 0);
    r.input.scale = model_get_input_scale_value(parsed, 0);
    r.input.zero_point = model_get_input_zeropoint(parsed, 0);
    size_t width = type_bytes(r.input.type);
    if (!width || !r.input.elements || r.input.elements > SIZE_MAX / width) {
        fprintf(stderr, "invalid input descriptor\n"); goto done;
    }
    r.input.bytes = r.input.elements * width;
    for (size_t i = 0; i < r.nout; i++) {
        desc_t *d = &r.outputs[i];
        d->elements = model_get_output_length(parsed, (int)i);
        d->type = model_get_output_datatype(parsed, (int)i);
        d->scale = model_get_output_scale_value(parsed, (int)i);
        d->zero_point = model_get_output_zeropoint(parsed, (int)i);
        if (d->type != VBX_CNN_CALC_TYPE_INT8 || !d->elements ||
            d->elements > SIZE_MAX - total_output) {
            fprintf(stderr, "output must be valid int8\n"); r.code = EXIT_USAGE; goto done;
        }
        d->bytes = d->elements;
        d->offset = total_output;
        total_output += d->bytes;
    }
    r.code = EXIT_USAGE;
    struct stat input_stat;
    if (stat(o.input_path, &input_stat) || input_stat.st_size < 0 ||
        (uintmax_t)input_stat.st_size > SIZE_MAX) {
        fprintf(stderr, "input read failed\n"); goto done;
    }
    input_size = (size_t)input_stat.st_size;
    if (!input_size || input_size % r.input.bytes) {
        fprintf(stderr, "input size mismatch: got %zu bytes, expected a multiple of %zu bytes\n",
                input_size, r.input.bytes);
        goto done;
    }
    if (read_binary(o.input_path, &host_input, &input_size)) {
        fprintf(stderr, "input read failed\n"); goto done;
    }
    r.samples = input_size / r.input.bytes;
    if (r.samples > SIZE_MAX / o.repeat ||
        r.samples * o.repeat > SIZE_MAX / sizeof(*r.times_ms)) {
        fprintf(stderr, "sample/repeat count overflow\n"); goto done;
    }
    r.times_ms = calloc(r.samples * o.repeat, sizeof(*r.times_ms));
    if (!r.times_ms) { r.code = EXIT_DEVICE; goto done; }
    r.code = EXIT_DEVICE;
    if (preflight(o.uio_name)) goto done;
    if (watchdog_start(&watchdog, o.json_path, o.timeout_ms, r.samples, &watchdog_thread)) {
        fprintf(stderr, "watchdog initialization failed\n"); goto done;
    }
    watchdog_started = 1;
    vbx = vbx_cnn_init(NULL);
    if (deadline_expired(&watchdog)) { r.code = EXIT_TIMEOUT; goto done; }
    if (!vbx || !vbx->initialized || !vbx->ctrl_reg || !vbx->io_buffers) {
        fprintf(stderr, "SDK device initialization failed\n"); goto done;
    }
    atomic_store(&watchdog.control_registers, (uintptr_t)vbx->ctrl_reg);
    r.version = vbx->ctrl_reg[VERSION_WORD];
    model = vbx_allocate_dma_buffer(vbx, allocation, 0);
    if (deadline_expired(&watchdog)) { r.code = EXIT_TIMEOUT; goto done; }
    if (!model) { fprintf(stderr, "model DMA allocation failed\n"); goto done; }
    memcpy(model, host_model, model_size);
    if (deadline_expired(&watchdog)) { r.code = EXIT_TIMEOUT; goto done; }
    r.input.dma = vbx_allocate_dma_buffer(vbx, r.input.bytes, 0);
    if (deadline_expired(&watchdog)) { r.code = EXIT_TIMEOUT; goto done; }
    if (!r.input.dma) { fprintf(stderr, "input DMA allocation failed\n"); goto done; }
    io[0] = (vbx_cnn_io_ptr_t)(uintptr_t)r.input.dma;
    for (size_t i = 0; i < r.nout; i++) {
        desc_t *d = &r.outputs[i];
        d->dma = vbx_allocate_dma_buffer(vbx, d->bytes, 0);
        if (deadline_expired(&watchdog)) { r.code = EXIT_TIMEOUT; goto done; }
        if (!d->dma) { fprintf(stderr, "output DMA allocation failed\n"); goto done; }
        io[1 + i] = (vbx_cnn_io_ptr_t)(uintptr_t)d->dma;
    }
    FILE *output = fopen(o.output_path, "wb");
    if (!output) { perror("output"); goto done; }
    for (size_t sample = 0; sample < r.samples; sample++) {
      memcpy(r.input.dma, host_input + sample * r.input.bytes, r.input.bytes);
      if (deadline_expired(&watchdog)) { r.code = EXIT_TIMEOUT; break; }
      for (unsigned run = 0; run < o.repeat; run++) {
        double begin = monotonic_ms();
        if (begin < 0) { r.code = EXIT_DEVICE; break; }
        if (deadline_expired(&watchdog)) { r.code = EXIT_TIMEOUT; break; }
        r.code = EXIT_NPU;
        if (vbx_cnn_get_state(vbx) != READY) {
            fprintf(stderr, "NPU is not ready\n"); break;
        }
        if (deadline_expired(&watchdog)) { r.code = EXIT_TIMEOUT; break; }
        if (vbx_cnn_model_start(vbx, model, io)) {
            fprintf(stderr, "NPU refused model start\n"); break;
        }
        if (deadline_expired(&watchdog)) { r.code = EXIT_TIMEOUT; break; }
        for (;;) {
            r.poll_result = vbx_cnn_model_poll(vbx);
            r.error = (int)vbx_cnn_get_error_val(vbx);
            if (deadline_expired(&watchdog)) { r.code = EXIT_TIMEOUT; break; }
            if (r.error || r.poll_result < 0) {
                fprintf(stderr, "NPU error: poll=%d error=%d\n", r.poll_result, r.error);
                break;
            }
            double elapsed = monotonic_ms() - begin;
            if (elapsed < 0) { r.code = EXIT_DEVICE; break; }
            if (r.poll_result == 0) {
                r.times_ms[r.completed++] = elapsed;
                r.code = 0;
                break;
            }
        }
        if (r.code) break;
      }
      if (r.code) break;
      for (size_t i = 0; i < r.nout; i++) {
          desc_t *d = &r.outputs[i];
          if (fwrite(d->dma, 1, d->bytes, output) != d->bytes) r.code = EXIT_DEVICE;
      }
      if (r.code || deadline_expired(&watchdog)) {
          if (!r.code) r.code = EXIT_TIMEOUT;
          break;
      }
    }
    if (fclose(output)) r.code = EXIT_DEVICE;
    if (deadline_expired(&watchdog)) r.code = EXIT_TIMEOUT;
done:
    if (watchdog_started) watchdog_stop(&watchdog, watchdog_thread);
    if (vbx && vbx->ctrl_reg) {
        r.control = vbx->ctrl_reg[CTRL_WORD];
        r.error = (int)vbx_cnn_get_error_val(vbx);
    }
    if (write_json(o.json_path, &r)) {
        fprintf(stderr, "metadata write failed\n");
        if (!r.code) r.code = EXIT_DEVICE;
    }
    free(r.times_ms);
    free(host_model);
    free(host_input);
    return r.code;
}
