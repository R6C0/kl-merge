/*
 * klucc.c - [Ucc] SUSPICION MESSAGES IN UNDERCOVER COP (2026-10-26; owner, re/ucc_design.md OWNER DECISIONS 6: "suspicion messages ON, and
 * heisters can also raise them themselves (an accuse key naming a player), next to the host's random fake pings"). Part of KLHook (included
 * by klhook.c after klnetchan.c). DEFAULT OFF. NOTHING HERE HAS RUN IN THE GAME. No code byte of kl2.exe changes and no game state is
 * written: the lines are shown through the game's own centre announcement routine 0x468430 (as kladren.c / klhud_popup.c do), the peers
 * are told through klnetchan.c (the hook's own UDP / Steam member data, outside the game's netcode).
 *
 * 1. PINGS (host): every PingMinS..PingMaxS seconds of play the HOST picks a random living heister of the session player table and a random
 *    line ('Someone saw <name> talking into a radio' ...), shows it and sends the FINISHED TEXT (type UPING); every modded peer shows the
 *    host's text, so all screens agree. The named heister is random: sometimes the real UCC, mostly not (misdirection, P5).
 * 2. ACCUSE (any heister): Key (F5) while aiming at another heister (the smallest angle to the eye -> aim-point ray inside ConeDeg, within
 *    RangeM; no aim point = the nearest heister within RangeM, said in the log) shows '<me> suspects <him>' here and sends it (type UACC).
 *    Rate limit: CooldownS per player, on the sender AND on every receiver (per sender id). The accuser must be a heister (type 2, police
 *    byte 0): a cop, a dead or a waiting player has no key. The hidden UCC is a heister on every screen, so he can accuse too (by design).
 * 3. NAMES: every modded peer sends HELLO '<my table index>|<my name>' every 5 s in a UCC round; my name = [Ucc] Name, else the Steam
 *    persona (steam_api SteamFriends()->GetPersonaName, ISteamFriends +0: re/netcode.md app. B; the game itself calls it at 0x869430), else
 *    'Player <index+1>'. A player nobody heard from is 'Player <index+1>' (same number on every peer: table order = load order). The SENDER
 *    names both players, so receivers never need the name table to agree.
 * 4. WHERE IT SHOWS: the FA announcement element [[[gamedata+0x15dc]]+0x10a8] (vtable 0xbbdd34, or klhud_popup.c's private copy), routine
 *    0x468430 head-checked. A stock message still on screen (clock [[0xdd2640]+0x48] < end float [el+0x30] x 1024) is not overwritten: ours
 *    waits up to 6 s, then goes anyway. With [HUD] Popups=1 it gets the painted chalk bar like every other announcement.
 * 5. WINDOW: kluc_gate - role 2/3, game type 4, sub-mode [0x168e59c] == 1, state 0x19..0x1e (GUESS: play). Messages heard outside it are
 *    dropped (logged at Log=2).
 * HOST-LOCAL PART (works with NO carrier: [NetChan] Udp=0 Steam=0, or internet play where the Steam lobby is gone): the host's own pings
 * and every player's own accusations show on that player's own screen; only the peers do not see them.
 *
 * GUESSES (to be settled by the live bench, re/hook_netchannel.md 5): aim point [P+0x27b0] is a world point (luvsic, klcopsquad.c);
 * feet [P+0x460] (klcopsquad.c); health [[P+0x5fc]+4] for a ZFFPlayer (ZFFActor's field; unreadable = taken as alive); the own entity
 * by klcharonline.c's klco_find_own; the session player table holds the humans (AI heisters of [Bots] OnlineFill may be named by a ping).
 *
 * KLHook.ini [Ucc]
 *   Pings=0          1 = the host sends fake suspicion pings (only the HOST's value matters)
 *   PingMinS=60 PingMaxS=120   seconds between pings (clamped 10..600 / min..900); the first one PingMinS after GO
 *   Accuse=0         1 = this player's accuse key is live (and accusations from others are shown)
 *   Key=0x74         F5 (free in the hook: E climb, F/G/H cop squad, G grenade, F6 shop page, F7 unstick / map set, F8 AI / shelf, F9 / F11
 *                    looks, Tab board; the key is polled, not consumed)
 *   CooldownS=20     per-player accusation gap (5..300)
 *   ConeDeg=15 RangeM=40      the aim cone and range
 *   ShowS=4          seconds a line stays
 *   Name=            my shown name (empty = Steam persona)
 *   Log=1            0 quiet, 1 events, 2 + every drop
 */
