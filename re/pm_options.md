# Private-match options: character, gun, map vote, map playlist / random (design, 2026-10-18)

Owner items 17 and 18 (re/owner_feedback_1017.md): "a settings / options thing when you do a private match so they can pick
their character within the match before it starts, and what gun they use ... maybe a map vote ... and the option to play
multiple maps in the same session as a bundle or 'random' map mode".

**DESIGN ONLY. Nothing was built, run or installed; no game file touched.** Sources are the repo's own notes (cited by file),
re-read for this document: re/private_match.md (kl2 addresses PROVEN there), re/fa_private_match_blueprint.md,
re/menus.md, re/netcode_fa.md, re/netcode_plan.md, re/slot_redirect.md, re/fa_slots.md, re/shop_plan.md, re/crew_random.md,
re/wardrobe.md, and the header comments of klhook/klchar.c, klslot.c, klmm.c, klnet.c. Tags: PROVEN = a note cites the
disassembly or a live run; GUESS = my inference. Nobody has ever run an online session with this hook (no `net:` line exists in
any log), so everything online below is static reading.

## 0. Answer in one screen

1. **What "private match" means here.** The online Fragile Alliance lobby made by `XBoxLiveCreatePrivate` (Steam lobby type 1,
   FriendsOnly; PROVEN, private_match.md 1). It is NOT Arcade. This matters because every AI-heister / balance / down / HUD
   part of the hook is Arcade-only (`ZGameRulesHeist`) and does nothing online; online uses `ZGameRulesFragileAllianceSv/Cl`
   (blueprint 0, 3). What a private match can use today: the maps (level data), the Steam transport, option wrappers,
   menu XML.
2. **The one pattern that makes the menu cheap is already proven live:** a menu row binds to an option by NAME, the names are
   compiled into the game, but the hook swaps the options object's vtable for a private copy and answers extra names itself
   (`KLChar`, `KLMask`, `KLOutfit`; klchar.c section 1; runs W1 - W6, 2026-10-09). More names are the same code. (As built in klpm.c they are `KLMGun`, `KLMVote`, `KLMPlay`: klgun.c answers every name that starts
   with `KLGun`, so `KLGun...` is taken; the later sections still say KLGun / KLVote / KLPlay.) Their `Set` wrapper is also the EVENT that tells the hook the player chose something.
3. **The pattern that makes the network cheap:** Steam lobby member data and lobby data, polled by the hook. The game never
   checks the build and the Steam-level join checks nothing (private_match.md 3, `0x629980`), so no new game code is needed to
   move a choice from one machine to another. The hook already owns the right interface (klmm.c proxy, 008 layout PROVEN
   against steamclient.dll, private_match.md 5 / 6).
4. **The hard parts are not the menu and not the transport:** (a) the lobby gives every peer a SLOT INDEX only, and the page
   latch that turns a slot into a Dead Men folder is dropped online, so a page / folder handshake has to exist before anything
   else (section 2, "prerequisite P"); (b) applying a character to a REMOTE player needs the Steam id -> session number ->
   player index chain, which is NOT ESTABLISHED; (c) a map change inside one match is NOT ESTABLISHED for FA.
5. **Build order, easiest and most useful first:** options page for the local player in Arcade (pattern proven) -> playlist /
   random in Arcade -> Steam transport in LOG-ONLY form -> prerequisite P (page + fingerprint handshake) -> map vote ->
   starting gun -> character cast with "once per match" -> online playlist between matches. Section 6.

## 1. Which part is menu XML, which is hook code, which is both

