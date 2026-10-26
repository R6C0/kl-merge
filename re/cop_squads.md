# Cops and Robbers: a squad of AI police under each human cop ([CopSquad], klhook/klcopsquad.c)

2026-10-26, cloud agent (worktree, branch rtp-schemas). Owner's item 4 of re/ucc_cnr_owner_request.md. STATIC reading of kl2.exe 0490
(debug/dasm.py, callers by a rel32 scan of .text) plus the repo's own notes. **Nothing here ran in the game.** VERIFIED = disassembled at the
address given; GUESS = inferred, to be proven by the bench in section 7. The approach is luvsic's (`third_party/anp/loader/squad.inc`,
github.com/luvsicccc/a-newer-perspective, read only, not linked; credit to him for the ZSquadControl route and the offsets of section 2).

## 1. What the brief said and what the exe says

| brief | exe | verdict |
|---|---|---|
| `0x908040 Recruit(sc, body)` | `__thiscall`, 1 stack arg, `ret 4`. Writes `[sc+0xcc] = 1`; handle of the player `[sc+4]` (0x6ece90); script = `[body+0x77c]`; node place (0x7b3020); `script->vt[0x1b0](handle)` = SetOwner (ZSoldier slot 108, 0x4c3b10); appends the script at `sc+0x1c[sc+0x18]` **only if `[sc+0x18] < 16`**, no duplicate test; scene name `*_test*` -> `vt[0x140]`; then `0x7b3490(sc, body)` (into the player squad). | VERIFIED |
| `0x4c3900 Follow(sc, char all)` | `__thiscall ret 4`. Busy test `0x6a88f0([sc+4])` -> nothing. `[sc+0xa0]` refusal flag -> `0x6eac60(sc, 7, 0x2f)` and return. Needs `[sc+0x18] >= 1`; `all == 0` needs the current receiver `[sc+0x10]` inside the list; `[sc+8]++`; gesture 7 to `[P+0x840]` when `[P+0xd28]`. Callers 0x75b6f9, 0x8f41ab. | VERIFIED head |
| ZSoldier slot 79 `0x760e50 MoveTo` | vt 0xbd0954 +0x13c (RTTI `ZSoldier@CPPScript`). `(pos[3], char soft, char reset, int)`, `ret 0x10`. **Returns at once when `0x863a60(sm)` (in a session) and `0x4b0a40(sm)` (`[sm+0x54] == 3`, client).** Then the actor's 'held' test vt+0x620 -> vt+0x160. klescort.c calls it (proven offline). | VERIFIED |
| ZSoldier slot 83 `0x831850 Attack` | vt+0x14c. `(DWORD handle_or_0, const float pos[3], float T)`, `ret 0xc`. Clears `[s+0x700] &= ~6`, `[s+0x4fc] = 0`; with a handle: `0x8ccde0(handle)` -> object kept at `[s+0x720]` (+0x724 the time); handle 0: `0x4c53b0(pos)` position attack via `[s+0x5ac]`. No callers in .text (vtable only). | VERIFIED head |
| `0x6eac60 Refuse(sc, gesture, voice)` | called by Follow with (7, 0x2f). Not used by the module (it speaks a voice id; DD's banks have no order lines: luvsic). | VERIFIED caller |
| `P = ZFFPlayer, sc = *(P+0xcd0)` | DD's own code reads `[P+0xcd0]` and passes it as `ecx` to Recruit at 0x615ea5 (soldier init 0x615c90, `0x660b00(gd, idx)` = the player) and at 0x4bcf55 (ZFFGameData slot 13 -> 0x6bb4c0, a ZSquadControl method that walks its own squad `[sc+0xa4]` and recruits every other member, gated by `[gd+0x4d14]`). ZSquadControl RTTI vtable 0xb798dc; `[sc+4]` = the player (Follow). | VERIFIED |
| "DD calls Recruit only in a hosted session" | 0x615c90 calls it on four paths (0x615eb1 / f13 / f26 / fcb) after tests on `[script+0x6e8]` (EIsMercenary) and the player index; the session test is not in the 0x160 bytes read here. | not re-read (luvsic's claim stands as his) |
| **"0x6f64f9 streams the Attack handle" (network)** | 0x6f64f9 is `call [ebx]+0x14c` inside **0x6f6240**, a 0x193b8-byte-frame routine that compares a name with `"Glacier.dlc"`, reads 4-byte arguments from a stream (`call edi` with (buf, 1, 4)) and calls vtable slots of a script with them: a generic script-call dispatcher, **not netcode**. | DISPROVED |

Consequence of the last two rows: orders are host-side only (MoveTo refuses on a client; nothing replicates an order). The clients see
the soldiers move through the ordinary `DDL_ZFFActor` replication, which is how the stock AI cops are seen online (re/bots_online_fill.md 2).
GUESS until the bench: that a soldier recruited into a player's squad control replicates like any other police soldier.

## 2. Objects (luvsic's offsets, the ones the module touches re-read here)

- ZSquadControl `sc`: +4 player (VERIFIED), +8 order counter, +0x10 current receiver, **+0x18 count / +0x1c[16] receiver scripts** (VERIFIED
  in Recruit), +0xa0 refusal flag (VERIFIED in Follow), +0xa4 the player squad (0x6bb4c0), +0xcc 'has recruited' (VERIFIED).
- ZSoldier@CPPScript `s` (vt 0xbd0954): +0x40 body (klescort), +0x4f4 squad, +0x69c owner player (SetOwner), +0x6a4 commandable,
  +0x720 attack target object (VERIFIED in Attack), +0x63c / +0x738 / +0x6d8 objects Recruit's callees dereference unchecked (luvsic; the
  module refuses a soldier lacking any of them).
- ZFFActor (vt 0xbb3bac): +4 node (flag bit 10 = off), +0x54 -> +4 team value, +0x576 'takes orders' (klescort.c), +0x5fc -> +4 health,
  +0x770 held as a human shield, +0x77c script.
- ZFFPlayer (vt 0xbb45f4): +0x273c type byte (2 heister, 3 policeman: re/cops_and_robbers.md), +0x460 feet, +0xcd0 squad control, +0x27b0
  aim point and `[+0xbd4]+0x2ac` aim target handle (luvsic, GUESS here: not re-read).

## 3. Finding the human cops (host)

The session player table: `0x6161c0(sm)` = `[[sm+4]]->vt[0x44]()` (needs `[sm+4]`) -> T; `[T]` = 12-byte entries `{?, ZFFPlayer* +4, ..., used
byte +9}`, `[T+4]` = a byte per index (0 = pickable), `[T+0xc]` = count (VERIFIED in the picker 0x6ee860, which takes the first entry with
`[P+0x273c] == type` and `used == 0`, then writes `used = 1` at 0x6ee8ce). A human cop = entry with a ZFFPlayer of type 3 and used == 1.
GUESS: the C&R lobby's team split marks the humans' entries used the same way (the FA death path does). The log line
`copsquad: cop ... recruit` counts them; zero cops with humans on the police side means the mark is elsewhere (then try `[T+4][i]`).
klsync.c's klsy_human (team object `[P+0x54]` or 40 units around the feet) is the test that keeps a HUMAN's body out of a pass; this
module never orders a ZFFPlayer's body: it only ever hands ZFFActors (police soldiers) to the cop's squad control, so the type-3 human
players are the LEADERS, never the followers. The local host player, if a cop, is found by the slot method (`gd+0x828+4*[gd+0x898]`,
klescort.c kle_human) and matched to its table entry: only his squad takes key orders.

## 4. Where the AI police come from, and the budget

- They are the level's own police squads: `ZSquadScript` groups whose game-type mask has bit 2 (TeamMode) survive the C&R collect filter at
  0x7b382c..0x7b384b (re/bots_online_fill.md 1); the stock maps' police squads are mostly eAllTypes (kept), the UCC-only ones are dropped.
  Their soldiers are ordinary `ZFFActor` + `ZSoldier`, run by the host's squad update (0x47e440 skips on a client).
- No new actor is created, so the **12 client seats are not touched** (AI has no seat: re/bots_online_fill.md 2). The budget is the number
  of police soldiers alive when the pass runs (10 s after the round state is entered, GUESS the same 10 s as `Timer_start_bots`): with 6
  human cops x 4 = 24 wanted, a map with fewer gives the nearest cops their four first (cops are staffed in table order). The receiver cap
  is 16 per squad control, so Per is clamped to 8.
- A recruited soldier stays in its level squad too (`0x7b3490` adds to the player squad; luvsic's `recruit_detach` removes it from the level
  squad first with 0x5230c0; the module does NOT detach, as DD's own hosted path does not). GUESS: the level squad's own chain may keep
  giving it steps, which is why Follow is re-issued every FollowS seconds.
- What they do under Follow: ZSquadControl's own update (0x523d10, luvsic: parks / re-recruits a receiver whose node is disabled) and the
  follow goal (ZSoldier slot 80). Whether a POLICE soldier (another animation set, team 3) follows a type-3 player as a merc follows Kane
  is the first thing the bench must show.

## 5. The module (klhook/klcopsquad.c, ~330 lines; pure parts in klcopsquad_logic.h, harness klcs_test.c: 64 checks, ALL PASS)

- Gate (`klcq_gate`): role `[sm+0x54] == 2` (host), `[sm+0x5c] == 4`, sub-mode `[0x168e59c] == 2`, state `[sm+0x70]` 0x13..0x1f (klsync.c's
  round window); game thread; `klh_exe_ok`. A client never passes (and 0x760e50 would return anyway).
- Head checks once per round (`klcq_heads`): the first bytes of 0x908040 (`83 ec 0c 55 8b 6c`), 0x4c3900 (`83 ec 24 56 8b f1`), 0x831850
  (`55 8b ec 51 53 56`), the 16 bytes klescort.c knows of 0x760e50, and vt 0xbd0954 +0x13c / +0x14c holding those two. A mismatch: nothing
  is ever called, said once.
- Staffing: 10 s into the round, every 500 ms: the human cops (section 3); for each not yet staffed this round, a walk of the scene's entity
  table (klsync.c's klsy_walk shape) collects police soldiers (section 2 tests, team value = `Team`, alive, not already a receiver of any
  cop's control, node on, +0x576 == 1, not held), `klcq_pick` takes the nearest Per within MaxM, each is Recruited (the receiver list is
  read back: `listed 1` in the log = the call took), then Follow(all). Re-issue: Follow(all) every FollowS s per staffed cop.
- Keys (host's own keyboard, game window in front, GetAsyncKeyState, not consumed; edge + 150 ms debounce): F Follow(all); G hold = MoveTo
  (own place, not soft, reset) per soldier; H attack = Attack(handle of the aimed actor or 0, aim point, AttackT) per soldier.
- Writes: none of its own; the game's functions write the heap (sc lists, script owner). No code byte changes. No __try: the guard is the
  pre-check pattern of klescort.c (readable objects, known vtables, known code heads).

Not in this module: orders from REMOTE cops (their keys never reach the host). The next step is a UDP order channel in klcharonline.c's
pattern ("KLCQ1;<entity idx>;<order>" from the client, the host applies it to that entity's squad) - after the bench shows the host-side
part works. Also not done: a HUD mark of the squad, voice acks (DD's banks have no order lines), a police-only animation check.

## 6. Risks

1. **Follow on a police soldier**: the follow goal was written for mercs following Kane; a type-3 player as owner and a police animation
   set are new. Expect at worst standing still, at best following; a crash would be in 0x4c3900's gesture path (`[P+0x840]`) on a REMOTE
   player's object. Bench with the host as the only cop first.
2. **Recruit's unchecked dereferences** (luvsic's list: script+0x63c/0x738/0x6d8, body node, vtable slots): the module refuses a soldier
   that lacks any; a crash there would be a new offset.
3. **The level squad fights the order** (its chain re-issues steps): the symptom is soldiers walking off between Follow re-issues; the
   remedy is luvsic's detach (0x5230c0) - not built.
4. **Replication**: GUESS that a recruited soldier still replicates as a plain police actor; a client seeing it frozen or teleporting would
   show in klsync's compare (`[Sync] Compare=1` on the client).
5. **Team value 3** is klsync's measured guess; a wrong value recruits nobody (log says `0 free within range`).
6. The used-byte test of section 3 (GUESS); zero cops found = the mark is elsewhere.

## 7. The live bench (not run)

Two instances on one PC (re/netsmooth_solo.md section 6: TEST hook with [Solo], `H_host.ini` then `J_join.ini` 45 s later) on stock DD01,
System Link, lobby in Cops and Robbers (6-player floor: `[Lobby] MinPlayers` / OnlineFill lowers the Ready floor, re/bots_online_fill.md 3),
the host on the police team. Ini: `[CopSquad] Enable=1 Log=2`, `[Sync] Probe=1 Compare=1` on the client, `[Net] Log=1`.
Read in KLHook.log, in order: `copsquad: ON`; `copsquad: round on the host, C&R (state 0x..)` (proves the sub-mode word and the state
window); `copsquad: cop <P> recruit actor ... receivers 0 -> 1, listed 1` x4 (proves Recruit took); `Follow(all) after recruit: 4 receivers,
order no. 1, refusal flag 0`; then watch: do the four cops walk after the host's player (Follow), stop on G, shoot at the aimed heister on H;
on the client, `sync: vs host` lines for those four slots must not be worse than the other cops'. A fault anywhere: `debug/triage.py --keep`,
the address goes into section 6. FAIL cases to expect first: `0 police soldiers seen` (team value), `no human cop in the session table`
(used byte), `listed 0` (Recruit refused: `[sc+0x18]` already 16 or the scene name test).
