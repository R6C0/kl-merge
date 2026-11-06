# Multiplayer smoothness audit (2026-11-06, offline, from existing bench logs)

Scope: where does the hook cost the game thread time when 4 to 9 seats play online, from logs that already exist. Nothing was launched.
Source of numbers: the `core: perf:` line of every `KLHook.log` (10 s windows: fps, hook tick ms a frame, slowest tick, memory reads a frame,
frames over 33 ms, longest frame). Bench dirs: `<work>/build/klhook/solo/` N9_DM01e (9 seats, 10-26), SM5E_DD05/DM03 (4 seats, 11-05),
RV5_DM01/DD03, Q35_DM03 (2 seats), PF6/lc1106 (no perf line). Notes: re/netsmooth_solo.md is about the two-instance setup and has nothing on
smoothness; re/open_work_log.md (stutter 10-14 .. 10-26, perf 11-05).

## 1. Evidence, per source

| Source | What hitched | Where | Cause (evidence) |
|---|---|---|---|
| N9_DM01e (9 seats, `[FrameLimit] Fps=30`, TEST ini with `[Sync] Probe/Compare/Puppet`) | In round: 17-24 fps instead of 30, hook tick 1-4 ms (slowest 85-300 ms), 5000-6800 reads/frame (900 in the lobby); longest frame 0.4-1.6 s | all 9 seats, round phase only | 9 kl2.exe on one PC are CPU bound (fps 30 -> 20), AND the `[Sync]` list walk: windows with a `sync: list` (512 lines every 5 s, klsync.c:1116) show 5300-5600 reads and slowest 100-267 ms; the windows without (08:25:17-37 inst7) show 1900-3400 reads, slowest 18-25 ms, 29 fps |
| N9_DM01e inst1 (host) | one 23.5 s gap at the first load (fps 1.9) | host, round load | the level load (no frames); "pollloss" 22-27 s per seat at the first load, benign (log 10-26) |
| N9_DM01e inst2 | 14.9 s stall in the last window | joiner 2, run end | the bench closing; not a round hitch |
| SM5E_DM03 / DD05 (4 seats, live ini, TEST twin) | slowest tick 289 ms at 13:20:09 and 329 ms at 13:21:09, 60 s apart = the two round starts | host and joiner, round start (round 1 and round 2) | `[CoverDump]` is ON by default in TEST: 4454 `coverdump:` lines (one WriteFile each) in the first 10 s of each round; 10502 of the run's 15478 log lines. Also 22-26 s with no frames at each load (fps 0.1) |
| SM5E / RV5 / Q35 in-round | host tick 1.1-2.2 ms (9-19 % of a 100-140 fps frame), joiner 0.6-1.1 ms; 3000-5200 reads/frame vs 350-1000 in lobby/shop; host 14-25 frames over 33 ms per 10 s, joiner 1-10 | round phase, host worse than joiner | reads go up 5x when the round starts: bots, brain, botfill, netsmooth, HUD crew list + the TEST-default-on probes (BotDeathProbe 250 ms samples, CoverRing poll every tick for 90 s after a load, MFProbe). Which part is the biggest is NOT measured per part yet (see TickProfile) |
| BO8b (10-26) | host frozen 297 s | host, when the joiner started presenting | two uncapped D3D9 instances starve the background one; bench inis cap Fps <= 60 with 2+ instances. Bench-only, not a game bug |
| Owner stutter 10-23..10-25 | 53-128 frames over 33 ms per minute | owner PC | NtUserPeekMessage under Medal/ReShade/overlay hooks; PD2 MCI jukebox (now off); logging handle reopened per line (fixed 10-14). Gone in the 19:04 run (2.3/min). Not an MP matter |
| Live ini (`<DD>\KLHook.ini`, read only) | has no `[Sync]`, no `[Perf]`; `[Shoulder] Log=1`, `[Heli] Probe=1`, `[FrameLimit] Enable=0` | owner PC | the perf keys (OsdBackoff/OnlineCache/FastRead) are written but NOT live (perf_1105 APPLY, pics_1105_hook SHIP 727a73bb); no bench has run them, so their effect is unmeasured |

Reading the 9-seat figures: the machine ran nine games, so fps there says little about nine PCs. What does carry over is the hook's own tick time
and read count per frame, and the spikes that line up with logged bursts.

## 2. Hook code that scales with players, bots or log volume

