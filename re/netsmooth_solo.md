# NetSmooth online with one PC: two kl2.exe, one machine (plan, 2026-10-21)

Static reading only; the game was never launched for this. CERTAIN = read in the disassembly (address given) or in code.
GUESS = inferred or untested. Source notes: scratchpad `solo_twoinst.md`, `solo_forced.md`, `solo_steamfake.md`, `solo_route.md`.
Goal: a remote ZFFPlayer replica exists in one Fragile Alliance round, so NetSmooth slot 393 / 0x600eb0 runs online.

## 1. Chosen route: System Link (raw UDP), NOT the Steam lobby

Two routes were on the table.
- Route S (Steam stand-in): fake a second Steam id, an emulated lobby, P2P loopback and callback delivery. About 150 stubs across
  Matchmaking, Networking, User, Apps, Utils and the callback registry. Big, and every layout is a GUESS.
- Route U (System Link over WinSock UDP): the game itself skips the Steam transport. Chosen, because it removes the whole shared-Steam-id problem.

Why route U works (CERTAIN, re-read for this doc):
- 0x5deb50 returns 1 if `[mgr+0x58]==2` or option `MP_RankedGame` (string 0xb41ea0) == 2.
- Net init 0x7ee0c0 calls it at 0x7ee1cf; `jne 0x7ee20b` skips the allocation and `call 0x409c60`, so the SteamTransportAdapter
  is not built (from solo_forced: global 0x1690a4c then stays 0 and the Quazal Socket 0x958e80/0x9590e0 binds a plain WinSock UDP socket, bind at 0x958f65).
- The peer table fed from the lobby (0x4d2a40) only runs when the Steam adapter exists (solo_forced, CERTAIN by its guard).
- The front end "System Link" create (0x77e220) sets game type 4 via 0x5be510(4), then SetMode(2), SetState(8), with no Steam lobby call.
- Therefore two processes on one Steam account are two different network stations. No fake Steam id is needed.
This corrects re/netcode_fa.md lines 342-347 and re/fa_private_match_blueprint.md line 299, which assumed System Link still used SteamSocketDriver.

Why the other routes lose:
- `-o StartAsServer`: CERTAIN no-op (jumps to 0x8734d7, sets nothing). `-o StartAsClient` sets mode 3 (0x873453) but supplies no target and no key exists for an IP or port. Not a bench by itself.
- A second Steam account: owner has none that owns the game (GUESS); also does not remove the mutex or fullscreen problems.
- `+connect_lobby <id>`: needs two distinct Steam ids, so needs route S anyway.

## 2. What still blocks even route U

1. CERTAIN single-instance mutex: 0x47690b `CreateMutexA("KANEANDLYNCH2MUTEX")` through IAT slot 0xb10264; `GetLastError==0xb7` (0x476917) shows a MessageBox and exits.
2. CERTAIN Steam is still needed at start: WinMain calls `SteamAPI_RestartAppIfNecessary(28000)` at 0x476781 (exits if true), then `SteamAPI_Init`, then
   `SteamApps()->vtbl[0]` (BIsSubscribed) into byte [0xdd2614]; 0 shows "SteamInitFailed". GUESS: env `SteamAppId=SteamGameId=28000` on a direct launch makes
   RestartAppIfNecessary return false. GUESS: real Steam lets a second kl2.exe of the same app and account run. This is the biggest unknown.
3. CERTAIN fullscreen exclusive D3D9 (ReShade.log: Windowed=FALSE). Two exclusive devices cannot coexist. GUESS fix: force windowed from a ReShade create_swapchain handler (klreshade.c); no in-game switch was found.
4. CERTAIN unfocused stall: main loop 0x87a930, branch 0x87a963-0x87a988 skips the frame when `[sys+0xb10]` (written by wndproc 0x714810) is set. klauto steps the script from the DirectInput poll, so the unfocused instance freezes.
   The skip is not taken for an online non-Arcade session (0x863a60 && !0x7f6850), so a real round may tick anyway (GUESS for the menu phase). Fix: write 0 to `[sys+0xb10]` every klh_tick.
