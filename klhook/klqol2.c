/*
 * klqol2.c - [QoL2] in-game quality of life, round 2 (track qol2, 2026-10-23). Part of KLHook (included by klhook.c after
 * klpm_arc.c, SHIP and TEST alike: it uses klslot.c's window-stack reader, klbot.c's crew snapshot, klescort.c's order call,
 * klcrew_rt.c's teleport and klhop.c's landing places). Names begin with kqb_ / KQB_ (klqol.c owns klq2_). Every key defaults to
 * the game as it is: with no [QoL2] section nothing here runs. NOTHING HERE HAS RUN IN THE GAME (the lead runs the live test in
 * re/qol2_1023.md). No code byte of kl2.exe changes; no new patch site.
 *
 * 1. WATCHDOG - a STUCK AI HEISTER gets help ([QoL2] Watchdog=1)
 *    Owner's list of what is still wrong with the crew: "stuck AI heister with no recovery". klmove.c's Restless already re-orders a bot
 *    that stood still, but (a) it is off unless [Bots] Restless is set, (b) it gives up on a bot after 4 orders on one spot / 6 per place
 *    ("left until its chain orders another place") and (c) its RestlessSnap needs its own keys. This is a last line of defence that is
 *    independent of all three: it keeps its own clock per bot (does not read klmove.c's records, so it works with Restless=0).
 *    Twice a second, on the game's thread, in an Arcade round that runs (session state 0x19) on a level that is NOT stock (klb_level, as
 *    klmove.c / klhop.c do), for every AI crew record in play (loyal, not a traitor, status 0):
 *      - it "stood" when its node place did not move more than WatchMoveCm (100 = 1 m) since the clock started;
 *      - it is NOT judged while: the round is younger than WatchAfter s (default 20: the rappel / start walk); it is downed (byte
 *        actor + 0x64c, the byte klbotdown.c / klmove.c's RestlessSkipDowned read - GUESS that it means "downed" here too); it lost health in
 *        the last 4 s (a bot that fights from where it stands); heist stage 3 while a vehicle is called or there (veh 1..5: the board tactic
 *        and the rules own it); aboard / dead / escaped (kle_bot says so); klhop.c walks it (klv_owned); it is within WatchMeantCm
 *        (default 300 = 3 m) of its defend place: a MEANT WAIT (a gate, a cover hold with its timer, a loot wait - klmove.c 3c). So the
 *        watchdog only judges a bot that stands OFF the place its chain ordered. A bot that waits AT its place for ever is not seen here
 *        (that is a chain bug, not a stuck body).
 *      - STEP 1 after WatchStillSec (default 25) of standing: the order it already holds is given again - the soldier's own routine
 *        0x760e50 through klescort.c's kle_order2 (the same call klmove.c's branch b makes: place = the defend block's place, so nothing of
 *        the route is chosen here). Logged: "qol2: watchdog: record i ... ORDER AGAIN".
 *      - STEP 2 after WatchTeleSec (default 20) MORE seconds of the same standing (the bot has not moved 1 m since step 1): the bot is put
 *        on its next route / hop place by the game's own actor teleport (klt_teleport, the call klmove.c's RestlessSnap and klhop.c
 *        make), then ordered there (kle_order2). The place, in this order:
 *          a. its defend block's place (the chain's next place) when it lies on the bot's floor (WatchHeightCm, default 600) and within
 *             WatchRangeCm (default 6000 = 60 m); this is what RestlessSnap does;
 *          b. else klhop.c's next free landing place (klv_free) of the level's [CrewHop] hop whose From is nearest to the bot and within
 *             twice that hop's Radius / Height (only when [CrewHop] Enable=1 and the level has a KLJoin.ini hop);
 *          c. else the nearest cover place of klmove.c's [Hops] list (klmv_hops, loaded when [Bots] RestlessHop is on) that is 3 m or more
 *             from the bot and on its floor.
 *        Not teleported (said once per bot): a human heister in play within WatchSeenCm (default 1500 = 15 m) of the bot or of the place
 *        (it must not pop in front of his eyes: step 1 repeats instead, every WatchTeleSec), klt_refuse() names a fault, the bot is held as a
 *        human shield, the teleport routine is not the known one. At most WatchMax (default 3) teleports per bot and round.
 *      - WatchDry=1: everything is judged and logged, nothing is called ("WOULD").
 *    Every decision is a klog line; the lead's check is grep "qol2:" KLHook.log.
 *    GUESS: the node place [actor+4] is the place of the bot (klmove.c / klhop.c use both this and +0x460; "neither reading was checked
 *    against the other"), 25 s / 20 s / 3 m / 15 m / 60 m / 6 m are tuning guesses, the +0x64c byte is "downed".
 *
 * 2. HEISTER PAGE SHORTCUT ([QoL2] HeisterKey=<virtual-key code>, default 0 = none)
 *    The Heister button is the first button added under the five stock ones of the Arcade page (window HeistModeMenu, mkoverlay.py;
 *    re\wardrobe.md 5), so the owner presses DOWN five times from the page's first button. ENGINE RESEARCH THAT WOULD BE NEEDED for a
 *    direct jump: the focus lives in ZWINDOWS (vtable 0xbab94c) slot 161 = 0x7f09f0 SetFocus(window object); klauto.c only learns the
 *    ZWINDOWS pointer from a detour on that very call (TEST build, breadcrumb hooks), there is no static address for it, and moving
 *    the focus without the page's key handler is unproven. NOT DONE that way (plan: find the ZWINDOWS global, read [zw+0x58] to know the
 *    focused element, call SetFocus with the Heister button's window object [element + 0x88] where the element comes from the proven
 *    find 0x83faf0 (klslot.c kls_page_clamp) - one live probe).
 *    What this does instead is the same thing the player does, with proven reads and a plain Win32 call: when the key goes DOWN (edge,
 *    only while the game window is in front) and the TOP window of the menu's window stack is HeistModeMenu (read by klslot.c's
 *    call-free kls_win_name, the same read kls_menu_watch uses), it sends HeisterDowns (default 5) DOWN-arrow key taps with SendInput
 *    (scan code 0xD0 + extended flag, 70 ms apart, one per tick-slot). The window stack is read again before every tap: if the top window
 *    is no longer HeistModeMenu (the player pressed Enter / Esc), the rest is dropped.
 *    GUESS 1: DirectInput's keyboard (the game reads it with GetDeviceData, klauto.c) sees a SendInput scan-code event (usual for DirectInput
 *    games; unproven for this one - if not, the log shows the taps and the focus does not move). GUESS 2: the page's focus is on its first
 *    button when the key is pressed (the page opens so; a player who has moved gets a wrong row - HeisterUps=<n> sends n UP taps FIRST to
 *    run back to the top; default 0, and it is not known whether the menu wraps, so more than the button count is harmless only if it does
 *    not wrap). GUESS 3: the mask gap - the Heister button is the sixth. HeisterDowns is the knob when a build has other buttons first.
 *    Keys: HeisterKey (VK, e.g. 72 = 0x48 'H'; 0 = off), HeisterDowns=5, HeisterUps=0.
 *
 * 3. MUTE WHEN UNFOCUSED ([QoL2] MuteBackground=1; from the notes' "not done" list)
 *    While another program is in front, the game's audio session volume is set to MuteLevelPct (default 0 %) and put back when the game is
 *    in front again. The notes' worry was "COM init on the game thread is unproven": this uses a thread of its own (started on the first game
 *    tick, not in DllMain) that does CoInitializeEx(MTA), IMMDeviceEnumerator -> default render endpoint -> IAudioSessionManager ->
 *    GetSimpleAudioVolume(NULL: this process's default session) -> SetMasterVolume, poll 250 ms. ole32 / user32 are resolved at run time
 *    (no new import). It silences everything the process plays, the winmm MCI jukebox and ambience (klmusic.c / klambience.c) included.
 *    A crash-safe habit: the volume the thread found is kept; at start it is put back to 100 % if it is found at exactly MuteLevelPct while the
 *    game is in front (Windows remembers a per-app volume, so a game closed while muted would start muted next time). GUESS: the game's sound
 *    goes through this process's default audio session (an engine that opens its own session group would not be muted; the live test says so).
 *    Keys: MuteBackground=0, MuteLevelPct=0 (0..90).
 *
 * KLHook.ini
 *   [QoL2]
 *   Watchdog=0          1 = a stuck AI heister is ordered again, later put on its next place (section 1)
 *   WatchStillSec=25    standing this long (8..300) -> step 1
 *   WatchTeleSec=20     still standing this long after step 1 (5..300) -> step 2
 *   WatchMoveCm=100     a bot that moved more than this has not stood
 *   WatchMeantCm=300    within this of its defend place = a meant wait, never judged
 *   WatchAfter=20       seconds from the round start before any bot is judged
 *   WatchRangeCm=6000   farthest the defend place may be for the teleport (a)
 *   WatchHeightCm=600   highest/lowest above/below the bot a teleport place may be
 *   WatchSeenCm=1500    no teleport within this of a living human heister (bot or place)
 *   WatchMax=3          teleports per bot and round
 *   WatchDry=0          1 = log only
 *   HeisterKey=0        virtual-key code of the shortcut, decimal (72) or 0x hex (0x48), 0 = none
 *   HeisterDowns=5      DOWN taps sent
 *   HeisterUps=0        UP taps sent first
 *   MuteBackground=0    1 = mute while another program is in front
 *   MuteLevelPct=0      volume while in the background (0..90)
 *   Log=1               0 = no 'qol2:' lines
 */
