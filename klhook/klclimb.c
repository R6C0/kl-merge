/*
 * klclimb.c - THE WALL CLIMB DEAD MEN HAD AND DOG DAYS DROPPED, for the local player: at a marked edge of the level he
 * is carried up by Dead Men's own climb clip (or, as a fall-back, by Dog Days' own vault action).
 * NOT WIRED: klhook.c does not include this file (WIRING, at the end of this comment). NOTHING HERE HAS RUN IN THE
 * GAME. Third version, 2026-10-11, after two reviews: re\climb_review.md (its M1, S1 .. S4 are named 'review' where they
 * are met) and re\climb_review2.md (its D1 .. D3 and N1 .. N4: named 'second review' where they are met).
 * It COMPILES: a copy of klhook\ with the three WIRING lines added built the SHIP hook (build.bat) and the TEST hook
 * (build_auto.bat) without a warning; cl /W4 gives no warning from this file either. No DLL of that copy was installed.
 * Its state machine passed an off-game test against a MODEL of the frame as section 1 reads it (re\climb.md 4.3):
 * evidence that the file does what the reading asks for, none that the reading is the game.
 * Written from static reading of kl2.exe build 0490 and kaneandlynch.exe; the account, every address and the live
 * checks K0 .. K8 are in re\climb.md.
 * Off unless KLHook.ini has [Climb] Enable=1. Arcade only (ZGameRulesHeist), never on a stock level, the game's own
 * thread only. NO data write of the hook's own and no code byte: calls of game routines, and what those routines
 * take for granted of the player is tested before EACH call - at the start and again at the end.
 *
 * 1. WHAT THE GAMES DO (re\climb.md 1 .. 3; every kl2.exe line here was read again for this version)
 *    Dead Men: ZFFPlayerMovementClimb (kaneandlynch.exe vtable 0x966c44) asks for NO level data. Its test 0x605b50
 *    finds an edge with rays (four probes straight down 25 / 40 / 55 / 70 in front, a clear way 15 over the top, 180
 *    headroom, a face 1 under the edge), 25 < h <= 220 over the feet; table 0x603340: Low h <= 120 clip slot
 *    '/Movement/Climb/Up/Low' stand-off 81, Medium <= 170 '/Movement/Climb/Up/Medium' 47, High <= 220
 *    '/Movement/Climb/Up/High' 47. Enter 0x602f30 plays the clip and aligns it twice (0x526620): the feet at the foot
 *    of the face, stand-off back from it, at clip event 5; the same place at top level at event 6; after that the
 *    clip's own root motion goes on (High: 91 forward and 24.5 up, so he ends ON the obstacle, 44 past its face).
 *    Dog Days: no such movement class. What it has, all read:
 *      0x5ea340  ZFFPlayer::StartMiniAnim(u16 slot, x, alignObject, char endWithClip), ret 0x10: stops the current
 *                action, makes ZFFActionMiniAnim (kind 0x23, vtable 0xbb4f0c, 0x28 bytes: +8 player, +0x18 slot,
 *                +0x1c alignObject, +0x20 the playing channel, +0x24 'reports count', +0x25 endWithClip) and starts
 *                it. Start 0x76d1d0: no clip for the slot -> [player+0x2758] = 1 and the action is over at once (no
 *                fault); else the weapon is lowered (0x74c040) and Play(clip, 1) (vtable +0x204) runs with byte
 *                +0x24 cleared. The game calls it from two places: 0x5022c0 (from 0x60b5c2, the stagger at a blast,
 *                ordinary play) asks for 'no action' (vtable +0x388 == 0) and down state [[player+0x2940]+0x24] == 0;
 *                0x607950 (ZMiniPlayerMoveTask, a mini cutscene's task) passes an align object and endWithClip = 0.
 *                Both leave the collision ON. It hands a null action to the start when the action pool 0x15151c0
 *                is empty (0x5ea3bc): the game's own flaw.
 *      WHO REPORTS A REPLACED CHANNEL (new, read): Play 0x4da1d0 itself, before it returns. With flag bit 0 it stops
 *                every one of the 16 channels ([player+0x70] + 0x1c + 0x38 * i: +0 clip, +4 the frame it is at, +8
 *                from, +0xc to, +0x10 frames a second, +0x14 flags, +0x18 id) that plays (state = flags & 7 = 1 or
 *                3) and is of the new clip's body class (flag 0x8000 <-> clip record +0x28 bit 0x10 clear), and
 *                reports each (0x4da711 .. 0x4da751): vtable +0x2e4 = 0x7cc140 -> 0x8f0df0 -> the dispatcher's slot 7
 *                0x5d0260 -> the CURRENT action's slot 10 -> if that says yes, the dispatcher's slot 6 0x595b70: End,
 *                then delete. The dispatcher makes an action current BEFORE its start runs (0x672d00). The mini
 *                animation's slot 10 (0x42b7f0) answers byte +0x24, which is 0 around its own Play: it survives.
 *                The vault's slot 10 is 'mov al, 1' (0x553070): a vault started while a full-body channel plays is
 *                ended and freed inside its own start, which then goes on with the freed object (0x6a2a62 ..).
 *      0x80fdc0  ZFFPlayer vtable +0x208 AlignTo(rot[9], pos[3], float frames) -> al: the first playing full-body
 *                channel whose clip has record flag 0x40 (0x760120) is corrected so that its ROOT is at pos / rot
 *                when `frames` more frames have played (channel flag 0x200); from then on the correction stays whole
 *                (0x50b0f6 .. 0x50b131) and the clip's own root motion goes on. rot = a node's world axes as
 *                0x857110 gives them: row 0 = the image of local z = where the BACK points (a clip's root runs along
 *                -z), row 1 = up, row 2 = the image of local x. 0x55f8f0 (ecx = out[9], edx = in[3]) makes such a
 *                matrix from the vector that is to be row 0 - what the vault 0x619790 calls with the cover's normal.
 *                This is the routine Dog Days' own NPC link mover 0x4a5160 calls for these very clips.
 *      WHO MOVES HIM WHILE THE CLIP PLAYS (read; the second review's N1 is in): ZPlayer's frame 0x74efc0 does
 *                nothing while byte [player+0x7a4] is set (0x710da0 instead), byte [player+0x430] is clear, or bit
 *                0x800 is set in the flags [+0x3c] of the node [[[[player+4]+0x50]+0x60]+4] - the node of the object
 *                0x598460 reaches from his own, the owner of what his node hangs on (0x74efe6 .. 0x74eff8; the game
 *                reads through that chain with no test). Else it runs the animation update (vtable +0x2e8 = 0x50ac80 at
 *                0x74f041, which also reports the channels that ENDED, 0x50b5e8 .. 0x50b645), reads the node's world
 *                transform as the move's 'from' (vtable +0x578 = 0x5aa510 at 0x74f057), runs Move (vtable +0x63c =
 *                0x6e6730 at 0x74f077) and at its end WRITES THE NODE from Move's result (vtable +0x60c = 0x693400
 *                -> 0x8caf30 at 0x74f2df; that routine does not touch the proxy) unless [player+0xd50] is not 0
 *                (vtable +0x678 = 0x5380d0 at 0x74f2c5). Move asks vtable +0x668 = 0x6d4570: is he 'moved by
 *                animation' (0x41a6b0: the channel 0x760120 finds has flag 0x200 = aligned, or its clip moves bone
 *                0x39) - then the frame goes to the ANIMATION movement [player+0x634] (ZMovementAnimation, vtable
 *                0xba6e94, update 0x5397e0) whatever the action's kind is, else to the current one [player+0x6b4].
 *                0x5397e0: its slot 35 0x536a20 makes the result = 'from' moved by the frame's root delta (vtable
 *                +0x5f8 = 0x72d010 hands out [player+0x20] and [player+0x44 .. 0x4c], what the animation update left
 *                there) - THAT is how the node follows the clip - and then the physics step (movement slot 33 =
 *                0x6d1ad0: the character proxy [player+0x7d0] is integrated and the result becomes THE PROXY'S
 *                PLACE) only while the collision flag is set (vtable +0x630 = byte [player+0x7a5]). So with the
 *                collision off the node follows the clip and the proxy STAYS BEHIND; and in the very frame the clip
 *                ends - End runs inside the animation update, Move right after it - the ordinary movement steps from
 *                the proxy again and the frame writes the node there: he is back where the proxy stayed.
 *      0x4af5b0  ZFFPlayer: the proxy is put at the node (if [player+0x7d0]: 0x7b3020 node place * 0.01 ->
 *                0xa768b0 -> the proxy's phantom 0x9fc110). EVERY routine of kl2.exe that ends an animated move of
 *                the player calls it, the actions inside their End, BEFORE the collision goes on: the vault's End
 *                0x82f796 then +0x564 at 0x82f7a6, ZFFActionJumpOver 0x5c8fa3, the mini cutscene's act 0x447bf2;
 *                the fall's clip end 0x4815c0 has the two the other way round. 31 call sites.
 *                ZFFActionMiniAnim's End 0x6fb600 only stops the channel: the game never carries a player with it
 *                WITH THE COLLISION OFF (with it on the proxy goes along through the physics step).
 *      0x5d6200 / 0x686600  ZFFPlayer vtable +0x560 / +0x564: character collision off / on. 0x8c5270 / 0x8b41c0:
 *                ++[player+0x7b4], [player+0x7a5] = 0 / the count back (not below 0) and [player+0x7a5] = 1 at
 *                zero; 0x5d6200 also clears byte [player+0x968]; both set the body's Havok layer (0xc / 5, whatever
 *                the count is) through 0x40ed30 on [[world+0x11840+4*[player+0x27cc]]] (5,000 entries, count at
 *                world+0x1183c: 0x4adce0).
 *      THE GAME'S CLOCK  [[0xdd2640]+0x48], 1024 a second (0x70da30: raw clock + an offset that is re-based every
 *                frame while the pause byte [[sys+0xac]+0xbc] is set, so it STANDS STILL in a pause; the frame's
 *                step [sys+0x50] is its difference and 0x50ac80 advances every channel by it).
 *      0x619790  ZFFPlayer::StartVaultOver(cover *, char left, float pos[3], float rot[9], char given, char
 *                writeBack), ret 0x18: makes ZFFActionVaultOver (kind 0x2b, vtable 0xbb5188) and starts it; with
 *                given = 1 the end place and rotation are the caller's (the network receiver 0x60c610 does that).
 *                It tests nothing but the action pool (empty: it returns 0 at 0x619826 -> 0x6199c7 and has stopped
 *                and started nothing; else it returns 1 whatever became of the action); of the cover record it reads
 *                +0x0c (3 floats), +0x2c (3 floats), +0x54 (float) and keeps the pointer at action +0x7c, which
 *                nothing reads. Start 0x6a27e0: leave cover 0x5fcb80 FIRST (0x6a2817; it writes through
 *                [player+0x2810], [player+0x2948], [player+0xccc]; reads the session [0x168e598]; 0x784460 when
 *                [player+0x2f70] is not -1), a Havok phantom ([world+0x14ec]), the collision off (0x6a2a4a), Play
 *                (0x6a2a5d), AlignTo (0x6a2a8a). Its End does the proxy and the collision ITSELF - so an End that
 *                runs BEFORE 0x6a2a4a gives nothing back (0x8b41c0 does not count below 0) and the start then
 *                switches the collision off with no action left to switch it on (second review D1: section 2). Its
 *                clip is one of '/Cover/Vaulting/Cover_Vault_{Left|Right}_{1M|2M}' (2M when the way is over 175): a
 *                hop made for a 1 m obstacle, whatever it is carried over.
 *
 * 2. WHAT THIS FILE DOES
 *    The edges come from the level's KLJoin.ini (the file kljoin.c reads beside the archive; tools\kl_fa_climb.py
 *    writes the [Climb] sections and has checked every one against the build's collision with Dead Men's rule - the
 *    hook casts no ray). In an Arcade round that runs (session state 0x19) on a level that is not the stock one of
 *    its slot, on the game's thread, twenty times a second, for the local human (a heister, alive, not attached to a
 *    vehicle):
 *      he is AT THE FOOT of an edge when his node's place is 15 .. 70 from the face on the side Normal= points to
 *      (Dead Men's probes reach 25 .. 70), between A and B, and his height (the node's, else the floats at +0x460:
 *      whichever is within 40 of Floor=) fits. If he stays there for Dwell ms, slower than Speed, looking at the face
 *      within Angle degrees (and with Key down, if a key is set), and klq_refuse lets him pass - no action, down
 *      state 0 (the game's own test), NOT IN COVER ([player+0x2954], bit 0x80 of [player+0x818]: what 0x40f840
 *      tests), standing or walking (movement kind 2 / 3), an ordinary frame ([player+0x7a4] clear, [player+0x430]
 *      set, bit 0x800 of the node 0x598460 reaches clear, [player+0xd50] 0: the four gates of 0x74efc0 - behind
 *      any of them the clip would play and he would not move), nobody has his collision off, and everything the calls
 *      below go through can be read:
 *      Mode=climb   the class is taken from the top over HIS FEET by Dead Men's table (not from Floor=); its slot
 *                   name is looked up in the level's slot table (read, as the game's own search 0x68a730 reads it);
 *                   StartMiniAnim(slot, 0, 0, 1). If the game kept the action (its vtable, this player, this slot, a
 *                   channel that plays, and that channel is the one 0x760120 would hand to AlignTo), the clip is
 *                   aligned as Dead Men aligns it: Align=2 - the foot place P1 (the point of the face nearest to
 *                   him, stand-off back along the normal, at his own height) at the frame of event 5, then, when
 *                   that frame has come, P2 = P1 raised by (top - his feet) at the frame of event 6; Align=1 - one
 *                   alignment at the last frame, to the place Dead Men's would end at, 10 OVER the top (KLQ_LIFT;
 *                   second review N3): the game blends the one correction in up to the last frame, so aimed AT the
 *                   top he would cross the face 1.8 .. 7.6 under it (measured on High for a top 183.5 .. 220 over
 *                   his feet; Medium up to 7.0); with the 10 he crosses it 0.8 .. 6.6 over it and comes down the 10
 *                   when the clip is over. Align=1 is not for class Low (refused): that clip lunges 52 forward in
 *                   its first 3 frames and only Dead Men's first alignment takes it back - he would run through the
 *                   face at foot level.
 *                   Only when the game has taken the alignment is the collision switched off (the game's vault has
 *                   the three in the order off, Play, AlignTo; nothing runs between them here either). If the game
 *                   finds no channel to align, the action is stopped at once and nothing else was changed. If the
 *                   SECOND alignment cannot be set (the frame of event 6 came in one long step, or the channel the
 *                   game would align is not the climb's any more) the climb is called off - stopped and given back
 *                   as at THE END below: without that alignment the clip rises by its own height only.
 *                   THE END (review M1; section 1 'who moves him'): from HandFrames (5) frames before the clip's
 *                   last one on, as soon as his node is 10 beyond the face - and in any case in the last tick before
 *                   the end (one and a half ticks' worth, at least one frame) - the hook HANDS HIM OVER in the
 *                   game's own order: the proxy is put at the node (0x4af5b0), then the collision is switched on
 *                   (0x686600). The last frames then play as the game's own mini animation plays, under the proxy,
 *                   and the action ends with its clip. It has to be done BEFORE the clip ends: the game steps the
 *                   ordinary movement from the proxy in the frame of the end, before any tick of this file.
 *                   Measured on the clips (re\climb.md 2.3): High is 10 beyond the face from frame 45.1 of 51, so
 *                   the hand-over comes at frame 46 (15 beyond the face, 24.5 over the top) and he walks 29 further;
 *                   Medium is 10 beyond only from frame 34.6 of 36; Low reaches the face at frame 25.7 of 26 - its
 *                   hand-over finds him in the air before the edge (not for a live run before High has been seen).
 *                   If the action goes earlier (another action, a death, one frame of the game longer than the
 *                   margin: 5 frames are 200 ms), the same two calls are made as soon as it is seen gone - by then
 *                   the game has him back where the proxy stayed (the foot), which is the clean way to fail.
 *                   NEVER INTO THE OBSTACLE (second review N4): whenever the two calls are due and his node is
 *                   between the obstacle's faces (less than 15 clear of either) and more than 3 under its top, the
 *                   proxy is NOT put at the node - the collision alone is switched on and the game's next frame
 *                   steps him from where the proxy stayed. That is the case of a climb this file calls off after the
 *                   first alignment only: its node is 28 under the top and beyond the face from frame 43 on.
 *                   Before EACH of those calls what they go through is read again (klq_carry_refuse: the object is
 *                   still one of the game's 28 players, his node, the proxy's phantom, the physics world, his body
 *                   entry); if that fails nothing is called, it is said, and it is tried again for 3 s (review S1).
 *                   The time-out runs on THE GAME'S CLOCK (review S2): an action that is still there 1.5 s of game
 *                   time after its clip's length is stopped (vtable +0x374) and given back. A pause that sets the
 *                   game's pause byte holds that clock and the clip alike; with the window not in front no tick of
 *                   the game's thread comes at all.
 *                   After the end the place is logged at +0.5 and +1 s and at +2 s a RESULT line says where he is: UP
 *                   on the obstacle, ACROSS (beyond its far face), INSIDE THE OBSTACLE (between its faces, under its
 *                   top), BACK AT THE FOOT (it did not hold), ELSEWHERE.
 *      Mode=vault   (or Fallback=1 when the body's set has no climb clip) one call: 0x619790 with a cover record of
 *                   this file's own and given = 1, end place = the middle of the obstacle's top. Tested before
 *                   (review S4): both vault slots have a clip for this body (0x59d550: two numbers of the game's
 *                   generator are drawn; without a clip Play returns no channel and 0x6a2a65 reads through it); NO
 *                   channel plays that the vault's Play would replace and report (section 1: that report ends and
 *                   frees the vault inside its own start - here it is a refusal with the count); what leave-cover
 *                   and the start write through. That count is of the MOMENT (the clips of the vault's body class
 *                   are also the walk, stop and turn clips - second review D2): the refusal is said once ('NOT
 *                   vaulted yet') and asked again four times a second while he stands there; when it has stood for a
 *                   second a line says 'REFUSED from this stand' with the number of tries, and if a later try
 *                   passes the 'VAULT started' line says how many refusals went before.
 *                   After: the current action must be the vault's. If it is not, his collision count and flag are
 *                   read (second review D1; klq_refuse had them at 0 and 1 in the same tick): a start that left the
 *                   collision switched off with no action to switch it on gets the two calls of THE END from this
 *                   file at once (or, if they cannot be made, for 3 s), with a line that says so, and a RESULT line.
 *    WHAT THE PLAYER SEES (expected, not seen): at the bank's yard wall (top 203.5 over the yard = High) he pulls
 *    himself up in 2.08 s and stands on the wall, 5 short of its far edge; a step on and he drops to the street (253
 *    down) or onto a dumpster lid (122 down) by the game's own fall. From the street the wall is 253 high: no climb,
 *    as in Dead Men. The AI heisters get nothing from this file: they keep their drop link through the sunk piece.
 *
 * 3. WHAT IS NOT DEAD MEN'S WAY, NOT DONE, NOT KNOWN
 *    - He is turned SQUARE to the wall (the matrix is made from the edge's normal); Dead Men keeps his heading (its
 *      matrix is made from his own back vector, 0x42fba0) and measures P1 back along that. Chosen: the end place on
 *      a 50-thick wall is then the same from every angle of approach.
 *    - No ray is cast (a car parked at the wall, a body: he is carried through it - the collision is off).
 *    - No input is taken away; an action the player starts during the climb (a reload ...) ends it early, and so
 *      does ANY channel of his that ends meanwhile (the mini animation's slot 10 says yes to every report once its
 *      own Play is over): he is then back at the foot, and the RESULT line says so. Live check K4.
 *    - A gamepad has no Key. With Key=0 (the default: a scripted run cannot press a key that GetAsyncKeyState sees)
 *      0.4 s at the foot, facing the wall, is the request - Dead Men asks for the USE tap; for play set Key=0x45.
 *    - The other players of a network round would see a slide, hence Arcade only.
 *    - The facing test rests on 'row 0 of a rotation is the back', read and not seen (the line at the foot prints
 *      the number: 1 = he looks straight at the face; Angle=0 switches the test off).
 *    - The vault's End also resets BaseMove's locomotion state (0x594960 -> 0x6721a0); this file does not (the
 *      game's own mini animation does not either).
 *    - Vault mode: 0x5abbb0 and 0x834ef0, which leave-cover calls inside the vault's start, were not read. If one of
 *      them ends the vault before its start has switched the collision off, the game's start goes on with a freed
 *      object (its flaw; this file can only refuse what it can count) and leaves the collision off: THAT this file
 *      sees and gives back (second review D1).
 *    - What Havok does with him after the hand-over - the proxy put 24.5 over the wall top while the clip still
 *      walks: whether the animation movement lets him fall, how he settles - could not be read. Live check K2 shows it.
 *    - What ends a climb early without anybody pressing anything: every channel of his that ends is reported and the
 *      mini animation says yes to each (weapon handling, faces: 872 clips of the other body class in the bank build,
 *      counted by the second review). The game's own stagger has the same exposure. It is the likeliest way K2 fails.
 *    - Which pauses set the pause byte was not read; whether the game's clock jumps when the window comes back to
 *      the front was not read (if it does, the clip jumps with it and ends in that frame: he is back at the foot).
 *
 * KLHook.ini
 *   [Climb]
 *   Enable=0          1 = this file is on
 *   Dry=0             1 = everything is watched and logged, NO game routine is called (live check K1)
 *   Mode=climb        climb | vault
 *   Fallback=0        1 = Mode=climb uses the vault at an edge when the body has no climb clip
 *   Align=2           2 = Dead Men's two alignments (events 5 and 6), 1 = one, at the last frame, to 10 over the top
 *                     (High and Medium only)
 *   HandFrames=5      the proxy and the collision are given back from this many frames (25 a second) before the
 *                     clip's last one on, once he is 10 beyond the face (1 .. 5). That test, not this number, keeps
 *                     a hand-over from coming before he is over the obstacle (High passes it from frame 45.1 of 51,
 *                     Medium from 34.6 of 36), so 5 costs nothing; it leaves 200 ms: one frame of the game longer
 *                     than that, begun before the hand-over, ends the clip unseen and he is back at the foot (3
 *                     left 125 ms: second review N2)
 *   Low=0             1 = edges of Dead Men's class Low (25 < top <= 120 over his feet) are climbed too; its clip
 *                     ends at the edge, so they are off until High has been seen (Medium and High are on)
 *   Key=0             a virtual-key code that must be down (0x45 = E); 0 = none: standing at the foot is enough
 *   Dwell=400         ms at the foot (100 .. 5000)
 *   Speed=150         slower than this, units a second (Dead Men asks under 375)
 *   Angle=60          he must look at the face within this many degrees; 0 = not asked
 *   Log=1             2 = also, every second, where the player stands against each edge near him (every 5 s when
 *                     he is near none: node, +0x460 and the proxy's place)
 * KLJoin.ini beside the level archive (written by tools\kl_fa_climb.py; up to 8 edges: [Climb], [Climb.2] ..)
 *   [Climb]
 *   A=-3450 403.5 -625        the two ends of the edge, x y z (y is up, the same in both): the top of the obstacle
 *   B=-2650 403.5 -625        on the face that is climbed
 *   Normal=0 -1               x z, unit, level: out of that face, towards the side one stands on
 *   Floor=200                 the floor at its foot
 *   Depth=50                  how thick the obstacle is behind the edge
 *
 * LOG (the numbers are examples: he stands at z -665, 40 on the yard side of the face at z -625; P1 is z -672, 47 from
 * it; at frame 46.2 of High he is 17 beyond the face = z -608 and 24.5 over the top = y 428; the clip ends 44 beyond
 * it = z -581. In the HAND-OVER line the FIRST place is where he stood, not P1: an alignment moves the node, not the
 * proxy - second review D3. Everything after the hand-over is expected, not seen.)
 *   climb: on; Mode=climb Fallback=0 Align=2 HandFrames=5 Low=0 Key=0 Dwell=400 Speed=150 Angle=60 Dry=0 Log=1; ...
 *   climb: 2 edge(s) from <file> for level f01\f01_main
 *   climb: edge 1: (-3450, 404, -625) - (-2650, 404, -625), 800 long, out of the face (0, -1); floor 200: 203.5 up = /Movement/Climb/Up/High, stand-off 47; 50 thick
 *   climb: node (-1250, 220, -1250), +0x460 (...), proxy (...): near none of the 2 edge(s), speed 310          (Log=2, every 5 s)
 *   climb: node (-3003, 200, -700), +0x460 (...): 75 from the face of edge 1, 447 along it (0 .. 800), +0 / +20 to its floor, speed 120, facing 0.99, 1 full-body channel(s) of his play      (Log=2, every second)
 *   climb: at the foot of edge 1: node (-3003, 200, -665), +0x460 (-3003, 200, -665), proxy (-3003, 200, -665), 40 from the face, speed 110, facing 0.99; the top is 203.5 over his feet = /Movement/Climb/Up/High, id 2505; 1 full-body channel(s) of his play as he arrives
 *   climb: edge 1: WOULD climb by /Movement/Climb/Up/High (slot 2505) from node (...), 40 from the face: P1 (...) at event 5, P2 (...) at event 6; 0 full-body channel(s) of his play NOW (after the dwell) - DRY RUN, nothing is called
 *   climb: edge 1: started /Movement/Climb/Up/High (slot 2505) from node (...), +0x460 (...), 40 from the face: action 0b7f2a40, clip 0a2c1e30 of 52 frames (flags 10c0), events 5 at 6 and 6 at 20; aligned to (-3003, 200, -672) in 6 frames
 *   climb: collision off (the climb starts; count 0 -> 1)
 *   climb: edge 1: frame 6.3: aligned to P2 (-3003, 404, -672) in 13.7 frames
 *   climb: edge 1: frame 46.2 of 51: HAND-OVER - the proxy put at the node: proxy (-3003, 200, -665) -> (-3003, 428, -608), node (-3003, 428, -608); collision on (count 1 -> 0)
 *   climb: edge 1: over after 2080 ms of game time (2090 ms by the clock), last seen at frame 50.6 of 51: node (-3003, 428, -583), +0x460 (...), proxy (...); his action now 00000000, his collision count 0
 *   climb: edge 1: +500 ms: node (-3003, 404, -581), +0x460 (...), proxy (...): 44 beyond the face, +0 to the top
 *   climb: edge 1: RESULT 2 s after the end: UP - he stands on the obstacle, 44 beyond the face, +0 to its top
 *   climb: edge 1: RESULT 2 s after the end: BACK AT THE FOOT - 40 on the near side of the face, -204 to the top: the climb did not hold
 *   climb: edge 1: ended at frame 31.0 of 51 BEFORE the hand-over (...): the game has him where the proxy stayed
 *   climb: edge 1: stopped - the proxy is NOT put at the node: node (-3003, 376, -609) is 16 beyond the face of a 50 thick obstacle and 28 under its top = INSIDE it; the proxy stays at (-3003, 200, -665) and the game's next frame steps him from there; collision on (count 1 -> 0)
 *   climb: edge 1 NOT climbed: <why>              (once per stay at the foot)
 *   Mode=vault:
 *   climb: edge 1 NOT vaulted yet: 1 channel(s) of his play that the vault's own Play would replace and report (the first: channel 2, clip 0a1f3c00 at frame 7.5 of 12): ... - asked again four times a second while he stands here
 *   climb: edge 1: the vault is REFUSED from this stand: 5 tries in 1010 ms of standing, the last: 1 channel(s) ... (asked on while he stands; said no more)
 *   climb: edge 1: the game's own VAULT started from node (...) to (...), slots 311 / 312: action 0b7f2a40 (...)
 *   climb: edge 1: (the vault had been refused 2 time(s) in the 500 ms before: the channels that played then are over)
 *   climb: edge 1: the vault's start LEFT HIS COLLISION SWITCHED OFF (count 1, flag 0; both were 0 and 1 before the call) and no vault action is there to switch it on (his action now 00000000): this file gives it back
 *   climb: edge 1: after a vault start that kept no action - the proxy put at the node: proxy (...) -> (...), node (...); collision on (count 1 -> 0)
 *
 * WIRING (klhook.c; three lines, nothing else of the hook changes; this file uses kljoin.c, klcrew_rt.c, klbot.c and
 * klescort.c, which the place after klhop.c gives)
 *   #include "klclimb.c"        after  #include "klhop.c"
 *   klq_tick(game_thread);      in klh_tick, after  klv_tick(game_thread);
 *   klq_init();                 in the init list, after  klv_init();
 */
