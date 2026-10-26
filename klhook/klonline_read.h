/*
 * klonline_read.h - the PURE part of klonline_read.c (no game, no globals): the snapshot struct and the small decisions.
 * Included by klonline_read.c (inside klhook.c, after klbot.c) and by klonline_read_test.c (off-game check).
 */
#ifndef KLONLINE_READ_H
#define KLONLINE_READ_H

#define KLOR_MAX    16                 /* seats read (the online FA cap is 12; the arrays of klbot.c hold 16) */
#define KLOR_NBOT   8                  /* AI heisters read (klhud.c's online bot rows were capped at 8) */

struct klor_row {
    int used;                          /* 1 = a seat in use / a bot found */
    int seat;                          /* human: the seat number = index in [rules+8] = index in every S array; bot: -1 */
    int bot;                           /* 1 = an AI heister (no record, no S row) */
    DWORD rec;                         /* human: the 0x74-byte record; 0 for a bot */
    DWORD player;                      /* human: the ZFFPlayer ([[rec]+0x378], GUESS read from re/round_end_online.md); bot: 0 */
    DWORD actor;                       /* the body's entity: human = player (when its type is heister), bot = the ZFFActor */
    DWORD model;                       /* the model the body wears NOW ([[actor+4]+0x68]); 0 = unreadable */
    int ch;                            /* 1.. = the character in the level's klw_source list whose root is the model; 0 = none matched */
    char name[32];                     /* the heister CHARACTER's name ("J.C.", "Tommy", ...); "" = unknown (caller falls back) */
    DWORD flags;                       /* human: S+0x98 custom flags; bot: 0 */
    long money, loot, reward;          /* human: Sharable + Unsharable, Unsharable, Sharable (S+0x188 / S+0x224); bot: 0 */
    int kills, police_kills;           /* human: S+0xec / S+0x170 (i8); bot: 0 */
    int killer;                        /* human: KillerIndex S+0xe0 (i8) = the seat that killed him, -1 none; LATCHED while he is dead */
    int alive;                         /* bot: health > 0; human: no dead / escaped bit in flags */
};

struct klor_snap {
    struct klb_snap b;                 /* klbot.c's online snapshot (the SAME struct Arcade uses): rules, state, on_* arrays; veh / timer / vehicle filled here from the mirrors */
    int ok;                            /* 1 = the rules object is Sv / Cl and the score object S passed its vtable test */
    int host;                          /* 1 = ZGameRulesFragileAllianceSv */
    DWORD score;                       /* S = [rules+0x2c], DDL_ZScoreFragileAlliance (vtable 0xbd5184) */
    int local;                         /* the local seat (osd player list element +0xefc), -1 unknown */
    struct klor_row r[KLOR_MAX]; int n;           /* humans in use, in seat order (r[i].seat is the seat) */
    struct klor_row bot[KLOR_NBOT]; int nbots;    /* AI heisters, living first */
    int round, rounds;                 /* S+0x34c / S+0x3d0 (i8); 0 = not plausible (not read) */
    float clock, length;               /* [rules+0x4c] (the HUD clock mirror) / S+0x324 (round length) */
    float esc_timer; BYTE esc_state; DWORD vehicle;   /* [rules+0x1d8] / [rules+0x1dc] / [rules+0x1e4] mirrors */
    int names_ok;                      /* how many rows got a character name from the model */
};

/* a seat is 'dead' for the killed-by latch: the Arcade score flags the online word carries (4 dead, 0x10 / 0x4000 waiting; GUESS that they carry over) */
static int klor_flags_dead(DWORD f) { return (f & (0x4u | 0x10u | 0x4000u)) != 0; }

/* the latch: *latched is the killer seat last seen while the seat was dead. dead = the seat is dead now, killer = KillerIndex now (-1 none).
   A living seat clears the latch; a dead one takes a valid killer and keeps it when the game clears the byte (rules slot 14 resets it when the killer leaves). -> the seat to show, -1 = none */
static int klor_killer_latch(int *latched, int dead, int killer, int nseats)
{
    if (!dead) { *latched = -1; return -1; }
    if (killer >= 0 && killer < nseats) *latched = killer;
    return *latched;
}

/* a round counter that can be shown: 1 <= round <= rounds <= 30 */
static int klor_round_ok(int round, int rounds) { return round >= 1 && rounds >= 1 && rounds <= 30 && round <= rounds; }

/* the loot bar's share: taken so far of the largest total seen (both >= 0). 0..1 */
static float klor_loot_share(long initial, long remaining)
{
    if (initial <= 0 || remaining < 0) return 0.0f;
    if (remaining > initial) return 0.0f;
    return (float)(initial - remaining) / (float)initial;
}

/* capital letters for the KILLED BY line */
static void klor_upper(char *s) { for (; *s; s++) if (*s >= 'a' && *s <= 'z') *s = (char)(*s - 32); }

#endif /* KLONLINE_READ_H */
