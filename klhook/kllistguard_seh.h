/* kllistguard_seh.h - the SEH wrapper of [Crash] ListUserGuard (MSVC, 32-bit). Included by kllistguard.c (inside klhook.c) and by
 * kllistguard_test.c (which stubs klog and sets kllg_lo / kllg_hi to a fake faulting function). Needs <windows.h>, klog(), kllistguard_logic.h.
 *
 * Calling convention: CListUser slot 0 is thiscall(this=ecx, n, rec) with `ret 8`. A __fastcall(ecx, edx, a, b) function with two stack words
 * and a callee that pops 8 has exactly the same register/stack contract (edx is ignored by the real function), so the wrapper is plain C and the
 * original is called through a __fastcall-typed pointer with a dummy edx. */
#ifndef KLLISTGUARD_SEH_H
#define KLLISTGUARD_SEH_H
#include "kllistguard_logic.h"

typedef void (__fastcall *KLLG_FN)(void *self, void *edx, unsigned n, void *rec);
static KLLG_FN kllg_orig;                      /* 0x630700 */
static unsigned kllg_lo = KLLG_FN_LO, kllg_hi = KLLG_FN_HI;   /* the test narrows these to its fake function */
static volatile LONG kllg_hits;                /* faults swallowed, all rounds */
static volatile LONG kllg_calls;               /* wrapper calls (the test proves the wrapper really ran) */
static unsigned kllg_last_log;
static int kllg_log;

static int kllg_filter(EXCEPTION_POINTERS *ep)
{
    EXCEPTION_RECORD *r = ep->ExceptionRecord;
    return kllg_catch((unsigned)r->ExceptionCode, (unsigned)(DWORD_PTR)r->ExceptionAddress, kllg_lo, kllg_hi) ? EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH;
}

static void kllg_caught(void *self, unsigned n)
{
    LONG h = InterlockedIncrement(&kllg_hits); DWORD now = GetTickCount();
    (void)self;
    if (kllg_log && kllg_log_due((int)h, now, kllg_last_log, 10000)) {
        kllg_last_log = now;
        klog("listguard: key-0 record skipped, one list update dropped (n=%u, %ld caught so far)", n, (long)h);
    }
}

static void __fastcall kllg_wrap(void *self, void *edx, unsigned n, void *rec)
{
    InterlockedIncrement(&kllg_calls);
    __try { kllg_orig(self, edx, n, rec); }
    __except (kllg_filter(GetExceptionInformation())) { kllg_caught(self, n); }
}
#endif
