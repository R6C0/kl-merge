/*
 * klhigh_test.c - klhigh.c's high half outside the game: a 32-bit console program WITH the large-address flag that
 * includes klhigh.c as it is (the helpers it takes from klhook.c are stubbed here), takes the upper 2 GB, lists ITSELF
 * as the foreign module (its own import slots of VirtualAlloc / VirtualFree are what gets wrapped) and checks:
 *   1. after the takeover a plain VirtualAlloc from "the game" (through the stubbed real pointer) is below 2 GB;
 *   2. a reservation through the wrapped import slot lands above 2 GB, commits, is writable, and MEM_RELEASE through
 *      the slot gives the pages back (the bookkeeping agrees, a second carve reuses the hole);
 *   3. an explicit address, a plain commit inside a carved block, a decommit, odd flags and a release of a non-start
 *      address are answered as Windows answers them;
 *   4. High=1 (measure) counts and places nothing above 2 GB.
 *   5. (review 2026-10-25) MEM_COMMIT alone is a new block and goes high; a size-0 MEM_DECOMMIT of the block at a
 *      chunk's start decommits THAT block only (its neighbour stays committed); nothing above 2 GB is free afterwards.
 * It proves the arena's bookkeeping, NOT that the game or the driver are content with where their blocks live.
 *
 *   call "...\vcvarsall.bat" x86
 *   cl /nologo /O2 /W3 /D_CRT_SECURE_NO_WARNINGS klhigh_test.c /Fe:klhigh_test.exe /link /LARGEADDRESSAWARE
 *   klhigh_test.exe            exit code 0 = every check passed
 * MinGW: i686-w64-mingw32-gcc -O2 -o klhigh_test.exe klhigh_test.c -Wl,--large-address-aware
 * Written 2026-10-25 (scheduled check-in); compiled with MinGW, NOT YET RUN on Windows.
 */
#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>

static DWORD img_lo;                                            /* klhigh.c reads the 4 GB flag from this image: here, our own */
static char klh_ini[MAX_PATH];
static int fails;

static void klog(const char *fmt, ...) { va_list ap; va_start(ap, fmt); printf("    "); vprintf(fmt, ap); printf("\n"); va_end(ap); }
#define CHECK(c, ...) do { if (c) printf("ok    " __VA_ARGS__); else { fails++; printf("FAIL  " __VA_ARGS__); } printf("\n"); } while (0)

#include "klhigh.c"

/* calls that go through THIS module's import slots (wrapped once this exe is listed) */
static LPVOID via_slot_alloc(LPVOID a, SIZE_T s, DWORD t, DWORD p) { return VirtualAlloc(a, s, t, p); }
static BOOL via_slot_free(LPVOID a, SIZE_T s, DWORD t) { return VirtualFree(a, s, t); }

static void write_ini(int mode, const char *leaf)
{
    FILE *f;
    GetModuleFileNameA(0, klh_ini, sizeof klh_ini); strcpy(strrchr(klh_ini, '\\') + 1, "klhigh_test.ini");
    f = fopen(klh_ini, "w");
    fprintf(f, "[Memory]\nHigh=%d\nHighModules=%s\nHighCount=d3d9.dll\nHighLog=1\n", mode, leaf);
    fclose(f);
}

