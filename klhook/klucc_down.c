/*
 * klucc_down.c - [Ucc] DownOnly: while the undercover cop (UCC) is hidden, his hits on heisters can only DOWN them, never kill them
 * (owner rule P7, re/ucc_design.md "OWNER DECISIONS" 2: 'you can tell he's not trying to kill, just harm'). Part of KLHook (included by
 * klhook.c AFTER klroundkeep.c and klnetsmooth.c, whose private vtables it shares / recognises). 2026-10-26, built, NOT run live.
 * Research, every address and what is a GUESS: re/ucc_down_only.md.
 *
 * WHERE A HIT ON A HUMAN IS DECIDED (kl2.exe 0490, read statically; CERTAIN unless marked):
 *   the shooter's PC prices the bullet and sends it: ZFFPlayer slot 422 (0x7e1700) packs [rec+0x28] / [rec+0x2c] and sends RMCReceiveHit
 *   (0x7a8410 -> 0x891490 -> 0x713180). The VICTIM's own PC (the master of his DDL_ZFFPlayer, 0x9425a0) rebuilds the record (0x8914f1..)
 *   and runs slot 423 = 0x458880 on his player: the down trigger 0x8da3b0 (0x458e7f), then the health change 0x6e3400(victim, -damage,
 *   attacker) (0x458ea8). 0x6e3400 calls, BEFORE it subtracts (0x8a7c60 at 0x6e361a), the rules hook 0x83ad70 -> rules vtable slot 15
 *   (+0x3c) = 0x425320(victim, &delta, attacker) on both FA rules classes (Sv 0xbd2eb4, Cl 0xbd31e4): THE DELTA IS PASSED BY POINTER.
 *   So: the victim's PC decides health and death, and a private copy of the rules object's vtable with slot 15 wrapped can bound the
 *   delta of one attacker on one victim before the game subtracts it. No code byte is touched; the rules vtable copy is the pattern of
 *   klroundkeep.c (which this file shares on the host when it is active).
 *
 * WHAT IT DOES (DownOnly=1): in an Undercover Cop round (game type 4, sub-mode [0x168e59c] == 1), when slot 15 is asked about a hit whose
 *   attacker is the UCC (player byte +0x2729, net flag bit 8 or score flag 0x80) and is not revealed (the reveal key, P6, is not built:
 *   klud_reveal() is its hook-in, until then he is hidden all round), and whose victim is a heister: the delta is clamped so the victim
 *   keeps at least Floor health. A downed (lying / getting up) heister then takes the hit but cannot die of it; a standing one at low
 *   health is left at Floor, where the game's OWN down rule floors him on the next burst (4 hits of 20+ within 1 s under 20 %, T+0x27c).
 *   DownOnly=2: as 1, and a hit that WOULD have killed a standing heister asks the game's down trigger 0x8da3b0 (kind 9, like klcdying.c)
 *   on the next game-thread tick, for at most ForceSecs: he goes down at once (GUESS: the call is untried online; klcdying's is untried too).
 *   Hits by anyone else (police AI, cops, traitors) are untouched: they can still finish him.
 *
 * KLHook.ini
 *   [Ucc]
 *   DownOnly=0      0 = stock. 1 = a hidden UCC's hits never take a heister under Floor. 2 = 1 + a would-be kill floors him (game's trigger).
 *   Floor=1         least health a UCC hit leaves (game health units; the FA player has 550, Arcade [Balance] Risk lowers it)
 *   ForceSecs=2.5   DownOnly=2: how long the down is asked (every 100 ms) after a would-be kill
 *   Dry=0           1 = log what it would do, change nothing (the vtable copy is still installed so the asks are seen)
 *   Log=1           2 = every clamped hit
 *   EVERY heister's PC needs the same key: the clamp runs where the victim is master (his own PC). A heister without it dies as stock.
 */
#ifndef KLUCC_DOWN_C
#define KLUCC_DOWN_C

#include "klucc_down_logic.h"

