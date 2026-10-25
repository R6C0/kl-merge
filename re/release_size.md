# Release size: what to ship, what to throw away (2026-10-25)

Source: three read-only measurements (variants audit, piece-level dedup, solid 7z run). Nothing was written to the game folder. Scratch is in D:\KL_size_1025. Numbers marked (est.) are estimates. Anything not measured says so.

## Short answer

| Question | Answer |
|---|---|
| Live KLExpansion on disk | 7.48 GB (25.7 GB logical, the rest is .before* backups) |
| Plain solid 7z of the current maps | 4,959 MB (4.84 GB), measured, from 6,105 MB input (about 19 percent saved) |
| Delta release (new pieces only) | about 560 to 640 MB (est.), about 8 times smaller |
| Biggest free win | Leave out the 471 .before* files: 17.63 GB, no judgment needed |

## 1) Dead weight in the game folder right now

### 1a) Map folders the audit marked unused-archive (may be moved to D:\KL_DD_archive_1025)

No rule in KLHook.ini ([Redirect], [Redirect.2], [Redirect.3], [Page.N], [Slots]) loads them. The only loader is klhook/klslot.c, and it uses a folder name only from an ini rule value.

| Folder | What it is | Logical | Live part | Verdict |
|---|---|---|---|---|
| Maps\DM09RB | Retomoto rope-bar test copy (182 MB zip, older than live DM09 at 219 MB) | 843 MB | about 226 MB | unused-archive |
| Maps\DM09RB2 | same | 843 MB | about 226 MB | unused-archive |
| Maps\DM09RB3 | same | 843 MB | about 226 MB | unused-archive |
| Maps\DM09RB4 | same | 843 MB | about 226 MB | unused-archive |
| Maps\DM09RD | rope test copy from the DM09_rope build | 843 MB | about 226 MB | unused-archive |
| Maps\DM09RV | rope test copy from DM09_rope | 843 MB | about 226 MB | unused-archive |
| Maps\DM09RV2 | second rope test copy | 843 MB | about 226 MB | unused-archive |
| Maps\T01 | developer live-test slot (207 MB zip), recreated by live.py on each run | 890 MB | about 247 MB | unused-archive |
| **Total** | | **6,791 MB** (7 x 843 + 890) | **about 1.8 GB** (7 x 226 + 247) | |

The rest of each folder (about 616 MB per R folder, about 642 MB for T01) is .before* backups, covered in 1b.

Before moving them, stop the tools that still loop over them, or they get rebuilt:
- tools/kl_ambience.py (RETOMOTO, BEDSKIP), tools/kl_sound3.py (LOCAL), tools/kl_fedoutfit_stage.py (lines 39-45).
- The DM-prefix loops in kl_climb_stage.py, kl_cover3_stage.py, kl_cover_pass.py (they also pick up T01).
- The [Ambience.DM09R*] sections in the live ini can go afterwards.

T01 holds 20 test reports (388 KB). Deleting it costs nothing, live.py recreates it. The R-folder name letters B, D, V are inferred, not documented.

Hard-link note: the F06_Main.zip files and the DM09 zip show nlink 2, so a build tree may share storage with them. Deleting from the game folder drops only one link, so the real freed space can be less than the table says.

### 1b) Other dead weight (not needed to run, not "variants")

| Item | Size | Suggested action |
|---|---|---|
| All *.before* files under KLExpansion (471 files) | 17.63 GB | Leave out of any release. Prune to the newest 3 per file (owner rule 10-25) or move to D:. Nothing loads them. |
| Test reports in map folders (T01 20 files, DM09R* 15 KB each, DM05A 1 KB, Maps\checks 30 files) | under 0.5 MB | Not needed to run; leave out of release. |
| KLExpansion root journals (adopt1018_lastcall, adopt1019_hook, adopt1019_rt, owner1018_ini, stockfa_install .json) | under 3 KB each | Undo data only; keep locally, leave out of release. |
| KLExpansion\manifest.json | 167 KB | Stale (no DM01B, DM06B, DM11B, DM07, DD10). The hook reads KLHook.ini, not this. Regenerate or drop. |
| KLExpansion\_installed\ | 0.2 MB | Undo data; local only. |
| KLExpansion\KLHook.expansion.ini | 2 KB | Stale duplicate of the redirect block. |
| Overlay Patch01.zip.before-1023b, -1023icons, -1025dig | part of Overlay 63 MB, counted in the 17.63 GB | Same as the .before* rule. |
| Game root logs and dumps: KLHook.log 52 MB, KLHook_1..4.dmp 158 MB, KLHook_map_* about 1.1 MB, other logs | about 211 MB | Never ship. Safe to empty. |
| About 75 kl2_490_crash_*.mdmp | about 20 MB | Never ship. |
| Game root backups: kl2.exe.before-1025laa 10.2 MB, about 28 dinput8.dll.before-* about 32 MB, about 45 KLHook.ini.before-*, ReShade backups | about 45 MB or more | Never ship. |

