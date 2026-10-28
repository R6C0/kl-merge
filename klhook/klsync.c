/*
 * klsync.c - [Sync] "does every peer see the same world?" PROBE + host->peer COMPARE channel (2026-10-26). Part of KLHook (included by
 * klhook.c after klcharonline.c, SHIP and TEST alike). READ-ONLY: this module writes NOTHING to the game. re\bots_online_sync.md has the
 * reading (which object kind is synced how, what is verified and what is GUESS) and the bench recipe.
 *
 * Why: owner 2026-10-26 (9-instance System Link round on a Dead Men map): the cops 'looked completely different on each screen', and
 * 'they all need to be in the same position for everything to be fair'. Static reading alone cannot tell WHICH of the possible causes it is
 * (re\bots_online_sync.md 3), so this module measures it, on every peer, with the same clock:
 *   [Sync] Probe=1   every Every ms (3000) in an online round: one header 'sync: list T=<ms> ...' then one line per object of interest:
 *                      'sync: s=<entity table slot> c=<class> t=<team|-> p=x,y,z hp=<health|-> f=<flag|->'
 *                    Order = entity table order = load order, so slot N is the SAME object on every peer that loaded the same level (the
 *                    DDL scene refs rely on the same fact). T = wall clock (ms, mod 1e9): peers on one PC share it exactly, LAN peers to NTP
 *                    accuracy. tools\kl_syncdiff.py lines the logs up by T and prints, per slot, the spread of the position / health.
 *                    Objects: every ZFFActor (cops, guards, civilians, AI heisters, players) FIRST, then the other kinds in kinds[] below.
 *   [Sync] Share=1   (host only) every ShareMs (250) the host broadcasts its ZFFActor slots, positions and health on UDP 27415.
 *   [Sync] Compare=1 (client only) compares each received host list with the own actors of the same slot and logs
 *                      'sync: vs host: N actors, M farther than Tol, worst slot S d=..' (+ the first 8 offenders) once a second.
 *                    This is the live answer to 'is the same cop at the same place': no log alignment needed. The host list is up to
 *                    ShareMs + network old, a walking cop moves ~3 units a second: read d against that, not against 0.
 *   [Sync] Apply=1   (CLIENT only, default 0, needs the host's Share=1) snaps a non-player ZFFActor (cop / guard / civilian / AI heister) to the
 *                    host's place when the host record is fresh (age <= 2 * ShareMs by the HOST clock) and the own place is farther than ApplyTol (150) away: the game's
 *                    own actor teleport (klt_teleport, klcrew_rt.c) from the game's tick. Records are 20 bytes ('KLSY2': slot, hp, place, class, team):
 *                    a slot is only snapped when class AND team match (slot ids are not assumed equal on every peer), and only after the Compare walk
 *                    (1 Hz, run internally by Apply too) found <= 10% of the shared slots with another class / team ('identity agreement').
 *                    Packets: only from the first source that sent a valid list this round; everything received is dropped on (re)entering a round.
 *                    The worst ApplyMax (8) offenders per pass (farthest first), at most 2 passes a second, each snap logged ('sync: apply: snap ...');
 *                    an actor that faults in the teleport is blacklisted for the round. Never on the host, never offline / Arcade, only mode 4
 *                    (System Link / online). Fail closed: no local ZFFPlayer found = no pass; a human's actor is never touched (klsy_human). The
 *                    team test also keeps AI heisters out when they share a team object with a human (so 'AI heister' may not be snapped; also a
 *                    cop within 40 units of a player's feet is skipped). Host hp<=0 while the own actor lives is only logged (nothing is
 *                    killed: GUESS area). [Sync] ApplyHp=1 is a STUB: it only logs hp differences.
 *                    GUESSES: the teleport's position is the node position kle_node reads (the feet may differ by a constant); the identity
 *                    rotation the game's routine takes turns the snapped actor to its default facing (no yaw is sent yet); no cool-down per
 *                    actor other than the tolerance, so a cop whose route the client simulates differently may be snapped again each list.
 *   [Sync] PuppetMode=1 (default 1, 2026-10-26 b): 0 = the velocity steer above. 1 = a cop whose controller [A+0x8e0] is 0 or != [A+0x50c] (0x70f660 would be a no-op) is moved
 *                    by bounded steps (min(dist, speed*dt), dt <= 100 ms) through ZFFActor slot 373 (0x560de0) toward the host's place; a cop with a matching controller gets
 *                    0x70f660(A, hostPlace, 0) (a POSITION, not a velocity) if the controller is a 0xbb42ac follower. GUESSES: slot 373 flags (1,0), vec2 of 0x70f660.
 *   [Sync] PuppetMode=2 (2026-10-26 c, from SP1c): mode 1's step CANNOT move a node. Slot 373 (0x560de0) only records the wanted place at [A+0x460..0x468] (+ a ground trace when
 *                    [A+0x57c]&1) and commits it through 0x607720 only when its 3rd stack argument is nonzero AND the node has flag 0x40000 (a physics-driven node); the cops'
 *                    nodes (flags 4b01918x) lack 0x40000 and the step passes 0, so the call returns without touching the node: 'step call did not move the node' for every slot.
 *                    [A+0x8c] is the routine's early-out byte (nonzero = return at once); it was 0 in every line, so that is not the reason. Mode 2 therefore places a cop that is
 *                    farther than SnapDist (300) from the host's place, alive on both sides and not a human, with the game's teleport 0x62a900 (klt_teleport behind klt_tele_known +
 *                    klt_refuse, as klauto.c's tele), at most once per SnapEvery ms (2000) per actor; the mode-1 step is off; the 0x70f660 follower steer and the no-progress
 *                    snap stay. Host entries that share one point (within 0.5 in x/z) or are all-zero are PLACEHOLDERS (SP1c: slots 564/565/... all at (509,-979,8648.7), probably
 *                    the cops' spawn point) and are never a goal. GUESS: 'ragdolled' has no known field, hp > 0 on both sides is the proxy. Log: 'sync: puppet: snap slot N d=D -> (x,y,z)'
 *                    and every 5 s 'sync: puppet: snap summary: ...'.
 *   [Sync] Puppet=1  (CLIENT only, default 0, needs the host's Share=1; use it INSTEAD of Apply) 2026-10-26, from the static report on kl2.exe 0490. The stock client
 *                    cop is a velocity-steered puppet (ZFFActor::Update slot 87 = 0x40ef60 -> 0x899c40 -> 0x8efe90 steer through 0x70f660(A, &vel, &zero) into the
 *                    movement controller [A+0x8e0], active only while [A+0x8e0] == [A+0x50c]). A cop of team PuppetTeam (3) that is farther than PuppetTol (60)
 *                    from the host's place gets a PRIVATE copy of the ZFFActor vtable (as klnetsmooth.c does for players) whose slot 87 runs the stock Update and then
 *                    calls the same 0x70f660 with a horizontal velocity of PuppetSpeed (300 units/s, raised to 1.25 x the host cop's measured speed, at most 3 x; slowing in the last quarter second) toward the host's place
                    (review 2026-10-26: a position gate (>= 60% of the cops within PuppetSnap of their slot's record) must be open before any hook; no snap in the first 1.5 s of a hook; a cop with no progress for 4 s (2 s if only vertical) is snapped;
                    a cop next to a human is released quietly and not re-hooked for 3 s; released after 3 s inside tolerance; the wrapper stops at health <= 0; every list-stale second > 3 releases all;
                    other modules read the vtable through klh_avt() so a puppeted cop is still a ZFFActor for them):
 *                    the AI's own move-to path, no animation reset. Back to the stock vtable once within PuppetTol for 4 passes, when it dies, when the host list
 *                    drops it, or the round ends. Beyond PuppetSnap (1500) the game's teleport (as Apply, 3 s cool-down per cop). Same trust as Apply: mode 4,
 *                    fresh list, identity agreement, a known local player, never a human or an actor sharing a human's team. 3 faults in the steer = Puppet off.
 *                    PuppetDiag=1 (works without Puppet) logs 'sync: puppet diag:' lines (DO, owner, controller pair, cover fields) for up to 8 cops in the first pass
 *                    and for offenders every 3 s, to tell 'steer skipped' from 'cover resolved elsewhere'. Proof lines: 'sync: puppet: slot N ... START / goal ... dist D /
 *                    CONVERGED / SNAP'. NOT RUN LIVE. A puppeted cop shows the private vtable: other modules' 'vtable == 0xbb3bac' tests skip it meanwhile.
 *                    GUESSES: units of the velocity (units/s, world axes, Y up), the meaning of the second vector, the cop team value 3, that the game calls slot 87
 *                    through the vtable (the log says if the wrapper never ran), that a steer toward the host's place beats the client's cover logic.
 * Class names come from the object's RTTI (vtable[-1] -> complete object locator +0xc -> type descriptor +8): CERTAIN layout for MSVC x86;
 * every read goes through klh_rd (guarded), an unreadable object is skipped.
 * GUESS: position of the non-actor kinds = kle_node([obj+4]) like the actors'; where that read fails the line says 'p=none'.
 */
#ifndef KLSYNC_C
#define KLSYNC_C

#include <ctype.h>
#define KLSY_PORT 27415
#define KLSY_MAXP 512

typedef struct { short fam; unsigned short port; unsigned long addr; char zero[8]; } klsy_sin;
/* 20 bytes per actor ('KLSY2'): slot, hp, place, and the IDENTITY the client checks before it moves anything: cls = low 16 bits of the actor's
   vtable (its class), team = the team value [[o+0x54]+4] (-1 = unreadable). Slot ids are NOT assumed equal on every peer (re\graft_formats.md). */
struct klsy_pe { unsigned short slot; short hp; float p[3]; unsigned short cls; short team; };
typedef char klsy_pe_size_is_20[sizeof(struct klsy_pe) == 20 ? 1 : -1];

/* ---- [Sync] Puppet state (client): see the header. The private ZFFActor vtable and the per-actor goal table. ---- */
#define KSP_ACTOR_VT 0x00bb3bacu
#define KSP_SLOT 87                                    /* ZFFActor::Update = 0x40ef60 (read in the exe, checked again before the first swap) */
#define KSP_NSLOT 512
#define KSP_MAXE 128                                   /* Track keeps a cop hooked until it dies / is parked / leaves the list: room for every live cop (review 2026-10-26) */
typedef void (__fastcall *ksp_fn)(void *self, void *edx);
typedef void (__fastcall *ksp_steer_fn)(void *self, void *edx, const float *vel, const float *zero);
static DWORD ksp_vtblk[KSP_NSLOT + 1];                 /* [0] = the stock vt[-1] (RTTI locator), then the private copy */
#define ksp_vt (ksp_vtblk + 1)
static DWORD ksp_orig; static int ksp_ready;
/* tolSince = since when the cop stays within PuppetTol (0 = not); best / bestAt = the smallest distance seen and when (the no-progress snap); prev* / hspeed = the host cop's own
   horizontal speed from consecutive host lists (scales the steer); dead = the Update wrapper saw health <= 0 (the next pass releases) */
struct ksp_e { DWORD o, slot, goalAt, since, lastLog, lastSnap, pass, tolSince, bestAt, prevAt, stepAt, nomove, trkAt; float goal[3], prev[3], d0, dlast, best, hspeed; volatile LONG calls, steered, mism, dead, stepped; };
static struct ksp_e ksp_e[KSP_MAXE];
static struct { DWORD o, until; } ksp_cool[16]; static int ksp_coolN;           /* cops released next to a human: not re-hooked for a while */
static struct { int pup, cops, bots, diag, nlive, gate; float tol, snap, speed, prevAvg, snapDist; int team, mode; DWORD pass, roundAt, diagAt, pupAt, snapEvery, sumAt; int faults, toldMism, toldNoCall; LONG nsteer, nsnap, nconv, nstep, nsn2, nph, nref, nflt; } ksp;
/* PuppetMode 2: per-actor time of the last placement (the SnapEvery limit) and the host entries that look like placeholders (set each pass) */
static struct { DWORD o, at; } ksp_sn[64]; static BYTE ksp_ph[KLSY_MAXP];
/* [Sync] ParkSkip: per actor, was its node off (bit 10 of [[A+4]+0x3c]) when last seen; a 1 -> 0 change = woken, snapped at once */
static struct { DWORD o; BYTE pk; } ksp_pk[64]; static struct { int on; LONG npark, nwake; } kspk;
static DWORD ksp_ours(void) { return ksp_ready ? (DWORD)(DWORD_PTR)ksp_vt : 0; }
/* the class vtable of an actor as the rest of this file means it: a puppeted actor shows our private table, which is still a ZFFActor */
static DWORD klsy_vtof(DWORD o)
{
    DWORD v = klh_rd32(o);
    return ((ksp_ready && v == (DWORD)(DWORD_PTR)ksp_vt) || (klh_actor_priv2 && v == klh_actor_priv2)) ? KSP_ACTOR_VT : v;      /* priv2: the host's bots (klbalance.c OnlineCopToBot) */
}
#define KLSY_REC 20
#define KLSY_NBAD 16
#define KLSY_MAXOFF 128
static struct {
    int on, share, cmp, max, tol10, apply, applyHp, applyMax, applyTol, toldApply, toldRefuse, toldHum, applyRx;
    int inwin, agree, rxAnchored, srcSet, lim, nbad, humLogs, rxAge;
    unsigned long srcAddr;
    DWORD every, shareMs, at, shAt, cmpAt, rxAt, rxT, applyAt, anchorNow, anchorT, bad[KLSY_NBAD];
    UINT_PTR sock; int sockTried, toldMode;
    struct klsy_pe host[KLSY_MAXP]; int nhost;
    int (WINAPI *WSAStartup)(WORD, void *);
    UINT_PTR (WINAPI *socket)(int, int, int);
    int (WINAPI *setsockopt)(UINT_PTR, int, int, const char *, int);
    int (WINAPI *bind)(UINT_PTR, const void *, int);
    int (WINAPI *sendto)(UINT_PTR, const char *, int, int, const void *, int);
    int (WINAPI *recvfrom)(UINT_PTR, char *, int, int, void *, int *);
    int (WINAPI *ioctl)(UINT_PTR, long, unsigned long *);
} klsy;

/* ---- [Sync] Track (2026-10-26, workflow wf_fa7929ae-a10 design): the 2 s snap leaves a snapped cop frozen while the host cop runs on (median snap distance ~900 = host speed x 2 s), and SP1f showed
   a just-snapped cop released again in the same millisecond (the snap returns skipped e->pass). Track places every hooked cop continuously at the host's place EXTRAPOLATED by the list age:
   per host entry a velocity from consecutive lists, goal = p + v * min(0.6 s, listAge + TrackLeadMs). Game calls only (klt_teleport behind klt_tele_known + klt_refuse) and data writes. ---- */
