# 2026-10-23 residual stutter with Payday 2 music OFF: today's four launches read from KLHook.log, the hitch sites resolved in kl2.exe - scheduled check-in, cloud

Read-only. Source: the live `KLHook.log` (9 MB, 13:39 - 14:00 PC clock, four launches, the owner playing DM01 / DM01B
in Arcade), aggregated per launch; the `KL2.exe+offset` samples of the hitch probe disassembled with `debug/dasm.py`
against a copy of `kl2.exe`. Nothing was run in the game. win32u / USER32 offsets are the local sessions' resolution
(klextpt.c): win32u+0x101c NtUserPeekMessage, +0x107c NtUserMessageCall, +0x11ec NtUserCallNextHookEx; +0x5fdc is not
resolved (a Nt* syscall below the three; it appears in every launch, with the Sleep return addresses).

## 1. The four launches (hook 1023u/v SHIP; `core: hitch` = a frame of 120 ms .. 3 s; the probe samples hitches of 50 ms+)

| launch (PC clock) | music | play time | `core: hitch` lines (sum, longest) | hitches of 100 ms+ per minute | main thread stood at (probe) |
|---|---|---|---|---|---|
| 13:39:38 | ON | 13:39:54 - 13:42:44 (2.8 min) | 89 (19.4 s, 549 ms) | 32 | win32u+0x101c PeekMessage 810, +0x107c MessageCall 405, ntdll+0x7320c 165, +0x11ec CallNextHookEx 154 |
| 13:45:37 | ON | 13:45:53 - 13:49:33 (3.7 min) | 75 (19.7 s, 549 ms) | 20 | the same three (951 / 405 / 188) + win32u+0x5fdc 319 |
| 13:50:42 | OFF | one scene only | 1 (2.5 s) | - | ntdll+0x7320c with steamclient.dll + KL2 0x9a6f03 / 0x994f1a on the stack (a Steam call, once) |
| 13:52:41 | OFF | 13:52:55 - 14:00:47 (7.9 min) | 12 (4.2 s, 693 ms) | 1.5 | win32u+0x5fdc 162, ntdll+0x7352c 76, +0x7320c 56, **KL2 0x90e0ae / b5 / c3 / b7 50** |

Return addresses with music ON: USER32+0x3c67a PeekMessageW 1341, +0x209e5 PeekMessageA 810, +0x43bb0 774, +0x3c316
CallNextHookEx 562, ReShade32+0x5ff67 410, gameoverlayrenderer+0x992bc 410, OpenAL32+0x3308 205, uiautomationcore+0x655f0
197 (launch 0); launch 1 adds KL2 0x531598 548 and the chain 0x41e984 / 0x6a3fb7 / 0x415cc4 / 0x472f24 (316 each).
With music OFF: KERNELBASE+0x140d30 198 (SleepEx), **KL2 0x90d4ed 81, 0x90da27 79**, KERNELBASE+0x13563b / +0x1355df 73,
KERNEL32+0x211a0 62, **KL2 0x53c806 62** (the Sleep(25) stream poll, klextpt.c), MSVCR90+0x3065f / +0x306be 58 / 55,
**KL2 0x90e620 58**.

So `[Music] Enable=0` took the 100 - 550 ms hitches from 20 - 32 a minute to 1.5 a minute - the owner's "stutters dont
feel prevalent anymore" (14:00) in numbers. The music-ON hitches are the known message-pump chain (klextpt.c: hooks run
by the game's own PeekMessage, with the overlay, ReShade and UI Automation on the stack); whether the MCI worker's missing
message pump is what makes those hooks slow stays the open A/B of the 14:30 note.

## 2. Where the remaining 12 hitches sit (music OFF launch): every one at a scene transition

