# DM05A memory wall: kl2's heap path (static RE, 2026-10-25, workflow wo0qcwz51, 3 investigators + 3 adversarial verifiers)

Static disassembly of kl2.exe only, nothing run. "VERIFIED" = a second agent reproduced it by its own disassembly.

## VERIFIED
- 0x7bb33c = return address of `call [0xb1011c]` (HeapAlloc) at 0x7bb336 inside ZWin32Allocator::Alloc 0x7bb2c0
  (vtable 0xb8ed54 slot 2, RTTI .?AVZWin32Allocator@@). Object = static 0xdda7a8, owned by ZSysMem (vtable 0xb8e6a0, global ptr 0xdda7a0).
- Heap handle = GetProcessHeap() cached at [obj+0x10f8] by the ctor 0x407090 (0x4070f2 / 0x4070f8). kl2 imports NO HeapCreate,
  HeapReAlloc, HeapSetInformation, HeapCompact, HeapWalk. So every operator new / ZMalloc lands on the PROCESS heap.
- Request = ((n+0x1f)&~0xf)+0x10 (min 0x30), 16-aligned, 16-byte header {0x12345678, prev, next (list 0xe05578/0xe0557c), raw}; caller gets header+0x10.
- No NULL test after HeapAlloc: NULL -> 0x8e5ba0 writes 0x12345678 to [0] at 0x8e5bbd (= the known 0x8e5bbd crash). The caller's check at
  0x4aa06b can never fire (return is header+0x10). OOM hook slot 8 (0x429f30) is `xor al,al; ret`: no recovery in kl2.
  (The run survived 29 refusals because klmem SmallRescue answers refused requests < 1 MB from its reserve, klmem.c 213-230.)
- Chain: operator new 0x89e850 (2725 sites) -> 0x4a2fd0 -> ZSysMem::Alloc 0x4aa010 -> `call edx` 0x4aa065 -> 0x7bb2c0.
  Free: 0x6ad680 (4562 sites) -> 0x7f05f0 -> slot 3 0x882c30 -> header check 0x466590 -> HeapFree [obj+0x10f8].
- Small-block pool (<= 0x80 bytes, 16-byte classes, refill 0x7bdef0) runs only if byte [obj+0x10f4] (0xddb89c) != 0; its only writer is
  0x504a7e in 0x5048f0 (VirtualAlloc reserve N MB, retry at 3/4), whose only caller is thunk 0x449510, which NOTHING references.
  => statically the pool is DEAD and every small object pays >= 0x30 + NT header. Live byte at 0xddb89c not read yet (dump check).
- Sound Lock (ZSoundBufferOpenAL slot 29, 0x75db50): unchecked _aligned_malloc(size+0x10,16); every Unlock path (0x4fb1c0) frees it: not a leak.
- LAA / 4 GB for kl2's own heap is unsafe: PE flags 0x103, bit-31 pointer tags (see the 85 s LAA crash at kl2+0x1d69ba in the log).
- vmmap at the refusal: about 15 MB free VA below 2 GB in about 470 pieces, largest 0.059 MB (unreservable, 64 KB granularity); 35 x 15.81 MB heap
  segments + halving series.

## NOT verified (hypotheses)
- msvcr90 malloc/_aligned_malloc on a separate _crtheap (plausible VS2008 CRT behaviour, msvcr90 not disassembled).
- Which allocations grow in round 1 (particles / ZAllocMany / decals / shatter): no site disassembled; the ranking is a guess.
- The 97% heap occupancy and the 230-490 MB sawtooth source: inputs were not in the files.
- LFH being already on (likely on Win10, unlogged).

## Levers (ranked)
1. MEASURE first: a size histogram and caller histogram at 0x7bb336 (e8's K49B gross-by-caller plus a count of requests <= 0x80).
   If small blocks dominate the count, lever 2 is worth trying.
2. Revive the dead small-block pool: the hook calls 0x5048f0 (an existing kl2 function, no .text write) early. The free path tests the pool range,
   so mixed pool and heap blocks are tolerated by design (0x882c33). Costs N MB of reserve VA; saves >= 32 bytes per small object. UNTESTED,
   TEST build only, needs e8 (hook area).
3. ReserveMB trim: the 128 MB reserve is the SmallRescue buffer, not idle. Trimming it removes the cushion that turns refusals into survivals; do NOT.
4. HeapCompact/decommit: no VA gain (decommit keeps reservations). An IAT redirect to a bigger-reserve heap needs GetProcessHeap
   (120 sites), HeapFree (109) and HeapValidate (0x447cc1) routing; the allocator caches the handle at construction, so the wrap must precede ZSysMem's ctor.
