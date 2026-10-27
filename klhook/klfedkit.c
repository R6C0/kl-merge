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
 * loadout routine) and are OFF unless their key is set. Sections 5 - 7 (track S: no traitor mark, his kills pay,
 * the HUD's two blocks on one place) are DATA WRITES ONLY again: the score object's dwords of client 0, one byte of
 * the player, one int of the tuning object, two fields of a HUD element. No code byte and no import slot changes. Research and the
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
 * 5. A FED IS ONLY A FED: NO TRAITOR MARK (key NoTraitor, default 1)          sections 5 - 7: track S, 2026-10-11
 *    The owner, after six kills as a fed on the bank (KLHook.log 14:30:58 .. 14:31:22; pictures research\watch\
 *    20261011_142846\0008, 0009): 'i became a traitor, as a fed youre only a fed, hud glitch fix and as a fed kill
 *    should pay check the FA multiplayer for these things'. His HUD: 'You killed a criminal. $0', the name replaced by
 *    'Traitor' in orange, 'Total score: -20,000'.
 *    EXE, Arcade: a dead AI heister reaches ZGameRulesHeist slot 16 = 0x485740, which calls the crew bookkeeping
 *    0x6706b0(victim index, killer object, &killer index, &'killer is police', &..) - a routine ONLY the Arcade class
 *    has (two callers: 0x4857b9 and the human's own kill rule 0x70472f). For a ZFFPlayer killer the killer index is 0
 *    (0x6707bc). At 0x6709dd: the victim is no policeman (slot 107 = 0x5aae60: client flag 8), does not carry flag 1
 *    (0x6709f4) and holds no yellow card against the killer (slot 122 = 0x833f70) -> slot 129 = 0x8fb0d0(killer,
 *    victim) 'becomes a traitor'. NOTHING on that way asks whether the KILLER is police. Slot 129, read whole:
 *      a. when [rules+0x1b3] == 0xff, the killer has no flag 1 and the victim neither 0x20 nor 0x40: the announcer
 *         0x67ee80(killer, victim, first = ([rules+0xe84] == 0)) - which skips every line and voice for a local
 *         client that is police (0x67ef20) and, when 'first', pops the player list up (0x72d130) and plays the
 *         betrayal sting (0x67f074 ..); then flag 2 on the killer with a 5 s timer (record +0x70);
 *      b. 0x8fb193 `test byte [score + 4 * killer + 0x1d4], 1 / jne end`: A KILLER WHO ALREADY CARRIES FLAG 1 GETS
 *         NOTHING OF WHAT FOLLOWS;
 *      c. flag 1 (slot 115 = 0x7ca230, a plain `or`), the local player's byte +0x2726 = 1 (0x70f770, which also tells
 *         the sense manager [0x1535c70], 0x4801a0);
 *      d. for killer 0 only (0x8fb1cf): `[score+0x24] += [tuning+0xc10]` (0x8fb1d3; tuning = [0x168d7c0], the int is
 *         -25000 in the constructor, 0x5309f7; no other reader was found) and the points pop-up (ZHeistPointsPopupDisplay
 *         slot 11 = 0x66bfa0: "%s$%d", sign and amount);
 *      e. a clamp of byte +0x35 of the killer's crew record; then (back in 0x6706b0) the hint state of slot 105 and
 *         `inc [rules+0xe84]`.
 *    The HUD's top-left block takes the local row's role from 0x572050, which tests flag 1 BEFORE flag 8: a client
 *    with both reads 'Traitor' (0x6f31b9 FA_Traitor) - his picture. -20,000 = that -25000 + the 5000 every NPC kill
 *    adds to the round's kill line ([score+0x10] += [tuning+0xbf8], 0x48592a).
 *    EXE, MULTIPLAYER: the server class's slot 129 = 0x41d480 begins `flags(killer) & 0xc -> return` (0x41d4ac): a
 *    client that is police (8) or dead (4) is never made a traitor; and its kill reward routine 0x4eb260 has the
 *    'killer is police' branch of section 6. Arcade's copy lost that test.
 *    NO DATA STOPS SLOT 129 for a police killer without a price: the three ways past it are a victim that carries
 *    flag 1 (pays 100000 a kill and changes the payout), yellow cards on every heister (flag 0x400: the exe has 35
 *    `test eax, 0x400` sites, not sorted) and a killer who already carries flag 1 (reads 'Traitor' on the HUD). So the hook lets the game's
 *    routine run and takes back what it did, every frame of the main loop while he is a fed in play:
 *      - bits 1 and 2 of client 0's dword [score+0x1d4] cleared when bit 1 is set (a read-modify-write of one dword,
 *        on the game's thread only; slot 116 = 0x676070 does the same `and`);
 *      - the local player's byte +0x2726 = 0 when it is set;
 *      - the int [tuning+0xc10] HELD at what section 6 wants (0 without Pay) from the pass that first sees him, so
 *        the kill never costs the 25000; put back to what the hook found when he is no fed in play any more (his
 *        second death, the round's end, a heister again), if it is still the hook's number on the same object;
 *      - should a negative amount land in [score+0x24] all the same (the int could not be written), it is taken out.
 *      A change of [score+0x24] counts as slot 129's ONLY in a frame that also finds flag 1 set (c and d are one
 *      call); any other change is the game's and only moves the hook's note of the line (review SHOULD 1).
 *      The put-back of the int is tried again at every pass until it holds, and a number above 0 found there before
 *      the hook's first write is never taken for the game's: -25000 is what goes back then (review SHOULD 5).
 *    WITH THE FLAG CLEARED, SLOT 129'S FIRST PART (a) AND ITS LAST (e) RUN AT EVERY KILL, not once a round: flag 2
 *    and its 5 s timer at record +0x70 are set anew each time (the hook clears flag 2 with flag 1; the timer runs
 *    out by itself), and the minimum into byte +0x35 of HIS crew record is taken again with the numbers of that
 *    moment. WHAT +0x35 IS WAS NOT READ - it can only fall, kill by kill, where stock lets it fall once.
 *    WHAT STAYS (EXE, NOT SEEN): the role can read 'Traitor' for the frame between the kill and the hook's pass;
 *    A KILL IN THE ROUND'S VERY LAST FRAME (slot 192 leaves state 0x19 in the frame of the kill): the hook's frame
 *    does not run any more - flag 1 and byte +0x2726 stay, the score page can read 'Traitor', that kill is not paid;
 *    the round reset 0x8c7a80 clears the flags, the police object with its byte is not used again;
 *    at his FIRST kill of a round in which nobody has betrayed yet the player list pops up for 2 s and the betrayal
 *    sting plays (a, 'first'; one int, [rules+0xe84], would stop it - its other readers were not followed, so it is
 *    not written); the sense manager is told 'the player changed' at every kill (c) and not again at the hook's
 *    clear - of the readers of +0x2726 that were read, the soldier's target test (0x882470) and the crosshair
 *    (0x8e9dfc) ask the police byte first, and the NPC damage routine lets an Ally NPC's hit on a marked Ally victim
 *    count while the byte is set (0x61aac1 .. 0x61ab17): one frame; the other fifteen readers were NOT read; bytes
 *    +0x35 / +0x12 of his own record and the count [rules+0xe84] stay as the game left them.
 *
 * 6. HIS KILLS PAY, AS MULTIPLAYER PAYS A COP (key Pay, default 1; PayKill = another amount)
 *    EXE, MULTIPLAYER, 0x4eb260(rules; killer player, victim player), the kill reward of the Fragile Alliance
 *    classes (0x794190 <- the server's slot 11, and the client's slot 11), by the role tests slot 108 'traitor'
 *    (Arcade's copy 0x6ee0f0 says no for a client with flag 8, 0x6ee12a), 110 (flag 0x80, the undercover cop) and
 *    112 ('a criminal': not police, not 0x80):
 *        killer a traitor                                        nothing
 *        criminal kills a traitor                                [tuning+0x65c] = 100000
 *        criminal kills a policeman                              [tuning+0x66c] = 10000 (an undercover cop +0x674 = 100000)
 *        POLICEMAN KILLS A CRIMINAL                              [tuning+0x664] = 50000        (0x4eb4c4)
 *        policeman kills a traitor                               +0x65c = 100000; the traitor who had killed HIM: +0x660 = 200000
 *        policeman kills a policeman                             nothing
 *    A FIXED REWARD: what the criminal carried plays no part (no money term is in the routine). It goes to the
 *    killer's score at once (0x7f3050 on [rules+0x2c]) with the line "<name> +N" in the points pop-up, and the
 *    announcement 'You killed a criminal. {Reward1}' (FA_Killed_Merc, 0x463f67) takes its number from rules slot
 *    169(0) - for both multiplayer classes 0x4d8950, a table read: kind 0 = [tuning+0x664]. At the round's end the
 *    outro gives a police client the line 'Your finder's fee' = the money he holds (0x73dcd3; Arcade's own copy
 *    0x7df24c with the payout's police branch 0x7965f2: record +0x28 = [score+0x150 + 4 * i]) besides his rewards.
 *    EXE, ARCADE: ZGameRulesHeist slot 169 = 0x58bbd0 = `xor eax, eax / ret 4`: EVERY reward kind is 0 - 'You killed
 *    a criminal. $0'. Slot 128 (the multiplayer server's 0x5df280) is `ret 0x10`. What Arcade does give at a crew
 *    kill: 5000 to the kill line as for any NPC (0x48592a) and, for a victim with flag 1, 100000 / 200000 to the
 *    killer's rewards [score+0x184 + 4 * killer] (0x67098e / 0x670968) - the same column the list's rows read
 *    (slot 55 = 0x6c05f0). AND AT THE ROUND'S END (slot 192 = 0x5dff40, 0x5dffec): a human who has not escaped
 *    (never flag 0x40: a policeman cannot board, 0x68414e) gets his round-start numbers back (0x491ad0), loses the
 *    life, and EVERY LINE OF THE ROUND IS ZEROED ([score+4 .. +0x30], 0x696410) before the round is added to the
 *    total (`[score+0x38] += [score+0x30]`, 0x5e001b; the shop buys from that total, 0x8eaa4a). So whatever a fed
 *    earns in a round line is gone three seconds after the last heister.
 *    THE HOOK: slot 169 is code, the announcement keeps its '$0' (see below). But 5.d is a ready-made 'add an amount
 *    to client 0 and show it' that runs exactly when the human has killed a heister who is no traitor - the case
 *    multiplayer pays 50000 for - and section 5 makes it run at EVERY such kill. So while he is a fed in play
 *    [tuning+0xc10] is held at +N, N = the game's own [tuning+0x664] (or PayKill): the game adds N to [score+0x24]
 *    and shows '+$N' in its points pop-up; the hook's next pass moves it out of that doomed line:
 *        [score+0x24] back to what it was when he became a fed;  [score+0x38] += N  (the total: kept, and the
 *        HUD's 'Total score' = money + lines + total does not change by the move).
 *        (The first version also added N to his rewards [score+0x184] for the list's column; that rested on an
 *        assumption nobody has seen and is gone - review SHOULD 4. The rewards int is only READ now.)
 *    A TRAITOR VICTIM (flag 1: a bot that backstabbed, or one klgrudge.c marked) never reaches slot 129 (0x6709f4);
 *    the game itself pays the killer on the way before it (0x6708a9 .. 0x6709ad: victim a traitor by slot 108, the
 *    killer neither by 108 nor 109): [score+0x184 + 4 * killer] += [tuning+0x65c] = 100000, or += [tuning+0x660] =
 *    200000 (and [score+0x18] += [tuning+0xc04]) when the victim is the one who had killed him - multiplayer's two
 *    numbers for a policeman. But the rewards int is given back to its round-start value at the round's end for a
 *    man who did not escape (0x491ad0), so a fed would keep NOTHING of it. With Pay the hook ADDS the same amount
 *    to the total when it sees, in one frame: the rewards risen by exactly one of those two ints AND the crew-kill
 *    byte [score+0x126] moved (0x6709bd, the same call). Nothing is taken out of the rewards: for the rest of that
 *    round 'Total score' may count it twice IF slot 56 includes the rewards (NOT READ) - the kept total is right.
 *    Pay needs NoTraitor (without the flag cleared the routine runs once a round). NOT PAID by this rule: a second
 *    kill in the same frame as another (the flag is still set: nothing is added; the log's kill count shows it),
 *    two traitors in one frame (the sum is neither number), a heister with a yellow card against him.
 *    WHERE THE PAID MONEY GOES WHEN THE SESSION ENDS (EXE 0x68b930, re\leaderboard.md 2.1 / 2.3; review MUST 1):
 *    [score+0x38] is read by the stats commit of the last life / of Quit: stats+0x24 = max, HeistTotalPoints[slot]
 *    = max (0x68bad9), the LOCAL top-12 list of the STOCK slot (profile+0x1408 + slot * 0x30, 0x68bb6d ..) which
 *    0x6587c0 saves to disk, and it is the score of UploadLeaderboardScore. STEAM: blocked ONLY BY klsteam.c's
 *    guard for a level that is not stock (this part acts only with klx_on and verdict 2 - the same test); should
 *    that guard ever be off or changed, Pay's money would be uploaded. THE LOCAL PROFILE: NOTHING PROTECTS IT - a
 *    tab-map session already files its total under the stock slot's list; Pay adds up to 7 x 50000 a fed round
 *    that stock Arcade would never have given (a fed round banks 0 there). Pay=0 keeps that out.
 *    WHAT STAYS WRONG: THE TEXT 'You killed a criminal. $0'. It is set once into the announcement's two text objects
 *    (0x468430) from slot 169's 0; no data reaches it. A LEVEL fix exists and is not this file's: the string
 *    AllLevels/Interface/Online/Announcements/FA_Killed_Merc of the map's .LOC without its '{Reward1}' - that text
 *    is shown ONLY to a police human who killed a heister. And the life: a fed's round still costs it (not changed).
 *
 * 7. THE HUD: THE LIST AND THE NAME BLOCK ON ONE PLACE (key HudFade, default 1; 2 = for a heister too)
 *    EXE: both are ONE element, ZFAPlayerListDisplay (osd +0x10c4, vtable 0xbbdf6c), by its state dword +0xee0:
 *    0 = the block (name and skulls, 'Total score', 'Round'), 2 = the list (shown 2 s by 0x72d130(0) at every kill
 *    announcement, 0x704ae1, and at a betrayal; 10 s by 0x72d130(1) from 0x7f919a - ASSUMED the list key), 1 = THE
 *    WAY BACK: the update (slot 5 = 0x76db00)
 *    adds dt x 0.5 to +0xf00 (0x76db86: the double 0.5 at 0xb35790) and the render (slot 2 = 0x5e60f0) draws the
 *    block with alpha +0xf00 (0x5e6249) AND the list with alpha 1 - +0xf00 (0x5e66bb) AT THE SAME PLACE - for two
 *    seconds two texts lie on each other (the block's 'Total score:' on the list's header, 'Round: 1' on its
 *    first row: picture 0008). No test of the player's side is in it: a heister sees the same after every kill;
 *    a fed who hunts sees it six times in a minute.
 *    THE WRITE, on the game's thread, when the state is 1: the state = 0 and +0xf00 = -1.0 - the two values the
 *    update itself writes when the fade is over (0x76dbab / 0x76dbb1). The list goes, the block stands at once.
 *    The element is reached as the game reaches it: [[gamedata+0x15dc]] when the byte beside it is not 0xff
 *    (0x588680, 0x4ddae0), then +0x10c4; it must have 0x76db00 in slot 5 of its vtable (the stock one, or a private
 *    copy klhud.c made).
 *
 * KLHook.ini (all under klfed.c's section; nothing here acts unless Enable=1 and Player=1)
 *   [Fed]
 *   NoTraitor=1       section 5: your kills of the crew leave no traitor flag and cost no 25000
 *   Pay=1             section 6: each heister you kill pays what multiplayer pays a cop, kept in your total
 *                     (that total is also what the session's end files in your LOCAL profile's high scores of the stock slot)
 *   PayKill=0         the amount; 0 = the game's own number [tuning+0x664] (50000)
 *   HudFade=1         section 7: no two seconds of list and name block on one place; 2 = for a heister as well; 0 = stock
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
 *   fedkit: rules: your flags 00080108, round line [score+0x24] 0, total 0; [tuning+0xc10] -25000 -> 50000 (what a kill of a heister adds for you) ...
 *   fedkit: traitor: the game marked you a traitor (flags 0008010b): flags -> 00080108, the player's traitor byte 1 -> 0 (1 of this life)
 *   fedkit: pay: +50000 for a heister (kill 1 of this life, your crew kills this round 1, 50000 paid in all): round line 50000 -> 0, total 0 -> 50000
 *   fedkit: pay: +100000 for a TRAITOR ([tuning+0x65c]; the game put it into your rewards 0 -> 100000, which the round's end takes back): total 50000 -> 150000, 150000 paid in all
 *   fedkit: the round line [score+0x24] went 0 -> -5 with no traitor flag set: not the traitor rule's add, left alone
 *   fedkit: traitor: [tuning+0xc10] put back to -25000 (you are no fed in play)
 *   fedkit: hud: the player list's cross-fade cut (state 1 -> 0, fade 0.01 -> -1.0): the name block stands alone at once
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
#define KLFK_SCORE      0x5f8                 /* rules: the score object */
#define KLFK_S_FLAGS    0x1d4                 /* score: one dword per client (getter slot 114 = 0x771a10); 1 traitor, 2 its 5 s mark, 8 police */
#define KLFK_S_REWARDS  0x184                 /* score: one int per client, the rewards column (slot 55 = 0x6c05f0) */
#define KLFK_S_LINE     0x24                  /* score: the round line slot 129 adds [tuning+0xc10] to */
#define KLFK_S_TOTAL    0x38                  /* score: the total the round's end adds the round to and the shop buys from */
#define KLFK_S_KILLS    0x126                 /* score: one byte per client, crew records he killed this round (0x6709bd) */
#define KLFK_GET114     0x00771a10
#define KLFK_BECOME     0x008fb0d0            /* ZGameRulesHeist slot 129: (killer, victim) becomes a traitor */
#define KLFK_TUNING     0x0168d7c0
#define KLFK_T_PENALTY  0xc10                 /* int, -25000: what slot 129 adds for client 0 */
#define KLFK_T_COPKILL  0x664                 /* int, 50000: multiplayer's 'a policeman killed a criminal' (0x4eb4c4) */
#define KLFK_T_TRAITOR  0x65c                 /* int, 100000: a traitor killed (multiplayer 0x4eb260; Arcade 0x67099b, into the killer's rewards) */
#define KLFK_T_REVENGE  0x660                 /* int, 200000: the traitor who had killed the killer (Arcade 0x670975) */
#define KLFK_PENALTY    (-25000)              /* what the tuning's constructor puts at +0xc10 (0x5309f7) */
#define KLFK_TRAITOR    0x2726               /* player: the traitor byte (0x70f770) */
#define KLFK_OSDHOLD    0x15dc                /* gamedata: -> { osd, byte != 0xff } (0x588680, 0x4ddae0) */
#define KLFK_O_PLIST    0x10c4                /* osd: ZFAPlayerListDisplay */
#define KLFK_PL_UPDATE  0x0076db00            /* its slot 5 */
#define KLFK_PL_STATE   0xee0                 /* 0 the name block, 1 block and list cross-fading, 2 the list */
#define KLFK_PL_FADE    0xf00

static int klx_on;                                                    /* klsteam.c, included after this file */
static int klx_level_verdict(const char *scene, char *why);           /* 0 no level, 1 stock, 2 not stock, 3 not known; why[200] */

static struct { int on, log, hunt, cross, body, ak, akitem, settle, notraitor, pay, paykill, fade, noloot; } klfk;
static struct {                               /* the level's [FedBody] */
    char key[64], file[MAX_PATH]; FILETIME ft;
    int on, nvar, var[KLFK_NVAR], akitem, akrecord; DWORD entries, root, stock; char name[80];
} klfk_lv;
static struct {                               /* the fed of this round */
    DWORD player, rules, since; int dice, variant, told, hunt_n, cross_n, body, body_tries, look_calls, ak, told_gate, told_thread;
    int live;                                 /* the last pass found every gate of section 0 open: the every-frame step may act */
    int rule;                                 /* sections 5 / 6: 0 not looked at, 1 the game's routine is the known one, 2 it is not (said) */
    int line0, amount, clear_n, paid_n, paid_sum, undo_n, told_rule;
    int rew0, kills0, trait_n, other_n;       /* the rewards int and the crew-kill byte of client 0 as the last frame saw them */
    int cash0, cash_have, cash_n;             /* NoLoot: the carried money [score+0x150] as the fed held it, and how many grabs were undone */
} klfk_r;
static struct { DWORD rules; BYTE was; int have; } klfk_cov;       /* [rules+0x283] as the hook found it, to put back */
static struct { DWORD tun; int was, set, have; } klfk_pen;         /* [tuning+0xc10] as the hook found it and what it wrote, to put back */
static int klfk_fade_n;

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

/* ---------------------------------------------------------------- sections 5 and 6: no traitor mark, his kills pay */

/* [tuning+0xc10] back to what the hook found there, when it still holds the hook's number on the same object */
static void klfk_pen_back(const char *why)
{
    static int told; DWORD t; int cur = 0;
    if (!klfk_pen.have) return;
    /* nothing of the hook's is there any more: another tuning object, the int unreadable, or not the hook's number */
    if (!(t = klh_rd32((DWORD_PTR)KLH_VA(KLFK_TUNING))) || t != klfk_pen.tun || !klh_rd(t + KLFK_T_PENALTY, &cur, 4) || cur != klfk_pen.set || cur == klfk_pen.was) { klfk_pen.have = 0; told = 0; return; }
    if (klh_data((void *)(DWORD_PTR)(t + KLFK_T_PENALTY), &klfk_pen.was, 4, "tuning: what the Arcade rules add for a crew kill of client 0, put back")) {
        klfk_pen.have = 0; told = 0;
        if (klfk.log) klog("fedkit: traitor: [tuning+0xc10] put back to %d (%s)", klfk_pen.was, why);
    } else if (!told++)     /* 'have' STAYS: every later pass tries again, and a next fed does not take the hook's number for the game's */
        klog("fedkit: traitor: [tuning+0xc10] could NOT be put back to %d: it stays %d; tried again at every pass", klfk_pen.was, cur);
}

/* The 50 ms pass of sections 5 / 6 while he is a fed in play: once per fed the game's routine is compared and the
   round line's value noted, then the int slot 129 adds for client 0 is HELD at 0 (no penalty) or at the pay. */
static void klfk_rule_pass(DWORD score)
{
    static const BYTE flag_code[16] = { 0x8b, 0x96, 0xf8, 0x05, 0x00, 0x00, 0x0f, 0xbe, 0xfb, 0xf6, 0x84, 0xba, 0xd4, 0x01, 0x00, 0x00 };  /* 0x8fb193 mov edx,[esi+0x5f8] ; movsx edi,bl ; test byte [edx+edi*4+0x1d4],.. */
    static const BYTE add_code[16] = { 0x8b, 0x0d, 0xc0, 0xd7, 0x68, 0x01, 0x8b, 0x91, 0x10, 0x0c, 0x00, 0x00, 0x8b, 0x86, 0xf8, 0x05 };   /* 0x8fb1d3 mov ecx,[0x168d7c0] ; mov edx,[ecx+0xc10] ; mov eax,[esi+0x5f8].. */
    DWORD t, flags = 0; int cur = 0, want = 0, n = 0, total = 0; BYTE kb = 0;
    if (!klfk.notraitor || klfk_r.rule == 2) return;
    if (!klfk_r.rule) {
        if (klh_rd32((DWORD_PTR)KLH_VA(KLFK_RULES_VT + 4 * 129)) != KLFK_BECOME || klh_rd32((DWORD_PTR)KLH_VA(KLFK_RULES_VT + 4 * 114)) != KLFK_GET114 ||
            !klc_same_code(KLFK_BECOME + 0xc3, flag_code, sizeof flag_code) || !klc_same_code(KLFK_BECOME + 0x103, add_code, sizeof add_code) ||
            !klh_rd(score + KLFK_S_LINE, &klfk_r.line0, 4) || !klh_rd(score + KLFK_S_REWARDS, &klfk_r.rew0, 4) || !klh_rd(score + KLFK_S_KILLS, &kb, 1)) {
            klfk_r.rule = 2; klog("fedkit: slots 129 / 114 of the Arcade rules are not the routines this build knows (or the score object cannot be read): NoTraitor and Pay write nothing");
            return;
        }
        klfk_r.rule = 1; klfk_r.kills0 = kb;
    }
    if (!(t = klh_rd32((DWORD_PTR)KLH_VA(KLFK_TUNING))) || !klh_rd(t + KLFK_T_PENALTY, &cur, 4)) return;
    if (klfk.pay) {                                           /* multiplayer's own number for 'a policeman killed a criminal', read where the game keeps it */
        want = klfk.paykill;
        if (want <= 0) want = klh_rd(t + KLFK_T_COPKILL, &n, 4) && n > 0 && n <= 10000000 ? n : 50000;
    }
    klfk_r.amount = want;
    if (klfk_pen.have && klfk_pen.tun == t && cur == klfk_pen.set && cur == want) return;                  /* held */
    if (!(klfk_pen.have && klfk_pen.tun == t && cur == klfk_pen.set)) {     /* the game's own number: first time, another object, or written again by the game */
        klfk_pen.tun = t; klfk_pen.was = cur;
        if (cur > 0) {                                        /* the game's is a penalty: a number above 0 is a pay the hook left behind */
            klfk_pen.was = KLFK_PENALTY;
            klog("fedkit: traitor: [tuning+0xc10] is %d before the hook wrote it - not the game's penalty: %d (the constructor's, 0x5309f7) is what will be put back", cur, KLFK_PENALTY);
        }
    }
    klfk_pen.have = 1; klfk_pen.set = want;
    if (cur != want && !klh_data((void *)(DWORD_PTR)(t + KLFK_T_PENALTY), &want, 4, "tuning: what the Arcade rules add for a crew kill of client 0")) {
        klfk_pen.set = cur;
        if (!klfk_r.told_rule++) klog("fedkit: traitor: [tuning+0xc10] could NOT be written: it stays %d (a penalty that lands in the round line is taken out again)", cur);
        return;
    }
    if (!klfk_r.told_rule++ && klfk.log) {
        klh_rd(score + KLFK_S_FLAGS, &flags, 4); klh_rd(score + KLFK_S_TOTAL, &total, 4);
        klog("fedkit: rules: your flags %08lx, round line [score+0x24] %d, total [score+0x38] %d; [tuning+0xc10] %d -> %d (what a kill of a heister adds for you: %s); the traitor mark is taken off again at every frame",
             flags, klfk_r.line0, total, klfk_pen.was, want, want ? "multiplayer's reward for a policeman who kills a criminal, moved to your total at once" : "nothing - Pay=0");
    }
}

/* EVERY frame of the main loop while a fed is in play (the game's thread only: a read-modify-write of dwords the
   game writes): what the Arcade rules' 'becomes a traitor' did at his kill is taken back, what it added is moved
   out of the round line - which the round's end wipes for a man who did not escape - into the total. It asks the few things again that the 50 ms pass asked (he is still that fed, in play). */
static void klfk_rule_frame(void)
{
    DWORD sm, gs, rules, gd, player, recs, score, t, flags = 0, nf, st = 0; BYTE sel = 0xff, pol = 0, status = 1, tr = 0, zero = 0, kills = 0;
    int line = 0, total = 0, rew = 0, a = 0, b = 0, d, marked;
    if (!klfk_r.live || klfk_r.rule != 1) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLFK_SESSION))) || klh_rd32(sm + 0x5c) != 4 || !klh_rd(sm + 0x70, &st, 4) || st != KLFK_ROUND) return;
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLFK_SETTINGS))) || (rules = klh_rd32(gs + 0x54)) != klfk_r.rules || klh_rd32(rules) != KLFK_RULES_VT) return;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel >= 28 || (player = klh_rd32(gd + 0x828 + 4 * sel)) != klfk_r.player ||
        !klh_rd(player + 0x2723, &pol, 1) || !pol) return;
    if (!(recs = klh_rd32(rules + 0x348)) || !klh_rd(recs + 0x10, &status, 1) || status) return;
    if (!(score = klh_rd32(rules + KLFK_SCORE)) || !klh_rd(score + KLFK_S_FLAGS, &flags, 4)) return;
    /* NoLoot: a police human is a 'player' to the loot trigger and to rules slot 201 (0x56f6e0: alive, not down -> 0x8e8750), which asks
       no role, so a fed who stands in a money object's reach (a case, or the stacks a dead bot dropped) is PAID its parts: 50-100K a second
       in the log (18:41:22 .. 18:41:39, Hasta, fed beside a dead bot's $1.29M; 11:10 the same). Fed rounds pay in the total (Pay) and the round
       line is zeroed at the end, so the carried money [score+0x150] of a fed is held where it was: a rise is written back every frame. */
    if (klfk.noloot) {
        int cash = 0, base;
        if (klh_rd(score + 0x150, &cash, 4) && cash >= 0 && cash < 100000000) {
            if (!klfk_r.cash_have) { klfk_r.cash_have = 1; klfk_r.cash0 = cash; }
            else if (cash < klfk_r.cash0) klfk_r.cash0 = cash;         /* a debit of somebody else's (the adrenaline share) lowers the mark */
            else if (cash > klfk_r.cash0) {
                base = klfk_r.cash0;
                if (klh_data((void *)(DWORD_PTR)(score + 0x150), &base, 4, "Arcade score: the fed's carried money (NoLoot)")) {
                    if (!klfk_r.cash_n++ || klfk.log > 1) klog("fedkit: noloot: a fed grabbed money (carried %d -> %d): put back to %d (%d of this life; the round's lines of a fed are zeroed at the end anyway)", base, cash, base, klfk_r.cash_n);
                } else if (!klfk_r.cash_n++) klog("fedkit: noloot: the carried money [score+0x150] could NOT be written");
            }
        }
    }
    klh_rd(player + KLFK_TRAITOR, &tr, 1);
    marked = (flags & 1) != 0;                                /* slot 129 ran since the last frame: it sets the flag in the call that adds to the round line */
    if (marked) {
        nf = flags & ~3u;                                    /* 1 = traitor, 2 = the five-second mark slot 129 sets with it */
        if (klh_data((void *)(DWORD_PTR)(score + KLFK_S_FLAGS), &nf, 4, "Arcade score: the traitor flag of a police human")) {
            if (!klfk_r.clear_n++ || klfk.log > 1)
                klog("fedkit: traitor: the game marked you a traitor (flags %08lx): flags -> %08lx, the player's traitor byte %u -> 0 (%d of this life)", flags, nf, tr, klfk_r.clear_n);
        } else if (!klfk_r.clear_n++) klog("fedkit: traitor: the flags [score+0x1d4] could NOT be written");
    }
    if (tr) klh_data((void *)(DWORD_PTR)(player + KLFK_TRAITOR), &zero, 1, "the police player's traitor byte");
    klh_rd(score + KLFK_S_KILLS, &kills, 1);
    /* section 6, a TRAITOR victim: the game itself has just put [tuning+0x65c] (or +0x660: he had killed the fed)
       into the fed's rewards (0x67099b / 0x670975, on the way that also counts the crew-kill byte, 0x6709bd) - a
       column the round's end takes back from a man who did not escape. The same amount is ADDED to the total, only
       when all three agree: the rewards rose since the last frame, by exactly one of the game's two numbers, and the
       crew-kill byte moved with it. The rewards int itself is never written by the hook. */
    if (klh_rd(score + KLFK_S_REWARDS, &rew, 4)) {
        d = rew - klfk_r.rew0;
        if (d > 0 && klfk.pay && (int)kills != klfk_r.kills0 && (t = klh_rd32((DWORD_PTR)KLH_VA(KLFK_TUNING))) != 0 &&
            ((klh_rd(t + KLFK_T_TRAITOR, &a, 4) && d == a) || (klh_rd(t + KLFK_T_REVENGE, &b, 4) && d == b)) && klh_rd(score + KLFK_S_TOTAL, &total, 4)) {
            total += d;
            if (klh_data((void *)(DWORD_PTR)(score + KLFK_S_TOTAL), &total, 4, "Arcade score: the total")) {
                klfk_r.trait_n++; klfk_r.paid_sum += d;
                if (klfk.log) klog("fedkit: pay: +%d for a TRAITOR (%s; the game put it into your rewards %d -> %d, which the round's end takes back): total %d -> %d, %d paid in all",
                                   d, d == a ? "[tuning+0x65c]" : "[tuning+0x660]: the one who had killed you", klfk_r.rew0, rew, total - d, total, klfk_r.paid_sum);
            }
        }
        klfk_r.rew0 = rew;
    }
    klfk_r.kills0 = kills;
    if (!klh_rd(score + KLFK_S_LINE, &line, 4) || (d = line - klfk_r.line0) == 0) return;
    if (!marked) {                                            /* not slot 129's add (that always comes with the flag): whatever changed the line is the game's - neither paid nor undone */
        if (!klfk_r.other_n++ || klfk.log > 1) klog("fedkit: the round line [score+0x24] went %d -> %d with no traitor flag set: not the traitor rule's add, left alone", klfk_r.line0, line);
        klfk_r.line0 = line; return;
    }
    if (d > 0 && !klfk.pay) { klfk_r.line0 = line; return; }                                              /* not the hook's amount: it stays where the game put it */
    if (!klh_data((void *)(DWORD_PTR)(score + KLFK_S_LINE), &klfk_r.line0, 4, "Arcade score: the round line of the traitor rule")) return;
    if (d < 0) {
        if (!klfk_r.undo_n++ || klfk.log > 1) klog("fedkit: traitor: a penalty of %d in the round line [score+0x24] taken out again (%d -> %d)", d, line, klfk_r.line0);
        return;
    }
    if (!klh_rd(score + KLFK_S_TOTAL, &total, 4)) return;
    total += d;
    klh_data((void *)(DWORD_PTR)(score + KLFK_S_TOTAL), &total, 4, "Arcade score: the total");
    klfk_r.paid_n++; klfk_r.paid_sum += d;
    if (klfk.log) klog("fedkit: pay: +%d for a heister (kill %d of this life, your crew kills this round %u, %d paid in all): round line %d -> %d, total %d -> %d",
                       d, klfk_r.paid_n, kills, klfk_r.paid_sum, line, klfk_r.line0, total - d, total);
}