#define KLUD_SUBMODE    0x0168e59cu          /* 0 FA, 1 UCC, 2 C&R */
#define KLUD_GAMESET    0x0168e9e4u          /* [+0x54] the rules object, [+0x58] 'rules hooks on' (0x83ad70) */
#define KLUD_SV_VT      0x00bd2eb4u          /* ZGameRulesFragileAllianceSv */
#define KLUD_CL_VT      0x00bd31e4u          /* ZGameRulesFragileAllianceCl */
#define KLUD_SLOT       15                   /* rules vtable +0x3c: 0x425320(victim, float *delta, attacker), ret 0xc */
#define KLUD_SLOT_FN    0x00425320u
#define KLUD_NSLOT      260                  /* as klroundkeep.c */
#define KLUD_PLAYER_VT  0x00bb45f4u          /* ZFFPlayer */
#define KLUD_TRIG       0x008da3b0u          /* the human down trigger (D, hit record), thiscall ret 4 (re/player_down.md 1) */
#ifndef KLUD_TRIG_CALL
#define KLUD_TRIG_CALL(d, rec) ((BYTE (__fastcall *)(void *, void *, void *))(DWORD_PTR)KLH_VA(KLUD_TRIG))((void *)(DWORD_PTR)(d), 0, (void *)(rec))
#endif

static struct { int on, mode, dry, log, pre; float floor, force_secs; } klud;
/* TRACK DAMAGE (2026-10-26, small separate hook): this wrapper is also the carrier of kldown.c's OnlinePreScale. kld_o_prescale(victim, &delta, attacker) (kldown.c, included AFTER this file, hence
   the forward declaration) prices a hit on this machine's own knocked-down body BEFORE the game subtracts it - the same slot-15 call, FA / UCC / C&R alike (the rules classes are the same
   Sv / Cl). klud.pre = [Down] Enable=1 + Online=1 + OnlinePreScale=1 (read here because klud_init runs before kld_init); klud.mode = [Ucc] DownOnly as before. Either one installs the table. */
static void kld_o_prescale(DWORD victim, float *pdelta, DWORD attacker);
static DWORD klud_sv[1 + KLUD_NSLOT], klud_cl[1 + KLUD_NSLOT];       /* [0] = RTTI locator, [1..] = slots */
static DWORD klud_rules, klud_wait0;                                /* the rules object seen last, when we began waiting for klroundkeep */
static unsigned long klud_revealed;                                 /* one bit per crew index: revealed UCCs (P6 sets it; nothing does yet) */
static LONG klud_n_ask, klud_n_ucc, klud_n_clamp, klud_n_lethal;
static struct { DWORD victim, t0, last; int tries, done; } klud_pend;

/* P6's hook-in: the reveal key (not built) calls this on every peer when crew index idx shows himself */
static void klud_reveal(int idx, int on)
{
    if (idx < 0 || idx > 31) return;
    if (on) klud_revealed |= 1ul << idx; else klud_revealed &= ~(1ul << idx);
}

static int klud_is_player(DWORD p)
{
    DWORD vt;
    if (p < 0x10000 || !(vt = klh_rd32(p))) return 0;
    return vt == (DWORD)(DWORD_PTR)KLH_VA(KLUD_PLAYER_VT) || vt == kns_ours();      /* klnetsmooth.c gives REMOTE players a private copy */
}

/* the crew index of a player: (signed char)(byte [[P+0x2748] + 0xdc] ^ 0xac) (0x8e8010 -> 0x5b1400); -1 = none */
static int klud_idx(DWORD p)
{
    DWORD c = klh_rd32(p + 0x2748); BYTE b = 0;
    if (!c || !klh_rd(c + 0xdc, &b, 1)) return -1;
    return (int)(signed char)(BYTE)(b ^ 0xac);
}

/* the score flags of crew index i, read as rules slot 114 (0x625be0) does; 0 when not in use / unreadable */
static unsigned long klud_flags(DWORD rules, int i)
{
    DWORD n = 0, fr, sc, f = 0; BYTE used = 1;
    if (i < 0 || !klh_rd(rules + 0x14, &n, 4) || (DWORD)i >= n || n > 16) return 0;
    if (!(fr = klh_rd32(rules + 0xc)) || !klh_rd(fr + i, &used, 1) || used) return 0;
    if (!(sc = klh_rd32(rules + 0x2c)) || !klh_rd(sc + 0x98 + 4 * i, &f, 4)) return 0;
    return f;
}

/* m_iFlags of the player's net object (word [[P+0x274c]+0x4c4] ^ 0xdead, 0x8c95e9 / 0x431f60); 0 offline / unreadable */
static unsigned short klud_netflags(DWORD p)
{
    DWORD net = klh_rd32(p + 0x274c); WORD w = 0;
    if (!net || !klh_rd(net + 0x4c4, &w, 2)) return 0;
    return (unsigned short)(w ^ 0xdead);
}

