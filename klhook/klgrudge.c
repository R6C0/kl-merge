/*
 * klgrudge.c - the AI heisters against YOU: tougher, a traitor that means it, and an answer when you shoot them.
 * The owner, 2026-10-11: 'also need something for making them a bit more bullet spongey, feels a bit one sided so the
 * player could just easily turn on them, i saw one backstab me it was too lenient i could get away with killing him,
 * so make it a lil less forgiving and if i shoot them but before i turn traitor the more i shoot the more they shoot
 * back or they might just try and kill me straight away or they just accept getting shot stuff like that'.
 * Part of KLHook (SHIP and TEST alike), track O. DATA WRITES ONLY, all of them floats / one bit of heap objects of the
 * running round, from the game's own thread: no code byte, no vtable, NO call of a game function.
 * Research, numbers, every address and the live checks: re\bots_fight.md. NOTHING HERE HAS RUN IN THE GAME.
 * Every part is OFF unless its key in [Bots] is set, needs [Bots] Enable=1, acts only in an Arcade session
 * (klbot.c's klb_read: session mode 4 - never in a multiplayer session) and only on a level that is NOT the stock one
 * of its slot (klbot.c section 0, klb_level). What it wrote goes back when it stops acting.
 *
 * 1. WHAT WAS READ (kl2.exe build 0490, 2026-10-11; EXE = in the disassembly)
 *    a. WHEN A BOT COUNTS YOU AS AN ENEMY. ZSoldier's target test 0x882470, for an Ally / Mercenary soldier in Arcade
 *       (0x882636 .. 0x882726): the player is a FRIEND unless one of four holds - [player+0x2723] (he is police),
 *       [player+0x2726] (he is the traitor), the bot's own record mask 2 (klbot.c 3), or 0x6a1c40(rules, bot index):
 *           float [rules + 0x884 + 4 * index]  >  max(float [R + 0x18], 25.0)        R = the Arcade level's record
 *       (0x6a1c7e fld [0xd1b398] = 25.0; [R+0x18] = 100 90 80 70 60 40 25 25 25 25 25 on levels 1..11).
 *    b. WHAT THAT FLOAT IS. 0x4d17f0(rules; victim actor, &-damage, attacker), called from the NPC's damage routine at
 *       0x84777d in Arcade: only for a victim with a crew record (0x78f470) and an attacker that is a ZFFPlayer, and
 *       not when the player or the bot already carries flag 1 'traitor' of the score table ([score+0x1d4+4*i], slot
 *       114 = 0x771a10). Then  d = 100 * damage / the victim's MAXIMUM health (slot 414 = 0x574060 = [[actor+0x5fc]+8];
 *       0x4d1973 .. 0x4d19aa: maximum - x, / maximum, x 100.0 (0xb3dde8), - 100)  is added to TWO sums:
 *           A[attacker 0][victim] = [rules + 0x884 + 4 * victim]            (rows of 12: 0x4c2861 has the general form)
 *           B[victim][attacker 0] = [rules + 0xac4 + 0x30 * victim]
 *       and the time [rules+0x50] is noted at [rules + 0x614 + 0x30 * victim]. So the float is THE SHARE OF HIS HEALTH,
 *       IN PER CENT, that your bullets took. B at 25.0 or more (0x4d19e4) -> slot 117 = 0x586c10(victim, 0): the YELLOW
 *       CARD (byte [rules + 0xd04 + 12 * victim + 0] = 1, flag 0x400 on you: slot 122 = 0x833f70 then lets that victim
 *       kill you without becoming a traitor).
 *       ITS OWN GATES (0x4d1842 .. 0x4d196d, read as code; the dword is each side's of the score table, slot 114):
 *       nothing is counted when slot 123 = 0x600470(victim, 0) answers no; when you or the bot carry bit 0x1000 (with
 *       or without 0x80: both pairs of tests return); when you carry 0x800 and the bot's own sum on YOU
 *       ([rules+0x884+0x30*victim]) is not 0; when you carry 8 and the bot 0x80. WHAT those bits are was NOT READ
 *       (1 = traitor and 0x400 = yellow card are the two known): in those states Grudge sees no hit at all.
 *       A SECOND READER of the switch: 0x570a1b (in 0x5706a0, the list of friendly players a soldier keeps) leaves a
 *       player out for the same 'mask 2 OR 0x6a1c40' - so a bot held by the float is treated as a mask-2 traitor in
 *       both places read. Indirect calls of the float's getter (slot 141 = 0x78d5c0) were NOT searched.
 *    c. THE GAME FORGIVES. 0x771af0 (state 0x19 only): for an attacker WITHOUT a yellow card every A that is not 0 and
 *       whose last hit is more than 10.0 s old (0xd1b390) is cleared by slot 119 = 0x521d30 (A, B, the time, the
 *       card byte). So in stock a bot turns on you only when you take more than [R+0x18] per cent of his health - ALL of
 *       it on Arcade levels 1 .. with the owner's Tune (Retaliate=0 = stock 100) - without a pause of 10 s: by then he
 *       is dead. That is 'today the AI heisters do nothing about it'.
 *    d. WHEN YOU BECOME THE TRAITOR. The kill bookkeeping 0x6706b0 (from slot 16 = 0x485740 for an AI member), at
 *       0x6709dd .. 0x670a22: the victim is no policeman, does not carry flag 1 itself, and slot 122(killer, victim) is
 *       false -> slot 129 = 0x8fb0d0(killer, victim): flag 1 on the killer and, whatever the index, the LOCAL PLAYER's
 *       byte [player+0x2726] (klbot.c 4). So: WOUNDING crew costs a yellow card at 25 %, KILLING a crew member who is
 *       not flagged a traitor makes you the traitor - then every bot fights you by the game's own test (a).
 *       A bot the tactic (or klbot.c's Backstab) turned carries record mask 2 only, NOT flag 1 of the score table
 *       (0x488eb0 sets the record byte and calls 0x4322f0, nothing else): READ, NOT SEEN - killing the bot that
 *       backstabbed you therefore looks like killing a loyal one to that bookkeeping. Key BackstabMark (4 c) and the
 *       'you: crew flags' log line (4 e) are there to see and to settle it.
 *    e. A soldier's accuracy: float [[soldier+0x6d8]+0x10] = ZSoldier field 4 as used, per cent, read at every shot
 *       (0x719cd8 .. 0x719ce9: the miss share is 1 - it / 100); soldier = [actor+0x77c] (klescort.c). The block is
 *       the ZSoldierRout's (rout+0x34, re\map_ai.md 1), which the soldier only points at: his alone while one rout
 *       makes one soldier (kly_aim looks before it writes). The crew's value in the level data: 50, one bot 90.
 *    f. A crew member's health object [actor+0x5fc] (klbot.c's Log=2 reads it): +4 health, +8 maximum, +0x24 the
 *       actor. 252.0 on every bot of every live log (280 x 0.9, the campaign difficulty row).
 *
 * 2. THE NUMBERS (re\bots_fight.md 1 has the table). Under the owner's Risk=2: your Zastava 58.5 a bullet at 10 m x
 *    YouToCrew 1.0 against 252 = 5 body hits, ONE head shot (x 10 for an NPC victim); a heister's 47 x CrewToYou 1.0
 *    against your 401.5 = 9, and he never gets a head shot. The key that makes them tougher against YOU and nobody
 *    else is klbalance.c's YouToCrew (it is exactly that float; 0.5 = 9 against 9, 0.4 = 11). CrewHealth below is the
 *    second way: it also makes them tougher against the police (multiply CopToCrew by the same factor to keep the
 *    police where they are) and it is the only one that takes the one-head-shot kill away at a factor the body hits
 *    do not show: YouToCrew 0.4 leaves a head shot at 234 of 252.
 *
 * 3. WHAT THE HOOK DOES (each key by itself)
 *    a. CrewHealth=<factor> (0.25 .. 10; 1 or no key = leave). Every AI heister in play: maximum = the game's x factor,
 *       his health kept at the same SHARE of it (so the write itself never heals or hurts). The game's maximum is
 *       tracked as klbalance.c tracks yours: a value that is neither the game's last nor ours is a new one of the
 *       game's and is scaled again. Put back when the hook stops acting.
 *    b. BackstabHealth=<factor> (same range). A bot that carries the traitor mask - turned by the game's tactic or by
 *       klbot.c's Backstab alike - gets its maximum x this (on top of CrewHealth) from the pass that sees the mask,
 *       at the same share: a traitor at full health has the whole of it at once. Back when the mask is cleared.
 *       BackstabAim=<per cent> (0 .. 100; -1 or no key = leave): his accuracy (1 e) is raised to this while he
 *       carries the mask (never lowered) and put back after; the line says what he had.
 *    c. BackstabMark=1 (default 0; an ASSUMPTION is tested by it, see 1 d): a bot with the traitor mask also gets bit 1
 *       of its dword in the score table ([score+0x1d4+4*i] |= 1), the bit the kill bookkeeping and the damage sum test
 *       for 'this one is a traitor' - so that killing your backstabber cannot make YOU the traitor. Cleared by the
 *       hook when the mask goes (so it stays on a dead / aboard / escaped bot to the round's end). IT CHANGES THE
 *       PAYOUT: 0x796576 .. 0x79657c - an escaped record WITH that bit keeps its own money and is out of the pool
 *       that is split, without it its money goes into the pool. NOT read: who else shows the bit (the HUD's crew list
 *       is likely to), whether loyal bots shoot at a bot that carries it.
 *       GrudgeMark=1 (default 0) is the same bit for a bot that Grudge (d) holds your enemy FOR GOOD, from the pass
 *       it turns to the round's end: without it KILLING such a bot makes you the traitor (1 d: the bot has no traitor
 *       flag and holds no card against you - a bot never gets one) and all seven turn. A bot that only answers for
 *       some seconds (ESCALATES below its for-good share) is NOT marked: kill him while he answers and you are the
 *       traitor - he was a crew member you shot first. With the bit the game counts no more hits on him (1 b).
 *    d. Grudge=1: PERSONALITIES. Each bot draws one of three at its first sight in a round (GrudgeMix=40,30,30):
 *         ESCALATES  every hit of yours makes him your enemy for GrudgeBase + GrudgePer x (per cent of his health you
 *                    have taken) seconds, GrudgeMax at most, counted from that hit - one stray bullet is a short answer,
 *                    a magazine a long one; stop shooting and he stops. At GrudgeForGood per cent (0 = never) he is
 *                    your enemy for the rest of the round.
 *         SNAPS      at your first or your second hit (drawn with the personality) he is your enemy for good;
 *                    GrudgeSnapHits=<n> fixes the number (2 = one stray bullet is forgiven by everybody; hits older
 *                    than GrudgeForget are forgotten first).
 *         TAKES IT   never: also not at the game's own limit.
 *       HOW: the game's own switch (1 a) and nothing else. The hook keeps its own sum of what the game adds to
 *       A[0][bot] (whatever stands there above what the hook last saw is a new hit), and writes into the float either
 *       0.01 (he is your friend; not 0, so that the game's forgiving of 1 c still runs 10 s after your last hit and
 *       clears the yellow-card sum with it) or the level's limit + 1 (he is not). While he is not, the time of 'your
 *       last hit' [rules+0x614+0x30*bot] is kept within 2 s of the rules' clock [rules+0x50], or the game would clear
 *       the float 10 s after the real hit. The record mask is never touched by this part, B (the yellow card) is the
 *       game's as ever, and the bot's tactics are not touched at all: a bot
 *       that fights you still loots, boards and escapes by its own tactic list - ASSUMED, as for a traitor bot (seen
 *       in the owner's rounds: bots with the mask went aboard and escaped).
 *       A tally is forgotten GrudgeForget seconds after your last hit on that bot (the game's own rule is 10 s).
 *       THE HAND-OVER: the moment YOU are the traitor ([player+0x2726]) or police ([player+0x2723]: klfed.c's fed), or
 *       are no longer in play, the hook writes every bot's own sum back into its float once and writes nothing more
 *       while that lasts: from there the game's own rules stand (for a traitor / a policeman every bot is an enemy
 *       by 1 a anyway). Outside state 0x19, on a stock level and at a new round the floats the hook holds go to 0.
 *       THE LOG: the draw and every turn are written with [Bots] Log=2 only - the owner is not to read his crew's
 *       temper off the log; Log=1 says how many bots drew, not what.
 *       AN ESCORT (klescort.c) that you shoot: klescort.c would go on calling it to your side - and it would shoot you
 *       from there. re\bots_fight.md 4.4 has the three lines for klescort.c that let it go instead (not applied: that
 *       file is another track's). Until they are in, kly_escort_free keeps a bot that klescort.c HOLDS from being
 *       turned at all (it sees whether klescort.c asks kly_angry); its tally runs on and it turns when released.
 *    e. THE LOG ([Bots] Log >= 1, on any level, reads only): 'grudge: you: crew flags ...' whenever your dword of the
 *       score table or your traitor byte changes (1 = TRAITOR, 0x400 = a yellow card).
 *
 * 4. REVIEW OF THE STATE MACHINE (klbot.c's B1 - B5 of re\hook_review_1010.md as the model)
 *    - B1, where it acts: klb_level() every pass; on a stock level nothing is written and what was is put back.
 *    - a round restart: a new rules object or the state becoming 0x19 (NOT klbot.c's third sign, a heist stage going
 *      down: a guess there, and a record released in mid-round would wipe every temper - review S1; if a round ever
 *      restarts with neither sign the tempers carry over, the health is still right: a new object / maximum is taken
 *      as the game's); before the round's memory is dropped every health / aim / mark of ours is put back through the
 *      pointers kept (each chain checked again: the actor's vtable, [actor+0x5fc] / [actor+0x77c] still the objects
 *      written, the value still ours) and every float the hook holds is zeroed - so the next round's first sight
 *      takes the GAME's maximum, not ours, and draws anew.
 *    - a second round / the next level: the same; a new rules object without a snapshot (the session ended) puts back
 *      through the kept pointers only.
 *    - a fed human / a traitor human / a dead human: the hand-over of 3 d; health and aim stay (the fed is to meet
 *      the same crew; FedToCrew in klbalance.c is his own number).
 *    - a dead bot's record reused by another actor: the record's actor is compared every pass; another one = the old
 *      one's writes are put back through the kept pointers, the slot starts empty and draws anew.
 *    - a bot that is aboard / dead / escaped is not written any more (its float is left as it is: nobody reads it).
 *    - nothing off the game's thread: with [KLHook] Tick=0 one line and nothing else.
 *    - indices: the sums are rows of 12; a record index of 12 or more is never written (Arcade has 8).
 *
 * WIRING (klhook.c; nothing else of the hook changes)
 *   #include "klgrudge.c"        after  #include "klbalance.c"   (it uses klbot.c's klb_read / klb_level / klb_roll / klb_who)
 *   kly_tick(game_thread);       in klh_tick, after  klr_tick(game_thread);
 *   kly_init();                  in the init list, after  klr_init();
 *   (The prefix is kly_: klg_ is klgun.c's.)
 * TESTED OFF-GAME ONLY (G:\kl_scratch\O2\t\kly_test.c: this file included as it is, made-up round objects - health,
 * the turn, the three writes of a traitor, ESCALATES through hit / calm / for good, SNAPS, TAKES IT, GrudgeForget,
 * GrudgeMark, an escort held / asked about, a shared accuracy block, the hand-over for a traitor and a dead human, a
 * record released in mid-round, the state leaving and re-entering 0x19, an unreadable limit, another actor in a
 * record, a stock level, the session's end). That proves this file's own logic only.
 *
 * KLHook.ini, section [Bots] (Enable=1 there)
 *   CrewHealth=1          BackstabHealth=1      BackstabAim=-1       BackstabMark=0
 *   Grudge=0              GrudgeMix=40,30,30    GrudgeBase=2  GrudgePer=0.15  GrudgeMax=20  GrudgeForGood=60  GrudgeForget=45
 *   GrudgeSnapHits=0      GrudgeMark=0
 */