#ifndef KLCLIMB_C
#define KLCLIMB_C

#define KLQ_PLAYER_VT   0x00bb45f4            /* ZFFPlayer */
#define KLQ_DISP_VT     0x00ba38d8            /* ZActionDispatcher = [player + 0x19c]; +4 = the current action (0 = none) */
#define KLQ_MINI_VT     0x00bb4f0c            /* ZFFActionMiniAnim */
#define KLQ_VAULT_VT    0x00bb5188            /* ZFFActionVaultOver */
#define KLQ_MINI        0x005ea340            /* ZFFPlayer::StartMiniAnim (player; u16 slot, x, alignObject, char endWithClip) */
#define KLQ_VAULT       0x00619790            /* ZFFPlayer::StartVaultOver (player; cover, char left, pos, rot, char given, char writeBack) */
#define KLQ_CLIP        0x0059d550            /* (player; u16 slot) -> clip record or 0; draws one number from the game's generator */
#define KLQ_ALIGN       0x0080fdc0            /* vtable +0x208: (player; rot[9], pos[3], float frames) -> al */
#define KLQ_COLL_OFF    0x005d6200            /* vtable +0x560 */
#define KLQ_COLL_ON     0x00686600            /* vtable +0x564 */
#define KLQ_SYNC        0x004af5b0            /* (player): the character proxy [player + 0x7d0] is put at the node's world place */
#define KLQ_STOP        0x008aef30            /* vtable +0x374: finish the current action (dispatcher slot 5 -> 6: End, delete) */
#define KLQ_MATRIX      0x0055f8f0            /* ecx = out[9], edx = in[3]: the rotation whose row 0 is the vector; pure */
#define KLQ_ANIMDATA    0x01546f6c            /* the animation manager; [+0x10] = the clips' data block (0x4a75d0) */
#define KLQ_NEDGE       8
#define KLQ_NEAR        15.0f                 /* at the foot = this far .. */
#define KLQ_FAR         70.0f                 /* .. this far from the face: Dead Men's last probe (kl_fa_climb.py has tried 30, 47 and 65) */
#define KLQ_HEIGHT      40.0f                 /* and within this of Floor= */
#define KLQ_OVER        10.0f                 /* the hand-over wants his node this far beyond the face (or the clip's last tick) */
#define KLQ_UNDER       3.0f                  /* 'under the top' = his node more than this under it (in their last frames Medium stands at +0, Low at +2.3 .. 3.3, High at +24.5) */
#define KLQ_LIFT        10.0f                 /* Align=1 aims this far over the top (top comment, section 2; second review N3) */
#define KLQ_RETRY       250u                  /* ms between two tries of a vault that was refused for the channels that play (each try draws from the game's generator: 0x59d550) */
#define KLQ_WHY         320                   /* a reason's buffer */
#define KLQ_BODIES      0x1388u               /* the physics world's body table: 5,000 entries (0x4adce0) */