#define KST_N 1024
static struct { float p0[3], v[3]; DWORD T0; unsigned short slot; BYTE ok; } ksp_trk[KST_N];
static struct {
    int keep, on, bound, cmpLead, bindFix, max, local, keepRot, start, stall, keepY; DWORD ms, stallMs; float tol, leadMs, boundDist, yTol;
    DWORD frame, sumAt, rvLogAt; BYTE ctl[KST_N], bound1[KST_N];
    float bdBest[KST_N]; DWORD bdAt[KST_N], bdHold[KST_N], rvAt0[KST_N]; BYTE rvN[KST_N];   /* bound-follower stall detector / revert cap, per slot */
    LONG nstall, nrevNet, nrevY;
    LONG nplace, nref, nflt, nclose, ndead, npark, nhum, nph, nbound, nrev, ntracked, nbind; double errSum; float errMax;   /* 5 s window (reset by the summary) except nrev / nbind (round) */
} kst;
struct ksp_rv { DWORD o, slot, at, frame; float pl[3]; BYTE stage, logged; };
static struct ksp_rv ksp_rv[16];
/* the host's place of entry i at 'now', moved on by v x min(0.6 s, time since the list was sent + leadMs) */
static void ksp_goal_at(int i, DWORD now, float leadMs, float out[3])
{
    float t = ((float)(int)(now - klsy.rxAt) + (float)klsy.rxAge + leadMs) / 1000.0f; int k = klsy.host[i].slot & (KST_N - 1);
    memcpy(out, klsy.host[i].p, 12);
    if (!ksp_trk[k].ok || ksp_trk[k].slot != klsy.host[i].slot) return;
    if (t < 0) t = 0; if (t > 0.6f) t = 0.6f;
    out[0] += ksp_trk[k].v[0] * t; out[2] += ksp_trk[k].v[2] * t;                    /* vy stays 0: the floor is the host's */
}
/* placeholders: GUESS = two or more host entries on one point (within 0.5 unit in x and z), or an all-zero place; SP1c showed 4+ slots at (509,-979,8648.7). Built where a list is accepted (review 2026-10-26: the flags must belong to klsy.host as it is now) and in each pass */
static void ksp_mkph(void)
{
    int a, b; memset(ksp_ph, 0, sizeof ksp_ph);
    for (a = 0; a < klsy.nhost && a < KLSY_MAXP; a++) {
        if (fabsf(klsy.host[a].p[0]) < 0.01f && fabsf(klsy.host[a].p[1]) < 0.01f && fabsf(klsy.host[a].p[2]) < 0.01f) ksp_ph[a] = 1;
        for (b = a + 1; b < klsy.nhost && b < KLSY_MAXP; b++)
            if (fabsf(klsy.host[a].p[0] - klsy.host[b].p[0]) < 0.5f && fabsf(klsy.host[a].p[2] - klsy.host[b].p[2]) < 0.5f && fabsf(klsy.host[a].p[1] - klsy.host[b].p[1]) < 2.0f) ksp_ph[a] = ksp_ph[b] = 1;
    }
}
/* a new host list was accepted (host clock T, ms mod 1e9): update every entry's velocity. Horizontal speed clamped to 900 u/s (GUESS: faster than a sprinting cop = a wake / teleport); a step over
   1500 units or a gap over 1000 ms (or a clock wrap) resets it to 0. Entries less than 40 ms apart keep the old state (a noisy quotient). */
static void ksp_trk_feed(DWORD T)
{
    int j;
    for (j = 0; j < klsy.nhost; j++) {
        struct klsy_pe *h = &klsy.host[j]; int k = h->slot & (KST_N - 1); int dt = 0; float dx, dy, dz, hs;
        if (ksp_trk[k].ok && ksp_trk[k].slot == h->slot) {
            dt = (int)(T - ksp_trk[k].T0);
            if (dt >= 0 && dt < 40) continue;
            dx = h->p[0] - ksp_trk[k].p0[0]; dy = h->p[1] - ksp_trk[k].p0[1]; dz = h->p[2] - ksp_trk[k].p0[2];
            if (dt <= 0 || dt > 1000 || sqrt(dx * dx + dy * dy + dz * dz) > 1500.0) ksp_trk[k].v[0] = ksp_trk[k].v[1] = ksp_trk[k].v[2] = 0;
            else {
                ksp_trk[k].v[0] = dx * 1000.0f / dt; ksp_trk[k].v[1] = 0; ksp_trk[k].v[2] = dz * 1000.0f / dt;
                hs = (float)sqrt(ksp_trk[k].v[0] * ksp_trk[k].v[0] + ksp_trk[k].v[2] * ksp_trk[k].v[2]);
                if (hs > 900.0f) { ksp_trk[k].v[0] *= 900.0f / hs; ksp_trk[k].v[2] *= 900.0f / hs; }
            }
        } else ksp_trk[k].v[0] = ksp_trk[k].v[1] = ksp_trk[k].v[2] = 0;
        memcpy(ksp_trk[k].p0, h->p, 12); ksp_trk[k].T0 = T; ksp_trk[k].slot = h->slot; ksp_trk[k].ok = 1;
    }
}

/* object kinds listed after the actors (substring of the RTTI class name, case-folded; the exclusions drop scripts, which are not objects
   with a place). Doors, glass, money, vehicles, helicopters, loose physics bodies, thrown / picked-up things: what the owner called
   'any object'. Class names of the exe: re\bots_online_sync.md 5 (the RTTI list is in re\netcode.md; the probe prints what it finds). */
static const char *const klsy_kinds[] = { "moneycontainer", "kickdoor", "shatter", "havokcar", "heli", "animatedvehicle", "vehicleonspline", "rigidbody", "itemweapon", "pickup", "throwable", "grenade", 0 };
static const char *const klsy_skip[] = { "behaviour", "monitor", "trigger", "controller", "rout", "netsync", "sync", "settings", 0 };

static DWORD klsy_vt[64]; static signed char klsy_vk[64]; static char klsy_vn[64][40]; static int klsy_nvt;

/* class of a vtable: -1 unknown / not of interest, 0 = ZFFActor, 1.. = klsy_kinds index + 1; name in *nm */
static int klsy_class(DWORD vt, const char **nm)
{
    int i; DWORD col, td; char b[48], l[48]; const char *s;
    if ((ksp_ready && vt == (DWORD)(DWORD_PTR)ksp_vt) || (klh_actor_priv2 && vt == klh_actor_priv2)) vt = KSP_ACTOR_VT;                 /* a puppeted actor / a host bot with the OnlineCopToBot table */
    for (i = 0; i < klsy_nvt; i++) if (klsy_vt[i] == vt) { *nm = klsy_vn[i]; return klsy_vk[i]; }
    if (klsy_nvt >= 64) { *nm = "?"; return -1; }
    i = klsy_nvt++; klsy_vt[i] = vt; klsy_vk[i] = -1; strcpy(klsy_vn[i], "?");
    if ((col = klh_rd32(vt - 4)) && (td = klh_rd32(col + 0xc)) && klh_rdstr(td + 8, b, sizeof b)) {
        int j, k;
        s = b; if (!strncmp(s, ".?AV", 4)) s += 4;
        for (j = 0; s[j] && s[j] != '@' && j < 39; j++) klsy_vn[i][j] = s[j];
        klsy_vn[i][j] = 0;
        for (j = 0; klsy_vn[i][j] && j < 47; j++) l[j] = (char)tolower((unsigned char)klsy_vn[i][j]);
        l[j] = 0;
        if (vt == 0x00bb3bac) klsy_vk[i] = 0;
        else {
            for (k = 0; klsy_skip[k]; k++) if (strstr(l, klsy_skip[k])) break;
            if (!klsy_skip[k]) for (k = 0; klsy_kinds[k]; k++) if (strstr(l, klsy_kinds[k])) { klsy_vk[i] = (signed char)(k + 1); break; }
        }
    } else if (vt == 0x00bb3bac) { klsy_vk[i] = 0; strcpy(klsy_vn[i], "ZFFActor"); }
    *nm = klsy_vn[i];
    return klsy_vk[i];
}

static unsigned __int64 klsy_T(void)
{
    FILETIME ft; unsigned __int64 t; GetSystemTimeAsFileTime(&ft);
    t = ((unsigned __int64)ft.dwHighDateTime << 32 | ft.dwLowDateTime) / 10000;
    return t % 1000000000ULL;
}

/* One actor's reading, shared by the probe, the host broadcast and the comparison. */
static void klsy_actor(DWORD o, float pos[3], int *havepos, float *hp, int *team)
{
    DWORD pr, h; float hv[2] = { 0, 0 };
    *havepos = kle_node(klh_rd32(o + 4), pos, 0);
    h = klh_rd32(o + 0x5fc); *hp = (h && klh_rd(h + 4, hv, 8)) ? hv[0] : -1.0f;
    *team = ((pr = klh_rd32(o + 0x54)) && klh_rd(pr + 4, team, 4)) ? *team : -1;
}

/* klcrewlook.c (included after this file; klcl_on is klbotfill.c's): OnlineLooks=1, the host's look list 'KLSYL' */
static void klcl_rx(const char *pk, int len, DWORD now, unsigned long from);
static void klcl_send(DWORD sm, DWORD now);
/* kllootsync.c: OnlineLootSync=1, the host's bot loot list 'KLSYB' (klls_on is klbotfill.c's) */
static void klls_rx(const char *pk, int len, DWORD now, unsigned long from);
static int klls_send(DWORD now, int force);
/* klbotvoice.c: OnlineVoice, the host's bot event line 'KLSYV' (klbv_mode is klbotfill.c's) */
static void klbv_rx(const char *pk, int len, DWORD now, unsigned long from);
/* klgetupbeacon.c: OnlineGetUpBeacon, the downed machine's 'KLSYD' to the host (klgb_on is klbotfill.c's) */
static void klgb_host_rx(DWORD now);

static void klsy_open(void)
{
    HMODULE m; BYTE wsa[600]; klsy_sin a; int one = 1; unsigned long nb = 1;
    if (klsy.sock || klsy.sockTried) return;
    klsy.sockTried = 1;
    if (!(m = LoadLibraryA("ws2_32.dll"))) { klog("sync: ws2_32 not loadable: no host list channel"); return; }
    klsy.WSAStartup = (int (WINAPI *)(WORD, void *))GetProcAddress(m, "WSAStartup"); klsy.socket = (UINT_PTR (WINAPI *)(int, int, int))GetProcAddress(m, "socket");
    klsy.setsockopt = (int (WINAPI *)(UINT_PTR, int, int, const char *, int))GetProcAddress(m, "setsockopt"); klsy.bind = (int (WINAPI *)(UINT_PTR, const void *, int))GetProcAddress(m, "bind");
    klsy.sendto = (int (WINAPI *)(UINT_PTR, const char *, int, int, const void *, int))GetProcAddress(m, "sendto");
    klsy.recvfrom = (int (WINAPI *)(UINT_PTR, char *, int, int, void *, int *))GetProcAddress(m, "recvfrom"); klsy.ioctl = (int (WINAPI *)(UINT_PTR, long, unsigned long *))GetProcAddress(m, "ioctlsocket");
    if (!klsy.WSAStartup || !klsy.socket || !klsy.setsockopt || !klsy.bind || !klsy.sendto || !klsy.recvfrom || !klsy.ioctl) { klog("sync: ws2_32 functions missing: no host list channel"); return; }
    if (klsy.WSAStartup(0x0202, wsa)) { klog("sync: WSAStartup failed: no host list channel"); return; }
    klsy.sock = klsy.socket(2, 2, 17);
    if (klsy.sock == (UINT_PTR)~0) { klsy.sock = 0; klog("sync: socket() failed: no host list channel"); return; }
    klsy.setsockopt(klsy.sock, 0xffff, 0x0004 /* SO_REUSEADDR */, (const char *)&one, 4);
    klsy.setsockopt(klsy.sock, 0xffff, 0x0020 /* SO_BROADCAST */, (const char *)&one, 4);
    klsy.ioctl(klsy.sock, (long)0x8004667E /* FIONBIO */, &nb);
    memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((KLSY_PORT & 0xff) << 8) | (KLSY_PORT >> 8)); a.addr = 0;
    if (klsy.bind(klsy.sock, &a, sizeof a)) klog("sync: bind to UDP %d failed (a second game on this PC without SO_REUSEADDR?): send only", KLSY_PORT);
    else klog("sync: UDP %d open", KLSY_PORT);
}

/* The walk. pass 0 = actors, pass 1 = the other kinds. f(o, slot, kind, name, ctx) */
typedef void (*klsy_fn)(DWORD o, DWORD slot, int kind, const char *nm, void *ctx);
static void klsy_walk(int pass, klsy_fn f, void *ctx)
{
    DWORD p, tab, i, blk[64 * 32];
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return;
    for (i = 0; i < (klsy.lim ? (DWORD)klsy.lim : 0x10000u); i += 64) {                       /* lim: Apply / Compare stop past the host's highest slot */
        DWORD k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4], vt; const char *nm; int kind;
            if (o < 0x10000 || (vt = klh_rd32(o)) < 0x10000) continue;
            kind = klsy_class(vt, &nm);
            if (kind < 0 || (pass == 0) != (kind == 0)) continue;
            f(o, i + k, kind, nm, ctx);
        }
    }
}

struct klsy_pr { int n, max, lines; };
static int klsy_vanprobe = 1;      /* [Sync] VanProbe: with Probe, the van's real state/place next to the ZAnimatedVehicle line (log only) */
static void klsy_line(DWORD o, DWORD slot, int kind, const char *nm, void *ctx)
{
    struct klsy_pr *c = (struct klsy_pr *)ctx; float pos[3] = { 0, 0, 0 }, hp = -1; int hv = 0, team = -1; char ps[64];
    c->n++;
    if (c->lines >= c->max) return;
    if (kind == 0) klsy_actor(o, pos, &hv, &hp, &team); else hv = kle_node(klh_rd32(o + 4), pos, 0);
    if (hv) snprintf(ps, sizeof ps, "%.1f,%.1f,%.1f", pos[0], pos[1], pos[2]); else strcpy(ps, "none");
    /* f = flag: actors: byte [o+0x5cd] (read by 0x40ef60, meaning NOT established, GUESS: logged only to be compared between peers);
       other kinds: none yet (the first bench shows which kinds differ at all, then a state field is picked per kind) */
    if (kind == 0) { BYTE fl = 0; klh_rd(o + 0x5cd, &fl, 1); klog("sync: s=%lu c=%s t=%d p=%s hp=%.0f f=%02x", (unsigned long)slot, nm, team, ps, hp, fl); }
    else klog("sync: s=%lu c=%s t=- p=%s hp=- f=-", (unsigned long)slot, nm, ps);
    if (klsy_vanprobe && kind != 0 && !strcmp(nm, "ZAnimatedVehicle")) {      /* BO9: this object's node reads (0,0,0) all round; GUESS: the group [rules+0x1e4] / boarding object [rules+0x1e0] carry the place (klescort.c kle_veh_read) */
        DWORD s0 = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598)), hd, rules = 0, g, bo, nd; BYTE st = 0, b22 = 0; float gp[3] = { 0, 0, 0 }, bp[3] = { 0, 0, 0 }, h14 = -1; int gv = 0, bv = 0;
        if (s0 && klh_rd32(s0 + 0x5c) == 4 && (hd = klh_rd32((DWORD_PTR)KLH_VA(0x0168e9e4)))) rules = klh_rd32(hd + 0x54);      /* as klbotfill.c: the FA rules */
        klh_rd(o + 0x14, &h14, 4); klh_rd(o + 0x22, &b22, 1);
        if (rules) {
            klh_rd(rules + 0x1dc, &st, 1); g = klh_rd32(rules + 0x1e4); bo = klh_rd32(rules + 0x1e0);
            if (g && (nd = klh_rd32(g + 4))) gv = kle_node(nd, gp, 0);
            if (bo && (nd = klh_rd32(bo + 4))) bv = kle_node(nd, bp, 0);
            klog("sync: van probe: s=%lu state=%u +0x14=%.1f +0x22=%02x group %08lx %s(%.1f,%.1f,%.1f) boarding %08lx %s(%.1f,%.1f,%.1f)", (unsigned long)slot, st, h14, b22, g, gv ? "" : "NONE ", gp[0], gp[1], gp[2], bo, bv ? "" : "NONE ", bp[0], bp[1], bp[2]);
        } else klog("sync: van probe: s=%lu no FA rules object (+0x14=%.1f +0x22=%02x)", (unsigned long)slot, h14, b22);
    }
    c->lines++;
}

