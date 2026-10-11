# Dead Men maps in a private Fragile Alliance lobby: what the game does, what the hook must do

Track Q, 2026-10-11. **Static reading of `kl2.exe` build 0490 and of the hook's sources. NOTHING HERE HAS RUN IN THE
GAME, no lobby was made or joined, no Steam call was issued.** It continues `re/netcode.md` (2026-10-09: the first
reading - Net-Z over Steam P2P, the DDL, the update filter) and corrects it where marked. Words: EXE = read in the
disassembly for this note (helper scripts: session scratchpad `q/q.py`, `q/getters.py`; `debug/dasm.py`);
ASSUMED = an interpretation the bytes do not prove; NOT ESTABLISHED = looked for and not settled, or not looked for.

Scope rule for everything below: private lobbies among people who all own both games and hold the identical build;
no public matchmaking, no ranked session, no Steam write (klsteam.c already fails stats / uploads / achievements on
every level that is not the stock one of its slot - that guard is mode-independent and stays on).

---------------------------------------------------------------------------------------------------------------

## 0. In short (for the owner)

1. **Can a private lobby start these maps? Very likely yes, and with what exists.** The peers are not told a map
   name: the host replicates a SLOT INDEX (0..8 = F01..F09) and each machine turns it into a scene name through its
   OWN level list (host 0x6c536f, client 0x491fd1). The hook's file redirect then swaps the archive on each machine.
   So "start Withdrawal online" = the host picks *Airport* (slot F03; the lobby shows the STOCK title) in a lobby while every peer's hook redirects F03 to
   `Maps\DM03`. What is missing is not netcode but (a) telling every hook "this session uses the Dead Men page"
   (there is no map page in a lobby - today the page latch is dropped before the online menu is reached, so an online
   game loads the STOCK map), and (b) a guard that nobody without the identical build is in the session.
   Stage 0 needs **no new code**: both players set `[Expansion] Page=2` for the test evening (section 2.3).
2. **Nothing in the game checks that the peers hold the same level.** No hash, and the one reader of the server's
   version text throws it away (0x53919c). Peers address objects by 16-bit scene references, so a mismatch is a
   desync at best (wrong doors open, shots on the wrong entity) and a crash at worst. The guard has to be ours.
3. **Every AI part of the hook is silent online today** (they test for the Arcade rules class `ZGameRulesHeist`; the
   online classes are `ZGameRulesFragileAllianceSv` / `Cl`, siblings with another layout). Two exceptions: `klgun.c`
   tests only the game type and WOULD write its gun looks in an online FA round; `kljoin.c` (the Retomoto jump) has
   no mode test and moves this machine's own player (section 3).
4. **Online FA has no AI heisters** (the crew records, the loot / board / traitor tactics and the kill-the-left-behind
   rule are all `ZGameRulesHeist`); **coming back as a fed is the game's own multiplayer rule** (0x6bb910): `klfed.c`
   is not needed online. What matters online from the fed work is LEVEL DATA: where the AFTER_DEATH points are, which
   model the eight police player objects wear, what they carry.
5. **'Spin botty'**: the code supports the reading "a remote player keeps turning / slides": heading is sent at most
   10 times a second, only when the remote prediction is off by 10.5 degrees, in unreliable packets, and the receiver
   extrapolates linearly from the last two samples with no cap (0x992f10) until the next packet, at worst 2 s later.
   The reading "the hook's bots / teleports run on one side" is NOT supported: those parts do not run online.
   By data the hook can shorten it (`klnet.c` Tune: twelve numbers, section 4); a cure needs code.
6. **Built**: `klhook/klnet.c` - `[Net] Log=1` (reads only) and `[Net] Tune=1` (data), OFF, not wired; compiles into
   TEST and SHIP. The tune acts for a HOST only in a lobby the game itself made friends-only (read from memory); for
   a machine that JOINED only with `TuneClient=1`, which is the player's word - a client cannot see the lobby's kind
   (2.2). **Not built** (design in 2.4): the lobby fingerprint and the redirect from lobby data.

*Second version, 2026-10-11, after the adversarial review `re/netcode_fa_review.md` (ACCEPT WITH FIXES): its one
MUST and its SHOULDs are in this text and in klnet.c; section 9 says point by point what was done.*

---------------------------------------------------------------------------------------------------------------

## 1. From the multiplayer menu to the level load (EXE)

### 1.1 Host

