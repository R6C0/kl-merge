/*
 * KLHook - the dinput8.dll proxy of the Dead Men expansion for Kane & Lynch 2: Dog Days (kl2.exe, 32-bit).
 *
 * Drop dinput8.dll + KLHook.ini next to kl2.exe. The game loads it instead of the system dinput8.dll; every
 * call is forwarded to the real one. Delete dinput8.dll (and the folder KLExpansion) to remove it.
 *
 * ONE SOURCE, TWO CONFIGURATIONS (both are this file; the others are #included by it)
 *   SHIP   build.bat        cl klhook.c                  what a player of the expansion runs
 *   TEST   build_auto.bat   cl /DKLHOOK_TEST klhook.c    SHIP + the test rig klauto.c
 *
 *   file          SHIP  TEST  what
 *   klhook.c       x     x    log, the patch guard, crash logging and dumps, clean end after a fatal fault,
 *                             exit tripwire, the per-frame tick, the DirectInput proxy, DllMain
 *   klranges.h     x     x    GENERATED (mkranges.py): the 225 address ranges kl2.exe's integrity checks hash
 *   klfix.c        x     x    repairs of faults in kl2.exe itself, by data writes (the leaderboard row count)
 *   klslot.c       x     x    the expansion: maps in their own folder ([Redirect], menu pages), overlay files,
 *                             slot names by data write ([Slots])
 *   klsteam.c      x     x    Steam write guard: a proxy ISteamUserStats behind one import slot; no leaderboard
 *                             upload, stat or achievement from a level that is not the stock level of its slot,
 *                             and none at all from a TEST build; the 'session: state' line
 *   klmm.c         x     x    [Net] PrivateLobby / BuildKey: a proxy ISteamMatchmaking behind one import slot, installed ONLY when a key
 *                             is set (friends-only / invite-only Fragile Alliance lobbies, a map-set key on lobby and search); v82g
 *   klstock.h      x     x    GENERATED (mkstock.py): size and directory hash of the 22 stock level archives
 *   kljoin.c       x     x    jump boxes: a two-part level joined by the game's own jump request ([Join], KLJoin.ini)
 *   klcrew_rt.c    x     x    the AI crew follows that jump ([CrewJoin]; calls 0x62a900, 0x72e0f0; no data, no code). OFF by default
 *   klchar.c       x     x    the heister the player chose: body, mask, outfit ([Character], KLWardrobe.ini)
 *   klcharonline.c x     x    [CharOnline] every online player's look on every peer (Steam member data + UDP 27414; off unless Enable=1)
 *   klgun.c        x     x    switchable gun looks ([Guns], KLGuns.ini)
 *   klcrew.c       x     x    random AI heisters ([Crew]; calls 0x783fb0, 0x88c810, with Names 0x83e2e0, 0x469250; eight heap
 *                             bytes) and 'who wears whom' for kltalk.c (read only). OFF by default
 *   kltalk.c       x     x    Kane / Lynch scenes and chatter ([Talk], KLTalk.ini; calls 0x828fa0, 0x421c70; no data, no
 *                             code). OFF by default
 *   klvoice.c      x     x    Dead Men voices for the eight Dead Men bodies' Dog Days event lines ([Voice]; calls 0x828fa0; DATA
 *                             writes only: one heap dword per swapped entry). OFF by default
 *   klbot.c        x     x    the AI crew's log and the backstab / bribe / leave / van rules ([Bots]). OFF by default
 *   klescort.c     x     x    one or two AI heisters stay near the human ([Bots] Escort; calls 0x760e50, the soldier's own
 *                             'defend this place' order; no data, no code) and [Bots] BoardAll (ONE data byte: a bot
 *                             held by loot gets heist stage 3 while the vehicle waits). OFF by default
 *   klhop.c        x     x    an AI heister that stands at a place the mesh does not carry it over is put beyond it
 *                             ([CrewHop], KLJoin.ini; calls 0x62a900 through klcrew_rt.c's functions, with Reorder
 *                             0x760e50; no data, no code). OFF by default
 *   klclimb.c      x     x    the PLAYER climbs a wall edge of the level's KLJoin.ini with Dead Men's climb clip
 *                             ([EdgeClimb], was [Climb]; game routines called: the mini animation, AlignTo, the collision
 *                             switch, the proxy; no code). OFF by default. Wired 2026-10-11 after two reviews; NOT RUN IN THE GAME
 *   klfreeclimb.c  x     x    Dead Men's FREE climb, W + E at any ledge 25 .. 220 high (luvsic's ANP climb.inc, ported): a
 *                             ZFFActionVaultOver with a vtable copy of this DLL's own; data writes only, every call under
 *                             a fault guard ([Climb]). OFF by default; needs the climb clips in the level's .ANM. NOT RUN
 *   klhud.c        x     x    the expansion's FA / Arcade HUD, Version 1 ([HUD]): crew list + money box drawn with the game's
 *                             own ZCHAROBJ texts from a private copy of the OSD's vtable (slot 55 wrapped, as klchar.c
 *                             wraps the option object); calls 0x8ccde0, 0x598460, 0x817810 and ZCHAROBJ slots on the
 *                             main thread; one data byte hides the stock top-left block. OFF by default, NOT RUN
 *   klmem.c klnudge.c x  x    address space reserve ([Memory]); the loader's cursor nudge ([Load])
 *   klhigh.c       x     x    [Memory] High: the 4 GB flag made safe - the upper 2 GB reserved at DllMain, the listed foreign modules'
 *                             own import slots of VirtualAlloc/Free carve theirs out of it; kl2.exe untouched. OFF by default; NOT RUN LIVE
 *   klauto.c             x    scripted input, breadcrumb detours, [Auto] options, result file, watchdog
 *   mkoverlay.py              builds KLExpansion\Overlay\Patch01.zip (the menu page of the expansion maps)
 *   build.bat build_auto.bat  SHIP / TEST; with --work into <work>\build\klhook\ship | test (DLL, sha1, ini): the
 *                             fixed place tools and live runs take a build from (workdir.py asks for <work>)
 *   A SHIP build does not contain klauto.c at all: no [Auto] key can switch a detour on in it.
 *
 * WHAT A HOOK MAY PATCH (re\antitamper.md): kl2.exe carries Valve CEG's code-integrity checks. Several hundred
 * inlined checks hash 84.9 % of .text and 65.9 % of .rdata; a changed byte ends a REAL session (Arcade / Fragile
 * Alliance started from the menu) with ExitProcess(0x8000dead) about 30 ms after the level loaded. Not hashed: the
 * import address table, .data / .bss, the heap, anything outside the image. Shown live: import wrappers, data
 * writes and five detours in unhashed pages each survived a session (runs X1 - X3, re\fa_round.md 7.1).
 * So every write this DLL makes goes through ONE guard, klh_may_write(), under one of three policies:
 *   ship     (SHIP build, fixed)                  import slots and data only. No byte of .text or .rdata, hashed
 *                                                 or not ("unhashed" is 15 % of the code, chosen by CEG's layout,
 *                                                 and only as good as the range map)
 *   session  (TEST, [KLHook] SessionSafe=1, the default)   + image bytes outside every hashed range
 *   direct   (TEST, [KLHook] SessionSafe=0)       anything. For direct-boot load tests ("-o DefaultScene="),
 *                                                 which never reach a check that covers these sites. A run that
 *                                                 starts a session with a hashed patch in place ends in the
 *                                                 integrity exit; the tripwire below says so in the log.
 * A refused patch is logged ("patch REFUSED ...") and simply not there; nothing else changes.
 * On an exe that is not build 0490 (time stamp / image size differ) the range table means nothing: then only
 * import slots and writable sections may be written, under every policy but 'direct'.
 *
 * PATCH SITES. "checker" = output of `ceg_ranges.py <address>:<length>` (<work>\research\agent_scripts\f-tamper),
 * run 2026-10-09 against the range map compiled in as klranges.h. S = SHIP, T = TEST. "session" = allowed in a
 * real session: yes / no / luck (an unhashed page: outside every range read, not for anything shipped).
 *
 *   site                      what                                        in  kind        checker       session
 *   ------------------------  ------------------------------------------  --  ----------  ------------  -------
 *   0xb10270                  CreateFileA           (klslot wrapper)      ST  import      0 checks      yes  X1 live
 *   0xb10204                  CreateFileW           (klslot wrapper)      ST  import      0 checks      yes  X1 live
 *   0xb10260                  GetFileAttributesA    (klslot wrapper)      ST  import      0 checks      yes  X1 live
 *   0xb1006c                  FindFirstFileA        (klslot wrapper)      ST  import      0 checks      yes  X1 live
 *   0xb10430                  MSVCR90 fopen         (klslot wrapper)      ST  import      0 checks      yes  X1 live
 *   0xb1018c                  ExitProcess           (exit tripwire)       ST  import      0 checks      yes  X1 live
 *   0xb103d0 0xb104b0         MSVCR90 exit, _exit   (the exit line)       ST  import      0 checks      yes  X1 live (as klauto's)
 *   0xb107bc                  steam_api SteamAPI_RunCallbacks (the tick)  ST  import      0 checks      yes  S1 live (+ S2 HK3 J2 J3)
 *   0xb107c8                  steam_api SteamUserStats (klsteam proxy)    ST  import      0 checks      yes  S1 live (+ S2 HK3 J2 J3)
 *   0xb107d8                  steam_api SteamMatchmaking (klmm proxy)     ST  import      0 checks      only with [Net] PrivateLobby / BuildKey; NOT RUN
 *   [0xdd265c]+0x8d4          jump-list entry to go to   (kljoin)         ST  heap        outside       yes  J2 live (J1b direct boot)
 *   0x156b358                 debug jump request = 1     (kljoin)         ST  .data       0 checks      yes  J2 live (J1b direct boot)
 *   [[[0x168e598]+0x17c]+0x198]+0x31fc   leaderboard row count (klfix)    ST  heap        outside       yes  live (klauto, 6 score pages)
 *   [0x168f750]+0x16+i*0x40   FA slot name          ([Slots])             ST  heap        outside       yes  X2 live (same bytes written back)
 *   [0x168f750]+4+i           FA slot available     (renamed slots only)  ST  heap        outside       yes  NOT RUN
 *   [0x168e598]+8             session default map name ([Slots] F01)      ST  heap        outside       yes  NOT RUN
 *   0xb103d0 0xb104b0         the same two slots again (klauto END lines)  T  import      0 checks      yes  X1 live
 *   0xb105a8 0xb10640         PostQuitMessage, DestroyWindow (klauto)      T  import      0 checks      yes  X1 live
 *   0x46fe96 +6               NODE    detour, node loader                  T  .text       0 checks      luck X3 live
 *   0x46ffbf +5               CTRL    detour, controller                   T  .text       0 checks      luck X3 live
 *   0x862780 +8               SCNBLK  detour, scene property block         T  .text       0 checks      luck X3 live
 *   0x6204b0 +6               REFFIX  detour, REF fix-up                   T  .text       0 checks      luck X3 live
 *   0x7f3b80 +10              GINIT   detour, geom staged init             T  .text       0 checks      luck X3 live
 *   0x53ac90 +6               PROG    detour, load progress                T  .text       12 checks     no
 *   0x8ad7c0 +8               GEOMS   detour, entity loader                T  .text       8 checks      no
 *   0x48e910 +5               ROOM    detour, room fix-up                  T  .text       10 checks     no
 *   0x9262b0 +5               GBUF    detour, geom buffer pass             T  .text       8 checks      no
 *   0x8d1210 +6               REFEND  detour, REF consumer                 T  .text       8 checks      no
 *   0x5acc50 +5               POST    detour, post-load init               T  .text       10 checks     no
 *   0x80d800 +6               CLIST   detour, object init list             T  .text       8 checks      no
 *   0x4eec50 +6               CINIT   detour, object init stepper          T  .text       11 checks     no
 *   0x6bee50 +7               OPENWIN detour, open window by name          T  .text       21 checks     no
 *   0x581c70 +5               ELFOCUS detour, element asks for focus       T  .text       10 checks     no
 *   0x7f09f0 +5               FOCUS   detour, ZWINDOWS set focus           T  .text       8 checks      no
 *   0x4c0680 +6               INPUT   detour, element input                T  .text       20 checks     no
 *   0xb8fa24 +4               scene-load vtable entry (LOAD start / end)   T  .rdata      8 checks      no
 *   0x5987af +5               [Engine] push operand                        T  .text       8 checks      no  (the text 0xb55dc0: 8 checks)
 *   the command line          [Auto] CmdDrop / CmdAdd                      T  heap        outside       yes RN5 live
 *   debug register DR0        script 'watch'                               T  thread ctx  -             no: Steam's probe 0xa8e3cb
 *                                                                                                       sabotages a thread with DR7 set
 *   GONE since 2026-10-09 (klslot's code patches, replaced by the data writes above and by the file redirect):
 *   0x836016.. nine `push <slot name>` (8 checks each), 0x69981e session default (11 checks), 0x8468ea..f5 DLC
 *   lock bytes (0 checks, luck), 0x7f5610 MountFirst detour (0 checks, luck).
 *   READ ONLY, no write: the menu's window stack [[[0xdd265c]+0x824]+4] (+0x328 count, +0x32c.. windows; a window's
 *   name at +0xc) = the page of the expansion menu (klslot.c kls_menu_watch; it also compares 11 + 4 code bytes at
 *   0x410930 / 0x962850 and reads two vtable slots - checker: 10 / 8 / 8 checks, i.e. hashed, which is why they are
 *   only read), the byte [0x156b73a] 'start pending' (0 checks), [0x154d5f4]+0xd4 (menu option 'Dummy', logged at
 *   [Expansion] Log=2 only), [0xdd2640]
 *   (+0x2b0 scene name: klsteam, kljoin), [0xdd265c] (+0x828 / +0x898 local players, +0x8c4 jump list: kljoin),
 *   0x58ffc3 (11 bytes of start-up code compared to find the game's own fatal-fault filter 0x90b780; a read),
 *   [0x168e598]+0x70 / +0x5c (session state and game mode: klsteam's 'session:' line; 0 checks), the window and
 *   player objects klauto looks at. The real ISteamUserStats table is read, never written. kl2.exe never reads another module's code and
 *   hashes nothing outside its own image (re\antitamper.md 2.1), so this DLL being loaded is not seen.
 *   The vectored exception handler passes Steam's probe (kl2 0xa8e3cb, a deliberate write to 0 before every
 *   scene load) on untouched and no longer dumps it (three 35 - 48 MB dumps a run for nothing: MaxDumps was
 *   used up before the real fault, and the in-process dumps cost address space - re\crash_scorepage.md 6).
 *
 * WHAT SHIP DOES
 *  - KLHook.log: every engine assert (int3 inside kl2.exe) and fault, with registers and the stack's kl2.exe
 *    return addresses; KLHook_N.dmp: a minidump that includes the memory registers / stack point at.
 *    ContinueAsserts=1 steps over engine asserts (retail asserts are bare int3: without this the first one ends
 *    the game).
 *  - A fatal fault (nothing handled it) is logged with module + offset whatever module it is in, dumped, handed
 *    to the game's own filter (kl2 0x90b780: Steam's kl2_<build>_crash_*.mdmp; it returns 0), and then the
 *    process is ended HERE with the exception code. Without that last step Windows Error Reporting takes over,
 *    and on this machine each such report left a thread-less "kl2.exe" entry behind that keeps dinput8.dll
 *    mapped until reboot (21 by 2026-10-09 11:10; `debug\zombies.py`, creation times = the 'Application Error'
 *    events to the second). EndOnFatal=0 gives the stock behaviour back. NOT CAUGHT: __fastfail / a /GS cookie
 *    failure (they go to Windows directly).
 *  - The leaderboard row count fix (klfix.c) and the expansion (klslot.c), both driven by the per-frame tick:
 *    kl2.exe's main loop 0x87a930 calls SteamAPI_RunCallbacks once a frame (call at 0x87aa7c; that return
 *    address is on every main-thread stack in the logs), so its import slot gives a call on the game's own
 *    thread with no code patch. Seen live (HK1, S1, S2, J2): the call comes in the menu and in a round; while a
 *    level loads the main loop stands still, so a fallback thread ticks every 100 ms whenever the slot has been
 *    silent for 500 ms (the 'tick: driven by' line flips a few times at every boot and load; said six times).
 *  - Exit tripwire: ExitProcess is logged; code 0x8000dead is spelled out as INTEGRITY EXIT. exit / _exit of the
 *    C runtime are logged too (an AutoExit end left no ExitProcess line in run HK1).
 *  - Steam write guard (klsteam.c) and jump boxes (kljoin.c); the CreateFileA / CreateFileW import wrappers of
 *    klslot.c are installed even with [Expansion] Enable=0, because the guard has to see which level archive the
 *    game opens (they change nothing then).
 *
 * KLHook.ini
 *   [KLHook]
 *   ContinueAsserts=1   MaxAsserts=200   MaxDumps=4
 *   EndOnFatal=1        end the process ourselves after a fatal fault was logged (see above)
 *   ExitLog=1           wrap ExitProcess and MSVCR90 exit / _exit (the tripwire and the exit line)
 *   Tick=1              wrap SteamAPI_RunCallbacks; 0 = the fallback thread alone drives the tick
 *   LbFix=1             klfix.c; 0 = only log the value found
 *   SessionSafe=1       TEST only (SHIP is always 'ship'): 0 = policy 'direct'
 *   Join=1              0 = no jump box fires (kljoin.c)
 *   [Expansion] [Redirect] [Redirect.N] [Page.N] [Slots]    klslot.c
 *   [Steam]                                                 klsteam.c (Block, Log, State)
 *   [Net] PrivateLobby=0/1/2  BuildKey=0/1                  klmm.c (default 0: nothing installed)
 *   [Join] [Join.2] .. [Join.8]                             kljoin.c (also KLJoin.ini beside a level archive)
 *   [CrewJoin] [Crew] [Talk] [Voice]                                klcrew_rt.c, klcrew.c, kltalk.c - each OFF unless its key is set
 *   [CrewHop]                                               klhop.c (also [CrewHop] in the KLJoin.ini beside a level archive) - OFF unless Enable=1
 *   [HUD]                                                   klhud.c (+ klhud_values.c, klhud_weapon.c, klhud_popup.c) - OFF unless Enable=1; Draft=1 = the whole draft
 *   [Auto] [Engine] [Script]                                klauto.c (TEST)
 *
 * BUILD: cl 19.4x x86, /O2 /LD /W3, export DirectInput8Create=_DirectInput8Create@20 (build.bat, build_auto.bat).
 * klauto.c compiled on its own still works: it defines KLHOOK_TEST and includes this file.
 * Off-game tests: see the end of klslot.c and re\slot_redirect.md 8 (harness sources are not in the repo).
 */
