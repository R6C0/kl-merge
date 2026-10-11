# The 'melee' that is not one: a soldier's point-blank rule (kl2 0x8c62e0), what it costs, and keys for it

Track 'melee-write', 2026-10-11. OFFLINE: the game was not started, nothing was written under the Dog Days folder, no
existing file of the repo was edited. New files: this note and `re/melee_damage.patch`. Scratch (scripts, listings,
the changed copy of the hook, builds, an off-game harness): `G:/kl_scratch/melee_write/`.
**NOTHING OF THE PATCH HAS RUN IN THE GAME.** It compiles (SHIP and TEST) and passes an off-game harness that enters
the wrapper through the game's own call site bytes (section 8.4) - that is all.

How each statement is marked:

- **M** = MEASURED here: own disassembly of kl2.exe build 0490 (`d.py <from> <to>`, scans `q.py refs | callers | vt |
  hashed`, both in the scratch folder) - the address range is given; or own count on files (`lvl.py`, `fit.py`,
  `kills.py`).
- **R** = READ: the file and the place are given.
- **A** = ASSUMED: the reason is given.
- **REP** = reported by the four readers / the reconciler / the three skeptics of this job and NOT re-read for this
  note. Not evidence; kept only where the argument does not rest on it.

## 0. Short answers

1. **It is not close combat.** The damage is made by `0x8c62e0`, a plain member of the soldier's FIRE TASK (its only
   callers are two sites of `ZFireWeaponTask@CPPScript` slot 2). At every step of a burst (0.1 .. 0.2 s), while the
   soldier's target is within **160 units** (1.6 m, node to node, height counts), it sends the target one
   `ProjectileHit` of the soldier's own gun whose hit record carries the damage scale **100.0** and the head bone.
2. **The dial DOES scale it.** The victim's ordinary bullet routine multiplies by the record's scale AND by the Arcade
   who-shoots-whom float. The hit is one bullet of the guard's gun x 100: with `CopToYou=0.02` a Type 79 guard still
   costs 72.0 x 1.05 x 100 x 0.02 = **151.2** a step - the log's number, to the decimal. Without the 0.02 it is 7,560.
   The lead's premise ('the dial does NOT scale it') is the one thing refuted; his leads 126 x 1.2, 168 x 0.9,
   550 x 0.275 fit one gun at one health maximum only and are refuted by the other guns (758.6, 582.8, 449.2, 154.2,
   147.8, 113.4, 81.6) and by the unchanged 151.2 at maximum 5500.
3. **The float:** hit record +0x18 = fire task +0x30, written with the constant `[0xb5c050]` = 100.0 at `0x8c63aa`
   immediately before the send. The constant is hashed .rdata with 138 users; the record is heap, rewritten at every
   call. **No plain float write can scale this hit alone.**
4. **The key that was built** (`re/melee_damage.patch`, klbalance.c + the sample ini): `PointBlankToYou`,
   `PointBlankToCrew`, `PointBlankToCop` in `[Balance]` = what stands in for the 100, by victim - 'how many ordinary
   bullets of his gun one step is worth'; 100 = the game's own (the steps are then only seen and logged). Data writes
   only: the database object's vtable pointer (a private copy with slot 19 wrapped, the technique klchar.c runs live)
   and the one float of the record. Same limits as the six factors. Section 7 says why this option and not the
   others; section 8 what exactly it does.
5. **What an AI heister loses** is the same product with the body part whole (x 1.2) and `CopToCrew`: at 0.05 a
   Type 79 step is 432 of his 252. The logged 236 / 246 / 202 / 115 are not sizes of a hit: each is exactly the
   health the bot still had (section 4.3).
6. **The true close combat** (ZFFActionCloseCombat slot 4, 50.0 flat, no Arcade factor) is another path and matches
   none of the logged numbers (section 6).

## 1. The question and the evidence

The session that tunes the balance (2026-10-11): in Arcade on the grafted maps a guard at arm's length does damage
'that the hook's damage dial does not scale'; which routine, which float, so that a `[Balance]` key can scale it.

**R** `<work>/build/klhook/live/K2b_DM03_wall_log.log` (587 lines; the bank, a scripted walking player; archive
`f03\f03_main.zip` 200,889,112 bytes, hash 98b35c56 - by its size the one in `<work>/build/w_tabT/KLExpansion/Maps/DM03`):

    line  15  balance: on; Log=2 Risk=2 Ramp=0 ... police->crew 0.05 crew->police 1.00 police->you 0.02 ... crew->you 0.02 ...
    line 302  balance: the damage table of the tuning object 0e3953b0 is what the game's code builds; campaign difficulty option 1
    line 303  balance: stock, Arcade level  1: police->crew 0.01  crew->police 3.00  police->you 0.10 ...
    line 360  balance: your health set: maximum 401.5 (the game gave 550.0) ...
    09:49:41.478 .. 42.042   you lost 1.4, 1.4, 1.5, 1.5, 1.5, 1.5, 1.5        (350.5 of 401.5 after the last)
    09:49:42.540   balance: you lost 151.2 (199.3 of 401.5)
    09:49:42.728   balance: you lost 151.2 (48.1 of 401.5)
    09:49:42.852   balance: you lost 30.2 (17.9 of 401.5)
    09:49:43.040   bots: record 0 (you): dead
    09:49:43.868   pos tick: me #7 (-392, 440, -5679) heading 100

**R** the picture `<work>/research/shots/K2b_DM03_wall_log_98s.png`: the staircase, the panel 'Killed by: The police'.
**R** `K1_DM03_wall_dry.log`, `K2_DM03_wall.log` beside it: the same death (09:24:32.571, 09:28:42.416); both have
`[Balance] Log=1`, so no loss lines.

## 2. The routine: 0x8c62e0, the fire task's point-blank rule

**M** `0x8c62e0..0x8c6432`, whole (`f_8c62e0.txt`). No pointer to it anywhere in the image (`q.py refs 8c62e0`: 0
places), two rel32 callers `0x7c0748` and `0x7c0a14`, both inside `0x7c02b0` = slot 2 of the vtable `0xbd0bd4`, RTTI
`ZFireWeaponTask@CPPScript`. `this` (esi) = the task; `[task+4]` = the soldier S; `[S+0x40]` his actor,
`[S+0xac]` his target, `[S+0xb0]` 'has a target'.

    008c62ec  cmp   dword ptr [eax + 0xb0], 0            ; eax = S: no target -> return
    008c62fc  call  0x4d2750                             ; ecx = [S+0x40]; false -> return   (a gate on the actor, section 9)
    008c6313  call  0x4087f0                             ; ecx = S, argument [S+0xac]: the distance
    008c631b  fld   dword ptr [0xb62260]                 ; 160.0
    008c6321  fcomp dword ptr [ebp - 4]                  ; the distance
    008c6326  test  ah, 5
    008c6329  jnp   0x8c642e                             ; 160 < distance -> return
    008c6378  lea   eax, [esi + 0x18]                    ; THE HIT RECORD = task + 0x18
    008c637b  lea   ebx, [esi + 0x38]
    008c637e  mov   dword ptr [eax], ebx                 ; +0x00 = the trace block, task + 0x38
    008c638d  call  0x86a130                             ; ecx = [S+0x40]
    008c6395  mov   dword ptr [esi + 0x20], eax          ; +0x08 = what it answers (the gun: REP)
    008c639e  fstp  dword ptr [esi + 0x2c]               ; +0x14 = the distance
    008c63a1  fld   dword ptr [0xb5c050]                 ; 100.0          bytes d9 05 50 c0 b5 00
    008c63a7  mov   dword ptr [esi + 0x24], edx          ; +0x0c = the attacker's actor [S+0x40]
    008c63aa  fstp  dword ptr [esi + 0x30]               ; +0x18 = THE SCALE
    008c63ef  push  0                                    ; the send's third argument
    008c63f4  push  edx                                  ; the send's second: the record (edx = [ebp-8] = task+0x18)
    008c63f5  mov   dword ptr [esi + 0x60], 7            ; trace +0x28 = bone id 7
    008c63fc  mov   eax, dword ptr [0xdd2640]
    008c6401  mov   ecx, dword ptr [eax + 0xac]          ; the database object
    008c6407  mov   eax, dword ptr [ecx]
    008c6409  mov   edx, dword ptr [eax + 0x4c]          ; its vtable slot 19
    008c640c  mov   esi, dword ptr [edi]                 ; edi = the target: its vtable
    008c640e  push  0x50
    008c6410  push  0xb22648                             ; "ff2\scripts\soldier\fireweapontask.cpp"
    008c6415  push  0
    008c6417  push  0xb63d18                             ; "ProjectileHit"
    008c641c  call  edx                                  ; name -> id
    008c641e  mov   edx, dword ptr [esi + 0x120]
    008c6424  movzx eax, ax
    008c6427  push  eax
    008c6428  mov   ecx, edi
    008c642a  call  edx                                  ; target->vtable[+0x120](id, &record, 0)

