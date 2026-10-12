# Splitting klhud.c - PROPOSAL ONLY (cloud session, 2026-10-12; nothing moved, nothing built)

klhud.c was 1,331 lines with 49 functions at ebe4d72 (the line numbers below are that commit's; 54ceb35 added the watch look, about +110 lines, `klu_watch_look` / `klu_escape_look` / `klu_dial_base` / `klu_hand` / `klu_track_f`, which belong in `klhud_watch.c` with `klu_dials`); with its parts the HUD is 4,775 lines in nine files, all compiled as ONE translation unit
(klhook.c `#include`s them, lines 584-591, and klhud.c itself includes klhud_weapon.c at its line 806). The split below keeps that unity
build (no new linkage, no header-guard games beyond what the parts already use) and changes NO behaviour. Do it only in a local session
that can build and run the harnesses, one step a commit.

## 1. What is in klhud.c today (HEAD line numbers)

| lines | what | thread |
|---|---|---|
| 1-300 | header comment (keys, the draw path, history), constants, `klu` (keys) and `klu_r` (level state) | - |
| 315-475 | render-slot code: `klu_same_code`, `klu_draw_one`, `klu_draw_stock`, `klu_pic`, `klu_inst`, `klu_draw_ours`, `klu_clock_face`, `klu_render_elem`; the tags' prototypes (432-435) | render |
| 476-500 | `klu_vtable_tick` (the clock element's private vtable) | main |
| 503-657 | making texts: `klu_rdata_ptr`, `klu_set`, font helpers (`klu_cap_of` twice: a prototype at 273), `klu_cen`, `klu_make_obj`, `klu_layout`, `klu_make_all` | main |
| 659-806 | money formatting, the picture queue and the ring painter (`klu_addpic` + the board2 redirect, `klu_outline`, `klu_sink`, `klu_arc_ok`, `klu_dabs`, `klu_arc`, `klu_track`), `klu_dials` (watch + escape dial), `#include "klhud_weapon.c"` | main (`klu_sink` also render, through `klu_pic`) |
| 809-991 | crew list / money box: `klu_row`, `klu_lives_row`, `klu_grid`, `klu_compose`, `klu_apply` | main |
| 992-1108 | lifecycle: `klu_hide_tick`, `klu_stand_down`, inset, `klu_extra_slot`, `klu_pic_prep`, `klu_fa_shown`, `klu_reset` | main |
| 1109-1274 | finding the OSD and the tick: `klu_osd_ok`, `klu_osd_direct`, `klu_find_osd`, `klu_current_osd`, `klu_tick` | main |
| 1275-1331 | ini helpers and `klu_init` | main |

## 2. Proposed files (included by klhook.c in this order, where klhud.c stands now)

| file | takes | why |
|---|---|---|
| `klhud_core.c` | the header comment's key list, constants, `klu` / `klu_r`, `klu_inif` / `klu_inii`, `klu_same_code`, `klu_rdata_ptr`, `klu_set`, the font helpers, `klu_make_obj`, money formatting | everything the parts call; nothing that draws |
| `klhud_render.c` | `klu_draw_one`, `klu_draw_stock`, `klu_pic`, `klu_inst`, `klu_draw_ours`, `klu_clock_face`, `klu_render_elem`, `klu_vtable_tick` | ALL render-thread code of the base in one place: the rule 'no system call, only TRY the lock, reads of prepared data' can be audited in one file |
| `klhud_paint.c` | the picture queue and the ring painter (`klu_addpic`, redirect, `klu_outline`, `klu_sink`, `klu_arc*`, `klu_dabs`, `klu_track`), `klu_pic_prep`, `klu_extra_slot` | used by the list, the dials, the weapon dial, the scoreboard, the pop-ups |
| `klhud_watch.c` | `klu_dials` (watch + escape dial) | where the watch rework (re/hud_watch_design.md) goes, apart from the list |
| `klhud_list.c` | `klu_layout`, `klu_make_all`, `klu_row`, `klu_lives_row`, `klu_grid`, `klu_compose`, `klu_apply` | the crew list and money box |
| `klhud.c` (kept name) | lifecycle + OSD finding + `klu_tick` + `klu_init` | the name every note and log refers to stays the entry point |
| `klhud_weapon.c` | unchanged, but included by klhook.c after `klhud_paint.c` instead of from inside klhud.c (line 806) | one include list, in klhook.c |

Size after the move: none above ~350 lines. A prototype block (`klhud_api.h`, or a block at the top of `klhud_core.c` like the tags'
prototypes at klhud.c 432-435) lists the functions one file calls in a file included later (`klu_compose` -> `klwd_compose`, the render
slot -> `klht_render`, `klu_reset` -> `klwd_reset` / `klht_reset`), so include order stops being load-bearing.

## 3. Duplication worth folding (after the move, each its own commit)

1. **The private-vtable wrap** is written five times: `klu_vtable_tick` (klhud.c), `klpu_wrap` (popup), the escape wrap
   (klhud_escape.c ~350), `klbrd` wrap (klhud_board.c ~86), `klsb_wrap` (klhud_board2.c 258). Each: read N slots + RTTI from `VT - 4`,
   check slot 2 (and sometimes 5) and the first code bytes, write the element's vtable pointer with `klh_data`, retry policy. One helper
   `klu_wrap(struct klu_wrap *w, DWORD el)` with {vt, nslot, render, tick, code, ncode, evt[], refused, wrapfail} would make the rule
   (no .text patch, one heap dword) one function to review. The retry policies DIFFER today (board2: 30 ticks then refuse; escape /
   board: 3 s; klhud: fault): keep them as a field, do not unify behaviour in the same commit.
2. **'The clock element to borrow picture desc and transform from'**: `klpu_clock` (klhud_popup.c 274), `klesc_clock` (klhud_escape.c 123)
   and board2's cached copy (`klsb_cache_pics`). One `klu_clock_for_pics()` in klhud_render.c; board2 keeps its cache (it draws when the
   clock does not).
3. **Text pools**: board2 (40), tags (up to 7 x 7), the list (24 + shadows) each call `klu_make_obj` in a loop with their own error text.
   A `klu_make_pool(DWORD *out, int n, roles[], styles[], colours[], layer, why)` is optional - small gain.

## 4. Warnings to clear while moving

- klhud_weapon.c `klwd_compose` (line 481 at ebe4d72, 533 after 54ceb35): locals `k` and `m` are declared and never used (`m` appears only in a comment) - the C4101
  warnings the local builds report (re/hud_board.md 5). Remove both. (Found here by a text scan, not by a compiler; the local /W4 build
  is the judge.)
- klhud_board2.c `klsb_compose`: `rm` and `lost` are silenced with `(void)`; `lost` is an out-parameter of `kluv_result` and is needed,
  `rm` is the 'OF m' that is deliberately not shown - leave both.
- klhud_board2.c `klsb_testdraw`: `(void)e` is no longer needed after this session's B2 fix (e is used now) - drop it.

## 5. How to prove 'no behaviour change' (local)

1. Move only (copy-paste of whole functions, no edits): TEST and SHIP build at /W4 with no new warning; `klsb_test.c` (91 + 2 checks)
   and the values harness (`build/hud_D/kluv_test.c`) pass unchanged.
2. Compare the log of one scripted bank run (hud test hook, `[HUD] Enable=1 Draft=1 Log=2`) before and after: the same `hud:` lines in the
   same order (addresses differ).
3. Then each fold of section 3 separately, with the same two checks.
Risk: the unity build means a `static` name in two files collides only if two files define it - the move does not create new names.
