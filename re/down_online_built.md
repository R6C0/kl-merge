# Down online: what was built (2026-10-26)

Built, NOT run in the game (no live test was made; the harness ran off-game). Source: `klhook/kldown.c` (block at `KLD_KEEPUP`, `kld_o_*`), `klhook/kldown_hold.h` (pure meter), `klhook/kldown_hold_test.c` (harness), `[Down]` comments in `klhook/KLHook.ini`. Reads it follows: `re/downed_online.md`, `re/down_online_read_a.md`, `re/down_online_read_b.md`.

## Keys ([Down], all read at start; Enable=1 is needed)
| Key | Default | Meaning |
|---|---|---|
| Online | 0 in code (ini: recommended on) | also act in an online FA / UCC / C&R round for this machine's own non-police player, stock and expansion maps alike |
| MashHold | 1 (read only online) | hold the get-up until the mash meter is full (recommended on); 0 = stock one-press get-up |
| MashNeed / MashPer / MashDecay | 8 / 1.0 / 1.5 | meter in presses: need, added per press, lost per second (GUESS numbers) |
| MashMax | 25 s | the hold gives up after this long lying (0 = never): a hold must not be a trap |
| MashKey / MashPad / MashPadBtn | 0x43 (C) / 1 / 0x1000 (A) | where presses are counted from (GUESS: pad Cover button not read) |
| MashHoldHow | 2 (recommended on) | 2 = hold ONLY the Cover key / pad button (he can still crawl, aim, shoot while down, like Arcade); 1 = the old input-mask bit 0x80 (blocks fire / aim / grenade / use too) |
| MashScan | 0 | DIK scan code of the Cover key the game reads; 0 = derived from MashKey (MapVirtualKey; 0x2e for C). Set it if Cover is rebound to a key whose scan code differs from MashKey's |

Online=0: `kld_o_gate` answers 0 at once, `kld_o.cur` stays 0, every added condition is neutral: Arcade is unchanged (compiled the same flow; not byte-identical machine code, behaviour identical by reading).

