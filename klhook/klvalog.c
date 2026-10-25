/*
 * klvalog.c - who takes the address space: VirtualAlloc / VirtualFree / VirtualAllocEx / HeapCreate wrapped in the import tables of the
 * OTHER modules of the process (drivers, overlays, system DLLs), with the calling module named. TEST build only. Part of KLHook.
 *
 * WHY: LC6_B (DM05A, 2026-10-25) ran out of address space ~40 s into round 1. Its KLHook_map files (load -> first refusal) show 16 private
 * allocations of 15.81 MB, fully committed (253 MB), and a halving series (7.91 MB x7, 3.95 x9, 1.98 x15, 0.99 x21, 0.50 x25), read-write
 * runs separated by single committed PAGE_NOACCESS pages. Not kl2's HeapAlloc (klmem.c logs >= 16 MB, nothing), not kl2's own two
 * VirtualAlloc sites (0x4108e8 commits into its own reserve, 0x504903 = the small-block allocator's init). nvd3dum.dll and nvgpucomp32.dll
 * import KERNEL32!VirtualAlloc (pefile, 10-25); ReShade32, gameoverlayrenderer, medal-hook32, nvspcap are loaded too.
 *
 * WHAT: a watcher thread looks at the module list every 2 s; each module not seen before (except ntdll, kernel32, kernelbase and this DLL)
 * has every slot of its import address table (the IAT data directory) that holds one of the targets' addresses (kernel32's or kernelbase's
 * export) pointed at the wrapper. A slot is changed only from the expected value to the wrapper (klh_poke). The wrapper calls kernelbase's
 * export. Calls through GetProcAddress, through ntdll's NtAllocateVirtualMemory or from inside the heap manager are NOT seen.
 * Per calling module: calls, reserved / committed bytes, what is still reserved (allocations of 64 KB+ in a table, minus MEM_RELEASE).
 * One line per call of 512 KB or more (the first 400), the per-module table every 10 s.
 *
 * K49_VA (DM05A, 10-25): no module made a call of 512 KB+ through its IAT, yet 17 more blocks of 15.81 MB (+ the halving series) came in
 * 29 s and every refusal was kl2's HeapAlloc (0x7bb33c) on heap 01D90000. The halving series is how the NT heap grows (a new segment twice
 * the last, halved while the reservation fails), inside ntdll. So, also every 10 s:
 *   the heaps of the process (GetProcessHeaps) with HeapSummary's committed / reserved (P = GetProcessHeap, C = msvcr90's _get_heap_handle),
 *   and kl2's HeapAlloc bytes of the last 10 s by caller: for a call from ZWin32Allocator (0x7bb2c0 -> HeapAlloc at 0x7bb336, return
 *   0x7bb33c) the caller is the return address of 0x7bb2c0 itself: [esp] of the wrapper + 7 dwords (3 arguments, edi/esi/ebx pushed by
 *   0x7bb2c4..c6). Gross bytes, not net: frees are not matched to callers.
 *
 * K49B_HEAP (DM05A, 10-25): the process heap P holds it all (reserved 1108 MB by 03:38, allocated swinging ~550 <-> ~1035 MB every ~20 s), but
 * kl2's HeapAlloc import moves only ~53 MB per 10 s (one caller: 0x4aa067, the pool routine 0x4aa010 calling ZWin32Allocator 0x7bb2c0 through
 * its vtable +8). So the rest of P's traffic comes from other modules. Now also wrapped in the other modules' IATs: HeapAlloc / HeapFree /
 * HeapReAlloc (kernel32's exports are forwarders: their slots hold ntdll's RtlAllocateHeap / RtlFreeHeap / RtlReAllocateHeap, which are
 * matched too). Per module, lock-free: bytes allocated / freed on P (a free is sized with HeapSize first), bytes allocated on other heaps,
 * calls - every 10 s, the 10 biggest by P traffic. kl2's own path (operator new 0x89e850 -> 0x4a2fd0 -> 0x4aa010 -> 0x7bb2c0, re/dm05a_heap_1025.md):
 * [7] = 0x4aa067 -> [17] (0x4aa010: sub esp,0xc + ebx/esi/edi + 3 arguments of the vtable call); 0x4a3009 -> [22] (0x4a2fd0: esi/edi + 2
 * arguments); 0x89e85c -> [25] (operator new: 2 arguments). Also the count of small requests (n <= 0x80) and kl2's small-block pool gate
 * byte 0xddb89c (set only by 0x5048f0, statically never called in DD).
 *
 * [Memory] VaLog=1   (default 0; TEST build only: nothing of this is in a SHIP build)
 */
