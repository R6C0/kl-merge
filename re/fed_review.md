# Coming back as a fed: adversarial review (2026-10-10)

Reviewed: `klhook\klfed.c` (490 lines), `tools\kl_fa_fed.py`, `<work>\build\x_fed\M01 M02 M03 M06`,
`re\fed.md`, `re\fed_respawn.md`. Offline only: nothing was installed, the game was not started, no
file of the repo but this one was written, no file of the builds was changed (audit / preflight, which
rewrite `audit.json` / `preflight.json`, were run on copies in the session scratchpad).

## 0. Verdict

| part | verdict | why |
|---|---|---|
| `klfed.c` wired into the hook, `[Fed] Enable=0` | **install switched off: yes** | `klp_tick` and `klp_init` return on their first line; compiled again here into a fresh copy of the repo's `klhook` with the three lines: SHIP and TEST, `/W3`, no warning |
| `Enable=1` alone (log, F0) | **switch on** | reads only (`klh_rd` = ReadProcessMemory); no write is reachable with `Player=0 Bots=0` |
| `Player=1` (F1 - F4) | **switch on for a first live check**, on **M03** first | every address holds (section 1); nothing found that writes outside an Arcade round on a non-stock level. Two small hardenings wanted, not blocking (2.2, 2.3) |
| `Bots=1` / `Bots=2`, ONE round (F0b, F5b) | **switch on for a first live check** | the two writes are what the update 0x47e440 needs; chain self-checking |
| `Bots=1` across a SECOND round on the same load (F6) | **fix first** | `klfed.c` 381 / 452-456: `klp_b[]` is not cleared at a new round - a write through a stale script pointer is possible (2.1). Two lines |
| `x_fed` builds as level data | **live check only (F5), not the owner's build** | all six checkers reproduce (section 4). But the stock precedent the design quotes is wrong (3.1), a parked Dead Men actor has never been seen to come in (3.2), and with `Bots=0` every heister who ESCAPES sends a SWAT man at the player (3.3) |
| `x_fed\M06` | **last** | police player model on an actor with a heister's voice / animation data: three assumptions in one body (3.4) |

Order I would run: F0 -> F0b (u_maps build, proves the chain and that a dead squad's update still
runs) -> F1 on M03 -> F5b on `x_fed\M02`. F5 with `Bots=0` only as the comparison run.

## 1. Addresses and offsets against kl2.exe 0490 - all hold

Disassembled again for this review (`debug\dasm.py`, plus byte searches over the whole image).