- **The distance** (**M** `0x4087f0..0x408836`, `0x6499b0..0x6499f1`): two positions by `0x7b3020` (the soldier's
  actor node and the target's node), the root of the three squared differences (`call 0xa8d554`). 3-D: the K2b site
  is a staircase.
- **The step** (**M** `0x7c0660..0x7c0748`): flags of `[S+0xa8]` (bit 0 and 0x10 set; 4, 0x200, 0x40 clear),
  `0x7c0697 call 0x4d2750`, burst time `0x7c06ad call 0x8c1830`; then a random number of the engine's generator
  (`0x7c06c9..0x7c06ec`), `0x7c06f2 fmul qword ptr [0xb59200]` (1/32768), `0x7c06fe fmul qword ptr [0xb724a0]` (0.1),
  `0x7c0704 fadd qword ptr [0xb4e7e8]` (0.1), cut to the burst time left (`0x7c070d..0x7c071e`), `0x7c0729 call
  0x630b50` (the wait), `0x7c0730 call 0x55b9f0`, `0x7c0748 call 0x8c62e0`. So once every 0.1 .. 0.2 s, shorter at a
  burst's end. The second site `0x7c0a14` stands in a second loop of the same shape (**M** the call list of
  `0x7c07d0..0x7c0a64` only; what that loop is for: REP 'bursts at up to two other targets').
- It fires nothing and stops nothing: whether the gun's real projectiles also land inside 160 units is NOT known
  (section 9). 160.0 at `0xb62260` has 12 users, 100.0 at `0xb5c050` has 138 (**M** `q.py refs`).

## 3. The receiving side

### 3.1 Dispatch (both classes)

**M** vtable slot 72 (+0x120) is `0x787250` in ZFFPlayer (vtable `0xbb45f4`, 427 slots) and in ZFFActor (`0xbb3bac`,
447 slots). `0x787250..0x787284`: `0x787267 call edx` = slot 89 (+0x164) with (id, record); after it the same record
goes to the object's listeners (`0x78727f call eax` = [vtable+0x11c] with 0x20).

- ZFFPlayer slot 89 = `0x5c7930`: `0x5c7cf2 cmp eax, dword ptr [0x1548d10]` -> `0x5c7d09 call edx` =
  [vtable+0x6a0] = slot 424 = **`0x4db580`**. (**M**; that word 0x1548d10 is the id of "ProjectileHit": REP - the
  same word is what the execution shot sends, `0x60d7fa`, **M**.)
- ZFFActor slot 89 = `0x6050a0`: `0x6050f3 cmp eax, dword ptr [0x1547b68]` -> `0x605108 call edx` = [vtable+0x69c] =
  slot 423 = **`0x61a980`**. (**M**)
- `0x4db580` and `0x61a980` stand in the image once each (their vtable entry) and have no direct caller (**M**).