#define KLVA_MODS 192
#define KLVA_LIVE 8192
static int klva_on;
static volatile LONG klva_lines;
static LPVOID (WINAPI *klva_real_alloc)(LPVOID, SIZE_T, DWORD, DWORD);
static BOOL (WINAPI *klva_real_free)(LPVOID, SIZE_T, DWORD);
static LPVOID (WINAPI *klva_real_allocex)(HANDLE, LPVOID, SIZE_T, DWORD, DWORD);
static HANDLE (WINAPI *klva_real_heapcreate)(DWORD, SIZE_T, SIZE_T);
static struct { BYTE *base; DWORD size; char name[40]; LONG calls, heaps; double res, com, live; } klva_mod[KLVA_MODS];
static int klva_nmod;
static struct { BYTE *at; SIZE_T size; int mod; } klva_live[KLVA_LIVE];
static int klva_nlive; static LONG klva_live_full;
static CRITICAL_SECTION klva_cs;
static LPVOID (WINAPI *klva_real_halloc)(HANDLE, DWORD, SIZE_T);
static BOOL (WINAPI *klva_real_hfree)(HANDLE, DWORD, LPVOID);
static LPVOID (WINAPI *klva_real_hrealloc)(HANDLE, DWORD, LPVOID, SIZE_T);
static SIZE_T (WINAPI *klva_real_hsize)(HANDLE, DWORD, LPCVOID);
static HANDLE klva_pheap;
/* the patched modules' ranges, appended by klva_watch only (row 0 = a caller outside them); read without a lock */
static struct { DWORD_PTR base, end; char name[40]; int crt; volatile LONG64 pa, pf, oa; volatile LONG calls; LONG64 lpa, lpf, loa; LONG lcalls; } klva_hm[KLVA_MODS];
static volatile LONG klva_nhm = 1;

static int klva_who(void *ret)
{   /* the index of the module ret lies in (added on first sight; its name is filled in by klva_tick, outside klva_cs: GetModuleFileName takes
       the loader lock, and a DllMain under it may be the caller), -1 = none. Inside klva_cs */
    MEMORY_BASIC_INFORMATION mbi; int i;
    if (!VirtualQuery(ret, &mbi, sizeof mbi) || mbi.Type != MEM_IMAGE) return -1;
    for (i = 0; i < klva_nmod; i++) if (klva_mod[i].base == (BYTE *)mbi.AllocationBase) return i;
    if (klva_nmod >= KLVA_MODS) return -1;
    i = klva_nmod;
    klva_mod[i].base = (BYTE *)mbi.AllocationBase; klva_mod[i].name[0] = 0;
    klva_nmod++;
    return i;
}

static void klva_note(const char *fn, void *ret, LPVOID want, SIZE_T size, DWORD type, DWORD prot, LPVOID got)
{
    DWORD err = GetLastError(); int m, i; LONG n;
    EnterCriticalSection(&klva_cs);
    m = klva_who(ret);
    if (m >= 0) {
        klva_mod[m].calls++;
        if (got && (type & MEM_RESERVE)) klva_mod[m].res += size;
        if (got && (type & MEM_COMMIT)) klva_mod[m].com += size;
    }
    if (got && (type & MEM_RESERVE) && size >= 0x10000) {
        if (klva_nlive < KLVA_LIVE) { i = klva_nlive++; klva_live[i].at = (BYTE *)got; klva_live[i].size = size; klva_live[i].mod = m; if (m >= 0) klva_mod[m].live += size; }
        else klva_live_full++;
    }
    LeaveCriticalSection(&klva_cs);
    if (size >= 0x80000 && (n = InterlockedIncrement(&klva_lines)) <= 400) {
        char mod[64]; DWORD off; klh_module((DWORD_PTR)ret, mod, sizeof mod, &off);
        klog("va: %s+%lx %s(%p, %.2f MB, type %lx, protect %lx) -> %p", mod, off, fn, want, size / 1048576.0, type, prot, got);
    }
    SetLastError(err);
}

static LPVOID WINAPI klva_alloc(LPVOID at, SIZE_T size, DWORD type, DWORD prot)
{
    LPVOID p = klva_real_alloc(at, size, type, prot);
    klva_note("VirtualAlloc", _ReturnAddress(), at, size, type, prot, p);
    return p;
}

static LPVOID WINAPI klva_allocex(HANDLE proc, LPVOID at, SIZE_T size, DWORD type, DWORD prot)
{
    LPVOID p = klva_real_allocex(proc, at, size, type, prot);
    if (proc == GetCurrentProcess() || GetProcessId(proc) == GetCurrentProcessId()) klva_note("VirtualAllocEx", _ReturnAddress(), at, size, type, prot, p);
    return p;
}

