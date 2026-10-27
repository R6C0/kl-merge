/*
 * klcopsquad.c - [CopSquad] AI POLICE UNDER EACH HUMAN COP IN COPS AND ROBBERS (2026-10-26; owner: "give a squad of 4 to each cop so
 * they can command 4 AI cops, like the AI heisters or like luvsic's AI"). Part of KLHook (included by klhook.c after klbotfill.c).
 * Default OFF ([CopSquad] Enable=0). NOTHING HERE HAS RUN IN THE GAME: every address below was read in kl2.exe (re/cop_squads.md),
 * every convention is marked VERIFIED (disassembled) or GUESS. No code byte of kl2.exe changes: game calls, reads and the heap writes
 * the game's own functions make. Game thread only, HOST only, Cops and Robbers only (game type 4, sub-mode word [0x168e59c] == 2).
 *
 * The approach is luvsic's (third_party/anp/loader/squad.inc, github.com/luvsicccc/a-newer-perspective, READ, not linked: credit to him):
 * kl2's own ZSquadControl does the work. Each ZFFPlayer P owns one at sc = [P+0xcd0] (VERIFIED: DD's own 0x615ea5 / 0x4bcf55 read it and
 * hand it to Recruit; Follow reads [sc+4] as the player).
 *   0x908040 ZSquadControl::Recruit(sc, ZFFActor *body)  __thiscall ret 4   VERIFIED: sc+0xcc = 1; script = [body+0x77c]; script->vt[0x1b0]
 *            (SetOwner, handle of [sc+4]); receivers sc+0x1c[sc+0x18], stops at 16, NO duplicate test; then 0x7b3490(sc, body) adds him
 *            to the player squad. DD itself calls it from the soldier init 0x615c90 and from 0x6bb4c0 (ZFFGameData slot 13).
 *   0x4c3900 ZSquadControl::Follow(sc, char all)         __thiscall ret 4   VERIFIED head: busy test 0x6a88f0([sc+4]); [sc+0xa0] refusal ->
 *            0x6eac60(sc, 7, 0x2f); needs [sc+0x18] >= 1; all=0 needs a current receiver [sc+0x10]; bumps [sc+8]; gesture 7 to [P+0x840].
 *   ZSoldier@CPPScript (vt 0xbd0954) slot 79 vt+0x13c = 0x760e50 MoveTo(pos[3], char soft, char reset, int) ret 0x10   VERIFIED (klescort.c
 *            proves it live offline); it RETURNS on a client (0x863a60 && 0x4b0a40): the host is the only place these orders exist.
 *   ZSoldier slot 83 vt+0x14c = 0x831850 Attack(DWORD handle_or_0, const float pos[3], float T) ret 0xc   VERIFIED head (0x8ccde0 resolves the
 *            handle, kept at [script+0x720]).
 * DISPROVED (brief): "0x6f64f9 streams the Attack handle over the network" - 0x6f64f9 is inside 0x6f6240, a generic script-call dispatcher
 * ("Glacier.dlc", reads arguments from a stream and calls vtable slots): not netcode. Orders do NOT replicate as orders; the clients see the
 * soldiers move through the ordinary DDL_ZFFActor replication (the same path the stock AI cops take online). GUESS until the bench shows it.
 *
 * WHO: a human cop = an entry of the session player table (0x6161c0(sm): 12-byte entries, ZFFPlayer* at +4, used byte at +9 - the table
 * DD's own picker 0x6ee860 walks) whose player is a ZFFPlayer (vt 0xbb45f4), type byte [P+0x273c] == 3 (policeman) and used == 1.
 * GUESS: the C&R team split marks a human cop's entry used the way the FA death path does (0x6ee8ce writes 1). The log says how many.
 * SOLDIERS: ZFFActors (vt 0xbb3bac) of team value [[actor+0x54]+4] == Team (3 = the cops, klsync.c's S2b measurement, GUESS), alive,
 * whose ZSoldier [actor+0x77c] has vt 0xbd0954 and [script+0x40] == actor, [actor+0x576] == 1 (takes orders, klescort.c), node flag bit 10
 * clear, not yet a receiver of any cop's squad control, within MaxM metres of the cop: the nearest Per of them are recruited, once per
 * cop per round. They come from the level's own police squads (bots_online_fill.md 1: squads of mask eAllTypes survive the C&R filter at
 * 0x7b382c, those of eFragileAllianceUCC do not): no new actor is made, so the 12 client seats are untouched (AI has no seat).
 * ORDERS: only the LOCAL player's squad takes key orders (the host reads its own keyboard; a remote cop's keys never reach the host: a UDP
 * order channel in klcharonline.c's pattern is the next step, NOT built). Every cop's squad gets Follow(all) at recruit time and again
 * every FollowS seconds (the chain's own steps may overwrite the order). Keys (game window in front, GetAsyncKeyState, NOT consumed):
 * F (0x46) follow, G (0x47) hold where they stand (MoveTo each soldier's own place, not soft, reset), H (0x48) attack what I aim at
 * (handle [[P+0xbd4]+0x2ac], point P+0x27b0: VERIFIED 2026-10-26 static review, re/cop_squads.md 8: [P+0xbd4] is the player's 0x430-byte
 * aim helper made in 0x60a520; its per-frame method 0x86a9c0 stores 0x8fcb50(3) at +0x2ac, and 0x8fcb50 returns 0x6ece90(nearest actor
 * in the aim cone) = a HANDLE or 0; P+0x27b0 is written by the same method's caller 0x4677c0 while the aim bit 2 of [P+0x2720] is set,
 * and by the setter 0x724a10. A stale handle resolves to 0 in 0x40a880 (generation word), so handle 0 = attack the point is the fallback).
 * WHAT FOLLOW ORDERS (VERIFIED in 0x4c3900 / 0x848460): Follow(all) walks the PLAYER SQUAD [sc+0xa4] (members at +0xc0 count / +0xc4[12],
 * cap 12 in 0x48c480), NOT the receiver list sc+0x1c, and takes a member only when 0x6c8510 passes: [script+0x4f4] == the player squad
 * (0x48c480 sets it), [script+0x6a4] != 0 (commandable, 1 from the ZSoldier constructor 0x761900), [body+0x576] == 1, body vt+0x680() false.
 * So a recruit COUNTS here only when the receiver list AND the squad pointer took it ("listed 1 insquad 1" in the log).
 * GUARDS: no __try (the hook's pattern, klescort.c): every object is read with klh_rd first, every routine's head bytes are compared
 * (klb_same_code) and the vtable slots must hold the known addresses, or nothing is called and the log says why.
 *
 * KLHook.ini
 *   [CopSquad]
 *   Enable=0        1 = on (host, C&R only)
 *   Per=4           soldiers per human cop, 1..8
 *   Team=3          the team value of the police actors (GUESS 3)
 *   FollowS=8       seconds between Follow re-issues (0 = only at recruit time)
 *   MaxM=40         a soldier farther than this from the cop is not recruited (metres)
 *   AttackT=5       the time argument of Attack (seconds, luvsic's default)
 *   KeyFollow=0x46 KeyHold=0x47 KeyAttack=0x48   virtual-key codes (0 = unbound)
 *   Log=1           0 quiet, 1 events, 2 + every refusal
 */
