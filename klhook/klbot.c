/*
 * klbot.c - the AI heisters of an Arcade round: a log of the crew records, and four things the owner asked for
 * ('want them to be able to backstab you and also pay the driver and leave without you or blow the van up or help
 * you up', 2026-10-10). Part of KLHook (included by klhook.c, SHIP and TEST alike). Heap data writes, and ONE call
 * of a game function from the game's own thread (the van, section 5, off unless asked for); no code byte changes.
 * Research: re\bots_behaviour.md, re\bots.md 5, re\bots_review.md. Everything below was read again in kl2.exe build
 * 0490 for this file (debug\dasm.py, 2026-10-10); where this file differs from those notes it says so.
 * NOTHING HERE HAS RUN IN THE GAME. Every part is OFF unless its key in [Bots] is set, and does nothing outside an
 * Arcade round.
 *
 * 0. WHERE THE GAMEPLAY PARTS ACT (re\hook_review_1010.md B1)
 *    Tune, Backstab, Bribe, Leave and Van change the rules of the round. klsteam.c's SHIP policy passes stats,
 *    achievements and the leaderboard upload on when the level's archive is the stock one, so a round under changed
 *    rules on stock Subway (which has an AI crew of its own) would go to the real board. Therefore these five act
 *    ONLY while the level that runs is NOT the stock level of its slot: klsteam.c's klx_level_verdict == 2, the very
 *    verdict under which every Steam write of the round is blocked. The same in the TEST build. Not on verdict 1
 *    (stock), not on 3 (archive not seen), and not at all when the Steam write guard is not on (no archive is
 *    judged then). One line says which, per round object. The Log part reads only and runs on every level.
 *
 * 1. THE OBJECTS (EXE = read in the disassembly)
 *    Arcade test = the game's own 0x7f6850: session = [0x168e598], [session+0x5c] == 4 and [session+0x54] not 2 / 3
 *    (jump table 0x7f6874). The round runs while [session+0x70] == 0x19 (the boarding rule 0x6840a0 and the kill
 *    rule 0x704610 do nothing in any other state): the hook ACTS only then. EXE.
 *    rules = [[0x168e9e4]+0x54], vtable 0xbd3514 (ZGameRulesHeist). EXE (0x508ef0, 0x7bb2a0).
 *      +0x348 crew records, 0x7c bytes each     +0x34c one byte per record, 0 = in use     +0x354 their number
 *      +0x1d8 float, seconds the escape vehicle still waits (counted down by slot 195 = 0x55ec70)
 *      +0x1dc byte, the vehicle's state: 1 / 2 driving in, 3 / 4 WAITING (can be boarded), 5 driving out,
 *             6 destroyed, 7 next vehicle / end; in 3 / 4 a timer at 0 -> slot 194 (5) = it drives off (0x55ed60)
 *      +0x1e0 the object whose place is the boarding point (0x5aeb00)      +0x1e4 the vehicle
 *      +0x1e8 who damaged the vehicle (set by slot 33 = 0x4d8a30)
 *      +0x1b2 byte 'somebody holds the driver'     +0x1b3 byte, crew index of who paid the driver, 0xff = nobody
 *             (read by ONE place of this class: slot 129 compares it with 0xff; reset to 0xff by 0x55ee62)
 *      +0x250 + 4 * i  a counter of slot 182 (0x4a4020), raised by the pay rule
 *      +0x33c byte, written by 0x4322f0 (below)      +0x884 + 4 * i  float 'damage the player did to crew member i'
 *      +0x5f8 the score object: +0x45 byte Arcade level (every reader clamps it to 1..11), +0x150 + 4 * i money
 *    A crew record:
 *      +0x00 pointer to a small client block (byte 0 'not local', byte 1 the index; 0x5c3b10, 0x704649)
 *      +0x04 the actor, for an AI member (0x78f470 finds a bot's record by it)
 *      +0x10 status byte: 0 = in play (0x4906b0 counts these as 'criminals left'), 4 = ABOARD (set by the boarding
 *            rule 0x6840a0 for players and actors alike), 7 = dead (0x48581d, 0x7046aa); 1 and 3 exist, not read
 *      +0x78 heist stage 0..3 (1 entered the bank, 2 left it, 3 at the vehicle; raised by 0x5dd890)
 *      +0x79 flags. THE BITS, settled here (re\bots_review.md asked): MASK 1 = 'an AI crew member' (0x78f4b1
 *            `test byte [edx+0x79], 1` in the routine that looks a bot's record up; 0x6a121b the same), MASK 2 =
 *            'this bot has turned traitor' (0x488ecd `or byte [eax+0x79], 2` in ZBecomeTraitorTactic's run;
 *            0x8826b6 `shr bl, 1 / and bl, 1` in the soldier's friend-or-enemy test). re\bots_behaviour.md calls
 *            them 'bit 1' and 'bit 2' counting from one; re\bots.md 5.1's masks are right.
 *    Local player = [gamedata + 0x828 + 4 * (char)[gamedata + 0x898]], gamedata = [0xdd265c]; feet = 3 floats at
 *    player+0x460 (kljoin.c); in Arcade his crew index is 0 (0x7af9d0 returns 0 there).
 *
 * 2. THE LOG (key Log; the measuring instrument for every live check of the bots)
 *    Once a second while the rules object is ZGameRulesHeist, one line with every crew record in use:
 *        bots: L3 s19 van 3 6.2s | 0 you in-play g1 $120000 | 1 bot in-play g1 $45000 | 2 TRAITOR aboard g3 $800000
 *    L = Arcade level, s = session state (hex), van = vehicle state and its timer, g = heist stage. Log=1 writes
 *    the line when something in it changed and at least every 10 s; Log=2 every second, with the damage float.
 *    A record's first appearance and every change of status / stage / traitor flag is also said in words.
 *
 * 3. BACKSTAB
 *    The game has it for Arcade bots: ZBecomeTraitorTactic (evaluate 0x79b7c0, run 0x488eb0). Per Arcade level L a
 *    record R = [0x168d7c0] + 0x6ac + L * 0x70 of the tuning object (a heap object without a vtable: its first
 *    byte is a bool variable, 0x52407d). A bot turns traitor when ALL hold (EXE):
 *      - 0x43ffb0: [rules+0x338] < int [R+0x6c], and a roll under 0.05 (levels 1-2), 0.10 (3-5), 0.30 (6-7),
 *        0.40 (8-11) - constants in .rdata, not writable. [rules+0x338] is never raised (the increment at 0x432310
 *        sits behind `or edi, ecx / jne` with edi = 1 << index, never zero), so [R+0x6c] is a switch: 0 = never;
 *      - stage term + bot money term + player money term >= float [R+0x20] (0x46d4d0), with
 *        stage term float [R+0x24 + 4 * stage of the BOT], bot term float [R+0x40..0x4c] by its money against the
 *        ints [R+0x34..0x3c], player term float [R+0x5c..0x68] by the local player's money against [R+0x50..0x58].
 *    Its run sets record +0x79 |= 2 and calls 0x4322f0 (which only does [rules+0x33c] &= 1 << index).
 *    A bot with mask 2 no longer counts the player as a friend (0x882715), and neither does a bot whose damage
 *    float [rules+0x884+4*i] is over max(float [R+0x18], 25.0) (0x6a1c40): shoot a bot enough and it turns on you.
 *    STOCK VALUES (from re\bots_behaviour.md 1.3, b-behave's emulation of the constructor - NOT re-derived here;
 *    the hook logs the table it finds, once, so the first live run settles it): [R+0x6c] = 0 on levels 1-3, 1 on
 *    4-5, 2 on 6-8, 3 on 9-10, 4 on 11; limit 7.0 everywhere; stage terms 0 / 0 / 2 / 3; money terms 0..3 for the
 *    bot (more = likelier) and 3..0 for the player (poorer = likelier); money limits 750,000 / 1,000,000 /
 *    1,250,000 (levels 10-11: 100,000 / 250,000 / 750,000); [R+0x18] = 100 90 80 70 60 40 25 25 25 25 25.
 *    So in stock a bot can never betray on levels 1-3, and later only with 7 of 9 points.
 *    WHAT THE HOOK DOES
 *    a. Tune=1 (H1, data): while an Arcade session is up, [R+0x6c] = max(stock, Traitors) (or exactly
 *       Traitors.<L>), [R+0x20] = Limit (or Limit.<L>), [R+0x18] = Retaliate when that key is not 0. The stock
 *       values are kept and written back when the session is no longer Arcade. Defaults Traitors=1, Limit=6.0:
 *       betrayal becomes possible on every level but still needs e.g. a bot at the vehicle (3) with over
 *       1,000,000 (2) and a player under 1,250,000 (1) - plausible, not certain. The table is only written when
 *       all eleven records look like the table (klb_tune_ok): the object has no vtable to check.
 *    b. Backstab=<percent> (H2, data): at the start of a round, with that chance, ONE bot is picked. When it is in
 *       play, has reached stage BackstabStage and carries BackstabMoney or more, and the player is in play, for
 *       BackstabDelay seconds: record +0x79 |= 2 and [rules+0x33c] &= 1 << index - exactly what the tactic's run
 *       leaves behind. The game clears the flag at the next round start (0x817d20).
 *    NOT ESTABLISHED: whether a traitor bot also fights the other bots; whether anything announces it (the tactic
 *    does not call the 'make traitor' rule). The log line is the only sure sign.
 *    d. THE MOMENT OF THE TURN (2026-10-11, track O; NOT RUN IN THE GAME; re\bots_fight.md 3). The owner: 'i saw one
 *       backstab me it was too lenient i could get away with killing him'. Once b's own conditions have held for
 *       BackstabDelay seconds the turn can wait for a moment that is bad for YOU: BackstabNear=<units> (the bot is
 *       within that many world units of you, 100 = 1 m), BackstabBehind=1 (it is more than 90 degrees off the way you
 *       face), BackstabBusy=1 (your health is under 97 % of its maximum = you were hit within the regeneration time).
 *       All that are set must hold at once; BackstabWait seconds (default 30) after the delay was FIRST over the bot
 *       turns at the next pass in which b's conditions hold, moment or not (the wait is not started again when they
 *       lapse). With none of the three set the turn is what it was. Reads only (klb_moment); the write is b's.
 *       BackstabBehind is a GUESS about where you LOOK: the vector at player+0xc14 is your direction of TRAVEL (seen
 *       live), so a player who backs away or strafes is judged wrongly; the camera's direction is not known to the hook.
 *    e. TraitorsMax=<n> (needs Tune=1; 0 = no cap, the default). SEEN in the owner's own rounds of 2026-10-11 (his
 *       KLHook.log 12:36 and 12:43, Tune=1 Traitors=1 Limit=6.0): FOUR bots carried the traitor flag in one round and
 *       two in the next, all set by the game's own tactic at the vehicle - 'traitors allowed' is a switch, not a count
 *       (above: [rules+0x338] is never raised). While n or more bots carry the flag the hook writes 0 into the switch
 *       of every level and puts Tune's number back when fewer do (the game clears the flags at the next round start).
 *       A cap PER ROUND, not 'alive at once': a traitor who is dead, aboard or escaped keeps his flag until the round
 *       start and still counts. A soft cap: the tactic can turn two bots between two passes of the hook (100 ms).
 *    f. TRAITORS ARE EVERYBODY'S ENEMY (2026-10-14, track w_betray; NOT RUN IN THE GAME). The owner: 'AI heisters also
 *       need to betray each other, and also shoot one if they do become a traitor, so someone could save the player'.
 *       WHY A MASK-2 BOT FIGHTS ONLY YOU (EXE, read for this): mask 2 is read in ONE kind of place, the soldier's test
 *       of a PLAYER (0x882470 slot 111: 0x8826b6) and the friendly-player list (0x570a1b). Between two NPCs the game
 *       compares TEAMS, read live from the actor: dword [[actor+0x54]+4] (0 Mercenary, 1 Enemy = the police,
 *       2 Ally = the crew, 3 Neutral): 0x5706a0 collects as friends the actors within reach whose team equals the
 *       soldier's own (0x5707b6 `mov ecx,[esi+0x54] / cmp [ecx+4],eax`), 0x59a5d0 the same for the squad list. A
 *       traitor bot stays team 2, so the loyal crew sees a friend and he sees friends. LOG (owner, 2026-10-14
 *       20:29:11): 'BACKSTAB: bot 7 ... turned traitor'; 20:29:41 'YOU ARE DOWN', 'record 0 (you): status1' - nobody
 *       stopped him; records 1..6 stayed 'bot' and went on with their work.
 *       TraitorFoe=1: a bot that carries mask 2 (the tactic, Backstab, BackstabCrew below or Bribe) and is IN PLAY
 *       gets team 1 (Enemy, the police's) written into [[actor+0x54]+4]; the 2 goes back the moment he is dead,
 *       aboard or anything but in play, when the mask goes, when the round state leaves 0x19 and before anything
 *       else is done with that record. Only when: the dword reads 2, the actor is a ZFFActor (0xbb3bac), and the
 *       object at actor+0x54 belongs to him alone (no other crew actor and not the local player point at the same
 *       one - klbotdown.c writes its per-bot 'no damage' word +0x3a in the same object, live, one bot at a time).
 *       EXPECTED (a GUESS, settled by check K7): the loyal bots and the escort see an enemy as they see a policeman
 *       and shoot him; he sees the crew and you as a policeman does (0x882636: a team-1 soldier counts the player
 *       as a target) and shoots whoever is near, crew with money included; the police leave him alone (he is on
 *       their team now); your HUD tag of him is red (0x8e9e2c: the crew's view paints team 1 red).
 *       THE KILL BOOKKEEPING (EXE, read for this - the reason the mark below is NOT optional): a crew member killed
 *       by a crew member is booked by 0x6706b0 (from slot 16 = 0x485740), for a BOT killer too (0x670779: a ZFFActor
 *       killer is looked up by 0x78f470). When the victim carries no bit 1 in its score dword ([score+0x1d4+4*i])
 *       and slot 122 (a yellow card) does not excuse the killer, slot 129 = 0x8fb0d0(killer, victim) runs - and that
 *       rule marks THE LOCAL PLAYER (0x8fb1b9 .. 0x8fb1ca, 0x70f770: [player+0x2726] = 1, every bot's enemy) unless
 *       the KILLER already carries bit 1 (0x8fb19c `test byte [score+killer*4+0x1d4],1 / jne` = it returns). So a
 *       turned bot that kills a loyal one would make YOU the traitor, and a loyal bot that kills the turned one the
 *       same. Therefore TraitorFoe also sets bit 1 of the turned bot's score dword (what klgrudge.c's BackstabMark
 *       writes), from the pass that sees the mask: his kills and his death book nobody else (0x6709f4 and
 *       0x8fb19c). Taken off when the mask goes (the next round start), so it stays on a dead / escaped one to the
 *       round's end. SIDE EFFECTS, as BackstabMark: an escaped marked bot keeps his own money and is out of the
 *       split (0x796576); the damage sum 0x4d17f0 counts no more hits of yours on him (Grudge / YouToCrewFar).
 *       Killing him as the human with the mark on: no traitor flag for you (the point of it).
 *       NOT KNOWN: whether the AI's knowledge system keeps an old 'friend' entry until the traitor is seen again
 *       (0x4801a0 refreshes what every knower sees of an entity when a PLAYER turns; nothing such is called here);
 *       whether a team-1 bot can still loot or board (0x626fb2 / 0x6fb767 test team 2 - probably NOT: a turned bot
 *       then stays outside, which only matters for a tactic traitor at the vehicle); the damage factors for him
 *       are the police's (0x7c1bf3 / 0x8b80a3 pick the crew's by team 2: klbalance.c's CopToCrew / player->police).
 *    g. BackstabCrew=<percent> (needs TraitorFoe=1; AI against AI): once a round, with that chance, ONE bot (not the
 *       Backstab pick) is picked. When it is in play at BackstabStage or later and ANOTHER loyal bot in play carries
 *       BackstabMoney or more within BackstabCrewNear (world units, default 1500 = 15 m), for BackstabDelay seconds,
 *       it turns (b's writes; you need not be in play) and f makes him the crew's enemy: he shoots the one with the
 *       money - or whoever is nearer: who he aims at is the game's choice. What the victim carried lies where he
 *       fell as in stock; the hook does NOT hand it to the traitor (a team-1 bot may not be able to pick it up: f).
 *    h. TraitorKillMax=<n> (default 2; 0 = off, the old behaviour; needs TraitorFoe=1; 2026-10-18, overnight audit: Vault round 2, one traitor with $1.28M killed 5
       crewmates in 22 s and the round was dead for the fed). klb_foe_tick already sees every death of a record that was in play on the pass before; when a team-Enemy
       traitor was within TraitorKillNear (3000 = 30 m) of a LOYAL AI heister that died, the death is booked to the NEAREST traitor (the killer is not read: a
       policeman's kill beside him counts too, so the cap errs towards sparing the crew). At n booked deaths that traitor's team goes back to 2 (klb_foe_back, the
       path that already runs at his death) and TraitorFoe does not swap him again (refused[]); he keeps the mask and the score bit, so the human still fights him
       and he still fights the human. A new mask (next round) starts at 0. NOT RUN IN THE GAME: log 'TRAITOR CAP:'.
    A HUMAN TRAITOR needs nothing new: the game's own mark ([player+0x2726], slot 129) makes every bot fight him
 *    (0x882708); with TraitorFoe the turned bots fight him as well (team 1 against a player).
 *
 * 4. PAY THE DRIVER AND LEAVE WITHOUT YOU
 *    The player's rule is ZGameRulesHeist slot 149 = 0x757510(index): slot 151 (0) -> [rules+0x1b2] = 0;
 *    [rules+0x1b3] = index; slot 182 -> ++[rules+0x250+4*index]; money -= money >> 1; slot 129 (index, -1) 'make
 *    traitor'; [rules+0x1d8] = 0.0; announcement 0x65c620. EXE, every step.
 *    THE RULE IS NOT CALLED FOR A BOT, AND MUST NOT BE (this is where this file differs from re\bots_behaviour.md
 *    2.4 A and re\bots.md H3): slot 129 = 0x8fb0d0 marks, whatever index it is given, the LOCAL PLAYER:
 *        0x8fb1b9  mov ecx, [0xdd265c] / push 1 / push 0 / call 0x660b00 / mov ecx, eax / call 0x70f770
 *    0x70f770 writes byte [player+0x2726] = 1 and tells the AI's knowledge system (0x4801a0). That byte is 'this
 *    player is a traitor': the soldier's friend test 0x882708 and the friend list 0x5709af both drop the player
 *    when it is set. In stock Arcade only the player ever reaches slot 129 (index 0), which is why the bots' own
 *    tactic sets record mask 2 instead. Called with a bot's index it would make EVERY bot the player's enemy -
 *    the player, not the bot, would be the traitor - and it faults if there is no local player (no null test).
 *    So the hook does the rule's steps as DATA, with the bot's own traitor mark in the place of slot 129:
 *    c. Bribe=<percent> (H3): a bot that has been aboard (status 4) for BribeDelay seconds with BribeMoney or
 *       more, while the vehicle waits (state 3 / 4) and the player is in play and NOT aboard: with that chance,
 *       once per bot and vehicle: [rules+0x1b2] = 0, [rules+0x1b3] = index, ++[rules+0x250+4*index], money -=
 *       money >> 1, record +0x79 |= 2, [rules+0x1d8] = 0.0. The vehicle then drives off at the game's next step.
 *       NOT done: the announcement 0x65c620 (it picks a speaker through 0x5977b0, not read to the end) - so
 *       no 'driver bribed' text or voice; the log line and the vehicle leaving are the signs.
 *       SIDE EFFECT (re\hook_review_1010.md B4; stock has the same window after the player's own bribe):
 *       [rules+0x1b3] stays the bot's index until slot 195 resets it at the next vehicle (0x55ee62). While it is
 *       not 0xff, slot 129 skips its guards (flags 1 / 0x20 / 0x40 of the caller, the announcement 0x67ee80) and
 *       goes straight to 0x8fb193: a player who shoots a crew member in that window is marked traitor without the
 *       usual announcement.
 *    d. Leave=<percent> (H4): every bot still in play is aboard, at least one is, the vehicle waits, and the
 *       player is in play, not aboard and FAR: farther than LeaveDistance (world units, 100 = 1 m) from the
 *       boarding point, for LeaveDelay seconds: with that chance, once per vehicle, [rules+0x1d8] = 0.0. The same
 *       write the game makes itself when the last criminal boards (0x6841b1) or the van is 'heavily damaged'.
 *       Boarding point = the place of [[rules+0x1e0]+4], a scene node: nine floats at +0x00, position at +0x24,
 *       parent at +0x50, composed up the chain with the arithmetic of 0x7b3020 (0x6be1c0: x' = x*m6 + y*m3 +
 *       z*m0 ..., then 0x42a4d0 adds the position) - computed from data, no call. When it cannot be read,
 *       'far' = the player's own stage is under 3.
 *    Stock already leaves without you: the vehicle waits 8 s on the stock maps (10 s for a spline car), 5 s more
 *    if held, and goes at once when nobody is left in play. c and d shorten that wait; they add no new ending.
 *
 * 5. BLOW THE VAN UP (H5, the ONE game call; key Van, default 0)
 *    ZGameRulesHeist slot 94 = 0x6a1100(grade) is what the vehicle's own damage ends in (0x594b10). EXE, whole:
 *      every grade: [score+0x60] = grade (0x6a1114; grade 0 then returns);
 *      grade 1 'heavily damaged': announcement 0x764f60, and in state 3 / 4 the timer = 0;
 *      grade 2 'destroyed', in states 1..5: slot 194 (6); every record with status 4 loses its money (0x544550)
 *        and is killed - an AI member through slot 16 = 0x485740(actor, 0x6ece90([rules+0x1e8])), a player through
 *        slot 11 = 0x704610(player, [rules+0x1e8]); announcements.
 *    It takes no crew index, so the question 'is it safe for an AI member' does not arise; it is called exactly
 *    as the game calls it, on the game's thread, after its first 16 bytes and the vtable slot were compared.
 *    Van=1 or 2 = the grade. When: a TRAITOR bot (mask 2) in play at the vehicle (stage 3) while it waits and
 *    somebody is aboard; with VanLeftBehind=1 also any bot in play at stage 3 while the vehicle drives out
 *    (state 5) with somebody aboard. For VanDelay seconds, then VanChance percent, once per vehicle.
 *    ASSUMPTIONS, said plainly:
 *      - [rules+0x1e8] may be null when the hook calls (nothing has shot the van). 0x6a11c9 tests it and
 *        0x6ece90 -> 0x86ca10 takes a null; what slots 11 and 16 do with a null killer further in was NOT read to
 *        the end. So for GRADE 2 ONLY (grade 1 never reads the field), when it is null, the hook writes the bot's
 *        actor there, calls, and writes the null BACK when the call has returned (re\hook_review_1010.md B2): the
 *        field is a raw pointer without a reference count (slot 33 = 0x4d8a30 `mov [ecx+0x1e8], eax / ret 4`) that
 *        the game follows later with no test of its own (0x6a11cd -> 0x7aace0 `mov eax,[ecx] / call [eax+0x30]`),
 *        so a pointer left behind would be called through after the actor is gone.
 *      - the code the pointer is handed to expects an ENTITY: 0x7aace0 calls its vtable slot 12 with no argument,
 *        0x86ca10 takes [obj+4] as a pointer into the entity pool. The actor of a crew record is taken to be a
 *        ZFFActor (vtable 0xbb3bac, the class's only one; its slot 12 = 0x557ba0 `mov eax,[0x1547b24] / ret`,
 *        the same kind of getter as ZFFPlayer's 0x4a7c60). NOT PROVEN that record +4 is one: the hook REQUIRES
 *        that vtable before the write and the call, for both grades (B3), and the log's 'record N appears' line
 *        prints the actor's vtable so that check K1 settles it before Van is ever switched on.
 *      - the bot's place is not known to the hook (an actor's position is only reached through virtual calls),
 *        so 'at the vehicle' is the game's own stage 3, not a distance.
 *      - whether the level's crash sequence plays (it is started by the vehicle's own damage, which did not
 *        happen) and what a spline car / helicopter of a Dead Men map does in state 6: NOT established. Try
 *        Retomoto (baked vans) first, grade 1 before grade 2.
 *
 * 6. HELP YOU UP - NOT IMPLEMENTED, because the code does not support it in Arcade. Read for this file:
 *      - ZHealTactic's evaluate 0x64ed60 looks for a LOCAL PLAYER whose state object [player+0x2940] has
 *        [+0x24] == 5, within a distance (0x64ee52..0x64ee75), and reserves him (0x47c110 -> state 6);
 *      - that object's state machine is 0x5fe270 (Dead Men's adrenaline shot). State 5 'waiting for a healer'
 *        is entered from state 4 only (0x5fe474), and state 3 goes to 4 ONLY when 0x87c980 is true =
 *        [session+0x5c] == 2; in every other mode it goes to 8 (0x5fe36e..0x5fe381). Arcade is mode 4.
 *      So in Arcade the tactic never finds anybody: giving the bots a HealTactic (kl_fa_bots --heal, ZSoldier
 *      field 2) cannot do anything, whatever the tuning byte [[0x168d7c0]+5] says (0x6ab6b4; its default was
 *      not looked up - it no longer matters).
 *      - `?Resurrect@ZFFPlayer@@QAEXPAVZGEOM@@_N1@Z` is NOT an export of kl2.exe (513 exports, none of that name;
 *        the text at 0xbb4540 is part of the RTTI name CEG_ForceRefClass_ZFFPlayer_Resurrect): the function
 *        has no fixed named address and belongs to Steam's CEG (re\antitamper.md). The hook does not look for it.
 *      Forcing the player's state machine to 5 from outside would be new behaviour written into a machine that
 *      was not read (states 4..15), not a switch: not done.
 *
 * TESTED OFF-GAME ONLY (2026-10-10; scratch program klbot_test.c, this file included as it is, a made-up session /
 * rules object / crew records / tuning table / scene nodes in the test's own memory, a made-up damage rule): the
 * log, the distance, the tuning written, restored and refused on a table that looks wrong, the backstab's stage /
 * money / delay, the bribe's six writes, the leave, the van call once per vehicle and refused when the code bytes
 * differ, nothing written off the game's thread (the tuning excepted: plain values, written from either thread),
 * outside Arcade or on another rules class; since the review (re\hook_review_1010.md) also: nothing but the log
 * on a stock level, on a level whose archive was not seen and with the Steam guard off; the tuning taken back when
 * the level turns out stock; the attacker written for grade 2 only and taken back; the call refused for an actor
 * that is not a ZFFActor; no second call for one vehicle when a stage drops. That proves this file's own logic and
 * nothing about the game.
 *
 * KLHook.ini
 *   [Bots]
 *   Enable=0            1 = this file is on (then only the log; every part below has its own key)
 *   Log=1               0 none, 1 on change and every 10 s, 2 every second + every loss of a bot's health in words
 *   Tune=0              1 = write the traitor tuning: Traitors=1 Limit=6.0 Retaliate=0 (0 = stock) and per level
 *                       Traitors.<1..11>= Limit.<1..11>=
 *                       TraitorsMax=0 (with Tune: at most that many bots turn traitor in a ROUND - dead ones count; 0 = no cap)
 *   TraitorKillMax=2    (needs TraitorFoe=1; section 3 h) a turned bot booked with that many crew deaths within TraitorKillNear=3000 units goes back to
 *                       team Ally (he stops shooting the crew; the mask stays, the human is still his target). 0 = no cap (the old behaviour). 2026-10-18.
 *   Backstab=0          percent per round that one bot is picked; BackstabStage=2 BackstabMoney=250000 BackstabDelay=20
 *                       the turn then waits for BackstabNear=0 (units) / BackstabBehind=0 (by your direction of travel: a guess) /
 *                       BackstabBusy=0, BackstabWait=30 s at most
 *   TraitorFoe=0        1 = a turned bot in play is team Enemy (the crew and the escort shoot him, he shoots them) and carries
 *                       the score table's traitor bit (section 3 f; a GUESS until K7)
 *   BackstabCrew=0      percent per round that one bot turns on a crewmate with BackstabMoney within BackstabCrewNear=1500 units
 *                       (needs TraitorFoe=1; section 3 g)
 *   Bribe=0            percent per bot aboard; BribeMoney=500000 BribeDelay=4
 *   Leave=0             percent per vehicle; LeaveDistance=4000 LeaveDelay=3
 *   Van=0               0 off, 1 'heavily damaged', 2 destroyed; VanChance=50 VanDelay=5 VanLeftBehind=0
 *   Tune / Backstab / Bribe / Leave / Van act only on a level that is not the stock one of its slot (section 0).
 *
 * LOG (every action is one line; the lead's live checks, in this order)
 *   K0  Enable=1 only, any Arcade round: 'bots: Arcade round object ...', the stock tuning table (11 lines), the
 *       line a second. On a stock map WITHOUT bots: one record 'you'. This check also proves the offsets.
 *   K1  a b_bots build: do records 1..7 say 'bot', do stages rise (g1 in the bank, g3 at the vehicle), does
 *       money rise, 'aboard' when they get in. Answers B3 / B4 / B7 of re\bots.md. And: every 'record N appears:
 *       bot' line must end in 'actor's vtable 00bb3bac = ZFFActor' - anything else and Van refuses (keep it off).
 *   K2  Tune=1 on a map that is NOT stock: 'bots: this level is not the stock one ...: Tune ... may act', then
 *       'bots: tuning written for 11 levels ...'; play until a bot stands at the vehicle with money:
 *       'bots: record N: traitor flag SET (flags 01 -> 03)' with no BACKSTAB line before it (= the game's own tactic) and the bot shoots you. Back in the menu: 'bots: stock tuning restored'.
 *   K3  Backstab=100 BackstabDelay=5 BackstabMoney=0 BackstabStage=1: 'bots: BACKSTAB: bot N ...' some seconds
 *       after the bots entered the bank; then: does it shoot you, do the others shoot it.
 *   K4  Bribe=100 BribeMoney=0, stay away from the vehicle: 'bots: BRIBE: bot N pays the driver ...' and the
 *       vehicle state goes 3 -> 5 in the next line; the bot's money is halved.
 *   K5  Leave=100, stay far away while all bots board: 'bots: LEAVE: every bot is aboard and you are N m away ...'
 *   K6  Van=1 VanChance=100 Backstab=100 (a traitor is needed): 'bots: VAN: ... grade 1' and the vehicle leaves;
 *       only then Van=2: '... grade 2', 'returned 1; vehicle state 6', everybody aboard dead.
 *   K7  TraitorFoe=1 Backstab=100 BackstabDelay=5 BackstabMoney=0 BackstabStage=1 (TraitorsMax=1 with Tune=1, so ONE
 *       turns): 'bots: BACKSTAB: bot N', then 'bots: FOE: record N (TRAITOR) is team Enemy now ... score bit 1 set'.
 *       WATCH: do the loyal bots / the escort shoot him (botdown / adren lines 'record N ... IS DOWN' for him; 'bots:
 *       FOE: ... died' lines), does he shoot them, do the police ignore him. When he is dead: 'FOE: record N: team
 *       2 back'; NO 'YOU ARE THE TRAITOR' / 'traitor flag' line for record 0. Round over: no 'team ... back' missing.
 *       If the loyal bots do NOT shoot him: the team is not read live for targets (3 f, NOT KNOWN) - keep TraitorFoe off.
 *   K8  K7 + BackstabCrew=100 Backstab=0: 'bots: backstab-crew: bot N may turn on a crewmate ...', then 'BACKSTAB-CREW:
 *       bot N turned on record M ($.., .. m away)' and the FOE lines.
 *   K2..K6 on a STOCK level say 'bots: this level is the STOCK one ...: Tune / Backstab / Bribe / Leave / Van do
 *   nothing here' once and then only the log lines: that is the gate of section 0, not a fault.
 *   Steam write guard on for all of them (klsteam.c; without it nothing but the log runs), do not Quit inside a session.
 */
