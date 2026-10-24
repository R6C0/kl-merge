/*
 * klescort.c - ONE OR TWO AI HEISTERS STAY NEAR THE HUMAN PLAYER and fight beside him; the others keep their routes.
 * Owner, 2026-10-10: 'the backstab helping out via being next to you', 'make the ai heisters go like with lynch or
 * someone else random every time'. Part of KLHook (included by klhook.c after klbot.c, SHIP and TEST alike).
 * No code byte. The ESCORT part writes no data: calls of ONE game function - the soldier's own 'defend this place' order,
 * the one the level scripts and the heist rules themselves give - from the game's own thread. The BoardAll part
 * (2026-10-11, its key's text below) writes ONE data byte, a held bot's heist stage, as the game's own 0x5dd890 does. Full account, the reading it
 * rests on and the live checks E0..E5: re\bots_escort.md. Everything below was read in kl2.exe build 0490 for this
 * file (debug\dasm.py, 2026-10-10). THE ESCORT PART HAS RUN IN THE GAME (2026-10-11, runs E1_DM03, E3_DM01, L11_DM02:
 * 63 orders, the release at the vehicle, the escort aboard; no fault). BoardAll too since (runs L12b_DM02, C3_DM03,
 * B1_DM01, B6_DM06: the byte, the bots board; no fault). Off unless [Bots] Enable=1 AND
 * (Escort=1 or 2, or BoardAll=1, or FollowOut=1, or FollowOutSpare=1).
 * The FollowOut part (2026-10-11, section 3; re\bots_follow_out.md) - 'the crew follows you out' - writes the same stage
 * byte, makes the same order call, and (each behind a key of its own) two more data writes: the vehicle's wait timer,
 * raised as the game's own 'hold the driver' rule raises it, and the rules' table of times at which the crew left
 * behind is shot. IT HAS NOT RUN IN THE GAME.
 *
 * 1. THE GAME'S MECHANISM (EXE = seen in the code)
 *    soldier = [actor + 0x77c] (set by the soldier's constructor 0x761900, `mov [edx+0x77c], esi`; the ONLY class
 *    is CPPScript::ZSoldier, vtable 0xbd0954, made by ZSoldierRout slot 13 = 0x622ae0), [soldier + 0x40] = the actor.
 *    [soldier + 0x64c] = the DEFEND POSITION, a 0x1c-byte block made in the soldier's slot 17 (0x6ab250; constructor
 *    0x40b540): +0 x y z, +0xc and +0x10 a move style and 'style given', +0x11 'changed', +0x12 'queued',
 *    +0x14 the soldier, +0x18 float 1.0. [soldier + 0x648] = the defend goal (+8 its state). EXE.
 *    THE ORDER: ZSoldier vtable +0x13c = 0x760e50 = void __thiscall (soldier, const float pos[3], char soft,
 *    char reset, char unused), ret 0x10. EXE, whole:
 *      - in a network session on a client: returns (Arcade is neither);
 *      - actor->vtable[0x620]() (0x86dba0: [actor + 0x770] != 0 = somebody holds this actor as a human shield):
 *        the place goes to another goal (soldier vtable +0x160). The hook never calls in that case;
 *      - soft2 = soft, but 1 when [soldier + 0xec] != 0 and the place is nearer than 250 units (squared distance
 *        under 62500.0, 0xb7eb28) - 'he is there already';
 *      - reset: [soldier + 0x720] = 0;   [soldier + 0x4fc] = soft2;
 *      - 0x412910 (defend block, pos): asks the pathfinder [[[0xdd2640] + 0xac] + 0xc] (vtable +0x80, then +0x84)
 *        for the place ON THE NAVIGATION MESH and stores that, or pos itself when the pathfinder has none.
 *        So the order snaps its own point: the hook needs no mesh query of its own. (ASSUMPTION for what the two
 *        virtual calls are - 'nearest polygon' and 'point on it'; the stored place is read back and logged.)
 *      - block +0x11 = 1; then: defend goal idle (state 0 or 4) -> soldier vtable +0x1b4 (0x6e49b0: NOT an interrupt -
 *        it erases the {goal, 150} queue entries of eleven behaviour goals, soldier +0x638..+0x664; re\boardall_review_exe.md
 *        3), the goal is queued (0x6cabf0, priority 150), vtable +0x50 (1) re-selects the root; goal running and not
 *        soft2 -> 0x7bbf70: the goal stack is popped down to its first element and that is pushed back - a running
 *        tactic (Loot too) is cut at its yield. 0x7bbf70 has NO empty-stack test (0x5ca0bf is an int3): kle_bot asks.
 *        Running and soft2 -> nothing more.
 *    WHO CALLS IT (38 call sites): ZDefendBehaviourGoal's run 0x686920 at 0x686bac / 0x686df2 with (place, 0, 1, 0)
 *    - this is what every Defend step of the bots' route chain does; ZDefendPlayerPosBehaviour 0x622d52 with (the
 *    nearest player's place, 0 on the first pass / 1 later, 1, 0); ZDefendNPCPos, ZDefendCurrentPos, ZMove, ZFlanking,
 *    ZLeapFrog, ZRunForHelp, ZGrenadeAttack goals the same way; the soldier's own tactics (ZAttackTarget,
 *    ZStayInCoverGoal, ZCloseInOnTarget) with (place, x, 0, 0); and - THE PRECEDENT FOR A CALL FROM OUTSIDE THE
 *    SOLDIER'S OWN SCRIPT - ZGameRulesHeist slot 194 (0x8fa6d0, the vehicle's state change) at 0x8fb04c: when the
 *    vehicle is CALLED, LEAVES or is destroyed (state 1, 2, 5, 6: byte table 0x8fb0a0 = 0,0,1,1,0,0 - NOT while it
 *    waits, as this file said until 2026-10-11) it walks the crew records exactly as this file does and, for every AI
 *    record (+0x79 mask 1) with heist stage >= 3 whose [actor + 0x77c] is not null:
 *        soldier->vtable[0x1b4]();  soldier->vtable[0x13c](&place, 1, 1, 0);
 *    with place = the boarding object's position + 500 along its own x axis (0x8faf72..0x8fafe6).
 *    WHILE THE VEHICLE WAITS (state 3 / 4) a stage-3 bot is taken aboard by its own ZBoardEscapeVehicleTactic (test
 *    0x4faf60, 'stage >= 3' at 0x4fb064), second in every soldier's tactic list (Loot is last); the running goal runs
 *    the first tactic whose test is over 0 (0x85f8e2..0x85f933).
 *    HOW A DEFEND STEP WAITS (0x686c42..0x686ce1): for every member, until the actor's vtable +0x3d0 says yes, or
 *    [soldier + 0x4fc] != 0, or the member is within 10 or 1000 (by the goal's +0x40, not read further) of the step's place. Then the
 *    step is over and its NEXT list is triggered. So: a step whose man was sent elsewhere WAITS; a step whose man
 *    got a SOFT order (or an order to a place he is within 250 of) is OVER at once.
 *    Heist stages are raised by the trigger boxes for whoever stands in them (ZOnlineGamePlayTrigger 0x8d2740 ->
 *    0x5dd890, a maximum; kind 2 = BOARDS also calls the boarding rule, slot 45 = 0x6840a0, which takes any AI
 *    record in play while the vehicle waits - no stage is asked for). EXE.
 *    The human: [gamedata + 0x828 + 4 * (char)[gamedata + 0x898]], feet at +0x460 (kljoin.c, seen live); the game's
 *    own 'nearest player' (0x7263d0) takes the world place of [player + 4], the object's node, and skips a player
 *    whose node has flag bit 10. A bot's place: the same node arithmetic on [actor + 4] (0x60b160 does exactly
 *    that for a soldier): v = M * v + position for the node and every parent (0x7b3020 -> 0x6be1c0, 0x42a4d0).
 *
 * 2. WHAT THE HOOK DOES
 *    Only in an Arcade round that runs (session state 0x19) on a level that is NOT the stock one of its slot
 *    (klbot.c section 0: the same gate as Backstab / Bribe / Leave / Van), from the game's own thread.
 *    CHOICE, 3 s after the round started (the crew has registered): of the AI records in play that are not
 *    traitors, the Escort nearest to the human, drawn at random among the nearest Escort + 2 (so it is not the
 *    same man every round: at the start all seven stand in one row). EscortRecord=<i> names the first one instead.
 *    HOLD, twice a second per escort:
 *      - the defend block is read. If it no longer holds what the hook's last order left there, somebody else gave
 *        an order: farther than 600 from ours = the bot's own route chain (kept as 'its route place'; the hook's
 *        hold is over until the next order), nearer = one of the soldier's own tactics moved it (taken as ours).
 *        GUESS: the 600; nothing in the block says who wrote it.
 *      - the human is farther than EscortFar (800 = 8 m) from the BOT, and the hook has no hold or the human has
 *        moved more than EscortRetarget (500) from it, and the last order is EscortEvery (2 s) old: ONE call
 *        soldier->vtable[0x13c](&p, 0, 1, 0) - the arguments of a Defend step - with p = EscortSide (300) from the
 *        human towards the bot (the second escort 70 degrees round), at the human's height. The game snaps it.
 *        The bot is then at least EscortFar - EscortSide from p: never within the 250 that would make the order
 *        'soft' and end the chain's waiting step.
 *      - a bot that has not come 1 m nearer to its place 12 s after an order gets the human's own place once
 *        (a point beside him may lie behind a wall; where he stands is on the mesh).
 *    Never a teleport, never a write: between two orders the bot is the game's own soldier holding a defend
 *    position - cover, fire, leash and spacing work as they do at any hold place of its route.
 *    AGAINST THE MAP'S CHAIN - who wins, and why that is safe. Both sides use the same routine, which only
 *    replaces the place and queues a plan: the LAST caller wins, nothing is left half written.
 *      a. A Defend step that was running when the hook ordered keeps waiting for its man (he is not at its place
 *         and the order was not soft). Its NEXT is not triggered: the chain stands still behind him.
 *      b. A step started by something else (a TriggerDelay2, a TriggerActorsDead, the jump list) orders him to
 *         ITS place: the bot turns and goes. The hook sees the block change, remembers the place, and calls him
 *         back only when he is EscortFar from the human again - so the chain gets up to 8 m of its way, then the
 *         hook wins again and the step of (b) waits like (a).
 *      c. The stage boxes are places, not chain steps: an escort gets stage 1 / 2 / 3 when it walks through them
 *         beside the human, or later on its own route.
 *    RELEASE - the escort must still board:
 *      - the vehicle WAITS (state 3 / 4; EscortUntil=1: already while it drives in): an escort at stage 3 is left
 *        alone - its own board tactic takes it to the vehicle (and slot 194 orders it when the vehicle leaves). An escort under stage 3
 *        (its chain stood still, so it never walked its last leg) gets the rules' own place by the same order with
 *        (place, 0, 1, 0): boarding object + 500 along its x axis, computed from the node data as 0x8faf72 does.
 *        Not soft, unlike the rules' call: a soft order would end the waiting step of (a) and the chain's next
 *        step would send the bot back into the level. On the way it crosses the BOARDS box, which gives stage 3
 *        and boards it. ASSUMPTION: the box is where the rules' place is (it is where stage-3 bots are sent).
 *      - the human is dead or aboard, or (EscortStage=1..3, default off) has reached that heist stage: when the
 *        hook's hold is still the bot's place and a route place is known, ONE order back to it (place, 0, 1, 0):
 *        the waiting step of (a) ends when he arrives and the chain goes on from where it stood. If the vehicle
 *        waits later and the bot is in play under stage 3, the boarding order above, once (EscortBoard=0: not).
 *      - the escort is dead, aboard, a traitor, or no longer the actor that was chosen: dropped, no call.
 *        EscortRefill=1 chooses another for a slot that was dropped before the release.
 *    WHAT IS TESTED BEFORE EVERY CALL (the game's own callers hand over a soldier a script owns; the hook comes
 *    from a crew record): the first 16 code bytes of 0x760e50; record in use, mask 1, not mask 2, status 0, still
 *    the actor chosen; actor's vtable 0xbb3bac; its node without flag bit 10; [actor + 0x576] == 1 (the test
 *    ZDefendPlayerPosBehaviour makes before it orders a member, 0x622c8d); [actor + 0x770] == 0; soldier's vtable
 *    0xbd0954 whose entry +0x13c is 0x760e50; [soldier + 0x40] == actor; the defend block readable with its +0x14
 *    == soldier; the defend goal readable; the pathfinder object and its two vtable entries inside kl2.exe.
 *    NOT ESTABLISHED: what [actor + 0x576] is beyond 'this member takes orders' (a downed or ragdolled bot?); what
 *    [soldier + 0xec] is; which of the soldier's tactics move the defend block by themselves and how far; whether
 *    a bot called away from a loot place drops what it does cleanly (the route chain's Defend steps do the same to
 *    looting bots, 0x686bac / 0x686df2 with the same arguments); two escorts whose places snap to the same polygon.
 *
 * 3. THE CREW FOLLOWS YOU OUT (FollowOut; read in kl2.exe 2026-10-11, full account re\bots_follow_out.md)
 *    WHAT KILLS THE CREW THAT IS LEFT BEHIND (EXE; live run PB_DM03_board_hp: four bots, 252 of 252 in one step each).
 *    ZGameRulesHeist - the Arcade class only - shoots them itself. Slot 194 (0x8fa6d0), case 'state 5 = the vehicle
 *    drives out', when client 0 (the human) has flag 0x20 'aboard' (0x8fab77 `test byte [score+0x1d4], 0x20`):
 *        base = now + 1.0 .. 1.3 s  ([sysif+0x48], 1/1024 s);  step = 8.0 s / [rules+0x354] (8 record slots: 1 s)
 *        [rules+0xeec + 4*k] = base + step * (k +- 0.7)          one time per slot k
 *        [rules+0xf1c + k]   = k, then shuffled (0x7f87c0)       which crew record slot k names
 *    and the rules' update, slot 7 (0x74b6d0), every frame while the state is 5 and that flag is set (0x74b8a2..0x74b99a):
 *    for every slot whose time has come and whose record is in use, an AI member (+0x79 mask 1) and has none of the
 *    client flags 4 dead / 0x20 aboard / 0x40 escaped:
 *        actor->vtable[0x694](&damage)    (0x69f900; the record's amount is float 1000000.0, 0xb631b0, no attacker)
 *        rules->vtable[0x40](actor, 0)    (slot 16 = 0x485740: money 0, kill text, flag 4, status 7)
 *    No distance, no stage, no traitor test: EVERY AI heister in play dies while the vehicle leaves, one about every
 *    second, in a random order (the times span 8 s over the slots whatever the vehicle's own drive-out is - 8.4 s on
 *    the F07 van, from its field [controller+0x74], 0x8fab3e: the last slot's time can lie past it, and stock then
 *    ends the round with one AI heister still in play - live run PB_DM01_board_hp). A bot is safe only aboard - the
 *    boarding rule (slot 45, 0x6840a0) still
 *    takes it in state 5 while float [tuning+0x630] minus the timer is under 1.0. With the human NOT aboard nothing of
 *    this runs (the vehicle comes back, state 7 -> 0): every idle-human run. Nothing of ours is in that code, stock
 *    Arcade does the same, and the multiplayer classes have no such loop (that flags test occurs once in the exe,
 *    here). When state 5 ends: 0x805120 (aboard -> escaped), the round is over 3 s later.
 *    WHAT THE HOOK DOES (Arcade round, a level that is not stock, the game's thread - as sections 0 / 2)
 *    SIGNAL: the human's own crew record has heist stage 3 - he stood in the exit trigger, whose routine 0x6c3d50
 *    gives stage 3 and calls the vehicle in the same step - while he is a heister in play or aboard and carries
 *    FollowOutMoney or more; FollowOutAfter seconds later. (Not 'near the boarding place': the rules know no boarding
 *    place before the vehicle is called, [rules+0x1e0] is 0 in state 0; and the exit boxes are large - the bank's is
 *    50 m from the van - so a distance only comes later than the stage. Time is what the crew lacks.)
 *    THEN, for every AI record in play that is no traitor:
 *      a. heist stage 3 into its record, once (the byte BoardAll writes; what 0x5dd890 writes). ONLY FOR A RECORD
 *         WHOSE ACTOR IS A ZFFActor WITH A READABLE PLACE: from stage 3 on the rules walk the record themselves, at
 *         every call and departure of the vehicle, with no test of the actor (0x8fb031 `mov ecx, [record+4]` /
 *         0x8fb034 `mov edi, [ecx+0x77c]`) - a stage 3 in a record with no actor would be a fault inside kl2.exe.
 *         From there the GAME does the work: its loot tactic lets go while the vehicle waits (0x4519dc - ONLY then:
 *         while the vehicle drives in a stage-3 bot in reach of loot goes on looting), its board tactic runs to the
 *         vehicle and boards (0x4fb064; also in the last 2 s of the drive in), and slot 194 gives every stage-3 AI the
 *         order to the boarding place at every later call and departure.
 *      b. FollowOutOrder=1: while the vehicle DRIVES IN (state 1 / 2) AND ITS TIMER IS 2 s OR MORE, one order to the
 *         rules' boarding place by the soldier's own routine (place, 0, 1, 0) - the call the escort's release makes.
 *         It is the order slot 194 gave the stage-3 AI when the vehicle was called, a moment before these bots had
 *         their stage. Again only when somebody else has moved its defend place more than 6 m from what our order
 *         left (KLE_ROUTE, section 2's measure for 'the route chain, not one of the soldier's own tactics'; GUESS as
 *         there - a renewal pops a fighting bot's goal stack, so a tactic's small move is left alone), and
 *         FollowOutEvery seconds apart; at a later call the game's own order has put the place there, and
 *         the hook orders only a bot whose place is not within 3 m of it. Only bots this part gave their stage: the
 *         others had the game's order. NOT while the board tactic can have the bot - while the vehicle waits, and
 *         in state 1 / 2 once the timer is under 2.0 (its test 0x4faff7 and its run 0x82f9be, `fcomp [0xb5c828]`): a
 *         not-soft order would cut that tactic at its yield. Not within 4 m of the place (within 2.5 m the game
 *         takes an order as 'soft', which ends a waiting step of the route chain). Never to an escort (section 2).
 *         THE ROUTE CHAIN against it: a step that was running waits for its man (2 a); a step started by a timer or
 *         a death orders him elsewhere and is answered by the renewal; the stage byte is not read by the chain.
 *      c. FollowOutHold=N: the game has a rule for 'driver, wait' - slot 152 (0x8b3930), the first criminal aboard
 *         pressing HoldEscape: timer += 5.0 (0xb5a068), ONCE a vehicle (behind [rules+0xd95]). The hook writes the
 *         same float by the same amount, up to N / 5 times a visit, and leaves that byte alone (the human's own
 *         HoldEscape still gives its 5 s): while the vehicle
 *         waits, the HUMAN IS ABOARD, its timer is under 2 s (and not 0: something set it to leave), nobody paid the
 *         driver ([rules+0x1b3] == 0xff), the vehicle is not damaged ([score+0x60] == 0: a heavily damaged one must
 *         go, 0x55ed4a) and at least one of the called crew in play COMES - it is 2 m or more nearer to the boarding
 *         place than 2 s before (KLE_COME; a bot that stands, fights, loots or walks the other way does not hold the
 *         driver): timer += min(5, what is
 *         left of N). At most N seconds a visit. Readers of the timer: its countdown (slot 195), the HUD's seconds
 *         (slot 191, a signed byte: the timer stays under 8 s here), the boarding rule's state-5 window, the board
 *         tactic in state 1 / 2. The round's own end timer (slot 192) does nothing while the vehicle's state is 1..6
 *         (0x5dffc6): a held vehicle postpones the round's end, it cannot lose the round by the clock. While the
 *         human sits aboard the game's ten scripted hits on the vehicle run as ever (0x6db660, read as: 1/30 of its
 *         health each, never under a tenth; made once per wait); real police fire can destroy a vehicle that waits
 *         longer - AND DID, the first two times the hold ran (c2).
 *     c2. THE HELD VEHICLE WAS DESTROYED WITH THE HUMAN ABOARD (LIVE 2026-10-11, the bank, runs N1_DM03_boardnear and
 *         N1b: 'record 0 (you): dead' with 5,500 health and no hit, the bot aboard dead in the same tick, klbot's
 *         line 'van 6 9.8s' = STATE 6, 20.9 / 21.3 s after the wait began; the run without the hold, N1c: escaped).
 *         EXE: the key-framed van's health is a ZAnimatedVehicle object under the vehicle group (kle_veh_read). Its
 *         'ProjectileHit' message (slot 89 = 0x87f340 -> 0x6c4730) takes weapon damage x the hit's scale [hit+0x18] x
 *         the vehicle's own factor off [+0x14] (0x5aebb0). THE DIRECT PATH (found by the review, re\bots_hold_review.md
 *         1): that hit routine itself, when the rules' vehicle kind [rules+0x1ec] is 3 and the health is at or under
 *         0 (0x5aec7c..0x5aec89), calls rules slot 33 (the attacker into [rules+0x1e8]) and rules slot 84 = 0x61e570,
 *         which in states 1..5 calls slot 94 = 0x6a1100 with grade 2: GRADE 2 SETS STATE 6 AND KILLS EVERY RECORD
 *         WITH STATUS 4 - the human by slot 11, an AI member by slot 16. No level wiring is in that chain, and it is
 *         why the state went 3 -> 6 with no 'heavily damaged' departure: grade 1 (a waiting vehicle's timer = 0)
 *         comes only as a level message (the object's update, slot 87 = 0x8fa330, sends 'Activate_DamageFX_01 / 02 /
 *         03' at half, a quarter and 0; the escape controller's 'EscVehicleState' 0x6d7d64 -> 0x594b10 -> slot 94 -
 *         a second way to the same routine, not what the death rests on). State 6 is made by nothing else (the
 *         review: slot 195 never makes it; the only 'push 6' are slot 94 and its multiplayer twin 0x839380).
 *         In Arcade the maximum is one of four of the vehicle's fields by the option Difficulty [0x156b5f0] (0x552e53;
 *         klbalance.c's KLR_DIFF, 0..3; the owner's logs say 'campaign difficulty option 1' = the second: the stock
 *         van's, IF the file's seven numbers lie in field order 3000 / 5000 / 7000 / 10000, is 5000 - N3a's first
 *         'health H of M' line says M). Stock exposes it for 8 s + the 8.4 s of the drive-out; a 15 s hold for 31.
 *         STOCK'S OWN EXPOSURE IS NOT SAFE EITHER: U_M01.log (Hot Coffee, idle human, no hold) has state 6 1.3 s into
 *         a second visit - so the health is not made new between visits, or one step takes all of it. NOT
 *         ESTABLISHED: that HITS took the health (no log has it; the DESTROYED line now says so when it went with
 *         this file's shield on), and whether steady fire did it or one point-blank step (a soldier within 1.6 m of
 *         his target sends 'ProjectileHit' with scale 100, re\melee_damage.md); the 'follow: vehicle:' lines now say
 *         the health as it falls.
 *         THE ANSWER (FollowOutShield, default 2): right before the first timer write of a visit the hook sets that
 *         object's 'Invulnerable' byte (+0x21: what its own 'Invulnerable' message writes, 0x87f426; both hit
 *         messages ask it first, 0x6c4740 / 0x87f36e) and takes it back (the 1 it wrote, on the same object) when the
 *         vehicle is gone - state 0, 1, 2, 6, 7, 8 - or, with FollowOutShield=1, when it drives out; also at a new
 *         round, at the round's end and when the round can no longer be read. NO SHIELD POSSIBLE = NO HOLD (the
 *         health object cannot be read, or the rules' kind byte [rules+0x1ec] is 3 = the key-framed van and no
 *         ZAnimatedVehicle was found under it); a vehicle of another kind with no such object (helicopter, car) is
 *         held unshielded - the hit routine calls 'destroyed' for kind 3 only (0x5aec7c). The shield goes on at the
 *         first timer write, about 6 s into the wait: before it, and at a visit that is not held, the risk is
 *         stock's. Under the shield the scripted hits go on (to a tenth at the lowest): with FollowOutShield=1, or
 *         at the next visit, the vehicle stands unshielded at what is left - the 'shield: off' line says how much.
 *         The scripted hits and a level's 'FakeDamage'
 *         do not ask the byte: the first cannot go under a tenth, the second no level of ours has (not checked).
 *         klmove.c's WaitForYouHold asks the same guard (kle_hold_guard): there bots sit aboard while the human comes.
 *      d. FollowOutSpare=1 (works without FollowOut): when the vehicle drives out, the times at rules +0xeec are set
 *         to 0x7fffffff (the loop's test is signed, `jg` 0x74b966): no slot's time comes, nobody left behind is shot.
 *         They stay in play to the round's end, 3 s after the human has escaped - an end state stock produces too (a
 *         slot whose time lies past the drive-out, 8.4 s on the F07 van: live run PB_DM01_board_hp). The first time
 *         is due 0.3 s after the state change at the earliest, so
 *         the state byte is read on EVERY pass of the tick while the vehicle waits. Written only when the table looks
 *         like one: every time a value of the game's clock (or ours), and EITHER the slot bytes a shuffle of
 *         0..slots-1 (a schedule was made: 0x8fabfd + 0x7f87c0) OR all twelve times 0 (a table never used: the
 *         constructor zeroes the times, 0x8355db.., and writes NOTHING at +0xf1c, so the slot bytes are then what the
 *         heap held - the game itself skips a slot byte out of range, 0x74b91e, and so must this test).
 *    STOPS: a bot aboard, dead, escaped, turned traitor or replaced in its record is left alone; orders end when the
 *    vehicle is 2 s from arriving; everything ends when the human is dead or has escaped (a bot found dead in that
 *    last pass still gets its line). THE STAGE IS NOT TAKEN BACK: a human who
 *    walks back inside after his stage 3 has a crew that goes to the vehicle and boards without him, as the game's own
 *    stage-3 bots do (his escort stays until the vehicle waits). FollowOutMoney keeps a walk through the exit box
 *    before any loot from calling the crew out.
 *    WHO ELSE READS STAGE 3: as under BoardAll below (the traitor tactic's stage term, Backstab, Van, the off-stage
 *    damage factor, kltalk). FollowOut is OFF with VanLeftBehind=1, for BoardAll's reason.
 *    TWO CONSEQUENCES THE OWNER MUST KNOW (EXE; re\bots_follow_out.md 2.5):
 *      - THE PAYOUT. At the round's end the rules zero the money of everybody who did not escape (0x70b920) and give
 *        every ESCAPED NON-TRAITOR the same share: the sum of what they carried over their number (0x796410; its
 *        factor 0x7360a0 is `fld1 / ret`). Being shot or being left in play is the same there - FollowOutSpare
 *        changes no payout - but every bot FollowOut / FollowOutHold gets aboard joins that pool: the human's cut,
 *        in stock already the average of those who escaped, becomes the average of a larger crew (control run: 550,000
 *        + 40,000 + 415,000 over 3). (A member with client flag 8 or 0x80 gets his own money instead; what those
 *        flags are was not read. What the score page prints, 0x783010, was not followed.)
 *      - TRAITORS. The traitor tactic's stage term is 0 / 0 / 2 / 3 by the BOT's stage (0x79b883; klbot.c 3): a bot
 *        inside at stage 1 cannot reach the stock limit 7.0 (0 + 3 + 3), a bot raised to 3 can (3 + its money + your
 *        money). So FollowOut makes a betrayal possible for a called bot wherever the tuning allows traitors: Arcade
 *        level 4 and up in stock. With [Bots] Tune=1 (every level, limit 6.0) a stage-1 bot could just turn already;
 *        a called one needs 3 points less of the two money terms.
 *
 * NO OFF-GAME RIG IN THE REPO: klbot.c had a scratch rig; the escort part is proven by its live runs; BoardAll by three
 * reviews of the code against the exe (re\boardall_review_exe.md, _code.md, _rework.md) and two live runs (L12a / b);
 * FollowOut by a scratch rig against a made-up round (re\bots_follow_out.md 6) - its own logic, nothing of the game -
 * and by one adversarial review (re\bots_follow_out_review.md: one MUST, seven SHOULD - all applied, re\bots_follow_out.md 10;
 * the rig now holds the review's five cases as checks).
 *
 * KLHook.ini
 *   [Bots]
 *   Enable=1            klbot.c must be on (the crew records are read through it)
 *   Escort=0            0 off, 1 or 2 = that many AI heisters stay near the human
 *   EscortDry=0         1 = everything is chosen and logged, NOTHING is called (live check E0)
 *   EscortFar=800       the human farther than this from the escort: it is called to him (100 = 1 m)
 *   EscortSide=300      how far beside the human its place is;  0 = the human's own place
 *   EscortRetarget=500  the human has moved this far from the escort's place: a new place
 *   EscortEvery=2       seconds between two orders to one escort, at least
 *   EscortUntil=3       vehicle state that ends the escort: 3 = it waits, 1 = it drives in
 *   EscortStage=0       1..3 = also ends when the HUMAN has reached that heist stage
 *   EscortBoard=1       a released escort under stage 3 is sent to the boarding place when the vehicle waits
 *   EscortRefill=0      1 = an escort that died is replaced
 *   EscortRecord=-1     crew record of the first escort (a test aid); -1 = the nearest
 *   EscortLog=1         2 = also every order and every place the route chain gave
 *   BoardAll=0          1 = NOBODY IS LEFT HELD BY LOOT (2026-10-11; reviewed re\boardall_review_exe.md, _code.md): while
 *                       the escape vehicle WAITS (state 3 / 4), an AI heister that is HELD gets heist stage 3 written
 *                       into its crew record. HELD = in play, no traitor, never an escort this round, at stage 1 or 2,
 *                       and for BoardAllStill seconds it has neither moved 1 m nor earned anything.
 *                       WHY (live runs L8 / L10 / L11 on Late Night Opening): ZLootTactic (test 0x451920) goes on
 *                       choosing any money object within 8 m (tuning +0xc1c.., 0x8b94d0) that is not 'taken'; one a
 *                       bot cannot take (a watch behind glass nobody opened, the watch shop's clerk) holds him for
 *                       the rest of the round - six of seven stood on the clerk for minutes, and the tactic runs
 *                       before the route chain's order is walked. The byte flips TWO of the game's own tests: Loot is
 *                       off while 'stage == 3 and the vehicle's state is 3 or 4' (0x4519dc), and
 *                       ZBoardEscapeVehicleTactic is on from stage 3 (0x4fb064) - so the bot runs to the vehicle by
 *                       itself; when the vehicle leaves, slot 194 gives every stage-3 AI the (soft) order to the
 *                       boarding place. It is what 0x5dd890 (the trigger boxes' routine) writes: max(stage, n), nothing else.
 *                       LIMITS: it ACTS ONLY ONCE SOMEBODY HAS CALLED THE VEHICLE - a wait needs somebody in the exit
 *                       trigger, and Loot lets a stage-3 bot go only while the vehicle waits. The case of runs L8 /
 *                       L10 (the whole crew held at the clerk, the human elsewhere, no vehicle ever) is NOT touched:
 *                       that one is the map's to solve (un-takeable money out of the bots' reach). The vehicle waits
 *                       8 s a visit and Loot is on again at state 5 - a bot 100 m away needs several visits, and may
 *                       be held again by other loot on its way. A bot with no path to the boarding object (the bank's
 *                       yard before the drop, Retomoto's tower) only stops looting. 'Held' as coded is 'stands and
 *                       earns nothing': a long route wait at stage 1 or 2 qualifies too (replay of L10 / L11: of 24
 *                       spells of 15 s, 8 were the trap; a wrong raise only sends a bot to the vehicle early).
 *                       WHO ELSE READS STAGE 3 (five readers in all, re\boardall_review_exe.md 1): the bot's own damage
 *                       on police (x [R+0x1c] while its stage is not the human's, 0x591c00), the traitor tactic's stage
 *                       term (0x79b883), klbot.c's Backstab ('stage >= BackstabStage') and Van ('at the vehicle' =
 *                       stage 3: DO NOT COMBINE BoardAll WITH Van / VanLeftBehind), kltalk.c's 'Stage2' line.
 *   BoardAllStill=15    seconds without moving and without earning that make a bot 'held'; 0 = every bot at stage 1 or 2
 *                       (a value that is not a plain number counts as 15). The clock starts again when the round stood
 *                       still (no pass of this file for 1.5 s: the game window was not in front).
 *   BoardAllStage=1     0 = the byte is not written (the pass only logs whom it would free)
 *   BoardAllOrder=0     1 = a freed bot also gets ONE not-soft order to the rules' boarding place per visit (the call
 *                       the escort part makes). Off: the byte alone does it, and that place lies on the van's approach.
 *   FollowOut=0         1 = THE CREW FOLLOWS YOU OUT (section 3; NOT RUN IN THE GAME): once YOUR crew record has heist
 *                       stage 3 (you stood in the exit trigger: the vehicle is called), every AI heister in play that
 *                       is no traitor gets heist stage 3 and, while the vehicle drives in (and is 2 s or more away),
 *                       one order to the boarding place. Works without Escort and with BoardAll. Not with
 *                       VanLeftBehind=1. TWO PRICES: every bot it gets aboard shares the escaped crew's money with
 *                       you (the rules pay each escaped non-traitor the average of what they carried); and a called
 *                       bot counts as 'at the vehicle' for the game's traitor tactic - on Arcade level 4 and up it
 *                       can turn on you where a bot inside the building could not (with Tune=1: on every level, and
 *                       with less money).
 *   FollowOutDry=0      1 = every line, NOTHING written or called (EscortDry=1 does the same for this part)
 *   FollowOutMoney=1    you must carry this much for the signal to count (a walk through the exit box before any loot
 *                       does not call the crew out); 0 = no condition
 *   FollowOutCrewMoney=0 1 = the money of the loyal AI heisters in play counts too (2026-10-18, run N1018_L10_DM03A_e56:
 *                       the bots took every Vault stack, you reached the exit with $0 and the crew with $2M stood idle
 *                       50 m off while the vehicle came three times)
 *   FollowOutAfter=0    seconds between your stage 3 and the call (a grace for the crew's last grab)
 *   FollowOutOrder=1    0 = the stage byte only (the game's own order comes at the vehicle's next call)
 *   FollowOutEvery=2    seconds between two orders to one bot, at least
 *   FollowOutHold=0     seconds the driver may be held per visit, at most (0 = never; 15 is a fair first value): while
 *                       the vehicle waits with YOU ABOARD and crew that was called still COMES (2 m nearer to the
 *                       boarding place in 2 s), its timer gets up to 5 s more each time it falls under 2 s - the float
 *                       and the amount of the game's own HoldEscape rule, more often than that rule's once.
 *                       25 is what the bank's crew needs once BoardNear makes it walk (re\bots_follow_out.md 11)
 *   FollowOutHoldAlone=0 1 = the hold also runs while YOU ARE IN PLAY, not aboard, when the nearest called bot that
 *                       comes is within FollowOutHoldAloneRange=40 m (GUESS, 1..100) of the boarding place (2026-10-18,
 *                       Vault run N1018_L22: the van left after 8.0 s with four called bots 37-53 m off and coming)
 *   FollowOutComeMoved=0 1 = a called bot also COMES (for the holds) when it moved 2 m in 3D or 1 m in height in the
 *                       2 s sample and got no more than 2 m farther (2026-10-18, Vault N1018_L24: the way out of the vault
 *                       first leads away from the vehicle). GUESS
 *   FollowOutStopPlace=0 1 = once the vehicle has waited this round, later drive-ins order the crew to where it
 *                       waited instead of to the moving vehicle ([rules+0x1e0] is the vehicle itself; L22's orders went
 *                       25-47 m back along its road). GUESS: it parks at the same place each visit
 *   FollowOutShield=2   what keeps a HELD vehicle from being destroyed with you aboard (section 3 c2; also for
 *                       WaitForYouHold): 2 = from the first held second it takes no hit until it is gone, 1 = until
 *                       it drives out (the drive-out's 8.4 s are the game's own risk again), 0 = no shield - the
 *                       form that killed the human aboard in runs N1 / N1b; nothing is safe then, stock's 8 s only
 *                       make it rare (U_M01.log). 2 or 1 is the OWNER's choice: 2 = after a hold the van cannot be
 *                       lost at all (less than stock's risk), 1 = it drives out unshielded at what the scripted
 *                       hits left of it (a tenth at the lowest: more than stock's risk for those 8.4 s)
 *   FollowOutSpare=0   1 = those who are not aboard when the vehicle drives out are NOT shot by the rules (one block
 *                       of the rules object: the times of their deaths, put off). A key of its own: works with
 *                       FollowOut=0. They are left in play; the round still ends 3 s after you have escaped. No
 *                       payout changes: dead or left in play, their money is not in the escaped crew's pool.
 *
 * LOG (the lines the live checks look for)
 *   escort: on; Escort=1 Far=800 Side=300 ...
 *   escort: you: record 0, player 1a2b3c00, feet (x, y, z), node (x, y, z)                        once per round
 *   escort: record 3 (actor ..., soldier ...) chosen: 2.1 m from you, 7 bot(s) could be; its place now (x, y, z)
 *   escort: record 3 re-pointed: you are 12.4 m away at (x, y, z); place asked (x, y, z), the game set (x, y, z);
 *           2 order(s) since the last line; its route place (x, y, z)                              at most every 5 s
 *   escort: record 3 released (the vehicle waits, state 3): sent to the boarding place (x, y, z)
 *   escort: record 3 released (you are aboard): back to its route place (x, y, z)
 *   escort: record 3 dropped: its record says dead
 *   board: on; BoardAll=1 Still=15 s Stage=1 Order=0 ...
 *   board: record 5 (stage 1) at (x, y, z): held for 41 s with $150000: the vehicle waits (state 3): heist stage set to 3
 *   board: record 5 at (x, y, z): sent to the boarding place (x, y, z) ...; visit 1 of the vehicle      (BoardAllOrder=1)
 *   follow: on; FollowOut=1 Money=1 After=0 s Order=1 Every=2 s Hold=15.0 s Spare=1 ...
 *   follow: you are at heist stage 3 (in play, $550000); vehicle state 1, timer 7.2 s: THE CREW IS CALLED - 5 AI ...
 *   follow: record 3 (stage 1, $0) at (472, 294, -4932), 55.1 m from the boarding place: heist stage set to 3
 *   follow: record 3 (stage 1): its actor is no ZFFActor with a readable place (00000000): the stage byte is NOT written ...
 *   follow: record 3 sent to the boarding place (x, y, z), the game set (x, y, z); order 1
 *   follow: the vehicle arrives in 1.9 s (call 1): no order from here on ...                       once per call
 *   follow: the vehicle waits (state 3, timer 8.0 s, visit 1): record 3 (stage 3, $0) in play at (x, y, z), 31.0 m from the boarding place, coming (4.2 m nearer in the last 2 s)
 *   follow: the vehicle waits: 1 of the crew aboard, 4 in play (nearest 12.0 m, farthest 55.1 m), 1 dead; you are in play
 *   follow: hold: the vehicle would leave in 1.8 s with you aboard and 3 of the crew still coming ...: timer 1.8 -> 6.8 s (5.0 of 15.0 s used); SHIELD ON: the vehicle's 'Invulnerable' byte [..+0x21] 0 -> 1 until it is gone (FollowOutShield=2); health 2400 of 3000
 *   follow: vehicle: it waits (state 3, timer 7.9 s, 0.0 s after it began to wait): health 3000 of 3000 (100 %), takes hits; you are in play
 *   follow: vehicle: hit (state 3, timer 4.1 s, 3.9 s after ...): health 2700 of 3000 (90 %), takes hits / SHIELDED by this file; you are aboard
 *   follow: vehicle: DESTROYED (state 6) 21.2 s after it began to wait: health 0 of 3000; the line before said ...
 *   follow: shield: off (the vehicle is gone): the vehicle's 'Invulnerable' byte [..+0x21] 1 -> 0 after 23.5 s; its health 2400 of 3000
 *   follow: record 3 aboard 21.4 s after the crew was called (vehicle state 3, timer 4.1 s)
 *   follow: the vehicle leaves (state 5, timer 8.4 s, visit 1): record 5 (stage 3, $0) in play at (x, y, z), 22.0 m from the boarding place, coming (5.1 m nearer in the last 2 s)
 *   follow: the vehicle leaves (state 5) with you aboard: 4 of the crew aboard, 1 left in play (record(s) 5), 1 dead
 *   follow: spare: the vehicle drives out with you aboard: the rules' times for those left behind (8 slots, the first due in 0.6 s) are put off: record(s) 5 not shot
 *   follow: spare: the vehicle drives out without you: no time was set for this departure; the table ... is put off in case you board in its first second
 *   follow: record 5 dead at (x, y, z) ... - LEFT BEHIND: the rules shoot whoever is not aboard while the vehicle drives out with you
 *   follow: record 5 dead ..., seen as the round ended for you - LEFT BEHIND: ...                  a death in the last pass before 'over'
 *   follow: over (you escaped): of the crew 4 escaped, 2 dead, 0 left in play
 */