struct klsy_tx { char pk[16 + KLSY_MAXP * KLSY_REC]; int n; };
static void klsy_collect(DWORD o, DWORD slot, int kind, const char *nm, void *ctx)
{
    struct klsy_tx *t = (struct klsy_tx *)ctx; float pos[3]; int hv, team; float hp; struct klsy_pe e;
    (void)kind; (void)nm;
    if (t->n >= KLSY_MAXP) return;
    klsy_actor(o, pos, &hv, &hp, &team);
    if (!hv) return;
    e.slot = (unsigned short)slot; e.hp = (short)hp; memcpy(e.p, pos, 12);
    e.cls = (unsigned short)(klsy_vtof(o) & 0xffff); e.team = (short)team;
    memcpy(t->pk + 16 + t->n * KLSY_REC, &e, KLSY_REC); t->n++;
}

struct klsy_cm { int n, bad, hpbad, idbad, parked, worst_s; float worst; float wo[3], wh[3]; int shown; int awake, o150, o60, ndl, dlworst_s; float dlworst, dls[128]; };   /* dl* = CompareLead */
/* identity of the own actor against the host's record: same class (vtable low 16 bits) and the same, readable team */
static int klsy_idok(DWORD o, int team, const struct klsy_pe *h)
{
    return h->cls == (unsigned short)(klsy_vtof(o) & 0xffff) && team != -1 && h->team != -1 && h->team == (short)team;
}
static void klsy_cmp(DWORD o, DWORD slot, int kind, const char *nm, void *ctx)
{
    struct klsy_cm *c = (struct klsy_cm *)ctx; float pos[3], dx, dy, dz, d, hp; int hv, team, i;
    (void)kind; (void)nm;
    for (i = 0; i < klsy.nhost && klsy.host[i].slot != (unsigned short)slot; i++) ;
    if (i == klsy.nhost) return;
    klsy_actor(o, pos, &hv, &hp, &team);
    c->n++;
    if (!klsy_idok(o, team, &klsy.host[i])) { c->idbad++; return; }                  /* another actor in that slot: no position compare */
    if (!hv) return;
    {   DWORD nd = 0, fl = 0;   /* parked here (node off, bit 10, see ParkSkip): its place is not shown or synced, so no distance compare (SP1e: 12 "far" = parked) */
        if (klh_rd(o + 4, &nd, 4) && nd && klh_rd(nd + 0x3c, &fl, 4) && (fl >> 10 & 1)) { c->parked++; return; } }
    dx = pos[0] - klsy.host[i].p[0]; dy = pos[1] - klsy.host[i].p[1]; dz = pos[2] - klsy.host[i].p[2];
    d = (float)sqrt(dx * dx + dy * dy + dz * dz);
    if ((short)hp != klsy.host[i].hp) c->hpbad++;
    if (kst.cmpLead) {   /* the host's place moved on by the list age (no TrackLead): the stale compare shows 50..150 units for a perfect client (a cop runs 450..630 u/s, the list is 93..250 ms old) */
        float g[3], ex, ey, ez, dl; ksp_goal_at(i, GetTickCount(), 0, g);
        ex = pos[0] - g[0]; ey = pos[1] - g[1]; ez = pos[2] - g[2]; dl = (float)sqrt(ex * ex + ey * ey + ez * ez);
        c->awake++; if (dl > 150.0f) c->o150++; if (dl > 60.0f) c->o60++;
        if (c->ndl < 128) c->dls[c->ndl++] = dl;
        if (dl > c->dlworst) { c->dlworst = dl; c->dlworst_s = (int)slot; }
    }
    if (d > c->worst) { c->worst = d; c->worst_s = (int)slot; memcpy(c->wo, pos, 12); memcpy(c->wh, klsy.host[i].p, 12); }
    if (d * 10.0f > (float)klsy.tol10) {
        c->bad++;
        if (c->shown < 8) { c->shown++; klog("sync: vs host: slot %lu team %d d=%.1f me (%.1f,%.1f,%.1f) host (%.1f,%.1f,%.1f) hp me %.0f host %d", (unsigned long)slot, team, d, pos[0], pos[1], pos[2],
                                  klsy.host[i].p[0], klsy.host[i].p[1], klsy.host[i].p[2], hp, klsy.host[i].hp); }
    }
}

/* ---- [Sync] Apply (client): see the header ---- */
static int klsy_nhum; static DWORD klsy_humteam[28]; static float klsy_humpos[28][3];
/* The human players this peer's player list holds: their team objects ([player+0x54]) and feet ([player+0x460]) -> how many were found.
   GUESS: a human's body actor shares the player's [+0x54] team object or stands on the player's feet; either test keeps it out of Apply.
   GUESS (unverified): whether the list at gd+0x828 holds the REMOTE humans' players on a client; the pass logs the count so a bench shows it.
   The team match also keeps every actor of a heister team (AI heisters too) out of Apply when the team object is shared: intended, fail closed. */
static int klsy_humans(void)
{
    DWORD gd, pl; int i; klsy_nhum = 0;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(0x00dd265c)))) return 0;
    for (i = 0; i < 28; i++) {
        float f[3];
        if (!(pl = klh_rd32(gd + 0x828 + 4 * i)) || klh_pvt(pl) != 0x00bb45f4 /* ZFFPlayer */) continue;
        klsy_humteam[klsy_nhum] = klh_rd32(pl + 0x54);
        if (!klh_rd(pl + 0x460, f, 12)) f[0] = f[1] = f[2] = 1e30f;
        memcpy(klsy_humpos[klsy_nhum], f, 12); klsy_nhum++;
    }
    return klsy_nhum;
}
static int klsy_human(DWORD o, const float pos[3])
{
    DWORD tm = klh_rd32(o + 0x54); int i;
    if (klsy_nhum == 0) return 1;                                                  /* fail closed: no human known = nothing is moved */
    for (i = 0; i < klsy_nhum; i++) {
        float dx = pos[0] - klsy_humpos[i][0], dy = pos[1] - klsy_humpos[i][1], dz = pos[2] - klsy_humpos[i][2];
        if (tm && tm == klsy_humteam[i] && !(ksp.bots && klh_rd32(tm + 4) == 2)) return 1;      /* a team-Ally bot may share the team object with a human crew (GUESS): then only the 40-unit test below keeps the human's body out */
        if (dx * dx + dy * dy + dz * dz < 40.0f * 40.0f) return 1;                 /* GUESS: 40 units around a player's feet = his own body */
    }
    return 0;
}
static int klsy_isbad(DWORD slot)
{
    int i; for (i = 0; i < klsy.nbad; i++) if (klsy.bad[i] == slot) return 1;
    return 0;
}
struct klsy_off { DWORD o, slot; int hi, team; float d, pos[3], hp; const char *nm; };
struct klsy_ap { int seen, snapped, skipped, deadlog, hplog, refused, idbad, nOff; struct klsy_off off[KLSY_MAXOFF]; };
/* walk callback: only COLLECTS offenders (identity checked, not human, alive both sides, farther than ApplyTol) */
static void klsy_applyfn(DWORD o, DWORD slot, int kind, const char *nm, void *ctx)
{
    struct klsy_ap *c = (struct klsy_ap *)ctx; float pos[3], dx, dy, dz, d, hp; int hv, team, i;
    (void)kind;
    for (i = 0; i < klsy.nhost && klsy.host[i].slot != (unsigned short)slot; i++) ;
    if (i == klsy.nhost) return;
    klsy_actor(o, pos, &hv, &hp, &team);
    if (!klsy_idok(o, team, &klsy.host[i])) { c->idbad++; return; }               /* class / team differ: a different actor, never snapped */
    if (!hv) return;
    c->seen++;
    if (klsy_isbad(slot)) return;                                                 /* faulted in the teleport before */
    if (klsy_human(o, pos)) return;
    if (klsy.applyHp && (short)hp != klsy.host[i].hp && c->hplog < 8) { c->hplog++; klog("sync: apply: hp stub slot %lu c=%s me %.0f host %d (logged only)", (unsigned long)slot, nm, hp, klsy.host[i].hp); }
    if (klsy.host[i].hp <= 0) {                                                    /* host says dead */
        if (hp > 0 && c->deadlog < 4) { c->deadlog++; klog("sync: apply: slot %lu c=%s is dead on the host (hp %d), alive here (hp %.0f): NOT killed (log only)", (unsigned long)slot, nm, klsy.host[i].hp, hp); }
        return;
    }
    if (hp <= 0) return;                                                          /* dead here: a corpse is not moved */
    dx = pos[0] - klsy.host[i].p[0]; dy = pos[1] - klsy.host[i].p[1]; dz = pos[2] - klsy.host[i].p[2];
    d = (float)sqrt(dx * dx + dy * dy + dz * dz);
    if (d <= (float)klsy.applyTol) return;
    if (c->nOff >= KLSY_MAXOFF) { c->skipped++; return; }
    { struct klsy_off *f = &c->off[c->nOff++]; f->o = o; f->slot = slot; f->hi = i; f->team = team; f->d = d; f->hp = hp; f->nm = nm; memcpy(f->pos, pos, 12); }
}
/* after the walk (same tick, same thread): the worst ApplyMax offenders, farthest first */
static void klsy_applysnap(struct klsy_ap *c)
{
    int a, b, tried = 0; const char *why;
    for (a = 1; a < c->nOff; a++) { struct klsy_off t = c->off[a]; for (b = a - 1; b >= 0 && c->off[b].d < t.d; b--) c->off[b + 1] = c->off[b]; c->off[b + 1] = t; }
    if (c->nOff && !klt_tele_known()) { if (!klsy.toldApply) { klsy.toldApply = 1; klog("sync: apply: the game's teleport 0x62a900 is not the known routine: no snaps"); } return; }
    for (a = 0; a < c->nOff; a++) {
        struct klsy_off *f = &c->off[a]; float after[3], hp; int ok, hv, team;
        if (c->snapped >= klsy.applyMax) { c->skipped += c->nOff - a; break; }
        tried++;
        if ((why = klt_refuse(f->o)) != 0) { c->refused++; if (klsy.toldRefuse < 3) { klsy.toldRefuse++; klog("sync: apply: slot %lu c=%s NOT snapped: %s", (unsigned long)f->slot, f->nm, why); } continue; }
        ok = 1;
        __try { klt_teleport(f->o, klsy.host[f->hi].p); } __except (1) { ok = 0; }
        if (!ok) {                                                                 /* a fault may leave the actor half-moved: never touch that slot again this round */
            c->refused++; if (klsy.nbad < KLSY_NBAD) klsy.bad[klsy.nbad++] = f->slot;
            klog("sync: apply: slot %lu c=%s FAULT in the teleport: slot blacklisted for this round", (unsigned long)f->slot, f->nm);
            continue;
        }
        c->snapped++;
        memset(after, 0, sizeof after); klsy_actor(f->o, after, &hv, &hp, &team);
        klog("sync: apply: snap slot %lu c=%s t=%d dist %.1f (%.1f,%.1f,%.1f) -> host (%.1f,%.1f,%.1f) now (%.1f,%.1f,%.1f)", (unsigned long)f->slot, f->nm, f->team, f->d, f->pos[0], f->pos[1], f->pos[2],
             klsy.host[f->hi].p[0], klsy.host[f->hi].p[1], klsy.host[f->hi].p[2], after[0], after[1], after[2]);
    }
    (void)tried;
}

/* ---- [Sync] Puppet (client): the stock puppet steers a replicated cop by a velocity toward the replicated state; here the steer is re-issued each
   frame toward the HOST's place for the cops that stand farther than PuppetTol from it. Game thread only (the tick and the Update wrapper). ---- */
static int ksp_rx;

static void ksp_wr_vt(DWORD o, DWORD vt, const char *what) { klh_data((void *)(DWORD_PTR)o, &vt, 4, what); }

static struct ksp_e *ksp_find(DWORD o)
{
    int i; for (i = 0; i < KSP_MAXE; i++) if (ksp_e[i].o == o) return &ksp_e[i];
    return 0;
}

/* give an actor its stock vtable back (only if it still shows ours: freed memory is never written) and free the entry */
static void ksp_release(struct ksp_e *e, const char *why)
{
    if (klh_rd32(e->o) == ksp_ours()) ksp_wr_vt(e->o, KSP_ACTOR_VT, "ZFFActor vtable pointer (puppet release)");
    if (why) klog("sync: puppet: slot %lu released (%s) after %lu ms: %ld steers in %ld Update calls, %ld controller-mismatch, %ld stepped", (unsigned long)e->slot, why, (unsigned long)(GetTickCount() - e->since),
                  (long)e->steered, (long)e->calls, (long)e->mism, (long)e->stepped);
    memset(e, 0, sizeof *e); ksp.nlive--;
}
static void ksp_release_all(const char *why)
{
    int i; if (!ksp.nlive) return;
    for (i = 0; i < KSP_MAXE; i++) if (ksp_e[i].o) ksp_release(&ksp_e[i], why);
    ksp.nlive = 0;
}

