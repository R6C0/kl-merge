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
 *   [Sync] Puppet=1  (CLIENT only, default 0, needs the host's Share=1; use it INSTEAD of Apply) 2026-10-26, from the static report on kl2.exe 0490. The stock client
 *                    cop is a velocity-steered puppet (ZFFActor::Update slot 87 = 0x40ef60 -> 0x899c40 -> 0x8efe90 steer through 0x70f660(A, &vel, &zero) into the
 *                    movement controller [A+0x8e0], active only while [A+0x8e0] == [A+0x50c]). A cop of team PuppetTeam (3) that is farther than PuppetTol (60)
 *                    from the host's place gets a PRIVATE copy of the ZFFActor vtable (as klnetsmooth.c does for players) whose slot 87 runs the stock Update and then
 *                    calls the same 0x70f660 with a horizontal velocity of PuppetSpeed (300 units/s, slowing in the last quarter second) toward the host's place:
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
#define KSP_MAXE 48
typedef void (__fastcall *ksp_fn)(void *self, void *edx);
typedef void (__fastcall *ksp_steer_fn)(void *self, void *edx, const float *vel, const float *zero);
static DWORD ksp_vtblk[KSP_NSLOT + 1];                 /* [0] = the stock vt[-1] (RTTI locator), then the private copy */
#define ksp_vt (ksp_vtblk + 1)
static DWORD ksp_orig; static int ksp_ready;
struct ksp_e { DWORD o, slot, goalAt, since, lastLog, lastSnap, pass; int inTol; float goal[3], d0, dlast; volatile LONG calls, steered, mism; };
static struct ksp_e ksp_e[KSP_MAXE];
static struct { int pup, diag, nlive; float tol, snap, speed; int team; DWORD pass, roundAt, diagAt, pupAt; int faults, toldMism, toldNoCall; LONG nsteer, nsnap, nconv; } ksp;
static DWORD ksp_ours(void) { return ksp_ready ? (DWORD)(DWORD_PTR)ksp_vt : 0; }
/* the class vtable of an actor as the rest of this file means it: a puppeted actor shows our private table, which is still a ZFFActor */
static DWORD klsy_vtof(DWORD o)
{
    DWORD v = klh_rd32(o);
    return (ksp_ready && v == (DWORD)(DWORD_PTR)ksp_vt) ? KSP_ACTOR_VT : v;
}
#define KLSY_REC 20
#define KLSY_NBAD 16
#define KLSY_MAXOFF 128
static struct {
    int on, share, cmp, max, tol10, apply, applyHp, applyMax, applyTol, toldApply, toldRefuse, toldHum, applyRx;
    int inwin, agree, rxAnchored, srcSet, lim, nbad, humLogs;
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
    if (ksp_ready && vt == (DWORD)(DWORD_PTR)ksp_vt) vt = KSP_ACTOR_VT;                 /* a puppeted actor */
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

struct klsy_cm { int n, bad, hpbad, idbad, worst_s; float worst; float wo[3], wh[3]; int shown; };
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
    dx = pos[0] - klsy.host[i].p[0]; dy = pos[1] - klsy.host[i].p[1]; dz = pos[2] - klsy.host[i].p[2];
    d = (float)sqrt(dx * dx + dy * dy + dz * dz);
    if ((short)hp != klsy.host[i].hp) c->hpbad++;
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
        if (!(pl = klh_rd32(gd + 0x828 + 4 * i)) || klh_rd32(pl) != 0x00bb45f4 /* ZFFPlayer */) continue;
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
        if (tm && tm == klsy_humteam[i]) return 1;
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
    if (why) klog("sync: puppet: slot %lu released (%s) after %lu ms: %ld steers in %ld Update calls, %ld controller-mismatch", (unsigned long)e->slot, why, (unsigned long)(GetTickCount() - e->since),
                  (long)e->steered, (long)e->calls, (long)e->mism);
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
        DWORD c = klh_rd32(a + 0x8e0), c2 = klh_rd32(a + 0x50c); float pos[3], v[3], z[3] = { 0, 0, 0 }, dx, dz, h, sp;
        if (!c || c != c2) { e->mism++; return; }                                        /* 0x70f660 would do nothing (cmp at 0x70f66a) */
        if (!kle_node(klh_rd32(a + 4), pos, 0)) return;
        dx = e->goal[0] - pos[0]; dz = e->goal[2] - pos[2]; h = (float)sqrt(dx * dx + dz * dz);
        if (h < ksp.tol * 0.5f) return;
        sp = ksp.speed; if (sp > h * 4.0f) sp = h * 4.0f;                                /* slow down in the last quarter second */
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
    ksp_wr_vt(e->o, ksp_ours(), "ZFFActor vtable pointer (puppet snap back)");
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

struct klsy_pp { int seen, started, steering, conv, diag, full, idbad; };
static void klsy_pupfn(DWORD o, DWORD slot, int kind, const char *nm, void *ctx)
{
    struct klsy_pp *c = (struct klsy_pp *)ctx; float pos[3], dx, dy, dz, d, hp; int hv, team, i; struct ksp_e *e; DWORD now = GetTickCount();
    (void)kind;
    for (i = 0; i < klsy.nhost && klsy.host[i].slot != (unsigned short)slot; i++) ;
    if (i == klsy.nhost) return;
    klsy_actor(o, pos, &hv, &hp, &team);
    if (!klsy_idok(o, team, &klsy.host[i])) { c->idbad++; return; }
    if (!hv || team != ksp.team) return;                                                 /* only the cops' team */
    if (klsy_human(o, pos)) return;                                                      /* fail closed: a human's body is never touched */
    if (klsy_isbad(slot)) return;
    e = ksp_find(o);
    if (hp <= 0 || klsy.host[i].hp <= 0) { if (e) ksp_release(e, "dead"); return; }
    c->seen++;
    dx = pos[0] - klsy.host[i].p[0]; dy = pos[1] - klsy.host[i].p[1]; dz = pos[2] - klsy.host[i].p[2];
    d = (float)sqrt(dx * dx + dy * dy + dz * dz);
    if (ksp.diag && c->diag < 8 && (ksp.pass == 1 || (d > ksp.tol && now - ksp.diagAt >= 3000))) { c->diag++; ksp_diag(o, slot, team, d); }
    if (!ksp.pup) return;
    if (d > ksp.tol) {
        if (!e) {
            int k; for (k = 0; k < KSP_MAXE && ksp_e[k].o; k++) ;
            if (k == KSP_MAXE || klh_rd32(o) != KSP_ACTOR_VT || !ksp_prepare()) { c->full++; return; }
            e = &ksp_e[k]; memset(e, 0, sizeof *e); e->o = o; e->slot = slot; e->since = now; e->d0 = d; ksp.nlive++;
            ksp_wr_vt(o, ksp_ours(), "ZFFActor vtable pointer (puppet)");
            c->started++;
            klog("sync: puppet: slot %lu c=%s t=%d START dist %.1f me (%.1f,%.1f,%.1f) goal (%.1f,%.1f,%.1f)", (unsigned long)slot, nm, team, d, pos[0], pos[1], pos[2], klsy.host[i].p[0], klsy.host[i].p[1], klsy.host[i].p[2]);
        }
        memcpy(e->goal, klsy.host[i].p, 12); e->goalAt = now; e->inTol = 0; e->dlast = d; e->pass = ksp.pass; c->steering++;
        if (d > ksp.snap && now - e->lastSnap >= 3000) { ksp_snap(e, nm, pos); return; }
        if (now - e->lastLog >= 2000) {
            e->lastLog = now;
            klog("sync: puppet: slot %lu c=%s goal (%.1f,%.1f,%.1f) dist %.1f (start %.1f, %lu ms ago): %ld steers in %ld Update calls, %ld controller-mismatch", (unsigned long)slot, nm, e->goal[0], e->goal[1], e->goal[2], d, e->d0,
                 (unsigned long)(now - e->since), (long)e->steered, (long)e->calls, (long)e->mism);
            if (now - e->since > 2000 && e->calls == 0 && !ksp.toldNoCall) { klog("sync: puppet: slot %lu hooked for %lu ms but the Update wrapper never ran (the game calls 0x40ef60 directly?)", (unsigned long)slot, (unsigned long)(now - e->since)); }
        }
    } else if (e) {
        e->pass = ksp.pass; e->dlast = d;
        if (++e->inTol >= 4) { ksp.nconv++; klog("sync: puppet: slot %lu c=%s CONVERGED dist %.1f (start %.1f) in %lu ms", (unsigned long)slot, nm, d, e->d0, (unsigned long)(now - e->since)); c->conv++; ksp_release(e, 0); }
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
    for (j = 0; j < KSP_MAXE; j++) if (ksp_e[j].o && klh_rd32(ksp_e[j].o) != ksp_ours()) { memset(&ksp_e[j], 0, sizeof ksp_e[j]); ksp.nlive--; }      /* gone (freed): nothing is written */
    klsy.lim = (mx | 63) + 1;
    klsy_walk(0, klsy_pupfn, &c);
    klsy.lim = 0;
    for (j = 0; j < KSP_MAXE; j++) if (ksp_e[j].o && ksp_e[j].pass != ksp.pass) ksp_release(&ksp_e[j], "not seen this pass (dead, human, or gone from the host list)");
    if (c.diag) ksp.diagAt = GetTickCount();
    if (c.started || c.conv || c.full || (ksp.pass % 8) == 1)
        klog("sync: puppet: pass %lu: %d cops checked, %d steering, %d started, %d converged, %d table full / not hookable, %d another class/team; live %d; totals %ld steers %ld snaps %ld converged %d faults", (unsigned long)ksp.pass,
             c.seen, c.steering, c.started, c.conv, c.full, c.idbad, ksp.nlive, (long)ksp.nsteer, (long)ksp.nsnap, (long)ksp.nconv, ksp.faults);
    if (ksp.faults > 3) { klog("sync: puppet: %d faults in the steer: Puppet off", ksp.faults); ksp.pup = 0; ksp_release_all("faults"); }
}

static void klsy_init(void)
{
    klsy.on = GetPrivateProfileIntA("Sync", "Probe", 0, klh_ini);
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
    ksp.pup = GetPrivateProfileIntA("Sync", "Puppet", 0, klh_ini) != 0;
    ksp.diag = GetPrivateProfileIntA("Sync", "PuppetDiag", 0, klh_ini) != 0;
    ksp.tol = (float)GetPrivateProfileIntA("Sync", "PuppetTol", 60, klh_ini); if (ksp.tol < 5) ksp.tol = 5;
    ksp.snap = (float)GetPrivateProfileIntA("Sync", "PuppetSnap", 1500, klh_ini); if (ksp.snap < ksp.tol * 2) ksp.snap = ksp.tol * 2;
    ksp.speed = (float)GetPrivateProfileIntA("Sync", "PuppetSpeed", 300, klh_ini); if (ksp.speed < 1) ksp.speed = 1;
    ksp.team = GetPrivateProfileIntA("Sync", "PuppetTeam", 3, klh_ini);       /* GUESS: team value 3 = the cops (S2b measurement) */
    if (ksp.pup || ksp.diag) klog("sync: Puppet=%d PuppetDiag=%d PuppetTol=%.0f PuppetSnap=%.0f PuppetSpeed=%.0f PuppetTeam=%d (client only; needs the host's Share=1)%s", ksp.pup, ksp.diag, ksp.tol, ksp.snap, ksp.speed, ksp.team,
                                   (ksp.pup && klsy.apply) ? " WARNING: Apply=1 too: the two fight, use Puppet alone" : "");
    if (klsy.apply) klog("sync: Apply=1 ApplyHp=%d ApplyMax=%d ApplyTol=%d (client only: a non-player actor farther than ApplyTol from the host's is teleported to it)", klsy.applyHp, klsy.applyMax, klsy.applyTol);
    if (klsy.on || klsy.share || klsy.cmp)
        klog("sync: Probe=%d Share=%d Compare=%d Every=%lu ShareMs=%lu Max=%d Tol=%.1f (Probe / Share / Compare are read-only)", klsy.on, klsy.share, klsy.cmp, (unsigned long)klsy.every, (unsigned long)klsy.shareMs, klsy.max, klsy.tol10 / 10.0);
}

/* The round was left (loading, lobby, restart) or has not begun: forget everything received. */
static void klsy_leave(void) { klsy.inwin = 0; klsy.toldMode = 0; ksp_release_all("round left"); ksp_rx = 0; }
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
    if (!(klsy.on || klsy.share || klsy.cmp || klsy.apply || ksp.pup || ksp.diag) || !game_thread || !klh_exe_ok) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) { klsy_leave(); return; }
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) { klsy_leave(); return; }
    if (klsy.on < 2 && ((role != 2 && role != 3) || mode != 4)) { klsy_leave(); return; }
    if (state < 0x13 || state > 0x1f) { klsy_leave(); return; }                /* in a round (botfill's window) */
    if ((klsy.share || klsy.cmp || klsy.apply || ksp.pup || ksp.diag) && !klsy.sock) klsy_open();
    if (!klsy.inwin) {                                                         /* entering the window: nothing from before this moment counts */
        klsy.inwin = 1; klsy_drain();
        klsy.nhost = 0; klsy.applyRx = 0; klsy.rxT = 0; klsy.rxAnchored = 0; klsy.srcSet = 0; klsy.agree = 0; klsy.nbad = 0;
        klsy.applyAt = 0; klsy.cmpAt = 0; klsy.toldHum = 0; klsy.humLogs = 0; klsy.toldRefuse = 0;
        ksp_release_all("round start"); ksp_rx = 0; ksp.pass = 0; ksp.pupAt = 0; ksp.diagAt = 0; ksp.roundAt = now;
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
    if ((klsy.cmp || klsy.apply || ksp.pup || ksp.diag) && role == 3 && klsy.sock) {                                /* client: take the newest FRESH host list, compare once a second */
        static char pk[16 + KLSY_MAXP * KLSY_REC]; klsy_sin from; int fl, len, k;
        for (k = 0; k < 256; k++) {                                                            /* drain the whole queue; the newest acceptable list wins */
            WORD cnt; DWORD T; int age;
            fl = sizeof from; len = klsy.recvfrom(klsy.sock, pk, sizeof pk, 0, &from, &fl);
            if (len < 0) break;
            if (len < 16 || memcmp(pk, "KLSY2", 5)) continue;
            memcpy(&cnt, pk + 12, 2); if (cnt > KLSY_MAXP || 16 + cnt * KLSY_REC > len) continue;
            if (klsy.srcSet && from.addr != klsy.srcAddr) continue;                            /* only the first source that sent a valid list this round */
            memcpy(&T, pk + 8, 4);
            if (klsy.rxAnchored && T <= klsy.rxT) { if (klsy.rxT - T < 500000000u) continue; klsy.rxAnchored = 0; }   /* older / repeated: dropped; a huge step back = the 1e9 ms wrap */
            if (!klsy.rxAnchored) { klsy.rxAnchored = 1; klsy.anchorNow = now; klsy.anchorT = T; }
            age = (int)(now - klsy.anchorNow) - (int)(T - klsy.anchorT);                       /* how long this list sat on the way, by the HOST's clock (GUESS: the first list was on time) */
            if (age > (int)(2 * klsy.shareMs)) continue;
            if (!klsy.srcSet) { klsy.srcSet = 1; klsy.srcAddr = from.addr; klog("sync: host list source locked to %lu.%lu.%lu.%lu", from.addr & 255, from.addr >> 8 & 255, from.addr >> 16 & 255, from.addr >> 24); }
            memcpy(klsy.host, pk + 16, cnt * KLSY_REC); klsy.nhost = cnt; klsy.rxT = T; klsy.rxAt = now; klsy.applyRx = 1; ksp_rx = 1;
        }
        if ((klsy.cmp || klsy.apply || ksp.pup || ksp.diag) && klsy.nhost && now - klsy.cmpAt >= 1000) {            /* the Compare walk also gives Apply its trust: identity agreement */
            struct klsy_cm c; int j, mx = 0, ag; klsy.cmpAt = now; memset(&c, 0, sizeof c); c.worst_s = -1;
            for (j = 0; j < klsy.nhost; j++) if (klsy.host[j].slot > mx) mx = klsy.host[j].slot;
            klsy.lim = (mx | 63) + 1;
            klsy_walk(0, klsy_cmp, &c);
            klsy.lim = 0;
            ag = c.n >= 1 && c.idbad * 10 <= c.n;                                              /* GUESS: at most 10% of the shared slots may differ in class / team */
            if (ag != klsy.agree) { klsy.agree = ag; klog("sync: identity agreement with the host %s (%d slots compared, %d with another class / team)", ag ? "OK" : "LOST", c.n, c.idbad); }
            if (klsy.cmp)
                klog("sync: vs host: %d actors compared (host list %lu ms old, %d in it), %d another class/team, %d farther than %.1f, %d with another health, worst slot %d d=%.1f", c.n,
                     (unsigned long)(now - klsy.rxAt), klsy.nhost, c.idbad, c.bad, klsy.tol10 / 10.0, c.hpbad, c.worst_s, c.worst);
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
