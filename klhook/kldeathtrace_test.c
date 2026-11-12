/* kldeathtrace_test.c - off-game checks of kldeathtrace_logic.h. Build: cl /nologo /W3 kldeathtrace_test.c */
#include <stdio.h>
#include "kldeathtrace_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

static int fake_rd(unsigned long ra, unsigned char *six, void *ctx)
{   /* the code bytes before an address: a call rel32 for ra 0x500000.., call eax for 0x600000.., junk else, unreadable for 0x700000 */
    (void)ctx; memset(six, 0x90, 6);
    if (ra == 0x700000ul) return 0;
    if (ra >= 0x500000ul && ra < 0x500100ul) six[1] = 0xe8;
    if (ra >= 0x600000ul && ra < 0x600100ul) { six[4] = 0xff; six[5] = 0xd0; }
    return 1;
}

int main(void)
{
    long n = 0; int i; kdt_ring r; kdt_samp s; unsigned long w[8], out[8];
    /* line cap */
    CHECK(kdt_take(&n, 2) == 1 && kdt_take(&n, 2) == 1 && kdt_take(&n, 2) == 0 && n == 2);
    n = 0; CHECK(kdt_take(&n, 0) == 0 && n == 0);
    /* period, wrap-safe */
    CHECK(kdt_due(1000, 900, 100) == 1 && kdt_due(999, 900, 100) == 0);
    CHECK(kdt_due(50, 0xfffffff0ul, 40) == 1 && kdt_due(20, 0xfffffff0ul, 40) == 0);
    /* ring: newest first, wraps at KDT_RING */
    kdt_ring_clear(&r); CHECK(kdt_ring_back(&r, 0) == 0);
    memset(&s, 0, sizeof s);
    for (i = 1; i <= KDT_RING + 5; i++) { s.t = (unsigned long)i; kdt_ring_push(&r, &s); }
    CHECK(r.n == KDT_RING && kdt_ring_back(&r, 0)->t == (unsigned long)(KDT_RING + 5) && kdt_ring_back(&r, KDT_RING - 1)->t == 6);
    CHECK(kdt_ring_back(&r, KDT_RING) == 0 && kdt_ring_back(&r, -1) == 0);
    kdt_ring_clear(&r); s.t = 7; kdt_ring_push(&r, &s); CHECK(r.n == 1 && kdt_ring_back(&r, 0)->t == 7 && kdt_ring_back(&r, 1) == 0);
    /* call forms: bytes END at the return address */
    { unsigned char e8[6] = { 0x90, 0xe8, 1, 2, 3, 4 };               CHECK(kdt_is_call_ret(e8)); }
    { unsigned char c1[6] = { 0x90, 0x90, 0x90, 0x90, 0xff, 0xd0 };   CHECK(kdt_is_call_ret(c1)); }       /* call eax */
    { unsigned char c2[6] = { 0x90, 0x90, 0x90, 0x90, 0xff, 0x12 };   CHECK(kdt_is_call_ret(c2)); }       /* call [edx] */
    { unsigned char c3[6] = { 0x90, 0x90, 0x90, 0xff, 0x50, 0x04 };   CHECK(kdt_is_call_ret(c3)); }       /* call [eax+4] */
    { unsigned char c4[6] = { 0x90, 0x90, 0x90, 0xff, 0x14, 0x88 };   CHECK(kdt_is_call_ret(c4)); }       /* call [eax+ecx*4] */
    { unsigned char c5[6] = { 0xff, 0x15, 1, 2, 3, 4 };               CHECK(kdt_is_call_ret(c5)); }       /* call [abs32] */
    { unsigned char c6[6] = { 0xff, 0x90, 1, 2, 3, 4 };               CHECK(kdt_is_call_ret(c6)); }       /* call [eax+disp32] */
    { unsigned char c7[6] = { 0x90, 0x90, 0xff, 0x54, 0x88, 0x10 };   CHECK(kdt_is_call_ret(c7)); }       /* call [eax+ecx*4+0x10] */
    { unsigned char j1[6] = { 0x90, 0x90, 0x90, 0x90, 0xff, 0xe0 };   CHECK(!kdt_is_call_ret(j1)); }      /* jmp eax: /4, not a call */
    { unsigned char j2[6] = { 0x90, 0x90, 0x90, 0x90, 0x90, 0x90 };   CHECK(!kdt_is_call_ret(j2)); }
    { unsigned char j3[6] = { 0x90, 0x90, 0x90, 0x90, 0xff, 0x15 };   CHECK(!kdt_is_call_ret(j3)); }      /* mod 0 rm 5 needs the 6-byte form */
    /* stack scan: w[0] is taken as is; data words, junk code words and unreadable ones are skipped */
    w[0] = 0x400100; w[1] = 0x1234; w[2] = 0x500010; w[3] = 0x500020; w[4] = 0x700000; w[5] = 0x600040; w[6] = 0x510000; w[7] = 0x500030;
    CHECK(kdt_scan_stack(w, 8, 0x401000ul, 0xb00000ul, fake_rd, 0, out, 6) == 4);
    CHECK(out[0] == 0x500010ul && out[3] == 0x500030ul);
    CHECK(kdt_scan_stack(w, 8, 0x400000ul, 0xb00000ul, fake_rd, 0, out, 6) == 5 && out[0] == 0x400100ul && out[1] == 0x500010ul && out[2] == 0x500020ul && out[3] == 0x600040ul && out[4] == 0x500030ul);
    CHECK(kdt_scan_stack(w, 8, 0x400000ul, 0xb00000ul, fake_rd, 0, out, 2) == 2);
    CHECK(kdt_scan_stack(w, 0, 0x400000ul, 0xb00000ul, fake_rd, 0, out, 6) == 0);
    printf("kldeathtrace_test: %d checks, %d fail\n", checks, fails);
    return fails != 0;
}
