# 2026-10-23 start-up stall (KLHook_stall.dmp, run of 09:51:47, killed 10:01:50)

Read-only triage of the watchdog dump (74 threads, 137 modules, no exception record) with debug/dump.py.

## 1. What the main thread (59060) is doing

- `ntdll+0x7373c` is the `ret 0x2c` of the stub `mov eax,0x55 ; call Wow64SystemServiceCall` =
  **NtCreateFile** (11 args; neighbours fit: 0x33 NtOpenFile ret 0x18, 0x34 NtDelayExecution ret 8,
  0x04 NtWaitForSingleObject ret 0xc). Not a wait, not a named-object open.
- Its arguments are intact at esp 01b4ef50: FileHandle slot still 0, DesiredAccess 0x00110081
  (FILE_READ_DATA | FILE_READ_ATTRIBUTES | **DELETE** | SYNCHRONIZE), OBJECT_ATTRIBUTES 01b4efe0 with
  Attributes 0, ObjectName = **`\??\C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KL2.exe`**,
  share 7, FILE_OPEN, FileAttributes 0x7fa7, CreateOptions 0x0064580e (DELETE_ON_CLOSE, OPEN_REPARSE_POINT,
  NO_RECALL, BACKUP_INTENT, NO_INTERMEDIATE_BUFFERING, overlapped) = KERNELBASE's translation of
  `CreateFileA(exe, 0x81, 7, 0, OPEN_EXISTING, dwFlagsAndAttributes = 0xFFFFFFFF, 0)`.