#ifndef KLGRUDGE_C
#define KLGRUDGE_C

#define KLY_SOLDIER_VT 0x00bd0954             /* CPPScript::ZSoldier (klescort.c's KLE_SOLDIER_VT) */
#define KLY_PLAYER_VT  0x00bb45f4             /* ZFFPlayer */
#define KLY_SUM        0x884                  /* rules: float A[attacker * 12 + victim]; the local player is attacker 0 in Arcade */
#define KLY_TIME       0x614                  /* rules: float [victim * 12 + attacker], the rules' clock [rules+0x50] at the last hit (0x4d19d0) */
#define KLY_CALM       0.01f                  /* a sum that is 'nothing' but not 0 (see kly_grudge) */
#define KLY_NROW       12
#define KLY_FLAGS      0x1d4                  /* score object: one dword per crew index (slot 114 = 0x771a10) */
#define KLY_ABS(x)     ((x) < 0 ? -(x) : (x))
enum { KLY_ESCALATES, KLY_SNAPS, KLY_TAKES };

static struct {
    int on, log, grudge, mark, mix[3];
    int gmark, snap;                          /* GrudgeMark: a bot that is your enemy FOR GOOD gets the score table's traitor bit; GrudgeSnapHits: 0 = drawn 1 or 2 */
    float crew, bs_health, bs_aim;            /* crew / bs_health: 0 = leave; bs_aim: < 0 = leave */
    float base, per, max, good, forget;       /* ESCALATES: seconds, seconds per per cent, seconds, per cent (0 = never); forget: seconds */
} kly;

#include "klogrudge_logic.h"     /* [Bots] OnlineGrudge pure decisions (klogrudge_test.c) */
#include "klhpmax_logic.h"      /* the one registry of every hook writer of an AI heister's maximum health (klhpmax_test.c); klbotfill.c / klbotdown.c use it too */
static int kly_hp_alive(unsigned int h, unsigned int a) { return klh_rd32(h + 0x24) == a; }      /* the object still belongs to that actor */

struct kly_bot {
    DWORD actor; int kind, snap_hits;        /* kind -1 = not drawn yet */
    int have, hostile, good, hits, handed; float wrote, tally; DWORD hit_at, angry_until;      /* the grudge: wrote = the float as last seen / written */
    DWORD hobj; float hmax0, hwrote;          /* health: the game's maximum (the registry's base, klhpmax_logic.h), the maximum wanted with our factor in (0 = our factor is 1) */
    DWORD soldier, dblk; float aim0; int aset; float awrote;      /* aim: the block, what he had, ours is in (awrote = the number we wrote) */
    int marked;                               /* BackstabMark / GrudgeMark: bit 1 of his score dword is ours */
    int turned;                               /* he was held your enemy FOR GOOD at least once this round (GrudgeMark keeps its bit from then on) */
    int cap_told;                             /* TurnMax: the 'waits' line was said once */
    int esc_told, aim_told;                   /* lines said once: an escort that is not turned, an accuracy block that is shared */
};
static struct {
    DWORD rules, score, state; int down, drew, said_drew, told_gate, told_down; char why[200];
    DWORD hflags; BYTE htraitor; int hhave;
    struct kly_bot b[KLB_NREC];
} kly_r;

/* For klescort.c (re\bots_fight.md 4.4; not called by anything until those three lines are in): does this file hold
   the bot of that crew record as your enemy right now? The call itself is remembered: it is how this file knows
   that klescort.c lets go of an escort that turns (kly_escort_free). */
static DWORD kly_asked[KLB_NREC];
static int kly_angry(int rec)
{
    if (rec < 0 || rec >= KLB_NREC) return 0;
    kly_asked[rec] = KLB_T(GetTickCount());
    return kly_r.b[rec].hostile;
}

