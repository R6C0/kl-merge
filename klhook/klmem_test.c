/*
 * klmem_test.c - klmem.c's reserve outside the game: a 32-bit console program that includes klmem.c as it is
 * (the helpers it takes from klhook.c are stubbed here) and replays the large requests of a level load in an
 * address space cut into small pieces, the state the owner's game was in when it crashed on 2026-10-10.
 * It proves the arena's bookkeeping, NOT that the game is content with where its blocks live.
 *
 *   call "...\vcvarsall.bat" x86
 *   cl /nologo /O2 /W3 /D_CRT_SECURE_NO_WARNINGS klmem_test.c /Fe:klmem_test.exe
 *   klmem_test.exe [ReserveMB [RoomMB]]      exit code 0 = every check passed. Default 128 0 (klmem.c's own);
 *                                            176 128 = the next step; 128 128 FAILS and shows why (klmem.c)
 *
 * The exe has no large-address flag (as kl2.exe has none), so it has the same 2 GB.
 */
#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdint.h>
#include <string.h>

static char klh_ini[MAX_PATH], dir[MAX_PATH];        /* dir: where klmem.c writes its KLHook_map_<n>.txt */
static int quiet;

static void klog(const char *fmt, ...)
{
    va_list ap;
    if (quiet) return;
    va_start(ap, fmt); printf("    "); vprintf(fmt, ap); printf("\n"); va_end(ap);
}

static int klh_iat(const char *dll, const char *fn, void *mine, void **real)
{   /* no import slot is changed here: the test calls the wrappers itself */
    (void)mine;
    *real = (void *)GetProcAddress(GetModuleHandleA(dll), fn);
    return *real != 0;
}

#include "klmem.c"

static int bad;
#define CHECK(c, ...) do { if (!(c)) { bad++; printf("FAIL: "); printf(__VA_ARGS__); printf("\n"); } } while (0)

/* Retomoto's large requests in the order the game makes them (KLHook.log, 2026-10-10): the scratch block of
   a scene load is freed before the next one is asked for; the other four live as long as the level */
static const double LOAD_MB[] = { 16.9, 74.6, 20.6, 25.9 };

static void *take(HANDLE h, double mb, int must_be_inside)
{
    SIZE_T size = (SIZE_T)(mb * 1048576.0); BYTE *p = klm_HeapAlloc(h, 0, size);
    CHECK(p != 0, "a block of %.1f MB was refused", mb);
    if (!p) return 0;
    CHECK(klm_HeapSize(h, 0, p) == size || !klm_inside(p), "HeapSize of the %.1f MB block is %lu, asked %lu", mb, (unsigned long)klm_HeapSize(h, 0, p), (unsigned long)size);
    if (must_be_inside) CHECK(klm_inside(p), "the %.1f MB block is not in the reserve", mb);
    p[0] = 0x5a; p[size - 1] = 0xa5; memset(p + size / 2, 0x77, 4096);       /* the pages are really there */
    return p;
}

static void one_load(HANDLE h, int n, int order, int must_be_inside)
{
    void *p[4], *scratch; int i, k; SIZE_T j;
    scratch = take(h, 32.0, 0);
    CHECK(klm_HeapFree(h, 0, scratch), "the scratch block was not freed");
    for (i = 0; i < 4; i++) p[i] = take(h, LOAD_MB[i], must_be_inside);
    for (i = 0; i < 4; i++) for (k = i + 1; k < 4; k++) if (p[i] && p[k]) {
        BYTE *a = p[i], *b = p[k]; SIZE_T la = (SIZE_T)(LOAD_MB[i] * 1048576.0), lb = (SIZE_T)(LOAD_MB[k] * 1048576.0);
        CHECK(a + la <= b || b + lb <= a, "load %d: blocks %d and %d overlap", n, i, k);
    }
    for (i = 0; i < 4; i++) if (p[i]) {                                       /* nobody wrote into another's pages */
        BYTE *a = p[i]; SIZE_T la = (SIZE_T)(LOAD_MB[i] * 1048576.0);
        CHECK(a[0] == 0x5a && a[la - 1] == 0xa5, "load %d: block %d lost its marks", n, i);
        for (j = 0; j < 4096; j++) if (a[la / 2 + j] != 0x77) { CHECK(0, "load %d: block %d lost its middle", n, i); break; }
    }
    for (i = 0; i < 4; i++) {                                                 /* three different orders of freeing */
        k = order == 0 ? i : order == 1 ? 3 - i : (i + 1) & 3;
        if (p[k]) CHECK(klm_HeapFree(h, 0, p[k]), "load %d: block %d was not freed", n, k);
    }
}

