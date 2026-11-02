/* klmodestab_test.c - OFF-GAME check of klmodestab_logic.h (ModesTab row / description text, ini -> state rules, RoundHints line, host toggle text). */
#include <stdio.h>
#include "klmodestab_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    int i; char o[300];
    { int v[5] = { 1, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_TACTICS, v, 0) == KMT_ON); }
    { int v[5] = { 0, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_TACTICS, v, 0) == KMT_OFF); }         /* needs OnlineHost */
    { int v[5] = { 1, 0, 1, 2, 0 }; CHECK(kmt_state(KMT_DROPTAKE, v, 0) == KMT_OFF); }        /* needs Tactics */
    { int v[5] = { 1, 1, 1, 2, 0 }; CHECK(kmt_state(KMT_DROPTAKE, v, 0) == KMT_ON); }         /* v3 = OnlineTacticsTake */
    { int v[5] = { 1, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_DROPTAKE, v, 0) == KMT_OFF); }        /* default ini: Take=0 -> nothing is taken */
    { int v[5] = { 1, 1, 1, 1, 0 }; CHECK(kmt_state(KMT_DROPTAKE, v, 0) == KMT_OFF); }        /* only Take=2 takes */
    { int v[5] = { 1, 1, 1, 1, 0 }; CHECK(kmt_state(KMT_DOORHOLD, v, 0) == KMT_ON); }         /* v3 = OnlineSkipDoorStacks */
    { int v[5] = { 1, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_DOORHOLD, v, 0) == KMT_OFF); }        /* SkipDoorStacks=0: nothing to hold */
    { int v[5] = { 1, 1, 0, 1, 0 }; CHECK(kmt_state(KMT_DOORHOLD, v, 0) == KMT_OFF); }
    { int v[5] = { 1, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_BANK, v, 0) == KMT_ON); }             /* v2 = OnlineTacticsTake (1 or 2) */
    { int v[5] = { 1, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_BANK, v, 0) == KMT_OFF); }            /* Take=0: no credit */
    { int v[5] = { 1, 0, 2, 0, 0 }; CHECK(kmt_state(KMT_BANK, v, 0) == KMT_OFF); }            /* the ledger alone credits nothing */
    { int v[5] = { 1, 2, 2, 0, 0 }; CHECK(kmt_state(KMT_BANK, v, 0) == KMT_DRY); }
    { int v[5] = { 2, 1, 2, 0, 0 }; CHECK(kmt_state(KMT_BANK, v, 0) == KMT_DRY); }
    { int v[5] = { 0, 1, 2, 0, 0 }; CHECK(kmt_state(KMT_BANK, v, 0) == KMT_OFF); }            /* credit without a ledger does nothing */
    { int v[5] = { 1, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_VOICE, v, 0) == KMT_ON); }
    { int v[5] = { 0, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_VOICE, v, 0) == KMT_OFF); }           /* [Voice] OnlineTalk is the crew banter, not bot voice (extra values are ignored) */
    { int v[5] = { 2, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_VOICE, v, 0) == KMT_DRY); }
    { int v[5] = { 2, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_TRIGGERS, v, 0) == KMT_DRY); }
    { int v[5] = { 3, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_ESCORT, v, 0) == KMT_OFF); }          /* out of range = the module's 0 */
    /* KMT_SHIELD takes the online flag (the caller passes kl_online()): Arcade = [Shield] Enable (v1), online = [Shield] Online (v0) alone (klshield.c: klsh.on = arc || online; Online=2 is the dry log) */
    { int v[5] = { 1, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_SHIELD, v, 1) == KMT_ON); }          /* online, Online=1 alone keeps the part on (klshield.c) */
    { int v[5] = { 1, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_SHIELD, v, 0) == KMT_OFF); }         /* Arcade: Enable=0 and the online switch does not act offline */
    { int v[5] = { 0, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_SHIELD, v, 0) == KMT_ON); }          /* Arcade Enable=1 */
    { int v[5] = { 0, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_SHIELD, v, 1) == KMT_OFF); }         /* online with Enable=1 but Online=0: the shield does not work online (the old row said ON) */
    { int v[5] = { 0, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_SHIELD, v, 0) == KMT_OFF && kmt_state(KMT_SHIELD, v, 1) == KMT_OFF); }
    { int v[5] = { 2, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_SHIELD, v, 1) == KMT_DRY); }         /* online dry log */
    { int v[5] = { 2, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_SHIELD, v, 0) == KMT_ON); }          /* offline the Arcade part is on, Online is not read */
    { int v[5] = { 1, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_SHIELD, v, 1) == KMT_ON); }
    /* kmt_host_only: the rows a client seat cannot act on (host-side code), and the description suffix */
    CHECK(kmt_host_only(KMT_TACTICS) && kmt_host_only(KMT_DROPTAKE) && kmt_host_only(KMT_TRIGGERS) && kmt_host_only(KMT_ESCORT) && kmt_host_only(KMT_SHIELD) && !kmt_host_only(KMT_SWAP) && !kmt_host_only(-1) && !kmt_host_only(KMT_N));
    { int v[5] = { 1, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_SWAP, v, 0) == KMT_ON); }             /* v1 Shop Enable, v2 ShopPage Enable | OnlineSwapArm */
    { int v[5] = { 1, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_SWAP, v, 0) == KMT_OFF); }            /* the early-make hook is not armed */
    { int v[5] = { 1, 0, 1, 0, 0 }; CHECK(kmt_state(KMT_SWAP, v, 0) == KMT_OFF); }            /* [Shop] Enable=0 */
    { int v[5] = { 2, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_SWAP, v, 0) == KMT_DRY); }
    { int v[5] = { 7, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_CLOCK, v, 0) == KMT_ON); }
    { int v[5] = { 25, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_CLOCK, v, 0) == KMT_OFF); }          /* kllobbyopt.c: > 20 = off */
    { int v[5] = { 0, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_CLOCK, v, 0) == KMT_OFF && kmt_state(99, v, 0) == KMT_OFF); }
    /* DropFollow / BoardAll / CrewHealth / Looks / Unique (wk-auditrows-1102): same prerequisites as klbotfill.c, klgrudge.c, klcharonline.c */
    { int v[5] = { 1, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_DROPFOLLOW, v, 0) == KMT_ON); }
    { int v[5] = { 1, 0, 1, 0, 0 }; CHECK(kmt_state(KMT_DROPFOLLOW, v, 0) == KMT_OFF); }       /* needs Tactics */
    { int v[5] = { 0, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_DROPFOLLOW, v, 0) == KMT_OFF); }       /* needs OnlineHost */
    { int v[5] = { 1, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_DROPFOLLOW, v, 0) == KMT_OFF); }
    { int v[5] = { 1, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_BOARDALL, v, 0) == KMT_ON); }
    { int v[5] = { 1, 1, 2, 0, 0 }; CHECK(kmt_state(KMT_BOARDALL, v, 0) == KMT_DRY); }          /* OnlineBoardAll=2 logs only */
    { int v[5] = { 1, 0, 1, 0, 0 }; CHECK(kmt_state(KMT_BOARDALL, v, 0) == KMT_OFF); }
    { int v[5] = { 0, 1, 1, 0, 0 }; CHECK(kmt_state(KMT_BOARDALL, v, 0) == KMT_OFF); }
    { int v[5] = { 150, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_CREWHP, v, 0) == KMT_ON); }          /* x1.5 */
    { int v[5] = { 150, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_CREWHP, v, 0) == KMT_DRY); }
    { int v[5] = { 100, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_CREWHP, v, 0) == KMT_OFF); }         /* 1.0 = off (klgrudge.c) */
    { int v[5] = { 0, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_CREWHP, v, 0) == KMT_OFF); }           /* dry alone does nothing */
    { int v[5] = { 24, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_CREWHP, v, 0) == KMT_OFF); }          /* below 0.25 */
    { int v[5] = { 1001, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_CREWHP, v, 0) == KMT_OFF); }        /* above 10 */
    { int v[5] = { 1, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_LOOKS, v, 0) == KMT_ON); }
    { int v[5] = { 1, 2, 0, 0, 0 }; CHECK(kmt_state(KMT_LOOKS, v, 0) == KMT_DRY); }
    { int v[5] = { 0, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_LOOKS, v, 0) == KMT_OFF); }            /* needs OnlineHost */
    { int v[5] = { 1, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_UNIQUE, v, 0) == KMT_ON); }
    { int v[5] = { 1, 0, 0, 0, 0 }; CHECK(kmt_state(KMT_UNIQUE, v, 0) == KMT_OFF); }
    { int v[5] = { 0, 1, 0, 0, 0 }; CHECK(kmt_state(KMT_UNIQUE, v, 0) == KMT_OFF); }           /* [CharOnline] Enable=0 */
    CHECK(kmt_host_only(KMT_DROPFOLLOW) && kmt_host_only(KMT_BOARDALL) && kmt_host_only(KMT_CREWHP) && kmt_host_only(KMT_LOOKS) && !kmt_host_only(KMT_UNIQUE));
    CHECK(KMT_N <= 16);                                                                         /* the page holds 16 rows (klshoppage.c kspg_m_feat: rows 0..7 + 17..24) */
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
    kmt_desc_ex(KMT_TRIGGERS, KMT_ON, 1, o, sizeof o); CHECK(strstr(o, " (host only: you are a client)"));      /* client seat, host-only row */
    kmt_desc_ex(KMT_TRIGGERS, KMT_ON, 0, o, sizeof o); CHECK(!strstr(o, "host only: you are a client"));
    kmt_desc_ex(KMT_SWAP, KMT_ON, 1, o, sizeof o); CHECK(!strstr(o, "host only: you are a client"));         /* not a host-only row */
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
