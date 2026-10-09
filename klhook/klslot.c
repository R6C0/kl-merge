/*
 * klslot.c - expansion content beside the stock game: a Dead Men map in its own folder, taking over one
 * Fragile Alliance entry only while KLHook.ini says so. Part of KLHook (klhook.c); full reasoning,
 * evidence and the plan for the menu-selected version: re\slot_redirect.md.
 *
 * NOTHING ON DISK IS REPLACED. Everything this file needs lives in <game>\KLExpansion\ and KLHook.ini;
 * delete dinput8.dll and that folder and the game is stock again.
 *
 * WHAT IT DOES (all off unless KLHook.ini has [Expansion] Enable=1)
 *  1. File redirect (the first step, no address of kl2.exe involved). Five import-table entries of the
 *     exe are pointed at wrappers: KERNEL32 CreateFileA, CreateFileW, GetFileAttributesA, FindFirstFileA
 *     and the C runtime's fopen. A wrapper only changes the PATH of a read-only open:
 *       [Redirect] F01=DM03   every file the game opens under  ...\Scenes\Locations\F01\  is opened
 *                             from  <game>\KLExpansion\Maps\DM03\  instead (same file name), if it is
 *                             there. The engine still believes it loads "Locations/F01/F01_Main", so
 *                             the archive in Maps\DM03 is the one built for the F01 slot (members
 *                             Scenes/Locations/F01/F01_Main.*), exactly what is installed over the
 *                             slot today. Works for every route into the level: Arcade, FA lobby, a
 *                             network client (index -> its own table) and "-o DefaultScene=".
 *       Overlay               a file that exists as  <game>\KLExpansion\Overlay\<path relative to the
 *                             game folder>  replaces the game's. This is how menu text / pictures are
 *                             changed without touching the stock Patch01.zip (Overlay\Patch01.zip =
 *                             stock members + ours) and how a level in a NEW folder is supplied for
 *                             [Slots] below (Overlay\Scenes\Locations\F0M03\F0M03_Main.zip).
 *  2. [Slots] F09=Locations/F0M03/F0M03_Main  - name redirect (re\fa_slots.md section 5): the operand
 *     of the constructor's "push <slot name>" is pointed at our string, so the engine itself loads
 *     another scene name. The archive must then be built under that name. Use a slot the owner cannot
 *     play (an unowned DLC slot: 4 = F05, 7 = F08, 8 = F09); its lock byte is released for that slot.
 *  3. [Expansion] MountFirst=KLExpansion/KLPatch.zip - an extra archive mounted BEFORE Patch01.zip at
 *     every scene load, so it may hold only our members (alternative to Overlay\Patch01.zip).
 *
 * KLHook.ini
 *   [Expansion]
 *   Enable=1
 *   Root=KLExpansion      folder next to kl2.exe
 *   Overlay=1             0 = ignore <Root>\Overlay
 *   Fallback=1            a file missing from Maps\<map> : 1 = the stock file is used (logged),
 *                         0 = the open fails as if the file did not exist
 *   Log=1                 0 nothing, 1 every redirect once, 2 also every other open once (first live
 *                         check: shows which API opens which file and in which spelling)
 *   MountFirst=           archive name relative to the game folder, '/' or '\', ending in .zip
 *   [Redirect]            <folder under Scenes\Locations> = <folder under Root\Maps>, at most 16 lines
 *   F01=DM03
 *   [Slots]               F01..F09 = scene name without extension, at most 63 characters
 *   ;F09=Locations/F0M03/F0M03_Main
 *
 * BUILD: this file is #included by the hook build after klhook.c (it uses klhook.c's dir, klog and
 * img_lo and has no DllMain). In klauto.c: add  #include "klslot.c"  below the block that includes
 * klhook.c, and  kls_init(inst);  in DllMain's DLL_PROCESS_ATTACH branch before kla_init(inst). It does
 * not use anything of klauto.c and patches none of klauto.c's sites, so klhook.c alone may include it
 * the same way (call kls_init(inst) at the end of its DllMain).
 *
 * EVIDENCE (kl2.exe sha1 9d99e01d..., TimeDateStamp 0x4c80f728, base 0x400000; read with pefile +
 * capstone on 2026-10-09. NOTHING HERE HAS RUN IN THE GAME.)
 *  - Imports: KERNEL32 OriginalFirstThunk 0x8cce54 / FirstThunk 0x71005c, MSVCR90 0x8cd080 / 0x710288,
 *    not bound (TimeDateStamp 0), so the names are readable in memory. CreateFileA = [0xb10270]: 17
 *    references in .text, every one "call [0xb10270]" or "mov esi,[0xb10270]" - no copy of the pointer
 *    elsewhere. Callers: ZSysFileWintel slots 2-6 (0x5e2aa0, 0x7f70a0, 0x5085e0, 0x77e910, 0x789930),
 *    AsyncFd_Windows slot 4 (0x43d120), ZIOStreamerWintel slot 5 (0x7a2f30), ZDllSound slot 36
 *    (0x67e810), the DLC presence test 0x5432d0, WinMain 0x476730, the profile (0x47c5f0, 0x6587c0),
 *    0x6b2b10 (CREATE_ALWAYS, a writer), 0x7aeb10, three at 0xb0f4a0.. . fopen = [0xb10430], 8 calls
 *    (IOFSPhysicalAccess_t slot 0 0x74db40 among them). GetFileAttributesA 1 call (0x7606e0),
 *    FindFirstFileA 3 (ZSysFileWintel slots 14, 66, 67), CreateFileW 104 (not classified).
 *    Which of these the level loader actually uses for the archive, the .WHD/.WAV and the _LS files
 *    was NOT traced to the end: that is why all five are wrapped and why Log=2 exists.
 *  - Archive mount: the file system object is [0xdd263c] (ZSysFileWintel, vtable 0xb8ed84). The scene
 *    loader 0x7f4f90 calls vtbl+0xac at 0x7f55fe (unmount everything), then at 0x7f5600-0x7f5615
 *    "mov ecx,[0xdd263c]; mov eax,[ecx]; mov edx,[eax+0x98]; push 1; push 0xb251fc 'Patch01.zip';
 *    call edx" (slot 38 0x72f800 -> vtbl+0x13c = slot 79 0x809200, "ret 8"), and mounts the scene's own
 *    archive at 0x7f5827 through vtbl+0x90. Slot 79 copies the name, turns '\' into '/', overwrites
 *    the text from the last '.' with ".zip" (no '.' = nothing mounted, 0x8092cb), asks vtbl+0xa8, then
 *    probes the file with slot 2 = CreateFileA(name, GENERIC_READ, FILE_SHARE_READ, OPEN_EXISTING,
 *    0x8000080) and returns quietly when that fails (0x80930a). So "Patch01.zip" reaches CreateFileA
 *    as a name relative to the current directory. 0xb251fc has one reference (0x7f5611); no branch in
 *    .text targets 0x7f5610..0x7f5616 (scan of every rel32 / rel8 branch).
 *    First mounted archive wins a name: the earlier boot-config research (FS slot 30 0x468bb0), not
 *    re-read here and never observed.
 *  - [Slots]: the nine "68 <imm32>" pushes at 0x836016.. and the "c6 46 xx 00" lock bytes at 0x8468ea..
 *    were re-read byte for byte (table below); 0xb75044 "Locations/F01/F01_Main" has exactly one other
 *    reference, the session default "68 44 50 b7 00" at 0x69981e.
 *  - DINPUT8.dll is a static import of kl2.exe: DllMain runs before the exe's entry point.
 *    ASSUMPTION: the loader has filled the exe's import table by then (Windows snaps all imports
 *    before it runs any DllMain). The code checks instead of trusting: an entry that does not point
 *    into a loaded image is left alone and reported.
 *  TESTED OFF-GAME (scratch harness, see re\slot_redirect.md section 8): the five wrappers on a
 *  made-up game folder, the patcher against a mapped copy of the real kl2.exe, the mount stub on a
 *  synthetic call site.
 */
