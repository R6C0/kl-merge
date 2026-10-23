/*
 * kladren.c - ADRENALINE (track Y2, 2026-10-11 night). Part of KLHook (included by klhook.c AFTER kldown.c; its tick
 * runs BEFORE kld_tick). OFF unless [Adrenaline] Enable=1. NOT RUN IN THE GAME. Reading: re\adrenaline.md.
 *
 * The owner: 'an adrenaline feature so it speeds up the down player state and the ai heisters and you get a share of
 * their cut since you helped them' / 'if you get someone down like that you would be a traitor too but if you revive
 * them youd become normal again'.
 *
 * WHAT IT DOES (Arcade, a level that is not stock, session state 0x19, data writes only - no call, no patch):
 *   b. A DOWNED crew member is one of
 *        - an AI heister the GAME has put down (byte [actor+0x64c] set: the NPC's 'down not dead', which only happens
 *          with [Down] Bots=1 - re\player_down.md 11), or
 *        - the local human in the game's own knock-down ([D+4] 1 lying / 2 on the floor in kldown.c's fall / 3 getting up, D = [player+0x2948]).
 *      A HELPER is another crew record in play, no traitor, not down itself, within Range (a human helper, optionally
 *      only while he holds Use: NeedUse) or BotRange (an AI heister standing by a downed human - the escort holds
 *      about 3 m from him) of the downed man.
 *        a downed AI heister: his lie tick [[soldier+0x4b8]+0x14] is pulled earlier, Rate times as fast as time runs
 *        the downed human:    kld_s.meter (kldown.c's mash meter) is held at Meter or more, so the get-up speed
 *                             FlopBase + FlopPerPress x meter (at most FlopTop) is what a hard mash would give; with
 *                             HumanFast=1 also the game's own 'fast get-up' byte [D+0x29] (speed 2.5 in 0x478270).
 *   c. THE SHARE. When the helped man is UP and the helper had helped for MinHelp seconds: x = Share x what the helped
 *      man carries. The helper gets x - the local human into his banked total [score+0x38] (as klfedkit.c's Pay does:
 *      it survives the round), anybody else into his carried money [score+0x150+4i]; Take=1 takes x out of an AI
 *      heister's carried money (a human is never debited). WHY AT THE GET-UP AND NOT AT THE PAYOUT: 0x796410 pools what
 *      the escaped non-traitors carry and gives each THE SAME share, so a transfer between two escapees is invisible
 *      in the payout, and the payout's own fields were not read far enough to add to (re\adrenaline.md 4).
 *   d. THE TRAITOR MARK BY DOWNING. A human whose bullets put a crewmate down (rules slot 131 adds to his word
 *      [score+0x1b8+2*record] when he takes an NPC's last health - re\player_down.md 11.1 - in the pass the game's down
 *      byte appears) is marked as the game marks a killer (rules slot 129 = 0x8fb0d0, read whole in re\fed_kit.md 10.2):
 *      client flag 1 at [score+0x1d4+4*record] (what slot 115 = 0x7ca230 ORs in), the local player's byte
 *      [player+0x2726] = 1 (0x70f770 writes it and then tells the sense manager - NOT done here, ASSUMED harmless but it
 *      may mean the bots do not turn on him: live check A4), and with MarkFine=1 the game's -25,000 ([score+0x24] +=
 *      [tuning+0xc10]). When the crewmate he put down gets up and HE helped (MinHelp), the mark goes again (and the fine
 *      is given back) - but ONLY a mark this part gave: a flag that was set before is never touched, and as soon as any
 *      crewmate DIES while the mark stands, the mark is the game's to keep (a real kill makes it his in the game's own
 *      books; slot 129 skips a client that already has flag 1, so it would never be marked again).
 *   e. Per crew RECORD, nothing assumes record 0 except the two places that must (banked total, [player+0x2726]: only
 *      the local player's), so an online human can be added later. Off for a police human, off on a stock level.
 *
 * NOT DONE (re\adrenaline.md 2): (a) AI heisters going down at the killing hit IN PLACE OF DYING with no [Down] Bots - the
 * game's refusal (b / d / e of 0x70e0e0) is not established and the one way to be sure (a wrapped damage routine,
 * slot 96 = 0x8473a0) needs a private ZSoldier vtable that six other parts of this hook reject by its address.
 *
 * Keys ([Adrenaline]):
 *   Enable=0   Dry=0 (1 = log only; nothing is written)   Log=1 (2 = every pass with a helper, once a second)
 *   Range=2.5 (m, a human helper)   BotRange=4.0 (m, an AI helper of a downed human)   NeedUse=0 (1 = a human helper must
 *   hold Use: bit 2 of [player+0xa54], a GUESS of re\hud_popup.md 7.12 - log it with Log=2 before turning this on)
 *   Rate=3.0 (a downed AI heister's lie runs this many times faster)   Meter=3.0 (the human's mash meter floor)
 *   HumanFast=0 (ON BREAKS THE OWNER'S RULE 'NEVER FASTER THAN NORMAL')   MinHelp=1.0 (s; review 7: a walk past is not help)   Share=0.25   Take=1   ShareBot=1 (AI helpers earn a share too)   ShareBank=1
 *   Mark=0 (1 = the traitor mark for downing a crewmate: the attribution is ASSUMED, check A4; the bots may not turn on a marked human)   MarkFine=0
 *   Prompt=1 (2026-10-14, the owner: 'i dont get the option to do an adrenaline on someone and no ai does it on me'): the help was
 *            there but nothing on screen said so. Now the game's own centre announcement (0x468430, the routine klhud_popup.c uses;
 *            game thread) tells you: a crewmate is DOWN near you (PromptRange m) and to go to him; that you are giving him adrenaline
 *            while you stand by him; that an AI heister is coming to get YOU up / is giving you adrenaline; and the share when he is up.
 *            0 = silent as before.   PromptRange=12 (m)
 *   Anim=0 (2026-10-15, the owner: 'I want it to be the Dead Men revive where they get a syringe whilst kneeling'): 1 = YOU kneel and give a
 *            downed AI heister Dead Men's adrenaline shot (/Special_moves/Heal_wounded, its 55-frame player clip; section 'Anim' below).
 *            AnimFace=1 (turn to him, AnimDist=60 units from him, over AnimAlignFrames=10)  AnimInject=1 (at AnimInjectFrame=30 his lie
 *            ends: he gets up, if your help is MinHelp)  AnimRepeat=0  AnimLog=1 (2 = every refusal)  AnimSlot= (absent: '/Special_moves/
 *            Heal_wounded_DM' = Dead Men's exact clip where kl_fa_syringe.py put it, else Dog Days' '/Special_moves/Heal_wounded')
 *   BotAnim=1 (2026-10-16, worker aisyr): an AI HEISTER who helps a downed crewmate kneels and plays the same slot (his NPC set: Dead Men's
 *            Heal_Wounded_NPC) through the NPC graph's empty state; BotAnimNear=2.0 (m) BotAnimFace=1 BotAnimDist=60 BotAnimAlignFrames=9
 *            BotAnimHold=1 (a downed AI heister waits for the shot) BotAnimInject=1 (BotAnimInjectFrame=44 ends his lie) BotAnimRepeat=0
 *            BotAnimLog=1 BotAnimSlot=/Special_moves/Heal_wounded BotAnimTest=0 (a test key: every N s the bot nearest to you plays it)
 *            (section 'BotAnim')
 *   NeedUse=1 now (the owner: 'just use e for it like when picking up a gun'): you help only while you HOLD E (UseKey=0x45, a Windows
 *            virtual-key code, read while the game's window is in front) or the game's own Use bit; the prompt says 'Hold E' in Range.
 */
#define KLADREN_C

#define KAD_PLAYER_VT  0x00bb45f4             /* ZFFPlayer */
#define KAD_GAMEDATA   0x00dd265c
#define KAD_CLOCK      0x00dd2640             /* +0x48 the game's tick (1/1024 s) */
#define KAD_TUNING     0x0168d7c0
#define KAD_SOLDIER_VT 0x00bd0954
#define KAD_ROUND      0x19
#define KAD_M          100.0f                 /* world units a metre */

static struct {
    int on, dry, log, needuse, humanfast, share_bot, bank, mark, fine, take, bothelp, rush, rushvan;
    float range, brange, rate, meter, minhelp, share, rushrange, rushvanrange;
    int prompt, usekey; float prange;
} kad;

static struct kad_rec {
    DWORD actor;                              /* whose record this is (a new actor in the record = a new man) */
    BYTE down;                                /* he is down now */
    DWORD t_down, tick_down, tick_last;       /* GetTickCount / the game's tick at the down; the game's tick last pass */
    int by;                                   /* the human record whose bullets put him down, -1 = not known */
    DWORD hm[KLB_NREC];                       /* ms each other record helped him this down */
    DWORD fast;                               /* the human: [D+0x29] was written by us */
    float lie0;                               /* the AI heister: seconds of lying left when he went down (log) */
    DWORD sped;                               /* ms of speed-up given (log) */
    int mkn;                                  /* the mark was put on because of him (counted in kad_m[by]) */
    int paid;                                 /* a share was paid for this man this round (review 5: once per man per round; reset with the actor / the round) */
    int rusher;                               /* Rush: record + 1 of the AI heister sent to him (0 = none) */
    DWORD rush_at, rush_soldier;              /* when the last order went; that bot's soldier (the order is checked against it) */
    float rush_back[3]; int rush_have_back;   /* where that bot's defend block was before: he is sent back there when the man is up */
    int an_n, an_logged; DWORD an_tried;     /* Anim: shots played on him this down, refusals logged, the last try (GetTickCount) */
} kad_r[KLB_NREC];

static struct kad_mark {
    int on;                                   /* this part's mark stands on this human record */
    int n;                                    /* crewmates he put down and has not revived */
    int keep;                                 /* the mark is the game's now (a crewmate died, or the flag was not ours) */
    int fined; int fine;                      /* the fine put on, to give back */
    BYTE byte2726;                            /* the local player's byte before */
} kad_m[KLB_NREC];

static struct { DWORD rules, state; WORD kw[KLB_NREC]; BYTE kwok[KLB_NREC]; DWORD nextlog; BYTE use_last; DWORD use_dw; DWORD said_at, hint_at; int said_key; } kad_g;

/* ---------------------------------------------------------------- Prompt: the game's own centre announcement */

#define KAD_ANNOUNCE   0x00468430u            /* thiscall (ZFAAnnouncementDisplay *, const char *, float seconds), ret 8 (klhud_popup.c) */
#define KAD_ANN_VT     0x00bbdd34u
#define KAD_O_ANN      0x10a8                 /* osd + this = the announcement element */

/* the human holds Use: the game's own bit (bit 2 of [player+0xa54], a GUESS of re\hud_popup.md 7.12) OR the UseKey on the keyboard while
   the game's window is in front (2026-10-14, the owner: 'just use e for it like when picking up a gun') */
static int kad_use_held(DWORD pl)
{   /* user32 is the game's own (loaded long before a round): looked up, not linked - this DLL does not link user32 */
    static HWND (WINAPI *fgw)(void); static DWORD (WINAPI *wtp)(HWND, LPDWORD); static SHORT (WINAPI *aks)(int); static int tried;
    DWORD dw = 0, pid = 0; HWND fg;
    if (pl && klh_rd(pl + 0xa54, &dw, 4) && (dw & 2)) return 1;
    if (!kad.usekey) return 0;
    if (!tried) {
        HMODULE u = GetModuleHandleA("user32.dll"); tried = 1;
        if (u) { fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId"); aks = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState"); }
        if (!fgw || !wtp || !aks) klog("adren: user32's GetForegroundWindow / GetWindowThreadProcessId / GetAsyncKeyState not found: the E key is not read (the game's own Use bit still is)");
    }
    if (!fgw || !wtp || !aks || !(fg = fgw())) return 0;
    wtp(fg, &pid);
    return pid == GetCurrentProcessId() && (aks(kad.usekey) & 0x8000) != 0;
}

/* a crewmate's name as the crew list shows it (klhud_names.c), else a plain word */
static void kad_name(int i, char *out, int cap)
{
    const struct klnm_rec *q = (i >= 0 && i < KLW_NREC) ? &klnm_r.r[i] : 0;
    snprintf(out, cap, "%s", q && q->used && q->chr[0] ? q->chr : q && q->used && q->stock[0] ? q->stock : "your crewmate");
}

/* one message, at most one every `gap` ms unless the key changes; the element must be the stock class (or klhud_popup.c's copy) */
static void kad_say(int key, DWORD gap, const char *msg, float secs)
{
    static int code = -1; static char buf[160];
    static const BYTE say_code[8] = { 0x56, 0x57, 0x8b, 0x7c, 0x24, 0x0c, 0x8b, 0xc7 };          /* 0x468430 */
    DWORD now = GetTickCount(), osd, el, vt = 0;
    if (!kad.prompt || !kset_v[2] || kad.dry) return;           /* kset_v[2]: the menu's row, at once */
    if (key == kad_g.said_key && now - kad_g.said_at < gap) return;
    if (code < 0) { code = klu_same_code(KAD_ANNOUNCE, say_code, sizeof say_code); if (!code) klog("adren: prompt: 0x468430 is not the announcement routine this build knows: no prompts"); }
    if (!code || !klu.on || !(osd = klu_r.osd) || klu_r.fault || klh_rd32(osd) != KLU_OSD_VT) return;
    if (!(el = klh_rd32(osd + KAD_O_ANN)) || !klh_rd(el, &vt, 4)) return;
    if (vt != KAD_ANN_VT && vt != (DWORD)(DWORD_PTR)&klpu_evt[1]) return;
    snprintf(buf, sizeof buf, "%s", msg);                       /* the element may keep the pointer: a static buffer */
    ((void (__fastcall *)(void *, void *, const char *, float))(DWORD_PTR)KLH_VA(KAD_ANNOUNCE))((void *)(DWORD_PTR)el, 0, buf, secs);
    kad_g.said_key = key; kad_g.said_at = now;
    if (kad.log >= 2) klog("adren: prompt '%s'", buf);
}

/* ---------------------------------------------------------------- pure arithmetic (tested off the game)  */

/* the nearest helper: -> index in dist[] of the smallest dist <= lim[i], or -1. dist < 0 = not a candidate */
static int kad_pick(const float *dist, const float *lim, int n)
{
    int i, best = -1;
    for (i = 0; i < n; i++) {
        if (dist[i] < 0 || dist[i] > lim[i]) continue;
        if (best < 0 || dist[i] < dist[best]) best = i;
    }
    return best;
}

/* a downed AI heister's lie tick pulled earlier. cur = the tick he lies until, tick = now, dt = ticks since the last
   pass. -> the new tick (never earlier than tick + 2, never later than cur); *done = ticks taken off */
