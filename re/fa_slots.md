# Fragile Alliance level slots in kl2.exe: the list, the limit, the hook

Static reading of `kl2.exe` (build string `Build 0490 (09-03-2010)` at [0xcd82cc], image base
0x400000, no ASLR, no `.bind` section: `.text` is plain on disk) with `debug/kl.py` + capstone,
plus read-only listings of stock archives. Nothing here was run in the game. Every "established"
below is something disassembled or counted; everything else is marked ASSUMPTION or
"not established". Scratch scripts: `...\scratchpad\agents\track-slots\` (`k.py` d/f/g/c/vt/s/p,
`g2.py`, `tabs.py`, `up.py`); the proposed C code was compiled there (MSVC x86, /W4), not installed.

## 1. The object

`ZDownloadableContentManagerSteam` (vtable 0xbd5494, 34 slots; base `ZDownloadableContentManager`
vtable 0xbd53b4), size 0x558, allocated and constructed once at 0x90ac38..0x90ac54 inside the
constructor of `ZSessionManagerSingleton` (0x90ab00), pointer stored in the global **0x168f750**.
0x168f750 has 175 code references; two are writes (0x90ac5d set, 0x6c980b clear), the rest load it
into a register and call a method.

| offset | size | content | written by |
|---|---|---|---|
| +0x000 | 4 | vtable | |
| +0x004 | 9 | FA `available[idx]` (owned / playable) | 0x8468d0 (slot 32): idx 0,1,2,3,5,6 = 1; idx 4,7,8 = 0. Slot 9 sets 1 |
| +0x00d | 9 | FA `present[idx]` | 0x84d5c0: idx 0,1,2,3,5,6 = 1; idx 4,7,8 = (arg > 0) |
| +0x016 | 9 x 0x40 | FA scene names, `Locations/F01/F01_Main` .. `F09` | constructor 0x835ff0, `sprintf(dst,"%s",literal)` |
| +0x256 | 11 | story `available[idx]` | slot 32: all 1 |
| +0x261 | 11 | story `present[idx]` | 0x84d5c0: all 1 |
| +0x26c | 11 x 0x40 | story scene names `Locations/L01/L01_Main` .. `L11` | constructor |
| +0x52c | 5 | content-pack flags (slot 11 sets, slot 14 reads) | Steam DLC checks |
| +0x534 | 4 | dword (slots 30 / 31 get / set) | |
| +0x538 | 4 + 1 | four bytes 0..3 shuffled by 0x5103b0, byte +0x53c | |
| +0x540 | 0x18 | Steam callback object | 0x717f40 |

The FA block is packed: names end at +0x256 exactly where the story bytes start, so
(0x256 - 0x16) / 0x40 = 9 and there is no spare room. idx 4, 7, 8 = F05, F08, F09 are the DLC maps.

Vtable slots that matter (address; what the code does):

| slot | address | meaning |
|---|---|---|
| 5 | 0x5e1510 | `IsFAAvailable(idx)`: true if 0x87c980(session manager) else `this[4+idx]` |
| 6 | 0x700c40 | `IsStoryAvailable(idx)`: `this[0x256+idx]` |
| 7 | 0x634b90 | bit mask of the nine FA available bytes (nine unrolled tests, +4..+0xc) |
| 8 | 0x5e2930 | bit mask of the story bytes, loop `cmp ecx,0xb` |
| 9 | 0x816d80 | `SetFA(idx, name)`: `this[4+idx] = 1; sprintf(this+0x16+idx*0x40, "%s", name)` |
| 10 | 0x4dc590 | same for story (+0x256, +0x26c) |
| 12 | 0x744020 | "current level is an owned DLC level": slot 13 and session-manager level code in {0x12, 0x15, 0x16} |
| 13 | 0x818ba0 | `IsFAAvailable(7)` |
| 15 | 0x7c5ca0 | **FA name: `return this + 0x16 + (int8)idx * 0x40`** (bytes `0f be 44 24 04 c1 e0 06 8d 44 08 16 c2 04 00`). No bound check |
| 16 | 0x7ef310 | story name: `this + 0x26c + idx * 0x40` |
| 17 / 18 | 0x5fb970 / 0x4b94c0 | next / previous available FA idx, modulo 9 (`lea edi,[ebx+9]` `8d 7b 09`, `lea esi,[ebx+8]` `8d 73 08`, magic 0x38e38e39 = /9) |
| 19 / 20 | 0x60c470 / 0x8a2920 | the same in menu order (through 0x746570), accepting present OR available (`8d 78 09`, `8d 58 08`, `mov cl,9`) |
| 21..24 | 0x4f1ba0, 0x4c7d20, 0x5619a0, 0x8c0180 | the same four for story, modulo 11 |
| 28 | 0x77adf0 | Steam ownership check (also reached through slot 1) |
| 32 | 0x8468d0 | reset of all availability bytes; called by the constructor (0x83600b) |

Two non-virtual helpers take the manager in ecx and a byte index:

- **0x746570** menu position -> slot: stack table `0,1,2,3,5,6,4,7,8`; returns 0xff if arg is 0xff
  or `> 9` (`3c 09 77 17` at 0x7465b2: position 9 is accepted and reads one byte past the table - a
  stock off-by-one). 38 direct callers.
- **0x80c9f0** slot -> menu position: table `0,1,2,3,6,4,5,7,8`, same bound at 0x80ca32. 11 callers.

So the option values `MP_SelectedLevel`, `MP_SelectedLevelCl`, `Heist_SelectedLevel` are MENU
POSITIONS (order F01 F02 F03 F04 F06 F07 F05 F08 F09), the session carries SLOT indices.

## 2. Who reads a FA slot name (slot 15) - complete for references through 0x168f750

Method: every code reference to 0x168f750 was listed and the vtable slot of the following call
resolved (`g2.py`, output `g_mgr.out`). Slot 15 is reached from exactly seven places. A caller
holding the pointer somewhere else than the global would be missed; none was seen.

| site | function | what it does with the name |
|---|---|---|
| 0x6c9ee1 | 0x6c9c10 FA session create (4 callers: 0x4198b2, 0x44839d, 0x47524e, 0x7b0a37) | mode = 4 (0x6c9ec4); `SetMapName(slot15(sm+0xbf))` (0x4e7da0: copy, max 0x40, to session manager +8); then `MPMap` (0x6c9f0b) overrides it; writes option `MP_SelectedLevel` = 0x80c9f0(idx) |
| 0x77e298 | 0x77e220 (caller 0x47520d) | mode = 4, `SetMapName(slot15(sm+0xbf))`; no MPMap test |
| 0x7e020d | 0x7e01a0 Arcade start (callers: `ZMercsLevelSelectorHeist` slot 8 at 0x459ef3 = message StartGame; `ZLoadSelectedScene` slot 10 at 0x5eb2c7 when session mode == 4) | position = [0xceceec]; slot = 0x746570(position); session vtbl+0x28(slot); `SetMapName(slot15(slot))`; then 0x725d40. No MPMap test |
| 0x491fd1 | 0x491f50, called from `ZSessionHandlerClient` slot 97 | client side: session +8 = MPMap ? settings.mapname : `slot15(settings.levelIndex)` (story: slot 16); also [0x154d61e] = 0x80c9f0(idx) |
| 0x6c536f | 0x6c49a0 `ZSessionManagerMultiplayer` slot 27 (state machine) | scene change: MPMap ? `0x86f230(settings.mapname)` : mode 4 `0x86f230(slot15(settings.levelIndex))`, mode 2 slot 16 or the literal `Locations/L00/L00_Main` |
| 0x89fa8f | 0x89fa20 (next round / level change; callers incl. `ZGameRulesCoopCl/Sv` slot 7) | unless MPMap: mode 4 `0x86f230(slot15(settings+0x18c))` |
| 0x77aeb3.. | 0x77adf0 slot 28, and 0x8456d0 (Steam callback) | DLC presence: see section 4 |

`settings` = the replicated object at session manager +0x84: map name string +0x230 (getter
0x4468a0), level index +0x1ac (0x467ae0, stored xor 0xac), second index +0x18c (0x8dc7f0), mode
+0x10c (0x83f980). The single-player handler `ZSessionHandlerSP` slot 1 (0x7359f0) loads
`0x86f230(sessionManager + 8)` directly.

Consequences, established: (a) the name is fetched fresh at every use, there is no cached copy of
the table; (b) a network client derives the scene from the INDEX in its OWN table, the name string
only travels when MPMap is set on that machine; (c) the Arcade start path never looks at MPMap.

Scene change 0x86f230(name): appends `.gms` if the current scene name (sysif +0x2b0) ends in
`.gms`, else `.zip` (`%s%s`), and calls EngineDataBase vtbl+0x74 (0x640640 -> 0x645820). The baked
default scene is `KaneAndLynch.gms`, so the suffix is `.gms` in a normal run.

### The two other tables

- **0xcef700**, 22 x {code, zip}: `L01`..`L11` (L03 -> `Locations/L03/L03_Main_Stress.zip`),
  `MM01` KaneAndLynch.zip, `AM01` AttractMode.zip, `F01`..`F09`. One reader, **0x6d0f90** (bound
  `83 ff 16` at 0x6d100a; one caller 0x6c8040, no RTTI owner): compares the string at its object
  +0x345 with each code; entries 0..10 are answered from manager slot 16 + `.zip`, entries >= 11
  from the table. It is not on any of the seven FA paths above. What object carries the code
  string: not established (a saved-progress record is my guess - ASSUMPTION).
- **0xd35dd4**, 20 pointers to `\SCENES\Locations\F01\F01_Main` .. `L11`: no instruction in `.text`
  holds any address in 0xd35dd0..0xd35e30 as an immediate or displacement (scanned every byte
  offset), and no data pointer to it exists. Unreferenced as far as an imm32 scan can tell.
- A third, on the stack, in **0x7e9dd0** (`ZSessionManagerMultiplayer` slot 14 calls it): 23 codes
  `NoChange!ThisWillNotBeFound!`, `KaneAndLynch`, `L00`..`L11`, `F01`..`F09` (bound `83 fe 17`);
  the first one found as a case-insensitive substring of the loaded scene name gives the level
  code stored at session manager +0x60 (F01 = 14 .. F09 = 22, nothing found = 0). Readers found
  (pattern "load 0x168e598, then [reg+0x60]", 15 hits): comparisons with 3, 6, 0xb, 0xd (story
  levels) and slot 12 above. A scene name with none of the codes gets 0.

## 3. Name-sensitive code: the naming rule for a new folder

All tests below use 0x7472b0 = case-insensitive substring search (`_memicmp`).

| site | test on the scene name | effect |
|---|---|---|
| 0x545efa.. (`ZEngineDataBase` slot 10, a size/count budget) | contains `_Main` and (`F0` or `F10`) | adds 0x32000 and 0x5dc to the two totals; `_Main` + `m05_YOU_WILL_NEVER_FIND_ME` adds 0x4b000 / 0x8fc; all add 0xea6 |
| 0x693167 (`ZDllSound` slot 16) | contains `locations\f` or `locations/f` | FA-only branch for every sound group not named `Music` |
| 0x5655a5 (loader sequence) | `Locations` + separator + `L` + number >= 1 | story flag (+0x40) |
| 0x7e9dd0 | `F01`..`F09`, `L00`..`L11`, `KaneAndLynch` | level code, see above |
| 0x881350 | `L01_Main`..`L11_Main`, `IntroCinematic`, `Funeral`, `AttractMode`, `Loader_Sequence` | story bookkeeping |
| 0x7b043a | `kaneandlynch` | frontend / splash |

Rule that satisfies every FA test and trips none of the others:
**`Locations/F0<tag>/F0<tag>_Main`**, tag = letters/digits such that the name contains none of
`F01`..`F09`, `L00`..`L11`. Example used below: `Locations/F0M01/F0M01_Main` (26 chars; limit 63,
the slot and every copy are 0x40 bytes). `Locations/DM01/DM01_Main` would load, but loses the FA
budget and the FA sound branch - what that costs in play is not established, so do not use it.
`Locations/F10/F10_Main` also passes (the exe has an `F10` literal), but only that one name.

## 4. What must exist on disk

For scene name N = `Locations/F0M01/F0M01_Main`, under the Dog Days folder:

| file | needed | evidence |
|---|---|---|
| `Scenes\Locations\F0M01\F0M01_Main.zip`, members `Scenes/Locations/F0M01/F0M01_Main.<ext>` and nine `..._Main<Language>.LOC` | yes | loader 0x7f4fe0: unmount all, mount `Patch01.zip` (0x7f5610), then the scene's `zip` name from 0x60c410 (0x7f561c), mounted at 0x7f5827. Stock F02: 31 members, named exactly like that, plus `guielems.xml`, `menu/ingame.xml`, `windows.xml`, `Menu/online.xml` |
| `F0M01_Main.WHD`, `F0M01_Main.WAV` beside the zip | yes if the .SND refers to them | every stock level has both; what a missing file does: not established |
| `F0M01_Main_LS.SND`, `F0M01_Main_LS_<Lang>.WHD/.WAV` | optional | 0x8ffd60 builds `<zip path minus .zip>_LS_<Lang>.WHD/.WAV` (strings `_LS_` 0x8ffe21, `.WHD` 0x8ffe59, `.WAV`, `.SND`); the loader tries the language, then `Default`, then deletes the object and goes on (0x7f5720..0x7f5768) |
| `Loader_Sequence.zip` (+ `.WHD/.WAV`) in the level folder | optional | 0x565500: tries the level folder, then `\AllLevels\Loader_Sequence.ZIP` (0x5656bf), then sets "no sequence" (+0xd) |
| `.hti` | no | earlier boot-config report: the string occurs nowhere in the exe (not re-checked here) |

DLC presence test **0x5432d0(name)**: `CreateFileA("Scenes/%s.zip")` relative to the current
directory (format at 0xb2c060). Slot 28 (0x77adf0) does, for app 28010 (`push 0x6d6a`,
SteamApps vtbl+0x1c): `n = slot15(4); if (0x5432d0(n)) slot9(4, n);` same for idx 7, and for
28017 (`0x6d71`) idx 8. It reads the name through slot 15, so a redirected slot is tested with its
new name. Nothing else checks files before the load starts.

## 5. Making a menu entry load a new folder

### Options compared

1. **Patch the nine `push` operands of the constructor in DllMain** (recommended). The names are
   written once, by `sprintf("%s")` from nine literals. Sites (all verified `68 <imm32>`):

   | idx | push at | operand | | idx | push at | operand |
   |---|---|---|---|---|---|---|
   | 0 F01 | 0x836016 | 0xb75044 | | 5 F06 | 0x83606f | 0xb19654 |
   | 1 F02 | 0x836026 | 0xb39e28 | | 6 F07 | 0x836085 | 0xb16f70 |
   | 2 F03 | 0x836036 | 0xb326a8 | | 7 F08 | 0x836098 | 0xb872a0 |
   | 3 F04 | 0x836049 | 0xb2c534 | | 8 F09 | 0x8360ab | 0xb7d4f0 |
   | 4 F05 | 0x83605c | 0xb672a4 | | | | |

   No timing problem: `DINPUT8.dll` is a static import of kl2.exe, so its DllMain runs before the
   exe entry point (0xa8dc71), i.e. before any constructor. The operand is replaced by the address
   of a buffer inside the hook DLL. Name length <= 63 or the sprintf overruns into the next slot.
2. Rewrite `[0x168f750] + 0x16 + idx*0x40` after construction. Works for the same reason (names
   are fetched fresh), but needs a trigger. `DirectInput8Create` is NOT one: it is called from
   WinMain (0x476d0a -> 0x72bd20 -> 0x5da840 -> input constructor 0x85df70 -> 0x6d7836), while the
   manager is created by the `ZSessionManagerSingleton` factory (0x539510, registered by the static
   initialiser 0xb02b60 through 0x676f90). Which comes first: not established. A polling thread
   (`*(void**)0x168f750 != 0` and first dword == 0xbd5494) is the only safe trigger; option 1 needs none.
3. `-o MPMap=<name>`: read at four places only (0x491fa1, 0x6c533d, 0x6c9f0b, 0x89fa62). It
   replaces the name in the FA session-create path 0x6c9c10 and makes the multiplayer state
   machine use the session's stored name. The Arcade start 0x7e01a0 and 0x77e220 never test it and
   the single-player handler loads session +8 directly, so **in Arcade MPMap is expected to do
   nothing** (established for those three functions; that Arcade runs through them and not through
   0x6c9c10 is read from the callers, not observed). MPMap also redirects EVERY map at once. Use it
   only as a diagnostic.

### What else must agree

- **Availability.** Base slots 0,1,2,3,5,6 are always available. A DLC slot (4, 7, 8) the owner
  does not own stays locked (slot 5 returns 0 -> "MissingContentPack" texts, 0x436845 etc.).
  For a REDIRECTED DLC slot only, flip the reset value in slot 32: `c6 46 0c 00` at 0x8468ea
  (idx 8), `c6 46 0b 00` at 0x8468ee (idx 7), `c6 46 08 00` at 0x8468f2 (idx 4): last byte -> 01.
  Never do this for a DLC slot that keeps its stock name: that would unlock paid content.
  `present[]` (+0xd) is only read by slots 19/20, which accept available OR present: leave it.
- **Which slot to take.** Additive delivery means taking a slot whose stock map the owner cannot
  play anyway: F09 (idx 8), then F08 (7), F05 (4), if those DLCs are not owned. Ownership is not
  knowable statically; the watcher below logs `available[]` after the Steam check so one run tells.
  If all nine are owned, any redirect hides a stock map while active (remove the ini line to get
  it back; no file is touched).
- **Session default.** The `ZSessionManager` constructor (0x6997f0) presets session +8 to the
  literal `Locations/F01/F01_Main` (`68 44 50 b7 00` at 0x69981e). Only relevant if idx 0 is
  redirected; then patch that operand too, to the same buffer.
- **Tables 0xcef700 / 0xd35dd4**: leave (section 2).
- **Title and picture** follow the slot, not the name: title = LOC string
  `/Menu/Online/Scenarios/Title%02i` with slot + 1 (0x436762, 0x5b6a25, 0x62b1a5, 0x631995;
  `%02d` variant at 0x43ab5d, 0x5baef5); picture = frontend.xml order. See section 7. A redirected
  F09 shows "Radio Tower" and its picture until those are overridden.
- **Loading screen**: `Loader_Sequence.zip` of the new folder, or the AllLevels one.
- **Level code** (session +0x60) becomes 0 with the recommended name: slot 12 ("owned DLC level")
  is false, as for a base map.
- **Online.** A client maps the replicated slot index through its own table (0x491fd1, 0x6c536f):
  a stock client joining a redirected host loads its stock map for that index. Session
  advertising carries the index (`MP_SelectedLevel` written at 0x6c9f50), not the folder. And
  `ZLeaderBoardServiceSteam` slot 1 (0x4b3c24) and `ZGameRulesHeist` slot 6 (0x5e8ae4) pick the
  leaderboard from 0x80c9f0(current slot): a redirected map would report under the stock map's
  board. **Test with Steam offline**; online is stage 4 and needs every player on the same pack.

### Hook code (proposed for klhook.c; compiled in scratch with `cl /W4`, never run in the game)

`KLHook.ini`:

```ini
[Slots]
; F01..F09 = scene name without extension, relative to Scenes\  (max 63 characters)
F09=Locations/F0M01/F0M01_Main
```

```c
/* ---- FA slot redirect (re/fa_slots.md). Goes above DllMain. ---- */
#define KL2_BUILD_PTR   0x00cd82cc              /* -> "Build 0490 (09-03-2010)" */
#define KL2_DLCMGR      0x0168f750              /* ZDownloadableContentManagerSteam *  (0 until created) */
#define FA_SLOTS        9
#define SLOT_LEN        0x40

