# Review 4 of the player-down work: track R4, `[Down] Bots` (the AI heisters' down) and 'Dead Men's own'

2026-10-11, adversarial review. Offline: kl2.exe 0490 re-read with `debug/dasm.py`, the diff of `klhook/kldown.c`
(sha1 fbf5ca54..) against HEAD 98564f7 read line by line, the compile re-run, the worker's clip and log scripts re-run.
Nothing ran in the game. The worker's files were not changed.

## Verdict: ACCEPT WITH FIXES

- The code is safe to carry: every key is off by default, the human's path is unchanged with `Bots=0`, the gates hold
  (Arcade, a level that is not stock, state 0x19, game thread), no call and no patch. B0 and B1 may run as scripted tests.
- **It is NOT shown that `Bots=1` makes an AI heister go down.** The one enabling write (`BotsForce`) removes tests
  f / g only, and by the code g cannot be what refused 177 of 177 (M1). Two refusals that CAN be systematic sit in
  test b, which no key touches. Nothing of this goes into the owner's ini, and the owner is not told 'the bots go
  down now', before B1 has shown an `IS DOWN` line.
- (A) holds: the flop he saw is Dead Men's clip, byte for byte.

## MUST

**M1. The 'why' is open, the named candidate is refuted as sufficient, and B0's count will mislead.**
- READ 0x70e206 .. 0x70e29c: with modifier 0, `[gamedata+0x4d04]` = 0 jumps past the 5 s test (0x70e22c); a last
  down older than `[T+0x58]` = 20 s is YES at once (0x70e273); only 5 .. 20 s is the 50 % draw (the constant
  0xb39f70 is -1024.0, so the compares read 'now >= last + n s'). The first heister to die after 20 quiet seconds
  goes down for certain if a .. e pass. So g cannot give 0 of 177 (nor 7 of 7 on T01).
- The game asks a .. e BEFORE f / g. The `DIED` line names its reason by the hook's own priority and prints
  `g: AN NPC WENT DOWN LESS THAN [T+0x54] s AGO` whenever a policeman fell within 5 / 20 s - which in a fire fight
  is nearly always - although b, d or e may have refused first. 'COUNT the reasons: that is 11.2's answer' (11.4,
  B0) is wrong: the count will say g whatever the cause.
- Two candidates the report does not name, both inside b (0x70f330), both untouched by `BotsForce`:
  - `[soldier+0xa4]` is the **ZHitAnimTask** (vtable 0xbcf87c by RTTI; made at 0x7cfc79). 0x4a05f0 refuses the down
    while its state is not 0 / 4 = while a hit animation plays. A heister dies under 250 .. 550 small hits at about
    3 a second.
  - the 16 probes of 100 units (0x70f3d1 .. 0x70f437, pathfinder slot 41): ALL must pass = one metre of mesh free in
    every direction. The bots are sent to cover boxes, walls and corridors.
  Neither is established; both fit 'always'.
- FIX: (a) the `g:` texts say 'g MAY have refused (a .. e are asked first and are not excluded)'; (b) the `DIED` line
  names the ZHitAnimTask and prints the bot's place (`kle_node`), so deaths can be laid on the mesh offline;
  (c) 11.2 / 11.4: B1 (force on) is the run that decides - deaths that still say 'the modifier was 1' = b / d / e;
  (d) re-word the report's 'best candidate g'.

**M2. What the game does to his route when he gets up was not read: `[soldier+0x4fc] = 1` (0x5f4dfc).**
- The report cites the line as proof the down was written for an Arcade ally. The repo already says what the byte
  does (re/boardall_review_code.md 200, re/boardall_review_exe.md 81; 0x686c77 re-read here): it makes the
  ZDefendBehaviourRout's wait loop count him as arrived. The WAITING Defend step of his chain ends and its NEXT fires
  without him having reached the place. It is put back by his next order (0x760efe).
- For our bots that is the question 'does he still fight, loot, board': a hold, a loot stop or a Retomoto gate step
  can be skipped by every down. With `BotsMax=2` twice a bot a round.
- FIX: say it in 11.1 / 11.6; add to B1 / B2 PASS: after `IS UP` the record's stage still goes 1 -> 2 -> 3 and it
  boards (klbot lines), and one run on DM09 (the gates) before any owner setting.

## SHOULD

1. **B1 stacks unproven writes.** As written B1 runs with the default `BotsFree=0.75` (the 'no damage' word, ASSUMED
   harmless). First enabling run: `BotsMax=1 BotsFree=0`; the shield in B2.
2. **`BotsFree` swallows every kill.** While the word is not 0 the routine writes no health (0x8477ae) and skips the
   death (0x847945): the left-behind 1,000,000 and the point-blank step too. The ini advises `BotsLie + 2`
   (seconds). Take the bit off when `sn.veh >= 5`; drop that advice or say the cost. Of the word's 20 readers
   (`cmp word [+0x3a]`) 4 are read; unread: 0x458889 0x4a81d7 0x58059c 0x5841f5 0x596039 0x613050 0x62a65d 0x636ad5
   0x661c40 0x6660c5 0x69fa49 0x6e2cb1 0x6f108f 0x77e7c9 0x8478f4 0x8c1c76. (For it: the game holds the same bit
   `[T+0x48]` seconds on the buddy, 0x5f4d9d.)
3. **`DIED` mislabels a death on the floor seen late.** `status == 7` with `dn == 1` and `b->down == 0` in one pass
   prints 'without going down'. Print `dn` and the current values beside the one-pass-old ones.