#ifndef KLBOT_C
#define KLBOT_C

#define KLB_SESSION   0x0168e598              /* +0x54, +0x5c = mode (4 = Arcade), +0x70 = state (0x19 = round runs) */
#define KLB_SETTINGS  0x0168e9e4              /* +0x54 = the rules object */
#define KLB_TUNING    0x0168d7c0              /* the tuning object (heap, no vtable) */
#define KLB_RULES_VT  0x00bd3514              /* ZGameRulesHeist */
#define KLB_DAMAGE    0x006a1100              /* its slot 94 (grade) */
#define KLB_ACTOR_VT  0x00bb3bac              /* ZFFActor (its only vtable; slot 12 = 0x557ba0, a no-argument class getter) */
#define KLB_RULES_SV  0x00bd2eb4              /* ZGameRulesFragileAllianceSv (online host) */
#define KLB_RULES_CL  0x00bd31e4              /* ZGameRulesFragileAllianceCl (online client) */
#define KLB_NREC      32                      /* the money array at score+0x150 has room for 33 */
#define KLB_NLEVEL    11
#define KLB_ROUND     0x19
#define KLB_T(t)      ((t) ? (t) : 1)     /* a time stamp that is never 0 (0 = 'not running'); NOT t | 1, which can lie 1 ms ahead */