#ifndef KLQOL2_C
#define KLQOL2_C

#include <mmdeviceapi.h>
#include <audiopolicy.h>

static struct {
    int wd, wd_dry, log;
    DWORD still_ms, tele_ms, after_ms; float move, meant, range, height, seen; int max_tele;
    int hkey, downs, ups;
    int mute, mute_pct;
    int resolved, ok;
    BOOL  (WINAPI *p_sendinput)(UINT, LPINPUT, int);
    SHORT (WINAPI *p_asyncstate)(int);
    HWND  (WINAPI *p_fg)(void);
    DWORD (WINAPI *p_tid)(HWND, LPDWORD);
} kqb;

/* ---------------------------------------------------------------- 1. the watchdog */

struct kqb_b {
    DWORD actor, since, order_at, hit_at, retry_at; int seen, step, teles; float pos[3], hp; BYTE told;      /* told: 1 meant wait said, 2 refusal said, 4 no place said, 8 order refusal said */
};
static struct { DWORD rules, state, round_at, last; struct kqb_b b[KLB_NREC]; int told_gate; } kqb_r;

static float kqb_h(const float a[3], const float b[3]) { return (float)sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[2] - b[2]) * (a[2] - b[2])); }

/* the next place for a bot that stands still and whose own place is no answer: klhop.c's next free landing place (b), else klmove.c's
   nearest cover place (c). -> 1 and *out, 0 = none. */
