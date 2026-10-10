/*
 * klmem.c - room for bigger levels: the game's address space. Part of KLHook (included by klhook.c, SHIP and TEST
 * alike). Import slots only; no code byte and no data of kl2.exe changes.
 *
 * THE LIMIT (re\crash_owner_1009.md). kl2.exe is a 32-bit program without the large-address flag:
 * 2048 MB of address space, whatever the machine has. A level's .prm is read into ONE heap block (0x82049b:
 * file size + 0x60000 through ZWin32Allocator 0x7bb2c0 -> HeapAlloc); when no free stretch of that size is left
 * the call returns NULL, the game does not test it and writes to address 0 at 0x8e5bbd. Seen with 60.7 MB asked
 * and 1828 MB in use; stock levels can hit it too. It is fragmentation as much as size: the space is cut up by
 * the graphics driver's DLLs (190 MB), about 100 thread stacks of 4 MB each, the textures, the overlays.
 * The flag cannot simply be set: it is in the file (the hook comes too late), and the engine marks a direct
 * pointer in a chunk reference by its TOP BIT (`test eax,eax ; jns <table look-up> ; and eax,0x7fffffff`,
 * e.g. 0x6ad0c7, 0x45f30b, 0x4aa984 - 429 sites of the table 0xeac7b0), so memory above 2 GB would be read as
 * something else. The 2 GB are what there is; this file spends them better.
 *
 * WHAT IT DOES
 *  1. THE RESERVE. At DLL load - before the driver, the threads and the level come - ReserveMB of address space
 *     are reserved in one piece (no memory is committed: it costs nothing but the addresses) and KEPT for the
 *     whole run. A request of BigMB or more through the exe's HeapAlloc import (0xb1011c) - the level's .prm
 *     block - is answered FROM the reserve: its pages are committed and the reserve's own address is returned.
 *     The game's allocator frees the block with HeapFree (0x882c95, import 0xb10120): the wrapper there sees the
 *     address, decommits the pages and the reserve is free for the next level. A smaller request (1 MB or more)
 *     that FAILS in the heap is answered the same way if the reserve is free.
 *     WHY NOT AS FIRST WRITTEN (release the reserve when the big request fails, take it again in the frontend):
 *     seen live 2026-10-09 22:53 - 23:00. First load of a fresh process: largest free piece 69.4 MB, 74.5 MB
 *     asked, the reserve released, the block fitted. But the other 53 MB of the released stretch were filled by
 *     later blocks that outlive the level, so back in the frontend the largest piece was 70.8 MB: the reserve
 *     could not be taken again, and the second load failed with nothing left (crash 0x8e5bbd, the owner's).
 *     The block is not a heap block: HeapSize (0xb10190) is wrapped too and answers for it. HeapValidate is
 *     only called for the whole heap (0x447cbf), HeapReAlloc is not imported.
 *     WHY SEVERAL BLOCKS (the owner's crashes of 2026-10-10 00:41, 00:44 and 00:47, all 0x8e5bbd on the third or
 *     fourth level load of one process). A level asks for FIVE large blocks through the same allocator, in this
 *     order on Retomoto: 32.0 MB (a scratch block of every scene load, freed a second later), 16.9, 74.6 (the
 *     .prm), 20.6 and 25.9 MB. The free address space does not shrink much from load to load (about 400 MB in
 *     the frontend) but it is cut smaller every time: its largest piece was 242 MB before the first load,
 *     32 MB before the second, 26 MB before the third. With the .prm in the reserve the 20.6 or the 25.9 MB
 *     block then found no piece, and the reserve held one block only. So the reserve is now an arena of
 *     64 KB-aligned blocks (first fit): the .prm always, and any request of 1 MB or more that FAILS in the
 *     heap. That is the old behaviour in every case that used to work, and a block instead of a fault in the
 *     case that crashed: 74.6 + 20.6 + 25.9 MB fit the 128 MB.
 *     NOT RUN IN THE GAME YET (Steam was signed out that night); klmem_test.c replays the requests in a
 *     cut-up address space outside the game.
 *     THE NEXT STEP, also only tried in klmem_test.c: RoomMB=128 with ReserveMB=176. Then a block of MidMB or
 *     more goes into the reserve FIRST whenever the largest free piece outside is under RoomMB, so that from
 *     the second load on all five live there (138 MB) and the heap keeps its large pieces. It needs a reserve
 *     that holds all of a level's large blocks: with 128 MB the first three fill it and the 25.9 MB block is
 *     left with nothing (klmem_test.exe 128 128 shows it). Unknown until run: whether the game is content with
 *     its .ANM and .fxc blocks living outside the heap (the 32 MB scratch block was, 00:41:39).
 *     The blocks by size: 16.9 MB = the level's .fxc, 74.6 = .prm, 20.6 = .ANM (file size + 0x60000 each);
 *     25.9 MB is no file of the archive (callers 0x51cf8e, 0x8e0286, 0x51c46e: not looked at).
 *  2. THREAD STACKS (off unless StackMB is set). The exe's PE header reserves 4 MB for every thread that asks
 *     for the default, in this process about 100 of them. With StackMB=1 the game's OWN new threads (its
 *     CreateThread and _beginthreadex imports, 34 threads counted) get 1 MB reserved instead: about 100 MB
 *     back. The main thread and the driver's threads are not touched. RISK: a game thread that really uses
 *     more than that overflows its stack; not measured, hence off.
 *  3. WHAT WAS FREE. Every request of 16 MB or more is logged with the largest free piece and the total free
 *     at that moment, and so is every failure - numbers the level budgets (kl_graft PRM_LIMIT, the .TEX size)
 *     can be set by instead of guessed.
 *
 * KLHook.ini
 *   [Memory]
 *   Enable=1
 *   ReserveMB=128    0 = no reserve (the log lines stay)
 *   BigMB=48         requests of this size or more go into the reserve
 *   MidMB=16         requests of this size or more go into it too when the largest free piece is under RoomMB
 *   RoomMB=0         0 = never (only when the heap fails). 128 needs ReserveMB=176 for Retomoto: see above
 *   StackMB=0        0 = leave the game's threads their 4 MB; 1 or 2 = reserve that much for its new threads
 *   Log=1
 */