| time | what the log shows | hitch |
|---|---|---|
| 13:52:55 | frontend -> Arcade, `KaneAndLynch.gms` loading | 365 + 172 ms; probe: ntdll+0x7352c / +0x7320c <- SleepEx <- KL2 0x53c806 (Sleep(25) poll) |
| 13:53:02 - 13:53:06 | `level archive f01\f01_main.zip opened` (DM01), `fed: round 2` | 655 + 281 + 149 ms; probe: win32u+0x5fdc 80, ntdll 42, **KL2 0x90e0b5 / c3 / ae / b7** 23 |
| 13:57:08 | `fed: round 3` | 136 ms = the hook's own `near: 1 ZAllyEscapeBox object(s) found in 125 ms (the game stood still that long; looked for anew at every round's start)` |
| 13:57:47 - 13:57:48 | round over -> `the scene 'SCENES\KaneAndLynch.gms' is no level` (menu) | 313 + 668 ms; probe: Sleep poll + KL2 0x50e0ae |
| 13:57:53 - 13:57:57 | `level archive f03\f03_main.zip opened` (DM01B), `fed: round 5` | 126 + 148 ms; probe (219 samples): **KL2 0x90e0c3 / b5 / ae / b7** 23, nvd3dum+0x13bd1b 6; returns **0x90d4ed 60, 0x90da27 59, 0x90e620 58**, MSVCR90+0x3065f 58 |
| 14:00:45 - 14:00:46 | round over -> menu | 518 + 693 ms; probe: win32u+0x5fdc 82, Sleep poll, KL2 0x90e224 / 0x90e23d / 0x90e0ae |

In play (13:53:16 - 13:57:45 and 13:58:07 - 14:00:40) there was no frame of 120 ms. The perf lines give the in-round
residual: 0 - 8 frames over 33 ms per 10 s (16 in the first window after the load), the longest 35 - 63 ms, at 110 - 230
fps; the hook's own tick 0.7 - 0.9 ms a frame (slowest 5 - 13 ms). Those 40 - 60 ms frames are under the probe's
`HitchMs=50` gate (the probe polls every 5 ms and samples every 10 ms: a 50 ms frame gives at most one sample), so they
have no stack in this log: two single samples only, 13:54:41 KL2 0x5f7940 <- 0x440739 <- 0x8703ef <- 0x696fa3 <-
0x4cc1ce <- 0x85ebb0 <- 0x4552b, and 13:58:51 NtUserPeekMessage <- PeekMessageW. Not enough to say anything.

## 3. KL2 0x90e020 .. 0x90e8xx is zlib (1.1.3) inflating a zip member; 0x593010 is the archive member extractor

`0x90e020` is `inflate_fast` of zlib 1.1.x: 8-byte Huffman code entries `{op, bits, val}` (`movzx ebx, byte [esi+ecx*8]`),
the bit-mask table at `0xcd8218` = 0, 1, 3, 7, 0xf, 0x1f .., op bits 0x10 (literal/length) and 0x40 (end of block), and the
copy loop at `0x90e220` (`mov cl,[esi]; mov [edi],cl; inc edi`). `0x90d980` = inflate_codes (calls it at 0x90da22), `0x90ce10`
= inflate_blocks (calls that at 0x90d4e8), `0x90e500` = `inflate()` (state machine with "unknown compression method",
"invalid window size", "incorrect header check"; calls inflate_blocks at 0x90e61b). `0x90e400` = inflateInit2_, `0x90e3b0` =
inflateEnd. The exe holds a second zlib ("1.2.3" at 0xbdcba0, "inflate 1." at 0xbe3709 - the one re/loading.md 4 names);
the archive reader uses the 1.1.3 one ("1.1.3" at 0xb7940c).

`inflate()` has three callers: 0x4f00fe, 0x57758b and **0x5930ea in 0x593010**, the one on today's hitch stacks. 0x593010
(a method; `esi` = an archive entry object with +0x14 the member's offset in the archive and +0x18 its stream object;
args: the member's header record `h` at [ebp+8] with word h+4 = compression method and dword h+0xe = compressed size,
i.e. a local file header without its signature, dst at [ebp+0xc], size at [ebp+0x14]):

```
0x593023  _chkstk(0x20000)                       a 128 KB buffer on the stack
0x593032  method = word [h+4]
0x59303b  method == 0  -> 0x593120: stream->vtbl[0x14](dst, size, entry+0x14)   ONE read of the whole member; return dst
0x593043  method != 8  -> return 0                                                any other method: the member fails
0x593050  csize = dword [h+0xe]; inflateInit2_(&strm, -15 /* raw deflate */, "1.1.3", 0x38)
0x59307e  loop while csize > 0 and strm.msg == 0:
            n = min(csize, 0x20000)
            if stream->vtbl[0x20]() then next_in = stream->vtbl[0x24](&strm, n, pos)      (GUESS: a memory-backed stream)
            else stream->vtbl[0x14](buf, n, pos); next_in = buf                             (a file stream: read 128 KB)
            inflate(&strm, n < csize ? Z_SYNC_FLUSH(2) : Z_FINISH(4))
            0x48a1e0()                                                             the keep-alive: SetThreadExecutionState,
            csize -= n                                                             SteamAPI_RunCallbacks, 0x753150(.., 500)