/* klsteam.c is included after this file (klhook.c): what section 0 needs of it */
static int klx_on;                                                   /* the Steam write guard is installed */
static int klx_level_verdict(const char *scene, char *why);          /* 0 no level, 1 stock, 2 not stock, 3 not known; why[200] */

static struct {
    int on, log, tune, traitors, trl[KLB_NLEVEL + 1]; float limit, liml[KLB_NLEVEL + 1], retaliate;
    int backstab, bs_stage, bs_money, bs_delay;
    int tr_max;                               /* TraitorsMax: 0 = no cap (section 3 e) */
    int tr_kills; float tr_kill_near;         /* TraitorKillMax / TraitorKillNear (section 3 h) */
    int bs_behind, bs_busy, bs_wait; float bs_near;      /* the moment of the turn (section 3 d); all 0 = as before */
    int bribe, br_money, br_delay;
    int leave, lv_delay; float lv_dist;
    int van, van_chance, van_delay, van_left;
    int foe, foe_fed, bs_crew; float bs_crew_near;     /* section 3 f / g: TraitorFoe, BackstabCrew, BackstabCrewNear */
} klb;

struct klb_rec { int used; DWORD at, actor, money; BYTE status, stage, flags; float hit; };
struct klb_snap {
    DWORD rules, score, state, vehicle; int n, level, human; BYTE veh; float timer;
    struct klb_rec r[KLB_NREC];
    int online;                               /* 1 = filled by klb_read_hud() from an ONLINE rules object (host/client): rules + state only, n = 0, score = 0 */
};

static struct {                               /* what the hook remembers of the round and of the vehicle now waiting */
    DWORD rules, state, round_at; int cand, backstabbed, stages; DWORD cand_since;      /* cand: -2 not rolled yet, -1 nobody */
    DWORD wait_since;                         /* section 3 d: BackstabDelay was first over (the wait for the moment runs from here and is NOT started again) */
    BYTE veh; DWORD aboard_at[KLB_NREC]; char rolled[KLB_NREC]; int bribed;
    DWORD leave_since; int leave_rolled; DWORD van_since; int van_rolled;
    int ccand, cdone; DWORD csince;           /* section 3 g: BackstabCrew's pick (-2 not rolled yet, -1 nobody), done, held since */
} klb_r;
static DWORD klb_seed;

static int klb_roll(int percent)
{   /* our own generator: the game's (sysif+0xb30) is not touched */
    klb_seed = klb_seed * 1103515245u + 12345u;
    return (int)((klb_seed >> 16) % 100u) < percent;
}

static int klb_finite(float f) { return f == f && f > -1e9f && f < 1e9f; }

/* ---------------------------------------------------------------- reading the round */

