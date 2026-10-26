# Online bot damage: how Arcade protects the AI crew from police, why online lacks it (2026-10-26)

Static RE of kl2.exe build 0490, read-only (workflow task B, follow-up of BO5..BO8c). Confidence: CERTAIN = read in the
disassembly this session or in a cited note that was re-checked here; LIKELY; GUESS = marked.

## 0. Short answer

- Arcade protects the crew with ONE float per Arcade level, `R+0x00` ("police -> crew") of the tuning object, multiplied
  into every NPC-on-NPC hit by 0x591b60. Stock value 0.01 (level 1) .. 0.5 (level 11). It is applied nowhere else.
- Online it is off for TWO independent reasons, both from the same session test: 0x61a980 asks 0x7f6850 (false for session
  roles 2/3) and, even past that, the rules getter 0x508ef0 itself returns NULL unless 0x7f6850 is true. So calling 0x591b60
  from outside is not an option either (it needs an Arcade rules object).
- SHIP-safe mechanism: a private copy of the ZFFActor vtable on each bot with slot 423 wrapped (data writes only), the
  wrapper multiplies the hit record's scale `[hit+0x18]` by K for hits from non-team-2 attackers on listed bots, calls the
  original, restores it. Section 4.

## 1. The Arcade factor (question 1)

Caller: `ZFFActor` vtable (0xbb3bac) slot 423 = 0x61a980, the ProjectileHit handler. `this` = the HIT NPC, one stack arg
`ret 4` = hit record (ebx). CERTAIN (0x61a980 prologue, `ret 4` at 0x61b0c9; the vtable at 0xbb3bac holds it once, the
ZFFPlayer vtable 0xbb45f4 has 0x458880 in slot 423).

Damage chain (CERTAIN, 0x61ac98..0x61ae21):

    dmg = gun(slot 0x2f0, [hit+0x14]) x bone factor (0x572f60) x [hit+0x18]          0x61ac98..0x61acc9
    x [attacker soldier +0x704]   attacker a ZFFActor with a soldier [att+0x77c]        0x61accd..0x61aced
    if 0x7f6850() && (rules = 0x508ef0()):  x 0x591b60(rules; attacker, victim)         0x61acf1..0x61ad21
    attacker is a ZHeli (pair 0x168ce48) with [att+0x7bc]: x [ctl+0x98]                 0x61ad25..0x61ad54
    attacker a ZFFPlayer: x the player extras, then (Arcade) x 0x7c1ba0 ("you -> police/crew") 0x61ae18

0x591b60 (CERTAIN, re/balance.md 10.1): level L = byte `[[rules+0x5f8]+0x45]` clamped 1..11; R = `[0x168d7c0] + 0x6ac + L*0x70`;
local player = 0x660b00; for a NON-police local player: attacker team (`[[att+0x54]+4]`) == 2 (Ally) -> `R+0x04`, else
`R+0x00`. So **police -> crew = R+0x00**. Then, only for an Ally attacker whose crew-record stage differs from the local
player's, times `R+0x1c`. Not relevant to cops hitting bots.

Stock R+0x00 by Arcade level 1..11 (constructor 0x524050, re/balance.md section 2, emulated): 0.01 0.05 0.1 0.15 0.2 0.25 0.3
0.35 0.4 0.45 0.5. The owner's klbalance `CopToCrew=0.05` writes this float. So in Arcade a cop hit on an AI heister costs 1 % to
50 % of its table value; a 65 hp hit is 0.65 hp at level 1. Online: 100 %.

Other things that scale the NPC-victim damage, none of them Arcade protection:
- Per-attacker `[soldier+0x704]` (1.0, ctor 0x761b1e; writers: script controller 0x7e25c0, buddy 0x4bcc95). Not mode gated.
  WARNING: the same float is also read in the PLAYER-victim path (0x4db997 in 0x4db580) and in 0x7a72e7, so writing it on cops
  lowers their damage on humans too. Not a victim-specific tool.
