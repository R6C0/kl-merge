# FA lobby rows: Heist time / Number of rounds (2026-10-25, static, not run live)

Rows are code, not scene data (frontend.xml has no value list for them). Selector `MercsFASelectorFALobby`
(ZMercsFASelectorLobby, vtable 0xbbd364, slot 10 = 0x7dc060, 3 stack args, key 0x7d left / 0x7e right, focus row [self+0x88]).
Clamps are immediates: time 3..5 (left 0x7dc412, right 0x7dca71), rounds 3..5 (6 / floor 4 / step 2 in mode [0x168e59c]==2),
players 4..8 (6..12 in mode 2). Values: time = sm byte +0x4b + settings object vtbl+0xa4 (seconds, float) + store MP_TimeLimit (minutes);
rounds = settings object vtbl+0x9c (byte) + 0x5b5f30 + store MP_NumberOfRounds (n-1). Replicated as m_fRoundTime float / m_iNumRounds int8.
Reader tags LobbyTimeLimit / LobbyNumberOfRounds (0x62bdb7 / 0x62bd81) print "%d" with no clamp. No per-round tables found.
Implementation: klhook/kllobbyopt.c, [Lobby] TimeMax / TimeMin / RoundsMax (default 0 = stock), private vtable copy of the selector;
for a press the stock clamp would swallow it pre-sets 4, runs the stock handler, then re-applies the wanted value through the same setters.
Players above 8 not offered (FA spawn count and Steam lobby member limit unknown).

## Row order and keyboard navigation (2026-11-02, static read of 0x7dc060 + the SL7 / maps9 live evidence)
`[self+0x88]` is the focus row; rows below 0 are the option rows, rows 0..n-1 the player list (n = connected players,
`[self+0x8c]`, 0x698250). The LEFT jump table 0x7dcfa8 (and RIGHT's 0x7dcfc0) index `row + 6`:
`-6` co-op level (`CoopLobbyLevelNameToggler`, 0x7dc757), `-5` co-op difficulty (0x7dc6d2), `-4` FA level (`LobbyLevelNameToggler`, 0x7dc5ad),
`-3` Number of players (0x7dc4bb), `-2` Heist time (0x7dc3c7), `-1` Number of rounds (0x7dc2bc).
The FA lobby opens on row -4 (0x6a9830: 0x87c980 false = not the co-op lobby -> `-4`; the co-op lobby starts at `-6`).
Keys in slot 10: `0x7b` DOWN = row + 1, `0x7c` UP = row - 1 (FA: both clamp to -4 .. n-1), `0x7d` LEFT, `0x7e` RIGHT,
`0x7f` SELECT = Ready (0x5a9920, does not read the row), `0x81` / `0x82` -> 0x649a20 / 0x7fb0f0. LEFT / RIGHT never move the row.
So from the lobby's start: 1 x DOWN = players, 2 x DOWN = Heist time, 3 x DOWN = rounds, 4 x DOWN = player row 0; UP from player row 0 = rounds.
Gates on every option change (and on a move into a negative row): host in the lobby (0x8e6a20 == 0xd) and the menu store's
`MP_RankedGame` lookup (`[[[0xdd265c]+0x824] vt+0x14] -> vt+8("MP_RankedGame", 0)`) non-zero; both held in the SL7 run that
stepped the time row and in the maps9 scripts (DOWN DOWN reached Heist time), so a bench script can count on them.
Script for a 6-minute round (TimeMax >= 6 in the ini): after the map RIGHTs, `tap DOWN`, `tap DOWN`, `tap RIGHT`, `tap RIGHT`
(4 -> 5 stock, 5 -> 6 through kllobbyopt; expect `lobbyopt: Heist time 5 -> 6 (the stock clamp would have kept 5)`), Ready from any row.
