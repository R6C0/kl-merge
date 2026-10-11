# Centre pop-ups and the loot ring (track P, 2026-10-11 night) - NOT RUN IN THE GAME

`klhook/klhud_popup.c` (new, untracked, NOT wired): `[HUD] Popups=1` and `[HUD] LootRing=1`, both default 0, both need
`[HUD] Enable=1` and draw only while klhud.c draws. SECOND FORM after its review (`re/hud_popup_review.md`; section 10
says finding by finding what was done). Compiles with HEAD b216248's klhud.c, alone and together with the two sibling
HUD parts (section 6). **The pop-ups are NOT complete: the kill / money lines and the countdown stay stock (section 9).**
Words: **READ** = read in kl2.exe build 0490 (static, capstone); **file** = read in a file of this repo; **GUESS** = neither.
Nothing here was seen in the running game. Scratch: `<scratchpad>\P\` (`p.py`, `ann_sites.txt`, `osdrefs.pkl`),
`<scratchpad>\Pfix\` (`d.py` = disassemble ranges; the fix round).

## 1. ZFAAnnouncementDisplay - the centre message (all READ)

`[osd+0x10a8]`, vtable 0xbbdd34, 0x3c bytes, made only in FA / Arcade (`re/hud.md` 2.2).

| slot | routine | what it does |
|---|---|---|
| 4 Init | 0x7cbce0 | frame `+0x38` = a child of the level object named `BackgroundFrame` (looked up by name, 0x7cbd37), style 0x14, **layer 0x17**; text `+0x28` = ZCHAROBJ, style 0x14, colour `[0xbbe494]` = ffcccccc, font = Init's font argument, byte `+0x9c` = 0x20, **layer 0x19**; shadow `+0x2c` the same with colour `[0xbbe4a4]` = 80000000, **layer 0x18**, byte `+0xbc` = 1. `+0x24` = 1 |
| 6 Update | 0x71d9c0 | `x = [0x154d92c] (0.0) * scale + 1280 * 0.5 = 640`, `y = [0xcedc78] (-60) * scale + 720 * 0.75 = 480`; SetOffset(scale, scale) on frame, text, shadow |
| 5 Tick | 0x4f1ea0 | Arcade / FA with a rules object: when `0 < [+0x30]` and `(int)([+0x30] * 1024) < clock` (`clock = [[0xdd2640]+0x48]`): `0x468430(this, "", 5.0)` = clear, `[+0x30] = -1.0`; then once (`+0x35`) the follow-camera element's hide byte `[osd+0x10a4]+0x25` is put back from `+0x34` when the session state is 0x19 |
| 2 Render | 0x4895b0 | Arcade / FA only. `xform = 0x7f07a0`. **While `clock < (int)([+0x30] * 1024)`**: the frame is sized from the STRING `[[text+0xa4]+0xc]`: `w = (characters of the first line * 15 + 15) * scale`, 20 a character when the string has five or more `W` / `w` (bytes 0xcedc7c = 20, 0xcedc7d = 15, float 0xcedc80 = 15), at least 300 (0xb6d240 / 0xb146e0); `h = (lines * 30 + 40) * scale` (byte 0xcedc7e, float 0xcedc84); `frame->vt[+0x218](0xff)`, `frame->vt[+0x23c](w, h)`, `frame->Draw` at `(x, y - 25, z)` (0xb5bbb0 = 25.0). **Then always** (0x48978a): `text->Draw` at `(x, y)`, `shadow->Draw` at `(x + 2, y + 2)` |

**The setter**: `0x468430(elem, const char *text, float seconds)`, thiscall, `ret 8`, NOT a virtual. Empty string: both
texts "" and `[+0x30] = -1.0`. Else SetText on text and shadow, `[+0x30] = (clock + seconds * 1024) / 1024`
(0x46848e .. 0x4684b8: `clock - (int)(seconds * -1024.0)`, `* 0.0009765625`), and the follow-camera element is hidden
(`[osd+0x10a4]+0x25 = 1`, its old byte kept in `+0x34`, `+0x35 = 0`).

So: **no message id, no colour and no fade are kept** - one string and one end time. WHICH message shows can only be told
from the text. Colour is set once, at Init. The whole element is hidden with the FA set by 0x75f780 (`re/hud.md` 2.3) and
is one of the few drawn while `osd+0x1225` 'HUD off' is set.

A second way into slot 2 (review N1, READ by the reviewer, not re-read here): slot 11 (0x63d590) calls Update, shifts the
place by 0.1 and calls slot 2 through the vtable; the OSD calls it from 0x64f99c in session states 0x29 .. 0x2b. klhud.c
does not draw there (`klu_draw_on` = 0), so the wrapped slot only passes on (and puts back, section 5).

The y float `[+0x18]` is read ONCE in Render (0x48960d, into a local) and serves the frame (y - 25) and both texts. The
frame's size is multiplied by float `[0xcee050]` (0x4896c7; 1.0 in the file, who writes it at run time was not followed).

Geometry that follows (GUESS, from the numbers above): the frame's top is 25 px above the text's y and a one-line frame is
70 px high, i.e. 25 + a ~22 px line + 23: **the text's y is its top, and frame and text are centred on x**. Style bytes
seen so far: 0x12 right-aligned at x (the clock, live), 0x44 centred at x (run H1_DM03_hud, HEAD c9d654d); 0x14 shares
0x12's high nibble and 0x44's low one - 'centred, y = top' fits both.

## 2. Every caller of 0x468430 (27 sites, READ; `ann_sites.txt` has the context of each)

All pass `[0xbcb330]` = 5.0 s unless noted. Section = the .LOC section, key = the key; `{..}` = placeholders replaced by
0x83e2e0 / 0x784e40 before the call. 'Arcade' = the site is in `ZGameRulesHeist`'s own vtable or reached from it as far as
this reading went; 'shared' = a routine of the FA rules base that Arcade inherits (its caller chain was NOT followed:
whether Arcade reaches it is a GUESS by the key's meaning); the English wordings are NOT read (the level's .LOC was not
opened) - those in quotes were seen in pictures of our own rounds (CLAUDE.md, `re/fa_round.md`).

| site (function) | section / key | when (by key and code) | Arcade? | our look |
|---|---|---|---|---|
| 0x67f03e (0x67ee80, called from 0x8fb15a = `ZGameRulesHeist` slot 129, 0x8fb0d0) | Announcements / `FA_Become_Traitor`, no placeholder | only on the machine of the player who turned (0x67ef61 `cmp al, bl`), and only with the routine's 'announce' argument set - **see 2.1: often NOT shown** | **yes** | **ORANGE letters in the painted box** |
| 0x6b35f3 (0x6b34f0) | Announcements / `Looting_Started` | the first loot ('Looting has started ...') | shared, yes by our rounds | chalk bar, ink |
| 0x5369b8 (0x5368a0) | Announcements / `Loot_Gone` or `Loot_Gone_Police` (+ a replace) | all loot taken | shared | chalk bar |
| 0x69d77d (0x69d4d0, called three times from Heist slot 45, 0x6840a0) | Exit / `FA_YouBoard` or `FA_YouBoard_Chopper` (also builds Exit / `FA_Board` with a name for the others) | you board: 'You jumped into the getaway car' | **yes** | chalk bar |
| 0x6da0aa (0x6d9ee0) | Exit / `FA_Escaped` with `{Player_Name1}`; Exit / `FA_YouEscaped` | somebody / you escaped | shared | chalk bar |
| 0x781eeb (0x781d80) | Money / `FA_Reward` with `{Reward1}` | a reward is paid | shared | chalk bar |
| 0x6c41b0 (0x6c4080, from 0x670987 = inside 0x6706b0, the 'human killed crew' routine klfedkit.c reads; 0x6706b0 is called from Heist slot 16 at 0x4857b9 and slot 11 at 0x70472f) | Money / `FA_Revenge` with `{Reward1}` | revenge on a traitor pays | **yes** | chalk bar |
| 0x4d29cf (0x4d27c0) | Announcements / `FA_Killed_Dirty` with `{Reward1}` | a dirty cop killed | FA modes | chalk bar |
| 0x704b79 (0x704a10 -> 0x463b70, 0x663c80; called from Heist slot 16 at 0x4857d1 and slot 11 at 0x70474a) | Announcements / `FA_Killed_Merc`, `FA_Killed_UCC` (+ names, rewards), or `FA_CnR_Revenge` | a kill's line (which branch Arcade takes: not followed) | **yes** (the call) | chalk bar |
| 0x6fff68 (FA slot 121, 0x6ffdc0), 0x868bb1 (0x8689c0) | Online / `FA_NoFriendlyFire`, `FA_NoFriendlyFireUCC`; **3.0 s** (`[0xb4a174]`) | you shot a crew member | shared | chalk bar |
| 0x4c639e (0x4c6330) | Announcements / `Police_Respawn` | you return as police | shared (klfed.c's fed path: likely) | chalk bar |
| 0x880b6c (0x880850) | Announcements / `FA_Become_Dirty`, `FA_Become_Dirty_UCC`, `FA_UCC_Dirty` | dirty cop | FA modes | chalk bar |
| 0x5571db, 0x5c3312, 0x5dda32 | Announcements / `FA_UCC_FailedMission(_You)`, `FA_UCC_CrimeCommitted(_Mercs)`, `FA_UCC_KilledBeforeCrimeCommitted` | Undercover Cop mode | no | chalk bar |
| 0x5e27e9, 0x663d16, 0x6c7ca6 | Announcements / `FA_CnR_GotRevenge`, `FA_CnR_Revenge`, `CnRSuddenDeath` | Cops and Robbers mode | no | chalk bar |
| 0x74c4cf (ZSessionManagerMultiplayer slot 26) | `AllLevels/Menu/Online/Status/` / `NewGameAnnouncement`, 3.0 s | multiplayer session | no | chalk bar |
| 0x5b17f2 (FA slot 194, not Heist's) | built from other texts, not followed | FA's vehicle part | no | chalk bar |
| 0x8a8857 (Heist slot 21), 0x6c2588 (FA slot 21), 0x8fad0e / 0x8fada9 (Heist slot 194), 0x8bc7ff (ZFADeathCamDisplay Render), 0x4f1f0e (the Tick) | `""` | CLEAR: respawn / state 0x19 entered, the vehicle's state changes, the death camera, time over | - | - |

Whatever text arrives there gets the chalk bar; only a string equal to the level's `FA_Become_Traitor` gets the box.

### 2.1 When the traitor message really comes (review S2; READ in this round)

Heist slot 129 (0x8fb0d0) does its work only while the session state is not 0x1f, `[rules+0x1b3]` is 0xff and the
player's flags (`vt[+0x1c8]`) have none of 1 (already a traitor), 0x20, 0x40. It then calls 0x67ee80 with 'announce' =
**1 only while `[rules+0xe84] == 0`** (0x8fb13a .. 0x8fb153), else 0. `[rules+0xe84]` is counted up at 0x670a34, inside
0x6706b0 (the 'a human killed a crew member' routine), reached from two branches that do NOT turn him (0x6709fc: the
victim already has flag 1; 0x670a11: `vt[+0x1e8]` says yes) as well as the turning one. It is set from `ebx` in three
initialisers: 0x4fb675, 0x74bd24, 0x83577d (at 0x83577d the neighbours are written from `bl` / `ebx` as zeros - a round
initialiser; that `ebx` is 0 at the other two, and when they run, was NOT followed).
So:
- the message comes at the FIRST counted crew kill by a human in the counter's life, if that kill is the one that turns him;
- **a later betrayal raises the traitor flag with no centre message at all** - nothing of ours is drawn then, by design;
- traitors made by other paths (klbot.c Backstab = a bot; klfedkit.c's writes) do not pass slot 129's message: no box.
The traitor MARK in the middle of the screen at such a kill is the points pop-up's line (0x8fb200 .. 0x8fb21a), which
this part does not restyle (section 3).

## 3. The other elements that write in the screen's middle (READ unless marked; none is restyled by this part)

| element | where it draws | what | why it is left stock here |
|---|---|---|---|
| **ZHeistPointsPopupDisplay** `[osd+0x10b8]`, vtable 0xbbde64 (14 slots) | text `+0x28` / shadow `+0x2c`, style 0x14, layers 0xf / 0xe (Init 0x5ab8b0); `x = 640`, `y = 360 - 90 = 270` (Update 0x635420); end time `+0x30` as above, a queue from `+0x34`; setter 0x433140(elem, text) | Arcade's **kill and money lines**: `AllLevels/Interface/Online/Kill/` + key with the reward (0x4ae130; Heist slot 16 0x485740 -> 0x485b7b), the traitor fine of 0x6706b0 (0x670941) = 'You killed a criminal. $0', Heist slot 129's 0x8fb200 (the traitor mark) | Its Render 0x549480 MOVES and FADES the pair inside the call: an offset `(t, 30 t)` with `t = (clock/1024 - end) / 1.5` added to the place, alpha `2 t * 255` under `t < 0.5` through `vt[+0x218]`. A bar would have to follow that maths frame by frame; black letters without a bar cannot be read. NEXT STEP if wanted: the same wrapper, bar at `y + 30 t`, alpha from the text's byte +0x86 |
| **ZFAIntroDisplay** `[osd+0x10ac]`, 0xbbdd98 | Render 0x768c40 (454 lines, not decoded) | 'Heist starts in {timer} sec' (`FA_GameStartCounter`, set by 0x6d7de0 / 0x70b9c0 with `GameStart/` texts), the intro cards | drawn in the countdown, state below 0x19; klhud.c's Draw=2 does not draw there at all |
| **ZFAHeadlineDisplay** `[osd+0x10bc]`, 0xbbdea8 | same Init as the points pop-up (0x5ab8b0); setter 0x401b70 | 'Round n' (`GameEnd/Round`) | a headline, not a message |
| **ZFAEscapeDisplay** `[osd+0x111c]`, 0xbbe9d0 | Render 0x5d7e00 | 'Hold Escape Vehicle' + health bar + mm:ss (`FA_HoldEscapeVehicle`); Heist slot 194 writes its byte `+0x28` = 0 | the escape dial's business (klhud.c Dials) |
| **ZFATimeDisplay** second line | `re/hud.md` 10 | Exit / `FA_Boarding`, `FA_LastBoarding`, `FA_LastExit`, `FA_Exit` (0x702990 = Heist slot 191) | under the clock, not in the middle |
| **ZMiniGameButtonMashingDisplay** `[osd+0x10fc]`, 0xbbe8f0 | Render 0x48f4b0: only with `+0x24` and `+0x50`; text `[+0x4c]` at the vec3 `+0x40`; picture 169 (`[tbl+0x7ec]`) at `(+0x28, +0x2c)` with desc `+0x60`, layer 9, white; picture 182 (`[tbl+0x888]`, UI_White) at `(+0x34, +0x38)` with desc `+0x94`, layer 0xb, the four corner colours `+0x104..+0x110` = `+0x114` - the bar. Tick 0x8ac680 builds the text from Interface / `TapQuickly` with `{TapCover}` / `{TapCycleWeapon}` / `{TapCloseCombat}` / `{TapUse}` | the break-free prompt kldown.c shows | pictures of the level data; its look is `tools/kl_hud.py`'s |
| **ZUseActionDisplay** `[osd+0x110c]`, 0xbbe844 | section 4 | the action prompt | section 4 |
| **ZOnscreenMessageDisplay** `[osd+0x10d8]`, 0xbbe0b0; **ZTextDisplay** `[osd+0x1104]` / `[+0x1108]`, 0xbbe800 | not decoded | campaign messages / text pages (callers 0x4a4269, 0x72d1a7 ..; 0x779c09 ..) | not FA's |

## 4. The use-action prompt and looting (READ)

**ZUseActionDisplay**: Tick 0x8b1030 copies the player's action from `[player+0xcfc]` (kind), `+0xd14`, `+0xd1c` (the
object), `+0xd24` into `elem+0x124 / +0x128 / +0x12c / +0x130` and, when they change, starts a fade (`+0x134`, `+0x138`
shown, `+0x139` alpha, `+0x14c` a fader); colour ffcccccc / shadow 80000000 every tick. Update 0x51f4a0: `x = 1280 * 0.5 +
0 = 640`, `y = 720 - 720 * inset - 75` (inset `[0xceeebc]` = 0.05 when byte `player+0x91e` is set, else `[0x154daac]` = 0):
**(640, 609) or (640, 645)**. Render 0x757100 (only with `+0x138`): the key icon = HUD picture `[0x154db68 + 4 * kind]`
(0x3d for kind 7, 0x3c with `+0x130`) through DrawChunk layer 0xb, the text `[+0x28]` + shadow `[+0x2c]` with the fader's
alpha, and with `+0x140` a frame `[+0x13c]`.
**It has no progress value and draws none.**

**A text object's measured size** (used by this part for the bar): that Render reads `[[text+4]+0x40]` and lays the icon
out with `2 * [+0x40]` (0x7571e6 .. 0x757204), and sizes its frame as `(int)(2 * [[text+4]+0x40] + 40 + 28)` by
`(int)(2 * [[text+4]+0x44] + 10 + 28)` (0x7573c9 .. 0x757430; 0xb62258 = 2.0, 0xb23668 = 40, 0xb5cde8 = 10, 0xbbe4e4 /
0xbbe4e8 = 14). So **`[[obj+4]+0x40]` / `+0x44` are the laid-out text's half width / half height**. Unit = the virtual
pixel: GUESS (it is added to virtual places). Whether it is current in the frame the string was set: not read.

**Looting a money OBJECT is not a hold action** (`re/bots_loot.md` 1, re-read here at 0x8e8750 and 0x727cb0): standing
in a money object's trigger starts it. The crew record (0x7c bytes at `[rules+0x348] + 0x7c * i`): `+0x15` loot state (0 none,
1 looting, 2 waiting for the trigger's next message, 3), `+0x18` float seconds left of the part being taken (= object
`+0x44` x the tuning factor 0x4f3e50), `+0x1c` the `ZOnlineMoneyCtrl` (vtable 0xbc874c; `+0x34` int amount left, `+0x40`
one part). The start also sets bit 0x2000 of `[score+0x1d4 + 4 * i]` with `i` = the CREW RECORD's index (0x8e8788 ..
0x8e87a1) - **that settles klhud.c's ASSUMPTION (d): the per-client flag dword is indexed like the money.**
**State 3 = the human takes money off a PERSON** (review S4; READ 0x727ce3 .. 0x727d9d and 0x727db8 .. 0x727e5f): for the
human's record only (`[[rec]] == 0`, the local player from 0x660b00), state 0 becomes 3 while bit 0x02 of
`[player+0xa54]` is set (`shr cl, 1 ; test cl, 1`) and `[player+0xa84]` holds an object whose money (`vt[+0xe0]` of the
rules with the index 0x78f470 gives, or 0x403a60 / 0x4536e0 for an object without a record) is above 0. While in 3:
`[rec+0x18]` counts down; at 0 it is set to `[0xba312c]` = 0.5 s and at most 20,000 (0x4e20) is taken; no object or no
money left -> state 0 (0x727f38). **That one is held**, and it has no stock progress drawing either.
=> **there is no stock loot progress drawing to hide or keep.** The ring is new and stands beside the prompt.

## 5. What klhud_popup.c does

**Pop-ups.** The announcement element gets a private copy of its vtable (12 dwords + the RTTI locator; slot 2 =
`klpu_render_ann`), installed by one heap dword write, as klhud.c does with the clock. In that call, while a message shows
(`[+0x30]` against the clock, the string not empty), klhud.c draws (`klu_draw_on`) and the level has a bar picture:

1. which message: `strcmp` with the level's own `FA_Become_Traitor` string, fetched once a level on the game thread by the
   game's lookup `[[[0xdd2640]+0xac]+0x94]->vt[0](section, key, 0)` (the call 0x67efb2 .. 0x67efdc makes; a game routine
   CALLED by the hook, vtable and target checked to lie in the image). The second sign is the human's traitor flag
   (record flag 2 or score flag 1): 'this message was first drawn between 0.3 s before and 0.7 s after the tick saw the
   flag rise' (mark and message are set in one call of slot 129; the tick samples every 50 ms). `PopupTraitor`:
   **1 (default)** the string decides, the flag only when the lookup gave no string - and a message that came with the
   flag's rise but is not the string is SAID in the log (`NOTE: that message came with the rise of your traitor flag
   ...`); **2** string or flag; **0** the flag alone, the lookup is never called. Why not 2 by default: section 2.1 - a
   later betrayal raises the flag with no traitor message, and whatever other message came in that second would get the
   box. The string cannot differ by language: it is fetched by the game's own lookup from the level's own file and 0x67ee80
   / SetText pass it on unchanged (READ, reviewer too).
2. size: `2 x` the text object's half extents when they are in range (2 .. 600, 2 .. 120), else longest line x 13 px and
   22 px + 30 a further line. Bar = text + `PopupPadX` (62) by text + `PopupPadY` (12): the draft's 'text + 62, 34 high'.
   Place: centred on the element's x, around the text block whose top is the element's y, + `PopupDY` (the bar alone).
   **`PopupY`** (review S3; default -1 = the game's 480; the draft's place is **520**): bar AND letters - the bar is
   drawn at that y and the element's `[+0x18]` is exchanged for it for the one stock Render call (read once there, so
   frame and both texts follow), put back by compare-and-swap. The game's place is kept by default ON PURPOSE until Q2
   has shown the first exchange (`[+0x30]`) to behave; the owner's tab should then carry `PopupY=520`.
   The stock frame follows the game's scale `[0xcee050]`, our bar does not (logged when the float is not 1).
3. look: plain = picture 111 (the painted stroke; 181 UI_White when the level has no extras) in chalk at layer 0x17,
   SetColour(text, ink 0c0c0d), the shadow's alpha 0. Traitor = 181 in e60c0c0d one layer below, picture 118 in orange
   5 px outside it (four 2 px bars of 181 when 118 is missing), SetColour(text, orange e8831f), shadow kept.
4. the stock frame: `[+0x30]` is exchanged for -1.0 for the one stock Render call and put back by compare-and-swap - the
   stock code then skips ONLY its frame (0x489632) and draws text and shadow. `PopupFrame=1`: no exchange, ours over it.

When no message shows or klhud.c does not draw, the same slot puts the text's colour (if it is one of ours) back to
ffcccccc and the shadow's alpha to what it was. **The put-back does not depend on this part's level state** (review M1):
the game sets the colour once (Init), so ink letters left behind would stay for the level. The render slot keeps, in
statics of its own that `klpu_forget` never clears, which element carries something of ours (`klpu_dirty`) and the
shadow's old alpha; when the element is no longer this part's (`klpu_r.ann` cleared: a klhud.c fault = for good,
'session state below 0x16' / 'rules object changed' = until taken up again) its next Render call puts both back and
then only passes on. The slot is reachable only through the private vtable, installed only on an object that showed
0xbbdd34. Nothing is written from the tick into the element except through the `PopupTest` call of 0x468430.
Guarded reads (review N2): none a frame while no message shows; about eight while one does.

**Loot ring.** The tick (50 ms) reads the human's crew record: state 1 / 2 with a money object -> the filled fraction
(`RingMode=1`: taken off this stack since he began / what lay there then - OUR meaning, the draft says 'fills while you
loot'; `RingMode=2`: the current part); **state 3 (money off a person): the 0.5 s step clock, a turn a step, whatever
RingMode says** (the person's whole money is behind a virtual call this part does not make); the place = the use-action element's `(+0x14, +0x18)` + (0, -64) (so (640, 545)
with the inset, (640, 581) without), or `RingX` / `RingY`. The render slot draws disc 114 (40 px, ff0f100f), thin ring
115 (40 px, ff8d8982), dollar 116 (34 px, green b063a65b) and `round(fraction x 20)` dabs 113 (6 x 8, chalk) on r = 26,
from the top clockwise, at least one. It stays 250 ms after the last looting sample. No ring without picture 113.
`RingMode=1` starts from nothing again when he was off the stack for more than those 250 ms (review N5): the fraction
is 'since he began THIS visit'.

Both use klhud.c's `klu_pic` with the record slot `KLU_NPIC` (DrawChunk memcpy's the record before it returns: READ,
klhud.c section 3), and its picture handles (`klu_pic_prep` is called from this part's tick when klhud.c has not).

## 6. WIRING (klhook.c only; klhud.c needs NO change) - exact old -> new, each old text occurs once

`python <work>\build\hud_P2\wire_P.py <copy of klhook.c>` applies exactly this; `wiring_P.diff` beside it is the result
against HEAD b216248.

1. old
   ```c
   #include "klhud.c"
   ```
   new
   ```c
   #include "klhud.c"
   #include "klhud_popup.c"
   ```
2. old
   ```c
       klu_tick(game_thread);                            /* klhud.c: the crew list / money box texts (game thread only) */
   ```
   new
   ```c
       klu_tick(game_thread);                            /* klhud.c: the crew list / money box texts (game thread only) */
       klpu_tick(game_thread);                           /* klhud_popup.c: centre pop-ups + loot ring (off unless [HUD] Popups / LootRing) */
   ```
3. old
   ```c
       klu_init();
   ```
   new
   ```c
       klu_init();
       klpu_init();                                      /* klhud_popup.c: after klu_init, it reads [HUD] with klhud.c's helpers */
   ```
4. klhook.c's header table and the KLHook.ini sample, `[HUD]`: `Popups=0 LootRing=0 PopupFrame=0 PopupMeasure=1
   PopupPadX=62 PopupPadY=12 PopupDY=0 PopupY=-1 PopupLayer=23 PopupTraitor=1 PopupTest=0 RingMode=1 RingX=-1 RingY=-1`.

Prefix `klpu_` / `KLPU_` (klfed.c owns `klp_`). With the sibling parts: `#include "klhud_values.c"` goes BEFORE klhud.c
(its wiring), klhud_weapon.c is included from inside klhud.c (its wiring), this file directly AFTER klhud.c; no name, key
or text-index clash (this part makes no text object and takes no `KLU_T_` index). Worth changing in klhud.c one day, not
needed: the comment of ASSUMPTION (d) (section 4 above).

