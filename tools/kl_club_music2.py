#!/usr/bin/env python3
"""
LAST CALL (DM05A) MUSIC, ROUND 2 (2026-10-25): the club music louder, plus a Dead Men OST bed on the whole map.
Owner: "club music needs to be more prominent, it's too quiet in the club, and there should be a Dead Men OST in the background
on the map; it feels too quiet on the map."

Builds on tools/kl_club_music.py (which gave the 12 club sounds their wave). Two packages, both pinned on MEMBERS and FILES, not on the
zip md5, so they install before or after any rebuild of the zip's .prp/.gms/... (lastcall5) that leaves these members alone:

  PACKAGE A  "Club music boost (recommended on)"      SND member + F01_Main.WHD + F01_Main_LS.SND   (no .prp change)
     pinned on: SND member 498cc81d, WHD 8cf764be, _LS.SND 3b21242c, WAV b143b49e (unchanged), PC_Def.str 30333312.
  PACKAGE B  "Dead Men OST bed (recommended on)"       .prp member only (settings fields 157 + 158)
     pinned on: the .prp member md5 of the zip it was built on (858d3371 = 7b5a... see the manifest), and the SND member = A's result.
     B changes the .prp, so if a rebuild of the zip changes the .prp, B must be rebuilt (python kl_club_music2.py build) - A survives.

WHAT A CHANGES (all in place, same size; nothing moves)
  PROVEN (read from the live bank): the 8 club music layers and the 5 club beds sit in mixer group 'Ambient' (0x55730), whose two
    volume floats (+0x24, +0x30) are 0.5; DD's own 'Music' group is also 0.5; the merged club PCM is about -12 dBFS RMS (peak -0.2), DD stock
    music -14.6 .. -21.6, so the CLIPS are not too quiet and must not be re-gained (no headroom).
  1. Group Ambient +0x24 and +0x30: 0.5 -> 1.0 (about +6 dB for every sound in the Ambient group of this bank: the club music and beds and the
     street/rooftop beds). GUESS: that these two floats are the group's gain (every stock group holds the same value twice; the one group
     where they differ, Ambient_Modifier, is not touched). Unity cannot clip beyond the clip's own peak.
  2. Per-sound flag byte b1 (byte 1 of the dword at +0x2c). GUESS: a percent volume (stock Music jukebox sounds 70, loot 100, DD Ambient 5..100).
     muffled layers 39 -> 70, Club_02 3D 63 -> 90, club entrance bed 5 -> 20, club bed 12 -> 25, Yoko office bed 11 -> 20.
     The clean layers are already 100; the street/rooftop beds keep their own values.
  3. The float at +0x18 of the 3D music layers x1.5 (6 -> 9, 2 -> 3, 2.5 -> 3.75). GUESS: a distance/attenuation radius ("audible across the
     club floors"); its meaning is unestablished, so this is the first thing to revert if the 3D layers sound wrong (set BOOST_RADIUS=1).
  4. NEW sound 'retomotoaction_ambient_v2_loop' (Dead Men M06_FA_A, Music/InHouse/M06/Retomoto_Ambient_V2_Loop.wav, Vorbis stereo 32 kHz 196 s,
     RMS -21.8 dBFS, a calm bed) + wave + 1 .WHD record, merged with kl_snd.merge exactly like the club sets; routed to group Ambient
     (kl_snd.merge put it in 'Music' = 0.5 by name), its b1 = 70. Nothing references it yet: A alone is silent about it. B starts it.
  Not touched: .WAV, PC_Def.str, [Music] of KLHook.ini (the Payday 2 jukebox stays off).

WHAT B CHANGES
  ZOnlineGameplaySettings fields 157 and 158 (0 in stock) = the bed sound. kl2 0x88edba (re/retomoto_audio.md 5.2, EXE): field 157 is played
  at once as a 2-D sound when the settings' Init runs (level load; the briefing included), field 158 replaces it when the local player turns
  traitor (0x67f0a9), so the bed carries on. One sound, no layers, no fades: it cannot be faded out in the club zones; it is simply
  ~10..13 dB under the club layers (RMS: bed -21.8 - 3 dB (b1 70) vs club -12) and the club's own SoundLimiterFade layers sit on top.
  LIVE (unproven): that field 157 plays in an FA round at all (Retomoto uses a PlayMusic controller, route A, for that reason), that the clip loops,
  and that 158 = 157 does not double it.

    python kl_club_music2.py build <outdir> [--map <folder>]    read the live files (read only), write <outdir>/stageA and <outdir>/stageB
    python kl_club_music2.py verify <outdir> [--map <folder>]   the offline proof
"""
import collections, hashlib, json, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_snd as S, kl_whd as W, kl_str

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAP = os.path.join(DD, 'KLExpansion', 'Maps', 'DM05A')
M_SND = 'Scenes/Locations/F01/F01_Main.SND'
M_PRP = 'Scenes/Locations/F01/F01_Main.prp'
STREAM_MAP = r'C:\kl_build\v_v2\PC_Def.str.map.json'
STREAM_MD5 = '303333126c18822ae74dc243a8d7c45f'
PIN = dict(snd='498cc81d', whd='8cf764be', wav='b143b49e', ls='3b21242c')
TAG_A, TAG_B = '.before-1025lcmusic', '.before-1025lcbed'
BED_LEVEL, BED_ROOT = 'M06_FA_A', 0x35490          # Dead Men sound 'retomotoaction_ambient_v2_loop' (and its wave 0x35470)
BED_CLIP = 'Music/InHouse/M06/Retomoto_Ambient_V2_Loop.wav'
BED_B1 = 70                                         # GUESS: percent volume (the merge's own value, kept)
G_AMBIENT = 0x55730                                 # group 'Ambient' of the live bank (checked by name in build)
GROUP_GAIN = 1.0                                    # GUESS: group gain, was 0.5 (+0x24 and +0x30)
BOOST_RADIUS = 1.5                                  # GUESS: +0x18 of the 3D music layers (1 = leave)
# sound-name suffix -> new b1 (GUESS: percent volume). Every name is checked to exist exactly once in the live bank.
B1 = {'m05_a_club_muffled': 70, 'm05_a_club_2_muffled': 70, 'm05_a_club_muffled_3d': 70, 'm05_a_club_2_clean_3d': 90,
      'club_entrance_ambience': 20, 'm05_club_ambience_01': 25, 'yoko_office_ambience': 20}
