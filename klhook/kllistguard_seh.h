/* kllistguard_seh.h - the SEH wrapper of [Crash] ListUserGuard (MSVC, 32-bit). Included by kllistguard.c (inside klhook.c) and by
 * kllistguard_test.c (which stubs klog and sets kllg_lo / kllg_hi to a fake faulting function). Needs <windows.h>, klog(), kllistguard_logic.h.
 *
 * Calling convention: CListUser slot 0 is thiscall(this=ecx, n, rec) with `ret 8`. A __fastcall(ecx, edx, a, b) function with two stack words
 * and a callee that pops 8 has exactly the same register/stack contract (edx is ignored by the real function), so the wrapper is plain C and the
 * original is called through a __fastcall-typed pointer with a dummy edx. */
#ifndef KLLISTGUARD_SEH_H
#define KLLISTGUARD_SEH_H
#include "kllistguard_logic.h"
#include "kllistguard_port.h"

typedef void (__fastcall *KLLG_FN)(void *self, void *edx, unsigned n, void *rec);
static KLLG_FN kllg_orig;                      /* 0x630700 */
static unsigned kllg_lo = KLLG_FN_LO, kllg_hi = KLLG_FN_HI;   /* the test narrows these to its fake function */
static volatile LONG kllg_hits;                /* faults swallowed, all rounds */
static volatile LONG kllg_calls;               /* wrapper calls (the test proves the wrapper really ran) */
static volatile LONG kllg_in;                  /* > 0 while the guarded call runs: veh() only stays quiet then (an unguarded fault keeps its CRASH line + dump) */
static unsigned kllg_last_log;
static int kllg_log;
static int kllg_mode = 1;                      /* [Crash] ListUserGuard: 1 = run the original 0x630700 under a catch, 2 = the C port kllg_port (key-0 skip, no half-done update) */
static KLLG_HELPERS kllg_helpers;              /* mode 2: the exe's helper functions (set by kllg_init, or by the test) */
static volatile LONG kllg_skips;               /* mode 2: key-0 records skipped, all rounds */
static unsigned kllg_last_skiplog;

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

static void kllg_onskip(unsigned site, unsigned idx, unsigned key)    /* mode 2: a key-0 record was not given to the hash helpers */
{
    LONG h = InterlockedIncrement(&kllg_skips); DWORD now = GetTickCount();
    (void)key;
    if (kllg_log && kllg_log_due((int)h, now, kllg_last_skiplog, 10000)) {
        kllg_last_skiplog = now;
        klog("listguard: key-0 record skipped idx %u (site %u, %ld skipped so far)", idx, site, (long)h);
    }
}

static int kllg_on;
static int kllg_veh_skip(EXCEPTION_POINTERS *ep)   /* veh(): 1 = this is the guarded fault, let the wrapper's __except have it, no CRASH line, no dump */
{
    EXCEPTION_RECORD *r = ep->ExceptionRecord;
    return kllg_on && kllg_in > 0 && kllg_catch((unsigned)r->ExceptionCode, (unsigned)(DWORD_PTR)r->ExceptionAddress, kllg_lo, kllg_hi);
}

static void __fastcall kllg_wrap(void *self, void *edx, unsigned n, void *rec)
{
    InterlockedIncrement(&kllg_calls);
    InterlockedIncrement(&kllg_in);
    __try {
        __try { if (kllg_mode == 2) kllg_port(&kllg_helpers, self, n, rec); else kllg_orig(self, edx, n, rec); }
        __except (kllg_filter(GetExceptionInformation())) { kllg_caught(self, n); }
    } __finally { InterlockedDecrement(&kllg_in); }       /* also when a fault we do not catch unwinds through */
}
#endif
