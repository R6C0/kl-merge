/*
 * klfedkit.c - THE KIT OF THE PLAYER WHO CAME BACK AS A FED (klfed.c makes him one): he may hunt at once, the
 * crosshair tells friend from enemy the right way round, he wears what the map's own law wears, and sometimes he
 * carries an AK. Owner, 2026-10-11, after playing the fed on the park: 'if you die too early you cant kill itll
 * just say you cant kill before you heist like before the money is picked up they still on green crosshairs to
 * indicate friendly when in reality it should be red and the enemies are the inverse of that. make sure to use a
 * model thats correct for the map so i was normal swat but i should be the yakuza biker outfit and then on
 * withdrawal normal swat etc. and make it so u have a chance to come back with an ak 47 instead of only just
 * having the mp5'.
 * Part of KLHook (to be included by klhook.c after klfed.c, SHIP and TEST alike; the three lines are at the end of
 * this comment). Sections 1 and 2 are DATA WRITES ONLY: two bytes of the heap object ZGameRulesHeist. Sections 3
 * and 4 call game routines from the game's own thread (the same two klchar.c / klcrew.c call, and the game's own
 * loadout routine) and are OFF unless their key is set. No code byte and no import slot changes. Research and the
 * live checks: re\fed_kit.md. Every address below was disassembled for this file (debug\dasm.py, kl2.exe build
 * 0490, 2026-10-11). NOTHING HERE HAS RUN IN THE GAME.
 *
 * 0. WHERE IT ACTS
 *    Only with [Fed] Enable=1 and Player=1 (klfed.c's keys: without them there is no police human in Arcade), and
 *    only while ALL of this holds: an Arcade session ([session+0x5c] == 4, [session+0x54] not 2 / 3), the round runs
 *    ([session+0x70] == 0x19), the rules object is ZGameRulesHeist (vtable 0xbd3514), the level that runs is NOT the
 *    stock level of its slot (klsteam.c's klx_level_verdict == 2: klfed.c's own gate), crew record 0 is the local
 *    human with status 0 (in play), and the local player object is a ZFFPlayer (vtable 0xbb45f4) of type 3 with the
 *    police byte +0x2723 set. That state exists only between klfed.c's respawn and the end of that round. Nothing
 *    for a criminal, nothing on a stock level, nothing in a multiplayer session (other rules classes).
 *
 * 1. 'NO FRIENDLY FIRE UNTIL THE LOOTING HAS STARTED' (key Hunt, default 1)
 *    EXE: ZFFActor vtable slot 422 = 0x8689c0 takes a hit on an NPC before the damage routine (slot 423, 0x61a980)
 *    sees it: it ends by sending the hit to itself as a message (0x868dcd), and every early exit jumps past that.
 *    0x868a88: Arcade; 0x868a93: the victim's team [[actor+0x54]+4] is 2 (the crew) or 0 -> 0x868b11: when the
 *    rules are the Arcade ones (0x7bb2a0), the attacker [hit+0] is a ZFFPlayer (0x7aace0) and rules slot 189
 *    (vtable +0x2f4 = 0x4ee010: `mov al, [ecx+0x285] / ret`) answers 0, the HUD gets the text
 *    AllLevels/Interface/Online 'FA_NoFriendlyFire' ("No friendly fire until the looting has started", 0x868b7b)
 *    and the hit is DROPPED (0x868bdf / 0x868c07 -> 0x868dcf). The police byte of the attacker is not asked: the
 *    rule was written for the human criminal and catches the fed too.
 *    [rules+0x285] = 'the looting has started': set by 0x5cac90 at the first loot of anybody (0x5cacd2; then
 *    the announcement 'Looting_Started' unless the local client is police), cleared at the round reset (slot 7,
 *    0x74bd92; slot 4, 0x51be38). One more writer exists: slot 190 = 0x8f3930 (`mov [ecx+0x285], al / ret 4`), a
 *    plain setter with no direct caller (virtual; who calls it was not found). Its other readers: 0x5cac93
 *    (itself), ZBoardEscapeVehicleTactic slot 3
 *    (0x5478e0: an AI heister's boarding tactic sets actor+0x8f1 only then), and the PLAYER-as-victim routines
 *    0x612c20 / 0x78f5d0 / 0x6e3400, which skip the test for a police victim (0x612e95, 0x78f66c). (0x425651,
 *    0x6ffe3f and 0x700127 read it too, in slots 15 / 121 of the multiplayer classes: Heist has its own slot 15 =
 *    0x4c25b0 and slot 121 = `ret 0xc`, so they are out of Arcade's reach.)
 *    The owner's round (KLHook.log 12:43:59 .. 12:45:26): dead 15 s after the start, a fed at 12:44:04 with every
 *    bot at '$0', none of them had looted when he was killed 82 s later - the byte was 0 for his whole life as a fed.
 *    THE WRITE: while section 0 holds and [rules+0x285] is 0: one byte = 1. What is lost: the 'Looting started'
 *    line at the first loot (not shown to a police client anyway, 0x5cacfe), and an AI heister at heist stage 3 may
 *    take its boarding tactic before anybody has looted (it has stage 3 only after the loot place: no case found).
 *    The game clears the byte itself at the next round.
 *
 * 2. THE CROSSHAIR: FRIEND GREEN, ENEMY RED (key Crosshair, default 1)
 *    EXE: ZCrossHairDisplay slot 5 = 0x8e9720, Arcade branch 0x8e9dc6: target an NPC (0x4ea3b0), colour red
 *    [0xbbe498] = ffcc0000 unless a rule makes it green [0xbbe49c] = ff22ff22:
 *      0x8e9dfc  the display's player [display+0x10] is police (+0x2723) or a dirty cop (+0x2729)
 *      0x8e9e1a      and rules slot 186 (vtable +0x2e8 = 0x4c0630: `mov al, [ecx+0x283] / ret`) answers 0:
 *      0x8e9e2c          target team 1, 4 or 3 -> GREEN; team 2 (the crew) and 0 stay RED          = the cop's view
 *      0x8e9e4a  else (a criminal, OR slot 186 answers non-zero): team 2, 0 or 3 that is no traitor -> GREEN,
 *                the police stay RED                                                               = the crew's view
 *    So a police human sees the crew's view exactly when [rules+0x283] is not 0 - what the owner saw.
 *    [rules+0x283] / +0x284 belong to the Undercover Cop mode ('the cop is still under cover'; setter slot 187 =
 *    0x74d9f0, called by one network handler, 0x418b20). ZGameRulesFragileAlliance clears both in its slot 4
 *    (0x7086a8, 0x7086ae). ZGameRulesHeist has its OWN slot 4 (0x51bbe0), which clears +0x282 and +0x285 and NOT
 *    +0x283 / +0x284, and the constructors (0x835480 -> 0x7de590) write +0x281 only: in Arcade the byte is whatever
 *    the heap block (0xf30 bytes from 0x89e850) held. ASSUMPTION, the best reading of the code and of what the
 *    owner saw; not proven: no dump holds the object. The hook's first line of every fed says the byte it found.
 *    If it says 0 and the colours are still wrong, the cause is elsewhere (candidate: the display's player pointer
 *    +0x10, set by slot 1 = 0x83ab00, still names the dead heister object) and this section does nothing.
 *    THE WRITE: while section 0 holds and [rules+0x283] is not 0: one byte = 0 (what the Fragile Alliance classes
 *    have there outside the Undercover Cop mode). EVERY reader of the byte (all instructions with that
 *    displacement on a rules object, scanned 2026-10-11) and what 0 means to it:
 *      in reach of Arcade:  slot 186's callers (the crosshair above);  the kill line 0x4ae1b9 (only for a client
 *        with flag 0x80);  the 'all dead' announcement 0x8429d0 (0 = the ordinary text);  and 0x4569bf in 0x4569b0,
 *        called on the FIRST-LOOT path (0x7ceb48, right before 0x5cac90): with [rules+0x282] == 0 AND [rules+0x283]
 *        == 0 it sets [rules+0x282] = 1 and tells the session handler (slots 132 / 78, then 0x471d10 on
 *        [session+0x84], which sends only with a network session and [session+0x15d]). So after this write the
 *        next first loot of the round sets +0x282, which with a non-zero +0x283 it did not. That is the path every
 *        Arcade round takes whose heap byte happened to be 0; +0x282 is cleared by Heist's slot 4 (0x51be32) and
 *        read in Arcade only through the getter slot 184 (0x7b9ad0). No harm found; it IS a difference.
 *      NOT in reach of Arcade (other classes' slots; Heist has its own or a `ret`):  0x4254fa (slot 15 of the
 *        Fragile Alliance classes; Heist's slot 15 is 0x4c25b0),  0x6ffe71 / 0x6fffba (their slot 121; Heist's is
 *        `ret 0xc`),  0x5df2eb (the server class's slot 128; Heist's is `ret 0x10`),  0x68109e / 0x6811c7 and
 *        0x5e22ea (the server class's slot 192 = 0x680f90 and its only callee 0x5e2230; Heist's is 0x5dff40),
 *        0x4eb337 / 0x4eb492 (0x4eb260: called from the client class's slot 11 and from 0x794190, which only
 *        the server class's slot 11 calls).
 *    PUT BACK: the byte the hook found is written back when the next round's heister is in play on the same rules
 *    object (and the byte is still the hook's 0), so a round without a fed runs with what the game had there.
 *    NOT TOUCHED: what the police AI does. EXE (re\fed_respawn.md 2.4): ZSoldier slot 111 (0x8824e7) makes a police
 *    player a target only for a team-2 soldier, and the damage routine drops a police player's hits on an NPC
 *    that is not crew (0x61ab34 .. 0x61ab6b, while dword [0xce8a44] is 1 and he is no dirty cop). So with these two
 *    bytes: every AI heister in play is a red, killable enemy from the tick after the respawn; the police AI is
 *    green, cannot be hurt by him and does not shoot him. LOG, the one piece of evidence there is: in run
 *    FD3_DM03_die the fed lived the 145 s to the end of the run with a maximum health of 27.5 under police -> you
 *    x 20, in the bank where the same player as a criminal was dead 25 s after the round began (those logs have no
 *    line per hit on the player). The owner's fed was killed 82 s after his respawn: by the code, by the crew.
 *
 * 3. THE BODY OF THE MAP (key Body, default 0; needs [FedBody] in the level's KLJoin.ini, tools\kl_fa_fedbody.py)
 *    The eight police player objects of every build wear ONE model (F07's SWAT, 1919). A model is a number,
 *    [[player+4]+0x68], and the game changes it with 0x783fb0(entity, model) = 0x792290(node, model) ; vtable slot
 *    119 (0x417a60 for ZFFPlayer as for ZFFActor: the bone arrays from the model) ; renderer notify - read whole
 *    for klchar.c / klcrew.c, where it has RUN: klchar.c's slot 137 (0x8f5e90) ends in it for the heister object
 *    (Dead Men heroes on the player, seen live), klcrew.c calls it on the AI heisters (seen live). Slot 137 itself
 *    refuses a policeman (0x8f5eb0 `cmp byte [player+0x2723], 0 / jne`) - that test is about the hero table, the
 *    routine below it does not know what kind of person it dresses. Rules slot 34 (0x4b5b20, masks and looks)
 *    returns at once for type 3 (0x4b5b4f), so nothing of the game sets the look back.
 *    The hook, once per fed, Settle ms after it first saw him, on the game's thread:
 *        the section's Entries == [0xeac7a4] (the loaded .prm's chunk count), no loader is filling the table
 *        ([0xeac7a0] == 0), the chunk table 0xeac7b0 has Root, and the chunk is a model root with a skeleton
 *        (word +2 == 7, byte +0xc bit 0: 0x67cca3, kl_chars.skeleton); the three routines' first bytes and
 *        ZFFPlayer's slot 119 are the ones this build knows
 *        -> 0x783fb0(player, Root), read back; then 0x88c810(player, variant) with one of Variants= drawn by chance
 *    Root=0 in the section = this map keeps the stock body. The body stays on that police object for the level
 *    load (the game never uses the object again: re\fed_respawn.md 2.3a).
 *    ASSUMPTIONS: that a police player object draws and animates an NPC's model as the heister objects do Dead Men
 *    heroes'; the bikers have no face bones and no model of Dead Men has free_bone01 (the tool's notes).
 *
 * 4. AN AK SOMETIMES (key AkChance, percent, default 0)
 *    EXE - where the fed's guns come from (re\fed_respawn.md 'not established'): the respawn 0x4b28d0 calls
 *    0x4b6680(weapons = [0x168e96c], player, 0, -1) at 0x4b2a19; its jump table (0x4b66e0) sends kind 0 to
 *    0x4b66ca: 0x410710(weapons, player, 0, 0x1c, 0) - THE LOADOUT ROUTINE (callers besides: 0x42bd3c, 0x4d104d,
 *    0x74ac22, 0x892dc3): removes what the player holds (0x80dc00 / 0x417bc0 / 0x633250, four slots), then gives
 *    row [arg 2] and row [arg 3] of the SHOP TABLE 0xbd1f68 (36 rows of 24 bytes: item, ammunition, price, rank,
 *    tier, DLC; hashed .rdata, only read here) through 0x538ec0(weapons, player, item, ammunition), then sets his
 *    health from the armour row [arg 4] (0x644310). Row 0 = item 6 HG_M-77B, 150; row 0x1c = item 29
 *    Rifle_Zastavam85, 300: the pistol and the rifle of the pictures (the owner's builds show the MP5 look on the
 *    Zastava: 'the mp5'). Row 29 = item 31 Rifle_AK47, 250; row 30 = item 32 Rifle_AK74, 250.
 *    THE POOL. 0x538ec0 takes a weapon OBJECT out of a pool: [weapons+0] -> {+4 count, +0x10 entries of 12 bytes:
 *    object, item, byte +8 'not handed out since the last reset', byte +9 'lies dropped'}; 0x55bee0 wants item
 *    equal, no owner ([object+0x5c] == 0), +9 == 0, +8 != 0, and 0x538f30 then clears +8. None free: 0x53abc0 takes
 *    the one of that item that has LAIN DROPPED the longest from the list [weapons+0xb4] ({object, item, time};
 *    filled by 0x6853e0, which also sets +9: called when a player dies holding it, 0x7be32b / 0x7be35f, and when
 *    he throws an empty gun away, 0x47f950; an entry leaves the list and +9 is cleared at a pick-up, 0x829960),
 *    and when that finds none either the index is -1 and the game stops at the `int3` 0x538f02.
 *    Made by 0x78a8d0 (session handler slot 6, 0x766ed2 / 0x5230a2; Arcade only): for EVERY row of the shop table
 *    whose item has a template in the level ([[gamedata+0x15b0] + 4 * item], 0x5d2f50) it makes 8 objects, 16 of
 *    items 6 and 29 (the fed's pistol and Zastava), 12 of each when [0x168e59c] == 2 - no test of the row's DLC
 *    or rank, so the AK-47 (row 29: DLC 1, rank -1) and the AK-74 (row 30) get their 8 like any other. Emptied by
 *    0x5cae10 (slot 8). RESET by 0x42d9a0 (every entry +8 = 1, +9 = 0, the dropped list emptied): called from
 *    0x874a90 at 0x874b58, which the Arcade rules' slot 7 calls at 0x74bd6a - the same round-reset case that
 *    clears [rules+0x285] (0x74bd92).
 *    THE REMOVAL, 0x633250(player, weapon), read whole with its callees: (a) 0x47d880 -> 0x76fed0: a message to
 *    the other peers, sent only with a network session (0x9425a0); (b) 0x539e30: the weapon's inventory kind; 0 =
 *    only (f); (c) IF THE WEAPON IS IN HIS HANDS (0x727b40; the respawn's own call never takes this path: the fresh
 *    body holds nothing): 0x8af180(0, 0, 1) = 'stop what the gun is doing' - returns at once in player states
 *    0x2e / 0x2f, sub-states 0xb / 7, or without flag [player+0x2720] & 2; else it leaves state 0xd, drops the
 *    aim list +0x83c, sets [player+0x838] = 4, and for a gun with NO round left at all throws it away as a
 *    dropped one (0x47f950); then, in a running round, it queues the player's action 0x2f (slots +0x384 / +0x374 /
 *    +0x370) - after it slot +0x4cc / +0x4c8 (right / left hand), +0x4ec(0) / +0x4f0(0) (the hand lets go), and
 *    0x649250 (the 'current weapon' item numbers +0x920 / +0x924 / +0x27ac from what is left in the hands);
 *    (d) if it is the weapon on his back [player+0xbc8]: 0x75e8f0 (off the back); (e) [player+0xbb8 / +0xbbc]
 *    cleared when they name it; (f) 0x7ddc30(inventory [player+0xcec], weapon): the inventory's slot for that item
 *    emptied (0x5aa000) and 0x5ef4f0 on its list; (g) 0x6d26f0([weapon+4], 0) = 0x440290: node flag 0x200000
 *    cleared (its meaning NOT established), the weapon's own slot 151 (0x8a3510) with state 2 (ends its fire /
 *    reload / aim sub-states, then its slot +0x54), and 0x50d7c0: the player's weapon-class bits of +0x84 worked
 *    out again from his hands.
 *    WHERE THE REMOVED GUNS GO: NOWHERE THE POOL CAN USE. Nothing in the removal touches the pool entry: it keeps
 *    +8 = 0 (handed out) and +9 = 0 (not dropped) and is not in the dropped list, so neither 0x55bee0 nor 0x53abc0
 *    finds that object again until the round reset 0x42d9a0 makes every entry free. THE COST OF ONE AK LIFE is
 *    therefore: the respawn's pistol and Zastava (removed, out of use for the rest of the round) + one more pistol
 *    + one AK = 2 of the 16 pistols, 1 of the 16 Zastavas, 1 of the 8 AKs, where the game's own respawn costs 1
 *    pistol and 1 Zastava. A human is a fed once a round (his second death is final), so it does not add up
 *    across rounds.
 *    THE HOOK, once per fed whose dice said yes (AkChance percent), at the pass after the one that first saw him
 *    (about 50 ms after the respawn: before he can have fired, and before the body step): finds the row of the
 *    item (the level's AkItem=, else [Fed] AkItem, default 31) in the shop table, REFUSES an item that is row 0's
 *    pistol or row 0x1c's rifle (the loadout would give ONE item twice: with one free object the second give
 *    finds none and reaches the int3 - and the stock rifle again is no change anyway), REQUIRES a free pool object
 *    of that item AND TWO free ones of row 0's pistol (the one this call takes and one left for the game's next
 *    give: the removal frees nothing, see above), compares the first bytes of 0x410710 / 0x538ec0 / 0x55bee0 with
 *    this build's, and calls 0x410710(weapons, player, 0, row, 0) on the game's thread - the respawn's own call
 *    with another row. It says each item's four counts (free / dropped / owned / out of use) before and after.
 *    Side effect: his health is set again to what the game gave him at the respawn (klbalance.c writes its own on
 *    top, as at every respawn).
 *    ASSUMPTION (the one thing here the game's own respawn does not do): the removal's in-hands path (c) on a
 *    player who holds, and may be aiming, the guns he was given a frame or two ago. None of the game's own callers
 *    of 0x410710 was shown to run it with a gun in the hands. That is why the key is off by default.
 *    WHY item 32 on the owner's builds: their KLGuns.ini shows the M4A1 look on the AK-47; the tool writes
 *    AkItem=32 (the AK-74, which looks like an AK there). GUESS that the look is what he means by 'an ak 47'.
 *
 * KLHook.ini (all under klfed.c's section; nothing here acts unless Enable=1 and Player=1)
 *   [Fed]
 *   Kit=1             0 = this file does nothing
 *   Hunt=1            section 1: the fed may hurt the crew before anybody has looted
 *   Crosshair=1       section 2: the fed sees the crew red and the police green
 *   Body=0            section 3: 1 = the fed wears the body the level's KLJoin.ini [FedBody] names
 *   AkChance=0        section 4: percent of respawns with the AK instead of the stock rifle (the owner: 'a chance')
 *   AkItem=31         the rifle item when the level's [FedBody] has no AkItem= (31 AK-47, 32 AK-74; any shop rifle)
 *   KitSettle=300     ms after the hook first saw the fed before section 3 changes the body
 *   KitLog=1
 * KLJoin.ini beside the level archive (tools\kl_fa_fedbody.py)
 *   [FedBody]
 *   Entries=47114     Root=36028     Variants=1,3,4     Stock=1919     Name=...     AkItem=32     AkRecord=30
 *
 * LOG (prefix 'fedkit:')
 *   fedkit: on; Hunt=1 Crosshair=1 Body=1 AkChance=35 AkItem=31 Settle=300 ...
 *   fedkit: level f04\f04_main: [FedBody] Root=36028 Variants=1,3,4 AkItem=32 (for a .prm of 47114 chunks) ...
 *   fedkit: YOU ARE A FED (player 34871050): 'looting has started' [rules+0x285] = 0, 'under cover' [rules+0x283] = 1 ...
 *   fedkit: hunt: [rules+0x285] 0 -> 1: your hits on the crew count from now ...
 *   fedkit: crosshair: [rules+0x283] 1 -> 0: the crew is red, the police green
 *   fedkit: body: model 1919 -> 36028 through the game's own routine: the player now has 36028
 *   fedkit: look: variant 1 -> 3
 *   fedkit: ak: dice 12 of 100 under AkChance=35: item 32 = shop row 30 (250 rounds); pool before (free / dropped / owned / out of use): item 32 8/0/0/0, pistol 6 15/0/1/0, stock rifle 29 15/0/1/0 ...
 *   fedkit: ak: back from the loadout routine; pool after: item 32 7/0/1/0, pistol 6 14/0/1/1, stock rifle 29 15/0/0/1 - GIVEN
 *   fedkit: crosshair: [rules+0x283] put back to 1 (a heister is in play again on that rules object)
 *
 * THE LEAD'S THREE LINES IN klhook.c (compiled that way in a scratch copy, SHIP and TEST):
 *   #include "klfedkit.c"        after  #include "klfed.c"
 *   klfk_tick(game_thread);      in klh_tick, after  klp_tick(game_thread);
 *   klfk_init();                 in DllMain, after  klp_init();
 * It uses klchar.c's klc_same_code, kljoin.c's klj_map_key / klj_map_file / klj_map_ft / klj_cs and klsteam.c's
 * klx_on / klx_level_verdict (declared below as klfed.c declares them); nothing of klfed.c itself.
 */
