# Initials through walls: a line-of-sight test per crew record - DESIGN ONLY (cloud session, 2026-10-12)

Problem (re/hud_audit.md, G2 94 / 102 / 106): the initials of AI heisters behind walls hang in bare rooms. The stock tag drawer 0x7b8150
has no occlusion test (re/hud_tags.md 1: projection only, no alpha, no distance); the stock list drew its tags the same way.
No code is written here: the task allows code only if the needed game routine and its calling convention are already in re/, and
NONE of the candidates below has its calling convention documented. Nothing built or run.

## 1. What re/ establishes that can help

| fact | where | use |
|---|---|---|
| The hook already has, per tag and frame, the bot's node (`[rec+4]`) and the render `cam` the stock Render got | klhud_tags.c `klht_render` | the two ends of a sight line, if the camera's world place can be read |
| The tag drawer finds the head: `pos = 0x8d3150(node)` (world place), `box = node->vt[0x340](node, 0x8cb2e0(node))`, `pos.y += box.top + [0xb23668]` | re/hud_tags.md 1 | the far end of the ray, the same point the tag is drawn at |
| The third-person camera object: final position `this+0x508` (0x7c9030), the room of the camera into `node+0x1b8` (0x6f8710); its own collision walk slot 55 = 0x897d60 ends in **0x6e0b20 = a raycast toward -750 along +0x468, `this+0x394` = blocked**; a "clear line" test is slot +0x5c4 | re/firstperson_camera.md 2-3 | a raycast routine the game uses every frame on the main thread - its arguments are NOT documented, and the camera object was not found in any dump (same note) |
| ZCheckVisible (singleton at [0x1535c70], vtable 0xba7ae4, 0x14120 bytes): a 16 x 1 x 16 cell grid, 200 records {cell, x, y, z} of registered objects at +0x12ae0, 200 blocks of 0x12c at +0x4080; 'the police find a target through ZCheckVisible's records' | re/crash_686a66.md 2 | the game's own visibility service for AI. What the 0x12c blocks hold (a per-cell or per-record visibility set?) is NOT established |
| Rooms and gates (portals): every level has room trees, gate records in the .buf; the renderer walks rooms through gates per camera per frame (0x522cc0, 1,024 frustum records) | re/campaign_fa.md (gates row), CLAUDE.md (rooms) | a coarse "is the bot's room drawn this frame" test |
| The collision rays offline: third_party/anp/scripts/hvk_ray.py casts on the level's collision (flags & 0x20 = sight blockers, eye 160 over the post) | re/club_campaign.md | proves the level's collision has a 'blocks sight' flag; offline only |

## 2. Options, ranked

**A. The game's own raycast (recommended, needs one reading).** Read 0x6e0b20 and 0x897d60's call of it in kl2.exe: the arguments
(start, end or direction + length, a filter / flags word, an out-record), the convention (thiscall on what object? the Havok world?),
the thread it runs on (the camera tick = main thread, re/firstperson_camera.md 3), and whether it can be called with any two points.
Then:
- Tick (main thread, klht_tick, 100 ms): for each bot with a tag (at most 7), cast from the CAMERA's eye to the bot's head point
  (the drawer's own formula: `0x8d3150(node)` + box top) and to the chest (head - 60), with the sight-blocking filter the camera uses.
  Visible = either ray clear. 14 rays per 100 ms.
- Camera eye: the render `cam` handed to the clock's Render is a ZCAMERA geometry node (re/firstperson_camera.md: node setters
  SetPosition 0x7ca930 -> geom 0x66d0f0) - its world translation is the eye. Reading it needs the geom node's matrix offset: NOT in re/.
  Fall-back eye: the human's head (player node place + 160) - wrong by the shoulder offset (180 back, 30 right in FA), good enough for
  walls (a tag hidden from the player's head but seen by the camera over his shoulder is rare and harmless).
- Hysteresis: hide after 2 blocked ticks in a row, show after 1 clear tick (fast in, slow out reads natural), and fade over 150 ms
  through the text objects' alpha (`klu_set ... KLU_VT_COLOUR` with alpha; the outline copies' alpha with them).
- Render: `klht_render` skips entries whose `q->seen` is 0 - one byte read, no call, no new render-thread code.
- Risk: calling a Havok query from the hook's tick between the game's frames. The camera calls it in its own tick on the same thread,
  so a call from klu_tick (also between frames, re/hud_hook.md) is the same situation - ASSUMPTION until read.

**B. ZCheckVisible's records (free if the data is there).** Read 0x59c790 (registration) and the update that fills the 0x12c blocks.
If a block is a per-record set of "visible from cell" or "visible to record r" bits that the AI keeps current, the tag test is a read:
the player's record vs the bot's. Only bots / police that register get a record (FakeTargets, cars register; whether a ZFFActor does is
NOT established). Cheapest at run time, zero calls; but the grid is 16 x 16 cells over the whole level (coarse: a cell can span a wall),
so it may say 'visible' through thin walls. Read first; use as a pre-filter for A if it is coarse.

