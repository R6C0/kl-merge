/*
 * klhud_values.c - the numbers the HUD draft still lacked, as small guarded readers (2026-10-11, track D).
 * Part of KLHook: to be included by klhook.c AFTER klbot.c (struct klb_snap, klb_read) and BEFORE klhud.c.
 * READS ONLY: no write, no call into the game, no code byte. Every read goes through klh_rd / klh_rd32; every reader
 * answers 0 (or the 'nothing' value its comment names) when a read fails or the score object is not a ZHeistScore.
 * NOTHING HERE HAS RUN IN THE GAME. Facts and how each was established: re\hud_values.md (same order as below).
 * EXE = read in kl2.exe build 0490 (capstone through debug\kl.py; scratch listings in the session's scratchpad
 * agents\hudD). GUESS / NOT ESTABLISHED are said where they apply.
 *
 * THE OBJECTS
 *   rules = [[0x168e9e4]+0x54], ZGameRulesHeist, vtable 0xbd3514 (klbot.c 1) = the Arcade rules class (the multiplayer
 *           ones are ZGameRulesFragileAllianceSv 0xbd2eb4 / Cl 0xbd31e4; Heist is the single-player subclass).
 *   score = [rules+0x5f8] = rules+0x36c, a ZHeistScore (vtable 0xbd3500) built inside the rules object: EXE ctor
 *           0x835509 `lea ecx,[esi+0x36c] / mov [ecx],0xbd3500`, slot 36 0x7c6d74 `lea eax,[esi+0x36c] / mov
 *           [esi+0x5f8],eax`. Its head is the replicated score record of the multiplayer class (the .rdata names
 *           m_fRoundTime, m_fRemainingRoundTime, m_iNumRounds, m_iCurrentRound belong to it: the ORDER fits the
 *           fields below, the name-to-offset pairing itself is a GUESS).
 *
 * (a) LIVES = signed byte [score+0x6c]. EXE: ctor 0x75bccd writes 3; the round-end rule 0x5dfffd `dec byte
 *     [eax+0x6c]` when client 0 did not escape (slot 106 = flag 0x40); Quit 0x418730 writes 0; the state after a
 *     round is 0x28 (game over) when it is <= 0 (0x4fa0f7). THE STOCK LIST READS THIS BYTE, NOT +0x44: 0x6f3116
 *     `movsx esi, byte [eax+0x6c]` and appends the text "{skull}" that many times to the player's name; so do the
 *     round-over page 0x7dfa5c and the intro 0x6d82ac. [score+0x44] IS NOT LIVES (see c).
 *     The skull is a GLYPH of the font, not a HUD picture: 0x7bb920 turns "{name}" into a private-use character
 *     through the table 0x926350 - "skull" / "skull_kb" -> U+E018 (0x9266a2), "moneysymbol" -> U+E019, "heist1up" ->
 *     U+E017, the pad buttons from U+E000. The strings are UTF-8 (0x4e8460 is a UTF-8 decoder), so the skull in a
 *     C string is EE 80 98. A lost life has NO look of its own in the stock HUD: the skull is simply not appended.
 *     ASSUMED: SetText (0x896e50) decodes the same UTF-8 (the stock code hands it exactly such strings) and the
 *     FA font (osd+0xd54) holds U+E018 (the stock top-left text is made with that font). NOT ESTABLISHED: whether
 *     the text's colour tints a page-1 (coloured) glyph. The stock code writes a space (0xb787a0, 0x7bb9c4) before
 *     each glyph; kluv_skulls does the same.
 *     OUR HUD (re\hud_layout.md, the own row): 'lives = three skulls (178) 12 x 12 ..., ink / 4c0c0c0d when lost' =
 *     three PICTURES (HUD picture 178, 'Kill', 32 x 32), not the glyph: kluv_skull_x / _y / _argb give the place and
 *     the tint of skull k, klhud.c queues them with klu_addpic (WIRING step 5). The glyph string stays as a TEST
 *     key (Lives=2). GUESS: picture 178's chunk is type 5 like 170 / 181 (klhud.c's handle[] test decides at run
 *     time: no handle = 'LIVES n' in the round line instead) and it takes the record's tint (drawn dark on chalk).
 * (b) MONEY. score lines, EXE from the menu variables of 0x5b5f40 (the round-over / status pages):
 *       +0x04 HeistPointsEscape   +0x08 HeistPointsNPCEscape   +0x0c HeistPointsLoot   +0x10 HeistPointsKills
 *       +0x14 the kill COUNT      +0x18 HeistPointsRevenge     +0x1c HeistPointsTime   +0x20 HeistPointsYellow
 *       +0x24 HeistPointsTraitor  +0x28 (not shown alone)      +0x2c HeistPointsCivilians
 *       +0x30 HeistPointsRound = 'ROUND SCORE' (page key Outro_Round_Points, 0x7df75b)
 *       +0x34 the best round so far (0x5e0030)                 +0x38 HeistPointsTotal = Outro_Total_Points
 *     +0x30 is written ONLY at the round's end (0x783010, from 0x70b920): +0x04 = [tuning+0xbec] and +0x1c =
 *     ftol([score+0x68]) * [tuning+0xc08] and +0x0c = record 0's payout when client 0 escaped, else 0; then
 *     +0x30 = +4 +8 +c +10 +18 +1c +20 +24 +2c; then [+0x38] += [+0x30] (0x5e001b). So IN the round +0x30 is 0.
 *     The live numbers the game itself shows:
 *       'Total score' (stock HUD)  0x807520 = carried(client 0) + (+4 +8 +c +10 +18 +1c +20 +24 +2c) + [+0x38]
 *       the round so far           slot 54 = 0x711010(0) = the same without [+0x38]
 *       carried                    slot 56 = 0x6f86c0(i) = [score+0x150 + 4 i]   (the stock list's 2nd column)
 *       rewards                    slot 55 = 0x6c05f0(i) = [score+0x184 + 4 i]   (3rd column; kill pay and fines,
 *                                  written by the kill rule 0x670968; can be negative)
 *     and per crew record, recomputed EVERY FRAME in state 0x19 / 0x29 by 0x796410:
 *       record+0x28  the SPLIT he would get if the round ended now: pool / sharers when his flag 0x40 (escaped) is
 *                    set and he is no traitor; for police (flag 8) / flag 0x80 what he carries
 *       record+0x2c  his PAYOUT = rewards + split (a traitor who escaped: rewards + what he carries)
 *       [rules+0x604] the pool (what the escaped, living, non-police, non-traitor records carry), [rules+0x608]
 *       their number, [rules+0x60c] the index of the record with the largest payout (-1 = a tie / nobody).
 *     The round-over page (0x7dede0): 'Your split' = record+0x28 ('Your grab' = carried for a traitor, 'Finder's
 *     fee' = record+0x28 for police), 'Your reward' = rewards, 'Round score' = +0x30, 'Total score' = +0x38.
 * (c) ROUND n OF m: n = signed byte [score+0x45] (ctor 1; ++ at 0x74bcf0 only when record 0's status is 6 =
 *     escaped: a failed round is played again under the same number). m = byte [score+0x44]: ctor 3, slot 36 writes
 *     0x6a1a90(settings) = the constant 10 in Arcade (0x6a1aa2 `mov al, 0xa`), the lobby's 'number of rounds'
 *     otherwise; getter slot 40 = 0x8e1090, setter slot 39. Both are sent together as session properties 1 and 0
 *     (0x74bbc6 .. 0x74bbeb). The page's own 'HeistRoundsCounter' is "<Round> %d" with n only (0x5ba92e).
 *     NOT ESTABLISHED: whether an Arcade session ends after round 10 (no compare of n with m was found in the
 *     Heist class; a sweep of every byte access to +0x44 / +0x45 in .text found none either) - and AGAINST it:
 *     the difficulty tables take n clamped to 1 .. 11 (0x591b89 .. 0x591b97 `cmp bl, 0xb`; re\balance.md has eleven
 *     rows), one more than m. So 'OF 10' is the game's nominal number, shown only on request (RoundOf=1).
 * (d) THE LEVEL'S LOOT = int [rules+0xdd0]. EXE: slot 81 = 0x4c1dc0(amount, object) appends the object to the list
 *     at rules+0xdbc (count +0xdc0, pointers [+0xdcc]) and does `add [esi+0xdd0], eax` (+0xdd4 a copy; +0xe70 /
 *     +0xe74 the largest single object and its amount); called by ZOnlineMoneyCtrl (vtable 0xbc874c) slot 13 =
 *     0x4d8e80 for money of type [obj+0x38] 0 and 2 with [obj+0x34] = its amount; type 1 goes to the other list
 *     (slot 79, rules+0xda8) and adds nothing. Reset by slot 3 = 0x4fb620. The game uses the sum itself: 0x72812b
 *     compares what a client carries with [rules+0xdd0] * 0.4 (double 0xb21fe0) for an announcement.
 *     What is LEFT = the sum of [obj+0x34] > 0 over that list (0x4536e0 'depleted' = [obj+0x34] <= 0).
 *     CAVEATS: a civilian's money controller counts like a safe. Slot 22 (0x8ea4e0) is the money object's STATE
 *     RESTORE: it reads a stream, puts [obj+0x8c] back into [obj+0x34] (0x8ea50e .. 0x8ea51a) and, in Arcade only
 *     (0x8ea601 `call 0x7f6850`), calls rules slot 81 again for types 0 and 2 (0x8ea622) - most likely the
 *     re-registration after the rules' reset (slot 3 zeroes +0xdd0 and +0xdc0). 0x4c1dc0 has NO test for an object
 *     that is already in the list (EXE, whole): if the restore ever runs without the reset the object is listed and
 *     counted twice. NOT ESTABLISHED whether that happens; kluv_loot_scan therefore counts the pointers that stand
 *     in the list more than once and kluv_loot_total takes their [obj+0x8c] off again (ASSUMED: +0x8c is the amount
 *     the second registration added - it is what the restore has just written into +0x34). The dump prints the
 *     raw sum, the duplicates and the corrected number; live check L1b (round 2) settles it.
 * (e) THE VEHICLE'S KIND = byte [rules+0x1ec] (slot 95 = 0x5822d0). EXE: 0xff from the ctor (0x8356da), then by
 *     three class tests of the vehicle [rules+0x1e4] (0x42cfb0 and twins): 1, 2 or 3. A vehicle of none of the
 *     three classes runs into an `int3` (0x42d007) before the 'kind 0' write: an assert in retail, so 0 is not a
 *     value a running round has. THE CLASSES (EXE, the static initialisers that hand each type pair to the class
 *     registration): 1 = 0x7d29f0 tests pair 0x168cddc = ZHavokCar (0xafcd10: name "ZHavokCar", parent
 *     "ZHavokLnkObj"; older notes in the repo call this pair ZHavokLnkObj - it is the car's); 2 = 0x7ae760 tests
 *     0x168ce48 = ZHeli (0xafcde0, parent ZHavokLnkObj); 3 = 0x409920 tests 0x168d624 = ZAnimatedVehicle (0xafda50,
 *     parent ZSTDOBJ, setter 0x6feba0) = the key-framed vehicle (F07's van). The stock clock (0x81e16e): `cmp al,
 *     3` -> picture 170 ([elem+8]+0x7f8), ANY other value -> picture 171 (+0x804) - so a Havok car (Dead Men's
 *     spline ZHavokCar builds) gets the helicopter picture in the stock HUD. OUR dial: kind 2 -> 171, else 170
 *     (kluv_vehicle_pic); the stock rule is kept for the log (kluv_vehicle_pic_stock).
 * (f) THE ROUND'S LENGTH = float [score+0x3c]; left = float [rules+0x4c]; played = float [rules+0x50]. EXE: the
 *     stock clock prints ftol(rules slot 73 = 0x61d070 = `fld [ecx+0x4c]`); the rules tick 0x74b724 does +0x4c -=
 *     dt and +0x50 += dt from state 0x19 on, clamps +0x4c at 0; slot 36 = 0x7c6d70 writes +0x4c = 0x6d3130() and
 *     the same into [score+0x3c] when it is > 0; 0x6d3130 = float 360.0 (0xb2e7fc) in Arcade, the lobby's time
 *     limit otherwise; slot 41 = 0x7f09a0 (set time) also writes +0x3c. [rules+0x200] (klhud.c's watch, klfed.c)
 *     is the Heist class's own END timer (0x5dff40), 600.0 at the round start (0x8c7a8b) and set with +0x4c by
 *     slot 42: not what the clock shows. [score+0x40] is the 'remaining' copy slot 85 reads back.
 *     ASSUMED: nothing shortens +0x3c during a round (slot 42 = 0x47d190, the cut klfed.c imitates, writes
 *     [rules+0x4c], [rules+0x200] and [score+0x40] and leaves +0x3c). NOT ESTABLISHED: what puts 360 back into
 *     [rules+0x4c] for the NEXT round (the round reset 0x8c7a80 writes 0 there and 600 into +0x200; slot 36 is
 *     the only writer of 360 that was read) - the ring is left / length whatever does it; live check L1b.
 * (g) A CREW RECORD'S STATE as the stock list decides it (0x572050, in THIS order) from the flag dword of rules
 *     slot 114 = 0x771a10(i) = [score+0x1d4 + 4 i] - indexed by the crew index like the money (EXE; klhud.c had
 *     this as an assumption): 0x4000 -> 6 (dead, waiting to return as police), 4 -> 7 (dead), 1 -> 1 (traitor),
 *     0x1000 -> 2 (dirty cop), 8 -> 5 (police), 0x80 -> 3 (4 with 0x40000: undercover cop), 0x10 -> 6, else 0.
 *     More bits: 0x20 aboard (set with status 4 by the boarding rule 0x684157 / 0x684236, players and actors
 *     alike), 0x40 escaped (slot 106 = 0x8110e0). The stock list has NO look for aboard / escaped. klbot.c's
 *     reading agrees: status byte record+0x10 0 in play, 1 waiting, 4 aboard, 6 escaped, 7 dead; record+0x79 mask
 *     2 is the BOT's own 'turned traitor' mark, which the stock list does NOT show (it tests score flag 1 only).
 *     Status 5 is NOT established (klfed.c's table prints 'escaped' for it; nothing read here sets it): no reader
 *     below gives it a meaning.
 *     THE FLAGS AT A DEATH (EXE): the kill rule sets 4 (0x70479c `or eax, 4`) and THEN, for a human who will come
 *     back as police, the waiting branch adds 0x4000 and status 1 (0x704840) - so he most likely reads 00004004
 *     while waiting; slot 204 = 0x7622f0 clears 0x34 (4, 0x10, 0x20) and sets 8, the respawn 0x4b28d0 clears
 *     0x4000 (0x4b2a54): the living fed reads 00000008.
 *     TWO DECISIONS, on purpose: kluv_stock_state = the stock list's own order, for the log only; kluv_state /
 *     kluv_kind = OUR rows (the one klhud.c runs): dead / waiting, escaped, FED BEFORE TRAITOR (the owner,
 *     2026-10-11: 'i became a traitor, as a fed youre only a fed'; the stock list has traitor first), traitor
 *     (score flag 1 or the bot's own mark), aboard, crew.
 * (h) KILLED BY = signed byte [score+0x10c + i] = the crew index of who killed client i (rules slot 25 =
 *     0x4838d0, only in state 0x19; -1 = nobody of the crew: an enemy, a fall, the kill box). The death panel's
 *     text is built by 0x500670 from the .LOC (AllLevels/Menu/Online/Respawn 'KilledBy', AllLevels/Interface/
 *     Online/Kill 'FA_DieFrom<role>' / 'FA_DieFromSelf' / the kill box's own key).
 *     THE ROUND-OVER RESULT (0x7df067 .. 0x7df428; keys under AllLevels/Interface/Online/GameEnd/): title
 *     'Game_Over' when lives <= 0 else 'Round_Over'; line: every record in use has flag 0x40 -> 'All_Esc'; else
 *     your flag 0x40 -> 'You_Esc'; else every record has 4 or 8 -> 'All_Dead'; else no record is left that is
 *     neither escaped nor police -> 'Last_Esc'; else your flags have 4 or 8 -> 'You_Dead'; else 'Time_Up'; and
 *     'LifeLost' is added whenever your flag 0x40 is clear. The English wording below is OURS (the .LOC has the
 *     game's; it was not read out of a level here).
 *
 * NAMES: everything here is kluv_ / KLUV_ ('klu values'); klv_ / KLV_ belong to klhop.c and klvis.c.
 * WIRED INTO klhud.c by re\hud_values.md 3: kluv_lives, kluv_skull_x / _y / _argb, kluv_skulls (Lives=2 only),
 * kluv_flags, kluv_kind, kluv_round, kluv_loot_total / _share, kluv_vehicle_pic, kluv_round_left / _len / _played,
 * kluv_dump. A LIBRARY for the pop-up / round-over tracks, used by the dump only so far: kluv_money / kluv_money3,
 * kluv_round_frac, kluv_killer, kluv_result / _key / _text, kluv_loot_scan, kluv_stock_state, kluv_vehicle_kind.
 */