#ifndef KLCOPSQUAD_C
#define KLCOPSQUAD_C
#include "klcopsquad_logic.h"

#define KLCQ_RECRUIT    0x00908040u
#define KLCQ_FOLLOW     0x004c3900u
#define KLCQ_ATTACK     0x00831850u
#define KLCQ_TABLE      0x006161c0u          /* session player table accessor (klcharonline.c KLCO_GETHERO_TABLE) */
#define KLCQ_SUBMODE    0x0168e59cu          /* 0 FA, 1 UCC, 2 C&R (re/cops_and_robbers.md) */
#define KLCQ_PLAYER_VT  0x00bb45f4u
#define KLCQ_SC_VT      0x00b798dcu          /* ZSquadControl (RTTI) */

struct klcq_cop { DWORD P, sc; int n, local; DWORD sold[KLCQ_PER_MAX]; DWORD followAt; int staffed, tries; };
#define KLCQ_TRIES_MAX 40                    /* recruit passes (500 ms apart) a cop with no recruit gets before the round gives up on him: ~20 s */
static struct {
    int on, per, team, log, attackT, kF, kH, kA; unsigned long followMs; float maxd2;
    int inwin, toldGate, toldHead, nopick; DWORD passAt, roundAt; int ncop; struct klcq_cop cop[KLCQ_COPS_MAX];
    struct klcq_key keyF, keyH, keyA; int calls, dead;
    SHORT (WINAPI *aks)(int); HWND (WINAPI *fgw)(void); DWORD (WINAPI *wtp)(HWND, LPDWORD);
} klcq;

