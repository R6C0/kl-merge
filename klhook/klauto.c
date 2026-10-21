/*
 * klauto.c - unattended load tests for Kane & Lynch 2: Dog Days, on top of KLHook (klhook.c).
 *
 * WHAT IT ADDS TO THE dinput8.dll PROXY (everything is off unless KLHook.ini has [Auto] Enable=1)
 *  1. Scripted keyboard: IDirectInput8 / IDirectInputDevice8 are wrapped; a script from KLHook.ini is
 *     fed to the game through the keyboard's GetDeviceData (and GetDeviceState, should it be polled).
 *  2. Breadcrumbs in KLHook.log: scene load start / end, the engine's own loading progress (stage and
 *     percent), every entity (and optionally controller) the node loader reaches, the loader phases
 *     after the nodes, and the post-load init stages. Every assert / fault gets a "where:" line.
 *  3. Faults in ANY module (module name + offset), C runtime fatal paths of MSVCR90, an unhandled-
 *     exception filter that ends the run, and a watchdog (no progress for StallMs, or MaxRunMs).
 *  4. KLHook.result (key=value, rewritten atomically) and a process exit code for a driving script.
 *  5. Engine ini lines without a command line: the baked ini text the exe parses is extended in memory.
 *
 * BUILD: this file is the TEST half of KLHook. klhook.c includes it when KLHOOK_TEST is defined
 * (build_auto.bat: cl /DKLHOOK_TEST klhook.c); a SHIP build (build.bat) does not contain it. Compiling THIS
 * file on its own still gives the TEST build (it defines KLHOOK_TEST and includes klhook.c, which includes it
 * back). klhook.c owns DllMain and DirectInput8Create and calls kla_init(inst) / kla_di8(o); klfix.c and
 * klslot.c are there in both builds. It uses klhook.c's dir, klog, write_dump, log_context, img_lo, img_hi,
 * dumps, max_dumps, MDWD, MEI, and - for EVERY write into the game - the patch guard (klh_poke / klh_data):
 *   [KLHook] SessionSafe=1 (default)   a detour, the vtable entry or the [Engine] operand that lies inside a
 *                     range kl2.exe's integrity checks hash is REFUSED (logged 'patch REFUSED'): of the
 *                     seventeen detours only NODE, CTRL, SCNBLK, REFFIX and GINIT go in, and there is no
 *                     'LOAD start / end' wrapper. This is what a run that starts a session may use.
 *   [KLHook] SessionSafe=0             everything goes in, as before: for direct-boot runs (DefaultScene) only.
 *   The table of all sites with the range checker's verdict is in klhook.c's top comment.
 *
 * KLHook.ini
 *   [Auto]
 *   Enable=1          master switch (0 = this file does nothing at all)
 *   Hooks=1           patch the breadcrumb sites into kl2.exe's code (in memory, bytes verified first)
 *   Detours=          with Hooks=0: install ONLY these detours (names of the site table, comma separated:
 *                     NODE,CTRL,PROG,GEOMS,SCNBLK,REFFIX,ROOM,GBUF,REFEND,POST,GINIT,CLIST,CINIT,OPENWIN,ELFOCUS,
 *                     FOCUS,INPUT). For the anti-tamper experiments X3 / X5 of re\antitamper.md section 8.
 *   VtLoad=1          with Hooks=0: install ONLY the scene-load vtable entry 0xb8fa24 (experiment X4)
 *   LbFix=1           (default 1) the leaderboard row count fix; now klfix.c, in SHIP and TEST ([KLHook] LbFix).
 *                     0 = only log the value found.
 *   EndHooks=1        with Hooks=0: wrap the five exit import slots anyway (the 'integrity exit' tripwire, X1)
 *   Nodes=1           0 remember the last entity only, 1 log every entity, 2 also every controller
 *                     (40,000 entities with a controller each = 4.2 MB of log, 0.1 s; measured off-game)
 *   StallMs=60000     no hook hit and no input frame for this long -> FAIL stall (0 = off)
 *   MaxRunMs=0        total run time limit -> FAIL maxrun (0 = off)
 *   LoadedMs=0        a level (scene name without "kaneandlynch") finished loading and frames kept
 *                     coming for this long -> PASS and exit (0 = off)
 *   Unfocused=1       while a script runs the keyboard reports DI_OK even when the real device is
 *                     not acquired (window not in the foreground)
 *   BlockReal=1       while a script runs, drop the real keyboard's events and zero the mouse
 *   FirstChance=1     log first-chance faults raised in modules other than kl2.exe
 *   CmdDrop=          comma-separated engine keys whose "-o <Key>=<value>" pair is blanked out of the
 *                     process command line (in memory, before any game code runs). WHY: "-o" lines are
 *                     parsed AFTER the baked text and a later key replaces an earlier one, so [Engine]
 *                     cannot override a key the Steam launch options give. The owner's options force
 *                     DefaultScene=Locations/F01/F01_Main.gms and AutoExit=120; a run that must start in
 *                     the menu uses CmdDrop=DefaultScene,AutoExit and gives AutoExit under [Engine].
 *                     Steam's settings are not touched; with Enable=0 the options act as before.
 *                     Verified by disassembly: the exe's startup passes *MSVCR90._acmdln to WinMain
 *                     (0xa8daaa -> 0x58ff90) and has no GetCommandLineA of its own. ASSUMPTION (not
 *                     run): _acmdln is GetCommandLineA()'s buffer, as in the CRT's sources. The read-
 *                     back is the "input: DirectInput8Create wrapped; scene='...' AutoExit=..." line:
 *                     it must name the frontend scene and the [Engine] AutoExit.
 *   CmdAdd=           text written into the stretch CmdDrop blanked, e.g. "-o DisableSplashScreens -o AutoExit=900".
 *                     Without such a stretch (launch options that have no pair to drop) the text is appended in a
 *                     buffer of the hook's own and GetCommandLineA / MSVCR90._acmdln are pointed at it (kla_cmd_append).
 *                     The way to give engine keys without touching kl2.exe's code (see ANTI-TAMPER below).
 *   Forbid=           comma-separated texts; a scene whose name contains one is never loaded: the run ends
 *                     as FAIL just before (needs Hooks=1). "Forbid=Locations\L" keeps a wrong menu key from
 *                     starting the story.
 *   [Engine]          lines appended to the exe's baked ini text (same effect as "-o <line>"). PATCHES CODE:
 *                     not for a run that starts a real session (ANTI-TAMPER)
 *   1=AutoExit=180
 *   2=DisableSplashScreens
 *   [Script]          one command per numbered key, read until the first missing number
 *   1=waitscene kaneandlynch 120000      wait until a scene whose name contains the text has LOADED
 *   2=wait 4000                          milliseconds
 *   3=tap RETURN                         tap <key> [hold ms, default 80]; also: down <key>, up <key>
 *   4=frames 30                          wait for that many keyboard polls
 *   5=waitload 240000                    wait until a level (not the frontend) has loaded
 *   6=log reached the level              text into KLHook.log
 *   7=pass 5000                          wait, then end: PASS if no assert / fault was seen
 *     also: fail <text>, quit <exit code>
 *   8=msg HeistLevel StartGame           send a menu message to a named GUI element of the open page,
 *                                        the way a <GuiElement Type="SendMessage" Receiver= Message=>
 *                                        does (ZSendMessage slot 10, kl2 0x869ac2-0x869aea: element =
 *                                        0x83faf0(name) on the menu manager [[0xdd265c]+0x824], then
 *                                        element->vtbl+0x50(&text)). 'HeistLevel' + 'StartGame' is what
 *                                        the gamepad layout's Accept sends on the Arcade map page
 *                                        (frontend.xml template BottomFrameHeistBackStartGameButtons);
 *                                        ZMercsLevelSelectorHeist slot 20 (0x49f4e0) then runs 0x502b40.
 *                                        Called on the game's thread from the keyboard poll, i.e. a
 *                                        little earlier in the frame than the menu would. Never run.
 *                                        An unknown element fails the script (exit 26).
 *   9=peek 0xceceec arcade-position      log the dword at an address (kl2.exe image or heap);
 *     peek 0x168e598+0x5c game-mode      with '+': the dword at [address] + offset (one pointer followed)
 *     peek 0x168e598+0x17c+0x198+0x31fc lb-count     a chain, up to six '+': [[[address]+a]+b]+c (each '+'
 *                                        follows one pointer, then adds). This one is the leaderboard row
 *                                        count of re\crash_scorepage.md 4; +0x10 / +0x14 = first / past-last.
 *   10=sel HeistLevel 0xceceec 0         step a toggle element until the dword at the address has the
 *                                        value: sends 'Decrease' / 'Increase' (ZToggle slot 20,
 *                                        0x90b170 -> vtbl+0xa8 / +0xa4) every 250 ms, at most 24
 *                                        times, and waits up to 10 s for the element to exist.
 *                                        [0xceceec] is the Arcade selector's position, copied there
 *                                        every frame by its slot 8 (0x459eec); 0 = Subway (F01).
 *                                        Needed because the page opens on the profile's last map
 *                                        (0x459eb7: 0x85f510 on the profile 0x1686e60).
 *   11=expect 0xceceec 0                 fail the script (exit 27) unless the dword has that value
 *   12=waitwin MainMenu 8000             wait until the top window of the menu stack has that name; a timeout
 *                                        fails the script (exit 26) with the stack in the reason. Works with
 *                                        Hooks=0 (reads the window system, calls each window's name getter).
 *   13=windows                           log the window stack and the focused element now
 *   14=focus Button_Heist DOWN 6         tap the key (at most 6 times, 0.7 s apart) until the description of
 *                                        the focused element contains the text; fails otherwise. Needs Hooks=1.
 *   15=open HeistPlayMenu                open a window by name, as the game's own code does
 *                                        (system->0x6bee50(name, 1, 0, 1)). Compiled, NOT RUN.
 *   16=watch 0xdd2640+0x6d 1 load:quit   hardware write watch (DR0) on 1 / 2 / 4 bytes at an address, or at
 *                                        [address] + offset; every write is logged with its callers. A label
 *                                        that starts with "load:" is armed when the next level load begins.
 *                                        NEVER arm it while the frontend runs: Steam's probe at 0xa8e3cb
 *                                        (raised before each scene load) jumps to 0 when a debug register is
 *                                        set (run RN2). Armed during the load it survived (run RN3).
 *   17=mouse 400 0 2000                  scripted mouse: counts per second in x and y for that many ms (through
 *                                        the mouse's GetDeviceState; the real mouse is dropped while a script runs).
 *                                        Run PX3: -400 counts/s for 4 s turned the player by -272 degrees = 0.17
 *                                        degrees a count at the default sensitivity (no profile is loaded).
 *      mdown 0 / mup 0                   mouse button 0..7 held / released (0 = fire)
 *   18=pos label                         log the moving player's position and heading (see PLAYERS below)
 *   19=goto 291 -9400 100 15000 sprint keep
 *                                        steer the player to world (x, z): W held, the mouse turned in proportion to
 *                                        the bearing error (5 / s, at most 1800 counts/s); done within <radius>
 *                                        (default 120). No path finding: give way points (the level's navigation
 *                                        mesh has them, re\fa_round.md 6). Not on for 1.5 s: side step A / D for
 *                                        0.7 s, every third time a tap on C ('Get Up' when the player is down).
 *                                        A timeout (default 20000 ms) is LOGGED and the script goes on. 'sprint'
 *                                        holds LSHIFT, 'keep' leaves the keys down for a following goto.
 *      face 300 -8300 5 3000             turn until the heading is within <degrees>; only works while walking
 *                                        (the heading at +0xc14 does not follow the camera of a standing player)
 *   20=onwin HeistStatusLeaderboard score   from now on: when that window comes up, let go of every key and go
 *      label score                          on at the label (a round can end while the script still walks)
 *   21=rewrite 0x168f750+0x16 64 slot-name   DATA WRITE test (experiment X2): read <n> bytes (at most 64) at an
 *      rewrite 0xd35420 4 netcode-global       address, or at [address] + offset, and write the same bytes back
 *   22=waitstate 0x19 90000              wait until the session state ([0x168e598]+0x70; 0x19 = the round runs, 'GO') is
 *                                        that value; a timeout (default 60000 ms) fails the script (exit 26). WHY: until
 *                                        GO the hero stands on its parking place and cannot move - a goto given then finds
 *                                        nobody moving and is skipped. GO comes 20.5 .. 22.1 s after the level's load.
 *   23=waitvan 3 60000                   wait until the escape vehicle's state (byte [rules+0x1dc], rules =
 *                                        [[0x168e9e4]+0x54], a ZGameRulesHeist: klbot.c 1) is that value; 3 also takes 4
 *                                        (it WAITS and can be boarded), 1 also 2 (it drives in). A timeout (default 60000
 *                                        ms) is LOGGED and the script goes on. WHY: a key-framed van's boarding box rides
 *                                        on the van and its nose kills - a script may step to its rear doors only while it
 *                                        stands. Read only.
 *   [Auto] PosLogMs=2000 logs 'pos tick' that often once a level runs; PosOff / DirOff / TurnDeg override the
 *   offsets and the mouse gain below. A script may have 640 lines.
 *
 * PLAYERS (read only; found by sampling the process from outside while a script walked, runs PX2 / PX3)
 *   A ZFFPlayer (vtable 0xbb45f4) is 16 objects a level, found by scanning the heap for the vtable (0.1 s).
 *   +0x460 three floats: world position of the feet (x, y up, z), the navigation mesh's own heights.
 *   +0xc14 three floats: unit vector pointing BACK; heading = atan2(-x, -z), within 1 degree of the direction
 *   of travel on every straight stretch. The entity slot (+4) of a player holds an identity matrix: no use.
 *   Which of the 16 is the local one: the game's own pointer [gamedata + 0x828 + 4 * (char)[gamedata + 0x898]],
 *   gamedata = [0xdd265c] (0x660b00; kljoin.c reads it the same way, seen live). When that cannot be read: the one
 *   that moves (the other heroes stand at their start places in Arcade). The pointer also follows a change of body
 *   (a dead heister who comes back as police, klfed.c: the one that moved first stays dead where it fell).
 *   Keys (kl2.exe's default binding text, 'GameplayInput={...}'): W A S D, LSHIFT / SPACE sprint, E use /
 *   pick up / heal, C cover and 'Get Up', R reload, Q weapon, mouse left fire, right aim, TAB scores.
 *
 *   Keys: A-Z 0-9 F1-F12 RETURN ESCAPE SPACE TAB BACK UP DOWN LEFT RIGHT LSHIFT LCONTROL LMENU INSERT
 *   DELETE HOME END PRIOR NEXT NUMPADENTER, or a DIK code as 0x1C. RSHIFT cannot be scripted: the game
 *   ignores DIK 0x36 from DirectInput and asks GetAsyncKeyState(0xA1) (kl2 0x6c8c2f, 0x6c8c91).
 *   The menu route into an Arcade round is in KLHook.round.ini (run live, 2026-10-09).
 *
 * MENU STATE (read off the disassembly, then seen live in runs OB1, RN1-RN6)
 *   - window system (ZXMLGUISystem, vtable 0xbaf2fc) = [[[0xdd265c]+0x824]+4]; open window by name =
 *     0x6bee50 (thiscall: name, bool, bool, bool; byte +0x4bc set = busy, the request is queued);
 *     window stack: count at +0x328, windows at +0x32c + 4*i for i = 1..count, the top one last
 *     (0x6bef1c, 0x6bef5d); a window's name = its vtable slot 3 (0x410930).
 *   - focus lives in the scene, not in the XML layer: ZWINDOWS (vtable 0xbab94c) slot 161 (0x7f09f0)
 *     SetFocus(window object), slot 162 (0x4ec1b0) returns [ZWINDOWS+0x58]. An element asks for it
 *     through 0x581c70 (its window object is element+0x88); arrow keys move it inside ZWINDOWS without
 *     asking any element, and the newly focused element is then sent input code 0x7b. Window objects
 *     are shared between pages ('Button#04'), so the owner of the focus is taken from the request that
 *     led to it or from that code 0x7b, never from a table.
 *   - element input = vtable slot 10 (code, ?, ?); base 0x4c0680. Codes seen: 0x7f ZW_SELECT (RETURN),
 *     0x86 ZW_CANCEL (ESC), 0x7b 'you have the focus', 0x83 Start, 0x7d / 0x7e left / right.
 *   - an element's Name is [element+4]; its other strings (Window of an OpenWindow at +0x104, text key
 *     at +0x9c, FocusGraphic at +0x64, Option at +0xe4) are logged as "+offset=text".
 *   - WHAT THE FRONTEND OPENS: with the ini key DisableSplashScreens the start-up code 0x7b0370 takes its
 *     'back from a game' branch (0x7b0422 -> 0x7b05ed): MainMenu, then CampaignMenu on top (HeistModeMenu
 *     when the option CoopNetMode is 4). No splash, no AttractMode, no press-start, no disclaimer. On
 *     CampaignMenu RETURN = Button_ResumeGame -> DifficultyScreen, RETURN there = QuickstartCampaign
 *     (0x4789d0) -> load of L00: that is why the first scripts (RD1-RD3) started the story.
 *     The frontend does not read the keyboard for about 22 s after its load (a frozen 'Buffering 100%').
 *   - NOTHING IS SAVED on this route: ZPressStart (0x418d10) is what sets byte 0x156b742, and the save
 *     reader 0x47c5f0 and writer 0x6587c0 (CreateFileA, CREATE_ALWAYS) both return at once without it.
 *
 * ANTI-TAMPER (established by runs RN1-RN4 against RN5; the check itself was not found)
 *   With the breadcrumb detours, the scene-load vtable entry, the import wrappers or the [Engine] push
 *   operand in place, a level started as a REAL session (Arcade StartGame) loads completely and the
 *   process then ends itself about 30 ms after the load: ExitProcess(0x8000dead), called through an
 *   XOR-ed pointer from 0x794ed6 in a routine (0x794e80) that first zeroes its stack and has no caller
 *   in the image. The quit byte sysif+0x6d is never written (hardware watch, RN3). The same DLL with
 *   Hooks=0 and no [Engine] (run RN5: only the DirectInput proxy, memory reads and calls of game
 *   functions) starts the round. A direct boot (DefaultScene) never ran into it with all hooks on.
 *   Which of the patches trips it was not separated. RULE: a run that starts a session uses Hooks=0,
 *   no [Engine], CmdAdd for engine keys; breadcrumbs are for direct-boot runs.
 *   With Hooks=0 a load is noticed as a pause of the keyboard polls followed by a new scene name.
 *   SINCE (re\antitamper.md: it is Valve CEG's code-integrity check over hashed ranges of the image; runs X1 - X3,
 *   re\fa_round.md 7.1): import-slot wrappers (EndHooks=1, klslot's [Expansion]), data writes ('rewrite') and the
 *   five detours in unhashed pages (Detours=NODE,CTRL,SCNBLK,REFFIX,GINIT) each survived a real session. The other
 *   eight detours, the vtable entry and [Engine] are inside hashed ranges (not separated live).
 *
 * RESULT FILE <game>\KLHook.result
 *   state=RUNNING | PASS | EXIT | FAIL      (EXIT = the process ended by itself and nothing was wrong)
 *   reason=...  exit=<code>  pid=  scene=  loading=0/1  loads=<finished loads>  level_loaded=0/1
 *   stage=  percent=  node=  total=  entity=  controller=  phase=  asserts=  faults=<first-chance
 *   faults inside kl2.exe>  foreign_first_chance=<in other modules; never decides the result>
 *   last_fault=  frames=<keyboard polls>  script=<line reached>  ms=<since load of the DLL>
 *   A driver deletes the file, starts the game and waits for the process to end (or state != RUNNING).
 *   state still RUNNING after the process is gone = it died without passing any handler below.
 *   Exit codes (only visible when the driver owns the process; through Steam use the file):
 *   0 PASS, 21 ended/loaded but asserts or faults were logged, 22 unhandled exception, 23 C runtime
 *   fatal, 24 stall, 25 MaxRunMs, 26 script wait timed out, 27 script "fail". When the game ends by
 *   itself (AutoExit, Quit) the process keeps the game's own exit code; only the file says EXIT or FAIL.
 *
 * EVIDENCE. All addresses: kl2.exe sha1 9d99e01d57f3cef404e1269851d67cb971335e4c, TimeDateStamp
 * 0x4c80f728, base 0x400000, SizeOfImage 0x134e000, entry 0xa8dc71 inside .text (no .bind section, so
 * no SteamStub wrapper decrypts code after our DllMain). Read with debug\dasm.py (capstone) on
 * 2026-10-09. "verified" below = read off that disassembly; nothing here has run inside the game yet.
 *
 *  Input (verified by disassembly)
 *   - One DirectInput8Create call, 0x6d7836 (version 0x800, interface -> [0xe05580]).
 *   - ZKeyboardWintel vtable 0xb8f4dc: open = slot 25 0x6144f0: IDirectInput8::CreateDevice (vtbl+0xc),
 *     SetDataFormat (+0x2c, format 0xbd61c4, data size 256), SetCooperativeLevel (+0x34, flags 0x16),
 *     SetProperty (+0x18, buffer size 0x100). Each failure is an int3.
 *   - Update = slot 27 0x6c8b90: skipped when device (+0x70) is null or byte +0x54 is 0; if byte +0x84
 *     is 0 it calls slot 29 -> 0x8fa080, which calls Acquire (+0x1c) ONCE and sets the acquired byte
 *     when the result is 0 or 1; then GetDeviceData(dev, 0x14, this+0x290, &count = 0x100, 0) at
 *     0x6c8bdf. ANY non-zero HRESULT, including DI_BUFFEROVERFLOW (1), clears the acquired byte and
 *     drops the frame's events - so the wrapper returns exactly 0. Per event the game reads only
 *     dwOfs (+0) and dwData & 0x80 (+4); time stamps come from the engine clock, not from DirectInput.
 *   - ZMouseWintel update 0x650840: GetDeviceState (+0x24, 0x14 bytes), buttons at +0xc.. of the state.
 *   NOT ESTABLISHED: who clears byte +0x54 (slot 20, 0x79ab10 "mov byte [ecx+0x54],0"). If the game
 *   disables its keyboard object when the window is deactivated, the script stalls while the window
 *   is in the background; the watchdog then reports "no input frames".
 *
 *  Breadcrumb sites (verified: bytes, position independence, no branch into the replaced bytes - a scan
 *  of every rel32 target in .text and of every jump in the containing function found none)
 *   id       address   replaced bytes                   what is known there
 *   NODE     0x46fe96  8b 74 24 20 8b 16                node loader 0x46fe20: EAX = entity name (char*,
 *                                                       "<NONAME>" 0xb31570 if none), EDI = class object,
 *                                                       EBP = locator; [0xe0ff14] = running node count,
 *                                                       [0xe0ff18] = total (both set at 0x8ade63)
 *   CTRL     0x46ffbf  8b 4d 60 8b 01                   [ESP+0x28] = controller name, char* (it is hashed
 *                                                       byte by byte in 0x8f47c0)
 *   PROG     0x53ac90  83 ec 30 56 8b f1                ZEngineDataBase slot 3 (vtable 0xb8fa04):
 *                                                       (stage, ?, fraction). overall = lo[stage] +
 *                                                       (hi - lo) * fraction, kept as a running maximum
 *                                                       at this+0xcc; every 50 ms it calls 0x607270 with
 *                                                       it (the loading screen). Stage bounds: 0 .1 .15
 *                                                       .35 .4 .5 .6 .7 .8 .9 1; when the scene name
 *                                                       contains "KaneAndLynch": 0 .2 .4 .35 .4 .7 .95
 *                                                       .98 1. The node loader reports stage 5 with
 *                                                       0.5 + 0.5 * node / total (0x46fe3b-0x46fe7c).
 *   GEOMS    0x8ad7c0  55 8d ac 24 e8 bf ff ff          entity loader (CreateGeoms), called at 0x820b6c
 *   SCNBLK   0x862780  55 8d ac 24 50 ff ff ff          scene property block reader (one caller 0x8ade24)
 *   REFFIX   0x6204b0  55 8b ec 83 e4 f0                REF fix-up after the nodes (one caller 0x8adecc)
 *   ROOM     0x48e910  53 8b 5c 24 08                   room fix-up, ECX = the ZROOM (one caller 0x8adf48)
 *   GBUF     0x9262b0  53 55 56 8b f1                   ZGeomBuffer pass (one caller 0x8adfeb)
 *   REFEND   0x8d1210  83 ec 0c 8b 41 04                last REF consumer (one caller 0x8adff7)
 *   POST     0x5acc50  a1 40 26 dd 00                   post-load init, called at 0x820e2d: sets
 *                                                       [0x1503910] = 1 then 2 and walks the geom tree
 *                                                       (root vtbl+0x3c), sets [0x150363c] = 1 then 2
 *                                                       and runs 0x80d800. Stages 4 and 5 follow in the
 *                                                       scene loader itself (0x820e6b-0x820edf).
 *   GINIT    0x7f3b80  53 56 8b f1 8b 0d 90 ff e0 00    ZGEOM slot 15, staged init of ONE geom: ECX =
 *                                                       geom, own stage byte geom+0xe, target stage
 *                                                       [0x1503910]; stage 1 -> vtbl+0x148, 2 -> +0x14c,
 *                                                       4 -> +0x150, 5 -> +0x154. The 2026-10-08 crashes
 *                                                       (callers 0088cc11 0088cba3 ... 005accbd 00820e32)
 *                                                       are inside this walk at stage 2.
 *   CLIST    0x80d800  55 8b ec 83 ec 10                init of the object list at EngineDB+0x2c, ECX =
 *                                                       list ([ECX] = count), stage [0x150363c]
 *   CINIT    0x4eec50  ff 05 40 36 50 01                per-object init stepper (obj, target stage, flag):
 *                                                       own stage byte obj+0x21; stage 1 -> vtbl+0x34,
 *                                                       2 -> +0x38, 4 -> +0x3c, 5 -> +0x40, 7 -> +0x70
 *   The four functions with "one caller" have one DIRECT call in .text; calls through pointers were not
 *   ruled out, so their lines are only logged while a scene load is running.
 *   Entity name of a geom: *(char **)(*(geom + 4) + 0x6c) (0x46fe84-0x46fe8a). Class: MSVC RTTI of the
 *   object's vtable.
 *   Scene load = ZEngineDataBase slot 8, 0x820300, "ret 4" (its only ret, 0x82105d). Its vtable entry
 *   0xb8fa24 is the only reference to it in the image (no direct call), so that entry is replaced by a
 *   wrapper: start / end / duration. The scene name is *(char **)(*(void **)0xdd2640 + 0x2b0)
 *   (read the same way at 0x53aca1-0x53acb6). ASSUMPTION: that field already names the scene being
 *   loaded when slot 8 is entered.
 *
 *  Engine ini (verified): ZSysInterface::ReadConfig 0x598730 executes "push 0xb55dc0" at 0x5987af
 *  (bytes 68 c0 5d b5 00) and parses that NUL-terminated text ("DefaultScene=KaneAndLynch.gms\n
 *  UseEidosMetricsServers\nDisableClientCountDisconnect\n"); "-o" lines are appended behind it and a
 *  later key replaces an earlier one (research: boot-config report). [Engine] lines are appended by
 *  pointing that operand at our own copy. DINPUT8.dll is a static import, so DllMain runs before any
 *  game code. AutoExit: read at 0x4bc2f2 (atof -> float sysif+0x68); 0x5c7203-0x5c7231 sets the quit
 *  byte sysif+0x6d once the tick count sysif+0x38 exceeds AutoExit * 1024. We log that float and the
 *  scene name at the first DirectInput8Create and at the first input frame: this is the read-back that
 *  shows whether an override arrived.
 *
 *  Faults
 *   - A vectored handler sees every first-chance exception of the process. Inside kl2.exe klhook.c
 *     already logs; here only the "where:" lines (printed just BEFORE klhook.c's ASSERT / CRASH line)
 *     and the counters are added. Elsewhere the fault is logged once per address with module + offset
 *     and is not dumped. First chance does not mean fatal (0xa8e3cb is a write to 0 that the game's
 *     own handler resumes; IsBadReadPtr faults by design), so the verdict comes from the unhandled-
 *     exception filter. The game installs its own filter at 0x58ffca (0x90b780, the Steam minidump);
 *     the watchdog re-installs ours every 250 ms and chains to whatever it displaced.
 *   - A stack overflow leaves no room to log on the faulting thread: it is handed to the watchdog.
 *   - MSVCR90's fatal paths raise no exception a filter sees (_invoke_watson clears the filter and
 *     terminates), so _set_invalid_parameter_handler, _set_purecall_handler and signal(SIGABRT) are
 *     set in the game's MSVCR90 (kl2.exe imports none of these setters, so nothing is displaced).
 *     ASSUMPTION: the game never relies on MSVCR90 ignoring an invalid parameter - with no handler
 *     set MSVCR90 terminates the process anyway, so making it a FAIL changes nothing.
 *   NOT CAUGHT: a /GS cookie failure (kl2 0xa8df52: SetUnhandledExceptionFilter(0), then
 *   UnhandledExceptionFilter, TerminateProcess) and __fastfail. The result file then stays RUNNING.
 *
 *  TESTED OFF-GAME (scratch harness, 2026-10-09; the game was never started): a 32-bit harness loads
 *  the DLL the way the game does, maps a copy of kl2.exe at another address and calls the hook
 *  handlers with made-up engine objects.
 *   - patcher on the real bytes: 13 of 13 detours + vtable entry + ini operand installed; 88 bytes
 *     of the image differ afterwards, all inside the 90 listed ones; every stub disassembled and compared
 *     (save, call, restore, the replaced instructions byte for byte, jump back to site + length);
 *     a detour on a synthetic function still returns the right value and passes its stack arguments.
 *   - the real system keyboard through the proxy with the game's call sequence, window NOT in the
 *     foreground: real GetDeviceData fails 8007000c, the scripted events arrive in order with DI_OK
 *     (tap, tap with hold, down / up, waitscene, waitload, pass -> state=PASS, exit code 0).
 *   - exit codes 22 (access violation inside msvcrt.dll, reported as msvcrt.dll+0x89820; stack
 *     overflow), 23 (abort, invalid parameter and pure call inside a real MSVCR90), 24 (stall, with
 *     the hung thread's location), 26 (script wait timed out), 0 via LoadedMs, state=EXIT on a normal
 *     process end, and Enable=0 leaving no trace.
 *  None of this shows that the hooks fire inside the game or that the game accepts the input.
 *
 *  LIVE STATUS 2026-10-09: a - e below were all exercised since (kl_graft.py run log): "-o" lines arrive,
 *  the detours fire and survive a direct boot, the keyboard is polled without focus, StallMs 180 s is safe.
 *  NEEDS A LIVE RUN (as written before the first run; kept for the reasoning)
 *   a. that "-o" lines arrive (first experiment, no new build needed): Steam > Dog Days > Properties >
 *      Launch options:  -o AutoExit=30 -o DisableSplashScreens   then Play and touch nothing. Confirmed
 *      if the splash screens are skipped and the game closes by itself (30 s of ENGINE time after
 *      start; whether engine time runs during loading is not established, so allow two minutes).
 *      Not confirmed if it sits in the menu: then use [Engine] in KLHook.ini.
 *   b. that code patched from DllMain survives (no integrity check was found, none was searched for
 *      exhaustively) and that all thirteen detours fire. Second experiment, with this file built and
 *      installed: [Auto] Enable=1, StallMs=180000, [Engine] 1=AutoExit=90, no [Script]; start and
 *      touch nothing. Expected in KLHook.log: "hooks: 13 of 13", "engine ini: 1 line(s) installed",
 *      "input: first keyboard poll ... AutoExit=90", "LOAD start scene='...KaneAndLynch...'", progress
 *      and node lines, "LOAD end", then "process exit" and state=EXIT in KLHook.result.
 *   c. that the keyboard keeps being polled without focus, and the menu key sequence.
 *   d. what DefaultScene=Locations/F02/F02_Main.zip does when booted directly (no session is created).
 *   e. that StallMs never fires during a legitimate pause (Steam start-up, movies): start high.
 */