static int kqb_other_place(const struct klb_snap *s, const float bp[3], float out[3], DWORD now, const char **how, int dry)
{
    int hi, j, best = -1; float bd = 1e30f;
    if (klv.on && klt_tele_known()) {
        char scene[160], key[64];
        if (klh_scene(scene, sizeof scene) && klh_level_key(scene, key, sizeof key)) {
            klv_source();
            if (klv_lv.n && !strcmp(key, klv_lv.key)) {
                int bh = -1;
                for (hi = 0; hi < KLV_NHOP; hi++) {
                    const struct klv_hop *h = &klv_lv.h[hi]; float d;
                    if (!h->on || h->walk) continue;
                    d = kqb_h(bp, h->from);
                    if (d <= 2.0f * h->radius && fabs(bp[1] - h->from[1]) <= 2.0f * h->height && d < bd) { bd = d; bh = hi; }
                }
                if (bh >= 0) {
                    int p = klv_free(bh, s, now);      /* GUESS: klv_free's "free place" test is the one a carried bot needs here too */
                    if (p >= 0) {
                        memcpy(out, klv_lv.h[bh].to[p], 12);
                        if (!dry) { klv_r.used[bh][p] = KLB_T(now); klv_r.next[bh] = (p + 1) % klv_lv.h[bh].nto; }      /* klhop.c hands it to nobody else for 2 s; a dry run reserves nothing */
                        *how = "klhop landing place"; return 1;
                    }
                }
            }
        }
    }
    bd = 1e30f;
    for (j = 0; j < klmv_nhop; j++) {
        float d = kqb_h(bp, klmv_hops[j]);
        if (d >= 300.0f && fabs(bp[1] - klmv_hops[j][1]) <= kqb.height && d < bd) { bd = d; best = j; }
    }
    if (best >= 0) { memcpy(out, klmv_hops[best], 12); *how = "klmove cover place"; return 1; }
    return 0;
}

