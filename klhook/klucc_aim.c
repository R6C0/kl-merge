/*
 * klucc_aim.c - [Ucc] PoliceAim: the police AI shoots a HIDDEN undercover cop (UCC) like any heister, while his own crew's AI keeps
 * treating him as a friend (owner decision 2 of re/ucc_design.md, the design doc's P2 "no behavioural tell": today "the cops never
 * shoot him" is the strongest tell). Part of KLHook (included by klhook.c AFTER klucchide.c, klucc_down.c and klroundkeep.c, whose
 * private rules vtables it shares). 2026-10-26 (scheduled cloud check-in), built, NOT compiled with MSVC, NOT run live.
 * Research, every address and what is a GUESS: re/ucc_police_aim.md.
 *
 * WHAT THE GAME DOES (kl2.exe 0490, static read; CERTAIN unless marked): in an Undercover Cop round every soldier-side test that
 *   looks at a ZFFPlayer with the UCC byte +0x2729 asks the FA rules object ONE question, slot 188 (vt+0x2f0 = 0x5119a0 =
 *   `[rules+0x284]`, the bUCCAIHostile byte of RMCUCCMissionFailed, stock 0 all round): the target scoring 0x882470 (ZSoldier@CPPScript
 *   slot 111: 0 -> he is no soldier's target at all, the police byte test 0x8824e7 is skipped for him; 1 -> scored like any player, and
 *   with his police byte the AI heisters shoot him too), the friend-in-the-fire-line list 0x5706a0 (0 -> a police friend) and the
 *   fire-cone list 0x51d6c0 (ZSoldier slot 114). The stock game sets the byte to 1 only when a police player shoots a police NPC dead
 *   (rules Sv slot 128 at 0x847886 -> 0x418b20(1, 1)): then he is exposed to everyone. Neither value is what the owner wants.
 *
 * WHAT THIS DOES (PoliceAim=1): slot 188 of the rules object's PRIVATE vtable copy (klroundkeep.c's, klucc_down.c's or klucchide.c's
 *   table when one is installed, else our own copy after the others had their chance - the pattern of klucchide.c; no code byte is
 *   touched) goes to a naked thunk that hands the C wrapper the return address and the caller's ebp / edi / esi. For the three known
 *   call sites the asking soldier and the player asked about are read from those (re/ucc_police_aim.md 3: VERIFIED on the listing);
 *   when the asker's actor team ([[actor+0x54]+4]) is police (Enemy 1 / Enemy2 4) and the player is the UCC and still hidden
 *   (klucchide.c's reveal mask, klud_revealed), the answer is 1 = hostile; every other asker, caller or player gets the stock byte, and
 *   a stock 1 is never turned into 0. After the reveal he is police again to the AI, as stock (the owner's P6 text). HOST ONLY in
 *   effect: the soldier AI runs on the host; a client's copy answers the same way and changes nothing there.
 *
 * KLHook.ini
 *   [Ucc]
 *   PoliceAim=0     0 = stock. 1 = police AI treats a hidden UCC as a target (and not as a friend in the line of fire).
 *   Dry=0           1 = log what it would answer, answer stock (shared with DownOnly)
 *   Log=1           2 = every hostile answer
 */
#ifndef KLUCC_AIM_C
#define KLUCC_AIM_C

#include "klucc_aim_logic.h"

#define KLUA_SLOT        188                  /* rules vtable +0x2f0 */
#define KLUA_SLOT_FN     0x005119a0u          /* mov al, [ecx+0x284]; ret (Sv and Cl tables alike, checked before a table is patched) */
#define KLUA_SOLDIER_VT  0x00bd0954u          /* ZSoldier@CPPScript (klescort.c KLE_SOLDIER_VT); [s+0x40] = the actor */
#define KLUA_VT_SV       0x00bd2eb4u
#define KLUA_VT_CL       0x00bd31e4u
#define KLUA_VT_SLOTS    260                  /* as klroundkeep.c / klucc_down.c / klucchide.c */
#define KLUA_WAIT_MS     9000                 /* longer than klucchide.c's 6 s: its copy goes first, ours only when nobody else took the object */

static struct {
    int on, dry, log; DWORD rules; DWORD vtSv[1 + KLUA_VT_SLOTS], vtCl[1 + KLUA_VT_SLOTS]; DWORD waitSince; int toldVt, toldWait, toldTeam;
    int toldSite[4]; LONG nAsk, nHostile, nUnknown;
} klua;

typedef BYTE (__fastcall *KLUA_F188)(void *self, void *edx);

