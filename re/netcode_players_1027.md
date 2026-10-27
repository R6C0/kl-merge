# Online FA: how REMOTE players appear and move - defect list (research only, 2026-10-27)

Owner 2026-10-27 00:25: "fix netcode for how players are". RESEARCH ONLY: no code was changed, nothing was launched, nothing was written to the game folder.
Sources read: re/netcode.md (8), re/netcode_fa_review.md, re/netsmooth_solo.md, re/char_online.md, re/online_round_data.md, re/bots_online_sync.md,
re/down_mirror.md, the 10-26 part of re/open_work_log.md, klhook/klsync.c, klcharonline.c, kldown_mirror.c, klnetchan.c, klnetsmooth.c, klonline_read.c, klgun.c
(all read in the main checkout C:/kl-merge/kl-merge; this worktree branch predates those files), the live ini
`C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days/KLHook.ini` (read only) and the bench logs
`<DM>/KL_PortTools/build/klhook/solo/CNR2/inst1|inst2|inst3/KLHook.log` (CNR2, 10-26 16:05-16:12, 3 instances, System Link, stock DD01, TEST out_ramp_1026).
CERTAIN = seen in a log line or in code; GUESS = inferred. No 2-machine Steam run exists for any item below.

## 0. Summary of what is wrong today

Players are replicated by the exe (Net-Z datasets; re/netcode.md 8): position/heading/camera/aim go out at most every 100 ms, only when the sender's own prediction
of the receiver is off by >20 units / >30 heading units, with a forced refresh every 2 s; the receiver steers the body by replicated stick input plus an offset and
rebuilds the heading raw from the int16 every frame (0x600eb0). The mod adds three layers on top, and the layers fight each other:

| layer | module | live ini today (Dog Days/KLHook.ini) | state |
|---|---|---|---|
| looks (hero/mask/outfit) | klcharonline.c | `[CharOnline] Enable=1 Unique=1 Steam=1 Udp=1` | on, UDP proven on one PC, Steam never proven |
| heading smoothing | klnetsmooth.c | NO `[NetSmooth]` section (Enable defaults 0) | off |
| send-rate tuning | klnet.c | NO `[Net]` section (Tune defaults 0) | off: stock 100 ms / 20 units / 2 s |
| down/flop/get-up | kldown*.c | `[Down] Online=1` etc. | local part on, mirror to peers unbenched |
| cops sync | klsync.c | NO `[Sync]` section (Share/Compare/Track default 0) | off; bench inis turn it on |

## 1. Ranked defect list

### D1. NetSmooth's private vtable blinds every module that tests `[player] == 0xbb45f4` (looks, flop mirror, online crew rows) - CERTAIN, found in logs
Evidence:
- klnetsmooth.c:354-368 copies ZFFPlayer's vtable and points the first dword of each REMOTE player at the copy (`kns_ours()`); the local player is not swapped.
- klcharonline.c:129 `klco_table` counts entities only while `klh_rd32(pl) == 0x00bb45f4` and `break`s at the first mismatch. klcharonline.c:316
  `if (!klco_table(...)) { klco.since = 0; return; }` runs BEFORE the publish and listen code (lines 320-380).
- CNR2 inst1 (host): `16:07:48.560 netsmooth: 15 remote player object(s) swapped` then `16:07:48.748 charonline: my body: entity 0 of 1 (518d3640, type 2)`:
  the table shrank from 16 to 1 (own body is entity 0 and is not swapped, entity 1 is). Result: the host logs ZERO `applied to body: peer` lines for the whole round
  although it heard `peer on entity 1 chose Kane`. The host never shows the client's hero/mask.
- CNR2 inst2 (client): the peers' looks were applied at 07:48.8-07:49.3 and `netsmooth ... swapped` came at 07:49.345, i.e. AFTER; from then on a client whose entity 0 is
  a swapped remote gets cnt = 0, `klco_table` returns 0 and charonline does nothing at all (no re-announce, no re-apply when slot 137 puts the seat model back at the next round / respawn).
