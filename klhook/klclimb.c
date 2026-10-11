/*
 * klclimb.c - THE WALL CLIMB DEAD MEN HAD AND DOG DAYS DROPPED, for the local player: at a marked edge of the level he
 * is carried up by Dead Men's own climb clip (or, as a fall-back, by Dog Days' own vault action).
 * NOT WIRED: klhook.c does not include this file (WIRING, at the end of this comment). NOTHING HERE HAS RUN IN THE
 * GAME and no hook was built with it; it passed a syntax check behind klhook.c (cl /Zs /W4: no warning of its own).
 * Written 2026-10-11 from static reading of kl2.exe build 0490 and kaneandlynch.exe; the account, every address and
 * the live checks K0 .. K8 are in re\climb.md.
 * Off unless KLHook.ini has [Climb] Enable=1. Arcade only (ZGameRulesHeist), never on a stock level, the game's own
 * thread only. NO data write of the hook's own and no code byte: calls of game routines, and what those routines
 * take for granted of the player is tested before each call.
 *
 * 1. WHAT THE GAMES DO (re\climb.md A, B, C)
 *    Dead Men: ZFFPlayerMovementClimb (kaneandlynch.exe vtable 0x966c44) asks for NO level data. Its test 0x605b50
 *    finds an edge with rays (four probes straight down 25 / 40 / 55 / 70 in front, a clear way 15 over the top, 180
 *    headroom, a face 1 under the edge), 25 < h <= 220 over the feet; table 0x603340: Low h <= 120 clip slot
 *    '/Movement/Climb/Up/Low' stand-off 81, Medium <= 170 '/Movement/Climb/Up/Medium' 47, High <= 220
 *    '/Movement/Climb/Up/High' 47. Enter 0x602f30 plays the clip and aligns it twice (0x526620): the feet at the foot
 *    of the face, stand-off back from it, at clip event 5; the same place at top level at event 6; after that the
 *    clip's own root motion goes on (High: 91 forward and 24.5 up, so he ends ON the obstacle, 44 past its face).
 *    Dog Days: no such movement class. What it has, all read:
 *      0x5ea340  ZFFPlayer::StartMiniAnim(u16 slot, x, alignObject, char endWithClip), ret 0x10: stops the current
 *                action, makes ZFFActionMiniAnim (kind 0x23, vtable 0xbb4f0c, 0x28 bytes: +8 player, +0x18 slot,
 *                +0x1c alignObject, +0x20 the playing channel, +0x25 endWithClip) and starts it. Start 0x76d1d0: no
 *                clip for the slot -> [player+0x2758] = 1 and the action is over at once (no fault); else
 *                Play(clip, 1) (vtable +0x204) with its own guard against the 'channel replaced' reports of that
 *                Play. The game calls it in ordinary play (0x5022c0 from 0x60b5c2: a full-body clip on a player who
 *                stands or walks with no action running) - which is what the vault's own start is NOT known to
 *                survive (re\climb.md C.6). It hands a null action to the start when the action pool 0x15151c0 is
 *                empty (0x5ea3bc): the game's own flaw, not tested here.
 *      0x80fdc0  ZLNKOBJ slot 130 (ZFFPlayer vtable +0x208) AlignTo(rot[9], pos[3], float frames) -> al: the running
 *                full-body channel whose clip has record flag 0x40 (found by 0x760120) is corrected so that its ROOT
 *                is at pos / rot when `frames` more frames have played; from then on the correction stays whole
 *                (0x50b0f6 .. 0x50b131) and the clip's own root motion goes on. A channel is {+0 clip, +4 the frame
 *                it is at, +8 from, +0xc to, +0x14 flags}. rot = a node's world axes as 0x857110 gives them: row 0 =
 *                the image of local z = where the BACK points (a clip's root runs along -z), row 1 = up, row 2 = the
 *                image of local x. 0x55f8f0 (ecx = out[9], edx = in[3]) makes such a matrix from the vector that is
 *                to be row 0 - what the vault 0x619790 calls with the cover's normal.
 *                This is the routine Dog Days' own NPC link mover 0x4a5160 calls for these very clips (kind-1
 *                navigation links: Dead Men's NPC climb, still in kl2.exe, used by no stock level).
 *      0x5d6200 / 0x686600  ZFFPlayer vtable +0x560 / +0x564: character collision off / on. 0x8c5270 / 0x8b41c0:
 *                ++[player+0x7b4], [player+0x7a5] = 0 / the count back and [player+0x7a5] = 1 at zero; the body's
 *                Havok layer 5 <-> 0xc through 0x40ed30. What every action that carries the player through things
 *                brackets itself with (the vault 0x6a27e0 / 0x82f780, the mini cutscene act 0x8e8d00 / 0x447bd0).
 *      0x619790  ZFFPlayer::StartVaultOver(cover *, char left, float pos[3], float rot[9], char given, char
 *                writeBack), ret 0x18: makes ZFFActionVaultOver (kind 0x2b, vtable 0xbb5188) and starts it; with
 *                given = 1 the end place and rotation are the caller's (the network receiver 0x60c610 does that).
 *                It tests nothing; of the cover record it reads +0x0c (3 floats), +0x2c (3 floats), +0x54 (float)
 *                and keeps the pointer at action +0x7c, which nothing reads. The action switches the collision off
 *                and on ITSELF. Its clip is one of '/Cover/Vaulting/Cover_Vault_{Left|Right}_{1M|2M}' (2M when the
 *                way is over 175): a hop made for a 1 m obstacle, whatever it is carried over.
 *
 * 2. WHAT THIS FILE DOES
 *    The edges come from the level's KLJoin.ini (the file kljoin.c reads beside the archive; tools\kl_fa_climb.py
 *    writes the [Climb] sections and has checked every one against the build's collision with Dead Men's rule - the
 *    hook casts no ray). In an Arcade round that runs (session state 0x19) on a level that is not the stock one of
 *    its slot, on the game's thread, twenty times a second, for the local human (a heister, alive, not attached to a
 *    vehicle):
 *      he is AT THE FOOT of an edge when his node's place is 15 .. 75 from the face on the side Normal= points to,
 *      between A and B, and his height (the node's, else the floats at +0x460: whichever is within 40 of Floor=) fits.
 *      If he stays there for Dwell ms, slower than Speed, looking at the face within Angle degrees (and with Key
 *      down, if a key is set), has no action running, stands or walks (movement kind 2 / 3) and nobody has his
 *      collision off:
 *      Mode=climb   the class is taken from top - Floor by Dead Men's table; its slot name is looked up in the
 *                   level's slot table (read, as the game's own search 0x68a730 reads it); StartMiniAnim(slot, 0, 0,
 *                   1); if the game kept the action (its vtable, this player, this slot, a channel), the collision is
 *                   switched off and the clip is aligned as Dead Men aligns it: Align=2 - the foot place P1 (the
 *                   point of the face nearest to him, stand-off back along the normal, at his own height) at the
 *                   frame of event 5, then, when that frame has come, P2 = P1 raised by (top - his feet) at the frame
 *                   of event 6; Align=1 - one alignment at the last frame, to the place Dead Men's would end at but
 *                   exactly at top height (no settle of 24.5 at the end; the grab comes a little late).
 *                   If the game finds no channel to align, the action is stopped at once and the collision switched
 *                   on: a clip that plays where he stands would end inside the obstacle.
 *                   Every frame after that the action is watched: when it is no longer the current one (the clip
 *                   ended, he died, the round ended), the collision is switched on again - once, and only for an
 *                   object that is still one of the game's players. A climb that outlives its clip by 1.5 s is
 *                   stopped (vtable +0x374) and the collision switched on.
 *      Mode=vault   (or Fallback=1 when the body's set has no climb clip) one call: 0x619790 with a cover record of
 *                   this file's own and given = 1, end place = the middle of the obstacle's top. Tested before: both
 *                   vault slots have a clip for this body (0x59d550: a null clip is a null read at 0x6a2a65). After:
 *                   the current action must be the vault's - if it is not, the action ended inside its own start
 *                   (the case that is not established) and the line says so.
 *    WHAT THE PLAYER SEES (expected, not seen): at the bank's yard wall (top 203.5 over the yard = High) he pulls
 *    himself up in 2.08 s and stands on the wall, 5 short of its far edge; a step on and he drops to the street (253
 *    down) or onto a dumpster lid (122 down) by the game's own fall. From the street the wall is 253 high: no climb,
 *    as in Dead Men. The AI heisters get nothing from this file: they keep their drop link through the sunk piece.
 *    NOT DONE HERE: no ray is cast (a car parked at the wall, a body: he is carried through it - the collision is
 *    off); no input is taken away (the clip moves him as a vault's does: vtable +0x214, 0x41a6b0, says 'moved by
 *    animation' for an aligned full-body clip; whether the stick still does something during it is live check K4); a
 *    gamepad has no Key; the other players of a network round would see a slide, hence Arcade only; the facing test
 *    rests on 'row 0 of a rotation is the back', read in the two routines above and not seen (the line at the foot
 *    prints the number: 1 = he looks straight at the face; Angle=0 switches the test off).
 *
 * KLHook.ini
 *   [Climb]
 *   Enable=0          1 = this file is on
 *   Dry=0             1 = everything is watched and logged, NO game routine is called (live check K1)
 *   Mode=climb        climb | vault
 *   Fallback=0        1 = Mode=climb uses the vault at an edge when the body has no climb clip
 *   Align=2           2 = Dead Men's two alignments (events 5 and 6), 1 = one, at the last frame, to top height
 *   Key=0             a virtual-key code that must be down (0x45 = E); 0 = none: standing at the foot is enough
 *   Dwell=400         ms at the foot (100 .. 5000)
 *   Speed=150         slower than this, units a second (Dead Men asks under 375)
 *   Angle=60          he must look at the face within this many degrees; 0 = not asked
 *   Log=1             2 = also, every second, where the player stands against each edge near him
 * KLJoin.ini beside the level archive (written by tools\kl_fa_climb.py; up to 8 edges: [Climb], [Climb.2] ..)
 *   [Climb]
 *   A=-3450 403.5 -625        the two ends of the edge, x y z (y is up, the same in both): the top of the obstacle
 *   B=-2650 403.5 -625        on the face that is climbed
 *   Normal=0 -1               x z, unit, level: out of that face, towards the side one stands on
 *   Floor=200                 the floor at its foot
 *   Depth=50                  how thick the obstacle is behind the edge
 *
 * LOG
 *   climb: on; Mode=climb Fallback=0 Align=2 Key=0 Dwell=400 Speed=150 Angle=60 Dry=0 Log=1; ...
 *   climb: 2 edge(s) from <file> for level f03\f03_main
 *   climb: edge 1: (-3450, 404, -625) - (-2650, 404, -625), 800 long, out of the face (0, -1); floor 200: 203.5 up = /Movement/Climb/Up/High, stand-off 47; 50 thick
 *   climb: at the foot of edge 1: node (-3003, 200, -672), +0x460 (-3003, 200, -672), 47 from the face, speed 0, facing 0.99; slot /Movement/Climb/Up/High = id 2507
 *   climb: edge 1: WOULD climb by /Movement/Climb/Up/High (slot 2507) from node (...): P1 (...) at event 5, P2 (...) at event 6 - DRY RUN, nothing is called
 *   climb: collision off (the climb starts; count 0 -> 1)
 *   climb: edge 1: started /Movement/Climb/Up/High (slot 2507) from node (...), +0x460 (...), 47 from the face: action 0b7f2a40, clip 0a2c1e30 of 52 frames (flags 10c0), events 5 at 6 and 6 at 20; aligned to (...) in 6 frames
 *   climb: edge 1: frame 6.3: aligned to P2 (-3003, 404, -672) in 13.7 frames
 *   climb: collision on (the climb is over; count 1 -> 0)
 *   climb: edge 1: over after 2090 ms: node (-3003, 404, -581), +0x460 (...); his action now 00000000
 *   climb: edge 1 NOT climbed: <why>              (once per stay at the foot)
 *
 * WIRING (klhook.c; three lines, nothing else of the hook changes; this file uses kljoin.c, klcrew_rt.c, klbot.c and
 * klescort.c, which the place after klhop.c gives)
 *   #include "klclimb.c"        after  #include "klhop.c"
 *   klq_tick(game_thread);      in klh_tick, after  klv_tick(game_thread);
 *   klq_init();                 in the init list, after  klv_init();
 */
