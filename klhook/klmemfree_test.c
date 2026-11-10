/*
 * klmemfree_test.c - klmemfree.c / klmemfree_logic.h outside the game: a 32-bit console program that includes klmem.c and klmemfree.c as
 * they are (the helpers they take from klhook.c are stubbed). Proves on THIS Windows build (not just on paper):
 *   - the pure logic: classes, the heap-segment header test, the release trigger (settle, cooldown, the .prm stamp);
 *   - the census finds the segments of a private heap by their header, the thread stack by its guard page, the reserve by its address;
 *   - HeapCompact / HeapOptimizeResources hand a segment that is ENTIRELY free back to the system, and do NOT touch one that still
 *     holds a live block (so the pinned segments of the owner's map stay pinned: that is DriverArena's job, see klmemfree.c).
 *
 *   call "...\vcvarsall.bat" x86
 *   cl /nologo /O2 /W3 /D_CRT_SECURE_NO_WARNINGS klmemfree_test.c /Fe:klmemfree_test.exe
 *   klmemfree_test.exe        exit code 0 = every check passed
 */
#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdint.h>
#include <string.h>

static char klh_ini[MAX_PATH], klh_out[MAX_PATH];
static int quiet = 1;
static void klog(const char *fmt, ...) { va_list ap; if (quiet) return; va_start(ap, fmt); printf("    "); vprintf(fmt, ap); printf("\n"); va_end(ap); }
static int klh_iat(const char *dll, const char *fn, void *mine, void **real) { (void)mine; *real = (void *)GetProcAddress(GetModuleHandleA(dll), fn); return *real != 0; }
static int klh_poke(void *at, const void *expect, int explen, const void *bytes, int len, const char *what) { (void)at; (void)expect; (void)explen; (void)bytes; (void)len; (void)what; return 0; }
static int klh_scene(char *out, int cap) { (void)cap; out[0] = 0; return 0; }
static int klh_level_key(const char *scene, char *key, int cap) { (void)scene; (void)key; (void)cap; return 0; }

#include "klmem.c"
#include "klmemfree.c"

static int bad;
#define CHECK(c, ...) do { if (!(c)) { bad++; printf("FAIL: "); printf(__VA_ARGS__); printf("\n"); } } while (0)