struct klq_edge { int on, cls; float a[3], b[3], n[2], u[2], len, floor, depth; };
static const struct { const char *slot; float top, stand; } klq_cls[3] = {        /* kaneandlynch.exe 0x603340 */
    { "/Movement/Climb/Up/Low", 120.0f, 81.0f }, { "/Movement/Climb/Up/Medium", 170.0f, 47.0f }, { "/Movement/Climb/Up/High", 220.0f, 47.0f } };
static const char *const klq_vault_slot[2] = { "/Cover/Vaulting/Cover_Vault_Right_1M", "/Cover/Vaulting/Cover_Vault_Right_2M" };

static struct { int on, dry, log, vault, fallback, align, key, low; DWORD dwell; float speed, cosang, hand; } klq;
static SHORT (WINAPI *klq_keystate)(int);     /* user32's GetAsyncKeyState, looked up at init when Key= is set: the hook does not link user32 (klnudge.c) */
static struct { int n; char key[64], file[MAX_PATH]; FILETIME ft; struct klq_edge e[KLQ_NEDGE]; } klq_lv;
static struct {                               /* the watch: where he was, since when he is at the foot of which edge */
    DWORD player, at, game_at, since[KLQ_NEDGE], say_at, vr_since[KLQ_NEDGE], vr_last[KLQ_NEDGE]; float pos[3], speed; int have, vr_n[KLQ_NEDGE];
    char told[KLQ_NEDGE], seen[KLQ_NEDGE];    /* told, bits: 1 = a reason of klq_refuse was said, 2 = tried at this stay (final), 4 = the vault was refused for the channels
                                                 that play (said; asked again since vr_since, vr_n tries, the last at vr_last), 8 = that it stood for a second was said,
                                                 16 = the body has no climb clip here (Fallback=1: the tries go to the vault) */
    int told_gate, told_thread, told_code;
} klq_w;
static struct {                               /* the climb that runs (player != 0) */
    DWORD player, action, chan, clip, began, tick_at, idle, clock0, limit, owe_since;
    int edge, vault, stage, owed, byft, have_clock, told_hand;      /* stage 1 = the second alignment is still to come; 9 = over, the collision is still owed */
    float p2[3], rot[12], f_foot, f_top, to, last_t, step, feet0, top_y;      /* top_y = the height his NODE has when his feet are at the top */
    struct klq_edge e;
} klq_r;
static struct {                               /* after a climb: where he is at +0.5, +1, +2 s (reads only) */
    DWORD player, at; int edge, step, byft; float feet0; struct klq_edge e;
} klq_a;
static BYTE klq_cover[0x60];                  /* the cover record 0x619790 is handed (it reads +0x0c, +0x2c, +0x54 and keeps the pointer) */

static float klq_num(const char *sec, const char *key, const char *def, const char *file)
{
    char t[32];
    GetPrivateProfileStringA(sec, key, def, t, sizeof t, file);
    return (float)atof(t);
}

/* the [Climb] sections of the KLJoin.ini kljoin.c has read for the running level (never a stock archive's) */
static void klq_source(void)
{
    char key[64], file[MAX_PATH], sec[16], t[32]; FILETIME ft; int i, c;
    EnterCriticalSection(&klj_cs);
    snprintf(key, sizeof key, "%s", klj_map_key); snprintf(file, sizeof file, "%s", klj_map_file); ft = klj_map_ft;
    LeaveCriticalSection(&klj_cs);
    if (!strcmp(key, klq_lv.key) && !_stricmp(file, klq_lv.file) && !CompareFileTime(&ft, &klq_lv.ft)) return;
    memset(&klq_lv, 0, sizeof klq_lv);
    strcpy(klq_lv.key, key); strcpy(klq_lv.file, file); klq_lv.ft = ft;
    if (!key[0] || !file[0]) return;
    for (i = 0; i < KLQ_NEDGE; i++) {
        struct klq_edge *e = &klq_lv.e[i]; float nx = 0, nz = 0, h, ln; char nt[64], *p;
        if (i) snprintf(sec, sizeof sec, "Climb.%d", i + 1); else strcpy(sec, "Climb");
        if (!GetPrivateProfileStringA(sec, 0, "", t, sizeof t, file)) continue;                 /* no such section */
        if (!klj_vec(sec, "A", file, e->a) || !klj_vec(sec, "B", file, e->b) || !kle_ok3(e->a) || !kle_ok3(e->b)) { klog("climb: [%s] of %s refused: A= and B= need three numbers each", sec, file); continue; }
        GetPrivateProfileStringA(sec, "Normal", "", nt, sizeof nt, file);
        for (p = nt; *p; p++) if (*p == ',' || *p == ';' || *p == '(' || *p == ')') *p = ' ';
        if (sscanf(nt, "%f %f", &nx, &nz) != 2 || !klb_finite(nx) || !klb_finite(nz) || fabs(nx * nx + nz * nz - 1.0f) > 0.02f) { klog("climb: [%s] of %s refused: Normal= needs two numbers, x z, of a unit vector", sec, file); continue; }
        e->n[0] = nx; e->n[1] = nz;
        e->u[0] = e->b[0] - e->a[0]; e->u[1] = e->b[2] - e->a[2];
        ln = (float)sqrt(e->u[0] * e->u[0] + e->u[1] * e->u[1]);
        if (ln < 60.0f || fabs(e->a[1] - e->b[1]) > 1.0f) { klog("climb: [%s] of %s refused: A - B must be level and 60 long or more", sec, file); continue; }
        e->u[0] /= ln; e->u[1] /= ln; e->len = ln;
        if (fabs(e->u[0] * e->n[0] + e->u[1] * e->n[1]) > 0.02f) { klog("climb: [%s] of %s refused: Normal= is not square to A - B", sec, file); continue; }
        GetPrivateProfileStringA(sec, "Floor", "", t, sizeof t, file);
        e->floor = (float)atof(t);
        if (!t[0] || !klb_finite(e->floor)) { klog("climb: [%s] of %s refused: Floor= is needed", sec, file); continue; }
        e->depth = klq_num(sec, "Depth", "50", file); if (!klb_finite(e->depth) || e->depth < 10.0f) e->depth = 10.0f;
        h = e->a[1] - e->floor;
        for (c = 0; c < 3 && klq_cls[c].top < h; c++) ;
        if (h <= 25.0f || c == 3) { klog("climb: [%s] of %s refused: the edge is %.1f over Floor=; Dead Men climbs over 25 and up to 220", sec, file, h); continue; }
        e->cls = c; e->on = 1; klq_lv.n++;                                                       /* cls: for the line below only; a climb takes its class from his feet */
    }
    if (!klq_lv.n) return;
    klog("climb: %d edge(s) from %s for level %s", klq_lv.n, file, key);
    for (i = 0; i < KLQ_NEDGE; i++) if (klq_lv.e[i].on) {
        const struct klq_edge *e = &klq_lv.e[i];
        klog("climb: edge %d: (%.0f, %.0f, %.0f) - (%.0f, %.0f, %.0f), %.0f long, out of the face (%g, %g); floor %.0f: %.1f up = %s, stand-off %.0f; %.0f thick",
             i + 1, e->a[0], e->a[1], e->a[2], e->b[0], e->b[1], e->b[2], e->len, e->n[0], e->n[1], e->floor, e->a[1] - e->floor, klq_cls[e->cls].slot, klq_cls[e->cls].stand, e->depth);
    }
}

/* A scene node's world place and the world image of its local z axis. That image is where the man's BACK points: a
   clip's root runs along -z (every climb, vault and fall clip of both games), and 0x857110 - what the vault and the
   alignment take a rotation from - gives it as row 0. Composed as klescort.c's kle_node composes the place; it walks
   the chain [node + 0x50] to the root as the game's 0x7b3020 does (which 0x4af5b0 calls with no test). */
