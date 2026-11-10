/*
 * klmemfree.c - [Memory] Release: give address space back after a level is gone, and say who holds the rest. Part of KLHook
 * (included by klhook.c, SHIP and TEST alike, AFTER klmem.c / klarena.c). Import slots and data only: no code byte of kl2.exe
 * changes; it calls documented Win32 functions on the heaps of the process.
 *
 * WHY (owner, 2026-11-10: 'late night opening gray screen after a few games'). KLHook.log of that session: after ONE match
 * (DD10) back at the menu the next load (DM05A, 00:23:35) found 476 MB free but the largest piece 24.9 MB, 0 pieces of 64 MB,
 * 'private reserved only 919 MB'; HeapAlloc 32 MB and 24 MB were refused (served from klmem's reserve); at 00:27:14 DM06B ran at
 * 1.4 fps for 40 s (VA starvation: the driver's allocations fail, the picture stays gray). The map file of that moment
 * (KLHook_map_refused_0.txt, run through the census here) says WHO: 28 allocations of 15.81 MB = NT heap segments with
 * 14-40 committed islands each (443 MB reserved, 58 MB committed); 47 thread stacks of 4 MB (188 MB, 6.5 MB committed); five
 * 32 MB blocks (146 MB reserved only); the klmem reserve (128 MB, held on purpose). See klmemfree_logic.h.
 *
 * WHAT IT DOES (every part a toggle)
 *  1. CENSUS (Census=1, log only). At every release (and once at the first start of a level) one line splits the private
 *     address space into: klmem's reserve, NT heap segments (found by the segment header, verified against GetProcessHeaps),
 *     thread stacks (guard page), other big blocks, other; for heap segments how many are 'sparse' (under 1 MB committed:
 *     mostly empty reservations; whether a live block sits in them is not told by the census). A second line before/after the release shows what it gained.
 *  2. RELEASE (Release=1), SettleMS (3000) after the level is gone (scene key left the Locations folder / the level's big
 *     block - the .prm in klmem's reserve - was freed by the game), at most once per CooldownMS (20000), on a short-lived
 *     worker thread (the game thread is not stopped): for every heap of GetProcessHeaps
 *       a. HeapCompact: coalesces free blocks and decommits big free ones. MEASURED (klmemfree_test.c, Windows 10 19045): it
 *          does NOT release a segment's ADDRESS SPACE, not even for an entirely free heap (347.1 -> 347.1 MB reserved);
 *          only the committed memory falls. So the gain in largest free piece is ~0: honest limit of this clean-up;
 *       b. HeapSetInformation(HeapOptimizeResources) (Windows 8.1+, ignored where missing): the OS's own 'trim the low-fragmentation
 *          heap and decommit' request.
 *     What it can NOT do: free a segment that still holds a live block (the engine's and the driver's long-lived small blocks
 *     sit in them) - that address space comes back only if those blocks never land there: [Memory] DriverArena=1 (klarena.c)
 *     keeps the driver's burst of ~2.8 KB blocks off the process heap in the first place. This file is the clean-up and the
 *     measurement, DriverArena is the cause. Both are 'recommended on'.
 *
 * KLHook.ini
 *   [Memory]
 *   Release=1        (recommended on) compact + optimize the process's heaps once the level is gone
 *   Compact=1        (recommended on) HeapCompact on every heap
 *   Optimize=1       (recommended on) HeapSetInformation(HeapOptimizeResources) on every heap
 *   Census=1         (recommended on) the owner census lines 'memfree:' (a few lines per level, even with [Memory] Log=0)
 *   SettleMS=3000    wait this long after the level is gone before releasing (the engine frees asynchronously)
 *   CooldownMS=20000 not more often than this
 */
#ifndef KLMEMFREE_C
#define KLMEMFREE_C

#include "klmemfree_logic.h"

#define KLMR_MAXHEAPS 64
static int klmr_on = 0, klmr_census_on = 1, klmr_compact = 1, klmr_optimize = 1, klmr_active;   /* klmr_active: Release or Census asked for */
static unsigned klmr_settle = 3000, klmr_cool = 20000;
static volatile LONG klmr_busy, klmr_runs;
static struct klmr_trig klmr_t;

struct klmr_tot {
    size_t free_total, free_largest; int free64, free16;
    size_t image, mapped, p_commit, p_rsv;
    struct { int n; size_t size, commit; } cls[KLMR_NCLS];
    int pinned; size_t pinned_size;                       /* heap segments under 1 MB committed */
    int nheaps;
};

static int klmr_heaps(uintptr_t *out)
{
    HANDLE h[KLMR_MAXHEAPS]; DWORD n = GetProcessHeaps(KLMR_MAXHEAPS, h), i;
    if (n > KLMR_MAXHEAPS) n = KLMR_MAXHEAPS;
    for (i = 0; i < n; i++) out[i] = (uintptr_t)h[i];
    return (int)n;
}

