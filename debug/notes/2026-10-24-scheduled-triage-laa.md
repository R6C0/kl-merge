# 2026-10-24 scheduled check-in (cloud, 21:48-22:05 UTC = 22:48 PC clock): the LAA-test crash dump, read

Nothing was launched or installed. The PC was busy (KLHook.ini 21:08 UTC = the k43 + CursorGuard install, dinput8.dll
20:56 UTC, the last commit 21:08 UTC), so this run stayed read-only: no game, no install, no screen. KLHook.result does
not exist in the game folder right now. KLHook.log (43 MB, last line 21:30:57 PC) ends with the k42 `exit: exit(0)`
that the 01:40 / k42 notes already explain (focus-loss ShowCursor stalls, clean exit, no dump); the only newer dump is
the LAA test's.

## kl2_490_crash_2026_10_24T19_2_42C0.mdmp (20:02:39 PC) = the 4GB/LAA test: a heap pointer above 2 GB lost its bit 31

The 01:40 log note files this as "LAA run: crash c0000005 at kl2.exe+0x1d69ba (write 02928030) after 85 s, unseen
before ... Engine tags direct pointers by bit 31 (re/hud.md), so LAA stays off". This is the dump's evidence for that
verdict (`debug/dump.py`, `dasm.py`, `rtti.py` on the staged dump + the staged kl2.exe, md5 68d7459e = the original
exe, so the restore held).

```
code 0xc0000005 at 0x5d69ba kl2.exe+0x1d69ba (WRITING address 0x02928030)     thread 45876 = the MAIN thread
eip=005d69ba esp=01a3e8f8 eax=0447dfe0 ebx=02928030 ecx=0000000d edx=005d6990 esi=0448a724 edi=02928030
callers: 0x67d0e3 (in 0x67cc60) < 0x60e218 < 0x462db5 < 0x5976fa / 0x597754 < 0x77b97a < (the same four again: a tree walk)
guest DLLs: ReShade32.dll 40/154, gameoverlayrenderer.dll, nvspcap.dll, medal-hook32.dll - none on the stack
```

| frame | what (RTTI via `rtti.py`) |
|---|---|
| 0x5d6990, slot 30 of **ZPrimAccessStandardWeightedMeshD3D** | copies one 0x34-byte record (13 dwords: a bone matrix row set) from record `[esp+0x18]` = 981 of the source array to record `[esp+0x10]` = 0 of the destination array: `rep movsd` with ecx = 0xd, esi = eax + 981*0x34, edi = ebx + 0 |
| 0x828f40 (called twice, once per array) | **the handle resolver**: four links deep (`[this+4]` -> `+0x28` -> `+0` -> `+4`), and at every link `test eax,eax; jns -> eax = [0xeac7b0 + 4*eax]` (bit 31 clear = a .prm chunk-table index) else `and eax, 0x7fffffff` (bit 31 set = a direct pointer with the tag stripped) |
| 0x67cc60, slot 3 of **ZRenderEntryBones** (+ Rigid / D3D variants) | the skinned-mesh render entry filling its bone palette, inside the scene-graph walk 0x77b8c0 > 0x597640 > 0x462da0 > 0x60e210 |

The destination array came back from the resolver as 0x02928030 and nothing is mapped there (the fault). The resolver
returns a value that is not a chunk-table entry only through its `and eax, 0x7fffffff` path, so the stored link was
**0x82928030**: a direct pointer. Without LAA no allocation can sit at 0x82928030 (user space ends at 0x7fffffff), and
with it the first heap block the game handed out above 2 GB is indistinguishable from a tagged pointer to 0x02928030.
That is why the run went 85 s (the block was allocated when the first skinned mesh of that kind needed a palette) and
why the same build never crashed there in weeks without LAA (and went 9 min clean right after the exe was put back).
The alternative reading - a stale tagged pointer to a freed block at 0x02928030 - would have crashed without LAA too.

How deep the tag goes (counted in kl2.exe's .text): **219** `jns ... ; and r32, 0x7fffffff` resolver sites and **418**
`[r32*4 + 0xeac7b0]` chunk-table loads. A 4 GB patch would need every one of those rewritten (or an allocator that
never returns an address above 2 GB, which is what no-LAA already is). Verdict: not KLHook, not a map, not ReShade.
**LAA stays off; nothing to fix in the repo.** `kl2.exe.laa-test` (10,504,344 bytes, 20:01 PC) is still in the game
folder; it is the patched copy and must never be launched or renamed over kl2.exe.

Owner: nothing to do for this one. (Optional, only if the 4 GB idea ever comes back: delete `kl2.exe.laa-test`.)