/* ---------------------------------------------------------------- section 7: the list and the name block on one place */

static void klfk_fade(int game_thread)
{
    static const BYTE upd_code[13] = { 0x83, 0xbe, 0xe0, 0x0e, 0x00, 0x00, 0x01, 0xd9, 0x05, 0x80, 0xe9, 0xb3, 0x00 };    /* 0x76db6e cmp dword [esi+0xee0],1 ; fld dword [0xb3e980] */
    static const BYTE draw_code[13] = { 0x8b, 0x86, 0xe0, 0x0e, 0x00, 0x00, 0x85, 0xc0, 0x74, 0x09, 0x83, 0xf8, 0x01 };   /* 0x5e622c mov eax,[esi+0xee0] ; test eax,eax ; je ; cmp eax,1 */
    static int code, told;
    DWORD gd, hold, osd, list, vt, state = 0, zero = 0; BYTE none = 0xff; float f = 0.0f, over = -1.0f;
    if (!game_thread) return;                                 /* two fields: between two frames only */
    if (!code) {
        code = klc_same_code(KLFK_PL_UPDATE + 0x6e, upd_code, sizeof upd_code) && klc_same_code(0x005e622c, draw_code, sizeof draw_code) ? 1 : 2;
        if (code == 2) klog("fedkit: hud: the player list's update / render are not the routines this build knows: HudFade writes nothing");
    }
    if (code != 1) return;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(hold = klh_rd32(gd + KLFK_OSDHOLD)) || !klh_rd(hold + 4, &none, 1) || none == 0xff || !(osd = klh_rd32(hold)) ||
        !(list = klh_rd32(osd + KLFK_O_PLIST)) || !(vt = klh_rd32(list))) return;
    if (klh_rd32(vt + 4 * 5) != KLFK_PL_UPDATE) { if (!told++) klog("fedkit: hud: the element at osd+0x10c4 has not the player list's update in slot 5: HudFade writes nothing"); return; }
    if (!klh_rd(list + KLFK_PL_STATE, &state, 4) || state != 1 || !klh_rd(list + KLFK_PL_FADE, &f, 4)) return;
    /* the state first: in state 0 the render does not read the fade value */
    if (!klh_data((void *)(DWORD_PTR)(list + KLFK_PL_STATE), &zero, 4, "HUD player list: the cross-fade's state") ||
        !klh_data((void *)(DWORD_PTR)(list + KLFK_PL_FADE), &over, 4, "HUD player list: the cross-fade's value")) return;
    if (!klfk_fade_n++ || klfk.log > 1) klog("fedkit: hud: the player list's cross-fade cut (state 1 -> 0, fade %.2f -> -1.0, as the game leaves them when it is over): the name block stands alone at once (%d)", f, klfk_fade_n);
}