#ifndef KLHOOK_C
#define KLHOOK_C
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <math.h>
#include <intrin.h>

#define KL2_BASE      0x400000u
#define KL2_TIMESTAMP 0x4c80f728u
#define KL2_IMAGESIZE 0x134e000u
#define KL2_PROBE     0xa8e3cbu                   /* Steam's anti-debug probe: a write to 0 its own SEH handler resumes */
#define KL2_SYSIF     0xdd2640u                   /* ZSysInterface *; +0x2b0 = char * name of the scene (klauto.c, 0x53aca1) */
#define KL2_GAMEDATA  0xdd265cu                   /* ZFFGameData * */

typedef HRESULT (WINAPI *DI8Create)(HINSTANCE, DWORD, REFIID, LPVOID *, LPUNKNOWN);
static DI8Create real_create;
static char dir[MAX_PATH], klh_ini[MAX_PATH], klh_out[MAX_PATH];   /* klh_out: KLHook.ini / .log / dumps = dir, or in TEST the env KLHOOK_DIR (klsolo.c) */
static int continue_asserts = 1, max_dumps = 4, dumps = 0, max_asserts = 200;
static DWORD seen[256]; static int nseen;
static CRITICAL_SECTION cs;
static DWORD img_lo = 0x400000, img_hi = 0x400000;
static int klh_exe_ok;                            /* the process image is kl2.exe build 0490 at 0x400000 */
static LONG_PTR klh_delta;                        /* 0 in the game; an off-game harness maps a copy of kl2.exe elsewhere */
#define KLH_VA(x) ((BYTE *)((DWORD_PTR)(x) + klh_delta))

/* KLHook.log stays OPEN for the whole run (2026-10-14, the owner: 'im getting bad stutters'): it used to be opened, appended to and
   closed for every line - on the game's threads, several times a second, on a file of 60+ MB - and each close of a changed file
   lets the virus scanner look at it again. Now one handle (append only, others may read, rename or delete it while the game runs),
   one WriteFile a line (the line is whole: appends of one call never interleave), no close until the process ends. */
static HANDLE volatile klog_h;
static void klog(const char *fmt, ...)
{
    char buf[1536], *line = buf; int n, m; DWORD put; SYSTEMTIME t; va_list a; HANDLE h = klog_h;
    if (!h) {
        char path[MAX_PATH]; WIN32_FILE_ATTRIBUTE_DATA fa; int cap;
        snprintf(path, sizeof path, "%s\\KLHook.log", klh_out);
        /* LogMaxMB (2026-10-23, default 64, 0 = no cap): a log over the cap when the game starts becomes KLHook.old.log (one
           older run's worth replaced) and a fresh one begins, so it can never grow back to the 562 MB of 10-23. */
        cap = klh_ini[0] ? (int)GetPrivateProfileIntA("KLHook", "LogMaxMB", 64, klh_ini) : 64;
        if (cap > 0 && GetFileAttributesExA(path, GetFileExInfoStandard, &fa) &&
            (fa.nFileSizeHigh || fa.nFileSizeLow > (DWORD)cap * 1048576u)) {
            char old[MAX_PATH]; snprintf(old, sizeof old, "%s\\KLHook.old.log", klh_out);
            MoveFileExA(path, old, MOVEFILE_REPLACE_EXISTING);
        }
        h = CreateFileA(path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, 0, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, 0);
        if (h == INVALID_HANDLE_VALUE) return;
        if (InterlockedCompareExchangePointer((void *volatile *)&klog_h, h, 0) != 0) { CloseHandle(h); h = klog_h; }
    }
    GetLocalTime(&t);
    n = snprintf(buf, sizeof buf, "%02d:%02d:%02d.%03d ", t.wHour, t.wMinute, t.wSecond, t.wMilliseconds);
    va_start(a, fmt); m = _vsnprintf(buf + n, sizeof buf - n - 2, fmt, a); va_end(a);
    if (m < 0) {                                              /* longer than the buffer (none so far is over 1200): the heap */
        int need; va_start(a, fmt); need = _vscprintf(fmt, a); va_end(a);
        if (need > 0 && (line = (char *)HeapAlloc(GetProcessHeap(), 0, (SIZE_T)n + need + 3)) != 0) {
            memcpy(line, buf, (size_t)n); va_start(a, fmt); m = _vsnprintf(line + n, (size_t)need + 1, fmt, a); va_end(a);
        } else { line = buf; m = (int)(sizeof buf - n - 2); }
        if (m < 0) m = 0;
    }
    n += m; line[n++] = '\r'; line[n++] = '\n';
    WriteFile(h, line, (DWORD)n, &put, 0);
    if (line != buf) HeapFree(GetProcessHeap(), 0, line);
}

static volatile LONG klh_reads;              /* klh_rd calls (the perf line; approximate: a plain count from several threads) */
static int klh_rd(DWORD_PTR p, void *out, SIZE_T n)
{   /* never faults: nothing in this DLL may raise an exception of its own */
    SIZE_T got = 0;
    klh_reads++;
    return p > 0xffff && ReadProcessMemory(GetCurrentProcess(), (void *)p, out, n, &got) && got == n;
}
static DWORD klh_rd32(DWORD_PTR p) { DWORD v = 0; klh_rd(p, &v, 4); return v; }
/* the session manager [0x168e598] (ZSessionManagerMultiplayer) has vtable 0xbd1ebc, or - with [Lobby] Solo=1, kllobby.c - the private copy of it at klh_sm_vt2 */
static DWORD klh_sm_vt2;
#define KLH_SM_VT_OK(v) ((v) == 0xbd1ebc || ((v) && (v) == klh_sm_vt2))
/* the Sv rules object (ZGameRulesFragileAllianceSv, 0xbd2eb4) with the private vtable copy of klroundkeep.c ([Lobby] KeepRound / TEST probe) */
static DWORD klh_rules_vt2;
#define KLH_RULES_SV_OK(v) ((v) == 0xbd2eb4 || ((v) && (v) == klh_rules_vt2))
/* the Cl rules object (ZGameRulesFragileAllianceCl, 0xbd31e4) with the private vtable copy of klucc_down.c ([Ucc] DownOnly, slot 15) */
static DWORD klh_rules_vt3;
#define KLH_RULES_CL_OK(v) ((v) == 0xbd31e4 || ((v) && (v) == klh_rules_vt3))

/* [Net] OnlineSafe=1 (default 1): kl_online() = 1 when this machine is in a NETWORK session, and then every part that WRITES game state
   stays out of it (re\netcode_plan.md 2.1). The test is the one the AI parts already make (klbot.c klb_read / klbalance.c klr_arcade):
   session [0x168e598]: role [+0x54] 2 = SERVER or 3 = CLIENT, or game type [+0x5c] == 4 with a rules object [[0x168e9e4]+0x54] whose
   vtable is not ZGameRulesHeist 0xbd3514 (online: ...FragileAllianceSv / Cl). No session, a story mode or an unreadable object = 0, so
   with the key absent (or =0) and offline the answer is always 0 and nothing changes. GUESS: a role of 2 / 3 is only ever set by a
   network session (klbot.c's reading; not seen live in an online game). Needs no later include: it reads three addresses itself. */
static int kl_online(void)
{
    static int safe = -1; DWORD sm, gs, rules, role = 0, mode = 0;
    if (safe < 0) safe = GetPrivateProfileIntA("Net", "OnlineSafe", 1, klh_ini) != 0;
    if (!safe || !klh_exe_ok) return 0;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598)))) return 0;
    if (klh_rd(sm + 0x54, &role, 4) && (role == 2 || role == 3)) return 1;
    if (!klh_rd(sm + 0x5c, &mode, 4) || mode != 4) return 0;
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(0x0168e9e4))) || !(rules = klh_rd32(gs + 0x54))) return 0;
    return klh_rd32(rules) != 0x00bd3514;
}

static int klh_rdstr(DWORD_PTR p, char *out, int cap)
{   /* a NUL-terminated text of the game, at most cap-1 characters; never faults. -> length, 0 = none / not text */
    int n = 0, i;
    out[0] = 0;
    while (n < cap - 1) {                             /* page by page: the text may end just before unmapped memory */
        int k = (int)(0x1000 - ((p + n) & 0xfff)); if (k > cap - 1 - n) k = cap - 1 - n;
        if (!klh_rd(p + n, out + n, (SIZE_T)k)) break;
        for (i = 0; i < k; i++) {
            if (!out[n + i]) return n + i;
            if ((BYTE)out[n + i] < 0x20) { out[0] = 0; return 0; }
        }
        n += k;
    }
    out[n] = 0;
    return n;
}

static int klh_scene(char *out, int cap)
{   /* the engine's scene name, e.g. 'SCENES\Locations\F01\F01_Main.gms'; 0 = none yet or not the known exe */
    DWORD sys;
    out[0] = 0;
    if (!klh_exe_ok || !(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF)))) return 0;
    return klh_rdstr(klh_rd32(sys + 0x2b0), out, cap);
}

static int klh_level_key(const char *scene, char *key, int cap)
{   /* 'SCENES\Locations\F01\F01_Main.gms' (or a path, either slash) -> "f01\f01_main" (lower case, no extension);
       0 = not under Locations */
    char low[200], *p, *q; int i;
    for (i = 0; scene[i] && i < (int)sizeof low - 1; i++) low[i] = (char)(scene[i] >= 'A' && scene[i] <= 'Z' ? scene[i] + 32 : scene[i] == '/' ? 0x5c : scene[i]);      /* 0x5c = backslash */
    low[i] = 0;
    for (p = 0, q = low; (q = strstr(q, "locations\\")) != 0; q += 10) if (q == low || q[-1] == 0x5c) p = q + 10;
    if (!p || !*p || (int)strlen(p) >= cap) return 0;
    strcpy(key, p);
    if ((q = strrchr(key, '.')) != 0 && !strchr(q, 0x5c)) *q = 0;
    return key[0] != 0;
}

/* ---------------------------------------------------------------- the patch guard */

#include "klranges.h"
enum { KLH_SHIP, KLH_SESSION, KLH_DIRECT };
#ifdef KLHOOK_TEST
static int klh_policy = KLH_SESSION;
#else
static const int klh_policy = KLH_SHIP;
#endif
static const char *const klh_policy_name[3] = { "ship (import slots and data only)", "session (nothing inside a hashed range)", "direct (anything; direct-boot runs only)" };
static LONG klh_refused, klh_hashed_in;           /* refused writes; hashed bytes patched under 'direct' */

static BYTE *klh_image(void) { return klh_delta ? KLH_VA(KL2_BASE) : (BYTE *)(DWORD_PTR)img_lo; }

static int klh_is_hashed(DWORD va, DWORD len)
{   /* does [va, va+len) touch a range the integrity checks hash? (table: klranges.h, ascending) */
    int lo = 0, hi = KLH_NHASHED - 1;
    while (lo <= hi) {
        int m = (lo + hi) / 2;
        if (klh_hashed[m][1] <= va) lo = m + 1; else if (klh_hashed[m][0] >= va + len) hi = m - 1; else return 1;
    }
    return 0;
}

/* what an address of the game's image is: 'i' import address table, 'w' a writable section (.data / .bss),
   'x' code, 'r' other read-only bytes (constants, vtables, headers); 0 = not in the image */
static int klh_kind(const void *at, DWORD len, char name[9])
{
    BYTE *base = klh_image(); IMAGE_NT_HEADERS *nt; IMAGE_SECTION_HEADER *s; IMAGE_DATA_DIRECTORY *d; IMAGE_IMPORT_DESCRIPTOR *im; DWORD rva; int i;
    name[0] = 0;
    if (IsBadReadPtr(base, 0x400) || ((IMAGE_DOS_HEADER *)base)->e_magic != IMAGE_DOS_SIGNATURE) return 0;
    nt = (IMAGE_NT_HEADERS *)(base + ((IMAGE_DOS_HEADER *)base)->e_lfanew);
    if ((BYTE *)at + len <= base || (BYTE *)at >= base + nt->OptionalHeader.SizeOfImage) return 0;
    rva = (DWORD)((BYTE *)at - base);
    d = &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IAT];
    if (d->VirtualAddress && rva >= d->VirtualAddress && rva + len <= d->VirtualAddress + d->Size) { strcpy(name, "IAT"); return 'i'; }
    d = &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
    if (d->VirtualAddress)                        /* no IAT directory: the FirstThunk arrays themselves */
        for (im = (IMAGE_IMPORT_DESCRIPTOR *)(base + d->VirtualAddress); im->Name; im++) {
            IMAGE_THUNK_DATA *t = (IMAGE_THUNK_DATA *)(base + im->FirstThunk), *n = (IMAGE_THUNK_DATA *)(base + (im->OriginalFirstThunk ? im->OriginalFirstThunk : im->FirstThunk));
            DWORD k = 0; while (n[k].u1.AddressOfData) k++;
            if ((BYTE *)at >= (BYTE *)t && (BYTE *)at + len <= (BYTE *)(t + k)) { strcpy(name, "IAT"); return 'i'; }
        }
    for (i = 0, s = IMAGE_FIRST_SECTION(nt); i < nt->FileHeader.NumberOfSections; i++, s++)
        if (rva >= s->VirtualAddress && rva < s->VirtualAddress + (s->Misc.VirtualSize ? s->Misc.VirtualSize : s->SizeOfRawData)) {
            memcpy(name, s->Name, 8); name[8] = 0;
            return s->Characteristics & IMAGE_SCN_MEM_WRITE ? 'w' : s->Characteristics & IMAGE_SCN_MEM_EXECUTE ? 'x' : 'r';
        }
    strcpy(name, "headers");
    return 'r';
}

/* the one header field a ship build may write: OptionalHeader.SizeOfStackReserve (klmem.c OtherStackKB), data CreateThread reads for
   a default stack (checked on Win10 WOW64 with a probe exe, 10-25: 4096 -> 1024 KB; thread-pool workers keep the size from process start).
   The header is outside every hashed range. */
static int klh_stack_field(const void *at, DWORD len)
{
    BYTE *base = klh_image(); IMAGE_NT_HEADERS32 *nt = (IMAGE_NT_HEADERS32 *)(base + ((IMAGE_DOS_HEADER *)base)->e_lfanew);
    return len == 4 && at == (const void *)&nt->OptionalHeader.SizeOfStackReserve;
}

/* THE guard: may len bytes at 'at' be written under the current policy? Every write of this DLL into the game
   asks here first (klh_poke, klh_data, klh_iat). A refusal is logged and counted. */
static int klh_may_write(const void *at, DWORD len, const char *what)
{
    char sec[9]; int kind = klh_kind(at, len, sec), hashed; DWORD va; const char *why = 0;
    if (!kind) return 1;                          /* heap, stacks, this DLL, other modules: data the game does not hash */
    va = (DWORD)((BYTE *)at - klh_image()) + KL2_BASE;
    hashed = klh_exe_ok ? klh_is_hashed(va, len) : kind != 'i' && kind != 'w';      /* unknown exe: no map, assume the worst */
    if (klh_policy == KLH_DIRECT) {
        if (hashed && InterlockedIncrement(&klh_hashed_in) <= 40)
            klog("patch %08lx +%lu (%s, %s): inside a HASHED range - policy 'direct': this run must not start a session", va, len, sec, what);
        return 1;
    }
    if (hashed) why = klh_exe_ok ? "inside a range kl2.exe's integrity checks hash" : "not the known kl2.exe: no range map, so only import slots and data";
    else if (klh_policy == KLH_SHIP && kind != 'i' && kind != 'w' && !klh_stack_field(at, len)) why = "code or constants: a ship build writes import slots and data only";
    if (!why) return 1;
    if (InterlockedIncrement(&klh_refused) <= 64)
        klog("patch REFUSED %08lx +%lu (%s, %s): %s%s", va, len, sec, what, why, klh_policy == KLH_SESSION ? " ([KLHook] SessionSafe=0 allows it for a direct-boot run)" : "");
    return 0;
}

/* Replace len bytes of the game's image (an import slot, or in TEST code / a vtable entry), only if the explen
   bytes there are exactly the expected ones and the guard agrees. */
static int klh_poke(void *at, const void *expect, int explen, const void *bytes, int len, const char *what)
{
    BYTE cur[16]; DWORD old; MEMORY_BASIC_INFORMATION mbi;
    if (explen > (int)sizeof cur || !klh_rd((DWORD_PTR)at, cur, explen) || memcmp(cur, expect, explen)) return 0;
    if (!klh_may_write(at, len, what)) return 0;
    if (!VirtualQuery(at, &mbi, sizeof mbi)) return 0;
    if (!VirtualProtect(at, len, mbi.Protect & (PAGE_EXECUTE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY) ? PAGE_EXECUTE_READWRITE : PAGE_READWRITE, &old)) return 0;
    memcpy(at, bytes, len);
    VirtualProtect(at, len, old, &old); FlushInstructionCache(GetCurrentProcess(), at, len);
    return 1;
}

/* Write DATA of the game: a heap object or a .data / .bss global. Never changes a page protection: memory that
   is not writable as it stands is not data, and is left alone. */
