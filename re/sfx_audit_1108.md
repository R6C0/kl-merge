# Sound audit, expansion maps, 2026-11-08 (read-only)

Tool: `tools/kl_sfx_audit_1108.py [MAP ...]` reads each live map zip's .SND plus the .WHD/.WAV beside it
(nothing written, no game launch). Checks: bank walks clean, every wave -> .WHD record resolves, every in-memory
record's data lies inside the .WAV, and which named sound objects exist per category (keyword match on names; GUESS:
it proves the event exists in the bank, not that a given script plays it).

| Map (slot) | waves | dead wave refs | in-memory records without data | sound objs | explosion | car expl. | door/kick | glass | shutter/garage |
|---|---|---|---|---|---|---|---|---|---|
| DM01 (F01) | 33493 | 0 | 0 | 5368 | 260 | 6 | 44 | 139 | 0 |
| DM03 (F03) | 33614 | 0 | 0 | 5440 | 259 | 6 | 69 | 155 | 3 |
| DM03A (F07) | 32535 | 0 | 0 | 5353 | 264 | 6 | 49 | 166 | 3 |
| DM06 (F04) | 33458 | 0 | 0 | 5319 | 260 | 6 | 38 | 109 | 0 |
| DM07 (F06) | 28576 | 0 | 0 | 4706 | 253 | 0 | 38 | 125 | 0 |
| DM09 (F06) | 32700 | 0 | 0 | 5533 | 274 | 9 | 53 | 155 | 0 |

Findings
- PROVEN: all six banks hold barrel/RPG/car/C4-style explosion, knee-kick (kick_knee_01..03), door and glass-break
  objects, and no wave reference is dead (0 of ~190k). No missing-sound gap was found for blast, kick or glass.
- PROVEN: each bank shows one walk note, "109 non-zero bytes no item claims" (same on DM07; not a missing event).
- PROVEN: DM07 has no car_explosion objects (others have 6-9). GUESS: DM07 has no drivable cars so nothing plays them;
  a car added later (see vehroutes work) would be silent on explosion. Fix would be a merge of explosion_car_0x from the
  DD stock bank; not staged.
- PROVEN: no shutter-named sound in DM01/DM06/DM07/DM09; only DM03/DM03A have garagedoor_open. GUESS: those maps have no
  shutters; a roll-down shutter added there needs the DM03 garagedoor objects.
- Not audited (other jobs/locked): DM01B, DM02, DM11B, DD10, DM05A, DM06B; run the tool on them to fill in.
- Not done: per-script check that each sound field in the .prp resolves (kl_snd.roots/sound_fields) and the
  grafted-DD-system event check; no bank was changed, so no sfx stage exists.