- Same raw test elsewhere: kldown_mirror.c:66, :144, :191 (the flop mirror only accepts a replica whose vtable is 0xbb45f4: with NetSmooth on, every replica is refused),
  kldown.c:766-769, :2447, :2078, klonline_read.c:195 (`klor` crew/score rows skip a player whose vtable is the private one), klcopsquad.c:113.
  kldown.c:2061 already knows the problem ("a vtable swap of the player breaks the KLD_PLAYER_VT checks") and only avoids it for one case.
- Latent today only because the live ini has no `[NetSmooth]`. The moment the owner turns smoothing on to fix the jitter, looks and downs break. The benches (CNR2) ran with NetSmooth on, so every online looks bench since 10-26 16:00 was partly blind.
Fix: one helper in klhook.c next to `klh_avt` (line 660): `klh_pvt(o)` returns 0x00bb45f4 when the dword is `kns_ours()`, else the dword; replace the 10 raw tests above with it
(klcharonline.c:129 also needs `n` to keep counting past non-players only if the first 16 slots are all ZFFPlayer: keep the break). NetSmooth cannot avoid the swap
(slot 393 lives in hashed .rdata, a SHIP build must not write it).
Owner: klcharonline.c, kldown.c, kldown_mirror.c = kl-merge-c9 (they make the edit); klhook.c helper + klnetsmooth.c + klonline_read.c + klcopsquad.c = lead / free.
Bench: CNR2-style 2 instances, `[NetSmooth] Enable=1`, `[CharOnline] Enable=1 Log=1`: pass = on BOTH instances `my body: entity K of 16` (not 1 / not 0), and
`applied to body: peer on entity J` appears AFTER the `remote player object(s) swapped` line; then Char=9 vs Char=14 in the two inis and a screenshot of each window showing the other's model.

