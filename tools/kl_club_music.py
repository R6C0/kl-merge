#!/usr/bin/env python3
"""
LAST CALL (DM05A) MUSIC + AMBIENCE: the sound-bank package that gives the club's 13 clips their .WHD records.

WHY IT WAS SILENT (measured 2026-10-25 on the live DM05A, md5 7ef0404f)
  The build (kl_fa_club.py -> kl_maps.one -> kl_snd.graft_audio) ran when PC_Def.str did not hold the club's blocks yet:
  merge() found no stream-file offset for them, so it copied the 12 NAMED sound objects of M05_A's music and ambience but left
  their wave pointer (+0x14) at 0 and added no .WHD record ('stream clips not in the merged stream file', the KNOWN item of
  kl_fa_club.py). PC_Def.str (= C:/kl_build/v_v2/PC_Def.str, 30333312) holds all 7 blocks since: this package adds the records.
  Live .SND (member Scenes/Locations/F01/F01_Main.SND of F01_Main.zip, db239c34, identical in lastcall2/lastcall3 main/alt):
  12 sounds with wave 0: 7 music layers + 5 ambience beds. The 8th music layer (2_Muffled_3D) is named by no object; it is the 4th
  record of its interleaved group and comes with it (13 .WHD records for 12 waves).

WHAT IT DOES (kl_snd.merge with roots = the 12 Dead Men wave objects; nothing else is reached)
  - .SND: kl_snd.merge appends the 12 wave objects (+ their name strings, the type-4 table grown) behind the base's objects; every
    byte below the first type table stays, EXCEPT 12 dwords: the wave pointer (+0x14) of the 12 existing sounds, from 0 to the new
    wave (the one thing merge() cannot do for a sound the base already has). Counts: waves 5134 -> 5146.
  - .WHD: 13 streamed records appended (two interleaved 4-layer groups + 5 single ambience beds), every old record where it was.
    Offsets into PC_Def.str come from v_v2's .map.json (Dead Men block -> the file the game folder has).
  - .WAV: unchanged (all 13 are streamed: the bytes are in PC_Def.str). md5 pinned all the same.
  - _LS.SND: first dword = the new trailer T (kl_snd.ls_bank; graft_audio does this for every build, equal in 40 of 40 stock pairs).
  - PC_Def.str: NOT touched (it already has the 7 blocks; the proof compares them with Dead Men's bytes).
  - F01_Main.zip: MUST change, because the .SND is a member of it (the engine reads the bank from the archive). Only that member:
    kl_zip_member.py rewrites the zip with every other member the same (CRC/size/compression/order checked). The member is
    identical in every Last Call build so far (db239c34), so the package applies to ANY F01_Main.zip whose SND member is db239c34
    (install lastcall3 first or after: the installer pins the member, not the zip).
  [Music] Enable (the Payday 2 jukebox in KLHook.ini) is not read or written.

    python kl_club_music.py build <outdir>      read the live files (read only), write the package files + installer
    python kl_club_music.py verify <outdir>     the offline proof (also run by build)
"""
import collections, hashlib, json, os, struct, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_snd as S, kl_whd as W, kl_str, kl_club_str as C, kl_vault_str as V

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAP = os.path.join(DD, 'KLExpansion', 'Maps', 'DM05A')
MEMBER = 'Scenes/Locations/F01/F01_Main.SND'
ZIPNAME, WHDNAME, WAVNAME, LSNAME = 'F01_Main.zip', 'F01_Main.WHD', 'F01_Main.WAV', 'F01_Main_LS.SND'
STREAM_MAP = r'C:\kl_build\v_v2\PC_Def.str.map.json'
STREAM_MD5 = '303333126c18822ae74dc243a8d7c45f'          # the live PC_Def.str (= v_v2's) the offsets point into
PIN = dict(snd='db239c34', whd='21a2b9a4', wav='b143b49e', ls='6a579c2b')   # md5 prefixes of what the package was built on
TAG = '.before-1025clubmusic'
CLIPS = {x.lower() for x in C.CLIPS}
md5 = lambda b: hashlib.md5(b).hexdigest()
cs = S.cs


def norm(n):
    return n.decode('latin1').replace('\\', '/').lower()


def read_live(folder=MAP):
    with zipfile.ZipFile(os.path.join(folder, ZIPNAME)) as z:
        snd = z.read(MEMBER)
    rd = lambda n: open(os.path.join(folder, n), 'rb').read()
    return snd, rd(WHDNAME), rd(WAVNAME), rd(LSNAME)