static void kqb_watch(const struct klb_snap *s, DWORD now, int human_in, const float hp[3])
{
    int i;
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; struct kqb_b *b = &kqb_r.b[i];
        DWORD node, ho, soldier, actor; float p[3], raw[0x28 / 4], cur[3], bp[3], want[3], got[3]; char w[100]; int fire, k; BYTE dn = 0;
        if (r->used && r->actor != b->actor) { memset(b, 0, sizeof *b); b->actor = r->actor; }
        if (!r->used || !(r->flags & 1) || (r->flags & 2) || r->status || !r->actor || klh_rd32(r->actor) != KLB_ACTOR_VT
            || !(node = klh_rd32(r->actor + 4)) || !kle_node(node, p, 0)) { b->seen = 0; b->step = 0; continue; }
        if (!b->seen || kle_dist(p, b->pos) > kqb.move) { memcpy(b->pos, p, 12); b->since = now; b->seen = 1; b->step = 0; }      /* moved: the clock and the steps start again */
        if ((ho = klh_rd32(r->actor + 0x5fc)) != 0 && klh_rd(ho, raw, sizeof raw) && ((DWORD *)raw)[0x24 / 4] == r->actor && klb_finite(raw[1])) {      /* klbot.c's health read */
            if (b->hp > 0 && raw[1] < b->hp - 0.05f) b->hit_at = KLB_T(now);
            b->hp = raw[1];
        }
        fire = b->hit_at && now - b->hit_at < 4000;
        if (now - kqb_r.round_at < kqb.after_ms) { b->since = now; continue; }
        if (klh_rd(r->actor + 0x64c, &dn, 1) && dn) { b->since = now; b->step = 0; continue; }      /* GUESS: downed (klbotdown.c) */
        if (fire || (r->stage >= 3 && s->veh >= 1 && s->veh <= 5) || klv_owned(i)) { b->since = now; continue; }
        if (now - b->since < kqb.still_ms) continue;
        if (!kle_bot(s, i, &actor, &soldier, bp, w)) continue;
        if (!kle_block(soldier, cur) || !(cur[0] || cur[1] || cur[2])) continue;
        if (kqb_h(bp, cur) <= kqb.meant && fabs(bp[1] - cur[1]) <= 300.0f) {
            if (!(b->told & 1)) { b->told |= 1; if (kqb.log) klog("qol2: watchdog: record %d stands %.0f s at (%.0f, %.0f, %.0f) within %.1f m of its defend place: a meant wait, left alone (said once per bot)", i, (now - b->since) / 1000.0, bp[0], bp[1], bp[2], kqb_h(bp, cur) / 100); }
            continue;
        }
        if (b->step == 2) b->step = 0;      /* review 1: it stood still_ms again after a teleport / a dry-run WOULD: judged afresh, so WatchMax and repeats are reachable */
        if (b->step == 0) {
            struct kle_e t;
            if (b->retry_at && now - b->retry_at < 5000) continue;      /* review 3: a refused order is retried every 5 s, not every tick */
            memcpy(want, cur, 12);
            memset(&t, 0, sizeof t); t.rec = i; t.actor = actor; t.soldier = soldier; t.told_soft = 1;
            k = kle_order2(&t, want, got, w, kqb.wd_dry);
            b->order_at = KLB_T(now);
            if (!k) { if (!(b->told & 8) && kqb.log) klog("qol2: watchdog: record %d stood %.0f s at (%.0f, %.0f, %.0f), %.1f m from its place: NOT ordered: %s (tries again every 5 s; said once per bot)", i, (now - b->since) / 1000.0, bp[0], bp[1], bp[2], kqb_h(bp, cur) / 100, w); b->told |= 8; b->order_at = 0; b->retry_at = KLB_T(now); continue; }
            b->retry_at = 0;
            b->step = 1;
            if (kqb.log) klog("qol2: watchdog: record %d (stage %u) stood %.0f s at (%.0f, %.0f, %.0f), %.1f m from its place (%.0f, %.0f, %.0f): %s (step 1 of 2); the game set (%.0f, %.0f, %.0f); a teleport follows in %.0f s if it still stands",
                              i, r->stage, (now - b->since) / 1000.0, bp[0], bp[1], bp[2], kqb_h(bp, cur) / 100, cur[0], cur[1], cur[2], k == 2 ? "ORDER AGAIN would be given (dry run)" : "ORDER AGAIN", got[0], got[1], got[2], kqb.tele_ms / 1000.0);
            continue;
        }
        if (b->step == 1 && now - b->order_at >= kqb.tele_ms) {      /* the same stillness, tele_ms after the order: step 2 */
            const char *no = 0, *how = "its defend place"; int have = 0; float to[3];
            if (b->teles >= kqb.max_tele) { if (!(b->told & 4)) { b->told |= 4; if (kqb.log) klog("qol2: watchdog: record %d stands still again after %d teleport(s) this round (WatchMax): left alone (said once per bot)", i, b->teles); } continue; }
            if (!klt_tele_known()) no = "the game's teleport routine is not the one this build knows";
            else if ((no = klt_refuse(actor)) == 0 && klh_rd32(actor + 0x770)) no = "it is held as a human shield";
            if (!no) {
                if (kqb_h(bp, cur) <= kqb.range && fabs(bp[1] - cur[1]) <= kqb.height) { memcpy(to, cur, 12); have = 1; }
                else have = kqb_other_place(s, bp, to, now, &how, kqb.wd_dry);
                if (!have) no = "no place to put it (its defend place is beyond WatchRangeCm / WatchHeightCm and the level has no free hop place near)";
            }
            if (!no && human_in && ((kqb_h(hp, bp) <= kqb.seen && fabs(hp[1] - bp[1]) <= 600.0f) || (kqb_h(hp, to) <= kqb.seen && fabs(hp[1] - to[1]) <= 600.0f))) no = "a human heister is near the bot or the place";
            if (no) {
                if (!(b->told & 2)) { b->told |= 2; if (kqb.log) klog("qol2: watchdog: record %d stood %.0f s at (%.0f, %.0f, %.0f) and is NOT teleported: %s (the order is given again; said once per bot)", i, (now - b->since) / 1000.0, bp[0], bp[1], bp[2], no); }
                b->step = 0; b->since = now - (kqb.still_ms > 0 ? kqb.still_ms : 0);      /* judged again next pass: step 1 repeats (the debounce of kle_order2 applies) */
                continue;
            }
            if (kqb.wd_dry) { klog("qol2: watchdog: record %d stood %.0f s: WOULD be put on (%.0f, %.0f, %.0f) [%s] - DRY RUN", i, (now - b->since) / 1000.0, to[0], to[1], to[2], how); b->step = 2; b->since = now; continue; }
            {
                struct kle_e t; float is[3] = { 0, 0, 0 }; double stood = (now - b->since) / 1000.0; int isok;
                klt_teleport(actor, to);
                kltr_tp(i, "qol2-watchdog", to, "stuck AI heister: put on its next place");
                memset(&t, 0, sizeof t); t.rec = i; t.actor = actor; t.soldier = soldier; t.told_soft = 1;
                k = kle_order2(&t, to, got, w, 0);      /* its order becomes the place it stands on (as klhop.c OrderTo); a refusal is only said */
                isok = kle_node(klh_rd32(actor + 4), is, 0);
                b->teles++; b->step = 2; if (isok) memcpy(b->pos, is, 12); else memcpy(b->pos, to, 12); b->since = now;
                klog("qol2: watchdog: record %d (stage %u) stood %.0f s at (%.0f, %.0f, %.0f) after its order was given again: TELEPORTED to (%.0f, %.0f, %.0f) [%s], now (%.0f, %.0f, %.0f)%s (time %d of %d)",
                     i, r->stage, stood, bp[0], bp[1], bp[2], to[0], to[1], to[2], how, is[0], is[1], is[2], k ? "; ordered there" : "; NOT ordered there", b->teles, kqb.max_tele);
            }
        }
    }
}