#ifndef KLUCC_C
#define KLUCC_C
#include "klucc_logic.h"

#define KLUC_SUBMODE   0x0168e59cu
#define KLUC_ANNOUNCE  0x00468430u
#define KLUC_ANN_VT    0x00bbdd34u
#define KLUC_OSD_VT    0x00bbe504u
#define KLUC_O_ANN     0x10a8
#define KLUC_OSDHOLD   0x15dc
#define KLUC_PEND      4

static struct {
    int pings, accuse, key, log, lo, hi; unsigned long cooldownMs, showMs; float cosCone, range;
    char myName[KLUC_NAME]; int nameFrom;                 /* 0 ini, 1 Steam persona, 2 fallback */
    int inwin, code, toldNoEl, toldNoOwn; DWORD roundAt, nextPing, helloAt, lastAccuse, passAt;
    unsigned rng; struct kluc_key kk; struct kluc_rl rl;
    char names[KLUC_N][KLUC_NAME]; DWORD nameAt[KLUC_N];
    char pend[KLUC_PEND][KLUC_TEXT]; DWORD pendAt[KLUC_PEND]; int npend;
    DWORD ents; int n, own; DWORD ownEnt;
    SHORT (WINAPI *aks)(int); HWND (WINAPI *fgw)(void); DWORD (WINAPI *wtp)(HWND, LPDWORD); BOOL (WINAPI *beep)(DWORD, DWORD);
} kluc;

/* ---- the announcement element and the show queue ---- */
static DWORD kluc_element(void)
{
    DWORD gd, hold, osd, el, vt = 0; BYTE none = 0xff;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(hold = klh_rd32(gd + KLUC_OSDHOLD)) || !klh_rd(hold + 4, &none, 1) || none == 0xff) return 0;
    if (!(osd = klh_rd32(hold)) || klh_rd32(osd) != KLUC_OSD_VT || !(el = klh_rd32(osd + KLUC_O_ANN)) || !klh_rd(el, &vt, 4)) return 0;
    if (vt != KLUC_ANN_VT && vt != (DWORD)(DWORD_PTR)&klpu_evt[1]) return 0;
    return el;
}
static int kluc_busy(DWORD el)
{   /* a stock message still on screen: [el+0x30] end (clock / 1024), the clock [[0xdd2640]+0x48] (klhud_popup.c's reading) */
    float end = -1.0f; LONG frame = 0; DWORD sys;
    return klh_rd(el + 0x30, &end, 4) && end > 0 && (sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) != 0 && klh_rd(sys + 0x48, &frame, 4) && frame < (LONG)(end * 1024.0f);
}
static int kluc_show_now(const char *text, int force)
{
    static char buf[KLUC_TEXT];                                   /* the element may keep the pointer: a static buffer */
    static const BYTE say_code[8] = { 0x56, 0x57, 0x8b, 0x7c, 0x24, 0x0c, 0x8b, 0xc7 };   /* 0x468430 */
    DWORD el;
    if (kluc.code < 0) { kluc.code = klu_same_code(KLUC_ANNOUNCE, say_code, sizeof say_code); if (!kluc.code) klog("ucc: 0x468430 is not the announcement routine this build knows: lines go to the log only"); }
    if (!kluc.code) return 1;                                     /* nothing can be shown: drop (logged once) */
    if (!(el = kluc_element())) { if (!kluc.toldNoEl++) klog("ucc: no FA announcement element yet ([[gamedata+0x15dc]]+0x10a8): line waits"); return 0; }
    if (!force && kluc_busy(el)) return 0;
    snprintf(buf, sizeof buf, "%s", text);
    ((void (__fastcall *)(void *, void *, const char *, float))(DWORD_PTR)KLH_VA(KLUC_ANNOUNCE))((void *)(DWORD_PTR)el, 0, buf, (float)kluc.showMs / 1000.0f);
    if (kluc.log) klog("ucc: shown '%s'%s", buf, force ? " (over a stock message after 6 s)" : "");
    return 1;
}
static void kluc_show(const char *text)
{
    if (kluc.npend == 0 && kluc_show_now(text, 0)) return;
    if (kluc.npend == KLUC_PEND) { if (kluc.log) klog("ucc: line dropped (4 waiting): '%s'", text); return; }
    snprintf(kluc.pend[kluc.npend], KLUC_TEXT, "%s", text); kluc.pendAt[kluc.npend] = GetTickCount(); kluc.npend++;
}
static void kluc_flush(DWORD now)
{
    while (kluc.npend) {
        int force = now - kluc.pendAt[0] >= 6000;
        if (!kluc_show_now(kluc.pend[0], force)) { if (now - kluc.pendAt[0] >= 12000) { klog("ucc: line dropped (no element for 12 s): '%s'", kluc.pend[0]); } else return; }
        memmove(kluc.pend[0], kluc.pend[1], sizeof kluc.pend[0] * (KLUC_PEND - 1)); memmove(kluc.pendAt, kluc.pendAt + 1, sizeof kluc.pendAt[0] * (KLUC_PEND - 1)); kluc.npend--;
        return;                                                   /* one line a tick: the next waits for this one's end */
    }
}