#ifndef KLSLOT_C
#define KLSLOT_C
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define KLS_TIMESTAMP 0x4c80f728u
#define KLS_IMAGESIZE 0x134e000u
#define KLS_DLCMGR    0x0168f750              /* ZDownloadableContentManagerSteam * (0 until created) */
#define KLS_DLCMGR_VT 0x00bd5494
#define KLS_FA        9
#define KLS_NAME      0x40
#define KLS_RULES     16

static LONG_PTR kls_delta;                    /* 0 in the game; the test harness maps a copy elsewhere */
#define KVA(x) ((BYTE *)((DWORD_PTR)(x) + kls_delta))

static int kls_on, kls_log = 1, kls_fallback = 1, kls_overlay_on, kls_exe_ok, kls_nrules;
static char kls_ini[MAX_PATH], kls_game_low[MAX_PATH], kls_root[MAX_PATH], kls_root_low[MAX_PATH], kls_overlay[MAX_PATH];
static int kls_game_len, kls_root_len;
static char kls_mount[64];
static CRITICAL_SECTION kls_cs;
static struct {
    char key[96]; int keylen;                 /* "\scenes\locations\f01\", lower case */
    char to[MAX_PATH]; int tolen;             /* "<game>\KLExpansion\Maps\DM03\" */
    char slot[32], map[48];
    LONG hits, misses;
} kls_rule[KLS_RULES];