static DWORD kad_lie_step(DWORD cur, DWORD tick, DWORD dt, float rate, DWORD *done)
{
    long left = (long)(cur - tick), take, nl;
    *done = 0;
    if (left <= 2 || rate <= 1.0f || dt == 0 || dt > 512) return cur;      /* a pass longer than half a second is a stall: no catch-up */
    take = (long)((rate - 1.0f) * (float)dt);
    nl = left - take; if (nl < 2) nl = 2;
    *done = (DWORD)(left - nl);
    return tick + (DWORD)nl;
}

/* the share: Share x carried, rounded down, never negative, capped at carried */
static int kad_share(int carried, float share)
{
    double x;
    if (carried <= 0 || share <= 0) return 0;
    x = (double)carried * (double)share;
    if (x > (double)carried) x = (double)carried;
    return (int)x;
}

/* ---------------------------------------------------------------- reading a man's place */

static int kad_place(const struct klb_snap *s, int i, float pos[3])
{
    if (i == s->human) { DWORD pl; float feet[3]; return kle_human(&pl, feet, pos); }
    return kle_node(klh_rd32(s->r[i].actor + 4), pos, 0);
}

static float kad_dist(const float a[3], const float b[3])
{
    float dx = a[0] - b[0], dy = a[1] - b[1], dz = a[2] - b[2];
    return (float)sqrt(dx * dx + dy * dy + dz * dz);
}

/* ---------------------------------------------------------------- the money */

static int kad_carried(const struct klb_snap *s, int i, int *v)
{
    return klh_rd(s->score + 0x150 + 4 * i, v, 4) && *v >= 0 && *v < 100000000;
}

static int kad_put32(DWORD at, int v, const char *what) { return klh_data((void *)(DWORD_PTR)at, &v, 4, what); }

/* pay helper h for having helped record i up */
static void kad_pay(const struct klb_snap *s, int i, int h, DWORD ms)
{
    int have = 0, x, hv = 0, tot = 0, ok = kad_carried(s, i, &have);
    char who[24];
    snprintf(who, sizeof who, "%s", h == s->human ? "you" : (s->r[h].flags & 2) ? "TRAITOR" : "bot");
    if (!ok) { klog("adren: record %d helped record %d up (%lu ms), but his carried money cannot be read: no share", h, i, (unsigned long)ms); return; }
    x = kad_share(have, kad.share);
    if (x <= 0) { klog("adren: record %d (%s) helped record %d up (%lu ms): he carries $%d, so Share %.2f is $0", h, who, i, (unsigned long)ms, have, kad.share); return; }
    if (h != s->human && !kad.share_bot) { klog("adren: record %d (%s) helped record %d up: ShareBot=0, no share ($%d would be)", h, who, i, x); return; }
    if (kad.dry) { klog("adren: Dry - record %d (%s) WOULD get $%d (Share %.2f of the $%d record %d carries)%s", h, who, x, kad.share, have, i,
                        kad.take ? "; and record i would lose it" : ""); return; }
    if (h == s->human && kad.bank) {
        if (!klh_rd(s->score + 0x38, &tot, 4) || !kad_put32(s->score + 0x38, tot + x, "score: the banked total (the adrenaline share)")) return;
        klog("adren: SHARE - record %d (you) gets $%d (Share %.2f of the $%d record %d carries; helped %lu ms), banked: [score+0x38] %d -> %d", h, x, kad.share, have, i, (unsigned long)ms, tot, tot + x);
    } else {
        if (!kad_carried(s, h, &hv) || !kad_put32(s->score + 0x150 + 4 * h, hv + x, "score: the helper's carried money (the adrenaline share)")) return;
        klog("adren: SHARE - record %d (%s) gets $%d (Share %.2f of the $%d record %d carries; helped %lu ms), carried: $%d -> $%d", h, who, x, kad.share, have, i, (unsigned long)ms, hv, hv + x);
    }
    /* review 5: the share must not make money - with Take=1 it comes out of the helped man's carried money, a human's too */
    if (kad.take && kad_put32(s->score + 0x150 + 4 * i, have - x, "score: the helped man's carried money (the adrenaline share is his cut)"))
        klog("adren: record %d (%s) carries $%d now (was $%d: the share is out of his cut)", i, i == s->human ? "you" : "bot", have - x, have);
    else if (!kad.take) klog("adren: Take=0 - the share of $%d is NEW money (nobody is debited)", x);
}

/* ---------------------------------------------------------------- the traitor mark */

static DWORD kad_flagat(const struct klb_snap *s, int h) { return s->score + 0x1d4 + 4 * h; }

static void kad_mark_on(const struct klb_snap *s, int h, int bot)
{
    DWORD fl = 0, pl = 0; BYTE b = 0; float feet[3], np[3];
    if (!kad.mark || h < 0 || h >= s->n) return;
    if (!klh_rd(kad_flagat(s, h), &fl, 4)) return;
    if (kad_m[h].on) { kad_m[h].n++; klog("adren: MARK - record %d put record %d down too: %d crewmate(s) down by his bullets", h, bot, kad_m[h].n); return; }
    if (fl & 0xd) { klog("adren: record %d put record %d down, but his client flags are %08lx already (traitor / dead / police): no mark of ours, nothing to take off later", h, bot, (unsigned long)fl); return; }
    if (kad.dry) { klog("adren: Dry - record %d WOULD be marked a traitor for putting record %d down (client flags %08lx -> %08lx)", h, bot, (unsigned long)fl, (unsigned long)(fl | 1)); return; }
    fl |= 1;
    if (!klh_data((void *)(DWORD_PTR)kad_flagat(s, h), &fl, 4, "client flags: the traitor flag (adrenaline: he put a crewmate down)")) return;
    kad_m[h].on = 1; kad_m[h].n = 1; kad_m[h].keep = 0; kad_m[h].fined = 0;
    if (h == s->human && kle_human(&pl, feet, np) && klh_rd(pl + 0x2726, &b, 1)) {
        BYTE one = 1; kad_m[h].byte2726 = b;
        if (b != 1) klh_data((void *)(DWORD_PTR)(pl + 0x2726), &one, 1, "player: the traitor byte (adrenaline)");
    }
    if (kad.fine && h == s->human) {
        DWORD tun = klh_rd32((DWORD_PTR)KLH_VA(KAD_TUNING)); int f = tun ? (int)klh_rd32(tun + 0xc10) : 0, cur = 0;
        if (f < 0 && f > -10000000 && klh_rd(s->score + 0x24, &cur, 4) && kad_put32(s->score + 0x24, cur + f, "score: the traitor fine (adrenaline)")) { kad_m[h].fined = 1; kad_m[h].fine = f; }
    }
    klog("adren: MARK - record %d is a TRAITOR (client flags %08lx -> %08lx) because his bullets put record %d down%s; he is normal again when record %d gets up and he helped", h, (unsigned long)(fl & ~1u), (unsigned long)fl, bot,
         kad_m[h].fined ? "; the game's fine is on his round line" : "", bot);
}

static void kad_mark_off(const struct klb_snap *s, int h, int bot, const char *why)
{
    DWORD fl = 0, pl = 0; float feet[3], np[3];
    if (h < 0 || h >= KLB_NREC || !kad_m[h].on) return;
    if (kad_m[h].n > 0) kad_m[h].n--;
    if (kad_m[h].n > 0) { klog("adren: record %d is still marked: %d crewmate(s) he put down are not up yet (%s)", h, kad_m[h].n, why); return; }
    if (kad_m[h].keep) { klog("adren: record %d keeps the mark: it is the game's now (%s)", h, why); kad_m[h].on = 0; return; }
    if (kad.dry || !klh_rd(kad_flagat(s, h), &fl, 4)) { kad_m[h].on = 0; return; }
    if (fl & 1) {
        fl &= ~1u; klh_data((void *)(DWORD_PTR)kad_flagat(s, h), &fl, 4, "client flags: the traitor flag off (adrenaline: he revived the crewmate)");
    }
    if (h == s->human && kle_human(&pl, feet, np)) { BYTE z = kad_m[h].byte2726; klh_data((void *)(DWORD_PTR)(pl + 0x2726), &z, 1, "player: the traitor byte back (adrenaline)"); }
    if (kad_m[h].fined) { int cur = 0; if (klh_rd(s->score + 0x24, &cur, 4)) kad_put32(s->score + 0x24, cur - kad_m[h].fine, "score: the traitor fine given back (adrenaline)"); }
    klog("adren: UNMARK - record %d is a normal heister again (client flags %08lx)%s - record %d is up (%s)", h, (unsigned long)fl, kad_m[h].fined ? "; the fine is given back" : "", bot, why);
    kad_m[h].on = 0; kad_m[h].fined = 0;
}

/* ---------------------------------------------------------------- Rush: an AI heister runs to a downed crewmate */

static int kad_rushing(int h)                 /* is record h already sent to somebody? */
{
    int i;
    for (i = 0; i < KLB_NREC; i++) if (kad_r[i].down && kad_r[i].rusher == h + 1) return 1;
    return 0;
}

/* a place 0.8 m from the downed man, on the bot's side */
static void kad_beside(const float man[3], const float bot[3], float out[3])
{
    float dx = bot[0] - man[0], dz = bot[2] - man[2], l = (float)sqrt(dx * dx + dz * dz);
    memcpy(out, man, 12);
    if (l > 1.0f) { out[0] = man[0] + dx / l * 0.8f * KAD_M; out[2] = man[2] + dz / l * 0.8f * KAD_M; }
}

/* RushVan (2026-10-18, 3f's Vault run N1018_L19): while the escape vehicle is called, comes or waits (s->veh 1 .. 5) the crew runs to it;
   a revive rush pulled the called bots back across the police (7 -> 1, 6 -> 7, 1 -> 6, all four dead 9 - 27 m from the doors) and the
   rush-back sent record 1 to its old defend place 47 m away in the middle of the wait. RushVan=1: no rush-back then (the follow / reach
   orders take him on), and a new rush only from a bot within RushVanRange (default 8 m, GUESS). 0 = as before (default). */
static int kad_vanlive(const struct klb_snap *s) { return kad.rushvan && s->veh >= 1 && s->veh <= 5; }

static void kad_rush(const struct klb_snap *s, int i, float pos[][3], const int *havepos, const BYTE *dn, DWORD now)
{
    struct kad_rec *k = &kad_r[i]; struct kle_e e; float bp[3], want[3], got[3], d; char why[100]; DWORD actor, soldier; int h, best = -1, r; float bd = 0;
    float range = kad_vanlive(s) && kad.rushvanrange < kad.rushrange ? kad.rushvanrange : kad.rushrange;
    if (!kad.rush || !havepos[i] || now - k->t_down < 600) return;
    if (k->rusher) {                                                       /* already sent: again every 2.5 s while he is not there yet */
        h = k->rusher - 1;
        if (now - k->rush_at < 2500 || !havepos[h] || dn[h]) return;
        if (!kle_bot(s, h, &actor, &soldier, bp, why) || soldier != k->rush_soldier) { klog("adren: RUSH - record %d no longer runs to record %d (%s)", h, i, why[0] ? why : "another soldier"); k->rusher = 0; k->rush_have_back = 0; return; }
        if ((d = kad_dist(bp, pos[i])) <= kad.brange * KAD_M * 0.9f) { k->rush_at = now; return; }
        memset(&e, 0, sizeof e); e.rec = h; e.actor = actor; e.soldier = soldier;
        kad_beside(pos[i], bp, want);
        kltr_set("adren", "RUSH: ordered again beside the downed heister", -1);
        kle_gap_exempt = 1; r = kle_order2(&e, want, got, why, kad.dry); kle_gap_exempt = 0; k->rush_at = now;   /* 2026-10-18: a revive rush is never held back by OrderGap */
        if (kad.log >= 2) klog("adren: RUSH - record %d is %.1f m from record %d: ordered again (%s)", h, d / KAD_M, i, r == 1 ? "called" : r == 2 ? "dry" : why);
        return;
    }
    for (h = 0; h < s->n; h++) {
        const struct klb_rec *q = &s->r[h];
        if (h == i || !q->used || !(q->flags & 1) || (q->flags & 2) || q->status != 0 || dn[h] || !havepos[h]) continue;
        if (kle_r.used[h] && i != s->human) continue;                      /* an escort stays with the human unless the human is the one down */
        if (kad_rushing(h)) continue;
        if (fabs(pos[h][1] - pos[i][1]) > 3.0f * KAD_M) continue;          /* another floor: the path may be long */
        d = kad_dist(pos[h], pos[i]);
        if (d > range * KAD_M) continue;
        if (best < 0 || d < bd) { best = h; bd = d; }
    }
    if (best < 0) return;
    if (bd <= kad.brange * KAD_M * 0.9f) return;                          /* somebody is by him already */
    if (!kle_bot(s, best, &actor, &soldier, bp, why)) { if (kad.log >= 2) klog("adren: RUSH - record %d cannot be sent to record %d: %s", best, i, why); return; }
    memset(&e, 0, sizeof e); e.rec = best; e.actor = actor; e.soldier = soldier;
    k->rush_have_back = kle_block(soldier, k->rush_back) && (k->rush_back[0] || k->rush_back[1] || k->rush_back[2]);
    kad_beside(pos[i], bp, want);
    kltr_set("adren", "RUSH: sent to the downed heister", -1);
    kle_gap_exempt = 1; r = kle_order2(&e, want, got, why, kad.dry); kle_gap_exempt = 0;
    if (!r) { klog("adren: RUSH - record %d not sent to record %d: %s", best, i, why); k->rush_have_back = 0; return; }
    k->rusher = best + 1; k->rush_at = now; k->rush_soldier = soldier;
    klog("adren: RUSH - record %d (%s) runs to record %d (%s), %.1f m away, to (%.0f, %.0f, %.0f)%s", best, kle_r.used[best] ? "your escort" : "bot", i, i == s->human ? "you" : "bot", bd / KAD_M,
         want[0], want[1], want[2], r == 2 ? " - DRY: not called" : "");
    if (kad.prompt && i == s->human && r == 1) { char nm[48], msg[160]; kad_name(best, nm, sizeof nm); snprintf(msg, sizeof msg, "%s is coming to get you up - adrenaline (%.0f m)", nm, bd / KAD_M); kad_say(310 + best, 0, msg, 3.0f); }      /* 2026-10-15, the owner: 'where's the adrenaline, i havent seen it' */
}

