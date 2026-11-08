#!/usr/bin/env python3
"""
Bench kits for the two staged-but-never-run builds (2026-11-06). One command each once the owner says "test".

    python tools/kl_bench_1106.py gen                 write/refresh the kit folders under C:/kl_build_1024/bench_1106 (no game contact)
    python tools/kl_bench_1106.py validate [kit|all]  DRY RUN: paths, md5s, TEST dll marker, ini sections, script ops, install.py --dry.
                                                      Never launches the game, never writes into the game folder.
    python tools/kl_bench_1106.py run lc1106 [solo|online|all]
    python tools/kl_bench_1106.py run dd10s1106 [solo|long|all]
    python tools/kl_bench_1106.py run lcglass1106 online       glass pass on the live chain: round-2 reset 0x25 time per seat
    python tools/kl_bench_1106.py verify lc1106|dd10s1106 [part]    re-read the logs of the last run (no game contact)

Kits
  lc1106     Last Call chain stage (C:/kl_build_1024/lastcall_chain_1105/stage: plain zip c8dd18ee, bots 42ed37ba, F01_Main_LS.SND)
             solo Arcade round on DM05A (slot F01, page 3) with [Heli] Probe=2, [Camera] Log=1, d3 shots; then an online 2-seat round
             (the hook swaps in the bots zip) = Q32 host/join pair, round 1 -> shop -> round 2.
  dd10s1106  DD10 Flat Raid slim stage (C:/kl_build_1024/dd10_slim_1105/stage, slot F07, page 3 entry 5): solo round + a long online match
             (4 rounds) with the memory log; compares the largest free block with the ~14.4 MB baseline.

IMPORTANT, said plainly: kl_solo_test.py runs kl2.exe against the LIVE Dog Days folder (it reads <DD>/KLExpansion/Maps/<MAP>), so the staged
files can only be tested by installing them there. `run` therefore (1) records the md5 of every file in the map folder, (2) runs the stage's
own install.py (originals renamed *.before-1105chain / *.before-1105slim, never overwritten), (3) runs the bench (which itself swaps the TEST
dinput8.dll in and the live one back), (4) ALWAYS runs install.py --undo in a finally block and compares the md5s with step 1. If the undo
fails the tool prints UNDO FAILED and the exact command to run by hand. It touches nothing but KLExpansion/Maps/<MAP> and dinput8.dll
(swapped by kl_solo_test). KL_PortBackup is never touched. The launch options are never changed (the bench starts kl2.exe directly).
"""
import math, hashlib, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = 'C:/kl_build_1024/bench_1106'
DD = 'C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days'
SOLO = 'G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools/build/klhook/solo'
HOOK_SRC = 'C:/kl_build_1024/n9_twins/727a73bb/dinput8.dll'    # TEST twin b6a69772 of SHIP 727a73bb (6b pics_1105_hook, live since 11-06)
HOOK_MD5 = 'b6a697726b66ca7270921d6d4543005f'
Q32 = 'C:/kl_build_1024/c9_1028/q32'
COVER = ('AssertSoft', 'ClientBuild', 'ClientBuildHost', 'ClientRewrite', 'ClientRingSync')
OPS = set('waitwin settle tapuntil tap wait windows sel expect msg waitload waitstate waitvan waitpeers tele goto face pos ents peek log pass fail label jump onwin mouse'.split())