/* ---------------------------------------------------------------- log: each distinct line once */

static DWORD kls_seen[1024]; static int kls_nseen;

static void kls_note(const char *api, const char *what, const char *from, const char *to)
{
    DWORD h = 2166136261u; const char *p; int i, dup = 0;
    for (p = what; *p; p++) h = (h ^ (BYTE)*p) * 16777619u;
    for (p = from; *p; p++) h = (h ^ (BYTE)(*p >= 'A' && *p <= 'Z' ? *p + 32 : *p)) * 16777619u;
    EnterCriticalSection(&kls_cs);
    for (i = 0; i < kls_nseen; i++) if (kls_seen[i] == h) { dup = 1; break; }
    if (!dup && kls_nseen < 1024) kls_seen[kls_nseen++] = h; else dup = 1;      /* table full: stay quiet */
    LeaveCriticalSection(&kls_cs);
    if (dup) return;
    if (to) klog("expansion: %s %s: %s -> %s", api, what, from, to);
    else klog("expansion: %s %s: %s", api, what, from);
}

/* ---------------------------------------------------------------- path mapping */

static void kls_lower(char *d, const char *s) { for (; (*d = (char)(*s >= 'A' && *s <= 'Z' ? *s + 32 : *s)) != 0; d++, s++) ; }

static int kls_isfile(const char *p)
{   /* GetFileAttributesA of THIS dll's import table, i.e. not the wrapped one */
    DWORD a = GetFileAttributesA(p);
    return a != INVALID_FILE_ATTRIBUTES && !(a & FILE_ATTRIBUTE_DIRECTORY);
}

/* -> 1 and the new path in out[MAX_PATH] when the open must go somewhere else, 0 when it stays.
   Keeps GetLastError() as it found it when it returns 0. */
static int kls_map(const char *in, char *out, const char *api)
{
    char full[MAX_PATH], low[MAX_PATH], *hit; DWORD n, err; int i, wild;
    if (!kls_on || !in || !in[0] || (in[0] == '\\' && in[1] == '\\')) return 0;   /* devices, pipes, UNC */
    err = GetLastError();
    n = GetFullPathNameA(in, MAX_PATH, full, 0);          /* absolute, '/' -> '\', "." and ".." resolved */
    if (!n || n >= MAX_PATH) { SetLastError(err); return 0; }
    kls_lower(low, full);
    if (!strncmp(low, kls_root_low, kls_root_len) && (low[kls_root_len] == '\\' || !low[kls_root_len])) { SetLastError(err); return 0; }   /* already ours */
    wild = strpbrk(full, "*?") != 0;
    for (i = 0; i < kls_nrules; i++) {
        if ((hit = strstr(low, kls_rule[i].key)) == 0) continue;
        {   const char *rest = full + (hit - low) + kls_rule[i].keylen;
            if (kls_rule[i].tolen + strlen(rest) >= MAX_PATH) break;
            memcpy(out, kls_rule[i].to, kls_rule[i].tolen); strcpy(out + kls_rule[i].tolen, rest);
        }
        if (wild || kls_isfile(out)) {                    /* a search pattern goes to the map folder as a whole */
            InterlockedIncrement(&kls_rule[i].hits);
            if (kls_log) kls_note(api, "redirect", full, out);
            SetLastError(err); return 1;
        }
        InterlockedIncrement(&kls_rule[i].misses);
        if (!kls_fallback) { if (kls_log) kls_note(api, "redirect (NOT in the map folder, Fallback=0: the open will fail)", full, out); SetLastError(err); return 1; }
        if (kls_log) kls_note(api, "NOT in the map folder, stock file used", full, out);
        break;
    }
    if (kls_overlay_on && !wild && !strncmp(low, kls_game_low, kls_game_len) && low[kls_game_len] == '\\' &&
        strlen(kls_overlay) + strlen(full + kls_game_len) < MAX_PATH) {
        strcpy(out, kls_overlay); strcat(out, full + kls_game_len);
        if (kls_isfile(out)) { if (kls_log) kls_note(api, "overlay", full, out); SetLastError(err); return 1; }
    }
    if (kls_log >= 2) kls_note(api, "open", full, 0);
    SetLastError(err);
    return 0;
}

