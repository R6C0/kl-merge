# Online bot voice: research + critique (10-28, ce)

## Research

**Report: online bot voice (gap #4). Static research only; nothing was edited, built or launched.**

**Short answer.** Arcade speech is a local, global (2D) "radio" line, not an actor-attached sound. A crew-record index is only needed to pick which voice (`_C<n>`) a per-character line uses, and to name the speaker on the HUD. A line can be played with no record by asking for a plain key. It is not replicated, so the host cannot make clients hear it. A new host-to-client packet is needed. `klk_say` in `kltalk.c` already does the playing side, online included.

### (1) How Arcade bot speech is triggered
- **Entry point.** `0x58a070(this = speech manager [0x168e958], group, otherLine, speaker, x)`, ret 0x10, e.g. `push 0; push spk; push 0; lea edx,[mgr+0x390]; call 0x58a070` at 0x4dc1ac..0x4dc1b8.
  - It picks one of the group's lines at random.
  - A group stays silent for 15.0 s after speaking.
  - It then calls `0x421c70(line, other, speaker, x)` (ret 0x10), which calls `0x578840(queue = [mgr+0x974], entry, prio, speaker, float, last)`, which calls `0x7d0e80`, which starts the sound.
  - `0x421c70` returns at once if `[mgr+0x956] != 0` or `[[0x168e598]+0x15d] == 0`.
- **The index in the Arcade branch.** The branch at 0x421cc7 is taken when `0x7f6850` is true, i.e. mode `[0x168e598+0x5c] == 4`. The speaker byte indexes the Arcade voice table through `0x6ae750`: `entry = list[ byte[rules+0x33e+slot] ]` (0x421dd1 and 0x421df8 call it). That byte is filled by `0x588980` as `groupname[0x12] - '1'`.
  - Speaker -2 (0xfe) picks a random in-round slot.
  - Speaker -6 (0xfa) picks entry 8 (Glazer).
  - A null entry falls back to `K_C1`.
- **Plain lines (flag 0).** `0x4220c2` ignores the table. It takes `[line]` and calls `0x578840` directly, so a plain key needs no record.
- **Speech in stock Arcade for bots is event-only.** Callers of `0x58a070` pass a rules slot. Examples: `0x6da1ed` (escaped, group at mgr+0x468), `0x4dc180` and `0x721190` (jackpot, g38, mgr+0x390), `0x426da0` (reach loot, g39, mgr+0x3a8), `0x407370` (exit loot, g40), `0x4060c0` (left behind), `0x65c620` (bribe), `0x67ee80` (backstab).
  - A bot only speaks when one of these fires with its slot (confirmed for the traitor routine only).
  - Whether a bot's own pickup fires jackpot was not traced (GUESS).
  - Beyond that, the hook's own Arcade chatter in `kltalk.c` supplies bot banter: `klk_chatter_say` at `kltalk.c:626` calls `klk_say` at `kltalk.c:471`.
  - Source docs: `re/bots_voice.md` sections 1.2 to 1.4; `re/voice_fields.json` gives field to group offset.

### (2) Can it be played without a crew record?
- **Yes, as a plain line, with a negative speaker.** This is what `klk_say` does: it calls `0x828fa0(key, entry)` for the entry (`klk_entry`, `kltalk.c:~440`), builds a 0x34-byte line with flag 0 and priority -1, and calls `0x421c70(mgr, line, 0, rec, 0)` (`kltalk.c:508-509`).
- **Which speaker byte.** `0x7d0e80` maps -6 and -2 to speaker object `[this+0xe0]` (crew), -4 to `+0xdc` (driver), and -3 and -5 to `+0xe4` (police/UC). The jump table is at 0x7d10c4.
  - -1 or a record that is not in use makes `0x7d0e80` answer 0 after the sound has started, so the line is queued and said twice. Avoid it.
  - On the plain path, -2 is rewritten at 0x4220e0 into a real slot by `0x5977b0`, and the HUD would then name a human. **Use -6 for bots.** Using the crew object `+0xe0` for the HUD portrait is a GUESS.
- **Speech is not positional.** `0x7d0ef0..0x7d0f98` starts the sound through the sound system `[[0xdd2640]+0xb00]` (vt+0x12c, then `0x659370(h)`), sets `[h+0x84] |= 0x20` and `&= ~4`, and passes no world position. It is global, like an Arcade bot's line.
  - Positional options exist: the player speech component `0x4a7860([player+0x840], slot)` needs a voice set that FA bots lack, and the 3D `+0x128` call via `0x467e00` is described in `klshot2d.c:1-60`.
  - Neither is Arcade behaviour. **Do not use them.**
- **Gate.** `0x7d0e80` calls `0x4658f0` when `last == 0`, so a dead or aboard local player silences the line. The same gate applies in Arcade.

### (3) Will clients hear the host's line?
- **No.** `0x421c70`, `0x578840` and `0x7d0e80` contain no network call. Each peer plays its own speech from its own rules events.
- **Online branch.** The online branch of `0x421c70` is at 0x421f07. For a slot speaker it uses `0x817160(session, slot, 8)`, which is the session virtual `+0x3c`, through the jump table 0x422170. That is the seat-to-voice mapping (GUESS V1 in `klvoice_online.c:11` says voice number = seat).
  - Speaker < 0 or a null entry falls to entry 0 (0x422063).
  - `0x7bb2a0` returns the rules object only in mode 4; it is null otherwise.
- **`kltalk.c` online path.** `klk_say` already runs online (`kltalk.c:487`, gated by `[Voice] OnlineTalk`). It plays a local line and sends nothing (`kltalk.c:938`). It has never been proven live (the A1SND bench was silent, now fixed).
- **So a new packet is needed:** host says "bot digit D, event E, variant V"; every seat, the host included, plays the line locally.
- **Packet transport.** The `KLSYL` precedent is the format at `klcrewlook.c:13-27`, sent at `klcrewlook.c:197`. The receive dispatch is `klsync.c:1043-1044`; add one line for the new magic.

### (4) Minimal design: `[BotFill] OnlineVoice=0|1|2`
- **Mode 0** is off. **Mode 1** is on. **Mode 2** logs only (no packet, no call to `0x421c70`).
- **Needs** `[Voice] Enable=1`, `[BotFill] OnlineLooks=1` (for the digit-to-character table), and the `kltalk.c` online gates (`OnlineTalk` and `Online`). Off on stock maps unless the keys exist; stock `.LOC`s hold the stock `_C<n>` leaves, so stock maps should work (GUESS).
- **New file** `klhook/klbotvoice.c`, included after `klcrewlook.c`. Add the dispatch line in `klsync.c` after line 1044 and the tick call next to `klcl_tick`.
- **Packet** `KLSYV`, UDP 27415, host broadcast, little endian:

  | offset | size | field |
  |---|---|---|
  | 0 | 8 | `"KLSYV\0\0\0"` |
  | 8 | u32 | host `klsy_T()` |
  | 12 | u16 | seq, a new value per event; the client drops stale or duplicate seqs |
  | 14 | u8 | ver = 1 |
  | 15 | u8 | event id |
  | 16 | u8 | digit, 2..8 (`klcrewlook.c`'s key) |
  | 17 | u8 | variant 1..3 |
  | 18 | u16 | 0 |

  A single record per event. Resend three times at 100 ms (UDP); the client drops repeats by seq.
- **Client play.** It resolves a key and calls `klk_say(key, -6, ...)`. The key is `<event key>_C<digit>`. It is the stock per-character key (the table byte is `digit-1` and the leaf is `K_C(byte+1)`). If the bot has a Dead Men body (`klw_r` or `klcl` look), use `KLVoice/<Name>/<event>` as `klvoice.c` does.
  - No leaf means no line; `klk_entry` logs once.
  - Per-bot-per-event gap of at least 15 s (the game's group gap) and a global gap of at least 2 s. A line is dropped if the queue is full (the queue holds 10).
- **Events and host sites** (all host-side data reads, no code patch):

  | event | host site | line (GUESS on each key) |
  |---|---|---|
  | grabbed loot | `klbotfill.c:1134` and `:1168` (GRABBED log lines) | Jackpot (g38, `FA_JackPot_0n` on DM maps; stock key name not found) or `ReachlootArea_01_R` |
  | leaving loot area | the same site once the stack is released | `ExitLootArea_01_R` |
  | downed | `klbotdown.c` down function `KLBD_DOWNFN` 0x70e0e0 (line 74) | none exists in FA (`bots_voice.md` section 0.2). Story `AllLevels/Oneliners/DownNotDead` is a GUESS; skip in v1 |
  | died | `klbotfill.c:1093` (slot freed) | none. Skip |
  | escaping | board loop `klbotfill.c:850-855` (`phase == 3`, "banked") | `FA_YouEscaped0n` (g47) |
  | spotted cops | no hook site exists | GUESS: a host poll of bot-to-cop distance, or `kltalk.c`'s `KLK_ON_FEDKILL`. Defer; no FA line |

- **Reuse of banter.** For idle and combat chatter, extend `klk_who_any` (`kltalk.c:722`) with pseudo-members per bot (voice = digit-1; `kltalk.c:606` already uses `rec` as voice online). Host decides, the packet carries the key id. This is the larger part and can follow v1.
- **GUESSes to settle with the mode-2 log first:**
  1. Speaker -6 gives the right HUD name and plays on a client with no record.
  2. `[rules+0x2c]` is non-null on a client (the `OnlineTalkNoScore` gate).
  3. The key-name spellings of Jackpot and YouEscaped on stock `.LOC`s (`re/voiceplain_1023.md:53` has `Multiplayer/F01/FA_YouEscaped01_R`).
  4. Client digit equals host digit for the same bot (shared with `OnlineLooks`, `crew_online_1028.md` GUESS 1).
  5. Entry cache scene key online (`klk_entry` keys on the rules pointer and scene).
- **Risks.** A bad digit passed to the list accessor `0x51ab20` is an int3 at 0x51ab2d (bounds 0..count). Always pass an explicit key rather than the table index. The `rules+0x33e` write is not possible online (the rules object is 0x3a8 or 0x334 bytes; `crew_online_1028.md` section 1).

### Files and addresses
- Paths are under `C:\kl-merge\wt\wk-lpbal\`: `klhook\klcrewlook.c`, `klhook\kltalk.c`, `klhook\klbotfill.c`, `klhook\klbotdown.c`, `klhook\klsync.c`, `klhook\klvoice_online.c`, `re\bots_voice.md`, `re\voice_fields.json`, `re\crew_online_1028.md`, `re\hook_review_talk.md`, `re\gun_ui_sounds_1028.md`.
- Exe addresses: `0x58a070`, `0x421c70`, `0x421f07`, `0x4220c2`, `0x578840`, `0x7d0e80`, `0x7d10c4`, `0x4658f0`, `0x6ae750`, `0x817160`, `0x7bb2a0`, `0x7f6850`, `0x5977b0`, `0x828fa0`, `0x588980`.

## Critique and final spec

**Verdict: feasible on host and client, risk low-to-moderate, with the corrections below. Nothing was built or run, and several points can only be settled live, so they stay GUESSes.**

**Verified by reading the code and disassembling `kl2.exe`**
- `kltalk.c`:
  - `klk_say` is at 471 and `klk_chatter_say` at 626. The 0x421c70 call (`mgr, 0, line, 0, rec, 0`) matches the signature `(this, line, other, speaker, last)`, and the line is built with flag 0 and priority -1.
  - `klk_who_any` is at 722. The `KLK_MANAGER`, `KLK_LOOKUP` and `KLK_SAY` defines are at 142-144.
  - The line 938 log says "nothing is sent".
- `klcrewlook.c`: the KLSYL format is at 13-27 and the send at 197.
- `klsync.c`: the KLSYL and KLSYB dispatch is at 1043-1044.
- `klbotfill.c`: the GRABBED log lines are at 1134 and 1168, the slot-free block is at 1091-1093 and the phase-3 "banked" loop is at 850-855.
- `klbotdown.c`: `KLBD_DOWNFN` 0x70e0e0 is at line 74.
- Exe:
  - `0x4220c2` is the plain-line path. It tests `[esi]` and calls `0x578840` directly.
  - `0x4220e0` rewrites speaker 0xfe through `0x5977b0`, as claimed.
  - `0x7d0e80` takes `ret 0xc` and starts the sound through `[0xdd2640]+0xb00`.
  - The lookup and say code bytes in `klk_say` match the exe.
  - `kltalk.c` already calls `klk_say` with a negative speaker (-3 at line 692), so a plain line with a negative speaker is existing practice.

**Wrong or unsupported in the research**
1. **GUESS V1 cite.** It is at `klvoice_online.c:7`, with the diag at line 81. Line 11 is GUESS V2.
2. **`klk_say` signature.** The call is `klk_say(key, rec, rt, what, rules, scene)`, not `klk_say(key, -6, ...)`. A client needs a `rules` pointer and a scene string.
3. **Client gate.** For online rules, `klk_say` returns 0 unless `OnlineTalkNoScore` is on and `[rules+0x2c]` is non-null. This is a hard requirement, not just a guess to log. `[BotFill] OnlineVoice` therefore also needs `OnlineTalkNoScore=1`.
4. **`0x421cc7`.** My disassembly at that address is mis-aligned. The `0x7f6850` mode-4 test and the `0x6ae750` indexing are not confirmed by what I read, so treat them as unverified. They don't affect the design, because the plain path never touches the table.
5. **Speaker -6.** Plain-path -6 is only supported as the crew object at `[this+0xe0]` through the `0x7d0e80` jump table. I did not re-read that table, and it must be checked in the mode-2 log first.
6. **Event keys.** Jackpot and `YouEscaped` spellings are unverified. The only evidence is `Multiplayer/F01/FA_YouEscaped01_R`.

**Corrected final spec**
- **Config.** `[BotFill] OnlineVoice=0|1|2` (0 off, 1 on, 2 log only). It needs `[Voice] Enable=1` and `Online=1`, `OnlineTalk=1`, `OnlineTalkNoScore=1` and `OnlineLooks=1`.
- **New file.** `klhook/klbotvoice.c`, included after `klcrewlook.c`. In `klsync.c`, add `KLSYV` to the dispatch after line 1044, plus a tick call next to `klcl_tick`.
- **Packet `KLSYV`.** UDP 27415, host broadcast, little endian.

  | offset | size | field |
  |---|---|---|
  | 0 | 8 | `"KLSYV\0\0\0"` |
  | 8 | u32 | `klsy_T()` |
  | 12 | u16 | seq |
  | 14 | u8 | ver 1 |
  | 15 | u8 | event |
  | 16 | u8 | digit 2..8 |
  | 17 | u8 | variant |
  | 18 | u16 | 0 |

  - Send it 3 times at 100 ms. The client drops repeated seqs and any packet shorter than 20 bytes.
  - Validate the digit against the `OnlineLooks` table before use.
  - The host also plays the line locally, from the same code path.
- **Client play.**
  - Build the key `<event>_C<digit>`, or `KLVoice/<Name>/<event>` for a Dead Men body.
  - Call `klk_say(key, -6, rt, what, rules, scene)`. Always pass an explicit key, never a table index (0x51ab2d is an int3 on a bad index).
  - Limits: a per-bot-per-event gap of at least 15 s, a global gap of at least 2 s, and no say when the queue count is above 8.
- **v1 events.** Only loot grab (`klbotfill.c:1134` and `:1168`, the grab, using `ReachlootArea` or Jackpot) and boarded/escaped (`:850-855`).
  - Leaving the loot area is deferred. The research named no distinct host site for it, only "the same site once the stack is released".
  - Down, death and spotted-cops are deferred (no FA line exists).
  - Jackpot's trigger is not traced, so keep it behind mode 2 until the log shows the key resolves.
- **First-live settle list**, using mode 2, then mode 1 with 1 bot and 1 client:
  1. -6 plays on a client with no record, and the HUD name is acceptable.
  2. `[rules+0x2c]` is non-null on the client.
  3. The key spellings resolve on stock `.LOC`s.
  4. The host digit equals the client digit.
  5. `klk_entry`'s scene cache key is correct online.
- **Risk.** Low in the host path (data reads, no code patch). The main crash risk is the unconfirmed -6 speaker routing, so ship mode 2 first. A queue overflow is guarded by the count check, and `klk_say` already refuses on a code-byte mismatch.
