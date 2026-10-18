# Retomoto (DM09): what the AI crew does after the human becomes a fed

2026-10-18, offline (static reading of klhook/*.c, the live DM09 KLJoin.ini b2bb6a2f, and the read-only Dog Days KLHook.log).
Nothing was launched, nothing in the game folder was written, no klhook/*.c file was edited. Every GUESS is marked.
Log line numbers are absolute lines of the KLHook.log that was live on 2026-10-18 (session L79, f06 = DM09).

## 1. Question

When the human dies early in the tower and returns as police ("fed"), the AI crew is left behind. In L79 no bot reached
heist stage 3 and five hop-3 walks ended in GIVE UP teleports. Over the log, 7 of 72 sessions got a van and none of the 22
sessions where the human left in-play got one (figures from the task text, not re-counted here beyond the 95-round census in 5).

## 2. What happens to the crew, by mechanism

Code facts (klhook/klcrew_rt.c, klhop.c, klescort.c):

| mechanism | after the human is a fed | evidence |
|---|---|---|
| Join box / CrewJoin EARLY (`klt_move`) | Skipped when a fed fires the box. `FedSkip=1` is the default. `done` is NOT set, so a later non-fed entry could still fire it (none can: the human is the only local player). | klcrew_rt.c 276-279, 309 |
| CrewJoin LATE | Same skip. | klcrew_rt.c 293 |
| A fed who never enters the join box | No crew jump at all. The box only fires on a local player standing in it. | klcrew_rt.c 286-297 |
| CrewHop 1, 2, 3, 4, 5, 6 | Keep running. Every DM09 hop has `Player=0`, so none waits for a human. | KLJoin.ini (b2bb6a2f) |
| A hop with `Player=1` | Would never pass again: `kle_human` returns 0 for a fed (player type 3). None exist in DM09. | klescort.c 491 |
| GiveUp teleport of the three walk hops ([CrewHop] 40 s, [CrewHop.3] 45 s, [CrewHop.5] 70 s) | Keeps running; it is the main way bots reach the street. | klhop.c, KLJoin.ini |
| klfedkit Hunted (live) | Orders bots towards the fed or to [Hops] cover places, competing with the walk orders. GUESS that this is why walks stall. | klfedkit.c ~770-996 |
| Escort (record 3) | Released the moment the human is out of play, back to its route place. | log 1131921 |

Where a bot ends up, in order of what the ini can do (all are HOP results, none is a join):
1. Tower, walking to the lift lobby (2560, 19601, 740), then carried by hop 2 to a street place (`To.n`, height 570).
2. If the walk takes 45 s without being carried, hop 3 GIVE UP teleports it to the next free street place.
3. A bot that never reaches hop 3's circle or any other circle stays in the tower (bot 2 in L79).
4. In the street the bots advance on their own; in L79 they were about 10 km short of the exit box when the round ended
   (GUESS on the distance: taken from my reading of the final bots line, not re-measured).

## 3. L79 evidence (DM09, human fed at 15:03)

| time | event | log line |
|---|---|---|
| 15:01:41.854 | round running, escort record 3 chosen | 1129771, 1129875 |
| 15:01:59 - 15:02:08 | all seven bots reach heist stage 1 | 1130211 - 1130441 |
| 15:03:03.433 | human dies (status 0 -> 1) | 1131903 |
| 15:03:03.855 | escort record 3 released ("you are out of play") | 1131921 |
| 15:03:08.434 | human back as police ("YOU ARE A FED", at (2502, 19601, -615)) | 1132061, 1132062 |
| 15:04:15 - 15:05:23 | six bots (3, 4, 7, 6, then 5 and 1) reach hop 3's From and wait 10 s, are ordered to WALK to (2560, 19601, 740) | 1133845, 1134262, 1134448, 1134484, 1135536, 1135625 |
| 15:04:38.308 | bot 3 carried by hop 2 to (6272, 570, -5200), 23 s after its walk order | 1134429, 1134494 |
| 15:05:17.138 | bot 4 GIVE UP after 45.1 s, teleported to To.2 | 1135460 |
| 15:05:23.917 | bot 7 GIVE UP, To.3 | 1135643 |
| 15:05:25.231 | bot 6 GIVE UP, To.4 | 1135687 |
| 15:05:50.232 | the fed body ENTERS join box 9; FedSkip fires ("the AI heisters are NOT moved") | 1136442, 1136443 |
| 15:06:04.713 | bot 5 GIVE UP, To.1 | 1136871 |
| 15:06:08.323 | bot 1 GIVE UP, To.1 | 1136988 |
| 15:07:10.666 | bot 3 dead | 1138603 |
| 15:07:30 / 15:07:38.824 | last bots line / RESULT PASS | end of the excerpt |

Per bot: bot 3 reached the street by a hop-2 carry (walk 23 s); bots 4, 7, 6, 5, 1 reached it only by GIVE UP after 45.1 s
(5 of 6 walks failed); bot 2 never left the tower. Heist stage 1 -> 2 happened for bots 7, 6, 3, 4, 5, 1 only after they stood in the
street (lines 1135668, 1135738, 1135748, 1135880, 1136939, 1137152). No bot reached stage 3, so no van was called (stage 3 is given
in the level exit box).

Timing: the first walk order came 71 s after the fed appeared (15:03:08 -> 15:04:15), the last street arrival 3 min after it. The
bots were busy elsewhere (fighting, hunting the fed) for most of that time. The delay is the hop's own `Wait` plus "at From" never
being true earlier; whether bots would have gone sooner under a CrewJoin jump is a GUESS.

Census (95 f06 rounds, my scratch script; parse caveats: a round line without a clock, sessions that restart mid-round): join times
typically 107 - 261 s, fed times 18 - 305 s, GIVE UP lines only in the recent sessions. Treat as a rough picture, not a count.

## 4. Correction to retomoto_fa.md s14

s14 says the fed "never reached the join box". The log shows the fed body entered box 9 at 15:05:50.232 (line 1136442) and
FedSkip fired (line 1136443). The crew was not moved because of FedSkip, not because the box was never reached.

## 5. Design

Goal: a leaderless crew carries on to the street and the exit box.

### 5.1 ini-only (what a KLJoin.ini key can do) - implemented as an opt-in flag

A hop cannot see "the human turned fed" (`Player=1` waits for a living human; there is no "fed" condition). The nearest ini-only
form is a time-based catch-all hop, not tied to the fed:

`python tools/kl_rt_joinini.py SRC OUT --leaderless-hop N` appends

```
[CrewHop.6]  From=2000 20000 -500  Radius=6000  Height=1500  Wait=N  Stage=0  Player=0  Again=0  Places=7  To.1..7 = the street list
```

Any bot that stays inside the tower volume for N s without a break (the per-bot timer restarts when it leaves the circle; klhop.c 433-438)
is carried once to a free street place (places 100+ apart; one bot per 0.5 s). Why this slot: KLV_NHOP is 6 and [CrewHop.6] is free
(the live ini has [CrewHop] through [CrewHop.5]; hop 4 already covers heights 1100 - 18900 only, so it never caught tower bots).
The flag is refused together with `--rescue-wedge` (same slot) and if [CrewHop.6] exists. Default output is byte identical
(proof in 7).

Limits (all GUESS unless noted):
- It is time from the bot's first sighting in the circle (about round start), not time since the human turned fed. With a living
  human it also fires at N s, moving the crew down before the human. That is a change to normal rounds too.
- N: join times in the census are 107 - 261 s, so N below ~107 pre-empts normal joins; in L79 the round clock started 15:01:41.66, the first bot was sighted at hop 3's From at 15:04:04.4 (143 s) and the walk orders came
  154 - 222 s after round start (log 1133845 - 1135625). So N=150 would have carried the whole crew at about the time the first walks started,
  roughly 3 min before the last GIVE UP (GUESS: assumes every bot stays inside the tower circle from the start, as the log suggests). GUESS 150 for the first test; 200 is the "only helps rounds that are already stuck" end.
- It carries bots straight to the street without waiting for the walk to the lift, so the lift-lobby hops 1 - 3 are skipped for
  any bot whose N-second timer ends first. Walks that were progressing are interrupted.
- It does not start the street steps of the entry's jump list (the game's jump routine sends AITrigger to the ZJumpPoint list;
  a hop does not). Whether street bots still behave is unknown. This is also why 5.2 sends AITrigger.
- Radius 6000 / Height 1500 cover the tower floors (heights 18500 - 21500). Not checked against every tower position; GUESS.

### 5.2 hook code (proposal for 3f, NOT applied)

A true "N s after the human turned fed" needs a per-round timer in klcrew_rt.c. Proposed key (KLHook.ini, default 0 = off, so the
default behaviour is unchanged): `[CrewJoin] FedAfter=N`. Design:
- start the timer the first time `klt_local_police(gd)` is true in a round; reset it if the player is not police again (a fed that
  returns to play);
- when it reaches N s, on the game thread, call `klt_move(rules)` once (sets `done`), skipping bots that are already in the street
  (height < 10000, GUESS threshold) so that street bots are not dragged back to the ring;
- if `klt.retrigger` and a jump point `jp` exists, send AITrigger as the LATE form does;
- the block goes before the EARLY test, because that test returns early for a fed.

```
--- klhook/klcrew_rt.c
-static struct { int on, log, retrigger, fedskip; } klt;
+static struct { int on, log, retrigger, fedskip, fedafter; } klt;
-static struct { DWORD rules; int left, done, far_seen, told, fedtold; } klt_r;
+static struct { DWORD rules; int left, done, far_seen, told, fedtold; DWORD fedat; } klt_r;
@@ klt_move(): in the per-bot loop, after klh_rd(actor + 0x460, was, 12):
+        if (klt_r.fedat && was[1] < 10000) continue;        /* FedAfter: already in the street - leave it */
@@ klt_tick(): after the klt_tele_known() / klt_same_code() check, before "/* EARLY: ..." :
+    if (klt.fedafter > 0) {
+        if (!klt_local_police(gd)) klt_r.fedat = 0;
+        else if (!klt_r.fedat) { klt_r.fedat = GetTickCount() | 1; klog("crewjoin: the local player is a FED: the AI heisters are moved in %d s (FedAfter)", klt.fedafter); }
+        else if (game_thread && (int)(GetTickCount() - (klt_r.fedat & ~1UL)) >= klt.fedafter * 1000) {
+            n = klt_move(rules); klt_r.done = 1;
+            klog("crewjoin: FedAfter: %d moved", n);
+            if (klt.retrigger && n && jp) ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLT_AITRIGGER))((void *)(DWORD_PTR)jp, 0);
+            return;
+        }
+    }
@@ klt_init():
+    klt.fedafter = (int)GetPrivateProfileIntA("CrewJoin", "FedAfter", 0, klh_ini); if (klt.fedafter < 0 || klt.fedafter > 600) klt.fedafter = 0;
```

Notes on the patch (GUESSes): the `| 1` and `& ~1UL` trick keeps `fedat` non-zero at tick 0; a plain `fedat = GetTickCount()` with
a separate flag is cleaner. `klt_entry()` must succeed (the join entry exists) for `rules`/`jp` to be known, which it does on DM09.
Whether `klt_local_police` is already true during the 4.9 s death countdown is not known; the timer starts on the first true read.
klt_move's `klt_refuse` and "at the entry already" tests still apply. Before enabling, the L79 observation (walk stalls from
competing orders) suggests also setting `[Bots] WalkExclusive=1` (hook key, not live yet).

## 6. Test recipe for 3f (live runs belong to 3f; the owner is back, so only when the queue allows)

1. ini-only: install the staged KLJoin.ini (`C:\kl_build_1018\rt_leaderless\DM09`, see 7) over the live one. KLJoin.ini is read
   from the level folder, no hook change.
2. Scripted early death: start DM09 Arcade, make the human die in the first 60 s (e.g. step off the ledge or take fire),
   return as fed, stand still in the tower or walk away from the lift. Run 150 s plus.
3. Expect in the log: `hop: bot N (...) hop 6: at From for 150.x s ... -> To.n`, then `bots: record N (bot): heist stage 1 -> 2`,
   and, if the street steps run, stage 2 -> 3 and a van (`bots: L1 sN van`). No `crewjoin:` line appears (FedSkip untouched).
4. Compare with L79: fewer GIVE UP lines, earlier stage 3, bot 2 no longer left in the tower.
5. Repeat once with a living human who plays normally: does hop 6 move the crew down before him (expected, see limits)? If yes
   raise N or do not adopt the ini form.
6. Hook form: after 3f applies the patch in 5.2, set `[CrewJoin] FedAfter=20` (and `Retrigger=1`, `[Bots] WalkExclusive=1`) and
   repeat 2; expect `crewjoin: the local player is a FED ...` then `crewjoin: FedAfter: N moved`.
7. Always restore: the live KLJoin.ini is b2bb6a2f.

## 7. Files and proofs

Changed: `tools/kl_rt_joinini.py` (new flag `--leaderless-hop SECONDS`, 10..600; other flags untouched), this document.
Default output unchanged: running the tool with no flag on the live ini gives md5 b2bb6a2f7d26d73feb8486fc15d9f8d8 (equal to the
source, "byte-identical"). `--leaderless-hop 150 --rescue-wedge` is refused; a second run on the output is refused ([CrewHop.6] exists).

Staged: `C:\kl_build_1018\rt_leaderless\DM09\KLJoin.ini`, built from rt_join_next2 b2bb6a2f with `--leaderless-hop 150`:
md5 0b557e406f311803518b2727a4083878 (23497 bytes + the 19 appended lines, no existing byte changed). The folder holds only
KLJoin.ini: the other members of rt_join_next2\DM09 (F06_Main.zip bf1dfdb3 etc.) are unchanged and not duplicated, to save disk
(about 2.8 GB). To adopt, copy this one file over the live KLJoin.ini; to undo, put b2bb6a2f back. Nothing was installed.

## 8. Summary of evidence tags

- Code behaviour: klcrew_rt.c, klhop.c, klescort.c lines cited in 2.
- Live data: KLHook.log lines in 3; KLJoin.ini b2bb6a2f in 2 and 5.1.
- GUESS: why walks stall, N=150, the 10000 height threshold, the tower volume, the street-step behaviour of hop-carried bots,
  the census parse, the "about 10 km short" figure.