#ifndef KLESCORT_C
#define KLESCORT_C

#define KLE_ORDER       0x00760e50            /* ZSoldier vtable +0x13c: (pos, soft, reset, unused) */
#define KLE_SOLDIER_VT  0x00bd0954            /* CPPScript::ZSoldier, the class's only vtable */
#define KLE_HELD_VT     0x0086dba0            /* ZFFActor vtable +0x620: [actor + 0x770] != 0 */
#define KLE_MAX         2
#define KLE_ROUTE       600.0f                /* a foreign place farther than this from ours = the route chain's. GUESS */
#define KLE_KILL_TIMES  0xeec                 /* rules: per slot the time ([sysif+0x48], 1/1024 s) at which its record is shot (0x8fabe3, 0x74b907) */
#define KLE_KILL_SLOTS  0xf1c                 /* rules: per slot one byte, the crew record it names (0x8fabfd, 0x74b910) */
#define KLE_KILL_NEVER  0x7fffffffu           /* a time the loop's signed test (0x74b963 cmp / jg) never reaches */
#define KLE_HOLD_AT     2.0f                  /* FollowOutHold: the wait timer under this many seconds gets more */
/* ... this much at a time. Was 5.0 (what the game's own hold rule adds, 0x8b3959 / 0xb5a068); the owner, 2026-10-14: the van marker's time
   'keeps flickering and doesnt match' - every 5 s step threw the shown time from under 2 s back up to 7 (a saw-tooth, and the marker's
   low-time state on and off). Now [Bots] HoldStep=0 (default) gives the whole rest of the hold in ONE step, so the time jumps once and then
   counts down to the real departure; HoldStep=5 is the old behaviour. Read by klmove.c's WaitForYouHold too. */