/* -> 1 and *s when an Arcade session with a ZGameRulesHeist object is up (whatever the session state) */
static int klb_read(struct klb_snap *s)
{
    DWORD sm, gs, recs, freeb, sub = 0, n = 0; BYTE raw[0x7c], b = 0; int i;
    memset(s, 0, sizeof *s); s->human = -1;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLB_SESSION))) || klh_rd32(sm + 0x5c) != 4 || !klh_rd(sm + 0x54, &sub, 4) || sub == 2 || sub == 3) return 0;
    if (!klh_rd(sm + 0x70, &s->state, 4)) return 0;
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLB_SETTINGS))) || !(s->rules = klh_rd32(gs + 0x54)) || klh_rd32(s->rules) != KLB_RULES_VT) return 0;
    if (!klh_rd(s->rules + 0x354, &n, 4) || !n || n > KLB_NREC) return 0;
    if (!(recs = klh_rd32(s->rules + 0x348)) || !(freeb = klh_rd32(s->rules + 0x34c)) || !(s->score = klh_rd32(s->rules + 0x5f8))) return 0;
    if (!klh_rd(s->rules + 0x1dc, &s->veh, 1) || !klh_rd(s->rules + 0x1d8, &s->timer, 4) || !klh_rd(s->score + 0x45, &b, 1)) return 0;
    s->vehicle = klh_rd32(s->rules + 0x1e4);
    s->level = (signed char)b < 1 ? 1 : b > KLB_NLEVEL ? KLB_NLEVEL : b;      /* the clamp every reader in the game applies */
    s->n = (int)n;
    for (i = 0; i < s->n; i++) {
        struct klb_rec *r = &s->r[i];
        if (!klh_rd(freeb + i, &b, 1) || b || !klh_rd(recs + 0x7c * i, raw, sizeof raw)) continue;
        r->used = 1; r->at = recs + 0x7c * i; r->actor = *(DWORD *)(raw + 4);
        r->status = raw[0x10]; r->stage = raw[0x78]; r->flags = raw[0x79];
        klh_rd(s->score + 0x150 + 4 * i, &r->money, 4); klh_rd(s->rules + 0x884 + 4 * i, &r->hit, 4);
        if (!(r->flags & 1) && s->human < 0) s->human = i;
    }
    return 1;
}

/* 2026-10-18, TASK B (re/hud_online.md): [HUD] Online. The owner's HUD may run in a network FA round (private match / online), but ONLY its local,
   cosmetic parts. klb_read stays what it was (Arcade: the AI, balance, fed, crew parts all ask it and must stay Arcade-only). klb_read_hud is
   klb_read, and where that says no, an ONLINE snapshot: the net role 2 (host) / 3 (client), game type 4, a rules object whose vtable is
   ...FragileAllianceSv / Cl. It carries ONLY what the base class ZGameRulesFragileAlliance holds (offsets < 0x334: Sv adds its own from 0x334, Cl
   adds none - ctors 0x79acc0 / 0x6fe090): rules, the session state and the vehicle bytes. n = 0, score = 0: every Heist-only reader (records
   at rules+0x348, ZHeistScore at +0x5f8) then answers 'nothing' by its own vtable test. Reads only. klb_hud_online is set from [HUD] Online by klhud.c. */
static int klb_hud_online;
static int klb_online_session(void)
{
    DWORD sm, role = 0;
    if (!klb_hud_online || !(sm = klh_rd32((DWORD_PTR)KLH_VA(KLB_SESSION))) || klh_rd32(sm + 0x5c) != 4 || !klh_rd(sm + 0x54, &role, 4)) return 0;
    return role == 2 || role == 3;
}

static int klb_read_hud(struct klb_snap *s)
{
    DWORD sm, gs, vt;
    if (klb_read(s)) return 1;
    memset(s, 0, sizeof *s); s->human = -1;
    if (!klb_online_session()) return 0;
    sm = klh_rd32((DWORD_PTR)KLH_VA(KLB_SESSION));
    if (!klh_rd(sm + 0x70, &s->state, 4)) return 0;       /* GUESS: the multiplayer session manager keeps its state at +0x70 like the single-player one (0x6c53db pushes state 0x12 for the load) */
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLB_SETTINGS))) || !(s->rules = klh_rd32(gs + 0x54)) || !klh_rd(s->rules, &vt, 4)) { s->rules = 0; return 0; }
    if (vt != KLB_RULES_SV && vt != KLB_RULES_CL) { s->rules = 0; return 0; }
    s->level = 1; s->online = 1;                          /* veh 0, timer 0, n 0, score 0: the escape dial and every record reader stay silent */
    return 1;
}

/* Section 0: may the gameplay parts act on the level that runs now? -> 1 only when its archive was seen and is NOT
   the stock one (the verdict under which klsteam.c blocks every Steam write of the round); why[200] says which. */
static int klb_level(char why[200])
{
    char scene[160], w[200]; int v;
    if (!klx_on) { strcpy(why, "the Steam write guard is not on, so no level archive is judged"); return 0; }
    if (!klh_scene(scene, sizeof scene)) { strcpy(why, "there is no scene name"); return 0; }
    v = klx_level_verdict(scene, w);
    if (v == 2) { snprintf(why, 200, "this level is not the stock one (%.150s)", w); return 1; }
    if (v == 1) strcpy(why, "this level is the STOCK one of its slot (a round here can go to Steam)");
    else if (v == 3) snprintf(why, 200, "this level is not known (%.150s)", w);
    else snprintf(why, 200, "the scene '%.100s' is no level", scene);
    return 0;
}

/* The local player's feet and the vehicle's boarding point -> distance in world units, or -1 when either cannot
   be read. The point is composed as the game's 0x7b3020 does it: v = M * v + pos for the node and each parent. */
static float klb_distance(DWORD rules)
{
    DWORD gd, pl, obj, node; BYTE sel = 0xff, type = 0; float feet[3], v[3] = { 0, 0, 0 }, m[12], t[3]; int depth;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel > 3) return -1;
    if (!(pl = klh_rd32(gd + 0x828 + 4 * sel)) || !klh_rd(pl + 0x273c, &type, 1) || type != 2 || !klh_rd(pl + 0x460, feet, 12)) return -1;
    if (!(obj = klh_rd32(rules + 0x1e0)) || !(node = klh_rd32(obj + 4))) return -1;
    for (depth = 0; node && depth < 32; depth++) {
        if (!klh_rd(node, m, sizeof m)) return -1;
        t[0] = v[0] * m[6] + v[1] * m[3] + v[2] * m[0] + m[9];              /* 0x6be1c0, then + [node+0x24] */
        t[1] = v[0] * m[7] + v[1] * m[4] + v[2] * m[1] + m[10];
        t[2] = v[0] * m[8] + v[1] * m[5] + v[2] * m[2] + m[11];
        memcpy(v, t, sizeof v);
        node = klh_rd32(node + 0x50);
    }
    if (node || !klb_finite(v[0]) || !klb_finite(v[1]) || !klb_finite(v[2]) || !klb_finite(feet[0]) || !klb_finite(feet[1]) || !klb_finite(feet[2])) return -1;
    return (float)sqrt((v[0] - feet[0]) * (v[0] - feet[0]) + (v[1] - feet[1]) * (v[1] - feet[1]) + (v[2] - feet[2]) * (v[2] - feet[2]));
}

/* ---------------------------------------------------------------- the log (H6) */

static const char *klb_status(BYTE st, char tmp[12])
{
    if (st == 0) return "in-play";
    if (st == 4) return "aboard";
    if (st == 7) return "dead";
    snprintf(tmp, 12, "status%u", st); return tmp;
}

static const char *klb_who(const struct klb_rec *r) { return !(r->flags & 1) ? "you" : r->flags & 2 ? "TRAITOR" : "bot"; }

/* Log=2 (2026-10-11, the Retomoto question 'all seven bots die in the boardroom within 95-150 s, with police->crew at
   the stock 0.01 too'): what each bot's health does, read-only. An NPC's health object is [actor+0x5fc] (set by its
   constructor at 0x8307fb, regenerated at 0x40f24d), the same 0x28-byte object the player keeps at +0xa48 (klbalance.c
   1 d): +0x04 health, +0x08 maximum, +0x24 the owner. A line per loss ('record 3 (bot): lost 0.6 (279.4 of 280.0)') tells
   bullets (many small steps: 60 x 0.01 = 0.6 for a Zastava hit at the stock factor) from a blast, a fall or a kill
   volume (one step to 0); a line at the first sight says the maximum. Nothing is written. */
static int kle_node(DWORD node, float pos[3], float dir[3]);          /* klescort.c (included after this file): a node's world place */
static DWORD hp_rules;
static void klb_health_tick(const struct klb_snap *s, int fresh)
{
    static DWORD obj[KLB_NREC]; static float seen[KLB_NREC], smax[KLB_NREC]; static int said[KLB_NREC];
    int i; float raw[0x28 / 4];
    if (fresh) { memset(obj, 0, sizeof obj); memset(seen, 0, sizeof seen); memset(smax, 0, sizeof smax); memset(said, 0, sizeof said); }
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; DWORD h;
        if (!r->used || !(r->flags & 1) || !r->actor) continue;
        if (!(h = klh_rd32(r->actor + 0x5fc)) || !klh_rd(h, raw, sizeof raw) || ((DWORD *)raw)[0x24 / 4] != r->actor) continue;
        if (!klb_finite(raw[1]) || !klb_finite(raw[2]) || raw[2] < 1 || raw[2] > 100000) continue;
        if (h != obj[i]) {
            obj[i] = h; seen[i] = raw[1]; smax[i] = raw[2];
            if (!said[i]++) klog("bots: record %d (bot): health object %08lx: %.1f of %.1f", i, h, raw[1], raw[2]);
            continue;
        }
        if (raw[2] > smax[i] + 0.01f || raw[2] < smax[i] - 0.01f) {
            /* the MAXIMUM changed (klgrudge.c's CrewHealth / BackstabHealth going in or back, at the same share): that
               step of the health is no loss and must not read as one - 'ONE STEP' below is evidence for other questions */
            klog("bots: record %d (bot): its maximum health changed %.1f -> %.1f (health %.1f -> %.1f): not counted as a loss", i, smax[i], raw[2], seen[i], raw[1]);
            smax[i] = raw[2]; seen[i] = raw[1];
            continue;
        }
        if (raw[1] < seen[i] - 0.05f) {
            /* + where it stood (its node [actor+4] in the world, as klescort.c measures) and its heist stage: a step over
               100 in one tick is no scaled bullet - the place names the killer (the window drop x > 6151, the FallingDebris
               pillar in the boardroom by the window, close combat where a guard stands) */
            float pos[3]; int have = kle_node(klh_rd32(r->actor + 4), pos, 0);
            klog("bots: record %d (bot): lost %.1f (%.1f of %.1f) g%u at %s%.0f %.0f %.0f%s%s", i, seen[i] - raw[1], raw[1], raw[2], r->stage,
                 have ? "" : "? ", have ? pos[0] : 0.0f, have ? pos[1] : 0.0f, have ? pos[2] : 0.0f,
                 seen[i] - raw[1] > 100 ? " - ONE STEP" : "", raw[1] <= 0 ? " - DOWN" : "");
        }
        seen[i] = raw[1];
    }
}

static void klb_log_tick(const struct klb_snap *s, DWORD now)
{
    static DWORD rules0, lastline, lastsay; static struct klb_rec prev[KLB_NREC]; static BYTE veh0; static DWORD state0; static int level0, dirty;
    char line[1100], tmp[12]; int i, k, changed = 0, ai = 0;
    if (s->rules != rules0) {
        rules0 = s->rules; memset(prev, 0, sizeof prev); lastline = 0; veh0 = 0xff; state0 = 0xffffffff; dirty = 1;
        for (i = 0; i < s->n; i++) ai += s->r[i].used && (s->r[i].flags & 1);
        klog("bots: Arcade round object %08lx: %d crew record slot(s), %d AI, Arcade level %d (line: L level, s session state, van state and seconds, per record: index who status g<stage> $money)", s->rules, s->n, ai, s->level);
    }
    for (i = 0; i < s->n; i++) {
        const struct klb_rec *r = &s->r[i], *p = &prev[i];
        if (r->used != p->used || r->status != p->status || r->stage != p->stage || r->flags != p->flags || r->actor != p->actor) {
            changed = 1;
            if (r->used && !p->used) {
                DWORD avt = r->actor ? klh_rd32(r->actor) : 0;      /* B3: what record +4 points at, said before Van is ever used */
                klog("bots: record %d appears: %s, actor %08lx, %s, stage %u, $%lu, flags %02x, actor's vtable %08lx%s", i, klb_who(r), r->actor, klb_status(r->status, tmp), r->stage, r->money, r->flags, avt,
                     !r->actor ? " (no actor)" : avt == KLB_ACTOR_VT ? " = ZFFActor" : (r->flags & 1) ? " = NOT ZFFActor's 00bb3bac: Van would refuse this bot" : "");
            }
            else if (!r->used) klog("bots: record %d is gone", i);
            else {
                if (r->status != p->status) klog("bots: record %d (%s): %s", i, klb_who(r), klb_status(r->status, tmp));
                if (r->stage != p->stage) klog("bots: record %d (%s): heist stage %u -> %u", i, klb_who(r), p->stage, r->stage);
                if ((r->flags ^ p->flags) & 2) klog("bots: record %d: traitor flag %s (flags %02x -> %02x)", i, r->flags & 2 ? "SET" : "cleared", p->flags, r->flags);
            }
        } else if (r->used && r->money != p->money) changed = 1;
    }
    if (klb.log >= 2) klb_health_tick(s, s->rules != hp_rules);          /* Log=2: every loss of health of every bot, in words */
    hp_rules = s->rules;
    if (s->veh != veh0 || s->state != state0 || s->level != level0) changed = 1;
    memcpy(prev, s->r, sizeof prev); veh0 = s->veh; state0 = s->state; level0 = s->level;      /* the words above are said once */
    dirty |= changed;
    if (now - lastsay < 1000) return;                                      /* the line: once a second at most */
    if (klb.log < 2 && !dirty && lastline && now - lastline < 10000) return;
    lastsay = lastline = KLB_T(now); dirty = 0;
    k = snprintf(line, sizeof line, "bots: L%d s%lx van %u %.1fs", s->level, s->state, s->veh, klb_finite(s->timer) ? s->timer : -1.0f);
    for (i = 0; i < s->n && k > 0 && k < (int)sizeof line - 80; i++) {
        const struct klb_rec *r = &s->r[i];
        if (!r->used) continue;
        k += snprintf(line + k, sizeof line - k, " | %d %s %s g%u $%lu", i, klb_who(r), klb_status(r->status, tmp), r->stage, r->money);
        if (klb.log >= 2 && (r->flags & 1) && k < (int)sizeof line - 40) k += snprintf(line + k, sizeof line - k, " hit %.0f", klb_finite(r->hit) ? r->hit : -1.0f);
    }
    klog("%s", line);
}

