/*
 * klrappel.c - THE ROPE DESCENT'S BODY: while the rappel cut of a level runs for the local human, move his node down the
 * clip's own root path, once a frame, by the placement call the cut itself used to start (ZFFPlayer 0x82cc40).
 * NEW FILE (track Y3, 2026-10-12). NOT WIRED into klhook.c (three lines at the end of this comment). OFF unless KLHook.ini
 * has [Rappel] Enable=1. NOTHING OF IT HAS RUN IN THE GAME. Credit: luvsic (third_party/anp) for the mini-cutscene act
 * form (the level half, tools/kl_fa_rappel.py).
 *
 * WHY (re\rappel.md section 8, read in kl2.exe build 0490, and the six live runs of the level-data climb, re\climb2.md 10-13):
 *   The cut is level data: a MiniCutsceneRout with a 'Lynch' head and ONE act (the clip /Level_Specific/L07/.../Repelling_01,
 *   a `startpos` PosObject 17.6 m over the balcony row). ZMiniPlayerActTask (0x8e8d00, read whole): vtable +0x2a4(1) /
 *   0x82cc40(rot, pos, 1, 0, 0) / +0x2a4(0) = the placement on the PosObject; vtable +0x560 = collision off; then the clip
 *   through the player's vtable +0x204 (Play whole, flags 0x20001 / 0x20003). LIVE (Y3a): the placement works, at once. The
 *   clip's root motion does NOT move him: the animation update 0x50ac80 hands the channel's root delta to 0x84c0d0 only for a
 *   channel that is aligned (flag 0x200) or moves the ground bone (0x400) (0x50b09e: test ecx, 0x600), and 0x84c0d0 passes it
 *   to the movement object ([player+0x38c] / [player+0x388]), which with the collision off has nothing to carry (re\climb.md:
 *   'the game never carries a player with it WITH THE COLLISION OFF'). No flag of the act or the clip switches that on, and
 *   the act has no event that does (the only ones it asks for are 0x27 and 0x14, the collision's, 0x8e8e9e / 0x8e8f37).
 *   So the hook does what the aligned channel would: the clip's root path (a table the level file carries) -> the node.
 *
 * WHAT IT DOES (once a frame, the game's own thread only):
 *   idle:    the local human has a full-body channel (state 1 / 3, flag 0x8000) whose clip has exactly Frames frames and his
 *            node is within Radius of Start= of the level's [Rappel] section -> the descent has begun (log line 'begun').
 *   running: t = the channel's frame; s = t / (Frames - 1); the node goes to Start + (Land - Start) * P(s), P = the clip's
 *            measured vertical root path from Profile= (linear in between), the lateral part at the same fraction; placed
 *            by 0x82cc40(rot, pos, 0, 0, 0) with the rotation he had at the start (0x55f8f0 from his back vector). From
 *            Frames - 1 - LastFrames the node is put on Land= and the hook lets go; the act ends by itself and its End
 *            (collision on, proxy sync 0x4af5b0) finds him at the landing.
 *   It gives up (and says why) when: the channel's clip changes or its state is not play; the node is not where the last
 *   placement left it (the GAME moves him too: Autodetect, then it does nothing more); the wall clock runs past
 *   Frames / 25 * 2 + 2 s; the player object changes.
 *
 * WHAT IT CALLS (read whole, say what it touches): 0x82cc40 PlaceAt(rot, pos, resetMove, force, sendNet) - with force = 0
 *   it checks [player+0x29e0] (a cooldown stamp only a forced placement sets: none is set here), writes the node frame
 *   (vtable +0x2a8) when he is attached to nothing ([player+0xd44] = 0), calls the proxy sync 0x4af5b0, the movement
 *   object's reset ([player+0x43c] vtable +0x60, vtable +0x5dc -> +0x34(1)), and with force = 0 and sendNet = 0 nothing else
 *   (the net block 0x82cd8e .. is behind both). 0x55f8f0 builds a rotation from a vector (pure). Both are checked by their
 *   first bytes before the first call. ASSUMPTION: a placement every frame is as harmless as the one the cut makes once
 *   (the movement reset runs each time); the live check shows it.
 *
 * KEYS (KLHook.ini)  [Rappel] Enable=0  Dry=0 (log only, no placement)  Log=1 (2 = a line every frame)
 *                              Radius=150 (how near to Start the node must be for the descent to begin)  LastFrames=1.5
 *                    The level's own KLJoin.ini (written by tools\kl_fa_rappel.py): [Rappel] Frames=105  Start=x y z  Land=x y z
 *                              Profile=0 12 ... 1000 (the vertical root path in thousandths, equal steps of the frame number)
 * Arcade only by the level (KLJoin.ini is read beside a level that is not stock); nothing for another player; multiplayer: it
 * does nothing unless that level file is there.
 *
 * WIRING (klhook.c; the include goes AFTER klclimb.c, the two calls beside klq_init / klq_tick):
 *     #include "klrappel.c"
 *     klrp_init();                    (in the init list, after klq_init();)
 *     klrp_tick(game_thread);         (in the tick, after klq_tick(game_thread);)
 * Off-game test: klrappel_test.c.
 */
