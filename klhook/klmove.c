/*
 * klmove.c - THE AI HEISTERS KEEP MOVING, GET FED UP WITH LOOT THAT DOES NOT PAY, WAIT FOR THE HUMAN, AND WALK TO THE CAR.
 * Owner, 2026-10-11: 'the ai seems to leave early, they should have to get to the car physically and make it so
 * they're normally moving majority of the time somewhat ... sometimes they just be standing still a bit ... they should
 * go onto like a money square thing and if nothing happens for like 5ish seconds they get fed up n move but if they do
 * end up getting the money they might go back for it'.
 * Part of KLHook (included by klhook.c after klhop.c: it uses klbot.c's crew records and klescort.c's order call).
 * Its names begin with klmv_ / KLMV_ (the first version's kly_ is klgrudge.c's prefix: the two could not be built together).
 * Wiring: #include "klmove.c" after klhop.c's, klmv_init(); after kle_init();, klmv_tick(game_thread); after kle_tick(game_thread);
 * No code byte of kl2.exe changes. Four keys, each OFF by default, each only in an Arcade round (session state 0x19)
 * on a level that is NOT the stock one of its slot (klbot.c section 0), from the game's own thread:
 *   Restless    one game call (the soldier's own order 0x760e50, as klescort.c makes it) + one data byte of a money object
 *   WaitForYou  one data byte and one float of the rules object
 *   BoardNear   a private copy of ONE class's vtable (ZAllyEscapeBox, 34 slots) put on that class's objects of the
 *               level (one to three a map), one slot wrapped; + the stage byte BoardAll writes
 * Measurements, the reading and the live checks: re\bots_move.md. NOTHING HERE HAS RUN IN THE GAME.
 * Everything below was read in kl2.exe build 0490 for this file (debug\dasm.py, 2026-10-11) unless a note is named.
 *
 * 1. WHAT THE OWNER SAW, FROM HIS LOG (KLHook.log 12:33 - 12:45, the bank twice, the park)
 *    a. 'they should have to get to the car physically': record 4 stood at (-1197, 200, -2651), 45.6 m from the van,
 *       and was 'aboard' 2.9 s later; record 5 at 48.6 m, aboard 1.5 s later. Nobody runs 16 m/s: they were taken by a
 *       ZAllyEscapeBox. Its update (vtable 0xbc7f6c slot 25 = 0x907a50, EXE whole): in Arcade, for every crew record
 *       that is an AI member (+0x79 mask 1) in play (+0x10 == 0) whose actor is inside the box (0x758cb0) ->
 *       0x74d7f0(index) -> rules vtable +0xb4 = the boarding rule 0x6840a0 (actor branch 0x6841fd: record status 4,
 *       0x89c890, [actor+0x8f0] = 1; if nobody is left in play the wait timer = 0). NO stage, NO path, NO distance to
 *       the vehicle: only 'the vehicle waits' (state 3 / 4, or 5 in its first second) inside 0x6840a0.
 *       Every bots build puts the seven's last places inside such a box 3.8 .. 8.4 m beside the van's stop
 *       (kl_fa_bots --park), and the bank has a second one at the one-way drop in the yard, 43 m from the van: that
 *       one is what took records 4 and 5. The board TACTIC (0x82f970) is physical: it runs to the boarding object and
 *       calls the same rule within 300 units (0x82fa35, squared 90000.0 at 0xd19a28).
 *    b. 'the ai seems to leave early': the vehicle's wait is the game's own 8 s a visit; whoever is in a box or within
 *       3 m is aboard at once and the vehicle goes when the 8 s are over - in the park 16 s after HE had called it
 *       (12:43:01 stage 3, 12:43:09 it waits, 12:43:17 'leaves without you: 2 of the crew aboard'), while he was on
 *       his way. On the bank's first round a BOT called it: record 1 stood in the exit trigger 8 s before him
 *       (12:35:34 against 12:35:42) - the exit trigger (ZOnlineExitLevelTrigger slot 34 = 0x6c3d50) gives stage 3 to
 *       whoever stands in it and calls the vehicle in the same step, human or AI, no stage or money asked for.
 *
 * 2. THE GAME'S HANDLES (EXE)
 *    THE CALL GATE. 0x6c3d50 after the stage (0x5dd890): vehicle state [rules+0x1dc] must be 0 (0x6c3e3e), and
 *    rules vtable +0x290 = 0x8ad6c0 `mov al, [ecx+0x1ee] / ret` must be 0 (0x6c3e4e), then vtable +0xb0 = slot 44 =
 *    0x6cd8e0 -> 0x8154f0 calls a vehicle. Byte [rules+0x1ee] is 'the LAST vehicle of the round has been called': set by
 *    slot 194 (0x8fa6d0) in its case for state 2 (0x8fa758; a call is state 2 instead of 1 when 0x8154f0 found the
 *    round's time too short for another trip, [rules+0xe8a]), cleared when the vehicle is reset (slot 3 = 0x4fb620 and
 *    the other callers of slot 194 with 0). Its other readers: slot 153 (0x87d000; and 0x6ba930, the same slot of the
 *    multiplayer rules classes, not of this one), 'may the human aboard hold / pay the driver' - behind the human's
 *    client flag 0x20 'aboard', so never in state 0 - AND THE HUD'S ROUND CLOCK (review M2; the first version of this
 *    text said 'nothing else'): ZFATimeDisplay slot 5 = 0x62a0c0 asks rules vtable +0x290 every frame (0x62a262,
 *    0x62a381), in every vehicle state, and gives the clock's two text objects the colour [0xbbe498] = 0xffcc0000
 *    (RED, 'the last vehicle') when it is set, else [0xbbe494] = 0xffcccccc.
 *    So while the vehicle's state is 0, [rules+0x1ee] = 1 means: the exit trigger still gives its stage 3 and calls
 *    nothing, AND THE ROUND CLOCK IS RED for as long as the byte is ours. No rule reads it otherwise. 0x8154f0
 *    itself does not read the byte: a call the rules force (the last vehicle) comes anyway.
 *    THE WAIT TIMER. float [rules+0x1d8], counted down by slot 195; the game's own 'hold the driver' (slot 152,
 *    0x8b3930) adds 5.0 to it; klescort.c's FollowOutHold writes it the same way (its comment has the readers).
 *    THE LOOT CANDIDATES. Rules slot 202 = 0x8b94d0(place of the bot, out[5]): list one = [rules+0xdcc], count
 *    [rules+0xdc0], pointers to ZOnlineMoneyCtrl objects (vtable 0xbc874c). An entry is passed over when it is null,
 *    taken (0x4536e0: int [obj+0x34] <= 0) or its byte [obj+0x6c] is 0 (0x8b95f2); its place is the node of the entity
 *    [obj+0x24] (0x8d3150 = node [ent+4] through its parents); then |dy| <= 400 and distance <= 800 (tuning +0xc20 /
 *    +0xc1c). ZLootTactic's test (0x451920) is 1.0 while one of the five nearest has a path, and its action runs to
 *    the nearest (re\bots_loot.md 4). NO PER-BOT MARK EXISTS: the test's only per-bot terms are the heist stage
 *    (off at 0, and at 3 while the vehicle waits) and a time stamp [[actor+0x54]+0x30] ('4 s since' - of what was
 *    not established: thirteen other readers, 0x40f714 0x4faf7d 0x6225f6 .., no writer found; NOT USED).
 *    WHO ELSE READS [obj+0x6c] (every function of the class's vtable and of the grab path was searched for the byte):
 *    the candidate filter above; the object's update (slot 25, 0x5f1b2b): ONLY 'the round is over (session state 0x1f)
 *    and +0x6c != 0 -> Deactivate (0x4c95d0)'; slots 21 / 22 (0x542910, 0x8ea4e0: the network copy of the object -
 *    Arcade has none). Writers: the init (1), taken (0x4e3f76: 0), Deactivate (0), and 'Activate' (0x4fb5d3 /
 *    0x4fb5e4: 1 - a container that is opened re-arms the byte by itself). The human's grab (trigger -> rules slot 201
 *    -> 0x8e8750 -> 0x727cb0) reads state +0x64 and active +0x74, never +0x6c (re\bots_loot.md 1). So +0x6c = 0 on an
 *    untaken object means: no AI heister goes for it; everything else about it is as it was.
 *
 * 3. WHAT THE HOOK DOES
 *    RESTLESS (Restless=<seconds>; the owner's value is about 5). Twice a second, for every AI heister in play that is
 *    no traitor, was never an escort this round, and is not a stage-3 bot while a vehicle is called or there (the
 *    board tactic and the rules own that one): where it stands and what it has; STOOD = neither moved 1 m nor earned.
 *    a. THE LOOT SQUARE (RestlessLoot seconds, default = Restless): a bot that has stood that long within
 *       RestlessLootNear (200 = 2 m, 2.5 m in height) of a money object that is a candidate (in list one, untaken,
 *       +0x6c set) whose amount has not gone down in that time (nobody else is taking it either) is FED UP: the
 *       object's byte +0x6c = 0. The loot tactic's test then finds no candidate there, for him and for every other AI
 *       heister, and his goal goes on with the order he has. THE HUMAN CAN STILL TAKE IT. The byte comes back - 'he
 *       might go back for it' - when RestlessLootBack seconds are over (30; doubled each time the same object soured
 *       again, 240 at most), at once when the object's amount or its 'active' byte +0x74 changes (somebody opened the
 *       case: the game re-arms +0x6c itself then; the human took a part), and always when the round is over (the
 *       game's own round-over Deactivate must find the byte set). The mark is per OBJECT, not per bot: the game has no
 *       per-bot form. What is per bot is the log line and the count.
 *       CATCHES: a shut container nobody opened, the watch shop's clerk (runs L8 / L10 / L11), a bot that jitters at a
 *       trigger's edge. DOES NOT CATCH: a bot held more than 2 m from the object it wants (no path's end at it).
 *       WHO IS JUDGED (after the review, S3): only a bot whose loot tactic is on (heist stage 1 or more), that lost no
 *       health in the last 4 s and has no grab running (crew record +0x15 = 0). Such a bot within 2 m of a candidate
 *       would be taking it if it could - the loot tactic ranks over the chain's orders - so a bot on a cover hold
 *       beside good money either takes it (and earns: its clock starts again) or the money is the trap.
 *       WHAT IS NOT PUT BACK (S4): an object whose state byte +0x64 changed while it was sour - the level's Deactivate
 *       (0x4c95d0) writes +0x6c = 0 and +0x64 = 3 and leaves +0x74 - keeps the game's 0, one line.
 *       A pass that cannot read the session does not lose the marks (S10): they are put back by the next pass that
 *       can, at the round's end, or at the next round's start if the object is still the one it was.
 *    b. STUCK OFF ITS PLACE (Restless seconds): a bot that stood that long MORE than 3 m from its defend place (the
 *       place its route chain last ordered: the soldier's defend block, klescort.c 1) and lost no health in the last
 *       4 s (S1: a bot that fights from where it stands is not pulled out) gets that very order again by the
 *       soldier's own routine (place, 0, 1, 0) - what klhop.c's Reorder does after a carry: a running tactic is cut at
 *       its yield and the walk starts anew. The third time on one spot it is sent beside the human instead, if he is
 *       in play and more than 8 m away, and stays there; after four orders on one spot, or six for one place of its
 *       chain wherever it stood, it is left until its chain orders another place (one line). The chain's place stays
 *       the anchor while the defend block holds what THIS file put there (S2): the counts start again only when the
 *       chain orders a place more than 6 m from the one they began at.
 *    c. A MEANT WAIT IS LEFT ALONE. A bot within 3 m of its defend place is where its chain put it: a gate of the
 *       tower (kl_fa_bots_rt's TriggerActorsDead), a cover hold with its timer (kl_fa_bots_dyn), a loot wait, the
 *       place beside the van. That is how the part tells a meant wait from a stuck bot: BY THE DEFEND BLOCK - not by
 *       the squad's node, which the hook cannot read cheaply. Such a bot is only moved with RestlessHold=<seconds>
 *       (default 0 = never): then, not while it lost health in the last 4 s (it is in cover under fire), not while a
 *       vehicle is called, not within 5 m of a ZAllyEscapeBox, it gets an order to a place RestlessPace (350) from
 *       its chain's place, a new side each time - it shifts round its hold, the chain's place stays the centre, and
 *       the chain's next order takes it on as ever (a Defend step is over when its man has arrived, klescort.c 1; the
 *       wait behind it is a timer or a TriggerActorsDead, which do not look where he stands). GUESS: 3.5 m is inside
 *       the room a hold was chosen for; a hold at a doorway can put him through it.
 *    WAIT FOR YOU (WaitForYou=1).
 *    d. NOBODY CALLS THE VEHICLE BEFORE YOU: while the human is a heister in play and under heist stage
 *       WaitForYouStage (default 3 = 'only you call it': his own step into the exit trigger; 2 = until he has left the
 *       building; 1 = until he has entered it) or the round is younger than WaitForYouFloor seconds, and the vehicle's
 *       state is 0: [rules+0x1ee] = 1. A bot in the exit trigger gets its stage 3 and stands at its last place; no
 *       vehicle comes. Released (the byte back to 0, only if it is still ours and the state still 0) when the human
 *       reaches the stage, is dead, a fed or aboard, when WaitForYouMax seconds (150) have passed since the first bot
 *       stood ready at stage 3, and whenever the round or the level ends. A vehicle the rules call by themselves (the
 *       last one) is not held back; if it comes as state 1 the byte is taken back at once.
 *       THE OWNER DID NOT ASK FOR THIS KEY (his clarification: 'not before im ready i mean before reaching it').
 *       WHAT IT COSTS: the round clock is RED while the byte is ours (section 2), and the crew that is through the
 *       exit trigger stands at its last place - the escape box beside the vehicle's stop, in the open - for up to
 *       WaitForYouMax seconds (review S9: live check W1 counts the deaths against the same run without the key).
 *       The exit trigger fires again for somebody who is still standing in it when the byte goes back to 0: READ by
 *       the review (the trigger's update 0x65dd10 walks everybody inside every tick and calls 0x6c3d50 for each: it is
 *       level-triggered, not on entry). Live check W2 shows it.
 *    e. THE DRIVER WAITS FOR YOU (WaitForYouHold=<seconds a visit>, default 15 with WaitForYou=1): while the vehicle
 *       waits, the human is a heister in play and COMES (2 m nearer to the boarding place than 2 s before, or within
 *       15 m of it), its timer is under 2 s (and not 0), nobody paid the driver and the vehicle is not damaged:
 *       timer += min(5, what is left). FollowOutHold's rule with the roles exchanged (there: he is aboard, the crew
 *       comes); the same float, the same amount as the game's own hold.
 *    WALK TO THE CAR (BoardNear=<distance>; 100 = 1 m).
 *    f. Every ZAllyEscapeBox of the level (found at EVERY ROUND'S START by its vtable in the committed private memory,
 *       as klhud.c finds the display - once per round and not once per rules address, because a level loaded again
 *       can put its rules object where the last one was (review S6); the game stands still for the scan, HOW LONG IS
 *       NOT MEASURED, the 'near: N ZAllyEscapeBox object(s) found in .. ms' line says it each time (S7)) gets a
 *       private copy of the class's vtable whose slot 25 is this file's: it calls the stock update 0x907a50 unless the
 *       box is DENIED. Denied = the vehicle STANDS (state 3 / 4), its boarding place is known, the box's node is
 *       farther than BoardNear from it, it is not the round's last vehicle ([rules+0xe8a]) and fewer than
 *       BoardNearVisits (3) waits of a vehicle have begun this round; what was decided while it stood is kept through
 *       state 5 (the boarding object drives off with the vehicle then: a near box keeps the stock boarding of that
 *       state's first second, review S8). With 1500 the boxes beside the van still work (the bots stand 4 - 8 m from
 *       its doors and vanish there as today) and the bank's box at the drop does not. With 300 no box works: only
 *       the board tactic takes a bot aboard, within 3 m of the boarding object - 'physically'.
 *    g. BoardNearStage=1 (default): an AI heister at stage 1 or 2 that stands within 5 m of a denied box while the
 *       vehicle waits gets heist stage 3 (the byte BoardAll writes, with BoardAll's tests: no traitor, in play, not
 *       this round's escort, the record read again before the write) - otherwise nothing would take it on: the board
 *       tactic wants stage 3 (0x4fb064) and then runs it to the vehicle.
 *    h. WHAT BoardNear COSTS THE CREW (review M3). A bot a far box used to take aboard now has the vehicle's 8 s a
 *       visit to WALK there (the bank's drop box is 43 m from the van: 14 s at 3 m/s). When the vehicle goes WITHOUT
 *       the human it comes again (about every 29.5 s) and from visit BoardNearVisits on every box works. When it goes
 *       WITH THE HUMAN ABOARD, stock Arcade shoots every AI heister still in play (rules slot 7 = 0x74b6d0,
 *       re\bots_follow_out.md): in the owner's bank rounds records 4, 5 and 3 lived only because the drop's box took
 *       them. So BoardNear belongs together with [Bots] FollowOutHold=<seconds> (the driver waits while called crew
 *       comes) or FollowOutSpare=1 (nobody left behind is shot), and the part counts it. LIVE 2026-10-11 (runs N1c /
 *       N1 / N1b, BoardNear=1500 on the bank): in a plain 8 s visit NOBODY of the crew arrives (46 .. 56 m off when it
 *       leaves, five shot); a bot from inside the bank is aboard 24 .. 25.5 s after the call, the last of the crew
 *       would need about 36 s: FollowOutHold=25, with FollowOutShield (klescort.c 3 c2 - the unshielded 15 s hold of
 *       those runs got the van destroyed and the human killed aboard). Then, as before: at every departure one line
 *       'near: visit N: the vehicle leaves ...: K AI heister(s) still in play ..., M of them (*) stood at a denied box'.
 *    NOT ESTABLISHED: on which thread a controller's update runs (the wrapper only reads a table of at most eight
 *    entries the tick writes); what a bot in a denied box does whose stage-3 board tactic finds no path (it stands;
 *    from the third visit the box takes it).
 *
 * 4. BoardReach - A BOT GOES ABOARD ONLY WHERE A HUMAN CAN (track N4, 2026-10-11; re\bots_move.md 9)
 *    Owner, after playing BoardNear=1500: 'saw a bot get in the car and he was like 30 metres away like even i couldnt
 *    get in that point they need to be just as close but some do and they sprint for the van'.
 *    MEASURED. BoardNear tests a box's CENTRE. Every bots build has one box of 350 x 416 x 350 HALF extents (the box
 *    entity's 'point inside' is ZBoxPrimitive's vtable +0x170 = 0x4aca80: |local| <= the three floats at entity
 *    +0x14) beside the vehicle's stop; its far corner is 8.4 .. 13.2 m from where the human boards (the bank: 13.2).
 *    The human boards at the node with PlayerAction 'EnterVehicle' = [rules+0x1e0], on the van maps the box
 *    V_Van_00\BoardingTrigger, half extents 95 x 135 x 80 at the rear doors (he is at most 1.24 m from its middle);
 *    the park's helicopter: 400 x 200 x 300. The action is registered with NO radius (0x4c4ee0: -1.0), so its zone is
 *    that box (live ESC3: E inside it; what the 50.0 of 0x4c4efa adds was not read).
 *    THE RULE. The stock update 0x907a50 boards EVERYBODY inside in one call (its loop 0x907ab0..0x907aee: record by
 *    0x7fd930, AI bit +0x79, actor +4, status +0x10, inside 0x758cb0, then 0x74d7f0), so a per-bot test cannot be
 *    put in front of it: with BoardReach the private slot 25 DOES THE UPDATE ITSELF - the same calls with the same
 *    arguments in the same order, where the stock one would have run - and leaves out 0x74d7f0 for a record whose
 *    actor's node is farther than BoardReach from the boarding BOX (0 inside it). Nothing is written to hide anybody.
 *    The whole update (164 bytes), the head of each routine called and of the rule 0x6840a0 are compared with what was
 *    read before the key does anything.
 *    WHEN (fix round, review M1): the private update is armed through the WHOLE round and reads the vehicle's state
 *    [rules+0x1dc] and the boarding box ITSELF, in the frame it runs in (the first form waited for the tick, up to
 *    250 ms after state 3: the stock update took everybody who already stood in the box). States 0 / 1 / 2 / 6 / 7:
 *    the stock update (the rule takes nobody). 3 / 4: the box is read and kept; 5: the kept one (the object drives
 *    off). From visit BoardReachVisits on (default 3) and at the round's last vehicle ([rules+0xe8a]): the stock update.
 *    AT THE DOORS (BoardReachDoors=1, default): the same update also takes a CALLED bot (heist stage 3, what the board
 *    tactic asks) that is within BoardReach - and never more than 3 m (KLMV_DOORS_MAX) - of the boarding box and
 *    outside the escape box that is being updated (every wrapped box does it) - the escape boxes stand 3.6 ..
 *    8.4 m to the side of the doors, and the board tactic's test (0x4faf60) wants a path of more than one node: on Hot
 *    Coffee, Late Night Opening, The Vault and half of the park's box the crew's last places are on the boarding
 *    object's OWN mesh polygon (measured; that 'node' = polygon is a GUESS). Without this a bot there would stand.
 *    WHO IS NOT TAKEN: gets heist stage 3 if it has less (BoardNearStage, as g) and, if it then stands a second within
 *    30 m of the boarding box, ONE order a visit to the boarding object's place (BoardReachOrder=1; the board
 *    tactic's own goal, by the soldier's own routine as klescort.c calls it). A traitor and a held escort get no order.
 *    MOVED BY NOTHING OF THIS FILE (stock's box took all three): a traitor, a bot at heist stage 0, a bot more than
 *    30 m off. They board by their own tactics, or from visit BoardReachVisits on / at the last vehicle.
 *    THE KEY ALSO ACTS WHEN THE HUMAN IS POLICE (FollowOut does not): the crew then has to reach the doors with
 *    nobody holding the vehicle.
 *    BoardReach is measured from the boarding box's SURFACE and from any side (the human must be INSIDE the box);
 *    the game's own board tactic takes a walking stage-3 bot within 3 m of the box's node whatever this key says.
 *    BoardNear IS NOT NEEDED WITH IT: the bank's box at the drop is 44 m off and takes nobody within any sane reach.
 *    The cost is BoardNear's (h): the walk to the doors takes longer than the vehicle's 8 s - use FollowOutHold /
 *    FollowOutSpare. The board tactic itself (within 3 m of the boarding object's node) is the game's and stays.
 *    NOT ESTABLISHED: the thread of a controller's update (the update keeps its own copy of the boarding box under a
 *    sequence count; what the tick hands it is single words).
 *
 * KLHook.ini
 *   [Bots]
 *   Enable=1              klbot.c must be on (the crew records are read through it)
 *   Restless=0            seconds an AI heister may stand without moving 1 m or earning; 0 = off (try 5)
 *   RestlessLoot=         seconds on a money object that pays nothing before it is fed up; default = Restless, 0 = never
 *   RestlessLootBack=30   seconds the object is no candidate; doubled each time it sours again (240 at most)
 *   RestlessLootNear=200  how near the object's node the bot must stand (100 = 1 m)
 *   RestlessHold=0        seconds at its own hold place before it shifts round it; 0 = a meant wait is never touched
 *   RestlessPace=350      how far from the chain's place a shift goes
 *   WaitForYou=0          1 = nobody calls the vehicle before you, and the driver waits for you (the round clock is red meanwhile)
 *   WaitForYouStage=3     your heist stage that ends the wait (3 your own call, 2 out of the building, 1 inside)
 *   WaitForYouFloor=0     seconds after the round's start in which no vehicle is called, whatever your stage
 *   WaitForYouMax=150     seconds the crew waits at most, from the first bot that stood ready
 *   WaitForYouHold=15     seconds the driver is held per visit while you come; 0 = never. A held vehicle is shielded
 *                         by [Bots] FollowOutShield (default 2; klescort.c 3 c2): unshielded, a 15 s hold got the
 *                         bank's van destroyed with everybody aboard (live runs N1 / N1b, 2026-10-11)
 *   BoardNear=0           a ZAllyEscapeBox farther than this from the boarding place takes nobody aboard; 0 = off.
 *                         Use it with FollowOutHold or FollowOutSpare: who is left in play when you are driven out is shot
 *   BoardNearVisits=3     from this visit of a vehicle on every box works again (0 = never again)
 *   BoardNearStage=1      a bot under stage 3 at a denied box gets stage 3 (so that its board tactic walks it)
 *   BoardReach=0          a box takes an AI heister aboard only when THAT BOT is within this of the vehicle's boarding
 *                         box - where you get in (100 = 1 m from the box's surface; 0 = off; least 50; proposed 100).
 *                         BoardNear is not needed with it
 *   BoardReachDoors=1     a called bot (stage 3) within BoardReach (3 m at most) of the boarding box is taken there
 *   BoardReachOrder=1     a called bot that stands within 30 m of the boarding box is sent to the doors, once a visit
 *   BoardReachRepeat=0    s after an order to the doors before it may go again while the vehicle waits; a bot in an
 *                         escape box beyond BoardReach is then sent without the 1 s stand-still test (0 = off)
 *   BoardReachFlat=0      1 = from a boarding object that is no box (its node stands above the floor) BoardReach
 *                         ignores the height when the bot is within 2.5 m below / above it (0 = off)
 *   BoardReachSettle=0    cm (0 = off; suggested 200 GUESS, at most 300): a CALLED bot (stage 3) that is within this of the
 *                         boarding box is taken aboard like one within BoardReach, in an escape box or at the doors.
 *                         DM02 L18 record 4 stood 1.4-3.3 m off: the game takes the order as 'there already', the doors
 *                         path wants BoardReach 1.0 m, so it was never taken and never sent again
 *   BoardReachChase=0     1 = (needs BoardReachRepeat) a called bot that already got an order to the doors this visit and
 *                         is walking off (the game's chain overrides the order within 250 ms) is sent again every
 *                         BoardReachRepeat s without the 1 s stand-still test, up to the 30 m limit. DM02 L18 record 5
 *                         was overridden at once, never stood still, and was out of the 30 m before the test passed
 *   BoardReachAim=0       cm (0 = off; suggested 150 GUESS, at most 300): the order to the doors goes to a point this far from the
 *                         boarding object towards the bot, at the bot's own height, not to the object's node. DM02 L21: bots 3-6 m
 *                         off sent to the node (-615, 122, -8712) walked away onto the y 22 deck (a detour) and drifted 10-18 m out
 *   BoardReachFight=0     1 = a CALLED bot (stage 3) hurt in the last 4 s and within BoardReachFightRange of the boarding box skips the
 *                         1 s stand-still test and gets the order to the doors (a fighting bot never 'stands'; Vault L24 record 4
 *                         stalled in a firefight 12 m from the van). Once a visit unless BoardReachRepeat is set. Needs BoardReach;
 *                         from BoardReachVisits on and at the round's last vehicle the reach code is off, so this is too (0 = off)
 *   BoardReachFightRange=1500  cm (15 m GUESS) for BoardReachFight, at most 3000
 *   LastVehicleLead=25    tenths of a s (2.5 s = the old literal, default; at least 25): the no-vehicle fallback of LastVehicle calls the
 *                         escape vehicle this long before the round's end. Last Call HELI3 missed its window; 150 (15 s) is a GUESS for a test
 *   BoardReachVisits=3    from this visit of a vehicle on the boxes work as in stock again (0 = never; the round's
 *                         last vehicle always works as in stock)
 *   MoveDry=0           1 = every line, NOTHING written or called (the boxes are not wrapped either)
 *   MoveLog=1             2 = also every order and every bot that holds a meant wait
 *
 * LOG (the lines the live checks look for)
 *   move: on; Restless=5 s Loot=5 s (back 30 s, near 200) Hold=0 s Pace=350 ...
 *   move: record 3 stood 5.5 s at (x, y, z) 0.9 m from money object 1a2b3c00 ($75000 left, active 1, state 1) and nothing was paid: FED UP - the object is no loot candidate for 30 s (time 1)
 *   move: money object 1a2b3c00 is a loot candidate again (30 s are over)
 *   move: record 3 stood 5.0 s at (x, y, z), 12.4 m from its place (x, y, z): its order is given again; the game set (x, y, z); time 1 on this spot
 *   move: record 3 stood ... : sent beside you (x, y, z) ...
 *   move: record 3 shifts round its hold (x, y, z) after 15.0 s: to (x, y, z), the game set (x, y, z)
 *   wait: on; ... / wait: no vehicle is called before you ... (rules +0x1ee = 1) / wait: record(s) 1 4 stand ready at stage 3 ...
 *   wait: released (you have reached heist stage 3): the exit trigger calls the vehicle again
 *   wait: hold: the vehicle would leave in 1.7 s and you are 22.0 m from it, coming: timer 1.7 -> 6.7 s (5.0 of 15.0 s used this visit)
 *   near: 2 ZAllyEscapeBox object(s) found in 140 ms: (x, y, z) (x, y, z); slot 25 wrapped
 *   near: visit 1: the box at (x, y, z) is 43.0 m from the boarding place (x, y, z), over BoardNear 15.0 m: it takes nobody aboard
 *   near: record 5 (stage 2) at (x, y, z) stands at a denied box: heist stage set to 3 - it has to walk to the vehicle
 *   near: visit 1 is over: the denied box at (x, y, z) was asked 212 time(s)
 *   near: visit 1: the vehicle leaves WITH YOU ABOARD: 3 AI heister(s) still in play (record, metres from the boarding place: 3 44 m 4* 12 m 5* 9 m), 2 of them (*) stood at a denied box on this visit - THE RULES SHOOT THEM NOW ...
 *   reach: on; BoardReach=200 Visits=0 Doors=1 Order=1 Stage=1: ...
 *   reach: visit 1: the vehicle's boarding box (where YOU get in) is 95 x 135 x 80 (half extents) round (x, y, z): an AI heister goes aboard only within 2.0 m of that box ...
 *   reach: visit 1: record 7 (bot, stage 3) at (x, y, z) stands in an escape box 9.6 m from the boarding box, over BoardReach 2.0 m: the box does not take it - it has to walk to the doors
 *   reach: visit 1: record 7 (stage 3) stood 9.6 m from the boarding box at (x, y, z): sent to the doors (x, y, z), the game set (x, y, z)
 *   reach: record 7 (stage 3) is taken aboard AT THE DOORS: it stood 1.4 m from the boarding box, outside the escape box that asked
 *   reach: visit 1 is over: an escape box took an AI heister within reach 0 time(s), the doors 5 time(s); 1310 time(s) a box was asked for one beyond BoardReach and did not take it
 */