static void klmr_close(struct klmr_tot *t, struct klmr_group *g, const uintptr_t *heaps, int nh)
{   /* the allocation in hand is complete: read its header when it could be a heap segment, classify, add */
    int c;
    if (!g->base) return;
    g->is_reserve = klm_reserve && (const void *)g->base == klm_reserve;
    if (!g->is_reserve && !g->guard && g->size >= ((size_t)1 << 20) && g->size <= ((size_t)64 << 20)) {
        unsigned char hdr[0x20]; SIZE_T got = 0;
        if (ReadProcessMemory(GetCurrentProcess(), (LPCVOID)g->base, hdr, sizeof hdr, &got) && got == sizeof hdr) g->is_seg = klmr_seg_hdr(hdr, heaps, nh);
    }
    c = klmr_classify(g);
    t->cls[c].n++; t->cls[c].size += g->size; t->cls[c].commit += g->commit;
    if (c == KLMR_HEAPSEG && g->commit < ((size_t)1 << 20)) { t->pinned++; t->pinned_size += g->size; }
}

static void klmr_census(struct klmr_tot *t)
{   /* one walk over the user half of the address space */
    MEMORY_BASIC_INFORMATION mbi; BYTE *p = (BYTE *)0x10000; struct klmr_group g; uintptr_t heaps[KLMR_MAXHEAPS]; int nh = klmr_heaps(heaps);
    memset(t, 0, sizeof *t); memset(&g, 0, sizeof g); t->nheaps = nh;
    for (;;) {
        int more = p < (BYTE *)0x7ffe0000 && VirtualQuery(p, &mbi, sizeof mbi);
        if (!more || mbi.State == MEM_FREE || mbi.Type != MEM_PRIVATE || (uintptr_t)mbi.AllocationBase != g.base) {
            klmr_close(t, &g, heaps, nh); memset(&g, 0, sizeof g);
        }
        if (!more) break;
        if (mbi.State == MEM_FREE) {
            t->free_total += mbi.RegionSize; if (mbi.RegionSize > t->free_largest) t->free_largest = mbi.RegionSize;
            if (mbi.RegionSize >= ((size_t)64 << 20)) t->free64++; else if (mbi.RegionSize >= ((size_t)16 << 20)) t->free16++;
        } else if (mbi.Type == MEM_IMAGE) t->image += mbi.RegionSize;
        else if (mbi.Type == MEM_MAPPED) t->mapped += mbi.RegionSize;
        else {
            g.base = (uintptr_t)mbi.AllocationBase; g.size += mbi.RegionSize;
            if (mbi.State == MEM_COMMIT) { g.commit += mbi.RegionSize; t->p_commit += mbi.RegionSize; if (mbi.Protect & PAGE_GUARD) g.guard = 1; }
            else t->p_rsv += mbi.RegionSize;
        }
        p = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
}

static void klmr_log_census(const char *when, const struct klmr_tot *t)
{
    int i; char who[400]; int n = 0;
    for (i = 0; i < KLMR_NCLS && n >= 0 && n < (int)sizeof who - 90; i++) {
        int k = _snprintf(who + n, sizeof who - n, "%s%s %d (%.0f MB, %.0f committed)", i ? "; " : "", klmr_cls_name[i], t->cls[i].n, klmr_mb(t->cls[i].size), klmr_mb(t->cls[i].commit));
        if (k < 0) break;
        n += k;
    }
    who[sizeof who - 1] = 0;
    klog("memfree: %s: free %.0f MB, largest piece %.1f MB, pieces of 64 MB+ %d, 16-64 MB %d; private reserved only %.0f MB, committed %.0f MB; modules %.0f, mapped %.0f; "
         "%s; sparse heap segments (under 1 MB committed) %d = %.0f MB of address space; %d heap(s)",
         when, klmr_mb(t->free_total), klmr_mb(t->free_largest), t->free64, t->free16, klmr_mb(t->p_rsv), klmr_mb(t->p_commit), klmr_mb(t->image), klmr_mb(t->mapped),
         who, t->pinned, klmr_mb(t->pinned_size), t->nheaps);
}

static void klmr_release_heaps(int *compacted, int *optimized)
{   /* the actions on every heap of the process; the worker thread's job */
    uintptr_t heaps[KLMR_MAXHEAPS]; int n = klmr_heaps(heaps), i;
    BOOL (WINAPI *hsi)(HANDLE, int, PVOID, SIZE_T) = (BOOL (WINAPI *)(HANDLE, int, PVOID, SIZE_T))GetProcAddress(GetModuleHandleA("kernel32.dll"), "HeapSetInformation");
    struct { ULONG Version, Flags; } opt = { 1, 0 };
    *compacted = *optimized = 0;
    for (i = 0; i < n; i++) {
        if (klmr_compact && HeapCompact((HANDLE)heaps[i], 0) != 0) (*compacted)++;
        if (klmr_optimize && hsi && hsi((HANDLE)heaps[i], 3 /* HeapOptimizeResources */, &opt, sizeof opt)) (*optimized)++;
    }
}

struct klmr_job { const char *why; int release; };
static struct klmr_job klmr_job;                                  /* one at a time (klmr_busy), so one slot */

static DWORD WINAPI klmr_worker(LPVOID unused)
{
    struct klmr_tot a, b; int comp = 0, opt = 0; DWORD t0 = GetTickCount(), t1; double r0, r1;
    const char *why = klmr_job.why; int rel = klmr_job.release && klmr_on;
    (void)unused;
    if (klmr_census_on) { klmr_census(&a); klmr_log_census("before the release", &a); }
    else memset(&a, 0, sizeof a);
    if (rel) klmr_release_heaps(&comp, &opt);
    t1 = GetTickCount() - t0;
    if (klmr_census_on) {
        klmr_census(&b); klmr_log_census("after the release", &b);
        r0 = klmr_mb(a.p_rsv); r1 = klmr_mb(b.p_rsv);
        klog("memfree: %s: %s in %lu ms (HeapCompact on %d, HeapOptimizeResources on %d of %d heaps); private reserved only %.0f -> %.0f MB (%+.0f), largest free piece %.1f -> %.1f MB, "
             "heap segments %d -> %d, committed %.0f -> %.0f MB; the klmem reserve holds %d block(s), %.1f of %d MB",
             why, rel ? "released" : "census only", (unsigned long)t1, comp, opt, b.nheaps, r0, r1, r1 - r0,
             klmr_mb(a.free_largest), klmr_mb(b.free_largest), a.cls[KLMR_HEAPSEG].n, b.cls[KLMR_HEAPSEG].n, klmr_mb(a.p_commit), klmr_mb(b.p_commit),
             klm_n, klm_used / 1048576.0, klm_reserve ? klm_reserve_mb : 0);
    } else klog("memfree: %s: released in %lu ms (HeapCompact on %d, HeapOptimizeResources on %d heaps)", why, (unsigned long)t1, comp, opt);
    InterlockedExchange(&klmr_busy, 0);
    return 0;
}

static void klmr_start(const char *why, int release)
{
    HANDLE h;
    if (InterlockedCompareExchange(&klmr_busy, 1, 0)) return;       /* one at a time */
    InterlockedIncrement(&klmr_runs);
    klmr_job.why = why; klmr_job.release = release;
    h = CreateThread(0, 128 << 10, klmr_worker, 0, STACK_SIZE_PARAM_IS_A_RESERVATION, 0);
    if (h) CloseHandle(h); else { InterlockedExchange(&klmr_busy, 0); klog("memfree: the worker thread could not be started"); }
}

static void klmr_tick(void)
{   /* game thread, called every frame like klm_tick: cheap until 500 ms have passed */
    static DWORD last; static int told; DWORD now; char scene[260], key[200]; int in_level;
    if (!klmr_active) return;
    now = GetTickCount();
    if ((DWORD)(now - last) < 500) return;
    last = now;
    in_level = klh_scene(scene, sizeof scene) && klh_level_key(scene, key, sizeof key);
    if (in_level && !told && klmr_census_on) { told = 1; klmr_start("a level is loaded", 0); }       /* the first census, for the log: what the level starts with */
    if (!in_level) told = 0;
    if (klmr_trig_step(&klmr_t, in_level, klm_prm_freed, now, klmr_settle, klmr_cool) && (klmr_on || klmr_census_on)) klmr_start("the level is gone", 1);
}

static void klmr_init(void)
{
    if (!GetPrivateProfileIntA("Memory", "Enable", 1, klh_ini)) return;
    klmr_on = GetPrivateProfileIntA("Memory", "Release", 0, klh_ini) != 0;
    klmr_compact = GetPrivateProfileIntA("Memory", "Compact", 1, klh_ini) != 0;
    klmr_optimize = GetPrivateProfileIntA("Memory", "Optimize", 1, klh_ini) != 0;
    klmr_census_on = GetPrivateProfileIntA("Memory", "Census", 1, klh_ini) != 0;
    klmr_settle = (unsigned)GetPrivateProfileIntA("Memory", "SettleMS", 3000, klh_ini); if (klmr_settle > 60000) klmr_settle = 3000;
    klmr_cool = (unsigned)GetPrivateProfileIntA("Memory", "CooldownMS", 20000, klh_ini); if (klmr_cool < 1000 || klmr_cool > 600000) klmr_cool = 20000;
    klmr_active = klmr_on || klmr_census_on;
    klog("memfree: Release %s (Compact %s, Optimize %s), Census %s, settle %u ms, cooldown %u ms", klmr_on ? "on" : "off", klmr_compact ? "on" : "off", klmr_optimize ? "on" : "off",
         klmr_census_on ? "on" : "off", klmr_settle, klmr_cool);
}

#endif /* KLMEMFREE_C */