static int klud_local(DWORD *me)
{   /* the game's own local player: [gd + 0x828 + 4 * byte [gd + 0x898]] (klcam.c / klnetsmooth.c) */
    DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(0xdd265c)); BYTE sel = 0xff;
    *me = 0;
    if (!gd || !klh_rd(gd + 0x898, &sel, 1) || sel >= 28) return 0;
    *me = klh_rd32(gd + 0x828 + 4 * sel);
    return *me != 0;
}

static float klud_rdf(DWORD a, int *ok) { float f = 0; if (!klh_rd(a, &f, 4)) *ok = 0; return f; }

/* the decision for one hit (game thread, inside the game's 0x6e3400) */
static void klud_filter(DWORD rules, DWORD victim, float *pdelta, DWORD attacker)
{
    DWORD sm, mode = 0, sub = 0, ho, D; int ia, iv, ok = 1; BYTE a29 = 0, v23 = 0, v29 = 0; float d, h, nd; DWORD ds = 0;
    unsigned long fa, fv;
    InterlockedIncrement(&klud_n_ask);
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd((DWORD_PTR)KLH_VA(KLUD_SUBMODE), &sub, 4)) return;
    if (!klud_gate(mode, sub)) return;
    if (!klud_is_player(attacker) || !klud_is_player(victim)) return;
    ia = klud_idx(attacker); iv = klud_idx(victim);
    fa = klud_flags(rules, ia); fv = klud_flags(rules, iv);
    klh_rd(attacker + 0x2729, &a29, 1); klh_rd(victim + 0x2723, &v23, 1); klh_rd(victim + 0x2729, &v29, 1);
    if (!klud_is_ucc(a29, klud_netflags(attacker), fa) || !klud_hidden(ia, klud_revealed)) return;
    InterlockedIncrement(&klud_n_ucc);
    if (!klud_is_heister(v23, v29, klud_netflags(victim), fv)) return;
    if (!(ho = klh_rd32(victim + 0xa48))) return;
    h = klud_rdf(ho + 4, &ok);
    if (!ok || !klh_rd((DWORD_PTR)pdelta, &d, 4)) return;
    nd = klud_clamp(d, h, klud.floor);
    if ((D = klh_rd32(victim + 0x2948)) && klh_rd32(D) == victim) klh_rd(D + 4, &ds, 4);
    if (nd == d) {
        if (klud.log >= 2) klog("uccdown: UCC (crew %d) hits heister (crew %d) for %.1f at health %.1f%s: not a would-be kill, passed unchanged", ia, iv, -d, h, ds ? " (DOWN)" : "");
        return;
    }
    {
        int lethal = klud_lethal(d, h, klud.floor), n = (int)InterlockedIncrement(&klud_n_clamp);
        if (lethal) InterlockedIncrement(&klud_n_lethal);
        if (klud.log >= 2 || n <= 30)
            klog("uccdown: UCC (crew %d) hits heister %08lx (crew %d, %s) for %.1f at health %.1f -> %.1f%s%s", ia, (unsigned long)victim, iv,
                 ds ? "DOWN" : "standing", -d, h, -nd, lethal ? " - a would-be KILL, kept alive" : "", klud.dry ? " (Dry: NOT written)" : "");
        if (!klud.dry) {
            if (!klh_data(pdelta, &nd, 4, "uccdown: the damage delta of one UCC hit (game stack)")) return;
            if (lethal && klud.mode == 2 && !ds) {
                DWORD me = 0;
                if (klud_local(&me) && me == victim && (!klud_pend.victim || klud_pend.done)) {
                    klud_pend.victim = victim; klud_pend.t0 = GetTickCount(); klud_pend.last = 0; klud_pend.tries = 0; klud_pend.done = 0;
                }
            }
        }
    }
}

static DWORD __fastcall klud_w15(void *self, void *edx, DWORD victim, float *pdelta, DWORD attacker)
{
    static int told;
    if (!told) { told = 1; klog("uccdown: the rules' damage hook (slot 15) is reached - the wrapper works"); }
    if (klud.pre && pdelta && victim) kld_o_prescale(victim, pdelta, attacker);      /* kldown.c: the downed own body's price, FIRST: the UCC clamp below then sees the priced delta (it only ever raises it toward 0) */
    if (klud.mode && pdelta && victim && attacker && attacker != victim) klud_filter((DWORD)(DWORD_PTR)self, victim, pdelta, attacker);
    return ((DWORD (__fastcall *)(void *, void *, DWORD, float *, DWORD))(DWORD_PTR)KLH_VA(KLUD_SLOT_FN))(self, edx, victim, pdelta, attacker);
}