#ifndef KLHOOK_C                                 /* compiled on its own: the TEST build, through klhook.c */
#ifndef KLHOOK_TEST
#define KLHOOK_TEST
#endif
#include "klhook.c"
#else
#ifndef KLAUTO_C
#define KLAUTO_C

#include <tlhelp32.h>
#include <intrin.h>
#include <math.h>
#include <signal.h>

#define KL2_TIMESTAMP 0x4c80f728u
#define KL2_IMAGESIZE 0x134e000u
enum { KLA_PASS = 0, KLA_PROBLEMS = 21, KLA_CRASH = 22, KLA_CRT = 23, KLA_STALL = 24, KLA_MAXRUN = 25,
       KLA_SCRIPT = 26, KLA_SCRIPTFAIL = 27 };

#define kla_delta klh_delta                      /* 0 in the game; the test harness maps a copy elsewhere */
#define kla_exe_ok klh_exe_ok
#define VA(x) ((BYTE *)((DWORD_PTR)(x) + kla_delta))
#define G32(x) (*(volatile DWORD *)VA(x))

static int kla_on, kla_hooks_on, kla_nodes, kla_unfocused, kla_block, kla_firstchance;
static DWORD kla_stall_ms, kla_maxrun_ms, kla_loaded_ms, kla_t0;
static volatile DWORD kla_beat, kla_frames, kla_main_tid;
static volatile LONG kla_done, kla_asserts, kla_faults, kla_foreign;
static DWORD kla_tls = TLS_OUT_OF_INDEXES;      /* set while this thread is inside one of our fault handlers */
static CRITICAL_SECTION kla_cs;
static BYTE *kla_stubs;
static char kla_ini[MAX_PATH], kla_engine_text[4096], kla_last_fault[160];
static LPTOP_LEVEL_EXCEPTION_FILTER kla_prev_uef;
static HANDLE kla_wake;
static EXCEPTION_POINTERS *volatile kla_so_ep;   /* stack overflow handed to the watchdog thread */

/* what the game was doing; written by the hooks, read by the fault handlers */
static struct {
    char scene[128], done_scene[128], ent[96], ctrl[64];
    const char *phase;
    DWORD loading, loads, level_tick, level_frames, load_t0;
    DWORD stage, percent, node, total, nodes_seen, rooms;
    DWORD gstage, gcount, geom, cstage, obj, otarget, ocount;
} kb = { "", "", "", "", "boot" };

/* ---------------------------------------------------------------- memory, names, log */

static int kla_rd(DWORD_PTR p, void *out, SIZE_T n)
{   /* never faults: the hooks must not raise exceptions of their own */
    SIZE_T got = 0;
    return p > 0xffff && ReadProcessMemory(GetCurrentProcess(), (void *)p, out, n, &got) && got == n;
}
static DWORD kla_rd32(DWORD_PTR p) { DWORD v = 0; kla_rd(p, &v, 4); return v; }

static void kla_rdstr(DWORD_PTR p, char *out, int cap)
{
    int n = 0, i, end = 0;
    while (p > 0xffff && !end && n < cap - 1) {
        int room = 0x1000 - (int)((p + n) & 0xfff), want = cap - 1 - n;
        if (want > room) want = room;
        if (!kla_rd(p + n, out + n, want)) break;
        for (i = 0; i < want && out[n + i]; i++) if ((BYTE)out[n + i] < 0x20 || (BYTE)out[n + i] > 0x7e) out[n + i] = '?';
        end = i < want; n += i;
    }
    out[n] = 0;
}

static void kla_rtti(DWORD_PTR obj, char *out, int cap)
{   /* class name of a C++ object: vtable[-1] -> complete object locator -> type descriptor + 8 */
    char raw[96], *e; DWORD vt = kla_rd32(obj), col, td;
    out[0] = 0;
    if (!vt || !(col = kla_rd32(vt - 4)) || kla_rd32(col) != 0 || !(td = kla_rd32(col + 12))) return;
    kla_rdstr(td + 8, raw, sizeof raw);
    if (strncmp(raw, ".?A", 3) || !raw[3]) return;
    if ((e = strstr(raw, "@@")) != 0) *e = 0;
    snprintf(out, cap, "%s", raw + 4);
}

static void kla_geom_name(DWORD_PTR geom, char *out, int cap)
{
    DWORD loc = kla_rd32(geom + 4);
    out[0] = 0;
    if (loc) kla_rdstr(kla_rd32(loc + 0x6c), out, cap);
}

static DWORD kla_sysif(void) { return kla_exe_ok ? G32(0xdd2640) : 0; }      /* the ZSysInterface object */

static void kla_scene(char *out, int cap)
{
    DWORD sys = kla_sysif();
    out[0] = 0;
    if (sys) kla_rdstr(kla_rd32(sys + 0x2b0), out, cap);
}

static int kla_contains(const char *hay, const char *needle)
{
    size_t n = strlen(needle);
    for (; *hay; hay++) if (!_strnicmp(hay, needle, n)) return 1;
    return 0;
}
static int kla_frontend(const char *scene) { return kla_contains(scene, "kaneandlynch"); }

static void kla_module(DWORD_PTR addr, char *out, int cap, DWORD *off)
{
    MEMORY_BASIC_INFORMATION mbi; char path[MAX_PATH], *s;
    *off = (DWORD)addr;
    if (kla_stubs && (BYTE *)addr >= kla_stubs && (BYTE *)addr < kla_stubs + 0x1000) { snprintf(out, cap, "KLHook-stub"); *off = (DWORD)((BYTE *)addr - kla_stubs); return; }
    if (VirtualQuery((void *)addr, &mbi, sizeof mbi) && mbi.AllocationBase && mbi.Type == MEM_IMAGE &&
        GetModuleFileNameA((HMODULE)mbi.AllocationBase, path, MAX_PATH)) {
        s = strrchr(path, '\\'); snprintf(out, cap, "%s", s ? s + 1 : path);
        *off = (DWORD)(addr - (DWORD_PTR)mbi.AllocationBase);
    } else snprintf(out, cap, "<no module>");
}

/* Buffered lines for KLHook.log (an entity line per node would otherwise cost an fopen each).
   klhook.c's klog() appends through its own handle; kla_flush() runs before anything important. */
static char kla_buf[32768]; static int kla_len; static HANDLE kla_log = INVALID_HANDLE_VALUE;

static void kla_flush(void)
{
    DWORD w;
    EnterCriticalSection(&kla_cs);
    if (kla_len) {
        if (kla_log == INVALID_HANDLE_VALUE) {
            char path[MAX_PATH]; snprintf(path, sizeof path, "%s\\KLHook.log", klh_out);
            kla_log = CreateFileA(path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, 0, OPEN_ALWAYS, 0, 0);
        }
        if (kla_log != INVALID_HANDLE_VALUE) WriteFile(kla_log, kla_buf, kla_len, &w, 0);
        kla_len = 0;
    }
    LeaveCriticalSection(&kla_cs);
}