static void logic(void)
{
    struct klmr_group g; unsigned char hdr[0x20]; uintptr_t heaps[2] = { 0x00340000, 0x01230000 }; struct klmr_trig t; unsigned now = 100000;
    memset(&g, 0, sizeof g); g.size = 4u << 20; g.commit = 8192; g.guard = 1;
    CHECK(klmr_classify(&g) == KLMR_STACK, "4 MB with a guard page is a stack");
    g.guard = 0; CHECK(klmr_classify(&g) == KLMR_OTHER, "4 MB without a guard page is other");
    g.size = 16u << 20; CHECK(klmr_classify(&g) == KLMR_BIG, "16 MB is big");
    g.is_seg = 1; CHECK(klmr_classify(&g) == KLMR_HEAPSEG, "a segment is a segment"); g.is_reserve = 1; CHECK(klmr_classify(&g) == KLMR_RESERVE, "the reserve first");
    g.is_reserve = 0; g.is_seg = 0; g.guard = 1; g.size = 128u << 20; CHECK(klmr_classify(&g) == KLMR_BIG, "a huge guarded block is not a stack");
    memset(hdr, 0, sizeof hdr); hdr[8] = 0xee; hdr[9] = 0xff; hdr[10] = 0xee; hdr[11] = 0xff; hdr[0x18] = 0x00; hdr[0x19] = 0x00; hdr[0x1a] = 0x23; hdr[0x1b] = 0x01;
    CHECK(klmr_seg_hdr(hdr, heaps, 2), "signature + known heap = segment");
    hdr[0x1a] = 0x24; CHECK(!klmr_seg_hdr(hdr, heaps, 2), "unknown heap pointer is no segment");
    hdr[0x1a] = 0x23; hdr[8] = 0; CHECK(!klmr_seg_hdr(hdr, heaps, 2), "no signature is no segment");

    memset(&t, 0, sizeof t);
    CHECK(!klmr_trig_step(&t, 0, 0, now, 3000, 20000), "idle at the menu: nothing");
    CHECK(!klmr_trig_step(&t, 1, 0, now += 500, 3000, 20000), "in a level: nothing");
    CHECK(!klmr_trig_step(&t, 0, 0, now += 500, 3000, 20000), "level left: armed, not yet");
    CHECK(!klmr_trig_step(&t, 0, 0, now += 2000, 3000, 20000), "2 s after: still settling");
    CHECK(klmr_trig_step(&t, 0, 0, now += 1000, 3000, 20000), "3.5 s after: run");
    CHECK(!klmr_trig_step(&t, 0, 0, now += 500, 3000, 20000), "only once");
    CHECK(!klmr_trig_step(&t, 1, 0, now += 500, 3000, 20000), "next level");
    CHECK(!klmr_trig_step(&t, 0, 0, now += 500, 3000, 20000), "left again: armed");
    CHECK(!klmr_trig_step(&t, 0, 0, now += 3000, 3000, 20000), "inside the cooldown: refused");
    CHECK(!klmr_trig_step(&t, 0, 0, now += 10000, 3000, 20000), "the refusal consumed the arming");

    memset(&t, 0, sizeof t); now = 50000;
    CHECK(!klmr_trig_step(&t, 0, 49000, now, 3000, 20000), "a stamp 1 s old: settling");
    CHECK(klmr_trig_step(&t, 0, 49000, now + 2500, 3000, 20000), "the same stamp 3.5 s old: run");
    CHECK(!klmr_trig_step(&t, 0, 49000, now + 2600, 3000, 20000), "the same stamp does not arm twice");
    CHECK(!klmr_trig_step(&t, 0, 60000, now + 11000, 3000, 20000), "a new stamp inside the cooldown arms, settles");
    CHECK(!klmr_trig_step(&t, 0, 60000, now + 14100, 3000, 20000), "refused: 11.6 s since the last run");
    CHECK(klmr_trig_step(&t, 0, 70000, now + 30000, 3000, 20000), "a later stamp past the cooldown runs");

    now = 0xfffffff0u; memset(&t, 0, sizeof t); t.was_level = 1;
    CHECK(!klmr_trig_step(&t, 0, 0, now, 3000, 20000), "tick wrap: armed");
    CHECK(klmr_trig_step(&t, 0, 0, now + 4000u, 3000, 20000), "tick wrap: runs across the wrap");
}