/* build one private copy from the stock table at vtva; 0 = the slot is not the function read */
static int klud_build(DWORD *blk, DWORD vtva, const char *name)
{
    if (blk[0]) return 1;
    if (!klh_rd((DWORD_PTR)KLH_VA(vtva - 4), blk, sizeof(DWORD) * (1 + KLUD_NSLOT))) return 0;
    if (blk[1 + KLUD_SLOT] != (DWORD)(DWORD_PTR)KLH_VA(KLUD_SLOT_FN)) {
        klog("uccdown: %s rules slot %d is %08lx, not the known 0x425320: left alone", name, KLUD_SLOT, (unsigned long)blk[1 + KLUD_SLOT]);
        blk[0] = 0; return 0;
    }
    blk[1 + KLUD_SLOT] = (DWORD)(DWORD_PTR)klud_w15;
    return 1;
}

static void klud_wrap(void)
{
    DWORD gs, r, vt, mine_sv = (DWORD)(DWORD_PTR)&klud_sv[1], mine_cl = (DWORD)(DWORD_PTR)&klud_cl[1], rk = (DWORD)(DWORD_PTR)&klrk_vt[1], nv = 0; int plan, wants;
    static int told_rk;
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLUD_GAMESET))) || !(r = klh_rd32(gs + 0x54)) || !(vt = klh_rd32(r))) return;
    if (r != klud_rules) { klud_rules = r; klud_wait0 = GetTickCount(); klud_revealed = 0; memset(&klud_pend, 0, sizeof klud_pend); }
#ifdef KLHOOK_TEST
    wants = 1;                                                       /* klroundkeep.c's TEST probe wraps the Sv object always */
#else
    wants = klrk_keep != 0;
#endif
    plan = klud_vt_plan(vt, (DWORD)(DWORD_PTR)KLH_VA(KLUD_SV_VT), (DWORD)(DWORD_PTR)KLH_VA(KLUD_CL_VT), rk, mine_sv, mine_cl, wants, GetTickCount() - klud_wait0);
    switch (plan) {
    case KLUD_VT_RK:                                                 /* the host with [Lobby] KeepRound: one table, both modules' slots */
        if (klrk_vt[1 + KLUD_SLOT] == (DWORD)(DWORD_PTR)KLH_VA(KLUD_SLOT_FN)) {
            klrk_vt[1 + KLUD_SLOT] = (DWORD)(DWORD_PTR)klud_w15;
            klog("uccdown: Sv rules %08lx already carries klroundkeep.c's private vtable: slot 15 added to it", (unsigned long)r);
        } else if (klrk_vt[1 + KLUD_SLOT] != (DWORD)(DWORD_PTR)klud_w15 && !told_rk) {
            told_rk = 1; klog("uccdown: klroundkeep's table has slot 15 = %08lx (not stock, not ours): left alone", (unsigned long)klrk_vt[1 + KLUD_SLOT]);
        }
        return;
    case KLUD_VT_SV:
        if (!klud_build(klud_sv, KLUD_SV_VT, "Sv")) return;
        nv = mine_sv; klh_rules_vt2 = nv;                            /* klbot.c / klbotfill.c / klnet.c accept it (KLH_RULES_SV_OK) */
        break;
    case KLUD_VT_CL:
        if (!klud_build(klud_cl, KLUD_CL_VT, "Cl")) return;
        nv = mine_cl; klh_rules_vt3 = nv;                            /* klbot.c / klnet.c accept it (KLH_RULES_CL_OK) */
        break;
    default: return;                                                 /* NONE, HAVE, WAIT */
    }
    if (klh_data((void *)(DWORD_PTR)r, &nv, 4, "uccdown: FA rules vtable (private copy, slot 15)"))
        klog("uccdown: %s rules %08lx wrapped (slot 15, the damage hook), DownOnly=%d Floor=%.1f%s", plan == KLUD_VT_SV ? "Sv" : "Cl", (unsigned long)r, klud.mode, klud.floor, klud.dry ? " Dry" : "");
}