/* the nine `push offset "Locations/Fxx/Fxx_Main"` in the manager constructor 0x835ff0 */
static const struct { DWORD site, str; } fa_push[FA_SLOTS] = {
    {0x836016, 0xb75044}, {0x836026, 0xb39e28}, {0x836036, 0xb326a8}, {0x836049, 0xb2c534}, {0x83605c, 0xb672a4},
    {0x83606f, 0xb19654}, {0x836085, 0xb16f70}, {0x836098, 0xb872a0}, {0x8360ab, 0xb7d4f0} };
/* `mov byte ptr [esi+4+idx], 0` in the availability reset 0x8468d0 (vtable slot 32), DLC slots only:
   address of the instruction, its four bytes. The last byte becomes 1. */
static const struct { int idx; DWORD site; BYTE b[4]; } fa_avail[3] = {
    {8, 0x8468ea, {0xc6, 0x46, 0x0c, 0x00}}, {7, 0x8468ee, {0xc6, 0x46, 0x0b, 0x00}}, {4, 0x8468f2, {0xc6, 0x46, 0x08, 0x00}} };
static char fa_name[FA_SLOTS][SLOT_LEN];        /* must outlive the process: the constructor reads them later */
static int fa_set[FA_SLOTS];

static int poke(DWORD at, const void *bytes, int n)
{
    DWORD old;
    if (!VirtualProtect((void *)at, n, PAGE_EXECUTE_READWRITE, &old)) return 0;
    memcpy((void *)at, bytes, n);
    VirtualProtect((void *)at, n, old, &old);
    FlushInstructionCache(GetCurrentProcess(), (void *)at, n);
    return 1;
}