5. CERTAIN file collisions: KLHook.ini, .log, .result live in the dinput8.dll folder (klhook.c:1036, klauto.c 479/521), so two instances need two folders; kl_autotest.py is single-instance (aborts if kl2.exe runs, swaps files in the game folder).
6. GUESS CEG/DRM IPC (`STEAM_DIPC_*`, `Local\SteamStart_SharedMem*`, handshake 0xa8e690) may collide between two processes.
7. GUESS UDP discovery port 9103 (0x942040 / static init 0xb05ab0) may fail to bind twice (no SO_REUSEADDR found). The listen socket itself (0x96f860) accepts port 0 = ephemeral.
8. Unknown: the System Link menu path is only read from frontend.xml; the discovery receive handler and reply format (solo_forced "unchecked"). GUESS: round content (FA, ZFFPlayer replicas) is identical on game type 4.

## 3. Build steps (in order, cheapest first)

Step 1 (FIRST THING TO BUILD): a hook module `klhook/klsolo.c`, TEST builds only, opt-in `[Solo] Enable=1`. It does:
- Wrap IAT slot 0xb10264 (CreateMutexA) with `klh_iat("kernel32.dll","CreateMutexA",...)` (pattern: klsteam.c / klslot import wrappers). If the name is "KANEANDLYNCH2MUTEX", append the PID. Reuse for the other named objects if the IPC step fails (CreateSemaphoreA / CreateFileMappingA names).
- Each klh_tick: `*(int*)(sys+0xb10)=0` (resolve sys the way the existing klauto/freeze code does; see re/freeze_1009.md 3.2).
- Force `MP_RankedGame` = 2: hook 0x5deb50 to return 1 (a 3-byte patch `mov eax,1; ret` at 0x5deb50, simplest and covers 0x7ee0c0), instead of changing the option store. Check that other 0x5deb50 callers are fine with it (GUESS: they only select the non-Steam path).
- Force windowed, 800x600, from the create_swapchain handler in klreshade.c ([Solo] Windowed=1).
- Log the PID in every KLHook.log line, or run from per-instance folders (below).
Step 2: a runner `tools/kl_solo_test.py` (do not extend kl_autotest): create `inst1`/`inst2` folders outside the game folder, each with TEST `dinput8.dll` and its own KLHook.ini; launch `kl2.exe` directly with env SteamAppId/SteamGameId=28000 and cwd = game folder (junction alternative: GUESS). Ini per instance: `[Auto] Enable=1 Hooks=0 Unfocused=1 BlockReal=1`, `[Net] Log=1`, `[NetSmooth] Enable=1 Log=1 Probe=1`, distinct `[Auto]` script. Collect two logs/results. Never launched by the agent that wrote this doc; the owner must be away (memory: live runs block input).
Step 3: first live run is just "does instance 2 start beside instance 1" (mutex and Steam). If Steam refuses it, fall back to a MINIMAL Steam stub (not route S): fake only Init=true, RestartAppIfNecessary=false, SteamApps BIsSubscribed=true, Utils GetAppID=28000, and no-op the rest (CERTAIN need from the 0x476730 gate; the other interfaces are on the lobby path that route U avoids; GUESS that nothing else on the System Link path calls them).
Step 4: scripted menu route per instance (frontend.xml, CERTAIN where stated in solo_route): `waitwin CampaignMenu`, `tap ESCAPE`, `waitwin MainMenu`, `tap DOWN` x2, `tap RETURN` (Online); the System Link entry sits in the same Online/Play pages (`ZCheckGamerPrivileges Window="SystemLink"`, MP_RankedGame=2; exact key sequence NOT yet read, do a recon run with `windows` / `focus`, because `msg` to an unknown element fails the script). Host: Create. Client: Find, join the listed host.
Step 5 (if discovery fails): patch the 0x942040 port per instance, then as last fallback inject a station URL `prudp:/address=127.0.0.1;port=P` and start JobConnectStation (0x9422d0) (GUESS, deep).

