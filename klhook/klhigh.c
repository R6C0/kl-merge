/*
 * klhigh.c - the HIGH HALF: with the 4 GB flag on kl2.exe, the graphics driver's memory moves above 2 GB and the game's
 * own memory stays below it. Part of KLHook (included by klhook.c after klmem.c, SHIP and TEST alike). NOT YET RUN IN
 * THE GAME (written 2026-10-25, scheduled check-in, compile-checked with MinGW against a stub of klhook's helpers only).
 *
 * WHY. DM05A dies of ADDRESS SPACE, not of memory (K48B..K48H, re/open_work_log.md 2026-10-25): a 32-bit process has
 * 2048 MB of addresses and round 1 fills them (free 16 MB, largest piece 0.1 MB), then the D3D driver (nvd3dum.dll) asks
 * for a block outside every wrapped call, gets none and crashes (K48C, nvd3dum+0x170a69). The obvious cure, the
 * large-address-aware flag (4 GB for a 32-bit process on 64-bit Windows), was tried on 2026-10-25 01:40 and crashed
 * after 85 s: the engine marks a direct pointer in a chunk reference by its TOP BIT (219 `jns ; and eax,0x7fffffff`
 * resolver sites, debug/notes/2026-10-24-scheduled-triage-laa.md), so the first GAME heap block above 2 GB was read as a
 * tagged pointer to the address 2 GB lower. The flag is poison for the game's own memory - and nothing else: the driver,
 * the overlays and ReShade never hand the game a pointer it stores in a chunk reference (GUESS, the reason for the
 * measure mode below and for a live test). So: give the upper 2 GB to THEM, and keep the game where it is.
 *
 * HOW (no byte of kl2.exe changes; no code of any DLL changes; no inline hook):
 *  1. At DLL load, when kl2.exe runs with the flag, the whole upper half (0x80000000 .. 0xfffeffff) is RESERVED by this
 *     file in chunks (64 MB top-down, then smaller to fill the holes; nothing is committed). From then on the process
 *     looks to everyone exactly as it did without the flag: no allocation of the game, the heap, a thread stack or a
 *     DLL can land above 2 GB, because nothing is free there. That is what makes the flag safe for the game.
 *  2. The IMPORT SLOTS of the listed foreign modules (nvd3dum.dll ...; their own IATs, found by function name, so an
 *     api-ms-win-core-memory-* import counts too) for VirtualAlloc / VirtualAllocEx / VirtualFree / VirtualFreeEx point
 *     at the wrappers below. A module that loads later (the driver loads with the D3D device) is caught by
 *     LdrRegisterDllNotification (an unload forgets the module, so a reload is wrapped again). A new block (address 0
 *     with MEM_RESERVE, or with MEM_COMMIT alone - that shortcut reserves too; no write-watch / large-page / physical
 *     flag) asked by one of them is carved out of the chunks (first fit, 64 KB granularity as VirtualAlloc's own) and
 *     committed there if asked; its MEM_RELEASE decommits the carved block and frees the bits; MEM_COMMIT / a sized
 *     MEM_DECOMMIT at an address inside the chunks pass straight through (the pages are reserved: Windows accepts them);
 *     MEM_DECOMMIT with size 0 ("the whole block") is answered for the carved block, never for the chunk. Everything
 *     else (an explicit address, the odd flags, the chunks being full) passes through to the real call, i.e. into the
 *     low half as today, and is counted as 'passed' / 'spilled'. After the takeover a walk of the high half must find
 *     NOTHING free; a WARNING line names any piece that is (the game could land there once the low half is full).
 *  Review 2026-10-25 (second scheduled check-in, static): MEM_COMMIT-alone blocks were passed through uncounted (the
 *     measure line would have missed every allocator using the shortcut, High=2 would have left them low), a size-0
 *     MEM_DECOMMIT of a block at a chunk's start would have decommitted the whole chunk under its neighbours, a module
 *     reloaded at its old base was never re-wrapped, and a chunk-limit shortfall was silent. All four fixed here.
 *  3. MEASURE first. [Memory] High=1 wraps and counts only: every 10 s a line says how many MB each listed module holds
 *     through VirtualAlloc. That needs no flag and changes nothing in placement; it says what High=2 would buy. The
 *     driver's small objects live in ITS heaps (HeapAlloc; grown by ntdll, not wrapped here) and stay low either way;
 *     the big ones (texture staging, shader caches, command buffers, ReShade's effect textures) are VirtualAlloc - GUESS
 *     until measured.
 *
 * RISKS (why this is off by default and why High=2 must be a live A/B, not an install):
 *  - A pointer into high memory that the game STORES in a chunk reference would crash as the LAA test did. Not expected
 *    from the listed modules (a driver hands the game Lock() pointers to write through, not to keep); d3d9.dll itself
 *    is NOT in the default placement list for that reason (its managed-pool system copies are big, which is why it is
 *    in the count list: measure first).
 *  - Signed compares on pointers in the game's own code (`cmp ..; jl`) would see a high pointer as negative. Same class
 *    as above; the measure run shows the game never receives one - or the A/B shows it.
 *  - VirtualQuery by a module on its own carved block answers with OUR chunk as the allocation base and a region that
 *    may span its neighbours; a module that sizes its block that way (rare) would be confused. MEM_RELEASE from a
 *    module other than the one that reserved the block (d3d9 freeing nvd3dum's block) goes to the real VirtualFree,
 *    fails, and leaks that block in the high half: a leak above 2 GB costs the game nothing.
 *  - The flag itself has to be set in kl2.exe's header on disk (the owner's one-byte patch, 0x103 -> 0x123 on
 *    2026-10-25; backup kl2.exe.before-1025laa). This file only READS the flag; with the flag off High=2 falls back to
 *    High=1 and says so.
 *  - Steam's integrity hashes (klranges.h) do not cover the PE header: the LAA run went 85 s and died of the tag, not
 *    of a hash. Not re-verified here.
 *
 * KLHook.ini
 *   [Memory]
 *   High=0            0 = off (nothing wrapped, nothing reserved); 1 = MEASURE (wrap + count, placement as before, no flag
 *                     needed); 2 = PLACE (needs the 4 GB flag in kl2.exe; falls back to 1 without it)
 *   HighModules=nvd3dum.dll,nvwgf2um.dll,ReShade32.dll,gameoverlayrenderer.dll
 *                     the modules whose reservations are counted AND, with High=2, placed in the high half
 *   HighCount=d3d9.dll,dxgi.dll,d3d10.dll
 *                     counted only, never placed (candidates for the list above, decided by the measure run)
 *   HighLog=1         the 10 s line and the wrap lines; 0 = only the start and the fall-back lines
 *
 * Log lines: 'high: ...'. The 10 s line (High on): per module reservations asked / held now, and for High=2 the
 * high half's chunks, MB carved, spilled (asked while the chunks were full) and passed (explicit address or odd flags).
 */
