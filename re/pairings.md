# Field pairings Dead Men -> Dog Days: what the converter assumes, checked

Scope: the 46 class levels `Converter.plan` puts in `Converter.assumed` (2026-10-09, schemas
`re/kaneandlynch.json` / `re/kl2.json`), ranked by objects in the four Dead Men FA maps
(M01FAA, M02FAA, M03FAA, M06FAA). Field numbers are indices **within the class level** (the
format of `LEVEL_MAPS`), `DM n` / `DD n`. "Current" = what difflib pairs today.

Result in one line: **20 class levels are paired wrongly today** (table A), 19 are right (table B),
7 cannot be decided or have nothing to convert (table C). The dict at the end fixes table A.

## How each pairing was decided (evidence kinds)

Data: every object of the 20 stock Dead Men levels and 21 stock Dog Days levels (F02-F09, L00-L11,
stock F01 from `KL_PortBackup`), split per class level; 71 class levels differ between the games.

- **[N] same-named objects.** Objects with the same scene name (last one or two path components)
  in both games, compared field by field; per candidate pair the number of names whose values are
  equal, against the number expected by chance from the two value distributions. Written
  `equal/N (chance c)`. Works where Dog Days kept Dead Men content: the shared effects, the legacy
  weapons / ammo / projectiles in `equipment.zip`.
- **[O] member offsets from the exes.** A property record is 0x14 bytes when it is a plain member:
  `{next, name, filter, type handler, member offset}` - the offset is at record +0x10. An accessor
  record is 0x20 bytes: getter at +0x10, setter at +0x18, both zero in the file and written by a
  static initializer (`mov eax, <fn>; mov [rec+0x10], eax`, e.g. kl2 0xafed50 for ZParticleEmitter
  field 0); the getter's code gives the member (`mov al,[ecx+0x33]; shr al,2` = bit 2 of +0x33).
  Offsets do not order same-typed neighbours, but they show gaps, moved blocks, sub-structs and
  bit positions. For controllers the offset is relative to `this - 4` of the virtual functions
  (seen on ZTriggerBox).
- **[T] fine type.** The schemas' type handler index is finer than the converter's `label()`
  (`I` is five types, `s` three, member and accessor variants differ). Handler indices were mapped
  across the games by voting over all class levels with identical label lists: 51 Dead Men types
  mapped, 0 ambiguous. A pair with different fine types is not the same property.
- **[V] value distributions** over all stock levels (constants, ranges, always-zero fields,
  scene-path / sound-name patterns).
- **[C] code.** Where the above fail: the function that uses the members, same vtable slot in
  both exes.

Not used: the class constructors (they do not initialise these members - checked on ZSoldierRout).

Two facts about the present code that explain most of table A:

1. difflib does **not** "keep the earlier ones" (kl_convert docstring). In a run of same-typed
   fields it may put the new field first (ZHavokRigidBody, CExplode, ZInventoryBinding,
   ZVehicleEffects, ZLNKWHANDS) or last; it has no reason either way.