/* Called from DllMain (the constructor has not run yet: dinput8.dll is a static import). */
static void slots_install(const char *ini)
{
    const char *build = *(const char **)KL2_BUILD_PTR;
    if (IsBadReadPtr(build, 24) || memcmp(build, "Build 0490 (09-03-2010)", 23)) { klog("slots: not build 0490, nothing patched"); return; }
    for (int i = 0; i < FA_SLOTS; i++) {
        char key[8]; snprintf(key, sizeof key, "F%02d", i + 1);
        if (!GetPrivateProfileStringA("Slots", key, "", fa_name[i], SLOT_LEN, ini)) continue;   /* truncates to 63 chars */
        BYTE *p = (BYTE *)fa_push[i].site;
        if (p[0] != 0x68 || *(DWORD *)(p + 1) != fa_push[i].str) { klog("slots: %s: unexpected bytes at %08lx, skipped", key, fa_push[i].site); continue; }
        DWORD to = (DWORD)fa_name[i];
        if (!poke(fa_push[i].site + 1, &to, 4)) { klog("slots: %s: VirtualProtect failed", key); continue; }
        fa_set[i] = 1;
        for (int k = 0; k < 3; k++)             /* a redirected DLC slot must not stay locked */
            if (fa_avail[k].idx == i && !memcmp((void *)fa_avail[k].site, fa_avail[k].b, 4)) {
                BYTE one = 1; poke(fa_avail[k].site + 3, &one, 1);
            }
        klog("slots: %s -> %s", key, fa_name[i]);
    }
}