static void kla_out(int now, const char *fmt, ...)
{
    char line[600]; int n; SYSTEMTIME t; va_list a;
    GetLocalTime(&t);
    n = snprintf(line, 16, "%02d:%02d:%02d.%03d ", t.wHour, t.wMinute, t.wSecond, t.wMilliseconds);
    va_start(a, fmt); n += vsnprintf(line + n, sizeof line - n - 2, fmt, a); va_end(a);
    if (n < 0 || n > (int)sizeof line - 3) n = sizeof line - 3;       /* truncated: drop vsnprintf's terminator too */
    line[n++] = '\r'; line[n++] = '\n';
    EnterCriticalSection(&kla_cs);
    if (kla_len + n > (int)sizeof kla_buf) kla_flush();
    memcpy(kla_buf + kla_len, line, n); kla_len += n;
    LeaveCriticalSection(&kla_cs);
    if (now) kla_flush();
}

static void kla_where(void)
{
    char g[96] = "", gc[64] = "", oc[64] = "";
    if (kb.geom) { kla_geom_name(kb.geom, g, sizeof g); kla_rtti(kb.geom, gc, sizeof gc); }
    if (kb.obj) kla_rtti(kb.obj, oc, sizeof oc);
    kla_out(0, "  where: scene='%s' loading=%lu phase=%s progress stage %lu %lu%% node %lu/%lu '%s' controller '%s'",
            kb.scene, kb.loading, kb.phase, kb.stage, kb.percent, kb.node, kb.total, kb.ent, kb.ctrl);
    kla_out(1, "  where: geom init stage %lu #%lu last geom '%s' [%s] | object init stage %lu #%lu last object %08lx [%s] | frames %lu",
            kb.gstage, kb.gcount, g, gc, kb.cstage, kb.ocount, kb.obj, oc, kla_frames);
}

/* ---------------------------------------------------------------- result file, end of run */

static int kla_script_pc(void);

static void kla_result(const char *state, const char *reason, int code)
{
    char path[MAX_PATH], tmp[MAX_PATH], text[1200]; HANDLE f; DWORD w; int n;
    snprintf(path, sizeof path, "%s\\KLHook.result", klh_out); snprintf(tmp, sizeof tmp, "%s\\KLHook.result.tmp", klh_out);
    n = snprintf(text, sizeof text,
        "state=%s\r\nreason=%s\r\nexit=%d\r\npid=%lu\r\nscene=%s\r\nloading=%lu\r\nloads=%lu\r\nlevel_loaded=%d\r\n"
        "stage=%lu\r\npercent=%lu\r\nnode=%lu\r\ntotal=%lu\r\nentity=%s\r\ncontroller=%s\r\nphase=%s\r\n"
        "asserts=%ld\r\nfaults=%ld\r\nforeign_first_chance=%ld\r\nlast_fault=%s\r\nframes=%lu\r\nscript=%d\r\nms=%lu\r\n",
        state, reason, code, GetCurrentProcessId(), kb.scene, kb.loading, kb.loads, kb.level_tick != 0,
        kb.stage, kb.percent, kb.node, kb.total, kb.ent, kb.ctrl, kb.phase,
        kla_asserts, kla_faults, kla_foreign, kla_last_fault, kla_frames, kla_script_pc(), GetTickCount() - kla_t0);
    if (n < 0 || n > (int)sizeof text) n = sizeof text;
    EnterCriticalSection(&kla_cs);
    f = CreateFileA(tmp, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, 0, 0);
    if (f != INVALID_HANDLE_VALUE) { WriteFile(f, text, n, &w, 0); CloseHandle(f); MoveFileExA(tmp, path, MOVEFILE_REPLACE_EXISTING); }
    LeaveCriticalSection(&kla_cs);
}

static void kla_finish(const char *state, const char *reason, int code)
{   /* ends the process; the first caller wins */
    if (InterlockedExchange(&kla_done, 1)) { Sleep(INFINITE); return; }
    kla_out(1, "RESULT %s (%s) exit code %d, asserts %ld, faults %ld, loads %lu, frames %lu",
            state, reason, code, kla_asserts, kla_faults, kb.loads, kla_frames);
    kla_result(state, reason, code);
    TerminateProcess(GetCurrentProcess(), code);
}

static void kla_pass(const char *why)
{
    char r[200];
    if (kla_asserts || kla_faults) {
        snprintf(r, sizeof r, "%s, but %ld asserts and %ld faults were logged", why, kla_asserts, kla_faults);
        kla_finish("FAIL", r, KLA_PROBLEMS);
    }
    kla_finish("PASS", why, KLA_PASS);
}

/* Write watch: one hardware breakpoint (DR0) on up to 4 bytes, armed on every thread of the process by the
   watchdog thread (a thread cannot set its own debug registers reliably). The vectored handler logs who
   wrote (the instruction AFTER the write, the new value, the kl2.exe callers on the stack) and resumes. */
static volatile DWORD kla_watch_addr, kla_watch_len, kla_watch_arm, kla_watch_hits, kla_watch_defer;
static char kla_top[64];                             /* name of the top menu window (kla_windows) */
static char kla_watch_label[48];

static void kla_watch_apply(void)
{
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0); THREADENTRY32 te; int n = 0, ok = 0;
    DWORD me = GetCurrentThreadId(), pid = GetCurrentProcessId(), len = kla_watch_len == 4 ? 3 : kla_watch_len == 2 ? 1 : 0;
    if (snap == INVALID_HANDLE_VALUE) return;
    te.dwSize = sizeof te;
    if (Thread32First(snap, &te)) do {
        HANDLE t; CONTEXT c;
        if (te.th32OwnerProcessID != pid || te.th32ThreadID == me) continue;
        t = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_SET_CONTEXT, FALSE, te.th32ThreadID);
        if (!t) continue;
        n++;
        if (SuspendThread(t) != (DWORD)-1) {
            memset(&c, 0, sizeof c); c.ContextFlags = CONTEXT_DEBUG_REGISTERS;
            if (GetThreadContext(t, &c)) {
                c.Dr0 = kla_watch_addr; c.Dr6 = 0;
                c.Dr7 = kla_watch_addr ? (c.Dr7 & ~0x000f0003u) | 1 | (1u << 16) | (len << 18) : c.Dr7 & ~0x000f0003u;   /* L0, RW0 = write, LEN0 */
                c.ContextFlags = CONTEXT_DEBUG_REGISTERS;
                if (SetThreadContext(t, &c)) ok++;
            }
            ResumeThread(t);
        }
        CloseHandle(t);
    } while (Thread32Next(snap, &te));
    CloseHandle(snap);
    kla_out(1, "watch: %s %08lx (%lu byte(s), '%s') on %d of %d threads", kla_watch_addr ? "armed on" : "cleared", kla_watch_addr, kla_watch_len, kla_watch_label, ok, n);
}

static void kla_atexit(void)
{   /* ExitProcess / exit() of the game itself, e.g. AutoExit or the menu's Quit */
    if (!kla_on || InterlockedExchange(&kla_done, 1)) return;
    kla_out(1, "process exit, asserts %ld, faults %ld, loads %lu", kla_asserts, kla_faults, kb.loads);
    {   /* who ended it: the engine's own state and the kl2.exe callers of exit() on this stack */
        CONTEXT c; DWORD sys = kla_sysif(); float ax = 0;
        if (sys) kla_rd(sys + 0x68, &ax, 4);
        kla_flush();
        klog("  exit: thread %lu (main %lu), sysif quit byte %lu, ticks %lu, AutoExit %g, top window '%s'", GetCurrentThreadId(), kla_main_tid,
             sys ? kla_rd32(sys + 0x6c) >> 8 & 0xff : 0, sys ? kla_rd32(sys + 0x38) : 0, ax, kla_top);
        memset(&c, 0, sizeof c); c.Esp = (DWORD)(DWORD_PTR)&c;
        log_context(&c);
    }
    if (kla_asserts || kla_faults) kla_result("FAIL", "the game ended by itself, asserts or faults were logged", KLA_PROBLEMS);
    else kla_result("EXIT", "the game ended by itself", 0);
}

/* ---------------------------------------------------------------- code detours */

typedef struct { DWORD edi, esi, ebp, esp, ebx, edx, ecx, eax, efl; } KREGS;   /* pushad order, then pushfd */
enum { H_NODE, H_CTRL, H_PROG, H_GEOMS, H_SCNBLK, H_REFFIX, H_ROOM, H_GBUF, H_REFEND, H_POST, H_GINIT, H_CLIST, H_CINIT,
       H_OPENWIN, H_ELFOCUS, H_FOCUS, H_INPUT, H_COUNT };
static const struct { DWORD va; BYTE len; BYTE bytes[10]; const char *what; } kla_sites[H_COUNT] = {
    { 0x46fe96, 6,  { 0x8b, 0x74, 0x24, 0x20, 0x8b, 0x16 }, "node properties (0x46fe20)" },
    { 0x46ffbf, 5,  { 0x8b, 0x4d, 0x60, 0x8b, 0x01 }, "controller" },
    { 0x53ac90, 6,  { 0x83, 0xec, 0x30, 0x56, 0x8b, 0xf1 }, "load progress" },
    { 0x8ad7c0, 8,  { 0x55, 0x8d, 0xac, 0x24, 0xe8, 0xbf, 0xff, 0xff }, "entity loader: create entities (0x8ad7c0)" },
    { 0x862780, 8,  { 0x55, 0x8d, 0xac, 0x24, 0x50, 0xff, 0xff, 0xff }, "scene property block (0x862780)" },
    { 0x6204b0, 6,  { 0x55, 0x8b, 0xec, 0x83, 0xe4, 0xf0 }, "REF fix-up (0x6204b0)" },
    { 0x48e910, 5,  { 0x53, 0x8b, 0x5c, 0x24, 0x08 }, "room fix-up (0x48e910)" },
    { 0x9262b0, 5,  { 0x53, 0x55, 0x56, 0x8b, 0xf1 }, "geom buffer pass (0x9262b0)" },
    { 0x8d1210, 6,  { 0x83, 0xec, 0x0c, 0x8b, 0x41, 0x04 }, "REF consumer (0x8d1210)" },
    { 0x5acc50, 5,  { 0xa1, 0x40, 0x26, 0xdd, 0x00 }, "post-load init (0x5acc50)" },
    { 0x7f3b80, 10, { 0x53, 0x56, 0x8b, 0xf1, 0x8b, 0x0d, 0x90, 0xff, 0xe0, 0x00 }, "geom staged init" },
    { 0x80d800, 6,  { 0x55, 0x8b, 0xec, 0x83, 0xec, 0x10 }, "object init list" },
    { 0x4eec50, 6,  { 0xff, 0x05, 0x40, 0x36, 0x50, 0x01 }, "object init stepper" },
    /* menu observation (2026-10-09, read off the disassembly; see MENU STATE in the top comment) */
    { 0x6bee50, 7,  { 0x6a, 0xff, 0x68, 0xe8, 0x30, 0xad, 0x00 }, "open window by name (0x6bee50)" },
    { 0x581c70, 5,  { 0x56, 0x8b, 0x74, 0x24, 0x08 }, "element asks for focus (0x581c70)" },
    { 0x7f09f0, 5,  { 0x53, 0x55, 0x56, 0x8b, 0xf1 }, "ZWINDOWS set focus (0x7f09f0)" },
    { 0x4c0680, 6,  { 0x8b, 0x81, 0x84, 0x00, 0x00, 0x00 }, "element input, base class (0x4c0680)" },
};

/* ---------------------------------------------------------------- menu state (windows, focus) */

static DWORD kla_zw;                                  /* the ZWINDOWS object, learnt from its SetFocus */
static DWORD kla_ask_geom, kla_ask_elem, kla_focus_elem;   /* last focus request of an element; owner of the focused window object */
static char kla_stack[400];
static DWORD kla_stack_sig, kla_input_lines;

static DWORD kla_wsys(void)
{   /* the window system (ZXMLGUISystem): [[[0xdd265c]+0x824]+4], as 0x478b5c-0x478b74 reaches it */
    DWORD gui, mgr;
    if (!kla_exe_ok || !(gui = G32(0xdd265c)) || !(mgr = kla_rd32(gui + 0x824))) return 0;
    return kla_rd32(mgr + 4);
}

static void kla_win_name(DWORD win, char *out, int cap)
{   /* a window's name: its vtable slot 3 (0x410930 for ZBaseWindow), called the way 0x606eba does */
    DWORD vt = kla_rd32(win), fn = vt ? kla_rd32(vt + 0xc) : 0;
    out[0] = 0;
    if (vt < img_lo || vt >= img_hi || fn < img_lo || fn >= img_hi) return;
    kla_rdstr((DWORD_PTR)((const char *(__fastcall *)(void *, void *))(DWORD_PTR)fn)((void *)(DWORD_PTR)win, 0), out, cap);
}

static int kla_windows(int force)
{   /* the window stack: count at system+0x328, windows at system+0x32c+4*i, i = 1..count, top last
       (0x6bef1c-0x6bef22, 0x6bef5d-0x6bef67). Logged when it changes. Game thread only. -> count */
    DWORD w = kla_wsys(), n, i, sig = 0; char nm[64]; int len = 0;
    if (!w) { kla_top[0] = 0; return 0; }
    n = kla_rd32(w + 0x328); if (n > 24) n = 24;
    for (i = 1; i <= n; i++) sig = sig * 31 + kla_rd32(w + 0x32c + 4 * i);
    sig += n;
    if (sig == kla_stack_sig && !force) return (int)n;
    kla_stack_sig = sig; kla_stack[0] = 0; kla_top[0] = 0;
    for (i = 1; i <= n; i++) {
        kla_win_name(kla_rd32(w + 0x32c + 4 * i), nm, sizeof nm);
        len += snprintf(kla_stack + len, sizeof kla_stack - len, "%s%s", i > 1 ? " > " : "", nm);
        if (len > (int)sizeof kla_stack - 70) break;
        if (i == n) snprintf(kla_top, sizeof kla_top, "%s", nm);
    }
    kla_out(1, "windows: %lu [%s]", n, kla_stack);
    return (int)n;
}

static void kla_elem_desc(DWORD elem, char *out, int cap)
{   /* class, Name (ZNameBase, elem+4: 0x962850) and every string member up to +0x130 (ZString = one char*):
       the Window an OpenWindow leads to, the Receiver / Message of a SendMessage, the option name ... */
    char cls[64], s[48]; int len, off, k; DWORD seen[24]; int ns = 0;
    kla_rtti(elem, cls, sizeof cls);
    kla_rdstr(kla_rd32(elem + 4), s, sizeof s);
    len = snprintf(out, cap, "%s '%s'", cls[0] ? cls : "?", s);
    for (off = 0x60; off < 0x130 && len < cap - 60; off += 4) {
        DWORD p = kla_rd32(elem + off); int ok = 1, dup = 0;
        if (p < 0x10000 || (p & 0x80000000)) continue;
        for (k = 0; k < ns; k++) if (seen[k] == p) dup = 1;
        if (dup) continue;
        kla_rdstr(p, s, sizeof s);
        if (strlen(s) < 3 || strlen(s) > 40) continue;
        for (k = 0; s[k]; k++) if (!(s[k] == '_' || s[k] == '/' || s[k] == '#' || s[k] == ' ' || (s[k] >= '0' && s[k] <= '9') || ((s[k] | 32) >= 'a' && (s[k] | 32) <= 'z'))) ok = 0;
        if (!ok || !(((s[0] | 32) >= 'a' && (s[0] | 32) <= 'z') || s[0] == '/')) continue;
        if (ns < 24) seen[ns++] = p;
        len += snprintf(out + len, cap - len, " +%x=%s", off, s);
    }
}

static void kla_focus_desc(char *out, int cap)
{   /* the focused element: ZWINDOWS+0x58 is the focused window object (0x4ec1b0 returns it, 0x7f0a68
       stores it); the element that owns it is known from the element's own focus request (0x581c70) */
    DWORD g = kla_zw ? kla_rd32(kla_zw + 0x58) : 0; char nm[64];
    out[0] = 0;
    if (!g) { snprintf(out, cap, "%s", kla_zw ? "(nothing focused)" : "(ZWINDOWS not seen yet)"); return; }
    if (kla_focus_elem && kla_rd32(kla_focus_elem + 0x88) == g) { kla_elem_desc(kla_focus_elem, out, cap); return; }
    kla_geom_name(g, nm, sizeof nm);
    snprintf(out, cap, "(window object '%s', owner element not seen)", nm);
}

static void kla_phase(const char *p)
{
    if (kb.phase == p) return;
    kb.phase = p;
    if (kb.loading) kla_out(1, "phase: %s", p);
}

