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
 *   klstock.h      x     x    GENERATED (mkstock.py): size and directory hash of the 22 stock level archives
 *   kljoin.c       x     x    jump boxes: a two-part level joined by the game's own jump request ([Join], KLJoin.ini)
 *   klcrew_rt.c    x     x    the AI crew follows that jump ([CrewJoin]; calls 0x62a900, 0x72e0f0; no data, no code). OFF by default
 *   klchar.c       x     x    the heister the player chose: body, mask, outfit ([Character], KLWardrobe.ini)
 *   klgun.c        x     x    switchable gun looks ([Guns], KLGuns.ini)
 *   klcrew.c       x     x    random AI heisters ([Crew]; calls 0x783fb0, 0x88c810, with Names 0x83e2e0, 0x469250; eight heap
 *                             bytes) and 'who wears whom' for kltalk.c (read only). OFF by default
 *   kltalk.c       x     x    Kane / Lynch scenes and chatter ([Talk], KLTalk.ini; calls 0x828fa0, 0x421c70; no data, no
 *                             code). OFF by default
 *   klbot.c        x     x    the AI crew's log and the backstab / bribe / leave / van rules ([Bots]). OFF by default
 *   klescort.c     x     x    one or two AI heisters stay near the human ([Bots] Escort; calls 0x760e50, the soldier's own
 *                             'defend this place' order; no data, no code) and [Bots] BoardAll (ONE data byte: a bot
 *                             held by loot gets heist stage 3 while the vehicle waits). OFF by default
 *   klhop.c        x     x    an AI heister that stands at a place the mesh does not carry it over is put beyond it
 *                             ([CrewHop], KLJoin.ini; calls 0x62a900 through klcrew_rt.c's functions, with Reorder
 *                             0x760e50; no data, no code). OFF by default
 *   klclimb.c      x     x    the PLAYER climbs a wall edge of the level's KLJoin.ini with Dead Men's climb clip
 *                             ([Climb]; game routines called: the mini animation, AlignTo, the collision switch, the
 *                             proxy; no code). OFF by default. Wired 2026-10-11 after two reviews; NOT RUN IN THE GAME
 *   klhud.c        x     x    the expansion's FA / Arcade HUD, Version 1 ([HUD]): crew list + money box drawn with the game's
 *                             own ZCHAROBJ texts from a private copy of the OSD's vtable (slot 55 wrapped, as klchar.c
 *                             wraps the option object); calls 0x8ccde0, 0x598460, 0x817810 and ZCHAROBJ slots on the
 *                             main thread; one data byte hides the stock top-left block. OFF by default, NOT RUN
 *   klmem.c klnudge.c x  x    address space reserve ([Memory]); the loader's cursor nudge ([Load])
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
 *   [Join] [Join.2] .. [Join.8]                             kljoin.c (also KLJoin.ini beside a level archive)
 *   [CrewJoin] [Crew] [Talk]                                klcrew_rt.c, klcrew.c, kltalk.c - each OFF unless its key is set
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
static char dir[MAX_PATH], klh_ini[MAX_PATH];
static int continue_asserts = 1, max_dumps = 4, dumps = 0, max_asserts = 200;
static DWORD seen[256]; static int nseen;
static CRITICAL_SECTION cs;
static DWORD img_lo = 0x400000, img_hi = 0x400000;
static int klh_exe_ok;                            /* the process image is kl2.exe build 0490 at 0x400000 */
static LONG_PTR klh_delta;                        /* 0 in the game; an off-game harness maps a copy of kl2.exe elsewhere */
#define KLH_VA(x) ((BYTE *)((DWORD_PTR)(x) + klh_delta))

static void klog(const char *fmt, ...)
{
    char path[MAX_PATH]; snprintf(path, sizeof path, "%s\\KLHook.log", dir);
    FILE *f = fopen(path, "a"); if (!f) return;
    SYSTEMTIME t; GetLocalTime(&t);
    fprintf(f, "%02d:%02d:%02d.%03d ", t.wHour, t.wMinute, t.wSecond, t.wMilliseconds);
    va_list a; va_start(a, fmt); vfprintf(f, fmt, a); va_end(a);
    fputc('\n', f); fclose(f);
}

