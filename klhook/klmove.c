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
 *       comes) or FollowOutSpare=1 (nobody left behind is shot), and the part counts it: at every departure one line
 *       'near: visit N: the vehicle leaves ...: K AI heister(s) still in play ..., M of them (*) stood at a denied box'.
 *    NOT ESTABLISHED: on which thread a controller's update runs (the wrapper only reads a table of at most eight
 *    entries the tick writes); what a bot in a denied box does whose stage-3 board tactic finds no path (it stands;
 *    from the third visit the box takes it).
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
 *   WaitForYouHold=15     seconds the driver is held per visit while you come; 0 = never
 *   BoardNear=0           a ZAllyEscapeBox farther than this from the boarding place takes nobody aboard; 0 = off.
 *                         Use it with FollowOutHold or FollowOutSpare: who is left in play when you are driven out is shot
 *   BoardNearVisits=3     from this visit of a vehicle on every box works again (0 = never again)
 *   BoardNearStage=1      a bot under stage 3 at a denied box gets stage 3 (so that its board tactic walks it)
 *   MoveDry=0             1 = every line, NOTHING written or called (the boxes are not wrapped either)
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
#define KLMV_BOXR       500.0f               /* a bot within this of a box's node stands 'at' the box (a box is 350 x 416 x 350). GUESS */

static struct {
    int any, dry, log;
    DWORD restless, loot, back, hold; float pace, loot_near;
    int wait, wait_stage; DWORD wait_max, wait_floor; float wait_hold;
    float near_; int near_visits, near_stage;
} klmv;

struct klmv_b {
    DWORD actor, since, money, order_at, hit_at, look_obj, look_at; int seen, have_anchor, have_target, tries, total, phase, paced, beside, look_amount; BYTE told;
    float pos[3], hp, anchor[3], anchor0[3], target[3], try_pos[3];      /* anchor = the place its chain ordered; anchor0 = where the count 'total' began */
};
static struct {
    DWORD rules, state, round_at, last_pass, half; int stages, told_gate, told_thread, told_list, told_ready;
    struct klmv_b b[KLB_NREC];
    int visit, was_waiting, scanned; BYTE was_veh; float near_bd[3]; DWORD gate_ready; int gate_told;
    int hold_visit, hold_told, h_comes; float hold_used, h_d; DWORD h_at;
} klmv_r;

/* what outlives a round's bookkeeping: bytes this file has written into objects of the level */
static DWORD klmv_gate_rules;                 /* the rules object whose +0x1ee this file set (0 = none) */
static struct { DWORD obj, rules, until, at; int amount, count, on; BYTE active, state; } klmv_sour[KLMV_NSOUR];
static struct { DWORD at; float pos[3], d; volatile LONG deny; LONG asked; int told_visit, would; } klmv_box[KLMV_NBOX];      /* would = denied by the rule (deny stays 0 in a dry run); d = its distance to the boarding place while the vehicle stood */
static int klmv_nbox; static DWORD klmv_box_rules, klmv_vt[KLMV_VT_N + 1]; static int klmv_vt_ok;
static DWORD klmv_fail_at;                    /* since when klb_read fails (0 = it does not) */
static struct { DWORD obj; float pos[3]; int amount; BYTE active, state; } klmv_obj[KLMV_NOBJ]; static int klmv_nobj;

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
         klmv.dry ? "DRY RUN: nothing is wrapped" : wrapped == klmv_nbox ? "slot 25 wrapped (a box farther than BoardNear from the boarding place takes nobody aboard)" : "NOT every one could be wrapped");
}

