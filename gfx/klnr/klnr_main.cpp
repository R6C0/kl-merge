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

void logNotes(KlNrPass& pass) {
  for (const std::string& note : pass.takeNotes()) logf("%s", note.c_str());
}

void logReady(KlNrPass& pass, ULONGLONG startedAt) {
  logf("ready on %s in %llu ms (blend scale %g)", pass.deviceName().c_str(), (unsigned long long)(GetTickCount64() - startedAt),
       pass.blendScale());
  if (!pass.readbackCached())
    logf("WARNING: no cached host memory for the frame readback: reading results back is slow on this GPU");
  logNotes(pass);
}

// klnr.exe is started by the game, so it inherits Steam's environment, which switches on the Steam overlay's and
// Fossilize's implicit Vulkan layers (ENABLE_VK_LAYER_VALVE_*). Other programs install implicit layers too (capture
// and overlay tools). They would sit between klnr.exe and the NVIDIA-only extensions the network uses, and a compute
// helper with no window needs none of them: implicit layers are off unless KLNR_LAYERS=1 is set. Explicit layers
// (VK_INSTANCE_LAYERS, e.g. the validation layer) are not affected. Read by the Vulkan loader at vkCreateInstance.
void disableImplicitLayers() {
  char keep[8] = "";
  if (GetEnvironmentVariableA("KLNR_LAYERS", keep, sizeof keep) && keep[0] == '1') {
    logf("implicit Vulkan layers kept (KLNR_LAYERS=1)");
    return;
  }
  SetEnvironmentVariableA("VK_LOADER_LAYERS_DISABLE", "~implicit~");    // Vulkan loader 1.3.234 and later
  SetEnvironmentVariableA("DISABLE_VK_LAYER_VALVE_steam_overlay_1", "1");   // older loaders: Steam's own switches
  SetEnvironmentVariableA("DISABLE_VK_LAYER_VALVE_steam_fossilize_1", "1");
}

