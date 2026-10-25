"""kl_vans_1025.py - DATA pass 'shootable vans and cars' (owner 2026-10-25: "make sure you can shoot the vans ... idk if it actually blows up,
same for the feds and AI, they should be able to shoot it too"; police cars / civilian cars too). Written 2026-10-25. Companion of the
hook's [VanBlow] (klhook/klescort.c, e8's area); a hook proposal is in re/vans_1025.md.

WHAT THE AUDIT FOUND (re/vans_1025.md has the detail): the escape van (key-framed ZAnimatedVehicle, health 9600 in the file, Arcade picks one of the
seven numbers 9600/10000/8000/3000/5000/7000/10000) is shielded by the hook while a crew is aboard, vulnerable while empty; a bullet that
lands subtracts weapon damage x scale, so 9600 hp is effectively unshootable. Police AI shoot a van only through the FakeTarget ('Mercenary') on
Body_Main; Dog Days' maps and DM01/DM02/DM03/DM09 have it, DM01B / DM03A / DM06B had it taken off (van_late builds). Dead Men's parked cars
(VehicleEffects, BlowupChance) are Definite on DM01/05A/06/09 but None on DM01B (46 cars), DM02/DM03/DM03A (1-2) and DM11B (1).

THREE FEATURES, each a switch of the builder (--features ft,vanhp,cars; default all) and, at install time, a per-map install (-Maps):
  ft     the stock FakeTarget controller (copied from the DM02 van body: 'Mercenary', -1, '', 20.0, [], 0, 1, 0.0, 0.0) back on the van's
         Body_Main where a map lost it. SAFE ONLY INSIDE THE VISION GRID (re/crash_686a66.md, 0x686a66): the builder reads the grid with
         kl_fa_bots_dyn.vision_space and REFUSES to restore a target whose place (node + PROBE_UP) is outside it. All three vans stand inside.
  vanhp  every ZAnimatedVehicle health number (fields 9..15, floats >= 100) is lowered to --van-hp (default 3000 = the lowest number Dog Days' own
         van carries, so no new value): shots register. GUESS: that those seven floats are what the difficulty pick (0x552e10) reads.
  cars   VehicleEffects BlowupChance None -> Definite on every node NOT under an 'EscapeSetup!' path (the escape choppers stay as noblow left them:
         re/hasta_chopper_1019.md). GUESS: a parked car's blow-up sends no EscVehicleState (rules slot 94 grade 2) - the message goes to the
         OnlineEscVehicleController only; DM01 has had Definite cars since the first build.
NOT DONE: new parked cars on DM06B (needs new entities; DM06B has a redesign job), a hook FX-only damage mode (proposal for e8).

Only the .prp member of each map zip differs (same entity order). Pinned on the live zip md5 (read at build time); INSTALL swaps in a patched COPY,
keeps the original as <zip>.before-1025vans; UNDO renames it back (byte identical). Never touches KL_PortBackup / stock files / the hook.

Usage (from tools/):  python kl_vans_1025.py --out <folder> [--game <DD>] [--features ft,vanhp,cars] [--van-hp 3000] [--rehearse <scratch>]
"""
import os, sys, json, gc, hashlib, shutil, subprocess, zipfile, struct, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_map_ai as MA
from kl_prp import units

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
TAG = '.before-1025vans'
BLOW_FIELD = 23
HP_FIELDS = range(9, 16)
SKIP = ('DD', 'T0')                      # Dog Days' own copies and the test slot are never touched
FT_DONOR = ('DM02', 'F02')               # a live map whose van body carries the stock FakeTarget
VAN_BODY = 'V_Van_00\\Body\\Body_Main'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def discover(game):
    out = []
    for d in sorted(glob.glob(os.path.join(game, 'KLExpansion', 'Maps', '*', 'F*_Main.zip'))):
        m = os.path.basename(os.path.dirname(d))
        if m.startswith(SKIP):
            continue
        out.append((m, os.path.basename(d)))
    return out