static int klq_node(DWORD node, float pos[3], float back[3])
{
    float v[3] = { 0, 0, 0 }, d[3] = { 0, 0, 1 }, m[12], t[3]; int depth;
    if (!node) return 0;
    for (depth = 0; node && depth < 32; depth++) {
        if (!klh_rd(node, m, sizeof m)) return 0;
        t[0] = v[0] * m[6] + v[1] * m[3] + v[2] * m[0] + m[9];
        t[1] = v[0] * m[7] + v[1] * m[4] + v[2] * m[1] + m[10];
        t[2] = v[0] * m[8] + v[1] * m[5] + v[2] * m[2] + m[11];
        memcpy(v, t, sizeof v);
        t[0] = d[0] * m[6] + d[1] * m[3] + d[2] * m[0];
        t[1] = d[0] * m[7] + d[1] * m[4] + d[2] * m[1];
        t[2] = d[0] * m[8] + d[1] * m[5] + d[2] * m[2];
        memcpy(d, t, sizeof d);
        node = klh_rd32(node + 0x50);
    }
    if (node || !kle_ok3(v) || !kle_ok3(d)) return 0;
    memcpy(pos, v, sizeof v); memcpy(back, d, sizeof d);
    return 1;
}

/* Where the character proxy is, in the level's units: [[[player + 0x7d0] + 0x30] + 0x18] + 0x30, four floats in
   Havok's units (0xa768a0), times 100 (0x408060). Reads only. -> 0 = he has none or it cannot be read */
static int klq_proxy(DWORD pl, float out[3])
{
    DWORD p = klh_rd32(pl + 0x7d0), ph, m; float v[3];
    out[0] = out[1] = out[2] = 0;
    if (!p || !(ph = klh_rd32(p + 0x30)) || !(m = klh_rd32(ph + 0x18)) || !klh_rd(m + 0x30, v, 12) || !kle_ok3(v)) return 0;
    out[0] = v[0] * 100.0f; out[1] = v[1] * 100.0f; out[2] = v[2] * 100.0f;
    return 1;
}

/* The game's clock, 1024 a second: it stands still in a pause and the animation channels advance by its steps
   (0x70da30, 0x50ac80; top comment). Reads only. */
static int klq_clock(DWORD *t)
{
    DWORD sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF));
    return sys && klh_rd(sys + 0x48, t, 4);
}

/* The id of a slot name in the level's slot table, read as the game's own search reads it (0x68a730 from 0x426890:
   [player + 0x80] -> {n, n x {text offset, id} sorted by name, the texts}); -1 = the level has no such name. */
static int klq_slot(DWORD pl, const char *name)
{
    DWORD t = klh_rd32(pl + 0x80), n = 0, lo = 0, hi, ent[2]; char s[200]; int c;
    if (!t || !klh_rd(t, &n, 4) || !n || n > 60000) return -1;
    for (hi = n; lo < hi; ) {
        DWORD mid = (lo + hi) / 2;
        if (!klh_rd(t + 4 + 8 * mid, ent, 8) || !klh_rdstr(t + 4 + 8 * n + ent[0], s, sizeof s)) return -1;
        if (!(c = strcmp(name, s))) return (int)(ent[1] & 0xffff);
        if (c > 0) lo = mid + 1; else hi = mid;
    }
    return -1;
}

/* A clip record of the game (0x68 bytes): its frames, the frames of its events 5 and 6 (-1 = none), its record flags,
   the forward part of its net root movement (+0x18; forward is -z). Reads only (the game's own lookup is 0x4a75d0). */
static int klq_clip(DWORD clip, float *frames, float *f5, float *f6, DWORD *flags, float *fwd)
{
    BYTE r[0x30], ev[8]; DWORD mgr, base; short n, i; float net[3];
    *f5 = *f6 = -1.0f; *frames = 0; *flags = 0; *fwd = 0;
    if (!clip || !klh_rd(clip, r, sizeof r)) return 0;
    *frames = (float)*(short *)(r + 2); *flags = *(DWORD *)(r + 8); n = *(short *)(r + 6);
    memcpy(net, r + 0x18, 12); if (klb_finite(net[2])) *fwd = -net[2];
    if (*frames < 2.0f || *frames > 2000.0f) return 0;
    if (n > 0 && n < 64 && (mgr = klh_rd32((DWORD_PTR)KLH_VA(KLQ_ANIMDATA))) != 0 && (base = klh_rd32(mgr + 0x10)) != 0)
        for (i = 0; i < n; i++) {
            if (!klh_rd(base + *(DWORD *)(r + 0x10) + 8 * i, ev, 8)) break;
            if (*(DWORD *)ev == 5 && *f5 < 0) *f5 = (float)*(WORD *)(ev + 4);
            if (*(DWORD *)ev == 6 && *f6 < 0) *f6 = (float)*(WORD *)(ev + 4);
        }
    return 1;
}

/* The channel AlignTo would take: the game's 0x760120 done by reads - the first of the player's 16 channels that
   plays (state 1 or 3), is a full-body one (flag 0x8000) and whose clip has record flag 0x40. -> its address, 0 = none */
static DWORD klq_root_chan(DWORD pl)
{
    DWORD an = klh_rd32(pl + 0x70), fl = 0, clip; BYTE b = 0; int i;
    if (!an) return 0;
    for (i = 0; i < 16; i++) {
        if (!klh_rd(an + 0x30 + 0x38 * i, &fl, 4)) return 0;
        if (((fl & 7) == 1 || (fl & 7) == 3) && (fl & 0x8000) && (clip = klh_rd32(an + 0x1c + 0x38 * i)) != 0 && klh_rd(clip + 8, &b, 1) && (b & 0x40)) return an + 0x1c + 0x38 * i;
    }
    return 0;
}

/* how many full-body channels of his play now (state 1 or 3, flag 0x8000): for the line at the foot. -1 = not readable */
static int klq_playing(DWORD pl)
{
    DWORD an = klh_rd32(pl + 0x70), fl = 0; int i, n = 0;
    if (!an) return -1;
    for (i = 0; i < 16; i++) {
        if (!klh_rd(an + 0x30 + 0x38 * i, &fl, 4)) return -1;
        if (((fl & 7) == 1 || (fl & 7) == 3) && (fl & 0x8000)) n++;
    }
    return n;
}

/* How many of his channels Play(clip, 1) would stop AND REPORT to the current action before it returns (0x4da294 ..
   0x4da306, 0x4da711 .. 0x4da751): those that play (state 1 or 3) and are of the clip's body class (flag 0x8000 <->
   record +0x28 bit 0x10 clear). The vault ends and frees itself at the first such report. -> the count, -1 = not
   readable; *first = the number of the first such channel (-1 = none) */
static int klq_replaced(DWORD pl, DWORD clip, int *first)
{
    DWORD an = klh_rd32(pl + 0x70), fl = 0, c28 = 0; int i, n = 0, body;
    *first = -1;
    if (!an || !klh_rd(clip + 0x28, &c28, 4)) return -1;
    body = !((c28 >> 4) & 1);
    for (i = 0; i < 16; i++) {
        if (!klh_rd(an + 0x30 + 0x38 * i, &fl, 4)) return -1;
        if (((fl & 7) == 1 || (fl & 7) == 3) && (int)((fl >> 15) & 1) == body) { if (!n) *first = i; n++; }
    }
    return n;
}

/* Are the game's routines the ones this build knows? Their first bytes, and the vtable entries they are called by. */
static int klq_code(void)
{
    static const BYTE mini[14]  = { 0x6a, 0xff, 0x68, 0x5b, 0x77, 0xad, 0x00, 0x64, 0xa1, 0x00, 0x00, 0x00, 0x00, 0x50 };      /* 0x5ea340 */
    static const BYTE vault[14] = { 0x83, 0xec, 0x7c, 0x53, 0x56, 0x57, 0x8b, 0xf1, 0x8d, 0x44, 0x24, 0x28, 0x50, 0x8d };      /* 0x619790 */
    static const BYTE clip[14]  = { 0x83, 0xec, 0x0c, 0xa1, 0x40, 0x26, 0xdd, 0x00, 0x8b, 0x90, 0x30, 0x0b, 0x00, 0x00 };      /* 0x59d550 */
    static const BYTE align[14] = { 0x81, 0xec, 0xb4, 0x00, 0x00, 0x00, 0x56, 0x57, 0x8b, 0xf1, 0xe8, 0x51, 0x03, 0xf5 };      /* 0x80fdc0 */
    static const BYTE off[14]   = { 0x56, 0x8b, 0xf1, 0xe8, 0x68, 0xf0, 0x2e, 0x00, 0x8b, 0x96, 0xcc, 0x27, 0x00, 0x00 };      /* 0x5d6200 */
    static const BYTE on[14]    = { 0x56, 0x8b, 0xf1, 0xe8, 0xb8, 0xdb, 0x22, 0x00, 0xa1, 0x40, 0x26, 0xdd, 0x00, 0x8b };      /* 0x686600 */
    static const BYTE sync[14]  = { 0x55, 0x8b, 0xec, 0x83, 0xe4, 0xf0, 0x83, 0xec, 0x1c, 0x56, 0x8b, 0xf1, 0x83, 0xbe };      /* 0x4af5b0 */
    static const BYTE mat[14]   = { 0x83, 0xec, 0x14, 0xd9, 0x42, 0x04, 0x56, 0xd9, 0x5c, 0x24, 0x04, 0x8b, 0xf1, 0xd9 };      /* 0x55f8f0 */
    DWORD_PTR vt = (DWORD_PTR)KLH_VA(KLQ_PLAYER_VT);
    return klt_same_code(KLQ_MINI, mini, sizeof mini) && klt_same_code(KLQ_VAULT, vault, sizeof vault) && klt_same_code(KLQ_CLIP, clip, sizeof clip) &&
           klt_same_code(KLQ_ALIGN, align, sizeof align) && klt_same_code(KLQ_COLL_OFF, off, sizeof off) && klt_same_code(KLQ_COLL_ON, on, sizeof on) &&
           klt_same_code(KLQ_SYNC, sync, sizeof sync) && klt_same_code(KLQ_MATRIX, mat, sizeof mat) &&
           klh_rd32(vt + 0x208) == KLQ_ALIGN && klh_rd32(vt + 0x560) == KLQ_COLL_OFF && klh_rd32(vt + 0x564) == KLQ_COLL_ON && klh_rd32(vt + 0x374) == KLQ_STOP;
}

/* Is pl still one of the game's players? (An object a level has thrown away may keep its bytes for a while.) */
static int klq_registered(DWORD pl)
{
    DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA)), tab[28]; int i;
    if (!gd || !klh_rd(gd + 0x828, tab, sizeof tab)) return 0;
    for (i = 0; i < 28; i++) if (tab[i] == pl) return 1;
    return 0;
}

/* What 0x4af5b0 and 0x5d6200 / 0x686600 go through without a test of their own -> 0 = they may be called, else why
   not. Reads only. Asked before the start AND before every later call (review S1): a death, a round's end or a level
   being taken down can lie between two ticks. */
static const char *klq_carry_refuse(DWORD pl)
{
    DWORD node, p, ph, w, sh, sys, a, wd, idx = 0, cnt = 0, e, body; BYTE filt = 0; float nd[3], bk[3], tol[2];
    if (klh_rd32(pl) != KLQ_PLAYER_VT || !klq_registered(pl)) return "the object is not one of the game's players any more";
    /* 0x4af5b0: the node chain to the root (0x7b3020); if [player+0x7d0]: its two floats at +0x58 are read (0xa768b0), its +0x30
       = the proxy's phantom, whose place at +0xa0 is written, whose world [+8] is asked for [+0x6c] and whose shape [+0x10]
       is called through vtable +0x18 (0x9fc110) */
    if (!(node = klh_rd32(pl + 4)) || !klq_node(node, nd, bk)) return "his node's place cannot be read (the chain 0x4af5b0 walks)";
    if ((p = klh_rd32(pl + 0x7d0)) != 0) {
        if (!klh_rd(p + 0x58, tol, 8) || !(ph = klh_rd32(p + 0x30)) || !klt_writable(ph + 0xa0, 16)) return "his character proxy [player+0x7d0] has no phantom that can be written (0x9fc110)";
        if ((w = klh_rd32(ph + 8)) != 0 && (!klh_rd32(w + 0x6c) || !(sh = klh_rd32(ph + 0x10)) || !klt_code(klh_rd32(klh_rd32(sh) + 0x18)))) return "his proxy's phantom has no world data or no shape (0x9fc110)";
    }
    /* 0x5d6200 / 0x686600: [[sys+0xac]+0x52cc] = the physics world, its body table by [player+0x27cc], the body's filter
       word at +0x2c is written; 0x40ed30 then asks the world's byte +0x14fc and, if set, uses [world+0x14dc] */
    if (!(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) || !(a = klh_rd32(sys + 0xac)) || !(wd = klh_rd32(a + 0x52cc))) return "there is no physics world ([[sysif+0xac]+0x52cc])";
    if (!klh_rd(pl + 0x27cc, &idx, 4) || !klh_rd(wd + 0x1183c, &cnt, 4) || cnt > KLQ_BODIES || idx >= cnt) return "his body's number [player+0x27cc] is not in the physics world's table";
    if (!(e = klh_rd32(wd + 4 * idx + 0x11840)) || !(body = klh_rd32(e)) || !klt_writable(body + 0x2c, 4)) return "his body in the physics world cannot be read ([[world+0x11840+4*[player+0x27cc]]])";
    if (!klh_rd(wd + 0x14fc, &filt, 1) || (filt && !klh_rd32(wd + 0x14dc))) return "the physics world's Havok world [world+0x14dc] is missing";
    return 0;
}

