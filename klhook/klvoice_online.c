/*
 * klvoice_online.c - [Voice] Online=1: the LOCAL player's own Dead Men lines in an online Fragile Alliance round (2026-10-27, owner: online = Arcade).
 * Part of KLHook (klhook.c includes it after klhud_tags.c, SHIP and TEST alike). NOT RUN LIVE. READ ONLY: klonline_read.c's klor_read (needs
 * [Online] Read=1) names the local seat's heister character; klvoice.c's kvo_tick then swaps the speech-manager entries of THAT voice number
 * exactly as in Arcade (heap data of the LOCAL manager only; nothing is sent, no replicated object is written). Remote players stay stock.
 *   kvo_online_who(&w, name) -> 1 and a one-member klw_who for kvo_tick (rec = the local seat, ch = the character), name = "Kane".."Hutchison" or "".
 * GUESS V1: the voice number the local player's lines use online is his seat number (Arcade: data[rules+0x33e+record]; the online rules have no
 *   such table known). If the swapped entry is not the one the game says, the line stays stock (nothing breaks); the walk log says what it replaced.
 * GUESS V2: the local seat found as klhud.c does ([osd+0x10c4] player list, +0xefc). Seats above 7 are not handled (the voice table has 8 entries).
 * [Voice] OnlineDiag=0 (recommended off; log lines only): re-logs 'local seat' / 'online crew' when a seat's name changes (the stock hero is read for
 *   ~0.5 s at round start, then the chosen look), logs rules+0x33e once per such log, and klvoice.c's walk line lists the wanted voice numbers.
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

/* [Voice] OnlineCrew=1 (needs Online=1): every human row of klor_read speaks its DM voice on THIS client (default 0, recommended off until benched) */
static int kvo_crew_on(void)
{
    static int v = -1;
    if (v < 0) v = GetPrivateProfileIntA("Voice", "Online", 0, klh_ini) != 0 && GetPrivateProfileIntA("Voice", "OnlineCrew", 0, klh_ini) != 0;
    return v;
}
/* kvo_onl_seatname[8][32] (declared in klvoice.c): per seat: the heister name of that seat's member in the last who ("" = not in it) */