static BOOL WINAPI klva_free(LPVOID at, SIZE_T size, DWORD type)
{
    BOOL ok = klva_real_free(at, size, type); DWORD err = GetLastError(); int i;
    if (ok && (type & MEM_RELEASE)) {
        EnterCriticalSection(&klva_cs);
        for (i = 0; i < klva_nlive && klva_live[i].at != (BYTE *)at; i++) ;
        if (i < klva_nlive) {
            if (klva_live[i].mod >= 0) klva_mod[klva_live[i].mod].live -= klva_live[i].size;
            klva_live[i] = klva_live[--klva_nlive];
        }
        LeaveCriticalSection(&klva_cs);
    }
    SetLastError(err);
    return ok;
}

static HANDLE WINAPI klva_heapcreate(DWORD flags, SIZE_T init, SIZE_T max)
{
    HANDLE h = klva_real_heapcreate(flags, init, max); DWORD err = GetLastError(); void *ret = _ReturnAddress(); int m; LONG n;
    EnterCriticalSection(&klva_cs); m = klva_who(ret); if (m >= 0) klva_mod[m].heaps++; LeaveCriticalSection(&klva_cs);
    if ((n = InterlockedIncrement(&klva_lines)) <= 400) {
        char mod[64]; DWORD off; klh_module((DWORD_PTR)ret, mod, sizeof mod, &off);
        klog("va: %s+%lx HeapCreate(flags %lx, initial %.2f MB, max %.2f MB) -> %p", mod, off, flags, init / 1048576.0, max / 1048576.0, h);
    }
    SetLastError(err);
    return h;
}

static int klva_hmod(void *ret)
{   /* the row of the patched module ret lies in, 0 = none; no lock (rows are only appended, klva_nhm is raised after the row is written) */
    DWORD_PTR a = (DWORD_PTR)ret; LONG i, n = klva_nhm;
    for (i = 1; i < n; i++) if (a >= klva_hm[i].base && a < klva_hm[i].end) return i;
    return 0;
}

static LONG64 klva_rd64(volatile LONG64 *p) { return InterlockedCompareExchange64(p, 0, 0); }   /* x86: a plain read of a LONG64 can tear */
static void klva_hsite(LONG at, SIZE_T size);

static void klva_hcount(void **ra, HANDLE heap, LONG64 add, LONG64 sub)
{   /* ra = the wrapper's return-address slot. A call from a C runtime (malloc, new) is billed to the first return address above it
       that lies in another followed module: a GUESS from a stack scan (no frame walk; a stale value can be picked) */
    int m = klva_hmod(ra[0]);
    if (m && klva_hm[m].crt) {
        DWORD_PTR top = __readfsdword(4); int j, k;   /* TIB StackBase: never read past it */
        for (j = 1; j < 48 && (DWORD_PTR)(ra + j + 1) <= top; j++) {
            int kl2 = (DWORD_PTR)ra[j] >= 0x401000 && (DWORD_PTR)ra[j] < 0xa00000;   /* kl2.exe code (base 0x400000, no ASLR) */
            k = klva_hmod(ra[j]);
            if ((!k && !kl2) || (k && klva_hm[k].crt)) continue;
            if (k) m = k;
            if (kl2 && add && heap == klva_pheap) klva_hsite((LONG)(DWORD_PTR)ra[j], (SIZE_T)add);   /* kl2 via the CRT: into the caller table too */
            break;
        }
    }
    InterlockedIncrement(&klva_hm[m].calls);
    if (heap == klva_pheap) { if (add) InterlockedExchangeAdd64(&klva_hm[m].pa, add); if (sub) InterlockedExchangeAdd64(&klva_hm[m].pf, sub); }
    else if (add) InterlockedExchangeAdd64(&klva_hm[m].oa, add);
}

static LPVOID WINAPI klva_halloc(HANDLE heap, DWORD flags, SIZE_T size)
{
    LPVOID p = klva_real_halloc(heap, flags, size); DWORD err = GetLastError();
    if (p) klva_hcount((void **)_AddressOfReturnAddress(), heap, (LONG64)size, 0);
    SetLastError(err);
    return p;
}

static BOOL WINAPI klva_hfree(HANDLE heap, DWORD flags, LPVOID p)
{
    SIZE_T n = (p && heap == klva_pheap) ? klva_real_hsize(heap, 0, p) : 0; BOOL ok = klva_real_hfree(heap, flags, p); DWORD err = GetLastError();
    if (ok && p) klva_hcount((void **)_AddressOfReturnAddress(), heap, 0, n == (SIZE_T)-1 ? 0 : (LONG64)n);
    SetLastError(err);
    return ok;
}

static LPVOID WINAPI klva_hrealloc(HANDLE heap, DWORD flags, LPVOID p, SIZE_T size)
{
    SIZE_T n = (p && heap == klva_pheap) ? klva_real_hsize(heap, 0, p) : 0; LPVOID q = klva_real_hrealloc(heap, flags, p, size); DWORD err = GetLastError();
    if (q) klva_hcount((void **)_AddressOfReturnAddress(), heap, (LONG64)size, n == (SIZE_T)-1 ? 0 : (LONG64)n);
    SetLastError(err);
    return q;
}