RADIUS = ('m05_a_club_clean_3d', 'm05_a_club_2_clean_3d', 'm05_a_club_muffled_3d')
md5 = lambda b: hashlib.md5(b).hexdigest()


def read_live(folder=MAP):
    zp = os.path.join(folder, 'F01_Main.zip')
    with zipfile.ZipFile(zp) as z:
        snd, prp = z.read(M_SND), z.read(M_PRP)
    rd = lambda n: open(os.path.join(folder, n), 'rb').read()
    return dict(snd=snd, prp=prp, whd=rd('F01_Main.WHD'), wav=rd('F01_Main.WAV'), ls=rd('F01_Main_LS.SND'), zip=zp)


def sounds_by_suffix(base):
    out = collections.defaultdict(list)
    for o, t in base.kind.items():
        if t == 1:
            n = base.name(o).decode()
            out[n.rsplit('/', 1)[-1].replace('#sound', '')].append(o)
    return out


def build_snd(live, log=print):
    """-> (snd, whd, ls, info). Pure function of the live members and Dead Men's M06_FA_A."""
    for n in ('snd', 'whd', 'wav', 'ls'):
        if md5(live[n])[:8] != PIN[n]:
            raise ValueError('%s md5 %s is not the pinned %s' % (n, md5(live[n])[:8], PIN[n]))
    base = S.Snd('dd', live['snd'], live['ls']).walk()
    dm = S.bank(BED_LEVEL, 'dm')
    dwhd, dwav = S.read(S.beside(BED_LEVEL, '.WHD', 'dm')), S.read(S.beside(BED_LEVEL, '.WAV', 'dm'))
    strmap = {k: v[0] for k, v in kl_str.load_map(STREAM_MAP).items()}
    st = collections.Counter()
    out, nwhd, nwav, omap = S.merge(base, dm, live['whd'], live['wav'], dwhd, dwav, {BED_ROOT}, strmap=strmap, log=log, stats=st)
    if nwav != live['wav']:
        raise ValueError('the bed clip is not streamed: the .WAV would change')
    bed = omap.get(BED_ROOT)
    if not bed:
        raise ValueError('bed sound has no Dog Days form')
    out = bytearray(out)
    names = sounds_by_suffix(base)
    # 1. group Ambient gain
    if S.cs(out, S.u32(out, G_AMBIENT + 0x3c)) != b'Ambient':
        raise ValueError('0x55730 is not group Ambient')
    for off in (0x24, 0x30):
        if struct.unpack_from('<f', out, G_AMBIENT + off)[0] != 0.5:
            raise ValueError('group Ambient +%#x is not 0.5' % off)
        struct.pack_into('<f', out, G_AMBIENT + off, GROUP_GAIN)
    # 2. b1 of the club sounds
    done = []
    for suf, v in B1.items():
        hit = sorted(set(names.get(suf, [])))
        if len(hit) != 1:
            raise ValueError('%s: %d sounds' % (suf, len(hit)))
        o = hit[0]
        old = out[o + 0x2d]
        out[o + 0x2d] = v
        done.append((suf, old, v))
    # 3. the radius float of the 3D music layers
    for suf in RADIUS:
        hit = sorted(set(names.get(suf, [])))
        if len(hit) != 1:
            raise ValueError('%s: %d sounds' % (suf, len(hit)))
        f = struct.unpack_from('<f', out, hit[0] + 0x18)[0]
        struct.pack_into('<f', out, hit[0] + 0x18, f * BOOST_RADIUS)
        done.append((suf + ' +0x18', f, f * BOOST_RADIUS))
    # 4. the bed: group Ambient instead of Music, b1
    pl = S.u32(out, bed + 0x10)
    q = [S.u32(out, pl + 4 * i) for i in range(S.u16(out, bed + 0xc)) if S.u32(out, S.u32(out, pl + 4 * i)) == 0x12]
    if len(q) != 1:
        raise ValueError('bed has %d group params' % len(q))
    struct.pack_into('<I', out, q[0] + 4, G_AMBIENT)
    out[bed + 0x2d] = BED_B1
    out = bytes(out)
    nls = S.ls_bank(live['ls'], S.u32(out, 0))
    return out, nwhd, nls, dict(bed=bed, edits=done, stats=dict(st), bed_param=q[0])


