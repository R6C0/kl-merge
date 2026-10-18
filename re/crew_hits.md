# Crew hit logging: how to wrap the damage path (static reading, 2026-10-18)

Goal: opt-in `[Balance] LogCrewHits=1` (default 0 = no patch, no wrapper) that logs each hit on an AI
heister (ZFFActor, team Ally): attacker, class/team, weapon or damage kind, amount, health before/after,
crew record, position. It must never change the hit. Nothing here was run; no code was edited.
CERTAIN = read in the disassembly (and, where noted, seen in the live log). GUESS = inferred.

## 1. 0x8473a0 calling convention and arguments
- CERTAIN: ZSoldier (CPPScript::ZSoldier, vtable 0xbd0954) slot 96 (+0x180) = 0x8473a0. Only reference
  to the address is the data word at 0xbd0ad4. Other RTTI vtables that seem to hold it are overlaps.
- CERTAIN: thiscall. ecx = soldier, ONE stack arg = pointer to the hit record, `ret 4`.
  Prologue `push ebp; mov ebp,esp; sub esp,0x74`. Wrapper shape:
  `static DWORD __fastcall w(void *self, void *edx, DWORD rec)`, return the game's eax unchanged.
- CERTAIN: no direct callers. Reached through the soldier message handler 0x608050(msgid,data) (`ret 8`):
  id 0x1c ("ScriptDamageInfo") -> 0x608174 -> `push edi (record); call [soldier+0x180]` at 0x608184.
  The handler ignores the return value.
- CERTAIN chain for a bullet: ZFFActor slot 423 (0x61a980, ProjectileHit handler, builds the record on
  its stack) -> slot 421 (0x69f900, network gate; clients forward via 0x4b5690) -> slot 422 (0x8689c0,
  friendly-fire/team filter) -> its tail (0x868dbf..0x868dcd) calls actor slot 72 (0x787250) with
  (msg id 0x1c, record, 0) -> soldier handler 0x608050.
- Mapping from soldier to actor: [soldier+0x40] = actor; [actor+0x77c] = soldier. Team = [[actor+0x54]+4]
  (Ally = 2).

## 2. Hit record layout
Offsets as read by 0x8473a0 and built by 0x61a980.
- +0x00 CERTAIN: attacker actor pointer (class tested through [vt+0x30] masks: ZFFPlayer
  [0x1548c7c]/[0x1548c80], ZFFActor [0x1547b24]/[0x1547b28]).
- +0x04 GUESS: 0 in the bullet build, meaning unknown.
- +0x08 CERTAIN: damage kind dword. 0x61a980 maps the gun type through a switch (table 0x61b0dc, targets
  0x61ae90/9a/a4 = kinds 2/3/4, default 0). Melee writes 1 (0x74b96d, GUESS which), 0x772e49 writes 10.
  Kind 9 = blast per re/player_down.md; which sender writes it NOT found (GUESS). Routine tests 1..5.
- +0x0c GUESS: copy of [msg+0x10] of the ProjectileHit message.
- +0x10..0x18 CERTAIN: hit position x,y,z (floats).
- +0x1c..0x24 CERTAIN: direction/normal vec3.
- +0x28 CERTAIN: damage amount (float). MODIFIED IN PLACE by the routine before health is applied
  (x0.1 under conditions, x tuning+0x3c, difficulty factors from [0x168d7c0]+0x2a4..0x2b0 when the
  victim has [actor+0x774]). So log the raw amount before the call and the real loss as hp_before-hp_after.
- +0x2c GUESS: second scale factor (passed to hit reaction slot 0xd0).
- +0x30 GUESS: byte flag, 1 when body-part class is 2 or 3 (head/vital?).
- Bone is NOT in the record (CERTAIN): it is in the ProjectileHit trace at [msg->trace]+0x28.

## 3. Vtable, sharing, other paths, other health writers
- CERTAIN: 0xbd0954 is the only soldier vtable; crew and police share it. Filter by victim team
  ([[[soldier+0x40]+0x54]+4]==2), not by vtable.