/* the man is up (or gone): the bot that ran to him goes back to where his own orders had him */
static void kad_rush_end(const struct klb_snap *s, int i, const char *why_)
{
    struct kad_rec *k = &kad_r[i]; struct kle_e e; float bp[3], got[3]; char why[100]; DWORD actor, soldier; int h = k->rusher - 1, r;
    if (!k->rusher) return;
    k->rusher = 0;
    if (!k->rush_have_back) { klog("adren: RUSH - record %d is done with record %d (%s); his own orders take him on", h, i, why_); return; }
    k->rush_have_back = 0;
    if (kad_vanlive(s)) { klog("adren: RUSH - record %d is done with record %d (%s): NOT sent back - the vehicle is called or waits (state %u, RushVan=1): his own orders take him on", h, i, why_, s->veh); return; }
    if (kle_r.used[h]) { klog("adren: RUSH - record %d (your escort) is done with record %d (%s): the escort takes him back", h, i, why_); return; }
    if (!kle_bot(s, h, &actor, &soldier, bp, why) || soldier != k->rush_soldier) { klog("adren: RUSH - record %d is done with record %d (%s); not sent back (%s)", h, i, why_, why); return; }
    memset(&e, 0, sizeof e); e.rec = h; e.actor = actor; e.soldier = soldier;
    kltr_set("adren", "RUSH done: back to the place it left", -1);
    kle_gap_exempt = 1; r = kle_order2(&e, k->rush_back, got, why, kad.dry); kle_gap_exempt = 0;   /* the rush-back is a one-shot: never refused */
    klog("adren: RUSH - record %d is done with record %d (%s): sent back to (%.0f, %.0f, %.0f) (%s)", h, i, why_, k->rush_back[0], k->rush_back[1], k->rush_back[2], r == 1 ? "called" : r == 2 ? "dry" : why);
}

/* ---------------------------------------------------------------- Anim: Dead Men's adrenaline shot, played by the human helper
 *
 * 2026-10-15, the owner: 'what animation plays for when they adrenaline you - I want it to be the Dead Men revive where they get a syringe
 * whilst kneeling'. Until now nothing played: the helper only stood by. With [Adrenaline] Anim=1 the LOCAL HUMAN, when he becomes the
 * helper of a downed AI heister, kneels and gives him the shot with Dead Men's own clip.
 *
 * THE CLIP (FILE, measured, re\adrenaline_anim.md): slot '/Special_moves/Heal_wounded' -> 'anim:Special_Moves/Heal_Wounded#Heal_Wounded_01',
 *   55 frames (2.2 s), no event, the PLAYERS' sets (Kane, Lynch); the NPC sets play Heal_Wounded_NPC (73 frames, events 5 @ 0 and 18) for the
 *   same slot. It is in ALL 20 Dead Men levels and in every stock Dog Days .ANM AND every build of ours (DM01 .. DM09 checked): no merge.
 *   Pose (kl_animsheet, legend rows 60/61): KNEELS 0-19, bent 20-32 (the shot), KNEELS 33-49, up 50-54. Dead Men played it from
 *   ZFFActionHealWounded (kaneandlynch vtable 0x966998), which also showed a child geom 'syringe' (0x601540); Dog Days kept the class
 *   (kl2 vtable 0xbb54fc, player factory kind 0x12 at 0x83985f) but gives it '/Special_moves/Heal_Down_not_dead' (19 frames,
 *   [player+0x998] / crouched +0x99c, filled at 0x8f6064) and a PLAYER target ([player+0xd34]; its Start 0x6244b0 calls the target's
 *   vt +0x340): not usable on an AI heister. No build has a syringe prop (Dead Men's 'Items_Dynamic/Syringe_01' is not converted): the
 *   hand is empty.
 * THE MOVE (klfreeclimb.c's form, luvsic's 'A Newer Perspective' climb.inc - credit to him): a REAL ZFFActionVaultOver (kind 0x2B, the
 *   player's factory vt +0x384) whose vptr points at a copy of its vtable in this DLL (slots 2 Start, 4 Update, 5 End, 10 AnimEnd ours);
 *   started by the player's dispatcher (vt +0x370). Start: leave cover (0x5fcb80) as the stock start does, collision off (vt +0x560; the
 *   stock End 0x82f780 gives it back through vt +0x564), Play the clip (vt +0x204), Face=1: ONE AlignTo (vt +0x208) that turns him to the
 *   downed man and puts him Dist units from him over AlignFrames frames (with the collision off the clip's root does not move him).
 *   Update: the stock vault update (camera), ends at the clip's end / a lost channel / a time-out. End: +0x38 / +0x68 = where he is (the
 *   stock End teleports there), then the stock End. CEG: no code byte or vtable of kl2.exe is changed (the copy is ours).
 * THE SHOT: Inject=1 - at InjectFrame (30: the end of the bent phase, a GUESS from the pose) the downed man's lie tick [dnd+0x14] is set
 *   to 2 ticks from now, so the game's own get-up starts (as Rate does, at once) - IF the human's help this down is MinHelp or more.
 * WHEN: the human is the nearest helper (the same test as the help: Range, NeedUse), not acting, standing/walking (movement 2 / 3), not down,
 *   the bot lies; once per down unless Repeat=1 (again 0.3 s after the clip while he still lies and is still helped). Any fault: logged,
 *   unwound, the anim is off for the session (the help itself goes on).
 * NOT DONE (re\adrenaline_anim.md): an AI heister playing it (no NPC state for an arbitrary slot was found: the NPC graph 0x730be0 has
 *   no heal state; the only proven NPC route is a level MiniCutscene act), the downed man's 'receive' clip (Dead Men has none: its downed
 *   man lies and gets up with the normal rise).
 */
#ifndef KAD_TEST_NOANIM
#define KAD_AN_SLOT_DEF "/Special_moves/Heal_wounded"
#define KAD_AN_SLOT_DM  "/Special_moves/Heal_wounded_DM"   /* Dead Men's own clip, added by claude_stage\agents\syringe\kl_fa_syringe.py apply */
static float kad_inif(const char *key, const char *def, float lo, float hi);

static struct { int on, face, repeat, inject, alignf, injectf, log, userslot; float dist; char slot[96]; } kad_ao;
static struct {
    int active, dead, startT, did560, frames, rec, injected, animEndLogs;
    DWORD act, P, clip, anim, anim0, dnd, soldier; int animId; float from, to;
    float M[9], Pf[3], Final[3]; const char *endReason; DWORD ended_at;
} kad_an;
static DWORD kad_an_vt[13];
static BYTE kad_an_edge[0x80];

static int kad_an_filter(EXCEPTION_POINTERS *ep, const char *what)
{
    DWORD code = ep->ExceptionRecord->ExceptionCode; CONTEXT *c = ep->ContextRecord;
    switch (code) {
    case EXCEPTION_ACCESS_VIOLATION: case EXCEPTION_ILLEGAL_INSTRUCTION: case EXCEPTION_PRIV_INSTRUCTION:
    case EXCEPTION_INT_DIVIDE_BY_ZERO: case EXCEPTION_INT_OVERFLOW: case EXCEPTION_FLT_DENORMAL_OPERAND:
    case EXCEPTION_FLT_DIVIDE_BY_ZERO: case EXCEPTION_FLT_INEXACT_RESULT: case EXCEPTION_FLT_INVALID_OPERATION:
    case EXCEPTION_FLT_OVERFLOW: case EXCEPTION_FLT_STACK_CHECK: case EXCEPTION_FLT_UNDERFLOW: case EXCEPTION_BREAKPOINT: break;
    default: return EXCEPTION_CONTINUE_SEARCH;
    }
    if (klh_exe_ok && c->Eip == (DWORD)(DWORD_PTR)KLH_VA(KL2_PROBE)) return EXCEPTION_CONTINUE_SEARCH;     /* Steam's probe: its own handler */
    klog("adren: anim FAULT %08lx at %08lx (address %08lx) in %s; eax=%08lx ecx=%08lx edx=%08lx esi=%08lx edi=%08lx esp=%08lx",
         code, c->Eip, ep->ExceptionRecord->NumberParameters > 1 ? (DWORD)ep->ExceptionRecord->ExceptionInformation[1] : 0,
         what, c->Eax, c->Ecx, c->Edx, c->Esi, c->Edi, c->Esp);
    return EXCEPTION_EXECUTE_HANDLER;
}
static int kad_an_guard(const char *what, int (*fn)(void *), void *arg)
{   /* fn(arg), or -1 after a fault (klfreeclimb.c's klfc_guard with this part's own log line) */
    int r; WORD cw = 0;
    __asm fnstcw cw
    __try { r = fn(arg); }
    __except (kad_an_filter(GetExceptionInformation(), what)) {
        __asm fninit
        __asm fldcw cw
        r = -1;
    }
    return r;
}
static void kad_an_disable(const char *where)
{
    kad_an.dead = 1;
    klog("adren: anim DISABLED for this session (fault in %s); the help without the animation goes on", where);
}
static float kad_an_cur(void)
{
    if (!kad_an.anim || klh_rd32(kad_an.anim) != kad_an.anim0) return -1.0f;
    return klfc_f(kad_an.anim + 4);
}

/* his pose turned about the world up axis so that he FACES `to` (rows: +Z = his back, up, +X - klfc_pose); out = M turned */
static int kad_an_face(const float M[9], const float feet[3], const float to[3], float out[9])
{
    float bx = M[0], bz = M[2], tx = -(to[0] - feet[0]), tz = -(to[2] - feet[2]), lb = (float)sqrt(bx * bx + bz * bz), lt = (float)sqrt(tx * tx + tz * tz), s, c;
    int r;
    if (lb < 1e-3f || lt < 1e-3f) { memcpy(out, M, 36); return 0; }
    bx /= lb; bz /= lb; tx /= lt; tz /= lt;                         /* the back now / the back wanted (away from him) */
    s = bz * tx - bx * tz; c = bx * tx + bz * tz;                   /* Ry(a) with x' = x c + z s, z' = -x s + z c maps b onto t */
    for (r = 0; r < 3; r++) {
        float x = M[3 * r], y = M[3 * r + 1], z = M[3 * r + 2];
        out[3 * r] = x * c + z * s; out[3 * r + 1] = y; out[3 * r + 2] = -x * s + z * c;
    }
    return 1;
}

static int kad_an_start_body(void *arg)
{
    DWORD self = (DWORD)(DWORD_PTR)arg, pl = klh_rd32(self + 8), anim, zero = 0; int ok;
    if (!kad_an.active || kad_an.act != self || pl != kad_an.P) { klog("adren: anim START on an unknown record"); return 0; }
    if (klh_rd32(pl + 0x2810)) KLFC_CALL(void (__fastcall *)(DWORD, DWORD), KLFC_LEAVECOVER)(pl, 0);       /* the stock vault start's prep */
    klfc_put(pl + 0x2d60, &zero, 4, "adren anim: vault offer");
    KLFC_PTR(void (__fastcall *)(DWORD, DWORD), klfc_vf(pl, 0x560))(pl, 0); kad_an.did560 = 1;
    anim = KLFC_PTR(DWORD (__fastcall *)(DWORD, DWORD, DWORD, int), klfc_vf(pl, 0x204))(pl, 0, kad_an.clip, 1);
    if (!klfc_ok(anim, 0x20)) { klog("adren: anim START Play failed (%08lx)", anim); kad_an.endReason = "playanim"; return 0; }
    klfc_put(self + 0xc, &anim, 4, "adren anim: action channel");
    kad_an.anim = anim; kad_an.anim0 = klh_rd32(anim); kad_an.animId = (int)klh_rd32(anim + 0x18);
    kad_an.from = klfc_f(anim + 8); kad_an.to = klfc_f(anim + 0xc);
    if (kad_ao.face) {
        float n = (float)kad_ao.alignf, span = kad_an.to - kad_an.from - 1.0f;
        if (n > span) n = span;
        if (n < 1.0f) n = 1.0f;
        ok = KLFC_PTR(BYTE (__fastcall *)(DWORD, DWORD, const float *, const float *, float), klfc_vf(pl, 0x208))(pl, 0, kad_an.M, kad_an.Final, n) & 0xff;
        if (!ok) klog("adren: anim START AlignTo refused (no root channel?) - he kneels where he stands");
    }
    if (kad_ao.log)
        klog("adren: anim START act=%08lx anim=%08lx id=%d from=%.1f to=%.1f Final=(%.0f,%.0f,%.0f) face=%d - record %d gets the shot",
             self, anim, kad_an.animId, kad_an.from, kad_an.to, kad_an.Final[0], kad_an.Final[1], kad_an.Final[2], kad_ao.face, kad_an.rec);
    return 1;
}
static BYTE __fastcall kad_an_v_start(DWORD self, DWORD edx)
{
    int r; (void)edx;
    r = kad_an_guard("Start", kad_an_start_body, (void *)(DWORD_PTR)self);
    if (r < 0) { kad_an_disable("Start"); kad_an.endReason = "fault"; return 0; }
    return (BYTE)(r == 1);
}
static int kad_an_update_body(void *arg)
{
    DWORD self = (DWORD)(DWORD_PTR)arg; int r, T; float cur;
    r = KLFC_CALL(BYTE (__fastcall *)(DWORD, DWORD), KLFC_V_UPDATE)(self, 0) & 0xff;      /* stock: the camera follows */
    if (!kad_an.active || kad_an.act != self) return r;
    cur = kad_an_cur(); T = klfc_T();
    if (cur < 0) { kad_an.endReason = "channel lost"; return 0; }
    if (kad_ao.inject && !kad_an.injected && cur >= (float)kad_ao.injectf) kad_an.injected = 1;           /* the tick applies it (1 = due) */
    if (T - kad_an.startT > kad_an.frames * 1024 / 25 + 1024) { kad_an.endReason = "timeout"; return 0; }
    if (cur >= kad_an.to - 0.5f) { kad_an.endReason = "clip end"; return 0; }
    return r;
}
static BYTE __fastcall kad_an_v_update(DWORD self, DWORD edx)
{
    int r; (void)edx;
    r = kad_an_guard("Update", kad_an_update_body, (void *)(DWORD_PTR)self);
    if (r < 0) { kad_an_disable("Update"); kad_an.endReason = "fault"; return 0; }
    return (BYTE)(r != 0);
}
struct kad_an_ae { DWORD self; int id; };
static int kad_an_animend_body(void *arg)
{
    struct kad_an_ae *a = (struct kad_an_ae *)arg;
    if (!kad_an.active || kad_an.act != a->self) return 1;
    if (kad_an_cur() >= 0 && a->id == kad_an.animId) { kad_an.endReason = "animend"; return 1; }
    if (kad_an.animEndLogs++ < 5 && kad_ao.log >= 2) klog("adren: anim: another channel ended (id %d, ours %d) - ignored", a->id, kad_an.animId);
    return 0;                                                       /* the vault's own slot 10 says yes to ANY channel (re\climb.md 1.3) */
}
static BYTE __fastcall kad_an_v_animend(DWORD self, DWORD edx, int id)
{
    struct kad_an_ae a; int r; (void)edx;
    a.self = self; a.id = id;
    r = kad_an_guard("AnimEnd", kad_an_animend_body, &a);
    if (r < 0) { kad_an_disable("AnimEnd"); kad_an.endReason = "fault"; return 1; }
    return (BYTE)(r != 0);
}
static int kad_an_end_body(void *arg)
{
    DWORD self = (DWORD)(DWORD_PTR)arg, pl = klh_rd32(self + 8); int mine = kad_an.active && kad_an.act == self; float cur = mine ? kad_an_cur() : -1.0f, M[9], f[3] = { 0, 0, 0 };
    if (klfc_pose(pl, M, f)) { klfc_put(self + 0x38, M, sizeof M, "adren anim: end rotation"); klfc_put(self + 0x68, f, 12, "adren anim: end place"); }   /* the stock End teleports there */
    if (!mine || kad_an.did560) KLFC_CALL(void (__fastcall *)(DWORD, DWORD), KLFC_V_END)(self, 0);      /* collision back (vt +0x564), stance, proxy */
    else KLFC_CALL(void (__fastcall *)(DWORD, DWORD), KLFC_SYNC)(pl, 0);
    if (kad_ao.log) klog("adren: anim END reason=%s frame=%.1f feet=(%.0f,%.0f,%.0f) shot=%s%s", kad_an.endReason ? kad_an.endReason : "engine", cur, f[0], f[1], f[2],
                         kad_an.injected == 2 ? "given" : kad_an.injected == 3 ? "not counted (help too short)" : kad_an.injected ? "due" : "no", mine ? "" : " (unknown record)");
    if (mine) { int rec = kad_an.rec, dead = kad_an.dead; memset(&kad_an, 0, sizeof kad_an); kad_an.dead = dead; kad_an.rec = rec; kad_an.ended_at = GetTickCount(); }
    return 0;
}
static void __fastcall kad_an_v_end(DWORD self, DWORD edx)
{
    (void)edx;
    if (kad_an_guard("End", kad_an_end_body, (void *)(DWORD_PTR)self) < 0) { int rec = kad_an.rec; kad_an_disable("End"); memset(&kad_an, 0, sizeof kad_an); kad_an.dead = 1; kad_an.rec = rec; }
}