/* the wrapper of ZFFActor slot 87: the stock Update first, then (only for an actor in the table with a fresh goal) the steer */
static void __fastcall ksp_update(void *self, void *edx)
{
    DWORD a = (DWORD)(DWORD_PTR)self; struct ksp_e *e;
    ((ksp_fn)(DWORD_PTR)ksp_orig)(self, edx);
    if (!ksp.pup || !(e = ksp_find(a))) return;
    e->calls++;
    if (GetTickCount() - e->goalAt > 1500) return;                                       /* no fresh host list: let the stock puppet be */
    __try {
        DWORD c = klh_rd32(a + 0x8e0), c2 = klh_rd32(a + 0x50c), ho = klh_rd32(a + 0x5fc); float pos[3], v[3], z[3] = { 0, 0, 0 }, dx, dz, h, sp, hpw; int mism;
        if (ho && klh_rd(ho + 4, &hpw, 4) && hpw <= 0) { e->dead = 1; return; }          /* dying / dead: never push it; the next pass releases it */
        mism = (!c || c != c2);
        if (mism) e->mism++;
        if (mism && ksp.mode != 1) return;                                              /* mode 2: the step cannot move the node (see the header), the placement is the pass's job */
        if (mism && !ksp.mode) return;                                                   /* PuppetMode 0: 0x70f660 would do nothing (cmp at 0x70f66a) */
        if (!kle_node(klh_rd32(a + 4), pos, 0)) return;
        if (mism) {                                                                      /* PuppetMode 1: bounded step by ZFFActor slot 373 (0x560de0), the call shape of the teleport at 0x62a95e */
            DWORD now = GetTickCount(), nd = klh_rd32(a + 4), fl3c = 0, dt = e->stepAt ? now - e->stepAt : 16; float d3, len, mx, s;
            if (!ksp_vt[373] || ksp_vt[373] != (DWORD)(DWORD_PTR)KLH_VA(0x560de0)) return;
            if (!nd || !klh_rd(nd + 0x3c, &fl3c, 4) || (fl3c >> 10 & 1)) return;        /* node off (flag bit 10): never */
            if (dt == 0) return;                                                         /* GetTickCount granularity: a zero-length call is pointless */
            if (dt > 100) dt = 100;                                                      /* a stall must not become a jump */
            e->stepAt = now;
            dx = e->goal[0] - pos[0]; v[1] = e->goal[1] - pos[1]; dz = e->goal[2] - pos[2];
            d3 = (float)sqrt(dx * dx + v[1] * v[1] + dz * dz);
            if (d3 < ksp.tol * 0.5f) return;
            mx = ksp.speed; if (e->hspeed * 1.25f > mx) mx = e->hspeed * 1.25f; if (mx > ksp.speed * 3.0f) mx = ksp.speed * 3.0f;
            len = mx * (dt / 1000.0f); if (len > d3) len = d3;
            s = len / d3; v[0] = pos[0] + dx * s; v[2] = pos[2] + dz * s; v[1] = pos[1] + v[1] * s;
            /* GUESS: slot 373 (thiscall, ret 0xc) is the actor's 'put at this place' with the two flags (1, 0) as 0x62a900 passes them: the argument is an ABSOLUTE
               place (it is stored at [A+0x460]); the meaning of the flags is not decoded; it returns at once when [A+0x8c] != 0 */
            ((void (__fastcall *)(void *, void *, const float *, int, int))(DWORD_PTR)ksp_vt[373])(self, 0, v, 1, 0);
            { float p2[3]; /* count a step only when the node really moved (slot 373 may return at once: [A+0x8c] != 0, node flags 0x40000 / 0x1000) */
              if (kle_node(klh_rd32(a + 4), p2, 0) && (fabsf(p2[0] - pos[0]) + fabsf(p2[1] - pos[1]) + fabsf(p2[2] - pos[2])) > 0.01f) { e->stepped++; ksp.nstep++; }
              else if (!e->nomove++) klog("sync: puppet: slot %lu: step call did not move the node ([A+0x8c]=%lu node flags=%08lx c=%08lx c2=%08lx)", (unsigned long)e->slot, (unsigned long)klh_rd32(a + 0x8c), (unsigned long)fl3c, (unsigned long)c, (unsigned long)c2); }
            return;
        }
        dx = e->goal[0] - pos[0]; dz = e->goal[2] - pos[2]; h = (float)sqrt(dx * dx + dz * dz);
        if (ksp.mode && h >= ksp.tol * 0.5f) {                                          /* PuppetMode 1, controller present: 0x70f660 takes a POSITION (static report 2026-10-26), not a velocity */
            if (klh_rd32(c) != 0xbb42ac) return;                                         /* only the puppet follower (ZFFFakePathFollower vtable) */
            ((ksp_steer_fn)(DWORD_PTR)KLH_VA(0x70f660))(self, 0, e->goal, z);          /* GUESS: (position, zero velocity); +0x1c = 1.0 lives 1 s as a time-to-live */
            e->steered++; ksp.nsteer++; return;
        }
        if (h < ksp.tol * 0.5f) return;                                                  /* (a pure vertical error is the pass's job: no-progress snap) */
        sp = ksp.speed;
        /* GUESS: a host cop running faster than PuppetSpeed needs a faster chase: 1.25 x its measured speed, at most 3 x PuppetSpeed */
        if (e->hspeed * 1.25f > sp) sp = e->hspeed * 1.25f;
        if (sp > ksp.speed * 3.0f) sp = ksp.speed * 3.0f;
        if (sp > h * 4.0f) sp = h * 4.0f;                                                /* slow down in the last quarter second */
        /* GUESS: x / z are the horizontal plane (Y up, as klnetsmooth.c), the first vector is a world velocity in units/s, the second (zero) an angular /
           secondary vector; 0x73f9f0 only stores them at controller+4..0xc and +0x10..0x18 and sets +0x1c = 1.0 */
        v[0] = dx / h * sp; v[1] = 0; v[2] = dz / h * sp;
        ((ksp_steer_fn)(DWORD_PTR)KLH_VA(0x70f660))(self, 0, v, z);
        e->steered++; ksp.nsteer++;
    } __except (1) { ksp.faults++; }
}

static int ksp_prepare(void)
{
    if (ksp_ready) return 1;
    if (!klh_rd((DWORD_PTR)KLH_VA(KSP_ACTOR_VT) - 4, ksp_vtblk, sizeof ksp_vtblk) || ksp_vt[KSP_SLOT] != (DWORD)(DWORD_PTR)KLH_VA(0x40ef60)) {
        klog("sync: puppet: ZFFActor slot %d is %08lx, not 0x40ef60: this build is not the one read - Puppet off", KSP_SLOT, (unsigned long)ksp_vt[KSP_SLOT]); ksp.pup = 0; return 0;
    }
    ksp_orig = ksp_vt[KSP_SLOT]; ksp_vt[KSP_SLOT] = (DWORD)(DWORD_PTR)ksp_update; ksp_ready = 1;
    klh_actor_priv = (DWORD)(DWORD_PTR)ksp_vt;                                          /* the other modules' ZFFActor tests (klh_avt) now see through it */
    klog("sync: puppet: private ZFFActor vtable ready (slot %d -> wrapper of 0x%lx)", KSP_SLOT, (unsigned long)ksp_orig);
    return 1;
}

/* a snap for a cop far beyond PuppetSnap: the game's teleport, with the stock vtable on for klt_refuse's class test */
static void ksp_snap(struct ksp_e *e, const char *nm, const float pos[3])
{
    const char *why; int ok = 1;
    if (!klt_tele_known()) { if (!ksp.toldNoCall) { ksp.toldNoCall = 1; klog("sync: puppet: the game's teleport 0x62a900 is not the known routine: no snaps"); } return; }
    ksp_wr_vt(e->o, KSP_ACTOR_VT, "ZFFActor vtable pointer (puppet snap)");
    if ((why = klt_refuse(e->o)) != 0) klog("sync: puppet: slot %lu c=%s NOT snapped: %s", (unsigned long)e->slot, nm, why);
    else { __try { klt_teleport(e->o, e->goal); } __except (1) { ok = 0; } }
    if (!why && !ok) klog("sync: puppet: slot %lu c=%s FAULT in the teleport", (unsigned long)e->slot, nm);
    else if (!why) { ksp.nsnap++; klog("sync: puppet: slot %lu c=%s SNAP %.1f units to (%.1f,%.1f,%.1f) from (%.1f,%.1f,%.1f)", (unsigned long)e->slot, nm, e->dlast, e->goal[0], e->goal[1], e->goal[2], pos[0], pos[1], pos[2]); }
    if (klh_rd32(e->o) == KSP_ACTOR_VT) ksp_wr_vt(e->o, ksp_ours(), "ZFFActor vtable pointer (puppet snap back)");
    e->lastSnap = GetTickCount();
}

/* Step 1 of the report, read-only: the fields that decide whether the stock steer runs (all offsets from the static reading, GUESS as to meaning) */
static void ksp_diag(DWORD a, DWORD slot, int team, float d)
{
    DWORD N = klh_rd32(a + 0x8d8), act = N ? klh_rd32(N + 0x2a0) : 0, own = N ? klh_rd32(N + 0x14) : 0, mv = klh_rd32(a + 0x8e0), mv2 = klh_rd32(a + 0x50c);
    DWORD p7 = klh_rd32(a + 0x7c0), x7c = p7 ? klh_rd32(p7 + 0x7c) : 0; float tg[3] = { 0, 0, 0 };
    if (N) klh_rd(N + 0x2ac, tg, 12);
    klog("sync: puppet diag: t+%lu ms slot %lu t=%d d=%.1f DO=%08lx DO.actor=%08lx%s DO.owner=%08lx ctl[+8e0]=%08lx ctl[+50c]=%08lx%s [[+7c0]+7c]=%08lx +90c=%08lx +918=%08lx DO.moveTo[+2ac]=(%g,%g,%g)",
         (unsigned long)(GetTickCount() - ksp.roundAt), (unsigned long)slot, team, d, (unsigned long)N, (unsigned long)act, act == a ? "(=self)" : "(NOT self)", (unsigned long)own, (unsigned long)mv, (unsigned long)mv2,
         mv == mv2 ? "(same)" : "(DIFFERENT: steer skipped)", (unsigned long)x7c, (unsigned long)klh_rd32(a + 0x90c), (unsigned long)klh_rd32(a + 0x918), tg[0], tg[1], tg[2]);
}

struct klsy_pp { int seen, started, steering, conv, diag, full, idbad, nearN, stepN, over, ph, snp, refd, pk; float stepSum, worst; };
/* PuppetMode 2: the game's own teleport 0x62a900 (klt_teleport, behind klt_tele_known + klt_refuse, as klauto.c's tele) for a cop farther than SnapDist from
   the host's place, at most once per SnapEvery ms per actor. A hooked cop (e) gets the stock vtable for klt_refuse's class test and its own back after. -> 1 = a placement was
   attempted (the caller stops there), 0 = not due / not possible. Never a player (klt_refuse wants the ZFFActor vtable; humans are filtered by the caller). */
static int ksp_snap2(DWORD o, DWORD slot, const char *nm, const float goal[3], float d, const float pos[3], struct ksp_e *e, DWORD now, struct klsy_pp *c)
{
    const char *why; int ok = 1, i, k = -1; float after[3], hp; int hv, tm;
    for (i = 0; i < 64; i++) { if (ksp_sn[i].o == o) { k = i; break; } if (k < 0 && !ksp_sn[i].o) k = i; }
    if (k < 0) { k = 0; for (i = 1; i < 64; i++) if ((int)(ksp_sn[k].at - ksp_sn[i].at) > 0) k = i; }
    if (ksp_sn[k].o == o && now - ksp_sn[k].at < ksp.snapEvery) return 0;
    if (klh_rd32(o) != (e ? ksp_ours() : KSP_ACTOR_VT)) return 0;                      /* not (any longer) a plain ZFFActor */
    if (!klt_tele_known()) { if (!ksp.toldNoCall) { ksp.toldNoCall = 1; klog("sync: puppet: the game's teleport 0x62a900 is not the known routine: no snaps"); } return 0; }
    ksp_sn[k].o = o; ksp_sn[k].at = now;
    if (e) ksp_wr_vt(o, KSP_ACTOR_VT, "ZFFActor vtable pointer (puppet snap2)");
    if ((why = klt_refuse(o)) != 0) { ksp.nref++; c->refd++; if (ksp.nref <= 6) klog("sync: puppet: slot %lu c=%s NOT snapped: %s", (unsigned long)slot, nm, why); }
    else { __try { klt_teleport(o, goal); } __except (1) { ok = 0; } }
    if (e && klh_rd32(o) == KSP_ACTOR_VT) ksp_wr_vt(o, ksp_ours(), "ZFFActor vtable pointer (puppet snap2 back)");
    if (why) return 1;
    if (!ok) { ksp.nflt++; if (klsy.nbad < KLSY_NBAD) klsy.bad[klsy.nbad++] = (DWORD)slot; klog("sync: puppet: slot %lu c=%s FAULT in the teleport: slot blacklisted for this round", (unsigned long)slot, nm); return 1; }
    ksp.nsn2++; c->snp++;
    memset(after, 0, sizeof after); klsy_actor(o, after, &hv, &hp, &tm);
    klog("sync: puppet: snap slot %lu d=%.1f -> (%.1f,%.1f,%.1f) (was (%.1f,%.1f,%.1f), now (%.1f,%.1f,%.1f))", (unsigned long)slot, d, goal[0], goal[1], goal[2], pos[0], pos[1], pos[2], after[0], after[1], after[2]);
    return 2;                                                                            /* 2 = really placed, 1 = refused / faulted (Track must not hook it on that) */
}

static int ksp_cooling(DWORD o, DWORD now) { int i; for (i = 0; i < 16; i++) if (ksp_cool[i].o == o && (int)(ksp_cool[i].until - now) > 0) return 1; return 0; }
static void ksp_setcool(DWORD o, DWORD now) { ksp_cool[ksp_coolN++ & 15].o = o; ksp_cool[(ksp_coolN - 1) & 15].until = now + 3000; }
/* SnapKeepHook: a snap of a HOOKED cop must keep the bookkeeping the pass would have done (SP1f: slot 565 snapped and released in the same millisecond, then a fresh START reset since / best / hspeed) */
static void ksp_keep(struct ksp_e *e, const float goal[3], float d, DWORD now)
{
    e->pass = ksp.pass; e->goalAt = now; e->lastSnap = now; memcpy(e->goal, goal, 12); e->dlast = d;
}

