/* klmodestab_test.c - OFF-GAME check of klmodestab_logic.h (ModesTab row / description text, ini -> state rules, RoundHints line, host toggle text). */
#include <stdio.h>
#include "klmodestab_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    int i; char o[300];
    { int v[5] = { 1, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_TACTICS, v) == KMT_ON); }
    { int v[5] = { 0, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_TACTICS, v) == KMT_OFF); }         /* needs OnlineHost */
    { int v[5] = { 1, 0, 1, 2, 0 }; CHECK(kmt_state(KMT_DROPTAKE, v) == KMT_OFF); }        /* needs Tactics */
    { int v[5] = { 1, 1, 1, 2, 0 }; CHECK(kmt_state(KMT_DROPTAKE, v) == KMT_ON); }         /* v3 = OnlineTacticsTake */
    { int v[5] = { 1, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_DROPTAKE, v) == KMT_OFF); }        /* default ini: Take=0 -> nothing is taken */
    { int v[5] = { 1, 1, 1, 1, 0 }; CHECK(kmt_state(KMT_DROPTAKE, v) == KMT_OFF); }        /* only Take=2 takes */
    { int v[5] = { 1, 1, 1, 1, 0 }; CHECK(kmt_state(KMT_DOORHOLD, v) == KMT_ON); }         /* v3 = OnlineSkipDoorStacks */
    { int v[5] = { 1, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_DOORHOLD, v) == KMT_OFF); }        /* SkipDoorStacks=0: nothing to hold */
    { int v[5] = { 1, 1, 0, 1, 0 }; CHECK(kmt_state(KMT_DOORHOLD, v) == KMT_OFF); }
    { int v[5] = { 1, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_BANK, v) == KMT_ON); }             /* v2 = OnlineTacticsTake (1 or 2) */
    { int v[5] = { 1, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_BANK, v) == KMT_OFF); }            /* Take=0: no credit */
    { int v[5] = { 1, 0, 2, 0, 0 }; CHECK(kmt_state(KMT_BANK, v) == KMT_OFF); }            /* the ledger alone credits nothing */
    { int v[5] = { 1, 2, 2, 0, 0 }; CHECK(kmt_state(KMT_BANK, v) == KMT_DRY); }
    { int v[5] = { 2, 1, 2, 0, 0 }; CHECK(kmt_state(KMT_BANK, v) == KMT_DRY); }
    { int v[5] = { 0, 1, 2, 0, 0 }; CHECK(kmt_state(KMT_BANK, v) == KMT_OFF); }            /* credit without a ledger does nothing */
    { int v[5] = { 1, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_VOICE, v) == KMT_ON); }
    { int v[5] = { 0, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_VOICE, v) == KMT_OFF); }           /* [Voice] OnlineTalk is the crew banter, not bot voice (extra values are ignored) */
    { int v[5] = { 2, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_VOICE, v) == KMT_DRY); }
    { int v[5] = { 2, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_TRIGGERS, v) == KMT_DRY); }
    { int v[5] = { 3, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_ESCORT, v) == KMT_OFF); }          /* out of range = the module's 0 */
    { int v[5] = { 1, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_SHIELD, v) == KMT_ON); }           /* Online alone keeps the part on (klshield.c) */
    { int v[5] = { 0, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_SHIELD, v) == KMT_ON); }           /* Arcade Enable=1 */
    { int v[5] = { 0, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_SHIELD, v) == KMT_OFF); }
    { int v[5] = { 2, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_SHIELD, v) == KMT_DRY); }
    { int v[5] = { 1, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_SWAP, v) == KMT_ON); }             /* v1 Shop Enable, v2 ShopPage Enable | OnlineSwapArm */
    { int v[5] = { 1, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_SWAP, v) == KMT_OFF); }            /* the early-make hook is not armed */
    { int v[5] = { 1, 0, 1, 0, 0 }; CHECK(kmt_state(KMT_SWAP, v) == KMT_OFF); }            /* [Shop] Enable=0 */
    { int v[5] = { 2, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_SWAP, v) == KMT_DRY); }
    { int v[5] = { 7, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_CLOCK, v) == KMT_ON); }
    { int v[5] = { 25, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_CLOCK, v) == KMT_OFF); }          /* kllobbyopt.c: > 20 = off */
    { int v[5] = { 0, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_CLOCK, v) == KMT_OFF && kmt_state(99, v) == KMT_OFF); }
    {   /* the page cycle: 0 stock, 1 page II, 2 hire, 3 controls, 4 bots and modes. ModesTab off must equal the old 4-page cycle */
        int a1, a2, a3, cur, m;
        for (a1 = 0; a1 < 2; a1++) for (a2 = 0; a2 < 2; a2++) for (a3 = 0; a3 < 2; a3++) for (cur = 0; cur < 4; cur++) {
            int av[5] = { 1, a1, a2, a3, 0 }, want = cur, i, p;
            for (i = 1; i <= 4; i++) { p = (cur + i) % 4; if (p != cur && av[p]) { want = p; break; } }   /* the old rule, mod 4 */
            CHECK(kmt_next(cur, av) == want);
        }
        for (m = 0; m < 2; m++) { int av[5] = { 1, 1, 1, 1, m }; CHECK(kmt_next(3, av) == (m ? 4 : 0)); CHECK(kmt_next(4, av) == 0); CHECK(kmt_next(2, av) == 3); }
        { int av[5] = { 1, 0, 0, 0, 0 }; CHECK(kmt_next(0, av) == 0); }                     /* nothing else: stays */
        { int av[5] = { 1, 0, 0, 0, 1 }; CHECK(kmt_next(0, av) == 4 && kmt_next(4, av) == 0); }
        CHECK(kmt_pend_of(2) == 0 && kmt_pend_of(3) == 1 && kmt_pend_of(4) == 2);
        CHECK(!kmt_pend_ctl_mode(0) && !kmt_pend_ctl_mode(1) && kmt_pend_ctl_mode(2));
    }
    for (i = 0; i < KMT_N; i++) {                                                           /* every row fits the shop row in all three states */
        int s;
        for (s = 0; s < 3; s++) { kmt_row(i, s, o, sizeof o); CHECK(strlen(o) <= 16 && strlen(o) > 3); }
        kmt_desc(i, KMT_ON, o, sizeof o); CHECK(strstr(o, kmt_def[i].scope) && strstr(o, kmt_def[i].ini) && strstr(o, "Now: ON"));
    }
    kmt_row(KMT_TACTICS, KMT_ON, o, sizeof o); CHECK(!strcmp(o, "BOT TACTICS ON"));
    kmt_row(KMT_SHIELD, KMT_OFF, o, sizeof o); CHECK(strlen(o) <= 16);
    kmt_row(-1, 0, o, sizeof o); CHECK(!strcmp(o, "-"));
    kmt_desc(KMT_BANK, KMT_DRY, o, sizeof o); CHECK(strstr(o, "DRY = it only writes the log"));
    kmt_desc(KMT_BANK, KMT_ON, o, sizeof o); CHECK(!strstr(o, "DRY ="));
    kmt_desc(-1, 0, o, 8); CHECK(o[0] == 0);
    {   /* hint line */
        const char *k[5] = { "F2", "E+W", "G", "End", "" }; const char *w[5] = { "shop pages", "climb", "grenade", "unstick", "x" }; int on[5] = { 1, 1, 1, 1, 1 };
        CHECK(kmt_hint_build(k, w, on, 5, o, sizeof o) == 4 && !strcmp(o, "F2 shop pages  E+W climb  G grenade  End unstick"));
        on[1] = 0; CHECK(kmt_hint_build(k, w, on, 5, o, sizeof o) == 3 && !strcmp(o, "F2 shop pages  G grenade  End unstick"));
        on[0] = on[2] = on[3] = 0; CHECK(kmt_hint_build(k, w, on, 5, o, sizeof o) == 0 && !o[0]);
        on[0] = on[1] = on[2] = on[3] = 1; CHECK(kmt_hint_build(k, w, on, 5, o, 30) == 2 && !strcmp(o, "F2 shop pages  E+W climb") && strlen(o) < 30);   /* cut at a whole entry */
        CHECK(kmt_hint_build(k, w, on, 5, o, 0) == 0);
    }
    kmt_host_text(0, 0, o, sizeof o); CHECK(!strcmp(o, "MAP SET: Dog Days"));
    kmt_host_text(0, 1, o, sizeof o); CHECK(!strcmp(o, "MAP SET: Dead Men"));
    kmt_host_text(0, 2, o, sizeof o); CHECK(!strcmp(o, "MAP SET: Both"));
    kmt_host_text(1, 1, o, sizeof o); CHECK(!strcmp(o, "AI HEISTERS: ON"));
    kmt_host_text(1, 2, o, sizeof o); CHECK(!strcmp(o, "AI HEISTERS: OFF"));        /* bit 0 only: the Solo bit does not make it ON */
    kmt_host_text(1, 3, o, sizeof o); CHECK(!strcmp(o, "AI HEISTERS: ON"));
    kmt_host_text(2, 3, o, sizeof o); CHECK(!strcmp(o, "MAP POOL: Mix"));
    kmt_host_text(2, 0, o, sizeof o); CHECK(!strcmp(o, "MAP POOL: OFF"));
    printf("klmodestab_test: %d checks, %d fail\n", checks, fails);
    return fails ? 1 : 0;
}