KITS = {
    'lc1106': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lastcall_chain_1105/stage', tag='.before-1105chain',
                   files={'F01_Main.zip': 'c8dd18ee28b511db2ee46a10f9e86e11', 'F01_Main.bots.zip': '42ed37ba', 'F01_Main_LS.SND': 'b6fdd4c0'},
                   solo_secs=1500, parts=('solo', 'online')),
    'dd10s1106': dict(map='DD10', slot='F07', entry=5, stage='C:/kl_build_1024/dd10_slim_1105/stage', tag='.before-1105slim',
                      files={'F07_Main.zip': '66ec246da361ace049fc65e2762b4a9c', 'F07_Main.bots.zip': '3ccb580fc527638af2eb099394fc5369',
                             'F07_Main.WAV': '9fd304579b3dd40c577265a79f7c4e90', 'F07_Main.WHD': '3a260f8b542f4308f77e0a62840075a0'},
                      solo_secs=1500, parts=('solo', 'long')),
    # glass pass on top of the LIVE chain (install.py pins c8dd18ee): the round-2 reset (0x25) must drop from 21-29 s per seat to seconds
    'lcglass1106': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lastcall_glass_1106/stage', tag='.before-1106glass',
                        files={'F01_Main.zip': '3f0018b38593d708ac830e53150fb814', 'F01_Main.bots.zip': 'cb962a65', 'F01_Main.bots.base.md5': '00cfe35a'},
                        solo_secs=1500, parts=('online', 'solo')),
    # the LIVE DM05A as it is (chain + glass + pd2guns + buttons + pics, 11-06): stage None = nothing installed, the live zip is pinned and
    # the map folder must be byte-identical after the run (escape boarding with E, re/lastcall_escape_screen_1106.md)
    'lclive1106': dict(map='DM05A', slot='F01', entry=0, stage=None, tag=None, live={'F01_Main.zip': 'e6d2f73e'},
                       solo_secs=1500, parts=('solo',)),
    # staged 11-06 on the live e6d2f73e (workflow lastcall-doors-spawns-stage, both reviewed ship_to_bench): kick doors (4 KL_Door groups,
    # +187 entities, +20 .prm chunks, inis Entries=54446) and the 31 start nodes moved to the west end of floor 2
    'lcdoors1106': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcdoors_1106', tag='.before-doors1106',
                        files={'F01_Main.zip': 'a24d7432beae06204e9f98bf35f07ede', 'F01_Main.bots.zip': '997d5b3f', 'KLGuns.ini': 'e6f95d99',
                               'KLJoin.ini': '520b0667'},
                        solo_secs=1500, parts=('solo',)),
    'lcspawn2f1106': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcspawn2f_1106', tag='.before-spawn2f1106',
                          files={'F01_Main.zip': '88e23dd5896afc5ee471860a1a8c100c', 'F01_Main.bots.zip': '5e16c4a0'},
                          solo_secs=1500, parts=('solo',)),
    # black escape outro (re/lastcall_outro_black_1106.md): the Escaping spline cut from 17 to 6 points (one .prp byte) so the heli parks
    # ~31 m from the fixed EscCamera01 eye instead of flying out of the lit scene; expect shots after departure to show the heli
    'lcoutro1106': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcoutro_1106', tag='.before-outro1106',
                        files={'F01_Main.zip': '77a42f74a8d6853299612a63884b1b89', 'F01_Main.bots.zip': '2cef6d0b', 'F01_Main.bots.base.md5': '5115b51a'},
                        solo_secs=1500, parts=('solo',)),
    # lcoutro1106 bench (11-06 12:15): outro 60 -> ~23 s but still black with the heli parked 18 m from the fixed eye; this adds the in-heli LookAtPos camera
    # (kl_club_helicam_1106 variant A on lcoutro_1106; lchelicam_1106's install.py re-pinned on the live e6d2f73e files)
    'lcoutcam1106': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcoutcam_1106', tag='.before-outcam1106',
                         files={'F01_Main.zip': '24576526f95507cbc8b9ffe61951b5c1', 'F01_Main.bots.zip': '2ae52345', 'F01_Main.bots.base.md5': 'd7116a6b'},
                         solo_secs=1500, parts=('solo',)),
    # lcoutcam1106 bench: flat grey outro; re/lastcall_helicam_geometry_1106.md says the variant A park point is INSIDE BuildingF. Two candidates, all offsets GUESSes
    # (both on lcoutro_1106, install.py live-pinned by kl_club_helicam_1106 stage --pin-live): 2a = eye east of F's face (f5 +700, f6 -500) aimed at the heli;
    # 2b = small offset (f5 -450, f6 +100) aimed at EscCameraLAST, rise/hover only (park may still be inside F)
    'lcoutcam2a1106': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcoutcam2a_1106', tag='.before-outcam2a1106',
                           files={'F01_Main.zip': '2e882b7852dc066c379aa8b1552fdbc2', 'F01_Main.bots.zip': '3fa2437c', 'F01_Main.bots.base.md5': '8ed9edb3'},
                           solo_secs=1500, parts=('solo',)),
    'lcoutcam2b1106': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcoutcam2b_1106', tag='.before-outcam2b1106',
                           files={'F01_Main.zip': 'eb4e450f48e2e8e0995e33c4a4f40c5c', 'F01_Main.bots.zip': '9fbd2565', 'F01_Main.bots.base.md5': 'e664ba34'},
                           solo_secs=1500, parts=('solo',)),
    # 6b's pd2guns_1106b went live on DM05A (1a97e186, Entries 54447): all four passes re-based on it in ONE chain by kl_lastcall_chain_1106
    # (doors -> spawn2f -> outro -> helicam 2a), one install.py pinning the 5 live files; expect doors, 2nd-floor start, short outro, 2a camera
    'lcchain2a1106': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcchain_2a_live_1a97e186', tag='.before-chain1106',
                          files={'F01_Main.zip': 'f048f569be30795d9b4ac6b958aacd8b', 'F01_Main.bots.zip': '34d25023', 'F01_Main.bots.base.md5': '5f486ecf',
                                 'KLGuns.ini': '70c39279', 'KLJoin.ini': 'e1d6646a'},
                          solo_secs=1500, parts=('solo',)),
    # lcchain2a1106 bench (11-06): PASS, but the outro is only 8 s (0x1f 450 s after launch) and fell between the 20 s shots: same stage, shots every
    # 4 s over 380-540 s (41 shots) to see the 2a camera's frame
    'lcchain2a1106s': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcchain_2a_live_1a97e186', tag='.before-chain1106',
                           files={'F01_Main.zip': 'f048f569be30795d9b4ac6b958aacd8b', 'F01_Main.bots.zip': '34d25023', 'F01_Main.bots.base.md5': '5f486ecf',
                                  'KLGuns.ini': '70c39279', 'KLJoin.ini': 'e1d6646a'},
                           solo_secs=900, parts=('solo',), shots='380-540:4'),
    # lcchain2a1106(s) 11-06: the bots' exit call never came, so the hook's clock call fired at 2.5 s left (heli state 4 at ~339 s), the bench player was left
    # behind and the outro was the TIME IS UP panel. 'b': same stage and files, the solo.ini sets [Bots] LastVehicleLead=600 (the clock call 60 s before the end,
    # the hook's own knob, 'Bots.DM05A' does not set it), boards at once at state 3 (tele + 2 E holds, no 5 s / 3 s / goto waits). The Arcade round cannot be
    # lengthened from a bench ini (RoundClockFix/TimeAuto act on an online lobby's heist time only). Shots are time-based (D3dShotFrom/Every/Max, no
    # event trigger): 400-556 every 4 s = the 40-shot cap, centred on the expected state 3 -> outro at ~400-450 s after launch
    'lcchain2a1106b': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcchain_2a_live_1a97e186', tag='.before-chain1106',
                           files={'F01_Main.zip': 'f048f569be30795d9b4ac6b958aacd8b', 'F01_Main.bots.zip': '34d25023', 'F01_Main.bots.base.md5': '5f486ecf',
                                  'KLGuns.ini': '70c39279', 'KLJoin.ini': 'e1d6646a'},
                           solo_secs=900, parts=('solo',), shots='400-556:4'),
    # d: as b, on the SAFE-DOORS chain (kl_lastcall_chain_1106.py chain --cam 2a --doors B01,A02): F03/F02 dropped (bots stood 12 s short of F03 in both chain runs)
    'lcchain2a1106d': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcchain_2a_safedoors_live_1a97e186', tag='.before-chain1106',
                           files={'F01_Main.zip': 'f4e801bda084228b4aee09ce4c86a14c', 'F01_Main.bots.zip': '6a552f8d', 'F01_Main.bots.base.md5': 'e9b020ca',
                                  'KLGuns.ini': '70c39279', 'KLJoin.ini': 'e1d6646a'},
                           solo_secs=900, parts=('solo',), shots='400-556:4'),
    # n (c9 11-06): as d WITHOUT LastVehicleLead: in d the 60 s clock call came at 300 s before any bot reached stage 2, so this one measures
    # when the bots call the heli themselves with only B01+A02 (door-less runs: first stage 1->2 at 281-346 s; 4-door chain: none by 358 s)
    'lcchain2a1106n': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcchain_2a_safedoors_live_1a97e186', tag='.before-chain1106',
                           files={'F01_Main.zip': 'f4e801bda084228b4aee09ce4c86a14c', 'F01_Main.bots.zip': '6a552f8d', 'F01_Main.bots.base.md5': 'e9b020ca',
                                  'KLGuns.ini': '70c39279', 'KLJoin.ini': 'e1d6646a'},
                           solo_secs=900, parts=('solo',), shots='400-556:6'),
    # c (c9 11-06, candidate 2c): as d, but the camera is a FIXED eye again (EscCamera01 = LookFromPos at CamPos01, inside the Roof .rmi box 7) and the
    # Escaping spline is a 5-point climb to the north-east over open air (kl_lastcall_chain_1106.py chain --cam 2c --doors B01,A02 on the pre-chain
    # live 1a97e186): room-culling diagnosis, the 2a/stock frames were uniform grey because eye and heli sat outside every Roof box.
    'lcchain2c1106d': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcchain_2c_safedoors_live_1a97e186', tag='.before-chain1106',
                           files={'F01_Main.zip': 'e10ea4882161fe91d653d1c4f6e87abc', 'F01_Main.bots.zip': 'bffb9736', 'F01_Main.bots.base.md5': '369e91e3',
                                  'KLGuns.ini': '70c39279', 'KLJoin.ini': 'e1d6646a'},
                           solo_secs=900, parts=('solo',), shots='400-556:4'),
    # d2 (c9 11-06, candidate 2d): as 2c, but EscCamera01 is the stock outside camera (eFMM_LookFromPosFA): eye = the box node moved to the 2c eye
    # (7093,2181,2727, Roof .rmi box 7), aim = the heli group (Escape_Chopper) re-read every frame, so the view follows the climb. Stage built from the
    # pre-chain base D:/kl_stage/lc2c_base_1a97e186 (1a97e186) with --pin-dir = the live folder: installs DIRECTLY over live 2c (e10ea488), backups .before-chain2d1106.
    # The eye check below stays active (the eye is fixed at CamPos01 again); the shots decide whether the heli is in view and lit.
    'lcchain2d1106d': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcchain_2d_safedoors_live_1a97e186', tag='.before-chain2d1106',
                           files={'F01_Main.zip': '1c1fc5d46dc60ce2a71319e8b56ece8b', 'F01_Main.bots.zip': '2718b4ca', 'F01_Main.bots.base.md5': 'a97a3f26'},
                           solo_secs=900, parts=('solo',), shots='400-556:4'),
    # e (c9 11-06, candidate 2e): the 2d camera with the eye moved to (7400,2500,2800) (Roof box 7) and the NORTH climb ROUTE_2E (the 2d route made the heli stop
    # on BuildingJ's terrace slab, hidden). Built with: kl_lastcall_chain_1106.py chain --cam 2e --only outro,helicam --tag .before-chain2e1106 on the LIVE zip
    # 14c8d9dd (6b's pd2guns c+d+e+f over the installed 2c chain, which already holds doors B01,A02 and spawn2f, hence --only). The stage installs over 14c8d9dd.
    # KLJoin/KLGuns are unchanged by this stage, so the kit keeps the live inis (pd2guns) and only lists the three changed files.
    'lcchain2e1106d': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcchain_2e_14c8d9dd', tag='.before-chain2e1106',
                           files={'F01_Main.zip': '9ba99a7c76aecaad2a7322fbcccc7563', 'F01_Main.bots.zip': '1fa0ff33', 'F01_Main.bots.base.md5': '62cdd295'},
                           solo_secs=900, parts=('solo',), shots='400-556:4'),
    # f (c9 11-06, candidate 2f): 2e (same eye, LookFromPosFA aim, north ROUTE_2E) + Roof .rmi box 7 enlarged to x 6676..9266, y 1460..6600, z 2594..4426 so the
    # lifted-off heli stays in a Roof box (hypothesis: a dynamic entity outside every Roof box is only in Backdrop and is not drawn). Built with:
    # kl_lastcall_chain_1106.py chain --cam 2f --only outro,helicam,rmi --expect-base 14c8d9dd --tag .before-chain2f1106 on the LIVE zip 14c8d9dd.
    # Installs over 14c8d9dd (NOT over 2e); inis unchanged (live pd2guns inis kept). Shots decide: heli drawn after lift-off, or not (then log the heli's room set 0x8df280).
    'lcchain2f1106d': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcchain_2f_14c8d9dd', tag='.before-chain2f1106',
                           files={'F01_Main.zip': '1d3252991c7e5261e02adea9881c1c07', 'F01_Main.bots.zip': 'db375c5a', 'F01_Main.bots.base.md5': '4dce350a'},
                           solo_secs=900, parts=('solo',), shots='400-556:4'),
    # the LIVE DM05A after the 2f install (11-06, owner's last test): nothing installed, live zip 1d325299 pinned, same ini tweaks and shots as lcchain2f1106d
    'lclive2f1106': dict(map='DM05A', slot='F01', entry=0, stage=None, tag=None, live={'F01_Main.zip': '1d325299'},
                         solo_secs=900, parts=('solo',), shots='400-556:4'),
    # 2h (11-08): heli arrival route (kl_arrival_1107.py stage --expect-base d65e8437) + Roof box 7 + club music boost (kl_lc_music_1107), on 6b's LIVE 1107r
    # DM05A d65e8437 (bots 72e4c5b5, base 388b40ec). Bench on the merged_1107 TEST dll (live SHIP 502677ee).
    'lcarr2h1108': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/arrival_1107/lcarr_2h_music_r', tag='.before-lcarr2hmusic1107',
                        files={'F01_Main.zip': '651a749259f54211c20eb67eff90ee65', 'F01_Main.bots.zip': 'ba98c0a6', 'F01_Main.bots.base.md5': '1d89ea85'},
                        hook=('C:/kl_build_1024/merged_1107/dll_test/dinput8.dll', '39e790110ccf917d007cdc28231618fb'),
                        solo_secs=900, parts=('solo',), shots='400-556:4'),
    # DM05A skyline (11-08, tools/kl_skyline_1108.py, stage C:/kl_build_1024/skyline_1108, pinned to the LIVE 2h DM05A 651a7492): Dead Men M05_A Buildings_MidRange as a static far
    # skyline EAST of the pad (T 60000,1884,-4000, held by Backdrop .rmi box 59 only = GUESS). Same run as lcarr2h1108 (the 2h heli comes from the east, the outro eye looks at it):
    # LOOK at the shots: is the skyline drawn behind the heli (box 59 alone)? does it hide the heli? lit / textured / right height? any hitch from the extra 33 .prm chunks?
    'skyline1108': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/skyline_1108', tag='.before-skyline1108',
                        files={'F01_Main.zip': 'cdd988728444fa618fd3f55ce524abdb', 'F01_Main.bots.zip': '464adc61', 'F01_Main.bots.base.md5': 'fdb74c80', 'KLGuns.ini': '33432bb9'},
                        hook=('C:/kl_build_1024/merged_1107/dll_test/dinput8.dll', '39e790110ccf917d007cdc28231618fb'),
                        solo_secs=900, parts=('solo',), shots='400-556:4'),
    # skyline look-east (11-08): skyline1108 PASS but its shots (escape box + outro) never faced east, so the draw stayed unproven. Same stage; no vehicle wait:
    # the player is teleported onto the pad and walks a few metres toward the skyline (60000,1884,-4000) so the chase camera looks at it, shots every 3 s.
    'skyeast1108': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/skyline_1108', tag='.before-skyline1108', look=(60000, -4000),
                        files={'F01_Main.zip': 'cdd988728444fa618fd3f55ce524abdb', 'F01_Main.bots.zip': '464adc61', 'F01_Main.bots.base.md5': 'fdb74c80', 'KLGuns.ini': '33432bb9'},
                        hook=('C:/kl_build_1024/merged_1107/dll_test/dinput8.dll', '39e790110ccf917d007cdc28231618fb'),
                        solo_secs=480, parts=('solo',), shots='60-240:3'),
    # skyline fog trial (11-08): skyeast1108 shots 12/20 face east from the pad into a cyan fog wall ~100 m out. Same walk on a copy of that stage
    # with the scene fog pushed out (tools/kl_skyfog_1108.py: CameraFar 30000 -> 80000, FogFull 0.95 -> 1.5, Begin 0.65 kept; GUESS fractions of Far).
    # LOOK: shots vs skyeast1108's (the control): more city visible? the far towers drawn? fps (frame log) vs the control. Bench only, never installed.
    # DM05A StreetGLOW trial (bench only): skyline_1108 with the StreetGLOW curtain's 85 vertex colours zeroed (tools/kl_streetglow_1108.py)
    'streetglow1108': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/streetglow_1108', tag='.before-streetglow1108', look=(60000, -4000),
                           files={'F01_Main.zip': '45bf2694', 'F01_Main.bots.zip': '8a473f98', 'F01_Main.bots.base.md5': '2a35c784', 'KLGuns.ini': '33432bb9'},
                           hook=('C:/kl_build_1024/merged_1108b/dll_test/dinput8.dll', '64701f02533659738f0672b5efa3b5e9'),
                           solo_secs=480, parts=('solo',), shots='60-240:3'),
    # DM05A city lights trial (bench only): glowfar_1108 with the dark 01d backdrop towers on their lit 01i material twin (tools/kl_citylights_1108.py)
    'citylights1108': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/citylights_1108', tag='.before-citylights1108', look=(60000, -4000),
                           files={'F01_Main.zip': '80b5547c', 'F01_Main.bots.zip': '1e02dbe5', 'F01_Main.bots.base.md5': 'c009e5af', 'KLGuns.ini': '33432bb9'},
                           hook=('C:/kl_build_1024/merged_1108b/dll_test/dinput8.dll', '64701f02533659738f0672b5efa3b5e9'),
                           solo_secs=480, parts=('solo',), shots='60-240:3'),
    # DM05A glow + far trial (bench only): skyfog_1108 (Far 80000, FogFull 1.5) with StreetGLOW vertex alpha x 0.25 (kl_streetglow_1108.py --alpha 0.25)
    # DM05A club music silent (11-08): kl_lc_music_fix_1108.py stage a (7 clean limiters always on) / b (settings f157+f158 = club_clean), bench only; no look step
    'lcmusica1108': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcmusic_a_1108', tag='.before-lcmusica1108',
                          files={'F01_Main.zip': '74a8c1f8', 'F01_Main.bots.zip': '3a7ac8d6', 'F01_Main.bots.base.md5': '9d15b6cf', 'KLGuns.ini': '33432bb9'},
                          hook=('C:/kl_build_1024/merged_1108b/dll_test/dinput8.dll', '64701f02533659738f0672b5efa3b5e9'),
                          solo_secs=480, parts=('solo',)),
    # DM05A heli DEPARTURE (11-08): Escaping key 0 = Incomming's hover end (kl_lc_depart_1108.py), 5 keys in place; bench only, no look step. VALIDATE ONLY until the owner says test.
    'lcdepart1108': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcdepart_1108', tag='.before-lcdepart1108',
                         files={'F01_Main.zip': 'fbaf450d', 'F01_Main.bots.zip': 'a04c54d7', 'F01_Main.bots.base.md5': '1859185b', 'KLGuns.ini': '33432bb9'},
                         hook=('C:/kl_build_1024/merged_1108b/dll_test/dinput8.dll', '64701f02533659738f0672b5efa3b5e9'),
                         solo_secs=480, parts=('solo',)),
    'lcmusicb1108': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lcmusic_b_1108', tag='.before-lcmusicb1108',
                          files={'F01_Main.zip': '530a2078', 'F01_Main.bots.zip': '7cf28cba', 'F01_Main.bots.base.md5': '02b17843', 'KLGuns.ini': '33432bb9'},
                          hook=('C:/kl_build_1024/merged_1108b/dll_test/dinput8.dll', '64701f02533659738f0672b5efa3b5e9'),
                          solo_secs=480, parts=('solo',)),
    'glowfar1108': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/glowfar_1108', tag='.before-glowfar1108', look=(60000, -4000),
                        files={'F01_Main.zip': 'cf7e32ff', 'F01_Main.bots.zip': '11f8a4eb', 'F01_Main.bots.base.md5': '7b302adc', 'KLGuns.ini': '33432bb9'},
                        hook=('C:/kl_build_1024/merged_1108b/dll_test/dinput8.dll', '64701f02533659738f0672b5efa3b5e9'),
                        solo_secs=480, parts=('solo',), shots='60-240:3'),
    # DM05A post-filter trial (bench only): skyline_1108 with all 20 PostFilterBoxes pointed at DD's neutral set 33189 (tools/kl_postneutral_1108.py)
    'postneutral1108': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/postneutral_1108', tag='.before-postneutral1108', look=(60000, -4000),
                            files={'F01_Main.zip': '5fce044f', 'F01_Main.bots.zip': '01119fdf', 'F01_Main.bots.base.md5': '32330624', 'KLGuns.ini': '33432bb9'},
                            hook=('C:/kl_build_1024/merged_1108b/dll_test/dinput8.dll', '64701f02533659738f0672b5efa3b5e9'),
                            solo_secs=480, parts=('solo',), shots='60-240:3'),
    'skyfog1108': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/skyfog_1108', tag='.before-skyfog1108', look=(60000, -4000),
                       files={'F01_Main.zip': '6686afe8', 'F01_Main.bots.zip': '708712b3', 'F01_Main.bots.base.md5': '9ae0f25b', 'KLGuns.ini': '33432bb9'},
                       hook=('C:/kl_build_1024/merged_1108b/dll_test/dinput8.dll', '64701f02533659738f0672b5efa3b5e9'),
                       solo_secs=480, parts=('solo',), shots='60-240:3'),
    # van empty-wait (11-08): owner 'flat raid vehicle ... always on fire but it doesnt pick you up'. The LIVE DD10 (nothing installed) on the
    # vanwait TEST dll (merged_1107 + [Echo] Probe code (0) + e184fd31 + review fix) with [VanBlow] ShieldWhileWaiting=1; nobody boards, the log decides.
    'vanwait1108': dict(map='DD10', slot='F07', entry=5, stage=None, tag=None, live={'F07_Main.zip': 'bc4d0bc3'}, van=True,
                        hook=('C:/kl-merge/kl-merge/klhook/out_vanwait1108b/dinput8.dll', '76bd4a9cfe325b750ab76546599c3518'),
                        ini=['[Bots]', 'LastVehicleLead=600', '[VanBlow]', 'ShieldWhileWaiting=1', 'Log=1'],
                        solo_secs=900, parts=('solo',), shots='300-840:30'),
    # DD10 van LANE (11-08, tools/kl_dd10_vanlane_1108.py, stage C:/kl_build_1024/dd10vanlane_1108, pinned to the LIVE DD10 bc4d0bc3): the escape van drove on z 1100 through
    # BigFence_A_02, both pillar pairs and the Exit_01 sign; lane z 1030 from x 7500 on, fence hidden (render only), stop + 5 nodes -70. Same script as vanwait1108 (nobody boards:
    # the van waits at state 4, drives out at 7); shots decide how the gate looks. VALIDATE ONLY until the owner says test.
    'dd10vanlane1108': dict(map='DD10', slot='F07', entry=5, stage='C:/kl_build_1024/dd10vanlane_1108', tag='.before-dd10vanlane1108', van=True,
                            files={'F07_Main.zip': '5d76d91a', 'F07_Main.bots.zip': '069f4402', 'F07_Main.bots.base.md5': '3dcfc1d3'},
                            hook=('C:/kl-merge/kl-merge/klhook/out_vanwait1108b/dinput8.dll', '76bd4a9cfe325b750ab76546599c3518'),
                            ini=['[Bots]', 'LastVehicleLead=600', '[VanBlow]', 'ShieldWhileWaiting=1', 'Log=1'],
                            solo_secs=900, parts=('solo',), shots='300-840:30'),
    # Retomoto van empty-wait (11-08): owner 'the vehicle on fire is the same occurance for retomoto tower'. The LIVE DM09 (nothing installed; slot F06, page 2 entry 4
    # = kl_arc2_kit's verified place) on the TEST twin of the live SHIP dll, [VanBlow] ShieldWhileWaiting=1 as live; nobody boards, the log decides (as vanwait1108).
    'vanwait09_1108': dict(map='DM09', slot='F06', page=2, entry=4, stage=None, tag=None, live={'F06_Main.zip': 'afee8967'}, van=True,
                           hook=('C:/kl-merge/kl-merge/klhook/out_vanwait1108b/dinput8.dll', '76bd4a9cfe325b750ab76546599c3518'),
                           ini=['[Bots]', 'LastVehicleLead=600', '[VanBlow]', 'ShieldWhileWaiting=1', 'Log=1'],
                           solo_secs=1100, parts=('solo',), shots='300-1040:30'),
    # vanwait09_1108 PASS (05:04) but the van ARRIVED at 1245 of 3000 (41 %): the cops hit it in the drive-in (state 2), before ShieldWhileWaiting
    # starts at 3/4, and the shield then froze it at 41 % (= burning). Same run + [VanBlow] HealFloor=95 (in the live dll since merged_1107, never run):
    # at the first empty pass of the wait the health goes back to max (+0x14 write, GUESS), then the shield holds it. vanlook: the seat is teleported
    # (TEST rig) 13 m in front of the boarding box (-1852, 121, 10459) at state 3 so the shots show whether the fire goes out with the health.
    'vanwait09h_1108': dict(map='DM09', slot='F06', page=2, entry=4, stage=None, tag=None, live={'F06_Main.zip': 'afee8967'}, van=True,
                            vanlook=(-1852, 200, 9159),
                            # TEST 988a279b = be08398f (ShieldDriveIn): the drive-in shield keeps the van whole, HealFloor=95 mends what still gets through
                            hook=('C:/kl-merge/kl-merge/klhook/out_drivein1108/dinput8.dll', '988a279ba3eababaf2cb832cee3c9409'),
                            ini=['[Bots]', 'LastVehicleLead=600', '[VanBlow]', 'ShieldWhileWaiting=1', 'ShieldDriveIn=1', 'HealFloor=95', 'Log=1'],
                            solo_secs=1100, parts=('solo',), shots='330-500:3'),
    # f0's merged_1108b kit (6f3df179): gen AFTER 'install.py --test' so KLHook_base.ini is the installed 6ddd03de with its own
    # '[VanBlow] ShieldDriveIn=1' line; this kit adds no ShieldDriveIn / HealFloor of its own, so the shipped line is what is tested
    'vanwait09m_1108': dict(map='DM09', slot='F06', page=2, entry=4, stage=None, tag=None, live={'F06_Main.zip': 'afee8967'}, van=True,
                            vanlook=(-1852, 200, 9159),
                            hook=('C:/kl_build_1024/merged_1108b/dll_test/dinput8.dll', '64701f02533659738f0672b5efa3b5e9'),
                            ini=['[Bots]', 'LastVehicleLead=600', '[VanBlow]', 'Log=1'],
                            solo_secs=1100, parts=('solo',), shots='330-500:3'),
    # DM06B traffic cars (11-08, tools/kl_dm06b_traffic_1108.py, stage C:/kl_build_1024/dm06b_traffic_1108, pinned to the LIVE DM06B a6c0aef1): 7 static TRAFFIC! cars on the
    # ramp road (Curvedroad waypoints 9..21). Offline Arcade, 1 seat on the merged_1107 TEST dll; the script teleports (TEST rig) 700 upstream of each car and faces it, shots
    # every 5 s. LOOK at the shots: cars drawn? (skinned models as static ZLNKOBJ = the open question), headlight glows rebuilt as Standard (GUESS), car heading/height.
    'dm06btraffic1108': dict(map='DM06B', slot='F02', entry=1, stage='C:/kl_build_1024/dm06b_traffic_1108', tag='.before-dm06btraffic1108', cars=True,
                             files={'F02_Main.zip': '7cee043dda5d62eeb6c48329b40fcda8', 'F02_Main.bots.zip': 'ec42c5e4', 'F02_Main.bots.base.md5': '171f7443', 'KLGuns.ini': '483f7450'},
                             hook=('C:/kl_build_1024/merged_1107/dll_test/dinput8.dll', '39e790110ccf917d007cdc28231618fb'),
                             solo_secs=600, parts=('solo',), shots='60-200:3'),
}
LC = ('lc1106', 'lcglass1106', 'lclive1106', 'lcdoors1106', 'lcspawn2f1106', 'lcoutro1106', 'lcoutcam1106', 'lcoutcam2a1106', 'lcoutcam2b1106', 'lcchain2a1106', 'lcchain2a1106s', 'lcchain2a1106b', 'lcchain2a1106d',
      'lcchain2a1106n', 'lcchain2c1106d', 'lcchain2d1106d', 'lcchain2e1106d', 'lcchain2f1106d', 'lclive2f1106', 'lcarr2h1108', 'skyline1108')