| step | where | what |
|---|---|---|
| menu | `frontend.xml`: `OnlineMenu` -> `FAPlay` -> `XboxLiveStart` -> `XBoxLiveCreate` / `XBoxLiveCreatePrivate` / `...Ranked`; `SystemLinkCreate` | options `MP_RankedGame` (0 = ranked, 1 = player match, 2 = system link), `MP_PrivateGame` (0 / 1) - re/menus.md 4.2 |
| create | **0x6c9c10** (callers 0x4196e0, 0x447fd0, 0x474e10, 0x7b0370; `ZMercsFAGameModeToggleText` with `GameType="OnlineGame"`, 0x47524e) | builds a `ZSessionProperties` block and hands it to the service's `CreateSession` (vtbl+0xa0 = 0x8e4fe0) |
| the bits | 0x6c9da5 `cmp MP_PrivateGame,1` -> **0x518b50**: property word +8 bit 4 = PRIVATE. 0x6c9dc8 `cmp MP_RankedGame,0 ; sete` -> **0x810df0**: bit 5 = RANKED. 0x6c9dde: a session that is both loses the private bit (0x518b50(0)) | re/netcode.md 3.2 had bit 5 as "the bit written to lobby key Ranked": same bit, now with its source |
| lobby type | 0x8e514b..0x8e5174: ranked -> 3 (invisible), else private -> **1 (friends only)**, else 2 (public); `SteamMatchmaking()->CreateLobby` at vtbl+0x30 (0x705000) | the service keeps: `[S+0x370..)` the property block, `[S+0x36f]` ranked, `[S+0x35e]` the lobby id (written by the create task's completion 0x822900 through the pointer 0x8e5143 passes), `[S+0x390]` own Steam id |
| lobby data | 0x869430: `name`, `Scenario`, `FAGameMode` / `CoopDifficulty`, `RoundTime`, `NumRounds`, `Ranked`, `Rank`, `GameType`; member limit | FOR THE SEARCH PAGE ONLY. `Scenario` is not what the peers load from |
| session | 0x6c9ec4 `push 4 ; call 0x5be510`: game type `[sm+0x5c] = 4`; 0x6c9ca0 `[sm+0xbf]` = the level index; 0x6c9ef6 `SetMapName(levellist->slot15(index))`; `-o MPMap` overrides the name (0x6c9f0b) | **game type 4 is the whole FA family, Arcade included** - Arcade differs by the net role `[sm+0x54]` (0 / 1 local, 2 server, 3 client: 0x7f6850, 0x863a60, 0x4b0a40) |
| lobby | `FALobby`: `ZMercsFASelectorLobby` slot 10 (0x7dc5c1..) steps `LobbyLevelNameToggler`, converts the menu position with 0x746570 and gives the SLOT to the session (vtbl+0x28) | re/menus.md 4.2 |
| may it start | state machine **0x6c49a0** (`ZSessionManagerMultiplayer` slot 27), 0x6c4cf5..0x6c4d8c: slot = 0x746570(`MP_SelectedLevel`); the host's own level list must say 'available' (`[0x168f750]` vtbl+0x14 = byte `[mgr+4+slot]`), and for each of the 12 client slots (0x8fdf90) 0x7ca830(client, slot) -> 0x73f270 must say that client has it (the replicated `m_iAvailableLevels`); else the countdown timer `[sm+0x194]` is reset (0x6c4dd3) | **the game's own 'everybody has this map' gate** - made for DLC, usable by a hook (2.4) |
| load | 0x6c5300..0x6c53db: `-o MPMap` ? `0x86f230(D.mapname)` : game type 4 ? **`0x86f230(levellist->slot15(D.levelIndex))`**; then state 0x12 | D = `[sm+0x84]`, the replicated `DDL_ZServer`: level index = byte `[D+0x1b0] ^ 0xac` (0x467ae0 -> 0x5b1400), game type = byte `[D+0x110] ^ 0xdc` (0x83f980 -> 0x532840), map name = char * `[D+0x234]` (0x4468a0) |

### 1.2 Client

| step | where | what |
|---|---|---|
| find / join | search 0x559dc0 / 0x424840, `JoinLobby` 0x572010 (vtbl+0x34); invite and `+connect_lobby <id>` (0x506cc0) | re/netcode.md 3.3. A friends-only lobby is joined through the Steam friends list / an invite |
| what a join leaves in the service | `JoinSession` **0x6d8640** (`ZOnlineServiceSteam` slot 45, +0xb4; found by the review, re-read): `[S+0x35c]` = 1, the lobby id `[S+0x35e]` / `[S+0x362]` from the search result +0x6d / +0x71 (0x6d8739, 0x6d8746), the ranked byte `[S+0x36f]` from its second argument (0x6d874c) | **it does NOT write the property block S+0x370**: on a client the private / ranked BITS are what the last `CreateSession` on that machine left, or zeros. Who passes the second argument: looked for (calls through +0xb4 near the service getter 0x5c9dd0 or `[sm+0x17c]`), NOT found |
| P2P | lobby chat `SyncLobbyWithNetZ` -> 0x4d2a40 makes the P2P peer table equal to the lobby | re/netcode.md 3.3 |
| the level | **0x491f50** (from `ZSessionHandlerClient` slot 97): `[sm+8]` = `-o MPMap` on THIS machine ? D.mapname : **`levellist->slot15(D.levelIndex)`** (0x491fd1); also min / max players, game type from D | the client never receives a scene name it uses, unless its own command line has `MPMap` |
| missing pack | 0x6c4bcd / 0x6c4e07: a client whose own level list says 'not available' for `[sm+0xbe]` shows `Online/MissingContentPackClient` | the client half of the gate above |
| version | `ZSessionHandlerClient` slot 97, 0x53919c: `call 0x57b2d0` (the string at D+0x250, ASSUMED `m_szVersion`) and the result is dropped; the only test there is latency > 800 -> join code 7 | **no version compare at the one reader**. Who raises join code 3 'Clash': NOT ESTABLISHED |

### 1.3 What that means for the redirect

- The level list is per machine and klslot's file redirect sits BELOW it (the engine believes it loads
  `Locations/F03/F03_Main`; five import slots swap the files). So the redirect acts identically for a host, a client
  and Arcade - **if it is active for that slot on every machine at the moment the archive is opened**.