static float kle_hold_step = 60.0f;
#define KLE_HOLD_STEP   kle_hold_step
#define KLE_COME        200.0f                /* ... while a called bot COMES: this much nearer to the boarding place than 2 s before. GUESS (a walk is about 3 m/s) */
#define KLE_BOARD_WIN   2.0f                  /* state 1 / 2 with the timer under this: the board tactic is live for a stage-3 bot (0x4faff7, 0x82f9be; float 0xb5c828) - no order */
#define KLE_VEH_VT      0x00bcc0b4            /* ZAnimatedVehicle, the class's only vtable (slot 87 = 0x8fa330 its update, slot 89 = 0x87f340 its messages): the escape van's health object */
#define KLE_ENTS        0x00e0ff90            /* the scene: [[[this]+0xc]+0xc] = the table of 128-byte entity slots (0x7936ea, 0x793c48) */
#define KLE_VEH_KIND    0x1ec                 /* rules: the escape vehicle's kind, a byte (slot 95 = 0x5822d0; written by 0x42cfb0 from the class of [rules+0x1e4]): 3 = the key-framed van, the only kind a hit can destroy (0x5aec7c) */
#define KLE_VEH_INV     0x21                 /* ZAnimatedVehicle: 1 = it takes no hit - the byte its messages 'Invulnerable' / 'Vulnerable' write (0x87f426 / 0x87f43b), asked by 'ProjectileHit' (0x6c4740) and 'DamageInfo' (0x87f36e) */

static struct {
    int n, dry, log, record, refill, until, stage, board; DWORD every; float far_, side, retarget;
    int all, all_stage, all_order; DWORD all_still;      /* BoardAll, BoardAllStage, BoardAllOrder, BoardAllStill in ms */
    int fo, fo_dry, fo_order, fo_spare, fo_shield, fo_crew_money; DWORD fo_after, fo_every, fo_money; float fo_hold;      /* FollowOut..: After / Every in ms, Hold in s; Shield 0 / 1 / 2 */
    int fo_unshielded;      /* FollowOutHoldUnshielded (default 1): hold a vehicle that has no health object to shield */
    int fo_hold_alone, fo_stop, fo_come_moved; float fo_hold_alone_m;      /* FollowOutHoldAlone (+ ..Range in m), FollowOutStopPlace (2026-10-18, Vault run N1018_L22) */
    int vb, vb_dry, vb_log; DWORD vb_delay; float vb_hp;                   /* [VanBlow] Enable / Dry / Log / EmptyDelay (ms) / HealthMax (2026-10-24) */
} kle;

/* [VanBlow] (owner 2026-10-24: 'they never blow up, they are always on fire from when the cops shoot it but never see it explode').
   WHY: with FollowOutShield=3 (live) the van's 'Invulnerable' byte (ZAnimatedVehicle +0x21) is set 0.5 s into EVERY wait until the
   vehicle is gone, so neither the player's nor the police's hits count and its health (stock 3000..10000 by difficulty) can never reach 0:
   the damage effects (fire at half / a quarter, 'Activate_DamageFX_01 / 02', from the scripted hits) show, the blow-up (health 0 ->
   0x5aec7c -> rules slot 84 -> slot 94 grade 2 = state 6, 'DamageFX_03', Crash/Explode relays) never comes. Live log 24 Oct: 93 % -> 80 % -> gone,
   'SHIELDED by this file'.
   WHAT: the shield was there so that a van with PEOPLE ABOARD is not destroyed (state 6 kills every record with status 4 - the human by
   slot 11, an AI member by slot 16; live 2026-10-11: held van shot to pieces, human dead). A van with NOBODY aboard has no one to lose,
   so: while a wait (state 3 / 4) or the drive-out (5) has had NO record with status 4 for EmptyDelay ms, this file takes its own shield off
   (kle_shield_off; only the byte it wrote) and does not set it again (kle_hold_guard says no); the moment somebody is aboard again it may
   be shielded again (FollowOutShield=3: the next pass; 2: by the next hold). So a van that is shot while the crew is not in it can burn
   and then EXPLODE; one with anybody aboard cannot be destroyed (the old protection). The cost, said plainly: an empty van shot to
   0 by the police ends the escape for everybody who is not aboard (that is the stock game's rule too).
   HealthMax (default 0 = leave): when the vehicle's health is above it at the start of a wait, health and the 'quarter' field are lowered to
   it (ZAnimatedVehicle +0x14 health, +0x18 = max / 4, both read by kle_veh_read; the write is a GUESS that the damage-effect thresholds
   - half / quarter / 0 of max, slot 87 - read +0x18 and not a cached copy). Dry=1: everything is only logged ('WOULD ...').
   Stock levels: this file acts on no stock level (klb_level), so Dog Days' own FA maps keep the game's rule (nothing is shielded there). */
static struct { DWORD rules, empty_at; int open, aboard, hp_done; } kle_vb;
static int kle_vb_aboard(const struct klb_snap *s)
{
    int i, n = 0;
    for (i = 0; i < s->n && i < KLB_NREC; i++) if (s->r[i].used && s->r[i].status == 4) n++;
    return n;
}

/* THE HOLD'S SHIELD (section 3 c2). Not in kle_r: that is cleared at every new round, and a byte of the level's vehicle
   that this file set must be taken back whatever happens to the round. obj = the ZAnimatedVehicle whose 'Invulnerable'
   byte is OURS (0 = none), rules = the round object it was set under, at = when, told = 'set again' was said */
static struct { DWORD obj, rules, at; int told; } kle_sh;

struct kle_e {
    int rec, mode;                            /* mode: 0 free, 1 hold, 2 released (may still be sent aboard), 3 done */
    DWORD actor, soldier, order_at, log_at; int orders, direct, told_soft, have_target, have_route;
    float target[3], route[3], d_order;
};
static struct {
    DWORD rules, state, round_at; int stages, picked, told_you, told_none, told_gate; char used[KLB_NREC];
    struct kle_e e[KLE_MAX];
    /* BoardAll: the vehicle's visits; who was ordered at which; all_raised 1 = this file wrote the byte, 2 = looked at
       (dry run / BoardAllStage=0); all_told bit 1 / 2 / 4 = a line said; where a bot stands, what it has, since when */
    int visit, was_waiting, told_nobd; int all_visit[KLB_NREC]; char all_told[KLB_NREC], all_raised[KLB_NREC], all_seen[KLB_NREC];
    float all_pos[KLB_NREC][3]; DWORD all_money[KLB_NREC], all_since[KLB_NREC], all_actor[KLB_NREC];
    /* FollowOut: fo_since = the human was first seen at stage 3 with his money, fo_fired = the crew was called (both a
       tick time, 0 = not), fo_over = said that it is over; fo_call = the calls of the vehicle seen since (state 1 / 2);
       fo_win_call = the call for which 'no order from here on' was said;
       per record fo_did: 1 the stage byte written, 2 would be (dry), 4 'not written' said, 8 aboard said, 0x10 dead
       said, 0x20 'no order' said for this call, 0x40 'has stage 3 / is a traitor' said, 0x80 'no actor' said;
       fo_moves = 1 it COMES: fo_d (its distance to the boarding place at the sample of fo_pos_at) fell by KLE_COME over
       the last 2 s sample, fo_near = by how much; 0 it does not; 2 not known yet (no whole sample: counted as no) */
    DWORD fo_since, fo_fired; int fo_over, fo_told, fo_call, fo_was_coming, fo_win_call, fo_hold_visit, fo_hold_told; BYTE fo_veh; float fo_held;
    int fo_stop_have, fo_stop_told; float fo_stop_at[3]; float fo_p[KLB_NREC][3];      /* FollowOutComeMoved: the bot's place at the last 2 s sample */      /* FollowOutStopPlace: the boarding place of the last wait this round (the vehicle parked) */
    BYTE fo_did[KLB_NREC]; char fo_moves[KLB_NREC]; int fo_ocall[KLB_NREC], fo_orders[KLB_NREC];
    DWORD fo_actor[KLB_NREC], fo_order_at[KLB_NREC], fo_pos_at[KLB_NREC]; float fo_target[KLB_NREC][3], fo_d[KLB_NREC], fo_near[KLB_NREC];
    /* FollowOutSpare: the rules object whose vehicle state the fast pass watches (0 = none); this departure is dealt
       with; its times were put off by this file (the dead of this departure are then not the rules' shot) */
    DWORD spare_rules; int spare_at5, spare_told, spare_put;
    /* the vehicle's health log (FollowOut): its state at the last pass, when its wait began, the health the last line
       said and when, 'cannot be read' / 'has no health object' said */
    BYTE vh_prev; DWORD vh_wait_at, vh_said_at; float vh_said; int vh_told;
} kle_r;

static float kle_dist(const float a[3], const float b[3])
{
    return (float)sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]) + (a[2] - b[2]) * (a[2] - b[2]));
}
static int kle_ok3(const float v[3]) { return klb_finite(v[0]) && klb_finite(v[1]) && klb_finite(v[2]); }

/* The world place of a scene node, and (dir != 0) its x axis in the world: 0x7b3020 / 0x717890 done from the node
   data - nine floats at +0, the position at +0x24, the parent at +0x50 (0x6be1c0: x' = x*m6 + y*m3 + z*m0 ...). */
static int kle_node(DWORD node, float pos[3], float dir[3])
{
    float v[3] = { 0, 0, 0 }, d[3] = { 1, 0, 0 }, m[12], t[3]; int depth;
    if (!node) return 0;
    for (depth = 0; node && depth < 32; depth++) {
        if (!klh_rd(node, m, sizeof m)) return 0;
        t[0] = v[0] * m[6] + v[1] * m[3] + v[2] * m[0] + m[9];
        t[1] = v[0] * m[7] + v[1] * m[4] + v[2] * m[1] + m[10];
        t[2] = v[0] * m[8] + v[1] * m[5] + v[2] * m[2] + m[11];
        memcpy(v, t, sizeof v);
        t[0] = d[0] * m[6] + d[1] * m[3] + d[2] * m[0];
        t[1] = d[0] * m[7] + d[1] * m[4] + d[2] * m[1];
        t[2] = d[0] * m[8] + d[1] * m[5] + d[2] * m[2];
        memcpy(d, t, sizeof d);
        node = klh_rd32(node + 0x50);
    }
    if (node || !kle_ok3(v) || !kle_ok3(d)) return 0;
    memcpy(pos, v, sizeof v);
    if (dir) memcpy(dir, d, sizeof d);
    return 1;
}

/* the local player: his object, his feet (+0x460, kljoin.c) and his node's place (what 0x7263d0 measures with) */
static int kle_human(DWORD *player, float feet[3], float nodepos[3])
{
    DWORD gd, pl, node, fl = 0; BYTE sel = 0xff, type = 0;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel > 3) return 0;
    if (!(pl = klh_rd32(gd + 0x828 + 4 * sel)) || !klh_rd(pl + 0x273c, &type, 1) || type != 2) return 0;
    if (!klh_rd(pl + 0x460, feet, 12) || !kle_ok3(feet)) return 0;
    if (!(node = klh_rd32(pl + 4)) || !klh_rd(node + 0x3c, &fl, 4) || (fl >> 10 & 1)) return 0;      /* 0x7263fa: such a player is nobody's 'nearest player' */
    if (!kle_node(node, nodepos, 0)) memcpy(nodepos, feet, 12);
    *player = pl;
    return 1;
}

static int kle_later;                         /* kle_bot's last refusal was one that passes (asked again next pass; no escort is dropped for it) */

/* Is crew record i a bot the order may be given to, now? -> 0 and why[100], or 1 with its actor, soldier and place. */
static int kle_bot(const struct klb_snap *s, int i, DWORD *actor_, DWORD *soldier_, float pos[3], char why[100])
{
    const struct klb_rec *r = &s->r[i]; DWORD actor = r->actor, node, soldier, fl = 0, held = 1, blk, goal, tmp; BYTE b576 = 0, raw[0x1c];
    why[0] = 0; kle_later = 0;
    if (i < 0 || i >= s->n || !r->used) { strcpy(why, "its record is gone"); return 0; }
    if (!(r->flags & 1)) { strcpy(why, "its record is not an AI member's"); return 0; }
    if (r->flags & 2) { strcpy(why, "it is a traitor"); return 0; }
    if (r->status) { snprintf(why, 100, "its record says %s", r->status == 4 ? "aboard" : r->status == 7 ? "dead" : r->status == 6 ? "escaped" : "not in play"); return 0; }
    if (!actor || klh_rd32(actor) != KLB_ACTOR_VT) { strcpy(why, "its actor is not a ZFFActor"); return 0; }
    if (klh_rd32((DWORD_PTR)KLH_VA(KLB_ACTOR_VT + 0x620)) != KLE_HELD_VT) { strcpy(why, "ZFFActor's 'held' test is not the one this build knows"); return 0; }
    if (!(node = klh_rd32(actor + 4)) || !klh_rd(node + 0x3c, &fl, 4) || (fl >> 10 & 1)) { strcpy(why, "its node is off (flag bit 10)"); return 0; }
    if (!klh_rd(actor + 0x576, &b576, 1) || b576 != 1) { strcpy(why, "its actor takes no orders now ([actor+0x576] is not 1)"); return 0; }
    if (!klh_rd(actor + 0x770, &held, 4) || held) { strcpy(why, "somebody holds it as a human shield"); return 0; }
    if (!(soldier = klh_rd32(actor + 0x77c)) || klh_rd32(soldier) != KLE_SOLDIER_VT || klh_rd32(soldier + 0x40) != actor) { strcpy(why, "actor +0x77c is not its ZSoldier"); return 0; }
    if (!(blk = klh_rd32(soldier + 0x64c)) || !klh_rd(blk, raw, sizeof raw) || *(DWORD *)(raw + 0x14) != soldier) { strcpy(why, "its soldier has no defend block yet"); return 0; }
    if (!(goal = klh_rd32(soldier + 0x648)) || !klh_rd(goal + 8, &tmp, 4)) { strcpy(why, "its soldier has no defend goal yet"); return 0; }
    if (tmp != 0 && tmp != 4) {               /* the defend goal RUNS: a not-soft order goes through 0x7bbf70, which pops the goal stack with no empty test */
        DWORD sb = klh_rd32(soldier + 4), se = klh_rd32(soldier + 8), g0 = 0;
        if (!sb || se <= sb || ((se - sb) & 3) || !klh_rd(sb, &g0, 4) || !g0) { strcpy(why, "its defend goal runs but its goal stack is empty (0x7bbf70 has no test for that)"); kle_later = 1; return 0; }
    }
    if (!kle_node(node, pos, 0)) { strcpy(why, "its place cannot be read"); return 0; }
    *actor_ = actor; *soldier_ = soldier;
    return 1;
}

static int kle_block(DWORD soldier, float pos[3])
{
    DWORD blk = klh_rd32(soldier + 0x64c);
    return blk && klh_rd(blk, pos, 12) && kle_ok3(pos);
}

/* what 0x760e50 and 0x412910 use without a test of their own */
static int kle_callable(char why[100])
{
    static const BYTE code[16] = { 0x55, 0x8b, 0xec, 0x83, 0xec, 0x0c, 0x56, 0x8b, 0xf1, 0x8b, 0x0d, 0x98, 0xe5, 0x68, 0x01, 0xe8 };      /* 0x760e50 */
    DWORD sys, a, pf, vt;
    if (klh_rd32((DWORD_PTR)KLH_VA(KLE_SOLDIER_VT + 0x13c)) != KLE_ORDER || !klb_same_code(KLE_ORDER, code, sizeof code)) { strcpy(why, "the soldier's order routine is not the one this build knows"); return 0; }
    if (!(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) || !(a = klh_rd32(sys + 0xac)) || !(pf = klh_rd32(a + 0xc)) || !(vt = klh_rd32(pf))) { strcpy(why, "there is no pathfinder object ([[sysif+0xac]+0xc])"); return 0; }
    if (!klt_code(klh_rd32(vt + 0x80)) || !klt_code(klh_rd32(vt + 0x84))) { strcpy(why, "the pathfinder object is no object of the game"); return 0; }
    return 1;
}

/* ONE call of the game's order (game thread only). want = the place asked; got = what the defend block holds after.
   -> 1 called, 0 not (why says), 2 dry run. */
/* STUTTER WATCH (2026-10-14): every order this hook gives, when and how long the call took - klhook.c's hitch line names the
   orders of the half second before a long frame ('orders' = the game's path request is the suspect of the owner's freezes) */
static volatile DWORD kle_order_at; static volatile LONG kle_order_n; static LARGE_INTEGER kle_order_f; static double kle_order_ms_max;

/* ORDER TRACE (v82i, [Bots] OrderTrace=1, default 0; re\bots_active.md 'Order trace'). One 'otrace:' line per order a module of this hook gives a
   crew bot, plus one per teleport of klhop.c, plus one when the defend block of a bot CHANGES without any of that (the game's own chain or a
   tactic: issuer 'GAME?'). OFF: kltr.on is 0 and every function here returns at its first test - no read, no write, no log.
   Issuers are named by the call site (kltr_set before the call); an order from a site that did not set one is 'untagged'. */