static void __cdecl kla_dispatch(int id, KREGS *r)
{
    DWORD *sp = (DWORD *)(DWORD_PTR)(r->esp + 4);      /* the game's esp at the replaced instruction */
    kla_beat = GetTickCount();
    switch (id) {
    case H_NODE:
        kb.node = G32(0xe0ff14); kb.total = G32(0xe0ff18); kb.geom = r->edi; kb.ctrl[0] = 0; kb.nodes_seen++;
        kla_rdstr(r->eax, kb.ent, sizeof kb.ent);
        kla_phase(kla_sites[H_NODE].what);
        if (kla_nodes >= 1) { char c[64]; kla_rtti(r->edi, c, sizeof c); kla_out(0, "node %lu/%lu %s [%s]", kb.node, kb.total, kb.ent, c); }
        break;
    case H_CTRL:
        kla_rdstr(sp[0x28 / 4], kb.ctrl, sizeof kb.ctrl);
        if (kla_nodes >= 2) kla_out(0, "  controller %s", kb.ctrl);
        break;
    case H_PROG: {
        static const float lo[2][11] = { { 0, .1f, .15f, .35f, .4f, .5f, .6f, .7f, .8f, .9f, 1 },
                                         { 0, .2f, .4f, .35f, .4f, .7f, .95f, .98f, 1, .9f, 1 } };
        DWORD stage = sp[1], pct; float f = *(float *)&sp[3]; int t;
        if (stage > 9 || !(f >= 0) || f > 1.5f) break;
        if (stage != kb.stage || !kb.scene[0]) kla_scene(kb.scene, sizeof kb.scene);
        t = kla_frontend(kb.scene);
        pct = (DWORD)((lo[t][stage] + (lo[t][stage + 1] - lo[t][stage]) * f) * 100 + 0.5f);
        if (stage != kb.stage || pct / 5 != kb.percent / 5)
            kla_out(stage != kb.stage, "progress stage %lu %d%% -> %lu%%", stage, (int)(f * 100 + 0.5f), pct);
        kb.stage = stage; kb.percent = pct;
        break; }
    case H_ROOM: kb.rooms++; kb.geom = r->ecx;          /* fall through */
    case H_GEOMS: case H_SCNBLK: case H_REFFIX: case H_GBUF: case H_REFEND: case H_POST:
        kla_phase(kla_sites[id].what);
        break;
    case H_GINIT: {
        DWORD st = G32(0x1503910);
        kb.geom = r->ecx;
        if (st != kb.gstage) { kb.gstage = st; kb.gcount = 0; if (st) { kb.phase = kla_sites[id].what; kla_out(1, "geom init stage %lu begins", st); } }
        kb.gcount++;
        break; }
    case H_CLIST:
        kb.cstage = G32(0x150363c); kb.ocount = 0; kb.phase = kla_sites[id].what;
        kla_out(1, "object init stage %lu begins, %lu objects (geom init stage %lu did %lu calls)", kb.cstage, kla_rd32(r->ecx), kb.gstage, kb.gcount);
        break;
    case H_CINIT:
        kb.obj = sp[1]; kb.otarget = sp[2]; kb.ocount++;
        break;
    case H_OPENWIN: {                                   /* thiscall (name, bool, bool, bool); +0x4bc = busy: queued */
        char nm[64]; kla_rdstr(sp[1], nm, sizeof nm);
        kla_out(1, "window: open '%s' (%lu %lu %lu)%s", nm, sp[2] & 0xff, sp[3] & 0xff, sp[4] & 0xff, kla_rd32(r->ecx + 0x4bc) & 0xff ? " queued" : "");
        break; }
    case H_ELFOCUS: {                                   /* ecx = element+0xa8 for a ZNavigator (0x5af5d0); (window object, bool) */
        DWORD e = 0, g = sp[1]; int i; char cls[64];
        static const int offs[] = { 0xa8, 0xb0, 0xac, 0xa4, 0xb8, 0xc0, 0x98, 0x9c, 0xa0, 0xb4, 0xbc };
        if (!g) break;
        for (i = 0; i < (int)(sizeof offs / sizeof offs[0]) && !e; i++) {
            kla_rtti(r->ecx - offs[i], cls, sizeof cls);
            if (cls[0] && kla_rd32(r->ecx - offs[i] + 0x88) == g) e = r->ecx - offs[i];
        }
        kla_ask_geom = g; kla_ask_elem = e;
        break; }
    case H_FOCUS: {                                     /* window objects are shared between pages ('Button#04'), so the
                                                           owner is only known from the request that led here, or from
                                                           the code 0x7b the newly focused element is sent (H_INPUT) */
        char d[400]; DWORD g = sp[1];
        kla_zw = r->ecx;
        if (kla_rd32(r->ecx + 0x58) == g) break;
        kla_focus_elem = g == kla_ask_geom ? kla_ask_elem : 0; kla_ask_geom = 0;
        if (kla_focus_elem) kla_elem_desc(kla_focus_elem, d, sizeof d);
        else { char nm[64]; kla_geom_name(g, nm, sizeof nm); snprintf(d, sizeof d, "(window object %08lx '%s')", g, nm); }
        kla_out(1, "focus: %s", d);
        break; }
    case H_INPUT: {                                     /* (key code, ?, ?): every element that passes input to its base */
        static DWORD last_e, last_k, last_t; DWORD now = GetTickCount(); char cls[64], nm[48];
        if (sp[1] == 0x7b) kla_focus_elem = r->ecx;     /* 0x7b = "you have the focus" (0x606f2f sends it too) */
        if ((r->ecx == last_e && sp[1] == last_k && now - last_t < 1000) || kla_input_lines > 1500) break;
        last_e = r->ecx; last_k = sp[1]; last_t = now; kla_input_lines++;
        kla_rtti(r->ecx, cls, sizeof cls); kla_rdstr(kla_rd32(r->ecx + 4), nm, sizeof nm);
        kla_out(0, "input: code 0x%lx -> %s '%s'", sp[1], cls, nm);
        break; }
    }
}

/* stub: save flags, registers and the FPU/SSE state, call kla_dispatch(id, regs), restore, run the
   replaced instructions (position independent, see the table), jump back behind them. */
static BYTE *kla_emit(BYTE *p, int id, const BYTE *orig, int len, BYTE *back)
{
    static const BYTE pre[] = { 0x9c, 0x60, 0x8b, 0xec, 0x83, 0xe4, 0xf0, 0x81, 0xec, 0x00, 0x02, 0x00, 0x00,
                                0x0f, 0xae, 0x04, 0x24, 0xfc, 0x55, 0x68 };
        /* pushfd; pushad; mov ebp,esp; and esp,-16; sub esp,0x200; fxsave [esp]; cld; push ebp; push id */
    static const BYTE post[] = { 0x83, 0xc4, 0x08, 0x0f, 0xae, 0x0c, 0x24, 0x8b, 0xe5, 0x61, 0x9d };
        /* add esp,8; fxrstor [esp]; mov esp,ebp; popad; popfd */
    DWORD v;
    memcpy(p, pre, sizeof pre); p += sizeof pre;
    v = (DWORD)id; memcpy(p, &v, 4); p += 4;
    *p++ = 0xb8; v = (DWORD)(DWORD_PTR)kla_dispatch; memcpy(p, &v, 4); p += 4;      /* mov eax, handler */
    *p++ = 0xff; *p++ = 0xd0;                                                          /* call eax */
    memcpy(p, post, sizeof post); p += sizeof post;
    memcpy(p, orig, len); p += len;
    *p++ = 0xe9; v = (DWORD)(back - (p + 4)); memcpy(p, &v, 4); p += 4;               /* jmp back */
    return p;
}

static const char *kla_what = "klauto";            /* what the next kla_poke is, for the guard's log line */
static int kla_poke(BYTE *at, const BYTE *expect, const BYTE *bytes, int len)
{   /* replace len bytes, only if they are exactly the expected ones AND klhook.c's patch guard allows a write
       there under the run's policy ([KLHook] SessionSafe): a site inside a hashed range is refused */
    return klh_poke(at, expect, len, bytes, len, kla_what);
}

typedef void *(__fastcall *KLA_LOAD)(void *self, void *edx, void *arg);
static KLA_LOAD kla_real_load;

static void *__fastcall kla_scene_load(void *self, void *edx, void *arg)
{   /* in ZEngineDataBase's vtable in place of slot 8 (0x820300, thiscall, one stack argument) */
    void *ret; DWORD t = GetTickCount(), a0 = kla_asserts;
    kla_main_tid = GetCurrentThreadId(); kla_beat = t;
    kla_scene(kb.scene, sizeof kb.scene);
    kb.loading = 1; kb.load_t0 = t; kb.phase = "scene files"; kb.stage = 0; kb.percent = 0; kb.node = kb.total = kb.nodes_seen = kb.rooms = 0;
    kb.gstage = kb.gcount = kb.cstage = kb.ocount = 0; kb.ent[0] = kb.ctrl[0] = 0;
    kla_out(1, "LOAD start scene='%s' (argument %p)", kb.scene, arg);
    {   /* [Auto] Forbid: a scene this run must never load (the story, when the menu route goes wrong) */
        char f[128], *k, *ctx = 0;
        GetPrivateProfileStringA("Auto", "Forbid", "", f, sizeof f, kla_ini);
        for (k = strtok_s(f, ",", &ctx); k; k = strtok_s(0, ",", &ctx))
            if (*k && kla_contains(kb.scene, k)) { char rr[200]; snprintf(rr, sizeof rr, "forbidden scene '%s' was about to load ([Auto] Forbid=%s): stopped before it", kb.scene, k); kla_finish("FAIL", rr, KLA_SCRIPTFAIL); }
    }
    kla_result("RUNNING", "loading", -1);
    if (kla_watch_defer && !kla_frontend(kb.scene)) { kla_watch_defer = 0; kla_watch_arm = 1; SetEvent(kla_wake); }
    ret = kla_real_load(self, edx, arg);
    kb.loading = 0; kb.loads++; kb.phase = "running";
    snprintf(kb.done_scene, sizeof kb.done_scene, "%s", kb.scene);
    if (kb.scene[0] && !kla_frontend(kb.scene)) { kb.level_tick = GetTickCount() | 1; kb.level_frames = kla_frames; }
    kla_out(1, "LOAD end scene='%s' %lu ms, %lu nodes, %lu rooms, asserts during load %ld", kb.scene, GetTickCount() - t, kb.nodes_seen, kb.rooms, kla_asserts - a0);
    kla_result("RUNNING", "loaded", -1);
    return ret;
}

static void kla_engine_ini(void)
{   /* [Engine] lines behind the exe's baked ini text; the "push imm32" at 0x5987af then pushes our copy */
    char line[512], key[8]; int i, n; DWORD mine, baked = 0xb55dc0; BYTE exp[5] = { 0x68, 0xc0, 0x5d, 0xb5, 0x00 }, rep[5];
    if (!kla_rd((DWORD_PTR)VA(baked), kla_engine_text, 128)) kla_engine_text[0] = 0;   /* raw copy: the newlines matter (82 bytes + NUL) */
    kla_engine_text[128] = 0; n = (int)strlen(kla_engine_text);
    if (n < 14 || n > 120 || strncmp(kla_engine_text, "DefaultScene=", 13) || kla_engine_text[n - 1] != '\n') { kla_out(1, "engine ini: baked text not found at %08lx, [Engine] ignored", baked); return; }
    for (i = 1; i < 64; i++) {
        snprintf(key, sizeof key, "%d", i);
        if (!GetPrivateProfileStringA("Engine", key, "", line, sizeof line, kla_ini)) break;
        if (n + (int)strlen(line) + 2 >= (int)sizeof kla_engine_text) break;
        n += snprintf(kla_engine_text + n, sizeof kla_engine_text - n, "%s\n", line);
        kla_out(0, "engine ini: + %s", line);
    }
    if (i == 1) return;
    mine = (DWORD)(DWORD_PTR)kla_engine_text; rep[0] = 0x68; memcpy(rep + 1, &mine, 4);
    kla_what = "[Engine] push operand";
    kla_out(1, "engine ini: %d line(s) %s", i - 1, kla_poke(VA(0x5987af), exp, rep, 5) ? "installed (operand of the push at 0x5987af)" : "NOT installed: refused by the patch guard (use [Auto] CmdAdd in a session run), or bytes at 0x5987af differ");
    kla_what = "klauto";
}

static int kla_cmd_drop_in(char *cmd, char *keys)
{   /* blank every "-o <Key>=..." / "-o <Key>" pair of the listed keys; -> pairs blanked */
    char *p, *k, *ctx = 0; int n = 0;
    for (k = strtok_s(keys, ", ", &ctx); k; k = strtok_s(0, ", ", &ctx)) {
        size_t kl = strlen(k);
        for (p = cmd; (p = strstr(p, "-o")) != 0; p += 2) {
            char *v = p + 2, *e;
            if (p != cmd && p[-1] != ' ' && p[-1] != '\t') continue;          /* "-o" must be a token of its own */
            if (*v != ' ' && *v != '\t') continue;
            while (*v == ' ' || *v == '\t') v++;
            e = v; if (*e == '"') e++;
            if (_strnicmp(e, k, kl) || (e[kl] != '=' && e[kl] != ' ' && e[kl] != '"' && e[kl])) continue;
            if (*v == '"') { e = strchr(v + 1, '"'); e = e ? e + 1 : v + strlen(v); }
            else for (e = v; *e && *e != ' ' && *e != '\t'; e++) ;
            memset(p, ' ', e - p); n++;
        }
    }
    return n;
}

static char kla_cmd_new[2048];
static int kla_cmd_append(char *cmd, const char *add)
{   /* [Auto] CmdAdd when the launch options leave no stretch to reuse (2026-10-09: the owner's are '-dx10' alone now):
       the old text + ' ' + add in a buffer of our own, handed out in the two places the exe's start-up can take
       its command line from. Both are DATA of other modules, kl2.exe is not written:
         - KernelBase's pointer behind GetCommandLineA, when that function is the plain 'mov eax, [p]; ret'
           (a1 xx xx xx xx c3; anything else is left alone) - MSVCR90 copies that pointer into _acmdln when IT
           starts, should that be after us;
         - MSVCR90._acmdln, when it already points at the old text.
       -> the number of places changed (0 = the keys were not given: the script's first waitwin then fails).
       ASSUMPTION: nothing frees or re-reads the old buffer (GetCommandLineW is untouched). */
    BYTE *f = (BYTE *)GetProcAddress(GetModuleHandleA("KernelBase.dll"), "GetCommandLineA"), c[6]; int n = 0; DWORD old;
    HMODULE crt = GetModuleHandleA("MSVCR90.dll"); char **ac = crt ? (char **)GetProcAddress(crt, "_acmdln") : 0, **g;
    if (strlen(cmd) + strlen(add) + 2 > sizeof kla_cmd_new) return 0;
    snprintf(kla_cmd_new, sizeof kla_cmd_new, "%s %s", cmd, add);
    if (f && klh_rd((DWORD_PTR)f, c, 6) && c[0] == 0xa1 && c[5] == 0xc3) {
        memcpy(&g, c + 1, 4);
        if (klh_rd((DWORD_PTR)g, &old, 4) && (char *)(DWORD_PTR)old == cmd && VirtualProtect(g, 4, PAGE_READWRITE, &old)) {
            *g = kla_cmd_new; VirtualProtect(g, 4, old, &old); n++;
        }
    }
    if (ac && *ac == cmd) { *ac = kla_cmd_new; n++; }
    kla_out(1, "CmdAdd: GetCommandLineA %s, MSVCR90._acmdln %s", GetCommandLineA() == kla_cmd_new ? "answers the new buffer" : "NOT changed",
            !ac ? "not found" : *ac == kla_cmd_new ? "points at the new buffer" : !*ac ? "not set yet (MSVCR90 has not started)" : "left alone");
    return n;
}

static void kla_cmd_drop(void)
{   /* [Auto] CmdDrop=Key,Key on the process command line, in place (see the top comment) */
    char keys[256], *cmd = GetCommandLineA(); DWORD old; MEMORY_BASIC_INFORMATION mbi; int n;
    if (!GetPrivateProfileStringA("Auto", "CmdDrop", "", keys, sizeof keys, kla_ini) || !cmd) return;
    if (!VirtualQuery(cmd, &mbi, sizeof mbi)) return;
    if (!(mbi.Protect & (PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READWRITE)) && !VirtualProtect(cmd, strlen(cmd) + 1, PAGE_READWRITE, &old)) { kla_out(1, "CmdDrop: the command line is not writable"); return; }
    {   /* kl2.exe's startup hands WinMain *MSVCR90._acmdln (0xa8daaa). MSVCR90 sets it to GetCommandLineA()'s
           buffer; should it ever hold a copy of its own, that copy is treated too */
        char keys2[256]; HMODULE crt = GetModuleHandleA("MSVCR90.dll"); char **ac = crt ? (char **)GetProcAddress(crt, "_acmdln") : 0;
        GetPrivateProfileStringA("Auto", "CmdDrop", "", keys2, sizeof keys2, kla_ini);
        if (ac && *ac && *ac != cmd && VirtualQuery(*ac, &mbi, sizeof mbi) && (mbi.Protect & (PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READWRITE)))
            kla_out(1, "CmdDrop: MSVCR90._acmdln is a separate buffer: %d pair(s) blanked there", kla_cmd_drop_in(*ac, keys2));
    }
    n = kla_cmd_drop_in(cmd, keys);
    {   /* [Auto] CmdAdd=<text>: written into the blanked stretch (it must fit there). The way to give engine
           keys WITHOUT touching kl2.exe's code: [Engine] patches a push operand in .text, and a real Arcade
           session ends in the exe's anti-tamper exit (ExitProcess(0x8000dead) from 0x794ed6) when .text or
           the import table was changed (runs RN1-RN4 against RN5). */
        char add[256], *p, *q; size_t need;
        if (GetPrivateProfileStringA("Auto", "CmdAdd", "", add, sizeof add, kla_ini)) {
            need = strlen(add) + 2;
            for (p = cmd; *p; p = q) {
                for (q = p; *q == ' '; q++) ;
                if ((size_t)(q - p) >= need) { memcpy(p + 1, add, need - 2); break; }
                if (q == p) q++;
            }
            if (!*p) kla_out(1, "CmdAdd: no blanked stretch of %u characters for '%s': %s", (unsigned)need, add, kla_cmd_append(cmd, add) ? "given through a new command-line buffer" : "NOT given");
        }
    }
    kla_out(1, "CmdDrop: %d '-o' pair(s) blanked; command line now: %s", n, GetCommandLineA());
}

/* Who ends the process: kl2.exe's import slots of the calls that end it (or its window) are pointed at
   wrappers that log the return address and the kl2.exe callers on the stack, then call the real one.
   Slots read off the import table: ExitProcess 0xb1018c, exit 0xb103d0, _exit 0xb104b0, PostQuitMessage
   0xb105a8, DestroyWindow 0xb10640. */
static FARPROC kla_real_end[5];
static void kla_end_log(const char *what, DWORD arg, void *ra)
{
    CONTEXT c;
    if (kla_done) return;
    kla_flush();
    klog("END %s(%lu) called from kl2 %08lx, thread %lu (main %lu)", what, arg, (DWORD)(DWORD_PTR)ra, GetCurrentThreadId(), kla_main_tid);
    memset(&c, 0, sizeof c); c.Esp = (DWORD)(DWORD_PTR)&c;
    log_context(&c);
    kla_where();
}
static void WINAPI kla_w_exitprocess(UINT code) { kla_end_log("ExitProcess", code, _ReturnAddress()); ((void (WINAPI *)(UINT))kla_real_end[0])(code); }
static void __cdecl kla_w_exit(int code) { kla_end_log("exit", (DWORD)code, _ReturnAddress()); ((void (__cdecl *)(int))kla_real_end[1])(code); }
static void __cdecl kla_w__exit(int code) { kla_end_log("_exit", (DWORD)code, _ReturnAddress()); ((void (__cdecl *)(int))kla_real_end[2])(code); }
static void WINAPI kla_w_postquit(int code) { kla_end_log("PostQuitMessage", (DWORD)code, _ReturnAddress()); ((void (WINAPI *)(int))kla_real_end[3])(code); }
static BOOL WINAPI kla_w_destroy(HWND h) { kla_end_log("DestroyWindow", (DWORD)(DWORD_PTR)h, _ReturnAddress()); return ((BOOL (WINAPI *)(HWND))kla_real_end[4])(h); }

static void kla_end_hooks(void)
{
    static const DWORD slot[5] = { 0xb1018c, 0xb103d0, 0xb104b0, 0xb105a8, 0xb10640 };
    void *w[5]; int i, n = 0;
    w[0] = (void *)kla_w_exitprocess; w[1] = (void *)kla_w_exit; w[2] = (void *)kla_w__exit; w[3] = (void *)kla_w_postquit; w[4] = (void *)kla_w_destroy;
    for (i = 0; i < 5; i++) {
        DWORD cur = kla_rd32((DWORD_PTR)VA(slot[i])), mine = (DWORD)(DWORD_PTR)w[i];
        if (!cur || (cur >= img_lo && cur < img_hi)) continue;                    /* not bound to a DLL: leave it */
        kla_real_end[i] = (FARPROC)(DWORD_PTR)cur;
        kla_what = "exit import slot";
        n += kla_poke(VA(slot[i]), (BYTE *)&cur, (BYTE *)&mine, 4);
        kla_what = "klauto";
    }
    kla_out(1, "end hooks: %d of 5 import slots wrapped", n);
}