| claim | result |
|---|---|
| gate 0x67f480 head `83 3d 60 ea 68 01 00 56 8b f1 74 04`, dword not 0 -> `xor al, al / ret` | holds |
| 0x168ea60: two references in the image, both compares | holds: 0x67f482, 0x86f522; no reference to 0x168ea5d..63 otherwise; `.data` raw size 0x73600, so the address is in the zero-filled tail; in none of the 225 hashed ranges |
| it is a variable of its own, not a member of an object some routine clears | holds: 0x168ea60 .. 0x168ea9c are single dwords with one to three readers each; the object before it (0x168ea54) ends at +0x5c |
| the gate has three callers | holds: 0x4b2a2c, 0x7047b5, 0x80530e; no pointer to it in `.rdata` |
| **the twin 0x86f520 (ten callers) cannot run in Arcade** - not argued in klfed.c, which only treats the gate's three callers | holds, checked here: its callers sit in `ZGameRulesFragileAllianceSv` slots 7, 11, 14, 44, 195 (or are reached only from them). `ZGameRulesHeist` and `...Sv` are siblings under `ZGameRulesFragileAlliance`; none of those routines is in the Heist vtable. The gate's callers are Heist slot 11 (kill rule), slot 7 -> 0x58b2c0 (per frame), slot 195 -> 0x805120 (vehicle left) |
| kill rule 0x704610: status 7, countdown 5.0 (0xbcb330), flag 4, gate; 'no' -> slot 112 -> status 1, `+0x11 = 0`, flag 0x4000 | holds. Also: `inc byte [record+0x13]`, and +4.0 s on the countdown when slot 108 says so |
| slot 112 = 0x4549f0, slots 42 / 192 / 193 / 199 / 204 | hold (0x47d190, 0x5dff40, 0x642850, 0x518e30, 0x7622f0) |
| per frame 0x58b40c: phase 2 under 4.0 s, respawn 0x4b28d0 at 0 | holds (jump table 0x58b618, case 1). The case does not test for record 0: any record with status 1 is respawned as a police PLAYER. Bots never get status 1 (their kill rule 0x485740 writes 7 only, 0x48581d) - but **nothing else may ever write status 1 to an AI record** |
| respawn: flag 0x100 -> new pick; else pick only if `+0x14 == 0xff`; `int3` 0x4b2984 | holds |
| pick 0x54cab0: slot byte 0, `[entry+4]+0x273c == type`, `entry+9 == 0`, sets `+9` | holds; `klp_count` counts exactly so. The pick does not test `[entry+4]` for 0, the hook does |
| table = `[[session+4]+8]` (0x6161c0 -> handler slot 17 = 0x6e2650) | holds |
| local player 0x660b00: `(char)[gd+0x898+n]`, 0xff = none, `[gd+0x828+4*i]` | holds (28 dwords fit before +0x898: the hook's `sel < 28`) |
| slot 192: timer `[rules+0x200]`, vehicle state 0 or >= 7, life `dec byte [score+0x6c]` unless slot 106(0), state 0x1f | holds |
| slot 42 writes `[rules+0x4c]`, `[rules+0x200]`, `[score+0x40]` | holds (it writes min(argument, 0x6d3130())) |
| Arcade test 0x7f6850 | holds: sub-mode 0, 1 and > 3 test mode 4; 2 and 3 say no |
| squad update 0x47e440: lists only when living < `[+0x40]`; field 8 when living == 0 and `[+0x20b] == 0`; then `[+0x40]` = living | holds. 0x87ebf0 sends the list at `+0xcc`, sets `+0x20b` and `+0x20d` |
| 'living' 0x71adc0: `+0x576 != 0`, `+0x8f0 == 0`, `+0x5cd == 0` over `[+0x4c] .. [+0x50]` | holds |
| boarding sets actor `+0x8f0 = 1` (0x684253) | holds: the ACTOR branch of 0x6840a0 (0x6841fd on); the player branch is the one with the police test 0x68414e |
| chain: actor `+0x77c` soldier, soldier `+0x40` actor, soldier `+0x4f4` squad, squad `+0x164` | hold (0x7b390a .. 0x7b3966, 0x7697f1) |
| vtables 0xbd3514 0xbd1be4 0xbb45f4 0xbb3bac 0xbccdac 0xbcce3c | RTTI names as stated, one primary vtable each |
| 0x8824e7 police player: target only for team 2; 0x817e10 `+0x14 = 0xff` at the round start; 0x8c7a8b 600.0 | hold |
| floats 5.0 / 3.0 / 4.0 / 600.0 | hold (0xbcb330, 0xb4a174, 0xb38f38, 0xb206d0) |

One thing the hook's comment leaves out about its own re-fire: with `[+0x40] = 1` and living 0 the
update walks the WHOLE ladder again - it sends the 'man lost' list `+0x78` once more and would call the
'first lost' / 'half' / 'one left' senders if their latches `+0x208 / +0x20a / +0x209` were 0. They are
1 after the muted pass, and the heister squads' lists 4..18 are empty but field 8, so nothing else goes
out. It stops being true the day a heister squad gets a second list (`kl_fa_fed.check` only NOTEs that).

## 2. klfed.c - what I tried to break

Not broken:

- **Inert without keys.** `Enable=0`: lines 443 and 479. `Enable=1` only: `klp_tick` reads and logs;
  line 458 and line 323 keep every write behind `Player` / `Bots`; line 448 touches the dword only with
  `Player=1`. The repo's `KLHook.ini` has no `[Fed]` block, so the default is off.
- **Stock level / no Arcade round.** `act` is `klx_level_verdict == 2` with the guard on (227-238);
  ON needs `act`, state 0x19, record 0 local with client index 0, the SP handler (324-338). Off in every
  other case, also when `klp_read` fails for any reason (447-451). Bots and the round-end write need
  `act && game_thread && state == 0x19` (341, 466).
- **Game thread.** No game function is called at all. ON only with `game_thread` (279); the heap writes
  only with `game_thread`; `klh_tick`'s busy flag keeps the two tick sources apart.
- **A value that is not ours** is left alone (274); the gate's twelve bytes are compared before arming.
- **`int3` 0x4b2984.** Armed only with a free type-3 body counted the way the pick counts. Nothing else
  takes a body during a round (the other callers of the pick are rules slots 9 and 197 = set-up).
- **Lives / score / round end.** The hook writes no life and no score. The life is taken by the game's
  own slot 192 as at every death. The round-end write is slot 42's three floats, once a round, only
  downwards. With vehicle state 1..6 the round waits at clock 0 until the state changes - the same as
  stock after a death.
- **The switch held while you are alive** changes nothing for the other two callers: the gate's real
  answer for a living local criminal is 'no' as well (0x67f55a ..), and for status 1 too (0x67f519).
- **Off-game test**: `klfed_test.exe` gives 52 PASS, 0 FAIL in three runs of four here; one run gave
  FAILs ('not an Arcade session: off'). Cause is the harness: `tick()` sleeps 105 ms, the fallback
  throttle is 100 ms and GetTickCount steps by 15.6 ms, so a pass is sometimes skipped. In the hook that
  means an OFF from the fallback thread can come one pass (100 ms) late. Harmless; the test should
  sleep 130 ms.

Findings:

### 2.1 FIX FIRST (before F6): `klp_b[]` survives a round - lines 381, 449, 452-456

A bot's entry is reset when its record or actor changes, or when it is 'in play again after not being in
play'. A bot that was still status 0 when the round ended keeps state MUTED and the OLD script pointer
into the next round. If Arcade rebuilds squads between rounds (not known: fed.md 7, F6), that pointer is
freed memory. At the bot's death `klp_script_ok` (369-373) tests vtable, `+0x3c` and `+0x48` - a freed
block often still passes - and lines 408 write one byte and one dword into it.

- line 454 (new-round branch of `klp_tick`): add `memset(klp_b, 0, sizeof klp_b);`
- line 372: also require the member list to be this actor still:
  `&& klh_rd32(klh_rd32(klp_b[i].script + 0x4c)) == klp_b[i].actor` and `[+0x50] - [+0x4c] == 4`.

A first round (F0b, F5b) is not affected.

### 2.2 Wanted, not blocking: record `+0x14` is printed but not tested - line 328 / 335-337

The respawn uses a `+0x14` that is not 0xff AS IT IS when flag 0x100 is clear (0x4b2933). The round
start writes 0xff, so this should not happen - but then the free-body count is not what protects, and
an index of a non-police entry would make that object the local player. One more condition before
`armed`: `h->body == 0xff || (h->cflags & 0x100)`, else stand down with a line. Also covers another
part of the hook (the proposed 'choose your police body') writing it later.

### 2.3 Wanted: status 1 arms without the hook having armed before - line 328

`h->status == 1` sets `want = 1` whoever produced status 1 and even with `klp_r.ours == 0`. Nothing in
stock Arcade produces it, so this is theory; `&& klp_r.ours` would make it exact.

### 2.4 Notes

- Line 96-100: the ASSUMPTION that a dead one-man squad's script is still updated decides whether
  `Bots=1` can work at all. F0b on the `u_maps` build answers it at no risk - run it before any `x_fed`
  build.
- A 50 ms window: the last heister leaves play and you die inside the same tick interval -> you return
  as a fed with nobody to hunt; the hook's round end closes it 3 s after you stand. Costs 8 s, no fault.
- `klp_r.was_fed` is written and never read.
- The compile check here used the repo's `klhook` as it was at 17:05; `klhook.c` / `KLHook.ini` were
  being changed by another session during the review (`kltalk.c` appeared). Compile again at wiring.

## 3. The level step

### 3.1 The stock precedent quoted is wrong (kl_fa_fed.py 35-37, fed.md 144-146, klfed.c section 3)

'Stock F03 `40_SWAT_Reinforcement_0n\HuntBehaviour`, which stock names from a squad's field 8 exactly as
here'. Measured on the nine stock levels:

- there are 5 `HuntBehaviourRout` in stock. The four of F03 are named by **nobody**.
- F03's field 8 names the next squad's **`DefendBehaviour`** (a `DefendBehaviourRout` with three
  position boxes), and a `RandomTrigger` names the same rout. The hunt group is an un-named child.
- the one stock hunt rout that IS a message target: F02 `04_Squad_police_guarding_middle_01\
  HuntBehaviour`, named by a `ZTriggerBox` (field 17) of its own subtree; its squad is `eStayBack`,
  `eAllTypes`, field 3 = 0. So 'a message to the hunt rout of a parked squad' runs in stock Arcade
  once - from a trigger box, not from a squad list.
- parked squads (field 3 = 0) with actors that Arcade loads: 51 `eAllTypes` + 4 `eHeistOnly` in stock,
  all started through `DefendBehaviourRout` / `RunToCoverBehaviourRout` / `SquadModifierBehaviour`.

So the fed's form (parked, `eUnleashed`, started by a squad list at its hunt rout) has NO exact stock
twin. It may well work (a list send is the same message whoever sends it, 0x77b820). If F5 shows no
fed: give the squad a `DefendBehaviourRout` (one box at its place) as the named target and leave the
hunt group un-named, which is literally F03. The three texts should be corrected either way.

### 3.2 A parked Dead Men actor has not been seen to come in

`re\map_ai.md` (table 'squads that arrive'): field 3 = 0 was seen live only on F07's own squads
(Retomoto); 'nobody has seen it on a Dead Men squad'. The feds of M01 / M02 / M03 are copies of the
maps' Dead Men police actors in a parked squad: first of their kind. F5 is the test; nothing offline
can settle it.

### 3.3 `Bots=0` on an `x_fed` build is a different game, not a neutral default

Known and documented (the boarding catch). What it means in play: in runs K1 / K2 the bots loot, board
and escape - on `x_fed` each of the seven who gets away sends an AK / SCAR SWAT man with 175 health
after whoever is still on foot, usually the owner. So: no `x_fed` build in the owner's slot unless the
hook with `Bots=1` (or 2) is in and F0b has shown the release works.

### 3.4 M06

Fed = the police PLAYER model 1919 on a copy of a heister actor: animation set `Lynch_NPC`, the
heister's `.SND` offsets (241120 / 265616), `ZFFActor` fields 5 / 6 = 20 / 40 where every police actor
has 0xffffffff, soldier row from stock F07. `check` says it as 7 NOTEs. Two of the feds stand 54 / 55
from an AFTER_DEATH point in the plan (13.8 m below it, so `check`'s 'ON a point' rule rightly does not
fire). Run M06 last.

### 3.5 What holds

- **References**: every reference out of a fed subtree resolves (weapon templates of the host's
  equipment; the search box); the only references INTO a fed are the seven `ZSquadScript[8]` entries,
  one per heister squad, each to its own number.
- **Body** (M02, read from the file): the fed actor and its group are field-for-field the template's
  (`PoliceSwats_01..04`: properties, soldier row, .gms flags, aux); only place and facing differ.
  Team Enemy, so no crew record is made for it.
- **On the mesh**: each fed on a polygon of the START row's part, clearance 61..199, a path to the
  START row exists (M02 149..157 m, M03 178..185 m, M01 198..202 m, M06 214..224 m), at least 2281 from
  the START row. On M02 / M01 / M06 the feds are NOT at the AFTER_DEATH points (20.5 m / 5.9 m / 1.5 m
  away in the plan and on another level), as fed.md says.
- **No large member grown**: `.prm .ANM .fxc .WAV .TEX` byte sizes as in `u_maps`; the `.prm` differs
  in 987..2491 dwords (the re-pointed .oct record offsets, the .oct grew 224 bytes), nothing else.
  Grown: `.prp` +7.1 kB, `.gms` +0.3..0.6 kB, `.buf` +352, `.oct` +224; `.rmi .rmc` same size. The .gms
  heap budget (+0x1c) is unchanged, REF slot count +35. 31 members, same order.
- **Files beside the archive**: only `fed.json`, `fed.txt`, `graft.txt`, `steps.json`, `audit.*`
  (and M03's `preflight.json`) differ from `u_maps`.

Not checked by any tool and not by me: what the hunt box means to the rout (GUESS in the tool), and the
'full size' reading of `ZBoxPrimitive` (only the group-tree box depends on it; `--no-tree` is the A / B).

## 4. Checkers, run again here

On `<work>\build\x_fed\<map>` (read-only ones) and on scratch copies (audit, preflight):

| | M02 | M01 | M03 | M06 |
|---|---|---|---|---|
| `kl_fa_fed.py check` | PASS 0 FAIL 0 NOTE | PASS 0 / 0 | PASS 0 / 0 | PASS 0 FAIL 7 NOTE |
| `kl_fa_fed.py diff u_maps x_fed` | only the feds and their list entries | same | same | same |
| `kl_fa_bots.py check` | PASS 0 / 0 | PASS 0 / 0 | PASS 0 FAIL 8 NOTE | PASS 0 FAIL 1 NOTE |
| `kl_impact.py` | problems: 0 | 0 | 0 | 0 |
| `kl_maps.py audit` | PASS, 0 that must be 0 (6 known) | PASS (1 known) | PASS (0 known) | PASS (6 known) |
| `kl_maps.py preflight` | CRASH 0, RISK 3, NOTE 13 | CRASH 0, RISK 0, NOTE 8 | CRASH 0, RISK 0, NOTE 9 | CRASH 0, RISK 2, NOTE 21 |

All exit 0; the numbers are those of fed.md's table and of the logs beside the builds.
Hook: SHIP and TEST build of a fresh copy with the three lines, no warning; `klfed_test.exe` as in 2.

## 5. For the lead

1. Wire `klfed.c` in with `[Fed] Enable=0`; that is safe to ship.
2. Before any second-round run with `Bots=1`: the two lines of 2.1. Take 2.2 and 2.3 in the same edit.
3. Live order: F0, F0b on the installed `u_maps` build, F1 on M03, then `x_fed\M02` with `Bots=1`.
4. Correct the stock-precedent sentence in `kl_fa_fed.py`, `fed.md` and `klfed.c` (3.1).
5. Keep `x_fed` out of the owner's slot until F5b has shown a fed arriving at a death and none at a
   boarding.