#define KLTR_CAP 2000
static struct { int on, rec; LONG n; DWORD rules, round_at, polled, said[KLB_NREC]; const char *who, *why; float last[KLB_NREC][3]; BYTE have[KLB_NREC], told_cap; } kltr;
static void kltr_set(const char *who, const char *why, int rec) { if (!kltr.on) return; kltr.who = who; kltr.why = why; kltr.rec = rec; }
static void kltr_round(DWORD rules, DWORD now)
{
    if (!kltr.on || rules == kltr.rules) return;
    kltr.rules = rules; kltr.n = 0; kltr.told_cap = 0; kltr.round_at = KLB_T(now); kltr.polled = 0;
    memset(kltr.have, 0, sizeof kltr.have); memset(kltr.said, 0, sizeof kltr.said);
}
static void kltr_line(int rec, const char *who, const char *kind, const float a[3], const char *blab, const float b[3], const char *why)
{
    DWORD now;
    if (!kltr.on) return;
    if (kltr.n >= KLTR_CAP) { if (!kltr.told_cap++) klog("otrace: %d lines this round: no more are written until the next round", KLTR_CAP); return; }
    now = GetTickCount(); kltr.n++;
    klog("otrace: t=%lu r=%.1f rec=%d by=%s %s (%.0f, %.0f, %.0f)%s(%.0f, %.0f, %.0f) why=%s", now, kltr.round_at ? (double)(LONG)(now - kltr.round_at) / 1000.0 : -1.0, rec, who, kind,
         a ? a[0] : 0, a ? a[1] : 0, a ? a[2] : 0, b ? blab : " ", b ? b[0] : 0, b ? b[1] : 0, b ? b[2] : 0, why ? why : "-");
}
/* res: 1 = called, 2 = dry run. rec < 0 = the hint of kltr_set. */
static void kltr_order(int rec, const float want[3], const float got[3], int res)
{
    const char *who, *why;
    if (!kltr.on) return;
    if (rec < 0) rec = kltr.rec;
    who = kltr.who ? kltr.who : "untagged"; why = kltr.why;
    kltr.who = 0; kltr.why = 0; kltr.rec = -1;
    kltr_line(rec, who, res == 2 ? "ORDER-DRY" : "ORDER", want, " set=", got, why);
    if (res != 2 && rec >= 0 && rec < KLB_NREC) { memcpy(kltr.last[rec], got, 12); kltr.have[rec] = 1; }
}
static void kltr_tp(int rec, const char *who, const float to[3], const char *why) { if (kltr.on) kltr_line(rec, who, "TELEPORT", to, 0, 0, why); }
/* twice a second: a block that moved and that none of the traced orders explains was set by the game (its chain / a tactic) or by a module that bypasses kle_order2 */
static void kltr_poll(const struct klb_snap *s, DWORD now)
{
    int i; float cur[3];
    if (!kltr.on || now - kltr.polled < 500) return;
    kltr.polled = KLB_T(now);
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; DWORD soldier;
        if (!r->used || !(r->flags & 1) || r->status || !r->actor || klh_rd32(r->actor) != KLB_ACTOR_VT) { kltr.have[i] = 0; continue; }
        if (!(soldier = klh_rd32(r->actor + 0x77c)) || klh_rd32(soldier) != KLE_SOLDIER_VT || !kle_block(soldier, cur)) continue;
        if (!kltr.have[i]) { memcpy(kltr.last[i], cur, 12); kltr.have[i] = 1; continue; }
        if (kle_dist(cur, kltr.last[i]) > 5.0f) {
            if (now - kltr.said[i] >= 1000) { kltr.said[i] = KLB_T(now); kltr_line(i, "GAME?", "BLOCK-CHANGED", cur, " was=", kltr.last[i], "block now differs from the last traced order or poll: the game's chain or a tactic (or a module that bypasses kle_order2)"); }
            memcpy(kltr.last[i], cur, 12);
        }
    }
}

/* ORDER KIND DEBOUNCE (2026-10-18, overnight audit: night_read counted 76 flip-flops in the owner's session 112 - escort / move-restless / fedkit-hunted
   giving one bot alternating places). Every order of this hook goes through kle_order2. Its caller is told apart by the entry it passes: a held
   escort's entry lives in kle_r.e[] (class 1 = follow the human); every other caller (klmove.c's Restless / reach, klfedkit.c's Hunted, the
   release of an escort) builds a temporary entry (class 2). [Bots] OrderGap=<seconds> (default 8, 0 = off): an order of the OTHER class to the
   same record less than that many seconds after the last one is REFUSED ('why' says so; every caller treats a refusal as 'not ordered now'
   and tries again on its own timer, no counter of theirs counts it). Not while a vehicle waits (kle_gap_wait: the doors beat everything), not in a dry
   run, and a released escort (mode 2 / 3) counts as class 2. Same-class orders are as before (their own timers). GUESS: that 8 s is long enough
   for the game's chain to lose its interest and short enough not to hold a bot back; the key is the lever. Not run in the game. */
static int kle_gap_s = 8; static volatile int kle_gap_wait, kle_gap_exempt;   /* exempt: BoardAll / FollowOut orders (set around their calls) and a released escort's orders are never refused */
static struct { DWORD at; BYTE cls; } kle_gap_last[KLB_NREC];
static DWORD kle_gap_refused;
static int kle_gap_check(const struct kle_e *e, char why[100])
{
    int cls, rec = e->rec; DWORD now = GetTickCount();
    if (kle_gap_s <= 0 || kle_gap_wait || rec < 0 || rec >= KLB_NREC) return 1;
    cls = (e >= kle_r.e && e < kle_r.e + KLE_MAX && e->mode == 1) ? 1 : 2;
    if (kle_gap_exempt || (e >= kle_r.e && e < kle_r.e + KLE_MAX && e->mode != 1)) { kle_gap_last[rec].at = KLB_T(now); kle_gap_last[rec].cls = 2; return 1; }      /* review 2026-10-18: a release (back to its route place / the boarding place) is a one-shot and the vehicle's timer runs: never refused */
    if (kle_gap_last[rec].at && kle_gap_last[rec].cls != cls && (DWORD)(now - kle_gap_last[rec].at) < (DWORD)kle_gap_s * 1000) {
        snprintf(why, 100, "debounce: record %d got a %s order %.1f s ago (OrderGap=%d s)", rec, kle_gap_last[rec].cls == 1 ? "escort" : "other", (now - kle_gap_last[rec].at) / 1000.0, kle_gap_s);
        if (!(kle_gap_refused++ % 20)) klog("order-gap: %s - %lu such refusal(s) so far", why, (unsigned long)kle_gap_refused);
        return 0;
    }
    kle_gap_last[rec].at = KLB_T(now); kle_gap_last[rec].cls = (BYTE)cls;
    return 1;
}

static int kle_order2(struct kle_e *e, const float want[3], float got[3], char why[100], int dry)
{
    float p[4]; BYTE soft = 0; LARGE_INTEGER t0, t1; double ms;
    memcpy(got, want, 12);
    if (!kle_ok3(want)) { strcpy(why, "the place is not a number"); return 0; }
    if (!kle_callable(why)) return 0;
    if (dry) { kltr_order(e->rec, want, want, 2); return 2; }
    if (!kle_gap_check(e, why)) return 0;
    p[0] = want[0]; p[1] = want[1]; p[2] = want[2]; p[3] = 0;
    if (!kle_order_f.QuadPart) QueryPerformanceFrequency(&kle_order_f);
    QueryPerformanceCounter(&t0);
    ((void (__fastcall *)(void *, void *, const float *, int, int, int))(DWORD_PTR)KLH_VA(KLE_ORDER))((void *)(DWORD_PTR)e->soldier, 0, p, 0, 1, 0);
    QueryPerformanceCounter(&t1);
    ms = (double)(t1.QuadPart - t0.QuadPart) * 1000.0 / (double)kle_order_f.QuadPart;
    kle_order_at = GetTickCount(); InterlockedIncrement(&kle_order_n);
    if (ms > kle_order_ms_max) kle_order_ms_max = ms;
    if (kltr.on) { float g2[3]; if (!kle_block(e->soldier, g2)) memcpy(g2, want, 12); kltr_order(e->rec, want, g2, 1); }
    if (ms > 15.0) klog("escort: SLOW ORDER: record %d to (%.0f, %.0f, %.0f) took %.1f ms inside the game's order routine", e->rec, want[0], want[1], want[2], ms);
    if (!kle_block(e->soldier, got)) memcpy(got, want, 12);
    if (klh_rd(e->soldier + 0x4fc, &soft, 1) && soft && !e->told_soft++)
        klog("escort: record %d: the game took an order as 'he is there already' ([soldier+0x4fc] = 1): a waiting step of its route chain ends now (said once per escort)", e->rec);
    return 1;
}
static int kle_order(struct kle_e *e, const float want[3], float got[3], char why[100]) { return kle_order2(e, want, got, why, kle.dry); }

/* the rules' own boarding place: boarding object + 500 along its x axis (0x8faf72..0x8fafe6) */
static int kle_boarding(DWORD rules, float out[3])
{
    DWORD obj, node; float p[3], x[3];
    if (!(obj = klh_rd32(rules + 0x1e0)) || !(node = klh_rd32(obj + 4)) || !kle_node(node, p, x)) return 0;
    out[0] = p[0] + 500.0f * x[0]; out[1] = p[1] + 500.0f * x[1]; out[2] = p[2] + 500.0f * x[2];
    return kle_ok3(out);
}

static void kle_pick(const struct klb_snap *s, const float hp[3], DWORD now)
{
    struct { int rec; float d; DWORD actor, soldier; } c[KLB_NREC], t; int nc = 0, i, k, slot, pool; char why[100]; float bp[3], blk[3];
    for (slot = 0; slot < kle.n && kle_r.e[slot].mode; slot++) ;
    if (slot >= kle.n) return;
    for (i = 0; i < s->n; i++) {
        if (!s->r[i].used || !(s->r[i].flags & 1) || kle_r.used[i]) continue;
        if (!kle_bot(s, i, &c[nc].actor, &c[nc].soldier, bp, why)) continue;
        c[nc].rec = i; c[nc].d = kle_dist(bp, hp); nc++;
    }
    if (!nc) {
        if (!kle_r.told_none++) klog("escort: no AI heister can be chosen yet (in play, not a traitor, with a soldier that takes orders): trying again");
        return;
    }
    for (i = 1; i < nc; i++) for (k = i; k > 0 && c[k].d < c[k - 1].d; k--) { t = c[k]; c[k] = c[k - 1]; c[k - 1] = t; }
    pool = nc < kle.n + 2 ? nc : kle.n + 2;   /* at random among the nearest Escort + 2: at the start they stand in one row */
    k = -1;
    if (kle.record >= 0 && !kle_r.picked) for (i = 0; i < nc; i++) if (c[i].rec == kle.record) k = i;
    if (k < 0) { klb_seed = klb_seed * 1103515245u + 12345u; k = (int)((klb_seed >> 16) % (DWORD)pool); }
    memset(&kle_r.e[slot], 0, sizeof kle_r.e[slot]);
    kle_r.e[slot].rec = c[k].rec; kle_r.e[slot].mode = 1; kle_r.e[slot].actor = c[k].actor; kle_r.e[slot].soldier = c[k].soldier;
    kle_r.used[c[k].rec] = 1; kle_r.picked++;
    if (kle_block(c[k].soldier, blk) && (blk[0] || blk[1] || blk[2])) { memcpy(kle_r.e[slot].route, blk, 12); kle_r.e[slot].have_route = 1; }
    else blk[0] = blk[1] = blk[2] = 0;
    klog("escort: record %d (actor %08lx, soldier %08lx) chosen%s: %.1f m from you, %d bot(s) could be; its place now (%.0f, %.0f, %.0f)%s; it is called when you are more than %.0f m from it%s",
         c[k].rec, c[k].actor, c[k].soldier, kle.record == c[k].rec ? " (EscortRecord)" : "", c[k].d / 100, nc, blk[0], blk[1], blk[2], kle_r.e[slot].have_route ? "" : " = none yet", kle.far_ / 100, kle.dry ? " - DRY RUN: nothing is called" : "");
    (void)now;
}

/* a place EscortSide from the human towards the bot, the second escort 70 degrees round; the human's height */
static void kle_place(const float hp[3], const float bp[3], int slot, int direct, float out[3])
{
    float dx = bp[0] - hp[0], dz = bp[2] - hp[2], l = (float)sqrt(dx * dx + dz * dz), c = 1, sn = 0, x;
    memcpy(out, hp, 12);
    if (direct || kle.side <= 0 || l < 1.0f) return;
    dx /= l; dz /= l;
    if (slot) { c = 0.342f; sn = 0.940f; }
    x = dx * c - dz * sn; dz = dz * c + dx * sn; dx = x;
    out[0] = hp[0] + dx * kle.side; out[2] = hp[2] + dz * kle.side;
}

static void kle_hold(const struct klb_snap *s, int slot, const float hp[3], const float bp[3], DWORD now)
{
    struct kle_e *e = &kle_r.e[slot]; float cur[3], want[3], got[3], d = kle_dist(bp, hp), dt; char why[100]; int direct = 0, r;
    if (kle_block(e->soldier, cur)) {
        if (e->have_target && kle_dist(cur, e->target) > 5.0f) {             /* somebody else gave an order since ours */
            if (kle_dist(cur, e->target) > KLE_ROUTE) {
                memcpy(e->route, cur, 12); e->have_route = 1; e->have_target = 0;
                if (kle.log >= 2) klog("escort: record %d: its route chain ordered it to (%.0f, %.0f, %.0f); it goes there until you are %.0f m from it", e->rec, cur[0], cur[1], cur[2], kle.far_ / 100);
            } else memcpy(e->target, cur, 12);                               /* a tactic of its own moved the place a little: still our hold */
        } else if (!e->have_target && (cur[0] || cur[1] || cur[2])) { memcpy(e->route, cur, 12); e->have_route = 1; }
    }
    if (!(d > kle.far_)) return;                                             /* near enough (a NaN is not far) */
    if (e->order_at && now - e->order_at < kle.every) return;
    if (e->have_target) {
        dt = kle_dist(bp, e->target);
        if (kle_dist(hp, e->target) <= kle.retarget) {                       /* the place is still beside the human: he is on his way */
            if (e->direct || now - e->order_at < 12000 || dt < e->d_order - 100.0f) return;
            direct = 1;                                                      /* 12 s and not 1 m nearer: the human's own place, once */
        }
    }
    kle_place(hp, bp, slot, direct, want);
    kltr_set("escort", "follow: keep beside the human", -1);
    r = kle_order(e, want, got, why);
    if (!r) {
        if (!e->log_at || now - e->log_at >= 5000) { e->log_at = KLB_T(now); klog("escort: record %d NOT re-pointed: %s", e->rec, why); }
        e->order_at = KLB_T(now);
        return;
    }
    e->order_at = KLB_T(now); e->orders++; e->direct = direct; e->d_order = kle_dist(bp, got);
    if (r == 1) { memcpy(e->target, got, 12); e->have_target = 1; }
    if (kle.log >= 2 || !e->log_at || now - e->log_at >= 5000) {
        klog("escort: record %d %s: you are %.1f m away at (%.0f, %.0f, %.0f); place asked (%.0f, %.0f, %.0f)%s, the game set (%.0f, %.0f, %.0f); %d order(s) since the last line; its route place (%.0f, %.0f, %.0f)%s",
             e->rec, r == 2 ? "WOULD be re-pointed (dry run)" : "re-pointed", d / 100, hp[0], hp[1], hp[2], want[0], want[1], want[2], direct ? " = where you stand (it did not get nearer in 12 s)" : "",
             got[0], got[1], got[2], e->orders, e->route[0], e->route[1], e->route[2], e->have_route ? "" : " = none seen");
        e->log_at = KLB_T(now); e->orders = 0;
    }
    (void)s;
}

/* why: 1 the human is out of play, 2 the vehicle, 3 the human's stage */
static void kle_release(const struct klb_snap *s, int slot, int reason, DWORD now)
{
    struct kle_e *e = &kle_r.e[slot]; const struct klb_rec *r = &s->r[e->rec]; float bd[3], got[3]; char why[100], what[80]; int waiting = s->veh == 3 || s->veh == 4, k;
    if (reason == 1) snprintf(what, sizeof what, "you are %s", s->human >= 0 && s->r[s->human].status == 4 ? "aboard" : "out of play");
    else if (reason == 2) snprintf(what, sizeof what, "the vehicle %s, state %u", waiting ? "waits" : "comes", s->veh);
    else snprintf(what, sizeof what, "you are at heist stage %u", s->human >= 0 ? s->r[s->human].stage : 0);
    e->mode = 2;
    if (waiting) {
        e->mode = 3;
        if (r->stage >= 3) { klog("escort: record %d released (%s): it is at stage 3, its own board tactic takes it aboard", e->rec, what); return; }
        if (!kle.board) { klog("escort: record %d released (%s): EscortBoard=0, it is left where it is", e->rec, what); return; }
        if (!kle_boarding(s->rules, bd)) { klog("escort: record %d released (%s): the boarding place cannot be read, nothing is called", e->rec, what); return; }
        kltr_set("escort", "released: to the boarding place", -1);
        k = kle_order(e, bd, got, why);
        if (k) klog("escort: record %d released (%s): %s to the boarding place (%.0f, %.0f, %.0f), the game set (%.0f, %.0f, %.0f); it is at stage %u", e->rec, what, k == 2 ? "WOULD be sent (dry run)" : "sent", bd[0], bd[1], bd[2], got[0], got[1], got[2], r->stage);
        else klog("escort: record %d released (%s): NOT sent to the boarding place: %s", e->rec, what, why);
        return;
    }
    if (e->have_target && e->have_route) {
        kltr_set("escort", "released: back to its route place", -1);
        k = kle_order(e, e->route, got, why);
        if (k) klog("escort: record %d released (%s): %s to its route place (%.0f, %.0f, %.0f), the game set (%.0f, %.0f, %.0f)", e->rec, what, k == 2 ? "WOULD go back (dry run)" : "back", e->route[0], e->route[1], e->route[2], got[0], got[1], got[2]);
        else klog("escort: record %d released (%s): NOT sent back to its route place: %s", e->rec, what, why);
    } else klog("escort: record %d released (%s): %s", e->rec, what, e->have_target ? "no route place was seen, it stays where it is until its chain orders it" : "its route chain's order is the one it has");
    e->have_target = 0;
    (void)now;
}

/* BoardAll, every pass of a round: where each AI heister in play stands and what it has, and since when neither
   has changed. Reads only. */
static void kle_all_track(const struct klb_snap *s, DWORD now)
{
    int i; DWORD node; float p[3];
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i];
        if (r->used && r->actor != kle_r.all_actor[i]) {                       /* another member in this record: nothing of the old one counts */
            kle_r.all_actor[i] = r->actor; kle_r.all_seen[i] = 0; kle_r.all_raised[i] = 0; kle_r.all_told[i] = 0; kle_r.all_visit[i] = 0;
        }
        if (!r->used || !(r->flags & 1) || r->status || !r->actor || klh_rd32(r->actor) != KLB_ACTOR_VT
            || !(node = klh_rd32(r->actor + 4)) || !kle_node(node, p, 0)) { kle_r.all_seen[i] = 0; continue; }
        if (!kle_r.all_seen[i] || kle_dist(p, kle_r.all_pos[i]) > 100.0f || r->money != kle_r.all_money[i]) {
            memcpy(kle_r.all_pos[i], p, 12); kle_r.all_money[i] = r->money; kle_r.all_since[i] = now; kle_r.all_seen[i] = 1;
        }
    }
}