static DWORD kla_only = 0xffffffff;              /* bit i: detour i is installed; bit 31: the vtable entry ([Auto] Detours / VtLoad) */
static int kla_install(void)
{
    int i, ok = 0, want = 0; BYTE *p, jmp[10]; DWORD v, old = 0x820300, mine;
    kla_stubs = (BYTE *)VirtualAlloc(0, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!kla_stubs) return 0;
    for (i = 0, p = kla_stubs; i < H_COUNT; i++, p += 64) {
        BYTE *at = VA(kla_sites[i].va); int len = kla_sites[i].len;
        if (!(kla_only >> i & 1)) continue;
        want++;
        kla_emit(p, i, kla_sites[i].bytes, len, at + len);
        memset(jmp, 0x90, sizeof jmp); jmp[0] = 0xe9; v = (DWORD)(p - (at + 5)); memcpy(jmp + 1, &v, 4);
        kla_what = kla_sites[i].what;
        if (kla_poke(at, kla_sites[i].bytes, jmp, len)) ok++;
        else kla_out(0, "hook %08lx (%s) NOT installed: refused by the patch guard, or bytes differ", kla_sites[i].va, kla_sites[i].what);
    }
    kla_real_load = (KLA_LOAD)(DWORD_PTR)(old + kla_delta); mine = (DWORD)(DWORD_PTR)kla_scene_load;
    kla_what = "scene-load vtable entry";
    i = kla_only >> 31 ? kla_poke(VA(0xb8fa24), (BYTE *)&old, (BYTE *)&mine, 4) : 0;
    kla_what = "klauto";
    kla_out(1, "hooks: %d of %d detours installed (mask %08lx), scene-load wrapper %s; patch policy: %s", ok, want, kla_only, i ? "installed (vtable entry 0xb8fa24)" : "NOT installed",
            klh_policy_name[klh_policy]);
    if (!i) kla_hooks_on = 0;                       /* no LOAD start / end wrapper: loads are then noticed at the keyboard poll (kd_getdata) */
    return ok + i;
}

/* ---------------------------------------------------------------- script */

typedef struct { char op; BYTE key; DWORD n, n2; char text[80]; float f[4]; DWORD off[6]; BYTE noff; } KCMD;
enum { C_WAIT = 1, C_FRAMES, C_TAP, C_DOWN, C_UP, C_WAITSCENE, C_WAITLOAD, C_LOG, C_PASS, C_FAIL, C_QUIT, C_MSG, C_PEEK, C_SEL, C_EXPECT, C_WAITWIN, C_OPEN, C_WINDOWS, C_FOCUS, C_WATCH, C_MOUSE, C_MDOWN, C_MUP, C_POS, C_GOTO, C_FACE, C_ONWIN, C_LABEL, C_REWRITE, C_WAITSTATE, C_WAITVAN };
static KCMD kla_cmd[640]; static int kla_ncmd, kla_pc; static DWORD kla_cmd_t, kla_cmd_f, kla_seq;
static BYTE kla_held[256]; static DWORD kla_rel_t[256], kla_rel_f[256]; static int kla_taps, kla_started;

static int kla_script_pc(void) { return kla_ncmd ? kla_pc + 1 : 0; }
static int kla_key_held(int dik) { return dik >= 0 && dik < 256 && kla_held[dik] != 0; }      /* klhud.c klu_tab_held: a scripted Tab counts as held */

/* ---- scripted mouse: relative counts per second, fed through the mouse's GetDeviceState (DIMOUSESTATE2:
   lX +0, lY +4, lZ +8, buttons +12..; the game reads 0x14 bytes once a frame, kl2 0x650840) */
static float kla_m_rate[2], kla_m_acc[2]; static BYTE kla_m_btn[8]; static DWORD kla_m_last;
static int kla_trap = -1;                         /* line of the armed 'onwin' command */

/* ---- the players, read only. A ZFFPlayer is found by its vtable (0xbb45f4, RTTI) in the heap: 16 per level
   (Heroes!Hero_01..08\Ground, Heroes!RespawnPolice#01..08\Ground), all at 16-byte aligned addresses in the
   two runs looked at (PX1, PX2). Fields are in kla_pl_* below; they were found by sampling the process from
   outside while a script walked (runs PX2, PX3). No game function is called and nothing is written. */
#define KLA_VT_FFPLAYER 0xbb45f4u
static DWORD kla_pl[32]; static int kla_npl, kla_me = -1; static DWORD kla_pl_scan_t;
static DWORD kla_pos_off = 0x460;                 /* [Auto] PosOff: three floats x, y (up), z */
static DWORD kla_dir_off = 0xc14;                 /* [Auto] DirOff: three floats, the unit vector pointing BACK */
static float kla_turn_deg = 0.17f;                /* [Auto] TurnDeg: degrees of heading per mouse count (run PX3:
                                                     -1600 counts in 4 s turned the player by -272 degrees) */
static DWORD kla_poslog_ms, kla_poslog_t;         /* [Auto] PosLogMs: log the moving player's position that often */
/* goto state */
static DWORD kla_go_t, kla_go_stuck_t, kla_go_side_t; static float kla_go_from[3]; static int kla_go_w, kla_go_side, kla_go_shift, kla_go_n, kla_go_fin;
static float kla_pl_first[32][3]; static float kla_pl_path[32], kla_pl_prev[32][3];

static int kla_player_pos(int i, float *v)
{
    if (i < 0 || i >= kla_npl || !kla_rd(kla_pl[i] + kla_pos_off, v, 12)) return 0;
    return v[0] == v[0] && v[1] == v[1] && v[2] == v[2] && (v[0] != 0 || v[2] != 0);
}

