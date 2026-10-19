/*
 * klhop.c - THE AI CREW GETS OVER A PLACE THE NAVIGATION MESH DOES NOT CARRY IT OVER: an AI heister that has stood
 * at a named place for some seconds is put on a landing place beyond it by the game's own actor teleport. Made for
 * Withdrawal (the bank, M03_FA_A): owner, 2026-10-10, 'the ai cant leave on withdrawal because theres no climb
 * animation ... they dont go through the wall', 'the van never ends there'; run R12_DM03: seven bots at heist stage
 * 2 in the yard to the end of the round, vehicle state 0 throughout.
 * Part of KLHook (included by klhook.c after klescort.c, SHIP and TEST alike). NO data write and no code byte: calls
 * of ONE game function, 0x62a900, from the game's own thread - the routine and the tests of klcrew_rt.c, through
 * that file's own functions (klt_refuse, klt_tele_known, klt_teleport). With Reorder=1 one more: the soldier's own
 * order routine 0x760e50 (klescort.c's), with the place the soldier's own order already holds.
 * Account, the level's side, the live checks H0..H4: re\bots_bank.md. NOTHING HERE HAS RUN IN THE GAME.
 * Off unless KLHook.ini has [CrewHop] Enable=1. Arcade only (ZGameRulesHeist), never on a stock level.
 *
 * WHY A FILE OF ITS OWN and not more of klcrew_rt.c: that part moves the WHOLE crew ONCE, at the moment of the
 * player's jump, to places counted by the bots' order, and is tied to a jump entry (Name / Target, the debug
 * request, 'AITrigger'). This one has no jump: it watches every bot by itself for the whole round, per hop, with a
 * waiting time, and hands out landing places as they are free. They share the routine, its guards and the side
 * file, nothing of the control flow. What they share is now three functions of klcrew_rt.c, not copied.
 *
 * 1. WHY THE BOTS STOOD THERE (re\bots_bank.md 1; the level data is repaired as well)
 *    The build had a drop link in its navigation mesh (kind 2, 232 across, 70 down) written by tools\kl_fa_bots.py.
 *    The path search 0x5cdd70 reaches a waypoint only through its polygon: 0x5ce320 `ecx = [polygon + 0x10]`
 *    (waypoints before), 0x5ce32c `al = [polygon + 1] ; test al, al ; jbe 0x5ce3a9` - polygon byte +1 is the NUMBER
 *    OF WAYPOINTS ON THE POLYGON (27,384 of 27,384 polygons of the 21 stock meshes), and the tool had left it 0 on
 *    the two polygons it gave a waypoint. So no search ever saw the link. kl_fa_bots.add_drop now raises the byte
 *    (build z_hop\M03). Whether the AI then TAKES the link is still not seen: this file is the way that does not
 *    depend on it, and it stands aside when the link works (a bot that drops is out of the radius before Wait).
 *
 * 2. WHAT THE HOOK DOES
 *    The hops come from the KLJoin.ini beside the level archive - the file kljoin.c reads when the archive is opened
 *    (a file with no [Join] section is taken: '0 box(es)'; never beside a stock archive, kljoin.c drops it there).
 *    In an Arcade round that runs (session state 0x19) on a level that is NOT the stock one of its slot (klbot.c
 *    section 0), on the game's own thread, ten times a second, for every hop and every AI crew record in play
 *    (record +0x79 mask 1, status 0):
 *      - the bot's place = the world place of its node ([actor + 4], composed as klescort.c's kle_node does) and
 *        the three floats at actor + 0x460 (klcrew_rt.c's 'feet'). EITHER within Radius of From in the plan and
 *        within Height of it = the bot is 'at From'. (Neither reading of a bot's place has been checked against the
 *        other in the game: the lines say both, the first live run settles which is right.)
 *      - at From without a break for Wait seconds, at heist stage >= Stage, and (Player=1) after the human was seen
 *        nearer to To.1 than to From: the bot is teleported to the next FREE landing place - not one that was given
 *        away in the last 2 s, not one a crew member (bot or human) stands within 100 of. No free place: next tick.
 *      - at most one bot per 0.5 s, each bot at most once per hop per round, never a bot somebody holds as a human
 *        shield ([actor + 0x770]), never an actor klt_refuse() names a fault of (vtable, node flag, the two int3
 *        pointers, +0x7c0, +0x50c: klcrew_rt.c section 2).
 *    A new round (another rules object, the session state entering 0x19, or the stage sum falling) forgets all.
 *    WHAT THE BOT DOES NEXT. Its route chain (tools\kl_fa_bots.py: DefendBehaviourRout steps) had ended the step of
 *    the gather place and STARTED the next one, whose places lie beyond the drop: the soldier holds a defend order
 *    for a place it found no path to. A Defend step waits until its man is at the place (klescort.c section 1,
 *    0x686c42..), so nothing of the chain is lost while he stands; put on the far mesh part he is where the order
 *    can be walked, and the chain goes on by arriving - no message is needed. ASSUMPTION, the one thing only the
 *    game can show: that the soldier plans a path to the order it already has once it stands on the other part
 *    (0x62a900 with flag 1 resets the animation state and clears [[actor + 0x7c0]]; what that does to a path
 *    request that failed was not read). If the bots land and stand: Reorder=1 gives the soldier its OWN order
 *    again half a second after the hop - soldier vtable +0x13c = 0x760e50 with (the place its defend block
 *    holds, 0, 1, 0), the arguments of a Defend step, the call klescort.c makes (its tests, its helper
 *    kle_callable). The place is the soldier's own: nothing of the route is chosen here.
 *    And without either: on the bank the landing places are inside the level exit box, which gives the bot heist
 *    stage 3 and calls the escape vehicle; while the vehicle waits a stage-3 bot boards by its own board tactic
 *    (0x4fb064), and when it is called or leaves the game's rules order every AI record of stage 3 to the boarding
 *    place (slot 194, 0x8fb04c, vehicle states 1 / 2 / 5 / 6: klescort.c section 1).
 *
 * KLHook.ini
 *   [CrewHop]
 *   Enable=0          1 = this file is on
 *   Dry=0             1 = everything is watched and logged, NOTHING is called (live check H0)
 *   Reorder=0         1 = 0.5 s after a hop the soldier gets the order it already has once more (0x760e50)
 *   OrderTo=1         1 = in the tick of the hop the soldier is ordered to its landing place (0x760e50): without it a bot whose
 *                     order lay behind it went straight back (live 2026-10-14, Retomoto lobby: three of four were back and falling)
 *   Log=1             2 = also, every 5 s, where every AI heister stands against every hop
 *   Recheck=2         (w_fedmove) 2 s after a hop a bot more than 1000 above / below its landing place by every reading of its place is
 *                     put on it again (and ordered there with OrderTo=1), at most this many times a hop; 0 = off. Live 2026-10-14
 *                     Retomoto: 4 of 26 lobby hops read 12,000 .. 16,000 above the landing 2 s later, two stood there 17 / 27 s
 * KLJoin.ini beside the level archive (written by tools\kl_fa_bots.py; up to 4 hops: [CrewHop], [CrewHop.2] ..)
 *   [CrewHop]
 *   From=-1729.3 220 -909.3   the gather place, x y z (y is up)
 *   Radius=240                in the plan            (default 300)
 *   Height=60                 above or below From    (default 150)
 *   Wait=6                    seconds at From        (default 3; 1 .. 600)
 *   Stage=2                   least heist stage      (default 2; 0 .. 3)
 *   Player=0                  1 = only after the human is beyond (nearer to To.1 than to From)
 *   Places=7                  To.1 .. To.8 = x y z, feet on the navigation mesh, 100 apart or more (a place nearer
 *   To.1=-1695.4 150 -283.6   to an earlier one, or inside From's own radius and height, is dropped)
 *   Lift=0                    added to the height of every landing place
 *   Again=0                   (w_fedmove) seconds after which a bot this hop carried may be carried by it once more (0 = once a
 *                             round; 1 .. 600). For a 'dead spot' hop whose From is a place no bot should ever stand at
 *   WalkTo=2560 19601 740     (v78, 2026-10-15) a WALK hop: the bot is not teleported from From but ORDERED to walk to this place
 *                             (the soldier's order routine 0x760e50, as OrderTo); an ordinary hop at that place (Retomoto: the
 *                             elevator floor, [CrewHop.2]) then carries it. The order is given again every 8 s while it is more than
 *                             3 m from WalkTo. Owner: 'the ai heisters all stop moving here ... where they should be pathing towards
 *                             to teleport down' (the floor1 atrium / lobby gates of the tower; the mesh joins both to the lift floor:
 *                             5,483 / 3,819 units by kl_fa_bots.Nav.path)
 *   GiveUp=40                 seconds after a walk order: a bot that is still not carried is teleported to To.n as an ordinary hop
 *
 * FAST LANDING WATCH (v78, 2026-10-15; owner's picture of a bot hanging in the air by the tower after a hop): for 3 s after a hop or
 * a put-back the bot's height is read every tick (0.1 s); when BOTH readings are more than 400 off the landing place's height it is put
 * back at once (Recheck counts these too; default now 5). Live 22:37:46: bot 6 read (4694, 2571, -5114) 0.1 s after its landing at
 * (5912, 570, -6545) and (-28, 15153, 433) 2 s later - drawn back towards the place it was taken from; the old 2 s look let it hang.
 *
 * LOG
 *   hop: on; Dry=0 Reorder=0 Log=1; ...
 *   hop: 1 hop(s) from <file> for level f03\f03_main
 *   hop: hop 1: From (-1729, 220, -909) radius 240 height 60, wait 6.0 s, stage 2, player 0; 7 landing places, To.1 (-1695, 150, -284)
 *   hop: bot 3 is at From of hop 1: node (-1731, 220, -921), +0x460 (-1731, 220, -921), heist stage 2; carried over in 6.0 s if it stays
 *   hop: bot 3 (actor ...) hop 1: at From for 6.1 s, node (...) -> To.2 (-1775, 150, -364): now node (...), +0x460 (...); its order (-1651, 150, -170)
 *   hop: bot 3 is at node (...) 2 s after hop 1, heist stage 3, vehicle state 1
 *   hop: bot 5 hop 1 NOT carried: <why>
 *   hop: bot 3 left From of hop 1 after 2.4 s by itself          (Log=2: the link, or its route, took it)
 */