## 4. Test procedure and pass criteria

Run host first, then client after the host's log shows its session line. Both with `[Net] Log=1`, `[NetSmooth] Enable=1 Log=1 Probe=1`.
Pass lines: "session: SERVER (role 2)" and "CLIENT (role 3)"; "remote player ... flags" with bit 2 of `[P+0x2720]` clear; `[P+0x274c]` non-zero; `placed` growing, `skipped` low; vtable swap and give-back; 0 faults on both instances.
Proof that slot 393 runs online: the client sees the host's remote heading follow scripted `mouse` flicks (pos logging). Until then it stays UNPROVEN.
Stages worth separate logs: (a) both start, (b) both reach FALobby/System Link lobby, (c) round loads on both, (d) remote replica exists, (e) NetSmooth probe lines.

## 5. Risks

- GUESS: second kl2.exe under one Steam account refused, or CEG IPC clash. Mitigation: env vars, then per-process object names, then the minimal stub.
- GUESS: System Link round differs from the FA lobby (no FA mode, map choice, ready logic). The test only needs a replica; any map suffices.
- GUESS: a Steam-less start fails CEG checks (nine CEG-named functions exist; IAT slots for Networking, User, Apps, Utils, Friends and callbacks were NOT run through ceg_ranges.py; only UserStats 0xb107c8 and Matchmaking 0xb107d8 were). Do not replace IAT slots beyond the minimal stub without that check.
- Ranked / stats safety: route U never touches Ranked lobbies (MP_RankedGame=2); keep klx's UserStats write guard active; TEST builds only.
- Owner constraint: no live runs while the owner plays. Do not run on the owner's monitor at 2560x1440 fullscreen: windowed forcing is mandatory.
- Not read yet: MPMap readers (0x491f50, 0x6c49a0, 0x6c9c10), JoinWaitTime site 0x4664bd, discovery receive handler, whether the Steam user id is baked into the station identity on the raw-UDP path.

## 6. Live results

### A1 (2026-10-22 00:07, TEST out_3f_1022a_test, `tools/kl_solo_test.py --tag A1`, owner asleep)
Run folder: `<work>/build/klhook/solo/A1/` (inst1/2 logs, shots, run.txt).
- PROVEN: two kl2.exe run side by side from one game folder, started directly (env SteamAppId=SteamGameId=28000, no steam://).
  Mutex renamed (`KANEANDLYNCH2MUTEX_<pid>`), CreateDevice forced windowed (2560x1440 back buffer, 240 Hz -> windowed,
  immediate) -> S_OK, windows placed at 0,0 and 960,0 (960x540), [sys+0xb10] focus write keeps the unfocused one running,
  KLHOOK_DIR gives each its own ini / log / result. Both reached MainMenu under script.
- Corrections to section 3: the focus write is 1 (not 0); per-instance folders come from env KLHOOK_DIR; ForceLan is opt-in (0).
- MENU ROUTE (CERTAIN, window stack): MainMenu, DOWN x2, RETURN = `OnlineMenu`; then DOWN, RETURN = `SystemLink`.
  inst1's own DOWN x2 landed on `ShowAchievements` instead (menu cursor differs per window; GUESS: the real mouse pointer
  hovers over the window at 0,0). The script must check the window name after each step.