| part | menu XML (`menu/frontend.xml` in `Overlay\Patch01.zip`, built by klhook/mkoverlay.py) | hook code (new file `klhook/klpm.c`) |
|---|---|---|
| options page (character, mask, outfit, gun, vote) | a `<Window>` of option rows, the story page's "Difficulty" row copied N times - exactly what `KLHeister` is today (wardrobe.md 5). **Entry counts are the options' ranges** (wardrobe.md 5a), so the XML is generated from the same lists the DLL has | the wrapped option names; value storage (DLL + `KLHook.ini [Character]`/`[Match]`, because the options object is deleted at every scene change: klslot.c, run MP1) |
| value texts | `<Text Text="%literal">` children (PROVEN: shown as written) | none, unless "taken" markers are wanted (section 3.2) |
| entry point to the page | one `OpenWindow` button on a page every player passes (section 3.1) | none |
| publishing a choice to the peers | - | `SetLobbyMemberData` (+0x60) on `Set`, section 4 |
| tally, cast, next map | - | host's hook, section 4 / 5 |
| applying a choice | - | local player: the game's own routines (0x783fb0 model, 0x88c810 variant; klchar.c). Gun: section 3.3. Map: `MP_SelectedLevel` + the klslot page latch |
| fingerprint / "same files" guard | - | `klx_build` in klmm.c (BuildKey=1) exists; member data for options is guarded by a version prefix, section 4.3 |

**Text and pictures:** all `%literal`, English only, as the Heister page does (no .LOC edit). Map names in the vote are
literal strings from `KLExpansion\Maps\maps.ini` (a table the DLL and mkoverlay.py both read; GUESS on its exact format, it does
not exist yet). No new pictures: reuse the stock `LevelPicture_F0x` of the slot the map is built for (slot_redirect.md 4).

**Menu room:** every created window, element and colour set uses one of 5096 table slots, overflow is a bare `int3`
(menus.md 2.5; the blueprint calls it "the first blocker for the menu part"). The stock frontend model over-counts, so the real
headroom is unknown. Step zero of the build order logs `[[[0xdd265c]+0x824]+0x9f48]` once in the main menu. The options page
is about 40 elements (6 rows x (label + arrows + value) + back); copy windows as `Lean=1` where the lobby copy is concerned.

## 2. Prerequisite P: peers must load the same Dead Men folder (everything online depends on this)

Facts (PROVEN unless marked):
- The host replicates a SLOT INDEX 0..8 (F01..F09), never a name. Each machine maps it through its own level list and klslot's
  redirect sits below that (netcode_plan.md 1; fa_slots.md 2: host `0x6c536f`, client `0x491fd1`). `-o MPMap` replaces the name
  only on the machine whose command line has it, and the launch options must not change (CLAUDE.md), so MPMap is not usable.
- klslot picks the redirect table (`[Redirect.N]`) by the PAGE latch, read off the open menu window `HeistPlayMenu<N>`; the latch
  is DROPPED when the frontend shows a window stack without a map page (klslot.c). So an online match loads STOCK maps today
  (blueprint 1.4). Stage-0 workaround: `[Expansion] Page=2` on every machine (no guard).
- A map is built for ONE slot (DM01 and DM05A both for F01). Six slots are free per page (F01 F02 F03 F04 F06 F07; DLC F05 F08
  F09 are never redirected, blueprint 5.1). Therefore a playlist / vote over more than six maps cannot be one page: the thing a
  vote selects must be a (map folder -> slot) pair, not a slot.

