# Review of track P - centre pop-ups and the loot ring (`klhook/klhud_popup.c`, `re/hud_popup.md`)

Reviewer, 2026-10-11 night. OFFLINE: nothing was run in the game, nothing was built again. Every address below was
disassembled again from the installed kl2.exe (capstone, `tools/kl_exe.py`); scratch: `<scratchpad>\Prev\d.py`.
**READ** = I read it in the code myself; **not re-read** = taken from the worker's note.

## Verdict: ACCEPT WITH FIXES

The reading is sound: every address, offset and calling convention the code relies on is confirmed. The method is the
proven one (private vtable copy, work done inside the element's own Render), no code byte changes, and the part acts only
where klhud.c acts. One MUST (a stand-down path that leaves black letters on the stock text for the rest of a level),
then SHOULDs about the traitor test, the draft's place, a loot state that gets no ring, and a stale build.
It may go into a TEST build for Q0 / Q1 once M1 is in; not onto the owner's game before Q1 - Q3 have run.

## What I confirmed (all READ)

| claim | evidence |
|---|---|
| ZFAAnnouncementDisplay vtable 0xbbdd34, 12 slots, slot 2 = 0x4895b0 | RTTI name; slots 0..11 are code, dword 12 is 0. ZUseActionDisplay (0xbbe844) has 11, so `KLPU_NSLOT 12` is right and one more than klhud.c's 11 |
| Render 0x4895b0 is thiscall (ctx, cam), `ret 8` | 0x4897ef |
| the frame is skipped when `[+0x30]` = -1.0, text and shadow are still drawn | 0x48961b: `fld [esi+0x30]; fmul 1024.0; ftol; cmp [sys+0x48], eax; jge 0x48978a`; 0x48978a draws `[+0x28]` then `[+0x2c]` at +2 / +2 |
| the frame's size comes from the string `[[text+0xa4]+0xc]`; 15 / 20 px a character, + 15, at least 300; lines x 30 + 40; drawn at y - 25 | 0x489649 .. 0x489731; bytes 0xcedc7c = 14 0f 1e, floats 15.0 / 40.0, doubles 300.0 / 25.0 |
| setter 0x468430 thiscall (text, float), `ret 8`; "" writes -1.0; else end = (clock + s x 1024) / 1024 | 0x468430 .. 0x4684b8; 27 `call` sites, the same 27 the note lists |
| Init: text colour ffcccccc, layer 0x19; shadow 80000000, layer 0x18; frame layer 0x17; style 0x14 on all three | 0x7cbd87 .. 0x7cbe72 (`vt+0x220` 0x14, `vt+0x234` 0x17 / 0x19 / 0x18, `vt+0x20c` with [0xbbe494] / [0xbbe4a4]) |
| Tick 0x4f1ea0 skips when `[+0x30]` <= 0, clears when the clock has passed it | 0x4f1ed8 .. 0x4f1f1d |
| ZCHAROBJ `vt+0x20c` = 0x8a0a30 (thiscall, 1 arg, `ret 4`; keeps the alpha byte +0x86, returns at once on the same rgb), `vt+0x218` = 0x639700 (thiscall, byte, `ret 4`), `vt+0x244` = 0x896e50 | vtable 0xbab45c dwords; the three bodies. The four code-byte arrays in `klpu_wrap` match the file |
| SetText stores the string unchanged at +0xa4 and rebuilds at once (`vt+0x238`) | 0x896e64 .. 0x896e97 - so a `strcmp` with the raw .LOC string is a fair test, and the extents are current in the frame a message is new (the note's open point 3, second half: settled as far as the rebuild is the layout) |
| the .LOC lookup is `[[[0xdd2640]+0xac]+0x94]->vt[0](section, key, 0)`, callee cleans 12 bytes, returns a `char *` | 0x67efb2 .. 0x67efe3: three pushes, the locals after the call are addressed as if 12 bytes were gone; the result goes straight into 0x83e2e0 -> 0x770520 (a string made from a pointer). 0xb38bc0 = 'AllLevels/Interface/Online/Announcements', 0xb4a6a8 = 'FA_Become_Traitor': section first, key second, as the hook passes them |
| the traitor string goes to the setter unchanged, 5.0 s, only on the turning player's machine | 0x67ef61, 0x67efe8 .. 0x67f03e |
| `[[text+4]+0x40]` / `+0x44` used as half width / half height | 0x7571e6 .. 0x757204; 0x7573c9 .. 0x757430 = `(int)(2 x + 40 + 2 * 14)`, `(int)(2 y + 10 + 2 * 14)` |
| use-action place: x = 640, y = 720 - inset x .. - 75 | 0x51f4a0 .. 0x51f4fd (0.5, -75.0, inset 0.05) |
| crew record +0x15 / +0x18 / +0x1c; ZOnlineMoneyCtrl 0xbc874c, +0x34 the amount left (0x74da10 returns it, 0x4e3f40 subtracts) ; the 0x2000 flag indexed by the record's index | 0x8e8750 .. 0x8e87de, 0x727f82 .. 0x7280a2 |
| DrawChunk copies the record before it returns, 7 arguments | 0x842dfd .. 0x842e03, `ret 0x1c` - so one record slot (`KLU_NPIC`) for all of this part's pictures is safe |

SHIP rule: kept. One heap dword (the element's vtable pointer, through `klh_data`), one float of the element exchanged
and put back inside its own Render call, calls of the text objects' own routines. No `.text` write.
Arcade / not stock: kept. The element is wrapped only after `klu_r.made`, which klhud.c sets only on an allowed level in
an Arcade session's states 0x17 .. 0x19; all drawing and the `PopupTest` call hang on `klu_draw_on`.
Shared objects: the two texts are made per element in Init (`vt+0x19c`), no other element draws them: a colour set here
cannot show on another screen.

## Findings

### MUST

**M1. When klhud.c latches a fault (or drops its level state) while a message shows, the ink colour and the shadow's
alpha 0 stay on the stock text for the rest of the level.**
`klpu_forget` does `memset(&klpu_r, 0, ...)`, which sets `klpu_r.ann = 0`. `klpu_render_ann` does everything, the restore
too, only under `e == klpu_r.ann`. So after a forget the wrapped slot is a bare pass-through and `klpu_restore` never
runs. `klpu_tick` is called directly after `klu_tick` in the same game tick, so there is no frame between
"klhud.c sets `klu_r.fault` / calls `klu_reset`" and the forget in which the render slot could still put things back.
The colour is set by the game ONCE, in Init (0x7cbdd2): nothing stock ever writes ffcccccc again. Result: every later
message of that level is near-black letters without shadow on the stock dark frame.
- for good: `klu_r.fault` (klhud.c latches it in `klu_apply`, `klu_vtable_tick`, `klu_make_all`) - `klpu_tick` then
  returns at `!klu_r.made || klu_r.fault` in every later tick;
- until the element is taken up again: `klu_reset` with the OSD still standing ('the session state is below 0x16',
  'the Arcade rules object changed').
The comment in `klpu_forget` ('the render slot puts the stock colours back by itself while it still runs') and section 2
of the header ('nothing is left behind when the HUD stands down') are wrong for these paths.
FIX (small): the render slot must not depend on `klpu_r.ann` for the restore. It is reachable only through the private
vtable, which only `klpu_wrap` puts on an object that showed 0xbbdd34 - so `e` IS an announcement element. Take the
`e == klpu_r.ann` test out of the restore path (keep it, or `klu_draw_on`, for drawing), e.g.

```c
if (ctx && *(const DWORD *)ctx == KLU_CTX_VT) {
    if (klpu.popups && e == klpu_r.ann && klpu_popup(e, ctx) && !klpu.frame) { ...exchange... }
    else if (e != klpu_r.ann) klpu_restore_el(e);     /* text / shadow of e, vtable-checked as klpu_popup does */
}
```

and correct the two comments. Add the case to live check Q4 (force a fault, or end a round, mid-message).

### SHOULD

**S1. The traitor test never falls back once the level's string was fetched.** `klpu_popup`: `if (klpu_traitor_ok)
traitor = !strcmp(...); else { flag rise }`. If the compare fails for any reason (another language's string with a
trailing blank, a build whose text file differs from what the lookup returns), the traitor message silently gets the
plain chalk bar and the flag path is dead. The compare is fair as read (SetText keeps the string unchanged), so this is
a safety net, not a known fault: make it `strcmp == 0 || (flag rose < 5.5 s ago && the message is new since the rise)`,
or at least log once when the flag rose and a message with another text was shown. Q1 cannot catch it: `PopupTest`
feeds the fetched string itself.

**S2. When the game shows the traitor message is narrower than the note says.** Heist slot 129 passes 'announce' = 1 only
while `[rules+0xe84] == 0` (READ 0x8fb13a .. 0x8fb153), and 0x6706b0 counts that dword up at 0x670a34 for every crew kill
by a human it handles - also on the branches that do NOT turn him (`jne 0x670a34` at 0x6709fc when the flag bit is
already set, at 0x670a11 when `vt+0x1e8` says yes). So a first kill that is 'allowed' uses the counter up and a later
real betrayal sets the flag WITHOUT any centre message. Not a fault of this part, but (a) the note's section 2 row
should say it, (b) live check Q3 must make the betrayal the FIRST crew kill of the round or it will look like a failure,
(c) a traitor made by another path (klbot.c's Backstab, klfedkit.c) never passes 0x67ee80 with the human as the turner:
no box there. I read only the two sites named; who resets +0xe84 (writes at 0x74bd24, 0x83577d) was not followed.

**S3. The draft's place is not reachable.** `re/hud_layout.md`: 'pop-up: centre (640, 520)'. The code leaves the text at
the game's (640, 480 = top) and `PopupDY` moves ONLY the bar - any value but 0 pulls bar and letters apart. Either say
in the note that the stock place is kept on purpose, or add a key that moves both: the same exchange-and-put-back the
part already does with `[+0x30]`, done on `[e+0x18]` around the stock Render call (Update 0x71d9c0 rewrites it every
frame, so nothing sticks). Also unsaid: the stock frame scales with the HUD scale `[0xcee050]` (0x4896c7), our bar does
not.

**S4. Loot state 3 gets no ring, and 'looting is not a hold action' is too wide.** READ 0x727ce3 .. 0x727d9d and
0x727db8 .. 0x727e5f: for the HUMAN's record only (`[[rec]] == 0`), state 0 goes to state 3 while bit 2 of
`[player+0xa54]` is set and `[player+0xa84]` holds an object: he is taking money off a PERSON (another crew record's
money through `vt+0xe0`, at most 20,000 a step, the step's clock `[rec+0x18]` = `[0xba312c]` = 0.5 s). That is the
player's own use action on a body - a hold. `klpu_ring_tick` accepts only state 1 / 2 with a ZOnlineMoneyCtrl, so no
ring there, and section 4 of the note does not mention the case ('3' has no meaning in its table). Add state 3 with the
part clock (RingMode 2's maths; there is no stack total) or state in the note that body looting has no ring.

**S5. Scope: the messages the owner sees most are not restyled.** The task named 'X killed Y' and 'Heist starts in n
sec'. Kill / money lines ('You killed a criminal. $0', the -25,000 fine: READ 0x8fb200 .. 0x8fb21a calls
ZHeistPointsPopupDisplay `vt+0x2c`) and the countdown stay stock light grey beside the new look. The note says so under
'NOT DONE' with a workable next step; the lead should not report the pop-ups as complete to the owner.

**S6. The builds are stale.** `<work>\build\hud_P\test|ship` were made at c9d654d from klhud_popup.c 6dee7559; HEAD is
now bac2f86, klhud.c has an uncommitted line (the picture-slot log), the file is 88a8ba08 and M1 changes code. Two more
untracked parts (`klhud_values.c`, `klhud_weapon.c`) will be wired next to it. No name or key clash found (`klpu_`
is free; neither file uses `KLU_NPIC` or the Popup / Ring keys), but all three must be compiled TOGETHER before any run.
The `.exp / .lib / .obj` beside both DLLs are still there.

### NOTE

**N1. A second way into the wrapped slot.** Slot 11 (0x63d590, the announcement's one extra virtual) calls Update, moves
the place by (0.1, 0.1), calls slot 2 THROUGH THE VTABLE and puts the place back; the OSD calls it from 0x64f99c in
session states 0x29 .. 0x2b. Our wrapper runs there too. `klu_draw_on` is 0 in those states (klhud.c draws in 0x17 ..
0x19 only), so it is the stock look - but it is one more reason for M1's fix (that is where a message still showing at
the round's end would be put back), and the note does not list it.

**N2. Guarded reads a frame.** klhud.c keeps its render slot to two `ReadProcessMemory` calls a frame on purpose
(its section 5b). This slot makes 2 - 3 when idle and about 10 while a message shows (text / shadow vtable, sysif,
clock, string pointer twice, the string, the extents, the clock element twice). Each is a system call; at 240 frames a
second that is ~2,400 a second for 5 s a message. Harmless in cost, but it departs from the house rule without saying
so. Cheap to halve: read `[text+0xa4]` once, call `klpu_clock` once a call.

**N3. Layer.** `PopupLayer` 0x17 is past the range klhud.c allows its own key (3 .. 15) and past every layer a hook
picture has been drawn with live (13). The bar is submitted BEFORE the stock text, so it is behind the letters whether
order or layer decides - unless a higher layer is drawn first. Q1 with `PopupFrame=1` is the right first run.

**N4. `klpu_sh_obj` / `klpu_sh_alpha` are statics that outlive the level.** A later level's shadow at the same address
with alpha 0 of its own would get the old alpha. Not reachable as read (the stock shadow is never 0); clear them in
`klpu_forget` anyway.

**N5. RingMode 1 starts again from nothing** when he steps off a stack for more than 250 ms and back (the start value is
dropped with the linger). A half-empty stack then shows an empty ring. The owner's call, as the note says; say this
case in R2.

**N6. Reads without a check that are fine:** `e + 0x14 / 0x18 / 0x28 / 0x2c / 0x30` (`e` is `this` of the running
call), `text + 0x14 / +4`, `shadow + 0x86` (after the vtable test), `*ctx` (the game's argument, as klhud.c).
`geom + 0x40`, the string, sysif are guarded. The exchange on `[e+0x30]` is aligned and put back by compare-and-swap;
the worst cases the note gives (one skipped Tick, a clear done twice) are what the code at 0x4f1ed8 and 0x46846f does.

**N7. The lookup is a game routine called by the hook** (once a level, game thread, same arguments as 0x67efc8). What
it does for a missing key was not read by either of us; a retail assert is a bare int3. The key is in every FA slot's
own .LOC, which our builds use as base, so the risk is a build with a foreign .LOC. Worth a line in the note's risks
with that reason.

**N8. Marked READ, really inference:** 'the element holds no message id' is READ for the setter and Render; 'style 0x14
= centred, y = top' and 'the extents are virtual pixels' are correctly marked GUESS. The Arcade column of section 2 is
marked as partly guessed. I found no claim marked READ that the code contradicts.

## The owner's look

Plain message: chalk stroke 111, black letters, no shadow - as agreed. Traitor: orange letters, dark fill, orange
painted box 118 - as agreed, and orange (never gold) is the hook's own `KLU_C_ORANGE`. Bar = text + 62 by 34 for one
line - the draft's numbers. Ring: 20 dabs on r = 26, disc and thin ring 40, dollar 34 in the dark green with alpha b0 -
the draft's numbers; the dab's 6 x 8 is the worker's choice (the layout gives none). Open against the draft: the place
(S3) and the stretch of 111 / 118 (the note's risk 6; nobody has seen pictures 111 .. 118 drawn yet at all).

## Live checks - changes to the worker's list

- Q1 as written (keep `PopupFrame=1` first). Add: read the log's `text object says W x H` against the picture before
  trusting `PopupMeasure=1`.
- Q3: the betrayal must be the first crew kill by the human in that round (S2); a second run where it is not, to see
  that no message comes and nothing of ours is drawn.
- Q4 after M1: (a) a round that ends while a message shows, then the next round's first message must be light grey with
  shadow until klhud.c draws again; (b) the same with a forced klhud.c fault if a key for one exists.
- R3 (new, S4): hold use on a dead crew member's money: state 3 - with the fix a ring, without it none; log the state.
- All of it on a build made from the three HUD parts together (S6).