- `klhook.c:277 klh_rd` is `ReadProcessMemory` on our own process for everything outside kl2.exe's image (FastRead only covers the image). In
  rounds 3000-6800 of these a frame run on the game thread. Cost per call is a syscall; this is the biggest known lever. FastRead for HEAP
  pointers needs a validity check (a stale pointer must not fault): an idea, not done here (6b's area).
- `klhook.c:349 kl_online` called dozens of times a tick, 3-6 reads each: OnlineCache (6b, default off) already addresses it.
- `klsync.c:1116-1121` `[Sync] Probe`: every `Every` ms (default 3000, bench 5000) two full entity walks plus up to `Max` (700) `klog` lines, 35 % of
  them `ZFFItemWeapon p=0,0,0`. Compare/Apply/Puppet passes (klsync.c:1085-1115) walk again up to 4 times a second. TEST bench inis only.
- `klcoverdump.c:476-482` `[CoverDump]`, `klcoverring.c:343` `[CoverRing]`, `klbotdeath.c:216` `[BotDeathProbe]`, `klmfprobe.c:187` `[MFProbe]`:
  default ON in the TEST build (`#ifdef KLHOOK_TEST int def = 1`). Every TEST-twin bench measured with them. CoverDump at a load = thousands of
  one-line WriteFile calls on the game thread in one frame. SHIP defaults are off, so players do not pay this; the bench numbers overstate SHIP.
- `klhook.c:229 klog` is fine (open handle, one WriteFile per line, no flush). The cost is the NUMBER of lines. Top emitters in a round
  (N9 inst3): sync 25809, coverdump 7069, expansion 1042, heli 697, bd 690, netsmooth 444, shoulder 253. `heli` and `shoulder` are the live ini's
  `[Heli] Probe=1` and `[Shoulder] Log=1` (the pending ship ini turns both off).
- The 100-odd `*_tick` calls in `klh_tick` (klhook.c:1377) are each "returns at once unless set" but there is no per-part time anywhere, so the
  3000-5000 reads cannot be attributed. This is the real gap in the evidence.

## 3. Ranked fixes

1. **Bench hygiene, no code (done below as `QuietProbes`)**: perf and smoothness benches must run the four TEST probes OFF and no `[Sync]`
   walk, otherwise round-start spikes (300 ms) and 1000s of reads a frame are the probes. Needs a live A/B (section 5).
2. **TickProfile (new, default off)**: one line per 10 s with the six parts that cost the game thread most (ms/frame, reads/frame, slowest call)
   plus the three slowest single calls. Turns "3000-5000 reads" into a named list; every later fix is aimed with it. Live A/B: one 4-seat bench.
3. **Switch the already-built perf keys on in a bench (6b's, no new code)**: `[Perf] OsdBackoff=1 OnlineCache=1 FastRead=1`, compare the
   `core: perf:` reads/frame and tick ms with the same bench without them. Needed before they go to the owner.
4. **Heap-read fast path** (design only): for `klh_rd` targets in a heap region already validated by VirtualQuery (cache the last region),
   memcpy under `__try`; falls back to RPM when outside the cached region. Expect a large cut of the per-frame syscalls. Not implemented: klh_rd is
   6b's FastRead code and the crash risk (guard pages, freed pools) wants a design review first.
5. **Ship the log-volume cuts**: `[Shoulder] Log=0`, `[Heli] Probe=0` in the live ini (already in pics_1105_hook), keep `[Sync]` out of player inis.
6. **Batch CoverDump lines** (one WriteFile per dump, same text): only matters for TEST benches after QuietProbes; low priority.
7. **Load stalls (22-26 s no frames)**: engine level load, not hook code; the only hook angle is the `[Load]` nudge pump already present.

## 4. What was implemented (all default off, behaviour identical when off)

- `[Perf] QuietProbes=1` (recommended on for perf benches; TEST builds only matter): the four probes above default OFF; an explicit key such as
  `[CoverDump] Enable=1` still wins. Files: klperf_logic.h `klperf_probe_default`, klhook.c (`klperf_quiet`), klbotdeath.c:216, klcoverdump.c:476,
  klcoverring.c:343, klmfprobe.c:187. SHIP builds already default off (no change).
- `[Perf] TickProfile=1` (recommended on only for perf benches): `KLPT()` wraps each of the 104 part ticks in `klh_tick` (klhook.c:1377 ff.,
  `klpt_add` / `klpt_frame` at klhook.c:1342-1375). Off = one int test per part. On = two QueryPerformanceCounter reads per part on the game thread
  (about 0.2 us each), so it adds roughly 0.02 ms a frame; do not leave on for players. Log line: `core: tickprofile: N frames in S s; by time (ms a
  frame / reads a frame / slowest call ms): name a/b/c; ... | slowest single calls: name x ms; ...`.
- Tests: klperf_test.c +10 checks (`klperf_probe_default`, `klperf_pick_top`).
- NOT done (files claimed by another session at 02:28-02:30): KLHook.ini sample rows and klset.c mod-options rows for the two keys. Lines to add:
  `QuietProbes=0   ; (recommended on for perf benches, off for normal play) TEST builds: probes default off` and
  `TickProfile=0   ; (recommended off) 10 s line with the parts that cost the game thread most`, under `[Perf]`.

## 5. Live A/B (needs the game; for whoever owns the next bench slot)

Same map, same seats, one TEST twin built from this tree, bench ini = live ini plus the lines below. Compare `core: perf:` (tick ms, reads a
frame, frames over 33 ms) in the in-round windows, and round-start windows for the spike.
- A (baseline, as 11-05): no `[Perf]` section.
- B: `[Perf]` `QuietProbes=1` only. Expect: no 300 ms spike at round start, `coverdump:` lines 0, reads/frame down by the probes' share.
- C: B plus `TickProfile=1` (log only). Read the `core: tickprofile:` lines: the top parts are the next fix targets.
- D: B plus `OsdBackoff=1 OnlineCache=1 FastRead=1`. Expect fewer reads a frame (FastRead counts in the perf line) and a lower tick ms.
- 9-seat run: keep `[FrameLimit] Enable=1 Fps=30` (never 1000 with 2+ instances), `[Sync]` section absent.
Open risk: the three keys were never run live; TickProfile/QuietProbes are new and unrun (only logic-tested here).