#ifndef KLMOVE_C
#define KLMOVE_C

#define KLMV_MONEY_VT   0x00bc874c            /* ZOnlineMoneyCtrl (the class's only vtable, 34 slots) */
#define KLMV_ALLY_VT    0x00bc7f6c            /* ZAllyEscapeBox (the class's only vtable, 34 slots) */
#define KLMV_ALLY_TICK  0x00907a50            /* its slot 25: void __thiscall (box), no argument */
#define KLMV_ALLY_SLOT  25
#define KLMV_VT_N       34
#define KLMV_NBOX       8
#define KLMV_NSOUR      16
#define KLMV_NOBJ       160
#define KLMV_OFF        300.0f                /* farther than this from its defend place = not at it (the game's own 'he is there' is 250) */
#define KLMV_TOTAL      6                     /* orders of (b) for ONE place of its chain, wherever the bot stood; then it is left */
#define KLMV_SAME       3                     /* v82f: orders of (b) to the SAME target, none of them brought the bot 200 closer: the target is dropped (left to its chain / the game) */
#define KLMV_PROGRESS   200.0f                /* v82f: less than this nearer the target (2 m) since the last order to it = no progress. GUESS (HELI3: 7 and 8.3 m from it at both orders, same z) */
#define KLMV_BOXR       500.0f               /* a bot within this of a box's node stands 'at' the box (a box is 350 x 416 x 350). GUESS */
/* BoardReach (section 4): what the stock update 0x907a50 calls, in its order */
#define KLMV_SESSION    0x0168e598            /* the session object (0x907a53) */
#define KLMV_HOLDER     0x0168e9e4            /* [this + 0x54] = the Arcade rules object (0x907a66 -> 0x508ef0) */
#define KLMV_ARCADE     0x007f6850            /* char __thiscall (session): the session is an Arcade one */
#define KLMV_RULESOF    0x00508ef0            /* rules * __thiscall (holder): [holder + 0x54] in Arcade, else 0 */
#define KLMV_NODEPOS    0x007b3020            /* void __thiscall (node, float v[3]): v through the node and its parents into the world */
#define KLMV_INSIDE     0x00758cb0            /* char __thiscall (box controller, actor): the actor's node (or its second point) inside the box entity */
#define KLMV_BOARD1     0x0074d7f0            /* void __thiscall (rules, char index): rules vtable +0xb4 (0x6840a0) with that record's actor */
#define KLMV_BOX_IN     0x004aca80            /* ZBoxPrimitive vtable +0x170: |local| <= the three floats at entity +0x14 (+ a margin) = HALF extents */
/* LAST VEHICLE (section 6, 2026-10-14, w_rt): the round's last vehicle when the game's own forced call brought none */
#define KLMV_EXIT_VT    0x00bc8c1c            /* ZOnlineExitLevelTrigger (RTTI; slot 34 = 0x6c3d50, slot 25 = 0x65dd10) */
#define KLMV_CALLVEH    0x008154f0            /* void __thiscall (rules, vehicle, char last): what rules slot 44 (0x6cd8e0) and the forced last call (0x81e570) call; ret 8 */
#define KLMV_LAST_AT    1.75f                 /* s left on the round clock: the game's own forced call is at 2.0 (0x81e570); this is the fallback after it */
#define KLMV_LAST_NOVEH 2.5f                  /* s left: with NO vehicle known to the rules the game's own call at 2.0 cannot happen (0x81e5aa), so there is nothing to give a frame to (v82d) */
#define KLMV_CLOCK_LEAD_GUESS 10.0f           /* v82e GUESS: how many s the HUD clock [rules+0x4c] runs ahead of the END timer [rules+0x200] when the latter cannot be read (HELI3: 10.25 s at the end) */
#define KLMV_SENT       3000.0f               /* BoardReachOrder: only a bot within this of the boarding box is sent to the doors. GUESS */

/* a box entity in the world: its node's place, its three axes, its half extents (box = 0: not a ZBoxPrimitive, a point) */
struct klmv_fr { float T[3], ax[3][3], half[3]; int box; };

static struct {
    int any, dry, log;
    DWORD restless, loot, back, hold, after; float pace, loot_near;      /* after = RestlessAfter (ms from the round start) */
    int wait, wait_stage; DWORD wait_max, wait_floor; float wait_hold;
    float near_; int near_visits, near_stage;
    float reach; int reach_visits, reach_doors, reach_order;
    DWORD hop; float hop_max;      /* RestlessHop (section 5): seconds at a hold before a hop to a cover place of the level's [Hops]; 0 = off */
    DWORD flagok;                  /* [Bots] LastVehicleFlagged (2026-10-18, L29 Last Call: the human's death set [rules+0xe8a] with no vehicle called): 1 = a flag with state 0 and no vehicle does not stop the last-vehicle fallback / BotVan; 0 = off (default) */
    float last_lead;               /* [Bots] LastVehicleLead (2026-10-18, Last Call HELI3 missed its window): s before the round's end from which the no-vehicle fallback calls the escape vehicle; 2.5 = the old literal (default) */
    int reach_fight;               /* [Bots] BoardReachFight (2026-10-18, Vault L24 record 4): 1 = a called, hurt bot within reach_fight_range of the boarding place is sent to the doors without the stand-still test; 0 = off (default) */
    float reach_fight_range;       /* [Bots] BoardReachFightRange: cm, default 1500 (15 m GUESS) */
    int last;                      /* LastVehicle (section 6): 1 = the fallback last vehicle is on (default), 0 = off */
    float reach_settle;            /* [Bots] BoardReachSettle (2026-10-18, DM02 L18 record 4): cm; a called bot within this of the boarding box counts as within BoardReach; 0 = off (default) */
    float reach_aim;               /* [Bots] BoardReachAim (2026-10-18, DM02 L21): cm; the doors order aims this far from the boarding object towards the bot, at its height; 0 = off (default) */
    int reach_chase;               /* [Bots] BoardReachChase (2026-10-18, DM02 L18 record 5): 1 = a bot that got an order this visit and walks off is re-sent without the stand-still test; 0 = off (default) */
    int reach_flat;                /* [Bots] BoardReachFlat (2026-10-18, DM02 L16): BoardReach from a boarding object that is no box ignores the height within 2.5 m; 0 = off (default, old behaviour) */
    DWORD reach_repeat;          /* [Bots] BoardReachRepeat (2026-10-18, 3f's DM02 run L14: orders to the doors were overridden by the game's chain within 4-14 s and never sent again; bots in an escape box 2.5-3.1 m off never stood the 1 s): ms after an order to the doors before it may be sent again while the vehicle waits, and a bot in an escape box beyond BoardReach is sent without the stand-still test; 0 = off (default, old behaviour) */
    int skip_down;                 /* [Bots] RestlessSkipDowned (2026-10-18, 3f saw bot 4 ordered while down at 02:09:14): a downed bot gets no order, snap or hop from klmv_restless and its counters stand still; 0 = off (default, old behaviour) */
    DWORD snap_range, snap_human; int snap, snap_cap;      /* RestlessSnap (2026-10-18, audit E2.2): after N orders to one place that did not bring the bot there, the bot is put at its chain's place; 0 = off */
    int escprobe, escfix;          /* [Bots] EscVisitProbe / EscVisitFix (2026-10-18, visit 1 never boards on Park II / Vault / Hot Coffee II): 1 = on, 0 = off (default) */
    int probe;                     /* [Bots] BoardProbe (2026-10-18, L34/L35 human E presses do not board): 1 = every 500 ms while the escape vehicle state is 3/4/5 one 'boardprobe:' line, read-only; 0 = off (default) */
    DWORD botvan;                  /* BotVan (section 7, v78): ms a loyal AI heister has had stage 3 with no vehicle before the hook calls one; 0 = off */
    /* [Bots] StairGather (2026-10-18, census of four Hasta runs, F04 / DM11B): the crew survives the 'nest' men of the stair squads only when 5-6 bots
       arrive together; the lead bot runs ahead alone. 0 = off (default, nothing here runs). PER-MAP: the ini is installed per level and nothing
       checks the level's name - the gather point is Hasta's. */
    int gather, gather_n; DWORD gather_radius, gather_timeout; float gather_at[3];
    int crew_alone;                /* [Bots] CrewRouteAlone (2026-10-18, Park II run N1018_L66: the watch script keeps you in play and never boards, so CrewRouteHold never ran and visit 1 left after its 8 s with 4 bots still on the route): 1 = CrewRouteHold also runs while you are IN PLAY (status 0), not only aboard; 0 = off (default) */
    float crew_hold, crew_range;   /* [Bots] CrewRouteHold (2026-10-18, Vault L61: the crew's walk out of the vault is ~120 m by route and leads AWAY from the van in a straight line, so klescort's 'comes nearer' test never passed and the van left after its 8 s): seconds per visit the van's timer may get while a called bot WALKS (moves 2 m in 2 s, whichever way) within CrewRouteRange m of the boarding place and you are aboard; 0 = off (default, nothing here runs) */
    float van_near; DWORD van_delay; int van_min;      /* [Bots] VanCallNear (2026-10-18, overnight census: 105 bot-instances of stage 1/2 were still in play when the van left, 154 of stage 3; e.g. Hot Coffee II L70 record 7 at stage 2 with $680000 stood 6 m from the doors): metres, 0 = off (default) */
    int van_last; float crew_hop;      /* [Bots] VanCallLast (2026-10-18, Last Call L72: 5 of 7 bots at stage 1, 29-45 m out, when the last van waited): 1 = on the round's last vehicle VanCallNear's distance is ignored; 0 = off (default). CrewRouteHopHold: seconds the CrewRouteHold budget may grow once a visit when it ran out while a stage-3 bot was still closing in (or had within the last 15 s: a hop waits 10 s); 0 = off (default) */
    DWORD gather_lone; int gather_minhp;      /* StairGatherLoneMs (0 = off): ms a held bot may stand with fewer than 2 loyal bots in the radius before it alone is released; StairGatherMinHp (0 = off): percent of the most health it was seen with, below which no hold is started */
} klmv;

/* ACTIVE (section 5, 2026-10-12): the level's list of cover places a bot may shift to while it waits at a hold, per GATE of the
   tower's way out. KLJoin.ini [Hops] (tools\kl_fa_bots_rt.py hops): Max=<most walk from a hold>, Gates=<n>, per gate g:
   Gate.g.Holds=<n>, Gate.g.Hold.j=x y z, Gate.g.Hops=<n>, Gate.g.Hop.j=x y z. A bot is at gate g when its chain's place lies
   within 150 of one of g's holds on its floor; it hops only to g's own places (a place of another gate may lie in a box that
   wakes men its gate did not mean to wake). Read again when kljoin.c's file changes. */
#define KLMV_NHOP 320
#define KLMV_NHOLD 320
#define KLMV_HOP_KEEP 10000       /* a hop one bot was sent to is no hop for another for this many ms (two bots in one tick went to the same place, 15:01:52) */
static float klmv_hops[KLMV_NHOP][3]; static int klmv_hop_g[KLMV_NHOP], klmv_nhop;
static float klmv_holds[KLMV_NHOLD][3]; static int klmv_hold_g[KLMV_NHOLD], klmv_nhold;
static float klmv_hop_dmax = 1800.0f;
static float klmv_hop_s[KLMV_NHOP], klmv_hold_s[KLMV_NHOLD];       /* progress along the route (100 = 1 m), -1 = the gate has none (the tower: no ordering) */
#define KLMV_PROG_SLACK 300.0f    /* a hop may lie this far behind the bot on the route (level with it across the lane) */
static DWORD klmv_hop_at[KLMV_NHOP]; static int klmv_hop_user[KLMV_NHOP];
static char klmv_hop_key[64], klmv_hop_file[MAX_PATH]; static FILETIME klmv_hop_ft;

struct klmv_b {
    DWORD actor, since, money, order_at, hit_at, look_obj, look_at; int seen, have_anchor, have_target, tries, total, phase, paced, beside, look_amount, reach_visit, hop_k; BYTE told;      /* told: 16 = a box did not take it on this visit, 32 = sent to the doors on this visit */
    float pos[3], hp, anchor[3], anchor0[3], target[3], try_pos[3];      /* anchor = the place its chain ordered; anchor0 = where the count 'total' began */
    int snaps;                                /* RestlessSnap: how often this bot was put at its place this round */
    float same_t[3], same_d; int same_n;      /* v82f: the target of the last (b) order, how far the bot was from it then, and how many orders in a row went to it without progress */
    int g_held, g_n; DWORD g_order_at, g_lone; int g_no; float g_hpmax, g_chain[3], g_ord[3];      /* StairGather: held now; orders given while held; when the last was given; the chain's goal it was held from; what the block held after our order */
};
static struct {
    DWORD rules, state, round_at, last_pass, half; int stages, told_gate, told_thread, told_list, told_ready;
    struct klmv_b b[KLB_NREC];
    int visit, was_waiting, scanned; BYTE was_veh; float near_bd[3]; DWORD gate_ready; int gate_told;
    int hold_visit, hold_told, h_comes; float hold_used, h_d; DWORD h_at;
    int rc_visit, rc_told; DWORD rc_wait_at;      /* BoardReach: the visit the boarding box was read for, its line said, when this wait began */
    int last_done, last_told;                     /* LastVehicle (section 6): 1 = looked at (called or found nothing to do) this round; the 2 s line said */
    DWORD bv_since, bv_last, bv_trig, bv_veh; int bv_told, bv_calls, flag_told;      /* BotVan (section 7) */
    int ev_have, ev_visit, ev_fixed; DWORD ev_st, ev_e0, ev_e4, ev_h;      /* EscVisitProbe / EscVisitFix: what was last seen, the visit of state 1/2 (counted here), the fix made on it */
    DWORD cr_at[KLB_NREC]; float cr_p[KLB_NREC][3]; BYTE cr_walk[KLB_NREC], cr_told; int cr_visit; float cr_used;      /* CrewRouteHold: per record the time/place of the last 2 s sample and whether it walked; the lines said; the visit; seconds given */
    float cr_extra; BYTE cr_xdone; DWORD cr_dat[KLB_NREC], cr_shr[KLB_NREC]; float cr_dd[KLB_NREC];      /* CrewRouteHopHold: seconds added to the budget, given this visit; per record the distance at the last 5 s sample, its time, and when the distance last shrank 1 m */
    DWORD vc_at; int vc_visit, vc_told, vc_n, vc_last_told;      /* VanCallNear: when this visit's wait was first seen, its visit, the line said, how many were called */
    DWORD g_at, g_first; int g_done;      /* StairGather: last pass, when the first bot was held (0 = none held), 1 = released this round (never again until the next round) */
} klmv_r;

/* BoardReach: what the tick decides and the boxes' update reads (section 4). armed = 1 through the WHOLE round on a
   level this file may act on (review M1: the tick comes up to 250 ms after the vehicle's state 3, and in that time the
   stock update took everybody who stood in the box) - the update itself reads the vehicle's state and the boarding box
   in the frame it runs in. Each field the tick writes is one word. fr = the UPDATE's own copy of the boarding box for
   state 5 (the object drives off with the vehicle), written and read by the update only, under seq (odd = being
   written; review S7: the update's thread is not established). far / took = one bit per crew record, set by the
   update, taken by the tick */
#define KLMV_DOORS_MAX  300.0f                /* the doors path never reaches farther than this from the boarding box, whatever BoardReach (review S3: stock has no box there at all; 3 m = the board tactic's own distance) */
#define KLMV_RULE       0x006840a0            /* rules vtable +0xb4: the boarding rule 0x74d7f0 calls */
static struct { volatile LONG armed, relax, seq, fr_ok; DWORD rules, fr_rules; struct klmv_fr fr; float reach, door_reach, settle; int doors; } klmv_rc;
static volatile LONG klmv_rc_far, klmv_rc_took, klmv_rc_refused, klmv_rc_box, klmv_rc_door;
static int klmv_reach_ok;                     /* 1 = the routines of section 4 are the ones this file read, -1 = not */

/* what outlives a round's bookkeeping: bytes this file has written into objects of the level */
static DWORD klmv_gate_rules;                 /* the rules object whose +0x1ee this file set (0 = none) */
static struct { DWORD obj, rules, until, at; int amount, count, on; BYTE active, state; } klmv_sour[KLMV_NSOUR];
static struct { DWORD at; float pos[3], d; volatile LONG deny; LONG asked; int told_visit, would; } klmv_box[KLMV_NBOX];      /* would = denied by the rule (deny stays 0 in a dry run); d = its distance to the boarding place while the vehicle stood */
static int klmv_nbox; static DWORD klmv_box_rules, klmv_vt[KLMV_VT_N + 1]; static int klmv_vt_ok;
static DWORD klmv_fail_at;                    /* since when klb_read fails (0 = it does not) */
static struct { DWORD obj; float pos[3]; int amount; BYTE active, state; } klmv_obj[KLMV_NOBJ]; static int klmv_nobj;

/* v82f: a place ANOTHER file ordered (klfedkit.c Hunted: a step TOWARDS the fed, a cover place, a step aside), per record. The block then holds a place
   that is not the chain's, and (b) below took it for the chain's place: HELI3 17:28:28 - 17:28:48, record 4 was ordered 52.9 m towards the human by
   klfedkit.c and (b) gave that order again, a fresh count for every new hunt step. klfk_hunted calls klmv_foreign() with what the game set. */
static float klmv_fo[KLB_NREC][3]; static BYTE klmv_fo_on[KLB_NREC];
static void klmv_foreign(int rec, const float got[3]) { if (rec >= 0 && rec < KLB_NREC) { memcpy(klmv_fo[rec], got, 12); klmv_fo_on[rec] = 1; } }

static float klmv_h(const float a[3], const float b[3]) { return (float)sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[2] - b[2]) * (a[2] - b[2])); }

/* ---------------------------------------------------------------- the loot candidates (list one of the rules) */

/* every object of list one that the loot tactic's filter would let through (0x8b9593..0x8b95f6), with its place */
static void klmv_objects(DWORD rules)
{
    DWORD arr, list[KLMV_NOBJ], node, ent; int n = 0, i; BYTE raw[0x84];
    klmv_nobj = 0;
    if (!klh_rd(rules + 0xdc0, &n, 4) || n <= 0 || n > 4096 || !(arr = klh_rd32(rules + 0xdcc))) return;
    if (n > KLMV_NOBJ) { if (!(klmv_r.told_list & 1)) { klmv_r.told_list |= 1; klog("move: the rules' money list has %d entries, the first %d are looked at", n, KLMV_NOBJ); } n = KLMV_NOBJ; }
    if (!klh_rd(arr, list, 4 * (SIZE_T)n)) return;
    for (i = 0; i < n; i++) {
        if (!list[i] || !klh_rd(list[i], raw, sizeof raw)) continue;
        if (*(DWORD *)raw != KLMV_MONEY_VT) {
            if (!(klmv_r.told_list & 2)) { klmv_r.told_list |= 2; klog("move: entry %d of the rules' money list (%08lx) is no ZOnlineMoneyCtrl (vtable %08lx): such entries are not looked at", i, list[i], *(DWORD *)raw); }
            continue;
        }
        if (*(int *)(raw + 0x34) <= 0 || !raw[0x6c]) continue;                 /* taken; or no candidate (also: soured by this file) */
        if (!(ent = *(DWORD *)(raw + 0x24)) || !(node = klh_rd32(ent + 4)) || !kle_node(node, klmv_obj[klmv_nobj].pos, 0)) continue;
        klmv_obj[klmv_nobj].obj = list[i]; klmv_obj[klmv_nobj].amount = *(int *)(raw + 0x34); klmv_obj[klmv_nobj].active = raw[0x74]; klmv_obj[klmv_nobj].state = raw[0x64];
        klmv_nobj++;
    }
}

/* is obj still an entry of this rules object's list one, and a ZOnlineMoneyCtrl? (before any write into it) */
static int klmv_listed(DWORD rules, DWORD obj)
{
    DWORD arr, list[KLMV_NOBJ]; int n = 0, i;
    if (!rules || klh_rd32(rules) != KLB_RULES_VT || !klh_rd(rules + 0xdc0, &n, 4) || n <= 0 || n > 4096 || !(arr = klh_rd32(rules + 0xdcc))) return 0;
    if (n > KLMV_NOBJ) n = KLMV_NOBJ;
    if (!klh_rd(arr, list, 4 * (SIZE_T)n)) return 0;
    for (i = 0; i < n; i++) if (list[i] == obj) return klh_rd32(obj) == KLMV_MONEY_VT;
    return 0;
}

