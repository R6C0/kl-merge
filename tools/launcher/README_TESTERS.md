# KL: Dead Men Rising - tester guide

KL: Dead Men Rising puts Kane & Lynch: Dead Men content (its Fragile Alliance maps, player models, voices, more) inside
Kane & Lynch 2: Dog Days on PC (Steam). It is a tester build: expect rough edges, and please send logs when it breaks.

Nothing you download contains game files. The package holds the mod's own code plus small binary "patches"; the
installer rebuilds every modded game file **on your PC from your own Dog Days / Dead Men (/ Payday 2) installs** and
checks every byte (sha1) before anything is written. Replaced stock files are **moved** to `<Dog Days>\KL_PortBackup\`,
never deleted, so UNINSTALL puts everything back exactly.

## What you need

| | |
|---|---|
| Windows 10 or 11, 64-bit | the launcher is `KL Dead Men Rising.exe` (it runs the readable `KLMergeLauncher.ps1` beside it on Windows' own PowerShell engine); no admin rights needed |
| **Kane & Lynch 2: Dog Days** on Steam | stock, unmodified. The installer checks `kl2.exe`; if it says the sha1 differs, run Steam > Properties > Installed Files > Verify integrity first |
| **Kane & Lynch: Dead Men** on Steam | **required.** The Dead Men maps, models and voices are rebuilt from YOUR Dead Men files. Without it the installer stops with "Dead Men was not found" and writes nothing |
| Payday 2 on Steam | optional. The Payday 2 guns / masks pieces are skipped when it is not installed (the installer says how many files it skipped); everything else works |
| Disk space on the Dog Days drive | roughly 6 to 8 GB for the rebuilt map folders (GUESS from the owner's folder; the installer prints the exact total and refuses with a clear message when the drive is short - it wants that total plus 1 GB headroom) |
| Download | the package zip: about 0.6 GB (estimate from the owner's size study; the real figure is in the release post). If you have no Python 3, Setup also fetches a 12 MB embedded Python from python.org plus one module from PyPI |
| Time | the install rebuilds and sha1-checks every file: allow 10 to 30 minutes on a normal PC (GUESS: not timed on a tester PC yet). Re-runs are fast: files that are already right are skipped |

## Install

1. Make a folder for the mod tools, e.g. `C:\DeadMenRising` (NOT inside the Dog Days folder), and put **`KL Dead Men Rising Setup.bat`** in it.
2. Double-click `KL Dead Men Rising Setup.bat`. (Windows SmartScreen may show "Windows protected your PC": More info > Run anyway.)
   It downloads the package into `download\`, unpacks it into `package\`, finds or fetches Python, and opens the launcher.
   From then on start the launcher with **`KL Dead Men Rising.exe`** in the same folder (no console window).
   Run the same file again any time to **update** (it only downloads when the server copy is newer).
3. In the launcher check the STATUS panel: DOG DAYS and DEAD MEN must show a folder (use the `...` buttons if not;
   Steam libraries on other drives are found automatically).
4. Click **INSTALL / UPDATE**. Watch the LOG pane. It ends with `finished, exit code 0 (OK)`.
   Exit code 2 means it refused BEFORE writing anything; the lines above say why (a source file missing or not stock).
5. Click **PLAY DEAD MEN RISING**. The game starts through Steam as usual (overlay and online work).
   The launcher hides itself once the game window is up, and comes back when the game closes or crashes
   (a crash is noted in its LOG pane: send the files listed under "When it crashes").
   In the game: Arcade Mode / Fragile Alliance - the Dead Men maps are on their own pages below the stock map button.

The launcher remembers your folders in `KLMergeLauncher.settings.json` beside it, and everything it prints in `KLMergeLauncher.log`.

## If Windows Defender / SmartScreen complains

- **SmartScreen** ("Windows protected your PC") shows for any downloaded .bat or unsigned .exe: More info > Run anyway.
  `KL Dead Men Rising.exe` is not code-signed yet, so expect this once per download.
- **Windows Defender** may flag `KL Dead Men Rising Setup.bat` with a heuristic name such as
  `Trojan:Win32/Ceprolad.A`. That heuristic fires on the *shape* of the script (a batch file that starts PowerShell with
  a lowered execution policy and downloads a file), not on anything it found inside. The .bat file and
  `KLMergeLauncher.ps1` are **plain text**: open them in Notepad and read what they do. They download the package from
  the one URL at the top of the Setup file, unpack it, start the launcher, and never delete anything (the only move is
  the unpacked package into `package\`).
- If Defender quarantined a file: Windows Security > Virus & threat protection > Protection history > the entry >
  Actions > Restore (or Allow). Then right-click the file > Properties > tick **Unblock** > OK, so the "downloaded from
  the internet" mark is gone, and run it again.
- The exe is a small starter (its source is `exe\DeadMenRising.cs` in the mod's repo): it only runs `KLMergeLauncher.ps1`.
  A code-signed build is planned; until then the scripts stay readable on purpose.

## Music and the background

The launcher plays a Dead Men music clip quietly. **That clip is not part of the download**: when the launcher knows
your Dead Men folder it reads one piece of music out of **your own** Dead Men files (`PC_Def.str`) once, into
`music\deadmen_riff.wav` beside the launcher (about 20 MB, 106 seconds): the guitar riff of Dead Men's trailer
(`Movies\Trailer.bik`) looped, fading into Dead Men's main menu theme and back. It is decoded on your PC by small
decoders that come with the download (`bin\kl_oggdec.exe`, public-domain Ogg Vorbis; `kl_pybink.py` for the trailer; ffmpeg
is used when you have it). Without the trailer you get the menu theme alone. Until then, or when your Dead Men
install has no readable clip, it simply stays silent - nothing else depends on it.

- **MUTE / UNMUTE** is in the top right, next to the `♪` state text (`♪ DEAD MEN 22%` playing, `♪ MUTED`, `♪ NO MUSIC`).
  The choice is remembered. `Volume` in `KLMergeLauncher.settings.json` sets how loud (0 to 1, default 0.22), and
  `MusicClip` lets you name another Dead Men clip (`python kl_launcher_music.py list --dm "<Dead Men folder>" Music` lists them).
- The background is two pictures, `bg\dead_men.jpg` and `bg\dog_days.jpg`, blended down the middle; if they are missing
  the launcher draws a plain one instead. Nothing of it touches the games.

## Stock game or modded game

The whole mod hangs on one file, `dinput8.dll` in the Dog Days folder (the "hook"). The game loads it because it sits
beside `kl2.exe`; without it the game is stock. The hook has no on/off switch inside it, so the launcher switches by
**renaming** (never deleting):

- **PLAY DOG DAYS** renames `dinput8.dll` to `dinput8.dll.klmerge-off`, then starts the game: stock game, stock menus.
  The mod's map folders stay on disk but nothing loads them.
- **PLAY DEAD MEN RISING** renames it back and starts the game.
- **HOOK ON / OFF** does the rename without starting anything.

Both refuse while `kl2.exe` is running - close the game first. One honesty note: the package may also replace a few
stock sound files and the stream file `PC_Def.str` inside the Dog Days folder (groups "stockwav" / "pcdef"); those stay
in place while the hook is off. They are Dog Days' own slots with added clips and the stock game runs with them, but
if you want a byte-exact stock game, use UNINSTALL.

Do not run Steam's "Verify integrity of game files" while the mod is installed: Steam would put stock files over the
replaced ones. Nothing is lost (the backups and the mod folders stay), but run INSTALL / UPDATE again afterwards and
VERIFY until it reports 0 problems.

## Verify, update, uninstall

- **VERIFY** checks every installed file against the package (size + sha1) and prints `verify: N files checked, 0 problems`.
  `edited KLHook.ini (yours)` is fine: your own `KLHook.ini` / `KLShopPage.ini` are never overwritten by an update; the
  new defaults land beside them as `KLHook.ini.new-<version>`.
- **Update**: run `KL Dead Men Rising Setup.bat` again (new package), then INSTALL / UPDATE. Only changed files are rebuilt.
  **Everybody in an online session must be on the same package version** - the game's own version check does not know
  about the mod's files, and a map built from another version desyncs or crashes the others.
- **UNINSTALL (RESTORE STOCK)** removes the mod's files and moves the stock files back from `KL_PortBackup` (journal
  `<Dog Days>\KLMergeInstall.json`). Files you edited yourself are kept as `<name>.edited-<time>`.
  If the launcher itself is gone: `python package\kl_release.py uninstall "<Dog Days folder>"`, or, last resort, delete
  `dinput8.dll`, `KLHook.ini`, `KLShopPage.ini` and the `KLExpansion` folder and let Steam verify the game files.

## Online play: firewall and ports

- **Windows Firewall must allow `kl2.exe`.** The game itself asks Windows Firewall about its own path and shows
  "blocked by a firewall" on the System Link page when it is not allowed. Windows Security > Firewall & network
  protection > Allow an app through firewall > Change settings > Allow another app > browse to
  `...\steamapps\common\Kane & Lynch 2 - Dog Days\kl2.exe`, tick **Private and Public**. (Or, as administrator:
  `netsh advfirewall firewall add rule name="KL2" dir=in action=allow program="<that path>\kl2.exe" enable=yes profile=any`
  and the same with `dir=out`.) The rule's program path must be exactly the game's path.
- The mod talks between players over Steam's own networking (like the stock game) plus a few extra UDP messages on
  ports **27413 to 27416** between the peers (player looks, host options, sync). On a LAN or direct connection allow
  UDP 27413-27416 in both directions. Whether anything has to be port-forwarded on a home router for Steam play has
  NOT been established - stock Dog Days needs no forwarding, and nothing in the mod's notes says the extra channel
  does either; if looks or options do not reach the other players, say so (it is the first thing to check).
- Private match and the stock 9 Dog Days maps work with the mod installed; the Dead Men maps need every player modded.

## When it crashes or misbehaves

Files to send (all in the Dog Days folder):

- `KLHook.log` - the hook's log (what the mod did, the last lines before a crash, the fault address)
- `KLHook_1.dmp` ... `KLHook_4.dmp` - the hook's own crash dumps
- `kl2_490_crash_*.mdmp` - the game's own crash dumps
- `KLMergeInstall.json` - what is installed (useful when the install itself misbehaves)

The launcher's **COLLECT LOGS** button zips all of them (plus `KLMergeLauncher.log`) into `DeadMenRising_logs_<date>.zip`
beside the launcher and opens the folder: send that file, with one line on what you were doing (map, mode, how many
players, what you pressed). If the game hangs instead of crashing, note the time and send the same files.

If the INSTALL step refuses, send the LOG pane text (it is in `KLMergeLauncher.log` too).

## Known limits of this tester build

- Written for the Steam versions of both games; other stores or cracked exes are refused (sha1).
- The installer writes only inside the Dog Days folder (plus the launcher's own folder). Steam launch options are never touched.
- `dinput8.dll` and `KLHook.ini` are how the mod runs; a game folder that already has another mod's `dinput8.dll`
  (ReShade, controller wrappers) will have it moved to `KL_PortBackup\_klmerge_replaced\...` by the install and put back by UNINSTALL.