static int klh_data(void *at, const void *bytes, int len, const char *what)
{
    MEMORY_BASIC_INFORMATION mbi;
    if (!klh_may_write(at, len, what)) return 0;
    if (!VirtualQuery(at, &mbi, sizeof mbi) || mbi.State != MEM_COMMIT || !(mbi.Protect & (PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READWRITE)) ||
        (mbi.Protect & PAGE_GUARD) || (BYTE *)at + len > (BYTE *)mbi.BaseAddress + mbi.RegionSize) return 0;
    memcpy(at, bytes, len);
    return 1;
}

/* Point the exe's import of <fn> (from <dll>, or from any module when dll is 0) at <mine>; the old target goes
   to *real first. -> entries changed. Walks the import directory by name: no address of kl2.exe is assumed. */
static int klh_iat(const char *dll, const char *fn, void *mine, void **real)
{
    BYTE *base = (BYTE *)(DWORD_PTR)img_lo; int done = 0;
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)(base + ((IMAGE_DOS_HEADER *)base)->e_lfanew);
    IMAGE_DATA_DIRECTORY *dd = &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
    IMAGE_IMPORT_DESCRIPTOR *d;
    if (!dd->VirtualAddress) return 0;
    for (d = (IMAGE_IMPORT_DESCRIPTOR *)(base + dd->VirtualAddress); d->Name; d++) {
        IMAGE_THUNK_DATA *nm, *at;
        if (!d->OriginalFirstThunk || (dll && _stricmp((char *)base + d->Name, dll))) continue;
        nm = (IMAGE_THUNK_DATA *)(base + d->OriginalFirstThunk); at = (IMAGE_THUNK_DATA *)(base + d->FirstThunk);
        for (; nm->u1.AddressOfData; nm++, at++) {
            MEMORY_BASIC_INFORMATION mbi; void *cur = (void *)(DWORD_PTR)at->u1.Function; DWORD_PTR v = (DWORD_PTR)mine;
            if (IMAGE_SNAP_BY_ORDINAL(nm->u1.Ordinal) || strcmp((char *)((IMAGE_IMPORT_BY_NAME *)(base + nm->u1.AddressOfData))->Name, fn)) continue;
            if (cur == mine) continue;
            if (!VirtualQuery(cur, &mbi, sizeof mbi) || mbi.Type != MEM_IMAGE || mbi.AllocationBase == (void *)base) {
                klog("import %s is not resolved yet (%p): left alone", fn, cur); continue;
            }
            if (!*real) *real = cur;
            if (klh_poke(&at->u1.Function, &cur, sizeof cur, &v, sizeof v, fn)) done++;
            else klog("import %s: slot not changed", fn);
        }
    }
    return done;
}

static void klh_module(DWORD_PTR addr, char *out, int cap, DWORD *off)
{
    MEMORY_BASIC_INFORMATION mbi; char path[MAX_PATH], *s;
    *off = (DWORD)addr;
    if (VirtualQuery((void *)addr, &mbi, sizeof mbi) && mbi.AllocationBase && mbi.Type == MEM_IMAGE &&
        GetModuleFileNameA((HMODULE)mbi.AllocationBase, path, MAX_PATH)) {
        s = strrchr(path, '\\'); snprintf(out, cap, "%s", s ? s + 1 : path);
        *off = (DWORD)(addr - (DWORD_PTR)mbi.AllocationBase);
    } else snprintf(out, cap, "<no module>");
}

/* ---------------------------------------------------------------- crash logging */

typedef BOOL (WINAPI *MDWD)(HANDLE, DWORD, HANDLE, int, void *, void *, void *);
typedef struct { DWORD tid; EXCEPTION_POINTERS *ep; BOOL client; } MEI;

static void write_dump(EXCEPTION_POINTERS *ep, const char *why)
{
    if (dumps >= max_dumps) return;
    HMODULE h = LoadLibraryA("dbghelp.dll"); if (!h) return;
    MDWD w = (MDWD)GetProcAddress(h, "MiniDumpWriteDump"); if (!w) return;
    char path[MAX_PATH]; snprintf(path, sizeof path, "%s\\KLHook_%d.dmp", klh_out, ++dumps);
    HANDLE f = CreateFileA(path, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, 0, 0);
    if (f == INVALID_HANDLE_VALUE) return;
    MEI mei = { GetCurrentThreadId(), ep, FALSE };
    /* Normal | DataSegs | IndirectlyReferencedMemory | ThreadInfo | FullMemoryInfo (the list of every region of the
       address space, free ones too: debug\vmmap.py reads it - who holds the 2 GB when a level's block finds no place) */
    int type = 0x0 | 0x1 | 0x40 | 0x1000 | 0x800;
    if (!w(GetCurrentProcess(), GetCurrentProcessId(), f, type, &mei, 0, 0)) {    /* a dbghelp.dll that does not know the list */
        SetFilePointer(f, 0, 0, FILE_BEGIN); SetEndOfFile(f);
        w(GetCurrentProcess(), GetCurrentProcessId(), f, type & ~0x800, &mei, 0, 0);
    }
    CloseHandle(f);
    klog("  dump written: KLHook_%d.dmp (%s)", dumps, why);
}

static void log_context(CONTEXT *c)
{
    klog("  eax=%08lx ebx=%08lx ecx=%08lx edx=%08lx esi=%08lx edi=%08lx ebp=%08lx esp=%08lx",
         c->Eax, c->Ebx, c->Ecx, c->Edx, c->Esi, c->Edi, c->Ebp, c->Esp);
    char line[512]; int n = 0, k = 0;
    DWORD *sp = (DWORD *)c->Esp;
    n += snprintf(line + n, sizeof line - n, "  callers:");
    for (int i = 0; i < 2048 && k < 16; i++) {
        DWORD v;
        if (IsBadReadPtr(sp + i, 4)) break;
        v = sp[i];
        if (v > img_lo && v < img_hi && !IsBadReadPtr((void *)(v - 5), 5) &&
            (((BYTE *)v)[-5] == 0xE8 || ((BYTE *)v)[-2] == 0xFF || ((BYTE *)v)[-3] == 0xFF || ((BYTE *)v)[-6] == 0xFF)) {
            n += snprintf(line + n, sizeof line - n, " %08lx", v); k++;
        }
    }
    klog("%s", line);
}

static LONG CALLBACK veh(EXCEPTION_POINTERS *ep)
{
    DWORD code = ep->ExceptionRecord->ExceptionCode;
    DWORD at = (DWORD)ep->ExceptionRecord->ExceptionAddress;
    if (at < img_lo || at >= img_hi) return EXCEPTION_CONTINUE_SEARCH;
    if (code != EXCEPTION_BREAKPOINT && code != EXCEPTION_ACCESS_VIOLATION &&
        code != EXCEPTION_ILLEGAL_INSTRUCTION && code != EXCEPTION_INT_DIVIDE_BY_ZERO)
        return EXCEPTION_CONTINUE_SEARCH;
    if (klh_exe_ok && at == KL2_PROBE) {              /* Steam's probe: passed on untouched (the context must not be
                                                         edited here, re\antitamper.md 6), not dumped, said once */
        static LONG told;
        if (!InterlockedExchange(&told, 1)) klog("Steam's probe at kl2.exe+68e3cb (a deliberate write to 0 before each scene load, resumed by the game's own handler): not a crash, not dumped; not logged again");
        return EXCEPTION_CONTINUE_SEARCH;
    }
    EnterCriticalSection(&cs);
    int first = 1;
    for (int i = 0; i < nseen; i++) if (seen[i] == at) first = 0;
    if (first && nseen < 256) seen[nseen++] = at;
    static int total;
    total++;
    if (code == EXCEPTION_BREAKPOINT) {
        if (first || total < 20) {
            klog("ASSERT at kl2.exe+%06lx (%08lx)%s", at - img_lo, at, first ? "" : " (again)");
            log_context(ep->ContextRecord);
            if (first) write_dump(ep, "assert");
        }
        if (continue_asserts && total < max_asserts && ((BYTE *)at)[0] == 0xCC) {
            ep->ContextRecord->Eip += 1;          /* step over the int3 */
            LeaveCriticalSection(&cs);
            return EXCEPTION_CONTINUE_EXECUTION;
        }
        klog("  not continuing (limit reached or disabled)");
    } else {
        klog("CRASH %08lx at kl2.exe+%06lx (%08lx)", code, at - img_lo, at);
        if (code == EXCEPTION_ACCESS_VIOLATION)
            klog("  %s address %08lx", ep->ExceptionRecord->ExceptionInformation[0] ? "writing" : "reading",
                 (DWORD)ep->ExceptionRecord->ExceptionInformation[1]);
        log_context(ep->ContextRecord);
        dumps = dumps < max_dumps ? dumps : max_dumps - 1;   /* always dump the crash itself */
        write_dump(ep, "crash");
    }
    LeaveCriticalSection(&cs);
    return EXCEPTION_CONTINUE_SEARCH;
}

/* ---------------------------------------------------------------- fatal faults: log, then end cleanly

   The last-chance filter. kl2.exe installs its own at 0x58ffc8 (0x90b780: SteamAPI_SetMiniDumpComment,
   SteamAPI_WriteMiniDump, returns 0 = continue search), after which Windows Error Reporting ends the process.
   Other DLLs install theirs later (wrap_oal.dll's calls UnhandledExceptionFilter again from inside itself:
   with a filter that chains to it that is an endless loop - run RN11's 'stack overflow', re\crash_scorepage.md
   3). So: ours is re-armed by the tick, the ONLY filter it ever calls is one that lies inside kl2.exe (the
   game's own), and it is entered once. */
static LPTOP_LEVEL_EXCEPTION_FILTER klh_game_uef;
static int klh_end_on_fatal = 1, klh_uef_on;

static LONG WINAPI klh_uef(EXCEPTION_POINTERS *ep)
{
    static volatile LONG busy;
    DWORD code = ep->ExceptionRecord->ExceptionCode, off; DWORD_PTR at = (DWORD_PTR)ep->ExceptionRecord->ExceptionAddress; char mod[80];
    if (InterlockedExchange(&busy, 1)) return EXCEPTION_CONTINUE_SEARCH;      /* re-entered (a filter that calls back) or a second thread */
    klh_module(at, mod, sizeof mod, &off);
    klog("FATAL unhandled exception %08lx at %s+0x%lx (%08lx)", code, mod, off, (DWORD)at);
    if (code == EXCEPTION_ACCESS_VIOLATION && ep->ExceptionRecord->NumberParameters >= 2)
        klog("  %s address %08lx", ep->ExceptionRecord->ExceptionInformation[0] ? "writing" : "reading", (DWORD)ep->ExceptionRecord->ExceptionInformation[1]);
    if (code != EXCEPTION_STACK_OVERFLOW) {                                    /* no room for a dump on an exhausted stack */
        log_context(ep->ContextRecord);
        dumps = dumps < max_dumps ? dumps : max_dumps - 1;
        write_dump(ep, "unhandled");
        if (klh_game_uef) klh_game_uef(ep);                                    /* the game's Steam minidump, kl2_<build>_crash_*.mdmp */
    }
    if (!klh_end_on_fatal) { klog("  EndOnFatal=0: left to Windows"); return EXCEPTION_CONTINUE_SEARCH; }
    klog("  process ended here with exit code %08lx (no Windows error report)", code);
    TerminateProcess(GetCurrentProcess(), code);
    return EXCEPTION_EXECUTE_HANDLER;
}

static void klh_uef_arm(void)
{
    static int told; LPTOP_LEVEL_EXCEPTION_FILTER prev;
    if (!klh_uef_on) return;
    /* Run HK1 (SHIP, live): the filters found under ours were none, CSERHelper.dll+0x12571 (Steam's) and
       wrap_oal.dll+0x491ba - never the game's. kl2.exe sets its own at start-up (0x58ffc3 `push 0x90b780 ; call
       SetUnhandledExceptionFilter`) and SteamAPI_Init puts Steam's over it within the same 100 ms, between two of
       our looks. So the game's filter is taken from the instruction that installs it, not from what
       SetUnhandledExceptionFilter hands back. Read only. */
    if (!klh_game_uef && klh_exe_ok && !klh_delta) {
        BYTE ins[11];
        if (klh_rd(0x58ffc3, ins, sizeof ins) && ins[0] == 0x68 && *(DWORD *)(ins + 1) == 0x90b780 && ins[5] == 0xff && ins[6] == 0x15 && *(DWORD *)(ins + 7) == 0xb10250) {
            klh_game_uef = (LPTOP_LEVEL_EXCEPTION_FILTER)(DWORD_PTR)0x90b780;
            klog("fatal-fault filter: the game's own is kl2.exe+0x50b780 (read from its start-up code); it is called after ours has logged");
        }
    }
    prev = SetUnhandledExceptionFilter(klh_uef);
    if (prev == klh_uef) return;
    if (!klh_game_uef && (DWORD_PTR)prev >= img_lo && (DWORD_PTR)prev < img_hi) klh_game_uef = prev;
    if (told++ < 6) { char mod[80]; DWORD off; klh_module((DWORD_PTR)prev, mod, sizeof mod, &off);
        klog("fatal-fault filter installed over %p (%s+0x%lx)%s", (void *)(DWORD_PTR)prev, prev ? mod : "none", prev ? off : 0, klh_game_uef == prev && prev ? ": the game's own" : ""); }
}

/* ---------------------------------------------------------------- exit tripwire (import slot of ExitProcess) */

static void (WINAPI *klh_real_exitprocess)(UINT);
static void klx_exit_line(void);
/* [KLHook] FastExit=1 (default 1; 2026-10-23, owner: 'alt f4 must close the game instead of crashing'): the process is ended with
   TerminateProcess at once - on Alt+F4 / WM_CLOSE / SC_CLOSE (klh_uia_proc below) and when the game reaches ExitProcess itself
   (menu Quit). A normal ExitProcess ends every other thread, then runs DLL_PROCESS_DETACH of every loaded DLL under the loader lock
   (steam_api, gameoverlayrenderer, ReShade32, the audio wrappers): GUESS that one of those, or a thread the game never joins, is what
   hung or crashed. Nothing on disk needs undoing at exit (klog is unbuffered WriteFile, the Windows cache survives TerminateProcess). */
static int klh_fastexit = 1;
/* [Log] ExitTrace=1 (k43, recommended on): who ends the game. klh_exit_trace (below, with the window subclass) logs the caller of exit / _exit /
   ExitProcess, the code, the foreground window (handle, pid, title) and whether the game window still exists; klh_uia_proc logs the close messages. */
static int klh_exittrace = 1;
static void klh_exit_trace(const char *what, int code, void *ra);
static void WINAPI klh_w_exitprocess(UINT code)
{
    klh_exit_trace("ExitProcess", (int)code, _ReturnAddress());
    if (code == 0x8000dead)
        klog("INTEGRITY EXIT: ExitProcess(0x8000dead) - kl2.exe's code-integrity check found a changed byte of its image (re\\antitamper.md). "
             "Patches refused this run: %ld; hashed bytes patched under policy 'direct': %ld", klh_refused, klh_hashed_in);
    else klog("exit: ExitProcess(%lu)", (DWORD)code);
    klx_exit_line();
    if (klh_fastexit) { klog("exit: FastExit - the process is ended without the DLL detach round"); TerminateProcess(GetCurrentProcess(), code); }
    klh_real_exitprocess(code);
}

/* The C runtime's exit / _exit (kl2.exe's imports from MSVCR90.dll, 8 + 5 call sites). Run HK1 (SHIP, direct boot
   ended by AutoExit) left NO 'exit:' line: that end does not come through kl2.exe's ExitProcess import (two call
   sites, 0x7e8a6c and 0x8f8793). ASSUMPTION, not seen: it leaves through exit() - WinMain returning into the C
   start-up code - whose ExitProcess call is MSVCR90's own import. klauto wraps the same two slots on top of
   these when [Auto] is on (its END lines); both chain. */
static void (__cdecl *klh_real_exit)(int), (__cdecl *klh_real__exit)(int);
static void __cdecl klh_w_exit(int code) { klh_exit_trace("exit", code, _ReturnAddress()); klog("exit: exit(%d)", code); klx_exit_line(); klh_real_exit(code); }
static void __cdecl klh_w__exit(int code) { klh_exit_trace("_exit", code, _ReturnAddress()); klog("exit: _exit(%d)", code); klx_exit_line(); klh_real__exit(code); }

/* ---------------------------------------------------------------- the parts */

static void klh_tick(int game_thread);
/* the vtable of a ZFFActor as the class tests mean it: klsync.c [Sync] Puppet gives a puppeted cop a private copy of the table (klh_actor_priv, 0 = none);
   every 'vtable == 0xbb3bac' test reads through this so a puppeted cop is still a ZFFActor for them */