Design (blueprint 2.3 / 2.4 refined, GUESS where marked):
1. The host publishes lobby data `kl_map = <folder id, e.g. DM05A>` (and `kl_ver`, a small integer, bumped whenever the wire
   format below changes). klslot gets ONE new input: "force folder X for slot S for the next load", instead of "page N". The
   slot S comes from `maps.ini` (the folder id's build slot). Every peer's klslot applies it at the moment `<S>_Main.zip` is
   opened (the point where it already takes the page, per load, klslot.c). Mixed-page problems vanish because the page is not
   needed any more (a page is just a bundle of folder ids).
2. A peer whose installed folder differs (klx_build on the lobby, per-folder size + CD hash from klsteam.c `klx_fingerprint`,
   GUESS that this set of files is what friends must share) is held out by the game's own "everybody owns this map" gate
   (`0x6c49a0`, byte `[[0x168f750]+4+slot]`, blueprint 2.3 / 2.4). **ASSUMED** that this byte is all that gate reads.
3. Solo testing of the host side: one PC can host and read back its own lobby data (blueprint E1 / E3); the second-peer
   behaviour needs luvsic or another owner of both games (netcode_plan.md 4). **This is the single biggest schedule risk of the
   whole document and nothing below can be proven live without it.**

Until P exists, the interim is the existing stage 0: `Page=2` forced on both machines, friends only, invitation only
(blueprint 2.4, 6). Options pages can still be built and used meanwhile; they simply apply on the stock map set.

## 3. The per-player options page

### 3.1 Where the player reaches it
The lobby window `FALobby` is owned by `MercsFASelectorLobby` ("owns all input", menus.md 4.2), so a button added inside it may
get no focus: GUESS, never tried. Joiners may skip every page (a friend's "Join game" goes straight to `0x547950`,
private_match.md 3). Therefore the entry point must not be a page only the host passes. Ranked by safety:
1. **Main menu -> Online -> "Match options"** (an `OpenWindow` row on `OnlineMenu`, or on the Heister page's neighbour). Every
   player passes it any time before hosting or joining, values persist in the DLL and in `KLHook.ini`, and it works the same in
   Arcade (the Heister page is already there and is the same window). Pure XML + the proven option wrappers. **Do this first.**
2. A button on `XBoxLiveCreatePrivate` (host only, before the lobby exists) for lobby-wide settings (playlist, vote on/off).
3. In-lobby access (a button in `FALobby`, or a hook-read hotkey that opens a window by name). Requires either input to reach the
   widget (GUESS) or the game's window-open call (not located). Do after the lobby handshake works; not needed for the first
   playable version because the choice is made before the lobby and republished when it changes.

### 3.2 Character: once per match (owner's stage 3 rule)
What exists: `KLChar` 0..16 (0 stock, 1..8 Dog Days heisters, 9..16 Dead Men), `KLMask`, `KLOutfit`, applied to the LOCAL player
through the game's own body swap in Arcade (klchar.c 2 / 3; wardrobe.md; seen live W1 - W6). The Heister row ranges come from the
XML entry counts.
Online design (blueprint 4.3, kept; every step marked):
1. Each peer publishes its wish: member data `kl_opt = "v1;c=<KLChar>;m=<KLMask>;o=<KLOutfit>;g=<KLGun>;x=<vote>"` on every `Set`
   of a KL option and when it joins the lobby (SetLobbyMemberData +0x60: PROVEN slot, argument sizes PROVEN in steamclient.dll).
2. The host arbitrates by join order and publishes lobby data `kl_cast = <steamid64>:<char>,...`. Rule: first come keeps it; a
   later duplicate gets the next free character. Join order = `GetLobbyMemberByIndex` order (+0x44): GUESS that this is join
   order; if not, order by the lobby owner first, then by Steam id (deterministic on every peer, which is all that matters).
3. A peer reads `kl_cast`, finds its own entry and writes that into its own `KLChar` value (so the page shows what it will be).
   **Greying a taken entry by game state is not possible from XML** (menus.md 6). Two cheap substitutes, in order: (a) the `Set`
   wrapper skips over taken values when the player steps through the row (no UI change, always consistent with `kl_cast`);
   (b) later: wrap slot 10 and implement slot 6 `GetText(name, &string)` so the row can print "Tommy (taken)". W2 showed the cost:
   slot 6 was NOT implemented and the row was blank. The `string` out type of `0x6994c0` is not read, so (b) is GUESS.
4. **Applying it to everyone.** Online the body follows a per-player session number: slot 137 = `0x74ee10` takes
   `index = 0x817160(session, record+0xdc)`, clamps to 0..7, and calls `0x783fb0(GetHero(2, index))` with the table at `rules+0x208`
   (menus.md 5, PROVEN for the code; "table at +0x208 in the Sv/Cl layout" is ASSUMED, blueprint 4.2). So the plan is for the
   HOST'S hook to write `heroes[session number]` = chosen model on every machine's table (all peers write the same table, same
   files), then the game's own slot 137 dresses each player. **NOT ESTABLISHED:** Steam id -> session number (blueprint 7.4 q2).
   Needed reading: `0x817160`, the session record, `m_iPlayerIndex[12]`. Mask and outfit are not replicated (`DDL_ZFFPlayer`
   has no variant field, GUESS) so every peer has to apply `0x88c810` to each player entity. Same requirement.
5. A dead heister returns as police (type 3, game rule); leave type 3 alone, as klchar does.
6. **Arcade needs none of this** (the player is one, the crew is random per round, nobody twice: crew_random.md). A character
   page in Arcade is the fast proof of the whole options page and costs nothing on top of what exists.

### 3.3 Starting gun
Facts: the online shop table (36 rows) is in hashed .rdata and cannot change; prices, rank locks and availability are checked by
hashed code (shop_plan.md 1, 3); money is the host's. A Dead Men gun is only a LOOK (hidden parts of a Dog Days gun,
klgun.c); AK-47 / M4 mapping is luvsic's, pending (owner_feedback items 14 - 16, other tracks).
Design: `KLGun` = one of the shop items (a list generated from the 36 rows, free choice, no price, no rank lock: it is a private
match). At round start, each peer equips the item into its OWN player's primary slot; the player is master of its inventory
(netcode_fa.md 3: `0x6300f0` only on the master) and the inventory replicates as item + weapon reference (`DDL_SInventoryItems`),
so peers see it without any wire work of ours.
- What is not known: the equip call. The shop's buy path (`MercsFASelectorWeapons`, 0x7558ce) ends in some inventory write; the
  note stops at the window level. **Step zero is reading that write** (static, no run). GUESS: the weapon template for every
  shop item already exists in every FA level, because the shop sells them; if a map lacks one, the equip must be refused with a
  log line (InventoryBinding allows each item once per level, CLAUDE.md: it is the template that matters).
- Interaction with the other tracks: klgun's look-switching and the icon / HUD tracks edit klgun.c / klhud_weapon.c, so KLGun
  stays in klpm.c and only READS their tables (do not edit those files).
- Arcade proof first: the Arcade player's start gun is whatever the level gives; the same equip call gives "pick your gun" there.

### 3.4 "Other options" worth the same page (cheap because they ride on the same wire)
Mask and outfit (exist). Lives / round time / number of rounds are the lobby's own rows (`MP_NumberOfRounds`, `MP_TimeLimit`, host
only) and need nothing. Nothing else is proposed: more rows cost menu elements (section 1) and each must be applied by
something nobody has read yet.

