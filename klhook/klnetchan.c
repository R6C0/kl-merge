/*
 * klnetchan.c - [NetChan] THE HOOK'S SHARED PEER MESSAGE CHANNEL (2026-10-26). Part of KLHook (included by klhook.c after klsync.c, SHIP and
 * TEST alike). One peer sends a short typed text line, every other modded peer in the session gets it. The design, the options that were
 * looked at and why this one: re/hook_netchannel.md. Users today: klucc.c ([Ucc] suspicion pings / accusations). Next users named there:
 * remote cop-squad orders (re/cop_squads.md 5) and the UCC reveal key (re/ucc_design.md OWNER DECISIONS 1).
 *
 * NO GAME STATE IS WRITTEN AND NO GAME NETCODE IS TOUCHED. Two carriers, both outside the game's Net-Z traffic:
 *   UDP   broadcast to 255.255.255.255:<Port> (27416) from the hook's own socket (ws2_32 looked up, as klhostopt.c / klcharonline.c do; their
 *         ports are 27413 / 27414, klsync.c's 27415). Reaches peers on the same PC (two instances, SO_REUSEADDR) and on the same LAN: System Link.
 *         PROVEN PATTERN: klcharonline.c's UDP 27414 carried both peers' looks live (B2, 2026-10-26 07:15, 'CharOnline both ways').
 *         Loss: each message goes out Repeat (3) times RepeatMs (300) apart with the same seq; receivers keep the first.
 *   Steam lobby MEMBER data, key klx_msg = the last 4 packet lines ('`'-joined), through klmm.c's ISteamMatchmaking proxy (slots 24 set,
 *         16/17/23 read; 17 has the hidden CSteamID return pointer, klbuild.c's convention). Reaches internet peers of a Steam lobby WHILE THE
 *         LOBBY EXISTS. GUESS (re/hook_netchannel.md 2): the game leaves the Steam lobby when every member answered SyncedWithLobby (0x745c80
 *         sends ExitLobby; 0x8bd520 then calls LeaveLobby 0x700910 unless [this+0x36e]), so in a Quick / Private match this carrier may be
 *         dead for the whole round. The log says once per session whether the lobby id is still there in a round ('netchan: steam lobby ...').
 * Internet play in a round therefore has NO proven carrier yet; the ranked options (a Steam P2P proxy on the game's own ISteamNetworking
 * import being the best) are in re/hook_netchannel.md 3.
 *
 * API (game thread only):
 *   knc_want(who)              a module asks for the channel (from its init); nothing opens and nothing is sent unless one module did
 *   knc_on(type, fn)           fn(msg, src) for every NEW message of that type from ANOTHER peer (src 1 Steam, 2 UDP); up to 8 handlers
 *   knc_send(type, payload, ent)  -> seq (0 = not sent: no session / not wanted / bad type). The sender does NOT get its own message back:
 *                              show it locally yourself. Log: the first send of each type per session, every send at Log=2
 *   knc_role()                 the session role at the last tick (2 host, 3 client, 0 none)
 * Trust: a LAN game among friends. 'From the host' = the sender says role 2; nothing is signed. Receivers sanitise every byte.
 *
 * KLHook.ini [NetChan] (read at the first knc_want): Udp=1 Steam=1 Port=27416 Repeat=3 RepeatMs=300 Log=1
 */
#ifndef KLNETCHAN_C
#define KLNETCHAN_C
#include "klnetchan_logic.h"

#define KNC_HANDLERS 8
#define KNC_OUTQ     8
typedef void (*knc_fn)(const struct knc_msg *m, int src);
typedef struct { short fam; unsigned short port; unsigned long addr; char zero[8]; } knc_sin;

static struct {
    int users, read, udp, steam, port, repeat, repeatMs, log;
    unsigned sid, seq; int role, lastRole;
    struct { char type[KLNC_TYPE_MAX]; knc_fn fn; } h[KNC_HANDLERS]; int nh;
    struct { char pkt[KLNC_PKT_MAX + 1]; int len, left; DWORD at; } q[KNC_OUTQ];
    struct knc_seen seen; struct knc_hw hw; struct knc_ring ring; int ringDirty;
    unsigned __int64 lobby; DWORD steamGet, steamSet; int toldLobby, toldOwn, toldSteamRound;
    char toldType[KNC_HANDLERS][KLNC_TYPE_MAX]; int ntold;          /* types whose first send this session was logged (the rest: Log=2) */
    UINT_PTR sock; int sockTried; unsigned long sent, heard;
} knc;

