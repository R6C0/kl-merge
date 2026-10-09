// See klnr_client.h.
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <stdio.h>
#include <string.h>

#include "klnr_client.h"

static std::string last_error(const char *what)
{
    char b[160];
    snprintf(b, sizeof b, "%s (error %lu)", what, GetLastError());
    return b;
}

bool KlnrClient::make_frame_section(uint32_t capacity)
{
    if (frame_) UnmapViewOfFile(frame_);
    if (frame_map_) CloseHandle(frame_map_);
    frame_ = nullptr;
    frame_map_ = nullptr;
    capacity_ = 0;
    const uint32_t generation = ctl_->generation + 1;
    char name[96];
    snprintf(name, sizeof name, "Local\\%s_f%u", session_.c_str(), generation);
    frame_map_ = CreateFileMappingA(INVALID_HANDLE_VALUE, nullptr, PAGE_READWRITE, 0, capacity, name);
    if (!frame_map_) { error_ = last_error("CreateFileMapping (frame)"); return false; }
    frame_ = (uint8_t *)MapViewOfFile(frame_map_, FILE_MAP_ALL_ACCESS, 0, 0, capacity);
    if (!frame_) { error_ = last_error("MapViewOfFile (frame)"); return false; }
    capacity_ = capacity;
    ctl_->capacity = capacity;
    MemoryBarrier();
    ctl_->generation = generation;
    return true;
}

bool KlnrClient::start(const KlnrClientConfig &config, uint32_t width, uint32_t height)
{
    stop();
    config_ = config;
    given_up_ = false;
    misses_in_row_ = 0;
    char b[64];
    snprintf(b, sizeof b, "KLNR_%lu", GetCurrentProcessId());
    session_ = b;
    const std::string prefix = "Local\\" + session_;
    control_map_ = CreateFileMappingA(INVALID_HANDLE_VALUE, nullptr, PAGE_READWRITE, 0, KLNR_CONTROL_BYTES, (prefix + "_ctl").c_str());
    if (!control_map_) { error_ = last_error("CreateFileMapping (control)"); stop(); return false; }
    ctl_ = (KlnrControl *)MapViewOfFile(control_map_, FILE_MAP_ALL_ACCESS, 0, 0, KLNR_CONTROL_BYTES);
    if (!ctl_) { error_ = last_error("MapViewOfFile (control)"); stop(); return false; }
    memset(ctl_, 0, KLNR_CONTROL_BYTES);
    ctl_->magic = KLNR_MAGIC;
    ctl_->version = KLNR_VERSION;
    ctl_->game_pid = GetCurrentProcessId();
    ctl_->control_bytes = KLNR_CONTROL_BYTES;
    ctl_->width = width;
    ctl_->height = height;
    ctl_->pitch = width * 4;
    ctl_->state = KLNR_STARTING;
    req_ = CreateEventA(nullptr, FALSE, FALSE, (prefix + "_req").c_str());
    done_ = CreateEventA(nullptr, FALSE, FALSE, (prefix + "_done").c_str());
    if (!req_ || !done_) { error_ = last_error("CreateEvent"); stop(); return false; }
    if (!make_frame_section(width * height * 4)) { stop(); return false; }

    std::string cmd = "\"" + config_.helper + "\" --session " + session_;
    if (!config_.model.empty()) cmd += " --model \"" + config_.model + "\"";
    if (!config_.log.empty()) cmd += " --log \"" + config_.log + "\"";
    std::string dir = config_.helper;
    size_t slash = dir.find_last_of("\\/");
    dir = slash == std::string::npos ? std::string(".") : dir.substr(0, slash);
    STARTUPINFOA si = {};
    si.cb = sizeof si;
    PROCESS_INFORMATION pi = {};
    std::string mutable_cmd = cmd;
    if (!CreateProcessA(config_.helper.c_str(), &mutable_cmd[0], nullptr, nullptr, FALSE, CREATE_NO_WINDOW, nullptr, dir.c_str(),
                        &si, &pi)) {
        error_ = last_error(("cannot start " + config_.helper).c_str());
        stop();
        return false;
    }
    CloseHandle(pi.hThread);
    process_ = pi.hProcess;
    error_.clear();
    return true;
}