#ifndef KLRAPPEL_C
#define KLRAPPEL_C

#define KLRP_PLAYER_VT 0x00bb45f4              /* ZFFPlayer */
#define KLRP_PLACE     0x0082cc40              /* ZFFPlayer::PlaceAt (player; float rot[9], float pos[3], char resetMove, char force, char sendNet), ret 0x14 */
#define KLRP_MATRIX    0x0055f8f0              /* ecx = out[9], edx = in[3]: the rotation whose row 0 is the vector; pure */
#define KLRP_PROFILE   64                      /* profile samples at most */

static struct { int on, dry, log; float radius, last; } klrp;
static struct {                               /* the level's [Rappel] */
    char key[64], file[MAX_PATH]; FILETIME ft; int ok, frames, n; float start[3], land[3], prof[KLRP_PROFILE];
} klrp_lv;
static struct {                               /* the descent that runs (player != 0) */
    DWORD player, chan, clip, began, last_log, clock; float rot[12], placed[3], t_last; int gamemoves, first, nplaced, have_clock;
} klrp_r;
static struct { DWORD gone_at, told_code, told_lv; int armed; } klrp_w;

/* a scene node's world place and the world image of its local z axis (= where the man's BACK points); klclimb.c's klq_node */
static int klrp_node(DWORD node, float pos[3], float back[3])
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
    if (node || !klb_finite(v[0]) || !klb_finite(v[1]) || !klb_finite(v[2]) || !klb_finite(d[0]) || !klb_finite(d[1]) || !klb_finite(d[2])) return 0;
    memcpy(pos, v, sizeof v); memcpy(back, d, sizeof d);
    return 1;
}

/* the first bytes of the two routines this file calls (kl2.exe build 0490) */
static int klrp_code(void)
{
    static const BYTE place[14] = { 0x83, 0xec, 0x0c, 0x53, 0x8a, 0x5c, 0x24, 0x20, 0x56, 0x8b, 0xf1, 0x84, 0xdb, 0x75 };      /* 0x82cc40 */
    static const BYTE mat[14]   = { 0x83, 0xec, 0x14, 0xd9, 0x42, 0x04, 0x56, 0xd9, 0x5c, 0x24, 0x04, 0x8b, 0xf1, 0xd9 };      /* 0x55f8f0 */
    return klt_same_code(KLRP_PLACE, place, sizeof place) && klt_same_code(KLRP_MATRIX, mat, sizeof mat);
}

#ifndef KLRP_PLACE_CALL
#define KLRP_PLACE_CALL(pl, rot, p) \
    ((char (__fastcall *)(void *, void *, const float *, const float *, char, char, char))(DWORD_PTR)KLH_VA(KLRP_PLACE))((void *)(DWORD_PTR)(pl), 0, (rot), (p), 0, 0, 0)
#endif
#ifndef KLRP_MATRIX_CALL
#define KLRP_MATRIX_CALL(rot, v3) ((void (__fastcall *)(float *, const float *))(DWORD_PTR)KLH_VA(KLRP_MATRIX))((rot), (v3))
#endif

