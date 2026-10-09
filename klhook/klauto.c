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
 * BUILD (no edit of klhook.c needed): compile THIS file instead of klhook.c; it includes klhook.c with
 * its DllMain / DirectInput8Create renamed and supplies the real ones. In klhook\build.bat replace
 * "%~dp0klhook.c" by "%~dp0klauto.c"; the /EXPORT stays the same. Built with cl 19.40 x86, /O2 /LD:
 * no warning at /W3; at /W4 only klhook.c's own C4100. To merge instead: define KLAUTO_FROM_KLHOOK,
 * #include "klauto.c" in klhook.c above its DirectInput8Create, call kla_init(inst) at the end of
 * DllMain and kla_di8(o) after a successful real_create() (that route was compiled too). It uses
 * klhook.c's dir, klog, write_dump, log_context, img_lo, img_hi, dumps, max_dumps, MDWD, MEI.
 *
 * KLHook.ini
 *   [Auto]
 *   Enable=1          master switch (0 = this file does nothing at all)
 *   Hooks=1           patch the breadcrumb sites into kl2.exe's code (in memory, bytes verified first)
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
 *   [Engine]          lines appended to the exe's baked ini text (same effect as "-o <line>")
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
 *   10=sel HeistLevel 0xceceec 0         step a toggle element until the dword at the address has the
 *                                        value: sends 'Decrease' / 'Increase' (ZToggle slot 20,
 *                                        0x90b170 -> vtbl+0xa8 / +0xa4) every 250 ms, at most 24
 *                                        times, and waits up to 10 s for the element to exist.
 *                                        [0xceceec] is the Arcade selector's position, copied there
 *                                        every frame by its slot 8 (0x459eec); 0 = Subway (F01).
 *                                        Needed because the page opens on the profile's last map
 *                                        (0x459eb7: 0x85f510 on the profile 0x1686e60).
 *   11=expect 0xceceec 0                 fail the script (exit 27) unless the dword has that value
 *   Keys: A-Z 0-9 F1-F12 RETURN ESCAPE SPACE TAB BACK UP DOWN LEFT RIGHT LSHIFT LCONTROL LMENU INSERT
 *   DELETE HOME END PRIOR NEXT NUMPADENTER, or a DIK code as 0x1C. RSHIFT cannot be scripted: the game
 *   ignores DIK 0x36 from DirectInput and asks GetAsyncKeyState(0xA1) (kl2 0x6c8c2f, 0x6c8c91).
 *   The menu key sequence for Arcade Mode -> Subway -> Accept is NOT ESTABLISHED here: record it once
 *   by hand (the menu block binds ZW_SELECT to RETURN, ZW_CANCEL to ESC, arrows to move: string at
 *   kl2 0xb15148) and put it in [Script].
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
 *  NEEDS A LIVE RUN (nothing below was observed in the game)
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
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <signal.h>

#ifndef KLAUTO_FROM_KLHOOK
#define DirectInput8Create klhook_DirectInput8Create
#define DllMain klhook_DllMain
#include "klhook.c"
#undef DirectInput8Create
#undef DllMain
#endif

#define KL2_TIMESTAMP 0x4c80f728u
#define KL2_IMAGESIZE 0x134e000u
enum { KLA_PASS = 0, KLA_PROBLEMS = 21, KLA_CRASH = 22, KLA_CRT = 23, KLA_STALL = 24, KLA_MAXRUN = 25,
       KLA_SCRIPT = 26, KLA_SCRIPTFAIL = 27 };

static LONG_PTR kla_delta;                       /* 0 in the game; the test harness maps a copy elsewhere */
#define VA(x) ((BYTE *)((DWORD_PTR)(x) + kla_delta))
#define G32(x) (*(volatile DWORD *)VA(x))

static int kla_on, kla_hooks_on, kla_nodes, kla_unfocused, kla_block, kla_firstchance, kla_exe_ok;
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
            char path[MAX_PATH]; snprintf(path, sizeof path, "%s\\KLHook.log", dir);
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
    snprintf(path, sizeof path, "%s\\KLHook.result", dir); snprintf(tmp, sizeof tmp, "%s\\KLHook.result.tmp", dir);
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

static void kla_atexit(void)
{   /* ExitProcess / exit() of the game itself, e.g. AutoExit or the menu's Quit */
    if (!kla_on || InterlockedExchange(&kla_done, 1)) return;
    kla_out(1, "process exit, asserts %ld, faults %ld, loads %lu", kla_asserts, kla_faults, kb.loads);
    if (kla_asserts || kla_faults) kla_result("FAIL", "the game ended by itself, asserts or faults were logged", KLA_PROBLEMS);
    else kla_result("EXIT", "the game ended by itself", 0);
}

/* ---------------------------------------------------------------- code detours */

typedef struct { DWORD edi, esi, ebp, esp, ebx, edx, ecx, eax, efl; } KREGS;   /* pushad order, then pushfd */
enum { H_NODE, H_CTRL, H_PROG, H_GEOMS, H_SCNBLK, H_REFFIX, H_ROOM, H_GBUF, H_REFEND, H_POST, H_GINIT, H_CLIST, H_CINIT, H_COUNT };
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
};

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

