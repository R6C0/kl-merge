# Traitor bot: how a human becomes a target candidate (sense side), kl2.exe 0490, 2026-11-03
Static only. Anything not read from code is marked GUESS. Nothing run, patched, committed.

## Verdict
The hole is a TEAM-MASK FILTER upstream of slot 111, not the score and not the sight system.
Every path that puts a candidate into the soldier's known-target list (`B::AddTarget`, 0x7bd720, ret 4, B = [soldier+0x698])
first tests the soldier's enemy-team bitmask against the sensed entity's team:
    cl = [[ent+0x54]+4]            ; entity team index
    test [[[soldier+0x40]+0x54]+0xc], 1<<cl   ; soldier's team record +0xc = enemy-team bitmask
    je -> drop (no AddTarget)
Callers: ZSoldier slot 105 0x5a8140 (test 0x5a8166-0x5a8180, AddTarget 0x5a8237); ZSoldier slot 1 0x608050 case 0x59
(0x60840e-0x60843a, AddTarget 0x60844a); slot 96 0x8473a0 (AddTarget 0x8478ba, its own team gate at 0x84784d-0x84785d:
team index 0 or 2 skips a side branch; the add itself is gated by `[ebp+8]` non-null and a local byte == 0, not by the mask - GUESS on meaning).
Humans and crew bots are both on team 2 in online FA, so a human is never in a team-2 bot's enemy mask: slot 105/1 drop it,
slot 113's candidate loop (0x767510, loop 0x7678a8) never sees it, slot 111 (0x882470) is never called for a human.
That matches bs11-bs13 ("marked soldier X scored human Y" never logged).

## Questions
1. 0x4801a0 (ZCheckVisible::RefreshTarget(byte targetIdx), thiscall ret 4; singleton [0x1535c70], vtable 0xba7ae4):
   for each observer i < [this+0x40], if byte [this+0x40bc+targetIdx+i*0x12c] & 0x80 (currently seen) -> 0x4af8c0(i,idx,1,1)
   which sends sensor message 0x805/0x806 through the observer's [vtable+0x120]. It only re-fires for targets ALREADY seen. Pure sight refresh.
2. Setter 0x70f770: `mov [esi+0x2726],al`; if 0x7f6850 true -> 0x4801a0([esi+0x6c]) else ret.
   0x7f6850 = ([0x168e598]+0x54 mode <=3 via jump table 0x7f6874, else true iff [+0x5c]==4). Online role 2/3 -> false (prior doc), so
   online the setter changes the byte and does not refresh sight at all. Even offline it only re-fires sight events; it does not touch the team mask.
3. Lists: (a) sense manager target table [0x1535c70]+0x12ae0 stride 28 (flag word +0x18), per-observer visibility bytes +0x3c+idx (0x80=seen);
   (b) per-soldier B (size 0x194, ctor 0x7758c0, B+0x154=soldier): known targets count [B], 10 entries x 20 bytes from B+4, ally list count [B+0xcc] at B+0xd0 (built by 0x59a5d0);
   dirty flag [B+0x184]; AddTarget notifies allies via [vtable+0x1a0], and for ZFFPlayer class mask 0x1548c7c sets it dirty. (c) team record at [entity+0x54]: +4 team index, +0xc enemy-team bitmask.
4. Offline Arcade: how a human becomes hostile to a marked bot is NOT visible in this sense path. rec+0x79 bit 2 is not read by any sense/AddTarget code I found;
   the only readers stay 0x882470 (gate 0x882614) and 0x5706a0 (0x570a12). So offline the human must reach the list either through the team mask
   (writers of [team+0xc] not located - OPEN) or the body bytes +0x2723/+0x2726 changing the relation elsewhere (GUESS). The 0x6a1c40 friendly-fire-float route (prior doc) is the second known road.
5. Online (role 2, mode 4): same code, same team test. The only online difference found is 0x7f6850 false (no refresh after the setter). Not gated off.
6. Remote client body class on host: NOT verified here. GUESS: ZFFPlayer 0xbb45f4 for host and remote bodies alike (mask 0x1548c7c is the ZFFPlayer class mask used in AddTarget's dirty branch); same lists, same team 2.
7. Writers of [team+0xc], entity id field for AddTarget's arg: not found in the time spent (OPEN).

## Smallest lever (no code patch)
A. Preferred: per-soldier call of the existing `B::AddTarget` (0x7bd720, thiscall, ecx=[soldier+0x698], push id = the human body's entity id as used by 0x8ccde0(id) in 0x5a8140), from the game thread, for each live human body on the host, for each marked bot, once per ~0.5 s (list holds 10 x 20 bytes; check the count at [B] and for duplicates first - GUESS that AddTarget dedups). Mirrors what slot 105 does after its gate. Id source: the arg 0x5a8140 receives (push of `[edi+0x10]` in 0x608050) = entity id; read the human body's id from the same field (OPEN, verify by reading a logged slot-105 call).
B. Alternative: private-vtable wrap of slot 105 (0x5a8140) for the marked soldier: if the sensed entity is a human body, run the post-gate tail by calling AddTarget directly (skips the mask test). Wrap slot 1 case 0x59 the same way. Heap-vtable, hook-safe, no hashed code touched.
C. Heavier: give the marked bot a private team record copy with +0xc | (1<<2) via its [soldier+0x40]+0x54 pointer. Risky: that record is shared by the team (GUESS), so a copy would need the soldier's pointer swapped and kept in sync; not recommended.
After A/B, slot 111 (klbr_w_score) should start logging, then slot 15/113/114 get reached.