/* ---- names ---- */
static int kluc_is_code(DWORD a)
{   /* committed executable memory of any module (Steam's interface functions live in steamclient.dll, not in kl2.exe) */
    MEMORY_BASIC_INFORMATION mbi;
    return a >= 0x10000 && VirtualQuery((const void *)(DWORD_PTR)a, &mbi, sizeof mbi) && mbi.State == MEM_COMMIT &&
           (mbi.Protect & (PAGE_EXECUTE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY)) && !(mbi.Protect & PAGE_GUARD);
}
static void kluc_my_name(void)
{
    char ini[64], tmp[KLUC_NAME]; HMODULE s;
    GetPrivateProfileStringA("Ucc", "Name", "", ini, sizeof ini, klh_ini);
    if (ini[0]) { kluc_clean_name(ini, -1, kluc.myName); kluc.nameFrom = 0; return; }
    if ((s = GetModuleHandleA("steam_api.dll")) != 0) {
        void *(__cdecl *sf)(void) = (void *(__cdecl *)(void))GetProcAddress(s, "SteamFriends"); void *fr; DWORD vt, fn; const char *p;
        if (sf && (fr = sf()) != 0 && (vt = klh_rd32((DWORD_PTR)fr)) != 0 && (fn = klh_rd32(vt)) != 0 && kluc_is_code(fn) &&
            (p = ((const char *(__fastcall *)(void *, void *))(DWORD_PTR)fn)(fr, 0)) != 0 && klh_rdstr((DWORD_PTR)p, tmp, sizeof tmp) > 0) {
            kluc_clean_name(tmp, -1, kluc.myName); kluc.nameFrom = 1; return;
        }
    }
    kluc.myName[0] = 0; kluc.nameFrom = 2;                        /* 'Player <index+1>' once the own index is known */
}
static const char *kluc_name_of(int ent)
{
    static char fb[4][KLUC_NAME]; static int r;
    if (ent == kluc.own && kluc.myName[0]) return kluc.myName;
    if (ent >= 0 && ent < KLUC_N && kluc.names[ent][0]) return kluc.names[ent];
    r = (r + 1) & 3; snprintf(fb[r], KLUC_NAME, "Player %d", ent + 1);
    return fb[r];
}

/* ---- bodies: living heisters of the session player table ---- */
static int kluc_alive_heister(DWORD P)
{
    DWORD h; float hp = 1.0f;
    if (!klco_heister(P)) return 0;                               /* type 2, police byte 0, node (klcharonline.c) */
    if ((h = klh_rd32(P + 0x5fc)) != 0 && klh_rd(h + 4, &hp, 4) && hp <= 0) return 0;     /* GUESS: ZFFActor's health holder; unreadable = alive */
    return 1;
}
static int kluc_feet(DWORD P, float f[3]) { return klh_rd(P + 0x460, f, 12) && klb_finite(f[0]) && klb_finite(f[1]) && klb_finite(f[2]); }