#ifndef KLHIGH_C
#define KLHIGH_C

#ifdef __GNUC__
#define _ReturnAddress() __builtin_return_address(0)
#endif

#define KLVH_MODS   24
#define KLVH_GRAN   0x10000u                                    /* VirtualAlloc's own allocation granularity */
#define KLVH_BASE   0x80000000u                                 /* the high half */
#define KLVH_PAGES  32768                                       /* 2 GB / 64 KB: one bit each in the maps below */
#define KLVH_CHUNKS 96                                          /* 32 x 64 MB fill an empty high half; the rest is for holes around what was already there (the takeover WARNS if it runs out) */

typedef struct {
    char name[48];                                              /* leaf name, as [Memory] HighModules spells it */
    HMODULE base; DWORD size;                                   /* set when the module is seen */
    int place;                                                  /* 1 = HighModules (placed with High=2), 0 = HighCount only */
    int slots;                                                  /* import slots pointed at the wrappers */
    LONG asked_n, held_n;                                       /* reservations asked / held now (through the wrappers) */
    SIZE_T asked_mb_x16, held;                                  /* asked in 1/16 MB (a sum that may pass 4 GB), held now in bytes */
    SIZE_T high;                                                /* bytes of it carved out of the high half (High=2) */
} klvh_mod;

static int klvh_mode, klvh_log = 1, klvh_placing;              /* klvh_placing: High=2 and the chunks are there */
static klvh_mod klvh_mods[KLVH_MODS]; static int klvh_nmods;
static CRITICAL_SECTION klvh_cs;
static LPVOID (WINAPI *klvh_real_VirtualAlloc)(LPVOID, SIZE_T, DWORD, DWORD);
static LPVOID (WINAPI *klvh_real_VirtualAllocEx)(HANDLE, LPVOID, SIZE_T, DWORD, DWORD);
static BOOL   (WINAPI *klvh_real_VirtualFree)(LPVOID, SIZE_T, DWORD);
static BOOL   (WINAPI *klvh_real_VirtualFreeEx)(HANDLE, LPVOID, SIZE_T, DWORD);
/* the high half: chunks reserved by this file, and three bit maps over its 64 KB pages */
static struct { BYTE *base; SIZE_T size; } klvh_chunk[KLVH_CHUNKS]; static int klvh_nchunk;
static DWORD klvh_in[KLVH_PAGES / 32], klvh_used[KLVH_PAGES / 32], klvh_start[KLVH_PAGES / 32];
static SIZE_T klvh_high_total, klvh_carved;                     /* bytes reserved by us; bytes carved out now */
static LONG klvh_spilled, klvh_passed, klvh_released, klvh_bad_release;
static SIZE_T klvh_spilled_bytes;

/* ---------------------------------------------------------------- bit maps */
static int klvh_bit(const DWORD *m, DWORD i) { return (m[i >> 5] >> (i & 31)) & 1; }
static void klvh_set(DWORD *m, DWORD i, int v) { if (v) m[i >> 5] |= 1u << (i & 31); else m[i >> 5] &= ~(1u << (i & 31)); }
static int klvh_in_high(const void *p) { return (DWORD_PTR)p >= KLVH_BASE && klvh_nchunk && klvh_bit(klvh_in, (DWORD)(((DWORD_PTR)p - KLVH_BASE) >> 16)); }