static DWORD klh_actor_priv, klh_actor_priv2;      /* priv2: klbalance.c [BotFill] OnlineCopToBot gives the host's bots a private table too (slot 423 wrapped) */
static DWORD klh_avt(DWORD o) { DWORD v = klh_rd32(o); return ((klh_actor_priv && v == klh_actor_priv) || (klh_actor_priv2 && v == klh_actor_priv2)) ? 0x00bb3bacu : v; }
static DWORD_PTR klh_rcb_ra;                          /* the return address of the SteamAPI_RunCallbacks call that runs this tick (klfreeclimb.c acts only at the gameplay one) */
#include "klmem.c"
#include "klhigh.c"                                      /* klhigh.c: [Memory] High - the 4 GB flag made safe: the listed foreign modules' VirtualAlloc goes above 2 GB, the game stays below (off unless High=1/2); AFTER klmem.c */
#include "klextpt.c"                                     /* klextpt.c: [KLHook] NoInject - no foreign hook DLLs in the game (stutter fix 2026-10-23); AFTER klog / klh_ini */
#ifdef KLHOOK_TEST
#include "klvalog.c"                                     /* klvalog.c: [Memory] VaLog - other modules' VirtualAlloc by caller (TEST only, default 0); AFTER klextpt.c (klxp_enum_fn) */
#endif
#include "klarena.c"                                     /* klarena.c: [Memory] DriverArena - nvd3dum's small process-heap blocks from 1 MB chunks released when empty (default 0); AFTER klvalog.c */
#ifdef KLHOOK_TEST
#include "kld3.c"                                       /* kld3.c: [Memory] D3dCount / D3dFlushEvery - Direct3D 9 call counts per vtable slot + a GPU flush experiment (TEST only, default 0); AFTER klarena.c, BEFORE klfps.c */
#endif
#include "klquad.c"                                       /* klquad.c: [Memory] QuadRing - a buffer ring for the 4 screen-quad VBs (DM05A driver pile; off unless set); BEFORE klfps.c */
#include "klnudge.c"
#include "klfix.c"
#include "kljoin.c"
#include "klcrew_rt.c"
#include "klgun.c"
#include "klset.c"                                        /* klset.c: the Mod settings rows (answered through klchar.c's option vtable) */
#include "klpm.c"                                         /* klpm.c: private-match options KLMGun / KLMVote / KLMPlay (off unless [Match] Enable); BEFORE klchar.c */
#include "klchar.c"
#include "klcrew.c"
#include "kltalk.c"
#include "klvoice.c"                                       /* klvoice.c: Dead Men voices for the eight Dead Men bodies (off unless [Voice] Enable=1); AFTER kltalk.c (klk_hash, klk_ini) */
#include "klbot.c"
#include "klonline.c"                                       /* klonline.c: klon_read / klon_money, the read-only online snapshot for [Music]/[Ambience]/[Stinger] Online; AFTER klbot.c */
#include "klescort.c"
#include "klhop.c"
#include "klmove.c"
#include "klclimb.c"
#include "klfreeclimb.c"                                 /* klfreeclimb.c: Dead Men's free climb, luvsic's port (off unless [Climb] Enable); AFTER klclimb.c (klq_slot) */
#include "klunstick.c"                                  /* klunstick.c: [Unstick] put a player stuck in cover back to his last free place (default on, offline); AFTER klfreeclimb.c (klfc_guard, klfc_pose) */
#include "klrappel.c"                                    /* klrappel.c: off unless [Rappel] Enable */
#include "klfallrescue.c"                              /* klfallrescue.c: [FallRescue] a player who leaves the level box is put back on his last safe place before the game kills him (default on); AFTER klrappel.c (klrp_r), klclimb.c (klq_r), klfreeclimb.c */
#include "kltrait.c"                                      /* kltrait.c: [Traits] a small trait per wardrobe character (a table + getters; AFTER klcrew.c, BEFORE klbalance.c) */
#include "klbalance.c"
#include "klgrudge.c"
#include "klhud_names.c"                              /* the crew list's character names + initials as tags ([HUD] Names / NameTags) */
#include "klucchide_logic.h"                          /* klucchide_logic.h: [Ucc] Hide - the Undercover Cop's hidden state + pure rules (klucchide.c fills it); BEFORE klhud.c / kllocname.c, which read it */
#include "klonline_read.h"                                /* klonline_read.h/.c: the online round reader ([Online] Read, default 0); AFTER klbot.c / klcrew.c / klchar.c, BEFORE klhud.c */
#include "klonline_read.c"
#include "klhud_values.c"                             /* the HUD's readers (reads only): BEFORE klhud.c, AFTER klbot.c */
#include "klhud.c"                                    /* includes klhud_weapon.c inside itself */
#include "klhud_popup.c"                              /* AFTER klhud.c: pop-ups + loot ring (uses its klu / klu_r / klu_pic) */
#include "klhud_kill.c"                              /* AFTER klhud_popup.c: the kill / reward line under REWARDS (uses klpu_str) */
#include "klhud_escape.c"                             /* AFTER klhud_popup.c: the escape-vehicle panel in the new look (uses klu / klu_r / klu_pic) */
#include "klhud_tracker.c"                           /* AFTER klhud_escape.c: the vehicle marker in the world - smaller, only near ([HUD] Tracker) */
#include "klhud_tags.c"                              /* AFTER klhud_escape.c: the tags over the heisters' heads (uses klu / klu_r / klu_cs / klnm_tag_ini) */
#include "klhud_board.c"                             /* AFTER klhud_tags.c: the pre-round panel in the new look ([HUD] Board, default 0) */
#include "klhud_board2.c"                            /* AFTER klhud_board.c: the round-over scoreboard ([HUD] Scoreboard, default 0) */
#include "klshoulder.c"
#include "klcam.c"                                      /* klcam.c: the camera rework ([Camera], default on; Log off) */
#include "klcamsmooth.c"                                 /* klcamsmooth.c: [CamSmooth] pivot / aim-out / dt-correct camera smoothing; AFTER klcam.c */
#include "klanimprobe.c"                               /* klanimprobe.c: [AnimProbe] LOG-ONLY probe of the animation Play 0x4da1d0 around the player's gait change (off unless Enable=1; TEST build only patches); AFTER klcamsmooth.c */
#include "klmfprobe.c"                                  /* klmfprobe.c: [MFProbe] TEST-only log probe of who raises the MissionFailedReload popup; AFTER klanimprobe.c, klescort.c */
#include "klbotdeath.c"                              /* klbotdeath.c: [BotDeathProbe] TEST-only log probe of what kills a team-2 bot online (health writes, hits, death routine); AFTER klmfprobe.c */
#include "klcoverdump.c"                              /* klcoverdump.c: [CoverDump] TEST-only read-only dump of the cover list; AFTER klmfprobe.c */
#include "klheliprobe.c"                                  /* klheliprobe.c: read-only chopper probe ([Heli] Probe, default 0); AFTER klescort.c */
#include "klcensor.c"                                    /* klcensor.c: [Censor] a killing head shot blows the head off (heap data only); AFTER klheliprobe.c */
#include "klcensus.c"                                    /* klcensus.c: [Census] read-only list of every ZFFActor (place, health); AFTER klcensor.c */
#include "klclubcalm.c"                                  /* klclubcalm.c: [ClubCalm] read-only probe of the hand item / shots (off unless Enable=1); AFTER klshoulder.c */
#include "klclubholster.c"                                /* klclubholster.c: [ClubHolster] Last Call starts holstered, the crowd panics when you draw (off unless Enable=1, Dry=1 default); AFTER klclubcalm.c */
#include "klvis.c"
#include "kltex.c"                                        /* kltex.c: [Graphics] Textures - anisotropic filtering (default on) */
#include "klfps.c"                                        /* klfps.c: [FrameLimit] RTSS-style frame limiter on the device's Present (default on) */
#include "klnet.c"
#include "klnetfix.c"
#include "klnetload.c"                                   /* klnetload.c: [NetLoad] Probe / ScaleSend - load probe and sender-rate scaling for bigger lobbies (off unless set); AFTER klnet.c */
#include "kllobby.c"                                      /* kllobby.c: [Lobby] MinPlayers - a hosted FA lobby may start below 4 (off unless set) */
#include "kllobbyopt.c"                                   /* kllobbyopt.c: [Lobby] TimeMax / TimeMin / RoundsMax - more choices on the FA lobby rows (off unless set); AFTER kllobby.c */
#include "klbotfill.c"                                    /* klbotfill.c: [Bots] OnlineFill plan + probe, read-only (off unless set); AFTER kllobby.c */
#include "klcopsquad.c"                                   /* klcopsquad.c: [CopSquad] AI police under each human cop in Cops and Robbers (off unless Enable=1); AFTER klbotfill.c, klescort.c */
#include "klsabotage.c"                                   /* klsabotage.c: [Sabotage] VanHold - the hosting UCC holds the escape van N s (off unless VanHold=1); AFTER klnet.c (KLNET_SESSION) */
#include "klroundkeep.c"                                  /* klroundkeep.c: [Lobby] KeepRound + TEST round-end probe (the online rules' early cuts); AFTER klbotfill.c, kllobbyopt.c */
#include "klqol.c"                                        /* klqol.c: [QoL] taskbar flash, background frame cap, mouse-clip release (off unless set); AFTER kllobby.c / klnet.c */
#include "klinv.c"
#include "klgrenade.c"                                     /* klgrenade.c: [Grenade] Probe - log-only grenade probe (off unless Probe=1) */
#include "klrigid.c"                                       /* klrigid.c: [Rigid] heavier mouse turn + remote shaping helpers (off unless Enable=1) */
#include "klaiturn.c"                                      /* klaiturn.c: [Rigid] AiTurnDps - one .data float caps every AI actor's body turn rate (off unless set) */
#include "klnetsmooth.c"
#include "klucc_down.c"                                   /* klucc_down.c: [Ucc] DownOnly - a hidden UCC's hits only down a heister (off unless set); AFTER klroundkeep.c, klnetsmooth.c */
#include "klmusic.c"                                      /* klmusic.c: [Music] a winmm MCI jukebox for the FA round (off unless Enable=1); AFTER klmove.c / klbot.c */
#include "klambience.c"                                  /* klambience.c: [Ambience] a looping bed + timed one-shots (radio, alarm, heli, distant) over winmm MCI (off unless Enable=1); AFTER klmusic.c */
#include "klshop.c"
#include "klshoppage.c"                           /* AFTER klshop.c: [ShopPage] page II of the weapon shop (key flips set A / B) */
#include "klfed.c"
#include "klfedkit.c"
#include "kldown.c"
#include "klbotdown.c"                                    /* klbotdown.c: AI heisters down, not dead (off unless [BotDown] Enable) */
#include "klcardown.c"                                   /* klcardown.c: a car blast floors the AI and you, revivable ([CarDown], on in Arcade on non-stock levels) */
#include "klshield.c"                                    /* klshield.c: the human shield covers you and floors the hostage ([Shield], on in Arcade rounds) */
#include "klcdying.c"                                   /* klcdying.c: almost dead = the revivable floor for you; heisters hold fire ([Dying]); AFTER klcardown.c */
#include "kladren.c"                                      /* kladren.c: adrenaline (off unless [Adrenaline] Enable); its tick runs BEFORE kld_tick */
#include "klstinger.c"                                  /* klstinger.c: [Stinger] event-driven one-shot cues over winmm MCI (off unless Enable=1); AFTER kladren.c / klbotdown.c / kldown.c */
#include "klreshade.c"                                    /* klreshade.c: the ReShade bridge - live looks from the menu, KL_* uniforms (off unless [ReShade] Bridge=1) */
#include "klsteam.c"
#include "klmm.c"                                          /* klmm.c: [Net] PrivateLobby / BuildKey - an ISteamMatchmaking proxy, only when a key is set */
#include "klslot.c"
#include "klserver.c"                                    /* klserver.c: [Server] host a Quick Match / Ranked lobby unattended (off unless Enable=1); AFTER klslot.c / klchar.c / kllobby.c */
#include "kllocname.c"                                    /* kllocname.c: [Names] an expansion map shows its own name in the FA lobby / lists (off unless Enable=1); AFTER klslot.c / klpm.c */
#include "klpm_gun.c"                                      /* klpm_gun.c: KLMGun equips the round-start gun (off unless [Match] Enable)  */
#include "klpm_arc.c"                                      /* klpm_arc.c: the Arcade playlist (off unless [Match] Enable + Arcade); AFTER klslot.c */
#include "klqol2.c"                                        /* klqol2.c: [QoL2] stuck-AI watchdog, Heister page key, mute when unfocused (off unless set); AFTER klslot.c / klpm_arc.c */
#include "klhostopt.c"                                    /* klhostopt.c: [HostOpts] host-controlled match options (off unless Enable=1); AFTER klslot.c / klbotfill.c / kllobby.c / klmm.c */
#include "klcharonline.c"                               /* klcharonline.c: [CharOnline] every player's heister/mask/outfit on every peer (off unless Enable=1); AFTER klchar.c / klmm.c / klslot.c */
#include "klsync.c"                                    /* klsync.c: [Sync] read-only probe + host list compare of actors / world objects per peer (off unless set); AFTER klcensus.c, klcharonline.c */
#include "klnetchan.c"                                 /* klnetchan.c: [NetChan] the hook's shared peer message channel (UDP 27416 + Steam member data; idle unless a module wants it); AFTER klmm.c, klslot.c */
#include "klucc.c"                                     /* klucc.c: [Ucc] Undercover Cop suspicion pings / accuse key (off unless Pings=1 or Accuse=1); AFTER klnetchan.c, klcharonline.c, klhud_popup.c */
#include "klucchide.c"                                 /* klucchide.c: [Ucc] Hide - the UCC stays hidden until his reveal key (off unless Hide=1); AFTER klucc.c, klucc_down.c, klnetchan.c, klroundkeep.c, klcharonline.c, klhud.c */
#include "klucc_aim.c"                                 /* klucc_aim.c: [Ucc] PoliceAim - police AI treats a hidden UCC as a target, rules slot 188 per asker (off unless PoliceAim=1); AFTER klucchide.c, klucc_down.c, klroundkeep.c */
#ifdef KLHOOK_TEST
#include "klauto.c"
#include "klsolo.c"                                       /* klsolo.c: [Solo] two kl2.exe on one PC (mutex, windowed, focus); TEST only, off unless Enable=1 */
#include "klprobe.c"                                      /* klprobe.c: [Probe] DoorProxy - escape-lift door chain log; TEST only, off unless DoorProxy=1 */
#endif

/* ---------------------------------------------------------------- the tick

   Once a frame on the game's own thread (the import slot of SteamAPI_RunCallbacks, called from the main loop
   at kl2 0x87aa7c), else every 100 ms from our own thread. Everything in it is a read or a guarded data
   write and must be cheap. */
static void (__cdecl *klh_real_runcallbacks)(void);
static volatile DWORD klh_tick_last, klh_ticks; static volatile LONG klh_tick_busy, klh_tick_seen;
static int klh_tick_source = -1;

static volatile LONG klh_game_ticks;                  /* frames of the main loop: half of the stall watch's heartbeat */
static DWORD klh_main_tid;                            /* the main loop's thread (its first SteamAPI_RunCallbacks call) */

/* ---------------------------------------------------------------- no UI Automation on the game window (SHIP and TEST)

   WHY (2026-10-14, the hitch probe in the owner's own rounds, 20:25 - 20:44): during nearly every freeze of 50 - 450 ms the main thread
   stood in win32u.dll's message calls with USER32 -> uiautomationcore.dll on its stack (and gameoverlayrenderer.dll / ReShade32.dll's
   window procedures under it): another program on the PC (an accessibility / assistive client: Grammarly, a screen reader, a remote-control
   or 'computer use' tool, Windows' text input host) asks the game's window for its UI Automation tree with WM_GETOBJECT, and answering
   that in the game's own message pump builds an automation provider for a full-screen D3D9 window - over and over.
   WHAT: the game's top-level window gets one more window procedure, outermost: WM_GETOBJECT (0x3D) is answered 0 ('no accessible
   object') at once; every other message goes on to the procedure that was there (CallWindowProc). The window is looked for every 2 s
   until found and again whenever another subclass has gone over ours (a chain is fine). user32 is looked up, not linked.
   [KLHook] NoUIA=1 (0 = the game as before). The 10 s perf line says how many such requests were refused. */
static LONG_PTR klh_uia_old; static HWND klh_uia_wnd; static volatile LONG klh_uia_n;
static int klh_nouia = 1;                              /* [KLHook] NoUIA; the subclass is also kept for FastExit */
static LRESULT (WINAPI *klh_cwp)(WNDPROC, HWND, UINT, WPARAM, LPARAM);
static LONG_PTR (WINAPI *klh_gwl)(HWND, int); static LONG_PTR (WINAPI *klh_swl)(HWND, int, LONG_PTR);
static BOOL (WINAPI *klh_uni)(HWND); static HMODULE klh_u;
/* ---------------------------------------------------------------- [Stall] Trace: where the main thread's message time goes (SHIP and TEST)

   WHY (2026-10-25, owner: 'stutters are there occasionally', DM01 16:43 - 16:48): in that log 22 hitch-probe lines, 10 to 25 of 28 samples a line at
   win32u.dll+0x101c = inside NtUserPeekMessage, return addresses USER32 PeekMessageW/A, USER32+0x43bb0, ntdll KiUserCallbackDispatcher and
   DINPUT8.dll+0x54050. That last one is THIS dll's klh_uia_proc (map of the f8271b2fd build: _klh_uia_proc@16 = 10054050, the outermost window
   procedure we put on the game window). Read: the main thread was inside a Peek that was running a window procedure (a SENT message, delivered to
   the thread from inside PeekMessage through the kernel's user-mode callback), and the procedure chain then stood in another PeekMessage (PeekMessageW
   appears twice per sample). The probe could not say WHICH message, from whom (another thread / process: Medal's medal-hook32.dll is loaded in the game,
   as are the Steam overlay and ReShade) or whether the time is in our procedure, the game's, or a foreign one under it.
   WHAT (diagnostic, no behaviour change; data/import-slot writes only):
     1. klh_uia_proc times every message it passes on (inclusive of everything under it) per message id: count, how many were SENT from another
        thread (InSendMessageEx), total and longest ms; a message of StallMsgMs (default 20) or more is logged at once (40 lines per run) with its
        id, wparam, lparam, nesting depth and whether it was sent.
     2. The game's USER32 PeekMessageA / PeekMessageW import slots are wrapped: calls, total ms, longest ms, calls over 10 ms, and how much of that
        time was spent in top-level window procedures (the rest is the kernel / a hook chain / a foreign in-process hook: 'own').
     3. The hitch probe adds, for each sample, the message stack in flight (id, ms so far) and whether a Peek was running (ms so far): one line per
        sample, 60 lines per run.
     4. Every 10 s with any such time: 'stall: ...' lines (top message ids by total ms, Peek totals).
   [Stall] Trace=1 (0 = nothing wrapped, nothing timed, the game window is not subclassed for this reason), StallMsgMs=20.
   The costs: two QueryPerformanceCounter reads per message and per Peek call (a few per frame). */
