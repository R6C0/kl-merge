# Soldier holder [S+0xb0] and bit 0x4 of [S+0xa8] (static research, 2026-11-04)

Scope: kl2.exe (DD, 32-bit, base 0x400000). Static disassembly only (debug/dasm.py), no game run.
Confidence tags: H high, M medium, L low. Anything not proven is marked GUESS.

## 1. What [S+0xb0] is

[S+0xa8] is an embedded "target reference / holder" struct (size 0x3c, ctor 0x6a2ce0) inside ZSoldier
(vtable 0xbd0954, ctor 0x761900 -> base 0x7cfac0). Layout (absolute offsets from S):

| Offset | Meaning |
|---|---|
| +0xa8 | flags dword |
| +0xac | entity pointer |
| +0xb0 | handle (entity pool slot+1) |
| +0xb4 | refcounted [ent+0x54] |
| +0xb8 | clock |
| +0xc0 | byte, flags&1 |
| +0xc4..+0xd8 | position floats |
| +0xdc | clock |

- Handle = 0x6ece90(entity): `mov ecx,[0xe0ff90]; call 0x86ca10` = entity pool index (page*size+rem+1). (H)
- Reverse: 0x8ccde0 (cdecl, handle -> entity, generation checked, 0 if stale). (H)
- A zero handle means "no holder". It is NOT a pointer and not a team id. (H)

### Users
- ZCloseIn eval 0x6724e0 and ZAttackNoCover eval 0x85ece0 both start with `cmp dword [S+0xb0],0` (0x85ed1d in the latter) and bail when 0. Then the flags mask test 0x616480 (ecx=&flags): bit0 and bit 0x10 must be set; bits 0x4, 0x40, 0x200 must be clear. (H)
- So with [S+0xb0]==0, neither tactic can ever pass: matches the live data (online 0 everywhere, Arcade 0x320/0x3d6). (H)

### Writers
Everything on the soldier goes through SetHolder 0x8bd420 (thiscall, ecx=&S+0xa8, args (handle, DWORD* flagsptr), ret 8). It stores handle and entity and copies *flagsptr into flags; handle 0 clears +8/+4/+0xc and leaves the flags dword untouched. Clear = 0x8b3650. (H)

- Main stock writer: target selection 0x767510 (HASHED range; this = B = [S+0x698], [B+0x154]=S, entered via slot-113 thunk 0x47a0f0).
  - Winner: SetHolder at 0x767eee (`add ecx,0xa8` after `mov [edi+0x154]`), handle from 0x6ece90(winner entity). (H)
  - No winner: SetHolder at 0x767f8a with (0, &0x168e35c) -> handle 0. (H)
  - Quick path stores flags at 0x76762e. (M)
- Other SetHolder/Clear callers seen but not classified (GUESS, L, mostly unrelated to the combat holder): 0x4f7062, 0x58300f, 0x5844c2, 0x7726a0, 0x7834e0, 0x7b48f0, 0x7f0570.
- Raw `[reg+0xb0]` writes elsewhere (6679 hits touching 0xa8/0xac/0xb0 in .text) belong to unrelated classes (property resets etc.); none other proven for ZSoldier.

### Candidate array in B and scoring (0x767510)
- Array base B+4, count [B], stride 0x14: +0 flags (bit0 valid/seen), +4 entity ptr, +8 type (0..3, jump tables 0x768004 / 0x768014), +0xc time. (H)
- Rescan throttle: [B+0x180] next time, [B+0x184] force, [B+0x18c] hold. (M)
- Score via soldier vcalls +0x1b8 (slot 110), +0x1bc (slot 111 = 0x882470), +0x1c0 (slot 112). Best starts at -1e38 (const 0xb5f1e0); replaced only if strictly greater. So a candidate scoring <= -1e38 or an empty array yields NO winner. (H)
- Array is fed by MarkSeen 0x4880d0 (takes entity POINTER, creates the entry, sets bit0), pruned by 0x51e480 (via 0x559190). (H)

## 2. Bit 0x4 of [S+0xa8]

- Set by `or [esi],4` at 0x767998, cleared by `and [esi],0xfffffffb` at 0x76799d, inside 0x767510, with the value coming from friend-in-line check 0x5706a0 (sets/clears bit 4 of the candidate entry flags). The entry flags are then copied into the holder flags by SetHolder. (H for the writer, M for the exact semantics "a friend stands in the firing line")
- 0x5706a0 depends on 0x7f6850 (true only in Arcade), rec+0x79 bit 2, and team. GUESS (M): online it takes the other branch, so bit 4 behaviour differs from Arcade. Online 0x10 constant vs Arcade 0x10/0x14 alternating fits this.
- Bit 4 set means the fire test 0x616480 FAILS (bit 4 must be clear): in Arcade a bot alternates 0x14 (friend in line, hold fire) / 0x10 (clear). Online it stays 0x10 because the flags are never rewritten: the no-winner path passes handle 0 and the flags dword keeps its stale value 0x10. (M)