/* BoardAll: the vehicle waits - a HELD AI heister gets heist stage 3 (the key's text at the top says why and what
   'held' is). The byte is the whole of it by default: the game's own tests then stop the loot tactic and start the
   board tactic. BoardAllOrder=1 adds the order to the rules' boarding place, once per visit, tried again every pass
   until kle_bot allows it. Never: a bot at stage 0 (the loot tactic is off for it, 0x4519d4, and the byte would switch
   it ON between two visits), a bot that reached 3 by itself, a traitor, anybody who was an escort this round
   (kle_release and the escort loop send that one), a record that changed since the snapshot. */
static void kle_board_all(const struct klb_snap *s, DWORD now)
{
    int i, k, have_bd; DWORD actor, soldier; float bp[3], bd[3], got[3]; char w[100]; struct kle_e t;
    have_bd = kle_boarding(s->rules, bd);
    if (kle.all_order && !have_bd && kle_r.told_nobd != kle_r.visit) {
        kle_r.told_nobd = kle_r.visit;
        klog("board: visit %d: the boarding place cannot be read (rules +0x1e0 = %08lx): the stage is still written, nobody is ordered", kle_r.visit, klh_rd32(s->rules + 0x1e0));
    }
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i];
        if (!r->used || !(r->flags & 1) || (r->flags & 2) || r->status || kle_r.used[i]) continue;
        if (!kle_r.all_raised[i]) {
            BYTE fl = 0, st = 0, cur = 3; DWORD stood;
            if (r->stage < 1 || r->stage >= 3) continue;
            if (!kle_r.all_seen[i]) {                                         /* its place cannot be read: not judged */
                if (!(kle_r.all_told[i] & 4)) { kle_r.all_told[i] |= 4; klog("board: record %d (stage %u): the vehicle waits but its place cannot be read: it is not judged", i, r->stage); }
                continue;
            }
            stood = now - kle_r.all_since[i];
            if (kle.all_still && stood < kle.all_still) continue;             /* it moves or it earns: not held */
            if (kle.all_stage && !kle.dry) {
                if (!klb_still(s, i, &fl, &st) || st || (fl & 2) || !klh_rd(r->at + 0x78, &cur, 1)) {            /* gone, aboard, dead or turned since the snapshot */
                    if (!(kle_r.all_told[i] & 8)) { kle_r.all_told[i] |= 8; klog("board: record %d: its record changed since this pass read it: nothing is written", i); }
                    continue;
                }
                if (cur < 3 && !klb_put8(r->at + 0x78, 3, "crew record: heist stage 3 (a bot held by loot while the vehicle waits)")) {
                    if (!(kle_r.all_told[i] & 1)) { kle_r.all_told[i] |= 1; klog("board: record %d (stage %u): the stage byte was not written: it is left alone", i, r->stage); }
                    continue;
                }
                kle_r.all_raised[i] = 1;
            } else kle_r.all_raised[i] = 2;
            klog("board: record %d (stage %u) at (%.0f, %.0f, %.0f): held for %lu s with $%lu: the vehicle waits (state %u): %s", i, r->stage,
                 kle_r.all_pos[i][0], kle_r.all_pos[i][1], kle_r.all_pos[i][2], stood / 1000, r->money, s->veh,
                 !kle.all_stage ? "BoardAllStage=0, the stage is left" : kle.dry ? "heist stage WOULD be set to 3 (dry run)" : "heist stage set to 3");
        }
        if (!kle.all_order || !have_bd || kle_r.all_visit[i] == kle_r.visit || r->stage >= 3 && kle_r.all_raised[i] != 1) continue;
        if (!kle_bot(s, i, &actor, &soldier, bp, w)) {
            if (!(kle_r.all_told[i] & 2)) { kle_r.all_told[i] |= 2; klog("board: record %d: no order to the boarding place yet: %s (tried again every pass of a visit)", i, w); }
            continue;
        }
        kle_r.all_visit[i] = kle_r.visit;
        memset(&t, 0, sizeof t); t.rec = i; t.actor = actor; t.soldier = soldier; t.told_soft = 1;      /* kle_order's 'soft' line is worded for an escort */
        kltr_set("board", "BoardAllOrder: to the boarding place", -1);
        kle_gap_exempt = 1; k = kle_order(&t, bd, got, w); kle_gap_exempt = 0;
        if (k) klog("board: record %d at (%.0f, %.0f, %.0f): %s to the boarding place (%.0f, %.0f, %.0f), the game set (%.0f, %.0f, %.0f); visit %d of the vehicle",
                    i, bp[0], bp[1], bp[2], k == 2 ? "WOULD be sent (dry run)" : "sent", bd[0], bd[1], bd[2], got[0], got[1], got[2], kle_r.visit);
        else klog("board: record %d: NOT sent to the boarding place: %s", i, w);
    }
}

/* ---------------------------------------------------------------- FollowOut (section 3) */

/* Is the local player a heister? [player + 0x273c] == 2 (a policeman after his death is 3: klfed.c). Without the node
   test of kle_human: a player aboard the vehicle must still count. */
static int kle_criminal(void)
{
    DWORD gd, pl; BYTE sel = 0xff, type = 0;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel > 3) return 0;
    return (pl = klh_rd32(gd + 0x828 + 4 * sel)) != 0 && klh_rd(pl + 0x273c, &type, 1) && type == 2;
}

/* THE ESCAPE VEHICLE'S HEALTH (section 3 c2; EXE). [rules+0x1e4] is the vehicle the rules use (slot 32 = 0x54b1a0; set
   from [score+0x5c] by slot 89, 0x49d18d). For the key-framed van it is a group; the game finds the health under it
   as the HUD's bar does (ZFAEscapeDisplay 0x793b7e..0x793c60, the scripted hits 0x6db841..): [group+0x40] = the first
   child's entity slot, [slot+0x60] = its object, word [slot+0x5e] = the next sibling's slot number (0 = none; the slot
   is table + 0x80 * number - 0x80). The child that is a ZAnimatedVehicle holds
       +0x14 health  +0x18 a quarter of the maximum (slot 82, 0x65322a: max * 0.25, double 0xb293f0)
       +0x1c..+0x1e  'Activate_DamageFX_01 / 02 / 03' was sent (health <= half, <= a quarter, <= 0: slot 87, 0x8fa4f5..)
       +0x21 Invulnerable  +0x22 its frame update runs
   -> 1 = found, 0 = the children were walked and none is one (a helicopter / a car), -1 = something could not be read.
   Reads only. */
