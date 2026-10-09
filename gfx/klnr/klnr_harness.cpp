// klnr_harness.exe: a stand-in for the game. Runs the KLGfx side of KLNR (klnr_client) against klnr.exe with
// synthetic frames and checks what comes back. Used before anything goes near kl2.exe.
//   klnr_harness.exe [--helper <klnr.exe>] [--model none|zero|<dir>] [--size WxH] [--frames N] [--timeout ms] [--resize]
// Checks: without a model the frame comes back as it went (each channel within 1); with --test the right half comes
// back grey and the left half untouched; --resize grows the frame half way through (new frame section, helper resize).
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <vector>

#include "klnr_client.h"

static void fill(uint8_t *buf, uint32_t w, uint32_t h, uint32_t pitch, uint32_t f)
{
    for (uint32_t y = 0; y < h; y++)
        for (uint32_t x = 0; x < w; x++) {
            uint8_t *p = buf + (size_t)y * pitch + x * 4;
            p[0] = (uint8_t)(x * 255 / (w - 1));
            p[1] = (uint8_t)(y * 255 / (h - 1));
            p[2] = (uint8_t)((x + y + f * 5) & 255);
            p[3] = 255;
        }
}

int main(int argc, char **argv)
{
    KlnrClientConfig cfg;
    char exe[MAX_PATH];
    GetModuleFileNameA(nullptr, exe, MAX_PATH);
    std::string dir = exe;
    dir = dir.substr(0, dir.find_last_of("\\/"));
    cfg.helper = dir + "\\klnr.exe";
    cfg.model = "none";
    cfg.timeout_ms = 5000;
    uint32_t w = 640, h = 480, frames = 20;
    bool test = false, resize = false;
    for (int i = 1; i < argc; i++) {
        std::string a = argv[i];
        auto next = [&]() { return i + 1 < argc ? std::string(argv[++i]) : std::string(); };
        if (a == "--helper") cfg.helper = next();
        else if (a == "--model") cfg.model = next();
        else if (a == "--size") sscanf(next().c_str(), "%ux%u", &w, &h);
        else if (a == "--frames") frames = (uint32_t)atoi(next().c_str());
        else if (a == "--timeout") cfg.timeout_ms = (uint32_t)atoi(next().c_str());
        else if (a == "--test") test = true;
        else if (a == "--resize") resize = true;
    }
    printf("harness: helper %s, model %s, %ux%u, %u frames%s%s\n", cfg.helper.c_str(), cfg.model.c_str(), w, h, frames,
           test ? ", test pattern" : "", resize ? ", resize half way" : "");
    KlnrClient client;
    if (!client.start(cfg, w, h)) { printf("FAIL start: %s\n", client.error().c_str()); return 2; }
    DWORD t0 = GetTickCount();
    while (!client.ready()) {
        if (client.given_up() || GetTickCount() - t0 > 120000) {
            printf("FAIL: helper not ready: %s\n", client.error().empty() ? "timeout" : client.error().c_str());
            return 3;
        }
        Sleep(50);
    }
    printf("ready after %lu ms: %s\n", GetTickCount() - t0, client.control()->message);
    int failures = 0;
    for (uint32_t f = 0; f < frames; f++) {
        if (resize && f == frames / 2) { w = w * 3 / 2; h = h * 3 / 2; }
        const uint32_t pitch = w * 4 + 32;
        uint8_t *buf = client.frame(w, h, pitch);
        if (!buf) { printf("FAIL frame buffer: %s\n", client.error().c_str()); return 4; }
        std::vector<uint8_t> ref((size_t)pitch * h);
        fill(ref.data(), w, h, pitch, f);
        memcpy(buf, ref.data(), ref.size());
        KlnrParams p;
        p.flags = KLNR_F_ENABLED | KLNR_F_TEMPORAL | (test ? KLNR_F_TEST : 0);
        if (!client.process(p)) { printf("FAIL frame %u: no result (%s)\n", f, client.error().c_str()); failures++; continue; }
        int worst = 0, notGrey = 0;
        for (uint32_t y = 0; y < h; y++)
            for (uint32_t x = 0; x < w; x++) {
                const uint8_t *o = buf + (size_t)y * pitch + x * 4, *r = ref.data() + (size_t)y * pitch + x * 4;
                if (test && x > w / 2) {
                    if (o[0] != o[1] || o[1] != o[2]) notGrey++;
                    continue;
                }
                for (int c = 0; c < 3; c++) worst = worst > abs(o[c] - r[c]) ? worst : abs(o[c] - r[c]);
            }
        const KlnrControl *k = client.control();
        printf("frame %2u %ux%u: wait %.1f ms (klnr %.1f, GPU %.1f), largest difference %d%s\n", f, w, h, client.last_wait_ms, k->ms_total,
               k->ms_gpu, worst, test ? (notGrey ? " RIGHT HALF NOT GREY" : ", right half grey") : "");
        if (worst > 1 || notGrey) failures++;
    }
    printf("%s: %u frames back, %u missed, %d failed checks\n", failures ? "FAIL" : "PASS", client.frames_ok, client.frames_missed,
           failures);
    client.stop();
    return failures ? 1 : 0;
}