/* Watcher: logs the table once the manager exists and whenever it changes. Reads only, except
   that it re-asserts availability of the redirected slots (insurance against a writer of
   available[] this document did not find). */
static DWORD WINAPI slots_watch(LPVOID unused)
{
    BYTE last[FA_SLOTS * (SLOT_LEN + 2)] = {0}, now[sizeof last];
    for (;;) {
        Sleep(500);
        BYTE *m = *(BYTE **)KL2_DLCMGR;
        if (!m || IsBadReadPtr(m, 0x558) || *(DWORD *)m != 0xbd5494) continue;        /* vtable of ...ManagerSteam */
        for (int i = 0; i < FA_SLOTS; i++) if (fa_set[i] && !m[4 + i]) m[4 + i] = 1;
        memcpy(now, m + 4, 9); memcpy(now + 9, m + 0xd, 9); memcpy(now + 18, m + 0x16, FA_SLOTS * SLOT_LEN);
        if (!memcmp(now, last, sizeof now)) continue;
        memcpy(last, now, sizeof now);
        for (int i = 0; i < FA_SLOTS; i++)
            klog("slots: [%d] available=%d present=%d %.63s", i, m[4 + i], m[0xd + i], (char *)m + 0x16 + i * SLOT_LEN);
    }
}
```

In `DllMain`, after `ini` is built and before the final `klog`:

```c
    slots_install(ini);
    CloseHandle(CreateThread(0, 0, slots_watch, 0, 0, 0));