/* a soured object becomes a candidate again. why 0 = no line (the level is gone or the game did it) */
static void klmv_sweeten(int k, const char *why)
{
    BYTE b = 1, st = 0; int amount = 0;
    if (!klmv_sour[k].on) return;
    klmv_sour[k].on = 0;
    if (!klmv_listed(klmv_sour[k].rules, klmv_sour[k].obj)) return;               /* the level is gone: nothing of ours is in memory that still is that object */
    if (!klh_rd(klmv_sour[k].obj + 0x6c, &b, 1) || b) return;                   /* the game re-armed it (a container was opened) */
    if (!klh_rd(klmv_sour[k].obj + 0x34, &amount, 4) || amount <= 0) return;    /* taken meanwhile: the game's own 0 */
    if (!klh_rd(klmv_sour[k].obj + 0x64, &st, 1) || st != klmv_sour[k].state) {  /* Deactivate (0x4c95d0) writes +0x6c = 0 AND state +0x64 = 3 and leaves +0x74: that 0 is the game's, not ours */
        if (klmv.log) klog("move: money object %08lx: its state went %u -> %u while it was sour (the level deactivated it?): its byte +0x6c is the game's now, nothing is written", klmv_sour[k].obj, klmv_sour[k].state, st);
        return;
    }
    if (klb_put8(klmv_sour[k].obj + 0x6c, 1, "money object: a loot candidate again") && why && klmv.log)
        klog("move: money object %08lx ($%d left) is a loot candidate again (%s)", klmv_sour[k].obj, amount, why);
}

static void klmv_sour_pass(DWORD rules, DWORD now)
{
    int k; BYTE raw[0x84];
    for (k = 0; k < KLMV_NSOUR; k++) {
        if (!klmv_sour[k].on) continue;
        if (klmv_sour[k].rules != rules || !klmv_listed(rules, klmv_sour[k].obj) || !klh_rd(klmv_sour[k].obj, raw, sizeof raw)) { klmv_sour[k].on = 0; continue; }
        if (raw[0x6c]) { klmv_sour[k].on = 0; if (klmv.log) klog("move: money object %08lx was re-armed by the game (opened): the AI heisters may come back for it", klmv_sour[k].obj); continue; }
        if (*(int *)(raw + 0x34) <= 0) { klmv_sour[k].on = 0; continue; }
        if (raw[0x64] != klmv_sour[k].state) klmv_sweeten(k, 0);                 /* says its own line and writes nothing */
        else if (*(int *)(raw + 0x34) != klmv_sour[k].amount) klmv_sweeten(k, "somebody took a part of it");
        else if (raw[0x74] != klmv_sour[k].active) klmv_sweeten(k, "its 'active' byte changed");
        else if (now - klmv_sour[k].at >= klmv_sour[k].until) klmv_sweeten(k, "its time is over");
    }
}

/* -> 1 soured, 0 not */
static int klmv_make_sour(DWORD rules, int o, DWORD now, DWORD *secs, int *times)
{
    int k, slot = -1; DWORD t;
    for (k = 0; k < KLMV_NSOUR; k++) if (klmv_sour[k].obj == klmv_obj[o].obj && klmv_sour[k].rules == rules) { slot = k; break; }      /* its own entry: the count goes on */
    if (slot < 0) for (k = 0; k < KLMV_NSOUR; k++) if (!klmv_sour[k].on && klmv_sour[k].rules != rules) { slot = k; break; }       /* an entry of a level that is gone */
    if (slot < 0) for (k = 0; k < KLMV_NSOUR; k++) if (!klmv_sour[k].on && (slot < 0 || klmv_sour[k].at < klmv_sour[slot].at)) slot = k;      /* the oldest one that is over */
    if (slot < 0) return 0;                                                    /* sixteen objects are sour already */
    if (klmv_sour[slot].obj != klmv_obj[o].obj || klmv_sour[slot].rules != rules) klmv_sour[slot].count = 0;
    t = klmv.back; for (k = 0; k < klmv_sour[slot].count && t < 240000; k++) t *= 2;
    if (t > 240000) t = 240000;
    if (!klmv.dry && !klb_put8(klmv_obj[o].obj + 0x6c, 0, "money object: no loot candidate for the AI heisters (it paid nobody)")) return 0;
    klmv_sour[slot].obj = klmv_obj[o].obj; klmv_sour[slot].rules = rules; klmv_sour[slot].at = KLB_T(now); klmv_sour[slot].until = t;
    klmv_sour[slot].amount = klmv_obj[o].amount; klmv_sour[slot].active = klmv_obj[o].active; klmv_sour[slot].state = klmv_obj[o].state; klmv_sour[slot].on = !klmv.dry; klmv_sour[slot].count++;
    *secs = t / 1000; *times = klmv_sour[slot].count;
    return 1;
}

/* ---------------------------------------------------------------- BoardNear: the ZAllyEscapeBox objects */

/* a box entity's frame: kle_node's walk (0x6be1c0: x' = x*m6 + y*m3 + z*m0 ..., the place at +0x24, the parent at
   +0x50) for the origin and the three axes; the half extents only from an entity whose 'point inside' is ZBoxPrimitive's
   (0x4aca80) and whose axes are of length 1 and square to each other - else it is a POINT (box = 0) */
static int klmv_frame(DWORD ent, struct klmv_fr *f)
{
    float v[4][3] = { { 0, 0, 0 }, { 1, 0, 0 }, { 0, 1, 0 }, { 0, 0, 1 } }, m[12], t[3]; DWORD node, vt; int depth, k, j;
    memset(f, 0, sizeof *f);
    if (!ent || !(node = klh_rd32(ent + 4))) return 0;
    for (depth = 0; node && depth < 32; depth++) {
        if (!klh_rd(node, m, sizeof m)) return 0;
        for (k = 0; k < 4; k++) {
            for (j = 0; j < 3; j++) t[j] = v[k][0] * m[6 + j] + v[k][1] * m[3 + j] + v[k][2] * m[j] + (k ? 0 : m[9 + j]);
            memcpy(v[k], t, sizeof t);
        }
        node = klh_rd32(node + 0x50);
    }
    if (node) return 0;
    for (k = 0; k < 4; k++) if (!kle_ok3(v[k])) return 0;
    memcpy(f->T, v[0], 12); memcpy(f->ax, v[1], 36);
    vt = klh_rd32(ent);
    if (vt > img_lo && vt < img_hi && klh_rd32(vt + 0x170) == KLMV_BOX_IN && klh_rd(ent + 0x14, f->half, 12) && kle_ok3(f->half)
        && f->half[0] > 0 && f->half[1] > 0 && f->half[2] > 0 && f->half[0] < 1e5f && f->half[1] < 1e5f && f->half[2] < 1e5f) {
        f->box = 1;
        for (k = 0; k < 3; k++) {
            float l = f->ax[k][0] * f->ax[k][0] + f->ax[k][1] * f->ax[k][1] + f->ax[k][2] * f->ax[k][2], *o = f->ax[(k + 1) % 3];
            if (l < 0.96f || l > 1.04f || fabs(f->ax[k][0] * o[0] + f->ax[k][1] * o[1] + f->ax[k][2] * o[2]) > 0.02f) f->box = 0;      /* scaled or sheared: its extents are not world lengths */
        }
    }
    return 1;
}

/* how far p is from the box (0 = inside it); from its node when it is a point */
static float klmv_fr_dist(const struct klmv_fr *f, const float p[3])
{
    float d[3], q, s = 0; int j;
    d[0] = p[0] - f->T[0]; d[1] = p[1] - f->T[1]; d[2] = p[2] - f->T[2];
    /* BoardReachFlat (2026-10-18, 3f's DM02 run L16): a boarding OBJECT that is no box has its node 1.22 m above the
       floor (-615, 122, -8712), so a bot ON the doors point was 1.22 m off and BoardReach 1.0 m never took anybody.
       With it the height is ignored when the bot is within 2.5 m (GUESS) below or above the node */
    if (!f->box && klmv.reach_flat && fabs(d[1]) <= 250.0f) d[1] = 0;
    if (!f->box) return (float)sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]);
    for (j = 0; j < 3; j++) { q = (float)fabs(d[0] * f->ax[j][0] + d[1] * f->ax[j][1] + d[2] * f->ax[j][2]) - f->half[j]; if (q > 0) s += q * q; }
    return (float)sqrt(s);
}

static void klmv_bit(volatile LONG *at, int i)
{
    LONG o;
    do o = *at; while (InterlockedCompareExchange(at, o | (LONG)(1u << i), o) != o);
}

/* BoardReach: the stock update 0x907a50 DONE HERE, call for call (section 4), with ONE test more per record: the bot
   itself must be within BoardReach of the vehicle's boarding box. Runs where the stock update runs (it is called in
   its place). What it touches is what the stock one touches: the box's own place cache at +0x4c (0x907a87) and, through
   0x74d7f0 -> 0x6840a0, the record that goes aboard. It reads the crew records and the actor's node besides. */
static void klmv_ally_reach(void *box)
{
    DWORD rules, ent, node, recs, actor, mine = klmv_rc.rules, obj; BYTE *rec, veh = 0, last = 0; float p[3], d = 0; int idx, inside, where, have = 0;
    struct klmv_fr fr; LONG q;
    /* WHAT THIS FRAME IS (review M1: read HERE, in the frame the rule 0x6840a0 would board in, not by the tick).
       Outside states 3 / 4 / 5 the rule takes nobody: the stock update. From BoardReachVisits on and at the round's
       last vehicle ([rules+0xe8a]): the stock update. States 3 / 4: the boarding box is read now (klmv_frame: reads
       only) and kept for state 5; it cannot be read = the stock update, as before */
    if (!mine || klh_rd32(mine) != KLB_RULES_VT || !klh_rd(mine + 0x1dc, &veh, 1) || veh < 3 || veh > 5) { klmv_rc.fr_ok = 0; goto stock; }
    klh_rd(mine + 0xe8a, &last, 1);
    if (klmv_rc.relax || last) goto stock;
    if (veh != 5) {
        if ((obj = klh_rd32(mine + 0x1e0)) != 0 && klmv_frame(obj, &fr)) {
            have = 1;
            InterlockedIncrement(&klmv_rc.seq); klmv_rc.fr = fr; klmv_rc.fr_rules = mine; klmv_rc.fr_ok = 1; InterlockedIncrement(&klmv_rc.seq);
        } else klmv_rc.fr_ok = 0;
    } else if (klmv_rc.fr_ok && klmv_rc.fr_rules == mine) {
        q = klmv_rc.seq; fr = klmv_rc.fr;
        if ((q & 1) || q != klmv_rc.seq) return;                               /* being written by another thread: nobody is taken by this box in this frame */
        have = 1;
    }
    if (!have) goto stock;
    if (!((char (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLMV_ARCADE))((void *)(DWORD_PTR)klh_rd32((DWORD_PTR)KLH_VA(KLMV_SESSION)), 0)) return;      /* 0x907a53 */
    rules = ((DWORD (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLMV_RULESOF))((void *)(DWORD_PTR)klh_rd32((DWORD_PTR)KLH_VA(KLMV_HOLDER)), 0);            /* 0x907a66 */
    if (!rules) return;
    ent = *(DWORD *)((BYTE *)box + 0x24); node = *(DWORD *)(DWORD_PTR)(ent + 4);                                  /* 0x907a78: a box that moves keeps its place at +0x4c */
    if (*(DWORD *)(DWORD_PTR)(node + 0x3c) & 0x20000000) {
        float *v = (float *)((BYTE *)box + 0x4c);
        v[0] = v[1] = v[2] = 0;
        ((void (__fastcall *)(void *, void *, float *))(DWORD_PTR)KLH_VA(KLMV_NODEPOS))((void *)(DWORD_PTR)node, 0, v);
    }
    for (idx = 0; idx < (int)(*(char (__fastcall **)(void *, void *))(DWORD_PTR)(*(DWORD *)(DWORD_PTR)rules + 0x50))((void *)(DWORD_PTR)rules, 0); idx++) {      /* 0x907a9a / 0x907adf: the count is asked every time round */
        recs = *(DWORD *)(DWORD_PTR)(rules + 0x348); rec = (BYTE *)(DWORD_PTR)(recs + 0x7c * (DWORD)(idx & 0xff));      /* 0x7fd930 */
        if (!(rec[0x79] & 1) || !(actor = *(DWORD *)(rec + 4)) || rec[0x10]) continue;                            /* an AI member, with an actor, in play */
        inside = ((char (__fastcall *)(void *, void *, void *))(DWORD_PTR)KLH_VA(KLMV_INSIDE))(box, 0, (void *)(DWORD_PTR)actor) != 0;
        /* THE TEST MORE: where = 1 within BoardReach of the boarding box, 2 beyond it, 0 not known (then as stock) */
        where = 0;
        if (rules == mine && (node = klh_rd32(actor + 4)) != 0 && kle_node(node, p, 0)) { d = klmv_fr_dist(&fr, p); where = d <= klmv_rc.reach ? 1 : 2; if (where == 2 && klmv_rc.settle > 0 && rec[0x78] >= 3 && d <= klmv_rc.settle) where = 1; }      /* BoardReachSettle */
        if (inside) {
            if (where == 2) { if (idx < 32) klmv_bit(&klmv_rc_far, idx); InterlockedIncrement(&klmv_rc_refused); continue; }
            InterlockedIncrement(&klmv_rc_box);
        } else {
            /* AT THE DOORS: outside THIS escape box, but as near the boarding box as BoardReach asks (3 m at most:
               KLMV_DOORS_MAX), and called (heist stage 3: what the board tactic asks, 0x4fb064). By EVERY wrapped box
               that is updated (review S4: the rule sets status 4 at once and the test above skips the record for the
               next box, so nobody is taken twice) */
            if (!klmv_rc.doors || where != 1 || d > (klmv_rc.settle > klmv_rc.door_reach ? klmv_rc.settle : klmv_rc.door_reach) || rec[0x78] < 3) continue;
            if (idx < 32) klmv_bit(&klmv_rc_took, idx);
            InterlockedIncrement(&klmv_rc_door);
        }
        ((void (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(KLMV_BOARD1))((void *)(DWORD_PTR)rules, 0, idx);      /* 0x907ad7 */
    }
    return;
stock:
    ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLMV_ALLY_TICK))(box, 0);
}

/* slot 25 of the private vtable (game code calls it as the box's update: __thiscall, no argument) */
static void __fastcall klmv_ally_tick(void *box, void *unused)
{
    int i;
    (void)unused;
    for (i = 0; i < KLMV_NBOX; i++)
        if (klmv_box[i].at == (DWORD)(DWORD_PTR)box) {
            if (klmv_box[i].deny) { InterlockedIncrement(&klmv_box[i].asked); return; }
            break;
        }
    if (klmv_rc.armed) { klmv_ally_reach(box); return; }
    ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLMV_ALLY_TICK))(box, 0);
}

