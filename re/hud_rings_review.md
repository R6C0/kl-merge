# Review: rings as one painted stroke, weapon circle x 0.85, shadows, escape plate (2026-10-12)

Scope: working-tree changes to klhook/klhud.c, klhud_weapon.c, klhud_popup.c, klhud_escape.c, tools/kl_hud.py; level
`build\hud_x6\DM03` (sha1 dfd83f14), `build\hud_x6\preview.png` (zoomed with ffmpeg: watch, escape dial, weapon ring, loot ring),
the draft (hud_mockup.html), kl2.exe. Nothing was run in the game by this review.
Verdict: ACCEPT WITH FIXES. No crash path found. One change (the prompt alpha) very probably does nothing, and the thin
track ring probably breaks into dashes in the game, which is the owner's complaint again.

## MUST

M1. `klesc_full_alpha` (klhud_escape.c 249) is probably a no-op, and if it did work it would destroy information.
re/hud_escape.md 2 (read in kl2.exe): the stock Render itself calls SetAlpha on the Share and Hold lines on every call,
0xff or 0x3f by the usable bytes +0x29 / +0x2a. klesc_prep runs BEFORE the stock Render (klhud_escape.c 342), so the stock
call overwrites our 255 straight away; the 'faint prompts' of S1 are the 0x3f 'not usable now' state. If the write did
stick, usable and dimmed would look the same, and re/hud_escape.md 59 promises 'usable / dimmed state (alpha untouched)'.
Remove the call, or do it where it works (after the stock SetAlpha, only for state 0x3f, and show 'dimmed' another way, e.g. a
darker chalk, not alpha). Expect the owner to see the same faint lines next run if nothing changes.

M2. The thin track ring (slot 115, a 512 px texture with a 5.6 texel line: kl_hud.py RING_STROKE 0.011) is minified 4x
(weapon, D 132 px), 7x (watch, D 72 px), 9x (loot ring, D 55 px). With plain bilinear sampling and no mip chain a 5.6 texel
line sampled every 4 .. 9 texels breaks into dashes. The preview already shows it on the loot ring (zoom at 600,435: the
inner circle is a string of dots, as dotted as the old beads) and a little on the watch. This is exactly 'that circle circle'.
Nothing in the repo shows the game builds mips for these textures (flags are copied from UI_White, 0x60210; the tool's comment
says `fl & ~0x100` of the small icons: whether 0x100 is the mip bit is not established). Fix: bake the track per target size
(a 128 or 256 px texture so that the line is >= 1.5 px wide AND minified by at most 2x), or draw the track with the
family-A / B slice slots (a full thin ring each) rather than one texture shared by 55 px and 132 px rings.

## SHOULD

S1. Picture count against ~320. Counted from the code (worst case, one frame, every part on): list 8 rows x (plate + strike) +
skulls + rule ~ 28; money box 5; watch: disc + track + 2 slices + up to 41 dabs + hand 19 + hub = ~65 (the dab run is longest
when the moving end t0 sits just past a slice boundary: 0.327 x 182 px / 1.5); escape dial: disc + track + slice + up to 33 dabs +
icon ~ 38; weapon: disc + track + 2 slices + up to 74 dabs (t1 just past a boundary: 0.333 x 331 px / 1.5; the stroke 6.3 x 0.25
= 1.58 is above the 1.5 cap) + divider + 2 guns + arrow ~ 82. Queue ~ 220 of 288. Drawn from the render slot, not queued: loot
ring 36, escape plate ~ 6, pop-up ~ 6. Whole frame ~ 270 against 280 proven: inside 320, but only 10 over what has drawn. The
queue drops pictures silently when full (klu_addpic `npic >= KLU_NPIC`), the late ones first (the weapon dial). Cheap cut: raise
KLU_DAB_MAXSTEP to 2.5 and the step to 0.4 x stroke (ripple of a 6.3 px round dab at 2.5 spacing = 0.5(d - sqrt(d^2 - s^2)) =
0.26 px, 0.09 px at 1.5): worst case ~ 150 queued, ~ 200 a frame. Alternative: ARC_N = 6 (six more free slots needed).