/* why the human cannot start it now (0 = he can): klfreeclimb.c's precondition without the ledge parts */
static const char *kad_an_precond(DWORD P, int T)
{
    DWORD fl = 0; BYTE b = 0; int id;
    if (kad_an.dead) return "anim disabled after a fault";
    if (kad_an.active) return "the shot is running";
    if (klfc_c.active) return "climbing";
    if (klh_rd32(P + 0x6b0) != P + 0xdb0) return "movement table (MiniScene?)";
    id = klfc_movid(P);
    if (id != 2 && id != 3) return "not standing / walking";
    if (klfc_cur_act(P)) return "an action runs";
    if (T - (int)klh_rd32(P + 0x2c48) < 512) return "< 0.5 s since his last action";
    if (klh_rd(P + 0xd29, &b, 1) && b) return "a use action runs";
    if (klh_rd(P + 0xed0, &fl, 4) && (fl & 0x80)) return "input blocked";
    if (klh_rd32(P + 0xd50) || klh_rd32(P + 0xd44)) return "seat / carrier";
    if (!klh_rd(P + 0x2720, &b, 1) || !(b & 2)) return "not the local human";
    if (klh_rd(P + 0x2954, &b, 1) && b) return "he is down himself";
    return 0;
}

struct kad_an_go { DWORD P; int rec; DWORD dnd, soldier; float to[3]; const char *why; };
static int kad_an_go_body(void *arg)
{
    struct kad_an_go *g = (struct kad_an_go *)arg; DWORD P = g->P, act, clip, vt, zero = 0, ptr; BYTE z2[2] = { 0, 0 }; int id, T = klfc_T(), i;
    float M[9], Pf[3], dx, dz, l; const char *sl = kad_ao.slot;
    if ((g->why = kad_an_precond(P, T)) != 0) return 0;
    id = kad_ao.userslot ? -1 : klq_slot(P, KAD_AN_SLOT_DM);        /* a build with Dead Men's exact clip: that one */
    if (id >= 0) sl = KAD_AN_SLOT_DM; else id = klq_slot(P, kad_ao.slot);
    if (id < 0) { g->why = "the clip's slot is not in this level's .ANM"; return 0; }
    clip = KLFC_CALL(DWORD (__fastcall *)(DWORD, DWORD, DWORD), KLFC_CLIPVAR)(P, 0, (DWORD)id);
    if (!klfc_ok(clip, 0x68)) { g->why = "the slot has no clip in his set"; return 0; }
    if (!klfc_pose(P, M, Pf)) { g->why = "his pose cannot be read"; return 0; }
    if (!kad_an_vt[1]) {
        kad_an_vt[0] = klh_rd32((DWORD_PTR)KLH_VA(KLFC_VAULT_VT - 4));
        for (i = 0; i < 12; i++) kad_an_vt[1 + i] = klh_rd32((DWORD_PTR)KLH_VA(KLFC_VAULT_VT + 4 * i));
        kad_an_vt[1 + 2] = (DWORD)(DWORD_PTR)kad_an_v_start;
        kad_an_vt[1 + 4] = (DWORD)(DWORD_PTR)kad_an_v_update;
        kad_an_vt[1 + 5] = (DWORD)(DWORD_PTR)kad_an_v_end;
        kad_an_vt[1 + 10] = (DWORD)(DWORD_PTR)kad_an_v_animend;
    }
    act = KLFC_PTR(DWORD (__fastcall *)(DWORD, DWORD, int), klfc_vf(P, 0x384))(P, 0, 0x2B);
    if (!klfc_ok(act, 0x80) || klh_rd32(act) != KLFC_VAULT_VT || klh_rd32(act + 8) != P) { g->why = "CreateAction(0x2B) gave no vault action"; return 0; }
    vt = (DWORD)(DWORD_PTR)&kad_an_vt[1];
    if (!klh_data((void *)(DWORD_PTR)act, &vt, 4, "adren anim: vptr")) { g->why = "the action's vptr could not be written"; return 0; }
    memset(&kad_an, 0, sizeof kad_an);
    kad_an.active = 1; kad_an.act = act; kad_an.P = P; kad_an.clip = clip; kad_an.rec = g->rec; kad_an.dnd = g->dnd; kad_an.soldier = g->soldier; kad_an.startT = T;
    kad_an.frames = (int)(klh_rd32(clip + 2) & 0xffff);
    memcpy(kad_an.Pf, Pf, 12); memcpy(kad_an.Final, Pf, 12);
    if (!kad_an_face(M, Pf, g->to, kad_an.M)) memcpy(kad_an.M, M, 36);
    dx = Pf[0] - g->to[0]; dz = Pf[2] - g->to[2]; l = (float)sqrt(dx * dx + dz * dz);
    if (l > 1.0f) { kad_an.Final[0] = g->to[0] + dx / l * kad_ao.dist; kad_an.Final[2] = g->to[2] + dz / l * kad_ao.dist; }        /* his own floor height */
    klfc_put(act + 0x14, M, 36, "adren anim: act"); klfc_put(act + 0x5c, Pf, 12, "adren anim: act");
    klfc_put(act + 0x38, M, 36, "adren anim: act"); klfc_put(act + 0x68, Pf, 12, "adren anim: act");
    klfc_put(act + 0x10, &clip, 4, "adren anim: act"); klfc_put(act + 0xc, &zero, 4, "adren anim: act");
    klfc_put(act + 0x74, z2, 2, "adren anim: act"); klfc_put(act + 0x78, &zero, 4, "adren anim: act");
    ptr = (DWORD)(DWORD_PTR)kad_an_edge; klfc_put(act + 0x7c, &ptr, 4, "adren anim: act");
    KLFC_PTR(void (__fastcall *)(DWORD, DWORD), klfc_vf(P, 0x374))(P, 0);                    /* Abort: a no-op when idle (precond: no action) */
    KLFC_PTR(void (__fastcall *)(DWORD, DWORD, DWORD), klfc_vf(P, 0x370))(P, 0, act);        /* StartAction: kad_an_v_start runs in here */
    if (klfc_cur_act(P) != act) {
        g->why = kad_an.endReason ? kad_an.endReason : "the action finished at once";
        if (kad_an.act == act) { int dead = kad_an.dead; memset(&kad_an, 0, sizeof kad_an); kad_an.dead = dead; }
        return 0;
    }
    if (kad_ao.log) klog("adren: anim - you kneel by record %d: slot '%s' id %d, clip %08lx (%d frames), %.0f units from him%s", g->rec, sl, id, clip, kad_an.frames, l, kad_ao.face ? ", turned to him" : "");
    return 1;
}

/* the tick's part: the human pl is the helper hp of downed AI heister i this pass */
static void kad_an_try(int i, struct kad_rec *k, DWORD pl, const float to[3], DWORD dnd, DWORD soldier)
{
    struct kad_an_go g; int r; DWORD now = GetTickCount();
    if (!kad_ao.on || kad.dry || kad_an.dead || kad_an.active || !pl || klh_rd32(pl) != KAD_PLAYER_VT) return;
    if (k->an_n && !kad_ao.repeat) return;
    if (k->an_n && now - kad_an.ended_at < 300) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA)) return;      /* only the main loop's gameplay call (luvsic's filter, klfreeclimb.c) */
    if (now - k->an_tried < 500) return;                           /* a refusal is asked again twice a second, not every frame */
    k->an_tried = now;
    memset(&g, 0, sizeof g); g.P = pl; g.rec = i; g.dnd = dnd; g.soldier = soldier; memcpy(g.to, to, 12);
    r = kad_an_guard("go", kad_an_go_body, &g);
    if (r < 0) { kad_an_disable("go"); return; }
    if (r == 1) k->an_n++;
    else if (kad_ao.log >= 2 || (g.why && strstr(g.why, "slot"))) { if (k->an_logged++ < 3) klog("adren: anim not started for record %d: %s", i, g.why ? g.why : "?"); }
}

/* the shot lands: the downed man's lie ends now (his help must be MinHelp or more) */
static void kad_an_inject(const struct klb_snap *s, const DWORD *dnd, DWORD tick)
{
    int i = kad_an.rec; DWORD nw;
    if (kad_an.injected != 1) return;
    if (i < 0 || i >= s->n || !kad_r[i].down || !dnd[i] || dnd[i] != kad_an.dnd || klh_rd32(dnd[i] + 4) != kad_an.soldier) { kad_an.injected = 3; klog("adren: anim: the shot finds record %d no longer lying - nothing to do", i); return; }
    if (s->human < 0 || kad_r[i].hm[s->human] < (DWORD)(kad.minhelp * 1000.0f)) { kad_an.injected = 3; klog("adren: anim: the shot is not counted - your help is %lu ms, MinHelp %.0f (hold E all through)", (unsigned long)(s->human >= 0 ? kad_r[i].hm[s->human] : 0), kad.minhelp * 1000.0f); return; }
    nw = tick + 2;
    if ((LONG)(klh_rd32(dnd[i] + 0x14) - nw) > 0 && klh_data((void *)(DWORD_PTR)(dnd[i] + 0x14), &nw, 4, "an AI heister's down-not-dead: the lie ends (the adrenaline shot)"))
        klog("adren: anim: THE SHOT - record %d gets up now (his lie tick -> %lu)", i, (unsigned long)nw);
    kad_an.injected = 2;
}