static void klmv_scan(DWORD rules)
{
    static const BYTE code[16] = { 0x55, 0x8b, 0xe9, 0x8b, 0x0d, 0x98, 0xe5, 0x68, 0x01, 0xe8, 0xf2, 0xed, 0xee, 0xff, 0x84, 0xc0 };      /* 0x907a50 */
    static BYTE buf[0x10000]; MEMORY_BASIC_INFORMATION mbi; BYTE *a = (BYTE *)0x10000; DWORD t0 = GetTickCount(), stock = KLMV_ALLY_VT, mine = (DWORD)(DWORD_PTR)&klmv_vt[1];
    char line[400]; int i, k = 0, wrapped = 0;
    klmv_box_rules = rules; klmv_nbox = 0; memset(klmv_box, 0, sizeof klmv_box);
    if (!klmv_vt_ok) {
        if (!klh_rd((DWORD_PTR)KLH_VA(KLMV_ALLY_VT - 4), klmv_vt, sizeof klmv_vt) || klmv_vt[1 + KLMV_ALLY_SLOT] != KLMV_ALLY_TICK || !klb_same_code(KLMV_ALLY_TICK, code, sizeof code)) {
            klog("near: ZAllyEscapeBox's vtable / update are not the ones this build knows: BoardNear does nothing");
            klmv_vt_ok = -1; return;
        }
        klmv_vt[1 + KLMV_ALLY_SLOT] = (DWORD)(DWORD_PTR)klmv_ally_tick;           /* the RTTI locator at [-1] is kept */
        klmv_vt_ok = 1;
    }
    if (klmv_vt_ok < 0) return;
    if (klmv.reach > 0 && !klmv_reach_ok) {   /* BoardReach does the stock update itself: every byte of it, and the head of each routine it calls, must be what was read */
        static const BYTE whole[0xa4] = {
            0x55, 0x8b, 0xe9, 0x8b, 0x0d, 0x98, 0xe5, 0x68, 0x01, 0xe8, 0xf2, 0xed, 0xee, 0xff, 0x84, 0xc0, 0x0f, 0x84, 0x8c, 0x00, 0x00, 0x00, 0x8b, 0x0d, 0xe4, 0xe9, 0x68, 0x01, 0x56, 0xe8, 0x7e, 0x14,
            0xc0, 0xff, 0x8b, 0xf0, 0x85, 0xf6, 0x74, 0x79, 0x8b, 0x45, 0x24, 0x8b, 0x48, 0x04, 0xf7, 0x41, 0x3c, 0x00, 0x00, 0x00, 0x20, 0x74, 0x13, 0xd9, 0xee, 0x8d, 0x45, 0x4c, 0xd9, 0x50, 0x08, 0x50,
            0xd9, 0x50, 0x04, 0xd9, 0x18, 0xe8, 0x86, 0xb5, 0xea, 0xff, 0x8b, 0x16, 0x8b, 0x42, 0x50, 0x57, 0x8b, 0xce, 0x33, 0xff, 0xff, 0xd0, 0x84, 0xc0, 0x7e, 0x46, 0x8d, 0x9b, 0x00, 0x00, 0x00, 0x00,
            0x57, 0x8b, 0xce, 0xe8, 0x78, 0x5e, 0xef, 0xff, 0xf6, 0x40, 0x79, 0x01, 0x74, 0x21, 0x8b, 0x48, 0x04, 0x85, 0xc9, 0x74, 0x1a, 0x80, 0x78, 0x10, 0x00, 0x75, 0x14, 0x51, 0x8b, 0xcd, 0xe8, 0xdd,
            0x11, 0xe5, 0xff, 0x84, 0xc0, 0x74, 0x08, 0x57, 0x8b, 0xce, 0xe8, 0x11, 0x5d, 0xe4, 0xff, 0x8b, 0x16, 0x8b, 0x42, 0x50, 0x8b, 0xce, 0x47, 0xff, 0xd0, 0x0f, 0xbe, 0xc8, 0x3b, 0xf9, 0x7c, 0xc0,
            0x5f, 0x5e, 0x5d, 0xc3 };
        static const struct { DWORD va; BYTE b[16]; } head[7] = {
            { KLMV_RULE,    { 0x56, 0x8b, 0xf1, 0x8b, 0x0d, 0x98, 0xe5, 0x68, 0x01, 0xe8, 0x72, 0x29, 0x26, 0x00, 0x83, 0xf8 } },
            { KLMV_INSIDE,  { 0x83, 0xec, 0x10, 0xd9, 0xee, 0x56, 0x57, 0xd9, 0x54, 0x24, 0x14, 0x8b, 0x7c, 0x24, 0x1c, 0xd9 } },
            { KLMV_BOARD1,  { 0x0f, 0xbe, 0x54, 0x24, 0x04, 0x8b, 0x01, 0x6b, 0xd2, 0x7c, 0x8b, 0x80, 0xb4, 0x00, 0x00, 0x00 } },
            { KLMV_NODEPOS, { 0x56, 0x57, 0x8b, 0x7c, 0x24, 0x0c, 0x8b, 0xf1, 0x8b, 0xd6, 0x8b, 0xcf, 0xe8, 0x8f, 0xb1, 0xf0 } },
            { KLMV_ARCADE,  { 0x8b, 0x0d, 0x98, 0xe5, 0x68, 0x01, 0x8b, 0x41, 0x54, 0x83, 0xf8, 0x03, 0x77, 0x07, 0xff, 0x24 } },
            { KLMV_RULESOF, { 0x56, 0x8b, 0xf1, 0x8b, 0x0d, 0x98, 0xe5, 0x68, 0x01, 0x83, 0x79, 0x5c, 0x04, 0x75, 0x0e, 0xe8 } },
            { KLMV_BOX_IN,  { 0x8b, 0x54, 0x24, 0x04, 0xd9, 0x02, 0xd9, 0xe1, 0xd9, 0x5c, 0x24, 0x04, 0xd9, 0x44, 0x24, 0x04 } } };
        BYTE now_[sizeof whole];
        klmv_reach_ok = klh_rd((DWORD_PTR)KLH_VA(KLMV_ALLY_TICK), now_, sizeof now_) && !memcmp(now_, whole, sizeof whole) ? 1 : -1;
        for (i = 0; i < 7 && klmv_reach_ok > 0; i++) if (!klb_same_code(head[i].va, head[i].b, 16)) klmv_reach_ok = -1;
        if (klh_rd32((DWORD_PTR)KLH_VA(KLB_RULES_VT + 0xb4)) != KLMV_RULE) klmv_reach_ok = -1;      /* what 0x74d7f0 calls (review S8 d) */
        if (klmv_reach_ok < 0) klog("reach: ZAllyEscapeBox's update or a routine it calls is not the one this build knows: BoardReach does nothing");
    }
    while ((DWORD_PTR)a < 0x7ffe0000 && VirtualQuery(a, &mbi, sizeof mbi)) {
        if (mbi.State == MEM_COMMIT && mbi.Type == MEM_PRIVATE && (mbi.Protect == PAGE_READWRITE || mbi.Protect == PAGE_EXECUTE_READWRITE)) {
            SIZE_T o, j;
            for (o = 0; o < mbi.RegionSize; o += sizeof buf) {
                SIZE_T n = mbi.RegionSize - o < sizeof buf ? mbi.RegionSize - o : sizeof buf;
                if (!klh_rd((DWORD_PTR)mbi.BaseAddress + o, buf, n)) continue;
                for (j = 0; j + 4 <= n; j += 4) {
                    DWORD v = *(DWORD *)(buf + j), at, ent, evt, node;
                    if ((v != stock && v != mine) || klmv_nbox >= KLMV_NBOX) continue;
                    at = (DWORD)((DWORD_PTR)mbi.BaseAddress + o + j);
                    /* a real one has its entity at +0x24 (0x907a78 `mov eax, [ebp+0x24]`): an object of the game with a node */
                    if (!(ent = klh_rd32(at + 0x24)) || !(evt = klh_rd32(ent)) || evt < img_lo || evt >= img_hi || !(node = klh_rd32(ent + 4)) || !kle_node(node, klmv_box[klmv_nbox].pos, 0)) continue;
                    klmv_box[klmv_nbox++].at = at;
                }
            }
        }
        a = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    line[0] = 0;
    for (i = 0; i < klmv_nbox; i++) {
        if (k < (int)sizeof line - 40) k += snprintf(line + k, sizeof line - k, " (%.0f, %.0f, %.0f)", klmv_box[i].pos[0], klmv_box[i].pos[1], klmv_box[i].pos[2]);
        if (klmv.dry) continue;
        if (klh_rd32(klmv_box[i].at) == mine || klh_data((void *)(DWORD_PTR)klmv_box[i].at, &mine, 4, "ZAllyEscapeBox vtable (private copy, slot 25 wrapped)")) wrapped++;
        else klmv_box[i].at = 0;                                                /* not ours: its stock update runs, nothing is denied */
    }
    klog("near: %d ZAllyEscapeBox object(s) found in %lu ms (the game stood still that long; looked for anew at every round's start):%s; %s", klmv_nbox, GetTickCount() - t0, klmv_nbox ? line : " none - only the board tactic takes an AI heister aboard on this level",
         klmv.dry ? "DRY RUN: nothing is wrapped" : wrapped != klmv_nbox ? "NOT every one could be wrapped" : klmv.reach > 0 && klmv_reach_ok > 0 ? "slot 25 wrapped (BoardReach: a box takes an AI heister aboard only when THAT BOT is within reach of the vehicle's boarding box)"
         : "slot 25 wrapped (a box farther than BoardNear from the boarding place takes nobody aboard)");
}

/* 6. THE ROUND'S LAST VEHICLE WHEN THE GAME BRINGS NONE (LastVehicle=1, the default; 2026-10-14, w_rt).
 *    Owner: 'there's no final car on Retomoto Tower so time could expire instead of having a vehicle'.
 *    EXE (read for this section, objdump of kl2.exe 0490): every rules update ends in 0x81e570(dt) (from 0x58b60a). Unless
 *    [rules+0xe8a] ('the last vehicle was flagged') is set it calls 0x8154f0(vehicle, 1) in the frame the round clock
 *    [rules+0x4c] crosses 2.0 s - the stock 'last vehicle'. Its vehicle: with the vehicle kind [rules+0x1ec] = 3 the one
 *    the rules already know (0x6ece90 on [rules+0x1e4], filled only by an earlier call: 0x8154f0 -> [score+0x5c] -> slot 89),
 *    else [rules+0xe80] (written only by rules slot 31 = 0x7437b0 and cleared by the ctor and the round reset 0x8c7a80; no
 *    caller of slot 31 was found). So before the FIRST call of a level load there is no vehicle to force.
 *    LOG (KLHook.log, Retomoto F06, today): rounds 17:48:51, 19:24:47, 20:32:03, 20:38:40 ran the full 360 s + 10 s and
 *    ended with 'van 0' (no vehicle ever called in that load); round 20:58:53 got the forced one ('van 2' at 21:05:01, clock
 *    at 2 s) because round 20:51:55 of the same load had called it. Stock maps never show it: there the first crew member
 *    at the exit calls a van within 2 - 3 minutes; Retomoto's way out (rappel, tower, lift, 100 m of street) is longer.
 *    WHAT THIS DOES: in a round on a level that is not stock, once per round, when the clock shows KLMV_LAST_AT (1.75) s
 *    or less (and more than 0), the vehicle state [rules+0x1dc] is 0 and [rules+0xe8a] is 0 - the game's own call at 2.0 s
 *    did not happen - it calls 0x8154f0(rules, vehicle, 1) itself, from the game thread, with the vehicle the level's
 *    exit trigger names first (ZOnlineExitLevelTrigger +0x48 .. +0x54 = its fields 2 .. 5, what 0x6c3f90 hands to rules
 *    slot 44). That is the stock last call with a known vehicle: state 2, [rules+0xe8a] = 1, the 'last van' message
 *    (0x43ef40), the clock red; the round is held while the vehicle comes, waits and leaves (as 21:05:01 - 21:05:24).
 *    It never acts where the game acted (state not 0 or 0xe8a set), so stock levels and rounds that worked are untouched.
 *    The exit trigger is looked for (vtable scan of the private memory, as klmv_scan) only at that moment, once a round.
 *    NOT RUN IN THE GAME. NOT KNOWN: why the forced call also failed in rounds where the human was a fed (all four rounds
 *    above): the reading says 'no vehicle known'; if the cause is another, this still calls the vehicle. */
static DWORD klmv_exit_vehicle(DWORD *trig)
{
    static BYTE buf[0x10000]; MEMORY_BASIC_INFORMATION mbi; BYTE *a = (BYTE *)0x10000; DWORD vt = (DWORD)(DWORD_PTR)KLH_VA(KLMV_EXIT_VT);
    *trig = 0;
    while ((DWORD_PTR)a < 0x7ffe0000 && VirtualQuery(a, &mbi, sizeof mbi)) {
        if (mbi.State == MEM_COMMIT && mbi.Type == MEM_PRIVATE && (mbi.Protect == PAGE_READWRITE || mbi.Protect == PAGE_EXECUTE_READWRITE)) {
            SIZE_T o, j;
            for (o = 0; o < mbi.RegionSize; o += sizeof buf) {
                SIZE_T n = mbi.RegionSize - o < sizeof buf ? mbi.RegionSize - o : sizeof buf;
                if (!klh_rd((DWORD_PTR)mbi.BaseAddress + o, buf, n)) continue;
                for (j = 0; j + 4 <= n; j += 4) {
                    DWORD at, ent, evt, v[4]; int k;
                    if (*(DWORD *)(buf + j) != vt) continue;
                    at = (DWORD)((DWORD_PTR)mbi.BaseAddress + o + j);
                    if (!(ent = klh_rd32(at + 0x24)) || !(evt = klh_rd32(ent)) || evt < img_lo || evt >= img_hi) continue;      /* an object of the game with an entity */
                    if (!klh_rd(at + 0x48, v, sizeof v)) continue;
                    for (k = 0; k < 4; k++) if (v[k]) { *trig = at; return v[k]; }
                }
            }
        }
        a = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    return 0;
}

/* v82d (2026-10-17, AA step 6): what the clock showed last, so a round that ends WITHOUT the call can say why. NOT reset per round (klmv_r is wiped
   when a crew stage drops): rules says which round it belongs to. */
static struct { DWORD rules, at; float left, endt, rem; int n, sec, told_end, told_fail, passes; } klmv_lc;
/* v82e (2026-10-17, AA step 7): HELI3 showed the call never fired because the round does NOT end on the HUD clock [rules+0x4c]. kl2 0x5dff40 (rules slot 192)
   counts [rules+0x200] down from state 0x19 and sets state 0x1f when it is <= 0 (vehicle state 0 or >= 7); the HUD clock ran about 10 s ahead of it, so the game's
   own 2.0 s crossing on [4c] (0x81e570) never came before the end. The trigger is now the time left on [rules+0x200] ('rem'); the HUD clock is only a fallback. */

/* the round left state 0x19 (or the session could not be read) and the last call has not been made: say what the clock was, once */
static void klmv_last_end(DWORD rules, DWORD state, int read_failed)
{
    int *told = read_failed ? &klmv_lc.told_fail : &klmv_lc.told_end; char what[80];
    if (!klmv.last || !klmv_lc.rules || (rules && rules != klmv_lc.rules) || klmv_r.last_done || *told || !klmv_lc.passes) return;
    if (read_failed && klmv_lc.rem > 15.0f) return;
    *told = 1;
    if (read_failed) strcpy(what, "the session could NOT be read"); else snprintf(what, sizeof what, "the round left state 0x19 (now 0x%lx)", (unsigned long)state);
    klog("last: %s without the last-vehicle call: the HUD clock was last read %.2f s, the END timer %.2f s, time left taken as %.2f s (%lu ms ago; %d pass(es) in the round, %d of them within 15 s of the end) - %s",
         what, klmv_lc.left, klmv_lc.endt, klmv_lc.rem, GetTickCount() - klmv_lc.at, klmv_lc.passes, klmv_lc.n,
         klmv_lc.rem > 2.5f ? "no pass saw the time left in the 2.5 s window: it jumped or the round was ended by something else" : klmv_lc.rem <= 0.0f ? "the time left read 0 before a pass saw it in the window" : "a pass saw it in the window but did not call (see the lines above)");
}

static void klmv_last_vehicle(const struct klb_snap *s)
{
    static const BYTE head[16] = { 0x56, 0x8b, 0xf1, 0x80, 0xbe, 0xdc, 0x01, 0x00, 0x00, 0x00, 0x0f, 0x85, 0x9e, 0x00, 0x00, 0x00 };      /* 0x8154f0 */
    float left = 0, endt = 0, rem, limit; int endt_ok, game_frame; BYTE flagged = 0, kind = 0, veh = 0; DWORD known, e80, trig = 0, v, t0;
    if (!klh_rd(s->rules + 0x4c, &left, 4) || !klb_finite(left)) return;
    /* v82d: every pass is noted; from 10 s on each whole second is said once (the clock, and what the game has done), so the next live run shows what the code saw */
    if (klmv_lc.rules != s->rules) { memset(&klmv_lc, 0, sizeof klmv_lc); klmv_lc.rules = s->rules; klmv_lc.sec = 99; }
    /* v82e: the round's real end is the END timer [rules+0x200] (0x5dff40); where it reads sanely it is the time left, else the HUD clock minus the GUESSed lead */
    klh_rd(s->rules + 0x200, &endt, 4);
    endt_ok = klb_finite(endt) && endt > 0.0f && endt <= 700.0f;
    rem = endt_ok ? endt : left - KLMV_CLOCK_LEAD_GUESS;
    klmv_lc.left = left; klmv_lc.endt = endt; klmv_lc.rem = rem; klmv_lc.at = GetTickCount(); klmv_lc.passes++; if (rem <= 15.0f) klmv_lc.n++;
    if (klmv_r.last_done) return;
    if (!klh_rd(s->rules + 0xe8a, &flagged, 1) || !klh_rd(s->rules + 0x1ec, &kind, 1) || !klh_rd(s->rules + 0x1dc, &veh, 1)) return;
    known = klh_rd32(s->rules + 0x1e4); e80 = klh_rd32(s->rules + 0xe80);
    game_frame = (known || e80) && endt_ok && left <= endt + 0.5f;      /* the HUD clock is not ahead of the end timer: the game's own 2.0 s crossing can still come before the end */
    if (rem <= 15.0f && rem > 0.0f && (int)rem < klmv_lc.sec) {      /* v82e: from 15 s before the end, each whole second once */
        klmv_lc.sec = (int)rem;
        klog("last: %.2f s left to the end (END timer %.2f%s, HUD clock %.2f, offset %.2f; pass %d within 15 s): vehicle state %u, [rules+0xe8a] %u, kind %u, vehicle %08lx, +0xe80 %08lx; the call is made at %.2f s left or less (%s)",
             rem, endt, endt_ok ? "" : " NOT USABLE: HUD clock less the GUESSed lead", left, left - rem, klmv_lc.n, veh, flagged, kind, known, e80,
             game_frame ? KLMV_LAST_AT : KLMV_LAST_NOVEH, game_frame ? "a vehicle is known and the HUD clock is not ahead: the game's own call at 2.0 s gets its frame" : "no vehicle known, or the HUD clock runs ahead of the end: the game's own call cannot come in time");
    }
    left = rem;                               /* from here on 'left' is the time to the round's end */
    if (left > klmv.last_lead || left <= 0.0f) return;      /* LastVehicleLead: 2.5 s unless set */
    if (flagged && !veh && !known && klmv.flagok) {      /* LastVehicleFlagged (GUESS): flag without a vehicle (the kill rule 0x70498c sets it on a human death); 0x8154f0 does not read it on entry */
        if (!klmv_r.flag_told++) klog("last: %.2f s left: [rules+0xe8a] is %u but the vehicle state is 0 and no vehicle is known (kind %u, +0xe80 %08lx): LastVehicleFlagged=1, treating the flag as unset (it is left as it is)", left, flagged, kind, e80);
        flagged = 0;
    }
    if (veh || flagged) {                     /* the game called one (its own forced call at 2.0 s, or a call before that is still running): nothing to do */
        if (left > KLMV_LAST_NOVEH) return;   /* LastVehicleLead > 2.5: an ordinary visit still running this early may end before 2.5 s; only latch from 2.5 s on, as before (never true by default) */
        if (!klmv_r.last_told++) klog("last: %.2f s left: a vehicle is under way or the last one is flagged already (state %u, [rules+0xe8a] %u, kind %u, vehicle %08lx, +0xe80 %08lx): nothing done", left, veh, flagged, kind, known, e80);
        klmv_r.last_done = 1; return;
    }
    /* v82d: the game's own call (0x81e570) needs a vehicle: [rules+0x1e4] / [rules+0xe80] (0x81e5aa 'je' past the call when edi = 0). With none known it will NEVER come,
       so there is no frame to give it: the call is made from 2.5 s on. With one known the game gets its frame at 2.0 s and this follows at 1.75 s. */
    limit = game_frame ? KLMV_LAST_AT : klmv.last_lead;      /* LastVehicleLead replaces KLMV_LAST_NOVEH (same 2.5 by default) */      /* v82e: the frame is given only when the game's 2.0 s crossing on [4c] precedes the end */
    if (left > limit) return;
    klmv_r.last_done = 1;
    if (klh_rd32(s->rules) != KLB_RULES_VT || !klb_same_code(KLMV_CALLVEH, head, sizeof head)) { klog("last: %.2f s left and NO last vehicle, but the rules object or 0x8154f0 is not the one this build knows: nothing done", left); return; }
    t0 = GetTickCount();
    if (!(v = klmv_exit_vehicle(&trig))) { klog("last: %.2f s left and NO last vehicle (state 0, [rules+0xe8a] 0, kind %u, vehicle %08lx, +0xe80 %08lx); no ZOnlineExitLevelTrigger naming a vehicle was found (%lu ms): nothing done", left, kind, known, e80, GetTickCount() - t0); return; }
    if (klmv.dry) { klog("last: %.2f s left and NO last vehicle (kind %u, vehicle %08lx, +0xe80 %08lx): DRY RUN - the exit trigger %08lx's vehicle %08lx WOULD be called as the last one", left, kind, known, e80, trig, v); return; }
    if (klmv_r.flag_told) klog("last: LastVehicleFlagged ACTS: calling 0x8154f0(vehicle %08lx, 1) although [rules+0xe8a] was already set (state 0, no vehicle under way)", v);
    ((void (__fastcall *)(void *, void *, DWORD, int))(DWORD_PTR)KLH_VA(KLMV_CALLVEH))((void *)(DWORD_PTR)s->rules, 0, v, 1);
    veh = 0; flagged = 0; klh_rd(s->rules + 0x1dc, &veh, 1); klh_rd(s->rules + 0xe8a, &flagged, 1);
    klog("last: %.2f s left and the game called NO last vehicle (state 0, [rules+0xe8a] 0, kind %u, vehicle %08lx, +0xe80 %08lx): the exit trigger %08lx's vehicle %08lx called as the round's last (0x8154f0, found in %lu ms): state now %u, [rules+0xe8a] %u",
         left, kind, known, e80, trig, v, GetTickCount() - t0, veh, flagged);
}

/* 7. BotVan (v78, 2026-10-15). Owner: 'the van should spawn for the other ai heisters if they get to the van first on retomoto tower'.
 *    LOG 22:40:50 (Retomoto, the human a fed): record 4 (bot) took heist stage 3 - it stood in the level exit box, whose routine 0x6c3d50 gives
 *    the stage and then calls the vehicle through rules slot 44 (0x6cd8e0 -> 0x8154f0) - and the vehicle state stayed 0: no vehicle came for
 *    the crew. Why slot 44 refused was not read. This part makes the call slot 44 makes, 0x8154f0(rules, vehicle, 0), with the vehicle the
 *    level's exit trigger names (klmv_exit_vehicle, section 6), when a loyal AI heister in play has had stage 3 for BotVan seconds while the
 *    vehicle state [rules+0x1dc] is 0, the last vehicle is not flagged ([rules+0xe8a] 0), [rules+0x1ee] is 0 (WaitForYou or the game's own
 *    'last called' hold the call: then nothing) and the round clock shows more than 20 s. At most once per 25 s. NOT RUN IN THE GAME. */
static void klmv_bot_van(const struct klb_snap *s, DWORD now)
{
    static const BYTE head[16] = { 0x56, 0x8b, 0xf1, 0x80, 0xbe, 0xdc, 0x01, 0x00, 0x00, 0x00, 0x0f, 0x85, 0x9e, 0x00, 0x00, 0x00 };      /* 0x8154f0 */
    BYTE veh = 1, flagged = 1, hold = 1; float left = 0; int i, who = -1; DWORD v, t0;
    if (!klh_rd(s->rules + 0x1dc, &veh, 1) || !klh_rd(s->rules + 0xe8a, &flagged, 1) || !klh_rd(s->rules + 0x1ee, &hold, 1) || !klh_rd(s->rules + 0x4c, &left, 4)) return;
    if (flagged && !veh && klmv.flagok && klh_rd32(s->rules + 0x1e4) == 0) flagged = 0;      /* LastVehicleFlagged: a flag with no vehicle does not hold the call */
    if (veh || flagged || hold || !klb_finite(left) || left < 20.0f) { klmv_r.bv_since = 0; return; }
    for (i = 0; i < s->n; i++) {
        const struct klb_rec *r = &s->r[i];
        if (i != s->human && r->used && (r->flags & 1) && !(r->flags & 2) && r->status == 0 && r->stage >= 3) { who = i; break; }
    }
    if (who < 0) { klmv_r.bv_since = 0; return; }
    if (!klmv_r.bv_since) { klmv_r.bv_since = KLB_T(now); return; }
    if (now - klmv_r.bv_since < klmv.botvan || (klmv_r.bv_last && now - klmv_r.bv_last < 25000)) return;
    klmv_r.bv_last = KLB_T(now);
    if (klh_rd32(s->rules) != KLB_RULES_VT || !klb_same_code(KLMV_CALLVEH, head, sizeof head)) { if (!klmv_r.bv_told++) klog("botvan: record %d has stage 3 and no vehicle comes, but the rules object or 0x8154f0 is not the one this build knows: nothing done", who); return; }
    t0 = GetTickCount();
    if (!klmv_r.bv_veh || klh_rd32(klmv_r.bv_trig) != (DWORD)(DWORD_PTR)KLH_VA(KLMV_EXIT_VT)) klmv_r.bv_veh = klmv_exit_vehicle(&klmv_r.bv_trig);
    if (!(v = klmv_r.bv_veh)) { if (!klmv_r.bv_told++) klog("botvan: record %d has had stage 3 for %.1f s and no vehicle comes; no ZOnlineExitLevelTrigger naming a vehicle was found (%lu ms): nothing done", who, (now - klmv_r.bv_since) / 1000.0, GetTickCount() - t0); return; }
    if (klmv.dry) { klog("botvan: record %d has had stage 3 for %.1f s and the vehicle state is 0: DRY RUN - the exit trigger %08lx's vehicle %08lx WOULD be called", who, (now - klmv_r.bv_since) / 1000.0, klmv_r.bv_trig, v); return; }
    ((void (__fastcall *)(void *, void *, DWORD, int))(DWORD_PTR)KLH_VA(KLMV_CALLVEH))((void *)(DWORD_PTR)s->rules, 0, v, 0);
    klmv_r.bv_calls++;
    veh = 0; flagged = 0; klh_rd(s->rules + 0x1dc, &veh, 1); klh_rd(s->rules + 0xe8a, &flagged, 1);
    klog("botvan: record %d (AI heister, stage 3) has waited %.1f s with no vehicle (state 0, %.1f s on the clock): the exit trigger %08lx's vehicle %08lx CALLED for the crew (0x8154f0, as rules slot 44 does; call %d of the round, %lu ms): state now %u, [rules+0xe8a] %u",
         who, (now - klmv_r.bv_since) / 1000.0, left, klmv_r.bv_trig, v, klmv_r.bv_calls, GetTickCount() - t0, veh, flagged);
}

static void klmv_deny_none(void) { int i; klmv_rc.armed = 0; for (i = 0; i < KLMV_NBOX; i++) klmv_box[i].deny = 0, klmv_box[i].would = 0; }

/* the stage byte BoardAll writes, with BoardAll's tests (no traitor, in play, not this round's escort, the record
   looked at again before the write), so that the bot's board tactic walks it (0x4fb064 asks stage 3). what = where it stands */
static int klmv_s3_wrote;      /* set by klmv_stage3 when the stage byte was really written (VanCallNear logs 'called' only then) */
static void klmv_stage3(const struct klb_snap *s, int i, const char *what)
{
    const struct klb_rec *r = &s->r[i]; struct klmv_b *b = &klmv_r.b[i]; BYTE fl = 0, st = 0, cur = 3;
    if (!klmv.near_stage || (r->flags & 2) || kle_r.used[i] || r->stage < 1 || r->stage >= 3 || (b->told & 4)) return;      /* the escort is klescort.c's: it releases it to the boarding place when the vehicle waits */
    if (klmv.dry) { b->told |= 4; klog("near: record %d (stage %u) at (%.0f, %.0f, %.0f) stands %s: heist stage WOULD be set to 3 (dry run)", i, r->stage, b->pos[0], b->pos[1], b->pos[2], what); return; }
    if (!klb_still(s, i, &fl, &st) || st || (fl & 2) || !klh_rd(r->at + 0x78, &cur, 1)) return;      /* gone, aboard, dead or turned since the snapshot: looked at again */
    b->told |= 4;
    if (cur < 3 && !klb_put8(r->at + 0x78, 3, "crew record: heist stage 3 (an escape box does not take it: it has to walk to the vehicle)")) { klog("near: record %d: the stage byte was NOT written", i); return; }
    if (cur < 3) klmv_s3_wrote = 1;
    klog("near: record %d (stage %u) at (%.0f, %.0f, %.0f) stands %s: heist stage set to 3 - it has to walk to the vehicle (its board tactic takes it aboard within 3 m)", i, r->stage, b->pos[0], b->pos[1], b->pos[2], what);
}

/* 4. BoardReach, the tick's half: the boarding box is read while the vehicle stands and handed to the boxes' update;
   who the update did not take is said, gets stage 3 if it has less, and - if it stands - the order to the doors */
static void klmv_reach_pass(const struct klb_snap *s, DWORD now)
{
    struct klmv_fr fr, bf[KLMV_NBOX]; int i, j, waiting = s->veh == 3 || s->veh == 4, relax, have = 0, nb = 0, first = 0; DWORD obj, actor, soldier; LONG beyond = 0, took = 0;
    float d, bp[3], got[3], aim[3]; char w[100]; struct kle_e t; BYTE last = 0; int fight;
    if (klmv_reach_ok <= 0) { klmv_rc.armed = 0; return; }      /* also in a dry run (review S8 a): no 'WOULD' line for an update that would never be used */
    /* THE UPDATE IS ARMED FOR THE WHOLE ROUND (review M1): it reads the vehicle's state and the boarding box itself,
       in its own frame. The tick only says for which rules object, how far, and whether the boxes work as in stock
       from this visit on - for the visit that stands or drives off, else for the NEXT one (the visit count is the
       tick's and comes up to 250 ms after the vehicle's state 3) */
    klh_rd(s->rules + 0xe8a, &last, 1);
    relax = klmv.reach_visits && klmv_r.visit >= klmv.reach_visits;
    klmv_rc.rules = s->rules; klmv_rc.reach = klmv.reach; klmv_rc.door_reach = klmv.reach < KLMV_DOORS_MAX ? klmv.reach : KLMV_DOORS_MAX; klmv_rc.doors = klmv.reach_doors; klmv_rc.settle = klmv.reach_settle;
    klmv_rc.relax = klmv.reach_visits && klmv_r.visit + (waiting || s->veh == 5 ? 0 : 1) >= klmv.reach_visits;
    klmv_rc.armed = !klmv.dry;
    if (last) relax = 1;                      /* the round's last vehicle: nobody is stranded for good (review S2; the update reads the byte itself) */
    if (waiting && !relax && (obj = klh_rd32(s->rules + 0x1e0)) != 0 && klmv_frame(obj, &fr)) have = 1;
    if (!have) {
        if (waiting && klmv_r.rc_told != klmv_r.visit) {
            klmv_r.rc_told = klmv_r.visit;
            klog("reach: visit %d: %s: every escape box works as in stock", klmv_r.visit, last ? "the round's last vehicle" : relax ? "BoardReachVisits: from this visit on" : "the vehicle's boarding object ([rules+0x1e0]) cannot be read");
        }
    } else {
        for (i = 0; i < klmv_nbox; i++) if (klmv_box[i].at && !klmv_box[i].deny) { first = 1; break; }
        if (klmv_r.rc_visit != klmv_r.visit) {
            /* the counts are NOT zeroed here: what the update counted in this wait's first 250 ms belongs to it (they are
               zeroed when the visit's line is said, below) */
            klmv_r.rc_visit = klmv_r.visit; klmv_r.rc_wait_at = KLB_T(now);
            if (fr.box) klog("reach: visit %d: the vehicle's boarding box (where YOU get in) is %.0f x %.0f x %.0f (half extents) round (%.0f, %.0f, %.0f): an AI heister goes aboard only within %.1f m of that box%s%s%s", klmv_r.visit,
                             fr.half[0], fr.half[1], fr.half[2], fr.T[0], fr.T[1], fr.T[2], klmv.reach / 100, klmv.reach_doors ? klmv.reach > KLMV_DOORS_MAX ? " - in an escape box or, called (stage 3), within 3.0 m of it at the doors" : " - in an escape box or, called (stage 3), at the doors" : " and inside an escape box",
                             first ? "" : "; NO escape box of this level runs this file's update: only the board tactic takes a bot aboard", klmv.dry ? " (DRY RUN: nothing is wrapped, the lines say what would be)" : "");
            else klog("reach: visit %d: the vehicle's boarding object at (%.0f, %.0f, %.0f) is not a box this file knows: BoardReach %.1f m is measured from its node%s", klmv_r.visit, fr.T[0], fr.T[1], fr.T[2], klmv.reach / 100, klmv.dry ? " (DRY RUN)" : "");
        }
    }
    beyond = InterlockedExchange(&klmv_rc_far, 0); took = InterlockedExchange(&klmv_rc_took, 0);
    if (!waiting && klmv_r.was_waiting) {
        LONG nb_ = InterlockedExchange(&klmv_rc_box, 0), nd = InterlockedExchange(&klmv_rc_door, 0), nr = InterlockedExchange(&klmv_rc_refused, 0);
        if (klmv_r.rc_visit == klmv_r.visit && klmv.log)
            klog("reach: visit %d is over: an escape box took an AI heister within reach %ld time(s), the doors %ld time(s); %ld time(s) a box was asked for one beyond BoardReach and did not take it (who it did not take and who has no stage 3, is a traitor or stood more than 30 m off was moved by nothing of this file)", klmv_r.visit, (long)nb_, (long)nd, (long)nr);
    }
    if (!have) return;
    if (klmv.dry) for (i = 0; i < klmv_nbox; i++) if (klmv_box[i].at && !klmv_box[i].would && klmv_frame(klh_rd32(klmv_box[i].at + 0x24), &bf[nb]) && bf[nb].box) nb++;      /* a dry run: this file's own 'inside' */
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; struct klmv_b *b = &klmv_r.b[i]; int out;
        if (!r->used || !(r->flags & 1)) continue;
        if (i < 32 && (took >> i & 1) && klmv.log) klog("reach: record %d (stage %u) is taken aboard AT THE DOORS: it stood %.1f m from the boarding box, outside the escape box that asked", i, r->stage, b->seen ? klmv_fr_dist(&fr, b->pos) / 100 : 0.0);
        if (r->status || !b->seen) continue;
        d = klmv_fr_dist(&fr, b->pos);
        out = i < 32 && (beyond >> i & 1);
        if (klmv.dry && d > klmv.reach) for (j = 0; j < nb && !out; j++) out = klmv_fr_dist(&bf[j], b->pos) <= 0;
        if (out) {
            b->told |= 16;                                                     /* for the line at the departure */
            if (b->reach_visit != klmv_r.visit) {
                b->reach_visit = klmv_r.visit;
                klog("reach: visit %d: record %d (%s, stage %u) at (%.0f, %.0f, %.0f) stands in an escape box %.1f m from the boarding box, over BoardReach %.1f m: the box %s - %s", klmv_r.visit, i,
                     r->flags & 2 ? "TRAITOR" : kle_r.used[i] ? "an escort" : "bot", r->stage, b->pos[0], b->pos[1], b->pos[2], d / 100, klmv.reach / 100, klmv.dry ? "WOULD not take it (dry run)" : "does not take it",
                     /* who is refused and moved by nothing of this file (review S5) */
                     r->flags & 2 ? "a traitor gets no order and no stage write: only its own tactics move it"
                     : kle_r.used[i] ? "klescort.c releases it to the boarding place"
                     : r->stage < 1 ? "heist stage 0: no stage write (BoardAll's rule) and no order - nothing of this file moves it"
                     : d > KLMV_SENT ? "it has to walk to the doors (more than 30 m off: no order from this file)" : "it has to walk to the doors");
            }
            klmv_stage3(s, i, "in an escape box beyond BoardReach");
        }
        /* THE ORDER TO THE DOORS. A called bot (stage 3) near the vehicle that does not move: its board tactic is off
           (its test 0x4faf60 asks a path of MORE THAN ONE node: a bot on the boarding object's own mesh polygon has
           none - GUESS that this is what holds it; four of the six maps park the crew on that polygon) or has no path.
           It gets the tactic's own goal - the boarding object's place - as its order, once a visit, by the soldier's
           own routine (klescort.c). There the doors take it. Not a traitor, not a held escort: kle_bot / below */
        if (klmv.reach_repeat && (b->told & 32) && b->order_at && KLB_T(now) - b->order_at >= klmv.reach_repeat) {
            b->told &= (BYTE)~32;                                               /* BoardReachRepeat: the order may go again on this visit */
            if (klmv.log > 1) klog("reach: visit %d: record %d: %.1f s since its order to the doors, %.1f m from the boarding box: it may be sent again (BoardReachRepeat)", klmv_r.visit, i, (KLB_T(now) - b->order_at) / 1000.0, d / 100);
        }
        if (!klmv.reach_order || r->stage < 3 || (r->flags & 2) || d <= klmv.reach || (klmv.reach_settle > 0 && d <= klmv.reach_settle) || d > KLMV_SENT || (b->told & 32)) continue;
        fight = klmv.reach_fight && b->hit_at && now - b->hit_at < 4000 && d <= klmv.reach_fight_range;      /* BoardReachFight: a hurt bot near the doors fights where it is and never 'stands' */
        if ((now - b->since < 1000 && !fight && !(klmv.reach_repeat && out) && !(klmv.reach_repeat && klmv.reach_chase && b->order_at && b->order_at >= klmv_r.rc_wait_at)) || now - klmv_r.rc_wait_at < 1000) continue;  /* it stands, a second into the wait (BoardReachRepeat: a bot in an escape box need not stand) */
        for (j = 0; j < KLE_MAX; j++) if (kle_r.e[j].mode == 1 && kle_r.e[j].rec == i) break;
        if (j < KLE_MAX) continue;                                              /* klescort.c holds it beside the human */
        b->told |= 32;
        if (!kle_bot(s, i, &actor, &soldier, bp, w)) { if (klmv.log) klog("reach: record %d stands %.1f m from the boarding box and gets no order to the doors: %s", i, d / 100, w); continue; }
        if (kle_dist(bp, fr.T) <= 260.0f) continue;                             /* the game would take it as 'he is there already' (soft): a waiting step of its chain would end */
        memset(&t, 0, sizeof t); t.rec = i; t.actor = actor; t.soldier = soldier; t.told_soft = 1;
        kltr_set("move-reach", "BoardReach: to the doors of the waiting vehicle", -1);
        memcpy(aim, fr.T, 12);
        if (klmv.reach_aim > 0) {      /* BoardReachAim: a point on the bot's own floor, reach_aim cm from the boarding object towards the bot (GUESS) */
            float hx = bp[0] - fr.T[0], hz = bp[2] - fr.T[2], hl = (float)sqrt(hx * hx + hz * hz);
            if (hl > klmv.reach_aim) { aim[0] = fr.T[0] + hx / hl * klmv.reach_aim; aim[2] = fr.T[2] + hz / hl * klmv.reach_aim; aim[1] = bp[1]; }
        }
        j = kle_order2(&t, aim, got, w, klmv.dry);
        if (!j) { klog("reach: record %d NOT sent to the doors: %s", i, w); continue; }
        b->order_at = KLB_T(now); b->since = now;
        klog("reach: visit %d: record %d (stage %u) stood %.1f m from the boarding box at (%.0f, %.0f, %.0f): %s to the doors (%.0f, %.0f, %.0f), the game set (%.0f, %.0f, %.0f)", klmv_r.visit, i, r->stage, d / 100, bp[0], bp[1], bp[2],
             j == 2 ? "WOULD be sent (dry run)" : "sent", aim[0], aim[1], aim[2], got[0], got[1], got[2]);
    }
}

static void klmv_boxes(const struct klb_snap *s, DWORD now)
{
    float bd[3] = { 0, 0, 0 }, p[3]; BYTE last = 0; int i, j, have_bd, waiting = s->veh == 3 || s->veh == 4, any = 0;
    DWORD mine = (DWORD)(DWORD_PTR)&klmv_vt[1], node;
    /* once a ROUND, not once per rules address: a level loaded again can put its rules object where the last one was,
       and its boxes anywhere (review S6). The cost is the scan's standstill at every round's start: the line says the ms */
    if (!klmv_r.scanned) { klmv_r.scanned = 1; klmv_scan(s->rules); }
    /* the rule is decided WHILE THE VEHICLE STANDS (states 3 / 4: the boarding place is the stop's) and kept as it is
       through state 5, when the boarding object drives off with the vehicle and every box would be 'far' - so a near
       box keeps the stock boarding of state 5's first second (review S8). In states 0 / 1 / 2 nothing is denied: the
       boarding rule 0x6840a0 takes nobody then anyway */
    have_bd = waiting && kle_boarding(s->rules, bd);
    if (have_bd) memcpy(klmv_r.near_bd, bd, 12);
    klh_rd(s->rules + 0xe8a, &last, 1);
    for (i = 0; i < klmv_nbox; i++) {
        LONG deny = 0; DWORD ent; float d;
        if (!klmv_box[i].at) continue;
        if (klmv.dry ? klh_rd32(klmv_box[i].at) != KLMV_ALLY_VT : klh_rd32(klmv_box[i].at) != mine) { klmv_box[i].deny = 0; klmv_box[i].would = 0; klmv_box[i].at = 0; continue; }      /* the object is gone */
        if ((ent = klh_rd32(klmv_box[i].at + 0x24)) != 0 && (node = klh_rd32(ent + 4)) != 0 && kle_node(node, p, 0)) memcpy(klmv_box[i].pos, p, 12);
        if (!waiting && klmv_r.was_waiting && klmv_box[i].asked && klmv.log)
            klog("near: visit %d is over: the denied box at (%.0f, %.0f, %.0f) was asked %ld time(s)", klmv_r.visit, klmv_box[i].pos[0], klmv_box[i].pos[1], klmv_box[i].pos[2], (long)klmv_box[i].asked);
        if (s->veh == 5 && !last) { if (klmv_box[i].would) any = 1; continue; }  /* as decided while it stood */
        d = have_bd ? kle_dist(klmv_box[i].pos, bd) : 0; klmv_box[i].d = d;
        if (klmv.near_ > 0 && have_bd && !last && d > klmv.near_ && (!klmv.near_visits || klmv_r.visit < klmv.near_visits)) deny = 1;
        klmv_box[i].would = (int)deny;
        if (!klmv.dry) klmv_box[i].deny = deny;
        if (deny) any = 1;
        if (klmv.near_ > 0 && waiting && klmv_box[i].told_visit != klmv_r.visit) {
            klmv_box[i].told_visit = klmv_r.visit; klmv_box[i].asked = 0;
            if (deny) klog("near: visit %d: the box at (%.0f, %.0f, %.0f) is %.1f m from the boarding place (%.0f, %.0f, %.0f), over BoardNear %.1f m: it %s", klmv_r.visit, klmv_box[i].pos[0], klmv_box[i].pos[1], klmv_box[i].pos[2],
                           d / 100, bd[0], bd[1], bd[2], klmv.near_ / 100, klmv.dry ? "WOULD take nobody aboard (dry run)" : "takes nobody aboard");
            else if (klmv.log) klog("near: visit %d: the box at (%.0f, %.0f, %.0f) is %.1f m from the boarding place: it works as in stock%s", klmv_r.visit, klmv_box[i].pos[0], klmv_box[i].pos[1], klmv_box[i].pos[2], d / 100,
                                   last ? " (the round's last vehicle: every box works)" : klmv.near_visits && klmv_r.visit >= klmv.near_visits ? " (BoardNearVisits: from this visit on every box works)" : "");
        }
    }
    /* THE COST, COUNTED (review M3): who is still in play as the vehicle drives off. With the human aboard the rules
       shoot every one of them in the next 8.4 s (slot 7 = 0x74b6d0, re\bots_follow_out.md) unless FollowOutSpare is on;
       'at a denied box' = this file kept the box from taking it on this visit */
    if (s->veh == 5 && klmv_r.was_waiting) {
        char list[160]; int k = 0, left = 0, denied = 0, hab = s->human >= 0 && s->r[s->human].status == 4; BYTE spare = 0;
        list[0] = 0;
        for (i = 0; i < s->n && i < KLB_NREC; i++) {
            const struct klb_rec *r = &s->r[i]; struct klmv_b *b = &klmv_r.b[i];
            if (!r->used || !(r->flags & 1) || r->status) continue;
            left++; if (b->told & 16) denied++;
            if (b->seen && k < (int)sizeof list - 40) k += snprintf(list + k, sizeof list - k, " %d%s %.0f m", i, b->told & 16 ? "*" : "", kle_dist(b->pos, klmv_r.near_bd) / 100);
        }
        spare = (BYTE)(kle.fo_spare != 0);
        klog("near: visit %d: the vehicle leaves %s: %d AI heister(s) still in play (record, metres from the boarding place:%s), %d of them (*) stood at a denied box or in a box beyond BoardReach on this visit%s", klmv_r.visit, hab ? "WITH YOU ABOARD" : "without you", left, left ? list : " none",
             denied, !left ? "" : !hab ? " - it comes again for them" : spare ? " - FollowOutSpare is on: nobody is shot" : " - THE RULES SHOOT THEM NOW (stock Arcade: every AI heister left in play when the human is driven out); FollowOutHold / FollowOutSpare are the keys against it");
        for (i = 0; i < KLB_NREC; i++) klmv_r.b[i].told &= (BYTE)~16;
    }
    if (!any || !waiting) return;                                              /* only while it STANDS */
    /* g. a bot under stage 3 at a denied box: the stage byte BoardAll writes, with BoardAll's tests (klmv_stage3) */
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; struct klmv_b *b = &klmv_r.b[i];
        if (!r->used || !(r->flags & 1) || r->status || !b->seen) continue;
        for (j = 0; j < klmv_nbox; j++) if (klmv_box[j].at && klmv_box[j].would && klmv_h(b->pos, klmv_box[j].pos) <= KLMV_BOXR && fabs(b->pos[1] - klmv_box[j].pos[1]) <= 400.0f) break;
        if (j >= klmv_nbox) continue;
        b->told |= 16;                                                         /* for the line at the departure */
        klmv_stage3(s, i, "at a denied box");
    }
    (void)now;
}