EYE_OF = {'lcchain2e1106d': (7400, 2500, 2800), 'lcchain2f1106d': (7400, 2500, 2800), 'lclive2f1106': (7400, 2500, 2800), 'lcarr2h1108': (7400, 2500, 2800), 'skyline1108': (7400, 2500, 2800)}          # kits whose outro eye is not the 2c CamPos01 eye (7093,2181,2727)
FASTBOARD = ('lcchain2a1106b', 'lcchain2a1106d', 'lcchain2a1106n', 'lcchain2c1106d', 'lcchain2d1106d', 'lcchain2e1106d', 'lcchain2f1106d', 'lcarr2h1108', 'skyline1108')          # boards at once at state 3
LEAD60 = ('lcchain2a1106b', 'lcchain2a1106d', 'lcchain2c1106d', 'lcchain2d1106d', 'lcchain2e1106d', 'lcchain2f1106d', 'lcarr2h1108', 'skyline1108')          # + LastVehicleLead=600 in solo.ini (the clock call 60 s before the end)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def mapdir(k):
    return '%s/KLExpansion/Maps/%s' % (DD, KITS[k]['map'])


def snap(d):
    return {n: md5(os.path.join(d, n)) for n in sorted(os.listdir(d)) if os.path.isfile(os.path.join(d, n))}


