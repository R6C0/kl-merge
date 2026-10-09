// The game side of KLNR (klnr_protocol.h): makes the session, starts klnr.exe, moves one frame per call through it.
// Used by KLGfx inside kl2.exe (32-bit) and by klnr_harness (a stand-in for the game). Windows only, no exceptions.
#pragma once
#include <stdint.h>
#include <string>

#include "klnr_protocol.h"

struct KlnrClientConfig {
    std::string helper;         // path of klnr.exe
    std::string model;          // "" (klnr.exe decides: its model\ folder if present, else none), "none", "zero", a dir
    std::string log;            // klnr.exe's log file ("" = klnr.log beside it)
    uint32_t timeout_ms = 100;  // per frame
    uint32_t max_misses = 30;   // frames in a row without a result (or still busy) before the client gives up
};

struct KlnrParams {
    uint32_t flags = KLNR_F_ENABLED | KLNR_F_TEMPORAL;
    float intensity = 1.0f, local_tone = 1.0f, local_structure = 1.0f, skin_structure = -1.0f;
    float paper_white = 1.0f, color_strength = 1.0f;
    int32_t style = 0;
};

class KlnrClient {
public:
    ~KlnrClient() { stop(); }
    // Makes the session objects for frames up to width x height and starts the helper. False: see error().
    bool start(const KlnrClientConfig &config, uint32_t width, uint32_t height);
    // Ends the helper (and waits for it) and closes the session.
    void stop();
    bool running() const { return ctl_ != nullptr; }
    // The helper finished starting (its device, model and kernels are loaded). Also notices a helper that ended.
    bool ready();
    bool given_up() const { return given_up_; }
    const std::string &error() const { return error_; }
    const KlnrControl *control() const { return ctl_; }
    // A request is still being processed (a late result after a timeout): the buffer must not be touched.
    bool busy() const { return ctl_ && ctl_->done != ctl_->request; }
    // busy() counted as a frame without a result (so a helper that never catches up is given up on); true = skip.
    bool skip_if_busy() { return busy() && !miss("klnr.exe still busy with an earlier frame"); }

    // The buffer to put a frame of width x height (pitch bytes per row) into; grows the frame section when needed.
    // nullptr while busy() (the frame should pass untouched) or on failure (see given_up()).
    uint8_t *frame(uint32_t width, uint32_t height, uint32_t pitch);
    // Sends the frame now in frame() and waits for the result in place. True: the buffer holds the processed frame.
    bool process(const KlnrParams &params);
    // Unmaps this process's view of the frame (address space back while the bridge is switched off); frame() maps
    // it again.
    void release_frame();

    uint32_t frames_ok = 0, frames_missed = 0;
    double last_wait_ms = 0;

private:
    bool make_frame_section(uint32_t capacity);
    bool miss(const char *why);
    KlnrClientConfig config_;
    std::string session_, error_;
    void *control_map_ = nullptr, *frame_map_ = nullptr, *req_ = nullptr, *done_ = nullptr, *process_ = nullptr;
    KlnrControl *ctl_ = nullptr;
    uint8_t *frame_ = nullptr;
    uint32_t capacity_ = 0, misses_in_row_ = 0;
    bool given_up_ = false;
};