#ifndef KLFEDKIT_C
#define KLFEDKIT_C

#define KLFK_SESSION    0x0168e598            /* +0x54, +0x5c = mode (4 = Arcade), +0x70 = state */
#define KLFK_SETTINGS   0x0168e9e4            /* +0x54 = the rules object */
#define KLFK_RULES_VT   0x00bd3514            /* ZGameRulesHeist */
#define KLFK_PLAYER_VT  0x00bb45f4            /* ZFFPlayer */
#define KLFK_ROUND      0x19
#define KLFK_LOOTING    0x285                 /* rules: 'the looting has started' (slot 189) */
#define KLFK_COVER      0x283                 /* rules: the Undercover Cop mode's 'still under cover' (slot 186) */
#define KLFK_GET189     0x004ee010
#define KLFK_GET186     0x004c0630
#define KLFK_SETMODEL   0x00783fb0            /* (entity, model) */
#define KLFK_NODEMODEL  0x00792290
#define KLFK_SETVARIANT 0x0088c810            /* (entity, variant) */
#define KLFK_REBUILD    0x00417a60            /* slot 119 of ZFFPlayer */
#define KLFK_TABLE      0x00eac7b0            /* chunk index -> pointer, 0x12000 slots (klgun.c 3) */
#define KLFK_SLOTS      0x12000
#define KLFK_COUNT      0x00eac7a4
#define KLFK_LOADING    0x00eac7a0
#define KLFK_WEAPONS    0x0168e96c            /* the weapon pool object */
#define KLFK_SHOP       0x00bd1f68            /* 36 rows of 24 bytes: item, ammunition, price, rank, tier, DLC */
#define KLFK_ROWS       36
#define KLFK_STOCKROW   0x1c                  /* the respawn's rifle row (0x4b66ca): item 29, the Zastava */
#define KLFK_LOADOUT    0x00410710            /* (weapons; player, char pistol row, int rifle row, int armour row) ret 0x10 */
#define KLFK_GIVE       0x00538ec0
#define KLFK_POOLFIND   0x0055bee0
#define KLFK_NVAR       8