static void kad_an_init(void)
{
    memset(&kad_ao, 0, sizeof kad_ao); memset(&kad_an, 0, sizeof kad_an);
    kad_ao.on = GetPrivateProfileIntA("Adrenaline", "Anim", 0, klh_ini) != 0;
    if (!kad_ao.on) return;
    kad_ao.log = GetPrivateProfileIntA("Adrenaline", "AnimLog", 1, klh_ini);
    kad_ao.face = GetPrivateProfileIntA("Adrenaline", "AnimFace", 1, klh_ini) != 0;
    kad_ao.repeat = GetPrivateProfileIntA("Adrenaline", "AnimRepeat", 0, klh_ini) != 0;
    kad_ao.inject = GetPrivateProfileIntA("Adrenaline", "AnimInject", 1, klh_ini) != 0;
    kad_ao.alignf = GetPrivateProfileIntA("Adrenaline", "AnimAlignFrames", 10, klh_ini);
    if (kad_ao.alignf < 1) kad_ao.alignf = 1;
    if (kad_ao.alignf > 60) kad_ao.alignf = 60;
    kad_ao.injectf = GetPrivateProfileIntA("Adrenaline", "AnimInjectFrame", 30, klh_ini);
    if (kad_ao.injectf < 0) kad_ao.injectf = 0;
    if (kad_ao.injectf > 200) kad_ao.injectf = 200;
    kad_ao.dist = kad_inif("AnimDist", "60", 0.0f, 250.0f);
    GetPrivateProfileStringA("Adrenaline", "AnimSlot", "", kad_ao.slot, sizeof kad_ao.slot, klh_ini);
    kad_ao.userslot = kad_ao.slot[0] != 0;                          /* absent: Dead Men's exact clip where the build has it, else Dog Days' version */
    if (!kad_ao.slot[0]) strcpy(kad_ao.slot, KAD_AN_SLOT_DEF);
    klog("adren: Anim=1 - you kneel and give a downed AI heister Dead Men's adrenaline shot ('%s'%s, 55 frames in the players' sets); AnimFace=%d AnimDist=%.0f AnimAlignFrames=%d AnimInject=%d (frame %d) AnimRepeat=%d AnimLog=%d. "
         "An AI heister plays it with [Adrenaline] BotAnim (section BotAnim)", kad_ao.slot, kad_ao.userslot ? "" : "; first '" KAD_AN_SLOT_DM "' where the build has it", kad_ao.face, kad_ao.dist, kad_ao.alignf, kad_ao.inject, kad_ao.injectf, kad_ao.repeat, kad_ao.log);
}
/* ---------------------------------------------------------------- BotAnim: an AI heister kneels and gives the shot (worker 'aisyr', 2026-10-16)
 *
 * The owner: 'when someone gets revived with adrenaline it should be Dead Men's revive - kneeling and injecting a syringe'. The human
 * helper does it since v77 (Anim, above); with [Adrenaline] BotAnim=1 an AI HEISTER who helps a downed crewmate (the Rush bot that runs
 * to him, or any bot standing by him) kneels and plays the same slot '/Special_moves/Heal_wounded' - in an NPC set that is Dead Men's
 * own NPC clip 'Heal_Wounded_NPC' (73 frames, 2.9 s; Dog Days' copy is byte-identical to Dead Men's, re\adrenaline_anim.md 1): stands
 * 0-8, KNEELS 9-46, bent 47-61 (the shot), kneels 62-68.
 *
 * THE ROUTE (read in kl2.exe 0490 by this worker; Dog Days' own way of playing a free clip on an NPC):
 *   The NPC animation graph (built at 0x730be0, [0x1549040]) has, besides Stand (word +0), ShootPose (+0x1c), DownNotDead (+0x2c) ...,
 *   an EMPTY state (word +0x18; 0x569bd0 node, flags 0x10000) that plays whatever the actor is told to play: ZFFActor's Play (vt +0x200
 *   = 0x71efd0) hands the clip to the state machine [actor+0x8d8] (0x843530) when the actor's state ([[actor+0x7c0]+0x7c]) is that one.
 *   ZFakeCloseCombat (CPPScript, vtable 0xbd1144) is the stock user: start 0x4e9550 -> 0x671fe0(soldier, [graph+0x18]) (= 0x6270d0
 *   (state, 1) on [actor+0x7c0]), the clip through vt +0x200 (clip, 0x20001, 0, [0xb3e980], 1) - the same call vt +0x204 (0x6f6830)
 *   makes with flags 0x20001 - and AlignTo (vt +0x208, 0x80fdc0, the routine the NPC link mover 0x4a5160 uses on actors too); its end
 *   0x875140 stops the channel (0x5a6ec0 finds it, vt +0x1f8 = 0x63e600 stops it) and gives the graph back Stand (0x83ad90(soldier,
 *   [graph+0]) = 0x8d41c0(state, 1)). This part makes exactly those calls, in that order, from the game's own thread.
 *   The clip: the slot id from the level's slot table (klq_slot, the human's table - the ids are the level's), the clip of the BOT's set
 *   by 0x59d550 (reads [actor+0x84], what the NPC link mover calls).
 * WHEN: the helper of a downed crewmate (kad_pick, the same test as the help) is an AI heister within BotAnimNear of him (and either
 *   standing - moved < 25 units for 150 ms - or within 1.2 m: the Rush bot arriving; the AlignTo puts him in place), not down, his graph state not the empty one already (a level script plays him) and not DownNotDead; once
 *   per downed man and helper (BotAnimRepeat=1: again 0.5 s after the clip while the man still lies). BotAnimFace=1: ONE AlignTo that turns
 *   him to the man and puts him BotAnimDist units from him over BotAnimAlignFrames frames (the clip's standing phase).
 * THE SHOT (a downed AI heister; for a downed HUMAN the bot's clip is the picture, his get-up stays kldown.c's): BotAnimHold=1 keeps the
 *   man lying (his lie tick [dnd+0x14] at least 0.25 s ahead, and no Rate speed-up) until BotAnimInjectFrame (44: the end of the kneel, a
 *   GUESS from the pose), then BotAnimInject=1 ends his lie (tick + 2: the game's own get-up starts; 44 = the end of the kneel, live the channel
 *   ended at frame 50 - the bent phase starts at 47) - the bot injects, the man rises.
 *   The hold never lasts past the clip (+1 s time-out).
 * WATCHED every pass: the channel still plays our clip (+0 = clip, +4 = frame), the graph state is still the empty one (anything else =
 *   the AI took him back: nothing is restored, the game's state stands), he is not down, the actor / soldier are the same. At the clip's
 *   end / a lost channel / the time-out / the round's end: stop the channel, Stand back - only while the state is still the empty one.
 * SAFETY: every routine is checked first (first bytes of 0x671fe0 / 0x83ad90, ZFFActor's vt +0x1f8 / +0x204 / +0x208 / the code of
 *   0x5a6ec0 and 0x59d550); any mismatch = BotAnim off with a line, the old behaviour (the bot only stands by) goes on. A fault in any call
 *   is caught (kad_an_guard), logged, the part is off for the session. No byte of kl2.exe is changed.
 * NOT DONE: Dead Men's syringe prop (no build carries 'Items_Dynamic/Syringe_01') and its sound (Dead Men's NPC clip names
 *   'healed_by_adrenaline_01_withdelay' of the Dead Men bank: Dog Days' bank has no such sound; the clip's +0x2C is empty in Dog Days).
 */
#define KAD_BA_GRAPH     0x01549040u   /* -> the NPC animation graph: WORD +0 Stand, +0x18 the empty (scripted) state, +0x2c DownNotDead */
#define KAD_BA_SETSTATE  0x00671fe0u   /* thiscall (soldier; state): -> [[soldier+0x40]+0x7c0] 0x6270d0(state, 1), ret 4 */
#define KAD_BA_BACKSTATE 0x0083ad90u   /* thiscall (soldier; state): -> [[soldier+0x40]+0x7c0] 0x8d41c0(state, 1), ret 4 */
#define KAD_BA_FINDCH    0x005a6ec0u   /* thiscall (actor; clip) -> the channel that plays it (0 = none), ret 4 */
#define KAD_BA_STOPCH    0x0063e600u   /* ZFFActor vt +0x1f8: (channel) stop it, ret 4 */
#define KAD_BA_PLAY      0x006f6830u   /* ZFFActor vt +0x204: (clip, flags) -> the channel, ret 8 */
#define KAD_BA_ALIGN     0x0080fdc0u   /* ZFFActor vt +0x208: AlignTo(rot[9], pos[3], float frames) -> al */

static struct { int on, log, face, inject, hold, injectf, alignf, repeat, test, sticky; float near_, dist; char slot[96]; } kad_bo;
static struct kad_ba {
    int active, rec, injected, frames, startT; DWORD actor, soldier, clip, began; float from, to, last;
    WORD scripted, stand, first_other; int reassert, replays, test; const char *why;
} kad_ba[KLB_NREC];                            /* per HELPER record */
static struct kad_bw { float p0[3]; DWORD t0, tried; DWORD actor; int rec; int n; } kad_bw[KLB_NREC];   /* the standing check, per helper; n: plays for rec this down */
static int kad_ba_dead, kad_ba_checked, kad_ba_logs, kad_ba_tests;

static int kad_ba_code(DWORD va, const BYTE *code, int n)
{
    BYTE b[24]; return n <= (int)sizeof b && klh_rd((DWORD_PTR)KLH_VA(va), b, n) && !memcmp(b, code, n);
}
static int kad_ba_check(void)
{   /* the routines this part calls are the ones read (build 0490): -> 1 */
    static const BYTE set_[] = { 0x55, 0x8b, 0xec, 0x8b, 0x45, 0x08, 0x8b, 0x49, 0x40, 0x8b, 0x89, 0xc0, 0x07, 0x00, 0x00, 0x6a, 0x01, 0x50, 0xe8 };
    static const BYTE fch[] = { 0x56, 0x8b, 0x71, 0x70, 0x57, 0x8b, 0x7c, 0x24, 0x0c };
    static const BYTE cv[] = { 0x83, 0xec, 0x0c, 0xa1, 0x40, 0x26, 0xdd, 0x00 };
    DWORD vt = (DWORD)(DWORD_PTR)KLH_VA(KLB_ACTOR_VT);
    if (kad_ba_checked) return kad_ba_checked > 0;
    kad_ba_checked = -1;
    if (!kad_ba_code(KAD_BA_SETSTATE, set_, sizeof set_) || !kad_ba_code(KAD_BA_BACKSTATE, set_, sizeof set_)) { klog("adren: BotAnim OFF - 0x671fe0 / 0x83ad90 are not the state setters this build knows"); return 0; }
    if (!kad_ba_code(KAD_BA_FINDCH, fch, sizeof fch) || !kad_ba_code(KLFC_CLIPVAR, cv, sizeof cv)) { klog("adren: BotAnim OFF - 0x5a6ec0 / 0x59d550 are not the routines this build knows"); return 0; }
    if (klh_rd32(vt + 0x1f8) != (DWORD)(DWORD_PTR)KLH_VA(KAD_BA_STOPCH) || klh_rd32(vt + 0x204) != (DWORD)(DWORD_PTR)KLH_VA(KAD_BA_PLAY) || klh_rd32(vt + 0x208) != (DWORD)(DWORD_PTR)KLH_VA(KAD_BA_ALIGN)) {
        klog("adren: BotAnim OFF - ZFFActor's vtable +0x1f8 / +0x204 / +0x208 are not the ones read"); return 0;
    }
    kad_ba_checked = 1;
    return 1;
}
static int kad_ba_state(DWORD actor, WORD *st)
{
    DWORD sm = klh_rd32(actor + 0x7c0);
    return sm && klh_rd(sm + 0x7c, st, 2);
}
static int kad_ba_graph(WORD *stand, WORD *scripted, WORD *dnd)
{
    DWORD g = klh_rd32((DWORD_PTR)KLH_VA(KAD_BA_GRAPH));
    return g && klh_rd(g, stand, 2) && klh_rd(g + 0x18, scripted, 2) && klh_rd(g + 0x2c, dnd, 2) && *stand != 0xffff && *scripted != 0xffff;
}
static int kad_ba_actor_ok(DWORD actor, DWORD soldier)
{
    BYTE d = 1;
    return actor && klh_rd32(actor) == KLB_ACTOR_VT && soldier && klh_rd32(actor + 0x77c) == soldier && klh_rd32(soldier) == KAD_SOLDIER_VT &&
           klh_rd32(soldier + 0x40) == actor && klh_rd(actor + 0x64c, &d, 1) && !d;
}

/* stop our channel (if it still plays our clip) and give the graph Stand back (only while it is still the empty state) */
static int kad_ba_release_body(void *arg)
{
    struct kad_ba *b = (struct kad_ba *)arg; WORD st = 0xffff; DWORD ch;
    if (!b->actor || klh_rd32(b->actor) != KLB_ACTOR_VT || klh_rd32(b->actor + 0x77c) != b->soldier || klh_rd32(b->soldier) != KAD_SOLDIER_VT) return 2;   /* he is gone: nothing to give back */
    if (!kad_ba_state(b->actor, &st) || st != b->scripted) return 3;                    /* the game's own state stands */
    ch = KLFC_CALL(DWORD (__fastcall *)(DWORD, DWORD, DWORD), KAD_BA_FINDCH)(b->actor, 0, b->clip);
    if (ch && klfc_ok(ch, 0x38)) KLFC_CALL(void (__fastcall *)(DWORD, DWORD, DWORD), KAD_BA_STOPCH)(b->actor, 0, ch);
    KLFC_CALL(void (__fastcall *)(DWORD, DWORD, DWORD), KAD_BA_BACKSTATE)(b->soldier, 0, (DWORD)b->stand);
    return 1;
}
static void kad_ba_end(int h, const char *why)
{
    struct kad_ba *b = &kad_ba[h]; int r = 0; WORD st = 0xffff;
    if (!b->active) return;
    if (!kad_ba_dead) {
        r = kad_an_guard("BotAnim end", kad_ba_release_body, b);
        if (r < 0) { kad_ba_dead = 1; klog("adren: BotAnim DISABLED for this session (fault at the end); the help without the animation goes on"); }
    }
    if (b->actor) kad_ba_state(b->actor, &st);
    if (kad_bo.log) klog("adren: BotAnim END record %d (by record %d) reason=%s frame=%.1f of %.0f, %.2f s, the AI asked another state %d time(s) (first %d; clip played again %d time(s)), shot=%s; %s (state now %u)", h, b->rec, why, b->last, b->to,
                         (GetTickCount() - b->began) / 1000.0f, b->reassert, b->reassert ? (int)b->first_other : -1, b->replays,
                         b->injected == 2 ? "given" : b->injected == 3 ? "nobody to give it to" : b->injected ? "due" : "no",
                         r == 1 ? "channel stopped, Stand given back" : r == 2 ? "he is gone" : r == 3 ? "the AI had taken him back already" : "fault", (unsigned)st);
    memset(b, 0, sizeof *b);
}

struct kad_ba_go { const struct klb_snap *s; int i, h; DWORD pl; float man[3]; int have_at; float at[3]; const char *why; };   /* at: the TEST's kneeling place */
static int kad_ba_go_body(void *arg)
{
    struct kad_ba_go *g = (struct kad_ba_go *)arg; struct kad_ba *b = &kad_ba[g->h]; DWORD actor = g->s->r[g->h].actor, soldier, clip, ch;
    WORD stand, scripted, dndst, st = 0xffff; int id; float M[9], M2[9], P[3], F[3], dx, dz, l, n;
    soldier = actor ? klh_rd32(actor + 0x77c) : 0;
    if (!kad_ba_actor_ok(actor, soldier)) { g->why = "not a standing ZFFActor with its ZSoldier"; return 0; }
    if (!kad_ba_graph(&stand, &scripted, &dndst)) { g->why = "the NPC animation graph cannot be read"; return 0; }
    if (!kad_ba_state(actor, &st)) { g->why = "his graph state cannot be read"; return 0; }
    if (st == scripted) { g->why = "his graph is in the empty state already (a script plays him)"; return 0; }
    if (st == dndst) { g->why = "his graph is in DownNotDead"; return 0; }
    id = g->pl ? klq_slot(g->pl, kad_bo.slot) : -1;
    if (id < 0) id = klq_slot(actor, kad_bo.slot);
    if (id < 0) { g->why = "the clip's slot is not in this level's .ANM"; return 0; }
    clip = KLFC_CALL(DWORD (__fastcall *)(DWORD, DWORD, DWORD), KLFC_CLIPVAR)(actor, 0, (DWORD)id);
    if (!klfc_ok(clip, 0x68)) { g->why = "the slot has no clip in his set"; return 0; }
    if (!klfc_pose(actor, M, P)) { g->why = "his pose cannot be read"; return 0; }
    memset(b, 0, sizeof *b);
    b->actor = actor; b->soldier = soldier; b->clip = clip; b->rec = g->i; b->scripted = scripted; b->stand = stand;
    b->frames = (int)(klh_rd32(clip + 2) & 0xffff); b->startT = klfc_T(); b->began = GetTickCount();
    KLFC_CALL(void (__fastcall *)(DWORD, DWORD, DWORD), KAD_BA_SETSTATE)(soldier, 0, (DWORD)scripted);
    if (!kad_ba_state(actor, &st) || st != scripted) { g->why = "the graph did not take the empty state"; memset(b, 0, sizeof *b); return 0; }
    b->active = 1;                                                  /* from here on kad_ba_end gives Stand back */
    ch = KLFC_PTR(DWORD (__fastcall *)(DWORD, DWORD, DWORD, int), klfc_vf(actor, 0x204))(actor, 0, clip, 0x20001);
    if (!klfc_ok(ch, 0x20) || klh_rd32(ch) != clip) { g->why = "Play gave no channel with the clip"; kad_ba_end(g->h, "no channel"); return 0; }
    b->from = klfc_f(ch + 8); b->to = klfc_f(ch + 0xc); b->last = klfc_f(ch + 4);
    if (kad_bo.face) {
        dx = P[0] - g->man[0]; dz = P[2] - g->man[2]; l = (float)sqrt(dx * dx + dz * dz);
        memcpy(F, P, 12);
        if (l > 1.0f) { F[0] = g->man[0] + dx / l * kad_bo.dist; F[2] = g->man[2] + dz / l * kad_bo.dist; }
        if (g->have_at) { F[0] = g->at[0]; F[2] = g->at[2]; }
        if (!kad_an_face(M, g->have_at ? F : P, g->man, M2)) memcpy(M2, M, 36);
        n = (float)kad_bo.alignf;
        if (n > b->to - b->from - 1.0f) n = b->to - b->from - 1.0f;
        if (n < 1.0f) n = 1.0f;
        if (!(KLFC_PTR(BYTE (__fastcall *)(DWORD, DWORD, const float *, const float *, float), klfc_vf(actor, 0x208))(actor, 0, M2, F, n) & 0xff))
            klog("adren: BotAnim AlignTo refused (record %d) - he kneels where he stands", g->h);
    }
    if (kad_bo.log) {
        char nm[48]; kad_name(g->h, nm, sizeof nm);
        klog("adren: BotAnim START record %d (%s) kneels by record %d (%s): slot '%s' id %d, clip %08lx (%d frames, channel %08lx from %.0f to %.0f), %.0f units from him, state %u -> %u (the empty state)",
             g->h, nm, g->i, g->i == g->s->human ? "you" : "bot", kad_bo.slot, id, (unsigned long)clip, b->frames, (unsigned long)ch, b->from, b->to,
             (float)sqrt((P[0] - g->man[0]) * (P[0] - g->man[0]) + (P[2] - g->man[2]) * (P[2] - g->man[2])), (unsigned)stand, (unsigned)scripted);
    }
    return 1;
}