static int kla_poke(BYTE *at, const BYTE *expect, const BYTE *bytes, int len)
{   /* replace len bytes, only if they are exactly the expected ones */
    BYTE cur[16]; DWORD old;
    if (!kla_rd((DWORD_PTR)at, cur, len) || memcmp(cur, expect, len)) return 0;
    if (!VirtualProtect(at, len, PAGE_EXECUTE_READWRITE, &old)) return 0;
    memcpy(at, bytes, len);
    VirtualProtect(at, len, old, &old); FlushInstructionCache(GetCurrentProcess(), at, len);
    return 1;
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
    kla_result("RUNNING", "loading", -1);
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
    kla_out(1, "engine ini: %d line(s) %s", i - 1, kla_poke(VA(0x5987af), exp, rep, 5) ? "installed (operand of the push at 0x5987af)" : "NOT installed: bytes at 0x5987af differ");
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
    kla_out(1, "CmdDrop: %d '-o' pair(s) blanked; command line now: %s", n, cmd);
}

static int kla_install(void)
{
    int i, ok = 0; BYTE *p, jmp[10]; DWORD v, old = 0x820300, mine;
    kla_stubs = (BYTE *)VirtualAlloc(0, 0x1000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!kla_stubs) return 0;
    for (i = 0, p = kla_stubs; i < H_COUNT; i++, p += 64) {
        BYTE *at = VA(kla_sites[i].va); int len = kla_sites[i].len;
        kla_emit(p, i, kla_sites[i].bytes, len, at + len);
        memset(jmp, 0x90, sizeof jmp); jmp[0] = 0xe9; v = (DWORD)(p - (at + 5)); memcpy(jmp + 1, &v, 4);
        if (kla_poke(at, kla_sites[i].bytes, jmp, len)) ok++;
        else kla_out(0, "hook %08lx (%s) NOT installed: bytes differ", kla_sites[i].va, kla_sites[i].what);
    }
    kla_real_load = (KLA_LOAD)(DWORD_PTR)(old + kla_delta); mine = (DWORD)(DWORD_PTR)kla_scene_load;
    i = kla_poke(VA(0xb8fa24), (BYTE *)&old, (BYTE *)&mine, 4);
    kla_out(1, "hooks: %d of %d detours installed, scene-load wrapper %s", ok, H_COUNT, i ? "installed (vtable entry 0xb8fa24)" : "NOT installed");
    return ok + i;
}

/* ---------------------------------------------------------------- script */

typedef struct { char op; BYTE key; DWORD n, n2; char text[80]; } KCMD;
enum { C_WAIT = 1, C_FRAMES, C_TAP, C_DOWN, C_UP, C_WAITSCENE, C_WAITLOAD, C_LOG, C_PASS, C_FAIL, C_QUIT, C_MSG, C_PEEK, C_SEL, C_EXPECT };
static KCMD kla_cmd[256]; static int kla_ncmd, kla_pc; static DWORD kla_cmd_t, kla_cmd_f, kla_seq;
static BYTE kla_held[256]; static DWORD kla_rel_t[256], kla_rel_f[256]; static int kla_taps, kla_started;

