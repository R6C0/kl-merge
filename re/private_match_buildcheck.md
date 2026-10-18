# Build-mismatch detection between lobby members (design only)

kl-merge-e5 research worker, 2026-10-18. Static reading of `kl2.exe` (build 0490) with `tools/kl_exe.py` + capstone; the game was not
run, the Dog Days folder was not written, `klhook/*` was not edited. Tags: **FACT** = bytes read at the address in this session or
copied from `re/private_match.md` / `re/netcode.md` (marked "carried"); **GUESS** = inference, to be tested live.

## 1. Problem
The FA start gate (0x6c4cf5..0x6c4d8c) only ANDs a 16-bit DLC mask per client (FACT, carried: slots F01-F04/F06/F07 are always set), and the
loader opens the client's own `Scenes/Locations/Fxx/Fxx_Main.zip`. A peer with a different or no `KLExpansion\Maps` build therefore
starts silently and then disagrees on 16-bit scene refs. Nothing compares content. KLHook already has half the transport
(`klhook/klmm.c`, `BuildKey=1`): the host writes lobby key `klx_build`, the search adds a string filter. NOT RUN. Missing: a CHECK on the
joiner/host side, a per-slot fingerprint, and a reaction.

## 2. Steam calls kl2.exe makes (FACT)
`SteamMatchmaking()` is import slot **0xb107d8**; 25 references re-enumerated here (call [0xb107d8] x17, mov reg,[0xb107d8] x8):
0x406595 0x424844 0x4cf798 0x4d2b08 0x4d2b56 0x4d2b97 0x4d2bf7 0x4e4bb7 0x559e46 0x559e5b 0x572014 0x6299b0 0x65f373 0x6f2d75 0x700943
0x705022 0x745cab 0x745d63 0x749f00 0x7ea683 0x81a5a3 0x81a85c 0x86944c 0x86b134 0x8bd535. Vtable offsets (SteamMatchMaking008, proven
against steamclient.dll in klmm.c) read at those sites:

| call | vtable | address (FACT) |
|---|---|---|
| RequestLobbyList / String(+0x14) / Numerical(+0x18) / NearValue(+0x1c) filter | 0x10 .. | 0x424851, 0x559e6a.. (filters), 0x86b148 |
| CreateLobby | 0x30 | 0x705035 (task 0x705000) |
| JoinLobby | 0x34 | 0x57202b (task slot 8 = 0x572010) |
| LeaveLobby | 0x38 | 0x700951 (0x700910, also the ExitLobby chat reaction at 0x8bd625) |
| GetNumLobbyMembers / GetLobbyMemberByIndex | 0x40 / 0x44 | 0x65f381; 0x4d2b16 0x4d2b64 0x4d2ba5 0x4d2c05 (members walk 0x4d2a40), 0x81a5af |
| GetLobbyData / SetLobbyData | 0x48 / 0x4c | 0x86b162.. (row reader 0x86b0f0); 0x869463 (writer 0x869430) |
| SendLobbyChatMsg / GetLobbyChatEntry | 0x64 / 0x68 | sends: 0x745d6e (`ExitLobby`, 10 bytes, string 0xb5acbc), 0x8bd5e3 (`SyncedWithLobby`, 0x10 bytes, string 0xbd58e0); reads: 0x745cd8, 0x8bd582 |
| RequestLobbyData | 0x6c | 0x6f2d81 |
| GetLobbyOwner | 0x88 | 0x6299cb (right after LobbyEnter), 0x4e4bc5, 0x7ea691 |
| SetLobbyJoinable | 0x84 | 0x406687 (carried) |
| **SetLobbyMemberData (0x60) / GetLobbyMemberData (0x5c)** | | **no site found**; the earlier full enumeration (private_match.md 2-5) lists none and this partial re-scan found none. Not an exhaustive proof, but the member-data namespace looks free for KLHook (GUESS) |