### 3.2 The player as victim: 0x4db580 (**M** `0x4db786..0x4dbb57`, `f_4db580.txt`; ebp = the record, esi = the player)

    004db789  movzx eax, byte ptr [edx + 0x28]           ; the trace's bone id (7)
    004db790  call  0x5575a0                             ; -> bone index (REP: through the skeleton's id table)
    004db7a9  mov   cl, byte ptr [edi + eax + 0x3f]      ; the bone's body part
    004db7d9  and   eax, dword ptr [0x150cce4] / cmp eax, dword ptr [0x150cce0]   ; the attacker's class is ZActor (R re/balance.md 1 a)
    004db7eb  cmp   al, 3 / cmp al, 2 -> 004db7f3  mov byte ptr [esp + 0x10], 1     ; part 2 / 3 becomes 1
    004db7ff  call  0x572f60                             ; the body part's float m
    004db808  fld   dword ptr [0xb38f38]                 ; 4.0: m = min(m, 4.0)
    004db82f  fsub  st(1), st(0) / 004db835  fmul qword ptr [0xb293f0] / 004db83b  faddp   ; 1 + (m - 1) x 0.25
    004db897  call  eax                                  ; gun template [vtable+0x2f0] = 0x46ef60(weapon, [rec+0x14])
    004db899  fmul  dword ptr [esp + 0x54]               ; x the softened body part
    004db8a2  fmul  dword ptr [ebp + 0x18]               ; x THE RECORD'S SCALE           bytes d8 4d 18
    004db997  fld   dword ptr [eax + 0x704]              ; eax = [attacker+0x77c], his soldier: x S
    004db9d1  call  0x8b8050 / 004db9d6  fmul dword ptr [esp + 0x44]                 ; x the Arcade float
    004dbabd  cmp   dword ptr [0xcef604], 0 / 004dbacc  call 0x60db40 / 004dbad1  fmul   ; x one more factor (below)
    004dbad9  cmp   dword ptr [esi + 0x2778], edi        ; the limiter (below)
    004dbb51  mov   dword ptr [esi + 0x2778], edi        ; the last attacker

- **The gun** (**M** `0x46ef60..0x46f205`): at a distance not over the first range `[gun+0xd4]`:
  `fld [ammo+0x84]` x `[gun+0xe4]` (0x46ef89) x `[gun+0x13c]` when the gun's owner is a ZActor (0x46efec) x
  `[gun+0x144]` in mode 4 (0x46f07b). The four ranges are multiplied by 100.0 when the template is loaded
  (**M** `0x6eaa2e..0x6eaa92`): a '5 m' first range is 500 units, the smallest of any template in the four builds
  is 3 m = 300 (**M** `lvl.py`), so 160 is always inside the first band.
- **The body part** (**M** `0x572f60..0x572fce` + its jump table `0x572fd4`): part 1 = `[0xcdeff8]`, part 0 =
  `[0xcdefe4]`, int3 for a part over 9. `0x45d594 / 0x45d59a` copy tuning+0x418 into 0xcdeff8, the tuning
  constructor stores 1.2 there (`0x528741 fld dword ptr [0xb255b0]` / `0x528747 lea ecx, [edi + 0x418]`). So an NPC's
  'head' hit is a part-1 hit = 1.2, and 1 + (1.2 - 1) x 0.25 = **1.05** on the player. On the builds of the runs
  bone id 7 is the bone "HEAD" with body part 2 on every skeleton that has a bone 7 at all: 25 of 98 skeletons on
  the bank, 24 of 97 / 96 / 92 on Retomoto, the diner, the park (**M** `lvl.py` on `w_tabT`; the reconciler's '27'
  was a slip - his own listing adds up to 25).
- **The Arcade float** (**M** `0x8b8050..0x8b80d5`): level byte `[[rules+0x5f8]+0x45]` clamped 1..11, record
  `[0x168d7c0] + 0x6ac + L * 0x70`; the shooter's team `[[actor+0x54]+4] == 2` (Ally) -> `fld [ecx + 0x10]`, else
  `fld [ecx + 8]`; the two cases exchanged for a police player (`[player+0x2723]`). It has three callers
  (`0x458946`, `0x4db9d1`, `0x743455`). **This is where the dial is in the product.**
- **One more factor, missing from the reconciled account** (**M** `0x4dbabd..0x4dbad5`, `0x60db40..0x60dbf2`,
  `0x4bcb99..0x4bcbdb`): `[0xcef604]` is 1 in the image, so `0x60db40(gamedata)` is called at every bullet hit on
  the player. It returns 1.0 unless `[gamedata+0x4cf4]` holds a time, the session mode is not 2 and the session is
  not online; then 1 + (5.0 - 1) x min(1, seconds since then / 50.0). The time is set only while the object
  `[gamedata+0x4cf0]` exists with byte +0x576 != 1 and cleared otherwise. In the runs it was 1.0 (every number
  fits without it). **A** that no grafted Arcade level has that object (REP: the campaign's buddy).
- **The limiter** (**M** `0x4dbad9..0x4dbb57`): another attacker than `[player+0x2778]`, or the last hit
  (`[player+0x2774]`) 0x800 ticks (2.0 s at 1/1024 s) or more old -> the sum `[player+0x277c]` becomes 0 and THIS hit
  is not counted. Else: `fld [edx + 8]` (maximum) `fmul qword ptr [0xb794c0]` (0.75), compared with the sum; sum >
  0.75 x maximum -> `fmul qword ptr [0xb5adf8]` (x 0.2); then sum += the hit as dealt.
- **From the product to the health** (**M**): `0x7e1709 call 0x863a60` (false while `[session+0x54]` is 0 or 1 -
  the sessions klbalance.c acts in) -> `0x7e182c`
  [vtable+0x69c] = `0x458880`. There the damage slot has three writers besides the load at `0x4588bc`: x tuning+0x1fc
  only in movement state 0x12 (`0x4588d4..0x4588e9`), x 10.0 only with `[player+0xd5c]` (`0x4588ed..0x458900`), x 0.1
  only in session mode 1 or 2 (`0x458dd4..0x458e32`; not Arcade - the reconciled account had left the mode test
  out). `0x458e9b fld / 0x458ea0 fchs / 0x458ea8 call 0x6e3400`; there the Arcade block `0x6e3486..0x6e35f8`
  changes the delta only for a ZFFPlayer attacker (edi = 0 for an NPC: every branch falls to `0x6e35fc`), and
  `0x6e361a call 0x8a7c60`: `0x8a7cfb fld dword ptr [esp + 0xc]` / `0x8a7d02 fadd dword ptr [eax]` / `0x8a7d07 fstp
  dword ptr [eax]` (eax = health object + 4), clamp by `0x6143f0`. `0x8a7c60` has one caller, `0x6e3400` three.
- **A gate that can swallow a hit whole** (**M** `0x458e78..0x458e93`, `0x8da3b0..0x8da4de`): before the health
  change `0x8da3b0([player+0x2948], record)`; when it answers true (and a flag byte of the routine is clear and the
  record's type `[rec+8]` is not 9) the routine returns and the hit costs nothing. It is the down-state controller (switch `[0xceb40c]` = 1 in the image); its
  first test `0x828710` needs among others byte `[gamedata+0x4d38]` != 0. When that holds in Arcade was NOT
  established; in the logs no hit was swallowed (every number is accounted for).

### 3.3 An NPC / AI heister as victim: 0x61a980 (**M** `0x61a980..0x61aa08`, `0x61aab0..0x61ab2a`, `0x61ac20..0x61ad30`, `0x61ae41..0x61b0c9`; ebx = the record, esi = the victim)

    0061ac2e  call  0x5575a0 / 0061ac44  mov cl, byte ptr [edi + eax + 0x3f]        ; the body part of the bone
    0061ac79  ... cmp eax, dword ptr [0x150cce0] / 0061ac8b  cmp al, 3 / cmp al, 2 -> 0061ac93  mov byte ptr [esp + 0x1c], 1
    0061acab  call  eax                                  ; the gun (slot 0x2f0)
    0061acb8  call  0x572f60 / 0061acbd  fmul qword ptr [esp + 0x20]               ; x the body part, WHOLE
    0061acc6  fmul  dword ptr [ebx + 0x18]               ; x THE RECORD'S SCALE           bytes d8 4b 18
    0061acdd  fld   dword ptr [eax + 0x704]              ; x S
    0061ad15  push  ebx (the attacker) / 0061ad18  call 0x591b60 / 0061ad1d  fmul   ; x the Arcade float

- `0x591b60` (**M** whole): an Ally shooter -> `fld [ebp + 4]`, another -> `fld [ebp]` (exchanged for a police
  player), x `[ebp + 0x1c]` for an Ally shooter at another heist stage (re/balance.md 10). One caller.
- A hit of an Ally / Mercenary NPC on an Ally / Mercenary NPC is dropped before the product unless the session is
  Arcade, `[victim+0x774]` != 0 and the local player's byte `[player+0x2726]` is set (`0x61aac1..0x61ab17`; the same
  reading as re/balance.md 10.1): an AI heister's step does not hurt another heister in an ordinary round.
- **The loot part** (**M** `0x61aeb6..0x61b019`, `0x4e84e0`, `0x7cd260`, `0x51c870`): for a victim with a money
  holder `[actor+0x8ec]` the damage is lowered by damage x `[tuning+0x638]` and (int)(`[tuning+0x63c]` x damage) is
  booked as money to drop. The tuning constructor stores 0.0 in both (`0x52a6cd fldz / lea ecx, [edi + 0x638]`,
  `0x52a70b fldz / lea ecx, [edi + 0x63c]`): no change by default. Whether anything writes them later: not read.
- **To the health**: `0x61b02c` [vtable+0x694] = `0x69f900` -> `0x69fa31` [vtable+0x698] = `0x8689c0` ->
  `0x868db8 movzx eax, word ptr [0x1547b74]` / `0x868dcd call edx` (+0x120); the scheduler's table entry `0xd17568` =
  {0x1c, "ScriptDamageInfo"}; ZSoldier@CPPScript slot 1 `0x608050`: byte `[0x608578 + 0x1c]` = 9, jump table entry 9
  = `0x608174`, `0x608184 call edx` = [vtable+0x180] = slot 96 = `0x8473a0` (**M** each of these; that the word
  0x1547b74 is that name's id and the scheduler's own call: REP). In `0x8473a0`: x 0.1 (`0x84763c fmul qword ptr
  [0xb4e7e8]`) or x `[tuning+0x3c]` for a held NPC under conditions not read here (`0x847610..0x847642`); then

      00847785  call  0x539dd0                             ; ecx = the actor: the health (REP: [[actor+0x5fc]+4])
      0084778a  fld   dword ptr [ebp - 0x14] / 0084778d  fmul qword ptr [0xb87940] / 00847793  fsubp st(1)   ; health - damage
      00847795  call  0xa8d330                             ; TO AN INTEGER
      0084779f  test  edi, edi / jge / xor edi, edi        ; not below 0
      0084788e  fild  dword ptr [ebp - 0xc] ... 0084789d  call edx      ; [vtable+0x670] = 0x792bc0 -> 0x61efd0 -> 0061f032 fstp dword ptr [edi]

  So an NPC's health is a whole number after every hit - which is why the bots' losses in the logs are whole.

## 4. The formula and every logged number

### 4.1 The formula

    PLAYER, one point-blank step:   damage = G x Bsoft x 100 x S x R       then the limiter (x 0.2 or not)
    NPC / AI HEISTER:               damage = G x B     x 100 x S x F       new health = (int)(health - damage), not below 0

- G = the gun at a distance inside its first range, NPC shooter, Arcade: ammo `[+0x84]` x gun `[+0xe4]` x `[+0x13c]` x
  `[+0x144]`. **M** with `tools/kl_map_ai.guns` on the four builds of `w_tabT` (`lvl.py` -> `lvl.txt`):

  | gun | G | on you at police->you 0.02 (x 2.1) | at stock level 1's 0.1 | at Risk=2's 1.0 | on a heister at police->crew 0.05 (x 6) |
  |---|---:|---:|---:|---:|---:|
  | SMG_Type79 | 72.0 | **151.2** | 756 | 7,560 | 432 |
  | SMG_HK_sp89 / SMG_MPi69 | 70.4 | **147.84** | 739 | 7,392 | 422.4 |
  | SMG_Type05 | 73.44 | **154.224** | 771 | 7,711 | 440.6 |
  | Rifle_AK74 | 64.8 | 136.08 | 680 | 6,804 | 388.8 |
  | Rifle_FN_SCAR | 54.0 | **113.4** | 567 | 5,670 | 324 |
  | Rifle_Type81 | 90.9 | 190.89 | 954 | 9,545 | 545.4 |
  | HG_M9Beretta | 213.9 | **449.19** | 2,246 | 22,460 | 1,283 |
  | HG_SigSauer226 | 277.5 | **582.75** | 2,914 | 29,138 | 1,665 |
  | HG_SW_MP45 | 361.25 | **758.625** | 3,793 | 37,931 | 2,168 |
  | Shotgun_Hawk_Bullpup | 38.85 | **81.585** | 408 | 4,079 | 233.1 |
  | Shotgun_Hawk_Police | 40.4 | 84.84 | 424 | 4,242 | 242.4 |
  | Rifle_zastavam85 (the crew's own) | 57.6 | | | | on a policeman at crew->police 1.0: 6,912 |

  (bold = seen in a log.) The bank's 15 armed police carry AK-74 x 5, Type 81 x 3, Type 79 x 2, SigSauer, SCAR,
  Bullpup, MP45, M9.
- Bsoft = 1.05, B = 1.2 (section 3.2). S = `[soldier+0x704]` = 1.0 (**M** the constructor `0x761aec fld1` .. `0x761b1e
  fst dword ptr [esi + 0x704]`; other writers `0x7e261a`, `0x4bcc95`). R / F = the Arcade float.
- A real bullet is the same product with the scale its projectile carries (**M** `0x6f7c20 fld [esi + 0x94]` ->
  +0x14, `0x6f7c2d fld [esi + 0xb8]` -> +0x18; `0x900e19 fld [edi + 0x3c]` / `0x900e1c fstp [esi + 0xb8]`); the logs'
  ordinary hits fit with exactly 1.0. The player's execution shot builds its own record with `fld1` (**M**
  `0x60d7c4..0x60d821`).

### 4.2 The player's numbers (**M** `fit.py` -> `fit.txt`, all logs of the live folder at 11:55: 217 logs then, 8 with 'you lost' lines, 1,479 such lines)

All eight have police->you 0.02. 73 losses of 20 or more:

| | count | |
|---|---:|---|
| one gun's product, to the log's decimal | 58 | Type79 151.2 x 35, sp89 / MPi69 147.8 x 8, Bullpup 81.6 x 5, Type05 154.2 x 4, SigSauer 582.8 x 2, SCAR 113.4 x 2, M9 449.2 x 1, MP45 758.6 x 1 |
| two products in one pass of the hook | 5 | 302.4 (2 x Type79), 163.2 x 2 (2 x Bullpup), 308.4 (2 x Type05), 295.7 (2 x sp89) |
| the limiter | 1 | K2b's 30.2 = 151.2 x 0.2 |
| a product plus 0.1 .. 2.8 of ordinary bullets in the same pass | 8 | 584.3, 155.8, 148.8, 150.6, 150.0 x 2, 149.0, 151.3 - approximate, not exact |
| not explained | 1 | J1_DM09_join 11:12:45.464 'you lost 90.9'. **A**: Shotgun_Hawk_Police 84.84 + one shell of seven pellets of 0.848 = 90.78; not shown |

By log: K2b 3, K2c_DM03_wall_hp 4 (151.2 x 3, 758.6), PB_DM03_board_hp 19 (151.2 x 8 and one 302.4, 582.8 x 2, 584.3,
81.6 x 5, 163.2 x 2), PB_DM06_board_hp 2 (113.4 x 2), J0_DM09_join_oldchain 4, J1_DM09_join 10, B1_DM09_board_gates
31; PB_DM01_board_hp none. (The reconciler's '151.2 nine times' in PB_DM03 is 8 lines + the double; his 'three logs
have loss lines' is eight - the five others were written while he worked or after.)

**K2b line by line.** The guard had hit before: seven ordinary Type 79 bullets 09:49:41.478 .. 42.042 = 72 x 0.9625
x 0.02 = 1.386 twice and 72 x 1.05 x 0.02 = 1.512 five times. The first of the seven starts the chain: the sum is
set to 0 and that hit is not counted. So the limiter's sum is 1.386 + 5 x 1.512 = 8.95 before the first big hit
(whole), 160.15 before the second (whole), **311.35** before the third - over 0.75 x 401.5 = 301.125 - and the third
is 151.2 x 0.2 = **30.24**. Health 350.5 -> 199.3 -> 48.1 -> 17.9 fits; a fourth 30.24 on 17.9 is the 'dead' of
09:49:43.040. Steps 188 and 124 ms apart = the task's 0.1 .. 0.2 s seen through the hook's 50 ms pass. With maximum
5500 (K2c, PB, J0, J1, B1: threshold 4,125) no cut ever shows: B1 has many whole Type 79 steps in a row.

What refutes the other readings: a Type 79 step is 151.2 at maximum 401.5 (K2b) and at maximum 5500 (K2c, PB_DM03,
J0, B1), so nothing proportional to the maximum - not a fall (**M** `0x88aec9..0x88af0f`: x maximum / 100); four
maps, eight guns, each exactly 100 x that gun's ordinary torso hit seen in the same logs (1.512 for the Type 79);
50 / 125 / 80 (the close-combat constants) match nothing.

### 4.3 The AI heisters' numbers (**M** `kills.py` -> `kills.txt`: 31 logs with bot loss lines, 5,812 lines)

31 losses of 60 or more:

| | count | |
|---|---:|---|
| a full 252 in one step | 18 | 17 with the vehicle in state 5 in the log's own crew line = the rules' 1,000,000 for crew left behind (section 6); 1 with the vehicle in state 1 (B1_DM01 06:14:37.748: cause not established) |
| a kill of the REST: the loss equals the health that record's previous line left | 12 | 230, 240, 202, 115, 118, 232, 208, 201, 206, 246, 120, 236 - the lead's 236 / 246 / 202 / 115 are four of these |
| not a kill | 1 | J0_DM09_join_oldchain 11:21:05.916 'record 1 (bot): lost 73.0 (63.0 of 252.0)' at police->crew 0.05 |

So the big bot numbers say nothing about the size of the hit: the product on a 252 bot is at least 233 at 0.05
(Bullpup; at HP_DM09's 0.15 at least 699, at T2_DM09's 0.03 at least 140), every such hit is a kill clipped at 0, and
the log prints what was left. The lines before two of the kills are ordinary bullets with the integer cut: PB_DM03
bot 7 goes 252 -> 235 -> 218 -> 201 (three SigSauer bullets of 277.5 x 1.2 x 0.05 = 16.65) and then 'lost 201.0
(0.0 of 252.0)'. **Not shown by any number:** the product on a heister itself (never a remainder), and which of the
twelve rest-kills are this rule (a scripted kill or a blast gives the same line). The one loss that is not a kill
(73.0) cannot be a point-blank step at 0.05 (the weakest gun carried gives 233): a third source, not identified.

## 5. Where each float lives

| float | value | who fills it | who else reads it | hashed (klhook/klranges.h) |
|---|---|---|---|---|
| **hit record +0x18 = fire task +0x30** (heap) | 100.0 for this rule; a projectile's `[proj+0xb8]`; 1.0 for the execution shot | `0x8c63aa`, at every call, before the send | `0x4db8a2` (player), `0x61acc6` (NPC); other receivers of a hit record (vehicles ..: REP); the target's listeners get the same record (`0x78727f`) | heap |
| `0xb5c050` (.rdata float32) | 100.0 | constant | 138 places hold its address, all .text (**M**) | YES (0xb11000-0xb8ac00) |
| `0xb62260` (.rdata float32) | 160.0 | constant | 12 places (**M**; `0x46a16b`, `0x4e95fc` among them) | YES |
| the instructions `0x8c631b` (d9 05 60 22 b6 00) and `0x8c63a1` (d9 05 50 c0 b5 00) | | code | | in NO range (rows 0x8c3000-0x8c6000 and 0x8c7000-0x8cc000: the page 0x8c6000 is between them) - but it is code |
| Arcade record R = `[0x168d7c0] + 0x6ac + L*0x70`: R+0x08 / R+0x10 (`0x8b8050`), R+0x00 / R+0x04 / R+0x1c (`0x591b60`) | the runs: 0.02 / 0.02 / 0.05 / 1.0 / 1.0; stock level 1: 0.1 / 0.1 / 0.01 / 3.0 / 0.5 (**R** K2b lines 303, 315) | the tuning constructor; klbalance.c | one reader each (re/balance.md 10.2) | heap |
| `[soldier+0x704]` | 1.0 | constructor `0x761b1e`; `0x7e261a`; `0x4bcc95` | `0x4db997`, `0x61acdd` (**M**); `0x7a72e7` (REP) | heap |
| `0xcdeff8` (.data) = body part 1 | 1.2 at run time (1.0 in the image) | `0x45d59a` from tuning+0x418 (`0x45c490`, one caller `0x645037` in ZFFGameData slot 1) | `0x572fb0` only | no |
| `0xb38f38` (4.0), `0xb293f0` (0.25): the player's softening | | constants | | YES |
| the limiter: `0xb794c0` (0.75), `0xb5adf8` (0.2), 0x800 ticks; `[player+0x2774]` time, `+0x2778` attacker, `+0x277c` sum | | constants; the three fields by `0x4dbb31..0x4dbb51` at every bullet hit | | constants YES; fields heap |
| gun / ammo templates: ammo +0x84; gun +0xe4, +0x13c, +0x144, ranges +0xd4.. | section 4.1's table | level properties; `0x6eaa10` scales the ranges | `0x46ef60` | heap |
| `0xcef604` (.data dword) | 1 | no writer (2 references: `0x4bcc4e`, `0x4dbabd`) | switches the `0x60db40` factor | no |
| `0xcef5ec` / `0xcef5f0` (.data) | 50.0 / 5.0 | constants, one reader each | `0x60dbb5`, `0x60dbd4` | no |
| health: player `[player+0xa48]+4` (written `0x8a7d07`), NPC `[actor+0x5fc]+4` (`0x61f032`) | 401.5 or 5500 in the runs; a heister 252 | | | heap |
| NOT this damage: `0xce8fcc` (.data) | 50.0 | no writer; 3 readers, all in ZFFActionCloseCombat slot 4 (`0x4995bb`, `0x4995c9`, `0x499827`) | | no |
| NOT this damage: `0xd1857c` (.data) | 80.0 | 2 readers (`0x6571eb`, `0x657263`, ZCloseCombat@CPPScript slot 2) | | no |

## 6. Damage paths the six factors do not touch (with addresses)

The point-blank hit is NOT one of them - it passes `0x8b8050` / `0x591b60` like every bullet. These do not:

| path | what | evidence |
|---|---|---|
| true close combat, an NPC on a player | record {attacker `[action+0xc]`, damage `fld dword ptr [0xce8fcc]` 50.0, `fmul qword ptr [0xb508a0]` x 2.5 when `cmp dword ptr [ecx], 2` on `[[soldier+0x6d8]]`} -> the player's [vtable+0x698] -> `0x7e1700` -> `0x458880` -> `0x6e3400`. No gun, no body part, no Arcade float (`0x8b8050` has three callers, none here) | **M** `0x499570..0x4995f2` in ZFFActionCloseCombat slot 4 `0x499160` |
| close combat, the player on an NPC | health - `fsub dword ptr [0xd1857c]` 80.0, twice | **M** refs; `0x6571eb`, `0x657263` in ZCloseCombat@CPPScript slot 2 `0x656fb0` (the surroundings: REP) |
| crew left behind | once byte `[rules+0x1dc]` == 5 every AI crew record (mask 1 at +0x79) still in play gets a damage record of `fld dword ptr [0xb631b0]` 1,000,000.0 by [vtable+0x694] | **M** `0x74b8b4`, `0x74b8c1`, `0x74b942`, `0x74b96d` in ZGameRulesHeist slot 7 `0x74b6d0`; the logs' series of 'lost 252.0 (0.0 of 252.0)' a second or two apart with the vehicle in state 5 |
| a message that kills the player | health x `fmul qword ptr [0xb3edb8]` (-20.0) straight into `0x6e3400` | **M** `0x5c7bb7..0x5c7bea` (which message: REP) |
| fall | (height fallen - `[mov+0x1f64]`) x maximum health x `[mov+0x1f68]` / 100 | **M** `0x88aec9..0x88af0f` |
| 'DamageInfo'-style messages | ZFFActor `0x6050db` -> [vtable+0x694]; ZFFPlayer `0x5c7d17` -> [vtable+0x698]: explosions, fire, kill boxes, vehicles enter here, after the routines that hold the Arcade float | **M** the two hand-overs; the senders and their numbers: REP |
| physics impact on the player | `0x60d1c7` calls `0x6e3400` directly, past the bullet routine | **M** the caller list of `0x6e3400` only; the routine itself not read. (The dog's bite is NOT in this table: `0x743455` is the third caller of `0x8b8050`, so the dial reaches it; not read further) |
| inside the bullet routine, not Arcade factors | friend fire x 0.1 / held NPC x `[tuning+0x3c]` (`0x847610..0x847642`), the loot part (3.3), `[0x1548c20]` (one reference `0x4db945`, no writer: with it non-zero a ZFFActor attacker's float `[actor+0x7f0]` replaces the damage), `[0x1535a2c]` (10 references, one writer `0x53bd15`: 1 = the health write is skipped, 2 = health is put back to 0.01), the gate of 3.2 | **M** as given |

## 7. Scale options

A .. J are the reconciled account's, K is the hook-safety skeptic's, L the code-path skeptic's. 'Ship' = legal under
`klh_may_write`'s ship rule (**R** klhook/klhook.c 313-331: import slots and data only; heap is outside the image).

| | option | ship | exact | why / why not |
|---|---|---|---|---|
| A | re-point the operand of `0x8c63a1` (`d9 05 50 c0 b5 00`) to a hook float | **no** (code) | yes | the page is unhashed but it is code. Good for a TEST-policy cross-check of K, not for the owner's hook |
| B | the same for the reach, `0x8c631b` | **no** | on / off | as A |
| C | private vtables on the VICTIMS (ZFFPlayer slot 424, ZFFActor slot 423) | yes | yes | eight hook files recognise these objects by the stock vtable address - klbalance.c itself (`klh_rd32(pl) != KLR_PLAYER_VT`): the health scale and every 'you lost' line would stop; new objects every level; hook code in the two busiest classes |
| D | `[soldier+0x704]` of the last attacker `[player+0x2778]` while he is near | yes | no | scales ALL his bullets, misses his first hit, nothing for the bots, writes through a pointer the game never clears |
| E | give the HEAD bone a body part of its own (part 0: `[0xcdefe4]`) | yes | no | the byte has six more readers that test for head parts (**M** `0x61a9f0`, `0x636b2a`, `0x847a41`, `0x682273`, `0x4aba53`, `0x5842a2`): head reactions change; one float cannot serve the player (needs 4.2 x key - 3, negative under 0.71) and the bots |
| F | give the health back in the tick | yes | no | cannot undo a death made in the same call (`0x458ea8` .. the death branch) |
| G | the dial as it is | yes | - | scales the step and every bullet together; the ratio stays 100 |
| H | body part 1 (`[0xcdeff8]`) | yes | no | prices every torso hit by anybody |
| I | `[0x1548c20]` = 1 | yes | no | unproven: what `[actor+0x7f0]` holds is not known |
| J | the true close combat's `[0xce8fcc]`, `[0xd1857c]` | yes | - | another path; does nothing for the logged damage |
| **K** | **a private vtable on the ONE ZEngineDataBase object, slot 19 wrapped: the wrapper is entered between the store of the 100.0 and the send, with the record's address on the stack** | **yes** | **yes** | **built: section 8** |
| L | the gun templates: a first range of 1.6 m with a scaled first damage | yes (level data) | nearly | changes the gun's range curve and needs ammo templates split; **A**, not built |

**Why K.** The reconciled account said of the record's float 'no window for a data write'. There is one, and the
routine opens it itself: between `0x8c63aa` (the store) and `0x8c642a` (the send) it makes a VIRTUAL call on a heap
object - the name look-up at `0x8c641c`.

- **M** the object: `[[0xdd2640]+0xac]`; vtable `0xb8fa04`, RTTI `ZEngineDataBase`, 74 slots, slot 19 (+0x4c) =
  `0x698840`. Made once: `0x543242 push 0x86e4` / alloc / `0x543262 call 0x476590` (the constructor; it stamps the
  vtable at `0x4765be`; one caller) / `0x54327f call eax` = the sys interface's slot 27 `0x4bd7b0`, which stores it
  at `[sys+0xac]` (and deletes a previous one through its own slot 0).
- **M** nothing compares the object's first dword with the address: `0xb8fa04` stands in the image twice, both
  `mov dword ptr [esi], 0xb8fa04` (`0x4765be` constructor, `0x82e08b` destructor). `0x698840` stands once (the
  vtable entry `0xb8fa50`) and has no direct caller.
- **M** `0x698840..0x6989e0`: thiscall, reads its first two arguments (`[esp + 0xa8]` the name, `[esp + 0xac]` the id
  asked for), returns the id in ax, `ret 0x10`. File and line are not read.
- **M** at its entry from `0x8c641c`: `[esp]` = `0x8c641e`, +4 the name `0xb63d18`, +8 0, +0xc `0xb22648`, +0x10 0x50,
  **+0x14 the record** (pushed at `0x8c63f4`), +0x18 the send's 0. `0xb22648` is pushed at `0x8c6410` and nowhere else
  in the image (**M** `q.py refs b22648`: 1 place).
- The stock table itself is hashed .rdata (`0xb8b000-0xbeb000`): it is copied, never written.
- **R** the precedent: klchar.c gives the menu's option object a private copy of its 15-slot vtable in exactly this
  way, live in the owner's game since 2026-10-09; klauto.c's scene-load wrapper is entry 8 of THIS vtable
  (`0xb8fa24`, klhook.c's patch table; klauto.c 253, 289, 1003). **A** from that: the live database object uses
  `0xb8fa04` (the direct-boot runs' LOAD lines came through that entry; not re-checked in a log here). The patch
  checks the first dword and does nothing if it is another.

What it costs: hook code now runs inside a call the game makes from about 450 places (**M** `slot19.py`: 456 call
sites by byte pattern). The compiled wrapper is 17 instructions on the pass path (**M** `dllwrap.py` on the built
DLL: `cmp [esp + 4], 0x8c641e` / `jne` / the four arguments pushed again / `call 0x698840` / `ret 0x10`).

## 8. The patch: `re/melee_damage.patch` (klhook/klbalance.c, klhook/KLHook.ini)

Made in a copy of the WHOLE hook folder as it stood at repo head e539e0d (`G:/kl_scratch/melee_write/klhook/`; only
these two files differ from the repo's). `git diff --no-index`, paths rewritten.

    git -c core.autocrlf=false apply --check re/melee_damage.patch      (tested: applies cleanly)
    git -c core.autocrlf=false apply re/melee_damage.patch              (tested: both files byte for byte the changed copies -
                                                                         klbalance.c sha1 06d8d36c, KLHook.ini sha1 f18988f1)

(With the repo's `core.autocrlf=true` a plain `git apply` also applies, but writes klbalance.c with CRLF line ends -
the same text; tested in a scratch repository, `applytest.py`.) The patch's KLHook.ini hunk carries CR bytes (that
file is CRLF, klbalance.c is LF): apply it from the file as it lies in the working tree now (sha1 00ba37b8). Should
it have been re-ended by a commit / checkout, take the two files from the scratch folder instead - they are the
patch's result.

### 8.1 The keys (`[Balance]`, with `Enable=1`)

    ;PointBlankToYou=2        the target is a ZFFPlayer (you, on either side)
    ;PointBlankToCrew=2       the target is a ZFFActor of team Ally (an AI heister; a traitor is still Ally)
    ;PointBlankToCop=100      the target is any other ZFFActor (police, guards, civilians): an AI heister's own steps

The number replaces the 100 in the hit record: **how many ordinary bullets of his gun one step is worth.**
100 = the game's own - the wrapper is then in, sees and logs the steps and writes nothing (the DRY RUN). 1 = one
bullet, 0 = none. No key, or a negative number = that victim is left alone. One number of 0 .. 100 and nothing else
(the seventh factor's strict reading): `0,5`, `abc`, `nan`, 101 are ignored and said so.

Named PointBlank.., not Melee..: it is the fire task's rule, and the game has a real close combat with numbers of
its own (section 6) that these keys do not touch. By VICTIM, so no mirror is needed for a police player.
Decisions the lead may want otherwise:

- **No Risk sets a value.** With the patch in and no key the hook is what it was (8.4 A). Whether `Risk=2` ('the
  same gun at the same range costs everybody the same') should imply a number is the owner's call.
- **Ramp does not touch them**: the game's 100 is the same on every Arcade level.
- `PointBlankToCop` is there because the rule is the soldier script's, whatever the soldier's side (**A**: that the
  AI heisters' soldiers run the same fire task - nothing logs what a policeman loses): with the 100 a heister's
  step on a policeman would be 57.6 x 1.2 x 100 x CrewToCop = 6,912 at 1.0. Left alone unless set; the dry run
  (100) shows whether such steps happen at all.
- **A first value: 2.** K2b shows seven ordinary Type 79 bullets in 0.56 s and steps 0.12 .. 0.19 s apart, with no
  ordinary loss between consecutive steps; one to two bullets a step is about what the same guard does at two
  metres. Rough (two time stamps through a 50 ms pass).

What a step then costs: you G x 1.05 x key x CopToYou; a heister (int) of G x 1.2 x key x CopToCrew.
With `PointBlankToYou=2`: a Type 79 guard 3.02 a step at CopToYou 0.02, 151.2 at Risk=2's 1.0 (where the game's own
is 7,560: death in one step from any gun). With `PointBlankToCrew=2` at CopToCrew 0.05: 8.64, which the integer cut
of 3.3 makes a loss of 9 from a whole health (252 -> 243), 34 from the SigSauer.

### 8.2 What is written, when

- **Nothing unless a key is set**: `klr_pb.any` stays 0, `klr_pb_tick` returns at once, no line is logged.
- While the dial ACTS - klr_tick's own test: an Arcade session with a ZGameRulesHeist object, `klb_level` says the
  level is not stock (the Steam guard on) - and on the game's own thread: if the database object's first dword is
  `0xb8fa04`, the copy's address is written there (`klh_data`). The copy (RTTI locator + 74 slots, slot 19 = the
  wrapper) is made once per process from the table as it then stands and never changed afterwards. Another first
  dword, or a slot 19 that is not `0x698840`: one line, nothing is written.
- The first pass after the dial stops acting (any thread: one aligned dword, both tables valid for ever): `0xb8fa04`
  is written back, only where the hook's own pointer still stands. A flag makes the wrapper pass everything on from
  the moment the dial stops, whatever table is in.
- In the wrapper: return address == `0x8c641e` and the flag set -> the step is looked at. All of this must hold or
  nothing is written (and the first three failures of an arming are logged with what was found): the file argument
  is `0xb22648`; `[rec]` == rec + 0x20 (the task's own trace block); the bone id at rec + 0x48 is 7; the attacker
  `[rec+0xc]` is the actor of the soldier at `[rec-0x14]`; the scale is exactly 100.0. Then by the target's first
  dword (`0xbb45f4` / `0xbb3bac` and its team) the key's number is written over the 100.0 - ONE heap float. Every
  call, matched or not, goes on to the game's `0x698840` with its four arguments and its eax comes back untouched.
- Nothing is put back in a record: `0x8c63aa` writes 100.0 again at the next step. The listeners of the target
  (`0x78727f`) see the changed scale, as they would under option A.
- With ONLY PointBlank keys the table and the health object are not touched (the keys do not set `klr.any`).
- Needs `[KLHook] Tick=1` (the default): the copy goes in from the game-thread tick only.

### 8.3 The log

    balance: point-blank keys (in place of the game's 100 in the hit a soldier sends at every burst step while his target is within 160 units): 2.00 on you, 1.50 on an AI heister, left at 100 on a policeman / another NPC; Arcade only, only on a level that is not stock
    balance: point-blank: the database object XXXXXXXX now has the hook's copy XXXXXXXX of its vtable 00b8fa04 (slot 19, the name look-up 00698840, wrapped): a soldier's step at arm's length - ... gets, in place of the 100: 2.00 on you, ...
    balance: point-blank step: soldier XXXXXXXX (actor XXXXXXXX, team 1) on you XXXXXXXX at 120 units: the hit's scale 100 -> 2.00 [on the main loop's thread]          (Log=2; the thread note on the first of an arming)
    balance: point-blank step: ... on a policeman / another NPC ...: the hit's scale 100 -> 100.00 (no key for this victim)
    balance: point-blank step: ... the hit's scale 100 -> 100.00 (the key is the game's own number, or the write was refused: logged only)          (the dry run)
    balance: point-blank: a call from 008c641e whose record is NOT as expected - left alone (file argument ..., record ...: first dword ..., bone id ..., scale ..., ...)
    balance: point-blank: the game's own vtable 00b8fa04 is back in the database object XXXXXXXX; steps seen while the hook's copy was in: on you N (N re-scaled), on AI heisters N (N), on police / other NPCs N (N), on other kinds of target N, records that were not as expected N; the steps came on the main loop's thread

The in / back lines come at any Log level; Log=2 adds a line per step seen, the first 200 of an arming.

### 8.4 Off-game proof (`G:/kl_scratch/melee_write/harness/`: `harness.h`, `t_old.c`, `t_new.c`, `run.py` -> `run_result.txt`)

Not the game. A 32-bit test program linked at 0x30000000 maps a flat copy of kl2.exe's image at 0x400000 (the range
is reserved by its parent while the child is still suspended), builds made-up objects (sys -> database with vtable
`0xb8fa04`; session, rules, tuning table, player, health object; a fire task with its soldier and four kinds of
target) and runs the last 27 instructions of the game's own routine, `0x8c63ea..0x8c6432`, on them. In the copy
three things are replaced: the code at `0x698840` by `mov eax, 0xdead1234 / ret 0x10`, and the entry +0x120 of the
two victim vtables by a receiver that records what the target is sent. The hook's helpers are stand-ins that print
every log line and every write. `t_old.exe` = the repo's klbalance.c, `t_new.exe` = the patched one.

    RESULT: PASS (92 checks, 0 failed)
    A. six inis without a PointBlank key (Enable=0; Enable=1; Log=2; Risk=2; the owner's Risk=2 CopToCrew=0.05; the K2b ini), nine
       situations each (stock level, not stock on the fallback thread, on the game thread, again, session not Arcade, Arcade again,
       a police player, stock again, session end): old and new print the SAME lines - every log line, every write (25 .. 554 lines)
    B. the K2b ini + PointBlankToYou=2 PointBlankToCrew=1.5 (also written '2 ; two bullets a step' / '  1.5  '):
       the copy is in the object exactly while the dial acts and the game thread has ticked; the target is sent the record once,
       with id 1234 and the 0, scale 2.0 (you), 1.5 (an AI heister), 100 (a policeman: no key), 100 (another class: counted),
       50 (a record that had 50: said once, left alone); 100 on a stock level, with the session not Arcade, and with the flag off
       while the copy is still in; another caller of slot 19 gets dead1234 back whole; the copy differs from the game's table in
       slot 19 only; an object with another vtable is refused with a line; at the end the table, the health and the vtable are
       the game's; the six factors and the health part write and log exactly what they do without the keys (529 lines)
    C. PointBlankToYou=100 alone (the dry run): the copy goes in, seven step lines, no write into a record
       PointBlankToYou=0 PointBlankToCrew=-0 PointBlankToCop=0.5, Log=1: 0 / 0 / 0.5 sent, no line per step
       0,5 / abc / 101 / nan: each 'is IGNORED'; -1: left alone; 'no key acts' - the vtable stays the game's; Enable=0 with a key = Enable=0

What it shows: the compiled wrapper finds the record where the game's own pushes put it, changes that one float,
passes the call on with a balanced stack, and the keys / the arming / the way back do what 8.2 says; and that the
file without a key behaves as the committed one. What it cannot show: section 9.

### 8.5 Builds (compile proof; NOT installed, NOT run)

    G:\kl_scratch\melee_write\klhook\build.bat G:\kl_scratch\melee_write\out_ship          -> built ...\out_ship\dinput8.dll (SHIP)
    G:\kl_scratch\melee_write\klhook\build_auto.bat G:\kl_scratch\melee_write\out_test     -> built ...\out_test\dinput8.dll (TEST)

Both exit 0 at /O2 /W3 with one warning, in a file of another track (`klhud.c(188): warning C4101: 'i':
unreferenced local variable`); none from klbalance.c.

    out_ship\dinput8.dll   SHIP   452,096 bytes   sha1 8624956d951064c0accb3657532cb1e2668a61e9
    out_test\dinput8.dll   TEST   502,784 bytes   sha1 94013d7faedf699b91a3dc10ba6ac179cf6d2c73

Sources: the hook folder of the working tree at e539e0d (last commit touching klhook: 4636092) + the two changed
files. `out_test` has no ini beside it.

Not done (other sessions' files): klhook.c's head comment (two rows for its patch table: `[[0xdd2640]+0xac]` +0 'the
database object's vtable pointer (klbalance.c point-blank keys)', heap; fire task +0x30 'hit record scale', heap;
both ST, NOT RUN) and CLAUDE.md.

## 9. Still assumed, and not known

- **Nothing of the patch has run in the game.** Assumed until the first live run: that the fire task runs on the
  main loop's thread (the log says which); that no code outside the image's two stamps looks at the database
  object's first dword; that a wrapped slot 19 costs nothing noticeable (about 450 call sites; how often they run
  was not measured); that the stack above the look-up's arguments is in the game what the bytes say (it is fixed by
  `0x8c63ef..0x8c641c`; the harness ran those bytes).
- **The dial was never varied**: all eight logs with loss lines have police->you 0.02. That the 0.02 is in the
  product rests on the size (151.2, not 7,560) and on `0x4db9d1`. The cheap proof without any patch: police->you
  0.01 must make a Type 79 guard cost exactly 75.6 a step, an MP45 guard 379.3.
- **No number shows the product on an AI heister** (4.3): code only (`0x61acbd`, `0x61acc6`, `0x61ad18`).
- Whether the gun's real projectiles still fly inside 160 units (the logs show no ordinary loss of the same gun
  between consecutive steps; a shotgun may be the exception - the 90.9).
- 'Two products in one pass' (163.2 twice on the bank, which has one Bullpup carrier): the hook's pass is 50 ms, a
  step 0.1 s or more. **A**: a short last step of a burst, or a late pass. Not established.
- What the gate `0x4d2750` means (**M** its tests only: `[actor+0x70]` != 0; node flag 0x1000; a virtual call;
  `[actor+0x654]` against 0.95; a bit of `[actor+0x42c]`); when the down-state gate `0x8da3b0` answers true in
  Arcade; who writes `[gamedata+0x4cf0]`.
- The body-part floats other than part 1 at run time (REP: 7.5, 9.0, 0.85, 0.6; the logs' 1.4 = 72 x 0.9625 x 0.02
  supports the 0.85). 8 skeletons of each build carry a bone 'free_bone01' with body part 205 (**M** `lvl.py`), for
  which `0x572f60` has an int3: whether a hit can name that bone was not established. And every person a soldier
  can come within 160 units of needs a bone with id 7: a check for `kl_impact` on wardrobe / Payday bodies (REP: a
  missing id reads the part byte before the bone array).
- The one bot loss that is not a kill (73.0), the one full-health kill outside vehicle state 5, the player's 90.9.
- Not re-read here (REP): `0x5575a0`, `0x86a130`, `0x660b00`, the scheduler, the tuning constructor's rows (the log
  line 'is what the game's code builds' covers the table), the second burst loop's purpose, the senders of the
  'DamageInfo' message.

## 10. The live check (the lead / the game holder; one variable a run; TEST hook built from the patched folder)

Map and script: the K2b run as it was - the bank through the tab (`w_tabT` DM03 or its successor), the scripted
walker to the stairs at (-392, 440, -5679), `[Balance] Enable=1 Log=2 Risk=2 Ramp=0 CopToYou=0.02 CrewToYou=0.02
CopToCrew=0.05`, `[Bots] Enable=1 Log=2`.

| run | add to `[Balance]` | must appear in the log | proves |
|---|---|---|---|
| **P0 dry** | `PointBlankToYou=100` `PointBlankToCrew=100` | `balance: point-blank keys (...): 100.00 on you, 100.00 on an AI heister, left at 100 on a policeman / another NPC; Arcade only ...` - after 'acts on this round': `balance: point-blank: the database object ... now has the hook's copy ... of its vtable 00b8fa04 (slot 19, the name look-up 00698840, wrapped)` - within one pass BEFORE each `you lost 151.2`: `balance: point-blank step: soldier ... (actor ..., team 1) on you ... at NNN units: the hit's scale 100 -> 100.00 (... logged only)`, NNN at most 160, the first with `[on the main loop's thread]` - the losses as in K2b: 151.2, 151.2, 30.2, `record 0 (you): dead` - at the session's end `balance: point-blank: the game's own vtable 00b8fa04 is back ...: on you N (0 re-scaled) ... records that were not as expected 0; the steps came on the main loop's thread` - RESULT PASS, no INTEGRITY EXIT, no fault, no `NOT as expected` line | the wrapper is entered by the fire task, on which thread, with the record where it is read; every big loss has its step (a step WITHOUT a loss would be new - the gate of 3.2, or a target that is not hit: note it); the game runs with the copy in |
| | if instead | no step line although 151.2 is lost: the call does not come through the object's vtable as read - stop, send the log. `NOT as expected`: the line says what was found - stop. `[on thread N, NOT the main loop's]`: nothing breaks (the wrapper is reentrant), but say so before P1 | |
| **P1** | `PointBlankToYou=2` (Crew still 100) | each step line `the hit's scale 100 -> 2.00`; `you lost 3.0` a step (72 x 1.05 x 2 x 0.02 = 3.024; an MP45 guard 15.2, the SigSauer 11.7, the Bullpup 1.6) where 151.2 stood; the walker is alive after the stairs; the back line `on you N (N re-scaled)` | the float is the one; the number is exact |
| **P2** | P1 + `PointBlankToCrew=2` | on the stairs where PB_DM03's bot 7 died: `point-blank step: ... on an AI heister ...: 100 -> 2.00` and bot losses of 9 a step from a Type 79 (8.64 and the integer cut: 252 -> 243 -> 234), 34 from the SigSauer (33.3), no 'lost N (0.0 of 252.0)' right after a step | the NPC side - the first number for the product on a heister |
| **P3** | P0's keys | the same run on Retomoto with the idle player (the R7 runs): every bot kill of a REST must or must not have a `point-blank step ... on an AI heister` line in the pass before it | which of the rest-kills are this rule |
| **P4** | any key | Arcade -> stock Subway from the stock page: `nothing is written here`, NO `now has the hook's copy` line; then quit to the menu from a Dead Men map: the `is back` line | stock levels are left alone; the way back |
| P5 (no patch needed) | `CopToYou=0.01`, no PointBlank key | `you lost 75.6` a step from a Type 79 guard | the dial is in the product (section 9) |

Read with it: `python G:/kl_scratch/melee_write/fit.py` re-counts every large loss of the live folder against the
formula.

## 11. Files

| | |
|---|---|
| `re/melee_damage.md` | this note |
| `re/melee_damage.patch` | klhook/klbalance.c + klhook/KLHook.ini, 24,954 bytes |
| `G:/kl_scratch/melee_write/klhook/` | the whole hook folder with the two changed files |
| `.../out_ship`, `.../out_test` | the two builds |
| `.../d.py`, `q.py`, `slot19.py`, `dllwrap.py` | disassembly with float notes; refs / callers / vtables / hashed; the slot's call sites; the compiled wrapper |
| `.../f_*.txt` | listings: `f_8c62e0`, `f_4db580`, `f_61a980`, `f_458880`, `f_6e3400`, `f_7e1700`, `f_8a7c60`, `f_46ef60`, `f_698840`, `f_60db40`, `f_8da3b0`, `f_7c0640` |
| `.../lvl.py` -> `lvl.txt` | guns, armed NPCs, head bones of the four `w_tabT` builds |
| `.../fit.py` -> `fit.txt`, `kills.py` -> `kills.txt` | the logs against the formula |
| `.../harness/` | the off-game harness and `run_result.txt` (`kl2_img.bin` there is a copy of the game's image: it stays on this machine) |
| `.../mkpatch.py`, `applytest.py` | how the patch was made and tested |
