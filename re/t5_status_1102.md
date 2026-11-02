# T5 status 2026-11-02 (branch wk-t5close-1102): gun icon / name / sound / remote-shot loudness, online vs Arcade

Offline research only; no code changed (no uncovered gap needs new code). Sources: re/gun_ui_parity_1028.md (A-E), re/gun_ui_sounds_1028.md,
week_plan_1028.md T5, open_work_log (GUN12b, GUN13-15, Q29), bench logs KL_PortTools/build/klhook/solo/GUN1..GUN15_*, SHOT2D.
kl_gunui_matrix.py is a STATIC archive reading, not a live result.

## Answers
1. MP45 (item 1, row 7) is NOT a swap row (pic 58 'SW MP45', same sound records and banks). Icon, name and sound are the same online and in Arcade.
   Only difference: remote shots play 3D online (own shots 2D); key [Sound] RemoteShot2D exists, default 0.
2. The real icon/name gap was swap rows 13/16/32/35 (HK69 / TYPE 81 / REM 700 / MINIMI) on unbaked archives. gunui_1029 baked DM07 + DD10;
   the other KLExpansion copies were already baked (1dbd01; DM01 8f69a4). All 21 archives (plain + .bots) read baked.
3. M-77B picture (GUN14_DM07 / GUN14_DD10 KLShot_inst2_34.jpg): NOT a baked picture. M-77B is a pistol list row, not a swap row, so it is the
   ordinary Dog Days card (identical on both maps, name and price $2,000 right). What differs between the two shots is per-map list content (DM07: USP,
   M9 BERETTA SIL; DD10: M9 BERETTA) and the primary (MP5 vs ZASTAVA M85). The baked-card evidence is GUN15_DM07 KLShot_inst2_259.jpg: row
   'REM 700 (LOCKED)' with a scoped-rifle picture, police reg 7700-R700. GUN15_DD10 inst2_259 is an in-round frame, so DD10's baked cards rest on archive + log only.
   The list highlight lags the info panel by a row (known).
4. Keys: none of OnlineSwap, OnlineSwapText, OnlineSwapPic, RemoteShot2D is set in the GUN15 inis, so GUN15 shows the baked archive WITHOUT hook help.
   In KLHook.ini they are commented, all 'recommended off'. GUN12b (DM07, pre-bake, keys on): OnlineSwap OURS on all four rows, OnlineSwapText=2 answered
   HK69/Type 81 over 'TOQ', OnlineSwapPic 7494 swaps = restores, 0 write failures, 0 faults. Never benched: OnlineSwapPic or Text on a genuine stock slot
   F01-F09 (GUN4-6 'f02' was the baked KLExpansion copy; GUN6 stock text 0). OnlineSwapPic never fires on a baked map (by design).
5. Remote-shot loudness: SHOT2D (F06) proved only 'vtable route installed, slot 74'; its script died before any shot. GUN1-6, 12b (all with RemoteShot2D=1 + LogAny=1, vtable route ready, code route REFUSED) and GUN15 (key off) and SHOT2D logs hold
   0 'played 2D' / 'would play 2D' lines. The gate caller (0x4cca6d) is unverified for REMOTE replicas. Arcade has no remote humans, so 'matches Arcade'
   means 'own-shot level'. Open since 10-28.

## Table
| map | icon | name | sound | remote-shot loudness | bench |
|---|---|---|---|---|---|
| DD01 | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DD02 | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DD03 | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DD04 | matches Arcade (baked card; osw OURS on rows 13/16/32/35) | matches Arcade (baked text, pool OURS) | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | GUN1-3 (oswlog STOCK then OURS 1 s later) |
| DD05 | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DD06 | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DD07 | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DD08 | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DD09 | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DD10 | matches Arcade by archive (baked ff017d); not seen in a shot | matches Arcade by archive (baked text) | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | GUN14/15 post-bake (archive + log; no shelf shot of a swap row) |
| DM01 | matches Arcade by archive (baked card 8f69a4); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DM01B | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DM02 | matches Arcade (baked card; osw OURS on rows 13/16/32/35) | matches Arcade (baked text, pool OURS) | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | GUN4-6 (GUN6: OURS at once, shop text baked) |
| DM03 | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DM03A | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DM05A | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DM06 | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DM06B | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DM07 | matches Arcade (baked card ff017d; REM 700 card seen in GUN15_DM07 shot 259) | matches Arcade (baked text) | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | GUN12b (pre-bake), GUN14/15 post-bake shots |
| DM09 | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |
| DM11B | matches Arcade by archive (baked card 1dbd01); not seen live | matches Arcade by archive (baked LOC text); not seen live | matches (same 61 shot records, same banks; static) | gap/unknown: RemoteShot2D=1 (+LogAny) was ON in GUN1-6 and GUN12b (vtable route ready, code route refused) and logged 0 played-2D lines; off in GUN15; no remote shot verified | none live |

Stock slots Scenes\Locations\F01-F09 (untouched by rule) still hold TOQ text and stock cards. Keys that close it at runtime (no new code):
name = [Shop] OnlineSwapText=2 (needs [Shop] Enable=1); picture = look-alike via OnlineSwapPic=1 (the true card is impossible there);
hand-over = OnlineSwap=1 + OnlineSwapArm=1. Benched on unbaked DM07 only (GUN12b), not on an F0x slot.

## Remaining gaps (bench work, existing keys)
- G1 remote shot loudness: TEST dll, RemoteShot2D=2 (dry) then 1, RemoteShot2DLogAny=1, no shop step (start MP45), both seats shoot at 3 m and 20 m, one map
  (e.g. DD08). grep: 'shot2d: .*would play 2D', 'played 2D', 'caller'.
- G2 stock-slot shelf: two-seat run on an unbaked F0x slot with OnlineSwap=1, OnlineSwapArm=1, OnlineSwapText=2, OnlineSwapLog=1, OnlineSwapPic=1;
  grep 'oswlog:', 'shoptext:', 'shoppic:'; shot of the list rows 13/16/32/35.
- G3 client seat first reports STOCK then OURS ~1 s later (state 0x16): does a buy in that second hand over the stock gun? Buy row 13 at once on the joiner.
- G4 HUD dial online: archive check only; grep 'hud: weapon:' on DD01, DM01, DM11B.
- Static-only (no live look): DD01-03, DD05-09, DM01, DM01B, DM03, DM03A, DM05A, DM06, DM06B, DM09, DM11B (grouped bench list in gun_ui_parity_1028.md E).
