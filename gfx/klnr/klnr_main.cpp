// klnr.exe: the 64-bit helper that runs OpenDLSS-NR's network on Kane & Lynch 2's frames for KLGfx (the d3d9.dll
// proxy inside the 32-bit game). Frames travel through shared memory (klnr_protocol.h).
//
//   klnr.exe --session KLNR_<pid> [--model none|zero|<dir>] [--log <file>]    started by KLGfx
//   klnr.exe --selftest [--size 1920x1080] [--frames 120] [--model ...] [--out <file.ppm>] [--test] [--split]
//   klnr.exe --info                                                           the GPU and what it supports
//
// Files beside the exe: spv/ and ptx/ (OpenDLSS-NR's kernels), shaders/ (nr_preprocess.spv, kl_composite.spv),
// model/ (optional: a model directory the user supplies; nothing in this project provides one), klnr.log.
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

#include <algorithm>
#include <cmath>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <memory>
#include <string>
#include <vector>

#include "klnr_pass.h"
#include "klnr_protocol.h"

namespace {

FILE* g_log = nullptr;

void logf(const char* fmt, ...) {
  SYSTEMTIME t;
  GetLocalTime(&t);
  char line[2048];
  va_list a;
  va_start(a, fmt);
  vsnprintf(line, sizeof line, fmt, a);
  va_end(a);
  for (FILE* f : {g_log, stderr}) {
    if (!f) continue;
    fprintf(f, "%02d:%02d:%02d.%03d %s\n", t.wHour, t.wMinute, t.wSecond, t.wMilliseconds, line);
    fflush(f);
  }
}

std::string exeDir() {
  char path[MAX_PATH];
  GetModuleFileNameA(nullptr, path, MAX_PATH);
  char* slash = strrchr(path, '\\');
  if (slash) *slash = 0;
  return path;
}

bool fileExists(const std::string& path) {
  DWORD a = GetFileAttributesA(path.c_str());
  return a != INVALID_FILE_ATTRIBUTES && !(a & FILE_ATTRIBUTE_DIRECTORY);
}

struct Args {
  std::string session, model, log, out;
  bool selftest = false, info = false, test = false, split = false, noTemporal = false;
  uint32_t width = 1920, height = 1080, frames = 120;
};

Args parse(int argc, char** argv) {
  Args a;
  for (int i = 1; i < argc; ++i) {
    std::string s = argv[i];
    auto next = [&]() -> std::string { return i + 1 < argc ? argv[++i] : ""; };
    if (s == "--session") a.session = next();
    else if (s == "--model") a.model = next();
    else if (s == "--log") a.log = next();
    else if (s == "--out") a.out = next();
    else if (s == "--selftest") a.selftest = true;
    else if (s == "--info") a.info = true;
    else if (s == "--test") a.test = true;
    else if (s == "--split") a.split = true;
    else if (s == "--no-temporal") a.noTemporal = true;
    else if (s == "--frames") a.frames = (uint32_t)atoi(next().c_str());
    else if (s == "--size") sscanf(next().c_str(), "%ux%u", &a.width, &a.height);
  }
  return a;
}

// "none" / "zero" / a directory; with no --model, <exe>\model is used when it holds a manifest.json.
std::string resolveModel(const std::string& requested, const std::string& base, uint32_t& kind) {
  std::string m = requested;
  if (m.empty()) m = fileExists(base + "\\model\\manifest.json") ? base + "\\model" : "none";
  if (m == "none") { kind = KLNR_MODEL_NONE; return "none"; }
  if (m == "zero") { kind = KLNR_MODEL_ZERO; return "zero"; }
  if (!fileExists(m + "\\manifest.json")) throw std::runtime_error("no manifest.json in the model directory " + m);
  kind = KLNR_MODEL_DIR;
  return m;
}

const char* modelName(uint32_t kind) {
  return kind == KLNR_MODEL_ZERO ? "synthetic zero model (full network cost, no change)"
         : kind == KLNR_MODEL_DIR ? "model directory" : "no model (round trip only)";
}

void copyText(char* dst, size_t n, const std::string& s) {
  strncpy(dst, s.c_str(), n - 1);
  dst[n - 1] = 0;
}

// ------------------------------------------------------------------------------------------------ --info
int runInfo() {
  try {
    vk::Context context;
    logf("device: %s, %u SMs, subgroup timestamps ok; the NR kernels' extensions are present", context.deviceName().c_str(),
         context.smCount());
    return 0;
  } catch (const std::exception& e) {
    logf("this GPU / driver cannot run the network: %s", e.what());
    return 1;
  }
}

// --------------------------------------------------------------------------------------------- --selftest
// A synthetic frame (gradients, bars, a moving square) through the whole path, then a comparison of output and input.
int runSelftest(const Args& args, const std::string& base) {
  uint32_t kind = KLNR_MODEL_NONE;
  const uint32_t w = args.width, h = args.height;
  std::unique_ptr<KlNrPass> pass;
  try {
    std::string model = resolveModel(args.model, base, kind);
    logf("selftest %ux%u, %u frames, %s", w, h, args.frames, modelName(kind));
    auto t0 = GetTickCount64();
    pass = std::make_unique<KlNrPass>(model, base, w, h);
    logf("ready on %s in %llu ms (blend scale %g)", pass->deviceName().c_str(), (unsigned long long)(GetTickCount64() - t0),
         pass->blendScale());
  } catch (const std::exception& e) {
    logf("FAILED to start: %s", e.what());
    return 2;
  }
  const uint32_t pitch = w * 4 + 64;   // a pitch wider than the row, as D3D9 surfaces have
  std::vector<uint8_t> input((size_t)pitch * h), frame;
  KlControls controls;
  controls.temporal = !args.noTemporal;
  controls.test = args.test;
  controls.split = args.split;
  std::vector<double> host, gpu, network;
  int worst = 0;
  double sumDiff = 0;
  for (uint32_t f = 0; f < args.frames; ++f) {
    for (uint32_t y = 0; y < h; ++y)
      for (uint32_t x = 0; x < w; ++x) {
        uint8_t* p = &input[(size_t)y * pitch + x * 4];
        bool square = x >= (f * 7) % w && x < (f * 7) % w + w / 8 && y >= h / 3 && y < h / 3 + h / 8;
        p[0] = (uint8_t)(x * 255 / std::max(1u, w - 1));            // B
        p[1] = (uint8_t)(y * 255 / std::max(1u, h - 1));            // G
        p[2] = square ? 255 : (uint8_t)(((x / 64 + y / 64) & 1) ? 200 : 40);   // R
        p[3] = 255;
      }
    frame = input;
    KlTimings t;
    try {
      pass->process(frame.data(), pitch, controls, t);
    } catch (const std::exception& e) {
      logf("FAILED at frame %u: %s", f, e.what());
      return 3;
    }
    host.push_back(t.hostMs); gpu.push_back(t.gpuMs); network.push_back(t.networkMs);
    if (f + 1 == args.frames) {
      for (uint32_t y = 0; y < h; ++y)
        for (uint32_t x = 0; x < w; ++x)
          for (int c = 0; c < 3; ++c) {
            int d = std::abs((int)frame[(size_t)y * pitch + x * 4 + c] - (int)input[(size_t)y * pitch + x * 4 + c]);
            worst = std::max(worst, d);
            sumDiff += d;
          }
    }
  }
  auto median = [](std::vector<double> v) { std::sort(v.begin(), v.end()); return v.empty() ? 0.0 : v[v.size() / 2]; };
  logf("per frame (median): host %.2f ms, GPU %.2f ms, of which network %.2f ms", median(host), median(gpu), median(network));
  logf("last frame vs input: largest channel difference %d, mean %.4f (a round trip without a model should be 0-1)",
       worst, sumDiff / ((double)w * h * 3));
  std::string out = args.out.empty() ? base + "\\selftest.ppm" : args.out;
  if (FILE* f = fopen(out.c_str(), "wb")) {
    fprintf(f, "P6\n%u %u\n255\n", w, h);
    std::vector<uint8_t> rgb((size_t)w * 3);
    for (uint32_t y = 0; y < h; ++y) {
      for (uint32_t x = 0; x < w; ++x) {
        const uint8_t* p = &frame[(size_t)y * pitch + x * 4];
        rgb[x * 3] = p[2]; rgb[x * 3 + 1] = p[1]; rgb[x * 3 + 2] = p[0];
      }
      fwrite(rgb.data(), 1, rgb.size(), f);
    }
    fclose(f);
    logf("last output written to %s", out.c_str());
  }
  return 0;
}

// ---------------------------------------------------------------------------------------------- --session
struct Session {
  HANDLE controlMap = nullptr, request = nullptr, done = nullptr, game = nullptr;
  KlnrControl* ctl = nullptr;
  HANDLE frameMap = nullptr;
  uint8_t* frame = nullptr;
  uint32_t generation = 0, capacity = 0;

