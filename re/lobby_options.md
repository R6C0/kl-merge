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