static void klcq_init(void)
{
    HMODULE u;
    klcq.on = GetPrivateProfileIntA("CopSquad", "Enable", 0, klh_ini) != 0;
    klcq.per = klcq_clamp_per(GetPrivateProfileIntA("CopSquad", "Per", 4, klh_ini));
    klcq.team = GetPrivateProfileIntA("CopSquad", "Team", 3, klh_ini);
    klcq.followMs = klcq_clamp_follow_ms(GetPrivateProfileIntA("CopSquad", "FollowS", 8, klh_ini));
    klcq.maxd2 = klcq_maxd2(GetPrivateProfileIntA("CopSquad", "MaxM", 40, klh_ini));
    klcq.attackT = GetPrivateProfileIntA("CopSquad", "AttackT", 5, klh_ini); if (klcq.attackT < 1) klcq.attackT = 1; if (klcq.attackT > 60) klcq.attackT = 60;
    klcq.kF = GetPrivateProfileIntA("CopSquad", "KeyFollow", 0x46, klh_ini); klcq.kH = GetPrivateProfileIntA("CopSquad", "KeyHold", 0x47, klh_ini); klcq.kA = GetPrivateProfileIntA("CopSquad", "KeyAttack", 0x48, klh_ini);
    klcq.log = GetPrivateProfileIntA("CopSquad", "Log", 1, klh_ini);
    if (!klcq.on) return;
    if ((u = GetModuleHandleA("user32.dll")) != 0) { klcq.aks = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState"); klcq.fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); klcq.wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId"); }
    klog("copsquad: ON (NOT yet run live): per %d team %d follow %lu ms max %.0f m attackT %d keys F/H/A %#x/%#x/%#x%s", klcq.per, klcq.team, klcq.followMs, (double)sqrt((double)klcq.maxd2) / 100.0, klcq.attackT, klcq.kF, klcq.kH, klcq.kA, klcq.aks ? "" : " (no GetAsyncKeyState: keys off)");
}