### 1c) Questions for the owner (unclear, no action suggested)

1. Game root items from the DLSS / ReShade side project: host64.off 425 MB, GITC-Uplift 158 MB, KLNR 33 MB, the Install/Verify-DLSS5Feeder scripts, reshade-shots. Are they separate from KL Merge? Assumed yes, but only you can confirm. They are not in the 7.48 GB.
2. KL_PortBackup (1.4 GB) is your backup of stock files. It must never be in a download. The installer should create it on the player's PC. Not touched here.
3. C: space. kl_build_1024 is 57 GB (from the notes). Nothing is proposed for deletion.
4. The hook source tree has dozens of untracked klhook/out_3f_* build folders. They are in the repo, not in the game folder, and are not release content. Clean up is your call.

## 2) What a release really has to ship

### Where the 12.8 GB (uncompressed) of live map data comes from

Every file was cut into pieces (textures one by one, mesh chunks, other files whole or in about 32 KB content-defined chunks) and each piece was classed in order: already in stock Dog Days, already seen in an earlier map of ours, or truly new.

| Group | Uncompressed | In stock Dog Days | Shared across our maps | Truly new |
|---|---|---|---|---|
| All 29 folders (21 maps + 8 variants/T01) | 12,775.7 MB | 7,618.2 MB | 3,697.6 MB | 1,459.9 MB |
| Main 21 maps only | 9,253.7 MB | 6,145.9 MB | 1,712.1 MB | 1,395.7 MB |
| Variant group (7 R folders + T01) | 3,522.0 MB | 1,472.3 MB | 1,985.5 MB | 64.2 MB |

Reading it: only about 15 percent of the main 21 maps (1,395.7 of 9,253.7 MB) is actually new data. About 66 percent already sits in the player's own stock Dog Days. The variants add almost nothing new (64.2 MB, about 13.4 MB deflated est.).

Per-map new data (MB, uncompressed). The first map to hold a piece pays for it, so later maps look cheap.

| Map | New | Map | New | Map | New |
|---|---|---|---|---|---|
| DD01 | 84.5 | DD10 | 27.8 | DM06 | 104.3 |
| DD02 | 9.6 | DM01 | 147.6 | DM06B | 35.2 |
| DD03 | 11.7 | DM01B | 107.5 | DM07 | 102.9 |
| DD04 | 13.2 | DM02 | 111.0 | DM09 | 133.4 |
| DD05 | 12.2 | DM03 | 90.8 | DM11B | 198.6 |
| DD06 | 13.4 | DM03A | 48.9 | | |
| DD07 | 14.4 | DM05A | 97.1 | | |
| DD08 | 14.4 | | | | |
| DD09 | 17.0 | | | | |

### (a) Plain solid 7z of the current maps (measured)

Command: 7z a -t7z -mx=9 -m0=lzma2 -md=256m -ms=on, run in KLExpansion. 872 files; *.before*, *.json and the 7 R folders plus T01 excluded.

| Result | Value |
|---|---|
| Input | 6,105 MB |
| Archive | 4,959 MB |
| Saved | about 19 percent |
| Wall time | 1,413 s |

Why so little: the map zips are already deflate, so the compressor cannot see inside them. Per-map 7z is about the same as, or larger than, the zips on disk (DD01 291.3 MB zip vs 287.6 MB 7z; DD04 315.9 vs 323.3; DD05 281.3 vs 292.1). Only DD01 to DD08 were measured per map; DD09 and the Dead Men maps were not. All *.json (including BuildInfo) were excluded from this run. The file set grew from 872 to 875 files during the run.

Realistic download: about 4.9 GB. It also contains Dog Days data (0.03 GB is byte-identical to whole stock members; the larger overlap is inside the zips).

