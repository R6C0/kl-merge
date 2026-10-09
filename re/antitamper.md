# kl2.exe anti-tamper: what ends a real Arcade / Fragile Alliance round, and where a hook may sit

Offline work, 2026-10-09 (agent f-tamper). Nothing here was run in the game. kl2.exe sha1
9d99e01d..., TimeDateStamp 0x4c80f728, base 0x400000, read with `debug\dasm.py` / capstone.
Tool: `<work>\research\agent_scripts\f-tamper\ceg_ranges.py` (builds `sites.json`, `union.json`;
`ceg_ranges.py <hex addr>[:len] ...` lists the checks that hash an address).

Purpose: keep the owner's own mod working with their own copy. This file describes the boundary and
designs that stay outside it. It is not a way round the protection, and none is wanted: the rule
that follows from it is "never change a byte that is hashed".

## 0. Result in short

1. The exit is **Valve CEG's code-integrity check, compiled into the game** (not SteamStub, not a
   thread, not a timer). CEG is inlined in several hundred places of game code. Each place hashes
   fixed address ranges of the kl2.exe image in memory and compares with constants in `.rdata`.
2. On a mismatch a small routine **overwrites a return address on the stack** with the address of
   an exit stub. That is why `0x794e80` "has no caller". The stub wipes the stack to the top of
   the page and calls `ExitProcess(0x8000dead)` through the import table.