/* the level's [Rappel] section of the KLJoin.ini kljoin.c has read for the running level (never beside a stock archive) */
static void klrp_source(void)
{
    char key[64], file[MAX_PATH], buf[1200], *p; FILETIME ft; int i;
    EnterCriticalSection(&klj_cs);
    snprintf(key, sizeof key, "%s", klj_map_key); snprintf(file, sizeof file, "%s", klj_map_file); ft = klj_map_ft;
    LeaveCriticalSection(&klj_cs);
    if (!strcmp(key, klrp_lv.key) && !_stricmp(file, klrp_lv.file) && !CompareFileTime(&ft, &klrp_lv.ft)) return;
    memset(&klrp_lv, 0, sizeof klrp_lv);
    strcpy(klrp_lv.key, key); strcpy(klrp_lv.file, file); klrp_lv.ft = ft;
    if (!key[0] || !file[0]) return;
    if (!GetPrivateProfileStringA("Rappel", 0, "", buf, sizeof buf, file)) return;           /* no such section */
    klrp_lv.frames = (int)GetPrivateProfileIntA("Rappel", "Frames", 0, file);
    if (!klj_vec("Rappel", "Start", file, klrp_lv.start) || !klj_vec("Rappel", "Land", file, klrp_lv.land) || klrp_lv.frames < 10 || klrp_lv.frames > 400 ||
        !klb_finite(klrp_lv.start[0]) || !klb_finite(klrp_lv.start[1]) || !klb_finite(klrp_lv.start[2]) || !klb_finite(klrp_lv.land[0]) || !klb_finite(klrp_lv.land[1]) || !klb_finite(klrp_lv.land[2])) {
        klog("rappel: [Rappel] of %s refused: Frames= (10 .. 400), Start= and Land= (three numbers each) are needed", file);
        return;
    }
    GetPrivateProfileStringA("Rappel", "Profile", "", buf, sizeof buf, file);
    for (p = buf, i = 0; i < KLRP_PROFILE; i++) {
        char *e; double v = strtod(p, &e);
        if (e == p) break;
        klrp_lv.prof[i] = (float)(v / 1000.0); p = e;
    }
    klrp_lv.n = i;
    if (klrp_lv.n < 2 || klrp_lv.prof[0] != 0.0f || klrp_lv.prof[klrp_lv.n - 1] < 0.99f || klrp_lv.prof[klrp_lv.n - 1] > 1.01f) {
        klog("rappel: [Rappel] of %s refused: Profile= needs 2 .. %d values from 0 to 1000 (read %d)", file, KLRP_PROFILE, klrp_lv.n);
        klrp_lv.n = 0; return;
    }
    for (i = 1; i < klrp_lv.n; i++) if (!(klrp_lv.prof[i] >= klrp_lv.prof[i - 1] - 0.001f)) { klog("rappel: [Rappel] of %s refused: Profile= goes back at value %d", file, i + 1); klrp_lv.n = 0; return; }
    klrp_lv.ok = 1;
    klog("rappel: %d-frame descent from %s: Start (%.0f, %.0f, %.0f) -> Land (%.0f, %.0f, %.0f), %d profile values, level %s", klrp_lv.frames, file,
         klrp_lv.start[0], klrp_lv.start[1], klrp_lv.start[2], klrp_lv.land[0], klrp_lv.land[1], klrp_lv.land[2], klrp_lv.n, key);
}

/* the share of the descent done at fraction s of the clip (0 .. 1) */
static float klrp_share(float s)
{
    float x; int i;
    if (!(s > 0.0f)) return 0.0f;
    if (s >= 1.0f) return 1.0f;
    x = s * (float)(klrp_lv.n - 1); i = (int)x; x -= (float)i;
    return klrp_lv.prof[i] + (klrp_lv.prof[i + 1] - klrp_lv.prof[i]) * x;
}