#ifndef KLHOP_C
#define KLHOP_C

#define KLV_NHOP   6                          /* v78: 6 (was 4): [CrewHop] .. [CrewHop.6] */
#define KLV_NTO    8
#define KLV_APART  100.0f                     /* the game's own crew jump 0x8f4100 puts its members this far apart (float 0xb5c050) */
#define KLV_OFF    1000.0f                    /* Recheck: a bot this far above or below its landing place 2 s after the hop did not land (w_fedmove) */
#define KLV_FAST   400.0f                     /* v78: within the first 3 s after a hop: this far above / below the landing = not landed */
#define KLV_WATCH  3000                       /* v78: ms of the fast landing watch */

static struct { int on, dry, reorder, log, orderto, recheck, walkx; } klv;
struct klv_hop { int on, nto, stage, player, nohuman, walk; DWORD wait, again, giveup; float from[3], radius, height, to[KLV_NTO][3], walkto[3]; };
static struct { int n; char key[64], file[MAX_PATH]; FILETIME ft; struct klv_hop h[KLV_NHOP]; } klv_lv;
struct klv_after { int rec, hop, step, to, tries; DWORD actor, at, watch; };      /* watch = the fast landing watch runs until this tick (v78) */
struct klv_walk { int hop, orders; DWORD actor, at, order_at; };                   /* hop = 1 + the walk hop, 0 = none (v78) */            /* step: 1 = the re-order is due, 2 = the '2 s after' line, 0 = free; to = its landing place, tries = Recheck put-backs */
static struct {
    DWORD rules, state, last_hop, say_at; int stages, told_gate, told_thread, told_code, told_passed[KLV_NHOP], passed[KLV_NHOP], next[KLV_NHOP];
    DWORD since[KLV_NHOP][KLB_NREC], actor[KLV_NHOP][KLB_NREC], used[KLV_NHOP][KLV_NTO], doneat[KLV_NHOP][KLB_NREC];
    char done[KLV_NHOP][KLB_NREC], told[KLV_NHOP][KLB_NREC];
    struct klv_after after[KLB_NREC];
    struct klv_walk walking[KLB_NREC];
} klv_r;