/* the asking soldier's team for one site; -1 = not readable / not a ZSoldier script (then: stock). *player = the player asked about */
static int klua_asker(int site, DWORD ebp, DWORD edi, DWORD esi, DWORD *player, DWORD *soldier)
{
    DWORD s = 0, th, a, tp, t = 0;
    *player = 0; *soldier = 0;
    switch (site) {
    case KLUA_SITE_SCORE: s = edi; *player = klh_rd32(ebp + 8); break;
    case KLUA_SITE_LINE:  th = klh_rd32(ebp - 0x30); s = th ? klh_rd32(th + 0x154) : 0; *player = esi; break;
    case KLUA_SITE_CONE:  s = edi >= 0x10000 ? klh_rd32(edi + 0x154) : 0; *player = esi; break;
    default: return -1;
    }
    if (s < 0x10000 || klh_rd32(s) != (DWORD)(DWORD_PTR)KLH_VA(KLUA_SOLDIER_VT)) return -1;
    if (!(a = klh_rd32(s + 0x40)) || !(tp = klh_rd32(a + 0x54)) || !klh_rd(tp + 4, &t, 4)) return -1;
    *soldier = s;
    if (site == KLUA_SITE_LINE) {                                    /* 0x5706a0 keeps the same team at [ebp-8]: cross-check the frame reading once */
        DWORD t2 = 0;
        if (klh_rd(ebp - 8, &t2, 4) && t2 != t && !klua.toldTeam++) klog("uccaim: fire-line site: frame team %lu differs from the soldier's %lu (the frame reading is off: stock answer there)", (unsigned long)t2, (unsigned long)t);
        if (t2 != t) return -1;
    }
    return (int)t;
}

/* is p the undercover cop and still hidden? (the marks and the mask of klucc_down.c / klucchide.c) */
static int klua_hidden_ucc(DWORD rules, DWORD p, int *idx)
{
    BYTE b29 = 0;
    *idx = -1;
    if (!klud_is_player(p)) return 0;
    *idx = klud_idx(p);
    klh_rd(p + 0x2729, &b29, 1);
    if (!klud_is_ucc(b29, klud_netflags(p), klud_flags(rules, *idx))) return 0;
    return klud_hidden(*idx, klud_revealed);
}

/* the wrapper: ra = the game's return address, ebp / edi / esi = the caller's registers as they were at its `call eax` (the thunk) */
static DWORD __fastcall klua_w188(void *self, void *edx, DWORD ra, DWORD ebp, DWORD edi, DWORD esi)
{
    BYTE stock = ((KLUA_F188)(DWORD_PTR)KLH_VA(KLUA_SLOT_FN))(self, 0);  /* every table we patch held exactly this function (checked) */
    int site, team, idx = -1, ans; DWORD player = 0, soldier = 0, sm, mode = 0, sub = 0;
    (void)edx;
    if (!klua.on || stock) return stock ? 1 : 0;
    InterlockedIncrement(&klua.nAsk);
    site = klua_site((unsigned long)ra, (unsigned long)(DWORD_PTR)KLH_VA(0));
    if (site == KLUA_SITE_NONE) {
        if (InterlockedIncrement(&klua.nUnknown) <= 5) klog("uccaim: slot 188 asked from %08lx (not one of the three AI sites): stock answer", (unsigned long)ra);
        return 0;
    }
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd((DWORD_PTR)KLH_VA(KLUD_SUBMODE), &sub, 4) || !klud_gate(mode, sub)) return 0;
    team = klua_asker(site, ebp, edi, esi, &player, &soldier);
    if (team < 0) return 0;
    ans = klua_answer(0, 1, site, klua_police_team(team), klua_hidden_ucc((DWORD)(DWORD_PTR)self, player, &idx));
    if (!ans) return 0;
    {
        long n = InterlockedIncrement(&klua.nHostile);
        if (klua.log >= 2 || !klua.toldSite[site]++ || n <= 10 || n % 500 == 0)
            klog("uccaim: %s: police soldier %08lx (team %d) asks about the hidden UCC %08lx (crew %d): %s (stock 0; %ld hostile answers so far)",
                 site == KLUA_SITE_SCORE ? "target scoring 0x882470" : site == KLUA_SITE_LINE ? "fire-line friends 0x5706a0" : "fire-cone bodies 0x51d6c0",
                 (unsigned long)soldier, team, (unsigned long)player, idx, klua.dry ? "would answer HOSTILE (Dry: stock)" : "HOSTILE", n);
    }
    return klua.dry ? 0 : 1;
}

/* the naked thunk in the vtable slot: thiscall with no arguments (ret 0); hands the wrapper [esp] (the return address) and the caller's
   ebp / edi / esi, untouched by the call; the __fastcall wrapper pops its four stack words, eax is the byte the game reads (al). */
#define KLUA_FWD(n) static __declspec(naked) void klua_fwd##n(void) { __asm mov eax, dword ptr [esp] __asm push esi __asm push edi __asm push ebp __asm push eax __asm call klua_w188 __asm ret }
KLUA_FWD(188)

/* slot 188 of a private table (ours or another part's, all in this DLL's .data): -> 1 when it now holds the thunk */
static int klua_patch(DWORD *slots, const char *whose, DWORD rules)
{
    if (slots[KLUA_SLOT] == (DWORD)(DWORD_PTR)klua_fwd188) return 1;
    if (slots[KLUA_SLOT] != (DWORD)(DWORD_PTR)KLH_VA(KLUA_SLOT_FN)) {
        if (!klua.toldVt++) klog("uccaim: %s rules table has slot 188 = %08lx, not 0x5119a0: the police AI is left as stock", whose, (unsigned long)slots[KLUA_SLOT]);
        return 0;
    }
    slots[KLUA_SLOT] = (DWORD)(DWORD_PTR)klua_fwd188;
    klog("uccaim: rules %08lx: slot 188 (bUCCAIHostile) of %s private vtable now answers HOSTILE to police AI about a hidden UCC%s", (unsigned long)rules, whose, klua.dry ? " (Dry: stock answers)" : "");
    return 1;
}