#ifndef KLMEM_C
#define KLMEM_C

#define KLM_BLOCKS 64
static int klm_on = 1, klm_log = 1, klm_reserve_mb = 128, klm_big_mb = 48, klm_mid_mb = 16, klm_room_mb, klm_stack_mb;
static void *klm_reserve;                               /* set once in klm_init, never released */
static volatile LONG klm_served, klm_threads;
static struct { SIZE_T off, len, asked; } klm_blk[KLM_BLOCKS];   /* the blocks in the reserve, by offset; len = asked rounded up to 64 KB */
static int klm_n;                                       /* how many */
static SIZE_T klm_used;                                 /* their len summed */
static CRITICAL_SECTION klm_cs;                         /* the three above */
static LPVOID (WINAPI *klm_real_HeapAlloc)(HANDLE, DWORD, SIZE_T);
static BOOL (WINAPI *klm_real_HeapFree)(HANDLE, DWORD, LPVOID);
static SIZE_T (WINAPI *klm_real_HeapSize)(HANDLE, DWORD, LPCVOID);
static HANDLE (WINAPI *klm_real_CreateThread)(LPSECURITY_ATTRIBUTES, SIZE_T, LPTHREAD_START_ROUTINE, LPVOID, DWORD, LPDWORD);
static uintptr_t (__cdecl *klm_real_beginthreadex)(void *, unsigned, unsigned (__stdcall *)(void *), void *, unsigned, unsigned *);