/* What the START takes for granted of the player it is handed -> 0 = he may be started, else why not. Reads only. */
static const char *klq_refuse(DWORD pl, DWORD *disp_)
{
    DWORD node, fl = 0, disp, act = 1, mv, kind = 0, f438 = 0, f818 = 0x80, down, st = 1, d44 = 1, cnt = 1, p, q, r, par, own, onode, ofl = 0x800, d50 = 1;
    BYTE on = 0, cov = 1, anim = 1, live = 0;
    if (klh_rd32(pl) != KLQ_PLAYER_VT) return "the local player is not a ZFFPlayer";
    if (!(node = klh_rd32(pl + 4)) || !klh_rd(node + 0x3c, &fl, 4) || (fl >> 10 & 1)) return "his node is off (flag bit 10)";
    if (!klh_rd(pl + 0x7a4, &anim, 1) || anim || !klh_rd(pl + 0x430, &live, 1) || !live) return "his frame is not the ordinary one ([player+0x7a4] is set or [player+0x430] is clear: 0x74efc0 then makes no Move)";
    /* the frame's two other gates (second review N1). 0x74efe6: bit 0x800 of the flags of the node [[[node+0x50]+0x60]+4] (0x598460: the owner of what his node
       hangs on) - the whole frame is skipped; 0x74f2c5: [player+0xd50] not 0 - the node is not written from the move. Behind either the clip would play and he
       would not move. The game reads through the first chain with no test, so for a player whose frames run it reads. */
    if (!(par = klh_rd32(node + 0x50)) || !(own = klh_rd32(par + 0x60)) || !(onode = klh_rd32(own + 4)) || !klh_rd(onode + 0x3c, &ofl, 4) || (ofl & 0x800))
        return "the node [[[node+0x50]+0x60]+4] (the owner of what his node hangs on) cannot be read or has flag bit 0x800: 0x74efc0 then skips his whole frame (0x74efe6)";
    if (!klh_rd(pl + 0xd50, &d50, 4) || d50) return "[player+0xd50] is not 0: 0x74efc0 then does not write his node from the move (0x5380d0 at 0x74f2c5)";
    if (!klh_rd(pl + 0xd44, &d44, 4) || d44) return "he is attached to something ([player+0xd44]: a vehicle, a seat)";
    if (!klh_rd(pl + 0x438, &f438, 4) || (f438 & 0x40000)) return "he is dead (bit 0x40000 of [player+0x438])";
    if (!(down = klh_rd32(pl + 0x2940)) || !klh_rd(down + 0x24, &st, 4)) return "[player+0x2940], his down state, cannot be read";
    if (st) return "his down state is not 0 ([[player+0x2940]+0x24]: the game's own caller of the mini animation, 0x5022c0, asks for 0)";
    if (!klh_rd(pl + 0x2954, &cov, 1) || cov || !klh_rd(pl + 0x818, &f818, 4) || (f818 & 0x80)) return "he is in cover ([player+0x2954] or bit 0x80 of [player+0x818], what the game's 0x40f840 tests): the mini animation does not leave cover";
    if (!(mv = klh_rd32(pl + 0x6b4)) || !klh_rd(mv + 0x44, &kind, 4) || (kind != 2 && kind != 3)) return "he neither stands nor walks (movement kind is not 2 / 3: a fall, a roll ...)";
    if (!(disp = klh_rd32(pl + 0x19c)) || klh_rd32(disp) != KLQ_DISP_VT || !klh_rd(disp + 4, &act, 4)) return "[player+0x19c] is not his action dispatcher";
    if (act) return "an action of his runs (a reload, a pick-up, a vault ...)";
    if (!klh_rd(pl + 0x7b4, &cnt, 4) || cnt || !klh_rd(pl + 0x7a5, &on, 1) || !on) return "his collision is switched off already ([player+0x7b4] is not 0 or [player+0x7a5] is 0)";
    /* what 0x5ea340 writes through without a test: [player+0xbe0] (+0x10, +0x18), its +0xc (+0xce4), [player+0xdbc] (+0x1ead .. +0x1eb1) */
    if (!(p = klh_rd32(pl + 0xbe0)) || !klt_writable(p, 0x1c) || !(q = klh_rd32(p + 0xc)) || !klt_writable(q + 0xce4, 1)) return "[player+0xbe0], which the game's routine writes through (0x8b7410), is null or not writable";
    if (!(r = klh_rd32(pl + 0xdbc)) || !klt_writable(r + 0x1ead, 5)) return "[player+0xdbc], which the game's routine writes through (0x4c1a70), is null or not writable";
    *disp_ = disp;
    return klq_carry_refuse(pl);
}

/* What the VAULT's start goes through besides (0x619790, leave-cover 0x5fcb80, 0x6a27e0) -> 0, else why not. Reads only. */
static const char *klq_vault_refuse(DWORD pl)
{
    DWORD p, sys, a, wd, x = 0; LONG slot = 0;
    if (!(p = klh_rd32(pl + 0x2810)) || !klt_writable(p + 0x1c, 4)) return "[player+0x2810], which leave-cover writes through (0x95e340), is null or not writable";
    if (!(p = klh_rd32(pl + 0x2948)) || !klt_writable(p + 8, 0x24)) return "[player+0x2948], which leave-cover writes through (0x84dda0), is null or not writable";
    if (!(p = klh_rd32(pl + 0xccc)) || !klt_writable(p + 0x24c, 4)) return "[player+0xccc], which leave-cover writes through (0x5ed5c0), is null or not writable";
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLB_SESSION))) || !klh_rd(p + 0x54, &x, 4)) return "the session object [0x168e598] cannot be read";
    if (!klh_rd(pl + 0x2f70, &slot, 4) || slot != -1) return "he holds a cover slot ([player+0x2f70] is not -1: leave-cover would give it back through the game's tables, 0x784460)";
    if (!(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) || !(a = klh_rd32(sys + 0xac)) || !(wd = klh_rd32(a + 0x52cc)) || !klh_rd32(wd + 0x14ec)) return "the physics world has no phantom maker ([world+0x14ec], 0x6a292e)";
    return 0;
}

static void klq_collision(DWORD pl, int on, const char *why)
{
    DWORD before = klh_rd32(pl + 0x7b4), after;
    ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(on ? KLQ_COLL_ON : KLQ_COLL_OFF))((void *)(DWORD_PTR)pl, 0);
    after = klh_rd32(pl + 0x7b4);
    if (klq.log) klog("climb: collision %s (%s; count %lu -> %lu)%s", on ? "on" : "off", why, before, after, on && after ? " - somebody else holds it off as well" : "");
}

/* how far his node is from the face of an edge (minus = beyond it) */
static float klq_off(const struct klq_edge *e, const float nd[3])
{
    return (nd[0] - e->a[0]) * e->n[0] + (nd[2] - e->a[2]) * e->n[1];
}

/* The end of the carrying, in the game's own order (the vault's End 0x82f796 / 0x82f7a6, ZFFActionJumpOver's 0x5c8fa3,
   the mini cutscene act's 0x447bf2): the character proxy is put at the node, THEN the collision is switched on.
   NEVER INTO THE OBSTACLE (second review N4): when his node is between the faces of edge e's obstacle (less than
   KLQ_NEAR clear of either) and more than KLQ_UNDER under its top - top_y = the height his NODE has with his feet at
   the top - the proxy is left where it is and only the collision is switched on: by the reading of the top comment's
   section 1 the game's next frame steps him from where the proxy stayed (the collision on without the sync is what
   the first version of this file did at every end, and what the game's fall does first, 0x4815e5).
   -> 1 done, 0 = klq_carry_refuse said no (*why; nothing was called). */
static int klq_give_back(DWORD pl, int ei, const struct klq_edge *e, float top_y, const char *what, const char **why)
{
    float p0[3], p1[3], nd[3] = { 0, 0, 0 }, bk[3], d = 0, up = 0; DWORD before, after; int h0, h1, inside = 0;
    if ((*why = klq_carry_refuse(pl)) != 0) return 0;
    h0 = klq_proxy(pl, p0);
    if (klq_node(klh_rd32(pl + 4), nd, bk)) { d = klq_off(e, nd); up = nd[1] - top_y; inside = d < KLQ_NEAR && d > -(e->depth + KLQ_NEAR) && up < -KLQ_UNDER; }
    if (!inside) ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLQ_SYNC))((void *)(DWORD_PTR)pl, 0);
    h1 = klq_proxy(pl, p1);
    before = klh_rd32(pl + 0x7b4);
    ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLQ_COLL_ON))((void *)(DWORD_PTR)pl, 0);
    after = klh_rd32(pl + 0x7b4);
    if (inside)
        klog("climb: edge %d: %s - the proxy is NOT put at the node: node (%.0f, %.0f, %.0f) is %.0f %s the face of a %.0f thick obstacle and %.0f under its top = INSIDE it; the proxy stays at (%.0f, %.0f, %.0f)%s and the game's next frame steps him from there; collision on (count %lu -> %lu)%s",
             ei + 1, what, nd[0], nd[1], nd[2], fabs(d), d < 0 ? "beyond" : "before", e->depth, -up, p1[0], p1[1], p1[2], h1 ? "" : " (not read: he has none?)", before, after,
             after ? " - somebody else holds it off as well" : "");
    else
        klog("climb: edge %d: %s - the proxy put at the node: proxy (%.0f, %.0f, %.0f) -> (%.0f, %.0f, %.0f)%s, node (%.0f, %.0f, %.0f); collision on (count %lu -> %lu)%s",
             ei + 1, what, p0[0], p0[1], p0[2], p1[0], p1[1], p1[2], h0 && h1 ? "" : " (the proxy could not be read: he has none?)", nd[0], nd[1], nd[2], before, after,
             after ? " - somebody else holds it off as well" : "");
    return 1;
}

static char klq_align(DWORD pl, const float rot[9], const float pos[3], float frames)
{
    float p[4];
    p[0] = pos[0]; p[1] = pos[1]; p[2] = pos[2]; p[3] = 0;
    return ((char (__fastcall *)(void *, void *, const float *, const float *, float))(DWORD_PTR)KLH_VA(KLQ_ALIGN))((void *)(DWORD_PTR)pl, 0, rot, p, frames);
}

/* After a climb or a vault: where he is 0.5, 1 and 2 s later, and what that means (review, live check K2: the 'over'
   line is printed before the game's next movement step and cannot tell a climb that held from one that did not). Reads only. */
static void klq_after(DWORD now)
{
    static const DWORD due[3] = { 500, 1000, 2000 };
    DWORD pl = klq_a.player; float nd[3], bk[3], ft[3] = { 0, 0, 0 }, pr[3], d, up, y; const struct klq_edge *e = &klq_a.e; int hp;
    if (now - klq_a.at < due[klq_a.step]) return;
    if (klh_rd32(pl) != KLQ_PLAYER_VT || !klq_registered(pl) || !klq_node(klh_rd32(pl + 4), nd, bk)) {
        klog("climb: edge %d: no RESULT: the player object %08lx is gone or his node cannot be read %lu ms after the end", klq_a.edge + 1, pl, now - klq_a.at);
        memset(&klq_a, 0, sizeof klq_a); return;
    }
    klh_rd(pl + 0x460, ft, 12); hp = klq_proxy(pl, pr);
    d = klq_off(e, nd); y = klq_a.byft ? ft[1] : nd[1]; up = y - e->a[1];
    if (klq_a.step < 2) {
        klog("climb: edge %d: +%lu ms: node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f), proxy (%.0f, %.0f, %.0f)%s: %.0f %s the face, %+.0f to the top",
             klq_a.edge + 1, due[klq_a.step], nd[0], nd[1], nd[2], ft[0], ft[1], ft[2], pr[0], pr[1], pr[2], hp ? "" : " (not read)", fabs(d), d < 0 ? "beyond" : "on the near side of", up);
        klq_a.step++; return;
    }
    if (klq_a.byft)                                                          /* his node was not at his feet when it began: +0x460 has the navigation mesh's heights (klauto.c), no height is judged */
        klog("climb: edge %d: RESULT 2 s after the end: %s - %.0f %s the face (no height is judged: his node is not at his feet and +0x460 reads %+.0f to the top); node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f)",
             klq_a.edge + 1, d < -5.0f ? "BEYOND THE FACE (up or across)" : d > 5.0f ? "ON THE NEAR SIDE (back, if that is where he began)" : "AT THE FACE", fabs(d), d < 0 ? "beyond" : "on the near side of", up, nd[0], nd[1], nd[2], ft[0], ft[1], ft[2]);
    else if (d <= 5.0f && d >= -(e->depth + 10.0f) && up >= -30.0f)
        klog("climb: edge %d: RESULT 2 s after the end: UP - he stands on the obstacle, %.0f beyond the face, %+.0f to its top; node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f)", klq_a.edge + 1, -d, up, nd[0], nd[1], nd[2], ft[0], ft[1], ft[2]);
    else if (d < -e->depth)
        klog("climb: edge %d: RESULT 2 s after the end: ACROSS - %.0f beyond the face (the obstacle is %.0f thick), %+.0f to the top (he went on over it%s); node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f)", klq_a.edge + 1, -d, e->depth, up,
             up < -30.0f ? " and dropped on the far side" : "", nd[0], nd[1], nd[2], ft[0], ft[1], ft[2]);
    else if (d < -5.0f)
        klog("climb: edge %d: RESULT 2 s after the end: INSIDE THE OBSTACLE - %.0f beyond the face of a %.0f thick obstacle and %+.0f to its top: between its faces, under its top; node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f)",
             klq_a.edge + 1, -d, e->depth, up, nd[0], nd[1], nd[2], ft[0], ft[1], ft[2]);
    else if (up < -30.0f)
        klog("climb: edge %d: RESULT 2 s after the end: BACK AT THE FOOT - %.0f on the near side of the face, %+.0f to the top, %+.0f to where his feet were: the climb did not hold; node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f)",
             klq_a.edge + 1, d, up, y - klq_a.feet0, nd[0], nd[1], nd[2], ft[0], ft[1], ft[2]);
    else
        klog("climb: edge %d: RESULT 2 s after the end: ELSEWHERE - %.0f on the near side of the face at %+.0f to the top; node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f)", klq_a.edge + 1, d, up, nd[0], nd[1], nd[2], ft[0], ft[1], ft[2]);
    memset(&klq_a, 0, sizeof klq_a);
}

