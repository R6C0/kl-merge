/*
 * KLHook - diagnostic proxy for Kane & Lynch 2: Dog Days (kl2.exe, 32-bit).
 *
 * Drop dinput8.dll + KLHook.ini next to kl2.exe. The game loads it instead of the system
 * dinput8.dll; every call is forwarded to the real one. Nothing in the game is patched.
 *
 * What it adds:
 *  - KLHook.log: every engine assert (int3 inside kl2.exe) and crash, with registers and the
 *    stack's kl2.exe return addresses.
 *  - KLHook_N.dmp: a minidump that includes the memory registers/stack point at (the game's
 *    own dumps only hold the stack), for the first few distinct problems.
 *  - ContinueAsserts=1: step over engine asserts so one run reports several problems.
 *
 * Delete dinput8.dll to remove it.
 */
#include <windows.h>
#include <stdio.h>

typedef HRESULT (WINAPI *DI8Create)(HINSTANCE, DWORD, REFIID, LPVOID *, LPUNKNOWN);
static DI8Create real_create;
static char dir[MAX_PATH];
static int continue_asserts = 1, max_dumps = 4, dumps = 0, max_asserts = 200;
static DWORD seen[256]; static int nseen;
static CRITICAL_SECTION cs;
static DWORD img_lo = 0x400000, img_hi = 0x400000;

static void klog(const char *fmt, ...)
{
    char path[MAX_PATH]; snprintf(path, sizeof path, "%s\\KLHook.log", dir);
    FILE *f = fopen(path, "a"); if (!f) return;
    SYSTEMTIME t; GetLocalTime(&t);
    fprintf(f, "%02d:%02d:%02d.%03d ", t.wHour, t.wMinute, t.wSecond, t.wMilliseconds);
    va_list a; va_start(a, fmt); vfprintf(f, fmt, a); va_end(a);
    fputc('\n', f); fclose(f);
}

typedef BOOL (WINAPI *MDWD)(HANDLE, DWORD, HANDLE, int, void *, void *, void *);
typedef struct { DWORD tid; EXCEPTION_POINTERS *ep; BOOL client; } MEI;

static void write_dump(EXCEPTION_POINTERS *ep, const char *why)
{
    if (dumps >= max_dumps) return;
    HMODULE h = LoadLibraryA("dbghelp.dll"); if (!h) return;
    MDWD w = (MDWD)GetProcAddress(h, "MiniDumpWriteDump"); if (!w) return;
    char path[MAX_PATH]; snprintf(path, sizeof path, "%s\\KLHook_%d.dmp", dir, ++dumps);
    HANDLE f = CreateFileA(path, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, 0, 0);
    if (f == INVALID_HANDLE_VALUE) return;
    MEI mei = { GetCurrentThreadId(), ep, FALSE };
    /* Normal | DataSegs | IndirectlyReferencedMemory | ThreadInfo */
    int type = 0x0 | 0x1 | 0x40 | 0x1000;
    w(GetCurrentProcess(), GetCurrentProcessId(), f, type, &mei, 0, 0);
    CloseHandle(f);
    klog("  dump written: KLHook_%d.dmp (%s)", dumps, why);
}

static void log_context(CONTEXT *c)
{
    klog("  eax=%08lx ebx=%08lx ecx=%08lx edx=%08lx esi=%08lx edi=%08lx ebp=%08lx esp=%08lx",
         c->Eax, c->Ebx, c->Ecx, c->Edx, c->Esi, c->Edi, c->Ebp, c->Esp);
    char line[512]; int n = 0, k = 0;
    DWORD *sp = (DWORD *)c->Esp;
    n += snprintf(line + n, sizeof line - n, "  callers:");
    for (int i = 0; i < 2048 && k < 16; i++) {
        DWORD v;
        if (IsBadReadPtr(sp + i, 4)) break;
        v = sp[i];
        if (v > img_lo && v < img_hi && !IsBadReadPtr((void *)(v - 5), 5) &&
            (((BYTE *)v)[-5] == 0xE8 || ((BYTE *)v)[-2] == 0xFF || ((BYTE *)v)[-3] == 0xFF || ((BYTE *)v)[-6] == 0xFF)) {
            n += snprintf(line + n, sizeof line - n, " %08lx", v); k++;
        }
    }
    klog("%s", line);
}

