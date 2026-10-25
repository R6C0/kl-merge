/* klarena.c - [Memory] DriverArena: the NVIDIA driver's small process-heap blocks from 1 MB chunks that go back to the system
   when they empty (default 0; TEST first).

   Why (K49E, DM05A 2026-10-25): nvd3dum.dll puts +366 MB of ~2.8 KB blocks on the process heap in one 10 s at level start (no kl2
   frame on the stack: the driver's own thread), frees them 10 s later, and the NT heap keeps the peak as reservation (allocated 942 ->
   544 MB, reserved stays 1015 MB). Free address space is then 14 MB, so every block of 508 KB+ (VirtualAlloc'd, needs fresh room)
   fails: kl2's HeapAlloc refusals at 0x7bb33c. Here those small blocks live in chunks of their own; an empty chunk is released (one
   per size class is kept, so the +300/-470 MB sawtooth does not turn into VirtualAlloc thrash), and the room comes back.

   How: nvd3dum.dll's own import slots HeapAlloc / HeapFree / HeapReAlloc / HeapSize (it imports them from KERNEL32 directly,
   kl-merge-27 checked the owner's driver build). Only blocks asked of the PROCESS heap, of at most KLAR_MAX bytes, come from the arena;
   all else, and any arena miss (no room for a chunk), goes to the real heap as before. Ownership is by address (a 64 KB-granular map),
   so a free of a block the driver took before the patch, or of any foreign pointer, passes through. d3d9.dll and nvgpucomp32.dll get
   the same Free / ReAlloc / Size slots (ownership test only, they never allocate here) in case a driver block is freed by them.
   Each block has an 8-byte header (requested size, magic): HeapSize returns the requested size like the NT heap. HEAP_ZERO_MEMORY is
   honoured (also on ReAlloc growth), HEAP_REALLOC_IN_PLACE_ONLY fails rather than moves, HEAP_NO_SERIALIZE is ignored (always locked).
   Import slots and data only: no code bytes are written (SHIP rule). */

#define KLAR_MAX 65528                 /* the biggest request served (header included = 64 KB) */
#define KLAR_CHUNK (1 << 20)
#define KLAR_NCHUNK 2048               /* descriptors: 2 GB of chunks at most */
#define KLAR_MAGIC 0x4b4c4152u         /* 'KLAR' */
#define KLAR_DEAD 0x64656164u

typedef struct klar_chunk { BYTE *base; struct klar_chunk *next, *prev; void *free; DWORD bump, used, cap; int cls, listed; } klar_chunk;
static const DWORD klar_size[] = { 16, 24, 32, 48, 64, 80, 96, 128, 160, 192, 256, 320, 384, 512, 640, 768, 1024, 1280, 1536, 2048, 2560,
                                  3072, 4096, 5120, 6144, 8192, 10240, 12288, 16384, 20480, 24576, 32768, 40960, 49152, 65536 };
#define KLAR_NCLS (sizeof klar_size / sizeof klar_size[0])
static struct { SRWLOCK lk; klar_chunk *part, *kept; } klar_cls[KLAR_NCLS];
static BYTE klar_clsof[4097];                    /* (header + request + 15) >> 4 -> class */
static klar_chunk *volatile klar_map[65536];      /* address >> 16 -> its chunk (4 GB: also right with the 4 GB flag) */
static klar_chunk klar_desc[KLAR_NCHUNK], *klar_dfree;
static CRITICAL_SECTION klar_dcs;
static int klar_on;
static HANDLE klar_pheap;
static volatile LONG klar_chunks, klar_peak, klar_kept, klar_fails, klar_bad;
static volatile LONG64 klar_inuse, klar_nalloc, klar_nfree, klar_npass;
static LPVOID (WINAPI *klar_real_alloc)(HANDLE, DWORD, SIZE_T);
static BOOL (WINAPI *klar_real_free)(HANDLE, DWORD, LPVOID);
static LPVOID (WINAPI *klar_real_realloc)(HANDLE, DWORD, LPVOID, SIZE_T);
static SIZE_T (WINAPI *klar_real_size)(HANDLE, DWORD, LPCVOID);

static void klar_unlist(int c, klar_chunk *k)
{
    if (!k->listed) return;
    if (k->prev) k->prev->next = k->next; else klar_cls[c].part = k->next;
    if (k->next) k->next->prev = k->prev;
    k->next = k->prev = 0; k->listed = 0;
}