static int kla_find_players(void)
{   /* scan the committed private read-write memory; 0.2 - 1 s, so only on demand and at most every 5 s */
    MEMORY_BASIC_INFORMATION mbi; BYTE *a = (BYTE *)0x10000; static BYTE buf[0x10000]; DWORD t0 = GetTickCount(); int i;
    if (kla_npl >= 16 && kla_rd32(kla_pl[0]) == KLA_VT_FFPLAYER) return kla_npl;
    if (kla_pl_scan_t && t0 - kla_pl_scan_t < 5000) return kla_npl;
    kla_npl = 0; kla_me = -1;
    while ((DWORD_PTR)a < 0x7ffe0000 && VirtualQuery(a, &mbi, sizeof mbi)) {
        if (mbi.State == MEM_COMMIT && mbi.Type == MEM_PRIVATE && (mbi.Protect == PAGE_READWRITE || mbi.Protect == PAGE_EXECUTE_READWRITE)) {
            SIZE_T o, k;
            for (o = 0; o < mbi.RegionSize; o += sizeof buf) {
                SIZE_T n = mbi.RegionSize - o < sizeof buf ? mbi.RegionSize - o : sizeof buf;
                if (!kla_rd((DWORD_PTR)mbi.BaseAddress + o, buf, n)) continue;
                for (k = 0; k + 4 <= n; k += 16)
                    if (*(DWORD *)(buf + k) == KLA_VT_FFPLAYER && kla_npl < 32) kla_pl[kla_npl++] = (DWORD)((DWORD_PTR)mbi.BaseAddress + o + k);
            }
        }
        a = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    kla_pl_scan_t = GetTickCount();
    for (i = 0; i < kla_npl; i++) { kla_pl_path[i] = 0; if (!kla_player_pos(i, kla_pl_first[i])) memset(kla_pl_first[i], 0, 12); memcpy(kla_pl_prev[i], kla_pl_first[i], 12); }
    kla_out(1, "players: %d ZFFPlayer object(s) found in %lu ms", kla_npl, kla_pl_scan_t - t0);
    return kla_npl;
}

static int kla_local_player(void)
{   /* the player the script moves: the game's own local player; when that pointer cannot be read, the one whose
       position has travelled furthest since the scan (the other fifteen stand still while nobody else plays;
       -1 until one has moved 30 units). */
    int i, best = -1; float v[3];
    kla_find_players();
    {   /* [gamedata + 0x828 + 4 * (char)[gamedata + 0x898]] (kl2 0x660b00): a ZFFPlayer, or nothing in the frontend */
        DWORD gd = kla_exe_ok ? kla_rd32((DWORD_PTR)VA(0xdd265c)) : 0, pl = 0; BYTE sel = 0xff;
        if (gd && kla_rd(gd + 0x898, &sel, 1) && sel < 28 && (pl = kla_rd32(gd + 0x828 + 4 * sel)) != 0 && kla_rd32(pl) == KLA_VT_FFPLAYER) {
            for (i = 0; i < kla_npl && kla_pl[i] != pl; i++) ;
            if (i == kla_npl && kla_npl < 32) {         /* not one the scan found (it looks at 16-byte steps): taken in */
                kla_pl[kla_npl++] = pl; kla_pl_path[i] = 0;
                if (!kla_player_pos(i, kla_pl_first[i])) memset(kla_pl_first[i], 0, 12);
                memcpy(kla_pl_prev[i], kla_pl_first[i], 12);
            }
            if (i < kla_npl) {
                if (i != kla_me) { kla_me = i; kla_out(1, "players: the local one is #%d at %08lx (the game's own pointer, slot %u)", i, pl, sel); }
                return kla_me;
            }
        }
    }
    for (i = 0; i < kla_npl; i++) {
        if (!kla_player_pos(i, v)) continue;
        if (kla_pl_prev[i][0] != 0 || kla_pl_prev[i][2] != 0) {
            float dx = v[0] - kla_pl_prev[i][0], dz = v[2] - kla_pl_prev[i][2], d = dx * dx + dz * dz;
            if (d < 250000.0f) kla_pl_path[i] += (float)sqrt(d);         /* a respawn is not walking */
        }
        memcpy(kla_pl_prev[i], v, 12);
        if (kla_pl_path[i] > 30.0f && (best < 0 || kla_pl_path[i] > kla_pl_path[best])) best = i;
    }
    if (best >= 0 && best != kla_me) { kla_me = best; kla_out(1, "players: the moving one is #%d at %08lx", best, kla_pl[best]); }
    return kla_me;
}

static int kla_player_dir(int i, float *deg)
{   /* heading in degrees, atan2(x, z) of the way the player faces: minus the vector at +0xc14. In run PX3 it
       equals the direction of travel to within 1 degree on every straight stretch (walking and sprinting)
       and keeps its value while the player stands. */
    float v[3];
    if (i < 0 || i >= kla_npl || !kla_rd(kla_pl[i] + kla_dir_off, v, 12) || (v[0] == 0 && v[2] == 0)) return 0;
    *deg = (float)(atan2(-v[0], -v[2]) * 57.29577951);
    return 1;
}

static void kla_log_pos(const char *label)
{
    int i, me = kla_local_player(); float v[3]; char line[900]; int n = 0;
    if (me >= 0 && kla_player_pos(me, v)) { float h = 0; kla_player_dir(me, &h); kla_out(1, "pos %s: me #%d (%.0f, %.0f, %.0f) heading %.0f", label, me, v[0], v[1], v[2], h); return; }
    n = snprintf(line, sizeof line, "pos %s: nobody has moved yet;", label);
    for (i = 0; i < kla_npl && n < 800; i++) if (kla_player_pos(i, v)) n += snprintf(line + n, sizeof line - n, " #%d (%.0f, %.0f, %.0f)", i, v[0], v[1], v[2]);
    kla_out(1, "%s", line);
}
static int kla_script_active(void) { return kla_pc < kla_ncmd; }

static int kla_key(const char *s)
{
    static const struct { const char *n; BYTE k; } t[] = {
        { "RETURN", 0x1c }, { "ENTER", 0x1c }, { "ESCAPE", 0x01 }, { "ESC", 0x01 }, { "SPACE", 0x39 }, { "TAB", 0x0f }, { "BACK", 0x0e },
        { "UP", 0xc8 }, { "DOWN", 0xd0 }, { "LEFT", 0xcb }, { "RIGHT", 0xcd }, { "LSHIFT", 0x2a }, { "LCONTROL", 0x1d }, { "LMENU", 0x38 },
        { "INSERT", 0xd2 }, { "DELETE", 0xd3 }, { "HOME", 0xc7 }, { "END", 0xcf }, { "PRIOR", 0xc9 }, { "NEXT", 0xd1 }, { "NUMPADENTER", 0x9c },
        { "F1", 0x3b }, { "F2", 0x3c }, { "F3", 0x3d }, { "F4", 0x3e }, { "F5", 0x3f }, { "F6", 0x40 }, { "F7", 0x41 }, { "F8", 0x42 },
        { "F9", 0x43 }, { "F10", 0x44 }, { "F11", 0x57 }, { "F12", 0x58 } };
    static const char rows[3][11] = { "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM" }; static const BYTE base[3] = { 0x10, 0x1e, 0x2c };
    int i; const char *p;
    if (s[0] == '0' && (s[1] == 'x' || s[1] == 'X')) return (int)strtoul(s, 0, 16) & 0xff;
    for (i = 0; i < (int)(sizeof t / sizeof t[0]); i++) if (!_stricmp(s, t[i].n)) return t[i].k;
    if (s[0] && !s[1]) {
        int c = s[0] >= 'a' && s[0] <= 'z' ? s[0] - 32 : s[0];
        if (c >= '1' && c <= '9') return 0x02 + c - '1';
        if (c == '0') return 0x0b;
        for (i = 0; i < 3; i++) if ((p = strchr(rows[i], c)) != 0) return base[i] + (int)(p - rows[i]);
    }
    return 0;
}

static void kla_script_load(void)
{
    char line[200], key[8], op[32], a[100]; int i;
    for (i = 1; i <= 640; i++) {
        KCMD *c = &kla_cmd[kla_ncmd]; char *rest;
        snprintf(key, sizeof key, "%d", i);
        if (!GetPrivateProfileStringA("Script", key, "", line, sizeof line, kla_ini)) break;
        op[0] = a[0] = 0; sscanf(line, "%31s %99s", op, a);
        rest = strstr(line, op) + strlen(op); while (*rest == ' ' || *rest == '\t') rest++;
        memset(c, 0, sizeof *c);
        if (!_stricmp(op, "wait")) { c->op = C_WAIT; c->n = strtoul(a, 0, 10); }
        else if (!_stricmp(op, "frames")) { c->op = C_FRAMES; c->n = strtoul(a, 0, 10); }
        else if (!_stricmp(op, "tap") || !_stricmp(op, "down") || !_stricmp(op, "up")) {
            c->op = (char)(!_stricmp(op, "tap") ? C_TAP : !_stricmp(op, "down") ? C_DOWN : C_UP); c->key = (BYTE)kla_key(a); c->n = 80;
            sscanf(rest + strlen(a), "%lu", &c->n);
            if (!c->key) { kla_out(1, "script line %d: unknown key '%s' - script not loaded", i, a); kla_ncmd = 0; return; }
        }
        else if (!_stricmp(op, "waitscene")) { c->op = C_WAITSCENE; snprintf(c->text, sizeof c->text, "%s", a); c->n = 120000; sscanf(rest + strlen(a), "%lu", &c->n); }
        else if (!_stricmp(op, "waitload")) { c->op = C_WAITLOAD; c->n = a[0] ? strtoul(a, 0, 10) : 240000; }
        else if (!_stricmp(op, "log")) { c->op = C_LOG; snprintf(c->text, sizeof c->text, "%s", rest); }
        else if (!_stricmp(op, "pass")) { c->op = C_PASS; c->n = strtoul(a, 0, 10); }
        else if (!_stricmp(op, "fail")) { c->op = C_FAIL; snprintf(c->text, sizeof c->text, "%s", rest); }
        else if (!_stricmp(op, "quit")) { c->op = C_QUIT; c->n = strtoul(a, 0, 10); }
        else if (!_stricmp(op, "msg")) {                /* text = element name, NUL, message */
            char m[64]; m[0] = 0; sscanf(rest + strlen(a), "%63s", m);
            if (!a[0] || !m[0] || strlen(a) + strlen(m) + 2 > sizeof c->text) { kla_out(1, "script line %d: msg needs <element> <message> - script not loaded", i); kla_ncmd = 0; return; }
            c->op = C_MSG; strcpy(c->text, a); strcpy(c->text + strlen(a) + 1, m);
        }
        else if (!_stricmp(op, "sel")) {
            char ad[32]; ad[0] = 0; c->n2 = 0; sscanf(rest + strlen(a), "%31s %lu", ad, &c->n2);
            c->op = C_SEL; c->n = strtoul(ad, 0, 16); snprintf(c->text, sizeof c->text, "%s", a);
            if (!a[0] || !c->n) { kla_out(1, "script line %d: sel needs <element> <hex address> <value> - script not loaded", i); kla_ncmd = 0; return; }
        }
        else if (!_stricmp(op, "expect")) { c->op = C_EXPECT; c->n = strtoul(a, 0, 16); c->n2 = 0; sscanf(rest + strlen(a), "%lu", &c->n2); }
        else if (!_stricmp(op, "waitwin")) { c->op = C_WAITWIN; snprintf(c->text, sizeof c->text, "%s", a); c->n = 15000; sscanf(rest + strlen(a), "%lu", &c->n); }
        else if (!_stricmp(op, "waitstate") || !_stricmp(op, "waitvan")) {      /* waitstate <state, hex or decimal> [timeout ms] / waitvan <state> [timeout ms] */
            c->op = (char)(!_stricmp(op, "waitstate") ? C_WAITSTATE : C_WAITVAN); c->n2 = strtoul(a, 0, 0); c->n = 60000; sscanf(rest + strlen(a), "%lu", &c->n);
            if (!a[0]) { kla_out(1, "script line %d: %s needs a state - script not loaded", i, op); kla_ncmd = 0; return; }
        }
        else if (!_stricmp(op, "open")) { c->op = C_OPEN; snprintf(c->text, sizeof c->text, "%s", a); }
        else if (!_stricmp(op, "windows")) c->op = C_WINDOWS;
        else if (!_stricmp(op, "focus")) {              /* focus <text> <key> [max taps, default 8] */
            char kn[32]; kn[0] = 0; c->n = 8; sscanf(rest + strlen(a), "%31s %lu", kn, &c->n);
            c->op = C_FOCUS; c->key = (BYTE)kla_key(kn); snprintf(c->text, sizeof c->text, "%s", a);
            if (!a[0] || !c->key) { kla_out(1, "script line %d: focus needs <text> <key> [max] - script not loaded", i); kla_ncmd = 0; return; }
        }
        else if (!_stricmp(op, "watch")) {              /* watch <hex address>[+<hex offset>] <1|2|4> <label>; address 0 = off */
            char *plus = strchr(a, '+'); char lab[48]; lab[0] = 0; c->n2 = 1;
            c->op = C_WATCH; c->n = strtoul(a, 0, 16); c->key = (BYTE)(plus != 0);
            sscanf(rest + strlen(a), "%lu %47s", &c->n2, lab);
            snprintf(c->text, sizeof c->text, "%s%s%s", plus ? plus + 1 : "0", " ", lab);
        }
        else if (!_stricmp(op, "mouse")) {              /* mouse <counts/s x> <counts/s y> <ms> */
            c->op = C_MOUSE; sscanf(rest, "%f %f %lu", &c->f[0], &c->f[1], &c->n);
        }
        else if (!_stricmp(op, "mdown") || !_stricmp(op, "mup")) { c->op = (char)(!_stricmp(op, "mdown") ? C_MDOWN : C_MUP); c->n = strtoul(a, 0, 10) & 7; }
        else if (!_stricmp(op, "goto") || !_stricmp(op, "face")) {      /* goto <x> <z> [radius 120] [timeout ms 20000] [sprint] [keep] */
            char w1[16], w2[16]; w1[0] = w2[0] = 0;
            c->op = (char)(!_stricmp(op, "goto") ? C_GOTO : C_FACE); c->f[2] = c->op == C_GOTO ? 120.0f : 4.0f; c->n = c->op == C_GOTO ? 20000 : 4000;
            if (sscanf(rest, "%f %f %f %lu %15s %15s", &c->f[0], &c->f[1], &c->f[2], &c->n, w1, w2) < 2) { kla_out(1, "script line %d: %s needs <x> <z> - script not loaded", i, op); kla_ncmd = 0; return; }
            c->key = (BYTE)((!_stricmp(w1, "sprint") || !_stricmp(w2, "sprint") ? 1 : 0) | (!_stricmp(w1, "keep") || !_stricmp(w2, "keep") ? 2 : 0));
        }
        else if (!_stricmp(op, "label")) { c->op = C_LABEL; snprintf(c->text, sizeof c->text, "%s", a); }
        else if (!_stricmp(op, "onwin")) {              /* onwin <window> <label>: text = window, NUL, label */
            char m[40]; m[0] = 0; sscanf(rest + strlen(a), "%39s", m);
            if (!a[0] || !m[0] || strlen(a) + strlen(m) + 2 > sizeof c->text) { kla_out(1, "script line %d: onwin needs <window> <label> - script not loaded", i); kla_ncmd = 0; return; }
            c->op = C_ONWIN; strcpy(c->text, a); strcpy(c->text + strlen(a) + 1, m);
        }
        else if (!_stricmp(op, "pos")) { c->op = C_POS; snprintf(c->text, sizeof c->text, "%s", rest); }
        else if (!_stricmp(op, "peek")) {
            char *plus = strchr(a, '+');                 /* <addr>[+off[+off...]]: every '+' follows one pointer, then adds */
            c->op = C_PEEK; c->n = strtoul(a, 0, 16); c->key = (BYTE)(plus != 0); c->n2 = plus ? strtoul(plus + 1, 0, 16) : 0;
            for (; plus && c->noff < 6; plus = strchr(plus + 1, '+')) c->off[c->noff++] = strtoul(plus + 1, 0, 16);
            if (plus) { kla_out(1, "script line %d: peek follows at most six pointers - script not loaded", i); kla_ncmd = 0; return; }
            snprintf(c->text, sizeof c->text, "%s", rest + strlen(a));
        }
        else if (!_stricmp(op, "rewrite")) {           /* rewrite <addr>[+off] <bytes> <label> */
            char *plus = strchr(a, '+'); char m[60]; m[0] = 0;
            c->op = C_REWRITE; c->n = strtoul(a, 0, 16); c->key = (BYTE)(plus != 0); c->n2 = plus ? strtoul(plus + 1, 0, 16) : 0;
            c->f[0] = 4; sscanf(rest + strlen(a), "%f %59s", &c->f[0], m); snprintf(c->text, sizeof c->text, "%s", m);
        }
        else { kla_out(1, "script line %d: unknown command '%s' - script not loaded", i, op); kla_ncmd = 0; return; }
        kla_ncmd++;
    }
    if (kla_ncmd) kla_out(1, "script: %d commands", kla_ncmd);
}

static void kla_event(DWORD *rg, DWORD *count, DWORD cap, int key, int down)
{   /* one DIDEVICEOBJECTDATA of the DirectInput 8 layout: dwOfs, dwData, dwTimeStamp, dwSequence, uAppData */
    DWORD *e;
    kla_held[key] = (BYTE)(down ? 0x80 : 0);
    if (*count >= cap) return;
    e = rg + 5 * *count; (*count)++;
    e[0] = (DWORD)key; e[1] = down ? 0x80 : 0; e[2] = GetTickCount(); e[3] = ++kla_seq; e[4] = 0;
}

typedef void *(__fastcall *KLA_FIND)(void *mgr, void *edx, const char *name);       /* 0x83faf0, thiscall, ret 4 */
typedef void (__fastcall *KLA_SEND)(void *elem, void *edx, const char **text);      /* vtbl+0x50, thiscall, ret 4 */

static DWORD kla_sel_t; static int kla_sel_n;

static int kla_msg(const char *elem, const char *msg)
{   /* what ZSendMessage does when activated (kl2 0x869ac2): find the element by name, call its slot 20
       with a pointer to a string object, which is one char* (0x83e2e0 builds it, 0x49f4ee reads [arg]).
       -> 1 sent, 0 no menu manager / no such element / not a kl2.exe vtable. */
    DWORD gui, mgr, vt, fn; void *e; char cls[64];
    if (!kla_exe_ok || !(gui = G32(0xdd265c)) || !(mgr = kla_rd32(gui + 0x824))) { kla_out(1, "msg: no menu manager yet"); return 0; }
    e = ((KLA_FIND)VA(0x83faf0))((void *)(DWORD_PTR)mgr, 0, elem);
    if (!e) { kla_out(1, "msg: no GUI element named '%s' in the open pages", elem); return 0; }
    vt = kla_rd32((DWORD_PTR)e); fn = kla_rd32(vt + 0x50); kla_rtti((DWORD_PTR)e, cls, sizeof cls);
    if (fn < img_lo || fn >= img_hi) { kla_out(1, "msg: element '%s' at %p has no usable vtable (%08lx)", elem, e, vt); return 0; }
    kla_out(1, "msg: '%s' -> %s '%s' at %p (slot 20 = %08lx)", msg, cls, elem, e, fn);
    ((KLA_SEND)(DWORD_PTR)fn)(e, 0, &msg);
    return 1;
}

/* The leaderboard row count fix (the score-page crash of run RN11) lives in klfix.c now: SHIP needs it too. */

static void kla_script_step(DWORD *rg, DWORD *count, DWORD cap)
{   /* called once per keyboard poll, on the game's thread */
    DWORD now = GetTickCount(); int k, guard = 0;
    if (!kla_started) { kla_started = 1; kla_cmd_t = now; kla_cmd_f = kla_frames; kla_out(1, "script: first keyboard poll, starting"); }
    for (k = 0; kla_taps && k < 256; k++)
        if (kla_rel_f[k] && (int)(now - kla_rel_t[k]) >= 0 && (int)(kla_frames - kla_rel_f[k]) >= 0) { kla_event(rg, count, cap, k, 0); kla_rel_f[k] = 0; kla_taps--; return; }
    if (kla_taps) return;                               /* the next command waits until every tap is released */
    if (kla_trap >= 0 && kla_trap < kla_ncmd && !_stricmp(kla_top, kla_cmd[kla_trap].text)) {
        /* 'onwin': the window came up (a round ended while the script was still walking): every held key and
           the mouse are let go, one event per poll, and the script goes on at the label */
        const char *lab = kla_cmd[kla_trap].text + strlen(kla_cmd[kla_trap].text) + 1; int j;
        kla_m_rate[0] = kla_m_rate[1] = 0; memset(kla_m_btn, 0, sizeof kla_m_btn);
        for (k = 0; k < 256; k++) if (kla_held[k]) { kla_event(rg, count, cap, k, 0); return; }
        kla_go_w = kla_go_shift = kla_go_side = kla_go_fin = kla_go_n = 0;
        for (j = 0; j < kla_ncmd; j++) if (kla_cmd[j].op == C_LABEL && !_stricmp(kla_cmd[j].text, lab)) break;
        kla_out(1, "script: window '%s' is up at line %d: going on at label '%s' (line %d)", kla_top, kla_pc + 1, lab, j + 1);
        kla_trap = -1; kla_pc = j; kla_cmd_t = now; kla_cmd_f = kla_frames;
    }
    while (kla_pc < kla_ncmd && guard++ < 16) {
        KCMD *c = &kla_cmd[kla_pc]; int next = 0;
        switch (c->op) {
        case C_WAIT: next = now - kla_cmd_t >= c->n; break;
        case C_FRAMES: next = kla_frames - kla_cmd_f >= c->n; break;
        case C_TAP: kla_event(rg, count, cap, c->key, 1); kla_rel_t[c->key] = now + c->n; kla_rel_f[c->key] = (kla_frames + 2) | 1; kla_taps++;
                    kla_out(1, "script %d: tap key 0x%02x", kla_pc + 1, c->key); next = 2; break;
        case C_DOWN: case C_UP: kla_event(rg, count, cap, c->key, c->op == C_DOWN); kla_out(1, "script %d: key 0x%02x %s", kla_pc + 1, c->key, c->op == C_DOWN ? "down" : "up"); next = 2; break;
        case C_WAITSCENE: case C_WAITLOAD:
            if (!kb.loading && (c->op == C_WAITSCENE ? kla_contains(kb.done_scene, c->text) : kb.level_tick != 0)) { kla_out(1, "script %d: scene '%s' is loaded", kla_pc + 1, kb.done_scene); next = 1; }
            else if (now - kla_cmd_t >= c->n) { char r[160]; snprintf(r, sizeof r, "script line %d: no such scene load within %lu ms (last loaded '%s')", kla_pc + 1, c->n, kb.done_scene); kla_where(); kla_finish("FAIL", r, KLA_SCRIPT); }
            break;
        case C_LOG: kla_out(1, "script %d: %s", kla_pc + 1, c->text); next = 1; break;
        case C_PASS: if (now - kla_cmd_t >= c->n) kla_pass("script reached pass"); break;
        case C_FAIL: kla_where(); kla_finish("FAIL", c->text, KLA_SCRIPTFAIL); break;
        case C_QUIT: kla_finish(c->n ? "FAIL" : "PASS", "script quit", (int)c->n); break;
        case C_MSG:
            if (kla_msg(c->text, c->text + strlen(c->text) + 1)) next = 2;
            else { char r[160]; snprintf(r, sizeof r, "script line %d: msg to '%s' could not be sent", kla_pc + 1, c->text); kla_where(); kla_finish("FAIL", r, KLA_SCRIPT); }
            break;
        case C_SEL: {
            DWORD v = 0xffffffff; kla_rd(VA(c->n) ? (DWORD_PTR)VA(c->n) : 0, &v, 4);
            if (v == c->n2) { kla_out(1, "script %d: %s is at %lu after %d step(s)", kla_pc + 1, c->text, v, kla_sel_n); kla_sel_n = 0; next = 1; break; }
            if (now - kla_sel_t < 250) return;
            kla_sel_t = now;
            if (now - kla_cmd_t > 10000 + 250u * 24 || kla_sel_n >= 24) { char r[160]; snprintf(r, sizeof r, "script line %d: %s did not reach %lu (value %lu after %d steps)", kla_pc + 1, c->text, c->n2, v, kla_sel_n); kla_where(); kla_finish("FAIL", r, KLA_SCRIPT); return; }
            if (v > 64) return;                         /* not a position yet: the page is not up */
            if (kla_msg(c->text, v > c->n2 ? "Decrease" : "Increase")) kla_sel_n++;
            return; }
        case C_EXPECT: { DWORD v = 0xffffffff; kla_rd((DWORD_PTR)VA(c->n), &v, 4);
            if (v == c->n2) { kla_out(1, "script %d: %08lx = %lu as expected", kla_pc + 1, c->n, v); next = 1; break; }
            { char r[160]; snprintf(r, sizeof r, "script line %d: %08lx is %lu, expected %lu", kla_pc + 1, c->n, v, c->n2); kla_where(); kla_finish("FAIL", r, KLA_SCRIPTFAIL); } return; }
        case C_WATCH: { DWORD at = c->n ? (DWORD)(DWORD_PTR)VA(c->n) : 0, off = strtoul(c->text, 0, 16); char *lab = strchr(c->text, ' ');
            if (at && c->key) at = kla_rd32(at) + off;
            kla_watch_addr = at; kla_watch_len = c->n2 == 2 || c->n2 == 4 ? c->n2 : 1; kla_watch_hits = 0;
            snprintf(kla_watch_label, sizeof kla_watch_label, "%s", lab ? lab + 1 : "");
            /* Steam's anti-debug probe (0xa8e3cb, raised once before every scene load) ends the process with a
               jump to 0 when it finds a debug register set (run RN2), so a label that starts with "load:" is
               armed only when the next level load has begun, after the probe */
            if (!strncmp(kla_watch_label, "load:", 5)) kla_watch_defer = 1; else { kla_watch_arm = 1; SetEvent(kla_wake); }
            kla_out(1, "script %d: watch %08lx requested%s", kla_pc + 1, at, kla_watch_defer ? " (armed at the next level load)" : ""); next = 2; break; }
        case C_WAITWIN:
            kla_windows(0);
            if (!_stricmp(kla_top, c->text)) { char d[400]; kla_focus_desc(d, sizeof d); kla_out(1, "script %d: window '%s' is on top; focus: %s", kla_pc + 1, kla_top, d); next = 1; }
            else if (now - kla_cmd_t >= c->n) { char r[300]; snprintf(r, sizeof r, "script line %d: window '%s' did not come up within %lu ms (stack: %.150s)", kla_pc + 1, c->text, c->n, kla_stack); kla_where(); kla_finish("FAIL", r, KLA_SCRIPT); }
            break;
        case C_WAITSTATE: {                             /* the session state: [[0x168e598]+0x70] (klsteam.c's 'session:' line reads the same dword) */
            DWORD sm = kla_exe_ok ? kla_rd32((DWORD_PTR)VA(0x168e598)) : 0, st = 0xffffffff;
            if (sm) kla_rd(sm + 0x70, &st, 4);
            if (st == c->n2) { kla_out(1, "script %d: the session state is 0x%lx after %lu ms", kla_pc + 1, st, now - kla_cmd_t); next = 1; }
            else if (now - kla_cmd_t >= c->n) { char r[160]; snprintf(r, sizeof r, "script line %d: the session state did not become 0x%lx within %lu ms (it is 0x%lx)", kla_pc + 1, c->n2, c->n, st); kla_where(); kla_finish("FAIL", r, KLA_SCRIPT); }
            break; }
        case C_WAITVAN: {                               /* the escape vehicle's state: byte [rules+0x1dc], rules = [[0x168e9e4]+0x54] with ZGameRulesHeist's vtable (klbot.c 1) */
            DWORD gs = kla_exe_ok ? kla_rd32((DWORD_PTR)VA(0x168e9e4)) : 0, rules = gs ? kla_rd32(gs + 0x54) : 0; BYTE veh = 0xff; float left = 0;
            if (rules && kla_rd32(rules) == 0xbd3514) { kla_rd(rules + 0x1dc, &veh, 1); kla_rd(rules + 0x1d8, &left, 4); }
            if (veh == c->n2 || (c->n2 == 3 && veh == 4) || (c->n2 == 1 && veh == 2)) {
                kla_out(1, "script %d: the vehicle's state is %u (its timer %.1f s) after %lu ms", kla_pc + 1, veh, left, now - kla_cmd_t); next = 1; }
            else if (now - kla_cmd_t >= c->n) {
                kla_out(1, "script %d: the vehicle's state did NOT become %lu within %lu ms (it is %u%s): the script goes on", kla_pc + 1, c->n2, c->n, veh, veh == 0xff ? " = no Arcade round object" : ""); next = 1; }
            break; }
        case C_OPEN: {                                  /* what 0x478b6b-0x478b74 does: system->0x6bee50(name, 1, 0, 1) */
            DWORD w = kla_wsys();
            if (!w) { kla_where(); kla_finish("FAIL", "open: no window system", KLA_SCRIPT); }
            kla_out(1, "script %d: open window '%s'", kla_pc + 1, c->text);
            ((void (__fastcall *)(void *, void *, const char *, int, int, int))VA(0x6bee50))((void *)(DWORD_PTR)w, 0, c->text, 1, 0, 1);
            next = 2; break; }
        case C_WINDOWS: { char d[400]; kla_windows(1); kla_focus_desc(d, sizeof d); kla_out(1, "script %d: focus: %s", kla_pc + 1, d); next = 1; break; }
        case C_FOCUS: { char d[400];
            if (now - kla_sel_t < 700) return;          /* let the last tap act */
            kla_focus_desc(d, sizeof d);
            if (kla_contains(d, c->text)) { kla_out(1, "script %d: focus is on %s after %d tap(s)", kla_pc + 1, d, kla_sel_n); kla_sel_n = 0; next = 1; break; }
            if ((DWORD)kla_sel_n >= c->n) { char r[400]; snprintf(r, sizeof r, "script line %d: focus did not reach '%s' after %d tap(s); it is on %.200s", kla_pc + 1, c->text, kla_sel_n, d); kla_sel_n = 0; kla_where(); kla_finish("FAIL", r, KLA_SCRIPT); return; }
            kla_event(rg, count, cap, c->key, 1); kla_rel_t[c->key] = now + 80; kla_rel_f[c->key] = (kla_frames + 2) | 1; kla_taps++;
            kla_sel_n++; kla_sel_t = now;
            kla_out(1, "script %d: tap key 0x%02x (focus was on %s)", kla_pc + 1, c->key, d);
            return; }
        case C_MOUSE:
            if (now - kla_cmd_t >= c->n) { kla_m_rate[0] = kla_m_rate[1] = 0; next = 1; }
            else { kla_m_rate[0] = c->f[0]; kla_m_rate[1] = c->f[1]; }
            break;
        case C_MDOWN: case C_MUP: kla_m_btn[c->n] = (BYTE)(c->op == C_MDOWN ? 0x80 : 0); kla_out(1, "script %d: mouse button %lu %s", kla_pc + 1, c->n, c->op == C_MDOWN ? "down" : "up"); next = 1; break;
        case C_POS: kla_log_pos(c->text); next = 1; break;
        case C_LABEL: next = 1; break;
        case C_ONWIN: kla_trap = kla_pc; kla_out(1, "script %d: when window '%s' comes up, go to label '%s'", kla_pc + 1, c->text, c->text + strlen(c->text) + 1); next = 1; break;
        case C_GOTO: case C_FACE: {
            /* steer the moving player to (x, z): W held, the mouse turned in proportion to the bearing error.
               No path finding: the script gives way points (taken from the level's navigation mesh). A player
               that does not get on for 1.5 s side-steps (A or D in turn) for 0.7 s. A timeout is logged and
               the script goes on: the pictures and the position log say what happened. */
            int me = kla_local_player(), walk = c->op == C_GOTO; float v[3], h, dx, dz, dist, err, rate;
            if (kla_go_fin) {                           /* one key event per poll: let go of what this step held */
                kla_m_rate[0] = kla_m_rate[1] = 0;
                if (kla_go_side) { kla_event(rg, count, cap, kla_go_side, 0); kla_go_side = 0; return; }
                if (kla_go_shift && !(c->key & 2)) { kla_event(rg, count, cap, 0x2a, 0); kla_go_shift = 0; return; }
                if (kla_go_w && !(c->key & 2)) { kla_event(rg, count, cap, 0x11, 0); kla_go_w = 0; return; }
                kla_go_fin = 0; kla_go_n = 0; next = 1; break;
            }
            if (walk && !(c->key & 1) && kla_go_shift) { kla_event(rg, count, cap, 0x2a, 0); kla_go_shift = 0; return; }
            if (kla_go_n != kla_pc + 1) { kla_go_n = kla_pc + 1; kla_go_t = now; kla_go_stuck_t = now; kla_go_side_t = 0; memset(kla_go_from, 0, 12); }
            if (walk && !kla_go_w) { kla_event(rg, count, cap, 0x11, 1); kla_go_w = 1; return; }
            if (walk && (c->key & 1) && !kla_go_shift) { kla_event(rg, count, cap, 0x2a, 1); kla_go_shift = 1; return; }
            if (me < 0 || !kla_player_pos(me, v) || !kla_player_dir(me, &h)) {
                if (now - kla_go_t > 6000) { kla_out(1, "script %d: no moving player found (%d ZFFPlayer objects) - step skipped", kla_pc + 1, kla_npl); goto go_done; }
                return;
            }
            dx = c->f[0] - v[0]; dz = c->f[1] - v[2]; dist = (float)sqrt(dx * dx + dz * dz);
            err = (float)(atan2(dx, dz) * 57.29577951) - h; while (err > 180) err -= 360; while (err < -180) err += 360;
            if (walk ? dist <= c->f[2] : (err < c->f[2] && err > -c->f[2])) {
                kla_out(1, "script %d: %s (%.0f, %.0f) reached in %lu ms: at (%.0f, %.0f, %.0f) heading %.0f", kla_pc + 1, walk ? "goto" : "face", c->f[0], c->f[1], now - kla_go_t, v[0], v[1], v[2], h);
                goto go_done;
            }
            if (now - kla_go_t >= c->n) {
                kla_out(1, "script %d: %s (%.0f, %.0f) NOT reached in %lu ms: at (%.0f, %.0f, %.0f) heading %.0f, %.0f away, bearing error %.0f", kla_pc + 1, walk ? "goto" : "face", c->f[0], c->f[1], c->n, v[0], v[1], v[2], h, dist, err);
                goto go_done;
            }
            rate = err / kla_turn_deg * 5.0f; if (rate > 1800) rate = 1800; if (rate < -1800) rate = -1800;
            kla_m_rate[0] = rate; kla_m_rate[1] = 0;
            if (walk) {
                if (kla_go_side && now - kla_go_side_t > 700) { kla_event(rg, count, cap, kla_go_side, 0); kla_go_side = 0; kla_go_stuck_t = now; memcpy(kla_go_from, v, 12); return; }
                if (kla_go_from[0] == 0 && kla_go_from[2] == 0) memcpy(kla_go_from, v, 12);
                if (now - kla_go_stuck_t > 1500) {
                    float mx = v[0] - kla_go_from[0], mz = v[2] - kla_go_from[2];
                    if (mx * mx + mz * mz < 40.0f * 40.0f && !kla_go_side) {
                        static int flip;
                        if (++flip % 3 == 0) {                  /* every third time: C = 'Get Up' when the player is down (Arcade) */
                            kla_out(1, "script %d: goto is stuck at (%.0f, %.0f, %.0f), %.0f away: tap C (get up)", kla_pc + 1, v[0], v[1], v[2], dist);
                            kla_event(rg, count, cap, 0x2e, 1); kla_rel_t[0x2e] = now + 120; kla_rel_f[0x2e] = (kla_frames + 2) | 1; kla_taps++;
                            kla_go_stuck_t = now; return;
                        }
                        kla_go_side = (flip & 1) ? 0x1e : 0x20; kla_go_side_t = now;
                        kla_out(1, "script %d: goto is stuck at (%.0f, %.0f, %.0f) heading %.0f, %.0f away: side step %s", kla_pc + 1, v[0], v[1], v[2], h, dist, kla_go_side == 0x1e ? "A" : "D");
                        kla_event(rg, count, cap, kla_go_side, 1); return;
                    }
                    kla_go_stuck_t = now; memcpy(kla_go_from, v, 12);
                }
            }
            return;
        go_done:
            kla_go_fin = 1; return; }
        case C_PEEK: { DWORD v = 0, at = (DWORD)(DWORD_PTR)VA(c->n); int ok = kla_rd(at, &v, 4), j, n; char ch[80];
            n = snprintf(ch, sizeof ch, "%08lx", c->n);
            for (j = 0; j < c->noff; j++) {
                n += snprintf(ch + n, sizeof ch - n, "+%lx", c->off[j]);
                if (ok) { ok = v > 0xffff; at = v + c->off[j]; v = 0; ok = ok && kla_rd(at, &v, 4); }
            }
            kla_out(1, "script %d: peek %s = %s%08lx%s (at %08lx) %s", kla_pc + 1, ch, ok ? "" : "unreadable ", v, ok ? "" : " (a null or bad pointer on the way)", at, c->text); next = 1; break; }
        case C_REWRITE: {                               /* the same bytes written back: a data write that changes nothing */
            BYTE b[64]; DWORD v = 0, at = (DWORD)(DWORD_PTR)VA(c->n); int n = (int)c->f[0], ok = 1, j; char hex[3 * 16 + 1], txt[17];
            MEMORY_BASIC_INFORMATION mbi;
            if (n < 1 || n > 64) n = 4;
            if (c->key) { ok = kla_rd(at, &v, 4) && v; at = v + c->n2; }
            ok = ok && kla_rd(at, b, n) && VirtualQuery((void *)(DWORD_PTR)at, &mbi, sizeof mbi) && (mbi.Protect & (PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READWRITE));
            if (ok) memcpy((void *)(DWORD_PTR)at, b, n);
            for (j = 0; j < n && j < 16; j++) { sprintf(hex + 3 * j, "%02x ", b[j]); txt[j] = (char)(b[j] >= 32 && b[j] < 127 ? b[j] : '.'); }
            hex[3 * j] = 0; txt[j] = 0;
            kla_out(1, "script %d: rewrite %08lx%s -> %08lx, %d byte(s) %s: %s'%s' %s", kla_pc + 1, c->n, c->key ? "+" : "", at, n,
                    ok ? "written back" : "NOT WRITTEN (unreadable, null pointer or not writable)", ok ? hex : "", ok ? txt : "", c->text); next = 1; break; }
        }
        if (!next) return;
        kla_pc++; kla_cmd_t = now; kla_cmd_f = kla_frames;
        if (next == 2) return;                          /* at most one key event per poll */
    }
}

/* ---------------------------------------------------------------- DirectInput proxies */

typedef void (*KFN)(void);
typedef struct KPX { KFN *vtbl; void **real; int kind; } KPX;      /* kind: 0 IDirectInput8, 1 device, 2 keyboard, 3 mouse */
#define KRV(p, i) ((*(void ***)(p)->real)[i])
#define KF0(pre, i) static HRESULT WINAPI pre##i(KPX *p) { return ((HRESULT (WINAPI *)(void *))KRV(p, i))(p->real); }
#define KF1(pre, i) static HRESULT WINAPI pre##i(KPX *p, DWORD a) { return ((HRESULT (WINAPI *)(void *, DWORD))KRV(p, i))(p->real, a); }
#define KF2(pre, i) static HRESULT WINAPI pre##i(KPX *p, DWORD a, DWORD b) { return ((HRESULT (WINAPI *)(void *, DWORD, DWORD))KRV(p, i))(p->real, a, b); }
#define KF3(pre, i) static HRESULT WINAPI pre##i(KPX *p, DWORD a, DWORD b, DWORD c) { return ((HRESULT (WINAPI *)(void *, DWORD, DWORD, DWORD))KRV(p, i))(p->real, a, b, c); }
#define KF4(pre, i) static HRESULT WINAPI pre##i(KPX *p, DWORD a, DWORD b, DWORD c, DWORD d) { return ((HRESULT (WINAPI *)(void *, DWORD, DWORD, DWORD, DWORD))KRV(p, i))(p->real, a, b, c, d); }
#define KF5(pre, i) static HRESULT WINAPI pre##i(KPX *p, DWORD a, DWORD b, DWORD c, DWORD d, DWORD e) { return ((HRESULT (WINAPI *)(void *, DWORD, DWORD, DWORD, DWORD, DWORD))KRV(p, i))(p->real, a, b, c, d, e); }

static HRESULT WINAPI kpx_qi(KPX *p, DWORD riid, void **out)
{   /* the proxy stands for the interface it wraps; any other interface is handed out unwrapped */
    HRESULT hr = ((HRESULT (WINAPI *)(void *, DWORD, void **))KRV(p, 0))(p->real, riid, out);
    if (SUCCEEDED(hr) && out && *out == (void *)p->real) *out = p;
    return hr;
}
static ULONG WINAPI kpx_addref(KPX *p) { return ((ULONG (WINAPI *)(void *))KRV(p, 1))(p->real); }
static ULONG WINAPI kpx_release(KPX *p)
{
    ULONG n = ((ULONG (WINAPI *)(void *))KRV(p, 2))(p->real);
    if (!n) HeapFree(GetProcessHeap(), 0, p);
    return n;
}

/* IDirectInputDevice8: 3 GetCapabilities 4 EnumObjects 5 GetProperty 6 SetProperty 7 Acquire 8 Unacquire
   9 GetDeviceState 10 GetDeviceData 11 SetDataFormat 12 SetEventNotification 13 SetCooperativeLevel
   14 GetObjectInfo 15 GetDeviceInfo 16 RunControlPanel 17 Initialize 18 CreateEffect 19 EnumEffects
   20 GetEffectInfo 21 GetForceFeedbackState 22 SendForceFeedbackCommand 23 EnumCreatedEffectObjects
   24 Escape 25 Poll 26 SendDeviceData 27 EnumEffectsInFile 28 WriteEffectToFile 29 BuildActionMap
   30 SetActionMap 31 GetImageInfo. Every argument is a DWORD or a pointer, so only the count matters. */
KF1(kd, 3) KF3(kd, 4) KF2(kd, 5) KF2(kd, 6) KF0(kd, 8) KF1(kd, 12) KF2(kd, 13) KF3(kd, 14) KF1(kd, 15) KF2(kd, 16)
KF3(kd, 17) KF4(kd, 18) KF3(kd, 19) KF2(kd, 20) KF1(kd, 21) KF1(kd, 22) KF3(kd, 23) KF1(kd, 24) KF0(kd, 25)
KF4(kd, 26) KF4(kd, 27) KF4(kd, 28) KF3(kd, 29) KF3(kd, 30) KF1(kd, 31)

static HRESULT WINAPI kd_acquire(KPX *p)
{
    HRESULT hr = ((HRESULT (WINAPI *)(void *))KRV(p, 7))(p->real);
    if (FAILED(hr) && (p->kind == 2 || p->kind == 3) && kla_unfocused && kla_script_active()) return 0;   /* the game then polls us (0x8fa0a0) */
    return hr;
}

static HRESULT WINAPI kd_setformat(KPX *p, DWORD *fmt)
{   /* DIDATAFORMAT.dwDataSize (+12): 256 = c_dfDIKeyboard, 20 = c_dfDIMouse2, 16 = c_dfDIMouse */
    DWORD size = fmt ? kla_rd32((DWORD_PTR)fmt + 12) : 0;
    if (size == 256) p->kind = 2; else if (size == 20 || size == 16) p->kind = 3;
    kla_out(1, "input: device %p data format size %lu -> %s", (void *)p->real, size, p->kind == 2 ? "keyboard" : p->kind == 3 ? "mouse" : "other");
    return ((HRESULT (WINAPI *)(void *, DWORD *))KRV(p, 11))(p->real, fmt);
}

static HRESULT WINAPI kd_getstate(KPX *p, DWORD cb, BYTE *data)
{
    HRESULT hr = ((HRESULT (WINAPI *)(void *, DWORD, BYTE *))KRV(p, 9))(p->real, cb, data);
    int k;
    if (!data || !kla_script_active()) return hr;
    if (p->kind == 3) {                                 /* the scripted mouse; the real one is dropped while a script runs */
        DWORD now = GetTickCount(); float dt = kla_m_last ? (now - kla_m_last) / 1000.0f : 0; int i;
        if (FAILED(hr)) { if (!kla_unfocused) return hr; memset(data, 0, cb); hr = 0; }
        else if (kla_block) memset(data, 0, cb);
        kla_m_last = now; if (dt > 0.1f) dt = 0.1f;
        for (i = 0; i < 2 && cb >= 8; i++) {
            LONG whole;
            kla_m_acc[i] += kla_m_rate[i] * dt; whole = (LONG)kla_m_acc[i]; kla_m_acc[i] -= (float)whole;
            *(LONG *)(data + 4 * i) += whole;
        }
        for (i = 0; i < 8 && 12 + i < (int)cb; i++) if (kla_m_btn[i]) data[12 + i] = 0x80;
        return hr;
    }
    if (p->kind != 2) return hr;
    if (FAILED(hr)) { if (!kla_unfocused) return hr; memset(data, 0, cb); hr = 0; }
    else if (kla_block) memset(data, 0, cb);
    for (k = 0; k < 256 && k < (int)cb; k++) if (kla_held[k]) data[k] = 0x80;
    return hr;
}

static HRESULT WINAPI kd_getdata(KPX *p, DWORD cb, DWORD *rg, DWORD *count, DWORD flags)
{
    DWORD cap = count ? *count : 0, n;
    HRESULT hr = ((HRESULT (WINAPI *)(void *, DWORD, DWORD *, DWORD *, DWORD))KRV(p, 10))(p->real, cb, rg, count, flags);
    static int told;
    if (p->kind != 2) return hr;
    if (!kla_hooks_on || !kla_exe_ok) {                 /* no scene-load wrapper: a load shows as a pause in the polls
                                                           (the keyboard is not read while a scene loads) and a new name */
        static DWORD last, chk; DWORD now = GetTickCount(); char sc[128];
        /* the name is also looked at four times a second: a level that loads in under 3 s (the Dead Men maps in slots
           F01 and F04: 2 s) made no pause long enough, 'waitload' never saw it and the script stood at that line for
           its whole timeout (runs E3_DM01, B1_DM01, I1_DM01, I4_DM06, PB_DM01 / PB_DM06, 2026-10-11) */
        if (!last || now - last > 3000 || now - chk >= 250) {
            chk = now;
            kla_scene(sc, sizeof sc);
            if (sc[0] && _stricmp(sc, kb.done_scene)) {
                snprintf(kb.scene, sizeof kb.scene, "%s", sc); snprintf(kb.done_scene, sizeof kb.done_scene, "%s", sc); kb.loads++; kb.phase = "running";
                if (!kla_frontend(sc)) { kb.level_tick = now | 1; kb.level_frames = kla_frames; }
                kla_out(1, "LOAD end scene='%s' (no hooks: seen at the first keyboard poll after a pause of %lu ms)", sc, last ? now - last : 0);
                kla_result("RUNNING", "loaded", -1);
            }
        }
        last = now;
    }
    kla_frames++; kla_beat = GetTickCount(); kla_main_tid = GetCurrentThreadId();
    if (!told) { char s[128]; DWORD sys = kla_sysif(); float ax = 0; told = 1; kla_scene(s, sizeof s); if (sys) kla_rd(sys + 0x68, &ax, 4);
                 kla_out(1, "input: first keyboard poll (result %08lx); scene='%s' AutoExit=%g", (DWORD)hr, s, ax); }
    if (kla_exe_ok && !kb.loading) kla_windows(0);
    klh_tick(1);                                        /* klfix.c / klslot.c: also driven from here, in case the SteamAPI_RunCallbacks slot is silent */
    if (kla_poslog_ms && kb.level_tick && !kb.loading && GetTickCount() - kla_poslog_t >= kla_poslog_ms && GetTickCount() - kb.level_tick > 8000) { kla_poslog_t = GetTickCount(); kla_log_pos("tick"); }
    if (!kla_script_active() || !rg || !count || cb != 20 || (flags & 1)) return hr;      /* 1 = DIGDD_PEEK */
    n = *count;
    if (FAILED(hr)) { if (!kla_unfocused) return hr; n = 0; }
    else if (kla_block) n = 0;
    if (n > cap) n = cap;
    kla_script_step(rg, &n, cap);
    *count = n;
    return 0;                                           /* never DI_BUFFEROVERFLOW: the game treats 1 as a failure */
}

#define K(f) (KFN)f
static KFN kd_vtbl[32] = {
    K(kpx_qi), K(kpx_addref), K(kpx_release), K(kd3), K(kd4), K(kd5), K(kd6), K(kd_acquire), K(kd8), K(kd_getstate), K(kd_getdata),
    K(kd_setformat), K(kd12), K(kd13), K(kd14), K(kd15), K(kd16), K(kd17), K(kd18), K(kd19), K(kd20), K(kd21), K(kd22), K(kd23),
    K(kd24), K(kd25), K(kd26), K(kd27), K(kd28), K(kd29), K(kd30), K(kd31) };

static void *kla_wrap(void *real, KFN *vtbl, int kind)
{
    KPX *p = (KPX *)HeapAlloc(GetProcessHeap(), 0, sizeof *p);
    if (!p) return real;
    p->vtbl = vtbl; p->real = (void **)real; p->kind = kind;
    return p;
}

/* IDirectInput8: 3 CreateDevice 4 EnumDevices 5 GetDeviceStatus 6 FindDevice 7 RunControlPanel
   8 Initialize 9 EnumDevicesBySemantics 10 ConfigureDevices */
KF4(ki, 4) KF1(ki, 5) KF3(ki, 6) KF2(ki, 7) KF2(ki, 8) KF5(ki, 9) KF4(ki, 10)

static HRESULT WINAPI ki_create(KPX *p, const GUID *g, void **out, void *outer)
{
    static const GUID kbd = { 0x6f1d2b61, 0xd5a0, 0x11cf, { 0xbf, 0xc7, 0x44, 0x45, 0x53, 0x54, 0x00, 0x00 } };   /* GUID_SysKeyboard */
    static const GUID mouse = { 0x6f1d2b60, 0xd5a0, 0x11cf, { 0xbf, 0xc7, 0x44, 0x45, 0x53, 0x54, 0x00, 0x00 } }; /* GUID_SysMouse */
    HRESULT hr = ((HRESULT (WINAPI *)(void *, const GUID *, void **, void *))KRV(p, 3))(p->real, g, out, outer);
    if (SUCCEEDED(hr) && out && *out && !outer)
        *out = kla_wrap(*out, kd_vtbl, g && !memcmp(g, &kbd, sizeof kbd) ? 2 : g && !memcmp(g, &mouse, sizeof mouse) ? 3 : 1);
    return hr;
}
static KFN ki_vtbl[11] = { K(kpx_qi), K(kpx_addref), K(kpx_release), K(ki_create), K(ki4), K(ki5), K(ki6), K(ki7), K(ki8), K(ki9), K(ki10) };

/* ---------------------------------------------------------------- faults, watchdog */

static void kla_dump_now(EXCEPTION_POINTERS *ep, const char *name)
{   /* own dump for cases klhook.c's write_dump cannot take (no exception record, or another thread's) */
    HMODULE h = LoadLibraryA("dbghelp.dll"); MDWD w = h ? (MDWD)GetProcAddress(h, "MiniDumpWriteDump") : 0;
    char path[MAX_PATH]; HANDLE f; MEI mei;
    if (!w) return;
    snprintf(path, sizeof path, "%s\\%s", klh_out, name);
    f = CreateFileA(path, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, 0, 0);
    if (f == INVALID_HANDLE_VALUE) return;
    mei.tid = GetCurrentThreadId(); mei.ep = ep; mei.client = FALSE;
    if (!w(GetCurrentProcess(), GetCurrentProcessId(), f, 0x1 | 0x40 | 0x1000 | 0x800, ep ? &mei : 0, 0, 0)) {    /* as klhook.c's write_dump */
        SetFilePointer(f, 0, 0, FILE_BEGIN); SetEndOfFile(f);
        w(GetCurrentProcess(), GetCurrentProcessId(), f, 0x1 | 0x40 | 0x1000, ep ? &mei : 0, 0, 0);
    }
    CloseHandle(f);
    kla_out(1, "  dump written: %s", name);
}

static int kla_bad_code(DWORD c)
{
    return c == 0xc0000005 || c == 0xc000001d || c == 0xc0000094 || c == 0xc00000fd || c == 0xc0000096 || c == 0xc0000006 ||
           c == 0xc0000374 || c == 0xc0000409 || c == 0xc0000417 || c == 0xc000008c || c == 0xc0000025 || c == 0xc000001e;
}

static void kla_log_fault(EXCEPTION_POINTERS *ep, const char *tag)
{
    char mod[80]; DWORD off, code = ep->ExceptionRecord->ExceptionCode; DWORD_PTR at = (DWORD_PTR)ep->ExceptionRecord->ExceptionAddress;
    kla_module(at, mod, sizeof mod, &off);
    if (!strstr(tag, "first chance")) snprintf(kla_last_fault, sizeof kla_last_fault, "%08lx at %s+0x%lx", code, mod, off);
    kla_flush();
    klog("%s %08lx at %s+0x%lx (%08lx)", tag, code, mod, off, (DWORD)at);
    if (code == 0xc0000005 && ep->ExceptionRecord->NumberParameters >= 2)
        klog("  %s address %08lx", ep->ExceptionRecord->ExceptionInformation[0] ? "writing" : "reading", (DWORD)ep->ExceptionRecord->ExceptionInformation[1]);
    log_context(ep->ContextRecord);
    kla_where();
}

static LONG CALLBACK kla_veh(EXCEPTION_POINTERS *ep)
{   /* registered in front of klhook.c's handler; never resumes anything itself */
    static DWORD_PTR at_seen[64]; static int at_n; static LONG total;
    DWORD code = ep->ExceptionRecord->ExceptionCode; DWORD_PTR at = (DWORD_PTR)ep->ExceptionRecord->ExceptionAddress;
    int i, first = 1, inside = at >= img_lo && at < img_hi;
    if (code == 0x80000004 && kla_watch_addr && (ep->ContextRecord->Dr6 & 1)) {            /* our write watch (DR0) */
        ep->ContextRecord->Dr6 = 0;
        if (kla_done || TlsGetValue(kla_tls)) return EXCEPTION_CONTINUE_EXECUTION;
        if (InterlockedIncrement((LONG *)&kla_watch_hits) <= 60) {
            DWORD v = 0; kla_rd(kla_watch_addr, &v, kla_watch_len);
            TlsSetValue(kla_tls, (void *)1);
            kla_flush();
            klog("WATCH '%s' %08lx written: now %0*lx, by the instruction before kl2 %08lx, thread %lu", kla_watch_label, kla_watch_addr, (int)kla_watch_len * 2, v, (DWORD)at, GetCurrentThreadId());
            log_context(ep->ContextRecord);
            TlsSetValue(kla_tls, 0);
        }
        return EXCEPTION_CONTINUE_EXECUTION;
    }
    if (kla_done || TlsGetValue(kla_tls)) return EXCEPTION_CONTINUE_SEARCH;    /* e.g. IsBadReadPtr probing inside log_context */
    if (code == 0xc00000fd) {                           /* stack overflow: no room to log on this thread */
        kla_so_ep = ep; SetEvent(kla_wake); Sleep(10000);
        return EXCEPTION_CONTINUE_SEARCH;
    }
    if (inside ? code != EXCEPTION_BREAKPOINT && !kla_bad_code(code) : !kla_bad_code(code)) return EXCEPTION_CONTINUE_SEARCH;
    if (inside && at == (DWORD_PTR)VA(0xa8e3cb)) return EXCEPTION_CONTINUE_SEARCH;       /* Steam's anti-debug probe, not a fault */
    EnterCriticalSection(&kla_cs);
    for (i = 0; i < at_n; i++) if (at_seen[i] == at) first = 0;
    if (first && at_n < 64) at_seen[at_n++] = at;
    LeaveCriticalSection(&kla_cs);
    InterlockedIncrement(&total);
    TlsSetValue(kla_tls, (void *)1);
    if (inside) {                                       /* klhook.c logs the ASSERT / CRASH lines right after this */
        if (code == EXCEPTION_BREAKPOINT) InterlockedIncrement(&kla_asserts);
        else { InterlockedIncrement(&kla_faults); snprintf(kla_last_fault, sizeof kla_last_fault, "%08lx at kl2.exe+0x%lx", code, (DWORD)(at - img_lo)); }
        if (first || total < 20) { kla_flush(); klog("AT kl2.exe+%06lx:", (DWORD)(at - img_lo)); kla_where(); }
    } else {                                            /* counted, but only an unhandled one decides the result */
        InterlockedIncrement(&kla_foreign);
        if (kla_firstchance && first) kla_log_fault(ep, "FAULT (first chance, may still be handled)");   /* dumped only if it ends in kla_uef */
    }
    TlsSetValue(kla_tls, 0);
    return EXCEPTION_CONTINUE_SEARCH;
}

static LONG WINAPI kla_uef(EXCEPTION_POINTERS *ep);
static LONG kla_uef2(EXCEPTION_POINTERS *ep, char *r, DWORD_PTR *seen_at_p, LONG *seen_n_p)
{
#define seen_at (*seen_at_p)
#define seen_n (*seen_n_p)
    /* The game's own filter does not always end the process: a fault on its sound thread (run RN5, divide
       fault at 0x44668b) came back through here every 0.35 s while the round went on. Only the first one
       of an address is logged and dumped (a 47 MB dump each time slowed the game to a crawl). */
    if ((DWORD_PTR)ep->ExceptionRecord->ExceptionAddress == seen_at) {
        LONG n = InterlockedIncrement(&seen_n);
        if (n == 10 || n == 100 || n == 1000) kla_out(1, "unhandled exception at %08lx came back %ld times (the game's filter resumes it)", (DWORD)seen_at, n);
        return EXCEPTION_CONTINUE_SEARCH;               /* not handed on a second time: the first round's hand-on already wrote the game's dump */
    }
    seen_at = (DWORD_PTR)ep->ExceptionRecord->ExceptionAddress; seen_n = 1;
    TlsSetValue(kla_tls, (void *)1);
    kla_log_fault(ep, "FATAL unhandled exception");
    dumps = dumps < max_dumps ? dumps : max_dumps - 1;
    write_dump(ep, "unhandled");
    TlsSetValue(kla_tls, 0);
    InterlockedIncrement(&kla_faults);
    if (kla_prev_uef && kla_prev_uef != kla_uef) kla_prev_uef(ep);        /* the game's own Steam minidump (0x90b780); may not return */
    snprintf(r, 200, "unhandled exception %s", kla_last_fault);
    kla_finish("FAIL", r, KLA_CRASH);
    return EXCEPTION_EXECUTE_HANDLER;
#undef seen_at
#undef seen_n
}

static LONG WINAPI kla_uef(EXCEPTION_POINTERS *ep)
{   /* nothing handled it: this is the verdict */
    char r[200]; static DWORD_PTR seen_at; static LONG seen_n; static volatile LONG depth; LONG res;
    if (kla_done) return EXCEPTION_CONTINUE_SEARCH;
    /* wrap_oal.dll installs a filter that chains to the one it replaced (ours); our re-arm then takes ITS as
       'previous': each calls the other until the stack is gone (run RN11: 18,003 nested rounds, read by g-crash,
       re\crash_scorepage.md 3). Entered again while a call of ours is under way = that loop: stop it here. */
    if (InterlockedIncrement(&depth) > 1) { InterlockedDecrement(&depth); return EXCEPTION_CONTINUE_SEARCH; }
    res = kla_uef2(ep, r, &seen_at, &seen_n);
    InterlockedDecrement(&depth);
    return res;
}

static void kla_crt_fatal(const char *what)
{
    CONTEXT c; char r[200];
    memset(&c, 0, sizeof c); c.Esp = (DWORD)(DWORD_PTR)&c;   /* only the stack matters: log_context lists the kl2.exe callers on it */
    TlsSetValue(kla_tls, (void *)1);
    kla_flush();
    klog("FATAL C runtime: %s (registers below are not the caller's)", what);
    log_context(&c);
    kla_where();
    kla_dump_now(0, "KLHook_crt.dmp");
    snprintf(r, sizeof r, "C runtime: %s", what);
    kla_finish("FAIL", r, KLA_CRT);
}
static void __cdecl kla_invalid_param(const wchar_t *a, const wchar_t *b, const wchar_t *c, unsigned d, uintptr_t e)
{ (void)a; (void)b; (void)c; (void)d; (void)e; kla_crt_fatal("invalid parameter passed to a C runtime function"); }
static void __cdecl kla_purecall(void) { kla_crt_fatal("pure virtual function call"); }
static void __cdecl kla_sigabrt(int s) { (void)s; kla_crt_fatal("abort()"); }

static int kla_crt_hooks(void)
{   /* the handlers live in the game's MSVCR90, not in this DLL's own static runtime */
    HMODULE m = GetModuleHandleA("MSVCR90.dll"); FARPROC f;
    if (!m) return 0;
    if ((f = GetProcAddress(m, "_set_invalid_parameter_handler")) != 0) ((void *(__cdecl *)(void *))f)((void *)kla_invalid_param);
    if ((f = GetProcAddress(m, "_set_purecall_handler")) != 0) ((void *(__cdecl *)(void *))f)((void *)kla_purecall);
    if ((f = GetProcAddress(m, "signal")) != 0) ((void *(__cdecl *)(int, void *))f)(SIGABRT, (void *)kla_sigabrt);
    if ((f = GetProcAddress(m, "_set_abort_behavior")) != 0) ((unsigned (__cdecl *)(unsigned, unsigned))f)(0, 3);   /* no message box, no Watson */
    kla_out(1, "C runtime handlers set in MSVCR90 at %p", (void *)m);
    return 1;
}

static void kla_stall(const char *why, int code)
{
    HANDLE t = kla_main_tid ? OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT, FALSE, kla_main_tid) : 0;
    CONTEXT c; char mod[80]; DWORD off;
    TlsSetValue(kla_tls, (void *)1);
    kla_flush();
    klog("WATCHDOG: %s", why);
    if (t) {
        memset(&c, 0, sizeof c); c.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
        if (SuspendThread(t) != (DWORD)-1) {
            int got = GetThreadContext(t, &c);
            ResumeThread(t);                            /* resumed before any logging: it may hold the heap lock */
            if (got) { kla_module(c.Eip, mod, sizeof mod, &off); klog("  main thread %lu at %s+0x%lx (%08lx)", kla_main_tid, mod, off, c.Eip); log_context(&c); }
        }
        CloseHandle(t);
    } else klog("  main thread not known (no keyboard poll and no scene load yet)");
    kla_where();
    kla_dump_now(0, "KLHook_stall.dmp");
    kla_finish("FAIL", why, code);
}