3. Hashed: **84.9 % of `.text`** (all of it except the 4 KB pages that hold CEG's own code),
   **65.9 % of `.rdata`** (vtables, strings, CEG's tables), the 4-byte `.version` section.
   **Not hashed: the import address table, `.data` / `.bss`, the heap, anything outside the image.**
4. Of klauto's patches **ten lie in hashed bytes** (eight detours, the scene-load vtable entry, the
   `[Engine]` push operand); five detours and all import-slot wrappers do not. Any one of the ten
   is enough to explain runs RN1, RN3, RN4.
5. Design rule for anything that must survive a real session: **import-table wrappers and data
   writes only** (plus the proxy DLL itself). klslot's file redirect (five import slots) is
   predicted safe as it is; its `[Slots]` push-operand patch is not (hashed) and has a data-only
   replacement (section 5).
6. Steam's "probe" at 0xa8e3cb is a separate thing: a deliberate fault whose SEH handler looks at
   the **debug registers** of the faulting thread. Hardware breakpoints are not usable as hooks.

Standing: 1-3 and 6 are read off the disassembly and partly proved by recomputation (section 2.4).
4-5 are predictions from the range map; the experiments in section 7 confirm or refute each with one
run.

## 1. How 0x794e80 is reached

### 1.1 The exit stubs
Ten stubs: 0x457680 0x5bc180 0x694da0 0x794e80 0x863be0 0x8c68f0 0x8f99e0 (optimised shape) and
0x56cd20 0x722d90 0x888120 (frame-pointer shape). All seven of the first kind were decoded:

    0x794e80  zero [esp+4 .. (esp+0x1004) & ~0xfff)      ; the caller's stack up to the page end
              sub esp,0x800 ; zero those 0x800 bytes
              edx = [0xb42c1c] ^ [0xb685e0]              ; = 0x8000dead
              ecx = [0xb42c1c + [0xb46648]]              ; = [0xb1018c] = KERNEL32.ExitProcess (IAT)
              push edx ; call ecx

The "XOR-ed pointer" is two things: the exit code is XOR-ed from two `.rdata` constants, and the
function pointer is read from the import slot of ExitProcess through a self-relative offset. Both
are link-time constants; there is no run-time key and nobody "installs" the pointer. Because the
call goes through the import slot, an ExitProcess import wrapper sees it (run RN4 did).
In RN4 esp was 0x01b4ea38 at the call, so the stub was entered within the last page of the main
thread's stack and the wipe reached the stack base: no caller survives. That is by design.

### 1.2 The redirect
Ten small functions (0x6a8390 0x5510e0 0x513b20 0x5a8fe0 0x6f3a00 0x78cc00 0x57cf20 0x7f4280 and two
more, one per stub), **336 call sites**. `0x6a8390(char skip, int n, void *frame...)`:

    skip != 0  -> return
    n <= 0     -> [own return address] = stub        (lea edx,[esp+8] / mov [edx-4],ecx)
    n == 1     -> [frame1 - 4]         = stub        (the return address of an outer function)
    n  > 1     -> [frame(GetTickCount() % (n-1)) - 4] = stub

The stub address is `0xb849ec + [0xb849ec]` (self-relative, no absolute pointer to a stub exists in
the image). So the stub runs when the chosen function *returns*: immediately for n <= 0, later for
the others. No table, timer or thread is involved; it runs on whichever thread executed the check
(RN4: the main thread).

### 1.3 The check that calls the redirect
Shape, here the one inside 0x45d600 / 0x879fd0 (others are copies with other constants):

    crc = 0xffffffff
    [15 of the 21 thunk resolvers: crc over 16 bytes produced by a helper first - see 2.3]
    for i in 0..N-1:  crc = crc32(crc, image[start[i] .. +len[i]])      ; 0x6633d0 -> 0x7890e0
    crc = crc32(crc, rva of the resolver's return address)              ; resolvers only
    crc = ~crc                                                          ; 0x4e5a20
    md5 = MD5(crc (4 bytes) + image[start2 .. +len2])                   ; 0x879fd0: 0xa8ef50/80, 0xa8f040
    if md5 != 16 bytes at 0xb7e4b4:  redirect(0, 0)                     ; 0x5325b0 compare, 0x6a8390

`start[i]` = `&T1[i] + T1[i]` (self-relative table in `.rdata`), `len[i]` = `T2[i]`; two more
tables hold a relocation block and its size (all zero in this exe: no relocations, the "undo the
relocations" path of the hash routine, taken when the image is not at 0x400000, is never used).
The CRC is the standard reflected CRC-32 (table built at 0x6e1520 into 0x1692898), the second hash
is plain MD5. The hash routine exists in **735 copies** (prologue `sub esp,K / mov eax,[esp+K+8] /
mov ecx,eax / sub ecx,[esp+K+0x1c]`), called from **594 places**.

Four flavours of site:
- **Address from the CRC** (90 places end in `lea eax,[esi+ebx]`; 21 of them are reached through a
  thunk `push ecx / mov eax,<resolver> / call eax / pop ecx / jmp eax`, e.g. 0x8af460 -> 0x45d600):
  the finished CRC *is* the address of the protected function (the five spare bytes after each
  thunk's `jmp eax` are what forces the value). The MD5 comparison follows, so a changed byte gives
  the clean exit and not a wild jump.
- **Self-check returning bool** inside ordinary functions (CRC loop, MD5, compare, redirect), e.g.
  0x5acc50..0x5ace4f with 73 ranges.
- **verify(seed, image, &start, len, &reloc, size, base)** helpers of 0x88 bytes (0x879fd0, 0x5acbc0,
  0x4064d0 ...), called by the two kinds above.
- **Variadic verify** (0x41dd10, 0x466960, 0x69cc70 ...: count, then start / len / reloc / size per
  range, a limit of 1,000,000 and a 0x208-byte output), used by the machine-binding functions of
  section 6.

### 1.4 When
Whenever game code passes one of those places. Nothing periodic was found: kl2.exe imports no
timer, timer-queue, APC or thread-pool function (import table read), and a check needs no thread
of its own. NOT SEARCHED: whether one of the seven CreateThread entry functions contains a site. Which places run is decided by what the game
does. A direct boot runs e.g. thunk 0x8af460 (save writer 0x65a4d0, called from the ZFFGameData
update at 0x4bcb83 / 0x4bccd5): its 23 ranges and its MD5 range contain none of klauto's sites, which
fits "a direct boot never trips it". A real session runs code a direct boot never enters: the online
service (`ZOnlineServiceWintel` slot 40 = thunk 0x790060 -> CreateSession 0x8e4fe0, slot 45 = thunk
0x605cb0 -> 0x6d8640), the session-only parts of the rules and player code.
NOT ESTABLISHED: which single check fired 30-90 ms after the load in RN1/RN3/RN4. It does not need to
be known for the design rule; the exit times of X4-X6 narrow it if wanted.

## 2. What is checked

### 2.1 Coverage (ceg_ranges.py: 626 range sets read at 594 call sites)

| section | range | hashed |
|---|---|---|
| `.text` | 0x401000-0xb0fe30 | 6,282,124 of 7,401,008 bytes = **84.9 %** |
| `.rdata` | 0xb10000-0xcd6a0a | 1,227,776 of 1,862,154 = **65.9 %**: 0xb11000-0xb8ac00, 0xb8b000-0xbeb000, 0xc7a000-0xccc000 |
| `.data` (+ `.bss`) | 0xcd7000-0x1692e5c | **0** |
| `.tls`, `.rsrc` | | 0 |
| `.version` | 0x1694000 | all 4 bytes (two checks, 0x200 each) |

- Ranges are 0x800-aligned blocks of 0x1000-0x4000 bytes; every hashed byte is covered by several
  independent checks (typically 8-12).
- The **221 unhashed stretches of `.text`** (appendix A) are exactly the 4 KB pages that contain
  CEG's own code (resolvers, hash copies, thunks, exit stubs' neighbours). They are unhashed because
  CEG cannot hash the pages it personalises, not because they are unimportant; game functions that
  happen to share such a page are unhashed by luck.
- Unhashed `.rdata`: **0xb10000-0xb11000 (the import address table, 0xb10000-0xb107f8)**,
  0xb8ac00-0xb8b000, 0xbeb000-0xc7a000, 0xccc000-end (import directory 0xcccc54 and the import names).
- All ranges lie inside the kl2.exe image (every start is self-relative). kl2.exe imports no
  VirtualQuery, ReadProcessMemory, Toolhelp or GetThreadContext; it never reads another module's code.
- The PE headers are not referenced by any range read.

### 2.2 Not read
52 `verify(...)` helpers (list printed by ceg_ranges.py: 0x4050a0, 0x405860, 0x4069f0 ...) have no
direct call and no pointer in the image. Either dead copies or reached only through a CRC-computed
address; their ranges come from a caller that could not be found. So "not hashed" below means "not
in any of the 626 range sets read". Experiment X3 tests the one place where the project leans on it.

### 2.3 CEG's or the game's?
CEG's. Evidence: the RTTI names `CEG_ForceRefClass_*`, the strings `STEAM_DRM_IPC` / `.STEAMSTART`
(re\netcode.md), the thunk/resolver template, and the machine binding: 15 of the 21 thunk resolvers
first hash 16 bytes produced by a helper (0x7d7ad0, 0x6dc400 ...), so their target address cannot be
computed from the file alone. The machine-bound part was deliberately not followed further.
The six that are not machine-bound were recomputed (2.4). The game's own code contributes only the
places where the developers put the checks.

### 2.4 Proof of the model (pure reading of the file)
For the six resolvers without the machine step the CRC and MD5 were recomputed in Python from the
exe on disk: every MD5 equals the stored digest, and every CRC is a function start.

| thunk | resolver | ranges | CRC = target | digest at |
|---|---|---|---|---|
| 0x8af460 | 0x45d600 | 23 | 0x65a4d0 (the save writer found earlier from a crash stack) | 0xb7e4b4 |
| 0x790060 | 0x8163c0 | 42 | 0x8e4fe0 (CreateSession, re\netcode.md) | 0xb54028 |
| 0x605cb0 | 0x61ffd0 | 43 | 0x6d8640 | 0xb5a210 |
| 0x4ef090 | 0x7ced90 | 40 | 0x6fc430 | 0xb62910 |
| 0x5de290 | 0x7c4fe0 | 41 | 0x4b3bd0 | 0xb62400 |
| 0x682d90 | 0x48ceb0 | 24 | 0x5cd220 | 0xb65cdc |

Range list of 0x45d600 as an example: 21 code blocks (0x43b400+0xc00 ... 0x788800+0x1000), its own
thunk 0x8af460+0x10, and `.rdata` 0xb21c00+0x39c8; MD5 range 0x6c2000+0x1800.

## 3. klauto's and klslot's patches against the map

| patch | address | hashed by | |
|---|---|---|---|
| NODE detour | 0x46fe96 | - | page 0x46e000 holds thunk 0x46f9a0 |
| CTRL detour | 0x46ffbf | - | same page |
| PROG detour | 0x53ac90 | 12 checks | **inside** |
| GEOMS detour | 0x8ad7c0 | 8 | **inside** |
| SCNBLK detour | 0x862780 | - | page 0x862000-0x8639d0 |
| REFFIX detour | 0x6204b0 | - | 0x61e000-0x621000 |
| ROOM detour | 0x48e910 | 10 | **inside** |
| GBUF detour | 0x9262b0 | 8 | **inside** |
| REFEND detour | 0x8d1210 | 8 | **inside** |
| POST detour | 0x5acc50 | 10 | **inside** |
| GINIT detour | 0x7f3b80 | - | 0x7f3000-0x7f4000 |
| CLIST detour | 0x80d800 | 8 | **inside** |
| CINIT detour | 0x4eec50 | 11 | **inside** |
| scene-load vtable entry | 0xb8fa24 (`.rdata`) | 8 | **inside**: vtables are hashed |
| `[Engine]` push operand | 0x5987af | 8 | **inside** (the baked ini text 0xb55dc0 too) |
| import slots ExitProcess / exit / PostQuitMessage / DestroyWindow / DirectInput8Create | 0xb1018c 0xb103d0 0xb105a8 0xb10640 0xb10034 | - | IAT: outside |
| klslot: CreateFileA / CreateFileW / GetFileAttributesA / FindFirstFileA / fopen slots | 0xb10270 0xb10204 0xb10260 0xb1006c ... | - | IAT: outside |
| klslot `[Slots]`: nine `push <slot name>` operands | 0x836016 ... 0x8360ab | 8 each | **inside** |
| klslot `[Slots]`: session default name | 0x69981e | 11 | **inside** |
| klslot `[Slots]`: the stock name strings | 0xb75044 ... | 2 | **inside** (do not edit in place) |
| klslot `[Slots]`: DLC lock bytes | 0x8468ea-0x8468f5 | - | page 0x846000 |
| klslot MountFirst detour | 0x7f5610 | - | 0x7f5000-0x7f7000 |
| hero index store / read (re\menus.md 7.4) | 0x835837 / 0x8f5ebd | 8 / 8 | **inside** |
| netcode globals | 0xd35420.. (`.data`) | - | outside |
| FA slot name table | `[0x168f750]+0x16+idx*0x40` (heap) | - | outside |
| menu option object | `[0x154d5f4]` (heap) | - | outside |

So the questions of the brief:
- **Data writes are safe**: `.data`, `.bss` and the heap are in no range.
- **Vtables in `.rdata` are checked** (0xb8b000-0xbeb000 completely).
- **The import address table is not checked.**
- **Detours in unhashed pages** are outside the ranges read (subject to 2.2). Do not build on that
  for anything shipped: it is 15 % of the code, chosen by CEG's layout, and unverified live.

## 4. What a hook may and may not do

May (outside every range read):
1. Be loaded as the dinput8 proxy, run its own threads, wrap COM interfaces it hands to the game
   (the scripted keyboard), read any memory, call game functions. Shown live by RN5 / RN6.
2. Replace **import address table** entries of kl2.exe (0xb10000-0xb107f8).
3. Write **data**: `.data` / `.bss` globals, heap objects, the in-memory command line (CmdAdd, RN5).
4. Give one **object** a private vtable: copy the class's vtable (with the RTTI locator dword in
   front) into our own memory, change the slot, store the copy's address in the object's first
   dword. The object is data; the stock vtable in `.rdata` stays byte-identical.
   ASSUMPTION (not run): nothing compares an object's vtable pointer with the stock address. The
   engine's class tests go through RTTI / class-info virtuals, which the copy keeps.
5. Supply files: an archive the game mounts itself, or a path changed in an import wrapper.
6. Keep a vectored exception handler (klhook has one in every run, including RN5 / RN6).

May not, in a build that has to live through a session:
1. Change any byte of the hashed 84.9 % of `.text` (detours, operand patches, nop-outs).
2. Change hashed `.rdata`: vtable entries, the engine's strings, the baked ini text.
3. Use hardware breakpoints on a thread that raises the probe (section 6).
4. Patch-and-restore around a check. Not wanted, and not workable either: checks run inline at
   several hundred places with no common entry.

Test builds for **direct-boot** runs may keep all thirteen detours: no check that covers them is
reached there (every DB run so far). The rule only binds runs that enter a session.

Tripwire worth keeping: an ExitProcess import wrapper that logs `code == 0x8000dead` as
"integrity exit" and then lets the exit happen. It turns every future violation into one clear
log line instead of a silent end. It must not swallow the exit.

## 5. Clean designs for what the project needs

### 5.1 File redirect for a map in its own folder (klslot.c section 1)
The five import wrappers are outside the check. Keep them. Hooking the same functions **inside
kernel32** (patching kernel32's code) is also outside it - kl2.exe hashes nothing but its own
image - but it gains nothing over the import slots (every file open of the exe leaves through them,
re\slot_redirect.md) and it would also redirect opens made by Steam's DLLs and the overlay in the
process. Not recommended.
An archive the game mounts itself is the cleanest of all for menu text and pictures: Patch01.zip is
mounted first and overrides same-named members, so `Overlay\Patch01.zip` through the CreateFileA
wrapper needs no engine address at all.

### 5.2 A level under a new name (klslot `[Slots]`)
Today: nine push operands at 0x836016.. (hashed) + 0x69981e (hashed) + lock bytes. Replace by data:
- The constructor 0x835ff0 puts the nine names into the level list (rea_slots.md); they live on the heap
  at `[0x168f750] + 0x16 + idx*0x40` (0x40 bytes each). **Write the name there** once the pointer
  at 0x168f750 is non-null. The hook already runs on the game's thread at every keyboard poll, so
  "poll until the list exists, then write once" needs no code hook.
  NOT ESTABLISHED: whether something re-runs the constructor or copies the name elsewhere before
  the poll sees it (the session default at 0x69981e is a second literal: find the object it is
  stored into and write that copy as well, or use `-o MPMap=` through CmdAdd).
- The lock: the availability bytes are `[list + 4 + idx]`, reset by slot 32 (0x8468d0). Write the
  byte in the object after each reset (poll), instead of changing the `mov byte ptr [esi+4+idx],0`.
- Simplest of all, and already supported: keep the stock slot name and redirect the *folder* in the
  file wrapper (`[Redirect] F01=DM03`). No name, no lock, no code.

### 5.3 MountFirst (0x7f5610)
In an unhashed page, so outside the ranges read, but it is a code patch that only luck protects.
Use `Overlay\Patch01.zip` through the file wrapper instead (same effect, data only).

### 5.4 Hero index (re\menus.md 7.4)
0x835837 and 0x8f5ebd are hashed. The value is a byte in a heap object: `[rules + 0x33d]`, written
once by the ZGameRulesHeist constructor and read by slot 137 (0x8f5e90). Write the byte in the
object from the keyboard-poll hook as soon as the rules object exists.
NOT ESTABLISHED: whether slot 137 can run in the same frame as the constructor, before the first
poll. If it does, give the rules object a private vtable (4. above) whose slot 137 sets the byte
and then calls the stock function; that needs a point where the object already exists but slot 137
has not run, which the same poll gives only if the order allows it. Experiment X8 decides.

### 5.5 Engine keys
`[Auto] CmdAdd` (the in-memory command line). Never `[Engine]` in a session run: its operand
0x5987af and the text 0xb55dc0 are hashed.

### 5.6 Logging in a session
- Scene-load start / end and loading progress: both are virtuals of the one ZEngineDataBase object
  (vtable 0xb8fa04: slot 3 = 0x53ac90 progress, slot 8 = 0x820300 load). Give that object a private
  vtable with the two slots wrapped. No image byte changes. (Today's patch of the entry 0xb8fa24 in
  place is hashed.)
- Per-node breadcrumbs (NODE, CTRL) have no data-only equivalent; keep them for direct-boot runs.
  A level that loads by direct boot loads the same way in a session.
- Exit diagnostics, file opens, faults: import wrappers and the VEH, as now.

## 6. The "probe" at 0xa8e3cb and hardware breakpoints

    0xa8e3c0  mov ecx,[esp+8] ; mov edi,[esp+0xc] ; xor eax,eax ; mov [eax],ecx ; ret

A deliberate write to address 0, called from 30 places. Each sits at the end of a machine-binding
function (e.g. 0x45ba20): variadic verify of three code ranges, then `HKLM\Software\Valve\Steam`
`InstallPath` is read (0xa8e3d0), that path is opened with CreateFileW, GetFileInformationByHandle,
eight bytes of the result are hashed and compared with a stored value (0xb57038); then, when the
caller passed 1, the fault is raised. ASSUMPTION: it is raised on the "matches" branch, because it
is raised on this machine at every scene load and the game goes on.

Sixteen wrappers (0xb0f7d0 ... 0xb0fb90) call such a function inside an SEH frame whose handler is
**0xb0fd20**:

    ctx = ContextRecord
    if (ctx.ContextFlags & 0x10010) == 0x10010 and (byte)ctx.Dr7 != 0:      ; a hardware breakpoint is enabled
        next outer SEH record: handler = 0xb0f648, data = 0xb0fce0           ; a chain that ends in address 0
    elif code == 0xc0000005:  ctx.Eax = 0xd49f2c ; continue execution        ; the write is redone into scratch
    elif code == 0xe06d7363:  continue execution
    ctx.ContextFlags |= 0x10010 ; ctx.Dr0..Dr3 = 0 ; ctx.Dr7 = 0             ; in every case

So the probe checks exactly one thing: **the low byte of DR7 of the thread that faults** (any of
the four breakpoints enabled, local or global). If set, it sabotages the SEH chain - run RN2's
"stack overflow / jump to 0". If not, it resumes, and it **clears DR0-DR3 and DR7 of that thread**
on the way, so a breakpoint armed earlier with DR7's enable bits off would be wiped anyway.
kl2.exe has no other debugger test on this path (IsDebuggerPresent is referenced once, in the /GS
failure code 0xa8df52).

Consequences:
- Hardware breakpoints are not a hook mechanism for this game: an execution breakpoint has to sit
  on the main thread, which raises the probe at every scene load.
- As a one-off *diagnostic* they work between two probes (RN3: armed after the load began, no
  harm), and they are gone after the next one.
- A vectored handler is fine as such; ours must keep passing 0xa8e3cb on untouched
  (klauto does: `EXCEPTION_CONTINUE_SEARCH`). It must not edit the context it is shown there.
- Guard pages on code (PAGE_GUARD as a "patch-free hook") are not an option either: every hash
  routine reads the code pages as data, several hundred times.

## 7. Satisfy instead of avoid?
No. A check compares live bytes with constants: the CRC is the call target, the MD5 digest sits in
`.rdata`, and those tables are themselves inside other checks' ranges. Making a changed byte pass
would mean rewriting CEG's tables or keeping two views of the code, i.e. defeating the protection.
Out of scope, and unnecessary: everything in section 5 has a design that changes no hashed byte.

## 8. Cheap experiments for the live agent (one variable per run)

Base for all: the RN6 configuration (klauto, `Hooks=0`, no `[Engine]`, CmdAdd, the menu route into an
Arcade round, slot F01 as installed). Result to read: round starts (`HEIST STARTS`) or
`END ExitProcess(2147540653)`. Keep the ExitProcess wrapper in every run as the tripwire.

| run | the one change | predicted | confirms |
|---|---|---|---|
| X1 | + klslot's five file-import wrappers (`[Expansion] Enable=1`, `[Redirect] F01=<map>`, no `[Slots]`, no MountFirst) and klauto's exit-import wrappers | round starts | the IAT is not checked; klslot section 1 is session-safe |
| X2 | + data writes only: rewrite the F01 entry of the slot table `[0x168f750]+0x16` with its own text, write one netcode global (0xd35420) back with its own value | round starts | data is not checked |
| X3 | + ONLY the five detours in unhashed pages (NODE, CTRL, SCNBLK, REFFIX, GINIT) | round starts | the page map, and that the 52 unread helpers do not cover them. An exit here means "no code patch anywhere" |
| X4 | + ONLY the vtable entry 0xb8fa24 | exit 0x8000dead | `.rdata` vtables are hashed |
| X5 | + ONLY the PROG detour (0x53ac90) | exit | hashed `.text` trips it; note ms between load end and exit |
| X6 | + ONLY the `[Engine]` operand (0x5987af) | exit | same for an operand patch; with X4 / X5 the three exit times show whether one check or several fire |
| X7 | + private vtable on the ZEngineDataBase object (slots 3 and 8 wrapped), nothing else | round starts, load start / end logged | 5.6, and the ASSUMPTION of 4. item 4 |
| X8 | + poll-write of `[rules+0x33d]` (log the frame the rules object first appears and whether the round's hero is the written one) | round starts with the chosen hero | 5.4 timing |
| X9 | direct boot with X4's patch only | clean run | checks covering 0xb8fa24 are session-only (already implied by every DB run) |

X1-X3 and X7 are the ones the project needs; X4-X6 are controls (if one of them does NOT exit, the
range map is wrong for that class and this file must be corrected before anything relies on it).
No experiment arms a debug register.

## Appendix A. `.text` stretches in no range read (221, 1,118,884 bytes)

    401000-402000 413000-414000 418000-419000 41a000-41b000 41d000-41e000 42a000-42b000 42f000-430000
    433000-435000 43c000-43d000 440000-440280 440290-441000 443000-444000 445000-446000 44e000-44f000
    456000-458000 45d000-45e000 461000-4622c0 4622d0-463000 465000-466000 46b000-46c000 46e000-46f9a0
    46f9b0-470000 471000-472000 47e000-47f000 480000-481000 484000-485000 489000-48b000 48c510-48d000
    490000-491000 496000-499000 49d000-49e000 4a6000-4a8000 4ab000-4ac000 4b5000-4b6000 4bd000-4be000
    4c1000-4c2000 4c3000-4c5000 4ca000-4cd000 4cf000-4cf870 4cf880-4d0000 4d1000-4d5000 4da000-4db000
    4dd000-4de000 4e5000-4e6000 4ef000-4ef090 4ef0a0-4f0000 4f6000-4f7000 4fe000-4ff000 507000-508000
    509000-50a000 513000-513b14 514000-516000 517000-51a000 51b000-51b300 51b310-51c000 520000-521000
    530000-532000 535000-536000 539000-53a000 53c000-53d000 54c000-54e000 554000-556000 55a000-55d000
    55e000-55f000 560000-561000 564000-565000 568000-56a000 56b000-56d000 575000-575410 575420-576000
    57c000-57c400 57cf80-57e000 57f000-580000 583000-584000 591000-592000 596000-597000 59b000-59f000
    5a9000-5aa000 5bb000-5bd000 5be000-5bf000 5c2000-5c3000 5c6000-5c7000 5ce000-5d0000 5db000-5dc000
    5de000-5de290 5de2a0-5df000 5e1000-5e2000 5e3000-5e4000 5ec000-5ed000 5f0000-5f3000 5f7000-5f8000
    5f9000-5fc000 5fd000-5fe000 5ff000-5ff9d0 5ff9e0-600000 605000-605cb0 605cc0-606000 60c000-60e000
    619000-61c000 61e000-621000 63b000-63c000 644000-645000 648000-649000 64b000-64c000 655000-656000
    659000-65b000 664000-665000 666000-669000 66a000-66e000 671000-673000 67b000-67c000 67d000-67f000
    682000-682d90 682da0-684000 685000-689000 68d000-68e000 694000-695000 696000-697000 6a6000-6a7000
    6ac000-6ad000 6b5000-6b6000 6b8000-6b9000 6c1000-6c2000 6c6000-6c8000 6ca000-6cc000 6d2000-6d3000
    6d7000-6d8000 6da000-6db000 6de000-6df000 6e0000-6e3000 6e7000-6e8000 6f9000-6fa000 705000-706000
    70a000-70b000 715000-716000 71d000-720000 723000-724000 739000-739f60 739f70-73a000 74a000-74b000
    74c000-74d000 74e000-74f000 75b000-75c000 762000-764000 76c000-771000 778000-779000 77a000-77b000
    783000-783280 783290-784000 787000-788000 78a000-78c000 790000-790060 790070-791000 798000-7988b0
    7988c0-79a000 79e000-7a0000 7a6000-7a7000 7a8000-7a9000 7ad000-7ae000 7b9000-7ba000 7c4000-7c6000
    7ce000-7cf000 7d0000-7d1000 7dd000-7de000 7e8000-7e9000 7ea000-7eb000 7f1000-7f2000 7f3000-7f4000
    7f5000-7f7000 7f8000-7f9000 800000-801000 803000-804000 814000-817000 81a000-81b000 821000-822000
    82c000-82d000 831000-832000 838000-839000 83b000-83c000 83f000-840000 844000-845000 846000-847000
    84d000-84d100 84d110-84e000 856000-857000 85d000-85e000 862000-8639d0 8639e0-864000 865000-866000
    869000-86b000 86c000-86e000 872000-873000 87a000-87b000 87d000-87e000 880000-881000 893000-894000
    89d000-89e000 8a8000-8a9000 8ac000-8ad000 8af000-8af460 8af470-8b0000 8be000-8bf000 8c1000-8c3000
    8c6000-8c7000 8cc000-8cd000 8cf000-8d0000 8d2000-8d3000 8d7000-8d8000 8d9000-8db000 8e1000-8e17b0
    8e17c0-8e2000 8e3000-8e4000 8eb000-8ec000 8ed000-8ee000 8f2000-8f3000 8f66a0-8f7000 8f8000-8f9000
    8fc000-8fc950 8fc960-8fd000 8fe000-900000 906000-907000

(0x907000-0xb0fe30, the statically linked libraries, is hashed throughout. Where a stretch is split
by 16 bytes, e.g. 0x440000-0x440280 / 0x440290-0x441000, the 16 bytes are a CEG thunk: it is hashed,
by its own resolver and one more check, while the rest of its page is not.)

## Appendix B. How the map was made, and its limits
`ceg_ranges.py` finds the 735 hash-routine copies by prologue, every `call` of one (594), and reads
the range arguments from the instructions before the call: 284 table loops, 142 single ranges, 90
through a `verify()` helper's caller, 110 through a variadic helper's caller (descriptor block: n
self-relative starts at X, n lengths at X + 4*(n+1), read off 0x5414a0-0x541501). Checked by
recomputing six digests (2.4). Limits: the 52 unreferenced helpers (2.2); the variadic block layout
is read off one call site and applied to all; a hash routine with a prologue the pattern misses
would be invisible (two shapes are matched: `sub esp,K` and `mov eax,K / call __chkstk`).