static void klar_list(int c, klar_chunk *k)
{
    if (k->listed) return;
    k->prev = 0; k->next = klar_cls[c].part; if (k->next) k->next->prev = k; klar_cls[c].part = k; k->listed = 1;
}

static klar_chunk *klar_newchunk(int c)
{   /* under the class lock: a descriptor and 1 MB of fresh room; 0 = none (the caller goes to the real heap) */
    klar_chunk *k; BYTE *b; DWORD i;
    EnterCriticalSection(&klar_dcs);
    k = klar_dfree; if (k) klar_dfree = k->next;
    LeaveCriticalSection(&klar_dcs);
    if (!k) return 0;
    b = (BYTE *)VirtualAlloc(0, KLAR_CHUNK, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    if (!b) { EnterCriticalSection(&klar_dcs); k->next = klar_dfree; klar_dfree = k; LeaveCriticalSection(&klar_dcs); return 0; }
    memset(k, 0, sizeof *k); k->base = b; k->cls = c; k->cap = KLAR_CHUNK / klar_size[c];
    for (i = 0; i < KLAR_CHUNK >> 16; i++) klar_map[((DWORD_PTR)b >> 16) + i] = k;
    i = InterlockedIncrement(&klar_chunks); if ((LONG)i > klar_peak) InterlockedExchange(&klar_peak, (LONG)i);
    return k;
}

static void klar_dropchunk(klar_chunk *k)
{   /* under the class lock, k empty and off every list */
    DWORD i;
    for (i = 0; i < KLAR_CHUNK >> 16; i++) klar_map[((DWORD_PTR)k->base >> 16) + i] = 0;
    VirtualFree(k->base, 0, MEM_RELEASE);
    InterlockedDecrement(&klar_chunks);
    EnterCriticalSection(&klar_dcs); k->next = klar_dfree; klar_dfree = k; LeaveCriticalSection(&klar_dcs);
}

static void *klar_take(SIZE_T n)
{   /* a block of n bytes (n <= KLAR_MAX) or 0 */
    int c = klar_clsof[(n + 8 + 15) >> 4]; klar_chunk *k; DWORD *b;
    AcquireSRWLockExclusive(&klar_cls[c].lk);
    k = klar_cls[c].part;
    if (!k && (k = klar_cls[c].kept) != 0) { klar_cls[c].kept = 0; InterlockedDecrement(&klar_kept); klar_list(c, k); }
    if (!k && (k = klar_newchunk(c)) != 0) klar_list(c, k);
    if (!k) { ReleaseSRWLockExclusive(&klar_cls[c].lk); InterlockedIncrement(&klar_fails); return 0; }
    if (k->free) { b = (DWORD *)k->free; k->free = *(void **)(b + 2); }
    else { b = (DWORD *)(k->base + k->bump); k->bump += klar_size[c]; }
    if (++k->used == k->cap) klar_unlist(c, k);
    ReleaseSRWLockExclusive(&klar_cls[c].lk);
    b[0] = (DWORD)n; b[1] = KLAR_MAGIC;
    InterlockedExchangeAdd64(&klar_inuse, (LONG64)n); InterlockedIncrement64(&klar_nalloc);
    return b + 2;
}

static klar_chunk *klar_owner(LPCVOID p)
{   /* the chunk p lies in, or 0 (not an arena block) */
    klar_chunk *k;
    if (!p) return 0;
    k = klar_map[(DWORD_PTR)p >> 16];
    return k && (DWORD_PTR)p >= (DWORD_PTR)k->base && (DWORD_PTR)p < (DWORD_PTR)k->base + KLAR_CHUNK ? k : 0;
}

static int klar_put(klar_chunk *k, void *p)
{   /* p (an arena block of k) back; 0 = not a live block (double free / not a block start): left alone */
    DWORD *b = (DWORD *)p - 2; int c = k->cls; DWORD n;
    if (b[1] != KLAR_MAGIC || ((BYTE *)b - k->base) % klar_size[c]) { InterlockedIncrement(&klar_bad); return 0; }
    n = b[0]; b[1] = KLAR_DEAD;
    AcquireSRWLockExclusive(&klar_cls[c].lk);
    *(void **)(b + 2) = k->free; k->free = b;
    if (k->used-- == k->cap) klar_list(c, k);
    if (!k->used) {
        klar_unlist(c, k);
        if (!klar_cls[c].kept) { k->free = 0; k->bump = 0; klar_cls[c].kept = k; InterlockedIncrement(&klar_kept); }   /* one empty per class stays */
        else klar_dropchunk(k);
    }
    ReleaseSRWLockExclusive(&klar_cls[c].lk);
    InterlockedExchangeAdd64(&klar_inuse, -(LONG64)n); InterlockedIncrement64(&klar_nfree);
    return 1;
}

static LPVOID WINAPI klar_halloc(HANDLE h, DWORD f, SIZE_T n)
{
    if (h == klar_pheap && n <= KLAR_MAX) {
        void *p = klar_take(n);
        if (p) { if (f & HEAP_ZERO_MEMORY) memset(p, 0, n); return p; }
    }
    InterlockedIncrement64(&klar_npass);
    return klar_real_alloc(h, f, n);
}

static BOOL WINAPI klar_hfree(HANDLE h, DWORD f, LPVOID p)
{
    klar_chunk *k = klar_owner(p);
    if (k) return klar_put(k, p);
    return klar_real_free(h, f, p);
}

static SIZE_T WINAPI klar_hsize(HANDLE h, DWORD f, LPCVOID p)
{
    klar_chunk *k = klar_owner(p);
    if (k) { const DWORD *b = (const DWORD *)p - 2; return b[1] == KLAR_MAGIC ? (SIZE_T)b[0] : (SIZE_T)-1; }
    return klar_real_size(h, f, p);
}

static LPVOID WINAPI klar_hrealloc(HANDLE h, DWORD f, LPVOID p, SIZE_T n)
{
    klar_chunk *k = klar_owner(p); DWORD *b; DWORD old; void *q;
    if (!k) return klar_real_realloc(h, f, p, n);
    b = (DWORD *)p - 2;
    if (b[1] != KLAR_MAGIC) { InterlockedIncrement(&klar_bad); SetLastError(ERROR_INVALID_PARAMETER); return 0; }
    old = b[0];
    if (n + 8 <= klar_size[k->cls]) {   /* fits the slot it has: in place */
        if ((f & HEAP_ZERO_MEMORY) && n > old) memset((BYTE *)p + old, 0, n - old);
        b[0] = (DWORD)n; InterlockedExchangeAdd64(&klar_inuse, (LONG64)n - (LONG64)old);
        return p;
    }
    if (f & HEAP_REALLOC_IN_PLACE_ONLY) { SetLastError(ERROR_NOT_ENOUGH_MEMORY); return 0; }
    q = klar_halloc(klar_pheap, f & ~HEAP_REALLOC_IN_PLACE_ONLY, n);   /* arena or the real process heap; ZERO_MEMORY zeroes it all */
    if (!q) return 0;
    memcpy(q, p, old < n ? old : n);
    klar_put(k, p);
    return q;
}

static int klar_patch(HMODULE m, int alloc)
{   /* m's IAT slots of HeapAlloc (only if alloc) / HeapFree / HeapReAlloc / HeapSize -> ours; matches kernel32's, kernelbase's and
       ntdll's Rtl* (kernel32's forward there), and in a TEST build VaLog's wrappers -> how many were changed */
    static const char *fn[4] = { "HeapAlloc", "HeapFree", "HeapReAlloc", "HeapSize" }, *rtl[4] = { "RtlAllocateHeap", "RtlFreeHeap", "RtlReAllocateHeap", "RtlSizeHeap" };
    void *mine[4] = { (void *)klar_halloc, (void *)klar_hfree, (void *)klar_hrealloc, (void *)klar_hsize }, *old[4][4];
    HMODULE k32 = GetModuleHandleA("kernel32.dll"), kb = GetModuleHandleA("kernelbase.dll"), nt0 = GetModuleHandleA("ntdll.dll");
    BYTE *base = (BYTE *)m; IMAGE_NT_HEADERS *nt; IMAGE_DATA_DIRECTORY *dd; void **slot, **end; int i, j, done = 0;
    if (((IMAGE_DOS_HEADER *)base)->e_magic != IMAGE_DOS_SIGNATURE) return 0;
    nt = (IMAGE_NT_HEADERS *)(base + ((IMAGE_DOS_HEADER *)base)->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE) return 0;
    dd = &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IAT];
    if (!dd->VirtualAddress || !dd->Size) return 0;
    for (i = 0; i < 4; i++) {
        old[i][0] = k32 ? (void *)GetProcAddress(k32, fn[i]) : 0; old[i][1] = kb ? (void *)GetProcAddress(kb, fn[i]) : 0;
        old[i][2] = nt0 ? (void *)GetProcAddress(nt0, rtl[i]) : 0; old[i][3] = 0;
    }
#ifdef KLHOOK_TEST
    old[0][3] = (void *)klva_halloc; old[1][3] = (void *)klva_hfree; old[2][3] = (void *)klva_hrealloc;   /* VaLog got there first */
#endif
    slot = (void **)(base + dd->VirtualAddress); end = (void **)(base + dd->VirtualAddress + dd->Size);
    for (; slot < end; slot++) {
        void *cur = *slot;
        if (!cur) continue;
        for (i = alloc ? 0 : 1; i < 4; i++) { for (j = 0; j < 4 && (!old[i][j] || cur != old[i][j]); j++) ; if (j < 4) break; }
        if (i == 4) continue;
        if (klh_poke(slot, &cur, sizeof cur, &mine[i], sizeof mine[i], fn[i])) done++;
    }
    return done;
}