/* the climb or the vault is over: the last line, the watch for the RESULT, and it is forgotten */
static void klq_done(DWORD now, const char *end, DWORD act, int ours)
{
    DWORD pl = klq_r.player, c = 0; float nd[3] = { 0, 0, 0 }, bk[3], ft[3] = { 0, 0, 0 }, pr[3]; int hp; char fr[64], tm[80];
    klq_node(klh_rd32(pl + 4), nd, bk); klh_rd(pl + 0x460, ft, 12); hp = klq_proxy(pl, pr);
    if (klq_r.vault) strcpy(fr, "the vault"); else snprintf(fr, sizeof fr, "last seen at frame %.1f of %.0f", klq_r.last_t, klq_r.to);
    if (klq_r.have_clock && klq_clock(&c)) snprintf(tm, sizeof tm, "%lu ms of game time (%lu ms by the clock)", (DWORD)((double)(c - klq_r.clock0) * 1000.0 / 1024.0), now - klq_r.began);
    else snprintf(tm, sizeof tm, "%lu ms by the clock (the game's clock was not read)", now - klq_r.began);
    klog("climb: edge %d: %s after %s, %s: node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f), proxy (%.0f, %.0f, %.0f)%s; his action now %08lx, his collision count %lu",
         klq_r.edge + 1, end, tm, fr, nd[0], nd[1], nd[2], ft[0], ft[1], ft[2], pr[0], pr[1], pr[2], hp ? "" : " (not read)", ours ? 0 : act, klh_rd32(pl + 0x7b4));
    memset(&klq_a, 0, sizeof klq_a);
    klq_a.player = pl; klq_a.at = KLB_T(now); klq_a.edge = klq_r.edge; klq_a.byft = klq_r.byft; klq_a.feet0 = klq_r.feet0; klq_a.e = klq_r.e;
    memset(&klq_r, 0, sizeof klq_r);
}

/* A climb or a vault runs: watched every frame of the game's thread, before any gate, until the action is gone. */
static void klq_follow(DWORD now)
{
    DWORD pl = klq_r.player, disp, act = 0, c = 0, gone; float t = -1.0f, margin, last; const char *end = 0, *no = 0, *off = 0; int ours, have_t = 0;
    if (klh_rd32(pl) != KLQ_PLAYER_VT || !klq_registered(pl)) {
        klog("climb: the player object %08lx is gone%s: forgotten, nothing is called", pl, klq_r.owed ? " while its collision was switched off by this file (the object went with its level)" : "");
        memset(&klq_r, 0, sizeof klq_r); return;
    }
    if (now - klq_r.tick_at > 250) klq_r.idle += now - klq_r.tick_at - 50;      /* no tick of the game's thread for a while: not the climb's time (used only when the game's clock cannot be read) */
    klq_r.tick_at = now;
    disp = klh_rd32(pl + 0x19c);
    if (disp && klh_rd32(disp) == KLQ_DISP_VT) klh_rd(disp + 4, &act, 4);
    if (klq_r.stage == 9) {                                                  /* the action is gone; the proxy and the collision could not be given back yet */
        if (klq_give_back(pl, klq_r.edge, &klq_r.e, klq_r.top_y, "the hand-over that was owed", &no)) { klq_r.owed = 0; klq_done(now, "over", act, 0); }
        else if (now - klq_r.owe_since > 3000) {
            klog("climb: edge %d: GIVEN UP after 3 s: the proxy and the collision of player %08lx were NOT given back (%s); his collision count is %lu", klq_r.edge + 1, pl, no, klh_rd32(pl + 0x7b4));
            klq_r.owed = 0; klq_done(now, "over, the collision NOT given back", act, 0);
        }
        return;
    }
    ours = act && act == klq_r.action && klh_rd32(act) == (DWORD)(klq_r.vault ? KLQ_VAULT_VT : KLQ_MINI_VT) && klh_rd32(act + 8) == pl &&
           (klq_r.vault || klh_rd32(act + 0x20) == klq_r.chan);
    if (ours && !klq_r.vault && klh_rd32(klq_r.chan) == klq_r.clip && klh_rd(klq_r.chan + 4, &t, 4) && klb_finite(t)) {
        have_t = 1;
        if (t > klq_r.last_t) klq_r.step = t - klq_r.last_t;                 /* frames one tick is worth now */
        klq_r.last_t = t;
    }
    if (have_t && klq_r.stage == 1 && t >= klq_r.f_foot) {                   /* the frame of event 5 has come */
        char ok = 0;
        klq_r.stage = 2;
        if (t < klq_r.f_top - 0.5f) {
            ok = klq_root_chan(pl) == klq_r.chan ? klq_align(pl, klq_r.rot, klq_r.p2, klq_r.f_top - t) : 0;
            klog("climb: edge %d: frame %.1f: %s to P2 (%.0f, %.0f, %.0f) in %.1f frames", klq_r.edge + 1, t, ok ? "aligned" : "NOT aligned (the channel the game would align is not the climb's any more)",
                 klq_r.p2[0], klq_r.p2[1], klq_r.p2[2], klq_r.f_top - t);
        } else klog("climb: edge %d: frame %.1f: the frame of event 6 (%.0f) came before the second alignment could be set (one step of %.1f frames)", klq_r.edge + 1, t, klq_r.f_top, klq_r.step);
        /* without the alignment to the top the clip rises by its own height only and would end inside the obstacle: it is called off (stopped below, and given
           back by klq_give_back's rule: the proxy goes to the node only when that is not inside the obstacle) */
        if (!ok) off = "CALLED OFF by this file (the alignment to the top was not set)";
    }
    /* THE HAND-OVER: before the clip's last frame, because the game steps the ordinary movement from the proxy in the frame
       the clip ends (top comment, 'who moves him'). From HandFrames before the end on it is made as soon as his node is
       KLQ_OVER beyond the face (the root still walks forward in the last frames: High is 10 beyond it from frame 45.1 of 51,
       Medium from 34.6 of 36, Low never - it is still 5 before it at 25 of 26: measured, re\climb.md 2.3); and in any case in
       the last tick before the end: one and a half ticks' worth, at least one frame. */
    last = klq_r.step * 1.5f; if (last < 1.0f) last = 1.0f; if (last > 5.0f) last = 5.0f;
    margin = klq.hand; if (margin < last) margin = last;
    if (klq_r.f_top > 0.0f && margin > klq_r.to - klq_r.f_top - 1.0f) margin = klq_r.to - klq_r.f_top - 1.0f;      /* never before the top alignment has come */
    if (margin < 0.5f) margin = 0.5f;
    if (last > margin) last = margin;
    if (!off && have_t && klq_r.owed && klq_r.stage == 2 && t >= klq_r.to - margin) {
        float nd[3], bk[3]; int over = klq_node(klh_rd32(pl + 4), nd, bk) && klq_off(&klq_r.e, nd) <= -KLQ_OVER;
        if (over || t >= klq_r.to - last) {
            char what[96];
            snprintf(what, sizeof what, "frame %.1f of %.0f: HAND-OVER%s", t, klq_r.to, over ? "" : " (the last tick before the clip's end; his node is not over the obstacle yet)");
            if (klq_give_back(pl, klq_r.edge, &klq_r.e, klq_r.top_y, what, &no)) klq_r.owed = 0;
            else if (!klq_r.told_hand++) klog("climb: edge %d: frame %.1f of %.0f: the hand-over is NOT made: %s - nothing is called; asked again every frame", klq_r.edge + 1, t, klq_r.to, no);
        }
    }
    if (!ours) end = "over";
    else {
        DWORD spent = klq_r.have_clock && klq_clock(&c) ? (DWORD)((double)(c - klq_r.clock0) * 1000.0 / 1024.0) : now - klq_r.began - klq_r.idle;
        /* the action did not end with its clip, by the game's own clock (a pause holds that clock and the clip alike) */
        if (!off && spent > klq_r.limit && spent < 0x7fffffff) off = "STOPPED by this file (the action outlived its clip by 1.5 s of game time)";
        if (off) {                                                            /* stopped as the game stops any action: its End runs (the mini animation's stops the channel) */
            ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLQ_STOP))((void *)(DWORD_PTR)pl, 0);
            end = off;
        }
    }
    if (!end) return;
    gone = act;
    if (klq_r.owed) {
        /* it ended before the hand-over: another action, a death, a channel of his that ended, one frame longer than the margin. A frame of
           the game has run since (unless this file stopped it just now): the ordinary movement has him where the proxy stayed. */
        if (!ours) klog("climb: edge %d: ended at frame %.1f of %.0f BEFORE the hand-over (his action now %08lx, his down state %lu, dead bit %lu): the game has him where the proxy stayed",
                        klq_r.edge + 1, klq_r.last_t, klq_r.to, act, klh_rd32(klh_rd32(pl + 0x2940) + 0x24), (klh_rd32(pl + 0x438) >> 18) & 1);
        if (!klq_give_back(pl, klq_r.edge, &klq_r.e, klq_r.top_y, ours ? "stopped" : "after its end", &no)) {
            klog("climb: edge %d: the proxy and the collision are NOT given back yet: %s - nothing is called; asked again every frame for 3 s", klq_r.edge + 1, no);
            klq_r.stage = 9; klq_r.owe_since = now; return;
        }
        klq_r.owed = 0;
    }
    klq_done(now, end, gone, ours);
}

/* The vault: one call of the game's own start with a cover record of this file's and the end place given. -> 1 started;
   0 not: why[KLQ_WHY]; *again = it was refused for the channels that play at this moment: the caller asks again */
