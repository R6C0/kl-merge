# Review of track W2: the second crash in The Vault (kl2 0x8a040e reading 0x2c)

Adversarial review, 2026-10-11. Subject: `re/crash_vault.md` section 7 (uncommitted) and the worker's report.
Kept data: `<work>\research\crash_1011_vault2\` (`KLHook_1.dmp`, `KLHook_2.dmp`, `KLHook_tail.log`).
Everything here is dump + exe + file reading. **Nothing ran in the game.** No file of the worker's was changed.

## Verdict

**ACCEPT WITH FIXES.** The cause stands: I reached it from the dump before reading the note, and could not refute
it. No new fix is needed; `q_vault\DM03A_fix` is the fix and differs from `q_vault\DM03A` in the .prm member only.
One MUST for the lead (which tree goes out), the rest are SHOULD corrections to the note.

## My own triage (done before reading section 7)

- `0x8a0400`: `mov eax,[esi]; mov edx,[eax+0x2c]; call edx`. esi = ecx = `7f32b8e0`, whose first dword is 0. Main
  thread. Both hook dumps have the same registers and stack.
- The object's own memory is no object any more: `7f32b8c8` holds `{0x34, 0, 7f32b91c, 1.5, 97.6, -24.89, 0, ...}`
  and from `7f32b91c` on 64-byte records with places (448.1, -2091, -13320), (992.6, -2100, -13220), ... The pointer
  `7f32b91c` is `7f32b8c8 + 0x54`: this is a DrawChunk kind-7 desc with its elements inline (0x842e5b: `0x54 + 64 n`,
  `[desc+8] = desc + 0x54`). n = 0x34 = 52, so the copy covers `7f32b8c8 .. 7f32c61c`.
- The caller's list (stack `01a7159c`, 184 pointers): 121 ZRenderEntryGeomD3D, 27 Light, 14 Sprite, 12 Bones,
  8 BonesRigid, and exactly two with a zero vtable: #137 `7f32b8e0` and #159 `7f32c210`. Both lie inside the copy's
  range; no other list entry does.
- The block before, `7f32b700` (#173 of the same list): vtable `0xb99ed4` = ZRenderEntryGeomD3D, `[+0x19c]` =
  `0xf6be`, `[+0x1a1]` = 1, `[+0x1a8]` = `7f32b8c8`, `[+0x1c0]` = `4114cf53 c106e685`. `[0xef4d7c]` = 1 in the dump, so
  `+0x1a8` and `+0x1c0` are the slots DrawChunk writes for this frame index.
- Heap layout there: header `12345678 next prev base` at `7f32b6f0` and `7f32b520`, the object 0x10 later. The next
  header is at `7f32b8d0`, so `entry+0x1dc` is its `base` field and `entry+0x1e0` is the next object's vtable.
  `base` for the block at `7f32b520` is `7f32b518` (header - 8); by the same rule the dead block's is `7f32b8c8`,
  which is where the desc was copied.
- `0x926db0` with a non-zero `[esi+0x1dc]` and a size not larger than `[esi+0x1e0]` returns `[esi+0x1dc]` and zeroes
  both. Any render-entry vtable (about 12 million) is larger than 3,412.
- `python tools/kl_fa_vaultfx.py check <work>\build\q_vault\DM03A`: `... writes 53cf1441 85e606c1 over the first 8
  bytes of chunk 63166 (sprite, now 00000200 a1070000)`. Those bytes are the dwords `4114cf53 c106e685` at
  `7f32b700 + 0x1c0`. 63166 = 0xf6be.
- All 14 real Sprite entries of the list keep heads of the form `00000200 <tex> 0 7 ..`; the only entries with a
  kind-7 head on a Geom vtable carry the broken pair.

Comparison: same routine, same object, same origin of the null, same culprit as the worker. Differences are listed
under SHOULD.

## Attempts to refute

1. **Would the cause put a null at that load?** Yes, by the code read: the zero at `7f32b8e0` is written by
   `0x926dda` (`[entry+0x1e0] = 0`) and again by the desc copy (desc dword 6 is 0). Not refuted.
2. **The first crash, again.** In the first dump the freed 'pointer' was `c1c71aa0`. In this dump `c1c71aa0` is the
   desc's sixth dword, at `7f32b8dc` = `entry+0x1dc`. So the first crash is this crash one draw later: had the fire
   sprite been drawn again before the dead neighbour was gathered, `0x926db0` would have read `[+0x1dc]` = -24.89 and
   `[+0x1e0]` = 0 and freed the float. This ties the two crashes together independently of the chunk id. It also
   means the first crash destroyed a neighbour too; the first note's 'the block DrawChunk allocated lies at
   entry+0x1c8' is better read as this reuse path.
3. **Rounds that did not crash.** Of the tab maps only Withdrawal has a short blob, and there it lands on a
   post-filter chunk (`r_tab\DM03`: FAIL, chunk 60552, `pf`), so six knock-downs on Retomoto, Hot Coffee and the bank
   without a fault say nothing against the cause and nothing for the knock-down part either. The Vault's scripted
   loads are the weak spot, see SHOULD 2.
4. **A hook part instead of the map.** The dead object is a render entry overwritten by fire particles through the
   game's own copy at `0x842e8a`. The culprit entry's broken head is predicted bit for bit from the level file.
   Nothing kldown, klescort, klmove, kltalk or klfed writes is a render entry or a .prm chunk. The last knock-down
   ended 13 s before; six earlier ones in the same round passed. Not refuted: the hook is out.
5. **Timing against the log.** First vault money in a `bots: L1` line at 20:47:47.06 (bot 2, $15,000), fault at
   20:48:02.996: 15.9 s. The owner's own money is $0 throughout. In the first crash it was 6.7 s. Both crashes
   follow the first vault loot; no crash is known before it.

## MUST

1. **Only tree `w_tabS` may go out; `w_tabR` must not.** The installed `Maps\DM03A\F07_Main.zip` (sha1 `bd94d046`,
   equal to `q_vault\w_tabQ`'s) fails `check`. The lead's `now/mk_rtab.py` line 98 builds tree `w_tabR` with
   `DM03A=q_vault/DM03A` ('its crash fix comes later') and `DM03` from `r_tab\DM03` (FAIL). `now/mk_stab.py` builds
   `w_tabS` with `r_tab\DM03v` and `q_vault\DM03A_fix`. Re-run here:
   `gate (vaultfx) .../build/w_tabS/KLExpansion: 6 map(s), PASS`, and `w_tabS`'s DM03A archive is member for member
   CRC-equal to `q_vault\DM03A_fix`. `gate ... q_vault/w_tabQ/KLExpansion: 6 map(s), FAIL (2)`. The Vault has now
   crashed in two of the owner's two rounds that reached the vault loot; until `w_tabS` (or a later tree that passes
   the gate) is installed, the owner should be told not to play The Vault. `DM03A_fix` has never been loaded: one
   load run first, as section 5 says.

## SHOULD

1. **Section 7, the 'second Geom entry of the same chunk' `7f32e520`.** It is #8 of the list and keeps the broken
   head at +0x1ac and +0x1c0, but its `[+0x19c]` is `0xda95`, not `0xf6be`. It also holds `0xd54` (= 3,412) at
   +0x1e4 and +0x1e8, so it was used for the 52-element fire draw in both frame indices and has since been handed
   to another chunk (`0x5f6ad0` asks a pool, `0x815f40`, before the factories). Say that, not 'of the same chunk'.
   It shows the damaged entries are recycled into ordinary geometry, which widens 'silent damage'.
2. **'No human needs to enter the vault ... at risk from anywhere' is stronger than the evidence.** Scripted run V1
   (unfixed build, idle human in the yard, bots had the vault loot 103 s after GO) ended without a fault. That run
   had a live camera and the blast. So either the pots had not written in V1, or the damage stayed silent. The open
   question from section 2 (when a pot's cloth takes its slot) is what separates V1 from the owner's two rounds, and
   section 7 does not mention V1. State it: a moving human crashed 2 of 2, an idle one 0 of 1 with loot.
3. **Say plainly that the fix is proved by bytes, not by the live check.** PASS in the live check is 'no CRASH for
   120 s', which V1 already met on the unfixed build. The proof is that the padded blob's scratch ends at 0x3508 of
   0x3510 (`check`: FITS), so the write that broke the header cannot happen. The live run only shows the padded
   level loads and plays. The live check should use the walking script along the owner's route (yard, dock, hall),
   not an idle player.
4. **A fourth face, not in the note.** DrawChunk writes five dwords of the chunk head to `entry + 0x1ac + 20 x
   index` before it reaches `0x926db0` (0x842d91 .. 0x842db4). With index 1 that is `+0x1c0 .. +0x1d4`: 12 bytes
   past a 0x1c8-byte Geom entry, and the dword at `+0x1d0` (`0804c002`) lands on the next block's `12345678` mark.
   Seen intact in `7f32e520`'s tail. So every odd frame of such a draw also breaks the neighbour's heap header,
   whatever `0x926db0` then does.
5. **'12,164,820' is right, 'a ZRenderEntryGeomD3D neighbour' is inferred.** The neighbour's vtable is gone from the
   dump; only its place in a run of Geom blocks says what it was. Any render-entry vtable gives the same outcome.
   Mark it as inferred.
6. **`KLHook_2.dmp` was looked at here:** same fault, same registers. The game's own `.mdmp` was not, by either of us.
7. **The owner's request is still unassigned.** 'i want the vault enemies to keep spawning in like its in waves' is
   not part of W2 and nothing was done. It belongs to `tools/kl_fa_bank.py` (kl-merge-9b's, with uncommitted edits
   in the tree). The lead has to start that as its own track.

## The fix, checked

| check | last line |
|---|---|
| `check q_vault\DM03A` | `check (vaultfx): FAIL (1)` |
| `check q_vault\DM03A_fix` | `check (vaultfx): PASS` (blob 63165: 13584 bytes, scratch ends 0x3508 of 0x3510) |
| `check q_vault\DM03_fix` | `check (vaultfx): PASS` |
| `check r_tab\DM03` | `check (vaultfx): FAIL (1)` |
| `check r_tab\DM03v` | `check (vaultfx): PASS` |
| `check` installed `Maps\DM03A\F07_Main.zip` (read only) | `check (vaultfx): FAIL (1)` |
| `tree q_vault\w_tabQ\KLExpansion` | `6 map(s), FAIL (2)` |
| `tree w_tabS\KLExpansion` | `6 map(s), PASS` |

`q_vault\DM03A` against `q_vault\DM03A_fix`: 31 members each, one differs,
`Scenes/Locations/F01/F01_Main.prm` 72,157,904 -> 72,157,920 bytes. Side files that differ: `audit.json`,
`audit.txt`, `dyn.json`, and the new `vaultfx.txt`. Archive sha1 `bf869e5247ee44bd1e4577b9ca4b88fef87601f6`, as
reported. The worker changed no tool and gave no patch text; none is called for. `git diff --stat`: only
`re/crash_vault.md` (+88) of the worker's two files.

## Not established (by this review either)

- When the pots' cloth takes its slot, and so why V1 did not crash.
- What the neighbour `7f32b8e0` was before it was overwritten.
- What vtable slot 11 of a render entry answers.
- Whether the black rectangles of the first crash's picture are this fault.
