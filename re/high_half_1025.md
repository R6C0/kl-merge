# The high half: the 4 GB flag made safe (klhook/klhigh.c) — design, 2026-10-25

Static work of a scheduled check-in. NOTHING here was run in the game; klhigh.c was compiled with MinGW against a stub of
klhook.c's helpers (the MSVC build was not possible off the PC) and its bitmap carving passed a native self-test
(18 checks, `klhook/klhigh_bits_test.c`; the Windows test program `klhook/klhigh_test.c` is written but not run). Everything marked GUESS is a guess.

## The problem it answers

DM05A dies of **address space**, not memory: K48B..K48H (re/open_work_log.md, 2026-10-25) show free address space
falling from 1728 MB before the load to 16 MB in round 1 (largest piece 0.1 MB), the hook's SmallRescue then serves
hundreds of refused small requests, and the D3D driver finally asks outside every wrapped call and crashes
(K48C: nvd3dum.dll+0x170a69, read [0+4], round 2 start). The live log at 02:48 UTC today, DM05A again: modules 264 MB,
mapped 64, private committed 1363, private reserved only 340, 145 thread stacks 131 MB, free 16 MB. The stack shrinkers
(OtherStackKB, GameStackKB) buy about 300 MB once; the growth is the game's own run-time data plus the driver's, and
both share the same 2048 MB.

The large-address-aware flag gives a 32-bit process 4 GB on 64-bit Windows, and it was tried (01:40 today): crash after
85 s at kl2.exe+0x1d69ba. `debug/notes/2026-10-24-scheduled-triage-laa.md` read the dump: the engine marks a direct
pointer in a chunk reference by its TOP BIT (`test eax,eax ; jns <table> ; and eax,0x7fffffff`, 219 resolver sites and
418 chunk-table loads in kl2.exe). The first GAME heap block above 2 GB (0x82928030) was taken for a tagged pointer to
0x02928030. Verdict then: "LAA stays off for good."

That verdict is right for the game's memory and says nothing about anyone else's. The flag is poison only for a block
the GAME stores in a chunk reference, i.e. its own heap blocks. The driver (nvd3dum.dll), ReShade32.dll, the Steam
overlay allocate for themselves; what they hand the game are Lock() pointers to write through and COM interfaces to call
through, not pointers the game keeps in a chunk reference (GUESS - exactly what the measure run and the A/B below test).

## The mechanism (klhigh.c)

1. **Take the high half first.** kl2.exe imports dinput8.dll, so the hook's DllMain runs before any game code. With the
   flag on, klhigh.c reserves the whole upper 2 GB (0x80000000 .. 0xfffeffff) in chunks: 64 MB top-down until a probe
   comes back below 2 GB, then 32 .. 1 MB, 256 KB and 64 KB pieces for what is left (about 43 chunks; nothing committed,
   the addresses cost nothing). From then on the process looks to EVERYONE exactly as it did without the flag: no
   allocation of the game, of the process heap, of a thread stack or of a DLL can land above 2 GB, because nothing is
   free there. A census line first says what was already above 2 GB at that moment (expected: nothing; a 32-bit image's
   DLLs and its first heap sit low — to be confirmed live).
2. **Wrap the foreign modules' own import slots** (their IATs, not kl2.exe's) for VirtualAlloc / VirtualAllocEx /
   VirtualFree / VirtualFreeEx, matched by function name so an import from `api-ms-win-core-memory-l1-1-0.dll` counts.
   Modules already loaded are walked at init (ReShade32 loads as the d3d9 proxy before the hook; the Steam overlay too);
   the driver loads with the D3D device and is caught by `LdrRegisterDllNotification` (ntdll), with a 10 s re-scan of
   the module list as the fall-back. The caller is attributed by the wrapper's return address (an import slot is the
   module's own, so the return address lies in that module).