/* WHERE THE BODY REALLY IS (first live run R0: the node moved as placed, the picture never did): the character proxy
   ([[[player+0x7d0]+0x30]+0x18]+0x30, Havok metres x 100), the navigation feet +0x460, the collision count +0x7b4, the current
   action's vtable ([[player+0x19c]+4]) and the player's own address. Reads only. */
static void klrp_diag(DWORD pl, char *out, int cap)
{
    DWORD p = klh_rd32(pl + 0x7d0), ph = p ? klh_rd32(p + 0x30) : 0, m = ph ? klh_rd32(ph + 0x18) : 0, disp = klh_rd32(pl + 0x19c), act = 0, cnt = 0;
    float v[3] = { 0, 0, 0 }, ft[3] = { 0, 0, 0 }; int hp = m && klh_rd(m + 0x30, v, 12) && klb_finite(v[0]) && klb_finite(v[1]) && klb_finite(v[2]);
    if (disp) klh_rd(disp + 4, &act, 4);
    klh_rd(pl + 0x7b4, &cnt, 4); klh_rd(pl + 0x460, ft, 12);
    snprintf(out, cap, "player %08lx: proxy %s(%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f), collision count %lu, action %08lx (vtable %08lx)",
             pl, hp ? "" : "NOT READ ", v[0] * 100.0f, v[1] * 100.0f, v[2] * 100.0f, ft[0], ft[1], ft[2], cnt, act, act ? klh_rd32(act) : 0);
}

static void klrp_place(DWORD pl, const float at[3], const char *what)
{
    float p[4];
    p[0] = at[0]; p[1] = at[1]; p[2] = at[2]; p[3] = 0;
    if (!klrp.dry) KLRP_PLACE_CALL(pl, klrp_r.rot, p);
    memcpy(klrp_r.placed, at, 12); klrp_r.nplaced++;
    if (klrp.log >= 2) klog("rappel: %s: %s at (%.1f, %.1f, %.1f)", what, klrp.dry ? "WOULD place" : "placed", at[0], at[1], at[2]);
}

static void klrp_end(DWORD now, const char *why)
{
    float nd[3] = { 0, 0, 0 }, bk[3];
    if (klrp_r.player) klrp_node(klh_rd32(klrp_r.player + 4), nd, bk);
    klog("rappel: %s after %lu ms by the clock, %d placement(s), last frame %.1f of %d: node (%.1f, %.1f, %.1f)", why, now - klrp_r.began, klrp_r.nplaced, klrp_r.t_last, klrp_lv.frames, nd[0], nd[1], nd[2]);
    memset(&klrp_r, 0, sizeof klrp_r);
    klrp_w.gone_at = now; klrp_w.armed = 0;
}

/* the game's clock, 1024 a second (klclimb.c's klq_clock) */
static int klrp_clock(DWORD *t)
{
    DWORD sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF));
    return sys && klh_rd(sys + 0x48, t, 4);
}

/* is player pl's channel i the descent's? -> the channel's address, else 0 */
static DWORD klrp_chan(DWORD pl, int frames, DWORD want_clip)
{
    DWORD an = klh_rd32(pl + 0x70), fl = 0, clip; WORD w = 0; int i;
    if (!an) return 0;
    for (i = 0; i < 16; i++) {
        if (!klh_rd(an + 0x30 + 0x38 * i, &fl, 4)) return 0;
        if (((fl & 7) != 1 && (fl & 7) != 3) || !(fl & 0x8000)) continue;
        clip = klh_rd32(an + 0x1c + 0x38 * i);
        if (!clip || (want_clip && clip != want_clip) || !klh_rd(clip + 2, &w, 2) || (int)w != frames) continue;
        return an + 0x1c + 0x38 * i;
    }
    return 0;
}