#ifndef KLHUD_VALUES_C
#define KLHUD_VALUES_C

#define KLUV_SCORE_VT    0x00bd3500u           /* ZHeistScore */
#define KLUV_MONEY_VT    0x00bc874cu           /* ZOnlineMoneyCtrl (d) */
#define KLUV_ARCADE_LEN  0x00b2e7fcu           /* float 360.0: 0x6d3130's answer in Arcade (f) */

#define KLUV_S_LINES     0x04                  /* eleven dwords +0x04 .. +0x2c, then +0x30 round, +0x34 best, +0x38 total */
#define KLUV_S_ROUNDPTS  0x30
#define KLUV_S_BEST      0x34
#define KLUV_S_BANKED    0x38
#define KLUV_S_LENGTH    0x3c                  /* float: the round's length (f) */
#define KLUV_S_NROUNDS   0x44                  /* byte: m (c) - NOT lives */
#define KLUV_S_ROUND     0x45                  /* byte: n (c) */
#define KLUV_S_LIVES     0x6c                  /* signed byte (a) */
#define KLUV_S_KILLER    0x10c                 /* one signed byte a client (h) */
#define KLUV_S_CARRIED   0x150                 /* one int a client */
#define KLUV_S_REWARDS   0x184
#define KLUV_S_FLAGS     0x1d4
#define KLUV_R_LEFT      0x4c                  /* rules: float, the clock (f) */
#define KLUV_R_PLAYED    0x50                  /* rules: float, seconds played since GO */
#define KLUV_R_VEHICLE   0x1e4
#define KLUV_R_KIND      0x1ec                 /* rules: byte (e) */
#define KLUV_R_POOL      0x604                 /* rules: int pool, +0x608 sharers, +0x60c leader (b) */
#define KLUV_R_LOOTN     0xdc0                 /* rules: number of registered money objects, pointers at [+0xdcc] (d) */
#define KLUV_R_LOOTP     0xdcc
#define KLUV_R_LOOT      0xdd0                 /* rules: int, the level's registered loot (d) */
#define KLUV_REC_SPLIT   0x28                  /* crew record: int (b) */
#define KLUV_REC_PAYOUT  0x2c
#define KLUV_M_AMOUNT    0x34                  /* money object: int, what is in it now (d) */
#define KLUV_M_START     0x8c                  /* money object: int, what the state restore 0x8ea4e0 puts back into +0x34 (d) */
#define KLUV_LOOT_MAX    1024                  /* more registered money objects than this = not a list we read */