/* ---------------------------------------------------------------- the tick */

/* ---- 8. HUNTED (key Hunted, default 0; 2026-10-12, re\bots_active.md 3). DATA READS + the soldier's own order (klescort.c's kle_order2,
   the call klescort.c / klmove.c make), from the game's own thread, only while he is a fed in play (everything above holds).
   The owner, 2026-10-12: 'they kinda feel like bullet sponges when im a fed which isnt bad but they are slow meaning they just let
   it happen, come on the ai needs to have faster reactions than that'. WHAT IS KNOWN (re\balance.md 11.2, re\bots_active.md 3): kl2
   0x882470 already makes a police human a target for every crew soldier of team Ally (no list to fill: 'hostile at the respawn' is
   what the game does), and the crew's ZSoldier rows carry the same numbers as stock's (accuracy 50, field 5 / 13 / 14 = 50 on eCustom).
   What the logs show is a bot that stays on its hold with the fed shooting it (Restless leaves a bot under fire alone on purpose).
   (2026-10-12 second form: HuntedRange 9000; HuntedFire=1 walks the hit bot at the fed; with no hop near a step aside of HuntedPace.)
   WHAT THIS DOES: a crew bot that LOSES HEALTH while the fed is within HuntedRange gets, HuntedDelay ms later, the soldier's own order
   to one of the level's cover places ([Hops], tools\kl_fa_bots_rt.py hops; the same list klmove.c's RestlessHop uses) within that
   list's Max of its chain's place - a different cover, not the one the fed is aiming at. Bots within HuntedAlert of it that were not
   hit follow, 150 ms apart, each to its own place: the squad reacts as one. A bot gets at most one such order per HuntedGap seconds.
   WHAT IT DOES NOT DO: it does not make a bot shoot faster, and it cannot tell WHO hit the bot (police AI near the bot count too:
   the log says how far the fed was). It is a GUESS that a cut tactic and a new walk make the soldier's own combat tactics start
   over sooner (klescort.c 1: 'a running tactic is cut at its yield'); it may also take a bot out of a fight it was winning. The
   order is the one the escort and Restless already give; a bot that is an escort, a traitor, at stage 3 with a vehicle called,
   or inside an escape box is left alone. Nothing is written but that call. HuntedDry=1: log what it WOULD do. */