/* ---------------------------------------------------------------- WaitForYou */

/* the byte back to 0 if it is still ours: the rules object still is one, its vehicle state 0, the byte 1 */
static void klmv_gate_release(const char *why)
{
    DWORD rules = klmv_gate_rules; BYTE veh = 1, b = 0;
    if (!rules) return;
    klmv_gate_rules = 0;
    if (klh_rd32(rules) != KLB_RULES_VT || !klh_rd(rules + 0x1dc, &veh, 1) || !klh_rd(rules + 0x1ee, &b, 1)) return;
    if (veh == 0 && b == 1) {
        if (klb_put8(rules + 0x1ee, 0, "rules: the exit trigger may call the vehicle again")) klog("wait: released (%s): the exit trigger calls the vehicle again for whoever stands in it", why);
        else klog("wait: released (%s) BUT rules +0x1ee could NOT be written back: no vehicle can be called until the round is reset", why);
    } else if (veh == 1 && b == 1) {         /* a vehicle that is not the last one came all the same: the game never has the byte set in state 1 */
        klb_put8(rules + 0x1ee, 0, "rules: 'the last vehicle was called' taken back (it was this file's, and this vehicle is not the last)");
        klog("wait: released (%s): a vehicle was called all the same (state 1); the byte is taken back", why);
    } else klog("wait: released (%s): vehicle state %u, rules +0x1ee = %u - the game's own from here on, nothing is written", why, veh, b);
}

static void klmv_gate(const struct klb_snap *s, DWORD now, const struct klb_rec *h, int criminal)
{
    static char why[80]; char list[64]; BYTE b = 0; int i, k = 0, ready = 0, hold;
    why[0] = 0; list[0] = 0;
    for (i = 0; i < s->n && i < KLB_NREC; i++)
        if (s->r[i].used && (s->r[i].flags & 3) == 1 && !s->r[i].status && s->r[i].stage >= 3) { ready++; if (k < (int)sizeof list - 6) k += snprintf(list + k, sizeof list - k, "%s%d", k ? " " : "", i); }
    if (!h) strcpy(why, "there is no human in the crew");
    else if (h->status == 4) strcpy(why, "you are aboard");
    else if (h->status) strcpy(why, "you are out of play");
    else if (!criminal) strcpy(why, "you are police");
    else if (h->stage >= klmv.wait_stage && now - klmv_r.round_at >= klmv.wait_floor) snprintf(why, sizeof why, "you have reached heist stage %u", h->stage);
    else if (klmv_r.gate_ready && now - klmv_r.gate_ready >= klmv.wait_max) snprintf(why, sizeof why, "WaitForYouMax: %lu s since the first bot stood ready", klmv.wait_max / 1000);
    hold = !why[0];
    if (hold && ready && !klmv_r.gate_ready) {
        klmv_r.gate_ready = KLB_T(now);
        klog("wait: record(s) %s stand ready at heist stage 3 (the exit trigger) and you are at stage %u: no vehicle is called - they wait for you, %lu s at most", list, h->stage, klmv.wait_max / 1000);
    }
    if (!klh_rd(s->rules + 0x1ee, &b, 1)) return;
    if (!hold) { if (klmv_gate_rules) klmv_gate_release(why); return; }
    if (klmv_gate_rules && klmv_gate_rules != s->rules) klmv_gate_release("another round object");
    if (s->veh != 0) {                        /* a vehicle is called or there (ours was not yet written, or the rules forced the last one) */
        if (klmv_gate_rules) klmv_gate_release("a vehicle was called by the rules themselves");
        return;
    }
    if (b) return;                            /* ours, or the game's own 'last vehicle was called' */
    if (klmv.dry) { if (!klmv_r.gate_told++) klog("wait: no vehicle WOULD be called before you (dry run: rules +0x1ee is left at 0); you are at stage %u, WaitForYouStage=%d", h->stage, klmv.wait_stage); return; }
    if (!klb_put8(s->rules + 0x1ee, 1, "rules: the exit trigger calls no vehicle (the crew waits for the human)")) { if (!klmv_r.gate_told++) klog("wait: rules +0x1ee could NOT be written: the crew may call the vehicle"); return; }
    klmv_gate_rules = s->rules;
    if (!klmv_r.gate_told++) klog("wait: no vehicle is called before you: the exit trigger gives its stage 3 and calls nothing (rules +0x1ee = 1) until you are at heist stage %d%s, or %lu s after the first bot stood ready; you are at stage %u",
                                 klmv.wait_stage, klmv.wait_floor ? " and the round's floor is over" : "", klmv.wait_max / 1000, h->stage);
}

/* e. the driver waits for the human who comes */
static void klmv_driver(const struct klb_snap *s, DWORD now, const struct klb_rec *h, int human_in, int criminal, const float hp[3])
{
    float bd[3], d, timer = klb_finite(s->timer) ? s->timer : -1.0f, tnow = 0, add; BYTE grade = 1, paid = 0, veh2 = 0; const char *no = 0; char gw[200], gn[200];
    gw[0] = gn[0] = 0;
    if (!(klmv.wait_hold > 0) || !(s->veh == 3 || s->veh == 4) || !h || h->status || !human_in || !criminal || !kle_boarding(s->rules, bd)) { klmv_r.h_at = 0; return; }
    if (klmv_r.hold_visit != klmv_r.visit) { klmv_r.hold_visit = klmv_r.visit; klmv_r.hold_used = 0; klmv_r.hold_told = 0; klmv_r.h_at = 0; }
    d = kle_dist(hp, bd);
    if (!klmv_r.h_at) { klmv_r.h_at = KLB_T(now); klmv_r.h_d = d; klmv_r.h_comes = d <= 1500.0f; }
    else if (now - klmv_r.h_at >= 2000) { klmv_r.h_comes = klmv_r.h_d - d >= KLE_COME || d <= 1500.0f; klmv_r.h_d = d; klmv_r.h_at = KLB_T(now); }
    if (!(timer > 0 && timer < KLE_HOLD_AT)) return;
    if (klmv.wait_hold - klmv_r.hold_used < 0.5f) {
        if (!(klmv_r.hold_told & 2)) { klmv_r.hold_told |= 2; klog("wait: hold: the vehicle leaves in %.1f s without you (%.1f m away): the %.1f s of WaitForYouHold are used", timer, d / 100, klmv.wait_hold); }
        return;
    }
    add = klmv.wait_hold - klmv_r.hold_used; if (add > KLE_HOLD_STEP) add = KLE_HOLD_STEP;
    if (!klmv_r.h_comes) no = "you do not come nearer (2 m in 2 s) and are not within 15 m";
    else if (!klh_rd(s->score + 0x60, &grade, 1) || grade) no = "the vehicle is damaged and must go";
    else if (!klh_rd(s->rules + 0x1b3, &paid, 1) || paid != 0xff) no = "somebody paid the driver";
    else if (!klh_rd(s->rules + 0x1dc, &veh2, 1) || (veh2 != 3 && veh2 != 4) || !klh_rd(s->rules + 0x1d8, &tnow, 4) || !klb_finite(tnow) || !(tnow > 0 && tnow < KLE_HOLD_AT)) no = "its timer changed since this pass read it";
    /* klescort.c 3 c2: a vehicle held past stock's 8 s was destroyed with everybody aboard (runs N1 / N1b; here the
       crew sits aboard while the human comes). The same guard as FollowOutHold's: [Bots] FollowOutShield (default 2)
       sets the vehicle's own 'Invulnerable' byte from the first held second, klescort.c takes it back; no shield
       possible = no hold. The last test, and the only one that writes. */
    if (!no && !kle_hold_guard(s, now, klmv.dry, gw, gn)) no = gw;
    if (no || klmv.dry) {
        if (!(klmv_r.hold_told & 1)) {
            klmv_r.hold_told |= 1;
            if (no) klog("wait: hold: the vehicle leaves in %.1f s without you (%.1f m away) and is NOT held: %s", timer, d / 100, no);
            else klog("wait: hold: the vehicle would leave in %.1f s and you are %.1f m from it, coming: its timer WOULD get %.1f s more (dry run); %s", timer, d / 100, add, gn);
        }
        return;
    }
    tnow += add;
    if (!klh_data((void *)(DWORD_PTR)(s->rules + 0x1d8), &tnow, 4, "escape vehicle wait timer (the driver waits for the human)")) { if (!(klmv_r.hold_told & 1)) { klmv_r.hold_told |= 1; klog("wait: hold: the vehicle's timer could NOT be written"); } return; }
    klmv_r.hold_used += add;
    klog("wait: hold: the vehicle would leave in %.1f s and you are %.1f m from it, coming: timer %.1f -> %.1f s (%.1f of %.1f s used this visit); %s", timer, d / 100, tnow - add, tnow, klmv_r.hold_used, klmv.wait_hold, gn);
}

/* e2. CrewRouteHold: the van waits for a crew that WALKS its (long, winding) route to it.
   Vault run N1018_L61: the called bots left the vault 20-60 m (straight line) and ~120 m (route) from the van; the way
   leads away from the van first, so klescort.c's 'comes nearer by 2 m in 2 s' (FollowOutHold) was false for all of
   them, 'NOT held: none comes nearer', and the van left after its 8 s with nobody aboard but you.
   Here a called loyal bot that MOVES 2 m (3D) over a 2 s sample counts, whichever way, if it is within CrewRouteRange
   of the boarding place. GUESS: a moving bot within that range is on its way (a fighting bot moves too).
   Same refusals and the same guard as klmv_driver / FollowOutHold; its own budget (CrewRouteHold s a visit), so the
   worst case with FollowOutHold is the sum of both. You must be aboard (the van is then yours to hold). */
static void klmv_crewhold(const struct klb_snap *s, DWORD now, const struct klb_rec *h, int criminal)
{
    float bd[3], p[3], timer = klb_finite(s->timer) ? s->timer : -1.0f, tnow = 0, add, dnear = -1; BYTE grade = 1, paid = 0, veh2 = 0; const char *no = 0; char gw[200], gn[200];
    int i, nwalk = 0, nplay = 0, napp = 0; float budget;
    gw[0] = gn[0] = 0;
    if (!(s->veh == 3 || s->veh == 4) || !h || !(h->status == 4 || (klmv.crew_alone && h->status == 0)) || !criminal || !kle_boarding(s->rules, bd)) { memset(klmv_r.cr_at, 0, sizeof klmv_r.cr_at); return; }
    if (klmv_r.cr_visit != klmv_r.visit) { klmv_r.cr_visit = klmv_r.visit; klmv_r.cr_used = 0; klmv_r.cr_told = 0; klmv_r.cr_extra = 0; klmv_r.cr_xdone = 0; memset(klmv_r.cr_at, 0, sizeof klmv_r.cr_at); }
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; float d;
        if (!r->used || (r->flags & 3) != 1 || r->status) { klmv_r.cr_at[i] = 0; continue; }
        if (!r->actor || klh_rd32(r->actor) != KLB_ACTOR_VT || !kle_node(klh_rd32(r->actor + 4), p, 0)) { klmv_r.cr_at[i] = 0; continue; }
        nplay++;
        d = kle_dist(p, bd);
        if (!klmv_r.cr_at[i]) { klmv_r.cr_at[i] = KLB_T(now); memcpy(klmv_r.cr_p[i], p, 12); klmv_r.cr_walk[i] = 0; klmv_r.cr_dat[i] = 0; klmv_r.cr_shr[i] = 0; }
        else if (now - klmv_r.cr_at[i] >= 2000) { klmv_r.cr_walk[i] = kle_dist(klmv_r.cr_p[i], p) >= KLE_COME; klmv_r.cr_at[i] = KLB_T(now); memcpy(klmv_r.cr_p[i], p, 12); }
        if (klmv.crew_hop > 0) {      /* CrewRouteHopHold (GUESS limits): 1 m nearer in 5 s counts as closing in; klhop.c's hop state is private there, so a bot carried over a hop (it stands 10 s at From) counts for 15 s after it last closed in */
            if (!klmv_r.cr_dat[i]) { klmv_r.cr_dat[i] = KLB_T(now); klmv_r.cr_dd[i] = d; }
            else if (now - klmv_r.cr_dat[i] >= 5000) { if (klmv_r.cr_dd[i] - d >= 100.0f) klmv_r.cr_shr[i] = KLB_T(now); klmv_r.cr_dat[i] = KLB_T(now); klmv_r.cr_dd[i] = d; }
            if (r->stage >= 3 && klmv_r.cr_shr[i] && now - klmv_r.cr_shr[i] <= 15000 && d <= klmv.crew_range * 100.0f) napp++;
        }
        if (klmv_r.cr_walk[i] && d <= klmv.crew_range * 100.0f) { nwalk++; if (dnear < 0 || d < dnear) dnear = d; }
    }
    if (!(timer > 0 && timer < KLE_HOLD_AT)) return;
    budget = klmv.crew_hold + klmv_r.cr_extra;
    if (budget - klmv_r.cr_used < 0.5f && klmv.crew_hop > 0 && !klmv_r.cr_xdone && napp && !klmv.dry) {      /* CrewRouteHopHold: once a visit */
        klmv_r.cr_xdone = 1; klmv_r.cr_extra = klmv.crew_hop; budget += klmv.crew_hop;
        klog("crewhold: the vehicle leaves in %.1f s and the %.1f s of CrewRouteHold are used, but %d stage-3 bot(s) closed in on the boarding place within the last 15 s (mid-hop or walking): CrewRouteHopHold adds up to %.1f s, once this visit", timer, klmv.crew_hold, napp, klmv.crew_hop);
    }
    if (budget - klmv_r.cr_used < 0.5f) {
        if (!(klmv_r.cr_told & 2)) { klmv_r.cr_told |= 2; klog("crewhold: the vehicle leaves in %.1f s: the %.1f s of CrewRouteHold are used", timer, budget); }
        return;
    }
    add = budget - klmv_r.cr_used; if (add > KLE_HOLD_STEP) add = KLE_HOLD_STEP;
    if (!nwalk) no = nplay ? "no called crew in play walks within CrewRouteRange of the boarding place (2 m in 2 s)" : "nobody of the crew is left in play";
    else if (!klh_rd(s->score + 0x60, &grade, 1) || grade) no = "the vehicle is damaged and must go";
    else if (!klh_rd(s->rules + 0x1b3, &paid, 1) || paid != 0xff) no = "somebody paid the driver";
    else if (!klh_rd(s->rules + 0x1dc, &veh2, 1) || (veh2 != 3 && veh2 != 4) || !klh_rd(s->rules + 0x1d8, &tnow, 4) || !klb_finite(tnow) || !(tnow > 0 && tnow < KLE_HOLD_AT)) no = "its timer changed since this pass read it";
    if (!no && !kle_hold_guard(s, now, klmv.dry, gw, gn)) no = gw;      /* the last test, and the only one that writes */
    if (no || klmv.dry) {
        if (!(klmv_r.cr_told & 1)) {
            klmv_r.cr_told |= 1;
            if (no) klog("crewhold: the vehicle leaves in %.1f s with you %s and is NOT held: %s (%d in play)", timer, h->status == 4 ? "aboard" : "in play (CrewRouteAlone)", no, nplay);
            else klog("crewhold: the vehicle would leave in %.1f s and %d of the crew walk, the nearest %.1f m out: its timer WOULD get %.1f s more (dry run); %s", timer, nwalk, dnear / 100, add, gn);
        }
        return;
    }
    tnow += add;
    if (!klh_data((void *)(DWORD_PTR)(s->rules + 0x1d8), &tnow, 4, "escape vehicle wait timer (the driver waits for the walking crew)")) { if (!(klmv_r.cr_told & 1)) { klmv_r.cr_told |= 1; klog("crewhold: the vehicle's timer could NOT be written"); } return; }
    klmv_r.cr_used += add;
    klog("crewhold: the vehicle would leave in %.1f s and %d of the crew walk (the nearest %.1f m out): timer %.1f -> %.1f s (%.1f of %.1f s used this visit); %s", timer, nwalk, dnear / 100, tnow - add, tnow, klmv_r.cr_used, budget, gn);
}

