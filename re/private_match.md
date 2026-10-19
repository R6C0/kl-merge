# Private matches in Dog Days' Steam lobbies: where to change it (research only)

Worker `net-research`, 2026-10-17. Static reading of `kl2.exe` (build 0490, TimeDateStamp 0x4c80f728), disassembled with
capstone through `tools/kl_exe.py` (imports resolved from the PE import table). **Nothing here was run or patched.**
It refines `re/netcode.md` 3.2 / 3.3 and `re/fa_private_match_blueprint.md` 2.3; where it disagrees, this file was
re-read from the bytes. Tags: **PROVEN** = disassembly read at the address given; **GUESS** = inference.
Adversarially re-checked 2026-10-17 (every address re-disassembled; corrections are marked **CORRECTED**).

## 0. Short answer

| question | answer |
|---|---|
| CreateLobby | `ISteamMatchmaking` vtable +0x30, one call, in `ZAsyncTaskCreateLobbySteam` slot 8 = **0x705000** (call at 0x705035). `ELobbyType` = arg 1, **max members = 16** (`mov edi,0x10` at 0x70500b) unless property flag 8 gives byte `props+5` (0x607290). |
| Type chosen | in `CreateSession` 0x8e4fe0: ranked -> 3 (0x8e5158 `push 3`), else private bit -> 1 (FriendsOnly), else 2 (Public) (0x8e5169..0x8e5173). |
| Search filters | **Only numeric ones** (server-side list only; there is one client-side row filter, see 2): `AddRequestLobbyListNumericalFilter` (+0x18) on `GameType`, `Scenario`, `CoopDifficulty` or `FAGameMode`, `Ranked`, plus `AddRequestLobbyListNearValueFilter` (+0x1c) on `Rank`, all in **0x559dc0**. **No string filter is used anywhere in the exe** (+0x14 is never called). |
| Lobby data keys written | `name`, `Scenario`, `CoopDifficulty` / `FAGameMode`, `RoundTime`, `NumRounds`, `Ranked`, `Rank`, `GameType` (0x869430). **No build / version / map-name key.** |
| Join by friend / invite | `GameLobbyJoinRequested_t` handler **0x547950** (registered at ZOnlineServiceSteam+0x1e0 via helper 0x838c70, callback id 0x14d); `LobbyInvite_t` handler 0x8bf680 is an empty `ret 4`; command line `+connect_lobby <id64>` read at **0x506d7a..0x506d9c**, only while the current menu is `MainMenu`. Both store the lobby id at service `+0x4b5/+0x4b9`; the id is consumed by 0x7fc2b0, a lobby-data request (**CORRECTED** from "join task built at 0x7fc2c0"; the JoinLobby task is made at 0x6d86ec, see 3). |
| Best patch route | **Not code.** The CEG integrity ranges (`klhook/klranges.h`) hash the type-choice bytes and the filter code, but **not the import slot 0xb107d8** (SteamMatchmaking) and **not the pages 0x705000-0x705fff and 0x869000-0x86afff**. House style (klsteam.c) = an import-slot proxy. |

## 1. Lobby creation (PROVEN)

`ZOnlineServiceSteam` `CreateSession` is **0x8e4fe0** (vtable slot 40; the ZOnlineServiceWintel thunk is 0x790060).

```
8e50c4  test al,0x10 ; je ...                 ; al = props flags (960d70 = mov eax,[ecx])
8e50ca  call 0x556f80                          ; movsx eax,word [ecx+8] ; shr 4 ; and 1   -> PRIVATE bit
8e50cf  mov [esp+0x38],al
8e5112  call 0x5e1080                          ; word [ecx+8] bit 5                       -> RANKED bit
8e5123  mov [ebp+0x36f],al                     ; service ranked byte
8e5143  add ebp,0x35e                          ; &lobby id out (written by completion 0x822900)
8e514b  test al,al ; je 8e5160
8e5158  push 3                                 ; ranked  -> k_ELobbyTypeInvisible
8e5160..8e5173  xor edx,edx ; cmp byte [esp+0x40],dl ; sete dl ; inc edx ; push edx
                                               ; private -> 1 (FriendsOnly), else 2 (Public)
8e5174  call eax                               ; task method +0x20(type): starts ZAsyncTaskCreateLobbySteam
```
The task body, 0x705000 (arg1 = ELobbyType, arg2 = the 32-byte property block):
```
705009  mov ecx,esi ; 70500b mov edi,0x10      ; default max members 16
705010  call 0x960d70 ; 705015 test al,8 ; je 705022
70501b  call 0x607290                           ; movsx eax,byte [ecx+5] -> max players from the properties
705022  call [0xb107d8]                         ; SteamMatchmaking()
705028  mov ecx,[esp+0x10]                      ; arg1 = lobby type
70502e  mov edx,[edx+0x30]                      ; vtable +0x30 = CreateLobby(type, maxMembers)
705031  push edi ; 705032 push ecx ; 705035 call edx
```
Steam values: 0 Private (invite only), 1 FriendsOnly, 2 Public, 3 Invisible. Vtable offsets are the
`SteamMatchMaking008` layout (see the evidence in 3): they fit every call site read (0x10 RequestLobbyList with no
arguments, 0x2c GetLobbyByIndex with a hidden return pointer, 0x30 two arguments, 0x34 JoinLobby, 0x38 LeaveLobby,
0x40 / 0x44 member count / by index, 0x48 GetLobbyData, 0x4c SetLobbyData with 4 dwords, 0x64 / 0x68 chat, 0x6c
RequestLobbyData, 0x78 SetLobbyMemberLimit, 0x84 SetLobbyJoinable, 0x88 GetLobbyOwner).
The game never calls SetLobbyType (+0x80), so the type is fixed at creation.

Lobby data, function **0x869430** (called from the create completion 0x82293b and from 0x4ec7e2 for later updates):
`SteamFriends()->GetPersonaName` then, through `mov ebx,[eax]; add ebx,0x4c; call [ebx]` (SetLobbyData(id, key, value)):

| key (string address) | condition |
|---|---|
| `name` 0xb2e088 | always, persona name (0x869473 push) |
| `Scenario` 0xb83b14 | flag bit 0; value from 0x94da50 when 0x82fd20 == 4, else from 0x8ee700 (**CORRECTED**: the draft had them reversed; the 0x8694a1 `jne` goes to the 0x8ee700 path) |
| `CoopDifficulty` 0xb8633c / `FAGameMode` 0xb26c28 | flag 0x200 with 0x87c980 true / flag 0x100 and game type 4 |
| `RoundTime` 0xb24c60, `NumRounds` 0xb1cab8 | flag bit 1 / bit 2 |
| `Ranked` 0xb4fde0, `Rank` 0xb3e774 | flag 0x20; Rank only when ranked |
| `GameType` 0xb2c7d8 | always (0x869725 is the last call; epilogue 0x869727..0x869739) |
and `SetLobbyMemberLimit` (+0x78) from 0x869654 when flag 8 is set. Values are decimal text (`_itoa`).

## 2. Search (PROVEN)

- Start: `ZAsyncTaskSessionSearchSteam` (vtable 0xbd58f4, built by ctor 0x43c650) has 13 slots and **0x424840 is slot 12
  (vtable +0x30), not slot 8 (CORRECTED)**; its slot 8 is 0x8d00b0. 0x424840 takes one byte argument (stored at task+0x48)
  and does `SteamMatchmaking()->vtbl+0x10` (RequestLobbyList, no arguments) at 0x424851; result goes to a CCallResult
  (handler 0x749e60). The builder 0x559dc0 creates the task, sets all filters, then starts it with
  `task->vtbl+0x30(byte props+0xb)` at 0x559f85, so the filters are always set right before RequestLobbyList (PROVEN; the
  draft called that call "a result limit": it is the search start, and its byte becomes the task+0x48 flag used below).
- Filters are set before that, by the session-search builder **0x559dc0** (ZOnlineServiceSteam slot 42), all with
  `eComparison` = 0 (Equal), `esi` = the accessor `[0xb107d8]`:
```
559e6a  call [edx+0x18]  push key 0xb2c7d8 "GameType", value 4 (or 2 when 0x82fd20 == 2), cmp 0    Numerical
559ebf/559efb/559f20  [ebp+0x18] "Scenario" (flag 1), "CoopDifficulty" (0x200) or "FAGameMode" (0x100)   Numerical
559f49..559f50  [ebx+0x18] "Ranked" (flag 0x20)                                                         Numerical
559f6b  call [edx+0x1c]  "Rank"  (only when ranked)                                                      NearValue
559f82  task->vtbl+0x30(byte [props+0xb])                                                               (a result limit on the task object, GUESS)
```
  No call to +0x14 (String), +0x20 (slots), +0x24 (distance), +0x28 (result count) anywhere: all 25 references to the
  `SteamMatchmaking` import slot were enumerated (`call [0xb107d8]` x17 and `mov reg,[0xb107d8]` x8) and their vtable
  offsets read. Steam's default distance filter therefore applies (GUESS: "close").
- Results: per lobby index the handler 0x749f00..0x749f4d does GetLobbyByIndex (+0x2c) and RequestLobbyData (+0x6c);
  the data-update callback calls **0x86b0f0 / 0x86b134**, which reads `name`, `GameType`, `NumRounds`, `RoundTime`,
  `Scenario`, `FAGameMode`, `CoopDifficulty` with GetLobbyData (+0x48) + `atoi` into a 0x7e-byte result row
  (stride 0x7e; lobby id at row+0x6d / +0x71 of the row base+9, i.e. `[row+9+0x6d]`). The row also gets `GetLobbyMemberLimit` (+0x7c) and
  `GetNumLobbyMembers` (+0x40).
- **CORRECTED: there IS one client-side comparison** (the draft said nothing is compared). 0x86b264..0x86b2b8: if
  `byte [task+0x48]` is set (the byte passed to 0x424840, `props+0xb`; the meaning "hide unavailable maps" is GUESS) and
  `[0x168f750]->vtbl+0x14(row Scenario byte)` returns 0, the row is REMOVED from the list (rows shifted down, count
  decremented). That slot (object vtable 0xbd5494) is 0x5e1510: it returns 1 when 0x87c980 is true (co-op), else the byte
  `[obj+4+slot]` (the blueprint's "level available" byte). PROVEN for the code, GUESS for whether the FA browser sets
  `props+0xb`. So a stock client with the flag set hides a host whose Scenario slot it has marked unavailable; nothing about
  the lobby's build or other content is compared.
- Therefore a stock client sees an expansion host's lobby as soon as it passes the numeric filters (and the row filter
  above). Only the type (private/invisible) or an extra filter on the searching side keeps stock clients out.

## 3. Invite / join-by-friend (PROVEN)

- RTTI names (kl2.exe): `CCallback<ZOnlineServiceSteam, GameLobbyJoinRequested_t>` (name 0xd36720),
  `CCallback<..., LobbyInvite_t>` (0xd366c8), `CCallback<..., LobbyChatMsg_t>` (0xd36780). The constructor
  0x879d40..0x879e80 builds them at `service+0x1c8` (LobbyInvite_t, handler **0x8bf680**), `+0x1e0`
  (GameLobbyJoinRequested_t, handler **0x547950**), `+0x1f8` (LobbyChatMsg_t, handler **0x8bd520**) via the
  `SteamAPI_RegisterCallback` import.
- **0x8bf680 is a bare `ret 4`**: the game ignores LobbyInvite_t. An invite reaches the game through Steam's
  "Join game" -> GameLobbyJoinRequested_t (the overlay / friends list produces it).
- **0x547950**: raises the window (GetWindowPlacement / ShowWindow), stores the 64-bit lobby id from the callback
  param at `service+0x4b5/+0x4b9` (0x5479a0, 0x5479a9), then: if `[0x156b3b8] == 1` calls 0x49b990 (a state change),
  if 0 calls `service->vtbl+0x30(1)` (join pending). No data is checked on the lobby.
- **`+connect_lobby`**: in the session manager (the function starting at 0x506cc0) the code requires `byte [ebp+0x79] == 0`
  (it is set to 1 the first time the menu IS `MainMenu`, so the switch is read once per process), the active menu name
  (`0x7851d0` -> vtbl+0xc) to equal `MainMenu` (string 0xb54fa4) and `[0x156b3b8] == 0`, then
  `strstr([0xdd2640]+0x9f8, "+connect_lobby")` (string 0xb3e2ec, 0x506d7a..0x506d80), `add eax,0xf`, `sscanf(.., "%I64u", &id)`
  (0xb440dc, 0x506d96..0x506d9c), `[service+0x4b5/+0x4b9] = id`, `service->vtbl+0x30(1)`, once (`[ebp+0x79]=1`).
- **CORRECTED consumer of the stored id.** The function is **0x7fc2b0** (`ZOnlineServiceSteam` vtable slot 14; 0x7fc2c0 is
  inside its prologue). It builds a 0x68-byte task with ctor **0x43c650, which stamps the `ZAsyncTaskSessionSearchSteam`
  vtable 0xbd58f4** (not the join task) and calls its vtbl+0x2c (slot 11 = **0x6f2d50**, call at 0x7fc313) with the lobby
  id. 0x6f2d50 does `RequestLobbyData` (+0x6c, 0x6f2d8c) for that id and makes a one-row result list: an invite first
  fetches the lobby's data and goes through the row builder 0x86b0f0 (task+0x48 is not set by this path as far as read, so
  the availability filter is probably off, GUESS). The real `JoinLobby` is `ZAsyncTaskJoinLobbySteam` (vtable 0xbd587c, ctor
  0x4d4bb0) slot 8 = **0x572010**, `JoinLobby` (+0x34) at 0x57202b; that task is created at 0x6d86ec in
  `ZOnlineServiceSteam` slot 45 (0x6d8640). The chain from the row to 0x6d8640 was **not traced** (GUESS).