static float klv_num(const char *sec, const char *key, const char *def, const char *file)
{
    char t[32];
    GetPrivateProfileStringA(sec, key, def, t, sizeof t, file);
    return (float)atof(t);
}

static int klv_at(const struct klv_hop *h, const float p[3])
{   /* within Radius in the plan and Height in height; a NaN is not there */
    float dx = p[0] - h->from[0], dz = p[2] - h->from[2];
    return dx * dx + dz * dz <= h->radius * h->radius && fabs(p[1] - h->from[1]) <= h->height;
}

/* the [CrewHop] sections of the KLJoin.ini kljoin.c has read for the running level (never a stock archive's) */
static void klv_source(void)
{
    char key[64], file[MAX_PATH], sec[16], t[32]; FILETIME ft; int i, k, j, n;
    EnterCriticalSection(&klj_cs);
    snprintf(key, sizeof key, "%s", klj_map_key); snprintf(file, sizeof file, "%s", klj_map_file); ft = klj_map_ft;
    LeaveCriticalSection(&klj_cs);
    if (!strcmp(key, klv_lv.key) && !_stricmp(file, klv_lv.file) && !CompareFileTime(&ft, &klv_lv.ft)) return;
    memset(&klv_lv, 0, sizeof klv_lv);
    strcpy(klv_lv.key, key); strcpy(klv_lv.file, file); klv_lv.ft = ft;
    if (!key[0] || !file[0]) return;
    for (i = 0; i < KLV_NHOP; i++) {
        struct klv_hop *h = &klv_lv.h[i]; float lift, v[3]; int st;
        if (i) snprintf(sec, sizeof sec, "CrewHop.%d", i + 1); else strcpy(sec, "CrewHop");
        if (!GetPrivateProfileStringA(sec, 0, "", t, sizeof t, file)) continue;                 /* no such section */
        if (!klj_vec(sec, "From", file, h->from)) { klog("hop: [%s] of %s refused: From= needs three numbers", sec, file); continue; }
        h->radius = klv_num(sec, "Radius", "300", file); h->height = klv_num(sec, "Height", "150", file);
        if (!klb_finite(h->radius) || h->radius < 50 || !klb_finite(h->height) || h->height < 10) { klog("hop: [%s] of %s refused: Radius (at least 50) / Height (at least 10)", sec, file); continue; }
        lift = klv_num(sec, "Wait", "3", file); if (!klb_finite(lift) || lift < 1) lift = 1; if (lift > 600) lift = 600;
        h->wait = (DWORD)(lift * 1000.0f);
        st = (int)GetPrivateProfileIntA(sec, "Stage", 2, file); h->stage = st < 0 ? 0 : st > 3 ? 3 : st;
        h->player = GetPrivateProfileIntA(sec, "Player", 0, file) != 0;
        h->nohuman = GetPrivateProfileIntA(sec, "NoHuman", 0, file) != 0;       /* 2026-10-19: 1 = idle (timers 0) while a LIVING human exists */
        lift = klv_num(sec, "Again", "0", file); if (!klb_finite(lift) || lift < 0) lift = 0; if (lift > 600) lift = 600;
        h->again = (DWORD)(lift * 1000.0f);                                 /* 0 = a bot is carried by this hop once a round (as before) */
        h->walk = klj_vec(sec, "WalkTo", file, h->walkto) && klb_finite(h->walkto[0]) && klb_finite(h->walkto[1]) && klb_finite(h->walkto[2]);
        lift = klv_num(sec, "GiveUp", "40", file); if (!klb_finite(lift) || lift < 5) lift = 5; if (lift > 600) lift = 600;
        h->giveup = (DWORD)(lift * 1000.0f);
        lift = klv_num(sec, "Lift", "0", file); if (!klb_finite(lift)) lift = 0;
        n = (int)GetPrivateProfileIntA(sec, "Places", 0, file);
        for (k = 0; k < n && k < KLV_NTO; k++) {
            snprintf(t, sizeof t, "To.%d", k + 1);
            if (!klj_vec(sec, t, file, v) || !klb_finite(v[0]) || !klb_finite(v[1]) || !klb_finite(v[2])) break;
            v[1] += lift;
            for (j = 0; j < h->nto && (v[0] - h->to[j][0]) * (v[0] - h->to[j][0]) + (v[1] - h->to[j][1]) * (v[1] - h->to[j][1]) + (v[2] - h->to[j][2]) * (v[2] - h->to[j][2]) >= KLV_APART * KLV_APART; j++) ;
            if (j < h->nto) { klog("hop: [%s] To.%d dropped: nearer than %.0f to an earlier landing place", sec, k + 1, KLV_APART); continue; }
            if (klv_at(h, v)) { klog("hop: [%s] To.%d dropped: it lies inside From's own radius and height", sec, k + 1); continue; }
            memcpy(h->to[h->nto++], v, sizeof v);
        }
        if (!h->nto) { klog("hop: [%s] of %s refused: no usable To.1", sec, file); continue; }
        h->on = 1; klv_lv.n++;
    }
    if (!klv_lv.n) return;
    klog("hop: %d hop(s) from %s for level %s", klv_lv.n, file, key);
    for (i = 0; i < KLV_NHOP; i++) if (klv_lv.h[i].on) {
        const struct klv_hop *h = &klv_lv.h[i];
        klog("hop: hop %d: From (%.0f, %.0f, %.0f) radius %.0f height %.0f, wait %.1f s, stage %d, player %d, again %.0f s (0 = once a round); %d landing places, To.1 (%.0f, %.0f, %.0f)",
             i + 1, h->from[0], h->from[1], h->from[2], h->radius, h->height, h->wait / 1000.0, h->stage, h->player, h->again / 1000.0, h->nto, h->to[0][0], h->to[0][1], h->to[0][2]);
        if (h->walk) klog("hop: hop %d is a WALK hop: a bot at From is ordered to walk to (%.0f, %.0f, %.0f) (again every 8 s while it is more than 3 m off); still not carried after %.0f s: teleported to To.n",
                          i + 1, h->walkto[0], h->walkto[1], h->walkto[2], h->giveup / 1000.0);
    }
}