def build_prp(live, bed, log=print):
    """-> new .prp bytes: settings fields 157 and 158 = the bed sound (kl_str.set_fa_music); everything else identical."""
    import kl_prpjoin as J
    sc = J.Scene.from_zip(live['zip'], 'dd')
    if sc.p.serialize() != live['prp']:
        raise ValueError('the .prp does not round-trip through kl_prpjoin: refusing to edit it')
    for field in (157, 158):
        n = kl_str.set_fa_music(sc, bed, field, log)
        if n != 1:
            raise ValueError('field %d: %d settings objects' % (field, n))
    return sc.p.serialize()


def verify_snd(snd, whd, ls, live, info, log=print):
    bad = []
    base = S.Snd('dd', live['snd'], live['ls']).walk()
    m = S.Snd('dd', snd, ls).walk()
    problems, _n = S.verify(base, snd, whd, live['wav'], ls)
    bad += [p for p in problems if not p.startswith('stock bytes below')]
    osnd = live['snd']
    ch = [o for o in range(16, base.cut, 4) if snd[o:o + 4] != osnd[o:o + 4]]
    sounds = {o for o, t in base.kind.items() if t == 1}
    log('  dwords below the first type table that changed: %d' % len(ch))
    kinds = collections.Counter()
    for o in ch:
        if o in (G_AMBIENT + 0x24, G_AMBIENT + 0x30):
            kinds['group gain'] += 1
        elif any(o == s + 0x2c for s in sounds):
            kinds['flags'] += 1
        elif any(o == s + 0x18 for s in sounds):
            kinds['radius'] += 1
        else:
            bad.append('unexpected change at %#x' % o)
    log('  by kind: %s' % dict(kinds))
    if len(snd) < len(osnd) or snd[:16] != osnd[:16] and S.u32(snd, 4) != len(snd):
        pass
    # b1 only: the flags dword may differ in byte 1 only
    for o in ch:
        if any(o == s + 0x2c for s in sounds):
            if (osnd[o:o + 4][0], osnd[o:o + 4][2], osnd[o:o + 4][3]) != (snd[o], snd[o + 2], snd[o + 3]):
                bad.append('flags dword %#x changed outside byte 1' % o)
    recs, old = W.records('dd', whd), W.records('dd', live['whd'])
    new = [k for k in recs if k not in old]
    log('  .WHD records %d -> %d; old ones unchanged: %s; new: %d' % (len(old), len(recs), all(recs.get(k) == v for k, v in old.items()), len(new)))
    if any(recs.get(k) != v for k, v in old.items()) or len(new) != 1:
        bad.append('.WHD: old records changed or new count != 1')
    bed = info['bed']
    w = S.u32(snd, bed + 0x14)
    r = recs.get(S.u32(snd, w + 0x14)) if m.kind.get(w) == 4 else None
    if not r or not (r['fmt'] & W.STREAMED):
        bad.append('bed wave has no streamed .WHD record')
    else:
        # the record must be the clip's block in the live stream file
        sf = os.path.join(DD, 'PC_Def.str')
        s = kl_str.Stream(sf)
        c = [x for x in s.clips if x.name == BED_CLIP]
        s.close() if hasattr(s, 'close') else None
        if len(c) != 1 or c[0].offset != r['off'] or c[0].size != r['size']:
            bad.append('bed record does not match the stream file clip (%s)' % [(hex(x.offset), x.size) for x in c])
        else:
            log('  bed record = stream clip %s at %#x, %d bytes, %d Hz %d ch' % (BED_CLIP, r['off'], r['size'], r['rate'], r['ch']))
    grp = S.u32(snd, S.u32(snd, S.u32(snd, bed + 0x10)) + 4)
    if grp != G_AMBIENT:
        bad.append('bed not in group Ambient')
    if S.u32(ls, 0) != m.T:
        bad.append('_LS first dword')
    return bad