static DWORD WINAPI kla_watch(LPVOID unused)
{
    int crt = 0, rearmed = 0; char why[200];
    (void)unused;
    for (;;) {
        DWORD now, idle;
        LPTOP_LEVEL_EXCEPTION_FILTER prev;
        WaitForSingleObject(kla_wake, 250);
        if (kla_done) return 0;
        if (kla_watch_arm) { kla_watch_arm = 0; kla_watch_apply(); }
        if (kla_so_ep) { TlsSetValue(kla_tls, (void *)1); kla_log_fault(kla_so_ep, "FATAL stack overflow"); kla_dump_now(0, "KLHook_stackoverflow.dmp"); kla_finish("FAIL", "stack overflow", KLA_CRASH); }
        kla_flush();
        prev = SetUnhandledExceptionFilter(kla_uef);    /* the game sets its own at 0x58ffca after we load */
        if (prev != kla_uef) {
            /* Only a filter INSIDE kl2.exe (the game's own, 0x90b780: Steam minidump, returns 0) is kept as the one
               to hand on to. Another DLL's is never called: wrap_oal.dll's calls UnhandledExceptionFilter again
               from inside itself, which came straight back here (run RN11: 18,003 nested rounds, 'stack
               overflow'; re\crash_scorepage.md 3). The depth counter in kla_uef stays as a second guard. */
            int game = (DWORD_PTR)prev >= img_lo && (DWORD_PTR)prev < img_hi;
            if (game) kla_prev_uef = prev;
            if (rearmed++ < 5) kla_out(1, "unhandled-exception filter re-installed over %p (%s)", (void *)(DWORD_PTR)prev, game ? "the game's own: handed on to after ours" : "another module's: not chained to");
        }
        if (!crt && (kla_frames || kb.loads || kb.loading)) crt = kla_crt_hooks();
        now = GetTickCount(); idle = now - kla_beat;
        if (kla_stall_ms && (int)idle > 0 && idle > kla_stall_ms) {
            snprintf(why, sizeof why, "stall: no hook hit and no input frame for %lu ms (%s)", idle, kb.loading ? "inside a scene load" : kla_frames ? "input polling stopped: hang, dialog or inactive window" : "before the first keyboard poll");
            kla_stall(why, KLA_STALL);
        }
        if (kla_maxrun_ms && now - kla_t0 > kla_maxrun_ms) { snprintf(why, sizeof why, "maxrun: %lu ms reached", kla_maxrun_ms); kla_stall(why, KLA_MAXRUN); }
        if (kla_loaded_ms && kb.level_tick && !kb.loading && now - kb.level_tick > kla_loaded_ms && kla_frames - kb.level_frames > 30)
            kla_pass("level loaded and running");
    }
}

