# Arcade features in Quick Play / Ranked / LAN (System Link) / Private: audit and plan (2026-10-25)

Owner: "we must implement all of the arcade features into quick play ranked and LAN". Static audit of klhook/*.c plus the data-side
features; NOTHING RUN. CERTAIN = read in code/comments at the place named; GUESS = inferred. "online" = `kl_online()` (klhook.c: role 2 host /
3 client, or game type 4 with a rules object that is not ZGameRulesHeist 0xbd3514; the online rules are `...FragileAllianceSv 0xbd2eb4` /
`Cl 0xbd31e4`).

## 0. Why almost everything is silent online (one cause, three layers)

1. **The data gate.** Every Arcade part reads the round through `klb_read` / `klw_who_now` / `klr_arcade` / `klinv_player`. All of them demand
   session type 4 AND a `ZGameRulesHeist` rules object with the crew records at `[rules+0x348]` and the `ZHeistScore` at `[rules+0x5f8]`. Online
   the rules class is another one with another layout (0x74-byte records at `[rules+8]`, 12 client seats), so those readers answer "no round"
   by their own vtable test. CERTAIN. Nothing crashes, nothing happens.
2. **The authority gate.** Online the game replicates players, AI actors (`DDL_ZFFActor`), inventories (`DDL_SInventoryItems`), the rules
   datasets (money, state). A part that changes such state on one machine desyncs or is overwritten. So the existing parts also stop at
   `kl_online()` (klcam lean/unstick, klfreeclimb start, kljoin, klgun, klinv, klshop, klunstick, klpm_arc, music/ambience/stinger).
3. **The seat gate.** There is no seat for an AI heister online (re/bots_online_fill.md 6).

What can be done per feature therefore falls in four classes:
- **L (local cosmetic)**: affects only this machine's screen/speakers. Needs only the data gate lifted (a read-only online snapshot).
  Desync risk: none. Done where listed.
- **H (host authoritative)**: the value lives on the host and is replicated. The host's hook may write, clients get it through the game.
  Needs the host's online rules layout (not decoded except the base class) -> not done blind.
- **C (needs replicated data)**: both sides must agree; needs a new net message, not available to a SHIP hook.
- **X (no)**: needs a seat/records the online rules do not have.

## 1. The table, easiest / most visible first

Columns: Arcade = what it does offline. Host/Client = behaviour today. Class as above. Status: DONE (this change, default OFF, own toggle),
OK (already works online), READY (small step, not blind-safe), NEEDS (work named), NO.

| # | Feature (file, key) | Arcade | Online today (host / client) | Why gated | What online takes | Desync risk | Status |
|---|---|---|---|---|---|---|---|
| 1 | Music jukebox (klmusic.c, `[Music] Enable`) | mood by round state, money, stage | silent / silent (`kl_online()` return) | the mood needs the Heist records | local read of the online rules state: CALM at state 0x19, ACTION by `AfterSeconds` or money (OnlineCrew), END on leaving | none (L) | DONE `[Music] Online=1`; state 0x19 online is a GUESS, `online:` log proves it |
| 2 | Ambience bed + one-shots (klambience.c) | same phases | silent / silent | same | same snapshot | none (L) | DONE `[Ambience] Online=1` |
| 3 | Event stingers (klstinger.c) | Dead/Down/Betray/Loot/Open/Last30/Loud | silent / silent | events come from records and the van timer | Loud by timer, Loot by money delta (OnlineCrew); the record events (Dead, Down, Betray, Reached, Open, Last30) need the online records decoded (`[rules+8]` 0x74 bytes, byte meaning unknown) | none (L) | DONE for the two events the snapshot has; rest NEEDS decode. `[Stinger] Online=1` |
| 4 | Head-shot censor (klcensor.c, `[Censor] Online`) | blow the head off | key exists, default 0 -> off / off | caution | a heap float per local actor; works if `klb_level` accepts the online scene (scene based, GUESS yes) | none, local look | OK code existed; **option row added** `censoronline` (off until seen) |
| 5 | Mod HUD (klhud*.c, `[HUD] Online`, OnlineCrew, HideOnline) | full | other agent's work | - | - | - | NOT MINE (HUD agent) |
| 6 | Heister / mask / outfit select (klchar.c) | local model swap by `0x88c810` | `kl_online` only logs; then returns at the Heist vtable test -> nothing / nothing | peers see the stock model; online the body follows a session number (0x74ee10); the attach code assumes the Heist player record | local-only look is harmless but the attach/variant call on a replicated player is unproven; needs a live probe of `[gamedata+0x828+4*sel]` online first | none if only a local model/variant, but a variant byte replicates (`[player+0x50]`): GUESS may be sent | READY-ish, NOT blind-safe; needs probe (see 3.2) |
| 7 | Dead Men guns look (klgun.c) | variant byte write | `kl_online` return | the variant byte replicates | local-only needs a render-side swap | medium | NO until a render-side swap exists |
| 8 | Weapon shop + page II (klshop.c, klshoppage.c) | swaps what a row hands over | `kl_online` return | the shop buys through replicated inventory (`DDL_SInventoryItems`) and the host validates the buy | host-validated purchase: both sides must know the new item; clients cannot hand out a gun the host did not give | high | NO (C) |
| 9 | More guns shelf (klinv.c) | extra carried guns | inert | pickup routine 0x6cc1d0, inventory replicates | C | high | NO |
|10 | Grenades (klgrenade.c) | G throws | Heist-only gate | needs inventory + a thrown object (spawned entity replicates) | C | high | NO |
|11 | AI heisters in empty seats | 7 squads, records, tactics | none (squads dropped by the 0x7b3790 filter; no records; tactics need 0x7f6850) | see section 3 | see section 3 | medium | PLAN + probe, default off |
|12 | AI crew features: klbot (backstab, pay driver), klmove, klescort, klgrudge, klhop, klcrew_rt, klbotdown, kladren, klcdying, klcardown, klshield, klbalance, klcrew, kltrait | all act on the crew records | inert (need records) | records exist only on `ZGameRulesHeist` | follows 3: they only make sense once a bot exists with a record; no point before | high | NO until 3 step 3 exists |
|13 | Damage scale (klbalance.c) | writes per-level floats `[0x168d7c0]+0x6ac+L*0x70` | inert | gate = Heist vtable | HOST-authoritative damage: the same table exists on the host (GUESS: a global of the game's data, not the rules); only the host's numbers matter. Needs `klb_level` on the host with `s.level=1` GUESS, and a live check the table is used by the online damage path | clients would see hits resolved by the host (it is host-authoritative for AI; players' own damage is client-predicted: GUESS) | H, READY for a TEST probe only (not done) |
|14 | Down / revive (kldown.c, klcdying.c) | player drops to a revivable down | inert (`klr_arcade`) | the online "dead" is the game's own state machine (fed return) | C: needs a state in the replicated actor | high | NO |
|15 | Fed return (klfed.c, klfedkit.c) | dead player returns as police | inert; the **game's own** online rule already does this ("fed return is the game's own rule", netcode_plan.md 1) | - | the owner's later wish "choose your police character after you die" = the online rule's character pick | - | OK stock |
|16 | Free climb / climb (klfreeclimb.c, klclimb.c) | plays Dead Men's clip, moves the body | no start online / inert | position is replicated as plain position updates: a slide for peers | C: needs the clip as a replicated animation | medium | NO (could be local-only teleport-free, but the body is the replicated one) |
|17 | Rappel/jump boxes (kljoin.c, klrappel.c, klcrew_rt.c) | joins Retomoto's two places | `kl_online` in kljoin; others are Arcade gated | the debug jump request desyncs | C: the jump must be requested by the host for everybody | high | NO |
|18 | Camera (klcam.c, klcamsmooth.c) | follow, lean, shoulder cover, unstick | lean + unstick + ShoulderCover off online (`ShoulderCoverOnline=1` is a test switch); klcamsmooth has no gate | cover side replicates (0x4520d0) | local view-only parts (follow speed, blends) are already allowed; writes to `[P+0xb84]`/bits are not | shoulder: medium | OK partly; leave |
|19 | Mouse turn (klrigid.c), stance fix (klstancefix.c), frame limiter (klfps.c), stutter fixes (klextpt.c, klmem, klhigh, klarena, klquad), QoL (klqol.c, klqol2.c), ReShade (klreshade.c), textures (kltex.c), Steam stat block (klsteam.c) | local | **work online already** (no gate or `kl_online` is irrelevant; klrigid says "offline and online") ; klqol `BackgroundMs` deliberately off online; klqol2 uses `klb_read` (watch/dry features are Arcade) | - | - | none | OK |
|20 | Voice lines (klvoice.c, klchar_voice.h), traits (kltrait.c), Talk (kltalk.c) | per-body lines via `klw_who_now`, .LOC entries, Retomoto scenes | inert (Heist vtable) | the voice table is `rules+0x33e+record` (Heist) | the speech manager `[0x168e958]` is local: a Dead Men line for a **remote** player needs his body id, which is a session number online | none for own voice (L) but needs the online body number | READY-ish: needs the online "which body is player i" probe; NOT blind |
|21 | Names on maps (kllocname.c), expansion maps (klslot.c, `[Expansion] OnlineSet`) | n/a | works (SL2 PASS) host; **client must have the same OnlineSet** (host choice is not sent, re/private_match_mapsync.md) | - | map sync = C (lobby data) | wrong map -> failed join | OK (already online) |
|22 | Private-match options (klpm.c, klpm_arc.c, klpm_gun.c) | Arcade playlist, starting gun | klpm_arc off online; klpm_gun checks `!kl_online()` | host-set rules | a host-only starting gun = H, rules object layout unknown online | medium | NEEDS decode |
|23 | Lobby (kllobby.c, kllobbyopt.c, klserver.c, klmm.c) | n/a | online features | - | owned elsewhere | - | OK |
|24 | HUD escape/tracker/board/popup/tags (klhud_*.c) | Arcade | HUD agent: `Online`, `OnlineCrew` | records | other agent | - | NOT MINE |
|25 | Online smoothing (klnetsmooth.c, klnetfix.c, klnet.c) | n/a | online only | - | - | - | OK |

Ranking by (visible to the owner) x (cheap): 1-3 (sound, done), 4 (censor, done as a row), 6 (heister select), 20 (own voice), 11 (AI heisters),
13 (host damage), then the rest need replication and are not hook-side jobs.

## 2. What this change enabled (all default OFF, each its own toggle, "(recommended off)" until a live SL test)

| key | where | effect |
|---|---|---|
| `[Music] Online=1` | klmusic.c via klonline.c `klon_read` | jukebox in a network round; CALM at the round state, ACTION by `AfterSeconds` / money |
| `[Ambience] Online=1` | klambience.c | bed and one-shots |
| `[Stinger] Online=1` | klstinger.c | Loud (timer) and Loot (money, needs `[HUD] OnlineCrew=1`) cues |
| `[Online] Log=1` (default 1) | klonline.c | `online:` line when the rules object or session state changes (max 40 lines) |
| `[Bots] OnlineFillSquads=1` | klbotfill.c, needs `OnlineFill=1` | heap-byte squad mask change, see 3 |
| option rows | tools/kl_mod_options.py | `musiconline`, `ambienceonline`, `stingeronline`, `censoronline`, `botfill`, `botfillsquads` |

`klon_read(s, allow)` = `klb_read`, else the HUD agent's `klb_read_hud` online snapshot (called, not edited: `klb_hud_online` is forced to 1 for the call).
`klon_money` = Arcade sum, else the OnlineCrew handles (`[S+0x224+4i] + [S+0x188+4i]`, the SL6 reading; GUESS that this is "money").
Everything is READ-ONLY; no game write; with the keys at 0 the code path is the old one (`kl_online() && !flag` -> same early return).

**Known limits (so the first live run is read right):** the online snapshot has n=0: no ESCAPE mood, no DOWN mood, no van cues; the round state
0x19 online is the same number as offline only by GUESS (the HUD agent's reading also GUESSES `sm+0x70`). Map key: `klmu_mapkey` takes the
folder from `klj_map_file` (file-open hook) so an online DM01 gets `[Music.DM01]`; if that fails online it falls back to `F01` = the slot, and a
Subway list plays. Check the `music:` log line for the key.

### 2.1 What is deliberately not enabled
- Anything that writes to a replicated object (guns, shop, inventory, climb, jump, down, balance on clients).
- klchar online (see row 6), klvoice online (row 20), klbalance host (row 13): each needs one TEST probe line before a write; listed in 3.2.

## 3. AI heisters in empty seats of a 6-player lobby (plan + what is built)

Read first: re/bots_online_fill.md (the reading of 0x7b3790 / 0x7f6850 / 0x6ab250 / slot 198). Short form and the answers to the questions:

### 3.1 The minimum levers (CERTAIN = read in disassembly this session)
`ZSquadScript` slot 14 = **0x7b3790**, `thiscall(ecx = squad)`, no stack args, `ret`. Per member (`[[squad+0x24]+4]` list, member in esi) it calls the member's
vtable slot 21 (`call [vt+0x54]`: removes it from play) when one of four tests holds; test 1 at **0x7b37d1..0x7b37f0**:
`0x863a60()` (networked) && `[0x168e59c] == 0` (FA) && `!([squad+0x34] & 1)`. Test 2 (0x7b3805) needs `0x7f6850()` (Arcade) and never fires online.
So **lever A: `[squad+0x34]` bit 1 set** (mask 8 -> 9) keeps the squad online - by the game's own filter, no code patched. That is a heap byte of the squad
object: SHIP-safe. (A shared-vtable write to replace slot 14 at 0xbcce74 would also work but it is `.rdata`: `klh_may_write` refuses it in a SHIP build -> TEST only; there is exactly one vtable holding 0x7b3790.)

**0x7f6850** is the arcade-ness check inside `CPPScript::ZSoldier` ctor (0x6ab250): when false the soldier gets NO `ZLootTactic / ZBoardEscapeVehicleTactic /
ZBecomeTraitorTactic` (`[soldier+0x5f0/4/8]`). It is a jump table on `[sm+0x54]` (roles 0/1 -> `[sm+0x5c]==4`; roles 2/3 -> false). Answering it differently
online is a CODE change (the function is in a hashed range: not SHIP). Lever B for tactics: none SHIP-safe. Without them the Ally soldier walks its route and fights police
(it is on team 2) but takes no loot, boards nothing, never betrays.

### 3.2 Do AI actors replicate to clients?
CERTAIN for police: they are AI online through the same machinery (squads of mask eAllTypes / eFragileAllianceUCC run on the host, `DDL_ZFFActor` replicates).
Ally soldiers are `ZFFActor + ZSoldier` too; nothing read tests the team in the replication path (GUESS). The squad update (0x47e440) is skipped on a client (role 3), so the host
drives them, clients see them as remote actors. The same filter runs on clients at load, so the **same mask change must happen on every peer** or a client drops
its squad object while the host replicates the actor (unknown result). `fill` must therefore be the same on all peers: host = `kllb_orig - connected`; client = `[sm+0xb9]` (GUESS: the replicated, unlowered target).

### 3.3 What is built (`klbotfill.c`, default off)
- `[Bots] OnlineFill=1` (as before): lowers the Ready floor (kllobby.c), logs `botfill: role .. fill N` and the Ally census.
- NEW `[Bots] OnlineFillSquads=1` (needs OnlineFill): before the round (state < 0x19, from the lobby countdown on) every second, up to 8 tries, `klbf_squads(fill)`
  walks the entity table for `ZSquadScript` (vtable 0xbcce3c), logs `botfill: squad pass: S ZSquadScript, K with mask 8, W given bit 1 for fill N; first masks: ...`,
  and gives the first `fill` mask-8 squads (entity-table order = load order, equal on peers) bit 1. Heap byte, `klh_data`, SHIP-safe.
- GUESS to resolve live: the game's thread may not tick during the load, so the entity table may only be readable AFTER 0x7b3790 ran; then W>0 but the census shows 0 Ally ("late").
  The log tells: `squad pass` before `LOAD` completes or not, and `round census: ... N team Ally`.

### 3.4 What is NOT possible SHIP-side, honest
Loot-taking, boarding, betraying heisters online = a crew record per bot in the Sv/Cl rules (`m_iTotalLootMoney[12]`), the Heist tactics on the online rules class, a score-page row
and "left behind" handling. That is code (hashed) or a re-implementation. Cheaper approximation for the owner (not built): after step 3 works, the host scripts the walkers
(`klescort`-style orders 0x760e50) to the loot boxes: no score, no escape.
**Data-side alternative for the Dead Men maps (recommended first):** build the 7 `Squad#0N` with `EGameType` = `eFragileAllianceOnly` (1) in tools/kl_fa_bots.py (line ~2688 writes eHeistOnly 8). Then every peer loads all 7 (no timing question) and the host
parks the surplus. Stock maps need lever A.

## 4. Live-test recipe (owner; System Link solo route `C:/kl_build_1024/online_1025/live/SL7.ini`, hook `out_parity_1025a_test`, `[Net] Log=1`, `[Online] Log=1`)

ini: `[Music] Enable=1 Online=1`, `[Ambience] Enable=1 Online=1`, `[Stinger] Enable=1 Online=1`, `[HUD] Online=1 OnlineCrew=1`, `[Expansion] OnlineSet=2`,
`[Bots] OnlineFill=1 OnlineFillSquads=1`, `[Lobby] MinPlayers=1` (implied), `[Censor] Enable=1 Online=1`. Music folder/lists as in the live ini (`[Music.DM01]`).
PASS lines in KLHook.log (in order):
1. `music: ... ` map key line shows `DM01` (not `F01`) once the level is loaded.
2. `online: network round seen by the cosmetic parts: rules 00bd.... state 0x19 (= round runs, GUESS)` -> the state GUESS holds. If a different state number appears while the round is clearly running, note it: the three parts then stay silent (`music: ` no mood) - FAIL, send the log.
3. Jukebox audible within 8 s of the round; `ambience: phase 0 on DM01`; after `AfterSeconds` ACTION; stinger line `stinger: Loud`.
4. Collect a briefcase with `OnlineCrew=1`: a Loot cue (money handle sum rises) - else the money GUESS is wrong (log `hudprobe` lines).
5. Leaving the round (state != 0x19): END mood, then silence (`kl_online()` no longer true after the session ends).
6. `botfill: squad pass: N ZSquadScript, 7 with mask 8, W given bit 1 for fill 5` with W = 5; then `botfill: round census: ... M team Ally`. M = 5 -> lever A works; M = 0 with W = 5 -> "late" (the collect ran first): fall back to the data-side build of 3.4. Tactics column `00000000 00000000 00000000` expected (walkers).
7. No `patch REFUSED` line, 0 asserts, 0 faults. Any `fault` in `klon_`/`klbf_`: send log.
With all new keys at 0 none of the above appears and behaviour equals the previous hook.