S2. Dab runs read slightly fatter than the baked slices. Each edge pixel is covered by 4 .. 5 soft-edged dabs and alpha compounds
(1 - (1-a)^n), so the run's edge is harder and ~ 0.3 .. 0.5 px wider than a slice edge. In the zoom the weapon ring's moving end
(about 8 o'clock) is a visible knob next to the slice before it. Steepen the dab's edge ramp in `_dab_pixels` or lower its ink.
The run also has no wobble or nicks while the slice has them; keep the wobble <= 2 %.

S3. Texture sizes vs on-screen size: A is 256 px for rings of 55 .. 73 px, B 512 px for 132 px. At 1440p (virtual x2) that is 1.8 ..
2.3x, fine; at 1080p 2.4 .. 3.1x. If the game has no mips, bake A at 128 px.

S4. Old levels. `klu_arc_ok` needs 113 and the three slice slots; a level baked with 8 extras (hud_x2 .. x5) under the new hook shows the
discs and texts but NO ring, and the weapon gate in klwd_compose tests only 113 / 114, so the weapon disc and counts draw with no
ring (a half dial). Either fall back to the old dab ring in klu_arc when the slices are missing (klu_dabs over the full range) or
require the slices in the weapon gate. Hook and level must be installed together; tell the owner.

S5. Shadows. `KLU_SHADOW_SMALL 0x40000000` is 25 % opacity (stock 0x80 = 50 %), at 1 px: nearly invisible. Coral labels (TOTAL,
LOOT, REWARDS, DEAD MEN) and the chalk crew names have no plate behind them (only the own row has a block), so on a bright wall
the shadow is what keeps them readable. Prefer 1 px at 0x60 for the small fonts, 2 px at 0x80 stays for the big font. Also the top
byte as alpha is a guess (stock's shadow colour is 0x80000000 at [0xbbe4a4], re/hud.md 202, which supports it); the text
alpha byte at +0x86 is separate, so if the colour setter drops the top byte the change is a silent no-op beyond the 1 px offset.
Look at one label in the next picture.

S6. Weapon circle x 0.85: the label stays ~ 179 px wide ('ZASTAVA M85 . 270' with the baked tracking) under a 120 px disc. Centred on the
disc it overhangs the inset line to the right by ~ 20 px at the default inset (cx = 1280 - 64 - 70.5 = 1145.5, right edge ~ 1235,
inset 1216). Right-align it to the inset or shorten the tracking. Counts (cap 11) were not scaled, the circle was: '30' and '150' sit
24 px above / 23 below the centre and look right in the preview; the gun pictures (54 / 31 px) and the arrow are scaled but
are not in the preview, so check one live round with the other gun picked up.

## NOTE

N1. Ring geometry against the draft (hud_mockup.html lines 378, 387, 418, 544). Direction and start are right everywhere: watch and
escape dial: the stroke is 1 - left .. 1 clockwise from the top (the empty part begins at the top, draft dasharray `0 58.8 92`);
weapon: from the top clockwise for what is left (draft `80 100`, rotate -90); loot ring: the filled part from the top clockwise.
Stroke / radius: watch 0.23 (draft 6/24 = 0.25); loot ring 0.23 at r 22 around a 17 px disc (draft: 6 at r 26 around a disc of 20: the
gap between disc and arc is in the draft, not a fault); weapon 0.12 against the draft's 6.5/43 = 0.15 (thinner; fine for 'keep it
light', family B could be 0.14). Seams between the three slices: none seen in any zoom.

N2. Slice joins. The slices share one wobble function of the global angle and overlap by 0.7 degree; the overlap double-blends over about
1 texel of the edge, not visible. A flat butt end appears only when a moving end falls on a slice boundary (within 1e-4) and changes to a
dab run with a round end a frame later. On a full ring the round caps at 0 / 360 degrees coincide: no notch. The six nicks on the
slice textures come and go as a slice turns into a dab run; small.

N3. Slot verification. The 17 slots with no row in kl2.exe's per-slot table (0xcee058, 183 rows of 200; I walked it: rows are missing
for exactly 14, 20, 26, 111 .. 118, 123 .. 126, 185, 190) are exactly the slots stock levels leave at 0 in their lists. The code has no
named picture for them, the strongest evidence that no stock element reads them. A displacement scan of .text for 12 x slot (+0, +4,
+8) is useless (80 .. 240 hits for every slot, structure offsets), so 'find every reader' is not available; the argument is the table.
123 .. 126, 185, 190 are as safe as 111 .. 118, which drew live (S1). 14, 20, 26 are rightly avoided. These slots get flags
0x10 / type 5 (no row), hence the flag copy: klu_pic_prep fires only when the chunk's flags are exactly 0x10 (a level without the extras has
handle 0 and nothing happens; a slot with a stock row is never touched). `klu_extra_slot` covers 111 .. 118, 123 .. 126, 185, 190; the
loop runs k = 0 .. 199.

N4. Queue sizes: klu_prec is KLU_NPIC + 3 = 291 records; the shared render-slot record (KLU_NPIC) and the two test slots stay in the
array. Every game read is through klh_rd / klh_rd32. No new crash path.

N5. Escape plate. The icon is now always orange (the draft says orange; the green arriving / coral leaving signal is gone, the dial is
the only state cue). KLESC_ICON_INK 0.47 is the measured 14 / 30 of S1: at 62 px the car is ~ 29 px against a bar of cap + 14 ~ 34.
The icon's left edge stays on screen for any bar of 64 px or more.

N6. Money bar: `klu.grid != 2 && total <= 0` is right; `total` is the same round total the fill fraction uses.

N7. Housekeeping: klhud_weapon.c 481 warns about unused `m`, `k`; KLWD_UNUSED_LABEL_DY, KLWD_RING_N, KLWD_DAB_W / H and
KLPU_RING_N / DAB_W / DAB_H are dead: remove them so nobody tunes the wrong number. The preview (kl_hud.py ~ 1857) is a second
implementation of klu_arc in Python; it matches the C numbers (KR 0.40, ratios 0.23 / 0.12, slot arrays) but does not prove the hook:
the first game picture is the test of the hook's arithmetic. I did not re-run `kl_hud.py check` on hud_x6 (the worker reports PASS).