/* May the bot of that record be turned on you now? Not while klescort.c HOLDS it at your side (kle_r, read only: a
   slot in mode 1) unless klescort.c has asked kly_angry about it within its last passes (it runs every 500 ms) -
   without that question it would go on ordering the bot back to 3 m beside you, and the bot would shoot you from
   there (review M2). So: with the three lines of re\bots_fight.md 4.4 in klescort.c an escort that turns is dropped
   by klescort.c one pass later; without them an escort is simply NOT turned while it escorts (its tally runs on, and
   it turns when the escort is released - at the vehicle - if that is still due). */
static int kly_escort_free(int rec, DWORD now)
{
    int k, held = 0;
    for (k = 0; k < KLE_MAX; k++) if (kle_r.e[k].mode == 1 && kle_r.e[k].rec == rec) held = 1;
    return !held || (kly_asked[rec] && now - kly_asked[rec] < 3000);
}

static const char *kly_kind(int k) { return k == KLY_ESCALATES ? "ESCALATES" : k == KLY_SNAPS ? "SNAPS" : "TAKES IT"; }

/* Put back, through the pointers kept, what this file wrote for one bot - each chain is read again and a value that is
   no longer ours is left alone. rules / score = the round object the record belongs to, 0 when it is gone. */
static void kly_undo(struct kly_bot *b, int i, DWORD rules, DWORD score)
{
    float raw[0x28 / 4], cur, v; DWORD fl = 0; struct khpm_ent *e;
    if (b->hwrote != 0 && b->actor && klh_avt(b->actor) == KLB_ACTOR_VT && b->hobj && klh_rd32(b->actor + 0x5fc) == b->hobj &&
        klh_rd(b->hobj, raw, sizeof raw) && ((DWORD *)raw)[0x24 / 4] == b->actor && klb_finite(raw[1]) && klb_finite(raw[2]) && raw[2] >= 1 && (e = khpm_find(b->hobj, b->actor, kly_hp_alive, 0)) != 0) {
        khpm_see(e, raw[2]);      /* a maximum that is not the hook's is the game's: it stays; only OUR factor goes (another writer's factor stays in: 350 x 2 x 5 -> x 5 = 1750) */
        if (khpm_plan(e, KHPM_GRUDGE, 1.0f, raw[2], &v)) {
            cur = raw[1] * v / raw[2];
            if (klh_data((void *)(DWORD_PTR)(b->hobj + 8), &v, 4, "an AI heister's maximum health (the game's own back)")) {
                khpm_done(e, v);
                if (raw[1] > 0) klh_data((void *)(DWORD_PTR)(b->hobj + 4), &cur, 4, "an AI heister's health, at the same share of the game's maximum");
            }
        }
    }
    b->hwrote = 0;
    if (b->aset && b->actor && klh_avt(b->actor) == KLB_ACTOR_VT && b->soldier && klh_rd32(b->actor + 0x77c) == b->soldier && klh_svt(b->soldier) == KLY_SOLDIER_VT &&
        klh_rd32(b->soldier + 0x6d8) == b->dblk && klh_rd(b->dblk + 0x10, &cur, 4) && KLY_ABS(cur - b->awrote) <= 0.01f)
        klh_data((void *)(DWORD_PTR)(b->dblk + 0x10), &b->aim0, 4, "an AI heister's accuracy (his own back)");
    b->aset = 0;
    if (b->marked && score && klh_rd(score + KLY_FLAGS + 4 * i, &fl, 4) && (fl & 1)) { fl &= ~1u; klh_data((void *)(DWORD_PTR)(score + KLY_FLAGS + 4 * i), &fl, 4, "score table: the traitor bit this hook gave a bot, off"); }
    b->marked = 0;
    if (b->have && b->hostile && rules && i < KLY_NROW && klh_rd(rules + KLY_SUM + 4 * i, &cur, 4) && KLY_ABS(cur - b->wrote) <= 0.001f) {
        v = 0; klh_data((void *)(DWORD_PTR)(rules + KLY_SUM + 4 * i), &v, 4, "the sum of your hits on a bot (the hook's hold, off)");
    }
    b->hostile = 0;
}

static void kly_undo_all(DWORD rules, DWORD score)
{
    int i;
    for (i = 0; i < KLB_NREC; i++) if (kly_r.b[i].actor) kly_undo(&kly_r.b[i], i, rules, score);
}

/* 3 a / 3 b: the bot's maximum health. act = the hook acts on this level. */
static void kly_health2(const struct klb_rec *r, struct kly_bot *b, int i, int act, float crew, float bs_health, float tf)
{
    float raw[0x28 / 4], cur, max, wmax, wcur, f = 1; DWORD h; struct khpm_ent *e;
    if (crew <= 0 && bs_health <= 0 && b->hwrote == 0 && tf == 1.0f) return;
    if (!(h = klh_rd32(r->actor + 0x5fc)) || !klh_rd(h, raw, sizeof raw) || ((DWORD *)raw)[0x24 / 4] != r->actor) return;
    cur = raw[1]; max = raw[2];
    if (!klb_finite(cur) || !klb_finite(max) || max < 1 || max > 100000 || cur > max * 1.01f + 1) return;
    if (act) {
        if (crew > 0) f *= crew;
        if ((r->flags & 2) && bs_health > 0) f *= bs_health;
        f *= tf;
    }
    /* the game's maximum and every hook writer's factor live in klhpmax_logic.h's registry (RV1A_DD05 2026-11-05: this file and klbotfill.c's OnlineHealthMul each took the other's write for 'a new maximum of
       the game's' and multiplied again, 350 -> 350000): our write is the product of ALL factors, a maximum that is the hook's is never taken as the game's */
    if (h != b->hobj) { b->hobj = h; b->hwrote = 0; }
    if (!(e = khpm_find(h, r->actor, kly_hp_alive, f != 1.0f || b->hwrote != 0))) return;      /* no factor of ours and none ever set: nothing to do */
    khpm_see(e, max);
    b->hmax0 = e->base;
    if (!khpm_plan(e, KHPM_GRUDGE, f, max, &wmax)) { b->hwrote = f != 1.0f ? e->base * f : 0; return; }      /* as wanted (another writer's factor in) */
    if (cur <= 0) return;                  /* he is down: a dead man's object is left; hwrote unchanged, so a put-back is tried again (review wou2kgqnw) */
    wcur = cur * wmax / max;
    if (!klh_data((void *)(DWORD_PTR)(h + 8), &wmax, 4, "an AI heister's maximum health")) return;
    klh_data((void *)(DWORD_PTR)(h + 4), &wcur, 4, "an AI heister's health, at the same share of the new maximum");
    khpm_done(e, wmax);
    b->hwrote = f != 1.0f ? e->base * f : 0;      /* only once the write is in */
    if (kly.log) klog("grudge: record %d (%s): health %.1f of %.1f -> %.1f of %.1f (the game gave %.1f; x %.2f%s)", i, klb_who(r), cur, max, wcur, wmax, b->hmax0, f,
                      !act ? " = put back" : (r->flags & 2) && bs_health > 0 ? ", CrewHealth x BackstabHealth: he has turned" : ", CrewHealth");
}
static void kly_health(const struct klb_rec *r, struct kly_bot *b, int i, int act)
{
    kly_health2(r, b, i, act, kly.crew, kly.bs_health, act ? kltt_hp(i) : 1.0f);      /* kltt_hp: kltrait.c, Health / DamageIn of the character he wears (1.0 = none) */
}

/* ONLINE (wk-arcmods2-1102, [Bots] OnlineCrewHealth=<factor>, default 0 = off, OnlineCrewHealthDry=1 logs only; NOT RUN in the game): the HOST scales the maximum health
   of every AI heister of the census (klbotdown.c klbd_online_view slot 3 = pseudo records, flags 1, the actor only) - the same data writes as CrewHealth above (health
   object [actor+0x5fc]: +4 health, +8 maximum, +0x24 the actor), same share, put back when the round / host state ends. No crew record, no Arcade gate, no stock-map gate
   (it also acts on Dog Days' stock FA maps, as Arcade's CrewHealth does not: the owner rule 'every feature on stock maps too'). Traits (kltt_hp) need real crew records: tf = 1.
   GUESS: the host's health object is the authoritative one for a CLIENT shooter's hit (DDL_ZFFActor::RMCReceiveHit path NOT traced, re/netcode.md 6); the bench must show a client's
   shots taking the scaled number of bullets and the client's puppet not dying early. Clients need no change (they send hits, the host owns the AI). */
static struct { float factor; int dry; DWORD rules; int told[KLB_NREC]; struct kly_bot b[KLB_NREC]; DWORD last; } klyo;
static int klbd_online_view(int who, struct klb_snap *sn, char why[200]);

static void kly_online_undo(void)
{
    int i; for (i = 0; i < KLB_NREC; i++) if (klyo.b[i].actor) kly_undo(&klyo.b[i], i, 0, 0);
    memset(klyo.b, 0, sizeof klyo.b); memset(klyo.told, 0, sizeof klyo.told); klyo.rules = 0;
}