static int klh_rd(DWORD_PTR p, void *out, SIZE_T n)
{   /* never faults: nothing in this DLL may raise an exception of its own */
    SIZE_T got = 0;
    return p > 0xffff && ReadProcessMemory(GetCurrentProcess(), (void *)p, out, n, &got) && got == n;
}
static DWORD klh_rd32(DWORD_PTR p) { DWORD v = 0; klh_rd(p, &v, 4); return v; }

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
    else if (klh_policy == KLH_SHIP && kind != 'i' && kind != 'w') why = "code or constants: a ship build writes import slots and data only";
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
    char path[MAX_PATH]; snprintf(path, sizeof path, "%s\\KLHook_%d.dmp", dir, ++dumps);
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
static void WINAPI klh_w_exitprocess(UINT code)
{
    if (code == 0x8000dead)
        klog("INTEGRITY EXIT: ExitProcess(0x8000dead) - kl2.exe's code-integrity check found a changed byte of its image (re\\antitamper.md). "
             "Patches refused this run: %ld; hashed bytes patched under policy 'direct': %ld", klh_refused, klh_hashed_in);
    else klog("exit: ExitProcess(%lu)", (DWORD)code);
    klx_exit_line();
    klh_real_exitprocess(code);
}

/* The C runtime's exit / _exit (kl2.exe's imports from MSVCR90.dll, 8 + 5 call sites). Run HK1 (SHIP, direct boot
   ended by AutoExit) left NO 'exit:' line: that end does not come through kl2.exe's ExitProcess import (two call
   sites, 0x7e8a6c and 0x8f8793). ASSUMPTION, not seen: it leaves through exit() - WinMain returning into the C
   start-up code - whose ExitProcess call is MSVCR90's own import. klauto wraps the same two slots on top of
   these when [Auto] is on (its END lines); both chain. */
static void (__cdecl *klh_real_exit)(int), (__cdecl *klh_real__exit)(int);
static void __cdecl klh_w_exit(int code) { klog("exit: exit(%d)", code); klx_exit_line(); klh_real_exit(code); }
static void __cdecl klh_w__exit(int code) { klog("exit: _exit(%d)", code); klx_exit_line(); klh_real__exit(code); }

/* ---------------------------------------------------------------- the parts */