/* ---------------------------------------------------------------- the traitor tuning (H1) */

struct klb_level { int maxtr; float limit, retaliate; };

/* Do the eleven records look like the game's table? (The object has no vtable; a wrong offset in another build,
   or an object not yet filled, must not be written into.) */
static int klb_tune_ok(DWORD tun, struct klb_level out[KLB_NLEVEL + 1])
{
    int L, k;
    for (L = 1; L <= KLB_NLEVEL; L++) {
        BYTE raw[0x70]; int *iv = (int *)raw; float *fv = (float *)raw;
        if (!klh_rd(tun + 0x6ac + 0x70 * L, raw, sizeof raw)) return 0;
        if (iv[0x6c / 4] < 0 || iv[0x6c / 4] > 32) return 0;                               /* allowed traitors */
        if (!klb_finite(fv[0x20 / 4]) || fv[0x20 / 4] <= 0 || fv[0x20 / 4] > 1000) return 0;   /* the limit */
        if (!klb_finite(fv[0x18 / 4]) || fv[0x18 / 4] < 0 || fv[0x18 / 4] > 100000) return 0;  /* the retaliation limit */
        for (k = 0; k < 4; k++) if (!klb_finite(fv[0x24 / 4 + k]) || fv[0x24 / 4 + k] < 0 || fv[0x24 / 4 + k] > 1000) return 0;        /* stage terms */
        if (iv[0x34 / 4] <= 0 || iv[0x34 / 4] > iv[0x38 / 4] || iv[0x38 / 4] > iv[0x3c / 4]) return 0;                              /* bot money limits, ascending */
        if (iv[0x50 / 4] <= 0 || iv[0x50 / 4] > iv[0x54 / 4] || iv[0x54 / 4] > iv[0x58 / 4]) return 0;                              /* player money limits */
        out[L].maxtr = iv[0x6c / 4]; out[L].limit = fv[0x20 / 4]; out[L].retaliate = fv[0x18 / 4];
    }
    return 1;
}

/* arcade: an Arcade round object is up (the table is looked at and its stock values logged, on any level);
   act: and the level is not stock (section 0) - only then is anything written; otherwise what was written goes back. */
static void klb_tune_tick(int arcade, int act, int capped)
{
    static DWORD tun0; static struct klb_level stock[KLB_NLEVEL + 1]; static int have, applied, toldbad, wascap;
    struct klb_level cur[KLB_NLEVEL + 1]; DWORD tun; int L, n = 0;
    if (!(tun = klh_rd32((DWORD_PTR)KLH_VA(KLB_TUNING)))) return;
    if (tun != tun0) { tun0 = tun; have = applied = wascap = 0; }
    if (!act) wascap = 0;
    if (!arcade && !applied) return;
    if (!klb_tune_ok(tun, cur)) {
        if (arcade && !toldbad++) klog("bots: the tuning object %08lx does not hold the traitor table where this build expects it: nothing is written", tun);
        return;
    }
    if (!have) {                              /* first sight in this process: what the game has (before any write of ours) */
        have = 1; memcpy(stock, cur, sizeof stock);
        for (L = 1; L <= KLB_NLEVEL; L++) {
            BYTE raw[0x70]; int *iv = (int *)raw; float *fv = (float *)raw;
            if (!klb.log || !klh_rd(tun + 0x6ac + 0x70 * L, raw, sizeof raw)) continue;
            klog("bots: stock tuning, level %2d: traitors allowed %d, limit %.1f, stage terms %.0f/%.0f/%.0f/%.0f, bot money %d/%d/%d -> %.0f/%.0f/%.0f/%.0f, player money %d/%d/%d -> %.0f/%.0f/%.0f/%.0f, turns on you after %.0f damage",
                 L, iv[0x6c / 4], fv[0x20 / 4], fv[0x24 / 4], fv[0x28 / 4], fv[0x2c / 4], fv[0x30 / 4], iv[0x34 / 4], iv[0x38 / 4], iv[0x3c / 4], fv[0x40 / 4], fv[0x44 / 4], fv[0x48 / 4], fv[0x4c / 4],
                 iv[0x50 / 4], iv[0x54 / 4], iv[0x58 / 4], fv[0x5c / 4], fv[0x60 / 4], fv[0x64 / 4], fv[0x68 / 4], fv[0x18 / 4]);
        }
    }
    if (!klb.tune || (!act && !applied)) return;         /* nothing of ours is in the table: it is not compared and not written */
    for (L = 1; L <= KLB_NLEVEL; L++) {
        struct klb_level want = stock[L]; DWORD R = tun + 0x6ac + 0x70 * L;
        if (act) {
            want.maxtr = klb.trl[L] >= 0 ? klb.trl[L] : stock[L].maxtr > klb.traitors ? stock[L].maxtr : klb.traitors;
            if (capped) want.maxtr = 0;       /* TraitorsMax reached: the switch is off until a traitor's flag is cleared (the next round) */
            want.limit = klb.liml[L] > 0 ? klb.liml[L] : klb.limit > 0 ? klb.limit : stock[L].limit;
            if (klb.retaliate > 0) want.retaliate = klb.retaliate;
        }
        if (want.maxtr != cur[L].maxtr) n += klh_data((void *)(DWORD_PTR)(R + 0x6c), &want.maxtr, 4, "traitors allowed per Arcade level");
        if (want.limit != cur[L].limit) n += klh_data((void *)(DWORD_PTR)(R + 0x20), &want.limit, 4, "traitor limit per Arcade level");
        if (want.retaliate != cur[L].retaliate) n += klh_data((void *)(DWORD_PTR)(R + 0x18), &want.retaliate, 4, "retaliation limit per Arcade level");
    }
    if (act && capped != wascap) {            /* said once per change, at any Log level: it changes who may turn */
        wascap = capped;
        if (capped) klog("bots: TraitorsMax=%d is reached: 'traitors allowed' is written 0 on every level (%d value(s)) - the game's own tactic turns nobody else this round", klb.tr_max, n);
        else klog("bots: no traitor flag is over TraitorsMax=%d any more: 'traitors allowed' is back (%d value(s))", klb.tr_max, n);
        if (n) applied = 1;
    } else if (act && n) {
        applied = 1;
        klog("bots: tuning written for %d levels (%d value(s) changed): traitors allowed at least %d, limit %.1f%s - stock values are in the lines above and come back when the session is not Arcade or the level is stock", KLB_NLEVEL, n, klb.traitors, klb.limit, klb.retaliate > 0 ? ", retaliation limit set" : "");
    } else if (!act) {
        applied = 0;
        if (n) klog("bots: stock tuning restored (%d value(s))", n);
    }
}

/* ---------------------------------------------------------------- acting on the round (game thread, state 0x19) */

static int klb_put8(DWORD at, BYTE v, const char *what) { return klh_data((void *)(DWORD_PTR)at, &v, 1, what); }

static int klb_same_code(DWORD va, const BYTE *bytes, int n)
{
    BYTE c[16];
    return n <= (int)sizeof c && klh_rd((DWORD_PTR)KLH_VA(va), c, n) && !memcmp(c, bytes, n);
}

/* The record as it is NOW, checked again just before a write: still in use, still that AI actor. */
static int klb_still(const struct klb_snap *s, int i, BYTE *flags, BYTE *status)
{
    DWORD freeb = klh_rd32(s->rules + 0x34c), recs = klh_rd32(s->rules + 0x348); BYTE b = 1, raw[0x7c];
    if (!freeb || recs + 0x7c * i != s->r[i].at || !klh_rd(freeb + i, &b, 1) || b || !klh_rd(s->r[i].at, raw, sizeof raw)) return 0;
    if (*(DWORD *)(raw + 4) != s->r[i].actor || !(raw[0x79] & 1)) return 0;
    *flags = raw[0x79]; *status = raw[0x10];
    return 1;
}

/* record +0x79 |= 2 and [rules+0x33c] &= 1 << index: what ZBecomeTraitorTactic's run (0x488eb0 -> 0x4322f0) leaves */
static int klb_make_traitor(const struct klb_snap *s, int i)
{
    BYTE fl, st, m = 0;
    if (!klb_still(s, i, &fl, &st)) return 0;
    if (!(fl & 2) && !klb_put8(s->r[i].at + 0x79, (BYTE)(fl | 2), "crew record: the bot's traitor flag")) return 0;
    if (i < 8 && klh_rd(s->rules + 0x33c, &m, 1) && m != (BYTE)(m & (1 << i))) klb_put8(s->rules + 0x33c, (BYTE)(m & (1 << i)), "rules +0x33c, as the traitor tactic leaves it");
    return 1;
}

/* Section 3 d: is NOW a good moment for the picked bot to turn? how[120] says what was measured ("" when no key asks).
   Reads only: the local player (as klb_distance finds him), his feet +0x460, the way he faces = MINUS the vector at
   player+0xc14 (klauto.c's kla_player_dir: seen live in run PX3 to be his direction of travel within 1 degree), his
   health object [player+0xa48] (+4 health, +8 maximum: klbalance.c 1 d), the bot's node [actor+4] (kle_node).
   Anything that cannot be read counts as 'not now' - BackstabWait then ends the wait. */
static int klb_moment(const struct klb_rec *r, char how[120])
{
    DWORD gd, pl, hobj; BYTE sel = 0xff, type = 0; float feet[3], face[3], bp[3], hp[2] = { 0, 0 }, dx, dz, d, dot = 0; int near_ = 1, behind = 1, busy = 1, n = 0;
    how[0] = 0;
    if (klb.bs_near <= 0 && !klb.bs_behind && !klb.bs_busy) return 1;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel > 3 ||
        !(pl = klh_rd32(gd + 0x828 + 4 * sel)) || !klh_rd(pl + 0x273c, &type, 1) || type != 2 || !klh_rd(pl + 0x460, feet, 12) ||
        !r->actor || !kle_node(klh_rd32(r->actor + 4), bp, 0)) { strcpy(how, "you or the bot could not be placed"); return 0; }
    dx = bp[0] - feet[0]; dz = bp[2] - feet[2]; d = (float)sqrt(dx * dx + dz * dz + (bp[1] - feet[1]) * (bp[1] - feet[1]));
    if (!klb_finite(d)) { strcpy(how, "you or the bot could not be placed"); return 0; }
    if (klb.bs_near > 0) near_ = d <= klb.bs_near;
    if (klb.bs_behind) {                      /* behind = more than 90 degrees off the way you face (in the ground plane) */
        behind = klh_rd(pl + 0xc14, face, 12) && klb_finite(face[0]) && klb_finite(face[2]) && (face[0] != 0 || face[2] != 0);
        if (behind) { dot = -face[0] * dx - face[2] * dz; behind = dot < 0; }
    }
    if (klb.bs_busy)                          /* hurt = your health is under 97 % of its maximum: you were hit within the regeneration time */
        busy = (hobj = klh_rd32(pl + 0xa48)) != 0 && klh_rd(hobj + 4, hp, 8) && klb_finite(hp[0]) && klb_finite(hp[1]) && hp[1] >= 1 && hp[0] > 0 && hp[0] < hp[1] * 0.97f;
    n = snprintf(how, 120, "it is %.1f m from you", d / 100);
    if (klb.bs_near > 0 && n < 100) n += snprintf(how + n, 120 - n, " (BackstabNear %.0f m)", klb.bs_near / 100);
    if (klb.bs_behind && n < 100) n += snprintf(how + n, 120 - n, behind ? ", behind you" : ", in front of you");
    if (klb.bs_busy && n < 90) n += snprintf(how + n, 120 - n, busy ? ", you are hurt (%.0f of %.0f)" : ", you are not hurt", hp[0], hp[1]);
    return near_ && behind && busy;
}

