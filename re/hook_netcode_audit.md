# KLHook tick modules: what each touches, and what a private-match (online FA) build must do

Static reading only (kl-merge research, 2026-10-18). No code changed, nothing launched, nothing written to the game folder.
Sources: `re/netcode.md` (host model, section 6), `re/private_match_buildcheck.md`, and the modules called from `klh_tick`
(`klhook/klhook.c:735-793`). Line numbers are into `klhook/`. **FACT** = read in the code cited; **GUESS** = not proven from code.
Nothing here ran in a networked game: kl_online() itself rests on a GUESS (see 1).

## 1. The two guards that matter

* **Arcade test** (`klb_read`, klbot.c:360-364; same test in klbalance.c:374-383 `klr_arcade`, klfed.c:198-204 `klp_read`,
  klchar.c / klcrew.c / klcrew_rt.c / klpm_gun.c as `[session+0x5c]==4` plus a rules-vtable test): session mode 4, role `[+0x54]`
  not 2/3 (2 = SERVER, 3 = CLIENT), and rules object vtable `0xbd3514` = ZGameRulesHeist. Online FA runs ...FragileAllianceSv/Cl
  (`klhook.c:249-266`, klnet.c:54), so **every module behind this test is structurally a no-op online**: it also has no crew
  records to act on (the Heist-only records at rules+0x348 do not exist in the Sv/Cl classes; klbot.c:386-389). Exception to read
  carefully: klchar.c:302, klcrew.c:224/395 and klcrew_rt.c:258 test only mode 4 plus the rules vtable, NOT the role 2/3; online they
  rest on the vtable test alone (and so on the GUESS that online FA never has the Heist vtable). FACT of the code;
  that Sv/Cl really lack them is read from klbot.c's comment (carried), not re-checked here.
* **`kl_online()`** (`klhook.c:249-266`, key `[Net] OnlineSafe`, default 1): true for role 2/3, or mode 4 with a non-Heist rules
  vtable. It answers 0 (not online) when `OnlineSafe=0`, when the exe check failed, and while mode is 4 but the rules object is not
  yet readable (`[[0x168e9e4]+0x54]` null: klhook.c:263), so a lobby window before the rules exist counts as offline. GUESS (klhook.c:253-254): a role of 2/3 is only ever set by a network session; never seen live. Used as an extra guard
  by kljoin, klfreeclimb, klgun, klcam, klcensor, klpm_gun, klpm_arc, klslot (playlist only) and `klchar` (log only).
* **Stock-level guard** `klb_level()` (klbot.c:414-425) = `klx_level_verdict == 2` (archive is not the stock one of its slot).
  `[KLHook] AllMaps=1` makes stock levels count as modded **in an Arcade session only** (klsteam.c:127-144, 323), so it does not
  open any module online.

Replication facts the verdicts lean on (from the code, not from a test):
* AI orders are host-side: the game's own order routine ZSoldier vtable +0x13c (0x760e50) "in a network session on a client:
  returns" (klescort.c:24-26). So an AI order issued on a client is dropped by the game; on the host it would take effect.
* The game's actor teleport 0x62a900 with flag b != 0 and a network session "sends the place to the peers" (klcrew_rt.c:14-16).
  The crew modules call it with b = 1 (klcrew_rt.c:19-22), so IF they ran on a host, those moves would reach peers.
* Player movement is client-authoritative (netcode.md section 6; ASSUMPTION per that file: AI host = server not traced).
  `ZFFActor` carries RMCServerForcePosition / RMCMoveToPosition (netcode.md section 6).

## 2. Table

