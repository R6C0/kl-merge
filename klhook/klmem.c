/*
 * klmem.c - room for bigger levels: the game's address space. Part of KLHook (included by klhook.c, SHIP and TEST
 * alike). Import slots only; no code byte and no data of kl2.exe changes. NOT RUN IN THE GAME YET (2026-10-09).
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
 *     are reserved in one piece (no memory is committed: it costs nothing but the addresses). The wrapper on the
 *     exe's HeapAlloc import (0xb1011c) passes every call on; when one FAILS for 1 MB or more, the reserve is
 *     released and the call repeated once. So the one big block a level needs finds a hole of at least that
 *     size, however the rest has fallen. The reserve is taken again when the game is back in the frontend and
 *     a piece of that size is free (the level's block has been given back by then).
 *     ASSUMPTION: the process heap takes a block of that size straight from VirtualAlloc (Windows does for
 *     anything above about 512 KB), so the freed stretch is what it gets.
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
 *   StackMB=0        0 = leave the game's threads their 4 MB; 1 or 2 = reserve that much for its new threads
 *   Log=1
 */
#ifndef KLMEM_C
#define KLMEM_C

static int klm_on = 1, klm_log = 1, klm_reserve_mb = 128, klm_stack_mb;
static void *volatile klm_reserve;
static volatile LONG klm_released, klm_saved, klm_threads;
static DWORD klm_released_at;
static LPVOID (WINAPI *klm_real_HeapAlloc)(HANDLE, DWORD, SIZE_T);
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

static int klm_take(void)
{
    void *p;
    if (klm_reserve_mb <= 0 || klm_reserve) return 0;
    p = VirtualAlloc(0, (SIZE_T)klm_reserve_mb << 20, MEM_RESERVE, PAGE_NOACCESS);
    if (!p) return 0;
    if (InterlockedCompareExchangePointer((void *volatile *)&klm_reserve, p, 0)) { VirtualFree(p, 0, MEM_RELEASE); return 0; }
    return 1;
}

static int klm_give(void)
{
    void *p = InterlockedExchangePointer((void *volatile *)&klm_reserve, 0);
    if (!p) return 0;
    VirtualFree(p, 0, MEM_RELEASE);
    klm_released_at = GetTickCount(); InterlockedIncrement(&klm_released);
    return 1;
}

static LPVOID WINAPI klm_HeapAlloc(HANDLE heap, DWORD flags, SIZE_T size)
{
    LPVOID p; SIZE_T largest, total; DWORD err;
    if (size < (1u << 20)) return klm_real_HeapAlloc(heap, flags, size);
    if (size >= (16u << 20) && klm_log) {
        err = GetLastError(); klm_free_space(&largest, &total); SetLastError(err);
        klog("memory: a block of %.1f MB is asked for; free address space %.0f MB, largest piece %.1f MB%s", size / 1048576.0, total / 1048576.0, largest / 1048576.0,
             klm_reserve ? " (+ the reserve)" : "");
    }
    p = klm_real_HeapAlloc(heap, flags, size);
    if (p) return p;
    klm_free_space(&largest, &total);
    if (klm_give()) {
        p = klm_real_HeapAlloc(heap, flags, size);
        klog("memory: HeapAlloc of %.1f MB FAILED (free %.0f MB, largest piece %.1f MB); the reserve of %d MB was released: %s", size / 1048576.0, total / 1048576.0,
             largest / 1048576.0, klm_reserve_mb, p ? "the block is there now" : "it failed AGAIN - the game will fault at 0x8e5bbd");
    } else klog("memory: HeapAlloc of %.1f MB FAILED (free %.0f MB, largest piece %.1f MB) and there is no reserve left - the game will fault at 0x8e5bbd", size / 1048576.0,
                total / 1048576.0, largest / 1048576.0);
    return p;
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
{   /* back in the frontend, a while after the reserve was spent: take it again if a piece of that size is free */
    static DWORD calls; static LONG told; char scene[160], key[64];
    if (!klm_on || (calls++ & 63)) return;
    if (klm_stack_mb > 0 && klm_threads != told) { told = klm_threads; if (klm_log) klog("memory: %ld game thread(s) so far started with a %d MB stack instead of 4 MB", told, klm_stack_mb); }
    if (klm_reserve || klm_reserve_mb <= 0 || !klm_released || (LONG)(GetTickCount() - klm_released_at) < 20000) return;
    if (!klh_scene(scene, sizeof scene) || klh_level_key(scene, key, sizeof key)) return;
    if (klm_take() && klm_log) klog("memory: the reserve of %d MB is held again (at %p)", klm_reserve_mb, klm_reserve);
    else klm_released_at = GetTickCount();
}

static void klm_init(void)
{
    SIZE_T largest, total; int n = 0;
    klm_on = GetPrivateProfileIntA("Memory", "Enable", 1, klh_ini);
    if (!klm_on) return;
    klm_log = GetPrivateProfileIntA("Memory", "Log", 1, klh_ini);
    klm_reserve_mb = (int)GetPrivateProfileIntA("Memory", "ReserveMB", 128, klh_ini); if (klm_reserve_mb < 0 || klm_reserve_mb > 512) klm_reserve_mb = 128;
    klm_stack_mb = (int)GetPrivateProfileIntA("Memory", "StackMB", 0, klh_ini); if (klm_stack_mb < 0 || klm_stack_mb > 3) klm_stack_mb = 0;
    klm_free_space(&largest, &total);
    klm_take();
    n += klh_iat("KERNEL32.dll", "HeapAlloc", (void *)klm_HeapAlloc, (void **)&klm_real_HeapAlloc);
    if (klm_stack_mb) {
        n += klh_iat("KERNEL32.dll", "CreateThread", (void *)klm_CreateThread, (void **)&klm_real_CreateThread);
        n += klh_iat("MSVCR90.dll", "_beginthreadex", (void *)klm_beginthreadex, (void **)&klm_real_beginthreadex);
    }
    klog("memory: at start %.0f MB of address space free, largest piece %.1f MB; reserve of %d MB %s; HeapAlloc %s; game thread stacks %s (%d import slot(s))",
         total / 1048576.0, largest / 1048576.0, klm_reserve_mb, klm_reserve ? "held" : klm_reserve_mb ? "NOT available" : "off",
         klm_real_HeapAlloc ? "wrapped" : "NOT wrapped", klm_stack_mb ? "reduced" : "left at 4 MB", n);
    if (!klm_real_HeapAlloc) klm_give();              /* nobody could release it */
}

#endif /* KLMEM_C */