static void klua_wrap(DWORD rules, DWORD now)
{
    DWORD vt = klh_rd32(rules), nv; int sv, others;
    if (vt == (DWORD)(DWORD_PTR)&klua.vtSv[1] || vt == (DWORD)(DWORD_PTR)&klua.vtCl[1]) return;
    if (vt == (DWORD)(DWORD_PTR)&klrk_vt[1]) { klua_patch(&klrk_vt[1], "klroundkeep.c's", rules); return; }
    if (vt == (DWORD)(DWORD_PTR)&klud_sv[1]) { klua_patch(&klud_sv[1], "klucc_down.c's Sv", rules); return; }
    if (vt == (DWORD)(DWORD_PTR)&klud_cl[1]) { klua_patch(&klud_cl[1], "klucc_down.c's Cl", rules); return; }
    if (vt == (DWORD)(DWORD_PTR)&klucc.vtSv[1]) { klua_patch(&klucc.vtSv[1], "klucchide.c's Sv", rules); return; }
    if (vt == (DWORD)(DWORD_PTR)&klucc.vtCl[1]) { klua_patch(&klucc.vtCl[1], "klucchide.c's Cl", rules); return; }
    if (vt != (DWORD)(DWORD_PTR)KLH_VA(KLUA_VT_SV) && vt != (DWORD)(DWORD_PTR)KLH_VA(KLUA_VT_CL)) {
        if (!klua.toldVt++) klog("uccaim: rules vtable %08lx is none we know (another part's copy?): the police AI is left as stock", (unsigned long)vt);
        return;
    }
    sv = vt == (DWORD)(DWORD_PTR)KLH_VA(KLUA_VT_SV);
    others = klud.on != 0 || klucc.strip != 0;                   /* they install on a stock table and refuse one they do not know: let them go first */
    if (sv) {
#ifdef KLHOOK_TEST
        others = 1;                                             /* klroundkeep.c's TEST probe wraps the Sv object always */
#else
        if (klrk_keep) others = 1;
#endif
    }
    if (others) {
        if (!klua.waitSince) klua.waitSince = now ? now : 1;
        if (now - klua.waitSince < KLUA_WAIT_MS) return;
        if (!klua.toldWait++) klog("uccaim: no other part took the %s rules in %d s: our own copy", sv ? "Sv" : "Cl", KLUA_WAIT_MS / 1000);
    }
    {
        DWORD *blk = sv ? klua.vtSv : klua.vtCl;
        if (!blk[0]) {
            if (!klh_rd((DWORD_PTR)KLH_VA(vt - 4), blk, sizeof(DWORD) * (1 + KLUA_VT_SLOTS))) return;
            if (!klua_patch(&blk[1], sv ? "our Sv" : "our Cl", rules)) { blk[0] = 0; klua.on = 0; return; }
        }
        nv = (DWORD)(DWORD_PTR)&blk[1];
        if (sv) klh_rules_vt2 = nv; else klh_rules_vt3 = nv;     /* KLH_RULES_SV_OK / KLH_RULES_CL_OK accept it */
        if (klh_data((void *)(DWORD_PTR)rules, &nv, 4, "uccaim: FA rules vtable (private copy, slot 188)")) klog("uccaim: %s rules %08lx now answers slot 188 through our copy", sv ? "Sv" : "Cl", (unsigned long)rules);
        else if (sv) klh_rules_vt2 = 0; else klh_rules_vt3 = 0;
    }
}

static void klua_tick(int game_thread)
{
    static DWORD last; DWORD gs, r, now;
    if (!klua.on || !game_thread || !klh_exe_ok) return;
    now = GetTickCount();
    if (now - last < 200) return;
    last = now;
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLUD_GAMESET))) || !(r = klh_rd32(gs + 0x54))) { klua.rules = 0; return; }
    if (r != klua.rules) { klua.rules = r; klua.waitSince = 0; klua.toldWait = 0; memset(klua.toldSite, 0, sizeof klua.toldSite); }
    klua_wrap(r, now);
}

static void klua_init(void)
{
    memset(&klua, 0, sizeof klua);
    klua.on = GetPrivateProfileIntA("Ucc", "PoliceAim", 0, klh_ini) == 1;
    if (!klua.on) return;
    klua.dry = GetPrivateProfileIntA("Ucc", "Dry", 0, klh_ini) != 0;
    klua.log = GetPrivateProfileIntA("Ucc", "Log", 1, klh_ini);
    klog("uccaim: PoliceAim=1 - in Undercover Cop rounds the police AI treats a hidden UCC as a target, his crew's AI does not (rules slot 188 per asker)%s (re/ucc_police_aim.md)", klua.dry ? " - Dry: stock answers" : "");
}

#endif