def build_bank(snd, whd, wav, ls, log=print):
    """-> (snd, whd, wav, ls, info) of the merged package. Pure function of the four live files and Dead Men's M05_A."""
    for n, b in (('snd', snd), ('whd', whd), ('wav', wav), ('ls', ls)):
        if md5(b)[:8] != PIN[n]:
            raise ValueError('%s md5 %s is not the pinned %s: the package was built on another bank' % (n, md5(b)[:8], PIN[n]))
    base = S.Snd('dd', snd, ls).walk()
    dm = S.bank('M05_A', 'dm')
    dm_whd, dm_wav = S.read(S.beside('M05_A', '.WHD', 'dm')), S.read(S.beside('M05_A', '.WAV', 'dm'))
    drecs = W.records('dm', dm_whd)
    strmap = {k: v[0] for k, v in kl_str.load_map(STREAM_MAP).items()}
    by = collections.defaultdict(list)
    for o, t in base.kind.items():
        if t == 1:
            by[S.cs(base.b, S.u32(base.b, o + 8))].append(o)
    pairs, seen = [], collections.OrderedDict()                       # (base sound, Dead Men wave), clip name
    for o, t in sorted(dm.kind.items()):
        w = S.u32(dm.b, o + 0x14) if t == 1 else 0
        if not w or w >= dm.T or dm.kind.get(w) != 4:
            continue
        r = drecs.get(S.u32(dm.b, w + 0x14))
        clip = norm(cs(dm_whd, r['name'])) if r else None
        if clip not in CLIPS:
            continue
        hit = by.get(dm.b[S.u32(dm.b, o + 8):dm.b.index(b'\0', S.u32(dm.b, o + 8))], [])
        if len(hit) != 1:
            raise ValueError('sound %s: %d objects of that name in the live bank' % (dm.name(o), len(hit)))
        if S.u32(base.b, hit[0] + 0x14):
            raise ValueError('sound %s already has a wave' % dm.name(o))
        pairs.append((hit[0], w)); seen[clip] = o
    log('  %d sounds of the live bank get a wave; clips named by them: %d of %d (the rest comes with an interleaved block)' % (
        len(pairs), len(seen), len(CLIPS)))
    st = collections.Counter()
    out, nwhd, nwav, omap = S.merge(base, dm, whd, wav, dm_whd, dm_wav, {w for _s, w in pairs}, strmap=strmap, log=log, stats=st)
    out = bytearray(out)
    for s, w in pairs:
        if not omap.get(w):
            raise ValueError('wave %#x of Dead Men has no Dog Days form' % w)
        struct.pack_into('<I', out, s + 0x14, omap[w])
    out = bytes(out)
    nls = S.ls_bank(ls, S.u32(out, 0))
    return out, nwhd, nwav, nls, dict(pairs=[(s, w, omap[w]) for s, w in pairs], stats=dict(st), clips=list(seen))