/* ---------------------------------------------------------------- Restless */

/* where every AI heister in play stands, what it has, its health; since when neither place nor money changed */
static void klmv_track(const struct klb_snap *s, DWORD now)
{
    int i; DWORD node, ho; float p[3], raw[0x28 / 4];
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; struct klmv_b *b = &klmv_r.b[i];
        if (r->used && r->actor != b->actor) { memset(b, 0, sizeof *b); b->actor = r->actor; if (i < KLB_NREC) klmv_fo_on[i] = 0; }      /* another member in this record */
        if (!r->used || !(r->flags & 1) || r->status || !r->actor || klh_rd32(r->actor) != KLB_ACTOR_VT
            || !(node = klh_rd32(r->actor + 4)) || !kle_node(node, p, 0)) { b->seen = 0; continue; }
        if (!b->seen || kle_dist(p, b->pos) > 100.0f || r->money != b->money) {
            memcpy(b->pos, p, 12); b->money = r->money; b->since = now; b->seen = 1; b->look_obj = 0;
        }
        if ((ho = klh_rd32(r->actor + 0x5fc)) != 0 && klh_rd(ho, raw, sizeof raw) && ((DWORD *)raw)[0x24 / 4] == r->actor && klb_finite(raw[1])) {      /* klbot.c's health log */
            if (b->hp > 0 && raw[1] < b->hp - 0.05f) b->hit_at = KLB_T(now);
            b->hp = raw[1];
        }
    }
}

/* the level's [Hops] (kljoin.c has found and stamped its KLJoin.ini; never a stock archive's). Cheap: a compare of the key,
   the path and the file time under kljoin.c's lock, the file is read again only when one of them changed. */
static void klmv_hops_load(void)
{
    char key[64], file[MAX_PATH], t[32], name[48], scene[160], cur[64]; FILETIME ft; int g, j, ng, nh;
    EnterCriticalSection(&klj_cs);
    snprintf(key, sizeof key, "%s", klj_map_key); snprintf(file, sizeof file, "%s", klj_map_file); ft = klj_map_ft;
    LeaveCriticalSection(&klj_cs);
    /* kljoin.c keeps the last level's file until a level with one opens (it drops it only when the SAME key opens
       without one): on another level - a stock one under [KLHook] AllMaps=1, or an expansion map without a KLJoin.ini -
       those hop places are not this level's. klhop / klclimb / klrappel / klfedkit compare the key themselves. */
    if (key[0] && (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, cur, sizeof cur) || strcmp(cur, key))) { key[0] = 0; file[0] = 0; memset(&ft, 0, sizeof ft); }
    if (!strcmp(key, klmv_hop_key) && !_stricmp(file, klmv_hop_file) && !CompareFileTime(&ft, &klmv_hop_ft)) return;
    klmv_nhop = 0; klmv_nhold = 0; memset(klmv_hop_at, 0, sizeof klmv_hop_at); memset(klmv_hop_user, 0, sizeof klmv_hop_user); snprintf(klmv_hop_key, sizeof klmv_hop_key, "%s", key); snprintf(klmv_hop_file, sizeof klmv_hop_file, "%s", file); klmv_hop_ft = ft;
    klmv_hop_dmax = 1800.0f;
    if (!key[0] || !file[0]) return;
    ng = (int)GetPrivateProfileIntA("Hops", "Gates", 0, file);
    if (ng <= 0) return;
    GetPrivateProfileStringA("Hops", "Max", "1800", t, sizeof t, file);
    klmv_hop_dmax = (float)atof(t); if (!klb_finite(klmv_hop_dmax) || klmv_hop_dmax < 300) klmv_hop_dmax = 300; if (klmv_hop_dmax > 4000) klmv_hop_dmax = 4000;
    for (g = 1; g <= ng && g <= 24; g++) {
        snprintf(name, sizeof name, "Gate.%d.Holds", g); nh = (int)GetPrivateProfileIntA("Hops", name, 0, file);
        for (j = 1; j <= nh && klmv_nhold < KLMV_NHOLD; j++) {
            snprintf(name, sizeof name, "Gate.%d.Hold.%d", g, j);
            if (klj_vec("Hops", name, file, klmv_holds[klmv_nhold])) {
                snprintf(name, sizeof name, "Gate.%d.HoldS.%d", g, j); GetPrivateProfileStringA("Hops", name, "", t, sizeof t, file); klmv_hold_s[klmv_nhold] = t[0] ? (float)atof(t) : -1.0f;
                klmv_hold_g[klmv_nhold++] = g;
            }
        }
        snprintf(name, sizeof name, "Gate.%d.Hops", g); nh = (int)GetPrivateProfileIntA("Hops", name, 0, file);
        for (j = 1; j <= nh && klmv_nhop < KLMV_NHOP; j++) {
            snprintf(name, sizeof name, "Gate.%d.Hop.%d", g, j);
            if (klj_vec("Hops", name, file, klmv_hops[klmv_nhop])) {
                snprintf(name, sizeof name, "Gate.%d.HopS.%d", g, j); GetPrivateProfileStringA("Hops", name, "", t, sizeof t, file); klmv_hop_s[klmv_nhop] = t[0] ? (float)atof(t) : -1.0f;
                klmv_hop_g[klmv_nhop++] = g;
            }
        }
    }
    klog("move: %d hop place(s) at %d hold(s) of %d gate(s) (cover places a bot may shift to while it waits at a hold of the same gate; at most %.0f from the hold) from %s for level %s", klmv_nhop, klmv_nhold, ng, klmv_hop_dmax, file, key);
}

/* The gate a bot's chain place belongs to: the gate of the nearest listed hold (or hop) within 150 on its floor (300); 0 = none. */
static int klmv_hop_gate(const float anchor[3], float *prog)
{
    int j, g = 0; float best = 150.0f;
    *prog = -1.0f;
    for (j = 0; j < klmv_nhold; j++) {
        float d = klmv_h(anchor, klmv_holds[j]);
        if (d <= best && fabs(anchor[1] - klmv_holds[j][1]) <= 300.0f) { best = d; g = klmv_hold_g[j]; *prog = klmv_hold_s[j]; }
    }
    for (j = 0; j < klmv_nhop; j++) {                                  /* a place this file sent it to (a hop) counts for its gate too */
        float d = klmv_h(anchor, klmv_hops[j]);
        if (d <= best && fabs(anchor[1] - klmv_hops[j][1]) <= 300.0f) { best = d; g = klmv_hop_g[j]; *prog = klmv_hop_s[j]; }
    }
    return g;
}

/* A hop for a bot that waits at `anchor` (its chain's place) and stands at `bp`: a place of its gate's list that is within the
   list's Max of the anchor and on its floor (300), at least KLMV_OFF (3 m) from where the bot stands, and not `last` (index + 1 of
   the one it hopped to the time before). away != 0: the one FARTHEST from that point (the shooter: cover from him); else one drawn
   by klb_seed. -> the index, -1 = none; out = its place. */
static int klmv_hop_free(int j, int who, DWORD now) { return !klmv_hop_user[j] || klmv_hop_user[j] - 1 == who || (LONG)(now - klmv_hop_at[j]) >= KLMV_HOP_KEEP; }      /* user = who + 1, 0 = nobody */
static void klmv_hop_take(int j, int who) { if (j >= 0 && j < klmv_nhop) { klmv_hop_at[j] = GetTickCount(); klmv_hop_user[j] = who + 1; } }
static int klmv_hop_pick(const float anchor[3], const float bp[3], int last, int who, const float *away, float out[3])
{
    int j, k = -1, n = 0, pick, g; float best = -1.0f, ps; DWORD now = GetTickCount();
    g = klmv_hop_gate(anchor, &ps);
    if (!g) return -1;
    for (j = 0; j < klmv_nhop; j++) {
        if (klmv_hop_g[j] != g || j + 1 == last || !klmv_hop_free(j, who, now) || (ps >= 0 && klmv_hop_s[j] >= 0 && klmv_hop_s[j] < ps - KLMV_PROG_SLACK) || klmv_h(anchor, klmv_hops[j]) > klmv_hop_dmax || fabs(anchor[1] - klmv_hops[j][1]) > 300.0f || klmv_h(bp, klmv_hops[j]) < KLMV_OFF) continue;
        if (away) { float d = klmv_h(away, klmv_hops[j]); if (d > best) { best = d; k = j; } }
        n++;
    }
    if (away || n == 0) { if (k >= 0) memcpy(out, klmv_hops[k], 12); return k; }
    klb_seed = klb_seed * 1103515245u + 12345u;
    pick = (int)((klb_seed >> 16) % (unsigned)n);
    for (j = 0; j < klmv_nhop; j++) {
        if (klmv_hop_g[j] != g || j + 1 == last || !klmv_hop_free(j, who, now) || (ps >= 0 && klmv_hop_s[j] >= 0 && klmv_hop_s[j] < ps - KLMV_PROG_SLACK) || klmv_h(anchor, klmv_hops[j]) > klmv_hop_dmax || fabs(anchor[1] - klmv_hops[j][1]) > 300.0f || klmv_h(bp, klmv_hops[j]) < KLMV_OFF) continue;
        if (pick-- == 0) { memcpy(out, klmv_hops[j], 12); return j; }
    }
    return -1;
}

static void klmv_restless(const struct klb_snap *s, DWORD now, int human_in, const float hp[3])
{
    int i, j, k, fire, there, hopk; DWORD actor, soldier, stood; float bp[3], cur[3], want[3], got[3], d; char w[100]; struct kle_e t; BYTE grab;
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; struct klmv_b *b = &klmv_r.b[i];
        grab = 1;
        if (!r->used || !(r->flags & 1) || (r->flags & 2) || r->status || !b->seen || kle_r.used[i]) continue;      /* not a traitor, never this round's escort */
        if (klmv.skip_down) {
            /* RestlessSkipDowned: the down byte klbotdown.c reads (actor + 0x64c, nonzero = downed; same read as klbd_is_down, which is
               static and only answers while [Bots] BotDown is on, so it is read here directly). A dead bot has r->status set and was skipped above.
               since = now: the stand-still clock starts again when the bot is up (GUESS: a bot that was down must not be 'restless' the instant it gets up). */
            BYTE dn = 0;
            if (r->actor && klh_rd(r->actor + 0x64c, &dn, 1) && dn) { b->since = now; continue; }
        }
        /* the place its chain ordered: whatever the defend block holds that this file did not put there. A place within
           KLE_ROUTE of ours is one of the soldier's own tactics moving it (klescort.c 2, the same GUESS): the centre stays */
        if ((soldier = klh_rd32(r->actor + 0x77c)) != 0 && klh_rd32(soldier) == KLE_SOLDIER_VT && kle_block(soldier, cur) && (cur[0] || cur[1] || cur[2])) {
            if (i < KLB_NREC && klmv_fo_on[i] && kle_dist(cur, klmv_fo[i]) <= 50.0f && !(b->have_target && kle_dist(cur, b->target) <= 50.0f)) {
                /* v82f: a place klfedkit.c ordered, not the chain's: the anchor and its counts stay (the bot is walked back to its chain's place, not kept on the hunt step) */
                b->have_target = 0; b->paced = 0; b->beside = 0;
                if (!(b->told & 64) && b->have_anchor) { b->told |= 64; klog("move: record %d: the block holds (%.0f, %.0f, %.0f), a place klfedkit.c ordered: not taken as its chain's place; its chain's place (%.0f, %.0f, %.0f) stays (v82f; said once per bot)", i, cur[0], cur[1], cur[2], b->anchor[0], b->anchor[1], b->anchor[2]); }
            } else if (b->have_target && kle_dist(cur, b->target) <= KLE_ROUTE) {
                /* still what this file put there (review S2): the chain's place stays the anchor and no count starts again.
                   Only a plain order-again (to the anchor itself) that is long done hands the block back - the game may
                   have set the place a little off what was asked (FO_J1: asked y 278, set y 150) - and that without a new count */
                memcpy(b->target, cur, 12);
                if (!b->paced && !b->beside && now - b->order_at > 10000) { memcpy(b->anchor, cur, 12); b->have_target = 0; }
            } else {
                if (!b->have_anchor || kle_dist(cur, b->anchor) > 5.0f) {
                    if (!b->have_anchor || kle_dist(cur, b->anchor0) > KLE_ROUTE) { memcpy(b->anchor0, cur, 12); b->total = 0; b->told &= (BYTE)~1; }      /* a new place of its chain: the counts start again */
                    memcpy(b->anchor, cur, 12); b->have_anchor = 1; b->tries = 0; b->told &= (BYTE)~2;
                }
                b->have_target = 0; b->paced = 0; b->beside = 0;
            }
        }
        if (r->stage >= 3 && s->veh >= 1 && s->veh <= 5) continue;             /* a vehicle is called or there: the board tactic and the rules' order own a stage-3 bot */
        stood = now - b->since;
        fire = b->hit_at && now - b->hit_at < 4000;                            /* it lost health in the last 4 s: it fights, nothing of this file moves it or judges it (review S1, S3) */
        /* a. the loot square. Only a bot whose loot tactic is ON (heist stage 1 or more: 0x4519d4), that is not under
           fire and has no grab running (crew record +0x15: 1 / 2 while 0x8e8750 .. 0x727cb0 work on an object). Such
           a bot within 2 m of a candidate WOULD be taking it - the tactic's test is 1.0 while a candidate has a path
           and it ranks over the route chain's orders (re/bots_squad.md 4) - so standing there unpaid is the trap, not
           a cover hold doing its job (review S3; a bot at stage 0 or under fire is not judged) */
        if (klmv.loot && stood >= 1000 && r->stage >= 1 && !fire && klh_rd(r->at + 0x15, &grab, 1) && !grab) {
            int o = -1; float best = klmv.loot_near;
            for (j = 0; j < klmv_nobj; j++) {
                d = klmv_h(b->pos, klmv_obj[j].pos);
                if (klmv_obj[j].amount > 0 && d <= best && fabs(b->pos[1] - klmv_obj[j].pos[1]) <= 250.0f) { best = d; o = j; }
            }
            if (o < 0) b->look_obj = 0;
            else if (b->look_obj != klmv_obj[o].obj || klmv_obj[o].amount < b->look_amount) { b->look_obj = klmv_obj[o].obj; b->look_amount = klmv_obj[o].amount; b->look_at = KLB_T(now); }      /* a new one; or somebody is taking it */
            else if (now - b->look_at >= klmv.loot && stood >= klmv.loot) {
                DWORD secs = 0; int times = 0;
                if (klmv_make_sour(s->rules, o, now, &secs, &times)) {
                    klog("move: record %d (stage %u, $%lu) stood %.1f s at (%.0f, %.0f, %.0f) %.1f m from money object %08lx ($%d left, active %u, state %u) and nothing was paid: FED UP - the object %s no loot candidate for %lu s (time %d); you can still take it",
                         i, r->stage, r->money, stood / 1000.0, b->pos[0], b->pos[1], b->pos[2], best / 100, klmv_obj[o].obj, klmv_obj[o].amount, klmv_obj[o].active, klmv_obj[o].state, klmv.dry ? "WOULD be (dry run)" : "is", secs, times);
                    klmv_obj[o].amount = 0;                                     /* not a candidate for the next bot of this pass */
                    b->since = now; b->look_obj = 0;
                    continue;
                }
            }
        }
        if (!klmv.restless || stood < klmv.restless || !b->have_anchor) continue;
        if (klv_owned(i)) { if (kltr.on) kltr_line(i, "move-restless", "SKIP", b->pos, 0, 0, "WalkExclusive: klhop.c walks this bot"); continue; }      /* v82i GUESS, [Bots] WalkExclusive (default 0): the walk of a hop is the bot's order now */
        if (b->order_at && now - b->order_at < (klmv.restless < 4000 ? 4000 : klmv.restless)) continue;
        if (fire) continue;                                                    /* b and c alike: a bot that fights from where it stands is not pulled out (review S1) */
        d = klmv_h(b->pos, b->anchor);
        /* where this file sent it (a shift round its hold, or beside the human) is its place too, while the block still holds that */
        there = b->have_target && (b->paced || b->beside) && klmv_h(b->pos, b->target) <= KLMV_OFF && fabs(b->pos[1] - b->target[1]) <= 300.0f;
        if (!there && (d > KLMV_OFF || fabs(b->pos[1] - b->anchor[1]) > 300.0f) && klmv.after && now - klmv_r.round_at < klmv.after) continue;      /* RestlessAfter: an off-place bot is left alone in the first seconds of a round (neither b. nor a hop round a stale hold) */
        if (!there && (d > KLMV_OFF || fabs(b->pos[1] - b->anchor[1]) > 300.0f)) {
            /* b. stuck off its place */
            int beside = 0;
            if (b->tries && kle_dist(b->pos, b->try_pos) > 200.0f) b->tries = 0;      /* another spot */
            if (b->tries >= 4 || b->total >= KLMV_TOTAL) {
                if (!(b->told & 1)) { b->told |= 1; klog("move: record %d still stands at (%.0f, %.0f, %.0f), %.1f m from its place, after %d order(s) on this spot and %d for this place of its chain: it is left until its chain orders another place", i, b->pos[0], b->pos[1], b->pos[2], d / 100, b->tries, b->total); }
                /* RestlessSnap (default off): the chain's orders did not bring it (audit 1018, record 7 stood 70..160 s wedged at a
                   mesh corner 3 cm off the mesh, 24 m from its place). It is put AT its place with the game's own actor teleport
                   (klt_teleport, the call klcrew_rt.c's jump uses), not past a human who could see it: only when the place is on its floor (300),
                   within RestlessSnapRange, the human is not within RestlessSnapHuman of the bot or the place, nobody holds it as a shield
                   and klt_refuse() lets it through. At most RestlessSnapMax times per bot and round. GUESS: the three limits' defaults. */
                if (klmv.snap && !klmv.dry && b->snaps < klmv.snap_cap && klt_tele_known() && fabs(b->pos[1] - b->anchor[1]) <= 300.0f && klmv_h(b->pos, b->anchor) <= (float)klmv.snap_range) {
                    int seen_by = human_in && (klmv_h(hp, b->pos) <= (float)klmv.snap_human || klmv_h(hp, b->anchor) <= (float)klmv.snap_human) && fabs(hp[1] - b->pos[1]) <= 600.0f;
                    const char *why = 0;
                    if (seen_by) why = "the human is near";
                    else if (!kle_bot(s, i, &actor, &soldier, bp, w)) why = w;
                    else if (klh_rd32(actor + 0x770)) why = "it is held as a human shield";
                    else why = klt_refuse(actor);
                    if (why) { if (!(b->told & 4)) { b->told |= 4; klog("move: record %d NOT snapped to its place: %s (said once per bot)", i, why); } }
                    else {
                        float to[3]; memcpy(to, b->anchor, 12);
                        kltr_tp(i, "move-restless-snap", to, "RestlessSnap: stuck off its chain place after the orders of this place were used up");
                        klt_teleport(actor, to);
                        b->snaps++; b->tries = 0; b->total = 0; b->same_n = 0; b->since = now; b->have_target = 0; b->told &= (BYTE)~(1 | 4 | 128);
                        klog("move: record %d SNAPPED from (%.0f, %.0f, %.0f) to its chain's place (%.0f, %.0f, %.0f), %.1f m, time %d of %d (RestlessSnap)", i, bp[0], bp[1], bp[2], to[0], to[1], to[2], d / 100, b->snaps, klmv.snap_cap);
                    }
                }
                continue;
            }
            if (!kle_bot(s, i, &actor, &soldier, bp, w)) { if (!(b->told & 2)) { b->told |= 2; klog("move: record %d stands at (%.0f, %.0f, %.0f) but gets no order: %s", i, b->pos[0], b->pos[1], b->pos[2], w); } continue; }
            memcpy(want, b->anchor, 12);
            /* beside the human only on HIS floor (2026-10-15, run v69_T1D on Retomoto: bots at the lift (y 19600) and in the lobby (y 560)
               were sent up to a human still on the balcony (y 21020) and walked the tower back; the owner: 'they walk back to the balcony').
               And only when he is within 25 m (run v70_T1E: bots in the top-floor offices were sent 45 m back to him on the balcony) */
            if (b->tries >= 2 && human_in && kle_dist(bp, hp) > 800.0f && kle_dist(bp, hp) <= 2500.0f && fabs(hp[1] - bp[1]) <= 300.0f) { kle_place(hp, bp, 1, 0, want); beside = 1; }
            if (kle_dist(bp, want) <= 260.0f) continue;                        /* the game would take it as 'he is there already' (soft): a waiting step of the chain would end */
            memset(&t, 0, sizeof t); t.rec = i; t.actor = actor; t.soldier = soldier; t.told_soft = 1;
            kltr_set("move-restless", beside ? "b: stuck off its chain place, sent beside the human" : "b: stuck off its chain place, order again", -1);
            k = kle_order2(&t, want, got, w, klmv.dry);
            b->order_at = KLB_T(now); memcpy(b->try_pos, b->pos, 12);
            if (!k) { if (!(b->told & 2)) { b->told |= 2; klog("move: record %d NOT ordered: %s", i, w); } continue; }
            b->tries++; b->total++; b->since = now;
            /* v82f: the same target again and the bot no nearer: after KLMV_SAME such orders the target is dropped (b->total is used up: the branch above leaves the bot to its
               chain and the game until the chain orders another place). It is the way out of any order the bot cannot walk (a point behind a wall, another floor) */
            if (b->same_n && kle_dist(got, b->same_t) <= 50.0f && b->same_d - klmv_h(bp, got) < KLMV_PROGRESS) b->same_n++; else b->same_n = 1;
            memcpy(b->same_t, got, 12); b->same_d = klmv_h(bp, got);
            if (b->same_n >= KLMV_SAME) {
                b->total = KLMV_TOTAL;
                if (!(b->told & 128)) { b->told |= 128; klog("move: record %d: %d orders in a row to (%.0f, %.0f, %.0f) and none brought it 2 m nearer (now %.1f m away): the target is DROPPED, it goes on with its chain's next place (v82f; said once per bot)", i, b->same_n, got[0], got[1], got[2], b->same_d / 100); }
            }
            if (k == 1) { memcpy(b->target, got, 12); b->have_target = 1; b->paced = 0; b->beside = beside; }
            klog("move: record %d (stage %u) stood %.1f s at (%.0f, %.0f, %.0f), %.1f m from its place (%.0f, %.0f, %.0f): %s; the game set (%.0f, %.0f, %.0f); time %d on this spot, %d of %d for this place",
                 i, r->stage, stood / 1000.0, bp[0], bp[1], bp[2], d / 100, b->anchor[0], b->anchor[1], b->anchor[2],
                 beside ? (k == 2 ? "WOULD be sent beside you (dry run)" : "sent beside you") : (k == 2 ? "its order WOULD be given again (dry run)" : "its order is given again"), got[0], got[1], got[2], b->tries, b->total, KLMV_TOTAL);
            continue;
        }
        /* c. at its own place: a meant wait. Only RestlessHold moves it, and only round that place */
        if (b->beside) continue;                                               /* sent beside the human: it stays there until its chain orders another place */
        hopk = -1;
        if (klmv.hop && klmv_nhop && stood >= klmv.hop && !(s->veh >= 1 && s->veh <= 5)) {      /* RestlessHop: cover to cover (section 5) */
            for (j = 0; j < klmv_nbox; j++) if (klmv_box[j].at && klmv_h(b->anchor, klmv_box[j].pos) <= KLMV_BOXR) break;
            if (j >= klmv_nbox && kle_bot(s, i, &actor, &soldier, bp, w)) hopk = klmv_hop_pick(b->anchor, bp, b->hop_k, i, 0, want);
        }
        if (hopk < 0) {
            if (!klmv.hold) { if (klmv.log >= 2 && !(b->told & 8)) { b->told |= 8; klog("move: record %d holds its place (%.0f, %.0f, %.0f) for %.0f s: a meant wait, left alone (RestlessHold=0%s; said once per bot)", i, b->anchor[0], b->anchor[1], b->anchor[2], stood / 1000.0, klmv.hop ? ", no hop place near" : ""); } continue; }
            if (stood < klmv.hold || (s->veh >= 1 && s->veh <= 5)) continue;
            for (j = 0; j < klmv_nbox; j++) if (klmv_box[j].at && klmv_h(b->anchor, klmv_box[j].pos) <= KLMV_BOXR) break;
            if (j < klmv_nbox) continue;                                            /* its place is in an escape box: a step out of it and the box would not take it */
            if (!kle_bot(s, i, &actor, &soldier, bp, w)) continue;
            klb_seed = klb_seed * 1103515245u + 12345u;
            for (j = 0, k = -1; j < 4 && k < 0; j++) {                              /* a side that is 3 m or more from where he stands (never 'soft') */
                float ang = (float)(((klb_seed >> 16) % 360u) + 90u * (unsigned)(j + b->phase)) * 0.0174533f;
                want[0] = b->anchor[0] + klmv.pace * (float)cos(ang); want[1] = b->anchor[1]; want[2] = b->anchor[2] + klmv.pace * (float)sin(ang);
                if (klmv_h(bp, want) >= KLMV_OFF) k = j;
            }
            if (k < 0) continue;
            b->phase += 2;
        }
        memset(&t, 0, sizeof t); t.rec = i; t.actor = actor; t.soldier = soldier; t.told_soft = 1;
        kltr_set("move-restless", hopk >= 0 ? "c: RestlessHop, cover to cover" : "c: RestlessHold, shift round the hold", -1);
        k = kle_order2(&t, want, got, w, klmv.dry);
        b->order_at = KLB_T(now); b->since = now;
        if (!k) continue;
        if (hopk >= 0) { b->hop_k = hopk + 1; klmv_hop_take(hopk, i); }
        if (k == 1) { memcpy(b->target, got, 12); b->have_target = 1; b->paced = 1; b->beside = 0; }
        if (klmv.log) klog("move: record %d %s its hold (%.0f, %.0f, %.0f) after %.1f s: to (%.0f, %.0f, %.0f), the game set (%.0f, %.0f, %.0f)%s", i,
                          hopk >= 0 ? (k == 2 ? "WOULD hop (dry run) from" : "hops from") : (k == 2 ? "WOULD shift (dry run) round" : "shifts round"),
                          b->anchor[0], b->anchor[1], b->anchor[2], stood / 1000.0, want[0], want[1], want[2], got[0], got[1], got[2], hopk >= 0 ? " - a cover place of the level's [Hops]" : "");
    }
}

