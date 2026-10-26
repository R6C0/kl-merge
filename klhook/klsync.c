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
 *   There is NO Apply key: nothing here moves an actor (re\bots_online_sync.md 6 says why that stays unwritten until the probe shows the cause).
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
struct klsy_pe { unsigned short slot; short hp; float p[3]; };
static struct {
    int on, share, cmp, max, tol10;
    DWORD every, shareMs, at, shAt, cmpAt, rxAt, rxT;
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
    for (i = 0; i < 0x10000; i += 64) {
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

struct klsy_tx { char pk[16 + KLSY_MAXP * 16]; int n; };
static void klsy_collect(DWORD o, DWORD slot, int kind, const char *nm, void *ctx)
{
    struct klsy_tx *t = (struct klsy_tx *)ctx; float pos[3]; int hv, team; float hp; struct klsy_pe e;
    (void)kind; (void)nm;
    if (t->n >= KLSY_MAXP) return;
    klsy_actor(o, pos, &hv, &hp, &team);
    if (!hv) return;
    e.slot = (unsigned short)slot; e.hp = (short)hp; memcpy(e.p, pos, 12);
    memcpy(t->pk + 16 + t->n * 16, &e, 16); t->n++;
}

struct klsy_cm { int n, bad, hpbad, worst_s; float worst; float wo[3], wh[3]; int shown; };
static void klsy_cmp(DWORD o, DWORD slot, int kind, const char *nm, void *ctx)
{
    struct klsy_cm *c = (struct klsy_cm *)ctx; float pos[3], dx, dy, dz, d, hp; int hv, team, i;
    (void)kind; (void)nm;
    for (i = 0; i < klsy.nhost && klsy.host[i].slot != (unsigned short)slot; i++) ;
    if (i == klsy.nhost) return;
    klsy_actor(o, pos, &hv, &hp, &team);
    c->n++;
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

static void klsy_init(void)
{
    klsy.on = GetPrivateProfileIntA("Sync", "Probe", 0, klh_ini);
    klsy.share = GetPrivateProfileIntA("Sync", "Share", 0, klh_ini) != 0;
    klsy.cmp = GetPrivateProfileIntA("Sync", "Compare", 0, klh_ini) != 0;
    klsy.every = (DWORD)GetPrivateProfileIntA("Sync", "Every", 3000, klh_ini); if (klsy.every < 500) klsy.every = 500;
    klsy.shareMs = (DWORD)GetPrivateProfileIntA("Sync", "ShareMs", 250, klh_ini); if (klsy.shareMs < 100) klsy.shareMs = 100;
    klsy.max = GetPrivateProfileIntA("Sync", "Max", 700, klh_ini); if (klsy.max < 1) klsy.max = 1;
    klsy.tol10 = GetPrivateProfileIntA("Sync", "Tol", 10, klh_ini);      /* tenths of a unit: 10 = 1.0 */
    if (klsy.on || klsy.share || klsy.cmp)
        klog("sync: Probe=%d Share=%d Compare=%d Every=%lu ShareMs=%lu Max=%d Tol=%.1f (read-only: nothing is written to the game)", klsy.on, klsy.share, klsy.cmp, (unsigned long)klsy.every, (unsigned long)klsy.shareMs, klsy.max, klsy.tol10 / 10.0);
}

static void klsy_tick(int game_thread)
{
    DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0;
    if (!(klsy.on || klsy.share || klsy.cmp) || !game_thread || !klh_exe_ok) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) return;
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) return;
    if (klsy.on < 2 && ((role != 2 && role != 3) || mode != 4)) { klsy.toldMode = 0; return; }
    if (state < 0x13 || state > 0x1f) return;                                  /* in a round (botfill's window) */
    if (!klsy.toldMode) { klsy.toldMode = 1; klog("sync: round: role %lu state 0x%lx (probe %d, share %d, compare %d)", (unsigned long)role, (unsigned long)state, klsy.on, klsy.share, klsy.cmp); }
    if ((klsy.share || klsy.cmp) && !klsy.sock) klsy_open();
    if (klsy.share && role == 2 && klsy.sock && now - klsy.shAt >= klsy.shareMs) {          /* host: its actors, binary: 'KLSY1' u32 T u16 n, n x {u16 slot, i16 hp, f32 x3} */
        struct klsy_tx *t = (struct klsy_tx *)calloc(1, sizeof *t);
        klsy.shAt = now;
        if (t) {
            klsy_sin a; DWORD T = (DWORD)klsy_T(); WORD cnt; int len, r;
            klsy_walk(0, klsy_collect, t);
            memcpy(t->pk, "KLSY1\0\0\0", 8); memcpy(t->pk + 8, &T, 4); cnt = (WORD)t->n; memcpy(t->pk + 12, &cnt, 2);
            len = 16 + t->n * 16;
            memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((KLSY_PORT & 0xff) << 8) | (KLSY_PORT >> 8)); a.addr = 0xffffffffu;
            r = klsy.sendto(klsy.sock, t->pk, len, 0, &a, sizeof a);
            { static int told; if (!told) { told = 1; klog("sync: host list: %d actors, %d bytes on UDP %d (sendto %d)", t->n, len, KLSY_PORT, r); } }
            free(t);
        }
    }
    if (klsy.cmp && role == 3 && klsy.sock) {                                  /* client: take the newest host list, compare once a second */
        static char pk[16 + KLSY_MAXP * 16]; klsy_sin from; int fl, len, k;
        for (k = 0; k < 32; k++) {
            fl = sizeof from; len = klsy.recvfrom(klsy.sock, pk, sizeof pk, 0, &from, &fl);
            if (len < 16) break;
            if (memcmp(pk, "KLSY1", 5)) continue;
            { WORD cnt; memcpy(&cnt, pk + 12, 2); if (cnt > KLSY_MAXP || 16 + cnt * 16 > len) continue;
              memcpy(klsy.host, pk + 16, cnt * 16); klsy.nhost = cnt; memcpy(&klsy.rxT, pk + 8, 4); klsy.rxAt = now; }
        }
        if (klsy.nhost && now - klsy.cmpAt >= 1000) {
            struct klsy_cm c; klsy.cmpAt = now; memset(&c, 0, sizeof c); c.worst_s = -1;
            klsy_walk(0, klsy_cmp, &c);
            klog("sync: vs host: %d actors compared (host list %lu ms old, %d in it), %d farther than %.1f, %d with another health, worst slot %d d=%.1f", c.n,
                 (unsigned long)(now - klsy.rxAt), klsy.nhost, c.bad, klsy.tol10 / 10.0, c.hpbad, c.worst_s, c.worst);
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