#ifndef KLCLIMB_C
#define KLCLIMB_C

#define KLQ_PLAYER_VT   0x00bb45f4            /* ZFFPlayer */
#define KLQ_DISP_VT     0x00ba38d8            /* ZActionDispatcher = [player + 0x19c]; +4 = the current action (0 = none) */
#define KLQ_MINI_VT     0x00bb4f0c            /* ZFFActionMiniAnim */
#define KLQ_VAULT_VT    0x00bb5188            /* ZFFActionVaultOver */
#define KLQ_MINI        0x005ea340            /* ZFFPlayer::StartMiniAnim (player; u16 slot, x, alignObject, char endWithClip) */
#define KLQ_VAULT       0x00619790            /* ZFFPlayer::StartVaultOver (player; cover, char left, pos, rot, char given, char writeBack) */
#define KLQ_CLIP        0x0059d550            /* (player; u16 slot) -> clip record or 0; draws one number from the game's generator */
#define KLQ_ALIGN       0x0080fdc0            /* vtable +0x208: (player; rot[9], pos[3], float frames) -> al */
#define KLQ_COLL_OFF    0x005d6200            /* vtable +0x560 */
#define KLQ_COLL_ON     0x00686600            /* vtable +0x564 */
#define KLQ_STOP        0x008aef30            /* vtable +0x374: finish the current action */
#define KLQ_MATRIX      0x0055f8f0            /* ecx = out[9], edx = in[3]: the rotation whose row 0 is the vector; pure */
#define KLQ_ANIMDATA    0x01546f6c            /* the animation manager; [+0x10] = the clips' data block (0x4a75d0) */
#define KLQ_NEDGE       8
#define KLQ_NEAR        15.0f                 /* at the foot = this far .. */
#define KLQ_FAR         75.0f                 /* .. this far from the face (kl_fa_climb.py has tried 30, 47 and 65) */
#define KLQ_HEIGHT      40.0f                 /* and within this of Floor= */