static void kqb_watch_tick(int game_thread, DWORD now)
{
    struct klb_snap s; char why[200]; const struct klb_rec *h; float hp[3], hn[3]; DWORD player; int human_in, i, stages = 0;
    if (!kqb.wd || !klh_exe_ok || now - kqb_r.last < 500) return;
    kqb_r.last = KLB_T(now);
    if (!klb_read(&s)) { kqb_r.rules = 0; return; }
    for (i = 0; i < s.n; i++) if (s.r[i].used) stages += s.r[i].stage;
    if (s.rules != kqb_r.rules || (s.state == KLB_ROUND && kqb_r.state != KLB_ROUND)) {      /* a new round */
        memset(&kqb_r, 0, sizeof kqb_r); kqb_r.rules = s.rules; kqb_r.round_at = KLB_T(now); kqb_r.last = KLB_T(now);
    }
    kqb_r.state = s.state;
    if (s.state != KLB_ROUND || !game_thread) return;
    if (!klb_level(why)) { if (!kqb_r.told_gate++ && kqb.log) klog("qol2: watchdog: %s: nobody is helped here (only on a level that is not stock)", why); return; }
    h = s.human >= 0 ? &s.r[s.human] : 0;
    human_in = h && h->status == 0 && kle_human(&player, hp, hn);
    kqb_watch(&s, now, human_in, hn);
}

/* ---------------------------------------------------------------- 2. the Heister page shortcut */

static struct { int armed, sent, total_up, total_down, held; DWORD at; } kqb_k;