/* ---------------------------------------------------------------- entry points */

static void kla_di8(LPVOID *o)
{   /* after a successful real DirectInput8Create */
    char s[128]; DWORD sys; float ax = 0;
    if (!kla_on || !o || !*o) return;
    kla_scene(s, sizeof s); sys = kla_sysif(); if (sys) kla_rd(sys + 0x68, &ax, 4);
    kla_out(1, "input: DirectInput8Create wrapped; scene='%s' AutoExit=%g", s, ax);
    *o = kla_wrap(*o, ki_vtbl, 0);
}

static void kla_init(HINSTANCE inst)
{   /* from DllMain, after klhook.c's own setup; no game code has run yet */
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)((BYTE *)(DWORD_PTR)img_lo + ((IMAGE_DOS_HEADER *)(DWORD_PTR)img_lo)->e_lfanew);
    (void)inst;
    InitializeCriticalSection(&kla_cs);
    snprintf(kla_ini, sizeof kla_ini, "%s\\KLHook.ini", klh_out);
    kla_on = GetPrivateProfileIntA("Auto", "Enable", 0, kla_ini);
    if (!kla_on) return;
    kla_hooks_on = GetPrivateProfileIntA("Auto", "Hooks", 1, kla_ini);
    kla_nodes = GetPrivateProfileIntA("Auto", "Nodes", 1, kla_ini);
    kla_stall_ms = GetPrivateProfileIntA("Auto", "StallMs", 60000, kla_ini);
    kla_maxrun_ms = GetPrivateProfileIntA("Auto", "MaxRunMs", 0, kla_ini);
    kla_loaded_ms = GetPrivateProfileIntA("Auto", "LoadedMs", 0, kla_ini);
    kla_unfocused = GetPrivateProfileIntA("Auto", "Unfocused", 1, kla_ini);
    kla_block = GetPrivateProfileIntA("Auto", "BlockReal", 1, kla_ini);
    kla_firstchance = GetPrivateProfileIntA("Auto", "FirstChance", 1, kla_ini);
    { char t[32]; GetPrivateProfileStringA("Auto", "PosOff", "0x460", t, sizeof t, kla_ini); kla_pos_off = strtoul(t, 0, 16);
      GetPrivateProfileStringA("Auto", "DirOff", "0xc14", t, sizeof t, kla_ini); kla_dir_off = strtoul(t, 0, 16);
      GetPrivateProfileStringA("Auto", "TurnDeg", "0.17", t, sizeof t, kla_ini); kla_turn_deg = (float)atof(t); if (kla_turn_deg == 0) kla_turn_deg = 0.17f;
      kla_poslog_ms = GetPrivateProfileIntA("Auto", "PosLogMs", 0, kla_ini); }
    kla_t0 = kla_beat = GetTickCount();
    kla_exe_ok = img_lo == 0x400000 && nt->FileHeader.TimeDateStamp == KL2_TIMESTAMP && nt->OptionalHeader.SizeOfImage == KL2_IMAGESIZE;
    kla_out(1, "klauto: enabled; exe %s; command line: %s", kla_exe_ok ? "is kl2.exe build 0490" : "is NOT the known kl2.exe - no code is patched", GetCommandLineA());
    if (kla_exe_ok) {
        kla_cmd_drop(); kla_engine_ini();
        if (kla_hooks_on) { kla_install(); kla_end_hooks(); }
        else {                                          /* one kind of patch at a time (re\antitamper.md section 8) */
            static const char *nm[H_COUNT] = { "NODE", "CTRL", "PROG", "GEOMS", "SCNBLK", "REFFIX", "ROOM", "GBUF", "REFEND", "POST", "GINIT", "CLIST", "CINIT",
                                               "OPENWIN", "ELFOCUS", "FOCUS", "INPUT" };
            char d[200], *t; int i;
            kla_only = GetPrivateProfileIntA("Auto", "VtLoad", 0, kla_ini) ? 0x80000000u : 0;
            GetPrivateProfileStringA("Auto", "Detours", "", d, sizeof d, kla_ini);
            for (t = strtok(d, ", "); t; t = strtok(0, ", ")) {
                for (i = 0; i < H_COUNT && _stricmp(t, nm[i]); i++) ;
                if (i < H_COUNT) kla_only |= 1u << i; else kla_out(1, "Detours: unknown name '%s'", t);
            }
            if (kla_only) kla_install();
            if (GetPrivateProfileIntA("Auto", "EndHooks", 0, kla_ini)) kla_end_hooks();
        }
    }
    kla_script_load();
    kla_tls = TlsAlloc();
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX);
    AddVectoredExceptionHandler(1, kla_veh);
    SetUnhandledExceptionFilter(kla_uef);               /* whatever was there before the game set its own is not chained to (kla_watch) */
    kla_wake = CreateEventA(0, FALSE, FALSE, 0);
    CloseHandle(CreateThread(0, 0, kla_watch, 0, 0, 0));
    atexit(kla_atexit);
    kla_result("RUNNING", "started", -1);
}

#ifdef KLAUTO_TEST
/* Test harness entry points (never built into the game's DLL): the harness maps a copy of kl2.exe at
   any address, so the patcher runs against the real bytes, and drives the handlers with made-up state. */
__declspec(dllexport) int kla_test_install(void *mapped, void *fake_loader)
{
    int n;
    kla_delta = (LONG_PTR)((DWORD_PTR)mapped - 0x400000); kla_exe_ok = 1;
    klh_policy = KLH_DIRECT;                            /* this entry tests the patcher itself: every site goes in */
    kla_engine_ini(); n = kla_install();
    if (fake_loader) kla_real_load = (KLA_LOAD)fake_loader;
    return n;
}
__declspec(dllexport) void *kla_test_stubs(void) { return kla_stubs; }
__declspec(dllexport) int kla_test_cmd_drop(char *cmd, char *keys) { return kla_cmd_drop_in(cmd, keys); }
__declspec(dllexport) int kla_test_cmd_append(const char *add) { return kla_cmd_append(GetCommandLineA(), add); }
__declspec(dllexport) const char *kla_test_engine_text(void) { return kla_engine_text; }
__declspec(dllexport) void kla_test_dispatch(int id, KREGS *r) { kla_dispatch(id, r); }
__declspec(dllexport) void *kla_test_load(void *self, void *arg) { return kla_scene_load(self, 0, arg); }
__declspec(dllexport) int kla_test_stub_runs(void)
{   /* a detour on a made-up function: mov eax,[esp+4]; add eax,[esp+8]; ret - must still return the sum */
    static const BYTE fn[] = { 0x8b, 0x44, 0x24, 0x04, 0x03, 0x44, 0x24, 0x08, 0xc3 };
    BYTE *m = (BYTE *)VirtualAlloc(0, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE), jmp[8]; DWORD v; int r;
    DWORD before = kb.ocount;
    memcpy(m, fn, sizeof fn);
    kla_emit(m + 0x100, H_CINIT, fn, 8, m + 8);
    memset(jmp, 0x90, 8); jmp[0] = 0xe9; v = (DWORD)(m + 0x100 - (m + 5)); memcpy(jmp + 1, &v, 4);
    if (!kla_poke(m, fn, jmp, 8)) return -1;
    r = ((int (__cdecl *)(int, int))m)(1000, 234);
    return r == 1234 && kb.ocount == before + 1 && kb.obj == 1000 && kb.otarget == 234;
}
#endif
#endif /* KLAUTO_C */
#endif /* KLHOOK_C */
