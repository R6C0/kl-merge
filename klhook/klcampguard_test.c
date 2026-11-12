/* klcampguard_test.c - off-game checks of klcampguard_logic.h against a byte map of kl2.exe build 0490's real code bytes (MEASURED 2026-11-09 from the
 * on-disk exe) and a fake stack. Build: cl /nologo /W3 klcampguard_test.c */
#include <stdio.h>
#include <string.h>
#include "klcampguard_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

/* ---- fake process memory: segments {base, bytes} ---- */
typedef struct { unsigned base, n; unsigned char b[512]; } seg;
static seg segs[40]; static int nseg;
static seg *mk(unsigned base, unsigned n) { seg *s = &segs[nseg++]; s->base = base; s->n = n; memset(s->b, 0, sizeof s->b); return s; }
static void code(unsigned at, const char *hex)
{
    unsigned char t[64]; int n = 0; unsigned v; seg *s;
    while (*hex) { if (*hex == ' ') { hex++; continue; } sscanf(hex, "%2x", &v); t[n++] = (unsigned char)v; hex += 2; }
    s = mk(at, n); memcpy(s->b, t, n);
}
static int rdn(void *u, unsigned a, void *out, int n)
{
    int i; (void)u;
    for (i = 0; i < nseg; i++) if (a >= segs[i].base && a + n <= segs[i].base + segs[i].n) { memcpy(out, segs[i].b + (a - segs[i].base), n); return 1; }
    return 0;
}
static unsigned char *at(unsigned a) { int i; for (i = 0; i < nseg; i++) if (a >= segs[i].base && a < segs[i].base + segs[i].n) return segs[i].b + (a - segs[i].base); return 0; }
static klcg_mem M = { 0, rdn };
#define ALL 0xffu
#define STK 0x0012f000u

static void reset(void)
{
    nseg = 0;
    code(0x4f8a60, "51 8b 54 24 08 89 0c 24"); code(0x4f8a6e, "8b 11"); code(0x4f8b40, "33 c0 5b 5e 5d 59 c2 0c 00"); code(0x4f8b45, "59 c2 0c 00");
    code(0x51f1a5, "3b c3 75 01 cc");
    code(0x927b4c, "8b 13 8b 82 e8 02 00 00 83 c4 04");
    code(0x446673, "8b 6c 24 1c f7 e5"); code(0x44668b, "f7 f5");
    code(0x900ff8, "66 3b 41 18"); code(0x577e08, "d9 02 d8");
    code(0x466590, "8b 44 24 04 83 c0 f0 81 38 78 56 34 12 75 3d"); code(0x4665dc, "cc c3"); code(0x882c7f, "51 e8 0b 39 be ff"); code(0x882c9b, "b0 01 5e c2 04 00");
    mk(STK, 0x100);                                                   /* the stack */
}
static void sp(int dw, unsigned v) { memcpy(at(STK) + dw * 4, &v, 4); }
static void inav(klcg_in *in, unsigned eip, unsigned fa) { memset(in, 0, sizeof *in); in->code = KLCG_AV; in->at = in->eip = eip; in->nparam = 2; in->info0 = 0; in->info1 = fa; in->reg[KLCG_ESP] = STK; }

