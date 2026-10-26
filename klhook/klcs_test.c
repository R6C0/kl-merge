/* klcs_test.c - OFF-GAME check of klcopsquad_logic.h: the C&R host gate, nearest-N soldier choice per cop, the Follow re-issue timer and the
 * key edge logic of [CopSquad]. Pure numbers; the game reads and calls are klcopsquad.c's (NOT run here).
 *   cl /nologo /W4 klcs_test.c      or      tools/run_harness_linux.sh klcs_test */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include "klcopsquad_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    struct klcq_cand c[8]; unsigned long out[KLCQ_PER_MAX]; struct klcq_key k; int n, i;
    /* gate: host, game type 4, sub-mode 2, in a round */
    CHECK(klcq_gate(2, 4, 0x19, 2));
    CHECK(klcq_gate(2, 4, 0x13, 2)); CHECK(klcq_gate(2, 4, 0x1f, 2));
    CHECK(!klcq_gate(3, 4, 0x19, 2));          /* client never */
    CHECK(!klcq_gate(0, 4, 0x19, 2)); CHECK(!klcq_gate(1, 4, 0x19, 2));
    CHECK(!klcq_gate(2, 3, 0x19, 2));          /* not game type 4 */
    CHECK(!klcq_gate(2, 4, 0x19, 0));          /* plain FA */
    CHECK(!klcq_gate(2, 4, 0x19, 1));          /* Undercover Cop */
    CHECK(!klcq_gate(2, 4, 0x12, 2)); CHECK(!klcq_gate(2, 4, 0x20, 2)); CHECK(!klcq_gate(2, 4, 0xd, 2));
    /* pick: nearest first, taken ones skipped, cap per */
    memset(c, 0, sizeof c);
    for (i = 0; i < 6; i++) { c[i].id = 0x1000 + i; c[i].d2 = (float)((6 - i) * (6 - i) * 10000); }   /* ids ..5 nearest */
    n = klcq_pick(c, 6, 4, 0, out);
    CHECK(n == 4); CHECK(out[0] == 0x1005); CHECK(out[1] == 0x1004); CHECK(out[2] == 0x1003); CHECK(out[3] == 0x1002);
    CHECK(c[5].taken && c[4].taken && c[3].taken && c[2].taken && !c[1].taken && !c[0].taken);
    n = klcq_pick(c, 6, 4, 0, out);            /* a second cop gets what is left */
    CHECK(n == 2); CHECK(out[0] == 0x1001); CHECK(out[1] == 0x1000);
    n = klcq_pick(c, 6, 4, 0, out); CHECK(n == 0);
    /* pick: a max distance keeps far ones out; a zero id, NaN or negative distance is never chosen */
    memset(c, 0, sizeof c);
    c[0].id = 1; c[0].d2 = 100.0f * 100.0f; c[1].id = 2; c[1].d2 = 5000.0f * 5000.0f; c[2].id = 0; c[2].d2 = 1.0f;
    c[3].id = 4; c[3].d2 = -1.0f; c[4].id = 5; { float z = 0.0f; c[4].d2 = z / z; }
    n = klcq_pick(c, 5, 4, klcq_maxd2(40), out);
    CHECK(n == 1); CHECK(out[0] == 1);
    memset(c, 0, sizeof c); c[0].id = 1; c[0].d2 = 1; c[1].id = 2; c[1].d2 = 2;
    n = klcq_pick(c, 2, 0, 0, out); CHECK(n == 0);                       /* per 0: nothing */
    for (i = 0; i < 8; i++) { c[i].id = 10 + i; c[i].d2 = (float)i; c[i].taken = 0; }
    n = klcq_pick(c, 8, 99, 0, out); CHECK(n == KLCQ_PER_MAX);           /* per over the cap: the cap */
    /* equal distances: the first in the list wins, every one taken once */
    for (i = 0; i < 4; i++) { c[i].id = 20 + i; c[i].d2 = 7.0f; c[i].taken = 0; }
    n = klcq_pick(c, 4, 2, 0, out); CHECK(n == 2 && out[0] == 20 && out[1] == 21);
    n = klcq_pick(c, 4, 2, 0, out); CHECK(n == 2 && out[0] == 22 && out[1] == 23);
    /* the re-issue timer */
    CHECK(klcq_due(0, 1000, 8000));            /* never issued */
    CHECK(!klcq_due(1000, 2000, 8000));
    CHECK(klcq_due(1000, 9000, 8000));
    CHECK(klcq_due(1000, 9001, 8000));
    CHECK(!klcq_due(1000, 8999, 8000));
    CHECK(!klcq_due(1000, 999999, 0));         /* period 0: once only */
    CHECK(klcq_due(0, 0, 0));
    CHECK(klcq_due(0xfffffff0ul, 0x10ul, 8000) == 0);   /* tick wrap: 32 ms passed, not due */
    CHECK(klcq_due(0xfffffff0ul, 0x2000ul, 8000) == 1);
    /* key edges: once per press, no repeat while held, debounced */
    memset(&k, 0, sizeof k);
    CHECK(!klcq_edge(&k, 0, 1000));
    CHECK(klcq_edge(&k, 1, 1000));
    CHECK(!klcq_edge(&k, 1, 1016)); CHECK(!klcq_edge(&k, 1, 1032));      /* held */
    CHECK(!klcq_edge(&k, 0, 1048));
    CHECK(!klcq_edge(&k, 1, 1100));            /* bounce 100 ms after the fired edge: swallowed */
    CHECK(!klcq_edge(&k, 0, 1116));
    CHECK(klcq_edge(&k, 1, 2500));             /* a real second press */
    CHECK(!klcq_edge(&k, 1, 9000));            /* still held: no repeat however long */
    memset(&k, 0, sizeof k);
    CHECK(klcq_edge(&k, 1, 0));                /* now 0 still fires (stored as 1) */
    CHECK(!klcq_edge(&k, 0, 10)); CHECK(!klcq_edge(&k, 1, 100));
    /* order of a key */
    CHECK(klcq_order_of(0x46, 0x46, 0x47, 0x48) == 1);
    CHECK(klcq_order_of(0x47, 0x46, 0x47, 0x48) == 2);
    CHECK(klcq_order_of(0x48, 0x46, 0x47, 0x48) == 3);
    CHECK(klcq_order_of(0x49, 0x46, 0x47, 0x48) == 0);
    CHECK(klcq_order_of(0, 0, 0x47, 0x48) == 0);        /* an unbound key (0) never matches */
    /* clamps */
    CHECK(klcq_clamp_per(0) == 1); CHECK(klcq_clamp_per(4) == 4); CHECK(klcq_clamp_per(100) == KLCQ_PER_MAX);
    CHECK(klcq_clamp_follow_ms(0) == 0); CHECK(klcq_clamp_follow_ms(1) == 2000); CHECK(klcq_clamp_follow_ms(8) == 8000); CHECK(klcq_clamp_follow_ms(999) == 120000);
    CHECK(klcq_maxd2(40) == 4000.0f * 4000.0f); CHECK(klcq_maxd2(0) == 500.0f * 500.0f); CHECK(klcq_maxd2(1000) == 20000.0f * 20000.0f);
    printf("%d checks, %d failed\n", checks, fails);
    printf(fails ? "FAIL\n" : "ALL PASS\n");
    return fails ? 1 : 0;
}
