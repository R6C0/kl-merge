# Is the AssertSoft step-over safe? (2026-11-01, static, kl2.exe sha1 9d99e01d, read with debug\dasm.py)

Nothing run in the game. Question: veh() steps over the int3 at five listed VAs (Eip += 1). What does each assert test,
and what runs next? Could it index `[L+0x44] + idx*0x7c` out of bounds and read or write there?

L = `[[0xdd265c]+0x15a0]` (0x713130), cover pool = `[L+0x44]`, record stride 0x7c, flags at `[rec+0x68]`.
The game's own bound is idx < 0x1788 (cmp at 0x656775 / 0x84599c). GUESS: the pool really holds 0x1788 records
(the bound is the only evidence; the allocation site was not read).

## What all five test
`flags = [rec+0x68]; if (flags & 2) -> kind 0 ; else if (flags & 0x200) -> kind 1 ; else int3`. The int3 sits on the
fall-through of the "neither bit" case and the next byte (int3+1) is `xor eax/al` = the SAME instruction the
"bit 2 set" case jumps to. So stepping over is exactly "kind 0", a path the game runs for every ordinary record.
A client spare record has flags 0x400 only (re/dm_car_cover_1101.md), hence the assert.

## Per site (condition, record source, what runs after)
| VA | function | rec / idx source | index bounded before the assert? | after the step | verdict |
|---|---|---|---|---|---|
| 0x6567e8 | 0x656740 (called by 0x581b40 <- 0x6afcf0) | edi = `[L+0x44] + [esi+4]*0x7c`, idx from the caller (movsx word) | yes: `jl` 0x656762/0x65676f and `cmp 0x1788; jge` 0x656775 skip the whole block (jump to 0x656869) | `al = 0` (0x6567e9), then bl = 0, `[esi+8]=1`, 0x598a80(…); no write to rec | safe (read of an in-range, unbuilt record) |
| 0x845a8b | 0x845980 (state setter, arg ebx) | esi = `[L+0x44] + [edi+4]*0x7c` | only when ebx != 0 (0x84598f: `je 0x8459a7` skips the check). `jl` is the only test on the assert path | `al = 0`; `[edi+8] = state`; for state 4 0x845b53 calls 0x4ede00 with rec (read-only kind-0 path); no write to rec | OOB READ possible with ebx == 0 and idx >= 0x1788; the read happens BEFORE the int3 (0x845a7d), the step changes nothing. No write. |
| 0x51d049 | 0x51d020 (kind query) | `0x491eb0`: rec = `[L+0x44] + [ctx+4]*0x7c`, NO bound at all | no | `eax = 0` (0x51d04a) then returns a code from `[esi]` (the ctx word), rec not touched again | OOB READ possible (pre-int3, at 0x51d034). Post-step safe: rec is not read again, no write |
| 0x555900 | 0x5558d0 (cover-point aim/fire helper) | edi = `0x491eb0` result, NO bound | no | falls to 0x555944 (kind 0): reads `[esi+0x40]`, `[esi+0xa8]`, calls 0x76c040 (= 0x8eb5e0, list search on rec: reads `[rec+0x20..]`) and 0x579f70 (reads `[rec+0x28..0x30]`, writes only its out argument `[ebp-0x10]`) | OOB READ possible if rec is outside the pool (pre-int3 at 0x5558eb AND post-step reads via 0x8eb5e0/0x579f70). Never a write to rec. A garbage `[rec+0x20]` loop count could make 0x8eb5e0 scan far: bounded by the same garbage, read only |
| 0x4ede1b | 0x4ede00 (kind test, this = rec) | esi = ecx = rec, computed by the caller (0x845b4d, unbounded idx) | n/a | 0x4ede65: builds a zero vector on the stack, calls 0x6903b0 with `[arg+0x40]`; no rec access | safe post-step; the pre-int3 read of `[rec+0x68]` is the caller's index risk |

Summary: no site writes out of bounds and none dereferences null AFTER the step that it would not also dereference on the
game's normal kind-0 path. The int3 is not a guard for anything; it is a debug `ASSERT(kind known)`. The only hazard is an
index that is itself out of range: for those the read of `[rec+0x68]` already happened before the int3 (an access violation
there is a CRASH, not an assert, and veh() does not soft-handle it), and the step-over only matters if the garbage flags happen
to be zero. At 0x555900 that case continues into two more reads of rec.

The entry check `[L+0x44]` null (client before the pool exists) would be a null deref in 0x491eb0 / the imul line itself, before
any int3; also not changed by the step.

## Callers (0x656740, 0x581b40)
0x581b40 (ZActor-ish net/anim entry, `ret 4`) calls 0x656740 with `movsx edx, word [esp+0xdc]` as the state index when
`0x9425a0` (is-local-owner) says no; 0x6afcf0 calls 0x581b40 for a non-null owner for which 0x9425a0 returns true. The index is a 16-bit
signed value, so it is -0x8000..0x7fff; 0x656740 stores it in `[esi+4]` and bounds it (0 <= idx < 0x1788) before touching the pool.
The host replicates indices of its runtime cover points; the client's pool slot is an unbuilt spare (flags 0x400), in range. That is
the observed AS2 case (83 soft hits at four sites, 0x6567e8 not hit in AS2).

## Verdict
- 0x6567e8: SAFE.
- 0x845a8b: SAFE for the observed case; OOB READ only for ebx == 0 and idx >= 0x1788 (pre-existing).
- 0x51d049: OOB READ only for an unbounded idx (pre-existing); post-step safe.
- 0x555900: OOB READ only for an unbounded idx; post-step reads rec further (read only).
- 0x4ede1b: SAFE post-step.
- No OOB WRITE and no null deref introduced by the step-over. AssertSoft as shipped is safe for the DM01 client case.

## Design kept for the residual risk: [KLHook] AssertSoftGuard=0 (default off)
No "skip the whole block" or "return failure" is needed: the fall-through already IS the failure value (kind 0) and forcing a
return from inside the frame (pop/ret imm, callee-saved registers, SEH frame of 0x581b40) is far riskier than the int3 step.
Instead `klassoft_logic.h` carries a per-site table (`kas_sites`: where the record lives at the int3: edi, esi, or index at
`[esi+4]`) and `kas_guard_ok()`. With the key on, veh() steps over silently only when the record is inside
`[L+0x44] .. +0x1788*0x7c` on a 0x7c boundary (or idx < 0x1788); otherwise the hit takes the ordinary, visible assert path
(logged, dumped once) and the first five refusals are logged as `AssertSoftGuard: ... NOT stepped over silently`. Test:
`klhook\klassoft_test.c`. Mod options row `assertsoftguard` "(recommended off until benched)". NOT run live.

## Anti-tamper (re/antitamper.md)
Nothing patches .text or uses debug registers: veh() only changes Eip (+1) and reads the pool pointers (data, heap), the
allowed kind of hook. The guard adds reads of `0xdd265c` (.data) and heap only.
