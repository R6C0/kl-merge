# Retomoto Tower level design: the plan for the next session (blueprint)

2026-10-09, cloud session (no game files; branch `claude/charming-johnson-xblvr1`, level with `rtp-schemas`
at 0191832). The owner asked for the Retomoto Tower level design from the concept in CLAUDE.md ("Owner's
design for it"). A multi-agent workflow was started and then STOPPED after a few minutes at the owner's
request (usage window). Nothing of it reached a result: two of six readers had begun, none had returned.
This file is what the next session needs to continue without re-deriving anything.

## 1. What already exists (read before designing)

| what | where | state |
|---|---|---|
| survey of M09_A (tower) and M09_B (lobby, street) with coordinates, rooms, statues, squads, music | `re/retomoto.md` (906 lines) | offline, verified on the files |
| first-pass FA layer: spawn row at the window, blast at round start, 15 statue stacks + 6 boardroom stacks gated on two squads, JumpPoint join tower car -> lobby car, 10 B squads start at the entrance, F07's three vans re-laid on the road, bounds | `tools/kl_fa_author.py` + `re/retomoto_fa.md` | built offline, `verify` 2 known problems, `kl_fa.check` 0 CRASH / 0 BROKEN; NEVER run in the game |
| the two-part build (F07 + M09_B + M09_A), nav_join, name clashes, world positions | `re/maps.md` section 5, 6 | offline |
| what a round needs, how F01 paces its waves, "loot when a group is dead" | `re/fa_gamemode.md` 2, 4, 5 | read from stock |
| what the live bank round proved (loot by E, clock, score page, round 2; escape not reached) | `re/fa_round.md` 6 | LIVE |

## 2. The gaps between the owner's concept and the layer as built

1. **The street is not "Heat" yet.** Only the campaign's 10 B squads (20 police) start, all at once, when a
   criminal passes the entrance. No waves along the road, none of F07's 14 police squads is used
   (`re/retomoto_fa.md` section 5 "Not built"). Next step named there: F07's `Gameplay!020_Loot!*` squads
   moved as rigid groups to the first road block (z 3602..3911), actors on campaign actor positions, started
   by MERCONLY trigger boxes as the criminals advance down the road (the F01 idiom, `re/fa_gamemode.md` 2:
   `tbPlatform#01_MercOnly` -> `10_Defend` routs; `tbStreet_RespawnOnly` for the police side).
2. **The tower fight is one wave.** All 23 kept A squads (43 actors) are started by the blast timer. The
   owner's "fight through" reads better as staged: boardroom door -> reception -> atrium 3rd -> stairs ->
   2nd -> 1st -> elevator lobby, each started by a trigger box at the step (room bounds in
   `re/retomoto.md` 1.3, stairs in the table after it).
3. **Music is silent.** The 7 clips `Music/InHouse/Japan/M09_A/*` are not in the merged `PC_Def.str`:
   `kl_audio.merge` takes `FA_FILTER` only (`tools/kl_audio.py` line ~157; patch 3 in `re/maps.md` 7).
   Also missing: `Bomb_WarmUp`, A's ambience beds, the Japanese guard / police lines (`re/retomoto_fa.md` 6).
   Two routes to play it: `Music!PlayMusic_TokyoAction` sent 'AITrigger' at the blast (built; no FA level
   has a PlayMusic: LIVE) or settings field 157 = the clip's .SND offset (needs the offset after
   `graft_audio`: three lines in kl_graft).
4. **The join is a mechanism, not yet a designed beat.** JumpPoint fired by a box in the tower car
   (`re/retomoto_fa.md` 3): instant, no fade known; who is moved online is one of three cases (3.3).
   Design to write: doors open at the blast or when the room is cleared, a delay, police following,
   AFTER_DEATH points moving from tower to street.
5. **Bounds / kill**: the window drop (the tower hangs at y 19,600 over B's square bound at y 10,373), the
   atrium void, the roof (rappel-only in the campaign), the open west side of the street (overpass, bus
   terminal). All GUESS slabs today.

## 3. How to continue: the saved workflow

`.claude/workflows/retomoto-level-design.js` is the whole plan as a Workflow script (run with
`Workflow({name: "retomoto-level-design"})` in a session where ultracode / workflows are allowed):

| phase | agents | what |
|---|---|---|
| Understand | 6 readers in parallel | fa-layer (F07's gameplay layer and how kl_fa_author keeps / moves subtrees), street-atlas (M09_B coordinates for the shoot-out zones), tower-atlas (M09_A route and trigger-box places), mechanics (field lists of every pacing controller from `re/kl2.json` + proof state), audio-music (the `kl_audio.py` patch for the 7 clips), join-net (JumpPoint, police respawn, vans, ordered live tests) |
| Design | 3 designers | the same brief from three angles: stock-faithful, cinematic / Heat, risk-first; fixed 12-section structure (0 timeline .. 11 risks), every number sourced or GUESS |
| Judge | 3 judges (owner, engineer, tester lenses) | scores, factual errors, ideas to graft |
| Synthesize | 1 | writes `re/retomoto_design.md` in the house style; section 9 = the implementation spec |
| Implement | 1 | edits `tools/kl_fa_author.py` (+ `kl_audio.py`); no new entity / controller; py_compile only |
| Review | 3 lenses x up to 2 rounds + fixer | API correctness (field indices, names), geometry (on a floor, in the room, on the road), build (verify / check still pass) |
| Critique | 1 | completeness against the owner's four bullets |

It runs with NO game files (everything from `re/*.md` and `tools/*.py`); the result still has to be built and
tested on the PC: `python tools/kl_fa_author.py test <out>` then `re/retomoto_fa.md` section 8's live order.
Without workflows: do the phases by hand in that order; the prompts in the script are the briefs.

## 4. Design decisions already taken (do not reopen without the owner)

- Both parts stay in their own coordinates (nothing re-baked); the join is the campaign's own escape
  elevator car (2974, 19600, 909) -> lobby car (6272, 560, -6305), B - A = (3298, -19040, -7214).
- No new entity and no new controller: every object is a stock F07 one re-placed and re-wired, or a kept
  campaign object (`CAMPAIGN_KEEP`).
- Host = F07 (three animated vans, `ZAnimatedVehicle`), tested slot F01, build by `kl_maps.chain`.
- Loot: statues 15 x 150,000 (GUESS), boardroom 6 x 300,000 hidden until its squads' field-8 lists have
  fired twice into a `TriggerCounter` (ASSUMPTION that field 8 is 'wiped out').

## 5. Live order that unlocks everything (from `re/retomoto_fa.md` 8, unchanged)

1 chain loads (direct boot) -> 2 boardroom state at load -> 3 hidden things have no collision -> 4 round
start blast -> 5 guards react -> 6 statue loot -> 7 main room -> 8 the join -> 9 street police and bounds
-> 10 vans -> 11 death -> police -> 12 round end. Each step's fail action is written there.