#define KLUV_LIVES_MAX   3                     /* the ctor's number (0x75bccd) */
#define KLUV_SKULL       "\xee\x80\x98"        /* U+E018 in UTF-8 (a) */
#define KLUV_DOLLAR      "\xee\x80\x99"        /* U+E019 'moneysymbol' */
#define KLUV_PIC_CAR     170
#define KLUV_PIC_CHOPPER 171
#define KLUV_KIND_CAR    1                     /* ZHavokCar (e) */
#define KLUV_KIND_HELI   2                     /* ZHeli */
#define KLUV_KIND_ANIM   3                     /* ZAnimatedVehicle */

/* (a) the own row's three skull pictures (re\hud_layout.md: 'three skulls (178) 12 x 12 from x 33 + name width + 8,
   ink / 4c0c0c0d when lost'). klhud.c has no width of a text, so the name's width is ESTIMATED from its length: every
   number here is a named GUESS until a picture has shown the row (live check L2b). */
#define KLUV_SKULL_PIC   178                   /* HUD picture 'Kill', 32 x 32 (re\hud_layout.md, re\hud_data.md) */
#define KLUV_SKULL_SIZE  12.0f
#define KLUV_SKULL_GAP   2.0f                  /* between two skulls */
#define KLUV_SKULL_LEAD  8.0f                  /* after the name (the layout's '+ 8') */
#define KLUV_NAME_CHARW  9.0f                  /* GUESS: the mean width of one character of a name in the row's font */
#define KLUV_CASH_ROOM   64.0f                 /* GUESS: kept free at the row's right end for the cash ('$1.2M') */
#define KLUV_BLOCK_UP    4.0f                  /* klhud.c klu_row: the painted block starts 4 above the text's y and is one row pitch high */
#define KLUV_C_SKULL_ON      0xff0c0c0du       /* ink: a life he has, on the chalk block */
#define KLUV_C_SKULL_LOST    0x4c0c0c0du       /* the layout's lost look on the block */
#define KLUV_C_SKULL_ON_BARE   0xfff3f0eau     /* no block (Plates=0): chalk ... */
#define KLUV_C_SKULL_LOST_BARE 0x4cf3f0eau     /* ... and the same alpha for a lost one */