/* ---------------------------------------------------------------- section 3 f: a turned bot is everybody's enemy */

#define KLB_FOE_TEAM  1                       /* team Enemy, the police's ([[actor+0x54]+4]; bots_dynamic.md / bots_squad.md) */
#define KLB_SCORE_FL  0x1d4                   /* score: dword per crew index, bit 1 = traitor (slot 114 = 0x771a10) */

static struct {                               /* what TraitorFoe wrote, per record; forgotten (never written) when the rules object changes */
    DWORD rules;
    DWORD actor[KLB_NREC], info[KLB_NREC], team0[KLB_NREC];
    char swapped[KLB_NREC], was[KLB_NREC], marked[KLB_NREC], refused[KLB_NREC]; BYTE st[KLB_NREC];
    int fed_told;                                 /* FoeSkipWhileFed: the once-per-round line was written (cleared with the rest when the rules object changes) */
    int kills[KLB_NREC]; char spared[KLB_NREC];   /* section 3 h: crew deaths booked to a team-Enemy traitor; 1 = he is back on team Ally for good (this mask) */
} klb_f;

/* [Bots] FoeSkipWhileFed (2026-10-19, owner run 13:23:18: the human was a fed and crew deaths near the game's own traitor
   were booked to him by section 3 h). Is the LOCAL human a policeman now? The byte klfed.c makes (ZFFPlayer + 0x2723; klfed.c
   is included after this file, so it is read here as klbalance.c / kldown.c read it). Unreadable = no. */
static int klb_human_fed(void)
{
    DWORD gd, pl; BYTE idx = 0xff, police = 0;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &idx, 1) || (signed char)idx < 0 || idx > 31 ||
        !(pl = klh_rd32(gd + 0x828 + 4 * idx)) || !klh_rd(pl + 0x2723, &police, 1)) return 0;
    return police != 0;
}

static void klb_foe_back(const struct klb_snap *s, int i, const char *why)
{
    DWORD info = 0, t = 0; const struct klb_rec *r = &s->r[i];
    if (!klb_f.swapped[i]) return;
    klb_f.swapped[i] = 0;
    if (r->used && r->actor == klb_f.actor[i] && (info = klh_rd32(r->actor + 0x54)) == klb_f.info[i] && klh_rd(info + 4, &t, 4) && t == KLB_FOE_TEAM &&
        klh_data((void *)(DWORD_PTR)(info + 4), &klb_f.team0[i], 4, "a turned AI heister's team: his own back (TraitorFoe)"))
        klog("bots: FOE: record %d: team %lu back (%s)", i, klb_f.team0[i], why);
    else klog("bots: FOE: record %d: its team is NOT written back (%s): the record or its actor changed (actor %08lx -> %08lx, team object %08lx -> %08lx, team now %lu)",
              i, why, klb_f.actor[i], r->used ? r->actor : 0, klb_f.info[i], info, t);
}

static void klb_foe_swap(const struct klb_snap *s, int i)
{
    DWORD gd, info, t = 0, one = KLB_FOE_TEAM, avt, pl; BYTE fl, st; int j; char why[100];
    const struct klb_rec *r = &s->r[i];
    why[0] = 0;
    if (!klb_still(s, i, &fl, &st) || !(fl & 2) || st != 0) return;
    if ((avt = klh_rd32(r->actor)) != KLB_ACTOR_VT) snprintf(why, sizeof why, "its actor's vtable is %08lx, not ZFFActor's", avt);
    else if (!(info = klh_rd32(r->actor + 0x54)) || !klh_rd(info + 4, &t, 4)) strcpy(why, "its team object cannot be read");
    else if (t != 2) snprintf(why, sizeof why, "its team reads %lu, not 2 (Ally)", t);
    else {
        for (j = 0; j < s->n && !why[0]; j++)
            if (j != i && s->r[j].used && s->r[j].actor && klh_rd32(s->r[j].actor + 0x54) == info) snprintf(why, sizeof why, "its team object %08lx is record %d's too", info, j);
        if (!why[0] && (gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) != 0)
            for (j = 0; j < 4 && !why[0]; j++) if ((pl = klh_rd32(gd + 0x828 + 4 * j)) != 0 && klh_rd32(pl + 0x54) == info) snprintf(why, sizeof why, "its team object %08lx is player slot %d's too", info, j);
    }
    if (!why[0] && !klh_data((void *)(DWORD_PTR)(info + 4), &one, 4, "a turned AI heister's team: Enemy (TraitorFoe)")) strcpy(why, "the team dword is not writable");
    if (why[0]) { klb_f.refused[i] = 1; klog("bots: FOE: record %d (TRAITOR) stays team Ally: %s - nothing written; the crew will not fight him", i, why); return; }
    klb_f.swapped[i] = klb_f.was[i] = 1; klb_f.actor[i] = r->actor; klb_f.info[i] = info; klb_f.team0[i] = t;
    klog("bots: FOE: record %d (TRAITOR, actor %08lx, stage %u, $%lu) is team Enemy now (team object %08lx: 2 -> 1): the crew and the escort should shoot him, he shoots them and you", i, r->actor, r->stage, r->money, info);
}

/* game thread only; every pass while an Arcade round object is up. act: the level may be changed (section 0). */
static void klb_foe_tick(const struct klb_snap *s, int act)
{
    int i, j, round = act && s->state == KLB_ROUND, fed = klb.foe_fed && round && klb_human_fed();
    if (s->rules != klb_f.rules) { memset(&klb_f, 0, sizeof klb_f); klb_f.rules = s->rules; memset(klb_f.st, 0xff, sizeof klb_f.st); }
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; DWORD fl = 0, at = s->score + KLB_SCORE_FL + 4 * i;
        /* evidence for K7: a death while a team-Enemy traitor is in play (who killed is not known to the hook) */
        if (fed && r->used && r->status == 7 && klb_f.st[i] == 0) {      /* FoeSkipWhileFed: no booking, no cap, while he is a policeman */
            if (!klb_f.fed_told) { klb_f.fed_told = 1; klog("bots: FOE: you are a fed: crew deaths are NOT booked to a turned bot and TraitorKillMax does not run while you are one (FoeSkipWhileFed=1; said once a round)"); }
        } else if (r->used && r->status == 7 && klb_f.st[i] == 0) {
            float vp[3], tp[3], d, best = -1; int nt = 0, near_ = -1, havev = r->actor && kle_node(klh_rd32(r->actor + 4), vp, 0);
            for (j = 0; j < s->n && j < KLB_NREC; j++) if (j != i && klb_f.swapped[j] && s->r[j].status == 0) {
                nt++;
                if (havev && s->r[j].actor && kle_node(klh_rd32(s->r[j].actor + 4), tp, 0) && klb_finite(d = (float)sqrt((tp[0] - vp[0]) * (tp[0] - vp[0]) + (tp[1] - vp[1]) * (tp[1] - vp[1]) + (tp[2] - vp[2]) * (tp[2] - vp[2]))) && (best < 0 || d < best)) { best = d; near_ = j; }
            }
            if (klb_f.swapped[i]) klog("bots: FOE: record %d (TRAITOR, team Enemy) died", i);
            else if (nt && near_ >= 0) {
                klog("bots: FOE: record %d (%s) died while %d team-Enemy traitor(s) were in play; the nearest, record %d, %.1f m away", i, klb_who(r), nt, near_, best / 100);
                /* section 3 h: a loyal AI heister's death is booked to the nearest traitor if he was close (the killer is not known: a policeman's kill near him counts too - errs towards sparing the crew) */
                if (klb.tr_kills > 0 && (r->flags & 1) && !(r->flags & 2) && i != s->human && best <= klb.tr_kill_near && ++klb_f.kills[near_] >= klb.tr_kills && !klb_f.spared[near_]) {
                    klb_f.spared[near_] = 1;
                    klog("bots: TRAITOR CAP: traitor record %d is booked with %d crew death(s) (TraitorKillMax=%d): he is team Ally again, he no longer shoots the crew (you stay his target); the mask stays", near_, klb_f.kills[near_], klb.tr_kills);
                    klb_foe_back(s, near_, "TraitorKillMax reached");
                    klb_f.refused[near_] = 1;
                }
            }
            else if (nt) klog("bots: FOE: record %d (%s) died while %d team-Enemy traitor(s) were in play (distance unknown)", i, klb_who(r), nt);
        }
        klb_f.st[i] = r->used ? r->status : 0xff;
        /* the team */
        if (klb_f.swapped[i]) {
            if (!round) klb_foe_back(s, i, "the round is not running");
            else if (!r->used || r->actor != klb_f.actor[i]) klb_foe_back(s, i, "the record changed");
            else if (!(r->flags & 2)) klb_foe_back(s, i, "the traitor flag is gone");
            else if (r->status != 0) klb_foe_back(s, i, r->status == 7 ? "he is dead" : r->status == 4 ? "he is aboard" : "he is out of play");
        } else if (klb.foe && round && r->used && (r->flags & 3) == 3 && r->status == 0 && r->actor && !klb_f.refused[i]) klb_foe_swap(s, i);
        /* the score table's traitor bit: on from the swap until the mask goes (the kill bookkeeping, 3 f) */
        if (!r->used || !(r->flags & 2)) {
            klb_f.refused[i] = klb_f.was[i] = 0; klb_f.kills[i] = 0; klb_f.spared[i] = 0;
            if (klb_f.marked[i]) {
                int ours = klb_f.marked[i] == 1;
                klb_f.marked[i] = 0;
                if (ours && r->used &&klh_rd(at, &fl, 4) && (fl & 1)) { fl &= ~1u; if (klh_data((void *)(DWORD_PTR)at, &fl, 4, "score table: the traitor bit TraitorFoe gave a bot, off")) klog("bots: FOE: record %d: score bit 1 off (%08lx): the mask is gone", i, fl); }
            }
        } else if (klb_f.was[i] && !klb_f.marked[i] && act && klh_rd(at, &fl, 4)) {
            if (fl & 1) klb_f.marked[i] = 2;  /* somebody's already (the game's, klgrudge.c's BackstabMark): not ours to take off */
            else { fl |= 1; if (klh_data((void *)(DWORD_PTR)at, &fl, 4, "score table: the traitor bit for a turned bot (TraitorFoe)")) { klb_f.marked[i] = 1; klog("bots: FOE: record %d: score bit 1 set (%08lx): his kills and his death make nobody else a traitor (0x8fb19c / 0x6709f4)", i, fl); } }
        }
    }
}

