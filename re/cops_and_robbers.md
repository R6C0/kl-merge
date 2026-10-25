# Cops and Robbers (C&R) in kl2.exe (2026-10-25, static; nothing here ran live)

C&R is NOT a separate game mode class. It is sub-mode 2 of the Fragile Alliance (FA) family: same session manager, same rules classes, same levels.

## 1. How it is built

- Session manager `ZSessionManagerMultiplayer` (global `sm` = [0x168e598], vtable 0xbd1ebc), game type `[sm+0x5c]` = 4 for the whole FA family (FA, Undercover Cop, C&R; Arcade Heist is 4 too but with `ZGameRulesHeist` 0xbd3514).
- **Sub-mode word `[0x168e59c]`: 0 = Fragile Alliance, 1 = Undercover Cop, 2 = Cops & Robbers.** 265 code references (list in the scratchpad `m59c.txt`; the main users are below).
- Rules classes: `ZGameRulesFragileAllianceSv` (0xbd2eb4, host) and `...Cl` (0xbd31e4, client). They branch on the sub-mode word; there is no C&R class.
- Selection: menu option / command line `-o FA2TeamMode` (UCC: `UndercoverCop`), read by 0x906ba0; 0x5721d0 sets the word from the toggle text ("TM"); the online create 0x6c9c10 passes the mode byte; it travels to clients as the Steam lobby data key `FAGameMode` (0x869430 writes name, Scenario, CoopDifficulty, FAGameMode, RoundTime, NumRounds, Ranked, Rank, GameType).
- Lobby selector `ZMercsFASelectorLobby` slot 10 = 0x7dc060 (3 stack args, key 0x7d/0x7e): in mode 2 the PLAYERS row is **6..12** (FA: 4..8) and the ROUNDS row floor is 4 with step 2 (FA: 3..5 step 1); time row 3..5 min in both. Host Ready (0x5a9920, message 0x7f) has a floor of 6 players in C&R, 4 otherwise.
- `ZGameRulesFragileAlliance` 0x822830 (per player) skips players whose `ZFFPlayer+0x273c == 3` (policeman) in the heist loop; C&R keeps them as the team that plays.

## 2. Teams and "how a player becomes a cop"

- A heister (`ZFFPlayer+0x273c == 2`, `eZFFP_TYPE_MULTIPLAYER_NORMAL`) who dies in plain FA becomes a policeman: rules slot 7 (0x827f00) -> 0x80ad60 -> 0x6bb910 picks `0x6ee860(client, 3, 0)` = the first free `ZFFPlayer` in the session player table (0x6161c0, 12-byte entries `{player*, ..., used byte +9}`) whose type byte is 3 (`eZFFP_TYPE_MULTIPLAYER_POLICEMAN`), places it at an `AFTER_DEATH` spawn through the RMCRespawn wrapper 0x63a0a0 and announces it (`RMCAnnounceFASpawnPolice`). Same picker is used at 0x426c70, 0x6cb2f5; the generic `(index, type, 0)` picker is 0x54cab0 (callers 0x42bdc9, 0x4b2929/0x4b2940, 0x6a20e5).
- C&R: the lobby splits the players into two teams at start; the level provides separate spawn sets: `TEAM_MERC` (6-8 points) with `TEAM_MERC1..4` sub-groups, `TEAM_POLICE` (6-8), UCC uses `UCC_MERC` (8). Team money stacks are `TeamModeDropMoney`; `OnlineSpawnpointTrigger` triggers the spawn. Team choice inputs: `TeamSpawnNext / Prev / Accept`, replicated by `m_iRespawnPointSelect` and `RMCSetRespawnIndex`.
- Levels: the 9 stock FA maps all carry the 16 `ZFFPlayer` (Hero_01..08 type 2 + RespawnPolice#01..08 type 3), `FA_START` x8, `AFTER_DEATH` x7-8, `TRAITOR` x4-6, and the team spawn sets. **Our Dead Men conversions lack the team/UCC sets**, so C&R cannot be offered on them yet (FA mode only).
- Scene includes: C&R uses the same `mainsceneincludes_multiplayer.zip`, no C&R-only include was found. The extra content is in the level (spawn sets, drop stacks).

## 3. What it gives us

(a) **More players.** C&R is the only mode the stock game lets reach 12 (lobby 6..12). It proves that 12 humans = 6 on `TEAM_MERC`-type seats + 6 on type-3 seats using the SAME 16 entities. See re/max_players.md: for FA 9..12 the cheapest seats are the type-3 ones.
(b) **Police-character choice after death.** The death path already has the right hooks: the picker takes `(client, type=3)`; the entity chosen carries the body/character. To let a dead player choose, replace the "first free" pick with "this specific" free type-3 entity (the used byte +9 of the entry is the lock), i.e. choose the index `i` the player picked in the wardrobe, then let 0x6bb910 continue unchanged. `m_iRespawnPointSelect` / TeamSpawnNext/Prev/Accept is the stock UI for choosing a spawn point and can carry the selection. Not built.
(c) **Teams and AI online.** In C&R the AI on the opposing team is not needed: the cops are humans. For FA with fewer humans the existing `[Bots] OnlineFill` plan (read-only so far, re/bots_online_fill.md) stays the AI route; C&R shows the team assignment happens at start in the rules Sv object and is replicated, which is where a human/AI mix per team would be hooked.

## 4. Open

- Where exactly the team list is built at start (rules Sv, not located by address yet).
- Whether the type-2 pick failing (-1, see max_players.md) is handled in C&R for team sizes above 8 (presumably team members beyond 8 use type-3 entities; unverified).
- Dead Men maps need team/UCC spawn sets authored before C&R can be offered there.