/* ---- Track: one placement of a hooked cop at 'g' (stock vtable on for klt_refuse's class test, ours back after) -> 1 placed, 0 refused / not possible, -1 fault ---- */
static int ksp_place(struct ksp_e *e, const float g[3])
{
    const char *why; int ok = 1;
    if (!klt_tele_known()) { if (!ksp.toldNoCall) { ksp.toldNoCall = 1; klog("sync: track: the game's teleport 0x62a900 is not the known routine: no placements"); } return 0; }
    ksp_wr_vt(e->o, KSP_ACTOR_VT, "ZFFActor vtable pointer (track)");
    if ((why = klt_refuse(e->o)) != 0) { kst.nref++; ok = 0; if (kst.nref <= 3) klog("sync: track: slot %lu NOT placed: %s", (unsigned long)e->slot, why); }
    else {
        float rot[12], *rp = 0; DWORD nd = klh_rd32(e->o + 4);
        if (kst.keepRot && nd && klh_rd(nd, rot, 36)) {                              /* GUESS: the node's own nine floats (+0) are the matrix the teleport reads; used only when they look like a rotation (unit rows) */
            float l0 = rot[0] * rot[0] + rot[1] * rot[1] + rot[2] * rot[2], l1 = rot[3] * rot[3] + rot[4] * rot[4] + rot[5] * rot[5], l2 = rot[6] * rot[6] + rot[7] * rot[7] + rot[8] * rot[8];
            rot[9] = rot[10] = rot[11] = 0;
            if (l0 > 0.9f && l0 < 1.1f && l1 > 0.9f && l1 < 1.1f && l2 > 0.9f && l2 < 1.1f) rp = rot;
        }
        __try { if (kst.local) klt_teleport_ex(e->o, g, rp, 0, 0); else klt_teleport_ex(e->o, g, rp, 1, 1); } __except (1) { ok = -1; }
    }
    if (klh_rd32(e->o) == KSP_ACTOR_VT) ksp_wr_vt(e->o, ksp_ours(), "ZFFActor vtable pointer (track back)");   /* else the class changed / freed mid-call: write nothing, ksp_pass drops the entry */
    if (ok == -1) { kst.nflt++; ksp.nflt++; if (klsy.nbad < KLSY_NBAD) klsy.bad[klsy.nbad++] = e->slot; klog("sync: track: slot %lu FAULT in the teleport: slot blacklisted for this round", (unsigned long)e->slot); return -1; }
    return ok;
}
/* the revert probe: after a placement the node is read back at the next frame and 100 ms later; moved more than 30 units = something put it back (second writer or the AI) */
static void ksp_rv_check(struct ksp_rv *r, DWORD now, const char *when)
{
    float p[3], dd, w[3] = { 0, 0, 0 }, nx = 1e30f, nz = 1e30f; DWORD a = r->o, vt50 = 0, c50 = klh_rd32(a + 0x50c); int netsnap;
    if (!kle_node(klh_rd32(a + 4), p, 0)) return;
    dd = (float)sqrt((p[0] - r->pl[0]) * (p[0] - r->pl[0]) + (p[2] - r->pl[2]) * (p[2] - r->pl[2]));   /* horizontal only (SP1g: the Y pops are the ground clamp) */
    { int k = r->slot & (KST_N - 1); float sp = 0, thr; if (ksp_trk[k].ok && ksp_trk[k].slot == r->slot) sp = (float)sqrt(ksp_trk[k].v[0] * ksp_trk[k].v[0] + ksp_trk[k].v[2] * ksp_trk[k].v[2]);
      thr = 30.0f + sp * (float)(int)(now - r->at) / 1000.0f;                                 /* a running cop legitimately moves speed x dt (review) */
      if (r->logged) return;
      if (dd <= thr) { if (fabsf(p[1] - r->pl[1]) > 30.0f) { r->logged = 1; kst.nrevY++; } return; }   /* y-only: counted apart, not a revert */
      r->logged = 1; kst.nrev++;
      /* revert cap: 3 reverts of one cop within 3 s hold the bound-follower skip for 3 s (the game's replication snap undoes a far placement) */
      if (!kst.rvN[k] || now - kst.rvAt0[k] > 3000) { kst.rvN[k] = 1; kst.rvAt0[k] = now; } else if (++kst.rvN[k] >= 3) { kst.bdHold[k] = now + 3000; kst.rvN[k] = 0; } }
    klh_rd(a + 0x90c, &nx, 4); klh_rd(a + 0x914, &nz, 4);
    netsnap = fabsf(p[0] - nx) < 1.0f && (fabsf(p[2] - nz) < 1.0f); if (netsnap) kst.nrevNet++;   /* GUESS: A+0x90c / A+0x914 = the received x / z (static report); A+0x918 is logged too */
    if (now - kst.rvLogAt < 250) return;                                                 /* rate limit: at most 4 lines a second, all counted in the summary */
    kst.rvLogAt = now; if (c50) vt50 = klh_rd32(c50);
    klh_rd(a + 0x460, w, 12);
    klog("sync: track: slot %lu reverted%s by %.0f in %lu ms (%s, %.0f u/s); node (%.1f,%.1f,%.1f) placed (%.1f,%.1f,%.1f) A+0x460 (%.1f,%.1f,%.1f) A+0x90c %08lx A+0x918 %08lx [A+0x8c]=%lu [A+0x50c] vt %08lx",
         (unsigned long)r->slot, netsnap ? " (netsnap)" : "", dd, (unsigned long)(now - r->at), when, (now - r->at) ? dd * 1000.0f / (now - r->at) : 0.0f, p[0], p[1], p[2], r->pl[0], r->pl[1], r->pl[2], w[0], w[1], w[2],
         (unsigned long)klh_rd32(a + 0x90c), (unsigned long)klh_rd32(a + 0x918), (unsigned long)klh_rd32(a + 0x8c), (unsigned long)vt50);
}
/* Track, every frame on the client (mode 4, gate OPEN, fresh list; the caller checks): each hooked cop farther than TrackTol from the extrapolated host place is placed there, at most
   TrackMax per frame and once per TrackMs per cop. Game thread. */
static void ksp_track(DWORD now)
{
    int j, jj, placed = 0, k; DWORD fr = ++kst.frame;
    for (k = 0; k < 16; k++) {
        struct ksp_rv *r = &ksp_rv[k];
        if (!r->o) continue;
        if (now - r->at > 600) { r->o = 0; continue; }
        if (r->stage == 0 && fr != r->frame) { ksp_rv_check(r, now, "next frame"); r->stage = 1; }
        if (r->stage == 1 && now - r->at >= 100) { ksp_rv_check(r, now, "+100 ms"); r->o = 0; }
    }
    if (!klsy_humans()) return;                                                          /* fail closed */
    for (jj = 0; jj < KSP_MAXE; jj++) {
        struct ksp_e *e; float pos[3], g[3], d, hpw = 1; DWORD nd, fl = 0, ho, c8, c5; int hi, r;
        if (placed >= kst.max) break;
        j = (kst.start + jj) % KSP_MAXE; e = &ksp_e[j];                                  /* round-robin start: no cop starves behind low indices */
        if (!e->o || klh_rd32(e->o) != ksp_ours()) continue;
        if (e->dead) { kst.ndead++; continue; }
        if (e->trkAt && (int)(now - e->trkAt) < (int)kst.ms) continue;                 /* signed: a back-off puts trkAt in the future */
        for (hi = 0; hi < klsy.nhost && klsy.host[hi].slot != (unsigned short)e->slot; hi++) ;
        if (hi == klsy.nhost) continue;
        if (ksp_ph[hi]) { kst.nph++; continue; }                                         /* a placeholder entry (several actors on one point) is never a goal */
        if (klsy_isbad(e->slot) || klsy.host[hi].hp <= 0) continue;
        nd = klh_rd32(e->o + 4);
        if (nd && klh_rd(nd + 0x3c, &fl, 4) && (fl >> 10 & 1)) { kst.npark++; continue; }   /* parked (node off): ParkSkip's job */
        if (!kle_node(nd, pos, 0)) continue;
        if ((ho = klh_rd32(e->o + 0x5fc)) != 0 && klh_rd(ho + 4, &hpw, 4) && hpw <= 0) { kst.ndead++; continue; }
        if (klsy_human(e->o, pos)) { kst.nhum++; continue; }
        ksp_goal_at(hi, now, kst.leadMs, g);
        if (kst.keepY && fabsf(g[1] - pos[1]) < kst.yTol) g[1] = pos[1];                 /* same floor: keep the cop's own y (the list age x vertical speed made a 30-110 unit pop) */
        if (klsy_human(e->o, g)) { kst.nhum++; continue; }                               /* the destination, too, is never next to a human */
        d = (float)sqrt((pos[0] - g[0]) * (pos[0] - g[0]) + (pos[1] - g[1]) * (pos[1] - g[1]) + (pos[2] - g[2]) * (pos[2] - g[2]));
        c8 = klh_rd32(e->o + 0x8e0); c5 = klh_rd32(e->o + 0x50c);
        if (!kst.ctl[e->slot & (KST_N - 1)]) { kst.ctl[e->slot & (KST_N - 1)] = 1;      /* controller class once per slot (B's pool-controller finding) */
            klog("sync: track: slot %lu controller [A+0x8e0]=%08lx (vt %08lx) [A+0x50c]=%08lx (vt %08lx)%s", (unsigned long)e->slot, (unsigned long)c8, (unsigned long)(c8 ? klh_rd32(c8) : 0), (unsigned long)c5, (unsigned long)(c5 ? klh_rd32(c5) : 0),
                 (c8 && c8 == c5) ? " bound" : " NOT bound (the stock steer is a no-op)"); }
        if (kst.bindFix && c8 && c8 != c5) {                                             /* BindFix (TEST, default off): make the gate [A+0x8e0]==[A+0x50c] hold */
            if (klh_data((void *)(DWORD_PTR)(e->o + 0x50c), &c8, 4, "actor: [A+0x50c] := [A+0x8e0] (BindFix)")) {
                kst.nbind++;
                if (!kst.bound1[e->slot & (KST_N - 1)]) { kst.bound1[e->slot & (KST_N - 1)] = 1; klog("sync: track: BindFix slot %lu [A+0x50c] %08lx -> %08lx", (unsigned long)e->slot, (unsigned long)c5, (unsigned long)c8); }
                c5 = c8;
            }
        }
        if (d < kst.tol) { kst.nclose++; kst.bdAt[e->slot & (KST_N - 1)] = 0; continue; }   /* back in tolerance: the stall timer restarts */
        if (!kst.bound && c8 && c8 == c5 && klh_rd32(c8) == 0xbb42ac && d < ksp.snapDist) {   /* a bound follower: the stock steer in the Update wrapper takes it while it is near */
            int sk = (int)(now - kst.bdHold[e->slot & (KST_N - 1)]) < 0 && kst.bdHold[e->slot & (KST_N - 1)];   /* held after 3 reverts */
            if (!sk && kst.stall) {                                                      /* SP1g slot 574: the steer is a no-op and the cop sat 230 units off for 25 s; skip only while it converges */
                int q = e->slot & (KST_N - 1);
                if (d < kst.boundDist) { kst.bdAt[q] = 0; sk = 1; }
                else if (!kst.bdAt[q] || d < kst.bdBest[q] - 15.0f) { kst.bdBest[q] = d; kst.bdAt[q] = now; sk = 1; }
                else if (now - kst.bdAt[q] < kst.stallMs) sk = 1;
                else { kst.nstall++; kst.bdAt[q] = 0; }                                  /* stalled: fall through to a placement */
            } else if (!sk) sk = 1;
            if (sk) { kst.nbound++; continue; }
        }
        e->trkAt = now;
        r = ksp_place(e, g);
        if (r <= 0) { e->trkAt = now + (r < 0 ? 5000 : 1500) - kst.ms; continue; }      /* refused / faulted: back off (not every 50 ms) */
        kst.start = j + 1;
        placed++; kst.nplace++; kst.errSum += d; if (d > kst.errMax) kst.errMax = d; e->lastSnap = now; e->dlast = d; memcpy(e->goal, g, 12); e->goalAt = now;                  /* the placed place, so the Update wrapper does not pull it back to the stale one */
        {   struct ksp_rv *rv = 0; int q;
            for (q = 0; q < 16; q++) if (!ksp_rv[q].o || ksp_rv[q].o == e->o) { rv = &ksp_rv[q]; break; }
            if (!rv) { rv = &ksp_rv[0]; for (q = 1; q < 16; q++) if ((int)(rv->at - ksp_rv[q].at) > 0) rv = &ksp_rv[q]; }
            rv->o = e->o; rv->slot = e->slot; rv->at = now; rv->frame = fr; rv->stage = 0; rv->logged = 0;
            if (!kle_node(klh_rd32(e->o + 4), rv->pl, 0)) memcpy(rv->pl, g, 12);
        }
    }
    kst.ntracked = ksp.nlive;
    if (now - kst.sumAt >= 5000) {
        if (kst.sumAt) {
            float dt = (now - kst.sumAt) / 1000.0f;
            klog("sync: track: %ld hooked, %ld placements (%.1f/s), error before placement mean %.0f max %.0f, refused %ld, faults %ld (total %ld); skipped: in tolerance %ld, bound followers %ld, parked %ld, human near %ld, placeholder %ld, dead %ld; reverts this round %ld (netsnap %ld, y-only %ld), bound stalls placed %ld, BindFix writes %ld",
                 (long)kst.ntracked, (long)kst.nplace, kst.nplace / dt, kst.nplace ? kst.errSum / kst.nplace : 0.0, kst.errMax, (long)kst.nref, (long)kst.nflt, (long)ksp.nflt, (long)kst.nclose, (long)kst.nbound, (long)kst.npark, (long)kst.nhum, (long)kst.nph, (long)kst.ndead, (long)kst.nrev, (long)kst.nrevNet, (long)kst.nrevY, (long)kst.nstall, (long)kst.nbind);
        }
        kst.sumAt = now; kst.nplace = kst.nref = kst.nflt = kst.nclose = kst.ndead = kst.npark = kst.nhum = kst.nph = kst.nbound = 0; kst.errSum = 0; kst.errMax = 0;
    }
}