/* ---------------------------------------------------------------- StairGather */

/* [Bots] StairGather=1 (default 0 = nothing here runs). Hasta (F04 / DM11B) census: the crew lives or dies by how many healthy bots reach the stair
   foot TOGETHER; the lead bot runs ahead alone. Twice a second: a loyal, alive, not-downed AI heister (not an escort) that stands within
   StairGatherRadius of StairGatherAt and whose chain's goal lies more than 200 below it (it wants to go DOWN) is ordered to the gather point (the
   same kle_order2 the Restless code uses) and re-ordered when the game's chain puts its own goal back (at most once a second per bot). Released -
   all together, once per round - when StairGatherN loyal AI heisters in play stand within the radius, or StairGatherTimeout s after the first one
   was held (or a vehicle is called). At the release each held bot gets ONE order back to the chain goal it was held from (GUESS: the chain would
   otherwise take a while to re-order it). Our orders are announced to the Restless code with klmv_foreign() so it does not take the gather
   point for the chain's place. LeashLead (a bot far ahead of the median crew position) is NOT built: 'ahead along the descent' needs a route
   axis this file does not have, and a hold place for a bot that is already ahead is not defined (GUESS: not simple). MoveDry=1: logs, orders nothing. */
static int klmv_downed(const struct klb_rec *r) { BYTE dn = 0; return r->actor && klh_rd(r->actor + 0x64c, &dn, 1) && dn; }

static void klmv_g_release(const struct klb_snap *s, const char *why, int near_n, DWORD now)
{
    int i, k, n = 0, len = 0; char list[200], w[100]; float cur[3], got[3], bp[3]; DWORD actor, soldier; struct kle_e t;
    list[0] = 0;
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        struct klmv_b *b = &klmv_r.b[i];
        if (!b->g_held) continue;
        b->g_held = 0; n++;
        if (len < (int)sizeof list - 12) len += snprintf(list + len, sizeof list - len, " %d(%dx)", i, b->g_n);
        if (klmv.dry || !kle_bot(s, i, &actor, &soldier, bp, w) || !kle_block(soldier, cur)) continue;
        if (kle_dist(cur, b->g_ord) > 50.0f) continue;                         /* the game already put its own goal back: leave that */
        memset(&t, 0, sizeof t); t.rec = i; t.actor = actor; t.soldier = soldier; t.told_soft = 1;
        kltr_set("gather", "StairGather release: back to the chain's goal", -1);
        if ((k = kle_order2(&t, b->g_chain, got, w, 0)) == 1) klmv_foreign(i, got);
    }
    klmv_r.g_done = 1; klmv_r.g_first = 0;
    klog("gather: RELEASE (%s): %d bot(s) released:%s; %d loyal bot(s) within %.0f m of (%.0f, %.0f, %.0f), %.1f s after the round's start; no gathering again this round",
         why, n, list, near_n, klmv.gather_radius / 100.0, klmv.gather_at[0], klmv.gather_at[1], klmv.gather_at[2], (now - klmv_r.round_at) / 1000.0);
}

static void klmv_gather(const struct klb_snap *s, DWORD now)
{
    int i, k, near_n = 0, held_n = 0; float cur[3], got[3], bp[3]; DWORD actor, soldier; char w[100]; struct kle_e t; char ok[KLB_NREC];
    if (!klmv.gather || klmv_r.g_done || now - klmv_r.g_at < 500) return;
    klmv_r.g_at = KLB_T(now);
    for (i = 0; i < s->n && i < KLB_NREC; i++) {                               /* who counts: a loyal AI heister in play, up, not an escort */
        const struct klb_rec *r = &s->r[i]; struct klmv_b *b = &klmv_r.b[i];
        ok[i] = 0;
        if (!r->used || !(r->flags & 1) || (r->flags & 2) || r->status || !b->seen || kle_r.used[i] || klmv_downed(r)) {
            if (b->g_held) { b->g_held = 0; klog("gather: record %d is no longer held (dead, down, aboard, escort or gone)", i); }
            continue;
        }
        ok[i] = 1;
        if (b->hp > b->g_hpmax) b->g_hpmax = b->hp;                            /* the most health this bot was seen with = its 100 % (StairGatherMinHp) */
        if (kle_dist(b->pos, klmv.gather_at) <= (float)klmv.gather_radius) near_n++;
        if (b->g_held) held_n++;
    }
    if (!held_n) klmv_r.g_first = 0;
    if (s->veh >= 1 && s->veh <= 5) { if (held_n) klmv_g_release(s, "a vehicle is called", near_n, now); else klmv_r.g_done = 1; return; }      /* the exit phase: never gather after a vehicle is called */
    if (held_n && near_n >= klmv.gather_n) { klmv_g_release(s, "count", near_n, now); return; }
    if (held_n && klmv_r.g_first && now - klmv_r.g_first >= klmv.gather_timeout) { klmv_g_release(s, "timeout", near_n, now); return; }
    if (klmv.gather_lone && held_n) {                                          /* StairGatherLoneMs: a held bot alone at the point is let go (only it) */
        for (i = 0; i < s->n && i < KLB_NREC; i++) {
            struct klmv_b *b = &klmv_r.b[i];
            if (!b->g_held) continue;
            if (near_n >= 2) { b->g_lone = 0; continue; }
            if (!b->g_lone) { b->g_lone = KLB_T(now); continue; }
            if (now - b->g_lone < klmv.gather_lone) continue;
            b->g_held = 0; b->g_no = 1; b->g_lone = 0; held_n--;
            if (!klmv.dry && kle_bot(s, i, &actor, &soldier, bp, w) && kle_block(soldier, cur) && kle_dist(cur, b->g_ord) <= 50.0f) {
                memset(&t, 0, sizeof t); t.rec = i; t.actor = actor; t.soldier = soldier; t.told_soft = 1;
                kltr_set("gather", "StairGather lone release: back to the chain's goal", -1);
                if ((k = kle_order2(&t, b->g_chain, got, w, 0)) == 1) klmv_foreign(i, got);
            }
            klog("gather: LONE RELEASE record %d: fewer than 2 loyal bots within %.0f m of the gather point for %lu s (%d held, %d orders given); back to its chain's goal (%.0f, %.0f, %.0f), not held again this round",
                 i, klmv.gather_radius / 100.0, klmv.gather_lone / 1000, held_n, b->g_n, b->g_chain[0], b->g_chain[1], b->g_chain[2]);
        }
        if (!held_n) klmv_r.g_first = 0;
    }
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; struct klmv_b *b = &klmv_r.b[i];
        if (!ok[i]) continue;
        if (!b->g_held && b->g_no) continue;                                   /* released alone this round */
        if (!b->g_held && klmv.gather_minhp && b->g_hpmax > 0 && b->hp < b->g_hpmax * klmv.gather_minhp / 100.0f) continue;      /* too hurt to be held (L47 rec 7: 38 %, downed 1.1 s later) */
        if (!b->g_held && (near_n >= klmv.gather_n || kle_dist(b->pos, klmv.gather_at) > (float)klmv.gather_radius)) continue;
        if (!kle_bot(s, i, &actor, &soldier, bp, w) || !kle_block(soldier, cur)) continue;      /* not now (said by the callers elsewhere); asked again next pass */
        if (!b->g_held) {
            if (cur[1] > b->pos[1] - 200.0f) continue;                         /* its chain's goal is not below it: it does not descend */
            if (r->stage >= 3) continue;                                       /* leaving the level: not ours */
            memcpy(b->g_chain, cur, 12);
        } else {
            if (kle_dist(cur, b->g_ord) <= 50.0f) continue;                    /* still our order */
            if (klmv.dry) continue;
            if (b->g_order_at && now - b->g_order_at < 1000) continue;         /* the game puts its goal back within 1 s (Last Call street spot): do not answer faster than 1 s */
            memcpy(b->g_chain, cur, 12);                                       /* the chain's newest goal is the one to go back to */
        }
        memset(&t, 0, sizeof t); t.rec = i; t.actor = actor; t.soldier = soldier; t.told_soft = 1;
        kltr_set("gather", b->g_held ? "StairGather: held, order again" : "StairGather: held at the gather point", -1);
        k = kle_order2(&t, klmv.gather_at, got, w, klmv.dry);
        b->g_order_at = KLB_T(now);
        if (!k) continue;                                                      /* refused (OrderGap, ...): asked again next pass */
        if (k == 1) { memcpy(b->g_ord, got, 12); klmv_foreign(i, got); }
        b->g_n++;
        if (!b->g_held) {
            b->g_held = 1; held_n++;
            if (!klmv_r.g_first) klmv_r.g_first = KLB_T(now);
            klog("gather: HOLD record %d at (%.0f, %.0f, %.0f), its chain goes to (%.0f, %.0f, %.0f); %d loyal bot(s) within %.0f m of the gather point, %d held, release at %d or %lu s%s",
                 i, b->pos[0], b->pos[1], b->pos[2], b->g_chain[0], b->g_chain[1], b->g_chain[2], near_n, klmv.gather_radius / 100.0, held_n, klmv.gather_n, klmv.gather_timeout / 1000,
                 k == 2 ? " (DRY RUN: nothing ordered)" : "");
        } else if (b->g_n <= 3 || b->g_n % 10 == 0)
            klog("gather: record %d: the game put its goal (%.0f, %.0f, %.0f) back, ordered to the gather point again (order %d)", i, b->g_chain[0], b->g_chain[1], b->g_chain[2], b->g_n);
    }
}

/* ---------------------------------------------------------------- the tick */

/* the round does not run (or not on a level this file may act on): what this file wrote goes back */
static void klmv_stand_down(DWORD rules, const char *why)
{
    int k;
    klmv_deny_none();
    if (klmv_gate_rules) klmv_gate_release(why);
    for (k = 0; k < KLMV_NSOUR; k++) if (klmv_sour[k].on) { if (klmv_sour[k].rules == rules) klmv_sweeten(k, why); else klmv_sour[k].on = 0; }
}

/* BoardProbe (default off): READ-ONLY. What the human's boarding rule 0x6840a0 tests, per 500 ms while the vehicle waits (state 3/4/5):
   session state [[0x168e598]+0x70] (0x19 wanted), vehicle state [rules+0x1dc], grace timer [rules+0x1d8], [rules+0x1e0] (owner set by 0x65ee60), [rules+0x1e4],
   the human record's status byte (+0x10, 0 wanted) and its index, player+0x2723 (0 wanted), the player's feet. NOT logged: the field-[1] trigger's active
   state and the action's volume at [action+0x88]+4 (their object is not located by this file; GUESS: needs a scan like klmv_scan) */
static void klmv_probe(const struct klb_snap *s, DWORD now)
{
    static DWORD last; DWORD player = 0, e0, e4, sess = 0, sess_obj; BYTE veh = 0, st = 0xff, b23 = 0xff; float tm = 0, hp[3] = { 0, 0, 0 }, hn[3]; int idx = s->human, got = 0;
    if (now - last < 500) return;
    if (!klh_rd(s->rules + 0x1dc, &veh, 1) || veh < 3 || veh > 5) return;
    last = now;
    e0 = klh_rd32(s->rules + 0x1e0); e4 = klh_rd32(s->rules + 0x1e4); klh_rd(s->rules + 0x1d8, &tm, 4);
    if ((sess_obj = klh_rd32((DWORD_PTR)KLH_VA(KLMV_SESSION))) != 0) klh_rd(sess_obj + 0x70, &sess, 4);
    if (idx >= 0) {
        DWORD recs = klh_rd32(s->rules + 0x348);
        if (recs) klh_rd(recs + 0x7c * (DWORD)(idx & 0xff) + 0x10, &st, 1);
        got = kle_human(&player, hp, hn);
        if (player) klh_rd(player + 0x2723, &b23, 1);
    }
    klog("boardprobe: veh=%d grace=%.2f session=0x%x rules1e0=%08x rules1e4=%08x human=%d status10=%d player=%08x p2723=%d feet=%s(%.0f,%.0f,%.0f)",
         (int)veh, klb_finite(tm) ? tm : -1.0f, sess, e0, e4, idx, st == 0xff ? -1 : (int)st, player, b23 == 0xff ? -1 : (int)b23, got ? "" : "?", hp[0], hp[1], hp[2]);
}

/* EscVisitProbe / EscVisitFix (default off, 2026-10-18). Facts read in kl2.exe: the exit trigger (0x6c3d50) -> rules slot 44 (0x6cd8e0) -> 0x8154f0 stores the
   vehicle handle at [[rules+0x5f8]+0x5c] and calls slot 194 (0x8fa6d0, thiscall, one stack arg, ret 4) with the state; slot 194 sets [rules+0x1dc] = state, for state 0
   clears [rules+0x1e0], else calls slot 89 (vtable +0x164, 0x49d170: [rules+0x1e4] = resolve(handle) and 1e0) ONLY while [rules+0x1e0] == 0 (0x8fa705). State 1 with
   [rules+0x1e4] == 0 skips the drive-in (0x8fa76e). On Park II, Vault and Hot Coffee II visit 1 shows 1e4 = 0 and the van never comes; visit 2 works.
   GUESS (mechanism of the fix): on those maps [rules+0x1e0] is already non-zero when visit 1's state 1 begins, so slot 89 is skipped. The probe logs the four
   values on every change (also the first sight of the round) to show whether that is so; the fix clears 1e0 and runs slot 194 again with the same state, once per visit. */
static void klmv_escvisit(const struct klb_snap *s, DWORD now)
{
    static const BYTE head[8] = { 0x83, 0xec, 0x24, 0x53, 0x55, 0x56, 0x8b, 0xf1 };      /* 0x8fa6d0 */
    DWORD rules = s->rules, st = 0, e0, e4, hp, h, vt, slot; BYTE b = 0xff; int changed;
    if (!rules || klh_rd32(rules) != KLB_RULES_VT || !klh_rd(rules + 0x1dc, &b, 1)) return;
    st = b; e0 = klh_rd32(rules + 0x1e0); e4 = klh_rd32(rules + 0x1e4);
    hp = klh_rd32(rules + 0x5f8); h = hp ? klh_rd32(hp + 0x5c) : 0;
    changed = !klmv_r.ev_have || st != klmv_r.ev_st || e0 != klmv_r.ev_e0 || e4 != klmv_r.ev_e4 || h != klmv_r.ev_h;
    if ((st == 1 || st == 2) && klmv_r.ev_st != 1 && klmv_r.ev_st != 2) { klmv_r.ev_visit++; klmv_r.ev_fixed = 0; }
    if (klmv.escprobe && changed)
        klog("escprobe: %s%u ms: state %u (was %d) 1e0 %08lx (was %08lx) 1e4 %08lx (was %08lx) handle %08lx (was %08lx) visit %d; 1e0's vtable %08lx",
             klmv_r.ev_have ? "" : "round start, ", now, st, klmv_r.ev_have ? (int)klmv_r.ev_st : -1, e0, klmv_r.ev_have ? klmv_r.ev_e0 : 0, e4, klmv_r.ev_have ? klmv_r.ev_e4 : 0,
             h, klmv_r.ev_have ? klmv_r.ev_h : 0, klmv_r.ev_visit, e0 ? klh_rd32(e0) : 0);      /* 2026-10-18 static reading (re/escape_visit1.md): the early non-zero 1e0 is written by 0x65ee60 from ZPlayerAction slot 26 (0x7fdbb0, the 'EnterVehicle' action) = [action+0x24]; its vtable names what that object is */
    klmv_r.ev_have = 1; klmv_r.ev_st = st; klmv_r.ev_e0 = e0; klmv_r.ev_e4 = e4; klmv_r.ev_h = h;
    if (!klmv.escfix || (st != 1 && st != 2) || e4 || !h || klmv_r.ev_fixed) return;
    vt = klh_rd32(rules); slot = klh_rd32(vt + 0x308);
    if (!vt || !slot || !klb_same_code(0x008fa6d0, head, sizeof head) || slot != 0x008fa6d0) { klmv_r.ev_fixed = 1; klog("escfix: visit %d: state %u, 1e4 0, handle %08lx, but rules slot 194 (%08lx) is not 0x8fa6d0 as this build knows: nothing done", klmv_r.ev_visit, st, h, slot); return; }
    klmv_r.ev_fixed = 1;
    if (klmv.dry) { klog("escfix: visit %d: DRY RUN - state %u, 1e0 %08lx, 1e4 0, handle %08lx: 1e0 WOULD be cleared and slot 194(%u) re-run", klmv_r.ev_visit, st, e0, h, st); return; }
    *(DWORD *)(DWORD_PTR)(rules + 0x1e0) = 0;      /* GUESS: slot 194 calls slot 89 only while this is 0 (0x8fa705); the re-run also repeats state 1/2's 0x709ba0(0) call and inc [rules+0x1ed] (no reader of +0x1ed found) */
    ((void (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)slot)((void *)(DWORD_PTR)rules, 0, st);      /* thiscall, one stack argument, ret 4 (0x8fb072) */
    klmv_r.ev_e0 = klh_rd32(rules + 0x1e0); klmv_r.ev_e4 = klh_rd32(rules + 0x1e4);
    b = 0xff; klh_rd(rules + 0x1dc, &b, 1); klmv_r.ev_st = b;
    klog("escfix: visit %d re-run state %u: 1e0 %08lx -> 0, 1e4 now %08lx (1e0 now %08lx, state now %u, handle %08lx; GUESS mechanism)", klmv_r.ev_visit, st, e0, klmv_r.ev_e4, klmv_r.ev_e0, b, h);
}

/* [Bots] VanCallNear=<metres> (2026-10-18, default 0 = this part does nothing; nothing else in this file changes with it off).
   The census of the overnight runs (KLHook.log, first 'van 5' snapshot of each round): of the AI heisters still in play when the van drove off,
   105 were at heist stage 1 or 2 and 154 at stage 3 (stage 3 = called: klmv_crewhold / reach / BoardAll look after those). A bot at stage 1/2 is
   never walked to the van by the board tactic (0x4fb064 asks stage 3). BoardAll (klescort.c) frees only a bot that has neither moved 1 m nor earned
   for 15 s; Hot Coffee II L70 record 7 (stage 2, $680000) stood 6.4 m from the doors, jittered under 1 m, and was left. Here: while the vehicle waits
   (state 3 / 4), VanCallDelay seconds into the wait, a loyal bot (no traitor, no escort, not downed, in play, no grab running) at heist stage
   VanCallMinStage..2 that stands within VanCallNear metres (horizontal) and 4 m (height) of the boarding place gets heist stage 3 by klmv_stage3
   (the byte BoardAll and BoardNear write, once per bot and round), and BoardReach's order to the doors takes it from there.
   GUESSES: that a bot of stage 1 within the range has nothing better to do than leave (it gives up its loot tactic); the height limit; the delay. */
static void klmv_vancall(const struct klb_snap *s, DWORD now)
{
    float bd[3]; int i, called = 0, cand = 0, waiting = s->veh == 3 || s->veh == 4; BYTE lastv = 0;
    if (!waiting || !kle_boarding(s->rules, bd)) { klmv_r.vc_at = 0; return; }
    if (klmv_r.vc_visit != klmv_r.visit) { klmv_r.vc_visit = klmv_r.visit; klmv_r.vc_at = 0; klmv_r.vc_told = 0; klmv_r.vc_n = 0; klmv_r.vc_last_told = 0; }
    if (!klmv_r.vc_at) klmv_r.vc_at = KLB_T(now);
    if (KLB_T(now) - klmv_r.vc_at < klmv.van_delay) return;
    if (klmv.van_last && klh_rd(s->rules + 0xe8a, &lastv, 1) && lastv) {      /* VanCallLast: the round's last vehicle ([rules+0xe8a], as BoardReach reads it): no range, no height limit */
        if (!klmv_r.vc_last_told) { klmv_r.vc_last_told = 1; klog("vancall: visit %d is the round's last vehicle: VanCallLast=1, every loyal bot at heist stage %d..2 in play is called, wherever it stands", klmv_r.visit, klmv.van_min); }
    } else lastv = 0;
    if (!lastv && klmv.van_near <= 0) return;
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; struct klmv_b *b = &klmv_r.b[i]; BYTE grab = 1; float dh;
        if (!r->used || !(r->flags & 1) || (r->flags & 2) || r->status || !b->seen || kle_r.used[i] || klmv_downed(r)) continue;
        if (r->stage < klmv.van_min || r->stage >= 3 || (b->told & 4)) continue;
        dh = klmv_h(b->pos, bd);
        if (!lastv && (dh > klmv.van_near || fabs(b->pos[1] - bd[1]) > 400.0f)) continue;
        cand++;
        if (!klh_rd(r->at + 0x15, &grab, 1) || grab) continue;                  /* a grab runs (crew record +0x15): let it end */
        if (klmv.dry) { if (!(b->told & 4)) { b->told |= 4; klog("vancall: visit %d: record %d (stage %u, $%lu) stands %.1f m from the boarding place: heist stage WOULD be set to 3 (dry run)", klmv_r.visit, i, r->stage, r->money, dh / 100); } continue; }
        klmv_s3_wrote = 0;
        klmv_stage3(s, i, lastv ? "at the round's last vehicle (VanCallLast)" : "near the waiting vehicle (VanCallNear)");
        if (klmv_s3_wrote) { called++; klog("vancall: visit %d: record %d (stage %u, $%lu) stood %.1f m from the boarding place (%s), %.1f s into the wait: called (stage 3)", klmv_r.visit, i, r->stage, r->money, dh / 100, lastv ? "VanCallLast, no limit" : "VanCallNear", (KLB_T(now) - klmv_r.vc_at) / 1000.0); }
    }
    klmv_r.vc_n += called;
    if (cand && !called && !klmv_r.vc_told && klmv.log > 1) { klmv_r.vc_told = 1; klog("vancall: visit %d: %d bot(s) of stage %d..2 within range, none called (a grab runs, or klmv_stage3 refused)", klmv_r.visit, cand, klmv.van_min); }
}