/* ---- channel handlers ---- */
static int kluc_in_round(void) { return kluc.inwin; }
static void kluc_on_ping(const struct knc_msg *m, int src)
{
    if (m->role != 2) { if (kluc.log >= 2) klog("ucc: ping from a non-host (role %d): dropped", m->role); return; }
    if (!kluc_in_round()) { if (kluc.log >= 2) klog("ucc: ping heard outside a UCC round: dropped"); return; }
    if (kluc.log) klog("ucc: host ping heard via %s: '%s'", src == 1 ? "Steam" : "UDP", m->payload);
    kluc_show(m->payload);
}
static void kluc_on_accuse(const struct knc_msg *m, int src)
{
    if (!kluc.accuse || !kluc_in_round()) { if (kluc.log >= 2) klog("ucc: accusation dropped (%s)", kluc.accuse ? "not in a UCC round" : "Accuse=0 here"); return; }
    if (!kluc_rl_ok(&kluc.rl, m->sid, GetTickCount(), kluc.cooldownMs * 4 / 5)) { if (kluc.log) klog("ucc: accusation from %08x too soon after its last: dropped", m->sid); return; }
    if (kluc.log) klog("ucc: accusation heard via %s from entity %d: '%s'", src == 1 ? "Steam" : "UDP", m->ent, m->payload);
    kluc_show(m->payload);
}
static void kluc_on_hello(const struct knc_msg *m, int src)
{
    int e; char nm[KLUC_NAME]; (void)src;
    if (!kluc_hello_parse(m->payload, &e, nm)) return;
    if (strcmp(kluc.names[e], nm) && kluc.log) klog("ucc: entity %d is '%s'", e, nm);
    strcpy(kluc.names[e], nm); kluc.nameAt[e] = GetTickCount();
}

static void kluc_init(void)
{
    HMODULE u, k; int cone, range;
    kluc.pings = GetPrivateProfileIntA("Ucc", "Pings", 0, klh_ini) != 0;
    kluc.accuse = GetPrivateProfileIntA("Ucc", "Accuse", 0, klh_ini) != 0;
    kluc.own = -1; kluc.code = -1;
    if (!kluc.pings && !kluc.accuse) return;
    kluc_ping_range((int)GetPrivateProfileIntA("Ucc", "PingMinS", 60, klh_ini), (int)GetPrivateProfileIntA("Ucc", "PingMaxS", 120, klh_ini), &kluc.lo, &kluc.hi);
    kluc.key = (int)GetPrivateProfileIntA("Ucc", "Key", 0x74, klh_ini) & 0xff;
    kluc.cooldownMs = (unsigned long)GetPrivateProfileIntA("Ucc", "CooldownS", 20, klh_ini); if (kluc.cooldownMs < 5) kluc.cooldownMs = 5; if (kluc.cooldownMs > 300) kluc.cooldownMs = 300; kluc.cooldownMs *= 1000;
    cone = (int)GetPrivateProfileIntA("Ucc", "ConeDeg", 15, klh_ini); if (cone < 2) cone = 2; if (cone > 60) cone = 60;
    range = (int)GetPrivateProfileIntA("Ucc", "RangeM", 40, klh_ini); if (range < 3) range = 3; if (range > 200) range = 200;
    kluc.cosCone = (float)cos((double)cone * 3.14159265358979 / 180.0); kluc.range = (float)range * 100.0f;
    kluc.showMs = (unsigned long)GetPrivateProfileIntA("Ucc", "ShowS", 4, klh_ini); if (kluc.showMs < 2) kluc.showMs = 2; if (kluc.showMs > 10) kluc.showMs = 10; kluc.showMs *= 1000;
    kluc.log = (int)GetPrivateProfileIntA("Ucc", "Log", 1, klh_ini);
    kluc.rng = GetTickCount() ^ (GetCurrentProcessId() * 2654435761u);
    if ((u = GetModuleHandleA("user32.dll")) != 0) { kluc.aks = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState"); kluc.fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); kluc.wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId"); }
    if ((k = GetModuleHandleA("kernel32.dll")) != 0) kluc.beep = (BOOL (WINAPI *)(DWORD, DWORD))GetProcAddress(k, "Beep");
    if (!knc_want("ucc")) klog("ucc: [NetChan] Udp=0 and Steam=0: HOST-LOCAL only (each player sees only his own lines)");
    knc_on("UPING", kluc_on_ping); knc_on("UACC", kluc_on_accuse); knc_on("HELLO", kluc_on_hello);
    klog("ucc: ON (NOT yet run live): Pings=%d (%d..%d s, host only) Accuse=%d key %#x cooldown %lu s cone %d deg range %d m show %lu s",
         kluc.pings, kluc.lo, kluc.hi, kluc.accuse, kluc.key, kluc.cooldownMs / 1000, cone, range, kluc.showMs / 1000);
}

