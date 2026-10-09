/*
 * KLNR shared-memory protocol between KLGfx (inside kl2.exe, 32-bit) and klnr.exe (64-bit helper).
 * Fixed-size fields only, so the structure has the same layout in both processes.
 *
 * Objects (session = "KLNR_<game pid>", all in the Local\ namespace):
 *   <session>_ctl       file mapping, KLNR_CONTROL_BYTES, this structure (made by KLGfx)
 *   <session>_f<gen>    file mapping, the frame: `capacity` bytes of BGRA8 rows, processed in place (made by KLGfx;
 *                       a bigger frame gets a new generation and klnr.exe maps the new one)
 *   <session>_req       auto-reset event: KLGfx -> klnr.exe, a frame is in the buffer (request = its number)
 *   <session>_done      auto-reset event: klnr.exe -> KLGfx, the result is in the buffer (done = that number)
 *
 * Per frame (KLGfx): copy the frame in, fill the parameters, request++, set _req, wait _done with a timeout,
 * use the buffer only if done == request. klnr.exe ends when the game process ends.
 */
#pragma once
#include <stdint.h>

#define KLNR_MAGIC 0x524e4c4bu /* "KLNR" */
#define KLNR_VERSION 1
#define KLNR_CONTROL_BYTES 4096

enum KlnrState { KLNR_STARTING = 0, KLNR_READY = 1, KLNR_FAILED = 2, KLNR_EXITED = 3 };
enum KlnrModel { KLNR_MODEL_NONE = 0, KLNR_MODEL_ZERO = 1, KLNR_MODEL_DIR = 2 };
enum KlnrFlags {
    KLNR_F_ENABLED = 1,        /* run the network (else the frame only makes the round trip) */
    KLNR_F_RESET_HISTORY = 2,  /* no temporal history for this frame (a cut, a load, a resize) */
    KLNR_F_TEMPORAL = 4,       /* blend with the previous output (the network's own per-pixel weight) */
    KLNR_F_SPLIT = 8,          /* left half untouched, right half processed (A/B view) */
    KLNR_F_TEST = 16           /* right half grey: proves the round trip on screen without a model */
};

typedef struct KlnrControl {
    uint32_t magic, version, game_pid, control_bytes;
    /* the frame section, written by KLGfx */
    volatile uint32_t generation;
    uint32_t capacity, width, height, pitch;
    /* one request, written by KLGfx before it sets _req */
    volatile uint32_t request;
    uint32_t flags;
    float intensity, local_tone, local_structure, skin_structure, paper_white, color_strength;
    int32_t style; /* 0 off, 1 natural, 2 cinematic */
    uint32_t reserved_in[32];
    /* written by klnr.exe */
    volatile uint32_t state; /* KlnrState */
    volatile uint32_t done;
    uint32_t model; /* KlnrModel */
    uint32_t helper_pid;
    float ms_upload, ms_gpu, ms_network, ms_download, ms_total; /* the last frame, inside klnr.exe */
    uint32_t frames;
    uint32_t reserved_out[32];
    char device[128];
    char message[512];
} KlnrControl;

#ifdef __cplusplus
#include <stddef.h>
static_assert(sizeof(KlnrControl) <= KLNR_CONTROL_BYTES, "KlnrControl must fit its section");
/* the same layout in the 32-bit game and the 64-bit helper (checked with both MinGW compilers) */
static_assert(offsetof(KlnrControl, request) == 36 && offsetof(KlnrControl, state) == 200 &&
                  offsetof(KlnrControl, message) == 496 && sizeof(KlnrControl) == 1008,
              "KlnrControl layout changed: both sides must be rebuilt and these numbers updated");
#endif