## 4. How the choices reach the other peers

### 4.1 Transport (all PROVEN as slot numbers, GUESS as behaviour)
Steam `ISteamMatchmaking` 008 (36 slots; ret-count check against steamclient.dll, private_match.md 5): +0x40 GetNumLobbyMembers,
+0x44 GetLobbyMemberByIndex, +0x48 GetLobbyData, +0x4c SetLobbyData, +0x5c GetLobbyMemberData, +0x60 SetLobbyMemberData, +0x64
SendLobbyChatMsg, +0x88 GetLobbyOwner. The lobby id is in the game's service object (`[S+0x35e]`, klnet.c). The hook should call
the interface through the real export (`GetProcAddress(steam_api, "SteamMatchmaking")`), not through the klmm proxy object, so the
options keep working when `PrivateLobby=0` and the proxy is not installed.
- **Poll, do not listen.** Every ~250 ms on the game thread read `kl_cast` / `kl_map` / `kl_ver` and every member's `kl_opt`. No
  Steam callback registration is needed (the data is a handful of short strings; keys <= 255 bytes, values far below the Steam limit).
- Not the lobby chat: the game's own `LobbyChatMsg_t` handler (0x8bd520) feeds `SyncLobbyWithNetZ` (netcode_fa.md); our text would
  hit code that expects its format. GUESS-level risk with no benefit, so: no chat.
