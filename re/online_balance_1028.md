# Online [Balance] bot factors on the HOST (wk-bal2, 2026-10-28)

Key: `[BotFill] OnlineBalance=0|1` (default 0, recommended off). Code: `klhook/klbalance.c` (klr_bo_*), pure logic `klhook/klbalonline.h`, test `klhook/klbalonline_test.c`.
Host only, no network message, no second detour: it rides the private-vtable slot-423 hit wrapper (klr_cb_hit) that OnlineCopToBot installs on every bot.

## What Arcade does
The victim's routine 0x61a980 (ZFFActor slot 423) multiplies a hit by one float of the per-level record R = [0x168d7c0]+0x6ac+L*0x70:
+0 CopToCrew, +4 CrewToCop, +8 CopToYou, +c YouToCop, +10 CrewToYou, +14 YouToCrew, +1c CrewOffStage. Ramp holds a number at/above (kind 1: CopToCrew,
CopToYou, CrewToYou) or at/below (kind -1: CrewToCop, YouToCop) the stock level row; YouToCrew is as given. Tough = NPC maximum health x f (health rows).
YouToCrewFar is approximated by rewriting +0x14 per pass. Online 0x7f6850 is false for roles 2/3, so these paths are skipped.

## What online does now (OnlineBalance=1)
Attacker kinds: ZFFPlayer (vtable 0xbb45f4; police byte +0x2723) or ZFFActor (team at [[att+0x54]+4], 2 = Ally = bot).
| hit | factor | done |
|---|---|---|
| cop / guard -> bot | CopToCrew (/ Tough) | yes: becomes k of the existing OnlineCopToBot path (CopToCrew 0 = token 0.0001) |
| human heister -> bot | YouToCrew x range / Tough | yes (a) |
| human police -> bot | FedMirror=1 FedToCrew else YouToCrew; FedMirror=0 YouToCop | yes |
| bot -> cop / guard | CrewToCop | yes (b), needs the cop on the private vtable (OnlineBalanceCops=1) |
| range sponge | YouToCrewFar, NearAt/FarAt (default 8/35 m), 0.02 steps, real per-hit distance | yes (c) |
| Tough | divisor 1/f on hits on bots | yes (c) |
Point-blank steps (scale > 1.0001 and <= the OnlinePointBlank want) are left alone.
Ramp: online has no Arcade level, so `[BotFill] OnlineBalanceLevel` (1..11, default 1, GUESS) picks the stock row Ramp holds against; Ramp=0 ignores it.
Also read: Risk row, the keys CopToCrew/CrewToCop/YouToCop/YouToCrew (0..20), FedToCrew, YouToCrewFar (0.05..1), Tough (0.25..10), even with [Balance] Enable=0.
OnlineBalance wins over `[Balance] Online=1|2` for a hit it has a factor for; the old path still gets hits OnlineBalance leaves.

## Not done (and why)
- CopToYou, CrewToYou, CrewToFed: the victim is a human ZFFPlayer (another vtable); this wrapper never sees it.
- YouToCop on cops, CopToYouFar, HeadShot: no cop-side or human-side wrapper; bot-vs-bot (left alone); CrewOffStage (no heist stages online); Tough on cops and blasts.
- Risk: many modules compare a raw ZFFActor vtable (kladren, klcopsquad, kldown, klescort ...). Putting cops on the private table is exposed to that; klh_actor_priv2 covers klh_avt / klsync only.
  Isolate with OnlineBalanceCops=0. GUESS: remote human position read at pl+0x460.
- Nothing was run live (peer bench held the game). Built SHIP and TEST dlls and the off-game test only.

## Bench recipe (only when the game is free)
Ini (KLHook.ini):
```
[BotFill]
OnlineHost=1
OnlineTactics=1
OnlineCopToBot=5
OnlineBalance=1
OnlineBalanceCops=1
[Balance]
Risk=2
Ramp=0
YouToCrew=0.5
CrewToCop=0.5
YouToCrewFar=0.5
Tough=1.5
```
Run an online FA round as host with bots, shoot bots at 5 m and at 40 m, let bots shoot guards. Grep KLHook.log:
- `balance: OnlineBalance ARMED` (config line) and `OnlineBalance factor ARMED` once per factor
- `OnlineBalance YouToCrew APPLIED` and `OnlineBalance CrewToCop APPLIED` (first 3 each)
- `cop(s) / NPC(s) now on the private table`
- `OnlineBalance 30 s:` counters: scaled > 0 for YouToCrew and CrewToCop, refused/noop/nopos small, range mean < 1 for far shots
Pass: the lines above, 0 faults, bot deaths slower than with OnlineBalance=0, no crash when cops die or squads move. If it crashes or cops/squads behave oddly, rerun with OnlineBalanceCops=0.