struct klq_edge { int on, cls; float a[3], b[3], n[2], u[2], len, floor, depth; };
static const struct { const char *slot; float top, stand; } klq_cls[3] = {        /* kaneandlynch.exe 0x603340 */
    { "/Movement/Climb/Up/Low", 120.0f, 81.0f }, { "/Movement/Climb/Up/Medium", 170.0f, 47.0f }, { "/Movement/Climb/Up/High", 220.0f, 47.0f } };
static const char *const klq_vault_slot[2] = { "/Cover/Vaulting/Cover_Vault_Right_1M", "/Cover/Vaulting/Cover_Vault_Right_2M" };

static struct { int on, dry, log, vault, fallback, align, key; DWORD dwell; float speed, cosang; } klq;
static struct { int n; char key[64], file[MAX_PATH]; FILETIME ft; struct klq_edge e[KLQ_NEDGE]; } klq_lv;
static struct {                               /* the watch: where he was, since when he is at the foot of which edge */
    DWORD player, at, game_at, since[KLQ_NEDGE], say_at; float pos[3], speed; int have; char told[KLQ_NEDGE], seen[KLQ_NEDGE];
    int told_gate, told_thread, told_code;
} klq_w;
static struct {                               /* the climb that runs (player != 0) */
    DWORD player, action, chan, began, limit; int edge, vault, stage, owed;      /* stage 1 = the second alignment is still to come */
    float p2[3], rot[12], f_foot, f_top;
} klq_r;
static BYTE klq_cover[0x60];                  /* the cover record 0x619790 is handed (it reads +0x0c, +0x2c, +0x54 and keeps the pointer) */

static float klq_num(const char *sec, const char *key, const char *def, const char *file)
{
    char t[32];
    GetPrivateProfileStringA(sec, key, def, t, sizeof t, file);
    return (float)atof(t);
}

/* the [Climb] sections of the KLJoin.ini kljoin.c has read for the running level (never a stock archive's) */
static void klq_source(void)
{
    char key[64], file[MAX_PATH], sec[16], t[32]; FILETIME ft; int i, c;
    EnterCriticalSection(&klj_cs);
    snprintf(key, sizeof key, "%s", klj_map_key); snprintf(file, sizeof file, "%s", klj_map_file); ft = klj_map_ft;
    LeaveCriticalSection(&klj_cs);
    if (!strcmp(key, klq_lv.key) && !_stricmp(file, klq_lv.file) && !CompareFileTime(&ft, &klq_lv.ft)) return;
    memset(&klq_lv, 0, sizeof klq_lv);
    strcpy(klq_lv.key, key); strcpy(klq_lv.file, file); klq_lv.ft = ft;
    if (!key[0] || !file[0]) return;
    for (i = 0; i < KLQ_NEDGE; i++) {
        struct klq_edge *e = &klq_lv.e[i]; float nx = 0, nz = 0, h, ln; char nt[64], *p;
        if (i) snprintf(sec, sizeof sec, "Climb.%d", i + 1); else strcpy(sec, "Climb");
        if (!GetPrivateProfileStringA(sec, 0, "", t, sizeof t, file)) continue;                 /* no such section */
        if (!klj_vec(sec, "A", file, e->a) || !klj_vec(sec, "B", file, e->b) || !kle_ok3(e->a) || !kle_ok3(e->b)) { klog("climb: [%s] of %s refused: A= and B= need three numbers each", sec, file); continue; }
        GetPrivateProfileStringA(sec, "Normal", "", nt, sizeof nt, file);
        for (p = nt; *p; p++) if (*p == ',' || *p == ';' || *p == '(' || *p == ')') *p = ' ';
        if (sscanf(nt, "%f %f", &nx, &nz) != 2 || !klb_finite(nx) || !klb_finite(nz) || fabs(nx * nx + nz * nz - 1.0f) > 0.02f) { klog("climb: [%s] of %s refused: Normal= needs two numbers, x z, of a unit vector", sec, file); continue; }
        e->n[0] = nx; e->n[1] = nz;
        e->u[0] = e->b[0] - e->a[0]; e->u[1] = e->b[2] - e->a[2];
        ln = (float)sqrt(e->u[0] * e->u[0] + e->u[1] * e->u[1]);
        if (ln < 60.0f || fabs(e->a[1] - e->b[1]) > 1.0f) { klog("climb: [%s] of %s refused: A - B must be level and 60 long or more", sec, file); continue; }
        e->u[0] /= ln; e->u[1] /= ln; e->len = ln;
        if (fabs(e->u[0] * e->n[0] + e->u[1] * e->n[1]) > 0.02f) { klog("climb: [%s] of %s refused: Normal= is not square to A - B", sec, file); continue; }
        GetPrivateProfileStringA(sec, "Floor", "", t, sizeof t, file);
        e->floor = (float)atof(t);
        if (!t[0] || !klb_finite(e->floor)) { klog("climb: [%s] of %s refused: Floor= is needed", sec, file); continue; }
        e->depth = klq_num(sec, "Depth", "50", file); if (!klb_finite(e->depth) || e->depth < 10.0f) e->depth = 10.0f;
        h = e->a[1] - e->floor;
        for (c = 0; c < 3 && klq_cls[c].top < h; c++) ;
        if (h <= 25.0f || c == 3) { klog("climb: [%s] of %s refused: the edge is %.1f over Floor=; Dead Men climbs over 25 and up to 220", sec, file, h); continue; }
        e->cls = c; e->on = 1; klq_lv.n++;
    }
    if (!klq_lv.n) return;
    klog("climb: %d edge(s) from %s for level %s", klq_lv.n, file, key);
    for (i = 0; i < KLQ_NEDGE; i++) if (klq_lv.e[i].on) {
        const struct klq_edge *e = &klq_lv.e[i];
        klog("climb: edge %d: (%.0f, %.0f, %.0f) - (%.0f, %.0f, %.0f), %.0f long, out of the face (%g, %g); floor %.0f: %.1f up = %s, stand-off %.0f; %.0f thick",
             i + 1, e->a[0], e->a[1], e->a[2], e->b[0], e->b[1], e->b[2], e->len, e->n[0], e->n[1], e->floor, e->a[1] - e->floor, klq_cls[e->cls].slot, klq_cls[e->cls].stand, e->depth);
    }
}

