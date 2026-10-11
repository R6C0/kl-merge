# Review of track W (the weapon dial) - `klhook/klhud_weapon.c`, `re/hud_weapon.md` - 2026-10-11

Adversarial review, offline (the owner is playing). Method: every routine the new code relies on disassembled again
from kl2.exe 0490 with capstone (scratch `<scratchpad>\Wrev\r.py`; nothing taken from the worker's dumps), the file
read line by line, the wiring applied to a plain copy of HEAD's `klhook/` (`git archive HEAD klhook`, no worktree)
and built. Words: **READ** = I read it in the code myself; **file** = in the exe's data; **GUESS** = not established.

## Verdict: ACCEPT WITH FIXES

The reverse engineering holds: every address, offset and calling convention the code depends on is confirmed below,
and the private-vtable deviation is justified. One MUST (an unchecked game call), then correctness points on what the
dial shows. Nothing of it has run; the first live run should be W0 / W1 only.

Build (mine): HEAD's klhook + `klhud_weapon.c` (sha1 d14fa8c9, as reported) + `wire.py` -> `build.bat` SHIP builds,
no error. At /W4 one warning, `klhud_weapon.c(457) C4701 'low' potentially uninitialized` - a false alarm (`low` is
read only under `klwd_r.ok`, which is set in the same branch that sets it). The worker's two DLLs exist with the
hashes reported (2d2ad0b6, 827777f7).

## What I re-derived (all READ unless marked)

| claim | where | result |
|---|---|---|
| ZWeaponDisplay vtable 0xbbe8c0: 11 slots, slot 2 = 0x5ec380, slot 5 = 0x5b1e00 | file | holds; the dword after slot 10 is the next RTTI locator |
| 0x5ec380 starts `83 ec 5c 56 8b f1 80 7e`, `ret 8` | 0x5ec380, 0x5ecbe7 | holds = the wrapper's `__fastcall (el, edx, ctx, cam)` is right |
| the caller ignores Render's result | 0x8bf5f0 .. 0x8bf5fd | holds: `call [vt+8]`, then the loop goes on. Returning 0 is harmless |
| the game's own +0x24 / +0x25 / 'HUD off' tests stand in front of slot 2 | 0x8bf583 .. 0x8bf5ee | holds, with one exception: bytes [0x154da65] and [0x154da67] both set render a hidden element anyway (then the tick has the dial off and the wrapper passes to the stock Render: correct) |
| Tick: slot 0 = `[player+0x924]`, bright / dim by `[player+0x920]`, slot 1 = 0x49b2f0(inv, sel, 4) | 0x88bacb .. 0x88bb5c | holds; the lead's reading was the other way round |
| 0x417bc0 -> 0x5aa000(inv+4, item): byte [inv+4] 0 = `[inv+8] + 16 item`, else a search of `[inv+0xc]` entries; object at entry+8 | 0x417bc0, 0x5aa000 .. 0x5aa047 | holds |
| 0x49b2f0: entries of `[inv+8]`, count `[inv+0xc]`; needs entry+8 != 0, info = entry+0xc, kind `[info+8]` 1 or 2, returns `[info+4]` when it is not the item given | 0x49b2f0 .. 0x49b353 | holds = `klwd_other_item` |
| rounds = `[weapon+0xdc] ^ 0xbeebbeeb` | 0x511f50 | holds. Two vtables carry 0x511f50 at +0x2fc (0xba3e6c, 0xbc042c); any other class reads as 'no counters' |
| reserve = `[weapon+0xe0] ^ key` - unless the gun is endless | 0x8b80e0 | holds, see S1 |
| `[elem+0x2e8+4i]` picture, `+0x2f0+4i` colour, `+0x2f8+i` / `+0x2fa+i` alphas, `+0x1228` | 0x88bb39 .. 0x88bd94 | holds |
| `[elem+0x150c+4i]` = the number shown | 0x4596d0 .. 0x4596f4 | holds |
| bar records: 0x6bc990(elem, rec, x0, x1) writes x1 x T[+0x14] to rec+0x44; +0x1134 gets min(179, rounds / size x 179), +0x10b4 gets 179 | 0x5c5747 .. 0x5c57b7, 0x6bc990 | holds. Referenced only by the Tick's 0x5c5670 and the Init (scan of .text for the displacements) |
| tick count `[elem+0x304]`: 0 under 1, 2 over 30.0 (double 0xb45350), else the size | 0x5c57dc .. 0x5c5a6d | holds |
| desc of gun i at `+0xd8 + 0x84 i` = {1, 0, -> +0xe4 + 0x84 i} | Init 0x832ee8 .. 0x832ef1 | holds |
| type-6 record: corners (-0.5 .. 0.5), width +0x5c, height +0x60, four ARGB +0x64 | 0x4bde70, 0x7c6bf0 (floats 0xb6e2ac = -0.5, 0xba312c = 0.5), 0x5ec62d, 0x5ec653, 0x5ec6f7 | holds |
| pictures 58 .. 106, 109, 110 are type 6; 111 .. 118 have no row = type 5 | 0x5e3810, table 0xcee058 (183 rows of 20 bytes) | holds |
| DrawChunk: 7 stack arguments, `ret 0x1c`; type from `[chunk+0xc]`; type 6 copies count x 0x74 bytes from desc[2] before it returns | 0x842d00 .. 0x842edf, jump table 0x842ee4 | holds = a record on the stack is safe |
| 0x5a3e90(T, out, in) is the same place arithmetic the weapon Render does inline (x T[+0x14], x T[+0x18], + T[0..8] by 0x42a4d0) | 0x5a3e90, 0x42a4d0, 0x5ec581 .. 0x5ec5b7 | holds |
| ZCHAROBJ vt+0x21c = 0x45d6e0, `(float *, x)`, `ret 8`; stores +0x1c / +0x20, sets bit 1 of +0x88, calls vt+0x1f0 | 0x45d6e0 | the call shape holds. That it is the SIZE stays ASSUMED, as the worker says |
| both stock hide groups write the weapon element's +0x25 | 0x75f780 (first write), 0x5e6091 | holds: the reason not to write the hide byte is sound |

## Findings

### MUST

**M1. `klwd_text_setup` calls a game method on a text object without checking it.**
`klhud_weapon.c` 397 - 403: `0x45d6e0` is called on `klu_r.t[KLWD_T_OTH].obj` and on its shadow with only `t->obj != 0`
tested. Every other call klhud.c makes on its texts comes after `klu_apply`'s per-tick `klh_rd` + vtable test; this one
runs inside `klu_compose`, BEFORE `klu_apply` of the same tick, and at the earliest one tick (100 ms) after the objects
were made. A freed or reused object there is a jump through a foreign vtable. The task's rule ('every read guarded,
vtable checks as klhud.c does') asks for it.
Fix: before each of the two calls `klh_rd(obj, &vt, 4) && vt == KLU_TEXT_VT`, else no call and `scaled` stays 0 for a
later tick.

### SHOULD

**S1. The label's reserve is the raw counter, not what the game counts - wrong for a gun with endless ammo.**
0x8b80e0 (READ): when the option byte `[[0xdd2640]+0xac]+0xb4` or the template's vt+0x2d8 says 'endless' and
`[0x15351e0] == 0` it returns `999 - rounds` and never looks at `[weapon+0xe0]`; with REF `[weapon+0x5c]` of a certain
class it returns 999; and 0x88bc2d makes the reserve equal to the rounds when the template flag is set. `klwd_compose`
459 - 463 takes `a->reserve` (the raw `+0xe0`) first and applies its 'endless' test (`n0 + rounds >= 999`) to that raw
value, so for such a gun the label shows a number that never moves. The test only works in the fall-back branch.
Fix: take the reserve as `a->total - a->rounds` whenever both are read (that IS the game's number, 999 included), the
raw `+0xe0` only for the log line. Consequence for live check W2: 'N != R + S = the object read is wrong, stop' is
too strict - N = 999 and N = 2 R are legal.

**S2. The ring empties the other way round than the owner's draft.**
The draft's weapon dial is `stroke-dasharray="80 100"` rotated to the top (`hud_mockup.html` line 418): the part LEFT
is drawn from the top clockwise and the gap is the LAST fifth. `klu_ring` draws dabs `first .. n-1`: the gap is the
FIRST fifth. (The draft's watch and escape dial, `0 65 35 100`, do run the way klu_ring does - only the weapon dial
differs.) W1's expected picture ('the first fifth clockwise from the top missing') describes the code, not the draft.
Fix inside this file: its own loop over `klu_addpic(113, ...)` for dabs `0 .. round(left x 32) - 1`. Also: with
`left` under 1 / 64 (one round of a 100-round belt) `klu_ring` draws no dab at all though a round is left - draw at
least one while rounds > 0.

**S3. With the dial up the player loses the pick-up arrow and the low-magazine warning.**
The skipped Render also draws picture 110 at `elem+0x12d4` (the pick-up arrow; READ 0x5ec95c .. 0x5eca31) and the
ticks in red when 0x54ee60 says the MAGAZINE is low (bar colour `elem+0x122c` = `[0xbbe4d0]`, 0x5c56dc). The dial's
coral comes only from the picture colour = 'rounds + reserve under one magazine' (0x77b790). So a nearly empty
magazine with reserve left gives no warning, and the hint that a gun can be picked up is gone. W2's line 'turns coral
when the stock panel would turn red' is therefore only half true.
Fix: ring coral when `(elem+0x122c & 0xffffff) == red` (one more checked read, the element is already read); for the
arrow either draw 110 through `klwd_pic6` when `elem+0x12d4 != 0` or put the loss before the owner as a decision.

**S4. A draw context of another class blanks the panel instead of falling back.**
`klwd_render_elem` 230: `if (!ctx || *(DWORD *)ctx != KLU_CTX_VT) return 0;` after the skip counter - neither the dial's
guns nor the stock panel. Every other failure in this file falls back to the stock Render; this one should too
(`return stock(el, 0, ctx, cam)`).

**S5. The one state in which the game draws no gun is not followed.**
0x5ec3a2 .. 0x5ec3d8 (READ): while `player->vt[+0x388]() == 0x21` and `[player->vt[+0x38c]() + 0xd4] == 3` the stock
Render draws neither picture nor number nor ticks. The dial stands on in it. The worker lists it under 'not done';
what state 0x21 / 3 is, is NOT established (GUESS: a mini game or the downed player - the owner has just asked for
'no shooting while down', so it matters which). Either make the two virtual calls (guarded: the player's vtable is
already tested as .rdata, the slots can be compared with fixed addresses once read) or leave the dial off there.

**S6. The global `[0xcee050]` is left out of the picture size.**
The Render multiplies width and height by `[0xcee050]` (0x5ec624, 0x5ec64a); the comment in `klwd_pic6` quotes it, the
code does not apply it. It is 1.0 in the file but it is a variable: two `fstp` writers exist in .text (354 readers).
One checked read in the tick, stored with the queue entry. (klhud.c's `klu_pic` has the same gap.)

**S7. A fall-back changes what the big number means, silently.**
When the gun object is not read (item not matched to the picture, another weapon class, a failed read) line 458 shows
`a->total` = rounds + reserve in the place of the magazine count: '24' becomes '207' with no line in the log besides
the raw dump. Log it once a level ('gun 0: no counters read, the panel's own number is shown'), or show no ring and
mark the number.

### NOTE

N1. **'READ' that is partly inference.** 'A type-6 picture's place is its middle' rests on the corner values
(-0.5 .. 0.5, READ) - what the renderer does with corners, width and height was not read; W1's picture decides. And
it says nothing about type 5 (klhud.c's `PicAnchor`), whose 40-byte record has no corners: 'both agree with run P1'
in section 0.5 mixes the two.

N2. **Names against baked gun looks.** The owner's maps carry `kl_map_guns.py` looks (Zastava = MP5, AK-47 = M4A1,
SCAR = SG 552, UMP = P90, MAC-10 = TMP, M9 = USP). The label will read 'AK-47' under an M4A1. The picture has the
same fault in the stock panel, but a NAME is new and the owner will see it. `KLGuns.ini` beside the archive has the
mapping.

N3. **The draft's thin grey outline of the disc** (`stroke="#55524d"`) is not drawn; picture 115 (ring) is among the
extras. And the label's separator is ' . ' for the draft's middle dot - whether the baked fonts have '.' or '-' is
unseen (worker's guess 8).

N4. **The dial's middle is 1145.5, the layout note says 1177.** It follows klhud.c's own inset rule (the money box is
at 1216 against the note's 1247), so it is consistent with the rest of the HUD; one of the two has to move for all
elements together. The label's lower edge (about y 692) lies under the inset line (684).

N5. **An unarmed player** gets an empty disc where the stock panel draws nothing (plate flag `+0x122b` 0).
`[elem+0x150c] == -1` (session mode 0xb with `[player+0xd50]`: the game hides the number) is not followed either:
the dial shows the rounds.

N6. **Log at Log=1:** 'the dial stands again' is written at Log=1 every time the game shows its panel again, while
the line before it ('the game does not show its ammo panel now') is Log=2 only - lone lines, possibly many.

N7. **Frames without the panel.** `TryEnterCriticalSection` failing = a frame with neither stock panel nor gun
pictures, where klhud.c so far only dropped its own additions. The dial's reads (up to 2 x `[inv+0xc]` + about 25
ReadProcessMemory calls) lengthen the time the tick holds `klu_cs`. Only matters if the render runs on another thread
than the tick; the Log=2 'lock busy' counter shows it. Likewise the wrapper tests `klu_draw_on` but not klhud's
canary: for up to one tick the guns can be drawn without disc and texts.

N8. **Stale state is contained.** `klwd_r.ok` survives a tick in which `klu_compose` did not run, but `klwd_show` ANDs
it with `show`, which is 0 then; `klwd_reset` runs under `klu_cs`; `klwd_r.elem` is set before the vtable dword goes
in; the element keeps the private vtable for its life and the wrapper passes through whenever `elem` or `draw_on` is
0. No hidden byte, nothing to restore: confirmed. No .text patch; one heap dword through `klh_data`. Nothing acts on
a stock level or outside Arcade beyond klhud.c's own gate (the wrap happens only inside `klu_compose`, and only when
113 / 114 and the three texts exist).

N9. **Wiring.** Applies cleanly to HEAD and builds. `klhud_popup.c` and `klhud_values.c` (untracked siblings) will
want the same `KLU_NTEXT` line, the same spot behind `klu_dials` and a call in `klu_compose`: the lead has to chain
them by hand, `wire.py`'s exact-match replaces will refuse a klhud.c another track has already wired. The working
tree's klhud.c differs from HEAD by one line (another session's).

N10. **Per frame:** two more DrawChunk calls (0x74-byte records) and one counter; per tick about 30 checked reads
plus the inventory walk. No concern.

## Live checks - changes to the worker's list

- W1 first, on its own, and read the 'render:' line before anything else: `skipped N, passed 0, 2N pictures, 0 busy`.
- W2: accept N = R + S, N = 999 (endless) and N = 2 R; note for each gun whether `bar a of b` x size = R.
- Add **W2b**: empty a magazine below a third with reserve left - the stock ticks go red (Weapon=0 control), the dial
  must warn too once S3 is in.
- Add **W6**: stand on a dropped gun with `Weapon=0` and `Weapon=1`: what the arrow showed and what is lost.
- W3: also the state of S5 (whichever it is: human shield, the knock-down) - stock shows an empty plate, the dial?
