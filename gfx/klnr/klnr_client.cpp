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

// kl2.exe is not large-address-aware and its biggest allocations (whole scene files) come from the bottom of its 2 GB:
// the frame view goes to the top of the address space instead, where it splits no large free block.
static void *map_high(HANDLE map, size_t size)
{
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    const uintptr_t gran = si.dwAllocationGranularity;
    uintptr_t p = (uintptr_t)si.lpMinimumApplicationAddress, best = 0;
    const uintptr_t top = (uintptr_t)si.lpMaximumApplicationAddress;
    MEMORY_BASIC_INFORMATION mbi;
    while (p < top && VirtualQuery((void *)p, &mbi, sizeof mbi)) {
        uintptr_t base = (uintptr_t)mbi.BaseAddress, end = base + mbi.RegionSize;
        if (mbi.State == MEM_FREE && end > base + size) {
            uintptr_t at = (end - size) & ~(gran - 1);   // the top of this free block, on an allocation boundary
            if (at >= base && at > best)
                best = at;
        }
        if (end <= p)
            break;
        p = end;
    }
    void *v = best ? MapViewOfFileEx(map, FILE_MAP_ALL_ACCESS, 0, 0, size, (void *)best) : nullptr;
    return v ? v : MapViewOfFile(map, FILE_MAP_ALL_ACCESS, 0, 0, size);
}

// "...\" before the closing quote would escape it for the helper's command line
static std::string quoted(std::string s)
{
    while (!s.empty() && (s.back() == '\\' || s.back() == '/'))
        s.pop_back();
    return "\"" + s + "\"";
}

bool KlnrClient::make_frame_section(uint32_t capacity)
{
    release_frame();
    if (frame_map_) CloseHandle(frame_map_);
    frame_map_ = nullptr;
    capacity_ = 0;
    const uint32_t generation = ctl_->generation + 1;
    char name[128];
    snprintf(name, sizeof name, "Local\\%s_f%u", session_.c_str(), generation);
    frame_map_ = CreateFileMappingA(INVALID_HANDLE_VALUE, nullptr, PAGE_READWRITE, 0, capacity, name);
    if (!frame_map_) { error_ = last_error("CreateFileMapping (frame)"); return false; }
    if (GetLastError() == ERROR_ALREADY_EXISTS) { error_ = "frame section exists already: " + std::string(name); return false; }
    capacity_ = capacity;
    frame_ = (uint8_t *)map_high(frame_map_, capacity_);
    if (!frame_) { error_ = last_error("MapViewOfFile (frame)"); return false; }
    ctl_->capacity = capacity;
    MemoryBarrier();
    ctl_->generation = generation;
    return true;
}

void KlnrClient::release_frame()
{
    if (frame_)
        UnmapViewOfFile(frame_);
    frame_ = nullptr;
}

bool KlnrClient::start(const KlnrClientConfig &config, uint32_t width, uint32_t height)
{
    stop();
    config_ = config;
    given_up_ = false;
    misses_in_row_ = 0;
    static LONG sessions;
    char b[64];
    snprintf(b, sizeof b, "KLNR_%lu_%ld", GetCurrentProcessId(), InterlockedIncrement(&sessions));
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

    std::string cmd = quoted(config_.helper) + " --session " + session_;
    if (!config_.model.empty()) cmd += " --model " + quoted(config_.model);
    if (!config_.log.empty()) cmd += " --log " + quoted(config_.log);
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
        // the helper ends by itself when this process ends; a session that ends earlier ends it here, and waits so
        // that nothing of it is still writing into the frame section
        if (WaitForSingleObject(process_, 0) == WAIT_TIMEOUT) {
            TerminateProcess(process_, 0);
            WaitForSingleObject(process_, 3000);
        }
        CloseHandle(process_);
    }
    release_frame();
    if (frame_map_) CloseHandle(frame_map_);
    if (ctl_) UnmapViewOfFile(ctl_);
    for (void *h : {control_map_, req_, done_})
        if (h) CloseHandle(h);
    process_ = frame_map_ = control_map_ = req_ = done_ = nullptr;
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

bool KlnrClient::miss(const char *why)
{
    if (++misses_in_row_ >= config_.max_misses) {
        char b[200];
        snprintf(b, sizeof b, "%s for %u frames in a row (timeout %u ms): switched off for this session", why, misses_in_row_,
                 config_.timeout_ms);
        error_ = b;
        given_up_ = true;
    }
    return false;
}

uint8_t *KlnrClient::frame(uint32_t width, uint32_t height, uint32_t pitch)
{
    if (!ctl_ || given_up_)
        return nullptr;
    if (busy()) {   // klnr.exe is still writing a late result into the buffer: leave it alone this frame
        miss("klnr.exe still busy with an earlier frame");
        return nullptr;
    }
    const uint64_t need = (uint64_t)pitch * height;
    if (need > 0x7fffffffu || pitch < width * 4)
        return nullptr;
    if (need > capacity_) {
        if (!make_frame_section((uint32_t)need)) {
            given_up_ = true;
            return nullptr;
        }
    } else if (!frame_) {
        frame_ = (uint8_t *)map_high(frame_map_, capacity_);
        if (!frame_) {
            error_ = last_error("MapViewOfFile (frame)");
            given_up_ = true;
            return nullptr;
        }
    }
    ctl_->width = width;
    ctl_->height = height;
    ctl_->pitch = pitch;
    return frame_;
}

bool KlnrClient::process(const KlnrParams &p)
{
    if (!ready() || !frame_)
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
    return miss("no result");
}