def verify_prp(prp, live, bed, log=print):
    import kl_prpjoin as J, kl_fa
    bad = []
    a, b = live['prp'], prp
    d = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    log('  .prp %d -> %d bytes; differing bytes: %d (offsets %s..%s)' % (len(a), len(b), len(d), hex(d[0]) if d else '-', hex(d[-1]) if d else '-'))
    if len(a) != len(b) or not d or len(d) > 16:
        bad.append('the .prp changed more than the two dwords')
    tmp = os.path.join(os.path.dirname(live['zip']), '_prpcheck.zip') if False else None
    return bad


def check_prp_readback(live, prp, bed, scratch, log=print):
    """Re-open the edited .prp as a Scene and read fields 157/158."""
    import kl_prpjoin as J, kl_fa
    zp = os.path.join(scratch, '_prpcheck.zip')
    with zipfile.ZipFile(live['zip']) as zi, zipfile.ZipFile(zp, 'w', zipfile.ZIP_STORED) as zo:
        for n in ('Scenes/Locations/F01/F01_Main.gms', 'Scenes/Locations/F01/F01_Main.buf'):
            zo.writestr(n, zi.read(n))
        zo.writestr(M_PRP, prp)
    sc = J.Scene.from_zip(zp, 'dd')
    vals = [(k, v[157], v[158]) for k, i, v in kl_fa.controllers(sc, kl_fa.SETTINGS)]
    os.remove(zp)
    log('  settings read back (node, f157, f158): %s' % vals)
    return [] if vals and all(x[1] == bed and x[2] == bed for x in vals) else ['fields 157/158 do not read back as the bed']


