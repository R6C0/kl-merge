/* klogrudge_logic.h - [Bots] OnlineGrudge, the PURE decisions (no game memory, no clock of its own). Included by klgrudge.c and klogrudge_test.c.
   A HUMAN who kills an AI heister of the host's online round becomes the traitor, as stock FA does for human on human (rules slot 129 = 0x41d480, re\online_grudge_1106.md).
   Attribution (fix 1106b): slot 15 of the rules NEVER runs for an AI heister (ZFFPlayer-only), so the hit is seen at the SOLDIER's hit handler 0x8473a0 (ZSoldier slot 96, klgrudge.c kog_w_hit):
   health before / after the original; the LETHAL blow's attacker ([hit+0]) is the killer. Failing that, a fresh human
   stamp ([soldier+0x708], valid while clock < [soldier+0x70c]; it marks the FIRST tagger, not the killer) at the instant of death counts, unless a non-human hit the bot in the window. */
#ifndef KLOGRUDGE_LOGIC_H
#define KLOGRUDGE_LOGIC_H

#define KGO_F_TRAITOR 0x1u      /* client flags dword (rules vt+0x1c8): 1 traitor, 4 dead, 8 police, 0x40 escaped, 0x80 undercover */
#define KGO_F_DEAD    0x4u
#define KGO_F_POLICE  0x8u
#define KGO_F_ESCAPED 0x40u
#define KGO_F_UNDERCOVER 0x80u  /* stock 0x794a9b 'test al,al; js' sends an undercover cop down another path: never the traitor path */
#define KGO_WINDOW_MS 4000u     /* GUESS: a non-human hit / a human stamp counts for this long */
#define KGO_LETHAL_MS 3000u     /* GUESS: a lethal blow seen by the damage hook is the killer when the death is seen within this long */
#define KGO_NEVER     0xfffffffful

/* the game's own validity test of the last-aggressor field (klbrain_logic.h kbr_tgt_valid): a target, and the clock still before the stamp */
static int kgo_fresh(long clock, long stamp) { return stamp > 0 && clock < stamp; }

/* may client index k be made the traitor by killing a bot? flags = its score flags; 0 when it is a police/dead/escaped/undercover/already-traitor seat (slot 129 returns on flags & 0xc anyway) */
static int kgo_eligible(int k, unsigned long flags)
{
    if (k < 0 || k >= 16) return 0;
    return !(flags & (KGO_F_TRAITOR | KGO_F_DEAD | KGO_F_POLICE | KGO_F_ESCAPED | KGO_F_UNDERCOVER));
}

/* the victim: 0 = may count, 1 = not team Ally (2) = police / fed / a turned traitor, 2 = it is or was a traitor (marked / turned by klbrain.c).
   Stock rewards a criminal who kills a traitor; he must not be marked for it. */
static int kgo_victim(unsigned long team, int was_traitor)
{
    if (team != 2) return 1;
    return was_traitor ? 2 : 0;
}

/* who killed a bot that was seen dead just now? lw = the damage hook's lethal blow (-1 none seen, -2 by a non-human, >= 0 a human's client index), lw_age ms;
   cur = the human index of a still fresh stamp (-1 none / not human); latch = the human index of the last alive poll's stamp (-1 none);
   nh_age = ms since a non-human hit was seen (KGO_NEVER none). -> client index, or -1; *how: 1 lethal blow, 2 non-human hit in the window, 3 lethal blow by a non-human,
   4 no fresh human stamp, 5 the stamp changed since the last poll, 6 stamp at the instant of death */
static int kgo_decide(int lw, unsigned long lw_age, int latch, int cur, unsigned long nh_age, int *how)
{
    if (lw == -2 && lw_age <= KGO_LETHAL_MS) { *how = 3; return -1; }
    if (lw >= 0 && lw_age <= KGO_LETHAL_MS) { *how = 1; return lw; }
    if (cur < 0) { *how = 4; return -1; }
    if (nh_age <= KGO_WINDOW_MS) { *how = 2; return -1; }
    if (latch >= 0 && latch != cur) { *how = 5; return -1; }
    *how = 6; return cur;
}

/* the damage hook's lethal-blow slot after one hit: a lethal hit names its attacker (k >= 0 human, else -2); a NON-lethal non-human hit clears a human's earlier predicted
   lethal blow (the prediction was wrong: the bot lived, and a cop / bot may finish him), so the human is not blamed; anything else keeps it */
static int kgo_after_hit(int lw, int human, int k, int lethal)
{
    if (lethal) return human && k >= 0 ? k : -2;
    if (!human && lw >= 0) return -1;
    return lw;
}

/* health before / after one run of the soldier's hit handler (completion synchronous = GUESS): finite numbers only. hurt = the hit took health; lethal = it took the last of it */
static int kgo_hurt(float hp0, float hp1) { return hp0 == hp0 && hp1 == hp1 && hp0 < 1e9f && hp1 > -1e9f && hp1 < hp0; }
static int kgo_lethal(float hp0, float hp1) { return kgo_hurt(hp0, hp1) && hp0 > 0.01f && hp1 <= 0.0f; }

/* the hook only acts in Fragile Alliance proper: sub-mode [0x168e59c] 0 (1 Undercover Cop, 2 Cops and Robbers: stock never makes a traitor there) */
static int kgo_submode_ok(long sub) { return sub == 0; }

/* per-record bookkeeping: 0 = nothing, 1 = alive-poll, 2 = fire now, 3 = first seen dead (booked, never fires). dead = status 7; done = already booked for this actor; first = first sight */
static int kgo_step(int dead, int done, int first)
{
    if (done) return 0;
    if (!dead) return 1;
    return first ? 3 : 2;
}

/* the set of actors booked this round (no double fire when a record slot is reused): 64 addresses, oldest evicted */
#define KGO_NDONE 64
static int kgo_done_has(const unsigned long *a, int n, unsigned long v) { int i; for (i = 0; i < n && i < KGO_NDONE; i++) if (a[i] == v) return 1; return 0; }
static void kgo_done_add(unsigned long *a, int *n, unsigned long v)
{
    if (kgo_done_has(a, *n, v)) return;
    a[*n % KGO_NDONE] = v; (*n)++;
}
#endif
