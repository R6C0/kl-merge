# HUD 1:1 review (2026-10-11) - typography, centring, pop-up / ring, against hud_mockup.html

Offline review only. Read: tools/kl_hud.py (DRAFT_SPECS, build_font, preview_hud), the working-tree diffs of klhud.c, klhud_weapon.c,
klhud_popup.c, klhud_values.c, the draft's CSS, build/hud_x3/preview.png, research/shots/V3_DM03_draft_150s.png.
Measured on the real hud_x3 archive (font chunk headers, glyph records of 'H'): see "Measured".

## Measured (hud_x3/DM03, header[9] = ascent offset, 'H' = w, h, xoff, yoff, adv)
- H2 = Text = Menu: header[9] -15, H (10,15,0,-15,10), line 22. Same bake three times.
- H1 = Header: header[9] -21, H (13/12, 21, ..), line 29. Same metrics for two slots.
- DebugText: -11, line 16. H3 (Segoe Black 13, track 3): -9, H (9,9,1,-9, adv 14), line 14. Button: -14, line 20.
- So the hook's Cap0..3 defaults 15 / 21 / 9 / 11 match the bake, and baseline = y + cap holds in the data (glyph yo = -cap).
- Header[2] ("size") reads 20 for 14-18 px fonts and 28 for 25-26 px: its meaning is unknown; the check does not look at it.

## MUST
1. Pop-up bar height is calibrated to the OLD font (klhud_popup.c, KLPU_BAR_LH 1.6). bh = 1.6 * h + 14.1 where h = 2 * the text
   object's half extent (+0x40/+0x44). The 1.6 came from "21 px" = the stock headline font's reported height. H1 is now baked
   with line height 29 (header[5] = round(cap * 1.3) + 2). If the extent follows the line height, the bar is 1.6*29+14.1 = 60.5 px
   against the draft's 47.7 (1.5 x 22.4 + 2 x 7.04). Draft value 47.7 is a constant for one line: use it (or cap based), do not
   scale a measured extent. Width has the same issue (text width is right, padding 61.4 right).
2. Pop-up vertical centring relies on style 0x44 and KLPU_CAP_UP = 3 measured on the STOCK font. How the game derives "middle"
   for nibble 4 (probably from header[5] / header[9]) changes with the new bake (line 29, ascent -21 instead of the stock values),
   so the 3 px is stale for H1 and the capitals may sit several px off the bar centre - the very fault the owner reported.
   The rows already use the exact rule (style top, y = centre - cap/2, klu_cen). Safer: keep the stock 0x14, draw the letters at
   y = barcentre - cap(H1)/2 (21/2 -> 10.5) and drop KLPU_CAP_UP and the SetStyle calls (also removes a vtable call from the render
   slot). Evidence: header[9] of H1 is -21 here, measured live stock ascent offset was -13 for H2 (V3 row 1).
3. H1 serves three jobs with three different draft sizes: total (draft 33 px), ammo (48.6 px), pop-up bar (22.4 px). Baked 26:
   total 0.79 of the draft, ammo 0.53 (preview.png shows "30" at about half the draft's size - the most visible 1:1 miss),
   pop-up 1.16. Applying the file's own 0.9 rule would give 30 / 44 / 20. One slot cannot be right for all; Header (same 25 px bake,
   used by stock headers) and H1 are duplicates, so one of them could be baked at 44-48 for ammo IF the hook can reach it (only
   four OSD refs are known; d48/d50/d54/d58). Otherwise state the compromise to the owner.