/* first fit of n pages inside ONE chunk (a commit may not span two reservations) -> page index or -1; marks them used */
static long klvh_carve_pages(DWORD n)
{
    int c; DWORD i, run, first;
    for (c = 0; c < klvh_nchunk; c++) {
        DWORD lo = (DWORD)(((DWORD_PTR)klvh_chunk[c].base - KLVH_BASE) >> 16), hi = lo + (DWORD)(klvh_chunk[c].size >> 16);
        for (i = lo, run = 0, first = lo; i < hi; i++) {
            if (klvh_bit(klvh_used, i)) { run = 0; first = i + 1; continue; }
            if (++run == n) { for (i = first; i < first + n; i++) klvh_set(klvh_used, i, 1); klvh_set(klvh_start, first, 1); return (long)first; }
        }
    }
    return -1;
}

/* the carved block starting at page i -> its page count (0 = not a block start); nothing changes */
static DWORD klvh_block_pages(DWORD i)
{
    DWORD n = 0;
    if (i >= KLVH_PAGES || !klvh_bit(klvh_start, i) || !klvh_bit(klvh_used, i)) return 0;
    for (; i < KLVH_PAGES && klvh_bit(klvh_used, i) && (n == 0 || !klvh_bit(klvh_start, i)); i++, n++) ;
    return n;
}

/* the carved block starting at page i -> its page count (0 = not a block start) and clears it */
static DWORD klvh_release_pages(DWORD i)
{
    DWORD n = klvh_block_pages(i), k;
    if (!n) return 0;
    klvh_set(klvh_start, i, 0);
    for (k = 0; k < n; k++) klvh_set(klvh_used, i + k, 0);
    return n;
}

/* ---------------------------------------------------------------- who called */
static klvh_mod *klvh_who(const void *ret)
{   /* the module whose import slot brought the call here: by the return address (the slot is the module's own) */
    int i;
    for (i = 0; i < klvh_nmods; i++)
        if (klvh_mods[i].base && (BYTE *)ret >= (BYTE *)klvh_mods[i].base && (BYTE *)ret < (BYTE *)klvh_mods[i].base + klvh_mods[i].size) return &klvh_mods[i];
    return 0;
}

/* ---------------------------------------------------------------- the wrappers */
#ifndef MEM_RESET_UNDO
#define MEM_RESET_UNDO 0x1000000
#endif
#define KLVH_ODD (MEM_WRITE_WATCH | MEM_PHYSICAL | MEM_LARGE_PAGES | MEM_RESET | MEM_RESET_UNDO)

static LPVOID klvh_alloc(klvh_mod *m, LPVOID addr, SIZE_T size, DWORD type, DWORD prot)
{
    LPVOID p;
    if (!m) return klvh_real_VirtualAlloc(addr, size, type, prot);          /* not one of ours after all: as it was */
    if (addr && klvh_in_high(addr)) {
        /* inside a carved block: commit / re-commit / reset is Windows' business (the pages are reserved: it accepts
           them); a re-reserve of reserved pages is answered yes (Windows would say ERROR_INVALID_ADDRESS, but the
           reservation is ours, not the caller's, and the caller's view - "my pages are reserved" - is true) */
        DWORD t = type & ~(MEM_RESERVE | MEM_TOP_DOWN);
        if (t) return klvh_real_VirtualAlloc(addr, size, t, prot);
        return addr;
    }
    if (addr) { InterlockedIncrement(&klvh_passed); return klvh_real_VirtualAlloc(addr, size, type, prot); }   /* an explicit address in the low half */
    /* a NEW block: address 0 with MEM_RESERVE, or with MEM_COMMIT alone - VirtualAlloc(0, n, MEM_COMMIT, p) reserves
       AND commits (the documented shortcut, common in allocators), so it is a reservation too (review fix 2026-10-25:
       it was passed through uncounted, so the measure line missed every such block and High=2 left them low) */
    if (!(type & (MEM_RESERVE | MEM_COMMIT)) || !size) return klvh_real_VirtualAlloc(addr, size, type, prot);   /* nothing to place (Windows answers it) */
    EnterCriticalSection(&klvh_cs);
    m->asked_n++; m->asked_mb_x16 += (size + 0xffff) >> 16;
    if (type & KLVH_ODD) klvh_passed++;                         /* write watch, large pages ...: only the real call can give those (low half) */
    else if (klvh_placing && m->place) {
        DWORD n = (DWORD)((size + KLVH_GRAN - 1) / KLVH_GRAN); long i = klvh_carve_pages(n);
        if (i >= 0) {
            p = (BYTE *)(DWORD_PTR)KLVH_BASE + ((SIZE_T)i << 16);
            if ((type & MEM_COMMIT) && !klvh_real_VirtualAlloc(p, size, MEM_COMMIT, prot)) {
                DWORD err = GetLastError(); klvh_release_pages((DWORD)i); LeaveCriticalSection(&klvh_cs);
                klog("high: %s: commit of %.1f MB at %p in the high half FAILED (error %lu): passed to the low half", m->name, size / 1048576.0, p, err);
                InterlockedIncrement(&klvh_spilled);
                return klvh_real_VirtualAlloc(0, size, type, prot);
            }
            m->held_n++; m->held += (SIZE_T)n << 16; m->high += (SIZE_T)n << 16; klvh_carved += (SIZE_T)n << 16;
            LeaveCriticalSection(&klvh_cs);
            return p;
        }
        klvh_spilled++; klvh_spilled_bytes += size;             /* the chunks are full: the low half as before */
    }
    LeaveCriticalSection(&klvh_cs);
    p = klvh_real_VirtualAlloc(addr, size, type, prot);
    if (p) { EnterCriticalSection(&klvh_cs); m->held_n++; m->held += (size + 0xffff) & ~(SIZE_T)0xffff; LeaveCriticalSection(&klvh_cs); }
    return p;
}