/* Where an actor is, read two ways -> bit 0 = node[] holds the world place of its node, bit 1 = feet[] holds the
   three floats at +0x460. Neither is established as THE place of a ZFFActor (see the top): both are used. */
static int klv_place(DWORD actor, float node[3], float feet[3])
{
    DWORD nd; int got = 0;
    node[0] = node[1] = node[2] = feet[0] = feet[1] = feet[2] = 0;
    if ((nd = klh_rd32(actor + 4)) != 0 && kle_node(nd, node, 0)) got |= 1;
    if (klh_rd(actor + 0x460, feet, 12) && kle_ok3(feet) && (feet[0] || feet[1] || feet[2])) got |= 2;
    return got;
}

/* the soldier of an actor when the order routine may be called on it (klescort.c's tests), else 0 and why[100] */
static DWORD klv_soldier(DWORD actor, char why[100])
{
    DWORD soldier, blk, goal, held = 1, tmp; BYTE b576 = 0, raw[0x1c];
    if (!klh_rd(actor + 0x576, &b576, 1) || b576 != 1) { strcpy(why, "its actor takes no orders now ([actor+0x576] is not 1)"); return 0; }
    if (!klh_rd(actor + 0x770, &held, 4) || held) { strcpy(why, "somebody holds it as a human shield"); return 0; }
    if (!(soldier = klh_rd32(actor + 0x77c)) || klh_rd32(soldier) != KLE_SOLDIER_VT || klh_rd32(soldier + 0x40) != actor) { strcpy(why, "actor +0x77c is not its ZSoldier"); return 0; }
    if (!(blk = klh_rd32(soldier + 0x64c)) || !klh_rd(blk, raw, sizeof raw) || *(DWORD *)(raw + 0x14) != soldier) { strcpy(why, "its soldier has no defend block"); return 0; }
    if (!(goal = klh_rd32(soldier + 0x648)) || !klh_rd(goal + 8, &tmp, 4)) { strcpy(why, "its soldier has no defend goal"); return 0; }
    if (!kle_callable(why)) return 0;
    return soldier;
}

/* The next landing place of hop hi nobody was given in the last 2 s and nobody of the crew stands on -> index, -1 = none now */
static int klv_free(int hi, const struct klb_snap *s, DWORD now)
{
    const struct klv_hop *h = &klv_lv.h[hi]; float who[KLB_NREC * 2 + 2][3], hf[3], hn[3]; DWORD pl; int nw = 0, i, k, j;
    for (i = 0; i < s->n; i++) {
        float nd[3], ft[3]; int got;
        if (!s->r[i].used || !s->r[i].actor || s->r[i].status || !(s->r[i].flags & 1)) continue;
        got = klv_place(s->r[i].actor, nd, ft);
        if (got & 1) memcpy(who[nw++], nd, 12);
        if (got & 2) memcpy(who[nw++], ft, 12);
    }
    if (kle_human(&pl, hf, hn)) { memcpy(who[nw++], hf, 12); memcpy(who[nw++], hn, 12); }
    for (k = 0; k < h->nto; k++) {
        int p = (klv_r.next[hi] + k) % h->nto;
        if (klv_r.used[hi][p] && now - klv_r.used[hi][p] < 2000) continue;
        for (j = 0; j < nw; j++) {
            float dx = who[j][0] - h->to[p][0], dz = who[j][2] - h->to[p][2];
            if (dx * dx + dz * dz < KLV_APART * KLV_APART && fabs(who[j][1] - h->to[p][1]) < 200) break;
        }
        if (j == nw) return p;
    }
    return -1;
}

/* v82i: 1 = klhop.c walks this record now and [Bots] WalkExclusive=1 asks the other order givers (klfedkit Hunted, klmove Restless) to leave it alone */
static int klv_owned(int rec) { return klv.on && klv.walkx && rec >= 0 && rec < KLB_NREC && klv_r.walking[rec].hop; }

/* v78: the soldier of an actor ordered to place p (0x760e50, the call OrderTo makes) -> 2 = ordered and set[] read, 1 = ordered, 0 = not (why) */
static int klv_order(DWORD actor, const float p[3], float set[3], char why[100])
{
    DWORD soldier = klh_rd32(actor + 0x77c); float q[4];
    set[0] = set[1] = set[2] = 0;
    if (!soldier || klh_rd32(soldier) != KLE_SOLDIER_VT) { strcpy(why, "actor +0x77c is not its ZSoldier"); return 0; }
    if (!kle_callable(why)) return 0;
    q[0] = p[0]; q[1] = p[1]; q[2] = p[2]; q[3] = 0;
    ((void (__fastcall *)(void *, void *, const float *, int, int, int))(DWORD_PTR)KLH_VA(KLE_ORDER))((void *)(DWORD_PTR)soldier, 0, q, 0, 1, 0);
    if (kltr.on) { float g2[3]; if (!kle_block(soldier, g2)) memcpy(g2, p, 12); kltr_order(-1, p, g2, 1); }
    return kle_block(soldier, set) ? 2 : 1;
}

