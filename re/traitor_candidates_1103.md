# Traitor candidates (1103) - section A: where slot 111's candidate comes from
Static RE of kl2.exe 0490 only. Nothing run, patched or committed. GUESS = not read from code.

## A1. Callers of slot 111 (+0x1bc, 0x882470)
The call sites in the task brief (0x8824e4, 0x8826ec, 0x882732, 0x5709c2) are NOT callers (ret of 0x882470 / 0x7f6850 gate sites).
The only ZSoldier callers are in slot 113's body 0x767510 (thunk 0x47a0f0): 0x767bda (call 0x767bfc) in loop 1 and 0x767e41 in loop 2.
Other [reg+0x1bc] vcalls (0x4df125/13e, 0x4eb483, 0x794847) are other classes.

## A2. Candidate source
Slot 113 walks B = [ZSoldier+0x698] (the soldier's "known entities" memory): count at B+0, entries at B+4, stride 0x14, cap 10.
Loop 1 skips entries whose bit0 is clear. Entry type 1 (ZFFActor) -> slot 110 (+0x1b8); type 2 (ZFFPlayer, ptr = entity,
+0x10 = [entity+0x54]) -> slot 111 with 7 args (candidate [ebp-4], entry ptr, floats, flags); other types -> slot 112 (+0x1c0).
So slot 111 sees a human only if B holds a type-2 entry. B is filled ONLY by B::NoteEntity 0x7bd720 (thiscall, arg = handle,
resolved via 0x8ccde0): ZFFPlayer-class -> sets B+0x184=1 and builds a type-2 entry; ZFFActor-class -> type 1 (ptr=[e+0x77c], no add if null);
else 0x64dc70 (type 3). Refreshes the +0xc timestamp if present; on overflow (10) replaces the oldest; notifies B+0xd0 listeners (vcall +0x1a0).
NoteEntity callers: 0x5a8230 (in 0x5a8140 = ZSoldier slot 105), 0x608443 (message handler 0x608050), 0x8478b3 (0x8473a0 = slot 96).
Pruning: 0x51e480 drops type-2 entries whose entity is dead/invalid (0x559190 on 0x6ece90) or unseen for a time from [0x168d7c0]+0x20.
Constructor: 0x615d1c new(0x194) + 0x7758c0 -> [soldier+0x698].

## A3. The filter that keeps humans out (team-bit gate)
Before NoteEntity both feeders test the sensed entity's team against a mask on the soldier's OWN team record:
 0x5a8166 eax=[edi+0x54] (sensed); ecx=[eax+4] (its team); eax=[esi+0x40] (own actor); edx=1<<cl; ecx=[eax+0x54];
 0x5a817d test [ecx+0xc],edx ; 0x5a8180 je 0x5a82b8  -> skip, entity never reaches 0x7bd720.
Same test in 0x608050 at 0x608424-0x60843a (also needs 0x7f7fb0 to pass). 0x8473a0 not read in detail (GUESS: same shape).
Consequence: a bot on team Ally (2) never notes a human crew member (team Mercenary 0, per balance.md) unless bit 0 of
[[bot actor+0x54]+0xc] is set. Online (role 2, mode 4) that bit is evidently clear for ally bots, matching bs11-bs13
(slot 111 never saw a ZFFPlayer candidate, slot 15 never reached). Offline Arcade: GUESS - the hostile mask differs or the
traitor path swaps the bot's team before sensing; not verified. Who writes [teamobj+0xc], and whether the team object is
per actor or shared per team ([actor+0x54] looks shared: +4 team index, +0x30 a timestamp), was NOT resolved (store search
for "+0xc" is too noisy). If shared, writing it would change every bot's view, not just the marked one.

## A4. Levers without patching hashed code (hash status of 0x7bd720/0x5a8140/0x608050 not checked against klranges.h)
1. Call B::NoteEntity directly: ecx=[markedSoldier+0x698], push the human's handle (0x6ece90 gives handle from entity), from the
   game thread (e.g. inside the existing private-vtable wrapper of the marked bot's slot 113/111 or its per-tick hook). Bypasses the
   team gate entirely and affects only that bot's B. Smallest lever; it is the same call the sensing code makes. Caveat: pruning by
   0x51e480 and the 10-entry cap mean it must be refreshed each tick or two; entries need bit0 set (NoteEntity does this).
2. Private vtable slot 105 (0x5a8140) wrapper on the marked bot only: invoke the original with the team-record mask
   temporarily OR'd with the human team bit (data write, restore after). Only safe if the team record is per actor (GUESS, unverified);
   otherwise use lever 1.
3. Write the human bit into [[actor+0x54]+0xc] permanently: only if per actor; GUESS.
Also needed after the candidate exists: slot 111's own gate (0x882614: 0x6db900/0x87c980 both false online so an ally scores humans
through 0x882584) and the 0x6e3400 step-4 damage neutraliser (see fireline_goal_path_1103.md).

## A5. Open
Writers/ownership of [teamobj+0xc]; whether 0x8473a0's path has the same gate; hashed status of the three functions;
what feeds the offline Arcade traitor.