// ------------------------------------------------------------------------------------------------ --info
int runInfo() {
  try {
    vk::Context context;
    logf("device: %s, %u SMs, subgroup timestamps ok; the NR kernels' extensions are present", context.deviceName().c_str(),
         context.smCount());
    logf("RESULT PASS info: %s can run the network", context.deviceName().c_str());
    return 0;
  } catch (const std::exception& e) {
    logf("this GPU / driver cannot run the network: %s", e.what());
    logf("RESULT FAIL info: this GPU / driver cannot run the network (%s); the bridge still works without a model", e.what());
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
    logf("selftest %ux%u, %u frames, %s%s", w, h, args.frames, modelName(kind), args.test ? ", test pattern" : "");
    auto t0 = GetTickCount64();
    pass = std::make_unique<KlNrPass>(model, base, w, h);
    logReady(*pass, t0);
  } catch (const std::exception& e) {
    logf("FAILED to start: %s", e.what());
    logf("RESULT FAIL selftest %ux%u %s: did not start", w, h, modelName(kind));
    return 2;
  }
  const uint32_t pitch = w * 4 + 64;   // a pitch wider than the row, as D3D9 surfaces have
  std::vector<uint8_t> input((size_t)pitch * h), frame;
  KlControls controls;
  controls.temporal = !args.noTemporal;
  controls.test = args.test;
  controls.split = args.split;
  std::vector<double> host, gpu, network;
  int worst = 0, worstLeft = 0;
  double sumDiff = 0;
  uint32_t greyRight = 0, rightPixels = 0, discarded = 0;
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
      logf("RESULT FAIL selftest %ux%u %s: frame %u failed", w, h, modelName(kind), f);
      return 3;
    }
    logNotes(*pass);
    discarded += t.discarded;
    host.push_back(t.hostMs); gpu.push_back(t.gpuMs); network.push_back(t.networkMs);
    if (f + 1 == args.frames) {
      for (uint32_t y = 0; y < h; ++y)
        for (uint32_t x = 0; x < w; ++x) {
          const uint8_t* o = &frame[(size_t)y * pitch + x * 4];
          const uint8_t* i = &input[(size_t)y * pitch + x * 4];
          int d = 0;
          for (int c = 0; c < 3; ++c) d = std::max(d, std::abs((int)o[c] - (int)i[c]));
          worst = std::max(worst, d);
          if (x + 1 < w / 2) worstLeft = std::max(worstLeft, d);   // the test pattern greys x > w/2
          if (x > w / 2 + 1) { rightPixels++; greyRight += o[0] == o[1] && o[1] == o[2]; }
          for (int c = 0; c < 3; ++c) sumDiff += std::abs((int)o[c] - (int)i[c]);
        }
    }
  }
  auto median = [](std::vector<double> v) { std::sort(v.begin(), v.end()); return v.empty() ? 0.0 : v[v.size() / 2]; };
  logf("per frame (median): host %.2f ms, GPU %.2f ms, of which network %.2f ms", median(host), median(gpu), median(network));
  logf("last frame vs input: largest channel difference %d, mean %.4f%s", worst, sumDiff / ((double)w * h * 3),
       args.test ? " (the test pattern greys the right half)" : kind == KLNR_MODEL_NONE ? " (a round trip without a model: 0-1)" : "");
  // The verdict. none: the frame must come back as it went (sRGB round trip, at most 1 code value). Test pattern: the
  // right half grey, the left half unchanged. Synthetic zero model: "no change" through the whole composite, which
  // rounds through half floats and the tone path: a few code values (GUESS: 3 until seen on a real GPU). A real model
  // changes the frame by design: no verdict on the difference.
  bool ok = discarded == 0;
  std::string why = discarded ? std::to_string(discarded) + " frame(s) discarded by the watchdog" : "";
  if (args.test) {
    const bool grey = greyRight == rightPixels && rightPixels > 0;
    ok = ok && grey && worstLeft <= 1;
    if (!grey) why += (why.empty() ? "" : "; ") + std::to_string(rightPixels - greyRight) + " right-half pixels not grey";
    if (worstLeft > 1) why += (why.empty() ? "" : "; ") + std::string("left half changed by ") + std::to_string(worstLeft);
  } else if (kind != KLNR_MODEL_DIR) {
    const int limit = kind == KLNR_MODEL_NONE ? 1 : 3;
    ok = ok && worst <= limit;
    if (worst > limit) why += (why.empty() ? "" : "; ") + std::string("changed by ") + std::to_string(worst) + " (limit " + std::to_string(limit) + ")";
  }
  logf("RESULT %s selftest %ux%u %s%s: host %.2f ms, GPU %.2f ms (network %.2f ms) per frame%s%s", ok ? "PASS" : "FAIL", w, h,
       modelName(kind), args.test ? ", test pattern" : "", median(host), median(gpu), median(network), why.empty() ? "" : "; ",
       why.c_str());
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
  return ok ? 0 : 5;
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
  // The section of the current generation; its size is taken from the view itself, not from the control block
  // (which may already describe a newer generation).
  bool mapFrame(const std::string& session) {
    const uint32_t gen = ctl->generation;
    if (frame && generation == gen) return true;
    if (frame) UnmapViewOfFile(frame);
    if (frameMap) CloseHandle(frameMap);
    frame = nullptr; frameMap = nullptr; capacity = 0;
    std::string name = "Local\\" + session + "_f" + std::to_string(gen);
    frameMap = OpenFileMappingA(FILE_MAP_ALL_ACCESS, FALSE, name.c_str());
    if (!frameMap) { logf("cannot open %s (error %lu)", name.c_str(), GetLastError()); return false; }
    frame = (uint8_t*)MapViewOfFile(frameMap, FILE_MAP_ALL_ACCESS, 0, 0, 0);
    if (!frame) { logf("cannot map %s (error %lu)", name.c_str(), GetLastError()); return false; }
    MEMORY_BASIC_INFORMATION mbi;
    if (!VirtualQuery(frame, &mbi, sizeof mbi)) { logf("cannot size %s", name.c_str()); return false; }
    generation = gen;
    capacity = (uint32_t)std::min<SIZE_T>(mbi.RegionSize, 0xffffffffu);
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
    logReady(*pass, t0);
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
      logf("frame %u passed through: %ux%u pitch %u, buffer %u bytes", request, w, h, pitch, s.capacity);
      MemoryBarrier();
      ctl->done = request;   // the buffer still holds the frame as it came: KLGfx shows it unchanged
      SetEvent(s.done);
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
        // A new size rebuilds the network's resources and runs it once (up to seconds, not a frame time): while the
        // state says STARTING, KLGfx shows its frames untouched without counting them as missed, as at the start.
        ctl->state = KLNR_STARTING;
        MemoryBarrier();
        logf("resize to %ux%u", w, h);
        const ULONGLONG r0 = GetTickCount64();
        pass->resize(w, h);
        logf("resized in %llu ms", (unsigned long long)(GetTickCount64() - r0));
        logNotes(*pass);
        MemoryBarrier();
        ctl->state = KLNR_READY;   // this frame follows within a frame time
      }
      pass->process(s.frame, pitch, c, t);
      logNotes(*pass);
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
    ctl->done = request;   // a discarded result left the buffer as the frame came: shown unchanged
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
  logf("==== klnr 0.2 (OpenDLSS-NR network, MIT; no NVIDIA software or weights included) %s", GetCommandLineA());
  disableImplicitLayers();
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