/* A scene node's world place and the world image of its local z axis. That image is where the man's BACK points: a
   clip's root runs along -z (every climb, vault and fall clip of both games), and 0x857110 - what the vault and the
   alignment take a rotation from - gives it as row 0. Composed as klescort.c's kle_node composes the place. */
static int klq_node(DWORD node, float pos[3], float back[3])
{
    float v[3] = { 0, 0, 0 }, d[3] = { 0, 0, 1 }, m[12], t[3]; int depth;
    if (!node) return 0;
    for (depth = 0; node && depth < 32; depth++) {
        if (!klh_rd(node, m, sizeof m)) return 0;
        t[0] = v[0] * m[6] + v[1] * m[3] + v[2] * m[0] + m[9];
        t[1] = v[0] * m[7] + v[1] * m[4] + v[2] * m[1] + m[10];
        t[2] = v[0] * m[8] + v[1] * m[5] + v[2] * m[2] + m[11];
        memcpy(v, t, sizeof v);
        t[0] = d[0] * m[6] + d[1] * m[3] + d[2] * m[0];
        t[1] = d[0] * m[7] + d[1] * m[4] + d[2] * m[1];
        t[2] = d[0] * m[8] + d[1] * m[5] + d[2] * m[2];
        memcpy(d, t, sizeof d);
        node = klh_rd32(node + 0x50);
    }
    if (node || !kle_ok3(v) || !kle_ok3(d)) return 0;
    memcpy(pos, v, sizeof v); memcpy(back, d, sizeof d);
    return 1;
}

/* The id of a slot name in the level's slot table, read as the game's own search reads it (0x68a730 from 0x426890:
   [player + 0x80] -> {n, n x {text offset, id} sorted by name, the texts}); -1 = the level has no such name. */
static int klq_slot(DWORD pl, const char *name)
{
    DWORD t = klh_rd32(pl + 0x80), n = 0, lo = 0, hi, ent[2]; char s[200]; int c;
    if (!t || !klh_rd(t, &n, 4) || !n || n > 60000) return -1;
    for (hi = n; lo < hi; ) {
        DWORD mid = (lo + hi) / 2;
        if (!klh_rd(t + 4 + 8 * mid, ent, 8) || !klh_rdstr(t + 4 + 8 * n + ent[0], s, sizeof s)) return -1;
        if (!(c = strcmp(name, s))) return (int)(ent[1] & 0xffff);
        if (c > 0) lo = mid + 1; else hi = mid;
    }
    return -1;
}

/* A clip record of the game (0x68 bytes): its frames, the frames of its events 5 and 6 (-1 = none), its record flags,
   the forward part of its net root movement (+0x18; forward is -z). Reads only (the game's own lookup is 0x4a75d0). */
static int klq_clip(DWORD clip, float *frames, float *f5, float *f6, DWORD *flags, float *fwd)
{
    BYTE r[0x30], ev[8]; DWORD mgr, base; short n, i; float net[3];
    *f5 = *f6 = -1.0f; *frames = 0; *flags = 0; *fwd = 0;
    if (!clip || !klh_rd(clip, r, sizeof r)) return 0;
    *frames = (float)*(short *)(r + 2); *flags = *(DWORD *)(r + 8); n = *(short *)(r + 6);
    memcpy(net, r + 0x18, 12); if (klb_finite(net[2])) *fwd = -net[2];
    if (*frames < 2.0f || *frames > 2000.0f) return 0;
    if (n > 0 && n < 64 && (mgr = klh_rd32((DWORD_PTR)KLH_VA(KLQ_ANIMDATA))) != 0 && (base = klh_rd32(mgr + 0x10)) != 0)
        for (i = 0; i < n; i++) {
            if (!klh_rd(base + *(DWORD *)(r + 0x10) + 8 * i, ev, 8)) break;
            if (*(DWORD *)ev == 5 && *f5 < 0) *f5 = (float)*(WORD *)(ev + 4);
            if (*(DWORD *)ev == 6 && *f6 < 0) *f6 = (float)*(WORD *)(ev + 4);
        }
    return 1;
}

/* Are the game's routines the ones this build knows? Their first bytes, and the vtable entries they are called by. */
static int klq_code(void)
{
    static const BYTE mini[14]  = { 0x6a, 0xff, 0x68, 0x5b, 0x77, 0xad, 0x00, 0x64, 0xa1, 0x00, 0x00, 0x00, 0x00, 0x50 };      /* 0x5ea340 */
    static const BYTE vault[14] = { 0x83, 0xec, 0x7c, 0x53, 0x56, 0x57, 0x8b, 0xf1, 0x8d, 0x44, 0x24, 0x28, 0x50, 0x8d };      /* 0x619790 */
    static const BYTE clip[14]  = { 0x83, 0xec, 0x0c, 0xa1, 0x40, 0x26, 0xdd, 0x00, 0x8b, 0x90, 0x30, 0x0b, 0x00, 0x00 };      /* 0x59d550 */
    static const BYTE align[14] = { 0x81, 0xec, 0xb4, 0x00, 0x00, 0x00, 0x56, 0x57, 0x8b, 0xf1, 0xe8, 0x51, 0x03, 0xf5 };      /* 0x80fdc0 */
    static const BYTE off[14]   = { 0x56, 0x8b, 0xf1, 0xe8, 0x68, 0xf0, 0x2e, 0x00, 0x8b, 0x96, 0xcc, 0x27, 0x00, 0x00 };      /* 0x5d6200 */
    static const BYTE on[14]    = { 0x56, 0x8b, 0xf1, 0xe8, 0xb8, 0xdb, 0x22, 0x00, 0xa1, 0x40, 0x26, 0xdd, 0x00, 0x8b };      /* 0x686600 */
    static const BYTE mat[14]   = { 0x83, 0xec, 0x14, 0xd9, 0x42, 0x04, 0x56, 0xd9, 0x5c, 0x24, 0x04, 0x8b, 0xf1, 0xd9 };      /* 0x55f8f0 */
    DWORD_PTR vt = (DWORD_PTR)KLH_VA(KLQ_PLAYER_VT);
    return klt_same_code(KLQ_MINI, mini, sizeof mini) && klt_same_code(KLQ_VAULT, vault, sizeof vault) && klt_same_code(KLQ_CLIP, clip, sizeof clip) &&
           klt_same_code(KLQ_ALIGN, align, sizeof align) && klt_same_code(KLQ_COLL_OFF, off, sizeof off) && klt_same_code(KLQ_COLL_ON, on, sizeof on) &&
           klt_same_code(KLQ_MATRIX, mat, sizeof mat) &&
           klh_rd32(vt + 0x208) == KLQ_ALIGN && klh_rd32(vt + 0x560) == KLQ_COLL_OFF && klh_rd32(vt + 0x564) == KLQ_COLL_ON && klh_rd32(vt + 0x374) == KLQ_STOP;
}