- inst1 crashed at kl2+0x43c785 (read [0x8], callers 0x80308d 0x842feb 0x624867 ...) while idle on ShowAchievements, at the
  moment inst2 left its CampaignMenu. Not investigated; keep scripts off the Achievements page.
  - 2026-10-22 static triage (e5, workflow w7eeb892u, read only; KLHook_1/_2.dmp + log):
    CERTAIN: the fault is VA 0x83c785 `mov esi,[edi+8]` on the RENDER thread (thread loop 0x561330), in sprite draw 0x83c320,
    type-5 case 0x83c74c (jump table 0x83d3e4). The entry is a ZRenderEntrySpriteD3D (vtable 0xb99e9c, at 0x3621a6e0). edi is
    the entry's buffer slot R: 0x83c753 `mov eax,[0xef4d80]` (R index), 0x83c758 `mov edi,[esi+eax*4+0x1a4]`; 0x42e1f0 is x87
    only. Slots are filled by the constructor at 0x842eb8 with W=[0xef4d7c]; 0x7c1723..0x7c1728 zeroes slot W of entries with
    [+4]&4 and 0x7c1958 flips R=old W (function 0x7c1610, ZRenderDrawD3D vtable slot at 0xb99df4). No Steam call on the stack,
    nothing from Steam in the log 00:08:03..00:08:10: NOT an achievements / stats-callback crash. Dump 2 shows the same entry
    with new slots, so it is a reused per-frame entry and the dump's R/W say nothing about the moment of the fault.
    CERTAIN: klso_tick forces [sys+0xb10]=1, while stock 0x87a963 returns early (no frame built) when it is 0, so the unfocused
    instance ran a state stock never runs (1755 frames in 10 s unfocused). Commit 547708589's klhook/klauto/klmem changes touch
    no render code; klso_init's Direct3DCreate9 wrapper was not read.
    SETTLED later the same night (3f, see 'Events=1' below): the race is real; its cause is kl2's NAMED render hand-off events,
    shared by both processes. The rest of this sub-bullet is the earlier reading.
    GUESS: a main/render-thread double-buffer race (slot R empty for an entry still listed), exposed by the forced-active
    unfocused window and timed by inst2's first frames (0.45 s after its stall ended). Stock vs hook is UNKNOWN without a control.
    Way on (no patch): check the window name after each key and back out of ShowAchievements at once; let inst2 finish its stall
    before touching inst1; control runs: one instance with [Solo] off parked 60 s on ShowAchievements, and [Solo] on with a single
    process; optional read-only breadcrumb logging [0xef4d7c]/[0xef4d80]. Overlay DLLs in the dump (ReShade32, medal-hook32,
    nvspcap, GameOverlayRenderer) are not tied to it.
  - Controls (2026-10-22, TEST 1022a, `kl_solo_test.py --n 1`, one process, [Solo] on, window unfocused):
    C1 idled 2 min in OnlineMenu: 0 faults. C2 (C_ach.ini) parked 2 min on ShowAchievements (screenshot at 120 s shows the
    list), the focus write active ('window not active' logged): 0 asserts, 0 faults, alive at the end. So the forced-active
    unfocused window plus the Achievements page do NOT crash alone: 0x43c785 needs the SECOND process (its device creation /
    first frames, 0.45 s before the fault in A1). Not yet tried: [Solo] off control (stock can't run unfocused anyway).
    Bench rule from this: start inst2 and let it reach its menu BEFORE inst1 opens any page with sprites; never park on
    ShowAchievements.
  - D2 (2026-10-22 02:36, TEST 1022a, two processes, D_idle2.ini: CampaignMenu -> ESCAPE -> park in MainMenu; inst2 started
    45 s after inst1, i.e. while inst1 was parked): both alive after 240 s, 0 asserts, 0 faults each. Two instances on the
    menus are stable; the A1 crash needs a sprite-heavy page (Achievements) during the other process's start.
- Host / join scripts drafted (2026-10-22 02:44, workflow wf_e36fc046-d86, static from Patch01 menu/frontend.xml + klauto.c's
  parser; NOT run): C:\kl_build_1019\live\solo\H_host.ini and J_join.ini (outside the repo, live folder).
  SystemLink buttons (XML order CERTAIN): Join Game (quick join), Find Game, Create Game.
  Host: SystemLink DOWN DOWN RETURN -> `SystemLinkCreate` RETURN (FA row first: GUESS) -> lobby (`FALobby`: GUESS) -> waits
  100 s for the client -> RETURN (Ready = ZW_SELECT: GUESS) -> waitload -> mouse flicks + pos logs.
  Client: SystemLink DOWN RETURN -> `SystemLinkFindGame` RETURN -> `SystemLinkServerBrowser` (15 s discovery) RETURN -> lobby
  RETURN. Both: `onwin ShowAchievements bail` guard. No Start button exists in the XML: whether Ready alone starts the
  countdown and whether MinNumPlayers allows 2 is open; map = MP_SelectedLevel (F01 default). Also open: two processes
  binding the System Link UDP port 9103 on one PC.
  Run (after the firewall allows kl2.exe): `kl_solo_test.py --hook ..\klhook\out_3f_1022a_test --tag H1 --secs 560 --gap 30
  --base <W02_stockF02.ini> --ini1 ...\H_host.ini --ini2 ...\J_join.ini --shots 60-540:60`.
- H0dry (2026-10-22 03:36, TEST 1022a, H_host.ini / J_join.ini, firewall still blocking, --gap 30): both scripts parse
  (72 / 62 commands), the onwin guard registers. Two NEW problems:
  (1) INPUT STALL: inst1's script stopped at its first DOWN once inst2's window came up (03:36:38 'window not active');
      from then 'rigid: frames 0' = the game no longer runs its mouse/keyboard update in the inactive window, though frames
      continue (~2000 fps). klauto.c's open question 'who clears ZKeyboardWintel +0x54' is now the live blocker.
  (2) inst2 (in front) reached `MainMenu > OnlineMenu > SystemLink > SysUIErrorScreen` and crashed at kl2+0x43c785 3 s
      later (inst1 alive). So 0x43c785 is not an Achievements-only crash: any sprite page with two processes. Workflow
      wf_c4634910-4ea investigates both and builds a [Solo] fix into klhook/out_3f_1022b_test.
- I1 (2026-10-22 03:50, TEST 1022b = commit 20ad71d2a, same scripts): [Solo] InputFix=1 FIXES (1). inst1 logged
  'inputfix: [mgr+0x94] was 1, cleared' at 03:51:11, 0.4 s after inst2 came up (mgr = [0xddb958] ZSysInputWintel, byte
  +0x94 = its disable flag, written by SetEnabled 0x8722d0 on focus loss; the device +0x54 bytes were never 0), and its
  script went on. Both instances walked to `SystemLink > SysUIErrorScreen` and stopped as scripted (exit 26), 0 faults,
  each ~15 s on the error page. Crash A/B (E_err.ini: both park 90 s on the error page; arms baseline / FpsCap=60 / Vsync=1
  / Multithreaded=1, keys in klsolo.c) was refused at 03:55: owner input. Static crash triage (wf_c4634910-4ea): no shared
  named object or file between processes in the render path, no device Reset logged; GUESS main/render race made likelier by
  CPU/GPU contention (both run ~2000 fps uncapped).
- E0a / E0b (2026-10-22 04:37 / 04:44, TEST 1022b, E_err.ini, baseline arm, no cap): E0a inst1 crashed at 0x43c785 22 s
  into the park on the error page, inst2 PASS. E0b inst1 crashed at a NEW site, kl2+0x3c1dcb (reading 0), frame 513, still
  in the menus, the moment inst2 started; inst2 PASS. 0x3c1dcb is in the RENDER THREAD's command-list player 0x7c1c30
  (caller 0x56139e, loop 0x561330; main thread waits for it at 0x459b1a): the command at ebp=0x1fce8f30 is ALL ZEROS
  (opcode 0, object [+0xc] = NULL), i.e. a list entry counted but never written. Same family as 0x43c785 (render thread, null
  object): supports the main/render race GUESS. Guest DLLs in both: ReShade32, GameOverlayRenderer, nvspcap, medal-hook32.
- Idle check fooled by the game itself: 0x6f4220 calls mouse_event(MOVE,0,0) while its window is in front, which resets
  GetLastInputInfo (E0a: nudge passed 04:37:43, "owner input" 04:38:39). The bench sets [Load] NudgeMs=86400000, but
  klnudge.c clamped anything over 60000 to 0 = slot NOT wrapped = a nudge every frame (E1a refused 04:46:46). Fixed in TEST
  1022c (commit 8395d9e: max 24 h). Arms rerun on 1022c: E0d baseline, E1a FpsCap=60, E0c, E1b, E1c.
- E0d (04:51, 1022c, baseline): 0 faults in both; inst1 bailed onto ShowAchievements (its menu taps overlapped inst2's start;
  gap now 45 s). Each instance still passed ONE nudge, its first call (timer started at 0): fixed in 1022d (klnudge first call
  held too).
- E1a (04:57, 1022d, [Solo] FpsCap=60 in both): inst1 PASS, inst2 CRASHED at 0x43c785 at frame 1720 (~29 s at 60 fps). The
  frame cap does NOT prevent it: the CPU-contention form of the race GUESS is weakened. Next arms: Vsync=1, Multithreaded=1.
- The idle check is still reset once per instance start by the game's own SetCursorPos to the window centre (window set-up
  0x56bae0; other callers 0x41e946, 0x6f4285). A [Solo] wrap of that import was REFUSED by the permission classifier (seen as a
  way round the owner-idle check) and is not built; the arms script instead waits for 310 s idle before each arm.