static int (WINAPI *knc_WSAStartup)(WORD, void *);
static UINT_PTR (WINAPI *knc_socket)(int, int, int);
static int (WINAPI *knc_setsockopt)(UINT_PTR, int, int, const char *, int);
static int (WINAPI *knc_bind)(UINT_PTR, const void *, int);
static int (WINAPI *knc_sendto)(UINT_PTR, const char *, int, int, const void *, int);
static int (WINAPI *knc_recvfrom)(UINT_PTR, char *, int, int, void *, int *);
static int (WINAPI *knc_ioctl)(UINT_PTR, long, unsigned long *);

static int knc_want(const char *who)
{
    if (!knc.read) {
        LARGE_INTEGER pc;
        knc.read = 1;
        knc.udp = GetPrivateProfileIntA("NetChan", "Udp", 1, klh_ini) != 0;
        knc.steam = GetPrivateProfileIntA("NetChan", "Steam", 1, klh_ini) != 0;
        knc.port = (int)GetPrivateProfileIntA("NetChan", "Port", 27416, klh_ini); if (knc.port < 1024 || knc.port > 65535) knc.port = 27416;
        knc.repeat = (int)GetPrivateProfileIntA("NetChan", "Repeat", 3, klh_ini); if (knc.repeat < 1) knc.repeat = 1; if (knc.repeat > 6) knc.repeat = 6;
        knc.repeatMs = (int)GetPrivateProfileIntA("NetChan", "RepeatMs", 300, klh_ini); if (knc.repeatMs < 50) knc.repeatMs = 50; if (knc.repeatMs > 2000) knc.repeatMs = 2000;
        knc.log = (int)GetPrivateProfileIntA("NetChan", "Log", 1, klh_ini);
        QueryPerformanceCounter(&pc);
        knc.sid = (unsigned)(pc.LowPart ^ (GetCurrentProcessId() << 16) ^ GetTickCount() ^ (DWORD)(DWORD_PTR)&knc); if (!knc.sid) knc.sid = 1;
    }
    knc.users++;
    klog("netchan: wanted by %s: Udp=%d (port %d) Steam=%d (member data klx_msg) Repeat=%d x %d ms; my sender id %08x", who, knc.udp, knc.port, knc.steam, knc.repeat, knc.repeatMs, knc.sid);
    return knc.udp || knc.steam;
}

static int knc_on(const char *type, knc_fn fn)
{
    if (knc.nh >= KNC_HANDLERS || !knc_type_ok(type) || !fn) return 0;
    strcpy(knc.h[knc.nh].type, type); knc.h[knc.nh].fn = fn; knc.nh++;
    return 1;
}

static int knc_role(void) { return knc.role; }

static void knc_open(void)
{
    HMODULE m; BYTE wsa[600]; knc_sin a; int one = 1; unsigned long nb = 1;
    if (knc.sock || knc.sockTried) return;
    knc.sockTried = 1;
    if (!(m = LoadLibraryA("ws2_32.dll"))) { klog("netchan: ws2_32 not loadable: no UDP"); return; }
    knc_WSAStartup = (int (WINAPI *)(WORD, void *))GetProcAddress(m, "WSAStartup"); knc_socket = (UINT_PTR (WINAPI *)(int, int, int))GetProcAddress(m, "socket");
    knc_setsockopt = (int (WINAPI *)(UINT_PTR, int, int, const char *, int))GetProcAddress(m, "setsockopt"); knc_bind = (int (WINAPI *)(UINT_PTR, const void *, int))GetProcAddress(m, "bind");
    knc_sendto = (int (WINAPI *)(UINT_PTR, const char *, int, int, const void *, int))GetProcAddress(m, "sendto");
    knc_recvfrom = (int (WINAPI *)(UINT_PTR, char *, int, int, void *, int *))GetProcAddress(m, "recvfrom"); knc_ioctl = (int (WINAPI *)(UINT_PTR, long, unsigned long *))GetProcAddress(m, "ioctlsocket");
    if (!knc_WSAStartup || !knc_socket || !knc_setsockopt || !knc_bind || !knc_sendto || !knc_recvfrom || !knc_ioctl) { klog("netchan: ws2_32 functions missing: no UDP"); return; }
    if (knc_WSAStartup(0x0202, wsa)) { klog("netchan: WSAStartup failed: no UDP"); return; }
    knc.sock = knc_socket(2, 2, 17);
    if (knc.sock == (UINT_PTR)~0) { knc.sock = 0; klog("netchan: socket() failed: no UDP"); return; }
    knc_setsockopt(knc.sock, 0xffff, 0x0004 /* SO_REUSEADDR */, (const char *)&one, 4);
    knc_setsockopt(knc.sock, 0xffff, 0x0020 /* SO_BROADCAST */, (const char *)&one, 4);
    knc_ioctl(knc.sock, (long)0x8004667E /* FIONBIO */, &nb);
    memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((knc.port & 0xff) << 8) | (knc.port >> 8)); a.addr = 0;
    if (knc_bind(knc.sock, &a, sizeof a)) klog("netchan: bind to UDP %d failed: send only", knc.port);
    else klog("netchan: UDP %d open (broadcast + listen)", knc.port);
}

