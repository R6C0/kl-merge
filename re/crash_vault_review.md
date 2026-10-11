# Review of track W: the crash in The Vault (kl2 0x466597)

Adversarial review, 2026-10-11, of `re/crash_vault.md`, `tools/kl_fa_vaultfx.py` and `<work>\build\q_vault\DM03A_fix`.
Offline only; nothing ran in the game; the worker's files are not changed.

**VERDICT: ACCEPT WITH FIXES.** The cause is right and proved by bytes; the fix build is what it says. The MUST points
are about what is still on the owner's game and in the source, not about a fault in the worker's deliverable.

## 1. My own triage (done before reading the worker's note)

From `KLHook_1.dmp`, kl2.exe and the build's .prm:

- 0x466590 is the heap's block-header test (`cmp [p-0x10], 0x12345678`), reached from the engine's free 0x882c30 <-
  0x7f05f0 <- 0x6ad680 <- 0x926db0. 0x926db0 is `mov eax,[esi+0x1dc] ... push eax; call 0x6ad680`: it frees a render
  entry's spare per-frame block when it is too small. p = c1c71aa0 = the float -24.89.
- esi there (saved at esp+0x28 and esp+0x50) = `48f9fc50`, vtable 0xb99ed4 = **ZRenderEntryGeomD3D**. DrawChunk's
  frame: handle **0xf6be = chunk 63166**, desc 71cc82ec `{1, 0, 71cc72ec, 1.5, 73.96, -24.89, ..}`, caller a
  **ZParticleController** (375f9140). DrawChunk took the branch for `[chunk+0xc] == 7` (0x842e5b).