3. **Carve.** A fresh reservation (address 0, MEM_RESERVE, none of write-watch / large-page / physical / reset) from a
   module on `HighModules` is cut out of the chunks: first fit over 64 KB pages (VirtualAlloc's own granularity), inside
   ONE chunk (a commit may not span two reservations), committed there if MEM_COMMIT was asked. Its MEM_RELEASE through
   the same slot decommits the carved pages and frees the bits (the chunk stays ours). A MEM_COMMIT or MEM_DECOMMIT at
   an address inside a carved block passes straight to Windows (the pages are reserved: it accepts them). An explicit
   address, the odd flags, or full chunks pass through to the real call — into the low half as today — and are counted
   (`passed`, `spilled`).
4. **Measure first.** `[Memory] High=1` wraps and counts only, needs no flag and moves nothing: every 10 s a line gives,
   per listed module, reservations asked (MB) and held (MB). `HighCount=` lists modules counted but never placed
   (default d3d9.dll, dxgi.dll, d3d10.dll: d3d9's managed-pool system copies may be the biggest single item, but d3d9
   is the one module whose pointers the game touches most, so it is measured, not placed, until the numbers say).
   With High=2 the same line adds the chunk total, MB carved now, released, spilled, passed and bad releases.

What stays low either way (and so is NOT bought by this): the driver's small objects (HeapAlloc on its own heaps; heap
segments are grown by ntdll, not through the module's VirtualAlloc slot), every thread stack (the kernel places them),
every DLL image, and of course the game. What might move: texture staging, shader caches, command buffers, ReShade's
effect textures and render targets kept in system memory — the big VirtualAlloc blocks. How much that is on DM05A is
the measure run's single output number. If it is under ~150 MB the idea is cheap to drop.

## Risks, named

- A high pointer the game STORES in a chunk reference crashes as the LAA test did. Not expected from the listed modules;
  d3d9.dll is kept out of placement for that reason. Only a live run shows it.
- Signed compares on pointers in game code (`cmp ; jl`) see a high pointer as negative. Same class; same test.
- A module that VirtualQuery()s its own block gets OUR chunk as the allocation base and a region that may run into the
  neighbours. Rare; a driver sizing its block that way would misbehave (GUESS: none does).
- A release by a module other than the one that reserved (d3d9 freeing nvd3dum's block) goes to the real VirtualFree,
  fails, leaks the block above 2 GB — a leak that costs the game nothing. Counted (`bad release` counts only releases
  through OUR slots that name a non-start address).
- The flag must be set on kl2.exe on disk (the owner's one-byte header patch of 01:40, backup `kl2.exe.before-1025laa`,
  patched copy `kl2.exe.laa-test` still in the game folder). Steam's integrity hashes (klranges.h) did not object in the
  85 s LAA run; not re-verified. klhigh.c only READS the flag: High=2 without it falls back to High=1 and says so;
  High=1 WITH the flag logs a warning (the game may then get a high block — the 01:40 crash — so with the flag set,
  High=2 is the only safe setting; High=0 with the flag is the 01:40 configuration).
- Import slots of OTHER modules are written (page made writable for the write, protection restored). kl2.exe is not
  touched: no hashed range, no code byte anywhere. New for the hook (every wrapper so far sat in kl2.exe's own IAT).

## How to try it (Owner / e8, in this order)

1. Build the hook (klhook.c includes klhigh.c after klmem.c; `klvh_init` after `klm_init`, `klvh_tick` after
   `klm_tick`). Build and run `klhigh_test.c` once (`cl ... /link /LARGEADDRESSAWARE`): exit code 0.
2. **Measure run**, stock exe, `[Memory] High=1`, DM05A, the usual route: read the `high: every 10 s` lines at the
   menu, after the load and deep in round 1. Note nvd3dum's and ReShade32's held MB. Also note the
   `high: <module> ... NOTHING wrapped` line if it appears (the module allocates through another DLL or by ordinal;
   then the idea needs a different hook).
3. If the number is worth it (> ~150 MB): **A/B** with `kl2.exe.laa-test` as the exe and `High=2`, same map, same
   route, against the stock exe with High=0. Watch for the 0x1d69ba-class crash (tag) in the first minutes and for the
   free-address-space line (klmem's) staying high through round 1 and 2. Keep `d3d9.dll` out of HighModules on the
   first A/B. The exe swap is an owner action (stock file).
4. If the A/B holds: the flag becomes part of the install (one byte of kl2.exe; the restore .bat must know it), and
   `High=2` the shipped default WITH the flag check that it already has.

## Review (2026-10-25, third scheduled check-in; static, fixed in klhigh.c)

Four defects found by reading the wrappers against VirtualAlloc's documented contract, all fixed: (1) `VirtualAlloc(0, n,
MEM_COMMIT)` - the reserve+commit shortcut - was not a "reservation" to the wrapper, so it was neither counted (the
measure run would have under-reported every allocator using it) nor placed; (2) `VirtualFree(p, 0, MEM_DECOMMIT)` on a
carved block went to Windows with size 0 = "the whole region", whose base is OUR CHUNK: a block at a chunk's start would
have decommitted the whole chunk under its neighbours (now answered for the block, from the bit maps); (3) a listed
module reloaded at the same base kept an unwrapped IAT (the UNLOADED notification now forgets it); (4) the 48-chunk
limit could leave free pieces above 2 GB without a word (now 96 chunks and a post-takeover walk that WARNS on any free
piece). `klhigh_bits_test.c` 20 checks PASS (gcc); `klhigh_test.c` gained the three new cases, still NOT run on
Windows; the MSVC build and the measure run are the owner's step 1-2 above, unchanged.

## Alternatives considered and not built

- An inline hook on `ntdll!NtAllocateVirtualMemory` forcing ZeroBits=1 for everyone but our own wrappers: catches heap
  growth and stacks too, but patches code in a system DLL (new risk class, and anti-cheat-like) and still needs the
  caller attribution by stack scan. The reservation-first scheme makes it unnecessary: nothing can land high anyway.
- Pre-creating the foreign modules' heaps high (`RtlCreateHeap` with a base): a heap given a base cannot grow; dropped.
- Relocating DLL images above 2 GB: the loader places them; not reachable from a hook without re-mapping. 264 MB stay.
- `MEM_TOP_DOWN` alone for foreign allocations without the takeover: the game's heap would still wander high once the
  low half fills — the 01:40 crash, delayed. The takeover is what makes the flag safe.