static int kqb_top_is_arcade(void)
{   /* the top window of the menu's window stack is HeistModeMenu: klslot.c kls_menu_watch's reads, no game call */
    DWORD gd, mgr, w, n, top; char nm[64];
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(mgr = klh_rd32(gd + 0x824)) || klh_rd32(mgr) != KLS_MENUMGR_VT || !(w = klh_rd32(mgr + 4)) || klh_rd32(w) != KLS_WSYS_VT) return 0;
    n = klh_rd32(w + 0x328);
    if (!n || n > 24 || !klh_rd(w + 0x32c + 4 * n, &top, 4) || !top) return 0;      /* windows at +0x32c + 4*i, i = 1..n, the top one last */
    if (!kls_win_name(top, nm, sizeof nm)) return 0;
    return !strcmp(nm, "HeistModeMenu");
}

static int kqb_front3(void)
{   /* 1 = a window of this process is in front, 0 = another program, -1 = unknown (no foreground window: alt-tab, UAC) */
    DWORD pid = 0; HWND f = kqb.p_fg();
    if (!f) return -1;
    kqb.p_tid(f, &pid);
    return pid == GetCurrentProcessId();
}
static int kqb_front(void) { return kqb_front3() == 1; }

static void kqb_tap(int down, int up)
{   /* a scan-code key event: DOWN arrow = 0xD0, UP arrow = 0xC8 with the extended flag; the game reads DirectInput, which sees scan codes (GUESS 1) */
    INPUT in[2]; BYTE sc = (BYTE)(down ? 0xD0 : 0xC8);
    (void)up;
    memset(in, 0, sizeof in);
    in[0].type = INPUT_KEYBOARD; in[0].ki.wScan = (WORD)(sc & 0x7f); in[0].ki.dwFlags = KEYEVENTF_SCANCODE | KEYEVENTF_EXTENDEDKEY;
    in[1].type = INPUT_KEYBOARD; in[1].ki.wScan = (WORD)(sc & 0x7f); in[1].ki.dwFlags = KEYEVENTF_SCANCODE | KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP;
    kqb.p_sendinput(2, in, sizeof(INPUT));
}

static void kqb_key_tick(DWORD now)
{
    int down;
    if (!kqb.hkey) return;
    down = (kqb.p_asyncstate(kqb.hkey) & 0x8000) != 0;
    if (down && !kqb_k.held && !kqb_k.armed && kqb_front()) {
        if (kqb_top_is_arcade()) {
            kqb_k.armed = 1; kqb_k.total_up = kqb.ups; kqb_k.total_down = kqb.downs; kqb_k.sent = 0; kqb_k.at = 0;
            if (kqb.log) klog("qol2: heister shortcut: the Arcade page (HeistModeMenu) is on top: %d UP, then %d DOWN taps", kqb.ups, kqb.downs);
        } else if (kqb.log) klog("qol2: heister shortcut: key pressed but the top window is not HeistModeMenu - ignored");
    }
    kqb_k.held = down;
    if (!kqb_k.armed || (kqb_k.at && now - kqb_k.at < 70)) return;
    if (!kqb_front() || !kqb_top_is_arcade()) { if (kqb.log) klog("qol2: heister shortcut: the Arcade page is gone after %d tap(s): the rest is dropped", kqb_k.sent); kqb_k.armed = 0; return; }
    if (kqb_k.sent < kqb_k.total_up + kqb_k.total_down) {
        int isdown = kqb_k.sent >= kqb_k.total_up;
        kqb_tap(isdown, !isdown); kqb_k.sent++; kqb_k.at = KLB_T(now);
    }
    if (kqb_k.sent >= kqb_k.total_up + kqb_k.total_down) { kqb_k.armed = 0; if (kqb.log) klog("qol2: heister shortcut: %d tap(s) sent (check the focus on the Heister button)", kqb_k.sent); }
}

/* ---------------------------------------------------------------- 3. mute while another program is in front */

static const GUID kqb_CLSID_Enum = { 0xBCDE0395, 0xE52F, 0x467C, { 0x8E, 0x3D, 0xC4, 0x57, 0x92, 0x91, 0x69, 0x2E } };      /* CLSID_MMDeviceEnumerator */
static const GUID kqb_IID_Enum   = { 0xA95664D2, 0x9614, 0x4F35, { 0xA7, 0x46, 0xDE, 0x8D, 0xB6, 0x36, 0x17, 0xE6 } };      /* IID_IMMDeviceEnumerator */
static const GUID kqb_IID_Mgr    = { 0xBFA971F1, 0x4D5E, 0x40BB, { 0x93, 0x5E, 0x96, 0x70, 0x39, 0xBF, 0xBE, 0xE4 } };      /* IID_IAudioSessionManager */

