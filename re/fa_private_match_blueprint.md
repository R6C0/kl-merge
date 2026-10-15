# KL Merge in ONLINE Fragile Alliance (private match): blueprint

Worker `mp`, 2026-10-15. Design document only, no patch. Base = `~/base72` (git a5954d4). Static reading of the
repo's notes and the hook sources, plus a look at the owner's installed folder. **Nothing in this file has been run.**
Tags: `file:line` = where the claim comes from (re/ and klhook/ paths are relative to the repo); **EXE (via note)** =
a kl2.exe address an earlier note read (not re-read for this note); **GUESS** = my inference, not checked.

The owner's request: "all of this in the real Fragile Alliance multiplayer mode as a private match, people can change
their characters in there, and maybe a map option that rotates through multiple maps".

Short version:
- **Maps online are cheap.** The peers are sent a **slot index** (0..8), not a map name. Each machine turns it into a scene
  name through its **own** level list, and klslot's file redirect sits underneath that. So a Dead Men map loads online
  on every machine that has the same files and the same redirect page (re/netcode_fa.md:23-30, 1.1-1.3).
  The missing parts are (a) a way to give every peer the same page, (b) a guard that nobody with different files gets
  into the match.
- **Most of what we built does NOT exist online.** AI heisters, balance, down/adrenaline, fed, talk, crew, our HUD and
  character swap all use the Arcade rules class `ZGameRulesHeist`. Online uses the `...Sv` / `...Cl` classes, which lay
  out memory differently, so these parts do nothing there (re/netcode_fa.md:175-200). What carries over online is
  **level data** (the maps, loot, escape vehicle, police spawn points, police bodies) and the Steam guard.
- **Two hook parts are not gated by mode and WOULD act online today:** klgun (klgun.c:365 checks only the game type)
  and kljoin (no mode test, klhook/kljoin.c:202-208). A third one, klrappel, is gated only by whether the level has
  the file (klrappel.c:44). The owner's ini has `[Guns] Enable=1` and every installed map has a KLGuns.ini, so klgun would act.
- **Character choice online** can probably reuse the game's own body routine: slot 137 online = 0x74ee10 calls
  `GetHero(2, index)` on the table at `rules+0x208` (re/menus.md:439-442). The plan is for every peer to write the same
  table. The masks and outfits are a variant byte that is GUESS-not-replicated, so every peer would have to apply them.
- **Rotation:** within a match, every round runs on the level that is already loaded (re/fa_round.md:445). The easy
  version is a playlist **between matches**: the host's hook moves the lobby's map selection on to the next entry.
  Rotating between rounds needs a level change inside a match (0x89fa20, re/fa_slots.md:78) and is NOT ESTABLISHED.
- **This PC alone can test the host side**, but not two peers. Steam runs one game per account, the transport finds
  peers by Steam id, and there is no second account (re/netcode_fa.md:338-347). Three solo experiments are in section 7.

---------------------------------------------------------------------------------------------------------------------

## 1. How Dog Days' online Fragile Alliance works

### 1.1 Stack
- **Net-Z 2008.9 SP1** (Quazal) for object replication, carried as **Steam P2P packets** (`SteamNetworking003`,
  `Quazal::SteamSocketDriver`). Matchmaking uses **Steam lobbies** (`SteamMatchMaking008`). There is no Rendez-Vous
  server and **no GFWL** (re/netcode.md:21-29, 45-60; the strings `SteamMatchMaking008` / `SteamNetworking003` are in
  the installed `steam_api.dll`, checked 2026-10-15). The `...Wintel` class names are the PC platform layer
  (`ZOnlineServiceWintel` thunks into the Steam service, re/antitamper.md:109), not Windows Live.
- Lobby data keys the game writes: name, Scenario, GameType, FAGameMode, RoundTime, NumRounds, Ranked, Rank,
  CoopDifficulty. These are for the search page only. **`Scenario` is not what peers load** (re/netcode_fa.md:62).
- Anti-cheat: none found. There is no file hash between peers, and the one reader of the server's version text
  throws the value away (0x53919c, re/netcode_fa.md:76). Join code 3 "Clash" exists, but nobody has found where it
  is raised (re/netcode.md:29-30, 498). There is no VAC import (GUESS: the import list at re/netcode.md:58 has none).
  **Valve CEG** code-integrity checks are compiled into the exe, and session paths run more of them (CreateSession is
  CEG-wrapped, re/netcode.md:91-93; re/antitamper.md:100-112). Our SHIP hook writes only import slots and data
  (klhook.c:287, 346), which is the design rule for anything that has to survive a session (re/antitamper.md:218-226).