/* the flag bits of [score+0x1d4 + 4 i] (g) */
#define KLUV_F_TRAITOR   0x1
#define KLUV_F_DEAD      0x4
#define KLUV_F_POLICE    0x8
#define KLUV_F_ABOARD    0x20
#define KLUV_F_ESCAPED   0x40
#define KLUV_F_UNDERCOP  0x80
#define KLUV_F_DIRTYCOP  0x1000
#define KLUV_F_WAITING   0x4000

/* kluv_stock_state's / kluv_state's answers: 0..7 are the stock list's own numbers (0x572050), 8 / 9 are ours */
enum { KLUV_ST_CREW = 0, KLUV_ST_TRAITOR = 1, KLUV_ST_DIRTYCOP = 2, KLUV_ST_UNDERCOP = 3, KLUV_ST_UNDERCOP2 = 4, KLUV_ST_POLICE = 5,
       KLUV_ST_WAITING = 6, KLUV_ST_DEAD = 7, KLUV_ST_ABOARD = 8, KLUV_ST_ESCAPED = 9 };
/* kluv_kind's answers = klhud.c klu_row's kinds */
enum { KLUV_K_CREW = 0, KLUV_K_YOU = 1, KLUV_K_TRAITOR = 2, KLUV_K_DEAD = 3, KLUV_K_ESCAPED = 4, KLUV_K_FED = 5 };
/* kluv_result's answers (h) */
enum { KLUV_RES_NONE = 0, KLUV_RES_ALL_ESC, KLUV_RES_YOU_ESC, KLUV_RES_ALL_DEAD, KLUV_RES_LAST_ESC, KLUV_RES_YOU_DEAD, KLUV_RES_TIME_UP };

struct kluv_money {
    long total;         /* the stock 'Total score' (0x807520) */
    long round_now;     /* the same without the rounds before (slot 54) */
    long carried;       /* what this record carries */
    long rewards;       /* kill pay and fines; can be negative */
    long split;         /* record+0x28: his share if the round ended now (0 until he has escaped) */
    long payout;        /* record+0x2c: rewards + split */
    long banked;        /* [score+0x38]: the rounds before */
    long round_score;   /* [score+0x30]: 0 until the round is over */
    long best;          /* [score+0x34] */
    long pool; int sharers, leader;
};

struct kluv_loot {
    long left;          /* the sum of [obj+0x34] > 0 over the objects, each object once */
    int count;          /* money objects walked (each once) */
    int dups;           /* list entries that name an object an earlier entry names already (d: the slot-22 caveat) */
    long dupsum;        /* the sum of [obj+0x8c] over those entries = what they added to [rules+0xdd0] a second time (ASSUMED) */
};