/* LocalAlloc / GlobalAlloc land on the process heap too, past every HeapAlloc slot (kl-merge-27, 10-25): counted as P traffic */
static HLOCAL (WINAPI *klva_real_lalloc)(UINT, SIZE_T); static HLOCAL (WINAPI *klva_real_lfree)(HLOCAL); static HLOCAL (WINAPI *klva_real_lrealloc)(HLOCAL, SIZE_T, UINT);
static SIZE_T (WINAPI *klva_real_lsize)(HLOCAL);
static HGLOBAL (WINAPI *klva_real_galloc)(UINT, SIZE_T); static HGLOBAL (WINAPI *klva_real_gfree)(HGLOBAL); static HGLOBAL (WINAPI *klva_real_grealloc)(HGLOBAL, SIZE_T, UINT);
static SIZE_T (WINAPI *klva_real_gsize)(HGLOBAL);

static HLOCAL WINAPI klva_lalloc(UINT flags, SIZE_T size)
{ HLOCAL h = klva_real_lalloc(flags, size); DWORD err = GetLastError(); if (h) klva_hcount((void **)_AddressOfReturnAddress(), klva_pheap, (LONG64)size, 0); SetLastError(err); return h; }
static HLOCAL WINAPI klva_lfree(HLOCAL h)
{ SIZE_T n = h ? klva_real_lsize(h) : 0; HLOCAL r = klva_real_lfree(h); DWORD err = GetLastError(); if (h && !r) klva_hcount((void **)_AddressOfReturnAddress(), klva_pheap, 0, (LONG64)n); SetLastError(err); return r; }
static HLOCAL WINAPI klva_lrealloc(HLOCAL h, SIZE_T size, UINT flags)
{ SIZE_T n = h ? klva_real_lsize(h) : 0; HLOCAL r = klva_real_lrealloc(h, size, flags); DWORD err = GetLastError(); if (r && !(flags & LMEM_MODIFY)) klva_hcount((void **)_AddressOfReturnAddress(), klva_pheap, (LONG64)size, (LONG64)n); SetLastError(err); return r; }
static HGLOBAL WINAPI klva_galloc(UINT flags, SIZE_T size)
{ HGLOBAL h = klva_real_galloc(flags, size); DWORD err = GetLastError(); if (h) klva_hcount((void **)_AddressOfReturnAddress(), klva_pheap, (LONG64)size, 0); SetLastError(err); return h; }
static HGLOBAL WINAPI klva_gfree(HGLOBAL h)
{ SIZE_T n = h ? klva_real_gsize(h) : 0; HGLOBAL r = klva_real_gfree(h); DWORD err = GetLastError(); if (h && !r) klva_hcount((void **)_AddressOfReturnAddress(), klva_pheap, 0, (LONG64)n); SetLastError(err); return r; }
static HGLOBAL WINAPI klva_grealloc(HGLOBAL h, SIZE_T size, UINT flags)
{ SIZE_T n = h ? klva_real_gsize(h) : 0; HGLOBAL r = klva_real_grealloc(h, size, flags); DWORD err = GetLastError(); if (r && !(flags & GMEM_MODIFY)) klva_hcount((void **)_AddressOfReturnAddress(), klva_pheap, (LONG64)size, (LONG64)n); SetLastError(err); return r; }