Chat protocol (FACT, read): host 0x406560 (`ZAsyncStartSessionAndSyncLobby`) sends `SyncLobbyWithNetZ`; receiver **0x8bd520** (strcmp at
0x8bd587..0x8bd5b7) runs 0x4d2a40 and answers `SyncedWithLobby`; **0x745c80** (host side) strcmps against `SyncedWithLobby` (0x745cdd),
marks that Steam id in a 9-byte-per-entry table at `[ebp+0x1c]` (count `[ebp+0x18]`), and once every entry is marked sends `ExitLobby`
(0x745d63..0x745d7f); 0x8bd520 on `ExitLobby` calls 0x700910 when byte `[this+0x36e]==0`. Both handlers ignore any other chat text (the
only branches are those compares), so an extra chat message is harmless to stock peers (GUESS: no other handler reads chat; the
`LobbyChatMsg_t` callback is registered once, by 0x879d40, carried).
The game registers callbacks for GameLobbyJoinRequested_t, LobbyInvite_t and LobbyChatMsg_t only (carried). It has no handler for
LobbyDataUpdate_t (GUESS from the RTTI list), so a lobby-data or member-data change is never noticed by the game itself.

## 3. Choosing the carrier
| candidate | verdict |
|---|---|
| Lobby data on the host (`klx_build`, `klx_slots`) | **Use.** Already written by klmm.c at the first `SetLobbyData("name")`. Readable with `GetLobbyData` (+0x48) once the joiner is in (GUESS: present at LobbyEnter; the game itself reads `Scenario` only after a separate RequestLobbyData, 0x6f2d81, so do the same if the first read is empty). |
| **Lobby MEMBER data (`klx_fp`, +0x60 set / +0x5c get)** | **Use for the reverse direction** (host sees each member's build). Persists, no callback needed: poll from the KLHook tick. Needs a new proxy override (slots 24/25 are tail jumps today). |
| Lobby chat message (`KLX1 <fp>`) | Fallback only. Works (+0x64 exists), stock handlers ignore it, but it is not stored: a member joining after the message misses it, and KLHook would have to register its own LobbyChatMsg_t callback. |
| Name tag (persona name in `name`) | Reject: visible, length-limited, and `name` is the host's persona. |
| P2P message | Reject: peers are only added after SyncLobbyWithNetZ (0x4d2a40), i.e. too late (the check must come BEFORE the match loads), and a packet from an unknown id is dropped (0x48ca80, carried). |

## 4. What to hash
Goal: everything that changes scene refs or object layout on the client side. Per slot and global:
- per slot `Fxx`: `Maps\<dir>\Fxx_Main.zip` = the existing `klx_fingerprint` (size + central-directory hash = every member's CRC-32 and
  size). 8 hex digits. Cheap (one seek to the zip tail), so fine at every lobby create.
- global: **Patch01.zip** (CLAUDE.md: mounted first, overrides members of EVERY archive, so a different Patch01 changes any map; klmm.c's
  current id does NOT include it) and the redirect table that says which expansion map sits in which slot (klslot.c; its output file was
  not read, GUESS).
- NOT in the id: write times, `.WHD/.WAV` (audio only; GUESS that a mismatch there cannot desync objects), KLHook version (not
  net-visible), `KLJoin.ini` (crew/bot behaviour is host-side AI; GUESS that clients do not simulate it. If they do, put it in a separate
  `klx_join` key that only warns).
- Wire format: `klx_build` = 8 hex over all of the above (kept, so the existing filter keeps working); `klx_slots` =
  `F01=1a2b3c4d,F02=...` for diagnosis ("slot F03 differs"). Far under Steam's per-value limit (GUESS: 8192 bytes; key <= 255).
  Filter recommendation: a mismatched friend's lobby silently vanishes from the browser when `klx_build` is a search filter, which is
  hard to debug. Better: filter on a constant `klx=1` ("is an expansion host", new key) and keep `klx_build` as data only, so the joiner
  can say "your build differs" instead of "no lobby".

## 5. Where to hook (all in the existing proxy, no byte of kl2.exe changes)
Import slot 0xb107d8 is outside CEG-hashed pages (carried, private_match.md 4). New overrides next to klmm.c's three:
1. **Host publish**: +0x4c SetLobbyData after key `name` (exists). Add `klx_slots` and `klx`. Also `SetLobbyMemberData(id,"klx_fp",<build>)` for
   the host itself (+0x60, new override or a direct call on the real table).
2. **Joiner record**: +0x34 JoinLobby (0x57202b) stores the lobby id the game is about to join (covers `+connect_lobby` and Join game, which
   both end in the task at 0x572010; that chain is partly GUESS, carried).
3. **Joiner check**: +0x88 GetLobbyOwner called from the LobbyEnter completion 0x629980 (call at 0x6299cb). That handler checks no data
   (carried). In the override: if the id equals the recorded one and is unchecked, `GetLobbyData(id,"klx_build")`; if empty,
   `RequestLobbyData` (+0x6c) and retry from the tick; compare with the local build id; `SetLobbyMemberData(id,"klx_fp",mine)` either way so
   the host can see it. Other callers of +0x88 (0x4e4bc5, 0x7ea691) pass through.
4. **Host watch**: from the KLHook tick (about 2 Hz, no new Steam callback): `GetNumLobbyMembers` (+0x40), `GetLobbyMemberByIndex` (+0x44),
   `GetLobbyMemberData(id, member, "klx_fp")` (+0x5c). Absent or different = mismatch. Absent means "stock client or no hook" and counts as a
   mismatch WHEN the selected slot is an expansion slot (a stock client loads stock Subway, silently, per private_match.md).
5. Selected slot: menu position -> slot map is 0x746570 (table 0,1,2,3,5,6,4,7,8, carried), called from the gate at 0x6c4d1f with
   `ecx=[0x168f750]` and a string from a menu widget (0x6c4d02..0x6c4d16, key 0xb6d6e4, FACT of the code, not of the value). Simplest first
   version: treat any mismatch as blocking.

## 6. Reaction on mismatch
In order of preference:
- **Log** always: `mm: build mismatch member#N slot Fxx host=... theirs=...` (no Steam id, matching klmm.c's rule).
- **Hold the countdown (refuse start)** with the game's own gate. FACT (read this session): the gate loops clients 0..11 (0x6c4d44..0x6c4d8c,
  `cmp edi,0xc`), asks `0x7ca830(client, slot)` per client, and on a clear bit zeroes `[esp+0x17]`, after which 0x6c4dd3 resets the countdown
  `[sm+0x194]`. The per-client mask is set by `0x845640` (ecx = client+0xb8; stores `mask ^ 0xdead`; returns 0 and changes nothing when the
  value is unchanged, so calling it every tick is idempotent). Host recipe: true mask = `0x634b90` (ecx=`[0x168f750]`), clear the bit of the
  grafted slot, call `0x845640` with ecx=`[sm+0x98]+0xb8` (the host's own client; per carried notes). The DLC callback 0x845700 re-pushes the
  true mask on its events, so re-apply from the tick. GUESS: the host's own client is one of the entries 0x8fdf90 returns; GUESS: the UI shows
  a generic "missing content" (`Online/MissingContentPackClient`, 0x6c4e07, is meant for clients, so the text may mislead on the host). Cost:
  the map stays selectable.
- **Joiner side**, if the joiner runs KLHook: clear its own mask bit the same way and show a notice. The host then sees it via the replicated
  dataset (GUESS: `m_iAvailableLevels` replicates after the lobby forms, netcode.md; not read). Needs only lobby data, so it also works
  against a host that has no `klx_fp` logic.
- **Notice**: existing `klhud_popup.c` machinery (API not read here) or the log line only; a stock peer cannot be shown anything.
- **Leave**: `LeaveLobby` (+0x38) from the joiner is possible but what the game does afterwards is unknown (0x629980 already stored state 1,
  carried). Not for a first version.
- The host cannot remove another member (no kick call among the 36 slots): only hold the start until they leave or fix.

## 7. Risks
1. All Steam member-data and chat behaviour is untested; the machine has one Steam account, so the first live test needs a second account or a
   friend (carried).
2. A hookless peer has no `klx_fp`; treating absence as mismatch also blocks hookless friends who only play stock slots. Block only when the
   selected slot is an expansion slot (5.5) once the slot is known.
3. Lobby data may be missing at LobbyEnter; the check must tolerate "empty" (retry, then warn, not block).
4. Holding the countdown through the host's mask hides the reason from the host UI; the HUD line has to carry it.
5. 0x845700 re-pushes can undo the hold for one tick; the countdown resets every frame (0x6c4dd3), so a one-tick gap does not matter.
6. CEG: every hook is in a non-hashed place (import slot, hook DLL). Calling 0x845640 / 0x634b90 / 0x746570 from the hook is a plain call
   (no byte patched).
7. The hash is only as good as the central directory: members rebuilt in another order differ (false alarm, safe side).

## 8. Open questions
- Does Steam deliver lobby and member data to the joiner at LobbyEnter or only after LobbyDataUpdate_t? (decides if 5.3 can be synchronous)
- Is the host's own client in the gate loop, and does a mask hold survive replication? (Test: clear the bit on the host, watch the countdown.)
- Does a client's replicated `m_iAvailableLevels` change after the lobby forms, so a joiner-side clear reaches the host?
- How to read the selected slot from a hook (the widget behind key 0xb6d6e4).
- ISteamFriends offset for GetFriendPersonaName is unmapped (needed to name the mismatched member).
- Does klslot.c's redirect table list the expansion slots (for the per-slot hash)? File not read.

## 9. Implementation sketch (for kl-merge-3f; nothing written)
`[Net] BuildCheck=0/1` (default 0, installs nothing): in klmm.c (a) add `klx_slots` and `klx=1`; (b) overrides for +0x34, +0x88 and
+0x60/+0x5c; (c) a tick `klmm_tick()` (host: poll members; both: apply or clear the mask bit; one log line per state change); (d) Patch01.zip
as a global hash input. Test order: single machine, log only (create a lobby, read back the keys); then two accounts.

## 10. Review corrections (2026-10-18, adversarial re-check of 72a595a8; every kl2.exe address above held)
- **Slot test is wrong as written (sections 6, 7).** An expansion map takes over a STOCK slot: klslot.c redirects Fxx to `KLExpansion\Maps\DMxx` via `[Redirect]` / `[Redirect.N]` in KLHook.ini, and `[Redirect.N]` applies only while menu page N is latched (`kls_page_now()`, set by `kls_menu_watch`). Clearing the F01 bit therefore also blocks stock Subway. Apply the mask hold only while a redirect rule is active for the current page, and lift it otherwise. Open questions 3 and 5 are answered by that: the page latch says which slot is expansion, and the widget behind `MP_SelectedLevel` need not be decoded.
- **Hash the redirect target.** The per-slot fingerprint must be of the file the redirect resolves to, and the redirect table itself belongs in the hash input (no longer a GUESS).
- **Write times are NOT left out:** the central directory hashed by `klx_fingerprint` holds each member's DOS timestamp, so a rebuild with identical content gives a (safe-side) false mismatch.
- **Slot numbers:** GetLobbyMemberData is slot 23 (+0x5c), SetLobbyMemberData slot 24 (+0x60); slot 25 is SendLobbyChatMsg.
- **Table fixes:** 0x86b148 is a `mov` before GetLobbyData (call at 0x86b166), not a filter site. Missing row: 0x749f00 (+0x2c GetLobbyByIndex); the count of 25 stands.
- **JoinLobby recording is unneeded:** the `GetLobbyOwner` override receives the lobby id as its argument, and return address 0x6299da identifies the join-completion caller.
- **Thread:** the mask calls (0x634b90, 0x845640) and the Steam polls run only when the tick's `game_thread` flag is true (klhook.c line 669). A ship build must not run game code from its own thread (klslot.c).
