# Review of track Y3 (rappel), 2026-10-11 night. Offline. No commit.

VERDICT: ACCEPT WITH FIXES. The data step is sound and conservatively scoped. The track does not deliver a rappel,
and its recommendation contradicts its own finding on the clips.

Re-run: `kl_fa_rappel.py check y_rappel\DM09` gives PASS (0 FAIL). `facts` reproduces the clip numbers: Repelling_01/02/03
= 105/90/82 frames, root net y -1756/-1487/-1300, 277 frames = 11.1 s, 45.4 m. The files `tools/kl_fa_rappel.py` and
`re/rappel.md` are untracked and no hook file is touched. I did not re-disassemble the Dead Men or Dog Days vtable addresses
(0x967144, 0xbb5ebc and so on); they are taken from the worker's report.

## MUST
1. The recommended chain contradicts the evidence. re/rappel.md 2 says the three clips are "alternatives (three
   soldiers hang at three heights), not stages": each is the whole drop from its own PosObject to the ground, and their
   start heights (1756 / 1487 / 1300) equal their drops, so each clip ENDS ON THE GROUND. Section 3 form A and the
   recommendation then string them end to end as if the end of one were the start of the next. The only support is
   the ASSUMPTION in the code comment at line 26 (the end pose of one matches the start pose of the next). By the worker's own
   reading the end of clip 1 is a landing and the start of clip 2 is a hanging pose. Root motion adds up (45.4 m against 44.7 m)
   but the body pose will snap three times. That the "joins" are the risk is acknowledged; that the whole chain may be
   wrong is not. Before form A is built, compare the last frame's pose of 01 with the first frame's pose of 02 and 03
   (bone rotations; kl_anm and kl_view can do it offline). If they differ, use ONE clip from a PosObject at the right height
   (01 is 17.6 m, 02 is 14.9 m and 03 is 13 m, so none covers 44.7 m alone) or drop the idea of dropping the whole
   facade. State that in the doc.
2. The end point is wrong by the doc's own numbers. The chain ends at 25483 - 4543 = 20940 and the balcony row is y 21011.
   rappel.md 3 calls this "0.7 m under the balcony floor ... to be tuned". Also, the clips carry lateral root motion
   (net x/z of 160, -155 and -30 units, up to 1.6 m) that the chain math ignores, and the heading of POS_Repelling_01 is
   turned 180 degrees against 02/03 (not resolved). Fine to leave open, but they are MUSTs for the nodes, not footnotes.
3. The owner's wish ("definitely rappel") is not delivered: `apply` is inert (the doc says so, correctly), the nodes
   are not built, and the human (the player, not the bots) needs a new hook part that is not written. The report is honest
   about this. The final summary to the owner must say "nothing rappels yet", not "built".

## SHOULD
4. The chain's "11 s" has no room in the approved timing. The blast is GO + ~10 s and the player cannot move for ~10 s
   after state 0x19. A descent that starts at GO ends at GO + 11 s, after the blast, unless it starts in the pre-round, where the
   game does not run the player. Form B depends on that unsettled point. Settle it live first (L-R0/L-R3) before writing
   klrappel.c.
5. The claim that the bots' MiniCutsceneRout works on the Retomoto `ZFFActor` bots (they are not `ZSoldier` snow wolves)
   is not supported; rappel.md lists it as assumed. A cheap offline test: check that the actor classes in the squad nodes accept
   the `Actor| ... anim| ...` script (the field layout of ZMiniCutsceneRout is in kl2.json). It also needs the "unbreakable-vulnerable"
   mode, which the squads' health tuning ([Balance] / Tough) may not honour.
6. Form C (Dead Men's free rappel through the Dog Days movement 16) is dismissed on "not known whether the code works". The
   existing evidence is that the class, ctor and slot lookup are present in kl2; one dry live probe (make the movement, read
   the log) would settle it. It stays unrecommended, fine.
7. The doc has a small slip: the "one-frame hanging poses" in the report are the 2-frame `Repelling_0N_1F` clips in
   rappel.md (the doc is right). The clip name `Repilling_01` is spelled that way in the file; make sure `apply`'s name
   lookup does not depend on the corrected spelling (check passes, so apparently not).
8. The merged .ANM adds 5 clips and 35 list entries to seven sets, including Swat_02 and Thug, which Retomoto's guards use. This
   is harmless but unseen: live check L-R0 (load and reach GO) is the one gate, and the doc rightly makes it first.
   Do not put `y_rappel\DM09` on the owner's tab before it passes; it changes nothing visible, so there is no gain.

## Answered / fine
- No hook or stock file touched; KLTalk.ini unchanged (the worker's cmp claim is plausible; I did not repeat it).
- luvsic: no rappel code pushed (claimed, not rechecked; the only borrowed thing is his clip +0x2C fix, credited).
- Live checks owed are ordered correctly.
