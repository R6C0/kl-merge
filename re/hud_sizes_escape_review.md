# Review: HUD sizes (quiet round) and the escape-panel restyle - 2026-10-11 night

Nothing launched, no game folder touched, no commit. Sources read line by line: tools/kl_hud.py (diff), klhook/klhud.c, klhud_popup.c, klhud_values.c, klhud_weapon.c (diffs), klhook/klhud_escape.c (whole). kl2.exe (build 0490) re-read with capstone: 0x5d7e00 (Render), 0x793ae0 (Tick), 0x773d50 (Init), 0x5ff260, vtable 0xbbe9d0 and the text vtable 0xbab45c. The baked level `build/hud_x5/DM03/F03_Main.zip` was parsed and `preview.png` looked at.

## MUST

**M1. klesc_style_text never sets the time's INK or the prompts' CHALK colour (sign bug).**
`klesc_style_text(int i, DWORD obj, int rgb, ...)` takes the colour as a signed int and treats `rgb < 0` as "leave" (`if (rgb >= 0 && ...)`). The callers pass `(int)KLU_C_INK` (0xff0c0c0d) and `(int)KLU_C_CHALK` (0xfff3f0ea). Both are negative as int, so `SetColour` is never called. Result in the game: the time stays the stock `[0xbbe494]` = ffcccccc (light grey) on the new CHALK bar (f3f0ea), i.e. nearly unreadable. The prompts stay grey instead of chalk.
Fix: take the colour as DWORD plus a separate `set_colour` flag, or use a sentinel that is not a valid ARGB (for example 0). The restore path (`rgb0`, `c_set`) is already right.

## SHOULD

**S1. The `refused` latch is permanent.** `klesc_tick` sets `klesc_r.refused = 1` on any `klesc_wrap` failure, and `klesc_forget` does not clear it. A transient failure (`osd+0x111c` still 0, or the element not yet FA) disables the part for the whole process, including later levels. Clear `refused` when the osd changes (in `klesc_forget`) and keep it only for the code-mismatch case (`klu_same_code`).

**S2. Silent stand-downs.** `klesc_prep` returns 0 without a log line when a text object's vtable is not exactly `KLU_TEXT_VT`, when `plate == 0`, or when `bar < 0` (only `n_nopic` counts it). Init (0x773e04..) makes the plate and the four texts from level objects by tag 'BOCZ', so the text class is assumed, not read. If E1 shows the stock panel, nothing in the log says why. Add one `klog` per reason, once.

**S3. Stale pointers written at level change.** `klesc_forget` drops `elem` and `osd` but not `klesc_tx[]`, `klesc_dirty_e` or `klesc_r.plate`. The next render of a new element then runs `klesc_restore_texts` / `klesc_plate_back` on addresses of the freed level. The vtable test (`klesc_txt_ok`, `vptr == our pvt`) makes a wrong write unlikely but not impossible, because a new level's text objects can reuse the addresses and have the same vtable (the colour, font and style would be written onto an unrelated text). In `klesc_forget`, `memset` the records and zero `klesc_dirty_e` and `klesc_r.plate` without writing. klhud_popup.c has the same pattern; the review of the popups did not cover it.

**S4. The Cap defaults are tied to the bake, not to the level.** `cd` in klhud.c changed from 19 / 30 / 10 / 15 to 11 / 15 / 10 / 10 for every `Fonts=1` level. A level baked before this round (hud_x4, or any map already installed with the old `kl_hud.py all` step) keeps cap 19 / 30. With hook v14 its text is centred 4 to 8 px off (rows, money box, weapon counts, pop-up). The hook and the levels must ship together, or the hook should read `header[9]` of each font chunk (the preview already does: `CAP = -font(n)[0][9]`). At the least, say in the notes that the old levels need a rebake.