static void knc_udp_out(const char *pkt, int len)
{
    knc_sin a;
    if (!knc.sock) return;
    memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((knc.port & 0xff) << 8) | (knc.port >> 8)); a.addr = 0xffffffffu;
    knc_sendto(knc.sock, pkt, len, 0, &a, sizeof a);
}

static unsigned knc_send(const char *type, const char *payload, int ent)
{
    char pkt[KLNC_PKT_MAX + 1]; int len, i;
    if (!knc.users || (knc.role != 2 && knc.role != 3)) return 0;
    len = knc_build(pkt, sizeof pkt, knc.sid, knc.role, ent, knc.seq + 1, type, payload);
    if (!len) { klog("netchan: message of type '%s' not sent: bad type or too long", type ? type : "?"); return 0; }
    knc.seq++;
    if (knc.udp && knc.sock) {
        knc_udp_out(pkt, len);
        for (i = 0; i < KNC_OUTQ && knc.q[i].left; i++) ;
        if (i < KNC_OUTQ && knc.repeat > 1) { memcpy(knc.q[i].pkt, pkt, (size_t)len + 1); knc.q[i].len = len; knc.q[i].left = knc.repeat - 1; knc.q[i].at = GetTickCount(); }
    }
    if (knc.steam) { knc_ring_push(&knc.ring, pkt); knc.ringDirty = 1; }
    knc.sent++;
    {   int t, first = 1;
        for (t = 0; t < knc.ntold; t++) if (!strcmp(knc.toldType[t], type)) first = 0;
        if (first && knc.ntold < KNC_HANDLERS) strcpy(knc.toldType[knc.ntold++], type);
        if (!first && knc.log < 2) return knc.seq;
    }
    if (knc.log) klog("netchan: sent #%u %s '%s' (role %d, entity %d)%s%s", knc.seq, type, payload ? payload : "", knc.role, ent,
                      knc.udp && knc.sock ? " via UDP" : "", knc.steam && klmm_real && knc.lobby ? " + Steam member data" : knc.steam ? " (Steam: no lobby now)" : "");
    return knc.seq;
}

static void knc_take(const char *line, int len, int src)
{
    struct knc_msg m; int i, took = 0;
    if (!knc_parse(line, len, &m)) return;
    if (m.sid == knc.sid) { if (!knc.toldOwn++) klog("netchan: heard my own message back via %s: ignored - that carrier works", src == 1 ? "Steam" : "UDP"); return; }
    if (!knc_seen_new(&knc.seen, m.sid, m.seq) || !knc_hw_ok(&knc.hw, m.sid, m.seq)) return;
    knc.heard++;
    for (i = 0; i < knc.nh; i++) if (!strcmp(knc.h[i].type, m.type)) { knc.h[i].fn(&m, src); took++; }
    if (knc.log >= 2 || (knc.log && !took)) klog("netchan: heard #%u %s from %08x (role %d, entity %d) via %s: '%s'%s", m.seq, m.type, m.sid, m.role, m.ent, src == 1 ? "Steam" : "UDP", m.payload, took ? "" : " - no handler");
}
static void knc_take_steam(const char *line, int len, void *ctx) { (void)ctx; knc_take(line, len, 1); }