/* the tick's part: AI heister h is the helper of downed record i this pass */
static void kad_ba_try(const struct klb_snap *s, int i, int h, const float hp[3], const float man[3], DWORD pl)
{
    struct kad_bw *w; struct kad_ba_go g; DWORD now = GetTickCount(); float dx, dz, mv, d; int r;
    if (!kad_bo.on || kad.dry || kad_ba_dead || h < 0 || h >= KLB_NREC || h == s->human || kad_ba[h].active) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA)) return;      /* only the main loop's gameplay call */
    w = &kad_bw[h];
    if (w->actor != s->r[h].actor || w->rec != i + 1) { memset(w, 0, sizeof *w); w->actor = s->r[h].actor; w->rec = i + 1; memcpy(w->p0, hp, 12); w->t0 = now; }
    dx = hp[0] - w->p0[0]; dz = hp[2] - w->p0[2]; mv = (float)sqrt(dx * dx + dz * dz);
    if (mv > 25.0f) { memcpy(w->p0, hp, 12); w->t0 = now; }              /* he moved: the standing clock starts again */
    dx = hp[0] - man[0]; dz = hp[2] - man[2]; d = (float)sqrt(dx * dx + dz * dz);
    if (w->n && !kad_bo.repeat) return;
    if (d > kad_bo.near_ * KAD_M || (now - w->t0 < 150 && d > 1.2f * KAD_M)) {      /* not by him yet: further than Near, or still walking up and more than 1.2 m off */
        if (kad_bo.log >= 2 && now - w->tried >= 1000) { w->tried = now; klog("adren: BotAnim waits: record %d helps record %d from %.2f m (Near %.1f), standing %lu ms", h, i, d / KAD_M, kad_bo.near_, (unsigned long)(now - w->t0)); }
        return;
    }
    if (now - w->tried < 500) return;
    for (r = 0; r < KLB_NREC; r++) if (kad_ba[r].active && kad_ba[r].rec == i && !kad_ba[r].test) return;     /* one syringe a man: another bot gives it already (live AISYR6: two knelt by one man) */
    w->tried = now;
    if (!kad_ba_check()) { kad_ba_dead = 1; return; }
    memset(&g, 0, sizeof g); g.s = s; g.i = i; g.h = h; g.pl = pl; memcpy(g.man, man, 12);
    r = kad_an_guard("BotAnim start", kad_ba_go_body, &g);
    if (r < 0) { kad_ba_dead = 1; memset(&kad_ba[h], 0, sizeof kad_ba[h]); klog("adren: BotAnim DISABLED for this session (fault at the start); the help without the animation goes on"); return; }
    if (r == 1) w->n++;
    else if (kad_ba_logs++ < 12 || kad_bo.log >= 2) klog("adren: BotAnim not started for record %d by record %d: %s", i, h, g.why ? g.why : "?");
}

/* BotAnimTest=N (a TEST key, 0 = off): every N seconds the AI heister nearest to YOU (in play, not down, within 8 m on your floor) plays
   the shot towards you as if you lay there - for an autotest that cannot wait for a real down. Logged 'BotAnim TEST'. */
static void kad_ba_test(const struct klb_snap *s, float pos[][3], const int *havepos, const BYTE *dn, DWORD pl)
{
    static DWORD last, first; DWORD now = GetTickCount(); int h, best = -1, r, front = 0; float bd = 0, bs = 1e9f, sc, d, M[9], F[3]; struct kad_ba_go g;
    if (!kad_bo.on || kad_bo.test <= 0 || kad.dry || kad_ba_dead || s->human < 0 || !havepos[s->human] || dn[s->human]) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA)) return;
    if (!first) first = now;
    if (now - first < 15000) return;                               /* past the round's opening camera */
    if (last && now - last < (DWORD)kad_bo.test * 1000u) return;
    front = pl && klfc_pose(pl, M, F);                              /* row 0 = where your back points */
    for (h = 0; h < s->n; h++) {
        if (h == s->human || !s->r[h].used || s->r[h].status != 0 || !(s->r[h].flags & 1) || dn[h] || !havepos[h] || kad_ba[h].active) continue;
        if (fabs(pos[h][1] - pos[s->human][1]) > 2.0f * KAD_M) continue;
        if ((d = kad_dist(pos[h], pos[s->human])) > 8.0f * KAD_M) continue;
        sc = d;
        if (front && d > 1.0f && ((pos[h][0] - pos[s->human][0]) * -M[0] + (pos[h][2] - pos[s->human][2]) * -M[2]) < 0.3f * d) sc += 100.0f * KAD_M;   /* behind you: only when nobody is in front (the picture) */
        if (sc < bs) { bs = sc; bd = d; best = h; }
    }
    last = now;
    if (best < 0) { klog("adren: BotAnim TEST - no AI heister within 8 m of you"); return; }
    if (!kad_ba_check()) { kad_ba_dead = 1; return; }
    memset(&g, 0, sizeof g); g.s = s; g.i = s->human; g.h = best; g.pl = pl; memcpy(g.man, pos[s->human], 12);
    if (front) {                                                    /* 1.7 m to one side of you (each test the other side), 0.6 m ahead: in the picture, not hidden by your own back */
        float l = (float)sqrt(M[0] * M[0] + M[2] * M[2]), lx = (float)sqrt(M[6] * M[6] + M[8] * M[8]), side = (kad_ba_tests++ & 1) ? 170.0f : -170.0f;
        if (l > 1e-3f && lx > 1e-3f) { g.have_at = 1; g.at[0] = pos[s->human][0] - M[0] / l * 60.0f + M[6] / lx * side; g.at[1] = pos[best][1]; g.at[2] = pos[s->human][2] - M[2] / l * 60.0f + M[8] / lx * side; }
    }
    klog("adren: BotAnim TEST - record %d, %.1f m from you, plays the shot towards you", best, bd / KAD_M);
    r = kad_an_guard("BotAnim test", kad_ba_go_body, &g);
    if (r == 1) kad_ba[best].test = 1;
    if (r < 0) { kad_ba_dead = 1; memset(&kad_ba[best], 0, sizeof kad_ba[best]); klog("adren: BotAnim DISABLED for this session (fault at the start)"); return; }
    if (r != 1) klog("adren: BotAnim TEST - not started: %s", g.why ? g.why : "?");
}

/* is a bot's shot running on downed record i, not yet given? (the Rate speed-up waits for it) */
static int kad_ba_holding(int i)
{
    int h;
    if (!kad_bo.on || !kad_bo.hold) return 0;
    for (h = 0; h < KLB_NREC; h++) if (kad_ba[h].active && kad_ba[h].rec == i && !kad_ba[h].injected) return 1;
    return 0;
}

struct kad_ba_up { struct kad_ba *b; float cur; const char *end; };
static int kad_ba_update_body(void *arg)
{
    struct kad_ba_up *u = (struct kad_ba_up *)arg; struct kad_ba *b = u->b; WORD st = 0xffff; DWORD ch; BYTE d = 0;
    if (!b->actor || klh_rd32(b->actor) != KLB_ACTOR_VT || klh_rd32(b->actor + 0x77c) != b->soldier) { u->end = "he is gone"; return 0; }
    if (klh_rd(b->actor + 0x64c, &d, 1) && d) { u->end = "he went down himself"; return 0; }
    if (!kad_ba_state(b->actor, &st)) { u->end = "his graph state cannot be read"; return 0; }
    ch = KLFC_CALL(DWORD (__fastcall *)(DWORD, DWORD, DWORD), KAD_BA_FINDCH)(b->actor, 0, b->clip);
    if (st == b->scripted && (!ch || !klfc_ok(ch, 0x38) || klh_rd32(ch) != b->clip)) { u->end = "channel over"; return 0; }
    if (st != b->scripted) {
        /* his own AI asked another state (Stand, Sneak ...): the graph's change took our channel with it (live, run AISYR4). Sticky: the
           empty state again and the clip again from the frame it had reached (channel +4), at most BotAnimSticky times a clip. */
        float at = b->last;
        if (b->reassert >= kad_bo.sticky) { u->end = "the AI took him back (BotAnimSticky used up)"; return 0; }
        if (b->injected) { u->end = "the AI took him back after the shot (not held)"; return 0; }
        if (!b->reassert) b->first_other = st;
        b->reassert++;
        KLFC_CALL(void (__fastcall *)(DWORD, DWORD, DWORD), KAD_BA_SETSTATE)(b->soldier, 0, (DWORD)b->scripted);
        if (!kad_ba_state(b->actor, &st) || st != b->scripted) { u->end = "the AI took him back (the empty state was refused)"; return 0; }
        if (!ch || !klfc_ok(ch, 0x38) || klh_rd32(ch) != b->clip) {
            ch = KLFC_PTR(DWORD (__fastcall *)(DWORD, DWORD, DWORD, int), klfc_vf(b->actor, 0x204))(b->actor, 0, b->clip, 0x20001);
            if (!klfc_ok(ch, 0x20) || klh_rd32(ch) != b->clip) { u->end = "the AI took him back (Play again gave no channel)"; return 0; }
            if (at > b->from && at < b->to - 1.0f) klh_data((void *)(DWORD_PTR)(ch + 4), &at, 4, "a bot's adrenaline clip: on from the frame it had reached");
            b->replays++;
        }
    }
    u->cur = klfc_f(ch + 4);
    return 1;
}
static void kad_ba_tick(const struct klb_snap *s, const DWORD *dnd, DWORD tick)
{
    int h, r; struct kad_ba_up u;
    if (!kad_bo.on) return;
    for (h = 0; h < KLB_NREC; h++) {
        struct kad_ba *b = &kad_ba[h]; int i;
        if (!b->active) continue;
        if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA)) return;
        if (kad_ba_dead) { memset(b, 0, sizeof *b); continue; }
        memset(&u, 0, sizeof u); u.b = b; u.cur = -1.0f;
        r = kad_an_guard("BotAnim update", kad_ba_update_body, &u);
        if (r < 0) { kad_ba_dead = 1; memset(b, 0, sizeof *b); klog("adren: BotAnim DISABLED for this session (fault in the update)"); continue; }
        i = b->rec;
        if (!r) {                                                   /* over: a clip that got past the kneel (frame 40) still gives the shot */
            if (kad_bo.inject && !b->injected && b->last >= 40.0f && i >= 0 && i < s->n && i != s->human && kad_r[i].down && dnd[i] && !kad.dry) {
                DWORD lt = klh_rd32(dnd[i] + 0x14), nw = tick + 2;
                if ((LONG)(lt - nw) > 0 && klh_data((void *)(DWORD_PTR)(dnd[i] + 0x14), &nw, 4, "an AI heister's down-not-dead: the lie ends (an AI heister's adrenaline shot)"))
                    klog("adren: BotAnim: THE SHOT - record %d injects record %d at the clip's end (frame %.1f): he gets up now", h, i, b->last);
                b->injected = 2;
            }
            kad_ba_end(h, u.end); continue;
        }
        b->last = u.cur;
        if (!b->injected && !b->test && (i < 0 || i >= s->n || !kad_r[i].down)) { kad_ba_end(h, "the man he kneels by is no longer down (up / dead / gone) before the shot"); continue; }
        /* the downed man: an AI heister still lying in this pass */
        if (i >= 0 && i < s->n && i != s->human && kad_r[i].down && dnd[i] && !kad.dry) {
            DWORD lt = klh_rd32(dnd[i] + 0x14), nw;
            if (kad_bo.inject && !b->injected && u.cur >= (float)kad_bo.injectf) {
                nw = tick + 2;
                if ((LONG)(lt - nw) > 0 && klh_data((void *)(DWORD_PTR)(dnd[i] + 0x14), &nw, 4, "an AI heister's down-not-dead: the lie ends (an AI heister's adrenaline shot)"))
                    klog("adren: BotAnim: THE SHOT - record %d injects record %d at frame %.1f: he gets up now", h, i, u.cur);
                b->injected = 2;
            } else if (kad_bo.hold && !b->injected) {
                nw = tick + 256;                                        /* 0.25 s ahead: he waits for the shot */
                if ((LONG)(nw - lt) > 0) klh_data((void *)(DWORD_PTR)(dnd[i] + 0x14), &nw, 4, "an AI heister's down-not-dead: he waits for the shot (adrenaline)");
            }
        } else if (kad_bo.inject && !b->injected && u.cur >= (float)kad_bo.injectf) b->injected = (i == s->human) ? 2 : 3;
        if (u.cur >= b->to - 0.5f) { kad_ba_end(h, "clip end"); continue; }
        if (klfc_T() - b->startT > b->frames * 1024 / 25 + 1024) { kad_ba_end(h, "timeout"); continue; }
    }
}
static void kad_ba_forget(const char *why)
{
    int h;
    for (h = 0; h < KLB_NREC; h++) if (kad_ba[h].active) kad_ba_end(h, why);
    memset(kad_bw, 0, sizeof kad_bw);
}
static void kad_ba_down(int i)
{   /* record i went down anew: every helper may give him one shot again */
    int h;
    for (h = 0; h < KLB_NREC; h++) if (kad_bw[h].rec == i + 1) kad_bw[h].n = 0;
}
static void kad_ba_init(void)
{
    memset(&kad_bo, 0, sizeof kad_bo); memset(kad_ba, 0, sizeof kad_ba); memset(kad_bw, 0, sizeof kad_bw); kad_ba_dead = 0; kad_ba_checked = 0; kad_ba_logs = 0;
    kad_bo.on = GetPrivateProfileIntA("Adrenaline", "BotAnim", 1, klh_ini) != 0;
    if (!kad_bo.on) { klog("adren: BotAnim=0 - an AI heister who helps only stands by"); return; }
    kad_bo.log = GetPrivateProfileIntA("Adrenaline", "BotAnimLog", 1, klh_ini);
    kad_bo.face = GetPrivateProfileIntA("Adrenaline", "BotAnimFace", 1, klh_ini) != 0;
    kad_bo.inject = GetPrivateProfileIntA("Adrenaline", "BotAnimInject", 1, klh_ini) != 0;
    kad_bo.hold = GetPrivateProfileIntA("Adrenaline", "BotAnimHold", 1, klh_ini) != 0;
    kad_bo.repeat = GetPrivateProfileIntA("Adrenaline", "BotAnimRepeat", 0, klh_ini) != 0;
    kad_bo.injectf = GetPrivateProfileIntA("Adrenaline", "BotAnimInjectFrame", 44, klh_ini);
    if (kad_bo.injectf < 0) kad_bo.injectf = 0;
    if (kad_bo.injectf > 200) kad_bo.injectf = 200;
    kad_bo.alignf = GetPrivateProfileIntA("Adrenaline", "BotAnimAlignFrames", 9, klh_ini);
    if (kad_bo.alignf < 1) kad_bo.alignf = 1;
    if (kad_bo.alignf > 60) kad_bo.alignf = 60;
    kad_bo.dist = kad_inif("BotAnimDist", "60", 0.0f, 250.0f);
    kad_bo.near_ = kad_inif("BotAnimNear", "2.0", 0.5f, 6.0f);
    kad_bo.test = GetPrivateProfileIntA("Adrenaline", "BotAnimTest", 0, klh_ini);
    kad_bo.sticky = GetPrivateProfileIntA("Adrenaline", "BotAnimSticky", 400, klh_ini);
    if (kad_bo.sticky < 0) kad_bo.sticky = 0;
    if (kad_bo.test) klog("adren: BotAnimTest=%d - TEST: every %d s the AI heister nearest to you plays the shot towards you", kad_bo.test, kad_bo.test);
    GetPrivateProfileStringA("Adrenaline", "BotAnimSlot", KAD_AN_SLOT_DEF, kad_bo.slot, sizeof kad_bo.slot, klh_ini);
    if (!kad_bo.slot[0]) strcpy(kad_bo.slot, KAD_AN_SLOT_DEF);
    klog("adren: BotAnim=1 - an AI heister who helps a downed crewmate kneels and gives him Dead Men's adrenaline shot ('%s': in an NPC set Dead Men's Heal_Wounded_NPC, 73 frames) through the NPC graph's empty state (ZFakeCloseCombat's calls); "
         "BotAnimNear=%.1f m BotAnimFace=%d (BotAnimDist=%.0f over %d frames) BotAnimHold=%d BotAnimInject=%d (frame %d) BotAnimRepeat=%d BotAnimLog=%d",
         kad_bo.slot, kad_bo.near_, kad_bo.face, kad_bo.dist, kad_bo.alignf, kad_bo.hold, kad_bo.inject, kad_bo.injectf, kad_bo.repeat, kad_bo.log);
}
#define KAD_BA_TRY(s, i, h, hp, man, pl) kad_ba_try(s, i, h, hp, man, pl)
#define KAD_BA_TICK(s, dnd, tick) kad_ba_tick(s, dnd, tick)
#define KAD_BA_HOLDING(i) kad_ba_holding(i)
#define KAD_BA_FORGET(why) kad_ba_forget(why)
#define KAD_BA_DOWN(i) kad_ba_down(i)
#define KAD_BA_INIT() kad_ba_init()
#define KAD_BA_TEST(s, pos, hv, dn, pl) kad_ba_test(s, pos, hv, dn, pl)