static struct { int on, dry, away, fire; float range, alert, pace, step, near_; DWORD delay, gap; } klfk_hu;
static struct { DWORD actor, hit_at, due, order_at; float hp; int hop_k; BYTE kind; } klfk_hb[KLB_NREC];       /* kind: 1 = hit, 2 = alerted */
static struct { DWORD rules, last; int hits, orders, told_hops, told_thread; } klfk_hr;

static void klfk_hunted(int game_thread, DWORD player, DWORD rules)
{
    struct klb_snap s; DWORD now = GetTickCount(), node, ho, actor, soldier; float fp[3], bp[3], bq[3], cur[3], want[3], got[3], raw[0x28 / 4], d; char why[200], w[100];
    int i, j, k, n, n_alert; struct kle_e t;
    if (!klfk_hu.on || now - klfk_hr.last < 250) return;
    klfk_hr.last = now;
    if (rules != klfk_hr.rules) { memset(klfk_hb, 0, sizeof klfk_hb); memset(&klfk_hr, 0, sizeof klfk_hr); klfk_hr.rules = rules; klfk_hr.last = now; }
    if (!klb_read(&s) || s.rules != rules || s.state != KLFK_ROUND || !klb_level(why)) return;
    if (!klh_rd(player + 0x460, fp, 12) || !kle_ok3(fp)) return;
    klmv_hops_load();
    for (i = 0; i < s.n && i < KLB_NREC; i++) {                    /* who lost health since the last look, and how far the fed was */
        const struct klb_rec *r = &s.r[i];
        if (!r->used || !(r->flags & 1) || r->status || !r->actor || klh_rd32(r->actor) != KLB_ACTOR_VT) { klfk_hb[i].hp = 0; continue; }
        if (r->actor != klfk_hb[i].actor) { memset(&klfk_hb[i], 0, sizeof klfk_hb[i]); klfk_hb[i].actor = r->actor; }
        if (!(ho = klh_rd32(r->actor + 0x5fc)) || !klh_rd(ho, raw, sizeof raw) || ((DWORD *)raw)[0x24 / 4] != r->actor || !klb_finite(raw[1])) continue;
        if (klfk_hb[i].hp > 0 && raw[1] < klfk_hb[i].hp - 0.05f && (node = klh_rd32(r->actor + 4)) != 0 && kle_node(node, bp, 0)) {
            d = klmv_h(bp, fp);
            klfk_hr.hits++;
            if (klfk.log > 1 || klfk_hr.hits <= 20) klog("fedkit: hunted: record %d lost %.1f (%.1f of %.1f left), %.1f m from you%s", i, klfk_hb[i].hp - raw[1], raw[1], raw[2], d / 100, d <= klfk_hu.range ? "" : " - too far: no reaction");
            if (d <= klfk_hu.range) {
                if (!klfk_hb[i].due) klfk_hb[i].due = now + klfk_hu.delay;
                klfk_hb[i].hit_at = now; klfk_hb[i].kind = 1;
                n_alert = 0;
                for (j = 0; j < s.n && j < KLB_NREC && klfk_hu.alert > 0; j++) {
                    const struct klb_rec *q = &s.r[j]; DWORD nj;
                    if (j == i || !q->used || !(q->flags & 1) || q->status || !q->actor || klh_rd32(q->actor) != KLB_ACTOR_VT || klfk_hb[j].due) continue;
                    if ((nj = klh_rd32(q->actor + 4)) != 0 && kle_node(nj, bq, 0) && klmv_h(bp, bq) <= klfk_hu.alert && fabs(bp[1] - bq[1]) <= 300.0f)
                    { klfk_hb[j].due = now + klfk_hu.delay + 150 * (DWORD)(++n_alert); klfk_hb[j].kind = 2; }
                }
            }
        }
        klfk_hb[i].hp = raw[1];
    }
    if (!game_thread) { if (!klfk_hr.told_thread++) klog("fedkit: hunted: the tick is not on the game's thread: nothing is ordered"); return; }
    for (i = 0; i < s.n && i < KLB_NREC; i++) {                    /* the due reactions */
        const struct klb_rec *r = &s.r[i];
        if (!klfk_hb[i].due || (LONG)(now - klfk_hb[i].due) < 0) continue;
        klfk_hb[i].due = 0;
        if (klfk_hb[i].order_at && now - klfk_hb[i].order_at < klfk_hu.gap) continue;
        if (kle_r.used[i] || (r->stage >= 3 && s.veh >= 1 && s.veh <= 5)) continue;           /* an escort, or the board tactic's / the rules' bot */
        if (klv_owned(i)) { if (kltr.on) kltr_line(i, "fedkit-hunted", "SKIP", 0, 0, 0, "WalkExclusive: klhop.c walks this bot"); continue; }      /* v82i GUESS, [Bots] WalkExclusive (default 0) */
        if (!kle_bot(&s, i, &actor, &soldier, bp, w)) continue;
        if (!kle_block(soldier, cur)) memcpy(cur, bp, 12);
        if (klmv_h(bp, fp) > klfk_hu.range * 1.5f) continue;                                    /* an alerted bot that is far from the fed */
        k = -1; j = 0;
        if (klfk_hu.fire && klfk_hb[i].kind == 1) {            /* HuntedFire: the bot that was hit walks at the fed (a bot that walks at an enemy sees him and answers by its own tactics: ASSUMED) */
            d = klmv_h(bp, fp);
            if (d > klfk_hu.near_) {
                float st = d - klfk_hu.near_ < klfk_hu.step ? d - klfk_hu.near_ : klfk_hu.step;
                want[0] = bp[0] + (fp[0] - bp[0]) / d * st; want[1] = bp[1]; want[2] = bp[2] + (fp[2] - bp[2]) / d * st;
                j = 1;
            }
        }
        if (!j && klmv_nhop) k = klmv_hop_pick(cur, bp, klfk_hb[i].hop_k, i, klfk_hu.away ? fp : 0, want), j = k >= 0 ? 2 : 0;
        if (!j) {                                              /* no hop near (the level has none here, or all are taken): a short step to a side of where it stands, a place 3 m or more away */
            int q;
            for (q = 0; q < 4 && !j; q++) {
                float ang; klb_seed = klb_seed * 1103515245u + 12345u;
                ang = (float)((klb_seed >> 16) % 360u) * 0.0174533f;
                want[0] = bp[0] + klfk_hu.pace * (float)cos(ang); want[1] = bp[1]; want[2] = bp[2] + klfk_hu.pace * (float)sin(ang);
                if (klmv_h(bp, want) >= KLMV_OFF) j = 3;
            }
        }
        if (!j) continue;
        memset(&t, 0, sizeof t); t.rec = i; t.actor = actor; t.soldier = soldier; t.told_soft = 1;
        kltr_set("fedkit-hunted", j == 1 ? "Hunted: hit bot walks at the fed" : j == 2 ? "Hunted: hit/alerted bot to a [Hops] cover place" : "Hunted: hit/alerted bot, a step aside", -1);
        n = kle_order2(&t, want, got, w, klfk_hu.dry);
        klfk_hb[i].order_at = now;
        if (!n) { if (klfk.log > 1) klog("fedkit: hunted: record %d NOT ordered: %s", i, w); continue; }
        if (j == 2) { klfk_hb[i].hop_k = k + 1; klmv_hop_take(k, i); }
        klfk_hr.orders++;
        if (n == 1) klmv_foreign(i, got);                      /* v82f: klmove.c's Restless must not take this place for its chain's */
        klog("fedkit: hunted: record %d %s %s (%.0f, %.0f, %.0f) from (%.0f, %.0f, %.0f), %.1f m from you; the game set (%.0f, %.0f, %.0f); order %d of the round", i,
             n == 2 ? "WOULD be ordered (dry run)" : "is ordered", j == 1 ? "TOWARDS YOU" : j == 2 ? "to a cover place of [Hops]" : "a step aside to",
             want[0], want[1], want[2], bp[0], bp[1], bp[2], klmv_h(bp, fp) / 100, got[0], got[1], got[2], klfk_hr.orders);
    }
}