/* DownOnly=2: ask the game's trigger for the local heister whose would-be kill was clamped */
static void klud_force(void)
{
    DWORD me = 0, D, ds = 0, ho; float hp; int ok = 1;
    if (!klud_pend.victim || klud_pend.done) return;
    if (GetTickCount() - klud_pend.t0 > (DWORD)(klud.force_secs * 1000.0f)) {
        klud_pend.done = 1; klog("uccdown: the down was refused for %.1f s (%d asks): he stays up at the floor", klud.force_secs, klud_pend.tries); return;
    }
    if (GetTickCount() - klud_pend.last < 100) return;
    klud_pend.last = GetTickCount();
    if (!klud_local(&me) || me != klud_pend.victim) { klud_pend.done = 1; return; }
    if (!(D = klh_rd32(me + 0x2948)) || klh_rd32(D) != me || !klh_rd(D + 4, &ds, 4) || !(ho = klh_rd32(me + 0xa48))) { klud_pend.done = 1; return; }
    hp = klud_rdf(ho + 4, &ok);
    if (!ok || hp <= 0.0f) { klud_pend.done = 1; return; }
    if (ds != 0) { klud_pend.done = 1; klog("uccdown: you are down (state %lu) after %d asks", (unsigned long)ds, klud_pend.tries); return; }
    {
        static BYTE rec[0x200]; BYTE yes; DWORD ds2 = 0;
        memset(rec, 0, sizeof rec); *(DWORD *)(rec + 8) = 9;         /* GUESS (klcdying.c / klcardown.c): kind 9 = a blast, skips the health and burst tests; no attacker, so no name in the feed */
        yes = (BYTE)KLUD_TRIG_CALL(D, rec);
        klh_rd(D + 4, &ds2, 4); klud_pend.tries++;
        if (klud.log >= 2 || ds2 != 0 || klud_pend.tries == 1)
            klog("uccdown: would-be kill by the UCC: the game's down trigger asked (try %d), it said %s, [D+4] %lu -> %lu", klud_pend.tries, yes ? "YES" : "NO", (unsigned long)ds, (unsigned long)ds2);
        if (ds2 != 0) klud_pend.done = 1;
    }
}

static void klud_tick(int game_thread)
{
    static DWORD last;
    if (!klud.on || !game_thread || !klh_exe_ok) return;
    if (GetTickCount() - last >= 200) { last = GetTickCount(); klud_wrap(); }
    if (klud.mode == 2 && !klud.dry) klud_force();
}

static float klud_inif(const char *key, const char *def, float lo, float hi)
{
    char t[40]; float v;
    GetPrivateProfileStringA("Ucc", key, def, t, sizeof t, klh_ini);
    v = (float)atof(t);
    if (!(v == v) || v < lo || v > hi) v = (float)atof(def);
    return v;
}

static void klud_init(void)
{
    memset(&klud, 0, sizeof klud);
    klud.mode = GetPrivateProfileIntA("Ucc", "DownOnly", 0, klh_ini);
    if (klud.mode < 0 || klud.mode > 2) klud.mode = 0;
    klud.pre = GetPrivateProfileIntA("Down", "Enable", 0, klh_ini) != 0 && GetPrivateProfileIntA("Down", "Online", 0, klh_ini) != 0 &&
               GetPrivateProfileIntA("Down", "OnlinePreScale", 1, klh_ini) != 0 &&
               (GetPrivateProfileIntA("Down", "OnlineFactors", 1, klh_ini) != 0 || GetPrivateProfileIntA("Down", "OnlineFreeFall", 1, klh_ini) != 0);
    klud.on = klud.mode != 0 || klud.pre;
    if (klud.pre) klog("uccdown: [Down] OnlinePreScale=1: the rules' damage hook (slot 15) is wrapped for kldown.c's pre-apply price of a downed own body's hits (FA / UCC / C&R online)");
    if (!klud.mode) return;
    klud.dry = GetPrivateProfileIntA("Ucc", "Dry", 0, klh_ini) != 0;
    klud.log = GetPrivateProfileIntA("Ucc", "Log", 1, klh_ini);
    klud.floor = klud_inif("Floor", "1", 0.1f, 1000.0f);
    klud.force_secs = klud_inif("ForceSecs", "2.5", 0.3f, 10.0f);
    klog("uccdown: DownOnly=%d - in Undercover Cop rounds a hidden UCC's hits leave a heister at least %.1f health%s%s (re/ucc_down_only.md)", klud.mode, klud.floor,
         klud.mode == 2 ? "; a would-be kill asks the game's down trigger" : "", klud.dry ? " - Dry: nothing written" : "");
}

#endif
