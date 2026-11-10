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

/* ---- a fake world for the C port (kllistguard_port.h): records are 0x80-byte blobs in one array (address order = index order), the "table" is a
   list of (key, rec) pairs, and every helper that gets key 0 counts a FAULT (the real ones fault at 0x4f8a8e / 0x5a4b06) ---- */
static unsigned char pool[16][0x80];
static unsigned fw_tkey[64], fw_trec[64]; static int fw_n;
static unsigned fw_A[16], fw_B[32], fw_C[32]; static unsigned char fw_self[0x60];
static int fw_fault, fw_add_cap, fw_rem_calls, fw_rem2_calls; static unsigned fw_remlog[64][2]; static int fw_nremlog;
static unsigned fw_skip_site[16], fw_skip_idx[16]; static int fw_nskip;
#define RECP(i) ((unsigned)(DWORD_PTR)pool[i])
#define SETKEY(i, k) (*(unsigned *)(pool[i] + 0x54) = ((k) & 0xffffffu) | 0xab000000u)     /* the top byte is not part of the key */
#define FLAGGED(i) ((*(unsigned *)(pool[i] + 0x3c) & 0x1000000u) != 0)
static int fw_has(unsigned k, unsigned r) { int i; for (i = 0; i < fw_n; i++) if (fw_tkey[i] == k && fw_trec[i] == r) return 1; return 0; }
static void fw_put(unsigned k, unsigned r) { fw_tkey[fw_n] = k; fw_trec[fw_n] = r; fw_n++; }
static void fw_sort(unsigned *a, unsigned lo, unsigned hi) { unsigned i, j, t; for (i = lo + 1; i <= hi; i++) for (j = i; j > lo && a[j - 1] > a[j]; j--) { t = a[j]; a[j] = a[j - 1]; a[j - 1] = t; } }
static unsigned __fastcall fw_range(void *self, void *edx, unsigned *out, unsigned key)
{   /* all recs of key: first half ascending, second half DESCENDING (the port has to sort it); returns (cnt << 16) | start like 0x8176f0 */
    int i, m = 0, start, a, b; unsigned t; (void)self; (void)edx;
    if (key == 0) fw_fault++;
    for (i = 0; i < fw_n; i++) if (fw_tkey[i] == key) out[m++] = fw_trec[i];
    start = m / 2; if (start > 1) fw_sort(out, 0, start - 1);
    fw_sort(out, start, m ? m - 1 : 0); a = start; b = m - 1; while (a < b) { t = out[a]; out[a] = out[b]; out[b] = t; a++; b--; }
    return ((unsigned)(m - start) << 16) | (unsigned)start;
}
static void fw_merge(unsigned *dst, unsigned *a, unsigned na, unsigned *b, unsigned nb)
{ unsigned i = 0, j = 0, k = 0; while (i < na || j < nb) dst[k++] = (j >= nb || (i < na && a[i] <= b[j])) ? a[i++] : b[j++]; }
static unsigned __fastcall fw_add(void *self, void *edx, unsigned key, unsigned *recs, unsigned count)
{ unsigned i; (void)self; (void)edx; if (key == 0) { fw_fault++; return 0; } for (i = 0; i < count && (int)i < fw_add_cap; i++) fw_put(key, recs[i]); return i; }
static unsigned __fastcall fw_rem(void *self, void *edx, unsigned key, void *rec, unsigned one)
{
    int i; (void)self; (void)edx; (void)one; fw_rem_calls++;
    if (key == 0) { fw_fault++; return 0; }
    if (fw_nremlog < 64) { fw_remlog[fw_nremlog][0] = key; fw_remlog[fw_nremlog][1] = (unsigned)(DWORD_PTR)rec; fw_nremlog++; }
    for (i = 0; i < fw_n; i++) if (fw_tkey[i] == key && fw_trec[i] == (unsigned)(DWORD_PTR)rec) { fw_tkey[i] = fw_tkey[fw_n - 1]; fw_trec[i] = fw_trec[fw_n - 1]; fw_n--; return 1; }
    return 0;
}
static unsigned __fastcall fw_rem2(void *self, void *edx, unsigned key, void *rec, unsigned one) { (void)self; (void)edx; (void)rec; (void)one; if (key == 0) fw_fault++; fw_rem2_calls++; return 1; }
static void fw_onskip(unsigned site, unsigned idx, unsigned key) { kllg_onskip(site, idx, key); if (fw_nskip < 16) { fw_skip_site[fw_nskip] = site; fw_skip_idx[fw_nskip] = idx; } fw_nskip++; }
static int fw_removed(unsigned k, int ri) { int i; for (i = 0; i < fw_nremlog; i++) if (fw_remlog[i][0] == k && fw_remlog[i][1] == RECP(ri)) return 1; return 0; }
static void fw_reset(int cap)
{
    int i; memset(pool, 0, sizeof pool); fw_n = 0; fw_fault = fw_rem_calls = fw_rem2_calls = fw_nremlog = fw_nskip = 0; fw_add_cap = cap;
    memset(fw_self, 0, sizeof fw_self); memset(fw_A, 0, sizeof fw_A);
    *(unsigned **)(fw_self + KLLG_O_A) = fw_A; *(unsigned **)(fw_self + KLLG_O_B) = fw_B; *(unsigned **)(fw_self + KLLG_O_C) = fw_C;
    for (i = 0; i < 16; i++) SETKEY(i, 100 + i);                                      /* every record: key 100 + index, unless a test sets it */
    kllg_helpers.sort = fw_sort; kllg_helpers.range = fw_range; kllg_helpers.merge = fw_merge; kllg_helpers.add = fw_add;
    kllg_helpers.rem = fw_rem; kllg_helpers.rem2 = fw_rem2; kllg_helpers.onskip = fw_onskip;
}

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
    CHECK(kllg_next_delay(0) == 2000 && kllg_next_delay(3) == 15000 && kllg_next_delay(4) == 10000u && kllg_next_delay(-1) == 10000u, "scan schedule");

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
    CHECK(kllg_in == 0, "the inside-wrapper count is back to 0 after clean, caught and passed-through calls (%ld)", (long)kllg_in);
    kllg_on = 1; { EXCEPTION_RECORD er = {0}; EXCEPTION_POINTERS ep = {&er, 0}; er.ExceptionCode = KLLG_AV; er.ExceptionAddress = (void *)(DWORD_PTR)kllg_lo;
        CHECK(!kllg_veh_skip(&ep), "veh() must not stay quiet for an in-range AV outside the wrapper (unguarded crash keeps its log + dump)");
        kllg_in = 1; CHECK(kllg_veh_skip(&ep), "inside the wrapper the in-range AV is skipped"); kllg_in = 0; }

    /* ---- the C port (ListUserGuard=2) ---- */
    CHECK(kllg_mode_of(0) == 0 && kllg_mode_of(1) == 1 && kllg_mode_of(2) == 2 && kllg_mode_of(7) == 2 && kllg_mode_of(-1) == 0, "mode values");
    for (r = 0; r < 7; r++) CHECK(kllg_helper_ids[r].va >= 0x401000 && kllg_helper_ids[r].va < 0xb11000 && kllg_helper_ids[r].dw != 0, "helper id table entry %d", r);
    {   /* scenario 1: a normal update, no dead record. argrec R0 (key 5), old list under key 5 = R1 R3 R4, new set A = R6 R3 (R6 new, R1 R4 left) */
        fw_reset(99); SETKEY(0, 5);
        fw_put(5, RECP(1)); fw_put(5, RECP(3)); fw_put(5, RECP(4)); fw_A[0] = RECP(6); fw_A[1] = RECP(3);                  /* A unsorted on purpose */
        kllg_mode = 2; kllg_skips = 0; kllg_wrap(fw_self, 0, 2, pool[0]);
        CHECK(fw_fault == 0, "scenario 1: no helper gets key 0");
        CHECK(fw_removed(101, 0) && fw_removed(5, 1) && fw_removed(104, 0) && fw_removed(5, 4), "scenario 1: R1 and R4 left the set (both directions removed)");
        CHECK(!fw_removed(103, 0) && !fw_removed(5, 3), "scenario 1: R3 stays");
        CHECK(fw_has(5, RECP(3)) && fw_has(5, RECP(6)) && !fw_has(5, RECP(1)) && !fw_has(5, RECP(4)) && fw_has(106, RECP(0)) && fw_n == 3, "scenario 1: final table = {5:R3, 5:R6, 106:R0} (n %d)", fw_n);
        CHECK(FLAGGED(0) && FLAGGED(6) && FLAGGED(1), "scenario 1: flags set on argrec, a new record and a C record");
        CHECK(fw_nskip == 0 && kllg_skips == 0, "scenario 1: nothing skipped");
    }
    {   /* scenario 2 (the crash): a key-0 record in the MIDDLE of the old list; later records must still be processed */
        fw_reset(99); SETKEY(0, 5); SETKEY(2, 0);                           /* R2 = released, key 0 */
        fw_put(5, RECP(1)); fw_put(5, RECP(2)); fw_put(5, RECP(3)); fw_put(5, RECP(4)); fw_A[0] = RECP(3); fw_A[1] = RECP(5);
        kllg_mode = 2; kllg_skips = 0; kllg_wrap(fw_self, 0, 2, pool[0]);
        CHECK(fw_fault == 0, "scenario 2: no helper got key 0 (it would have faulted) - %d faults", fw_fault);
        CHECK(fw_nskip == 1 && fw_skip_site[0] == KLLG_SITE_LOOP1 && fw_skip_idx[0] == 1 && kllg_skips == 1, "scenario 2: exactly the key-0 record skipped, at C index 1 (skips %d idx %u)", fw_nskip, fw_skip_idx[0]);
        CHECK(fw_removed(101, 0) && fw_removed(5, 1), "scenario 2: the record BEFORE the dead one is processed");
        CHECK(fw_removed(5, 2), "scenario 2: the dead record is still dropped from the list of argkey (stale entry cleaned)");
        CHECK(fw_removed(104, 0) && fw_removed(5, 4), "scenario 2: the record AFTER the dead one is still processed (later records not left unprocessed)");
        CHECK(fw_has(5, RECP(3)) && fw_has(5, RECP(5)) && fw_n == 3 && fw_has(105, RECP(0)), "scenario 2: final table = {5:R3, 5:R5, 105:R0} (n %d)", fw_n);
        CHECK(FLAGGED(4) && FLAGGED(0) && FLAGGED(3), "scenario 2: flags set after the dead record too");
    }
    {   /* scenario 2b: key-0 records first and last in address order, empty A */
        fw_reset(99); SETKEY(0, 5); SETKEY(1, 0); SETKEY(9, 0);
        fw_put(5, RECP(1)); fw_put(5, RECP(9)); kllg_mode = 2; kllg_wrap(fw_self, 0, 0, pool[0]);
        CHECK(fw_fault == 0 && fw_nskip == 2 && fw_n == 0, "scenario 2b: two dead records skipped, both stale entries dropped, no fault (skips %d, table %d)", fw_nskip, fw_n);
    }
    {   /* scenario 3: the fake really flags a key-0 call (the test is not vacuous) */
        fw_reset(99); fw_rem(0, 0, 0, pool[1], 1); CHECK(fw_fault == 1, "the fake helper counts a key-0 call as a fault");
    }
    {   /* scenario 4: 0x5a4ad0 takes only part of the batch -> roll back what went in, no loop 3 */
        fw_reset(1); SETKEY(0, 5); fw_A[0] = RECP(5); fw_A[1] = RECP(6);
        kllg_mode = 2; kllg_wrap(fw_self, 0, 2, pool[0]);
        CHECK(fw_n == 0 && fw_fault == 0, "scenario 4: the one record that fitted was rolled back (table %d)", fw_n);
        CHECK(fw_removed(5, 5), "scenario 4: rollback removed A[0] from argkey");
    }
    {   /* scenario 5: the update's own record is dead (key 0): no table helper runs, flag set, no fault */
        fw_reset(99); SETKEY(0, 0); fw_A[0] = RECP(3); fw_put(103, RECP(0));
        kllg_mode = 2; kllg_wrap(fw_self, 0, 1, pool[0]);
        CHECK(fw_fault == 0 && fw_rem_calls == 0 && fw_n == 1 && fw_nskip == 1 && fw_skip_site[0] == KLLG_SITE_SELF, "scenario 5: dead argrec -> only the self skip (faults %d, rem %d)", fw_fault, fw_rem_calls);
        CHECK(FLAGGED(0), "scenario 5: flag(rec) still set");
    }
    {   /* scenario 6: a NEW record with key 0 in A (the caller filters these, but the port must not fault on one) */
        fw_reset(99); SETKEY(0, 5); SETKEY(6, 0); fw_A[0] = RECP(5); fw_A[1] = RECP(6);
        kllg_mode = 2; kllg_wrap(fw_self, 0, 2, pool[0]);
        CHECK(fw_fault == 0 && fw_nskip == 1 && fw_skip_site[0] == KLLG_SITE_LOOP3, "scenario 6: key-0 new record skipped without a fault (faults %d, skips %d)", fw_fault, fw_nskip);
        CHECK(fw_has(105, RECP(0)), "scenario 6: the live new record R5 still got its entry");
    }
    CHECK(kllg_in == 0, "inside count back to 0 after port calls (%ld)", (long)kllg_in);
    kllg_mode = 1;

    printf(bad ? "kllistguard_test: %d FAIL\n" : "kllistguard_test: all passed\n", bad);
    return bad ? 1 : 0;
}