def read_secs(path):
    secs, cur = [], None
    for ln in open(path, encoding='latin-1').read().splitlines():
        m = re.match(r'\s*\[([^\]]+)\]\s*$', ln)
        if m:
            cur = (m.group(1), []); secs.append(cur)
        elif cur is not None and '=' in ln and not ln.lstrip().startswith(';'):
            k, _, v = ln.partition('=')
            cur[1].append((k.strip(), v))
    return secs


def script_of(path):
    return [v for s, kv in read_secs(path) if s == 'Script' for k, v in kv]


# ---------------------------------------------------------------- generation
def solo_script(k, secs_total):
    c = KITS[k]
    s = ['waitwin CampaignMenu 180000', 'settle 15 150 60000', 'tapuntil ESCAPE MainMenu 10000 3', 'settle 8 150 30000', 'wait 1500', 'tap DOWN', 'wait 1200',
         'tapuntil RETURN HeistModeMenu 15000 2', 'settle 8 150 30000', 'wait 3000', 'windows']
    pg = c.get('page', 3)          # page 2 = 6 x DOWN on HeistModeMenu, page 3 = 7 x DOWN (kl_arc2_kit.py, verified live_1026 smoke inis)
    for _ in range({2: 6, 3: 7}[pg]):
        s += ['tap DOWN', 'wait 500']
    s += ['wait 2500', 'windows', 'tap RETURN', 'waitwin HeistPlayMenu%d 8000' % pg, 'wait 3000', 'windows',
          'sel HeistLevel_P%d 0xceceec %d' % (pg, c['entry']), 'wait 2500', 'expect 0xceceec %d' % c['entry'],
          'log BENCH1106 %s entry %d page %d slot %s' % (c['map'], c['entry'], pg, c['slot']), 'msg HeistLevel_P%d StartGame' % pg, 'waitload 300000',
          'log BENCH1106 level loaded: %s' % c['map'], 'wait 23000', 'peek 0x168e598+0x70 session-state-must-be-0x19', 'pos spawn']
    if k in LC:
        # Escape: the vehicle state machine is open-loop timers (re/lastcall_heli_1105.md). Wait for state 3 (van/chopper at the pad),
        # board by teleporting into the box (GUESS: the coordinates are the box from the doc, 7361/2014/3201; 'tele' is TEST-rig only),
        # then wait for the round-over panel (0x1f) and the shop (0x20). Every wait goes on at its timeout so a dead chain still ends.
        if k in FASTBOARD:
            # fast boarding: state 3 also matches 4; the player goes into the box at once and holds E (a human boards by HOLDING E, 2-5 s)
            s += ['wait 30000', 'pos at-60s', 'log BENCH1106 waiting for vehicle state 3', 'waitvan 3 600000', 'pos van3',
                  # c9: keep the +x walk-in that boarded in lclive/lcspawn2f/lcoutro (facing GUESS as below), only the long waits go
                  'tele 7361 2014 3201', 'log BENCH1106 teleported into the escape box', 'wait 1000',
                  'goto 7561 3201 60 8000', 'goto 7361 3201 60 8000', 'pos in-box', 'tap E 3500', 'wait 500', 'tap E 3500', 'wait 500', 'tap E 4000', 'pos boarded',
                  'waitvan 5 120000', 'pos van5',
                  'wait 8000', 'pos after5', 'waitstate 0x1f 240000', 'pos s1f', 'wait 12000', 'waitstate 0x20 120000', 'log BENCH1106 LC solo done', 'wait 3000', 'pass 1000']
            return s
        s += ['wait 30000', 'pos at-60s', 'log BENCH1106 waiting for vehicle state 3', 'waitvan 3 600000', 'pos van3', 'wait 5000',
              'tele 7361 2014 3201', 'log BENCH1106 teleported into the escape box', 'wait 3000', 'pos teleported',
              # run lc1106 (11-06 02:43): the player stood in BoardingTrigger_Heli (centre 7361/2014/3201, half extents 400x200x300, so y 1814..2214;
              # floor 1881) but never went aboard: a human boards only through PlayerAction 'EnterVehicle', i.e. HOLDING E there
              # (re/human_escape_online_1028.md, live hold 2-5 s); the bench never pressed it. Walk from +x first: facing is a GUESS (eIntDir_CtrlDir)
              'goto 7561 3201 60 8000', 'goto 7361 3201 60 8000', 'wait 1000', 'pos in-box',
              'tap E 3000', 'wait 1000', 'pos try1', 'tap E 3000', 'wait 1000', 'pos try2', 'tap E 4000', 'wait 1000', 'pos boarded',
              'waitvan 5 120000', 'pos van5',
              'wait 8000', 'pos after5', 'waitstate 0x1f 240000', 'pos s1f', 'wait 12000', 'waitstate 0x20 120000', 'log BENCH1106 LC solo done', 'wait 3000', 'pass 1000']
    elif c.get('cars'):
        # one station per car: 1200 upstream (against the spline heading) and 150 up (the road climbs ~0.06/unit upstream, +40 could land under it), then
        # WALK toward the car (goto holds W: 'face' does not turn a standing player, klauto.c) and stop 1000 short (500 hid the car behind the body, 11-08 shots); 'tele' is TEST-rig only, the guard may refuse (the log says)
        import json
        rep = json.load(open('%s/build_report.json' % c['stage']))['reports']['F02_Main.zip']
        s += ['wait 8000', 'pos before-cars']
        for i, (sp, hd) in enumerate(zip(rep['spots'], rep['headings'])):
            (x, y, z), n = sp[0], math.hypot(hd[0], hd[1]) or 1.0
            ux, uz = x - 1200 * hd[0] / n, z - 1200 * hd[1] / n
            s += ['tele %d %d %d' % (ux, y + 150, uz), 'wait 1500', 'goto %d %d 1000 5000' % (x, z), 'log BENCH1106 car %d station' % (i + 1), 'wait 9000', 'pos car-%d' % (i + 1)]
        s += ['log BENCH1106 cars done', 'pass 1000']
    elif c.get('look'):
        # stand on the pad (the escape box, 7361/2014/3201) and walk toward the look point in short legs: goto holds W, so the chase camera ends up
        # facing it; legs of 150 / 300 stay on the pad (box half extent 400 in x)
        (lx, lz), (bx, bz) = c['look'], (7361, 3201)
        n = math.hypot(lx - bx, lz - bz)
        s += ['wait 5000', 'tele %d 2014 %d' % (bx, bz), 'wait 2000', 'log BENCH1106 on the pad']
        for d in (150, 300):
            s += ['goto %d %d 40 4000' % (bx + d * (lx - bx) / n, bz + d * (lz - bz) / n), 'log BENCH1106 facing look point (%d)' % d, 'wait 12000', 'pos look-%d' % d]
        s += ['wait 30000', 'pos look-end', 'log BENCH1106 look done', 'pass 1000']
    elif c.get('van'):
        # empty-wait van (11-08, [VanBlow] ShieldWhileWaiting): nobody boards; the seat stands at spawn while the van waits at the pickup.
        # The log then shows whether the van was shielded ('vanblow: ShieldWhileWaiting', 'follow: shield') and whether it reached 6 (destroyed).
        s += ['wait 30000', 'pos at-60s', 'log BENCH1106 waiting for vehicle state 3', 'waitvan 3 600000', 'pos van3']
        if c.get('vanlook'):           # vanwait09_1108 had the seat in the tower: no shot showed the van. TEST rig tele to a point facing the doors
            s += ['tele %d %d %d' % c['vanlook'], 'wait 1500', 'log BENCH1106 at the van look point', 'pos vanlook']
        for i in range(1, 9):
            s += ['wait 15000', 'pos wait-%ds' % (15 * i)]
        s += ['log BENCH1106 van empty-wait done', 'pass 1000']
    else:
        for i in range(1, 11):
            s += ['wait 30000', 'pos at-%ds' % (60 + 30 * i)]
            if i % 3 == 0:
                s.append('windows')
        s += ['log BENCH1106 DD10 solo done', 'pass 1000']
    return s


