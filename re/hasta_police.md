# Hasta (DM11B) plaza police: what build 3a186c93 changed, why 8 of 10 never start, what shot the heli (2026-10-18)

Offline, read only (tools/kl_fa.py load, kl_fa_hasta_police.py check, kl_fa_hasta_layer.py). Nothing launched, nothing written to the
game folder. Zips: live `ce42dcc9` = C:\kl_build_1018\owner_1018\Maps\DM11B\F04_Main.zip, police build `3a186c93` =
C:\kl_build_1018\hasta_next\DM11B\F04_Main.zip. Marks: FACT = read in the two .prp files or the source; GUESS = not proven.

## (1) Which change made 3a186c93, and the object diff
FACT: commit 702af665 (tools/kl_fa_hasta_police.py, default `--keep ExitStreet_Left`; de57449c only fixed the usage text). It is a post-pass
on the finished ce42dcc9. Of the zip members only `Scenes/Locations/F04/F04_Main.prp` differs; all other members and all side files are
byte-identical. Of the 21,286 nodes, exactly four differ:

| node | name | class | what differs |
|---|---|---|---|
| 19993 | `Gameplay!RunToEscape!RunToEscapeGate\Way#01` | ZBoxPrimitive | its 4 GatePath controllers (see below) |
| 19992 | `...\Way#02` | ZBoxPrimitive | same |
| 19991 | `...RunToEscapeGate` | ZGROUP | child bookkeeping only (the property/ctrl bytes before are the same) |
| 0 | ROOT | - | child bookkeeping only |

GatePath field 0 (the start list) of Way#01 and Way#02, same edit on both:
- ce42dcc9: four entries `030_FinancialAlleyExit_Left`, `030_FinancialAlleyExitStreet_Left`, `030_FinancialAlleyExit_Right`,
  `030_FinancialAlleyExitStreet_Right` (each `Gameplay!030_AfterLoot!<squad>\10_RunToCover`).
- 3a186c93: one entry, `030_FinancialAlleyExitStreet_Left\10_RunToCover`.