static int klx_on;                                                    /* klsteam.c, included after this file */
static int klx_level_verdict(const char *scene, char *why);           /* 0 no level, 1 stock, 2 not stock, 3 not known; why[200] */

static struct { int on, log, hunt, cross, body, ak, akitem, settle; } klfk;
static struct {                               /* the level's [FedBody] */
    char key[64], file[MAX_PATH]; FILETIME ft;
    int on, nvar, var[KLFK_NVAR], akitem, akrecord; DWORD entries, root, stock; char name[80];
} klfk_lv;
static struct {                               /* the fed of this round */
    DWORD player, rules, since; int dice, variant, told, hunt_n, cross_n, body, body_tries, look_calls, ak, told_gate, told_thread;
} klfk_r;
static struct { DWORD rules; BYTE was; int have; } klfk_cov;       /* [rules+0x283] as the hook found it, to put back */

static DWORD klfk_rand(void)
{
    static DWORD s; LARGE_INTEGER q;
    if (!s) { QueryPerformanceCounter(&q); s = q.LowPart ^ GetTickCount() ^ 0x9e3779b9u; if (!s) s = 1; }
    s ^= s << 13; s ^= s >> 17; s ^= s << 5;
    return s;
}

/* the [FedBody] section of the KLJoin.ini kljoin.c has read for the running level (never a stock archive's) */
static void klfk_source(void)
{
    char key[64], file[MAX_PATH], t[96], *p; FILETIME ft; int v;
    EnterCriticalSection(&klj_cs);
    snprintf(key, sizeof key, "%s", klj_map_key); snprintf(file, sizeof file, "%s", klj_map_file); ft = klj_map_ft;
    LeaveCriticalSection(&klj_cs);
    if (!strcmp(key, klfk_lv.key) && !_stricmp(file, klfk_lv.file) && !CompareFileTime(&ft, &klfk_lv.ft)) return;
    memset(&klfk_lv, 0, sizeof klfk_lv);
    strcpy(klfk_lv.key, key); strcpy(klfk_lv.file, file); klfk_lv.ft = ft;
    if (!key[0] || !file[0]) return;
    if (!GetPrivateProfileStringA("FedBody", 0, "", t, sizeof t, file)) return;                 /* no such section */
    klfk_lv.entries = GetPrivateProfileIntA("FedBody", "Entries", 0, file);
    klfk_lv.root = GetPrivateProfileIntA("FedBody", "Root", 0, file);
    klfk_lv.stock = GetPrivateProfileIntA("FedBody", "Stock", 0, file);
    klfk_lv.akitem = (int)GetPrivateProfileIntA("FedBody", "AkItem", 0, file);
    klfk_lv.akrecord = (int)GetPrivateProfileIntA("FedBody", "AkRecord", -1, file);
    GetPrivateProfileStringA("FedBody", "Name", "", klfk_lv.name, sizeof klfk_lv.name, file);
    GetPrivateProfileStringA("FedBody", "Variants", "", t, sizeof t, file);
    for (p = t; *p && klfk_lv.nvar < KLFK_NVAR; ) {
        while (*p == ' ' || *p == ',' || *p == ';') p++;
        if (!*p) break;
        v = atoi(p);
        if (v >= 1 && v <= 255) klfk_lv.var[klfk_lv.nvar++] = v;
        while (*p && *p != ',' && *p != ';' && *p != ' ') p++;
    }
    /* Root is tested against Entries, not against the table's size: a slot at or above the loaded .prm's count may
       still hold what a former, larger level left there */
    if (!klfk_lv.entries || klfk_lv.entries > KLFK_SLOTS || klfk_lv.root >= klfk_lv.entries || (klfk_lv.root && !klfk_lv.nvar) || klfk_lv.akitem < 0 || klfk_lv.akitem > 63) {
        klog("fedkit: [FedBody] of %s refused (Entries=%lu Root=%lu, %d variant(s), AkItem=%d): it needs Entries= (1..%d), Root= below Entries, Variants= with Root=, AkItem= 0..63", file,
             klfk_lv.entries, klfk_lv.root, klfk_lv.nvar, klfk_lv.akitem, KLFK_SLOTS);
        return;
    }
    klfk_lv.on = 1;
    if (klfk.log) klog("fedkit: level %s: [FedBody] Root=%lu (%d look(s), first %d) AkItem=%d '%s' (%s, for a .prm of %lu chunks)%s", key, klfk_lv.root, klfk_lv.nvar, klfk_lv.nvar ? klfk_lv.var[0] : 0,
                       klfk_lv.akitem, klfk_lv.name, file, klfk_lv.entries, klfk_lv.root ? "" : ": this map keeps the stock police body");
}

