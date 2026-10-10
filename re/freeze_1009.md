# The freeze of 22:23, the DiscordHook faults, the "slow frontend" (2026-10-09)

Offline diagnosis, 2026-10-10 (agent z-freeze). Nothing was run in the game, nothing installed, nothing
written into the Dog Days folder. Sources: `<DD>\KLHook.log`, the kept dumps, kl2.exe (disassembly through
`debug/kl.py`), `<work>\research\watch\*` (kl_watch pictures), `<work>\build\klhook\live\M*.log`, the Windows
event logs (System, Application), Steam's `logs\*.txt`, Medal's `.logs\*.log` and the Medal clip written
2.4 s before the last log line (video frames only). "Established" = read in a log, a dump or the exe;
everything else is marked.

Three things in the task text do not hold and are corrected here:

- The game is **Direct3D 9**, not 10: kl2.exe imports `d3d9.dll` / `d3dx9_42.dll` only and holds no string
  `dx10` (the `-dx10` launch word is not read by anything). All overlay questions are D3D9 questions.
- At 22:23 the memory reserve was **still held**: every `memory:` line of that process ends
  `(+ the reserve)` and there is no `HeapAlloc ... FAILED` line. (The release happened in the NEXT
  process: 22:53:27 on its first load, then the 0x8e5bbd crash at 23:00:07 on its second.)
- The "display watchdog reports at 22:28" are **not** driver time-outs. They are what Windows writes
  when the user presses Win+Ctrl+Shift+B (section 1.2).

## 0. Short answers