AUTO = ['[Auto]', 'Enable=1', 'Hooks=0', 'Nodes=0', 'EndHooks=1', 'CmdDrop=DefaultScene,AutoExit', 'CmdAdd=-o DisableSplashScreens -o AutoExit={x}',
        'StallMs=300000', 'MaxRunMs={m}', 'LoadedMs=0', 'Unfocused=1', 'BlockReal=1', 'FirstChance=1', 'PosLogMs=5000']


def probes(k):
    t = ['[Memory]', 'Log=1']
    if k in LC:
        # lclive1106 (11-06 10:52): 0 KLShot files, d3count 0 frames: ReShade owns Present here, so shots go through its bridge (as MT3B 11-02)
        t = ['[Heli]', 'Probe=2', '[Camera]', 'Log=1', '[Memory]', 'Log=1', 'D3dShotPost=1', '[ReShade]', 'Bridge=1']
    elif KITS[k].get('cars') or KITS[k].get('van') or KITS[k].get('look'):
        # dm06btraffic1108 / vanwait1108 (11-08): 0 KLShot files, these kits had no ReShade bridge lines (only LC kits did)
        t = ['[Memory]', 'Log=1', 'D3dShotPost=1', '[ReShade]', 'Bridge=1']
    return t


def long_match(lines, extra_rounds):
    """Insert extra 'shop -> next round' blocks before the pass line of a Q32 script (rounds 3, 4 ...)."""
    i = max(j for j, l in enumerate(lines) if l.startswith('pass '))
    add = []
    for r in range(3, 3 + extra_rounds):
        add += ['log BENCH1106 shop before round %d' % r, 'waitstate 0x20 600000', 'waitstate 0x19 240000', 'log BENCH1106 ROUND %d running' % r, 'wait 30000', 'pos host-r%d' % r]
    return lines[:i] + add + lines[i:]


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='latin-1', newline='\n') as f:
        f.write(text)