#define KLH_ST_N 40
static int klh_st_on = 1, klh_st_msgms = 20, klh_st_lines, klh_st_slines;
static double klh_st_freq;                                    /* ticks per ms */
static BOOL (WINAPI *klh_st_ismex)(LONG);                    /* user32 InSendMessageEx(NULL) -> ISMEX_* flags (looked up, not linked) */
typedef struct { UINT msg; LONG n, nsent; double ms, max; } klh_st_msg_t;
static klh_st_msg_t klh_st_w[KLH_ST_N];
/* n_mm / ms_mm = calls that returned WM_MOUSEMOVE, n_no / ms_no = calls that returned FALSE (queue empty), the rest returned another message */
typedef struct { LONG n, over10, n_mm, n_no, throttled; double ms, wp_ms, max, ms_mm, ms_no; } klh_st_pk_t;
/* [Input] MouseMoveMs (2026-10-25, PEEK lane; default 0 = off, nothing changes): see klh_st_real. */
static int klh_mm_ms; static double klh_mm_last;
static klh_st_pk_t klh_st_pk[2];                              /* 0 = PeekMessageA, 1 = PeekMessageW */
static double klh_st_wp_acc;                                  /* ms in top-level (depth 0) window procedures, running total */
static volatile LONG klh_st_depth;
static volatile struct { UINT msg; WPARAM w; LPARAM l; double t0; LONG sent; } klh_st_stk[8];   /* messages in flight, [depth] */
static volatile double klh_st_peek_t0; static volatile LONG klh_st_peek_n;                       /* a Peek is running since (ms); nesting count */
static BOOL (WINAPI *klh_real_pka)(LPMSG, HWND, UINT, UINT, UINT);
static BOOL (WINAPI *klh_real_pkw)(LPMSG, HWND, UINT, UINT, UINT);

static double klh_st_now(void)
{   /* ms from QueryPerformanceCounter (the frequency is read on first use) */
    LARGE_INTEGER c;
    if (klh_st_freq == 0) { LARGE_INTEGER f; QueryPerformanceFrequency(&f); klh_st_freq = f.QuadPart / 1000.0; if (klh_st_freq <= 0) klh_st_freq = 1; }
    QueryPerformanceCounter(&c);
    return c.QuadPart / klh_st_freq;
}

static const char *klh_st_name(UINT m)
{
    switch (m) {
    case 0x0001: return "CREATE"; case 0x0003: return "MOVE"; case 0x0005: return "SIZE"; case 0x0006: return "ACTIVATE"; case 0x0007: return "SETFOCUS";
    case 0x0008: return "KILLFOCUS"; case 0x000F: return "PAINT"; case 0x0014: return "ERASEBKGND"; case 0x001C: return "ACTIVATEAPP";
    case 0x0020: return "SETCURSOR"; case 0x0024: return "GETMINMAXINFO"; case 0x0046: return "WINDOWPOSCHANGING"; case 0x0047: return "WINDOWPOSCHANGED";
    case 0x0081: return "NCCREATE"; case 0x0083: return "NCCALCSIZE"; case 0x0084: return "NCHITTEST"; case 0x0085: return "NCPAINT"; case 0x0086: return "NCACTIVATE";
    case 0x00FF: return "INPUT"; case 0x0100: return "KEYDOWN"; case 0x0101: return "KEYUP"; case 0x0104: return "SYSKEYDOWN"; case 0x0112: return "SYSCOMMAND";
    case 0x0113: return "TIMER"; case 0x0200: return "MOUSEMOVE"; case 0x0281: return "IME_SETCONTEXT"; case 0x0282: return "IME_NOTIFY";
    case 0x0286: return "IME_CHAR"; case 0x0288: return "IME_REQUEST"; case 0x003D: return "GETOBJECT"; case 0x0219: return "DEVICECHANGE";
    case 0x031A: return "THEMECHANGED"; case 0x031E: return "DWMCOMPOSITIONCHANGED"; case 0x02E0: return "DPICHANGED"; case 0x0018: return "SHOWWINDOW";
    case 0x0021: return "MOUSEACTIVATE"; case 0x0214: return "SIZING"; case 0x0231: return "ENTERSIZEMOVE"; case 0x0232: return "EXITSIZEMOVE";
    case 0x0000: return "NULL"; case 0x004E: return "NOTIFY"; case 0x0319: return "APPCOMMAND";
    default: return m >= 0xC000 ? "registered" : (m >= 0x8000 ? "app" : (m >= 0x400 ? "user" : "-"));
    }
}

static void klh_st_account(UINT m, double ms, int sent)
{
    int i;
    for (i = 0; i < KLH_ST_N; i++) {
        if (klh_st_w[i].n && klh_st_w[i].msg != m) continue;
        if (!klh_st_w[i].n) klh_st_w[i].msg = m;
        klh_st_w[i].n++; if (sent) klh_st_w[i].nsent++;
        klh_st_w[i].ms += ms; if (ms > klh_st_w[i].max) klh_st_w[i].max = ms;
        return;
    }
}

/* the final hop of klh_uia_proc: the window procedure under ours, timed */
static LRESULT klh_st_pass(HWND h, UINT m, WPARAM w, LPARAM l)
{
    LRESULT r; LONG d; double t0, dt; int sent = 0;
    if (!klh_st_on) return klh_cwp((WNDPROC)klh_uia_old, h, m, w, l);
    if (klh_st_ismex) sent = (klh_st_ismex(0) & 1 /* ISMEX_SEND: sent from another thread, its sender waits */) != 0;
    d = klh_st_depth; t0 = klh_st_now();
    if (d >= 0 && d < 8) { klh_st_stk[d].msg = m; klh_st_stk[d].w = w; klh_st_stk[d].l = l; klh_st_stk[d].t0 = t0; klh_st_stk[d].sent = sent; }
    klh_st_depth = d + 1;
    r = klh_cwp((WNDPROC)klh_uia_old, h, m, w, l);
    klh_st_depth = d;
    dt = klh_st_now() - t0;
    if (d == 0) klh_st_wp_acc += dt;
    klh_st_account(m, dt, sent);
    if (dt >= klh_st_msgms && klh_st_lines < 40) {
        klh_st_lines++;
        klog("stall: window message %04x (%s) wparam %08lx lparam %08lx took %.1f ms%s, nesting depth %ld%s", (unsigned)m, klh_st_name(m), (DWORD)w, (DWORD)l, dt,
             sent ? " (SENT from another thread: its sender waited that long)" : "", (long)d, klh_st_lines == 40 ? " (last such line)" : "");
    }
    return r;
}

/* MouseMoveMs=N (N>0): a pump call "any message, remove" (hwnd 0, filter 0..0, PM_REMOVE) hands out WM_MOUSEMOVE at most once every N ms.
   WHY (2026-10-25 17:25 - 17:39 log, DM01): ~0.3 ms of USER32 PeekMessage time for every mouse move the pump retrieves (1.1 s of the main thread per
   10 s at ~190 moves/s; the window procedures take 5 ms of it, the rest is the hook chain run inside the Peek: gameoverlayrenderer.dll+0x992bc,
   ReShade32.dll+0x5fd99 / +0x5ff67 are on the stack of 25 of 26 samples). A WH_GETMESSAGE-type hook runs once per message that Peek RETURNS, so a
   move that is not returned costs the hooks nothing. Inside the window the call is split in two filtered calls (0..0x1FF, then 0x201..0xFFFF) so the
   queued move stays where it is (the kernel keeps one coalesced move; the latest position is delivered after the window). Every other message,
   WM_PAINT / WM_QUIT / WM_TIMER / buttons / wheel / keys, still comes out in the same call. GUESS (not run live): that the hook cost is per returned
   message and not per hit-test inside the kernel; the 10 s line's 'mm' and 'no' columns say what a returned move costs. Unknown: whether the game
   reads WM_MOUSEMOVE at all (it imports GetCursorPos / SetCursorPos; mouse look is probably not message driven); 8 .. 16 ms keeps 60 .. 125 moves/s. */
static BOOL klh_st_real(int which, LPMSG msg, HWND h, UINT a, UINT b, UINT f, int *thr)
{
    BOOL (WINAPI *real)(LPMSG, HWND, UINT, UINT, UINT) = which ? klh_real_pkw : klh_real_pka; BOOL r;
    if (klh_mm_ms > 0 && a == 0 && b == 0 && (f & 1 /* PM_REMOVE */)) {
        double now = klh_st_now();
        if (now - klh_mm_last < (double)klh_mm_ms) {
            *thr = 1;
            r = real(msg, h, 0, 0x1FF, f);
            if (!r) r = real(msg, h, 0x201, 0xFFFF, f);
            return r;
        }
        r = real(msg, h, a, b, f);
        if (r && msg->message == 0x0200) klh_mm_last = now;
        return r;
    }
    return real(msg, h, a, b, f);
}

static BOOL klh_st_peek(int which, LPMSG msg, HWND h, UINT a, UINT b, UINT f)
{
    BOOL r; double t0, dt, wp0; klh_st_pk_t *k = &klh_st_pk[which]; int thr = 0;
    if (!klh_st_on) return klh_st_real(which, msg, h, a, b, f, &thr);
    t0 = klh_st_now(); wp0 = klh_st_wp_acc;
    if (klh_st_peek_n++ == 0) klh_st_peek_t0 = t0;
    r = klh_st_real(which, msg, h, a, b, f, &thr);
    if (--klh_st_peek_n < 0) klh_st_peek_n = 0;
    dt = klh_st_now() - t0;
    k->n++; k->ms += dt; k->wp_ms += klh_st_wp_acc - wp0; if (dt > k->max) k->max = dt; if (dt >= 10) k->over10++;
    if (thr) k->throttled++;
    if (!r) { k->n_no++; k->ms_no += dt; } else if (msg->message == 0x0200) { k->n_mm++; k->ms_mm += dt; }
    return r;
}
static BOOL WINAPI klh_w_pka(LPMSG msg, HWND h, UINT a, UINT b, UINT f) { return klh_st_peek(0, msg, h, a, b, f); }
static BOOL WINAPI klh_w_pkw(LPMSG msg, HWND h, UINT a, UINT b, UINT f) { return klh_st_peek(1, msg, h, a, b, f); }

static void klh_st_init(void)
{   /* DllMain: read the switch, wrap the game's Peek imports */
    klh_st_on = GetPrivateProfileIntA("Stall", "Trace", 1, klh_ini) != 0;
    klh_st_msgms = GetPrivateProfileIntA("Stall", "StallMsgMs", 20, klh_ini);
    if (klh_st_msgms < 1) klh_st_msgms = 1;
    klh_mm_ms = GetPrivateProfileIntA("Input", "MouseMoveMs", 0, klh_ini);
    if (klh_mm_ms < 0) klh_mm_ms = 0; if (klh_mm_ms > 100) klh_mm_ms = 100;
    if (!klh_st_on) klog("stall: trace off ([Stall] Trace=0)");
    if (!klh_st_on && !klh_mm_ms) return;
    {
        int a = klh_iat("USER32.dll", "PeekMessageA", (void *)klh_w_pka, (void **)&klh_real_pka);
        int w = klh_iat("USER32.dll", "PeekMessageW", (void *)klh_w_pkw, (void **)&klh_real_pkw);
        if (klh_mm_ms) klog("input: MouseMoveMs=%d: the game's pump gets WM_MOUSEMOVE at most once every %d ms (PeekMessageA %s, W %s wrapped); 0 = off", klh_mm_ms, klh_mm_ms, a ? "yes" : "no", w ? "yes" : "no");
        if (!klh_st_on) return;
        HMODULE u = GetModuleHandleA("user32.dll");
        if (u) klh_st_ismex = (BOOL (WINAPI *)(LONG))GetProcAddress(u, "InSendMessageEx");
        klh_st_now();
        klog("stall: trace on: PeekMessageA %s, PeekMessageW %s wrapped; InSendMessageEx %s; messages of %d ms or more are logged ([Stall] Trace=0 = off)",
             a ? "yes" : "no", w ? "yes" : "no", klh_st_ismex ? "found" : "missing", klh_st_msgms);
    }
}

/* the hitch probe calls this after a sample (the main thread has been resumed); one line, 60 per run */
static void klh_st_sample(void)
{
    char line[600]; size_t at; int i; double now;
    if (!klh_st_on || klh_st_slines >= 60) return;
    klh_st_slines++; now = klh_st_now();
    at = (size_t)snprintf(line, sizeof line, "stall sample: PeekMessage %s", klh_st_peek_n > 0 ? "RUNNING" : "not running");
    if (klh_st_peek_n > 0) at += (size_t)snprintf(line + at, sizeof line - at, " for %.0f ms (nest %ld)", now - klh_st_peek_t0, (long)klh_st_peek_n);
    at += (size_t)snprintf(line + at, sizeof line - at, "; window procedure depth %ld", (long)klh_st_depth);
    for (i = 0; i < klh_st_depth && i < 8 && at < sizeof line - 120; i++)
        at += (size_t)snprintf(line + at, sizeof line - at, " [%d: %04x %s%s for %.0f ms]", i, (unsigned)klh_st_stk[i].msg, klh_st_name(klh_st_stk[i].msg),
                               klh_st_stk[i].sent ? " SENT" : "", now - klh_st_stk[i].t0);
    if (klh_st_slines == 60) snprintf(line + at, sizeof line - at, " (last such line)");
    klog("%s", line);
}

/* every 10 s (called from the probe thread's loop): the deltas since the last call, top message ids by total ms, Peek totals */
static void klh_st_say(void)
{
    static klh_st_msg_t prev[KLH_ST_N]; static klh_st_pk_t pprev[2];
    klh_st_msg_t cur[KLH_ST_N], d[KLH_ST_N]; klh_st_pk_t pk[2]; int i, j, k, shown = 0; char line[900]; size_t at; double tot = 0;
    if (!klh_st_on) return;
    memcpy(cur, klh_st_w, sizeof cur); memcpy(pk, klh_st_pk, sizeof pk);
    for (i = 0; i < KLH_ST_N; i++) {
        d[i] = cur[i];
        for (j = 0; j < KLH_ST_N; j++) if (prev[j].n && prev[j].msg == cur[i].msg) { d[i].n -= prev[j].n; d[i].nsent -= prev[j].nsent; d[i].ms -= prev[j].ms; break; }
        if (d[i].n > 0) tot += d[i].ms;
    }
    at = (size_t)snprintf(line, sizeof line, "stall: 10 s window procedures: %.1f ms in all;", tot);
    for (k = 0; k < 6; k++) {
        int best = -1;
        for (i = 0; i < KLH_ST_N; i++) if (d[i].n > 0 && (best < 0 || d[i].ms > d[best].ms)) best = i;
        if (best < 0) break;
        if (d[best].ms < 0.05 && k) break;
        at += (size_t)snprintf(line + at, sizeof line - at, " %04x %s x%ld (sent %ld) %.1f ms (longest ever %.1f);", (unsigned)d[best].msg, klh_st_name(d[best].msg),
                               (long)d[best].n, (long)d[best].nsent, d[best].ms, cur[best].max);
        d[best].n = 0; shown++;
    }
    memcpy(prev, cur, sizeof prev);
    {
        klh_st_pk_t a = pk[0], w = pk[1];
        a.n -= pprev[0].n; a.ms -= pprev[0].ms; a.wp_ms -= pprev[0].wp_ms; a.over10 -= pprev[0].over10;
        a.n_mm -= pprev[0].n_mm; a.ms_mm -= pprev[0].ms_mm; a.n_no -= pprev[0].n_no; a.ms_no -= pprev[0].ms_no; a.throttled -= pprev[0].throttled;
        w.n -= pprev[1].n; w.ms -= pprev[1].ms; w.wp_ms -= pprev[1].wp_ms; w.over10 -= pprev[1].over10;
        if (a.n || w.n || shown) {
            klog("%s", line);
            klog("stall: 10 s PeekMessage: A %ld calls %.1f ms (in window procs %.1f, own %.1f; %ld over 10 ms; longest ever %.1f) | W %ld calls %.1f ms (in window procs %.1f, own %.1f; %ld over 10 ms; longest ever %.1f)",
                 (long)a.n, a.ms, a.wp_ms, a.ms - a.wp_ms, (long)a.over10, pk[0].max, (long)w.n, w.ms, w.wp_ms, w.ms - w.wp_ms, (long)w.over10, pk[1].max);
            if (a.n) klog("stall: 10 s PeekMessageA by result: WM_MOUSEMOVE %ld calls %.1f ms (%.3f ms each) | empty %ld calls %.1f ms | other messages %ld calls %.1f ms | MouseMoveMs=%d throttled %ld calls",
                 (long)a.n_mm, a.ms_mm, a.n_mm ? a.ms_mm / a.n_mm : 0.0, (long)a.n_no, a.ms_no, (long)(a.n - a.n_mm - a.n_no), a.ms - a.ms_mm - a.ms_no, klh_mm_ms, (long)a.throttled);
        }
        pprev[0] = pk[0]; pprev[1] = pk[1];
    }
}