#define KAD_AN_TRY(i, k, pl, to, dnd, sol) kad_an_try(i, k, pl, to, dnd, sol)
#define KAD_AN_INJECT(s, dnd, tick) kad_an_inject(s, dnd, tick)
#define KAD_AN_INIT() kad_an_init()
#else
#define KAD_AN_TRY(i, k, pl, to, dnd, sol) ((void)0)
#define KAD_AN_INJECT(s, dnd, tick) ((void)0)
#define KAD_AN_INIT() ((void)0)
#define KAD_BA_TRY(s, i, h, hp, man, pl) ((void)0)
#define KAD_BA_TICK(s, dnd, tick) ((void)0)
#define KAD_BA_HOLDING(i) 0
#define KAD_BA_FORGET(why) ((void)0)
#define KAD_BA_DOWN(i) ((void)0)
#define KAD_BA_INIT() ((void)0)
#define KAD_BA_TEST(s, pos, hv, dn, pl) ((void)0)
#endif

/* ---------------------------------------------------------------- one pass */

static void kad_forget(const char *why)
{
    int i; (void)why;
    KAD_BA_FORGET(why);                                       /* BotAnim: a kneeling bot gets Stand back */
    for (i = 0; i < KLB_NREC; i++) if (kad_r[i].fast) kad_r[i].fast = 0;      /* [D+0x29] is the game's own to reset with D */
    memset(kad_r, 0, sizeof kad_r);
    memset(kad_m, 0, sizeof kad_m);
    memset(&kad_g, 0, sizeof kad_g);
    for (i = 0; i < KLB_NREC; i++) kad_g.kw[i] = 0xffff;      /* no 'before' yet: the first pass of a round is no rise */
}