## 3. Why online [S+0xb0] is 0 (explanation)

0x767510 either never finds a winner online, or never runs its winner branch for the marked bot. Candidates (all GUESS):
1. (M) klbrain Sense/LosGate skips LOS-blocked humans, so the known list B has no human; cops may be absent from B or score <= -1e38 in slot 111 for a traitor bot (cops are same-team-ish targets). Result: empty winner -> SetHolder(0,...).
2. (L) slot-111 score 0x882470 gates (see re/traitor_slot111_gates_1103.md) reject humans online.
3. (L) Arcade winner 0x320/0x3d6 might be a cop, not a human; unproven.
The 0x767f8a no-winner path is the exact stock writer of the observed 0. (H)

## 4. Lever proposal (default off, no hashed detour)

Goal: while the marked traitor bot's nearest human is the intended target, make [S+0xb0] hold that human's handle.

### Option A (preferred, stock writer): feed the list
From the host game-thread tick, for the marked bot's B = [S+0x698], call MarkSeen 0x4880d0 (entity POINTER of the human body, as the Sense code does) so the stock 0x767510 creates the entry and may pick it. Calling hashed functions is allowed; no detour. Risks: still needs the human to score strictly highest in slot 111, and Sense is deliberately skipping blocked humans (LosGate), so this reopens the through-walls fire seen in bs38. GUESS (L-M that it wins the score).

### Option B (data write, deterministic): direct SetHolder
Per host tick, only while the human is LosGate-blocked (so the bot should approach, not fire), for marked bot S and nearest human body H:
```
handle = ((int(__thiscall*)(void*))0x6ece90)(H);          // ecx = entity H
if (((void*(*)(int))0x8ccde0)(handle) != H) return;        // generation check
DWORD fl = 0x11;                                           // bit0|bit4? NO: 0x11 = bit0 + bit 0x10; bit 0x4 clear
((void(__thiscall*)(void*,int,DWORD*))0x8bd420)((char*)S + 0xa8, handle, &fl);
```
- ecx for 0x6ece90 is the entity (it loads [0xe0ff90] itself); confirm by one disassembly check before coding. (M)
- 0x11 is chosen so 0x616480 passes (bit0, bit 0x10 set; 0x4/0x40/0x200 clear). (H on mask, M that bit0 is also right for a freshly set holder)
- The write is overwritten at the next 0x767510 rescan (about every 0x400 ms, [B+0x180]); rewrite each tick, or re-apply after the rescan. GUESS (M).
- Ordering risk: if NoCover 0x85ece0 precedes ZCloseIn 0x6724e0 in list A, a valid holder lets the bot FIRE through the wall before approaching. Gate the lever on "approach phase" and clear (handle 0) when the human becomes LOS-clear or within range, or set bit 0x4 (fire test fails) during approach: flags 0x15 keeps bit0/0x10 but blocks 0x616480 for firing while ZCloseIn only checks the handle != 0 (0x6724e0). GUESS (L-M): ZCloseIn may also run 0x616480; verify by disassembling 0x6724e0 past the handle check before relying on it.
- Existing klbrain HolderFix (klbr_hx_apply) is the same idea; this note adds the exact functions and the bit 0x4 trick.

### Verification plan (probe first)
Extend ModeBProbe to log [S+0xb0], flags, and 0x8ccde0([S+0xb0]) class for the marked bot, once with the lever off and once on; check that CloseIn eval 0x6724e0 returns nonzero and that combat flag [S+0x4fc] (Defend tick 0x85f6c0 walks list A only when [S+0x4fc]!=0 and [S+0x6fc]==0) is also set, otherwise list B runs and CloseIn (list A only) is never evaluated.

## 5. Open
- Which candidates actually sit in B online (cops? humans?) and their slot-111 scores.
- Whether Arcade holders 0x320/0x3d6 are cops or humans.
- Classification of the remaining SetHolder/Clear callers listed in section 1.

## Verifier (2026-11-04, static, debug/dasm.py plus a full-.text linear sweep for callers; no game run)