static BOOL klvh_free(klvh_mod *m, LPVOID addr, SIZE_T size, DWORD type)
{
    if (addr && klvh_in_high(addr)) {
        if (type & MEM_RELEASE) {
            DWORD n; BOOL ok = TRUE; DWORD err = 0;
            if (size) { SetLastError(ERROR_INVALID_PARAMETER); return FALSE; }       /* as Windows: a release names the whole block */
            EnterCriticalSection(&klvh_cs);
            n = klvh_release_pages((DWORD)(((DWORD_PTR)addr - KLVH_BASE) >> 16));
            if (n) {
                ok = klvh_real_VirtualFree(addr, (SIZE_T)n << 16, MEM_DECOMMIT); err = ok ? 0 : GetLastError();
                klvh_carved -= (SIZE_T)n << 16; klvh_released++;
                if (m) { m->held_n--; m->held -= (SIZE_T)n << 16; m->high -= (SIZE_T)n << 16; }
            } else klvh_bad_release++;
            LeaveCriticalSection(&klvh_cs);
            if (!n) { SetLastError(ERROR_INVALID_ADDRESS); return FALSE; }      /* not a block start: as Windows would answer */
            if (!ok) klog("high: decommit of %lu pages at %p failed (error %lu)", n, addr, err);
            return TRUE;                                        /* the pages are ours again whatever the decommit said */
        }
        if ((type & MEM_DECOMMIT) && !size) {
            /* MEM_DECOMMIT with size 0 means "the whole block" and Windows then wants the block's own base. The base of
               the Windows region is OUR CHUNK, so passing it on would either fail (ERROR_INVALID_ADDRESS, block not at
               the chunk's start) or decommit the WHOLE CHUNK - every neighbour's pages with it (block at the chunk's
               start). Review fix 2026-10-25: answer it for the carved block, as Windows would for a block of its own. */
            DWORD n;
            EnterCriticalSection(&klvh_cs); n = klvh_block_pages((DWORD)(((DWORD_PTR)addr - KLVH_BASE) >> 16)); LeaveCriticalSection(&klvh_cs);
            if (!n) { SetLastError(ERROR_INVALID_ADDRESS); return FALSE; }
            return klvh_real_VirtualFree(addr, (SIZE_T)n << 16, MEM_DECOMMIT);
        }
        return klvh_real_VirtualFree(addr, size, type);         /* a sized decommit inside a carved block: Windows' business */
    }
    if (m && (type & MEM_RELEASE) && addr) {
        /* a low-half block of this module going away: the size is not given to us; VirtualQuery it (reservation = allocation base) */
        MEMORY_BASIC_INFORMATION mbi; SIZE_T span = 0; BYTE *p = (BYTE *)addr;
        while (VirtualQuery(p, &mbi, sizeof mbi) && mbi.AllocationBase == addr && mbi.State != MEM_FREE) { span += mbi.RegionSize; p = (BYTE *)mbi.BaseAddress + mbi.RegionSize; }
        if (klvh_real_VirtualFree(addr, size, type)) {
            EnterCriticalSection(&klvh_cs);
            if (m->held_n > 0) m->held_n--;
            m->held = span <= m->held ? m->held - span : 0;
            LeaveCriticalSection(&klvh_cs);
            return TRUE;
        }
        return FALSE;
    }
    return klvh_real_VirtualFree(addr, size, type);
}