def renumber(lines):
    out, n = [], 0
    for l in lines:
        if l.startswith(';'):
            out.append(l)
        else:
            n += 1; out.append('%d=%s' % (n, l))
    return out


def pair(k, who, long_rounds):
    """Q32 host/join file with the kit's probes added and, for the long match, extra rounds in the script (both seats)."""
    q = '%s/Q32_%s_%s.ini' % (Q32, KITS[k]['map'], who)
    secs = read_secs(q)
    scr = script_of(q)
    if long_rounds:
        scr = long_match(scr, long_rounds)
    # keep every non-Script section, drop [Auto] (rewritten for the longer run), keep order
    secs_t = ['; bench_1106 %s %s: Q32 pair (round 1 -> shop -> round 2%s) + probes' % (k, who, (' -> %d more' % long_rounds) if long_rounds else '')]
    total = 2400 if long_rounds else 1950
    for name, kv in secs:
        if name == 'Script':
            continue
        if name == 'Auto':
            kv = [(a, b) for a, b in kv if a not in ('CmdAdd', 'MaxRunMs')] + [('CmdAdd', '-o DisableSplashScreens -o AutoExit=%d' % total), ('MaxRunMs', str((total - 10) * 1000))]
        secs_t.append('[%s]' % name); secs_t += ['%s=%s' % kv_ for kv_ in kv]
    secs_t += probes(k)
    secs_t += ['[Script]'] + renumber(scr)
    return '\n'.join(secs_t) + '\n'


def gen(which='all'):
    import shutil
    os.makedirs(KIT, exist_ok=True)
    live = '%s/KLHook.ini' % DD
    for k, c in KITS.items():
        if which != 'all' and k != which:
            continue
        d = '%s/%s' % (KIT, k)
        os.makedirs('%s/hook_test' % d, exist_ok=True)
        shutil.copy2(c.get('hook', (HOOK_SRC,))[0], '%s/hook_test/dinput8.dll' % d)
        shutil.copy2(live, '%s/KLHook_base.ini' % d)       # snapshot of the live ini (cover lines etc.); a later live edit does not change a kit
        shutil.copy2('%s/KLShopPage.ini' % DD, '%s/KLShopPage.ini' % d)
        t = ['; bench_1106 %s solo: OFFLINE Arcade, 1 seat, %s slot %s page 3 entry %d' % (k, c['map'], c['slot'], c['entry']),
             '; the seat stands still; cops hurt it 0.001 x so its death does not end the round (as ARC1)',
             '[Balance]', 'CopToYou=0.001', 'PointBlankToYou=0.0'] + probes(k)
        n = c['solo_secs']
        if k in LEAD60:
            t += ['[Bots]', 'LastVehicleLead=600']
        t += c.get('ini', [])
        t += [l.replace('{x}', str(n - 60)).replace('{m}', str((n - 70) * 1000)) for l in AUTO]
        t += ['[Script]'] + renumber(solo_script(k, n))
        write('%s/solo.ini' % d, '\n'.join(t) + '\n')
        lr = 2 if k == 'dd10s1106' else 0
        write('%s/online_host.ini' % d, pair(k, 'host', lr))
        write('%s/online_join.ini' % d, pair(k, 'join', lr))
    print('gen: kits written under', KIT)


# ---------------------------------------------------------------- validate
class V:
    def __init__(s):
        s.fail = 0

    def ok(s, cond, text, warn=False):
        tag = 'PASS' if cond else ('WARN' if warn else 'FAIL')
        if not cond and not warn:
            s.fail += 1
        print('  %-4s %s' % (tag, text))
        return cond


def validate(which):
    v = V()
    print('validate (dry run: no game launch, no write into the game folder)')
    v.ok(os.path.isdir(DD), 'Dog Days folder %s' % DD)
    v.ok(os.path.isfile('%s/kl2.exe' % DD), 'kl2.exe present')
    tl = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe'], capture_output=True, text=True).stdout
    v.ok('kl2.exe' not in tl, 'no kl2.exe is running (a run would refuse otherwise)', warn=True)
    v.ok(os.path.isfile(os.path.join(ROOT, 'tools/kl_solo_test.py')), 'tools/kl_solo_test.py')
    v.ok(os.path.isdir(SOLO), 'solo work folder %s' % SOLO)
    for k in (list(KITS) if which == 'all' else [which]):
        c, d = KITS[k], '%s/%s' % (KIT, k)
        print('[%s]' % k)
        dll = '%s/hook_test/dinput8.dll' % d
        if v.ok(os.path.isfile(dll), 'bench dll %s' % dll):
            data = open(dll, 'rb').read()
            want = c.get('hook', (HOOK_SRC, HOOK_MD5))[1]
            v.ok(hashlib.md5(data).hexdigest() == want, 'dll md5 %s = TEST twin %s' % (hashlib.md5(data).hexdigest()[:8], want[:8]))
            v.ok(data.count(b'(TEST)') >= 3 and b"klauto's scripted keys" in data, 'dll carries the TEST markers ((TEST) x%d, klauto strings = build_auto.bat build; SHIP has 1)' % data.count(b'(TEST)'))
            v.ok(2_500_000 < len(data) < 3_000_000, 'dll size %.2f MB (TEST builds: 2.59 MB in 1106, 2.71 MB for merged_1107)' % (len(data) / 1e6))
        live_dll = '%s/dinput8.dll' % DD
        if os.path.isfile(live_dll):
            v.ok(b"klauto's scripted keys" not in open(live_dll, 'rb').read(), 'live dll is the SHIP build, no klauto (md5 %s; kl_solo_test swaps the TEST dll in and back)' % md5(live_dll)[:8], warn=True)
        base = '%s/KLHook_base.ini' % d
        if v.ok(os.path.isfile(base), 'base ini snapshot'):
            txt = open(base, encoding='latin-1').read()
            for key in COVER:
                v.ok(re.search(r'^%s=' % key, txt, re.M) is not None, 'base ini has cover line %s' % key)
            for sec in ('Expansion', 'Memory', 'Heli', 'Camera', 'Lobby'):
                v.ok('[%s]' % sec in txt, 'base ini has [%s]' % sec, warn=sec in ('Heli', 'Camera'))
            if c['slot'] not in (re.search(r'^ClientBuildMaps=([^\s;]*)', txt, re.M) or [0, ''])[1].split(','):
                v.ok(False, 'ClientBuildMaps does not list %s (kits copy the live cover lines; ONLINE client build for that slot is whatever the live ini says)' % c['slot'], warn=True)
        v.ok(os.path.isfile('%s/KLShopPage.ini' % d), 'KLShopPage.ini copy (staged into solo/<TAG>/inst1+2 by run)')
        for f in ('solo.ini', 'online_host.ini', 'online_join.ini'):
            p = '%s/%s' % (d, f)
            if v.ok(os.path.isfile(p), 'kit file %s' % f):
                scr = script_of(p)
                bad = sorted({l.split()[0] for l in scr if l.split() and l.split()[0] not in OPS})
                v.ok(not bad and len(scr) > 20, '%s: %d script lines, ops known%s' % (f, len(scr), (' (UNKNOWN: %s)' % bad) if bad else ''))
                v.ok(sum(1 for l in re.findall(r'^\[Script\]', open(p, encoding='latin-1').read(), re.M)) == 1, '%s: exactly one [Script] section' % f)
                v.ok(any(l.startswith('pass') for l in scr), '%s: ends with pass' % f)
        st = c['stage']
        if st is None:
            for n, want in c['live'].items():
                p = '%s/%s' % (mapdir(k), n)
                v.ok(os.path.isfile(p) and md5(p).startswith(want), 'live %s md5 %s = pin %s (nothing is installed)' % (n, md5(p)[:8] if os.path.isfile(p) else '-', want))
            for part in c['parts']:
                print('  command: python tools/kl_bench_1106.py run %s %s' % (k, part))
            continue
        inst = '%s/install.py' % st
        v.ok(os.path.isfile(inst), 'stage install.py (md5 %s)' % (md5(inst)[:8] if os.path.isfile(inst) else '-'))
        for n, want in c['files'].items():
            p = '%s/%s' % (st, n)
            if v.ok(os.path.isfile(p), 'staged %s' % n):
                v.ok(md5(p).startswith(want[:8]), 'staged %s md5 %s = %s' % (n, md5(p)[:8], want[:8]))
        md = mapdir(k)
        if v.ok(os.path.isdir(md), 'live map folder %s' % md):
            haveb = [n for n in os.listdir(md) if n.endswith(c['tag'])]
            v.ok(not haveb, 'no %s backups present (install refuses otherwise)%s' % (c['tag'], (': ' + ', '.join(haveb)) if haveb else ''))
            v.ok(True, 'live md5s now: ' + ', '.join('%s=%s' % (n, m[:8]) for n, m in snap(md).items() if '.before-' not in n and n.startswith(c['slot'] + '_Main.') and n.split('.')[-1] in ('zip', 'WAV', 'WHD', 'SND', 'md5')))
        if os.path.isfile(inst):
            r = subprocess.run([sys.executable, inst, '--dry', '--game', DD] if k == 'dd10s1106' else [sys.executable, inst, '--dry'], capture_output=True, text=True)
            v.ok(r.returncode == 0, 'install.py --dry exit %d: %s' % (r.returncode, (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or [''])[-1][:140]))
        for part in c['parts']:
            print('  command: python tools/kl_bench_1106.py run %s %s' % (k, part))
    print('RESULT: validate %s - %d FAIL' % ('OK' if not v.fail else 'FAILED', v.fail))
    return 1 if v.fail else 0