### D2. Remote players are shown with the stock 100 ms / 20 unit / 2 s dead-reckoning and a raw heading: position jitter and "spinning" - CERTAIN mechanism, effect never judged
Evidence: re/netcode.md 8.2-8.5 (min interval 100 ms, position tolerance 20, heading tolerance 30/1024 turn, forced refresh 2 s, linear 2-sample extrapolation 0x992f10,
receiver builds heading raw from int16 each frame, hypotheses H1 spin on a lost "stopped turning" packet, H3 jitter). Live ini: no `[Net]` and no `[NetSmooth]` section, so
all of it is stock. `[NetSmooth]` is absent from klhook/KLHook.ini and from tools/kl_mod_options.py (0 occurrences), so the owner has no menu toggle for it either.
NetSmooth was only proven to RUN (H3 2026-10-23: `placed 1720 skipped 0` on the client, write path via B->vtbl[0x8c] works); "whether it LOOKS better is the owner's call" was never asked.
Fix (all existing code, only keys and rows): (a) add `[NetSmooth]` to klhook/KLHook.ini and a kl_mod_options.py row "(recommended off until benched)"; (b) `[Net] Tune=1 TuneClient=1`
with PlayerMs=33 RefreshMs=250 PosTol=5 AngTol=10 (the numbers netcode.md 11-B suggested; only the SENDER's values matter, so both players need the build); (c) CamYaw=1 for the upper-body spin
(re/netsmooth_camyaw.md: heading and camera yaw are separate datasets; NetSmooth Enable alone leaves the camera/aim yaw raw). Do D1 first.
Owner: klnet.c / klnetsmooth.c / ini / options = free (not in the c9 list).
Bench: two instances, scripted mouse flick on one (`mouse` steps in the solo ini), `[NetSmooth] Probe=1 Log=1` on the other: compare per-frame yaw deltas of the remote body with
Enable=0 vs 1 (max deg/frame, count of frames above 20 deg); position: log the remote body place every frame and report max |step| / median step while the sender walks straight (stock should show 100 ms staircase).

### D3. Nobody measures remote HUMAN position error (klsync compares cops only) - CERTAIN
klsync.c compares/shares ZFFActor slots (`klsy_human` excludes players; header lines 1-60). CNR2 inst2 shows `sync: vs host: 49 actors compared ... p50 0 p90 0 worst 0`: the cops
are fine (the 10-26 puppet/track work did its job) but the same logs say nothing about the 2-15 player bodies. So "positions of players" is the one thing nobody has a number for, and D2 cannot be accepted without it.
Fix: extend the sync probe to ZFFPlayer entities (table order = same index on all peers, same assumption as charonline) - host Share lists the player places (own body + each remote's as the host SEES it),
the client logs `sync: players vs host: slot i d=..` for REMOTE bodies only, excluding the client's own. Read-only, new key `[Sync] PlayerProbe=1`.
Owner: klsync.c = kl-merge-c9 (describe, do not edit). Bench: CNR2 recipe below, walk one instance in a square for 60 s, expect p50 < 20, p90 < 60 units at 250 ms list age.

### D4. Looks (hero/mask/outfit) have only ever been proven on one PC over UDP; Steam lobby member data is a GUESS path - CERTAIN (code) / GUESS (works)
Evidence: re/char_online.md 3 marks the ISteamMatchmaking008 slot numbers 16/17/23/24 as GUESS; the lobby id is read from `[svc+0x35e]` with `[svc+0x35c]` as exists flag (klcharonline.c:312-314);
UDP broadcast 255.255.255.255:27414 reaches LAN/System Link only (re/down_mirror.md "Carriers"). The 10-26 hidden-pointer fix (klcharonline.c comment at the GetLobbyMemberByIndex call) was found by reading, never run in a Steam lobby.
Owner symptom 10-26 20:45 "no skins online" was a missing ini section; the first real Steam run after that is still outstanding. Also GUESS: the game leaves the lobby when the round starts, which would silence the Steam channel for the whole round
(re/down_mirror.md, same carrier question for klnetchan `klx_msg`).
Further weakness: the announcement is `i<table index>c<wardrobe char>m.o.` and the receiver resolves `c` against ITS OWN `KLWardrobe.ini` for the CURRENT level key (klcharonline.c klco_look: `wardrobe = klc_w.on && !_stricmp(key, klc_w.key)`). On the 9 stock maps there is no wardrobe unless the stock slot carries one,
so the log line `wants X ... has no such model` is expected there and the stock seat model stays (re/char_online.md 5 "Without a KLWardrobe.ini ... no Dog Days hero choice").
Fix: (1) bench the Steam path (needs 2 Steam accounts or the owner + a friend; not possible on one PC); until then keep UDP as the only claimed carrier and say so in the options row. (2) Make the announcement carry the HERO NAME ("Kane") instead of the wardrobe index so a receiver with another wardrobe layout (stock map vs DM map, different n) maps by name. (3) For stock maps, ship `KLWardrobe` with the F01..F09 slot stocks, or log once per round that looks are unavailable (it is silent today beyond one `toldNoWar`).
Owner: klcharonline.c / klnetchan.c / klmm.c = kl-merge-c9. Bench: 2 instances on stock DD02 (not DM) with Char=9 / Char=14: expect `applied to body: peer` on both or an explicit "no wardrobe" line.

### D5. The online flop / get-up mirror is built but its prerequisites are open; peers see the STOCK fall - CERTAIN (stated in the notes)
Evidence: re/down_mirror.md "Remaining GUESSES" 1-5 (replica prone movement honours the pool pairs, pool EXCLUSIVE vs SHARED for two bodies of one hero model, same table index on all peers, writable replica channel);
messages ride UDP 27416 (LAN only) or Steam `klx_msg` (internet, unproven); over Steam internet only `OnlineFlopMirrorAssume=1` (hash) can work and is default off. OPEN: 10-26 20:30 log "peers still see the stock fall, a single hit bigger than his health still kills".
Interaction: D1 makes the mirror refuse every replica when NetSmooth is on (kldown_mirror.c:66 raw vtable test). Pools: two Parkers share `[pl+0x78]` (likely SHARED), so the mirror would refuse and the fix would be a private pool copy (not built).
Fix order: D1, then bench with ReplicaProbe=1; if SHARED, build the private pool copy for replicas; keep Assume=0.
Owner: kldown*.c = kl-merge-c9. Bench (re/down_mirror.md checklist): `[Down] Enable=1 Log=1 ReplicaProbe=1 Flop=3 OnlineFlopMirror=1` on both; victim goes down (script `shoot`/console kill), expect `ARMED replica` + `MIRROR OK`, screenshot of the copy lying down.

### D6. Weapon looks / DM guns and the gun shop never appear on remote players - CERTAIN (by design)
klgun.c:408-409 returns outside Arcade and `if (kl_online()) return;` ("no variant-byte write in a network session"), so modded gun looks are Arcade-only; a peer sees only what the exe replicates (BuyWeaponPack: primary/secondary/suit as int8 ids, re/netcode.md RMC list), i.e. stock Dog Days ids. A weapon the buyer owns that the receiver's build does not know shows as the stock model or nothing (GUESS: no case observed).
Not a bug while the owner's rule is "Dog Days guns reused", but it must be written down because "buying characters / grades" will have the same boundary: whatever the mod adds locally is invisible to peers unless it is announced like the looks (klx_look channel).
Fix: none now; if DM guns go online, extend the klx_look string with a weapon id and apply on the replica like klc variant. Owner: klgun.c is free; the channel is c9's.

### D7. Peer announcement is unauthenticated and keyed by table index; "Unique" (each character once) is only resolved locally - GUESS/limit
- klcharonline.c:109 `klco_heard` trusts any UDP packet on port 27414 from anyone on the LAN (anyone can restyle any entity). Low risk on a friends LAN; fix = include the Steam/session id or drop packets not from a known session peer address.
- `klco_effective` (lines 197-216) resolves duplicates identically on all modded peers only if all see the same announcements; a peer that joins late or misses 2 s broadcasts shows another Unique result for several seconds (re/char_online.md 5). An unmodded peer is an unannounced entity wearing the stock seat hero and can duplicate a wardrobe pick (two Kanes) - Unique does not count the stock seat models.
- The table index is assumed equal on every peer (re/char_online.md 2: GUESS, "order of the level's ZFFPlayer entities"). In CNR2 it held (host `entity 0`, client `heard peer on entity 0`), but the C&R roles differ per seat (client own body = entity 8, type 3) so a 2-human + 14-AI table is not proof for 9 humans.
Owner: klcharonline.c = c9. Bench: three instances with two of them Char=9 -> expect `unique: entity N asked for Kane ... shown as X` on all three and identical on-screen results.

### D8. Own body is found late on a client: ~9 s of a new round without announce - CERTAIN (log)
CNR2 inst2: `16:07:40.058 own body NOT found (gamedata sel 255 -> pl 00000000 ...)` repeated, found `16:07:49.312 ... entity 8 of 16 found by gamedata slot`. For those ~9 s the client publishes nothing and applies nothing (peers' looks too: apply is after `klco.ownIdx` etc. only for own; peer apply still runs but needs the table). The "master scan" fallback (7 in char_online.md) printed the table `R0 o0 nb` for all 16 entries: R is [P+0x274c] = 0 at that moment, so the DDL objects were not bound yet - the scan cannot work before binding.
Fix: publish what is known (the table index is not needed to BROADCAST the choice when the packet also carries the Steam/UDP sender id; or retry at 250 ms and stop logging after the first line). Also apply peers' looks even when the own body is unknown (they are independent). Owner: klcharonline.c = c9.

### D9. Names above players / the crew list online - open, not a mod bug yet
re/online_round_data.md "Open" 3: the stock FA name text object is not located; names in the replacement crew list come from `klonline_read.c` and need `[HUD] OnlineCrew=1` (added to the live ini 10-26 18:58). klonline_read.c:195 has the D1 vtable test, so with NetSmooth on, the swapped players have no row. Nothing else known; no 2-machine proof of names exists.
Fix: after D1, run the crew/score read with 2 humans and compare names with the lobby list.

### D10. Hygiene found while reading (not sync defects)
- The live ini contains `[Online]\nRead=1` TWICE (lines 1089-1093): a second run of an install script appended it again (GetPrivateProfileInt reads the first, harmless, but the "twice-run" claim in the install note was about `[Down]`/`[HUD]` keys). Dedupe in the installer.
- Template klhook/KLHook.ini lacks `[NetSmooth]`; kl_mod_options.py has no NetSmooth row and no `[Net]` row for the send-rate keys (rule: every feature a toggle).

## 2. Top 5 fixes (in the order to do them)

1. D1: `klh_pvt()` for the 10 raw `== 0xbb45f4` tests (klcharonline.c:129 first). Without it NetSmooth cannot be turned on without losing looks, flop mirror and online crew rows. c9 edits klcharonline/kldown*, lead adds the helper.
2. D2: add `[NetSmooth]` (Enable, CamYaw, Probe) to klhook/KLHook.ini + a kl_mod_options row, and `[Net] Tune=1 TuneClient=1 PlayerMs=33 RefreshMs=250` rows; bench Enable 0/1 with the yaw/step metric. Free files.
3. D3: player-position probe in klsync.c (`[Sync] PlayerProbe`) so D2 has a number. c9.
4. D4/D8: looks transport: name-based announcement, publish before the own body is known, a stock-map "no wardrobe" line, then the first real Steam-lobby run. c9.
5. D5: after D1, bench the flop mirror with ReplicaProbe; if pools are SHARED build the private pool copy for replicas. c9.

## 3. Bench recipe (2 instances, System Link, no Steam needed) - queue.py style

Runner: `C:/kl_build_1024/lan_1025/queue.py` takes `<tag> | --hook <TEST out folder> --n 2 --secs 300 --ini1 <host.ini> --ini2 <join.ini> --shots 60-300:60` lines from `queue.txt`
(it takes LIVE.lock, calls `tools/kl_solo_test.py ... --tag <tag> --force`, logs to `<tag>_run.txt`; logs land in `<DM>/KL_PortTools/build/klhook/solo/<tag>/inst1|inst2/KLHook.log`).
Do not start it while another process holds LIVE.lock or the owner plays; this research did not launch anything.

Inis (copy `C:/kl_build_1024/lan_1025/BOSM_DD01_host.ini` / `_join.ini`, drop the `[Bots]`/`[BotFill]` blocks, keep `[Expansion] Page=0`, `[Lobby]` rows):
```
; host (inst1)                      ; join (inst2)
[CharOnline]                        [CharOnline]
Enable=1 Udp=1 Steam=0 Log=1        Enable=1 Udp=1 Steam=0 Log=1
[Character]  Char=14 Mask=1 Outfit=22  [Character]  Char=9 Mask=1 Outfit=22
[NetSmooth]  Enable=1 Probe=1 Log=1 CamYaw=1   (same on both; second run Enable=0 as control)
[Net]        Log=1 Tune=1 TuneClient=1 PlayerMs=33 RefreshMs=250 PosTol=5 AngTol=10   (third run: Tune=0 control)
[Sync]       Probe=1 Share=1 (host)  Compare=1 (join)
[Down]       Enable=1 Log=1 ReplicaProbe=1 Flop=3 OnlineFlopMirror=1
[HUD]        OnlineCrew=1 Names=1
```
Queue lines (TEST build must contain the D1 fix; until then expect the D1 failure signature below):
```
PL1 | --hook C:/kl-merge/kl-merge/klhook/out_<build>_test --n 2 --secs 300 --ini1 C:/kl_build_1024/lan_1025/PL1_host.ini --ini2 C:/kl_build_1024/lan_1025/PL1_join.ini --shots 60-300:60
PL0 | (same, [NetSmooth] Enable=0 [Net] Tune=0)  <- control
```
Script (kl_solo_test `steps`/`mouse`/`key` in the ini as the BO* benches do): on both, wait for state 0x19, host walks a square 60 s, client flicks the mouse 360 degrees twice, host presses the down trigger once.

PASS lines (grep the two logs):
- D1: both `charonline: my body: entity K of 16`; no `of 1` / `of 0` after `netsmooth: .. swapped`; `applied to body: peer on entity J` on BOTH after the swap line; shots show each other's hero.
- D2: `netsmooth: ... placed N` growing, `skipped (not a pure yaw)` low, no fault; metric from the probe: max remote-yaw step per frame and median positional step (control run for comparison).
- D3: `sync: players vs host:` p50 < 20, p90 < 60 (after the probe exists).
- D4/D8: `heard peer on entity J chose X via UDP` within 3 s of the round start; own body found within 2 s (today 9 s).
- D5: `ARMED replica ... MIRROR OK`, `ReplicaProbe ... EXCLUSIVE|SHARED`.
FAIL signatures already seen: `entity 0 of 1` (D1), `own body NOT found` > 3 s (D8), no `applied to body: peer` on the host (D1).
Not provable on one PC: the Steam lobby channel (D4) and any Steam-internet latency behaviour; keep those marked unproven in options labels.