static void klh_msg_trace(UINT m, WPARAM w)
{   /* k43 ExitTrace: each close-type message once per run, with a timestamp. WM_QUIT is posted to the thread queue and never reaches a window procedure,
       so it cannot be seen here (GUESS: the exit() caller line of klh_exit_trace is the next best); SC_CLOSE is WM_SYSCOMMAND with 0xF060. */
    static LONG seen; int bit; const char *nm;
    if (!klh_exittrace) return;
    if (m == 0x0010) { bit = 1; nm = "WM_CLOSE"; } else if (m == 0x0002) { bit = 2; nm = "WM_DESTROY"; } else if (m == 0x0011) { bit = 4; nm = "WM_QUERYENDSESSION"; }
    else if (m == 0x0016) { bit = 8; nm = "WM_ENDSESSION"; } else if (m == 0x0112 && (w & 0xFFF0) == 0xF060) { bit = 16; nm = "SC_CLOSE"; }
    else if (m == 0x0012) { bit = 32; nm = "WM_QUIT"; } else return;
    if (InterlockedOr(&seen, bit) & bit) return;
    klog("exit trace: window message %s (%04x, wparam %08lx) at tick %lu", nm, (unsigned)m, (DWORD)w, GetTickCount());
}
static LRESULT CALLBACK klh_uia_proc(HWND h, UINT m, WPARAM w, LPARAM l)
{
    if (m < 0x20 || m == 0x0112) klh_msg_trace(m, w);
    if (m == 0x003D && klh_nouia) { InterlockedIncrement(&klh_uia_n); return 0; }
    if (klh_fastexit && (m == 0x0010 /* WM_CLOSE */ || (m == 0x0112 && (w & 0xFFF0) == 0xF060 /* WM_SYSCOMMAND SC_CLOSE */) ||
                         (m == 0x0104 && w == 0x73 /* WM_SYSKEYDOWN VK_F4 */ && (l & (1 << 29)) /* Alt held */))) {
        klog("exit: Alt+F4 / close (msg %04x): the process is ended at once", (unsigned)m);
        TerminateProcess(GetCurrentProcess(), 0);
    }
    return klh_st_pass(h, m, w, l);                    /* [Stall] Trace: the same CallWindowProc, timed */
}
static BOOL CALLBACK klh_uia_pick(HWND h, LPARAM best)
{
    static BOOL (WINAPI *vis)(HWND); static BOOL (WINAPI *rect)(HWND, LPRECT); RECT r; HWND *b = (HWND *)best;
    if (!vis) { HMODULE u = GetModuleHandleA("user32.dll"); vis = (BOOL (WINAPI *)(HWND))GetProcAddress(u, "IsWindowVisible"); rect = (BOOL (WINAPI *)(HWND, LPRECT))GetProcAddress(u, "GetClientRect"); }
    if (vis && rect && vis(h) && rect(h, &r) && r.right - r.left >= 640 && r.bottom - r.top >= 400) { *b = h; return FALSE; }
    return TRUE;
}
static void klh_fgname(HWND f, DWORD *pid, char *title, int cap)
{   /* the window's pid and title; user32 is looked up, not linked */
    static DWORD (WINAPI *wtp)(HWND, LPDWORD); static int (WINAPI *gwt)(HWND, LPSTR, int); static int looked;
    if (!looked) { HMODULE u = GetModuleHandleA("user32.dll"); looked = 1; if (u) { wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId"); gwt = (int (WINAPI *)(HWND, LPSTR, int))GetProcAddress(u, "GetWindowTextA"); } }
    *pid = 0; title[0] = 0;
    if (!f) return;
    if (wtp) wtp(f, pid);
    if (*pid == GetCurrentProcessId()) return;               /* our own window: GetWindowText would SEND WM_GETTEXT, which blocks if the game thread hangs */
    if (gwt) { gwt(f, title, cap); title[cap - 1] = 0; }    /* another process's window: read from the window's own record, no message sent */
}
static void klh_exit_trace(const char *what, int code, void *ra)
{
    static HWND (WINAPI *fgw)(void); static BOOL (WINAPI *isw)(HWND); static int looked; HWND f; DWORD pid, off = 0; char title[96], mod[80];
    if (!klh_exittrace) return;
    if (!looked) { HMODULE u = GetModuleHandleA("user32.dll"); looked = 1; if (u) { fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); isw = (BOOL (WINAPI *)(HWND))GetProcAddress(u, "IsWindow"); } }
    f = fgw ? fgw() : 0; klh_fgname(f, &pid, title, sizeof title);
    klh_module((DWORD_PTR)ra, mod, sizeof mod, &off);
    klog("exit trace: %s(%d) called from %p (%s+0x%lx); foreground window %p pid %lu%s title '%s'; game window %p exists %d; tick %lu", what, code, ra, mod, off, (void *)f, pid,
         pid == GetCurrentProcessId() ? " (the game)" : "", title, (void *)klh_uia_wnd, (klh_uia_wnd && isw) ? (int)isw(klh_uia_wnd) : -1, GetTickCount());
}
static void klh_fg_watch(void)
{   /* k43 ExitTrace: while another window has the focus, who has it - at most every 5 s, 20 lines per run (the 10-24 21:30 exit followed a focus loss) */
    static HWND (WINAPI *fgw)(void); static int looked, lines; static DWORD last; DWORD now = GetTickCount(), pid; char title[96]; HWND f;
    if (!klh_exittrace || lines >= 20 || now - last < 5000) return;
    if (!looked) { HMODULE u = GetModuleHandleA("user32.dll"); looked = 1; if (u) fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); }
    if (!fgw) return;
    last = now;                                               /* the 5 s throttle holds while the game is in front too (one query per 5 s, not per tick) */
    if (!(f = fgw())) return;                                 /* no foreground window (switching): not worth one of the 20 lines */
    klh_fgname(f, &pid, title, sizeof title);
    if (pid == GetCurrentProcessId()) return;                 /* the game has the focus: nothing to say */
    lines++;
    klog("exit trace: the game is not in the foreground: window %p pid %lu title '%s'%s", (void *)f, pid, title, lines == 20 ? " (last such line)" : "");
}
static void klh_uia_tick(void)
{
    klh_fg_watch();
    static DWORD last; static int on = -1, told; static BOOL (WINAPI *etw)(DWORD, WNDENUMPROC, LPARAM); DWORD now = GetTickCount(); HWND w = 0;
    if (on < 0) {
        HMODULE u = GetModuleHandleA("user32.dll");
        klh_nouia = GetPrivateProfileIntA("KLHook", "NoUIA", 1, klh_ini) != 0;
        klh_exittrace = GetPrivateProfileIntA("Log", "ExitTrace", 1, klh_ini) != 0;
        on = klh_nouia || klh_fastexit || klh_exittrace || klh_st_on;
        if (u) { etw = (BOOL (WINAPI *)(DWORD, WNDENUMPROC, LPARAM))GetProcAddress(u, "EnumThreadWindows"); klh_uni = (BOOL (WINAPI *)(HWND))GetProcAddress(u, "IsWindowUnicode"); klh_u = u; }
        if (on && (!etw || !klh_uni)) { on = 0; klog("noUIA: user32's window functions not found: the game window answers UI Automation as before"); }
    }
    if (!on || !klh_main_tid || now - last < 2000) return;
    last = now;
    if (klh_uia_wnd && klh_gwl && klh_gwl(klh_uia_wnd, -4) == (LONG_PTR)klh_uia_proc) return;      /* GWL_WNDPROC: ours is still outermost */
    etw(klh_main_tid, klh_uia_pick, (LPARAM)&w);
    if (!w) return;
    {   /* the A or W pair as the window is (a W window subclassed through the A functions would get every text message converted) */
        int wide = klh_uni(w) ? 1 : 0;
        klh_cwp = (LRESULT (WINAPI *)(WNDPROC, HWND, UINT, WPARAM, LPARAM))GetProcAddress(klh_u, wide ? "CallWindowProcW" : "CallWindowProcA");
        klh_gwl = (LONG_PTR (WINAPI *)(HWND, int))GetProcAddress(klh_u, wide ? "GetWindowLongW" : "GetWindowLongA");
        klh_swl = (LONG_PTR (WINAPI *)(HWND, int, LONG_PTR))GetProcAddress(klh_u, wide ? "SetWindowLongW" : "SetWindowLongA");
        if (!klh_cwp || !klh_gwl || !klh_swl) return;
    }
    {
        LONG_PTR cur = klh_gwl(w, -4);
        if (!cur || cur == (LONG_PTR)klh_uia_proc) return;
        klh_uia_old = cur;
        if (klh_swl(w, -4, (LONG_PTR)klh_uia_proc)) { klh_uia_wnd = w; if (told++ < 4) klog("noUIA: the game window %p now refuses WM_GETOBJECT (UI Automation) at once; the procedure under it was %08lx", (void *)w, (DWORD)cur); }
    }
}

/* ---------------------------------------------------------------- Alt+F4 key watch (FastExit's second road)

   WHY (2026-10-24, the owner's 12:15 - 12:29 session): Alt+F4 did not end the game. The log's last line is 'qol: game left the foreground'
   at 12:29:12 with no 'exit:' line: the WM_SYSKEYDOWN never reached the subclassed window (the window lost focus when Alt went down, or the
   main thread stood in a 721 ms scene-load hitch and never pumped it). WHAT: a thread of its own, every 15 ms, reads the keyboard's state
   (GetAsyncKeyState) and ends the process when Alt and F4 are both down and either the game owns the foreground window or Alt went down
   while it did. It does not wait for the game's message pump, so a stalled main thread still dies. GUESS: GetAsyncKeyState sees the keys
   while the game holds DirectInput's keyboard exclusively (it reads the system's key state, not the window's queue). Off with FastExit=0. */