static void klrp_run(DWORD now)
{
    DWORD pl = klrp_r.player, c = 0; float t = -1.0f, nd[3], bk[3], s, sh, at[3], lastf; int i;
    if (klh_rd32(pl) != KLRP_PLAYER_VT) { klrp_end(now, "OVER: the player object is gone"); return; }
    if (now - klrp_r.began > (DWORD)(klrp_lv.frames / 25.0 * 2000.0 + 2000.0)) { klrp_end(now, "GAVE UP: longer than twice the clip"); return; }
    if (klrp_chan(pl, klrp_lv.frames, klrp_r.clip) != klrp_r.chan || !klh_rd(klrp_r.chan + 4, &t, 4) || !klb_finite(t)) {
        klrp_end(now, klrp_r.t_last >= (float)(klrp_lv.frames - 1) - klrp.last - 3.0f ? "OVER: the clip ended" : "STOPPED: his rappel channel is gone before its last frames");
        return;
    }
    if (!klrp_node(klh_rd32(pl + 4), nd, bk)) { klrp_end(now, "GAVE UP: his node cannot be read"); return; }
    if (klrp_r.nplaced && !klrp_r.gamemoves) {                                  /* did anything but this file move him since the last placement? */
        float d = (float)fabs(nd[1] - klrp_r.placed[1]) + (float)fabs(nd[0] - klrp_r.placed[0]) + (float)fabs(nd[2] - klrp_r.placed[2]);
        if (!klrp.dry && d > 6.0f) {
            klrp_r.gamemoves = 1;
            klog("rappel: the node is %.1f from where the last placement left it ((%.1f, %.1f, %.1f) against (%.1f, %.1f, %.1f)) at frame %.1f: THE GAME MOVES HIM TOO (root motion applied after all) - nothing more is placed until the last frames",
                 d, nd[0], nd[1], nd[2], klrp_r.placed[0], klrp_r.placed[1], klrp_r.placed[2], t);
        }
    }
    klrp_r.t_last = t;
    lastf = (float)(klrp_lv.frames - 1);
    s = t / lastf;
    sh = klrp_share(s);
    for (i = 0; i < 3; i++) at[i] = klrp_lv.start[i] + (klrp_lv.land[i] - klrp_lv.start[i]) * sh;
    if (t >= lastf - klrp.last) {                                              /* the last frames: on the row, then let go */
        memcpy(at, klrp_lv.land, 12);
        klrp_place(pl, at, "landing");
        klrp_end(now, "LANDED");
        return;
    }
    if (klrp_r.gamemoves) return;
    if (now - klrp_r.last_log >= 500 || klrp.log >= 3) {
        char dg[300];
        klrp_r.last_log = now;
        klrp_diag(pl, dg, sizeof dg);
        if (klrp.log >= 1) klog("rappel: %s", dg);
        if (klrp.log >= 1) klog("rappel: frame %.1f of %d (%.0f %%): node (%.1f, %.1f, %.1f) -> (%.1f, %.1f, %.1f)%s", t, klrp_lv.frames, sh * 100.0f, nd[0], nd[1], nd[2], at[0], at[1], at[2], klrp.dry ? " - DRY RUN" : "");
    }
    if (klrp_r.have_clock && klrp_clock(&c) && c == klrp_r.clock) return;      /* one placement for each step of the game's clock, not one for every tick of the hook (run R0: 920 a second) */
    if (klrp_clock(&c)) { klrp_r.have_clock = 1; klrp_r.clock = c; }
    klrp_place(pl, at, "descent");
}