# ---------------------------------------------------------------- verify
def logs(tag):
    out = {}
    for n in (1, 2):
        p = '%s/%s/inst%d/KLHook.log' % (SOLO, tag, n)
        if os.path.isfile(p):
            out[n] = open(p, encoding='latin-1', errors='replace').read().splitlines()
    return out


def faults(lines):
    """Case-sensitive on purpose: 'EndOnFatal=1' / 'ContinueAsserts' lines are settings, not faults."""
    pat = re.compile(r'(EXCEPTION|FATAL|CRASH|ACCESS_VIOLATION)|access violation|memory fault|c0000005', re.I if False else 0)
    return [l for l in lines if pat.search(l)]


def dumps(tag, n):
    d = '%s/%s/inst%d' % (SOLO, tag, n)
    return [f for f in os.listdir(d) if f.lower().endswith(('.dmp', '.mdmp'))] if os.path.isdir(d) else []


def nums(l):
    return [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', l)]


def near(p, q, r):
    return sum((a - b) ** 2 for a, b in zip(p, q)) ** 0.5 <= r


def verify(k, part, tagbase=None):
    tag = '%s_%s' % (k, part)
    L = logs(tag)
    res = []
    if not L:
        print('RESULT: %s no logs under %s/%s' % (tag, SOLO, tag)); return 1

    def chk(name, cond, detail=''):
        res.append(cond); print('  %s %s %s' % ('PASS' if cond else 'FAIL', name, detail))
    print('verify %s' % tag)
    for n, lines in L.items():
        f = faults(lines)
        dm = dumps(tag, n)
        chk('inst%d no fault lines / dump files' % n, not f and not dm, ('first: ' + (f[0][:160] if f else dm[0])) if (f or dm) else '(%d log lines, 0 dumps)' % len(lines))
    if part == 'solo':
        a = L[1]
        # the census line ("botfill: round census") is logged only in an online FA round (klbotfill.c klbf_tick gate):
        # the 130 check lives in the online branch
        hel = []
        for l in a:
            m = re.search(r'heli: t=.*zheli=(\w+) vt=\w+ pos=\S*\((-?\d+), (-?\d+), (-?\d+)\)', l)
            if m and m.group(1) != '00000000':
                hel.append((l[:12], tuple(float(m.group(i)) for i in (2, 3, 4))))
        pad = (7300, 2249, 3500)
        if k in LC:
            if hel:
                d0 = sum((x - y) ** 2 for x, y in zip(hel[0][1], pad)) ** .5
                d1 = min(sum((x - y) ** 2 for x, y in zip(h[1], pad)) ** .5 for h in hel)
                chk('ZHeli moves toward (7300,2249,3500)', d1 < d0 * 0.5, 'first %s %.0f m away, closest %.0f m (%d samples; stock hang was 15394,6942,18351)' % (hel[0][0], d0, d1, len(hel)))
            else:
                chk('ZHeli moves toward (7300,2249,3500)', False, 'no "heli: t=" line with a ZHeli (is [Heli] Probe=2 in the run ini?)')
            eye = EYE_OF.get(k, (7093, 2181, 2727))
            # klcam.c logs the render camera as "cam: ... eye X Y Z"; only the outro (after 0x19 -> 0x1f) counts
            i0 = next((i for i, l in enumerate(a) if re.search(r'session: state \S+ -> 0x1f', l)), len(a))
            eyes = [tuple(float(m.group(j)) for j in (1, 2, 3)) for l in a[i0:] if ' cam:' in l for m in [re.search(r'\beye (-?[\d.]+) (-?[\d.]+) (-?[\d.]+)', l)] if m]
            hit = [e for e in eyes if near(e, eye, 150)]
            if k in ('lcoutcam1106', 'lcoutcam2a1106', 'lcoutcam2b1106', 'lcchain2a1106', 'lcchain2a1106s', 'lcchain2a1106b', 'lcchain2a1106d', 'lcchain2a1106n'):
                # these stages move the eye on purpose (LookAtPos, f5/f6 offset from the heli): info only, the frames are judged by eye
                chk('escape camera eye moved off (7093,2181,2727) (info)', True, '%d outro cam eyes, last %s' % (len(eyes), ('(%.0f,%.0f,%.0f)' % eyes[-1]) if eyes else 'none'))
            else:   # includes lcchain2c1106d / lcchain2d1106d: the eye is FIXED at CamPos01 (2d: the box node itself), so it is still checked
              chk('escape camera eye about (%d,%d,%d) in the outro' % eye, bool(hit), '%d outro cam eyes, %s' % (len(eyes), ('e.g. (%.0f,%.0f,%.0f)' % hit[0]) if hit else ('last (%.0f,%.0f,%.0f)' % eyes[-1]) if eyes else 'none'))
        st = [m.group(1) for l in a for m in [re.search(r'session: state \S+ -> (0x[0-9a-f]+)', l)] if m]
        if not KITS[k].get('cars'):
          chk('session reaches 0x1f then 0x20', '0x1f' in st and '0x20' in st[st.index('0x1f'):] if '0x1f' in st else False, 'states seen: %s' % ' '.join(st[-8:]))
        van = [l[:140] for l in a if 'van card' in l or 'vehicle state' in l]
        print('  info vehicle lines: %d, last: %s' % (len(van), van[-1] if van else '-'))
        if k in LC:
            print('  info grey screen: LOOK at the shots (KLShot_inst1_NN.jpg in %s/%s); event times below' % (SOLO, tag))
            ev = [l[:12] + ' ' + l[13:100] for l in a if re.search(r'session: state \S+ -> 0x(1f|20)|BENCH1106|hud: van card.*state (3|5)', l)]
            for e in ev[:40]:
                print('       ', e)
            import glob
            for s in sorted(glob.glob('%s/%s/KLShot_inst1_*.jpg' % (SOLO, tag)))[:90]:
                print('        shot %s %s' % (time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(s))), os.path.basename(s)))
            # civilian speech is the engine's own sound-bank playback: the hook logs none, so no log check is possible
            print('  info women / civilian voices: not logged by the hook; LOOK at the shots and listen')
            sq = [l for l in a if re.search(r'squad|spawn', l, re.I)]
            print('  info squad/spawn lines: %d (first: %s)' % (len(sq), sq[0][:140] if sq else '-'))
    if k == 'dd10s1106':
        a = L[1]
        mem = [(m.group(1), float(m.group(2))) for l in a for m in [re.search(r'(\S+) memory: every 10 s: .*largest piece ([\d.]+) MB', l)] if m]
        if mem:
            lo = min(x[1] for x in mem)
            chk('largest free block stays above the ~14.4 MB baseline', lo > 14.4, 'min %.1f MB, last %.1f MB, %d samples' % (lo, mem[-1][1], len(mem)))
        else:
            chk('largest free block logged', False, 'no "memory: every 10 s" lines ([Memory] Log=1)')
        sn = [l[:150] for l in a if re.search(r'wav|whd|sound bank|SND', l, re.I) and re.search(r'fail|bad|error|missing|refus', l, re.I)]
        chk('no sound/WAV load error lines', not sn, sn[0] if sn else '(audio itself: owner ear check, the bench is silent by design)')
    if part in ('online', 'long'):
        for n, lines in L.items():
            st = [m.group(1) for l in lines for m in [re.search(r'session: state \S+ -> (0x[0-9a-f]+)', l)] if m]
            # a round ends 0x19 -> 0x1f; after the match's last round 0x1f goes to 0x28 (match over), not to the shop 0x20
            want = 3 if part == 'long' else 2
            ends = sum(1 for i in range(1, len(st)) if st[i] == '0x1f' and st[i - 1] == '0x19')
            # the online script ends ~30 s into the last round (lcglass1106 11-06: round 2 entered, never ended), so the gate is
            # "round N entered" (N entries into 0x19) plus N-1 completed round ends; a full last round is the long part's job
            ins = st.count('0x19')
            chk('inst%d reaches round %d (%d+ entries into 0x19, %d+ round ends)' % (n, want, want, want - 1), ins >= want and ends >= want - 1,
                'entries %d, round ends %d, shops %d, match over %s' % (ins, ends, st.count('0x20'), '0x28' in st))
        for n, lines in L.items():
            # round reset dwell: the stripped HavokShatterGlassConnectivity made 0x25 last 21-29 s per seat on DM05A (DD maps ~0.01 s)
            ts = [(l[:12], m.group(1), m.group(2)) for l in lines for m in [re.search(r'session: state (0x[0-9a-f]+) -> (0x[0-9a-f]+)', l)] if m]
            sec = lambda t: int(t[0:2]) * 3600 + int(t[3:5]) * 60 + float(t[6:12])
            dw = [sec(ts[i + 1][0]) - sec(ts[i][0]) for i in range(len(ts) - 1) if ts[i][2] == '0x25' and ts[i + 1][1] == '0x25']
            chk('inst%d round reset 0x25 under 8 s' % n, bool(dw) and max(dw) < 8, '0x25 dwell s: %s' % (', '.join('%.1f' % x for x in dw) or 'never reached'))
        if k in LC:
            rx = re.compile(r'botfill: round census: (\d+) ZFFActor')
            for n, lines in L.items():
                c = sorted({int(m.group(1)) for l in lines for m in [rx.search(l)] if m})
                chk('inst%d loads with census 130 (previously 116)' % n, 130 in c, 'census lines: %s' % (c or 'none'))
        a = L[1]
        bg = [l[:150] for l in a if 'botgate' in l and ('bots' in l)]
        chk('botgate decided for the slot', bool(bg), bg[-1] if bg else 'no botgate line')
        if k == 'dd10s1106':
            mem = [float(m.group(1)) for n_ in L.values() for l in n_ for m in [re.search(r'memory: every 10 s: .*largest piece ([\d.]+) MB', l)] if m]
            if mem:
                chk('largest free block stays above 14.4 MB over the long match', min(mem) > 14.4, 'min %.1f MB over %d samples (both seats)' % (min(mem), len(mem)))
    bad = res.count(False)
    print('RESULT: %s %s (%d checks, %d FAIL)' % (tag, 'PASS' if not bad else 'FAIL', len(res), bad))
    return 1 if bad else 0