No squad, soldier or position object was touched (a squad's 10 men stay in the level; they are just never named). Men per squad
(ARRIVE_XZ in kl_fa_hasta_layer.py): Exit_Left 3, ExitStreet_Left 2, Exit_Right 3, ExitStreet_Right 2 = 10. 3a186c93 starts the 2 of
ExitStreet_Left only. `kl_fa_hasta_police.py check` says PASS on both zips.

## (2) Why 8 of 10 never start: by design, there is no second wake path
FACT: this is not a defect of the build; the post-pass removed their only start entry on purpose.
- The only objects anywhere in the level that name the four squads from outside are the two GatePath nodes (Way#01, Way#02). Nothing else
  (no TriggerBox, AIMonitor, timer) holds a path with `030_FinancialAlley`; the other hits are the squads' own children (DefendBehaviourRout
  `40_RunToEscape` / `10_Defend`, the RunToCoverPosInfoRout `RunToPosInfo#NN`, which name the squad's own men).
- Way#01 is fired by the floor box (`tb_RIGHT_TheySpotYou`, the stair top, together with the van timer); Way#02 by the backstop
  (`RivalMercVan!Timer`, 300 s, together with the van timer). Both lists are now the same single entry.
- Each squad: ZSquadScript `['eStayBack','eAllTypes','eNormalAlertness', 0 (field 3 = active flag), ...]`, so the active flag is 0 in
  both zips. Children: `10_RunToCover` (RunToCoverBehaviourRout, the start child), `30_smUnleash` (SquadModifierBehaviour eLM_Leash),
  `10_Defend`/`40_RunToEscape` (DefendBehaviourRout), 2-3 `Police_SWAT_01__*` groups, each with a ZFFActor `Ground` (ZSoldier eArmy,
  weapon template `SMG_Type05`).
- Source note (kl_fa_author.py, retomoto_spawns.md 1, a code READING, not run here): a squad with field 3 = 0 has its men HIDDEN at level
  start (kl2 0x787a10 -> 0x8d2e20) and shown when the squad gets its first goal (0x7f6750 -> 0x7c0d50). So the 8 unstarted men are
  most likely not just passive, they are not in the world at all (GUESS that this applies to these squads; it is the same field, same
  class). That also means they cannot "react when shot at", which the docstring of kl_fa_hasta_police.py allows for: probably they cannot.
- 43 ZFFActor+ZSoldier in the level have the same empty override; there is nothing per-man that wakes them.

## (3) What shot the heli
FACT (from 07:34 / 07:50 / 08:22 notes): in L44-46 and L49 the heli went to state 6 (destroyed) 0.9-4.9 s after lift-off with ~10 plaza
police alive (~34 m north of the pad); good in L9/L36/L47/L48 with 0-4 alive; L73 (2 started) good. There are no hit lines: the cause
is correlation only.
FACT about the objects: the heli is `V_Coli_Shot_01` (ZHeli, node 12031 under `Escape_Chopper`), with HeliWeapon (its own gun) and a damage
model (`Hind_Dammage_01` effects, `ShatterGeom`, a last field `ENEMY`). The police are ZSoldier eArmy with `SMG_Type05`
(range fields 150 / 5000 / 800, accuracy 85 / 82); there is no launcher on them (no rocket/RPG weapon in their template).
GUESS (mechanism): up to ~10 police on the square are awake and engaged, shoot at the airborne heli at 16-34 m with SMG fire (sustained
small-arms damage to a ZHeli whose faction field is ENEMY), the damage accumulates in a few seconds after lift-off, and the rules turn
state 6 into "everyone aboard dies". Also possible and not separable from the data: ZHeli health is simply low (the field set `100.0 /
300 / 500 / 2.5 / 4.5 ...` was not decoded) or the damage comes from splash of the bots' own fire; "SMG kills it" is the favoured guess
only because 2 men (L73) vs ~10 (L44-49) separates the runs.
Why L73 survived is the same guess in reverse: 2 SMG men are below the kill rate. Timing is also a candidate: L73 is a single run.

## Proposal: one opt-in flag, `--rest-late S` (rebuild or post-pass, default off)
Goal: the 8 passive men are not passive forever (pressure on the crew), but are not alive and awake while the heli is lifting off.
Change (3 GatePath edits, one spare object):
- Way#01 (floor box, stair top) keeps the 1 entry it has now (ExitStreet_Left, 2 men);
- Way#02 gets the other 3 squads (8 men) and is no longer fired by the backstop at 300 s but by a one-shot TriggerDelay2 (the layer's
  `FLOOR_DELAY` spare, `RivalMercVan!TimerVanGo`, used the same way by `--floor-late=N`) with f0 = S seconds, started by the floor box.
  The delay object is only kept in the build when the layer is run with the flag (KEEP); it is not in 3a186c93, so this needs a layer
  rebuild, not the post-pass alone. (A pure post-pass variant with zero new objects is possible: put the 8 men in Way#02 only, so they wake
  at the backstop, 300 s. That is weaker, and the van timer also fires then, so GUESS: it makes it worse.)
What it changes: the 8 men appear S seconds after the crew reaches the stair top instead of never; everything else is as 3a186c93.
GUESSES: S. Pick S after the heli has left on a normal run (the boarding time was not logged in the notes; L73's log is not in the repo
or in the work folders now). Proposed first S = 120 s, then read the L73-style log for call to lift-off and set S = lift-off + 5 s.
Risks: (a) a slow crew still has men awake at lift-off; (b) the late arrivals fight the stragglers; (c) waking squads while the human
is boarding could kill the human instead of the heli, which is a different failure. A cleaner (not level-only) alternative is the hook-side
refusal to call the heli while more than 2 plaza police live: the owner's call, not built.