static void klmv_deny_none(void) { int i; for (i = 0; i < KLMV_NBOX; i++) klmv_box[i].deny = 0, klmv_box[i].would = 0; }

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
        if (have_bd && !last && d > klmv.near_ && (!klmv.near_visits || klmv_r.visit < klmv.near_visits)) deny = 1;
        klmv_box[i].would = (int)deny;
        if (!klmv.dry) klmv_box[i].deny = deny;
        if (deny) any = 1;
        if (waiting && klmv_box[i].told_visit != klmv_r.visit) {
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
        klog("near: visit %d: the vehicle leaves %s: %d AI heister(s) still in play (record, metres from the boarding place:%s), %d of them (*) stood at a denied box on this visit%s", klmv_r.visit, hab ? "WITH YOU ABOARD" : "without you", left, left ? list : " none",
             denied, !left ? "" : !hab ? " - it comes again for them" : spare ? " - FollowOutSpare is on: nobody is shot" : " - THE RULES SHOOT THEM NOW (stock Arcade: every AI heister left in play when the human is driven out); FollowOutHold / FollowOutSpare are the keys against it");
        for (i = 0; i < KLB_NREC; i++) klmv_r.b[i].told &= (BYTE)~16;
    }
    if (!any || !waiting) return;                                              /* only while it STANDS */
    /* g. a bot under stage 3 at a denied box: the stage byte BoardAll writes, with BoardAll's tests (no traitor, in play,
       not this round's escort, the record looked at again before the write), so that its board tactic walks it */
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; struct klmv_b *b = &klmv_r.b[i]; BYTE fl = 0, st = 0, cur = 3;
        if (!r->used || !(r->flags & 1) || r->status || !b->seen) continue;
        for (j = 0; j < klmv_nbox; j++) if (klmv_box[j].at && klmv_box[j].would && klmv_h(b->pos, klmv_box[j].pos) <= KLMV_BOXR && fabs(b->pos[1] - klmv_box[j].pos[1]) <= 400.0f) break;
        if (j >= klmv_nbox) continue;
        b->told |= 16;                                                         /* for the line at the departure */
        if (!klmv.near_stage || (r->flags & 2) || kle_r.used[i] || r->stage < 1 || r->stage >= 3 || (b->told & 4)) continue;      /* the escort is klescort.c's: it releases it to the boarding place when the vehicle waits */
        if (klmv.dry) { b->told |= 4; klog("near: record %d (stage %u) at (%.0f, %.0f, %.0f) stands at a denied box: heist stage WOULD be set to 3 (dry run)", i, r->stage, b->pos[0], b->pos[1], b->pos[2]); continue; }
        if (!klb_still(s, i, &fl, &st) || st || (fl & 2) || !klh_rd(r->at + 0x78, &cur, 1)) continue;      /* gone, aboard, dead or turned since the snapshot: looked at again */
        b->told |= 4;
        if (cur < 3 && !klb_put8(r->at + 0x78, 3, "crew record: heist stage 3 (at a denied escape box: it has to walk to the vehicle)")) { klog("near: record %d: the stage byte was NOT written", i); continue; }
        klog("near: record %d (stage %u) at (%.0f, %.0f, %.0f) stands at a denied box: heist stage set to 3 - it has to walk to the vehicle (its board tactic takes it aboard within 3 m)", i, r->stage, b->pos[0], b->pos[1], b->pos[2]);
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
    float bd[3], d, timer = klb_finite(s->timer) ? s->timer : -1.0f, tnow = 0, add; BYTE grade = 1, paid = 0, veh2 = 0; const char *no = 0;
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
    if (no || klmv.dry) {
        if (!(klmv_r.hold_told & 1)) {
            klmv_r.hold_told |= 1;
            if (no) klog("wait: hold: the vehicle leaves in %.1f s without you (%.1f m away) and is NOT held: %s", timer, d / 100, no);
            else klog("wait: hold: the vehicle would leave in %.1f s and you are %.1f m from it, coming: its timer WOULD get %.1f s more (dry run)", timer, d / 100, add);
        }
        return;
    }
    tnow += add;
    if (!klh_data((void *)(DWORD_PTR)(s->rules + 0x1d8), &tnow, 4, "escape vehicle wait timer (the driver waits for the human)")) { if (!(klmv_r.hold_told & 1)) { klmv_r.hold_told |= 1; klog("wait: hold: the vehicle's timer could NOT be written"); } return; }
    klmv_r.hold_used += add;
    klog("wait: hold: the vehicle would leave in %.1f s and you are %.1f m from it, coming: timer %.1f -> %.1f s (%.1f of %.1f s used this visit)", timer, d / 100, tnow - add, tnow, klmv_r.hold_used, klmv.wait_hold);
}

/* ---------------------------------------------------------------- Restless */