static DWORD WINAPI klar_watch(LPVOID unused)
{   /* every 100 ms for 30 min: d3d9 / nvgpucomp32 (ownership slots) first, then nvd3dum (all four), each once */
    static const char *name[3] = { "d3d9.dll", "nvgpucomp32.dll", "nvd3dum.dll" }; HMODULE got[3] = { 0, 0, 0 }; int t, i; (void)unused;
    for (t = 0; t < 18000; t++) {
        for (i = 0; i < 3; i++) {
            HMODULE m = GetModuleHandleA(name[i]); int n;
            if (!m || m == got[i]) continue;
            got[i] = m;
            __try { n = klar_patch(m, i == 2); } __except (EXCEPTION_EXECUTE_HANDLER) { n = 0; }
            klog("arena: %s at %p: %d heap import slot(s) taken%s", name[i], (void *)m, n, i == 2 ? " (its small process-heap blocks now come from the arena)" : " (frees of arena blocks only)");
        }
        Sleep(100);
    }
    return 0;
}

static void klarena_tick(void)
{   /* every 10 s */
    static DWORD last;
    if (!klar_on || GetTickCount() - last < 10000) return;
    last = GetTickCount();
    klog("arena: %ld chunk(s) of 1 MB held (peak %ld, %ld kept empty), %.1f MB in use; blocks taken %I64d, given back %I64d, to the real heap %I64d; no room for a chunk %ld; bad frees %ld",
         klar_chunks, klar_peak, klar_kept, klar_inuse / 1048576.0, klar_nalloc, klar_nfree, klar_npass, klar_fails, klar_bad);
}