static int klva_patch(BYTE *base)
{   /* the slots of one module's IAT that hold a target: -> how many were changed. A heap function's slot holds kernel32's export, kernelbase's,
       or (kernel32's are forwarders) ntdll's Rtl* function: all three are matched */
#define KLVA_FN 13
    static const char *fn[KLVA_FN] = { "VirtualAlloc", "VirtualFree", "VirtualAllocEx", "HeapCreate", "HeapAlloc", "HeapFree", "HeapReAlloc",
                                       "LocalAlloc", "LocalFree", "LocalReAlloc", "GlobalAlloc", "GlobalFree", "GlobalReAlloc" };
    static const char *rtl[KLVA_FN] = { 0, 0, 0, 0, "RtlAllocateHeap", "RtlFreeHeap", "RtlReAllocateHeap" };
    void *mine[KLVA_FN] = { (void *)klva_alloc, (void *)klva_free, (void *)klva_allocex, (void *)klva_heapcreate, (void *)klva_halloc, (void *)klva_hfree, (void *)klva_hrealloc,
                            (void *)klva_lalloc, (void *)klva_lfree, (void *)klva_lrealloc, (void *)klva_galloc, (void *)klva_gfree, (void *)klva_grealloc };
    void *old[3 * KLVA_FN]; HMODULE k32 = GetModuleHandleA("kernel32.dll"), kb = GetModuleHandleA("kernelbase.dll"), nt0 = GetModuleHandleA("ntdll.dll");
    IMAGE_NT_HEADERS *nt; IMAGE_DATA_DIRECTORY *dd; void **slot, **end; int i, done = 0;
    if (((IMAGE_DOS_HEADER *)base)->e_magic != IMAGE_DOS_SIGNATURE) return 0;
    nt = (IMAGE_NT_HEADERS *)(base + ((IMAGE_DOS_HEADER *)base)->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE) return 0;
    if (klva_nhm < KLVA_MODS) {   /* the module's range, for the heap tally: written now, made visible (klva_nhm raised) only once a slot is wrapped */
        LONG r = klva_nhm; char path[MAX_PATH], *s;
        klva_hm[r].base = (DWORD_PTR)base; klva_hm[r].end = (DWORD_PTR)base + nt->OptionalHeader.SizeOfImage;
        if (GetModuleFileNameA((HMODULE)base, path, sizeof path)) { s = strrchr(path, '\\'); snprintf(klva_hm[r].name, sizeof klva_hm[r].name, "%s", s ? s + 1 : path); }
        else snprintf(klva_hm[r].name, sizeof klva_hm[r].name, "%p", (void *)base);
        klva_hm[r].crt = !_strnicmp(klva_hm[r].name, "msvcr", 5) || !_strnicmp(klva_hm[r].name, "msvcp", 5) || !_strnicmp(klva_hm[r].name, "ucrtbase", 8);
    }
    dd = &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IAT];
    if (!dd->VirtualAddress || !dd->Size) return 0;
    for (i = 0; i < KLVA_FN; i++) {
        old[3 * i] = k32 ? (void *)GetProcAddress(k32, fn[i]) : 0; old[3 * i + 1] = kb ? (void *)GetProcAddress(kb, fn[i]) : 0;
        old[3 * i + 2] = rtl[i] && nt0 ? (void *)GetProcAddress(nt0, rtl[i]) : 0;
    }
    slot = (void **)(base + dd->VirtualAddress); end = (void **)(base + dd->VirtualAddress + dd->Size);
    for (; slot < end; slot++) {
        void *cur = *slot;
        if (!cur) continue;
        for (i = 0; i < 3 * KLVA_FN; i++) if (old[i] && cur == old[i]) break;
        if (i == 3 * KLVA_FN) continue;
        if (klh_poke(slot, &cur, sizeof cur, &mine[i / 3], sizeof mine[i / 3], fn[i / 3])) done++;
    }
    if (done && klva_nhm < KLVA_MODS) InterlockedExchange(&klva_nhm, klva_nhm + 1);   /* only this thread appends */
    return done;
}

static void klva_hheaps(void)
{   /* every 10 s: the 10 modules with the most process-heap traffic since the last tick */
    int ord[10], no = 0, i, k, n; LONG cnt = klva_nhm; static LONG64 d[KLVA_MODS], f[KLVA_MODS], o[KLVA_MODS]; static LONG c[KLVA_MODS]; char line[1600]; double ta = 0, tf = 0;   /* static: tick thread only, off the game stack */
    for (i = 0; i < cnt; i++) {
        LONG64 a = klva_rd64(&klva_hm[i].pa), b = klva_rd64(&klva_hm[i].pf), e = klva_rd64(&klva_hm[i].oa); LONG m = klva_hm[i].calls;
        d[i] = a - klva_hm[i].lpa; f[i] = b - klva_hm[i].lpf; o[i] = e - klva_hm[i].loa; c[i] = m - klva_hm[i].lcalls;
        klva_hm[i].lpa = a; klva_hm[i].lpf = b; klva_hm[i].loa = e; klva_hm[i].lcalls = m; ta += (double)d[i]; tf += (double)f[i];
        if (!c[i]) continue;
        if (no == 10 && d[ord[9]] + f[ord[9]] >= d[i] + f[i]) continue;
        if (no < 10) no++;
        for (k = no - 1; k > 0 && d[ord[k - 1]] + f[ord[k - 1]] < d[i] + f[i]; k--) ord[k] = ord[k - 1];
        ord[k] = i;
    }
    n = _snprintf(line, sizeof line, "va: other modules on the process heap in the last 10 s: +%.1f / -%.1f MB; by module P alloc/P free/other heaps MB, calls:", ta / 1048576.0, tf / 1048576.0);
    for (i = 0; i < no && n > 0 && n < (int)sizeof line; i++) {
        int m = ord[i];
        k = _snprintf(line + n, sizeof line - n, " %s %.1f/%.1f/%.1f %ld;", m ? klva_hm[m].name : "(outside)", d[m] / 1048576.0, f[m] / 1048576.0, o[m] / 1048576.0, c[m]);
        if (k < 0) break;
        n += k;
    }
    line[sizeof line - 1] = 0; klog("%s", line);
}