static int kla_script_pc(void) { return kla_ncmd ? kla_pc + 1 : 0; }
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
    for (i = 1; i <= 256; i++) {
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
        else if (!_stricmp(op, "peek")) {
            char *plus = strchr(a, '+');
            c->op = C_PEEK; c->n = strtoul(a, 0, 16); c->key = (BYTE)(plus != 0); c->n2 = plus ? strtoul(plus + 1, 0, 16) : 0;
            snprintf(c->text, sizeof c->text, "%s", rest + strlen(a));
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

static void kla_script_step(DWORD *rg, DWORD *count, DWORD cap)
{   /* called once per keyboard poll, on the game's thread */
    DWORD now = GetTickCount(); int k, guard = 0;
    if (!kla_started) { kla_started = 1; kla_cmd_t = now; kla_cmd_f = kla_frames; kla_out(1, "script: first keyboard poll, starting"); }
    for (k = 0; kla_taps && k < 256; k++)
        if (kla_rel_f[k] && (int)(now - kla_rel_t[k]) >= 0 && (int)(kla_frames - kla_rel_f[k]) >= 0) { kla_event(rg, count, cap, k, 0); kla_rel_f[k] = 0; kla_taps--; return; }
    if (kla_taps) return;                               /* the next command waits until every tap is released */
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
        case C_PEEK: { DWORD v = 0, at = (DWORD)(DWORD_PTR)VA(c->n); int ok = kla_rd(at, &v, 4);
            if (ok && c->key) { at = v + c->n2; v = 0; ok = kla_rd(at, &v, 4); }
            kla_out(1, "script %d: peek %08lx%s = %s%08lx %s", kla_pc + 1, c->n, c->key ? "+" : "", ok ? "" : "unreadable ", v, c->text); next = 1; break; }
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
    if (FAILED(hr) && p->kind == 2 && kla_unfocused && kla_script_active()) return 0;   /* the game then polls us (0x8fa0a0) */
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
    if (p->kind == 3) { if (SUCCEEDED(hr) && kla_block) memset(data, 0, cb); return hr; }
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
    kla_frames++; kla_beat = GetTickCount(); kla_main_tid = GetCurrentThreadId();
    if (!told) { char s[128]; DWORD sys = kla_sysif(); float ax = 0; told = 1; kla_scene(s, sizeof s); if (sys) kla_rd(sys + 0x68, &ax, 4);
                 kla_out(1, "input: first keyboard poll (result %08lx); scene='%s' AutoExit=%g", (DWORD)hr, s, ax); }
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
    snprintf(path, sizeof path, "%s\\%s", dir, name);
    f = CreateFileA(path, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, 0, 0);
    if (f == INVALID_HANDLE_VALUE) return;
    mei.tid = GetCurrentThreadId(); mei.ep = ep; mei.client = FALSE;
    w(GetCurrentProcess(), GetCurrentProcessId(), f, 0x1 | 0x40 | 0x1000, ep ? &mei : 0, 0, 0);
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

static LONG WINAPI kla_uef(EXCEPTION_POINTERS *ep)
{   /* nothing handled it: this is the verdict */
    char r[200];
    if (kla_done) return EXCEPTION_CONTINUE_SEARCH;
    TlsSetValue(kla_tls, (void *)1);
    kla_log_fault(ep, "FATAL unhandled exception");
    dumps = dumps < max_dumps ? dumps : max_dumps - 1;
    write_dump(ep, "unhandled");
    if (kla_prev_uef && kla_prev_uef != kla_uef) kla_prev_uef(ep);        /* the game's own Steam minidump (0x90b780) */
    snprintf(r, sizeof r, "unhandled exception %s", kla_last_fault);
    kla_finish("FAIL", r, KLA_CRASH);
    return EXCEPTION_EXECUTE_HANDLER;
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
        if (kla_so_ep) { TlsSetValue(kla_tls, (void *)1); kla_log_fault(kla_so_ep, "FATAL stack overflow"); kla_dump_now(0, "KLHook_stackoverflow.dmp"); kla_finish("FAIL", "stack overflow", KLA_CRASH); }
        kla_flush();
        prev = SetUnhandledExceptionFilter(kla_uef);    /* the game sets its own at 0x58ffca after we load */
        if (prev != kla_uef) { kla_prev_uef = prev; if (rearmed++ < 5) kla_out(1, "unhandled-exception filter re-installed over %p", (void *)(DWORD_PTR)prev); }
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
    snprintf(kla_ini, sizeof kla_ini, "%s\\KLHook.ini", dir);
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
    kla_t0 = kla_beat = GetTickCount();
    kla_exe_ok = img_lo == 0x400000 && nt->FileHeader.TimeDateStamp == KL2_TIMESTAMP && nt->OptionalHeader.SizeOfImage == KL2_IMAGESIZE;
    kla_out(1, "klauto: enabled; exe %s; command line: %s", kla_exe_ok ? "is kl2.exe build 0490" : "is NOT the known kl2.exe - no code is patched", GetCommandLineA());
    if (kla_exe_ok) { kla_cmd_drop(); kla_engine_ini(); if (kla_hooks_on) kla_install(); }
    kla_script_load();
    kla_tls = TlsAlloc();
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX);
    AddVectoredExceptionHandler(1, kla_veh);
    kla_prev_uef = SetUnhandledExceptionFilter(kla_uef);
    kla_wake = CreateEventA(0, FALSE, FALSE, 0);
    CloseHandle(CreateThread(0, 0, kla_watch, 0, 0, 0));
    atexit(kla_atexit);
    kla_result("RUNNING", "started", -1);
}

#ifndef KLAUTO_FROM_KLHOOK
HRESULT WINAPI DirectInput8Create(HINSTANCE h, DWORD v, REFIID r, LPVOID *o, LPUNKNOWN u)
{
    HRESULT hr = klhook_DirectInput8Create(h, v, r, o, u);
    if (SUCCEEDED(hr)) kla_di8(o);
    return hr;
}

BOOL WINAPI DllMain(HINSTANCE inst, DWORD reason, LPVOID res)
{
    BOOL ok = klhook_DllMain(inst, reason, res);
    if (reason == DLL_PROCESS_ATTACH) kla_init(inst);
    return ok;
}
#endif

#ifdef KLAUTO_TEST
/* Test harness entry points (never built into the game's DLL): the harness maps a copy of kl2.exe at
   any address, so the patcher runs against the real bytes, and drives the handlers with made-up state. */
__declspec(dllexport) int kla_test_install(void *mapped, void *fake_loader)
{
    int n;
    kla_delta = (LONG_PTR)((DWORD_PTR)mapped - 0x400000); kla_exe_ok = 1;
    kla_engine_ini(); n = kla_install();
    if (fake_loader) kla_real_load = (KLA_LOAD)fake_loader;
    return n;
}
__declspec(dllexport) void *kla_test_stubs(void) { return kla_stubs; }
__declspec(dllexport) int kla_test_cmd_drop(char *cmd, char *keys) { return kla_cmd_drop_in(cmd, keys); }
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