static DWORD WINAPI klh_keywatch(LPVOID unused)
{
    HMODULE u = GetModuleHandleA("user32.dll"); int alt_game = 0;
    SHORT (WINAPI *gaks)(int); HWND (WINAPI *fg)(void); DWORD (WINAPI *wtp)(HWND, LPDWORD);
    (void)unused;
    if (!u) u = LoadLibraryA("user32.dll");
    gaks = u ? (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState") : 0;
    fg = u ? (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow") : 0;
    wtp = u ? (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId") : 0;
    if (!gaks || !fg || !wtp) { klog("exit: key watch off: user32's key functions not found"); return 0; }
    klog("exit: key watch on: Alt+F4 ends the process even when the window misses the key");
    for (;;) {
        DWORD pid = 0; HWND f; int alt, front;
        Sleep(15);
        alt = (gaks(0x12 /* VK_MENU */) & 0x8000) != 0;
        if (!alt) { alt_game = 0; continue; }
        f = fg(); if (f) wtp(f, &pid);
        front = f && pid == GetCurrentProcessId();
        if (front) alt_game = 1;
        if ((front || alt_game) && (gaks(0x73 /* VK_F4 */) & 0x8000)) {
            klog("exit: Alt+F4 seen by the key watch (game in front: %d): the process is ended at once", front);
            TerminateProcess(GetCurrentProcess(), 0);
        }
    }
}

static void klh_tick(int game_thread)
{
    DWORD now = GetTickCount(); static DWORD armed;
    if (game_thread) { InterlockedIncrement(&klh_game_ticks); if (!klh_main_tid) klh_main_tid = GetCurrentThreadId(); }
    if (InterlockedExchange(&klh_tick_busy, 1)) return;
    if (game_thread) { klh_tick_last = now; klh_tick_seen = 1; }
    if (klh_tick_source != game_thread) {             /* changes at every scene load (the main loop stands still): said six times */
        static int told;
        klh_tick_source = game_thread;
        if (told++ < 6) klog("tick: driven by %s", game_thread ? "the game's main loop (SteamAPI_RunCallbacks)" : "the fallback thread (no SteamAPI_RunCallbacks call for 500 ms)");
    }
    klh_ticks++;
    if (now - armed >= 1000) { armed = now; klh_uef_arm(); }
    if (game_thread) klh_uia_tick();                  /* the game window refuses UI Automation (the hitch probe's finding, 2026-10-14) */
    klf_tick();
    kls_tick();
    kllnm_tick(game_thread);                          /* kllocname.c: the LOC lookup wrapper (off unless [Names] Enable=1; game thread only) */
    kpm_gun_tick();                                   /* klpm_gun.c: starting gun (off unless [Match] Enable=1 and KLMGun > 0) */
    kpm_arc_tick();                                   /* klpm_arc.c: next Arcade map after a match (off unless [Match] Enable=1) */
    klx_tick();
    klj_tick();
    klt_tick(game_thread);                            /* DIRECTLY after klj_tick: it must see kljoin.c's request while it is pending (klcrew_rt.c, EARLY) */
    klv_tick(game_thread);                            /* klhop.c: an AI heister that stands at a [CrewHop] place is put beyond it (one game call a tick) */
    kus_tick(game_thread);                            /* klunstick.c: stuck in cover -> back to the last free place (default ON; offline only) */
    klfr_tick(game_thread);                           /* klfallrescue.c: left the level box / fell -> back to the last safe place (default ON) */
    klfc_tick(game_thread);                           /* klfreeclimb.c: W + E at a ledge (OFF unless [Climb] Enable=1; gameplay call only) */
    klq_tick(game_thread);                            /* klclimb.c: the player at the foot of a KLJoin.ini [Climb] edge climbs it (OFF unless [EdgeClimb] Enable=1) */
    klrp_tick(game_thread);                           /* klrappel.c: the descent of the rappel cut */
    klc_tick(game_thread);
    klw_tick(game_thread);                            /* after klc_tick: the player's own body goes first */
    klk_tick(game_thread);                            /* after klw_tick: it reads who wears whom */
    kvo_tick(game_thread);                            /* klvoice.c: after klk_tick (OFF unless [Voice] Enable=1; data writes only) */
    kltt_tick(game_thread);                            /* kltrait.c: record -> character -> trait factors (reads only; off unless [Traits] Enable=1) */
    klb_tick(game_thread);
    kle_tick(game_thread);                            /* klescort.c: after klb_tick; one game call per order, game thread only */
    klmv_tick(game_thread);                           /* klmove.c: Restless / WaitForYou / BoardNear (all off unless set) */
    klr_tick(game_thread);                            /* klbalance.c: one damage scale for player, police and crew */
    klnm_tick(game_thread);
    kly_tick(game_thread);                            /* klgrudge.c: the crew answers your bullets (off unless [Bots] Grudge) */
    klu_tick(game_thread);                            /* klhud.c: the crew list / money box texts (game thread only) */
    klesc_tick(game_thread);                          /* klhud_escape.c: the escape-vehicle panel (off unless [HUD] Escape / Draft) */
    kltrk_tick(game_thread);                          /* klhud_tracker.c: the vehicle marker */
    klbrd_tick(game_thread);                          /* klhud_board.c: the pre-round panel (off unless [HUD] Board=1) */
    klsb_tick(game_thread);                           /* klhud_board2.c: the round-over scoreboard (off unless [HUD] Scoreboard=1) */
    klkf_tick(game_thread);                           /* klhud_kill.c: the kill / reward line under REWARDS (off unless [HUD] KillLine / Draft) */
    klpu_tick(game_thread);                           /* klhud_popup.c: centre pop-ups + loot ring (after klu_tick; off unless [HUD] Popups / LootRing / Draft) */
    klo_tick(game_thread);                            /* klshoulder.c: log only */
    klcam_tick(game_thread);                          /* klcam.c: the camera rework (game thread, gameplay site only) */
    klcamsmooth_tick(game_thread);                    /* klcamsmooth.c: [CamSmooth] after klcam_tick, same site */
    klap_tick(game_thread);                           /* klanimprobe.c: [AnimProbe] gait-change watch (returns at once unless Enable=1) */
    klhp_tick(game_thread);                           /* klheliprobe.c: read-only chopper probe (returns at once unless [Heli] Probe) */
    klcn_tick(game_thread);                           /* klcensor.c: pre-arm the head-hit sum so a killing head shot censors */
    klcs_tick(game_thread);                           /* klcensus.c: read-only actor list (returns at once unless [Census] Enable) */
    klbdp_tick(game_thread);                           /* klbotdeath.c: [BotDeathProbe] 250 ms bot health samples (returns at once unless Enable) */
    kcvd_tick(game_thread);                           /* klcoverdump.c: [CoverDump] cover list dump (returns at once unless Enable) */
    klcc_tick(game_thread);                           /* klclubcalm.c: read-only hand / shot log (returns at once unless [ClubCalm] Enable) */
    klch_tick(game_thread);                           /* klclubholster.c: holster at the Last Call start, unlock at the loot, panic on the draw */
    klvis_tick();                                  /* klvis.c: log only (the vision grid and its record 0xff) */
    klnet_tick(game_thread);                          /* klnet.c: multiplayer log / update numbers (off unless [Net]) */
    klq2_tick(game_thread);                           /* klqol.c: [QoL] (off unless set) */
    kqb_tick(game_thread);                            /* klqol2.c: [QoL2] (off unless set) */
    klsv_tick(game_thread);                           /* klserver.c: [Server] (off unless Enable=1; game thread only) */
    kllb_tick();                                      /* kllobby.c: [Lobby] MinPlayers (off unless set) */
    klho_tick(game_thread);                           /* klhostopt.c: [HostOpts] (off unless Enable=1) */
    klco_tick(game_thread);                           /* klcharonline.c: [CharOnline] (off unless Enable=1) */
    klsy_tick(game_thread);                           /* klsync.c: [Sync] probe / host list (off unless set) */
    knc_tick(game_thread);                            /* klnetchan.c: the shared message channel (idle unless a module wants it) */
    kluc_tick(game_thread);                           /* klucc.c: [Ucc] suspicion messages (off unless Pings=1 or Accuse=1) */
    kllo_tick();                                      /* kllobbyopt.c: [Lobby] TimeMax / TimeMin / RoundsMax (off unless set) */
    klbf_tick(game_thread);                           /* klbotfill.c: [Bots] OnlineFill plan + probe (off unless set) */
    klcq_tick(game_thread);                           /* klcopsquad.c: [CopSquad] (off unless Enable=1; host, C&R, game thread only) */
    klsab_tick(game_thread);                          /* klsabotage.c: [Sabotage] VanHold (off unless VanHold=1; host, UCC rounds, game thread only) */
    klnetfix_tick(game_thread);                       /* klnetfix.c: [Net] Hold* receiver hold times (off unless set) */
    knl_tick(game_thread);                            /* klnetload.c: [NetLoad] (off unless set) */
    klinv_tick(game_thread);                          /* klinv.c: [Inv] gun shelf, Arcade only (off unless Enable=1) */
    klgrenade_tick(game_thread);                      /* klgrenade.c: [Grenade] Probe, log only (off unless Probe=1) */
    klmu_tick(game_thread);                           /* klmusic.c: the jukebox cue (reads only; off unless [Music] Enable=1) */
    klam_tick(game_thread);                           /* klambience.c: the ambience bed + one-shots (reads only; off unless [Ambience] Enable=1) */
    klst_tick(game_thread);                           /* klstinger.c: event stingers (reads only; off unless [Stinger] Enable=1) */
    klnetsmooth_tick(game_thread);                    /* klnetsmooth.c: [NetSmooth] remote players turn smoothly (off unless Enable=1) */
    klud_tick(game_thread);                           /* klucc_down.c: [Ucc] DownOnly (off unless set; game thread only) */
    klucc_tick(game_thread);                          /* klucchide.c: [Ucc] Hide (off unless set; game thread only); AFTER klud_tick and kllo_tick (their rules vtable copies go first) */
    klua_tick(game_thread);                           /* klucc_aim.c: [Ucc] PoliceAim (off unless set; game thread only); AFTER klucc_tick (patches slot 188 into whichever private rules vtable exists) */
    klrigid_tick(game_thread);                        /* klrigid.c: [Rigid] 10 s summary line (Log=1) */
    klshoppage_tick(game_thread);                     /* klshoppage.c: page II of the weapon shop (off unless [ShopPage] Enable=1) */
    klshop_tick(game_thread);                         /* klshop.c: [Shop] Swap= a shop row hands over another gun, Arcade only (off unless Enable=1) */
    klp_tick(game_thread);                            /* klfed.c: come back as a fed (data writes only) */
    klfk_tick(game_thread);                           /* klfedkit.c: the fed can hunt, body, AK (with [Fed] Player=1; Kit=0 = off) */
    klbd_tick(game_thread);                           /* klbotdown.c: before kladren, which reads its down state */
    klcd_tick(game_thread);                           /* klcardown.c: a car blast floors the AI and you */
    klsh_tick(game_thread);                           /* klshield.c: the human shield covers you, the hostage goes down */
    kldy_tick(game_thread);                           /* klcdying.c: almost dead = the game's revivable down (you) */
    kad_tick(game_thread);                            /* kladren.c: raises the mash meter first */
    kld_tick(game_thread);                            /* kldown.c: the mash get-up (off unless [Down] Enable) */
    klrs_tick(game_thread);                           /* klreshade.c: the numbers the shaders get (reads only; off unless [ReShade] Bridge=1) */
    kset_tick(game_thread);                           /* klset.c: the menu manager's table count, a log line (reads only; off unless [Menu] TableLog=1) */
#ifdef KLHOOK_TEST
    klso_tick(game_thread);                           /* klsolo.c: keeps an unfocused window running (off unless [Solo] Enable=1) */
#endif
    klg_tick();
    klm_tick();
    klvh_tick();                                      /* klhigh.c: the 10 s census of the listed modules' reservations (off unless [Memory] High) */
#ifdef KLHOOK_TEST
    klva_tick();                                      /* klvalog.c: the per-caller table every 10 s (off unless [Memory] VaLog=1) */
#endif
    klarena_tick();                                   /* klarena.c: its 10 s line (off unless [Memory] DriverArena=1) */
    klquad_tick();                                    /* klquad.c: wraps VB Lock once the first quad buffer exists, a 60 s line (off unless [Memory] QuadRing) */
#ifdef KLHOOK_TEST
    kld3_tick();                                      /* kld3.c: its 10 s lines (off unless [Memory] D3dCount=1) */
#endif
    InterlockedExchange(&klh_tick_busy, 0);
}

/* SteamAPI_RunCallbacks has TWELVE call sites in kl2.exe (re/hook_review_talk.md): two in the main loop 0x87a930
   (0x87a9e6, 0x87aa7c), the others in the loader's pump, the lobby update, the network send / receive and five
   getters. 'The game's own thread, between two frames' - what every part that CALLS a game routine relies on - is
   only the main loop's two: the return address must lie inside that function, on the thread that first did so. */
static void __cdecl klh_w_runcallbacks(void)
{
    DWORD_PTR ra = (DWORD_PTR)_ReturnAddress(); int loop = ra >= (DWORD_PTR)KLH_VA(0x87a930) && ra < (DWORD_PTR)KLH_VA(0x87ab40);
    klh_real_runcallbacks();
    if (loop && klh_main_tid && klh_main_tid != GetCurrentThreadId()) loop = 0;
    if (loop) {
        /* [KLHook] Perf=1 (2026-10-14, the owner's '200+ fps'): every 10 s one line - the game's frames (this wrapper runs once a frame
           on the main loop), the time this hook's tick took on the main thread, and its memory reads. The whole-run frames / ms of
           KLHook.result mixes menus and loads (it varied +-40 % between equal runs); this line is the in-game figure. */
        static LARGE_INTEGER f, t0, a, b, prev; static LONGLONG spent, dt_max, tick_max; static LONG frames, reads0, hitch, told; static int perf = -1;
        if (perf < 0) { perf = GetPrivateProfileIntA("KLHook", "Perf", 1, klh_ini); QueryPerformanceFrequency(&f); QueryPerformanceCounter(&t0); reads0 = klh_reads; }
        if (perf) QueryPerformanceCounter(&a);
        klh_rcb_ra = ra;
        klh_tick(1);
        klh_rcb_ra = 0;
        if (perf) {
            QueryPerformanceCounter(&b); spent += b.QuadPart - a.QuadPart; frames++;
            if (b.QuadPart - a.QuadPart > tick_max) tick_max = b.QuadPart - a.QuadPart;
            if (prev.QuadPart) {                  /* STUTTER: frame to frame (2026-10-14, the owner: 'im getting bad stutters') */
                LONGLONG dt = a.QuadPart - prev.QuadPart;
                if (dt > dt_max) dt_max = dt;
                if (dt * 30 > f.QuadPart) hitch++;  /* a frame over 33 ms */
                if (dt * 1000 > f.QuadPart * 120 && dt < f.QuadPart * 3 && told < 6) {     /* each frame of 120 ms .. 3 s (not a load), at most 6 a window */
                    told++; klog("core: hitch %.0f ms", (double)dt * 1000.0 / (double)f.QuadPart);
                }
            }
            prev = a;
            if (b.QuadPart - t0.QuadPart >= f.QuadPart * 10) {
                double secs = (double)(b.QuadPart - t0.QuadPart) / (double)f.QuadPart, ms = (double)spent * 1000.0 / (double)f.QuadPart; LONG rd = klh_reads - reads0;
                klog("core: perf: %ld frames in %.1f s = %.1f fps; the hook's tick %.2f ms a frame (%.1f %% of the frame time, slowest %.1f ms), %ld memory reads a frame; "
                     "stutter: %ld frame(s) over 33 ms, the longest %.0f ms; UI Automation requests refused: %ld",
                     frames, secs, frames / secs, frames ? ms / frames : 0.0, ms / (secs * 10.0), (double)tick_max * 1000.0 / (double)f.QuadPart,
                     frames ? rd / frames : 0L, hitch, (double)dt_max * 1000.0 / (double)f.QuadPart, (long)InterlockedExchange(&klh_uia_n, 0));
                t0 = b; spent = 0; frames = 0; reads0 = klh_reads; hitch = 0; told = 0; dt_max = 0; tick_max = 0;
            }
        }
        klfps_mapcap_tick();                             /* klfps.c: [FrameLimit] MapCap, the per-map ceiling (DM05A:60) */
        klfps_gtick(ra);                                 /* klfps.c: the frame limiter's game thread fallback (only after a Present-route cut; after the perf line, which times the hook only) */
    }
}

/* ---------------------------------------------------------------- the stall watch (SHIP and TEST)

   WHY (re\freeze_1009.md). 2026-10-09 22:23: the owner quit from the score page, the session went 0x20 -> 0x2e and
   the game stood still, full screen, for 6.5 minutes until the PC was reset. The hook wrote nothing after the state
   line: no fault happened, so no dump, and what the main thread waited for is not known.
   WHAT. The ticker thread counts its own 100 ms steps in which the main thread gave no sign of life. A sign is a
   frame (the SteamAPI_RunCallbacks wrapper) or a step of the loader's message pump (klnudge.c's GetForegroundWindow
   wrapper, when [Load] has it in: a level load makes no frames). Steps are counted, not clock time, so a PC that
   slept does not look like a stall.
     StallSayMs   a silence longer than this is logged with its length when it ends (the healthy ones: 8.6 s on
                  Alt+Tab and 10.7 s in a frontend load are the longest in the logs up to 2026-10-10)
     StallMs      silent this long: one line with where the main thread stands, and KLHook_freeze.dmp (all threads,
                  region list; twice per process at most). Nothing else is done.
     StallEndMs   0 = never. Else the process is ENDED after that much silence, which gives the desktop back.
                  OFF by default: which silences a healthy game can have is not measured widely enough (a level
                  load without the GetForegroundWindow wrapper is silent for its whole length - 200 s were seen).
   NOT RUN IN THE GAME. */
static int klh_stall_say_ms = 3000, klh_stall_ms = 30000, klh_stall_end_ms;

static void klh_freeze_dump(void)
{
    HMODULE h = LoadLibraryA("dbghelp.dll"); MDWD w = h ? (MDWD)GetProcAddress(h, "MiniDumpWriteDump") : 0; char path[MAX_PATH]; HANDLE f;
    if (!w) return;
    snprintf(path, sizeof path, "%s\\KLHook_freeze.dmp", klh_out);
    f = CreateFileA(path, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, 0, 0);
    if (f == INVALID_HANDLE_VALUE) return;
    if (!w(GetCurrentProcess(), GetCurrentProcessId(), f, 0x1 | 0x40 | 0x1000 | 0x800, 0, 0, 0)) {    /* as write_dump */
        SetFilePointer(f, 0, 0, FILE_BEGIN); SetEndOfFile(f);
        w(GetCurrentProcess(), GetCurrentProcessId(), f, 0x1 | 0x40 | 0x1000, 0, 0, 0);
    }
    CloseHandle(f);
    klog("  dump written: KLHook_freeze.dmp (every thread; `python debug\\dump.py` says where the main and the render thread stand)");
}

static void klh_stall_watch(void)
{   /* every 100 ms on the ticker thread */
    static LONG last; static DWORD quiet; static int told, dumps;
    LONG beat = klh_game_ticks + kln_calls;
    if (!klh_tick_seen) return;                       /* before the main loop's first frame: start-up, movies */
    if (beat != last) {
        if (quiet * 100 >= (DWORD)klh_stall_say_ms && klh_stall_say_ms)
            klog("stall watch: the main thread is back after %.1f s without a frame or a loader step", quiet / 10.0);
        last = beat; quiet = 0; told = 0;
        return;
    }
    quiet++;
    if (klh_stall_ms && !told && quiet * 100 >= (DWORD)klh_stall_ms) {
        HANDLE t = klh_main_tid ? OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT, FALSE, klh_main_tid) : 0;
        CONTEXT c; char mod[80]; DWORD off; int got = 0;
        told = 1;
        klog("STALL: the main thread has given no frame and no loader step for %.0f s%s", quiet / 10.0,
             kln_real ? "" : " (the GetForegroundWindow wrapper is not in: a level load looks the same)");
        if (t) {
            memset(&c, 0, sizeof c); c.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
            if (SuspendThread(t) != (DWORD)-1) { got = GetThreadContext(t, &c); ResumeThread(t); }   /* resumed before any logging: it may hold a lock the log needs */
            CloseHandle(t);
            if (got) { klh_module(c.Eip, mod, sizeof mod, &off); klog("  main thread %lu at %s+0x%lx (%08lx)", klh_main_tid, mod, off, c.Eip); log_context(&c); }
        }
        if (dumps++ < 2) klh_freeze_dump();
    }
    if (klh_stall_end_ms && quiet * 100 >= (DWORD)klh_stall_end_ms) {
        klog("STALL: %.0f s of silence reached StallEndMs=%d: the process is ended here", quiet / 10.0, klh_stall_end_ms);
        TerminateProcess(GetCurrentProcess(), 0x57a11);
    }
}

/* ---------------------------------------------------------------- the hitch probe (SHIP and TEST)

   WHY (2026-10-14, the owner: 'im still experiencing stutters ... sort them out'). The perf line counts frames over 33 ms
   (2 .. 18 every 10 s while he moves through Retomoto, 150 .. 450 ms each, none while he stands still) but cannot say WHAT
   the main thread was doing. This thread looks every 5 ms; when the main loop has given no frame for HitchMs (default 50),
   it stops the main thread for a moment (SuspendThread / GetThreadContext / ResumeThread - no logging while it is
   stopped), takes where it stands (EIP) and the first return addresses on its stack that lie in a module, and counts them.
   Every 10 s with a hitch, one line: the places that were seen most, as module+offset (kl2.exe offsets read in the
   disassembly; d3d9 / nvd3dum / kernel32 / ReShade say who). A sample every 10 ms of a hitch: a 200 ms hitch is ~20
   samples. Costs nothing while frames come (one compare every 5 ms). [KLHook] HitchProbe=1 (0 = off) HitchMs=50 */
#define KLH_HP_N 48
static struct { DWORD addr; LONG n; } klh_hp_eip[KLH_HP_N], klh_hp_ret[KLH_HP_N];
static LONG klh_hp_samples, klh_hp_hitches;

static void klh_hp_count(DWORD a, int ret)
{
    int i; void *t = ret ? (void *)klh_hp_ret : (void *)klh_hp_eip;
    struct { DWORD addr; LONG n; } *tab = t;
    for (i = 0; i < KLH_HP_N; i++) {
        if (tab[i].addr == a) { tab[i].n++; return; }
        if (!tab[i].addr) { tab[i].addr = a; tab[i].n = 1; return; }
    }
}

static void klh_hp_say(void)
{
    int k, j, best; char mod[80], line[1100]; DWORD off; size_t at;
    if (!klh_hp_samples) return;
    for (k = 0; k < 2; k++) {
        struct { DWORD addr; LONG n; } *tab = k ? (void *)klh_hp_ret : (void *)klh_hp_eip;
        at = (size_t)snprintf(line, sizeof line, "hitch probe: %ld hitch(es), %ld sample(s); %s:", (long)klh_hp_hitches, (long)klh_hp_samples,
                              k ? "stack return addresses most seen" : "the main thread stood at");
        for (j = 0; j < 8; j++) {
            int i; best = -1;
            for (i = 0; i < KLH_HP_N; i++) if (tab[i].addr && tab[i].n > 0 && (best < 0 || tab[i].n > tab[best].n)) best = i;
            if (best < 0) break;
            klh_module(tab[best].addr, mod, sizeof mod, &off);
            if (at < sizeof line - 60) at += (size_t)snprintf(line + at, sizeof line - at, " %s+0x%lx x%ld", mod, off, (long)tab[best].n);
            tab[best].n = -tab[best].n;                         /* taken: shown once */
        }
        klog("%s", line);
    }
    memset(klh_hp_eip, 0, sizeof klh_hp_eip); memset(klh_hp_ret, 0, sizeof klh_hp_ret);
    klh_hp_samples = 0; klh_hp_hitches = 0;
}

static int klh_hp_in_code(DWORD a)
{
    MEMORY_BASIC_INFORMATION m;
    return a > 0x10000 && VirtualQuery((void *)(DWORD_PTR)a, &m, sizeof m) && m.Type == MEM_IMAGE && (m.Protect & (PAGE_EXECUTE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY));
}

static DWORD WINAPI klh_hitch_probe(LPVOID unused)
{
    int ms = GetPrivateProfileIntA("KLHook", "HitchMs", 50, klh_ini); LONG last = -1; DWORD since = 0, said = GetTickCount(), lastsample = 0; int in_hitch = 0;
    HANDLE t = 0;
    (void)unused;
    if (ms < 20) ms = 20;
    for (;;) {
        DWORD now; LONG beat;
        Sleep(5);
        if (!klh_tick_seen || !klh_main_tid) continue;
        if (!t) { t = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT, FALSE, klh_main_tid); if (!t) { Sleep(1000); continue; } }
        now = GetTickCount(); beat = klh_game_ticks;
        if (beat != last) { last = beat; since = now; in_hitch = 0; }
        else if (now - since >= (DWORD)ms && now - since < 5000 && now - lastsample >= 10) {   /* a hitch (a load or Alt+Tab of seconds: not counted) */
            CONTEXT c; DWORD st[256], got = 0; int ok = 0, i, n = 0;
            memset(&c, 0, sizeof c); c.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
            if (SuspendThread(t) != (DWORD)-1) {
                ok = GetThreadContext(t, &c);
                if (ok) got = klh_rd(c.Esp, st, sizeof st) ? 256 : (klh_rd(c.Esp, st, 64 * 4) ? 64 : 0);
                ResumeThread(t);
            }
            lastsample = now;
            if (!ok) continue;
            if (!in_hitch) { in_hitch = 1; klh_hp_hitches++; }
            klh_hp_samples++;
            klh_hp_count(c.Eip, 0);
            for (i = 0; i < (int)got && n < 6; i++) if (klh_hp_in_code(st[i])) { klh_hp_count(st[i], 1); n++; }
            klh_st_sample();                                    /* [Stall] Trace: the window message / Peek in flight (the thread runs again) */
        }
        if (now - said >= 10000) { said = now; klh_hp_say(); klh_st_say(); }
    }
}

static DWORD WINAPI klh_ticker(LPVOID unused)
{
    (void)unused;
    for (;;) {
        Sleep(100);
        klh_stall_watch();
        /* signed: the main loop may have ticked between the two reads. (Until 2026-10-09 this was `last = now | 1`
           and an unsigned compare: on an even tick count the difference wrapped and the fallback fired although the
           main loop was ticking - the 'driven by' line flipping within milliseconds in run HK1.) */
        if (!klh_tick_seen || (LONG)(GetTickCount() - klh_tick_last) > 500) klh_tick(0);
    }
}

/* ---------------------------------------------------------------- entry points */

__declspec(dllexport) HRESULT WINAPI DirectInput8Create(HINSTANCE h, DWORD v, REFIID r, LPVOID *o, LPUNKNOWN u)
{
    HRESULT hr;
    if (!real_create) {
        char p[MAX_PATH]; GetSystemDirectoryA(p, MAX_PATH); strcat(p, "\\dinput8.dll");
        HMODULE m = LoadLibraryA(p);
        real_create = m ? (DI8Create)GetProcAddress(m, "DirectInput8Create") : 0;
        if (!real_create) return E_FAIL;
    }
    hr = real_create(h, v, r, o, u);
#ifdef KLHOOK_TEST
    if (SUCCEEDED(hr)) kla_di8(o);
#endif
    if (SUCCEEDED(hr)) klrigid_di8(o);                 /* klrigid.c: [Rigid] mouse filter (no-op unless Enable=1) */
    return hr;
}

BOOL WINAPI DllMain(HINSTANCE inst, DWORD reason, LPVOID res)
{
    int n = 0; (void)res;
    if (reason != DLL_PROCESS_ATTACH) return TRUE;
    DisableThreadLibraryCalls(inst);
    InitializeCriticalSection(&cs);
    GetModuleFileNameA(inst, dir, MAX_PATH);
    char *s = strrchr(dir, '\\'); if (s) *s = 0;
    strcpy(klh_out, dir);
#ifdef KLHOOK_TEST
    {   /* klsolo.c: two kl2.exe from one game folder load the same dinput8.dll; each gets its own ini / log / result folder */
        char e[MAX_PATH]; DWORD k = GetEnvironmentVariableA("KLHOOK_DIR", e, sizeof e), a = k && k < sizeof e ? GetFileAttributesA(e) : INVALID_FILE_ATTRIBUTES;
        if (a != INVALID_FILE_ATTRIBUTES && (a & FILE_ATTRIBUTE_DIRECTORY)) strcpy(klh_out, e);
    }
#endif
    snprintf(klh_ini, sizeof klh_ini, "%s\\KLHook.ini", klh_out);
    continue_asserts = GetPrivateProfileIntA("KLHook", "ContinueAsserts", 1, klh_ini);
    max_dumps = GetPrivateProfileIntA("KLHook", "MaxDumps", 4, klh_ini);
    max_asserts = GetPrivateProfileIntA("KLHook", "MaxAsserts", 200, klh_ini);
    klh_end_on_fatal = GetPrivateProfileIntA("KLHook", "EndOnFatal", 1, klh_ini);
    klh_fastexit = GetPrivateProfileIntA("KLHook", "FastExit", 1, klh_ini) != 0;
    klh_stall_say_ms = GetPrivateProfileIntA("KLHook", "StallSayMs", 3000, klh_ini);
    klh_stall_ms = GetPrivateProfileIntA("KLHook", "StallMs", 30000, klh_ini);
    klh_stall_end_ms = GetPrivateProfileIntA("KLHook", "StallEndMs", 0, klh_ini);
    if (klh_stall_end_ms && klh_stall_end_ms < 60000) klh_stall_end_ms = 60000;     /* never a short fuse */
#ifdef KLHOOK_TEST
    klh_policy = GetPrivateProfileIntA("KLHook", "SessionSafe", 1, klh_ini) ? KLH_SESSION : KLH_DIRECT;
#endif
    HMODULE exe = GetModuleHandleA(NULL);
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)((BYTE *)exe + ((IMAGE_DOS_HEADER *)exe)->e_lfanew);
    img_lo = (DWORD)exe; img_hi = img_lo + nt->OptionalHeader.SizeOfImage;
    klh_exe_ok = img_lo == KL2_BASE && nt->FileHeader.TimeDateStamp == KL2_TIMESTAMP && nt->OptionalHeader.SizeOfImage == KL2_IMAGESIZE;
    AddVectoredExceptionHandler(1, veh);
    klog("==== KLHook loaded (ContinueAsserts=%d MaxDumps=%d) kl2.exe %08lx-%08lx", continue_asserts, max_dumps, img_lo, img_hi);
    klog("build: %s, %s %s; exe %s; patch policy: %s",
#ifdef KLHOOK_TEST
         "TEST (klauto)",
#else
         "SHIP",
#endif
         __DATE__, __TIME__, klh_exe_ok ? "is kl2.exe build 0490" : "is NOT the known kl2.exe: data fixes and [Slots] are off, only import slots are wrapped", klh_policy_name[klh_policy]);
    if (GetPrivateProfileIntA("KLHook", "ExitLog", 1, klh_ini)) {
        int m;
        n += klh_iat("KERNEL32.dll", "ExitProcess", (void *)klh_w_exitprocess, (void **)&klh_real_exitprocess);
        m = klh_iat("MSVCR90.dll", "exit", (void *)klh_w_exit, (void **)&klh_real_exit) + klh_iat("MSVCR90.dll", "_exit", (void *)klh_w__exit, (void **)&klh_real__exit);
        if (m) klog("core: %d more import slot(s) wrapped for the exit line (MSVCR90 exit %s, _exit %s)", m, klh_real_exit ? "yes" : "no", klh_real__exit ? "yes" : "no");
    }
    if (GetPrivateProfileIntA("KLHook", "Tick", 1, klh_ini)) n += klh_iat("steam_api.dll", "SteamAPI_RunCallbacks", (void *)klh_w_runcallbacks, (void **)&klh_real_runcallbacks);
    klh_st_init();                                    /* [Stall] Trace: PeekMessageA / W import slots (timing only) */
    klog("core: %d import slot(s) wrapped (ExitProcess %s, SteamAPI_RunCallbacks %s); EndOnFatal=%d", n, klh_real_exitprocess ? "yes" : "no", klh_real_runcallbacks ? "yes" : "no", klh_end_on_fatal);
    kset_init();                                      /* klset.c: the menu rows first - klreshade.c reads them for the live preset */
    {   /* [Graphics] Look (2026-10-14, the owner: 'have these as different setting options so people can choose how they want their game to
           look but not impact performance if they dont want it on'): 0 = Off, ReShade is not loaded at all (the stock frame rate; run
           LOOK2: ~130 fps average with ReShade in the Direct3D 9 path against ~252 without); 1 = KL (ReShadePreset_KL.ini: KL_Look.fx, the
           cool overcast grade); 2 = LiveLeak (ReShadePreset_LiveLeak.ini: KL_Camcorder.fx). ReShade - and with it the Uplift add-on, F10 -
           is loaded from ReShade32.dll beside the game (it was d3d9.dll) after its ReShade.ini [GENERAL] PresetPath is pointed at the
           chosen preset. Read once at start, before the game makes its device: a change needs a restart. [Graphics] ReShade=0 = Look=0.
           2026-10-15: with [ReShade] Bridge=1 (klreshade.c) ReShade is pointed at the bridge's own live preset instead (made here from
           the look's preset) and KLHook registers itself as a ReShade add-on after the load: the Mod settings rows then switch live.
           [ReShade] LoadWhenOff=1 loads ReShade with Look=0 too (every effect off) so that a look can be switched on in the menu. */
        static const char *const preset[3] = { "", ".\\ReShadePreset_KL.ini", ".\\ReShadePreset_LiveLeak.ini" };
        static const char *const lname[3] = { "Off", "KL", "LiveLeak" };
        char rp[MAX_PATH], ri[MAX_PATH]; int look = GetPrivateProfileIntA("Graphics", "Look", 1, klh_ini), load;
        if (!GetPrivateProfileIntA("Graphics", "ReShade", 1, klh_ini)) look = 0;
        if (look < 0 || look > 2) look = 1;
        load = look || (GetPrivateProfileIntA("ReShade", "Bridge", 0, klh_ini) && GetPrivateProfileIntA("ReShade", "LoadWhenOff", 0, klh_ini) &&
                        GetPrivateProfileIntA("Graphics", "ReShade", 1, klh_ini));
        snprintf(rp, sizeof rp, "%s\\ReShade32.dll", dir); snprintf(ri, sizeof ri, "%s\\ReShade.ini", dir);
        if (load && GetFileAttributesA(rp) != INVALID_FILE_ATTRIBUTES) {
            HMODULE rm; char ao[MAX_PATH], af[MAX_PATH]; const char *live;
            /* [Graphics] Neural (2026-10-14): the GITC Uplift add-on (DLSS/DLAA through the neural renderer, F10) is a ReShade add-on that
               ReShade loads by finding gitc-uplift.addon32 beside it; even switched off (F10 not pressed) it hooks the device. 0 = the add-on
               file is set aside as gitc-uplift.addon32.off before ReShade loads, so it costs nothing; 1 = it is put back. */
            int neural = GetPrivateProfileIntA("Graphics", "Neural", 0, klh_ini);
            snprintf(ao, sizeof ao, "%s\\gitc-uplift.addon32", dir); snprintf(af, sizeof af, "%s\\gitc-uplift.addon32.off", dir);
            if (neural && GetFileAttributesA(ao) == INVALID_FILE_ATTRIBUTES && GetFileAttributesA(af) != INVALID_FILE_ATTRIBUTES) MoveFileA(af, ao);
            if (!neural && GetFileAttributesA(ao) != INVALID_FILE_ATTRIBUTES && GetFileAttributesA(af) == INVALID_FILE_ATTRIBUTES) MoveFileA(ao, af);
            klog("graphics: neural (Uplift add-on) %s: %s", neural ? "on" : "off", GetFileAttributesA(ao) != INVALID_FILE_ATTRIBUTES ? "gitc-uplift.addon32 present" : "add-on set aside or absent");
            live = klrs_prepare(look);                     /* klreshade.c: 0 unless [ReShade] Bridge=1 (then its live preset, written now) */
            WritePrivateProfileStringA("GENERAL", "PresetPath", live ? live : preset[look ? look : 1], ri);
            rm = LoadLibraryA(rp);
            klog("graphics: look %s: ReShade %s from %s (preset %s)%s", lname[look], rm ? "loaded" : "FAILED to load", rp, live ? live : preset[look ? look : 1],
                 look ? "" : " - [ReShade] LoadWhenOff=1: every effect starts off");
            if (rm && live) klrs_attach(rm, (HMODULE)inst);     /* klreshade.c: KLHook as a ReShade add-on; logs and does nothing when it cannot */
        } else klog("graphics: look %s: ReShade not loaded%s", lname[look], look ? " (no ReShade32.dll beside the game)" : "");
    }
    kltx_init();                                   /* after ReShade: the Direct3DCreate9 wrapper sits in front of it */
#ifdef KLHOOK_TEST
    klso_init();                                   /* klsolo.c: AFTER kltx_init, so its Direct3DCreate9 wrapper is the outer one */
#endif
    klfps_init();                                  /* klfps.c: LAST of the Direct3DCreate9 wrappers (outermost); [FrameLimit] */
    klm_init();
    klvh_init();                                   /* klhigh.c: AFTER klm_init (the reserve is taken first, low); wraps the listed modules' import slots, with High=2 takes the high half */
#ifdef KLHOOK_TEST
    klva_init();                                   /* klvalog.c: AFTER klm_init (its reserve is not counted); off unless [Memory] VaLog=1 */
#endif
    klarena_init();                                /* klarena.c: AFTER klva_init; off unless [Memory] DriverArena=1 */
    klquad_init();                                 /* klquad.c: off unless [Memory] QuadRing (TEST: off while kld3.c D3dRing is on) */
#ifdef KLHOOK_TEST
    kld3_init();                                   /* kld3.c: AFTER klarena_init (reads its counters); off unless [Memory] D3dCount=1 */
#endif
    klxp_init();                                   /* klextpt.c: extension points off (hook DLLs of other programs), watcher of foreign modules */
    kln_init();
    klf_init();
    klj_init();
    klt_init();
    klc_init();
    kpm_init();                                       /* klpm.c: [Match] (default off) */
    klw_init();
    kltt_init();                                       /* kltrait.c: BEFORE klr_init / kly_init, which read its switch */
    klnm_init();
    klk_init();
    klvo_init();                                      /* klvoice.c: [Voice] (default off) */
    klb_init();
    kle_init();
    klmv_init();
    klv_init();
    klfc_init();
    kus_init();
    klfr_init();
    klq_init();
    klrp_init();
    klr_init();
    kly_init();
    klu_init();
    klesc_init();                                     /* klhud_escape.c: after klu_init */
    kltrk_init();                                     /* klhud_tracker.c: after klu_init */
    klbrd_init();                                     /* klhud_board.c: after klu_init */
    klsb_init();                                      /* klhud_board2.c: after klu_init */
    klkf_init();                                      /* klhud_kill.c: after klu_init */
    klpu_init();                                      /* klhud_popup.c: after klu_init, it reads [HUD] with klhud.c's helpers */
    klo_init();
    klcam_init();
    klcamsmooth_init();                               /* klcamsmooth.c: reads [CamSmooth] */
    klap_init();                                      /* klanimprobe.c: reads [AnimProbe]; patches the top of Play only when Enable=1 and the guard allows */
    klmf_init();                                      /* klmfprobe.c: reads [MFProbe]; TEST build detours 0x8edc40 / 0x6d2500 / 0x5f2370 (log only) */
    klhp_init();                                      /* klheliprobe.c: reads [Heli] Probe, installs nothing */
    klcn_init();                                      /* klcensor.c: reads [Censor] */
    klcs_init();                                      /* klcensus.c: reads [Census] */
    klbdp_init();                                      /* klbotdeath.c: reads [BotDeathProbe]; TEST build detours 0x61efd0 / 0x61a980 / 0x4bd540 / 0x688190 / 0x8edaf0 (log only) */
    kcvd_init();                                      /* klcoverdump.c: reads [CoverDump] */
    klcc_init();                                      /* klclubcalm.c: reads [ClubCalm] */
    klch_init();                                      /* klclubholster.c: reads [ClubHolster] */
    klvis_init();
    klnet_init();
    kllb_init();
    kllo_init();                                      /* kllobbyopt.c: reads [Lobby] TimeMax / TimeMin / RoundsMax */
    klon_init();                                      /* klonline.c: [Online] Log */
    klor_init();                                      /* klonline_read.c: [Online] Read */
    klbf_init();                                      /* klbotfill.c: reads [Bots] OnlineFill (after kllb_init: it reads the same key) */
    klcq_init();                                      /* klcopsquad.c: reads [CopSquad] */
    klsab_init();                                     /* klsabotage.c: reads [Sabotage] */
    klq2_init();                                      /* klqol.c: [QoL] (default off) */
    kqb_init();                                       /* klqol2.c: [QoL2] (default off) */
    klnetfix_init();
    knl_init();                                       /* klnetload.c: reads [NetLoad] */
    klinv_init();
    klgrenade_init();                                 /* klgrenade.c: after klinv_init (shares its user32 pointers) */
    klnetsmooth_init();
    klud_init();                                      /* klucc_down.c: reads [Ucc] DownOnly */
    klmu_init();                                      /* klmusic.c: [Music] (default off) */
    klam_init();                                     /* klambience.c: [Ambience] (default off) */
    klst_init();                                      /* klstinger.c: [Stinger] (default off) */
    klrigid_init();
    klaiturn_init();                                  /* klaiturn.c: after klrigid_init; one guarded data write at start-up */
    klshop_init();
    kspg_init();                                      /* klshoppage.c: reads KLShopPage.ini */
    klp_init();
    klfk_init();
    kld_init();
    klbd_init();
    klcd_init();
    klsh_init();
    kldy_init();                                      /* klcdying.c: reads [Dying]; after klbd_init (sets its NoFire) */
    kad_init();
    klg_init();
    klx_init();
    klsv_init();                                      /* klserver.c: [Server] (default off) */
    klmm_init();                                      /* klmm.c: installs nothing unless [Net] PrivateLobby or BuildKey is set */
    kls_init(inst);
    klho_init();                                      /* klhostopt.c: after kls_init (kls_online_set) and klbf_init / kllb_init */
    klco_init();                                      /* klcharonline.c: after klc_init (it reads the choice) */
    klsy_init();                                      /* klsync.c: reads [Sync] */
    kluc_init();                                      /* klucc.c: reads [Ucc]; asks klnetchan.c for the channel when on */
    klucc_init();                                     /* klucchide.c: reads [Ucc] Hide; asks klnetchan.c for the channel when on */
    klua_init();                                      /* klucc_aim.c: reads [Ucc] PoliceAim */
    kllnm_init();                                     /* kllocname.c: after kls_init (it reads the rule table) */
#ifdef KLHOOK_TEST
    kla_init(inst);
    klpr_init_all();                              /* klprobe.c: reads [Probe] DoorProxy, installs nothing when 0 */
    klh_uef_on = !kla_on;                         /* with [Auto] Enable=1 the test rig's own filter gives the verdict */
#else
    klh_uef_on = 1;
#endif
    klh_uef_arm();
    CloseHandle(CreateThread(0, 0, klh_ticker, 0, 0, 0));
    if (klh_fastexit) CloseHandle(CreateThread(0, 0, klh_keywatch, 0, 0, 0));
    if (GetPrivateProfileIntA("KLHook", "HitchProbe", 1, klh_ini)) CloseHandle(CreateThread(0, 0, klh_hitch_probe, 0, 0, 0));
    return TRUE;
}

#ifdef KLHOOK_HARNESS
/* off-game harness only: ask the guard about an address of a copy of kl2.exe mapped at <mapped> (or any pointer) */
__declspec(dllexport) int klh_test_may(void *mapped, void *at, int len, int policy)
{
    klh_delta = (LONG_PTR)((DWORD_PTR)mapped - KL2_BASE); klh_exe_ok = 1;
#ifdef KLHOOK_TEST
    klh_policy = policy;
#else
    (void)policy;
#endif
    return klh_may_write(at, (DWORD)len, "harness");
}
/* the tick's parts against a copy of kl2.exe mapped at <mapped> (its .data holds the harness's made-up pointers) */
__declspec(dllexport) void klh_test_tick(void *mapped, int times)
{
    klh_delta = (LONG_PTR)((DWORD_PTR)mapped - KL2_BASE); klh_exe_ok = 1;
    while (times-- > 0) { klx_tick(); klj_tick(); }
}
#endif
#endif /* KLHOOK_C */