static DWORD WINAPI klva_watch(LPVOID unused)
{
    HMODULE k = GetModuleHandleA("kernel32.dll"), mods[1024], skip[4]; klxp_enum_fn en; HMODULE seen[1024]; int nseen = 0; (void)unused;
    en = (klxp_enum_fn)GetProcAddress(k, "K32EnumProcessModules");
    if (!en) { klog("va: K32EnumProcessModules not found: VaLog does nothing"); return 0; }
    skip[0] = GetModuleHandleA("ntdll.dll"); skip[1] = k; skip[2] = GetModuleHandleA("kernelbase.dll"); skip[3] = 0; GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCSTR)klva_watch, &skip[3]);
    for (;;) {
        DWORD need = 0, cnt, i; int j;
        if (en(GetCurrentProcess(), mods, sizeof mods, &need)) {
            cnt = need / sizeof(HMODULE); if (cnt > 1024) cnt = 1024;
            for (i = 0; i < cnt; i++) {
                int n; char mod[64]; DWORD off;
                for (j = 0; j < nseen && seen[j] != mods[i]; j++) ;
                if (j < nseen) continue;
                if (nseen < 1024) seen[nseen++] = mods[i];
                for (j = 0; j < 4 && skip[j] != mods[i]; j++) ;
                if (j < 4) continue;
                __try { n = klva_patch((BYTE *)mods[i]); }   /* a module unloaded since the enumeration: its reads fault */
                __except (EXCEPTION_EXECUTE_HANDLER) { n = 0; klog("va: module %p went away while it was patched", (void *)mods[i]); }
                if (n) { klh_module((DWORD_PTR)mods[i], mod, sizeof mod, &off); klog("va: %s at %p: %d import slot(s) wrapped", mod, (void *)mods[i], n); }
            }
        }
        Sleep(2000);
    }
    return 0;
}

#define KLVA_SITES 1024
static struct { volatile LONG at; volatile LONG cnt; volatile LONG64 bytes; LONG64 last; LONG lastcnt; } klva_site[KLVA_SITES];
static volatile LONG klva_site_full, klva_small, klva_small_b;
static int klva_census_on = 1;

static void klva_hnote(void **ra, HANDLE heap, SIZE_T size)
{   /* from klm_HeapAlloc (kl2's import, every size): no lock, open addressing on the caller; a full table only counts */
    LONG at = (LONG)(DWORD_PTR)ra[0]; (void)heap;
    if (at == 0x7bb33c) at = (LONG)(DWORD_PTR)ra[7];
    if (at == 0x4aa067) at = (LONG)(DWORD_PTR)ra[17];
    if (at == 0x4a3009) at = (LONG)(DWORD_PTR)ra[22];   /* 0x4a2fd0: push esi/edi, 2 arguments to 0x4aa010 */
    if (at == 0x89e85c) at = (LONG)(DWORD_PTR)ra[25];   /* operator new 0x89e850: 2 arguments to 0x4a2fd0, nothing saved */
    if (size <= 0xa0) { InterlockedIncrement(&klva_small); InterlockedExchangeAdd(&klva_small_b, (LONG)size); }   /* n <= 0x80 (size = ((n+0x1f)&~0xf)+0x10) */
    klva_hsite(at, size);
}

static void klva_hsite(LONG at, SIZE_T size)
{   /* one caller's tally; a full table only counts */
    LONG h, i, n;
    if (!at) at = 1;   /* 0 marks an empty slot */
    h = (LONG)(((DWORD)at * 2654435761u) >> 22);
    for (n = 0; n < 32; n++) {
        LONG cur;
        i = (h + n) & (KLVA_SITES - 1);
        cur = klva_site[i].at;
        if (!cur && (cur = InterlockedCompareExchange(&klva_site[i].at, at, 0)) == 0) cur = at;   /* the empty slot is ours */
        if (cur != at) continue;
        InterlockedIncrement(&klva_site[i].cnt); InterlockedExchangeAdd64(&klva_site[i].bytes, (LONG64)size);
        return;
    }
    InterlockedIncrement(&klva_site_full);
}

