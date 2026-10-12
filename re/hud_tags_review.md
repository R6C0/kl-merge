# Review: klhud_tags.c (head tags, 2026-10-12)

VERDICT: ACCEPT WITH FIXES. The route is sound and the offsets re-derive from kl2.exe. One MUST (stale objects after a reload at the same template address) and two SHOULDs. Nothing found near osd+0x10fc; nothing is written into the game's tag, record or element.

## Re-derived from kl2.exe (all agree with the worker)
- 0x7b8150 is thiscall (ecx = tag struct), 5 stack args, `ret 0x14`: a1 (unused), node, ctx, cam, a5 (unused). The hook's `__fastcall(this, edx, a1, node, ctx, cam, a5)` matches. Prologue bytes `83 ec 68 53 8b d9 80 7b 40 00` match `klht_code`.
- The drawer only READS the tag struct: [this] (our object), [this+4] (picture desc, only if config 0x793550), [this+0x40] (flag). It never writes it, so the 0x48-byte copy is safe. The final call is vt[0x1e8](ctx, cam, pos, scale) = 0x5a6d40 (ZCHAROBJ::Draw). The xform comes from the drawer's own 0x7f07a0, so this does not rely on klu_draw_one's reconstructed matrix.
- Stock loop 0x5e6160..0x5e6226 matches klht_render and klht_tick: the `0xff` skip; node = [rec+4] when byte[rec+0x79]&1; rec = [recs+0x348] + 0x7c*id (0x7fd930); the draw condition `[el+0xed8] || E+0x10 in {1,4} || E+0x14 in {5,6}`; state gate 0x19 (0x5e6120). `s->rules` equals the object 0x508ef0 returns ([[0x168e9e4]+0x54]); klbot.c:294 reads it the same way. klb flags bit 0 is the record's 0x79 bit 0 (klbot.c:42), so guess 3 of the worker is settled.
- SetOffset 0x45d6e0 = vt+0x21c: (vec*, byte), `ret 8`, stores +0x1c/+0x20 and calls vt+0x1f0. The hook's call and its vtable check are right. SetText 0x896e50 copies into the object's string (0x783290 on +0xa4), so passing the stack `buf`/`mb` is fine.
- Element hidden by +0x25, so nothing of the top-left block is drawn. klfedkit writes only +0xee0/+0xf00, which the hidden element does not draw. No conflict.

## MUST
M1. Stale objects when a level is reloaded at the same template address.
- `klht_r` is reset only when `klht_r.tmpl != klu_r.tmpl` (klhud_tags.c:89), and that test runs only inside klht_tick.
- klu_reset (klhud.c:1087) zeroes klu_r, so tmpl becomes 0. The next klht_tick, which sees tmpl 0, comes only after klu_tick passes line 1217. A scene change, a new round or an osd change returns earlier with no klht_tick call. If the new level's template is allocated at the same address (tmpl = 0x8ccde0([osd+0xd4c]); klhud.c:1186-1200 already worries about "the same address"), `klht_r.s[i].made` stays 1 with `ini/inis/mon/mons` pointing into the freed scene.
- Consequence: `klu_set` writes into freed or reused heap, and Draw gets a dead object. That is heap corruption or a crash on the second round.
- Fix: add `klht_reset()` called from klu_reset, inside the lock, next to `klwd_reset()` (the weapon dial does exactly this, klhud_weapon.c:602). Or key on a generation counter bumped in klu_reset. Do not key on tmpl.

## SHOULD
S1. The draw-instance budget is unmeasured with the tags. klu_n_maxinst is sampled in klu_draw_ours (klhud.c:416), BEFORE klht_render, and DrawChunk has no capacity test (klhud.c:416 comment). Worst case is 12 bots x (2 initials objects + 2 money objects). H1h measured about 7 instances for a short string; that gives roughly 70 instances at HeadTags=1 and about 250 at HeadTags=2, on top of the "hundreds" of the rings. Sample `*ctx[1]` after the loop into klu_n_maxinst, and read the peak in G1 with HeadTags=2 and 7 bots before shipping HeadTags=2. Consider skipping the shadows when the count passes a measured bound.
S2. Traitor colour leaks to the player. `kluv_state` returns TRAITOR on the bot's own mark `flags&2` (klhud_values.c:~517), which is set before the bot turns on anyone (klbot.c Tune/Backstab). The tag is projected with no occlusion test (the drawer has none), so the orange initials are visible through walls. The crew list showing it was a design decision of the owner; a world tag is a different exposure. Make tag orange depend on score flag KLUV_F_TRAITOR only, or add a key `HeadTraitor=0`.

## NOTE
N1. Fallback initials (klhud_tags.c:109) when klnm_tag_ini fails are not unique, and they flicker to the table value once klnm_refresh succeeds. klnm_tag_ini has no settle time like the rename path's 1.5 s. Low impact.
N2. TryEnterCriticalSection failure skips the whole tag pass for that frame, so tags blink while the tick holds the lock. Same trade-off as the rest of the HUD (klu_n_try counts it).
N3. About 130 ReadProcessMemory calls per frame (klh_rd) plus up to 48 drawer calls, each re-projecting the head. Roughly 0.2-0.4 ms; fine at 60 Hz. Compute once per bot and draw 2-4 objects if it ever matters.
N4. State changes (0x19 to 0x1b, level end) are seen up to 100 ms late, because the gate is the tick's `s->state`. There is no crash path: klu_draw_on and klu_r.hid drop at the next tick, and the osd cannot be freed while its clock element is rendering.
N5. Bots aboard the van (kind CREW) keep their tag, as the stock loop does (E+0x10/+0x14 conditions). The same applies to bots hidden behind the camera: the drawer has no cull.
N6. On stock levels and online the part is inert: klu_r.made needs the non-stock verdict or Stock=1; online fails klb_read (rules vtable), so `s` is NULL and klht_tick exits. HideStock=0 or Crew=0 leaves the stock tags (full names) and this part idle, as documented. Setting both NameTags=1 and HeadTags is harmless.
N7. Nothing near osd+0x10fc is read or written (only +0x10c4 via KLU_O_PLIST). The SHA1s in the report match the files on disk (870ea5e5.., 57ccdce4..).