static void kly_online_tick(int game_thread)
{
    struct klb_snap s; char why[200]; DWORD now = GetTickCount(); int i, v;
    if (klyo.factor <= 0 || !game_thread || !klh_exe_ok) return;
    if (now - klyo.last < 250) return;
    klyo.last = KLB_T(now);
    why[0] = 0;
    v = klbd_online_view(3, &s, why);
    if (v < 0) return;                                         /* a transient: change nothing */
    if (v == 0) { if (klyo.rules || klyo.b[0].actor || klyo.b[1].actor || klyo.b[2].actor || klyo.b[3].actor) kly_online_undo(); return; }      /* not the host / not a round: back */
    if (s.rules != klyo.rules) { kly_online_undo(); klyo.rules = s.rules; klog("grudge: online CrewHealth x %.2f%s: %s", klyo.factor, klyo.dry ? " (dry log)" : "", why); }
    for (i = 0; i < s.n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s.r[i]; struct kly_bot *b = &klyo.b[i];
        if (!r->used || !r->actor) continue;
        if (b->actor != r->actor) { if (b->actor) kly_undo(b, i, 0, 0); memset(b, 0, sizeof *b); b->actor = r->actor; klyo.told[i] = 0; }
        if (klh_avt(r->actor) != KLB_ACTOR_VT || r->status != 0) continue;
        if (klyo.dry) {
            DWORD h; float hp[2];
            if (!klyo.told[i] && (h = klh_rd32(r->actor + 0x5fc)) && klh_rd32(h + 0x24) == r->actor && klh_rd(h + 4, hp, 8)) {
                klyo.told[i] = 1; klog("grudge: online dry: record %d actor %08lx health %.1f of %.1f would be x %.2f", i, r->actor, hp[0], hp[1], klyo.factor);
            }
            continue;
        }
        kly_health2(r, b, i, 1, klyo.factor, 0, 1.0f);
    }
}

/* [Bots] OnlineGrudge (default 0, bench-run live 11-06: grudge_1106 pass A + B PASS, 2 seats DD09; re\online_grudge_1106.md): HOST only. A human who kills an AI heister of the host's round becomes the traitor, as stock does for
   human on human: rules slot 129 (0x41d480, killer index, victim index) sets the traitor bit and sends RMCSetTraitor to the clients. Stock never reaches it for a bot (no ZFFPlayer record).
   RULES: s.rules of klbd_online_view is the SESSION object (the round key); the REAL rules object is [[0x168e9e4] + 0x54] (kog_rules), the one slot 129 / klud_flags / KLH_RULES_SV_OK want.
   KILLER, best first: (1) the LETHAL blow seen at the SOLDIER's hit handler (ZSoldier slot 96 = 0x8473a0, kog_w_hit below: attacker [hit+0], health before / after the original; rules slot 15 does
   NOT work for this: it is ZFFPlayer-only, never runs for an AI heister); (2) a fresh human stamp ([[actor+0x77c]+0x708], valid while clock [[0xdd2640]+0x48] < [soldier+0x70c]) at the instant of
   death - that field marks the FIRST tagger, so it is refused when a non-human hit the bot in the window or the stamp changed since the last poll. Human = vtable ZFFPlayer AND the body is a used rules record's player
   (klbr_rec_member). Victim index -1 (GUESS: skips the announce, ok). Stock's tail after slot 129: only slot 105 (0x42e510, the killer's state refresh) is replayed, see the note. */
static int klbr_rec_member(DWORD P, int *nused);
static int klud_idx(DWORD p);
static unsigned long klud_flags(DWORD rules, int i);
static int klbr_was_traitor_actor(DWORD actor);      /* klbrain.c (included after this file) */
static int klbr_traitor_bots(void);
static int klbr_og_rules_busy(DWORD r);
#define KOG_N KLB_NREC
static struct { int on, dry, ndone, nfire, nlog, told_kind, told_sub, latch[KOG_N], lw[KOG_N]; DWORD rules, last, tid, actor[KOG_N], sol[KOG_N], vtold[KOG_N], lat_at[KOG_N], nh_at[KOG_N], lw_at[KOG_N]; unsigned long done[KGO_NDONE]; } kog_;

/* THE HIT HOOK (fix 1106b; bench-run live 11-06, pass A + B PASS). Rules slot 15 (klud_w15) is ZFFPlayer-only and never runs for an AI heister, so a human's kill of a bot was never seen there. The bot's own hit handler is
   ZSoldier slot 96 = vtable 0xbd0954 + 0x180 = 0x8473a0 (thiscall: ecx soldier, one stack arg = hit record, ret 4; attacker actor [hit+0], hit type [hit+8]; actor = [soldier+0x40]; health [[actor+0x5fc]+4]).
   A SHIP build writes data only and the stock table is .rdata, so (as klbrain.c's klh_soldier_priv) a PRIVATE copy of the table (128 slots, the class has 118) carries slot 96 = kog_w_hit, and the
   hook points a TRACKED bot's soldier ([soldier+0], heap) at it (klh_svt maps it back to 0xbd0954: klh_soldier_og). Put back at a round's end / when the bot leaves the census. A soldier already on
   klbrain.c's table is not touched (a traitor bot is no victim for this feature anyway); klbrain.c may take a soldier over from ours. kog_w_hit passes straight through unless the soldier is tracked. */
#define KOG_SLOT 96
#define KOG_ORG  0x008473a0
#define KOG_NSLOT 128
static DWORD kog_vt[1 + KOG_NSLOT];
static int kog_vt_ok, kog_vt_try;
static DWORD __fastcall kog_w_hit(void *self, void *edx, DWORD *hit);

static int kog_vt_make(void)
{
    DWORD org[KOG_NSLOT], col = 0, va = (DWORD)(DWORD_PTR)KLH_VA(KLY_SOLDIER_VT);
    if (kog_vt_ok) return 1;
    if (kog_vt_try) return 0;
    kog_vt_try = 1;
    if (!klh_rd(va, org, sizeof org) || org[KOG_SLOT] != (DWORD)(DWORD_PTR)KLH_VA(KOG_ORG)) { klog("grudge: online grudge: ZSoldier slot %d reads %08lx, not 0x8473a0: the hit hook is OFF (no killer can be seen)", KOG_SLOT, (unsigned long)org[KOG_SLOT]); return 0; }
    klh_rd(va - 4, &col, 4);                                                            /* slot -1 = the RTTI locator, copied like klbrain.c's tables */
    kog_vt[0] = col; memcpy(kog_vt + 1, org, sizeof org); kog_vt[1 + KOG_SLOT] = (DWORD)(DWORD_PTR)kog_w_hit;
    klh_soldier_og = (DWORD)(DWORD_PTR)(kog_vt + 1); kog_vt_ok = 1;
    klog("grudge: online grudge: private ZSoldier table %08lx made (slot %d = the hit handler 0x8473a0 wrapped, %d slots copied)", (unsigned long)klh_soldier_og, KOG_SLOT, KOG_NSLOT);
    return 1;
}
static void kog_svt_on(int i, DWORD act)
{   /* a tracked, living bot: its soldier wears our table (once; only from the stock one) */
    DWORD sol = klh_rd32(act + 0x77c), vt, stock = (DWORD)(DWORD_PTR)KLH_VA(KLY_SOLDIER_VT);
    DWORD pr = klh_rd32(act + 0x54), team = 99;
    if (pr > 0xffff) klh_rd(pr + 4, &team, 4);
    if (team != 2) return;                                                              /* only Ally bots can be victims; retried every tick, so a later team change is caught */
    if (!kog_vt_ok || sol < 0x10000 || klh_rd32(sol + 0x40) != act) return;
    vt = klh_rd32(sol);
    if (vt == klh_soldier_og) { kog_.sol[i] = sol; return; }
    if (vt != stock) { if (!kog_.vtold[i]++) klog("grudge: online grudge: AI heister %d soldier %08lx has vtable %08lx (klbrain.c's private table?), not the stock one: its hits are NOT seen", i, (unsigned long)sol, (unsigned long)vt); return; }
    if (!klh_data((void *)(DWORD_PTR)sol, &klh_soldier_og, 4, "ZSoldier vtable pointer (OnlineGrudge hit hook)")) { if (!kog_.vtold[i]++) klog("grudge: online grudge: AI heister %d: the vtable write was refused", i); return; }
    kog_.sol[i] = sol;
}
static void kog_svt_back(int i)
{   /* only where it is still ours and still that bot's soldier */
    DWORD stock = (DWORD)(DWORD_PTR)KLH_VA(KLY_SOLDIER_VT);
    if (kog_.sol[i] && kog_.actor[i] && klh_soldier_og && klh_rd32(kog_.sol[i]) == klh_soldier_og && klh_rd32(kog_.sol[i] + 0x40) == kog_.actor[i])
        klh_data((void *)(DWORD_PTR)kog_.sol[i], &stock, 4, "ZSoldier vtable pointer back (OnlineGrudge hit hook)");
    kog_.sol[i] = 0;
}
static void kog_svt_back_all(void) { int i; for (i = 0; i < KOG_N; i++) kog_svt_back(i); }

static void kog_slot_clear(int i) { kog_.actor[i] = 0; kog_.sol[i] = 0; kog_.vtold[i] = 0; kog_.latch[i] = -1; kog_.lw[i] = -1; kog_.lat_at[i] = kog_.nh_at[i] = kog_.lw_at[i] = 0; }
static void kog_reset(DWORD rules)
{   /* a new round (or none): everything but the switches and the session counters */
    int on = kog_.on, dry = kog_.dry, nf = kog_.nfire, nu = kog_.nlog, tk = kog_.told_kind, i;
    kog_svt_back_all();                                                                 /* the stock soldier tables back BEFORE the round's memory is dropped */
    memset(&kog_, 0, sizeof kog_); kog_.on = on; kog_.dry = dry; kog_.nfire = nf; kog_.nlog = nu; kog_.told_kind = tk; kog_.rules = rules;
    for (i = 0; i < KOG_N; i++) kog_slot_clear(i);
}