L = local only (this machine's UI, camera, own player), S = shared state. "Online risk" is the risk if the module ran in a
private match. "Guard" = what stops it today.

| Module (tick) | What it touches | L/S | Online risk | Existing guard (file:line) |
|---|---|---|---|---|
| klf_tick (klfix.c) | one count in the leaderboard service object (score-page crash fix), data | L | none | writes only when the count is garbage; no mode test (klfix.c:1-14) |
| kls_tick (klslot.c) | import-slot wrappers on CreateFile/FindFirstFile/fopen; redirects `Locations/Fxx/` to `KLExpansion\Maps\...`; reads the menu window stack for the "page" | L (but decides WHICH MAP LOADS) | **HIGH: map mismatch.** The page comes from this machine's own menu stack (klslot.c:279, 286). A client that joined from the lobby never opened the host's map page, so it loads the page-0 rule or the stock map while the host loads DM; scene refs then differ (re/private_match_buildcheck.md s1). A static `[Redirect]` (page 0) applies to every mode, also online | `kl_online()` only gates the Arcade playlist override (klslot.c:280). No guard on the redirect itself. |
| klmm (Steam matchmaking proxy, installed at boot) | CreateLobby type (`PrivateLobby`), `klx_build` lobby data, search filter | S (lobby metadata, seen by Steam and peers) | medium: intended to be online; by design | off unless `[Net] PrivateLobby` / `BuildKey` set; "NOT a gate on purpose" (klmm.c:48-53). NOT RUN |
| klx_tick / klsteam | proxy ISteamUserStats: blocks stat/achievement/leaderboard writes on non-stock levels | L | low (blocks the owner's profile writes also in private match; harmless) | verdict 2 gate (klsteam.c:131-144) |
| klg_tick (klgun.c) | variant byte per gun part in the loaded .prm (gun look) | L (look of own build; peers draw their own copy) | low; if a peer lacks the .prm variant the byte is just their stock look. GUESS | `kl_online()` returns early (klgun.c:409) |
| klm_tick (klmem.c) | none per tick (import slots, address-space) | L | none | no game state (klmem.c:1-20) |
| kpm_gun_tick (klpm_gun.c) | writes the player's crew-record gun row before the loadout runs | S (loadout of local player; would feed the equip) | low-medium; the stock loadout path may replicate the weapon, not traced. GUESS | Arcade `+0x5c==4`, Heist rules vtable, `kl_online()` (klpm_gun.c:48, 62-66) |
| kpm_arc_tick (klpm_arc.c) | writes the Arcade map-selector byte `[0x154d632]` after a match | L (Arcade menu) | none online | `kl_online()` (klpm_arc.c:91, 120) |
| klj_tick (kljoin.c) | writes `[gamedata+0x8d4]` and `[0x156b358]` = "jump request"; the game moves the local player to a jump entry | S (position of a local player; no crew walk) | **medium-high**: a cross-map jump on one machine only; peers see only position updates. Retomoto (tower to lobby) depends on it | `kl_online()` blocks the request (kljoin.c:244-248) |
| klt_tick (klcrew_rt.c) | calls 0x62a900 on every AI heister (the "crew follows the jump") | S (AI position, would be sent by 0x62a900 b=1) | structurally none online (no Heist crew); on a host it WOULD replicate. GUESS that peers accept it | Arcade `+0x5c==4`, rules vtable == Heist (klcrew_rt.c:262-266); no `kl_online()` |
| klv_tick (klhop.c) | 0x62a900 on AI heisters at hop places; bot walks | S | none online (same reason as klcrew_rt) | `klb_read` (klhop.c:390), `klb_level` (klhop.c:400) |
| klfc_tick (klfreeclimb.c) | starts a climb action on the local player (game calls, SEH-guarded) | L (own body; peers see position) | medium: has no mode test of its own (klfreeclimb.c:650 says so); a running climb is let finish | `kl_online()` (klfreeclimb.c:650-654); `[Climb] Enable=0` default |
| klq_tick (klclimb.c) | carries the local player up a level-data edge | L | none online | `klb_read` + `klb_level` (klclimb.c:1283, 1287) |
| klrp_tick (klrappel.c) | places the local human's node every frame along the rappel clip (0x82cc40) | L (own player, position replicated as movement) | **medium: no online guard**; fires wherever a level's KLJoin.ini has `[Rappel]`, in any mode. Peers' own cut may not be in sync (the cut is level data, replication of cuts not read). GUESS | only `[Rappel] Enable=1` and the level key (klrappel.c:253-259) |
| klc_tick (klchar.c) | heister model/mask/outfit: writes the rules' hero table, calls attach/setvariant; options-menu wrapper | L look | none effectively. The comment says "peers see the stock model" (klchar.c:298-302) but the code then returns because the rules vtable is not Heist (klchar.c:302-306), so online it does nothing. The menu rows (private vtable of the options object) stay local UI | `+0x5c==4`, rules vtable test (klchar.c:302-306) |
| klw_tick (klcrew.c) | random AI heister look (table + game calls) | S for AI look | none online (no crew) | `+0x5c==4` + vtable (klcrew.c:395, 409) |
| klk_tick (kltalk.c) | calls the game's speech routine for Kane/Lynch lines | L audio (a speech call; whether the game replicates it is untraced. GUESS) | none online | `klw_who_now` Arcade-only, verdict 2, `[Talk] Enable` (kltalk.c:599-606) |
| klb_tick (klbot.c) | per-level tuning record (traitors, limits) in the game's global tuning object, ZHeistScore; backstab/bribe calls | S | none online; global tuning object is written only while the session is Arcade; restored otherwise (klbot.c:569-616) | `klb_read` + `klb_level` (klbot.c:943-945) |
| kle_tick (klescort.c) | AI heister orders (0x760e50), shields rules' shoot-the-left-behind | S (AI orders: host-authoritative) | none online (no crew). If run on a host orders WOULD take effect and replicate by actor state (GUESS). | `klb_read` (klescort.c:1349), `klb_level` (:1358) |
| klmv_tick (klmove.c) | private vtable copy on ZAllyEscapeBox, rules fields (van call timers), AI stage, bot teleport via klv; scans committed memory for vtables | S | none online; **the memory scan runs per round start only after the Arcade test** | `klb_read` (klmove.c:1719), `klb_level` (:1747), session test 0x7f6850 (klmove.c:590) |
| klr_tick (klbalance.c) | damage table in the global tuning object; local health object; point-blank database vtable wrapper (copy) | S in effect (the damage numbers, the table is per machine) | none online: `klr_arcade` fails; "back" paths run when not arcade (klbalance.c:936-944). Note: online each machine computes its OWN damage; a table change on one machine only would desync hit results (ReceiveHit/UpdateHitPoints are reported by the shooter, netcode.md s6) | `klr_arcade` (klbalance.c:374-383), `klb_level` (:930) |
| klnm_tick / klu_tick / klesc / kltrk / klbrd / klsb / klkf / klpu (klhud*.c) | OSD elements' vtables (private copies), hidden byte of the stock list, `[0xceeebc]` HUD inset, draws text/pictures | L | low; purely local drawing | `[HUD] Enable`; level gate `klu.stock \|\| klb_online_session() \|\| verdict==2` (klhud.c:1549); `[HUD] Online=0` default (klhud.c:1637) so online reads are off; `klb_read_hud` gives no records online (klbot.c:391-409). `klhud_board2.c` and `klhud_popup.c` use `klb_read` (Arcade only) |
| kly_tick (klgrudge.c) | floats in heap objects (bot grudge/health) | S (AI health/aggro) | none online | `klb_read` (klgrudge.c:427), `klb_level` (:441) |
| klo_tick (klshoulder.c) | log only | none | none | no writes |
| klcam_tick (klcam.c) | camera profile floats (client data), shoulder swap, "unstick" writes, eye setter call | L (camera). Shoulder/cover side is replicated (klcam.c:443-444 says so) | low: swap and unstick gated (the swap gate is lifted by the test switch `[Camera] ShoulderCoverOnline=1`, klcam.c:447); profile floats are not | `kl_online()` at klcam.c:382, 418, 447, 569, 632, 684, 1032; profile floats ungated (klcam.c:16-17) |
| klhp_tick / klcs_tick / klvis_tick (klheliprobe, klcensus, klvis) | read-only logs | none | none | return at once unless their key is set |
| klcn_tick (klcensor.c) | pre-arms the head-hit sum `[actor+0x600]` of every actor (heap float) so a killing head shot censors | S (writes AI actor state; NPC kills happen on the host) | medium: on a client the write does nothing useful; on a host it changes what kills do and peers see a different death. GUESS | `[Censor] Enable=1` by DEFAULT, but returns when `kl_online()` unless `[Censor] Online=1` (klcensor.c:74, 95) |
| klnet_tick (klnet.c) | in a network FA session writes Net-Z update intervals and tolerances (global `.data`, 12 numbers) | S in effect: sender-side numbers; only the sender's count (klnet.c:92-96) | medium; by design online only; stock FA unchanged when off | `[Net] Tune=1` and gate: mode 4, state 0x13..0x1f, non-stock slot, not ranked, host only on a private lobby, client only with `TuneClient=1` (klnet.c:313-318) |
| klp_tick (klfed.c) | "come back as a fed": data writes, spawns the dead player as police | S (police status, roles) | structurally none online (it would collide with `RMCSetPoliceMan` / `Respawn`, server-owned: netcode.md s6) | `klp_read` Arcade test + verdict (klfed.c:198-204, 524) |
| klfk_tick (klfedkit.c) | fed kit: bodies, AK, hunt flags, loot flags | S | none online | `klb_read` + `klb_level` (klfedkit.c:798; :21 is the header comment) |
| klbd_tick (klbotdown.c), kad_tick (kladren.c), kld_tick (kldown.c) | AI downed state, adrenaline, player mash get-up (data writes) | S | none online | `klr_arcade && klb_level && klb_read` (klbotdown.c:266, kladren.c:1060); kldown.c: bots part `klb_read` (:1321), main tick `klr_arcade` + `klb_level` (:2104-2106) |
| klrs_tick (klreshade.c), kset_tick (klset.c) | reads only | none | none | `[ReShade] Bridge`, `[Menu] TableLog` |
| kpm_* option rows (klpm.c) | three option names in the menu, values stored in the DLL and `KLHook.ini [Match]` | L (menu) | none | `[Match] Enable=0` default (klpm.c header) |

## 3. Findings by category

Local only and safe in a private match: klhud*.c (cosmetic, with `[HUD] Online=1` it runs without records), klcam profile floats,
klfix, klmem, klsteam, klshoulder/klheliprobe/klcensus/klvis/klreshade/klset (log only), the options-menu wrappers of klchar/klpm.

Acts on shared state but is Arcade-only by construction (crew records, ZGameRulesHeist): klbot, klescort, klmove, klhop,
klcrew_rt, klbalance, klgrudge, klfed, klfedkit, kldown, kladren, klbotdown, klcrew, kltalk, klclimb. They cannot run online,
for the vtable reason in section 1, so they need no online switch. The one thing to remember is that they REPLICATE if
someone ever enabled them for a host: the AI-order routine is host-only in the game's own code (klescort.c:24-26) and the actor
teleport sends the place to peers (klcrew_rt.c:14-16). That is also the only place where "make it host-only" would apply.

Does it reach peers through Dog Days' replication? For AI state: probably yes from the host (ZFFActor replicates position, angle,
animation ids, hit points, target; that the AI station is the host is an ASSUMPTION, netcode.md s6, not traced). For anything
written on a client: no, a client's AI is a mirror (netcode.md s6).

## 4. What a private-match build must switch off or make host-only

1. **Map selection must travel with the lobby.** `klslot.c` decides the map from the local menu page (klslot.c:279, 286). In a
   private match every peer must resolve the same `KLExpansion\Maps\<dir>\Fxx_Main.zip` for the host's chosen slot. Make the
   redirect host-driven (host publishes page/map in lobby data; joiner uses it instead of the local latch) and block the start
   when builds differ (`re/private_match_buildcheck.md`, klbuild.c). Without that the matchmaker, not the hook, will find a
   crash. This is the single most dangerous module online. FACT of the code path; the exact failure is a GUESS until two clients
   run it.
2. **kljoin.c** (cross-map jump): already blocked online. A map that needs the jump (Retomoto) cannot be played as private match
   until the jump is host-driven (an `RMCTeleportToPosition` / `ServerForcePosition` for each player, netcode.md s6 line 372-375,
   or no jump map).
3. **klrappel.c**: add the `kl_online()` guard (or run only for all peers at the same round event); today it has none
   (klrappel.c:248-259). GUESS that the cut itself is not synced between peers.
4. **klfreeclimb.c**: guard exists but is only `kl_online()`; keep `[Climb] Enable=0` (default) in a private match until the
   climb's position replication is tested.
5. **klcensor.c**: `[Censor] Enable=1` is the DEFAULT; keep `Online=0`. If a host wants it, host-only (the head-hit sum is an
   NPC-side value; a client write is pointless).
6. **klnet.c Tune**: must stay opt-in, and be set on every peer (each sender's numbers count, klnet.c:92-96). Do not default it.
7. **klmm.c** `PrivateLobby` / `BuildKey`: intended online; both are NOT RUN. The tail-jump slots must keep working for stock
   hosts (klmm.c:48-53).
8. **Modules that "cannot run online" must stay unreachable**: do not add a code path that relaxes `klb_read`'s role check, and do
   not set `[HUD] Online=1` together with a feature that needs records (it returns n = 0 online by design, klbot.c:386-389).
9. **Build identity**: every peer needs the identical build of KLHook inputs that change the map, `Patch01.zip` and the redirect
   table (re/private_match_buildcheck.md s4, s10). The hook's own gameplay modules are not in that fingerprint, because they
   do nothing online.
10. Do NOT give the private-match build the Arcade-only tuning (traitors, damage table, point-blank vtable, fed). `klr_arcade` /
   `klb_read` stop them today; leave those tests as they are.

## 5. Unproven (GUESS)

* That role 2/3 appears only for network sessions (klhook.c:253-254).
* That the Sv/Cl classes have no ZGameRulesHeist crew records (klbot.c:386-389 is a comment from earlier reading).
* That the AI station is always the host (netcode.md s6).
* That the effect of a data-only write like the head-hit pre-arm or gun variant byte stays local for the writer.
* Whether klrappel / the rappel mini-cutscene runs on every peer in sync (cut sync not read).
* That there is no other call of an Arcade-only module reachable from the fallback thread (`klh_tick(0)`, klhook.c:997); the
  game-thread flag is passed on, but this audit did not trace each module's use of it.