static void klsy_pupfn(DWORD o, DWORD slot, int kind, const char *nm, void *ctx)
{
    struct klsy_pp *c = (struct klsy_pp *)ctx; float pos[3], dx, dy, dz, d, h, hp; int hv, team, i; struct ksp_e *e; DWORD now = GetTickCount();
    (void)kind;
    for (i = 0; i < klsy.nhost && klsy.host[i].slot != (unsigned short)slot; i++) ;
    if (i == klsy.nhost) return;
    klsy_actor(o, pos, &hv, &hp, &team);
    e = ksp_find(o);
    if (e && e->dead) { ksp_release(e, "dead (seen by the Update wrapper)"); return; }
    if (!klsy_idok(o, team, &klsy.host[i])) { c->idbad++; return; }
    /* only the cops' team (Puppet=1) and, with [BotFill] OnlineHost=1, the AI heisters = team Ally 2 (GUESS: the value 2 is the one klbotfill.c's census counts as 'Ally'; humans are not team 2 there) */
    if (!hv || !((ksp.cops && team == ksp.team) || (ksp.bots && team == 2))) return;
    /* fail closed: a human's body is never touched. A hooked cop that comes next to one is released quietly and not re-hooked for 3 s
       (time hysteresis instead of the 80-unit one: no flap of vtable writes and log lines at melee range) */
    if (klsy_human(o, pos)) { if (e) { ksp_release(e, 0); ksp_setcool(o, now); } return; }
    if (klsy_isbad(slot)) { if (e) ksp_release(e, 0); return; }
    if (hp <= 0 || klsy.host[i].hp <= 0) { if (e) ksp_release(e, "dead"); return; }
    dx = pos[0] - klsy.host[i].p[0]; dy = pos[1] - klsy.host[i].p[1]; dz = pos[2] - klsy.host[i].p[2];
    d = (float)sqrt(dx * dx + dy * dy + dz * dz); h = (float)sqrt(dx * dx + dz * dz);
    if (kspk.on) {
        /* ParkSkip (SP1d, workflow wovn0auy1): a cop whose node is off (bit 10, the bit klt_refuse refuses) is parked: invisible, no collision, so its offset
           does not show; the no-progress snap was refused every ~4 s for slots 563/565/765/773 and the puppet hook stepped it for nothing. Skip it (and leave it
           out of the position gate). When the bit clears (woken), snap it at once if it is farther than PuppetTol, under SnapDist too. Reads + the existing teleport.
           GUESS: the game parks spawn-pool / reserve cops this way (the code that sets 0x400 on them was not found). */
        DWORD nd = klh_rd32(o + 4), fl = 0; int pk = nd && klh_rd(nd + 0x3c, &fl, 4) && (fl >> 10 & 1), k, f = -1, was = 0;
        for (k = 0; k < 64; k++) { if (ksp_pk[k].o == o) { f = k; break; } if (f < 0 && !ksp_pk[k].o) f = k; }
        if (f < 0) f = (int)(slot & 63);
        if (ksp_pk[f].o == o) was = ksp_pk[f].pk;
        ksp_pk[f].o = o; ksp_pk[f].pk = (BYTE)pk;
        if (pk) { if (e) ksp_release(e, 0); c->pk++; kspk.npark++; return; }
        if (was && d > ksp.tol && ksp.pup && ksp.gate && !ksp_ph[i]) {
            int s;
            for (k = 0; k < 64; k++) if (ksp_sn[k].o == o) ksp_sn[k].at = now - ksp.snapEvery;   /* the woken snap is never held back by SnapEvery */
            s = ksp_snap2(o, slot, nm, klsy.host[i].p, d, pos, e, now, c);
            kspk.nwake++;
            klog("sync: puppet: slot %lu c=%s woken (node bit 10 cleared) %.1f from the host's place: %s", (unsigned long)slot, nm, d, s ? "snapped" : "snap not possible");
            if (s) { if (e) { e->bestAt = now; e->best = d; e->lastSnap = now; if (kst.keep) ksp_keep(e, klsy.host[i].p, d, now); } if (e || !kst.on || s == 1) return; }   /* Track: an unhooked woken cop falls through to the hook creation below */
        }
    }
    c->seen++;
    if (d < ksp.snap) c->nearN++;                                                        /* the positional sanity gate (slot numbers may differ per peer; the identity check cannot tell cop from cop) */
    if (ksp.mode >= 2 && d > ksp.snapDist) { int s2 = 0;                                           /* PuppetMode 2: place it at the host's position (alive both sides, not human: checked above) */
        c->over++; if (d > c->worst) c->worst = d;
        if (ksp_ph[i]) { c->ph++; ksp.nph++; }                                            /* a placeholder entry (several actors on one point): never a goal */
        else if (ksp.pup && ksp.gate && (s2 = ksp_snap2(o, slot, nm, klsy.host[i].p, d, pos, e, now, c)) != 0) { if (e) { e->bestAt = now; e->best = d; if (kst.keep) ksp_keep(e, klsy.host[i].p, d, now); } if (e || !kst.on || s2 == 1) return; }   /* Track: the first placement of an unhooked far cop; it is hooked below and tracked */
    }
    if (ksp.diag && c->diag < 8 && (ksp.pass == 1 || (d > ksp.tol && now - ksp.diagAt >= 3000))) { c->diag++; ksp_diag(o, slot, team, d); }
    if (!ksp.pup) return;
    if (d > ksp.tol || e) {
        if (!e) {
            int k;
            if (!ksp.gate || ksp_cooling(o, now)) return;                                /* the gate is from the previous pass: the first pass of a round only measures */
            for (k = 0; k < KSP_MAXE && ksp_e[k].o; k++) ;
            if (k == KSP_MAXE || klh_rd32(o) != KSP_ACTOR_VT || !ksp_prepare()) { c->full++; return; }
            e = &ksp_e[k]; memset(e, 0, sizeof *e); e->o = o; e->slot = slot; e->since = now; e->d0 = d; e->best = d; e->bestAt = now; ksp.nlive++;
            ksp_wr_vt(o, ksp_ours(), "ZFFActor vtable pointer (puppet)");
            c->started++;
            klog("sync: puppet: slot %lu c=%s t=%d START dist %.1f me (%.1f,%.1f,%.1f) goal (%.1f,%.1f,%.1f)", (unsigned long)slot, nm, team, d, pos[0], pos[1], pos[2], klsy.host[i].p[0], klsy.host[i].p[1], klsy.host[i].p[2]);
        }
        /* the host cop's own speed (horizontal, from consecutive lists, smoothed) scales the steer in the wrapper */
        if (e->prevAt && now - e->prevAt >= 100) {
            float sx = klsy.host[i].p[0] - e->prev[0], sz = klsy.host[i].p[2] - e->prev[2], sp = (float)sqrt(sx * sx + sz * sz) / ((now - e->prevAt) / 1000.0f);
            e->hspeed = e->hspeed == 0 ? sp : 0.5f * e->hspeed + 0.5f * sp; memcpy(e->prev, klsy.host[i].p, 12); e->prevAt = now;
        } else if (!e->prevAt) { memcpy(e->prev, klsy.host[i].p, 12); e->prevAt = now; }
        if (kst.on) ksp_goal_at(i, now, kst.leadMs, e->goal); else memcpy(e->goal, klsy.host[i].p, 12);   /* Track: the extrapolated place, as ksp_track places it */
        e->goalAt = now; e->dlast = d; e->pass = ksp.pass; c->steering++;
        if (ksp.mode && e->stepped) { c->stepN++; c->stepSum += d; }                    /* actors the mismatch step path moved: count and distance trend */
        if (kst.on) return;                                                              /* Track: ksp_track() places the hooked cop every frame; no CONVERGED release, no steer-first / no-progress snap (it stays hooked until dead / human / parked / gone from the list) */
        if (d > ksp.tol) {
            DWORD stuckMs;
            e->tolSince = 0;
            if (d < e->best - 5.0f) { e->best = d; e->bestAt = now; }
            stuckMs = h < ksp.tol * 0.5f ? 2000 : 4000;                                  /* a pure vertical error (wrong floor) is never steered: snap sooner */
            /* never on the first sighting: steer first (1.5 s) and let it prove it converges; then the teleport for a far cop or one that makes no progress */
            if (now - e->since >= 1500 && now - e->lastSnap >= 3000 && (d > ksp.snap || now - e->bestAt > stuckMs)) {
                if (d <= ksp.snap) klog("sync: puppet: slot %lu c=%s no progress for %lu ms (dist %.1f, best %.1f, horizontal %.1f): snap", (unsigned long)slot, nm, (unsigned long)(now - e->bestAt), d, e->best, h);
                ksp_snap(e, nm, pos); e->bestAt = now; e->best = d; return;
            }
            if (now - e->lastLog >= 2000) {
                e->lastLog = now;
                klog("sync: puppet: slot %lu c=%s goal (%.1f,%.1f,%.1f) dist %.1f (start %.1f, %lu ms ago, host speed %.0f): %ld steers in %ld Update calls, %ld controller-mismatch", (unsigned long)slot, nm, e->goal[0], e->goal[1], e->goal[2], d, e->d0,
                     (unsigned long)(now - e->since), e->hspeed, (long)e->steered, (long)e->calls, (long)e->mism);
                if (now - e->since > 2000 && e->calls == 0 && !ksp.toldNoCall) { klog("sync: puppet: slot %lu hooked for %lu ms but the Update wrapper never ran (the game calls 0x40ef60 directly?)", (unsigned long)slot, (unsigned long)(now - e->since)); }
            }
        } else {
            /* within tolerance: the hook (and the goal) stay while the host cop moves; released after 3 s of staying inside */
            if (!e->tolSince) e->tolSince = now;
            e->best = d; e->bestAt = now;
            if (now - e->tolSince >= 3000) { ksp.nconv++; klog("sync: puppet: slot %lu c=%s CONVERGED dist %.1f (start %.1f) in %lu ms", (unsigned long)slot, nm, d, e->d0, (unsigned long)(now - e->since)); c->conv++; ksp_release(e, 0); }
        }
    }
}

/* one pass (same tick, same thread as the game's frame loop) */
static void ksp_pass(void)
{
    struct klsy_pp c; int j, mx = 0, nh;
    nh = klsy_humans();
    if (!nh) { static int told; if (!told) { told = 1; klog("sync: puppet: no local player found: pass skipped (fail closed)"); } return; }
    for (j = 0; j < klsy.nhost; j++) if (klsy.host[j].slot > mx) mx = klsy.host[j].slot;
    memset(&c, 0, sizeof c); ksp.pass++;
    if (ksp.mode >= 2 || kst.on) ksp_mkph();
    for (j = 0; j < KSP_MAXE; j++) if (ksp_e[j].o && klh_rd32(ksp_e[j].o) != ksp_ours()) { memset(&ksp_e[j], 0, sizeof ksp_e[j]); ksp.nlive--; }      /* gone (freed): nothing is written */
    klsy.lim = (mx | 63) + 1;
    klsy_walk(0, klsy_pupfn, &c);
    klsy.lim = 0;
    /* positional sanity gate (review finding 1): at least ~60% of the cops must stand within PuppetSnap of the host record carrying their slot number;
       otherwise the slot numbers do not match on this peer and a cop would be steered to another cop's place */
    { int g = c.seen == 0 || c.nearN * 10 >= c.seen * 6;
      if (g != ksp.gate) { klog("sync: puppet: position gate %s (%d of %d cops within %.0f of the host's record with their slot number)", g ? "OPEN" : "CLOSED - no hooks", c.nearN, c.seen, ksp.snap); ksp.gate = g; }
      if (!g && ksp.nlive) ksp_release_all("slot numbers disagree with the host's list"); }
    for (j = 0; j < KSP_MAXE; j++) if (ksp_e[j].o && ksp_e[j].pass != ksp.pass) ksp_release(&ksp_e[j], "not seen this pass (dead, human, or gone from the host list)");
    if (c.diag) ksp.diagAt = GetTickCount();
    if (ksp.mode >= 2 && GetTickCount() - ksp.sumAt >= 5000) {
        ksp.sumAt = GetTickCount();
        klog("sync: puppet: snap summary: %d cops checked, %d farther than %.0f (worst %.1f), %d placeholder entries skipped, %d snapped this pass, %d parked (node off) skipped; totals %ld snaps %ld placeholder-skips %ld refused %ld faults %ld woken", c.seen, c.over, ksp.snapDist, c.worst, c.ph, c.snp, c.pk,
             (long)ksp.nsn2, (long)ksp.nph, (long)ksp.nref, (long)ksp.nflt, (long)kspk.nwake);
    }
    if (ksp.mode && c.stepN) {
        float avg = c.stepSum / c.stepN;
        if ((ksp.pass % 4) == 0) klog("sync: puppet: step path: %d mismatched-controller cops stepped (total %ld steps), mean distance %.1f (previous report %.1f: %s)", c.stepN, (long)ksp.nstep, avg, ksp.prevAvg,
                                      ksp.prevAvg == 0 ? "first" : avg < ksp.prevAvg - 1 ? "closing" : avg > ksp.prevAvg + 1 ? "OPENING" : "flat");
        if ((ksp.pass % 4) == 0) ksp.prevAvg = avg;
    }
    if (c.started || c.conv || c.full || (ksp.pass % 8) == 1)
        klog("sync: puppet: pass %lu: %d cops checked, %d steering, %d started, %d converged, %d table full / not hookable, %d another class/team; live %d; totals %ld steers %ld snaps %ld converged %d faults", (unsigned long)ksp.pass,
             c.seen, c.steering, c.started, c.conv, c.full, c.idbad, ksp.nlive, (long)ksp.nsteer, (long)ksp.nsnap, (long)ksp.nconv, ksp.faults);
    if (ksp.faults > 3) { klog("sync: puppet: %d faults in the steer: Puppet off", ksp.faults); ksp.pup = 0; ksp_release_all("faults"); }
}

/* ---- [Sync] PlayerProbe (2026-10-27, re\netcode_players_1027.md D3): the HUMAN bodies' place error. READ-ONLY. The actor walk above never sees them (a ZFFPlayer is
   not class 0), so nobody had a number for 'are the players where the host has them'. The host (PlayerProbe=1) broadcasts every ShareMs the session's player table
   ('KLSYP' u32 T u16 n u16 0, n x {u16 table index, u16 0, f32 x3}) on the same UDP port; the client (PlayerProbe=1) compares every REMOTE body of the same table index
   (its own, klcharonline's 'my body', is left out: its place is the client's own word) and logs every 5 s 'sync: players vs host: ...' with p50 / p90 / worst of the raw
   distance and of the lead-corrected one (the host place moved on by the list age at the speed of the last two lists). Table order = same index on every peer: the
   assumption klcharonline's looks rely on (proven on a client 10-26/27). GUESS: kle_node([ent+4]) is the body's place on every peer (the actors' reading). ---- */
