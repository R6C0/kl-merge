/*
 * klvoice_online.c - [Voice] Online=1: the LOCAL player's own Dead Men lines in an online Fragile Alliance round (2026-10-27, owner: online = Arcade).
 * Part of KLHook (klhook.c includes it after klhud_tags.c, SHIP and TEST alike). NOT RUN LIVE. READ ONLY: klonline_read.c's klor_read (needs
 * [Online] Read=1) names the local seat's heister character; klvoice.c's kvo_tick then swaps the speech-manager entries of THAT voice number
 * exactly as in Arcade (heap data of the LOCAL manager only; nothing is sent, no replicated object is written). Remote players stay stock.
 *   kvo_online_who(&w, name) -> 1 and a one-member klw_who for kvo_tick (rec = the local seat, ch = the character), name = "Kane".."Hutchison" or "".
 * GUESS V1: the voice number the local player's lines use online is his seat number (Arcade: data[rules+0x33e+record]; the online rules have no
 *   such table known). If the swapped entry is not the one the game says, the line stays stock (nothing breaks); the walk log says what it replaced.
 * GUESS V2: the local seat found as klhud.c does ([osd+0x10c4] player list, +0xefc). Seats above 7 are not handled (the voice table has 8 entries).
 * [Voice] OnlineTraits=0 (recommended off until benched; needs Online=1): kltalk.c's klk_tick and kltrait.c's kltt_tick take this who too (see kltrait.c ONLINE).
 * KLHook.ini [Voice] Online=0 (recommended off until benched); needs Enable=1, [Online] Read=1 and the Dead Men leaves in the level's .LOC.
 */
#ifndef KLVOICE_ONLINE_C
#define KLVOICE_ONLINE_C

/* the online round's character list as a klw_src, for kltrait.c ([Voice] OnlineTraits=1); 0 if klor_read has not read one yet */
static int kvo_online_src(struct klw_src *s)
{
    if (!klor_s.src.n) return 0;
    *s = klor_s.src; return 1;
}

static int kvo_online_who(struct klw_who *w, char *name)
{
    static struct klw_who last; static char lname[32]; static DWORD lat, ltry, lround_rules; static int lround = -1, lok;
    DWORD now = GetTickCount(), pl, li = 0; struct klor_snap o; char scene[160];
    name[0] = 0;
    if (lok && (DWORD)(now - ltry) < 400) { *w = last; snprintf(name, 32, "%s", lname); return 1; }   /* cached: klor_read is a scan */
    ltry = now ? now : 1;
    pl = klu_r.osd ? klh_rd32(klu_r.osd + KLU_O_PLIST) : 0;
    if (pl && klu_is_plist(pl) && klh_rd(pl + 0xefc, &li, 4) && li < 8) {
        klor_noev = 1; lok = klor_read(&o, (int)li) && o.ok; klor_noev = 0;      /* this reader never takes the kill-feed events */
        if (lok) {
            int k, f = -1;
            for (k = 0; k < o.n; k++) if (o.r[k].seat == (int)li) f = k;
            if (f < 0 || !o.r[f].name[0] || !klh_scene(scene, sizeof scene)) lok = 0;
            else {
                memset(&last, 0, sizeof last); last.human = 0; last.rules = o.b.rules; last.state = o.b.state; last.n = 1;
                last.nchar = klor_s.src.n; last.wardrobe = klor_s.src.wardrobe;
                if (!klh_level_key(scene, last.key, sizeof last.key)) lok = 0;
                last.m[0].rec = (int)li; last.m[0].ch = o.r[f].ch; last.m[0].model = o.r[f].model; last.m[0].actor = o.r[f].actor;
                snprintf(lname, sizeof lname, "%s", o.r[f].name);
                if (lok && (lround_rules != o.b.rules || lround != o.round)) {       /* once per round */
                    lround_rules = o.b.rules; lround = o.round;
                    klog("voice: online: local seat %d plays '%s' (character %d of %d), round %d of %d; its lines use voice number %d (GUESS V1: the seat number)", (int)li, lname, last.m[0].ch, last.nchar, o.round, o.rounds, (int)li);
                }
            }
        }
    } else lok = 0;
    if (lok) { lat = now ? now : 1; *w = last; snprintf(name, 32, "%s", lname); return 1; }
    if (lat && (DWORD)(now - lat) < 3000) { *w = last; snprintf(name, 32, "%s", lname); return 1; }    /* a short read failure does not flap the swaps */
    return 0;
}

#endif /* KLVOICE_ONLINE_C */