- CAUSE FOUND (static, workflow wf_9f76e0ce-f97, two readers + a verifier, 2026-10-22 05:05): 0x7ebbe0 creates the render
  hand-off events with CreateEventA (slot 0xb10228) and fixed NAMES - RenderThreadInit S+0x11b8, RenderThreadEnd +0x11bc,
  UpdateRenderState +0x11cc, DrawBegin +0x11c0, DrawEnd +0x11c4 (manual reset), DeviceUpdate +0x11d4, ResetDevice +0x11d0
  (S = [[0xdd2640]+0x970]). Two kl2.exe in one session share them: one process's render thread SetEvents the other's main
  thread awake (and auto-reset events swallow signals), so main resets list [renderer+0xa8690-4*sel] (0x7c17e9: count 0,
  end = begin) and flips the sprite set [0xef4d7c]/[0xef4d80] (0x7c1728 zeroes slots) while its render thread still plays
  them. The player 0x7c1c30 ends only on ebp == end (0x7c48f5 jne), walks into zeroed memory -> 0x7c1dcb; the sprite draw
  reads a recycled slot -> 0x83c785. Render loop: 0x561330 Wait(DeviceUpdate) / SetEvent(DrawBegin) / 0x7c1c30 /
  SetEvent(DrawEnd); 0x7c1c30 SetEvents UpdateRenderState at 0x7c1cad; main waits it at 0x7c17d0 and DrawEnd at 0x459b1a.
  This explains 'two processes only' and why FpsCap did not help. FIX: [Solo] Events=1 (klsolo.c, TEST 1022e) wraps
  CreateEventA/W (import page, not hashed) and appends _<pid> to exactly those seven names (Steam's own events untouched).
  Rejected: patching 0x7c48f5 / 0x83c785 (hashed), vtable swaps at 0xb97fc8 (hashed). Live proof: arms F0a-F0d.
- PROVEN LIVE (2026-10-22 05:09-05:30, TEST 1022e, E_err.ini, no cap, gap 45 s): F0a, F0b, F0c, F0d = 8 of 8 instances PASS,
  0 faults; each log names all seven events '_<pid>' (DrawEnd manual reset 1, as read) and both stood on SysUIErrorScreen
  together. Same bench without Events (E0a, E0b, E0c, E1a, E0d, earlier H0dry): a crash in 4 of the last 6 runs. [Solo]
  Events=1 is the default; the bench is stable for host / join once the firewall lets System Link through.
- G0a / G0b (2026-10-22 06:36-06:45, TEST 1022e, base W02_stockF02.ini, no script override): BOTH instances load stock
  Bridge offline at once (Arcade, 45 s apart) and play the sweep input (walk, sprint, fire, reload, aim): 4/4 PASS, level_loaded=1,
  0 asserts, 0 faults. Two processes rendering a 3D level side by side are stable with Events=1.
  G1a (W10_DM01.ini, slot F01) / G1b (W14_DM09.ini, slot F06), 07:36-07:45, same set-up on two Dead Men maps: 4/4 PASS, 0 faults.
  G2 (08:36-10:09, the other 16 sweep inis W01-W19): 32/32 PASS, level_loaded=1, 0 asserts, 0 faults. So all 19 FA maps (9 stock,
  10 Dead Men) run in two processes at once.
  K0a soak (10:36-10:48, live/solo/K_soak.ini, Bridge held ~8 min): both rounds ended early on the score page (idle player
  killed: inst1 after ~3 min, inst2 ~7 min, 132,267 frames), both PASS, 0 asserts, 0 faults.
- PORTS ON ONE PC (static, workflow wf_7818ce5f-935, 2 readers + verifier, 2026-10-22 05:50): no fix needed IF the host
  reaches Create Game before the client reaches Find / Join. Discovery socket (ctor 0x968320 -> 0x967ef0) binds UDP 9100 and
  falls back to an ephemeral port (0x967f30), host and client alike: the FIRST process keeps 9100. Host station socket
  0x9498d0 -> 0x957370 binds 9103 strictly (failure = error path 0x949937, Create Game error state). Client JoinSession 0x948450
  -> 0x957b50: 9103, else ephemeral (0x9573e0). Find Game broadcasts to 255.255.255.255:9100 ([0x1691530], word [0xd42600])
  via 0x9680f0 -> WSASendTo; the 9100 owner answers. Plain bind at 0x958f65, no SO_REUSEADDR (do not add one). Wrong order =
  silent 'no games found'. GUESS: Windows delivers the local broadcast to the other process; the client does not drop a host
  with its own IP. Only if order-independence is ever needed: a TEST wrap of the ws2_32 bind slot 0xb106e8 that gives inst2
  port 0 for 9100 / 9103 (not built).
  Run once the firewall allows kl2.exe: `python tools/kl_solo_test.py --hook ..\klhook\out_3f_1022e_test --tag H1 --secs 560
  --gap 45 --base C:\kl_build_1019\live\sweep\W02_stockF02.ini --ini1 C:\kl_build_1019\live\solo\H_host.ini --ini2
  C:\kl_build_1019\live\solo\J_join.ini --shots 60-540:60` (from tools/).
- BLOCKER: SystemLink opens `SysUIErrorScreen` "This game is blocked by a firewall" (string Online/BlockedByFirewall, 0x51dcd0).
  Check: GetModuleFileNameA -> 0x5cce20 -> 0x8945d0: CoCreateInstance(NetFwMgr) via 0x7232d0 (import 0xb1079c), LocalPolicy,
  CurrentProfile; passes when get_FirewallEnabled = FALSE or the exe's AuthorizedApplications entry is enabled. Network profile
  is Public. Both functions are hashed. A hook-side stand-in for that COM class was REFUSED by the permission classifier
  (security weakening) and is not built. The way on is the owner's: allow kl2.exe in Windows Firewall (Allow an app through
  firewall, Private and Public), then rerun with the same script past SystemLink.
  SOLVED 2026-10-22 by the owner (kl2.exe allowed, Public profile included).