#define KPL_N 16
#define KPL_S 512
struct kpl_rec { unsigned short idx, pad; float p[3]; };
typedef char kpl_rec_size_is_16[sizeof(struct kpl_rec) == 16 ? 1 : -1];
static struct {
    int on, n, pn, anch, nraw, nown, toldOwn, toldTbl, nl;
    DWORD shAt, rxAt, rxT, pT, cmpAt, sumAt, anchNow, anchT;
    struct kpl_rec h[KPL_N], pv[KPL_N];
    float raw[KPL_S], lead[KPL_S], last[KPL_N];
} kpl;
static void kpl_reset(void) { int on = kpl.on; memset(&kpl, 0, sizeof kpl); kpl.on = on; }
static void kpl_send(DWORD sm, DWORD now)
{
    char pk[16 + KPL_N * 16]; struct kpl_rec r; klsy_sin a; DWORD T = (DWORD)klsy_T(), ents = 0; WORD cnt = 0; int i, n = 0, hv, team; float hp;
    kpl.shAt = now;
    if (!klco_table(sm, &ents, &n)) n = 0;                                                 /* klcharonline.c's reader of the session's player table */
    for (i = 0; i < n && i < KPL_N; i++) {
        DWORD pl = klh_rd32(ents + 12 * i + 4);
        if (!pl) continue;
        memset(&r, 0, sizeof r); r.idx = (unsigned short)i;
        klsy_actor(pl, r.p, &hv, &hp, &team);
        if (!hv) continue;
        memcpy(pk + 16 + cnt * 16, &r, 16); cnt++;
    }
    memcpy(pk, "KLSYP\0\0\0", 8); memcpy(pk + 8, &T, 4); memcpy(pk + 12, &cnt, 2); pk[14] = pk[15] = 0;
    memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((KLSY_PORT & 0xff) << 8) | (KLSY_PORT >> 8)); a.addr = 0xffffffffu;
    i = klsy.sendto(klsy.sock, pk, 16 + cnt * 16, 0, &a, sizeof a);
    if (!kpl.toldTbl) { kpl.toldTbl = 1; klog("sync: players: host list %d of %d table bodies (sendto %d)", cnt, n, i); }
}
/* client: one 'KLSYP' packet (already checked for the source lock) */
static void kpl_rx(const char *pk, int len, DWORD now)
{
    WORD cnt; DWORD T;
    memcpy(&cnt, pk + 12, 2); if (cnt > KPL_N || 16 + cnt * 16 > len) return;
    memcpy(&T, pk + 8, 4);
    if (kpl.anch && T <= kpl.rxT && kpl.rxT - T < 500000000u) return;                       /* older / repeated (a huge step back = the 1e9 ms wrap) */
    if (!kpl.anch || T <= kpl.rxT || (int)(now - kpl.anchNow) - (int)(T - kpl.anchT) < 0) { kpl.anch = 1; kpl.anchNow = now; kpl.anchT = T; }
    /* anchor = the FASTEST list so far (GUESS: that one was on time). Q27_DD01m: anchoring on the first list (late, sent while loading) made every
       later list look early, the age stayed clamped at 0 and the lead correction did nothing. A client clock running faster than the host's is
       not caught (the age creeps up by ppm), which is fine for a 5 s probe. */
    if (kpl.n) { memcpy(kpl.pv, kpl.h, sizeof kpl.h); kpl.pn = kpl.n; kpl.pT = kpl.rxT; }
    memcpy(kpl.h, pk + 16, cnt * 16); kpl.n = cnt; kpl.rxT = T; kpl.rxAt = now;
}
static int kpl_fcmp(const void *a, const void *b) { float x = *(const float *)a, y = *(const float *)b; return x < y ? -1 : x > y; }
static void kpl_compare(DWORD sm, DWORD now)
{
    int j, n = 0, k; int age; DWORD dT, ents = 0;
    kpl.cmpAt = now;
    if (!kpl.n || now - kpl.rxAt > 1000 || !klco_table(sm, &ents, &n)) return;             /* no fresh host list / no player table here */
    age = (int)(now - kpl.anchNow) - (int)(kpl.rxT - kpl.anchT); if (age < 0) age = 0; if (age > 600) age = 600;
    dT = kpl.rxT - kpl.pT;
    if (klco.ownIdx < 0 && !kpl.toldOwn) { kpl.toldOwn = 1; klog("sync: players: my body is not known yet (klcharonline): every table body is compared, my own too"); }
    for (j = 0; j < kpl.n; j++) {
        const struct kpl_rec *h = &kpl.h[j]; DWORD pl; float pos[3], g[3], hp, dx, dy, dz, d, dl; int hv, team;
        if ((int)h->idx == klco.ownIdx) { kpl.nown++; continue; }
        if (h->idx >= n || !(pl = klh_rd32(ents + 12 * h->idx + 4))) continue;
        klsy_actor(pl, pos, &hv, &hp, &team);
        if (!hv) continue;
        memcpy(g, h->p, 12);
        if (kpl.pn && dT >= 50 && dT <= 1000)                                              /* lead: the host body's speed from the last two lists */
            for (k = 0; k < kpl.pn; k++) if (kpl.pv[k].idx == h->idx) {
                int a; for (a = 0; a < 3; a++) g[a] += (h->p[a] - kpl.pv[k].p[a]) * (float)age / (float)dT;
                break;
            }
        dx = pos[0] - h->p[0]; dy = pos[1] - h->p[1]; dz = pos[2] - h->p[2]; d = (float)sqrt(dx * dx + dy * dy + dz * dz);
        dx = pos[0] - g[0]; dy = pos[1] - g[1]; dz = pos[2] - g[2]; dl = (float)sqrt(dx * dx + dy * dy + dz * dz);
        if (kpl.nraw < KPL_S) { kpl.raw[kpl.nraw] = d; kpl.lead[kpl.nraw] = dl; kpl.nraw++; }
        if (h->idx < KPL_N && dl > kpl.last[h->idx]) kpl.last[h->idx] = dl;              /* per body: the worst lead-corrected gap of this 5 s window */
    }
    if (now - kpl.sumAt >= 5000 && kpl.nraw) {
        char per[160]; int m = kpl.nraw, o = 0;
        kpl.sumAt = now;
        qsort(kpl.raw, m, sizeof(float), kpl_fcmp); qsort(kpl.lead, m, sizeof(float), kpl_fcmp);
        per[0] = 0;
        for (j = 0; j < kpl.n && j < 8 && o < (int)sizeof per - 20; j++) if ((int)kpl.h[j].idx != klco.ownIdx && kpl.h[j].idx < KPL_N)
            o += snprintf(per + o, sizeof per - o, " i%u=%.0f", kpl.h[j].idx, kpl.last[kpl.h[j].idx]);
        klog("sync: players vs host: %d samples (own body i%d left out %d x), list %d ms old: raw p50 %.0f p90 %.0f worst %.0f | lead-corrected p50 %.0f p90 %.0f worst %.0f | worst per body:%s",
             m, klco.ownIdx, kpl.nown, age, kpl.raw[m / 2], kpl.raw[(m * 9) / 10 < m ? (m * 9) / 10 : m - 1], kpl.raw[m - 1],
             kpl.lead[m / 2], kpl.lead[(m * 9) / 10 < m ? (m * 9) / 10 : m - 1], kpl.lead[m - 1], per);
        kpl.nraw = 0; kpl.nown = 0; memset(kpl.last, 0, sizeof kpl.last);
    }
}

static void klsy_init(void)
{
    kpl.on = GetPrivateProfileIntA("Sync", "PlayerProbe", 0, klh_ini) != 0;               /* (recommended off: a measurement for benches, log only) */
    klsy.on = GetPrivateProfileIntA("Sync", "Probe", 0, klh_ini);
    klsy_vanprobe = GetPrivateProfileIntA("Sync", "VanProbe", 1, klh_ini) != 0;      /* (recommended on, log only; needs Probe) */
    klsy.share = GetPrivateProfileIntA("Sync", "Share", 0, klh_ini) != 0;
    klsy.cmp = GetPrivateProfileIntA("Sync", "Compare", 0, klh_ini) != 0;
    klsy.every = (DWORD)GetPrivateProfileIntA("Sync", "Every", 3000, klh_ini); if (klsy.every < 500) klsy.every = 500;
    klsy.shareMs = (DWORD)GetPrivateProfileIntA("Sync", "ShareMs", 250, klh_ini); if (klsy.shareMs < 100) klsy.shareMs = 100;
    klsy.max = GetPrivateProfileIntA("Sync", "Max", 700, klh_ini); if (klsy.max < 1) klsy.max = 1;
    klsy.tol10 = GetPrivateProfileIntA("Sync", "Tol", 10, klh_ini);      /* tenths of a unit: 10 = 1.0 */
    klsy.apply = GetPrivateProfileIntA("Sync", "Apply", 0, klh_ini) != 0;
    klsy.applyHp = GetPrivateProfileIntA("Sync", "ApplyHp", 0, klh_ini) != 0;
    klsy.applyMax = GetPrivateProfileIntA("Sync", "ApplyMax", 8, klh_ini); if (klsy.applyMax < 1) klsy.applyMax = 1;
    klsy.applyTol = GetPrivateProfileIntA("Sync", "ApplyTol", 150, klh_ini); if (klsy.applyTol < 1) klsy.applyTol = 1;
    ksp.cops = GetPrivateProfileIntA("Sync", "Puppet", 0, klh_ini) != 0;
    ksp.bots = klbf_oh;                                               /* [BotFill] OnlineHost (klbotfill.c is included and initialised before this file): host shares, client mirrors the Ally bots through the same Puppet code */
    ksp.pup = ksp.cops || ksp.bots;
    if (ksp.bots) klsy.share = 1;                                     /* the host's list is the bots' authority; a client never sends (role == 2 only) */
    ksp.diag = GetPrivateProfileIntA("Sync", "PuppetDiag", 0, klh_ini) != 0;
    ksp.tol = (float)GetPrivateProfileIntA("Sync", "PuppetTol", 60, klh_ini); if (ksp.tol < 5) ksp.tol = 5;
    ksp.snap = (float)GetPrivateProfileIntA("Sync", "PuppetSnap", 1500, klh_ini); if (ksp.snap < ksp.tol * 2) ksp.snap = ksp.tol * 2;
    ksp.speed = (float)GetPrivateProfileIntA("Sync", "PuppetSpeed", 300, klh_ini); if (ksp.speed < 1) ksp.speed = 1;
    ksp.team = GetPrivateProfileIntA("Sync", "PuppetTeam", 3, klh_ini);       /* GUESS: team value 3 = the cops (S2b measurement) */
    ksp.mode = GetPrivateProfileIntA("Sync", "PuppetMode", 1, klh_ini); if (ksp.mode < 0) ksp.mode = 0; if (ksp.mode > 2) ksp.mode = 2;
    ksp.snapDist = (float)GetPrivateProfileIntA("Sync", "SnapDist", 300, klh_ini); if (ksp.snapDist < ksp.tol) ksp.snapDist = ksp.tol;
    ksp.snapEvery = (DWORD)GetPrivateProfileIntA("Sync", "SnapEvery", 2000, klh_ini); if (ksp.snapEvery < 250) ksp.snapEvery = 250;  /* 0 = old behaviour; 1 = bounded step (slot 373) for mismatched controllers + 0x70f660 with a position (static report 2026-10-26) */
    kspk.on = GetPrivateProfileIntA("Sync", "ParkSkip", 1, klh_ini) != 0;
    kst.keep = GetPrivateProfileIntA("Sync", "SnapKeepHook", 1, klh_ini) != 0;
    kst.on = GetPrivateProfileIntA("Sync", "Track", 1, klh_ini) != 0;
    kst.ms = (DWORD)GetPrivateProfileIntA("Sync", "TrackMs", 50, klh_ini); if (kst.ms < 16) kst.ms = 16; if (kst.ms > 1000) kst.ms = 1000;
    kst.max = GetPrivateProfileIntA("Sync", "TrackMax", 8, klh_ini); if (kst.max < 1) kst.max = 1; if (kst.max > 32) kst.max = 32;
    kst.tol = (float)GetPrivateProfileIntA("Sync", "TrackTol", 40, klh_ini); if (kst.tol < 5) kst.tol = 5; if (kst.tol > 1000) kst.tol = 1000;
    kst.leadMs = (float)GetPrivateProfileIntA("Sync", "TrackLeadMs", 60, klh_ini); if (kst.leadMs < 0) kst.leadMs = 0; if (kst.leadMs > 300) kst.leadMs = 300;   /* GUESS: ~ one frame of placement lateness */
    kst.bound = GetPrivateProfileIntA("Sync", "TrackBound", 0, klh_ini) != 0;
    kst.stall = GetPrivateProfileIntA("Sync", "TrackBoundStall", 1, klh_ini) != 0;
    kst.boundDist = (float)GetPrivateProfileIntA("Sync", "TrackBoundDist", 100, klh_ini); if (kst.boundDist < 20) kst.boundDist = 20; if (kst.boundDist > 1000) kst.boundDist = 1000;   /* GUESS */
    kst.stallMs = (DWORD)GetPrivateProfileIntA("Sync", "TrackBoundStallMs", 1000, klh_ini); if (kst.stallMs < 250) kst.stallMs = 250; if (kst.stallMs > 10000) kst.stallMs = 10000;   /* GUESS */
    kst.keepY = GetPrivateProfileIntA("Sync", "TrackKeepY", 1, klh_ini) != 0;
    kst.yTol = (float)GetPrivateProfileIntA("Sync", "TrackYTol", 150, klh_ini); if (kst.yTol < 10) kst.yTol = 10; if (kst.yTol > 2000) kst.yTol = 2000;   /* GUESS: a floor is more than this apart */
    if (ksp.pup) klog("sync: TrackBoundStall=%d (a bound follower is skipped only while it converges; recommended on) TrackBoundDist=%.0f TrackBoundStallMs=%lu TrackKeepY=%d (recommended on) TrackYTol=%.0f", kst.stall, kst.boundDist, (unsigned long)kst.stallMs, kst.keepY, kst.yTol);
    kst.cmpLead = GetPrivateProfileIntA("Sync", "CompareLead", 1, klh_ini) != 0;
    kst.bindFix = GetPrivateProfileIntA("Sync", "BindFix", 0, klh_ini) != 0;
    kst.local = GetPrivateProfileIntA("Sync", "TrackLocal", 1, klh_ini) != 0;       /* placements with the teleport's two flags 0 (no animation reset, no net send); GUESS from klcrew_rt.c's reading of 0x62a900 */
    kst.keepRot = GetPrivateProfileIntA("Sync", "TrackKeepRot", 1, klh_ini) != 0;   /* GUESS: the actor node's nine floats at +0 have the layout the teleport reads */
    if (ksp.pup) klog("sync: SnapKeepHook=%d (a snapped hooked cop keeps its hook; recommended on) Track=%d (continuous placement at the extrapolated host place; recommended on) TrackMs=%lu TrackMax=%d TrackTol=%.0f TrackLeadMs=%.0f TrackBound=%d (recommended off) BindFix=%d (recommended off until measured) TrackLocal=%d (recommended on) TrackKeepRot=%d (recommended on)",
                      kst.keep, kst.on, (unsigned long)kst.ms, kst.max, kst.tol, kst.leadMs, kst.bound, kst.bindFix, kst.local, kst.keepRot);
    if (klsy.cmp || klsy.apply) klog("sync: CompareLead=%d (the 'vs host' line adds the lead-corrected distance; recommended on)", kst.cmpLead);
    if (ksp.pup) klog("sync: PuppetMode=%d SnapDist=%.0f SnapEvery=%lu ParkSkip=%d (parked cops skipped, snapped when woken; recommended on)", ksp.mode, ksp.snapDist, (unsigned long)ksp.snapEvery, kspk.on);
    if (ksp.bots) klog("sync: OnlineHost: bots (team 2) are mirrored by the Puppet code%s; this peer shares its list when it is the host", ksp.cops ? " together with the cops (Puppet=1)" : " (cops untouched: Puppet=0)");
    if (ksp.pup || ksp.diag) klog("sync: Puppet=%d PuppetDiag=%d PuppetTol=%.0f PuppetSnap=%.0f PuppetSpeed=%.0f PuppetTeam=%d (client only; needs the host's Share=1)%s", ksp.pup, ksp.diag, ksp.tol, ksp.snap, ksp.speed, ksp.team,
                                   (ksp.pup && klsy.apply) ? " WARNING: Apply=1 too: the two fight, use Puppet alone" : "");
    if (klsy.apply) klog("sync: Apply=1 ApplyHp=%d ApplyMax=%d ApplyTol=%d (client only: a non-player actor farther than ApplyTol from the host's is teleported to it)", klsy.applyHp, klsy.applyMax, klsy.applyTol);
    if (kpl.on) klog("sync: PlayerProbe=1 (read-only): the host sends its player table places, a client logs 'sync: players vs host' every 5 s");
    if (klsy.on || klsy.share || klsy.cmp)
        klog("sync: Probe=%d Share=%d Compare=%d Every=%lu ShareMs=%lu Max=%d Tol=%.1f (Probe / Share / Compare are read-only)", klsy.on, klsy.share, klsy.cmp, (unsigned long)klsy.every, (unsigned long)klsy.shareMs, klsy.max, klsy.tol10 / 10.0);
}