static DWORD kog_rules(void)
{   /* the REAL rules object (Sv), 0 = not one */
    DWORD gs = klh_rd32((DWORD_PTR)KLH_VA(0x168e9e4)), r = gs > 0xffff ? klh_rd32(gs + 0x54) : 0, vt = r > 0xffff ? klh_rd32(r) : 0;
    if (klbr_og_rules_busy(r)) return 0;                                                /* the brain's shadow block, or a swap is live: never the real one now */
    return (vt > 0xffff && KLH_RULES_SV_OK(vt)) ? r : 0;
}
static int kog_used(DWORD rules, int k)
{   /* client record k exists (free byte 0), as the game's own slot tests read it */
    DWORD n = 0, fr; BYTE u = 1;
    if (k < 0 || !klh_rd(rules + 0x14, &n, 4) || (DWORD)k >= n || n > 16) return 0;
    return (fr = klh_rd32(rules + 0xc)) && klh_rd(fr + k, &u, 1) && !u;
}
static int kog_human(DWORD body, int *idx, int *rm, const char **why)
{   /* 1 = body is a human heister's ZFFPlayer (vtable AND a used rules record), client index in *idx; else 0 and *why says which check failed */
    int nu = 0, k; DWORD vt;
    *idx = -1; *rm = -2;
    if (body < 0x10000) { *why = "no aggressor"; return 0; }
    vt = klh_pvt(body);
    if (vt != 0x00bb45f4u) { *why = "vtable check: not a ZFFPlayer"; return 0; }
    *rm = klbr_rec_member(body, &nu);
    if (*rm != 1) { *why = *rm < 0 ? "rules-record check: walk unavailable (treated as not human)" : "rules-record check: ZFFPlayer without a seat"; return 0; }
    k = klud_idx(body);
    if (k < 0 || k >= 16) { *why = "client index out of range"; return 0; }
    *idx = k; *why = "human"; return 1;
}

struct kog_agg { int cls, idx, rm; DWORD tgt, vt; long remain; const char *why; };      /* cls: 0 no fresh stamp, 1 fresh non-human, 2 fresh human */
static void kly_og_agg(DWORD actor, struct kog_agg *a)
{   /* the bot's last aggressor stamp, classified */
    DWORD sol, tgt = 0, stamp = 0, obj, clk = 0;
    memset(a, 0, sizeof *a); a->idx = -1; a->rm = -2; a->why = "no soldier";
    if (!(sol = klh_rd32(actor + 0x77c)) || !klh_rd(sol + 0x708, &tgt, 4) || !klh_rd(sol + 0x70c, &stamp, 4)) return;
    a->why = "no stamp"; if (tgt < 0x10000) return;
    obj = klh_rd32((DWORD_PTR)KLH_VA(0xdd2640));
    if (obj < 0x10000 || !klh_rd(obj + 0x48, &clk, 4)) { a->why = "clock unreadable"; return; }
    a->tgt = tgt; a->vt = klh_rd32(tgt); a->remain = (long)stamp - (long)clk;
    if (!kgo_fresh((long)clk, (long)stamp)) { a->why = "stamp stale"; return; }
    a->cls = 1;
    if (kog_human(tgt, &a->idx, &a->rm, &a->why)) a->cls = 2;
}

static int nlog0, nlogh;                                                                /* separate small log budget for hits that took no health, so they cannot eat the real ones; and one for HUMAN
                                                                                           attackers (grudge_1106 pass A: 8 AI/cop hits in 2 s filled the shared budget before the host's first shot) */
static void kog_hit(int i, DWORD act, DWORD h, float hp0, DWORD *hit)
{   /* AFTER the original handler, on the game thread, for a tracked bot: who hit him, did it take health, was it the last of it. READ ONLY. */
    float hp1 = hp0; DWORD att = klh_rd32((DWORD_PTR)hit), ty = klh_rd32((DWORD_PTR)hit + 8), now = GetTickCount(); int k = -1, rm = -2, hum, lethal, hurt; const char *why = "";
    if (klh_rd32(h + 0x24) == act) klh_rd(h + 4, &hp1, 4);                              /* the health object may be gone if the handler freed him: then hp1 = hp0 = no news */
    hurt = kgo_hurt(hp0, hp1); lethal = kgo_lethal(hp0, hp1);                           /* GUESS: the handler has applied the damage when it returns (0x84789d writes it through actor vt+0x670; synchronous?) */
    hum = att > 0xffff && kog_human(att, &k, &rm, &why);
    if (att <= 0xffff) why = "no aggressor";
    if (hum ? nlogh < 16 : hurt ? kog_.nlog < 8 : nlog0 < 3) {
        if (hum) nlogh++; else if (hurt) kog_.nlog++; else nlog0++;
        klog("grudge: online grudge%s: hit #%d on AI heister %d (actor %08lx): attacker %08lx vtable %08lx (%s), hit type %lu, health %.1f -> %.1f%s", kog_.dry ? " dry" : "", hum ? nlogh : hurt ? kog_.nlog : nlog0, i, (unsigned long)act, (unsigned long)att,
             (unsigned long)(att > 0xffff ? klh_rd32(att) : 0), hum ? "HUMAN" : why, (unsigned long)ty, hp0, hp1, lethal ? " LETHAL" : hurt ? "" : " (no health taken: dead already, or completion not synchronous)");
    }
    if (!hurt) return;                                                                  /* a hit that took nothing says nothing */
    if (!hum) { kog_.nh_at[i] = now | 1; kog_.latch[i] = -1; }
    kog_.lw[i] = kgo_after_hit(kog_.lw[i], hum, k, lethal);                             /* a non-lethal non-human hit clears a human's predicted lethal blow */
    if (!lethal) return;
    kog_.lw_at[i] = now | 1;
    klog("grudge: online grudge%s: lethal blow on AI heister %d (actor %08lx, health %.1f -> %.1f): attacker %08lx vtable %08lx: %s",
         kog_.dry ? " dry" : "", i, (unsigned long)act, hp0, hp1, (unsigned long)att, (unsigned long)(att > 0xffff ? klh_rd32(att) : 0), hum ? "HUMAN" : why);
}

static DWORD __fastcall kog_w_hit(void *self, void *edx, DWORD *hit)
{   /* ZSoldier slot 96 (0x8473a0), see the block above. Straight through unless this soldier is a tracked bot's and we are on the tick's game thread. */
    DWORD act = 0, h = 0, r; float hp0 = 0; int i = KOG_N;
    if (kog_.on && kog_.tid && hit && GetCurrentThreadId() == kog_.tid && (act = klh_rd32((DWORD_PTR)self + 0x40)) > 0xffff) {
        for (i = 0; i < KOG_N; i++) if (kog_.actor[i] == act && kog_.sol[i] == (DWORD)(DWORD_PTR)self) break;
        if (i < KOG_N && (!(h = klh_rd32(act + 0x5fc)) || klh_rd32(h + 0x24) != act || !klh_rd(h + 4, &hp0, 4) || !(hp0 == hp0))) i = KOG_N;
    }
    r = ((DWORD (__fastcall *)(void *, void *, DWORD *))(DWORD_PTR)KLH_VA(KOG_ORG))(self, edx, hit);      /* the original: thiscall, ret 4 */
    if (i < KOG_N) kog_hit(i, act, h, hp0, hit);
    return r;
}

static void kog_traitors(DWORD rules)
{   /* log only: traitors now, bots (klbrain.c marks / turns) and humans (rules flag bit 1) */
    DWORD n = 0; int k, hn = 0;
    if (klh_rd(rules + 0x14, &n, 4) && n <= 16) for (k = 0; k < (int)n; k++) if (kog_used(rules, k) && (klud_flags(rules, k) & KGO_F_TRAITOR)) hn++;
    klog("grudge: online grudge: traitors now: bots %d human %d (a human made here does not count toward OnlineBrainTraitorMax)", klbr_traitor_bots(), hn);
}

static void kly_og_fire(DWORD rules, int killer, int slot)
{
    DWORD vt = klh_rd32(rules), fn = vt > 0xffff ? klh_rd32(vt + 0x204) : 0, fn2 = vt > 0xffff ? klh_rd32(vt + 0x1a4) : 0; unsigned long fl = 0;
    if (!rules || !KLH_RULES_SV_OK(vt) || fn != (DWORD)(DWORD_PTR)KLH_VA(0x41d480)) { klog("grudge: online grudge: slot 129 is %08lx, not 0x41d480: not called", (unsigned long)fn); return; }
    if (!kog_used(rules, killer)) { klog("grudge: online grudge: client %d has no seat now: not called", killer); return; }
    fl = klud_flags(rules, killer);
    if (!kgo_eligible(killer, fl)) { klog("grudge: online grudge: AI heister %d killed by client %d, flags %08lx: not eligible (traitor / dead / police / escaped / undercover)", slot, killer, fl); return; }
    if (kog_.dry) { klog("grudge: online grudge dry: would call slot 129 (killer %d, victim -1), flags %08lx, then slot 105%s", killer, fl, fn2 == (DWORD)(DWORD_PTR)KLH_VA(0x42e510) ? "" : " (NOT: slot 105 is not 0x42e510)"); return; }
    __try {
        ((void (__fastcall *)(void *, void *, int, int))(DWORD_PTR)fn)((void *)(DWORD_PTR)rules, 0, killer, -1);
        if (fn2 == (DWORD)(DWORD_PTR)KLH_VA(0x42e510)) ((void (__fastcall *)(void *, void *, int))(DWORD_PTR)fn2)((void *)(DWORD_PTR)rules, 0, killer);      /* stock's next step (0x794afc), killer only */
    }
    __except (EXCEPTION_EXECUTE_HANDLER) { klog("grudge: online grudge: slot 129 / 105 faulted (killer %d): disabled", killer); kog_.on = 0; return; }
    kog_.nfire++;
    klog("grudge: online grudge: human %d killed an AI heister: made traitor (slot 129 killer %d victim -1, then slot 105), fire #%d, flags %08lx -> %08lx (bit 1 = %s)", killer, killer, kog_.nfire, fl, klud_flags(rules, killer),
         (klud_flags(rules, killer) & KGO_F_TRAITOR) ? "SET" : "NOT set");
    kog_traitors(rules);
}