```

The header comment of klhook.c ("Nothing in the game is patched") must then change. With no
`[Slots]` section nothing is patched and the watcher only logs.

Expected `KLHook.log` of a correct first run: `slots: F09 -> Locations/F0M01/F0M01_Main`, later nine
`slots: [i] available=.. present=.. <name>` lines with [8] showing the new name and available=1;
further blocks appear when the Steam check or a menu changes a byte (that is the ownership answer).

## 6. More than nine

The 9 is not one constant. Sites that encode it (bytes as on disk):

| what | where | bytes / form |
|---|---|---|
| storage: three packed arrays followed by story data | object +4, +0xd, +0x16 | layout |
| name accessor | slot 15 0x7c5ca0 | `8d 44 08 16` (`+0x16`), `c1 e0 06` |
| available getter / setter | slot 5 0x5e1528 `8a 44 30 04`; slot 9 0x816d89 `c6 44 08 04 01` + `8d 44 08 16` | |
| availability mask | slot 7 0x634b90 | nine unrolled `cmp byte [ecx+4..0xc]` |
| next / previous | slots 17, 18, 19, 20 | `8d 7b 09`, `8d 73 08`, `8d 78 09`, `8d 58 08`, `mov cl,9`, 0x38e38e39 (eight uses) |
| reset | slot 32 0x8468d8..0x8468f2 | nine `mov byte [esi+N]` |
| present flags | 0x84d5c0 | nine `mov byte [ecx+N]` |
| constructor | 0x836016..0x8360bc | nine sprintf |
| order tables | 0x746570, 0x80c9f0 | nine `mov byte [esp+N]` each, bound `3c 09 77 17` |
| Arcade selector step | `ZMercsLevelSelectorHeist` slot 10, 0x929479 / 0x929485 | `83 fb 08`, `83 f8 09` |
| DLC literals | slot 13 (`push 7`), slot 12 (0x12, 0x15, 0x16), slot 28 (4, 7, 8) | |
| level code table | 0x7e9dd0 | 23 entries, `83 fe 17` |
| code/zip table | 0x6d0f90 | 22 entries, `83 ff 16` |
| XML | frontend.xml: 5 text lists + 2 image lists + 9 picture elements; Menu/online.xml: 2 text lists | section 7 |
| LOC | `Title01`..`Title09`, then `Title11`..`Title15` ("DLC03".."DLC07"); **no `Title10`** | English LOC of kaneandlynch.zip |
| options | `MP_SelectedLevel`, `MP_SelectedLevelCl` (position + 1, 0 = All), `Heist_SelectedLevel` | value range comes from the XML child count - ASSUMPTION, the toggle classes were not disassembled |

Relocating the arrays in place means rewriting about fifteen functions. The cheaper design uses
the fact that outside the class every per-index access goes through the vtable or the two order
helpers (section 2 method; I found no code that reads `[mgr+4+idx]` or `[mgr+0x16+..]` directly from
outside, but that is a negative result from a pattern search, not a proof):

1. Hook-owned arrays `avail[N]`, `present[N]`, `name[N][0x40]`, N up to 127 (indices travel as
   signed bytes: `movsx` in slots 5, 9, 15; position 0xff means "none").
2. Copy the 34-entry vtable 0xbd5494, replace slots 5, 7, 9, 13?, 15, 17, 18, 19, 20 (and 32 to
   reset the hook arrays) with `__thiscall`-compatible hook functions (`__fastcall f(void *self,
   void *edx, ...)`), and store the copy's address in the object's first dword once the object
   exists (polling thread; the vtable check then becomes "0xbd5494 or ours").
3. Detour 0x746570 and 0x80c9f0 (5-byte `jmp` at entry; both start with `83 ec 10 a1 e0 9e d4 00`,
   so the first 8 bytes move to a trampoline or the functions are replaced outright - they are
   pure) with identity-extended tables: positions >= 9 map to themselves.
4. Patch 0x929479 (`83 fb 08` -> N-1) and 0x929485 (`83 f8 09` -> N).
5. frontend.xml / online.xml: one more `<Text>` and `<Graphic>` per list; LOC: add `Title10` or
   skip slot 9 and start extra maps at slot 10 (`Title11` = "DLC03" exists).
6. Leave 0x7e9dd0 and 0x6d0f90 alone (unknown names already fall through).

Not established and to be checked before trusting it: slot 7's mask is consumed where
(0x8b660f, one site - a 32-bit mask caps N at 32 if it matters); whether the toggle GUI classes
size themselves from the XML; whether saved options / profiles store a position that must stay
< 9 when the hook is absent (a profile saved with position 9+ and then loaded WITHOUT the hook
would index past the stock arrays: slot 15 has no bound check). Confidence that the site list is
complete: medium for the class and helpers (enumerated from the global), low for GUI-side limits.

Run-time verification: in the vtable copy, give every FA slot a logging wrapper for the first
session (slot number, index argument, return address) and add a guard page or a canary after the
stock arrays; drive the menu to position N-1 in Arcade and in the FA lobby. Any index >= 9
reaching a stock function, or a return address not in the tables above, is a missed site.

Nine is enough for the stated plan as long as unowned DLC slots exist (up to three extra maps
with nothing lost); go beyond only when a fourth Dead Men map is ready.

## 7. frontend.xml / LOC: name and picture of an entry

Files: `menu/frontend.xml` (Patch01.zip copy, 666,602 bytes, is the one in effect: Patch01.zip is
mounted first and wins), `Menu/online.xml` (in every scene archive, not in Patch01.zip),
`menu/ingame.xml` (no level lists). Line numbers are of the Patch01 frontend.xml.

| line | element | option | entries |
|---|---|---|---|
| 2440 | `MercsLevelSelectorHeist` "HeistLevel" (Arcade), `ToggleReceivers="HeistLevelImageToggler,HeistIndicator"` | `Heist_SelectedLevel` | 9 `<Text Text="/Menu/Online/Scenarios/TitleNN"/>` in order 01 02 03 04 06 07 05 08 09 |
| 2392..2403 | `H01_LevelPicture`..`H09` (`Graphic="LevelPicture_H01"`..) + `ToggleImages` "HeistLevelImageToggler" | | Arcade pictures |
| 5221, 8658 | `ToggleText` "SLFGCreateLevel", "OFGCreateLevel" | `MP_SelectedLevelCl` | "All" + 9 titles (search filters) |
| 7424, 7546 | two more title lists | | 9 titles |
| 7974 | `ToggleText` "LobbyLevelNameToggler" | `MP_SelectedLevel` | 9 empty texts |
| 7989..7997 | `LobbyPictureF01`..`F09` (`Graphic="LevelPicture_F01"`..) | | FA lobby pictures |
| 8000 | `ToggleImages` "LobbyImageToggler" | `MP_SelectedLevel` | 9 `<Graphic>` in order F01 F02 F03 F04 F06 F07 F05 F08 F09 |

- **Title text** is a LOC path: `/Menu/Online/Scenarios/Title01` = "Subway" .. `Title09` =
  "Radio Tower" (node `Scenarios`, 15 children, in `Scenes/kaneandlynch<Language>.LOC`; the same
  node is repeated in every level's `<L>_Main<Language>.LOC`, checked in F02). The exe also builds
  the path itself (`Title%02i`, slot + 1) for the lobby tag `LevelName`, so an XML edit alone does
  not rename the entry everywhere.
- **Picture** `Graphic="LevelPicture_F09"` names an object of the FRONTEND SCENE: the string is an
  entity name in `Scenes/kaneandlynch.buf` (offset 160288; nine `_F`, nine `_H`, eleven `_L`), its
  image is in `Scenes/kaneandlynch.TEX`. It is not an image file.

Override recipes (Patch01.zip-style: a member in Patch01.zip replaces the same-named member of
every archive; back up the stock Patch01.zip to KL_PortBackup first; that the override also works
for large scene members is the earlier report's static reading, not observed):

- Rename one entry everywhere: Patch01 member `Scenes/kaneandlynch<Language>.LOC` (nine files)
  with `Title09` changed, AND the same `Title09` in the new level's own nine LOC members (ours to
  write anyway). Needs a LOC writer: the node stores child offsets, so the string cannot simply be
  lengthened in place; a same-length-or-shorter overwrite padded with NULs is the no-tool route
  (ASSUMPTION that trailing NULs are harmless; stock strings are followed by 5 NUL bytes).
- Rename in the menus only, without touching a LOC: replace the `<Text Text="/Menu/..Title09"/>`
  lines by a literal in `menu/frontend.xml` (already a Patch01 member) and a Patch01 copy of
  `Menu/online.xml`. ASSUMPTION that a text not starting with `/` is shown literally (the stock
  file has `<Text Text="All" />` and `Text="Scenario"` in the same lists); the lobby `LevelName`
  tag would still show the LOC title.
- Picture: cheapest is to point the slot's `<Graphic>` / `H0n_LevelPicture` at another existing
  picture object in frontend.xml. A new picture means replacing that object's texture inside
  `Scenes/kaneandlynch.TEX` (84.8 MB member, same id and format) as a Patch01 member; a genuinely
  additional picture object is a graft on the frontend scene (new entity in .gms/.prp/.buf, new
  texture, new material) - only needed together with section 6.
- Add an entry (with section 6): one `<Text>` per title list, one `Graphic` element + one
  `<Graphic>` per image list, `Title10` in the LOCs.

## 8. Click-free load testing

Established statically:

- No ini key sets session mode 4. `ZSessionManagerMultiplayer` slot 15 (0x8733e0) reads `MPTutor`,
  `StartAsServer`, `StartAsClient` (state 3), `StartAsCoop` / `EnableCoop`, `StartAsSinglePlayer`
  (0x74b210(1), mode 1). Mode 4 is set only by 0x6c9ec4 and 0x77e260 (`push 4; call 0x5be510`).
- The Arcade round is started by **0x7e01a0** (no arguments): position from [0xceceec] (if < 0 it
  asks 0x85f510), slot = 0x746570(position), session vtbl+0x68(8), vtbl+0x28(slot), SetMapName,
  then 0x725d40. It is called by the Arcade selector on StartGame and by `ZLoadSelectedScene`
  only when session mode is already 4.
- `-o DefaultScene=Locations/F02/F02_Main.gms` makes the engine load that scene at boot with
  whatever the session manager defaults to; whether a FA level then starts a round, sits idle or
  asserts is **not established**.

Experiments, in this order, each with Steam offline and `-o AutoExit=N` so the run ends itself:

1. `-o AutoExit=25 -o DisableSplashScreens`. Seen if `-o` works: no splash, process ends after
   about 25 s, KLHook.log has the load line and (with the watcher) the nine slot lines. If the game
   stays up, `-o` is not honoured and everything below must go through KLHook instead.
2. `-o DefaultScene=Locations/F02/F02_Main.gms -o AutoExit=120 -o DisableSplashScreens` (a STOCK
   map, so a failure is the boot route and not our data). Outcomes: (a) round starts -> direct
   boot is the load test, repeat with the grafted map's name; (b) loads to 100 % but no round /
   no player -> still a valid LOAD test for a converted archive (crash triage needs no more),
   useless for play testing; (c) assert or crash in session / game-rules code -> route dead,
   record the site in debug/kl.py SITES. Repeat once with `-o StartAsSinglePlayer` added.
3. If 2 gives (b) or (c): keep the menu and let KLHook drive it. Two forms. Key injection inside
   the dinput8 proxy (wrap `IDirectInput8A::CreateDevice` and the keyboard's `GetDeviceData`,
   append DIK events: Return / arrows per `MenuInput`) - the menu route is known to work by hand.
   Or, as an experiment only, from the game's own thread (inside the proxied `GetDeviceData`)
   once the Arcade page is up: write the wanted position to [0xceceec] and call 0x7e01a0. What
   state that function expects beyond session mode 4 (0x5eb2c1) is not established; the Arcade
   page constructor 0x75fdf0 sets option `CoopNetMode` = 4 first.

For a redirected slot the Arcade position is 0x80c9f0(slot): F09 = position 8 = the last entry.

## 9. Open points

- Order of manager construction versus `DirectInput8Create` (irrelevant for the proposed patch).
- Any writer of `available[]` other than slot 9, slot 32 and the constructor (the watcher covers it).
- Effect of a missing `.WHD/.WAV`, and of level code 0 on HUD / statistics code not matched by the
  +0x60 pattern search.
- Owner of the object read by 0x6d0f90 (code string at +0x345).
- Whether Patch01.zip can carry `Scenes/kaneandlynch.TEX` / `.LOC` overrides at run time.
- GUI toggle classes' own entry limits (needed only for more than nine).