static void klfk_pass(int game_thread)
{
    static const BYTE get189[7] = { 0x8a, 0x81, 0x85, 0x02, 0x00, 0x00, 0xc3 };          /* mov al, [ecx+0x285] ; ret */
    static const BYTE get186[7] = { 0x8a, 0x81, 0x83, 0x02, 0x00, 0x00, 0xc3 };          /* mov al, [ecx+0x283] ; ret */
    static int told_code;
    DWORD now = GetTickCount(), sm, gs, rules, gd, player, recs, freeb, client, score, sub = 0, state = 0, n = 0; BYTE sel = 0xff, type = 0, pol = 0, b = 1, raw[0x7c], cl[2], loot = 0, cover = 0, v;
    char scene[160], why[200];
    klfk_r.live = 0;
    /* ---- section 0: a police human in a running Arcade round of a level that is not stock */
    /* What is remembered of a fed (klfk_r) is dropped when the session or its rules object is gone, or when the local
       player is somebody who is no policeman (the next round's heister). It is KEPT through anything else - a pause,
       a state between two frames - so that one life gets one body and one throw of the dice. */
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLFK_SESSION))) || klh_rd32(sm + 0x5c) != 4 || !klh_rd(sm + 0x54, &sub, 4) || sub == 2 || sub == 3 ||
        !(gs = klh_rd32((DWORD_PTR)KLH_VA(KLFK_SETTINGS))) || !(rules = klh_rd32(gs + 0x54)) || klh_rd32(rules) != KLFK_RULES_VT) { klfk_r.player = 0; klfk_cov.have = 0; return; }
    if (klfk_cov.have && klfk_cov.rules != rules) klfk_cov.have = 0;      /* that rules object is gone: nothing to put back */
    if (!klh_rd(sm + 0x70, &state, 4) || state != KLFK_ROUND) return;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel >= 28 || !(player = klh_rd32(gd + 0x828 + 4 * sel)) || klh_pvt(player) != KLFK_PLAYER_VT ||
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
        klfk_r.player = 0;
        /* section 7 for a heister too, when asked for (HudFade=2): the same two seconds follow every kill line */
        if (klfk.fade == 2 && klx_on && klh_scene(scene, sizeof scene) && klx_level_verdict(scene, why) == 2) klfk_fade(game_thread);
        return;
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
    klfk_r.live = 1;
    /* ---- sections 5 - 7: the traitor rule's int held (its flag is taken off every frame: klfk_rule_frame), the HUD's cross-fade cut */
    if ((score = klh_rd32(rules + KLFK_SCORE)) != 0) klfk_rule_pass(score);
    if (klfk.fade) klfk_fade(game_thread);
    if (klfk_hu.on) klfk_hunted(game_thread, player, rules);          /* section 8 */
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