**S5. The font roles are shared with stock elements.** Per re/hud.md 2.2, d54 (H2) is also the font of ZMiniGameButtonMashingDisplay (osd+0x10fc, kldown.c's knock-down prompt), ZHumanShieldDisplay (break free), ZUseActionDisplay, ZCoverDisplay, ZObjectiveDisplay, ZOnscreenMessage, ZPlayerNameDisplay and ZFAEscapeDisplay. d50 (H1) is also ZFAIntroDisplay ("Heist starts in N sec"), ZFAHeadlineDisplay ("Round N"), ZFAAnnouncement, ZFAOutro, ZHeistOutro (the Arcade round-over text) and ZWeaponDisplay. They went from cap 19 to 11 (H2) and from 30 to 15 (H1). kldown.c is untouched, but its prompt now shrinks by 42 %. The intro countdown and the round headline halve. That fits "so its not all in your face", but nobody has seen it. Look at the mash prompt, the countdown and the round-over page in the next live run before this goes onto the owner's tab.

**S6. Vertical anchor of the restyled texts is not proven.** The stock time text uses style 0x01 and the prompts 0x21; the part sets 0x14. What was seen live is that 0x14 (pop-ups) and 0x11 put y at the top of the capitals. The high nibble (0 / 2 / 1) may also select the vertical anchor. If it does, the chalk bar (centred on `top + cap / 2`) and the time will not agree, and the prompts can move by a line. `EscapeDY` moves only the pictures, so there is no key to move the texts. E1 will show it; adding `EscapeTextDY` would make the correction one ini edit.

**S7. kl_hud.py is saved with CRLF.** `git diff --stat` shows 2022 changed lines and `--ignore-space-at-eol` shows 76. HEAD is LF. Convert before committing, or the commit buries the real change.

**S8. Pop-up line step.** `KLPU_LINE_STEP` 24 against the baked H1 line height of 22 (round(1.3 x 15) + 2, measured: H1 22, H2 16, H3 15). A two-line pop-up (the traitor box) grows 2 px per extra line more than the text does. Use 22.

## NOTE (checked, holds)

Sizes:
- The baked caps measure 11 / 15 / 10 / 10 (H2 / H1 / DebugText / H3), matching the new Cap0..3 defaults. Line heights: H2 16, H1 22, H3 15.
- KLUV_NAME_CHARW 6.8 against a measured mean capital advance of 6.88 for H2. Skull lead 12 = inset 6 + gap 6.
- The strike (name width + 8 from x+2) overhangs the name by 4 px on each side.
- Weapon counts keep their middles. On-gun: -36 with cap 11 gives -28.5 (before -28.5). Off-gun: +18 with cap 10 gives +26 (before 25.5).
- Round line to TOTAL: about 12 px of clear space. TOTAL baseline = label baseline. The bar sits 7 px from both. The watch ring bottom (100.5) is above the round label (111).
- The preview shows no overlap and everything centred. Its skulls are solid squares and its ring dabs are blocks, so it overstates the skull ink.
- Skull ratio (picture / cap) is 11 / 11 = 1.0, against 15 / 19 = 0.79 in the run the owner accepted (12 / 19 was "far too small"). It will not read too small.
- Chips: H2 and H3 are chip-free. H1 (17 px) still has chips; with the gentle `_chip` (radius at most about 0.63, at most 3 % of the ink) a 3 px stem survives.
- H1 digits are not tabular ('1' advances 7, the others 10; H2: 5 against 7). The chalk bar behind the escape time follows the text extent, so it will change by about 2 to 3 px per second. Round `bw` up to a multiple of 4 if that looks restless.
- Stock texts at the new sizes: name tags (H2 cap 11) and subtitles / tracker (H3 cap 10, Anton 11 px) are small but legible at 1080p and up. The hook's own clock is hidden while the watch dial is on. Check the last minute and the subtitles live.

Escape, verified in kl2.exe:
- Render 0x5d7e00. Gates: +0x24, +0x28, local player, vt+0x1c8 bits. Order: plate, time, shadow, icon, icon shadow, Share, Hold, bar. All as in the doc.
- The plate Draw is called through `[plate vt + 0x1e8]` with four stack arguments (ctx, cam, pos, xform) and the callee cleans. The `__fastcall` wrapper (two registers plus four stack arguments, ret 0x10) is the right shape.
- The vtable has 11 slots and the next locator follows at 0xbbe9fc. A 13-dword copy is enough, and slot 2 = 0x5d7e00.
- Render copies +0x5c to +0x90 each call, and +0x154 to +0x144..+0x150. The icon shadow colour +0xc4 is never rewritten in Render. So alpha 0 on +0x5c / +0xc4 / +0x154 with a compare-and-swap restore is sound.
- All stock colours have alpha ff (0xffffffff, ffcc0000, ff22ff22, ffaaaa55). Masking the alpha byte takes effect only if DrawChunk honours alpha 0, which is the author's marked guess.
- Tick: the bar width is min(ratio x 80, 80) through 0x5ff260(quad, 0, w), and the quad's +0x44 is A x w, so `quad / (A x 80)` is the health ratio (the NaN case falls to 0). The colour is white while ratio > the threshold, else cc0000.
- The icon row: +0x58 = osd + 0x7f8 (170) or 0x804 (171), and 12 x 170 = 0x7f8. The slot arithmetic is right.
- The prompts' position (+0x30, +0x40) is passed by pointer to Draw. Update rewrites it each frame, and the compare-and-swap restore leaves Update's value alone if it wrote in between.
- Anchor: the screenshot (T2_172s, 1.5625 px per virtual px) gives Share at about y 633 and Hold at about 662, matching ay - 32 and the stock offset. The new health bar ends at about ay - 53, so there is room above the Share line.
- State at stand-down: icon and bar colours are restored unconditionally in `klesc_after`. Texts and the plate vtable pointer are put back the next time the element renders without `act` (before the stock call).
- osd+0x10fc is never referenced. No two wraps share an element: klhud wraps the clock, popup the announcement, weapon the ammo, escape 0x111c. The wiring (include after klhud_popup.c, tick before `klpu_tick`, init before `klpu_init`) does not collide. klhook.c in the repo is not changed yet; the doc's wiring is still to do.
- Minor: the plate's private vtable copy (256 dwords, fallback 161) would break only if the plate class had more than 161 slots and the large read failed. The popup's frame object is the same kind and has 122+ slots.
- The framed bar uses picture 117 stretched (about 0.27 x), while the money bar under TOTAL was changed to 1 px strips (`klu_outline`). They will look different.
