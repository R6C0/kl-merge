/*
 * kllistguard.c - [Crash] ListUserGuard: swallows the one known kl2.exe crash in the per-frame CListUser update (SHIP and TEST alike).
 * Part of KLHook (included by klhook.c after klfresh.c). Writes NO code byte and NO .rdata byte: data only (a dword in a heap object).
 *
 * CRASH (owner, DM03 round 2, 2026-11-09 16:46, debug/notes/2026-11-09-dm03-fedrespawn-crash.md): c0000005 at kl2 0x4f8a8e (cmp [edx],esi in
 * the hash-chain remove 0x4f8a60) reading 0x4f09, right after a fed (police) respawn. CListUser slot 0 (0x630700, thiscall(this, n, rec),
 * ret 8) walks an array of records; a record that was released while still in the list has [rec+0x54] & 0xffffff == 0, key 0 = the table's
 * header word, and the chain walk follows a count as if it were a node pointer.
 *
 * WHY A PRIVATE VTABLE (not a poke of 0xb5a1d4): that vtable is inside a HASHED .rdata range (klranges.h 0xb11000..0xb8ac00); a changed byte
 * ends a real session and the ship policy refuses it. The object itself is heap data, so its vptr (dword at +0) may point at a private copy of
 * the vtable whose slot 0 is kllg_wrap (kllistguard_seh.h): the same route as klroundkeep.c / kllobby.c. The only call of 0x630700 is
 * `call edx` at 0x5bfc03 through [[obj]], and no other vtable holds 0x630700 (whole-file scan), so every call is seen.
 *
 * FINDING THE OBJECT: nothing in the exe lists it (one is made per level by the loader at 0x8adfa6, stored in an owner at +0x86d4). A
 * low-priority thread scans committed private read-write memory for a 4-aligned dword 0xb5a1d4 whose +0x20 pointer is set (kllg_cand_ok),
 * each hit is repointed by the game thread (klh_data, re-checking the dword first). Scans: +2, +6, +15, +30 s after a scene change, then
 * every 10 s (a round-2 object without a scene change is caught within 10 s). Every scan reads in __try, so a page freed meanwhile only ends that region.
 *
 * ON A CATCH: only an access violation whose address lies in 0x4f8a60..0x4f8b49 is swallowed; the half-done update of that one list is
 * dropped (GUESS: harmless, the next frame redoes it; the record with key 0 was dead anyway). Anything else goes on to the game's handler.
 * A VEH installed earlier ([CampGuard] ListUserFA=1) sees the fault first and then this wrapper never fires; both are fine together.
 *
 * KLHook.ini
 *   [Crash]
 *   ListUserGuard=0    1 = on (recommended on)
 *   Log=1              one line per catch (first one, then at most one per 10 s) and one per object found
 */
#include "kllistguard_logic.h"
#include "kllistguard_seh.h"

static DWORD *kllg_vt;                         /* the private vtable (VirtualAlloc'd, never freed) */
static volatile LONG kllg_busy, kllg_done;     /* scanner thread: running / results ready */
static DWORD kllg_cand[16]; static volatile LONG kllg_ncand;
static int kllg_patched, kllg_scans, kllg_step;
static DWORD kllg_next;
static char kllg_scene[160];

static DWORD WINAPI kllg_scan_thread(LPVOID unused)
{
    SYSTEM_INFO si; BYTE *p; NT_TIB *tib = (NT_TIB *)NtCurrentTeb(); MEMORY_BASIC_INFORMATION mbi; LONG n = 0;
    (void)unused;
    SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_BELOW_NORMAL);
    GetSystemInfo(&si);
    for (p = (BYTE *)si.lpMinimumApplicationAddress; p < (BYTE *)si.lpMaximumApplicationAddress && n < 16; p = (BYTE *)mbi.BaseAddress + mbi.RegionSize) {
        if (!VirtualQuery(p, &mbi, sizeof mbi)) break;
        if (mbi.State != MEM_COMMIT || mbi.Type != MEM_PRIVATE || mbi.Protect != PAGE_READWRITE || mbi.RegionSize < KLLG_OBJ_SZ) continue;
        if ((BYTE *)mbi.BaseAddress + mbi.RegionSize > (BYTE *)tib->StackLimit && (BYTE *)mbi.BaseAddress < (BYTE *)tib->StackBase) continue;   /* our own stack */
        __try {
            DWORD *q = (DWORD *)mbi.BaseAddress, *e = (DWORD *)((BYTE *)mbi.BaseAddress + mbi.RegionSize - KLLG_OBJ_SZ);
            for (; q <= e; q++)
                if (*q == KLLG_VT && kllg_cand_ok((unsigned)(DWORD_PTR)q, q[0], q[8]) && n < 16) kllg_cand[n++] = (DWORD)(DWORD_PTR)q;
        } __except (EXCEPTION_EXECUTE_HANDLER) { }
    }
    kllg_ncand = n; InterlockedExchange(&kllg_done, 1); InterlockedExchange(&kllg_busy, 0);
    return 0;
}