- The entry's own copy of the chunk head (entry+0x1ac, and again +0x1c0): `4114cf53 c106e685 00000000 00000007
  0804c002`. In the file chunk 63166 is `00020000 000007a1 00000000 00000007 0804c002`: a sprite whose first 8 bytes
  were replaced. The sprite factory 0x6bb690 does test `word [chunk+2] == 2` and makes 0x1ec bytes.
- `4114cf53 c106e685` occurs exactly ONCE in the 72 MB .prm: at +0x928 of chunk 63165, the chunk right before, as the
  y and z of the last of its 193 twelve-byte records (70.603, 9.3006, -8.4313). In memory the two chunks are adjacent
  (table 0xeea2a4: 07f80880 and 07f83d80 = +0x3500).
- The block at entry+0x1c8 (48f9fe18) is the previous frame's desc copy (`.. 1.5, 47.85, -24.89`; its first three
  dwords overwritten by the head copy at +0x1c0): the entry is shorter than 0x1dc and had been drawn at least once.
- 0x87df60 (read in full): base = slot table end, `and ecx,0xf / sub / add` at 0x87e041..0x87e04f rounds it up to 16.
  Dead Men's 0x58ae9a..0x58aeaf has the same code WITHOUT the rounding. Blob 63165: table ends 0x22e4, 24 x 193 of
  scratch -> 0x34fc in Dead Men, 0x3508 in Dog Days, chunk 0x3500.
- The 18:40:31 dump: DiscordHook.dll+0x1f7fd, render thread inside Present. Unrelated.

Same routine, same object, same chunk, same mechanism as the worker. Nothing in his chain was found wrong.

**My two-sentence cause:** the plant pots' Dead Men cloth blob (chunk 63165) is 8 bytes shorter than Dog Days'
16-rounded layout addresses, so when a pot's cloth takes its simulation slot the game itself writes the last particle's
y and z over the head of the next .prm chunk - in The Vault the sprite of the vault fire's `Vault_Fire` template. The
headless sprite gets a geometry render entry that is too short for DrawChunk's sprite path, which then frees a float
of the particle desc lying behind it as a pointer.

## 2. Attempts to refute

| attempt | result |
|---|---|
| Does the data pattern give THAT pointer at THAT instruction? | Yes. The 8 bytes over the sprite are unique in the file and are the neighbour's last 8 payload bytes; -24.89 is the desc's sixth dword, 0x14 into the block that lies at entry+0x1c8. |
| Same pattern in builds that ran for hours without this fault? | **Yes: Withdrawal on the owner's tab** (`z_cover3\M03` = `p_tab\DM03`, blob 60551, 13 pots) - but the chunk behind it there is the post-filter set (kind `pf`), not a sprite, so no geometry entry and no crash is expected. Not a refutation; it is MUST 1. The four other tab maps: PASS (0, 2, 10, 2 blobs). Stock: 88 blobs, 0 short (re-run by me). |
| A hook part instead? | Ruled out by the bytes: no part writes floats into a sprite head, and the value is predicted from the level files alone. klmem served this .prm from the reserve (log: `block of 69.2 MB is in the reserve (04180000`); the buffer starts at 0x04180010, 16-aligned, so the exe's rounding (done on the absolute address) equals the tool's (done on the offset). klgun writes one bit in mesh objects. BoardNear / klcrew / kltalk / klbalance touch no .prm chunk; no down, no fed in that round. |
| The blast's show (the builder's added note)? | The faulting chunk IS one of the show's (the fire of `Bank_Vault_Fire01`), but it is a good Dog Days sprite in the file; it was broken by its neighbour, not by being a Dead Men template. |
| Deterministic? V1's log? | Not established, as the worker says. V0 / V1 / V2 end `RESULT PASS ... faults 0` with an idle player; they do not discriminate (neither 'a pot took its slot' nor 'the fire was drawn' is shown for them). No cloth object is in the dump, so which pot wrote and when cannot be read from it. |

## 3. The fix, checked

- `DM03A` vs `DM03A_fix` archives: 31 members, same order, only `F01_Main.prm` differs (72157904 -> 72157920). The
  tool's own proof (every other chunk equal, blob = old bytes + 16 zeros) is in `apply`. sha1 bf869e52.. confirmed.
- Tree `w_tabQ\...\DM03A\F07_Main.zip` = `q_vault\DM03A` member for member (CRC + size), so the fix base is what the
  owner played.
- Beside the archive: `dyn.json` (the stated edit), `audit.txt` / `audit.json` (rewritten by the worker's audit run:
  path and content id only), new `vaultfx.txt`. Everything else byte-equal.
- Re-run by me on a scratch copy: fedbody PASS, kl_impact `problems: 0`, fedpoints PASS (7 NOTE), bots_dyn PASS,
  kl_fa_bank check PASS / reverify 0, kl_chars 0, map_guns ok, talk FAIL 0, audit exit 1 with 2 findings - the same
  last lines as `_log\checks\summary.txt` for the old folder.
- `kl_fa_vaultfx check`: exit 1 on `q_vault\DM03A`, `c_bank\bank_vault*` (4), `p_tab\DM03`, `z_cover3\M03`; exit 0 on
  `DM03A_fix`, `p_tab\DM01/02/06/09`. `stock`: 0 short, 88 exact, 16 longer than Dead Men's layout.
- Coverage: in DM03, DM03A the chunks `kl_prmgraph.walk` calls `cloth` are exactly the ones `ZCloth[15]` names.
- Side files keyed to the .prm (KLGuns.ini, KLJoin.ini, KLWardrobe.ini) go by chunk COUNT, which does not change.
- The `dyn.json` edit is acceptable: the check compares `big_before` with the folder, the old size stays readable
  under the `vaultfx` key.

## 4. MUST

1. **Withdrawal on the owner's tab has the same overrun and must be fixed in the same tree.** `z_cover3\M03`
   (`p_tab\DM03`): blob 60551 writes `9bcf1441 d2e606c1` over chunk 60552, the post-filter set that the scene's
   PostFilterBoxes name. It is memory corruption in a map he plays daily, whatever the two floats mean. `apply` on
   that folder (to a NEW folder, not built here), re-run its checks, and swap it in together with `DM03A_fix`.
2. **The source still makes it.** kl-merge-9b's running rebuild (`c_bank2`) and every later bank / M03 graft will carry
   the short blob again. Until `fix_level` is in `kl_graft.build`, `kl_fa_vaultfx check` must be a gate of the tree
   build (beside the audit), not a step somebody remembers. All four `c_bank` folders fail it today.
3. **The live PASS must not hang on the black rectangles.** They are a GUESS in the note, and near-black boxes round
   fires are known on Withdrawal (`re/carfx.md`), where no sprite is hit. PASS for this fix = no fault for 60 s in the
   vault after the first vault loot, facing both fire places. Rectangles are reported separately (if they stay, they
   are track T's subject or the show's Dead Men templates: then `--no-blast` for the owner until looked at).

## 5. SHOULD

4. Answer the builder's added question in the note in one line: yes, the chunk is the show's; no, `--no-blast` is not
   the fix (the overrun stays and hits whatever chunk follows); it would only hide the symptom, because the fire's
   emitters never start. With the pad in, the Dead Men fire is drawn properly by Dog Days for the first time before a
   human - look at it in the scripted run before it goes on the tab.
5. The note says 0x72a920 'copies the rest places into both arrays'. For this blob h = 1 (`[obj+0x84] == 1`), so the
   routine takes its first branch (0x72a941: two calls of slot 8 of `[[obj+0x40]]` with (0, n, dest) and dest + 12 n),
   not the float loop. Same extent, and the dump shows the bytes are the rest place - but say which branch.
6. The tool's rule is offset arithmetic; the exe rounds the absolute address. Equal only while the .prm buffer is
   16-aligned (it is: 0x04180010 from the hook's reserve). One sentence in the docstring.
7. A multi-slot Dead Men blob whose step (24 n) is not a multiple of 16 is accepted as the known shape; stock stores
   steps rounded to 16. None of today's builds has one (flags: 720, 2 x 58, 64, 72 - checked). A NOTE line for that
   case would be cheap.
8. The 3 `plant` chunks (ZPlant[2]) are the other Dead Men simulation blobs in these levels; their layout was not
   compared between the two games. Not shown to be at fault - an open item, worth one read of the exe.
9. 'Deterministic or not' could be settled offline by reading who calls ZCloth slot 119 (0x8ac1d0) and its distance
   test (`[obj+0x44]` vs `[obj+0x4c]`, `[0xdd2640]+0x50`); the live control run on the old build is otherwise the
   only evidence, and one clean run would not clear it (the worker says so).

## 6. Not done by this review

Nothing ran in the game. The Withdrawal fix folder was not built. The post-filter fields were not read. Who calls
slot 119 was not read.
