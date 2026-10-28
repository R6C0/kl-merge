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

## 7. LIVE FINDING GU3 (10-28) and the down beacon (wk-getup2-1028, `[BotFill] OnlineGetUpBeacon`)
Finding (bench GU3, DD04 online, 2 seats, 0 faults, `OnlineGetUp=1`): the JOINER logged `down: YOU ARE DOWN ... health 420.0 of 550.0, down state 2`, but the HOST never logged `botfill: getup: seat N IS DOWN`. So guess (a) of section 4 is FALSE for a joiner: on the host the replica's D state never leaves 0, because kldown.c's down mirror refuses the replica (`ReplicaProbe ... pool SHARED with other bodies - the mirror REFUSES`, host counter `1 refused`). The host half (rush) therefore never fires online; the downed-machine half (bot near the own body adds to the meter) needs a bot that only the host can order there.

Design: the downed machine tells the host. Same channel family as KLSYB (loot) / KLSYV (bot voice): UDP 27415, broadcast, `klsy.sock`, magic `KLSYD`, 32 bytes (layout in klgetupbeacon.h): version, seat, flags (bit0 down), seq, tag (FNV of the scene name), sender tick T, own feet [pl+0x460].
- Client (`klgb_own`, called from kldown.c's pass for the own body, only role 3 in a round): down at once, then every 1 s with a new seq; on getting up ONE new seq sent 3x, 100 ms apart. Dying counts as "up" (alive=0).
- Host (`klgb_host_rx`, from klsy_tick, role 2): drains the socket (skips everything not KLSYD, e.g. its own list broadcasts), drops a wrong level tag, a repeat or older seq, keeps one record per table index (`klgb_seats`, klbotfill.c). An up beacon clears at once; a down lapses 3 s after its arrival.
- `klbf_gu_pass`: a seat is down if the replica says so (old path) OR a fresh down beacon does (and the replica is alive: hp > 0). The place is the replica's feet when readable, else the beacon's. Log `seat N IS DOWN (...) (beacon)`. With OnlineGetUp=2 the host only logs (dry). Everything after "down" (rush, hold, release) is the existing code.
- Identity: the sender's index in the session player table (`klco_table` entry whose entity is the own body; fallback `klco_find_own`). The table index is the convention klcharonline.c announces looks with and down_mirror.md item 3 assumes (CNR2 / CharOnline: host `entity 0` = client `heard peer on entity 0`); with 2 humans + AI this is evidence, not proof for 9 humans. So the host CHECKS it: if the replica at that index is farther than 1500 cm from the beacon's place the index is not trusted and the nearest heister replica within 600 cm is used (GUESS thresholds), logged once per seat; none near = beacon ignored. An unreadable replica place is trusted.
- Ini: `[BotFill] OnlineGetUpBeacon=0|1` (default 0, recommended off), effective only when OnlineGetUp is 1 or 2; set on every machine. Mod options entry `onlinegetupbeacon`.
- Pure part + test: klgetupbeacon.h, klgetupbeacon_test.c (pack/unpack, seq dedupe, staleness, send schedule, tick wrap, seat check). Not run live.
- Limits: UDP broadcast, so it needs the same path as OnlineLooks/OnlineVoice (LAN, two instances on one PC); a Steam-relay-only pair would not get it (the same limit as KLSYL/KLSYB). A down beacon with the host seat's own index is never sent (only role 3 sends).

Bench recipe: see the commit message / the worker's return (GU3 ini + `[BotFill] OnlineGetUpBeacon=1`, `OnlineGetUp=1` on both). PASS lines: client `getup: beacon SENT down seq 1 seat S`, host `getup: beacon rx seat S down seq 1` then `botfill: getup: seat S IS DOWN (...) (beacon)`, `getup: bot B sent to seat S`, `bot B is by seat S`, joiner `a bot stands X cm from this machine's downed body`, then client `beacon SENT up`, host `beacon rx seat S up`, `seat S is up / out of play`, `bot B released`.
