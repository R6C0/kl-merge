RELEASE 1023b - one install for today's hook work (Kane & Lynch 2: Dog Days + the expansion)
==========================================================================================
This replaces the earlier "release 1023" kit. Use ONE of them; 1023b is the newer (it has the stinger code that 1023 lacks).
It has its own backup folder (release_1023b_backup), so the two kits' undo files never mix.

WHAT CHANGES IN THE GAME
1. New hook (dinput8.dll, SHIP build of everything merged on rtp-schemas up to 751c25d20 on 2026-10-23, including the
   event stingers and sound pass 3 code). New features in it are off unless the ini turns them on.
2. Balance pass 2 (KLHook.ini [Balance]; you said the AI felt a bit too strong):
   - a guard at arm's length hits you for 4.5 bullets (was 6.0)
   - police bullets on you x0.7 (was 0.9); AI heister bullets on you x0.6 (new line)
   - your health is the game's own 550 (was 495)
   - NEW: police bullets from far away hurt less: full strength inside 12 m, x0.6 from 40 m on, in between smoothly
   (Live-tested on 2026-10-23: the far-police factor x0.86 at 21 m.) Only the early Arcade levels feel it.
   Your KLHook.ini already has [Balance] Enable=1, so the plain INSTALL is enough. The installer prints the live
   Enable/Risk/... values; only if it shows a NOTE that Enable is not 1, re-run it with -BalanceOn (adds Enable=1).
3. Two quality-of-life keys ([QoL]) - read live, the flash and the cursor release themselves are NOT proven in the game yet:
   - FlashOnReady=1: the taskbar button flashes when a level finished loading, when the lobby countdown starts and when the
     round is over, while you are in another window.
   - ReleaseCursor=1: the mouse is freed when you alt-tab out of the game.
   Left OFF on purpose: BackgroundMs and everything in [QoL2].

OPTIONAL ADD-ONS (more lively: both were played on DM01 on 2026-10-23, 0 faults). They only add clips and ini lines; they never
touch dinput8.dll, so they cannot put an older hook back.
 A. Sound pass 3 ("OPTIONAL 1 sound3.bat"): per-map one-shot sounds for Local and Panic moments plus Payday 2 ASSAULT music.
    Clips go to <DD>\KLExpansion\Ambience\local and \panic; it rewrites the [Ambience.*] / [Music.*] sections of KLHook.ini
    (keeps a copy KLHook.ini.before-sound3 the first time).
 B. Event stingers ("OPTIONAL 2 stinger.bat"): a short music cue when the heist goes loud, loot is taken, someone is down or dead,
    a betrayal, the last 30 seconds, the escape opens, you reach the van. Clips go to <DD>\KLExpansion\Stinger; a [Stinger]
    block is appended to KLHook.ini between two marker lines.
 Which clip fits which event was picked from file names; nobody has judged it by ear beyond the one run. Edit the lists in the
 ini [Stinger] block if one sounds wrong.

HOW TO INSTALL (in this order)
 1. Close the game (every script refuses while kl2.exe runs).
 2. Double-click "INSTALL release 1023b.bat". Python must be on the PATH (kl_ini_patch.py needs it).
    It checks the package dll against dinput8.dll.sha1, prints the sha1 of the dll it replaces, copies your dinput8.dll and
    KLHook.ini to ..\release_1023b_backup with a time stamp, puts the new dll in, edits only the lines named above in
    KLHook.ini and writes the undo. Running it twice is harmless.
 3. Optional: double-click "OPTIONAL 1 sound3.bat", then "OPTIONAL 2 stinger.bat". They look for the folders
    ..\sound3_1023 and ..\stinger_1023 next to this kit (<work>\build\). Do the add-ons AFTER step 2.
 4. NEVER add the switch -Dll to the stinger installer by hand: the dll inside the stinger folder is older than this release's.
    The OPTIONAL bats here do not pass it.
 Nothing else in the Dog Days folder is touched (not KL_PortBackup, no map zips).

HOW TO UNDO (reverse order)
 1. Close the game.
 2. Add-ons first (only the ones you installed): "OPTIONAL 2 UNDO stinger.bat", "OPTIONAL 1 UNDO sound3.bat".
    Each removes only its own ini lines and its own clip folder.
 3. Then ..\release_1023b_backup\UNDO release 1023b.bat (path: <work>\build\release_1023b_backup\). It puts dinput8.dll and
    KLHook.ini back byte for byte (md5 checked) to what they were before step 2 of the install. If you changed KLHook.ini
    after the install, that edited copy is first saved there as KLHook.ini.undo-<time>.
    Note: this puts the WHOLE ini back, so ini lines the add-ons wrote vanish too (their clips stay on disk, unused). That is why
    the add-ons go first on the way out; if you do it the other way round nothing breaks, the add-on undo just finds nothing to remove.
 4. Only the dll or only the ini: copy dinput8.dll.<stamp> / KLHook.ini.<stamp> from release_1023b_backup by hand.

IF YOU ALREADY INSTALLED THE OLD "release 1023" KIT: just run this kit on top. Its backups are then the old kit's state, so its
undo returns to that. The old kit's own undo is still in release_1023_backup.

EARLIER UNDO BATS (independent of this release; <work> = G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools)
 - <work>\build\shopcut4_1023_undo\UNDO shopcut4 1023.bat   (keep the shopcut3_1023 folder)
 - <work>\build\shopcut3_1023_backup\UNDO shopcut 1023.bat
 - <work>\build\shopbar_1023_backup\UNDO shopbar 1023.bat
 - <work>\build\ambience2_1023_backup\UNDO ambience2 1023.bat
 - <work>\build\acc75_1023_backup\UNDO acc75 1023.bat
 - <work>\build\locfit_1023_backup\UNDO locfit 1023.bat
 - do NOT run "INSTALL balance2 1023.bat" as well: same keys, its undo would restore an older ini.