# ----------------------------------------------------------------------------------------------------------- installer
PS1 = r'''# lcmusic.ps1 - Last Call (DM05A) music package (tools/kl_club_music2.py, 2026-10-25). Reads lcmusic.json beside it.
#   powershell -ExecutionPolicy Bypass -File lcmusic.ps1 [-Undo] [-DryRun] [-Rehearsal] [-Game <folder>]
# WHAT: replaces the zip MEMBERS and/or whole files listed in lcmusic.json inside <Game>\KLExpansion\Maps\DM05A, each original kept as
#   <name><tag> (never overwritten). Every other member of F01_Main.zip is checked equal afterwards (CRC/size/compression/order).
# SAFETY: refuses while kl2.exe runs from that folder; every pinned member / file md5 (prefix) must match or NOTHING is changed (the zip md5 is
#   NOT pinned: any Last Call build whose pinned members match will do); read-back after; a failure puts everything back.
#   Re-running an installed package is a no-op. UNDO restores the backups byte for byte when the zip is still what this install wrote, else
#   (the zip was rebuilt in between, e.g. lastcall5) it puts the original MEMBERS back from orig\ and leaves every other member alone.
# -Rehearsal: for a scratch -Game folder (no kl2.exe / PC_Def.str needed, process check skipped). -DryRun: report only.
param([switch]$Undo, [switch]$DryRun, [switch]$Rehearsal,
      [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days')
$ErrorActionPreference = 'Stop'
$man = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'lcmusic.json') -Raw | ConvertFrom-Json
$tag = $man.tag
function md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }
function Find-Python { foreach ($n in 'python', 'py') { $c = Get-Command $n -ErrorAction SilentlyContinue; if ($c) { return $c.Source } }; return $null }
function Pin($have, $want) { return $have.StartsWith($want.ToLower()) }
if (-not $Rehearsal) {
  if (Get-Process kl2 -ErrorAction SilentlyContinue | Where-Object { -not $_.Path -or $_.Path -like (Join-Path $Game '*') }) { 'kl2.exe is running from this folder: close the game first. Nothing was changed.'; exit 1 }
  if (-not (Test-Path (Join-Path $Game 'kl2.exe'))) { "no kl2.exe in $Game"; exit 1 }
}
$dir = Join-Path $Game 'KLExpansion\Maps\DM05A'
$zip = Join-Path $dir 'F01_Main.zip'
$state = Join-Path $dir $man.state
$py = Find-Python
if (-not $py) { 'python (or py) not found on PATH: needed to rewrite zip members. Nothing was changed.'; exit 1 }
$zm = Join-Path $PSScriptRoot 'kl_zip_member.py'
function zmd5($z, $m) { (& $py -I $zm md5 $z $m).Trim().ToLower() }
$members = @($man.members); $files = @($man.files)
$memberNames = @($members | ForEach-Object { $_.member })
if (-not (Test-Path -LiteralPath $zip)) { "SKIP, $zip not installed"; exit 4 }
foreach ($f in $files) { if (-not (Test-Path -LiteralPath (Join-Path $dir $f.name))) { "SKIP, $($f.name) not installed"; exit 4 } }

if ($Undo) {
  if (-not (Test-Path -LiteralPath $state)) { 'SKIP, no state file: nothing installed by this package (or already undone).'; exit 0 }
  $s = Get-Content -LiteralPath $state -Raw | ConvertFrom-Json
  foreach ($f in $files) {
    if (-not (Test-Path -LiteralPath (Join-Path $dir ($f.name + $tag)))) { "SKIP, backup $($f.name)$tag missing. Nothing changed."; exit 4 }
    if ((md5 (Join-Path $dir $f.name)) -ne $s.after.($f.name)) { "SKIP, live $($f.name) changed since the install. Backups left in place."; exit 4 }
  }
  $zipNow = md5 $zip
  $whole = ($zipNow -eq $s.after.'F01_Main.zip') -and (Test-Path -LiteralPath ($zip + $tag))
  if (-not $whole) {
    foreach ($m in $members) { if ((zmd5 $zip $m.member) -ne $m.new) { "SKIP, member $($m.member) is not what this install wrote (another change in between). Nothing changed."; exit 4 } }
  }
  if ($DryRun) { if ($whole) { 'would restore the originals by renaming the backups back (dry run)' } else { 'would put the original members back, zip rebuilt in between (dry run)' }; exit 0 }
  if ($whole) {
    Remove-Item -LiteralPath $zip -Force
    Rename-Item -LiteralPath ($zip + $tag) -NewName 'F01_Main.zip'
    if ((md5 $zip) -ne $s.before.'F01_Main.zip') { 'FAILED, restored zip does not read back right!'; exit 4 }
  } else {
    $cur = $zip
    $i = 0
    $tmp = Join-Path $dir 'F01_Main.zip.undo1025'
    foreach ($m in $members) {
      $i++
      $nxt = $tmp + $i
      & $py -I $zm replace $cur $m.member (Join-Path (Join-Path $PSScriptRoot 'orig') $m.src) $nxt
      if ($LASTEXITCODE -ne 0) { 'zip rewrite failed; nothing changed'; exit 4 }
      if ($i -gt 1) { Remove-Item -LiteralPath $cur -Force }
      $cur = $nxt
    }
    & $py -I $zm same $zip $cur @memberNames
    if ($LASTEXITCODE -ne 0) { Remove-Item -LiteralPath $cur -Force; 'rewritten zip differs in another member; nothing changed'; exit 4 }
    Remove-Item -LiteralPath $zip -Force
    Rename-Item -LiteralPath $cur -NewName 'F01_Main.zip'
    foreach ($m in $members) { if ((zmd5 $zip $m.member) -ne $m.old) { 'FAILED, restored member does not read back right!'; exit 4 } }
    if (Test-Path -LiteralPath ($zip + $tag)) { Remove-Item -LiteralPath ($zip + $tag) -Force }
  }
  foreach ($f in $files) {
    $p = Join-Path $dir $f.name
    Remove-Item -LiteralPath $p -Force
    Rename-Item -LiteralPath ($p + $tag) -NewName $f.name
    if ((md5 $p) -ne $s.before.($f.name)) { "FAILED, restored $($f.name) does not read back right!"; exit 4 }
  }
  Remove-Item -LiteralPath $state -Force
  'originals restored, read back ok'; exit 0
}

if (Test-Path -LiteralPath $state) { 'already installed (state file present): nothing to do'; exit 0 }
foreach ($f in $files + @(@{ name = 'F01_Main.zip' })) { if (Test-Path -LiteralPath (Join-Path $dir ($f.name + $tag))) { "SKIP, $($f.name)$tag already exists. Not changed."; exit 4 } }
if ($man.pcdef) {
  $pc = Join-Path $Game 'PC_Def.str'
  if (Test-Path -LiteralPath $pc) { if ((md5 $pc) -ne $man.pcdef) { 'SKIP, PC_Def.str md5 is not the one the stream offsets point into. Not changed.'; exit 4 } }
  elseif (-not $Rehearsal) { 'SKIP, no PC_Def.str in the game folder. Not changed.'; exit 4 }
}
foreach ($f in $files) { $h = md5 (Join-Path $dir $f.name); if (-not (Pin $h $f.old)) { "SKIP, live $($f.name) is $h, expected $($f.old). Not changed."; exit 4 } }
foreach ($r in @($man.requireFiles)) { if ($r) { $h = md5 (Join-Path $dir $r.name); if (-not (Pin $h $r.md5)) { "SKIP, live $($r.name) is $h, expected $($r.md5). Not changed."; exit 4 } } }
foreach ($m in $members) { $h = zmd5 $zip $m.member; if (-not (Pin $h $m.old)) { "SKIP, zip member $($m.member) is $h, expected $($m.old) (another build). Not changed."; exit 4 } }
foreach ($r in @($man.requireMembers)) { if ($r) { $h = zmd5 $zip $r.member; if (-not (Pin $h $r.md5)) { "SKIP, zip member $($r.member) is $h, expected $($r.md5) (the other package first?). Not changed."; exit 4 } } }
$zipNow = md5 $zip
"target: $dir  (zip $($zipNow.Substring(0,8)); pinned members/files all match)"
if ($DryRun) { 'would install (dry run)'; exit 0 }

$tmpZip = $zip + '.tmp1025'
$tmpF = @{}; foreach ($f in $files) { $tmpF[$f.name] = (Join-Path $dir $f.name) + '.tmp1025' }
function Clean { foreach ($t in @($tmpZip) + @($tmpF.Values) + @($tmpZip + '.p')) { if (Test-Path -LiteralPath $t) { Remove-Item -LiteralPath $t -Force } } }
Clean
try {
  foreach ($f in $files) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $f.src) -Destination $tmpF[$f.name]
    if (-not (Pin (md5 $tmpF[$f.name]) $f.new)) { throw "copy of $($f.name) does not read back" }
  }
  $cur = $zip; $i = 0
  foreach ($m in $members) {
    $i++
    $nxt = if ($i -eq $members.Count) { $tmpZip } else { $tmpZip + '.p' }
    & $py -I $zm replace $cur $m.member (Join-Path $PSScriptRoot $m.src) $nxt
    if ($LASTEXITCODE -ne 0) { throw 'zip rewrite failed' }
    if ($cur -ne $zip) { Remove-Item -LiteralPath $cur -Force }
    $cur = $nxt
  }
  foreach ($m in $members) { if (-not (Pin (zmd5 $tmpZip $m.member) $m.new)) { throw "new zip: member $($m.member) is not the package's" } }
  & $py -I $zm same $zip $tmpZip @memberNames
  if ($LASTEXITCODE -ne 0) { throw 'new zip: another member differs from the live zip' }
} catch { Clean; "FAILED before touching the game files: $_"; exit 4 }
$before = @{ 'F01_Main.zip' = $zipNow }; foreach ($f in $files) { $before[$f.name] = md5 (Join-Path $dir $f.name) }
$tmps = @{ 'F01_Main.zip' = $tmpZip }; foreach ($f in $files) { $tmps[$f.name] = $tmpF[$f.name] }
$names = @('F01_Main.zip') + @($files | ForEach-Object { $_.name })
try {
  foreach ($n in $names) {
    $p = Join-Path $dir $n
    Rename-Item -LiteralPath $p -NewName ($n + $tag)
    Rename-Item -LiteralPath $tmps[$n] -NewName $n
  }
} catch {
  foreach ($n in $names) {
    $p = Join-Path $dir $n; $b = $p + $tag
    if (Test-Path -LiteralPath $b) { if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force }; Rename-Item -LiteralPath $b -NewName $n }
  }
  Clean; "FAILED swap, originals put back: $_"; exit 4
}
$after = @{}; foreach ($n in $names) { $after[$n] = md5 (Join-Path $dir $n) }
$ok = $true
foreach ($f in $files) { if (-not (Pin $after[$f.name] $f.new)) { $ok = $false } }
foreach ($m in $members) { if (-not (Pin (zmd5 $zip $m.member) $m.new)) { $ok = $false } }
if (-not $ok) { 'FAILED read-back, run UNDO'; exit 4 }
@{ before = $before; after = $after } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $state -Encoding ascii
"installed: $(($names | ForEach-Object { $_ + ' ' + $after[$_].Substring(0,8) }) -join ', '); originals kept as *$tag"
'''