def donor_ft(game):
    sc, _, _ = kl_fa.load(os.path.join(game, 'KLExpansion', 'Maps', FT_DONOR[0], FT_DONOR[1] + '_Main.zip'))
    for k in range(1, len(sc.nodes)):
        if sc.path[k].endswith(VAN_BODY):
            for i, (nm, b) in enumerate(sc.nodes[k]['ctrls']):
                if sc.p.key(nm) == 'FakeTarget':
                    return sc, sc.nodes[k]['ctrls'][i]
    raise ValueError('donor %s has no van FakeTarget' % (FT_DONOR,))


def restore_ft(sc, B, donor, log):
    """FakeTarget back on every van Body_Main without one, if its place is inside the vision grid. -> [changes]"""
    import kl_fa_bots_dyn as D
    dsc, (dname, dbody) = donor
    space = D.vision_space(B)
    ch = []
    for k in range(1, len(sc.nodes)):
        if not sc.path[k].endswith(VAN_BODY) or kl_fa.has(sc, k, 'FakeTarget'):
            continue
        if not space:
            log('  ft: %s : vision space unreadable, NOT restored' % sc.path[k][-60:])
            continue
        out = D.outside(space, B.at(k))
        if out:
            log('  ft: %s : place %s outside the vision grid by %s, NOT restored (0x686a66)' % (sc.path[k][-60:], [round(x) for x in B.at(k)], out))
            continue

        def conv(t):                      # string (0x0c) and enum (0x0e) tokens hold an index of the file's own key table
            return (t[0], struct.pack('<I', sc.p.key_index(dsc.p.key(t)))) if t[0] in (0x0c, 0x0e) else t
        sc.nodes[k]['ctrls'].append((conv(dname), [conv(t) for t in dbody]))
        ch.append('ft: %s gets the stock FakeTarget (inside the grid at %s)' % (sc.path[k][-60:], [round(x) for x in B.at(k)]))
    return ch


def lower_hp(sc, hp):
    ch = []
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) != 'ZAnimatedVehicle':
            continue
        vals = kl_fa.node_values(sc, k)
        want = [i for i in HP_FIELDS if isinstance(vals[i], float) and vals[i] > hp]
        if not want:
            continue

        def fn(us, want=want):
            for i in want:
                MA.setv(sc, us, i, float(hp))
        kl_fa.edit(sc, k, None, fn)
        ch.append('vanhp: %s health numbers %s -> %.0f' % (sc.path[k][-40:], [vals[i] for i in want], hp))
    return ch


def cars_definite(sc):
    ch = []
    for k in range(1, len(sc.nodes)):
        if 'escapesetup!' in sc.path[k].lower():
            continue
        for ci, (nm, b) in enumerate(sc.nodes[k]['ctrls']):
            if sc.p.key(nm) != 'VehicleEffects':
                continue
            us = [list(u) for u in units(b[1:-1])]
            if kl_fa.value(sc, us[BLOW_FIELD]) != 'BlowupChanceNone':
                continue
            kl_fa.edit(sc, k, ci, lambda f: MA.setv(sc, f, BLOW_FIELD, 'BlowupChanceDefinite'))
            ch.append('cars: %s None -> Definite' % sc.path[k][-50:])
    return ch


def patch_map(live, feats, hp, donor, log):
    import kl_fa_bots as F
    zf = zipfile.ZipFile(live)
    sc, _, _ = kl_fa.load(live)
    B = F.Built(live, os.path.basename(live).split('_Main')[0]) if 'ft' in feats else None
    ch = []
    if 'ft' in feats:
        ch += restore_ft(sc, B, donor, log)
    if 'vanhp' in feats:
        ch += lower_hp(sc, hp)
    if 'cars' in feats:
        ch += cars_definite(sc)
    pn = [n for n in zf.namelist() if n.lower().endswith('_main.prp')][0]
    prp = sc.p.serialize() if ch else None
    if prp:                              # round trip: the new .prp must parse and keep every node
        import kl_fa_bots as F2
        back = F2.Prp(prp)
        assert back.serialize() == prp and len(back.nodes()) == len(sc.nodes), 'new .prp does not round-trip'
    zf.close()
    del B
    gc.collect()
    return pn, prp, ch


