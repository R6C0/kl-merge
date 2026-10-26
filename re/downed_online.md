# The down / revive extras online: what the game already shares, and five ways to get the mod's parts there

2026-10-26, cloud session, on the owner's "find ways to sort it". Static reading of kl2.exe 0490 (debug/kl.py + capstone) plus the
repo's notes (re/netcode.md, re/player_down.md 14.6, re/hook_netcode_audit.md, re/arcade_online_parity.md). **Nothing here ran online.**
VERIFIED = disassembled at the address given; GUESS = inferred, named as such.

## 0. The verdict in one paragraph

The premise "the downed state is not shared: the host's game and the other players' games each decide it separately" is only half
right, and the half that is wrong is the useful half. The stock game ALREADY shares a human's down state and his health, and it
decides both on ONE machine: the machine that owns the player (his own PC). His own damage routine fires the down trigger, his machine
performs the fall and tells everyone with `RMCDownNotDead_SetDowned`; his one press of GET UP tells everyone with
`RMCDownNotDead_GettingUp`; his health goes out as `RMCUpdateHitPoints` + the unreliable hit-point dataset; a bullet from another
player reaches him as `RMCReceiveHit(damage)` priced on the SHOOTER's machine and applied on his. So a rule that each machine applies
to ITS OWN player (the trigger numbers, how long he lies, how fast he rises) needs no new net message at all: stock replication
carries the result, provided every peer runs the same hook with the same numbers - which the expansion already requires (everyone
needs the map files). What stock does NOT share is (a) the mash meter / how long the get-up CLIP plays on the other screens, (b) rule
state the host should own (adrenaline revive, traitor-until-revive), (c) anything about the AI crew other than what the actor's own
replication carries. The five ways below answer those three, cheapest first; two of them need no code on the wire.

## 1. What kl2.exe says (read today)