static void klh_tick(int game_thread);
#include "klmem.c"
#include "klnudge.c"
#include "klfix.c"
#include "kljoin.c"
#include "klcrew_rt.c"
#include "klgun.c"
#include "klchar.c"
#include "klcrew.c"
#include "kltalk.c"
#include "klbot.c"
#include "klescort.c"
#include "klhop.c"
#include "klmove.c"
#include "klclimb.c"
#include "klrappel.c"                                    /* klrappel.c: off unless [Rappel] Enable */
#include "klbalance.c"
#include "klgrudge.c"
#include "klhud_names.c"                              /* the crew list's character names + initials as tags ([HUD] Names / NameTags) */
#include "klhud_values.c"                             /* the HUD's readers (reads only): BEFORE klhud.c, AFTER klbot.c */
#include "klhud.c"                                    /* includes klhud_weapon.c inside itself */
#include "klhud_popup.c"                              /* AFTER klhud.c: pop-ups + loot ring (uses its klu / klu_r / klu_pic) */
#include "klhud_kill.c"                              /* AFTER klhud_popup.c: the kill / reward line under REWARDS (uses klpu_str) */
#include "klhud_escape.c"                             /* AFTER klhud_popup.c: the escape-vehicle panel in the new look (uses klu / klu_r / klu_pic) */
#include "klhud_tags.c"                              /* AFTER klhud_escape.c: the tags over the heisters' heads (uses klu / klu_r / klu_cs / klnm_tag_ini) */
#include "klhud_board.c"                             /* AFTER klhud_tags.c: the pre-round panel in the new look ([HUD] Board, default 0) */
#include "klhud_board2.c"                            /* AFTER klhud_board.c: the round-over scoreboard ([HUD] Scoreboard, default 0) */
#include "klshoulder.c"
#include "klvis.c"
#include "klnet.c"
#include "klfed.c"
#include "klfedkit.c"
#include "kldown.c"
#include "klbotdown.c"                                    /* klbotdown.c: AI heisters down, not dead (off unless [BotDown] Enable) */
#include "kladren.c"                                      /* kladren.c: adrenaline (off unless [Adrenaline] Enable); its tick runs BEFORE kld_tick */
#include "klsteam.c"
#include "klslot.c"
#ifdef KLHOOK_TEST
#include "klauto.c"
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
    klf_tick();
    kls_tick();
    klx_tick();
    klj_tick();
    klt_tick(game_thread);                            /* DIRECTLY after klj_tick: it must see kljoin.c's request while it is pending (klcrew_rt.c, EARLY) */
    klv_tick(game_thread);                            /* klhop.c: an AI heister that stands at a [CrewHop] place is put beyond it (one game call a tick) */
    klq_tick(game_thread);                            /* klclimb.c: the player at the foot of a [Climb] edge climbs it (OFF unless [Climb] Enable=1) */
    klrp_tick(game_thread);                           /* klrappel.c: the descent of the rappel cut */
    klc_tick(game_thread);
    klw_tick(game_thread);                            /* after klc_tick: the player's own body goes first */
    klk_tick(game_thread);                            /* after klw_tick: it reads who wears whom */
    klb_tick(game_thread);
    kle_tick(game_thread);                            /* klescort.c: after klb_tick; one game call per order, game thread only */
    klmv_tick(game_thread);                           /* klmove.c: Restless / WaitForYou / BoardNear (all off unless set) */
    klr_tick(game_thread);                            /* klbalance.c: one damage scale for player, police and crew */
    klnm_tick(game_thread);
    kly_tick(game_thread);                            /* klgrudge.c: the crew answers your bullets (off unless [Bots] Grudge) */
    klu_tick(game_thread);                            /* klhud.c: the crew list / money box texts (game thread only) */
    klesc_tick(game_thread);                          /* klhud_escape.c: the escape-vehicle panel (off unless [HUD] Escape / Draft) */
    klbrd_tick(game_thread);                          /* klhud_board.c: the pre-round panel (off unless [HUD] Board=1) */
    klsb_tick(game_thread);                           /* klhud_board2.c: the round-over scoreboard (off unless [HUD] Scoreboard=1) */
    klkf_tick(game_thread);                           /* klhud_kill.c: the kill / reward line under REWARDS (off unless [HUD] KillLine / Draft) */
    klpu_tick(game_thread);                           /* klhud_popup.c: centre pop-ups + loot ring (after klu_tick; off unless [HUD] Popups / LootRing / Draft) */
    klo_tick(game_thread);                            /* klshoulder.c: log only */
    klvis_tick();                                     /* klvis.c: log only (the vision grid and its record 0xff) */
    klnet_tick(game_thread);                          /* klnet.c: multiplayer log / update numbers (off unless [Net]) */
    klp_tick(game_thread);                            /* klfed.c: come back as a fed (data writes only) */
    klfk_tick(game_thread);                           /* klfedkit.c: the fed can hunt, body, AK (with [Fed] Player=1; Kit=0 = off) */
    klbd_tick(game_thread);                           /* klbotdown.c: before kladren, which reads its down state */
    kad_tick(game_thread);                            /* kladren.c: raises the mash meter first */
    kld_tick(game_thread);                            /* kldown.c: the mash get-up (off unless [Down] Enable) */
    klg_tick();
    klm_tick();
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
    if (loop) klh_tick(1);
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
    snprintf(path, sizeof path, "%s\\KLHook_freeze.dmp", dir);
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
    snprintf(klh_ini, sizeof klh_ini, "%s\\KLHook.ini", dir);
    continue_asserts = GetPrivateProfileIntA("KLHook", "ContinueAsserts", 1, klh_ini);
    max_dumps = GetPrivateProfileIntA("KLHook", "MaxDumps", 4, klh_ini);
    max_asserts = GetPrivateProfileIntA("KLHook", "MaxAsserts", 200, klh_ini);
    klh_end_on_fatal = GetPrivateProfileIntA("KLHook", "EndOnFatal", 1, klh_ini);
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
    klog("core: %d import slot(s) wrapped (ExitProcess %s, SteamAPI_RunCallbacks %s); EndOnFatal=%d", n, klh_real_exitprocess ? "yes" : "no", klh_real_runcallbacks ? "yes" : "no", klh_end_on_fatal);
    klm_init();
    kln_init();
    klf_init();
    klj_init();
    klt_init();
    klc_init();
    klw_init();
    klnm_init();
    klk_init();
    klb_init();
    kle_init();
    klmv_init();
    klv_init();
    klq_init();
    klrp_init();
    klr_init();
    kly_init();
    klu_init();
    klesc_init();                                     /* klhud_escape.c: after klu_init */
    klbrd_init();                                     /* klhud_board.c: after klu_init */
    klsb_init();                                      /* klhud_board2.c: after klu_init */
    klkf_init();                                      /* klhud_kill.c: after klu_init */
    klpu_init();                                      /* klhud_popup.c: after klu_init, it reads [HUD] with klhud.c's helpers */
    klo_init();
    klvis_init();
    klnet_init();
    klp_init();
    klfk_init();
    kld_init();
    klbd_init();
    kad_init();
    klg_init();
    klx_init();
    kls_init(inst);
#ifdef KLHOOK_TEST
    kla_init(inst);
    klh_uef_on = !kla_on;                         /* with [Auto] Enable=1 the test rig's own filter gives the verdict */
#else
    klh_uef_on = 1;
#endif
    klh_uef_arm();
    CloseHandle(CreateThread(0, 0, klh_ticker, 0, 0, 0));
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
