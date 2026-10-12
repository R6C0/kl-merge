# Review of klhud_board2.c (round-over scoreboard) and klhud_tags.c (initials above heads) - cloud session, 2026-10-12

Done by READING the source at HEAD ebe4d72 (and the parts of klhud.c they lean on: `klu_reset`, `klu_stand_down`, `klu_hide_tick`,
`klu_pic`, `klu_draw_one`, `klu_addpic`). No game, no kl2.exe, no compiler in this session: NOTHING here was built or run, and every
"the game does X" below is taken from re/ (cited), not read again in the exe. Line numbers are those of HEAD ebe4d72 unless marked.

Asked for: anything that could CRASH in the round-over states (0x1f .. 0x27), or leave a STOCK ELEMENT HIDDEN after the hook stands down.
Short answer: no crash path found that is not already guarded by the same rule the rest of the HUD uses (render thread only TRIES the lock,
pictures need the transform the game itself passes, objects checked by vtable). Neither file hides a stock element: board2 hides nothing
(it skips one Render call), tags draw only while klhud.c holds the player list hidden, and klhud.c's `klu_hide_tick` gives the hide back
or leaves it to the game (0x75f780) - see section 3. One functional fault (B1) very likely kept the installed scoreboard from ever showing
in a long session: FIXED in source, not built.

Grades: MUST = wrong behaviour or a crash path that a normal session can reach; SHOULD = fix before more live runs; NOTE = for the record.

## 1. klhud_board2.c

| id | grade | line(s) | finding | outcome |
|---|---|---|---|---|
| B1 | MUST | 209 | The render decision required `end < 1000.0f`. `end` = the outro element's deadline `[el+0xd8]` = (game clock `[[0xdd2640]+0x48]` + 0x2800) / 1024 (re/hud_board_b.md 1). The clock is 1/1024 s units (re/climb.md: raw clock + offset, held in a pause) and is NOT shown to restart per level. So once the game clock passes ~1014 s (17 min) every round-over fails the test and the stock panel draws, silently (no log line: the branch just falls to `return 0`). The owner's sessions run longer than 17 min, so the scoreboard installed at 15:27 ([HUD] Scoreboard=1) may never have shown. The harness (klsb_test.c) only used frame 1000 = 1 s. | FIXED in source: bound 2.0e6 (23 days; `end*1024` stays below 2^31). klsb_test.c: a case at frame 2,000,000 (draws ours) and one just past that deadline (stock). NOT BUILT, NOT RUN. Live: SB1 should be done in a process that has been up more than 20 min. |
| B2 | SHOULD | 231 | `klsb_testdraw` (ScoreboardTest=1) drew pictures through the CLOCK's cached transform without the `e+0xc == T` / `e+8 == tbl` test that `klsb_ours` makes (210). If the outro element's transform differs, test mode would draw at a wrong scale and SB0b would mislead (not a crash: the clock's transform object lives as long as the OSD). | FIXED in source: the same test. NOT BUILT. |
| B3 | SHOULD | 246-248 | When ours draws, the wrapper returns 1; otherwise it returns the stock Render's value (harness: the stub's 7 comes through). What 0x8bf300 does with slot 2's return (0x8bf5f6) is NOT established in re/ (re/hud.md 2.3 lists the call, not its use). If the caller uses it ("drawn" / "keep"), 1 may differ from what the stock returns on a frame where it drew the plate. | Not changed. Local session: read the three instructions after the call at 0x8bf5f6; if the value is used, return what 0x577e70 returns in its plate branch. |
| B4 | NOTE | 197-200, 216 | The canary checks the OSD and text 0 only; then `klu_draw_one` reads the first dword of all 40 objects DIRECTLY (klhud.c 331). The objects are scene-owned and die together, and the element being rendered proves the scene is alive, so a freed-but-mapped single object is not a realistic case. Same discipline as the HUD's own texts. | Keep. |
| B5 | NOTE | 246, 206 | `klsb_r.elem` and `klsb_r.state` are read on the render thread outside `klsb_cs` (the tick writes them without the lock at 502, 510). Both are aligned DWORDs; the worst case is one frame of the stock panel. | Keep. |
| B6 | NOTE | 286-291, 273 | After `klsb_forget` (OSD changed, klu fault, klu reset) the element keeps OUR private vtable copy; slot 2 then always takes the stock branch (`e != klsb_r.elem`). Correct as long as the DLL is never unloaded (it is not, as far as re/ says). The copy is 16 dwords + RTTI; re/hud_board_b.md 7.5 says the vtable has code slots to 10 and data after, so nothing reads past the copy. | Keep. |
| B7 | NOTE | 505 | The wrap is retried 30 ticks (3 s) and then refused for the whole OSD. The element is made in the OSD's constructor (re/hud.md 2.2: all elements from 0x42e8a0), so it exists from the first tick; a refusal means a real mismatch. | Keep. |
| B8 | NOTE | 330 | `human = s->human >= 0 ? s->human : 0`: with no human record found, record 0 is used as 'you'. Arcade always has the human; `kluv_idx` refuses an empty record. Cosmetic at worst. | Keep. |
| B9 | NOTE | 293-305 | 40 new ZCHAROBJs per OSD; when klhud resets on a new rules object each round (`klu_reset`, klhud.c 1209) the pool is made again in the next 0x17..0x19, so a long session leaves 40 scene-owned objects per round in the persistent scene (review S3 of re/hud_scoreboard.md 6b). | Watch in SB3 (memory line of the hook) - no change. |
| B10 | NOTE | 343-456 | The `klu_addpic_q` redirect is set and cleared inside one main-thread call with no early return between (the early returns are all before 343). The render-thread users of the ring helpers (klhud_popup.c 359/363) pass a non-NULL element, which goes through `klu_pic`, never `klu_addpic`. No race. | Keep. |

