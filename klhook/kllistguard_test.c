/*
 * kllistguard_test.c - kllistguard_logic.h and the SEH wrapper kllistguard_seh.h outside the game (32-bit console program, MSVC).
 * Proves: the catch filter takes ONLY an access violation inside the remove function's range; slot 0 verification; the vtable copy length;
 * the heap-candidate rule; the log rate limit; and, for real, that the __fastcall wrapper passes this/n/rec through to a thiscall-style
 * callee, swallows a deliberate access violation raised inside the "guarded range", and lets a fault OUTSIDE the range (and a non-AV) through.
 *
 *   call "...\vcvarsall.bat" x86
 *   cl /nologo /W3 /D_CRT_SECURE_NO_WARNINGS kllistguard_test.c /Fe:kllistguard_test.exe
 *   kllistguard_test.exe        exit code 0 = every check passed
 */
#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>

static int bad, logged;
static void klog(const char *fmt, ...) { va_list ap; va_start(ap, fmt); logged++; printf("    log: "); vprintf(fmt, ap); printf("\n"); va_end(ap); }
#define CHECK(c, ...) do { if (!(c)) { bad++; printf("FAIL: "); printf(__VA_ARGS__); printf("\n"); } } while (0)

#include "kllistguard_seh.h"

/* the fake CListUser slot 0: records its arguments; mode picks what it does */
static void *seen_self; static unsigned seen_n; static void *seen_rec; static volatile int mode;
__declspec(noinline) static void __fastcall fake_inside(void *self, void *edx, unsigned n, void *rec)
{
    (void)edx; seen_self = self; seen_n = n; seen_rec = rec;
    if (mode == 1) *(volatile int *)(DWORD_PTR)0x4f09 = 1;                      /* the real crash: a read/write of a tiny address */
    if (mode == 2) RaiseException(EXCEPTION_INT_DIVIDE_BY_ZERO, 0, 0, 0);
}
__declspec(noinline) static void __fastcall fake_end(void) { }                    /* marks an address after fake_inside */

int main(void)
{
    unsigned vt[8] = { 0x630700, 0x5a9b70, 0x805740, 0xb2e000, 0xb11000, 0x1, 0, 0 }; int r;
    /* ---- logic ---- */
    CHECK(kllg_catch(KLLG_AV, 0x4f8a8e, KLLG_FN_LO, KLLG_FN_HI), "the crash address must be caught");
    CHECK(kllg_catch(KLLG_AV, 0x4f8a60, KLLG_FN_LO, KLLG_FN_HI), "first byte caught");
    CHECK(kllg_catch(KLLG_AV, 0x4f8b48, KLLG_FN_LO, KLLG_FN_HI), "last byte (ret 0xc) caught");
    CHECK(!kllg_catch(KLLG_AV, 0x4f8b49, KLLG_FN_LO, KLLG_FN_HI), "padding after the function is out");
    CHECK(!kllg_catch(KLLG_AV, 0x4f8b50, KLLG_FN_LO, KLLG_FN_HI), "the next function is out");
    CHECK(!kllg_catch(KLLG_AV, 0x4f8a5f, KLLG_FN_LO, KLLG_FN_HI), "byte before is out");
    CHECK(!kllg_catch(0xc0000094u, 0x4f8a8e, KLLG_FN_LO, KLLG_FN_HI), "a divide by zero in range is not caught");
    CHECK(!kllg_catch(KLLG_AV, 0x630720, KLLG_FN_LO, KLLG_FN_HI), "an AV in 0x630700 itself is not caught");
    CHECK(kllg_slot_ok(0x630700) && !kllg_slot_ok(0) && !kllg_slot_ok(0x630701), "slot verify is exact");
    r = kllg_vt_len(vt, 8, 0x401000, 0xb11000); CHECK(r == 3, "vt len stops at the first non-code entry (got %d)", r);
    r = kllg_vt_len(vt, 2, 0x401000, 0xb11000); CHECK(r == 2, "vt len honours max (got %d)", r);
    CHECK(kllg_cand_ok(0x2000000, KLLG_VT, 0x3000000), "a normal heap object is a candidate");
    CHECK(!kllg_cand_ok(0x2000002, KLLG_VT, 0x3000000), "unaligned is not");
    CHECK(!kllg_cand_ok(0x2000000, KLLG_VT, 0), "null table pointer is not");
    CHECK(!kllg_cand_ok(0x2000000, 0x1234, 0x3000000), "wrong vptr is not");
    CHECK(kllg_log_due(1, 100, 0, 10000) && !kllg_log_due(2, 5000, 100, 10000) && kllg_log_due(2, 10200, 100, 10000), "log rate limit");
    CHECK(kllg_log_due(2, 5, 4294967000u, 10000) == 0, "tick wrap: now 5, last 4294967000 is a 301 ms gap, not due");
    CHECK(kllg_next_delay(0) == 2000 && kllg_next_delay(3) == 15000 && kllg_next_delay(4) == 60000u && kllg_next_delay(-1) == 60000u, "scan schedule");

    /* ---- the real wrapper ---- */
    kllg_orig = (KLLG_FN)fake_inside; kllg_log = 1;
    kllg_lo = (unsigned)(DWORD_PTR)fake_inside; kllg_hi = kllg_lo + 0x200;        /* the fake function's own bytes */
    mode = 0;
    kllg_wrap((void *)0x1111, (void *)0x9999, 7, (void *)0x2222);
    CHECK(seen_self == (void *)0x1111 && seen_n == 7 && seen_rec == (void *)0x2222, "arguments must reach the original (this %p n %u rec %p)", seen_self, seen_n, seen_rec);
    CHECK(kllg_hits == 0 && kllg_calls == 1, "a clean call is not a catch");
    mode = 1;
    kllg_wrap((void *)0x3333, 0, 9, (void *)0x4444);
    CHECK(kllg_hits == 1 && logged == 1, "the in-range access violation must be swallowed and logged once (hits %ld logs %d)", (long)kllg_hits, logged);
    kllg_wrap((void *)0x3333, 0, 10, (void *)0x4444);
    CHECK(kllg_hits == 2 && logged == 1, "second catch inside the gap: counted, not logged again (hits %ld logs %d)", (long)kllg_hits, logged);
    mode = 0; kllg_wrap((void *)0x5555, 0, 11, (void *)0x6666);
    CHECK(seen_self == (void *)0x5555, "the wrapper still works after a catch (stack/regs sane)");
    /* a fault OUTSIDE the range must pass through: catch it with an outer __try */
    kllg_lo = 0x4f8a60; kllg_hi = 0x4f8b49; mode = 1; r = 0;
    __try { kllg_wrap((void *)1, 0, 1, (void *)1); } __except (EXCEPTION_EXECUTE_HANDLER) { r = 1; }
    CHECK(r == 1 && kllg_hits == 2, "an AV outside the range must reach the outer handler and not count");
    kllg_lo = (unsigned)(DWORD_PTR)fake_inside; kllg_hi = kllg_lo + 0x200; mode = 2; r = 0;
    __try { kllg_wrap((void *)1, 0, 1, (void *)1); } __except (EXCEPTION_EXECUTE_HANDLER) { r = 1; }
    CHECK(r == 1 && kllg_hits == 2, "a non-AV must reach the outer handler");

    printf(bad ? "kllistguard_test: %d FAIL\n" : "kllistguard_test: all passed\n", bad);
    return bad ? 1 : 0;
}