int main(void)
{
    char path[MAX_PATH], *leaf; BYTE *p, *q, *r; MEMORY_BASIC_INFORMATION mbi; klvh_mod *me; SIZE_T carved0;
    img_lo = (DWORD)(DWORD_PTR)GetModuleHandleA(0);
    GetModuleFileNameA(0, path, sizeof path); leaf = strrchr(path, '\\') + 1;
    printf("klhigh_test: %s, 4 GB flag %s\n", leaf, klvh_flag_on() ? "ON" : "OFF (link with /LARGEADDRESSAWARE)");
    if (!klvh_flag_on()) return 2;

    /* ---- High=2 */
    write_ini(2, leaf);
    klvh_init();
    CHECK(klvh_placing && klvh_nchunk > 0, "placing: %d chunk(s), %.0f MB above 2 GB", klvh_nchunk, klvh_high_total / 1048576.0);
    CHECK(klvh_high_total >= (SIZE_T)1536 << 20, "at least 1.5 GB of the high half is ours (%.0f MB)", klvh_high_total / 1048576.0);
    me = klvh_find(leaf);
    CHECK(me && me->base == GetModuleHandleA(0) && me->slots >= 2, "this exe is listed and %d of its import slots are wrapped", me ? me->slots : 0);

    /* 1. the game's own allocation stays low */
    p = (BYTE *)klvh_real_VirtualAlloc(0, 1 << 20, MEM_RESERVE | MEM_TOP_DOWN, PAGE_NOACCESS);
    CHECK(p && (DWORD_PTR)p < KLVH_BASE, "a top-down reservation by the game lands below 2 GB (%p)", p);
    if (p) klvh_real_VirtualFree(p, 0, MEM_RELEASE);

    /* 2. a foreign reservation goes high, commits, writes, releases */
    carved0 = klvh_carved;
    q = (BYTE *)via_slot_alloc(0, 3 << 20, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    CHECK(q && (DWORD_PTR)q >= KLVH_BASE, "reserve+commit 3 MB through the slot -> high half (%p)", q);
    if (q) { memset(q, 0x5a, 3 << 20); CHECK(q[0] == 0x5a && q[(3 << 20) - 1] == 0x5a, "the 3 MB are writable end to end"); }
    CHECK(klvh_carved == carved0 + (3 << 20) && me->held_n == 1 && me->high == (3 << 20), "bookkeeping: carved %.1f MB, held %ld, high %.1f MB", klvh_carved / 1048576.0, me->held_n, me->high / 1048576.0);
    r = (BYTE *)via_slot_alloc(0, 1 << 20, MEM_RESERVE, PAGE_NOACCESS);
    CHECK(r && (DWORD_PTR)r >= KLVH_BASE && r != q, "a second, reserve-only block -> high half (%p)", r);
    CHECK(VirtualQuery(r, &mbi, sizeof mbi) && mbi.State == MEM_RESERVE, "it is reserved, not committed");
    /* 3. commit inside it, decommit, odd answers */
    CHECK(via_slot_alloc(r + 0x10000, 0x1000, MEM_COMMIT, PAGE_READWRITE) == r + 0x10000, "a plain commit inside the carved block is Windows' business");
    r[0x10000] = 1;
    CHECK(via_slot_free(r + 0x10000, 0x1000, MEM_DECOMMIT), "and so is the decommit");
    CHECK(!via_slot_free(r + 0x10000, 0, MEM_RELEASE) && GetLastError() == ERROR_INVALID_ADDRESS, "a release of a non-start address is refused like Windows' (error %lu)", GetLastError());
    CHECK(!via_slot_free(q, 0x1000, MEM_RELEASE) && GetLastError() == ERROR_INVALID_PARAMETER, "a release with a size is refused like Windows' (error %lu)", GetLastError());
    p = (BYTE *)via_slot_alloc(0, 1 << 20, MEM_RESERVE | MEM_WRITE_WATCH, PAGE_NOACCESS);
    CHECK(p && (DWORD_PTR)p < KLVH_BASE, "a write-watch reservation passes to the low half (%p)", p);
    if (p) via_slot_free(p, 0, MEM_RELEASE);
    CHECK(klvh_passed >= 1, "and is counted as passed (%ld)", klvh_passed);
    /* 3b. review fixes of 2026-10-25: MEM_COMMIT alone is a new block too; a size-0 decommit means the carved block, not the chunk */
    p = (BYTE *)via_slot_alloc(0, 2 << 20, MEM_COMMIT, PAGE_READWRITE);
    CHECK(p && (DWORD_PTR)p >= KLVH_BASE, "MEM_COMMIT alone (the reserve+commit shortcut) through the slot -> high half (%p)", p);
    if (p) { memset(p, 0x3c, 2 << 20); CHECK(p[(2 << 20) - 1] == 0x3c, "and its 2 MB are writable"); }
    CHECK(!via_slot_free(q + 0x10000, 0, MEM_DECOMMIT) && GetLastError() == ERROR_INVALID_ADDRESS, "a size-0 decommit of a non-start address is refused like Windows' (error %lu)", GetLastError());
    /* q was the first carve, i.e. it sits at the FIRST CHUNK's start: the case where the real call with size 0 would have decommitted the whole chunk */
    CHECK(via_slot_free(q, 0, MEM_DECOMMIT), "a size-0 decommit of the block at the chunk's start decommits that block");
    CHECK(VirtualQuery(q, &mbi, sizeof mbi) && mbi.State == MEM_RESERVE && mbi.RegionSize >= (3 << 20), "its pages are reserved again (%lu KB region)", (unsigned long)(mbi.RegionSize >> 10));
    CHECK(p && VirtualQuery(p, &mbi, sizeof mbi) && mbi.State == MEM_COMMIT && p[0] == 0x3c, "and the neighbour p in the same chunk is still committed (the chunk was not decommitted)");
    if (p) CHECK(via_slot_free(p, 0, MEM_RELEASE), "the commit-only block releases through the slot");
    CHECK(klvh_high_left() == 0, "nothing above 2 GB is free after the takeover");
    /* release both, re-carve: the hole is reused */
    CHECK(via_slot_free(q, 0, MEM_RELEASE) && via_slot_free(r, 0, MEM_RELEASE), "both blocks released through the slot");
    CHECK(klvh_carved == carved0 && me->held_n == 0 && me->high == 0, "bookkeeping back to zero (carved %.1f MB, held %ld)", klvh_carved / 1048576.0, me->held_n);
    CHECK(VirtualQuery(q, &mbi, sizeof mbi) && mbi.State == MEM_RESERVE, "the released pages are reserved again (ours), not committed");
    p = (BYTE *)via_slot_alloc(0, 3 << 20, MEM_RESERVE, PAGE_NOACCESS);
    CHECK(p == q, "the next carve of the same size reuses the hole (%p = %p)", p, q);
    if (p) via_slot_free(p, 0, MEM_RELEASE);
    klvh_tick();                                                /* the 10 s line, once */
    printf("\n%s: %d check(s) failed\n", leaf, fails);
    DeleteFileA(klh_ini);
    return fails ? 1 : 0;
}