/* What the routines take for granted of the player they are handed -> 0 = they may be called, else why not. Reads only. */
static const char *klq_refuse(DWORD pl, DWORD *disp_)
{
    DWORD node, fl = 0, disp, act = 1, mv, kind = 0, f438 = 0, down, st = 0, d44 = 1, cnt = 1, p, q, r, sys, a, w, idx = 0, e; BYTE on = 0;
    if (klh_rd32(pl) != KLQ_PLAYER_VT) return "the local player is not a ZFFPlayer";
    if (!(node = klh_rd32(pl + 4)) || !klh_rd(node + 0x3c, &fl, 4) || (fl >> 10 & 1)) return "his node is off (flag bit 10)";
    if (!klh_rd(pl + 0xd44, &d44, 4) || d44) return "he is attached to something ([player+0xd44]: a vehicle, a seat)";
    if (!klh_rd(pl + 0x438, &f438, 4) || (f438 & 0x40000)) return "he is dead (bit 0x40000 of [player+0x438])";
    if (!(down = klh_rd32(pl + 0x2940)) || !klh_rd(down + 0x24, &st, 4)) return "[player+0x2940], his down state, cannot be read";
    if (st >= 2 && st <= 13 && st != 10) return "he is down ([[player+0x2940]+0x24] is 2 .. 13)";
    if (!(mv = klh_rd32(pl + 0x6b4)) || !klh_rd(mv + 0x44, &kind, 4) || (kind != 2 && kind != 3)) return "he neither stands nor walks (movement kind is not 2 / 3: cover, a fall, a roll ...)";
    if (!(disp = klh_rd32(pl + 0x19c)) || klh_rd32(disp) != KLQ_DISP_VT || !klh_rd(disp + 4, &act, 4)) return "[player+0x19c] is not his action dispatcher";
    if (act) return "an action of his runs (a reload, a pick-up, a vault ...)";
    if (!klh_rd(pl + 0x7b4, &cnt, 4) || cnt || !klh_rd(pl + 0x7a5, &on, 1) || !on) return "his collision is switched off already ([player+0x7b4] is not 0 or [player+0x7a5] is 0)";
    /* what 0x5ea340 writes through without a test: [player+0xbe0] (+0x10, +0x18), its +0xc (+0xce4), [player+0xdbc] (+0x1ead .. +0x1eb1) */
    if (!(p = klh_rd32(pl + 0xbe0)) || !klt_writable(p, 0x1c) || !(q = klh_rd32(p + 0xc)) || !klt_writable(q + 0xce4, 1)) return "[player+0xbe0], which the game's routine writes through (0x8b7410), is null or not writable";
    if (!(r = klh_rd32(pl + 0xdbc)) || !klt_writable(r + 0x1ead, 5)) return "[player+0xdbc], which the game's routine writes through (0x4c1a70), is null or not writable";
    /* what 0x5d6200 / 0x686600 read without a test: the physics world's body table at +0x11840, by [player+0x27cc] */
    if (!(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) || !(a = klh_rd32(sys + 0xac)) || !(w = klh_rd32(a + 0x52cc)) || !klh_rd(pl + 0x27cc, &idx, 4) || idx > 0x400 ||
        !(e = klh_rd32(w + 4 * idx + 0x11840)) || !klh_rd32(e)) return "his body in the physics world cannot be read ([[world+0x11840+4*[player+0x27cc]]])";
    *disp_ = disp;
    return 0;
}

/* Is pl still one of the game's players? (An object a level has thrown away may keep its bytes for a while.) */
static int klq_registered(DWORD pl)
{
    DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA)), tab[28]; int i;
    if (!gd || !klh_rd(gd + 0x828, tab, sizeof tab)) return 0;
    for (i = 0; i < 28; i++) if (tab[i] == pl) return 1;
    return 0;
}

static void klq_collision(DWORD pl, int on, const char *why)
{
    DWORD before = klh_rd32(pl + 0x7b4);
    ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(on ? KLQ_COLL_ON : KLQ_COLL_OFF))((void *)(DWORD_PTR)pl, 0);
    if (klq.log) klog("climb: collision %s (%s; count %lu -> %lu)", on ? "on" : "off", why, before, klh_rd32(pl + 0x7b4));
}

static char klq_align(DWORD pl, const float rot[9], const float pos[3], float frames)
{
    float p[4];
    p[0] = pos[0]; p[1] = pos[1]; p[2] = pos[2]; p[3] = 0;
    return ((char (__fastcall *)(void *, void *, const float *, const float *, float))(DWORD_PTR)KLH_VA(KLQ_ALIGN))((void *)(DWORD_PTR)pl, 0, rot, p, frames);
}

