# Private match: how the host's expansion-map choice reaches every joiner (design only)

kl-merge research, 2026-10-18. Static reading of the repo. Nothing was built, run or launched; no code was changed; the game folder
was not touched. Stage 4 (online) is NOT OK'd by the owner: every item below waits for that.
Tags: **FACT** = read in the file:line cited (or carried from a doc named). **GUESS** = not proven. **TO FIND** = a kl2.exe address
still to be found. Line numbers are into `klhook/` as of commit 900e79a2.

## 1. The problem

* The game replicates a SLOT INDEX (0..8 = F01..F09, level index byte `[D+0x1b0]^0xac`), never a map name. Host `0x6c5342..0x6c53d6`,
  client `0x491f77..0x491fe3`; each machine turns the index into `Locations/Fxx/Fxx_Main` with its own level list (`re/netcode_fa.md`
  1.1 / 1.2, `re/netcode_plan.md` 1). FACT (carried).
* KLHook's expansion maps take over a stock slot. `kls_map` (klslot.c:260) rewrites the open of `Scenes\Locations\Fxx\...` to
  `KLExpansion\Maps\<dir>\` using a rule chosen at klslot.c:279-287: `page = kls_page_now()` (klslot.c:212-215) then
  `kls_find_rule(s, page)`, falling back to page 0 (`[Redirect]`). `kls_page_now()` is `kls_page_force` or `kls_menu_page`, the latch
  that `kls_menu_watch` (klslot.c:366-416) reads from THIS machine's own menu window stack.
* So the map is decided by local UI state:
  1. A joiner that entered through an invite or `+connect_lobby` never opened `HeistPlayMenu2`; its latch is 0, so it loads the page-0
     rule or the stock map while the host loads the Dead Men map. FACT of the code path (klslot.c:279-287); the exact failure (scene
     refs differ, 16-bit refs, a crash or a silent desync) is a GUESS (`re/private_match_buildcheck.md` 1).
  2. Even the HOST has the problem: the latch is dropped 1 s after the frontend shows a window stack without a map page
     (klslot.c:407-415), and the online menu / FALobby pages are such a stack. So online the host also falls back to page 0.
     (`re/netcode_plan.md` 1 says the same; the drop online is not seen live: GUESS.) The stage-0 workaround is `[Expansion] Page=N` on
     both machines (klslot.c:558), identical ini by hand, private lobby only.
* The build check (klbuild.c) already tells two machines when they would load DIFFERENT FILES for a slot (klbuild.c:617-625 prints,
  :639-651 `klbld_diff`), but it only describes each machine's own page-based choice; it does not make the choices equal.

Goal: the host's choice is authoritative. A joiner loads exactly the folder the host announced for the slot, or is refused with a
visible reason, BEFORE the level archive opens (the first open of `<slot>_Main.zip`, klslot.c:278).

## 2. Channels that exist (and what is rejected)

| channel | exists? | verdict |
|---|---|---|
| Steam lobby data, host writes, joiners read (ISteamMatchmaking008 +0x4c / +0x48) | FACT: the game itself writes 9 keys with it at `0x869430` (`re/netcode.md` 3.2); klmm.c:169-176 and klbuild.c:682-688,779-787 already write extra keys; klbuild.c:815-853 already reads `klx_slots` / `klx_code` with `RequestLobbyData` retries | **CHOSEN** for the table |
| Steam lobby MEMBER data (+0x60 set / +0x5c get) | FACT: used by klbuild.c:767-771 (set), :800 (get); the game has no site (buildcheck 2) | **CHOSEN** for the joiner's acknowledgement |
| Lobby chat (+0x64 / +0x68) | exists, stock handlers ignore extra text (GUESS, buildcheck 2); not stored, late joiners miss it | rejected (fallback only) |
| The game's own session data (`DDL_ZServer.m_szServerMap` `[D+0x234]`, `m_iScenarioIndex`) | replicated by Net-Z (`re/netcode.md` 181), but the client load path ignores the name unless its OWN command line has `-o MPMap` (`re/netcode_fa.md` 1.2, 0x491f50). Writing a name into the replicated object means writing host game state: GUESS it replicates, and the slot index still picks the file | rejected for v1 |
| `-o MPMap` on the joiner | the only place a client uses a name (0x491f50) but it is a command line, fixed at launch (CLAUDE.md: launch options are the owner's) | rejected |
| P2P / Net-Z message | peers are added only after `SyncLobbyWithNetZ` (0x4d2a40), i.e. after the decision; unknown ids are dropped (0x48ca80) (buildcheck 3) | rejected |
| A string in the persona name | visible, length limited (buildcheck 3) | rejected |

Chosen channel: **lobby data key `klx_maps` written by the host** (what to load per slot), **member data key `klx_ack` written by each
joiner** (what it adopted). Both through the existing 36-slot ISteamMatchmaking proxy of klbuild.c (import slot `0xb107d8`;
klbuild.c:705-722, table 893-905). It rides the same wrapper, so MapSync needs `[Build] Check=1`.

## 3. What it builds on (file:line)

| need | existing code |
|---|---|
| host/joiner role of the lobby | `klbld_SetLobbyData` marks host on key `name` (klbuild.c:682-688); `klbld_GetLobbyOwner` marks the joiner by return address `0x6299da` (klbuild.c:697-703, const :84) |
| write lobby data / member data | `KLBLD_REAL(19)` (klbuild.c:779-780, 786), `KLBLD_REAL(24)` via `klbld_member_publish` (:767-772) |
| read lobby data / retry | `KLBLD_REAL(18)` (:822), `KLBLD_REAL(27)` RequestLobbyData, up to 8 tries (:843-847) |
| walk members, read member data | `KLBLD_REAL(16/17/23)` (:791-800), 500 ms poll (:92, 789) |
| per-slot print of the file that WOULD load | `klbld_effective_rule` (:610-615) -> `klbld_rule_token` (:584-594; `MISSING` if the file is absent) -> `klbld_my_fp` (:617-625) |
| compare, per slot | `klbld_diff` (:639-651), bit n-1 for Fn |
| refuse start | `klbld_apply` / `klbld_push_mask` (:727-756): clears the slot bit in this machine's client mask via kl2 `0x634b90` / `0x845640`, game thread only (:863) |
| the file redirect and its rules | `kls_map` (klslot.c:260-308), `kls_rule[]` / `kls_slot[]` (:168-179), `kls_find_rule` (:251) |
| rule loader (folder must exist, plain names) | `kls_rules` (klslot.c:510-540) |
| "am I online" | `kl_online()` (klhook.c:255-) |
| tick that cannot call Steam during a load | `klh_tick` switches to the fallback thread while the main loop stands still (klhook.c:741-744) -> the table must be CACHED before the load; no Steam call from `kls_map` (it runs inside CreateFile wrappers, klslot.c:320-336) |
| build code, offline | `tools/kl_buildprint.py` (compute :184, compare :256), in-hook twin `klbld_full_*` (klbuild.c:511-580, `klbld_full_thread` / `klbld_full_start`) |

## 4. The design

### 4.1 Wire format (all keys new, all written only when `[MapSync] Enable=1`)

Lobby data, host:
* `klx_maps` = `S=<seq>;F01=<dir|->;F02=<dir|->;...;F09=<dir|->`. `<dir>` = the folder under `KLExpansion\Maps` the host's rule for that
  slot resolves to under the host's EFFECTIVE page; `-` = the stock level. `seq` = a counter the host bumps whenever the string changes.
  Written for ALL nine slots, so the host never has to know which slot the selector has chosen (the selector is TO FIND, section 8).
  Length < 200 bytes (GUESS: far under Steam's per-value limit, buildcheck 4).
* The existing `klx_slots` (print per slot, klbuild.c:780) and `klx_code` (:786) stay; they verify the CONTENT of what `klx_maps` names.
Member data, every machine with the hook (host and joiners): existing `klx_fp` (klbuild.c:770) plus new `klx_ack` = `<seq>:<8 hex of a
hash of the adopted table>` (joiner), or `-` when it could not adopt.

### 4.2 Host-side: what "the host's page" is online

* New key `[MapSync] HostPage=-1` (default -1 = unchanged: whatever `kls_page_now()` says). `0..9` = the page whose `[Redirect.N]` table
  the host publishes AND uses for its own load. Implementation sketch (not written): `kls_page_now()` (klslot.c:212) returns
  HostPage while a NEW flag `kls_online_host` is set (it does not exist yet; it would come from klbuild.c's `klbld_lobby == klbld_host_lobby` test, klbuild.c:686). This makes the stage-0 `[Expansion] Page=N` unnecessary and does not touch the offline path.
* v1 has no in-lobby map-page UI: the page is a host ini value. A selector inside FALobby needs a menu change (`re/menus.md`, the nine
  slot entries are fixed, TO FIND: the widget behind `MP_SelectedLevel`, key `0xb6d6e4`, buildcheck 5.5). GUESS that it is not worth
  it before the ini route is proven.
* Which slot is loaded needs no hook code at all: the game's own index (host `0x6c53db`, client `0x491fd1`) picks the entry of the table.

### 4.3 Joiner-side: adopting the table

* The joiner tick (klbuild.c:815-853) is extended: next to `klx_slots` it reads `klx_maps` (same `RequestLobbyData` retry, same
  `klbld_joiner_tries`) and, when the string is well formed (folder names pass the `kls_plain` rule, klslot.c:483, `<=47` chars, `S=` present),
  stores it in a small table `kls_net_dir[9][48]` with a volatile `kls_net_seq` (written last).
* `kls_map` is changed (proposed) at klslot.c:279-287 (REVIEW 2026-10-18: the latch update at :279-283 must be bypassed too, else the
  log line and `kls_slot[s].page` still carry the local page; the offline-only `kpm_override` at :280 stays untouched): if `[MapSync]`
  is on and `kls_net_seq != 0` (that is the gate; do NOT also require `kl_online()` here: klhook.c:255-264 answers 0 until the session
  object and rules object exist, and a false answer at the archive open would silently fall back to the local page; `kls_net_seq` is
  cleared by `klbld_reset_lobby`/`LeaveLobby`, which is what keeps offline Arcade and stock rounds unchanged), the rule for slot `s` is NOT `kls_find_rule(s, page)` but the rule whose `.slot` is `s` and `.map` equals
  `kls_net_dir[s]` (case-blind, as klmm/klbuild compare), or "stock" when the entry is `-`. This is authoritative in both directions:
  a joiner whose own `[Redirect]` page 0 maps F01 to a Dead Men map still loads STOCK F01 when the host says `-`.
* PREREQUISITE (REVIEW): `kls_on` is set only when `[Expansion] Enable=1` and the root is valid (klslot.c:547-586); with it off `kls_map`
  answers 0 at its first line (:263), so a joiner with the expansion disabled cannot adopt anything. MapSync must log that, or require
  the same ini. Slots are also limited to `KLS_SLOTS` 16 (klslot.c:156).
* Rule lookup by folder needs a rule to exist. Rules are built only from the joiner's own ini (`kls_rules`, klslot.c:510-540, folder must
  exist at init: :521-522). If the joiner has the folder but no ini line for it, v1 adds a runtime rule: from the game-thread tick (not
  from `kls_map`) append to `kls_rule[]` (`KLS_RULES` 64, klslot.c:157; GUESS: lock-free append, bump `kls_nrules` last, is safe on x86 since
  readers only scan up to the count) and create the `kls_slot[]` entry if the slot has none (klslot.c:524-531). If the folder is not on disk: no rule
  is made and the entry counts as MISSING (section 5).
* The page latch (`kls_slot[s].page`, klslot.c:281-283) is not used on this path.
* `klbld_effective_rule` (klbuild.c:610) is changed the same way (so the joiner's `klx_fp` print is of the file it will really load, and
  `klbld_diff` compares like with like). The token cache is per rule index (klbuild.c:582), which keeps working for runtime rules.

### 4.4 Step by step

HOST (on a game-made private lobby; `[Net] PrivateLobby=1` is recommended, klmm.c:219-221, GUESS that nobody should run this on a public one):
1. Create game. The game's `0x869430` writes `name` first (klbuild.c:686 marks the lobby as host). Existing ticks publish `klx`,
   `klx_slots`, `klx_fp` (klbuild.c:774-784).
2. NEW, same tick: build the table from the rules under `HostPage` (or `kls_page_now()`), write `klx_maps` if it changed (seq+1), write member
   `klx_ack=<seq>:<hash>` for itself.
3. The host plays its own selector as today. The index is the game's.
4. NEW: before the start gate lets the countdown run, require every member with the hook to carry `klx_ack` equal to the current
   `<seq>:<hash>` (poll at 500 ms, klbuild.c:789-811). A member whose ack is missing or different for longer than a grace (3 s,
   klbuild.c:91) sets the bit of the slots that are non-stock in the table in `want`, so the existing mask hold applies (klbuild.c:742-756). REVIEW: the hold clears bits in THIS machine's client mask only (:738); that it stops the
   countdown is the GUESS of buildcheck 6/8, not shown. A member WITHOUT the hook counts as stock (klbuild.c:803-808): it differs on every non-stock slot, hold as
   today.
5. The countdown then runs, the game loads `Locations/Fxx/Fxx_Main` on the host: `kls_map` picks the same table entry.

JOINER:
1. Join (invite, `+connect_lobby`, browser). `klbld_GetLobbyOwner` records the lobby (klbuild.c:697-703).
2. NEW: tick reads `klx_maps` and `klx_slots`, retrying `RequestLobbyData` (klbuild.c:843-847). Adopts the table (4.3). Computes `klx_fp`
   from the ADOPTED folders; publishes `klx_fp` and `klx_ack`.
3. Compare per slot with `klbld_diff`. A differing slot (file missing, other content, other Patch01) clears that slot's bit in the joiner's own
   mask (klbuild.c:742-756). The game then shows its own "missing content" text for a slot it thinks it does not own
   (`Online/MissingContentPackClient`, kl2 0x6c4bcd / 0x6c4e07, `re/netcode_fa.md` 1.2), which is the only player-visible message this design
   relies on. The clear is the same trick that is already written (it clears the bit in the JOINER's own mask, klbuild.c:738; it reaches the host's gate only if `m_iAvailableLevels` is re-sent, section 7 item 2); its effect on the HOST's gate (replicated `m_iAvailableLevels`) is a GUESS
   (buildcheck 6, 8).
4. When the host starts, `kls_map` serves the adopted table. No Steam call happens in `kls_map`.

### 4.5 Stock-map case (no change by default)

* `[MapSync] Enable=0` (default): not one line of the existing path changes, nothing is published, no rule is added.
* Enable=1 and the host's table is all `-` (a stock round): the joiner adopts "stock for every slot", so a joiner with `[Redirect]` lines in
  its ini loads the stock level, exactly what the host loads. A host/joiner whose rules never match gives the same result as today.
* A joiner with the module on that meets a lobby WITHOUT `klx_maps` (a stock host, or a host with MapSync off): `JoinedWithoutTable` =
  `follow` (default 0 = keep today's behaviour and log a warning; 1 = force stock for all nine slots, the safe choice for hook-vs-stock
  games; matches `NoKeyBlocks` in klbuild.c:29-30 in spirit).
* A stock-client joiner to a hooked host: nothing to adopt; klbuild's existing rule counts it as stock (klbuild.c:803-808) and the host
  holds the start on any non-stock slot, never on a stock one (klbuild.c:40-43 for the token rule, :803-808 and :647-648 for the stock-client case; the earlier cite `:155` was a hash-constant line).

## 5. Failure cases

| case | detection | reaction |
|---|---|---|
| joiner lacks the host's map folder | its `kls_net_dir[s]` has no folder. REVIEW: no rule is made then, and `klbld_rule_token(-1)` returns `-` (klbuild.c:587), the STOCK print, not `MISSING` (that string only appears for an existing rule whose zip vanished, :592). The new code must publish an explicit `MISSING` / `klx_ack=-` for that slot, else only the diff against the host's non-stock token flags it | log `mapsync: slot F0n: map <dir> not installed`; clear the slot bit (own mask hold); `klx_ack=-` so the host holds. Do NOT let `Fallback=1` (klslot.c:296-297) quietly use the stock file: under MapSync an announced slot with no file is `Fallback=0` (the open fails) in case the hold failed. GUESS: a failed open of the archive ends in a crash or a stuck load; hence the primary defence is the hold |
| joiner has the folder, other build / content | `klx_slots` token differs (klbuild.c:639-651); full code differs (klbuild.c:829-833, log only) | hold the slot (as above); log with the three codes (offline: `kl_buildprint.py --compare`) |
| other Patch01.zip | `P=` token (klbuild.c:596-603) | every slot with a rule on either side differs (klbuild.c:645-648) |
| joiner without the hook | no `klx_fp`/`klx_ack` after the grace (klbuild.c:803) | host holds non-stock slots; joiner sees only the game's own text, if any (GUESS) |
| host without the hook (stock host) | no `klx_maps` after 8 requests (klbuild.c:848-851) | `JoinedWithoutTable`; warn or force stock |
| host changes the choice after the joiner read it | `seq` increases; the joiner tick re-reads each 1 s (2 x 500 ms, klbuild.c:820) | joiner re-adopts; the host's gate waits until the ack equals the new seq. Race: the main loop stands still during a load (klhook.c:741), so a change in the last moments cannot be adopted: the ack gate is what prevents it |
| host leaves / lobby left | `klbld_LeaveLobby` (klbuild.c:690-695) | `klbld_reset_lobby` (:760-765) is extended to clear `kls_net_*` and the rules added at run time stay but unused; the mask is put back (:873) |
| Steam value missing or malformed | parse fails | table not adopted, warning, stays on today's behaviour (no wrong map from a half-read string) |
| a joiner changes its own ini mid-lobby | print changes | `klx_fp` republished (klbuild.c:767-772) |
| lobby is public (Quick Match) | nothing can tell a stranger | not covered; private lobbies only (`re/netcode_plan.md` 1 hazard). `[MapSync] PrivateOnly=1` (default) refuses to publish unless `[Net] PrivateLobby` is set (klmm.c:219) |
| ranked | `Ranked` lobby key / session ranked byte | not covered; klsteam.c already blocks stat writes on non-stock levels (klslot.c:81-86) |

The player is told by: the game's missing-content text (via the mask clear; GUESS), the log line, and, in a round only, a HUD popup
(`klhud_popup.c`, drawn only while an Arcade round is on, header :10-15, so it cannot show in a lobby). A lobby-time message needs a
UI hook that does not exist yet: TO FIND (the lobby's text-widget set call). v1 can only promise the log line.

## 6. Ini keys (KLHook.ini, all opt-in, default off)

```
[Build]      Check=1         existing (klbuild.c:25): required, MapSync rides its Steam wrapper
[MapSync]    Enable=0        0 = nothing changes. 1 = publish klx_maps / klx_ack, adopt the host's table, extend the hold
             HostPage=-1     host: page whose [Redirect.N] table is published and used online (-1 = kls_page_now())
             JoinedWithoutTable=0   joiner meets a lobby with no klx_maps: 0 warn only, 1 load stock for every slot
             PrivateOnly=1   publish only when [Net] PrivateLobby is 1 or 2 (klmm.c:219)
             AckGraceMs=3000   how long the host waits for a member's ack before it holds (default = klbuild.c:91)
             Hold=1          0 = log only (klbuild.c:26's Hold also applies)
```
Reading rule: `Enable` read once at init (as klbuild.c:886-890), absent = 0. Nothing is written to disk and no code byte of kl2.exe changes.

## 7. kl2.exe addresses still to find

Static pass 2026-10-18 (kl2.exe read by address with `tools/kl_exe.py` + capstone; nothing run, nothing written to the game folder). Tags per
result: PROVEN = read in the disassembly cited; PARTIAL = the code is read but a link is inferred; GUESS = not read. Addresses are kl2.exe
virtual addresses (base 0x400000).

1. The widget behind `MP_SelectedLevel` (key `0xb6d6e4`, read at `0x6c4d02..0x6c4d16`) and how the FALobby selector reaches `0x746570`; needed
   only for an in-lobby page chooser (not v1). (buildcheck 5.5)
   * Result, PARTIAL (the store and its readers/writers PROVEN; which toggler entries exist is not decoded).
   * `MP_SelectedLevel` is not a widget but a key in a per-menu value store: `[0xdd265c]` (GUI manager) `+0x824` -> store; store vtbl+8 = Get(key,
     default), vtbl+0x14 = Set(key, value, 0). Read form (0x6c4cfb..0x6c4d16, 0x7dc644..0x7dc665, 0x7dcca3..0x7dccc4):
     `mov ecx,[ecx+0x824]; mov edx,[ecx]; call [edx+0x14]; ...; push 0; push 0xb6d6e4; call [edx+8]`.
   * Writers (`push 0; push value; push 0xb6d6e4; call [edx+0x14]`): 0x4798b8..0x4798da (writes only if the toggler byte differs from the stored
     one, then pokes `LobbyImageToggler` and `LobbyLevelNameToggler` by name), 0x6c9f43..0x6c9f57 (value = byte at `[esp+0x6c]`), 0x7d0c3b..0x7d0c56
     (pushes `ebx` twice; ebx was compared with the store pointer at 0x7d0c33, so it is probably 0 = a reset; the register's value is not traced). A coop twin exists at 0x479857 (`CoopLobbyLevelNameToggler`, `CoopLobbyBriefingToggler`).
   * Reader chain in the FALobby selector (class name `ZMercsFASelectorLobby` / slot 10 taken from the earlier pass, not re-checked in the 2nd pass; code 0x7dc5c1..0x7dc693): toggler `LobbyLevelNameToggler` (0x7dc5e4) ->
     Get(`MP_SelectedLevel`) (0x7dc660) -> 0x746570 (0x7dc676; table 0,1,2,3,5,6,4,7,8 built on the stack at 0x746582..0x7465a9, 0xff -> -1 at 0x7465d3; the bound test is `ja 9`, so input 9 passes it and reads the never-set byte [esp+9]: input 9 is undefined) ->
     `[0x168e598]` vtbl+0x28(slot) (0x7dc685..0x7dc691) -> 0x7163e0(slot), 0x520c60(slot). A second copy of the body is at 0x7dcc3d..0x7dcce4.
   * An in-lobby chooser would write the key and let 0x479888 poke the togglers: GUESS, not read.

2. Whether `m_iAvailableLevels` is re-sent after the lobby forms, i.e. whether a joiner-side mask clear reaches the host's gate (the DDL send
   path; buildcheck 8). Decides whether the joiner can refuse by itself.
   * Result, PARTIAL (local object and setter PROVEN; the send trigger NOT read, so "reaches the host" stays a GUESS).
   * Declared `m_iAvailableLevels : DDL_UInt16Reliable` (strings at 0xd2f366 / 0xd2f37c). On the local client (`[0x168e598]+0x98`) it is the
     word-sized value object at `+0xb8`: content at `+4` stored XOR 0xdead, previous content at `+0x1c`, flag byte at `+0x1e`.
   * Getter 0x431f60: `movzx eax,word [ecx+4]; xor eax,0xdead; ret`. Setter 0x845640: if the flag is set and the new value equals the old, returns
     0 unchanged; else `mov dx,[ecx+4]; xor eax,0xdead; mov [ecx+4],ax; mov [ecx+0x1c],dx; mov al,1; ret 4` (returns 1, keeps old value at +0x1c):
     a dataset set with change detection. Gate reader 0x73f270..0x73f289: `add ecx,0xb8; call 0x431f60; mov edx,1; shl edx,cl; test dx,ax; setne al`
     (via 0x7ca830(client,slot)).
   * The game rewrites the mask after the lobby exists: the DLC-install callback 0x845700 (jump table 0x845954, ids 0x6d6a..0x6d71) calls 0x845640
     at 0x845835, 0x845894, 0x84590f on `[[0x168e598]+0x98]`. A mask rewritten mid-session only makes sense if it is sent; that is inference.
   * NOT found: the code that notices `[+4] != [+0x1c]` and queues the send; it is in the Net-Z library through generic offsets. The word
     "Reliable" in the type name is the only hint it is sent (GUESS). Live test (section 8) still decides.
   * 3rd pass (static, 2026-10-18; kl2.exe bytes via kl_exe + capstone, nothing run). Result: no dirty flag and no send call exist at the setter; the sender is still NOT found, so "a changed mask reaches the host" stays a GUESS.
     * PROVEN, the setter marks nothing: 0x845640 (14 instructions, 0x845640..0x845670) writes only `[ecx+4]` and `[ecx+0x1c]` and returns al; it has no call, no flag write, no queue. Its 44 direct callers are plain stores (all `call`/`jmp` rel32 to it, byte scan).
     * PROVEN, the value object has three virtuals only: constructor 0x8fded0 stamps vtable 0xbd414c at `[obj]` (and 0xbd4144 at `[obj+8]`), sets `[obj+4]=[obj+0x1c]=0xdead` (mask 0) and `byte [obj+0x1e]=1` (0x8fdf13..0x8fdf1d). Slots: 0 = 0x6b34b0 (dtor), 1 = 0x49d050 (`mov ax,[ecx+4]; mov [ecx+0x1c],ax`: snapshot cur -> prev), 2 = 0x56b5d0 (de-xors prev and cur, then calls a listener list on `obj+8` through 0x7761a0 with (old, new)). No slot compares cur with prev or builds a message. 0x7761a0 only walks an {id, fn} list and calls the matching function: a change-listener fan-out, not a send.
     * PROVEN, member numbering in the ZClient object: ctor 0x56b740 constructs members with ids 0..8 at +0x58, +0x78, +0x98, +0xb8, +0xd8, +0xf8, +0x118, +0x138, +0x158 (`mov byte [esp+0x14], n` between calls); the mask `+0xb8` is member 3 (`+0x98`, the campaign mask, is member 2). Both are set together at 0x8b6626/0x8b6642 and 0x4d1fba/0x4d1fc6.
     * PROVEN, the only member walker found is the RECEIVE bracket: ZClient DDL vtable 0xbd4eac slot 7 = 0x4f0a20(stream, mode). For each member n it asks `stream vtbl+0x20(n)` ("field n in this update") and then calls `member vtbl+4` (mode 0, snapshot, before the values are applied) or `member vtbl+8` (mode 1, listener notify, after); other modes jump to the no-op 0x716640 via 0x951e30 (0x4f1270). The same pattern covers id 4 -> `+0xb8` at 0x4f0ab3 (mode 0) and 0x4f0ed3 (mode 1). The store of the new word into `[obj+4]` between the two modes is not in this function (GUESS: done by the stream reader in Net-Z).
     * NOT found: any writer-side counterpart (a function that tests `[obj+4]` against `[obj+0x1c]` and sets a field bit on an outgoing stream). A byte scan for `66 3b/39/8b/33/31 .. 1c` (word compare against disp 0x1c) gave 22 sites; the five looked at (0x655b13, 0x655b29, 0x517208, 0x56b5e4, 0x952115) are the listener call, a size computation and an unrelated 16-bit id lookup, none a dirty test. GUESS: the generic Net-Z dataset code (0x93.. / 0x95.. range, `0x8dbb30 -> 0x942b20` is its "update this dataset" path for the player datasets only: 9 callers, all player-side) also covers reliable members, with the old value at +0x1c as the delta base; unproven.
     * Reading of the evidence (GUESS): the shadow at +0x1c exists so the receive path can hand (old, new) to listeners; whether the master also uses it as a delta base is not shown. Consequence for the plan: the clear must still be tested live (a client clears its bit and the host log shows the countdown held) before any design relies on it.
   * Does the host's start countdown read the clients' masks, and where? YES, PROVEN (bytes), every frame, no cache:
     * State machine 0x6c49a0, loop `edi` = 0..11 (`cmp edi,0xc`, 0x6c4d89): client pointer = `0x8fdf90(edi)` (array accessor on the session object `esi`), skipped if null (0x6c4d4e) or if its object pointer is 0 (0x6c4d5a); then `0x7ca830(client, slot ebp)` (0x6c4d72) -> `0x73f270` -> `0x431f60` (the xor getter) and `test (1<<slot), mask`. A second identical loop copy calls it at 0x6c4f58. The host's own entry first: `[0x168f750] vtbl+0x14` (0x5e1510) at 0x6c4d34..0x6c4d38.
     * Any clear bit gives ok=0 (0x6c4d83), and 0x6c4dd3 resets the countdown `[esi+0x194]`; it only counts down (`fsub`, 0x6c4dbb) when ok != 0, `[esi+0x1f4] != 0`, `[esi+0x5c] == 4` (0x6c4db5) and the count test at 0x6c4da1 passes. So the host reads the DO copies of the clients, wherever they were filled from; the read is live. Whether a remote client's copy ever changes after its first update is exactly the unproven send/receive link above.
     * Other readers of the same getter (not followed): 0x436be5, 0x5b6eb5, 0x62c5df, 0x632e1f (callers of 0x7ca830) and 0x408bdf, 0x40d2e8, 0x4780ef and 25 more callers of 0x431f60.

3. The time of `0x491f50` (client level name) relative to the first open of `<slot>_Main.zip` and the thread of the call, to prove the table is
   read-only at that moment; and which thread runs the CreateFile wrappers (klslot.c:320-336) during a load.
   * Result, PARTIAL (both call chains read; that the load request comes AFTER 0x491f50 is an inference from session state numbers, 0xa vs 0x13/0x19..0x22, not from one traced run; "main thread" is an inference, no thread id observed).
   * 0x491f50 is called once, at 0x5392ec, from the `ZSessionHandlerClient` handler (slot 97, holds 0x53919c): stores the name in `[sm+8]`
     (copy call 0x4f99e0 at 0x491f89, name from 0x4468a0; `MPMap` is looked up at 0x491f9c (0x793550) and wins if present; only when the game type from 0x83f980 is 4 does it use `levellist->slot15(D.levelIndex)` at 0x491fd1..0x491fe3, game type 2 and others branch at 0x491fe7), calls 0x87c980, returns. It opens no
     archive. The caller then reads the server DO (0x5392da), sets session state `vtbl+0x68(0xa)` (0x5393ff) and returns 2 (0x539422).
   * The load request comes later from 0x89fa20 (callers 0x57b205, 0x74c433, 0x827be0, 0x8c58b3, 0x8f8dfa), only in state 0x19 or 0x1f..0x22
     (0x89fa24..0x89fa3a): `vtbl+0x68(0x13)`; for game type 4 (0x89fa75) the name is again `levellist vtbl+0x3c(byte from 0x8dc7f0(D))`
     (0x89fa81..0x89fa98), `MPMap` first (0x89fa5d), else D's name via 0x4468a0 (0x89fb10). Both end in 0x86f230(name) (0x89faa1, 0x89fb1e). The host
     does the same from 0x6c49a0 (0x6c5354, 0x6c53a4, 0x6c53d6).
   * So a client reads the level index twice, each time through its OWN level list (0x491fd1 early, 0x89fa98 at load); the table must be final
     before the second. The ack gate of section 5 provides that.
   * 0x86f230 builds `"%s%s"` (0x86f29c) and calls `[[0xdd2640]+0xac] vtbl+0x74(string)` (0x86f2b5..0x86f2c8), the scene-load request. The loader
     is `ZEngineDataBase` slot 4 = 0x7f4f90 (vtable 0xb8fa04; virtual, no direct caller): unmounts, mounts `Patch01.zip`, then the scene archive.
   * Thread: `CreateThread` call sites 0x6a547c, 0x73ba88, 0x7ebe85, 0x83001f, 0x9a70b6, 0x9c8a97 and `_beginthreadex` 0x95acc3 have start
     procs 0x458750, 0x927e80, 0x561330, 0x64cb80, 0x9a7010, 0x95ac50 (+1 register proc); none is the scene loader (by push sequences and
     `re/loading.md`, no full call-graph walk). The loader's progress callback (`ZEngineDataBase` slot 3, 0x53ac90 -> 0x48a1e0) runs
     `SteamAPI_RunCallbacks` and the Windows message pump, and klhook.c:741 logs the tick as driven by the main loop, so the load runs
     synchronously on the main (window) thread: inference. CreateFileA users 16 call sites ([0xb10270]), CreateFileW 74 ([0xb10204]),
     CreateFileMappingA 3, ReadFile 7: a worker that only reads an already open archive is not excluded.
   * Verdict: the table is read after 0x89fa20, which is after 0x491f50; another reader on a worker thread during a load is not excluded (GUESS),
     which is why section 9 keeps the append-race item.

4. A text-set call for a lobby message (the label that shows `Online/MissingContentPackClient`, `0x6c4e07`) to name the missing map to the
   player.
   * Result, PARTIAL: the call sequence and key lookup are read (PROVEN); that the entry is a modal pop-up is INFERRED from the table name `ErrorMessages` and key `ErrorOccuredHeader` (the display code 0x54d690 / 0x47c3dd was not read); no lobby label setter found; the free-text case is a GUESS.
   * The whole sequence runs only when `levellist(0x168f750) vtbl+0x14(level byte [esi+0xbe])` returns false (0x6c4e07..0x6c4e1e), i.e. it is the level-availability refusal on the host side (function around 0x6c49a0).
   * 0x6c4e07..0x6c4e91 builds three string objects with 0x83e2e0 (ecx = object, push = key): `Online/MissingContentPackClient` (0x6c4e25), the
     empty string (0xb34850, 0x6c4e35) and `Online/ErrorOccuredHeader` (0x6c4e4e). Then `push &text; push &none; push &header; push 0;
     mov ecx,0x1686e60; call 0x58bbd0` (0x6c4e67..0x6c4e8b) and `push eax; mov ecx,0x1686e60; call 0x47c260` (0x6c4e90..0x6c4e96). 0x58bbd0 is
     the stub `xor eax,eax; ret 4` (33 c0 c2 04 00; ICF-folded, also `ZGameRulesHeist` slot 169); it pops the `push 0` and returns 0, and
     0x47c260 takes the remaining four dwords (`ret 0x10`, 0x47c404). The same sequence is at 0x6c4beb..0x6c4c50, 0x6c5091, 0x6c515d.
   * 0x47c260 (error-message manager, global 0x1686e60) resolves each key through the table `AllLevels/Menu/ErrorMessages`
     (`[[0xdd2640]+0xac]+0x94` vtbl[0](0, key char*, 0xb6f2c8) at 0x47c2a2..0x47c318), stores the results at `[mgr+0x18/0x1c/0x20]`, pushes an
     entry (kind 3) into a 9-dword-stride list at `[mgr+0xe4..]` counted at `[mgr+0x150]` (0x47c321..0x47c341) and shows it (0x54d690, 0x47c3dd).
     0x47c287..0x47c29c returns when a flagged entry is already open: one message at a time.
   * Naming a map therefore needs a KEY in the `ErrorMessages` .LOC (Patch01.zip overrides same-named members) or reuse of an existing key. What
     the lookup returns for a key that is not in the table (raw key, empty, crash) is NOT read: GUESS. A hook calling 0x47c260 itself must build
     the three objects the same way (0x83e2e0 -> 0x770520). No lobby text-label setter was found.

5. The caller of the `JoinSession` second argument (private/ranked bit on a client, `re/netcode_fa.md` 1.2) so PrivateOnly can be tested on a joiner.
   * Result, PROVEN for the call sites (three); PARTIAL for the value (two sources found; which one a plain invite uses is NOT read). 2nd-pass correction: on the message path arg2 is the 4-byte read, not the 1-byte one.
   * `JoinSession` = 0x6d8640 (`ret 8`; arg2 stored at `[S+0x36f]`, 0x6d874c) is `ZOnlineServiceSteam` vtable slot 45 (vtable 0xbd597c, +0xb4).
     All 80 `+0xb4` call sites were scanned; those with exactly two pushes:
     1. 0x8d27a9 (`ZOnlineGamePlayTrigger` vtable 0xbc8b8c, slot 34 = 0x8d2740): service getter 0x7bb2a0 (returns `[ecx+0x54]` only if
        `[0x168e598]+0x5c == 4`), then `mov ecx,[esi+0x44]; push ecx; push edi; call [edx+0xb4]` (0x8d27a4..0x8d27b3). arg2 = `[trigger+0x44]`.
     2. 0x8649bf (same class, slot 26 = 0x864990): arg2 = `[esi+0x44]` (0x8649ba, 0x8649c5), arg1 = `[esp+0x10]`, guard: argument == `[0x168c510]`.
     3. 0x619b5c (function 0x619b20, `ret 8`): arg1 = 0x8ee6d0(`[esp+4]`), arg2 = the function's second argument (0x619b56, 0x619b62). Guards:
        0x905460 true and `byte [[0x168e598]+0x15d] != 0` (0x619b26..0x619b3c). Sole caller 0x71fc0f in 0x71fbd0, which reads a message: two reads
        via 0x950f20(buf,size,count): first ONE byte (0x71fbe1..0x71fbee, buffer [esp+0xc] at 0x71fc07) which becomes arg1 (`push eax`, 0x71fc0c, after 0x8ee6d0 in 0x619b44), then a DWORD (0x71fbf3..0x71fbfe, buffer [esp+0x14] at 0x71fc03) which is pushed first (`push edx`, 0x71fc0b) and so is arg2; JoinSession stores only its low byte (`mov cl,[esp+0x2c]`, 0x6d8742, 0x6d874c). The earlier text had the two reversed. 0x71fbd0 is called at
        0x693e0b from a dispatcher that compares a message id with `word [handler+0xb6]` (0x693dfe..0x693e0b).
   * So arg2 is a property of a `ZOnlineGamePlayTrigger` entity (level/menu object) or the low byte of a dword in a received session message, never read from the
     lobby's own data. A joiner arriving by invite or `+connect_lobby` cannot be told "private" from this byte (as `re/netcode_fa.md` 1.2 said).
     NOT read: which of the three paths `+connect_lobby` (0x506cc0) and the invite handler take; so a PrivateOnly test on a joiner still has to use
     the lobby type (Steam `GetLobbyData`). That `[trigger+0x44]` is the ranked/online flag is a GUESS (schema entry not looked up).

6. `ISteamFriends` GetFriendPersonaName offset to name the mismatched member (buildcheck 8).
   * Result, PARTIAL: the bytes PROVE a vtable call at `+0x1c` taking a 64-bit id (two pushes) and returning a `char*` that is copied into a 33-byte buffer; that this is GetFriendPersonaName rests on the SteamFriends005 slot order recalled from the SDK header, and that `[0xb107d4]` is the `SteamFriends` accessor was NOT checked (the IAT slot holds a stub address 0x8ce596 in the file image; no import name read). The member-list claim is inferred (the loop compares ids at `[esi+0x84]`, owner of that array not identified).
   * Call site 0x8aec31..0x8aec48: `call [0xb107d4]` (the `SteamFriends` import), then `mov ecx,[esp+0x14]; mov edx,[eax]; mov edx,[edx+0x1c];
     push ecx; mov ecx,[esp+0x14]; push ecx; mov ecx,eax; call edx`: two pushes (the 64-bit CSteamID, low and high), returns a `const char*`.
     0x8aec4a..0x8aec5a: `push 0x20; push eax; lea eax,[esp+0x34]; push 0x21; push eax; call [0xb10390]` (`strncpy_s`, dest 0x21 bytes, max 0x20):
     the name goes into a 33-byte buffer, and the same function formats the id with `%llu` (0xb674e0, 0x8aec86): the member list's name-and-id
     builder. The loop before it (0x8aeba5..0x8aebf0) compares 64-bit ids at `[esi+0x84]+8*i`, so the id is a lobby member's.
   * Cross-checks on the same layout: 0x8db740 `+0xc` with `push 0xffff` = GetFriendCount(all flags); 0x64c286..0x64c298 `+0x4c` with `push 'Friends'`
     (0xb69138) = ActivateGameOverlay (guarded by `SteamUtils()+0x44`, 0x64c273..0x64c284). The SDK 005 order (0 GetPersonaName, 4 SetPersonaName,
     8 GetPersonaState, 0xc GetFriendCount, 0x10 GetFriendByIndex, 0x14 GetFriendRelationship, 0x18 GetFriendPersonaState, 0x1c
     GetFriendPersonaName, ..., 0x4c ActivateGameOverlay) fits all three. Slot names other than these come from the SDK header as remembered
     (GUESS), not from the exe, which holds no names.

## 8. Live tests for when stage 4 is OK'd (two Steam accounts, identical tree except where noted; keep `[Net] Log=1`)

1. Single machine, log only: create a private lobby with MapSync on; read back `klx_maps` and `klx_ack` in the log (`mapsync:` prefix); check the
   table matches the rules under `HostPage`. Leave: keys cleared.
2. Page independence: host HostPage=2, joiner enters by invite WITHOUT opening any map page and with `[Redirect]` page 0 pointing elsewhere;
   both load the same folder (log `expansion: slot F0n: ... -> <dir>` on both; compare archive hashes).
3. Stock round: HostPage=-1 and no rules: table all `-`; joiner with a `[Redirect]` ini loads stock; stock joiner unaffected.
4. Joiner without the folder: the hold engages, the game's missing-content text appears (or not: record), no countdown, nothing crashes.
5. Joiner with a changed map zip (one member differs): `klx_slots` token differs, hold, `kl_buildprint.py --compare` agrees.
6. Joiner with another Patch01.zip: `P=` differs, all non-stock slots held.
7. Host changes HostPage (ini edit + restart is not possible mid-lobby; use a second lobby) / changes the slot index mid-lobby: seq bumps, joiner
   re-adopts, gate waits for the ack, no wrong map loads.
8. Hookless joiner to a hooked host (non-stock slot held; stock slot allowed) and a hooked joiner to a stock host (`JoinedWithoutTable` 0 and 1).
9. Late joiner (joins after the table was written; no chat dependency).
10. Host quits during the countdown: `klbld_reset_lobby` runs, rules added at run time do no harm in the next stock game.
11. Whole round on a grafted map with two machines: scene refs agree (no desync/crash in the first minute), the round ends, stats are not written
    (klsteam verdict 2).
12. Hash parity: the in-hook `build: code` line equals `python tools/kl_buildprint.py` on both machines (not compared end to end yet, buildcheck 11).

## 9. Unproven (GUESS), in one list

* That role/mode detection (`kl_online()`) is true in the lobby window before the rules object exists; klhook.c answers 0 until then, so MapSync's
  joiner path must test "lobby seen", not `kl_online()`, to adopt early (klhook.c:250-264, comment and code; `re/hook_netcode_audit.md` s1).
* That the first `GetLobbyData` after join returns the host's keys (else retried, klbuild.c:843-847).
* That a runtime append to `kls_rule[]` is safe against a concurrent `kls_map` on a loader thread.
* That clearing a slot bit stops the host's countdown and shows a useful message (buildcheck 6, 8).
* That the client always reaches the archive open after the table is final (the ack gate is the defence; the load order is not traced).
* That a stock peer ignores unknown lobby/member keys (Steam stores them; the game has no LobbyDataUpdate_t handler, buildcheck 2).
* That the module cannot disturb a stock game: with `Enable=0` it must be one ini read and a return (the pattern of klbuild.c:21-22, 858-863).

## 10. Implemented 2026-10-25 (mapset_1025a): the cheap route, host-local, no sync

Built (TEST `klhook/out_mapset_1025a_test`, SHIP `klhook/out_mapset_1025a`). NOT run live. Data-only: no code byte of kl2.exe changes.
Only klslot.c changed (no klhook.c / klgrenade.c edit, no new include).

* (a) Diagnostics. Every open of a slot's `<slot>_Main.zip` (first 96) logs
  `expansion: LOAD F0n: latch=.. force=.. online=.. OnlineSet=.. keep=.. -> page P, rule <dir|none (stock level)>; stack [..]`
  plus a WARNING when online with a non-zero page. The stack text is the last window stack read (full names, `A > B > C`). The existing drop line
  now also prints online / OnlineSet / kept. Log=2 adds `menu windows [...]` for every stack change.
* (b) `[Expansion] OnlineSet=0|2|3` (default 0): while `kl_online()` is true (cached 250 ms), `kls_page_now()` answers that page whatever the latch says.
  `[Expansion] KeepPageOnline=1` (default 0, only with OnlineSet=0): the last expansion page latched in the OFFLINE menu (`kls_keep`) is used when
  the latch is 0 online. `KeepClear=1` (default 1) forgets it when a window name containing `MainMenu` is in the frontend stack (GUESS: that name;
  read it off the log). Offline nothing changes. Rows in tools/kl_mod_options.py: onlinedm (OnlineSet=2), onlinecamp (=3), keeppage; all rec off.
  Quick Match / public lobbies are NOT detectable here (lobby type is only seen by klmm.c's proxy, installed only with [Net] PrivateLobby/BuildKey),
  so the exclusion is the default-off key plus the label; a stricter guard is planned: have klmm_CreateLobby record the type and skip type 2.
* (c) Lobby titles: kllocname.c already asks `kls_page_now()`, so with `[Names] Enable=1 Override=1` the titles follow OnlineSet / the kept page for
  free. Not enabled by default (unproven, unchanged).
* (d) Both peers: the LOAD line warns. Lobby data key NOT implemented (klbuild.c is not included in klhook.c); plan stays sections 2-3: host writes
  `klx_maps`, joiner `klx_ack` via klbuild.c once it is included and run. Menu overlay toggler: plan only (element cap 5096, ~4793 used): one
  extra FA-lobby toggler text cycling OnlineSet 0/2/3 needs ~3 elements; do after klbuild is live.

Live test (two machines, same KLHook.ini on both, `[Expansion] Log=1`; SHIP dll + ini copies, game folder write by the owner):
1. Solo first: `[Expansion] OnlineSet=2`, Private Match with the stock lobby, pick any slot, Start. Read KLHook.log: the `LOAD F0n` line must show
   `online=1 ... page 2, rule DM..`. If `online=0` the detection did not fire in the lobby (section 9 first bullet): record it.
2. Same with `OnlineSet=0 KeepPageOnline=1`: open Arcade > Dead Men maps (log `page 2 kept`), back out to the main menu (log `kept page 2 forgotten` if
   MainMenu matched), then Private Match: kept=2 only if not forgotten; repeat without visiting the main menu.
3. System Link: same as 1 on both machines; both logs must show the same folder.
4. Refutation of the latch drop: with OnlineSet=0 and Page=-1, open HeistPlayMenu2 then go to Private Match; the drop line names the stack.
5. Quick Match with all keys 0: LOAD lines show page 0 (unchanged behaviour).
