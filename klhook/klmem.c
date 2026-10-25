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
 *     25.9 MB = the sound bank beside the archive, F01_Main.WAV, read whole (0x51cf80: allocate the size,
 *     keep the pointer at +0x23c08, read through [0xdd263c] slot 26). Stock F01 has 5.9 / 63.5 / 19.8 / 14.7 MB
 *     in those four: Retomoto asks for 34 MB more in large blocks than a stock level (.fxc +11, .prm +11,
 *     .WAV +11), which a build can give back.
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
 *   OtherStackKB=0   every OTHER thread asking for the default stack (driver, sound, overlays, thread pool) reserves this
 *                    many KB instead of the exe header's 4 MB; kl2.exe's own threads keep 4 MB (0 = off; 2048 kept DM05A alive, K48F_A)
 *                    It also starts the census: every 60 s a line "game threads by routine" with the deepest commit per routine
 *   GameStackKB=0    with OtherStackKB: kl2.exe's own threads reserve this many KB (2048 at least) instead of 4 MB, except
 *   GameStackKeep=   these routines (kl2.exe offsets in hex, comma-separated, from the census line) which keep 4 MB
 *                    (recommended off: K48I_A, 2048: routine +5a7010 (x40) committed 2020 of 2048 KB - 1028 of 4096 with 4 MB, it
 *                    grows into what it is given - and free VA still fell to 14 MB, round 1's own growth varies more than this saves)
 *   SmallRescue=1    a request under 1 MB that the heap refuses (HeapAlloc, or the sound buffers' _aligned_malloc) is logged
 *                    and answered from the reserve (recommended on; 0 = logged only, the game then faults at 0x8e5bbd or
 *                    0x6d2107 as before)
 *   Log=1
 *   Maps=1           KLHook_map_0..7.txt beside the log: the whole address space at each level's largest block
 *                    (and KLHook_map_refused_0/1.txt at the first two refused requests after it)
 */
#ifndef KLMEM_C
#define KLMEM_C

#define KLM_BLOCKS 2048                                 /* 64 large blocks were enough; small rescues (SmallRescue) take one 64 KB entry each */
static int klm_on = 1, klm_log = 1, klm_reserve_mb = 128, klm_big_mb = 48, klm_mid_mb = 16, klm_room_mb, klm_stack_mb, klm_maps = 1, klm_small = 1;
static int klm_ok;                                      /* HeapFree and HeapSize are wrapped: the reserve may hand out blocks */
static int klm_aligned;                                 /* _aligned_malloc and _aligned_free are wrapped too */
static volatile LONG klm_nulls, klm_full_told;          /* small requests the heap refused; the table-full line was written */
static void *klm_reserve;                               /* set once in klm_init, never released */
static volatile LONG klm_served, klm_threads, klm_kept;
static int klm_other_kb; static SIZE_T klm_exe_reserve;   /* OtherStackKB; the header's old reserve once lowered */
static struct { SIZE_T off, len, asked; } klm_blk[KLM_BLOCKS];   /* the blocks in the reserve, by offset; len = asked rounded up to 64 KB */
static int klm_n;                                       /* how many */
static SIZE_T klm_used;                                 /* their len summed */
static CRITICAL_SECTION klm_cs;                         /* the three above */
static LPVOID (WINAPI *klm_real_HeapAlloc)(HANDLE, DWORD, SIZE_T);
static BOOL (WINAPI *klm_real_HeapFree)(HANDLE, DWORD, LPVOID);
static SIZE_T (WINAPI *klm_real_HeapSize)(HANDLE, DWORD, LPCVOID);
static BOOL (WINAPI *klm_real_HeapValidate)(HANDLE, DWORD, LPCVOID);   /* kl2 imports it too: a reserve block is valid while it is in the table */
static HANDLE (WINAPI *klm_real_CreateThread)(LPSECURITY_ATTRIBUTES, SIZE_T, LPTHREAD_START_ROUTINE, LPVOID, DWORD, LPDWORD);
static uintptr_t (__cdecl *klm_real_beginthreadex)(void *, unsigned, unsigned (__stdcall *)(void *), void *, unsigned, unsigned *);
static void *(__cdecl *klm_real_aligned_malloc)(size_t, size_t);
static void (__cdecl *klm_real_aligned_free)(void *);

static void klm_free_space(SIZE_T *largest, SIZE_T *total)
{   /* a walk over the user half of the address space */
    MEMORY_BASIC_INFORMATION mbi; BYTE *p = (BYTE *)0x10000;
    *largest = *total = 0;
    while (p < (BYTE *)0x7ffe0000 && VirtualQuery(p, &mbi, sizeof mbi)) {
        if (mbi.State == MEM_FREE) { *total += mbi.RegionSize; if (mbi.RegionSize > *largest) *largest = mbi.RegionSize; }
        p = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
}

static void klm_map_file(const char *when, int refused)
{   /* every region of the user half, one line each, into KLHook_map_<n>.txt beside the log (n = 0..7: the last eight level loads
       are kept; the first two refused requests after each go into KLHook_map_refused_0 / _1.txt). The line above says how much; two of these files, taken at the same point of two level loads, say
       WHICH allocations came in between and where they sit: `python debug/vmmap.py <map A> <map B>`.
       Columns: base, allocation base, size (hex), state F/C/R, type I/M/P, protection (hex), module of an image. */
    static LONG no, left = 2; static char buf[0x10000];
    char path[MAX_PATH], name[MAX_PATH], *leaf; MEMORY_BASIC_INFORMATION mbi; BYTE *p = (BYTE *)0x10000; HANDLE f; DWORD w, at = 0; SYSTEMTIME t; LONG n;
    if (!klm_maps) return;
    if (refused) { if (left <= 0) return; left--; n = no; snprintf(path, sizeof path, "%s\\KLHook_map_refused_%ld.txt", klh_out, 1 - left); }
    else { left = 2; n = InterlockedIncrement(&no) - 1; snprintf(path, sizeof path, "%s\\KLHook_map_%ld.txt", klh_out, n & 7); }
    f = CreateFileA(path, GENERIC_WRITE, FILE_SHARE_READ, 0, CREATE_ALWAYS, 0, 0);
    if (f == INVALID_HANDLE_VALUE) return;
    GetLocalTime(&t);
    at = (DWORD)snprintf(buf, sizeof buf, "# map %ld%s of process %lu, %02d:%02d:%02d, %s; the reserve is %p + %d MB and holds %d block(s)\r\n",
                         refused ? n : n + 1, refused ? " (a refused request after it)" : "", GetCurrentProcessId(), t.wHour, t.wMinute, t.wSecond, when, klm_reserve, klm_reserve ? klm_reserve_mb : 0, klm_n);
    while (p < (BYTE *)0x7ffe0000 && VirtualQuery(p, &mbi, sizeof mbi)) {
        name[0] = 0; leaf = name;
        if (mbi.State != MEM_FREE && mbi.Type == MEM_IMAGE && mbi.AllocationBase == mbi.BaseAddress && GetModuleFileNameA((HMODULE)mbi.AllocationBase, name, sizeof name))
            { leaf = strrchr(name, '\\'); leaf = leaf ? leaf + 1 : name; }
        if (at > sizeof buf - 400) { WriteFile(f, buf, at, &w, 0); at = 0; }
        at += (DWORD)snprintf(buf + at, 400, "%08lx %08lx %08lx %c %c %04lx %s\r\n", (unsigned long)(uintptr_t)mbi.BaseAddress,
                              (unsigned long)(uintptr_t)(mbi.State == MEM_FREE ? 0 : mbi.AllocationBase), (unsigned long)mbi.RegionSize,
                              mbi.State == MEM_FREE ? 'F' : mbi.State == MEM_COMMIT ? 'C' : 'R',
                              mbi.State == MEM_FREE ? '-' : mbi.Type == MEM_IMAGE ? 'I' : mbi.Type == MEM_MAPPED ? 'M' : 'P', (unsigned long)(mbi.State == MEM_COMMIT ? mbi.Protect : 0), leaf);
        p = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    if (at) WriteFile(f, buf, at, &w, 0);
    CloseHandle(f);
}

static void klm_map_line(const char *when, int refused)
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
    klm_map_file(when, refused);
    SetLastError(err);
}

static int klm_inside(LPCVOID p)
{
    return klm_reserve && (const BYTE *)p >= (const BYTE *)klm_reserve && (const BYTE *)p < (const BYTE *)klm_reserve + ((SIZE_T)klm_reserve_mb << 20);
}

static void *klm_from_reserve(SIZE_T size)
{   /* a block in the first gap of the reserve that fits, or 0: no reserve, no gap, the table is full, or the commit failed */
    SIZE_T room = (SIZE_T)klm_reserve_mb << 20, len = (size + 0xffff) & ~(SIZE_T)0xffff, at = 0; int i, k; void *p = 0;
    if (!klm_reserve || !klm_ok || !size || len < size || len > room) return 0;
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
    if (!p && klm_n >= KLM_BLOCKS && !InterlockedExchange(&klm_full_told, 1)) klog("memory: the reserve's table is full (%d blocks): no more blocks from it", KLM_BLOCKS);
    return p;
}

static int klm_release(LPVOID p, SIZE_T *asked, int *left, double *used_mb)
{   /* p is inside the reserve: decommit its block and drop it from the table; 0 = no block starts at p */
    SIZE_T off = (SIZE_T)((BYTE *)p - (BYTE *)klm_reserve); int i, found = 0;
    EnterCriticalSection(&klm_cs);
    for (i = 0; i < klm_n && klm_blk[i].off != off; i++) ;
    if (i < klm_n) {
        VirtualFree(p, klm_blk[i].len, MEM_DECOMMIT);  /* this block's pages only; they come back zeroed at the next commit */
        *asked = klm_blk[i].asked; klm_used -= klm_blk[i].len; klm_n--; found = 1;
        for (; i < klm_n; i++) klm_blk[i] = klm_blk[i + 1];
    }
    *left = klm_n; *used_mb = klm_used / 1048576.0;
    LeaveCriticalSection(&klm_cs);
    return found;
}

static LPVOID klm_small_failed(const char *fn, HANDLE heap, DWORD flags, SIZE_T size, void *ret, int can)
{   /* K47A (DM05A, 2026-10-25): the process heap refused 0x2ba0 bytes for the game allocator 0x7bb2c0 (its heap is GetProcessHeap(), kl2 has no
       HeapCreate), which does not test the result: 0x8e5bbd writes its 0x12345678 header to 0. Free address space was 385 MB, largest piece 64 MB at
       the last line before, and this path did not log. Now it logs what ran out (commit or address space) and, with SmallRescue=1, answers from the
       reserve (64 KB a block, committed zeroed; klm_HeapFree / klm_HeapSize already know reserve blocks). If commit is what ran out, that fails too.
       fn = "HeapAlloc" or "_aligned_malloc" (then flags = the alignment); can = 0: the caller's free path would not see a reserve block. */
    MEMORYSTATUSEX ms; SIZE_T largest = 0, total = 0; DWORD err = GetLastError(); LONG n = InterlockedIncrement(&klm_nulls); LPVOID p = 0;
    if (klm_small && can && klm_reserve) p = klm_from_reserve(size);
    if (n <= 32) {                                      /* a runaway must not fill the disk */
        ms.dwLength = sizeof ms; if (!GlobalMemoryStatusEx(&ms)) ms.ullAvailPageFile = ms.ullTotalPageFile = ms.ullAvailVirtual = 0;
        klm_free_space(&largest, &total);
        klog("memory: %s(heap %p, flags/align %lx, %lu bytes) from %p returned NULL (#%ld, error %lu); free address space %.0f MB, largest piece %.1f MB; "
             "commit left %.0f of %.0f MB; %s (the reserve holds %d block(s), %.1f of %d MB)",
             fn, heap, flags, (unsigned long)size, ret, n, err, total / 1048576.0, largest / 1048576.0, ms.ullAvailPageFile / 1048576.0, ms.ullTotalPageFile / 1048576.0,
             p ? "answered from the reserve" : !klm_small ? "SmallRescue=0: the caller gets NULL" : !can ? "not rescuable here: the caller gets NULL" :
             !klm_reserve ? "no reserve: the caller gets NULL" : "the reserve could not answer it either: the caller gets NULL",
             klm_n, klm_used / 1048576.0, klm_reserve ? klm_reserve_mb : 0);
        if (n <= 2) klm_map_line(p ? "at a refused small request" : "at a refused small request (not answered)", 1);
    }
    SetLastError(err);
    return p;
}

static LPVOID WINAPI klm_HeapAlloc(HANDLE heap, DWORD flags, SIZE_T size)
{
    LPVOID p; SIZE_T largest = 0, total = 0; DWORD err; int first = 0;
    if (size < (1u << 20)) { p = klm_real_HeapAlloc(heap, flags, size); return (p || !size) ? p : klm_small_failed("HeapAlloc", heap, flags, size, _ReturnAddress(), 1); }
    if (size >= ((SIZE_T)klm_mid_mb << 20) || size >= (16u << 20)) {
        err = GetLastError(); klm_free_space(&largest, &total); SetLastError(err);
        if (klm_log) klog("memory: a block of %.1f MB is asked for; free address space %.0f MB, largest piece %.1f MB (the reserve holds %d block(s), %.1f of %d MB)",
                          size / 1048576.0, total / 1048576.0, largest / 1048576.0, klm_n, klm_used / 1048576.0, klm_reserve ? klm_reserve_mb : 0);
        first = size >= ((SIZE_T)klm_big_mb << 20) || (size >= ((SIZE_T)klm_mid_mb << 20) && largest < ((SIZE_T)klm_room_mb << 20));
        if (klm_log && size >= ((SIZE_T)klm_big_mb << 20)) klm_map_line("at the level's largest block", 0);
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
    klm_map_line(p ? "at the refused request" : "at the fault", 1);
    return p;
}

static BOOL WINAPI klm_HeapFree(HANDLE heap, DWORD flags, LPVOID p)
{
    SIZE_T asked = 0; int n = 0; double used = 0;
    if (!p || !klm_inside(p)) return klm_real_HeapFree(heap, flags, p);
    if (!klm_release(p, &asked, &n, &used)) { klog("memory: HeapFree of %p, which is inside the reserve but no block of it - refused", p); SetLastError(ERROR_INVALID_PARAMETER); return FALSE; }
    if (klm_log && asked >= (1u << 20)) klog("memory: the block of %.1f MB in the reserve was freed by the game (it holds %d block(s), %.1f MB now)", asked / 1048576.0, n, used);
    return TRUE;
}

static BOOL WINAPI klm_HeapValidate(HANDLE heap, DWORD flags, LPCVOID p)
{
    SIZE_T off; int i, found = 0;
    if (!p || !klm_inside(p)) return klm_real_HeapValidate(heap, flags, p);
    off = (SIZE_T)((const BYTE *)p - (const BYTE *)klm_reserve);
    EnterCriticalSection(&klm_cs);
    for (i = 0; i < klm_n; i++) if (klm_blk[i].off == off) found = 1;
    LeaveCriticalSection(&klm_cs);
    return found;
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

static void *__cdecl klm_aligned_malloc(size_t size, size_t align)
{   /* K44P2b, K47B, K48A (2026-10-25): 0x6d2107 = the ADPCM decoder writing to 0. The sound buffer's Lock (ZSoundBufferOpenAL slot 29, 0x75db50) takes
       _aligned_malloc(size + 0x10, 0x10) through the import 0xb10398 and returns true without testing it. A reserve block is 64 KB aligned, so it
       answers any alignment up to that; its free comes back through _aligned_free (0xb1039c), wrapped below. */
    void *p = klm_real_aligned_malloc(size, align);
    return (p || !size) ? p : klm_small_failed("_aligned_malloc", 0, (DWORD)align, size, _ReturnAddress(), klm_aligned && align <= 0x10000);
}

static void __cdecl klm_aligned_free(void *p)
{
    SIZE_T asked = 0; int n = 0; double used = 0;
    if (!p || !klm_inside(p)) { klm_real_aligned_free(p); return; }
    if (!klm_release(p, &asked, &n, &used)) klog("memory: _aligned_free of %p, which is inside the reserve but no block of it - ignored", p);
}

/* THE GAME'S THREADS BY ROUTINE (k48g). K48F_A: with OtherStackKB=2048, 70 of the 4 MB stacks left were kl2.exe's own threads (280 MB), the
   deepest of all of them 1280 KB committed. Which routine needs how much is what GameStackKB needs: every thread made through the two wrapped
   imports starts in klm_thread_start, which notes its routine and its stack, and the 60 s line gives the deepest commit seen per routine. */
#define KLM_THREADS 512
static struct klm_thr { void *fn, *arg; BYTE *lo, *top; SIZE_T res, deep; volatile LONG live; } klm_thr[KLM_THREADS];
static volatile LONG klm_nthr, klm_thr_full;
static int klm_game_kb;                                 /* GameStackKB: 0 = kl2's threads keep 4 MB */
static DWORD klm_keep[16]; static int klm_nkeep;        /* GameStackKeep: routines (kl2.exe offsets) that keep 4 MB anyway */

static SIZE_T klm_depth(struct klm_thr *t)
{   /* the committed part of a stack noted in klm_thread_start: every committed region of its allocation summed (the top page is a region
       of its own - K48G_A read 4 KB for every thread from the top region alone). 0 once it is gone */
    MEMORY_BASIC_INFORMATION mbi; BYTE *p = t->lo; SIZE_T c = 0;
    if (!t->top || !p) return 0;
    while (p < t->top && VirtualQuery(p, &mbi, sizeof mbi) && mbi.AllocationBase == t->lo) {
        if (mbi.State == MEM_COMMIT) c += mbi.RegionSize;
        p = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    return c;
}

static void klm_note_depth(struct klm_thr *t)
{
    SIZE_T d = t->live ? klm_depth(t) : 0;
    if (d > t->deep) t->deep = d;
}

static DWORD WINAPI klm_thread_start(LPVOID p)
{   /* one frame above the game's routine: where its stack is, then the routine itself (same ABI for CreateThread and _beginthreadex) */
    struct klm_thr *t = (struct klm_thr *)p; MEMORY_BASIC_INFORMATION mbi; DWORD r;
    t->top = (BYTE *)((NT_TIB *)NtCurrentTeb())->StackBase;
    if (VirtualQuery(&mbi, &mbi, sizeof mbi)) { t->lo = (BYTE *)mbi.AllocationBase; t->res = (SIZE_T)(t->top - t->lo); }
    t->live = 1;
    r = ((DWORD (WINAPI *)(LPVOID))t->fn)(t->arg);     /* a routine ending in ExitThread / _endthreadex skips the rest: 'live' stays 1 (census only) */
    klm_note_depth(t); t->live = 0;
    return r;
}

static struct klm_thr *klm_thr_new(void *fn, void *arg)
{   /* a slot for a new thread; 0 = table full (the thread then starts as it would without the hook) */
    LONG i = InterlockedIncrement(&klm_nthr) - 1;
    if (i >= KLM_THREADS) { InterlockedIncrement(&klm_thr_full); return 0; }
    klm_thr[i].fn = fn; klm_thr[i].arg = arg;
    return &klm_thr[i];
}

static int klm_kept_routine(void *fn)
{
    DWORD off = (DWORD)((BYTE *)fn - (BYTE *)GetModuleHandleA(0)); int i;
    for (i = 0; i < klm_nkeep; i++) if (klm_keep[i] == off) return 1;
    return 0;
}

static SIZE_T klm_game_stack(SIZE_T stack, DWORD *flags, void *fn)
{   /* the stack a thread of kl2.exe's own gets. StackMB: the default is shrunk (the old, WRONG set: the game's deep threads are among them).
       OtherStackKB: the exe header's default is lowered for everyone else, so the game's own threads are given the header's old 4 MB
       explicitly, or GameStackKB unless their routine is in GameStackKeep. A size passed without the flag is a commit size, reserved from
       the (now lower) header default: it becomes a reservation too (the commit then grows on demand, as for the default). */
    if (klm_stack_mb > 0 && !stack) { *flags |= STACK_SIZE_PARAM_IS_A_RESERVATION; InterlockedIncrement(&klm_threads); return (SIZE_T)klm_stack_mb << 20; }
    if (klm_exe_reserve && (!stack || (!(*flags & STACK_SIZE_PARAM_IS_A_RESERVATION) && stack < klm_exe_reserve))) {
        SIZE_T want = klm_game_kb && !klm_kept_routine(fn) ? (SIZE_T)klm_game_kb << 10 : klm_exe_reserve;
        if (stack > want) { InterlockedIncrement(&klm_threads); return stack; }   /* a commit bigger than the shrunk reserve: as asked (reserve = that commit) */
        *flags |= STACK_SIZE_PARAM_IS_A_RESERVATION;
        if (want == klm_exe_reserve) InterlockedIncrement(&klm_kept); else InterlockedIncrement(&klm_threads);
        return want;
    }
    return stack;
}

static HANDLE WINAPI klm_CreateThread(LPSECURITY_ATTRIBUTES sa, SIZE_T stack, LPTHREAD_START_ROUTINE fn, LPVOID arg, DWORD flags, LPDWORD id)
{
    struct klm_thr *t = klm_thr_new((void *)fn, arg);
    stack = klm_game_stack(stack, &flags, (void *)fn);
    return t ? klm_real_CreateThread(sa, stack, klm_thread_start, t, flags, id) : klm_real_CreateThread(sa, stack, fn, arg, flags, id);
}

static uintptr_t __cdecl klm_beginthreadex(void *sec, unsigned stack, unsigned (__stdcall *fn)(void *), void *arg, unsigned flags, unsigned *id)
{   /* the C runtime hands stack and flags to CreateThread as they are */
    struct klm_thr *t = klm_thr_new((void *)fn, arg); DWORD f = flags;
    stack = (unsigned)klm_game_stack(stack, &f, (void *)fn);
    return t ? klm_real_beginthreadex(sec, stack, (unsigned (__stdcall *)(void *))klm_thread_start, t, (unsigned)f, id)
             : klm_real_beginthreadex(sec, stack, fn, arg, (unsigned)f, id);
}

static void klm_routines(void)
{   /* the 60 s line: per routine (kl2.exe offset, or an address outside it) how many threads, how many alive, reserve, deepest commit */
    struct { void *fn; int n, alive; SIZE_T res, deep; } r[48]; int nr = 0, i, j, n; LONG cnt = klm_nthr; char line[1400];
    if (cnt > KLM_THREADS) cnt = KLM_THREADS;
    for (i = 0; i < cnt; i++) {
        struct klm_thr *t = &klm_thr[i];
        if (!t->fn) continue;
        klm_note_depth(t);
        for (j = 0; j < nr && r[j].fn != t->fn; j++) ;
        if (j == nr) { if (nr == 48) continue; r[nr].fn = t->fn; r[nr].n = r[nr].alive = 0; r[nr].res = r[nr].deep = 0; nr++; }
        r[j].n++; if (t->live) r[j].alive++;
        if (t->res > r[j].res) r[j].res = t->res;
        if (t->deep > r[j].deep) r[j].deep = t->deep;
    }
    n = _snprintf(line, sizeof line, "memory: game threads by routine (%ld made, %ld not followed): ", klm_nthr, klm_thr_full);
    for (i = 0; i < nr && n > 0 && n < (int)sizeof line; i++) {
        BYTE *exe = (BYTE *)GetModuleHandleA(0); int k;
        DWORD off = (DWORD)((BYTE *)r[i].fn - exe);
        k = off < 0x1000000 ? _snprintf(line + n, sizeof line - n, "%s+%lx x%d (%d alive) %lu/%lu KB", i ? "; " : "", off, r[i].n, r[i].alive, (DWORD)(r[i].deep >> 10), (DWORD)(r[i].res >> 10))
                            : _snprintf(line + n, sizeof line - n, "%s%p x%d (%d alive) %lu/%lu KB", i ? "; " : "", r[i].fn, r[i].n, r[i].alive, (DWORD)(r[i].deep >> 10), (DWORD)(r[i].res >> 10));
        if (k < 0) break;
        n += k;
    }
    line[sizeof line - 1] = 0;
    klog("%s", line);
}

static void klm_other_stacks(void)
{   /* OtherStackKB: the in-memory PE header of kl2.exe (data, not code) is what CreateThread reads for a thread that asks for the default
       stack: K48D_A had 65 stacks of 4 MB (260 MB of address space), 62 of them used at most 72 KB. Win10 WOW64 reads the header in memory
       for CreateThread / _beginthreadex (probe exe, 10-25: 4096 -> 1024 KB); thread-pool workers keep the size taken at process start, and
       threads made before this runs keep 4 MB. */
    BYTE *b = (BYTE *)GetModuleHandleA(0); IMAGE_NT_HEADERS32 *nt; DWORD old, want;
    if (!klm_other_kb || !b || ((IMAGE_DOS_HEADER *)b)->e_magic != IMAGE_DOS_SIGNATURE) return;
    nt = (IMAGE_NT_HEADERS32 *)(b + ((IMAGE_DOS_HEADER *)b)->e_lfanew);
    want = (DWORD)klm_other_kb << 10;
    if (nt->Signature != IMAGE_NT_SIGNATURE || want >= nt->OptionalHeader.SizeOfStackReserve || want < nt->OptionalHeader.SizeOfStackCommit) {
        klog("memory: OtherStackKB=%d not applied (the header reserves %lu KB, commits %lu KB)", klm_other_kb,
             nt->OptionalHeader.SizeOfStackReserve >> 10, nt->OptionalHeader.SizeOfStackCommit >> 10);
        return;
    }
    old = nt->OptionalHeader.SizeOfStackReserve;
    klm_exe_reserve = old;                              /* before the write: a thread made meanwhile by the game must already get 4 MB */
    if (!klh_poke(&nt->OptionalHeader.SizeOfStackReserve, &old, 4, &want, 4, "OtherStackKB")) {
        klm_exe_reserve = 0; klog("memory: OtherStackKB: the exe header was not changed"); return;
    }
    klog("memory: OtherStackKB: a thread that asks for the default stack now reserves %d KB instead of %lu KB; kl2.exe's own threads keep %lu KB",
         klm_other_kb, (DWORD)(klm_exe_reserve >> 10), (DWORD)(klm_exe_reserve >> 10));
}

static void klm_owners(char *out, int cap)
{   /* who holds the address space, for the 10 s line: modules / mapped / private split, and the four biggest private allocations (one
       VirtualAlloc each: a heap segment, a driver buffer, a thread stack, the reserve) with their committed part. Who made one is not known
       here; the base address is for KLHook_map_*.txt and a dump. */
    MEMORY_BASIC_INFORMATION mbi; BYTE *p = (BYTE *)0x10000; void *base = 0; SIZE_T image = 0, mapped = 0, commit = 0, reserved = 0, sz = 0, cm = 0;
    struct { void *base; SIZE_T sz, cm; } top[4] = { 0 }; int i, k, n, g = 0, nbig = 0, nsmall = 0;
    SIZE_T sbig = 0, ssmall = 0, deepbig = 0, deepsmall = 0;   /* thread stacks (an allocation with a guard page): 4 MB ones and smaller ones */
    for (;;) {
        int more = p < (BYTE *)0x7ffe0000 && VirtualQuery(p, &mbi, sizeof mbi);
        if (!more || mbi.State == MEM_FREE || mbi.Type != MEM_PRIVATE || mbi.AllocationBase != base) {   /* the allocation in hand ends */
            if (base && sz > top[3].sz) {
                for (i = 0; i < 3 && sz <= top[i].sz; i++) ;
                for (k = 3; k > i; k--) top[k] = top[k - 1];
                top[i].base = base; top[i].sz = sz; top[i].cm = cm;
            }
            if (base && g) {
                if (sz >= ((SIZE_T)4 << 20)) { nbig++; sbig += sz; if (cm > deepbig) deepbig = cm; }
                else { nsmall++; ssmall += sz; if (cm > deepsmall) deepsmall = cm; }
            }
            base = 0; sz = cm = 0; g = 0;
        }
        if (!more) break;
        if (mbi.State != MEM_FREE) {
            if (mbi.Type == MEM_IMAGE) image += mbi.RegionSize; else if (mbi.Type == MEM_MAPPED) mapped += mbi.RegionSize;
            else {
                if (mbi.State == MEM_COMMIT) { commit += mbi.RegionSize; cm += mbi.RegionSize; } else reserved += mbi.RegionSize;
                base = mbi.AllocationBase; sz += mbi.RegionSize;
                if (mbi.State == MEM_COMMIT && (mbi.Protect & PAGE_GUARD)) g = 1;
            }
        }
        p = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    n = _snprintf(out, cap, "modules %.0f MB, mapped %.0f, private committed %.0f, private reserved only %.0f; thread stacks: %d of 4 MB or more (%.0f MB, "
                  "deepest %.0f KB), %d smaller (%.0f MB, deepest %.0f KB), %ld game thread(s) given 4 MB; biggest private:",
                  image / 1048576.0, mapped / 1048576.0, commit / 1048576.0, reserved / 1048576.0, nbig, sbig / 1048576.0, deepbig / 1024.0,
                  nsmall, ssmall / 1048576.0, deepsmall / 1024.0, klm_kept);
    for (i = 0; i < 4 && top[i].sz && n > 0 && n < cap; i++) {
        k = _snprintf(out + n, cap - n, " %p %.1f MB (%.1f committed)%s", top[i].base, top[i].sz / 1048576.0, top[i].cm / 1048576.0, top[i].base == klm_reserve ? " = the reserve" : "");
        if (k < 0) break;   /* truncated */
        n += k;
    }
    out[cap - 1] = 0;
}

static void klm_tick(void)
{
    static DWORD calls, last, routines; static LONG told; DWORD now; SIZE_T largest, total; char who[600];
    if (!klm_on || (calls++ & 63)) return;
    if (klm_stack_mb > 0 && klm_threads != told) { told = klm_threads; if (klm_log) klog("memory: %ld game thread(s) so far started with a %d MB stack instead of 4 MB", told, klm_stack_mb); }
    now = GetTickCount();
    if (klm_log && now - last >= 10000) {             /* K48B: free space fell from 419 MB after the load to 16 MB in round 1; this shows the slope */
        last = now; klm_free_space(&largest, &total); klm_owners(who, sizeof who);
        klog("memory: every 10 s: free address space %.0f MB, largest piece %.1f MB; the reserve holds %d block(s), %.1f of %d MB; refused small requests so far %ld; %s",
             total / 1048576.0, largest / 1048576.0, klm_n, klm_used / 1048576.0, klm_reserve ? klm_reserve_mb : 0, klm_nulls, who);
        if (klm_nthr && ++routines % 6 == 1) klm_routines();   /* every 60 s, the first at 10 s */
    }
}

static void klm_init(void)
{
    SIZE_T largest, total; int n = 0;
    klm_on = GetPrivateProfileIntA("Memory", "Enable", 1, klh_ini);
    if (!klm_on) return;
    klm_log = GetPrivateProfileIntA("Memory", "Log", 1, klh_ini);
    klm_maps = GetPrivateProfileIntA("Memory", "Maps", 1, klh_ini);
    klm_reserve_mb = (int)GetPrivateProfileIntA("Memory", "ReserveMB", 128, klh_ini); if (klm_reserve_mb < 0 || klm_reserve_mb > 512) klm_reserve_mb = 128;
    klm_stack_mb = (int)GetPrivateProfileIntA("Memory", "StackMB", 0, klh_ini); if (klm_stack_mb < 0 || klm_stack_mb > 3) klm_stack_mb = 0;
    klm_big_mb = (int)GetPrivateProfileIntA("Memory", "BigMB", 48, klh_ini); if (klm_big_mb < 1 || klm_big_mb > 512) klm_big_mb = 48;
    klm_mid_mb = (int)GetPrivateProfileIntA("Memory", "MidMB", 16, klh_ini); if (klm_mid_mb < 1 || klm_mid_mb > 512) klm_mid_mb = 16;
    klm_room_mb = (int)GetPrivateProfileIntA("Memory", "RoomMB", 0, klh_ini); if (klm_room_mb < 0 || klm_room_mb > 2048) klm_room_mb = 0;
    klm_small = GetPrivateProfileIntA("Memory", "SmallRescue", 1, klh_ini) != 0;
    klm_other_kb = (int)GetPrivateProfileIntA("Memory", "OtherStackKB", 0, klh_ini); if (klm_other_kb < 0 || klm_other_kb > 4096) klm_other_kb = 0;
    if (klm_other_kb && klm_other_kb < 256) klm_other_kb = 256;      /* a floor: the shallow threads in K48D_A used up to 72 KB */
    klm_game_kb = (int)GetPrivateProfileIntA("Memory", "GameStackKB", 0, klh_ini); if (klm_game_kb < 0 || klm_game_kb >= 4096) klm_game_kb = 0;
    if (klm_game_kb && klm_game_kb < 2048) klm_game_kb = 2048;       /* a floor: K48F_A's deepest game thread committed 1280 KB (one run, one map); deeper routines go in GameStackKeep */
    {   char keep[256], *q, *e; DWORD v;
        GetPrivateProfileStringA("Memory", "GameStackKeep", "", keep, sizeof keep, klh_ini);
        for (q = keep; *q && klm_nkeep < 16; ) {
            v = strtoul(q, &e, 16);
            if (e == q) { q++; continue; }             /* not a hex digit (comma, space, '+'): step over it */
            klm_keep[klm_nkeep++] = v; q = e;
        }
    }
    InitializeCriticalSection(&klm_cs);
    klm_free_space(&largest, &total);
    if (klm_reserve_mb > 0) klm_reserve = VirtualAlloc(0, (SIZE_T)klm_reserve_mb << 20, MEM_RESERVE, PAGE_NOACCESS);
    /* HeapFree and HeapSize first: a block is only handed out of the reserve when its free can be seen */
    n += klh_iat("KERNEL32.dll", "HeapFree", (void *)klm_HeapFree, (void **)&klm_real_HeapFree);
    n += klh_iat("KERNEL32.dll", "HeapSize", (void *)klm_HeapSize, (void **)&klm_real_HeapSize);
    n += klh_iat("KERNEL32.dll", "HeapValidate", (void *)klm_HeapValidate, (void **)&klm_real_HeapValidate);
    if (!klm_real_HeapValidate) klm_small = 0;      /* rescue only small blocks the game cannot tell from heap blocks */
    klm_ok = klm_real_HeapFree && klm_real_HeapSize;   /* a wrapper that is in place keeps its real pointer: it is still called */
    if (!klm_ok) klog("memory: HeapFree or HeapSize NOT wrapped: the reserve is not used");
    /* the free first, as above; the sound buffers' allocation (see klm_aligned_malloc) */
    n += klh_iat("MSVCR90.dll", "_aligned_free", (void *)klm_aligned_free, (void **)&klm_real_aligned_free);
    if (klm_real_aligned_free) n += klh_iat("MSVCR90.dll", "_aligned_malloc", (void *)klm_aligned_malloc, (void **)&klm_real_aligned_malloc);
    klm_aligned = klm_real_aligned_free && klm_real_aligned_malloc;
    n += klh_iat("KERNEL32.dll", "HeapAlloc", (void *)klm_HeapAlloc, (void **)&klm_real_HeapAlloc);
    if (klm_stack_mb || klm_other_kb) {
        int a = klh_iat("KERNEL32.dll", "CreateThread", (void *)klm_CreateThread, (void **)&klm_real_CreateThread);
        int b = klh_iat("MSVCR90.dll", "_beginthreadex", (void *)klm_beginthreadex, (void **)&klm_real_beginthreadex);
        n += a + b;
        /* the header is lowered only once both of the game's thread imports hand its threads the old 4 MB */
        if (klm_other_kb && a && b) {
            klm_other_stacks();
            if (klm_game_kb && klm_exe_reserve) klog("memory: GameStackKB: kl2.exe's own new threads reserve %d KB; %d routine(s) in GameStackKeep keep %lu KB", klm_game_kb, klm_nkeep, (DWORD)(klm_exe_reserve >> 10));
        }
        else if (klm_other_kb) klog("memory: OtherStackKB not applied: CreateThread %s, _beginthreadex %s", a ? "wrapped" : "NOT wrapped", b ? "wrapped" : "NOT wrapped");
    }
    klog("memory: at start %.0f MB of address space free, largest piece %.1f MB; reserve of %d MB %s (blocks of %d MB or more go into it, any of 1 MB or more that the heap refuses, and - RoomMB - of %d MB or more while the largest free piece is under %d MB); HeapAlloc %s, HeapFree %s; game thread stacks %s (%d import slot(s))",
         total / 1048576.0, largest / 1048576.0, klm_reserve_mb, klm_reserve ? "held for the whole run" : klm_reserve_mb ? "NOT available" : "off", klm_big_mb, klm_mid_mb, klm_room_mb,
         klm_real_HeapAlloc ? "wrapped" : "NOT wrapped", klm_real_HeapFree ? "wrapped" : "NOT wrapped", klm_stack_mb ? "reduced" : "left at 4 MB", n);
    if (klm_log) klog("memory: _aligned_malloc %s; SmallRescue %s", klm_aligned ? "wrapped" : "NOT wrapped", klm_small ? "on" : "off");
    if ((!klm_real_HeapAlloc || !klm_ok) && klm_reserve) { VirtualFree(klm_reserve, 0, MEM_RELEASE); klm_reserve = 0; }   /* nobody could use it */
}

#endif /* KLMEM_C */