/* A climb or a vault runs: watched every frame of the game's thread, before any gate, until the action is gone. */
static void klq_follow(DWORD now)
{
    DWORD pl = klq_r.player, disp, act = 0; float nd[3] = { 0, 0, 0 }, bk[3], ft[3] = { 0, 0, 0 }, t = 0; const char *end = 0; int ours;
    if (klh_rd32(pl) != KLQ_PLAYER_VT || !klq_registered(pl)) {
        klog("climb: the player object %08lx is gone%s: forgotten, nothing is called", pl, klq_r.owed ? " while its collision was switched off by this file (the object went with its level)" : "");
        memset(&klq_r, 0, sizeof klq_r); return;
    }
    disp = klh_rd32(pl + 0x19c);
    if (disp && klh_rd32(disp) == KLQ_DISP_VT) klh_rd(disp + 4, &act, 4);
    ours = act && act == klq_r.action && klh_rd32(act) == (DWORD)(klq_r.vault ? KLQ_VAULT_VT : KLQ_MINI_VT) && klh_rd32(act + 8) == pl &&
           (klq_r.vault || klh_rd32(act + 0x20) == klq_r.chan);
    if (ours && klq_r.stage == 1 && klh_rd(klq_r.chan + 4, &t, 4) && klb_finite(t) && t >= klq_r.f_foot) {      /* the frame of event 5 has come */
        klq_r.stage = 2;
        if (t < klq_r.f_top - 0.5f) {
            char ok = klq_align(pl, klq_r.rot, klq_r.p2, klq_r.f_top - t);
            if (klq.log) klog("climb: edge %d: frame %.1f: %s to P2 (%.0f, %.0f, %.0f) in %.1f frames", klq_r.edge + 1, t, ok ? "aligned" : "NOT aligned (the game found no channel to align)",
                              klq_r.p2[0], klq_r.p2[1], klq_r.p2[2], klq_r.f_top - t);
        } else klog("climb: edge %d: frame %.1f: the frame of event 6 (%.0f) came before the second alignment could be set - the clip goes on from the foot alignment alone", klq_r.edge + 1, t, klq_r.f_top);
    }
    if (!ours) end = "over";
    else if (now - klq_r.began > klq_r.limit) {
        /* the action did not end with its clip: stop it as the game stops any action (its End runs) */
        ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLQ_STOP))((void *)(DWORD_PTR)pl, 0);
        end = "STOPPED by this file (the action outlived its clip by 1.5 s)";
    }
    if (!end) return;
    if (klq_r.owed) klq_collision(pl, 1, "the climb is over");
    klq_node(klh_rd32(pl + 4), nd, bk); klh_rd(pl + 0x460, ft, 12);
    klog("climb: edge %d: %s after %lu ms: node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f); his action now %08lx", klq_r.edge + 1, end, now - klq_r.began,
         nd[0], nd[1], nd[2], ft[0], ft[1], ft[2], ours ? 0 : act);
    memset(&klq_r, 0, sizeof klq_r);
}

/* The vault: one call of the game's own start with a cover record of this file's and the end place given. -> 1 started */
static int klq_vault(DWORD pl, DWORD disp, int ei, const float nd[3], const float foot[3], float rise, char why[200])
{
    const struct klq_edge *e = &klq_lv.e[ei]; float n3[4] = { 0, 0, 0, 0 }, rot[12], pos[4]; DWORD act = 0; int k, s[2];
    for (k = 0; k < 2; k++) {
        if ((s[k] = klq_slot(pl, klq_vault_slot[k])) < 0) { snprintf(why, 200, "the level's .ANM has no slot %s", klq_vault_slot[k]); return 0; }
        if (!((DWORD (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)KLH_VA(KLQ_CLIP))((void *)(DWORD_PTR)pl, 0, (DWORD)s[k])) { snprintf(why, 200, "this body's set has no clip for %s (the vault would read through a null clip, 0x6a2a65)", klq_vault_slot[k]); return 0; }
    }
    n3[0] = e->n[0]; n3[2] = e->n[1];
    memset(rot, 0, sizeof rot);
    ((void (__fastcall *)(float *, const float *))(DWORD_PTR)KLH_VA(KLQ_MATRIX))(rot, n3);
    pos[0] = foot[0] - e->n[0] * e->depth * 0.5f; pos[1] = nd[1] + rise; pos[2] = foot[2] - e->n[1] * e->depth * 0.5f; pos[3] = 0;      /* the middle of the top */
    memset(klq_cover, 0, sizeof klq_cover);
    *(float *)(klq_cover + 0x0c) = foot[0]; *(float *)(klq_cover + 0x10) = nd[1]; *(float *)(klq_cover + 0x14) = foot[2];
    memcpy(klq_cover + 0x2c, n3, 12); *(float *)(klq_cover + 0x54) = e->depth;
    k = ((char (__fastcall *)(void *, void *, void *, DWORD, float *, float *, DWORD, DWORD))(DWORD_PTR)KLH_VA(KLQ_VAULT))((void *)(DWORD_PTR)pl, 0, klq_cover, 0, pos, rot, 1, 0);
    klh_rd(disp + 4, &act, 4);
    if (!k || !act || klh_rd32(act) != KLQ_VAULT_VT) {
        snprintf(why, 200, "the game's vault start %s and his action now is %08lx: the vault did not outlive its own start (re\\climb.md C.6, the case that was not established)", k ? "said yes" : "said NO", act);
        return 0;
    }
    memset(&klq_r, 0, sizeof klq_r);
    klq_r.player = pl; klq_r.action = act; klq_r.began = KLB_T(GetTickCount()); klq_r.limit = 4000; klq_r.edge = ei; klq_r.vault = 1;
    klog("climb: edge %d: the game's own VAULT started from node (%.0f, %.0f, %.0f) to (%.0f, %.0f, %.0f), slots %d / %d: action %08lx (it switches the collision off and on itself)",
         ei + 1, nd[0], nd[1], nd[2], pos[0], pos[1], pos[2], s[0], s[1], act);
    return 1;
}

/* The climb. -> 1 started (or dry), 0 not: why[200]; *noclip = the body has no clip for the slot (the vault may be tried) */
static int klq_climb(DWORD pl, DWORD disp, int ei, const float nd[3], const float ft[3], const float foot[3], float dist, float rise, int *noclip, char why[200])
{
    const struct klq_edge *e = &klq_lv.e[ei]; const char *name = klq_cls[e->cls].slot; float stand = klq_cls[e->cls].stand;
    float p1[3], p2[3], to[3], n3[4] = { 0, 0, 0, 0 }, frames, f5, f6, fwd, target; DWORD act = 0, chan = 0, clip, flags; int slot; char ok;
    *noclip = 0;
    if ((slot = klq_slot(pl, name)) < 0) { snprintf(why, 200, "the level's .ANM has no slot %s (a build without the step of tools\\kl_fa_climb.py)", name); *noclip = 1; return 0; }
    p1[0] = foot[0] + e->n[0] * stand; p1[1] = nd[1]; p1[2] = foot[2] + e->n[1] * stand;
    p2[0] = p1[0]; p2[1] = nd[1] + rise; p2[2] = p1[2];
    if (klq.dry) {
        klog("climb: edge %d: WOULD climb by %s (slot %d) from node (%.0f, %.0f, %.0f), %.0f from the face: P1 (%.0f, %.0f, %.0f) at event 5, P2 (%.0f, %.0f, %.0f) at event 6 - DRY RUN, nothing is called",
             ei + 1, name, slot, nd[0], nd[1], nd[2], dist, p1[0], p1[1], p1[2], p2[0], p2[1], p2[2]);
        return 1;
    }
    ((void (__fastcall *)(void *, void *, DWORD, DWORD, DWORD, DWORD))(DWORD_PTR)KLH_VA(KLQ_MINI))((void *)(DWORD_PTR)pl, 0, (DWORD)slot, 0, 0, 1);
    klh_rd(disp + 4, &act, 4);
    if (!act || klh_rd32(act) != KLQ_MINI_VT || klh_rd32(act + 8) != pl || (klh_rd32(act + 0x18) & 0xffff) != (DWORD)slot || !(chan = klh_rd32(act + 0x20))) {
        snprintf(why, 200, "the game did not keep the action for %s (his action now is %08lx): this body's set has no clip for the slot", name, act);
        *noclip = 1; return 0;
    }
    clip = klh_rd32(chan);
    if (!klq_clip(clip, &frames, &f5, &f6, &flags, &fwd)) { frames = 50.0f; f5 = f6 = -1.0f; }
    n3[0] = e->n[0]; n3[2] = e->n[1];
    memset(&klq_r, 0, sizeof klq_r);
    klq_r.player = pl; klq_r.action = act; klq_r.chan = chan; klq_r.began = KLB_T(GetTickCount()); klq_r.edge = ei;
    klq_r.limit = (DWORD)(frames * 40.0f) + 1500;                             /* 25 frames a second */
    ((void (__fastcall *)(float *, const float *))(DWORD_PTR)KLH_VA(KLQ_MATRIX))(klq_r.rot, n3);
    klq_collision(pl, 0, "the climb starts"); klq_r.owed = 1;
    if (klq.align == 2 && f5 > 0.0f && f6 > f5) {                             /* Dead Men: the foot at event 5, then the top at event 6 */
        memcpy(klq_r.p2, p2, 12); klq_r.f_foot = f5; klq_r.f_top = f6; klq_r.stage = 1;
        memcpy(to, p1, 12); target = f5;
    } else if (klq.align == 2 && f6 > 0.0f) {                                 /* no event 5: the top at event 6 alone, as the game's NPC mover does */
        klq_r.stage = 2; memcpy(to, p2, 12); target = f6;
    } else {                                                                  /* Align=1, or a clip without the events: the end place at the last frame */
        float over = fwd - stand; if (!(over > 5.0f)) over = 5.0f; if (over > e->depth - 5.0f) over = e->depth - 5.0f;
        to[0] = foot[0] - e->n[0] * over; to[1] = p2[1]; to[2] = foot[2] - e->n[1] * over;
        klq_r.stage = 2; target = frames - 1.0f;
    }
    ok = klq_align(pl, klq_r.rot, to, target);
    klog("climb: edge %d: started %s (slot %d) from node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f), %.0f from the face: action %08lx, clip %08lx of %.0f frames (flags %lx), events 5 at %.0f and 6 at %.0f; %s to (%.0f, %.0f, %.0f) in %.0f frames",
         ei + 1, name, slot, nd[0], nd[1], nd[2], ft[0], ft[1], ft[2], dist, act, clip, frames, flags, f5, f6, ok ? "aligned" : "NOT aligned", to[0], to[1], to[2], target);
    if (!ok) {
        /* no full-body channel with root motion was found (0x760120): the clip would play where he stands and end inside the obstacle */
        ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLQ_STOP))((void *)(DWORD_PTR)pl, 0);
        klq_collision(pl, 1, "the climb is called off");
        memset(&klq_r, 0, sizeof klq_r);
        snprintf(why, 200, "the game found no channel to align (clip flags %lx: 0x40 = root motion %s): the action was stopped, he stays where he was", flags, flags & 0x40 ? "is set" : "is NOT set");
        return 0;
    }
    return 1;
}

