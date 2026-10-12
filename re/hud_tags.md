# HUD tags over the heisters' heads: initials in the new look (2026-10-12)

Owner: 'initials for like above their head'. Part: `klhook/klhud_tags.c` (new; hooks in klhud.c: `klht_render`, `klht_tick`, `klht_init`; one include
line in klhook.c). Static reading of kl2.exe (build 0490). NOT RUN IN THE GAME. Builds: `<work>\build\klhook\hud_v20_test` (TEST) / `hud_v20_ship` (SHIP).

## 1. What draws the tags (read in kl2.exe)

**The tags are the FIRST LOOP of `ZFAPlayerListDisplay`'s Render** (vtable 0xbbdf6c slot 2 = 0x5e60f0). The same function then draws the
top-left block and the crew rows, so the element cannot be split by hiding parts; klhud hides the whole element (+0x25), so the tags went too.
(re/hud_names.md 'the tag element is not identified' is answered: it IS this element.)

Annotated pseudo-code (el = the element, ctx / cam = Render's arguments, `rules` = [0x168e598]):
```
5e60f0 Render(ctx, cam):
  5e6102 if !0x7bb2a0([0x168e9e4])            return            ; the session's client table exists (state 4)
  5e6115 if 0x8e6a20(rules) != 0x19           return            ; state 0x19 = round running (NOT 0x17 / 0x18)
  5e6129 if [0x168e59c] == 2:  0x5090a0(el, ctx, cam)           ; another mode only
  ; --- A: THE TAG LOOP -----------------------------------------------------------------------------------------
  5e614a for i in 0 .. [el+0x28]-1:                             ; E = el + 0x2c + i*0x10c   (entry, at most 12: 0x470b65)
  5e6160   if byte[E] == 0xff continue                          ; byte[E] = the client / record id
  5e6174   if 0x7f6850() (Arcade):                              ; the else branch is the other session modes
             recs = 0x508ef0([0x168e9e4], id)  -> rules object  ; (0x508ef0 returns [client table + 0x54] when [rules+0x5c] == 4)
             rec  = 0x7fd930(recs, id) = [recs+0x348] + 0x7c*id ; the crew record: id == the record's index
             node = (byte[rec+0x79] & 1) ? [rec+4]              ; an AI heister: the actor, from the record
                                          : 0x5c3b10([rec])     ; a human: his player node
  5e61df   if byte[el+0xed8] || dword[E+0x10] in {1,4} || dword[E+0x14] in {5,6}:
             0x7b8150(this = E+0x38, a1 = [el+0x10], node, ctx, cam, a5 = [el+0xc])      ; ret 0x14
  ; --- B: the local player's block: texts [el+0xea8]/[+0xeac] (name + 'Total score' + 'Round', built by 0x6f3000: 0x6f3403, 0x6f3982),
  ;        [+0xeb0..+0xecc], [+0xed0], pictures via 0x80a690(entry [el+0xefc]) at E+0xa8 / E+0xdc, skulls - alpha from the cross-fade
  ;        state [el+0xee0] / [el+0xf00] (0 block, 1 both fading, 2 list): 0x5e622c, 0x5e66b1
  ; --- C: the crew rows: for i in 0 .. [el+0xe5c]-1 (0x5e6e11 .. 0x5e7893), the row texts E+0x18..E+0x34 (built by 0x929800)
```
**0x7b8150 (the tag drawer), this = the tag struct `E+0x38`** (size 0x44): `[this]` = a ZCHAROBJ (the text), `[this+4]` a picture desc, `[this+0x40]` a byte
tested first (0x7b8156). Body:
```
  if !byte[this+0x40] return;  if !node return
  pos  = 0x8d3150(node)                                    ; the actor's world place
  box  = node->vt[0x340](node, 0x8cb2e0(node))             ; its top (bounding box); pos.y += box.top + double[0xb23668]
  m    = node->vt[0x670](node); 0x873dd0([m+4], &t) ; ...  ; the model / frame the point is projected through
  0x585ca0(... , 0x154d9d0 = the virtual screen vector ...) ; world -> screen (virtual 1280 x 720)
  if 0x793550(cfg, 0xb56534): ctx->vt[0x14](...)           ; an optional picture from [this+4] (not seen on screen in the pictures: off)
  scale = (1/[T+0x14], 1/[T+0x18]) with T = [0x154d9e0]+0xc ; 0x8946f0
  [this]->vt[0x1e8](ctx, cam, &pos, &scale)                ; ZCHAROBJ::Draw - the text, once
```
Exactly ONE text object is drawn per tag; no distance fade or alpha was found in it (the pictures' name over 'Total score' is the block B).
The struct's text is made by **0x51f3b0** (called from the entry builder 0x470be6 and from 0x7dba1f): a ZCHAROBJ, style 0x44 (centred), colour [0xbbe494]
(0xffcccccc), layer 0xf, the FA font; [this+4] = 1 and the desc only if config 0x793550 says so. **WHO WRITES THAT TEXT I DID NOT FIND**: not 0x6f3000
(only the block B: its `$%i` 0xb5bf60 is the LOCAL player's total), not 0x929800 (the row texts), not Render. So whether the stock tag re-reads the record's
name every frame is NOT established - which is why this part does not depend on it (section 2). The earlier N1 guess (NameTags rewrites the record's string)
stays available (`NameTags=1`) but is no longer the default.

Also read: `0x76db00` (Tick, slot 5; runs hidden too, state 0x17..0x19) advances the cross-fade and calls 0x6f3000 (refresh) and 0x412dc0; slot 6 `0x72be40`
(Update) places the block's texts from the transform. A cut-scene hide `0x75f780` sets +0x25 of this element WITH the clock (re/hud.md 2.3).

## 2. The route taken, and why

The element cannot be split: blanking B and C would need every picture's alpha zeroed inside one Render call (only texts can be blanked, ' ' is proven; pictures
only by a ctx wrap) and a cut of the cross-fade state fights klfedkit's HudFade (klfedkit.c writes +0xee0 / +0xf00 when it reads 1, `fedkit: hud: the player list's
cross-fade cut`). **So the element stays HIDDEN** (klhud's HideStock, nothing blanked, nothing to restore) and **the hook runs loop A itself** from the clock
element's Render slot (the one place whose draws are proven): same state gate (0x19), same entry walk, same conditions, same node - and the same call of the
game's own 0x7b8150, but on a COPY of the tag struct (`tag[0x44]`) whose text pointer is one of OUR ZCHAROBJs. The game does the projection; we choose words, font, colour,
shadow. The record's name string is never written (kill feed and score page keep full names): **NameTags defaults to 0 whenever HeadTags is on** (klhud_names.c).

- Entries drawn: bots only (`rec flag bit 0`, the klb 'bot'), never the local entry (`[el+0xefc]`), only crew / traitor / other-human rows (dead, escaped, fed: none).
- Initials: `klnm_tag_ini` (new, klhud_names.c: the table klnm_refresh already makes, among the AI heisters of the round, unique 'LI' / 'LY'); no table (no wardrobe
  match) -> the initials of the record's own name string.
- Fonts: initials in the NAMES role (Anton, quiet cap 11: the condensed heavy face keeps two letters legible small; the label font Montserrat is wider and lighter),
  the money line in the SMALL-figures role. Colour: chalk (0xfff3f0ea); a traitor ORANGE (0xffe8831f) - the element does not know traitors, klbot's flags do (the same
  `kluv_kind` the crew list uses); money green (0xff4f8f49). Shadow: a second object in 0x60000000, 1 px, drawn first.
- The money line is a SECOND text object drawn through the same copy (HeadTags=2) with `SetOffset (0, line)` (0x45d6e0 via vtable +0x21c, the stock offset call).

## 3. Keys ([HUD]; Enable=1, HideStock=1)

| key | default | meaning |
|---|---|---|
| HeadTags | 1 under Draft, else 0 | 0 none (tags go with the hidden element, as before), 1 initials, 2 initials + money line |
| HeadShadow | 1 | the 1 px shadow object |
| HeadLine | names cap + 5 | the money line's distance below the initials, virtual px |
| NameTags | 0 with HeadTags, 1 under Draft without it | the record rename of klhud_names.c (kill feed / score page then show initials too) |

With `HideStock=0` the stock draws its own tags; this part is idle then. Log: `tags: HeadTags=..` at start; `tags: on ..` once a level; Log=2: `tags: entry i (record id at ..):
initials 'A' -> 'B'`, and every 5 s `tags: N tag draws, n without a node, n by the stock conditions, n with the drawer's flag clear`. Stand-down lines: an object could not be
made; 0x7b8150 not the known code.

## 4. Interplay

- klhud HideStock: unchanged. The tags act only while `klu_r.hid` (the element hidden BY US) and state 0x19; at a stand-down / the game's own hide (clock hidden) the clock Render
  does not run and the tags stop with it.
- klfedkit HudFade writes +0xee0 / +0xf00 of this element: our loop never reads them and the hidden element never draws them: no conflict (as before).
- klhud_names NameTags: off by default now; with NameTags=1 AND HeadTags the record holds initials and the tag draws initials of the record's initials-from-table: harmless but pointless.
- Ours reads the element's entries every frame (id re-checked against the tick's table, bot node re-read: two checked reads a tag) - the stock element's memory is only READ.

## 5. Guesses / risks (all in this build, none run)

1. `[el+0x10]` / `[el+0xc]` are passed as the stock passes them; 0x7b8150 does not appear to use `a1`/`a5` (not proven).
2. **The offset unit of SetOffset** (money line, shadow): taken as virtual pixels, y down. If the shadow does not move, the shadow sits under the letters (invisible, harmless).
3. A bot's node is `[rec+4]` when byte[rec+0x79] & 1 (read from 0x5e619e/0x5e61aa); the hook tests klbot's flag bit 0 instead, which should be the same byte (flags = a byte of the record).
4. The copy absorbs writes of the drawer to the struct; if the drawer needs the REAL struct's picture desc to persist across frames, the optional picture (0x793550) would flicker - it is off in the pictures.
5. Drawing one object twice a frame is not done (one object per entry and role); the shadow is a second object.
6. If the stock tag shows more than a text (an icon), it is gone: only text is drawn.
7. The tag's vertical anchor: name over money was ONE text in the stock (probably 'name\n$n'); ours are two objects, line distance by key.

## 5b. Review round (re\hud_tags_review.md, ACCEPT WITH FIXES)

- **M1 DONE**: `klht_reset()` (klhud_tags.c) is called from `klu_reset` inside `klu_cs`, next to `klwd_reset()`; it clears `klht_r` (keeps only the "told" flag), so a reload at the same template address cannot reuse freed objects. The `tmpl` compare in the tick stays as a second guard.
- **S1 DONE**: `klht_render` samples the draw-instance count (ctx[1]) after the tag loop into `klu_n_maxinst`. Measuring still owed: G1 with 7 bots and HeadTags=2.
- **S2 DONE**: the world tag is orange only for the SCORE flag (`KLUV_F_TRAITOR`), not for the bot's own mark (flags&2), so a not-yet-turned bot does not show through walls. (The crew list is unchanged.)
- N1..N6: not changed (N1 fallback initials are not unique and switch to the table value later; N2 tags can blink while the tick holds the lock; N5 aboard bots keep a tag as in stock).
- Builds: `hud_v21_test` 2F1C86EA, `hud_v21_ship` 3E90EF58 (git archive HEAD klhook + working klhud*.c + klhook.c).

## 6. Live check G1

Hook `hud_v21_test` (or ship), archive `<work>\build\hud_x6\DM03` swapped in, `[HUD] Enable=1 Draft=1 Log=2` (HeadTags defaults to 1), `[Crew] Random=1`, an idle player among the bots,
pictures every 2 s. Log must show: `tags: HeadTags=1 ..`, `tags: on (HeadTags=1): the stock element ... stays hidden ...`, per bot `tags: entry i (record ..): initials '' -> 'K'`,
and the 5 s line with growing `tag draws` and few `without a node`. Pictures: each visible heister has one or two chalk capitals over his head, orange on a traitor, no 'Tommy / $0',
none over your own head, the top-left block still absent, no tag left over a dead heister. Then HeadTags=2 (money line under the initials in green; check the line distance and the shadow),
then NameTags=1 to see the fallback. Also with 7 bots and HeadTags=2 read the `maxinst` field of the 5 s `hud:` line (peak draw instances; S1) and play two rounds in one process (M1: no fault, `tags: on` logged again after the reload; "told" is kept so it may not repeat - then look for `tag draws` growing). FAIL readings: no `tags: on` line (conditions: state 0x19, `klu_r.hid`); `tag draws` 0 with entries -> look at `n with the drawer's flag clear`
(the stock never set E+0x78: then entries must be found another way) or `without a node`; tags in the wrong place -> a1/a5 guess (1).
