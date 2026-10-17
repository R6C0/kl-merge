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
