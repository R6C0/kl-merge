# HUD audit, 2026-10-12 (offline, from pictures only)

Source: G2_DM03_tags_70..190 s (sheets every 4 s, plus 94, 102 full size), R1p_DM03_rings_111 s, S1_DM03_quiet_104 s. Nothing was run in the game.
Frame = run + seconds. Severity: H = readable / plainly ugly in normal play, M = noticeable, L = cosmetic.

| Frame | Element | Fault | Sev | Fix |
|---|---|---|---|---|
| G2 94, 98, 102, 106 | initials above heads | letters 9 px high, thin, no backing: vanish on pale walls and on the lit square (G2 78/82 frames) | H | v22: big face (cap 15), four-way dark outline (HeadOutline=1, HeadFont=1); optional dark tab (HeadTab=1, GUESS) |
| G2 94, 102, 106 | initials | tags are drawn for crew that are behind walls (LY R B M A hang in a bare concrete room). The stock drawer does not test sight; the stock list drew them the same way (unverified) | M | not fixed: needs a visibility test per record (kl2 line-of-sight call not read). Next candidate: fade by distance / hide when the stock's own "on screen" byte is 0 |
| R1p 111 | pop-up bar vs loot ring | ring (centre y ~550, r 22) overlaps the bar's lower edge (bar 504..542) | H | v22: PopupLift=1 lifts bar + letters clear of the ring (gap 6 px) while it shows |
| G2 178..190 | weapon label | 'ZASTAVA M85 . 270' ends at x 1268 of 1280, past the 5 % inset and nearly on the screen edge | M | v22: centre pulled in so the estimated right end is <= LabelRight (1256); LabelCharW 10.5 is a GUESS from this picture |
| G2 94..110 | red discs / arcs | big translucent red discs, black blobs and a red arc over the scene. They also show in S1_104 (no HUD tags involved) and the arc is a hit-direction mark: the game's own damage indicators, still in the old (soft) look | M | not changed: restyle candidate (stock texture, not our data) |
| G2 70..82 | pre-round | stock 'FRAGILE ALLIANCE ARCADE - ROUND 1 / LIVES LEFT / HEIST STARTS IN 7 SEC' panel: old grey plate, old font | M | restyle candidate |
| G2 70 | loading page | stock black page with camera stills, 'Buffering 100%', tip line in a third face | L | candidate |
| G2 118 | 'F TAKE HUMAN SHIELD' prompt | stock small white text, red key, no backing; fine in the dark, thin on bright | L | candidate (same kind as the prompts below) |
| G2 158..166 | 'YOU JUMPED INTO THE GETAWAY CAR' | painted chalk bar, ink text: correct. Sub-lines 'SHARE 50/50 WITH THE DRIVER' / 'SPACE HOLD ESCAPE VEHICLE' stay stock: dim grey, almost unreadable on the dark floor | M | candidate: the use-prompt texts |
| G2 154 | escape plate | restyled plate right; green car icon, white bar, time. OK | - | - |
| G2 166..178 | crew list while dead | dead rows struck + red: correct; one frame (G2 174) shows rows 3-5 red with a stray small glyph left of 'MITCHEL' (stock mark under our list) | L | check live |
| G2 182..190 | round-over / score pages | stock look: 'ROUND 1 ROUND OVER' translucent grey panel, then the black score page in the stock face. On the score page 'ROUND SCORE' is printed over '$585,791' (the total row's two texts overlap) | H (page) | the menu bake (kl_hud_menu.py) is built but never run: owner's decision / live check M0 |
| G2 190 | score page | stock cursor arrow top left of the panel frame | L | - |
| S1 104 | own row | the human's row reads the profile name 'R6KXO' (a stock name, not a character) while the bots show characters | M | candidate: show the character's name for the human too |
| all | round watch | the dial's hand is drawn; 'ROUND 1 OF 10' is right of it, fine | - | - |
| all | list / money box | no overlaps; 'TOTAL' bar fills with loot; REWARDS $0 | - | - |
| consecutive frames | flicker | none seen at 4 s spacing (2 s spacing for 94..102 looked steady). Not measurable from stills | - | - |

Not rated: subtitles and the knock-down / break-free prompt did not occur in these runs (no downed player, no voice subtitle in the frames looked at). They share the smaller fonts: still to be looked at in a live round.

## v22 changes (hooks hud_v22_test / hud_v22_ship)
- klhud_tags.c: HeadFont (default 1 = big face), HeadOutline (default 1), HeadTab (default 0, GUESS), HeadTabPadX/PadY/DY.
- klhud_popup.c: PopupLift (default 1), PopupLiftGap (6).
- klhud_weapon.c: LabelRight (1256, 0 = off), LabelCharW (10.5).
- tools/kl_hud.py unchanged: no rebake needed.

## Live check A1 (owner away)
Bank, hud_v22_test, [HUD] Enable=1 Draft=1 Log=2 HeadTab=1: (1) pictures of the initials against a bright wall; (2) the log line 'tags: tab: first tab at (x, y)' and a tab centred behind the letters (if it sits off, HeadTabDY / the read of +0x3c is wrong: set HeadTab=0); (3) loot a case: bar clear of the ring; (4) the weapon label's right end <= x 1256; (5) look at the outline alpha (KLHT_C_OUTLINE 0xd8080808 is a GUESS: if the outline is too grey/black, the alpha byte is not honoured).