/* -> 1 when the snap's score object reads as a ZHeistScore */
static int kluv_ok(const struct klb_snap *s)
{
    return s && s->rules && s->score && klh_rd32(s->score) == KLUV_SCORE_VT;
}

static int kluv_idx(const struct klb_snap *s, int i) { return i >= 0 && i < s->n && i < KLB_NREC && s->r[i].used; }

static int kluv_int(DWORD_PTR at, long *out)
{
    DWORD v = 0;
    if (!klh_rd(at, &v, 4)) return 0;
    *out = (long)(int)v;
    return 1;
}

/* (a) the lives the stock list shows as skulls: 0 .. 9; 0 also when the read fails */
static int kluv_lives(const struct klb_snap *s)
{
    signed char b = 0;
    if (!kluv_ok(s) || !klh_rd(s->score + KLUV_S_LIVES, &b, 1) || b < 0) return 0;
    return b > 9 ? 9 : b;
}

/* (a) TEST form (Lives=2): n skull glyphs as the stock list appends them, a space before each (0x7bb9c4); -> the
   number written. out needs 4 n + 1 bytes */
static int kluv_skulls(char *out, int cap, int n)
{
    int k = 0;
    if (cap <= 0) return 0;
    out[0] = 0;
    for (; k < n && 4 * (k + 1) < cap; k++) { out[4 * k] = ' '; memcpy(out + 4 * k + 1, KLUV_SKULL, 4); }
    return k;
}

/* (a) the own row's skull pictures. x of skull k (0 ..) from the row's LEFT edge: after the name's estimated width,
   never into the room kept for the cash */
static float kluv_skull_x(const char *name, float crew_w, int k)
{
    float w = KLUV_SKULL_LEAD, most = crew_w - KLUV_CASH_ROOM - KLUV_LIVES_MAX * (KLUV_SKULL_SIZE + KLUV_SKULL_GAP);
    const unsigned char *c;
    for (c = (const unsigned char *)name; c && *c; c++) if ((*c & 0xc0) != 0x80) w += KLUV_NAME_CHARW;       /* characters, not UTF-8 bytes */
    if (most < 0) most = 0;
    if (w > most) w = most;
    return w + (float)k * (KLUV_SKULL_SIZE + KLUV_SKULL_GAP);
}

/* y of the skulls from the row text's y: in the middle of the painted block (klhud.c klu_row) */
static float kluv_skull_y(float row_pitch) { return (row_pitch - KLUV_SKULL_SIZE) * 0.5f - KLUV_BLOCK_UP; }

/* the tint of skull k: held (k < lives) or lost; block = the row stands on its chalk block (Plates=1) */
static DWORD kluv_skull_argb(int k, int lives, int block)
{
    if (k < lives) return block ? KLUV_C_SKULL_ON : KLUV_C_SKULL_ON_BARE;
    return block ? KLUV_C_SKULL_LOST : KLUV_C_SKULL_LOST_BARE;
}

/* (b) every money number of crew index i. -> 0 (and *m all 0, leader -1) when the score object or the record cannot be read */
static int kluv_money(const struct klb_snap *s, int i, struct kluv_money *m)
{
    static const int add[9] = { 0x04, 0x08, 0x0c, 0x10, 0x18, 0x1c, 0x20, 0x24, 0x2c };      /* 0x807520 / 0x711010: not +0x14 (a count), not +0x28 */
    DWORD line[14]; long c0 = 0, v; int k; struct kluv_money t;
    memset(m, 0, sizeof *m); m->leader = -1;
    memset(&t, 0, sizeof t); t.leader = -1;
    if (!kluv_ok(s) || !kluv_idx(s, i) || !klh_rd(s->score + KLUV_S_LINES, line, sizeof line)) return 0;       /* +0x04 .. +0x38 */
    for (k = 0; k < 9; k++) t.round_now += (long)(int)line[(add[k] - KLUV_S_LINES) / 4];
    if (s->r[0].used) { if (!kluv_int(s->score + KLUV_S_CARRIED, &c0)) return 0; t.round_now += c0; }       /* slot 56 (0): -1 for a free record 0 in the game; taken as 0 here */
    t.round_score = (long)(int)line[(KLUV_S_ROUNDPTS - KLUV_S_LINES) / 4];
    t.best = (long)(int)line[(KLUV_S_BEST - KLUV_S_LINES) / 4];
    t.banked = (long)(int)line[(KLUV_S_BANKED - KLUV_S_LINES) / 4];
    t.total = t.round_now + t.banked;
    if (!kluv_int(s->score + KLUV_S_CARRIED + 4 * i, &t.carried) || !kluv_int(s->score + KLUV_S_REWARDS + 4 * i, &t.rewards)) return 0;
    if (!kluv_int(s->r[i].at + KLUV_REC_SPLIT, &t.split) || !kluv_int(s->r[i].at + KLUV_REC_PAYOUT, &t.payout)) return 0;
    if (kluv_int(s->rules + KLUV_R_POOL, &t.pool) && kluv_int(s->rules + KLUV_R_POOL + 4, &v)) t.sharers = (int)v;
    if (kluv_int(s->rules + KLUV_R_POOL + 8, &v) && v >= 0 && v < s->n) t.leader = (int)v;
    *m = t;
    return 1;
}

/* (b) the money box's three numbers as the game's own HUD / list defines them: Total = the stock 'Total score',
   Loot = what crew index i carries, Rewards = his rewards column */
static int kluv_money3(const struct klb_snap *s, int i, long *total, long *loot, long *rewards)
{
    struct kluv_money m;
    *total = *loot = *rewards = 0;
    if (!kluv_money(s, i, &m)) return 0;
    *total = m.total; *loot = m.carried; *rewards = m.rewards;
    return 1;
}