/* -> 1 when the section is the running level's and its .prm is the loaded one; why (literal) otherwise */
static int klfk_level_ok(const char **why)
{
    char scene[160], key[64]; DWORD loading = 1, count = 0;
    klfk_source();
    if (!klfk_lv.on) { *why = "the level's KLJoin.ini has no usable [FedBody] section"; return 0; }
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key) || _stricmp(key, klfk_lv.key)) { *why = "the [FedBody] section that was read belongs to another level"; return 0; }
    if (!klh_rd((DWORD_PTR)KLH_VA(KLFK_LOADING), &loading, 4) || loading) { *why = "a loader is filling the chunk table"; return 0; }
    if (!klh_rd((DWORD_PTR)KLH_VA(KLFK_COUNT), &count, 4) || count != klfk_lv.entries) { *why = "Entries= is not the loaded .prm's chunk count: the section was written for another build"; return 0; }
    return 1;
}

/* ---------------------------------------------------------------- section 3: the body */

static void klfk_body_tick(DWORD player, int game_thread)
{
    static const BYTE model_code[14] = { 0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b, 0xf1, 0x57, 0x8b, 0x7e, 0x04, 0x50, 0x8b, 0xcf };      /* 0x783fb0 */
    static const BYTE node_code[12] = { 0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b, 0xf1, 0x57, 0x8b, 0x7e, 0x68, 0x89 };                  /* 0x792290 */
    static const BYTE variant_code[10] = { 0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b, 0xf1, 0x89, 0x46, 0x50 };                           /* 0x88c810 */
    const char *why = 0; DWORD node, model = 0, cur = 0, ptr, v = 0; BYTE hdr[16];
    if (klfk_r.body) return;                                  /* 1 done, 2 given up (said) */
    if (!klfk_level_ok(&why)) { klfk_r.body = 2; klog("fedkit: body: %s: the stock police body stays", why); return; }
    if (!klfk_lv.root) { klfk_r.body = 1; if (klfk.log) klog("fedkit: body: this map keeps the stock police body ([FedBody] Root=0)"); return; }
    if (!(node = klh_rd32(player + 4)) || !klh_rd(node + 0x68, &model, 4) || !model) { klfk_r.body = 2; klog("fedkit: body: the player's node / model cannot be read: nothing changed"); return; }
    if (!(ptr = klh_rd32((DWORD_PTR)KLH_VA(KLFK_TABLE) + 4 * klfk_lv.root)) || !klh_rd(ptr, hdr, sizeof hdr) || hdr[2] != 7 || hdr[3] != 0 || !(hdr[0x0c] & 1)) {
        klfk_r.body = 2; klog("fedkit: body: chunk %lu of the loaded .prm is not a model root with a skeleton: nothing changed", klfk_lv.root); return;
    }
    if (!klc_same_code(KLFK_SETMODEL, model_code, sizeof model_code) || !klc_same_code(KLFK_NODEMODEL, node_code, sizeof node_code) ||
        !klc_same_code(KLFK_SETVARIANT, variant_code, sizeof variant_code) || klh_rd32((DWORD_PTR)KLH_VA(KLFK_PLAYER_VT + 4 * 119)) != KLFK_REBUILD) {
        klfk_r.body = 2; klog("fedkit: body: the game routines are not the ones this build knows: nothing changed"); return;
    }
    if (!game_thread) { if (!klfk_r.told_thread++) klog("fedkit: the tick is not on the game's thread ([KLHook] Tick=0?): body and rifle cannot be changed"); return; }
    if (model != klfk_lv.root) {
        if (klfk_r.body_tries >= 2) { klfk_r.body = 2; return; }
        klfk_r.body_tries++;
        ((void (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)KLH_VA(KLFK_SETMODEL))((void *)(DWORD_PTR)player, 0, klfk_lv.root);
        klh_rd(node + 0x68, &cur, 4);
        klog("fedkit: body: model %lu -> %lu (%s) through the game's own routine (try %d): the player now has %lu%s", model, klfk_lv.root, klfk_lv.name, klfk_r.body_tries, cur, cur == klfk_lv.root ? "" : " - NOT taken");
        return;                                               /* the look at the next pass */
    }
    if (!klh_rd(player + 0x50, &v, 4)) { klfk_r.body = 2; return; }
    if (v != (DWORD)klfk_r.variant) {
        if (klfk_r.look_calls >= 4) { klfk_r.body = 2; klog("fedkit: look: the variant is %lu after four calls for %d: left alone", v, klfk_r.variant); return; }
        klfk_r.look_calls++;
        ((void (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(KLFK_SETVARIANT))((void *)(DWORD_PTR)player, 0, klfk_r.variant);
        if (klfk.log) klog("fedkit: look: variant %lu -> %d on model %lu", v, klfk_r.variant, klfk_lv.root);
        return;
    }
    klfk_r.body = 1;
    if (klfk.log) klog("fedkit: body: the fed wears model %lu, variant %d (%s)", klfk_lv.root, klfk_r.variant, klfk_lv.name);
}

/* ---------------------------------------------------------------- section 4: the rifle */

/* The pool's objects of an item in four heaps: c[0] FREE as 0x55bee0 would find them (byte +8 set, byte +9 clear, no
   owner; stricter than the game: an owner field that is not 0 counts as owned whatever it resolves to), c[1] lying
   DROPPED (byte +9: 0x53abc0 may take them again), c[2] OWNED (handed out, [object+0x5c] not 0), c[3] OUT OF USE
   (handed out, no owner, not dropped: nothing gives them again before the round reset 0x42d9a0).
   -> the free number, or -1 when the pool cannot be read */
static int klfk_pool(DWORD item, int c[4])
{
    DWORD w, a, n = 0, ents, i, e[3], owner;
    c[0] = c[1] = c[2] = c[3] = 0;
    if (!(w = klh_rd32((DWORD_PTR)KLH_VA(KLFK_WEAPONS))) || !(a = klh_rd32(w)) || !klh_rd(a + 4, &n, 4) || !n || n > 4096 || !(ents = klh_rd32(a + 0x10))) return -1;
    for (i = 0; i < n; i++) {
        if (!klh_rd(ents + 12 * i, e, 12)) return -1;
        if (e[1] != item || !e[0]) continue;
        owner = 1;
        if (!klh_rd(e[0] + 0x5c, &owner, 4)) owner = 1;
        if (e[2] & 0xff00) c[1]++;                            /* byte +9 */
        else if (owner) c[2]++;
        else if (e[2] & 0xff) c[0]++;                         /* byte +8 */
        else c[3]++;
    }
    return c[0];
}

static void klfk_ak_tick(DWORD player, int game_thread)
{
    static const BYTE loadout_code[10] = { 0x55, 0x8b, 0xe9, 0x8b, 0x0d, 0x98, 0xe5, 0x68, 0x01, 0xe8 };                /* 0x410710 push ebp ; mov ebp,ecx ; mov ecx,[0x168e598] ; call */
    static const BYTE give_code[11] = { 0x56, 0x8b, 0x74, 0x24, 0x0c, 0x57, 0x8b, 0xf9, 0x83, 0xfe, 0x40 };             /* 0x538ec0 .. cmp esi, 0x40 */
    static const BYTE find_code[11] = { 0x51, 0x8b, 0x01, 0x53, 0x55, 0x56, 0x57, 0x89, 0x4c, 0x24, 0x10 };             /* 0x55bee0 push ecx ; mov eax,[ecx] .. */
    DWORD w, row[2], pistol[2], stock[2], shop = (DWORD)(DWORD_PTR)KLH_VA(KLFK_SHOP); int item, r, i, free_rifle, free_pistol, after, b[3][4], a[3][4]; const char *why = 0;
    if (klfk_r.ak) return;                                    /* 1 done / not drawn, 2 given up */
    if (klfk_r.dice >= klfk.ak) { klfk_r.ak = 1; if (klfk.log) klog("fedkit: ak: dice %d of 100, not under AkChance=%d: the stock rifle stays", klfk_r.dice, klfk.ak); return; }
    item = klfk.akitem;
    if (klfk_level_ok(&why) && klfk_lv.akitem) item = klfk_lv.akitem;
    for (r = -1, i = 0; i < KLFK_ROWS; i++) if (klh_rd(shop + 24 * i, row, 8) && row[0] == (DWORD)item) { r = i; break; }
    if (r < 0 || !row[1] || row[1] > 1000 || !klh_rd(shop, pistol, 8) || !pistol[0] || pistol[0] > 63 || !klh_rd(shop + 24 * KLFK_STOCKROW, stock, 8) || !stock[0] || stock[0] > 63) {
        klfk_r.ak = 2; klog("fedkit: ak: item %d is in no row of the shop table at %08x: the stock rifle stays", item, KLFK_SHOP); return;
    }
    /* the loadout gives row 0 and then this row: the SAME item twice wants two free objects of it, and with one the
       second give ends in the game's int3 (0x538f02). The pistol's item is refused for that; the stock rifle's item
       would be no change. */
    if ((DWORD)item == pistol[0] || (DWORD)item == stock[0]) {
        klfk_r.ak = 2;
        klog("fedkit: ak: item %d is the fed's own %s (shop row %d): AkItem must be another rifle (31 AK-47, 32 AK-74): the stock rifle stays", item, (DWORD)item == pistol[0] ? "pistol" : "stock rifle", (DWORD)item == pistol[0] ? 0 : KLFK_STOCKROW);
        return;
    }
    if (klfk_lv.on && klfk_lv.akitem == item && klfk_lv.akrecord >= 0 && klfk_lv.akrecord != r) { klfk_r.ak = 2; klog("fedkit: ak: the level's AkRecord=%d, the exe has item %d in row %d: the stock rifle stays", klfk_lv.akrecord, item, r); return; }
    if (!klc_same_code(KLFK_LOADOUT, loadout_code, sizeof loadout_code) || !klc_same_code(KLFK_GIVE, give_code, sizeof give_code) || !klc_same_code(KLFK_POOLFIND, find_code, sizeof find_code)) {
        klfk_r.ak = 2; klog("fedkit: ak: the game's loadout routines are not the ones this build knows: the stock rifle stays"); return;
    }
    free_rifle = klfk_pool((DWORD)item, b[0]); free_pistol = klfk_pool(pistol[0], b[1]); klfk_pool(stock[0], b[2]);
    if (free_rifle < 1 || free_pistol < 2) {
        klfk_r.ak = 2;
        klog("fedkit: ak: dice %d under %d, but the weapon pool has %d free of item %d (1 needed) and %d free of the pistol, item %lu (2 needed: the one this call takes and one for the game's next give; the game stops at an int3 without): the stock rifle stays%s",
             klfk_r.dice, klfk.ak, free_rifle, item, free_pistol, pistol[0], free_rifle == 0 && !b[0][1] && !b[0][2] && !b[0][3] ? " - this level has no object of that item at all (no template for it in the level)" : "");
        return;
    }
    if (!game_thread) { if (!klfk_r.told_thread++) klog("fedkit: the tick is not on the game's thread ([KLHook] Tick=0?): body and rifle cannot be changed"); return; }
    w = klh_rd32((DWORD_PTR)KLH_VA(KLFK_WEAPONS));
    klfk_r.ak = 1;
    klog("fedkit: ak: dice %d of 100 under AkChance=%d: item %d = shop row %d (%lu rounds); pool before (free / dropped / owned / out of use): item %d %d/%d/%d/%d, pistol %lu %d/%d/%d/%d, stock rifle %lu %d/%d/%d/%d: the game's loadout routine is called with that row",
         klfk_r.dice, klfk.ak, item, r, row[1], item, b[0][0], b[0][1], b[0][2], b[0][3], pistol[0], b[1][0], b[1][1], b[1][2], b[1][3], stock[0], b[2][0], b[2][1], b[2][2], b[2][3]);
    ((void (__fastcall *)(void *, void *, DWORD, int, int, int))(DWORD_PTR)KLH_VA(KLFK_LOADOUT))((void *)(DWORD_PTR)w, 0, player, 0, r, 0);
    after = klfk_pool((DWORD)item, a[0]); klfk_pool(pistol[0], a[1]); klfk_pool(stock[0], a[2]);
    /* by the code the removed pistol and stock rifle end 'out of use' (the removal does not touch the pool: this
       file's section 4); 'owned' still counting them = [object+0x5c] is not cleared by the removal - the same thing
       for the pool, they are not given again before the round reset */
    klog("fedkit: ak: back from the loadout routine; pool after: item %d %d/%d/%d/%d, pistol %lu %d/%d/%d/%d, stock rifle %lu %d/%d/%d/%d - %s", item, a[0][0], a[0][1], a[0][2], a[0][3],
         pistol[0], a[1][0], a[1][1], a[1][2], a[1][3], stock[0], a[2][0], a[2][1], a[2][2], a[2][3],
         after == free_rifle - 1 ? (a[1][0] == b[1][0] - 1 ? "GIVEN (one more pistol and the rifle; the two he held are out of the pool until the next round)" : "GIVEN, but the pistol's free count did not go down by one: read the counts")
                                 : "NOT given by that count (the session test 0x8df480 may have said no)");
}

/* ---------------------------------------------------------------- the tick */

static void klfk_tick(int game_thread)
{
    static const BYTE get189[7] = { 0x8a, 0x81, 0x85, 0x02, 0x00, 0x00, 0xc3 };          /* mov al, [ecx+0x285] ; ret */
    static const BYTE get186[7] = { 0x8a, 0x81, 0x83, 0x02, 0x00, 0x00, 0xc3 };          /* mov al, [ecx+0x283] ; ret */
    static DWORD last; static int told_code;
    DWORD now = GetTickCount(), sm, gs, rules, gd, player, recs, freeb, client, sub = 0, state = 0, n = 0; BYTE sel = 0xff, type = 0, pol = 0, b = 1, raw[0x7c], cl[2], loot = 0, cover = 0, v;
    char scene[160], why[200];
    if (!klfk.on || !klh_exe_ok) return;
    if (now - last < 50) return;
    last = now;
    /* ---- section 0: a police human in a running Arcade round of a level that is not stock */
    /* What is remembered of a fed (klfk_r) is dropped when the session or its rules object is gone, or when the local
       player is somebody who is no policeman (the next round's heister). It is KEPT through anything else - a pause,
       a state between two frames - so that one life gets one body and one throw of the dice. */
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLFK_SESSION))) || klh_rd32(sm + 0x5c) != 4 || !klh_rd(sm + 0x54, &sub, 4) || sub == 2 || sub == 3 ||
        !(gs = klh_rd32((DWORD_PTR)KLH_VA(KLFK_SETTINGS))) || !(rules = klh_rd32(gs + 0x54)) || klh_rd32(rules) != KLFK_RULES_VT) { klfk_r.player = 0; klfk_cov.have = 0; return; }
    if (klfk_cov.have && klfk_cov.rules != rules) klfk_cov.have = 0;      /* that rules object is gone: nothing to put back */
    if (!klh_rd(sm + 0x70, &state, 4) || state != KLFK_ROUND) return;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel >= 28 || !(player = klh_rd32(gd + 0x828 + 4 * sel)) || klh_rd32(player) != KLFK_PLAYER_VT ||
        !klh_rd(player + 0x273c, &type, 1) || !klh_rd(player + 0x2723, &pol, 1)) return;
    if (type != 3 || !pol) {
        /* a heister is in play: the next round. The 'under cover' byte goes back to what the game had there, when it
           is still the hook's 0 (the same object, the vtable just checked) - a round without a fed is the game's own. */
        if (klfk_cov.have && klh_rd(rules + KLFK_COVER, &cover, 1)) {
            if (!cover && klfk_cov.was && klh_data((void *)(DWORD_PTR)(rules + KLFK_COVER), &klfk_cov.was, 1, "Arcade rules: the 'under cover' byte put back")) {
                if (klfk.log) klog("fedkit: crosshair: [rules+0x283] put back to %u (a heister is in play again on that rules object)", klfk_cov.was);
            }
            klfk_cov.have = 0;
        }
        klfk_r.player = 0; return;
    }
    if (!klh_rd(rules + 0x354, &n, 4) || !n || n > 32 || !(recs = klh_rd32(rules + 0x348)) || !(freeb = klh_rd32(rules + 0x34c)) || !klh_rd(freeb, &b, 1) || b ||
        !klh_rd(recs, raw, sizeof raw) || (raw[0x79] & 1) || raw[0x10] != 0 || !(client = *(DWORD *)raw) || !klh_rd(client, cl, 2) || cl[0] != 0 || cl[1] != 0) return;
    if (!klx_on || !klh_scene(scene, sizeof scene) || klx_level_verdict(scene, why) != 2) {
        if (!klfk_r.told_gate++ && klfk.log) klog("fedkit: a police human on a level that is stock or not judged: nothing is done");
        return;
    }
    if (!klh_rd(rules + KLFK_LOOTING, &loot, 1) || !klh_rd(rules + KLFK_COVER, &cover, 1)) return;
    if (player != klfk_r.player || rules != klfk_r.rules) {   /* a new fed */
        const char *lw = 0; int have;
        memset(&klfk_r, 0, sizeof klfk_r);
        klfk_r.player = player; klfk_r.rules = rules; klfk_r.since = now ? now : 1;
        klfk_r.dice = (int)(klfk_rand() % 100);
        have = klfk_level_ok(&lw);
        klfk_r.variant = have && klfk_lv.nvar ? klfk_lv.var[klfk_rand() % (DWORD)klfk_lv.nvar] : 1;
        if (klfk.log) klog("fedkit: YOU ARE A FED (player %08lx, rules %08lx): 'the looting has started' [rules+0x285] = %u, the Undercover Cop mode's 'under cover' [rules+0x283] = %u (not 0 = the crosshair shows a police human the crew's colours; 0 = Crosshair has nothing to write, and colours that are still wrong have another cause); %s%s",
                           player, rules, loot, cover, have ? "this level has a [FedBody] section" : "no [FedBody]: ", have ? "" : lw);
    }
    /* ---- sections 1 and 2: two bytes of the rules object, held while he is a fed in play (any thread: single bytes the game only reads here) */
    if (!told_code && (klh_rd32((DWORD_PTR)KLH_VA(KLFK_RULES_VT + 4 * 189)) != KLFK_GET189 || klh_rd32((DWORD_PTR)KLH_VA(KLFK_RULES_VT + 4 * 186)) != KLFK_GET186 ||
                       !klc_same_code(KLFK_GET189, get189, sizeof get189) || !klc_same_code(KLFK_GET186, get186, sizeof get186))) {
        told_code = 2; klog("fedkit: slots 189 / 186 of the Arcade rules are not the two getters this build knows: Hunt and Crosshair write nothing");
    } else if (!told_code) told_code = 1;
    if (told_code == 1) {
        if (klfk.hunt && !loot) {
            v = 1;
            if (klh_data((void *)(DWORD_PTR)(rules + KLFK_LOOTING), &v, 1, "Arcade rules: 'the looting has started'")) {
                if (!klfk_r.hunt_n++ || klfk.log > 1) klog("fedkit: hunt: [rules+0x285] 0 -> 1 ('the looting has started'): your hits on the crew count from now; the game clears it at the next round");
            } else if (!klfk_r.hunt_n++) klog("fedkit: hunt: [rules+0x285] could NOT be written");
        }
        if (klfk.cross && cover) {
            v = 0;
            if (!klfk_cov.have) { klfk_cov.rules = rules; klfk_cov.was = cover; klfk_cov.have = 1; }
            if (klh_data((void *)(DWORD_PTR)(rules + KLFK_COVER), &v, 1, "Arcade rules: the Undercover Cop mode's 'under cover' byte")) {
                if (!klfk_r.cross_n++ || klfk.log > 1) klog("fedkit: crosshair: [rules+0x283] %u -> 0: a police human now gets the cop's colours - the crew red, the police green", cover);
                else if (klfk_r.cross_n == 8) klog("fedkit: crosshair: [rules+0x283] has come back eight times: something of the game writes it (not found in the exe)");
            } else if (!klfk_r.cross_n++) klog("fedkit: crosshair: [rules+0x283] could NOT be written");
        }
    }
    /* ---- sections 4 and 3: game calls, once per fed, one step a pass. The rifle FIRST, at the pass that follows the
       one that saw him (the respawn gave him his guns a frame or two ago and he has done nothing with them yet); the
       body once the respawn has settled. */
    if (klfk.ak > 0 && !klfk_r.ak) { if (now != klfk_r.since) klfk_ak_tick(player, game_thread); return; }
    if ((LONG)(now - klfk_r.since) < klfk.settle) return;
    if (klfk.body && !klfk_r.body) klfk_body_tick(player, game_thread);
}