PS1 = r'''# vans.ps1 - shootable vans and cars (tools/kl_vans_1025.py, 2026-10-25).
#   powershell -ExecutionPolicy Bypass -File vans.ps1 [-Undo] [-DryRun] [-Rehearsal] [-Maps DM01B,DM03A] [-Game <folder>]
# WHAT: only the .prp member inside each map's Fxx_Main.zip is replaced (same name, same entity order). The live zip is COPIED, the copy is
#   patched and checked (member md5, entry count), then swapped in; the live zip is renamed <zip>.before-1025vans.
# SAFETY: refuses while kl2.exe runs; a map is skipped unless its live zip md5 is exactly the pinned one (or already the new one);
#   read-back after the swap, on failure the original is put back; UNDO renames the backup back (md5 == the original).
#   -Rehearsal: does not need kl2.exe to be absent and refuses the real game folder (only a folder given with -Game that is not the Steam one).
# Not touched: KL_PortBackup, stock files, KLHook.ini, dinput8.dll.
param([switch]$Undo, [switch]$DryRun, [switch]$Rehearsal, [string]$Maps = '',
      [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days')
$ErrorActionPreference = 'Stop'
$tag = '.before-1025vans'
$man = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'vans.json') -Raw | ConvertFrom-Json
$want = @(); if ($Maps) { $want = $Maps.Split(',') | ForEach-Object { $_.Trim().ToUpper() } }
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
function md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }
function Patch-Zip($zip, $member, $prp) {
  $z = [System.IO.Compression.ZipFile]::Open($zip, 'Update')
  try {
    $old = $z.Entries | Where-Object { $_.FullName -eq $member } | Select-Object -First 1
    if (-not $old) { throw "member $member not found" }
    $old.Delete()
    $e = $z.CreateEntry($member, [System.IO.Compression.CompressionLevel]::Optimal)
    $e.LastWriteTime = [DateTimeOffset]::new(2026, 10, 25, 0, 0, 0, [TimeSpan]::Zero)
    $s = $e.Open(); $b = [System.IO.File]::ReadAllBytes($prp); $s.Write($b, 0, $b.Length); $s.Dispose()
  } finally { $z.Dispose() }
}
function Member-Md5($zip, $member) {
  $z = [System.IO.Compression.ZipFile]::OpenRead($zip)
  try {
    $e = $z.Entries | Where-Object { $_.FullName -eq $member } | Select-Object -First 1
    if (-not $e) { return '' }
    $s = $e.Open(); $m = New-Object System.IO.MemoryStream; $s.CopyTo($m); $s.Dispose()
    $h = [System.Security.Cryptography.MD5]::Create().ComputeHash($m.ToArray())
    return ([BitConverter]::ToString($h) -replace '-', '').ToLower()
  } finally { $z.Dispose() }
}
function Count-Entries($zip) { $z = [System.IO.Compression.ZipFile]::OpenRead($zip); try { $z.Entries.Count } finally { $z.Dispose() } }
$real = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
if ($Rehearsal -and ([IO.Path]::GetFullPath($Game).TrimEnd('\') -ieq $real)) { 'Rehearsal refuses the real game folder.'; exit 1 }
if (-not $Rehearsal -and (Get-Process kl2 -ErrorAction SilentlyContinue)) { 'kl2.exe is running: close the game first. Nothing was changed.'; exit 1 }
if (-not (Test-Path (Join-Path $Game 'kl2.exe'))) { "no kl2.exe in $Game"; exit 1 }
$bad = 0
foreach ($x in $man.maps) {
  if ($want.Count -gt 0 -and ($want -notcontains $x.m.ToUpper())) { continue }
  $dst = Join-Path $Game ('KLExpansion\Maps\' + $x.m + '\' + $x.f)
  $bak = "$dst$tag"; $tmp = "$dst.tmp1025"
  $src = Join-Path $PSScriptRoot ($x.m + '\' + $x.prp_file)
  $name = $x.m + '\' + $x.f
  if (-not (Test-Path -LiteralPath $dst)) { "$name : SKIP, not installed"; $bad++; continue }
  $cur = md5 $dst
  if ($Undo) {
    if (-not (Test-Path -LiteralPath $bak)) { if ($cur -eq $x.old) { "$name : already undone" } else { "$name : SKIP, no backup and live is $cur"; $bad++ }; continue }
    if ($x.new -and $cur -ne $x.new) { "$name : SKIP, live is $cur, not the vans build (changed since?). Backup left in place."; $bad++; continue }
    if ((md5 $bak) -ne $x.old) { "$name : SKIP, backup is not the expected original"; $bad++; continue }
    if ($DryRun) { "$name : would restore the original (dry run)"; continue }
    Remove-Item -LiteralPath $dst -Force
    Rename-Item -LiteralPath $bak -NewName $x.f
    if ((md5 $dst) -ne $x.old) { "$name : FAILED, restored file does not read back right!"; $bad++; continue }
    "$name : original restored, read back ok"
    continue
  }
  if ($x.new -and $cur -eq $x.new) { "$name : already installed"; continue }
  if ($cur -ne $x.old) { "$name : SKIP, live md5 is $cur, expected $($x.old). Another install in between? Not changed (rebuild with tools/kl_vans_1025.py on the new live file)."; $bad++; continue }
  if (Test-Path -LiteralPath $bak) { "$name : SKIP, $bak already exists. Not changed."; $bad++; continue }
  if (-not (Test-Path -LiteralPath $src) -or (md5 $src) -ne $x.prp_md5) { "$name : SKIP, build file $src missing or changed"; $bad++; continue }
  if ($DryRun) { "$name : would patch $($x.member) (dry run)"; continue }
  if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
  Copy-Item -LiteralPath $dst -Destination $tmp
  try {
    $n0 = Count-Entries $tmp
    Patch-Zip $tmp $x.member $src
    if ((Count-Entries $tmp) -ne $n0) { throw 'entry count changed' }
    if ((Member-Md5 $tmp $x.member) -ne $x.prp_md5) { throw 'member does not read back' }
    if ($x.new -and (md5 $tmp) -ne $x.new) { throw "patched zip md5 $(md5 $tmp) is not the rehearsed $($x.new)" }
  } catch { "$name : FAILED while patching the copy ($_). Live file untouched."; Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue; $bad++; continue }
  Rename-Item -LiteralPath $dst -NewName ($x.f + $tag)
  $ok = $false
  try { Rename-Item -LiteralPath $tmp -NewName $x.f; $ok = (Test-Path -LiteralPath $dst) } catch { $ok = $false }
  if (-not $ok) {
    if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Force }
    Rename-Item -LiteralPath $bak -NewName $x.f
    "$name : FAILED swap, original put back"; $bad++; continue
  }
  "$name : installed (md5 $((md5 $dst).Substring(0,8))), original kept as $($x.f)$tag"
}
if ($bad) { "done with $bad problem(s), see above."; exit 4 }
'done.'
'''