  ~Session() {
    if (frame) UnmapViewOfFile(frame);
    if (frameMap) CloseHandle(frameMap);
    if (ctl) UnmapViewOfFile(ctl);
    for (HANDLE h : {controlMap, request, done, game})
      if (h) CloseHandle(h);
  }
  bool mapFrame(const std::string& session) {
    if (frame && generation == ctl->generation) return true;
    if (frame) UnmapViewOfFile(frame);
    if (frameMap) CloseHandle(frameMap);
    frame = nullptr; frameMap = nullptr;
    std::string name = "Local\\" + session + "_f" + std::to_string(ctl->generation);
    frameMap = OpenFileMappingA(FILE_MAP_ALL_ACCESS, FALSE, name.c_str());
    if (!frameMap) { logf("cannot open %s (error %lu)", name.c_str(), GetLastError()); return false; }
    frame = (uint8_t*)MapViewOfFile(frameMap, FILE_MAP_ALL_ACCESS, 0, 0, 0);
    if (!frame) { logf("cannot map %s (error %lu)", name.c_str(), GetLastError()); return false; }
    generation = ctl->generation;
    capacity = ctl->capacity;
    logf("frame buffer %s: %u bytes", name.c_str(), capacity);
    return true;
  }
};

int runSession(const Args& args, const std::string& base) {
  Session s;
  const std::string prefix = "Local\\" + args.session;
  s.controlMap = OpenFileMappingA(FILE_MAP_ALL_ACCESS, FALSE, (prefix + "_ctl").c_str());
  if (!s.controlMap) { logf("no session %s (error %lu)", args.session.c_str(), GetLastError()); return 2; }
  s.ctl = (KlnrControl*)MapViewOfFile(s.controlMap, FILE_MAP_ALL_ACCESS, 0, 0, KLNR_CONTROL_BYTES);
  if (!s.ctl || s.ctl->magic != KLNR_MAGIC || s.ctl->version != KLNR_VERSION) { logf("session %s: wrong control block", args.session.c_str()); return 2; }
  KlnrControl* ctl = s.ctl;
  s.request = OpenEventA(SYNCHRONIZE | EVENT_MODIFY_STATE, FALSE, (prefix + "_req").c_str());
  s.done = OpenEventA(SYNCHRONIZE | EVENT_MODIFY_STATE, FALSE, (prefix + "_done").c_str());
  s.game = OpenProcess(SYNCHRONIZE, FALSE, ctl->game_pid);
  if (!s.request || !s.done || !s.game) { logf("session %s: events or game process missing", args.session.c_str()); return 2; }
  ctl->helper_pid = GetCurrentProcessId();
  ctl->state = KLNR_STARTING;

  std::unique_ptr<KlNrPass> pass;
  try {
    uint32_t kind = KLNR_MODEL_NONE;
    std::string model = resolveModel(args.model, base, kind);
    const uint32_t w = std::max(ctl->width, 64u), h = std::max(ctl->height, 64u);
    logf("session %s, game pid %u, %ux%u, %s", args.session.c_str(), ctl->game_pid, w, h, modelName(kind));
    auto t0 = GetTickCount64();
    pass = std::make_unique<KlNrPass>(model, base, w, h);
    ctl->model = kind;
    copyText(ctl->device, sizeof ctl->device, pass->deviceName());
    copyText(ctl->message, sizeof ctl->message, std::string("ready: ") + modelName(kind) + " on " + pass->deviceName());
    logf("ready on %s in %llu ms", pass->deviceName().c_str(), (unsigned long long)(GetTickCount64() - t0));
  } catch (const std::exception& e) {
    copyText(ctl->message, sizeof ctl->message, e.what());
    MemoryBarrier();
    ctl->state = KLNR_FAILED;
    logf("FAILED to start: %s", e.what());
    return 3;
  }
  MemoryBarrier();
  ctl->state = KLNR_READY;

  double sumHost = 0, sumGpu = 0, sumNet = 0;
  uint32_t count = 0;
  ULONGLONG lastReport = GetTickCount64();
  int rc = 0;
  for (;;) {
    HANDLE waits[2] = {s.request, s.game};
    DWORD r = WaitForMultipleObjects(2, waits, FALSE, 5000);
    if (r == WAIT_OBJECT_0 + 1) { logf("the game has ended"); break; }
    if (r != WAIT_OBJECT_0) continue;
    const uint32_t request = ctl->request;
    MemoryBarrier();
    const uint32_t w = ctl->width, h = ctl->height, pitch = ctl->pitch;
    if (!s.mapFrame(args.session) || w < 16 || h < 16 || (uint64_t)pitch * h > s.capacity || pitch < w * 4) {
      logf("frame %u skipped: %ux%u pitch %u, buffer %u bytes", request, w, h, pitch, s.capacity);
      SetEvent(s.done);   // done stays behind request: KLGfx keeps its own frame
      continue;
    }
    KlControls c;
    c.enabled = (ctl->flags & KLNR_F_ENABLED) != 0;
    c.temporal = (ctl->flags & KLNR_F_TEMPORAL) != 0;
    c.resetHistory = (ctl->flags & KLNR_F_RESET_HISTORY) != 0;
    c.split = (ctl->flags & KLNR_F_SPLIT) != 0;
    c.test = (ctl->flags & KLNR_F_TEST) != 0;
    c.intensity = ctl->intensity; c.localTone = ctl->local_tone; c.localStructure = ctl->local_structure;
    c.skinStructure = ctl->skin_structure; c.paperWhite = ctl->paper_white > 0 ? ctl->paper_white : 1.0f;
    c.colorStrength = ctl->color_strength; c.style = ctl->style;
    KlTimings t;
    try {
      if (w != pass->width() || h != pass->height()) {
        logf("resize to %ux%u", w, h);
        pass->resize(w, h);
      }
      pass->process(s.frame, pitch, c, t);
    } catch (const std::exception& e) {
      copyText(ctl->message, sizeof ctl->message, e.what());
      MemoryBarrier();
      ctl->state = KLNR_FAILED;
      logf("FAILED at frame %u: %s", request, e.what());
      SetEvent(s.done);
      rc = 4;
      break;
    }
    ctl->ms_upload = (float)t.uploadMs; ctl->ms_gpu = (float)t.gpuMs; ctl->ms_network = (float)t.networkMs;
    ctl->ms_download = (float)t.downloadMs; ctl->ms_total = (float)t.hostMs;
    ctl->frames++;
    MemoryBarrier();
    ctl->done = request;
    SetEvent(s.done);
    sumHost += t.hostMs; sumGpu += t.gpuMs; sumNet += t.networkMs; ++count;
    if (GetTickCount64() - lastReport >= 10000 && count) {
      logf("%u frames: per frame %.2f ms in klnr (GPU %.2f, network %.2f), %ux%u, flags %#x", ctl->frames, sumHost / count,
           sumGpu / count, sumNet / count, w, h, ctl->flags);
      sumHost = sumGpu = sumNet = 0; count = 0;
      lastReport = GetTickCount64();
    }
  }
  if (ctl->state != KLNR_FAILED) ctl->state = KLNR_EXITED;
  pass.reset();
  return rc;
}

}  // namespace

int main(int argc, char** argv) {
  Args args = parse(argc, argv);
  const std::string base = exeDir();
  std::string logPath = args.log.empty() ? base + "\\klnr.log" : args.log;
  g_log = fopen(logPath.c_str(), "a");
  logf("==== klnr 0.1 (OpenDLSS-NR network, MIT; no NVIDIA software or weights included) %s", GetCommandLineA());
  int rc;
  if (args.info) rc = runInfo();
  else if (args.selftest) rc = runSelftest(args, base);
  else if (!args.session.empty()) rc = runSession(args, base);
  else {
    fprintf(stderr, "usage: klnr --session KLNR_<pid> | --selftest [--size WxH] [--frames N] [--model none|zero|dir] | --info\n");
    rc = 1;
  }
  logf("exit %d", rc);
  if (g_log) fclose(g_log);
  return rc;
}