static void klrp_tick(int game_thread)
{
    static DWORD scene_at; DWORD now, pl = 0, chan; float ft[3], nd[3], bk[3], v3[3], d; char scene[160], key[64];
    if (!klrp.on || !klh_exe_ok || !game_thread) return;
    now = GetTickCount();
    klrp_source();
    if (!klrp_lv.ok) { if (klrp_r.player) klrp_end(now, "OVER: the level has no [Rappel] any more"); return; }
    if (klrp_r.player) { klrp_run(now); return; }
    if (now - scene_at < 50) return;                                         /* looking for a start: twenty times a second is plenty */
    scene_at = now;
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key) || strcmp(key, klrp_lv.key)) return;
    if (!kle_human(&pl, ft, nd) || klh_rd32(pl) != KLRP_PLAYER_VT) return;
    chan = klrp_chan(pl, klrp_lv.frames, 0);
    if (!chan) { if (!klrp_w.armed && now - klrp_w.gone_at > 2000) klrp_w.armed = 1; return; }      /* armed again 2 s after no such channel plays */
    if (!klrp_w.armed) return;                                                /* the same descent's channel is still there (the cut holds the last frame) */
    if (!klrp_node(klh_rd32(pl + 4), nd, bk)) return;
    d = (float)sqrt((nd[0] - klrp_lv.start[0]) * (nd[0] - klrp_lv.start[0]) + (nd[2] - klrp_lv.start[2]) * (nd[2] - klrp_lv.start[2]));
    if (d > klrp.radius || (float)fabs(nd[1] - klrp_lv.start[1]) > klrp.radius) {
        if (!klrp_w.told_lv++) klog("rappel: a %d-frame full-body clip plays for the human but his node (%.0f, %.0f, %.0f) is %.0f from Start (%.0f, %.0f, %.0f): not the descent", klrp_lv.frames, nd[0], nd[1], nd[2], d, klrp_lv.start[0], klrp_lv.start[1], klrp_lv.start[2]);
        return;
    }
    if (!klrp_code()) { if (!klrp_w.told_code++) klog("rappel: the game's routines are not the ones this build knows: nobody is placed"); return; }
    memset(&klrp_r, 0, sizeof klrp_r);
    klrp_r.player = pl; klrp_r.chan = chan; klrp_r.clip = klh_rd32(chan); klrp_r.began = now; klrp_r.first = 1;
    memset(klrp_r.rot, 0, sizeof klrp_r.rot);
    v3[0] = bk[0]; v3[1] = 0.0f; v3[2] = bk[2];                             /* the cut put him on the PosObject facing as the START rows do: the back vector, level */
    KLRP_MATRIX_CALL(klrp_r.rot, v3);
    klrp_w.armed = 0; klrp_w.told_lv = 0;
    { char dg[300]; klrp_diag(pl, dg, sizeof dg); klog("rappel: at the start: %s", dg); }
    klog("rappel: begun%s: the human's node is at (%.1f, %.1f, %.1f), %.1f from Start, back (%.2f, %.2f, %.2f); %d-frame clip %08lx in channel %08lx; the descent follows the profile to Land (%.0f, %.0f, %.0f)",
         klrp.dry ? " (DRY RUN: nothing is placed)" : "", nd[0], nd[1], nd[2], d, bk[0], bk[1], bk[2], klrp_lv.frames, klrp_r.clip, chan, klrp_lv.land[0], klrp_lv.land[1], klrp_lv.land[2]);
}

static void klrp_init(void)
{
    char t[32];
    memset(&klrp, 0, sizeof klrp); memset(&klrp_lv, 0, sizeof klrp_lv); memset(&klrp_r, 0, sizeof klrp_r); memset(&klrp_w, 0, sizeof klrp_w);
    klrp.on = GetPrivateProfileIntA("Rappel", "Enable", 0, klh_ini) != 0;
    if (!klrp.on) return;
    klrp.dry = GetPrivateProfileIntA("Rappel", "Dry", 0, klh_ini) != 0;
    klrp.log = (int)GetPrivateProfileIntA("Rappel", "Log", 1, klh_ini);
    GetPrivateProfileStringA("Rappel", "Radius", "150", t, sizeof t, klh_ini); klrp.radius = (float)atof(t);
    if (!klb_finite(klrp.radius) || klrp.radius < 20.0f) klrp.radius = 150.0f;
    GetPrivateProfileStringA("Rappel", "LastFrames", "1.5", t, sizeof t, klh_ini); klrp.last = (float)atof(t);
    if (!klb_finite(klrp.last) || klrp.last < 0.5f || klrp.last > 6.0f) klrp.last = 1.5f;
    klrp_w.armed = 1;
    klog("rappel: on; Dry=%d Log=%d Radius=%.0f LastFrames=%.1f; while the level's rappel cut (a [Rappel] section in its KLJoin.ini) runs for the local human, his node follows the clip's root path (placement 0x82cc40 once a frame)%s",
         klrp.dry, klrp.log, klrp.radius, klrp.last, klrp.dry ? " - DRY RUN: no game routine is called" : "");
}

#endif /* KLRAPPEL_C */