void KlnrClient::stop()
{
    if (process_) {
        // the helper ends by itself when this process ends; when the session ends earlier, it is told so this way
        if (WaitForSingleObject(process_, 0) == WAIT_TIMEOUT) TerminateProcess(process_, 0);
        CloseHandle(process_);
    }
    if (frame_) UnmapViewOfFile(frame_);
    if (frame_map_) CloseHandle(frame_map_);
    if (ctl_) UnmapViewOfFile(ctl_);
    for (void *h : {control_map_, req_, done_})
        if (h) CloseHandle(h);
    process_ = frame_map_ = control_map_ = req_ = done_ = nullptr;
    frame_ = nullptr;
    ctl_ = nullptr;
    capacity_ = 0;
}

bool KlnrClient::ready()
{
    if (!ctl_ || given_up_)
        return false;
    if (process_ && WaitForSingleObject(process_, 0) == WAIT_OBJECT_0) {
        DWORD code = 0;
        GetExitCodeProcess(process_, &code);
        char b[700];
        snprintf(b, sizeof b, "klnr.exe ended (exit code %lu)%s%s", code, ctl_->message[0] ? ": " : "", ctl_->message);
        error_ = b;
        given_up_ = true;
        return false;
    }
    if (ctl_->state == KLNR_FAILED) {
        error_ = std::string("klnr.exe failed: ") + ctl_->message;
        given_up_ = true;
        return false;
    }
    return ctl_->state == KLNR_READY;
}

uint8_t *KlnrClient::frame(uint32_t width, uint32_t height, uint32_t pitch)
{
    if (!ctl_ || given_up_)
        return nullptr;
    const uint64_t need = (uint64_t)pitch * height;
    if (need > 0x7fffffffu || pitch < width * 4)
        return nullptr;
    if (need > capacity_ && !make_frame_section((uint32_t)need)) {
        given_up_ = true;
        return nullptr;
    }
    ctl_->width = width;
    ctl_->height = height;
    ctl_->pitch = pitch;
    return frame_;
}

bool KlnrClient::process(const KlnrParams &p)
{
    if (!ready())
        return false;
    ctl_->flags = p.flags;
    ctl_->intensity = p.intensity;
    ctl_->local_tone = p.local_tone;
    ctl_->local_structure = p.local_structure;
    ctl_->skin_structure = p.skin_structure;
    ctl_->paper_white = p.paper_white;
    ctl_->color_strength = p.color_strength;
    ctl_->style = p.style;
    const uint32_t request = ctl_->request + 1;
    MemoryBarrier();
    ctl_->request = request;
    SetEvent(req_);
    LARGE_INTEGER f, t0, t1;
    QueryPerformanceFrequency(&f);
    QueryPerformanceCounter(&t0);
    const DWORD start = GetTickCount();
    bool ok = false;
    for (;;) {
        const DWORD spent = GetTickCount() - start;
        if (spent >= config_.timeout_ms)
            break;
        if (WaitForSingleObject(done_, config_.timeout_ms - spent) != WAIT_OBJECT_0)
            break;
        MemoryBarrier();
        if (ctl_->done == request) { ok = true; break; }   // an older, late result signals too: wait on
        if (ctl_->state == KLNR_FAILED) break;
    }
    QueryPerformanceCounter(&t1);
    last_wait_ms = (double)(t1.QuadPart - t0.QuadPart) * 1000.0 / (double)f.QuadPart;
    if (ok) {
        frames_ok++;
        misses_in_row_ = 0;
        return true;
    }
    frames_missed++;
    if (++misses_in_row_ >= config_.max_misses) {
        char b[160];
        snprintf(b, sizeof b, "no result for %u frames in a row (timeout %u ms): switched off for this session", misses_in_row_,
                 config_.timeout_ms);
        error_ = b;
        given_up_ = true;
    }
    return false;
}