static void knc_tick(int game_thread)
{
    DWORD now = GetTickCount(), sm, role = 0; int i;
    if (!knc.users || !game_thread || !klh_exe_ok) return;
    sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION));
    if (sm && kls_online_cached()) klh_rd(sm + 0x54, &role, 4);
    knc.role = (role == 2 || role == 3) ? (int)role : 0;
    if (knc.role != knc.lastRole) {
        if (knc.log) klog("netchan: session role %d -> %d%s", knc.lastRole, knc.role, knc.role ? "" : " (channel idle)");
        knc.lastRole = knc.role;
        if (!knc.role) { knc.ring.n = 0; knc.ringDirty = 0; knc.toldSteamRound = 0; knc.ntold = 0; memset(knc.q, 0, sizeof knc.q); }
    }
    if (!knc.role) return;
    {   /* the Steam lobby id (service +0x35c exists, +0x35e id: klhostopt.c) */
        DWORD svc = klh_rd32(sm + 0x17c), lob[2] = { 0, 0 }; BYTE ex = 0; unsigned __int64 was = knc.lobby;
        if (svc && klh_rd(svc + 0x35c, &ex, 1) && ex && klh_rd(svc + 0x35e, lob, 8)) knc.lobby = (unsigned __int64)lob[1] << 32 | lob[0]; else knc.lobby = 0;
        if (knc.steam && (!!was != !!knc.lobby) && knc.log) klog("netchan: Steam lobby %s (role %d)", knc.lobby ? "present: member data carrier ON" : "gone: member data carrier off", knc.role);
    }
    if (knc.udp) knc_open();
    for (i = 0; i < KNC_OUTQ; i++) if (knc.q[i].left && now - knc.q[i].at >= (DWORD)knc.repeatMs) { knc_udp_out(knc.q[i].pkt, knc.q[i].len); knc.q[i].left--; knc.q[i].at = now; }
    if (knc.udp && knc.sock) {
        char pk[KLNC_PKT_MAX + 1]; knc_sin from; int fl, len, k;
        for (k = 0; k < 32; k++) {
            fl = sizeof from; len = knc_recvfrom(knc.sock, pk, sizeof pk - 1, 0, &from, &fl);
            if (len <= 0) break;
            pk[len] = 0;
            knc_take(pk, len, 2);
        }
    }
    if (knc.steam && klmm_real && knc.lobby) {
        if (knc.ringDirty || (knc.ring.n && now - knc.steamSet >= 5000)) {
            char v[KLNC_RING * (KLNC_PKT_MAX + 1) + 8];
            knc_ring_join(&knc.ring, v, sizeof v);
            ((void (__fastcall *)(void *, void *, unsigned __int64, const char *, const char *))KLMM_REAL(24))(klmm_real, 0, knc.lobby, "klx_msg", v);
            knc.ringDirty = 0; knc.steamSet = now;
        }
        if (now - knc.steamGet >= 500) {
            int cnt = ((int (__fastcall *)(void *, void *, unsigned __int64))KLMM_REAL(16))(klmm_real, 0, knc.lobby), mi;
            knc.steamGet = now;
            for (mi = 0; mi < cnt && mi < 16; mi++) {
                unsigned __int64 id = 0; const char *v; char b[KLNC_RING * (KLNC_PKT_MAX + 1) + 8];
                ((void *(__fastcall *)(void *, void *, unsigned __int64 *, unsigned __int64, int))KLMM_REAL(17))(klmm_real, 0, &id, knc.lobby, mi);     /* hidden CSteamID return (klbuild.c) */
                if (!id) continue;
                v = ((const char *(__fastcall *)(void *, void *, unsigned __int64, unsigned __int64, const char *))KLMM_REAL(23))(klmm_real, 0, knc.lobby, id, "klx_msg");
                if (v && klh_rdstr((DWORD_PTR)v, b, sizeof b) > 0) knc_ring_split(b, knc_take_steam, 0);
            }
        }
    } else if (knc.steam && !knc.toldSteamRound && knc.log) {
        knc.toldSteamRound = 1;
        klog("netchan: Steam carrier not usable now (%s): UDP only", !klmm_real ? "no ISteamMatchmaking proxy (klmm.c)" : "no Steam lobby - System Link, or the game left the lobby at match start (GUESS, re/hook_netchannel.md 2)");
    }
}

#endif /* KLNETCHAN_C */