- Not Net-Z objects: new replicated classes would need engine-side registration (hashed code, antitamper.md).

### 4.2 Authority
Each peer is the authority for its own `kl_opt`. The HOST is the authority for `kl_cast`, `kl_map`, the vote result and the
playlist cursor (host = lobby owner = Net-Z server; the "server is always the host" is ASSUMED, netcode.md 6). A client never
acts on another client's `kl_opt` except through the host's `kl_cast`. (Review note: 4.1 says every peer polls every member's `kl_opt`;
that is for display and logging only, to stay consistent with this rule.)

### 4.3 Version and safety
- Every value starts with `v1;`. A peer that sees another version, or a member with no `kl_opt`, falls back to "stock behaviour for
  that member" and logs once. A peer without the hook publishes nothing -> the existing availability guard (fingerprint, section 2)
  keeps the countdown from starting. The whole feature is inert unless `[Match] Enable=1` and the lobby is the FriendsOnly kind the
  hook can recognise (klnet.c: host sees the private bit; a client "cannot tell" and goes by the player's word, `TuneClient`).
- Never ranked, never public (blueprint 6): the options code does nothing in a ranked / public lobby.
- All writes are heap data and import-slot proxies; no code byte (CEG, antitamper.md). Never take a TEST/`direct` build online.
- **No build check exists in the game** (netcode_fa.md 2.1: every player must have identical files). The options wire format does
  not change that; the fingerprint of section 2 does.

## 5. Map vote and map playlist / random

### 5.1 Vote
- Row `KLVote` = one of the maps in `maps.ini` (or "no preference"). Published in `kl_opt` (`x=`).
  **Desync risk (review 2026-10-18):** the stored value is the 1-based INDEX into the local maps.ini, and `kpm_tally` returns an index. Two
  machines with maps.ini files that differ in order or length would read the same number as different maps (and `KLMVote` is clamped to the
  local count). Publish the map ID string (`x=DM05A`) and tally on IDs; only the host's `kl_map` result is applied, as an ID. The same
  holds for the playlist cursor: it indexes the host's list, so only the host may advance it and peers must never run `kpm_next` themselves.
- The host tallies when it needs a map: when the lobby asks for the map (the host presses Ready) or when everyone has voted, whichever
  comes first. Ties and "no preference" resolve by a seeded draw (seed = lobby id) so a restart does not re-roll. Tally is a
  function of the member data only, so the host's choice is reproducible in a unit test off-game.
- **Applying it** (the uncertain step). The lobby's own toggler changes the map by writing `MP_SelectedLevel` (menu POSITION byte
  `[0x154d61e]`) and giving the slot to the session manager (`vtbl+0x28`, `0x7163e0`; `ZMercsFASelectorLobby` slot 10, menus.md 4.2).
  The host's hook does the same: the position of the map's slot (`0x80c9f0` inverse table), then the game's own Increase/Decrease
  message to `LobbyLevelNameToggler`, or the direct session call. GUESS which of the two is enough; trying the message path first
  because it is the game's own path. Then publish `kl_map`. Clients learn the slot from the replicated settings by themselves and the
  folder from `kl_map` (section 2). Display: the lobby shows the stock title and picture of the slot (blueprint 2.4); a
  `LobbyLevelNameToggler` overlay with literal names would fix that for the Dead Men page (mkoverlay), GUESS that the toggler's texts
  come from `<Text>` children there (menus.md says the shown name comes from the code tag `LobbyLevelName`, so the overlay may not
  help: PROVEN code path, so likely it does NOT).
- Test solo: a lobby of one is a vote of one; the tally, the map change and the slot redirect are all testable on this PC, the
  multi-voter case is a unit test of the tally function.