4. Stock-drawn text moves with the bake. Header[9] and line height of every slot were rewritten, so every stock text using them
   shifts: name tags / clock (H2: caps top now at y, was about y-1.5; line 22), pop-up letters and headlines (H1), and tracker
   distance + subtitles (H3 = 13 px Segoe Black, ALL CAPS, 3 px tracking, line height 14). Draft: the tracker distance is Anton
   20.5 px with a small coral unit; here it becomes a tiny tracked label. Subtitles and multi-line stock texts become small, wide
   and tight (14 px line). Needs a look at one subtitle and the round-over page before the owner sees it. (the report already lists
   it as a side effect; it is a MUST because H3's tracking is baked into the advance and cannot be switched per text.)

## SHOULD
5. Role -> font offset is an ASSUMPTION (d50 H1, d54 H2, d58 H3, d48 DebugText). klu_make_all calls KLU_REFOBJ(ref) with whatever
   dword sits at osd+off without validating it as a REF (klhud.c, the new loop). A wrong offset yields garbage into a game
   function (possible fault) or silently the FA font (log line only at Log>=1). Check the 'hud: fonts:' line in the first run and
   make a distinct-objects test (warn if two roles resolve to one object, as they would for the duplicated Header/H1 or Text/Menu/H2).
6. Cap values are not read from the level. Fonts=1 + an archive baked before 2026-10-11 (hud_x2, any owner map not rebuilt) puts
   texts 2-8 px off with no warning (header[9] then is the old stock value, not -cap). Read header[9] from the font object
   (or the 'H' glyph record) at make time, or verify against Cap0..3 and log; kl_hud check has no assertion header[9] == -cap or
   header[5] == round(1.3 cap) + 2 for DRAFT_SPECS fonts (check() only tests members, record rectangles, char presence).
7. Sizes against the draft (draft px at 1280 -> baked), all Impact standing in for Anton:
   names 20.5 -> 18 (0.88); crew cash / count 16 -> 14 (0.88); money rows 23 -> 18 (0.78, the table's own 0.9 would be 20.7);
   total 33 -> 26 (0.79); second-gun reserve 18 (1.4cqw) -> 14 (0.78); gun name / labels 11.5 Montserrat -> 13 Segoe Black (1.13,
   cap 9 vs ~8). Bake by matching cap height to Anton's real cap height, not a blanket 0.9 (Anton is not installed, so the
   ratio is unverified here - a GUESS in the file).
8. Letter-spacing: draft names .04em (0.8 px), cash / money / total .03em, pop-up .06em (1.3 px), tracker .05em. Only H3 has
   tracking baked (3 px = .23em against the draft's .25-.32em = 2.9-3.7 px: fine). Impact slots have 0; the pop-up and the names
   are about 1 px tighter per letter than the draft. Small, but visible on long strings.
9. H3 tracking is added after the LAST letter as well (H: w 9, adv 14): right-aligned labels end about 3 px (plus bearing) short of
   the edge ('ROUND 1 OF 10' ends x 1245 against the money values at 1247 in preview.png) and centred labels (gun name) sit
   1.5 px left. Compensate in the hook (x + 3 for right, + 1.5 for centre) or bake the last advance without tracking.
10. Draw-instance budget: dabs now watch 40, escape 32, weapon 64 (was 48), loot 32 (was 20) = up to 168 ring dabs plus rows,
    strikes, skulls; V3 peaked at 279 and the capacity is unknown. Log the peak and refuse nothing silently; run once with the
    loot ring AND weapon dial AND escape dial on screen (a van wait while looting) to see whether pictures vanish.
11. Loot ring: the report could not show it failing. Only draws while crew-record loot state is 1/2 AND the money object's vtable
    matches; PopupTest (12 s cycle) is the right way to see it. Keep the fallback (call klpu_ring_draw from klu_render_elem) ready.
    Dab 9 x 8 on r = 26 with 32 dabs: spacing 5.1 px against ink 5.3 x 5.9: touching, fine; draft stroke is 6 px.

## NOTE
12. Row centring (computed): block middle rc = row top + 9 (block y-5 .. y+23). Names cap 15: top floor(rc-7.5+.5) = rc-7, rows
    rc-7..rc+7, ink centre rc+0.5. Cash cap 11: top rc-5, ink centre rc+0.5. So both 0.5 px low, equal to each other: correct.
    '$' and ',' extend past cap height, so the ink of cash strings sits about 1 px lower than the capitals. Horizontal: name at
    block + 12, cash right edge at block - 12 (preview 41 / 236 in a 29..248 block): equal. Skull 15 px at rc-7.5: centred.
    The strike (4 px at rc-2) is centred; in the V3 picture dead rows were struck over the text's upper half, expected fixed.
13. Non-centred texts keep the old baseline y+13 by drawing at y + 13 - cap. Right only where the old font's baseline was 13
    (names font). The Total (old big font) and weapon counts used another baseline, so they move by their old ascent minus 13 -
    unmeasured; compare Total in the first picture.
14. Round line colour chalk now matches '.clock .round' (S5's coral was wrong). Draft's 'Round' text size is .9cqw label: OK.
15. Draft clock digits (4.1cqw = 52 px) have no counterpart: the stock clock digits are hidden behind the watch. Not a type issue.
16. Atlases are baked at virtual 1280x720 pixels and scaled by the game: at 2560x1440 an 18 px Impact is drawn 2x (the V3 picture
    is soft), at 4:3 or ultrawide the layout (fixed virtual pixels, right edge 1247) follows the game's own 16:9 virtual screen
    only; nothing here is aspect-aware. Not new, but 1:1 sharpness would need a 2x bake (atlas page limits: 'does not fit the page'
    error exists in build_font).
17. Style byte klpu_style: reads obj+0x84 unguarded (like the existing +0x14 reads) before any klh_rd; text objects come from the
    element just checked by klh_rd32 vtable, so low risk. The put-back runs through klpu_restore on every non-draw call: fine. Order
    in klpu_render_ann is right (style set in klpu_popup before the stock Render draws the letters).
18. "All that one font": the HUD now has two faces (Impact for display, Segoe UI Black for labels) as the draft has two (Anton,
    Montserrat). It will still read as one display face because Anton is replaced by Impact; real Anton would need installing the
    font on the bake PC only (OFL, glyphs are baked into the level) - owner's decision, previously declined.
19. Preview tool limits: preview.png draws only own row block, strike, skull squares and texts, so it cannot show the pop-up bar,
    rings or any stock text; it therefore proves the row/label centring only.

## Order for the first run
fonts line ('hud: fonts: ...' roles resolved?), a picture of the rows, then PopupTest (pictures every 2 s), then a stock subtitle
and the round-over page for the H3 / H1 side effects.
