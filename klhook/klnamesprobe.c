/*
 * klnamesprobe.c - [BotFill] OnlineNamesProbe=0|1 (default 0, recommended off: a bench probe). LOG ONLY: nothing is written to the game, nothing is sent, no code patch,
 * no game routine is called. It reads what klbotfill.c's OnlineLooks=2 probe reads (the Ally census: group digit + model root) and resolves each model root to the
 * level's wardrobe character exactly as klonline_read.c / klhud_names.c do for the HUD, then logs ONE line per seat:
 *
 *   botfill: names: HOST|CLIENT n=7 digest=1a2b3c4d: 2=Kane 3=Liam 4=- 5=Pierre ...
 *
 * Why: the names the owner sees on a bot online (crew list, tags, scoreboard rows, KILLED BY) are derived LOCALLY per peer from the model the bot wears. The digest is keyed by
 * the group digit (not by census order, which is unproven across peers), so with [BotFill] OnlineLooks=1 the host's and every client's digest must be EQUAL once the looks have
 * applied. A 9-seat bench grades it with `grep "botfill: names:" KLHook.log` on each instance: compare the last digest per round.
 * Spec: re/parity_gaps_7_8_11_1106.md section 4. NOT RUN IN THE GAME.
 *
 * Part of KLHook (included by klhook.c AFTER klcrewlook.c, SHIP and TEST alike). Gate: a session with role 2 (host) or 3 (client), game type 4, state 0x13..0x1e (intro .. round),
 * game thread. Cadence: at once on the first line, on a change of the digest (not twice within 2 s), and every 10 s as a heartbeat. Per round the log is bounded by that cadence.
 *
 * KLHook.ini
 *   [BotFill]
 *   OnlineNamesProbe=0     (recommended off) 1 = log the digest line described above; any other value = off
 */
#ifndef KLNAMESPROBE_C
#define KLNAMESPROBE_C

#include "klnamesprobe_logic.h"

#define KLNP_MIN_MS  2000ul
#define KLNP_BEAT_MS 10000ul

static struct { int inited, mode, first; unsigned long sig, at, sm; } klnp_t;

static void klnp_tick(int game_thread)
{
    static struct klbf_lkrec lk[64];
    struct klnp_e e[KLNP_MAXE]; struct klw_src src; char list[300];
    DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0, rules = 0; int n, i, k, m = 0; unsigned long dig;
    if (!klnp_t.inited) {      /* the ini is read once, on the first tick (this file has no init hook of its own) */
        klnp_t.inited = 1; klnp_t.first = 1;
        klnp_t.mode = (int)GetPrivateProfileIntA("BotFill", "OnlineNamesProbe", 0, klh_ini); if (klnp_t.mode != 1) klnp_t.mode = 0;
        if (klnp_t.mode) klog("botfill: OnlineNamesProbe=1: LOG ONLY, one 'botfill: names:' line per seat (digest of digit -> wardrobe character); compare the digest of the host and every client (equal = the same names on every screen)");
    }
    if (!klnp_t.mode || !game_thread || !klh_exe_ok) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) { klnp_t.first = 1; klnp_t.sm = 0; return; }
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) return;
    if ((role != 2 && role != 3) || mode != 4 || state < 0x13 || state > 0x1e) { if (state < 0x13 || state >= 0x1f) klnp_t.first = 1; return; }      /* a new round logs at once */
    if (!klcl_src(&src, &rules)) return;
    n = klbf_ally_census(lk, 64, NULL);
    for (i = 0; i < n && m < KLNP_MAXE; i++) {
        struct klnp_e *p = &e[m++];
        p->digit = lk[i].digit >= '1' && lk[i].digit <= '9' ? lk[i].digit - '0' : 0; p->model = lk[i].model; p->name[0] = 0;
        if (lk[i].model) for (k = 0; k < src.n && k < KLC_NCHAR; k++) if (src.c[k].root == lk[i].model) { snprintf(p->name, sizeof p->name, "%s", src.c[k].name); break; }
    }
    dig = klnp_digest(e, m);
    if (!klnp_due(now, dig, &klnp_t.sig, &klnp_t.at, &klnp_t.first, KLNP_MIN_MS, KLNP_BEAT_MS)) return;
    klnp_list(list, sizeof list, e, m);
    klog("botfill: names: %s n=%d digest=%08lx: %s", role == 2 ? "HOST" : "CLIENT", m, dig, list);
}

#endif /* KLNAMESPROBE_C */
