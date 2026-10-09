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
 *   StackMB=0        0 = leave the game's threads their 4 MB; 1 or 2 = reserve that much for its new threads
 *   Log=1
 */
#ifndef KLMEM_C
#define KLMEM_C

static int klm_on = 1, klm_log = 1, klm_reserve_mb = 128, klm_big_mb = 48, klm_stack_mb;
static void *klm_reserve;                               /* set once in klm_init, never released */
static volatile LONG klm_busy, klm_served, klm_threads; /* klm_busy: the reserve holds a block */
static SIZE_T klm_block;                                /* its size */
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

static void *klm_from_reserve(SIZE_T size)
{   /* the block at the reserve's address, or 0: no reserve, too large, already holding one, or the commit failed */
    if (!klm_reserve || !klm_real_HeapFree || size > ((SIZE_T)klm_reserve_mb << 20) || InterlockedCompareExchange(&klm_busy, 1, 0)) return 0;
    if (!VirtualAlloc(klm_reserve, size, MEM_COMMIT, PAGE_READWRITE)) { InterlockedExchange(&klm_busy, 0); return 0; }
    klm_block = size; InterlockedIncrement(&klm_served);
    return klm_reserve;
}

static LPVOID WINAPI klm_HeapAlloc(HANDLE heap, DWORD flags, SIZE_T size)
{
    LPVOID p; SIZE_T largest = 0, total = 0; DWORD err;
    if (size < (1u << 20)) return klm_real_HeapAlloc(heap, flags, size);
    if (size >= (16u << 20) && klm_log) {
        err = GetLastError(); klm_free_space(&largest, &total); SetLastError(err);
        klog("memory: a block of %.1f MB is asked for; free address space %.0f MB, largest piece %.1f MB%s", size / 1048576.0, total / 1048576.0, largest / 1048576.0,
             !klm_reserve ? "" : klm_busy ? " (the reserve is in use)" : " (+ the reserve)");
    }
    if (size >= ((SIZE_T)klm_big_mb << 20) && (p = klm_from_reserve(size)) != 0) {
        if (klm_log) klog("memory: the block of %.1f MB is in the reserve (%p, use %ld)", size / 1048576.0, p, klm_served);
        return p;
    }
    p = klm_real_HeapAlloc(heap, flags, size);
    if (p) return p;
    klm_free_space(&largest, &total);
    p = klm_from_reserve(size);
    klog("memory: HeapAlloc of %.1f MB FAILED (free %.0f MB, largest piece %.1f MB); %s", size / 1048576.0, total / 1048576.0, largest / 1048576.0,
         p ? "the block is in the reserve instead" : !klm_reserve ? "there is no reserve - the game will fault (0x8e5bbd for a level's .prm)" :
         klm_busy ? "the reserve already holds a block - the game will fault (0x8e5bbd for a level's .prm)" : "it does not fit the reserve either - the game will fault");
    return p;
}

static BOOL WINAPI klm_HeapFree(HANDLE heap, DWORD flags, LPVOID p)
{
    if (p && p == klm_reserve && klm_busy) {
        VirtualFree(klm_reserve, 0, MEM_DECOMMIT);    /* the whole reservation: pages come back zeroed at the next commit */
        if (klm_log) klog("memory: the block of %.1f MB in the reserve was freed by the game", klm_block / 1048576.0);
        klm_block = 0; InterlockedExchange(&klm_busy, 0);
        return TRUE;
    }
    return klm_real_HeapFree(heap, flags, p);
}

static SIZE_T WINAPI klm_HeapSize(HANDLE heap, DWORD flags, LPCVOID p)
{
    if (p && p == klm_reserve && klm_busy) return klm_block;
    return klm_real_HeapSize(heap, flags, p);
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
    klog("memory: at start %.0f MB of address space free, largest piece %.1f MB; reserve of %d MB %s (blocks of %d MB or more go into it); HeapAlloc %s, HeapFree %s; game thread stacks %s (%d import slot(s))",
         total / 1048576.0, largest / 1048576.0, klm_reserve_mb, klm_reserve ? "held for the whole run" : klm_reserve_mb ? "NOT available" : "off", klm_big_mb,
         klm_real_HeapAlloc ? "wrapped" : "NOT wrapped", klm_real_HeapFree ? "wrapped" : "NOT wrapped", klm_stack_mb ? "reduced" : "left at 4 MB", n);
    if ((!klm_real_HeapAlloc || !klm_real_HeapFree) && klm_reserve) { VirtualFree(klm_reserve, 0, MEM_RELEASE); klm_reserve = 0; }   /* nobody could use it */
}

#endif /* KLMEM_C */