static void klfk_init(void)
{
    int v;
    if (!GetPrivateProfileIntA("Fed", "Enable", 0, klh_ini) || !GetPrivateProfileIntA("Fed", "Player", 0, klh_ini) || !GetPrivateProfileIntA("Fed", "Kit", 1, klh_ini)) return;
    klfk.on = 1;
    v = (int)GetPrivateProfileIntA("Fed", "KitLog", 1, klh_ini); klfk.log = v < 0 ? 0 : v > 2 ? 2 : v;
    klfk.hunt = GetPrivateProfileIntA("Fed", "Hunt", 1, klh_ini) != 0;
    klfk.cross = GetPrivateProfileIntA("Fed", "Crosshair", 1, klh_ini) != 0;
    klfk.body = GetPrivateProfileIntA("Fed", "Body", 0, klh_ini) != 0;
    v = (int)GetPrivateProfileIntA("Fed", "AkChance", 0, klh_ini); klfk.ak = v < 0 ? 0 : v > 100 ? 100 : v;
    v = (int)GetPrivateProfileIntA("Fed", "AkItem", 31, klh_ini); klfk.akitem = v < 1 || v > 63 ? 31 : v;
    v = (int)GetPrivateProfileIntA("Fed", "KitSettle", 300, klh_ini); klfk.settle = v < 100 ? 100 : v > 5000 ? 5000 : v;
    klog("fedkit: on; Hunt=%d Crosshair=%d (two bytes of the Arcade rules object, only while you are a fed in play) Body=%d (the level's [FedBody]) AkChance=%d AkItem=%d KitSettle=%d (game calls, once per fed); only on a level that is not the stock one of its slot",
         klfk.hunt, klfk.cross, klfk.body, klfk.ak, klfk.akitem, klfk.settle);
}

#endif /* KLFEDKIT_C */