int main(int argc, char **argv)
{
    HANDLE h = GetProcessHeap(); SIZE_T largest, total; BYTE *a; void *p, *q; char num[32];
    int i, n = 0, reserve = argc > 1 ? atoi(argv[1]) : 128, room = argc > 2 ? atoi(argv[2]) : 0;
    GetTempPathA(MAX_PATH, dir); if (dir[0] && dir[strlen(dir) - 1] == '\\') dir[strlen(dir) - 1] = 0;
    GetTempPathA(MAX_PATH, klh_ini); strcat(klh_ini, "klmem_test.ini");
    DeleteFileA(klh_ini);
    sprintf(num, "%d", reserve); WritePrivateProfileStringA("Memory", "ReserveMB", num, klh_ini);
    sprintf(num, "%d", room); WritePrivateProfileStringA("Memory", "RoomMB", num, klh_ini);
    printf("klmem_test: ReserveMB=%d RoomMB=%d\n", reserve, room);
    klm_init();
    CHECK(klm_reserve != 0, "no reserve");

    printf("1. a fresh process: only the .prm goes into the reserve\n");
    p = take(h, 20.6, 0);
    CHECK(room > 600 || !klm_inside(p), "a 20.6 MB block went into the reserve although %d MB pieces are free", room);
    q = take(h, 74.6, 1);
    CHECK(klm_n == (klm_inside(p) ? 2 : 1), "the reserve holds %d blocks", klm_n);
    klm_HeapFree(h, 0, q); klm_HeapFree(h, 0, p);
    CHECK(klm_n == 0 && klm_used == 0, "the reserve is not empty after the frees (%d blocks)", klm_n);

    printf("2. the address space is cut up: a 64 KB reservation every 24 MB, so that no piece of 26 MB is left\n");
    for (a = (BYTE *)0x01000000; a < (BYTE *)0x7f000000; a += 24u << 20) if (VirtualAlloc(a, 0x10000, MEM_RESERVE, PAGE_NOACCESS)) n++;
    /* what is still larger (the test's own modules sit in the way of some) is filled the same way */
    for (i = 0; i < 4000; i++) {
        MEMORY_BASIC_INFORMATION mbi; BYTE *s = (BYTE *)0x10000; BYTE *big = 0;
        while (s < (BYTE *)0x7ffe0000 && VirtualQuery(s, &mbi, sizeof mbi)) {
            if (mbi.State == MEM_FREE && mbi.RegionSize > (24u << 20)) { big = (BYTE *)mbi.BaseAddress; break; }
            s = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
        }
        if (!big) break;
        big = (BYTE *)(((uintptr_t)big + (20u << 20)) & ~(uintptr_t)0xffff);
        if (!VirtualAlloc(big, 0x10000, MEM_RESERVE, PAGE_NOACCESS)) break;
        n++;
    }
    klm_free_space(&largest, &total);
    printf("    %d reservations; free %.0f MB, largest piece %.1f MB\n", n, total / 1048576.0, largest / 1048576.0);
    CHECK(largest < (26u << 20), "the largest free piece is still %.1f MB", largest / 1048576.0);

    printf("3. eight level loads in that state (32.0 scratch, then 16.9 + 74.6 + 20.6 + 25.9 MB held together)\n");
    for (i = 1; i <= 8; i++) {
        quiet = i > 1;                                                        /* the first load's lines are shown */
        one_load(h, i, i % 3, 0);
        CHECK(klm_n == 0 && klm_used == 0, "load %d: the reserve is not empty afterwards (%d blocks, %.1f MB)", i, klm_n, klm_used / 1048576.0);
    }
    quiet = 0;

    printf("4. what must be refused or passed on\n");
    p = take(h, 74.6, 1);
    CHECK(!klm_HeapFree(h, 0, (BYTE *)p + 0x20000), "an address inside a block was taken for a block");
    CHECK(klm_HeapSize(h, 0, (BYTE *)p + 0x20000) == (SIZE_T)-1, "HeapSize answered for an address inside a block");
    q = klm_HeapAlloc(h, 0, 4096);                                            /* a small block is the heap's */
    CHECK(q && !klm_inside(q) && klm_HeapSize(h, 0, q) == 4096 && klm_HeapFree(h, 0, q), "a small heap block was not passed on");
    quiet = 1; q = klm_HeapAlloc(h, 0, (SIZE_T)reserve << 20); quiet = 0;     /* cannot fit beside the .prm, nor anywhere else */
    CHECK(q == 0, "a block as large as the whole reserve was handed out beside another one");
    CHECK(klm_HeapFree(h, 0, p) && klm_n == 0, "the .prm block was not freed");

    printf("5. more small failing requests than the table has rows\n");
    quiet = 1;
    {
        static void *many[KLM_BLOCKS + 8]; int got = 0, inside = 0;
        for (i = 0; i < KLM_BLOCKS + 8; i++) { many[i] = klm_HeapAlloc(h, 0, 25u << 20); if (many[i]) { got++; inside += klm_inside(many[i]); } }
        quiet = 0;
        printf("    %d of %d blocks of 25 MB handed out, %d of them in the reserve (it has room for %d)\n", got, KLM_BLOCKS + 8, inside, reserve / 25);
        CHECK(inside == reserve / 25, "the reserve took %d blocks of 25 MB, it has room for %d", inside, reserve / 25);
        for (i = 0; i < KLM_BLOCKS + 8; i++) if (many[i]) klm_HeapFree(h, 0, many[i]);
        CHECK(klm_n == 0 && klm_used == 0, "the reserve is not empty at the end");
    }
    DeleteFileA(klh_ini);
    printf(bad ? "RESULT: %d check(s) FAILED\n" : "RESULT: PASS\n", bad);
    return bad ? 1 : 0;
}
