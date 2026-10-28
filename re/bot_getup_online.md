# Bots help a downed human get up, online (gap #3, wk-getup-1028)

Status: implemented default OFF (`[BotFill] OnlineGetUp=0`, "(recommended off)"), static research only, NOT RUN live. Compiles in the SHIP dll; pure logic has a self-test (klhook/klgetup_test.c).

## 1. How Arcade does it (CONFIRMED from the repo sources and notes, read-only)
- The Arcade "help" is NOT stock code. It is the mod's own `klhook/kladren.c` (re/adrenaline.md, adrenaline_anim.md), working on the crew records (`klb_snap`):
  - Rush: the nearest free AI heister (same floor, within BotRange, not carrying, not boarded, van not called) is sent to `BotAnimNear` (2 m) from the downed human with `kle_order2` (0x760e50, `rec=-1`, `told_soft=1`), re-ordered every 2.5 s while it is not there.
  - Pull: while the human lies, a bot by him floors his mash meter / adds presses (meter floor 3.0, lie-tick pull `[[soldier+0x4b8]+0x14]`), so the get-up comes faster.
  - A bot kneel animation, share and traitor logic ride on the same records.
- The stock heal path (ZHealTactic 0xbd027c -> ZHealPlayerBehaviourGoal / ZSoldierHealGoal) needs player state 5, which exists only in session mode 2 (co-op). Arcade and Fragile Alliance never reach it (CONFIRMED in re/adrenaline.md).
- Online, kladren.c does not act: its crew records are the Arcade AI heisters, and the hook-filled online bots (klbotfill.c) are not on them. So a downed online human lies until he gets up alone (re/bot_gaps2_1028.md gap 3).

## 2. Online anatomy used (addresses)
- Human down state: `D = [player+0x2948]`, `[D] == player`, `ds = [D+4]` (0 up, 1 lying, 2 falling, 3 getting up). CONFIRMED on the owner's body (kldown.c, kladren.c). GUESS: a REPLICA's D on the host is run by the same 0x76a450 (re/downed_online.md says a replica sets `[D+0x21]=1`), so the host can read a remote human's state. If the read fails the host pass never sees "down" and does nothing (safe).
- Bot order: `kle_order2` (klescort.c:660, 0x760e50), exactly as `klbf_esc_pass` uses it. CONFIRMED path (OnlineEscort uses it live, wk-move).
- The mash meter: `kld_o.h.meter` (kldown.c `kld_o_step`, `[Down] MashHold`, need 8). The stock GettingUp message (0x6cd720) already replicates the rise to the other machines, so no new message is needed.

## 3. Implementation (klhook/klbotfill.c, klgetup_logic.h, kldown.c)
Ini `[BotFill]`: `OnlineGetUp=0|1|2` (2 = dry, log only), `OnlineGetUpRange=2500` cm, `OnlineGetUpRate=3.0` presses/s, `OnlineGetUpNear=400` cm. Needs `OnlineHost=1`, `OnlineTactics=1`, and `[Down] MashHold` on (the meter is the hold meter). Set it on every machine.
- HOST `klbf_gu_pass` (once a second after the escort pass): for each living human whose D state is 1/2, pick the nearest free bot (phase 0/1, tally 0, not guard-walking, same floor within 4 m height, within Range; none while the van is called/waiting, vstate 1..5). `kle_order2` it to 2 m from the human; repeat every 2.5 s while it is not within 3 m; `guHum/guAt` hold the puppeteer's stack order and the escort pass off that bot (3.5 s, refreshed). Released when the human is up. All in `__try`.
- DOWNED MACHINE `klbf_gu_rate_now(pl, now)` called from `kld_o_step`: a living Ally bot with a soldier, not itself down (`[actor+0x64c]`), within Near of this machine's own feet and 2 m of height adds Rate/s to `kld_o.h.meter` (capped at need) while he lies. Census cached 500 ms.
- Pure functions (`kgu_*`) and a kldh_step integration (helper alone frees him in about 5 s; no helper and no press stays held) in klgetup_test.c.

## 4. CONFIRMED vs GUESS
CONFIRMED: Arcade help is the mod's (not stock); stock heal unreachable in FA; kle_order2 usable online for bots (OnlineEscort); GettingUp replicates the rise; build compiles, pure logic passes.
GUESS (a live bench decides): (a) the host reads a remote human's D state; (b) a bot ordered to 2 m by kle_order2 actually walks there and stays while down (the escort pass relies on the same); (c) own feet `[pl+0x460]` stay within 4 m of the body while down on the downed machine; (d) a bot freezing while the puppeteer is held does not trip the stuck/stall counters (klbf_ot guards use `ordered`, which is refreshed on each order); (e) the bot's `[actor+0x64c]` is the NPC down flag online too.

## 5. Not ported / risks
- No bot kneel/revive animation, no share, no traitor logic online (Arcade has them; this is the order and the meter only).
- MashHold off or OnlineMashSpeed (kld_o.omash) mode: the meter does not exist, the pull does nothing; only the rush happens.
- A bot held by `guAt` stops looting for as long as the human lies; if he never rises (a down with no get-up) the bot stays until released 3.5 s after the D state leaves 1/2.
- If both a human and the bot are in the lift/stair area, 4 m height tolerance may pick a bot on the next floor; Range 2500 limits it.
- All default off; with OnlineGetUp=0 no code path changes (klbf_gu is 0 at every call).

## 6. Bench
Two instances online FA (host + joiner), ini on both: `[BotFill] OnlineHost=1, OnlineTactics=1, OnlineGetUp=1`, `[Down] MashHold=1`. First `OnlineGetUp=2` (dry) on the host: log lines "getup: seat N IS DOWN" prove guess (a) when the joiner is shot down. Then `=1`: get the joiner downed away from every bot and check: "getup: bot S sent to seat N", the bot walks to him, "bot is by seat N", and on the joiner "a bot stands X cm from this machine's downed body: the mash meter gets +3.0 a second", then the joiner rises in about 3 s without pressing. Release lines "bot released" after he is up. Watch the host log for FAULT and the bot for stalls (guess d).