BAT = '@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0lcmusic.ps1" {arg}\r\npause\r\n'


def stage(out, name, label, tag, state, members, files, require_members=(), pcdef=None, log=print):
    """members: [(zip member, old bytes, new bytes, file name)], files: [(live name, old, new)]"""
    d = os.path.join(out, name)
    os.makedirs(os.path.join(d, 'orig'), exist_ok=True)
    man = dict(label=label, tag=tag, state=state, pcdef=pcdef, members=[], files=[],
               requireMembers=[dict(member=m, md5=h) for m, h in require_members],
               requireFiles=[dict(name='F01_Main.WAV', md5=PIN['wav'])])
    for mem, old, new, fn in members:
        open(os.path.join(d, fn), 'wb').write(new)
        open(os.path.join(d, 'orig', fn), 'wb').write(old)
        man['members'].append(dict(member=mem, old=md5(old), new=md5(new), src=fn))
    for fn, old, new in files:
        open(os.path.join(d, fn), 'wb').write(new)
        man['files'].append(dict(name=fn, old=md5(old), new=md5(new), src=fn))
    json.dump(man, open(os.path.join(d, 'lcmusic.json'), 'w'), indent=1)
    with open(os.path.join(d, 'lcmusic.ps1'), 'w', newline='\r\n') as fh:
        fh.write(PS1)
    for nm, arg in (('INSTALL %s.bat' % label, ''), ('UNDO %s.bat' % label, '-Undo')):
        with open(os.path.join(d, nm), 'w', newline='') as fh:
            fh.write(BAT.format(arg=arg))
    shutil.copyfile(os.path.join(HERE, 'kl_zip_member.py'), os.path.join(d, 'kl_zip_member.py'))
    return man