### 1.2 Menu, lobby kinds, ranked (EXE, via re/netcode_fa.md:53-66 and re/menus.md:376-385)
- Path: `OnlineMenu` -> `FAPlay` -> `XboxLiveStart` -> `XBoxLiveCreate` / **`XBoxLiveCreatePrivate`** / `...Ranked`.
  There is also `SystemLinkCreate` (LAN). The options are `MP_RankedGame` (0 ranked, 1 player match, 2 system link) and
  `MP_PrivateGame` (0/1).
- Create 0x6c9c10: property word bit 4 = PRIVATE, bit 5 = RANKED. A session that is both loses PRIVATE. The Steam lobby
  type is ranked -> 3 (invisible), private -> **1 (friends only)**, otherwise 2 (public).
- The host's lobby `FALobby` (`ZMercsFASelectorLobby` slot 10) steps `LobbyLevelNameToggler` and passes the **slot**
  to the session.
- **The start gate** 0x6c49a0 (0x6c4cf5..0x6c4d8c) is the game's own "everybody owns this map" check, built for DLC.
  The host's `available[slot]` byte (`[[0x168f750]+4+slot]`) and every client's replicated `m_iAvailableLevels` must
  say yes, or the countdown is reset. A client without the map sees `Online/MissingContentPackClient` (0x6c4bcd).
  The countdown also needs players >= `[sm+0xb9]` (re/netcode_fa.md:331, 8). **Which minimum the menu sets is NOT
  ESTABLISHED**, so it is unknown whether one person can start a round alone (experiment E1).
- The load: host 0x6c536f and client 0x491fd1 each call `levellist->slot15(levelIndex)`. `-o MPMap` replaces the name,
  **but only on the machine whose command line has it** (re/fa_slots.md:62-74).

### 1.3 Who is authoritative (re/netcode_fa.md:177-185, re/netcode.md:28-31)
- Each machine is master of its **own player** (position, heading, aim, input, inventory). Movement is sent unreliably,
  min 100 ms / max 2000 ms between updates, with dead bands (re/netcode_fa.md:256-268).
- **The server (= lobby host, ASSUMED)** owns the AI actors, the score, money and escape state, the level state (doors,
  money containers, `SetActorActive`), traitor decisions, and dying-into-police (`RMCRespawn`).
- Damage: `RMCReceiveHit(m_refOwner, m_eDamageType, m_refWeaponTemplate, m_iDamage, m_iHeadshot)`
  (re/netcode.md:595). ASSUMED: the shooter's machine decides the damage number (re/netcode_fa.md:196).
- Rules classes: `ZGameRulesFragileAllianceSv` 0xbd2eb4 (host), `...Cl` 0xbd31e4 (client), `ZGameRulesHeist` 0xbd3514
  (Arcade only). They are siblings that share 62 / 66 of 203 vtable slots. **The Arcade crew records (0x7c bytes at
  rules+0x348) are 0x74 bytes at rules+8 online** (re/netcode_fa.md:182-185).
- Game type `[sm+0x5c] == 4` is the **whole FA family, Arcade included**. Online is told apart by the net role
  `[sm+0x54]` = 2 (server) / 3 (client) (re/netcode_fa.md:63, klnet.c:16-20).

### 1.4 What the hook already has for online
- **klnet.c is WIRED** (klhook.c:619, 739, 1068), unlike the "NOT WIRED" its header still says (klnet.c:8). Its log
  part (`[Net] Log=1`) only reads: role, rules class, lobby id and private/ranked bits on a host, level index, and the
  twelve Net-Z update numbers. `[Net] Tune=1` changes those numbers for a host of a friends-only lobby, or for a client
  only with `TuneClient=1` (klnet.c:391-403; re/netcode_fa.md:352-385). The owner's KLHook.ini has **no `[Net]`
  section**, and the installed KLHook.log has **no `net:` line**. **Live check N1 has never been run.**
- klsteam.c blocks stats, achievements and leaderboard uploads on any level that is not the stock one of its slot,
  in **any mode** (klsteam.c:1-60; re/netcode_fa.md:188). The online board path 0x65d950 (`KL2_FA/UCC/TM_TotalMoney`)
  goes through the same import, so it is covered on every **hooked** machine (re/leaderboard.md:317-320).