static int kluc_keydown(int vk)
{
    HWND fg; DWORD pid = 0;
    if (!vk || !kluc.aks || !kluc.fgw || !kluc.wtp || !(fg = kluc.fgw())) return 0;
    kluc.wtp(fg, &pid);
    return pid == GetCurrentProcessId() && (kluc.aks(vk) & 0x8000) != 0;
}

static void kluc_ping(DWORD now)
{
    int idx[KLUC_N], c = 0, i, k; char text[KLUC_TEXT];
    for (i = 0; i < kluc.n && i < KLUC_N; i++) if (kluc_alive_heister(klco_ent(kluc.ents, kluc.n, i))) idx[c++] = i;
    kluc.nextPing = now + kluc_next_ms(&kluc.rng, kluc.lo, kluc.hi);
    if (!c) { if (kluc.log) klog("ucc: ping due but no living heister in the table"); return; }
    k = idx[kluc_pick(&kluc.rng, c)];
    kluc_ping_text((int)(kluc_rand(&kluc.rng) % KLUC_PING_VARIANTS), kluc_name_of(k), text, sizeof text);
    if (kluc.log) klog("ucc: HOST ping names entity %d of %d living heisters; next in %lu s", k, c, (kluc.nextPing - now) / 1000);
    kluc_show(text);
    knc_send("UPING", text, kluc.own);
}

static void kluc_accuse_key(DWORD now)
{
    DWORD me = kluc.ownEnt; float feet[3], eye[3], aim[3]; struct kluc_body b[KLUC_N]; int nb = 0, i, k, how = 1; unsigned long wait; char text[KLUC_TEXT];
    if (kluc.own < 0 || !me) { if (kluc.log) klog("ucc: accuse key: my own body is not in the player table"); return; }
    if (!kluc_alive_heister(me)) { if (kluc.log) klog("ucc: accuse key: only a living heister can accuse"); return; }
    if ((wait = kluc_wait_left(kluc.lastAccuse, now, kluc.cooldownMs)) != 0) {
        if (kluc.log) klog("ucc: accuse key: %lu s left of the cooldown", (wait + 999) / 1000);
        if (kluc.beep) kluc.beep(300, 60);
        return;
    }
    if (!kluc_feet(me, feet)) { klog("ucc: accuse key: no feet of my body"); return; }
    eye[0] = feet[0]; eye[1] = feet[1] + KLUC_EYE; eye[2] = feet[2];
    for (i = 0; i < kluc.n && i < KLUC_N; i++) {
        DWORD P = klco_ent(kluc.ents, kluc.n, i); float f[3];
        if (i == kluc.own || !kluc_alive_heister(P) || !kluc_feet(P, f)) continue;
        b[nb].ent = i; b[nb].p[0] = f[0]; b[nb].p[1] = f[1] + KLUC_CHEST; b[nb].p[2] = f[2]; nb++;
    }
    if (klh_rd(me + 0x27b0, aim, 12) && klb_finite(aim[0]) && klb_finite(aim[1]) && klb_finite(aim[2])) k = kluc_aim_pick(eye, aim, b, nb, kluc.cosCone, kluc.range);
    else { how = 0; k = kluc_nearest(eye, b, nb, kluc.range); }
    if (k < 0) {
        if (kluc.log) klog("ucc: accuse key: nobody %s (%d other living heisters)", how ? "in the aim cone" : "in range (no aim point: GUESS [P+0x27b0])", nb);
        if (kluc.beep) kluc.beep(300, 60);
        return;
    }
    kluc.lastAccuse = now ? now : 1;
    kluc_accuse_text(kluc_name_of(kluc.own), kluc_name_of(b[k].ent), text, sizeof text);
    if (kluc.log) klog("ucc: I accuse entity %d (%s)", b[k].ent, how ? "aimed at" : "nearest: no aim point");
    kluc_show(text);
    knc_send("UACC", text, kluc.own);
}