static void klfk_tick(int game_thread)
{
    static DWORD last; DWORD now;
    if (!klfk.on || !klh_exe_ok) return;
    if (game_thread && klfk_r.player) klfk_rule_frame();      /* sections 5 / 6: every frame of the main loop while a fed is known */
    now = GetTickCount();
    if (now - last < 50) return;
    last = now;
    klfk_pass(game_thread);
    if (!klfk_r.live) klfk_pen_back("you are no fed in play");    /* his second death, the round's end, the menu, a heister again: the game's own number */
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
    klfk.notraitor = GetPrivateProfileIntA("Fed", "NoTraitor", 1, klh_ini) != 0;
    klfk.noloot = GetPrivateProfileIntA("Fed", "NoLoot", 1, klh_ini) != 0;                  /* the fed's carried money is held where it was: a fed is no looter */
    klfk.pay = GetPrivateProfileIntA("Fed", "Pay", 1, klh_ini) != 0 && klfk.notraitor;       /* the game's routine pays only a killer without the traitor flag */
    v = (int)GetPrivateProfileIntA("Fed", "PayKill", 0, klh_ini); klfk.paykill = v < 0 ? 0 : v > 10000000 ? 10000000 : v;
    v = (int)GetPrivateProfileIntA("Fed", "HudFade", 1, klh_ini); klfk.fade = v < 0 ? 0 : v > 2 ? 2 : v;
    klfk_hu.on = GetPrivateProfileIntA("Fed", "Hunted", 0, klh_ini) != 0;
    if (klfk_hu.on) {
        char tb[32];
        GetPrivateProfileStringA("Fed", "HuntedRange", "9000", tb, sizeof tb, klh_ini); klfk_hu.range = (float)atof(tb); if (!klb_finite(klfk_hu.range) || klfk_hu.range < 500) klfk_hu.range = 500; if (klfk_hu.range > 20000) klfk_hu.range = 20000;
        GetPrivateProfileStringA("Fed", "HuntedAlert", "1500", tb, sizeof tb, klh_ini); klfk_hu.alert = (float)atof(tb); if (!klb_finite(klfk_hu.alert) || klfk_hu.alert < 0) klfk_hu.alert = 0; if (klfk_hu.alert > 5000) klfk_hu.alert = 5000;
        v = (int)GetPrivateProfileIntA("Fed", "HuntedDelay", 250, klh_ini); klfk_hu.delay = (DWORD)(v < 0 ? 0 : v > 3000 ? 3000 : v);
        v = (int)GetPrivateProfileIntA("Fed", "HuntedGap", 4, klh_ini); klfk_hu.gap = (DWORD)(v < 1 ? 1 : v > 60 ? 60 : v) * 1000;
        GetPrivateProfileStringA("Fed", "HuntedPace", "500", tb, sizeof tb, klh_ini); klfk_hu.pace = (float)atof(tb); if (!klb_finite(klfk_hu.pace) || klfk_hu.pace < 300) klfk_hu.pace = 300; if (klfk_hu.pace > 1500) klfk_hu.pace = 1500;
        GetPrivateProfileStringA("Fed", "HuntedStep", "1500", tb, sizeof tb, klh_ini); klfk_hu.step = (float)atof(tb); if (!klb_finite(klfk_hu.step) || klfk_hu.step < 300) klfk_hu.step = 300; if (klfk_hu.step > 5000) klfk_hu.step = 5000;
        GetPrivateProfileStringA("Fed", "HuntedNear", "2500", tb, sizeof tb, klh_ini); klfk_hu.near_ = (float)atof(tb); if (!klb_finite(klfk_hu.near_) || klfk_hu.near_ < 500) klfk_hu.near_ = 500; if (klfk_hu.near_ > 10000) klfk_hu.near_ = 10000;
        klfk_hu.fire = GetPrivateProfileIntA("Fed", "HuntedFire", 0, klh_ini) != 0;
        klfk_hu.away = GetPrivateProfileIntA("Fed", "HuntedAway", 0, klh_ini) != 0;
        klfk_hu.dry = GetPrivateProfileIntA("Fed", "HuntedDry", 0, klh_ini) != 0;
        klog("fedkit: Hunted=1 Range=%.0f Alert=%.0f Delay=%lu ms Gap=%lu s Away=%d%s: while you are a fed, a crew bot that loses health with you within Range is ordered (the soldier's own order, as the escort's) to one of the level's cover places [Hops] after Delay ms, the bots within Alert of it after it; at most one order per bot per Gap; needs [Hops] in the level's KLJoin.ini (kl_fa_bots_rt.py hops); a GUESS that this makes them react faster: re/bots_active.md 3",
             klfk_hu.range, klfk_hu.alert, klfk_hu.delay, klfk_hu.gap / 1000, klfk_hu.away, klfk_hu.dry ? " DRY RUN (HuntedDry=1: nothing is ordered)" : "");
        if (klfk_hu.fire) klog("fedkit: HuntedFire=1: the bot that was hit walks %.0f at you (Step) until it is %.0f from you (Near): the soldier's own order to a point on the line to you; ASSUMED that a bot that walks at an enemy sees and shoots him (no target is handed over: no game routine for that was found); the bots near it take a cover place or a step of %.0f aside (Pace)", klfk_hu.step, klfk_hu.near_, klfk_hu.pace);
    }
    klog("fedkit: on; Hunt=%d Crosshair=%d (two bytes of the Arcade rules object, only while you are a fed in play) Body=%d (the level's [FedBody]) AkChance=%d AkItem=%d KitSettle=%d (game calls, once per fed); only on a level that is not the stock one of its slot",
         klfk.hunt, klfk.cross, klfk.body, klfk.ak, klfk.akitem, klfk.settle);
    klog("fedkit: NoTraitor=%d (your kills of the crew leave no traitor flag and cost nothing) Pay=%d PayKill=%d (0 = multiplayer's own number for a policeman who kills a criminal; kept in your total)%s HudFade=%d (1 = the list and the name block never lie on each other while you are a fed, 2 = for a heister too); data only",
         klfk.notraitor, klfk.pay, klfk.paykill, GetPrivateProfileIntA("Fed", "Pay", 1, klh_ini) && !klfk.notraitor ? " - Pay is OFF without NoTraitor" : "", klfk.fade);
}

#endif /* KLFEDKIT_C */
