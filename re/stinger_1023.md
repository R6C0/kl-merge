# Event stingers, 2026-10-23 (branch feat/1023-stinger) - BUILT, NEVER RUN IN THE GAME

Owner wish: "make the maps feel more engaging and lively ... more unique sounds ... more payday music n stuff, just make it more lively
all around". klmusic.c is a mood jukebox, klambience.c plays timed one-shots; neither reacts to a single thing a player DID. klstinger.c plays
ONE short cue (3 to 10 s) the moment the round does something. Everything is off by default ([Stinger] Enable=0, and an event with an empty
list stays silent). The code only READS game memory (no write, no patch, no game call); sound goes through the winmm MCI worker thread
pattern of klambience.c (own aliases kst0 / kst1, beside kmua/kmub and kamb/kam0..3).

## Events and signals (all existing reads; GUESS = unproven offset or meaning)
| Event   | Fires when | Signal |
|---------|------------|--------|
| Loud    | the heist goes loud | a heister's heist stage (record +0x78) >= 1, or LoudAfter s into the round (GUESS: no police signal is known) |
| Loot    | crew money rose above the start value (first rise; LootEvery=1 = every rise) | klb_read money sum (same as klmusic/klambience) |
| Down    | a heister is down | human: [player+0x2948][+4] != 0 (kldown.c); bot: [actor+0x64c] == 1 (GUESS: klbotdown.c says the down goal sets it; if the stock game also uses it for something else a bot cues "down" there) |
| Dead    | a record's status became 7 | klb_read record (any heister, you too) |
| Betray  | traitor flag (flags +0x79 bit 2) 0 -> 1 | klb_read record; tactic, Backstab, BackstabCrew, Bribe all set it |
| Last30  | van waits (rules+0x1dc 3..4) and timer (rules+0x1d8) <= LastSec | GUESS: that timer is the van wait, not a round clock; suppressed if the wait began within LastSec+5 s (would fire with Open) |
| Open    | van state < 3 -> 3..5 | rules+0x1dc (klmusic's "escape coming") |
| Reached | YOU aboard (status 4) or escaped (6) | your klb_read record |

Edges are seen between two 250 ms passes. A record's first sight and the first 8 s of a round only set the baseline (no cue on a joined or
restarted round). Silent: no round, online (kl_online()), `[Solo]` bench unless SoloPlay=1, `[Stinger.<key>] Enable=0`. A playing cue is left
to finish at round end (so Reached is heard). Anti-spam: per event Cool (s), Max (per round, 0 = none), Chance (%), global Gap (s) with
priority (Reached > Betray > Open > Last30 > Dead > Down > Loot > Loud: a lower one inside the gap is DROPPED, not delayed), no same clip
twice in a row, two MCI slots (a third cue cuts the oldest).

## ini keys (KLHook.ini)
```
[Stinger]
Enable=0            ; 1 = on
Volume=70           ; 0..100 master (per event Vol multiplies)
Folder=<dir>        ; the lists below are relative to it
Gap=3  LoudAfter=45 (0 = stage only)  LastSec=30  LootEvery=0  SoloPlay=0
Log=1               ; 2 = also log why a cue was dropped
Loud=loud\loud_1.mp3;loud\loud_2.mp3     ; same form: Loot Down Dead Betray Last30 Open Reached
LoudVol= LoudCool= LoudMax= LoudChance=  ; per event; defaults (all GUESS, unheard):
;   Loud 75/0s/1/100%  Loot 65/0/1/100  Down 65/15/0/80  Dead 70/8/0/100  Betray 80/10/0/100  Last30 70/0/1/100  Open 70/0/1/100  Reached 75/0/1/100
[Stinger.DM01B]     ; the same keys for one map (map key as klmusic.c: DM01B, F02 ...); Enable=0 silences it
```
Log lines: `stinger: on ...`, `stinger: map <key>: Loud n / Loot n ... clips, volume v, gap g s`, `stinger: <Event> <file> (<why>; map <key>, round second N)`,
`stinger: MCI '...' failed`, `stinger: <list>: '<path>' is not there - dropped`.