static void kluc_tick(int game_thread)
{
    DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0, sub = 0;
    int down;
    if ((!kluc.pings && !kluc.accuse) || !game_thread || !klh_exe_ok) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm)) || !klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)
        || !klh_rd((DWORD_PTR)KLH_VA(KLUC_SUBMODE), &sub, 4) || !kluc_gate(role, mode, state, sub)) {
        if (kluc.inwin && kluc.log) klog("ucc: round window closed (role %lu, mode %lu, state 0x%lx, sub-mode %lu)", (unsigned long)role, (unsigned long)mode, (unsigned long)state, (unsigned long)sub);
        kluc.inwin = 0; kluc.npend = 0; kluc.own = -1; kluc.ownEnt = 0;
        return;
    }
    if (!kluc.inwin) {
        kluc.inwin = 1; kluc.roundAt = now; kluc.helloAt = 0; kluc.passAt = 0; kluc.toldNoOwn = 0;
        kluc.nextPing = now + (DWORD)kluc.lo * 1000;
        kluc_my_name();                                           /* each round: the Steam persona may only be readable once the session runs */
        memset(kluc.names, 0, sizeof kluc.names);                 /* table indices belong to the round: peers re-announce every 5 s */
        klog("ucc: UCC round, role %lu (%s), state 0x%lx; my name '%s' (%s)%s", (unsigned long)role, role == 2 ? "HOST" : "client", (unsigned long)state,
             kluc.myName[0] ? kluc.myName : "Player <n>", kluc.nameFrom == 0 ? "[Ucc] Name" : kluc.nameFrom == 1 ? "Steam persona" : "fallback",
             role == 2 && kluc.pings ? "; first ping in PingMinS" : "");
    }
    if (now - kluc.passAt >= 250) {                               /* the table and my own entry, 4 times a second */
        DWORD pl = 0; int how = 0;
        kluc.passAt = now;
        if (klco_table(sm, &kluc.ents, &kluc.n)) {
            int idx = klco_find_own(kluc.ents, kluc.n, now, &pl, &how);
            if (idx != kluc.own) { if (kluc.log) klog("ucc: my entry in the player table: %d of %d (%s)", idx, kluc.n, how == 1 ? "gamedata slot" : how == 2 ? "master scan" : "not found"); kluc.own = idx; }
            kluc.ownEnt = idx >= 0 ? pl : 0;
        } else { kluc.n = 0; kluc.own = -1; kluc.ownEnt = 0; }
        if (kluc.own >= 0 && (!kluc.helloAt || now - kluc.helloAt >= 5000)) {
            char p[KLUC_NAME + 8];
            kluc.helloAt = now;
            snprintf(p, sizeof p, "%d|%s", kluc.own, kluc_name_of(kluc.own));
            knc_send("HELLO", p, kluc.own);
        }
    }
    kluc_flush(now);
    if (kluc.pings && role == 2 && kluc.n && (LONG)(now - kluc.nextPing) >= 0) kluc_ping(now);
    down = kluc.accuse && kluc_keydown(kluc.key);
    if (kluc_edge(&kluc.kk, down, now)) kluc_accuse_key(now);
}
#endif /* KLUCC_C */
