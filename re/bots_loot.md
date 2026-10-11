# AI heisters held by loot they cannot take: the loot window, the grab, the census, the fix

2026-10-11, agent A (track 'loot trap'), **second pass after the review** (`re/bots_loot_review.md`; what was done
about each of its defects: section 13). **OFFLINE: the game was not started, nothing was written into the Dog Days
folder, nothing was committed.** Changed: `tools/kl_fa_bots.py` only. Builds: `<work>\build\z_loot3\M01 M02 M03 M06`
(logs of every run: `<work>\build\z_loot3\logs\`). Not loaded in the game by anybody.
The first pass's builds are kept in `<work>\build\z_loot3\_v1\` and are **superseded: not to be installed** (they
fail the check as it stands now, section 7).

Words: **read** = disassembled at the address given (kl2.exe, base 0x400000); **measured** = counted on the build
files with the tool; **live** = from the hook's logs of tonight's runs (`<work>\build\klhook\live\`);
**ASSUMPTION** = fits the evidence, not proven; **not read / not established** = said so.

Fields are 0-based positions of a controller's stored list. Members of `ZOnlineMoneyCtrl` and `ZTriggerBox2` are
`property offset + 4` (the property records of both classes carry offsets from the sub-object at +4: measured
against the code, e.g. field 1 = record offset 0x30 = the dword `[object+0x34]` that 0x4536e0 tests).

## 0. Short answers

1. **The window is 800 (3D distance) and 400 (height)**, measured from the bot's node to the object's node, for
   the placed loot; 400 / 200 for dropped stacks. Four code defaults of the tuning object (constructor 0x52ad20:
   `+0xc1c` = 800 at 0x530aa2, `+0xc20` = 400 at 0x530ad8, `+0xc24` = 400, `+0xc28` = 200). No file feeds them.
2. **Every money object that is not taken is a candidate**, whatever its state: byte `+0x6c` is set by the
   controller's init for every type (0x4d8ec4), a shut container's item included; it is cleared only when the
   object is taken (0x4e3f76) or gets `'Deactivate'` (0x4c95e6). So yes: a closed case is a candidate.
3. **By the code, what a bot cannot take stays a candidate for the whole round and the bot's own loot tactic goes
   for it.** The test (0x451920) returns 1.0 while one of the five nearest candidates has a path; the action
   (0x7bc7d0) runs to the nearest one with a path. **Seen live as a hold to the end of the round in two forms
   only:** two bots in front of two shut watch cases that nothing opened (L11), and every living bot at the post
   of the watch shop's clerk (L8, L10). **Not a general law:** in L8 and L10 the bots left the jewel store with
   200,000 untaken inside the window of all their places, in R13 Hot Coffee's waitress (40,000 untaken) held
   nobody, in H0 the bank's two civilians held nobody. What separates the cases is not established (section 3).
   A new Defend order of the route did not move the held bots (live, L10: the loot waits have a deadline of
   15 .. 60 s, the six bots stood 150 s).
4. **The clerk.** Nothing in the grab tests the civilian: by the code a bot inside her trigger takes her 75,000 in
   four parts of 0.7 s. Her money was never paid although six bots stood 9 from her group's origin for two and a
   half minutes. What the code leaves: the take message never reached the controller, or was dropped. Two
   explanations, neither read to the end (section 3): A, the trigger sits where the civilian is and she had left;
   B, her group node was hidden. **No run shows a civilian's money paid to a bot at all** (the first pass said the
   jewel store's clerk was paid; that is not established - review D2, section 3).
5. **Census.** By the rule 'a place inside the window of something the bot cannot take there' the builds on the tab
   have: Hot Coffee 1 object / 7 squads (the waitress), Late Night Opening one stop 3 watch cases nothing opens +
   the jewel store's clerk (+ the stricter 'open before in reach'), two stops the clerks (+ the stricter rule),
   Withdrawal 2 civilians / 7 squads, the park none, Retomoto none. **The census names three squads for the two
   watches of run L11 - Squad#02 (495 / 510), #04 (633 / 640), #06 (409) - and the two bots that stood there are
   crew records 1 and 3**, i.e. Squad#02 and #04 if the records follow the squads' order (ASSUMPTION: the crew log
   does not name the squad).
6. **The fix** (option `window`, in `RECIPE`): (a) every squad's own relays open every case a bot comes near, from
   a timer one station *before* the bots are in reach; (b) the money on a civilian that a place comes near is
   **taken out of the level as stored data**: her group loses its `OnlineMoneyCtrl` and the trigger that fed it.
   No message is involved (the first pass's `'Deactivate'` relay is gone: the handler drops that message for a
   hidden node exactly like the take, review D1). Late Night Opening keeps both stops. `check()` FAILs the old
   builds and passes the new ones; the park's build is byte for byte what it was.
7. **Owed: the owner's word** (section 6): the civilians' money - 215,000 on Late Night Opening, 40,000 on Hot
   Coffee, 30,000 on Withdrawal - is gone for the human too, although only the watch shop's clerk was seen to hold
   anybody; and the jewel store's glass bursts by itself about half a minute after GO.

## 1. The grab, from the trigger to the money

All read.

| step | code | what must hold |
|---|---|---|
| the trigger | `ZTriggerBox2` update 0x626ec0 | every object within the box's reach: a player, or - in Arcade (0x7f6850) - an actor whose `[[actor+0x54]+4] == 2` (team Ally: a bot). With field 3 set ('people only', what `kl_fa.money_people` writes) nothing else. Inside test in radius mode (field 1 set, all money triggers): 0x783e60 - a ball of field 2 + 40 round the trigger node's centre point (entity `+0x30..+0x38`, taken through the parents), against the visitor's centre point. It fires on every tick the visitor is inside (field 6 = 0: no delay), field 5 = the message, field 0 = the targets (the node itself) |
| delivery | 0x697310 -> 0x7592e0 | the target node's own handler (`+0x164`; a ZGROUP's is 0x547000: nothing), then its controllers. Children get nothing |
| the money object | `ZOnlineMoneyCtrl` slot 26, 0x6cdb40 | in this order (re-read in the second pass, 0x6cdb40 .. 0x6cdb93): `'Activate'` is served first (0x6cdb48); then **every other message is dropped when the node is hidden** (entity flags bit 0x400: 0x6cdb65 .. 0x6cdb76 return 1 with nothing done) **or the object's state `+0x64` is 2 or 3** (0x6cdb78 .. 0x6cdb84 return 0); then `'AI_TRIGGER_WITH_ACTIVATOR'` (0x6cdb87) needs the object active (byte `+0x74`, 0x6cdb8f); `'DoorOpened'` and `'Deactivate'` come after that. In Arcade the take goes to rules slot 201 |
| the rules | `ZGameRulesHeist` slot 201, 0x56f6e0 | Arcade (game type 0x19). An actor: alive (`+0x576 != 0`, virtual +0x3d0 = 0x87f870) and with a crew record (0x78f470) -> 0x8e8750. A player: not dead, not in one state -> 0x8e8750 |
| the start | 0x8e8750 | record `+0x15` 0 -> 1 (looting), `+0x1c` = the object, `+0x18` = object `+0x44` (field 5) x tuning `+0x624` (0x4f3e50): the time of ONE part; crew status bit 0x2000 = 'busy looting'. With `+0x15` = 2 and the same object: back to 1 |
| every tick | 0x727cb0 (the record's state machine; its caller was not read) | state 1: stop if the object is taken, if its state `+0x64` is not 1, for a bot if the actor's `+0x576` is not 1, for a player if he is down. Else: object `+0x80` |= this crew member, time -= dt, **state = 2**. State 2 on the next tick = the trigger did not fire again in between: stop, bit 0x2000 cleared, the clock starts anew next time. So the visitor has to STAY in the trigger |
| a part is paid | 0x728007.. | when the time is up: part = min(what is left, object `+0x40` = field 4) -> 0x4e3f40 (does nothing while the object's state is 2 or 3), the crew member's money `[[rules+0x5f8]+0x150+4*i]` += part, the clock is set again. When the object is empty: a DROP stack goes back to its pool (0x57f320), record cleared, bit 0x2000 cleared |

So a grab STARTS when a living bot with a crew record is inside the object's trigger and the object is shown,
active and in state 1; it COMPLETES when the bot stays there for (amount / field 4, rounded up) x field 5 x factor
seconds. An object is left 'not taken' after a bot stood at it when the message is dropped (hidden node, state 2 /
3, **inactive = a shut container's item**) or never sent (the bot is not inside the trigger's ball).

## 2. `OnlineMoneyCtrl`: the twelve stored fields, the three types, the container

Property records at 0xd0ae94 (read with `props.py`); meanings from the code that reads the member.

| # | member | kind | meaning | read at |
|---|---|---|---|---|
| 0 | +0x30 | enum EZMoneyCtrlGameMode (ALL, FA_ONLY, UCC_ONLY, TM_ONLY) | only `== TM_ONLY` with type DROP is tested (0x4d8f6e). No gate for Arcade: every object registers | 0x4d8e80 |
| 1 | +0x34 | int | the amount LEFT. 'taken' = `<= 0` | 0x4536e0, 0x4e3f52 |
| 2 | +0x38 | enum EZMoneyCtrlType NORMAL 0, DROP 1, CONTAINER 2 | below | 0x4d8e96, 0x4fb5c7 |
| 3 | +0x3c | enum EZMoneyCtrlVariant NORMAL, SMALL, LARGE | not read (the list-two entry takes its low byte, 0x7eb8fb) | - |
| 4 | +0x40 | int (20000) | the size of ONE part of a grab | 0x72806d |
| 5 | +0x44 | float (0.5, 0.7; F07 0.15) | seconds per part, x tuning `+0x624` | 0x8e87b3, 0x728051 |
| 6 | +0x48 | byte | hide the node when the object is gone (0x4bf120). Init sets it for DROP and CONTAINER itself | 0x4c95e2, 0x4e3f72 |
| 7 | +0x4c | float (45, 100; default 30) | } three floats of the HUD marker the controller makes for itself (0x571b40 -> 0x60f860). | 0x571bb0 |
| 8 | +0x50 | float (700; F07 2800) | } ASSUMPTION: its height above the node and the two distances | |
| 9 | +0x54 | float (950; F07 3000) | } between which it fades | |
| 10 | +0x58 | int (0; stock DROP 100) | money the object loses by itself per second while it lies active | 0x5f1d67 |
| 11 | +0x5c | byte (0; stock F01's 58 vault items 1) | **'behind a door' for the AI**: the loot tactic's test passes the object over unless an enabled `KickDoor` controller is within 500 / 250 of it (0x451a88 -> 0x454c20; registry gamedata+0xaa4, filled by `ZKickDoorController` slot 13 0x7eb880); the message `'DoorOpened'` clears it (0x6cdc0e). The grab never reads it | section 4 |

Not stored: `+0x64` state (0 new -> 1 by the first update 0x5f1ef7; 2 = 'appearing', 3 s (0x4fb5de); 3 = gone),
`+0x6c` 'in play', `+0x74` active, `+0x80` who is looting it.

- **NORMAL**: registered on the rules' list one (init 0x4d8f3a -> rules `+0x144` = 0x4c1dc0, which also adds field 1
  to the level's total and keeps the one richest object for the 'first loot' line). Active from the start.
  **The registration is the controller's own init: a node without the controller is no money object.**
- **CONTAINER**: the same list, but init clears `+0x74` (0x4d8ea6). It becomes active when an
  `OnlineMoneyContainer` that names it gets `'Open'` (0x419f80 -> 0x766e50 -> after the container's countdown
  0x868fb0 -> 0x4fb580(1): `+0x74` = 1, state 1 at once for this type). Dead Men's jewel and watch cases get `'Open'`
  only from their glass (`HavokShatterGlass` + `RelayMessage` 'HavokShattered' -> 'Open'; `'Activate'` on the glass
  shatters it as a bullet does, 0x8d1b60): re/bots.md 12.1. **A CONTAINER object no container names is never
  active** (Withdrawal's ten `Money!ContainerMoney!Box_Money_nn`, parked with the drop pool).
- **DROP**: list two (rules `+0x13c` = 0x7eb8e0), an entry with a flag byte; `+0x140` (0x57f320) sets the flag
  when the stack is back in the pool, and 0x8b96fc passes flagged entries over.
- Messages the class knows (slot 26): `'Activate'` (0x4fb580 with its own `+0x74`), `'AI_TRIGGER_WITH_ACTIVATOR'`
  (the take), `'DoorOpened'` (clears field 11), `'Deactivate'` (0x4c95d0: `+0x6c` = 0, state 3, marker removed -
  the host's branch, and in Arcade the host test 0x8df480 holds whenever the Arcade test 0x7f6850 does: same
  two tables). All but `'Activate'` are behind the hidden-node and state tests (section 1).

## 3. Why the clerk held the bots - what is known, what is not

Measured (`<work>\build\z_route\M02`): `Civilians!Civ_male_watch\female_clerk` is a ZGROUP at (-1769, 503, 2801)
with `OnlineMoneyCtrl` {ALL, 75000, NORMAL, SMALL, 20000, 0.7, 0, 100, 700, 950, 0, 0}, `TriggerBox2` {itself, 1,
75.0, 1, 0, 'AI_TRIGGER_WITH_ACTIVATOR', 0}, an `OnlineSpeakTrigger` {1, 800.0, .., 'eZOST_SPEAKER_DRIVER', a
civilian's panic line, .., 20}, and the child `Ground` (ZFFActor, `ZCivilian`). Nothing but its own trigger names
the group. Stop 1's `Civ_male_jewel\male_clerk` (100,000) has the same form; stock F07 has five such objects on
rival mercs (`...HeistGuys_0n\Guard_01`: the same trigger {.., 1, 75.0, 0, ..}), so 'money on a person's group' is
a stock form - on ARMED people; no stock level has money on a civilian. Squad#03's loot place of stop 2 was 3 from
her origin (the old plan put each bot 'beside its loot object').

Live (L8, L10; `money.py` of the review, re-run in the second pass):

| run | the jewel store (the old stop's 21 objects: 19 in glass cases 1,600,000, the drawer 100,000, the clerk 100,000) | the watch shop |
|---|---|---|
| L8 | 1,600,000 by 02:44:12. One object paid in 20,000 parts: bot 3 alone, +20,000 +40,000 +40,000 | +460,000; then every living bot at (-1772, 500, 2792) to the end; exactly 75,000 left |
| L10 | 1,600,000 by 03:02:21. 03:02:13.2: bots 1, 2, 3, 6 +20,000 each in ONE log tick, 03:02:14.3 bot 1 +20,000 | +460,000; six bots at the same point from 03:03:45 to the end; exactly 75,000 left |
| L11 (one stop) | 1,700,000 by 03:13:53. Bot 4 alone in 20,000 / 40,000 parts | not a stop; two bots at two shut cases |

The jewel store has TWO objects of 100,000 that pay 20,000 a part within the bots' reach (measured): the clerk
(0.7 s a part, trigger 75) and the self-opening `PC0406_M02_FA_Cashdrawer_01\Money_Attachroot` at (1318, 575, 2589)
(0.5 s, trigger 125). In each of the three runs exactly ONE such object was paid. Four bots getting their first
part in the same tick (L10) is what a container looks like that becomes active under bots already standing in its
trigger; a clerk who can be taken from the start would be paid to each bot as it arrives. **So that the jewel
store's clerk was paid is NOT established (the drawer fits better), and no run shows a bot taking a civilian's
money.** The first pass's sentence 'four bots took the male clerk's 100,000' is withdrawn, and with it the timing
argument for assumption A ('the male clerk was reached 85 s after GO, the female one 155 s').

The same sums say: in L8 and L10 the bots LEFT the jewel store with 200,000 untaken inside the window of all their
places - 100,000 of jewels in cases the relays had opened, and the clerk or the drawer. In L11 100,000 stayed (the
clerk or the drawer). So an untaken candidate in the window does not always hold a bot. Seen to hold: a case
nothing opens (L11, two bots while the van came three times) and the watch shop's clerk (twice of twice, every
living bot). Not seen to hold: the jewel store's leftovers (three runs), Hot Coffee's waitress (R13: 40,000
untaken, all seven squads' places 82 .. 374 from her post), the Senator's 1,250,000 (R13, a place 3 from his post),
the park's bosses (R12), the bank's two civilians (H0). **Why: not established.** Hot Coffee, the park and the
jewel store have a gunfight or other loot going while the bots are there and the watch shop at the end has
neither; the tactic's first test is 'at least 4.0 s (tuning `+0xc34`) since the time stamp `[[actor+0x54]+0x30]`'
(0x451935..0x451968) - what that stamp is was not read (ASSUMPTION: the last contact with an enemy).

Read against the clerk (section 1): the trigger takes a bot (0x626f9b), it does not look at the civilian, the rules
do not look at her, there is no 'only when dead' anywhere on the path. So at the watch shop the message was not
sent or was dropped:

- **Explanation A - the money is where the clerk is.** The inside test uses the group entity's `+0x30` point
  (0x783e6c), not its origin; the loot tactic takes the origin (0x8d3150 = the zero point through the parents). If a
  group's centre follows the actor below it, the money is at the clerk's feet wherever she is, and the bots stand
  at her post. That a group's centre follows its child was NOT read.
- **Explanation B - the node was hidden** (0x6cdb65 drops the message): if the game hides the group when its
  civilian has got away (the map has `CivilFleePoints!`). Not read either.

**The fix must not depend on which of the two it is - and the first pass's fix did** (review D1): a `'Deactivate'`
message is behind the same hidden-node test as the take (section 1), so under B it is dropped whenever it arrives
after the group was hidden, and byte `+0x6c` stays set. That is why the second pass takes the controller off the
node in the level file (section 6): an object that is never registered cannot be a candidate under A, under B, or
under anything else.

What a level builder can say: **money on a civilian was never seen paid to a bot, stays a candidate at her post,
and once held every bot there.** How the human gets it (by standing at her - under A wherever he catches her) was
not tried by anybody tonight.

## 4. The window, the test, the action

`ZGameRulesHeist` slot 202, 0x8b94d0(position of the bot's node, out[5]) - read line by line:

- list one (`rules+0xdcc`, count `+0xdc0`): skip a null entry, a taken object (0x8b95cf), one with byte `+0x6c`
  clear (0x8b95f2); object position = its node's origin (0x8d3150); `|dy| <= tuning+0xc20` (0x8b9641: the second
  component, the one the levels call y) and `dx2 + dy2 + dz2 <= (tuning+0xc1c)2` (0x8b9678);
- list two (`rules+0xdb8`, count `+0xdac`, 8-byte entries): skip a flagged entry (0x8b96fc) and a taken object;
  `|dy| <= +0xc28`, distance `<= +0xc24`;
- the survivors are sorted by squared distance (0x7bbe80 / 0x7b29a0), the first five returned.

| float | default | where set | what |
|---|---|---|---|
| tuning `+0xc1c` | 800.0 | 0x530aa2 | list one: 3D distance |
| `+0xc20` | 400.0 | 0x530ad8 | list one: height |
| `+0xc24` | 400.0 | 0x530b0e | list two: 3D distance |
| `+0xc28` | 200.0 | 0x530b44 | list two: height |
| `+0xc2c` / `+0xc30` | 500.0 / 250.0 | 0x530b7a / 0x530bb0 | a KickDoor's reach for an object with field 11 (0x454c35) |
| `+0xc34` | 4.0 | 0x530be6 | seconds since the stamp of the tactic's first test |

The tuning object is `[0x168d7c0]`; 0x52ad20 makes 786 variable objects, each writes its default, and frees them
(loop 0x530c20) - there is no level or settings file behind it. Its other writer is a copy (0x776270; the review
did not follow the one vtable slot that names it: 'no file feeds them' is plausible, not proven). So an Arcade
round has the defaults (KLHook could write them: four floats).

`ZLootTactic` slot 11, 0x451920 (the test), in order: the 4 s stamp; Arcade rules; the bot's crew record with stage
`+0x78 >= 1`; not (stage 3 and vehicle state 3 / 4); the five candidates; **if the crew status has bit 0x2000 (a
grab is running) return 1.0**; then for each candidate: with field 11 set, 0x454c20 looks for a KickDoor (found ->
1.0 with the door in `this+0x28` and the index in `+0x2c`); else a path from the bot's node to the object's node
(the pathfinder `[[0xdd2640]+0xac]+0xc`: virtual +0x7c for each end, +0x60 for the search) and **1.0 when the
result's node count `[ebp-0xb0]` is more than 1**. Else 0.0. ASSUMPTION: a found path counts its two ends, so 'more
than one node' means 'a path exists' - the bots of L8 / L10 / L11 stood AT the path's end and the test kept passing.
An object on a mesh part the bot's is not joined to has no path and is dropped (Late Night Opening's two office
jewels, 250,000: their triggers are reached from a part of 24 polygons only; the bots left the jewel store in
three runs with them untaken).

**The stage.** `+0x78` is raised by the stage boxes (0x5dd890, which only raises): 1 in an ENTERS_BANK box, 2 in an
EXITS_BANK box, 3 in a BOARDS box or a level exit box. The test wants `>= 1`, so a bot that walks through an EXITS
or exit box first has the tactic too; and the body gets the stage on the LEG that crosses a box, not at the first
route place that lies in one (review D3; section 7).

Slot 2, 0x7bc7d0 (the action): nothing while bit 0x2000 is set; else from index `this+0x2c` - which only the
door branch ever writes, so 0 on a map without a KickDoor - the FIRST candidate with a path: run to the path's end
(0x8997a0). With a path count of 1 or less it waits 0.5 .. 0.6 s (0x7bc9be..0x7bca0c, read by the review) and
tries the next candidate; none -> flag 8 of `actor+0x57d`. **It does not test field 11.**

**Does a Defend order beat it?** Not read: the tactic returns 1.0 / 0.0 and stands in three of the soldier script's
tactic lists (built at 0x6ab250; appended at 0x6abea8, 0x6ac29f, 0x6ac4d8), but which list is used when and where
the Defend goal's tactic stands in them was not followed. Live: at the watch shop no (L10's loot waits end after
15 .. 60 s at the latest, 0x811fb0, and the six bots stood 150 s and more with the next steps issued); at the
jewel store the bots did go on with untaken candidates in reach (section 3). So: sometimes, and what decides it
is not established.

## 5. Census (`python tools\kl_fa_bots.py census <folder> ...`; full text: `z_loot3\logs\census_tab.txt`, `census_new.txt`)

'Trap' = an object inside the window of a place (any branch, any hold of kl_fa_bots_dyn) that the bot has reached
with a heist stage, which it cannot take at that time. Distances: object to the nearest such place. Counted with
the check as it stands after the review (the stage begins on the leg that crosses a stage box).

| build on the tab | money objects (list one) | traps by the rule |
|---|---|---|
| Hot Coffee `z_route3\M01` | 4 on armed people 1,790,000; 1 in the register (opens itself) 100,000; 1 on a civilian | `Fat_Waitress_01` 40,000: all seven squads, 82 .. 374. **Held nobody in R13** |
| Late Night Opening, one stop `z_m02s1\M02` | 38 in cases (3 open themselves, 35 behind glass), 3 on civilians, 3 plain | watches `M6_01`, `M5_01` (**nothing opens them: the hold of L11**): Squad#02 495 / 510, #04 633 / 640, #06 409 - L11's two held bots are crew records 1 and 3 (= #02 and #04 if records follow the squads); `L2_01`: #02 698, #04 736, #06 468; `male_clerk`: all seven, 160 .. 544 (held nobody in L11); `Clerk_Female` (cafe): #07 672; + the jewel store's own cases under the stricter rule below |
| Late Night Opening, two stops `z_route\M02` | the same | **`female_clerk` 75,000: all seven, 3 .. 500 (the hold of L8 / L10)**; `male_clerk`: all seven, 160 .. 544 (held nobody); `Clerk_Female`: #07 672; + every case of both stores under the stricter rule (142 .. 303 at the place in front of the timer) |
| Withdrawal `z_hop\M03` | 12 in containers that open themselves 2,400,000; 2 on civilians; 10 CONTAINER objects nothing names (never active, parked 4,400 .. 5,300 from every place) | `Civilian_in_Bank_01` 20,000: six squads at a place, 184 .. 771, the seventh (#05) 566 on its way; `Clerk_Female` 10,000: all seven, 90 .. 637. **Held nobody in H0** |
| the park `z_route\M06` | 4 on armed people 3,350,000 | none |
| Retomoto `rt_full7\retomoto_full` | 21 plain 4,050,000 | none by the rule. One table stack, `TM_MoneyStack_022` (300,000) at (5000, 21070, -223): no point of the bots' mesh part is inside its trigger (radius 125 + 40, `trigger_reach`: this module's estimate of the ball of 0x783e60); a two-polygon islet of the mesh at the table is. Squad#04 has a place 267 from it. NOT established which part the pathfinder takes the stack to: with a path from the bots' part and the trigger out of reach it would be a candidate nobody on that part can take. `check()` says so in a NOTE now (review D4). For the Retomoto session: do the bots' logs show them leaving the boardroom with that stack untaken |

- 'Takeable from the start': plain objects and money on armed people (where the person is). 'After a message':
  a case - `'Open'` to its container; in the old builds sent by three squads' relays per case at the store's door,
  in the one-stop build by nobody for the watch shop. 'Never': the ten parked CONTAINER objects of Withdrawal.
- Was it luck that Hot Coffee, Withdrawal and the park ran clean (R12 / R13 / H0)? The park: no - it has nothing a
  bot cannot take but money on armed people, which held nobody. Hot Coffee and Withdrawal: by the rule they have
  the clerk's pattern, and they ran clean. Why they were not held is not established (section 3); so: not shown
  to be safe, not shown to be a trap. The new builds take the question away at the price of the civilians' money.
- The old two-stop form opened a store's cases from a timer AFTER the place in front of the store, and both
  stores were looted in L8 / L10 - that part of the FAIL on `z_route\M02` is the STRICTER rule of the check
  ('opened before the bot is in reach'), not a trap that was seen. The check's FAIL text says which of the two a
  line is (review D9).

## 6. The fix (`tools/kl_fa_bots.py`, option `window`; in `RECIPE` for all four maps, `--no-window` takes it off)

1. **Cases.** Every squad's relays name EVERY case (a container only its glass opens) that any bot's place comes
   within `LOOT_WINDOW + CASE_GUARD` = 800 + 1150 of - not the three nearest bots' cases - and the timer that fires
   them follows the last station that is still farther than that from all of them. A case met first on the way
   out belongs to the last stop's timer, one met at a leg's first station to the stop before. Relay lists hold at
   most 10 targets (`RELAY_MAX`: stock F01's largest), longer ones are split (`018_Relay_open_cases`, `..._b`).
   The forms are the ones the stops already had (`TriggerDelay2` 1 s -> `RelayMessageList` 'AITrigger' ->
   'Activate' / 'Open'). All of it is the squads' own nodes.
2. **Money on a civilian** that a place comes within the same 800 + 1150 of is **taken out of the level**
   (`strip_money`, called by `build()` after the plan): the civilian's GROUP node loses its `OnlineMoneyCtrl` and
   the `TriggerBox2` that sends `'AI_TRIGGER_WITH_ACTIVATOR'` to the node itself. Nothing else changes: the node,
   its place and flags, its `OnlineSpeakTrigger` (her panic line), the civilian below it; no entity is added or
   removed; only the `.prp` member knows (the `.gms` record is as it was). The money is also no loot of the route
   (no loot wait names it, no bot gets its place beside it).
   - Why this is safe to load (measured, `civ.py` / `flags.py` in `<work>\research\agent_scripts\a-loot\pass2\`,
     output in `z_loot3\logs\civ_M0n.txt`, `flags.txt`): what is left - a ZGROUP with an `OnlineSpeakTrigger` and a
     `ZCivilian`'s actor below it - is the form of civilians these maps already run: Hot Coffee's `LeavingWoman`
     and `LeavingMan`, Withdrawal's `Civ_out_03`, `Civ_in_02`, `Civ_in_01`. The only reference to each group was
     its own trigger's. The `.gms` flag bit 0x200000, which nodes named by a reference carry, stays set on the
     group: 289 nodes of the bank and 283 of stock F07 carry it without being named. A controller taken off a node
     of a finished build has run live before: the tab's Hot Coffee (`z_route3\M01` = `z_gate\M01` + the dynamic
     step) has its `DistanceRumbleCam` off through `kl_fix_lean` (runs G_DM01 / H_DM01, CLAUDE.md 2026-10-11 02:35).
   - `diff` allows exactly this edit and nothing else: 'only the squad was added, the money controller taken off
     n civilian(s)'. Proved to bite (`difftest.py`, `z_loot3\logs\difftest_M02.txt`): the group also without its
     speak trigger, the civilian without a controller, the edit not declared in bots.json - each is UNEXPECTED.
3. `CASE_GUARD` 1150 = kl_fa_bots_dyn's `REACH` 900 + `RING` 230: that step puts a hold up to that far from a route
   place and BEFORE the timer that follows the place. The first build of the first pass (guard 600) failed its own
   check after the dynamic step: four squads held 163 .. 230 from a shut case, inside the ENTERS_BANK box. It is
   an option now (`--case-guard N`): section 9.

Late Night Opening (`z_loot3\M02`), per squad:

| timer | after station | opens |
|---|---|---|
| `018_Timer_at_cases` | 2, in the upper mall, about (2565, 1000, -213): 2,037 from the nearest object | 15 cases (the jewel store's 11 and the 4 watch cases on its side of the mall) |
| `038_Timer_at_cases` | 9, the first one on the way from the jewel store, about (616, 500, 2521): 2,010 away | the other 8 watch cases |

and taken out of the level: `male_clerk` 100,000 (first within 1,950 at station 3), `female_clerk` 75,000
(station 10), the cafe's `Clerk_Female` 40,000 (station 16).

Both stops stay (`RECIPE['M02_FA_A']` keeps `stops` at `STOP_MAX`): stop 1 the jewel store, 20 objects, 1,700,000;
stop 2 the watch shop, 17 objects, 460,000. Hot Coffee: no relay at all; the waitress's 40,000 out. Withdrawal: no
relay; the two civilians' 30,000 out. The park: nothing - its archive and the 19 files beside it have the CRCs
of the bots build under the tab's (`z_final\M06`), and its dynamic build those of `z_route\M06`.

### What the human sees change - THE OWNER'S DECISION (review D6)

- **The glass.** On Late Night Opening the jewel store's glass and four watch cases burst by themselves when the
  first bot is in the upper mall - by L10's times about 20 .. 30 s after GO and 20 s before a bot is at the door
  (estimate, not measured) - and the rest of the watch shop when the first bot leaves the jewel store. He no
  longer shoots those cases himself unless he is there first. The early time is not the window's doing but the
  guard's (section 9): with track B's change the glass could go at the last station before each store.
- **The civilians' money is not in the level any more**: no '$' on the three clerks of Late Night Opening
  (215,000), on Hot Coffee's waitress (40,000), on Withdrawal's two bank civilians (30,000), from the start of the
  round. Nobody gets it.
- **What this buys, honestly:** only the watch shop's clerk (75,000) was seen to hold anybody. The jewel store's
  clerk, the waitress and the bank's two held nobody in the runs there are; they are taken out because the
  code gives no reason why they could not, and the check cannot tell them apart.
- **So the choice per map is:** Late Night Opening - `z_loot3\M02` (needed: the tab's builds hold the bots at the
  clerk or at the watches). Hot Coffee and Withdrawal - `z_loot3\M01` / `M03` (pass the check, 40,000 / 30,000
  less for the human, an edit that has never run) **or keep the tab's `z_route3\M01` / `z_hop\M03`** (ran clean
  in R13 / H0, fail the check's civilian rule by design). Suggested order: M02 first; M01 / M03 once M02 has shown
  that the edit loads and plays. If the owner wants a civilian's money back on a map where no hold was seen, that
  needs a named waiver in `check()` - a decision for the lead, not made here.

Not chosen, and why:

- **A `'Deactivate'` relay to the civilian's money** (the first pass's form): dropped for a hidden node and for
  state 2 / 3 like the take itself (0x6cdb65 .. 0x6cdb84), never sent to a money object by a stock level, and it
  only acted at a timer. `check()` does not accept such a relay (the rule of before the first pass again).
- **Field 11 on the clerk** (the stored property that exists: section 2). The test then passes her over, the
  human keeps her money. But the action does not read the field: while any other candidate in the window passes the
  test, a bot whose NEAREST candidate is the clerk's post runs to it and stands - and in a small shop that can be
  every bot that is left, with a watch untaken behind them. It narrows the trap, it does not close it.
- **Field 1 = 0** ('taken' from the start): the controller's update divides by the start amount for its marker
  (0x5f1e19: 0 / 0). Not tried.
- **Moving the route out of her window**: the watch shop is 8 m across, she stands in it.
- **Making a bot shoot the glass**: no AI code shoots at an object (re/bots.md 12.1).

## 7. The check (`kl_fa_bots.check`, so also `kl_fa_bots_dyn.py check`)

In the walk of every squad and every branch set: from where the bot first has a heist stage on, each place - and
each hold beside the chain, a `DefendBehaviourRout` without a NEXT that the step names directly, through a
`RandomTrigger` or behind kl_fa_bots_dyn's gap timer - is held against every object of list one with what THIS
squad's relays had opened by then. **FAIL** when the place is inside 800 / 400 of: an object in a case not opened
before it, money on a civilian that is still in the level, a CONTAINER object nothing names. An object with field
11 and no KickDoor near it is no candidate.

After the review:

- **Where the stage begins** (D3): the place the bot is walking to when the stand-in path (the module's mesh path,
  sampled every 20, feet or chest) is first inside ANY stage box - ENTERS_BANK, EXITS_BANK, BOARDS, a level exit -
  or a hold beside the chain that lies in such a box or is reached through one. Not 'the first place inside an
  ENTERS box'. On `z_loot3\M02` that is one or two places earlier for five squads (#02: place 9, not 11); nothing
  is in reach there. `facts['loot_window']['first_stage']` has it per squad.
- **The FAIL text says what is known** (D9): 'SEEN' for a case nothing opens (L11); 'THE STRICTER RULE' for a case
  that a relay opens too late; for a civilian that one of them held the bots and the others did not.
- **NOTE - on the way** (D4): the same test on the stand-in path between the staged places, every 40. A NOTE, not
  a FAIL: a bot was seen held where it stood; whether one in transit is pulled off its way is not established.
- **NOTE - a plain object nobody on the bots' mesh part can stand in the trigger of** (D4): Late Night Opening's
  two office jewels (held nobody in three runs), Retomoto's `TM_MoneyStack_022` (not established).
- **NOTE - the money the build took out of the level**, with the sum, in every check of such a build.
- **The relay rule is the one of before the first pass again** (D8): `'Activate'` to glass, `'Open'` to
  containers, anything else FAILs - `'Deactivate'` to a money object too.

| folder | `kl_fa_bots_dyn.py check` (last lines) | what fails |
|---|---|---|
| `z_route\M02` (two stops, the tab) | FAIL (14 FAIL, 4 NOTE) / dyn FAIL (14 FAIL, 6 NOTE) | per squad the clerks (the hold of L8 / L10 among them) and the cases opened too late; nothing else |
| `z_m02s1\M02` (one stop) | FAIL (17 FAIL, 4 NOTE) / dyn FAIL (17 FAIL, 4 NOTE) | per squad the jewel store's clerk and its cases; for #02, #04, #06 the watch cases nothing opens (the hold of L11); nothing else |
| `z_route3\M01` | FAIL (7 FAIL, 2 NOTE) / dyn FAIL (7 FAIL, 2 NOTE) | the waitress |
| `z_hop\M03` | FAIL (7 FAIL, 3 NOTE) / dyn FAIL (7 FAIL, 3 NOTE) | the two civilians |
| `z_route\M06` | PASS (0 FAIL, 2 NOTE) / dyn PASS (0 FAIL, 3 NOTE) | - |
| `rt_full7\retomoto_full` (`kl_fa_bots.py check`, read only) | PASS (0 FAIL, 10 NOTE) | - (one NOTE more than before: the table stack) |
| `z_loot3\_v1\M01` `M02` `M03` (the first pass, superseded) | FAIL (14 / 21 / 14 FAIL) | the `'Deactivate'` relays (14 / 28 / 14 lines of both checks) and the civilians they were meant for |
| `z_loot3\M01` `M02` `M03` `M06` | PASS (0 FAIL; 3, 4, 3, 2 NOTE) / dyn PASS (0 FAIL; 2, 4, 3, 3 NOTE) | closest shut object to any staged place: nothing / 1,344 / 4,379 (the parked boxes) / nothing |

A build of Late Night Opening made with `--no-window` has the archive of `z_final\M02` byte for byte (51 members
and files, 0 differ) and fails with 14 (`z_loot3\logs\z_loot3_M02_nowindow.log`, `neg_summary.log`).

## 8. The builds

    python tools\kl_fa_bots.py owner <work>\build\z_gate\_van  <work>\build\z_loot3\_bots M01
    python tools\kl_fix_lean.py apply <work>\build\z_loot3\_bots\M01 <work>\build\z_loot3\_pre\M01 --ctrl DistanceRumbleCam
    python tools\kl_fa_bots.py owner <work>\build\z_final\_van <work>\build\z_loot3\_bots M02
    python tools\kl_fa_bots.py owner <work>\build\z_final\_van <work>\build\z_loot3\_bots M03
    python tools\kl_fa_bots.py owner <work>\build\t_maps2      <work>\build\z_loot3\_bots M06
    python tools\kl_fa_bots_dyn.py build <work>\build\z_loot3\_pre\M01  <work>\build\z_loot3\M01
    python tools\kl_fa_bots_dyn.py build <work>\build\z_loot3\_bots\M0x <work>\build\z_loot3\M0x     (M02 M03 M06)

(`chain.sh` in `<work>\research\agent_scripts\a-loot\pass2\` runs one map's chain with every check;
`z_loot3\logs\chain_M0n.log` has the times and the tools' sha1.) Tools at the build: `kl_fa_bots.py` sha1
59183dc42505; **`kl_fa_bots_dyn.py` aa7f65f8d592 - track B's uncommitted file, edited four times while this pass
ran** (05:47, 05:51, 06:13, 06:31). It was not edited here. The whole chain was run three times, at 06:08, 06:14
and 06:32, with three states of that file (7613e7602a74, 12fdbedb87f5, aa7f65f8d592) and with this module changed
only in its check and log texts in between: the four archives and the four bots builds came out byte for byte the
same each time (`neg_summary.log`: 0 members differ against the round before). The delivered folders are the
third round's: review D11.

| | M01 | M02 | M03 | M06 |
|---|---|---|---|---|
| archive sha1 (first 12) | 0a0ad56244ad | a004c014c5ce | 5f014f12ee6c | 1d799830eeee (= `z_route\M06`) |
| bots build sha1 | 7015a575e366 (+ lean: 1557f16ed7a8) | 6c97733e2420 | 6d8565e7467a | 042c10e62cf5 (= `z_final\M06`) |
| `kl_fa_bots.py check` on the bots build | PASS (0 FAIL, 3 NOTE) | PASS (0 FAIL, 4 NOTE) | PASS (0 FAIL, 3 NOTE) | PASS (0 FAIL, 2 NOTE) |
| `kl_fa_bots.py diff <source> <bots build>` | only the squad was added, 2 level exit boxes cut (x and first size), the money controller taken off 1 civilian(s) | only the squad was added, the money controller taken off 3 civilian(s) | only the squad was added, 1 drop link(s) in the navigation mesh, the money controller taken off 2 civilian(s) | only the squad was added |
| `kl_fix_lean` | DistanceRumbleCam controller taken off 1 objects, 0 kept; only the .prp member differs | - | - | - |
| `kl_fa_bots_dyn.py build`: its diff | only the squad's steps were made anew | same | same | same |
| `kl_fa_bots_dyn.py check` | PASS (0 FAIL, 3 NOTE) / (kl_fa_bots_dyn): PASS (0 FAIL, 2 NOTE) | PASS (0 FAIL, 4 NOTE) / PASS (0 FAIL, 4 NOTE) | PASS (0 FAIL, 3 NOTE) / PASS (0 FAIL, 3 NOTE) | PASS (0 FAIL, 2 NOTE) / PASS (0 FAIL, 3 NOTE) |
| `kl_impact.py` | problems: 0 in 1 levels | same | same | same |
| `kl_maps.py audit` | PASS (0 findings that must be 0, 1 known and accepted) | PASS (.. 6 known ..) | PASS (.. 0 known ..) | PASS (.. 6 known ..) |
| `kl_map_guns.py check` | 6 guns with looks ...; problems: 0 | same | same | same |
| `kl_map_escape.py van-check` | 0 fault(s) | 0 fault(s) | 0 fault(s) | (helicopter) |
| squad nodes (bots build -> dynamic) | 170 -> 697 | 310 -> 1,246 | 199 -> 754 | 205 -> 828 |
| relays of the squads | none | 21 'Activate', 21 'Open'; 23 panes, 23 containers; at most 10 targets a list; 0 faulty references | none | none |
| money taken out of the level | `Fat_Waitress_01` 40,000 | `female_clerk` 75,000, `Clerk_Female` 40,000, `male_clerk` 100,000 | `Civilian_in_Bank_01` 20,000, `Clerk_Female` 10,000 | - |
| `.prm` / `.ANM` / `.fxc` / `.WAV` | 56,992,176 / 22,039,292 / 17,760,648 / 21,145,936 | 56,522,544 / 22,180,036 / 17,760,648 / 22,113,616 | 62,581,504 / 22,202,616 / 17,760,648 / 22,669,648 | 50,415,712 / 21,642,576 / 17,760,648 / 21,775,744 |

The four large blocks are the sizes of the builds on the tab (`z_route3\M01`, `z_route\M02`, `z_hop\M03`,
`z_route\M06`): none grew. `z_loot3\M03\KLJoin.ini` is `z_hop\M03`'s byte for byte (its `[CrewHop]`).
Against the tab's builds (`neg_summary.log`): M06 0 of 51 members and files differ; M03 only the `.prp` member (the
squads' loot lists without the two civilians, the two groups without their controllers - the entity table and
every place are the tab's); M01 and M02 `.prp .gms .buf .oct .prm` (the squad: other loot places, on M02 the
timers and relays).

## 9. For track B (`tools/kl_fa_bots_dyn.py`) - nothing is needed for these builds; this would let the cases open later

The dynamic step emits, for a route place P that is followed by one of the bots build's timers,
`rout(.. P) -> [pos_cover hold -> Timer_hold] -> <the kept timer>`: the hold (up to REACH 900 + RING 230 from P)
is walked BEFORE the kept timer's relays fire. A cases timer therefore has to stand 1,150 farther out than its
window needs, which is why the jewel store's glass goes while the bots are still in the upper mall. If a kept
timer that names relays (`e['cases']`, parse()) were emitted directly after its rout and the hold after the timer -
or if no hold were made for a rout that such a timer follows - the bots build could be made with
`python tools\kl_fa_bots.py owner ... --case-guard 300` and the cases would open at the last station before each
store. `kl_fa_bots.check` says at once when a hold is inside a window too early; nothing else has to change.

## 10. Live checks for the lead (the owner away; none of this has run)

TEST hook, `[Bots] Enable=1 Log=1`, the player idle. For the position lines run with the lead's
`now\live.py --poslog` (a TEST-ONLY `KLJoin.ini` with a `[CrewHop]` nobody can stand at - `From=0 9000 0`, `Radius=50`,
`Height=50`, `Wait=6`, `Stage=1`, `Player=0`, `Places=2`, `To.1=0 9000 500`, `To.2=0 9000 900` - and
`[CrewHop] Enable=1 Dry=1 Log=2` in the hook's ini; removed afterwards). `z_loot3\M02` has no KLJoin.ini of its
own, so without that no `hop:` line exists whatever the bots do (review D5).

**W1 - Late Night Opening, `z_loot3\M02`.** One clean run is fair evidence (the hold came twice of twice, for every
living bot); two are better.

- SUCCESS, all of: `bots: record n (bot): heist stage 0 -> 1` for every living bot; the bots' money rising at the
  jewel store to about 1,600,000 .. 1,700,000 in steps of 50,000 and more with one object in 20,000 steps (L8 /
  L10 / L11), then in 20,000 / 5,000 / 10,000 steps at the watch shop by about +460,000; then `heist stage 1 -> 2`,
  `-> 3`, van state 3, `aboard` / `status6`; **no living bot `in-play g1` at the end of the round**; no run of
  `hop: bot n stage s: node (x, y, z)` lines with one node for several bots over minutes.
- The bots' total is at most 2,320,000: the level holds 2,570,000 now (41 objects), 250,000 of it the two office
  jewels no bot reaches; the credit card (100,000) and the cafe's drawer (60,000) off the route count as healthy.
  Nothing of the three clerks can show: their 215,000 are not in the level.
- FAILURE A: bots again on (-1772, 500, 2792) with the watch shop empty = it was not her money object that held
  them (it does not exist in this build): the theory of section 0.3 is wrong there; send the log.
- FAILURE B: bots on one point somewhere else = an object the rule does not know. `python tools\kl_fa_bots.py
  census <folder>` for the object nearest to that node; the 'plain, out of reach' lines first.
- FAILURE C: a load fault or an assert at the level's start that the tab's M02 does not have = the edit of the
  three civilians' groups (the only change outside the squads): try `z_loot3\M06` (no such edit) and the tab's M02
  to tell them apart.

**W2 - a look, not a criterion** (the human at the keys): the jewel store's glass bursts by itself while the first
bots are still in the upper mall; the jewels can be picked up shortly after; no '$' on any clerk. If the glass
stands but the jewels can be taken, 'Activate' did nothing from that far and 'Open' did: the build still works.

**W3 - `z_loot3\M01`, `z_loot3\M03`** (only if the owner wants them, section 6): as R13 / H0 - the bots loot and
leave, van / hop as before; no '$' on the waitress / the bank's two civilians.

**W4 - `z_loot3\M06`**: nothing new, it is the tab's build byte for byte.

**Why the clerk held them** (one run with a human, on the TAB's `z_route\M02` or `z_m02s1\M02`, where she still has
her money): stand at `female_clerk` (-1769, 503, 2801) in the first minute - is the '$' there, is her 75,000 paid at
her post, does the '$' follow her when she runs, is it there after she has gone. That separates A from B and says
whether a civilian's money could be given back to the human some other way. The fix does not wait for it.

Install per map as usual with the game closed: `python debug\slot.py put "<work>\build\z_loot3\M02" F01` (or into
the expansion tree in place of `z_route\M02` / `z_m02s1\M02`); M03 carries its KLJoin.ini with `[CrewHop]`.

## 11. ASSUMPTIONS, guesses, not done

- Why the clerk's money was not paid (section 3, A or B) and why the other civilians and the jewel store's
  leftovers held nobody: not established. The fix does not depend on the first; the second is why the civilians'
  rule is stricter than what was seen.
- That removing the money object removes the hold at the watch shop: follows from the code (the tactic's
  candidates are the registered money objects only) and from L8 / L10 (exactly her 75,000 were left, the bots
  stood 9 from her group's origin) - not seen live.
- That a civilian's group without its money controller and trigger loads and plays as the same maps' other
  civilians do: the form is theirs (section 6); these very nodes in that form have not run.
- That 'more than one path node' means 'a path exists'; what the time stamp of the tactic's 4 s test is; who
  calls 0x727cb0; the unit of a container's countdown (field 4 = 10).
- That `'Activate'` on glass and `'Open'` work from 20 m away as they did from the door (the relay has no
  distance; the glass's own code was read in re/bots.md 12.1).
- `CASE_GUARD` 1150 is what the dynamic step needs today, not a property of the game. `trigger_reach` (the census's
  and the check's 'no mesh point inside its trigger') is this module's estimate of the ball of 0x783e60: centre =
  origin, a bot's centre 90 above its feet. The stand-in path (stage entry, 'on the way') is this module's mesh
  path through the middles of shared edges, not the game's pathfinder.
- That L11's crew records 1 and 3 are Squad#02 and #04 (the crew log does not name the squad). The 20 .. 30 s
  after GO for the first glass is computed from L10's times, not measured.
- NOT done: Retomoto was read, not built (its one doubtful table stack is for its owner; the check NOTEs it now);
  no hook part; the Defend-against-Loot order in the soldier's tactic lists was not read; the early glass
  (section 9) is unchanged; nothing in `check()` lets a civilian keep her money.
- `tools/kl_fa_loot.py` already exists (Retomoto's loot props, another session's): nothing was put there; the
  census and the window live in `kl_fa_bots.py`.

## 12. Changes in `tools/kl_fa_bots.py`

First pass: constants `LOOT_WINDOW DROP_WINDOW TRIGGER_PAD CASE_GUARD RELAY_MAX`; `money_objects`, `in_window`,
`cannot_take`, `window_report`, `trigger_reach`, `census` (command `census`); `plan` (option `window`: civilians out
of the loot, the units and their first station, one timer a stop with all cases, `P['window']`), the steps (a timer
after a named station), `make` (the timer's place in the chain, split lists), `check` (`side_holds`, the window
rule, `facts['loot_window']`), `options` (`--window`, `--no-window`), `DEFAULTS`, `RECIPE`.

Second pass: `strip_money` (new) and its call in `build()`, `diff` (the civilians' rule, the RESULT text), `plan`
(no `'Deactivate'` units; `P['window']['money_off']`; the guard as an option; no stale 'cases of stop' lines with
the option), `make` (two relays a timer again; the split suffix `_b .. _j, _11, _12 ..`), `cannot_take` /
`window_report` (no 'switched off' state; `WHY_*` reasons and `WHY_KNOWN`; plain objects), `leg_samples`,
`stand_in_way` (new), `check` (the relay rule as before the first pass; where the stage begins; the three NOTEs;
`facts['loot_window']` with `first_stage`, `on_the_way`, `plain_out_of_reach`, `money_taken_off`), `census` (the
same three), `options` (`--case-guard`), the docstring ('WHAT A SQUAD IS': the timers and relays). Without the
option `plan` / `make` produce what they produced (proved on M02 and M06, section 7 / 8); `kl_fa_bots_rt` calls
`plan` / `apply` / `check` / `diff` as before (Retomoto's check: PASS, one NOTE more).

Scripts (`<work>\research\agent_scripts\a-loot\`; they read): `fn.py` (a function of kl2.exe with floats and
vtables), `scan.py` (who uses a displacement), `pat.py` (functions by instruction patterns), `props.py` (property
records with member offsets), `node.py`, `people.py`, `cen.py`, `walk.py` (a squad's chain against the money),
`relays.py`, `crc.py`, `reach2.py`, `fld11.py` / `deact.py` / `rl.py` / `kd.py` (stock statistics: field 11, senders
of the four messages, relay sizes, KickDoor). `pass2\`: `civ.py` (the civilians of a build and their groups'
controllers), `flags.py` (entity flag bits against controllers and references), `difftest.py` (does diff's
civilian rule bite), `chain.sh`, `neg.sh` (the runs of sections 7 and 8).

## 13. After the review: each defect and what was done

| | severity | where | done |
|---|---|---|---|
| D1 | must | 'the fix does not depend on which [A or B]'; `plan()` option window; `z_loot3\M02` | **FIXED.** Re-read 0x6cdb40 .. 0x6cdb93 myself: the hidden-node test (0x6cdb65) and the state test (0x6cdb78) stand before every message but `'Activate'`, so a late `'Deactivate'` under B is dropped - the review is right. Neither of its two cheap fixes was taken as written: naming the civilians in the first timer only narrows B. The money controller and its trigger are taken off the civilians' groups in the build (`strip_money`): stored, no message, independent of A / B. No `'Deactivate'` relay is made any more. Sections 0, 3, 6, 11 corrected. M01, M02, M03 rebuilt, every check run again (section 8) |
| D2 | should | sections 0.4, 3, 5; 'four bots took the male clerk's 100,000' | **FIXED (the notes).** Re-ran the review's evidence: the jewel store has the clerk AND a self-opening drawer of 100,000 in 20,000 parts; in L8 / L10 / L11 exactly one such object was paid. 'Not established' is said; the timing argument for A and 'the human gets it by standing at the clerk' are withdrawn; that the bots left 200,000 at the jewel store is said, and that the hold is confirmed for a shut case and seen for one clerk only (sections 0.3, 3) |
| D3 | should | `check()`, where stage 1 begins | **FIXED.** The stage begins at the place the bot is walking to when the stand-in path is first inside any stage box, or at a hold beside the chain in / through one; EXITS_BANK, BOARDS and level exit boxes count too. Stricter than before on every build; the four new builds pass, the old ones fail as before (section 7) |
| D4 | should | `cannot_take()` / `check()`; `census()` | **FIXED as a NOTE.** `check()` NOTEs every plain object in the window whose trigger no point of the bots' mesh part reaches (Retomoto's stack, the two office jewels), and tests the way between the places (a NOTE: section 7 says why not a FAIL) |
| D5 | should | section 10, W1 / W2 | **FIXED (the notes).** The criteria are the review's (stages, van, nobody `in-play g1`); the position lines need `--poslog`; the bound is 2,320,000 (measured on the new build: 2,570,000 in the level, 250,000 out of reach); the 'did Deactivate arrive' question is gone with the message; the human run that separates A from B is kept, on the tab's build |
| D6 | should | the hand-over; `RECIPE` 'window' for all four maps | **NOT MINE TO DECIDE; laid out, partly eased.** The loss is said in the RECIPE comment, in a NOTE of every check and in section 6 with the choice per map (M02 needed; M01 / M03 optional, the tab's builds as the alternative). The civilians' switch-off is kept where the hold was seen and, by the same rule, where it was not - the check cannot tell them apart and a waiver was not built. The early glass is unchanged: it needs track B's change; `--case-guard` is the knob for then |
| D7 | note | `plan()`, `'Deactivate'` and stored field 6 | gone with the message (nothing sends `'Deactivate'`) |
| D8 | note | `check()`, the relay rule | **FIXED**: the rule of before the first pass; a `'Deactivate'` relay FAILs (the first pass's own builds now do) |
| D9 | note | the FAIL text | **FIXED**: `WHY_KNOWN` - SEEN / THE STRICTER RULE / one of five civilians |
| D10 | note | `make()` and `plan()`; the docstring | **FIXED**: the suffix beyond `_j` is a number; no 'each is opened by 3 bots' lines and no stale counts with the option; the docstring describes the timers |
| D11 | note | the dynamic step is track B's uncommitted file | **Re-run three times**, with its states 7613e7602a74, 12fdbedb87f5 and aa7f65f8d592: the same four archives. It is still uncommitted and still being edited: run `chain.sh` (or the two commands of section 8) once more when track B is committed and compare the sha1 of section 8 |