Round-over states, checked one by one (what each tick / frame does in 0x1f .. 0x27):
- 0x1f: tick composes (main thread, `klsb_cs`), render draws ours or stock. klhud.c's own tick stands down (`show` is 0) and does NOT un-hide the player list because the game's 0x75f780 has hidden the clock too (`klu_hide_tick` 996-1001: the hide is left to the game).
- 0x20 and later: `klsb_r.valid` drops in the next tick (522-525); until then (<= 100 ms) the render's own `klsb_r.state == 0x1f` test and the deadline test keep the stock path. The XML page is untouched.
- A new round (rules object changes) or a scene change: klhud.c resets (`klu_r.osd` = 0) and the next klsb tick forgets everything (501). In the <= 100 ms between, a render call can still draw ours: its objects belong to the same, still-live scene; `klsb_pic2` re-reads `klu_r.handle[n]` per picture, which `klu_reset` zeroes -> pictures are skipped, never drawn from a stale handle.

## 2. klhud_tags.c

| id | grade | line(s) | finding | outcome |
|---|---|---|---|---|
| T1 | SHOULD | 191-203 | The tag drawer 0x7b8150 calls `[this]->vt[0x1e8]` (re/hud_tags.md 1), i.e. a virtual call through OUR text object's vtable. `klht_render` passes `q->ini`, `q->out[k]`, `q->inis`, `q->mon`, `q->mons` without the vtable canary that `klu_draw_one` (klhud.c 331) and the scoreboard (`klsb_alive`) make. The objects are cleared by `klht_reset` inside `klu_cs` on every scene / OSD / rules change, and the render takes the same lock, so a stale pointer needs a scene freed while the clock element still renders - not seen as reachable. A one-read canary per object (`klh_rd32(o[k]) == KLU_TEXT_VT`) costs at most 7 guarded reads a tag and closes the case. | Not changed (cheap to add in the next local build; listed for the local session). |
| T2 | SHOULD | 198 | With `HeadTab=1` the render writes 8 bytes straight into our own ZCHAROBJ at +0x3c (unguarded `memcpy`). The field's meaning (stored position) is from H1f / H1g notes, not read in the class. Only our object is written, off by default (`HeadTab=0`). | Keep off; if A1 turns HeadTab on, route the write through `klh_data` or read +0x3c before the draw instead of zeroing it. |
| T3 | NOTE | 176 | `klht_r.active`, `klu_draw_on`, `klu_r.hid` are read before `TryEnterCriticalSection`; `active` is re-tested inside (179). Benign. | Keep. |
| T4 | NOTE | 113, 176 | Round-over: tags draw only when the tick saw state 0x19 AND the clock element renders (`klht_render` is called from the clock's wrapped Render). In 0x1f the game hides the clock (0x75f780), so no tag can be drawn over the scoreboard. No path found that draws tags in 0x1f .. 0x27. | - |
| T5 | NOTE | 188 | The node is re-read from the record and must equal the tick's snapshot actor; a bot that died and was released between tick and frame is skipped. The drawer then makes two virtual calls on the node (`vt[0x340]`, `vt[0x670]`) as the stock loop does under the same entry conditions (st10 / st14). | Keep. |
| T6 | NOTE | 129 | `klht_make` failing half way leaves some objects made and latches `klht_r.fault` for the level: no tags, no retry storm. | Keep. |
| T7 | NOTE | whole file | Tags have NO line-of-sight test: they show through walls (re/hud_audit.md). The stock drawer has none either. Design: re/hud_tags_sight.md. | Design only. |
| T8 | NOTE | 180 | `a1 = [pl+0x10]`, `a5 = [pl+0xc]` passed as the stock passes them; whether the drawer uses them is a guess (re/hud_tags.md 5.1). | Keep. |

## 3. Can a stock element stay hidden after the hook stands down?

- Board2 writes one dword (the element's vtable pointer) and never a hide byte. Fall-back = the stock Render is called. Nothing to restore.
- Tags write nothing to the game's elements. They depend on the player list being hidden BY klhud.c (`klu_r.hid`).
- klhud.c `klu_stand_down` (1024-1029) un-hides the player list unless the game has hidden the clock too (996-1001, the round-over case), and the
  game's own 'show' later writes 0 to both. One gap, NOT new: if klhud resets with `klu_reset` while it holds the hide (`klu_r.hid` = 1) and the
  OSD lives on (the rules-object branch at 1207-1210 calls `klu_stand_down` FIRST - correct; the "OSD object changed" branch at 1220-1223 resets
  without a stand-down, but there the old OSD is no longer the one shown). The scene-change branch drops the old OSD on purpose. No change asked.
- klhud_escape.c / klhud_popup.c / klhud_board.c were not part of this review.

## 4. For the local session (needs a Windows build and the game)

1. Build TEST + SHIP from HEAD (klhud_board2.c B1 / B2 changed); run `cl /W4 klsb_test.c` in klhook: expect the old 91 checks + 2 new ones PASS.
2. SB1 / SB2 in a process that has been running more than 20 minutes (B1 is exactly the case the earlier harness missed). Log: `scoreboard: the first snapshot ... ready` and, with Log=2, `N ours` > 0 in the 5 s line.
3. Read 0x8bf5f6 .. +0x10 for B3.
4. T1: add the per-object canary when next touching klhud_tags.c.

## 5. Addendum: the watch rework 54ceb35 (landed while this review was written; read after rebasing onto it)

The local session's own adversarial review (re/hud_watch_review.md, fixes in re/hud_hook.md 14.10) already caught the hand direction, the
default of WatchStyle, the last-minute digits, the queue overflow log, the gun picture and the label bar's margin. What it did not cover:

| id | grade | where | finding | proposal |
|---|---|---|---|---|
| W1 | MUST (operational) | tools/kl_hud_tab.py `WATCH_STYLE = 1`, tools/kl_hud.py `set_watch` default 1; klhud.c `WatchStyle` default 0 | The bake now defaults to the WATCH look while the hook defaults to the OLD look. re/hud_install.md's standing rule is 'after any kl_expansion install run kl_hud_tab.py build and copy the zips'. Followed as written, the next install puts watch-look archives under a hook that draws the old look: slot 112 (now the 128 x 128 wear texture) is drawn as every strike-through, crew rule and scoreboard line; 115 (now the bezel) as the loot ring's and the dials' track ring (re/hud_watch_review.md MUST 2, the 'mirror case'). No crash; visible on the owner's game. | Until WatchStyle=1 goes into the owner's ini together with rebaked maps: run `kl_hud_tab.py build ... --watch 0` (or set its default to 0). A line saying so is added to re/hud_install.md by this session. |
| W2 | SHOULD | klhud.c `klu_pic_prep` (reads `tbl + 12 * k`) | 14.10 says 'the hook cannot tell the textures apart'. It can: the OSD's picture table entry is {handle, u16 width, u16 height} (re/hud.md 0 item 3 and 1: `osd+0x3ec + 12*n`, filled by 0x5e3810 from the texture info; `klu_pic_prep` already reads the handle at the same address). Slot 112 is 256 x 32 in the old bake and 128 x 128 in the watch bake (`EXTRAS_OLD` / `EXTRAS_NEW`). | In `klu_pic_prep`, read the two u16 after slot 112's handle; keep a per-level `klu_r.wlook` = 1 only when [HUD] WatchStyle=1 AND 112 is 128 x 128, = 0 when 112 is 256 x 32 (log the mismatch once: 'WatchStyle=1 but this level is baked with the old look: old look drawn'); use `klu_r.wlook` where the code reads `klu.wstyle` at draw time. Caveat: `klu_layout` reads `klu.wstyle` when the text objects are made (styles of the weapon texts), which happens before the first `klu_pic_prep`; those styles can stay keyed on the ini (they only matter in the watch look). NOT written here (klhud.c changed under this session; a local build is needed). |
| W3 | SHOULD | klhud.c `klu_dial_base`, klhud_weapon.c `klwd_base` | The case picture goes to `klu.layer - 4`. `[HUD] Layer` accepts 3 (`klu_inii("Layer", 0xd, 3, 15)`), so Layer=3 gives layer -1, which DrawChunk takes as the byte 0xff (re/hud.md 8: `layer u8`) - the dark case on top of everything. Default 13 is fine. | Raise the key's minimum to 4, or clamp as board2 does (`klsb_ly`). |
| W4 | NOTE | klhud.c `klu_hand` | One step for the whole hand (1.0 for the Mercedes hand, 1.2 sword, 1.1 seconds) while the width tapers: at the Mercedes tip (0.8) and along the seconds hand (1.1) the step is at or above the dab's ink size, so the tip and the seconds hand may read as beads at 2x (1440p). A step of 0.5 x the local width (min 0.6) keeps them solid and also halves the shaft's dabs (3.0 wide at 1.0 -> 1.5). | Look in W1 at 1440p; only if beaded. |
| W5 | NOTE | `WatchLast=1` | The draft says the watch becomes a RED TIMER (digits) in the last minute; the new default blanks the stock digits and shows red hands / stroke instead. A deviation from the draft that the owner has not seen. | Owner's call after W1. |
| W6 | NOTE | re/hud_watch_design.md | Written by this session before 54ceb35 was visible; superseded by it. Its section 8 checklist was applied above: no new slot (but 112 / 114 / 115 change meaning: W1 / W2), hands continuous except W4, wear only in the bake with WatchWear, no brand mark, queue overflow logged, Draft does not switch it on, preview mirrors the C numbers (kl_hud_watch.py). | - |

## 6. Tests RUN in the cloud session (2026-10-12 evening; MinGW i686 + Wine 9 on Linux - the hook's harnesses, NOT the game)

How: `tools/run_harness_linux.sh <harness> [args]` builds a klhook harness with i686-w64-mingw32-gcc and runs it under Wine (32-bit);
`tools/run_harness_linux.sh --check-hook` type-checks the WHOLE hook (SHIP and TEST) with GCC from a scratch copy whose MSVC naked
`__asm` forwarders (klsteam.c KLX_FWD) are stubbed - so the real dinput8.dll is still an MSVC-only build.

| what | result |
|---|---|
| klsb_test (scoreboard, incl. the two new late-deadline cases of B1) | 93 checks, 0 failed |
| B1 mutation: the old `end < 1000` put back | 1 FAIL - exactly the new case (a round over after 32 min of game clock draws the stock panel). So the harness now catches the bug, and HEAD fixes it |
| kladren_test | did not LINK: kladren.c calls `klbd_by` (klbotdown.c's export, added after the harness was written). Stub added to the harness (returns -1 = [BotDown] off); then ALL PASS |
| klbotdown_test, klmem_test, klrappel_test | ALL PASS / PASS / ALL PASS |
| whole hook, GCC type check, SHIP + TEST | 0 errors. Warnings: klhud_weapon.c `k`, `m` unused (REMOVED), kldown.c 2473 `need` unused (not this session's file), klhook.c 755 no return in `klh_ticker` (an endless loop: harmless) |
| NEW klhook/klwatch_test.c + tools/kl_hud_watch_check.py compare: every picture `klu_watch_look` / `klu_escape_look` queue at ten round times (with and without WatchSeconds) and four escape-dial states, against tools/kl_hud_watch.py | 24 of 24 cases MATCH (slot, place, size, tint, layer) after one fix: the escape dial's car icon was tinted with the HUD chalk f3f0ea in C, the watch chalk e9e6df in the model the previews were judged on -> C now uses KLW_C_CHALK |
| model vs C, weapon circle | the model still put the gun picture at cx + 28 S; C moved it to 25 S in the watch review -> model fixed |
| picture budget, real C, whole round in 0.1 s steps | watch worst 103 (at 3:59.9), 137 with WatchSeconds=1; escape dial worst 49; weapon circle (model) worst 65; label bar 1 -> about 218 for the dials, under the queue's 300 |
| render: the hook's own picture lists drawn with the baked `--watch 1` textures (`kl_hud_watch_check.py render`) | reads as a dive watch at 1x and 2x on dark and light ground; wear light. SEEN: (a) at 0:59 the stroke becomes a FULL saturated red ring - the loudest thing on the HUD for the whole last minute, against the owner's 'quiet' rule (the review's acknowledged 1:00 jump, now visible); (b) WatchSeconds=1's coral hand lies ON the sword hand (both show seconds left): a red-white beaded double line - as designed it adds nothing; (c) at 2:10 the hands merge (known); (d) the sword tip is slightly scalloped at 6x (W4), not visible at 1x / 2x |
| tools/kl_hud.py preview-hud (watch look, the default) / preview-dials | import `kl_hud_wprev`, which is NOT in the repository: both fail on any clone but the local session's. Commit it |

Proposals from the render (NOT applied - the owner decides the look): (a) keep the bezel stroke on the HOUR quantity all round, so it
drains to nothing at 0:00 with no jump, and make the last minute red by the sword hand alone (the review's own alternative); or dim the
red stroke to the bezel grey's weight. (b) If a seconds hand is wanted, let it sweep REAL seconds (game clock) instead of the time left,
or drop the key.

## 7. Applied after the tests (cloud session, same evening; each covered by a harness run above; NOT BUILT WITH MSVC, NOT RUN IN THE GAME)

| id | change | test |
|---|---|---|
| W2 | `klu_choose_look`: the level's bake (slot 112: 128 x 128 watch / 256 x 32 old, OSD picture table `osd+0x3ec + 12 n` {handle, u16 w, u16 h}, re/hud.md 1) decides the look before the layout; WatchStyle only when it cannot tell. Also covers the mirror case (watch bake under WatchStyle=0 now draws the coherent watch look instead of the broken mix). RELIES ON the table layout of re/hud.md 1 (read from 0x5e3810's writes, the width / height fields not yet read back live: the first live start logs the decision) | `klwatch_test look`: 9 checks PASS; with the detector disabled 2 FAIL |
| W3 | `[HUD] Layer` minimum 3 -> 4 | GCC type check |
| T1 | klhud_tags.c: every object handed to the tag drawer passes `klh_rd32(obj) == KLU_TEXT_VT` | GCC type check (no tags harness exists) |
| - | escape icon tint KLW_C_CHALK; model gun offset 25; unused `k` / `m` removed | `kl_hud_watch_check.py compare` 24/24 |
W1's operational rule (bake --watch 0 for the owner) stays until a hook from this HEAD is on his game.