- H1 (2026-10-22, TEST 1022e): FIRST TWO-PROCESS SYSTEM LINK. Host created an FA game, client found and joined it, both went
  Ready ("Players connected: 2"), but the round never started: the lobby's "Number of players" (minimum, [sm+0xb9]) stood at
  6 and the menu's LEFT stops at 4 (0x7dc519). 0 faults.
- Fix: klhook/kllobby.c, `[Lobby] MinPlayers=N` (1..8): while HOSTING an FA lobby (role 2, game type 4, state 0xd / 0xe) the
  byte is held at N (data write, SHIP-safe). The engine's own setter 0x739f20 clamps only to [connected, 12].
  0x5d4920 (msg 0x86) is NOT the start check: it is the FAQuitLobbyConfirm path. Likely start site 0x5067c7: min <= connected
  -> 0x464750(1).
- H2 (2026-10-23 01:21-01:26, TEST 1022f, H_host.ini with [Lobby] MinPlayers=2): `lobby: minimum players 6 -> 2` at the host's
  lobby; client Ready 01:23:27 -> both instances state 0xd -> 0x12 at 01:23:41 (BEFORE the host's own Ready press, scripted
  for 01:24:06) -> 0x14 / 0x16 / 0x17 / 0x19: both load F01 (Subway) and play the same networked round (screenshots: two
  different heisters, LOOT AREA prompt). Both PASS, 0 asserts, 0 faults; the owner's dll was restored (09b322a1).
  NetSmooth did NOT switch on: its gate (and klnetfix's) only accepts the service vtable 0xbd597c ZOnlineServiceSteam. RTTI:
  0xbd5ad4 ZOnlineServiceWintel is its subclass (stamped at 0x4ed61c / 0x6c9b18; overrides slots 0, 40, 45 JoinSession,
  69-71). GUESS: System Link runs on Wintel. TEST 1023a accepts both and logs the vtable of any refused in-range session (H3).
- H3 (2026-10-23 01:28-01:32, TEST 1023a): System Link round on F01 again, both PASS, 0 faults. NetSmooth SWITCHED ON in both
  (no "session refused" line, so the Wintel guess holds): `15 remote player object(s) swapped` on each (16 slots, the local
  one skipped), the private slot 393 ran (host 24,440 updates, client 8,387), no chain failure logged (the online chain
  P -> [P+0x274c] -> [R+0x540] -> body resolved), but `placed 0, skipped 0`: no body ever changed heading. The probe agrees:
  every body stayed at yaw -90 / +90 for the whole round, and `pos` read heading 0 throughout. The host's scripted mouse turned
  only its camera; a STANDING body does not follow the camera (klauto.c's note on +0xc14). Write path online: still unproven.
  Next, H5: H5_host.ini holds W while turning (steps 47-59) so the host's body heading changes on the client.
- kllobby redesign (TEST/SHIP 1023b): H2's version held the target at MinPlayers from the lobby on, which also closes the join
  gate (slot 49 refuses a peer once target <= connected) - a 3rd player would have been turned away. Now nothing is written
  until the HOST presses Ready (state 0xe); then, with >= MinPlayers connected, the target drops to the number connected.
- H4 (2026-10-23 01:34-01:38, TEST 1023b): client Ready 01:35:46 (state 0xe) and NO start for 38 s; host Ready 01:36:24.4 ->
  `lobby: host Ready with 2 connected: target players 6 -> 2` -> state 0xd -> 0x12 at 01:36:25.1 (0.6 s) -> both load F01
  and reach 0x19. Both PASS, 0 asserts, 0 faults. NetSmooth swapped 15 remote objects on both again.
  In play: [Lobby] MinPlayers=2 (or 1) in the HOST's KLHook.ini; everyone presses Ready, the host last; the round starts.
- H5 (2026-10-23 01:39-01:43, TEST 1023b, H5_host.ini: the host holds W while turning, steps 47-59): FIRST ONLINE SMOOTHING.
  Host `pos` heading 0 -> -85 -> -61 -> -164 -> 14 while walking (a walking body follows the camera). On the client the
  probe saw the host's remote body at yaw -90 / -104.1 / 58.4 / 97.0 and NetSmooth `placed 1720` (01:41:49-01:42:09, the
  walk), skipped 0 (every remote matrix was the pure mirrored-yaw form), no chain failure, 0 faults; the host placed 0
  (the client stood still). Both PASS. Write path through B->vtbl[0x8c] online: PROVEN. Whether it LOOKS better is
  the owner's call (stills cannot show it).