# ---------------------------------------------------------------- run
def sh(cmd, **kw):
    print('  $ ' + ' '.join('"%s"' % c if ' ' in c else c for c in cmd), flush=True)
    return subprocess.run(cmd, **kw).returncode


def kl2_procs():
    """[(pid, working set KB)] for every kl2.exe, from tasklist's CSV."""
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe', '/FO', 'CSV', '/NH'], capture_output=True, text=True).stdout
    r = []
    for l in out.splitlines():
        f = [x.strip('"') for x in l.split('","')]
        if len(f) >= 5 and f[0].lower() == 'kl2.exe':
            r.append((int(f[1]), int(re.sub(r'\D', '', f[4]) or 0)))
    return r


def run(k, part):
    c = KITS[k]
    if validate(k):
        print('RESULT: not started - validate failed'); return 1
    parts = c['parts'] if part == 'all' else (part,)
    for p in parts:
        if p not in c['parts']:
            print('RESULT: not started - %s has parts %s' % (k, c['parts'])); return 1
    d, md, before = '%s/%s' % (KIT, k), mapdir(k), None
    before = snap(md)
    inst = [sys.executable, '%s/install.py' % c['stage']] + (['--game', DD] if k == 'dd10s1106' else []) if c['stage'] else None
    z = kl2_procs()
    if any(kb >= 1024 for _, kb in z):
        print('RESULT: not started - a live kl2.exe is running: %s' % z); return 1
    if z:
        # unkillable kl2.exe left at ~44 K (Access denied to Stop-Process) hold no game: install.py's own tasklist check
        # would refuse forever, so skip it only when every kl2.exe is such a zombie
        print('  ignoring zombie kl2.exe (working set < 1 MB): %s' % z, flush=True)
        # any stage whose install.py knows the flag (dm06btraffic1108 11-08 was refused: only LC kits got it)
        if inst and '--skip-run-check' in open('%s/install.py' % c['stage'], encoding='utf-8', errors='replace').read():
            inst.append('--skip-run-check')
    rc_total = 0
    if inst:
        print('INSTALLING the stage into the LIVE game folder (undone at the end): %s' % md, flush=True)
        if sh(inst):
            print('RESULT: not started - install.py refused (nothing changed)'); return 1
    else:
        print('nothing installed: the bench runs on the live %s as it is' % md, flush=True)
    try:
        for p in parts:
            tag = '%s_%s' % (k, p)
            for i in (1, 2):
                os.makedirs('%s/%s/inst%d' % (SOLO, tag, i), exist_ok=True)
                import shutil
                shutil.copy2('%s/KLShopPage.ini' % d, '%s/%s/inst%d/KLShopPage.ini' % (SOLO, tag, i))
            if p == 'solo':
                args = ['--n', '1', '--secs', str(c['solo_secs']), '--ini1', '%s/solo.ini' % d, '--shots', c.get('shots', '30-%d:20' % (c['solo_secs'] - 60)), '--d3shots']
            else:
                secs = 2500 if p == 'long' else 1900
                args = ['--n', '2', '--secs', str(secs), '--gap', '45', '--relaunch', '2', '--ini1', '%s/online_host.ini' % d, '--ini2', '%s/online_join.ini' % d]
                if k in LC:
                    args += ['--shots', '60-%d:60' % (secs - 60), '--d3shots']
            cmd = [sys.executable, 'tools/kl_solo_test.py', '--hook', '%s/hook_test' % d, '--tag', tag, '--base', '%s/KLHook_base.ini' % d, '--owner-away'] + args
            with open('%s/%s_run.txt' % (d, p), 'w') as out:
                print('  run %s (log %s/%s_run.txt)' % (tag, d, p), flush=True)
                rc = subprocess.run(cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT).returncode
            print('  bench exit %d' % rc, flush=True)
            rc_total |= verify(k, p)
    finally:
        if inst:
            print('UNDOING the stage (install.py --undo)', flush=True)
            r = sh(inst + ['--undo'])
        else:
            r = 0
        after = snap(md)
        same = {n: m for n, m in after.items() if not (c['tag'] and n.endswith(c['tag']))} == {n: m for n, m in before.items()}
        if not inst and not same:
            print('MAP FOLDER CHANGED during the run (nothing was installed): compare with the md5s above'); rc_total = 1
        elif r or not same:
            print('UNDO FAILED - run by hand: python "%s/install.py" --undo%s ; then compare with the md5s above' % (c['stage'], (' --game "%s"' % DD) if k == 'dd10s1106' else ''))
            rc_total = 1
        else:
            print('undo OK: every file in %s has its pre-run md5 again' % md)
    print('RESULT: %s run done, %s' % (k, 'ALL PASS' if not rc_total else 'see FAIL lines'))
    return rc_total


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return 2
    cmd = a[0]
    if cmd == 'gen':
        gen(a[1] if len(a) > 1 else 'all'); return 0
    if cmd == 'validate':
        return validate(a[1] if len(a) > 1 else 'all')
    if cmd == 'run' and len(a) > 1 and a[1] in KITS:
        return run(a[1], a[2] if len(a) > 2 else 'all')
    if cmd == 'verify' and len(a) > 1 and a[1] in KITS:
        parts = [a[2]] if len(a) > 2 else KITS[a[1]]['parts']
        return max(verify(a[1], p) for p in parts)
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main())
