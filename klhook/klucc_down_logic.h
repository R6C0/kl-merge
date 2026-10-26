/* klucc_down_logic.h - the PURE parts of klucc_down.c ([Ucc] DownOnly: a hidden undercover cop's hits only DOWN a heister, never kill him).
 * No game reads here: klucc_down.c feeds it numbers it read; klud_test.c checks it off-game (tools/run_harness_linux.sh klud_test).
 * Research and every address: re/ucc_down_only.md. */
#ifndef KLUCC_DOWN_LOGIC_H
#define KLUCC_DOWN_LOGIC_H

/* crew-record flag bits of the FA score object ([[rules+0x2c] + 0x98 + 4 i], rules slot 114 = 0x625be0 -> 0x571750 -> 0x4aece0) */
#define KLUD_F_DEAD      0x00000004u
#define KLUD_F_POLICE    0x00000008u
#define KLUD_F_UCC       0x00000080u     /* set by the Sv rules when it makes a player the undercover cop (0x40fabc push 0x80) */
#define KLUD_F_DIRTYCOP  0x00001000u
#define KLUD_F_WAITING   0x00004000u
/* m_iFlags of the player's net object: word [[P+0x274c] + 0x4c4] ^ 0xdead (0x431f60); SetUndercoverCop sets bit 8 (0x8c9601) */
#define KLUD_NF_UCC      0x0008u

/* The session this part works in: game type 4 (the FA family) and the FA sub-mode word [0x168e59c] == 1 (Undercover Cop).
   Host and client alike: the hit is applied on the VICTIM's own PC (re/ucc_down_only.md 2), so every heister's PC needs the key. */
static int klud_gate(unsigned long mode, unsigned long submode)
{
    return mode == 4 && submode == 1;
}

/* Is the attacker the undercover cop? Any one of the three marks the game leaves (each is read on a different peer, re/ucc_down_only.md 3):
   the player byte +0x2729 (0x4622b0, set on the machine that runs SetUndercoverCop's handler), the replicated net flag bit 8, the score flag 0x80. */
static int klud_is_ucc(unsigned char b2729, unsigned short netflags, unsigned long scoreflags)
{
    return b2729 != 0 || (netflags & KLUD_NF_UCC) != 0 || (scoreflags & KLUD_F_UCC) != 0;
}

/* Is the victim a heister (not police of any kind, not the UCC, not dead / waiting)? b2723 = police byte, b2729 = the UCC / dirty-cop byte. */
static int klud_is_heister(unsigned char b2723, unsigned char b2729, unsigned short netflags, unsigned long scoreflags)
{
    if (b2723 || b2729 || (netflags & KLUD_NF_UCC)) return 0;
    if (scoreflags & (KLUD_F_UCC | KLUD_F_POLICE | KLUD_F_DIRTYCOP | KLUD_F_DEAD | KLUD_F_WAITING)) return 0;
    return 1;
}

/* Hidden = not yet revealed. revealed_mask holds one bit per crew index (0..31); the reveal itself (P6) is not built yet, so the mask
   stays 0 and a UCC is hidden for the whole round. A crew index outside 0..31 (unknown) counts as hidden. */
static int klud_hidden(int idx, unsigned long revealed_mask)
{
    if (idx < 0 || idx > 31) return 1;
    return (revealed_mask & (1ul << idx)) == 0;
}

static int klud_fin(float f) { return f == f && f > -1e9f && f < 1e9f; }

/* The clamp. delta = the health change the game is about to apply (negative = damage), health = the victim's health before it,
   floor = the least health a UCC hit may leave. -> the delta to apply: never below (floor - health), never a heal turned into damage.
   A positive delta (a heal) and unreadable numbers pass unchanged; a victim already at or under the floor takes 0. */
static float klud_clamp(float delta, float health, float floor)
{
    float least;
    if (!klud_fin(delta) || !klud_fin(health) || !klud_fin(floor)) return delta;
    if (delta >= 0.0f) return delta;
    if (health <= floor) return 0.0f;
    least = floor - health;                 /* the most negative delta allowed */
    return delta < least ? least : delta;
}

/* Was the hit a would-be kill (so the clamp acted to keep him alive)? Used to queue the forced down of DownOnly=2. */
static int klud_lethal(float delta, float health, float floor)
{
    if (!klud_fin(delta) || !klud_fin(health) || !klud_fin(floor) || delta >= 0.0f) return 0;
    return health + delta <= floor;
}

/* Which rules vtable to use for the slot-15 wrapper. vt = the rules object's vtable now; sv / cl = the stock Sv / Cl tables;
   rk = klroundkeep.c's private Sv copy (0 = none); mine_sv / mine_cl = ours; rk_wants = klroundkeep will wrap the Sv object
   (TEST build or [Lobby] KeepRound) and waited_ms = how long we already waited for it.
   -> KLUD_VT_NONE (not an FA rules object), KLUD_VT_HAVE (already wrapped), KLUD_VT_RK (patch slot 15 into klroundkeep's table),
      KLUD_VT_WAIT (leave the stock Sv for klroundkeep a little longer), KLUD_VT_SV / KLUD_VT_CL (install our own copy). */
enum { KLUD_VT_NONE = 0, KLUD_VT_HAVE, KLUD_VT_RK, KLUD_VT_WAIT, KLUD_VT_SV, KLUD_VT_CL };
#define KLUD_RK_WAIT_MS 3000
static int klud_vt_plan(unsigned long vt, unsigned long sv, unsigned long cl, unsigned long rk, unsigned long mine_sv, unsigned long mine_cl,
                        int rk_wants, unsigned long waited_ms)
{
    if (!vt) return KLUD_VT_NONE;
    if (vt == mine_sv || vt == mine_cl) return KLUD_VT_HAVE;
    if (rk && vt == rk) return KLUD_VT_RK;
    if (vt == sv) return (rk_wants && waited_ms < KLUD_RK_WAIT_MS) ? KLUD_VT_WAIT : KLUD_VT_SV;
    if (vt == cl) return KLUD_VT_CL;
    return KLUD_VT_NONE;
}

#endif