static volatile LONG kqb_mute_state;                  /* thread: 0 not started, 1 running, -1 gave up */
static volatile LONG kqb_muted;

static DWORD WINAPI kqb_mute_thread(LPVOID unused)
{
    HMODULE ole = LoadLibraryA("ole32.dll");
    HRESULT (WINAPI *p_init)(LPVOID, DWORD) = ole ? (HRESULT (WINAPI *)(LPVOID, DWORD))GetProcAddress(ole, "CoInitializeEx") : 0;
    HRESULT (WINAPI *p_create)(REFCLSID, LPUNKNOWN, DWORD, REFIID, LPVOID *) = ole ? (HRESULT (WINAPI *)(REFCLSID, LPUNKNOWN, DWORD, REFIID, LPVOID *))GetProcAddress(ole, "CoCreateInstance") : 0;
    IMMDeviceEnumerator *en = 0; IMMDevice *dev = 0; IAudioSessionManager *mgr = 0; ISimpleAudioVolume *vol = 0;
    float level = kqb.mute_pct / 100.0f, orig = 1.0f; int muted = 0, first = 1, front_prev = 1, nfront = 0; DWORD retry = 0;
    (void)unused;
    if (!p_init || !p_create || FAILED(p_init(0, 0 /* COINIT_MULTITHREADED */))) { klog("qol2: mute: COM could not be started - MuteBackground does nothing"); InterlockedExchange(&kqb_mute_state, -1); return 0; }
    for (;;) {
        int fs = kqb_front3(), front;
        DWORD now = GetTickCount();
        /* review 6: no foreground window = unchanged; 'not in front' must hold for 2 polls (500 ms) before the mute */
        if (fs == 1) { front_prev = 1; nfront = 0; } else if (fs == 0) { if (++nfront >= 2) front_prev = 0; }
        front = front_prev;
        if (!vol && (!retry || now - retry >= 5000)) {
            retry = KLB_T(now);
            if (SUCCEEDED(p_create(&kqb_CLSID_Enum, 0, CLSCTX_ALL, &kqb_IID_Enum, (LPVOID *)&en)) &&
                SUCCEEDED(en->lpVtbl->GetDefaultAudioEndpoint(en, eRender, eConsole, &dev)) &&
                SUCCEEDED(dev->lpVtbl->Activate(dev, &kqb_IID_Mgr, CLSCTX_ALL, 0, (void **)&mgr)) &&
                SUCCEEDED(mgr->lpVtbl->GetSimpleAudioVolume(mgr, 0, FALSE, &vol))) {
                float v = 1.0f;
                vol->lpVtbl->GetMasterVolume(vol, &v);
                if (first && v < 0.999f && v >= level - 0.005f && v <= level + 0.005f) {      /* left muted by a game closed in the background (review 2: front or not; a deliberate per-app volume of MuteLevelPct is forced to 100 %) */
                    vol->lpVtbl->SetMasterVolume(vol, 1.0f, 0); v = 1.0f;
                    klog("qol2: mute: the session volume was found at %.0f %% (a leftover of a muted exit): put back to 100 %%", level * 100);
                }
                orig = v <= level + 0.005f ? 1.0f : v; first = 0;      /* never keep a value at or below the mute level as the one to go back to */
                klog("qol2: mute: audio session found, volume %.0f %%", v * 100);
            } else {
                if (mgr) { mgr->lpVtbl->Release(mgr); mgr = 0; }
                if (dev) { dev->lpVtbl->Release(dev); dev = 0; }
                if (en) { en->lpVtbl->Release(en); en = 0; }
                if (first) { klog("qol2: mute: no audio session yet (tries again every 5 s)"); first = 0; }
            }
        }
        if (vol) {
            if (!front && !muted) { vol->lpVtbl->GetMasterVolume(vol, &orig); if (orig <= level + 0.005f) orig = 1.0f; vol->lpVtbl->SetMasterVolume(vol, level, 0); muted = 1; InterlockedExchange(&kqb_muted, 1); klog("qol2: mute: game in the background - volume %.0f %% -> %.0f %%", orig * 100, level * 100); }
            else if (front && muted) { vol->lpVtbl->SetMasterVolume(vol, orig, 0); muted = 0; InterlockedExchange(&kqb_muted, 0); klog("qol2: mute: game in front - volume back to %.0f %%", orig * 100); }
        }
        Sleep(250);
    }
}

/* ---------------------------------------------------------------- wiring */