static void kad_tick(int game_thread)
{
    struct klb_snap sn; DWORD rules, state, now, tick = 0, clock, gd, pl = 0, D = 0, ds = 0; int level, act, i, j, hs = -1; char why[200];
    BYTE police = 0, idx = 0xff;
    float pos[KLB_NREC][3]; int havepos[KLB_NREC]; BYTE dn[KLB_NREC]; DWORD dnd[KLB_NREC];
    if (!kad.on || !game_thread || !klh_exe_ok) return;
    now = GetTickCount();
    act = klr_arcade(&rules, &state, &level) && klb_level(why) && state == KAD_ROUND && klb_read(&sn) && sn.state == KAD_ROUND;
    if (!act) { if (kad_g.rules) kad_forget("round over"); return; }
    if (sn.rules != kad_g.rules) {            /* a new round / rules object: a mark left over from the last round is taken off, nothing else is carried */
        for (i = 0; i < KLB_NREC; i++) if (kad_m[i].on && !kad_m[i].keep && !kad.dry) { DWORD fl = 0; if (klh_rd(sn.score + 0x1d4 + 4 * i, &fl, 4) && (fl & 1)) { fl &= ~1u; klh_data((void *)(DWORD_PTR)(sn.score + 0x1d4 + 4 * i), &fl, 4, "client flags: a mark of last round (adrenaline)"); } }
        kad_forget("new rules object"); kad_g.rules = sn.rules;
        kad_g.hint_at = now + 9000;          /* the round's first prompt: once the countdown is over, what the key is for */
        klog("adren: a round runs (Arcade, not the stock level: %s); %d crew record(s); Range %.1f m, BotRange %.1f m, Rate %.1f, Meter %.1f, Share %.2f, Mark %d%s", why, sn.n, kad.range, kad.brange, kad.rate, kad.meter, kad.share, kad.mark, kad.dry ? " - Dry: nothing is written" : "");
    }
    if (kad_g.hint_at && (LONG)(now - kad_g.hint_at) >= 0) {
        kad_g.hint_at = 0;
        if (kad.prompt && kset_v[3]) { kad_say(1, 0, kad.usekey == 0x45 ? "Crewmate down? Hold E by him: adrenaline gets him up and you get a cut" : "Crewmate down? Hold Use by him: adrenaline gets him up and you get a cut", 5.0f);
                                         klog("adren: prompt: the round's hint said (%s)", kad_g.said_key == 1 ? "shown" : "NOT shown: no announcement element yet"); }
    }
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KAD_GAMEDATA))) || !(clock = klh_rd32((DWORD_PTR)KLH_VA(KLD_CLOCK))) || !klh_rd(clock + 0x48, &tick, 4)) return;
    /* the local human's knock-down state (D), if he is a criminal in play */
    if (klh_rd(gd + 0x898, &idx, 1) && idx < 4 && (pl = klh_rd32(gd + 0x828 + 4 * idx)) != 0 && klh_rd32(pl) == KAD_PLAYER_VT && klh_rd(pl + 0x2723, &police, 1) && !police &&
        (D = klh_rd32(pl + 0x2948)) != 0 && klh_rd32(D) == pl && klh_rd(D + 4, &ds, 4)) hs = sn.human; else { pl = 0; D = 0; ds = 0; }
    /* each record: down? place? */
    for (i = 0; i < sn.n; i++) {
        const struct klb_rec *r = &sn.r[i]; struct kad_rec *k = &kad_r[i]; BYTE d = 0; DWORD s = 0, dn_ = 0;
        dn[i] = 0; dnd[i] = 0; havepos[i] = 0;
        if (!r->used) { if (k->actor) memset(k, 0, sizeof *k); continue; }
        if (k->actor != r->actor) { memset(k, 0, sizeof *k); k->actor = r->actor; k->by = -1; }
        if (r->status != 0) continue;           /* aboard / escaped / dead: out of play */
        if (i == sn.human) { if (i == hs && ds >= 1 && ds <= 3) d = 1; }     /* 2 = on the floor in kldown.c's knock-down (live, run v52_RTW2: 'down state 2'): down too */
        else if ((r->flags & 1) && r->actor && klh_rd32(r->actor) == KLB_ACTOR_VT && (s = klh_rd32(r->actor + 0x77c)) != 0 && klh_rd32(s) == KAD_SOLDIER_VT && klh_rd32(s + 0x40) == r->actor) {
            klh_rd(r->actor + 0x64c, &d, 1);
            if (d) { dn_ = klh_rd32(s + 0x4b8); if (dn_ && klh_rd32(dn_ + 4) != s) dn_ = 0; dnd[i] = dn_; }
        }
        dn[i] = d ? 1 : 0;
        havepos[i] = kad_place(&sn, i, pos[i]);
    }
    /* the humans' bullets: whose word [score+0x1b8+2i] rose since the last pass */
    for (i = 0; i < sn.n; i++) {
        WORD w = 0; kad_g.kwok[i] = 0;
        if (sn.r[i].used && !(sn.r[i].flags & 1) && klh_rd(sn.score + 0x1b8 + 2 * i, &w, 2)) { kad_g.kwok[i] = 1; }
        (void)w;
    }
    for (i = 0; i < sn.n; i++) {
        const struct klb_rec *r = &sn.r[i]; struct kad_rec *k = &kad_r[i]; DWORD dt;
        if (!r->used) continue;
        if (r->status != 0 && k->down) {        /* he left play while down (died, was left behind) */
            kad_rush_end(&sn, i, "he left play");
            k->down = 0;
            if (k->mkn) { kad_m[k->by].keep = 1; }
            klog("adren: record %d left play while down (%s)", i, r->status == 7 ? "he DIED" : "status other than in-play"); continue;
        }
        if (r->status != 0) continue;
        dt = k->tick_last ? tick - k->tick_last : 0; k->tick_last = tick;
        if (dt > 512) dt = 0;                  /* a stall or a load: no catch-up, no credit */
        if (dn[i] && !k->down) {
            /* ---- he goes down */
            int by = -1, h;
            k->down = 1; k->t_down = now; k->tick_down = tick; k->by = -1; memset(k->hm, 0, sizeof k->hm); k->sped = 0; k->mkn = 0; k->an_n = 0; k->an_logged = 0; k->an_tried = 0;
            KAD_BA_DOWN(i);
            if (i != sn.human) for (h = 0; h < sn.n; h++) {       /* a human whose word rose in this pass put him down (ASSUMED reading of re\player_down.md 11.1) */
                WORD w = 0;
                if (!sn.r[h].used || (sn.r[h].flags & 1) || !kad_g.kwok[h] || !klh_rd(sn.score + 0x1b8 + 2 * h, &w, 2)) continue;
                if (w != kad_g.kw[h] && kad_g.kw[h] != 0xffff && (WORD)(w - kad_g.kw[h]) < 1000) { by = h; break; }
            }
            if (by < 0 && klbd_by(i) >= 0) by = klbd_by(i);          /* klbotdown.c: the threshold down never raises the score word */
            k->by = by;
            if (i == sn.human) {
                if (kad.prompt) kad_say(300, 0, "YOU'RE DOWN - mash GET UP. A crewmate by you gets you up faster", 4.0f);      /* 2026-10-15: the down was there but nothing said so */
                klog("adren: YOU ARE DOWN (state %lu) at (%.0f, %.0f, %.0f)%s", ds, havepos[i] ? pos[i][0] : 0, havepos[i] ? pos[i][1] : 0, havepos[i] ? pos[i][2] : 0, kld.on ? "" : " ([Down] is off: the meter cannot be driven)");
            } else {
                long lt = dnd[i] ? (long)(klh_rd32(dnd[i] + 0x14) - tick) : 0; k->lie0 = lt / 1024.0f;
                klog("adren: record %d (%s) IS DOWN at (%.0f, %.0f, %.0f); he lies %.2f s; put down by %s", i, sn.r[i].flags & 2 ? "TRAITOR" : "bot", havepos[i] ? pos[i][0] : 0, havepos[i] ? pos[i][1] : 0, havepos[i] ? pos[i][2] : 0, k->lie0,
                     by >= 0 ? "a human's bullet (his word rose)" : "nobody known (police, or the word did not rise)");
                if (by >= 0 && !(sn.r[i].flags & 2)) { kad_mark_on(&sn, by, i); if (kad_m[by].on) k->mkn = 1; }
            }
        } else if (!dn[i] && k->down) {
            /* ---- he is up */
            int best = -1, h; DWORD bm = 0;
            kad_rush_end(&sn, i, "he is up");
            k->down = 0;
            for (h = 0; h < sn.n; h++) if (k->hm[h] > bm) { bm = k->hm[h]; best = h; }
            klog("adren: record %d IS UP after %.2f s on the floor (he lay %.2f s at go-down; unhelped the game gives 1.5 .. 3.0); helped %lu ms by %s", i, (now - k->t_down) / 1000.0f, k->lie0, (unsigned long)bm, best >= 0 ? (best == sn.human ? "you" : "a bot") : "nobody");
            if (i != sn.human) { DWORD ho = klh_rd32(sn.r[i].actor + 0x5fc), v4 = 0, v8 = 0; float f4, f8; if (ho) { v4 = klh_rd32(ho + 4); v8 = klh_rd32(ho + 8); memcpy(&f4, &v4, 4); memcpy(&f8, &v8, 4); klog("adren: record %d health object %08lx at the get-up: [+4] %.1f [+8] %.1f (RAW, layout not read: A0/A1 expect about 75 %% of the maximum if the game ended the lie itself, 0 or less if our pull ended it too soon)", i, (unsigned long)ho, f4, f8); } }
            if (k->fast && pl) { BYTE z = 0; klh_data((void *)(DWORD_PTR)(D + 0x29), &z, 1, "player: the fast get-up byte back (adrenaline)"); }
            k->fast = 0;
            if (best >= 0 && bm >= (DWORD)(kad.minhelp * 1000.0f)) {
                if (kad.share > 0) { if (k->paid) klog("adren: record %d was helped up before this round: no second share (once per man per round)", i); else { k->paid = 1; kad_pay(&sn, i, best, bm); } }
                if (kad.prompt && i == sn.human && best >= 0 && best != sn.human) { char nm[48], msg[160]; kad_name(best, nm, sizeof nm); snprintf(msg, sizeof msg, "ADRENALINE: %s got you up - he takes a cut of your money", nm); kad_say(320 + best, 0, msg, 3.5f); }
                if (kad.prompt && best == sn.human && i != sn.human) { char nm[48], msg[160]; kad_name(i, nm, sizeof nm); snprintf(msg, sizeof msg, "%s is back up - you get a cut of his money", nm); kad_say(500 + i, 0, msg, 3.0f); }
                if (k->by >= 0 && k->by == best) kad_mark_off(&sn, k->by, i, "he helped him up");
                else if (k->by >= 0 && k->mkn) klog("adren: record %d (who put record %d down) did not help him up: his mark stays", k->by, i);
            } else if (k->by >= 0 && k->mkn) klog("adren: record %d got up without enough help (%lu ms of %.0f): the mark of record %d stays", i, (unsigned long)bm, kad.minhelp * 1000.0f, k->by);
            k->by = -1; k->mkn = 0;
            continue;
        }
        if (!dn[i] || !k->down) continue;
        /* ---- he lies: who is by him? */
        {
            float dist[KLB_NREC], lim[KLB_NREC]; int h, hp; BYTE use = 0; DWORD usedw = 0;
            for (h = 0; h < sn.n; h++) {
                const struct klb_rec *q = &sn.r[h];
                dist[h] = -1; lim[h] = 0;
                if (h == i || !q->used || q->status != 0 || dn[h] || (q->flags & 2) || !havepos[h] || !havepos[i]) continue;
                if (!(q->flags & 1) && h != sn.human) continue;             /* a human that is not the local one: his place is not read here (online later) */
                if (h == sn.human && police) continue;
                if (!(q->flags & 1)) {                                       /* a human helper: Range, and Use if asked */
                    if (kset_v[3] && !(h == sn.human && kad_use_held(pl))) continue;   /* kset_v[3]: the menu's row */
                    lim[h] = kad.range * KAD_M;
                } else if (i == sn.human) lim[h] = kad.brange * KAD_M;       /* an AI heister by a downed human */
                else if (kad.bothelp) lim[h] = kad.brange * KAD_M;          /* BotHelp: an AI heister by a downed AI heister */
                else continue;
                if (fabs(pos[h][1] - pos[i][1]) > 2.0f * KAD_M) continue;    /* another floor */
                dist[h] = kad_dist(pos[h], pos[i]);
            }
            hp = kad_pick(dist, lim, sn.n);
            kad_rush(&sn, i, pos, havepos, dn, now);
            if (kad.prompt) {
                char nm[48], msg[160]; int hu = sn.human;
                if (i != hu && hu >= 0 && hu < sn.n && !dn[hu] && !police && havepos[hu] && havepos[i] && !(sn.r[i].flags & 2) &&
                    fabs(pos[hu][1] - pos[i][1]) <= 2.0f * KAD_M) {
                    float d = kad_dist(pos[hu], pos[i]);
                    kad_name(i, nm, sizeof nm);
                    if (hp == hu) { snprintf(msg, sizeof msg, "ADRENALINE: getting %s up - keep holding", nm); kad_say(100 + i, 2500, msg, 2.4f); }
                    else if (d <= kad.range * KAD_M && kset_v[3]) { snprintf(msg, sizeof msg, "Hold %s - adrenaline for %s", kad.usekey == 0x45 ? "E" : "Use", nm); kad_say(150 + i, 2500, msg, 2.4f); }
                    else if (d <= kad.prange * KAD_M) { snprintf(msg, sizeof msg, "%s IS DOWN - get to him (%.0f m) for adrenaline and a cut", nm, d / KAD_M); kad_say(200 + i, 4000, msg, 3.0f); }
                }
                /* nothing is said while YOU are down (2026-10-14, the owner: 'it says someone is gonna help me but they arent'): the AI
                   heisters have no revive animation, so a line about one would promise what the screen does not show */
            }
            if (pl && klh_rd(pl + 0xa54, &usedw, 4)) { use = (BYTE)((usedw & 2) != 0); if (kad.log >= 2 && (usedw != kad_g.use_dw)) { klog("adren: [player+0xa54] %08lx -> %08lx (bit 2, the GUESSED 'use key held': %d)", (unsigned long)kad_g.use_dw, (unsigned long)usedw, use); kad_g.use_dw = usedw; } }
            if (hp < 0) { if (k->fast && pl && i == sn.human) { BYTE z = 0; klh_data((void *)(DWORD_PTR)(D + 0x29), &z, 1, "player: the fast get-up byte back (adrenaline)"); k->fast = 0; } continue; }
            k->hm[hp] += dt * 1000u / 1024u;
            if (hp == sn.human && i != sn.human && dnd[i]) KAD_AN_TRY(i, k, pl, pos[i], dnd[i], klh_rd32(dnd[i] + 4));     /* Anim: the human kneels and gives the shot */
            if (hp != sn.human && (sn.r[hp].flags & 1)) KAD_BA_TRY(&sn, i, hp, pos[hp], pos[i], pl);                   /* BotAnim: an AI heister kneels and gives it */
            if (kad.log >= 2 && now >= kad_g.nextlog) { kad_g.nextlog = now + 1000; klog("adren: record %d is helped by record %d (%s), %.1f m away, %lu ms so far", i, hp, hp == sn.human ? "you" : "a bot", dist[hp] / KAD_M, (unsigned long)k->hm[hp]); }
            if (kad.dry) continue;
            if (i == sn.human) {
                /* the mash meter: the same condition as kldown.c's press count (a get-up it drives, or a landed Flop fall) */
                if (kld.on && (kld_s.up || (KLD_ONE && kld_s.fnow && kld_s.t_land && !kld_s.fdone))) {
                    if (kld_s.meter < kad.meter * kltt_get(hp, KLTT_ADREN)) kld_s.meter = kad.meter * kltt_get(hp, KLTT_ADREN);      /* kltrait.c Adrenaline of the helper's character */
                }
                if (kad.humanfast && ds == 1 && !k->fast) {
                    BYTE one = 1, cur = 0;
                    if (klh_rd(D + 0x29, &cur, 1) && !cur && klh_data((void *)(DWORD_PTR)(D + 0x29), &one, 1, "player: the fast get-up byte (adrenaline)")) { k->fast = 1; klog("adren: HumanFast - [D+0x29] = 1: the game's own fast get-up (speed 2.5) is asked while record %d stands by him", hp); }
                }
            } else if (dnd[i] && !KAD_BA_HOLDING(i)) {             /* BotAnimHold: while a bot's shot runs on him the shot ends his lie, not the Rate */
                DWORD cur = klh_rd32(dnd[i] + 0x14), done = 0, nw = kad_lie_step(cur, tick, dt, 1.0f + (kad.rate - 1.0f) * kltt_get(hp, KLTT_ADREN), &done);      /* kltrait.c Adrenaline of the HELPER's character */
                if (nw != cur && klh_data((void *)(DWORD_PTR)(dnd[i] + 0x14), &nw, 4, "an AI heister's down-not-dead: the tick he lies until (adrenaline)")) k->sped += done;
            }
            (void)use; (void)j;
        }
    }
    if (!kad.dry) KAD_AN_INJECT(&sn, dnd, tick);           /* Anim: the shot lands at AnimInjectFrame */
    KAD_BA_TEST(&sn, pos, havepos, dn, pl);                /* BotAnimTest (a test key, off): the nearest bot plays it towards you */
    KAD_BA_TICK(&sn, dnd, tick);                           /* BotAnim: the kneeling bots - their shot, their end */
    /* a crewmate that DIED (status 7) while a mark of ours stands: the mark is the game's from now on */
    for (i = 0; i < sn.n; i++) if (sn.r[i].used && sn.r[i].status == 7 && !kad_r[i].down)
        for (j = 0; j < KLB_NREC; j++) if (kad_m[j].on && !kad_m[j].keep) { kad_m[j].keep = 1; klog("adren: record %d died while the mark of record %d stands: the mark is the game's to keep now", i, j); }
    /* the words for the next pass */
    for (i = 0; i < sn.n; i++) { WORD w = 0; if (kad_g.kwok[i] && klh_rd(sn.score + 0x1b8 + 2 * i, &w, 2)) kad_g.kw[i] = w; else kad_g.kw[i] = 0xffff; }
    kad_g.state = state;
}

/* ---------------------------------------------------------------- init */

static float kad_inif(const char *key, const char *def, float lo, float hi)
{
    char t[40]; float v;
    GetPrivateProfileStringA("Adrenaline", key, def, t, sizeof t, klh_ini);
    v = (float)atof(t);
    if (!(v == v) || v < lo || v > hi) v = (float)atof(def);
    return v;
}

static void kad_init(void)
{
    memset(&kad, 0, sizeof kad); memset(kad_r, 0, sizeof kad_r); memset(kad_m, 0, sizeof kad_m); memset(&kad_g, 0, sizeof kad_g);
    kad.on = GetPrivateProfileIntA("Adrenaline", "Enable", 0, klh_ini) != 0;
    if (!kad.on) return;
    kad.dry = GetPrivateProfileIntA("Adrenaline", "Dry", 0, klh_ini) != 0;
    kad.log = GetPrivateProfileIntA("Adrenaline", "Log", 1, klh_ini);
    kad.needuse = GetPrivateProfileIntA("Adrenaline", "NeedUse", 1, klh_ini) != 0;        /* 2026-10-14: hold E (UseKey) by him, as for a gun on the floor */
    kad.usekey = GetPrivateProfileIntA("Adrenaline", "UseKey", 0x45, klh_ini) & 0xff;      /* a virtual-key code: 0x45 = E; 0 = only the game's own bit */
    kad.humanfast = GetPrivateProfileIntA("Adrenaline", "HumanFast", 0, klh_ini) != 0;
    kad.share_bot = GetPrivateProfileIntA("Adrenaline", "ShareBot", 1, klh_ini) != 0;
    kad.bank = GetPrivateProfileIntA("Adrenaline", "ShareBank", 1, klh_ini) != 0;
    kad.mark = GetPrivateProfileIntA("Adrenaline", "Mark", 0, klh_ini) != 0;   /* review 3: OFF until check A4 shows the word rises only for crew victims */
    kad.fine = GetPrivateProfileIntA("Adrenaline", "MarkFine", 0, klh_ini) != 0;
    kad.take = GetPrivateProfileIntA("Adrenaline", "Take", 1, klh_ini) != 0;
    kad.range = kad_inif("Range", "2.5", 0.5f, 10.0f);
    kad.brange = kad_inif("BotRange", "4.0", 0.5f, 15.0f);
    kad.rate = kad_inif("Rate", "3.0", 1.0f, 10.0f);
    kad.meter = kad_inif("Meter", "3.0", 0.0f, 20.0f);
    kad.minhelp = kad_inif("MinHelp", "1.0", 0.0f, 10.0f);
    kad.share = kad_inif("Share", "0.25", 0.0f, 1.0f);
    kad.bothelp = GetPrivateProfileIntA("Adrenaline", "BotHelp", 1, klh_ini) != 0;
    kad.rush = GetPrivateProfileIntA("Adrenaline", "Rush", 1, klh_ini) != 0;
    kad.rushrange = kad_inif("RushRange", "25", 2.0f, 80.0f);
    kad.rushvan = GetPrivateProfileIntA("Adrenaline", "RushVan", 0, klh_ini) != 0;      /* 0 = off (default); see kad_vanlive */
    kad.rushvanrange = kad_inif("RushVanRange", "8", 0.0f, 80.0f);                      /* GUESS */
    if (kad.rushvan) klog("adren: RushVan=1: while the escape vehicle is called or waits, no rush-back and a new rush only within %.0f m", kad.rushvanrange);
    kad.prompt = GetPrivateProfileIntA("Adrenaline", "Prompt", 1, klh_ini) != 0;
    kad.prange = kad_inif("PromptRange", "30", 2.0f, 60.0f);      /* 30 (was 12) since 2026-10-15: the owner never saw a downed crewmate prompt */
    KAD_AN_INIT();
    KAD_BA_INIT();
    klog("adren: on%s; a downed crewmate gets up faster with a helper within %.1f m (a bot by a downed human: %.1f m; NeedUse=%d); AI lie x%.1f, your mash meter at least %.1f (HumanFast=%d); the helper gets %.0f %% of what the helped man carries (%s, Take=%d, ShareBot=%d); Mark=%d MarkFine=%d. Arcade on a level that is not stock, not for a police human; data writes only (re\\adrenaline.md)",
         kad.dry ? " (Dry=1: nothing is written)" : "", kad.range, kad.brange, kad.needuse, kad.rate, kad.meter, kad.humanfast, kad.share * 100.0f, kad.bank ? "banked for a human" : "carried", kad.take, kad.share_bot, kad.mark, kad.fine);
    klog("adren: Prompt=%d (the centre announcement says who is down near you, that you are helping, who is coming for you; PromptRange %.0f m)", kad.prompt, kad.prange);
    klog("adren: BotHelp=%d (an AI heister by a downed AI heister helps and earns as a human would), Rush=%d (the nearest free AI heister within %.0f m on the same floor RUNS to a downed crewmate, and goes back to his own place when the man is up)", kad.bothelp, kad.rush, kad.rushrange);
    if (!kld.on) klog("adren: [Down] Enable=0 - the human's knock-down is the game's own plain one: the meter cannot be driven (HumanFast=1 can still ask the fast get-up); an AI heister only lies when [Down] Bots=1 (or the game puts him down)");
    else if (!kld_bk.on) klog("adren: [Down] Bots=0 - no AI heister goes down, so only the human side acts (a bot by a downed human); set [Down] Bots=1 (BotsLie=6 gives the adrenaline something to speed)");
}