- The game is opening ITS OWN EXE and the open has not returned (handle slot 0; the context sits at the
  stub's `ret`, where WOW64 parks a thread blocked in a system call).
- eax = 0xc0000034: GUESS, consistent. A blocked WOW64 thread's 32-bit context keeps the status of the
  LAST system call that returned (sleeping workers show stale junk in eax, never a syscall number). The
  call right before this open is the hook's `kls_isfile("...\KLExpansion\Overlay\KL2.exe")`
  (NtQueryAttributesFile; the ASCII path is in the wrapper's frame at 01b4f0b4); the file does not exist
  -> STATUS_OBJECT_NAME_NOT_FOUND. The "not found" is the overlay miss, not the exe.

## 2. Who asked: the CEG probes in the main loop

Live chain (dinput8.dll @50d30000 is the hook; the system one is @752d0000):
`NtCreateFile < KERNELBASE+0x110b8b/0x11068e/0x10d661 (CreateFileA->W) < dinput8+0x8da78 (kls_CreateFileA
forwarding) < kl2 0xb0f4e6 < 0xb0fdc0 < 0x87a93b < 0x584073 < 0x7549bf < 0x926aa6 < 0x8016ca < 0x4c36af
< 0x476d35 (WinMain)`. 0xb0f4be / 0xb0fc16 / 0xb0f6a4 are stale returns of the probe's SEH dance.

- **0xb0f4a0** (only caller: wrapper **0xb0fda0**, only called at **0x87a936 = first instruction of the
  main-loop step 0x87a930**): 0x7bf680 (a .data pointer) -> 0xb0f710 (GetModuleHandleExA(6, 0xb0f650) +
  GetModuleFileNameA = the exe's path, then 0xb0f650: SEH frame, handler 0xb0fc80, GetProcessTimes,
  0xb0fbd0 = **RaiseException**; the handler flags the record 0x10010 and continues). Then
  **CreateFileA(exe path, 0x81, share 7, OPEN_EXISTING, flags -1)**; if the handle is valid:
  GetFileTime + InterlockedIncrement [0xdd2608], CloseHandle.
- **0xb0f520** is the twin (0x4e19b0, callback 0xb0f770, counter [0xdd25d8]); only caller **0xb0fdd0**,
  only called at **0x583fb3 = first instruction of ZSysInterfaceWintel slot 47, the per-frame update**.
- So 0xb0f4a0..0xb0fdff is the CEG runtime (same shape as the sixteen 0xb0f7d0.. wrappers in
  re/antitamper.md), and **every frame opens kl2.exe twice with DELETE_ON_CLOSE**. On a running image
  NTFS refuses that at once (STATUS_CANNOT_DELETE): handle -1, counters untouched. A success would mean
  "the file on disk is not the mapped image" (GUESS) and would also delete the opened file.
- No combase/ole32 frame on the main thread: **not the firewall COM query 0x8945d0**, not Steam init,
  not the overlay. steamclient.dll / Steam.dll are loaded: Steam was running.

## 3. Why ten minutes: the open itself is slow; nothing in the process holds it

Three samples of the main thread all stand in this open: the hitch probe's copy of the main stack
(thread 69908's `st[]`, 0d00fcfc..: returns 0xb0f53e/0xb0f566 = probe B), the watchdog's log line (same
eip, esp 0x10 higher = probe B's shallower frame, GUESS) and the dump (probe A). So the thread advances,
one frame per ~150 s; 4 frames / 10 min fits two minute-long opens per frame.

No second thread holds it: the 24 job threads (0x92699f), the render thread 69352 (0x561375, waiting
for the main thread), streamer threads (0x9a8fb6), nvd3dum, Medal, ReShade and the hook's threads are
all in waits or Sleep; the wrapper is below the game on the stack, past kls_map (no hook lock). A local
NtCreateFile is delayed only from outside the process: a minifilter (antivirus on an open with DELETE
intent on an executable) or an **oplock holder** that must acknowledge a break before an open with
DELETE access proceeds (indexer, sync/backup tool, an agent-side tool holding kl2.exe). Which one:
**GUESS, not in the dump**; 13 passes earlier and hook builds around 09:51-10:01 say transient. Steam
client state never blocks a file open. No level load involved (scene KaneAndLynch.gms, loading 0).

## 4. Verdict and mitigations

VERDICT: the main thread was neither deadlocked nor in any game system; it sat in NtCreateFile of
`C:\Steam\...\Dog Days\KL2.exe` (DELETE access, DELETE_ON_CLOSE, flags -1) issued by Valve CEG's two
per-frame self-checks (0xb0f4a0 from the main-loop step 0x87a930, 0xb0f520 from the per-frame update
0x583fb0), through the hook's CreateFileA wrapper, and each open took about a minute instead of
microseconds. eax 0xc0000034 is (GUESS) the preceding overlay probe `KLExpansion\Overlay\KL2.exe`
missing. The slowness comes from outside the process (filter driver or oplock on kl2.exe: GUESS which).
Not the firewall path, not a Steam client state.

Cheap mitigations (no kl2.exe code touched):
1. Hook: time `kls_real_CreateFile*` (QueryPerformanceCounter); log once per path any open over 250 ms
   with path, access, flags, `_ReturnAddress()`, result; keep {path, flags, start tick} in a global the
   stall watchdog prints ("main thread inside CreateFileA('...kl2.exe', ffffffff) for 93 s").
2. Hook guard: never redirect an open carrying FILE_FLAG_DELETE_ON_CLOSE (0x04000000), never map the exe.
   If a build ever drops an Overlay\KL2.exe, the CEG probe would open it, Windows would delete it on
   close, and the tamper counter [0xdd2608] would start counting.
3. Autotest launch condition: time a plain open of kl2.exe (GENERIC_READ, share 7, no DELETE flags);
   over 1 s or failing -> wait, retry, list holders (Restart Manager RmGetList / handle.exe), log them.
   Never imitate the probe's DELETE_ON_CLOSE open from a script: on a non-running copy it deletes the file.
4. Not recommended: changing the probe's flags or answering its open in the wrapper (changes what CEG
   observes; GUESS what it does with it).

## Applied / proposed (cloud session, 10:40)

- The guard of mitigation (2) is written as `re/klslot_ceg_guard.patch` (two lines in kls_CreateFileA / W plus a
  helper): an open carrying FILE_FLAG_DELETE_ON_CLOSE or DELETE access, or of kl2.exe itself, is never redirected
  or overlaid. Verified from the exe (0x87a930's first instruction calls 0xb0fda0 -> 0xb0f4a0: CreateFileA(own exe,
  0x81, share 7, OPEN_EXISTING, flags -1) -> GetFileTime -> InterlockedIncrement [0xdd2608]). Passes the GCC
  type check of the whole hook. NOT applied to klhook/klslot.c on the branch because the local session is
  building a hook from it today: `git apply re/klslot_ceg_guard.patch` when convenient. No behaviour change for
  any current build (no Overlay\KL2.exe exists), so there is nothing to see live; it closes a door.
- Mitigation (1), the slow-open log and the watchdog naming the open, and (3), the autotest launch condition,
  are proposals for the local sessions (klslot.c / klauto.c / tools/kl_autotest.py are theirs today).