static LPVOID WINAPI klvh_VirtualAlloc(LPVOID addr, SIZE_T size, DWORD type, DWORD prot) { return klvh_alloc(klvh_who(_ReturnAddress()), addr, size, type, prot); }
static BOOL   WINAPI klvh_VirtualFree(LPVOID addr, SIZE_T size, DWORD type) { return klvh_free(klvh_who(_ReturnAddress()), addr, size, type); }
static LPVOID WINAPI klvh_VirtualAllocEx(HANDLE h, LPVOID addr, SIZE_T size, DWORD type, DWORD prot)
{   /* the Ex forms on this very process are the plain ones; another process is not our business */
    if (h == GetCurrentProcess() || GetProcessId(h) == GetCurrentProcessId()) return klvh_alloc(klvh_who(_ReturnAddress()), addr, size, type, prot);
    return klvh_real_VirtualAllocEx(h, addr, size, type, prot);
}
static BOOL WINAPI klvh_VirtualFreeEx(HANDLE h, LPVOID addr, SIZE_T size, DWORD type)
{
    if (h == GetCurrentProcess() || GetProcessId(h) == GetCurrentProcessId()) return klvh_free(klvh_who(_ReturnAddress()), addr, size, type);
    return klvh_real_VirtualFreeEx(h, addr, size, type);
}

/* ---------------------------------------------------------------- the import slots of a foreign module */
static int klvh_slot(void **slot, void *mine, const char *fn, const char *mod)
{   /* one import slot of ANOTHER module (not kl2.exe: klh_poke's guard is for the game's image); its page is made writable for the write */
    DWORD old; MEMORY_BASIC_INFORMATION mbi;
    if (*slot == mine) return 0;
    if (!VirtualQuery(slot, &mbi, sizeof mbi) || mbi.State != MEM_COMMIT) return 0;
    if (!VirtualProtect(slot, sizeof *slot, PAGE_READWRITE, &old)) { klog("high: %s: import slot of %s not writable (error %lu)", mod, fn, GetLastError()); return 0; }
    *slot = mine;
    VirtualProtect(slot, sizeof *slot, old, &old);
    return 1;
}

static void klvh_wrap(klvh_mod *m)
{   /* every import of VirtualAlloc(Ex) / VirtualFree(Ex) in m's import directory, whatever DLL name it is imported from */
    BYTE *base = (BYTE *)m->base; IMAGE_NT_HEADERS *nt; IMAGE_DATA_DIRECTORY *dd; IMAGE_IMPORT_DESCRIPTOR *d; int n = 0; char from[64] = "";
    if (!base || ((IMAGE_DOS_HEADER *)base)->e_magic != IMAGE_DOS_SIGNATURE) return;
    nt = (IMAGE_NT_HEADERS *)(base + ((IMAGE_DOS_HEADER *)base)->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE) return;
    m->size = nt->OptionalHeader.SizeOfImage;
    dd = &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
    if (!dd->VirtualAddress) { klog("high: %s has no import directory: not wrapped", m->name); return; }
    for (d = (IMAGE_IMPORT_DESCRIPTOR *)(base + dd->VirtualAddress); d->Name; d++) {
        IMAGE_THUNK_DATA *nm, *at;
        if (!d->OriginalFirstThunk) continue;
        nm = (IMAGE_THUNK_DATA *)(base + d->OriginalFirstThunk); at = (IMAGE_THUNK_DATA *)(base + d->FirstThunk);
        for (; nm->u1.AddressOfData; nm++, at++) {
            const char *fn; void *mine;
            if (IMAGE_SNAP_BY_ORDINAL(nm->u1.Ordinal)) continue;
            fn = (const char *)((IMAGE_IMPORT_BY_NAME *)(base + nm->u1.AddressOfData))->Name;
            if (!strcmp(fn, "VirtualAlloc")) mine = (void *)klvh_VirtualAlloc;
            else if (!strcmp(fn, "VirtualFree")) mine = (void *)klvh_VirtualFree;
            else if (!strcmp(fn, "VirtualAllocEx")) mine = (void *)klvh_VirtualAllocEx;
            else if (!strcmp(fn, "VirtualFreeEx")) mine = (void *)klvh_VirtualFreeEx;
            else continue;
            if (klvh_slot((void **)&at->u1.Function, mine, fn, m->name)) { n++; if (!from[0]) snprintf(from, sizeof from, "%s", (char *)base + d->Name); }
        }
    }
    m->slots += n;
    if (klvh_log || !n) klog("high: %s at %p (%lu KB): %d import slot(s) of VirtualAlloc / VirtualFree%s%s%s", m->name, (void *)base, (unsigned long)(m->size >> 10), n,
                             n ? " wrapped (imported from " : " - NOTHING wrapped (it allocates through another DLL or by ordinal)", n ? from : "", n ? ")" : "");
}

static klvh_mod *klvh_find_n(const char *leaf, int n)
{
    int i;
    for (i = 0; i < klvh_nmods; i++) if (!_strnicmp(klvh_mods[i].name, leaf, n) && !klvh_mods[i].name[n]) return &klvh_mods[i];
    return 0;
}
static klvh_mod *klvh_find(const char *leaf) { return klvh_find_n(leaf, (int)strlen(leaf)); }

static void klvh_seen(HMODULE h, const char *leaf)
{   /* a module is in the process (now, or just loaded): wrap it if it is on a list */
    klvh_mod *m = klvh_find(leaf);
    if (!m || m->base == h) return;
    EnterCriticalSection(&klvh_cs);
    if (m->base != h) { m->base = h; m->slots = 0; }
    LeaveCriticalSection(&klvh_cs);
    klvh_wrap(m);
}