4. **b is read short in the code and the report.** 0x75a2e0 is three-part (`[actor+0x88c]` and `[seat+0x18]` != 0 and
   `[seat+0x40]` == 0; the log tests the pointer only). The fifth test is missing from both (only 'not read further'
   in the .md): `[actor+0x5b4]` is the object he is attached to (0x57a380 / 0x8c9015), refused when it is a ZLNKOBJ
   (type pair 0x153a898) AND a ZHavokLnkObj (0x168cddc) - readable, add it to the snapshot.
5. **A human who floors a bot.** At health 0 with a player attacker the routine calls rules slot 131 (+0x20c,
   0x8477fd) and, for a police player, slot 128 (+0x200, 0x847886) BEFORE the down is asked. Slot 128 is `ret 0x10`
   for Heist (re/fed_kit.md); slot 131 is not read. The owner plays with `[Fed] Player=1`: a kill may be credited
   for a bot that gets up.
6. **The owner's question.** CLAUDE.md (1ebd45d) reads him as wanting 'the AI heisters' own shot clips'. The report
   leaves exactly that unread (who sets `[generic+0x98]` = 2, the full-body hit reaction of a living NPC). The answer
   to him must not be 'they have a down and never use it' alone.
7. Small: e is 'more than 1,000' (0x70e1c7 jumps on C0 only), not '1,000 or more'. With `Enable=0 BotsDry=1` the
   round line says 'the part acts on this round'. Slots +0x1c4 / +0x164 in the script are the soldier's own
   (`[actor+0x77c]`), not 'his weapon's'. `klgrudge.c` also writes a crew member's health object: say which part
   wins with `BotsUpPct`.

## What was tried and holds

| claim | result |
|---|---|
| asked at health 0 only, word `[+0x3a]` 0, slot 51 = 0x688190 (dog = no) -> 0x70e0e0 | holds (0x847937 .. 0x847968; vtable 0xbd0954 +0xcc) |
| a: actor slot 405 = 0x410a30 = `[actor+0x64c]`; ZWounded state 0 / 4 | holds |
| c: `[actor+0x5cb]`, one reader 0x70e142, set 0x5f4b56, other writers store 0 | holds (0x6ccccf and 0x830445 write `bl` after `xor ebx, ebx`) |
| d: attacker, `[rec+0x30]`, kind not 1, nearer than `[T+0x5c]` | holds (0x70e15c .. 0x70e18c) |
| e: 1,000 / 500,000 for the buddy | holds (0x70e1a1), strictly greater |
| f: 1 = yes past g, 2 = no; writer 0x803530 with the three debug strings | holds |
| no team / Arcade / squad-kind test in the path | holds for 0x8473a0, 0x688190, 0x70e0e0, 0x70f330 |
| slot 1 0x7ea990: lie tick `[dnd+0x14]`, last-down tick, health to 25 % | holds (0xb293f0 = 0.25) |
| script 0x5f4ac0: lies while `[dnd+0x14]` >= now in 0.1 s steps, fires, then 75 % | holds (0xb794c0 = 0.75; a further wait of at most 2 s) |
| the bit: 0x6c75c0 sets word + mask + tick, 0x638e2e takes it off, 0x6f4890 clears | holds |
| **ends by itself** | holds: end slot 3 = 0x67fa10 clears `[actor+0x64c]`, the 0x800 bit (health > 0), `[dnd+0x14]`. `BotsLie` writes one fixed tick of at most 15 s. A bot lying for good was not found |
| **immortal** | bounded: the hook takes the bit off at `IS UP` / death / round end, and the game's end slot clears it anyway |
| **dead but counted** | not found by reading: status 7 comes from the death path (rules slot 16, per re/fed_respawn.md; not re-read). B1's 'no klbot dead' line is the check |
| state reset | holds: `kld_b` cleared at init; round over / other rules object / record gone / other actor -> modifier back to 0, bit off, `[T+0x5c]` back |
| stock level, online, off by default | holds: `klr_arcade` + `klb_level` before `kld_bots`; `Bots` default 0; ini keys commented, `[Down] Enable=0` untouched |
| the human's path | holds: two lines of `kld_tick` changed; with `Bots=0` nothing differs |
| files | only `klhook/kldown.c`, `klhook/KLHook.ini` ([Down] block, 27 added lines), `re/player_down.md` (149 added, 0 removed); no `z_botdown`, no tool |
| compile | re-run from `git archive HEAD klhook` + this kldown.c in `G:\kl_scratch\R4rev`: 'built ... (TEST)' 6e4394c6.., 'built ... (SHIP)' f403f7ec.. (the sha1s differ from the worker's 8e8b60b4.. / 73288206..: another folder and build time); one warning, klhud.c(285) C4101 |
| (A) the clips | re-run `R4/same.py` on M03FAA_Main.zip against F07: `Hero_Torso_Back` 186 frames 37,228 bytes 0737fdfe40 SAME DATA; `Hero_Torso_Front`, `Get_Up_From_Stomach` SAME DATA; no Down_Not_Dead clip in Dead Men |
| the logs | re-run `R4/logs.py`: 267 of 267, none back within 25 s |
| the klescort patch text | fits `kle_bot` as it stands (`why`, `kle_later`, `actor` exist); needed only if `[actor+0x576]` stays 1 during a down - not read |

Not re-read: 0x6fd7c0, 0x4860e0, 0x6cabf0, the state graph 0x730be0, rules slots 16 / 131, kaneandlynch.exe.