/* (c) n = the round being played (1 ..), m = the number of rounds the game holds (10 in Arcade); -> 0 on a failed read */
static int kluv_round(const struct klb_snap *s, int *n, int *m)
{
    signed char b[2] = { 0, 0 };
    *n = *m = 0;
    if (!kluv_ok(s) || !klh_rd(s->score + KLUV_S_NROUNDS, b, 2) || b[1] < 1) return 0;      /* +0x44 m, +0x45 n */
    *n = b[1]; *m = b[0] > 0 ? b[0] : 0;
    return 1;
}

/* (d) [rules+0xdd0] as it stands: what the rules added up, a twice-registered object twice. 0 = none / not readable */
static long kluv_loot_raw(const struct klb_snap *s)
{
    long v = 0;
    if (!kluv_ok(s) || !kluv_int(s->rules + KLUV_R_LOOT, &v) || v < 0) return 0;
    return v;
}

/* (d) one walk of the registered money objects: what is left in them, how many there are, and the entries that name
   an object a second time. -> 0 (and *o all 0) on any failed read. Two reads an object: not for every frame - the
   wired readers go through kluv_loot_cached */
static int kluv_loot_scan(const struct klb_snap *s, struct kluv_loot *o)
{
    static DWORD obj[KLUV_LOOT_MAX]; DWORD n = 0, p = 0, i, k; struct kluv_loot t;
    memset(o, 0, sizeof *o); memset(&t, 0, sizeof t);
    if (!kluv_ok(s) || !klh_rd(s->rules + KLUV_R_LOOTN, &n, 4) || !n || n > KLUV_LOOT_MAX || !(p = klh_rd32(s->rules + KLUV_R_LOOTP))) return 0;
    if (!klh_rd(p, obj, 4 * n)) return 0;
    for (i = 0; i < n; i++) {
        long v = 0;
        if (!obj[i] || klh_rd32(obj[i]) != KLUV_MONEY_VT) continue;                  /* an object that is not a money controller is left out, not a failure */
        for (k = 0; k < i && obj[k] != obj[i]; k++) ;
        if (k < i) { t.dups++; if (kluv_int(obj[i] + KLUV_M_START, &v) && v > 0) t.dupsum += v; continue; }
        if (!kluv_int(obj[i] + KLUV_M_AMOUNT, &v)) continue;
        if (v > 0) t.left += v;
        t.count++;
    }
    *o = t;
    return 1;
}

/* the walk at most once a second (and at once for another rules object); -> the last walk's result, 0s when it failed */
static const struct kluv_loot *kluv_loot_cached(const struct klb_snap *s)
{
    static struct kluv_loot c; static DWORD rules, at; DWORD now = GetTickCount();
    if (!s || s->rules != rules || now - at >= 1000) { rules = s ? s->rules : 0; at = now; kluv_loot_scan(s, &c); }
    return &c;
}

/* (d) what is still in the registered money objects; *count = how many objects were walked (each once) */
static long kluv_loot_left(const struct klb_snap *s, int *count)
{
    const struct kluv_loot *c = kluv_loot_cached(s);
    if (count) *count = c->count;
    return c->left;
}

/* (d) the level's loot: [rules+0xdd0], less what entries that stand in the list twice added a second time (none on
   every path read so far; the correction is an ASSUMPTION and does nothing while there are no such entries) */
static long kluv_loot_total(const struct klb_snap *s)
{
    long v = kluv_loot_raw(s), d;
    if (v <= 0) return 0;
    d = kluv_loot_cached(s)->dupsum;
    return d > 0 && d < v ? v - d : v;
}

/* (d) the loot bar (re\hud_layout.md: 'sum of the crew's money against the level's loot total'): what every record in
   use carries against the level's loot, 0 .. 1; 0 when the level's loot is not known */
static float kluv_loot_share(const struct klb_snap *s)
{
    long total = kluv_loot_total(s), held = 0; int i; float f;
    if (total <= 0) return 0.0f;
    for (i = 0; i < s->n && i < KLB_NREC; i++) if (s->r[i].used && (long)(int)s->r[i].money > 0) held += (long)(int)s->r[i].money;
    f = (float)held / (float)total;
    return f < 0 ? 0.0f : f > 1.0f ? 1.0f : f;
}

/* (e) the kind byte as it stands and the vehicle pointer, for the log: *raw = -1 when the byte cannot be read */
static void kluv_vehicle_raw(const struct klb_snap *s, int *raw, DWORD *vehicle)
{
    BYTE b = 0;
    *raw = -1; *vehicle = 0;
    if (!kluv_ok(s)) return;
    *vehicle = klh_rd32(s->rules + KLUV_R_VEHICLE);
    if (klh_rd(s->rules + KLUV_R_KIND, &b, 1)) *raw = b;
}

/* (e) KLUV_KIND_*: 1 a Havok car, 2 a helicopter, 3 an animated (key-framed) vehicle; 0 = the rules hold no vehicle
   yet (the byte is 0xff) or the read failed - kluv_vehicle_raw tells those apart */
static int kluv_vehicle_kind(const struct klb_snap *s)
{
    int raw; DWORD v;
    kluv_vehicle_raw(s, &raw, &v);
    return v && raw >= KLUV_KIND_CAR && raw <= KLUV_KIND_ANIM ? raw : 0;
}

/* (e) the picture of OUR escape dial: the helicopter (171) for a ZHeli, the car (170) for both kinds of car; 0 while
   the rules hold no vehicle */
static int kluv_vehicle_pic(const struct klb_snap *s)
{
    int k = kluv_vehicle_kind(s);
    return !k ? 0 : k == KLUV_KIND_HELI ? KLUV_PIC_CHOPPER : KLUV_PIC_CAR;
}

/* (e) what the STOCK clock takes (0x81e16e): 170 when the kind is 3, else 171 - a Havok car gets the helicopter there.
   For the log */
static int kluv_vehicle_pic_stock(const struct klb_snap *s)
{
    int k = kluv_vehicle_kind(s);
    return !k ? 0 : k == KLUV_KIND_ANIM ? KLUV_PIC_CAR : KLUV_PIC_CHOPPER;
}

static int kluv_secs(float f) { return f == f && f >= 0.0f && f < 36000.0f; }