static int klq_vault(DWORD pl, DWORD disp, int ei, const float nd[3], const float ft[3], const float foot[3], float feet, float rise, int *again, char *why)
{
    const struct klq_edge *e = &klq_lv.e[ei]; const char *no; float n3[4] = { 0, 0, 0, 0 }, rot[12], pos[4]; DWORD act = 0, clip[2], c = 0, cnt = 0, now; int k, s[2], rep, first; BYTE on = 1;
    *again = 0;
    if ((no = klq_vault_refuse(pl)) != 0) { snprintf(why, KLQ_WHY, "%s", no); return 0; }
    for (k = 0; k < 2; k++) {
        if ((s[k] = klq_slot(pl, klq_vault_slot[k])) < 0) { snprintf(why, KLQ_WHY, "the level's .ANM has no slot %s", klq_vault_slot[k]); return 0; }
        clip[k] = ((DWORD (__fastcall *)(void *, void *, DWORD))(DWORD_PTR)KLH_VA(KLQ_CLIP))((void *)(DWORD_PTR)pl, 0, (DWORD)s[k]);
        if (!clip[k]) { snprintf(why, KLQ_WHY, "this body's set has no clip for %s (Play would return no channel and the vault's start reads through it, 0x6a2a65)", klq_vault_slot[k]); return 0; }
        /* review S4: a channel the vault's Play replaces is reported to the vault before Play returns, and the vault says yes to any report */
        if ((rep = klq_replaced(pl, clip[k], &first)) != 0) {
            if (rep < 0) snprintf(why, KLQ_WHY, "his animation channels cannot be read");
            else {
                DWORD ch = klh_rd32(pl + 0x70) + 0x1c + 0x38 * (DWORD)first; float cf = 0, ct = 0;
                klh_rd(ch + 4, &cf, 4); klh_rd(ch + 0xc, &ct, 4); if (!klb_finite(cf)) cf = -1.0f; if (!klb_finite(ct)) ct = -1.0f;
                snprintf(why, KLQ_WHY, "%d channel(s) of his play that the vault's own Play would replace and report (the first: channel %d, clip %08lx at frame %.1f of %.0f): the vault would be ended and freed inside its start (0x4da711, 0x5d0260, 0x595b70)",
                         rep, first, klh_rd32(ch), cf, ct);
                *again = 1;                                                  /* second review D2: the count is of the moment (a stop transition, a turn) */
            }
            return 0;
        }
    }
    n3[0] = e->n[0]; n3[2] = e->n[1];
    memset(rot, 0, sizeof rot);
    ((void (__fastcall *)(float *, const float *))(DWORD_PTR)KLH_VA(KLQ_MATRIX))(rot, n3);
    pos[0] = foot[0] - e->n[0] * e->depth * 0.5f; pos[1] = nd[1] + rise; pos[2] = foot[2] - e->n[1] * e->depth * 0.5f; pos[3] = 0;      /* the middle of the top */
    memset(klq_cover, 0, sizeof klq_cover);
    *(float *)(klq_cover + 0x0c) = foot[0]; *(float *)(klq_cover + 0x10) = nd[1]; *(float *)(klq_cover + 0x14) = foot[2];
    memcpy(klq_cover + 0x2c, n3, 12); *(float *)(klq_cover + 0x54) = e->depth;
    k = ((char (__fastcall *)(void *, void *, void *, DWORD, float *, float *, DWORD, DWORD))(DWORD_PTR)KLH_VA(KLQ_VAULT))((void *)(DWORD_PTR)pl, 0, klq_cover, 0, pos, rot, 1, 0);
    klh_rd(disp + 4, &act, 4);
    now = KLB_T(GetTickCount());
    if (!k || !act || klh_rd32(act) != KLQ_VAULT_VT || klh_rd32(act + 8) != pl) {
        int rd = klh_rd(pl + 0x7b4, &cnt, 4) && klh_rd(pl + 0x7a5, &on, 1);
        snprintf(why, KLQ_WHY, "the game's vault start %s and his action now is %08lx: the vault did not outlive its own start (no channel was there to be replaced: another cause); right after the start his collision count was %lu and the flag %d%s",
                 k ? "said yes" : "said NO (the action pool is empty: nothing was stopped or started)", act, cnt, on, rd ? "" : " (NOT READ)");
        /* Second review D1. klq_refuse had the count at 0 and the flag at 1 in this very tick, and nothing but the start ran since. The start switches the
           collision off at 0x6a2a4a, AFTER leave-cover (0x6a2817); an End that ran before that point gave nothing back (0x8b41c0 does not count below 0), the
           object was deleted, and the start went on to switch the collision off - with no action left to switch it on. (An End that ran inside Play, after
           0x6a2a4a, gave it back itself: the count is 0 then.) So a count that is not 0 here is the start's own: this file gives it back - the proxy to the
           node (he still stands at the foot), then the collision on - or owes it for 3 s as after a climb, and watches for the RESULT. */
        if (rd && (cnt || !on)) {
            klog("climb: edge %d: the vault's start LEFT HIS COLLISION SWITCHED OFF (count %lu, flag %d; both were 0 and 1 before the call) and no vault action is there to switch it on (his action now %08lx): this file gives it back",
                 ei + 1, cnt, on, act);
            memset(&klq_r, 0, sizeof klq_r); memset(&klq_a, 0, sizeof klq_a);
            if (klq_give_back(pl, ei, e, nd[1] + rise, "after a vault start that kept no action", &no)) {
                klq_a.player = pl; klq_a.at = now; klq_a.edge = ei; klq_a.byft = feet != nd[1]; klq_a.feet0 = feet; klq_a.e = *e;      /* the RESULT 2 s later: the start's own clip may still play */
            } else {
                klog("climb: edge %d: the proxy and the collision are NOT given back yet: %s - nothing is called; asked again every frame for 3 s", ei + 1, no);
                klq_r.player = pl; klq_r.began = klq_r.tick_at = klq_r.owe_since = now; klq_r.edge = ei; klq_r.vault = 1; klq_r.e = *e; klq_r.stage = 9; klq_r.owed = 1;
                klq_r.have_clock = klq_clock(&c); klq_r.clock0 = c; klq_r.byft = feet != nd[1]; klq_r.feet0 = feet; klq_r.top_y = nd[1] + rise;
            }
        }
        return 0;
    }
    memset(&klq_r, 0, sizeof klq_r); memset(&klq_a, 0, sizeof klq_a);
    klq_r.player = pl; klq_r.action = act; klq_r.began = klq_r.tick_at = now; klq_r.limit = 4000; klq_r.edge = ei; klq_r.vault = 1; klq_r.e = *e;
    klq_r.have_clock = klq_clock(&c); klq_r.clock0 = c; klq_r.byft = feet != nd[1]; klq_r.feet0 = feet; klq_r.stage = 2; klq_r.top_y = nd[1] + rise;
    klog("climb: edge %d: the game's own VAULT started from node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f) to (%.0f, %.0f, %.0f), slots %d / %d: action %08lx (its End puts the proxy at the node and switches the collision on itself)",
         ei + 1, nd[0], nd[1], nd[2], ft[0], ft[1], ft[2], pos[0], pos[1], pos[2], s[0], s[1], act);
    return 1;
}

/* The climb. -> 1 started (or dry), 0 not: why[KLQ_WHY]; *noclip = the body has no clip for the slot (the vault may be tried) */
static int klq_climb(DWORD pl, DWORD disp, int ei, int cls, const float nd[3], const float ft[3], const float foot[3], float dist, float feet, float rise, int *noclip, char *why)
{
    const struct klq_edge *e = &klq_lv.e[ei]; const char *name = klq_cls[cls].slot; float stand = klq_cls[cls].stand;
    float p1[3], p2[3], to[3], n3[4] = { 0, 0, 0, 0 }, rot[12], frames, f5, f6, fwd, target, t0 = 0, cto = 0; DWORD act = 0, chan = 0, clip, flags, fl = 0, c = 0; int slot; char ok;
    *noclip = 0;
    if ((slot = klq_slot(pl, name)) < 0) { snprintf(why, KLQ_WHY, "the level's .ANM has no slot %s (a build without the step of tools\\kl_fa_climb.py)", name); *noclip = 1; return 0; }
    p1[0] = foot[0] + e->n[0] * stand; p1[1] = nd[1]; p1[2] = foot[2] + e->n[1] * stand;
    p2[0] = p1[0]; p2[1] = nd[1] + rise; p2[2] = p1[2];
    if (klq.dry) {
        klog("climb: edge %d: WOULD climb by %s (slot %d) from node (%.0f, %.0f, %.0f), %.0f from the face: P1 (%.0f, %.0f, %.0f) at event 5, P2 (%.0f, %.0f, %.0f) at event 6; %d full-body channel(s) of his play NOW (after the dwell) - DRY RUN, nothing is called",
             ei + 1, name, slot, nd[0], nd[1], nd[2], dist, p1[0], p1[1], p1[2], p2[0], p2[1], p2[2], klq_playing(pl));
        return 1;
    }
    ((void (__fastcall *)(void *, void *, DWORD, DWORD, DWORD, DWORD))(DWORD_PTR)KLH_VA(KLQ_MINI))((void *)(DWORD_PTR)pl, 0, (DWORD)slot, 0, 0, 1);
    klh_rd(disp + 4, &act, 4);
    if (!act || klh_rd32(act) != KLQ_MINI_VT || klh_rd32(act + 8) != pl || (klh_rd32(act + 0x18) & 0xffff) != (DWORD)slot || !(chan = klh_rd32(act + 0x20))) {
        snprintf(why, KLQ_WHY, "the game did not keep the action for %s (his action now is %08lx): this body's set has no clip for the slot", name, act);
        *noclip = 1; return 0;
    }
    clip = klh_rd32(chan);
    if (!klq_clip(clip, &frames, &f5, &f6, &flags, &fwd) || !klh_rd(chan + 4, &t0, 4) || !klh_rd(chan + 0xc, &cto, 4) || !klh_rd(chan + 0x14, &fl, 4) || !klb_finite(t0) || !klb_finite(cto) || cto < 2.0f ||
        ((fl & 7) != 1 && (fl & 7) != 3) || klq_root_chan(pl) != chan) {
        /* not the picture the start gives by the code read: the clip record, or a channel that plays from t0 to its last frame and is the one the game would align */
        ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLQ_STOP))((void *)(DWORD_PTR)pl, 0);
        snprintf(why, KLQ_WHY, "the action's channel %08lx (clip %08lx, flags %lx) is not the playing full-body root-motion channel the game would align: stopped, nothing else changed", chan, clip, fl);
        return 0;
    }
    n3[0] = e->n[0]; n3[2] = e->n[1];
    memset(rot, 0, sizeof rot);
    ((void (__fastcall *)(float *, const float *))(DWORD_PTR)KLH_VA(KLQ_MATRIX))(rot, n3);
    memset(&klq_r, 0, sizeof klq_r); memset(&klq_a, 0, sizeof klq_a);
    memcpy(klq_r.rot, rot, sizeof rot);
    if (klq.align == 2 && f5 > t0 && f6 > f5 && f6 < cto) {                    /* Dead Men: the foot at event 5, then the top at event 6 */
        memcpy(klq_r.p2, p2, 12); klq_r.f_foot = f5; klq_r.f_top = f6; klq_r.stage = 1;
        memcpy(to, p1, 12); target = f5 - t0;
    } else if (klq.align == 2 && f6 > t0 && f6 < cto) {                        /* no event 5: the top at event 6 alone, as the game's NPC mover does */
        klq_r.stage = 2; klq_r.f_top = f6; memcpy(to, p2, 12); target = f6 - t0;
    } else {                                                                  /* Align=1, or a clip without the events: the end place at the last frame */
        /* KLQ_LIFT over the top (second review N3): the game blends this one correction in linearly up to the last frame, so aimed AT the top he would cross
           the face under it (High, top 203.5 over his feet: 5.0 under at the face, 3.1 under at frame 46 - measured); with the lift he crosses it 0.8 .. 6.6
           over it for every High rise tried (183.5 .. 220) and comes down the 10 when the clip is over */
        float over = fwd - stand; if (!(over > 5.0f)) over = 5.0f; if (over > e->depth - 5.0f) over = e->depth - 5.0f;
        to[0] = foot[0] - e->n[0] * over; to[1] = p2[1] + KLQ_LIFT; to[2] = foot[2] - e->n[1] * over;
        klq_r.stage = 2; target = cto - t0;
    }
    ok = klq_align(pl, rot, to, target);
    klog("climb: edge %d: started %s (slot %d) from node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f), %.0f from the face: action %08lx, clip %08lx of %.0f frames (flags %lx), events 5 at %.0f and 6 at %.0f; %s to (%.0f, %.0f, %.0f) in %.0f frames",
         ei + 1, name, slot, nd[0], nd[1], nd[2], ft[0], ft[1], ft[2], dist, act, clip, frames, flags, f5, f6, ok ? "aligned" : "NOT aligned", to[0], to[1], to[2], target);
    if (!ok) {
        /* the game took no channel (0x760120): the clip would play where he stands and end inside the obstacle. The collision has not been touched. */
        ((void (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLQ_STOP))((void *)(DWORD_PTR)pl, 0);
        memset(&klq_r, 0, sizeof klq_r);
        snprintf(why, KLQ_WHY, "the game found no channel to align (clip flags %lx: 0x40 = root motion %s): the action was stopped, he stays where he was, nothing else was changed", flags, flags & 0x40 ? "is set" : "is NOT set");
        return 0;
    }
    klq_r.player = pl; klq_r.action = act; klq_r.chan = chan; klq_r.clip = clip; klq_r.began = klq_r.tick_at = KLB_T(GetTickCount()); klq_r.edge = ei; klq_r.e = *e;
    klq_r.limit = (DWORD)(frames * 40.0f) + 1500;                             /* 25 frames a second, on the game's clock */
    klq_r.have_clock = klq_clock(&c); klq_r.clock0 = c; klq_r.to = cto; klq_r.last_t = t0; klq_r.byft = feet != nd[1]; klq_r.feet0 = feet; klq_r.top_y = p2[1];
    klq_collision(pl, 0, "the climb starts"); klq_r.owed = 1;
    return 1;
}