struct kle_veh { DWORD obj; float hp, max; BYTE fx[3], inv, upd; };
static char kle_veh_err[96];           /* why the last kle_veh_read gave -1 (2026-10-18, Vault L30 visit 1: no reason was logged) */
static int kle_veh_read(DWORD rules, struct kle_veh *v)
{
    DWORD g = 0, vt = 0, slot = 0, tab = 0, p, c, o = 0; WORD next = 0; int k; float f[2]; BYTE b[7];
    memset(v, 0, sizeof *v); kle_veh_err[0] = 0;
    if (!klh_rd(rules + 0x1e4, &g, 4) || !g || !klh_rd(g, &vt, 4)) { _snprintf(kle_veh_err, sizeof kle_veh_err - 1, "[rules+0x1e4] %08lx unreadable", g); return -1; }
    if (vt == KLE_VEH_VT) o = g;
    else {
        if (!klh_rd(g + 0x40, &slot, 4) || !(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) { _snprintf(kle_veh_err, sizeof kle_veh_err - 1, "group %08lx (vt %08lx): its first slot / the entity table unreadable", g, vt); return -1; }
        for (k = 0; k < 64; k++) {
            if (slot < tab || slot - tab >= 0x10000u * 0x80 || ((slot - tab) & 0x7f)) { _snprintf(kle_veh_err, sizeof kle_veh_err - 1, "group %08lx (vt %08lx): child %d slot %08lx not in the table", g, vt, k, slot); return k ? -1 : 0; }      /* no slot of the table: the first = this object has no children as a group has them */
            if (!klh_rd(slot + 0x60, &c, 4) || !klh_rd(slot + 0x5e, &next, 2)) { _snprintf(kle_veh_err, sizeof kle_veh_err - 1, "group %08lx: child %d slot %08lx unreadable", g, k, slot); return -1; }
            if (c && klh_rd32(c) == KLE_VEH_VT) { o = c; break; }
            if (!next) return 0;
            slot = tab + (DWORD)next * 0x80 - 0x80;
        }
        if (!o) { _snprintf(kle_veh_err, sizeof kle_veh_err - 1, "group %08lx (vt %08lx): 64 children and no end", g, vt); return -1; }                    /* 64 children and no end: not the list this build knows */
    }
    if (!klh_rd(o + 0x14, f, sizeof f) || !klh_rd(o + 0x1c, b, sizeof b) || !klb_finite(f[0]) || !klb_finite(f[1]) || !(f[1] > 0) || f[0] < 0 || f[0] > f[1] * 4 + 1) { _snprintf(kle_veh_err, sizeof kle_veh_err - 1, "vehicle %08lx: health %.1f / quarter-max %.1f not sane", o, f[0], f[1]); return -1; }
    v->obj = o; v->hp = f[0]; v->max = f[1] * 4; memcpy(v->fx, b, 3); v->inv = b[5]; v->upd = b[6];
    return 1;
}

/* the shield off: the byte back to 0 - only if the object is still a ZAnimatedVehicle and the byte still the 1 we wrote */
static void kle_shield_off(const char *why, DWORD now)
{
    DWORD o = kle_sh.obj; BYTE b = 0; float f[2] = { 0, 0 };
    if (!o) return;
    kle_sh.obj = 0;
    if (klh_rd32(o) != KLE_VEH_VT || !klh_rd(o + KLE_VEH_INV, &b, 1)) { klog("follow: shield: off (%s): the vehicle's health object %08lx can no longer be read: nothing is written back", why, o); return; }
    if (b != 1) { klog("follow: shield: off (%s): the 'Invulnerable' byte of %08lx is %u, no longer the 1 this file wrote: left alone", why, o, b); return; }
    klh_rd(o + 0x14, f, sizeof f);
    if (klb_put8(o + KLE_VEH_INV, 0, "escape vehicle: Vulnerable again (the hold's shield is taken off)"))
        klog("follow: shield: off (%s): the vehicle's 'Invulnerable' byte [%08lx+0x%x] 1 -> 0 after %.1f s; it takes hits again at health %.0f of %.0f (%.0f %%; the game's scripted hits went on under the shield, down to a tenth at the lowest)", why, o, KLE_VEH_INV, (now - kle_sh.at) / 1000.0, f[0], f[1] * 4, f[1] > 0 ? 25.0f * f[0] / f[1] : 0.0f);
    else klog("follow: shield: off (%s): the 'Invulnerable' byte of %08lx could NOT be written back: THE VEHICLE STAYS INVULNERABLE until the level is loaded again", why, o);
}

/* May the driver be held now? Asked by BOTH holds (FollowOutHold here, WaitForYouHold in klmove.c) right before the
   timer is written. WHY (live runs N1 / N1b, 2026-10-11): a vehicle held 15 s was DESTROYED 20.9 / 21.3 s after it
   began to wait, and the rules then kill everybody aboard, the human too (slot 94 = 0x6a1100, grade 2: state 6, slot
   11 for a human and slot 16 for an AI member with status 4). Stock never lets it stand that long: 8 s + the 8.4 s
   of the drive-out. So with FollowOutShield 1 / 2 (default 2) the vehicle's own 'Invulnerable' byte is set from the
   first held second on - one byte of the level's ZAnimatedVehicle, what its 'Invulnerable' message writes - and
   kle_veh_pass takes it back. -> 1 = hold (note[200] says what was done), 0 = do not (why[200]).
   NOT COVERED, and said in the start line: the shield goes on at the first timer write, about 6 s into the wait
   (the timer falls from 8.0 to under KLE_HOLD_AT first). Until then, and at any visit that is not held, the risk is
   stock's - and stock's is not nil: U_M01.log (Hot Coffee, 2026-10-10, no hold, nobody aboard) has 'van 4 8.0s' and
   1.3 s later 'van 6 9.9s' on a SECOND visit. */
static int kle_hold_guard(const struct klb_snap *s, DWORD now, int dry, char *why, char *note)
{
    struct kle_veh v; int k; BYTE kind = 0xff;
    why[0] = note[0] = 0;
    if (!kle.fo_shield) { strcpy(note, "NO SHIELD (FollowOutShield=0): a vehicle that stands longer than stock's 8 s can be destroyed with everybody aboard"); return 1; }
    if (kle.vb && !kle.vb_dry && kle_vb.open && kle_vb.rules == s->rules && kle_vb_aboard(s) == 0) {      /* [VanBlow]: an EMPTY vehicle is left vulnerable so that it can blow up */
        strcpy(why, "VanBlow: nobody is aboard, the vehicle is left vulnerable (it can be destroyed) and is not held or shielded until somebody boards"); return 0;
    }
    k = kle_veh_read(s->rules, &v);
    if (k < 0) { _snprintf(why, 199, "the vehicle's health object cannot be read (%s), so it cannot be shielded - an unshielded hold got the vehicle destroyed with everybody aboard (FollowOutShield=0 holds all the same)", kle_veh_err); why[199] = 0; return 0; }
    if (!k) {
        /* FAIL CLOSED (the review's point 2). The game's own name for the vehicle's kind is the byte [rules+0x1ec]
           (slot 95 = 0x5822d0; set by 0x42cfb0 from the class of [rules+0x1e4]: 1, 2 = two other vehicle classes, 3 =
           the third cast 0x409920, 0 = none). 3 is what the hit routine asks before it calls 'destroyed' (0x5aec7c)
           and what the state machine asks (0x55ecf4): a vehicle of kind 3 CAN be destroyed by a hit, so one whose
           health object this file's walk did not find (a derived class, another tree) is not held. */
        if (!klh_rd(s->rules + KLE_VEH_KIND, &kind, 1)) { strcpy(why, "the vehicle's kind [rules+0x1ec] cannot be read and no health object was found: it cannot be shielded"); return 0; }
        if (kind == 3) { strcpy(why, "the rules say it is the key-framed van (kind 3: a hit can destroy it) but no ZAnimatedVehicle was found under it: it cannot be shielded (FollowOutShield=0 holds all the same)"); return 0; }
        /* 2026-10-19, live run 13:29:27 (Hasta, Dead Men Escape_Chopper, BlowupChanceDefinite, 2200 hp): the comment above
           ASSUMED only kind 3 is ever destroyed. DISPROVEN: the held chopper (kind 2, 45 s hold, no shield possible) went to
           state 6 and the rules killed the 5 bots aboard. No health / damage field of a ZHeli that could stand in for the
           'Invulnerable' byte was established from kl2.exe, so nothing is written for it (GUESS: one may exist). Fallback:
           an unshieldable vehicle is NOT held, it leaves on its own timer. [Bots] FollowOutHoldUnshielded=1 = the old
           behaviour (hold all the same), for a test. */
        if (!kle.fo_unshielded) {
            snprintf(why, 199, "hold: vehicle unshieldable, not held (no ZAnimatedVehicle health object, kind %u: a helicopter or a car that takes hits and can be destroyed all the same; FollowOutHoldUnshielded=1 holds it anyway)", kind); why[199] = 0;
            return 0;
        }
        snprintf(note, 200, "the vehicle has no ZAnimatedVehicle health object and is of kind %u, not 3 (a helicopter or a car): nothing to shield, held all the same (FollowOutHoldUnshielded=1)", kind);
        return 1;
    }
    if (!(v.hp > 0)) { strcpy(why, "the vehicle's health is 0: it is destroyed"); return 0; }
    if (kle_sh.obj == v.obj && v.inv == 1) { snprintf(note, 200, "shielded since %.1f s; health %.0f of %.0f", (now - kle_sh.at) / 1000.0, v.hp, v.max); return 1; }
    if (v.inv) { snprintf(note, 200, "the level itself has the vehicle Invulnerable (byte %u): left as it is; health %.0f of %.0f", v.inv, v.hp, v.max); return 1; }
    if (dry) { snprintf(note, 200, "the vehicle WOULD be shielded (dry run); health %.0f of %.0f", v.hp, v.max); return 1; }
    if (kle_sh.obj == v.obj) {                /* ours, and the byte is 0 again (the level's 'Vulnerable' inside the last 0.5 s): set again, the shield's start stays */
        if (!klb_put8(v.obj + KLE_VEH_INV, 1, "escape vehicle: Invulnerable while the driver is held (set again)")) { strcpy(why, "the vehicle's 'Invulnerable' byte was 0 again and could not be written, so it cannot be shielded"); return 0; }
        snprintf(note, 200, "SHIELD ON AGAIN: the 'Invulnerable' byte [%08lx+0x%x] was 0 again (the level's 'Vulnerable'?), 0 -> 1; shielded since %.1f s; health %.0f of %.0f", v.obj, KLE_VEH_INV, (now - kle_sh.at) / 1000.0, v.hp, v.max);
        return 1;
    }
    if (kle_sh.obj) kle_shield_off("another vehicle is held", now);
    if (!klb_put8(v.obj + KLE_VEH_INV, 1, "escape vehicle: Invulnerable while the driver is held")) { strcpy(why, "the vehicle's 'Invulnerable' byte could not be written, so it cannot be shielded"); return 0; }
    kle_sh.obj = v.obj; kle_sh.rules = s->rules; kle_sh.at = KLB_T(now); kle_sh.told = 0;
    snprintf(note, 200, "SHIELD ON: the vehicle's 'Invulnerable' byte [%08lx+0x%x] 0 -> 1 %s (FollowOutShield=%d); health %.0f of %.0f", v.obj, KLE_VEH_INV,
             kle.fo_shield == 1 ? "until it drives out" : "until it is gone", kle.fo_shield, v.hp, v.max);
    return 1;
}

/* [VanBlow], once per 0.5 s pass while the vehicle is in state 3..5 (see the block at kle_vb): the empty-vehicle test, the shield's
   release, and HealthMax at the first pass of a wait. */
static void kle_vb_pass(const struct klb_snap *s, DWORD now, int edge)
{
    int n = kle_vb_aboard(s); DWORD t = KLB_T(now); struct kle_veh v;
    if (kle_vb.rules != s->rules) memset(&kle_vb, 0, sizeof kle_vb), kle_vb.rules = s->rules;
    kle_vb.aboard = n;
    if (edge && s->veh <= 4 && kle.vb_hp > 0 && !kle_vb.hp_done && kle_veh_read(s->rules, &v) > 0) {
        kle_vb.hp_done = 1;
        if (v.hp > kle.vb_hp) {
            float hp = kle.vb_hp, q = kle.vb_hp / 4.0f;
            if (kle.vb_dry) klog("vanblow: HealthMax=%.0f: the vehicle's health %.0f of %.0f WOULD be lowered to %.0f (dry run)", kle.vb_hp, v.hp, v.max, hp);
            else if (klh_data((void *)(DWORD_PTR)(v.obj + 0x14), &hp, 4, "escape vehicle: health lowered (VanBlow HealthMax)") && klh_data((void *)(DWORD_PTR)(v.obj + 0x18), &q, 4, "escape vehicle: quarter-max lowered (VanBlow HealthMax)"))
                klog("vanblow: HealthMax=%.0f: the vehicle's health %.0f of %.0f lowered to %.0f of %.0f ([%08lx+0x14] and +0x18; the +0x18 write is a GUESS - watch the 'follow: vehicle:' lines for the fire at half / a quarter)", kle.vb_hp, v.hp, v.max, hp, kle.vb_hp, v.obj);
            else klog("vanblow: HealthMax=%.0f: the health of %08lx could NOT be written", kle.vb_hp, v.obj);
        }
    }
    if (n) {
        kle_vb.empty_at = 0;
        if (kle_vb.open) { kle_vb.open = 0; if (kle.vb_log) klog("vanblow: %d aboard again (state %u): the vehicle may be shielded again", n, s->veh); }
        return;
    }
    if (!kle_vb.empty_at) kle_vb.empty_at = t;
    if (t - kle_vb.empty_at < kle.vb_delay) return;
    if (!kle_vb.open) {
        kle_vb.open = 1;
        if (kle.vb_log) klog("vanblow: nobody aboard for %.1f s (state %u): the vehicle is left VULNERABLE%s - shot to 0 it blows up (fire, then the blast); it is shielded again when somebody boards", kle.vb_delay / 1000.0, s->veh, kle.vb_dry ? " (DRY RUN: the shield stays)" : "");
    }
    if (!kle.vb_dry && kle_sh.obj && kle_sh.rules == s->rules) kle_shield_off("VanBlow: nobody is aboard, so the vehicle may be destroyed", now);
}

/* every 0.5 s pass of a round, before FollowOut: the shield's upkeep and release, and (FollowOut on) the vehicle's
   health in the log - at the wait, at the drive-out, whenever it fell by a twentieth of the maximum (1 s apart at
   least), and when the vehicle is destroyed. The log is what tells steady fire from one step. */
static void kle_veh_pass(const struct klb_snap *s, DWORD now)
{
    struct kle_veh v; BYTE prev = kle_r.vh_prev, b = 0; int k, live = s->veh >= 3 && s->veh <= 5, edge = s->veh != prev;
    const struct klb_rec *h = s->human >= 0 ? &s->r[s->human] : 0; float timer = klb_finite(s->timer) ? s->timer : -1.0f, since;
    /* what the shield WAS when this pass began, before the release below takes it off (the review's MUST: the
       DESTROYED line must be able to say that the vehicle went with our shield on): sh_was = our object of this
       round, sh_byte = its 'Invulnerable' byte as this pass found it (0xff = it could not be read) */
    DWORD sh_was = kle_sh.obj && kle_sh.rules == s->rules ? kle_sh.obj : 0; BYTE sh_byte = 0xff; float sh_for = sh_was ? (now - kle_sh.at) / 1000.0f : 0; char tail[240];
    if (sh_was && (klh_rd32(sh_was) != KLE_VEH_VT || !klh_rd(sh_was + KLE_VEH_INV, &sh_byte, 1))) sh_byte = 0xff;
    kle_r.vh_prev = s->veh;
    if (kle.vb) {
        if (s->veh >= 3 && s->veh <= 5) kle_vb_pass(s, now, edge && (prev < 3 || prev > 5));
        else if (edge && s->veh == 6 && prev >= 3 && prev <= 5 && kle.vb_log)
            klog("vanblow: the vehicle BLEW UP (state 6; it was in state %u) with %d aboard at the last pass%s", prev, kle_vb.aboard, kle_vb.aboard ? " - they are killed by the rules (slot 94, grade 2); the shield should have prevented this: tell the track" : " - nobody was in it");
        if (s->veh < 3 || s->veh > 5) kle_vb.open = 0;
    }
    if (kle_sh.obj) {
        if (s->rules != kle_sh.rules) kle_shield_off("another round object", now);
        else if (!(s->veh == 3 || s->veh == 4 || (s->veh == 5 && kle.fo_shield != 1)))
            kle_shield_off(s->veh == 5 ? "it drives out, and FollowOutShield=1 leaves the drive-out to the game" : s->veh == 6 ? "the vehicle is destroyed" : "the vehicle is gone", now);
        else if (klh_rd32(kle_sh.obj) != KLE_VEH_VT || !klh_rd(kle_sh.obj + KLE_VEH_INV, &b, 1)) kle_shield_off("its health object can no longer be read", now);
        else if (!b) {                        /* the level sent 'Vulnerable' meanwhile: ours again while the hold's reason lasts */
            k = klb_put8(kle_sh.obj + KLE_VEH_INV, 1, "escape vehicle: Invulnerable while the driver is held (set again)");
            if (!kle_sh.told++) klog("follow: shield: the vehicle's 'Invulnerable' byte was 0 again (the level's own 'Vulnerable' message?): %s (said once)", k ? "set to 1 again" : "it could NOT be written");
        }
    }
    /* the wait's begin: only FollowOut sees it for sure (with WaitForYouHold alone this pass does not run before the
       shield is set: no begin is known then, and the lines say -1.0 s) */
    if ((s->veh == 3 || s->veh == 4) && prev != 3 && prev != 4) { kle_r.vh_wait_at = kle.fo ? KLB_T(now) : 0; kle_r.vh_said = -1; kle_r.vh_told = 0; }
    /* FollowOutShield=3 (owner 2026-10-11: 'all the police outside the vault shoot the van straight away'; the club's first full run
       lost its van, state 3 -> 6, with two AI heisters aboard and no hold): the shield goes on in the first pass of EVERY wait, held or
       not, human aboard or not, and stays until the vehicle is gone, as with 2. Less risk than stock on purpose. */
    /* VanBlow review fix: a van that was left vulnerable while empty and is boarded only in the drive-out (state 5) is shielded again there too (the old shield covered the drive-out) */
    if (kle.fo_shield == 3 && (s->veh == 3 || s->veh == 4 || (s->veh == 5 && kle.vb && !kle.vb_dry && kle_vb.aboard > 0)) && !kle_sh.obj && !(kle.vb && !kle.vb_dry && kle_vb.open)) {
        char why3[200], note3[200]; static DWORD said3; int ok3;
        ok3 = kle_hold_guard(s, now, kle.fo_dry, why3, note3);
        if (ok3 && (kle_sh.obj || now - said3 > 30000)) { said3 = now; klog("follow: shield: the vehicle waits (state %u) and FollowOutShield=3 shields every wait: %s", s->veh, note3); }
        else if (!ok3 && now - said3 > 30000) { said3 = now; klog("follow: shield: FollowOutShield=3 but the waiting vehicle is NOT shielded: %s", why3); }
    }
    /* DESTROYED is said whenever our shield was on this round, FollowOut or not (klmove.c's hold); the rest is FollowOut's log */
    if (!kle.fo && !(sh_was && edge && s->veh == 6)) return;
    if (!live && !(edge && s->veh == 6)) return;
    tail[0] = 0;
    if (edge && s->veh == 6) {
        if (sh_was && sh_byte == 1)
            snprintf(tail, sizeof tail, " - ALTHOUGH THIS FILE'S SHIELD WAS ON (the 'Invulnerable' byte of %08lx read 1 at this pass, set %.1f s ago): SOMETHING ELSE THAN A HIT TOOK ITS HEALTH, the cause read in the exe is not the whole of it (tell the track)", sh_was, sh_for);
        else if (sh_was)
            snprintf(tail, sizeof tail, " - this file's shield was set %.1f s ago but the 'Invulnerable' byte of %08lx read %u at this pass (0 = the level's 'Vulnerable' inside the last 0.5 s, 255 = unreadable): a hit could get through", sh_for, sh_was, sh_byte);
    }
    k = kle_veh_read(s->rules, &v);
    if (k <= 0) {
        if (!kle_r.vh_told++) klog("follow: vehicle: %s (state %u)", k ? "its health object cannot be read" : "it has no ZAnimatedVehicle health object (a helicopter or a car): no health is logged, no shield is needed", s->veh);
        if (edge && s->veh == 6) klog("follow: vehicle: DESTROYED (state 6): the rules kill everybody aboard (slot 94, grade 2)%s", tail);
        return;
    }
    since = kle_r.vh_wait_at ? (now - kle_r.vh_wait_at) / 1000.0f : -1.0f;
    if (edge && s->veh == 6) {
        if (!tail[0] && v.inv) snprintf(tail, sizeof tail, " - ALTHOUGH ITS 'Invulnerable' BYTE IS %u (the level's, not this file's): something else than a hit took its health (tell the track)", v.inv);
        klog("follow: vehicle: DESTROYED (state 6) %.1f s after it began to wait: health %.0f of %.0f; the line before said %.0f, %.1f s ago. The rules kill everybody aboard (0x5aec7c -> slot 84 -> slot 94 = 0x6a1100, grade 2)%s",
             since, v.hp, v.max, kle_r.vh_said, kle_r.vh_said_at ? (now - kle_r.vh_said_at) / 1000.0 : -1.0, tail);
        if (!kle.fo) return;
    }
    else if ((edge && (s->veh == 5 || prev < 3 || prev > 5)) || kle_r.vh_said < 0 || (kle_r.vh_said - v.hp >= v.max / 20 && now - kle_r.vh_said_at >= 1000))
        klog("follow: vehicle: %s (state %u, timer %.1f s, %.1f s after it began to wait): health %.0f of %.0f (%.0f %%), %s; you are %s", edge && s->veh == 5 ? "it drives out" : edge ? "it waits" : "hit", s->veh, timer, since, v.hp, v.max,
             100.0f * v.hp / v.max, kle_sh.obj == v.obj ? "SHIELDED by this file" : v.inv ? "Invulnerable by the level" : "takes hits", h && h->status == 4 ? "aboard" : h && !h->status ? "in play" : "out");
    else return;
    kle_r.vh_said = v.hp; kle_r.vh_said_at = KLB_T(now);
}

/* FollowOutSpare: the vehicle drives out (state 5). The rules have just set, for every slot, the time at which the
   record it names is shot if it is an AI member still in play (0x8fab77..0x8fac9a; read by 0x74b8a2..0x74b99a while the
   human's client flag 0x20 is set). All of them are put off to a time that never comes - ONE block of the rules
   object, written only when it looks like that table. The table has three honest shapes:
     - scheduled (at this departure, or at an earlier one of this round object): every time a value of the game's
       clock that is not more than 16 s ahead (the latest the game sets is 9.3 s), the slot bytes a shuffle of
       0..slots-1 (0x8fabfd writes k, 0x7f87c0 swaps);
     - never used: all TWELVE times 0, as the constructor leaves them (0x8355db..0x83561d). It writes NOTHING at
       +0xf1c: the slot bytes are then what the heap held, and the game's loop skips one out of range (0x74b91e
       `cmp edi, [esi+0x354] / jge`). So the bytes are not judged in this shape (review S3: the first departure of a
       round object with the human not aboard was refused as 'not the table');
     - put off by this file: every time ours.
   Also done when the human is not aboard: no time was set then, but he can still board in the first second of
   state 5, and the loop would run on what the table held before. */
static void kle_spare(DWORD rules)
{
    struct klb_snap s; DWORD sys, tnow = 0, fl0 = 0, t[12], put[12], named = 0; BYTE slot[12]; char list[100]; long first = 0x7fffffff;
    int i, k = 0, n, due = 0, left = 0, zero = 0, shuffle = 1, dry = kle.dry || kle.fo_dry;
    if (kle_r.spare_at5) return;
    if (!klb_read(&s) || s.rules != rules || s.state != KLB_ROUND || s.veh != 5) return;
    kle_r.spare_at5 = 1;                      /* this departure is dealt with, whatever is found below */
    n = s.n;
    if (n < 1 || n > 12 || !(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) || !klh_rd(sys + 0x48, &tnow, 4) || !klh_rd(rules + KLE_KILL_TIMES, t, sizeof t)
        || !klh_rd(rules + KLE_KILL_SLOTS, slot, (SIZE_T)n) || !klh_rd(s.score + 0x1d4, &fl0, 4)) {
        klog("follow: spare: the rules' table of times cannot be read (%d record slots): nothing is written", n);
        return;
    }
    for (i = 0; i < 12; i++) if (!t[i]) zero++;                               /* 12 = the table as the constructor made it */
    for (i = 0; i < n; i++) {
        if (t[i] != KLE_KILL_NEVER && ((long)t[i] < 0 || t[i] > tnow + 16 * 1024)) {
            klog("follow: spare: rules +0x%x does not hold the table of times this build knows (slot %d: %08lx is no time of the clock, which is %08lx): nothing is written", KLE_KILL_TIMES, i, t[i], tnow);
            return;
        }
        if (slot[i] >= n || (named >> slot[i] & 1)) shuffle = 0; else named |= 1u << slot[i];
        if (t[i] != KLE_KILL_NEVER) { due++; if (t[i] && (long)(t[i] - tnow) < first) first = (long)(t[i] - tnow); }
        put[i] = KLE_KILL_NEVER;
    }
    if (!due) return;                         /* put off already, at an earlier departure of this round object */
    if (!shuffle && zero != 12) {             /* times of the clock, but the bytes beside them name no record each: not the table */
        klog("follow: spare: rules +0x%x / +0x%x do not hold the table this build knows (the %d slot bytes %02x %02x %02x %02x .. are no shuffle of 0..%d, and the times are not the zeros of a table never used; the clock is %08lx): nothing is written",
             KLE_KILL_TIMES, KLE_KILL_SLOTS, n, slot[0], n > 1 ? slot[1] : 0, n > 2 ? slot[2] : 0, n > 3 ? slot[3] : 0, n - 1, tnow);
        return;
    }
    list[0] = 0;
    for (i = 0; i < n; i++)
        if (s.r[i].used && (s.r[i].flags & 1) && s.r[i].status == 0) { left++; if (k < (int)sizeof list - 8) k += snprintf(list + k, sizeof list - k, "%s%d", k ? " " : "", i); }
    if (!dry && !klh_data((void *)(DWORD_PTR)(rules + KLE_KILL_TIMES), put, 4 * n, "the times at which the rules shoot the crew left behind (put off)")) {
        klog("follow: spare: the rules' times could NOT be written: those left behind are shot as in stock");
        return;
    }
    if (!dry) kle_r.spare_put = 1;
    if (zero == 12) {                         /* never used: nobody was scheduled, whoever is aboard */
        if (fl0 & 0x20)
            klog("follow: spare: the vehicle drives out with you aboard, but the rules' table was never used (twelve times of 0: you boarded after it began to drive out, no time was set): it %s all the same - a slot byte the heap left could name a record: %d AI heister(s) in play%s%s%s",
                 dry ? "WOULD be put off (dry run)" : "is put off", left, left ? " (record(s) " : "", list, left ? ")" : "");
        else if (!kle_r.spare_told++)
            klog("follow: spare: the vehicle drives out without you: no time was set for this departure; the table as the round object was made (never used: times of 0, and slot bytes that are whatever the heap held - the game skips those out of range) %s in case you board in its first second (said once a round)", dry ? "WOULD be put off (dry run)" : "is put off");
    } else if (fl0 & 0x20)
        klog("follow: spare: the vehicle drives out with you aboard: the rules' times for those left behind (%d slot(s), the first due in %.1f s) %s: %d AI heister(s) in play%s%s%s", due, first / 1024.0,
             dry ? "WOULD be put off (dry run: they are shot)" : "are put off", left, left ? (dry ? " (record(s) " : " are not shot (record(s) ") : "", list, left ? ")" : "");
    else if (!kle_r.spare_told++)
        klog("follow: spare: the vehicle drives out without you: no time was set for this departure; the table of an earlier one (%d slot(s)) %s in case you board in its first second (said once a round)", due, dry ? "WOULD be put off (dry run)" : "is put off");
}

/* every pass of the tick while the vehicle waits: ONE read of its state byte. The first time is due 0.3 s after the
   change to state 5 at the earliest (8 slots), and the 500 ms pass could come later than that. */
static void kle_spare_fast(void)
{
    DWORD rules = kle_r.spare_rules; BYTE veh = 0;
    if (!klh_rd(rules + 0x1dc, &veh, 1)) { kle_r.spare_rules = 0; return; }
    if (veh == 3 || veh == 4) return;         /* it still waits */
    kle_r.spare_rules = 0;
    if (veh == 5) kle_spare(rules);
}

/* FollowOut, every pass of a round (the key's text and section 3 say why and what). */
static void kle_follow(const struct klb_snap *s, DWORD now)
{
    const struct klb_rec *h = s->human >= 0 ? &s->r[s->human] : 0; struct kle_e t; DWORD actor, soldier; BYTE prev;
    int i, k, dry = kle.dry || kle.fo_dry, waiting = s->veh == 3 || s->veh == 4, coming = s->veh == 1 || s->veh == 2, have_bd, edge_wait, edge_leave;
    int n_play = 0, n_aboard = 0, n_dead = 0, n_moving = 0, nl = 0; float bd[3] = { 0, 0, 0 }, p[3] = { 0, 0, 0 }, bp[3], got[3], cur[3], d, dmin = -1, dmax = -1, dcome = -1, timer = klb_finite(s->timer) ? s->timer : -1.0f;
    char w[100], left[100], dt[64], rg[80];

    if (kle.fo_spare) {                       /* a key of its own: before every test of FollowOut */
        if (s->veh != 5) kle_r.spare_at5 = 0;
        if (s->veh >= 1 && s->veh <= 4) kle_r.spare_put = 0;                  /* a new visit; kept through state 5 and after it, for the 'dead' lines of that departure */
        kle_r.spare_rules = waiting ? s->rules : 0;                           /* the fast pass reads the state byte from here on */
        if (s->veh == 5) kle_spare(s->rules);
    }
    if (!kle.fo || !h) return;

    /* ---- the signal: the human's own record has heist stage 3, he is a heister in play or aboard, with his money */
    if (!kle_r.fo_fired) {
        int ai = 0; float tun[4] = { 0, 0, 0, 0 }; DWORD tu;
        if (kle_r.fo_over || (h->status != 0 && h->status != 4) || h->stage < 3 || !kle_criminal()) { kle_r.fo_since = 0; return; }
        if (h->money < kle.fo_money && kle.fo_crew_money) {     /* FollowOutCrewMoney: the loyal crew's money in play counts too */
            DWORD crew = 0;
            for (i = 0; i < s->n && i < KLB_NREC; i++) { const struct klb_rec *r = &s->r[i]; if (i != s->human && r->used && (r->flags & 1) && !(r->flags & 2) && r->status == 0) crew += r->money; }
            if (h->money + crew >= kle.fo_money) {
                if (!(kle_r.fo_told & 2)) { kle_r.fo_told |= 2; klog("follow: you are at heist stage 3 with $%lu, the loyal crew in play carries $%lu: that counts (FollowOutCrewMoney=1)", h->money, crew); }
                goto money_ok;
            }
        }
        if (h->money < kle.fo_money) {
            if (!(kle_r.fo_told & 1)) { kle_r.fo_told |= 1; klog("follow: you are at heist stage 3 with $%lu, under FollowOutMoney=%lu: the crew is not called yet", h->money, kle.fo_money); }
            kle_r.fo_since = 0;
            return;
        }
      money_ok:
        if (!kle_r.fo_since) {
            kle_r.fo_since = KLB_T(now);
            if (kle.fo_after) klog("follow: you are at heist stage 3 with $%lu (vehicle state %u): the crew is called in %lu s (FollowOutAfter)", h->money, s->veh, kle.fo_after / 1000);
        }
        if (now - kle_r.fo_since < kle.fo_after) return;
        kle_r.fo_fired = KLB_T(now); kle_r.fo_veh = 0;
        for (i = 0; i < s->n && i < KLB_NREC; i++) {
            const struct klb_rec *r = &s->r[i];
            kle_r.fo_actor[i] = r->actor; kle_r.fo_did[i] = 0; kle_r.fo_pos_at[i] = 0; kle_r.fo_ocall[i] = 0; kle_r.fo_orders[i] = 0;
            if (!r->used || !(r->flags & 1)) continue;
            if (r->status >= 4 && r->status <= 6) kle_r.fo_did[i] |= 8;       /* aboard before the call: not this part's to report */
            else if (r->status) kle_r.fo_did[i] |= 0x10;                      /* dead before it */
            else if (!(r->flags & 2)) ai++;
        }
        if ((tu = klh_rd32((DWORD_PTR)KLH_VA(KLB_TUNING))) != 0) klh_rd(tu + 0x628, tun, sizeof tun);
        for (i = 0; i < 4; i++) if (!klb_finite(tun[i])) tun[i] = -1;
        klog("follow: you are at heist stage 3 (%s, $%lu); vehicle state %u, timer %.1f s: THE CREW IS CALLED - %d AI heister(s) in play that are no traitors %s heist stage 3%s%s; the tuning's vehicle times %.1f / %.1f / %.1f / %.1f s (boarding stays open in state 5 while the third minus the timer is under 1)",
             h->status == 4 ? "aboard" : "in play", h->money, s->veh, timer, ai, dry ? "WOULD get (dry run)" : "get",
             kle.fo_order ? " and, while the vehicle drives in, the order to the boarding place" : "", kle.fo_hold > 0 ? "; the driver may be held for them" : "", tun[0], tun[1], tun[2], tun[3]);
    }
    if (h->status != 0 && h->status != 4) {   /* dead, or escaped: the round is over for him */
        if (!kle_r.fo_over) {
            int esc = 0, dead = 0, play = 0, escaped = h->status == 5 || h->status == 6, out = escaped && kle_r.fo_veh == 5;      /* out: the pass before this one saw the vehicle drive out with him aboard */
            kle_r.fo_over = 1;
            for (i = 0; i < s->n && i < KLB_NREC; i++) {
                const struct klb_rec *r = &s->r[i]; BYTE did;
                if (!r->used || !(r->flags & 1)) continue;
                if (r->status == 0) play++; else if (r->status >= 4 && r->status <= 6) esc++;
                else {
                    dead++;
                    /* a bot that died since the last pass - with the human aboard, in the last half second of the
                       drive-out (review S4: the control's last death is 0.43 s before 'status6') - still gets its line */
                    did = r->actor == kle_r.fo_actor[i] ? kle_r.fo_did[i] : 0;
                    if (did & 0x10) continue;
                    kle_r.fo_actor[i] = r->actor; kle_r.fo_did[i] = (BYTE)(did | 0x10);
                    if (!(r->actor && klh_rd32(r->actor) == KLB_ACTOR_VT && kle_node(klh_rd32(r->actor + 4), p, 0))) p[0] = p[1] = p[2] = 0;
                    klog("follow: record %d%s dead %.1f s after the crew was called, at (%.0f, %.0f, %.0f); vehicle state %u, seen as the round ended for you%s", i, kle_r.used[i] ? " (an escort)" : "", (now - kle_r.fo_fired) / 1000.0, p[0], p[1], p[2], s->veh,
                         !out ? "" : kle_r.spare_put ? " - while the vehicle drove out with you, although the rules' times were put off (FollowOutSpare): not their shot" : " - LEFT BEHIND: the rules shoot whoever is not aboard while the vehicle drives out with you");
                }
            }
            klog("follow: over (you %s): of the crew %d escaped, %d dead, %d left in play", escaped ? "escaped" : "are dead", esc, dead, play);
        }
        return;
    }

    prev = kle_r.fo_veh; kle_r.fo_veh = s->veh;
    edge_wait = waiting && prev != 3 && prev != 4;
    edge_leave = s->veh == 5 && prev != 5;
    if (coming && !kle_r.fo_was_coming) { kle_r.fo_call++; for (i = 0; i < KLB_NREC; i++) kle_r.fo_did[i] &= ~0x20; }      /* the vehicle was called: a new visit */
    kle_r.fo_was_coming = coming;
    have_bd = s->veh >= 1 && s->veh <= 5 && kle_boarding(s->rules, bd);      /* [rules+0x1e0] is set from the call on (slot 89, 0x49d170) and cleared in state 0 and 7 */
    /* FollowOutStopPlace: [rules+0x1e0] is the vehicle itself, so while it drives in (state 1 / 2) the 'boarding place'
       is wherever the vehicle is on its road - Vault run N1018_L22: orders to (-4100, -11687), (-3988, -11720), then
       (-1730, -12231), (-3701, -11773), (-1880, -12166) while it parks near (627, -11233), 25-47 m on; the called crew
       walked back along the road. The place of a wait (state 3 / 4: parked) is kept, and a later drive-in of the same
       round goes by it. GUESS: the vehicle parks at the same place every visit (one road per level). The first visit
       has no kept place and goes by the vehicle as before. */
    if (kle.fo_stop && have_bd) {
        if (waiting) {
            if (!kle_r.fo_stop_have || kle_dist(kle_r.fo_stop_at, bd) > 300.0f) klog("follow: stop place: the vehicle waits at (%.0f, %.0f, %.0f): later drive-ins this round send the crew there, not to the moving vehicle (FollowOutStopPlace=1)", bd[0], bd[1], bd[2]);
            memcpy(kle_r.fo_stop_at, bd, 12); kle_r.fo_stop_have = 1;
        } else if (coming && kle_r.fo_stop_have) {
            if (kle_r.fo_stop_told != kle_r.fo_call) { kle_r.fo_stop_told = kle_r.fo_call; klog("follow: stop place: the vehicle drives in at (%.0f, %.0f, %.0f) (call %d): the crew goes by the kept stop place (%.0f, %.0f, %.0f), %.1f m on", bd[0], bd[1], bd[2], kle_r.fo_call, kle_r.fo_stop_at[0], kle_r.fo_stop_at[1], kle_r.fo_stop_at[2], kle_dist(bd, kle_r.fo_stop_at) / 100); }
            memcpy(bd, kle_r.fo_stop_at, 12);
        }
    }
    left[0] = 0;
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; BYTE *did = &kle_r.fo_did[i]; const char *esc = kle_r.used[i] ? " (an escort)" : ""; int havep; BYTE fl = 0, st = 0, curst = 3, soft = 0; char mv[64];
        if (!r->used || !(r->flags & 1)) continue;
        if (r->actor != kle_r.fo_actor[i]) {                                  /* another member in this record: nothing of the old one counts */
            kle_r.fo_actor[i] = r->actor; *did = 0; kle_r.fo_pos_at[i] = 0; kle_r.fo_moves[i] = 0; kle_r.fo_ocall[i] = 0; kle_r.fo_orders[i] = 0;
        }
        havep = r->actor && klh_rd32(r->actor) == KLB_ACTOR_VT && kle_node(klh_rd32(r->actor + 4), p, 0);
        d = havep && have_bd ? kle_dist(p, bd) : -1;
        if (d >= 0) snprintf(dt, sizeof dt, ", %.1f m from the boarding place", d / 100); else strcpy(dt, havep ? "" : " (its place cannot be read)");
        if (!havep) p[0] = p[1] = p[2] = 0;
        if (r->status >= 4 && r->status <= 6) {
            n_aboard++;
            if (!(*did & 8)) { *did |= 8; klog("follow: record %d%s %s %.1f s after the crew was called (vehicle state %u, timer %.1f s)", i, esc, r->status == 4 ? "aboard" : "escaped", (now - kle_r.fo_fired) / 1000.0, s->veh, timer); }
            continue;
        }
        if (r->status) {
            n_dead++;
            if (!(*did & 0x10)) {
                *did |= 0x10;
                klog("follow: record %d%s dead %.1f s after the crew was called, at (%.0f, %.0f, %.0f)%s; vehicle state %u%s", i, esc, (now - kle_r.fo_fired) / 1000.0, p[0], p[1], p[2], dt, s->veh,
                     s->veh != 5 || h->status != 4 ? "" : kle_r.spare_put ? " - while the vehicle drives out with you, although the rules' times were put off (FollowOutSpare): not their shot" : " - LEFT BEHIND: the rules shoot whoever is not aboard while the vehicle drives out with you");
            }
            continue;
        }
        if (r->flags & 2) { if (!(*did & 0x40)) { *did |= 0x40; klog("follow: record %d is a traitor: it is not called", i); } continue; }
        n_play++;
        if (nl < (int)sizeof left - 8) nl += snprintf(left + nl, sizeof left - nl, "%s%d", nl ? " " : "", i);
        if (d >= 0) { if (dmin < 0 || d < dmin) dmin = d; if (d > dmax) dmax = d; }
        /* does it COME? Its distance to the boarding place fell by KLE_COME over the last 2 s sample. Not 'does it move':
           a bot that walks the other way moved too, and held the driver with the human aboard (review S1). Not known
           (no place, no boarding place, no whole sample yet) = no. */
        if (d < 0) { kle_r.fo_moves[i] = 2; kle_r.fo_pos_at[i] = 0; }
        else if (!kle_r.fo_pos_at[i]) { kle_r.fo_d[i] = d; kle_r.fo_near[i] = 0; kle_r.fo_pos_at[i] = KLB_T(now); kle_r.fo_moves[i] = 2; memcpy(kle_r.fo_p[i], p, 12); }
        else if (now - kle_r.fo_pos_at[i] >= 2000) {
            kle_r.fo_near[i] = kle_r.fo_d[i] - d; kle_r.fo_moves[i] = kle_r.fo_near[i] >= KLE_COME;
            /* FollowOutComeMoved (2026-10-18, Vault run N1018_L24, kl-merge-e5's read): the way out of the vault leads AWAY
               from the vehicle first (vault y -490 -> stairs -> hall y 240 -> y 800 floor -> street); record 4 showed
               -1.3 / 0.0 / 1.5 m nearer while it climbed 49 -> 12 m. Also COMES: moved KLE_COME in 3D, or 100 cm in
               height, over the sample. GUESS: a called bot that moves that much is on its way (a fighting bot moves too). */
            if (kle.fo_come_moved && !kle_r.fo_moves[i] && kle_r.fo_near[i] > -KLE_COME && (kle_dist(kle_r.fo_p[i], p) >= KLE_COME || fabsf(p[1] - kle_r.fo_p[i][1]) >= 100.0f)) kle_r.fo_moves[i] = 1;
            kle_r.fo_d[i] = d; kle_r.fo_pos_at[i] = KLB_T(now); memcpy(kle_r.fo_p[i], p, 12);
        }
        if (edge_wait || edge_leave) {        /* the two lines a bot's way during the wait is read from (review S5): place and distance when it began and when it ended */
            if (kle_r.fo_moves[i] == 2) strcpy(mv, "not known yet whether it comes"); else snprintf(mv, sizeof mv, "%s (%.1f m nearer in the last 2 s)", kle_r.fo_moves[i] ? "coming" : "not coming", kle_r.fo_near[i] / 100);
            klog("follow: the vehicle %s (state %u, timer %.1f s, visit %d): record %d%s (stage %u, $%lu) in play at (%.0f, %.0f, %.0f)%s, %s", edge_wait ? "waits" : "leaves", s->veh, timer, kle_r.visit, i, esc, r->stage, r->money, p[0], p[1], p[2], dt, mv);
        }
        /* a. the stage byte, once */
        if (!(*did & 0x43)) {
            const char *what;
            if (r->stage >= 3) { *did |= 0x40; what = "it has heist stage 3 already"; }
            else if (!havep) {
                /* review M1: no stage 3 for a record whose actor was not seen to be one. From stage 3 on the rules' own
                   order loop reads [record+4] and [actor+0x77c] at every call and departure with no test (0x8fb031 /
                   0x8fb034): a null or stale actor there is a fault inside kl2.exe. BoardAll asks the same (all_seen). */
                if (!(*did & 0x80)) { *did |= 0x80; klog("follow: record %d%s (stage %u): its actor is no ZFFActor with a readable place (%08lx): the stage byte is NOT written - the rules walk a stage-3 record's actor with no test of their own (looked at again every pass)", i, esc, r->stage, r->actor); }
                continue;
            }
            else if (dry) { *did |= 2; what = "heist stage WOULD be set to 3 (dry run)"; }
            else if (!klb_still(s, i, &fl, &st) || st || (fl & 2) || !klh_rd(r->at + 0x78, &curst, 1)) {      /* gone, aboard, dead or turned since the snapshot */
                if (!(*did & 4)) { *did |= 4; klog("follow: record %d: its record changed since this pass read it: nothing is written (looked at again next pass)", i); }
                continue;
            }
            else if (curst >= 3) { *did |= 0x40; what = "it has heist stage 3 since this pass read it (BoardAll, or a trigger box)"; }
            else if (!klb_put8(r->at + 0x78, 3, "crew record: heist stage 3 (the crew follows the human out)")) {
                if (!(*did & 4)) { *did |= 4; klog("follow: record %d (stage %u): the stage byte was NOT written: it is left alone", i, r->stage); }
                continue;
            }
            else { *did |= 1; what = "heist stage set to 3"; }
            klog("follow: record %d%s (stage %u, $%lu) at (%.0f, %.0f, %.0f)%s: %s", i, esc, r->stage, r->money, p[0], p[1], p[2], dt, what);
        }
        if (kle_r.fo_moves[i] == 1) { n_moving++; if (d >= 0 && (dcome < 0 || d < dcome)) dcome = d; }      /* only a bot that passed (a): called crew at stage 3; dcome = the nearest that comes */
        /* b. the order to the boarding place: only while the vehicle drives in AND the board tactic cannot have the bot
           yet. That tactic is live while the vehicle waits and, in state 1 / 2, once the timer is under 2.0 (its test
           0x4faff7, its run 0x82f9be): a not-soft order then would cut the very tactic that takes him aboard (review S2). */
        if (!kle.fo_order || !coming || !have_bd || !havep || kle_r.used[i] || !(*did & 3) || d < 400.0f) continue;      /* only whom this part gave its stage (the others had the game's order at the call); within 4 m it is there (and within 2.5 m the game would take the order as 'soft') */
        if (!(timer >= KLE_BOARD_WIN)) {                                      /* also a timer that is no number */
            if (kle_r.fo_win_call != kle_r.fo_call) { kle_r.fo_win_call = kle_r.fo_call; klog("follow: the vehicle arrives in %.1f s (call %d): no order from here on - under %.0f s a stage-3 bot's own board tactic is live, and a not-soft order would cut it", timer, kle_r.fo_call, KLE_BOARD_WIN); }
            continue;
        }
        k = kle_r.fo_ocall[i] == kle_r.fo_call;                               /* ordered for this call already */
        if (k && (dry || now - kle_r.fo_order_at[i] < kle.fo_every)) continue;
        /* its defend place IS the boarding place: what the game's own order at this call did (snapped to the mesh: 3 m),
           or - after an order of ours - anything within KLE_ROUTE of what that left: nearer than that, one of the
           soldier's own tactics moved it (section 2's GUESS), and a renewal would pop a fighting bot's goal stack every
           FollowOutEvery (review S2) */
        if ((soldier = klh_rd32(r->actor + 0x77c)) != 0 && kle_block(soldier, cur)
            && kle_dist(cur, k ? kle_r.fo_target[i] : bd) <= (k ? KLE_ROUTE : 300.0f)) continue;
        if (!kle_bot(s, i, &actor, &soldier, bp, w)) {
            if (!(*did & 0x20)) { *did |= 0x20; klog("follow: record %d: no order to the boarding place yet: %s (asked again every pass while the vehicle drives in)", i, w); }
            continue;
        }
        memset(&t, 0, sizeof t); t.rec = i; t.actor = actor; t.soldier = soldier; t.told_soft = 1;      /* kle_order2's 'soft' line is worded for an escort */
        kle_gap_exempt = 1; k = kle_order2(&t, bd, got, w, dry); kle_gap_exempt = 0;
        kle_r.fo_order_at[i] = KLB_T(now);
        if (!k) { if (!(*did & 0x20)) { *did |= 0x20; klog("follow: record %d NOT sent to the boarding place: %s", i, w); } continue; }
        kle_r.fo_ocall[i] = kle_r.fo_call; memcpy(kle_r.fo_target[i], got, 12); kle_r.fo_orders[i]++;
        if (k == 1) klh_rd(soldier + 0x4fc, &soft, 1);
        klog("follow: record %d %s to the boarding place (%.0f, %.0f, %.0f), the game set (%.0f, %.0f, %.0f); order %d%s%s", i, k == 2 ? "WOULD be sent (dry run)" : "sent", bd[0], bd[1], bd[2], got[0], got[1], got[2],
             kle_r.fo_orders[i], kle_r.fo_orders[i] > 1 ? ": something had moved its place since the last one" : "", soft ? " - the game took it as 'he is there already' (soft): a waiting step of its route chain ends" : "");
    }
    if (dmin >= 0) snprintf(rg, sizeof rg, " (nearest %.1f m, farthest %.1f m from the boarding place)", dmin / 100, dmax / 100); else rg[0] = 0;
    if (edge_wait) klog("follow: the vehicle waits: %d of the crew aboard, %d in play%s, %d dead; you are %s", n_aboard, n_play, rg, n_dead, h->status == 4 ? "aboard" : "in play");
    if (edge_leave) klog("follow: the vehicle leaves (state 5, timer %.1f s) %s: %d of the crew aboard, %d left in play%s%s%s, %d dead%s", timer, h->status == 4 ? "with you aboard" : "without you", n_aboard, n_play,
                         n_play ? " (record(s) " : "", left, n_play ? ")" : "", n_dead, h->status == 4 && n_play && !kle.fo_spare ? "; the rules shoot those left in play, one about every second" : "");

    /* c. FollowOutHold: the human is aboard, the vehicle waits and would leave, crew that was called still comes.
       FollowOutHoldAlone=1 (2026-10-18, Vault run N1018_L22: visit 2 left after its 8.0 s while all four called bots
       came at 9-18 m per 2 s from 37-53 m; the hold never ran, you were in play, not aboard): also while you are IN PLAY,
       if the nearest called bot that comes is within FollowOutHoldAloneRange m (GUESS 40) of the boarding place. Same
       seconds per visit, same step, same shield. */
    if (kle.fo_hold > 0 && waiting && (h->status == 4 || (kle.fo_hold_alone && h->status == 0 && dcome >= 0 && dcome <= kle.fo_hold_alone_m * 100.0f))) {
        BYTE grade = 1, paid = 0, veh2 = 0; float tnow = 0, add; const char *no = 0; char gw[200], gn[200];
        const char *you = h->status == 4 ? "with you aboard" : "with you in play (FollowOutHoldAlone)";
        gw[0] = gn[0] = 0;
        if (kle_r.fo_hold_visit != kle_r.visit) { kle_r.fo_hold_visit = kle_r.visit; kle_r.fo_held = 0; kle_r.fo_hold_told = 0; }
        if (!(timer > 0 && timer < KLE_HOLD_AT)) return;                      /* not yet; or a timer of 0: somebody set it to leave */
        if (kle.fo_hold - kle_r.fo_held < 0.5f) {                             /* the seconds of this visit are used */
            if (!(kle_r.fo_hold_told & 2)) { kle_r.fo_hold_told |= 2; klog("follow: hold: the vehicle leaves in %.1f s %s: the %.1f s of FollowOutHold are used (%d of the crew in play%s)", timer, you, kle.fo_hold, n_play, rg); }
            return;
        }
        add = kle.fo_hold - kle_r.fo_held; if (add > KLE_HOLD_STEP) add = KLE_HOLD_STEP;
        if (!n_moving) no = n_play ? "none of the called crew in play comes nearer to the boarding place (2 m in 2 s)" : "nobody of the crew is left in play";
        else if (!klh_rd(s->score + 0x60, &grade, 1) || grade) no = "the vehicle is damaged and must go";
        else if (!klh_rd(s->rules + 0x1b3, &paid, 1) || paid != 0xff) no = "somebody paid the driver";
        else if (!klh_rd(s->rules + 0x1dc, &veh2, 1) || (veh2 != 3 && veh2 != 4) || !klh_rd(s->rules + 0x1d8, &tnow, 4) || !klb_finite(tnow) || !(tnow > 0 && tnow < KLE_HOLD_AT)) no = "its timer changed since this pass read it";
        /* the last test, and the only one that writes: the vehicle must not be shot to pieces while it is held (runs N1 / N1b) */
        if (!no && !kle_hold_guard(s, now, dry, gw, gn)) no = gw;
        if (no || dry) {
            if (!(kle_r.fo_hold_told & 1)) {
                kle_r.fo_hold_told |= 1;
                if (no) klog("follow: hold: the vehicle leaves in %.1f s %s and is NOT held: %s (%d in play%s)", timer, you, no, n_play, rg);
                else klog("follow: hold: the vehicle would leave in %.1f s %s and %d of the crew still coming%s: its timer WOULD get %.1f s more (dry run); %s", timer, you, n_moving, rg, add, gn);
            }
            return;
        }
        tnow += add;
        if (!klh_data((void *)(DWORD_PTR)(s->rules + 0x1d8), &tnow, 4, "escape vehicle wait timer (the driver is held for the crew)")) {
            if (!(kle_r.fo_hold_told & 1)) { kle_r.fo_hold_told |= 1; klog("follow: hold: the vehicle's timer could NOT be written"); }
            return;
        }
        kle_r.fo_held += add;
        klog("follow: hold: the vehicle would leave in %.1f s %s and %d of the crew still coming%s: timer %.1f -> %.1f s (%.1f of %.1f s used this visit); %s", timer, you, n_moving, rg, tnow - add, tnow, kle_r.fo_held, kle.fo_hold, gn);
    }
}

