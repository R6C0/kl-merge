/* klucc_aim_logic.h - the PURE parts of klucc_aim.c ([Ucc] PoliceAim: the police AI treats a HIDDEN undercover cop as a heister,
 * owner decision 2 of re/ucc_design.md = P2 "no behavioural tell"). No game reads here: klucc_aim.c feeds it numbers it read;
 * klua_test.c checks it off-game (tools/run_harness_linux.sh klua_test). Research and every address: re/ucc_police_aim.md.
 *
 * THE STOCK GATE (kl2.exe 0490, static read 2026-10-26): in an Undercover Cop round (game type 4, sub-mode [0x168e59c] == 1) the three
 * soldier-side tests that decide whether a ZFFPlayer is an enemy, a friend in the line of fire or a body in the fire cone all branch,
 * for a player with the UCC byte +0x2729, on ONE byte: rules slot 188 (vt+0x2f0 = 0x5119a0 = `[rules+0x284]`, "bUCCAIHostile" of
 * RMCUCCMissionFailed). 0 (stock all round, until he shoots a police NPC dead): the UCC is NOBODY's target - the police test
 * `[P+0x2723]` is bypassed for him - and he counts as a police friend. 1: every soldier scores him like any player, and because he
 * carries the police byte the AI heisters shoot him too. So the owner's "police shoot him like a heister, his own crew does not" is
 * neither value: it is slot 188 answering 1 to a POLICE asker and 0 to a heister asker, per call. The wrapper tells the asker from
 * the return address and the caller's registers (klucc_aim.c), and this header decides. */
#ifndef KLUCC_AIM_LOGIC_H
#define KLUCC_AIM_LOGIC_H

/* the call sites of slot 188 (the instruction AFTER each `call eax`; what the caller keeps where, all VERIFIED on the listing) */
#define KLUA_RA_SCORE  0x008824d5u    /* ZSoldier@CPPScript slot 111 0x882470: a soldier scores a player as a target; edi = the soldier script (also [ebp-0xc]), player [ebp+8] */
#define KLUA_RA_LINE   0x005708c4u    /* 0x5706a0: friends along the fire line; [ebp-0x30] = this (+0x154 = soldier script), [ebp-8] = its team, player = esi */
#define KLUA_RA_CONE1  0x0051d9fbu    /* ZSoldier@CPPScript slot 114 0x51d6c0: bodies in the fire cone; edi = this (+0x154 = soldier script), player = esi */
#define KLUA_RA_CONE2  0x0051dac5u    /* the same routine, second pass */

/* the actor's team, ZFFActor node property 19 = [[actor+0x54]+4] (re/balance.md 90): Mercenary 0, Enemy 1, Ally 2, Enemy2 4 */
#define KLUA_TEAM_MERC   0
#define KLUA_TEAM_ENEMY  1
#define KLUA_TEAM_ALLY   2
#define KLUA_TEAM_ENEMY2 4

enum { KLUA_SITE_NONE = 0, KLUA_SITE_SCORE, KLUA_SITE_LINE, KLUA_SITE_CONE };

/* which site the return address is (0 = a caller we do not know: the stock answer, always) */
static int klua_site(unsigned long ra, unsigned long base)
{
    if (ra == base + KLUA_RA_SCORE) return KLUA_SITE_SCORE;
    if (ra == base + KLUA_RA_LINE) return KLUA_SITE_LINE;
    if (ra == base + KLUA_RA_CONE1 || ra == base + KLUA_RA_CONE2) return KLUA_SITE_CONE;
    return KLUA_SITE_NONE;
}

/* Is the asking soldier police? 0x882470 itself takes team 1 and 4 down the same "enemy" path ([ebp-2] = team not 1 and not 4), so both
   count. Team 2 (Ally: the AI heisters) and 0 (Mercenary) are the crew; 3 (neutral: civilians) and anything else: not police. */
static int klua_police_team(int team)
{
    return team == KLUA_TEAM_ENEMY || team == KLUA_TEAM_ENEMY2;
}

/* The answer slot 188 gives. stock = the byte the game holds ([rules+0x284], 0 or 1); on = [Ucc] PoliceAim; site = klua_site();
   police_asker = klua_police_team(the asker's team); hidden_ucc = the player asked about is the UCC and still hidden (klucchide.c's
   mask through klud_revealed). -> 1 = hostile to this asker, else the stock byte. Never turns a stock 1 into 0 (an exposed UCC stays
   exposed), never changes a heister's or an unknown caller's view, never acts on a revealed UCC (he is police again, as stock). */
static int klua_answer(int stock, int on, int site, int police_asker, int hidden_ucc)
{
    if (stock) return 1;
    if (!on || site == KLUA_SITE_NONE || !police_asker || !hidden_ucc) return stock ? 1 : 0;
    return 1;
}

#endif