/* LdrRegisterDllNotification (ntdll, Vista+): a later load of a listed module, e.g. the driver with the D3D device */
typedef struct { USHORT Length; USHORT MaximumLength; PWSTR Buffer; } klvh_ustr;
typedef struct { ULONG Flags; const klvh_ustr *FullDllName; const klvh_ustr *BaseDllName; PVOID DllBase; ULONG SizeOfImage; } klvh_ldr_data;
typedef VOID (CALLBACK *klvh_ldr_cb)(ULONG, const klvh_ldr_data *, PVOID);
typedef LONG (NTAPI *klvh_ldr_reg)(ULONG, klvh_ldr_cb, PVOID, PVOID *);
static PVOID klvh_ldr_cookie;

static void klvh_gone(HMODULE h)
{   /* a listed module is unloading: forget its base, so a reload at the SAME address is wrapped again (klvh_seen would
       otherwise see 'already this base' and leave the fresh, unwrapped IAT alone) and its old range stops attributing
       whoever lands there next. Its blocks in the high half stay carved (a release through a slot that is gone cannot
       reach us; counted nowhere - a leak above 2 GB costs the game nothing). Review fix 2026-10-25. */
    int i;
    EnterCriticalSection(&klvh_cs);
    for (i = 0; i < klvh_nmods; i++) if (klvh_mods[i].base == h) { klvh_mods[i].base = 0; klvh_mods[i].size = 0; klvh_mods[i].slots = 0; }
    LeaveCriticalSection(&klvh_cs);
}

static VOID CALLBACK klvh_on_dll(ULONG reason, const klvh_ldr_data *d, PVOID ctx)
{
    char leaf[64]; int i, n;
    (void)ctx;
    if (!d) return;
    if (reason == 2 /* LDR_DLL_NOTIFICATION_REASON_UNLOADED */) { klvh_gone((HMODULE)d->DllBase); return; }
    if (reason != 1 /* LDR_DLL_NOTIFICATION_REASON_LOADED */ || !d->BaseDllName || !d->BaseDllName->Buffer) return;
    n = d->BaseDllName->Length / 2; if (n >= (int)sizeof leaf) n = sizeof leaf - 1;
    for (i = 0; i < n; i++) leaf[i] = d->BaseDllName->Buffer[i] < 128 ? (char)d->BaseDllName->Buffer[i] : '?';
    leaf[n] = 0;
    klvh_seen((HMODULE)d->DllBase, leaf);
}

static void klvh_modules_now(void)
{   /* the modules already in the process (ReShade32 as the d3d9 proxy, the Steam overlay ... load before this DLL) */
    typedef BOOL (WINAPI *enum_fn)(HANDLE, HMODULE *, DWORD, LPDWORD);
    HMODULE k = GetModuleHandleA("kernel32.dll"), mods[512]; DWORD need = 0, i; char path[MAX_PATH], *leaf;
    enum_fn en = k ? (enum_fn)GetProcAddress(k, "K32EnumProcessModules") : 0;
    if (!en || !en(GetCurrentProcess(), mods, sizeof mods, &need)) return;
    if (need > sizeof mods) need = sizeof mods;
    for (i = 0; i < need / sizeof(HMODULE); i++) {
        if (!GetModuleFileNameA(mods[i], path, sizeof path)) continue;
        leaf = strrchr(path, '\\'); klvh_seen(mods[i], leaf ? leaf + 1 : path);
    }
}

/* ---------------------------------------------------------------- the high half itself */
static int klvh_flag_on(void)
{   /* kl2.exe's in-memory header: IMAGE_FILE_LARGE_ADDRESS_AWARE */
    BYTE *b = (BYTE *)(DWORD_PTR)img_lo; IMAGE_NT_HEADERS *nt;
    if (!b || ((IMAGE_DOS_HEADER *)b)->e_magic != IMAGE_DOS_SIGNATURE) return 0;
    nt = (IMAGE_NT_HEADERS *)(b + ((IMAGE_DOS_HEADER *)b)->e_lfanew);
    return (nt->FileHeader.Characteristics & IMAGE_FILE_LARGE_ADDRESS_AWARE) != 0;
}