static void kle_tick(int game_thread)
{
    static DWORD last; static int toldthread; struct klb_snap s; DWORD now = GetTickCount(), player = 0, actor, soldier; char why[200], w[100];
    float hp[3], hn[3], bp[3], bd[3], got[3]; const struct klb_rec *h; int i, stages = 0, human_in, rel = 0, waiting, k;
    /* kle_sh.obj: klmove.c's WaitForYouHold can have set the shield with none of this file's keys on - it is still taken back here */
    if ((!kle.n && !kle.all && !kle.fo && !kle.fo_spare && !kle_sh.obj) || !klb.on || !klh_exe_ok) return;
    if (kle_r.spare_rules && game_thread) kle_spare_fast();                   /* FollowOutSpare: one read on every pass while the vehicle waits */
    if (now - last < 500) return;
    last = now;
    if (!klb_read(&s)) { kle_r.rules = 0; kle_r.spare_rules = 0; if (game_thread) kle_shield_off("the round can no longer be read", now); return; }
    for (i = 0; i < s.n; i++) if (s.r[i].used) stages += s.r[i].stage;
    if (s.rules != kle_r.rules || (s.state == KLB_ROUND && kle_r.state != KLB_ROUND) || stages < kle_r.stages) {      /* a new round: as klbot.c's klb_act */
        if (game_thread && kle_r.rules) kle_shield_off("a new round", now);   /* not at the first pass of this file after the shield was set by klmove.c (kle_r.rules is 0 then) */
        memset(&kle_r, 0, sizeof kle_r); kle_r.rules = s.rules; kle_r.round_at = KLB_T(now);
    }
    kltr_round(s.rules, now);
    kle_r.state = s.state; kle_r.stages = stages;
    if (s.state != KLB_ROUND) { kle_r.spare_rules = 0; if (game_thread) kle_shield_off("the round is over", now); return; }
    if (!klb_level(why)) {                    /* klbot.c section 0: nothing on a stock level, on an unknown one, or without the Steam guard */
        if (!kle_r.told_gate++) klog("%s: %s: nothing is done here (this part acts only on a level that is not stock)", kle.n ? "escort" : kle.all ? "board" : "follow", why);
        kle_r.spare_rules = 0;
        if (game_thread) kle_shield_off("the level counts as stock now", now);
        return;
    }
    if (!game_thread) { if (!toldthread++) klog("escort / board / follow: the tick is not on the game's thread ([KLHook] Tick=0?): nothing is ordered or written"); return; }
    h = s.human >= 0 ? &s.r[s.human] : 0;
    human_in = h && h->status == 0 && kle_human(&player, hp, hn);
    waiting = s.veh == 3 || s.veh == 4;
    if (waiting && !kle_r.was_waiting) {                                      /* a new visit of the vehicle (the first is 1) */
        kle_r.visit++;
        for (i = 0; i < KLB_NREC; i++) if (kle_r.all_raised[i] == 2) kle_r.all_raised[i] = 0;      /* only looked at (dry / Stage=0): judged again */
    }
    kle_r.was_waiting = waiting; kle_gap_wait = waiting;
    if (kle.all) {
        static DWORD tracked;                 /* the last pass that got here: the stillness clock is wall time, the round is not */
        if (tracked && now - tracked > 1500) memset(kle_r.all_seen, 0, sizeof kle_r.all_seen);     /* a pass was missing (the window was not in front, the round stood still): every clock starts again */
        tracked = KLB_T(now);
        kle_all_track(&s, now); if (waiting) kle_board_all(&s, now);
    }
    kle_veh_pass(&s, now);                                                    /* the shield's upkeep and release; with FollowOut the vehicle's health in the log */
    if (kle.fo || kle.fo_spare) kle_follow(&s, now);                          /* after BoardAll: a byte it has just written is seen as 'stage 3 since this pass' */
    if (kle.n && human_in && !kle_r.told_you++)
        klog("escort: you: record %d, player %08lx, feet (%.0f, %.0f, %.0f), node (%.0f, %.0f, %.0f) - the two should agree to within a body's height", s.human, player, hp[0], hp[1], hp[2], hn[0], hn[1], hn[2]);
    if (!human_in) rel = 1;
    else if (s.veh >= (BYTE)kle.until && s.veh <= 5) rel = 2;
    else if (kle.stage && h->stage >= kle.stage) rel = 3;
    for (i = 0; i < kle.n; i++) {
        struct kle_e *e = &kle_r.e[i];
        if (e->mode != 1 && e->mode != 2) continue;
        k = kle_bot(&s, e->rec, &actor, &soldier, bp, w);
        if (!k && kle_later) continue;                                        /* a state that passes: asked again next pass, no order meanwhile */
        if (!k || actor != e->actor || soldier != e->soldier) {
            klog("escort: record %d dropped: %s", e->rec, w[0] ? w : "its actor is no longer the one chosen");
            k = e->mode; memset(e, 0, sizeof *e);
            if (k == 2 || !kle.refill) e->mode = 3;                           /* mode 0 = the slot may be given to another */
            continue;
        }
        if (e->mode == 1) {
            if (rel) kle_release(&s, i, rel, now);
            else kle_hold(&s, i, hp, bp, now);
        } else if (waiting && kle.board) {                                    /* released earlier; now the vehicle waits */
            e->mode = 3;
            if (s.r[e->rec].stage >= 3) continue;                             /* its own board tactic takes it (0x4fb064) */
            if (!kle_boarding(s.rules, bd)) { klog("escort: record %d (released): the vehicle waits but the boarding place cannot be read", e->rec); continue; }
            kltr_set("escort", "released earlier, the vehicle waits: to the boarding place", -1);
            k = kle_order(e, bd, got, w);
            if (k) klog("escort: record %d (released, stage %u): the vehicle waits: %s to the boarding place (%.0f, %.0f, %.0f), the game set (%.0f, %.0f, %.0f)", e->rec, s.r[e->rec].stage, k == 2 ? "WOULD be sent (dry run)" : "sent", bd[0], bd[1], bd[2], got[0], got[1], got[2]);
            else klog("escort: record %d (released): NOT sent to the boarding place: %s", e->rec, w);
        }
    }
    if (kle.n && !rel && now - kle_r.round_at >= 3000) kle_pick(&s, hn, now); /* one slot per pass */
}