def verify_bank(snd, whd, wav, ls, live, folder, log=print):
    """The offline proof. live = (snd, whd, wav, ls) of the live files. -> [problems]"""
    osnd, owhd, owav, ols = live
    bad = []
    base = S.Snd('dd', osnd, ols).walk()
    m = S.Snd('dd', snd, ls).walk()
    problems, n = S.verify(base, snd, whd, wav, ls)
    bad += [p for p in problems if not p.startswith('stock bytes below')]
    # the only changed bytes below the first type table: the 12 wave pointers (0 -> a wave object)
    ch = [o for o in range(16, base.cut, 4) if snd[o:o + 4] != osnd[o:o + 4]]
    sounds = {o: t for o, t in base.kind.items() if t == 1}
    log('  bytes below the first type table that changed: %d dwords: %s' % (len(ch), 'all are wave pointers of sounds, old 0' if all(
        o - 0x14 in sounds and S.u32(osnd, o) == 0 for o in ch) else 'NOT ALL'))
    if not all(o - 0x14 in sounds and S.u32(osnd, o) == 0 for o in ch):
        bad.append('a changed dword is not a 0 wave pointer of a sound')
    if snd[:16] != osnd[:16] and (S.u32(snd, 4) != len(snd)):
        bad.append('size field')
    # every audio node: sound -> wave -> .WHD record (streamed, resolves into PC_Def.str, rate/channels = the index entry)
    recs = W.records('dd', whd)
    old = W.records('dd', owhd)
    if any(recs.get(k) != v for k, v in old.items()):
        bad.append('an old .WHD record changed')
    log('  .WHD records %d -> %d (old ones all unchanged: %s); .WAV %s' % (len(old), len(recs), all(recs.get(k) == v for k, v in old.items()),
                                                                      'unchanged' if wav == owav else 'CHANGED'))
    if wav != owav:
        bad.append('.WAV changed')
    nsound = 0
    for o in sorted(sounds):
        if S.u32(snd, o + 0x14) != S.u32(osnd, o + 0x14):
            w = S.u32(snd, o + 0x14)
            ok = m.kind.get(w) == 4 and S.u32(snd, w) in (0, 4)
            r = recs.get(S.u32(snd, w + 0x14)) if ok else None
            nsound += 1
            if not r:
                bad.append('sound %s: wave %#x -> no .WHD record' % (cs(snd, S.u32(snd, o + 8)), w))
    log('  audio nodes now resolving: %d sounds -> wave -> .WHD record' % nsound)
    if ls and S.u32(ls, 0) != m.T:
        bad.append('_LS first dword')
    # the stream side: klshort whd check of kl_club_str on a folder that holds the new .WHD
    tmp = os.path.join(folder, 'proof')
    os.makedirs(tmp, exist_ok=True)
    open(os.path.join(tmp, 'F01_Main.WHD'), 'wb').write(whd)
    sf = os.path.join(os.path.dirname(STREAM_MAP), 'PC_Def.str')
    log('  --- stream proof (kl_club_str whd: 13 records, each = Dead Men\'s block bytes, rate/channels/size = the index entry)')
    bad += C.V.whd(sf, tmp, log=log, names=C.CLIPS)
    # codec / rate of the 13 against the bank's own streamed music-like records (informational, the engine decodes by the record's fmt)
    fm = collections.Counter()
    names = {}
    for at, f in recs.items():
        if at >= S.u32(owhd, 0) and f['fmt'] & W.STREAMED:
            fm[(f['fmt'] & 0xffff, f['fmt'] >> 24, f['rate'], f['ch'])] += 1
    log('  new records by (codec, group byte, rate, channels): %s' % dict(fm))
    stock = collections.Counter((f['fmt'] & 0xffff, f['rate'], f['ch']) for f in old.values() if f['fmt'] & W.STREAMED and f['fmt'] >> 24)
    log('  old grouped stream records of the bank by (codec, rate, channels): %s' % dict(stock.most_common(6)))
    return bad


def ps1():
    return PS1


