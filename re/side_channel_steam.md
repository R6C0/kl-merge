2026-10-29 BUILT (probe), branch wk-steamside-1029: `[Net] SideChannelSteam=1` (default 0, recommended off) = step 1 only, LOG ONLY. It extends klsteamprobe.c (the
SteamProbe module already existed): same one-shot GetISteamNetworking("SteamNetworking005" then "004") look, plus the peer table (global 0x168f960, [s+0x28]/[s+0x2c], 16-byte
entries, id u64 at +1, byte +9) logged at most once a minute and 20 lines a session, guarded reads (klh_rd), SEH around the Steam calls (FAULT line + probe off). Pure logic in
klhook/klsteamside.h, checked by klhook/klsteamside_test.c (in kl_tests.py). Sends nothing, reads no packet. Hook point: klsp_tick (game thread, round state 0x13..0x1f, peer
table non-empty), so the Steam call only happens long after the game initialised Steam.
CONFIRMED OFFLINE (steam_api.dll in the DD folder, capstone): SteamAPI_Init calls `mov edx,[eax+0x44]; push "SteamNetworking003"; push esi; push edi; call edx` with ecx = client
(two copies, 0x3b403663..0x3b40366d and 0x3b40472e..0x3b40473e). esi = [0x3b417e8c] = what SteamAPI_GetHSteamPipe returns, edi = [0x3b417e90] = SteamAPI_GetHSteamUser's
(both exports are `mov eax,[global]; ret`). So vtable +0x44 = index 17, thiscall, args (hUser, hPipe, version), as the review said. NOT readable offline: whether 005/004 are served (the log answers).
Bench, ONE PC (System Link / solo bench): set `SideChannelSteam=1` in the instance's KLHook.ini; expect NO `steamprobe:` line at all (no peer table on System Link: the probe is silent by
design) and no change in play; a `steamprobe:` FAULT line is a bug to report. In a Steam-lobby online match on one PC (same account, not a real P2P peer) expect at most:
`steamprobe: first look: round state 0x.. peer table .. count N`, `peer K id .. flag9 ..`, `exports SteamClient ..`, `SteamClient() .. hUser .. hPipe ..`, `ISteamClient vtable .. [+0x44] ..`,
two `GetISteamNetworking("SteamNetworking005"/"004") -> ptr vtable .. slots 0..2 ..` lines, `done (nothing was sent)`; then one `steamprobe: peers:` block per minute, 20 lines total, then
`peer-table log budget spent`.
Bench, TWO PCs (AnyDesk, two accounts, different networks, re/anydesk_setup.md): same hook dll + ini with SideChannelSteam=1 on both, host a Fragile Alliance online match, join, play into the
round, read KLHook.log on both: the 005/004 lines tell which version is served (non-null ptr with vtable slots 0..2 inside steamclient.dll = served; null = not), the `peers:` blocks list the
other player's Steam ID (id_hi reads 0110000x) and flag9 (1 once the game has sent to it). Send the lines back; then step 2 (framing + loopback shim) can be planned.

# KLSY* side channels over the internet (Steam P2P): design + review, 2026-10-28 [ce]