static void kle_init(void)
{
    int v;
    memset(&kle, 0, sizeof kle); memset(&kle_r, 0, sizeof kle_r);
    memset(&kltr, 0, sizeof kltr); kltr.rec = -1;
    kltr.on = GetPrivateProfileIntA("Bots", "OrderTrace", 0, klh_ini) != 0;      /* v82i: the only read of this key; 0 = the trace does nothing */
    if (kltr.on) klog("otrace: ON ([Bots] OrderTrace=1): one 'otrace:' line per order a module of this hook gives a crew bot, per klhop.c teleport, and per change of a defend block that none of them explains (by=GAME?); at most %d lines a round; re/bots_active.md 'Order trace'", KLTR_CAP);
    if (!klb.on) {                            /* [Bots] Enable=0: klbot.c is off, and so is this */
        if (GetPrivateProfileIntA("Bots", "BoardAll", 0, klh_ini) || GetPrivateProfileIntA("Bots", "Escort", 0, klh_ini) > 0
            || GetPrivateProfileIntA("Bots", "FollowOut", 0, klh_ini) || GetPrivateProfileIntA("Bots", "FollowOutSpare", 0, klh_ini))
            klog("escort / board / follow: [Bots] Escort, BoardAll, FollowOut or FollowOutSpare is set but [Bots] Enable is 0: they need klbot.c's crew records, nothing is done");
        return;
    }
    v = (int)GetPrivateProfileIntA("Bots", "Escort", 0, klh_ini);
    kle.n = v < 0 ? 0 : v > KLE_MAX ? KLE_MAX : v;
    kle.all = GetPrivateProfileIntA("Bots", "BoardAll", 0, klh_ini) != 0;
    kle.all_stage = GetPrivateProfileIntA("Bots", "BoardAllStage", 1, klh_ini) != 0;
    kle.all_order = GetPrivateProfileIntA("Bots", "BoardAllOrder", 0, klh_ini) != 0;
    {   char t[16]; int j, num = 1;           /* a value that is not a plain number is the default, not 0 = 'every bot' */
        GetPrivateProfileStringA("Bots", "BoardAllStill", "15", t, sizeof t, klh_ini);
        for (j = 0; t[j]; j++) if (t[j] < '0' || t[j] > '9') num = 0;
        kle.all_still = (DWORD)(num && j ? klb_pos("BoardAllStill", 15, 600) : 15) * 1000;
    }
    if (kle.all && klb.van && klb.van_left) {
        klog("board: BoardAll is OFF: [Bots] VanLeftBehind=1 takes every bot at heist stage 3 as standing at the vehicle, and BoardAll gives stage 3 to bots far from it");
        kle.all = 0;
    }
    kle.dry = GetPrivateProfileIntA("Bots", "EscortDry", 0, klh_ini) != 0;
    if (kle.all) klog("board: on; BoardAll=1 Still=%lu s Stage=%d Order=%d%s: while the escape vehicle waits, an AI heister at heist stage 1 or 2 that has neither moved 1 m nor earned for that long %s%s; Arcade only, on a level that is not the stock one of its slot",
                      kle.all_still / 1000, kle.all_stage, kle.all_order, kle.dry ? " DRY RUN (EscortDry=1: nothing is written or called)" : "",
                      kle.all_stage ? "gets heist stage 3 (one byte of its crew record: the game's loot tactic lets go, its board tactic starts)" : "is named in the log (BoardAllStage=0: nothing is written)",
                      kle.all_order ? " and one order to the boarding place a visit" : "");
    kle.fo = GetPrivateProfileIntA("Bots", "FollowOut", 0, klh_ini) != 0;
    kle.fo_spare = GetPrivateProfileIntA("Bots", "FollowOutSpare", 0, klh_ini) != 0;
    kle.fo_dry = GetPrivateProfileIntA("Bots", "FollowOutDry", 0, klh_ini) != 0;
    kle.fo_order = GetPrivateProfileIntA("Bots", "FollowOutOrder", 1, klh_ini) != 0;
    kle.fo_money = (DWORD)klb_pos("FollowOutMoney", 1, 0x7fffffff);
    kle.fo_crew_money = GetPrivateProfileIntA("Bots", "FollowOutCrewMoney", 0, klh_ini) != 0;
    kle.fo_after = (DWORD)klb_pos("FollowOutAfter", 0, 600) * 1000;
    kle.fo_every = (DWORD)klb_pos("FollowOutEvery", 2, 60) * 1000; if (kle.fo_every < 1000) kle.fo_every = 1000;
    kle_hold_step = klb_inif("HoldStep", "0"); if (!klb_finite(kle_hold_step) || kle_hold_step <= 0 || kle_hold_step > 60) kle_hold_step = 60.0f;      /* 0 = the whole hold at once */
    kle.fo_hold = klb_inif("FollowOutHold", "0"); if (!klb_finite(kle.fo_hold) || kle.fo_hold < 0) kle.fo_hold = 0; if (kle.fo_hold > 60) kle.fo_hold = 60;
    kle.fo_shield = klb_pos("FollowOutShield", 2, 3);                         /* also klmove.c's WaitForYouHold goes by it */
    kle.vb = GetPrivateProfileIntA("VanBlow", "Enable", 1, klh_ini) != 0;     /* 2026-10-24: default ON - the owner wants the escape vehicle to blow up */
    kle.vb_dry = GetPrivateProfileIntA("VanBlow", "Dry", 0, klh_ini) != 0;
    kle.vb_log = GetPrivateProfileIntA("VanBlow", "Log", 1, klh_ini) != 0;
    kle.vb_delay = (DWORD)GetPrivateProfileIntA("VanBlow", "EmptyDelay", 1500, klh_ini); if (kle.vb_delay > 60000) kle.vb_delay = 60000;
    kle.vb_hp = (float)GetPrivateProfileIntA("VanBlow", "HealthMax", 0, klh_ini); if (kle.vb_hp < 0) kle.vb_hp = 0; if (kle.vb_hp > 100000) kle.vb_hp = 100000;
    if (kle.vb && kle.fo_shield) klog("vanblow: Enable=1%s: the escape vehicle's shield (FollowOutShield=%d) is taken off while NOBODY is aboard (for %u ms), so the vehicle can be shot to 0 and blow up; with anybody aboard it stays shielded (state 6 would kill them). HealthMax=%.0f (0 = the file's own). Acts on non-stock levels only; Dog Days' own FA maps are never shielded", kle.vb_dry ? " (DRY RUN: only logged)" : "", kle.fo_shield, (unsigned)kle.vb_delay, kle.vb_hp);
    kle.fo_unshielded = GetPrivateProfileIntA("Bots", "FollowOutHoldUnshielded", 1, klh_ini) != 0;      /* DEFAULT 1 = the old behaviour: hold all the same; 0 = an unshieldable vehicle is not held (2026-10-19: Hasta loss still under investigation) */
    kle.fo_hold_alone = GetPrivateProfileIntA("Bots", "FollowOutHoldAlone", 0, klh_ini) != 0;
    kle.fo_hold_alone_m = klb_inif("FollowOutHoldAloneRange", "40"); if (!klb_finite(kle.fo_hold_alone_m) || kle.fo_hold_alone_m < 1) kle.fo_hold_alone_m = 40; if (kle.fo_hold_alone_m > 100) kle.fo_hold_alone_m = 100;      /* GUESS */
    kle.fo_stop = GetPrivateProfileIntA("Bots", "FollowOutStopPlace", 0, klh_ini) != 0;
    kle.fo_come_moved = GetPrivateProfileIntA("Bots", "FollowOutComeMoved", 0, klh_ini) != 0;
    if (kle.fo && kle.fo_come_moved) klog("follow: FollowOutComeMoved=1: a called bot that moved 2 m (or 1 m in height) in 2 s, and got no more than 2 m farther, counts as coming (for the holds)");
    if (kle.fo && kle.fo_hold > 0 && kle.fo_hold_alone) klog("follow: hold: FollowOutHoldAlone=1: the hold also runs while you are in play (not aboard), when the nearest called bot that comes is within %.0f m of the boarding place", kle.fo_hold_alone_m);
    if (kle.fo && kle.fo_stop) klog("follow: FollowOutStopPlace=1: after the vehicle's first wait, a drive-in sends the crew to where it waited, not to the moving vehicle");
    if (kle.fo && klb.van && klb.van_left) {
        klog("follow: FollowOut is OFF: [Bots] VanLeftBehind=1 takes every bot at heist stage 3 as standing at the vehicle, and FollowOut gives stage 3 to bots far from it");
        kle.fo = 0;
    }
    if (kle.fo) klog("follow: on; FollowOut=1 Money=%lu After=%lu s Order=%d Every=%lu s Hold=%.1f s Spare=%d%s: once your own crew record has heist stage 3 (the exit trigger: the vehicle is called) and you carry that money, every AI heister in play that is no traitor gets heist stage 3 (one byte of its record)%s%s%s; Arcade only, on a level that is not the stock one of its slot",
                     kle.fo_money, kle.fo_after / 1000, kle.fo_order, kle.fo_every / 1000, kle.fo_hold, kle.fo_spare, kle.dry || kle.fo_dry ? " DRY RUN (nothing is written or called)" : "",
                     kle.fo_order ? " and, while the vehicle drives in and is 2 s or more away, the soldier's own order to the boarding place" : "",
                     kle.fo_hold > 0 ? "; while it waits with you aboard and called crew still comes nearer, its timer gets up to 5 s more under 2 s, that many seconds a visit at most" : "",
                     klb.van ? "; NOTE [Bots] Van is on: a bot that turns traitor after it was called counts as 'at the vehicle' for it" : "");
    if (kle.fo && kle.fo_hold > 0)
        klog(kle.fo_shield ? "follow: hold: FollowOutShield=%d: from the first held second the vehicle takes no hit (its own 'Invulnerable' byte, ZAnimatedVehicle +0x%x, one data write) %s; no shield possible = no hold. BEFORE the first hold (about the first 6 s of a wait) and at a visit that is not held it takes hits as in stock. The clocks a hold touches: the wait timer [rules+0x1d8] and nothing else"
                           : "follow: hold: FollowOutShield=%d (+0x%x not written%s): THE HELD VEHICLE CAN BE DESTROYED WITH YOU ABOARD - live runs N1 / N1b: 20.9 / 21.3 s after it began to wait, stock stands 8 s",
             kle.fo_shield, KLE_VEH_INV, !kle.fo_shield ? "" : kle.fo_shield == 1 ? "until it drives out (the 8.4 s of the drive-out are the game's)" : "until it is gone");
    if (kle.fo_spare) klog("follow: spare on%s: when the escape vehicle drives out, the rules' times for shooting the AI heisters left behind (rules +0x%x) are put off: they stay in play; Arcade only, on a level that is not the stock one of its slot",
                           kle.dry || kle.fo_dry ? " DRY RUN (nothing is written)" : "", KLE_KILL_TIMES);
    if (!kle.n) return;
    kle.log = klb_pos("EscortLog", 1, 2);
    kle.record = (int)GetPrivateProfileIntA("Bots", "EscortRecord", -1, klh_ini); if (kle.record >= KLB_NREC) kle.record = -1;
    kle.refill = GetPrivateProfileIntA("Bots", "EscortRefill", 0, klh_ini) != 0;
    kle.until = GetPrivateProfileIntA("Bots", "EscortUntil", 3, klh_ini) == 1 ? 1 : 3;
    kle.stage = klb_pos("EscortStage", 0, 3);
    kle.board = GetPrivateProfileIntA("Bots", "EscortBoard", 1, klh_ini) != 0;
    kle_gap_s = klb_pos("OrderGap", 8, 120);
    if (kle_gap_s) klog("order-gap: OrderGap=%d s: an order of another kind (escort follow / the other order givers) to the same bot within that time is refused (0 = off)", kle_gap_s);
    kle.every = (DWORD)klb_pos("EscortEvery", 2, 60) * 1000; if (kle.every < 1000) kle.every = 1000;
    kle.far_ = klb_inif("EscortFar", "800"); if (!klb_finite(kle.far_) || kle.far_ < 400) kle.far_ = 400;      /* under 4 m the place could come within the game's 250 */
    kle.side = klb_inif("EscortSide", "300"); if (!klb_finite(kle.side) || kle.side < 0) kle.side = 0;
    if (kle.side > kle.far_ - 300) kle.side = kle.far_ - 300;                 /* the bot stays at least 3 m from the place it is called to */
    kle.retarget = klb_inif("EscortRetarget", "500"); if (!klb_finite(kle.retarget) || kle.retarget < kle.side + 100) kle.retarget = kle.side + 100;
    klog("escort: on; Escort=%d Far=%.0f Side=%.0f Retarget=%.0f Every=%lu s Until=%d Stage=%d Board=%d Refill=%d Record=%d%s; Arcade only, on a level that is not the stock one of its slot; one game call (the soldier's own order %08x), no write",
         kle.n, kle.far_, kle.side, kle.retarget, kle.every / 1000, kle.until, kle.stage, kle.board, kle.refill, kle.record, kle.dry ? " DRY RUN (nothing is called)" : "", KLE_ORDER);
}

#endif /* KLESCORT_C */