/* The round was left (loading, lobby, restart) or has not begun: forget everything received. */
static void klsy_leave(void) { klsy.inwin = 0; klsy.toldMode = 0; ksp_release_all("round left"); ksp_rx = 0; if (kpl.n || kpl.anch) kpl_reset(); }
/* Empty the socket (old rounds' / levels' lists queue there while the tick is out of the state window). */
static void klsy_drain(void)
{
    static char b[16 + KLSY_MAXP * KLSY_REC]; klsy_sin from; int fl, k;
    if (!klsy.sock) return;
    for (k = 0; k < 1024; k++) { fl = sizeof from; if (klsy.recvfrom(klsy.sock, b, sizeof b, 0, &from, &fl) < 0) break; }
}

static void klsy_tick(int game_thread)
{
    DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0;
    if (!(klsy.on || klsy.share || klsy.cmp || klsy.apply || ksp.pup || ksp.diag || kpl.on || klcl_on || klls_on || klbv_mode || klgb_on) || !game_thread || !klh_exe_ok) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) { klsy_leave(); return; }
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) { klsy_leave(); return; }
    if (klsy.on < 2 && ((role != 2 && role != 3) || mode != 4)) { klsy_leave(); return; }
    if (state < 0x13 || state > 0x1f) { klsy_leave(); return; }                /* in a round (botfill's window) */
    if ((klsy.share || klsy.cmp || klsy.apply || ksp.pup || ksp.diag || kpl.on || klcl_on || klls_on || klbv_mode || klgb_on) && !klsy.sock) klsy_open();
    if (!klsy.inwin) {                                                         /* entering the window: nothing from before this moment counts */
        klsy.inwin = 1; klsy_drain();
        klsy.nhost = 0; klsy.applyRx = 0; klsy.rxT = 0; klsy.rxAnchored = 0; klsy.srcSet = 0; klsy.agree = 0; klsy.nbad = 0;
        klsy.applyAt = 0; klsy.cmpAt = 0; klsy.toldHum = 0; klsy.humLogs = 0; klsy.toldRefuse = 0; kpl_reset();
        ksp_release_all("round start"); memset(ksp_trk, 0, sizeof ksp_trk); memset(ksp_rv, 0, sizeof ksp_rv); memset(kst.ctl, 0, sizeof kst.ctl); memset(kst.bound1, 0, sizeof kst.bound1); kst.nrev = kst.nbind = 0; kst.sumAt = 0; memset(ksp_pk, 0, sizeof ksp_pk); ksp_rx = 0; ksp.pass = 0; ksp.gate = 0; ksp.pupAt = 0; ksp.diagAt = 0; ksp.roundAt = now;
    }
    if (!klsy.toldMode) { klsy.toldMode = 1; klog("sync: round: role %lu state 0x%lx (probe %d, share %d, compare %d, apply %d)", (unsigned long)role, (unsigned long)state, klsy.on, klsy.share, klsy.cmp, klsy.apply); }
    if (klsy.share && role == 2 && klsy.sock && now - klsy.shAt >= klsy.shareMs) {          /* host: its actors, binary: 'KLSY2' u32 T u16 n, n x {u16 slot, i16 hp, f32 x3, u16 cls, i16 team} */
        struct klsy_tx *t = (struct klsy_tx *)calloc(1, sizeof *t);
        klsy.shAt = now;
        if (t) {
            klsy_sin a; DWORD T = (DWORD)klsy_T(); WORD cnt; int len, r;
            klsy_walk(0, klsy_collect, t);
            memcpy(t->pk, "KLSY2\0\0\0", 8); memcpy(t->pk + 8, &T, 4); cnt = (WORD)t->n; memcpy(t->pk + 12, &cnt, 2);
            len = 16 + t->n * KLSY_REC;
            memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((KLSY_PORT & 0xff) << 8) | (KLSY_PORT >> 8)); a.addr = 0xffffffffu;
            r = klsy.sendto(klsy.sock, t->pk, len, 0, &a, sizeof a);
            { static int told; if (!told) { told = 1; klog("sync: host list: %d actors, %d bytes on UDP %d (sendto %d)", t->n, len, KLSY_PORT, r); } }
            free(t);
        }
    }
    if (kpl.on && role == 2 && klsy.sock && now - kpl.shAt >= klsy.shareMs) kpl_send(sm, now);         /* PlayerProbe: the host's player table places */
    if (klls_on && role == 2 && klsy.sock) klls_send(now, 0);                                           /* OnlineLootSync=1: the host's bot loot list (kllootsync.c; its own schedule) */
    if (klgb_on && role == 2 && klsy.sock) klgb_host_rx(now);                                          /* OnlineGetUpBeacon=1: the downed machines' 'KLSYD' (klgetupbeacon.c) */
    if (klcl_on && role == 2 && klsy.sock) klcl_send(sm, now);                                        /* OnlineLooks=1: the host's look list (its own schedule) */
    if ((klsy.cmp || klsy.apply || ksp.pup || ksp.diag || kpl.on || klcl_on || klls_on || klbv_mode || klgb_on) && role == 3 && klsy.sock) {                                /* client: take the newest FRESH host list, compare once a second */
        static char pk[16 + KLSY_MAXP * KLSY_REC]; klsy_sin from; int fl, len, k;
        for (k = 0; k < 256; k++) {                                                            /* drain the whole queue; the newest acceptable list wins */
            WORD cnt; DWORD T; int age;
            fl = sizeof from; len = klsy.recvfrom(klsy.sock, pk, sizeof pk, 0, &from, &fl);
            if (len < 0) break;
            if (len >= 24 && !memcmp(pk, "KLSYL", 5)) { if (klcl_on) klcl_rx(pk, len, now, from.addr); continue; }      /* OnlineLooks=1: the host's look list */
            if (len >= 20 && !memcmp(pk, "KLSYV", 5)) { if (klbv_mode) klbv_rx(pk, len, now, from.addr); continue; }      /* OnlineVoice: the host's bot event line */
            if (len >= 28 && !memcmp(pk, "KLSYB", 5)) { if (klls_on) klls_rx(pk, len, now, from.addr); continue; }      /* OnlineLootSync=1: the host's bot loot list */
            if (!(klsy.cmp || klsy.apply || ksp.pup || ksp.diag || kpl.on)) continue;                                  /* OnlineLooks alone: no other list is used */
            if (len >= 16 && !memcmp(pk, "KLSYP", 5)) { if (kpl.on && (!klsy.srcSet || from.addr == klsy.srcAddr)) kpl_rx(pk, len, now); continue; }   /* PlayerProbe list */
            if (len < 16 || memcmp(pk, "KLSY2", 5)) continue;
            memcpy(&cnt, pk + 12, 2); if (cnt > KLSY_MAXP || 16 + cnt * KLSY_REC > len) continue;
            if (klsy.srcSet && from.addr != klsy.srcAddr) continue;                            /* only the first source that sent a valid list this round */
            memcpy(&T, pk + 8, 4);
            if (klsy.rxAnchored && T <= klsy.rxT) { if (klsy.rxT - T < 500000000u) continue; klsy.rxAnchored = 0; }   /* older / repeated: dropped; a huge step back = the 1e9 ms wrap */
            if (!klsy.rxAnchored) { klsy.rxAnchored = 1; klsy.anchorNow = now; klsy.anchorT = T; }
            age = (int)(now - klsy.anchorNow) - (int)(T - klsy.anchorT);                       /* how long this list sat on the way, by the HOST's clock (GUESS: the fastest list was on time) */
            if (age < 0) { klsy.anchorNow = now; klsy.anchorT = T; age = 0; }                  /* faster than the anchor: re-anchor (a late first list made every later one look early: age 0, no lead; PlayerProbe Q27_DD01m) */
            if (age > (int)(2 * klsy.shareMs)) continue;
            if (!klsy.srcSet) { klsy.srcSet = 1; klsy.srcAddr = from.addr; klog("sync: host list source locked to %lu.%lu.%lu.%lu", from.addr & 255, from.addr >> 8 & 255, from.addr >> 16 & 255, from.addr >> 24); }
            memcpy(klsy.host, pk + 16, cnt * KLSY_REC); klsy.nhost = cnt; klsy.rxT = T; klsy.rxAt = now; klsy.applyRx = 1; ksp_rx = 1; klsy.rxAge = age < 0 ? 0 : age;
            if (ksp.mode >= 2 || kst.on) ksp_mkph();
            if (kst.on || kst.cmpLead) ksp_trk_feed(T);
        }
        if (ksp.nlive && now - klsy.rxAt > 3000) ksp_release_all("host list stale");                 /* the host's packets stopped: give every vtable back */
        if (kpl.on && now - kpl.cmpAt >= 1000) kpl_compare(sm, now);                            /* PlayerProbe: remote bodies vs the host's places, once a second */
        if ((klsy.cmp || klsy.apply || ksp.pup || ksp.diag) && klsy.nhost && now - klsy.cmpAt >= 1000) {            /* the Compare walk also gives Apply its trust: identity agreement */
            struct klsy_cm c; int j, mx = 0, ag; klsy.cmpAt = now; memset(&c, 0, sizeof c); c.worst_s = -1;
            for (j = 0; j < klsy.nhost; j++) if (klsy.host[j].slot > mx) mx = klsy.host[j].slot;
            klsy.lim = (mx | 63) + 1;
            klsy_walk(0, klsy_cmp, &c);
            klsy.lim = 0;
            ag = c.n >= 1 && c.idbad * 10 <= c.n;                                              /* GUESS: at most 10% of the shared slots may differ in class / team */
            if (ag != klsy.agree) { klsy.agree = ag; klog("sync: identity agreement with the host %s (%d slots compared, %d with another class / team)", ag ? "OK" : "LOST", c.n, c.idbad); }
            if (klsy.cmp)
            {   char ld[200]; ld[0] = 0;
                if (kst.cmpLead) {                                                             /* CompareLead: the lead-corrected distance (the host place extrapolated by the list age) of the awake cops */
                    int a, b; for (a = 1; a < c.ndl; a++) { float t = c.dls[a]; for (b = a - 1; b >= 0 && c.dls[b] > t; b--) c.dls[b + 1] = c.dls[b]; c.dls[b + 1] = t; }
                    snprintf(ld, sizeof ld, " | lead-corrected: awake %d, >150: %d, >60: %d, p50 %.0f p90 %.0f worst %.0f (slot %d)", c.awake, c.o150, c.o60, c.ndl ? c.dls[c.ndl / 2] : 0.0f, c.ndl ? c.dls[(c.ndl * 9) / 10 < c.ndl ? (c.ndl * 9) / 10 : c.ndl - 1] : 0.0f, c.dlworst, c.dlworst_s);
                }
                klog("sync: vs host: %d actors compared (host list %lu ms old, %d in it), %d another class/team, %d parked here (not compared), %d farther than %.1f, %d with another health, worst slot %d d=%.1f%s", c.n,
                     (unsigned long)(now - klsy.rxAt), klsy.nhost, c.idbad, c.parked, c.bad, klsy.tol10 / 10.0, c.hpbad, c.worst_s, c.worst, ld); }
        }
        /* Apply: only a System Link / online client (mode 4, even with Probe=2), a fresh list, the identity agreement, a known local player; at most 2 passes a second */
        if (klsy.apply && mode == 4 && klsy.agree && klsy.applyRx && klsy.nhost && now - klsy.rxAt <= 2 * klsy.shareMs && now - klsy.applyAt >= 500) {
            struct klsy_ap *c = (struct klsy_ap *)calloc(1, sizeof *c); int j, mx = 0, nh;
            klsy.applyRx = 0; klsy.applyAt = now;
            nh = klsy_humans();
            if (klsy.humLogs < 3) { klsy.humLogs++; klog("sync: apply: pass: %d local ZFFPlayer(s) in the list at gd+0x828 (does it hold remote humans? compare with the number of humans in the round)", nh); }
            if (!nh) { if (!klsy.toldHum) { klsy.toldHum = 1; klog("sync: apply: no local player found: pass skipped (fail closed)"); } }
            else if (c) {
                for (j = 0; j < klsy.nhost; j++) if (klsy.host[j].slot > mx) mx = klsy.host[j].slot;
                klsy.lim = (mx | 63) + 1;
                klsy_walk(0, klsy_applyfn, c);
                klsy.lim = 0;
                klsy_applysnap(c);
                if (c->snapped || c->skipped || c->refused || c->idbad) klog("sync: apply: %d actors checked, %d snapped, %d over the ApplyMax cap, %d refused / faulted, %d another class/team", c->seen, c->snapped, c->skipped, c->refused, c->idbad);
            }
            free(c);
        }
        /* Puppet / PuppetDiag: same trust as Apply (System Link / online client, fresh list, identity agreement), up to 4 passes a second */
        if ((ksp.pup || ksp.diag) && mode == 4 && klsy.agree && ksp_rx && klsy.nhost && now - klsy.rxAt <= 2 * klsy.shareMs && now - ksp.pupAt >= 250) {
            ksp_rx = 0; ksp.pupAt = now;
            ksp_pass();
        }
        /* Track: every frame, same trust as the Puppet pass plus the open position gate and a fresh list */
        if (kst.on && ksp.pup && mode == 4 && klsy.agree && ksp.gate && ksp.nlive && klsy.nhost && now - klsy.rxAt <= 2 * klsy.shareMs) ksp_track(now);
    }
    if (klsy.on && now - klsy.at >= klsy.every) {
        struct klsy_pr c; klsy.at = now; c.n = 0; c.max = klsy.max; c.lines = 0;
        klog("sync: list T=%I64u role %lu state 0x%lx", klsy_T(), (unsigned long)role, (unsigned long)state);
        klsy_walk(0, klsy_line, &c);
        klsy_walk(1, klsy_line, &c);
        klog("sync: list end: %d objects of interest, %d lines", c.n, c.lines);
    }
}

#endif /* KLSYNC_C */
