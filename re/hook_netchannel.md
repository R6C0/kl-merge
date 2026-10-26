# The hook's shared peer message channel (klhook/klnetchan.c, [NetChan])

2026-10-26, cloud agent (worktree, branch rtp-schemas). Built for the UCC suspicion messages (klhook/klucc.c, re/ucc_design.md P5 + OWNER
DECISIONS 6) and meant as THE channel for every later "one peer tells all peers" feature: remote cop-squad orders (re/cop_squads.md 5), the
UCC reveal key (re/ucc_design.md OWNER DECISIONS 1). Static reading + harness only: **nothing here ran in the game.** GUESS = not proven.

## 1. What exists (the search)

| candidate | where | verdict |
|---|---|---|
| Hook UDP broadcast (own socket, ws2_32 looked up) | klhostopt.c 27413, klcharonline.c 27414, klsync.c 27415 | **USED** (port 27416). Outside the game's traffic, nothing of the game is written. Proven pattern: CharOnline carried both peers' looks live over UDP 27414 (open_work_log 2026-10-26 07:15, B2). Reach: same PC (SO_REUSEADDR, broadcast goes to every bound socket) and same LAN = **System Link**. Not the internet. |
| Steam lobby MEMBER data (ISteamMatchmaking008 slot 24 set, 16/17/23 read) through klmm.c's proxy | klbuild.c, klcharonline.c, klhostopt.c (lobby data) | **USED** as the second carrier (key `klx_msg`). The game has no member-data site and no LobbyDataUpdate_t handler (private_match_buildcheck.md 2), so the namespace is free. Reach: every member of the Steam lobby, internet included - **while the lobby exists**, see 2. |
| Lobby chat (+0x64 send / +0x68 read) | the game's own sync protocol: `SyncLobbyWithNetZ`, `SyncedWithLobby`, `ExitLobby` | not used: stock handlers ignore other text (buildcheck 2), but it has the same lifetime problem as member data and needs a LobbyChatMsg_t callback (or polling chat ids). No gain over member data. |
| In-game text chat | - | **none found**. DD's online UI has voice only (options `Online_Voice_Chat`, `Online_Speak`; the lobby's `LobbyPlayerChat_T` tags are the `Speak#` talk icons, re/lobby_12rows.md). GUESS-level: the exe was not string-searched in this session (no game files in the cloud repo). |
| A replicated value to borrow: `m_iCustomFlags:int32[12]` in `DDL_ZScoreFragileAllianceContainer`, set by RMC `SetCustomFlagsOnServer(iPlayerIndex, iFlags)` (re/netcode.md DDL dump) | game state | rejected for now: the bits' stock meanings are not read (scoring / achievements?), writing them is a write of replicated game state, and a client would have to make an RMC call. High risk. |
| The variant byte `[ent+0x50]` (GUESS replicated, char_online.md 5) | game state | rejected: visible side effect (mask / outfit), 8 bits. |
| Stock announcement RMCs on ZServer / ZClient (`AnnounceFAMissionReminder`, `AnnounceFACashMajority(iClientIndex)` ...) | game calls | not now: fixed texts (a `.LOC` re-route per map could reword one, kllocname.c style), a host-side game call that replicates. A real candidate for HOST -> ALL over the internet if option 3a below fails. |
| Steam P2P (the game's own transport, SteamNetworking003 through `Quazal::SteamSocketDriver`, netcode.md 3.4) | game import | not built: see 3a. |

## 2. The lobby lifetime problem (why Steam member data may not help in a round)

Static, from re/private_match_buildcheck.md 2: the host's 0x745c80 marks each member that answered `SyncedWithLobby` and, once all have,
sends `ExitLobby`; every peer's 0x8bd520 then calls 0x700910 (-> LeaveLobby +0x38) **unless byte `[this+0x36e]` is set**. What sets
`+0x36e` is not read. GUESS: in a Quick / Private match every peer leaves the Steam lobby at match start, so member data reaches nobody in a
round. klnetchan.c logs it: `netchan: Steam lobby present / gone` on every change and `Steam carrier not usable now (...)` once a session.
klcharonline.c's Steam half has the same dependency (B2 was System Link: UDP).

## 3. Internet play: options ranked by risk (none built)

a. **Steam P2P proxy (recommended next).** Wrap the `steam_api.SteamNetworking` import exactly as klmm.c wraps `SteamMatchmaking`
   (one import slot, a 003-layout proxy table, tail jumps for the slots we do not override; check the real interface's slot count and
   pops in steamclient.dll first, as klmm.c did for 008). Send: our packets (`KLNC1;...`, the same text) with `SendP2PPacket(+0)` to each
   Steam id of the game's own peer table (global 0x168f960, table +0x28, count +0x2c, 16-byte entries, id at +1, open byte +9: netcode.md
   3.4) - sessions already exist, no new accept. Receive: override `IsP2PPacketAvailable(+4)` / `ReadP2PPacket(+8)`: read the real packet
   into our buffer; a `KLNC1;` packet is handed to klnetchan and the loop reads on; any other packet is kept and reported to Quazal as
   available, then returned by our ReadP2PPacket. Risk: MEDIUM - every game packet passes our code (a bug = broken netcode; latency is
   one memcpy), and Quazal must never see ours (SteamNetworking003 has no channel argument per netcode.md App. B, so filtering is the only
   separation). No byte of kl2.exe changes (import slot, as klmm.c / klsteam.c). Cost M. Bench: two PCs over the internet, Quick Match.