/* the put-back of a bot that did not land (Recheck; the fast watch and the 2 s look alike). nd / ft / got = where it is read now */
static void klv_putback(struct klv_after *a, const float nd[3], const float ft[3], int got, DWORD now, const char *when)
{
    const float *to = klv_lv.h[a->hop].to[a->to]; const char *no; DWORD held = 1; float off = (got & 1 ? nd[1] : ft[1]) - to[1];
    no = klt_refuse(a->actor);
    if (!no && (!klh_rd(a->actor + 0x770, &held, 4) || held)) no = "somebody holds it as a human shield";
    if (a->tries >= klv.recheck) {
        if (a->tries++ == klv.recheck) klog("hop: bot %d is still %.0f off the height of its landing place To.%d of hop %d (%s): NOT put back again (Recheck=%d done)", a->rec, off, a->to + 1, a->hop + 1, when, klv.recheck);
        return;
    }
    if (no) { klog("hop: bot %d is %.0f off the height of its landing place To.%d of hop %d (%s): NOT put back: %s", a->rec, off, a->to + 1, a->hop + 1, when, no); a->tries++; return; }
    if (klv.dry) { klog("hop: bot %d is %.0f off the height of its landing place To.%d of hop %d (%s): WOULD be put back - DRY RUN", a->rec, off, a->to + 1, a->hop + 1, when); a->tries++; return; }
    {
        float is_n[3], is_f[3], set[3] = { 0, 0, 0 }; char why2[100]; int ord = 0;
        klt_teleport(a->actor, to);
        kltr_tp(a->rec, "hop-putback", to, when);
        kltr_set("hop-putback", "the bot did not land: ordered to the landing place again", a->rec);
        if (klv.orderto) ord = klv_order(a->actor, to, set, why2);
        kltr_set(0, 0, -1);
        klv_place(a->actor, is_n, is_f);
        a->tries++; a->step = 2; a->at = KLB_T(now); a->watch = KLB_T(now + KLV_WATCH);       /* looked at again: every tick for 3 s, and 2 s from now */
        klog("hop: bot %d did NOT land: %.0f off the height of To.%d of hop %d (%s): put back on (%.0f, %.0f, %.0f) (time %d of %d): now node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f)%s (%.0f, %.0f, %.0f)",
             a->rec, off, a->to + 1, a->hop + 1, when, to[0], to[1], to[2], a->tries, klv.recheck, is_n[0], is_n[1], is_n[2], is_f[0], is_f[1], is_f[2],
             ord == 2 ? "; ordered there, the game set" : ord ? "; ordered there" : "; NOT ordered there", set[0], set[1], set[2]);
    }
}

/* v78: the walking bots of walk hops: the order again, the hand-over (another hop or the crew join took it), the give-up teleport */
static void klv_walks(const struct klb_snap *s, DWORD now)
{
    int i;
    for (i = 0; i < KLB_NREC; i++) {
        struct klv_walk *w = &klv_r.walking[i]; const struct klv_hop *h; const struct klb_rec *r; float nd[3], ft[3], set[3]; const float *q; char why[100]; int got, p, k;
        if (!w->hop) continue;
        h = &klv_lv.h[w->hop - 1]; r = &s->r[i];
        if (i >= s->n || !r->used || r->actor != w->actor || r->status || (r->flags & 2) || !h->on || !h->walk) { w->hop = 0; continue; }     /* gone, dead, aboard, turned */
        if (!(got = klv_place(r->actor, nd, ft))) continue;
        q = got & 1 ? nd : ft;
        if (fabs(q[1] - h->walkto[1]) > 1000.0f) { if (klv.log) klog("hop: bot %d (walk of hop %d) is off the walk's floor now at (%.0f, %.0f, %.0f) after %.1f s: carried by another hop or the crew join", i, w->hop, q[0], q[1], q[2], (now - w->at) / 1000.0); w->hop = 0; continue; }
        if (now - w->at >= h->giveup) {
            const char *no = klt_refuse(r->actor); DWORD held = 1;
            if (!no && (!klh_rd(r->actor + 0x770, &held, 4) || held)) no = "somebody holds it as a human shield";
            if (no || (p = klv_free(w->hop - 1, s, now)) < 0) {   /* v82c: said once per 10 s (it used to be silent: a bot could walk for ever with no line) */
                static DWORD said[KLB_NREC];
                if (now - said[i] >= 10000) { said[i] = now; klog("hop: bot %d (walk of hop %d) is past its %.0f s but is NOT given up: %s", i, w->hop, h->giveup / 1000.0, no ? no : "no free To place"); }
                continue;
            }
            w->hop = 0;
            klv_r.used[h - klv_lv.h][p] = KLB_T(now);
            klt_teleport(r->actor, h->to[p]);
            kltr_tp(i, "hop-walk-giveup", h->to[p], "walk not carried in time");
            kltr_set("hop-walk-giveup", "walk gave up: ordered to the landing place", i);
            k = klv.orderto ? klv_order(r->actor, h->to[p], set, why) : 0;
            kltr_set(0, 0, -1);
            klog("hop: bot %d walked %.1f s towards (%.0f, %.0f, %.0f) and was not carried: GIVE UP - teleported from (%.0f, %.0f, %.0f) to To.%d (%.0f, %.0f, %.0f)%s",
                 i, (now - w->at) / 1000.0, h->walkto[0], h->walkto[1], h->walkto[2], q[0], q[1], q[2], p + 1, h->to[p][0], h->to[p][1], h->to[p][2], k ? "; ordered there" : "");
            klv_r.after[i].rec = i; klv_r.after[i].hop = (int)(h - klv_lv.h); klv_r.after[i].actor = r->actor; klv_r.after[i].at = KLB_T(now); klv_r.after[i].step = 1;
            klv_r.after[i].to = p; klv_r.after[i].tries = 0; klv_r.after[i].watch = KLB_T(now + KLV_WATCH);
            return;                                                           /* one call a tick */
        }
        if (now - w->order_at >= 8000 && (q[0] - h->walkto[0]) * (q[0] - h->walkto[0]) + (q[2] - h->walkto[2]) * (q[2] - h->walkto[2]) > 300.0f * 300.0f) {
            w->order_at = KLB_T(now);
            kltr_set("hop-walk", "walk: ordered to the walk's end again (every 8 s while 3 m+ from it)", i);
            k = klv_order(r->actor, h->walkto, set, why);
            kltr_set(0, 0, -1);
            if (k) w->orders++;
            if (klv.log >= 2 || w->orders <= 2 || !k)
                klog("hop: bot %d (walk of hop %d) at (%.0f, %.0f, %.0f), %.1f m from the walk's end after %.1f s: %s", i, w->hop, q[0], q[1], q[2],
                     sqrt((q[0] - h->walkto[0]) * (q[0] - h->walkto[0]) + (q[2] - h->walkto[2]) * (q[2] - h->walkto[2])) / 100.0, (now - w->at) / 1000.0, k ? "ordered there again" : why);
            return;
        }
    }
}