**Build** (worktree `G:\kl_scratch\Pfix` at HEAD b216248, removed again; `build_auto.bat` / `build.bat`, /W3, **no
warning** in any of the four; klhud_popup.c sha1 4f88a7a9):

| folder under `<work>\build\hud_P2\` | what | sha1 |
|---|---|---|
| `test\dinput8.dll` | TEST, HEAD + this part alone | 2f9fe359 |
| `ship\dinput8.dll` | SHIP, the same | 0336fdab |
| `all3_test\dinput8.dll` | TEST, HEAD + **the three HUD parts together** (review S6): klhud_values.c 79f73a5a with `hud_D\wiring.patch`'s klhud.c part, klhud_weapon.c d14fa8c9 with `hud_W\wire.py`, this part; `all3_wiring.diff` = the whole difference to HEAD | dd884259 |
| `all3_ship\dinput8.dll` | SHIP, the same | 9ec76ecd |

The siblings were taken as they lay at 21:00 / 21:02 on 2026-10-11; if their own fix rounds change them, `all3_*` is
stale and the lead's own build of the three is the one to run. `<work>\build\hud_P\` is the FIRST form (STALE.txt
there); the compiler's by-products are removed from both folders.

## 7. GUESSES and risks, in the order they could bite

1. **Layers**: a higher layer byte is drawn in front (the stock frame 0x17 < shadow 0x18 < text 0x19 says so; klhud.c
   assumes the same). If not, the bar hides the letters: `PopupLayer`. 0x17 is past klhud.c's own range (3 .. 15) and
   past any layer a hook picture was drawn with live (13) (review N3): Q1 with `PopupFrame=1` is the first run for that.
2. **The bar's place**: style 0x14 = centred on x with y the text's top (section 1). Wrong by half a line -> `PopupDY`.
3. **The measured size**: the unit, and whether it is current when the message is new. The log prints measured and
   estimated size side by side for every message; `PopupMeasure=0` uses the estimate only.
4. **The exchange of `[+0x30]`** runs on the thread that renders. The Tick (main thread) reading -1.0 in that instant
   just skips one tick (0x4f1ed8 .. 0x4f1ee2); a message set in that instant is kept (compare-and-swap); a CLEAR in that
   instant is undone and the Tick clears again when the old end time passes (texts are already ""). Not a crash path.
5. **SetColour / SetAlpha from the render slot** - klhud.c's Dials do SetText / SetColour there (run H1l proved SetText).
   SetAlpha 0x639700 also toggles a flag through `vt[+0x200]` when alpha changes to / from 0xff: other elements call it
   every frame in their Render (0x75733f, 0x54954f), so it is a render-time call in stock too.
6. **Picture 118 / 111 stretched** to the bar's size: 256 x 64 and 256 x 32 textures scaled to e.g. 330 x 44 - the painted
   edge's look at that stretch is for the eye.
7. The lookup call for the traitor string when a level's .LOC lacks the key (review N7): the result is checked
   (readable, 2+ characters); what the routine itself does then was read by neither worker nor reviewer, and a retail
   assert is a bare int3. The stock slot's own .LOC is the base of every build of ours and the game makes the same call
   with the same key, so the risk is a build with a foreign text file. `PopupTraitor=0` never makes the call.
8. `PopupTest` calls 0x468430, which hides the follow-camera element for the message's time, as every stock message does.
9. The Arcade column of section 2 for the 'shared' rows.
10. **`PopupY`'s exchange of `[+0x18]`**: Update (slot 6) writes that float every frame; on which thread was not read.
    A write by it inside the one stock Render call is kept (compare-and-swap); the letters could then stand at the
    game's y for one frame under a bar at ours. Not a crash path.
11. The flag sign's window (0.3 s before .. 0.7 s after) is a GUESS at how far the tick's sample and the first drawn
    frame of the message can lie apart; it matters only without a string or under `PopupTraitor=0 / 2`.
12. State 3's ring: that bit 0x02 of `[player+0xa54]` is 'the use key is held' is a GUESS by its use; the state byte is
    what the ring reads.

## 8. Live checks (owner away; TEST build of HEAD + the wiring; the bank = slot F03 of page 2, a level with the extras:
`<work>\build\hud_x\DM03` or any `kl_hud.py --look deadmen` build since a1c61e7)

Every run: `[HUD] Enable=1 Log=2` + klhud.c's keys as its last passing run had them; pictures every 1 s from GO + 5 s.
A CRASH with the DLL, 0x4895b0, 0x639700, 0x8a0a30 or 0x842d00 in the callers = stop; the dump says which call.

- **Q0** `Popups=0 LootRing=0`: no `hud: popup:` line at all; the game as in klhud.c's last run.
- **Q1** `Popups=1 PopupTest=1 PopupFrame=1` (the first run keeps the stock frame: no float is exchanged). LOG, in order:
  `hud: popup: on; ...`, `... element ... (the announcements) now renders through the private vtable`, `... pictures of
  this level: bar 111 (the painted stroke), traitor box 118, ...`, `... the traitor message of this level is '...'`, then
  every 8 s `TEST message '...' shown through 0x468430` and `hud: popup: '...' (1 line(s)) -> chalk bar, ink letters; the
  text object says W x H (used), the string's length W2 x H2; text at (640, 480), bar ...`, alternating with `-> ORANGE BOX
  (the traitor message)`; every 5 s `... N bars, M traitor boxes ...` with N, M > 0.
  PICTURE: (a) a chalk stroke behind BLACK letters at screen centre, y about 474 .. 508 of 720; the stock dark frame
  around / behind it (expected in this run); (b) the letters IN FRONT of the bar (else `PopupLayer=22` .. 24);
  (c) the bar centred on the text, about 31 px wider each side and 6 px higher each side (else `PopupDY`, `PopupPadX`);
  (d) `W x H` of the log against the text on the picture: W about the text's width in 1280ths of the screen (1440p: half
  the pixels) = the unit GUESS holds; far off -> `PopupMeasure=0`; (e) the traitor message: orange letters, a dark fill,
  an orange painted outline; (f) after each message: the next stock message (or the countdown's texts) is light grey
  again, with its shadow.
  Read the log's `W x H` against the picture BEFORE trusting `PopupMeasure=1` in any later run.
- **Q2** the same with `PopupFrame=0`: the stock frame is GONE, text and bar stay; the message still ends after 5 s and
  the follow-camera hide comes back (no `hud:` fault line; `Log=2` counters go on). Three messages in a row from
  `PopupTest` must each end on time (the compare-and-swap).
- **Q2b** Q2 + `PopupY=520`: the log's `text at (640, 520) (PopupY)`; bar and letters TOGETHER 40 px lower than in Q2
  (720ths), never apart for more than a single frame; after the message the next stock text is at its own place.
- **Q3** `PopupTest=0`, a real round with bots, `[Bots] Backstab=0`, no fed. **The betrayal must be the FIRST crew kill by
  the human in that round** (section 2.1): do not kill a traitor bot or anybody of the crew before it. Shoot a crew
  member once or twice for the 3 s 'no friendly fire' line (bar), loot ('Looting has started ...' on the bar), then kill
  one crew member = the orange box and the log's `ORANGE BOX (the traitor message)` - NOT `(told by the traitor flag's
  rise)`, and no `NOTE:` line; the boarding and escape lines on the bar; a two-line message (if one comes): the bar
  covers both lines.
- **Q3b** the same round, but FIRST kill a crew member in a way that does not turn you (a bot that already is a traitor:
  `[Bots] Backstab=100`, wait for 'backstab: bot N may turn' / 'record N TRAITOR', kill him), THEN kill a loyal one:
  expected by the reading - your flag rises, NO centre message, nothing of ours drawn, no `ORANGE BOX` line. If another
  message stood at that moment the log has `NOTE: that message came with the rise of your traitor flag and is NOT ...`.
  (If the traitor message DOES come here, section 2.1's reading of `+0xe84` is wrong: note it.)
- **Q4** klhud.c standing down mid-message: (a) `PopupTest=1`, end the round (die, or board) while a test message
  shows: on the round-over page / at the next round's start the first message is LIGHT GREY WITH ITS SHADOW and the
  stock frame, no bar, until klhud.c draws again - then the bar again; (b) the same on a state drop of klhud.c
  ('session state below 0x16' / 'rules object changed' in its log) - there is NO key that forces a klhud.c fault, so the
  fault path itself can only be read (klhud_popup.c section 2), not run; (c) `Stock=0` on stock Subway: no `popup:` line
  after `on;`, the game's own look throughout.
- **R1** `LootRing=1 PopupTest=1`: LOG `ring dab 113, disc 114, thin ring 115, dollar 116`, counters `... K ring frames
  (ring on 1, n %)`. PICTURE: at (640, 545) (or 581) a dark disc, a thin grey ring, a faded green dollar sign, chalk dabs
  growing clockwise from the top over 4 s; does it sit clear of the prompt's key icon and of the pop-up bar (else
  `RingY`).
- **R2** `PopupTest=0`, stand on a money stack: `hud: ring: you loot money object ...: N left, T s a part`; the ring
  appears with the first part and fills as the stack empties, is gone 0.25 s after it is empty or you step off;
  `RingMode=2`: a turn a part - decide which the owner wants. Stepping off for more than 0.25 s and on again starts
  `RingMode=1` from nothing (the stack's rest is the new whole).
- **R3** (review S4) hold use on a dead crew member's / a civilian's money: `hud: ring: you take money off a person
  (loot state 3): the step clock 0.50 s`; the ring turns once every 0.5 s while the money comes, gone 0.25 s after.
  No such line while the money visibly comes = the state byte is not 3 there: note what `Log=2` of klbot.c says.
- ALL of it on a build of the three HUD parts together (`all3_test`, or the lead's own after wiring).
- For the owner's tab afterwards: `Popups=1` (+ `LootRing=1`) with what passed.

## 9. NOT DONE - the pop-ups are not complete (review S5)

**The two messages the owner sees most are still stock:** the kill / money lines of ZHeistPointsPopupDisplay ('You
killed a criminal. $0', the traitor fine, 'X killed Y' with its reward; section 3: needs a bar that follows the element's
own move and fade) and the countdown 'Heist starts in n sec' (ZFAIntroDisplay, drawn before state 0x19 where klhud.c
does not draw at all). The task named both. What IS restyled: every text of ZFAAnnouncementDisplay (section 2).
Also not done: the headline texts,
the prompt's own look (key block: level pictures), localised checks of any language but the one installed, FA online
(klhud.c's gate is Arcade), the English wordings of section 2.

## 10. Review round (2026-10-11 late; `re/hud_popup_review.md`: ACCEPT WITH FIXES) - finding -> what was done

Each finding was checked against the exe / the code first (`<scratchpad>\Pfix\d.py`).

| finding | holds? | done |
|---|---|---|
| **M1** a klhud.c fault / state drop mid-message leaves ink letters and a shadow of alpha 0 | yes (`klpu_forget` cleared `klpu_r.ann`, the slot's put-back hung on it) | the put-back no longer needs `klpu_r`: render-thread statics `klpu_dirty` (the element carrying something of ours) and the shadow's old alpha, never cleared by `klpu_forget`; `klpu_restore_el(e)` at that element's next Render call. Drawing still needs `e == klpu_r.ann`. Both wrong comments corrected; Q4 (a) / (b) |
| **S1** the traitor test never falls back once the string is known | yes | `PopupTraitor` 1 / 2 / 0. Default 1 = string, and a LOG NOTE when a message came with the flag's rise and is not the string. The reviewer's first form (string OR flag) is `PopupTraitor=2`, NOT the default: with S2 a later betrayal raises the flag without a traitor message and the OR would box whatever other message stood then. The flag sign is now bound to the message ('first drawn 0.3 s before .. 0.7 s after the rise'), no longer '5.5 s after the rise' |
| **S2** the traitor message is rarer than the note said | yes, READ 0x8fb13a .. 0x8fb153, 0x670a34, 0x6709fc, 0x670a11 | section 2.1; Q3 rewritten (first crew kill), Q3b added. The three writers of `+0xe84` are listed, their callers not followed |
| **S3** the draft's place (640, 520) not reachable | yes | key `PopupY` (exchange of `[+0x18]` for the one stock call; READ: read once at 0x48960d). Default -1 on purpose until Q2 has run; Q2b. The unscaled bar is said in code, note and log |
| **S4** loot state 3 gets no ring; 'not a hold action' too wide | yes, READ 0x727ce3 .. 0x727e5f | state 3 draws the ring from the 0.5 s step clock; the sentence corrected in code and note; R3 |
| **S5** the most seen messages are not restyled | yes | said at the top, in section 9 and in the report: NOT complete |
| **S6** stale builds | yes | `<work>\build\hud_P2\`: this part alone and the three HUD parts together, TEST + SHIP, no warning; by-products removed; `hud_P` marked stale |
| N1 slot 11 as a second way in | taken from the reviewer, not re-read | section 1 |
| N2 guarded reads a frame | yes | no guarded read while no message shows and nothing of ours is on the element; the string pointer read once |
| N3 layer 0x17 beyond anything seen live | yes | risk 1 |
| N4 `klpu_sh_obj` / `klpu_sh_alpha` outlive the level | holds, but clearing them in `klpu_forget` would BREAK M1's put-back (the alpha to restore is in them) | REJECTED as proposed; instead they are cleared the moment the alpha is put back, so nothing stale is kept past one put-back |
| N5 RingMode 1 restarts | yes | section 5, R2 |
| N7 the lookup for a missing key | not read | risk 7; `PopupTraitor=0` never calls it |
| N6, N8 | - | nothing to do |

Not changed: the look (colours, sizes, pictures), `PopupTest`, the wiring's three lines.