/* (f) seconds; each 0 on a failed read / a value that is no time */
static float kluv_round_left(const struct klb_snap *s)
{
    float f = 0;
    return kluv_ok(s) && klh_rd(s->rules + KLUV_R_LEFT, &f, 4) && kluv_secs(f) ? f : 0.0f;
}

static float kluv_round_played(const struct klb_snap *s)
{
    float f = 0;
    return kluv_ok(s) && klh_rd(s->rules + KLUV_R_PLAYED, &f, 4) && kluv_secs(f) ? f : 0.0f;
}

static float kluv_round_len(const struct klb_snap *s)
{
    float f = 0;
    if (!kluv_ok(s)) return 0.0f;
    if (klh_rd(s->score + KLUV_S_LENGTH, &f, 4) && kluv_secs(f) && f >= 1.0f) return f;
    /* the constant 0x6d3130 answers in Arcade (klb_read has checked that this is an Arcade session) */
    if (klh_rd((DWORD_PTR)KLH_VA(KLUV_ARCADE_LEN), &f, 4) && kluv_secs(f) && f >= 1.0f) return f;
    return 0.0f;
}

/* (f) the watch's ring: the part of the round that is LEFT, 0 .. 1. By the round's length; when that is not known
   (or the clock stands above it: something set a longer time) by left / (left + played). 0 = not known */
static float kluv_round_frac(const struct klb_snap *s)
{
    float left = kluv_round_left(s), len = kluv_round_len(s), played;
    if (!(left > 0)) return 0.0f;
    if (len >= 1.0f && left <= len) return left / len;
    played = kluv_round_played(s);
    return left + played > 0 ? left / (left + played) : 0.0f;
}

/* (g) the flag dword of crew index i; 0 on a failed read */
static DWORD kluv_flags(const struct klb_snap *s, int i)
{
    DWORD f = 0;
    if (!kluv_ok(s) || !kluv_idx(s, i) || !klh_rd(s->score + KLUV_S_FLAGS + 4 * i, &f, 4)) return 0;
    return f;
}

/* (g) the STOCK list's decision from a flag dword, in its own order (0x572050, whole). For the log: our rows are
   decided by kluv_state */
static int kluv_stock_state(DWORD f)
{
    if (f & KLUV_F_WAITING) return KLUV_ST_WAITING;
    if (f & KLUV_F_DEAD) return KLUV_ST_DEAD;
    if (f & KLUV_F_TRAITOR) return KLUV_ST_TRAITOR;
    if (f & KLUV_F_DIRTYCOP) return KLUV_ST_DIRTYCOP;
    if (f & KLUV_F_POLICE) return KLUV_ST_POLICE;
    if (f & KLUV_F_UNDERCOP) return (f & 0x40000) ? KLUV_ST_UNDERCOP2 : KLUV_ST_UNDERCOP;
    if (f & 0x10) return KLUV_ST_WAITING;
    return KLUV_ST_CREW;
}

/* (g) OUR row state, KLUV_ST_* - THE decision klhud.c runs (through kluv_kind). From the score flags and, where the
   flags say nothing, klbot.c's status byte (1 waiting, 4 aboard, 6 escaped, 7 dead) and the bot's own traitor mark.
   The order, and where it leaves the stock list's:
     1 waiting to return as police, 2 dead                 (as stock; a waiting human reads 0x4004)
     3 escaped                                             (ours: the stock list has no look for it; before fed /
                                                            traitor, as klhud.c Version 2 had it - a traitor who got
                                                            out is 'OUT')
     4 dirty cop, police, undercover cop                   BEFORE traitor: the owner's 'as a fed youre only a fed'
                                                            (2026-10-11); the stock list tests traitor first
     5 traitor: score flag 1, or the bot's mark            (the stock list does not show the bot's mark)
     6 flag 0x10 -> waiting                                (the stock list's last test; what sets 0x10 was not read)
     7 aboard                                              (ours; no look in klhud.c yet)
   Status 5 has no meaning here (not established). */
static int kluv_state(const struct klb_snap *s, int i)
{
    DWORD f; const struct klb_rec *r;
    if (!kluv_ok(s) || !kluv_idx(s, i)) return KLUV_ST_CREW;
    f = kluv_flags(s, i); r = &s->r[i];
    if ((f & KLUV_F_WAITING) || r->status == 1) return KLUV_ST_WAITING;
    if ((f & KLUV_F_DEAD) || r->status == 7) return KLUV_ST_DEAD;
    if ((f & KLUV_F_ESCAPED) || r->status == 6) return KLUV_ST_ESCAPED;
    if (f & KLUV_F_DIRTYCOP) return KLUV_ST_DIRTYCOP;
    if (f & KLUV_F_POLICE) return KLUV_ST_POLICE;
    if (f & KLUV_F_UNDERCOP) return (f & 0x40000) ? KLUV_ST_UNDERCOP2 : KLUV_ST_UNDERCOP;
    if ((f & KLUV_F_TRAITOR) || (r->flags & 2)) return KLUV_ST_TRAITOR;
    if (f & 0x10) return KLUV_ST_WAITING;
    if ((f & KLUV_F_ABOARD) || r->status == 4) return KLUV_ST_ABOARD;
    return KLUV_ST_CREW;
}

/* (g) klhud.c klu_row's kind of crew index i: KLUV_K_* (0 crew, 1 you, 2 traitor, 3 dead, 4 escaped, 5 fed) */
static int kluv_kind(const struct klb_snap *s, int i)
{
    switch (kluv_state(s, i)) {
    case KLUV_ST_WAITING: case KLUV_ST_DEAD:                                  return KLUV_K_DEAD;
    case KLUV_ST_ESCAPED:                                                     return KLUV_K_ESCAPED;
    case KLUV_ST_DIRTYCOP: case KLUV_ST_POLICE: case KLUV_ST_UNDERCOP: case KLUV_ST_UNDERCOP2: return KLUV_K_FED;
    case KLUV_ST_TRAITOR:                                                     return KLUV_K_TRAITOR;
    default:                                                                  return kluv_idx(s, i) && !(s->r[i].flags & 1) ? KLUV_K_YOU : KLUV_K_CREW;
    }
}