/* what is due after a hop: the re-order (Reorder=1) at +0.5 s, the 'where is it now' line at +2 s */
static void klv_follow(const struct klb_snap *s, DWORD now)
{
    int i;
    for (i = 0; i < KLB_NREC; i++) {
        struct klv_after *a = &klv_r.after[i]; const struct klb_rec *r; float nd[3], ft[3], blk[3]; char why[100]; DWORD soldier; int got;
        if (!a->step) continue;
        r = &s->r[a->rec];
        if (a->rec >= s->n || !r->used || r->actor != a->actor || r->status) { a->step = 0; continue; }        /* gone, dead or aboard: nothing to say */
        if (klv.recheck && a->watch && (LONG)(a->watch - now) > 0 && a->hop >= 0 && a->hop < KLV_NHOP && a->to >= 0 && a->to < klv_lv.h[a->hop].nto) {      /* v78: the fast landing watch */
            const float *to = klv_lv.h[a->hop].to[a->to];
            got = klv_place(a->actor, nd, ft);
            if (got && (!(got & 1) || fabs(nd[1] - to[1]) > KLV_FAST) && (!(got & 2) || fabs(ft[1] - to[1]) > KLV_FAST)) {
                char when[48]; snprintf(when, sizeof when, "%.1f s after", (now - (a->watch - KLV_WATCH)) / 1000.0);
                klv_putback(a, nd, ft, got, now, when);
                continue;
            }
        }
        if (a->step == 1) {
            if (now - a->at < 500) continue;
            a->step = 2;
            if (!klv.reorder) continue;
            if (!(soldier = klv_soldier(a->actor, why))) { klog("hop: bot %d hop %d: its order is NOT given again: %s", a->rec, a->hop + 1, why); continue; }
            if (!kle_block(soldier, blk) || !(blk[0] || blk[1] || blk[2])) { klog("hop: bot %d hop %d: its soldier holds no order to give again", a->rec, a->hop + 1); continue; }
            if (klv_at(&klv_lv.h[a->hop], blk)) { klog("hop: bot %d hop %d: its order (%.0f, %.0f, %.0f) is the gather place itself: NOT given again (it would walk back)", a->rec, a->hop + 1, blk[0], blk[1], blk[2]); continue; }
            {
                float p[4], set[3];
                p[0] = blk[0]; p[1] = blk[1]; p[2] = blk[2]; p[3] = 0;
                ((void (__fastcall *)(void *, void *, const float *, int, int, int))(DWORD_PTR)KLH_VA(KLE_ORDER))((void *)(DWORD_PTR)soldier, 0, p, 0, 1, 0);
                if (!kle_block(soldier, set)) memcpy(set, blk, 12);
                kltr_set("hop-reorder", "Reorder: its own order 0.5 s after the hop", a->rec); kltr_order(-1, blk, set, 1);
                klog("hop: bot %d hop %d: its own order (%.0f, %.0f, %.0f) given again by the soldier's order routine; the game set (%.0f, %.0f, %.0f)", a->rec, a->hop + 1, blk[0], blk[1], blk[2], set[0], set[1], set[2]);
            }
        } else if (now - a->at >= 2000) {
            a->step = 0;
            got = klv_place(a->actor, nd, ft);
            klog("hop: bot %d is at node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f)%s 2 s after hop %d, heist stage %u, vehicle state %u", a->rec, nd[0], nd[1], nd[2], ft[0], ft[1], ft[2],
                 got == 3 ? "" : got ? " (one of the two could not be read)" : " (neither could be read)", a->hop + 1, r->stage, s->veh);
            /* Recheck (w_fedmove, 2026-10-14): on Retomoto four of 26 hops to the lobby left the bot, 2 s later, 12,000 .. 16,000 ABOVE its
               landing place - (99, 14941, 846), (5765, 15473, -5795), (388, 16521, -95), (5765, 12722, -5795) - and two of them stood there
               until the human's jump moved them (19:26:54 .. 19:27:11, 21:01:34 .. 21:02:00: 'stood 5.0 s at (5760, 12722, -5794)' x 5).
               Why is NOT known. A bot that is more than KLV_OFF off its landing place's height, by every reading, is put on it again. */
            if (klv.recheck && got && a->hop >= 0 && a->hop < KLV_NHOP && a->to >= 0 && a->to < klv_lv.h[a->hop].nto) {
                const float *to = klv_lv.h[a->hop].to[a->to];
                if ((!(got & 1) || fabs(nd[1] - to[1]) > KLV_OFF) && (!(got & 2) || fabs(ft[1] - to[1]) > KLV_OFF)) klv_putback(a, nd, ft, got, now, "2 s after");
            }
        }
    }
}