1. **Freeze.** The owner chose Quit on the page between two rounds (score page, session state 0x20);
   the game went 0x20 -> 0x2e at 22:23:50.594 and its main thread never came back to the main loop:
   0x0, which follows within 4-22 ms in all 17 clean session ends of the log, never came, so the level
   was not even unloaded. That quit path was used **once** in the whole log - this time. The process
   (PID 38352) stayed alive, hung, until the hard reset at 22:30. There was no driver time-out, no
   bugcheck and no shortage of address space. **Why** the main thread stopped is NOT established (no
   dump). The exe has a mechanism that turns any stall of its render thread into exactly this picture:
   the main thread waits for the render thread once a frame **without a timeout** (kl2 0x459b1a). The
   best-fitting explanation is that wait meeting a focus change of the full-screen window in the same
   second (Medal's log points at one); the other is the quit path itself. One question to the owner
   and two short runs separate them (1.5, 1.6).
2. **DiscordHook.dll.** Three faults, not two (17:08, 17:55, 00:25), the same instruction each time:
   Discord's own D3D9 overlay hook takes a lock in an object whose global pointer is still NULL, on the
   game's render thread inside `IDirect3DSwapChain9::Present`. The DLL is in the process ONLY in those
   dumps and is the last DLL loaded: Discord injects it into the running game (after an Alt+Tab in the
   two cases with evidence) and its first frames kill the game. Not the level, not KLHook. Tell the
   owner to switch Discord's in-game overlay off for this game.
3. **Slow frontend.** The frontend was not slow. While the game's window is not the active window the
   main loop runs no frame and polls no input (kl2 0x87a963) - it only pumps messages, ~15,000 times a
   second. The scripts are stepped from the keyboard poll, so they stood still. Stock behaviour: an
   owner who alt-tabs gets a paused game, in the menu and in an Arcade round. In run M5 a second,
   separate thing added to it: `waitscene` can no longer see the (now fast) return to the menu.

## 1. The freeze at 22:23

### 1.1 Timeline

Process: SHIP hook built 22:02:59 (klnudge NudgeMs=1000, klchar, old klmem), kl2.exe PID 38352, F01 slot =
Retomoto + wardrobe (zip 212,120,742 bytes). First session 22:14:20 - 22:17:58 (three rounds, last life
lost, session end 0x28 -> 0x2e -> 0x0 in 7 ms). Second session from 22:18:00.

| time | what | source |
|---|---|---|
| 22:10:44 | Medal updates its recorder 2641.2922.1 -> 2641.2933.1 and restarts it | Medal `recorder-management.log` |
| 22:14:00 | Medal: `capturing` (stays so for the whole process) | same |
| 22:18:02.8 | second level load done: free 140 MB, largest piece 35.8 MB, `(+ the reserve)` | KLHook.log |
| 22:18:05-15 | game window not in front for part of this stretch (nudge line `no`, 5 of 10 passes) | KLHook.log |
| 22:21:40.8 | join box, jump to the street | KLHook.log |
| 22:23:21.5 | escaped (`SetAchievement('SIAI_HEIST_SINGLE_ESCAPE')` blocked) | KLHook.log |
| 22:23:24.5 | state 0x19 -> 0x1f, ROUND OVER "Continue in: 4" | log, picture 0058 |
| 22:23:32.5 | state 0x1f -> 0x20, score page (Buy Weapons / Ready) | log, clip |
| 22:23:35.873 | **last nudge line** (216 calls/s, window in front) | KLHook.log |
| ~22:23:36-41 | owner browses Buy weapons, goes Back | clip frames at 171.0 / 172.4 / 173.5 s |
| ~22:23:42.4 | Escape: "Do you really want to quit?" opens, No selected | clip, last changes at 174.23 s |
| ~22:23:43.0 | selection moved to Yes - **last picture change in the clip** | clip, 174.85 s |
| 22:23:45.873 | a nudge line is due at the first pump call from here on: none ever comes | KLHook.log |
| 22:23:48.146 | owner presses PageDown: Medal saves the last 3 minutes (320 MB, file closed 22:23:48.69) | clip name / file time, Medal `settings.json` |
| 22:23:48 | Medal re-shows its always-on-top overlay window (the "Saved the last 3m" note) | Medal `overlay.log` |
| 22:23:48.99 | kl_watch's last picture: quit dialog, Yes selected, Medal note top left | picture 0060 |
| 22:23:50 | Medal recorder: `capturing -> ready` | Medal log |
| **22:23:50.594** | **state 0x20 -> 0x2e - the last line of the hook log** | KLHook.log |
| 22:23:51 | Medal recorder: `ready -> capturing`; overlay window sized and shown again | Medal logs |
| after 22:23:49 | kl_watch writes nothing more: no picture, and the 22:23:50.594 line never reaches its `watch.log` | watch folder |
| 22:24:20 | Medal: `capturing -> inactive`, recorder shut down, overlay window closed | Medal logs |
| 22:24:41.6 / 42.1 | a new `steamwebhelper.exe` starts and dies after 0.5 s (c0000409 in libcef.dll) | Application log 1000 |
| 22:24:49.9 | lock screen app (LockApp hive) | System log |
| 22:24:59.99 - 22:25:10 | a new DWM session port; temporary account `defaultuser100000` created, logged on, removed | System / Application |
| 22:28:43 | `WindowsBlackScreenDiagnosticsV1`, P1 DWM, P3 ColorBits, **P4 Hotkey** | Application log 1001 |
| 22:28:47 | `LiveKernelEvent` 1a8 and 1b8 (P2 = 1), files `WATCHDOG-20261009-2228.dmp`, `WATCHDOG4400-...` | Application log 1001 |
| 22:29:33 - 22:30:02 | the machine sleeps and wakes (`Suspending` / `resuming`) | Steam `systemmanager.txt`, `steamui_system.txt` |
| 22:30:21.8 | power button (`PowerButtonTimestamp`), no long press detected | Kernel-Power 41 data |
| 22:30:46.5 | boot; Kernel-Power 41, BugcheckCode 0; EventLog 6008 | System log |

Clip time is mapped to the clock by its end = the hotkey (179.97 s = 22:23:48.15); the two session-state
changes it shows (156.48 s, 164.48 s) land within 0.2 s of the hook's lines, so the mapping holds.

### 1.2 Established

- **The trigger moment is the quit on the score page.** Clip and picture show the dialog; 0x20 -> 0x2e
  follows. It is the only `-> 0x2e` in 28,827 log lines that does not come from 0x28 (session end) or
  from the frontend at exit, apart from one online lobby the owner left at 00:43:51 (0xd -> 0x2e, which
  took 9.8 s and DID reach 0x0).
- **What that path is in the exe.** `ZGUIOQuitGame` accept (0x599a50, message 0x7f) -> Arcade branch
  0x599b49 -> 0x418660. With the state >= 0x1f that routine only zeroes the lives (`[state+0x6c] = 0`,
  0x418730), sets `[rules+0x200] = 600.0` and jumps to rules slot 82 (0x4f9f90) - which returns at once
  in states 0x20 / 0x21 / 0x22 / 0x28 (0x4f9fa1..0x4f9fbb). So no 0x28: **no upload, no stats** (hence
  no `BLOCKED` lines), and the session closes directly. 0x2e has three setters (found by scanning for
  `push 0x2e` ahead of a call through the state setter `[vt+0x68]`; other code shapes were not searched): 0x66a889
  (`ZSessionHandlerServer` slot 1: next round refused when 0x6ba140 says no), 0x8a4f03 (`ZSessionManager`
  slot 4 = close session, which also opens the window `FASessionClosingInterlude`; reached through
  `ZSessionManagerMultiplayer` slot 4, 0x5c8ea0) and 0x759073 (client handler). Which of the first two
  ran here is not established.
- **The main thread stopped within one frame's work after 0x2e.** All 17 Arcade session ends of the log
  go 0x28 -> 0x2e -> 0x0 in 4 - 22 ms; the `.prm` block is freed ~55 ms after 0x0 and the frontend scene
  is current ~10 ms later (lines of 23:29:40.108 / .113 / .166 / .171 are typical). Here 0x0 never came.
  The level unload, the frontend load and their allocations were therefore never reached: **address
  space cannot be the cause** of the stop (and 140 MB were free, 128 MB more in the intact reserve; a
  failed allocation in this game is a write to 0, a crash, not a hang).
- **No pump call after 22:23:45.873.** The nudge line is written at the first `GetForegroundWindow`
  call 10 s after the previous one. It is called from the message pump 0x82dfb0 <- 0x48a1e0. With the
  window active that is once a frame (150-250 a second in this session); with the window inactive the
  main loop calls it ~15,000 times a second. Neither happened again in the 6.5 minutes the process
  lived on, so the main thread was not idling in either loop: it stood in a wait or in a call.
- **The process did not die.** Steam tracked PID 38352 from 22:13:53 and never logged its end before
  the reboot; no Application Error / hang entry for kl2.exe; no `kl2_490_crash_*.mdmp`; no `exit:` line.
- **No driver time-out, no bugcheck.** System log, whole day: no Display 4101 ("nvlddmkm stopped
  responding"), no nvlddmkm entry, no LiveKernelEvent 141 / 117; Kernel-Power 41 has BugcheckCode 0.
  The 22:28 entries carry `P4: Hotkey`: the black-screen diagnostics of Win+Ctrl+Shift+B, i.e. the
  owner trying to get the picture back five minutes after the freeze. (1a8 / 1b8 are the live dumps
  that key combination makes - VIDEO_DXGKRNL_LIVEDUMP / VIDEO_MINIPORT_BLACK_SCREEN_LIVEDUMP from
  memory, not looked up. `C:\Windows\LiveKernelReports` and three of the four WER report folders are
  not readable from this account; nothing was copied.)
- **More than the game was stuck.** kl_watch, a separate Python process that only looks for the game
  window and grabs the screen with ffmpeg, stopped completing its loop between 22:23:49 and 22:23:56:
  the next thing it does after a grab is copy new KLHook.log lines, and the 22:23:50.594 line is not in
  its `watch.log` (last write 22:23:42.9); the folder's time stamp shows no file was created or removed
  after picture 0060. What is left in its loop is a window call or the desktop grab. Together with the
  web helper that died at start (22:24:42), Medal closing its recorder (22:24:20), the lock screen, the
  hotkey and the reset this is a blockage of the desktop session's display path, not only one hung
  window. INFERENCE from kl_watch's silence; that someone ended kl_watch in those seconds cannot be
  excluded, nothing suggests it.
- **The exe turns a render-thread stall into a main-thread stall.** The game draws on its own thread
  (loop 0x561330: wait for the frame event `[win+0x11d4]`, draw 0x7c1c30, whose last call is
  `IDirect3DSwapChain9::Present` at 0x7c4c07, then set `[win+0x11c4]`). The main thread, once a frame
  (engine frame 0x5c7100 -> 0x5c71cb -> 0x459ac0), does `WaitForSingleObject([win+0x11c4], INFINITE)`
  at 0x459b1a (`push -1` at 0x459b17). If Present does not return - a hook, the driver, a display that
  is in transition - the main thread never pumps a message again and the game never notices anything.
  Seen live in both DiscordHook dumps: render thread faulting inside Present, main thread standing at
  0x459b20. This is the mechanism; that it is what happened at 22:23 is NOT established.
- `win` = `[[0xdd2640]+0x970]`, the window object; `[win+0x11a8]` is its device-lost flag (set at
  0x7c4c10 when Present returns D3DERR_DEVICELOST). Not to be confused with `[sys+0x11a8]`, the
  re-entry guard of the message pump 0x82dfb0 (same offset, other object).

### 1.3 Not established

- Where the main thread stood (no dump: the SHIP hook has no stall watchdog).
- Whether the game was already stalling before the Yes was taken. The picture did not change from
  ~22:23:43.0 to at least 22:23:48.9 and no pump call came after 22:23:45.873, but the Yes was taken at
  ~22:23:50.5, so the main thread was alive then. Reading R1: the owner simply waited 7 s on the dialog
  (saved the clip in between) and the frame path of "quit dialog over the score page" does not reach
  the pump. Reading R2: Enter was pressed at once, the game answered 7 s late (the render thread slow
  in Present from ~22:23:43-45), then stopped for good. In a round, the pause menu and the quit dialog
  do keep the pump going (~470 calls/s in runs M2-M7, estimated from the 10-s counts), which speaks for
  R2; the score page is another page, which leaves R1 open.
- What exactly Medal's `capturing -> ready -> capturing` at 22:23:50 / :51 is. It is not a clip save
  (clips at 22:54:48 and 22:57:29 made none) and not a session end (none of the clean ends has one).
  After the reboot the same one-second pair occurs five times - 23:16:36, 23:22:52, 23:41:54, 00:20:10,
  00:31:52 - and every one sits on the game window changing between active and inactive (nudge lines
  flip `yes` / `no`, or show a one-second burst of the 15,000-a-second inactive loop); none of those
  froze. So at 22:23:50 the game window most likely **lost or regained the foreground in the very
  second of the last log line**. What took the foreground is unknown (Medal had shown its always-on-top
  window two seconds earlier and shows it again at :51; Windows replaces a window that stopped
  answering after 5 s - which is reading R2). Cause or symptom: unknown.
- Whether the quit path itself (stock code, reached with the hook's blocked Steam writes or not) can
  hang. It closes a session that never went through 0x28; in Arcade `ZGUIOSessionStateInterlude` slot 8
  (0x563ff0) does nothing in state 0x2e because 0x7aca80 answers 0 for game mode 4 with net state <= 1,
  and the session update (0x6c49a0) ignores states above 0x2b; the code that takes 0x2e to 0x0 was not
  found.
- Why the screen could not be recovered by the owner (lock screen reached at 22:24:49, sleep at
  22:29:33). The game runs full screen at 2560x1440; Medal treats it as a window and lays its own
  always-on-top window over it.

### 1.4 What differed from the sessions that left cleanly

| | 22:23 freeze | 17 clean Arcade ends (21:37 ... 00:50) |
|---|---|---|
| path | Quit on the score page: 0x20 -> 0x2e | 0x28 -> 0x2e (last life lost, or Quit in a round) |
| upload / stats | none attempted | 29-31 writes blocked or passed, every time |
| time in 0x2e | for ever | 4 - 22 ms |
| session number in the process | 2nd | 1st, 2nd and 3rd (00:45:24, 00:45:58, 00:46:58: three in one process) |
| free after the level load | 140 MB, largest 35.8, reserve intact | 132 - 265 MB, largest 14 - 85 MB (all 23 Retomoto loads with a `memory:` line) |
| klmem | old (release on failure), reserve never touched; the first `HeapAlloc ... FAILED` of the whole log is 22:53:27, the next process | old and rewritten, both |
| Medal | recorder version 13 minutes old, clip saved 2.4 s before | same version from 22:31 on, clips at 22:54, 22:57, 00:22, 00:40, 00:47 without a freeze |
| our helper scripts | kl_watch running (its folder); kl_loadfocus probably (window out of front at the 22:18 load) | neither after the reboot |

So "second session" and "memory" do not separate the cases. The quit path does - together with what
fell into the same seconds: the clip saved 2.4 s earlier and a likely focus change of the window (1.3).

### 1.5 Ranked explanations (none established)

1. **A focus change of the full-screen window met the frame hand-off.** The render thread was in
   Present (or in a hook inside it: Medal `medal-hook32.dll`, Steam `gameoverlayrenderer.dll`, NVIDIA
   `nvspcap.dll`; Discord's DLL was most likely not in the process, it is in none of the 12 non-Discord
   dumps) when the window lost or regained the foreground; a full-screen Direct3D 9 device then needs
   the WINDOW's thread (messages sent to it, the mode change), and that thread - the main thread - is
   at 0x459b1a waiting for the render thread without pumping. Each waits for the other. Fits: no pump
   call (an inactive window would otherwise show 15,000 calls a second), no state 0x0, Medal's capture
   restart in that second, a display transition that never completes and blocks other programs, no
   driver time-out, and the rarity (the focus change has to land inside the wait). ASSUMPTION as to the
   call that needs the window thread; the wait without a pump is read in the exe.
2. The quit-from-score-page path hangs in game code (a wait that never ends) and a hung full-screen
   D3D9 window did the rest. Fits the uniqueness of the path; does not by itself explain kl_watch.
3. Chance coincidence of the quit with a display fault of the machine. Nothing supports it: no
   time-out, no hardware error entries.

### 1.6 Cheapest next steps

- **Ask the owner (costs nothing):** did the game stop reacting BEFORE the quit was confirmed (Enter
  pressed and nothing for seconds), or did they wait on the dialog, save the clip, then confirm? And
  what did the screen show afterwards - frozen picture or black? This separates R1 from R2.
- **E1, one run of ~4 minutes, TEST hook** (its watchdog writes `KLHook_stall.dmp` with every thread):
  Retomoto as installed, one round to the score page (the standing player is shot ~20 s after GO), then
  `tap ESCAPE`, `wait 30000`, select Yes, `tap RETURN`; `StallMs=20000`. Read: (a) do nudge lines go on
  during the 30 s on the dialog (R1 or R2), (b) does 0x20 -> 0x2e -> 0x0 complete. If it hangs:
  `python debug/dump.py KLHook_stall.dmp --threads` names the thread standing in Present or in game
  code. Repeat as second session of the process, and with Medal closed. If it never hangs, repeat with a
  Medal clip (PageDown) two seconds before Yes.
- **E1b, the focus reading** (explanation 1): same hook, any level, game full screen, and a helper that
  takes the foreground away and gives it back every few seconds for five minutes (the cover window of
  `tools/kl_loadfocus.py` does exactly that). A hang with the main thread at 0x459b20 and the render
  thread inside d3d9.dll / user32.dll confirms it; then repeat with `-o DisableSeparateRenderThread`.
- **E2, same run on stock F02** - is the path sound on a stock level at all.
- Until E1 is done the owner should leave a session by Ready -> pause menu -> Quit inside the round
  (0x19 -> 0x28 -> 0x2e -> 0x0, clean every time), not from the score page.

### 1.7 Hook changes proposed (described only; klhook is not mine)

1. **Stall watchdog in the SHIP build.** The ticker thread (`klh_ticker`, 100 ms) already knows when the
   main loop last called `SteamAPI_RunCallbacks`. Loads keep ticking (the loader calls 0x48a1e0); the
   longest healthy silences in the log are 10.7 s (frontend load, 21:37:17) and 8.6 s (Alt+Tab, 17:54:59).
   So: silent for `[Watchdog] StallMs` (30000) -> write `KLHook_stall.dmp` once with all threads and log
   the main and render thread positions; silent for `EndMs` (90000) -> `TerminateProcess`. At 22:23 this
   would have left a dump that answers section 1.3 and given the desktop back without a reset.
2. Say when the pump stops: keep the tick count of the last `GetForegroundWindow` call and let the
   ticker log `nudge: no call for 3 s (last at ...)` once - the exact moment instead of a 10-s window.
3. `tick: driven by` is capped at six lines per process and was used up by 22:17:10; log every silence
   of more than 2 s with its length instead.
4. Worth one test run, not a default: `-o DisableSeparateRenderThread` (kl2 0xb226a0, read at 0x6e0af7
   by the same switch reader 0x793550 as `DisableSplashScreens`; clears `[renderer+0xa8668]`). Present
   then runs on the main thread (0x66e543) and the hand-off wait disappears. Static reading only. The
   TEST hook's `CmdAdd` can add it for one run without touching the Steam launch options.
5. Only if E1b confirms explanation 1: make the hand-off wait answer the window. Both waits go through
   the import slot of `KERNEL32.WaitForSingleObject` (0xb1023c, 38 call sites; the two are 0x459b1a and
   0x459b73). A wrapper that passes every call on, except INFINITE waits on the main thread returning
   to 0x459b20 / 0x459b79, which it runs as `while (wait(h, 50) == WAIT_TIMEOUT)
   PeekMessage(&m, 0, 0, 0, PM_NOREMOVE | PM_QS_SENDMESSAGE);` - that lets messages SENT from other
   threads through and takes nothing out of the queue. An import slot only, as the ship policy asks.

## 2. The DiscordHook.dll faults

### 2.1 Facts

| when | run | state | game window before | kl2 return addresses on the faulting stack |
|---|---|---|---|---|
| 17:08:08.944 | test MP2b | 0x15, 3.6 s after the level came in | not logged | 0x7c4c09 < 0x56139e |
| 17:55:12.298 | owner | 0x20 score page / Buy weapons | Alt+Tab at 17:54:59 (kl_watch picture 0081 shows the task switcher; main loop silent 17:54:59.1 - 17:55:07.7) | 0x8409bc, 0x406cd2 (stale), 0x7c4c09 < 0x56139e |
| 00:25:04.299 | owner | 0x20 score page | not in front from ~00:22:45 to at least 00:25:01 (nudge lines `no`) | same as 17:55 |

- Same instruction every time, `DiscordHook.dll+0x1f7fd`, same registers but for the stack base:

  ```
  +1f7f0  push ebp ; mov ebp, esp
  +1f7f3  mov  edx, [DiscordHook+0x1093d0]     ; a global object pointer
  +1f7f9  mov  cl, 1 ; xor eax, eax
  +1f7fd  lock cmpxchg byte ptr [edx+0x45], cl ; edx = 0 -> 'writing address 00000045'
  ```
  A try-lock on a byte of a global object whose pointer is NULL.
- The faulting thread is the game's **render thread** (0x56139e = loop 0x561330), inside
  `IDirect3DSwapChain9::Present` (0x7c4c07; the call passes five zeros and the swap chain
  `[win+0x1798]`, the result is compared with 0x88760868 = D3DERR_DEVICELOST). Above it on the stack:
  `DiscordHook.dll` frames mixed with `d3d9.dll` frames - Discord's Present hook drawing its overlay.
  The main thread stands at 0x459b20, waiting for the render thread. 0x8409bc / 0x406cd2
  (`DrawIndexedPrimitive` wrapper 0x840990) are leftovers lower on the stack, not live frames.
- `DiscordHook.dll` (Discord app-1.0.9260, `discord_hook-1`, linked 2026-09-28) is in the module list
  of the two fault dumps **and of no other dump**: the 12 other dumped events of 10-08 to 10-10 (among
  them the crashes of 17:37, 17:41, 18:20, 21:39, 00:41, 00:44, 00:47 and the watchdog dumps of 08:49
  and 23:45) hold Steam's, NVIDIA's and Medal's hook DLLs but not Discord's. In the two fault dumps it is the last DLL loaded (129 of 131, 131 of
  133), followed only by `D3DCompiler_47.dll` - which no other dump has, so Discord's hook loaded it -
  and `wow64cpu.dll`, which is always last.
- At 00:25 the nudge wrapper was in (SHIP 23:02:52), at 17:08 and 17:55 it was not: the wrapper is
  neither cause nor cure. No kl2.exe device reset, resolution or back-buffer change is involved on our
  side; KLHook touches no Direct3D call.

### 2.2 What it is

Discord does not ride along from the start of the game here. It injects its overlay DLL into the
RUNNING process - in the two cases with evidence right after the owner had been out of the game by
Alt+Tab - hooks Present, and the render thread's next Present runs Discord's hook before (or without)
the hook's global state existing. Discord's bug; a game that presents from a thread other than its
window thread makes such a race easy to lose. INFERENCE for the reason of the NULL pointer (no symbols);
the late injection, the thread, the call and the NULL are established.

It is not caused by the grafted level (Present is the same call on any level) and would be expected on
the stock game too. Not shown: E3 below.

### 2.3 What to tell the owner

- Turn Discord's in-game overlay off for Kane & Lynch 2 (Discord: User Settings -> Game Overlay, or
  Registered Games -> the game -> overlay off). The DLL is then never injected. Voice chat keeps working.
- All three known faults killed the game within seconds of coming back to it (or of its start); with the
  overlay on, Alt+Tab to Discord during a session is the thing to avoid.
- Medal, Steam's overlay and NVIDIA's capture DLL are in every dump and none of them appears in any
  fault: no reason to remove them for this. (For the freeze, Medal is still a candidate: section 1.)

### 2.4 Cheapest experiment (E3)

Stock F02, Discord running as on 10-09 (overlay on, in a voice channel), Alt+Tab to Discord and back
three times. Expected: `FATAL ... DiscordHook.dll+0x1f7fd` on the first or second return. Then overlay
off, same thing: no fault, and `python debug/dump.py <any later dump>` lists no DiscordHook.dll among
the guest DLLs. A hook-side block of the injection is possible but not worth writing for one setting.

## 3. The "slow frontend" in runs M3 - M5

### 3.1 Facts

- While the scripts stood still the nudge lines say `game window in front at the last one: no` with
  14,000 - 17,000 calls a second. Calls per second with the window in front: 1,600 - 4,500 in the
  frontend, 400 - 500 on the end-of-session pages.
- M4: `waitscene` done at 23:30:25.9 "at the first keyboard poll after a pause of 15437 ms"; then
  `wait 7000` ran from 23:30:25.9 to 23:32:16.5 = **110.6 s**; the window was in front only around
  23:30:26-28 and 23:32:16-18. `log.py` now adds this up: not in front for 170 s in three stretches.
- M5: no keyboard poll from 23:36:57.9 to 23:41:54.8 (296,891 ms); not in front for 530 s in all; ended
  by `maxrun`. The watchdog's stack shows the main thread inside the main loop step (0x87a93b), i.e.
  looping, not hung. `frames=263655` for 700 s: the counter is the keyboard poll count.
- M6 and M7 kept the window in front and ran at full speed (M7 PASS).

### 3.2 Why (read in the exe)

The main loop step 0x87a930, called from `ZSysInterfaceWintel` slot 47:

```
87a936  call 0xb0fda0
87a93b  al = session && 0x863a60(session) && !0x7f6850(session)   ; a session that is not Arcade
87a963  if ([sys+0xb10] == 0 && !al):       ; window not active
87a97d      sys->vt[0x20](0)                ; message pump 0x82dfb0
87a97f      call 0x48a1e0                   ; RunCallbacks + pump again
87a988      return                          ; NO engine frame, NO input poll, NO draw
        ... otherwise the normal frame (input 0x87a9fd, engine frame 0x87aa7a, RunCallbacks 0x87aa7c)
```

`[sys+0xb10]` is written by the window procedure 0x714810: 1 on WM_ACTIVATE (active) and WM_SETFOCUS
(0x7148b1, 0x7149de), 0 on WM_ACTIVATE (inactive) and WM_KILLFOCUS (0x714901, 0x714a57). There is no
Sleep in the inactive branch: one core spins. Arcade counts as "not online" (0x7f6850), so a round
pauses too.

klauto steps its script inside the keyboard poll (`kla_script_step` from the poll hook, `kla_frames++`
there): no poll, no step. `Unfocused=1` only makes the poll succeed when the device is not acquired; it
does not make the game poll.

Who took the foreground in M3 - M5 is not in the logs (the owner working on the PC is the plain
explanation; `kl_loadfocus.py` only acts on `0x0 -> 0x12` / `0x12 -> 0x15` lines).

### 3.3 The second thing in M5: `waitscene`

With Hooks=0 klauto recognises a finished load by a PAUSE in the keyboard polls. Since the nudge fix
the return to the frontend takes under a second, so there is no pause and `waitscene KaneAndLynch`
waits although the scene is long loaded (M6: failed after 120 s with the window in front the whole
time). In M4 and M5 it was the focus loss itself that produced a pause and let the script go on. For
the script: after a session end wait for the window (`waitwin MainMenu` / `HeistModeMenu`), not for the
scene. For klauto (described, not mine): let `waitscene` succeed at once when the named scene is
already the current one.

### 3.4 What follows

- For the owner: nothing to fix. Alt+Tab pauses the game in the menu and in Arcade; it resumes when
  the window is active again. (Coming back with Discord's overlay on is section 2.)
- For unattended runs while the owner uses the PC (described, not written): a TEST-only switch that
  keeps `[[0xdd2640]+0xb10]` at 1 from the tick while a script runs. It is heap data, outside the hashed
  ranges; the window procedure rewrites it on every focus change, so the tick has to set it again.
  ASSUMPTION: the game runs frames with a lost device - Present then returns DEVICELOST and the render
  thread parks (0x5613ac); not tried.

## 4. Tools

Changed (debug/, mine):

- `debug/log.py`: after the events of the last session it now prints the session states and notes on
  how the run went and ended - a close into 0x2e that does not come from 0x28, a session that never
  left 0x2e, the stretches the window was not in front, a nudge line overdue at the end, and `NO END
  LINE` when the log simply stops. `--all` marks every session without an end line. Before, a hang
  showed as nothing at all: on the 22:13 session the last thing printed was the 22:23:21 achievement.
- `debug/kl.py`: `CALLERS` knows the return addresses that tell the threads apart (main loop, engine
  frame, the render hand-off wait 0x459b20, the pump, the render thread loop 0x56139e, back from Present
  0x7c4c09); `GUESTS` = overlay / recorder DLL names.
- `debug/dump.py` (and `triage.py`): two last lines - which thread faulted (main / render / other, with
  the main thread's position when it is another) and the guest DLLs with their place in the load order.
  On the 17:55 dump: `faulting thread 33104 is the render thread, inside IDirect3DSwapChain9::Present
  ...; main thread 26348: 0x459b20 (MAIN THREAD WAITS FOR THE RENDER THREAD ...)` and
  `DiscordHook.dll 129/131`.

None of the debug tools failed on these logs; they were silent about hangs.

Found in other people's files (not changed):

- `tools/kl_watch.py` took a picture of the owner's **desktop**: `<work>\research\watch\20261009_174356\
  0081_661s.jpg` (17:54:59) shows the Alt+Tab switcher over other programs' windows. Its test "the game
  window is the foreground window" is still true while the task switcher is up and the full-screen game
  is already off the screen. The owner should be told and the picture deleted if they wish; the tool
  should also require that the window is not minimised and that the window at the centre of its
  rectangle belongs to kl2.exe. Other runs were not searched for more such pictures.
- klauto's `waitscene` (3.3).

## 5. How to redo the reading

```
python debug/log.py --all                      # every session; 'NO END LINE' = hang, kill or reboot
python debug/log.py <a copy of one session>    # states, focus stretches, how it ended
python debug/dump.py <dump>                    # thread role and guest DLLs in the last two lines
python debug/dasm.py 87a930 170                # the main loop step (3.2)
python debug/dasm.py 459ac0 d0                 # the wait for the render thread (0x459b1a)
python debug/dasm.py 561330 b0                 # the render thread loop
python debug/dasm.py 418660 f0                 # Arcade quit; 4f9f90 = rules slot 82
ffmpeg -ss 150 -i <the 22:23:48 clip> -an -vf "scale=480:-2,freezedetect=n=0.002:d=0.4" -f null -
Get-WinEvent -FilterHashtable @{LogName='Application'; Id=1000,1001,1002; StartTime=...; EndTime=...}
```