/* (h) the crew index of who killed crew index i, or -1: nobody of the crew / not known */
static int kluv_killer(const struct klb_snap *s, int i)
{
    signed char b = -1;
    if (!kluv_ok(s) || !kluv_idx(s, i) || !klh_rd(s->score + KLUV_S_KILLER + i, &b, 1) || b < 0 || b >= s->n) return -1;
    return b;
}

/* (h) the round-over page's result line as 0x7df067 decides it, for crew index `me`; *life_lost = the page adds its
   'LifeLost' line; *game_over = its title is 'Game_Over'. KLUV_RES_NONE on a failed read */
static int kluv_result(const struct klb_snap *s, int me, int *life_lost, int *game_over)
{
    DWORD mine, f; int i, all_esc = 1, all_dead = 1, none_left = 1; signed char lives = 0;
    if (life_lost) *life_lost = 0;
    if (game_over) *game_over = 0;
    if (!kluv_ok(s) || !kluv_idx(s, me) || !klh_rd(s->score + KLUV_S_FLAGS + 4 * me, &mine, 4)) return KLUV_RES_NONE;
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        if (!s->r[i].used) continue;
        if (!klh_rd(s->score + KLUV_S_FLAGS + 4 * i, &f, 4)) return KLUV_RES_NONE;
        if (!(f & KLUV_F_ESCAPED)) all_esc = 0;
        if (!(f & (KLUV_F_DEAD | KLUV_F_POLICE))) all_dead = 0;
        if (!(f & (KLUV_F_ESCAPED | KLUV_F_POLICE))) none_left = 0;
    }
    if (life_lost) *life_lost = !(mine & KLUV_F_ESCAPED);
    if (game_over && klh_rd(s->score + KLUV_S_LIVES, &lives, 1)) *game_over = lives <= 0;
    if (all_esc) return KLUV_RES_ALL_ESC;
    if (mine & KLUV_F_ESCAPED) return KLUV_RES_YOU_ESC;
    if (all_dead) return KLUV_RES_ALL_DEAD;
    if (none_left) return KLUV_RES_LAST_ESC;
    if (mine & (KLUV_F_DEAD | KLUV_F_POLICE)) return KLUV_RES_YOU_DEAD;
    return KLUV_RES_TIME_UP;
}

/* the .LOC key of a result under AllLevels/Interface/Online/GameEnd/ (the game's), and an English line of OURS in the
   draft's capitals for a HUD that does not look the key up */
static const char *kluv_result_key(int res)
{
    static const char *k[7] = { "", "All_Esc", "You_Esc", "All_Dead", "Last_Esc", "You_Dead", "Time_Up" };
    return res >= 0 && res < 7 ? k[res] : "";
}

static const char *kluv_result_text(int res)
{
    static const char *t[7] = { "", "EVERYBODY GOT OUT", "YOU GOT OUT", "EVERYBODY IS DEAD", "THE LAST MAN GOT OUT", "YOU ARE DEAD", "TIME IS UP" };
    return res >= 0 && res < 7 ? t[res] : "";
}

/* Log=2: one line with every value. The values are LOOKED AT once a second at most (nothing is computed between two
   looks); the line is said when something other than the clock changed, and every 10 s anyway.
   `me` = the human's crew index (klb_snap.human, 0 in Arcade) */
static void kluv_dump(const struct klb_snap *s, int me)
{
    static char key[520]; static DWORD looked, said; static int none;
    char line[640], head[520], clock[120]; DWORD now = GetTickCount(), veh = 0, fl;
    struct kluv_money m; struct kluv_loot lt; int n = 0, mm = 0, lost = 0, over = 0, res, ok, raw = -1;
    if (looked && now - looked < 1000) return;
    looked = now ? now : 1;
    if (!kluv_ok(s)) {
        if (!none) { none = 1; key[0] = 0; said = now; klog("hud: values: no ZHeistScore at [rules+0x5f8] (rules %08lx, score %08lx): every reader answers 0", s ? s->rules : 0, s ? s->score : 0); }
        return;
    }
    none = 0;
    if (me < 0) me = 0;
    ok = kluv_money(s, me, &m); kluv_round(s, &n, &mm); kluv_loot_scan(s, &lt); res = kluv_result(s, me, &lost, &over);
    kluv_vehicle_raw(s, &raw, &veh); fl = kluv_flags(s, me);
    /* everything but the clock: the key that decides whether the line is said */
    snprintf(head, sizeof head,
             "lives %d of %d | round %d of %d | money%s total %ld = now %ld + banked %ld; carried %ld, rewards %ld, split %ld, payout %ld, pool %ld / %d, leader %d; round score %ld, best %ld"
             " | loot: level %ld (rules sum %ld, %d listed twice = %ld), left %ld in %d object(s), crew holds %.0f%%"
             " | vehicle %08lx kind byte %d -> kind %d, picture %d (stock clock %d)"
             " | you: flags %08lx state %d kind %d (stock list %d), killer %d | result now '%s'%s%s",
             kluv_lives(s), KLUV_LIVES_MAX, n, mm, ok ? "" : " (NOT READ)", m.total, m.round_now, m.banked, m.carried, m.rewards, m.split, m.payout, m.pool, m.sharers, m.leader, m.round_score, m.best,
             kluv_loot_total(s), kluv_loot_raw(s), lt.dups, lt.dupsum, lt.left, lt.count, 100.0f * kluv_loot_share(s),
             veh, raw, kluv_vehicle_kind(s), kluv_vehicle_pic(s), kluv_vehicle_pic_stock(s),
             fl, kluv_state(s, me), kluv_kind(s, me), kluv_stock_state(fl), kluv_killer(s, me),
             kluv_result_key(res), lost ? " + LifeLost" : "", over ? " (Game_Over)" : "");
    if (!strcmp(head, key) && now - said < 10000) return;
    snprintf(key, sizeof key, "%s", head); said = now;
    snprintf(clock, sizeof clock, "clock: left %.0f s, played %.0f s, length %.0f s, ring %.2f", kluv_round_left(s), kluv_round_played(s), kluv_round_len(s), kluv_round_frac(s));
    snprintf(line, sizeof line, "%s | %s", head, clock);
    klog("hud: values: %s", line);
}

#endif /* KLHUD_VALUES_C */