static LONG CALLBACK veh(EXCEPTION_POINTERS *ep)
{
    DWORD code = ep->ExceptionRecord->ExceptionCode;
    DWORD at = (DWORD)ep->ExceptionRecord->ExceptionAddress;
    if (at < img_lo || at >= img_hi) return EXCEPTION_CONTINUE_SEARCH;
    if (code != EXCEPTION_BREAKPOINT && code != EXCEPTION_ACCESS_VIOLATION &&
        code != EXCEPTION_ILLEGAL_INSTRUCTION && code != EXCEPTION_INT_DIVIDE_BY_ZERO)
        return EXCEPTION_CONTINUE_SEARCH;
    EnterCriticalSection(&cs);
    int first = 1;
    for (int i = 0; i < nseen; i++) if (seen[i] == at) first = 0;
    if (first && nseen < 256) seen[nseen++] = at;
    static int total;
    total++;
    if (code == EXCEPTION_BREAKPOINT) {
        if (first || total < 20) {
            klog("ASSERT at kl2.exe+%06lx (%08lx)%s", at - img_lo, at, first ? "" : " (again)");
            log_context(ep->ContextRecord);
            if (first) write_dump(ep, "assert");
        }
        if (continue_asserts && total < max_asserts && ((BYTE *)at)[0] == 0xCC) {
            ep->ContextRecord->Eip += 1;          /* step over the int3 */
            LeaveCriticalSection(&cs);
            return EXCEPTION_CONTINUE_EXECUTION;
        }
        klog("  not continuing (limit reached or disabled)");
    } else {
        klog("CRASH %08lx at kl2.exe+%06lx (%08lx)", code, at - img_lo, at);
        if (code == EXCEPTION_ACCESS_VIOLATION)
            klog("  %s address %08lx", ep->ExceptionRecord->ExceptionInformation[0] ? "writing" : "reading",
                 (DWORD)ep->ExceptionRecord->ExceptionInformation[1]);
        log_context(ep->ContextRecord);
        dumps = dumps < max_dumps ? dumps : max_dumps - 1;   /* always dump the crash itself */
        write_dump(ep, "crash");
    }
    LeaveCriticalSection(&cs);
    return EXCEPTION_CONTINUE_SEARCH;
}

__declspec(dllexport) HRESULT WINAPI DirectInput8Create(HINSTANCE h, DWORD v, REFIID r, LPVOID *o, LPUNKNOWN u)
{
    if (!real_create) {
        char p[MAX_PATH]; GetSystemDirectoryA(p, MAX_PATH); strcat(p, "\\dinput8.dll");
        HMODULE m = LoadLibraryA(p);
        real_create = m ? (DI8Create)GetProcAddress(m, "DirectInput8Create") : 0;
        if (!real_create) return E_FAIL;
    }
    return real_create(h, v, r, o, u);
}

BOOL WINAPI DllMain(HINSTANCE inst, DWORD reason, LPVOID res)
{
    if (reason != DLL_PROCESS_ATTACH) return TRUE;
    DisableThreadLibraryCalls(inst);
    InitializeCriticalSection(&cs);
    GetModuleFileNameA(inst, dir, MAX_PATH);
    char *s = strrchr(dir, '\\'); if (s) *s = 0;
    char ini[MAX_PATH]; snprintf(ini, sizeof ini, "%s\\KLHook.ini", dir);
    continue_asserts = GetPrivateProfileIntA("KLHook", "ContinueAsserts", 1, ini);
    max_dumps = GetPrivateProfileIntA("KLHook", "MaxDumps", 4, ini);
    max_asserts = GetPrivateProfileIntA("KLHook", "MaxAsserts", 200, ini);
    HMODULE exe = GetModuleHandleA(NULL);
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)((BYTE *)exe + ((IMAGE_DOS_HEADER *)exe)->e_lfanew);
    img_lo = (DWORD)exe; img_hi = img_lo + nt->OptionalHeader.SizeOfImage;
    AddVectoredExceptionHandler(1, veh);
    klog("==== KLHook loaded (ContinueAsserts=%d MaxDumps=%d) kl2.exe %08lx-%08lx", continue_asserts, max_dumps, img_lo, img_hi);
    return TRUE;
}
