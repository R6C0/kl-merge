# 2026-10-23 03:05 crash (KLHook_1.dmp, kl2+0x526b40): .LOC past the 600,000-byte block - scheduled check-in, cloud

Read-only triage with `debug/dump.py` and a capstone sweep of every instruction of `kl2.exe` `.text`. The local sessions
had already found the same cause and installed the cap by 05:40 (`kl_loc.LOC_CAP = 612634`, `kl_loc_fit`, commit
4e2de5568; re/engine_facts.md "Known kl2.exe sites"). This note keeps the dump evidence and answers the open question
left there (why the 612,634-byte stock Russian file does not crash). Nothing was run in the game.

## 1. The fault, from the dump

```
CRASH c0000005 at kl2.exe+526b40 (00926b40)  reading 5dd133ae      main thread, 42.9 s after the F01 load
eax=2e73656c ebx=7763e8c0 ecx=01692d20 edx=00315000 esi=00000000 edi=776400c0 esp=01b4f604
callers: 006f3fd2 007549d6 (RMCSetCover) 00926aa6 008016ca 004c36af 00476d35 (WinMain)
slot F01 -> KLExpansion\Maps\DM01\F01_Main.zip (174,049,994 bytes, the 1023voice build), TEST hook of 03:00:39
```

`0x926b20` pops a 16-bit handle under the critical section `0x1692d20`: `eax = [0xeac170]` (the free count), then
`movzx ecx, word [eax*2 + 0xea68d6]`. The count held `0x2e73656c` = `les.`, the end of the line `"Don't ever
underestimate me, assholes."` (`YouEsc_04_R_C1`); `0xea68d6 + 2 * 0x2e73656c = 0x5dd133ae` is the faulting address.

The copied `.LOC` image in the dump runs `0xe100b8 .. 0xeac399` = **639,713 bytes** (the local note says 639,672 for
the V1 file; this run's file was 41 bytes longer). Everything from `0xea2878` to `0xeac399` was text.

## 2. What lies past the block (capstone sweep, skipdata, of .text 0x401000..0xb0fe30)

Addresses in `0xe100b9 .. 0xeb0000` that an instruction names (immediate or displacement):

| address | what | refs |
|---|---|---|
| 0xea2878 | the level's surface-table pointer (kl2 0x788cc0; freed by the scene teardown 0x41c360) | 68 |
| 0xea2880 / 84 / 88 | stack-switch scratch of 0x66ac50 / 0x926780 (esp and a pointer, written on use) | 3 / 2 / 1 |
| 0xea288c .. 0xea6887 | **nothing** | 0 |
| 0xea6888 .. 0xea6894 | the stack-switch slots (continuation address, saved esp, copy pointer, size) | 15 |
| 0xea6898 / 99 / 9c | byte flags | 5 |
| 0xea68ac / b0 | an object pointer and an object | 17 |
| 0xea68c8 / cc | counters | 7 |
| 0xea68d6 (0x400 words), 0xea70d8 (16-byte records), 0xeac0d8 (words), 0xeac158..0xeac174 | the handle allocator 0x926b20 / 0x6f4700 / 0x801610 pop, push and count here | 58 |
| 0xeac180, 0xeac280 | byte tables | 5 |
| 0xeac380 .. 0xeac3a0, 0xeac7a0 .. | misc, then a 429-reference table at 0xeac7b0 | - |

(The earlier `push 0xe100`, `push 0xea60` hits of a byte scan are decimal immediates, not addresses: the sweep
decodes instructions, so they are not in the table.)

## 3. Why stock Russian (612,634 bytes, spill to 0xea59d2) survives - the open question

In the dump `[0xea2878] = 0x6172f980`, a heap pointer sitting INSIDE the copied text: the game writes that pointer
AFTER the `.LOC` memcpy of the level load. `0xea2880/84/88` are written before each use. The rest of the spill band,
`0xea288c .. 0xea6887`, is addressed by no instruction (padding, or data reached only through a pointer - not
established). So the 12,634-byte spill of a stock Russian / Japanese load is overwritten or never read: that is why
`LOC_CAP = 612634` has held in shipped play, and why it is a grey band rather than proven room. The first state a
bigger file breaks is `0xea6888` (offset 616,400); the count at `0xeac170` (offset 639,160) is what faulted here.
English stays well under 600,000 (installed at 10:00 UTC: DM03 595,634 and DM06 595,206 are the closest).

## 4. Nothing to fix now

The installed 29 map zips: 0 members over `LOC_CAP`, 59 at 612,6xx (Russian / Japanese, as stock). A hook-side
guard would be a clamp of the two `call 0xa8d31e` memcpy sites (`0x7fef3b`, `0x466947`) at 600,000 bytes with a log
line - left to the local sessions, since klhook is theirs and the data-side cap already holds.