b. **Keep the Steam lobby.** If `[this+0x36e]` is a plain flag, a guarded data write before ExitLobby arrives would keep every peer in the
   lobby and member data would work in rounds. Risk MEDIUM-HIGH: unknown what else the flag gates (joining mid-match? the lobby shows as
   joinable?). Needs the reader of +0x36e first.
c. **Stock announcement RMC re-worded via .LOC** (host -> all only; text fixed per map build). Risk MEDIUM-HIGH: a game call, and texts
   with a `%s` placeholder are not established. Only for host pings, never for accusations from clients.
d. **m_iCustomFlags bits.** HIGH (section 1).

## 4. The protocol (klnetchan_logic.h; klnc_test.c checks it: 151 checks, ALL PASS)

`KLNC1;<sid 8 hex>;<role>;<ent>;<seq>;<TYPE>;<payload>` - one printable line, at most 200 bytes, payload at most 127.
- `sid`: random per process (two games on one PC differ); `role`: the sender's `[session+0x54]` (2 host, 3 client) when it sent; `ent`: the
  sender's own entry in the session player table (`0x6161c0`, klcharonline.c's index; -1 unknown); `seq`: per-sender message number.
- UDP: each message is broadcast Repeat (3) times RepeatMs (300) apart with the same seq. Steam: the member value is the last 4 lines
  joined by '`' (klh_rdstr refuses control bytes), re-written on change and every 5 s, every member read every 500 ms.
- Receivers: drop own sid; keep the first of each (sid, seq) (ring of 64); drop a seq 8 or more below the sender's highest (Steam values are
  re-read forever); dispatch by TYPE to the handlers modules registered with `knc_on`. Payload bytes are sanitised (printable ASCII,
  '`' -> `'`). Nothing is signed: the trust model is a game among friends; 'from the host' = role 2 in the packet.
- Types in use: `UPING` (host's ping text; receivers accept role 2 only), `UACC` (accusation text; receivers rate-limit per sid at 80 % of
  their own CooldownS), `HELLO` (`<ent>|<name>` every 5 s in a UCC round). Proposed: `CQORD` (`<ent>;<order>` cop squad order, host
  applies to that entity's squad control), `UREV` (UCC reveal request, host validates and calls the reveal).
- The channel is idle (no socket, no proxy) unless a module calls `knc_want` at init; klmm.c installs its proxy for it only when `[Ucc]`
  is on and `[NetChan] Steam=1`.

## 5. Live bench (not run) - what needs proving, in order

Two instances on one PC (re/netsmooth_solo.md 6), System Link, stock DD01, lobby in **Undercover Cop**. Both: `[Ucc] Pings=1 Accuse=1
PingMinS=10 PingMaxS=15 Log=2`, `[NetChan] Log=2`, `[Lobby] MinPlayers=2` (the UCC lobby floor is 4), `[HUD] Enable=1` (Popups=1 optional), distinct `[Ucc] Name=A` / `Name=B`.
1. `netchan: wanted by ucc`, `netchan: UDP 27416 open`, `ucc: UCC round, role 2 (HOST)` / `role 3 (client)` (proves the sub-mode word
   1 and the state window 0x19..0x1e).
2. `ucc: my entry in the player table: K` on both (klco_find_own online), then `ucc: entity K is 'A'` on the other side (HELLO over UDP).
3. Host: `ucc: HOST ping names entity ...`, `ucc: shown '...'`; client: `ucc: host ping heard via UDP` + `ucc: shown` with the same text, and
   the line on both screens at the announcement place.
4. Accuse: aim at the other heister, F5 -> `ucc: I accuse entity J (aimed at)` (proves the aim point [P+0x27b0]); the other screen shows
   `A suspects B`; a second F5 within 20 s -> `cooldown` + low beep.
5. Steam half: a Private Match between two PCs - read `netchan: Steam lobby present/gone` across match start: it settles section 2's GUESS.
FAIL cases first expected: `no FA announcement element yet` (osd not via `gamedata+0x15dc` online), `my own body is not in the player
table`, `nobody in the aim cone` while aiming (the aim point is not a world point: use the nearest fallback by setting ConeDeg=60).