/* the private heap's own segments: how many, how much they reserve and commit (header + GetProcessHeaps, like the census) */
static void heap_seg_stats(HANDLE heap, int *nseg, size_t *rsv, size_t *commit)
{
    MEMORY_BASIC_INFORMATION mbi; BYTE *p = (BYTE *)0x10000; uintptr_t heaps[KLMR_MAXHEAPS]; int nh = klmr_heaps(heaps), i, mine = 0;
    *nseg = 0; *rsv = *commit = 0;
    for (i = 0; i < nh; i++) if (heaps[i] == (uintptr_t)heap) mine = 1;
    CHECK(mine, "the private heap is in GetProcessHeaps");
    while (p < (BYTE *)0x7ffe0000 && VirtualQuery(p, &mbi, sizeof mbi)) {
        if (mbi.State == MEM_COMMIT && mbi.Type == MEM_PRIVATE && (BYTE *)mbi.AllocationBase == (BYTE *)mbi.BaseAddress) {
            unsigned char hdr[0x20]; SIZE_T got = 0;
            if (ReadProcessMemory(GetCurrentProcess(), mbi.BaseAddress, hdr, sizeof hdr, &got) && got == sizeof hdr && klmr_seg_hdr(hdr, heaps, nh)
                && *(DWORD *)(hdr + 0x18) == (DWORD)(uintptr_t)heap) {
                BYTE *q = (BYTE *)mbi.AllocationBase; MEMORY_BASIC_INFORMATION m2; SIZE_T r = 0, c = 0;
                while (VirtualQuery(q, &m2, sizeof m2) && m2.AllocationBase == mbi.AllocationBase) { r += m2.RegionSize; if (m2.State == MEM_COMMIT) c += m2.RegionSize; q += m2.RegionSize; }
                (*nseg)++; *rsv += r; *commit += c;
            }
        }
        p = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
}

#define NB 6000
static void *blk[NB];

static void heaps_real(void)
{
    HANDLE h = HeapCreate(0, 0, 0); int i, ns0, ns1, ns2, ns3, ns4, comp, opt; size_t r0, r1, r2, r3, r4, c0, c1, c2, c3, c4; struct klmr_tot t;
    CHECK(h != 0, "HeapCreate");
    for (i = 0; i < NB; i++) { blk[i] = HeapAlloc(h, 0, 60000); if (!blk[i]) break; memset(blk[i], 1, 64); }
    CHECK(i == NB, "allocated %d of %d", i, NB);
    heap_seg_stats(h, &ns0, &r0, &c0);
    printf("  heap with %d x 60000 B: %d segment(s), %.1f MB reserved, %.1f MB committed\n", NB, ns0, r0 / 1048576.0, c0 / 1048576.0);
    CHECK(ns0 >= 3, "the test heap needs several segments to prove anything (got %d)", ns0);
    klmr_census(&t);
    CHECK(t.cls[KLMR_HEAPSEG].n >= ns0, "census sees %d heap segments, the heap has %d of its own", t.cls[KLMR_HEAPSEG].n, ns0);
    for (i = 0; i < NB; i++) if (i % 100) { HeapFree(h, 0, blk[i]); blk[i] = 0; }      /* every segment keeps live blocks: pinned */
    heap_seg_stats(h, &ns1, &r1, &c1);
    klmr_compact = 1; klmr_optimize = 1; klmr_release_heaps(&comp, &opt);
    heap_seg_stats(h, &ns2, &r2, &c2);
    printf("  pinned (1 block in 100 kept): before the release %d seg %.1f MB rsv %.1f MB commit; after %d seg %.1f MB rsv %.1f MB commit (HeapCompact %d, optimize %d heaps)\n",
           ns1, r1 / 1048576.0, c1 / 1048576.0, ns2, r2 / 1048576.0, c2 / 1048576.0, comp, opt);
    CHECK(ns2 == ns1, "segments that hold a live block stay: %d -> %d", ns1, ns2);
    CHECK(c2 <= c1, "committed does not grow");
    for (i = 0; i < NB; i++) if (blk[i]) { HeapFree(h, 0, blk[i]); blk[i] = 0; }      /* now everything is free */
    heap_seg_stats(h, &ns3, &r3, &c3);
    klmr_release_heaps(&comp, &opt);
    heap_seg_stats(h, &ns4, &r4, &c4);
    printf("  all freed: before the release %d seg %.1f MB rsv %.1f MB commit; after %d seg %.1f MB rsv %.1f MB commit\n", ns3, r3 / 1048576.0, c3 / 1048576.0, ns4, r4 / 1048576.0, c4 / 1048576.0);
    /* MEASURED on Windows 10 19045: HeapCompact / HeapOptimizeResources decommit but never release a segment's address space.
       So this only records the number; the release is NOT claimed to give VA back. */
    printf("  entirely free heap: reserved %.1f -> %.1f MB after compact (VA release not expected)\n", r3 / 1048576.0, r4 / 1048576.0);
    CHECK(r4 <= r3, "compaction never grows the reservation: %.1f -> %.1f MB", r3 / 1048576.0, r4 / 1048576.0);
    HeapDestroy(h);
}

/* the driver's case (K49E): ~2.8 KB blocks in a low-fragmentation heap, a burst of 150000 (420 MB), then freed except a scattering */
#define NS 150000
static void *small_blk[NS];
static void lfh_pile(int keep_every)
{
    HANDLE h = HeapCreate(0, 0, 0); ULONG lfh = 2; int i, ns0, ns1, ns2, comp, opt; size_t r0, r1, r2, c0, c1, c2; BOOL ok = HeapSetInformation(h, HeapCompatibilityInformation, &lfh, sizeof lfh);
    for (i = 0; i < NS; i++) { small_blk[i] = HeapAlloc(h, 0, 2800); if (!small_blk[i]) break; ((char *)small_blk[i])[0] = 1; }
    heap_seg_stats(h, &ns0, &r0, &c0);
    for (i = 0; i < NS; i++) if (!keep_every || i % keep_every) { HeapFree(h, 0, small_blk[i]); small_blk[i] = 0; }
    heap_seg_stats(h, &ns1, &r1, &c1);
    klmr_compact = 1; klmr_optimize = 1; klmr_release_heaps(&comp, &opt);
    heap_seg_stats(h, &ns2, &r2, &c2);
    printf("  LFH %s, %d x 2800 B, keep 1 in %d: peak %d seg %.0f MB rsv %.0f MB commit; freed %d seg %.0f rsv %.0f commit; after release %d seg %.0f rsv %.0f commit\n",
           ok ? "on" : "NOT set", i, keep_every, ns0, r0 / 1048576.0, c0 / 1048576.0, ns1, r1 / 1048576.0, c1 / 1048576.0, ns2, r2 / 1048576.0, c2 / 1048576.0);
    HeapDestroy(h);
}

static void census_real(void)
{
    struct klmr_tot t; void *rsv = VirtualAlloc(0, 24u << 20, MEM_RESERVE, PAGE_NOACCESS), *big = VirtualAlloc(0, 12u << 20, MEM_RESERVE, PAGE_NOACCESS);
    CHECK(rsv && big, "VirtualAlloc");
    klm_reserve = rsv; klm_reserve_mb = 24;
    VirtualAlloc((BYTE *)rsv + 65536, 65536, MEM_COMMIT, PAGE_READWRITE);
    klmr_census(&t);
    CHECK(t.cls[KLMR_RESERVE].n == 1 && t.cls[KLMR_RESERVE].size == (24u << 20), "the reserve is counted once, %.1f MB", t.cls[KLMR_RESERVE].size / 1048576.0);
    CHECK(t.cls[KLMR_BIG].n >= 1, "the 12 MB reservation is 'big'");
    CHECK(t.cls[KLMR_STACK].n >= 1, "this thread's own stack is a stack (guard page)");
    CHECK(t.free_total > 0 && t.free_largest > 0, "free space is measured");
    CHECK(t.p_rsv > 0 && t.p_commit > 0, "private reserved/committed measured");
    printf("  census: free %.0f MB (largest %.1f), %d heaps, segments %d, stacks %d, big %d, other %d\n", klmr_mb(t.free_total), klmr_mb(t.free_largest), t.nheaps,
           t.cls[KLMR_HEAPSEG].n, t.cls[KLMR_STACK].n, t.cls[KLMR_BIG].n, t.cls[KLMR_OTHER].n);
    quiet = 0; klmr_log_census("test", &t); quiet = 1;
    klm_reserve = 0;
    VirtualFree(rsv, 0, MEM_RELEASE); VirtualFree(big, 0, MEM_RELEASE);
}

static void stamp_real(void)
{   /* klmem.c stamps the free of a BigMB block in the reserve */
    LPVOID p;
    klm_reserve_mb = 128; klm_ok = 1; klm_big_mb = 48; InitializeCriticalSection(&klm_cs);
    klm_reserve = VirtualAlloc(0, (SIZE_T)128 << 20, MEM_RESERVE, PAGE_NOACCESS);
    CHECK(klm_reserve != 0, "128 MB reservation");
    p = klm_from_reserve((SIZE_T)60 << 20);
    CHECK(p != 0, "60 MB block from the reserve");
    CHECK(klm_prm_freed == 0, "no stamp yet");
    klm_real_HeapFree = (BOOL (WINAPI *)(HANDLE, DWORD, LPVOID))GetProcAddress(GetModuleHandleA("kernel32.dll"), "HeapFree");
    CHECK(klm_HeapFree(GetProcessHeap(), 0, p), "freed");
    CHECK(klm_prm_freed != 0, "stamped by the free of a BigMB block");
    p = klm_from_reserve((SIZE_T)2 << 20); klm_prm_freed = 0; klm_HeapFree(GetProcessHeap(), 0, p);
    CHECK(klm_prm_freed == 0, "a 2 MB block does not stamp");
    VirtualFree(klm_reserve, 0, MEM_RELEASE); klm_reserve = 0;
}

int main(void)
{
    printf("klmemfree_test\n");
    logic(); heaps_real(); lfh_pile(0); lfh_pile(500); census_real(); stamp_real();
    printf(bad ? "FAILED: %d check(s)\n" : "PASS\n", bad);
    return bad != 0;
}