- Health: ZSoldier health = field 7 x difficulty row[2] (0x831f00 picks the table by session; Arcade = story rows 0.5/0.9/1.15/1.3,
  online = a different row set at tuning+0x5b4 pointers; online row values NOT READ). Health only, not damage.
- 0x8473a0 (ZSoldier slot 96, the health subtraction) calls 0x7f6850 at 0x84774d, but only to feed `rules->0x4d17f0`
  (per-victim hit sums for the rules); the subtraction is `health - dmg * const(0xb87940)`; no protection there (CERTAIN
  for the block 0x847738..0x847793; the constant's value was not decoded, it is applied to both uses).

## 2. The gate (question 2)

`0x7f6850` (CERTAIN, disassembled): `sm = [0x168e598]; role = [sm+0x54]; if role > 3 -> (sm+0x5c == 4); jump table 0x7f6874 =
{0x7f6865, 0x7f6865, 0x7f686e, 0x7f686e}`: roles 0 and 1 return `[sm+0x5c] == 4` (mode 4 = Arcade), roles 2 and 3 return false.
0x863a60 is the sibling table (true for roles 2/3). Online FA host = role 2 (GUESS from re/private_match.md: "3 = client is
FACT, 0/1 local, 2 server GUESS"), client = 3. Hence false online for every bot-bearing role, even though `[sm+0x5c]==4`
("covers all FA").

Second lock (CERTAIN, 0x508ef0): `if [sm+0x5c]==4 && 0x7f6850(): return [this+0x54]` else NULL. The caller at 0x61acfa/0x61ad00
tests it for NULL and skips. So even a patch of the first test would reach nothing. The rules object that exists online is a
different class without `+0x5f8` / `+0x348` (stated in re/bots_online_fill.md; not re-verified here).

Consequence for a "toggle the role around the call" trick: NOT recommended. It would also open the 0x61aac1 friendly-fire
rules, the 0x61ab34 mode-4 block, 0x7c1ba0, and 0x591b60 would read the missing rules fields (crash risk). GUESS-level analysis,
not tried.

## 3. Hookable points for the online bot victim (question 3)

| point | kind | ship-safe? | note |
|---|---|---|---|
| ZFFActor vtable slot 423 in place (0xbb4248) | .rdata write | NO | inside the hashed ranges of klranges.h (checked: 0xbb4248 is hashed); klhook.c: SHIP touches import slots and data only |
| 0x61a980 detour (klbotdeath id1 style) | code patch | NO (TEST only) | the function is NOT hashed, stolen bytes `81 ec d0 00 00 00`, back 0x61a986 |
| private vtable copy per bot, slot 423 replaced | data (actor's first dword + a copy of the table) | YES, same technique as klsync.c's puppet (`ksp_vt`, `klh_actor_priv`, `klh_avt`) | reaches the handler for exactly the listed bots |
| health object `[actor+0x5fc]` (OnlineHealthMul) | data | YES | also divides HUMAN damage on bots, does not touch cop damage per hit, does not stop the cop's kill rate by ratio |
| `[soldier+0x704]` on cops | data | YES | hits humans too (0x4db997) |
| call 0x591b60 / 0x508ef0 | game call | NO | rules NULL online |

There is no per-actor or per-DO damage multiplier on the VICTIM side: victim-specific inputs of 0x61a980 are only the bone
table, `[esi+0x821]`, team and health (CERTAIN for the section read; the earlier notes agree: "the health object has no virtual in that path").

## 4. Recommended mechanism

Private ZFFActor vtable copy, slot 423 wrapper (data only):

    wrapper(ecx = victim, [sp+4] = hit):                      // thiscall, ret 4
        if victim in the bot census (klbf_pb_is_bot) and role is 2 (host) and state 0x13..0x1f:
            att = [hit+0xc]; team = [[att+0x54]+4]
            if att != 0 and team != 2:                         // cops, guards, civilians; humans and bots untouched
                f = [hit+0x18]; [hit+0x18] = f * K
                r = original(0x61a980)(victim, hit); [hit+0x18] = f; return r
        return original(victim, hit)

- `[hit+0x18]` is read at 0x61acc6 (`fmul [ebx+0x18]`) and is the "scale 1.00" the klbotdeath probe logs (CERTAIN). The hit
  record is the one passed into the wrapper, restore after the call so any later reader of the same record is unchanged
  (the call is synchronous on the game thread; GUESS that nothing keeps the pointer).
- Install per bot like `ksp_wr_vt`: copy the table once (`vt[-1]` locator plus all slots, check slot 423 == 0x61a980 first),
  write the actor's first dword. Extend `klh_avt` (klhook.c:655, one `klh_actor_priv` today) to recognise a second private table
  or reuse `ksp_vt` by adding the slot-423 wrapper to it (then puppet cops and bots share one table and the wrapper's
  bot test keeps cops unaffected). The code that must see through it: every `klh_avt(o) == 0xbb3bac` user is fine;
  direct reads of the first dword (klbotdeath.c klbdp_team? klbot.c KLB_ACTOR_VT) must be checked. ASSUMED: nothing in the game
  compares the first dword with 0xbb3bac (klsync's Puppet has run with a private table; whether the game was clean in a long
  round is the open question of that module).
- Value: `OnlineCopToBot` (new key, default the Arcade level-2 value 0.05, range 0.01 .. 1; matches the owner's `CopToCrew`).
  Arithmetic against BO8c: 65 hp x ~10 hits/s = 650 hp/s against one bot group; at K = 0.05 that is 32 hp/s, a 280 hp bot lasts
  ~9 s of sustained group fire, a 5600 hp (x20) bot ~3 min; with K = 0.01 (Arcade level 1) 280 hp lasts ~43 s. Set
  OnlineHealthMul back to 1 once K works (it also divides the humans' damage on bots). The point-blank step (scale 2.00 by
  klr_pb) stays; the same K could be applied to the hit scale to keep step and ordinary hits consistent.
- Explosions / melee: GUESS that they also arrive at slot 423 (re/melee_damage.md says the handler receives the ProjectileHit
  message; explosions NOT checked). If a death shows a different caller in the next probe, extend the wrapper there.

## 5. Accuracy / rate of fire (question 4)

Found no Arcade- or crew-specific accuracy or fire-rate rule:
- Accuracy is level data: ZSoldier field 4 ("per cent", miss share = 1 - f/100, 0x557b17, 0x719ce1, burst chooser 0x719b00,
  fire-task set-up 0x8b84b0). 55 on stock SWAT/cops, 100 on some converted guards (re/balance.md section 6). Nothing in those
  routines reads 0x7f6850 or the target's team (CERTAIN for the call lists scanned: 0x7f6850 has 219 caller functions, none of
  them are 0x719b00, 0x557ae0 or 0x8b84b0; 0x5706a0, the friend list, has Arcade branches but those decide who is a target, not
  accuracy).
- The aim object value 0x884a70(tuning +0x374 = 2.5, +0x378 = 0.3, accuracy) (0x557b5b): not read; range dependence unknown.
- Difficulty row [3] (`fld [row+0xc]` at 0x4cc04c, after 0x831f00): multiplies the spread of a shooter whose team is 1
  (Enemy = cops/guards), whoever the target. Arcade uses the story rows (1.0 at every difficulty per re/balance.md); the online
  row values (pointer table at tuning+0x5b4) were NOT read here. Online cops may therefore have a different spread than Arcade
  cops. UNKNOWN; reading the 0x524050 constructor blocks for the online row would settle it.
- Rate of fire: per weapon template (tuning), not mode dependent (no evidence of a crew-specific reduction).

So the entire Arcade protection of the crew is the damage float R+0x00 (plus the crew's health table and its regeneration, both
level-data); there is no hidden accuracy handicap to restore.

## 6. Not verified

- Which role the online host really has (2 is a GUESS from reading).
- The level byte `[[rules+0x5f8]+0x45]` for the Arcade level the owner compares with (R+0x00 value is a function of it).
- That a private-vtable bot is safe through death/despawn paths (the destructor slot is a copy of the same pointer, LIKELY).
- Online difficulty-row values (section 5).