static void klv_tick(int game_thread)
{
    static DWORD last; struct klb_snap s; DWORD now = GetTickCount(), pl; char scene[160], key[64], why[200]; float hf[3], hn[3]; int i, hi, stages = 0, human, say;
    if (!klv.on || !klh_exe_ok || now - last < 100) return;
    last = now;
    if (!klb_read(&s)) { klv_r.rules = 0; return; }                          /* Arcade with a ZGameRulesHeist object, or nothing */
    for (i = 0; i < s.n; i++) if (s.r[i].used) stages += s.r[i].stage;
    if (s.rules != klv_r.rules || (s.state == KLB_ROUND && klv_r.state != KLB_ROUND) || stages < klv_r.stages) {      /* a new round: as klbot.c's klb_act */
        memset(&klv_r, 0, sizeof klv_r); klv_r.rules = s.rules;
    }
    klv_r.state = s.state; klv_r.stages = stages;
    if (s.state != KLB_ROUND) return;
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return;
    klv_source();
    if (!klv_lv.n || strcmp(key, klv_lv.key)) return;                        /* no hop, or not the level the file belongs to */
    if (!klb_level(why)) {                                                   /* klbot.c section 0: not on a stock level, an unknown one, or without the Steam guard */
        if (!klv_r.told_gate++) klog("hop: %s: nobody is carried here (it acts only on a level that is not stock)", why);
        return;
    }
    if (!game_thread) { if (!klv_r.told_thread++) klog("hop: the tick is not on the game's thread ([KLHook] Tick=0?): nobody is carried"); return; }
    if (!klt_tele_known()) { if (!klv_r.told_code++) klog("hop: the game's teleport routine is not the one this build knows: nobody is carried"); return; }
    klv_follow(&s, now);
    klv_walks(&s, now);
    human = kle_human(&pl, hf, hn);
    say = klv.log >= 2 && now - klv_r.say_at >= 5000;
    if (say) klv_r.say_at = KLB_T(now);
    for (hi = 0; hi < KLV_NHOP; hi++) {
        const struct klv_hop *h = &klv_lv.h[hi];
        if (!h->on) continue;
        if (h->nohuman && human) {
            static DWORD held_at; memset(klv_r.since[hi], 0, sizeof klv_r.since[hi]);
            if (klv.log && now - held_at >= 30000) { held_at = now; klog("hop: hop %d held (NoHuman=1): a living human is in play", hi + 1); }
            continue;
        }
        if (h->player && !klv_r.passed[hi] && human) {
            float a = (hf[0] - h->to[0][0]) * (hf[0] - h->to[0][0]) + (hf[1] - h->to[0][1]) * (hf[1] - h->to[0][1]) + (hf[2] - h->to[0][2]) * (hf[2] - h->to[0][2]);
            float b = (hf[0] - h->from[0]) * (hf[0] - h->from[0]) + (hf[1] - h->from[1]) * (hf[1] - h->from[1]) + (hf[2] - h->from[2]) * (hf[2] - h->from[2]);
            if (a < b) { klv_r.passed[hi] = 1; klog("hop: hop %d: you are beyond it at (%.0f, %.0f, %.0f): the AI heisters may follow", hi + 1, hf[0], hf[1], hf[2]); }
        }
        for (i = 0; i < s.n; i++) {
            const struct klb_rec *r = &s.r[i]; float nd[3], ft[3], is_n[3], is_f[3], blk[3] = { 0, 0, 0 }; const char *no; DWORD held = 1, soldier; int got, in, p, have_blk = 0;
            if (klv_r.done[hi][i] && h->again && klv_r.doneat[hi][i] && now - klv_r.doneat[hi][i] >= h->again) { klv_r.done[hi][i] = 0; klv_r.told[hi][i] = 0; }   /* Again=: it may be carried once more */
            if (!r->used || !(r->flags & 1) || !r->actor || r->status || klv_r.done[hi][i]) { klv_r.since[hi][i] = 0; continue; }
            if (h->walk && ((r->flags & 2) || (klv_r.walking[i].hop && klv_r.walking[i].actor == r->actor))) { klv_r.since[hi][i] = 0; continue; }      /* v78: walking already; a traitor is not walked */
            if (klv_r.actor[hi][i] != r->actor) { klv_r.actor[hi][i] = r->actor; klv_r.since[hi][i] = 0; klv_r.told[hi][i] = 0; }
            got = klv_place(r->actor, nd, ft);
            in = ((got & 1) && klv_at(h, nd)) || ((got & 2) && klv_at(h, ft));
            if (say && r->stage >= h->stage) {
                const float *q = got & 1 ? nd : ft;
                klog("hop: bot %d stage %u: node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f): %.0f from From of hop %d in the plan, %+.0f in height%s", i, r->stage, nd[0], nd[1], nd[2], ft[0], ft[1], ft[2],
                     sqrt((q[0] - h->from[0]) * (q[0] - h->from[0]) + (q[2] - h->from[2]) * (q[2] - h->from[2])), hi + 1, q[1] - h->from[1], in ? " = AT From" : "");
            }
            if (!in) {
                if (klv_r.since[hi][i] && klv.log >= 2) klog("hop: bot %d left From of hop %d after %.1f s by itself", i, hi + 1, (now - klv_r.since[hi][i]) / 1000.0);
                klv_r.since[hi][i] = 0;
                continue;
            }
            if (!klv_r.since[hi][i]) {
                klv_r.since[hi][i] = KLB_T(now);
                if (klv.log) klog("hop: bot %d is at From of hop %d: node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f), heist stage %u; carried over in %.1f s if it stays%s%s", i, hi + 1, nd[0], nd[1], nd[2], ft[0], ft[1], ft[2],
                                  r->stage, h->wait / 1000.0, r->stage < h->stage ? " and reaches the hop's stage" : "", got == 3 && klv_at(h, nd) != klv_at(h, ft) ? " (ONLY ONE of the two places is at From: they disagree)" : "");
            }
            if (r->stage < h->stage || (h->player && !klv_r.passed[hi]) || now - klv_r.since[hi][i] < h->wait) continue;
            if (klv_r.last_hop && now - klv_r.last_hop < 500) continue;       /* one bot per half second */
            no = klt_refuse(r->actor);
            if (!no && (!klh_rd(r->actor + 0x770, &held, 4) || held)) no = "somebody holds it as a human shield";
            if (no) {
                if (!klv_r.told[hi][i]++) klog("hop: bot %d hop %d NOT carried: %s (tried again while it stands there)", i, hi + 1, no);
                continue;
            }
            if (h->walk) {                                                    /* v78: a WALK hop orders, it does not carry */
                float set[3]; char why2[100]; int k; kltr_set("hop-walk", "walk hop: at From long enough, first order to the walk's end", i); k = klv.dry ? 0 : klv_order(r->actor, h->walkto, set, why2); kltr_set(0, 0, -1);
                klv_r.done[hi][i] = 1; klv_r.doneat[hi][i] = KLB_T(now); klv_r.last_hop = KLB_T(now);
                if (klv.dry) { klog("hop: bot %d hop %d: at From for %.1f s: WOULD be ordered to walk to (%.0f, %.0f, %.0f) - DRY RUN", i, hi + 1, (now - klv_r.since[hi][i]) / 1000.0, h->walkto[0], h->walkto[1], h->walkto[2]); return; }
                if (!k) { klog("hop: bot %d hop %d: at From for %.1f s but NOT ordered to walk: %s", i, hi + 1, (now - klv_r.since[hi][i]) / 1000.0, why2); return; }
                klv_r.walking[i].hop = hi + 1; klv_r.walking[i].actor = r->actor; klv_r.walking[i].at = KLB_T(now); klv_r.walking[i].order_at = KLB_T(now); klv_r.walking[i].orders = 1;
                klog("hop: bot %d (actor %08lx) hop %d: at From for %.1f s, node (%.0f, %.0f, %.0f): ordered to WALK to (%.0f, %.0f, %.0f), the game set (%.0f, %.0f, %.0f); heist stage %u; teleported to To.n if not carried in %.0f s",
                     i, r->actor, hi + 1, (now - klv_r.since[hi][i]) / 1000.0, nd[0], nd[1], nd[2], h->walkto[0], h->walkto[1], h->walkto[2], set[0], set[1], set[2], r->stage, h->giveup / 1000.0);
                return;
            }
            if ((p = klv_free(hi, &s, now)) < 0) continue;                    /* every landing place is taken just now */
            if ((soldier = klh_rd32(r->actor + 0x77c)) != 0 && klh_rd32(soldier) == KLE_SOLDIER_VT) have_blk = kle_block(soldier, blk);
            klv_r.done[hi][i] = 1; klv_r.doneat[hi][i] = KLB_T(now); klv_r.used[hi][p] = KLB_T(now); klv_r.next[hi] = (p + 1) % h->nto; klv_r.last_hop = KLB_T(now);
            if (klv.dry) {
                klog("hop: bot %d (actor %08lx) hop %d: at From for %.1f s, node (%.0f, %.0f, %.0f): WOULD be put on To.%d (%.0f, %.0f, %.0f) - DRY RUN, nothing is called; its order (%.0f, %.0f, %.0f)%s",
                     i, r->actor, hi + 1, (now - klv_r.since[hi][i]) / 1000.0, nd[0], nd[1], nd[2], p + 1, h->to[p][0], h->to[p][1], h->to[p][2], blk[0], blk[1], blk[2], have_blk ? "" : " = none read");
                return;
            }
            klt_teleport(r->actor, h->to[p]);
            kltr_tp(i, "hop", h->to[p], "carried hop: From to landing place To.n");
            if (klv.orderto && soldier && klh_rd32(soldier) == KLE_SOLDIER_VT) {
                /* OrderTo (2026-10-14, live on Retomoto: bots 4 / 5 / 7 were back at the lobby 2 s after the hop, falling - the soldier still
                   walked to its old place, which no path reaches from the landing): in the same tick its order becomes the landing place */
                char why2[100]; float q[4], set[3];
                if (kle_callable(why2)) {
                    q[0] = h->to[p][0]; q[1] = h->to[p][1]; q[2] = h->to[p][2]; q[3] = 0;
                    ((void (__fastcall *)(void *, void *, const float *, int, int, int))(DWORD_PTR)KLH_VA(KLE_ORDER))((void *)(DWORD_PTR)soldier, 0, q, 0, 1, 0);
                    if (kle_block(soldier, set)) { blk[0] = set[0]; blk[1] = set[1]; blk[2] = set[2]; have_blk = 1; }
                    if (kltr.on) { float g3[3]; kltr_set("hop", "OrderTo: its order becomes the landing place", i); kltr_order(-1, q, kle_block(soldier, g3) ? g3 : q, 1); }
                } else klog("hop: bot %d: its order is NOT moved to the landing place: %s", i, why2);
            }
            klv_place(r->actor, is_n, is_f);
            klog("hop: bot %d (actor %08lx) hop %d: at From for %.1f s, node (%.0f, %.0f, %.0f) -> To.%d (%.0f, %.0f, %.0f): now node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f); heist stage %u, vehicle state %u; its order (%.0f, %.0f, %.0f)%s",
                 i, r->actor, hi + 1, (now - klv_r.since[hi][i]) / 1000.0, nd[0], nd[1], nd[2], p + 1, h->to[p][0], h->to[p][1], h->to[p][2], is_n[0], is_n[1], is_n[2], is_f[0], is_f[1], is_f[2],
                 r->stage, s.veh, blk[0], blk[1], blk[2], have_blk ? "" : " = none read");
            klv_r.after[i].rec = i; klv_r.after[i].hop = hi; klv_r.after[i].actor = r->actor; klv_r.after[i].at = KLB_T(now); klv_r.after[i].step = 1;
            klv_r.after[i].to = p; klv_r.after[i].tries = 0; klv_r.after[i].watch = KLB_T(now + KLV_WATCH);
            if (klv_r.walking[i].hop) { if (klv.log) klog("hop: bot %d: its walk of hop %d ends here (%.1f s)", i, klv_r.walking[i].hop, (now - klv_r.walking[i].at) / 1000.0); klv_r.walking[i].hop = 0; }
            return;                                                           /* one call a tick */
        }
    }
}