- klslot.c's page latch: `kls_page_now()` = forced `[Expansion] Page` or the latch read from the menu's window stack
  (klslot.c:212-215, 365ff). The latch is dropped when the frontend shows a window stack without a map page for 1 s,
  so **with the owner's ini an online match loads STOCK maps today** (re/netcode_fa.md:78-90). That is the safe default.

---------------------------------------------------------------------------------------------------------------------

## 2. Every player loads the same Dead Men map

### 2.1 Why it has to be the same bytes
Peers refer to entities by **16-bit scene references** (`m_iGeomRef`, weapon refs, money containers, the escape
vehicle ...). If two machines load different archives for the same slot, every reference points at a different
object: desync at best, crash at worst (re/netcode_fa.md:94-103). Two **builds** of the same Dead Men map are just as
bad, because entity ids change whenever an entity is added. Rebuilds happen daily: DM09's zip was hand-installed on
10-14, md5 86447af9 (NIGHT_PLAN 23:32 entry).

### 2.2 What must be identical on every peer
| item | where | note |
|---|---|---|
| the map archives + .WHD/.WAV/_LS files | `<DD>\KLExpansion\Maps\<id>\` | per redirected slot |
| the per-map ini files the hook reads | `KLJoin.ini`, `KLGuns.ini`, `KLWardrobe.ini`, `KLTalk.ini` beside each archive (all installed maps have KLGuns + KLWardrobe; DM03A/DM09/T01 KLTalk) | KLJoin/KLGuns change behaviour online (section 3) |
| the overlay `Overlay\Patch01.zip` (menu XML) | klslot.c:21-27 | menu only, but it holds the online button of 2.4 |
| the redirect table `[Redirect.N]` and the page number | KLHook.ini | today `[Redirect.2] F01=DM01 F02=DM02 F03=DM03 F04=DM06 F06=DM09 F07=DM03A` (owner's ini) |
| the hook DLL (build stamp) | dinput8.dll | parts that act online must agree |
| any number a peer puts on the wire (damage, health) | KLHook.ini `[Balance]` | only if balance is ever allowed online (3.3) |

### 2.3 The fingerprint (refines re/netcode_fa.md 2.4, NOT BUILT)
- **Do not hash `manifest.json`.** It is stale on the owner's PC: it says `Maps/DM09/F06_Main.zip` is sha1 92f0f0fa,
  218,983,203 bytes, but the installed file is sha1 17e6a68a, 180,318,765 bytes (checked 2026-10-15). Maps are swapped
  in by hand between tree builds.
- **Do hash what is actually there**, cheaply. klsteam.c already has `klx_fingerprint(path, &size, &hash, &ft, extra)`:
  size + zip **central-directory hash** (klsteam.c:177-179), which covers every member's CRC without reading 180 MB.
  Fingerprint = H( for each slot in the active page: slot, folder, size + CD hash of `<slot>_Main.zip`, sizes of the
  .WHD/.WAV, CRC of each KL*.ini beside it ) + H(overlay Patch01.zip CD) + the hook build stamp + H(the `[Redirect.N]`
  lines). Compute it once at startup and again whenever the page changes. Log it as `net: fingerprint <hex> (...)`.
- Publish and compare it through Steam lobby data (re/netcode_fa.md:152-158):
  - every hooked peer sets `SetLobbyMemberData("kl_fp")`;
  - the host sets `SetLobbyData("kl_page")`, `"kl_fp"`, `"kl_ver"`;
  - clients poll `GetLobbyData`.
  The vtable offsets +0x48/+0x4c/+0x5c/+0x60 of `SteamMatchMaking008` are **ASSUMED**: they must be checked against
  steamclient.dll's adapter class, as klsteam.c did for ISteamUserStats (klsteam.c:17-25). `C:\Steam\steamclient.dll`
  is not under the VM's mounts, so this has to be done on the PC.
- **The guard uses the game's own gate** (re/netcode_fa.md:160-167). While the lobby is not unanimous, each hook holds
  the `available` byte `[[0x168f750]+4+slot]` at 0 for the redirected slots. Not unanimous means: a member with no
  `kl_fp` or a different one, or a lobby that is not friends-only, or one that is ranked. Then the host's countdown
  cannot start, and a mismatched client gets "missing content pack". klslot already writes this byte the other way for
  renamed slots (klslot.c:93-94). ASSUMED: that byte is all the gate reads (0x5e1510 was not read in full).
  - A peer **without the hook** publishes nothing, so the match can never start. That is the right answer, because a
    stock peer would load stock Airport and its own unguarded stats would be written.
  - **Never** set this byte to 1 for a DLC slot (F05/F08/F09) the player does not own (klslot.c:94;
    kl_expansion.py:112).

### 2.4 Giving every peer the same page
- **Stage 0 (no code, test evening only):** `[Expansion] Page=2` on **every** machine (re/netcode_fa.md:128-144).
  No guard at all, so this is for invitation-only rounds between friends, and the line comes out the same evening.
- **Real form:**
  - add a host button "Dead Men maps (private)" on `XboxLiveStart`. It opens a copy of `XBoxLiveCreatePrivate` named
    `XBoxLiveCreatePrivate2`, so klslot's window-stack latch reads page 2 the same way it reads `HeistPlayMenu2`;
  - the latch is kept while a lobby exists (klnet sees `[S+0x35e]` non-zero);
  - clients take the page from the lobby's `kl_page` and only if the fingerprint matches. The single code point is
    `kls_page_now()` (klslot.c:212), which asks klnet first.
  - **Menu room:** the menu manager's element table had a margin of about 4 entries after page 3 ("A FOURTH PAGE OR
    ANY NEW MENU ELEMENT NEEDS ROOM MADE FIRST", CLAUDE.md:223). A copied lobby-create window has to be a `Lean=1`
    copy, or room has to be made first. **This is the first blocker for the menu part, not for the netcode.**
- The lobby list and briefing still show the **stock** title and picture for the slot (re/netcode_fa.md:24-26). The
  Arcade map page overlay renames titles only in the Arcade window. A renamed online `LobbyLevelNameToggler` needs the
  same overlay treatment (mkoverlay). GUESS: the toggler takes its texts from `<Text>` children like the Arcade one.

---------------------------------------------------------------------------------------------------------------------

## 3. Host-authoritative or per-client: what each feature becomes online

Gate legend: **H** = Arcade-only via `klb_read` / Heist vtable, so it does nothing online; **M** = game type 4 only,
so it acts online; **L** = gated only by the level file; **-** = no gate.

| part (file) | gate today (evidence) | online today | what it should be online |
|---|---|---|---|
| klslot redirect / overlay | - (klslot.c) | loads stock unless `Page` is forced (1.4) | same on every peer, page from the lobby (2.4) |
| klsteam Steam guard | - (klsteam.c:5-42) | blocks on non-stock, every mode | keep. Every peer must run it (a stock peer writes its own stats) |
| klnet log / tune | net role (klnet.c) | wired, off | E1 first |
| AI heisters: klbot, klescort, klhop, klmove, klgrudge, klcrew, klcrew_rt, kltalk, klbotdown | H (klbot.c:21-24, 347; klhop.c:294; klcrew.c:224; klcrew_rt.c:249; klbotdown.c:266) | inert | **nothing to drive.** Online FA never runs AI heisters, and empty seats stay empty (re/netcode_fa.md:30-31, 334). Bots online would mean running the Heist tactics under the Sv class: new research, stage 3 |
| balance klbalance | H (klbalance.c:296, 373) | inert | **off online**, or one dial for everyone published by the host (`kl_bal=<hash>`, part of the fingerprint). The Arcade per-level tuning floats are not the online damage path. Online, the shooter's `m_iDamage` decides (ASSUMED), so a dial that differs between peers makes one player's bullets stronger. The health write does not touch the replicated `[player+0x274c]` (re/netcode_fa.md:196) |
| down / adrenaline kldown, kladren | H (kldown.c:1321; kladren.c:367) | inert | the stock online down-not-dead is replicated (`m_iDownNotDeadFlags`, re/netcode.md:622). Our mash/adrenaline is a local player effect. A port needs the get-up to go through replicated state: GUESS hard. Stock down only for now |
| fed: klfed, klfedkit, FedMirror | Arcade (klfed.c:14-22; klfedkit.c:20-21) | inert | **not needed.** Coming back as police is the game's own online rule (0x6bb910, re/netcode_fa.md:202-219). What carries over is level data: AFTER_DEATH points, the police model per map (`[FedBody]` in KLJoin.ini is applied by the hook, so it is NOT level data), and the AK only as level inventory |
| HUD klhud* | H (klhud.c:64, 104) | inert, so the stock HUD shows | per-client by nature (HUD is local). The scores/names would come from `DDL_ZScoreFragileAllianceContainer` (re/netcode.md:602): a new reader, stage 2+ |
| character klchar | H (klchar.c:268-271) | inert | section 4 |
| guns klgun | **M** (klgun.c:365) | **ACTS** (`[Guns] Enable=1`, KLGuns.ini on every map) | local picture only, no wire effect. Same files means same picture. **Fix: also require role != 2/3, like klbot.c:21** until gun looks are part of the fingerprint |
| kljoin (Retomoto jump) | **-** (kljoin.c:202-208) | **ACTS** on DM09 | each human jumps on his own machine. The jump list's `AITrigger` fires only where he jumped, and AI is the host's, so a client's jump may not start the street police. Int16 positions: Retomoto's parked vans at y -60040 are out of range (re/netcode_fa.md:221-240). **Retomoto online goes last.** Gate it off online until then |
| klrappel | **L** (klrappel.c:44) | **ACTS** on DM09 (`[Rappel]` in KLJoin.ini) | plays the descent on the local player only; others see a slide/streak. Gate it off online |
| klclimb | H (klclimb.c:23, 1282) | inert | the same issue as rappel |
| klmem, klnudge, klfix, klshoulder, klvis, kltex, the UIA fix | - | local | keep |

**Rule for the lead (one small patch, NOT written here):** add a shared helper `klh_online()` = `[[0x168e598]+0x54]` is
2 or 3, and return early in klgun (`klg_*` at :365), kljoin (`klj_tick` at :202) and klrappel (`klrp_tick` at :251)
when it is true. Each of these lines already reads the session pointer or can.

---------------------------------------------------------------------------------------------------------------------

## 4. Character selection in a private lobby

### 4.1 What exists
- Arcade: klchar.c sets the body through the game's own swap. The steps are: `heroes[slot] = model`, `rules+0x33d =
  slot`, call slot 137 = 0x8f5e90 (klchar.c:41-63). Mask and outfit are set through the variant byte
  `[player+0x50]` via 0x88c810 (klchar.c:64-80).
- Options `KLChar` (0..16), `KLMask`, `KLOutfit` live in the DLL through a private vtable on the options object
  (klchar.c:9-38). `KLWardrobe.ini` beside each map lists the 8 Dead Men bodies x 24 outfits. Every installed map has
  one (checked 2026-10-15). The owner's ini: Char=16 Mask=1 Outfit=22.

### 4.2 Online mechanism (EXE via re/menus.md:425-442)
- Slot 137 **online** = 0x74ee10, shared by Sv and Cl. It takes `index = 0x817160(session, record+0xdc)`, clamps it to
  0..7, gets `hero = GetHero(2, index)` = `[rules+0x208+index*4]`, and calls `player->0x783fb0(hero)`. So the body
  follows a per-player **session number**. The client -> player-entity map is replicated
  (`DDL_ZServerClientPlayers.m_iPlayerIndex[12]`, re/netcode.md:578).
- `rules+0x208` is written by slot 135 `Register` (base 0x6761f0, Heist 0x5684f0). **ASSUMED**: the hero table sits at
  +0x208 in the Sv/Cl layout too. The base-class slot names it, but re/netcode_fa.md:182 warns that Heist offsets do
  not hold online. Re-read 0x6761f0 / 0x452a40 / 0x74ee10 first.

### 4.3 Design (NOT BUILT)
1. **Choosing:** the same three options, as rows on the lobby page (`FALobby`, an overlay copy of the Arcade "Heister"
   row; menu room as in 2.4). The value stays in the DLL and the ini, as now.
2. **Publishing:** each peer sets `SetLobbyMemberData("kl_look", "<char>,<mask>,<outfit>")`.
3. **Who wears what, once per match (the owner's stage 3 rule, CLAUDE.md:1050):** the host arbitrates. When a choice
   arrives, it takes the first free character in lobby-join order and publishes the result as lobby data
   `kl_cast = <steamid>:<char>,...`. A clash gets the next free one and a lobby chat line. Greying a taken entry by game
   state needs code (re/menus.md:603, the "grey out by game state" row of 6). Start with "first come, the others are told".
4. **Applying, on every peer:** once the round's player entities exist, each hook needs Steam id -> client index ->
   player index. The last step is `m_iPlayerIndex[12]`. **Steam id -> client index is NOT ESTABLISHED**. GUESS: the
   session record holds the Steam id; it must be found.
   - Body: write `heroes[playerIndex] = model(char)` on every peer, the same table everywhere, then let the game's own
     slot 137 run. GUESS: it runs at spawn, so writing before the spawn is enough. If it runs earlier, call 0x783fb0
     for each remote player as klchar does.
   - Mask and outfit: GUESS, not replicated (the `DDL_ZFFPlayer` dataset list at re/netcode.md:622 has no variant
     field). Every peer calls 0x88c810 for every player entity with that player's variant. This runs on the game thread
     only, and again after every respawn. A dead heister comes back as **police** (type 3). Leave type 3 alone, as
     klchar does now (klchar.c:83).
5. **Data limit:** a wardrobe on every map costs chunks. Retomoto + wardrobe once overflowed the 73,728-entry chunk
   table (re/wardrobe.md:336-342). kl_chars now reuses dead chunk indices. Every map's wardrobe build must stay under
   the limit. It is the same bytes for everyone, because KLWardrobe.ini + the archive are in the fingerprint.
6. Voices and names follow `rules+0x33e` (index -> C1..C9) (re/menus.md:446-450). Online names are Steam personas, so
   leave them.

---------------------------------------------------------------------------------------------------------------------

## 5. Map rotation

### 5.1 Facts
- Nine FA slots are hard-coded: names packed at `[0x168f750]+0x16+idx*0x40`, no spare room, menu permutation
  `0,1,2,3,5,6,4,7,8` (re/fa_slots.md:14-44). DLC slots F05/F08/F09 are never redirected (kl_expansion.py:112), so a
  page has **six free slots** (F01 F02 F03 F04 F06 F07).
- A map is **built for a slot**: the members are `Scenes/Locations/<slot>/<slot>_Main.*` (kl_expansion.py:64-75).
  Installed: DM01=F01, DM02=F02, DM03=F03, DM03A=F07, DM05A=F01, DM06=F04, DM09=F06, T01=F01 (checked 2026-10-15).
- klslot takes the page **per load**, when `<slot>_Main.zip` is opened (klslot.c:64-70). A new table can therefore be
  chosen at every load without mixing two loads.
- Within one match the rounds reuse the loaded level: Ready -> `FAWaitForPlayers` -> the next round "on the same loaded
  level" (re/fa_round.md:445).
- A level-change path exists: 0x89fa20 "next round / level change", which loads `slot15(settings+0x18c)` = the
  **second index** `[D+0x190]^0xac`. Its known callers are the Coop rules slot 7 (re/fa_slots.md:78;
  re/netcode_fa.md comment at klnet.c:31). **Whether FA ever goes through it is NOT ESTABLISHED.**

### 5.2 Options, cheapest first
| | form | how | risk |
|---|---|---|---|
| **R1** | **playlist between matches** (recommended) | `[Rotation] Enable=1 List=F03,F01,F04,F02,F06` (page-2 entries). When the host's lobby is shown again after a match (klnet: role 2, state back to the lobby state - its number NOT ESTABLISHED, see E3), the host's hook sets `MP_SelectedLevel` = next entry (a menu **position**, through 0x80c9f0) via the options interface `Set` (slot 5, a game call on the game thread, as klchar's wrapped object already handles names). The index travels to clients by itself; every peer has the same page-2 table | low. GUESS: the lobby's toggler re-reads the option. Fall back to showing "next: Hot Coffee" in the lobby and letting the host press the arrow |
| R2 | one slot, rotating folder | always slot F03 in the lobby; the host publishes `kl_map=DM06` and every peer's klslot picks that folder at the F03 archive open | needs **a build of each map per slot** (5 x ~0.6 GB more); the lobby shows "Airport" whatever plays; a peer that misses the lobby datum loads the wrong map -> must be in the guard |
| R3 | rotate **between rounds** | after round N the host sets the second index and the game reloads through 0x89fa20 | NOT ESTABLISHED that FA reloads mid-match; a reload resets money / score state (GUESS); research first |
| R0 | Arcade rotation (offline) | the same as R1 on `Heist_SelectedLevel` when `HeistModeMenu` comes back after a session (klslot.c:44) | none online; a cheap way to build and test R1's code alone |

R1 + R0 share the code. Ship R0 first (Arcade, today's playground), then R1.

---------------------------------------------------------------------------------------------------------------------

## 6. Anti-cheat / Steam safety: private only, never ranked

1. **Stats, rank, boards, achievements**: klsteam.c blocks every write on a non-stock level, in every mode
   (klsteam.c:5-42). Achievements stay blocked until the process ends (klsteam.c:27). Keep `Block=1`. Online adds the
   per-player upload 0x65d950, covered by the same import slot on every hooked peer (re/leaderboard.md:317-320). A
   **stock peer** in the match would write its own stats for a desynced round. The guard (2.3) makes that impossible.
2. **Never ranked, never public, while a redirect is active.** Use **both** layers of re/netcode_fa.md:116-127:
   - (a) the availability byte held at 0 unless the host's lobby is friends-only and not ranked. This is data only and
     uses the game's own refusal;
   - (b) optionally, a proxy `ISteamMatchmaking` behind import 0xb107d8, built like klsteam's. It forces `CreateLobby`
     type 1 and refuses `RequestLobbyList` / `JoinLobby` of a lobby without `kl_fp` while a page is active. That covers
     Quick Match, which (a) does not stop on a client (a client cannot read the lobby kind, re/netcode_fa.md:108-114).
   - Until (b) exists: **no Quick Match and no server browser while any `Page` line is set** (the stage-0 rule).
3. **CEG**: the SHIP hook refuses code / .rdata writes (klhook.c:346). Session code runs integrity checks a direct boot
   never reaches (re/antitamper.md:105-112). A run must keep that policy. **Never take a TEST or `direct` build
   online.** Keep the ExitProcess tripwire so an integrity exit leaves one log line (re/antitamper.md:232-236).
4. **Net tune**: only the sender's numbers count, nothing compares them, and they act only in a friends-only lobby
   (host) or on the player's word (client) (re/netcode_fa.md:305-312).
5. **Public play stays stock**: no `Page` forced and no lobby page means stock maps load. That is today's behaviour
   (1.4), and it must stay the default.

---------------------------------------------------------------------------------------------------------------------

## 7. Staged plan

### 7.1 Stages
| stage | what | code | proves |
|---|---|---|---|
| **S0 (this PC)** | E1-E3 below | E3 needs a small probe | host path, solo start, lobby data |
| S1 (this PC) | online gate on klgun / kljoin / klrappel (`klh_online()`); R0 Arcade rotation | small | nothing acts online that should not |
| S2 (needs a 2nd person who owns DD + Dead Men, e.g. luvsic) | N2 of re/netcode_fa.md:417-444: `Page=2` on both, invitation only, F03 = Withdrawal (the simplest single-part map), then N3 tune / `-o DisableSyncChange2` | none | index -> redirect on a client, doors/loot agree, death -> police works, klsteam blocks on both |
| S3 | fingerprint + lobby page + availability guard (klnet v2), the online lobby button (menu room first) | medium | a peer with other files cannot start |
| S4 | lobby characters (section 4), R1 playlist | medium | |
| S5 | Retomoto online; balance online (only after the damage path is read); bots online = research | large | |

### 7.2 The first three experiments on this PC alone

There is no second Steam account. A second kl2.exe under the same account cannot be a peer: Steam P2P addresses peers
by Steam id, one account = one id, and `SteamAPI_RestartAppIfNecessary` is imported (re/netcode_fa.md:338-341;
re/netcode.md:58). **GUESS:** Steam refuses or merges a second copy. System Link (LAN, `MP_RankedGame=2`, create path
0x77e220, no Steam lobby) still runs over `SteamSocketDriver` (re/netcode_fa.md:342-347), so loopback with two copies
is NOT ESTABLISHED and probably fails on the Steam id. **So the experiments below test the HOST side only.** None of
them involves another player, and each runs at a time the owner is not playing (the game is the lead's).

**E1 - N1 + "can a host start alone?"** (no code: existing klnet)
- ini: `[Net] Log=1`. No `Page` key. Stock map, so klsteam lets the owner's real stats through if a round is played.
  Do NOT play a round in E1. The only exit is backing out of the lobby, and klauto never runs online (an unguarded
  session end on the klauto route would write zero totals, CLAUDE.md:986-990).
- Steps: Online -> Play -> player match -> **Create private game**, FA, Airport. Wait 20 s, back out. Create the same
  game a second time in the same process.
- PASS (re/netcode_fa.md:395-412):
  - `net: session: SERVER (role 2) ... rules ZGameRulesFragileAllianceSv; players <min>..<max>`
  - `net: lobby <id> ... PRIVATE (friends only, type 1)`
  - the update numbers
  - every line again for the second lobby
- **Write down `<min>`.** Also note whether the lobby's Start/Ready lets one person start (look at the screen).
- Copy every `net: state 0x.. -> 0x..` line. The lobby-state number feeds R1 (5.2).
- Risk: friends on the friends list can see and join a friends-only lobby. Do it at an hour they are not online, and
  leave at once if anyone joins.

**E2 - a Dead Men map hosted online, solo** (no code, only if E1's min = 1)
- ini: E1 + `[Expansion] Page=2`. The owner must take this line out afterwards, because it would also apply to his
  public play. Also `[Guns] Enable=0`, because klgun acts online (section 3).
- Steps: Create private game -> Airport (F03 -> Maps\DM03 Withdrawal) -> start alone -> play to the van or die once ->
  end through the game's own end/lobby -> quit.
- PASS:
  - `expansion: ... -> DM03` and the redirect lines;
  - `net: server object ...: level index 2 (F03)` and `net: level ...F03_Main.gms: NOT stock`;
  - `steam: ... BLOCKED` at the session end, and Steam's `UserGameStats_*.bin` unchanged;
  - **no** `bots:` / `balance:` / `down:` / `fed:` / `character:` line that wrote anything;
  - by eye: the map loads under the Sv rules (stock HUD, no AI heisters; police AI as the host simulates it), loot,
    van, escape. If he dies: does he come back as police at an AFTER_DEATH point (stock online rule)?
- This is the first proof that a grafted map runs under the online server rules. Escape vehicle, AFTER_DEATH points,
  police bodies and the settings object get read by Sv code that Arcade never ran.
- If min >= 2: try the same from **System Link -> Create** (0x77e220; game type 4, no Steam lobby). Whether it starts
  alone is NOT ESTABLISHED. Still blocked: `-o StartAsServer` (re/netcode.md:83-87), untraced, used only if both fail.
- Risks:
  - a crash in Sv code on a DM-built level (e.g. the online exit / van, re/fa_gamemode.md:23-33);
  - a missing online-only object. Triage with `debug/triage.py`.
  - A friend joining a forced-page lobby would load stock Airport (desync): same precaution as E1.

**E3 - lobby data round-trip probe** (small code: klnet `[Net] Probe=1`, read + one write of our own key, host only)
- What: while this machine is host of a **friends-only, not ranked** lobby (klnet's existing host test), on the game
  thread, once:
  1. get `SteamMatchmaking()` from the loaded steam_api.dll export (do not call through the game);
  2. `GetLobbyData(id, "Scenario")` and `"NumRounds"` (keys the game itself set), and log them;
  3. `SetLobbyData(id, "kl_probe", "<fingerprint>")`, read it back, `GetNumLobbyMembers`, and
     `SetLobbyMemberData("kl_fp", ...)` + `GetLobbyMemberData(id, self, "kl_fp")`.
- Before any code: verify the `SteamMatchMaking008` slot offsets and `ret n` bytes against
  `C:\Steam\steamclient.dll`'s `CAdapterSteamMatchmaking008` vtable, the way klsteam.c:17-25 did it. A wrong slot
  unbalances the stack.
- PASS: the game's own keys read back with the values the lobby shows, and our keys round-trip. This proves the stage-3
  transport (fingerprint + page + cast list) on one PC.
- The same run tests R1's precondition: finish the lobby -> start (if E1 allows) -> back to lobby, and log the state
  sequence and `MP_SelectedLevel` each time.
- Risks:
  - the first Steam calls from the hook: lobby data is visible to friends (harmless text);
  - a wrong vtable offset crashes. Mitigation: exact verification first, TEST build log, and nothing written but
    `kl_` keys.

### 7.3 Risks overall
- **Unrun base:** not one online session has ever run with our hook (no `net:` line in the installed log). Every
  online claim above is static reading.
- Desync from mismatched builds is silent in stock (2.1). Until S3, the stage-0 rules are the only guard.
- The menu element table is nearly full (CLAUDE.md:223). Every lobby button, row and character page competes for it.
- Retomoto: kljoin / rappel / crewjoin are local, AITrigger lists fire on the jumping machine, and int16 coordinates
  matter (re/netcode_fa.md:221-240). It goes last.
- "Spin botty" remote movement is the stock netcode. The tune helps by data, and a cure needs .text = CEG-forbidden
  (re/netcode_fa.md:284-323).
- Bots online do not exist in stock. The owner's AI-crew work does not carry into multiplayer without a research
  project (S5).
- Host leaving / host migration: NOT ESTABLISHED (re/netcode.md:507).

### 7.4 Open questions to read before S3/S4 code (EXE, none read for this note)
1. 0x6761f0 / 0x74ee10: does the online hero table sit at rules+0x208?
2. Steam id -> client index -> player index.
3. The full reader of the availability gate (0x5e1510 / 0x7ca830 / 0x73f270).
4. Whether FA ever calls 0x89fa20 (mid-match level change).
5. The lobby-return state number and whether `LobbyLevelNameToggler` re-reads `MP_SelectedLevel`.
6. The online damage path, for any balance online.
7. `SteamMatchMaking008` offsets.