static void klb_act(const struct klb_snap *s, DWORD now)
{
    const struct klb_rec *h = s->human >= 0 ? &s->r[s->human] : 0;
    int i, waiting = s->veh == 3 || s->veh == 4, bots_play = 0, bots_aboard = 0, aboard = 0, stages = 0, nb = 0;
    /* ---- a new round / a new vehicle. A round starts when the rules object is new, when the session state becomes
       0x19, or when a heist stage went DOWN (the game never lowers one inside a round; 0x817d20 clears them at a
       round start - for a session whose state stays 0x19 between two rounds, which was not looked at). */
    for (i = 0; i < s->n; i++) if (s->r[i].used) { stages += s->r[i].stage; nb += s->r[i].flags & 1; }
    if (s->rules != klb_r.rules || (s->state == KLB_ROUND && klb_r.state != KLB_ROUND)) {
        memset(&klb_r, 0, sizeof klb_r); klb_r.rules = s->rules; klb_r.cand = -2; klb_r.ccand = -2; klb_r.veh = s->veh; klb_r.round_at = KLB_T(now);
    } else if (stages < klb_r.stages) {
        /* B5 of the review: only a GUESS at a new round (a record released in the middle of one would look the same).
           The backstab pick starts again; the once-per-vehicle marks (bribed, rolled, leave, van) stay until the
           vehicle itself is a new one (below): no second bribe, no second call of the damage rule for one vehicle. */
        klb_r.cand = -2; klb_r.backstabbed = 0; klb_r.cand_since = 0; klb_r.wait_since = 0; klb_r.round_at = KLB_T(now);
        klb_r.ccand = -2; klb_r.cdone = 0; klb_r.csince = 0;
    }
    klb_r.stages = stages;
    if (klb_r.cand == -2 && s->state == KLB_ROUND && nb && now - klb_r.round_at >= 3000) {      /* 3 s: the crew has registered */
        klb_r.cand = -1;
        if (klb.backstab > 0) {
            if (klb_roll(klb.backstab)) {
                int pick = (int)((klb_seed >> 8) % (DWORD)nb);
                for (i = 0; i < s->n; i++) if (s->r[i].used && (s->r[i].flags & 1) && !pick--) { klb_r.cand = i; break; }
                klog("bots: backstab: this round bot %d may turn (Backstab=%d%%): when it is in play at stage %d or later with $%d or more for %d s", klb_r.cand, klb.backstab, klb.bs_stage, klb.bs_money, klb.bs_delay);
            } else klog("bots: backstab: nobody was picked this round (Backstab=%d%%)", klb.backstab);
        }
    }
    if (klb_r.ccand == -2 && s->state == KLB_ROUND && nb && now - klb_r.round_at >= 3000) {     /* section 3 g: its own roll, after Backstab's */
        klb_r.ccand = -1;
        if (klb.bs_crew > 0 && klb.foe) {
            if (klb_roll(klb.bs_crew)) {
                int left = nb - (klb_r.cand >= 0), pick = left > 0 ? (int)((klb_seed >> 8) % (DWORD)left) : -1;
                for (i = 0; i < s->n && pick >= 0; i++) if (s->r[i].used && (s->r[i].flags & 1) && i != klb_r.cand && !pick--) { klb_r.ccand = i; break; }
                klog("bots: backstab-crew: this round bot %d may turn on a crewmate (BackstabCrew=%d%%): when it is in play at stage %d or later and another bot in play with $%d or more is within %.0f m, for %d s", klb_r.ccand, klb.bs_crew, klb.bs_stage, klb.bs_money, klb.bs_crew_near / 100, klb.bs_delay);
            } else klog("bots: backstab-crew: nobody was picked this round (BackstabCrew=%d%%)", klb.bs_crew);
        }
    }
    klb_r.state = s->state;
    if (s->veh != klb_r.veh) {
        if (s->veh < 3 || s->veh > 6) {       /* driving in again, or none: what was rolled for the last vehicle is over */
            memset(klb_r.aboard_at, 0, sizeof klb_r.aboard_at); memset(klb_r.rolled, 0, sizeof klb_r.rolled);
            klb_r.bribed = klb_r.leave_rolled = klb_r.van_rolled = 0; klb_r.leave_since = klb_r.van_since = 0;
        }
        klb_r.veh = s->veh;
    }
    if (s->state != KLB_ROUND) return;
    for (i = 0; i < s->n; i++) {
        const struct klb_rec *r = &s->r[i];
        if (!r->used) continue;
        aboard += r->status == 4;
        if (!(r->flags & 1)) continue;
        bots_play += r->status == 0; bots_aboard += r->status == 4;
        if (r->status == 4) { if (!klb_r.aboard_at[i]) klb_r.aboard_at[i] = KLB_T(now); } else klb_r.aboard_at[i] = 0;
    }
    /* ---- H2: the picked bot turns */
    if (klb_r.cand >= 0 && !klb_r.backstabbed) {
        const struct klb_rec *r = &s->r[klb_r.cand];
        if (r->used && (r->flags & 3) == 1 && r->status == 0 && r->stage >= klb.bs_stage && r->money >= (DWORD)klb.bs_money && h && h->status == 0) {
            if (!klb_r.cand_since) klb_r.cand_since = KLB_T(now);
            else if (now - klb_r.cand_since >= (DWORD)klb.bs_delay * 1000 || (klb_r.wait_since && now - klb_r.wait_since >= (DWORD)klb.bs_wait * 1000)) {
                /* section 3 d: the turn waits for its moment (near you / behind you / while you are hurt), BackstabWait
                   seconds at most; with none of the three keys the test is 1 at once = as before */
                char how[120]; int late;
                if (!klb_r.wait_since) klb_r.wait_since = KLB_T(now);      /* kept when b's conditions lapse for a pass: BackstabWait is a limit */
                late = now - klb_r.wait_since >= (DWORD)klb.bs_wait * 1000;
                if (klb_moment(r, how) || late) {
                    klb_r.backstabbed = 1;
                    if (klb_make_traitor(s, klb_r.cand)) klog("bots: BACKSTAB: bot %d (actor %08lx, stage %u, $%lu; you have $%lu) turned traitor: record +0x79 |= 2%s%s%s", klb_r.cand, r->actor, r->stage, r->money, h->money,
                                                              how[0] ? "; " : "", how, how[0] && late ? " - BackstabWait is over, it turns anyway" : "");
                    else klog("bots: BACKSTAB: bot %d could NOT be turned (its record changed or is not writable)", klb_r.cand);
                }
            }
        } else klb_r.cand_since = 0;
    }
    /* ---- section 3 g: the picked bot turns on a crewmate who carries money near it (TraitorFoe makes it a fight) */
    if (klb_r.ccand >= 0 && !klb_r.cdone && klb.foe) {
        const struct klb_rec *r = &s->r[klb_r.ccand]; int vic = -1; float bp[3], vp[3], best = 0;
        if (r->used && (r->flags & 3) == 1 && r->status == 0 && r->stage >= klb.bs_stage && r->actor && kle_node(klh_rd32(r->actor + 4), bp, 0))
            for (i = 0; i < s->n; i++) {
                const struct klb_rec *v = &s->r[i]; float d;
                if (i == klb_r.ccand || !v->used || (v->flags & 3) != 1 || v->status != 0 || v->money < (DWORD)klb.bs_money || !v->actor || !kle_node(klh_rd32(v->actor + 4), vp, 0)) continue;
                d = (float)sqrt((vp[0] - bp[0]) * (vp[0] - bp[0]) + (vp[1] - bp[1]) * (vp[1] - bp[1]) + (vp[2] - bp[2]) * (vp[2] - bp[2]));
                if (klb_finite(d) && d <= klb.bs_crew_near && (vic < 0 || v->money > s->r[vic].money)) { vic = i; best = d; }      /* the richest within reach */
            }
        if (vic < 0) klb_r.csince = 0;
        else if (!klb_r.csince) klb_r.csince = KLB_T(now);
        else if (now - klb_r.csince >= (DWORD)klb.bs_delay * 1000) {
            klb_r.cdone = 1;
            if (klb_make_traitor(s, klb_r.ccand)) klog("bots: BACKSTAB-CREW: bot %d (actor %08lx, stage %u, $%lu) turned on record %d ($%lu, %.1f m away): record +0x79 |= 2 - TraitorFoe makes it the crew's enemy at the next pass; whom it shoots is the game's choice",
                                                       klb_r.ccand, r->actor, r->stage, r->money, vic, s->r[vic].money, best / 100);
            else klog("bots: BACKSTAB-CREW: bot %d could NOT be turned (its record changed or is not writable)", klb_r.ccand);
        }
    }
    /* ---- H3: a bot aboard pays the driver */
    if (klb.bribe > 0 && waiting && !klb_r.bribed && h && h->status == 0 && klb_finite(s->timer) && s->timer > 0.5f)
        for (i = 0; i < s->n; i++) {
            const struct klb_rec *r = &s->r[i]; BYTE fl, st; DWORD money, half, cnt = 0; float zero = 0;
            if (!r->used || !(r->flags & 1) || r->status != 4 || klb_r.rolled[i] || !klb_r.aboard_at[i] || now - klb_r.aboard_at[i] < (DWORD)klb.br_delay * 1000) continue;
            klb_r.rolled[i] = 1;
            if (r->money < (DWORD)klb.br_money) { klog("bots: bribe: bot %d is aboard with $%lu, under BribeMoney=%d: it does not pay", i, r->money, klb.br_money); continue; }
            if (!klb_roll(klb.bribe)) { klog("bots: bribe: bot %d is aboard with $%lu and decided not to pay (Bribe=%d%%)", i, r->money, klb.bribe); continue; }
            if (!klb_still(s, i, &fl, &st) || st != 4 || !klh_rd(s->score + 0x150 + 4 * i, &money, 4)) continue;
            half = money - (money >> 1);                                      /* 0x757541: money -= money >> 1 */
            if (!klh_data((void *)(DWORD_PTR)(s->rules + 0x1d8), &zero, 4, "escape vehicle wait timer")) { klog("bots: BRIBE: bot %d: the vehicle's timer could NOT be written, nothing changed", i); continue; }
            klh_data((void *)(DWORD_PTR)(s->score + 0x150 + 4 * i), &half, 4, "crew money (the driver's half)");
            klb_put8(s->rules + 0x1b2, 0, "driver hold flag"); klb_put8(s->rules + 0x1b3, (BYTE)i, "who paid the driver");
            if (i < 8 && klh_rd(s->rules + 0x250 + 4 * i, &cnt, 4)) { cnt++; klh_data((void *)(DWORD_PTR)(s->rules + 0x250 + 4 * i), &cnt, 4, "pay-the-driver counter"); }
            klb_make_traitor(s, i);
            klb_r.bribed = 1;
            klog("bots: BRIBE: bot %d pays the driver $%lu of $%lu and the vehicle leaves now (timer %.1f s -> 0, state %u); you are not aboard", i, money - half, money, s->timer, s->veh);
            return;
        }
    /* ---- H4: the last bots are aboard and the player is far away */
    if (klb.leave > 0 && waiting && !klb_r.bribed && !klb_r.leave_rolled && bots_aboard && !bots_play && h && h->status == 0 && klb_finite(s->timer) && s->timer > 0.5f) {
        float d = klb_distance(s->rules), zero = 0; int far_ = d >= 0 ? d > klb.lv_dist : h->stage < 3;
        if (!far_) klb_r.leave_since = 0;
        else if (!klb_r.leave_since) klb_r.leave_since = KLB_T(now);
        else if (now - klb_r.leave_since >= (DWORD)klb.lv_delay * 1000) {
            klb_r.leave_rolled = 1;
            if (!klb_roll(klb.leave)) klog("bots: leave: every bot is aboard (%d) and you are far, but they wait (Leave=%d%%)", bots_aboard, klb.leave);
            else if (klh_data((void *)(DWORD_PTR)(s->rules + 0x1d8), &zero, 4, "escape vehicle wait timer")) {
                if (d >= 0) klog("bots: LEAVE: every bot is aboard (%d) and you are %.0f m away (LeaveDistance %.0f m): the vehicle leaves now (timer %.1f s -> 0, state %u)", bots_aboard, d / 100, klb.lv_dist / 100, s->timer, s->veh);
                else klog("bots: LEAVE: every bot is aboard (%d) and you are at heist stage %u (the boarding point could not be read): the vehicle leaves now (timer %.1f s -> 0, state %u)", bots_aboard, h->stage, s->timer, s->veh);
            } else klog("bots: LEAVE: the vehicle's timer could NOT be written");
        }
    } else if (!klb_r.leave_rolled) klb_r.leave_since = 0;
    /* ---- H5: a bot outside blows the vehicle up */
    if (klb.van > 0 && !klb_r.van_rolled && s->vehicle && aboard && (waiting || (klb.van_left && s->veh == 5))) {
        static const BYTE code[16] = { 0x83, 0xec, 0x08, 0x56, 0x8b, 0xf1, 0x8b, 0x86, 0xf8, 0x05, 0x00, 0x00, 0x8a, 0x4c, 0x24, 0x10 };   /* 0x6a1100 */
        int who = -1, lent = 0; BYTE fl, st, veh2 = 0; DWORD att = 0, att2 = 0, avt = 0, zero = 0; int ret;
        for (i = 0; i < s->n && who < 0; i++) {
            const struct klb_rec *r = &s->r[i];
            if (!r->used || !(r->flags & 1) || r->status != 0 || r->stage < 3 || !r->actor) continue;
            if (waiting ? (r->flags & 2) != 0 : 1) who = i;                  /* waiting: a traitor; driving out: whoever was left behind */
        }
        if (who < 0) klb_r.van_since = 0;
        else if (!klb_r.van_since) klb_r.van_since = KLB_T(now);
        else if (now - klb_r.van_since >= (DWORD)klb.van_delay * 1000) {
            klb_r.van_rolled = 1;
            if (!klb_roll(klb.van_chance)) klog("bots: van: bot %d stands at the vehicle with %d aboard and lets it go (VanChance=%d%%)", who, aboard, klb.van_chance);
            else if (klh_rd32(klh_rd32(s->rules) + 4 * 94) != KLB_DAMAGE || !klb_same_code(KLB_DAMAGE, code, sizeof code)) klog("bots: van: the vehicle-damage rule is not the one this build knows: nothing is called");
            else if (!klb_still(s, who, &fl, &st) || st != 0 || !(avt = klh_rd32(s->r[who].actor))) klog("bots: van: bot %d is no longer a live actor: nothing is called", who);
            else if (avt != KLB_ACTOR_VT) klog("bots: van: bot %d's actor %08lx has vtable %08lx, not ZFFActor's %08x: nothing is written, nothing is called", who, s->r[who].actor, avt, KLB_ACTOR_VT);      /* B3 */
            else if (!klh_rd(s->rules + 0x1e8, &att, 4)) klog("bots: van: the attacker field of the rules object cannot be read: nothing is called");
            else {
                /* B2: the attacker is lent for grade 2 only, when the field is null, and taken back after the call */
                if (klb.van == 2 && !att) lent = klh_data((void *)(DWORD_PTR)(s->rules + 0x1e8), &s->r[who].actor, 4, "who damaged the escape vehicle (for the call only)") != 0;
                klog("bots: VAN: bot %d (%s, actor %08lx, vtable %08lx) blows the vehicle up: calling the game's damage rule %08x with grade %d (state %u, %d aboard, attacker %08lx%s)", who, s->r[who].flags & 2 ? "traitor" : "left behind", s->r[who].actor, avt, KLB_DAMAGE, klb.van, s->veh, aboard,
                     lent ? s->r[who].actor : att, lent ? " = the bot, for this call only" : att ? ", the game's own" : klb.van == 2 ? ": the field could not be written" : ": grade 1 does not read it");
                ret = ((int (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(KLB_DAMAGE))((void *)(DWORD_PTR)s->rules, 0, klb.van) & 0xff;
                if (lent) {                   /* only our own value is taken back: one the game stored during the call stays */
                    if (klh_rd(s->rules + 0x1e8, &att2, 4) && att2 == s->r[who].actor) lent = klh_data((void *)(DWORD_PTR)(s->rules + 0x1e8), &zero, 4, "who damaged the escape vehicle (taken back)") ? 2 : 3;
                    else lent = 4;
                }
                klh_rd(s->rules + 0x1dc, &veh2, 1);
                klog("bots: VAN: the rule returned %d; vehicle state %u -> %u%s", ret, s->veh, veh2,
                     lent == 2 ? "; attacker field back to null" : lent == 3 ? "; the attacker field could NOT be put back to null" : lent == 4 ? "; the attacker field was changed by the game during the call and is left as it is" : "");
            }
        }
    } else if (!klb_r.van_rolled) klb_r.van_since = 0;
}

static void klb_tick(int game_thread)
{
    static DWORD last, toldrules; static int toldthread; static char toldwhy[200]; struct klb_snap s; DWORD now = GetTickCount(); int arcade, act = 0, capped = 0;
    char why[200];
    if (!klb.on || !klh_exe_ok || now - last < 100) return;
    last = now;
    arcade = klb_read(&s);
    if (arcade && (klb.tune || klb.backstab > 0 || klb.bribe > 0 || klb.leave > 0 || klb.van > 0 || klb.foe)) {
        act = klb_level(why);                 /* section 0 (B1): asked every pass, the verdict changes when the archive is opened */
        if (s.rules != toldrules || strcmp(why, toldwhy)) {       /* said per round object, and again when the answer changes */
            toldrules = s.rules; strcpy(toldwhy, why);
            if (act) klog("bots: %s: Tune / Backstab / Bribe / Leave / Van may act, as far as their keys are set; the Steam guard blocks every write of this round", why);
            else klog("bots: %s: Tune / Backstab / Bribe / Leave / Van do nothing here (they act only on a level that is not stock); the log runs", why);
        }
    }
    if (arcade && act && klb.tune && klb.tr_max > 0) {       /* section 3 e: bots that carry the traitor flag now */
        int i;
        for (i = 0; i < s.n; i++) capped += s.r[i].used && (s.r[i].flags & 3) == 3;
        capped = capped >= klb.tr_max;
    }
    klb_tune_tick(arcade, act, capped);
    if (!arcade) { klb_r.rules = 0; return; }
    if (klb.log) klb_log_tick(&s, now);
    if (klb.foe && game_thread) klb_foe_tick(&s, act);      /* section 3 f: also when act is 0 - then it only puts back */
    if (!(klb.backstab > 0 || klb.bribe > 0 || klb.leave > 0 || klb.van > 0 || klb.bs_crew > 0)) return;
    if (!act) { klb_r.rules = 0; return; }    /* what was remembered of the round goes with the permission */
    if (!game_thread) {                       /* the round's data is only changed between two frames of the game itself */
        if (s.state == KLB_ROUND && !toldthread++) klog("bots: the tick is not on the game's thread ([KLHook] Tick=0?): backstab / bribe / leave / van do nothing");
        return;
    }
    klb_act(&s, now);
}

static float klb_inif(const char *key, const char *def)
{
    char t[32];
    GetPrivateProfileStringA("Bots", key, def, t, sizeof t, klh_ini);
    return (float)atof(t);
}

static int klb_pct(const char *key) { int v = (int)GetPrivateProfileIntA("Bots", key, 0, klh_ini); return v < 0 ? 0 : v > 100 ? 100 : v; }
static int klb_pos(const char *key, int def, int top) { int v = (int)GetPrivateProfileIntA("Bots", key, def, klh_ini); return v < 0 ? 0 : v > top ? top : v; }

static void klb_init(void)
{
    int L; char key[24];
    klb.on = GetPrivateProfileIntA("Bots", "Enable", 0, klh_ini) != 0;
    if (!klb.on) return;
    klb.log = klb_pos("Log", 1, 2);
    klb.tune = GetPrivateProfileIntA("Bots", "Tune", 0, klh_ini) != 0;
    klb.traitors = klb_pos("Traitors", 1, 32);
    klb.limit = klb_inif("Limit", "6.0"); if (!klb_finite(klb.limit) || klb.limit < 0 || klb.limit > 1000) klb.limit = 6.0f;
    klb.retaliate = klb_inif("Retaliate", "0"); if (!klb_finite(klb.retaliate) || klb.retaliate < 0 || klb.retaliate > 100000) klb.retaliate = 0;
    for (L = 1; L <= KLB_NLEVEL; L++) {
        snprintf(key, sizeof key, "Traitors.%d", L); klb.trl[L] = (int)GetPrivateProfileIntA("Bots", key, -1, klh_ini); if (klb.trl[L] > 32) klb.trl[L] = 32;
        snprintf(key, sizeof key, "Limit.%d", L); klb.liml[L] = klb_inif(key, "0"); if (!klb_finite(klb.liml[L]) || klb.liml[L] < 0 || klb.liml[L] > 1000) klb.liml[L] = 0;
    }
    klb.backstab = klb_pct("Backstab"); klb.bs_stage = klb_pos("BackstabStage", 2, 3); klb.bs_money = klb_pos("BackstabMoney", 250000, 0x7fffffff); klb.bs_delay = klb_pos("BackstabDelay", 20, 3600);
    klb.tr_max = klb_pos("TraitorsMax", 0, 32);
    klb.tr_kills = klb_pos("TraitorKillMax", 2, 32);   /* section 3 h: 0 = no cap (the old behaviour); default 2 */
    klb.tr_kill_near = klb_inif("TraitorKillNear", "3000"); if (!klb_finite(klb.tr_kill_near) || klb.tr_kill_near <= 0) klb.tr_kill_near = 3000;
    klb.bs_near = klb_inif("BackstabNear", "0"); if (!klb_finite(klb.bs_near) || klb.bs_near < 0) klb.bs_near = 0;
    klb.bs_behind = GetPrivateProfileIntA("Bots", "BackstabBehind", 0, klh_ini) != 0; klb.bs_busy = GetPrivateProfileIntA("Bots", "BackstabBusy", 0, klh_ini) != 0;
    klb.bs_wait = klb_pos("BackstabWait", 30, 3600);
    klb.bribe = klb_pct("Bribe"); klb.br_money = klb_pos("BribeMoney", 500000, 0x7fffffff); klb.br_delay = klb_pos("BribeDelay", 4, 600);
    klb.leave = klb_pct("Leave"); klb.lv_delay = klb_pos("LeaveDelay", 3, 600); klb.lv_dist = klb_inif("LeaveDistance", "4000"); if (!klb_finite(klb.lv_dist) || klb.lv_dist < 0) klb.lv_dist = 4000;
    klb.van = klb_pos("Van", 0, 2); klb.van_chance = klb_pos("VanChance", 50, 100); klb.van_delay = klb_pos("VanDelay", 5, 600); klb.van_left = GetPrivateProfileIntA("Bots", "VanLeftBehind", 0, klh_ini) != 0;
    klb_seed = GetTickCount() ^ (GetCurrentProcessId() << 12) ^ 0x9e3779b9u;
    klog("bots: on; Log=%d Tune=%d (Traitors=%d Limit=%.1f Retaliate=%.0f) Backstab=%d%% (stage %d, $%d, %d s) Bribe=%d%% ($%d, %d s) Leave=%d%% (%.0f units, %d s) Van=%d (%d%%, %d s, left behind %d); Arcade only, and everything but the log only on a level that is not the stock one of its slot",
         klb.log, klb.tune, klb.traitors, klb.limit, klb.retaliate, klb.backstab, klb.bs_stage, klb.bs_money, klb.bs_delay, klb.bribe, klb.br_money, klb.br_delay, klb.leave, klb.lv_dist, klb.lv_delay, klb.van, klb.van_chance, klb.van_delay, klb.van_left);
    if (klb.tr_max || klb.bs_near > 0 || klb.bs_behind || klb.bs_busy)      /* only when one is set: the start-up lines of a hook without them are what they were */
        klog("bots: TraitorsMax=%d a round (0 = no cap; needs Tune=1; dead traitors count); the picked bot's turn waits for: within %.0f units of you (0 = any distance), behind you %d (by your direction of travel), you hurt %d - for BackstabWait=%d s at most, then it turns anyway",
             klb.tr_max, klb.bs_near, klb.bs_behind, klb.bs_busy, klb.bs_wait);
    /* section 3 f / g (only said when set, as above) */
    klb.foe = GetPrivateProfileIntA("Bots", "TraitorFoe", 0, klh_ini) != 0;
    klb.foe_fed = GetPrivateProfileIntA("Bots", "FoeSkipWhileFed", 0, klh_ini) != 0;      /* opt-in: 0 = as before */
    klb.bs_crew = klb_pct("BackstabCrew");
    klb.bs_crew_near = klb_inif("BackstabCrewNear", "1500"); if (!klb_finite(klb.bs_crew_near) || klb.bs_crew_near <= 0) klb.bs_crew_near = 1500;
    if (klb.bs_crew > 0 && !klb.foe) { klog("bots: BackstabCrew=%d%% needs TraitorFoe=1 (a turned bot is no enemy of the crew without it): BackstabCrew is OFF", klb.bs_crew); klb.bs_crew = 0; }
    if (klb.foe && klb.tr_kills > 0) klog("bots: TraitorKillMax=%d: a turned bot that is booked with that many crew deaths within %.0f m of him goes back to team Ally (he stops shooting the crew; set 0 for the old, uncapped behaviour)", klb.tr_kills, klb.tr_kill_near / 100);
    if (klb.foe)
        klog("bots: TraitorFoe=1: a turned bot in play is team Enemy (the police's) - the crew and the escort should shoot him, he shoots them and you - and carries the score table's traitor bit (his kills and his death make nobody else a traitor); team 2 back when he is dead / aboard / the round ends; a GUESS until check K7. BackstabCrew=%d%% (stage %d, $%d, within %.0f m, %d s)",
             klb.bs_crew, klb.bs_stage, klb.bs_money, klb.bs_crew_near / 100, klb.bs_delay);
}

#endif /* KLBOT_C */