STATUS: offline design only, NOTHING BUILT. The review below CORRECTS the design (ISteamClient::GetISteamNetworking is vtable +0x44 = index 17, args user then pipe;
KLSYD goes joiner -> host; entry+9 = 'game has sent here', not 'session open'). The solo bench (System Link, one Steam account) CANNOT exercise any Steam
path: validation needs two PCs and two accounts (the owner's AnyDesk setup, re/anydesk_setup.md). First step there: a log-only probe for SteamNetworking005/004.
Overlaps re/hook_netchannel.md 3a (klnetchan.c): reuse that module rather than a second proxy.

---

# Design: [Net] SideChannelSteam (KLSY* over Steam P2P)

Status: design only, nothing built. READ = disassembled or read in a file. GUESS = inferred, must be verified before coding.
Ini: `[Net] SideChannelSteam=0` (default 0, label "(recommended off)" until benched; then flip to "(recommended on)").
Extra keys: `SideChannelChannel=` (default 7, option B only), `SideChannelShare=0` (carry the big KLSY2/KLSYP diagnostics list too; off by default).

## 1. Scope: what rides the Steam carrier

Carry by default: KLSYL (crew look), KLSYB (loot ledger), KLSYV (voice event), and the getup beacon KLSYD (on wk-getup2, not inspected here; assumed a small host-to-client datagram like the others).
Do NOT carry by default: KLSY2 (host actor list, up to ~10 KB) and KLSYP (probe). They are Compare/Apply/steering/diagnostic paths, are streamed at 4 Hz, and times 8 peers they would be about 300+ packets/s of ~1.1 KB. Gated by `SideChannelShare=1` and chunked (section 4). This keeps the default risk and bandwidth low: the four event channels total under ~200 bytes each and are already loss tolerant (repeats / 3x sends).
The port-27414 (KLCH1), 27413 (KLHO1) and NetChan 27416 broadcasts have the same LAN limit; they can reuse the same carrier later (same framing, new `kind`). Out of scope here.

## 2. Carrier choice

Chosen: Steam P2P through the game's own already-open sessions (no public IP, no lobby, Steam does NAT traversal / relay). Two variants, tried in this order at runtime:

**Option B (preferred, channel 7, invisible to Net-Z):**
1. At init (game thread, once Steam is up) call exported `SteamClient()` from steam_api.dll, plus `SteamAPI_GetHSteamUser()` and `SteamAPI_GetHSteamPipe()` (both exported, READ).
2. `ISteamClient::GetISteamNetworking(hUser, hPipe, "SteamNetworking005")`. The vtable index is GUESS (SDK order puts it at about index 16 in ISteamClient012-era headers: CreatePipe0, Release1, ConnectGlobal2, CreateLocal3, ReleaseUser4, GetUser5, GetGameServer6, SetLocalIP7, Friends8, Utils9, Matchmaking10, MMServers11, Generic12, UserStats13, GameServerStats14, Apps15, Networking16). VERIFY offline by disassembling the one place steam_api.dll's `SteamNetworking` export (the one kl2 imports at IAT 0xb107ec) fetches the interface: it calls exactly this method with "SteamNetworking003", so its vtable index and ABI are READable from the dll. Reuse that index; only the version string changes.
3. Non-null result with 005 (fall back to 004) means private channel works. Probe fails (null) means go to option A or off.
4. SDK-005 ABI (GUESS from SDK, verify against the dll's 003 thunk for the common part): `SendP2PPacket(CSteamID id [2 dwords], const void*, uint32 cb, EP2PSend type, int nChannel)`, `IsP2PPacketAvailable(uint32* pcb, int nChannel)`, `ReadP2PPacket(void* dest, uint32 cb, uint32* pcbRead, CSteamID* pId, int nChannel)`. vtable order: SendP2PPacket0, IsP2PPacketAvailable1, ReadP2PPacket2, Accept3, Close4, CloseChannel5, GetState6 (CloseChannel inserted in 004+, so offsets of later slots differ from the game's 003 table; we only need slots 0 to 2).
5. Because it is a separate channel, the game's loop at 0x48ca80 (which drains channel 0 and closes sessions for unknown IDs) never sees our packets. No proxy of the game's import is needed. This is the minimum-intrusion path: we never touch the game's IAT slot 0xb107ec.

**Option A (fallback, shared channel 0, needs an import proxy):** only if B's probe fails.
- Replace IAT slot 0xb107ec (`SteamNetworking`, same technique as `klmm.c` for 0xb107d8) with a function returning our proxy object. Proxy vtable = copy of the 003 vtable with slots +0 (Send), +4 (IsAvailable), +8 (Read) overridden; all others tail-jump to the original.
- Our receive: the proxy's +4 first drains the real queue by calling the original +4/+8 (the same ones the game would), diverts packets starting with our magic into the ring queue, stashes everything else in a second FIFO, and reports from that FIFO. +8 returns FIFO entries to the game byte-for-byte (including the original steam ID out-param).
- Risk specific to A: a stock peer or any Net-Z path receives our packets as channel-0 data (GUESS: dropped; unverified, and a drop may also close the session via 0x48cb33). Hence A sends only to peers that said hello (section 5). Because of this risk, A should ship as "SideChannelSteam=2" and stay opt-in even after B is benched.

## 3. Addresses / calls used (all READ unless marked)

- Peer table singleton: global 0x168f960; `[s+0x28]` = table ptr, `[s+0x2c]` = count; entry 16 bytes: Steam ID u64 at entry+1 (unaligned), session-open byte at +9. Send targets = entries with `[+9] != 0`. Read with a guarded copy (SEH or VirtualQuery check; the table can be reallocated by the net thread).
- Own Steam ID: ISteamUser vtable +8 (GUESS: GetSteamID; same ISteamUser the game calls at 0x8e50ea / 0x6d8705); alternatively the game's copy at `[obj+0x390]/[obj+0x394]`. Used only for self-filtering.
- Game Steam sites to stay away from (A only): send 0x883e33, read 0x48cae8, avail 0x48cab7, accept 0x6e26d7/0x6e2722, close 0x48cb33/0x50309e/0x738836.
- SendP2PPacket type: `k_EP2PSendUnreliable` (0). Never use reliable (type 2) for streaming data; the game uses it only for the session-open packet at 0x6fc2f2.
- MTU: unreliable P2P payload limit is ~1200 bytes (GUESS from SDK docs, verify by sending a larger one on the bench and seeing it rejected). Frame budget: 1100 bytes payload.

## 4. Framing

Every Steam packet = 12-byte outer header + the original LAN datagram (or one fragment of it):

| Off | Size | Field |
|---|---|---|
| 0 | 4 | `KLSX` (own magic, distinct from the five `KLSY*` magics; on channel 0 (A) it must also never look like a Net-Z first byte: UNVERIFIED, Net-Z header format not read) |
| 4 | 1 | ver = 1 |
| 5 | 1 | kind: 0 hello, 1 datagram, 2 fragment |
| 6 | 2 | msgid (u16, per sender, increments per fragmented datagram) |
| 8 | 1 | frag index |
| 9 | 1 | frag count (1 for kind 1) |
| 10 | 2 | payload length of this packet |

- Payload for kind 1 is the unmodified existing datagram (starts with `KLSYx\0\0\0`). The existing decoders (`klcl_rx`, `klls_rx`, `klbv_rx`, `kpl_rx`, `klsy` dispatch) are reused untouched; they already reject out-of-range fields and unknown magic.
- Fragments only for KLSY2 when `SideChannelShare=1`: receiver keeps up to 4 partial msgids per sender, drops a partial after 1 s or when a newer msgid arrives from that sender, never delivers an incomplete datagram (KLSY2 is replaced by the next one anyway). Cap n so a datagram needs at most 255 fragments (it is 10 fragments max).
- Receive integration: add `klsy_recv(buf, max, &src)` used by all receive loops. It first pops completed datagrams from a lock-protected ring (CRITICAL_SECTION; ring of 64 entries x 1.1 KB, drop oldest) then falls back to the LAN `recvfrom`. Synthetic source address for ring entries: `0x7E000000 | (steamId_lo24)` (never a real LAN address), so the existing "pin first valid source" logic in `klsync.c:1059`, `klcrewlook.c:260`, `kllootsync.c:130`, `klbotvoice.c:176` works unchanged and keeps LAN and Steam sources apart. Each pinner keeps its own pin, so a client that hears both LAN and Steam from the same host pins whichever came first and ignores the other; that is correct because they are the same data (T is newer-only, so the duplicate path is dropped as stale).
- Who receives when: the ring is filled by whoever calls the channel read. In B we do the read ourselves in `klsy_tick` (game thread, `IsP2PPacketAvailable(&sz, 7)` then `ReadP2PPacket` up to 64 per tick), so no extra thread and no lock is needed. In A the game's net thread may call the proxy, so the lock is required.

## 5. Peer selection and handshake

- Host sends only to peers that sent a hello. Never broadcast over Steam; this protects stock-DLL peers.
- Client sends `kind 0` hello to the session host's Steam ID every 2 s until it has received any host datagram, then every 10 s as keepalive. Payload: ver, a feature mask (bits: L, B, V, D, Share), wardrobe `wsig`.
- Host: on hello from an ID that is in the peer table (`[+9] != 0`), add to the sub-list with last-seen time; drop after 30 s of silence or when the ID leaves the table. Max 16.
- Who is the host's Steam ID for the client: GUESS/OPEN. Candidates: (1) a table entry whose peer sends Net-Z traffic first (not readable), (2) lobby owner via `ISteamMatchmaking::GetLobbyOwner` (the hook already wraps matchmaking in `klmm.c` and knows the lobby) which is only valid while the lobby exists, (3) just send hello to every open table entry (at most 8 small packets/2 s). Take (3) for v1: harmless on B (separate channel, a stock peer never reads it; Steam queues at most a few packets per channel), and unambiguous. Host accepts hello from anyone in the table.
- Spoofing/trust: accept datagrams only from IDs in the peer table. The "first valid sender wins" pin is by synthetic address derived from the verified Steam ID, so it is no longer an IP guess. Note the weakness that remains: any joiner could play host and send a forged KLSYL/B/V to others; the decoders range-check, so impact is cosmetic. Optional hardening: client ignores Steam datagrams from IDs other than the one whose hello got a reply (host replies with a `kind 0` ack).

## 6. Fallback and coexistence

- LAN broadcast stays exactly as is. With `SideChannelSteam=1` the Steam path is additive. Stale duplicates are dropped by existing T checks; stats counters `lan_rx / steam_rx / dup` are logged once per 30 s.
- Init failures (null interface, vtable guess wrong, no Steam) log one line and leave the carrier off. A runtime failure (SendP2PPacket returns false 20 times in a row) disables the carrier until the next round; it never touches game state.
- `SideChannelSteam=0` must be byte-identical to today's behavior (no IAT patch, no `SteamClient()` call).
- Sleep-safe: all Steam calls happen inside `klsy_tick`'s existing gate (role 2/3, mode 4, state 0x13..0x1f), plus hello/probe at join. No calls from the render path.
- SessionSafe: B patches no code or IAT; A patches only the import slot, same as `klmm.c`.

## 7. Benching with the two-instance solo bench

What it proves (both instances on one PC):
- Framing, fragmentation/reassembly, ring queue, dedupe by T, off-by-one in chunk sizes, ini plumbing, default-off byte identity. Also an off-game unit test: `klhook/klsx_test.c` that feeds frames through encode/decode/reassemble with loss, reorder and duplicate (add to `tools/kl_tests.py`).
- That the vtable index/ABI of 005 is right (probe returns non-null, Send returns true, own packets are readable).
- With a forced test mode (`SideChannelSteam=1`, `[Net] SideChannelForceSteam=1` which suppresses the LAN path in the receive loop for that bench only): that all four channels still work end to end when only the Steam carrier delivers them, including voice and getup beacon.
- Option A only: that Net-Z traffic still flows with the proxy installed (round completes, 0 faults).

What it does NOT prove:
- Anything about NAT traversal, relay, latency, loss or MTU on the real internet. Two instances on one PC share a LAN/loopback.
- Whether two instances even get distinct Steam IDs: Steam allows one client logon per account, so two real P2P peers on one PC may be impossible. If the bench uses one account, the two instances have the same Steam ID, P2P-to-self is not reliable, and the peer table path may be a stub. In that case the bench can only exercise the code via a loopback shim (`ISteamNetworking` fake that routes Send to the other instance's ring through a local UDP socket), which proves logic but not Steam. Decide this first by checking how the bench instances connect today (needs a look at `kl_solo_test.py`; not read in this task).
- Whether stock peers tolerate channel-0 packets (option A).
Required real test before flipping the recommendation: host on one PC, joiner on another machine/account on a different network (phone hotspot), 9-player online FA round, compare against a LAN round: crew looks, loot ledger line, voice events, getup beacon all appear; `steam_rx > 0`, `lan_rx == 0`; Net-Z unaffected (no new disconnects, ping unchanged).

## 8. Open risks (ranked)

1. **Steam interface version availability (B):** `SteamNetworking005` may not be served to this app, or the ISteamClient index guess is wrong. Mitigation: derive the index from the dll thunk; probe and fall back; first bench task.
2. **Wrong-peer effects on channel 0 (A):** stock peers' Net-Z may close the session or log errors on unknown packets. Mitigation: hello-gated sending, ship A only as `=2`.
3. **Shared Steam ID on bench / single machine:** cannot prove real P2P. Needs a second PC/account (owner or friend); schedule it.
4. **Packet size / rate:** unreliable limit ~1200 bytes (GUESS); KLSY2 at 8 peers is too heavy, hence off by default.
5. **Host identity and trust:** hello to all open table entries; forged packets cosmetic only; pin by Steam ID.
6. **Threading:** P2P reads in the proxy (A) from the net thread; ring needs lock; B stays single-threaded.
7. **Session lifetime:** Steam closes an idle P2P session; the game's session is the same one, so our keepalive hello keeps it alive but also could delay the game's own close logic by a few seconds (GUESS, low).
8. **Unknown KLSYD details:** the getup beacon is only on wk-getup2; confirm its datagram size and that it uses the same `klsy_open` socket before wiring it through `klsy_recv`/a `klsy_send` helper (replace the five `sendto` sites at `klsync.c:1030`, `klsync.c:880`, `klcrewlook.c:232`, `kllootsync.c:89`, `klbotvoice.c:160` with one `klsy_send_all(buf,len)` that does LAN broadcast plus Steam unicast per hello'd peer).

## 9. Implementation steps (when approved)

1. Offline: disassemble the steam_api.dll `SteamNetworking` export to get the ISteamClient index and calling convention; confirm 004/005 slot order from the dll's interface strings.
2. New `klhook/klsteamch.c` + `klsx_logic.h` (pure framing, unit-testable), `klsy_send_all` / `klsy_recv` shims in `klsync.c`, ini in `[Net]`, options-UI entry labelled "(recommended off)".
3. `klhook/klsx_test.c` into `kl_tests.py`; then solo bench with the loopback shim; then two-machine test; then update `re/netcode.md` and the open_work_log.

---

# Adversarial review (corrections)

**Verdict: the carrier idea is sound, but the design has two factual errors in its core address and ABI claims, one wrong direction assumption (KLSYD), and a bench plan that cannot reach the Steam code at all. Treat Option B as feasible but unproven, and not ready to code.**

## Wrong (refuted against the binaries and notes)

1. **The `SteamNetworking` export does not make the `GetISteamNetworking` call.**
   - In `steam_api.dll`, `SteamNetworking` at RVA 0x3740 is `mov eax,[0x3b417f40]; ret`. It only returns a cached pointer. `SteamClient` (0x36c0), `SteamUser` and the others are the same kind of getter.
   - The actual call is inside `SteamAPI_Init` (file offsets 0x35a0..0x3680). The step 1 reading plan ("read the index in the export") is wrong.
2. **The ISteamClient vtable index is 17, not about 16.**
   - In `SteamAPI_Init`, the call `[vt+0x44](hUser, hPipe, "SteamNetworking003")` stores its result in the global that the export returns. `+0x44` is index 17.
   - The args are user first, then pipe: `push str; push esi(pipe=[7e8c]); push edi(user=[7e90])`.
   - The SDK-order guess in the design is off by one. The user handle is `SteamAPI_GetHSteamUser`'s global and the pipe handle is `SteamAPI_GetHSteamPipe`'s global.
   - The ISteamClient version bound in this dll is `SteamClient009`.
3. **KLSYD does not go host to client.**
   - In `wk-getup2`, `klgetupbeacon.c:5` and `:45-46` show the downed machine sending a 32-byte datagram to the host, once a second while down and 3x on getting up. It uses `klsy.sock`, port 27415, broadcast.
   - The design assumed host to client. So `klsy_send_all` with host-side "hello'd peers" does not cover it.
   - Clients need to unicast to the host's Steam ID. That is the design's own OPEN item, so it is a hard requirement rather than an optional extra.
   - The `sendto` site list also omits `klgetupbeacon.c:46`. The host-side drain is `klgb_host_rx`, called from `klsy_tick` (`klsync.c:1040`).
4. **"Session-open byte at entry+9" is mislabelled.**
   - `0x883e3d` sets `[entry+9]=1` only after the game's own successful send (`0x883e33` returns true). It means "the game has sent to this entry at least once", not "session open".
   - The lookup at `0x883df8` compares a 32-bit key against `[entry+1]`, and the send then passes `[+1]` and `[+5]` as the Steam ID.
   - Filtering recipients by `[+9]!=0` will skip peers the game has not yet sent to. Use presence in the table plus the own-ID filter instead, and treat `+9` as a soft hint.
5. **The bench cannot test any Steam path.**
   - `re/netsmooth_solo.md` says the two-instance bench runs on "route U" (System Link: UDP LAN, station identity is the URL, no Steam ID). It is a different socket driver from `SteamSocketDriver`, so `0x168f960` and `0x883dd0` are probably never used there.
   - `re/fa_private_match_blueprint.md` §7.2 says a second kl2.exe on the same account cannot be a P2P peer.
   - So the "vtable index/ABI right, probe non-null, packet readable" claim cannot be proven on the bench. The loopback shim tests only your own framing code.
   - Everything Steam-specific needs two PCs and two accounts.

## Unverified

- **`SteamNetworking005` availability.**
  - The dll only contains "SteamNetworking003". Whether the current steamclient serves 004, 005 or 006 to this app id cannot be read from the allowed files.
  - The channel-bearing signatures (`SendP2PPacket(id, p, cb, type, nChannel)`, `IsP2PPacketAvailable(&cb, nChannel)`, `ReadP2PPacket(..., nChannel)`) and the slot order Send 0, Avail 1, Read 2 for 005 come from SDK memory. The game's 003 usage (verified below) is the only anchor.
  - A wrong-version ABI would be a silent crash. Request exactly one version and treat a null result as "off".
- **Calling convention.** The 003 calls verified at `0x883e0e..0x883e33` and `0x48caa9..0x48cae8` are thiscall (`ecx=this`) with args pushed right to left.
  - Send takes 5 dwords: id_lo, id_hi, data, cb, type 0. Avail takes one arg (`&cb`). Read takes four.
  - The design never states thiscall.
- **Option A:** whether Net-Z tolerates foreign channel-0 bytes is unread. Closing a session on an unknown ID (`0x48cb33`, `[vt+0x10]`) is verified for unknown IDs only.
- **IAT slot 0xb107ec** has not been through `ceg_ranges.py`. `re/netsmooth_solo.md:66` warns that CEG checks may cover other slots. This is a risk for A only.
- **The 1200-byte unreliable limit** is an SDK-doc figure, not tested here.
- **Whether stock peers' unread channel 7 queues** grow without bound is unknown. Low risk.
- **Idle-session behaviour** with the keepalive hello is unknown.

## Confirmed correct

- `0x168f960` singleton, `+0x28` table, `+0x2c` count, 16-byte entries, ID at `+1`, send at `0x883dd0` (call at `0x883e33`).
- Receive at `0x48ca80`: avail call at `0x48cab7`, read at `0x48cae8`, close at `0x48cb33`.
- Unreliable (type 0) send.
- The drain reads without a channel argument, so a channel-7 packet is invisible to it.
- `klsy_tick` is game-thread only (`klsync.c:1011`) and gated to state `0x13..0x1f` (`:1015`).
- `SteamAPI_GetHSteamUser`, `SteamAPI_GetHSteamPipe` and `SteamClient` are exported.
- `ISteamUser` +8 is `GetSteamID` (`re/netcode.md:523`).

## Other problems

- **Hello at join falls outside the gate.** `klsy_tick` returns before state `0x13`, so the "hello and probe at join" needs a separate hook point.
- **Overlap with `re/hook_netchannel.md` §3a.** That note already proposes a Steam P2P import proxy (sending via the peer table, filtering `KLNC1` out of Quazal's reads) and a shared channel, `klnetchan.c`. Option A duplicates it. Building a second framing layer next to `klnetchan` and `klnc_test` will split maintenance, so reuse that module.
- **Host identity** is real, not minor.
  - KLSYD and the hello both need the host's ID.
  - `GetLobbyOwner` is unreliable because `hook_netchannel.md` §2 says peers likely leave the lobby at match start.
  - Candidate sources are the per-session role (`[sm+0x54]`) or the first Net-Z sender. An unauthenticated "first hello wins" lets any joiner pose as host (cosmetic only for KLSYL/B/V, but KLSYD flows the other way, so check it).
- **Threading.** The design calls the game-thread-only Steam reads "no lock needed". The game's net thread calls the 003 interface concurrently with ours. Steam's client IPC is generally thread-safe per pipe, but this is unverified.

## Corrected recommendation

1. **Offline, now:** read `steam_api.dll` `SteamAPI_Init` to confirm ISteamClient index 17 and the thiscall ABI (done above, re-check by disassembly). Fix the design text accordingly. The 005 ABI itself is still not checkable offline.
2. **Spike on a real two-PC session first.** Before writing `klsx_logic.h`, add a bare probe: call `SteamClient()->GetISteamNetworking` (vtable +0x44, user/pipe from the exports) for "SteamNetworking005", then 004, and log the result. Do not send anything yet. This answers risk #1 for free.
3. **Gate the probe on the peer table existing** (non-null `0x168f960` and a non-empty table), so the bench's System Link route skips the Steam path cleanly.
4. **Ship order:** B only, off by default, hello-gated, unicast to table entries.
   - Make it bidirectional: host to client for L, B, V; client to host for D.
   - Defer A until B is benched. If wanted, fold it into the `klnetchan.c` proxy rather than a second one.
5. **Testing:** a loopback shim for framing and fragment logic only. Real validation is host plus a joiner on another account and network, as the design says, with `steam_rx > 0` and `lan_rx == 0` for L, B, V and D.

Files and addresses read: `steam_api.dll` and `kl2.exe` in the DD folder (disassembly only), `C:/kl-merge/wt/wk-merge/re/hook_netchannel.md`, `netcode.md`, `fa_private_match_blueprint.md`, `C:/kl-merge/kl-merge/re/netsmooth_solo.md`, `C:/kl-merge/wt/wk-merge/klhook/klsync.c`, `C:/kl-merge/wt/wk-getup2/klhook/klgetupbeacon.c`.

---

# How to run the SteamProbe on two PCs (klsteamprobe.c, added 2026-10-28)

`[Net] SteamProbe=1` in KLHook.ini (default 0, recommended off) logs and sends nothing. Steps: (1) both PCs get the same hook build (dinput8.dll + ini) with SteamProbe=1,
each signed into its OWN Steam account (a second kl2.exe on one account cannot be a P2P peer). (2) Host a Fragile Alliance match online (not System Link: the peer
table at 0x168f960 does not exist there, the probe then stays silent by design); the other PC joins over the internet (a different network, e.g. a phone hotspot, to
exercise NAT). (3) Play until the round runs (session state 0x13..0x1f) and the peer table has an entry. (4) Read `KLHook.log` on both PCs for lines starting
`steamprobe:`. Expected: both `GetISteamNetworking("SteamNetworking005")` and `("SteamNetworking004")` lines; a non-null pointer with a readable vtable means that
version is served (then slots 0..2 should be code addresses inside steamclient.dll), a null pointer means not served. Send those lines back; the probe fires once per
game start (restart the game to repeat it). A `FAULT` line means the vtable +0x44 ABI guess is wrong; the probe disables itself and the game goes on.
