# klnet_poollog: log the entity slot pool at each level load (opt-in, read only)

2026-10-19. Patch: `re/klnet_poollog.patch` (one file, `klhook/klnet.c`, `git apply` from the repo root). NOT applied to
the repo, NOT run. Compiled once in a scratch copy under %TEMP% with `klhook\build.bat` (SHIP flags `/O2 /LD /W3`, no
warnings printed): patched dll md5 E0F71EB7EEBD405A75BE4C6B7252C813; unpatched current sources
9D99723D1AE2FD588A4FE5B1538C26DE. klhook/* is 3f's; the patch waits for 3f.

## What it adds
- `KLHook.ini`: `[Net]` `PoolLog=1` (default 0 = no code path taken, no log line, behaviour unchanged).
- `klnet_pool_tick()`, called at the top of `klnet_tick` (before the session gate, so it also works in Arcade, where there
  is no network session and `[Net] Log` would stay silent). Polls every 100 ms; logs only on a CHANGE of any of: manager,
  pool, cap, slot size, memory block, scene name. First poll always logs. Every read goes through `klh_rd`
  (ReadProcessMemory, never faults).
- Chain, from re/private_match.md ("where the wire ids come from", "pool lifetime"): `M = [0xe0ff90]` (slot manager),
  `P = [M+0xc]` (pool object), `[P+4]` slot size, `[P+8]` cap in slots, `[P+0xc]` memory block, `[P+0x10]` table of cap signed
  16-bit tags. VERIFIED against kl2.exe by disassembly (review 2026-10-19): 0x6ece90 = `mov ecx,[0xe0ff90]; call 0x86ca10`; 0x86ca10 reads P=[ecx+0xc], divides (obj-[P+0xc]) by [P+4], indexes the word table [P+0x10], multiplies the tag by [P+8]; the pool builder 0x89bc80 stores size at +4, cap at +8, block at +0xc, table (cap words, filled with 0xffff) at +0x10; 0x4c2f01 builds it with (0x80, [mgr+8]); 0x4c2fdc stores the manager in [0xe0ff90]; 0x8ad931 tests [db+8]. The task text's `[[0xe0ff90]+0xc]+8` is the cap; the task's "mgr" is the POOL P in the section's names.
  Checked against the section's text only; not run.
- Also logs, on each change, how many tags are >= 0 (slot in use; a freed slot has a negative tag, 0x8861a0) and the highest tag
  (capped: only when cap <= 0x20000; the buffer is 256 KB static). This tells whether a level went through the pool a
  second time.
- Scene: `klh_scene()`, the hook's existing reader (`[[sysif]+0x2b0]`).

Log lines (KLHook.log):
```
net: PoolLog=1: ...                               (once, at init)
net: pool #N: scene '...'; manager [0xe0ff90]=.., pool [mgr+0xc]=.., slot size 128, cap C, block .., tags ..; slots with tag >= 0:
net: pool #N: K slot(s) with tag >= 0 (...), highest tag T ...; cap*128 = .. bytes
```
A scene name can change a moment before or after the pool does: read two adjacent lines as a pair. Brief states during a
load (pool gone, `NO MANAGER`) are logged too.

## Test plan for 3f
1. `[Net] PoolLog=1`. Start a session on map A (an FA map of the rotation), play or sit until the round is up. Note
   line #N.
2. Let the rotation load map B (or leave and start B from the menu in the same process). Do NOT restart the game.
   If possible a third map C, and A again.
3. Read the lines. Compare `pool`, `cap`, `block`, `tags` between the A and B lines, and the tag counts.
4. Choose maps with different caps (private_match.md, cap table: F03 27014, F04 27505, F06 27539, F08 29145; F01/F02/F05/
   F07/F09 sit at the 26624 floor), e.g. F08 then F01, so "cap kept" and "cap recomputed" differ visibly.
5. Local Arcade works for this too (no net needed), and the same log on a second PC in a real session tells whether
   both PCs agree.

## Reading the outcomes
- Same `pool`, same `cap`, same `block` after B loads (a NO MANAGER gap absent): the pool SURVIVES level changes. Cap comes
  from the FIRST map of the session (GUESS in the section). Tag-0 ids still match between peers. Ids with tag > 0 depend
  on how often slots were reused, so different play histories can make them diverge. Consequence for the rule:
  "start on the same map" matters because the first map fixes the cap for the session; two PCs whose first maps differ
  (different cap) disagree on every id with tag > 0 after the first reuse. Highest tag > 0 after B = slots were
  reused. "Same first map and build" stays the rule; a second map is then as safe as the first for tag-0 ids.
- A NO MANAGER line (`[0xe0ff90]`=0) between A and B, then a new pool with `cap` for B: the pool is REBUILT at each load
  (slot 11 / destructor path runs between scenes). Tags restart at 0 for every level, cap follows each map, so the
  "start on the same map" rule is weaker than stated: each map just has to be the same zip on both PCs. Overflow only matters inside
  one round.
- A new pointer for P or `block` but with no visible NO MANAGER gap (the poll missed it, 100 ms): same as above;
  the pointer change is the evidence.
- Same pointer, different `cap`: not expected from the code read (cap is set at build); if seen, the structure
  is wrong or reused in place: report the lines, do not draw a conclusion.
- Unreadable fields (`manager without a readable pool`, `tags not read`): the chain is wrong for this build; the
  static reading is not confirmed.

## Limits / GUESS
- GUESS: 100 ms polling sees every rebuild (a rebuild during a load lasts seconds; a very fast one could be missed).
  The pointer would still differ when seen later.
- GUESS: a freed-and-reallocated heap block could return the same address for a rebuilt pool. Compare `tags` and the live
  count too: a rebuilt pool starts with 0 slots >= 0 until the load (all tags -1).
- Tag semantics (-1 never used, >= 0 allocated, < 0 freed) are from the static reading, not verified live.
- Does not decide wire-id equality between PCs; it only settles pool lifetime. Each peer logs its own.