static void klm_free_space(SIZE_T *largest, SIZE_T *total)
{   /* a walk over the user half of the address space */
    MEMORY_BASIC_INFORMATION mbi; BYTE *p = (BYTE *)0x10000;
    *largest = *total = 0;
    while (p < (BYTE *)0x7ffe0000 && VirtualQuery(p, &mbi, sizeof mbi)) {
        if (mbi.State == MEM_FREE) { *total += mbi.RegionSize; if (mbi.RegionSize > *largest) *largest = mbi.RegionSize; }
        p = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
}

static void klm_map_line(const char *when)
{   /* who holds the address space, in one line: written at every level's .prm request and at a failure, so that the
       loads of one process can be compared (what stays behind, and in pieces of what size). The reserve itself
       counts under 'reserved only'; so do the unused parts of thread stacks and of heap segments. */
    static const SIZE_T edge[4] = { 64u << 20, 16u << 20, 4u << 20, 1u << 20 };
    MEMORY_BASIC_INFORMATION mbi; BYTE *p = (BYTE *)0x10000; SIZE_T fr[5] = { 0 }, image = 0, mapped = 0, commit = 0, reserved = 0; int nf[5] = { 0 }, regions = 0, i;
    DWORD err = GetLastError();
    while (p < (BYTE *)0x7ffe0000 && VirtualQuery(p, &mbi, sizeof mbi)) {
        if (mbi.State == MEM_FREE) { for (i = 0; i < 4 && mbi.RegionSize < edge[i]; i++) ; nf[i]++; fr[i] += mbi.RegionSize; }
        else {
            regions++;
            if (mbi.Type == MEM_IMAGE) image += mbi.RegionSize; else if (mbi.Type == MEM_MAPPED) mapped += mbi.RegionSize;
            else if (mbi.State == MEM_COMMIT) commit += mbi.RegionSize; else reserved += mbi.RegionSize;
        }
        p = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    klog("memory: %s: free pieces of 64 MB+ %d (%.0f MB), 16-64 MB %d (%.0f), 4-16 MB %d (%.0f), 1-4 MB %d (%.0f), under 1 MB %d (%.0f); in use: modules %.0f MB, mapped files %.0f, private committed %.0f, private reserved only %.0f; %d regions",
         when, nf[0], fr[0] / 1048576.0, nf[1], fr[1] / 1048576.0, nf[2], fr[2] / 1048576.0, nf[3], fr[3] / 1048576.0, nf[4], fr[4] / 1048576.0,
         image / 1048576.0, mapped / 1048576.0, commit / 1048576.0, reserved / 1048576.0, regions);
    SetLastError(err);
}

static int klm_inside(LPCVOID p)
{
    return klm_reserve && (const BYTE *)p >= (const BYTE *)klm_reserve && (const BYTE *)p < (const BYTE *)klm_reserve + ((SIZE_T)klm_reserve_mb << 20);
}

static void *klm_from_reserve(SIZE_T size)
{   /* a block in the first gap of the reserve that fits, or 0: no reserve, no gap, the table is full, or the commit failed */
    SIZE_T room = (SIZE_T)klm_reserve_mb << 20, len = (size + 0xffff) & ~(SIZE_T)0xffff, at = 0; int i, k; void *p = 0;
    if (!klm_reserve || !klm_real_HeapFree || !size || len < size || len > room) return 0;
    EnterCriticalSection(&klm_cs);
    if (klm_n < KLM_BLOCKS) {
        for (i = 0; i <= klm_n; i++) {                /* the gap before block i; i == klm_n: the one after the last */
            if ((i < klm_n ? klm_blk[i].off : room) - at >= len) break;
            if (i < klm_n) at = klm_blk[i].off + klm_blk[i].len;
        }
        if (i <= klm_n && VirtualAlloc((BYTE *)klm_reserve + at, len, MEM_COMMIT, PAGE_READWRITE)) {
            for (k = klm_n; k > i; k--) klm_blk[k] = klm_blk[k - 1];
            klm_blk[i].off = at; klm_blk[i].len = len; klm_blk[i].asked = size; klm_n++; klm_used += len;
            p = (BYTE *)klm_reserve + at; InterlockedIncrement(&klm_served);
        }
    }
    LeaveCriticalSection(&klm_cs);
    return p;
}

static LPVOID WINAPI klm_HeapAlloc(HANDLE heap, DWORD flags, SIZE_T size)
{
    LPVOID p; SIZE_T largest = 0, total = 0; DWORD err; int first = 0;
    if (size < (1u << 20)) return klm_real_HeapAlloc(heap, flags, size);
    if (size >= ((SIZE_T)klm_mid_mb << 20) || size >= (16u << 20)) {
        err = GetLastError(); klm_free_space(&largest, &total); SetLastError(err);
        if (klm_log) klog("memory: a block of %.1f MB is asked for; free address space %.0f MB, largest piece %.1f MB (the reserve holds %d block(s), %.1f of %d MB)",
                          size / 1048576.0, total / 1048576.0, largest / 1048576.0, klm_n, klm_used / 1048576.0, klm_reserve ? klm_reserve_mb : 0);
        first = size >= ((SIZE_T)klm_big_mb << 20) || (size >= ((SIZE_T)klm_mid_mb << 20) && largest < ((SIZE_T)klm_room_mb << 20));
        if (klm_log && size >= ((SIZE_T)klm_big_mb << 20)) klm_map_line("at the level's largest block");
    }
    if (first && (p = klm_from_reserve(size)) != 0) {
        if (klm_log) klog("memory: the block of %.1f MB is in the reserve (%p, use %ld)", size / 1048576.0, p, klm_served);
        return p;
    }
    p = klm_real_HeapAlloc(heap, flags, size);
    if (p) return p;
    klm_free_space(&largest, &total);
    p = klm_from_reserve(size);
    klog("memory: HeapAlloc of %.1f MB FAILED (free %.0f MB, largest piece %.1f MB); %s", size / 1048576.0, total / 1048576.0, largest / 1048576.0,
         p ? "the block is in the reserve instead" : !klm_reserve ? "there is no reserve - the game will fault (0x8e5bbd for a level's .prm)" :
         "the reserve has no room for it either - the game will fault (0x8e5bbd for a level's large blocks)");
    if (!p && klm_reserve) klog("memory: the reserve holds %d block(s), %.1f of %d MB", klm_n, klm_used / 1048576.0, klm_reserve_mb);
    klm_map_line(p ? "at the refused request" : "at the fault");
    return p;
}

static BOOL WINAPI klm_HeapFree(HANDLE heap, DWORD flags, LPVOID p)
{
    SIZE_T off, asked = 0; int i, n = 0, found = 0; double used = 0;
    if (!p || !klm_inside(p)) return klm_real_HeapFree(heap, flags, p);
    off = (SIZE_T)((BYTE *)p - (BYTE *)klm_reserve);
    EnterCriticalSection(&klm_cs);
    for (i = 0; i < klm_n && klm_blk[i].off != off; i++) ;
    if (i < klm_n) {
        VirtualFree(p, klm_blk[i].len, MEM_DECOMMIT);  /* this block's pages only; they come back zeroed at the next commit */
        asked = klm_blk[i].asked; klm_used -= klm_blk[i].len; klm_n--; found = 1;
        for (; i < klm_n; i++) klm_blk[i] = klm_blk[i + 1];
    }
    n = klm_n; used = klm_used / 1048576.0;
    LeaveCriticalSection(&klm_cs);
    if (!found) { klog("memory: HeapFree of %p, which is inside the reserve but no block of it - refused", p); SetLastError(ERROR_INVALID_PARAMETER); return FALSE; }
    if (klm_log) klog("memory: the block of %.1f MB in the reserve was freed by the game (it holds %d block(s), %.1f MB now)", asked / 1048576.0, n, used);
    return TRUE;
}

static SIZE_T WINAPI klm_HeapSize(HANDLE heap, DWORD flags, LPCVOID p)
{
    SIZE_T off, asked = (SIZE_T)-1; int i;
    if (!p || !klm_inside(p)) return klm_real_HeapSize(heap, flags, p);
    off = (SIZE_T)((const BYTE *)p - (const BYTE *)klm_reserve);
    EnterCriticalSection(&klm_cs);
    for (i = 0; i < klm_n; i++) if (klm_blk[i].off == off) asked = klm_blk[i].asked;
    LeaveCriticalSection(&klm_cs);
    return asked;
}

static HANDLE WINAPI klm_CreateThread(LPSECURITY_ATTRIBUTES sa, SIZE_T stack, LPTHREAD_START_ROUTINE fn, LPVOID arg, DWORD flags, LPDWORD id)
{
    if (klm_stack_mb > 0 && !stack) { stack = (SIZE_T)klm_stack_mb << 20; flags |= STACK_SIZE_PARAM_IS_A_RESERVATION; InterlockedIncrement(&klm_threads); }
    return klm_real_CreateThread(sa, stack, fn, arg, flags, id);
}

static uintptr_t __cdecl klm_beginthreadex(void *sec, unsigned stack, unsigned (__stdcall *fn)(void *), void *arg, unsigned flags, unsigned *id)
{   /* the C runtime hands stack and flags to CreateThread as they are */
    if (klm_stack_mb > 0 && !stack) { stack = (unsigned)klm_stack_mb << 20; flags |= STACK_SIZE_PARAM_IS_A_RESERVATION; InterlockedIncrement(&klm_threads); }
    return klm_real_beginthreadex(sec, stack, fn, arg, flags, id);
}

static void klm_tick(void)
{
    static DWORD calls; static LONG told;
    if (!klm_on || (calls++ & 63)) return;
    if (klm_stack_mb > 0 && klm_threads != told) { told = klm_threads; if (klm_log) klog("memory: %ld game thread(s) so far started with a %d MB stack instead of 4 MB", told, klm_stack_mb); }
}

static void klm_init(void)
{
    SIZE_T largest, total; int n = 0;
    klm_on = GetPrivateProfileIntA("Memory", "Enable", 1, klh_ini);
    if (!klm_on) return;
    klm_log = GetPrivateProfileIntA("Memory", "Log", 1, klh_ini);
    klm_reserve_mb = (int)GetPrivateProfileIntA("Memory", "ReserveMB", 128, klh_ini); if (klm_reserve_mb < 0 || klm_reserve_mb > 512) klm_reserve_mb = 128;
    klm_stack_mb = (int)GetPrivateProfileIntA("Memory", "StackMB", 0, klh_ini); if (klm_stack_mb < 0 || klm_stack_mb > 3) klm_stack_mb = 0;
    klm_big_mb = (int)GetPrivateProfileIntA("Memory", "BigMB", 48, klh_ini); if (klm_big_mb < 1 || klm_big_mb > 512) klm_big_mb = 48;
    klm_mid_mb = (int)GetPrivateProfileIntA("Memory", "MidMB", 16, klh_ini); if (klm_mid_mb < 1 || klm_mid_mb > 512) klm_mid_mb = 16;
    klm_room_mb = (int)GetPrivateProfileIntA("Memory", "RoomMB", 0, klh_ini); if (klm_room_mb < 0 || klm_room_mb > 2048) klm_room_mb = 0;
    InitializeCriticalSection(&klm_cs);
    klm_free_space(&largest, &total);
    if (klm_reserve_mb > 0) klm_reserve = VirtualAlloc(0, (SIZE_T)klm_reserve_mb << 20, MEM_RESERVE, PAGE_NOACCESS);
    /* HeapFree and HeapSize first: a block is only handed out of the reserve when its free can be seen */
    n += klh_iat("KERNEL32.dll", "HeapFree", (void *)klm_HeapFree, (void **)&klm_real_HeapFree);
    n += klh_iat("KERNEL32.dll", "HeapSize", (void *)klm_HeapSize, (void **)&klm_real_HeapSize);
    if (!klm_real_HeapSize) { klm_real_HeapFree = 0; klog("memory: HeapSize NOT wrapped: the reserve is not used"); }
    n += klh_iat("KERNEL32.dll", "HeapAlloc", (void *)klm_HeapAlloc, (void **)&klm_real_HeapAlloc);
    if (klm_stack_mb) {
        n += klh_iat("KERNEL32.dll", "CreateThread", (void *)klm_CreateThread, (void **)&klm_real_CreateThread);
        n += klh_iat("MSVCR90.dll", "_beginthreadex", (void *)klm_beginthreadex, (void **)&klm_real_beginthreadex);
    }
    klog("memory: at start %.0f MB of address space free, largest piece %.1f MB; reserve of %d MB %s (blocks of %d MB or more go into it, any of 1 MB or more that the heap refuses, and - RoomMB - of %d MB or more while the largest free piece is under %d MB); HeapAlloc %s, HeapFree %s; game thread stacks %s (%d import slot(s))",
         total / 1048576.0, largest / 1048576.0, klm_reserve_mb, klm_reserve ? "held for the whole run" : klm_reserve_mb ? "NOT available" : "off", klm_big_mb, klm_mid_mb, klm_room_mb,
         klm_real_HeapAlloc ? "wrapped" : "NOT wrapped", klm_real_HeapFree ? "wrapped" : "NOT wrapped", klm_stack_mb ? "reduced" : "left at 4 MB", n);
    if ((!klm_real_HeapAlloc || !klm_real_HeapFree) && klm_reserve) { VirtualFree(klm_reserve, 0, MEM_RELEASE); klm_reserve = 0; }   /* nobody could use it */
}

#endif /* KLMEM_C */
