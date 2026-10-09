# Loading time (2026-10-09, agent m-load; offline: kept logs, kl2.exe read statically, builds in scratch)

Question: a grafted level's "first boot takes 80 - 200 s, later ones 10 - 25 s" (re/fa_round.md 8.5,
re/maps.md 12) - why, and what makes both faster.

Short answer. The first / later split is wrong. The SAME build, the same file, loads in 11 - 15 s or in
100 - 200 s, and what tells the two apart in 67 kept loads is one thing: whether the game window was in
the FOREGROUND. Stock levels behave the same (stock L01: 155 s in the foreground). The size of the
archive hardly matters; the number of entities does. The cause is in kl2.exe, not in our files, and the
fix belongs in the hook (section 3). What the build side can do is implemented (section 5) and makes the
archives 40 - 50 % smaller, for a second or two of loading.

Tools: `python tools/kl_loadtime.py log <log>` (time per load stage), `... runs` (the table of section 1),
`... sheet <build>` (bytes per member, textures, unreferenced share). Options: `kl_graft.py build ...
--load trim,slim` or the environment variable `KL_GRAFT_LOAD`; `kl_graft.py lighten <build> <out>`.

## 1. What the kept logs say (ESTABLISHED: measured, `kl_loadtime.py runs`)

Every load of a level in `<work>/build/klhook/live/*.log`, with the window state klauto logs at the
first keyboard poll of the process (`result 00000000` = the DirectInput keyboard is acquired = foreground;
`8007000c` DIERR_NOTACQUIRED = not foreground):

| level in the slot | window | loads | median | range |
|---|---|---|---|---|
| F01 slot (grafted builds, 296 - 336 MB) | foreground | 49 | 135 s | 29 .. 206 s |
| F01 slot (the same builds) | background | 17 | 14 s | 11 .. 79 s |
| stock F02 (S4tb) | background | 1 | 8 s | |
| stock L00 (story intro, 9,474 nodes) | foreground | 3 | 41 s | 38 .. 43 s |
| stock L01 (34,288 nodes) | foreground | 1 | 155 s | |

- All runs before 14:20 had the window in the foreground and all were slow, first boot or not: the bank
  103, 111, 124, 108, 99, 137, 136 ... s on the same installed file; Retomoto 198, 190, 197, 199, 206 s.
- All runs 15:14 - 16:57 had it in the background and all were fast, INCLUDING first boots: CH1d was a
  build never loaded before (other size than CH0b - CH0d before it) and took 11.0 s; Retomoto took
  14.0 - 14.5 s seven times (N0, N0b, VAN1 - VAN5), the bank 10.8 - 12.1 s.
- The menu scene, a STOCK file that never changes, shows the same factor: `KaneAndLynch.gms` 18.9 s in
  RN3 (foreground), 1.7 - 1.9 s in VAN1 .. VAN5 (background).
- The owner's own session of this evening (`<DD>\KLHook.log`, read as a copy; one installed file,
  312,377,636 bytes, installed 17:21): direct boots took 119 s (17:21), 15 s (17:32), 114 s (17:37) and
  about 151 s (17:44, through the menu). The 15 s load lies BETWEEN two slow ones of the same file, so
  neither Windows' file cache, nor a scan of a new file, nor any cache the game writes explains the
  slow ones. (The SHIP hook does not log the window state; that the 17:32 load ran with another window
  in front is an inference, not seen.)
- Outliers: CH0 79 s and C1 69 s 'background', MP2b 29 s 'foreground'. The state is sampled once per
  process, at the first keyboard poll; a load during which the focus changed is filed under the wrong
  heading. ASSUMPTION, nothing in those logs can confirm it.

Time per stage, breadcrumbs on (Hooks=1), all three with the window in the foreground:

| | menu scene (RN3) | bank F07+M03 (RN3) | Retomoto (RT1c, stalled later) |
|---|---|---|---|
| nodes | 6,222 | 19,828 | 25,490 |
| stages 1 - 4, 10 - 50 % (the files) | 1.9 s | 7.2 s | 11.5 s |
| stage 5 entity loader 0x8ad7c0 | 6.8 s | 25.8 s | 45.0 s |
| stage 5 node properties 0x46fe20 | 7.8 s | 24.5 s | 42.5 s |
| stage 6 REF fix-up 0x6204b0 | 0.0 s | 6.5 s | 14.0 s |
| stage 7 object init stages 1 / 2 / 4 / 5 | 0.7 / 0.5 / 0.5 / 0.6 s | 7.1 / 10.2 / 10.7 / 10.7 s | - (HK3: 14 / 24 / 23 / 22 s) |
| total | 18.9 s | 102.9 s | 205 s (HK3) |

So in a slow load the FILE part is 7 - 12 % of the time. 1.3 ms per node in the entity loader and 1.2 ms
again in the property pass (Retomoto 1.8 and 1.7), 1.8 ms per object in each init stage: about the same
cost per step, whatever the step does (the menu scene's 6,222 stock nodes pay 1.1 and 1.25 ms).
Background runs have no stage lines (no
run with Hooks=1 had the window in the background); from their totals: 0.3 - 0.6 ms per node all in.
The level archive is opened three times per load: +0.0, +0.04 s and again at +2.2 s (background) /
+6.0 s (foreground), i.e. the third open comes around the end of stage 2.

## 2. Why: the loader's keep-alive pump (code ESTABLISHED by reading; its cost is the best explanation, NOT measured)

`ZEngineDataBase` slot 3 (0x53ac90) is the progress callback: the node loader calls it once per node
(0x46fe3b - 0x46fe7c), the staged init 0x80d800 once per object (0x80d8f2), and by their rates the entity
loader per entity and the file stages many times (those two call sites were not read). Its FIRST
instruction is `call 0x48a1e0`, before the 50 ms test that limits redraws of the loading screen:

    0x48a1e0  SetThreadExecutionState(0x80000003)
              if ([0x168e598]) { SteamAPI_RunCallbacks(); 0x753150(session, 0.0, 500); }
              ZSysInterfaceWintel slot 8 (0x82dfb0)(0):
    0x82dfb0      0x6f4220()                       <- the nudge
                  while (PeekMessageA(..)) { GetMessageA; TranslateMessage; DispatchMessageA }
    0x6f4220  h = top-level owner of GetForegroundWindow()   (GetParent / GetWindow(h, GW_OWNER) loop)
              if (h == [this+0x964])  {            <- only when the GAME is the foreground window
                  GetCursorPos(&p); SetCursorPos(p.x, p.y); mouse_event(MOUSEEVENTF_MOVE, 0, 0, 0, 0); }

So with the game in front, every progress step sets the cursor where it is and injects a mouse move of
(0, 0) - an idle-timer reset from 2010 - and then pumps the messages that this produced. An injected
mouse event is delivered synchronously to every low-level mouse hook and raw-input reader on the
desktop (overlays, recorders, peripheral software; this PC runs several). With the game NOT in front the
branch is skipped and a step costs only its own work.
- `mouse_event` (import slot 0xb105a4) has ONE reference in kl2.exe, 0x6f4295; `GetForegroundWindow`
  (0xb10594) ONE, 0x6f422b. 0x6f4220 has one caller (0x82dfc7).
- 0x48a1e0 has 27 callers: the progress callback, 11 places in the scene loader 0x820300, the staged
  init 0x80d800 - and the MAIN LOOP 0x87a930 (0x87a97f), once a frame. So the same cost is paid on
  every frame of play while the game is in front.
- One sample of where the time goes: `RT2_KLHook_stall.dmp` (the hook's watchdog dump of a foreground
  load). Main thread: win32u.dll system call <- return address 0x6f4299 (the instruction after the
  `mouse_event` call) <- 0x82dfcc <- 0x48a21f <- 0x53ac9b <- 0x80d8f2. It is one sample.
- Arithmetic: bank RN3, (2 x 19,828 nodes + 19,613 init objects) = 59.3 k steps in 89 s -> 1.5 ms per
  step; menu scene 13.9 k steps in 16.9 s -> 1.2 ms. One number for two very different scenes, as a
  per-call tax would give. A redraw of the loading screen (every 50 ms of `clock()`, 0x53ad84) cannot
  produce a factor of 10: it would have to take 450 ms a frame.
NOT ESTABLISHED: that the 1.2 - 1.5 ms are the two user32 calls and not something else that follows the
foreground state (the redraw, a presentation wait, the overlay). Experiment E1 in section 6 settles it.

Consequences already visible:
- 'A healthy level needs 205 s or more to its AutoExit', 'AutoExit counts ticks, not seconds', 'the slow
  clock' (kl_graft docstring, runs 6 / 7) and 'the frontend does not read the keyboard for about 22 s'
  (klauto.c) are this effect.
- Shot times of an unattended run cannot be copied from another run (N0 had no picture): take them
  from the log of the same run.
- In the foreground the load time follows the number of ENTITIES (and init objects), not bytes:
  Retomoto's archive is smaller than the bank's (296 against 321 MB) and loads slower in both states
  (25,490 against 19,828 nodes).

## 3. The fix that matters: in the hook (PROPOSED, not built - klhook is not this agent's)

Wrap the import slot of `USER32!GetForegroundWindow` (0xb10594; import slots are what the SHIP patch
policy allows, `klh_iat`) and return NULL except once per `CursorNudgeMs` (suggested 1000; 0 = pass
through, the game as shipped). With NULL the owner loop ends at once, 0x6f4260 compares 0 with the game
window and skips `GetCursorPos / SetCursorPos / mouse_event`. Nothing else in kl2.exe calls the function.

    static HWND WINAPI klh_w_getforegroundwindow(void)      /* kl2.exe: one call site, 0x6f422b in 0x6f4220 */
    {
        static DWORD last; DWORD now = GetTickCount();
        if (klh_nudge_ms && now - last < klh_nudge_ms) return NULL;
        last = now; return klh_real_getforegroundwindow();
    }
    ... n += klh_iat("USER32.dll", "GetForegroundWindow", (void *)klh_w_getforegroundwindow, (void **)&klh_real_getforegroundwindow);

Expected, IF section 2 is right: a foreground load like a background one - Retomoto about 14 s instead
of 115 - 200, the bank about 12, stock levels faster too - and about 1 ms less per frame in play. The
idle timer is still reset by `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED |
ES_DISPLAY_REQUIRED)` in the same function, and once a second by the nudge that is let through.
Also worth a line in the SHIP log (it has no window-state line): `GetForegroundWindow() == game window`
at each 'level archive opened'.
Until then, for the owner: no file helps; the evidence says a load runs about ten times faster while
another window is in front (click the other monitor / Alt-Tab while 'Buffering' shows, come back when the
sound of the level starts). Not tried on purpose yet.

## 4. The file path (partly read; marked)

- ESTABLISHED: kl2.exe holds zlib (`inflate 1.2.3`), parses the central directory (signature
  0x02014b50 at six sites), so a member is found by the directory, not by its position: member ORDER
  is not a correctness matter. All 45 stock archives have the directory in physical order and one order
  of extensions (.zgf .prp .sup .buf .HVK .gms .TEX .MAT .ANM [.LOC ..] .SND .oct .sgp .rmc .rmi .prm
  .sgd .hrd .fxc); kl_graft writes S's order, i.e. the same.
- ESTABLISHED: stock archives are deflate throughout; method 0 (stored) occurs 153 times, never for
  more than 32 bytes (.zgf 17, .sup 24, an empty .LOC 5). Whether the reader takes a LARGE stored member
  is therefore not shown by any stock file. The two functions with the local-header signature
  (0x54b610, 0x726630) are the archive WRITER (save games); the reading side was not found by signature
  and not followed further. NOT ESTABLISHED: buffer sizes, whether a member is inflated whole or in
  pieces, on which thread.
- ESTABLISHED: a read thread exists (0x458750, started from 0x6a5440): waits on two events, then
  `SetFilePointer(file, offset)` + `ReadFile(file, buffer, size)` synchronously and resets the event -
  a buffered stream with a reader thread; whose stream (archive, .WAV, stream file) was not followed.
  `CreateFileA` for reading: 0x43d1c9 with FILE_FLAG_OVERLAPPED | FILE_FLAG_SEQUENTIAL_SCAN, 0x5085f9
  FILE_FLAG_RANDOM_ACCESS, 0x5e2ab9 FILE_FLAG_SEQUENTIAL_SCAN, five more with plain attributes. Three
  `MapViewOfFile` sites exist; not attributed.
- ESTABLISHED: the whole .prm goes into ONE heap block of file size + 0x60000 (0x82049b, kl_graft).
- ESTABLISHED by the logs: opening costs nothing. The hook's fingerprint of the central directory
  (klsteam) and the first two opens lie within 40 ms of each other, also on a file installed a minute
  before (17:21:30.194 / .237) - no scanner delay at open. No file is written by the game during a
  load: nothing in the Dog Days folder but our installs and logs changed in three days, so there is no
  shader or level cache on disk (the .fxc member IS the compiled-shader cache).
- Offline measure of the file part (Python's zlib on this PC, warm cache; the game's 32-bit zlib 1.2.3
  is slower, by an unknown factor): reading and inflating all members takes 1.3 s for the bank or
  Retomoto as built, 0.6 - 0.9 s after `trim,slim`, 0.2 s stored. A freshly installed archive is in
  Windows' cache already (it was just written), so a 'first boot' was never a cold read.
- NOT MEASURED: texture creation per texture (the .TEX is 77 % of the unpacked bytes), the sound bank
  (.WHD / .WAV beside the archive, the `_LS` loading-sound files), the navigation mesh. From the
  background totals all of it together is at most the 2 - 3 s that separate a grafted level from what
  its node count alone predicts.

## 5. What the build does now (tools/kl_graft.py; each is an option; savings measured offline)

`python tools/kl_loadtime.py sheet <build>` prints the numbers per build.

| option | what | bank F07+M03_FA_A | Retomoto (F07+M09_B+M09_A) | state |
|---|---|---|---|---|
| (default) fixed time stamp | every member stamped 2010-08-17 12:00 (`STAMP`) | two builds 45 s apart: sha1 d694a22b both; equal to a repack of the installed 12:52 build | - | default; `stamp=now` = before |
| `trim` | .prm vertex / index chunks no live root reaches -> 16-byte stubs, always (was: only past 90 MB) | .prm 86.6 -> 44.3 MB (8,650 chunks, 1,401 dead roots); zip 321 -> 301 MB | already done by PRM_LIMIT (60.3 MB) | same operation Retomoto has run with live; never on the bank |
| `slim` | textures that only dead map materials name -> their own mip levels of 4 x 4 and below; ids, names, formats, material file unchanged | 464 of 1,864 textures, 192 MB; .TEX 387 -> 197 MB | 447 of 2,195, 180 MB; .TEX 406 -> 227 MB | NOT LOADED LIVE |
| `trim,slim` | both | zip 321.1 -> 164.0 MB, unpacked 531 -> 298 MB | zip 312.4 -> 183.0 MB, unpacked 529 -> 351 MB | candidates built: `<work>/build/m_load/bank_trim_slim`, `retomoto_trim_slim` |
| `level=6` | deflate level (1 before) | 164.0 -> 137.8 MB, packing 1.5 -> 4.4 s | 183.0 -> 152.1 MB, 2.3 -> 7.6 s | safe (stock is deflate); level 9: 134.9 / 148.6 MB for 15 - 18 s |
| `stored` | no compression | 298 MB (with trim,slim), inflate time gone | 351 MB | ASSUMPTION about the reader (section 4): try it once before use |

- Renumbering S was NOT done, on purpose: stubs keep every chunk index, texture id and material slot,
  so no reference anywhere (also the ones nobody has found yet) can dangle; the price is 135 bytes per
  dead texture and 16 per dead chunk. Materials are left alone (the file is 1 MB).
- What counts as dead (`kl_graft.dead_assets`): model roots that no entity (.gms record +0x0c) and no
  property (kl_prmgraph.prp_roots) names, found by shape (kl_prmgraph.orphans); a material that a dead
  mesh uses and no live one; a texture that such a material or a dead sprite names and NOTHING else
  does - every other material (also one no mesh names), the live chunks' texture fields, the HUD list
  ZOnScreenDisplay2[7] and the frame lists of kept textures count as users. Checked on stock F07: the
  textures called dead in a graft (Rival_Merc, Police_SP, the dog, F07's stone and concrete) belong to
  ZFFActors under `Gameplay!...`, the map side.
  ASSUMPTION: the engine never reaches a material by slot, or a model by chunk index, that the level's
  files name only on S's removed map. If it does, `slim` shows a 4 x 4 blur and `trim` nothing at that
  spot; neither can crash on a missing id.
- Checks in the tool: every chunk the level reaches is byte-equal after `trim`, the walk from the live
  roots is unchanged, the .MAT ref table the .prm implies is unchanged, the .TEX round-trips with the
  same ids; `build ... --load trim,slim` verifies with 0 problems and is byte-equal to `lighten` of the
  plain build (sha1 b1ecc623). 886 shrunk records were compared with their originals: same format,
  flags, name, group word, and the kept levels' bytes.
- Expected gain in loading: the file part only - an estimated 1 - 2 s of a 12 - 14 s background load,
  a little more in the foreground (about 450 textures fewer to create; a texture is one progress step).
  The real gain is disk and download size (-45 %) and 180 - 190 MB less texture memory.
- Sharing between maps: every grafted archive carries S's systems (about 190 MB of textures after
  `slim`). The loader takes one archive per level plus Patch01.zip (same-named members only), so shared
  members would need a hook redirect; not attempted.
- Fewer entities would help in both window states (0.5 ms per node in the background, 5 - 8 ms in the
  foreground). That is a content decision (kl_fa_author / kl_maps), not packing.

## 6. Live experiments, for when the owner releases the game (one variable per run)

Driver: `kl_autotest.py 420 --tag <run>` with klauto (it logs the first-keyboard-poll line), then
`python tools/kl_loadtime.py log <work>/build/klhook/live/<run>.log`. For the window state the tester
must really put the window in front or not (click it / click another window within 2 s of the launch)
and the log line must agree. 'Cold' = after a reboot; anything installed or loaded since boot is warm.

| run | build / hook | window | expects |
|---|---|---|---|
| E0a, E0b | installed Retomoto, today's hook, direct boot | front / back | 115 - 200 s / 14 s: the baseline of the day |
| E1 | the same + hook with `CursorNudgeMs=1000` (section 3) | front | about 14 s. THE experiment: if it stays slow, section 2's attribution is wrong |
| E1b | E1 with Hooks=1 | front | stage table: stage 5 at a fraction of a ms per node instead of 2.5 - 3.5 |
| E2 | E1 | back | unchanged, about 14 s |
| E3 | `m_load/bank_trim_slim` against the installed bank, E1's hook | front | 1 - 2 s less; shots: HUD, muzzle flash, blood, glass, police and civilians unchanged |
| E4 | `m_load/retomoto_trim_slim` | front | the same on Retomoto; walk both parts |
| E5 | E4 repacked `--load level=6` | front | no change in time, 31 MB less on disk |
| E6 | E4 repacked `--load stored` | front | loads at all (the reader takes a large stored member)? then up to 1 s less |
| E7 | E1 on stock F02 (plain) and from the menu | front | stock levels faster too; the menu scene 2 s instead of 19 |
| C1, C2 | E0a and E4 after a reboot, first load | front | the cold read: expected under 2 s more on this SSD |

## 7. Files

- `tools/kl_loadtime.py` (new): `log`, `runs`, `sheet`.
- `tools/kl_graft.py`: `load_options`, `write_zip` (fixed stamp), `dead_assets`, `small_texture`,
  `lighten`, `open_built`, `relight`; `build(..., load=None)`; CLI `--load`, `lighten`.
- Scratch: `<work>/build/m_load/bank_trim_slim`, `retomoto_trim_slim` (complete folders for
  `kl_graft.py install F01 --from ...`; the Retomoto folder has no KLJoin.ini, as its source has none).