### 5.2 Playlist (a bundle) and random
What a "match" is: `NumRounds` rounds on the map that is loaded; between rounds the SAME LOADED LEVEL is reused (Ready ->
`FAWaitForPlayers` -> next round, fa_round.md live line 445). So a playlist advances between MATCHES, not rounds.
- **R1 (recommended):** `[Match] Playlist = DM01,DM03A,DM05A,...` (or `Mode=random`). When the host's lobby comes back after a match
  the host's hook advances a cursor, selects the next map exactly as the vote does (5.1), and publishes `kl_map`. Players press Ready
  again. Random = seeded draw without repeats until the list is exhausted. A "bundle" is a named list in `maps.ini`.
  Make the bundle feel continuous by setting 1 - 2 rounds per map in the lobby's own `NumRounds` row (host; stock).
- **Premises that must be read before R1 is built:** (a) that the session returns to the lobby after the match ends (stock FA lobbies
  persist across matches: GUESS, never logged); the state number of that return is unknown (blueprint 5.2 / E3: log the `net: state
  0x.. -> 0x..` lines in one solo round-trip); (b) that `MP_SelectedLevel` is re-read by the lobby widgets then.
- **R3 (mid-match map change):** `0x89fa20` "next round / level change" loads `slot15(settings+0x18c)`, known callers are the Coop
  rules only (fa_slots.md). NOT ESTABLISHED for FA; a reload probably resets score and money. Research only, after R1 runs.
- **R0 (Arcade):** the same cursor on `Heist_SelectedLevel` when `HeistModeMenu` returns after a session. No network. Build and test the
  whole playlist / random / maps.ini code here first.
- Rejected: one rotating folder behind one slot (R2): needs a build of every map per slot and the lobby would lie about the map.

## 6. Ranking and build order

Feasibility (1 = most feasible), with the evidence level:

| # | part | difficulty | why |
|---|---|---|---|
| 1 | Options page, local player, Arcade (character, mask, outfit already; add gun, vote rows as stubs) | low | XML + option wrappers proven live (W1 - W6); only the element budget is unread |
| 2 | Playlist / random in Arcade (R0) + `maps.ini` | low | game's own selector + hook cursor; no network; also exercises the table the vote uses |
| 3 | Steam transport, log-only (read own lobby data, write `kl_probe`, member data round trip) | low-medium | slot offsets PROVEN, behaviour needs one solo lobby (blueprint E3); first-ever online run with this hook |
| 4 | Prerequisite P: folder force + fingerprint gate | medium | klslot input is small; the gate byte reader `0x5e1510` is not fully read; needs a second peer to prove |
| 5 | Map vote (host side, apply via the game's selector) | medium | tally trivial; "apply to the lobby" is the unknown, testable solo |
| 6 | Starting gun | medium | needs the equip write read first; local and master-owned, no wire work |
| 7 | Online playlist between matches (R1) | medium | needs the lobby-return behaviour logged first |
| 8 | Character cast, "once per match", seen by everyone | hard | Steam id -> session number -> player index not established; mask / outfit not replicated; second peer needed |
| 9 | Map change inside a match (R3) | research | no evidence FA uses `0x89fa20` |

Build order (each step is one session of work and one live check; "N" = a live check only the owner can start):
- **B0 (static, no run):** read the equip write behind the shop buy; read `0x817160` and the session record (Steam id, number); read `0x5e1510`.
  Add a one-off log of the menu element count. Output: three short notes appended to this file.
- **B1:** `klpm.c` (NEW file, included from klhook.c with a minimal Edit; build.bat / KLHook.ini only gain a line each; keys `[Match] Enable`,
  `Playlist`, `Mode`): option names `KLGun`, `KLVote`, `KLPlay` on top of the klchar wrapper; value storage; `maps.ini`; tally and cursor
  as pure functions with an off-game test (same style as klcrew_test.c). Overlay: extend mkoverlay.py's Heister window (or a sibling
  `KLMatch`) and the "Match options" entry; stage a build under `build\pm_1018\` with install .ps1 + .bat + undo .bat (owner installs).
  N1: Arcade, page opens, every row steps, values survive a map load.
- **B2:** Arcade playlist (R0). N2: three maps in a row.
- **B3:** transport, log-only. N3: host a private lobby alone, leave, host again (blueprint E1 + E3 in one run); fills section 5.2's unknowns.
- **B4:** prerequisite P and the cast / vote publication (`kl_opt`, `kl_cast`, `kl_map`). Needs N4 with a second player (stage-0 style).
- **B5:** vote applied (host), gun applied, R1 playlist. N5 (two players).
- **B6:** online cast + remote bodies, once B0's reading is done.

## 7. Risks and open questions (GUESS list)
1. Whether the hook may call Steam from the game thread without a CEG/integrity consequence: klsteam.c already proxies the stats interface
   on every hooked machine, so a plain call through the export is the same class of act; still never run on a TEST build online.
2. FALobby input and a button inside it (3.1); the lobby widget set may also refuse unknown windows.
3. `GetLobbyMemberByIndex` order = join order (3.2).
4. Writing `MP_SelectedLevel` re-targets the session map for the clients (5.1), including the "available" gate for a DLC-less peer.
5. Lobby return after the match, and which state number it is (5.2).
6. Menu element table headroom (section 1).
7. The wire strings are short but visible to friends in the lobby; contain no Steam id of ours, only `kl_cast` carries ids the lobby already shows.
8. Whether a peer with a different hook build and the same files can still enter (`kl_ver` mismatch -> that member is treated as stock; the cast skips it).

## 8. B0 results and B1 state (2026-10-18; static reads of kl2.exe, nothing run; GUESS marks what is inferred)

### 8.1 The equip behind the shop buy (answers 3.3's "step zero")
- 0x7558ce is NOT the buy. It is the opener of the window FABuyWeaponsNew (MercsFAStatusReady input routine, message 0x81 -> 0x6bee50).
- 0x7f73d0 is the weapon-row selector input (MercsFASelectorWeapons; options MP_Weapon_Screen / MP_Weapon_PageIndex). Checks in order:
  already owned (bytes at 0xced638 / 0xced639 = current primary / secondary row), rank (0x8a3e40, 0x6a9d50), DLC (vtbl+0x38 of the object
  at [0x168f750], "NeedToBuyDLC" / "NeedToHigherRank"), price (0x6a5260(row) against money), availability (0x808220). On success it opens
  the window BuyWeaponDialog (0x7f7586).
- 0x76b840 is that dialog's handler. Case 8 (confirm) sends a remote method call through the object's vtbl+0x124 with the RMC id word
  at [edi+0x88]; that word is ZServer RMCBuyWeaponPack (iPrimaryWeapon, iSecondaryWeapon), registered in 0x6f69e0 at 0x6f6fc3.
  ZClient also has RMCSetPrimaryWeapon (+0x94), RMCSetSecondaryWeapon (+0x9c), RMCSetProtectionSuit (+0x96) (registered 0x722540).
- Server side: 0x8ea990 (and the variant 0x55d3e0) price the three rows with 0x6a5260 / 0x8736f0, deduct `sub [money+0x38]`, then write
  `byte [rec+3] = primary row, [rec+4] = secondary row, [rec+5] = suit row` into the player's 0x7c-byte crew record
  (table at rules+0x348, stride 0x7c, money field rules+0x5f8). Rows are the 36 shop rows (table 0xbd1f68).
  Neither has a direct E8 caller (called through the RMC dispatch, i.e. a vtable) - the call chain from RMCBuyWeaponPack to 0x8ea990 is
  GUESS.
- CONSEQUENCE for KLMGun: the equip IS "write three row bytes into the crew record of the player" (money check skipped) and the client
  field m_iPrimaryWeapon / m_iSecondaryWeapon follows through the replication of the record (GUESS: not read). A hook can only do it by
  a heap write at a known moment (after the record exists, before the spawn reads rec[3..5]; the spawn reader is NOT read) or by calling
  the RMC handler with a fake price of 0. Neither is safe enough to ship blind: KLMGun stays a VALUE (klpm.c says so); next read: the
  spawn-time reader of rec[3]/[4] and the vtable that dispatches 0x8ea990.

### 8.2 Steam id -> player slot
DDL_ZClient property setter 0x8da640 (vtable 0xbd4f7c slot 18) gives the object layout: m_iClientIndex +0xdc, m_iClientSessionState +0xfc,
m_iOnlineServiceID +0x180 (ZOnlineUserID = uint64[5]; element 0 = the Steam id is GUESS), m_iPrimaryWeapon +0x1dc, m_iProtectionSuit
+0x1fc, m_iRMCPlayerIndex +0x21c, m_iReadyForPlay +0x25c, m_iSecondaryWeapon +0x29c, m_iTeam +0x2bc, m_iUseMask +0x33c, m_szName +0x35c.
Chain (GUESS): lobby member Steam id == m_iOnlineServiceID of one ZClient -> that client's m_iClientIndex / m_iRMCPlayerIndex is the
session player number. How the list of ZClient objects is reached from the session (0x817160 is virtual: `[[session+4]->vtbl+0x3c]`)
is NOT decoded; so 3.2's "cast" and the vote's per-player count stay B4/B6 work, and the solo parts do not need it.

### 8.3 Availability gate
0x5e1510 returns 1 when 0x87c980 (co-op), else byte `[obj+4+slot]` of the object at [0x168f750]. Its filler (0x7ca830 / 0x73f270) is
still unread, as before; nothing in B1 relies on it.

### 8.4 Menu element headroom
Live log (KLHook.log, v27c overlay): `menu: table 5065 of 5096` = 31 free. The Match window costs 20 table entries (19 window tags +
1 Options button: mkoverlay's `table_tags` 4353 -> 4373), leaving 11 free by that live number (8 if the installed overlay's tag count is
the 4353 the current ini gives, i.e. 3 more than the 4350 of the v27c note). Budget: lean page, no arrows / focus bars / lines / icon.

### 8.5 B1 as built
- `klhook/klpm.c` (5a2934b3, 021774a4): options KLMGun 0..36, KLMVote 0..N, KLMPlay 0..2; off unless `[Match] Enable=1`.
- `klhook/mkoverlay.py`: window KLMatch (Options menu button "Match options" after "Mod settings"), rows Character (KLChar, 17), Gun
  (KLMGun, 37: "Level default" + "Shop gun 1..36", GUESS: the shop rows have no names in the exe), Map vote (KLMVote, 1 + maps.ini maps),
  Playlist (KLMPlay, 3). Built only if the ini has `[Match] Enable=1` (Menu=0 leaves it out). Map names from `klhook/maps.ini.sample`
  (or env KL_MATCH_MAPS). The vote row's entry count must equal the maps.ini count the DLL loads (nobody checks - GUESS).
  Not seen in the game: keyboard Left / Right on a ToggleText without arrow elements, and the button's place in the Options column, are GUESS.
- `klhook/maps.ini.sample`: 10 expansion maps (pages 2 and 3 of the Arcade list), the 9 stock slots DD01..DD09, 2 bundles.
- B2 (Arcade playlist) is NOT built: choosing the next map needs a write to the session's selected-level option or a slot rewrite at the
  moment the results screen ends, neither read; stops at B1 as the task allows.

### 8.6 Review of 34b8ba8d (2026-10-18)
- Staged overlay re-built: the live ini's page 3 names `LevelPicture_M06` / `LevelPicture_FA01`, which the installed `Overlay\Scenes\kaneandlynch.zip` does not hold (only DM05A); a missing Graphic is a boot risk. Overlay now built with those two `Picture=` lines left out (stock L02 / L03 pictures), md5 f9e058ac78340e76844a754998861794. Table estimate unchanged (4373 tags, live 5088 of 5096, 8 free).
- install_pm.ps1: a second run no longer overwrites `dinput8.dll.before-pm1018` with the already-installed dll.
- Off by default confirmed: no [Match] Enable=1 -> mkoverlay builds no page, klpm answers -1. Checked: the KLMatch XML follows the Mod settings pattern (names unique, KLFocus guard, 4 rows, entry counts = option ranges).