static void kqb_resolve(void)
{   /* lazily on the first game tick (not under DllMain's loader lock) */
    HMODULE u = GetModuleHandleA("user32.dll");
    if (!u) u = LoadLibraryA("user32.dll");
    kqb.resolved = 1;
    if (u) {
        kqb.p_sendinput = (BOOL (WINAPI *)(UINT, LPINPUT, int))GetProcAddress(u, "SendInput");
        kqb.p_asyncstate = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState");
        kqb.p_fg = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow");
        kqb.p_tid = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId");
    }
    kqb.ok = kqb.p_sendinput && kqb.p_asyncstate && kqb.p_fg && kqb.p_tid;
    if (!kqb.ok) { klog("qol2: user32 functions not found - the shortcut and the mute do nothing"); return; }
    klog("qol2: Watchdog=%d (still %lu s, then %lu s; dry %d) HeisterKey=%d (%d UP, %d DOWN) MuteBackground=%d (%d %%)", kqb.wd, kqb.still_ms / 1000, kqb.tele_ms / 1000, kqb.wd_dry, kqb.hkey, kqb.ups, kqb.downs, kqb.mute, kqb.mute_pct);
}

static float kqb_inif(const char *key, const char *def, float lo, float hi)
{
    char t[32]; float v;
    GetPrivateProfileStringA("QoL2", key, def, t, sizeof t, klh_ini);
    v = (float)atof(t);
    return !klb_finite(v) ? (float)atof(def) : v < lo ? lo : v > hi ? hi : v;
}

static void kqb_init(void)
{   /* ini only: runs from DllMain */
    kqb.wd = GetPrivateProfileIntA("QoL2", "Watchdog", 0, klh_ini) != 0;
    kqb.wd_dry = GetPrivateProfileIntA("QoL2", "WatchDry", 0, klh_ini) != 0;
    kqb.still_ms = (DWORD)kqb_inif("WatchStillSec", "25", 8, 300) * 1000;
    kqb.tele_ms = (DWORD)kqb_inif("WatchTeleSec", "20", 5, 300) * 1000;
    kqb.after_ms = (DWORD)kqb_inif("WatchAfter", "20", 0, 600) * 1000;
    kqb.move = kqb_inif("WatchMoveCm", "100", 30, 1000);
    kqb.meant = kqb_inif("WatchMeantCm", "300", 100, 2000);
    kqb.range = kqb_inif("WatchRangeCm", "6000", 500, 30000);
    kqb.height = kqb_inif("WatchHeightCm", "600", 100, 3000);
    kqb.seen = kqb_inif("WatchSeenCm", "1500", 0, 10000);
    kqb.max_tele = (int)kqb_inif("WatchMax", "3", 1, 20);
    {   /* review 7: decimal or 0x hex (GetPrivateProfileInt takes decimal only) */
        char t[16]; GetPrivateProfileStringA("QoL2", "HeisterKey", "0", t, sizeof t, klh_ini);
        kqb.hkey = (int)strtol(t, 0, 0);
    }
    if (kqb.hkey < 0 || kqb.hkey > 254) kqb.hkey = 0;
    kqb.downs = (int)kqb_inif("HeisterDowns", "5", 1, 12);
    kqb.ups = (int)kqb_inif("HeisterUps", "0", 0, 12);
    kqb.mute = GetPrivateProfileIntA("QoL2", "MuteBackground", 0, klh_ini) != 0;
    kqb.mute_pct = (int)kqb_inif("MuteLevelPct", "0", 0, 90);
    kqb.log = GetPrivateProfileIntA("QoL2", "Log", 1, klh_ini) != 0;
    kqb.resolved = (!kqb.wd && !kqb.hkey && !kqb.mute);      /* nothing asked for: never resolved, ok stays 0 */
}

static void kqb_tick(int game_thread)
{
    DWORD now;
    if (!game_thread) return;
    if (!kqb.resolved) kqb_resolve();
    if (!kqb.wd && !kqb.ok) return;
    now = GetTickCount();
    if (kqb.wd) kqb_watch_tick(game_thread, now);
    if (!kqb.ok) return;
    if (kqb.hkey) kqb_key_tick(now);
    if (kqb.mute && !kqb_mute_state) {
        HANDLE th;
        InterlockedExchange(&kqb_mute_state, 1);
        th = CreateThread(0, 0, kqb_mute_thread, 0, 0, 0);
        if (th) CloseHandle(th); else { InterlockedExchange(&kqb_mute_state, -1); klog("qol2: mute: the thread could not be started"); }
    }
}

#endif
