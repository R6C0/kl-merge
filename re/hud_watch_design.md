# The round watch, reworked: a dial with watch hands and light wear - DESIGN ONLY (cloud session, 2026-10-12)

**SUPERSEDED** by the local session's commit 54ceb35 (re/hud_hook.md 14, re/hud_watch_review.md), which landed while this was written.
Kept only for its review checklist (section 8), applied in re/hud_cloud_review.md section 5.

No code. Nothing built, baked or run. Written because no 'WatchStyle' commit (re/hud_hook.md section 14) was on `rtp-schemas` at
ebe4d72 / 44661c6; a local session was building one when the task was written. IF THAT WORK LANDS, IT WINS: use this note only as a
checklist to review it against (section 8).

Owner's words: "clock needs a rehaul and the circle on the gun"; "make the clock more like a watch like rolex hands and a bit more wear
n tear". Standing rules from him: rings are ONE painted stroke, never dots; wear was called "overdone" twice, so it stays light; quiet,
not "in your face"; 1:1 with the draft where the draft has an answer (re/hud_layout.md: watch at (1212, 66), diameter 69, red timer in
the last minute).

## 1. What is drawn today (klhud.c `klu_dials`, HEAD)

- back: picture 114 (disc) 69 x 69, 0x9c080809, layer - 2; track: picture 115 at r 29; stroke: `klu_arc` family A (slices 123..125 +
  one dab run) from `1 - left` to 1 = the time that is LEFT, clockwise from the top.
- hand: 19 dabs (113) of 4.3 px from the hub along the angle of the stroke's start + a hub dab of 8.6 px. One hand, a dotted line in
  effect (the very "circle circle" the owner disliked, on a small scale).
- last minute (`clock <= 60`): the watch is not drawn; `klu_clock_face` lets the stock clock's digits through, coral.
- updated in the 100 ms tick (queued pictures), so everything steps 10 times a second.

## 2. The look (what the owner should see)

A dark watch face with a worn chalk bezel:
- **Bezel** = the stroke ring that is there now (time left, chalk, the one painted stroke) - kept, it is approved and it carries the
  information at a glance. Track ring 115 under it as now.
- **Dial** = the dark disc (114) as now, plus a **faint second disc** of the same picture at 0.92 of the diameter in a warmer ink
  (0x40 1a1714) = a sunk dial edge; no new picture.
- **Indices** (the "Rolex" read without any brand mark): at 12 a DOUBLE baton, at 3 / 6 / 9 single batons (axis-aligned rectangles:
  picture 181, no rotation needed), at the other eight hours round dots (dab 113). Chalk, alpha 0xe6 with a fixed per-index jitter of
  -0x10 .. 0 (worn lume, deterministic, never random per frame).
- **Hands**, three, the classic set:
  - hour hand = "Mercedes" style: a short broad hand with a small open circle near its tip, chalk;
  - minute hand = "sword": long, tapering to a point, chalk;
  - seconds hand = thin, coral, with a small round "lollipop" disc two thirds out and a short tail behind the hub.
  - hub: chalk 4.6 px, ink centre 1.6 px.
- **Wear**: only in the baked disc (section 5) and the index jitter above. No scratches drawn as pictures, no dirt on the hands.
- **No brand**: no crown, no name, no lettering on the face. "Rolex hands" means the hand SHAPES only.

## 3. What the hands show (a reading that works like a watch)

The round counts DOWN from its length (6:00 on every map so far: `kluv_round_len`, score+0x3c). The watch shows the time LEFT, read
the way a watch is read (the short hand on the 12 marks, the long hand on the 60 ticks). Mapping (simple, readable at 69 px, every hand
meaningful; a purely decorative sweep was considered and dropped as busy):
| hand | shows | one turn = |
|---|---|---|
| Mercedes (short) | minutes left | 12 min |
| sword (long) | seconds left | 60 s |
| coral seconds | seconds left, with the tick's sub-second part (smooth at 10 Hz) | 60 s |
The sword and the coral hand then point the same way; to avoid that, `WatchSeconds` defaults to **0 = the coral hand is not drawn and
the SWORD is coral-tipped** (the tip's last third in coral). WatchSeconds=1 adds the thin hand for the owner to compare. GUESS: two hands
read better than three at this size; the pictures decide.
Bezel stroke = time left / round length (as now). With a 6-minute round the Mercedes hand and the bezel's end agree (both at 6 at GO,
both at 3 at 3:00 left) - deliberate: the bezel is the round's share, the hands are the clock reading.

## 4. How it is drawn (primitives that exist; one probe-gated option)

Rotation of a picture is NOT established. `DrawChunk` takes a 3 x 3 `xform9` (re/hud.md 8 / 9: the stock passes {0,0,1, 0,1,0, 1,0,0},
`[6]` = scale) and builds an instance matrix from it (0x64ecc0), so a rotation in the screen plane is PLAUSIBLE, but which entries are
which axis is not read. So two ways, the first the default:

**D. Hands from dabs (works with what is proven).** A hand = a run of dabs (113) along its axis with sizes that follow its outline:
- sword: from r 2 to r 19, size 2.8 -> 1.4 px (linear taper), step 0.6 x size, tip dab 1.4; coral on the last third with WatchSeconds=0.
- Mercedes: from r 2 to r 11 size 3.2 constant, then the circle = picture 115 (the thin track ring, an unbroken line) drawn at
  D = 5.5 px centred at r 9.5 (115 is a ring texture: at that size it is a small open circle), then a dab triangle 3.0 -> 1.2 from r 12
  to r 13.5 for the arrow tip. ASSUMPTION: 115 at 5.5 px still reads as a circle (128 px texture, mips not known: review S3 of the rings).
- coral seconds hand (WatchSeconds=1): dabs of 1.6 px from r -5 to r 21, lollipop dab 3.2 px at r 14.
- Minimum dab size 1.6 px (below that a 32 px dab texture minified without mips may shimmer - GUESS from the rings' review S3).
Cost, worst case: sword ~22, Mercedes ~16 + 1, seconds ~28, indices 4 batons (5 pictures) + 8 dots, hub 2, sunk disc 1 = about 85,
against about 20 for today's hand: +65 pictures a frame. Today's worst case is ~205 of a 288 queue (re/hud_hook.md 13): ~270 with
WatchSeconds=1, ~242 with the default. TIGHT: with WatchSeconds=1 the queue cap must be checked (`klu_n_maxinst`), or the dial must give
dabs back (sword step 0.8 x size). The local session must log the peak (`hud: render: ... largest instance count`).

**R. Rotated hand sprites (only after a probe).** Three new pictures (hand shapes baked upright) drawn with a rotation in `xform9`.
Needs (1) a probe key `WatchProbe=1` that draws one upright hand four times with four candidate matrices (rotation in entries [0,1,3,4],
in [0,2,6,8] ...) and logs which; the pictures decide; (2) THREE FREE PICTURE SLOTS - there are none: the 17 slots without a row in the
exe's table are all used (111..118, 123..126, 185, 190) except 14, 20, 26, which the rings review says to avoid (re/hud_rings_review.md N3).
So R also needs a slot answer (pack three hands into ONE texture is not possible either: the picture record's sub-rectangle fields are not
read). R is therefore NOT for this round; D is.

## 5. Wear (light)

- Bake (tools/kl_hud.py, picture 114 = the disc of ALL dials): a radial grain at 4 % contrast, a 1 px darker rim, two or three faint
  arcs of lighter rubbing near the rim at 3 % - one parameter `--disc-wear` (0 = today's disc), default 0.15 on a 0..1 scale; preview
  next to today's disc before anything goes on his game. Because 114 is shared, the weapon dial, escape dial, loot ring and scoreboard
  ring get the same faint wear: consistent with "gritty yet polished", and the cheapest. If the owner wants it on the watch only, a
  second disc picture needs a slot (none free, section 4).
- Index jitter (section 2). Hands stay clean (worn hands read as broken at 69 px).
- NOT done: scratches over the face, a cracked crystal, dirt - all "overdone" territory.

## 6. Last minute

Draft: "the watch becomes a red timer in the last minute". Keep the default as today (`WatchLastMinute=1`: the watch goes, coral mm:ss
digits). `WatchLastMinute=0`: the watch stays, the bezel stroke turns coral, the sword fully coral, digits hidden - for the owner to
compare. GUESS: he will keep the draft's red timer.

## 7. Keys (proposed; all under [HUD], need Dials=1 and the level's extras)

| key | default | meaning |
|---|---|---|
| WatchStyle | 0 | 0 today's watch (one dotted hand); 1 this design (indices + Mercedes + sword) |
| WatchSeconds | 0 | 1 = the thin coral seconds hand as well (section 3) |
| WatchLastMinute | 1 | 1 the coral digits replace the watch in the last minute (draft); 0 the watch stays, coral accents |
| WatchD | 69 | the dial's diameter, virtual px (everything scales with it) |
| WatchProbe | 0 | option R's matrix probe (section 4); log + test pictures only |
Default Draft=1 does NOT switch WatchStyle on until a live check has passed (same rule as Scoreboard).

## 8. Where it goes, and the review checklist for the local work

- Code: a function `klu_watch(cx, cy, left, len)` beside `klu_dials` (or in the proposed klhud_watch.c, re/hud_refactor.md) called
  from the watch branch of `klu_dials`; all pictures through `klu_addpic` (main thread, queued), so no new render-thread code.
- Preview: `tools/kl_hud.py preview-hud` must mirror every number (it does for the rings today) so the owner can judge offline.
- Checklist for whoever reviews the landed WatchStyle work: (1) no new picture slot used other than proven ones, or a probe for it;
  (2) hands are continuous (no visible dab spacing at 1440p: step <= 0.6 x size); (3) wear only in the bake, a key to turn it off;
  (4) no brand mark; (5) the queue's peak logged and under 288 with every dial on; (6) the last-minute behaviour unchanged by default;
  (7) Draft does not switch it on before a live check; (8) the preview mirrors the C numbers.

## 9. Live check W1 (local; owner away)

Bank, `[HUD] Enable=1 Draft=1 Log=2 WatchStyle=1`, pictures every 2 s: at GO (Mercedes at 6, sword at 12, bezel full), at 3:00 left
(Mercedes at 3, bezel half), at 1:05 (Mercedes just past 1, sword at 1), then the last minute (digits). Log: the 5 s `hud: render:` line's
largest instance count. Then `WatchSeconds=1` once. Then the owner judges.
