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
 * [Memory] VaLog=1   (default 0; TEST build only: nothing of this is in a SHIP build)
 */
#define KLVA_MODS 96
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

static int klva_patch(BYTE *base)
{   /* the slots of one module's IAT that hold a target: -> how many were changed */
    static const char *fn[4] = { "VirtualAlloc", "VirtualFree", "VirtualAllocEx", "HeapCreate" };
    void *mine[4] = { (void *)klva_alloc, (void *)klva_free, (void *)klva_allocex, (void *)klva_heapcreate };
    void *old[8]; HMODULE k32 = GetModuleHandleA("kernel32.dll"), kb = GetModuleHandleA("kernelbase.dll");
    IMAGE_NT_HEADERS *nt; IMAGE_DATA_DIRECTORY *dd; void **slot, **end; int i, done = 0;
    if (((IMAGE_DOS_HEADER *)base)->e_magic != IMAGE_DOS_SIGNATURE) return 0;
    nt = (IMAGE_NT_HEADERS *)(base + ((IMAGE_DOS_HEADER *)base)->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE) return 0;
    dd = &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IAT];
    if (!dd->VirtualAddress || !dd->Size) return 0;
    for (i = 0; i < 4; i++) { old[2 * i] = k32 ? (void *)GetProcAddress(k32, fn[i]) : 0; old[2 * i + 1] = kb ? (void *)GetProcAddress(kb, fn[i]) : 0; }
    slot = (void **)(base + dd->VirtualAddress); end = (void **)(base + dd->VirtualAddress + dd->Size);
    for (; slot < end; slot++) {
        void *cur = *slot;
        if (!cur) continue;
        for (i = 0; i < 8; i++) if (old[i] && cur == old[i]) break;
        if (i == 8) continue;
        if (klh_poke(slot, &cur, sizeof cur, &mine[i / 2], sizeof mine[i / 2], fn[i / 2])) done++;
    }
    return done;
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
                n = klva_patch((BYTE *)mods[i]);
                if (n) { klh_module((DWORD_PTR)mods[i], mod, sizeof mod, &off); klog("va: %s at %p: %d import slot(s) wrapped", mod, (void *)mods[i], n); }
            }
        }
        Sleep(2000);
    }
    return 0;
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
    InitializeCriticalSection(&klva_cs);
    CloseHandle(CreateThread(0, 64 << 10, klva_watch, 0, STACK_SIZE_PARAM_IS_A_RESERVATION, 0));
    klog("va: VaLog on: VirtualAlloc / VirtualFree / VirtualAllocEx / HeapCreate of every other module are followed (calls of 512 KB+ one line each, the first 400)");
}
