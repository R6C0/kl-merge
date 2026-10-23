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
  Run once the firewall allows kl2.exe (2026-10-23: use TEST 1023b or later, which has [Lobby] MinPlayers; 1022e stops in the
  lobby at 6 players, H9fw): `python tools/kl_solo_test.py --hook ..\klhook\out_3f_1023r_test --tag H1 --secs 560
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
- Static reading (2026-10-23, workflow read + refute, nothing run) of where a remote body's heading comes from:
  - Receiver 0x600eb0 (via 0x4a1890; R = [P+0x274c], P' = [R+0x540]): on the main path it builds a pure Y rotation from
    int16 [R+0x60] (m_Angle, /162.97 = 1024 units per turn, refreshed by 0x519e80) and calls B->vtbl[0x8c] at 0x60191e EVERY
    frame. No call on: [P'+0x2760]>0 or [P'+0xd5c]!=0 (0x601938), vtbl 0x1c8/0x3d0 true, session state not 0x17/18/19/1f,
    or the far-distance teleport (0x60157a -> 0x5f21c0). Other 0x8c callers: [P'+0xd50] (0x600ff5, animation pose), [P'+0xd58]
    (0x6011bc). vtbl 0x5d8 == 8 exits only when 0x544fb0 is also true.
  - Sender 0x6300f0: m_Angle = yaw of the sender's BODY matrix [B+4] (0x429ff0 atan), not the camera. If [P'+0xd50] != 0
    (0x63014c) it sends only the aim point (R+0x170) and never updates m_Angle.
  - Camera yaw is a separate dataset m_CamAngle (int16 [R+0xe0]; sender 0x789820 from [P'+0x2808], receiver 0x5d31c0 writes
    [P'+0x2808] and clears mask 0x08 of [R+0x548]). NetSmooth does not touch it. If the owner still sees "spinning" upper
    bodies online, that is this path (or the aim point), and it needs its own smoother at 0x5d31c0 or at [P'+0x2808]'s readers.
  - H5 fits: walking turns the body, so m_Angle changes and slot 393 sees it. Standing players send no heading change.

## 7. Cloud static reading, 2026-10-23 (a): MPMap readers, JoinWaitTime, discovery receive, station identity

Static only (capstone over kl2.exe 0490 in the cloud, nothing run). CERTAIN unless marked GUESS.
Summary (10 lines):
1. `-o MPMap` is a key in the engine option store `[0xe05568]` (0x793550 -> vtable slot 36 of that object, args (name, 2)); the value is written only at CREATE (0x6c9c10, 0x6c9f14 -> `[sm+8]`).
2. On the other three sites the VALUE is ignored: the option's mere presence makes the code load the HOST'S replicated map name `D+0x230` (m_szServerMap, DDL dispatcher 0x5a7580) instead of the level-list slot.
3. Client 0x491f50: MPMap present -> `[sm+8]` = D name (0x491fb0); else game type 4 -> levellist slot 15(index), type 2 -> slot 16. Same in 0x89fa20 (0x89fb10) and in the host state machine 0x6c49a0 (0x6c534c).
4. So a JOINER launched with `-o MPMap=anything` follows whatever name the host replicates: a map-sync lever that needs no patch (GUESS: whether D+0x230 is filled from the host's `[sm+8]`; its writer was not found).
5. JoinWaitTime: ZSessionManagerMultiplayer slot 1 0x466350 (runs once, flag `[sm+0x78]`), `atoi` -> `[sm+0x154]` (0x4664d8). No reader of `[sm+0x154]` was found by three sweeps: the option is dead until one is found.
6. System Link discovery is Quazal `LANSessionDiscovery` (vtable 0xbdbb24): open 0x967ef0 binds the port word `[+0x1c]` (= `[0xd42600]`, 9100, set by slot 9 0x968230) and falls back to port 0; it registers a `DiscoveryStream` (vtable 0xbdbb14) with the socket driver's dispatcher (0x95f2f0 at driver+0x4d0).
7. Receive: DiscoveryStream slot 1 0x967c90 -> LANSessionDiscovery slot 8 0x968460 -> 0x9682c0: first dword = message type; 1 -> 0x968150 (HOST answers a Find), 2 -> 0x967e10 (CLIENT records a reply).
8. 0x968150 answers only if `[[disc+8]+0x79]` and (`[+0x78]` or global byte 0x169152c) (GUESS: 'session open / joinable'); the reply (0x967da0: type 2, the request's 64-bit query id, then the owner's StationURL `[[disc+8]+0x3c]` serialised by 0x9479d0) goes to the request's source address and port (0x93f300 / 0x93f3d0).
9. 0x967e10 drops a reply whose id != `[disc+0x18]` (the id made at Find time, 0x96828e, from 0x9710c0: GUESS a time stamp), parses the StationURL (0x947e10), stores the sender address and the "LAN" tag (0x947780 / 0x9477b0), and adds the entry (0x97a0e0 -> 0x96a060, dedup on `[entry+0x28]`).
10. Station identity on route U is the StationURL (address, port, sid): no Steam id. The URL key "PID" (0xbd682c) has no code user; sid is set to 1 (0x93f630 at 0x9645e4 / 0x96b2bf / 0x96b981). The client join handler ZSessionHandlerClient slot 95 0x758e90 skips its whole Steam-id member loop (0x758f06..0x758ffa, `SteamUser()->GetSteamID` compared per lobby member) when 0x5deb50 says System Link (0x758ef9 `jne 0x758ffd`) and joins by the URL string alone (0x877b90).

Detail and evidence:
- Option store: 0x793550 = `0x7ee640(name)` on the .data object 0xe05568 (vtable +0x90, arg 2). GUESS: a hook could set `MPMap` at run time through it (data, nothing hashed) - not attempted.
- Create 0x6c9c10: 0x6c9ee1..0x6c9ef6 `[sm+8]` = levellist slot 15(`[sm+0xbf]`) via 0x4e7da0 (0x40-byte copy); 0x6c9f0b MPMap, if present 0x6c9f1b overwrites `[sm+8]` with the option VALUE.
- 0x491f50: 0x491fa1 asks MPMap, 0x491fb0 re-reads the D name (the option value `[esp+0x10]` is never used), 0x491fd1 / 0x492001 are the slot-table variants.
- 0x6c49a0 (host): 0x6c533d MPMap -> 0x6c534c D name -> 0x86f230; 0x6c536f slot 15. 0x86f230 ends in DB slot 29 (0x86f2c8), the pending-scene request (private_match.md 2026-10-23).
- JoinWaitTime readers searched: every `[reg+0x154]` in the 28 sm vtable functions, in the 187 functions called with ecx = `[0x168e598]`, and every site whose base was loaded from that global within 40 instructions: only the write 0x4664d8. The ctor 0x7d69b0 sets no default (GUESS 0).
- Steam id on the wire: `DDL_ZClient` has a 64-bit `m_iOnlineServiceID` at client+0x180 (0x8da640). Writer and reader NOT found; GUESS it is the Steam id (ZOnlineServiceSteam slot 5 0x4139a0 formats one as "%llu"), so two instances of one account replicate the SAME id: anything keyed on it is the residual risk of route U.

Live confirmation: (1) a joiner with `-o MPMap=x` logs `[sm+8]` after state 0x13 (expect the host's name); (2) JoinWaitTime=N changes nothing; (3) `[Net] Log=1` on the client shows the found entry's URL (address:port), no Steam id; (4) both instances' client+0x180 are equal and nothing breaks.

## 8. Cloud static reading, 2026-10-23 (b): the AI-actor receiver 0x569eb0

Summary (10 lines):
1. 0x569eb0 is NOT virtual: its `this` is a `DDL_ZFFActor` (vtable 0xbd493c, made by the factory `_DOC_DDL_ZFFActor` slot 3 0x75d3d0 -> ctor 0x4a9d60), the actor's Net-Z duplicated object. That is why RTTI never found an owner.
2. Links: `[actor+0x8d8]` = the DDL object N (0x78d930 sets it, 0x424350 reads it); `[N+0x2a0]` = the owner ZFFActor A (0x5d0740 sets it). Mirror of the player pair `[P+0x274c]` / `[R+0x540]`.
3. Reached every frame from ZFFActor slot 87 0x40ef60 at 0x40f3d1 (`0x6b8380([A+0x8d8])` -> 0x82b7f0) when `[N+0x2a0]` is set, the object is NOT owned locally (0x9425a0) and the session state (0x8e6a20) is 0x19 = in round; also once at bind time from the session-handler slots 44/45/47/48 through 0x5d0740.
4. Gates inside: throttle `[N+0x2d0] < [sys+0x48]` (else 0x71ba00), A's vtable slot 244 false, `[N+0x20c]` == 0, `[[A+0x88]+0x13]` == 0, 0x53c080() false, `[A+0x5b4]` == 0, and (unless 0x575100()) `[[A+0x7c0]+0x7c]` != `[[0x1549040]+0x18]` (GUESS: not controlled by the local client).
5. It samples two datasets with 0x519e80: heading at N+0x58 (int16 at +0x60, / 162.97 = 1024 per turn, the players' constant 0xb78bc8) and position at N+0x110 (int16 x,y,z at +0x118/0x11a/0x11c).
6. Writes: A+0x90c = the packet position as floats (0x56a07b..0x56a088); A+0x918 = the same after a ground probe (DB `[+0x8c]` slot 153 ray at 0x56a1a5, used when the height error |dy| < 0.005 at 0x56a12e; GUESS: 'snap to floor').
7. The heading is turned into a matrix (0x589440, GUESS rotation from yaw) but that matrix is only used by ONE call: A's vtable slot 343 = 0x7084c0 -> 0x6d0240 -> `B->vtbl[0x94](mat, pos)` with B = 0x598460(`[A+4]`) = the same body chain NetSmooth uses, slot 37 instead of the players' slot 35.
8. That call is gated at 0x56a202..0x56a215 on |pos| >= 1,000,000 (0x42e1f0 = vector length, double 0xb49b40) or NaN: in practice never (positions are in the thousands). GUESS: a sentinel for 'not yet placed'.
9. So on a client the receiver does NOT place the AI body from the raw heading each frame; it only refreshes target positions (A+0x90c / A+0x918) that the actor's own movement code consumes (consumer not identified by this pass). There is no per-packet heading snap to smooth: NetSmooth's body-chain smoothing does not apply to AI heisters and is not needed for them.
10. If an AI body still looks jerky online, the lever is elsewhere (the actor's steering toward A+0x918, 0x7b3020 / 0x70f660 on the dead-reckoning branch at 0x56a0b5), not slot 37.

Evidence notes: 0x82b7f0 reads `[this+0x2a0]`, calls 0x9425a0 (ownership: `[obj+0x14]` vs local station, re/private_match.md) and 0x8e6a20 (session state) before 0x569eb0; the session handler keeps 12-byte {N, A, state} entries at `[handler+0x20]` (0x7ded70 unbinds both ways: 0x78d930(A, 0) then 0x5d0740(N, 0)). 0x5d0740 initialises the datasets at N+0xf0 / +0x110 / +0x58 (0x753dd0 / 0x7fb7c0 / 0x6adff0) with the owner as argument. Dead-reckoning branch: 0x82fd20(N+0x240) true and DB slot 30 (`[db]+0x78`) false -> 0x7b3020(`[A+4]`, zero vector) and 0x70f660, then return (GUESS: freeze the body while extrapolating). Not read: 0x589440's exact matrix layout, slot 37's meaning vs slot 35 (GUESS teleport vs place), 0x4eca40 / 0x4188e0 / 0x5f3a60 (an object of A that, when valid, skips the receiver entirely: GUESS the vehicle or climb that owns the position).

Live confirmation: `[NetSmooth] Probe=1` extended to log, for each remote ZFFActor in an online round, A+0x90c, A+0x918 and the body yaw per frame: the yaw must change smoothly between packets while A+0x918 steps; a slot-37 call should never be seen (a TEST-only read-only wrap of `B->vtbl[0x94]` would count them).

## 2026-10-23 10:30 - LIVE: the firewall is open; the lobby waits at "Number of players: 6" (cloud session, from the owner's photo)

The owner added the Windows Firewall rules at 10:06 and the bench then reached a Fragile Alliance LAN lobby in both
instances: "Players connected: 2 / Waiting for players...", Location Subway, Number of players 6, Heist time 4,
Rounds 3, both players "r6kxo", Ready buttons showing. So System Link discovery + join WORK on one PC. Two things seen:

   UPDATE 10:50 (local): the photo is H9fw (10:21-10:27), run on TEST 1022e as section 6's old command line says; 1022e
   predates kllobby.c, so the lobby kept MinNumPlayers 6. Key stepping cannot reach 2 anyway: the menu's LEFT stops at 4
   (0x7dc519, H1). H_host.ini already has [Lobby] MinPlayers=2; run the bench with TEST 1023b or later (H4 / H5 / H8 PASS).
   UPDATE 10:36: the local session already has it: the hook logs "lobby: MinPlayers=2 - a hosted FA lobby starts on
   the host's Ready once that many are connected" (10:28, 10:32, both runs PASS). A data write beats the key stepping
   below; keep this entry only as the explanation of what the photo showed.
1. **The round cannot start because "Number of players" is the MINIMUM (re/menus.md 387: the row is
   `MinNumPlayers`), stock 6, and only 2 are connected.** H_host.ini presses Ready without lowering it. The lobby rows
   are stepped by `LobbyArrowL_1..4 / LobbyArrowR_1..4` (menus.md 216); which row index the players count is, and
   whether LEFT on that row goes 6 -> 5 -> ... -> 2 (or whether 2 is allowed at all: the level property
   `LobbyMinNumPlayers` at 0xb284d1 and the replicated `m_iMinPlayers` / `m_iMaxPlayers` of netcode.md 581 bound it),
   is for the next recon run: `windows` / `focus` on the lobby, then LEFT x4 on the row, read the row's text, then
   Ready on BOTH instances. GUESS: the order of the rows is scenario, players, time, rounds (the XML order of
   LobbyInfoScenario / MinNumPlayers / TimeLimit / NumberOfRounds), so the players row is the second.
2. The lobby says "Subway": expected. The redirected map is the Dead Men one (klslot [Redirect] F01 -> DD01) but the
   lobby's level toggler only has the nine stock names and pictures (menus.md 387, klslot.c KNOWN LIMITS). Own
   names and pictures per expansion map = the roadmap's "Custom map previews" (Patch01.zip XML + one picture each):
   separate work, not a bench blocker.

## 9. OWNER 2026-10-23 10:36: "need to test it on custom match too" (the Steam online path)

What the bench has proven so far is System Link (route U, raw UDP): discovery, join, a 2-player lobby. A CUSTOM MATCH is the
other route: Online -> Create Game, a Steam lobby (CreateLobby +0x30, type from [Net] PrivateLobby: re/private_match.md 7)
and Steam P2P transport (the adapter 0x7ee0c0 builds when 0x5deb50 says "not System Link"). Different code on both sides
of the wire, so the LAN result does not cover it. It cannot be done with two kl2.exe on ONE Steam account (section 1,
route S was rejected for that reason: both instances would be the same station on Steam, GUESS-level risk even if the
lobby let them in). Three ways to get a second Steam identity, in order of cost:

1. **Two PCs, two accounts (the real thing).** Josh plus one friend, both with the SAME map build (private_match.md
   2026-10-23: same build of the current round's map; the cap and ids are rebuilt per map). Hook: SHIP build,
   [Net] PrivateLobby=1 (FriendsOnly: friends see it in the server browser, Public clients do not), [NetSmooth] on,
   [Net] Log=1 on both. Host: Online -> Create Game -> FA -> the expansion map's slot -> Ready. Joiner: Online -> Find /
   Join Friend from the Steam overlay. Read: the P2P connect lines (1202 / 1203 callbacks, private_match.md 8), the
   firewall line (Steam P2P uses UDP too: the new rule covers it), MinPlayers=2 from the hook, and the NetSmooth
   probe once in the round. This is the test that matters for the Discord group.
2. **One PC, a second Steam account in Steam Family / a second Steam install.** Steam does not run two clients on one
   Windows session; a second account needs a second user session (Windows "switch user" with its own Steam) or a VM
   with its own Steam login: heavy, and Family Sharing locks the game when the owner plays. Not recommended.
3. **One PC, one account, the Steam stand-in (route S).** The 150-stub emulation the bench rejected. Not worth it
   while (1) is available.

So: (1). What the cloud / local sessions can prepare without the second PC: the SHIP build with PrivateLobby, a one-page
sheet for the friend (install the same KLExpansion folder + hook, same build hash: tools/kl_netcheck.py says SAME SLOT
ORDER for two map zips), and the log lines to collect. Owner: who is the second player, and when.