| fact | where | verdict |
|---|---|---|
| Every RMC wrapper routes on `0x9425a0(this)` ("am I the master of this DDL object", `[this+0x14]` owner vs the local id) after `0x905460(sm)` (in a session) and `[sm+0x15d]` (connected). | 0x846d90, 0x6cd720, 0x8759e0, 0x807220 | VERIFIED |
| **SetDowned** wrapper 0x846d90(`rWhatDownMe:u16`): master -> SEND (stub 0x6557f0, message 0x950dd0 + 0x953890); not master (= a replica of another player's object) -> `D = [[this+0x540]+0x2948]`, `[D+0xf0] = 0x8ccde0(ref)`, call **0x76a450 (go down)**. Called on the master by 0x76a450 itself (0x76aa38, the game's own fall) and on the replicas by the dispatcher 0x658b60 -> stub 0x4cdf00. | 0x846d90, 0x4cdf00 | VERIFIED |
| **GettingUp** wrapper 0x6cd720: master -> SEND (stub 0x5d2c20); replica -> `[D+0x21] = 1` (the replica's state machine then starts its own get-up at stock speed). Sent from the get-up start 0x7180b0 (0x7180bc -> 0x8b74d0 -> jmp 0x6cd720), i.e. at the ONE press kldown.c describes. | 0x6cd720, 0x7180b0 | VERIFIED |
| `m_iDownNotDeadFlags` is a reliable u16 dataset of `DDL_ZFFPlayer` at **+0x4a4** (registration 0x741b70; `m_iClientIndex` at +0x484, `m_iFlags` next). | 0x741da9..0x741dcf | VERIFIED |
| **ReceiveHit** wrapper 0x807220: master -> apply here (builds a hit record from the message: the two refs through 0x8ccde0, `m_iDamage` sign-extended, headshot byte, zero momentum, then `[this+0x2a0]` slot 0x698); not master -> SEND. Reached from the actor vtable slot 421 (vt+0x694 = 0x69f900, pointer 0xbb4240): in a session, when the victim's object is not local (0x86a150 / `[+0x5b4]` 0x86f0c0) -> 0x4b5690 -> 0x807220, else slot 422 (0x698, apply) directly. The damage in the record was computed BEFORE slot 421 on the machine that fired. | 0x807220, 0x69f900 | VERIFIED (structure); the two "is it local" tests not read line by line |
| **UpdateHitPoints** wrapper 0x8759e0(`u16`): master -> SEND (stub 0x8dbf20); replica -> `0x4aa8b0(player, float hp)` = `0x61efd0([player+0xa48], hp)` (set health). Sender 0x57fae0 (the master's own health bookkeeping, through 0x7acde0). Receive stub 0x6a18f0 from the dispatcher. | 0x8759e0, 0x57fae0 | VERIFIED |
| `RMCPullHimDown(rPlayer)` wrapper 0x8f5160 (stub 0x7ff190); `RMCOnDownedYellowcardKill` (NetClient 0x4c3120 / 0x722540); `RMCTrackDownNotDeadCoopKill` (0x8e7f20): exist, not read further. | strings 0xb79978, 0xb7a378, 0xb393bc | located |
| An AI actor (`DDL_ZFFActor`) replicates `m_GeneralData` (ASH current / target state, move set number, preferred state, hit points), `m_iActorState` (reliable), ragdoll and attach data, plus `ActivateAnimSegment(header, con, start, end, fAnimSpeed)` and ReceiveHit RMCs. The AI is simulated on one station (the host, by the repo's reading). | re/netcode.md 590-595 | from the notes |

Consequence for the notes: re/player_down.md 14.6 "a remote player's down would be lost" and re/arcade_online_parity.md row 14 "needs a
state in the replicated actor" describe the hook's current Arcade-only build, not a gap in the game. The game HAS the state and the
messages. What re/private_match.md left as GUESS ("who prices a hit") is now: the shooter's machine prices, the victim's machine applies.

## 2. The three things stock does not carry, and the way for each

### Way 0 (no wire, exact parity): move the mash BEFORE the get-up, not into it   <- recommended first step

Today's design (kldown.c part 1) slows the get-up CLIP and speeds it with each press. Online the owner's clip speed is his alone:
the others saw `GettingUp` at his first press and play the stock 0.8 s clip, so for up to ~2 s he is standing on their screens while
he still lies on his. Re-cut the rule so the MASH IS THE LYING PHASE: while `[D+4] == 1` the hook holds the game's own GET UP byte
`[D+0x2b]` at 0 (a data write of the kind kldown already does, every frame) and counts the presses itself (the raw key / pad read it
has); when the meter is full it lets ONE press through, and the stock one-press get-up runs at stock speed and replicates exactly
(0x7180b0 sends `GettingUp`; every replica plays the same clip). The owner's words - "they have to spam like breaking out from a human
shield to get up so the animation is slow, gets faster whilst you spam" - keep their feel: he is down longer when he does not mash,
and under fire he is exposed exactly as long on every screen. Dead Men's get-up clip can still replace the stock clip on EVERY peer
(if the replacement is a file in the expansion folder, each machine plays its own copy for the replica too: GUESS until klcdying's
clip route is re-read for online). Cost: the clip no longer speeds up;
the meter decides WHEN it starts. Work: kldown.c part 1 rewritten (smaller than it is), the Arcade gate replaced by "my own player" +
`klb_level`, a HUD meter already exists. Risk: low (the GET UP byte is the game's own input product, already read by the hook; while he is down 0x84dda0
already zeroes the Cover byte it comes from, so holding it is a write of the same kind). GUESS to confirm: that 0x47cd80 reads
`[D+0x2b]` and nothing else to start the get-up. Open point to read: whether `[D+0x2b]` is read anywhere else than 0x47cd80.

### Way 1 (no wire): the same hook on every peer applies the per-player rules to its own player

The trigger numbers (`[T+0x268]` health per cent, burst, window, cooldown, DownHealth) are tuning the OWNER's damage routine reads for
his own fall. Each peer writes them for itself; stock replicates the fall. `klr_arcade` is replaced by "a session of game type 4 or
Arcade, my own local player, not police, same ini on every peer"; the hook logs its numbers at round start so a mismatch is visible in
every log. This is the UCC "only down" rule's natural home too (section 3). Risk: a peer without the hook (or with other numbers)
plays stock for himself only; nothing desyncs, because only his own fall is decided by his numbers.

### Way 2 (small side channel, proven pattern): broadcast the meter for the mash-in-the-clip variant

If the owner wants the clip itself to speed up with the mash, the replicas need the meter: a `KLDN1` broadcast in klsync's shape
(own UDP port, e.g. 27416, 100 ms, `{slot, state, meter}` from the downed player's machine; klsync.c:922-932 is the sender to copy),
and the remote hook applies kldown's speed write to the REPLICA's channel (the replica has its own `D` and `M`: 0x846d90's receive
path uses `[[this+0x540]+0x2948]`, so kldown's code runs on it unchanged, fed by the received meter instead of local presses). Proven
live for klsync (SP1h, UCC2, CNR1 on System Link). Limit: broadcast = LAN / System Link; over Steam the only side path built is lobby
member data (5 s period, too slow for a meter) - so for internet play Way 0 is the one that holds.

### Way 3 (host-owned rules through the owner's machine): adrenaline revive and traitor-until-revive

Rule state belongs on the host (it owns the rules Sv and the money). The ACTIONS go through the owner's machine, never the host's
copy of the victim: a host that writes a client's replica is overwritten by the owner's next update (parity audit, authority gate).
Two messages do it, both in patterns the hook has: `host -> owner "revive slot N (health H)"` and `host -> all "slot N is traitor until
he revives slot M"`. The owner's hook raises its OWN player's health (the write kldown already makes on its own player) and stock sends
`UpdateHitPoints` to everyone; the traitor mark goes through the game's own `RMCBecomeTraitor` (stub 0x7c9d90 / wrapper 0x745da0,
host authoritative) or the hook's own flag until that call is read. Transport: klsync's host-only broadcast for LAN now; for Steam,
either the lobby member data (acceptable for a revive: one event, not a stream) or a Steam P2P channel (not built). Alternative
without any channel: `RMCReceiveHit` with a NEGATIVE `m_iDamage` reaches the owner's apply path - whether slot 422 clamps or heals is
NOT READ (GUESS, 10 minutes of reading at 0x458880 decide it). Prefer the hook channel: the owner's hook knows the rule and can show the
HUD at once.

### Way 4 (host only, replication does the rest): the AI crew's down and dying

Online the AI heisters exist only on the host (klbotfill); klbotdown / klcardown / klcdying write host-side and the clients see the
actor through `DDL_ZFFActor`: the pose through `m_iASHCurrentStateId` / `m_iMSPrefferedState`, the health through `m_iHitPoints`, the
ragdoll through `m_RagdollData`. GUESS: the actors' down-not-dead pose is an ASH / move-set state and so replicates by itself; the
first online bot bench with klbotdown on says so (watch a downed bot on the client with `[Sync] Compare=1`). Dead Men's get-up clip on
a bot can even be driven with speed from the host: `RMCActivateAnimSegment(..., fAnimSpeed)` exists for actors. These parts also need
the online crew record (the Heist-only records at rules+0x348 do not exist online: parity row 12): klbotfill's census is that record
online, so they attach to it, not to ZGameRulesHeist.

## 3. The Undercover Cop's "his hits only DOWN heisters" (re/ucc_design.md decision 2) on this picture

The UCC is a human; his bullets on another human are priced on HIS machine and sent as `RMCReceiveHit(m_iDamage)` to the victim, whose
own damage routine runs the down trigger with the victim's own tuning. So the rule has two halves and lives on two machines:
1. **On the UCC's machine (the shooter prices):** cap each of his hits on a heister so the victim's health cannot reach 0: the hook
   knows the victim's replicated health (`[[replica+0x540]+0xa48]`, kept by `UpdateHitPoints` / the unreliable dataset, so up to one
   update stale) and writes the hit record's damage before slot 421 sends it - or, with no code patch, scales it the way
   klbotfill's private ZFFActor vtable scales `[hit+0x18]` (re/online_bot_damage.md). The cap must also leave the hit >= `[T+0x274]`
   (MinHit, 20) or it never books into the down window.
2. **On the victim's machine (the owner decides the fall):** the stock trigger wants health <= 40 % AND 120 damage inside 1 s (or 80
   under 20 %). A capped UCC can never deliver the burst, so with stock numbers the heister just bleeds to the cap and stands. The
   victim's hook must make "a hit from the UCC at or under HealthPct floors me" true: kldown part 2's Burst=1 / MinHit write - per
   machine, on his own player, Way 1 - gated on the attacker being the hidden UCC if the owner wants ordinary shots unchanged (the
   attacker is in the hit record: `rWhatDownMe` / the ReceiveHit owner ref).
So the two things any workflow on this rule has to check are exactly these: (i) that the capped damage still books into the window on
the victim's machine (MinHit) and the victim's trigger fires with the hook's numbers - the fall then replicates by itself; (ii) that the
cap on the shooter's side is applied BEFORE the send (slot 421) and uses a health figure fresh enough that a burst of three hits does
not overshoot to a kill (the unreliable dataset is per frame; `UpdateHitPoints` reliable is the fallback). Both are host-independent:
the host never prices a human's bullet.

## 4. Order of work and what each step proves

1. Read `[D+0x2b]`'s other readers and 0x458880's negative-damage handling (an hour, static).
2. Way 0 in kldown.c (the mash as the lying phase) + Way 1's gate change; bench: 2 instances System Link, DM01, one player floored by
   police: both screens show the same lying time, the get-up starts on both within one frame of the owner's final press.
3. Way 4: klbotdown on for a BOS bench; the client log says whether the downed bot's pose replicates.
4. Way 3: a `KLRULE` host->owner line for revive / traitor (klsync shape), adrenaline on top; bench with the host as the reviver first.
5. UCC cap (section 3) on a UCC bench: a 3-instance System Link round where the hidden UCC empties a magazine into a heister.