PS1 = r'''# clubmusic.ps1 - Last Call (DM05A): the club's music + ambience (tools/kl_club_music.py, 2026-10-25).
#   powershell -ExecutionPolicy Bypass -File clubmusic.ps1 [-Undo] [-DryRun] [-Game <folder>]
# WHAT: three files of KLExpansion\Maps\DM05A change, each backed up with the suffix .before-1025clubmusic (never overwritten):
#   F01_Main.WHD (13 stream records appended), F01_Main_LS.SND (first dword), and F01_Main.zip - ONLY its member
#   Scenes/Locations/F01/F01_Main.SND (12 sounds get their wave) - via python kl_zip_member.py; all other members are checked equal after.
#   F01_Main.WAV and PC_Def.str are not touched. KLHook.ini ([Music] = the Payday 2 jukebox) is not touched.
# SAFETY: refuses while kl2.exe runs; the SND member / WHD / LS md5 must be the ones this was built on (the zip may be ANY Last Call
#   build: lastcall2/3 main/alt all carry the same member); PC_Def.str md5 must be the one the offsets point into; read-back after;
#   a failure puts everything back. UNDO only when the live files are exactly what this install wrote (state file clubmusic.state.json
#   in the map folder), then renames the three backups back (byte identical).
param([switch]$Undo, [switch]$DryRun,
      [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days')
$ErrorActionPreference = 'Stop'
$tag = '.before-1025clubmusic'
$man = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'clubmusic.json') -Raw | ConvertFrom-Json
function md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }
function Find-Python {
  foreach ($n in 'python', 'py') { $c = Get-Command $n -ErrorAction SilentlyContinue; if ($c) { return $c.Source } }
  return $null
}
if (Get-Process kl2 -ErrorAction SilentlyContinue | Where-Object { -not $_.Path -or $_.Path -like (Join-Path $Game '*') }) { 'kl2.exe is running from this folder: close the game first. Nothing was changed.'; exit 1 }
if (-not (Test-Path (Join-Path $Game 'kl2.exe'))) { "no kl2.exe in $Game"; exit 1 }
$dir = Join-Path $Game 'KLExpansion\Maps\DM05A'
$state = Join-Path $dir 'clubmusic.state.json'
$files = @('F01_Main.zip', 'F01_Main.WHD', 'F01_Main_LS.SND')
foreach ($f in $files) { if (-not (Test-Path -LiteralPath (Join-Path $dir $f))) { "SKIP, $dir\$f not installed"; exit 4 } }
$py = Find-Python
if (-not $py) { 'python (or py) not found on PATH: needed to rewrite the one zip member. Nothing was changed.'; exit 1 }
$zm = Join-Path $PSScriptRoot 'kl_zip_member.py'
$member = 'Scenes/Locations/F01/F01_Main.SND'
function zipsnd($z) { (& $py -I $zm md5 $z $member).Trim().ToLower() }

if ($Undo) {
  if (-not (Test-Path -LiteralPath $state)) { 'SKIP, no clubmusic.state.json: nothing installed by this package (or already undone).'; exit 0 }
  $s = Get-Content -LiteralPath $state -Raw | ConvertFrom-Json
  foreach ($f in $files) {
    if (-not (Test-Path -LiteralPath (Join-Path $dir ($f + $tag)))) { "SKIP, backup $f$tag missing. Nothing changed."; exit 4 }
    if ((md5 (Join-Path $dir $f)) -ne $s.after.$f) { "SKIP, live $f changed since the install (another install in between?). Backups left in place."; exit 4 }
  }
  if ($DryRun) { 'would restore the three originals (dry run)'; exit 0 }
  foreach ($f in $files) {
    $p = Join-Path $dir $f
    Remove-Item -LiteralPath $p -Force
    Rename-Item -LiteralPath ($p + $tag) -NewName $f
    if ((md5 $p) -ne $s.before.$f) { "FAILED, restored $f does not read back right!"; exit 4 }
  }
  Remove-Item -LiteralPath $state -Force
  'originals restored, read back ok'; exit 0
}

if (Test-Path -LiteralPath $state) { 'already installed (state file present)'; exit 0 }
foreach ($f in $files) { if (Test-Path -LiteralPath (Join-Path $dir ($f + $tag))) { "SKIP, $f$tag already exists. Not changed."; exit 4 } }
$pc = Join-Path $Game 'PC_Def.str'
if ((md5 $pc) -ne $man.pcdef) { "SKIP, PC_Def.str md5 is not the one the stream offsets point into ($($man.pcdef.Substring(0,8))). Not changed."; exit 4 }
$whdNow = md5 (Join-Path $dir 'F01_Main.WHD'); $lsNow = md5 (Join-Path $dir 'F01_Main_LS.SND')
if ($whdNow -ne $man.old.whd) { "SKIP, live WHD is $whdNow, expected $($man.old.whd). Not changed."; exit 4 }
if ($lsNow -ne $man.old.ls) { "SKIP, live _LS.SND is $lsNow, expected $($man.old.ls). Not changed."; exit 4 }
$zipNow = md5 (Join-Path $dir 'F01_Main.zip')
$sndNow = zipsnd (Join-Path $dir 'F01_Main.zip')
if ($sndNow -ne $man.old.snd) { "SKIP, the zip's SND member is $sndNow, expected $($man.old.snd) (a build with another sound bank). Not changed."; exit 4 }
"target: $dir  (zip $($zipNow.Substring(0,8)), SND member $($sndNow.Substring(0,8)) -> $($man.new.snd.Substring(0,8)))"
if ($DryRun) { 'would install (dry run)'; exit 0 }

$tmpZip = Join-Path $dir 'F01_Main.zip.tmp1025'; $tmpWhd = Join-Path $dir 'F01_Main.WHD.tmp1025'; $tmpLs = Join-Path $dir 'F01_Main_LS.SND.tmp1025'
foreach ($t in $tmpZip, $tmpWhd, $tmpLs) { if (Test-Path -LiteralPath $t) { Remove-Item -LiteralPath $t -Force } }
try {
  Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'F01_Main.WHD') -Destination $tmpWhd
  Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'F01_Main_LS.SND') -Destination $tmpLs
  if ((md5 $tmpWhd) -ne $man.new.whd -or (md5 $tmpLs) -ne $man.new.ls) { throw 'copy of the .WHD / _LS.SND does not read back' }
  & $py -I $zm replace (Join-Path $dir 'F01_Main.zip') $member (Join-Path $PSScriptRoot 'F01_Main.SND') $tmpZip
  if ($LASTEXITCODE -ne 0) { throw 'zip rewrite failed' }
  if ((zipsnd $tmpZip) -ne $man.new.snd) { throw 'new zip: the SND member is not the package''s' }
  & $py -I $zm same (Join-Path $dir 'F01_Main.zip') $tmpZip $member
  if ($LASTEXITCODE -ne 0) { throw 'new zip: another member differs from the live zip' }
} catch {
  foreach ($t in $tmpZip, $tmpWhd, $tmpLs) { if (Test-Path -LiteralPath $t) { Remove-Item -LiteralPath $t -Force } }
  "FAILED before touching the game files: $_"; exit 4
}
$before = @{}; foreach ($f in $files) { $before[$f] = md5 (Join-Path $dir $f) }
$tmps = @{ 'F01_Main.zip' = $tmpZip; 'F01_Main.WHD' = $tmpWhd; 'F01_Main_LS.SND' = $tmpLs }
$done = @()
try {
  foreach ($f in $files) {
    $p = Join-Path $dir $f
    Rename-Item -LiteralPath $p -NewName ($f + $tag)
    Rename-Item -LiteralPath $tmps[$f] -NewName $f
    $done += $f
  }
} catch {
  foreach ($f in $done + @()) { }
  foreach ($f in $files) {
    $p = Join-Path $dir $f; $b = $p + $tag
    if (Test-Path -LiteralPath $b) { if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force }; Rename-Item -LiteralPath $b -NewName $f }
  }
  foreach ($t in $tmpZip, $tmpWhd, $tmpLs) { if (Test-Path -LiteralPath $t) { Remove-Item -LiteralPath $t -Force } }
  "FAILED swap, originals put back: $_"; exit 4
}
$after = @{}; foreach ($f in $files) { $after[$f] = md5 (Join-Path $dir $f) }
if ($after['F01_Main.WHD'] -ne $man.new.whd -or $after['F01_Main_LS.SND'] -ne $man.new.ls -or (zipsnd (Join-Path $dir 'F01_Main.zip')) -ne $man.new.snd) { 'FAILED read-back, run UNDO'; exit 4 }
@{ before = $before; after = $after } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $state -Encoding ascii
"installed: .WHD $($after['F01_Main.WHD'].Substring(0,8)), _LS.SND $($after['F01_Main_LS.SND'].Substring(0,8)), zip $($after['F01_Main.zip'].Substring(0,8)); originals kept as *$tag"
'''