- CERTAIN: blasts/fire/kill boxes/vehicles enter through the actor message handler 0x6050e5 (message
  [0x1547b5c]) which forwards the incoming record to actor slot 421, hence the same chain to slot 96
  (per re/melee_damage.md:346; the forwarding itself read in code).
- GUESS: falls use a DamageInfo kind through the same path (no fall sender found).
- Health writers: CERTAIN only actor slot 412 (+0x670) = 0x792bc0 (`ret 4`, float) -> 0x61efd0 (clamp,
  stamps [h+0x1c]/[h+0x20], listener 0x8ab200) writes actor health. The other 0x61efd0 callers
  (0x4aa8be 0x580726 0x5c8034 0x64438f 0x69fa92 0x6e3644 0x783b19) use [esi+0xa48] (player health).
  Heal/regen/get-up also go through slot 412 (callers not classified). The slot 96 write is skipped when
  word [[actor+0x54]+0x3a] != 0 (no-damage bits, at 0x8477ae). At health 0 it calls soldier slot 51
  (0x688190 -> 0x70e0e0) with (rec,0): yes = goes down instead of dying.
- Early exits with no damage: 0x847ea4 (from 0x8473be/ca/d9, actor slot 0x654 false) and 0x847ea3.

## 4. Where health and maximum are read
- CERTAIN: h = [actor+0x5fc]; current = [h+4], maximum = [h+8]; [h+0x24] = owner actor (sanity check as in
  klbotdown.c); [h+0x1c]/[h+0x20] = last-change ticks; [h+0x14] regen timing.
  0x539dd0 is `mov eax,[ecx+0x5fc]; fld [eax+4]; ret`. 0xa8d330 truncates to int.
- GUESS: [actor+0x600] accumulates damage (0x61a980 and 0x8689c0 add the amount).

## 5. Least risky hook point and threading
Write constraints (CERTAIN, klhook.c): klh_data writes heap/.data/.bss only; klh_poke into code or .rdata is
refused in SHIP and inside klranges.h hashed ranges. 0x8473a0 (0x847000-0x84d000), the vtables
(0xb8b000-0xbeb000), 0x69f900 and 0x8689c0 are hashed; 0x61a980/0x61efd0/0x787250/0x688190 are not hashed but
are code. So a global vtable-slot patch or a detour is NOT allowed in a ship build.

Options:
- (C) RECOMMENDED, always: zero-write sampler in the existing per-frame tick (as klbotdown.c): for each crew
  actor read h=[actor+0x5fc], hp=[h+4], hmax=[h+8] (validate [h+0x24]==actor), log each drop with position,
  ticks [h+0x1c]/[h+0x20], [actor+0x600], nearest cop/grenade/fire object. No attacker/kind, sub-frame
  multi-hits merge. Cannot alter the hit.
- (A) optional extra diagnostic: per-crew-soldier PRIVATE ZSoldier vtable copy (RTTI locator copied to
  vt[-1]) with slot 96 wrapped (pattern: klr_pb in klbalance.c, which wraps slot 19 of the database object
  0xb8fa04 and filters on `_ReturnAddress()==0x8c641e`). Log before/after calling the game's routine
  (attacker rec+0, kind rec+8, raw amount rec+0x28, position rec+0x10, hp before/after). CAVEAT CERTAIN:
  seven modules identify a crew soldier by `[soldier]==0xbd0954` (kladren, klbotdown, kldown, klescort,
  klhop, klgrudge, klmove; kladren.c:42 notes a private vtable is rejected by six). Those soldiers would
  silently lose botdown/escort/hop/grudge/move/adrenaline/down while logging, changing the behaviour under
  study. Use only as a labelled diagnostic, or first teach those tests to accept the private vtable.
- (B) private ZFFActor vtable with slot 423 wrapped: victim is ecx, message has gun/bone/attacker
  ([msg+0xc])/scale ([msg+0x18]); bullets only; breaks `[actor]==0xbb3bac` identity used in klbot, klescort,
  klfed, klgrudge, klbalance (re/bots_fight.md rejected it). Not recommended.