static void kllg_init(void)
{
    DWORD slot0, *tab; int len, i; DWORD tl = 0x401000, th = 0x00b11000;   /* .text = 0x401000..0xb11000 */
    kllg_on = GetPrivateProfileIntA("Crash", "ListUserGuard", 0, klh_ini) != 0;
    kllg_log = GetPrivateProfileIntA("Crash", "Log", 1, klh_ini);
    if (!kllg_on) return;
    if (!klh_exe_ok || klh_delta) { klog("listguard: ListUserGuard=1 but this is not kl2.exe build 0490 at 0x400000: off"); kllg_on = 0; return; }
    slot0 = klh_rd32((DWORD_PTR)KLH_VA(KLLG_VT));
    if (!kllg_slot_ok(slot0)) { klog("listguard: REFUSED, vtable 0x%08x slot 0 holds 0x%08x (expected 0x%08x): not the known exe", KLLG_VT, slot0, KLLG_SLOT0); kllg_on = 0; return; }
    tab = (DWORD *)VirtualAlloc(0, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!tab) { klog("listguard: no memory for the vtable copy: off"); kllg_on = 0; return; }
    for (i = 0; i < KLLG_VT_MAX; i++) tab[i] = klh_rd32((DWORD_PTR)KLH_VA(KLLG_VT) + 4 * i);
    len = kllg_vt_len(tab, KLLG_VT_MAX, tl, th);
    if (len < 1) { klog("listguard: vtable copy empty: off"); kllg_on = 0; return; }
    kllg_orig = (KLLG_FN)(DWORD_PTR)slot0;
    tab[0] = (DWORD)(DWORD_PTR)kllg_wrap;
    kllg_vt = tab;
    klog("listguard: ListUserGuard on (private vtable of %d slots, slot 0 0x%08x -> wrapper, catches only c0000005 inside 0x%08x..0x%08x)", len, slot0, kllg_lo, kllg_hi);
}

static void kllg_tick(int game_thread)
{
    static DWORD last; DWORD now = GetTickCount(); char scene[160]; int i;
    if (!kllg_on || !game_thread) return;
    if (now - last < 250) return;
    last = now;
    if (InterlockedCompareExchange(&kllg_done, 0, 1) == 1) {                 /* results of a scan: repoint what still has the original vptr */
        for (i = 0; i < kllg_ncand; i++) {
            DWORD at = kllg_cand[i], nv = (DWORD)(DWORD_PTR)kllg_vt;
            if (klh_rd32(at) != KLLG_VT || !klh_rd32(at + 0x20)) continue;      /* re-check the layout at write time (block freed/reused since the scan) */
            if (klh_data((void *)(DWORD_PTR)at, &nv, 4, "listguard: CListUser vptr (private vtable)")) {
                kllg_patched++;
                if (kllg_log) klog("listguard: CListUser object at 0x%08x now uses the guarded vtable (%d patched, scan %d)", at, kllg_patched, kllg_scans);
            }
        }
    }
    if (klh_scene(scene, sizeof scene) && strcmp(scene, kllg_scene)) {      /* a new scene: scan again soon */
        snprintf(kllg_scene, sizeof kllg_scene, "%s", scene);
        kllg_next = now + kllg_next_delay(0); kllg_step = 1;
    }
    if (kllg_scene[0] && !kllg_busy && (int)(now - kllg_next) >= 0 && kllg_next) {
        HANDLE h;
        InterlockedExchange(&kllg_busy, 1); kllg_scans++;
        h = CreateThread(0, 0, kllg_scan_thread, 0, 0, 0);
        if (h) CloseHandle(h); else InterlockedExchange(&kllg_busy, 0);
        kllg_next = now + kllg_next_delay(kllg_step); if (kllg_step < 4) kllg_step++;
        if (!kllg_next) kllg_next = 1;
    }
}