static void klv_init(void)
{
    memset(&klv, 0, sizeof klv); memset(&klv_lv, 0, sizeof klv_lv); memset(&klv_r, 0, sizeof klv_r);
    klv.on = GetPrivateProfileIntA("CrewHop", "Enable", 0, klh_ini) != 0;
    if (!klv.on) return;
    klv.dry = GetPrivateProfileIntA("CrewHop", "Dry", 0, klh_ini) != 0;
    klv.reorder = GetPrivateProfileIntA("CrewHop", "Reorder", 0, klh_ini) != 0;
    klv.orderto = GetPrivateProfileIntA("CrewHop", "OrderTo", 1, klh_ini) != 0;       /* 1 = at the hop the soldier's order becomes the landing place */
    klv.log = (int)GetPrivateProfileIntA("CrewHop", "Log", 1, klh_ini);
    klv.walkx = GetPrivateProfileIntA("Bots", "WalkExclusive", 0, klh_ini) != 0;      /* v82i GUESS fix, default 0: while klhop.c walks a bot, klfedkit Hunted and klmove Restless give it no order */
    klv.recheck = (int)GetPrivateProfileIntA("CrewHop", "Recheck", 5, klh_ini);         /* v78: default 5 (the fast watch counts too) */       /* put-backs of a bot that did not land (0 = off) */
    if (klv.recheck < 0) klv.recheck = 0;
    if (klv.recheck > 5) klv.recheck = 5;
    klog("hop: on; Dry=%d Reorder=%d Log=%d Recheck=%d; an AI heister that stands at a [CrewHop] place of the level's KLJoin.ini is put beyond it by the game's own actor teleport (%08x)%s; Arcade only, on a level that is not the stock one of its slot",
         klv.dry, klv.reorder, klv.log, klv.recheck, KLT_TELEPORT, klv.dry ? " - DRY RUN: nothing is called" : "");
}

#endif /* KLHOP_C */