static void klva_heaps(void)
{   /* the heaps by reserved size; a census slower than 500 ms is not repeated */
    typedef struct { DWORD cb; SIZE_T cbAllocated, cbCommitted, cbReserved, cbMaxReserve; } klva_hs;
    static BOOL (WINAPI *sum)(HANDLE, DWORD, klva_hs *); static HANDLE crt; static int once;
    HANDLE hs[64], p = GetProcessHeap(); klva_hs s[64]; char line[1600]; int i, k, n, cnt, ord[64]; DWORD t0 = GetTickCount(), dt; double com = 0, res = 0;
    if (!once) {
        HMODULE m = GetModuleHandleA("msvcr90.dll"); intptr_t (__cdecl *gh)(void) = m ? (void *)GetProcAddress(m, "_get_heap_handle") : 0;
        once = 1; sum = (void *)GetProcAddress(GetModuleHandleA("kernel32.dll"), "HeapSummary"); crt = gh ? (HANDLE)gh() : 0;
        if (!sum) klog("va: HeapSummary not exported: no heap census");
    }
    if (!sum || !klva_census_on) return;
    cnt = (int)GetProcessHeaps(64, hs); if (cnt > 64) cnt = 64;
    for (i = 0; i < cnt; i++) { memset(&s[i], 0, sizeof s[i]); s[i].cb = sizeof s[i]; if (!sum(hs[i], 0, &s[i])) s[i].cbReserved = s[i].cbCommitted = 0; ord[i] = i; com += s[i].cbCommitted; res += s[i].cbReserved; }
    dt = GetTickCount() - t0;
    for (i = 1; i < cnt; i++) { int v = ord[i]; for (k = i; k > 0 && s[ord[k - 1]].cbReserved < s[v].cbReserved; k--) ord[k] = ord[k - 1]; ord[k] = v; }
    n = _snprintf(line, sizeof line, "va: %d heaps, %.0f MB committed / %.0f MB reserved (census %lu ms); allocated/committed/reserved MB:", cnt, com / 1048576.0, res / 1048576.0, dt);
    for (i = 0; i < cnt && i < 10 && n > 0 && n < (int)sizeof line; i++) {
        int h = ord[i];
        k = _snprintf(line + n, sizeof line - n, " %p%s %.1f/%.1f/%.1f;", hs[h], hs[h] == p ? " P" : hs[h] == crt ? " C" : "", s[h].cbAllocated / 1048576.0, s[h].cbCommitted / 1048576.0, s[h].cbReserved / 1048576.0);
        if (k < 0) break;
        n += k;
    }
    line[sizeof line - 1] = 0; klog("%s", line);
    if (dt > 500) { klva_census_on = 0; klog("va: the heap census took %lu ms: not repeated", dt); }
}

static void klva_callers(void)
{   /* kl2's HeapAlloc bytes since the last tick, the 12 biggest callers */
    int ord[12], no = 0, i, k, n; static LONG64 d[KLVA_SITES]; static LONG dc[KLVA_SITES]; char line[1600]; double tot = 0;   /* static: tick thread only */
    for (i = 0; i < KLVA_SITES; i++) {
        LONG64 b = klva_rd64(&klva_site[i].bytes); LONG c = klva_site[i].cnt;
        d[i] = b - klva_site[i].last; dc[i] = c - klva_site[i].lastcnt; klva_site[i].last = b; klva_site[i].lastcnt = c; tot += (double)d[i];
        if (!klva_site[i].at || d[i] <= 0) continue;
        if (no == 12 && d[ord[11]] >= d[i]) continue;
        if (no < 12) no++;
        for (k = no - 1; k > 0 && d[ord[k - 1]] < d[i]; k--) ord[k] = ord[k - 1];
        ord[k] = i;
    }
    {   LONG sc = InterlockedExchange(&klva_small, 0), sb = InterlockedExchange(&klva_small_b, 0);   /* reset each tick: no overflow */
        n = _snprintf(line, sizeof line, "va: kl2 HeapAlloc in the last 10 s: %.1f MB (%ld callers not tracked); n <= 0x80: %ld calls, %.1f MB; small-block pool gate [0xddb89c] = %d; by caller MB/calls:",
                      tot / 1048576.0, klva_site_full, sc, sb / 1048576.0, GetModuleHandleA("kl2.exe") ? (int)*(volatile BYTE *)0xddb89c : -1);
    }
    for (i = 0; i < no && n > 0 && n < (int)sizeof line; i++) {
        char mod[64]; DWORD off; klh_module((DWORD_PTR)klva_site[ord[i]].at, mod, sizeof mod, &off);
        k = _snprintf(line + n, sizeof line - n, " %s+%lx %.1f/%ld;", mod, off, d[ord[i]] / 1048576.0, dc[ord[i]]);
        if (k < 0) break;
        n += k;
    }
    line[sizeof line - 1] = 0; klog("%s", line);
}