static void klarena_init(void)
{
    HMODULE k32 = GetModuleHandleA("kernel32.dll"); int i, c;
    klar_on = GetPrivateProfileIntA("Memory", "DriverArena", 0, klh_ini) != 0;
    if (!klar_on) return;
    klar_real_alloc = (void *)GetProcAddress(k32, "HeapAlloc"); klar_real_free = (void *)GetProcAddress(k32, "HeapFree");
    klar_real_realloc = (void *)GetProcAddress(k32, "HeapReAlloc"); klar_real_size = (void *)GetProcAddress(k32, "HeapSize");
    if (!klar_real_alloc || !klar_real_free || !klar_real_realloc || !klar_real_size) { klar_on = 0; klog("arena: a heap function is not exported: DriverArena off"); return; }
    klar_pheap = GetProcessHeap();
    for (i = 0, c = 0; i <= 4096; i++) { while (klar_size[c] < (DWORD)i << 4) c++; klar_clsof[i] = (BYTE)c; }
    for (c = 0; c < (int)KLAR_NCLS; c++) InitializeSRWLock(&klar_cls[c].lk);
    for (i = KLAR_NCHUNK - 1; i >= 0; i--) { klar_desc[i].next = klar_dfree; klar_dfree = &klar_desc[i]; }
    InitializeCriticalSection(&klar_dcs);
    CloseHandle(CreateThread(0, 64 << 10, klar_watch, 0, STACK_SIZE_PARAM_IS_A_RESERVATION, 0));
    klog("arena: DriverArena on: nvd3dum.dll's process-heap blocks up to %d bytes come from 1 MB chunks that are released when empty (one per size class kept)", KLAR_MAX);
}