0x593101  inflateEnd; return dst if Z_STREAM_END, or Z_BUF_ERROR with csize 0 and no bytes left; else 0
```

Callers of 0x593010: 0x4a57a2 (function 0x4a5600) and 0x79c869 (0x79c830) - not read further.

What this settles (by code, not run):
- **The reader takes a STORED member of any size**: method 0 is one plain stream read of `size` bytes with no size test
  and no special case. `re/loading.md` 4 ("whether the reader takes a LARGE stored member is not shown by any stock file")
  and the ASSUMPTION in `kl_graft.write_zip` are answered: `--load stored` cannot fail on the reader's side. Experiment E6
  is still worth its one run (the stream read of 300 MB, and whether the stored .prm's one heap block is sized by the
  stored = uncompressed size: `0x82049b` takes file size + 0x60000, the same number either way).
- **What `stored` saves**: a deflated map is inflated on the MAIN thread in 128 KB compressed chunks, ~1300 for a 164 MB
  DM01 archive, and after EVERY chunk the keep-alive 0x48a1e0 runs - the pump that re/loading.md 2 shows costing 1.2 - 1.5
  ms per call while the game is the foreground window (SetCursorPos + mouse_event + PeekMessage loop). 1300 x 1.2 ms is
  about 1.6 s of the load on top of the inflate work itself (0.6 - 1.3 s measured offline with a faster zlib). Stored:
  no chunks, no inflate, no per-chunk pump.
- Today's transition hitches (the 655 / 281 / 149 ms at the DM01 round start, 126 / 148 at DM01B, the 0x90e0ae samples in
  the menu returns) are this extractor at work on the main thread: zip members pulled while the scene is already
  ticking (the stock engine does the same with its own deflated archives; ours are larger).

## 4. Suggested next steps (nothing here was run; the owner / local sessions decide)

1. E6 as written in re/loading.md: `python tools/kl_graft.py ... --load stored` into the F01 test slot, one autotest.
   Expected: load time down (no inflate, ~1300 fewer keep-alive pumps), 298 MB on disk instead of 164. If the SSD
   read dominates instead, `level=1` stays.
2. For the in-round 40 - 60 ms frames: one owner round with `[KLHook] HitchMs=30` (the probe's gate; floor 20) so each
   gets 1 - 3 samples; the log then names their site the way it named the music-ON chain.
3. The hook's own 125 ms `ZAllyEscapeBox` scan at every round start (klhook `near:`) is one in-round hitch per round
   that is the hook's: cache the result per map / level load, or scan on the ticker thread.
4. The music-ON chain stays the 14:30 note's A/B (an MsgWaitForMultipleObjects + PeekMessage drain in the MCI worker
   threads). Today's numbers are the baseline for it: 20 - 32 hitches of 100 ms+ a minute with music ON, 1.5 with it OFF.