- (D) return-address-filtered trap on a shared object (klr_pb style): none found in the damage path
  (singletons called non-virtually; 0x61efd0 makes no virtual calls).

Threading: CERTAIN that the fire task and point-blank steps ran on the main loop's thread (KLHook.log).
GUESS that slot 96 also does. Wrapper rules: reentrant, no globals mutated except an InterlockedIncrement
rate limiter, read with klh_rd/klh_rd32 only, never write the record, pass the argument and return eax
unchanged, restore the game's vtable when the key is 0.

## 6. The sampler's 'who could have done it' (2026-10-18; klbalance.c a9b; NOT RUN; zero writes)
What a `balance: crew hit:` line says now, after the old part (record, health -> , place, your distance, nearest heister):
`who could have: N soldier(s) aim at him: [crew record 3 TRAITOR 4.2 m] [Enemy (police / guard) 12.5 m] ... ; nearest living
non-Ally: Enemy 8.3 m, aims at him|someone else|nobody; nearest Ally aiming at him (friendly-fire candidate): crew record 4 6.1 m`.
The DIED line repeats the last drop's text ("who could have done it then").
- CERTAIN (kl2 0x8c62ec, 0x8c630c, 0x8c6334; re/melee_damage.md 2): the soldier's current target is `[soldier+0xac]` (the target's
  object; for a man his ZFFActor) and `[soldier+0xb0]` is a dword 'has a target' (the fire task returns at once when it is 0).
  So the sampler counts a soldier as an aimer only while +0xb0 != 0 and +0xac == the victim's actor. (klbotdown.c's comment
  calls +0xb0 'the target': that is the flag; its NoFire clears the flag and leaves +0xac stale.)
- The soldier list is built once per pass, only if a line is written or a death falls in it (one entity-table walk as klcensus.c;
  256 soldiers at most; a rate-limited drop is not looked up). Teams: Mercenary 0, Enemy 1, Ally 2, Enemy2 4 (re/balance.md);
  an Ally with a crew record is shown by record, TRAITOR when the crew record's flag bit 2 is set. Class is not printed: every
  soldier is vtable 0xbd0954 and every actor 0xbb3bac (a filter, not information).
- How to read it:
  - COPS: a drop with one or more `Enemy` aimers (and no Ally aimer) = police / guard fire. Several aimers = a firing line.
  - FRIENDLY FIRE: an aimer that is `crew record N` (or TRAITOR), or `nearest Ally aiming at him` not `no Ally aims at him`.
    Mixed cop + Ally aimers cannot be separated: the line only names the candidates.
  - BLAST / FALL / SCRIPT: `no soldier aims at him` with `NO AIMER and a big loss` (more than 25 % of his maximum in one 50 ms
    pass). A small loss with no aimer is unexplained (stray bullet from a man aiming elsewhere, fire, YOU).
- GUESS: aiming = shooting (a soldier may aim and miss, or a stray bullet hits a man next to the target); team 1 is police AND
  guards; +0xac is cleared when a soldier drops his target (a stale value could name the victim for a moment); a grenade, fire,
  a vehicle, the helicopter and YOU (ZFFPlayer, not a soldier, never listed) show only as 'no aimer'.
- Two hits in one 50 ms pass are still one line; targets are read at the pass, up to 50 ms after the bullet, so a man who
  shot and then switched target is missed.

## 7. Review fixes (2026-10-18)
- lwho is 640 bytes; the friendly-fire clause is written first, so a cut never loses it.
- A soldier with a crew record is labelled by record whatever his team (a TraitorFoe traitor is team 1 in play) and counts as crew (friendly-fire candidate), not as police.
- "KILLED HIM" only on the hit that takes a not-yet-dead record to hp <= 0 / status 7. A fatal hit always builds the who text (no rate-limit skip) and a fatal hit with no targeter says the killer may have just dropped him as target.
- Wording says "has him as target (fire-task field +0xac)": only the point-blank task (0x8c62e0) is read; that rifle fire uses the same field is a GUESS.