static void klq_tick(int game_thread)
{
    static DWORD last; struct klb_snap s; DWORD now, pl = 0, disp = 0; char scene[160], key[64], why[KLQ_WHY]; float ft[3], hn[3], nd[3], bk[3], pr[3], face, dt; const char *no; int i;
    if (!klq.on || !klh_exe_ok) return;
    now = GetTickCount();
    if (!game_thread) {                                                      /* everything here belongs to the game's thread */
        if (now - klq_w.game_at > 5000 && !klq_w.told_thread && klb_read(&s) && s.state == KLB_ROUND) {      /* (reads only) */
            klq_w.told_thread = 1;
            klog("climb: a round runs and no tick has come on the game's thread for 5 s ([KLHook] Tick=0?): nobody climbs meanwhile");
        }
        return;
    }
    klq_w.game_at = KLB_T(now);
    if (klq_r.player) { klq_follow(now); return; }                            /* a climb runs: every frame, whatever the round does */
    if (klq_a.player) klq_after(now);                                         /* the RESULT of the last one (reads only) */
    if (now - last < 50) return;
    last = now;
    if (!klb_read(&s) || s.state != KLB_ROUND) { klq_w.have = 0; return; }    /* an Arcade round that runs, or nothing */
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return;
    klq_source();
    if (!klq_lv.n || strcmp(key, klq_lv.key)) return;                        /* no edge, or not the level the file belongs to */
    if (!klb_level(why)) {                                                   /* klbot.c section 0: not on a stock level, an unknown one, or without the Steam guard */
        if (!klq_w.told_gate++) klog("climb: %s: nobody climbs here (it acts only on a level that is not stock)", why);
        return;
    }
    if (!klq_code()) { if (!klq_w.told_code++) klog("climb: the game's routines are not the ones this build knows: nobody climbs"); return; }
    if (!kle_human(&pl, ft, hn) || !klq_node(klh_rd32(pl + 4), nd, bk)) { klq_w.have = 0; return; }      /* no local heister in play */
    if (!klq_w.have || klq_w.player != pl) {
        memset(klq_w.since, 0, sizeof klq_w.since); memset(klq_w.told, 0, sizeof klq_w.told); memset(klq_w.seen, 0, sizeof klq_w.seen);
        memset(klq_w.vr_since, 0, sizeof klq_w.vr_since); memset(klq_w.vr_last, 0, sizeof klq_w.vr_last); memset(klq_w.vr_n, 0, sizeof klq_w.vr_n); klq_w.speed = 1e9f;
    }
    else if ((dt = (now - klq_w.at) / 1000.0f) > 0.0f)
        klq_w.speed = (float)sqrt((nd[0] - klq_w.pos[0]) * (nd[0] - klq_w.pos[0]) + (nd[2] - klq_w.pos[2]) * (nd[2] - klq_w.pos[2])) / dt;
    klq_w.have = 1; klq_w.player = pl; klq_w.at = now; memcpy(klq_w.pos, nd, 12);
    face = (float)sqrt(bk[0] * bk[0] + bk[2] * bk[2]);
    for (i = 0; i < KLQ_NEDGE; i++) {
        const struct klq_edge *e = &klq_lv.e[i]; float d, along, foot[3], look, feet, rise; int in, noclip = 0, done, cls, again = 0, usevault;
        if (!e->on) continue;
        d = klq_off(e, nd);
        along = (nd[0] - e->a[0]) * e->u[0] + (nd[2] - e->a[2]) * e->u[1];
        /* his feet: the node's height when that is at the floor, else the floats at +0x460 (klhop.c's two readings) */
        feet = fabs(nd[1] - e->floor) <= KLQ_HEIGHT ? nd[1] : ft[1];
        in = d > KLQ_NEAR && d <= KLQ_FAR && along >= 0.0f && along <= e->len && fabs(feet - e->floor) <= KLQ_HEIGHT;      /* a NaN is not there */
        look = face > 0.01f ? (bk[0] * e->n[0] + bk[2] * e->n[1]) / face : 0.0f;      /* 1 = his back points out of the face: he looks straight at it */
        rise = e->a[1] - feet;                                               /* Dead Men's h: the top over his feet; its table gives the class */
        for (cls = 0; cls < 3 && klq_cls[cls].top < rise; cls++) ;
        if (klq.log >= 2 && now - klq_w.say_at >= 1000 && d > -200.0f && d < 600.0f && along > -200.0f && along < e->len + 200.0f) {
            klq_w.say_at = KLB_T(now);
            klog("climb: node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f): %.0f from the face of edge %d, %.0f along it (0 .. %.0f), %+.0f / %+.0f to its floor, speed %.0f, facing %.2f, %d full-body channel(s) of his play%s",
                 nd[0], nd[1], nd[2], ft[0], ft[1], ft[2], d, i + 1, along, e->len, nd[1] - e->floor, ft[1] - e->floor, klq_w.speed, look, klq_playing(pl), in ? " = AT THE FOOT" : "");
        }
        if (!in) { klq_w.since[i] = 0; klq_w.told[i] = 0; klq_w.seen[i] = 0; klq_w.vr_since[i] = klq_w.vr_last[i] = 0; klq_w.vr_n[i] = 0; continue; }
        if (!klq_w.seen[i]) {
            int hp = klq_proxy(pl, pr);
            klq_w.seen[i] = 1;
            /* the channel count of this line is of the moment he ARRIVES (still walking): not the count a vault would meet after the dwell (second review D2) */
            if (klq.log) klog("climb: at the foot of edge %d: node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f), proxy (%.0f, %.0f, %.0f)%s, %.0f from the face, speed %.0f, facing %.2f; the top is %.1f over his feet = %s, id %d; %d full-body channel(s) of his play as he arrives%s",
                              i + 1, nd[0], nd[1], nd[2], ft[0], ft[1], ft[2], pr[0], pr[1], pr[2], hp ? "" : " (not read)", d, klq_w.speed, look, rise, cls < 3 && rise > 25.0f ? klq_cls[cls].slot : "no class of Dead Men's table",
                              cls < 3 ? klq_slot(pl, klq_cls[cls].slot) : -1, klq_playing(pl), feet == nd[1] ? "" : " (his NODE is not at the floor: the height is taken from +0x460)");
        }
        if (klq_w.told[i] & 2) continue;                                     /* tried at this stay: he has to step away first */
        if (klq_w.speed > klq.speed || (klq.cosang > -1.5f && look < klq.cosang) || (klq.key && !(klq_keystate && (klq_keystate(klq.key) & 0x8000)))) {
            klq_w.since[i] = 0; klq_w.vr_since[i] = klq_w.vr_last[i] = 0; klq_w.vr_n[i] = 0; klq_w.told[i] &= ~12;      /* the stand is broken: a refused vault is counted anew */
            continue;
        }
        if (!klq_w.since[i]) klq_w.since[i] = KLB_T(now);
        if (now - klq_w.since[i] < klq.dwell) continue;
        if ((klq_w.told[i] & 4) && now - klq_w.vr_last[i] < KLQ_RETRY) continue;      /* a vault refused for the channels that play: asked again four times a second */
        if ((no = klq_refuse(pl, &disp)) != 0) {                             /* a reload, a fall: it passes - said once, tried again while he stays */
            if (!(klq_w.told[i] & 1)) { klq_w.told[i] |= 1; klog("climb: edge %d NOT climbed yet: %s", i + 1, no); }
            continue;
        }
        foot[0] = e->a[0] + e->u[0] * along; foot[1] = e->a[1]; foot[2] = e->a[2] + e->u[1] * along;       /* the point of the edge nearest to him */
        klq_w.told[i] |= 2; why[0] = 0;
        if (!(rise > 25.0f) || cls == 3) { klog("climb: edge %d NOT climbed: its top is %.1f over his feet; Dead Men climbs over 25 and up to 220", i + 1, rise); return; }
        if (!klq.vault && cls == 0 && !klq.low) { klog("climb: edge %d NOT climbed: its top is %.1f over his feet = Dead Men's Low, whose clip reaches the face only in its last frame (re\\climb.md 2.3): off unless [Climb] Low=1", i + 1, rise); return; }
        if (!klq.vault && cls == 0 && klq.align == 1) { klog("climb: edge %d NOT climbed: its top is %.1f over his feet = Dead Men's Low, and Align=1 is not for that class (its clip lunges 52 forward in its first 3 frames; only the first of Dead Men's two alignments takes that back: he would run through the face at foot level): Align=2", i + 1, rise); return; }
        if (klq.vault && klq.dry) {
            klog("climb: edge %d: WOULD vault from node (%.0f, %.0f, %.0f) onto the top, %.0f up; %d full-body channel(s) of his play NOW (after the dwell; the vault's Play would replace and report each: with one or more the vault is refused at this moment and asked again) - DRY RUN, nothing is called",
                 i + 1, nd[0], nd[1], nd[2], rise, klq_playing(pl));
            return;
        }
        usevault = klq.vault || (klq_w.told[i] & 16);
        done = usevault ? klq_vault(pl, disp, i, nd, ft, foot, feet, rise, &again, why) : klq_climb(pl, disp, i, cls, nd, ft, foot, d, feet, rise, &noclip, why);
        if (!done && !usevault && noclip && klq.fallback && !klq.dry) {
            klog("climb: edge %d: %s - the vault is tried (Fallback=1)", i + 1, why);
            klq_w.told[i] |= 16;                                             /* a later try at this stay goes straight to the vault: the start that found no clip is not called again */
            if ((no = klq_refuse(pl, &disp)) != 0) { snprintf(why, sizeof why, "%s", no); done = 0; }
            else done = klq_vault(pl, disp, i, nd, ft, foot, feet, rise, &again, why);
        }
        if (!done && again) {
            /* Second review D2: the channels that play are of the moment - the clips of the vault's body class are also the walk, stop and turn clips. So this
               refusal does not end the stay: it is said once, asked again every KLQ_RETRY ms while he stands, and when it has stood for a second that is said
               (with the tries) - only that line means 'the vault is refused from this stand'. */
            klq_w.told[i] &= ~2; klq_w.vr_last[i] = KLB_T(now); klq_w.vr_n[i]++;
            if (!(klq_w.told[i] & 4)) { klq_w.told[i] |= 4; klq_w.vr_since[i] = KLB_T(now); klog("climb: edge %d NOT vaulted yet: %s - asked again four times a second while he stands here", i + 1, why); }
            else if (!(klq_w.told[i] & 8) && now - klq_w.vr_since[i] >= 1000) {
                klq_w.told[i] |= 8;
                klog("climb: edge %d: the vault is REFUSED from this stand: %d tries in %lu ms of standing, the last: %s (asked on while he stands; said no more)", i + 1, klq_w.vr_n[i], now - klq_w.vr_since[i], why);
            }
            return;
        }
        if (done && usevault && klq_w.vr_n[i]) klog("climb: edge %d: (the vault had been refused %d time(s) in the %lu ms before: the channels that played then are over)", i + 1, klq_w.vr_n[i], now - klq_w.vr_since[i]);
        if (!done) klog("climb: edge %d NOT climbed: %s", i + 1, why[0] ? why : "his state changed during the start");
        return;                                                               /* one start a tick */
    }
    if (klq.log >= 2 && now - klq_w.say_at >= 5000) {                         /* near no edge: every 5 s, so that a wrong reading of his place shows (live check K1) */
        int hp = klq_proxy(pl, pr);
        klq_w.say_at = KLB_T(now);
        klog("climb: node (%.0f, %.0f, %.0f), +0x460 (%.0f, %.0f, %.0f), proxy (%.0f, %.0f, %.0f)%s: near none of the %d edge(s), speed %.0f",
             nd[0], nd[1], nd[2], ft[0], ft[1], ft[2], pr[0], pr[1], pr[2], hp ? "" : " (not read)", klq_lv.n, klq_w.speed);
    }
}

static void klq_init(void)
{
    char t[32]; float ang; int v;
    memset(&klq, 0, sizeof klq); memset(&klq_lv, 0, sizeof klq_lv); memset(&klq_w, 0, sizeof klq_w); memset(&klq_r, 0, sizeof klq_r); memset(&klq_a, 0, sizeof klq_a);
    klq.on = GetPrivateProfileIntA("Climb", "Enable", 0, klh_ini) != 0;
    if (!klq.on) return;
    klq.dry = GetPrivateProfileIntA("Climb", "Dry", 0, klh_ini) != 0;
    GetPrivateProfileStringA("Climb", "Mode", "climb", t, sizeof t, klh_ini);
    klq.vault = !_stricmp(t, "vault");
    klq.fallback = GetPrivateProfileIntA("Climb", "Fallback", 0, klh_ini) != 0;
    klq.align = GetPrivateProfileIntA("Climb", "Align", 2, klh_ini) == 1 ? 1 : 2;
    klq.low = GetPrivateProfileIntA("Climb", "Low", 0, klh_ini) != 0;
    v = (int)GetPrivateProfileIntA("Climb", "HandFrames", 5, klh_ini); klq.hand = (float)(v < 1 ? 1 : v > 5 ? 5 : v);      /* 5 = 200 ms (second review N2) */
    klq.key = (int)GetPrivateProfileIntA("Climb", "Key", 0, klh_ini) & 0xff;
    klq_keystate = 0;
    if (klq.key) {
        HMODULE u = GetModuleHandleA("user32.dll");
        if (u) klq_keystate = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState");
        if (!klq_keystate) klog("climb: Key=%d is set and user32's GetAsyncKeyState was not found: the key cannot be asked, so NOBODY climbs (Key=0 asks for no key)", klq.key);
    }
    v = (int)GetPrivateProfileIntA("Climb", "Dwell", 400, klh_ini); klq.dwell = (DWORD)(v < 100 ? 100 : v > 5000 ? 5000 : v);
    klq.speed = klq_num("Climb", "Speed", "150", klh_ini); if (!klb_finite(klq.speed) || klq.speed < 10.0f) klq.speed = 10.0f;
    ang = klq_num("Climb", "Angle", "60", klh_ini);
    if (!klb_finite(ang) || ang <= 0.0f || ang >= 180.0f) ang = 0.0f;
    klq.cosang = ang > 0.0f ? (float)cos(ang * 3.14159265 / 180.0) : -2.0f;      /* -2 = not asked */
    klq.log = (int)GetPrivateProfileIntA("Climb", "Log", 1, klh_ini);
    klq_w.game_at = GetTickCount();
    klog("climb: on; Mode=%s Fallback=%d Align=%d HandFrames=%.0f Low=%d Key=%d Dwell=%lu Speed=%.0f Angle=%.0f Dry=%d Log=%d; at a [Climb] edge of the level's KLJoin.ini the local player is carried up by %s; Arcade only, on a level that is not the stock one of its slot%s",
         klq.vault ? "vault" : "climb", klq.fallback, klq.align, klq.hand, klq.low, klq.key, klq.dwell, klq.speed, ang, klq.dry, klq.log,
         klq.vault ? "the game's own vault action (0x619790)" : "Dead Men's climb clip (StartMiniAnim 0x5ea340, the alignment 0x80fdc0, the collision switch 0x5d6200 / 0x686600, the proxy 0x4af5b0)",
         klq.dry ? " - DRY RUN: no game routine is called" : "");
}

#endif /* KLCLIMB_C */