- `[Redirect]` (page 0) lines are active always, online included. `[Redirect.N]` lines need the page latch; the latch
  comes from an open `HeistPlayMenu<N>` window (Arcade's map page) and is DROPPED when the frontend shows any other
  window stack for 1 s (klslot.c `kls_menu_watch`). The way to the online menu passes the Arcade page and the main
  menu: **with the owner's ini (only `[Redirect.2]`) an online session loads stock maps today.** That is the safe
  default and should stay the default.
- `[Slots]` name mode would NOT help: the index travels, not the name; each peer needs the same `[Slots]` line anyway.

---------------------------------------------------------------------------------------------------------------

## 2. Starting a Dead Men map in a private lobby

### 2.1 One peer has the redirect, another has not

Both load "slot 2". One loads the bank from `Maps\DM03`, the other stock *Airport*. Nothing stops it (1.2). From then on
every `uint16` reference on the wire (`m_iGeomRef`, `m_iRef`, `iKickDoorRef`, weapon refs, money containers, the
escape vehicle, `SetActorActive` ...) names a different entity on the two machines, and player positions are in
another map. EXE for the mechanism (the DDL, re/netcode.md Appendix A); what the receiving code does with a
reference that resolves to an entity of another class, or to none, was NOT read: ASSUMED desync first (invisible
shots, doors, loot) and a crash soon after (the loader's own crash classes: a wrong class behind a reference).
The same holds for two DIFFERENT BUILDS of the same Dead Men map (entity order follows the build: SLOT ids change
whenever an entity is added - CLAUDE.md 'two id spaces').

### 2.2 Private, public, ranked

- The game makes a friends-only lobby when the menu's `XBoxLiveCreatePrivate` path was taken (`MP_PrivateGame = 1`,
  not ranked). The hook can READ that ON THE HOST (`[S+0x378]` bit 4 / bit 5, `[S+0x36f]`; klnet.c logs it).
- **A CLIENT CANNOT READ IT** (1.2: the join writes the id and a ranked byte only; the bits are stale). From memory a
  client knows 'a lobby, ranked byte 0 / 1' and nothing about private or public. Anything that must be 'private
  lobbies only' on a client therefore needs either a datum a hooked host puts into the lobby (2.4) or the player's
  word (klnet's `TuneClient=1`). The game's own lobby keys do not help: none of them says 'private' (the 0x869430
  list in 1.1).
- To make SURE a redirected session is never public or ranked the hook needs one of (none is built):
  (a) the availability gate of 2.4 keyed on those bits - data only: a host whose session is not private keeps the
  redirected slot 'unavailable', so the game itself refuses to start; or
  (b) a proxy `ISteamMatchmaking` behind the import slot **0xb107d8** (`steam_api.SteamMatchmaking`; outside every
  hashed range like its neighbour 0xb107c8, which klsteam.c wraps the same way) that turns the type of `CreateLobby`
  (vtbl+0x30) into 1 and fails `RequestLobbyList` (vtbl+0x10) / `JoinLobby` (vtbl+0x34) of a lobby without the
  fingerprint while a redirect is active. The interface is `SteamMatchMaking008`; every slot's argument bytes must be
  verified against steamclient.dll's adapter class the way klsteam.c did for `ISteamUserStats` before it is written.
- Ranked: `MP_RankedGame = 0` gives lobby type 3 and writes `Ranked`. A redirected session must never be ranked:
  both (a) and (b) refuse it; klnet's tune refuses it too.
- Steam writes at a session end (stats, rank, boards): blocked by klsteam.c on every level that is not stock,
  whatever the mode. A session end on a redirected map therefore changes nothing on Steam on a hooked machine - and
  every machine in such a session is a hooked one, or it is the mismatch of 2.1.

### 2.3 Stage 0 with no new code

On BOTH machines, for the test only: `[Expansion] Page=2` in KLHook.ini (the forced page: every load takes the
`[Redirect.2]` table - F01 F02 F03 F04 F06 are the five Dead Men maps, F05 F07 F08 F09 stay stock), the identical
tree (`kl_expansion.py install` of the same `w_tab*` build; compare `manifest.json`), the identical hook. Host:
Online -> Play -> player match -> **Create private game**, pick *Airport* (F03 = Withdrawal; F01 Subway = Hot Coffee, F02 Bridge = Late Night
Opening, F04 Fish Market = A Walk in the Park, F06 Harbor = Retomoto Tower: the lobby shows the stock title and
picture). Friend joins through the friends list.
HAZARD, and the reason this is a test setting only: with `Page=2` forced, a QUICK MATCH or any public lobby on those
five slots would load the Dead Men map against strangers' stock map (2.1). **Stage 0 has NO guard at all**; the
rules that stand in for one are steps of check N2 (section 7), not advice:
1. while the line is in the ini: join ONLY by invitation / the friends list; never Quick Match, never the server
   browser, never 'Create game' without 'private';
2. both players take `Page=2` out again before they leave that evening;
3. before the host starts the countdown BOTH logs must have the redirect line. A machine without it is on stock
   *Airport*: its own klsteam verdict is 'stock', so ITS stats and rank are written for a desynced round, hook or
   not. Stop BEFORE the countdown, not after.

### 2.4 The design for the real thing (NOT BUILT; every step is data or a Steam call from the hook, no game code)

1. **Fingerprint** = a hash over the installed tree's `manifest.json` `files` table restricted to `Maps\` (name,
   size, sha1 per file; `tools/kl_expansion.py` writes the manifest) + the hook's own build stamp. Computed once at
   start by the hook; logged.
2. **Publishing it**: each hooked peer writes `SetLobbyMemberData(lobby, "kl_fp", <hex>)` (vtbl+0x60) once it is in
   a lobby (`[S+0x35e]`); the host also `SetLobbyData(lobby, "kl_page", "2")` + `"kl_fp"` (vtbl+0x4c) when the owner
   asked for a Dead Men session. How the host asks: an overlay button on `XboxLiveStart`, "Dead Men maps (private)",
   opening a COPY of the `XBoxLiveCreatePrivate` window under the name `XBoxLiveCreatePrivate2` - the same window-stack
   latch klslot uses for `HeistPlayMenu2` (mkoverlay.py makes such copies already). The latch 'net page 2' is kept
   while a lobby exists and dropped with it.
3. **Reading it**: a client's hook polls `GetLobbyData(lobby, "kl_page" / "kl_fp")` (vtbl+0x48) while in a lobby;
   equal fingerprint -> its page latch = the lobby's page (klslot needs one new input: `kls_page_now()` asks klnet
   first); the host's hook polls `GetLobbyMemberData` (vtbl+0x5c) of every member.
4. **The guard, with the game's own gate** (1.1 'may it start', 1.2 'missing pack'): while a lobby with `kl_page` is
   not unanimous (a member without `kl_fp`, or another value; or the lobby is not friends-only / is ranked), the
   hook keeps the 'available' byte `[[0x168f750]+4+slot]` of the five redirected slots at 0 on its machine - a heap
   byte klslot already writes the other way for renamed slots. The host's game then cannot start the countdown, and
   a client's game says 'missing content pack' by itself. ASSUMED: that the byte is all the gate reads (0x5e1510 =
   level list slot 5 was not read whole), and that clearing it for an OWNED base map has no side effect outside the
   lobby (it is put back when the lobby is left). A peer with NO hook publishes nothing -> never unanimous -> the
   host cannot start. A peer who joins a Dead Men lobby with a hook but another build sees 'missing content pack'.
5. Steam vtable offsets used above are from the `SteamMatchMaking008` header as remembered, anchored by the eight
   offsets the game itself uses (re/netcode.md Appendix B: +0x10 +0x30 +0x34 +0x40 +0x44 +0x4c +0x64 +0x68 +0x6c
   +0x78 +0x84 all fall on the remembered order; +0x48 `GetLobbyData`, +0x5c / +0x60 member data, +0x80
   `SetLobbyType`, +0x88 `GetLobbyOwner` are NOT used by the game): ASSUMED until checked against the adapter class.

---------------------------------------------------------------------------------------------------------------

## 3. The hook's parts in a network session