2. Dog Days moved properties between record lists, so order changed, not only length
   (ZParticleEmitter's velocity vector, ZBarrelEffects' reference list, ZKillBox's last bool).

## A. Wrong today - corrected pairing

| class level | FA objs | DM objs | pairing (DD <- DM) that differs from current | evidence | confidence |
|---|---|---|---|---|---|
| ZParticleEmitter | 20617 | 84866 | DD6<-DM6, DD7<-DM8, DD8<-DM10, DD21<-DM7, DD20<-DM16; new: DD14, DD22, DD33. Current: DD6<-DM8, DD7<-DM9, DD21 = default (emitter loses its f*3, DM6 and DM7 dropped) | see below | high (DD8: medium) |
| ZHavokRigidBody | 315 | 1351 | DD3..6<-DM3..6, DD7 new, DD8<-DM7. Current: DD3 new, DD4..8<-DM3..7 | [V] DD7 = 0 in 578/578; DM7 = 1e4 in 1214/1351, DD8 = 1e4 / 1000 / 2000; DM6 and DD6 both ~0 with a few 45s; DM4, DM5 <= 1 like DD4, DD5. No same-named objects (0 of 848 / 211 names) | medium-high |
| ZInventoryBinding | 152 | 760 | DD0<-DM0, DD1<-DM1, DD2 new. Current: DD0 new, DD1<-DM0, DD2<-DM1 | [N] 10 legacy items: (DM0, DM1) = (DD0, DD1) for 4 (Launcher_HK69A1 x3: 5,7; RPG_7V_Hind: 999,999), current pairing fits 0 | high |
| ZItemTemplateWeapon | 144 | 720 | DD7<-DM6, DD9<-DM7, DD10<-DM8, DD11<-DM9, DD12<-DM10; DD6, DD8 new; DD17 new (list), DM15 and DM18 (strings) dropped. Current: DD6..10<-DM6..10, DD11, DD12 new | [N] 10 legacy weapons: DD7=DM6 8/10 (chance 2), DD9=DM7 9/10, DD11=DM9 9/10, DD12=DM10 8/10; e.g. Grenade_Fragmentation DM 600,0,100,1500,1,80,200 -> DD 600,0,**-1**,100,**-1**,1500,1,80,200 | high |
| ZItemTemplateAmmo | 128 | 640 | DD3<-DM2, DD5<-DM3; DD2, DD4 new. Current: DD2, DD3 new, DD4<-DM2, DD5<-DM3 | [N] 13 legacy ammo: Grenade_Incendiary / Smoke 500,200 -> -1,500,-1,200; RPG_7V_Hind 250,300 -> -1,250,-1,300; TearGas 0,0 -> -1,0,-1,0 (DD3=DM2 6/13 chance 2, DD5=DM3 7/13) | high |
| ZLNKWHANDS | 129 | 1764 | DD0<-DM0, DD5<-DM1; DD1..4 new. Current: DD4<-DM0, DD5<-DM1 (DD0 = default) | [V] DD3, DD4 = 0 in 1891/1891, so DM0 (non-zero in 1450/1764) is not DD4; DM1 never 0, 23 values <-> DD5 never 0, 21 values; DD0,1,2 are a rising triple (292016, 306496, 320896) = one slot per LOD. [O] slots 0x10 apart, [T] all type 46 | DD5 high, DD0 medium |
| ZFFActor | 65 | 1668 | DD17<-DM7, DD19<-DM8; DM6 dropped; DD6..16, DD18 new. Current: DD6<-DM6, DD7<-DM7, DD8<-DM8 | [T] DM7 is type 46 (handle), DD6/DD7 are type 21 (count), only DD17 is type 46; [O] DM7 and DD17 are both followed by a 0x14-byte gap, then bools. [V] DM8 = 1 on civilians (197 of 213 Neutral), DD19 = 1 on 115 Neutral, DD18 and DD8 = 0 in 1696/1696 | DD17 high, DD19 medium, DM6 not established |
| ZSoldierRout | 54 | 1455 | DD13<-DM9, DD14<-DM10, DD15<-DM11; DD9..12 new; DM12, DM13 dropped. Current: DD9..12<-DM9..12, DD13..17 new | [V] DD9..12 = 1 in 1412/1413 while DM9..12 are 50, 50, 5000, 0; DD13, DD14 = 50 like DM9, DM10; DD15 = 5000 in 469 like DM11 (5000 in 1260) | medium (values only) |
| ZVehicleEffects | 32 | 484 | DD0..3<-DM0..3, DD10..12<-DM4..6, DD15..19<-DM9..13, DD21<-DM14, DD22<-DM15; new DD4..9, DD20. Current: DD0..5 new, DD6..12<-DM0..6, DD15 new, DD16..22<-DM9..15 | [V] constants line up: DM 40, 60, (1/200), x, 0, 100, 100 / 900, 12, 2.5 <-> DD 40, 60, 200, x, x, 1,1,1,1,1, 0, 100, 100 / 900, 12, 2.5 (DD has 18 objects, all with these values) | block high; DD3 vs DD4 and DD20 vs DD21 not established |
| CExplode | 28 | 246 | DD0<-DM0, DD1<-DM1, DD3<-DM2, DD4<-DM3; DD2, DD5, DD17 new. Current: DD0, DD1 new, DD2..5<-DM0..3 | [N] 3 legacy projectiles, all fields: Rocket_RPG7 500,150,1000,200 -> 500,150,**200**,1000,200,**1**; Projectile_50cal_01 250,0,50,100 -> 250,0,200,50,100,1; Rocket_RPG7_Hind likewise, and its DM12 = 1 -> DD14 = 1 | high |
| ZTriggerBox | 26 | 926 | DD8<-DM7, DD9<-DM8; DD7 new. Current: DD7<-DM7, DD8<-DM8, DD9 new | [C] vtable slot 25 (DM 0x69fff0, DD 0x42afd0) tests the bools in member order, each `jne` (skip) or `je` + call: DM jne,je \| jne \| jne \| jne,je; DD jne,je \| jne \| jne,**je** \| jne,je - the extra `je`+call is DD byte +0x4c = DD7 | medium-high |
| ZOnlineExitLevelTrigger | 5 | 5 | DD2<-DM0. Current: DD1<-DM0 | [V] DM0 is the escape vehicle path (5/5); DD1 = '' in 9/9, DD2 = the escape vehicle in 9/9 | medium-high |
| ZOnlineEscCamTrigger | 5 | 5 | DD1<-DM0, DD0 new. Current: DD0<-DM0 | [V] DM0 is a camera (EscCamera01/02); DD1 is a camera / cam relay in 45/45, DD0 is '' or the escape vehicle animation in 45/45 | medium-high |
| ZHeliFlyBehaviourRout | 4 | 60 | DD6<-DM6 (same enum), DD8<-DM7, DD9..12 new. Current: DD6, DD8 = default, DD9..11<-DM3..5 | [O] DM7 / DD8 is the list after the attack enum; DD9..12 are a new block behind it; DM3..5 sit before the enum where DD has two EHeliFacingMode enums and one bool | lists and enum high; DM3..5 not established (left unpaired) |
| ZPlayerAction | 4 | 34 | DD1..3<-DM1..3, DD4, DD5 new. Current: DD1, DD2 new, DD3..5<-DM1..3 | [V] DM1 is the main list (non-empty 28/34), DD1 non-empty 41/41, DD2 and DD3 empty 41/41, DD4/DD5 hold the per-player lists (..Door_Lynch / ..Door_Kane) | medium-high |
| ZOnlineFragileAllianceSettings | 4 | 4 | DD17..23<-DM12..18 (briefings); DD12..16, DD24..26 new. DD27..172<-DM19..164 as today. DM165..175 (11 tutorial lines) and DM176..179 (4 floats) left unpaired. Current: DD20..26<-DM12..18, DD173..183<-DM165..175, DD327..330<-DM176..179 | [V] event names of the dialogue lines: 121 of 140 non-empty pairs have similar names (the rest are renames in place: LastPossibleTransport/LastEsc, TimeReminder/OneMinLeft, Drop_Cash removed), 16 pairs empty in both; DM12..15 MissionBriefing = DD17..20, DM16 Police briefing = DD21; DD12..16 are interface paths, DD24..26 UCC briefings | strings high; tutorial lines, floats: not established |
| ZMiniCutsceneRout | 0 | 1080 | DD2<-DM2, DD3 new. Current: DD2 new, DD3<-DM2 | [O] base bool DM +0x32 = DD +0x3e, DD +0x3f is new: over the 7 behaviour classes stored by both games DM +0x32 is 1 in 2324/2506 objects, DD +0x3e in 4625/5329, DD +0x3f in 64/5329 | high |
| ZWarnBehaviourRout | 0 | 7 | DD3<-DM2, DD4<-DM3, DD2 new. Current: DD2<-DM2, DD3<-DM3 | [O] same rule: DD2 is the +0x3f bool | medium-high (no DD objects) |
| ZKillBox | 0 | 77 | DD10<-DM6, DD6 new. Current: DD6<-DM6 | [O] DM6 and DD10 are the bool behind the large embedded struct (DM +0x6c, DD +0x90), DD6 is a new bool right behind the list | medium-high |
| ZBarrelEffects | 0 | 42 | DD9<-DM0 (the list moved to the end). Current: DD9 = default | [T][V] only list on both sides, both hold `...GeomActivator` paths. Which five of DD0..5 take DM1..5: not established (kept as today) | list high |

ZParticleEmitter in detail (the big one). [O]: Dead Men keeps everything in the object
(+0x14..+0x80); Dog Days moved fields 0..19 into a struct behind `[this+0x18]` (accessor records),
and that struct still has the 12-byte hole of the old f*3 between DD6 (+0x28) and DD7 (+0x38) -
the vector itself (DM7, +0x40) now lives in the object at +0x1c = DD21. [N] 194 emitters with the
same parent\name: DD21=DM7 190 (chance 8), DD6=DM6 177 (22), DD7=DM8 176 (41), DD1=DM1 183 (13),
DD34=DM32 186 (2); the current DD6<-DM8 8 (3), DD7<-DM9 11 (11). [T]: DD20 and DM16 are the only
fields of type 71 (both 0xffffffff in every object). Flags: DM24..27 = bits 0..3 of +0x7d,
DM30/31 = bits 5/6; DD25..28 = bits 0..3 of +0x33, DD31/32 = bits 5/6; DD33 = bit 4 of +0x34 (new).
DD8<-DM10 rather than DM9: 193 (179) against 187 (187), DM9 is 0 in all 84,866 objects - either
way the stored value is 0. DD16<-DM18 agrees for only 99 of 194 (chance 87): position by layout
(bytes +0x70..+0x74 -> +0x58..+0x5c), value agreement weak.

## B. Right today (no map needed)

| class level | FA objs | DM objs | what is new in Dog Days | evidence |
|---|---|---|---|---|
| ZParticleTemplate | 1434 | 7843 | DD37 (f, +0x120, last) | [N] 405 same-named templates: every field with more than one value agrees with its own index (DD0 396 (chance 10), DD4 380 (15), DD29 389 (2), ...); [O] offsets identical |
| ZHavokShatter | 309 | 2190 | DD44..47 (f, b, f, f at +0x14c..+0x158) | [T] DD45 is a member bool, DM44..46 are accessor bools -> DD48..50; [O] DD0..43 = DM0..43 shifted by 4 |
| ZSoundLimiterFade | 98 | 600 | DD7 | [O] bools at +0x3c, +0x3d, +0x48 -> +0x44, +0x45, +0x50, new one +0x5c |
| ZFlankingBehaviourRout, ZHuntBehaviourRout, ZDefendBehaviourRout, ZPatrolBehaviourRout, ZIdleWalkPathRout, ZFollowBehaviourRout, ZCoveredMoveActRout, ZSquadModifierBehaviour, ZBloodLust-, ZFollowPlayer-, ZKillCivilians-, ZRunForHelpBehaviourRout | 28, 19, 11, 5, 5, 0, ... | 129, 37, 536, 23, 5, 35, ... | the bool at +0x3f (last field); ZPatrol also DD4..7; ZSquadModifier the enums Dog Days names differently, f DD24, b DD25 (its own list DM23 is dropped) | [O][V] the +0x32 / +0x3e / +0x3f rule above |
| ZTrafficFlow | 14 | 49 | DD10 | [O] +0x35 behind +0x34; DM9 and DD9 both 0 everywhere |
| ZCivilianRout | 11 | 213 | DD1..8 | [V] DM0 = 5000 in 154/213, DD0 = 5000 in 283/283 |
| ZTriggerCounter | 5 | 226 | DD3 (b, +0x41) | [V] DD3 = 0 in 412/412; medium |
| ZHeli | 2 | 12 | DD14..23 | [O][T] 14 identical leading fields, new ones behind |
| CCheckInside | 0 | 7 | DD10 | [V] usual values DM 1,0,1,0,0,0 / DD 1,0,1,0,0,0,0; medium |

## C. Not established / nothing to pair

| class level | FA objs | state |
|---|---|---|
| ZPlayerMonitor | 0 | restructured: Dead Men has 22 event lists, Dog Days one event enum + one list. Not a pairing problem; one Dead Men monitor would become several. Current plan keeps only DM2 |
| ZHeliMonitor | 0 | 7 -> 25 lists; no Dead Men level stores one |
| ZActorMonitor | 0 | 4 -> 5 lists of one type; 18 DM objects, 1 DD object; which is new: not established |
| ZVehicleGetAwayEffects | 0 | one float more in the last run; 2 DM objects, 0 DD objects: not established |
| ZItemState, ZItemStateProjectile | 0 | Dead Men's first field has no known shape (no level stores the class) |
| inside table A | | ZFFActor DM6; ZSoldierRout DM12 (DD16 or DD17) and all of it beyond "values fit"; ZVehicleEffects DD3/DD4, DD20/DD21; ZHeliFlyBehaviourRout DM3..5; ZBarrelEffects floats; FA settings tutorial lines and floats |

## Dog Days-only fields that need something other than the most common value

| field | most common in DD | wanted | why |
|---|---|---|---|
| ZItemTemplateWeapon DD8 | 30 | -1 | 8 of 10 legacy weapons have DD6 = DD8 = -1 (the other two were retuned); over all Dog Days weapons (-1, -1) occurs 108 times and DD8 = -1 never without DD6 = -1. DD6's most common value is already -1 |
| ZItemTemplateWeapon DD20 | 2 | 1 | 9 of 10 legacy weapons |
| ZItemTemplateAmmo DD2, DD4 | -1 | -1 | already right; fixed in the dict so it cannot drift |
| ZInventoryBinding DD2 | 150 | = DM1 | DD2 = DD1 in 538/692, larger in 125 (legacy launchers 1000). ASSUMPTION: copy DM1 |
| ZSoldierRout DD16, DD17 | 600000 | 800 | DD15 = 5000 comes with 800, 800 in 469/469 objects, 600000 only with DD15 = 1. ASSUMPTION |
| ZSoldierRout DD9..12 | 1 | 1 | already right; fixed in the dict |
| ZFFActor DD6, DD7 | -1 | -1 | already right once DM6/DM7 stop landing there (today they get 0) |
| ZItemTemplateWeapon DD17 | a muzzle flash list | DM15 as a one-entry list | type changed (string -> reference list); a map cannot express it, needs code. Until then empty |
| ZPlayerAction DD17, DD18 | eOnly_Mercs, UA_FA_ESCAPE | as is for FA | right for FA escape vehicles, wrong for anything else |

Everything else: the most common value equals what the unchanged legacy objects hold (checked for
ZItemTemplateWeapon DD21..31, ZItemTemplateAmmo DD13, DD14, CExplode DD2 = 200, DD5 = 1, DD17 = 0).
ZItemTemplateAmmo DD12 is 100 for bullets but 25 / 40 on legacy grenades and rockets.

## Checks run on the result

- The dict below was loaded into `kl_convert.LEVEL_MAPS` in memory and `Converter.wanted()` run:
  453 class plans built, 3638 paired fields, every pair has equal `label()`; `assumed` drops
  from 46 to 26 (tables B and C).
- Fine types [T] over the dict: no pair with different types except member/accessor variants
  (ZParticleEmitter) and two Dead Men types no identical-label level uses (the char of the FA settings, the WEAPONOPERATION flag set).
- The 25 class levels that differ but are not flagged "assumed" (ZGEOM, ZSNDOBJ, ZShotActivate,
  ZOnlineMoneyCtrl, ZItemTemplate, ZFFItemTemplateWeapon, ZCloth, ZROOM, ...): the difflib plan
  pairs no fields of different fine type (ZGEOM, ZROOM and ZOnScreenDisplay2 have Dead Men types the vote could not map: unchecked). Their values were NOT compared - not established beyond that.
- Not done: no level was converted or loaded with the new maps.

## Ready to paste (tools/kl_convert.py, merge into LEVEL_MAPS)

```python
F = lambda v: [(0x0a, struct.pack('<f', v))]          # a float token

def _run(*blocks):
    """(first Dog Days index, first Dead Men index, count) blocks -> {Dog Days index: Dead Men index}"""
    return {dd + k: dm + k for dd, dm, n in blocks for k in range(n)}

LEVEL_MAPS.update({
    # velocity vector DM7 moved to DD21, DM9 (always 0) dropped; 190 of 194 same-named emitters
    'ZParticleEmitter': {
        'map': {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 8, 8: 10, 9: 11, 10: 12, 11: 13, 12: 14, 13: 15,
                15: 17, 16: 18, 17: 19, 18: 20, 19: 21, 20: 16, 21: 7, 23: 22, 24: 23, 25: 24, 26: 25, 27: 26,
                28: 27, 29: 28, 30: 29, 31: 30, 32: 31, 34: 32},
        'values': {},
    },
    # the new float is DD7 (0 in every Dog Days object), not DD3: by values only
    'ZHavokRigidBody': {
        'map': {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 8: 7, 9: 8, 10: 9, 11: 10, 12: 11, 13: 12, 14: 13,
                15: 14, 16: 15, 17: 16, 18: 17},
        'values': {},
    },
    # DD2 (a second maximum) takes DM1 too: ASSUMPTION, DD2 == DD1 in 538 of 692 Dog Days objects
    'ZInventoryBinding': {'map': {0: 0, 1: 1, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}, 'values': {}},
    # 10 legacy weapons; DM15 (muzzle flash string, a list in Dog Days) and DM18 are dropped
    'ZItemTemplateWeapon': {
        'map': {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 7: 6, 9: 7, 10: 8, 11: 9, 12: 10, 13: 11, 14: 12, 15: 13,
                16: 14, 18: 16, 19: 17},
        'values': {6: F(-1.0), 8: F(-1.0), 20: F(1.0)},
    },
    # 13 legacy ammo templates
    'ZItemTemplateAmmo': {
        'map': {0: 0, 1: 1, 3: 2, 5: 3, 6: 4, 7: 5, 8: 6, 9: 7, 10: 8, 11: 9},
        'values': {2: F(-1.0), 4: F(-1.0)},
    },
    # DD0..2 one slot per LOD, DD5 the slot every character fills (DM1): by values
    'ZLNKWHANDS': {'map': {0: 0, 5: 1, 6: 2}, 'values': {}},
    # DM7 is a handle (type 46) = DD17; DM8 = DD19 by values (GUESS between DD18 and DD19); DM6 dropped
    'ZFFActor': {'map': {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 17: 7, 19: 8}, 'values': {}},
    # by values only. DM12 dropped; DD16/DD17 = 800 is what Dog Days stores next to DD15 = 5000: GUESS
    'ZSoldierRout': {
        'map': {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 13: 9, 14: 10, 15: 11, 18: 14, 19: 15, 20: 16},
        'values': {9: F(1.0), 10: F(1.0), 11: F(1.0), 12: F(1.0), 16: F(800.0), 17: F(800.0)},
    },
    # by constants; DM3 -> DD3 (not DD4) and DM14 -> DD21 (not DD20) are GUESSES
    'ZVehicleEffects': {'map': _run((0, 0, 4), (10, 4, 10), (21, 14, 21)), 'values': {}},
    # 3 legacy projectiles
    'CExplode': {'map': {0: 0, 1: 1, 3: 2, 4: 3, **_run((6, 4, 11))}, 'values': {}},
    # the new bool is DD7 (update function, kl2 0x42afd0 against Dead Men 0x69fff0)
    'ZTriggerBox': {
        'map': {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 8: 7, 9: 8, 10: 9, 12: 10, 13: 11, 14: 12, 17: 13},
        'values': {},
    },
    # behaviour base: Dead Men's bool is the one at Dog Days +0x3e, the new one is at +0x3f
    'ZMiniCutsceneRout': {'map': {0: 0, 1: 1, 2: 2, 4: 3, 5: 4, 6: 5, 7: 6}, 'values': {}},
    'ZWarnBehaviourRout': {'map': {0: 0, 1: 1, 3: 2, 4: 3}, 'values': {}},
    'ZKillBox': {'map': {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 10: 6}, 'values': {}},
    'ZPlayerAction': {
        'map': {0: 0, 1: 1, 2: 2, 3: 3, 6: 4, 7: 5, 8: 6, 9: 7, 10: 8, 11: 9, 12: 10, 13: 11, 14: 12, 15: 13,
                16: 14, 19: 15},
        'values': {},
    },
    # the three Dead Men bools (DM3..5) are not paired: not established which Dog Days field each became
    'ZHeliFlyBehaviourRout': {'map': {0: 0, 1: 1, 2: 2, 6: 6, 8: 7, 14: 8, 15: 9}, 'values': {}},
    'ZOnlineExitLevelTrigger': {'map': {2: 0}, 'values': {}},
    'ZOnlineEscCamTrigger': {'map': {1: 0}, 'values': {}},
    # the list moved to the end; the five floats stay where difflib put them (not established)
    'ZBarrelEffects': {'map': {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 0}, 'values': {}},
    # dialogue lines by event name; tutorial lines (DM165..175) and the four floats are not paired
    'ZOnlineFragileAllianceSettings': {
        'map': _run((0, 0, 12), (17, 12, 7), (27, 19, 146), (331, 180, 2), (333, 182, 6)),
        'values': {},
    },
})
```

Scripts and the per-class value dumps behind every number: scratchpad `agents/track-pairings`
(`build_cache.py`, `an.py` matrix, `side.py` same-named rows, `acc.py` offsets, `tmap.py` fine
types, `ctx.py` code context, `validate.py`). They are not part of the repo.