static void klva_tick(void)
{   /* every 10 s: the modules by what they still hold */
    static DWORD last; DWORD now = GetTickCount(); char line[1600]; int i, k, n, ord[KLVA_MODS], cnt;
    if (!klva_on || now - last < 10000) return;
    last = now;
    for (i = 0; i < klva_nmod; i++) if (!klva_mod[i].name[0]) {   /* a row is never removed: its base stays */
        char path[MAX_PATH], *s;
        if (GetModuleFileNameA((HMODULE)klva_mod[i].base, path, sizeof path)) { s = strrchr(path, '\\'); snprintf(klva_mod[i].name, sizeof klva_mod[i].name, "%s", s ? s + 1 : path); }
        else snprintf(klva_mod[i].name, sizeof klva_mod[i].name, "%p", (void *)klva_mod[i].base);
    }
    EnterCriticalSection(&klva_cs);
    cnt = klva_nmod;
    for (i = 0; i < cnt; i++) ord[i] = i;
    for (i = 1; i < cnt; i++) { int v = ord[i]; for (k = i; k > 0 && klva_mod[ord[k - 1]].live < klva_mod[v].live; k--) ord[k] = ord[k - 1]; ord[k] = v; }
    n = _snprintf(line, sizeof line, "va: every 10 s, held now by caller (reserved MB live / reserved total / committed total, calls, heaps; %d tracked, %ld untracked):", klva_nlive, klva_live_full);
    for (i = 0; i < cnt && i < 16 && n > 0 && n < (int)sizeof line; i++) {
        int m = ord[i];
        k = _snprintf(line + n, sizeof line - n, " %s %.1f/%.1f/%.1f %ld h%ld;", klva_mod[m].name[0] ? klva_mod[m].name : "?", klva_mod[m].live / 1048576.0,
                      klva_mod[m].res / 1048576.0, klva_mod[m].com / 1048576.0, klva_mod[m].calls, klva_mod[m].heaps);
        if (k < 0) break;
        n += k;
    }
    LeaveCriticalSection(&klva_cs);
    line[sizeof line - 1] = 0;
    klog("%s", line);
    klva_heaps();
    klva_callers();
    klva_hheaps();
}

static void klva_init(void)
{
    HMODULE kb = GetModuleHandleA("kernelbase.dll"), k32 = GetModuleHandleA("kernel32.dll");
    klva_on = GetPrivateProfileIntA("Memory", "VaLog", 0, klh_ini) != 0;
    if (!klva_on) return;
    klva_real_alloc = (void *)GetProcAddress(kb ? kb : k32, "VirtualAlloc");
    klva_real_free = (void *)GetProcAddress(kb ? kb : k32, "VirtualFree");
    klva_real_allocex = (void *)GetProcAddress(kb ? kb : k32, "VirtualAllocEx");
    klva_real_heapcreate = (void *)GetProcAddress(kb ? kb : k32, "HeapCreate");
    if (!klva_real_heapcreate) klva_real_heapcreate = (void *)GetProcAddress(k32, "HeapCreate");
    if (!klva_real_alloc || !klva_real_free || !klva_real_allocex || !klva_real_heapcreate) { klva_on = 0; klog("va: a target is not exported: VaLog off"); return; }
    klva_real_halloc = (void *)GetProcAddress(k32, "HeapAlloc"); klva_real_hfree = (void *)GetProcAddress(k32, "HeapFree");
    klva_real_hrealloc = (void *)GetProcAddress(k32, "HeapReAlloc"); klva_real_hsize = (void *)GetProcAddress(k32, "HeapSize");
    if (!klva_real_halloc || !klva_real_hfree || !klva_real_hrealloc || !klva_real_hsize) { klva_on = 0; klog("va: a heap function is not exported: VaLog off"); return; }
    klva_real_lalloc = (void *)GetProcAddress(k32, "LocalAlloc"); klva_real_lfree = (void *)GetProcAddress(k32, "LocalFree");
    klva_real_lrealloc = (void *)GetProcAddress(k32, "LocalReAlloc"); klva_real_lsize = (void *)GetProcAddress(k32, "LocalSize");
    klva_real_galloc = (void *)GetProcAddress(k32, "GlobalAlloc"); klva_real_gfree = (void *)GetProcAddress(k32, "GlobalFree");
    klva_real_grealloc = (void *)GetProcAddress(k32, "GlobalReAlloc"); klva_real_gsize = (void *)GetProcAddress(k32, "GlobalSize");
    if (!klva_real_lalloc || !klva_real_lfree || !klva_real_lrealloc || !klva_real_lsize || !klva_real_galloc || !klva_real_gfree || !klva_real_grealloc || !klva_real_gsize)
        { klva_on = 0; klog("va: a Local/Global function is not exported: VaLog off"); return; }
    klva_pheap = GetProcessHeap(); lstrcpyA(klva_hm[0].name, "(outside)");
    InitializeCriticalSection(&klva_cs);
    CloseHandle(CreateThread(0, 64 << 10, klva_watch, 0, STACK_SIZE_PARAM_IS_A_RESERVATION, 0));
    klog("va: VaLog on: VirtualAlloc / VirtualFree / VirtualAllocEx / HeapCreate of every other module are followed (calls of 512 KB+ one line each, the first 400)");
}