int main(void)
{
    klcg_in in; klcg_act a; seg *s; unsigned v, i;

    /* ---- CListUser: the owner's DM03 crash 2026-11-09 (edx = fault address 0x4f09, ret 0x6307ed, record id 0) ---- */
    reset(); inav(&in, 0x4f8a8e, 0x4f09); in.reg[KLCG_EDX] = 0x4f09; sp(4, 0x6307ed); sp(5, 0);
    CHECK(klcg_decide(&M, &in, ALL, 0, &a) == KLCG_CL_BUCKET);
    CHECK(a.eip == 0x4f8b40 && (a.regset & 1) && a.reg[KLCG_EAX] == 0 && a.i0 == 0x6307ed && a.i1 == 0);
    CHECK(klcg_group(a.site) == KLCG_G_LISTUSER);
    CHECK(klcg_decide(&M, &in, ALL & ~KLCG_G_LISTUSER, 0, &a) == 0);          /* group off */
    CHECK(klcg_decide(&M, &in, 0, 0, &a) == 0);
    for (i = 0; i < 3; i++) { unsigned e[3] = { 0x4f8a92, 0x4f8a97, 0x4f8a9e }; inav(&in, e[i], 0x4f0c); in.reg[KLCG_EDX] = 0x4f09; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == KLCG_CL_BUCKET); }
    inav(&in, 0x4f8a8e, 0x4f09); in.reg[KLCG_EDX] = 0x4f09;
    in.info1 = 0x4f19; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);          /* fault address outside [edx, edx+0x10) */
    in.info1 = 0x4f08; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);
    in.info1 = 0x4f09; in.info0 = 1; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);   /* a WRITE fault */
    in.info0 = 0; sp(4, 0x401234); CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);     /* unknown caller */
    sp(4, 0x6307ed); at(0x4f8b40)[0] = 0x90; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);   /* resume target bytes changed */
    at(0x4f8b40)[0] = 0x33; at(0x4f8a60)[0] = 0x52; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);   /* function prologue changed */
    at(0x4f8a60)[0] = 0x51; in.code = KLCG_BP; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);
    inav(&in, 0x4f8a8e, 0x4f09); in.reg[KLCG_EDX] = 0x4f09; in.at = 0x4f8a8f; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);   /* ExceptionAddress != Eip */
    inav(&in, 0x4f8a8e, 0x4f09); in.reg[KLCG_EDX] = 0x4f09; in.reg[KLCG_ESP] = 0x7000; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);   /* stack unreadable */
    /* slot read */
    inav(&in, 0x4f8a6e, 0x33ce7604); in.reg[KLCG_ECX] = 0x33ce7604; sp(1, 0x630811); sp(2, 0x7b2);
    CHECK(klcg_decide(&M, &in, ALL, 0, &a) == KLCG_CL_SLOT && a.eip == 0x4f8b45 && a.reg[KLCG_EAX] == 0 && a.i1 == 0x7b2);
    in.info1 = 5; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);               /* fault address is not ecx */
    in.info1 = in.reg[KLCG_ECX]; sp(1, 0x111111); CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);

    /* ---- gfx int3 ---- */
    reset(); memset(&in, 0, sizeof in); in.code = KLCG_BP; in.at = 0x51f1a9; in.eip = 0x51f1aa; in.reg[KLCG_ESP] = STK;
    s = mk(0x30000000u, 0x40);
    sp(0, 0xd1); sp(1, 0xe1); sp(2, 0xb1); sp(7, 0x6a1234); sp(8, 0x30000000u);
    CHECK(klcg_decide(&M, &in, ALL, 0, &a) == KLCG_GFX);
    CHECK(a.eip == 0x6a1234 && a.reg[KLCG_EDI] == 0xd1 && a.reg[KLCG_ESI] == 0xe1 && a.reg[KLCG_EBX] == 0xb1 && a.reg[KLCG_ESP] == STK + 0x30);
    CHECK(a.zeroAt == 0x30000000u && a.zeroN == 0x19 && !(a.regset & 1));
    in.eip = 0x51f1a9; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == KLCG_GFX);
    in.reg[KLCG_EAX] = 5; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);       /* template WAS found */
    in.reg[KLCG_EAX] = 0; sp(8, 0x40000000u); CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);   /* result struct unreachable */
    sp(8, 0x30000000u); sp(7, 0x12); CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);
    sp(7, 0x6a1234); at(0x51f1a9)[0] = 0x90; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);
    (void)s;

    /* ---- collision callback ---- */
    reset(); inav(&in, 0x927b4c, 0); in.reg[KLCG_EBX] = 0; sp(0, 0x1234);
    CHECK(klcg_decide(&M, &in, ALL, 0, &a) == KLCG_COLL && a.eip == 0x927b5f && a.reg[KLCG_ESP] == STK + 4);
    inav(&in, 0x927b4e, 0x2e8 + 0x10); in.reg[KLCG_EDX] = 0x10; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == KLCG_COLL);
    in.info1 = 0x2e8; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);
    inav(&in, 0x927b4c, 4); in.reg[KLCG_EBX] = 0; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);   /* fault address is not the handle object */
    inav(&in, 0xdeadbee0, 0xdeadbee0); in.reg[KLCG_ECX] = in.reg[KLCG_EBX] = 0x55; in.reg[KLCG_EAX] = 0x12340000; sp(0, 0x927b5b);
    CHECK(klcg_decide(&M, &in, ALL, 0, &a) == KLCG_COLL_CALL && a.eip == 0x927b5b && a.reg[KLCG_EAX] == 0x12340001 && a.reg[KLCG_ESP] == STK + 4);
    sp(0, 0x927b60); CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);            /* not called from the callback */
    sp(0, 0x927b5b); in.reg[KLCG_ECX] = 7; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);

    /* ---- sound stream rate 0 and the range divide ---- */
    reset(); memset(&in, 0, sizeof in); in.code = KLCG_DIV0; in.at = in.eip = 0x44668b; in.reg[KLCG_ESP] = STK; in.reg[KLCG_EBP] = 0; sp(7, 0);
    CHECK(klcg_decide(&M, &in, ALL, 0, &a) == KLCG_SND && a.eip == 0x446673 && a.reg[KLCG_EAX] == 0xcccccccdu && a.npoke == 1 && a.poke[0].a == STK + 0x1c && a.poke[0].v == 22050);
    sp(7, 5); CHECK(klcg_decide(&M, &in, ALL & ~KLCG_G_SNDDIV, 0, &a) == 0);   /* the stream rate is set: not this fault */
    sp(7, 0); in.reg[KLCG_EBP] = 3; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);
    in.reg[KLCG_EBP] = 0; CHECK(klcg_decide(&M, &in, KLCG_G_SNDDIV, 0, &a) == 0 || a.site == KLCG_DIVRANGE);
    /* range divide: div [esp+0x20] / div esi / div edi */
    reset(); code(0x447000, "f7 74 24 20"); memset(&in, 0, sizeof in); in.code = KLCG_DIV0; in.at = in.eip = 0x447000; in.reg[KLCG_ESP] = STK; sp(8, 0);
    CHECK(klcg_decide(&M, &in, ALL, 0, &a) == KLCG_DIVRANGE && a.eip == 0x447000 && a.npoke == 1 && a.poke[0].a == STK + 0x20 && a.poke[0].v == 1);
    sp(8, 4); CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);                   /* divisor is not 0 (overflow, not ours) */
    reset(); code(0x447010, "f7 f6 90 90"); memset(&in, 0, sizeof in); in.code = KLCG_DIV0; in.at = in.eip = 0x447010; in.reg[KLCG_ESP] = STK; in.reg[KLCG_ESI] = 0;
    CHECK(klcg_decide(&M, &in, ALL, 0, &a) == KLCG_DIVRANGE && (a.regset & (1u << KLCG_ESI)) && a.reg[KLCG_ESI] == 1);
    in.reg[KLCG_EDX] = 1; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);       /* edx != 0 */
    in.reg[KLCG_EDX] = 0; at(0x447010)[1] = 0xf0; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);   /* div eax */
    at(0x447010)[1] = 0xf4; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);     /* div esp */
    at(0x447010)[1] = 0xf2; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);     /* div edx */
    reset(); code(0x4c0000, "f7 f6"); memset(&in, 0, sizeof in); in.code = KLCG_DIV0; in.at = in.eip = 0x4c0000; in.reg[KLCG_ESP] = STK;
    CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);                              /* outside the sound range */

    /* ---- null sound list ---- */
    reset(); inav(&in, 0x900ff8, 0); in.reg[KLCG_ECX] = 0; sp(0, 0x5a0000); sp(1, 7);
    CHECK(klcg_decide(&M, &in, ALL, 0, &a) == KLCG_NULLLIST && a.eip == 0x5a0000 && a.reg[KLCG_EAX] == 0 && a.reg[KLCG_ESP] == STK + 8);
    in.reg[KLCG_ECX] = 4; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);
    in.reg[KLCG_ECX] = 0; sp(0, 0x20); CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);

    /* ---- v4BonesLights ---- */
    reset(); inav(&in, 0x577e08, 0); in.reg[KLCG_ESI] = 0x31000000u + 0x9c; sp(3, 0x7d57ec); s = mk(0x31000000u + 0x3d0, 8);
    CHECK(klcg_decide(&M, &in, ALL, 0x7000, &a) == KLCG_BONES);
    CHECK(a.eip == 0x577e08 && a.reg[KLCG_EDX] == 0x7000 && a.reg[KLCG_EDI] == 0x7000 && a.npoke == 2 && a.poke[0].a == 0xf1b244 && a.poke[1].a == 0x31000000u + 0x3d0 && a.poke[1].v == 0x20);
    in.reg[KLCG_EDX] = 4; CHECK(klcg_decide(&M, &in, ALL, 0x7000, &a) == 0);
    in.reg[KLCG_EDX] = 0; sp(3, 0x1); CHECK(klcg_decide(&M, &in, ALL, 0x7000, &a) == 0);
    sp(3, 0x7d57ec); s->b[0] = 0x20; CHECK(klcg_decide(&M, &in, ALL, 0x7000, &a) == 0);   /* ctx+0x3d0 already set: some other fault */
    (void)s;

    /* ---- heap int3 ---- */
    reset(); memset(&in, 0, sizeof in); in.code = KLCG_BP; in.at = 0x4665dc; in.eip = 0x4665dd; in.reg[KLCG_ESP] = STK; in.reg[KLCG_EAX] = 0x32000000u;
    sp(0, 0x882c85); sp(1, 0x32000010u); s = mk(0x32000000u, 16); s->b[0] = 0x11;
    CHECK(klcg_decide(&M, &in, ALL, 0, &a) == KLCG_HEAP && a.eip == 0x882c9b && a.reg[KLCG_ESP] == STK + 8 && a.i0 == 0x32000010u);
    v = 0x12345678; memcpy(s->b, &v, 4); CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);   /* magic is fine: not this int3 */
    s->b[0] = 0x11; sp(0, 0x882c86); CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);
    sp(0, 0x882c85); in.reg[KLCG_EAX] = 0x32000004u; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);
    in.reg[KLCG_EAX] = 0x32000000u; at(0x882c9b)[0] = 0; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);
    at(0x882c9b)[0] = 0xb0; in.code = KLCG_AV; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);

    /* ---- unrelated faults are never ours ---- */
    reset(); inav(&in, 0x401000, 0); CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);
    in.code = 0xC000001Du; CHECK(klcg_decide(&M, &in, ALL, 0, &a) == 0);
    CHECK(klcg_log_now(1) && klcg_log_now(3) && !klcg_log_now(5) && klcg_log_now(8) && !klcg_log_now(0) && klcg_log_now(1024));
    CHECK(klcg_group(KLCG_NONE) == 0 && klcg_group(KLCG_NSITE) == 0);
    for (i = 1; i < KLCG_NSITE; i++) CHECK(klcg_group((int)i) != 0 && klcg_name((int)i)[0] != '?');

    printf("RESULT: %s (%d checks, %d failed)\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails != 0;
}