Verdict: the core is CONFIRMED (what [S+0xb0] is, who gates on it, that the online 0 comes from the no-winner clear). The writer list is REFUTED as complete (13 SetHolder call sites, the report named 10 and mixed in a different class). The "flags from 0x168e35c" story is CORRECTED. "7f6850 true only in Arcade" is UNVERIFIED as stated. Option A and the flags value 0x11 are not endorsed. Endorsed lever: Option B with flags 0x01 (end of section).

### Confirmed
- Holder struct. SetHolder 0x8bd420 (thiscall, ret 8) stores flags [this+0] = *flagsptr (0x8bd4dd..e4), entity [this+4], handle [this+8] (= S+0xb0), refcounted ptr [this+0xc] = [ent+0x54] only if a type-mask test passes (0x8bd48e..b5), clocks [this+0x10] and [this+0x34], byte [this+0x18] = flags&1. Handle 0 (0x8bd42e..57) zeroes +4/+8/+0xc and does NOT read or write the flags dword. (H)
- 0x6ece90: `push ecx; mov ecx,[0xe0ff90]; call 0x86ca10`. So ecx = the ENTITY (it is passed on as 0x86ca10's stack arg; 0x86ca10 is `ret 4`). Result 0 for null or [ent+4]==0, else pool-index based +1 with a sign test on a per-slot word (stale gives 0). The "one disassembly check" the report asked for is done: ecx = entity. (H)
- 0x8ccde0: cdecl (plain `ret`), wraps 0x796ff0 -> 0x40a880 -> [obj+0x60], 0 when the lookup fails; not hashed. That the generation check lives inside 0x40a880 was not read (M); the 0 on failure is read (H).
- Gates: 0x6724e0 `cmp [S+0xb0],0; je bail` at 0x67259a (S = [tactic+4]); 0x85ece0 at 0x85ed1d; 0x616480 needs bit0 and bit 0x10 set, bits 0x4, 0x40, 0x200 clear (also inlined at 0x85ed2c..43). (H)
- Candidate array stride 0x14, entry +0 flags, +4 entity, +8 type: matches 0x4c75f0 and the type tables. (H)
- No-winner clear = SetHolder(0) at 0x767f8a, reached from `test ebx,ebx; je 0x767f77` at 0x767eb9. Winner write at 0x767eee. Bit 4: `or [esi],4` 0x767998 / `and [esi],~4` 0x76799d from the 0x5706a0 result. (H)
- Hashed status (klranges.h). HASHED (calling is fine, no detour): 0x767510, 0x8bd420, 0x6ece90, 0x4880d0, 0x4c75f0, 0x85ece0, 0x616480, 0x5706a0, 0x582fb0, 0x584150, 0x7b48f0, 0x8b3650, 0x5a3430, 0x85f6c0, 0x882470. NOT hashed: 0x8ccde0, 0x6724e0, 0x7834e0, 0x4f6fb0, 0x7f6850. (H)
- MarkSeen 0x4880d0 takes the entity POINTER (stack arg, ecx = B). It sets [B+0x184]=1 (0x4880de), meaning "force a full rescan on the next 0x767510 call". When S's current holder entity [S+0xac] equals the arg it also ORs 1 into [S+0xa8], sets [S+0xc0]=1 and sets/clears flag 0x80. (H)
- 0x767510 control flow: with arg 0, [B+0x184]==0 and now < [B+0x180] it takes the QUICK path (0x767574..0x767675): returns at once if the holder handle is 0, else rewrites only the flags dword (0x200 recomputed, 0x4 / 0x10 carried over; store at 0x76762e). Otherwise (0x767678): [B+0x180] = now + 0x400, rescan, winner or clear. So a raw holder write survives until the next full scan (>= 0x400 ms, or immediately after any MarkSeen). (H)

### Refuted / corrected
1. WRITER LIST INCOMPLETE. All 13 direct SetHolder callers (full-.text sweep) and what they are:
   - 0x767eee, 0x767f8a: 0x767510 (B = ecx, S = [B+0x154]).
   - 0x4f4706, 0x4f4a0a, 0x4f4ce7: the ZAttackTarget mode-B code (range 0x4f0000..0x4f6000, HASHED). MISSED by the report; each does `lea ecx,[eax+0xa8]`.
   - 0x4f7062 (func 0x4f6fb0, UNHASHED): a clean stock "nearest player" setter, see below. Not "unrelated".
   - 0x58300f (func 0x582fb0): stock SetTargetHandle(handle), thiscall ecx=S, `ret 4`, reached from the message dispatcher 0x7b48f0 (case at 0x7b4920).
   - 0x5844c2 (func 0x584150): message handler, holder = 0x6ece90 of an event entity, called from the same dispatcher (0x7b4990). The "PTR 0xce301d" data xref is an unaligned false hit.
   - 0x7b495e: inline case of the dispatcher 0x7b48f0 (handle from the message, flags ptr 0x168e35c, then |=1, [S+0xbc]=now, 0x6f1080(0)).
   - 0x78351a (func 0x7834e0, UNHASHED): B::ForceTarget(handle, float), see below. Callers 0x5a3461 (func 0x5a3430, reads its target entity from [this+0x14]; a ZAttackTarget-style goal, class not named) and 0x60fe75 (func 0x60fd40).
   - 0x7f05a6 (func 0x7f0570): thin wrapper on `[obj+0x77c]+0xa8`, callers 0x5d07ea and 0x8f9986; object with an S pointer at +0x77c (GUESS L: the player controller).
   - 0x772934, 0x7729da (func 0x7726a0): the holder is at [edi+0xd0], NOT S+0xa8. A different class; the report listing it as a soldier writer is wrong.
   - Clear 0x8b3650 callers: 0x4f7079, 0x5f4c3a, 0x5f4cb4, 0x608337, 0x772b1b, 0x7c034c, 0x7e0c42, 0x8fd4ce (unclassified, mostly other classes).
   - Flags-only writers the report lacks: MarkSeen 0x488142, 0x488149, 0x488172, 0x48817a (bits 1 and 0x80, byte +0xc0); quick path 0x76762e; bit 0x10 near 0x767a9b.
   - "Only SetHolder writes the handle" is PLAUSIBLE, NOT PROVEN. A sweep for raw `mov [reg+0xb0]` hits hundreds of unrelated sites (ctors, property resets) and cannot be filtered statically to ZSoldier.
2. "Flags from 0x168e35c is the exact source of the online zeros" is WRONG as worded. 0x168e35c is never written in .text (only pushed as an address at 0x4f704f, 0x583001, 0x5844af, 0x767f7d, 0x7729d3, 0x7b4950; static value 0) and with handle 0 SetHolder never reads it. The online zero comes only from "no winner -> SetHolder(0)". Consequence: every stock one-shot setter (0x582fb0, 0x584150, 0x4f6fb0, the 0x7b4940 case) leaves flags = 0 | 1 = 0x01, bit 0x10 NOT set, so a holder set that way can never pass the fire test.
3. "A winner always passes a handle" is wrong for entry type 0. Jump table 0x768024 = {0x767ec9 (ecx=0), 0x767ecd ([e+4] then +0x40), 0x767ed5, 0x767ed5}. Type 0 gives handle 0 even with a winner; type 1 stores the handle of [entity+0x40] (a controller's body); types 2 and 3 the entity itself.
4. 0x85ece0 gate order was mis-stated. Real order: (a) [S+0x4fc]==0 and mode [S+0x88]==1 -> returns 0 (0x85ece6..f6); (b) now >= [[S+0x40]+0x698]+0x800; (c) 0x6d9eb0() true; (d) [S+0xb0]!=0; (e) flags mask. With bs41's mode 1, NoCover needs [S+0x4fc]!=0 as well.
5. "7f6850 is true only in Arcade" is UNVERIFIED as written. 0x7f6850 reads the mode object [0x168e598]: [+0x54] values 0,1 -> test [+0x5c]==4; 2,3 -> false; above 3 -> test [+0x5c]==4. 0x863a60 (the "is network" test) is a sibling that reads [+0x54] only. 0x5706a0 calls 0x863a60 first and 0x7f6850 only when that is false (0x570842..51); the other branch uses the player-record bytes +0x2723/+0x2727. Both branches can set bit 4 as far as read; bs41's "bit 0x4 only in Arcade" is empirical only. Separately, the tactic objects (ZCloseIn at [S+0x590]) are built in the ctor only when 0x7f6850() is true (0x6ab57c) and the team ebx is 0 or 2 (0x6ab585..8c); see re/arcade_brain_online_1102.md for the shadow-rules swap. Precondition for any approach lever: log [S+0x590] != 0 for the marked bot.
6. Cause of the online zero. Hypothesis 1 is the best one and has direct evidence the report did not cite: the HolderFix header in klbrain.c (bs20, before LosGate existed) says the human holder "sat at 0x05" online, so a human DID win the holder online when Sense/MarkSeen fed it. bs39..bs41 have LosGate on, which makes Sense skip blocked humans; B's array then has no human, 0x767510 finds no winner and clears. So the zero is most likely CAUSED by LosGate, not by a stock online defect (M, not proven). A LosGate-off sample of [S+0xb0] with the same probe decides it. Hypotheses 2 and 3 stay open.
7. CloseIn does not check the flags. The whole body 0x6724e0..0x672778 has no read of [S+0xa8] (only +0xac and +0xb0) and no call to 0x616480. This CONFIRMS the premise of the report's "a flags value that blocks firing while CloseIn passes" (H). Other CloseIn gates the report did not list: tactic timer [tactic+0x14] (bail while now < timer, 0x672505), vcall S+0x84 compared with [[0x168d7c0]+0x108] (0x6725a9..c9), 0x4087f0(entity [S+0xac]) against [S+0x6a8] (0x6725d9..f4), 0x8a2e50 against a constant, 0x651060 / 0x76ca60 path checks. A valid holder is necessary, not sufficient.
8. Option A (MarkSeen) is NOT endorsed. It re-feeds the entry LosGate removes, the human must still win slot 111, and it reopens the bs38 through-wall fire; MarkSeen does not control the 0x10 bit either.
9. The Option B flags value is wrong. The report's own comment says 0x11 = bit0 + bit 0x10 with 0x4 clear, which is exactly the value that PASSES 0x616480 and lets NoCover 0x85ece0 fire, the opposite of the intent while the human is blocked. Use 0x01 (what every stock setter produces) or 0x15; both fail the fire test and both pass CloseIn.

### Stock setters worth knowing (new)
- 0x4f6fb0 (thiscall ecx=S, `ret 4`, UNHASHED): loops the player array [[0xdd265c]+0x828 .. +0x898) (28 slots), skips entities with bit 10 of [[e+4]+0x3c] set or where 0x6a88f0(e) is true, takes the nearest by 0x4087f0 under 2000.0 (double at 0xb3fbe0), then SetHolder(0x6ece90(e), &0x168e35c) and `or [holder],1`; with none (or state [[S+0x55c]+8] 0 or 4) it calls Clear 0x8b3650. Seven callers (0x45aa00, 0x4fc7e0, 0x60c010, 0x7f4790 x2, 0x80e680, 0x844e80). GUESS: that the traitor bot itself is not in that array, and what 0x6a88f0 means (tests flag 0x40000 at [e+0x438] and state [[e+0x2940]+0x24]; looks like "unavailable").
- 0x7834e0 (thiscall ecx=B, args handle, float, `ret 8`, UNHASHED): clears [B+0x184], needs the entity in B's array (0x4c75f0 returns the entry or 0, else NO-OP), then SetHolder(handle, &entry.flags), i.e. it copies the ENTRY flags, then sets [B+0x180] from the float (semantics GUESS). Useless while LosGate keeps the human out of B.
- 0x582fb0 (thiscall ecx=S, handle, `ret 4`): flags 0|1, [S+0xbc]=now, then 0x6f1080(1), which sends message 0x3c with the handle to the team ([S+0x4f4]) and notifies: a visible side effect. Avoid.

### Endorsed lever
Option B, corrected. Default off, no detour, host game thread, only for a marked bot whose human target is LOS-blocked and which is in the approach phase:
1. H = nearest human body (entity pointer; the object HolderFix reads from [S+0xac], vtable 0xbb45f4).
2. handle = 0x6ece90 with ecx = H (confirmed). Require handle != 0 and 0x8ccde0(handle) == H.
3. fl = 0x00000001 (NOT 0x11; 0x15 also acceptable). Call SetHolder 0x8bd420 with ecx = S+0xa8, args (handle, &fl); callee pops 8.
4. Re-apply every host tick: a full scan wipes it ("no winner -> SetHolder(0)"); the quick path between scans keeps handle and flags.
5. Also needs [S+0x4fc]!=0 and [S+0x6fc]==0 while Defend is current (so list A with ZCloseIn is walked, per re/approach_lever_1104.md) and [S+0x590] non-null.
6. When the human becomes LOS-clear, stop writing (and let the next scan or HolderFix take over) so the stock fire path resumes.

Cheaper alternative to test first: call 0x4f6fb0 with ecx=S once per tick during the approach phase. Same flags result (0x01), engine code only; nearest player within 2000, not LOS-aware, so it may pick the wrong human (GUESS). Not endorsed over Option B because its array semantics were read, not traced.

Probe additions before relying on either: per sample log [S+0xb0], vtable of [S+0xac], flags, whether 0x8ccde0([S+0xb0]) == [S+0xac], [S+0x590], and the result of the CloseIn eval 0x6724e0 (probe id 31 already counts calls). Run once with LosGate off to settle item 6.
