/*
 * klonline.c - ARCADE FEATURES IN A NETWORK ROUND (owner 2026-10-25: "we must implement all of the arcade features into quick play
 * ranked and LAN"). Part of KLHook (included by klhook.c right after klbot.c, SHIP and TEST alike). Audit and ranking of every
 * feature: re/arcade_online_parity.md. This file holds the shared, READ-ONLY helper the purely local, cosmetic parts use to see
 * an online round. It writes NOTHING and calls no game routine.
 *
 *   klon_read(s, allow)  = klb_read (Arcade) and, when allow != 0, the ONLINE snapshot of klbot.c klb_read_hud (host role 2 / client
 *                          role 3, game type 4, rules ...FragileAllianceSv / Cl): rules + session state, n = 0, score = 0 (+ the
 *                          crew money handles when [HUD] OnlineCrew=1). The online path of klb_read_hud belongs to the HUD
 *                          work and is only CALLED here: klb_hud_online is forced to 1 for the length of the call and put back.
 *   klon_money(s)        = the crew money the music / ambience / stinger parts read: the Arcade sum, or - online and only with
 *                          [HUD] OnlineCrew=1 - the sum of the online handles (GUESS: 'Total' = [S+0x224+4i] + [S+0x188+4i], the SL6 reading).
 *
 * WHAT THE ONLINE SNAPSHOT CAN DRIVE (so what [Music] / [Ambience] / [Stinger] Online=1 do):
 *   state 0x19 (KLB_ROUND, GUESS: the multiplayer session keeps the same state numbers; the 'online:' log line prints every
 *   state change so the first live run proves it) = round runs -> CALM; ACTION by the AfterSeconds timer (and by money when
 *   OnlineCrew is on); ESCAPE / DOWN / the van events need the Heist records and stay silent online. END on leaving the round.
 *
 * KLHook.ini   (each default 0 = the game as before; all four "(recommended on)" once SL tests pass)
 *   [Music] Online=0     [Ambience] Online=0     [Stinger] Online=0
 *   [Online] Log=1       0 = no 'online:' lines
 */
#ifndef KLONLINE_C
#define KLONLINE_C

static int klon_log = 1;

static int klon_read(struct klb_snap *s, int allow)
{
    int save, r; static DWORD last_state = 0xffffffffu, last_rules; static LONG told;
    if (klb_read(s)) return 1;
    if (!allow) return 0;
    save = klb_hud_online; klb_hud_online = 1;
    r = klb_read_hud(s);
    klb_hud_online = save;
    if (r && klon_log && (s->state != last_state || s->rules != last_rules) && InterlockedIncrement(&told) <= 40)
        klog("online: network round seen by the cosmetic parts: rules %08lx state 0x%lx%s", (unsigned long)s->rules, (unsigned long)s->state, s->state == KLB_ROUND ? " (= round runs, GUESS)" : "");
    if (r) { last_state = s->state; last_rules = s->rules; }
    return r;
}

static DWORD klon_money(const struct klb_snap *s)
{
    DWORD m = 0; int i;
    if (s->online) { for (i = 0; i < s->on_n && i < 16; i++) if (s->on_used[i] && s->on_money[i] > 0) m += (DWORD)s->on_money[i]; return m; }
    for (i = 0; i < s->n; i++) if (s->r[i].used) m += s->r[i].money;
    return m;
}

static void klon_init(void)
{
    klon_log = GetPrivateProfileIntA("Online", "Log", 1, klh_ini) != 0;
}

#endif /* KLONLINE_C */