BAT = '@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0vans.ps1" {arg}\r\npause\r\n'


def build(game, out, feats, hp, log=print):
    os.makedirs(out, exist_ok=True)
    man = {'features': sorted(feats), 'van_hp': hp, 'maps': []}
    donor = donor_ft(game) if 'ft' in feats else None
    for m, f in discover(game):
        live = os.path.join(game, 'KLExpansion', 'Maps', m, f)
        pn, prp, ch = patch_map(live, feats, hp, donor, log)
        if not prp:
            log('%s\\%s: nothing to change' % (m, f))
            continue
        d = os.path.join(out, m)
        os.makedirs(d, exist_ok=True)
        pf = f.replace('_Main.zip', '_Main.prp')
        with open(os.path.join(d, pf), 'wb') as fh:
            fh.write(prp)
        with zipfile.ZipFile(live) as z:
            old_member = hashlib.md5(z.read(pn)).hexdigest()
        man['maps'].append({'m': m, 'f': f, 'member': pn, 'prp_file': pf, 'old': md5(live), 'old_member_md5': old_member,
                            'prp_md5': hashlib.md5(prp).hexdigest(), 'new': '', 'changes': ch})
        log('%s\\%s: %d change(s)' % (m, f, len(ch)))
        for c in ch[:6]:
            log('    ' + c)
        if len(ch) > 6:
            log('    ... +%d more' % (len(ch) - 6))
    write_files(out, man)
    return man


