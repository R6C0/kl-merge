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
| build code, offline | `tools/kl_buildprint.py` (compute :184, compare :256), in-hook twin `klbld_full_*` (klbuild.c:511-580) |

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
  HostPage while `kls_online_host` is set. This makes the stage-0 `[Expansion] Page=N` unnecessary and does not touch the offline path.
* v1 has no in-lobby map-page UI: the page is a host ini value. A selector inside FALobby needs a menu change (`re/menus.md`, the nine
  slot entries are fixed, TO FIND: the widget behind `MP_SelectedLevel`, key `0xb6d6e4`, buildcheck 5.5). GUESS that it is not worth
  it before the ini route is proven.
* Which slot is loaded needs no hook code at all: the game's own index (host `0x6c53db`, client `0x491fd1`) picks the entry of the table.

### 4.3 Joiner-side: adopting the table

* The joiner tick (klbuild.c:815-853) is extended: next to `klx_slots` it reads `klx_maps` (same `RequestLobbyData` retry, same
  `klbld_joiner_tries`) and, when the string is well formed (folder names pass the `kls_plain` rule, klslot.c:483, `<=47` chars, `S=` present),
  stores it in a small table `kls_net_dir[9][48]` with a volatile `kls_net_seq` (written last).
* `kls_map` is changed (proposed) at klslot.c:286-287: if `[MapSync]` is on, this machine is in a network session (`kl_online()`) and
  `kls_net_seq != 0`, the rule for slot `s` is NOT `kls_find_rule(s, page)` but the rule whose `.slot` is `s` and `.map` equals
  `kls_net_dir[s]` (case-blind, as klmm/klbuild compare), or "stock" when the entry is `-`. This is authoritative in both directions:
  a joiner whose own `[Redirect]` page 0 maps F01 to a Dead Men map still loads STOCK F01 when the host says `-`.
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
   klbuild.c:91) sets the bit of the slots that are non-stock in the table in `want`, so the existing mask hold stops the countdown
   (klbuild.c:742-756). A member WITHOUT the hook counts as stock (klbuild.c:803-808): it differs on every non-stock slot, hold as
   today.
5. The countdown then runs, the game loads `Locations/Fxx/Fxx_Main` on the host: `kls_map` picks the same table entry.

JOINER:
1. Join (invite, `+connect_lobby`, browser). `klbld_GetLobbyOwner` records the lobby (klbuild.c:697-703).
2. NEW: tick reads `klx_maps` and `klx_slots`, retrying `RequestLobbyData` (klbuild.c:843-847). Adopts the table (4.3). Computes `klx_fp`
   from the ADOPTED folders; publishes `klx_fp` and `klx_ack`.
3. Compare per slot with `klbld_diff`. A differing slot (file missing, other content, other Patch01) clears that slot's bit in the joiner's own
   mask (klbuild.c:742-756). The game then shows its own "missing content" text for a slot it thinks it does not own
   (`Online/MissingContentPackClient`, kl2 0x6c4bcd / 0x6c4e07, `re/netcode_fa.md` 1.2), which is the only player-visible message this design
   relies on. The clear is the same trick that is already written; its effect on the HOST's gate (replicated `m_iAvailableLevels`) is a GUESS
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
  holds the start on any non-stock slot, never on a stock one (klbuild.c:42, 155).

## 5. Failure cases

| case | detection | reaction |
|---|---|---|
| joiner lacks the host's map folder | its `kls_net_dir[s]` has no folder / `klbld_rule_token` = `MISSING` (klbuild.c:592) | log `mapsync: slot F0n: map <dir> not installed`; clear the slot bit (own mask hold); `klx_ack=-` so the host holds. Do NOT let `Fallback=1` (klslot.c:296-297) quietly use the stock file: under MapSync an announced slot with no file is `Fallback=0` (the open fails) in case the hold failed. GUESS: a failed open of the archive ends in a crash or a stuck load; hence the primary defence is the hold |
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

1. The widget behind `MP_SelectedLevel` (key `0xb6d6e4`, read at `0x6c4d02..0x6c4d16`) and how the FALobby selector reaches `0x746570`; needed
   only for an in-lobby page chooser (not v1). (buildcheck 5.5)
2. Whether `m_iAvailableLevels` is re-sent after the lobby forms, i.e. whether a joiner-side mask clear reaches the host's gate (the DDL send
   path; buildcheck 8). Decides whether the joiner can refuse by itself.
3. The time of `0x491f50` (client level name) relative to the first open of `<slot>_Main.zip` and the thread of the call, to prove the table is
   read-only at that moment; and which thread runs the CreateFile wrappers (klslot.c:320-336) during a load.
4. A text-set call for a lobby message (the label that shows `Online/MissingContentPackClient`, `0x6c4e07`) to name the missing map to the
   player.
5. The caller of the `JoinSession` second argument (private/ranked bit on a client, `re/netcode_fa.md` 1.2) so PrivateOnly can be tested on a joiner.
6. `ISteamFriends` GetFriendPersonaName offset to name the mismatched member (buildcheck 8).

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
  joiner path must test "lobby seen", not `kl_online()`, to adopt early (klhook.c:263 comment in the audit, section 1).
* That the first `GetLobbyData` after join returns the host's keys (else retried, klbuild.c:843-847).
* That a runtime append to `kls_rule[]` is safe against a concurrent `kls_map` on a loader thread.
* That clearing a slot bit stops the host's countdown and shows a useful message (buildcheck 6, 8).
* That the client always reaches the archive open after the table is final (the ack gate is the defence; the load order is not traced).
* That a stock peer ignores unknown lobby/member keys (Steam stores them; the game has no LobbyDataUpdate_t handler, buildcheck 2).
* That the module cannot disturb a stock game: with `Enable=0` it must be one ini read and a return (the pattern of klbuild.c:21-22, 858-863).