static SIZE_T klvh_high_walk(int want_free, int *count, char *who, int cap)
{   /* the regions above 2 GB that are (want_free) free / (else) in use: total bytes, count, and the first few named */
    MEMORY_BASIC_INFORMATION mbi; BYTE *p = (BYTE *)(DWORD_PTR)KLVH_BASE; SIZE_T total = 0; int n = 0, at = 0;
    who[0] = 0;
    while (p >= (BYTE *)(DWORD_PTR)KLVH_BASE && VirtualQuery(p, &mbi, sizeof mbi)) {
        if ((mbi.State == MEM_FREE) == (want_free != 0)) {
            total += mbi.RegionSize; n++;
            if (at < cap - 60) {
                char name[MAX_PATH] = "", *leaf = name;
                if (!want_free && mbi.Type == MEM_IMAGE && GetModuleFileNameA((HMODULE)mbi.AllocationBase, name, sizeof name)) { leaf = strrchr(name, '\\'); leaf = leaf ? leaf + 1 : name; }
                at += snprintf(who + at, cap - at, " %p+%luK%s%s", mbi.BaseAddress, (unsigned long)(mbi.RegionSize >> 10), *leaf ? " " : "", leaf);
            }
        }
        if ((BYTE *)mbi.BaseAddress + mbi.RegionSize <= p) break;          /* wrapped around the top */
        p = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    *count = n;
    return total;
}

static void klvh_high_census(void)
{   /* what is above 2 GB before we take it: expected nothing (a 32-bit image's DLLs and the first heap sit low) */
    char who[400]; int n; SIZE_T used = klvh_high_walk(0, &n, who, sizeof who);
    klog("high: before the reservation %d region(s) already above 2 GB, %.1f MB%s%s", n, used / 1048576.0, n ? ":" : "", who);
}

static SIZE_T klvh_high_left(void)
{   /* what is STILL FREE above 2 GB after the takeover: must be 0, else the game can land there once the low half is
       full (the chunk limit, or a hole smaller than 64 KB cannot exist - so any number here means the limit was hit) */
    char who[400]; int n; SIZE_T left = klvh_high_walk(1, &n, who, sizeof who);
    if (left) klog("high: WARNING %d piece(s) above 2 GB are still free after the takeover, %.1f MB%s - the game's heap or a stack can land there once the low half is full (the LAA tag crash); raise KLVH_CHUNKS:%s",
                   n, left / 1048576.0, klvh_nchunk >= KLVH_CHUNKS ? " (the chunk limit was hit)" : "", who);
    return left;
}

static int klvh_take_high(void)
{   /* reserve the high half top-down, 64 MB at a time, then smaller pieces for what is left -> chunks (0 = there is no high half) */
    static const SIZE_T sizes[] = { 64u << 20, 32u << 20, 16u << 20, 8u << 20, 4u << 20, 2u << 20, 1u << 20, 256u << 10, 64u << 10 };
    int s; BYTE *lo = 0, *hi = 0;
    for (s = 0; s < (int)(sizeof sizes / sizeof sizes[0]) && klvh_nchunk < KLVH_CHUNKS; s++) {
        for (;;) {
            BYTE *p = (BYTE *)klvh_real_VirtualAlloc(0, sizes[s], MEM_RESERVE | MEM_TOP_DOWN, PAGE_NOACCESS);
            DWORD i, n;
            if (!p) break;
            if ((DWORD_PTR)p < KLVH_BASE) { klvh_real_VirtualFree(p, 0, MEM_RELEASE); break; }     /* the high half is full: this one came from the low */
            klvh_chunk[klvh_nchunk].base = p; klvh_chunk[klvh_nchunk].size = sizes[s]; klvh_nchunk++;
            klvh_high_total += sizes[s];
            for (i = (DWORD)(((DWORD_PTR)p - KLVH_BASE) >> 16), n = (DWORD)(sizes[s] >> 16); n; i++, n--) klvh_set(klvh_in, i, 1);
            if (!lo || p < lo) lo = p;
            if (p + sizes[s] > hi) hi = p + sizes[s];
            if (klvh_nchunk >= KLVH_CHUNKS) break;
        }
    }
    if (!klvh_nchunk) return 0;
    klog("high: the high half is OURS: %d chunk(s), %.0f MB reserved (nothing committed) from %p to %p; the game, its heap, the stacks and the DLLs cannot land there now",
         klvh_nchunk, klvh_high_total / 1048576.0, (void *)lo, (void *)hi);
    klvh_high_left();                                           /* 0 expected; a WARNING line otherwise */
    return 1;
}

/* ---------------------------------------------------------------- init / tick */
static void klvh_list(const char *key, const char *def, int place)
{
    char buf[512], *q, *e;
    GetPrivateProfileStringA("Memory", key, def, buf, sizeof buf, klh_ini);
    for (q = buf; *q && klvh_nmods < KLVH_MODS; q = e) {
        while (*q == ' ' || *q == ',' || *q == ';') q++;
        if (!*q) break;
        for (e = q; *e && *e != ',' && *e != ';'; e++) ;
        while (e > q && e[-1] == ' ') e--;
        if (e > q && e - q < (int)sizeof klvh_mods[0].name && !klvh_find_n(q, (int)(e - q))) {
            memcpy(klvh_mods[klvh_nmods].name, q, e - q); klvh_mods[klvh_nmods].name[e - q] = 0; klvh_mods[klvh_nmods].place = place; klvh_nmods++;
        }
        while (*e == ' ') e++;
    }
}

static void klvh_init(void)
{
    HMODULE k = GetModuleHandleA("kernel32.dll"), nt = GetModuleHandleA("ntdll.dll"); klvh_ldr_reg reg; int i; char l[400]; int at = 0;
    klvh_mode = GetPrivateProfileIntA("Memory", "High", 0, klh_ini); if (klvh_mode < 0 || klvh_mode > 2) klvh_mode = 0;
    if (!klvh_mode) return;
    klvh_log = GetPrivateProfileIntA("Memory", "HighLog", 1, klh_ini) != 0;
    InitializeCriticalSection(&klvh_cs);
    klvh_real_VirtualAlloc = k ? (LPVOID (WINAPI *)(LPVOID, SIZE_T, DWORD, DWORD))GetProcAddress(k, "VirtualAlloc") : 0;
    klvh_real_VirtualFree = k ? (BOOL (WINAPI *)(LPVOID, SIZE_T, DWORD))GetProcAddress(k, "VirtualFree") : 0;
    klvh_real_VirtualAllocEx = k ? (LPVOID (WINAPI *)(HANDLE, LPVOID, SIZE_T, DWORD, DWORD))GetProcAddress(k, "VirtualAllocEx") : 0;
    klvh_real_VirtualFreeEx = k ? (BOOL (WINAPI *)(HANDLE, LPVOID, SIZE_T, DWORD))GetProcAddress(k, "VirtualFreeEx") : 0;
    if (!klvh_real_VirtualAlloc || !klvh_real_VirtualFree || !klvh_real_VirtualAllocEx || !klvh_real_VirtualFreeEx) { klog("high: kernel32's VirtualAlloc / VirtualFree not found: off"); klvh_mode = 0; return; }
    klvh_list("HighModules", "nvd3dum.dll,nvwgf2um.dll,ReShade32.dll,gameoverlayrenderer.dll", 1);
    klvh_list("HighCount", "d3d9.dll,dxgi.dll,d3d10.dll", 0);
    if (klvh_mode == 2) {
        if (!klvh_flag_on()) { klog("high: High=2 asked but kl2.exe runs WITHOUT the 4 GB flag (IMAGE_FILE_LARGE_ADDRESS_AWARE): measuring only (High=1)"); klvh_mode = 1; }
        else { klvh_high_census(); if (klvh_take_high()) klvh_placing = 1; else { klog("high: High=2: no address above 2 GB could be reserved (the flag is set but Windows gave none): measuring only"); klvh_mode = 1; } }
    } else if (klvh_flag_on()) klog("high: kl2.exe runs WITH the 4 GB flag and High=1: nothing is reserved above 2 GB - the GAME may get a block there (the LAA crash of 2026-10-25 01:40); High=2 is the safe setting with the flag");
    for (i = 0; i < klvh_nmods && at < (int)sizeof l - 60; i++) at += snprintf(l + at, sizeof l - at, "%s%s%s", i ? ", " : "", klvh_mods[i].name, klvh_mods[i].place ? "" : " (count only)");
    klog("high: %s: %s", klvh_placing ? "PLACING the listed modules' reservations in the high half" : "MEASURING the listed modules' reservations (placement unchanged)", l);
    reg = nt ? (klvh_ldr_reg)GetProcAddress(nt, "LdrRegisterDllNotification") : 0;
    if (!reg || reg(0, klvh_on_dll, 0, &klvh_ldr_cookie) != 0) klog("high: LdrRegisterDllNotification %s: a module loaded from now on is wrapped by the 10 s pass instead", reg ? "failed" : "not found");
    klvh_modules_now();
}

static void klvh_tick(void)
{   /* every 10 s (in step with klmem's line): the census; also a re-scan of the module list (the fall-back for a missed load notification) */
    static DWORD calls, last; DWORD now; int i, at = 0; char l[900];
    if (!klvh_mode || (calls++ & 63)) return;
    now = GetTickCount();
    if (now - last < 10000) return;
    last = now;
    klvh_modules_now();
    if (!klvh_log) return;
    EnterCriticalSection(&klvh_cs);
    for (i = 0; i < klvh_nmods && at < (int)sizeof l - 120; i++) {
        klvh_mod *m = &klvh_mods[i];
        if (!m->base) continue;
        at += snprintf(l + at, sizeof l - at, "%s%s %ld asked (%.0f MB) %ld held (%.1f MB)", at ? "; " : "", m->name, m->asked_n, m->asked_mb_x16 / 16.0, m->held_n, m->held / 1048576.0);
        if (klvh_placing && m->place) at += snprintf(l + at, sizeof l - at, " of which %.1f MB in the high half", m->high / 1048576.0);
    }
    if (klvh_placing) at += snprintf(l + at, sizeof l - at, " | high half %.0f MB in %d chunk(s), carved now %.1f MB, released %ld, spilled %ld (%.1f MB), passed %ld, bad release %ld",
                                     klvh_high_total / 1048576.0, klvh_nchunk, klvh_carved / 1048576.0, klvh_released, klvh_spilled, klvh_spilled_bytes / 1048576.0, klvh_passed, klvh_bad_release);
    LeaveCriticalSection(&klvh_cs);
    klog("high: every 10 s: %s", at ? l : "none of the listed modules is loaded");
}

#endif /* KLHIGH_C */
