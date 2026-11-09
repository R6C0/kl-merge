# KL: Dead Men Rising - owner release steps (Josh / the local sessions), tester download Tue 2026-11-10, play Wed 2026-11-11

Written offline in the cloud on 2026-11-09. **Everything under `tools/launcher/` is UNTESTED on a Windows PC**: the
scripts were written against the documented behaviour of cmd / Windows PowerShell 5.1 / WPF and against
`tools/kl_release.py` as committed; `tools/launcher/launcher_test.py` checks the files statically (placeholders, CLI
verbs vs kl_release's argparse, XAML well-formed, bracket balance) and, on a PC with `pwsh`/`powershell`, parses the
.ps1 files. Steps marked UNTESTED below have never been run by anyone.

## 0. What the tester receives, and why it carries no game data

- `KL Dead Men Rising Setup.bat` (one file; RELEASE_URL inside it) -> downloads `KLMerge_package_v<ver>.zip` -> unpacks:
  `manifest.json`, `patches\*.klp`, `kl_release.py`, optionally `KLMergeSetup.exe`, and `launcher\` (the .ps1,
  `KL Dead Men Rising.exe`, the tester README; Setup copies them up beside itself, so re-running Setup updates the launcher too).
- `kl_release.py make` ships ONLY: our own files as literal bytes (`dinput8.dll`, `KLHook.ini`, `KLShopPage.ini`,
  `KL_MOD_SETTINGS.txt`, `KLExpansion\KLHook.expansion.ini`, the Ambience / Stinger clips except anything with `pd2` in
  the name, overlay .ini files) and PATCHES whose copy operations point into the player's own stock Dog Days / Dead Men /
  Payday 2 files. A map zip is shipped as its zip skeleton + per-member copy ops + the literal bytes no source has.
  (kl_release.py header; re/release_size.md: delta estimate 560 to 640 MB.)
- The tester needs Dead Men installed (the installer stops without it) and gets Payday 2 bits only when Payday 2 is there.
- The launcher's MUSIC is not in the package either: `launcher\kl_launcher_music.py` (= `tools\kl_launcher_music.py`) runs on
  the tester's PC and decodes one clip of THEIR Dead Men `PC_Def.str` into `music\deadmen_riff.wav` beside the launcher
  (first start with a known Dead Men folder, after INSTALL, or on UNMUTE). The default clip is Dead Men's MAIN MENU loop
  `SFX/UserInterface/MenuLoop_01.wav` (an Ogg Vorbis stream, 77 s), decoded by `launcher\bin\kl_oggdec.exe` (= `tools\launcher\bin\kl_oggdec.exe`,
  public-domain stb_vorbis pinned by sha256 in `tools\launcher\oggdec\stb_vorbis.sha256`; rebuild with `tools\launcher\oggdec\build.bat`,
  32-bit, packed by `pack_release.ps1`, copied up by Setup); without the exe it tries ffmpeg on the PATH, then the next candidate. Your own `tools\launcher\music\` is never
  packed (`pack_release.ps1` refuses it; a `.wav` in the staging folder is refused by the extension check too).
- The launcher's BACKGROUND pictures `launcher\bg\dead_men.jpg` and `bg\dog_days.jpg` ARE packed - they are yours (section 2b).

## 1. Before `make`: the live Dog Days folder IS the release content

`make` reads the LIVE files: `<DD>\dinput8.dll`, `<DD>\KLHook.ini`, `KLShopPage.ini`, `KL_MOD_SETTINGS.txt`,
`KLExpansion\**` (Maps, Overlay, Ambience, Stinger), every stock-slot file under `Scenes\Locations\F01..F09, L00..L11`
that differs from its `KL_PortBackup` copy (group `stockwav`), and `PC_Def.str` (group `pcdef`). So:

1. Close the game. Make sure the installed hook is the SHIP dll you want testers to run (no TEST / klauto build:
   the launcher shows the live dll's sha1 and compares it with the package's), and the ini is the one to ship.
   **Review `KLHook.ini` first**: it is shipped as-is (minus nothing). Take out test-only sections and keys
   (`[Auto]`, `[Bench]`, `[Script]`, `[Solo]`, high `Log=` levels, anything "(recommended on)" that is not meant for
   strangers) and leave the Steam write guard as it is. `KEEP_USER` only protects a tester's OWN later edits.
2. F01 must hold the STOCK Subway, not a test build (`tools\RESTORE Dog Days originals.bat` or the F01 part of it),
   unless a modified F01 file is meant to ship as `stockwav`.
3. Stock proof: a file under `<DD>` with mtime after 2026-09-14 needs its stock copy in `KL_PortBackup` (or a
   `.before-1024gunsnd2` twin older than that), else `make` raises "no stock proof for DD file ..." for that source.
4. Disk: C: is nearly full (CLAUDE.md: ~976 MB). Put the output on D: (6.7 GB free) or G:. The output is the package
   (~0.6 GB est.) plus `_snap\` (copies of the small own files) plus `sha1cache.json`.
5. Python on your PC with `numpy` and `zstandard` (`pip install numpy zstandard`).

## 2. Make the package

```bat
cd /d <this repo>
python tools\kl_release.py make D:\kl_release\pkg_1110 --dd "C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days" --dm "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men" --pd2 "C:\Steam\steamapps\common\PAYDAY 2"
```

- Paths are CLAUDE.md's (DD on C:, DM on G:, Payday 2 on C:). `--level 15` is the default zstd level; `--only core,DM03`
  makes a partial package for a quick test. Runs at BELOW_NORMAL priority; takes long (every member deflate-matched).
- It prints `manifest: N files, M patches, X of patches` at the end: **X is the download size to put in the release
  post and in README_TESTERS.md** (replace the "about 0.6 GB" estimate). `WARN ... changed while it was read` means
  another session wrote into the game folder during make: re-run (patches already made are reused by sha1 name).
- `NOT SHIPPED (Payday 2 audio): ...` lists the pd2 clips left out by design.
- Then, with nothing else touching the folder:
  `python tools\kl_release.py checklive D:\kl_release\pkg_1110 --dd "<DD>"` -> `0 changed/missing`, and
  `python tools\kl_release.py verify "<DD>" --pkg D:\kl_release\pkg_1110` -> `0 problems` (the live folder equals the manifest).
- Bump `VERSION = '1.0.0'` in `tools/kl_release.py` for every package you hand out (the launcher shows it; a tester's
  kept `KLHook.ini` gets the new default as `KLHook.ini.new-<VERSION>`; `--pkg` folders with different versions must
  not be mixed).

## 2b. The launcher's two background pictures (yours; before `pack_release.ps1`)

The window blends two images at a soft diagonal seam: **left = Dead Men, right = Dog Days**. Put your OWN screenshots in
`tools\launcher\bg\` (the folder is git-ignored except for its README; nothing of it is committed):

- `tools\launcher\bg\dead_men.jpg` - a Dead Men screenshot (the grainy 2007 look; a wide shot without HUD reads best)
- `tools\launcher\bg\dog_days.jpg` - a Dog Days screenshot (the camcorder look)

Rules of thumb: JPEG, 16:9 or wider, 1600 px wide or more (the window is 960 x 680 by default and can be resized;
`UniformToFill` crops, never stretches), darker pictures work better (the launcher dims them to about 40 % and puts its
grain and vignette on top so the text stays readable). No third-party art: your screenshots of the two games only.
`pack_release.ps1` copies `launcher\bg\*.jpg` into the package; Setup copies them up beside the launcher on the tester's PC.
With one or both missing the launcher draws its fallback (grey film grain left, dark teal video blocks right) and logs one line.

To hear the music on YOUR PC before packing: `python tools\kl_launcher_music.py extract --dm "G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men" --out tools\launcher\music\deadmen_riff.wav`
(exit 0 and a `wrote ...` line; exit 2 = no decodable clip, say so). `--list` prints the Music/ clips with their codec, `--clip NAME`
picks another one; the default order is in the tool's `CANDIDATES` (Dead Men's main menu loop `MenuLoop_01` if a decoder is there, then the FA theme `FA_SlashMixPrison` if it is PCM, else the
Retomoto tension bed `TakyoAction_Layer2_TAmbient_Loop`, then the bank break-in bed). A tester can set `MusicClip` in the settings file.
The written `.wav` stays on your PC (`tools\launcher\music\` is git-ignored and never packed).

## 3. Freeze KLMergeSetup.exe (optional, UNTESTED here) - or skip it

With the frozen exe in the package the tester needs no Python at all and Setup skips the python.org / PyPI downloads.
```bat
pip install pyinstaller
pyinstaller --onefile --name KLMergeSetup --hidden-import zstandard --hidden-import zstandard.backend_c tools\kl_release.py
```
-> `dist\KLMergeSetup.exe` (hidden-import names are a GUESS; test `dist\KLMergeSetup.exe verify "<DD>" --pkg <pkg>` on
your PC: it must print the same `verify:` line as the python run). The launcher uses the exe when
`<package>\KLMergeSetup.exe` exists, else `python -u kl_release.py`. Skip the freeze if PyInstaller is not installed:
`KL Dead Men Rising Setup.bat` then fetches the embeddable Python 3.12 into `<launcher>\python\` and pip-installs `zstandard`
(needs internet to python.org and pypi.org on the tester's PC; URLs are GUESS-marked in the .bat).
SmartScreen will warn about an unsigned exe either way (the .bat too); the README tells testers to click through.
Defender (2026-11-09): your helper .bat was flagged Trojan:Win32/Ceprolad.A (heuristic: powershell -WindowStyle Hidden +
-ExecutionPolicy Bypass from a .bat). The Setup now starts `KL Dead Men Rising.exe` (no console at all: it hosts the .ps1
in-process; KLMerge.bat is gone) and falls back to a MINIMIZED powershell (`start /min`), never hidden, and README_TESTERS has a "If Windows Defender / SmartScreen complains" section (plain-text scripts, Protection
history > Restore, Properties > Unblock, signed exe planned). Before the upload: scan the packed zip with Defender once.

## 4. Pack and upload (UNTESTED here)

First build the launcher exe (after any change to `exe\DeadMenRising.cs` or the icon): `tools\launcher\exe\build.bat`
-> `tools\launcher\KL Dead Men Rising.exe` (unsigned; pack_release prints a note when it is missing).

```bat
powershell -ExecutionPolicy Bypass -File tools\launcher\pack_release.ps1 -Out D:\kl_release\pkg_1110 [-Exe dist\KLMergeSetup.exe]
```
-> `D:\kl_release\KLMerge_package_v<ver>.zip` + `.sha1`. It copies only manifest.json, patches\, kl_release.py, the
launcher files (+ `launcher\kl_launcher_music.py` and your `launcher\bg\*.jpg`, section 2b) and the optional exe (never
`_snap`, `parts`, `sha1cache.json`, never `launcher\music\`) and refuses if anything with a game extension slipped into
the staging folder.

Where to host - **decision for Josh**:
- A PRIVATE GitHub repo's release assets need a token: `curl` from the tester's PC gets 404. So either make a
  separate **public** repo (e.g. `klmerge-release`, no source needed, just Releases; the zip holds no game data and
  no Dead Men / Dog Days bytes, only our code + patch recipes) and upload the zip as a release asset (GitHub's limit is
  2 GB per asset), or use any plain https host (Dropbox link with `?dl=1`; avoid Google Drive: large files hit the
  virus-scan page and `curl` gets HTML).
- Copy the asset's download URL (`https://github.com/<user>/klmerge-release/releases/download/v<ver>/KLMerge_package_v<ver>.zip`)
  into the ONE `set "RELEASE_URL=..."` line of `tools\launcher\KL Dead Men Rising Setup.bat`. Hand out that .bat (and the
  README) only; everything else comes through the URL. Keep the .bat out of this private repo's Releases.
- `curl -z` makes a re-run download only when the server copy is newer (GitHub assets send Last-Modified: GUESS that
  the redirect target does too; if not, re-runs re-download - annoying, not harmful).

## 5. Rehearsal on a clean PC (do this before Tuesday; all UNTESTED)

A second PC, or a new Windows user on yours, with Steam + Dog Days + Dead Men installed and nothing of the mod:
1. Put `KL Dead Men Rising Setup.bat` in `C:\DeadMenRising`, run it: download, unpack, python, launcher window. Note the download
   size and time.
2. STATUS finds DOG DAYS and DEAD MEN (and PAYDAY 2 if installed). If not: the `...` pickers.
3. INSTALL / UPDATE: watch for `CANNOT INSTALL` (a non-stock source) vs `Done.`; time it.
4. VERIFY -> `0 problems`.
5. PLAY DEAD MEN RISING -> the launcher hides once the game window is up and comes back when the game
   closes (or crashes: noted in its LOG). A Dead Men map round from the Arcade pages. Check `<DD>\KLHook.log` starts with
   `==== KLHook loaded` and `build: SHIP`.
6. PLAY DOG DAYS -> the stock game; `dinput8.dll.klmerge-off` exists, `dinput8.dll` does not. PLAY DEAD MEN RISING -> back.
7. UNINSTALL -> then Steam > Verify integrity must find **0 files to re-acquire** (byte-exact restore). Then INSTALL again.
8. COLLECT LOGS -> the zip opens in Explorer.
On YOUR PC the PLAY buttons will not behave: your Steam launch options (`-dx10 -o DefaultScene=Locations/F01/F01_Main.gms
-o AutoExit=120`) boot straight into F01 and quit after 120 s. Clear them for a play session or test on the other PC.
The launcher never reads or writes launch options.

## 6. Decisions / open points for Josh

1. **Release host** (section 4): public release repo on GitHub, or another https host.
2. **Package size**: the `manifest:` line of `make`; put the real number in the release post and README_TESTERS.md.
3. **Freeze or not** (section 3). Without it, testers need internet to python.org + pypi.org during Setup.
4. **ReShade**: the hook loads `ReShade32.dll` + `ReShadePreset_*.ini` from the game folder when present
   (`[Graphics] Look`), but `kl_release.py` does not ship them (OWN_ROOT). Testers get no ReShade look unless you add
   those files to OWN_ROOT (licence: ReShade's own; your call) or tell them it is optional.
5. **The shipped ini** is your live `KLHook.ini` (section 1). Decide what stays on for strangers.
6. **Payday 2 audio** clips are never shipped (by design in kl_release.py); the Payday 2 masks / guns need the tester's own
   Payday 2 install. Say so in the release post (README does).
7. Firewall: README tells testers to allow `kl2.exe` in Windows Firewall (the game checks its own path, kl2 0x8945d0)
   and names UDP 27413-27416 for the hook's peer channel. Whether router port forwarding is ever needed is unknown.
8. **Launcher music and pictures** (section 2b): which Dead Men clip (the default list is a GUESS of taste: FA theme, else the
   Retomoto bed), the volume (0.22 = "slightly", `Volume` in the settings file), and your two screenshots in `bg\`.

## 7. What is untested / GUESS (collected)

- All of `tools/launcher/` on Windows: cmd flow of the .bat (curl -z, tar.exe zip extraction, robocopy /MOVE for a
  zip with a top folder, the `._pth` edit of the embeddable Python, get-pip), the WPF window (font list, grain brush,
  FolderBrowserDialog under -STA), `Start-Process -RedirectStandardOutput` tailing into the log pane, `Compress-Archive`.
- PyInstaller hidden-import names; whether the frozen exe flushes stdout line by line (python runs with `-u`).
- The Payday 2 Steam folder name `PAYDAY 2` (taken from kl_release.py).
- Sizes and times in README_TESTERS.md are estimates until the rehearsal.
- Music: `System.Windows.Media.MediaPlayer` looping a .wav through MediaEnded + Position = 0 (a gap at the seam is possible; the
  clip is faded in and out so a gap is quiet), volume 0.22, `Start-Process` of the python tool from the window. The
  decoder itself (`tools/kl_launcher_music.py`) is proven on synthetic data only (`kl_launcher_music_test.py`, 48 checks: PCM,
  2-layer interleaved PCM sets behind a LIP block, unequal-rate sets, mono IMA ADPCM, Ogg Vorbis framing + CRC + decoder fallback); the Dead Men file
  layout it reads is the one `tools/kl_str.py` measured on the real file. The codec of `FA_SlashMixPrison` is unknown
  (skipped if Vorbis and no decoder); the Retomoto set `TokyoAction1` is PCM 2 x stereo 32 kHz (re/retomoto_audio.md 4.1).
- Background: WPF JPEG decode of your screenshots, `OpacityMask` on a Grid for the seam, the seam's angle (relative gradient points).