static void klq_tick(int game_thread)
{
    static DWORD last; struct klb_snap s; DWORD now, pl = 0, disp = 0; char scene[160], key[64], why[200]; float ft[3], hn[3], nd[3], bk[3], face, dt; const char *no; int i;
    if (!klq.on || !klh_exe_ok) return;
    now = GetTickCount();
    if (!game_thread) {                                                      /* everything here belongs to the game's thread */
        if (now - klq_w.game_at > 5000 && !klq_w.told_thread && klb_read(&s) && s.state == KLB_ROUND) {      /* (reads only) */
            klq_w.told_thread = 1;
            klog("climb: a round runs and no tick has come on the game's thread for 5 s ([KLHook] Tick=0?): nobody climbs meanwhile");
        }
        return;
    }
    klq_w.game_at = KLB_T(now);
    if (klq_r.player) { klq_follow(now); return; }                            /* a climb runs: every frame, whatever the round does */
    if (now - last < 50) return;
    last = now;
    if (!klb_read(&s) || s.state != KLB_ROUND) { klq_w.have = 0; return; }    /* an Arcade round that runs, or nothing */
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return;
    klq_source();
    if (!klq_lv.n || strcmp(key, klq_lv.key)) return;                        /* no edge, or not the level the file belongs to */
    if (!klb_level(why)) {                                                   /* klbot.c section 0: not on a stock level, an unknown one, or without the Steam guard */
        if (!klq_w.told_gate++) klog("climb: %s: nobody climbs here (it acts only on a level that is not stock)", why);
        return;
    }
    if (!klq_code()) { if (!klq_w.told_code++) klog("climb: the game's routines are not the ones this build knows: nobody climbs"); return; }
    if (!kle_human(&pl, ft, hn) || !klq_node(klh_rd32(pl + 4), nd, bk)) { klq_w.have = 0; return; }      /* no local heister in play */
    if (!klq_w.have || klq_w.player != pl) { memset(klq_w.since, 0, sizeof klq_w.since); memset(klq_w.told, 0, sizeof klq_w.told); memset(klq_w.seen, 0, sizeof klq_w.seen); klq_w.speed = 1e9f; }
    else if ((dt = (now - klq_w.at) / 1000.0f) > 0.0f)
        klq_w.speed = (float)sqrt((nd[0] - klq_w.pos[0]) * (nd[0] - klq_w.pos[0]) + (nd[2] - klq_w.pos[2]) * (nd[2] - klq_w.pos[2])) / dt;
    klq_w.have = 1; klq_w.player = pl; klq_w.at = now; memcpy(klq_w.pos, nd, 12);
    face = (float)sqrt(bk[0] * bk[0] + bk[2] * bk[2]);
    for (i = 0; i < KLQ_NEDGE; i++) {
        const struct klq_edge *e = &klq_lv.e[i]; float d, along, foot[3], look, feet, rise; int in, noclip = 0, done;
        if (!e->on) continue;
        d = (nd[0] - e->a[0]) * e->n[0] + (nd[2] - e->a[2]) * e->n[1];
        along = (nd[0] - e->a[0]) * e->u[0] + (nd[2] - e->a[2]) * e->u[1];
        /* his feet: the node's height when that is at the floor, else the floats at +0x460 (klhop.c's two readings) */
        feet = fabs(nd[1] - e->floor) <= KLQ_HEIGHT ? nd[1] : ft[1];
        in = d > KLQ_NEAR && d <= KLQ_FAR && along >= 0.0f && along <= e->len && fabs(feet - e->floor) <= KLQ_HEIGHT;      /* a NaN is not there */
        look = face > 0.01f ? (bk[0] * e->n[0] + bk[2] * e->n[1]) / face : 0.0f;      /* 1 = his back points out of the face: he looks straight at it */
        if (klq.log >= 2 && now - klq_w.say_at >= 1000 && d > -200.0f && d < 600.0f && along > -200.0f && along < e->len + 200.0f) {
            klq_w.say_at = KLB_T(now);
            klog("climb: node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f): %.0f from the face of edge %d, %.0f along it (0 .. %.0f), %+.0f / %+.0f to its floor, speed %.0f, facing %.2f%s",
                 nd[0], nd[1], nd[2], ft[0], ft[1], ft[2], d, i + 1, along, e->len, nd[1] - e->floor, ft[1] - e->floor, klq_w.speed, look, in ? " = AT THE FOOT" : "");
        }
        if (!in) { klq_w.since[i] = 0; klq_w.told[i] = 0; klq_w.seen[i] = 0; continue; }
        if (!klq_w.seen[i]) {
            klq_w.seen[i] = 1;
            if (klq.log) klog("climb: at the foot of edge %d: node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f), %.0f from the face, speed %.0f, facing %.2f; slot %s = id %d%s",
                              i + 1, nd[0], nd[1], nd[2], ft[0], ft[1], ft[2], d, klq_w.speed, look, klq_cls[e->cls].slot, klq_slot(pl, klq_cls[e->cls].slot),
                              feet == nd[1] ? "" : " (his NODE is not at the floor: the height is taken from +0x460)");
        }
        if (klq_w.told[i] == 2) continue;                                    /* tried at this stay: he has to step away first */
        if (klq_w.speed > klq.speed || (klq.cosang > -1.5f && look < klq.cosang) || (klq.key && !(GetAsyncKeyState(klq.key) & 0x8000))) { klq_w.since[i] = 0; continue; }
        if (!klq_w.since[i]) klq_w.since[i] = KLB_T(now);
        if (now - klq_w.since[i] < klq.dwell) continue;
        if ((no = klq_refuse(pl, &disp)) != 0) {                             /* a reload, a fall: it passes - said once, tried again while he stays */
            if (!klq_w.told[i]) { klq_w.told[i] = 1; klog("climb: edge %d NOT climbed yet: %s", i + 1, no); }
            continue;
        }
        foot[0] = e->a[0] + e->u[0] * along; foot[1] = e->a[1]; foot[2] = e->a[2] + e->u[1] * along;       /* the point of the edge nearest to him */
        rise = e->a[1] - feet;                                               /* Dead Men's h: the top over his feet */
        klq_w.told[i] = 2; why[0] = 0;
        if (klq.vault && klq.dry) { klog("climb: edge %d: WOULD vault from node (%.0f, %.0f, %.0f) onto the top, %.0f up - DRY RUN, nothing is called", i + 1, nd[0], nd[1], nd[2], rise); return; }
        done = klq.vault ? klq_vault(pl, disp, i, nd, foot, rise, why) : klq_climb(pl, disp, i, nd, ft, foot, d, rise, &noclip, why);
        if (!done && noclip && klq.fallback && !klq.dry) {
            klog("climb: edge %d: %s - the vault is tried (Fallback=1)", i + 1, why);
            done = klq_refuse(pl, &disp) ? 0 : klq_vault(pl, disp, i, nd, foot, rise, why);
        }
        if (!done) klog("climb: edge %d NOT climbed: %s", i + 1, why[0] ? why : "his state changed during the start");
        return;                                                               /* one start a tick */
    }
}

