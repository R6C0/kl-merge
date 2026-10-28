# Ally bots triggering cops / spawns (T4) - static research, 2026-10-28

Scope: STATIC only (disassembly of kl2.exe + reading klhook/*.c and re/*.md). Nothing launched, nothing written to the game folder.
Marks: CERTAIN = seen in code / disassembly / log. GUESS = inferred, needs a bench.

## 1. Finding in one paragraph

- CERTAIN: a ZTriggerBox counts a team-2 (Ally) actor as "a player" only when the game's session check 0x7f6850 is true. 0x7f6850 is a jump table on the session role `[sm+0x54]` (sm = `[0x168e598]`): roles 0/1 (Arcade, solo) return `[sm+0x5c]==4`; roles 2/3 (online host and client) return false. So in Arcade AI heisters set off cop/spawn trigger boxes; online they do not.
- CERTAIN: SHIP policy forbids .text/.rdata patches, so the code gate cannot be flipped. Only data/import-slot writes and game calls are allowed.
- CERTAIN: squad wake-up is NOT player filtered. It is noise driven (0x873c30 fills the noise list at gamedata+0x15bc; 0x4e71e0 wakes squads over that list). Bots that shoot/make noise already wake squads online (mostly CERTAIN, some callers unread = GUESS for edge cases).
- CERTAIN: online the heister-side squads are `eHeistOnly`; filter 0x7b3790 drops them online. Data fix already exists: tools/kl_botsonline.py / kl_fa_bots.py `--squad-game eAllTypes`.

## 2. Site table (kl2.exe, base 0x400000)

| Site | What | Mark |
|---|---|---|
| 0x7f6850 | Arcade check, jump table on `[sm+0x54]`; true only roles 0/1 | CERTAIN |
| 0x42afd0 | ZTriggerBox update; gate call at 0x42b1e0 (team-2 counts if 0x7f6850) | CERTAIN |
| 0x626ec0 / 0x626f92 | ZTriggerBox2 update and its team-2 gate | CERTAIN |
| 0x6c3d50 (0x6c3f2f / 0x6c3f44) | exit trigger actor branch (escape zone) | CERTAIN |
| 0x8c16c0 | inside test: node position -> 0x7b3020 -> compare box centre `[box+0x84]`, radius `[box+0x90]` | CERTAIN |
| 0x6ae730 | fire: sync slot 3, then slot 34 | CERTAIN |
| 0x45f5d0 | slot 34: posts AITrigger word `[0x1688e70]` to list `[box+0x38]`, applies field-10 re-arm | CERTAIN |
| 0x873c30 / 0x4e71e0 / 0x79e1b0 / 0x47e64c | noise list fill and squad wake | CERTAIN (callers partly unread) |
| 0x6ab250 | ZSoldier constructor | CERTAIN |
| 0x7b3790 | online squad filter (eHeistOnly dropped) | CERTAIN |

ZTriggerBox fields: +0x40 enabled, +0x41 enter, +0x44 count, +0x48 left, +0x4b team-2 enter, +0x50 re-arm, +0x58 tracked, +0x60 ECPS, +0x64 local-only, +0x68 EFAMPS, +0x6c sync object, +0x74 re-arm time, +0x78..+0x7c last-pass flags, +0x38 target list, +0x84 centre, +0x90 radius (re/triggerbox.md is authoritative).

## 3. Proposed patch: host-side OnlineTriggers (SHIP-safe)

Template: klhook/klbotfill.c OnlineRampFire (KLBF_RAMP_VT 0xbc232c, KLBF_RAMP_FIRE 0x45f5d0, klbf_ramp_probe, klbf_ramp_tick; proven on F08).

Design (GUESS on details, mechanism CERTAIN):
1. Toggle `[BotFill] OnlineTriggers=1` (recommended on), logged. Active only when role is host (2) AND not Arcade; in Arcade the game already does it (never double fire).
2. Each tick (reuse the ramp tick cadence): scan the entity table for ZTriggerBox objects (vtable probe like klbf_ramp_probe). Cache the list; rescan on map load.
3. Per box mirror the heap gates: enabled +0x40, not local-only +0x64 handled as the game does, re-arm state +0x50/+0x74, last-pass +0x78.
4. For each live Ally bot (team 2, ZSoldier) read node position, call the game's 0x8c16c0 inside test against the box. Mirror the edge: enter on first inside tick, left on exit.
5. Fire through 0x6ae730 (preferred, goes through sync slot 3 so clients get it) with fallback to 0x45f5d0 as OnlineRampFire does. Set `[box+0x78]=1` so the game's own update does not double fire.
6. Host-authoritative: only the host fires; clients receive via the game's own sync object (+0x6c). Clients run nothing new (online = Arcade 1:1 for outcomes).
7. Log prefix `botfill: trig:` - lines: `trig: on (host, N boxes)`, `trig: bot <name> entered box <id> (<label>) -> fire`, `trig: skipped box <id> (gate: enabled=0/rearm)`, `trig: off (Arcade: game counts allies)`.
8. ZTriggerBox2 (0x626ec0) and the exit trigger 0x6c3d50: ZTriggerBox2 can use the same mirror (GUESS: layout differs, probe needed). The exit trigger MUST stay player-only so bots do not trigger escape for the team (GUESS; Arcade behaviour for bots at exit is a separate question, see open questions). Loot/pickup is not a trigger box path (not covered).

Works on stock FA maps and Dead Men grafts because it keys on box objects, not on map data. Private match: same host path.

## 4. Squad wake (no patch)

Noise-driven, not player filtered (CERTAIN for 0x873c30/0x4e71e0). Online only data fix needed: `--squad-game eAllTypes` so the squads survive 0x7b3790 (existing tools). Bench to confirm bot gunfire wakes squads online (GUESS until run).

## 5. Bench recipe (not run)

kl_solo_test.py with host + 1 join, a stock FA map with a known cop trigger (e.g. F08 where ramp fire is proven, then F01 Subway), `[BotFill] OnlineTriggers=1`, bots only crossing the box (human stays away).
PASS lines: `botfill: trig: on (host, N boxes)`, `trig: bot ... entered box ... -> fire`, then the stage's cop squad spawn line / AITrigger post, 0 faults, client sees the spawn.
A/B: OnlineTriggers=0 -> no `trig:` lines and no wave while only bots enter. Arcade control: same map solo, expect `trig: off (Arcade...)` and the game's own wave.

## 6. Risks

- Double fire (game census + hook): guarded by `[box+0x78]=1` and Arcade-off; GUESS on exact bookkeeping order.
- Box with re-arm timing: wrong +0x74 handling could re-fire every tick; cap one fire per box per N seconds in the hook.
- Wrong vtable probe picks non-box objects: probe by vtable like the ramp code, log count.
- ZTriggerBox2 layout unverified.
- Not benched; SHIP only after a TEST twin passes.

## 7. ZTriggerBox2 and ZOnlineTriggerBox (wk-bots2, 2026-10-28, static, kl2.exe via debug/dasm.py, vtfuncs.py)

Marks: CERTAIN = read in disassembly or in the stock .prp files. GUESS = inferred.

| Class | vtable | update (slot 25) | fire | player gate |
|---|---|---|---|---|
| ZTriggerBox | 0xbc232c | 0x42afd0 | slot 34 0x45f5d0 via 0x6ae730 | CERTAIN, see section 2 |
| ZTriggerBox2 | 0xbc953c | 0x626ec0 (shared with ZOnlineSpeakTrigger, which has its own vtable) | slot 34 0x557820 (post 'AITrigger' word `[+0x46]` to the list `[+0x38]` for the object; `+0x45` one-shot calls 0x66beb0) | `+0x44` = players only. bl=1 for a human (class mask 0x1548c7c) or, only under 0x7f6850, a team-2 actor (mask 0x1547b24 + `[obj+0x54]+4 == 2`). `+0x44` = 0: every object counts, bots too. CERTAIN |
| ZOnlineTriggerBox | 0xbc95cc | 0x49ab90, whole update gated by 0x8df480 | edge starts a delay (0x49ad0f: `+0x54` = float(`+0x40`), `+0x59` = 1); when it runs out the update calls 0x6557b0 -> 0x642f20(`[+0x30]`, 0, 1) = a network message (0x900970 / 0x942b20) | `+0x38` = players only (same census), `+0x39` = also class mask 0x168cddc. CERTAIN |

- 0x8df480 is a second role check like 0x7f6850: roles 0/1 (solo/Arcade) true when `[sm+0x5c] == 4`, role 3 (client) false, role 2 (host) true. So ZOnlineTriggerBox runs on the host and in Arcade only (CERTAIN).
- ZTriggerBox2 update shape: if `+0x64` (delay running): `+0x60 -= dt`, at 0 clear `+0x64`, call `[vt+0x88](+0x68)`; else tracker query (radius `+0x58`, or `+0x5c` when `+0x3d`), per object: bl test, `+0x44` filter, inside test 0x68d030(box, obj) ret 4; inside and `+0x48 == 0` = fire at once (every update while inside, no edge), `+0x48 != 0` = `+0x68 = obj`, `+0x64 = 1`, `+0x60 = float(+0x48)` (0x626ff3). There is no on-leave action, no re-arm field, no ECPS or EFAMPS gate (CERTAIN). `+0x18` bit 0x10 = still in the update list is GUESS (from 0x66beb0 in triggerbox.md).
- ZOnlineTriggerBox: `+0x58` = 'was inside' (recomputed each pass, never written by us), inside test 0x758cb0(box, obj) ret 4 (same shape as 0x68d030).

### Which class starts cop waves and spawns on the stock maps (CERTAIN, F01..F09 `_Main.zip` read from the DD Scenes folder with kl_fa.controllers; F01 is the owner's test slot, so its numbers are the installed build's)
| map | TriggerBox | TriggerBox2 (of which targeting MoneyStack_NNN) | OnlineTriggerBox | OnlineSpeakTrigger |
|---|---|---|---|---|
| F01 | 45 | 241 (125) | 0 | 0 |
| F02 | 24 | 149 (125) | 0 | 0 |
| F03 | 30 | 151 (125) | 0 | 0 |
| F04 | 20 | 135 (125) | 0 | 0 |
| F05 | 13 | 139 (133) | 0 | 0 |
| F06 | 19 | 133 (125) | 0 | 1 |
| F07 | 18 | 138 (133) | 0 | 0 |
| F08 | 18 | 219 (125) | 0 | 0 |
| F09 | 39 | 139 (133) | 0 | 0 |
- Cop waves, door scripts and spawn lists are ZTriggerBox (one-shot -1 boxes with ECPS BOTH / FA_MERCONLY, enter bool set, target lists of 1 to 7). That is the class the existing OnlineTriggers already covers.
- ZTriggerBox2 on the stock maps is the loot stacks' own pick-up box (radius 90, players-only 1, 'AI_TRIGGER_WITH_ACTIVATOR', one per `Specials!DropMoney!MoneyStack_NNN` node) plus location trackers (`..._LOC_Inside/Outside`, 'Open' door proxies on F01/F03/F08). The non-stack ones are not cop spawns. ZOnlineTriggerBox is in none of the nine.
- Arcade (0x7f6850 true) does NOT leave bots out of any of the three: all three census loops use 0x7f6850 to count a team-2 actor as the player (ZOnlineTriggerBox additionally needs the 0x8df480 role gate, true in Arcade). So no Arcade coverage is needed; the hook is host/online only.

### What was built
`[BotFill] OnlineTriggersExtra=0|1|2` (default 0, needs OnlineTriggers non-zero, 2 = dry; either key at 2 makes the extras dry). klbf_trig_scan also collects ZTriggerBox2 and ZOnlineTriggerBox objects (new vtables), klbf_trig_other handles them:
- only boxes with the players-only byte set (`+0x44` / `+0x38`); boxes where every object counts are left to the game (marked dead);
- ZTriggerBox2 boxes whose node name contains MoneyStack or DropMoney are never tracked (the tactics module takes stacks; a second fire could double a grab);
- one fire per entry, the bots must leave before the next, 3 fires per box and round, one-shot (`+0x45`) once; never the exit trigger; host tick only;
- no write to a recomputed field: `+0x58` (ZOnlineTriggerBox) and the ZTriggerBox2 scratch vector are untouched. ZOnlineTriggerBox: write only the delay start (`+0x54`, `+0x59`) and the game's own update fires 0x6557b0. ZTriggerBox2 with `+0x48 == 0`: call slot 34 with the bot's actor; with a delay: write `+0x68`, `+0x60`, `+0x64` exactly as 0x626ff3 does;
- neither class has an on-leave action, so the on-leave skip does not apply (ZTriggerBox keeps it).
GUESS comments are in the code: the `+0x18` bit, bot actor as the object of 0x68d030 / 0x758cb0 (same layout as 0x8c16c0's), the class-mask test via `[obj_vt+0x30]`. Not run live.