**C. Rooms drawn this frame.** If the bot's geometry node carries its room (as the camera node does at +0x1b8: for other nodes NOT
established) and the renderer's per-frame list of rooms reached through gates can be read, hide a tag whose room is not in the list.
Matches what the renderer itself culls; misses walls inside one room (furniture, pillars) and keeps tags over a gate's whole view.
Coarser than A, no Havok call. Needs two readings (node room field, the frame's room list).

**D. Without the game (a stop-gap, can be done now with proven reads).** Hide a tag beyond N metres (`HeadMaxDist`, e.g. 25 m) and fade
it from N-5. It does not fix walls but removes the worst case (initials across a whole floor). Needs: the human's feet
`[player+0x460]` (kljoin.c / klescort.c, seen live) and the bot's place as klescort.c / klmove.c already read it for their distance
tests (`klb_rec` itself carries no place). If the owner wants something before A is read, this is it - pure data reading, no game call.

## 3. Proposed keys ([HUD], with HeadTags)

| key | default | meaning |
|---|---|---|
| HeadSight | 0 | 0 none (today), 1 option A (rays), 2 option B (ZCheckVisible), 3 option C (rooms) - only the ones implemented accept a value |
| HeadMaxDist | 0 | option D: metres beyond which no tag is drawn (0 = off) |
| HeadSightHold | 2 | ticks a ray must be blocked before the tag hides |
| HeadSightLog | 0 | 1 = every 5 s: rays cast, blocked, tags hidden by sight / by distance |

## 4. Order of work

1. (local, static) Read 0x6e0b20 + the call in 0x897d60 -> write the convention into re/firstperson_camera.md or a new re/sight.md.
2. (local, static) Read the 0x12c blocks of ZCheckVisible (B) - one afternoon; if they are per-pair visibility, B first.
3. Code A (or B) in klhud_tags.c: tick computes `seen[]`, render reads it. Off by default. Harness: the ray stubbed.
4. Live check S1: the bank, idle player in the hall, bots in the side rooms: pictures every 2 s; tags only on bots in view; the log's
   ray counts; no fault. Then a whole heist with HeadSight=1 for the frame budget (rays are main-thread time, not pictures).
5. If 1-2 cannot be done soon: D as `HeadMaxDist=25` for the owner to try (no game call; a small change in klht_tick).


## 5. 2026-10-23 (cloud session, static reading of kl2.exe only; nothing run)

**Option D is written**: `[HUD] HeadMaxDist=N` (metres, 0 = off, default) and `HeadFade=N` (default 5) in klhud_tags.c; the
arithmetic in klhud_tags_dist.h, checked by klhook/klht_test.c (448 checks, Linux + Wine). The human's feet and the bot's node
place are read with kle_human / kle_node (klescort.c, proven live); a tag past the limit is not drawn, one inside the fade gets
the colour's alpha scaled (the same alpha-in-colour GUESS as the outline's 0xd8). The 5 s log line (Log=2) counts "hidden as
too far / faded". Not run in the game: live check S1 of section 4 applies to it as to A (the alpha byte above all).
Suggested first try: `HeadMaxDist=25`.

**Option A, step 1 - the premise was wrong.** 0x6e0b20 is NOT a raycast. Read in full: it is the third-person camera's
pull-in step: `[this+0x3f8] = [0xb5f1e0]` (a constant), then `0x457c00(this, &point)`, which (when `[this+0x504]` = the followed
object is set) takes vtable slot 0xd4 (the followed object's "model" getter), its `+0xd50` skeleton, finds a bone index with
0x4a01b0 / 0x88c520, reads that bone's 48-byte matrix (0x78c710 = bone matrices, 0x64ecc0 = matrix -> quaternion) and writes the
bone's world position into `point` (0x4c34a0 / 0x7566e0 = vector store + transform). So 0x6e0b20 moves the camera's anchor to a
bone of the followed character and scales `[this+0x468]` toward it (0x7c97a0); the "-750 along +0x468" of section 1 is that
scaling, not a cast. 0x457c00 ret 4, __thiscall(this, float3 *out); 0x6e0b20 __thiscall(this), no arguments.

**Where the real cast is (not yet read):** Havok's `hkWorldRayCaster` and `hkSimpleWorldRayCaster` are in the exe (RTTI at
0xd490ab / 0xd49195), and `hkAabbPhantom::linearCast` (0xbe9d7d). The game-side wrapper that the camera's collision walk
(0x897d60, slot 55) and the AI's ZCheckVisible use has not been identified; nothing else in 0x6e0b20's neighbourhood casts.
Next static step: find the callers of the hkWorldRayCaster vtable (its vtable address follows the RTTI object locator; the
caller that builds a hkpWorldRayCastInput {from, to, filter} on the stack is the wrapper), then its convention. Until then
A stays unwritten and D is the stop-gap.