BAT = '@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0clubmusic.ps1" {arg}\r\npause\r\n'


def write_package(out, log=print):
    live = read_live()
    snd, whd, wav, ls, info = build_bank(*live, log=log)
    os.makedirs(out, exist_ok=True)
    for n, b in (('F01_Main.SND', snd), ('F01_Main.WHD', whd), ('F01_Main_LS.SND', ls)):
        open(os.path.join(out, n), 'wb').write(b)
    man = dict(old=dict(snd=md5(live[0]), whd=md5(live[1]), wav=md5(live[2]), ls=md5(live[3])),
               new=dict(snd=md5(snd), whd=md5(whd), wav=md5(wav), ls=md5(ls)),
               pcdef=STREAM_MD5, tag=TAG, member=MEMBER, pairs=['%#x %#x %#x' % p for p in info['pairs']])
    json.dump(man, open(os.path.join(out, 'clubmusic.json'), 'w'), indent=1)
    with open(os.path.join(out, 'clubmusic.ps1'), 'w', newline='\r\n') as fh:
        fh.write(PS1)
    for nm, arg in (('INSTALL clubmusic.bat', ''), ('UNDO clubmusic.bat', '-Undo')):
        with open(os.path.join(out, nm), 'w', newline='') as fh:
            fh.write(BAT.format(arg=arg))
    import shutil
    shutil.copyfile(os.path.join(HERE, 'kl_zip_member.py'), os.path.join(out, 'kl_zip_member.py'))
    bad = verify_bank(snd, whd, wav, ls, live, out, log)
    log('PACKAGE: %s' % ('PASS' if not bad else 'FAIL'))
    for x in bad:
        log('  PROBLEM ' + x)
    log('md5 in : %s' % man['old']); log('md5 out: %s' % man['new'])
    return bad


def main(a):
    if a[:1] == ['build'] and len(a) == 2:
        return 1 if write_package(a[1]) else 0
    if a[:1] == ['verify'] and len(a) == 2:
        live = read_live()
        d = lambda n: open(os.path.join(a[1], n), 'rb').read()
        bad = verify_bank(d('F01_Main.SND'), d('F01_Main.WHD'), live[2], d('F01_Main_LS.SND'), live, a[1])
        print('VERIFY:', 'PASS' if not bad else bad)
        return 1 if bad else 0
    print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