- Completion **0x629980** (CCallResult handler for LobbyEnter_t, set up at 0x572030): on failure flag sets task state 3;
  else state 1, then `GetLobbyOwner` (+0x88, 0x6299cb) and stores the owner id in the task. **It does not read
  EChatRoomEnterResponse or any lobby data**, so the Steam-level join is never refused for content (PROVEN for this
  handler only; the pre-join data fetch and the later start gate are separate). (The game's other rejections come later: the "everybody
  owns this map" gate 0x6c49a0, see the blueprint.)
- The game never calls `InviteUserToLobby` (+0x3c) or `SetLobbyType` (+0x80). `SetLobbyJoinable(false)` (+0x84, `push 0`) is
  called only at 0x406687 inside 0x406560, when a SteamID argument equals `SteamUser()->GetSteamID()` (0x40665b..0x406679;
  PROVEN; "at session start" is the older note's reading, GUESS). GUESS: invites go through the Steam friends list "Invite to game" /
  "Join game" and need a lobby the friend is allowed to join (types 0, 1, 2).

## 4. What a KLHook patch would change

CEG status (from `klhook/klranges.h`, 225 hashed ranges; checked here with a script, address -> inside a hashed range?):
0xb107d8 import slot **no**; 0x705000-0x705fff **no**; 0x869000-0x86afff **no**; 0x8e5158 / 0x8e5169 / 0x8e5173 **yes**;
0x559dc0 / 0x424851 **yes**; 0x62998e / 0x6299b0 **yes**; 0x547950, 0x822900, 0x4ec7e2, 0x506d96, 0x7fc2c0 **yes**.
A byte change in a "yes" range ends a real session (re/antitamper.md). So the options, safest first:

### Route A (recommended): proxy `ISteamMatchmaking` behind the import slot 0xb107d8
Same pattern as klsteam.c (`klh_iat("steam_api.dll","SteamMatchmaking", proxy_accessor, &real)`); 0 integrity checks on
the slot. The game fetches the interface afresh at nearly every use (the caches are inside single functions: 0x869430,
0x559dc0, 0x4cf798, 0x749f00, 0x86b0f0, 0x8bd520, 0x406560), so a one-pointer proxy object with a copy of the real
table (slots 0..0x8c step 4) and these overrides works. The vtable must be verified first against
`steamclient.dll`'s adapter (as klsteam.c did for UserStats); the layout above is **ASSUMED to be 008 without
CompatibleMembersFilter** but fits all 25 call sites.

| goal | proxy slot | what it does |
|---|---|---|
| (a) friends-only / invite-only | **+0x30 CreateLobby(type, max)** (slot PROVEN; per the Steamworks docs, GUESS for this build: FriendsOnly and Private lobbies do not appear in RequestLobbyList results at all, so friends would have to join through Steam's "Join game" -> 0x547950, not the in-game browser) | replace `type` by 1 (FriendsOnly) or 0 (Private, invitees only, not found by search) whenever the session is the expansion's; keep `max`. Covers the ranked path too (type 3 -> 1/0; 3 is only chosen for ranked, which a grafted map should never be) |
| (b) build key on the host | **+0x4c SetLobbyData(id, key, value)** | after forwarding a call whose key is `"name"` (first call of 0x869430, used for both create 0x82293b and updates 0x4ec7e2), forward one more call `SetLobbyData(id, "klx_build", "<build id>")` |
| (b) build key, search | **+0x10 RequestLobbyList()** | before forwarding, call the real **+0x14 AddRequestLobbyListStringFilter("klx_build", "<build id>", 0 /*Equal*/)** (it is accumulated until RequestLobbyList and then cleared). A stock lobby has no such key and is not listed |
| (b) build key, join | **+0x34 JoinLobby(id)** and/or **+0x88 GetLobbyOwner(id)** | JoinLobby is the only point that sees the id before the game; a client-side check needs the lobby's data first (RequestLobbyData +0x6c is asynchronous). Cheapest: in **+0x88** (called by the game right after a successful LobbyEnter, 0x6299cb) read `GetLobbyData(id,"klx_build")`; on mismatch call real **+0x38 LeaveLobby(id)**. What the game then does (it already stored state 1) is **GUESS**; the host-side guard below is the dependable one. **Added:** +0x88 is called from at least three other sites (0x4e4bb7 compares the owner with the service's stored one, 0x7ea683 is a wrapper, 0x6299cb), so the hook must act only on a lobby id it saw in +0x34 JoinLobby, not on every call |
| friends-only for the join side | none needed | the join task does not look at the type |

String filter semantics and the key text: the filter key is at most 255 bytes, value too; use
`klx_build` and a short hex (the KLExpansion fingerprint of the blueprint, 2.3). The Steam call-site count is small
and every one passes the interface pointer in `ecx`, so a proxy whose methods are `__thiscall` (MSVC `__fastcall`
shim with a dummy edx) is the usual way.

### Route B (unneeded unless A fails): code patches in non-hashed pages
- **0x705000 CreateLobby task (page not hashed)**: `705028  8b 4c 24 10` (`mov ecx,[esp+0x10]`) -> `6a 01 59 90` (`push 1 / pop ecx / nop`) forces FriendsOnly; `6a 00 59 90` forces Private. The max members is the `bf 10 00 00 00` at 0x70500b (change the 16 here, or override byte `props+5`). GUESS (not checked against the loader's guard): the page is not under CEG, but `KLHook` has never patched .text without a "luck" tag, so this needs the same live check as the other detours (re/antitamper.md 218-226).
- **0x869430 lobby data (not hashed)**: a detour at the final `call edx` (0x869725, 2 bytes) into a cave that makes one extra SetLobbyData with `edi` (the vtable) and the lobby id from the arguments `[esp+0x40]/[esp+0x44]` (second pair of dwords is the lobby id as passed by the caller 0x82293b / 0x4ec7e2). Needs a cave and a careful stack picture: GUESS.
- Do **not** patch 0x8e5158 / 0x8e5169..0x8e5173 (the game's own type choice, hashed) or 0x559dc0 (filters, hashed).

### The host-side build guard (independent of the lobby type)
re/netcode.md says there is no level hash check, and none of the join code above has one. The two-sided guard
therefore is: (1) the lobby key `klx_build` keeps stock players out of the search; (2) the **member data** `klx_fp`
(`SetLobbyMemberData` +0x60) lets the host see every member's fingerprint, and the blueprint's `available[slot]` gate
(0x6c49a0, `[[0x168f750]+4+slot]`) holds the countdown while any member differs. (1) alone is not enough: an invite or
`+connect_lobby` join skips the search, and 0x547950 / 0x629980 check nothing. (2) lives in the blueprint's design.

## 5. Not established

- The exact `SteamMatchMaking` interface version string. kl2.exe holds none; `steam_api.dll` carries the text
  `SteamMatchMaking008` (PROVEN, offset 0x13cdc; also SteamUser013, SteamFriends005). `C:\Steam\steamclient.dll`'s
  `CAdapterSteamMatchmaking008` vtable has 36 slots (0..0x8c), which equals the layout used here ending with
  SetLobbyOwner (+0x8c) and no CompatibleMembersFilter/SetLinkedLobby; with the semantic fit of every call site that makes the
  layout very likely right, but the per-slot argument sizes of the adapter were not decoded. Slots 0x14-0x28 order (String, Numerical, NearValue, FilterSlotsAvailable,
  Distance, ResultCount) is from the SDK header **as remembered**; the two used here (+0x18 Numerical with 3 args, +0x1c
  NearValue with 2) are consistent with the game's argument counts and with the literal keys.
- Whether `ELobbyComparison` in String filters takes the same enum value (0 = Equal) in that 008 generation: GUESS,
  because the game's own Numerical calls push 0 for Equal.
- Which function fills the property block's `props+5` (max players) for Fragile Alliance, and thus the real online
  player limit: not traced (default 16 when the flag is absent).
- Whether `LeaveLobby` inside a hooked `GetLobbyOwner` produces a clean "join failed" in the UI, and how Steam's
  "Invite to game" behaves for a type-0 lobby: both need a live two-account test (the machine has one Steam account).
- Whether CEG hashes cover thunk memory the proxy creates: the proxy is in the hook DLL, not in kl2.exe, as klsteam's.
- ISteamFriends use: offsets +0x00 (persona name, 0x869446), +0x1c, +0x0c, +0x4c, +0x50, +0x58 are called at 0x8aec31,
  0x8db740, 0x64c286, 0x55a1f6, 0x5789e6, 0x5e2853, 0x5ffad6 (a re-scan also found 0x418c54, using +0x48 and +0x20..+0x2c); **not mapped to names**, and no rich-presence `connect`
  call was identified.

## 6. Route A implemented: KLHook v82g, `klhook/klmm.c` (2026-10-17, NOT RUN, not installed)

Keys (`KLHook.ini`, `[Net]`, both default 0): `PrivateLobby` 0 / 1 / 2 (2 = Private, Steam type 0; 1 = FriendsOnly, type 1)
and `BuildKey` 0 / 1. With both 0 **nothing is installed** (the import slot 0xb107d8 is not touched): v82f behaviour. With a
key set, `klh_iat("steam_api.dll", "SteamMatchmaking", ...)` swaps the slot for an accessor that hands out a proxy object
(36-slot table: 33 naked tail jumps into the real table, three overrides). The accessor refuses (logs `NOT PROXIED`, the
game keeps the real interface) unless `steam_api.dll` holds exactly the text `SteamMatchMaking008` and no other
`SteamMatchMaking0xx`, and all 36 real slots point into code of a loaded module.

| slot | override | does |
|---|---|---|
| +0x10 RequestLobbyList | `BuildKey=1` | real +0x14 `AddRequestLobbyListStringFilter("klx_build", id, 0)`, then the real call |
| +0x30 CreateLobby | `PrivateLobby` != 0 | type -> 1 (key 1) or 0 (key 2); max members as given; 64-bit call handle returned untouched |
| +0x4c SetLobbyData | `BuildKey=1` | the real call first (result returned), and when its key is `"name"` one more real call with `"klx_build"` = id |

Build id: FNV-1a over the sorted `<dir>\<file>`, size and zip central-directory hash (`klsteam.c` `klx_fingerprint`,
which holds every member's CRC-32) of every `<game>\<Root>\Maps\*\F*_Main.zip`; 8 hex digits, `none` if there are no maps.
Write times, `.WHD/.WAV` beside a zip and loose ini files are not in it. GUESS that this set is what a friend has to share.
Log lines (`mm: ...`, at most 200, never a Steam id): wrapper installed, build id, one per CreateLobby, SetLobbyData `name`
seen, RequestLobbyList, each with `online=0/1` (what `kl_online()` answered).

**OnlineSafe is not a gate here** (deliberate; see the klmm.c comment): `kl_online()` is probably already true when the host's
CreateLobby runs, so a gate would disable the feature when needed; these calls change lobby metadata only. The log shows
`online=` so the first live run tells. Putting `if (kl_online())` before the forward in the three overrides gates it.

### Slots that were GUESS in section 5 and are now PROVEN (static read of `C:\Steam\steamclient.dll`, 2026-10-17)
- `CAdapterSteamMatchmaking008` has 36 slots; the `ret n` of slots 11..35 are 8 8 8 0x10 8 0x10 0xc 0x10 8 0x1c 0xc 0x14 0x10
  0x10 0x1c 8 0x18 0x14 0xc 8 0xc 0xc 0xc 0x10: exactly the SDK argument sizes of GetLobbyByIndex .. SetLobbyOwner
  (a CSteamID is two dwords). The layout without CompatibleMembersFilter is therefore right.
- Slots 4..10 are tail jumps into the client class (vtable of `IClientMatchmakingMap`, whose methods pop 0 / 0xc / 0xc / 8 /
  4 / 4 / 4 bytes) and slot 12 into its +0x34 (pops 8). Slot 5 (+0x14) reads arguments 1 and 2 with the string
  serialiser 0x386280b0 and argument 3 as a 4-byte number: **AddRequestLobbyListStringFilter(key, value, comparison), 12 bytes**.
  Slot 6 reads argument 1 as a string and 2, 3 as numbers (Numerical), slot 7 pops 8 (NearValue). The order String,
  Numerical, NearValue is confirmed; the stack effect of the call the proxy makes is exact.
- Still GUESS: comparison value 0 = Equal for a string filter (same enum as the numeric ones the game pushes 0 for); that the
  filter accumulates until RequestLobbyList (SDK documentation); FriendsOnly / Private lobbies missing from search results;
  `kl_online()` at CreateLobby time; the import name `SteamMatchmaking` is PROVEN (present in kl2.exe and exported by steam_api.dll).

## 7. Static check of the v82g proxy against Dog Days' own files (2026-10-17, handover; nothing run, nothing installed, no source changed)
Read only: `C:\Steam\...\Kane & Lynch 2 - Dog Days\kl2.exe` and `steam_api.dll` (121,984 bytes), capstone through `tools/kl_exe.py`.
- **Interface version**: kl2.exe holds no version string, only the import `steam_api!SteamMatchmaking` (IAT 0xb107d8, confirmed by walking
  the import directory). steam_api.dll holds exactly one `SteamMatchMaking0xx` text, `SteamMatchMaking008` (plus `...Servers002`,
  which `klmm_has_008` does not match: it compares 17 bytes "SteamMatchMaking0"). Its export is `mov eax,[global]; ret` (a cached
  pointer filled by SteamAPI_Init, null before it: the wrapper returns 0 then), so the accessor is cdecl, no arguments, stable object.
- **Slot order (SDK 008, no CompatibleMembersFilter)**: 0..3 favourites, 4 RequestLobbyList, 5 String / 6 Numerical / 7 NearValue /
  8 SlotsAvailable / 9 Distance / 10 ResultCount filters, 11 GetLobbyByIndex, 12 CreateLobby, 13 JoinLobby, 14 LeaveLobby, 15 Invite,
  16 GetNumLobbyMembers, 17 GetLobbyMemberByIndex, 18 GetLobbyData, 19 SetLobbyData ... 35 SetLobbyOwner. The 24 `ret n` values of
  section 5 for slots 12..35 match this list one by one (rechecked: 8 8 8 0x10 8 0x10 0xc 0x10 8 0x1c 0xc 0x14 0x10 0x10 0x1c 8 0x18
  0x14 0xc 8 0xc 0xc 0xc 0x10). Proxy indices 4 / 5 / 12 / 19 are right.
- **How kl2 calls it** (every one of the 25 references to 0xb107d8 is `call [slot]` or `mov reg,[slot]` + `call reg`, i.e. through
  the patched IAT; vtable offsets seen at the call sites): +0x10 RequestLobbyList (0x424846), +0x18 Numerical filter (key "GameType",
  0x559e6a), +0x2c GetLobbyByIndex, +0x30 CreateLobby (0x705024), +0x34 JoinLobby, +0x38 LeaveLobby, +0x40 / +0x44 GetNumLobbyMembers /
  GetLobbyMemberByIndex, +0x48 GetLobbyData, +0x4c SetLobbyData (0x86944e, key "name", string at 0xb2e088; the vtable slot address is
  cached in ebx across calls, harmless: it is the proxy table), +0x64 SendLobbyChatMsg, +0x68 GetLobbyChatEntry, +0x6c RequestLobbyData,
  +0x88 GetLobbyOwner. All consistent with 008. (The addresses in parentheses are real kl2 VAs of one call site each.)
- **Calling convention**: thiscall = ecx this, args on the stack, callee pops. `__fastcall(self, edx, args...)` has the same stack
  layout and callee cleanup, so both the three overrides (ret 0 / 8 / 16) and the outgoing calls through `KLMM_REAL(n)` with ecx = real,
  edx = 0 are right; 64-bit SteamAPICall_t in edx:eax, `bool` in al, CSteamID as two dwords low first. Argument counts: RequestLobbyList 0,
  String filter 3 (12 bytes), CreateLobby 2 (8), SetLobbyData 4 dwords (16). The naked forwarders reload ecx from `klmm_real` and jump
  through the real table, stack untouched. ELobbyType Private 0 / FriendsOnly 1 and ELobbyComparison Equal 0: from the SDK, as coded.
- **Hooked object**: the only way kl2 reaches the interface is the IAT slot, which `klh_iat("steam_api.dll","SteamMatchmaking")` swaps
  (kl2.exe is not packed; imports resolved before any DLL entry point; `steam_api.dll` is a static import, so `GetModuleHandle` in
  `klmm_init` succeeds). Nothing in kl2.exe keeps the interface pointer past a call, only vtable slot addresses of the object it got.
- **PrivateLobby=0 and BuildKey=0**: `klmm_init` returns right after reading the two ints; no IAT write, no critical section, no log
  line, `klmm_real` stays null. klhook.c's v82g diff is a comment block, the include and that call: v82f behaviour.
- **Build**: `klhook\build_auto.bat` (TEST) built clean into `klhook\out_auto\dinput8.dll` (1,102,848 bytes). Run it with its full path
  (`cmd /c C:\kl-merge\kl-merge\klhook\build_auto.bat`); `build_auto.bat` alone is not found from the tool shell. SHIP build not made.
- **Fixes**: none needed. **Still GUESS**: comparison 0 = Equal for a string filter; that the game's "name" SetLobbyData is made for
  the host after creation (one site only, so the build key is written only if it runs); that Steam really hides Private / FriendsOnly
  lobbies from search; `kl_online()` at CreateLobby time; whether the game ever calls InviteUserToLobby (no +0x3c site seen, so
  PrivateLobby=2 would rely on Steam's friends list / overlay invite, not on the game); the 008 slot order is from memory of the SDK
  headers, backed by the 24 ret counts (exact for stack sizes, but two same-sized neighbours could in theory swap).

## 8. How a friend gets into a FriendsOnly / Private lobby: every Steam callback kl2.exe registers (2026-10-17, static only, nothing run, read-only `kl2.exe`)
Method: `tools/kl_exe.py` + capstone. `SteamAPI_RegisterCallback` = IAT 0xb107d0 (16 call sites, each inside a `CCallbackBase::Register`
wrapper `[obj+0xc]=this [obj+0x10]=handler [obj+0x14]=0; push id; push obj; call IAT`), `SteamAPI_RegisterCallResult` = IAT 0xb107dc
(one wrapper, 0x92a930, 7 callers). The id is the immediate pushed in the wrapper. The constructors that stamp the CCallback vtable were read for
the handler and the owning class (RTTI name of the vtable).

| id | callback | owner class (RTTI) | handler VA | where registered |
|---|---|---|---|---|
| 333 | GameLobbyJoinRequested_t | ZOnlineServiceSteam | **0x547950** | service+0x1e0, ctor 0x879d40 (call 0x879dde -> wrapper 0x838c70) |
| 503 | LobbyInvite_t | ZOnlineServiceSteam | 0x8bf680 = bare `ret 4` | service+0x1c8 (0x879dab -> 0x5fb810) |
| 505 | LobbyDataUpdate_t | ZAsyncTaskSessionSearchSteam | 0x86b0f0 (row builder) | per search task, 0x43c6b1 -> 0x8da360 |
| 507 | LobbyChatMsg_t | ZOnlineServiceSteam | 0x8bd520 | service+0x1f8 (0x879e11 -> 0x88ae00) |
| 507 | LobbyChatMsg_t | ZAsyncStartSessionAndSyncLobby | 0x745c80 (re-verified) | 0x489252 -> 0x88ae00 |
| 331 | GameOverlayActivated_t | ZOnlineServiceSteam | 0x6ac6c0 | service+0x210 (0x879e44 -> 0x552860) |
| 331 | GameOverlayActivated_t | ZFFPlayerProfileSteam | **0x70e680** (corrected: 0x7ae680 is the id-304 handler) | 0x7ae429 -> 0x45f220 |
| 304 | (PersonaStateChange_t by SDK numbering, GUESS) | object with vtable 0xb14930 | 0x7ae680 | 0x7ae3f9 -> 0x4e4af0 |
| 704 | SteamShutdown_t | ZOnlineServiceSteam | 0x78e8a0 | service+0x228 (0x879e77 -> 0x483640) |
| 117 | IPCFailure_t | ZOnlineServiceSteam | 0x78e8a0 | service+0x240 (0x879eaa -> 0x535a20) |
| 1101 | UserStatsReceived_t | ZAsyncTaskReadUserStatsSteam | 0x4341c0 | 0x6ca9e6 -> 0x6a0be0 |
| 1102 | UserStatsStored_t | ZAsyncTaskWriteUserProfileSteam / ZAchievementsSteam | 0x7f9e70 / 0x5229a0 | 0x53e7dd (wrapper 0x816060), 0x7842ac (wrapper 0x82f730) |
| 1103 | UserAchievementStored_t | ZAchievementsSteam | 0x5229a0 | 0x7842dc -> 0x7e7c30 |
| 1203 | P2PSessionConnectFail_t (RTTI name) | Quazal::SteamSocketContext | **0x47a3d0** (corrected; 0x6e2690 is the 1202 handler) | 0x544488 -> 0x76c370 |
| 1202 | (P2PSessionRequest_t by SDK numbering, GUESS) | same ctor as 1203 (object vtable 0xb36ea4, no RTTI name) | 0x6e2690 | 0x54445b -> 0x706e60 (corrected: it HAS a caller) |
| 1005 | (DlcInstalled_t by SDK numbering, GUESS) | ZDownloadableContentManagerSteam | 0x845700 | 0x717f7d -> 0x8a2bc0 (corrected: it HAS a caller) |

Call results (`RegisterCallResult`, wrapper 0x92a930): RequestLobbyList 0x424862 (handler 0x749e60); **JoinLobby 0x57203c, handler 0x629980 =
the LobbyEnter_t (504) completion** (the task ctor 0x4d4bb0 writes 504 at task+0x18, 0x4d4be1); CreateLobby 0x705046 (handler 0x822900);
four more at 0x5ebe6d, 0x7552a0, 0x78974d, 0x7ef44e (not identified).
**Not registered as callbacks anywhere: 337 GameRichPresenceJoinRequested_t** (no push of 0x151 in .text), **506 LobbyChatUpdate_t** (the two
`push 0x1fa` hits, 0x8f63c3 and 0xa4ef1a, are `__LINE__` arguments of assert calls), and **504 LobbyEnter_t as a plain callback** (call result only).
So 337 is not handled, and the game never sets a `connect` rich-presence key either: SteamFriends is used at 8 sites, vtable offsets
0x00 (persona name), 0x0c, 0x1c, 0x4c, 0x50, 0x58; nothing at or above 0x5c, so no SetRichPresence and no ActivateGameOverlayInviteDialog
(SDK-005 numbering, GUESS).

### Correction to section 3
`service->vtbl+0x30` is **slot 12 = 0x45a950**, which is only `mov [ecx+0x4b4], al` (a "join pending" byte). Both the 333 handler (0x547950)
and the `+connect_lobby` parse (0x506cc0, stores at 0x506dbf..0x506dcb) store the 64-bit lobby id at service+0x4b5/+0x4b9 and call that setter with 1.
Slot 11 (0x4a3ca0) is the getter of the byte, slot 13 (0x8925c0) clears it, slot 14 (0x7fc2b0, the "consumer" of section 3) reads the id and builds the
search task. Chain: handler -> flag + id; a poller (NOT FOUND, see GUESS) -> slot 14 -> RequestLobbyData -> row -> join task -> `JoinLobby` 0x57202b.
`+connect_lobby` is searched in `[0xdd2640]+0x9f8` (the process command line) only in the main menu, once per process, with `[0x156b3b8]==0`.
JoinLobby (+0x34) has exactly one call site (0x57202b), so there is no second join route; 0x547950 itself does not call JoinLobby.

### Conclusion
- Both entry points exist and end in the same pending-join state: Steam delivers **GameLobbyJoinRequested_t (333)** to a running kl2.exe
  (handler 0x547950), or starts a not-yet-running kl2.exe with **`+connect_lobby <id>`** (parsed in MainMenu). Neither reads the lobby type or any
  lobby data, and the LobbyEnter completion (0x629980) ignores the response content. LobbyInvite_t (503) is ignored (bare `ret`).
- Steam UI that produces 333 / `+connect_lobby`: (a) friends-list "Join game" and (b) friend right-click / overlay "Invite to game" are the Steam
  client's own lobby features (the client knows the user's lobby from CreateLobby/JoinLobby); the game takes no part in either, so for kl2 they are
  the same path. From SDK documentation (GUESS, not testable offline): FriendsOnly lobbies are joinable by friends ((a) and (b) should work);
  Private lobbies are joinable by invitation only ((b) only). kl2 never calls InviteUserToLobby, so the inviter is the Steam client.
- Recommended setting: `PrivateLobby=1` (FriendsOnly). `PrivateLobby=2` (Private) is the one that may leave friends with no working path.
- Not a path: GameRichPresenceJoinRequested_t (337), LobbyChatUpdate_t (506), the game's own UI (no invite dialog, no rich presence).

### Design (not code): smallest KLHook additions if the first live test shows (a)/(b) missing
1. **Host-side invite (fixes Private, helps FriendsOnly), in `klmm.c`**: capture the lobby id from the `SetLobbyData` override (slot +0x4c; its first
   two dwords are the lobby CSteamID, and the host's "name" write is already intercepted). On the first "name" call of a lobby, for each 64-bit id in a new
   `[Net] InviteSteamIds=` (comma list written by the user; no enumeration of the friends list, no automatic mass invite) call the REAL slot +0x3c
   `InviteUserToLobby(CSteamID lobby, CSteamID invitee)` (`ret 0x10`, bool in al) with ecx = real object, like the existing forwarders. Steam then shows
   the friend an invite; accepting raises 333 (game running) or `+connect_lobby` (not running). Log `mm: invite sent=%d`, no ids. Empty = no-op.
   If "name" is not set for the host (open GUESS, section 7), take the id from the CreateLobby call result (LobbyCreated_t) instead.
2. **Join without the Steam UI (testing, or when Steam does not raise 333)**: `[Net] JoinLobby=<u64>`; once the active menu is `MainMenu` (condition of
   0x506d1b..0x506d65), call the game's own handler 0x547950 (`thiscall`, ecx = the ZOnlineServiceSteam from `[0x168e598]` vtbl+0x2c, one stack
   argument = pointer to `{u64 lobbyId, u64 friendId}`, `ret 4`), i.e. emulate GameLobbyJoinRequested_t. It reuses the game's whole join chain and writes
   nothing into its objects by hand. Alternative with the same effect: put `+connect_lobby <id>` into the command-line buffer at `[0xdd2640]+0x9f8`
   before the menu appears (size and ownership of that buffer must be checked first).
3. A proxy for slot +0x34 (JoinLobby) is NOT needed: it is only the end of the chain and the game never refuses on content.
Both additions are no-ops with their keys empty, like PrivateLobby=0.

### GUESS list
- That the Steam friends list shows "Join game" for a friend in a FriendsOnly lobby and that the client's "Invite to game" works for a Private lobby the
  game made (Steam client behaviour, SDK documentation only; the first live two-account test settles it).
- Ids 304, 1202, 1005 are named by SDK numbering; 1202/1005 are DLC / P2P-request callbacks, irrelevant to joining (handlers now listed in the table, bodies not read).
- The **poller** between the pending byte (slot 11 getter) and slot 14 was not located: searches for `[reg+0x38]` calls after the online-manager accessor
  `[0x168e598]` vtbl+0x2c found only unrelated UI code (0x5b4934 etc.), and the slot-11 callers (0x4809ea, 0x5e2e39, 0x56e15d) gate something else. It may
  run through a state-machine object that holds the service. So the exact menu/moment in which a pending join is consumed is unknown; a request that
  arrives mid-match (`[0x156b3b8]==1`) goes to 0x49b990 instead of the pending flag.
- The `SetLobbyData "name"` call being made for the host (section 7), and `InviteUserToLobby` being slot +0x3c with `ret 0x10` (SDK 008 order plus the
  section 7 ret-size list; two neighbours of equal size could in theory swap).


## 2026-10-18: owner-map readiness check (kl-merge-e5, workflow wd7vzdmcy, read-only)


Read-only. Nothing was launched, installed or committed. Tags: **FACT** means I re-read it in the code or the exe. **GUESS** means inferred. **CARRIED** means taken from the two reports and not re-checked.

`re/private_match.md` (347 lines) and `re/fa_private_match_blueprint.md` already exist. They cover lobby creation, lobby keys, the friend-join path and the `klmm` proxy. This note should be added as a new section and must not replace them.

### 0. Adversarial check of the two reports

**Re-verified FACT**
- The role gates exist as stated: `klbot.c:364`, `klbalance.c:378` and `klfed.c:202` all reject `[sm+0x54]` of 2 or 3. `klfedkit.c:881` does the same.
- `kl_online()` is at `klhook.c:255-265`. The report said 249-266, so the lines are slightly off. Its body matches the report.
- Vtable slots 7, 89 and 194 match the report's table for all four classes (read from the exe):

  | Class | Slot 7 | Slot 89 | Slot 194 |
  |---|---|---|---|
  | Heist (0xbd3514) | 0x74b6d0 | 0x49d170 | 0x8fa6d0 |
  | FA Sv (0xbd2eb4) | 0x827f00 | 0x70f0a0 | 0x51e390 |
  | FA Cl (0xbd31e4) | 0x4f27b0 | 0x70f0a0 | 0x5b1410 |
  | FA base (0xbd2b9c) | 0x5671e0 | 0x70f0a0 | 0x5b1410 |

- 0x5b1410 uses `[rules+0x1dc]`, `+0x1e0` and `+0x1e4` and calls vtable +0x164 (slot 89). So the offsets are shared with the FA base class, not Heist-only.
- 0x57b2d0 is `add ecx,0x250; jmp 0x962850`, so it reads `m_szVersion`. Its only direct `E8` caller is 0x53919c. Indirect or vtable callers were not scanned.
- The `klchar.c:298-301` online branch only logs. Lines 302-307 then return unless the type is 4 and the vtable is Heist. The inert-online result is accidental, as the hook report said.
- (CORRECTED 2026-10-19 Verify: `klslot.c:280` skips only the Arcade PLAYLIST override when `kl_online()` is true; the file redirect itself has no online guard.) `klgun.c:409` and `kljoin.c:244` are guarded by `kl_online()`.
- `klmm.c:48-53` is deliberately not gated.

**Corrections and upgrades**
1. **0x760e50 (orders).** The report says it "returns at once on a network client". The actual test is `0x863a60(sm)` AND `0x4b0a40(sm)`. 0x863a60 is a jump table on `[sm+0x54]` that I did not decode. 0x4b0a40 is exactly `[sm+0x54]==3`. The early return needs both, so it is not an unconditional client test.
   - This upgrades one GUESS: **role 3 = network client** is now FACT, because the game has a helper named by that test.
   - Role 2 = server is still unverified directly.
2. **`klbot.c:391-407` was missed by the hook report.** `klb_online_session()` is a role 2/3 reader. It accepts only Sv/Cl rules, and only when `[HUD] Online=1` (`klhud.c:1637`, default 0). It reads a state from `[sm+0x70]` as a GUESS (`klbot.c:405`). The claim "HUD is low risk" holds, but only by that opt-in default. Also `klhud.c:1549` lets the HUD run on any level online, not only on non-stock levels.
3. **Slot-availability gate.** The game report calls the 0x6c4cf5 gate content-blind (CARRIED). That makes the redirect-mismatch hazard worse than either report said. A client without the expansion has stock `F01..F07` available, so the gate passes. It then silently loads the stock map while the host loads `DMxx`. No dialog appears.
4. **`kl_online()` false positive.** With type 4 and a non-Heist vtable it returns 1. During load or menu transitions, `[rules]` may be a stale or different object (GUESS). Online-only code should also demand role 2/3 or an Sv/Cl vtable. It should not rely on "not Heist".
5. **GUESSes still not settled by either report.**
   - Who is the simulation station.
   - Who prices a hit between machines.
   - Whether a client's rule writes are overwritten.
   - Host migration.
   - Join code 3 "Clash".
   - Whether the CEG scaffolding rejects a patched exe.
   - What happens on a mismatch.
   - The wire ref id space.

   Treat all of these as open.
6. **Not re-verified (CARRIED).** The REF slot table, the 0x6c4cf5 gate, the 0x40a880 resolver, the lobby-key list and the klcrew_rt/klhop line numbers. The REF table is the one to double-check before relying on it.

### 1. What is known

- **Mode.**
  - The session manager is `sm=[0x168e598]`. `[sm+0x54]` is the net role (3 = client is FACT; 0/1 local and 2 server are GUESS from reading). `[sm+0x5c]==4` covers all FA, Arcade included.
  - Arcade runs the Heist rules (0xbd3514). Online runs Sv (host) or Cl (client). So every hook module that is gated to Heist is inert online (FACT). That includes bots, escort, balance, down/revive, fed, crew join and the wardrobe.
- **Maps.**
  - The host replicates a level slot index, not a name (CARRIED). Each machine maps it to a scene through its own level list.
  - The `Maps\DMxx` redirect needs the page latch, and that latch is dropped for online (CARRIED).
  - `m_szVersion` is never compared.
  - Nothing compares the build, the ini or the map set between peers. `klmm BuildKey=1` is the only mechanism, and it is NOT RUN.
- **Replication.**
  - Objects go over the wire by 16-bit scene reference. Any difference in scene order silently breaks doors, loot and hits (the effect is a GUESS, the absence of a check is FACT).
  - The escape state lives in the score object. It is driven by the shared slot 194 of the FA base class.
- **AI and privacy.**
  - Online FA has no AI heisters (strong GUESS from the class split).
  - Only the host can read the private bit (`klnet.c`).

### 2. Risk table

| Area | Risk | Reason |
|---|---|---|
| Different map or ini on the two machines | **High** | Silent desync. No runtime check exists. |
| Client without the hook or the expansion | **High** | The slot gate passes and it loads the stock map. |
| `[Expansion] Page=2` with a public lobby or Quick Match | **High** | A Dead Men map is loaded against strangers' stock map. |
| Teleports (`klcrew_rt`, `klhop`, `kljoin`) from a client | **High if ungated** | 0x62a900 with b=1 replicates (CARRIED). Today they are inert. |
| Rule-float, heist-byte and money-byte writes (`klmove`) | Medium to high if ungated | Overwritten or divergent. A GUESS. |
| `klbalance` / `klbotdown` | Medium | Damage is priced on the shooter's machine (GUESS). Inert today. |
| `kl_online()` false positive on load | Low to medium | See correction 4. |
| `klnet` Tune on a client | Medium | The client's private status is unverifiable. It is trust-based. |
| `klmm` | Unknown | NOT RUN. |
| HUD, wardrobe look, `kltalk`, `klcam`, `klgun`, `klsteam` | Low | Local or cosmetic only. |
| Escape "visit 1" bug (`1e0` before state 1) | Medium (GUESS) | The gating code is in the shared FA base. |
| 16-bit refs | Low | Every checked map has a REF count at or below 38,706, under 65,535. Stock F08 (34,369) already exceeds 32,767. |

### 3. Changes before a first private-match test (ordered, each opt-in)

1. **No code.** Test only with the Arcade-only modules off or inert. Do not turn on `[HUD] Online`, `AllMaps`, `CrewJoin` or `BuildKey`.
2. **Identical installs.** Compare the `KLExpansion` `manifest.json`, the sha1 of every `Maps\DMxx` file, `dinput8.dll` and `KLHook.ini` on both machines. The owner does the install.
3. **Test-only `[Expansion] Page=2` on both.** Remove it afterwards and never leave it on for public play.
4. **Log-only fingerprint.** Add `[Net] Log=1`, and log the manifest id, the hook build and the redirect line in `KLHook.log`. No behaviour change.
5. **Opt-in fingerprint in the lobby.** Extend `klmm` `BuildKey` with the manifest content id. This is the base for refusal. It needs a live run of `klmm` first.
6. **Opt-in refusal.** Refuse to start on a fingerprint mismatch. Clear the availability byte so the host's countdown stalls (the same route the game uses for a missing level).
7. **`klh_net_role()` helper.** One function returning local, host or client. Any Sv port is host-only (role 2), and nothing ever acts on role 3.
8. **Make `klchar`'s online branch return.** Do it truthfully, so safety does not depend on a later check.
9. **Balance and down online.** Leave off until the damage path is read.
10. **Hardened `kl_online()`.** Require an Sv/Cl vtable or role 2/3 before treating a non-Heist object as online.

### 4. Two-machine test plan

Steam allows one instance per account, so a single PC cannot test the netcode. `-o StartAsServer/StartAsClient` and System Link are NOT ESTABLISHED as a bench.

**Stage S (one machine).** Create a private game on a stock map with `[Net] Log=1`. Check the `net: session` line, the lobby PRIVATE line and the update numbers.

**Stage 0 (both PCs, friends-only).**
1. The host picks Airport (F03), which is DM03 on page 2. DM03 is a single-part map and the closest to stock FA.
2. Check first that both logs show the same slot index and the redirect line before the countdown. If they differ, stop.
3. Then check that the client loads, spawns and moves. Check doors, loot pickup and a police wave.
4. Escape: watch the `[rules+0x1dc]` transitions on both machines, and whether the vehicle appears on the client.

**Stage 0b.** Try `-o DisableSyncChange2`. If there is jitter, try `[Net] Tune=1 PlayerMs=50 RefreshMs=300 AngTol=12`.

**Negative control.** Run once with the client on a different map folder (or without the expansion). The expected result is a silent stock load. This confirms risk 1.

**Stage 1 (not built).** Fingerprint in lobby data, the hook clearing the availability byte, and a refused join.

**Order of maps.** DM03 first. Then DM01, DM02, DM06, DM09 and DM03A. Then the page-3 campaign maps. Retomoto and any map with the kljoin jump come last, because the jump fires locally only and AI trigger lists run on the machine that jumped.

**Logs to compare:** `net: session`, `net: server object` (the level index is `[D+0x1b0]^0xac`), `net: lobby`, `net: level ... NOT stock`, the klslot redirect lines, the klsteam block lines, `KLHook.log`, and any `KLHook_N.dmp` or `kl2_490_crash_*.mdmp`. Note the first desync symptom (a door, loot or vehicle that differs).

**Still open after this plan:** who simulates ZFFActor, where RMCReceiveHit is dispatched, the caller of slot 194 on a client, the id space of the wire refs, the origin of join code 3, host migration, and whether the CEG checks reject a patched exe.

## 2026-10-18: net roles, client escape, hit pricing

Static disassembly of `kl2.exe` only. Nothing was launched and no repo files were written. Each claim from the first draft was re-read against the exe. Corrections are marked **CORRECTED**. Items I could not reproduce are marked **GUESS**.

### 1. Role helpers on `[sm+0x54]` (sm = `[0x168e598]`)

| Helper | Role 0 | Role 1 | Role 2 | Role 3 | Role 4 and up |
|---|---|---|---|---|---|
| 0x863a60 | false | false | true | true | false |
| 0x4b0a40 | false | false | false | true | false |
| 0x8df480 | `[sm+0x5c]==4` | `[sm+0x5c]==4` | true | false | `[sm+0x5c]==4` |
| 0x7f6850 | `[sm+0x5c]==4` | `[sm+0x5c]==4` | false | false | `[sm+0x5c]==4` |

- **FACT, tables re-read:**
  - 0x863a60 uses the jump table at 0x863a78 (roles 0 and 1 go to `xor al,al`, roles 2 and 3 to `mov al,1`). It means "networked".
  - 0x4b0a40 is `cmp [ecx+0x54],3; sete`.
  - The 0x8df480 table is at 0x8df4a8. Roles 2 and 3 fall into `cmp [ecx+0x54],2; sete`.
  - The 0x7f6850 table is at 0x7f6874. Roles 0 and 1 answer yes, roles 2 and 3 answer no.
- **CORRECTED, 0x8df480 caveat:** its role 2/3 branch compares `[ecx+0x54]`, using the caller's `ecx`, not the `edx` it loaded from the session manager. It is correct only if the caller passes `ecx=sm`. The "role 3 false" cell assumes that.
- **CORRECTED, "only code that tests role == 2":** this is false.
  - 0x83da50 is a separate, real helper (`xor eax,eax; cmp [ecx+0x54],2; sete al; ret`). It has 0 direct callers, so it is probably called through vtables or pointers.
  - 0x8df4a0 is the fall-through inside 0x8df480.
  - 0x4649a5 only looked like a match. It compares offset 0x254 of another object.
- **CORRECTED, caller counts.** Direct `call rel32` counts:

  | Helper | Direct callers |
  |---|---|
  | 0x863a60 | 350 (not ~480) |
  | 0x4b0a40 | 59 |
  | 0x8df480 | 239 |
  | 0x7f6850 | 291 |

  Any indirect calls would be extra. The statement that role 3 is tested all over the code stands. `re/private_match.md` is wrong to say "nothing ever acts on role 3".
- **Role setter 0x74b210 (FACT):** `SetNetRole(this=sm, role)`.
  - It returns early if the role is unchanged.
  - Role 0 clears `[sm+0x5c]` and `[sm+0x58]`.
  - Role 1 sets `[sm+0x58]=1`.
  - Other roles only write `[sm+0x54]`.
- **CORRECTED, call sites.** There are 26 direct calls. The role argument below is the nearest `push imm` before the call, so treat it as a heuristic.

  | Role | Sites |
  |---|---|
  | 0 | 0x4483b8, 0x473b93, 0x700b2c, 0x92a19b |
  | 1 | 0x4ccf86, 0x627df4, 0x741381, 0x8734ab, 0x8734bf, and 0x7d0c02 (push is far back, unclear) |
  | 2 | 0x77e309, 0x77e369, 0x7ba9b0, 0x81ff3a, 0x92a260, 0x92a48f |
  | 3 | 0x43d47f, 0x448216, 0x473b4d, 0x643f79, 0x700a52, 0x80782b |

  - The draft listed only one site for role 2 and four for role 1.
  - 0x873453 is a direct write `[esi+0x54]=3` in the code that handles the `StartAsClient` string (0xb622c8). It does not go through the setter.
  - In the same function, the `StartAsCoop`, `EnableCoop` and `StartAsSinglePlayer` strings lead to role 1 (0x8734ab and 0x8734bf).
- **CORRECTED, `MercsGameMode` function (string 0xb61e38, read at 0x7ba96b):**
  - A local `ebp==0` pushes 1 and sets role 1, after calling 0x64e4f0 with 1.
  - `ebp==1` or `ebp==2` sets role 2, after calling 0x64e4f0 with 2 or 3.
  - 0x64e4f0 compares and sets `[sm+0x58]`, not `[sm+0x5c]`. The draft said this function only sets role 2.
- **0x700a50 (FACT):** `push 3` followed by `call 0x74b210`. `[sm+0x1a3]=1` is set just before it, and a byte at `+0x1a2` is set through another register just before that (that register is not visibly the same object).
- **0x905460 (CORRECTED):** this is a membership test on `[sm+0x70]`, not a plain range test. It returns true for states 0x17, 0x18, 0x19, 0x1b to 0x21, 0x28, 0x2a and 0x2b. It returns false for 0x1a, 0x22 to 0x27, 0x29, and anything outside 0x17..0x2b. (Table at 0x905488 and jump table at 0x905480; byte 0 means true.)
- **GUESS:** the word "host" for role 2 and "local" for roles 0 and 1. The helper semantics are FACT.
- **GUESS:** treating `[sm+0x5c]==4` as "game type FA". The value 4 is FACT, the name is not.

### 2. FragileAlliance rules slot 194

- **Vtable slots (FACT, found by scanning .rdata):**
  - 0x5b1410 sits at slot 194 of the FA base class (vtable 0xbd2b9c) and of `ZGameRulesFragileAllianceCl` (vtable 0xbd31e4, entry at 0xbd34ec).
  - 0x51e390 sits at slot 194 of `ZGameRulesFragileAllianceSv` (vtable 0xbd2eb4).
  - Sv slot 195 is 0x727610, Cl slot 195 is 0x7a30c0, and Heist slot 195 is 0x55ec70.
- **0x5b1410 is `SetState(byte)` (FACT).**
  - It stores the new state in `[rules+0x1dc]`.
  - State 0 clears `[rules+0x1e0]`.
  - Otherwise, if `[rules+0x1e0]==0`, it calls slot 89 (+0x164). That is the gate at 0x5b144a.
  - It then switches on states 0 to 7 (table at 0x5b19c0).
- **Sv wrapper 0x51e390 (FACT):**
  - It calls 0x5b1410, then calls 0x4b8960 with `ecx=[rules+0x2c]` and the state byte. 0x4b8960 operates on score+0x38c / +0x390.
  - It then calls 0x84f030 on the same object with 0 when the state is 0 or 7. The draft missed this.
  - The only direct `call 0x5b1410` in the exe is at 0x51e398. Every other caller goes through `[vtbl+0x308]`.
  - **GUESS:** that the score object is the DDL `ZScoreFragileAlliance`.
- **Sv per-frame update 0x727610 (FACT):** it is the timer driver.
  - It is skipped while `[0x168ea6c]` is non-zero.
  - It ticks `[rules+0x1d8]`, switches on `[rules+0x1dc]-1`, and calls `[vtbl+0x308]` at 0x7276d4, 0x727743, 0x7277a4, 0x7277d5 and 0x72782e.
  - At 0x7276d4 it pushes 3 if the state is 1, otherwise 4.
- **Cl per-frame update 0x7a30c0 (FACT):** it has the same timer tick and state switch, but contains no `[vtbl+0x308]` call. An exe-wide sweep of `mov reg,[reg+0x308]` found 71 sites, none inside it.
  - Its state-1 case calls `+0x2fc` and conditionally 0x8830f0 on `[rules+0x1e4]`.
  - **GUESS:** `+0x2fc` is a warning or HUD tick.
- **Conclusion (GUESS built on FACT):** a client does not advance the escape state from its own timer. The server drives it and the client gets the state some other way, perhaps through the score object. The client path was not found.
- **Vtable slots of the other slot-194 callers (CORRECTED).** The draft's "Cl[290]", "Cl[298]", "Cl[207]", "Base[27]" and similar numbers do not exist. The `ZGameRulesFragileAllianceCl` vtable has only about 204 slots, and the higher addresses belong to the `ZGameRulesHeist` vtable at 0xbd3514. Correct entries:

  | Function | Slot | What it does |
  |---|---|---|
  | 0x6df7d0 | Heist[86] | `SetState(byte [[this+0x5f8]+0x54])` (FACT) |
  | 0x6a1100 | Heist[94] | |
  | 0x4f9f90 | Heist[82] | |
  | 0x4fb620 | Heist[3] | |
  | 0x51bbe0 | Heist[4] | |
  | 0x839380 | Sv[94] | |
  | 0x508880 | Sv[82] | |
  | 0x717140 | Sv[3] | |
  | 0x5b59d0 | FA base[3] | |
  | 0x8c4df0 | Cl[3] | |

  Each of these contains a `[vtbl+0x308]` call site (0x6df7dc, 0x6a114a, 0x4fa2c8, 0x4fb626, 0x51bc27, 0x8393c8, 0x508eb3, 0x717148, 0x5b59d6 and 0x8c4dfb).
- **Not re-verified, GUESS:**
  - The identity of the object at `[this+0x5f8]` is unidentified.
  - The "pushes 6 in a message handler" readings.
  - What calls those slots on a client.
  - "Cl[290] is probably the client's state sync" is withdrawn, because that slot does not exist.
- **GUESS:** a host-only fix to the "visit 1" bug may not change what a client does. Both sides run the same 0x5b1410 gate.

### 3. RMCReceiveHit

- **Strings (FACT):**

  | String | Address |
  |---|---|
  | `RMCReceiveHit` | 0xb6a610 |
  | `RMCSetDamageDealer` | 0xb5657c |
  | `RMCReceiveCloseCombat` | 0xb38b70 |
  | `RMCRemoteShotActivateApplyDamage` | 0xb38cd0 |
  | `RMCUpdateHitPoints` | 0xb80a34 |
  | `RMCAnnounceFAEscapeVehicleArrived` | 0xb23850 |
  | `RMCAnnounceFAEscape` | 0xb65418 |
  | `RMCHoldEscapeVehicle` | 0xb5ce0c |
  | `RMCResetEscapeVehicle` | 0xb1e230 |
  | `RMCAnnounceFALastPlayerEscaped` | 0xb57be8 |

  The `.data` copies are at 0xd24291 and 0xd242aa. The draft's 0xd26029 was not found. Treat the "RTTI-like name copies" description as unverified.
- **CORRECTED, references to the name:** the `push 0xb6a610` instructions are at 0x4b0fc7, 0x639c8c, 0x71318c and 0x80aa93. The draft listed the operand address, one byte higher. Whether these are the registration and send builders is GUESS. 0x639c8c is confirmed as the sender.
- **Sender 0x639c80 (CORRECTED):** it has 6 arguments (`ret 0x18`) and one caller, 0x807373.
  - It writes four fields with 0x950dd0 (sizes 2, 1, 2 and 2), one value with 0x951020, and then sends with 0x953890.
  - It does not write six fields with 0x950dd0.
  - The payload is {word, byte, word, int16, byte}.
- **Wrapper 0x807220 (FACT):** 5 stack arguments, `ret 0x14`.
  1. It returns doing nothing if `0x905460(sm)` is false or `[sm+0x15d]==0`.
  2. If 0x9425a0(this) is true, it takes the local path. It rebuilds a hit struct, zeroes the float fields, converts the signed 16-bit argument 4 to a float with `fild`, and calls `[[this+0x2a0]+0x698]`.
  3. Otherwise it sends `RMCReceiveHit` through 0x639c80. If the send returns 0, it calls 0x89e080 (an error path, GUESS).
  - Its only direct callers are 0x4b56b1 (inside 0x4b5690) and 0x6821bc. 0x4b5690 calls it with a plain `call`, not a tail call.
- **0x9425a0 (CORRECTED).**
  - If the owner id `[this+0x14]` is 0, it returns false. The draft said true.
  - Otherwise it looks up the local peer id with 0x94bc10. If that lookup yields 0, it returns true. If not, it returns `owner == local`.
- **Dispatcher 0x69f900 (CORRECTED, more branches than the draft said):**
  - It has no direct callers (virtual).
  - If 0x863a60(sm) is false, or `[this+0x821]!=0`, it runs `[vtbl+0x698]` locally.
  - Otherwise it calls `[vtbl+0x3d0]`. If that is true, it runs the local handler, unless 0x86a150 is true and 0x86f0c0 is also true, in which case it does nothing.
  - If `[vtbl+0x3d0]` is false, it reads the shooter at `[hit+0]`.
    - Depending on 0x7aace0 and 0x7de570 checks of the shooter's `[+0x274c]` and of `[this+0x8d8]`, it drops the hit, runs it locally, or sends.
    - The send goes through 0x4b5690 and then 0x807220, with this packet:
      - `[hit+0]` and `[hit+0xc]` compressed through 0x6ece90;
      - bytes `[hit+4]` and `[hit+8]`;
      - two floats `[hit+0x2c]` and `[hit+0x28]` quantised to 16 bits through 0xa8d330 (the first call also takes the byte `[hit+0x30]`).
  - What 0x3d0, 0x86a150, 0x86f0c0 and 0x7de570 mean is not decoded.
- **Where damage is priced: still GUESS, the draft's conclusion is withdrawn.**
  - FACT: the message carries only one 16-bit signed number that becomes a float in the receiver's hit struct. The other floats are zeroed on the local path.
  - Neither "victim's owner prices it" nor "shooter prices it" is established. The 16-bit value could be damage or a force.
  - **GUESS:** the remote handler `[vtbl+0x698]` runs on the machine for which `0x9425a0` is true.
  - **GUESS:** bot ownership. Probably the host, as the notes already assumed.
  - Both `private_match.md` claims, "priced on the shooter's machine" and "priced by the victim's owner", stay unproven.

### Next steps

- Decode the `[hit+0x28]`, `[hit+0x2c]` and `[hit+0x30]` meanings by reading what handler 0x698 does with the struct, to learn what the int16 means.
- Find who calls Heist[86] (0x6df7d0) and what `[this+0x5f8]` is.
- Find how a client receives the escape state, since its slot-195 update does not advance it. Look at what the score object triggers.
- `klh_net_role()` can call 0x863a60 and 0x4b0a40 with `ecx=[0x168e598]`. Call 0x8df480 with `ecx=sm` too.
## 2026-10-18: what the "everybody has this map" gate really tests (kl-merge-e5 worker, static only)

Read-only disassembly of `kl2.exe` (capstone via `tools/kl_exe.py`; nothing run, nothing patched). Tags: **FACT** = bytes read at the address; **GUESS** = inference.

**Question.** The host's start gate (0x6c4cf5..0x6c4d8c) was carried as "content-blind" and nobody had read where its availability bits come from. Would a client whose `Maps\DMxx` build differs, or who lacks the expansion, be refused by the game's own gate, or load silently?

**Answer: the gate is content-blind for six of the nine FA slots, so a mismatched client is NOT refused. Only slots 4, 7, 8 (stock F05, F08, F09) look at the disk, and only for the file's existence, never its contents.**

Evidence:

1. **FACT, the gate (0x6c49a0 state, game type `[sm+0x5c]==4`).** 0x6c4d1f `call 0x746570` maps the menu position to a slot (table pushed at 0x746586..0x7465a4: 0,1,2,3,5,6,4,7,8). 0x6c4d34 calls `[0x168f750]` vtable +0x14 = **0x5e1510** (host's own availability), then for client slots 0..11 (loop to 0xc at 0x6c4d89) `0x7ca830(client, slot)` -> **0x73f270**: `ecx+=0xb8`, `0x431f60` (= `movzx word [ecx+4]; xor 0xdead`), then `test (1<<slot), mask`. If any bit is clear the byte at 0x6c4d3e/0x6c4d83 goes 0 and 0x6c4dd3 resets the countdown `[sm+0x194]`. So the per-client input is a 16-bit mask, xor-obfuscated with 0xdead, in the replicated client dataset (`m_iAvailableLevels`, string 0xb76360).
2. **FACT, who owns `[0x168f750]`.** Writer 0x90ac5e stores the result of constructor `0x717f40`, which stamps vtable **0xbd5494** = `ZDownloadableContentManagerSteam` (RTTI via `kl_exe`). Its vtable slot 5 = 0x5e1510, slot 7 = 0x634b90, slot 9 = 0x816d80, slot 15 = 0x7c5ca0, slot 28 = 0x77adf0.
3. **FACT, slot 7 (0x634b90) is the mask.** Bit i = `byte [mgr+4+i]` for i = 0..8. Slot 5 (0x5e1510) returns `byte [mgr+4+slot]`, or 1 outright if `0x87c980` (`[sm+0x5c]==2`) is true; game type 4 is not 2.
4. **FACT, defaults.** Init 0x8468d0 (called from 0x835ff0, the base constructor) sets bytes +4,+5,+6,+7,+9,+0xa = 1 (slots 0,1,2,3,5,6) and +8,+0xb,+0xc = 0 (slots 4,7,8). Slots 0-3,5,6 (F01..F04, F06, F07) are therefore ALWAYS available on every install, with no file test anywhere I found. The names are built by 0x835ff0 as `Locations/F0n/F0n_Main` at `mgr+0x16+slot*0x40` (strings 0xb75044, 0xb39e28, 0xb326a8, 0xb2c534 ...).
5. **FACT, the only disk test.** Slot 28 (0x77adf0): skipped for Demo/PreviewBuild/LifePreviewBuild (strings 0xb4ee00, 0xb62800, 0xb4e3ec). Otherwise `SteamApps()` (IAT 0xb107c4) vtable +0x1c (BIsDlcInstalled; GUESS on the method name, the +0x1c slot is FACT) with app 0x6d6a: then for slot 4 and slot 7 `0x5432d0(name)` and, if true, `SetAvailable` (slot 9, 0x816d80 sets `byte [mgr+4+idx]=1`). App 0x6d71 gates slot 8 the same way (0x77af28..0x77af56). `0x5432d0` is `CreateFileA("Scenes/%s.zip")` (fmt 0xb2c060, call 0xb10270, OPEN_EXISTING, handle closed): existence only, never size or hash.
6. **FACT, when the mask is pushed.** 0x845700 is a Steam DLC callback handler registered in the manager constructor (0x717f57 `mov edi,0x845700`; its switch is `[event] - 0x6d6a`, 0..7). After updating bytes it calls `0x845640(client+0xb8, mask)` with `mask = [mgr] vtbl+0x1c` at 0x845835 / 0x845894 / 0x84590f (`[sm+0x98]` = local client object). The own client object also gets the mask at creation, 0x8b6626 (inside 0x8b65e0). 0x845640 stores `mask^0xdead` and returns 1 only if it changed.
7. **FACT, what a client then loads.** From the previous notes (0x491fd1, re-verified as unchanged): the scene is `levellist->slot15(D.levelIndex)` of the client's own list, i.e. its own `Scenes/Locations/F0n/F0n_Main.zip`. Nothing between the gate and the load compares content.

**Consequences for the owner's setup.**
- A friend with no expansion and the owner's DM01B in slot F01 (index 0) reports bit 0 set, the host starts, and the friend loads stock Subway while the host loads the grafted map. No dialog. (Matches risk 1 of the 10-18 readiness check; the new part is that the cause is a hard default, not an oversight in a check.)
- Only for stock slots F05, F08, F09 does a client lacking the zip report the bit clear and block the countdown, and only if it owns app 0x6d6a / 0x6d71 (GUESS: an owner of the base game without that DLC never sets those bytes, so those slots are blocked for them anyway; I did not trace what the menu does with an unavailable slot, but 0x6c4e07 shows `Online/MissingContentPackClient` for a client).
- **Cheapest game-native refusal (GUESS that it replicates, not run):** a hook on the client clears `byte [mgr+4+slot]` for the grafted slot when its build fingerprint differs from the lobby's, then calls `0x845640([sm+0x98]+0xb8, 0x634b90(mgr))`. The host's gate then sees the bit clear and holds the countdown, with no new UI. The mask is only re-pushed on DLC callbacks and at client creation (item 6), so the hook has to push it itself. The fingerprint transport (lobby key via `klmm`) is still the unbuilt part.
- Host-only versus every-peer for hook features: this work does not change the earlier finding that the Heist-gated modules are inert in a real FA lobby (role 2/3 uses the Sv/Cl rules classes). It only settles that nothing protects a lobby from mixed builds, so every peer must be given the identical `Maps\DMxx` build by hand.

**Not established (still GUESS/open):** whether the DDL layer really replicates `m_iAvailableLevels` changes made after the lobby forms (netcode.md says the field is replicated; I did not read the DDL send path); what slot is used when the lobby is Quick Match; whether Steam sets 0x6d6a/0x6d71 true for owners of the PC edition at all (the retail PC FA maps F05/F08/F09 are known to be playable, so presumably yes).

## 2026-10-19 - authority, hook sides, what must match (static reading, kl2.exe build 0490; nothing run)

### Findings
1. Authority. The HOST runs everything; clients replicate. Session manager sm=[0x168e598]: net role [sm+0x54] (2 host, 3 client), game type [sm+0x5c], state [sm+0x70].
   - Helpers: 0x863a60 networked (roles 2/3); 0x4b0a40 client; 0x8df480 authority (host true, client false, local type 4 true); 0x9425a0 master of a net object.
   - Squad scripts: ZSquadScript update 0x47e440 skips its loop on a client (call 0x4b0a40 at 0x47e465, jne 0x47e70c). ZSoldier orders (0x760e50) are dropped on a client.
   - Money, containers, doors, escape vehicles are gated by 0x8df480, so loot and escape are host-decided. (Call sites FACT: ZOnlineMoneyContainer 0x419f80, ZOnlineEscVehicleController 0x6d7d20, ZKickDoorMonitor 0x611430, ZOnlineMoneyCtrl, ZOnlineEscVehicleMonitor 0x84d8f0. "Host-decided" is the reading of those message handlers: GUESS. Other door classes not checked.)
   - Crew bots exist only under ZGameRulesHeist (vtable 0xbd3514, Arcade) (carried from klbot.c comments, GUESS). Online rules are ZGameRulesFragileAllianceSv (0xbd2eb4) / Cl (0xbd31e4) (FACT, RTTI); "only Sv issues server commands" is GUESS.
   - Civilians: ZCivilian and ZSoldier slot 17 (0x4f5310 call at 0x4f539c, 0x6ab250 calls at 0x6ac5cc..0x6ac5eb) test networked && game type 2 && client (FACT). So for game type 4 (FA) that branch does nothing; whether FA civilians run on clients: GUESS (not established).
2. Hook modules are inert online. klbot.c klb_read (line 360-364), klfedkit.c (line ~878), klbalance.c klr_arcade (line 414-418) and klbot-based klmove/klescort/klhop require rules vtable == Heist and `[sm+0x5c]==4` and role not 2/3. klcrew_rt.c:258 and klchar.c:302 test only type 4 + the Heist vtable (no role test), so online they rest on the vtable alone. kljoin.c:244 refuses the jump request when kl_online() ([Net] OnlineSafe).
   - NOT inert (see Verify): klslot.c (live ini has [Expansion] Enable=1), klrappel.c (no online guard), klcensor.c (default on; blocked by kl_online() unless [Censor] Online=1), [HUD] Online=1 in the live ini.
   - Arcade-only, host or client: nothing runs online. Per module the sites are those in re/hook_netcode_audit.md.
   - If a module DID run on a host only: orders and the 0x62a900 teleport (b=1) replicate and are fine for clients; plain data writes (klh_data, private vtable copies, import-slot proxies klh_iat) exist only on that PC and desync from peers that lack them (GUESS on visible effect).
   - If it ran on a client only: its writes are overwritten by the host or diverge locally. Do not enable.
   - Included in every build, but NOT all "always on": klsteam.c (stat/achievement proxy, always installed, local only). klmm.c installs nothing unless [Net] PrivateLobby or BuildKey is set (klmm.c:219-224). klnet.c writes nothing unless [Net] Tune=1 (klnet.c:395); Log defaults 0. klslot.c does nothing unless [Expansion] Enable=1, which the live ini HAS. klbuild.c is written but NOT included in klhook.c (include list lines 614-664) and not in build.bat.
3. Must match between players: the map archive the redirect resolves to (live: KLExpansion\Maps\<dir>\Fxx_Main.zip plus .WHD/.WAV/.hti/_LS.* beside it, chosen by klslot.c; NOT Scenes\Locations\Fxx unless no rule applies), KLExpansion\Overlay\Patch01.zip, KLJoin/KLGuns/KLTalk/KLWardrobe.ini, KLHook.ini and dinput8.dll. Scene entity order must be identical (objects are addressed by 16-bit scene references; GUESS on the failure mode).
   - Game checks: none FOUND (absence of evidence, not proof). No hash, CRC or version comparison located. 0x53919c calls the m_szVersion getter 0x57b2d0 and does not use the result (FACT); indirect/vtable callers were not scanned. Steam lobby keys carry no build, version or map name (netcode.md:113). The DDL replicates m_szServerMap and m_szVersion strings; their consumers are unknown.
   - Availability gate (ZDownloadableContentManagerSteam, vtable 0xbd5494, global 0x168f750) is content-blind for F01-F04, F06, F07: a mismatched client silently loads whatever zip it has. Expect a desync or crash, not a refusal.
   - KLHook.ini keys that matter online (defaults in code; LIVE values in brackets): [Expansion] Enable (default 0; live 1, Overlay=1, page-0 [Redirect] F01..F09 = DD01..DD09, so even the stock FA slots load modded overlays), [Net] Log/Tune/PrivateLobby/BuildKey (live: no [Net] section, all off), [HUD] Online (default 0; live 1), [Censor] Online. The rest are inert online but keep both PCs identical anyway.
4. Slot maps. A private lobby picks them like stock ones: the client's level index is the DDL byte at [[sm+0x84]+0x1b0] ^ 0xac (0x467ae0 -> 0x5b1400; klnet.c:304 reads the same), mapped to a scene through each side's own list (host 0x6c536f, client 0x491fd1). The Steam lobby key `Scenario` is a number used for search and the row filter. The name travels only with `-o MPMap` (GUESS, MPMap not re-checked). Nothing in the lobby uses a display name or level id we changed; names are local menu XML/LOC. Only 7 of the 9 hard-coded slots are gate-free (above).

### First two-PC test (no new code)
- Copy to PC2: the same dinput8.dll, KLHook.ini, the four ini files, the whole KLExpansion folder (Maps\<dir> with sidecars, Overlay\Patch01.zip). Never touch KL_PortBackup.
- Compare with `certutil -hashfile <file> MD5` on both PCs for every file above; they must be identical. Reference values (checked 2026-10-19): live dinput8.dll md5 043419cb (mtime Oct 19 01:25, will change on reinstall); Hasta police3 F04_Main.zip md5 43a7c699 (C:\kl_build_1018\hasta_police3\DM11B). NOTE 7cd07d15 is the Vault map build id in re/adopt_list.md:19, not a hook hash; its live F07 file hashes differently as md5 (unresolved scheme).
- Host creates a private lobby on the slot, client joins by invite. Keep [Net] Log on; compare KLHook.log on both sides (lobby create/join lines, level index, scene load). Check entity counts and the first loot pickup on both screens.
- Start with a stock map first to prove the link, then the slot map. With the live ini the "stock" FA map already loads the DDnn overlay on the owner's PC, so PC2 needs the same KLExpansion or the test is not stock.
- Online the page latch is GUESSED to be 0 (the lobby menus show no map page; klslot.c kls_menu_watch, not run), so a Dead Men map (page 2/3 rule) would not load in a lobby unless a page-0 rule points a slot at it. Not run.

### Smallest KLHook additions to make a mismatch visible (proposals, NOT written)
Already written but not built: klbuild.c (lobby build check, design re/private_match_buildcheck.md) and klmm.c BuildKey (klx_fingerprint over the Maps\*\F*_Main.zip central directories; off by default). Prefer reviving those over the list below.
- Hash the loaded slot zip (or its central directory) at level load and log it; send it through klmm.c as a lobby member key and log the peer's value.
- Log the entity count after the .gms load, and the dinput8 build id, to KLHook.log on both sides.
- Put the hook build id in a klmm lobby key (BuildKey exists in [Net]) and show a warning line in the log when the peer's differs.
- Log the role at 0x8df480 / [sm+0x54] when a round starts, so the logs say who was host.

### Verify (2026-10-19, second reader; static only, kl2.exe via tools/kl_exe.py + capstone, klhook sources, read-only look at the live Dog Days ini and hashes)
Confirmed (FACT, bytes read):
- Helpers: 0x8df480 (role table 0x8df4a8: roles 0,1 -> type==4; role 2 -> true; role 3 -> false), 0x4b0a40 (role==3), 0x863a60 (roles 2,3), 0x87c980 (type==2).
- 0x47e440 (ZSquadScript slot 25) skips on client at 0x47e465; 0x760e50 (ZSoldier slot 79) returns when networked && client (0x760e5f..0x760e75 -> 0x760f65).
- 0x8df480 is called from 239 sites incl. ZOnlineMoneyContainer 0x419f80, ZOnlineEscVehicleController 0x6d7d20, ZKickDoorMonitor 0x611430.
- RTTI vtables: Heist 0xbd3514, FA Sv 0xbd2eb4, Cl 0xbd31e4, DLC manager Steam 0xbd5494 (slots 5/7/9/28 = 0x5e1510/0x634b90/0x816d80/0x77adf0). Defaults at 0x8468d0 make slots 0-3,5,6 (F01-F04,F06,F07) available; slot names F01..F09 in order at 0x835ff0.
- Host and client level index loads: 0x6c536f and 0x491fd1 call vtable +0x3c of [0x168f750] with the index from 0x467ae0 (xor 0xac byte in the DDL object).
- kljoin.c:244, klhook.c include list (614-664) without klbuild.c, no other reference to klbuild.c in klhook/ or build.bat.
- Hash 43a7c699 = md5 of C:\kl_build_1018\hasta_police3\DM11B\F04_Main.zip.
Changed:
- Hash "live hook 7cd07d15" was wrong: it is the Vault map build id (re/adopt_list.md:19). Live dinput8.dll md5 starts 043419cb.
- klmm.c, klnet.c, klslot.c are NOT always on: off by default (klmm.c:223, klnet.c:395, klslot.c header). The LIVE ini has [Expansion] Enable=1, Overlay=1, [Redirect] F01..F09 = DD01..DD09 and [HUD] Online=1, no [Net] section. So klslot and the HUD online parts are active on the owner's PC.
- klcrew_rt.c:258 and klchar.c:302 have no role 2/3 test (vtable test only). klrappel.c has no online guard (hook_netcode_audit.md). klcensor is on by default.
- "Slot zip" is KLExpansion\Maps\<dir>\, not Scenes\Locations\Fxx (live Maps\DD01 F01_Main.zip md5 403d78e7 vs Scenes F01 644fe120).
- The three claimed hook-addition ideas partly exist: klmm.c BuildKey (zip central-directory fingerprint) and klbuild.c (design in re/private_match_buildcheck.md). Level index source corrected (DDL byte, not the Steam key). Earlier line about klslot.c:280 corrected.
- "Game checks nothing" and "0x53919c discards m_szVersion" reworded: the getter result is unused there (FACT) but nothing proves no other comparison exists.
Downgraded to GUESS: crew bots Heist-only; only Sv issues commands; host-decided loot/doors/escape (call sites FACT, meaning inferred); FA civilians on clients; desync vs crash on mismatch; -o MPMap as the only name path; page latch 0 online.
Could not check: 0x53919c is mid-function (enclosing function start not identified); indirect callers of 0x57b2d0; whether anything else writes DLC manager bytes +4..+0xc; Net-Z/DDL version stamps (exe-level, identical for identical kl2.exe: GUESS); nothing run on two PCs.

## 2026-10-19: the open questions (static reading, kl2.exe build 0490; nothing run)

Two readers answered; a third pass re-disassembled the cited addresses (kl_exe + capstone, read-only). FACT = bytes seen by that pass; GUESS = inferred or taken from a reader without re-reading. Of the six items under "Still open after this plan", Q1-Q5 below are answered in part; the CEG check versus a patched exe was not touched.

### Q1. Who simulates a ZFFActor online
- Answer (GUESS, probable): the peer that OWNS the actor's DDL_ZFFActor net object runs it; every other peer follows replicated, extrapolated state. AI decisions are host-only, so for AI actors the owner is almost certainly the host. Not proven.
- Evidence, FACT: ZFFActor::Update (0x40ef60) calls 0x899c40([actor+0x8d8]) at 0x40f0ea. That ends in 0x8efe90, which returns at once if [actor+0x2a0]==0 (0x8efe96..0x8efe9d) or if 0x9425a0 says this peer is master (0x8efea3..0x8efeaa). Otherwise it needs byte [0xce7eeb]!=0 (0x8efeb0) and then steers the actor (the steering body 0x70f660 and the session state 0x19 test were NOT re-read: GUESS). 0x9425a0: owner [obj+0x14]==0 -> false; local id from 0x94bc10 equal 0 -> true; else owner compared to local id.
- Squad scripts (0x47e440) and ZSoldier orders (0x760e50) skip on a client: FACT (earlier verify).
- Still open: the site that creates and publishes the actor net object; the callers of 0x4fe5e0 (0x466f22, 0x5a8b6b, 0x6ca1c2); whether a client owns the net object of its OWN ZFFPlayer.
- Test meaning: bot, klmove, klhop and klescort steer actors through orders on the host. The modules are inert online anyway (Heist-vtable and role guards, see the previous section), so the first online run is expected to show NO bots in an FA lobby; that is not a bug. A client must never run actor-steering code: 0x8efe90 would overwrite it with the extrapolated host state.

### Q2. Id space of the wire references
- Answer (GUESS): the 16-bit scene refs very probably use the run-time loader SLOT index (+1), not the REF label (record +0x30). No encoder or decoder site was shown to do it.
- Evidence, FACT: 0x6ece90 loads [0xe0ff90] and calls 0x86ca10. Correction to reader 1: 0x86ca10 reads the field [obj+4] of the object (not the pointer itself; null object or null field gives 0), subtracts the pool base [pool+0xc], divides by the page size [pool+4], reads a signed 16-bit page number from the table [pool+0x10] (negative gives 0), and returns page*[pool+8]+rem+1. So it is slot+1 (the file's other notes say slot+2: the offset convention on the wire is a GUESS).
- Still open: whether any net writer (m_iGeomRef, m_iFFWeaponRef dataset writers) is fed by 0x6ece90. Not traced.
- Test meaning: fits "identical build of a grafted map". Entity order and the cluster/pool table must match, so both PCs need byte-identical map zips; one entity added or removed shifts every later ref. Compare md5 of the zips first. A mismatch is expected to show as wrong weapons or geometry or a crash, not a refusal (GUESS).

### Q3. Who applies a hit (RMCReceiveHit)
- Answer: damage is applied on the peer that OWNS the victim ([victim+0x14] equals the local station id); a shooter applies directly if the victim is local to them, otherwise sends the RMC. No host arbitration step was found (absence of evidence).
- Evidence, FACT: apply-or-send wrappers 0x807220 (ZFFActor) and 0x891490 (ZFFPlayer). Correction to reader 2: each first calls 0x905460 on the session manager (0x807252, 0x8914c2; it is a jump-table state test over session states 0x17 and up, table not decoded) and leaves at once when that fails, then calls 0x9425a0 on the victim (0x807274, 0x8914e4). Master path ends in a vtable call (call eax at 0x80730c, 0x89158f); the other path reaches the senders 0x639c80 (0x807373) and 0x713180 (0x891626). The receive stubs 0x682140 / 0x59f140 and the dispatchers 0x618a70 / 0x658b60 are from reader 2, NOT re-read (GUESS).
- Still open: ownership assignment (is a client's own character owned by that client?).
- Test meaning: damage tweaks (hit pricing, armour) must run where the victim is owned: for AI actors probably the host, for players probably each player's own PC (GUESS). Test both bot-shot-by-player and player-shot-by-bot.

### Q4. FragileAlliance rules slot 194 (SetState) on a client
- Answer (GUESS, reader 2, not re-read): clients receive it. Escape state is replicated through the score object (score+0x38c, xor 0xac; rules+0x2c holds the score pointer) and three RMC receive stubs (0x563b10, 0x7dc000, 0x4d9ce0) apply on the receiver. The decision is host-side (Sv tick 0x727610, Sv wrapper 0x51e390); the Cl tick is 0x7a30c0. Slot 194 = 0x5b1410 in base vtable 0xbd2b9c.
- Still open: that no client code writes score+0x38c.
- Test meaning: escape logic of a grafted map (vehicle, rappel exit) must be satisfied on the host; a client only mirrors the result. Test escaping as the CLIENT: it should get the result when the host's zone fires.

### Q5. Join code 3 and host migration
- Join code 3, FACT (re-checked): the join result handler is 0x8309d0 (slot 98, offset 0x188). It is called from the state function near 0x539060: [esi+0x58] is loaded at 0x5390f2 and the call is `call edx` at 0x539118. The jump table at 0x830fc8 is indexed by code-1: its first entry is 0x830d5e (code 1, ServerFull string 0xb7e944) and entry 3 is 0x830c32, which pushes "Online/JoinSessionFailedNotInGame" (0xb5a524, at 0x830c40). So code 3 = the host says the session is not in game (the joiner arrived while no match was running or loading).
- Writer of [esi+0x58]: NOT FOUND. GUESS: copied from Net-Z's join result.
- Host migration: FACT, seen: MigrateStation at 0xbdda37 (Net-Z library name, linked in); "HostDisconnect" is matched at 0x6455bb and sets [esi+0x88]=9 at 0x6455cd; the strings FAStatus_HostDisconnect (0xb1b120) and /Menu/ErrorMessages/Online/HostDisconnected (0xb61908) exist. The other Net-Z names and the UI call sites are from reader 2 (GUESS). Answer: the host leaving ends the match; no hand-over was found. Whether Net-Z migration is enabled at session creation: NOT FOUND (GUESS: off).
- Test meaning: if the host PC crashes (likely in early graft tests) the client sees "host disconnected"; that is not a client bug. A NotInGame refusal means timing (join after the round started or before it loaded), not a map mismatch.

### What this means for the first two-PC test (AI bots, klmove, rappel, HUD)
1. Bots, klmove, klescort, klhop: not expected to run online (guards). Do not count absent bots as a failure; do not enable on the client.
2. Rappel (klrappel.c has no online guard): enable on the host only for the first run; on a client it would move a player against replicated state (GUESS). Watch the second PC's log for rappel lines.
3. HUD ([HUD] Online=1): local drawing; keep identical KLHook.ini and dinput8.dll on both PCs to remove variables.
4. Map: byte-identical zip on both PCs (Q2); stock slot first.
5. Escape and loot: host-decided (Q4); test the client escaping.
6. Log on both sides ([Net] Log=1) and note which PC hosted; a host disconnect ends the round (Q5).
7. Still unknown: actor net-object ownership (Q1, Q3) and the CEG checks versus a patched exe.

## 2026-10-19: where the wire ids come from (static)
Second reader re-checked a first report against kl2.exe build 0490 (capstone, read only, nothing run). Result: the 16-bit object id is built from the entity's slot index in the engine's slot pool. It is not the REF label (record +0x30). This replaces the GUESS in Q2 for the encoder and decoder; the producer of the slot tags is still open.

### Pool layout (CHECKED, corrects the first report)
- The slot manager is the global `[0xe0ff90]`. It is set at 0x4c2fdc. Its pool object is at `[mgr+0xc]`.
- The pool constructor is 0x89bc80(this, slotSize, count). Fields: `+4` = slot size (the loader passes 0x80), `+8` = capacity in SLOTS (not a page size), `+0xc` = memory block (count * slotSize), `+0x10` = a table of `count` signed 16-bit words, all set to -1 at start (0x89bce0 loop).
- The capacity is the memory size >> 7 (0x541b12, 0x541b1a). The loader sizes it with a floor of 0x340000 bytes (0x8ad907..0x8ad914), so at least 26,624 slots.
- So the table is indexed by PHYSICAL slot index. Its word is a per-slot tag (generation), not a page number taken from the address. 0x7f37f0 and 0x7f3838 treat a negative word as a FREE slot (they build the free list from them).
- The first report said "page = off / [pool+4], rem = off % [pool+4]". That is wrong. In 0x86ca10 the quotient (the slot index) is used and the remainder is thrown away.

### Pointer to id (CHECKED)
- 0x6ece90 is `mov ecx,[0xe0ff90]; call 0x86ca10`, about 900 callers, so it is the generic "entity to ref" call and is not net-specific.
- 0x86ca10 returns 0 for a null object or a null `[obj+4]`. Else `idx = ([obj+4] - [pool+0xc]) / [pool+4]`. It reads `tag = word [pool+0x10 + idx*2]` (0x86ca2d). A negative tag gives 0 (0x86ca45). Else the result is `tag*[pool+8] + idx + 1` (0x86ca39..0x86ca3f).
- 0x902570 is the same arithmetic from a raw slot pointer. Neither function nor 0x40a880 or 0x796ff0 reads record +0x30. CHECKED: the REF label is not on this path.
- For a slot with tag 0 the id is exactly `slot index + 1`. GUESS: loaded level entities have tag 0. The code that writes tags >= 0 into the table was NOT found (the pool constructor only writes -1; the loader at 0x8adb59 bumps a pointer by 0x80 and never touches the table).

### Id to object (CHECKED)
- 0x8ccde0 is `mov ecx,[0xe0ff90]; call 0x796ff0`. 0x796ff0 calls 0x40a880 and returns `[slot+0x60]`, the entity object in the slot (0 if the slot is 0).
- 0x40a880, static branch (bit 0x40000000 clear): `n = id-1`, `q = n / [pool+8]`, `r = n % [pool+8]`. It requires `word [pool+0x10 + r*2] == q` and returns `[pool+0xc] + r*[pool+4]`. Otherwise 0. So the check is on the tag, and a stale id for a slot with another tag gives null, not another entity.
- Dynamic branch (bit 0x40000000 set): `[pool+0xc] + ((id>>7)&0x7fffff)*[pool+4]`, no tag check. A 16-bit field cannot hold bit 0x40000000. GUESS: run-time spawned objects use another path or a wider field. Not traced.
- Other direction, CHECKED: 0x883840.. computes a slot from the word at `[obj+0x5e]` as `base + (w<<7) - 0x80`, so that word is a 1-based slot number and the slot size is 0x80.

### Loader link (CHECKED)
- Loader 0x8ad7c0 at 0x8adb59..0x8adb71: `cat = 0x829b10(record)`, `idx = cat + 8*byte[rec+0x35]`, `slot = [edi+idx*4]`, then `[edi+idx*4] = slot+0x80`. This is the bump allocation from the parent group's block, as in `kl_gms.rebuild_clusters`.
- 0x883770 (call at 0x8adbb5, slot in esi) creates the entity object IN that slot: type id & 0xf, hash chain at 0x8837f7..0x883812, then `call [eax+0x40]`. With a null slot it allocates a 0x80 heap object (0x8837ac), the dynamic case.
- Whether the loader's block lies inside the pool block `[pool+0xc]` is consistent with the decoder (it only returns addresses inside that block) but the block hand-out code was not read. GUESS.

### Net side
- CHECKED: the receive stub 0x682140 reads a 2-byte field (0x950f20 at 0x682160), a 1-byte field, two more 2-byte fields, one more field (0x951230), and calls 0x807220 with five values (0x6821bc).
- CHECKED: 0x807220 first calls 0x9425a0 (is the object owned by the local station: `[obj+0x14]` compared with the result of 0x94bc10). If yes, it turns two of its word arguments into objects with 0x8ccde0 (0x807292, 0x8072a4) and calls vtable slot 0x698 of `[this+0x2a0]`. If no, it calls the sender 0x639c80 (call at 0x807373). So 16-bit wire fields ARE resolved with the slot decoder above. CHECKED. Ownership is a separate field: the id only picks the object.
- CHECKED: the hit send 0x69f900 passes `0x6ece90([hit+0])` and `0x6ece90([hit+0xc])` to 0x4b5690 (0x69f9cf, 0x69f9e1, 0x69f9ee), and 0x4b5690 forwards five arguments to 0x807220 (0x4b56b1).
- CHECKED: 0x639c80 writes its first field with 0x950dd0(src, 2, 1), and 0x950dd0 ends in a memcpy of size*count bytes (0x95eb00), so 2 bytes go on the wire per such field.
- NOT CONFIRMED (downgraded to GUESS): that the 2 bytes are the low 16 bits of the 32-bit result of 0x6ece90, and which 639c80 argument is which 807220 argument. The pointer arguments pushed at 0x807353..0x807370 are stack locals whose frame offsets I could not resolve by hand. The idea (little-endian low word of the ref) is the natural reading, not proven.
- GUESS: the DDL dataset writers (m_iGeomRef, m_iFFWeaponRef, m_iRef) use 0x6ece90 too. Not traced.

### Consequence for two PCs
- CHECKED: an id is `tag*capacity + slot index + 1`. For tag 0 it is the slot index + 1, so both PCs need the same slot assignment: same .gms entity order, same cluster table (pool counts), same category and priority for each entity. One entity added to or removed from a pool shifts every later slot in it.
- CHECKED: the static decoder rejects an id whose tag does not match (returns null), so some mismatches give a null object, not a different entity. The first report said a stale id "still resolves to some entity"; that holds only when the tag matches, which for tag 0 means any in-range index. Out-of-range or free slots give null.
- GUESS: the capacity also enters ids for tag > 0, and it depends on the memory size the loader computes (floor 0x340000). Different map data could change it.
- GUESS (rule, unchanged): use a byte-identical map zip on both PCs. Entity order alone might be enough for the ids, but .prp values, .buf, .oct and .HVK also feed the simulation, and no version or hash check was found. Compare the md5 of the zip first. If a variant must be tested, compare the entity order and cluster table first.
- Not done: the writer of the slot tags (hence the exact tag of loaded entities), the DDL dataset writers, the producer of dynamic ids, and the exact 639c80 argument mapping.

## 2026-10-19: slot tags and the send path (static)
Re-checked against kl2.exe disassembly (python + capstone, read only). This closes three of the "Not done" items above. Addresses are VAs.

### Who writes the slot tags (CHECKED)
- Pool ctor 0x89bc80(this=pool, size, count): `[pool+4]=max(size,4)`, `[pool+8]=count`. The tag table at `[pool+0x10]` gets 0xFFFF in every word (loop 0x89bce0). It then calls 0x7f37f0.
- 0x7f37f0 links every slot whose tag word is negative (`cmp word [edx],0 / jl`) into a free list. It scans from the top and prepends, so the head (`pool+0x14`) is the lowest index and the list ascends. The tail is `pool+0x18`. It sets the "built" byte `[pool+0]=1` at 0x7f3867.
- Allocator 0x7a39f0(ecx=pool) builds the list first if `[pool]==0`, then pops the head, derives `idx=(head-[pool+0xc])/[pool+4]` and does `not word [tags+idx*2]` (0x7a3a12..0x7a3a18). A fresh slot goes from -1 to 0. An empty list returns 0. Wrappers: 0x687080 -> 0x88cc30 (`ecx=[ecx+0xc]`) -> 0x7a39f0. 0x7196b0 also calls it.
- Free function 0x8861a0(ecx=pool, slot): `not dx / dec dx` (0x8861bc..0x8861c1), so tag t becomes -t-2 (negative, free). The slot is appended at the TAIL (0x8861d5..0x8861df). The next allocation does `not` again and gives t+1. So each free+alloc cycle adds exactly 1 to the tag.
- FIFO is CHECKED: allocation takes the head, free appends at the tail, so a freed slot is reused only after the never-used slots are gone.
- Level loading uses the allocator, which corrects the earlier note "the loader never touches the table". Loader 0x8ad7c0: `0x8ada48` sums the 24 per-category counts into esi. `0x8ada5a: push 0x80 / call 0x687080` takes the first slot (null gives int3 at 0x8ada8e). `0x8adaa0` repeats the call esi-1 more times. `0x8adad8` then gives each category a run of `count<<7` bytes starting at the first slot (`[edi+ecx*4]=esi; esi+=count<<7`).
- On a fresh pool a loaded entity therefore has tag 0 and wire id = slot index + 1. CHECKED by arithmetic.
- GUESS: the 0x80-byte blocks are contiguous because the free list is pristine and ascending. Nothing was traced that allocates between pool creation and the first level load.
- Pool creation: the pool exists once. The loader tests `cmp [ebx+8],0` (0x8ad931) and only then builds the manager with 0x541ae0. 0x541ae0 sets `[this+8]=arg1>>7` and calls 0x4c2eb0, which builds the pool with count `[this+8]` (0x4c2f01) and stores it in `[0xe0ff90]` (0x4c2fdc).
- Capacity (CHECKED, new): arg1 is `esi=(value from the vcall at 0x8ad860)<<7`, floored to 0x340000 (0x8ad8f7). So `cap = max(that value, 0x340000>>7=26624)`. GUESS: the vcall value is the entity or slot count of the level. cap is set by the FIRST level loaded in the session and is not recomputed while the manager survives (GUESS that it survives level changes; the `[ebx+8]` test suggests it does).
- So `id = tag*cap + idx + 1` with cap >= 26624 and cap depends on the first map. For tag 0 the cap does not enter the id, but the decoder at 0x40a880 still needs `id-1 < cap`.

### 16-bit truncation (corrected)
- The wire carries 16 bits (see below). With cap = 26624, tag 0 and tag 1 always fit, tag 2 fits only for idx+1 <= 12287, tag 3 and up never fit. With a larger cap the limit comes earlier, and if cap > 65535 even tag 0 can overflow.
- Correction to the first pass: a truncated id does NOT always decode to null. The decoder gets `low16(id)`, computes `q=(low16-1)/cap` and `r=(low16-1)%cap`, and accepts it if the tag of slot r equals q. A truncated id can therefore resolve to a DIFFERENT live entity whose tag happens to match. CHECKED for the decoder arithmetic (0x40a880: `div`, `cmp word [tags+r*2],ax`). GUESS that this ever happens in play. It needs a slot reused 2+ times.
- Same for two PCs with different slot assignment at tag 0: the id resolves to another entity, not null, whenever that slot holds a live tag-0 entity. Null only comes from a tag mismatch or an out-of-range index. So the earlier line "a mismatch gives a null object, not another entity" holds only for stale tags, not for a different load order.

### Argument mapping, hit send to the wire (CHECKED)
- Hit send 0x69f900 (path at 0x69f9a7..0x69f9ee) pushes 10 values to 0x4b5690 (cdecl, `add esp,0x28`). 0x6ece90 takes the object in ECX (it does `push ecx; call 0x86ca10`). In push order: byte `[hit+0x30]`, word ftol(`[hit+0x2c]`), word ftol(`[hit+0x28]`), `&[hit+0x1c]`, `&[hit+0x10]`, then `id_B=0x6ece90([hit+0xc])`, byte `[hit+8]`, byte `[hit+4]`, then `id_A=0x6ece90([hit+0])`, then `this=[0x69f900's this +0x8d8]`.
- 0x4b5690 reshuffles (0x4b5698..0x4b56b1) and calls 0x807220 with: arg1 = id_A (`[hit+0]`), arg2 = byte `[hit+8]`, arg3 = id_B (`[hit+0xc]`), arg4 = word `ftol[hit+0x28]`, arg5 = byte `[hit+0x30]`. Worked out from the stack offsets of both functions; arg2 is the byte at `[hit+8]` and the byte at `[hit+4]` is not forwarded by this wrapper.
- 0x807220 frame (CHECKED): after the prologue S=esp, arg1=S+0x110, arg2=S+0x114, arg3=S+0x118, arg4=S+0x11c, arg5=S+0x120. Local path: arg1 and arg3 go to 0x8ccde0 as `movzx word` (0x807281, 0x807297), arg4 is `movsx word` (0x8072a9), arg5 and arg2 are bytes. Types are (word id, byte, word id, sword, byte).
- Remote path (0x807344..0x807373): after 0x949f20 (ret 8) esp is back at S. The pushes are &arg5, &arg4, &arg3, &arg2, &arg1, then the message object at S+0x40. The last push is the first parameter, so `639c80(this=esi, p1=msg, p2=&arg1, p3=&arg2, p4=&arg3, p5=&arg4, p6=&arg5)`, `ret 0x18`.
- 0x639c80 stack (CHECKED, this resolves the earlier "NOT RESOLVED"): the bookkeeping was off because 0x93f860 is `ret 4` and 0x94a090 is `ret 8`. With those, esp at 0x639cb1 is E-20 and `[esp+0x18]` is p1, so `edi=p1=msg`. At 0x639ccd esp is E-12, so `[esp+0x14..0x24]` are p2..p6. The function epilogue (`pop edi/esi/ecx; ret 0x18` from E-12) agrees.
- Field order on the wire (0x639cd1..0x639d16): `950dd0(p2, size 2)`, `950dd0(p3, size 1)`, `950dd0(p4, size 2)`, `950dd0(p5, size 2)`, `951020(p6)` = one byte (`cmp byte [p6],0; setne`). So the wire has (id_A 2 bytes, arg2 1 byte, id_B 2 bytes, arg4 2 bytes, arg5 1 byte). Matches the receive stub order 2,1,2,2,1.
- 0x950dd0 does `95eb00(stream, src_pointer, size*count, -1)`, which appends a memcpy from the SOURCE POINTER (0x95eb00 -> 0xa8d31e). The sources are pointers to the 32-bit stack slots, so little-endian x86 puts the LOW 16 bits of the id on the wire. CHECKED. Wire id = `low16(0x6ece90(obj))`, with id1 = the object at `[hit+0]` and id2 = the object at `[hit+0xc]`. What those two objects are (shooter, victim, weapon) was not identified: GUESS.

### Dynamic id, bit 0x40000000 (still not found)
- Consumer CHECKED again: 0x40a880 with bit 30 set returns `[pool+0xc] + ((id>>7)&0x7fffff)*[pool+4]`, no tag check. With slot size 0x80 this is `0x40000000 | byte offset of the slot in the block`, so the low 7 bits are free. The slot size is 0x80 because 0x4c2f01 passes it to the ctor (CHECKED).
- Producer: not found (not re-scanned; the first report's scan stands). The 0x6ece90 / 0x902570 encoder never sets bit 30 (CHECKED above: both return `tag*cap+idx+1` or 0). A 16-bit field cannot hold bit 30, so such ids are either never sent on this path or are cut to a plain 16-bit value. GUESS.

### What this means (updated)
- For the first load after a fresh start with a byte-identical map zip, loaded entities get tag 0 and equal ids on both PCs (CHECKED arithmetic, GUESS on contiguity).
- A second map load in the same session reuses freed slots at tag 1, in FIFO order after the unused ones. cap stays that of the first load (GUESS). Start both PCs fresh for each test and load the same map first.
- Spawned objects that reuse slots change tag. After 2 reuse cycles the 16-bit wire id can be wrong or alias another entity.

## 2026-10-19: pool lifetime and 16-bit overflow (static)
Static only (python + capstone on kl2.exe, plus kl_gms on the stock zips). Nothing was run. Re-checked by a second reader; the marks below are the second reader's.

### Pool size (cap)
- CHECKED: loader 0x8ad7c0 calls DB vtable slot 10 at 0x8ad860 (`mov edx,[edx+0x28]; call edx`). The object is a ZEngineDataBase (RTTI of vtable 0xb8fa04). Slot 10 is 0x545e50, `ret 0x10`.
- CHECKED: out1 becomes `esi=out1<<7` (0x8ad8de), floored at 0x340000 (0x8ad8f7) and passed to the manager 0x541ae0. So `cap = max(out1, 26624)` slots. The .gms +0x1c heap budget is a different value.
- CHECKED: out1 = (1 if `[db+0x8c]==0`) + sum of the .gms class-table counts (u32 at header +0x10 is an offset; there a u32 n, then n x {type, count, count2}) + 0xf0 + 0xea6, plus a path term. Path term: scene path contains "_Main" (0xb89a6c) and then "F0" (0xb38154) or "F10" (0xb61de8) gives +0x5dc; "m05_YOU_WILL_NEVER_FIND_ME" (0xb45710) gives +0x8fc instead; neither gives 0. Lookup 0x7472b0 is a substring search (CHECKED); that its haystack `[[0xdd2640]+0x2b0]` is the scene path is a GUESS; case handling not checked.
- CHECKED on the stock zips (re-computed): F03 27014, F04 27505, F06 27539, F08 29145, L01 39382, L10 48694 (L maps get no +0x5dc). F01, F02, F05, F07, F09, L00 sit under the floor, so 26624.
- CHECKED correction to the report: the entity count N equals the sum of the CLUSTER-table counts (the 24 per-category dwords per block at gms +0x14), e.g. F01 15871, L10 42915. The CLASS-table sum used for cap is about 1k to 2.8k larger than N (F01 18615).
- GUESS: the `+1` term ([db+0x8c]==0 at the first load). It moves cap by one only.
- Expansion rows (DM01 .. DM09, T01 and so on, cap 26624 to 36444) were NOT re-checked by the second reader; they come from the first report.

### Pool lifetime
- CHECKED: the manager is built only when `[db+8]==0` (0x8ad931). Two code paths destroy it and zero `[db+8]`: DB vtable slot 11 = 0x4623e0 (0x46240b, it also frees `[db+0x8c]`), and the DB destructor 0x82e060 (0x82e10a..119). The manager destructor 0x861640 clears `[0xe0ff90]` (0x86166f); 0x4c2fdc sets it again on build.
- CHECKED: nothing calls 0x4623e0 directly, and its only data reference is the vtable slot at 0xb8fa30. The caller would be an indirect `call [reg+0x2c]`; there are 220 such sites and none could be tied to this object.
- GUESS: the pool is rebuilt at each level change (slot 11 called between scenes). Open. A live log of `[[0xe0ff90]+0xc]+8` at each level change would settle it.
- GUESS: if the pool survives levels, cap comes from the first map of the session.

### Overflow of the 16-bit wire id
- CHECKED: id = tag*cap + idx + 1; tag-1 ids pass 65535 when idx > 65534-cap; tag-2 when idx > 65534-2*cap. cap 26624: tag 1 above idx 38910, tag 2 above 12286. cap 29445: 36089. cap 34948: 30586. cap 36444: 29090. L10 (cap 48694): tag 1 above 16840.
- CHECKED (first report, spot-checked): no stock or expansion map has idx above 65535; the largest FA-slot map is DM05A with N=28169, below its own tag-1 limit 29090. Tag-0 ids never wrap.
- CHECKED: free slots are used in ascending order. Spare tag-0 slots are cap-N: 10753 for F01, 8275 for DM05A. A tag-1 slot appears only after those are used up, so overflow is a late-round risk with very many spawns, not a start-of-round risk.
- Tag 2 and up wrap for most idx values. Only a slot reused twice gets there (needs a long match).
- GUESS: a PC that kept a larger or smaller pool from an earlier map gets a different cap. Tag-0 ids still match; ids with tag > 0 do not.

### Bit-30 ids (0x40000000)
- CHECKED: producers at 0x882d52..61 and 0x4f7349..58 do `field&~7, +0x70, |0x40000000, call 0x40a880`, then store the pointer back with the low 3 flag bits. These are load-time style pointer fix-ups of stored fields (the callers were not traced: GUESS).
- CHECKED: decoder 0x40a880 turns bit 30 into `base + ((id>>7)&0x7fffff)*slotsize` with no tag check.
- CHECKED earlier (not redone): encoders 0x86ca10 and 0x902570 never set bit 30, so wire ids do not carry it.
- Other `or ...,0x40000000` sites are flag ORs on object fields (not re-read).

### Practical rule for players
- Both PCs start the session on the same map zip, same build. Do not rely on a second map load in one session until the pool lifetime is settled. Overflow is not a risk at the start of a round.

## 2026-10-19: which ADOPT changes the slot order
- ONLINE (2026-10-19 08:40, tools/kl_netcheck.py, live map vs each ADOPT zip): only ADOPT 5 (Hasta police4 a9ee0ebe) changes the map's slot order (from entity 20014). ADOPT 1 (3a186c93), 2 (Last Call 5b0a025b), 4 (Hot Coffee 21c6ed49) and 6 (Park 3386b972) keep it. So for a private match both PCs need the same Hasta state if ADOPT 5 is used; for the others a same slot order is necessary but not sufficient (the .prp etc. still differ, effect UNKNOWN): safest is that both PCs install the same ADOPTs.

## 2026-10-19 23:50: pool lifetime, static pass 2 (workflow wfg5gjc7i, read only): still UNKNOWN
- Confirmed: only three code sites write [db+8]: the build at 0x8ad96c (guarded by 0x8ad931), DB vtable (0xb8fa04) slot 11 0x4623e0
  (virtual delete + zero at 0x46240b) and the DB destructor 0x82e060. Tags are set to 0xFFFF only by pool ctor 0x89bc80 (via 0x4c2eb0,
  manager in global 0xe0ff90, destroyed by 0x861640); alloc 0x7a39f0 / free 0x8861a0 touch one tag each.
- The scene load path (DB slot 8 0x820300 -> loader 0x8ad7c0 at 0x820b6c) neither frees nor rebuilds the pool.
- The open link: DB slot 31 0x41c360 is a heavy per-scene teardown that ends by calling slot 11 (0x41c476), so it CLEARS the pool; it is
  reached from DB slot 23 0x8d70c0 (0x8d710c), which ZSysInterface (vtable 0xb8f67c) slots 16 0x4f8260 / 9 0x5c36a0 call. Slot 16 sets
  [sys+0x1348]=1 and the per-frame update 0x583fb0 then re-inits the engine (0x6ee140). Whether slot 16/9/23 runs at a map change is not
  shown: all callers are virtual and no level-change caller was found (absence of a found caller, not proof).
- Two tracers said 'survives level change'; the verifier refuted that as unproven (and corrected one tracer: [sys+0x1348] writers are
  0x4f82b8, 0x583fff, 0x68fc15, 0x68fc50, 0x494f68, 0x6c189b).
- So the rule stays: both PCs start the session on the same map zip and build. The opt-in PoolLog patch (re/klnet_poollog.patch) settles it
  live; a cheaper live probe would be to log [0xe0ff90] (or [db+8]) before and after one map change.

## 2026-10-20 01:00: pool lifetime, static pass 3 (workflow w7af8b3iv, read only): still UNKNOWN; static search stopped
- CONFIRMED: the sys interface is [0xdd2640]; the DB is [[0xdd2640]+0xac] (SetDatabase 0x4bd7b0, sys slot 27, deletes the old DB first).
  Of the [+0x1348] writers only 0x4f82b8 (set, sys slot 16) and 0x583fff (clear, slot 47) are on the sys object; 0x6ee140 (full re-init,
  new DB = new pool) has one caller, 0x584014, behind that flag.
- Scene-change request: 0x6d36b0 reads DefaultSceneChangeName, sets [DB+0xb8]=1 (0x6d3984), then DB slot 29 (0x6d39e0) or session
  manager (vtable 0xbd1ebc) slot 26 0x74c080 with state 0x28 / 0x1f. Those state-entry handlers (0x74c43d, 0x74c418 -> 0x89fa20) call no
  DB slot 8/11/23/31/33 and no sys slot 16. 0x6bcc15 resets [DB+0xb8]/[DB+0xbc] and tears down session objects without clearing the pool.
- Every candidate (DB slots 8, 11, 23, 31, 33; sys slots 9, 16) is reached only by virtual calls; no map-change caller was found
  (absence, not proof). Not covered: the dispatcher that consumes [DB+0xb8], DB slot 29 handler 0x640640, MPMap / round-end 0x6c5338,
  0x6c9f06, 0x89fa5d.
- Next step is live, not static: log [0xe0ff90] and [db+8] before and after one map change (PoolLog, re/klnet_poollog.patch, owner's OK).