/* where every AI heister in play stands, what it has, its health; since when neither place nor money changed */
static void klmv_track(const struct klb_snap *s, DWORD now)
{
    int i; DWORD node, ho; float p[3], raw[0x28 / 4];
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; struct klmv_b *b = &klmv_r.b[i];
        if (r->used && r->actor != b->actor) { memset(b, 0, sizeof *b); b->actor = r->actor; }      /* another member in this record */
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

static void klmv_restless(const struct klb_snap *s, DWORD now, int human_in, const float hp[3])
{
    int i, j, k, fire, there; DWORD actor, soldier, stood; float bp[3], cur[3], want[3], got[3], d; char w[100]; struct kle_e t; BYTE grab;
    for (i = 0; i < s->n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &s->r[i]; struct klmv_b *b = &klmv_r.b[i];
        grab = 1;
        if (!r->used || !(r->flags & 1) || (r->flags & 2) || r->status || !b->seen || kle_r.used[i]) continue;      /* not a traitor, never this round's escort */
        /* the place its chain ordered: whatever the defend block holds that this file did not put there. A place within
           KLE_ROUTE of ours is one of the soldier's own tactics moving it (klescort.c 2, the same GUESS): the centre stays */
        if ((soldier = klh_rd32(r->actor + 0x77c)) != 0 && klh_rd32(soldier) == KLE_SOLDIER_VT && kle_block(soldier, cur) && (cur[0] || cur[1] || cur[2])) {
            if (b->have_target && kle_dist(cur, b->target) <= KLE_ROUTE) {
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
        if (b->order_at && now - b->order_at < (klmv.restless < 4000 ? 4000 : klmv.restless)) continue;
        if (fire) continue;                                                    /* b and c alike: a bot that fights from where it stands is not pulled out (review S1) */
        d = klmv_h(b->pos, b->anchor);
        /* where this file sent it (a shift round its hold, or beside the human) is its place too, while the block still holds that */
        there = b->have_target && (b->paced || b->beside) && klmv_h(b->pos, b->target) <= KLMV_OFF && fabs(b->pos[1] - b->target[1]) <= 300.0f;
        if (!there && (d > KLMV_OFF || fabs(b->pos[1] - b->anchor[1]) > 300.0f)) {
            /* b. stuck off its place */
            int beside = 0;
            if (b->tries && kle_dist(b->pos, b->try_pos) > 200.0f) b->tries = 0;      /* another spot */
            if (b->tries >= 4 || b->total >= KLMV_TOTAL) {
                if (!(b->told & 1)) { b->told |= 1; klog("move: record %d still stands at (%.0f, %.0f, %.0f), %.1f m from its place, after %d order(s) on this spot and %d for this place of its chain: it is left until its chain orders another place", i, b->pos[0], b->pos[1], b->pos[2], d / 100, b->tries, b->total); }
                continue;
            }
            if (!kle_bot(s, i, &actor, &soldier, bp, w)) { if (!(b->told & 2)) { b->told |= 2; klog("move: record %d stands at (%.0f, %.0f, %.0f) but gets no order: %s", i, b->pos[0], b->pos[1], b->pos[2], w); } continue; }
            memcpy(want, b->anchor, 12);
            if (b->tries >= 2 && human_in && kle_dist(bp, hp) > 800.0f) { kle_place(hp, bp, 1, 0, want); beside = 1; }
            if (kle_dist(bp, want) <= 260.0f) continue;                        /* the game would take it as 'he is there already' (soft): a waiting step of the chain would end */
            memset(&t, 0, sizeof t); t.rec = i; t.actor = actor; t.soldier = soldier; t.told_soft = 1;
            k = kle_order2(&t, want, got, w, klmv.dry);
            b->order_at = KLB_T(now); memcpy(b->try_pos, b->pos, 12);
            if (!k) { if (!(b->told & 2)) { b->told |= 2; klog("move: record %d NOT ordered: %s", i, w); } continue; }
            b->tries++; b->total++; b->since = now;
            if (k == 1) { memcpy(b->target, got, 12); b->have_target = 1; b->paced = 0; b->beside = beside; }
            klog("move: record %d (stage %u) stood %.1f s at (%.0f, %.0f, %.0f), %.1f m from its place (%.0f, %.0f, %.0f): %s; the game set (%.0f, %.0f, %.0f); time %d on this spot, %d of %d for this place",
                 i, r->stage, stood / 1000.0, bp[0], bp[1], bp[2], d / 100, b->anchor[0], b->anchor[1], b->anchor[2],
                 beside ? (k == 2 ? "WOULD be sent beside you (dry run)" : "sent beside you") : (k == 2 ? "its order WOULD be given again (dry run)" : "its order is given again"), got[0], got[1], got[2], b->tries, b->total, KLMV_TOTAL);
            continue;
        }
        /* c. at its own place: a meant wait. Only RestlessHold moves it, and only round that place */
        if (b->beside) continue;                                               /* sent beside the human: it stays there until its chain orders another place */
        if (!klmv.hold) { if (klmv.log >= 2 && !(b->told & 8)) { b->told |= 8; klog("move: record %d holds its place (%.0f, %.0f, %.0f) for %.0f s: a meant wait, left alone (RestlessHold=0; said once per bot)", i, b->anchor[0], b->anchor[1], b->anchor[2], stood / 1000.0); } continue; }
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
        memset(&t, 0, sizeof t); t.rec = i; t.actor = actor; t.soldier = soldier; t.told_soft = 1;
        k = kle_order2(&t, want, got, w, klmv.dry);
        b->order_at = KLB_T(now); b->since = now;
        if (!k) continue;
        if (k == 1) { memcpy(b->target, got, 12); b->have_target = 1; b->paced = 1; b->beside = 0; }
        if (klmv.log) klog("move: record %d %s round its hold (%.0f, %.0f, %.0f) after %.1f s: to (%.0f, %.0f, %.0f), the game set (%.0f, %.0f, %.0f)", i, k == 2 ? "WOULD shift (dry run)" : "shifts",
                          b->anchor[0], b->anchor[1], b->anchor[2], stood / 1000.0, want[0], want[1], want[2], got[0], got[1], got[2]);
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
        if (!klmv_fail_at) klmv_fail_at = KLB_T(now);
        if (now - klmv_fail_at < 3000) return;
        klmv_r.rules = 0;
        if (klmv_gate_rules && game_thread) klmv_gate_release("no Arcade round object");
        return;
    }
    klmv_fail_at = 0;
    for (i = 0; i < s.n; i++) if (s.r[i].used) stages += s.r[i].stage;
    if (s.rules != klmv_r.rules || (s.state == KLB_ROUND && klmv_r.state != KLB_ROUND) || stages < klmv_r.stages) {      /* a new round: as klbot.c's klb_act */
        memset(&klmv_r, 0, sizeof klmv_r); klmv_r.rules = s.rules; klmv_r.round_at = KLB_T(now);
        if (game_thread)                      /* what is still sour is from before this round (the round's end puts them back; these outlived a pass that could not read): back if it still is that object, else forgotten */
            for (i = 0; i < KLMV_NSOUR; i++) if (klmv_sour[i].on) { if (klmv_sour[i].rules == s.rules) klmv_sweeten(i, "a new round"); else klmv_sour[i].on = 0; }
    }
    klmv_r.state = s.state; klmv_r.stages = stages;
    if (!game_thread) {
        if (s.state == KLB_ROUND && !klmv_r.told_thread++) klog("move / wait / near: the tick is not on the game's thread ([KLHook] Tick=0?): nothing is ordered or written");
        return;
    }
    if (s.state != KLB_ROUND) { klmv_stand_down(s.rules, "the round is over"); return; }
    if (!klb_level(why)) {                    /* klbot.c section 0 */
        if (!klmv_r.told_gate++) klog("move / wait / near: %s: nothing is done here (this part acts only on a level that is not stock)", why);
        klmv_stand_down(s.rules, "this level is stock or not known");
        return;
    }
    h = s.human >= 0 ? &s.r[s.human] : 0;
    criminal = kle_criminal();
    human_in = h && h->status == 0 && kle_human(&player, hp, hn);
    waiting = s.veh == 3 || s.veh == 4;
    if (waiting && !klmv_r.was_waiting) klmv_r.visit++;
    if (klmv_r.last_pass && now - klmv_r.last_pass > 1500) for (i = 0; i < KLB_NREC; i++) klmv_r.b[i].seen = 0;      /* the round stood still (the window was not in front): every clock starts again */
    klmv_r.last_pass = KLB_T(now);
    klmv_track(&s, now);
    if (klmv.near_ > 0) klmv_boxes(&s, now);
    klmv_r.was_waiting = waiting;
    if (klmv.wait) { klmv_gate(&s, now, h, criminal); klmv_driver(&s, now, h, human_in, criminal, hp); }
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
    GetPrivateProfileStringA("Bots", "RestlessLoot", "", t, sizeof t, klh_ini);
    klmv.loot = t[0] ? (DWORD)klb_pos("RestlessLoot", 0, 600) * 1000 : klmv.restless;
    klmv.back = (DWORD)klb_pos("RestlessLootBack", 30, 240) * 1000; if (klmv.back < 5000) klmv.back = 5000;
    klmv.loot_near = klb_inif("RestlessLootNear", "200"); if (!klb_finite(klmv.loot_near) || klmv.loot_near < 50) klmv.loot_near = 50; if (klmv.loot_near > 600) klmv.loot_near = 600;
    klmv.hold = (DWORD)klb_pos("RestlessHold", 0, 600) * 1000; if (klmv.hold && klmv.hold < 5000) klmv.hold = 5000;
    if (!klmv.restless) klmv.hold = 0;
    klmv.pace = klb_inif("RestlessPace", "350"); if (!klb_finite(klmv.pace) || klmv.pace < 300) klmv.pace = 300; if (klmv.pace > 800) klmv.pace = 800;
    klmv.wait = GetPrivateProfileIntA("Bots", "WaitForYou", 0, klh_ini) != 0;
    klmv.wait_stage = klb_pos("WaitForYouStage", 3, 3); if (klmv.wait_stage < 1) klmv.wait_stage = 1;
    klmv.wait_max = (DWORD)klb_pos("WaitForYouMax", 150, 3600) * 1000;
    klmv.wait_floor = (DWORD)klb_pos("WaitForYouFloor", 0, 3600) * 1000;
    klmv.wait_hold = klb_inif("WaitForYouHold", "15"); if (!klb_finite(klmv.wait_hold) || klmv.wait_hold < 0) klmv.wait_hold = 0; if (klmv.wait_hold > 60) klmv.wait_hold = 60;
    klmv.near_ = klb_inif("BoardNear", "0"); if (!klb_finite(klmv.near_) || klmv.near_ < 0) klmv.near_ = 0;
    klmv.near_visits = klb_pos("BoardNearVisits", 3, 100);
    klmv.near_stage = GetPrivateProfileIntA("Bots", "BoardNearStage", 1, klh_ini) != 0;
    klmv.dry = GetPrivateProfileIntA("Bots", "MoveDry", 0, klh_ini) != 0;
    klmv.log = klb_pos("MoveLog", 1, 2);
    klmv.any = klmv.restless || klmv.loot || klmv.wait || klmv.near_ > 0;
    if (!klmv.any) return;
    if (!klb.on) { klog("move / wait / near: [Bots] Restless, WaitForYou or BoardNear is set but [Bots] Enable is 0: they need klbot.c's crew records, nothing is done"); klmv.any = 0; return; }
    if (klmv.restless || klmv.loot)
        klog("move: on; Restless=%lu s Loot=%lu s (back %lu s, near %.0f) Hold=%lu s Pace=%.0f%s: an AI heister that stands that long without moving 1 m or earning - on a money object that pays nothing: the object is no loot candidate for a while (one byte of it; you can still take it); more than 3 m from the place its chain ordered: that order again (the soldier's own order %08x)%s; Arcade only, on a level that is not the stock one of its slot",
             klmv.restless / 1000, klmv.loot / 1000, klmv.back / 1000, klmv.loot_near, klmv.hold / 1000, klmv.pace, klmv.dry ? " DRY RUN (MoveDry=1: nothing is written or called)" : "", KLE_ORDER,
             klmv.hold ? "; at its own hold place for Hold seconds: a shift round it" : "; a bot at its own place (a meant wait) is left alone");
    if (klmv.wait)
        klog("wait: on; WaitForYou=1 Stage=%d Floor=%lu s Max=%lu s Hold=%.1f s%s: while you are a heister in play under that heist stage no vehicle is called (rules +0x1ee, a byte the exit trigger asks - and the HUD's round clock: it is RED meanwhile); while a vehicle waits and you come, its timer gets up to 5 s more under 2 s, Hold seconds a visit at most; Arcade only, on a level that is not the stock one of its slot",
             klmv.wait_stage, klmv.wait_floor / 1000, klmv.wait_max / 1000, klmv.wait_hold, klmv.dry ? " DRY RUN" : "");
    if (klmv.near_ > 0)
        klog("near: on; BoardNear=%.0f Visits=%d Stage=%d%s: a ZAllyEscapeBox farther than that from the escape vehicle's boarding place takes no AI heister aboard (a private vtable copy on the level's box objects, slot 25); Arcade only, on a level that is not the stock one of its slot. FollowOutHold=%.0f FollowOutSpare=%d%s",
             klmv.near_, klmv.near_visits, klmv.near_stage, klmv.dry ? " DRY RUN" : "", kle.fo_hold, kle.fo_spare,
             kle.fo_hold > 0 || kle.fo_spare ? "" : ": NEITHER IS ON - an AI heister a far box no longer takes is shot by the rules when the vehicle leaves with you aboard");
}

#endif /* KLMOVE_C */