### (b) Delta release (new pieces only, maps rebuilt on the player's PC)

| Estimate | Size |
|---|---|
| New data, main 21 maps, uncompressed | 1,395.7 MB |
| Deflated, independent per piece | about 640 MB (est.) |
| With lzma | about 560 MB (est.; ratio 0.878 measured on an 82 MB sample only) |
| Variants included as well | add about 13 MB deflated (est.) |

Against the solid 7z: 4,959 MB divided by 560 to 640 MB is about 7.7 to 8.9 times smaller (arithmetic on the figures above).

Caveats, all measured or stated by the dedup run:
- "New" is an upper bound. Piece identity is the exact bytes. A texture that differs only in name or header, and mesh structure chunks with renumbered indexes, count as new. Chunks of 1 KB or less (about 96 MB "new") are partly spurious.
- "In stock" means the piece exists somewhere in stock Dog Days, not that it can be referenced in place. The recipe has to point at a concrete stock zip, member and offset. This is not yet proven for every piece.
- Mostly the Dead Men textures are the new bulk (769 MB of new textures sit in DD01 alone, per the dedup notes); the sound loose files add more (about 894 MB WAV in the main set, only 76 MB matches stock, 49 MB shared). Sound is the part most worth examining.
- Compression estimate uses per-piece deflate; it loses cross-piece context, so a real packer could do slightly better or worse.
- A rebuilt zip is not byte-identical unless the deflate settings match. Verify by hash of the uncompressed member contents, not the zip file.
- The "new" data includes Dead Men content. This is not Dog Days data, but it is still the publisher's, and the player owns it only if they have Dead Men. See the legal note.

## 3) Recommended path

Ship the delta release (b). The solid 7z (a) is the fallback for a first quick test build, but at 4.9 GB it is still large, and it redistributes Dog Days data.

### Work needed

| Piece | What it does | Status |
|---|---|---|
| Packer (tools) | Cuts each map into pieces as the dedup run did. Writes only new pieces into a store (ideally lzma, one solid archive) and one recipe per map: ordered list of members, each made of (source: stock zip + member + range, or store piece id). Records the SHA1 of each rebuilt member and each final file. | to write; the dedup script D:\KL_size_1025\scripts\pieces.py is the starting point |
| Installer (player PC) | Reads the player's own Dog Days zips (and Dead Men if the recipe uses it), rebuilds each map zip into KLExpansion\Maps\<MAP>\, verifies every member by hash, refuses with a clear message if the player's stock files differ. Creates KL_PortBackup itself, never overwrites originals. | to write |
| Stock-version check | Hash the player's stock zips against the ones the recipes were built from (Steam build may differ). | to write |
| Loose files | WAV/WHD/.hti/_LS.SND treated the same way; sound is the least measured part. | to measure |

### Quick wins available now

| Win | Measured saving | Notes |
|---|---|---|
| Leave all .before* files out of the release | 17.63 GB (disk on the dev PC) | Zero risk. Already excluded from the solid 7z. |
| Archive or delete the 7 R folders + T01 | about 1.8 GB live, 6.8 GB logical | Needs the tool-list edits in 1a first. In a release they are already excluded. |
| Ship shared pieces once (delta method) | 1,712.1 MB of repeats across the main 21 maps | Part of the delta design, not a separate step. |
| Drop stale files (manifest.json, KLHook.expansion.ini, journals, test reports) | under 1 MB | Hygiene only. |
| Duplicate sound banks | not measured separately | Only the WAV numbers above exist: 894 MB WAV in the main set, 76 MB in stock, 49 MB shared. Measure per bank before claiming a saving. |
| Texture mip or format choices | not measured | No measurement exists. Do not quote a number. A lower-quality option would also change the look, so make it opt-in. |

### Legal note

Shipping only our own data and new pieces, and rebuilding the maps from the player's own Dog Days files, is also the cleaner way to avoid redistributing Dog Days assets. The same reasoning applies to Dead Men: if the recipes may point at the player's own Dead Men install, the download shrinks further (not measured here) and no publisher data is shipped. This is a design recommendation, not legal advice.

### Decisions needed from the owner

1. Move the 7 R folders and T01 to D:\KL_DD_archive_1025 (after the tool lists are edited)?
2. Pick the delta route as the target release?
3. Should recipes also source from the player's Dead Men install?
4. Are host64.off, GITC-Uplift and KLNR outside KL Merge?