## What happens online
- Gate `kld_o_gate`: session type [0x168e598+0x5c]==4, rules vtable Sv/Cl (`KLH_RULES_SV_OK/CL_OK`, so klroundkeep/klucc_down private copies pass), sub-mode [0x168e59c] 0..2. Arcade's `klr_arcade` (Heist rules) is tried first and wins.
- Own player: `klco_table` + `klco_find_own` (klcharonline.c; forward prototypes), cached 2 s. Police body: nothing acts.
- `kld.flop` is swapped to 0 at run time (`kld_o_mode`, teardown of the old mode first). Round line says why: a belly clip is a write into this machine's own animation pool, and no read showed a replica plays it (read A Q3: GUESS). The stock fall is kept; never desync on purpose.
- Speed-the-clip mash (channel fps + two end ticks): skipped online (local-only write).
- Hold (MashHoldHow=1, the old way): input mask bit 0x80 (same dword NoFire uses) while D state is 2 or 1; it also gates TapFire / HoldFire / aim / grenade / use, so a downed player could not shoot (the owner's complaint). MashHoldHow=2 (default) replaces it, see the next section; meter counts key edges from GetAsyncKeyState / XInput only while lying (state 1); full meter (or MashMax) -> bit off -> one real press runs the stock get-up and its GettingUp RMC. The bit is only taken off where this part set it.
- Off online: Vulnerable ([0xceb40c] would freeze every player's down state), DownFromCop/Crew factors, point-blank cap, Bots. Kept: tuning object numbers (victim applies), NoFire, camera, tap prompt (its bar shows the meter, full bar = press now), Dry=1 (meter runs and logs "hold WOULD be on", nothing written).
- One round line (`down: online: ROUND ...`) at state 0x19 with all numbers; a start line `down: online: Online=...` at init.
- UCC (sub-mode 1): acts too; klucc_down writes only the hit delta and does not touch the tuning object or the mask, so no conflict is read (GUESS; read B said yield).

## Cover-only hold (MashHoldHow=2, 2026-10-26, built, NOT run live)
- Keyboard: `klrigid.c` (SHIP and TEST; klauto.c is TEST only, so the filter could not live there) wraps the SysKeyboard device in its DirectInput proxy ONLY when kldown armed it at start (`klkf_armed`: Enable=1 Online=1 MashHold=1 MashHoldHow=2 and a scan code). The proxy's GetDeviceData / GetDeviceState pass everything through unless `klkf_scan` (volatile, a DIK code) is non-zero. kldown sets it only while the hold is on and clears it in `kld_o_release`, which every release path calls (death, round end, police body, mode change, MashMax bound, unreadable D, no key source, meter full, get-up running); the stalled-game-thread fallback also clears it. In a TEST build the proxy sits on top of klauto's, so a script's Cover press is hidden only while the hold is on; with the hold off nothing changes.
- The pure part is in `kldown_hold.h` (`kldh_filter_events`, `kldh_filter_state`): drops the Cover key's press events and the release of a press it dropped, keeps every other event in order, returns the fixed count; a key already down when the hold began keeps its release (the game is never left with a key it thinks is down). DIGDD_PEEK reads filter a copy of the state so the real read sees the same.
- The meter keeps counting the hidden presses: it reads GetAsyncKeyState (user32's async key table), not DirectInput's buffer. By API design; not seen live.
- Pad: kl2.exe has no named XInput import; it imports `XINPUT1_3.dll` by ORDINAL (2 and 3, IAT 0xb10728 / 0xb10724; class `ZXInputGameControl`). Ordinal 2 of xinput1_3 is XInputGetState; kldown proves that at run time (`GetProcAddress` by ordinal equals by name) and only then points that one IAT slot at a filter that clears the MashPadBtn bit (A, 0x1000) from `wButtons` (+4 of XINPUT_STATE) while the hold is on. Triggers, sticks, other buttons pass, so the pad can fire while down. The meter's own pad read calls the DLL directly, so it still sees A. If the slot is not resolved yet it is retried once a second (40 tries); if it cannot be wrapped, the old bit-0x80 hold is used ONLY while a pad is the active input (a button pressed in the last 5 s) and the log says that this hold also blocks fire.
- Logs: `down: online: MashHoldHow=2: ...` at start, `pad: ... wrapped`, `HOLD on ... fire, aim and grenade work while he lies`, `hold off (why): the Cover key / pad filter is off`.

## Harness
`kldown_hold_test.c`: 82 checks, 0 failed (the 13 new ones: the Cover filter drops only the Cover scan code, press and release, keeps order, fixes the count, keeps a pre-held key's release, no-op when off / scan 0 / empty, 20-byte event, GetDeviceState clear; the old ones: fall holds, no pre-charge, 6/s frees in ~1.8 s, 3/s ~5 s, 1/s never, held key counts once, key held through landing, hitch clamp, time bound incl. clock wrap, death reset, second down fresh, NaN dt).

## Open GUESSES
1. Input slot 12 vs 0x47cd80 order: not needed (the mask gates the action in slot 7), but that bit 0x80 also blocks TapCover on THIS build online is read, not seen.
2. Cover default key C and pad A; owner rebinding needs MashKey.
3. Rules/session objects answer the same on a client as on a host.
4. Local-player finder on a client (klco bench L3/L4 said the gamedata slot fails there; the master test is a GUESS).
5. The stock press after release reaches the replica as GettingUp (read A Q1/Q3: replica apply not read).
6. Meter numbers; MashMax 25 s.
7. MashHoldHow=2: the game reads the keyboard ONLY through the buffered GetDeviceData / GetDeviceState (no raw input / WM_KEYDOWN for Cover); A is the pad's Cover button and the game reads the pad ONLY through the xinput1_3 import (no DirectInput pad); the Cover key is C unless MashKey / MashScan say otherwise. Not read in code or seen live.

## Bench plan (2 instances, System Link, after a normal FA bench)
1. TEST build + `KLHook.ini` from `out_downonline_1026_test`, `[Down] Enable=1 Online=1 Log=1`, both instances; host FA on a stock map, then an expansion map.
2. Down the client (shots): log `down: online: HOLD on`, bar on screen; press C slowly (stays), mash (log `METER FULL`), one press: get-up at stock speed; host sees him rise (no stuck prone). Repeat as host.
3. Check `ROUND` line, no `kld.flop` writes, no crash; MashMax timeout (do not press); death while held (bit released); UCC and C&R round.
3b. While down: fire works (LMB shoots, aim works, grenade throws) on keyboard and, with a pad, RT fires; press C slowly (stays down, meter log), mash (METER FULL), one press gets up. A key held through the start of the hold (C down when he falls) must not stick afterwards. Pad: look for the `pad: ... wrapped` line; if it says not wrapped, the pad fallback line must appear instead.
4. Steam: same with a Steam lobby once System Link passes; focus loss mid-hold must free him at MashMax.