def write_files(out, man):
    with open(os.path.join(out, 'vans.json'), 'w') as fh:
        json.dump(man, fh, indent=1)
    with open(os.path.join(out, 'vans.ps1'), 'w', newline='\r\n') as fh:
        fh.write(PS1)
    names = [('INSTALL-ALL vans.bat', ''), ('UNDO-ALL vans.bat', '-Undo')]
    for x in man['maps']:
        names.append(('INSTALL %s vans.bat' % x['m'], '-Maps %s' % x['m']))
        names.append(('UNDO %s vans.bat' % x['m'], '-Undo -Maps %s' % x['m']))
    for nm, arg in names:
        with open(os.path.join(out, nm), 'w', newline='') as fh:
            fh.write(BAT.format(arg=arg))


def ps(out, game, *extra):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(out, 'vans.ps1'), '-Rehearsal', '-Game', game] + list(extra)
    r = subprocess.run(a, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def rehearse(out, game, scratch, log=print):
    """INSTALL / UNDO on COPIES in <scratch>\\game (an empty kl2.exe stand-in; never run). Fills 'new' in vans.json."""
    g = os.path.join(scratch, 'game')
    man = json.load(open(os.path.join(out, 'vans.json')))
    for x in man['maps']:
        d = os.path.join(g, 'KLExpansion', 'Maps', x['m'])
        os.makedirs(d, exist_ok=True)
        shutil.copy2(os.path.join(game, 'KLExpansion', 'Maps', x['m'], x['f']), d)
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    zp = lambda x: os.path.join(g, 'KLExpansion', 'Maps', x['m'], x['f'])
    rc, txt = ps(out, g, '-DryRun'); log(txt)
    rc, txt = ps(out, g); log(txt); assert rc == 0, 'install rc %d' % rc
    new = {}
    for x in man['maps']:
        new[x['m']] = md5(zp(x))
        with zipfile.ZipFile(zp(x)) as z:
            assert z.testzip() is None, 'zip test failed ' + x['m']
            assert hashlib.md5(z.read(x['member'])).hexdigest() == x['prp_md5']
        sc, _, _ = kl_fa.load(zp(x)); gc.collect()
        log('  %s patched md5 %s, %d nodes read back' % (x['m'], new[x['m']], len(sc.nodes)))
    rc, txt = ps(out, g, '-Undo'); log(txt); assert rc == 0, 'undo rc %d' % rc
    for x in man['maps']:
        assert md5(zp(x)) == x['old'], 'undo is not byte identical: ' + x['m']
        assert not os.path.exists(zp(x) + TAG)
    log('UNDO byte identical: ok')
    rc, txt = ps(out, g); assert rc == 0
    for x in man['maps']:
        assert md5(zp(x)) == new[x['m']], 'second install differs (not deterministic): ' + x['m']
        x['new'] = new[x['m']]
    log('second install gives the same md5s: ok')
    json.dump(man, open(os.path.join(out, 'vans.json'), 'w'), indent=1)
    rc, txt = ps(out, g); log(txt)              # with md5s in the manifest: 'already installed'
    rc, txt = ps(out, g, '-Undo'); log(txt)
    for x in man['maps']:
        assert md5(zp(x)) == x['old']
    # single-map stage + wrong live file refused
    one = man['maps'][0]
    rc, txt = ps(out, g, '-Maps', one['m']); log(txt)
    assert md5(zp(one)) == one['new'] and all(md5(zp(y)) == y['old'] for y in man['maps'][1:]), '-Maps touched another map'
    rc, txt = ps(out, g, '-Undo', '-Maps', one['m']); log(txt)
    with open(zp(one), 'ab') as fh:
        fh.write(b'x')
    rc, txt = ps(out, g, '-Maps', one['m']); log(txt)
    assert rc == 4 and 'SKIP, live md5' in txt, 'a changed live file must be refused'
    log('pin check: a changed live file is refused: ok')
    log('final UNDO byte identical: ok')
    shutil.rmtree(g)


def main():
    a = sys.argv[1:]
    def opt(k, d=None):
        return a[a.index(k) + 1] if k in a else d
    game, out = opt('--game', DD), opt('--out')
    if not out:
        print(__doc__); return 2
    feats = set(opt('--features', 'ft,vanhp,cars').split(','))
    man = build(game, out, feats, float(opt('--van-hp', 3000)))
    print('kl_vans_1025: %d map(s) -> %s' % (len(man['maps']), out))
    if '--rehearse' in a:
        rehearse(out, game, opt('--rehearse'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