static void kly_og_death(DWORD rules, int i, DWORD act, DWORD now)
{   /* a tracked bot is seen dead for the first time: who killed him, and may that human be made the traitor? */
    struct kog_agg ag; DWORD pr, team = 99; int cur, killer, how = 0, vr; unsigned long lw_age, nh_age;
    kly_og_agg(act, &ag);
    cur = ag.cls == 2 ? ag.idx : -1;
    lw_age = kog_.lw_at[i] ? (unsigned long)(now - kog_.lw_at[i]) : KGO_NEVER;
    nh_age = kog_.nh_at[i] ? (unsigned long)(now - kog_.nh_at[i]) : KGO_NEVER;
    if ((pr = klh_rd32(act + 0x54)) > 0xffff) klh_rd(pr + 4, &team, 4);
    vr = kgo_victim(team, klbr_was_traitor_actor(act));
    if (vr == 2) { klog("grudge: online grudge%s: AI heister %d (actor %08lx) died: victim was a traitor: no mark", kog_.dry ? " dry" : "", i, (unsigned long)act); return; }
    if (vr == 1) { klog("grudge: online grudge%s: AI heister %d (actor %08lx) died: team %lu is not Ally (police / fed / turned): no mark", kog_.dry ? " dry" : "", i, (unsigned long)act, (unsigned long)team); return; }
    killer = kgo_decide(kog_.lw[i], lw_age, kog_.latch[i], cur, nh_age, &how);
    klog("grudge: online grudge%s: AI heister %d (actor %08lx) died: lethal blow %s (%lu ms), stamp %s (%s; target %08lx vtable %08lx rec-member %d, valid %ld more ticks), last poll latch %d, non-human hit %lu ms ago -> %s (%d)",
         kog_.dry ? " dry" : "", i, (unsigned long)act, kog_.lw[i] >= 0 ? "human" : kog_.lw[i] == -2 ? "NOT human" : "none", lw_age == KGO_NEVER ? 0ul : lw_age,
         ag.cls == 2 ? "human" : ag.cls == 1 ? "fresh, not human" : "none", ag.why, (unsigned long)ag.tgt, (unsigned long)ag.vt, ag.rm, ag.remain, kog_.latch[i], nh_age == KGO_NEVER ? 0ul : nh_age,
         killer >= 0 ? "killer found" : "no human killer", how);
    if (killer < 0) return;
    kly_og_fire(rules, killer, i);
}

static void kly_og_tick(int game_thread)
{
    struct klb_snap s; char why[200]; DWORD now = GetTickCount(), rules; int i, v; long sub = -1;
    if (!kog_.on || !game_thread || !klh_exe_ok) return;
    kog_.tid = GetCurrentThreadId();                                                    /* kog_w_hit only acts on this thread */
    if (now - kog_.last < 250) return;
    kog_.last = now | 1;
    why[0] = 0; v = klbd_online_view(3, &s, why);
    if (v < 0) return;
    if (v == 0) { if (kog_.rules) kog_reset(0); return; }
    if (s.rules != kog_.rules) { kog_reset(s.rules); kog_.told_sub = 0; klog("grudge: online grudge: new round, %s", why); }
    klh_rd((DWORD_PTR)KLH_VA(0x168e59c), &sub, 4);
    if (!kgo_submode_ok(sub)) {                                                         /* Undercover Cop / Cops and Robbers: stock never makes a traitor; the stock tables go back, so the hit hook has nothing to see */
        if (!kog_.told_sub) { kog_.told_sub = 1; klog("grudge: online grudge: sub-mode [0x168e59c] = %ld, not Fragile Alliance (0): off this round", sub); }
        kog_.tid = 0; kog_svt_back_all(); return;
    }
    if (!kog_.told_sub) { kog_.told_sub = 1; klog("grudge: online grudge: sub-mode [0x168e59c] = 0 (Fragile Alliance): on"); }
    if (klbr_og_rules_busy(0)) return;                                                  /* a brain swap frame is open: poll again next time */
    kog_vt_make();
    rules = kog_rules();                                                               /* the REAL rules object; s.rules (the session) is only the round key */
    for (i = 0; i < KOG_N; i++) {
        const struct klb_rec *r = i < s.n ? &s.r[i] : 0; DWORD act = (r && r->used) ? r->actor : 0; int first, st;
        if (kog_.actor[i] && kog_.actor[i] != act) {
            if (kog_.latch[i] >= 0 && !kgo_done_has(kog_.done, kog_.ndone, kog_.actor[i])) klog("grudge: online grudge: AI heister left the census with a human latch (record %d, actor %08lx, client %d)", i, (unsigned long)kog_.actor[i], kog_.latch[i]);
            kog_svt_back(i); kog_slot_clear(i);
        }
        if (!act || klh_avt(act) != KLB_ACTOR_VT) continue;
        first = kog_.actor[i] != act;
        if (first) { kog_slot_clear(i); kog_.actor[i] = act; }
        st = kgo_step(r->status == 7, kgo_done_has(kog_.done, kog_.ndone, act), first);
        if (st == 1) {
            struct kog_agg ag; kly_og_agg(act, &ag);
            kog_svt_on(i, act);
            if (ag.cls == 2) { kog_.latch[i] = ag.idx; kog_.lat_at[i] = now | 1; }
            else if (ag.cls == 1) { kog_.latch[i] = -1; kog_.nh_at[i] = now | 1; }      /* a fresh non-human aggressor: the latch is cleared, the window opens */
        } else if (st == 3) {
            kgo_done_add(kog_.done, &kog_.ndone, act);
            klog("grudge: online grudge: AI heister %d (actor %08lx) first seen already dead: no mark", i, (unsigned long)act);
        } else if (st == 2) {
            kgo_done_add(kog_.done, &kog_.ndone, act);                                  /* once per actor for the whole round, whatever the outcome */
            if (!rules) { klog("grudge: online grudge: AI heister %d died but the real rules object is not an Sv one: no mark", i); continue; }
            kly_og_death(rules, i, act, now);
        }
    }
}

/* 3 b: a turned bot's accuracy. The float is NOT the soldier's own memory: the block D belongs to the ZSoldierRout
   that made him (rout+0x34, re\map_ai.md 1) and the soldier only points at it ([soldier+0x6d8]) - his own as long as
   one rout makes one soldier, which is what every crew squad of the five maps has. So before the first write the
   other crew records are looked at: a block that another AI heister's soldier points at too is NOT written (one line). */
static void kly_aim(const struct klb_snap *s, const struct klb_rec *r, struct kly_bot *b, int i, int act)
{
    DWORD sol, d; float cur, want; int k;
    if (kly.bs_aim < 0 && !b->aset && !(act && kltt_aim(i, 50.0f) != 50.0f)) return;      /* kltrait.c: AimSpread / DamageOut move the accuracy too */
    if (!(sol = klh_rd32(r->actor + 0x77c)) || klh_svt(sol) != KLY_SOLDIER_VT || klh_rd32(sol + 0x40) != r->actor || !(d = klh_rd32(sol + 0x6d8)) ||
        !klh_rd(d + 0x10, &cur, 4) || !klb_finite(cur) || cur < 0 || cur > 100) return;
    if (d != b->dblk || sol != b->soldier) { b->soldier = sol; b->dblk = d; b->aim0 = cur; b->aset = 0; }
    else if (!b->aset) b->aim0 = cur;
    else if (KLY_ABS(cur - b->awrote) > 0.01f) { b->aim0 = cur; b->aset = 0; }      /* somebody else wrote it since: that is his now */
    want = act ? kltt_aim(i, b->aim0) : b->aim0;                  /* the character's trait (kltrait.c), then the backstab raise on top */
    if (act && (r->flags & 2) && kly.bs_aim > want) want = kly.bs_aim;
    if (KLY_ABS(cur - want) <= 0.01f) return;
    if (!b->aset) for (k = 0; k < s->n && k < KLB_NREC; k++) {      /* going in: is the block his alone? */
        DWORD a2 = s->r[k].actor, s2;
        if (k == i || !s->r[k].used || !(s->r[k].flags & 1) || !a2 || a2 == r->actor || klh_rd32(a2) != KLB_ACTOR_VT) continue;
        if ((s2 = klh_rd32(a2 + 0x77c)) != 0 && klh_svt(s2) == KLY_SOLDIER_VT && klh_rd32(s2 + 0x6d8) == d) {
            if (!b->aim_told++) klog("grudge: record %d (%s): its accuracy block %08lx is also record %d's (one ZSoldierRout made both): BackstabAim is NOT written for it", i, klb_who(r), d, k);
            return;
        }
    }
    if (!klh_data((void *)(DWORD_PTR)(d + 0x10), &want, 4, "a turned AI heister's accuracy (ZSoldier field 4 as used)")) return;
    b->aset = KLY_ABS(want - b->aim0) > 0.01f; b->awrote = want;
    if (kly.log) klog("grudge: record %d (%s): accuracy %.0f %% -> %.0f %% (%s)", i, klb_who(r), cur, want, b->aset ? ((r->flags & 2) && kly.bs_aim > 0 ? "BackstabAim / trait: he has turned" : "his character's AimSpread / DamageOut") : "his own back");
}

/* 3 c: the score table's traitor bit for a bot that carries the record mask */
static void kly_mark(const struct klb_snap *s, const struct klb_rec *r, struct kly_bot *b, int i, int act)
{
    DWORD fl = 0, at = s->score + KLY_FLAGS + 4 * i; int bs = act && kly.mark && (r->flags & 2), gr = act && kly.gmark && b->turned, want = bs || gr;
    if ((!kly.mark && !kly.gmark && !b->marked) || !klh_rd(at, &fl, 4)) return;
    if (want && !(fl & 1)) {
        fl |= 1;
        if (klh_data((void *)(DWORD_PTR)at, &fl, 4, "score table: the traitor bit for a bot that turned")) {
            b->marked = 1;        /* the GrudgeMark line gives a temper away: Log=2 only, as the draw */
            if (kly.log >= (bs ? 1 : 2)) klog("grudge: record %d (%s): bit 1 of its score dword set (%08lx): killing it is killing a traitor (%s); if it escapes it keeps its own money and is out of the split", i, bs ? "TRAITOR" : "your enemy for good", fl, bs ? "BackstabMark" : "GrudgeMark");
        }
    } else if (!want && b->marked) {
        if (fl & 1) { fl &= ~1u; klh_data((void *)(DWORD_PTR)at, &fl, 4, "score table: the traitor bit this hook gave a bot, off"); }
        b->marked = 0;
    }
}