Who owns what (EXE unless marked): each machine is master of its own `DDL_ZFFPlayer` (position, heading, aim, input,
inventory: 0x6300f0 runs only on the master, 0x9425a0); AI (`DDL_ZFFActor`), score / money / escape state
(`DDL_ZScoreFragileAlliance`), level state (`RMCSetGeomActive`, `SetActorActive`, money containers, doors) are the
server's - that the server is always the lobby host is ASSUMED (re/netcode.md 6); an AI order on a client returns
at once (0x760e50, klescort.c 1). Rules: `ZGameRulesFragileAllianceSv` 0xbd2eb4 on the host, `...Cl` 0xbd31e4 on a
client, `ZGameRulesHeist` 0xbd3514 only in Arcade. RTTI: the three are siblings under `ZGameRulesFragileAlliance`;
of 203 vtable slots Heist shares 62 with Sv and 66 with Cl. **None of the Heist offsets the hook uses hold online**:
the crew records are 0x7c bytes at `[rules+0x348]` in Heist and 0x74 bytes at `[rules+8]` in Sv (re/netcode.md 10);
slot 137 (the body swap 0x8f5e90), slot 194 (vehicle), slot 7 / 11 (death), slot 129 (traitor) are other functions.

| part | writes | gate today | online: what it would have to be |
|---|---|---|---|
| klslot (redirect, page, overlay) | file names; 3 heap fields | none (mode-blind) | **every peer the same**; the page must come from the lobby (2.4) |
| klsteam (Steam write guard) | fails 9 `ISteamUserStats` calls on a level that is not stock | none | every peer; keeps a redirected session off the stats, rank and boards. Keep |
| klmem, klnudge, klfix, klshoulder, klvis | local memory reserve, a per-frame call, a score-page count, logs | none | local, may differ per peer. Keep |
| klbot (crew log, traitor tuning table `[0x168d7c0]+0x6ac..`, backstab / bribe / leave / van) | Arcade tuning floats, crew record bytes | `klb_read`: role not 2 / 3 AND rules == Heist | **inert online, and nothing to do there: online FA has no AI heisters** (ASSUMED from the class split: every AI-crew routine read so far is a Heist slot or a tactic that asks 0x7f6850) |
| klescort / BoardAll / FollowOut, klhop, klclimb, klhud | orders to AI soldiers, crew bytes, a mini animation on the local player, HUD strings | `klb_read` | inert. If ever wanted: AI orders = HOST ONLY (a client's call returns); the climb is a local player animation the peers would not see (animation state is replicated by ids, the merged clip must exist on every peer: same build) |
| klcrew, klcrew_rt, kltalk | AI crew models / voices, AI crew teleport at the Retomoto join, speech | game type 4 AND rules == Heist | inert; no AI crew online |
| klfed + klbalance FedMirror | dword `[0x168ea60]`, the round clock; swapped damage pairs | Arcade (`klp_read`, handler == `ZSessionHandlerSP`) | **must stay off; not needed** - 3.1 |
| klbalance (Risk, six factors, health, point-blank) | per-Arcade-level damage floats, player health floats, a private vtable on the database object | Arcade + rules == Heist | **must stay off** until read for online: the six floats are the ARCADE table; online damage goes through `RMCReceiveHit(m_iDamage)` - the shooter's machine names the damage (ASSUMED from the parameter list) - so a dial that differs between peers makes one player's bullets worth more: every peer the same or not at all. The health write does not touch the replicated copy `[player+0x274c]` |
| klchar (body, mask, outfit) | the Heist hero table `[rules+0x208]`, the Heist body swap 0x8f5e90, variant bytes | game type 4 AND rules == Heist | inert. Online the body is the server's choice (`m_ClientPlayers.m_iPlayerIndex[12]`: client -> player entity) and a model swap is NOT replicated: every peer's hook would have to apply every player's choice to that player's entity, the choice carried as lobby member data (`kl_look=<char>,<mask>,<outfit>`). Needs the online slot 137 (0x74ee10) read first. Design only |
| **klgun** (gun looks: hide bits in the loaded `.prm`) | bytes of the level's models | **game type 4 ONLY** (klgun.c line 365) | **acts in an online FA round today** if `[Guns] Enable=1` and the level has a KLGuns.ini. Local picture only (every gun of that type, whoever holds it), no wire effect; peers see different guns. One-line fix for the lead: also require `[sm+0x54]` not 2 / 3, as klbot.c does |
| **kljoin** (the Retomoto jump) | `[gamedata+0x8d4]`, `[0x156b358]` | none: any mode, the level with a KLJoin.ini | 3.2 |
| klnet (new) | nothing; with Tune twelve `.data` numbers | network session only | section 4, 6 |

### 3.1 The fed online

`ZGameRulesFragileAllianceSv` slot 11 (0x46bd40) / 0x6bb910 / 0x6ee860 / client 0x63a0a0 (re/netcode.md 10,
re/fed_respawn.md 1): a dead criminal's client gets `RMCRespawn(bBecomePolice, playerIndex, followClient)` with the
first free player entity whose type byte `[ZFFPlayer+0x273c]` is 3, placed at an AFTER_DEATH point. That is stock
and runs on our builds as it stands (they carry F07's 16 player objects and 5..7 AFTER_DEATH points a map). So:

- `klfed.c` and FedMirror: not needed, must not run (they hold an Arcade-only switch).
- **What remains of track L / M online is level data**, which every peer has by having the same build: the PLACE
  (AFTER_DEATH points - the Retomoto tower-lift fault is the same fault online), the BODY (the model of the eight
  type-3 player objects: 'the yakuza biker on the night park, SWAT on Withdrawal' as a per-map model in the level
  works online; a hook-side model write on the local player would be seen by nobody else), the GUN (the player
  object's inventory is replicated as item + weapon reference, `DDL_SInventoryItems`; an AK as a level weapon bound
  to the police objects works; an AK handed over by a hook write on one machine needs that weapon entity in the
  level and the game's own pickup path to tell the others - NOT read). 'A chance of an AK' online has to be the
  SERVER's draw; in level data it can only be per police object (e.g. three of the eight carry it).
- The crosshair / 'cannot kill before the heist' fault the owner saw as a fed is Arcade's (FedMirror and the rules'
  stage test); online the game's own police rules apply. Not looked at here.

### 3.2 The Retomoto join online

kljoin writes the game's debug jump request when THIS machine's local player enters the box; 0x8f3fa0 moves this
machine's local players. Each human therefore jumps by himself, on his own machine, when he walks into the lift -
which is the right rule for humans - provided every peer has the hook and the KLJoin.ini (same tree).
What the others see: his position samples jump ~190 m. Receiver 0x600eb0 step 4: an offset over 1000 units goes to
0x5f21c0 (ASSUMED: a snap). The sender's extrapolation model gets two samples 190 m apart within one interval, so
for up to one update interval (100 ms) the remote copy can be extrapolated along that line before the next sample
stops it: a visible streak is possible. The game's own teleports use `RMCTeleportToPosition` /
`RMCMoveToPositionWithContinuityBreak` (stubs 0x69ab90, 0x411f40; wrappers 0x63a9f0, 0x4f9570); whether the debug
jump reaches them was NOT ESTABLISHED (none of 0x8f3fa0's direct callees is one of them).
OPEN, and the real risk: the jump entry's 'AITrigger' list fires on the machine that jumped. AI and level state are
the server's: if a CLIENT jumps first, the street's police are started only when the HOST's player jumps (ASSUMED;
how trigger lists of a level run on a client was not read - `RMCBehaviourTriggerEvent` and `ZOnlineTriggerSync`
exist for it). Retomoto is the LAST map to try online; the four single-part maps have no such thing.
Also for Retomoto: position samples are int16 world units with no scale (0x5a0ff0): the playable space must lie
within +-32767 on every axis. Retomoto's tower is at y 19,600..21,000 (inside); its two parked vans at y -60,040 are
outside (not player space). A check of every map's spawn / bounds / route extremes against that range is OWED.

---------------------------------------------------------------------------------------------------------------

## 4. 'Spin botty'

### 4.1 What the code does (re/netcode.md 8, re-read where marked)

- Sender (the player's own machine, 0x6300f0): heading as a running int16 in 1/1024 turn, position as three int16
  world units, stick input as two int8, camera angle, aim point. All `unreliable` behind Net-Z's extrapolation filter.
- The filter, per dataset and per remote station (0x48db30 for player position): no update sooner than MIN ms
  after the last (0x902e80; EXE: a MIN of 0 or less switches the test off); an update when the value differs from
  what that station is predicted to show by more than the TOLERANCE (0x4ac330; the tolerance object holds the
  allowed error squared at +0 - 0x990e40 - and four polynomial coefficients in the distance that this game leaves 0);
  a forced update after MAX ms (0x861430).
- The numbers (EXE: 0x4825b0, whose one caller is 0x7ee35d in the Net-Z start 0x7ee0c0; 0x7ee0c0 is not a vtable
  slot itself: slot 1 of BOTH handlers calls it with ecx = sm - `ZSessionHandlerServer` slot 1 = 0x66a820 at
  0x66a854 (read for this version), `...Client` slot 1 = 0x5f6690 at 0x5f66a3; B = `[sm+0x158]` = 100, constructor
  0x8c4b5b; a tolerance goes in through 0x990f00(tol) = 0x990e40(tol, 0, 0, -1.0): squared at +0, +4..+0x10 = 0,
  degree +0x18 = 0, +0x1c = -1.0):

  | dataset | tolerance obj | value | MAX global | stock | MIN global | file / after 0x4825b0 |
  |---|---|---|---|---|---|---|
  | actor position | 0x168f1e4 | 30 | 0xd34664 | 2000 | 0xd34668 | 150 / B = 100 |
  | actor angle | 0x168f244 | 30 | 0xd34684 | 2000 | 0xd34688 | 150 / 100 |
  | player position | 0x168f440 | 20 | 0xd35420 | 2000 | 0xd35424 | 150 / 100 |
  | player angle | 0x168f4b0 | 30 (= 10.5 degrees) | 0xd35458 | 2000 | 0xd3545c | 150 / 100 |
  | camera angle | 0x168f510 | 40 | 0xd35478 | 2000 | 0xd3547c | 150 / 2 B = 200 |
  | aim point | 0x168f570 | 5 | 0xd35498 | 2000 | 0xd3549c | 150 / 1.5 B = 150 |

  All twelve are `.data` (0xcd7000..0x1692e5c), outside every hashed range (klranges.h).
- The policy pairs 0x4825b0 also sets - (250, 1000) for player position and angle, (50, 250) for the other four -
  are the bounds of a clamp (0x990d80: `min(max(x, [+0xc]), [+8])`) used by 0x991e90 on a time taken from the sample
  history, in four model functions (0x992070, 0x9921e0, 0x9925f0, 0x992760). ASSUMED: the time over which the model
  blends an old trajectory into a new one - a quarter second to a second for a player, i.e. corrections are SLOW,
  not snapped. NEW against re/netcode.md 12 item 4; the meaning is still an assumption.
- `0x990d30` writes global 0x1691d40, which 0x990db0 adds to a time stamp in the update message; the last call of
  0x4825b0 leaves it 0. No effect.
- Receiver model read 0x992f10 (EXE, now read to its end): finds the two samples around the asked time and returns
  `v0 + (v1 - v0) / (t1 - t0) * (t - t0)`. **No cap on `t - t0`**: with no newer sample it goes on along the last
  slope for as long as nothing arrives.
- Receiver 0x600eb0: heading = the extrapolated integer turned into a rotation, no smoothing of its own; position:
  over 1000 units off -> 0x5f21c0, else the remote character is steered by the replicated stick input plus the offset.
- Remote AI: the same filter with the actor numbers; the host is the sender. AI aim is the server's
  (`RMCAimAtTarget`, `RMCFireWeapon`): not driven per peer.

### 4.2 Which reading of 'spin botty' the code supports

- **Supported - a remote player keeps turning (H1 of re/netcode.md):** a fast turn gives two heading samples with a
  large slope; the 'he stopped' sample is one unreliable packet; if it is lost the sender does not resend (it
  compares against what it PREDICTS the remote shows) until its own prediction drifts 10.5 degrees or 2 s pass, and
  the receiver has no cap. Even without loss, each fast flick overshoots for up to 100 ms and is then blended back
  over 250..1000 ms (if the clamp is what it seems).
- **Supported - sliding / jitter:** 10 position updates a second at best, a 20-unit dead band, steering by input.
- **Possible, rare:** the int16 heading wraps after 32 net turns one way (H2).
- **Not supported: 'the hook's bots and teleports run on one side only'.** They do not run online (section 3). The
  one exception is the Retomoto jump (3.2), which would show as ONE streak per player, not as spinning.
- Not established: that any of this is what the owner saw. It needs two machines to see.

### 4.3 What the hook can do by data (klnet.c `[Net] Tune=1`; section 6)

| key | number | stock | try | effect | risk |
|---|---|---|---|---|---|
| `PlayerMs` | MIN of player position, angle (camera 2x, aim 1.5x) | 100 | 50 | twice the update rate while moving / turning: overshoot halves | twice the packets up (per peer: 20 + 20 a second at most) |
| `RefreshMs` | MAX of the four player datasets | 2000 | 300 | a lost 'stopped' packet is repaired within 0.3 s instead of 2 s | ~3 extra small packets a second per dataset per peer while standing still |
| `AngTol` | player angle tolerance | 30 (10.5 degrees) | 12 (4.2 degrees) | a wrong remote heading is corrected sooner | more heading packets while turning slowly |
| `PosTol` | player position tolerance | 20 | leave | | |
| `ActorMs` / `ActorRefreshMs` / `ActorPosTol` / `ActorAngTol` | the AI's (host) | 100 / 2000 / 30 / 30 | leave first | | the host feeds every AI to every peer: the costly ones |

Only the SENDER's numbers count: each peer needs the keys to be seen better by the others. The numbers are not
replicated and nothing compares them, so peers with different numbers do not break each other.
So in a two-player test the HOST's keys change how the friend sees the host and every AI, with no word needed (the
host's lobby kind is read from memory); the FRIEND's keys change how the host sees him and need `TuneClient=1` on
the friend's machine (his word that he joined a friends-only lobby).
Net-Z's own behaviour under load (a send budget? drops?) was NOT read; start with the 'try' column, not lower.

### 4.4 What needs code (not allowed by the hook policy: said plainly)

A cap on the extrapolation time in 0x992f10 / a hold when the newest sample is older than N ms; a reliable 'end of
turn' sample; smoothing of the heading in 0x600eb0; wrapping the int16 heading. Each is a `.text` change in hashed
ranges. A private-vtable form exists only if the model objects (`PHBDRModel`, per dataset per station, made at
0x4675a0 and five siblings) call the read virtually - NOT looked at; that would be the next thing to read if the
tune is not enough. `-o DisableSyncChange2` (a developer switch inside 0x600eb0, 0x601789) is a free experiment:
it is a launch option, no hook.

---------------------------------------------------------------------------------------------------------------

## 5. A plan in stages

| stage | what | needs | proves |
|---|---|---|---|
| **S** (one machine, now) | wire klnet.c, `[Net] Log=1`. The owner alone: Online -> Create private game on a STOCK map, sit in the lobby, leave | nobody else; no redirect | the log's reading of role / lobby / private bit / update numbers (check N1) - and whether a host can start alone: the start gate 0x6c4d8e..0x6c4da3 (read by the review) lets the countdown run only while the player count (0x698250) is >= min players `[sm+0xb9]`, byte `[sm+0x1f4]` is set and the game type is 4. N1's session line prints `players <min>..<max>`: min 1 = one person can start, 2 or more = not (which minimum the menu sets was NOT read) |
| **0** | two PCs, identical tree and hook, `[Expansion] Page=2` on both, every AI key as it is (they are inert online), `[Net] Log=1`; private lobby, *Airport* -> Withdrawal; play one round | luvsic (owns both games) with the owner's tree: `kl_expansion.py` builds it on HIS machine from HIS two installs - no game data is sent | the index -> redirect path on host and client, that an online round runs on a grafted map at all (loot, vehicle, traitor, dying into a fed), klsteam's block lines at the session end (check N2) |
| 0b | the same with `-o DisableSyncChange2`, then with `[Net] Tune=1 PlayerMs=50 RefreshMs=300 AngTol=12` on both | the same two people | whether remote movement / spinning changes (check N3) |
| 1 | the guard of 2.4 (fingerprint, lobby page, availability byte) as `klnet.c` version 2; remove `Page=2` | code + review + stage 0 passed | a peer with another build cannot be started with |
| 2 | wardrobe online (klchar's looks carried as lobby member data, applied on every peer); klgun's role test; balance: decide 'off online' or 'the same dial on every peer' after the online damage path is read | stage 1 | - |
| 3 | bots online | **there is no stock mechanism**: online FA never runs AI heisters, empty seats stay empty. A host-run AI crew would need the Heist tactics on the Sv rules class - new research, not a tuning job | - |
| 4 | the fed online | nothing from the hook: stock. Level data from tracks L / M (points, body per map, AK on some police objects) | seen in stage 0 already |
| last | Retomoto online (3.2) | stages 0-1 on the four single-part maps first | - |

**What one machine can prove:** the log (stage S), the lobby type, every offline check. Not the netcode: Steam runs
one instance of the game per account (`SteamAPI_RestartAppIfNecessary` is imported), and the transport addresses
peers by Steam id. `-o StartAsServer` / `StartAsClient` (0x8733e0) exist; whether a pair can meet without a lobby is
NOT ESTABLISHED (re/netcode.md 12.9).
**LAN:** the PC front end HAS a 'System Link' entry (`frontend.xml` line 5354: `<Platform XENON="True" PC="True">`,
`ZCheckGamerPrivileges Window="SystemLink"`, `MP_RankedGame = 2`), with create / find / server browser pages; its
create goes to another routine (0x77e220 for `GameType="SystemLinkGame"`, 0x47520d) that sets game type 4 and makes
NO Steam lobby; `Quazal::LANSessionDiscovery` is linked. Whether two PCs on one LAN find each other and connect on
the Steam build (the socket driver is `SteamSocketDriver`: peers by Steam id) is NOT ESTABLISHED - it is the one
lobby-free path worth one try by two people in one house; it still needs two Steam accounts that own the game.
No direct-IP page exists in the XML.

---------------------------------------------------------------------------------------------------------------

## 6. klhook/klnet.c (built 2026-10-11, NOT WIRED, NOT RUN)

- `[Net] Log=1`: reads only (session manager, handler, rules class, server object, the service's property bits and
  lobby id, level verdict, the twelve numbers); one line per change; nothing for a local session unless `Log=2`.
- On a machine that JOINED, the lobby line says the id and the ranked byte only ('kind not known on a client'). When
  a network session ends everything said is forgotten: a second, identical lobby of the same process says all its
  lines again.
- `[Net] Tune=1` + numbers: data writes of the twelve numbers of 4.1. ALL of these must hold, else nothing is
  written and what was written goes back (unless the game has set the number again itself):
  1. this machine is server or client of a game type 4 session;
  2. the session state is 0x13..0x1f - after the load state 0x12 (EXE for a host: 0x6c53db), so the level's archive
     has been opened again and the verdict is THIS level's; 0x19 / 0x1f are Arcade knowledge and the window is
     ASSUMED online - if online states lie outside it the tune never acts (it fails shut);
  3. the scene the engine names is the slot of this session's level index (the server object's `[D+0x1b0]^0xac`;
     a host without one yet: `[sm+0xbf]`) - `Locations\F03\F03_Main` for index 2. Not with `-o MPMap`;
  4. that level is NOT stock (klsteam's verdict 2);
  5. HOST: ranked byte 0, ranked bit 0, private bit 1 - the game made a friends-only lobby; read from memory;
  6. CLIENT: ranked byte 0 AND `TuneClient=1`. A client cannot see the lobby's kind (2.2): on a client the 'private
     lobbies only' rule RESTS ON THE PLAYER'S WORD, and the init line, the gate line and the ini say so. Without the
     key a client never writes. (The ranked byte itself rests on JoinSession's second argument, caller not found.)

  Each number is checked before the write (plausible MIN / MAX, a tolerance object of degree 0 with only its first
  float set).
- No Steam call, no game call, no code patch, nothing that makes or joins a lobby.
- Compile check as the rules say, second version (fresh `git archive HEAD klhook` -> `G:\kl_scratch\Q\fix\src`,
  klnet.c copied in, three lines added there): TEST `G:\kl_scratch\Q\fix\test\dinput8.dll` sha1
  ffb5217307edc2ae2fde60f1221087e26de16490, SHIP `G:\kl_scratch\Q\fix\ship\dinput8.dll` sha1
  35d4593f6afd92ca9f9b1b37126a250c4b11617e; no warning from klnet.c at /W3 (the one warning is klhud.c(188), old).
  The first version's pair (`G:\kl_scratch\Q\test`, `...\ship`: a7fed6a7 / 375f554f) has the client fault of the
  review's MUST 1: do not use it. No off-game harness exists for klnet.c (its gate is a chain of memory reads).
- Wiring (klhook.c): `#include "klnet.c"` below `#include "klvis.c"`; `klnet_init();` below `klvis_init();`;
  `klnet_tick(game_thread);` below `klvis_tick();`.

---------------------------------------------------------------------------------------------------------------

## 7. Live checks (for the lead and the owner; in this order)

**N0 - offline, anyone:** the wired hook starts with `[Net] Log=0 Tune=0`: no `net:` line at all.

**N1 - one person, stock map, no redirect** (`[Net] Log=1`): Online -> Play -> player match -> Create private game,
Fragile Alliance, any stock map; wait in the lobby 20 s; back out. PASS = the log has
`net: session: SERVER (role 2), game type 4 (FA family) ... handler ZSessionHandlerServer; rules ...; players
<min>..<max>; ...` - WRITE DOWN THE MIN: 1 = one person can start a round alone, 2 or more = the countdown needs
that many (the start gate 0x6c4d8e) -,
`net: lobby <16 hex digits not all zero> ... PRIVATE (friends only, type 1) - private bit 1, ranked bit 0`, and
`net: update numbers, as they stand (B = 100 ...): ... player position min 100 max 2000 tolerance 20.0 | player
angle min 100 max 2000 tolerance 30.0 | camera angle min 200 ... 40.0 | aim point min 150 ... 5.0`. A lobby line that
says PUBLIC after 'Create private game' means the private bit is read from the wrong place: stop, report.
Also note whether the lobby lets the host start alone (it should agree with the min above).
Repeat it once in the same process (back out to the main menu, create the same private game again): every line
must come a second time. A second lobby without a `net: session:` line = the reset of what was said does not work.

**N2 - two people, stage 0** (2.3; both `Log=1`, `[Expansion] Log=1`, `[Net] Tune=0`). THE STEPS, in this order -
stage 0 has no guard, these steps are the guard:
1. Both: identical tree (compare `manifest.json`) and hook; both put `[Expansion] Page=2` into KLHook.ini. From now
   until step 7 NEITHER uses Quick Match, the server browser or a public 'Create game'.
2. Host: Online -> Play -> player match -> **Create private game**, *Airport*. His log must say
   `net: lobby ... PRIVATE (friends only, type 1)`. PUBLIC or RANKED: leave the lobby at once.
3. Friend: joins by the host's INVITATION / the friends list only. His log says `net: session: CLIENT (role 3) ...`
   and `net: lobby <the same id> ...: JOINED - ranked byte 0; kind (private / public) not known on a client` (that
   is right: a client cannot see it; the host's line of step 2 is the proof).
4. BEFORE the host starts the countdown, both read their logs to each other: each needs
   `expansion: slot F03: menu page 2 from now on -> DM03` (or the forced-page line of that hook build). A machine
   without it would load stock *Airport*, judge the level stock and WRITE ITS OWNER'S STATS AND RANK for a desynced
   round: do not start; fix the ini and begin again at step 2.
5. Start; play to the vehicle; one of the two dies on purpose.
6. Leave the session through the game's own end / lobby, then quit the game.
7. Both take `Page=2` out of KLHook.ini the same evening, before anything else is played online.

PASS on BOTH logs: `expansion: slot F03: menu page 2 from now on -> DM03` and the redirect lines for the zip / WHD /
WAV; `net: server object ...: level index 2 (F03)`; `net: level SCENES\Locations\F03\F03_Main.gms: NOT stock`;
host `rules ZGameRulesFragileAllianceSv`, friend `rules ZGameRulesFragileAllianceCl`; NO line of `bots:` / `escort:` /
`fed:` / `balance:` / `crew:` / `talk:` / `character:` that says it wrote or called something; at the session end
`steam: ... BLOCKED` lines and no change of either Steam stats file. By eye: both see each other, doors and loot
agree, the dead one comes back as police at an AFTER_DEATH point, the round ends for both.
FAIL classes: one side loads stock (its log has no redirect line) -> 2.1, stop at once; a crash -> `debug/triage.py`
on that machine, with both logs.

**N3 - the same two, the tune** (N2's steps 1-4 and 6-7 apply unchanged): (a) both add `-o DisableSyncChange2` to
the launch options for one round (then remove it); (b) both `[Net] Tune=1 PlayerMs=50 RefreshMs=300 AngTol=12`, and
the FRIEND also `TuneClient=1` (his word that this is the host's friends-only lobby; he takes the line out with
`Page=2` in step 7). PASS for (b):
- both, at start: `net: on; Log=1 Tune=1 TuneClient=<0 host / 1 friend> ...`;
- host: `net: tune: acts on this session - as the HOST of a lobby the game made friends-only (private bit 1, ranked 0)`;
- friend: `net: tune: acts on this session - as a CLIENT, on the player's word (TuneClient=1) ...`. With
  TuneClient=0 the friend's log must instead say `net: tune: nothing is written: this machine has JOINED ...` and no
  `number(s) written` line, ever (run that once first: it is the test of the review's MUST 1);
- each: `net: update numbers, the game's, before the tune ...`, `net: tune: 9 number(s) written` (four MIN: player
  position / angle 50, camera 100, aim 75; four MAX 300; the angle tolerance 12.0), and when the session ends or
  the next level loads `net: tune: ... number(s) put back`;
- neither log has a `number(s) written` line before the `net: level ...F03_Main.gms: NOT stock` line of that load.

ALSO COPY OUT EVERY `net: state 0x.. -> 0x..` LINE of both logs from the lobby to the second round's start: the
tune's window 0x13..0x1f is Arcade knowledge. No 'acts' line at all = the online round's states lie outside it:
report the numbers. A put-back / rewrite pair between two rounds is expected (the load state 0x12).
By eye: one player spins the mouse hard and stops, the other says whether the body keeps turning, before and after.

---------------------------------------------------------------------------------------------------------------

## 8. ASSUMED and NOT ESTABLISHED (the list to shrink)

- SETTLED since the first version (EXE, review + re-read): `[S+0x35e]` IS the lobby id on a client (0x6d8739 /
  0x6d8746); 'a client's property bits mean anything' is REFUTED - they are stale, klnet.c does not use them on a
  client; the Net-Z start 0x7ee0c0 is called from slot 1 of both handlers (0x66a854, 0x5f66a3); the start gate
  needs player count >= `[sm+0xb9]` (0x6c4d8e..0x6c4da3).
- ASSUMED: that an online session's states are Arcade's (0x19 round, 0x1f score) and stay within 0x13..0x1f
  during a round (klnet's tune window; N3 checks it); that a client's ranked byte `[S+0x36f]` is right
  (JoinSession's second argument, caller not found); D+0x250 is
  `m_szVersion`; the server station is always the lobby host; online FA never activates the AI heister squads that
  are in the level (stock levels carry them too); the 0x5f21c0 branch is a snap; the (250, 1000) clamp is a blend time;
  the availability byte is all the 'missing content pack' gate reads; the `SteamMatchMaking008` slots the game does
  not use.
- NOT ESTABLISHED: what a peer does with a scene reference of the wrong class (2.1); who raises join code 3;
  whether a host can start a FA session alone; Net-Z's behaviour when the update rate is raised; whether the debug
  jump of kljoin breaks the extrapolation model's continuity; how a level's trigger lists run on a client; the
  online damage path (who scales a hit) - needed before any balance key may act online; system link and
  `StartAsServer` on the Steam build; host migration.
- NOT DONE: the fingerprint / lobby-data / availability guard (2.4); the `ISteamMatchmaking` proxy; a log of remote
  players' heading samples (it would tell H1 from H2: the `DDL_ZFFPlayer` objects have to be found first); a check
  of every map's coordinates against the int16 range (3.2); klgun's role test (one line, the lead's file).
- READ BY THE WORKER ONLY, NOT RE-READ BY THE REVIEW (its point 10): the receiver side (0x600eb0, 0x5f21c0, the 'no
  cap' reading of 0x992f10 - the review saw the two-sample linear form in its first 0x190 bytes), 0x6300f0, the
  online fed chain (0x46bd40 / 0x6bb910 / 0x6ee860), system link 0x77e220, the 62 / 66 shared vtable slots, the
  int16 position claim (0x5a0ff0), the `SteamMatchMaking008` slot numbers of 2.4. None carries code in klnet.c; all
  carry the PLAN: stage 1's code (the guard) and anything of stages 2-4 needs its own review of these addresses
  first.

---------------------------------------------------------------------------------------------------------------

## 9. The review's points and what became of them (re/netcode_fa_review.md)

| point | what was done |
|---|---|
| MUST 1 - the tune acted on a client in any non-ranked lobby | DONE: a client writes only with `[Net] TuneClient=1` (default 0); the header, the init line, the gate line and the ini say it is the player's word; 2.2, 6, N3 |
| 2 - a client's lobby line printed a kind | DONE: role 3 prints id + ranked byte + 'kind not known on a client'; the client's ranked test is `[S+0x36f]` alone; the stale bits are out of the line's change signature |
| 3 - two ASSUMED items settled | DONE: section 8, 1.2, the klnet.c header |
| 4 - signatures never reset | DONE: at every change local <-> network all of them (session, server object, lobby, numbers, level, state, the gate told) are cleared; N1 repeats the lobby to check it |
| 5 - the previous level's verdict in early 0x12 | DONE, both of the review's forms: the window starts at 0x13, and the scene must be the slot of the session's level index |
| 6 - the state window is Arcade knowledge | DONE: marked ASSUMED (header, 6, 8), fails shut, N3 lists the state lines |
| 7a - '0x7ee0c0 = slot 1' | DONE, and the server's call followed: 0x66a820 calls it at 0x66a854 |
| 7b - 'never ranked' on a client | DONE in the wording; the caller of JoinSession was looked for and NOT found |
| 7c - 0x990f00's fourth argument is -1.0 | DONE (4.1, header). No text of this track had said 1.0 |
| 8 - stage 0 has no guard | DONE: 2.3 and N2 carry it as numbered steps |
| 9 - N1 and min players | DONE: N1's PASS list, stage S |
| 10 - not re-read by the review | DONE: listed in section 8 as carrying the plan; no code of klnet.c rests on them |

Refuted: none.
