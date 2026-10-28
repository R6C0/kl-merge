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