/* max([R+0x18], 25.0) of the level, as 0x6a1c40 takes it; 0 when the tuning object cannot be read */
static float kly_limit(int level)
{
    DWORD tun = klh_rd32((DWORD_PTR)KLH_VA(KLB_TUNING)); float v = 0;
    if (!tun || !klh_rd(tun + 0x6ac + 0x70 * level + 0x18, &v, 4) || !klb_finite(v) || v < 0 || v > 100000) return 0;
    return v < 25.0f ? 25.0f : v;
}

/* 3 d. live = the hook holds the floats now (a round runs, the level is ours, you are a criminal in play);
   limit = kly_limit, 0 = not known (then nothing is written). */
static void kly_grudge(const struct klb_snap *s, const struct klb_rec *r, struct kly_bot *b, int i, DWORD now, float limit, int live)
{
    DWORD at = s->rules + KLY_SUM + 4 * i; float cur, want, d = 0; int was = b->hostile, hit = 0;
    if (i >= KLY_NROW || !klh_rd(at, &cur, 4) || !klb_finite(cur)) return;
    if (!b->have) { b->have = 1; b->wrote = cur; }
    if (cur > b->wrote + 0.01f) { d = cur - b->wrote; b->tally += d; b->hits++; b->hit_at = KLB_T(now); hit = 1; }      /* the game added a hit of yours */
    b->wrote = cur;
    if (!live || limit <= 0) {
        if (b->hostile || (kly_r.down == 1 && !b->handed)) {      /* the hand-over: his own sum, ONCE (the game may forgive it after that); off: zero */
            want = kly_r.down == 1 ? b->tally : 0;
            if (KLY_ABS(cur - want) > 0.001f && klh_data((void *)(DWORD_PTR)at, &want, 4, "the sum of your hits on a bot (handed back to the game)")) b->wrote = want;
            b->hostile = 0; b->handed = kly_r.down == 1;
        }
        return;
    }
    b->handed = 0;
    if (b->kind < 0) {
        int roll; klb_seed = klb_seed * 1103515245u + 12345u; roll = (int)((klb_seed >> 16) % 100u);
        b->kind = roll < kly.mix[0] ? KLY_ESCALATES : roll < kly.mix[0] + kly.mix[1] ? KLY_SNAPS : KLY_TAKES;
        b->snap_hits = 1 + klb_roll(50);      /* the roll is made also with GrudgeSnapHits set: the sequence of draws stays the same */
        if (kly.snap > 0) b->snap_hits = kly.snap;
        kly_r.drew++;
        if (kly.log >= 2) {
            char at_[40]; at_[0] = 0;
            if (b->kind == KLY_SNAPS) snprintf(at_, sizeof at_, " (at hit %d of yours)", b->snap_hits);
            klog("grudge: record %d: %s%s", i, kly_kind(b->kind), at_);
        }
    }
    if (!hit && b->tally > 0 && !b->good && kly.forget > 0 && now - b->hit_at > (DWORD)(kly.forget * 1000)) {
        if (kly.log >= 2) klog("grudge: record %d (%s): %.0f s without a hit of yours: %.0f %% of its health in %d hit(s) forgotten", i, kly_kind(b->kind), kly.forget, b->tally, b->hits);
        b->tally = 0; b->hits = 0;
    }
    if (b->kind == KLY_SNAPS) { if (b->hits >= b->snap_hits) b->good = 1; }
    else if (b->kind == KLY_ESCALATES && hit) {
        float sec = kly.base + kly.per * b->tally; DWORD until;
        if (sec > kly.max) sec = kly.max;
        until = KLB_T(now + (DWORD)(sec * 1000));
        if (!b->angry_until || (int)(until - b->angry_until) > 0) b->angry_until = until;
        if (kly.good > 0 && b->tally >= kly.good) b->good = 1;
    }
    if (b->angry_until && (int)(now - b->angry_until) >= 0) b->angry_until = 0;
    b->hostile = b->kind != KLY_TAKES && (b->good || b->angry_until);
    if (b->hostile && !was && klb.turn_max > 0) {      /* [Bots] TurnMax: at most n bots your enemy at once (retried every pass; the anger timer keeps running). Not for a human traitor: live is 0 then */
        int j, n = 0;
        for (j = 0; j < KLB_NREC; j++) if (j != i && kly_r.b[j].hostile) n++;
        if (!kltr_turn_ok(n, klb.turn_max)) { b->hostile = 0; if (kly.log >= 2 && !b->cap_told++) klog("grudge: record %d would turn on you but %d bot(s) already are (TurnMax=%d): it waits", i, n, klb.turn_max); }
    }
    if (b->hostile && !kly_escort_free(i, now)) {      /* klescort.c holds him at your side and does not ask: he is not turned (review M2) */
        b->hostile = 0;
        if (!b->esc_told++ && kly.log >= 2) klog("grudge: record %d (%s): it is your escort and klescort.c does not ask klgrudge.c about it (the three lines of re\\bots_fight.md 4.4 are not in): it is NOT turned on you while it escorts you", i, kly_kind(b->kind));
    }
    if (b->hostile && b->good) b->turned = 1;
    /* The float: limit + 1 while he is your enemy; else 'next to nothing' - NOT 0 after a hit: the game's own forgiving
       (0x771af0) looks at sums that are not 0 and clears the yellow-card sum B and the time with them 10 s after your
       last hit, as it always did; a float that is 0 already is left 0. */
    want = b->hostile ? limit + 1.0f : cur > KLY_CALM + 0.001f ? KLY_CALM : cur;
    if (KLY_ABS(cur - want) > 0.001f) {
        if (klh_data((void *)(DWORD_PTR)at, &want, 4, "the sum of your hits on a bot (the switch of 0x6a1c40)")) b->wrote = want;
        else b->hostile = was;
    }
    if (b->hostile) {                         /* ... and while he is, the time of 'your last hit' is kept young: the game would
                                                 clear the float 10 s after the real one (and again every pass after that) */
        float tnow, tcur; DWORD tat = s->rules + KLY_TIME + 0x30 * i;
        if (klh_rd(s->rules + 0x50, &tnow, 4) && klh_rd(tat, &tcur, 4) && klb_finite(tnow) && klb_finite(tcur) && tnow - tcur > 2.0f)
            klh_data((void *)(DWORD_PTR)tat, &tnow, 4, "the time of your last hit on a bot (kept young while the hook holds him your enemy)");
    }
    if (kly.log >= 2 && hit)
        klog("grudge: record %d (%s): your hit took %.1f %% of its health (%.1f %% in %d hit(s)); %s", i, kly_kind(b->kind), d, b->tally, b->hits,
             !b->hostile ? "it stays your friend" : b->good ? "it is your enemy for the rest of the round" : "it is your enemy for some seconds from now");
    if (kly.log >= 2 && b->hostile != was && !hit) klog("grudge: record %d (%s): %s (the float %.1f -> %.1f; the level's limit is %.0f)", i, kly_kind(b->kind), b->hostile ? "turns on you" : "is your friend again", cur, want, limit);
    (void)r;
}

/* the human: 1 = a criminal in play (the floats may be held); *why: 1 he is the traitor / police / out of play (the
   hand-over), 2 no player object. Also the 'crew flags' log line (3 e). */
static int kly_human(const struct klb_snap *s, int *why)
{
    DWORD gd, pl, fl = 0; BYTE sel = 0xff, police = 0, traitor = 0;
    *why = 2;
    if (s->human != 0) return 0;              /* the game's sums are wired for attacker 0 (0x4d17f0: push 0 throughout): another index is not ours */
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel > 31 || !(pl = klh_rd32(gd + 0x828 + 4 * sel)) ||
        klh_pvt(pl) != KLY_PLAYER_VT || !klh_rd(pl + 0x2723, &police, 1) || !klh_rd(pl + 0x2726, &traitor, 1)) return 0;
    if (klh_rd(s->score + KLY_FLAGS + 4 * s->human, &fl, 4) && (!kly_r.hhave || fl != kly_r.hflags || traitor != kly_r.htraitor)) {
        if (kly.log && (kly_r.hhave || fl || traitor))
            klog("grudge: you: crew flags %08lx -> %08lx, traitor byte %u -> %u%s%s%s", kly_r.hhave ? kly_r.hflags : 0, fl, kly_r.hhave ? kly_r.htraitor : 0, traitor,
                 (fl & 1) || traitor ? " - YOU ARE THE TRAITOR: every AI heister is your enemy by the game's own rule" : "",
                 (fl & 0x400) ? " - a YELLOW CARD (you took 25 % of a crew member's health: he may kill you for it)" : "", police ? " - you are police" : "");
        kly_r.hhave = 1; kly_r.hflags = fl; kly_r.htraitor = traitor;
    }
    *why = 1;
    return !police && !traitor && !(fl & 1) && s->r[s->human].status == 0;
}