static void klmv_tick(int game_thread)
{
    static DWORD last; struct klb_snap s; DWORD now = GetTickCount(), player = 0; char why[200]; float hp[3] = { 0, 0, 0 }, hn[3];
    const struct klb_rec *h; int i, stages = 0, human_in, criminal, waiting;
    if (!klmv.any || !klb.on || !klh_exe_ok) return;
    if (now - last < 250) return;
    last = now;
    if (!klb_read(&s)) {
        /* no Arcade session can be read. ONE failed pass in a round must not lose what this file wrote (review S10): no
           box is denied meanwhile, the round's book and the gate are kept for 3 s, and the soured objects are kept for
           good - the next pass that reads a session puts them back or drops them by klmv_listed (the object must still
           be a ZOnlineMoneyCtrl in that rules object's list, with the state it had) */
        klmv_deny_none();
        klmv_last_end(0, 0, 1);
        if (!klmv_fail_at) klmv_fail_at = KLB_T(now);
        if (now - klmv_fail_at < 3000) return;
        klmv_r.rules = 0;
        if (klmv_gate_rules && game_thread) klmv_gate_release("no Arcade round object");
        return;
    }
    klmv_fail_at = 0;
    for (i = 0; i < s.n; i++) if (s.r[i].used) stages += s.r[i].stage;
    if (s.rules != klmv_r.rules || (s.state == KLB_ROUND && klmv_r.state != KLB_ROUND) || stages < klmv_r.stages) {      /* a new round: as klbot.c's klb_act */
        if (s.state == KLB_ROUND && klmv_r.state != KLB_ROUND) memset(&klmv_lc, 0, sizeof klmv_lc);      /* v82d: the last-call book starts with the round */
        memset(&klmv_r, 0, sizeof klmv_r); memset(klmv_fo_on, 0, sizeof klmv_fo_on); klmv_r.rules = s.rules; klmv_r.round_at = KLB_T(now); klmv_rc.armed = 0; klmv_rc.rules = 0; klmv_rc.relax = 0;
        if (game_thread)                      /* what is still sour is from before this round (the round's end puts them back; these outlived a pass that could not read): back if it still is that object, else forgotten */
            for (i = 0; i < KLMV_NSOUR; i++) if (klmv_sour[i].on) { if (klmv_sour[i].rules == s.rules) klmv_sweeten(i, "a new round"); else klmv_sour[i].on = 0; }
    }
    klmv_r.state = s.state; klmv_r.stages = stages;
    kltr_round(s.rules, now);
    if (!game_thread) {
        if (s.state == KLB_ROUND && !klmv_r.told_thread++) klog("move / wait / near: the tick is not on the game's thread ([KLHook] Tick=0?): nothing is ordered or written");
        return;
    }
    if (s.state != KLB_ROUND) { klmv_last_end(s.rules, s.state, 0); klmv_stand_down(s.rules, "the round is over"); return; }
    if (!klb_level(why)) {                    /* klbot.c section 0 */
        if (!klmv_r.told_gate++) klog("move / wait / near: %s: nothing is done here (this part acts only on a level that is not stock)", why);
        klmv_stand_down(s.rules, "this level is stock or not known");
        return;
    }
    h = s.human >= 0 ? &s.r[s.human] : 0;
    criminal = kle_criminal();
    human_in = h && h->status == 0 && kle_human(&player, hp, hn);
    waiting = s.veh == 3 || s.veh == 4;
    if (waiting && !klmv_r.was_waiting) { klmv_r.visit++; for (i = 0; i < KLB_NREC; i++) klmv_r.b[i].told &= (BYTE)~(16 | 32); }
    if (klmv_r.last_pass && now - klmv_r.last_pass > 1500) for (i = 0; i < KLB_NREC; i++) klmv_r.b[i].seen = 0;      /* the round stood still (the window was not in front): every clock starts again */
    klmv_r.last_pass = KLB_T(now);
    klmv_track(&s, now);
    kltr_poll(&s, now);
    if (klmv.probe) klmv_probe(&s, now);
    if (klmv.escprobe || klmv.escfix) klmv_escvisit(&s, now);
    if (klmv.last) klmv_last_vehicle(&s);
    if (klmv.botvan) klmv_bot_van(&s, now);
    if (klmv.hop) klmv_hops_load();
    if (klmv.near_ > 0 || klmv.reach > 0) klmv_boxes(&s, now);
    if (klmv.reach > 0) klmv_reach_pass(&s, now);
    klmv_r.was_waiting = waiting;
    if (klmv.wait) { klmv_gate(&s, now, h, criminal); klmv_driver(&s, now, h, human_in, criminal, hp); }
    if (klmv.crew_hold > 0) klmv_crewhold(&s, now, h, criminal);
    if (klmv.gather) klmv_gather(&s, now);
    if (klmv.van_near > 0 || klmv.van_last) klmv_vancall(&s, now);
    if (klmv.restless || klmv.loot) {
        klmv_sour_pass(s.rules, now);
        if (now - klmv_r.half >= 500) {        /* twice a second */
            klmv_r.half = KLB_T(now);
            if (klmv.loot) klmv_objects(s.rules); else klmv_nobj = 0;
            klmv_restless(&s, now, human_in, hp);
        }
    }
}

static void klmv_init(void)
{
    char t[16]; int v;
    memset(&klmv, 0, sizeof klmv); memset(&klmv_r, 0, sizeof klmv_r);
    v = klb_pos("Restless", 0, 600); klmv.restless = (DWORD)v * 1000;
    klmv.after = (DWORD)klb_pos("RestlessAfter", 0, 600) * 1000;      /* 2026-10-15 (run v74_T13rt2, Retomoto): for ~30 s after the round start the defend place of a bot is still its rappel landing on the balcony while the loot tactic has taken it into the room - b. ordered it back out ("they walk back to the balcony") */
    GetPrivateProfileStringA("Bots", "RestlessLoot", "", t, sizeof t, klh_ini);
    klmv.loot = t[0] ? (DWORD)klb_pos("RestlessLoot", 0, 600) * 1000 : klmv.restless;
    klmv.back = (DWORD)klb_pos("RestlessLootBack", 30, 240) * 1000; if (klmv.back < 5000) klmv.back = 5000;
    klmv.loot_near = klb_inif("RestlessLootNear", "200"); if (!klb_finite(klmv.loot_near) || klmv.loot_near < 50) klmv.loot_near = 50; if (klmv.loot_near > 600) klmv.loot_near = 600;
    klmv.hold = (DWORD)klb_pos("RestlessHold", 0, 600) * 1000; if (klmv.hold && klmv.hold < 5000) klmv.hold = 5000;
    if (!klmv.restless) klmv.hold = 0;
    klmv.hop = (DWORD)klb_pos("RestlessHop", 0, 600) * 1000; if (klmv.hop && klmv.hop < 5000) klmv.hop = 5000;
    if (!klmv.restless) klmv.hop = 0;
    klmv.hop_max = 1800.0f;
    klmv.pace = klb_inif("RestlessPace", "350"); if (!klb_finite(klmv.pace) || klmv.pace < 300) klmv.pace = 300; if (klmv.pace > 800) klmv.pace = 800;
    klmv.wait = GetPrivateProfileIntA("Bots", "WaitForYou", 0, klh_ini) != 0;
    klmv.wait_stage = klb_pos("WaitForYouStage", 3, 3); if (klmv.wait_stage < 1) klmv.wait_stage = 1;
    klmv.wait_max = (DWORD)klb_pos("WaitForYouMax", 150, 3600) * 1000;
    klmv.wait_floor = (DWORD)klb_pos("WaitForYouFloor", 0, 3600) * 1000;
    klmv.wait_hold = klb_inif("WaitForYouHold", "15"); if (!klb_finite(klmv.wait_hold) || klmv.wait_hold < 0) klmv.wait_hold = 0; if (klmv.wait_hold > 60) klmv.wait_hold = 60;
    klmv.crew_hold = klb_inif("CrewRouteHold", "0"); if (!klb_finite(klmv.crew_hold) || klmv.crew_hold < 0) klmv.crew_hold = 0; if (klmv.crew_hold > 60) klmv.crew_hold = 60;      /* 0 = off (default); GUESS if used: 45 (as FollowOutHold on Last Call) */
    klmv.crew_alone = GetPrivateProfileIntA("Bots", "CrewRouteAlone", 0, klh_ini) != 0;      /* 0 = off (default) */
    klmv.crew_range = klb_inif("CrewRouteRange", "100"); if (!klb_finite(klmv.crew_range) || klmv.crew_range < 5) klmv.crew_range = 100; if (klmv.crew_range > 300) klmv.crew_range = 300;      /* metres; 100 = GUESS (L61: 20-60 m straight line) */
    klmv.near_ = klb_inif("BoardNear", "0"); if (!klb_finite(klmv.near_) || klmv.near_ < 0) klmv.near_ = 0;
    klmv.near_visits = klb_pos("BoardNearVisits", 3, 100);
    klmv.near_stage = GetPrivateProfileIntA("Bots", "BoardNearStage", 1, klh_ini) != 0;
    klmv.reach = klb_inif("BoardReach", "0"); if (!klb_finite(klmv.reach) || klmv.reach < 0) klmv.reach = 0; if (klmv.reach > 0 && klmv.reach < 50) klmv.reach = 50;
    klmv.reach_visits = klb_pos("BoardReachVisits", 3, 100);      /* default 3 as BoardNearVisits (review S2: a bot nothing can walk to the doors is not stranded for the whole round) */
    klmv.reach_doors = GetPrivateProfileIntA("Bots", "BoardReachDoors", 1, klh_ini) != 0;
    klmv.reach_order = GetPrivateProfileIntA("Bots", "BoardReachOrder", 1, klh_ini) != 0;
    klmv.reach_repeat = (DWORD)klb_pos("BoardReachRepeat", 0, 60) * 1000;      /* 0 = off (default); proposed 3 s GUESS */
    klmv.reach_settle = (float)GetPrivateProfileIntA("Bots", "BoardReachSettle", 0, klh_ini); if (klmv.reach_settle < 0) klmv.reach_settle = 0; if (klmv.reach_settle > KLMV_DOORS_MAX) klmv.reach_settle = KLMV_DOORS_MAX;      /* 0 = off (default); proposed 200 GUESS */
    klmv.reach_aim = (float)GetPrivateProfileIntA("Bots", "BoardReachAim", 0, klh_ini); if (klmv.reach_aim < 0) klmv.reach_aim = 0; if (klmv.reach_aim > KLMV_DOORS_MAX) klmv.reach_aim = KLMV_DOORS_MAX;      /* 0 = off (default); proposed 150 GUESS */
    klmv.reach_chase = GetPrivateProfileIntA("Bots", "BoardReachChase", 0, klh_ini) != 0;      /* 0 = off (default) */
    klmv.reach_flat = GetPrivateProfileIntA("Bots", "BoardReachFlat", 0, klh_ini) != 0;      /* 0 = off (default) */
    klmv.van_near = (float)GetPrivateProfileIntA("Bots", "VanCallNear", 0, klh_ini); if (klmv.van_near < 0) klmv.van_near = 0; if (klmv.van_near > 20000) klmv.van_near = 20000;      /* metres in the ini, cm inside; 0 = off (default); GUESS if used: 40 */
    if (klmv.van_near > 0) klmv.van_near *= 100.0f;
    klmv.van_delay = (DWORD)klb_pos("VanCallDelay", 3, 60) * 1000;      /* seconds into the wait; GUESS 3 */
    klmv.van_min = klb_pos("VanCallMinStage", 1, 2); if (klmv.van_min < 1) klmv.van_min = 1;
    klmv.van_last = GetPrivateProfileIntA("Bots", "VanCallLast", 0, klh_ini) ? 1 : 0;      /* default 0 = unchanged */
    klmv.crew_hop = klb_inif("CrewRouteHopHold", "0"); if (!klb_finite(klmv.crew_hop) || klmv.crew_hop < 0) klmv.crew_hop = 0; if (klmv.crew_hop > 60) klmv.crew_hop = 60;      /* seconds, 0 = off (default); GUESS if used: 15 */
    klmv.dry = GetPrivateProfileIntA("Bots", "MoveDry", 0, klh_ini) != 0;
    klmv.log = klb_pos("MoveLog", 1, 2);
    klmv.last = GetPrivateProfileIntA("Bots", "LastVehicle", 1, klh_ini) != 0;
    klmv.flagok = GetPrivateProfileIntA("Bots", "LastVehicleFlagged", 0, klh_ini) ? 1 : 0;      /* default 0 = unchanged */
    klmv.last_lead = (float)GetPrivateProfileIntA("Bots", "LastVehicleLead", 25, klh_ini) / 10.0f; if (klmv.last_lead < 2.5f) klmv.last_lead = 2.5f; if (klmv.last_lead > 60.0f) klmv.last_lead = 60.0f;      /* tenths of a s (25 = 2.5 s, the old literal = default); 15 s is a GUESS for a test */
    klmv.reach_fight = GetPrivateProfileIntA("Bots", "BoardReachFight", 0, klh_ini) != 0;      /* 0 = off (default) */
    klmv.reach_fight_range = (float)GetPrivateProfileIntA("Bots", "BoardReachFightRange", 1500, klh_ini); if (klmv.reach_fight_range < 0) klmv.reach_fight_range = 0; if (klmv.reach_fight_range > KLMV_SENT) klmv.reach_fight_range = KLMV_SENT;      /* cm; 1500 = 15 m GUESS */
    klmv.snap = klmv.restless ? klb_pos("RestlessSnap", 0, 1) : 0;      /* 0 = off (default) */
    klmv.skip_down = GetPrivateProfileIntA("Bots", "RestlessSkipDowned", 0, klh_ini) != 0;      /* 0 = off (default) */
    klmv.snap_range = (DWORD)klb_pos("RestlessSnapRange", 4000, 20000);      /* GUESS: 40 m */
    klmv.snap_human = (DWORD)klb_pos("RestlessSnapHuman", 1500, 20000);      /* GUESS: 15 m */
    klmv.snap_cap = klb_pos("RestlessSnapMax", 2, 20);
    klmv.escprobe = GetPrivateProfileIntA("Bots", "EscVisitProbe", 0, klh_ini) != 0;      /* 0 = off (default) */
    klmv.escfix = GetPrivateProfileIntA("Bots", "EscVisitFix", 0, klh_ini) != 0;      /* 0 = off (default); GUESS fix, see klmv_escvisit */
    klmv.probe = GetPrivateProfileIntA("Bots", "BoardProbe", 0, klh_ini) != 0;      /* 0 = off (default) */
    klmv.botvan = (DWORD)klb_pos("BotVan", 4, 120) * 1000;      /* v78: default 4 s; 0 = off */
    klmv.gather = GetPrivateProfileIntA("Bots", "StairGather", 0, klh_ini) != 0;      /* 0 = off (default) */
    klmv.gather_n = klb_pos("StairGatherN", 4, 8); if (klmv.gather_n < 2) klmv.gather_n = 2;      /* GUESS: 4 (L36 cleared the nest with 5-6) */
    klmv.gather_radius = (DWORD)klb_pos("StairGatherRadius", 2000, 20000);      /* cm; GUESS: 20 m */
    klmv.gather_timeout = (DWORD)klb_pos("StairGatherTimeout", 30, 600) * 1000;      /* GUESS: 30 s */
    klmv.gather_lone = (DWORD)klb_pos("StairGatherLoneMs", 0, 600000);      /* 0 = off (default); GUESS if used: the L47 lone hold of rec 3 was harmless for 30 s */
    klmv.gather_minhp = klb_pos("StairGatherMinHp", 0, 100);      /* percent; 0 = off (default); GUESS if used: 50 (L47 rec 7 was held at 38 % and died; recs 1-3 were held at full health) */
    klmv.gather_at[0] = 27167.0f; klmv.gather_at[1] = 582.0f; klmv.gather_at[2] = 30386.0f;      /* GUESS: Hasta's stair top = the lead bot's chain goal in the census */
    {
        char at[96]; float a[3];
        GetPrivateProfileStringA("Bots", "StairGatherAt", "", at, sizeof at, klh_ini);
        if (at[0] && sscanf(at, "%f , %f , %f", &a[0], &a[1], &a[2]) == 3 && klb_finite(a[0]) && klb_finite(a[1]) && klb_finite(a[2])) memcpy(klmv.gather_at, a, 12);
        else if (at[0]) klog("gather: StairGatherAt=%s is not x,y,z: the default (Hasta's stair top) is used", at);
    }
    klmv.any = klmv.restless || klmv.loot || klmv.wait || klmv.near_ > 0 || klmv.reach > 0 || klmv.last || klmv.botvan || klmv.probe || klmv.gather || klmv.escprobe || klmv.escfix || klmv.crew_hold > 0 || klmv.van_near > 0 || klmv.van_last;
    if (!klmv.any) return;
    if (!klb.on) { klog("move / wait / near / reach: [Bots] Restless, WaitForYou, BoardNear or BoardReach is set but [Bots] Enable is 0: they need klbot.c's crew records, nothing is done"); klmv.any = 0; return; }
    if (klmv.restless || klmv.loot)
        klog("move: on; Restless=%lu s Loot=%lu s (back %lu s, near %.0f) Hold=%lu s Pace=%.0f%s: an AI heister that stands that long without moving 1 m or earning - on a money object that pays nothing: the object is no loot candidate for a while (one byte of it; you can still take it); more than 3 m from the place its chain ordered: that order again (the soldier's own order %08x)%s; Arcade only, on a level that is not the stock one of its slot",
             klmv.restless / 1000, klmv.loot / 1000, klmv.back / 1000, klmv.loot_near, klmv.hold / 1000, klmv.pace, klmv.dry ? " DRY RUN (MoveDry=1: nothing is written or called)" : "", KLE_ORDER,
             klmv.hold ? "; at its own hold place for Hold seconds: a shift round it" : "; a bot at its own place (a meant wait) is left alone");
    if (klmv.gather) klog("gather: StairGather on (GUESS limits): a loyal AI heister within %lu m of (%.0f, %.0f, %.0f) whose chain goes more than 2 m down is held there until %d loyal bots stand within the radius or %lu s after the first was held; once per round; per-map ini (no level check)%s",
                           klmv.gather_radius / 100, klmv.gather_at[0], klmv.gather_at[1], klmv.gather_at[2], klmv.gather_n, klmv.gather_timeout / 1000, klmv.dry ? "; MoveDry=1: nothing is ordered" : "");
    if (klmv.gather && (klmv.gather_lone || klmv.gather_minhp)) klog("gather: StairGatherLoneMs=%lu (a held bot with fewer than 2 loyal bots in the radius for that long is released alone, 0 = off), StairGatherMinHp=%d (no hold below that percent of the health it was seen with, 0 = off)", klmv.gather_lone, klmv.gather_minhp);
    if (klmv.crew_hold > 0) klog("crewhold: CrewRouteHold=%.1f s a visit, CrewRouteRange=%.0f m (GUESS limits)%s: with you aboard and the vehicle's timer under %.1f s, a called loyal bot that moves %.0f m in 2 s (either way) within that range of the boarding place holds the driver, same refusals and shield as FollowOutHold; its seconds are counted apart from FollowOutHold's", klmv.crew_hold, klmv.crew_range, klmv.dry ? "; MoveDry=1: nothing is written" : "", KLE_HOLD_AT, KLE_COME / 100);
    if (klmv.crew_hold > 0 && klmv.crew_alone) klog("crewhold: CrewRouteAlone=1: the hold also runs while you are in play (not aboard). GUESS: a human who is still fighting wants the crew held too");
    if (klmv.van_last) klog("vancall: VanCallLast=1: on the round's last vehicle every loyal in-play bot at heist stage %d..2 is called whatever its distance (after VanCallDelay %lu s; GUESS)", klmv.van_min, klmv.van_delay / 1000);
    if (klmv.crew_hop > 0) klog("crewhold: CrewRouteHopHold=%.1f s (GUESS): once a visit, when CrewRouteHold is used up and a stage-3 bot closed 1 m in on the boarding place within 15 s, the budget grows by that", klmv.crew_hop);
    if (klmv.van_near > 0) klog("vancall: on; VanCallNear=%.0f m VanCallDelay=%lu s MinStage=%d%s: while the vehicle waits a loyal bot at heist stage %d..2 within that range of the boarding place gets heist stage 3 (GUESS limits)", klmv.van_near / 100, klmv.van_delay / 1000, klmv.van_min, klmv.dry ? " DRY RUN" : "", klmv.van_min);
    if (klmv.skip_down) klog("move: RestlessSkipDowned on: a downed heister gets no restless order, snap or hop and its stand-still clock restarts when it is up");
    if (klmv.snap) klog("move: RestlessSnap on (audit 1018 E2.2, GUESS limits): a bot whose chain place was ordered %d times without arriving is put AT the place (range %lu, human not within %lu, at most %d times per bot and round)%s", KLMV_TOTAL, klmv.snap_range / 100, klmv.snap_human / 100, klmv.snap_cap, klmv.dry ? "; MoveDry=1: never" : "");
    if (klmv.last)
        klog("last: on (LastVehicle=1, the default; 0 = off)%s: in an Arcade round on a level that is not the stock one, v82e: when the END timer [rules+0x200] (what really ends the round, kl2 0x5dff40) shows %.2f s or less and the game has called no vehicle (state 0, [rules+0xe8a] 0: its own last call at 2.0 s found no vehicle - none was called before in this level load), the vehicle the exit trigger names is called as the round's last (0x8154f0, as the game's own)",
             klmv.dry ? " DRY RUN (MoveDry=1)" : "", KLMV_LAST_AT);
    if (klmv.botvan)
        klog("botvan: on (BotVan=%lu s, the default 4; 0 = off)%s: when a loyal AI heister in play has had heist stage 3 (it stood in the level exit box) that long and no vehicle was called (state 0, not the last one, nothing holds the call, more than 20 s on the clock), the vehicle the exit trigger names is called for the crew (0x8154f0 with 0, as the box's own call)",
             klmv.botvan / 1000, klmv.dry ? " DRY RUN (MoveDry=1)" : "");
    if (klmv.hop)
        klog("move: RestlessHop=%lu s: a bot that has stood that long at its own hold place (not under fire, not in an escape box, no vehicle called) is ordered to a cover place of the level's KLJoin.ini [Hops] within that list's Max of the hold (tools/kl_fa_bots_rt.py hops); none near, or none listed: the old shift round the hold when RestlessHold is set, else nothing", klmv.hop / 1000);
    if (klmv.wait)
        klog("wait: on; WaitForYou=1 Stage=%d Floor=%lu s Max=%lu s Hold=%.1f s%s: while you are a heister in play under that heist stage no vehicle is called (rules +0x1ee, a byte the exit trigger asks - and the HUD's round clock: it is RED meanwhile); while a vehicle waits and you come, its timer gets up to 5 s more under 2 s, Hold seconds a visit at most; Arcade only, on a level that is not the stock one of its slot",
             klmv.wait_stage, klmv.wait_floor / 1000, klmv.wait_max / 1000, klmv.wait_hold, klmv.dry ? " DRY RUN" : "");
    if (klmv.near_ > 0)
        klog("near: on; BoardNear=%.0f Visits=%d Stage=%d%s: a ZAllyEscapeBox farther than that from the escape vehicle's boarding place takes no AI heister aboard (a private vtable copy on the level's box objects, slot 25); Arcade only, on a level that is not the stock one of its slot. FollowOutHold=%.0f FollowOutSpare=%d%s",
             klmv.near_, klmv.near_visits, klmv.near_stage, klmv.dry ? " DRY RUN" : "", kle.fo_hold, kle.fo_spare,
             kle.fo_hold > 0 || kle.fo_spare ? "" : ": NEITHER IS ON - an AI heister a far box no longer takes is shot by the rules when the vehicle leaves with you aboard");
    if (klmv.reach > 0)
        klog("reach: on; BoardReach=%.0f Visits=%d Doors=%d Order=%d Stage=%d%s: while the escape vehicle stands, a ZAllyEscapeBox takes an AI heister aboard only when THAT BOT is within that distance of the vehicle's boarding box - the box YOU get in at (the boxes' update done by this file, record by record, with the game's own calls; a private vtable copy on the level's box objects, slot 25)%s%s; Arcade only, on a level that is not the stock one of its slot.%s FollowOutHold=%.0f FollowOutSpare=%d%s",
             klmv.reach, klmv.reach_visits, klmv.reach_doors, klmv.reach_order, klmv.near_stage, klmv.dry ? " DRY RUN" : "",
             klmv.reach_doors ? "; a called bot (stage 3) that near is taken there, in a box or not" : "", klmv.reach_order ? "; a called bot that stands within 30 m of it is sent to the doors once a visit" : "",
             klmv.near_ > 0 ? " BoardNear is set too: a box it denies takes nobody whatever BoardReach says (BoardReach alone is enough)." : "", kle.fo_hold, kle.fo_spare,
             kle.fo_hold > 0 || kle.fo_spare ? "" : ": NEITHER IS ON - an AI heister who does not reach the doors in the vehicle's 8 s is shot by the rules when it leaves with you aboard");
}

#endif /* KLMOVE_C */
