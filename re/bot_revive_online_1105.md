# Online revive of a downed AI heister (c9 2026-11-05, workflow wmae5p048: design + skeptical review)
Phase 1 spec below is the REVIEWED one (the design's view-4 index plan was refuted). Read-only analysis, GUESSes marked.

## Design (superseded where the review says so)

DESIGN: online revive of a downed AI heister by a human (Arcade parity). Read-only analysis; nothing was edited, built or run. Paths are under C:\kl-merge\kl-merge\klhook\. Every GUESS is marked.

**0. Facts that shape the fix**
- Arcade revive is kladren.c `kad_tick` (1063-1237). The helper search is at 1163-1226 and skips non-local humans at 1169, the "human that is not the local one: online later" branch.
  - Use key: `kad_use_held` (125-139), which reads `GetAsyncKeyState(0x45)` with the game window in front.
  - Prompt text: 1189-1203. Pull: 1221-1224.
  - Anim: `kad_an_try` (628) and `kad_an_inject` (645-655).
- The "get-up" is not a call. It is the data write `[dnd+0x14] = tick+2`.
  - `dnd = [soldier+0x4b8]`, valid only if `[dnd+4]==soldier`.
  - The game's own ZDownNotDeadNPC goal then stands the bot up.
  - The tick clock is `[0x00dd2640]+0x48`, in 1/1024 s.
  - `klbd_speed(rec, rate)` (klbotdown.c:244) already does this write, but no live caller uses it (only klbotdown_test.c scenario 6). The lie write at klbotdown.c:496-513 and the 1.4 s helper-yield check at :499 show how klbotdown itself treats a helper.
- Online bots come from the host-only census (`klbd_census` :290, `klbd_online_host` :316, `klbd_ov_fill` :338, `klbd_online_snap` :360, `klbd_online_view(who 0..3)` :377). Online has no crew records, so klbotdown uses pseudo records in `klbd_ovs`/`klbd_o`.
- Host-only consumers follow the pattern in klshield.c:130-170 (`klbd_online_view(2,...)` plus `kle_human`, klescort.c:519).
- Live ini: [Adrenaline] Enable=1 Anim=1 Prompt=1 Range=4 Meter=4.0 NeedUse=0. [BotDown] Enable=1 LieSeconds=15 FreeSeconds=10 DownsMax=3. [Down] OnlineBotDown defaults to 1.

**PHASE 1: host human revives a bot (host only, no network)**

*Sites*
- New pass `klbd_revive_pass()` in klbotdown.c, called at the end of `klbd_pass` (:406-581) when `sn.n>0`. It runs on the host game thread only, inside the existing `__try`/`klh_data` guards. Alternative: a new klbotrevive.c included after klbotdown.c and before kladren.c, ticked next to `klbd_tick` (:393).
- Enlarge `klbd_ovs` by one slot (new `who` 4 = "downed only"). Then `klbd_online_view(4,...)` returns bots whose `klbd_is_down(rec)` is true.
- Host human: `kle_human` (klescort.c:519). Host-only gate: the same host/round check `klbd_online_host` (:316) uses (role 2 = host is a GUESS, state 0x19).
- Reviver conditions:
  - the human is the local player (`klh_slot_player_mine`), alive, not himself down and not police;
  - `kad_use_held()` is true;
  - the bot is within `OnlineReviveRange` on the XZ plane and |dy| <= 2 m (feet from the bot actor and the player);
  - the bot's `[actor+0x64c]` down byte is set and `dnd` is valid.
- Accumulate help ms like `k->hm`, with `MinHelp`. Then pull with `klbd_speed(rec, 1+(Rate-1)*kltt_get(...))`, or a direct `[dnd+0x14]=tick+2` write through `klh_data`.
  - Bound the write: only if the existing value is greater than now+2 ticks, and only once per bot per down.
  - This also serves the Arcade 1.4 s helper-yield rule, so klbotdown does not rewrite the lie tick against the helper. Set `klbd_o[i].helped_until` the way :499 expects. GUESS: field name, to be matched to the real struct.
- Prompt: reuse `kad_say` (119-158) and the text built at kladren.c:1189-1203, fed from the online view (new `kad_prompt_for(rec_name, pct)`). It needs the announcement element (0x468430). GUESS: that element exists in an online HUD. Check it like kad_say does, and fall back to log-only if it is missing.
- Anim (separate switch): `kad_an_try` (628) needs the local ZFFPlayer and the Heal_wounded slot. Online it should work for the host's own body only. GUESS: the inject is replicated as an ordinary animation (ZFFPlayer replicates its own anims, so clients likely see the kneel). Keep it off until benched (`OnlineReviveAnim=0`).
- Skip the Arcade share/mark records online (Arcade-only); log "would pay".

*Reuse*: `klbd_online_view`, `kle_human`, `kad_use_held`, `klbd_speed`, `kad_say`, `klh_data`/`klh_rd`, `kad_an_guard` (restores the FPU control word), `kltt_get`.

*New ini keys* ([Adrenaline], all default 0, "(recommended off)" until benched; 2 = dry log only)
- `OnlineRevive=0|1|2`
- `OnlineReviveRange` (default = Range, 4)
- `OnlineReviveRate` (default = Meter, 4.0)
- `OnlineReviveMinHelpMs` (default 400)
- `OnlineRevivePrompt=0|1`
- `OnlineReviveAnim=0|1`
- `OnlineReviveLog=1`
- Bench-only: `OnlineReviveBenchHold=1`. The host treats "key held" as true when a downed bot is within Range. This is needed because klauto's scripted DirectInput E does NOT trigger `GetAsyncKeyState` (see the bench plan).

*Log lines* (prefix `adren-online:`)
- `adren-online: init OnlineRevive=%d range=%.1f rate=%.1f anim=%d`
- `adren-online: bot REC (actor %08x) DOWN seen, lie tick %u`
- `adren-online: bot REC helped by HOST seat %d, %d ms, dist %.1f m`
- `adren-online: bot REC PULL lie tick %u -> %u` (the live line); `adren-online: DRY would pull bot REC` (mode 2)
- `adren-online: bot REC UP after %.1f s (helper)`
- `adren-online: bot REC refused: <far|dy|self down|no dnd|not host|callable>`
- `adren-online: prompt shown / prompt skipped (no announcement element)`

*What the client sees*
- Nothing is sent. The bot stands up through the game's own goal on the host, and the host's DDL_ZFFActor replication carries pose and position.
- So the client sees the early get-up exactly as well as it sees the bot's down. GUESS: the down pose and byte replicate (re/downed_online.md Way 4). If they do not replicate, the client sees nothing of either. Verify with `[Sync] Compare=1`.
- The client gets no prompt in phase 1.

*Crash risks*
- Host game thread only. Never call from the netchan or UI thread: gate on `game_thread`, as klbk_tick does.
- Check `[dnd+4]==soldier` immediately before the write (a stale `dnd` after a bot death or despawn). Use `klh_data` writes, and wrap the pass in `__try` with the FPU control word restored (`kad_an_guard` style).
- x87 state: do float math before the guarded block, not inside the `__try`.
- Write only once per bot per down. Never write if `dry`.
- Do not touch `[actor+0x64c]` or the health object (+0x5fc) from this pass. Only the lie tick is written.
- A bot that dies in the same tick: the existing `klbd_callable` code-byte checks (:160) stay valid, and the pass does nothing when it fails.

**PHASE 2: client human revives a bot (client to host request)**

*Carrier*: klnetchan (klnetchan.c / klnetchan_logic.h). Packet `KLNC1;sid;role;ent;seq;type;payload`, payload at most 127 printable ASCII, 16 handlers, 3x repeat dedupe. It runs over UDP broadcast 27416 (LAN/System Link) plus the Steam lobby member data `klx_msg`. Copy the client-to-host request/ack structure of klucchide.c (~185-215, 280-345; UREV resend + timeout) and klhire_online.c (request/ack plus host validity check).

*Messages* (new types, handlers registered with `knc_want`/`knc_on`; sender uses `knc_send`)
- Client to host `RVRQ`: `seat|px|py|pz|holdms|digit`. Own feet in cm, hold time so far, and optionally the bot's look digit (klbotvoice names bots by a look digit). Resend every 500 ms while E is held. Stop after 2 s of no hold or a timeout of 4 s.
- Host to client `RVAK`: `ok|digit|pct` or `no|why`. This drives the client prompt, and its absence means no prompt (the dry fallback).
- Client-side hold sampling: a `kad_use_held` branch added at kladren.c:1169. For the non-local, non-host case, change "continue" to "send RVRQ".

*Host handler* (runs on the game thread inside `knc_tick`, which must be verified; GUESS)
- Validate:
  - the host is in round 0x19 with `OnlineRevive>=1`;
  - the `ent` from the packet header is a used seat in the rules records (`klbr_rec_member`-style used-record test);
  - the claimed position is within 600 cm of that seat's replica feet. This is the GU3 lesson (re/bot_getup_online.md): do not trust indices or the host's view of a joiner's down state. Reject if it fails;
  - the sender is not police and not himself down. GUESS: the host cannot see a joiner's down state (GU3), so skip this check and log "unverified".
- Choose the nearest downed bot (view 4) within `OnlineReviveRange` of the claimed position. Apply the same accumulation and pull as phase 1, keyed per (seat, bot). Cap one active helper per bot.
- Rate limit: ignore more than 8 requests per second per seat. Reply `RVAK`.
- Trust model is LAN among friends (a forged packet can pull a bot up early, so the damage is bounded). Internet (Steam, no lobby) has no proven carrier, the same limit as KLSYL/UREV.

*Client prompt*: on `RVAK ok`, show the Arcade text through `kad_say`. The client knows the bot is down only from the host's reply. Reading the client's replica `+0x64c` is a GUESS, so use the reply instead.

*New ini keys* (default 0, "(recommended off)", 2 = dry log)
- `OnlineReviveClient=0|1|2`
- `OnlineReviveClientPrompt=0|1`
- `OnlineReviveRepeatMs` (500)
- `OnlineReviveMaxDist` (600 cm)
- Host and client must both have the key on.

*Log lines*
- Client: `adren-online: client RVRQ sent seat %d bot digit %d hold %d ms`; `adren-online: client RVAK ok/no <why>`.
- Host: `adren-online: host RVRQ from seat %d pos %.0f/%.0f/%.0f replica dist %.0f -> accepted/refused <why>`; the same PULL/UP lines as phase 1, with `by CLIENT seat %d`.

*What the client sees*: the bot's get-up via replication (the same GUESS as phase 1), plus the RVAK prompt. The client's own kneel anim is off here (`kad_an` needs the local body, which is valid on the client too, but it is a separate GUESS, so keep `OnlineReviveAnim=0`).

*Crash risks*: the handler never touches game memory except through the phase-1 pull, which is guarded. Payload parsing is length-bounded (127). Strict numeric parsing: reject NaN or out-of-range. Never block the netchan thread.

**Bench plan** (klauto TEST build, "(TEST)", about 2.59 MB; a SHIP build has no klauto and the bench hangs)

*Forcing a bot down* (klbench_down.c's `[Bench] SelfDown*` only downs the LOCAL player, so it cannot down a bot)
- Natural fight: DM03 or DD05 (bots go down at DownPct 30 in fights, and `downs_max` is 3). This is not deterministic.
- Recommended new bench key `[Bench] BotDownAt=<s in state 0x19>`: at that second the host drives bot N (look digit) to 25 % health on the same health object klbotdown reads, so the existing census downs him. GUESS: the health write path. Alternative: lower `DownPct` to 100 in the seat ini so the first check downs the bot.
- Pair it with `LieSeconds=15`, `FreeSeconds=10`.

*Phase 1 script* (host seat 1 only; 2-seat map such as DM03)
1. `waitstate 0x19`, then `settle`.
2. `ents` (find the downed bot's position), then `goto x z` to within 3 m.
3. `pos` to log; `down E`, `wait 2500`, `up E`. Plain scripted E will not set `GetAsyncKeyState`, so run with `OnlineReviveBenchHold=1`, or find the real Use bit `[player+0xa54]` bit 2 (GUESS). There is no `hold` command: use `down`/`wait`/`up` (klauto.c header 1-260).
4. Grep the host log: DOWN seen, helped by HOST, PULL, UP after (expect UP within about 2.5 s of the first hold, against a 15 s lie).
5. Control run: same script without E. Expect UP only after about 15 s (LieSeconds), proving the pull caused the early get-up.

*Phase 2 script* (host + client seat, `[Sync] Compare=1` on)
1. The client does `goto` near the downed bot, then `down E`, `wait 2500`, `up E` (needs the same client-side hold override as above: `OnlineReviveBenchHold` on the client to force RVRQ).
2. Grep: client `RVRQ sent`, host `RVRQ ... accepted`, host `PULL ... by CLIENT`, client `RVAK ok`.
3. Negative tests: the client 20 m away (expect `refused: far`); spoofed position with a wrong `pz` (expect `refused: replica dist`); the client holds E but the bot is not down (expect `no downed bot`).
4. Check the client's `[Sync] Compare` for the bot's pose around the UP time. If the pose stays down, the get-up does not replicate (GUESS fails), so a phase-2 follow-up needs an explicit get-up replicate path.

*Acceptance*
- 0 faults, 0 asserts, the live autotest `RESULT:` clean exit (`python tools/kl_autotest.py`), and `python tools/kl_tests.py` passes before the build.
- Dry first: `OnlineRevive=2` logs "would pull" with 0 writes, across DM03, DD05 and DD03 (the three BS-bench maps).

**Open GUESSes (summary)**
- Role 2 means host at `[sm+0x54]`.
- The down pose and byte (`+0x64c`) replicate to clients through DDL_ZFFActor, and so does the early get-up.
- A `knc_on` handler runs on the game thread.
- The announcement element (0x468430) exists in an online HUD.
- `[player+0xa54]` bit 2 is the real Use bit.
- The `klbd_o` helper-yield field name (:499).
- The health-object bench write.
- The host cannot see a joiner's down state (GU3), so the sender's down state is unverified.
- The client's own kneel anim.

**Do first**: Phase 1 with `OnlineRevive=2` (dry), then 1 (live) in the host-only bench; leave Phase 2 until Phase 1 passes. A SHIP build ships both keys at 0.

## Review (authoritative)

**VERDICT: PARTLY REFUTED.** The intent is sound: the get-up is a data write to `[dnd+0x14]`, and `klbd_speed` and `klbd_lie_step` are safe to reuse on the host. But the Phase 1 plumbing would act on the wrong bot, several parameters and expectations are wrong, and the Phase 2 client hook sits where it can never run. Read-only; nothing was built or run, and the replication question is not settled.

**Defects and fixes**

1. **Pseudo-record index mismatch (the most serious).**
   - The plan adds a `who` 4 slot to `klbd_ovs`. The `klbd_ovs[4]` tables are separate from `klbd_o`, so a record number from `klbd_online_view(4)` does not index `klbd_r[]`.
   - `klbd_speed(record, rate)` (klbotdown.c:244) reads `klbd_r[record]`: its actor, `down`, `soldier`, `spd_last`. The online pass fills `klbd_r[i]` from `klbd_o` (klbotdown.c:414 ff.).
   - With a view-4 index, `klbd_speed` would return 0 (`!b->actor`) or hit another bot's state.
   - Fix: drop view 4. Put the reviver inside `klbd_pass`'s per-bot loop, in the `if (b->down)` branch after the `lie_done` block. There `b`, `r->actor`, `s`, `dnd`, `tick` and `i` are all in hand and consistent.
   - This needs `[Down] OnlineBotDown=1`, which the live ini has, and `!klbd.odry`. `klbd_speed` already returns 0 when `klbd.dry` is set.

2. **`helped_until` does not exist, and nothing needs it.**
   - klbotdown.c:499 is only the test `(long)(cur - b->tick_down) >= 1400`, inside the one-shot `!b->lie_done` block.
   - `klbd_speed` sets `lie_done=1` itself (:254). If it runs before the part's own LieSeconds write, the part never writes (:498). If it runs after, nothing rewrites.
   - Drop the "set helper-yield field" step.

3. **"Pull to tick+2 once per bot per down" is not Arcade parity.**
   - Arcade's help (kladren.c:1220-1224) is a continuous speed-up: `kad_lie_step(cur, tick, dt, 1+(Rate-1)*kltt_get(helper, KLTT_ADREN))`. `klbd_lie_step` (klbotdown.c:134) is the same step. A tick+2 write is the Anim "shot" (kladren.c:644 ff.), which needs `MinHelp` and the kneel.
   - Use `klbd_speed(i, rate)` every tick the helper qualifies.
   - **Rate is `[Adrenaline] Rate`** (default 3.0, kladren.c:1267). `Meter` is the downed human's mash-meter floor and is irrelevant to a bot. The live ini has no `Rate` key, so the rate is 3.0.
   - Online trait multiplier: `kltt_bot(r->actor, KLTT_ADREN)`, not `kltt_get(hp, ...)`. klbotdown.c:477 already makes the same distinction for `KLTT_REVIVE`.
   - The bench expectation "UP within about 2.5 s" is wrong. With `LieSeconds=15` and rate 3, the lie shrinks to about 5 s. With the lie pulled early, a quicker get-up needs the Anim shot, which is out of Phase 1.

4. **Parameters.**
   - `MinHelp` is `kad.minhelp`, default 1.0 s, not 400 ms. In Arcade it gates the share, the prompt and the Anim shot, not the speed-up.
   - Live `Range=4` is the helper range. The code default is 2.5.
   - `Meter=4.0` is not a rate; drop `OnlineReviveRate=Meter`. Do not add `OnlineReviveRange`, `Rate` or `MinHelp` keys; reuse `kad.range`, `kad.rate`, `kad.minhelp`.
   - Gate on `kad.on` as well. `kad.usekey` and `kad.range` are only set under `[Adrenaline] Enable`.

5. **`NeedUse=0` live means the key is not needed.**
   - kladren.c:1172 demands the key only when `kset_v[3]` (the NeedUse row) is on. With `NeedUse=0`, proximity alone helps.
   - Mirror that: `if (kset_v[3] && !kad_use_held(pl)) skip`. `OnlineReviveBenchHold` is then unnecessary.
   - For `NeedUse=1` in a TEST build, scripted keys are readable via `kla_key_held(0x12)` (DIK_E). klhud.c:1625-1633 forward-declares and uses it the same way for Tab. Scripted DirectInput E does not reach `GetAsyncKeyState`, so `kad_use_held` is false in the bench. Add `kla_key_held(0x12)` to the online branch only, not to `kad_use_held`.

6. **Include order.** klbotdown.c (klhook.c:837) comes before kladren.c (:841), so `kad_use_held`, `kad.*` and `kad_say` are not visible there.
   - Forward-declare `static int kad_use_held(DWORD pl);`, which is legal for a static defined later in the same translation unit. Alternatively, keep the code in klbotdown.c behind small `#ifndef` hooks, as the file does with `KLBD_CALL`.
   - klbotdown_test.c includes klbotdown.c alone, so it needs stub macros.
   - `kle_human` (klescort.c:519, included at :767) is visible.

7. **Phase 1 prompt and anim.**
   - `kad_say` needs `kset_v[2]`, `klan_ready(KLAN_ADREN)`, `klu.on` and a valid OSD announcement element (kladren.c:148). Whether that exists on a host in an online round is unproven. The "fall back to log-only" plan is right.
   - The `KAD_AN_TRY` path takes a `kad_r[i]` record `k`, which does not exist online. Defer the anim to a later phase. Keep `OnlineReviveAnim` out of Phase 1.

8. **Local-human gating.** Replicate kad_tick's reads of the local player: `gd+0x898` selection, the `police` byte, the player's own down state (`dn[sn.human]` there), and the 2 m vertical test (kladren.c:1180). `kle_human` only gives the player and his feet.

9. **Replication of the get-up is still a GUESS.**
   - re/downed_online.md line 91 says the down pose replicates as "GUESS". Nothing in the repo confirms it.
   - klsync.c was not read, so I cannot say whether `[Sync] Compare` shows `+0x64c`.
   - Cheapest check: on the client, add a read-only probe of the replica actor's `+0x64c` and a log line.
   - Interim: if clients never see the down, they also see no revive.

10. **Phase 2.**
    - The client hold branch at kladren.c:1169 can never run online. `kad_tick` returns at :1071 when `!klr_arcade`. A separate client-side tick is needed.
    - Resolved GUESS: `knc_tick(game_thread)` dispatches handlers, and the API note says game thread only. Handlers do not run on the netchan thread.
    - GU3 still holds: the host cannot trust a joiner's down state or indices. Validate the position against the replica feet, as planned.
    - Do not start Phase 2 before Phase 1 passes.

11. **Bench.**
    - `[Bench] BotDownAt` does not exist. Do not build it for Phase 1.
    - `[BotDown] DownPct` is clamped to a maximum of 60 (klbotdown.c:612), so "DownPct 100" is impossible. Use `DownPct=60` in the seat ini or fight on DM03/DD05.
    - Confirmed klauto ops: `down`, `up`, `waitstate`, `settle`, `goto`, `pos`, `ents`, `wait` (klauto.c:1380-1468). No `hold` op, as stated. Check the key table in `kla_key` for "E".

12. **Key-name clashes.** Grepping all klhook/*.c found no existing `OnlineRevive*` or `BotDownAt` names. `[Adrenaline]` already has `Enable, Anim, Prompt, Range, BotRange, Rate, Meter, MinHelp, NeedUse, UseKey, PromptRange`.

**Corrected Phase 1 spec (host human revives a bot)**

*Keys.* In `[Adrenaline]`, add only `OnlineRevive=0|1|2` (0 off, 1 live, 2 dry log-only; default 0, "(recommended off)" until benched) and `OnlineReviveLog=0|1`. Reuse `Range`, `Rate`, `MinHelp`, `NeedUse`, `UseKey`, `Prompt`. Read the keys where klbotdown.c reads its own (near :612) with `GetPrivateProfileIntA`.

*Function `klbd_revive_one(i, b, r, dnd, tick, now, dt)`* in klbotdown.c, called at the end of the `if (b->down)` branch of `klbd_pass`. It is called only when `online && klbd.orev` and `dnd` is non-zero (`[dnd+4]==s` is already verified at :429). The branch returns early when `klbd.dry`, so mode 2 needs a variant before that `continue`.
1. Float math first, outside any `__try`.
2. Check `kad.on`, a host in round (`online` already means this), and `kle_human(&pl, feet, node)`.
3. Refuse reasons: not police, local player not down, `|feet.y - botpos.y| <= 2 m` (kladren.c:1180), XZ distance `<= kad.range * 100` using `kle_node(klh_rd32(r->actor+4), pos, 0)`.
4. If `kset_v[3]`, require `kad_use_held(pl)` or, in a TEST build, `kla_key_held(0x12)`.
5. Accumulate `b->hm += dt*1000/1024`, in a new `DWORD rv_hm` in `struct klbd_rec`. Reset it at the down transition (:462 reset line).
6. If `rv_hm` is at least `MinHelp` ms, write `klbd_speed(i, 1+(kad.rate-1)*kltt_bot(r->actor, KLTT_ADREN))`. In mode 2, log only and skip the write.
7. `klbd_speed` already guards `dnd`/soldier, uses `klh_data`, and does no FPU work beyond the step. Do not touch `+0x64c` or `+0x5fc`.

*Log lines* (prefix `adren-online:`, only when `OnlineReviveLog`)
- `init OnlineRevive=%d range=%.1f rate=%.1f minhelp=%.1f needuse=%d`
- `bot rec %d (actor %08lx) down; lie tick %lu`
- `bot rec %d helped by HOST %lu ms, %.1f m`
- `bot rec %d PULL lie tick %lu -> %lu (rate %.2f)`, or `DRY would pull`
- `bot rec %d refused: far|floor|self down|police|no key|no dnd`, once per down per reason
- `bot rec %d UP after %.1f s, helped %lu ms`: add to the existing "IS UP" line at klbotdown.c:~470.

*Prompt (optional, after the pull works).* Call `kad_say(100+i, 2500, "ADRENALINE: getting <name> up - keep holding", 2.4f)` from klbotdown.c. Bots have no wardrobe name, so use "your crewmate". Skip it if `kad_say` returns without speaking. Fall back to a log line `prompt skipped`.

*Bench.* Use a TEST build (klauto, "(TEST)", about 2.59 MB) and the pqq-style quick kit on DM03 or DD05 in the host-only bench.
- Seat ini: `[BotDown] DownPct=60 LieSeconds=15 FreeSeconds=10`, `[Adrenaline] NeedUse=0 OnlineRevive=2`, then 1.
- Script: `waitstate 0x19`, `settle`, `ents` to find the downed bot, `goto x z` to within 3 m, `pos`, `wait 6000`. With `NeedUse=1`: `down E`, `wait 6000`, `up E`.
- Run A (revive on): expect "helped", "PULL" and "UP after" at about 5-6 s, against 15 s without help.
- Run B (control, `OnlineRevive=0` or standing far away): expect UP at about 15 s.
- Run C (`OnlineRevive=2`): "DRY would pull" lines and 0 writes.
- Acceptance: 0 faults, 0 asserts. Run `python tools/kl_tests.py` before the build, extend klbotdown_test.c with an online-pseudo-record scenario, and finish with `python tools/kl_autotest.py` giving a clean `RESULT:`.
- If no bot goes down naturally within 120 s, the bench is inconclusive, not failed.

*Replication check (before Phase 2).* Add a client-side read-only probe of the replica bot's `+0x64c`. Compare the client-seen get-up time with the host's "UP" line.