static void kly_tick(int game_thread)
{
    static DWORD last, off_since; static int told_thread;
    struct klb_snap s; DWORD now = GetTickCount(); char why[200]; int i, act, human, hwhy = 0, live; float limit;
    kly_online_tick(game_thread);             /* the host-only online path: its own key, its own state (returns at once unless OnlineCrewHealth is set) */
    kly_og_tick(game_thread);                 /* [Bots] OnlineGrudge: host only, off unless set */
    if (!kly.on || !klb.on || !klh_exe_ok) return;
    if (!game_thread) {                       /* the round's objects are only written between two frames of the game itself */
        if (!off_since) off_since = KLB_T(now);
        else if (!last && !told_thread && now - off_since > 20000 && klb_read(&s) && s.state == KLB_ROUND) { told_thread = 1; klog("grudge: no tick has come on the game's thread ([KLHook] Tick=0?): nothing is written"); }
        return;
    }
    if (now - last < 50) return;
    last = KLB_T(now);
    if (!klb_read(&s)) {                      /* no Arcade round object: what is still ours goes back through the kept pointers */
        if (kly_r.rules) { kly_undo_all(0, 0); memset(&kly_r, 0, sizeof kly_r); }
        return;
    }
    /* A new round: a new rules object, or the state BECOMING 0x19. klbot.c's third sign - the sum of the heist stages
       going down - is 'only a GUESS' there (B5) and is NOT taken here (review S1: a record released in mid-round lowers
       the sum, and a bot that had turned on you for good became a friend with a new temper). A record whose actor
       changed starts empty by itself (below), and a new health object or maximum is taken as the game's (kly_health). */
    if (s.rules != kly_r.rules || (s.state == KLB_ROUND && kly_r.state != KLB_ROUND)) {
        int same = s.rules == kly_r.rules;
        if (kly_r.rules) kly_undo_all(same ? s.rules : 0, same ? s.score : 0);
        memset(&kly_r, 0, sizeof kly_r); kly_r.rules = s.rules; kly_r.score = s.score;
    }
    kly_r.state = s.state;
    act = klb_level(why);
    if (!kly_r.told_gate || strcmp(why, kly_r.why)) {
        kly_r.told_gate = 1; strcpy(kly_r.why, why);
        klog("grudge: %s: %s", why, act ? "CrewHealth / Backstab.. / Grudge act here, as far as their keys are set" : "nothing is written here (this part acts only on a level that is not stock)");
    }
    human = kly_human(&s, &hwhy);
    live = act && kly.grudge && s.state == KLB_ROUND && human;
    kly_r.down = live ? 0 : (act && kly.grudge && s.state == KLB_ROUND && hwhy == 1) ? 1 : 2;      /* 1 = the hand-over (sums back), 2 = off (zero) */
    if (kly.grudge && act && s.state == KLB_ROUND && kly_r.down == 1 && !kly_r.told_down) {
        kly_r.told_down = 1;
        if (kly.log) klog("grudge: you are the traitor, police or out of play: every bot's own sum of your hits goes back into its float and the game's rules stand from here (the hand-over)");
    } else if (live) kly_r.told_down = 0;
    limit = kly_limit(s.level);
    for (i = 0; i < s.n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s.r[i]; struct kly_bot *b = &kly_r.b[i];
        if (!r->used || !(r->flags & 1) || !r->actor) continue;
        if (b->actor != r->actor) {           /* the record has another actor: the old one's writes go back, the slot starts empty */
            if (b->actor) kly_undo(b, i, s.rules, s.score);
            memset(b, 0, sizeof *b); b->actor = r->actor; b->kind = -1;
        }
        if (klh_avt(r->actor) != KLB_ACTOR_VT) continue;
        kly_mark(&s, r, b, i, act);
        if (r->status != 0) continue;         /* aboard, dead, escaped: not written any more */
        kly_health(r, b, i, act);
        kly_aim(&s, r, b, i, act);
        if (kly.grudge || b->hostile) kly_grudge(&s, r, b, i, now, limit, live);
    }
    if (kly.grudge && kly.log == 1 && live && kly_r.drew && kly_r.drew != kly_r.said_drew) {      /* Log=1: how many drew, not what */
        kly_r.said_drew = kly_r.drew;
        klog("grudge: %d AI heister(s) have drawn how they take being shot by you this round (Log=2 says what)", kly_r.drew);
    }
}

static float kly_inif(const char *key, const char *def, float lo, float hi, float bad)
{
    char t[32]; char *e; double d;
    GetPrivateProfileStringA("Bots", key, def, t, sizeof t, klh_ini);
    d = strtod(t, &e);
    while (*e == ' ' || *e == '\t') e++;
    if (e == t || (*e && *e != ';') || d != d || d < lo || d > hi) {      /* one number and nothing else ('0,5' is not 0) */
        if (t[0] && strcmp(t, def)) klog("grudge: %s=%s is IGNORED: it must be one number of %g .. %g with a decimal point", key, t, lo, hi);
        return bad;
    }
    return (float)d;
}

static void kly_init(void)
{
    char t[64]; int a = 40, b = 30, c = 30, sum;
    klyo.factor = kly_inif("OnlineCrewHealth", "0", 0.25f, 10, 0); if (klyo.factor == 1.0f) klyo.factor = 0;      /* own key: works without [Bots] Enable (online has no Arcade crew) */
    klyo.dry = klyo.factor > 0 && GetPrivateProfileIntA("Bots", "OnlineCrewHealthDry", 0, klh_ini) != 0;
    kog_.on = GetPrivateProfileIntA("Bots", "OnlineGrudge", 0, klh_ini) != 0; kog_.dry = kog_.on && GetPrivateProfileIntA("Bots", "OnlineGrudgeDry", 0, klh_ini) != 0;
    if (kog_.on) klog("grudge: OnlineGrudge on%s: HOST only; a human who kills an AI heister becomes the traitor (rules slot 129; the kill is seen at the soldier's hit handler 0x8473a0 via a private ZSoldier table); bench-run live 11-06 (grudge_1106 pass A + B)", kog_.dry ? " (dry log)" : "");
    kly.log = (int)GetPrivateProfileIntA("Bots", "Log", 1, klh_ini); if (kly.log < 0) kly.log = 0; if (kly.log > 2) kly.log = 2;
    if (klyo.factor > 0) klog("grudge: OnlineCrewHealth x %.2f%s: HOST only, online rounds, data writes only; acts when this machine hosts a round (GUESS: a client's hit is priced against the host's health object, not traced)", klyo.factor, klyo.dry ? " (dry log)" : "");
    if (!GetPrivateProfileIntA("Bots", "Enable", 0, klh_ini)) return;
    kly.crew = kly_inif("CrewHealth", "1", 0.25f, 10, 0); if (kly.crew == 1.0f) kly.crew = 0;
    kly.bs_health = kly_inif("BackstabHealth", "1", 0.25f, 10, 0); if (kly.bs_health == 1.0f) kly.bs_health = 0;
    kly.bs_aim = kly_inif("BackstabAim", "-1", -1, 100, -1);
    kly.mark = GetPrivateProfileIntA("Bots", "BackstabMark", 0, klh_ini) != 0;
    kly.grudge = GetPrivateProfileIntA("Bots", "Grudge", 0, klh_ini) != 0;
    GetPrivateProfileStringA("Bots", "GrudgeMix", "40,30,30", t, sizeof t, klh_ini);
    if (sscanf(t, "%d , %d , %d", &a, &b, &c) != 3 || a < 0 || b < 0 || c < 0 || (sum = a + b + c) <= 0) { a = 40; b = 30; c = 30; sum = 100; if (kly.grudge) klog("grudge: GrudgeMix=%s is IGNORED (three shares: ESCALATES,SNAPS,TAKES IT): 40,30,30 stands", t); }
    kly.mix[0] = a * 100 / sum; kly.mix[1] = b * 100 / sum; kly.mix[2] = 100 - kly.mix[0] - kly.mix[1];
    kly.base = kly_inif("GrudgeBase", "2", 0, 600, 2); kly.per = kly_inif("GrudgePer", "0.15", 0, 60, 0.15f); kly.max = kly_inif("GrudgeMax", "20", 0.5f, 3600, 20);
    kly.good = kly_inif("GrudgeForGood", "60", 0, 100000, 60); kly.forget = kly_inif("GrudgeForget", "45", 0, 36000, 45);
    kly.gmark = kly.grudge && GetPrivateProfileIntA("Bots", "GrudgeMark", 0, klh_ini) != 0;
    kly.snap = (int)GetPrivateProfileIntA("Bots", "GrudgeSnapHits", 0, klh_ini); if (kly.snap < 0 || kly.snap > 50) kly.snap = 0;
    kly.on = kly.crew > 0 || kly.bs_health > 0 || kly.bs_aim >= 0 || kly.mark || kly.grudge || (ktrait.on && !ktrait.dry);      /* ktrait.on: a character's trait needs the tick (kltrait.c; kltt_init runs first) */
    if (!kly.on) return;                      /* no key: no line, no tick - the hook is what it was */
    klog("grudge: on; CrewHealth x %.2f (0 = the game's) BackstabHealth x %.2f BackstabAim %.0f %% (-1 = his own) BackstabMark=%d; Grudge=%d mix ESCALATES %d / SNAPS %d / TAKES IT %d, an answer of %.1f s + %.2f s per %% of his health you took (%.0f s at most), for good at %.0f %% (0 = never), forgotten after %.0f s; GrudgeSnapHits=%d (0 = drawn: 1 or 2) GrudgeMark=%d; Arcade only, only on a level that is not stock, data writes only",
         kly.crew, kly.bs_health, kly.bs_aim, kly.mark, kly.grudge, kly.mix[0], kly.mix[1], kly.mix[2], kly.base, kly.per, kly.max, kly.good, kly.forget, kly.snap, kly.gmark);
    if (kly.grudge && GetPrivateProfileIntA("Bots", "Escort", 0, klh_ini) > 0)      /* review M2: said once, at any Log level */
        klog("grudge: [Bots] Escort is on: an escort is turned on you only if klescort.c asks klgrudge.c about it (the three lines of re\\bots_fight.md 4.4: it then lets the escort go); a klescort.c without them keeps its escort, and the escort is NOT turned while it escorts you");
    if (kly.grudge && !kly.gmark)             /* review M3: the owner is to know it before his ini has Grudge */
        klog("grudge: GrudgeMark=0: KILLING a bot that fights you by Grudge makes YOU the traitor (the game's own rule, 0x6709f4: he carries no traitor flag) - also one that turned on you for good; GrudgeMark=1 gives such a bot the score table's traitor bit");
}

#endif /* KLGRUDGE_C */