## Clips (staged, not committed): `python tools/kl_stinger.py build | ini | check | package [--dll SHIP.dll]`
Output `<work>\build\stinger_1023` (G:, 3.5 MB incl. the 1.2 MB dll): 8 folders, 24 mp3 (stereo 44.1 kHz 96 kbps, 3 to 10 s, 20 ms fade in, 1.2 s fade
out, loudnorm -20 LUFS), MANIFEST.txt (which source made which file), KLHook.stinger.patch.ini, INSTALL/UNDO bats, stinger_1023.ps1, dll\dinput8.dll (SHIP).
Sources: 21 Dog Days PC_Def.str `SFX/Music/Music_Moments/*` phrases (IMA-ADPCM one-shot music moments) and 3 Payday 2 excerpts from `<work>\pd2\audio\wav`
(razormind 0..7 s -> loud, deathwish 30..38 s -> betray, music_121224598 0..10 s -> reached). `check`: 0 problems (all exist, decode, 0.5..12.5 s, mean volume above -50 dB).
GUESS: which phrase suits which event is chosen from the FILE NAMES and the PD2 offsets are blind. Nobody has listened. The lead should play the
folders once and edit SPEC in tools/kl_stinger.py (or the lists in the ini); no code depends on the choice.

## Install / undo (the owner or lead runs it; the agent did not touch the game folder)
`INSTALL stinger 1023.bat` (add `-Dll` for the package hook): refuses while kl2.exe runs; copies the clips to `<DD>\KLExpansion\Stinger` with an md5
check; appends the `[Stinger]` block between `; stinger-1023 block (tools/kl_stinger.py)` and `; stinger-1023 block end` (Folder= rewritten); makes a
timestamped ini copy for manual recovery only. `-Dll` refuses unless the live dinput8.dll equals the backup `.before-1023stg` or the package dll.
`UNDO stinger 1023.bat` (`-Dll` puts the old dll back): removes only the marker block and `KLExpansion\Stinger`. Tested on a fake DD folder copy only
(`-SkipRunCheck`): install, repeat (idempotent), `-Dll` refusal on a foreign dll, undo (ini byte-identical to before).
Block as shipped: Enable=1 Volume=70 Gap=3 LoudAfter=45 LastSec=30 Log=1, all 8 lists set. A map you do NOT want gets `[Stinger.<key>]` `Enable=0`.

## Offline checks done
* Both hooks build with no warnings (SHIP out_stinger_1023 sha1 33C0D99E2B2A759F55D602430104C89CE8A7A38B, TEST out_stinger_1023_test sha1 513D170008408CF025C1C7526A66F6CDE096B29E).
* `klhook/klstinger_test.c` (worker only, volume 0): 3 shots on 2 slots leave 2 open, clips close when they end, a stop closes a cue, 0 MCI errors; 5 of 5 runs pass.
  It found a real bug: the worker computed `now` before a slow `open` and then `now - started` wrapped (a new cue was closed at once). Fixed (now re-read before the poll).
  The same `now - started` pattern may exist in klambience.c (not checked, not my change).

## Live test (proposed; needs the owner away from the machine, TEST hook)
1. Put the TEST dll `klhook\out_stinger_1023_test\dinput8.dll` in `<DD>` (back up the live one first) and run the INSTALL bat WITHOUT -Dll (the package dll is the SHIP build).
2. Add under `[Stinger]` for speed: `Gap=1`, `LoudAfter=5`, `Log=2`, `LastSec=30`; keep Volume=70.
3. Launch as usual (the F01 slot, `python tools/kl_autotest.py`) or play an offline Fragile Alliance round with bots on any map (Arcade Mode -> a map -> Accept). Not online, no `[Solo]`.
4. Proof in `<DD>\KLHook.log`: `stinger: on`, `stinger: map F01 ... clips`, then `stinger: Loud loud_N.mp3 (...; round second 5..)` at about 5 s;
   `Loot` when money is picked up; `Down` / `Dead` when a heister (bot or you) goes down or dies; `Open` then `Last30` as the van arrives;
   `Reached` when you board. A ear check: the cue is audible and does not cut the jukebox/ambience. With Log=2 `dropped (gap|cool|max|chance ...)` lines show the anti-spam at work.
5. Bad outcomes: no `stinger:` line = hook not the new one or Enable=0; `MCI ... failed` = winmm; a Down cue for a healthy bot = the +0x64c GUESS is wrong (set `DownChance=0` and report).
6. Undo: UNDO bat (+ `-Dll`), restore the dll.

## Open risks
* Never heard: clip choice, volumes (loudnorm -20 LUFS then 65..80 %) and levels against music/ambience are guesses.
* Down for bots uses [actor+0x64c] directly (GUESS, klbotdown.c comment is the only source); Loud has no real police signal.
* Last30 relies on rules+0x1d8 being the van wait in seconds (GUESS).
* Same cue may overlap jukebox music: only the volume balances it; the stinger does not duck the jukebox.
* A `Reached` cue after the round ends relies on the worker thread outliving the round (it does, a process-lifetime thread).