/* ---- the three code heads this module calls through (read in kl2.exe 0490; a mismatch = nothing is ever called) ---- */
static int klcq_heads(void)
{
    static const BYTE rec[6] = { 0x83, 0xec, 0x0c, 0x55, 0x8b, 0x6c }, fol[6] = { 0x83, 0xec, 0x24, 0x56, 0x8b, 0xf1 }, atk[6] = { 0x55, 0x8b, 0xec, 0x51, 0x53, 0x56 };
    static const BYTE mov[16] = { 0x55, 0x8b, 0xec, 0x83, 0xec, 0x0c, 0x56, 0x8b, 0xf1, 0x8b, 0x0d, 0x98, 0xe5, 0x68, 0x01, 0xe8 };
    if (!klh_exe_ok) return 0;
    if (!klb_same_code(KLCQ_RECRUIT, rec, 6) || !klb_same_code(KLCQ_FOLLOW, fol, 6) || !klb_same_code(KLCQ_ATTACK, atk, 6) || !klb_same_code(KLE_ORDER, mov, 16)) return 0;
    if (klh_rd32((DWORD_PTR)KLH_VA(KLE_SOLDIER_VT + 0x13c)) != KLE_ORDER || klh_rd32((DWORD_PTR)KLH_VA(KLE_SOLDIER_VT + 0x14c)) != KLCQ_ATTACK) return 0;
    return 1;
}
/* the human cops of the session player table (see the header; GUESS: used byte +9 marks a human's entry) */
static int klcq_cops(DWORD sm)
{
    DWORD tbl, e; int i, n = 0, cnt = 0;
    if (!klh_rd32(sm + 4) || !(tbl = ((DWORD (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLCQ_TABLE))((void *)(DWORD_PTR)sm, 0)) || !(e = klh_rd32(tbl)) || (cnt = (int)klh_rd32(tbl + 0xc)) <= 0) return 0;
    if (cnt > 16) cnt = 16;
    for (i = 0; i < cnt && n < KLCQ_COPS_MAX; i++) {
        DWORD P = klh_rd32(e + 12 * i + 4), sc; BYTE used = 0, type = 0; int j;
        if (!P || klh_pvt(P) != KLCQ_PLAYER_VT || !klh_rd(P + 0x273c, &type, 1) || type != 3 || !klh_rd(e + 12 * i + 9, &used, 1)) continue;
        /* GUESS (section 3 of re/cop_squads.md): used == 1 marks a human's entry. The table reset 0x56f360 clears +9 AND the entry's first
           word (+0, an owner object it hands to 0x54c380(sm, ...)) together, so +0 != 0 is the other candidate mark: logged for the bench. */
        if (klcq.log >= 2) klog("copsquad: table entry %d: policeman player %08lx used %d owner word %08lx", i, (unsigned long)P, used, (unsigned long)klh_rd32(e + 12 * i));
        if (!used) continue;
        if (!(sc = klh_rd32(P + 0xcd0)) || klh_rd32(sc) != KLCQ_SC_VT || klh_rd32(sc + 4) != P) { if (klcq.log >= 2) klog("copsquad: cop entry %d: [P+0xcd0] is no ZSquadControl of this player", i); continue; }
        for (j = 0; j < klcq.ncop && klcq.cop[j].P != P; j++) ;
        if (j == klcq.ncop) { memset(&klcq.cop[j], 0, sizeof klcq.cop[j]); klcq.cop[j].P = P; klcq.cop[j].sc = sc; klcq.ncop++; }
        n++;
    }
    return n;
}
static int klcq_feet(DWORD P, float f[3]) { return klh_rd(P + 0x460, f, 12) && klb_finite(f[0]) && klb_finite(f[1]) && klb_finite(f[2]); }
static int klcq_is_receiver(DWORD actor)                      /* of ANY cop's squad control this module knows */
{
    int j, k; DWORD s = klh_rd32(actor + 0x77c);
    for (j = 0; j < klcq.ncop; j++) {
        DWORD n = klh_rd32(klcq.cop[j].sc + 0x18); if (n > 16) n = 16;
        for (k = 0; k < (int)n; k++) if (klh_rd32(klcq.cop[j].sc + 0x1c + 4 * k) == s) return 1;
    }
    return 0;
}
/* a police soldier that can be recruited and ordered now (klescort.c kle_bot's tests, without the crew record) */
static DWORD klcq_soldier(DWORD actor)
{
    DWORD node, s, fl = 0, h, held = 1; BYTE b = 0; float hv[2] = { 0, 0 }; int team = -1;
    if (klh_rd32(actor) != KLB_ACTOR_VT) return 0;
    if (!(h = klh_rd32(actor + 0x54)) || !klh_rd(h + 4, &team, 4) || team != klcq.team) return 0;
    if (!(h = klh_rd32(actor + 0x5fc)) || !klh_rd(h + 4, hv, 8) || hv[0] <= 0) return 0;
    if (!(node = klh_rd32(actor + 4)) || !klh_rd(node + 0x3c, &fl, 4) || (fl >> 10 & 1)) return 0;
    if (!klh_rd(actor + 0x576, &b, 1) || b != 1 || !klh_rd(actor + 0x770, &held, 4) || held) return 0;
    if (!(s = klh_rd32(actor + 0x77c)) || klh_rd32(s) != KLE_SOLDIER_VT || klh_rd32(s + 0x40) != actor) return 0;
    if (!klh_rd32(s + 0x63c) || !klh_rd32(s + 0x738) || !klh_rd32(s + 0x6d8)) return 0;      /* 0x4c3b10 (SetOwner) dereferences +0x63c / +0x738, 0x48c480 (squad add) [+0x6d8]: VERIFIED, unchecked there */
    if (!klh_rd(s + 0x6a4, &b, 1) || !b) return 0;                                             /* commandable: Follow's member test 0x6c8510 skips a soldier with 0 here (set 0 by 0x6bf452 / 0x8fd4b8) */
    return s;
}
static void klcq_follow(struct klcq_cop *c, DWORD now, const char *why)
{
    DWORD nr = klh_rd32(c->sc + 0x18); BYTE busy = 0;
    c->followAt = now ? now : 1;
    if (!nr || nr > 16) return;
    ((void (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(KLCQ_FOLLOW))((void *)(DWORD_PTR)c->sc, 0, 1); klcq.calls++;
    klh_rd(c->sc + 0xa0, &busy, 1);
    if (klcq.log) klog("copsquad: cop %08lx Follow(all) %s: %lu receivers, order no. %lu, refusal flag %d", (unsigned long)c->P, why, (unsigned long)nr, (unsigned long)klh_rd32(c->sc + 8), busy);
}
static void klcq_recruit(struct klcq_cop *c, DWORD now)
{
    struct klcq_cand cand[KLCQ_CAND_MAX]; DWORD out[KLCQ_PER_MAX], p, tab, i, nr0, sq; float cf[3]; int n = 0, k, got = 0;
    /* a pass that recruits nobody is retried (the police squads spawn through the round; the first pass is 10 s in) up to KLCQ_TRIES_MAX */
    if (++c->tries >= KLCQ_TRIES_MAX) c->staffed = 1;
    if (!(sq = klh_rd32(c->sc + 0xa4))) { c->staffed = 1; klog("copsquad: cop %08lx: squad control %08lx has no player squad (+0xa4): no recruit (0x7b3490 would read it unchecked)", (unsigned long)c->P, (unsigned long)c->sc); return; }
    if (!klcq_feet(c->P, cf)) { if (klcq.log >= 2) klog("copsquad: cop %08lx: no feet yet: no recruit this pass", (unsigned long)c->P); return; }
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return;
    for (i = 0; i < 0x4000u && n < KLCQ_CAND_MAX; i += 64) {                 /* the scene's entity table, 128-byte slots (klsync.c klsy_walk) */
        DWORD blk[64 * 32], j;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (j = 0; j < 64 && n < KLCQ_CAND_MAX; j++) {
            DWORD o = blk[j * 32 + 0x60 / 4]; float ap[3];
            if (o < 0x10000 || !klcq_soldier(o) || klcq_is_receiver(o) || !kle_node(klh_rd32(o + 4), ap, 0)) continue;
            cand[n].id = o; cand[n].taken = 0; cand[n].d2 = (ap[0] - cf[0]) * (ap[0] - cf[0]) + (ap[1] - cf[1]) * (ap[1] - cf[1]) + (ap[2] - cf[2]) * (ap[2] - cf[2]); n++;
        }
    }
    k = klcq_pick(cand, n, klcq.per, klcq.maxd2, out);
    if (!k) { if (c->staffed || klcq.log >= 2) klog("copsquad: cop %08lx: %d police soldiers seen, none free within range%s", (unsigned long)c->P, n, c->staffed ? ": no squad this round" : " (pass retried)"); return; }
    c->staffed = 1;
    for (i = 0; i < (DWORD)k; i++) {
        DWORD s = klh_rd32(out[i] + 0x77c), nr1; int listed = 0, insquad, q; float d2 = -1;
        for (q = 0; q < n; q++) if (cand[q].id == out[i]) d2 = cand[q].d2;
        nr0 = klh_rd32(c->sc + 0x18); if (nr0 >= 16) { klog("copsquad: cop %08lx: squad control full (16 receivers)", (unsigned long)c->P); break; }
        if (klh_rd32(sq + 0xc0) >= 12) { klog("copsquad: cop %08lx: player squad full (12 members): 0x7b3490 would drop the add", (unsigned long)c->P); break; }
        if (klcq_is_receiver(out[i])) continue;                                          /* 0x908040 has no duplicate test */
        ((void (__fastcall *)(void *, void *, void *))(DWORD_PTR)KLH_VA(KLCQ_RECRUIT))((void *)(DWORD_PTR)c->sc, 0, (void *)(DWORD_PTR)out[i]); klcq.calls++;
        nr1 = klh_rd32(c->sc + 0x18); if (nr1 > 16) nr1 = 16;
        for (q = 0; q < (int)nr1; q++) if (klh_rd32(c->sc + 0x1c + 4 * q) == s) listed = 1;
        insquad = klh_rd32(s + 0x4f4) == sq;                                             /* 0x48c480 moved his squad pointer: what Follow(all) walks */
        if (klcq.log) klog("copsquad: cop %08lx recruit actor %08lx script %08lx at %.1f m: receivers %lu -> %lu, listed %d, insquad %d (members %lu), owner %08lx", (unsigned long)c->P, (unsigned long)out[i], (unsigned long)s, d2 < 0 ? -1.0 : (double)sqrt((double)d2) / 100.0, (unsigned long)nr0, (unsigned long)nr1, listed, insquad, (unsigned long)klh_rd32(sq + 0xc0), (unsigned long)klh_rd32(s + 0x69c));
        if (listed && insquad && c->n < KLCQ_PER_MAX) c->sold[c->n++] = out[i];
        got += listed && insquad;
    }
    klog("copsquad: cop %08lx%s: %d of %d recruited (%d candidates seen, pass %d)", (unsigned long)c->P, c->local ? " (local)" : "", got, k, n, c->tries);
    if (got) klcq_follow(c, now, "after recruit");
}
/* the local player's cop record, if the host itself plays a cop (gd+0x828+4*[gd+0x898], the slot method of klescort.c kle_human) */
static struct klcq_cop *klcq_local(void)
{
    DWORD gd, pl; BYTE sel = 0xff; int j;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel > 3 || !(pl = klh_rd32(gd + 0x828 + 4 * sel))) return 0;
    for (j = 0; j < klcq.ncop; j++) if (klcq.cop[j].P == pl) { klcq.cop[j].local = 1; return &klcq.cop[j]; }
    return 0;
}
static int klcq_key(int vk)
{
    HWND fg; DWORD pid = 0;
    if (!vk || !klcq.aks || !klcq.fgw || !klcq.wtp || !(fg = klcq.fgw())) return 0;
    klcq.wtp(fg, &pid);
    return pid == GetCurrentProcessId() && (klcq.aks(vk) & 0x8000) != 0;
}
static void klcq_order(struct klcq_cop *c, int order, DWORD now)
{
    int i, done = 0; float aim[3]; DWORD h = 0, a;
    if (order == 1) { klcq_follow(c, now, "key"); return; }
    if (order == 3) {                                                     /* VERIFIED (header): aim point P+0x27b0, aimed-actor handle [[P+0xbd4]+0x2ac] (0 = none, stale = resolves to nothing) */
        if (!klh_rd(c->P + 0x27b0, aim, 12) || !klb_finite(aim[0]) || !klb_finite(aim[1]) || !klb_finite(aim[2])) { klog("copsquad: attack: no aim point"); return; }
        if ((a = klh_rd32(c->P + 0xbd4)) != 0) h = klh_rd32(a + 0x2ac);
    }
    for (i = 0; i < c->n; i++) {
        DWORD actor = c->sold[i], s = klcq_soldier(actor); float p[4];
        if (!s || !klcq_is_receiver(actor)) continue;
        if (order == 2) {                                                 /* hold: MoveTo his own place, not soft, reset (klescort.c's arguments) */
            if (!kle_node(klh_rd32(actor + 4), p, 0)) continue; p[3] = 0;
            ((void (__fastcall *)(void *, void *, const float *, int, int, int))(DWORD_PTR)KLH_VA(KLE_ORDER))((void *)(DWORD_PTR)s, 0, p, 0, 1, 0);
        } else {
            float T = (float)klcq.attackT;
            ((void (__fastcall *)(void *, void *, DWORD, const float *, float))(DWORD_PTR)KLH_VA(KLCQ_ATTACK))((void *)(DWORD_PTR)s, 0, h, aim, T);
        }
        klcq.calls++; done++;
    }
    if (klcq.log) klog("copsquad: key order %s: %d of %d soldiers%s", order == 2 ? "HOLD" : "ATTACK", done, c->n, order == 3 ? (h ? " (at the aimed actor)" : " (at the aim point: no target handle)") : "");
}

static void klcq_tick(int game_thread)
{
    DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0, sub = 0; int j, vk = 0;
    if (!klcq.on || !game_thread || !klh_exe_ok || klcq.dead) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm)) || !klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4) || !klh_rd((DWORD_PTR)KLH_VA(KLCQ_SUBMODE), &sub, 4)
        || !klcq_gate(role, mode, state, sub)) { klcq.inwin = 0; klcq.ncop = 0; return; }
    if (!klcq.inwin) {
        klcq.inwin = 1; klcq.ncop = 0; klcq.roundAt = now; klcq.passAt = 0;
        memset(&klcq.keyF, 0, sizeof klcq.keyF); memset(&klcq.keyH, 0, sizeof klcq.keyH); memset(&klcq.keyA, 0, sizeof klcq.keyA);
        if (!klcq_heads()) { if (!klcq.toldHead++) klog("copsquad: a routine (0x908040 / 0x4c3900 / 0x831850 / 0x760e50) or a ZSoldier vtable slot is not the one this build knows: NOTHING is called"); klcq.dead = 1; return; }
        klog("copsquad: round on the host, C&R (state 0x%lx): human cops are staffed %d s after the start", (unsigned long)state, 10);
    }
    if (now - klcq.passAt < 500) goto keys;                                 /* two passes a second */
    klcq.passAt = now;
    if (now - klcq.roundAt < 10000) return;                                 /* GUESS: 10 s for the team placement and the police squads to be up (Timer_start_bots is 10 s) */
    if (!klcq_cops(sm)) { if (klcq.log >= 2) klog("copsquad: no human cop in the session table yet"); return; }
    for (j = 0; j < klcq.ncop; j++) {
        struct klcq_cop *c = &klcq.cop[j];
        if (!c->staffed) klcq_recruit(c, now);
        else if (c->n && klcq.followMs && klcq_due(c->followAt, now, klcq.followMs)) klcq_follow(c, now, "re-issue");
    }
keys:
    if (klcq_edge(&klcq.keyF, klcq_key(klcq.kF), now)) vk = klcq.kF;
    if (klcq_edge(&klcq.keyH, klcq_key(klcq.kH), now)) vk = klcq.kH;
    if (klcq_edge(&klcq.keyA, klcq_key(klcq.kA), now)) vk = klcq.kA;
    if (vk) {
        struct klcq_cop *c = klcq_local(); int order = klcq_order_of(vk, klcq.kF, klcq.kH, klcq.kA);
        if (!c || !c->n) { if (klcq.log) klog("copsquad: key %#x: the local player leads no squad (%s)", vk, c ? "nobody recruited" : "not a cop of the table"); return; }
        klcq_order(c, order, now);
    }
}
#endif /* KLCOPSQUAD_C */