static void klq_init(void)
{
    char t[32]; float ang; int v;
    memset(&klq, 0, sizeof klq); memset(&klq_lv, 0, sizeof klq_lv); memset(&klq_w, 0, sizeof klq_w); memset(&klq_r, 0, sizeof klq_r);
    klq.on = GetPrivateProfileIntA("Climb", "Enable", 0, klh_ini) != 0;
    if (!klq.on) return;
    klq.dry = GetPrivateProfileIntA("Climb", "Dry", 0, klh_ini) != 0;
    GetPrivateProfileStringA("Climb", "Mode", "climb", t, sizeof t, klh_ini);
    klq.vault = !_stricmp(t, "vault");
    klq.fallback = GetPrivateProfileIntA("Climb", "Fallback", 0, klh_ini) != 0;
    klq.align = GetPrivateProfileIntA("Climb", "Align", 2, klh_ini) == 1 ? 1 : 2;
    klq.key = (int)GetPrivateProfileIntA("Climb", "Key", 0, klh_ini) & 0xff;
    v = (int)GetPrivateProfileIntA("Climb", "Dwell", 400, klh_ini); klq.dwell = (DWORD)(v < 100 ? 100 : v > 5000 ? 5000 : v);
    klq.speed = klq_num("Climb", "Speed", "150", klh_ini); if (!klb_finite(klq.speed) || klq.speed < 10.0f) klq.speed = 10.0f;
    ang = klq_num("Climb", "Angle", "60", klh_ini);
    if (!klb_finite(ang) || ang <= 0.0f || ang >= 180.0f) ang = 0.0f;
    klq.cosang = ang > 0.0f ? (float)cos(ang * 3.14159265 / 180.0) : -2.0f;      /* -2 = not asked */
    klq.log = (int)GetPrivateProfileIntA("Climb", "Log", 1, klh_ini);
    klq_w.game_at = GetTickCount();
    klog("climb: on; Mode=%s Fallback=%d Align=%d Key=%d Dwell=%lu Speed=%.0f Angle=%.0f Dry=%d Log=%d; at a [Climb] edge of the level's KLJoin.ini the local player is carried up by %s; Arcade only, on a level that is not the stock one of its slot%s",
         klq.vault ? "vault" : "climb", klq.fallback, klq.align, klq.key, klq.dwell, klq.speed, ang, klq.dry, klq.log,
         klq.vault ? "the game's own vault action (0x619790)" : "Dead Men's climb clip (StartMiniAnim 0x5ea340, the alignment 0x80fdc0, the collision switch 0x5d6200 / 0x686600)",
         klq.dry ? " - DRY RUN: no game routine is called" : "");
}

#endif /* KLCLIMB_C */