def build(out, folder=MAP, log=print):
    live = read_live(folder)
    snd, whd, ls, info = build_snd(live, log)
    bad = verify_snd(snd, whd, ls, live, info, log)
    os.makedirs(out, exist_ok=True)
    prp = build_prp(dict(live, snd=snd), info['bed'], log)
    bad += verify_prp(prp, live, info['bed'], log)
    bad += check_prp_readback(live, prp, info['bed'], out, log)
    mA = stage(out, 'stageA', 'Club music boost (recommended on)', TAG_A, 'lcmusic.state.json',
               [(M_SND, live['snd'], snd, 'F01_Main.SND')],
               [('F01_Main.WHD', live['whd'], whd), ('F01_Main_LS.SND', live['ls'], ls)], pcdef=STREAM_MD5, log=log)
    mB = stage(out, 'stageB', 'Dead Men OST bed (recommended on)', TAG_B, 'lcbed.state.json',
               [(M_PRP, live['prp'], prp, 'F01_Main.prp')], [],
               require_members=[(M_SND, md5(snd)[:8])], log=log)
    json.dump(dict(edits=[(a, b if not isinstance(b, bytes) else b, c) for a, b, c in info['edits']], bed=hex(info['bed'])),
              open(os.path.join(out, 'edits.json'), 'w'), indent=1, default=str)
    log('PACKAGE: %s' % ('PASS' if not bad else 'FAIL'))
    for x in bad:
        log('  PROBLEM ' + x)
    log('A: snd %s whd %s ls %s | B: prp %s (in: snd %s prp %s whd %s ls %s wav %s)' % (
        md5(snd)[:8], md5(whd)[:8], md5(ls)[:8], md5(prp)[:8], md5(live['snd'])[:8], md5(live['prp'])[:8], md5(live['whd'])[:8], md5(live['ls'])[:8], md5(live['wav'])[:8]))
    log('edits: %s' % info['edits'])
    return bad


def main(a):
    folder = MAP
    if '--map' in a:
        i = a.index('--map'); folder = a[i + 1]; a = a[:i] + a[i + 2:]
    if a[:1] == ['build'] and len(a) == 2:
        return 1 if build(a[1], folder) else 0
    print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