static int kvo_online_who_wide(struct klw_who *w, char *name, int wide)
{
    /* wide = 1 (kltalk.c [Voice] OnlineTalk=1): also the other human rows, as OnlineCrew=1 does; own cache [1] so klvoice.c's narrow who is not changed by it */
    static struct klw_who lastc[2]; static char lnamec[2][32], lsn[8][32]; static DWORD latc[2], ltryc[2], lround_rules, lhash; static int lround = -1, lokc[2];
#define last lastc[wide != 0]
#define lname lnamec[wide != 0]
#define lat latc[wide != 0]
#define ltry ltryc[wide != 0]
#define lok lokc[wide != 0]
    DWORD now = GetTickCount(), pl, li = 0, hsh = 0; struct klor_snap o; char scene[160]; int why = 0, wf = -1, wn = 0;   /* why: the refusal, for the 10-27 'who refused' line */
    static int toldwhy = -1, nwhy;
    name[0] = 0;
    if (lok && (DWORD)(now - ltry) < 400) { *w = last; snprintf(name, 32, "%s", lname); return 1; }   /* cached: klor_read is a scan */
    ltry = now ? now : 1;
    pl = klu_r.osd ? klh_rd32(klu_r.osd + KLU_O_PLIST) : 0;
    if (!pl) why = 1; else if (!klu_is_plist(pl)) why = 2; else if (!klh_rd(pl + 0xefc, &li, 1) || li >= 8) why = 3;
    if (!why) {
        int rd; klor_noev = 1; rd = klor_read(&o, (int)li); lok = rd && o.ok; klor_noev = 0;      /* this reader never takes the kill-feed events */
        if (!lok) why = rd ? 5 : 4;
        if (lok) {
            int k, f = -1;
            for (k = 0; k < o.n; k++) if (o.r[k].seat == (int)li) f = k;
            wf = f; wn = o.n;
            if (f < 0 || !o.r[f].name[0] || !klh_scene(scene, sizeof scene)) { lok = 0; why = f < 0 ? 6 : !o.r[f].name[0] ? 7 : 8; }
            else {
                memset(&last, 0, sizeof last); last.human = 0; last.rules = o.b.rules; last.state = o.b.state; last.n = 1;
                last.nchar = klor_s.src.n; last.wardrobe = klor_s.src.wardrobe;
                if (!klh_level_key(scene, last.key, sizeof last.key)) { lok = 0; why = 9; }
                last.m[0].rec = (int)li; last.m[0].ch = o.r[f].ch; last.m[0].model = o.r[f].model; last.m[0].actor = o.r[f].actor;
                snprintf(lname, sizeof lname, "%s", o.r[f].name);
                memset(lsn, 0, sizeof lsn); snprintf(lsn[li], sizeof lsn[li], "%s", o.r[f].name);
                if (kvo_crew_on() || wide) {                                           /* the other human rows, seats < 8 only (the voice table has 8 entries) */
                    for (k = 0; k < o.n && last.n < KLW_NREC; k++) {
                        if (k == f || o.r[k].seat < 0 || o.r[k].seat > 7 || !o.r[k].name[0]) continue;
                        last.m[last.n].rec = o.r[k].seat; last.m[last.n].ch = o.r[k].ch; last.m[last.n].model = o.r[k].model; last.m[last.n].actor = o.r[k].actor;
                        snprintf(lsn[o.r[k].seat], sizeof lsn[0], "%s", o.r[k].name); last.n++;
                    }
                }
                if (kvo_diag) { int a, b; for (a = 0; a < 8; a++) for (b = 0; lsn[a][b]; b++) hsh = hsh * 31 + (BYTE)lsn[a][b] + (DWORD)a * 7; }   /* OnlineDiag: the (seat, name) set */
                if (lok && (lround_rules != o.b.rules || lround != o.round || (kvo_diag && lhash != hsh))) {       /* once per round (OnlineDiag=1: and again whenever a seat's name changes or a human joins; bench ce5 froze the first stale snapshot) */
                    lround_rules = o.b.rules; lround = o.round; lhash = hsh;
                    if (kvo_diag) {                                                    /* read-only: does rules+0x33e (the Arcade voice table) hold anything on these rules? settles GUESS V1 */
                        BYTE vt[8]; memset(vt, 0xee, sizeof vt);
                        if (!KLH_RULES_CL_OK(klh_rd32(o.b.rules)) && klh_rd(o.b.rules + 0x33e, vt, 8)) klog("voice: diag: rules %08lx +0x33e = %02x %02x %02x %02x %02x %02x %02x %02x (Arcade: voice number per record; GUESS V1 says online voice = seat, compare with the seat table below)", o.b.rules, vt[0], vt[1], vt[2], vt[3], vt[4], vt[5], vt[6], vt[7]);      /* OOB: Cl rules are 0x334 bytes, +0x33e is past the end (Sv 0x3a8: in bounds, still no voice table) */
                        else klog("voice: diag: rules %08lx +0x33e is not readable", o.b.rules);
                    }
                    klog("voice: online: local seat %d plays '%s' (character %d of %d), round %d of %d; its lines use voice number %d (GUESS V1: the seat number)", (int)li, lname, last.m[0].ch, last.nchar, o.round, o.rounds, (int)li);
                    if (kvo.log >= 1 && last.n > 1) {
                        char mp[256]; int q, ml = 0; mp[0] = 0;
                        for (q = 0; q < last.n && ml < 200; q++) ml += snprintf(mp + ml, sizeof mp - ml, "%sseat %d=voice %d '%s'", q ? ", " : "", last.m[q].rec, last.m[q].rec, lsn[last.m[q].rec]);
                        klog("voice: online crew (OnlineCrew=1): %d humans: %s (GUESS V1: voice number = seat; seats above 7 skipped)", last.n, mp);
                    }
                }
            }
        }
    } else lok = 0;
    if (why != toldwhy && nwhy < 40) {                                                      /* 10-27 (bench Q27_DD01oob: the client never got a local seat): one line per change of the reason */
        static const char *const wtxt[] = { "none (ok)", "no player list (osd)", "not the FA player list", "local index unreadable or >= 8", "klor_read failed", "klor_read not ok", "no row with the local seat", "the local row has no name", "no scene", "no level key" };
        toldwhy = why; nwhy++;
        klog("voice: online who: %s (osd %08lx list %08lx local %lu, rows %d, local row %d)", wtxt[why], (unsigned long)klu_r.osd, (unsigned long)pl, (unsigned long)li, wn, wf);
    }
    if (!wide) memcpy(kvo_onl_seatname, lsn, sizeof lsn);
    if (lok) { lat = now ? now : 1; *w = last; snprintf(name, 32, "%s", lname); return 1; }
    if (lat && (DWORD)(now - lat) < 3000) { *w = last; snprintf(name, 32, "%s", lname); return 1; }    /* a short read failure does not flap the swaps */
    return 0;
#undef last
#undef lname
#undef lat
#undef ltry
#undef lok
}

static int kvo_online_who(struct klw_who *w, char *name) { return kvo_online_who_wide(w, name, 0); }

#endif /* KLVOICE_ONLINE_C */