/* ---------------------------------------------------------------- the five wrappers */

static HANDLE (WINAPI *kls_real_CreateFileA)(LPCSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
static HANDLE (WINAPI *kls_real_CreateFileW)(LPCWSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
static DWORD (WINAPI *kls_real_GetFileAttributesA)(LPCSTR);
static HANDLE (WINAPI *kls_real_FindFirstFileA)(LPCSTR, LPWIN32_FIND_DATAA);
static void *(__cdecl *kls_real_fopen)(const char *, const char *);

#define KLS_READONLY(acc, disp) ((disp) == OPEN_EXISTING && !((acc) & (GENERIC_WRITE | GENERIC_ALL | FILE_WRITE_DATA | FILE_APPEND_DATA)))

static HANDLE WINAPI kls_CreateFileA(LPCSTR name, DWORD acc, DWORD share, LPSECURITY_ATTRIBUTES sa, DWORD disp, DWORD flags, HANDLE tmpl)
{
    char to[MAX_PATH];
    if (KLS_READONLY(acc, disp) && kls_map(name, to, "CreateFileA")) name = to;
    return kls_real_CreateFileA(name, acc, share, sa, disp, flags, tmpl);
}

static HANDLE WINAPI kls_CreateFileW(LPCWSTR name, DWORD acc, DWORD share, LPSECURITY_ATTRIBUTES sa, DWORD disp, DWORD flags, HANDLE tmpl)
{
    char a[MAX_PATH], to[MAX_PATH]; WCHAR w[MAX_PATH]; BOOL lossy = FALSE; DWORD err = GetLastError();
    if (name && KLS_READONLY(acc, disp) && WideCharToMultiByte(CP_ACP, 0, name, -1, a, MAX_PATH, 0, &lossy) && !lossy &&
        kls_map(a, to, "CreateFileW") && MultiByteToWideChar(CP_ACP, 0, to, -1, w, MAX_PATH)) name = w;
    SetLastError(err);
    return kls_real_CreateFileW(name, acc, share, sa, disp, flags, tmpl);
}

static DWORD WINAPI kls_GetFileAttributesA(LPCSTR name)
{
    char to[MAX_PATH];
    if (kls_map(name, to, "GetFileAttributesA")) name = to;
    return kls_real_GetFileAttributesA(name);
}

static HANDLE WINAPI kls_FindFirstFileA(LPCSTR name, LPWIN32_FIND_DATAA fd)
{
    char to[MAX_PATH];
    if (kls_map(name, to, "FindFirstFileA")) name = to;
    return kls_real_FindFirstFileA(name, fd);
}

static void *__cdecl kls_fopen(const char *name, const char *mode)
{   /* the FILE belongs to the game's C runtime; it is only passed through */
    char to[MAX_PATH];
    if (mode && mode[0] == 'r' && !strchr(mode, '+') && kls_map(name, to, "fopen")) name = to;
    return kls_real_fopen(name, mode);
}

/* Point the exe's import of <fn> (from <dll>, or from any module when dll is 0) at <mine>; the old
   target goes to *real first. -> entries changed. Walks the import directory by name: no address of
   kl2.exe is assumed, so this part also works on another build. */
static int kls_iat(const char *dll, const char *fn, void *mine, void **real)
{
    BYTE *base = (BYTE *)(DWORD_PTR)img_lo; int done = 0;
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)(base + ((IMAGE_DOS_HEADER *)base)->e_lfanew);
    IMAGE_DATA_DIRECTORY *dd = &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
    IMAGE_IMPORT_DESCRIPTOR *d;
    if (!dd->VirtualAddress) return 0;
    for (d = (IMAGE_IMPORT_DESCRIPTOR *)(base + dd->VirtualAddress); d->Name; d++) {
        IMAGE_THUNK_DATA *nm, *at;
        if (!d->OriginalFirstThunk || (dll && _stricmp((char *)base + d->Name, dll))) continue;
        nm = (IMAGE_THUNK_DATA *)(base + d->OriginalFirstThunk); at = (IMAGE_THUNK_DATA *)(base + d->FirstThunk);
        for (; nm->u1.AddressOfData; nm++, at++) {
            MEMORY_BASIC_INFORMATION mbi; DWORD old; void *cur = (void *)(DWORD_PTR)at->u1.Function;
            if (IMAGE_SNAP_BY_ORDINAL(nm->u1.Ordinal) || strcmp((char *)((IMAGE_IMPORT_BY_NAME *)(base + nm->u1.AddressOfData))->Name, fn)) continue;
            if (cur == mine) continue;
            if (!VirtualQuery(cur, &mbi, sizeof mbi) || mbi.Type != MEM_IMAGE || mbi.AllocationBase == (void *)base) {
                klog("expansion: import %s is not resolved yet (%p): left alone", fn, cur); continue;
            }
            if (!VirtualProtect(&at->u1.Function, sizeof(void *), PAGE_READWRITE, &old)) { klog("expansion: import %s: VirtualProtect failed", fn); continue; }
            if (!*real) *real = cur;
            at->u1.Function = (DWORD_PTR)mine;
            VirtualProtect(&at->u1.Function, sizeof(void *), old, &old);
            done++;
        }
    }
    return done;
}

/* ---------------------------------------------------------------- kl2.exe code patches */

static int kls_poke(BYTE *at, const BYTE *expect, int explen, const void *bytes, int len)
{   /* write len bytes, only if the explen bytes there are exactly the expected ones */
    DWORD old;
    if (IsBadReadPtr(at, explen) || memcmp(at, expect, explen)) return 0;
    if (!VirtualProtect(at, len, PAGE_EXECUTE_READWRITE, &old)) return 0;
    memcpy(at, bytes, len);
    VirtualProtect(at, len, old, &old); FlushInstructionCache(GetCurrentProcess(), at, len);
    return 1;
}

/* the nine `push offset "Locations/Fxx/Fxx_Main"` of the level-list constructor 0x835ff0 */
static const struct { DWORD site, str; } kls_push[KLS_FA] = {
    { 0x836016, 0xb75044 }, { 0x836026, 0xb39e28 }, { 0x836036, 0xb326a8 }, { 0x836049, 0xb2c534 }, { 0x83605c, 0xb672a4 },
    { 0x83606f, 0xb19654 }, { 0x836085, 0xb16f70 }, { 0x836098, 0xb872a0 }, { 0x8360ab, 0xb7d4f0 } };
/* `mov byte ptr [esi+4+idx], 0` in the availability reset 0x8468d0 (level list slot 32), DLC slots only */
static const struct { int idx; DWORD site; BYTE b[4]; } kls_lock[3] = {
    { 8, 0x8468ea, { 0xc6, 0x46, 0x0c, 0x00 } }, { 7, 0x8468ee, { 0xc6, 0x46, 0x0b, 0x00 } }, { 4, 0x8468f2, { 0xc6, 0x46, 0x08, 0x00 } } };
static char kls_name[KLS_FA][KLS_NAME];       /* must outlive the process: the constructor reads them later */
static int kls_set[KLS_FA], kls_nset;

static void kls_slots(void)
{   /* [Slots]: re\fa_slots.md section 5, option 1 */
    int i, k; char key[8]; BYTE exp[5], rep[5]; DWORD v;
    for (i = 0; i < KLS_FA; i++) {
        snprintf(key, sizeof key, "F%02d", i + 1);
        if (!GetPrivateProfileStringA("Slots", key, "", kls_name[i], KLS_NAME, kls_ini)) continue;    /* cut to 63 characters */
        exp[0] = rep[0] = 0x68; memcpy(exp + 1, &kls_push[i].str, 4); v = (DWORD)(DWORD_PTR)kls_name[i]; memcpy(rep + 1, &v, 4);
        if (!kls_poke(KVA(kls_push[i].site), exp, 5, rep, 5)) { klog("expansion: [Slots] %s: unexpected bytes at %08lx, skipped", key, kls_push[i].site); kls_name[i][0] = 0; continue; }
        kls_set[i] = 1; kls_nset++;
        if (i == 0) {                         /* the session manager's preset map name is the same F01 literal (0x69981e) */
            if (!kls_poke(KVA(0x69981e), exp, 5, rep, 5)) klog("expansion: [Slots] F01: session default at 0069981e not changed (bytes differ)");
        }
        for (k = 0; k < 3; k++)               /* a renamed DLC slot must not stay locked; a slot that keeps its stock name is never touched */
            if (kls_lock[k].idx == i) {
                BYTE open[4]; memcpy(open, kls_lock[k].b, 4); open[3] = 1;
                if (!kls_poke(KVA(kls_lock[k].site), kls_lock[k].b, 4, open, 4)) klog("expansion: [Slots] %s: lock byte at %08lx not as expected, slot may stay locked", key, kls_lock[k].site);
            }
        klog("expansion: [Slots] %s -> %s", key, kls_name[i]);
    }
}

/* Stub for "MountFirst". The site 0x7f5610 "push 0xb251fc" (5 bytes) becomes "call stub"; on entry
   ecx = file system, edx = its Mount (thiscall, name, flag; ret 8), stack = [return 0x7f5615][1].
   The stub mounts our archive, then leaves the stack as the replaced push would have and returns to
   the stock "call edx". eax is dead there (it held the vtable; the call that follows overwrites it). */
static BYTE *kls_emit_mount(BYTE *p, const char *ours, DWORD stock_name)
{
    DWORD v = (DWORD)(DWORD_PTR)ours;
    *p++ = 0x51; *p++ = 0x52;                             /* push ecx; push edx */
    *p++ = 0x6a; *p++ = 0x01;                             /* push 1            (same flag as Patch01.zip) */
    *p++ = 0x68; memcpy(p, &v, 4); p += 4;                /* push ours */
    *p++ = 0xff; *p++ = 0xd2;                             /* call edx */
    *p++ = 0x5a; *p++ = 0x59;                             /* pop edx; pop ecx */
    *p++ = 0x58;                                          /* pop eax           (return address) */
    *p++ = 0x68; memcpy(p, &stock_name, 4); p += 4;       /* push "Patch01.zip" */
    *p++ = 0xff; *p++ = 0xe0;                             /* jmp eax */
    return p;
}

static void kls_mount_first(void)
{
    static const BYTE exp[7] = { 0x68, 0xfc, 0x51, 0xb2, 0x00, 0xff, 0xd2 };
    BYTE *site = KVA(0x7f5610), *stub, call[5]; DWORD v; char full[MAX_PATH]; size_t n;
    if (!GetPrivateProfileStringA("Expansion", "MountFirst", "", kls_mount, sizeof kls_mount, kls_ini)) return;
    n = strlen(kls_mount);
    if (n < 5 || _stricmp(kls_mount + n - 4, ".zip") || strchr(kls_mount, ':') || kls_mount[0] == '\\' || kls_mount[0] == '/' || strstr(kls_mount, "..")) {
        klog("expansion: MountFirst=%s refused: a name relative to the game folder ending in .zip is needed", kls_mount); return; }
    snprintf(full, sizeof full, "%s\\%s", dir, kls_mount);
    if (!kls_isfile(full)) { klog("expansion: MountFirst: %s does not exist, nothing patched", full); return; }
    stub = (BYTE *)VirtualAlloc(0, 64, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!stub) return;
    kls_emit_mount(stub, kls_mount, 0xb251fc);
    call[0] = 0xe8; v = (DWORD)(stub - (site + 5)); memcpy(call + 1, &v, 4);
    klog("expansion: MountFirst=%s %s", kls_mount, kls_poke(site, exp, 7, call, 5) ? "installed (call at 007f5610; mounted before Patch01.zip at every scene load)" : "NOT installed: bytes at 007f5610 differ");
}

static DWORD WINAPI kls_watch(LPVOID unused)
{   /* logs the level list once it exists and whenever it changes; reads only, except that it keeps a
       RENAMED slot available (insurance against a writer of available[] that was not found) */
    BYTE last[18 + KLS_FA * KLS_NAME], now[sizeof last], m[0x260]; BYTE *mgr; SIZE_T got; int i;
    (void)unused; memset(last, 0, sizeof last);
    for (;;) {
        Sleep(500);
        mgr = *(BYTE **)KVA(KLS_DLCMGR);
        if (!mgr || !ReadProcessMemory(GetCurrentProcess(), mgr, m, sizeof m, &got) || got != sizeof m || *(DWORD *)m != KLS_DLCMGR_VT) continue;
        for (i = 0; i < KLS_FA; i++) if (kls_set[i] && !m[4 + i]) { mgr[4 + i] = 1; m[4 + i] = 1; }
        memcpy(now, m + 4, 18); memcpy(now + 18, m + 0x16, KLS_FA * KLS_NAME);
        if (!memcmp(now, last, sizeof now)) continue;
        memcpy(last, now, sizeof now);
        for (i = 0; i < KLS_FA; i++) { m[0x16 + i * KLS_NAME + KLS_NAME - 1] = 0; klog("expansion: slot %d available=%d present=%d %s", i, m[4 + i], m[0xd + i], (char *)m + 0x16 + i * KLS_NAME); }
    }
}

/* ---------------------------------------------------------------- set-up */

static int kls_plain(const char *s)
{   /* a folder name: letters, digits, '_' and '-' only (no separators, no dots) */
    if (!*s) return 0;
    for (; *s; s++) if (!((*s >= 'a' && *s <= 'z') || (*s >= 'A' && *s <= 'Z') || (*s >= '0' && *s <= '9') || *s == '_' || *s == '-')) return 0;
    return 1;
}

static void kls_compare(const char *slot, const char *to)
{   /* what the map folder holds, and which stock files of the slot have no counterpart */
    char pat[MAX_PATH], p[MAX_PATH]; WIN32_FIND_DATAA fd; HANDLE h; int n = 0;
    snprintf(pat, sizeof pat, "%s*", to);
    if ((h = FindFirstFileA(pat, &fd)) != INVALID_HANDLE_VALUE) {
        do if (!(fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) { klog("expansion:   has %s (%lu bytes)", fd.cFileName, fd.nFileSizeLow); n++; } while (FindNextFileA(h, &fd));
        FindClose(h);
    }
    if (!n) klog("expansion:   the map folder is empty: every open falls through to the stock level");
    snprintf(pat, sizeof pat, "%s\\Scenes\\Locations\\%s\\*", dir, slot);
    if ((h = FindFirstFileA(pat, &fd)) == INVALID_HANDLE_VALUE) return;
    do {
        size_t l = strlen(fd.cFileName);
        if ((fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) || (l > 4 && !_stricmp(fd.cFileName + l - 4, ".hti"))) continue;   /* .hti: the exe never opens it */
        snprintf(p, sizeof p, "%s%s", to, fd.cFileName);
        if (!kls_isfile(p)) klog("expansion:   stock %s has no counterpart: %s", fd.cFileName, kls_fallback ? "the STOCK file will be used" : "the open will fail");
    } while (FindNextFileA(h, &fd));
    FindClose(h);
}

static void kls_rules(void)
{
    char keys[1024], val[64], *k;
    if (!GetPrivateProfileStringA("Redirect", 0, "", keys, sizeof keys, kls_ini)) return;      /* all key names, NUL separated */
    for (k = keys; *k; k += strlen(k) + 1) {
        int r = kls_nrules; DWORD a;
        GetPrivateProfileStringA("Redirect", k, "", val, sizeof val, kls_ini);
        if (r >= KLS_RULES) { klog("expansion: [Redirect] %s ignored: more than %d lines", k, KLS_RULES); continue; }
        if (!kls_plain(k) || !kls_plain(val) || strlen(k) > 31 || strlen(val) > 47) { klog("expansion: [Redirect] %s=%s refused: plain folder names only", k, val); continue; }
        snprintf(kls_rule[r].to, MAX_PATH, "%s\\Maps\\%s\\", kls_root, val);
        a = GetFileAttributesA(kls_rule[r].to);
        if (a == INVALID_FILE_ATTRIBUTES || !(a & FILE_ATTRIBUTE_DIRECTORY)) { klog("expansion: [Redirect] %s=%s: folder %s not found, rule off (stock level stays)", k, val, kls_rule[r].to); continue; }
        kls_rule[r].tolen = (int)strlen(kls_rule[r].to);
        snprintf(kls_rule[r].key, sizeof kls_rule[r].key, "\\scenes\\locations\\%s\\", k); kls_lower(kls_rule[r].key, kls_rule[r].key);
        kls_rule[r].keylen = (int)strlen(kls_rule[r].key);
        snprintf(kls_rule[r].slot, sizeof kls_rule[r].slot, "%s", k); snprintf(kls_rule[r].map, sizeof kls_rule[r].map, "%s", val);
        kls_nrules++;
        klog("expansion: [Redirect] Scenes\\Locations\\%s\\ -> %s", k, kls_rule[r].to);
        kls_compare(k, kls_rule[r].to);
    }
}

static void kls_init(HINSTANCE inst)
{   /* from DllMain, after klhook.c's own set-up; no game code has run yet */
    char root[64]; DWORD a; int n;
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)((BYTE *)(DWORD_PTR)img_lo + ((IMAGE_DOS_HEADER *)(DWORD_PTR)img_lo)->e_lfanew);
    (void)inst;
    snprintf(kls_ini, sizeof kls_ini, "%s\\KLHook.ini", dir);
    if (!GetPrivateProfileIntA("Expansion", "Enable", 0, kls_ini)) return;
    InitializeCriticalSection(&kls_cs);
    kls_log = GetPrivateProfileIntA("Expansion", "Log", 1, kls_ini);
    kls_fallback = GetPrivateProfileIntA("Expansion", "Fallback", 1, kls_ini);
    GetPrivateProfileStringA("Expansion", "Root", "KLExpansion", root, sizeof root, kls_ini);
    if (!kls_plain(root)) { klog("expansion: Root=%s refused: a plain folder name next to kl2.exe is needed", root); return; }
    kls_lower(kls_game_low, dir); kls_game_len = (int)strlen(kls_game_low);
    snprintf(kls_root, sizeof kls_root, "%s\\%s", dir, root); kls_lower(kls_root_low, kls_root); kls_root_len = (int)strlen(kls_root_low);
    snprintf(kls_overlay, sizeof kls_overlay, "%s\\Overlay", kls_root);
    a = GetFileAttributesA(kls_overlay);
    kls_overlay_on = GetPrivateProfileIntA("Expansion", "Overlay", 1, kls_ini) && a != INVALID_FILE_ATTRIBUTES && (a & FILE_ATTRIBUTE_DIRECTORY);
    kls_exe_ok = img_lo == 0x400000 && nt->FileHeader.TimeDateStamp == KLS_TIMESTAMP && nt->OptionalHeader.SizeOfImage == KLS_IMAGESIZE;
    klog("expansion: enabled; root %s; overlay %s; Fallback=%d Log=%d; exe %s", kls_root, kls_overlay_on ? "on" : "off (no Overlay folder, or Overlay=0)",
         kls_fallback, kls_log, kls_exe_ok ? "is kl2.exe build 0490" : "is NOT the known kl2.exe: [Slots] and MountFirst are ignored");
    kls_rules();
    kls_on = 1;
    n  = kls_iat("KERNEL32.dll", "CreateFileA", (void *)kls_CreateFileA, (void **)&kls_real_CreateFileA);
    n += kls_iat("KERNEL32.dll", "CreateFileW", (void *)kls_CreateFileW, (void **)&kls_real_CreateFileW);
    n += kls_iat("KERNEL32.dll", "GetFileAttributesA", (void *)kls_GetFileAttributesA, (void **)&kls_real_GetFileAttributesA);
    n += kls_iat("KERNEL32.dll", "FindFirstFileA", (void *)kls_FindFirstFileA, (void **)&kls_real_FindFirstFileA);
    n += kls_iat(0, "fopen", (void *)kls_fopen, (void **)&kls_real_fopen);
    klog("expansion: %d import(s) of the exe wrapped (CreateFileA %s, CreateFileW %s, GetFileAttributesA %s, FindFirstFileA %s, fopen %s); %d redirect rule(s)",
         n, kls_real_CreateFileA ? "yes" : "NO", kls_real_CreateFileW ? "yes" : "no", kls_real_GetFileAttributesA ? "yes" : "no",
         kls_real_FindFirstFileA ? "yes" : "no", kls_real_fopen ? "yes" : "no", kls_nrules);
    if (!kls_exe_ok) return;
    kls_slots();
    kls_mount_first();
    if (kls_nset || kls_log >= 2) CloseHandle(CreateThread(0, 0, kls_watch, 0, 0, 0));
}

#ifdef KLSLOT_TEST
/* Test harness entry points (never built into the game's DLL). */
__declspec(dllexport) int kls_test_map(const char *in, char *out) { return kls_map(in, out, "test"); }
__declspec(dllexport) int kls_test_patch(void *mapped)
{   /* run the code patches against a copy of kl2.exe mapped anywhere; -> slots renamed */
    kls_delta = (LONG_PTR)((DWORD_PTR)mapped - 0x400000);
    kls_slots(); kls_mount_first();
    return kls_nset;
}
__declspec(dllexport) const char *kls_test_slot_name(int i) { return kls_name[i]; }
__declspec(dllexport) void *kls_test_emit_mount(void *p, const char *ours, DWORD stock) { return kls_emit_mount((BYTE *)p, ours, stock); }
#endif
#endif /* KLSLOT_C */
