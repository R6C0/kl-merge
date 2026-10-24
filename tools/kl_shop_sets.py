#!/usr/bin/env python3
r"""
kl_shop_sets.py - set B ("page II") of the Dog Days between-rounds weapon shop, for klhook\klshoppage.c. OFFLINE; never writes the game folder.

    python kl_shop_sets.py show [--grenades] [kl2.exe]     the pairs: row (stock gun) -> set-B gun, carrier price/rank/tier, picture row
    python kl_shop_sets.py ini [--grenades] [out.ini]       KLShopPage.ini text (default: stdout)
    python kl_shop_sets.py stage <out folder> [--grenades] [--dll=<dinput8.dll>] [--game=<Dog Days folder>]
                                                            out\KLShopPage.ini, optional dinput8.dll.page, INSTALL/UNDO bats + shoppage_install.ps1

Facts (re\shop_cap.md, re\shop_more_guns.md): the shop table (36 rows, 0xbd1f68) is hashed: price, rank, tier, lock and ammo of a row are
the CARRIER's. Usable non-shop items on every stock map: 33 35 38 40-59 62 63 (60/61 have no template). Nothing here was run in the game.
Carrier choice (GUESS, a balance call): by category (pistols 0-10, shotguns 11-16, SMGs 17-27, rifles 28-35); inside a category the
set-B guns are ordered light -> heavy and spread over the carriers ordered cheap -> dear, preferring rows with no DLC lock (dlc == -1).
A row without a pair keeps its stock gun on page II.
"""
import hashlib, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
EXE = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\kl2.exe'
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
TABLE, ROWS = 0xbd1f68, 36
CATS = {'pistol': range(0, 11), 'shotgun': range(11, 17), 'smg': range(17, 28), 'rifle': range(28, 36)}

# item -> (name shown, kind line, picture row = the stock gun whose picture is nearest, GUESS)
ITEMS = {
    62: ('M-77B SHIELD', 'Hand gun. Origin: Japanese. The one held behind a hostage.', 0),
    63: ('M9 SHIELD', 'Hand gun. Origin: Italian. The one held behind a hostage.', 2),
    54: ('HK69 FLARE', 'Flare launcher. Origin: German. Lights the sky, burns a little.', 14),
    53: ('HK69 GAS', 'Grenade launcher. Origin: German. Gas rounds.', 14),
    52: ('HK69', 'Grenade launcher. Origin: German. One 40 mm grenade at a time.', 14),
    51: ('RPG-7 HIND', 'Rocket launcher. Origin: Russian. The helicopter pod version.', 14),
    50: ('RPG-7', 'Rocket launcher. Origin: Russian. Not for the faint-hearted.', 14),
    41: ('TYPE 88 MG L09', 'Light machine gun. Origin: Chinese. Warehouse stock.', 31),
    42: ('TYPE 88 MG HELI', 'Light machine gun. Origin: Chinese. Door-mounted, taken off its mount.', 31),
    43: ('TYPE 88 MG HELI P', 'Light machine gun. Origin: Chinese. Door-mounted, taken off its mount.', 31),
    44: ('TYPE 88 MG L10', 'Light machine gun. Origin: Chinese. Rooftop stock.', 31),
    45: ('MINIMI HELI P', 'Light machine gun. Origin: Belgian. Door-mounted, taken off its mount.', 32),
    46: ('MINIMI L10', 'Light machine gun. Origin: Belgian. Rooftop stock.', 32),
    48: ('MINIMI HELI', 'Light machine gun. Origin: Belgian. Door-mounted, taken off its mount.', 32),
    40: ('TYPE 88 MG', 'Light machine gun. Origin: Chinese. Belt-fed and heavy.', 31),
    47: ('MINIMI', 'Light machine gun. Origin: Belgian. Lifted from an army depot.', 32),
    33: ('TYPE 81', 'Assault rifle. Origin: Chinese. Plain, rugged and everywhere.', 30),
    35: ('TYPE 88 L09', 'Assault rifle. Origin: Chinese. Warehouse stock.', 31),
    38: ('TYPE 95 L09', 'Assault rifle. Origin: Chinese. Warehouse stock.', 34),
    49: ('REM 700', 'Sniper rifle. Origin: American. A hunting rifle with a long reach.', 32),
    55: ('SMOKE GRENADE', 'Grenade. Smoke. Thrown, not fired.', 4),
    56: ('GAS GRENADE', 'Grenade. Gas. Thrown, not fired.', 4),
    57: ('FRAG GRENADE', 'Grenade. Fragmentation. Thrown, not fired.', 4),
    58: ('INCENDIARY', 'Grenade. Incendiary. Thrown, not fired.', 4),
    59: ('FLASHBANG', 'Grenade. Flash-bang. Thrown, not fired.', 4),
}
# light -> heavy order per category (GUESS)
ORDER = {
    'pistol': [62, 63],
    'shotgun': [54, 53, 52, 51, 50],
    'smg': [41, 42, 43, 44, 45, 46, 48, 40, 47],
    'rifle': [33, 35, 38, 49],
}
GRENADES = [55, 56, 57, 58, 59]            # opt-in: [4, 6, 8, 10, ...] pistol rows get them (thrown items in a gun slot are untried)


def rows(path=EXE):
    import kl_exe
    x = kl_exe.Exe(path)
    return [struct.unpack('<6i', x.read(TABLE + 24 * i, 24)) for i in range(ROWS)]


def names():
    import kl_hud_shop as S
    return [r[1] for r in S.ROWS]


def pairs(grenades=False, path=EXE):
    """-> {row: (item, name, desc, picrow)}"""
    tab, nm = rows(path), names()
    out = {}
    for cat, items in ORDER.items():
        items = list(items)
        carriers = [r for r in CATS[cat] if tab[r][5] == -1] or list(CATS[cat])
        if len(carriers) < len(items):
            carriers = list(CATS[cat])
        carriers.sort(key=lambda r: (tab[r][2], r))
        k, m = len(items), len(carriers)
        picks = sorted({round(i * (m - 1) / (k - 1)) if k > 1 else m - 1 for i in range(k)})
        while len(picks) < k:                                  # rounding collisions: fill with the next free carrier
            for j in range(m):
                if j not in picks:
                    picks.append(j); break
            picks.sort()
        for it, j in zip(items, picks):
            out[carriers[j]] = it
    if grenades:
        free = [r for r in CATS['pistol'] if r not in out and tab[r][5] == -1]
        for it, r in zip(GRENADES, free):
            out[r] = it
    res = {}
    for r, it in sorted(out.items()):
        name, kind, pic = ITEMS[it]
        desc = ('Police reg.: 2%03d-II%02d\n%s Page II: sold in the %s row, same price, same rank.' % (it, it, kind, nm[r]))
        res[r] = (it, name, desc, pic)
    return res


def ini_text(grenades=False, path=EXE):
    p = pairs(grenades, path)
    L = ['; KLShopPage.ini - written by tools/kl_shop_sets.py; read by klhook/klshoppage.c (beside KLHook.ini). row|item|picture row|name', '[Pairs]', 'Count=%d' % len(p)]
    for i, (r, (it, name, desc, pic)) in enumerate(p.items()):
        L.append('P%d=%d|%d|%d|%s' % (i, r, it, pic, name))
    L.append('[Desc]')
    for i, (r, (it, name, desc, pic)) in enumerate(p.items()):
        L.append('D%d=%s' % (i, desc.replace('\n', '\\n')))
    return '\r\n'.join(L) + '\r\n'


def show(grenades, path):
    tab, nm = rows(path), names()
    for r, (it, name, desc, pic) in pairs(grenades, path).items():
        t = tab[r]
        print('row %2d %-16s -> item %2d %-18s  price %7d rank %2d tier %d dlc %2d  picture of row %d (%s)' % (r, nm[r], it, name, t[2], t[3], t[4], t[5], pic, nm[pic]))


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


PS1 = r'''# shoppage_install.ps1 - install (or -Undo) shop page II: the hook dll + KLShopPage.ini + a [ShopPage] block in KLHook.ini.
# Install: refuses while kl2.exe runs; refuses unless the LIVE dinput8.dll is the build this was made on (LIVE_MD5); needs the staged dll to match shoppage.md5; backs up dinput8.dll, KLHook.ini and (if present) KLShopPage.ini as
#   <name>.before-1024page (never overwritten); copies the dll and ini; adds the block (Enable=1) between markers; sets nothing else.
# Undo: puts the dll back from its backup (md5 checked; refuses, unless -Force, when the live dll is not the one INSTALL put there), removes the block,
#   restores or deletes KLShopPage.ini, always deletes the KLHook.ini backup.
param([switch]$Undo, [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days', [switch]$Force)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$tag = '.before-1024page'
$begin = '; --- shoppage installer block BEGIN (run UNDO shoppage.bat to take it out) ---'
$end = '; --- shoppage installer block END ---'
$liveExpect = '@LIVE@'   # the hook build in the game folder when this was staged (k37)
function Md5($p) { (Get-FileHash -LiteralPath $p -Algorithm MD5).Hash.ToUpper() }
function Die($m) { Write-Host "REFUSED: $m"; exit 1 }
if (-not $Force -and (Get-Process -Name kl2 -ErrorAction SilentlyContinue)) { Die 'kl2.exe is running' }
$dll = Join-Path $Game 'dinput8.dll'; $ini = Join-Path $Game 'KLHook.ini'; $pg = Join-Path $Game 'KLShopPage.ini'
if (-not (Test-Path -LiteralPath $dll)) { Die "no dinput8.dll in $Game" }
if (-not (Test-Path -LiteralPath $ini)) { Die "no KLHook.ini in $Game" }
$enc = [Text.Encoding]::GetEncoding(28591)
$want = $null
Get-Content -LiteralPath (Join-Path $here 'shoppage.md5') | ForEach-Object { if ($_ -match '^([0-9A-Fa-f]{32})\s+\*?dinput8\.dll\.page\s*$') { $want = $Matches[1].ToUpper() } }
if (-not $want) { Die 'no md5 line for dinput8.dll.page in shoppage.md5' }
if ($Undo) {
    $bd = $dll + $tag
    if ((Test-Path -LiteralPath $bd) -and -not $Force -and (Md5 $dll) -ne $want -and (Md5 $dll) -ne (Md5 $bd)) { Die "the live dinput8.dll ($(Md5 $dll)) is not the page build this installed ($want): a later hook build is live. Undoing would downgrade it. Run with -Force to do it anyway." }
    if (Test-Path -LiteralPath $bd) {
        Copy-Item -LiteralPath $bd -Destination $dll -Force
        if ((Md5 $dll) -ne (Md5 $bd)) { Die 'restore of dinput8.dll failed the md5 check' }
        Remove-Item -LiteralPath $bd
    } else { Write-Host "no dinput8.dll${tag}: dll left as it is" }
    $raw = [IO.File]::ReadAllText($ini, $enc)
    $i = $raw.IndexOf($begin); $j = $raw.IndexOf($end)
    if ($i -ge 0 -and $j -gt $i) {
        $after = $raw.Substring($j + $end.Length).TrimStart("`r", "`n")
        $head = $raw.Substring(0, $i).TrimEnd("`r", "`n")
        $nl = if ($raw.Contains("`r`n")) { "`r`n" } else { "`n" }
        $new = if ($after) { $head + $nl + $nl + $after } else { $head + $nl }
        [IO.File]::WriteAllText($ini, $new, $enc)
        Write-Host 'removed the shoppage block from KLHook.ini'
    } else { Write-Host 'no shoppage block in KLHook.ini' }
    if (Test-Path -LiteralPath ($pg + $tag)) { Copy-Item -LiteralPath ($pg + $tag) -Destination $pg -Force; Remove-Item -LiteralPath ($pg + $tag) }
    elseif (Test-Path -LiteralPath $pg) { Remove-Item -LiteralPath $pg }
    if (Test-Path -LiteralPath ($ini + $tag)) { Remove-Item -LiteralPath ($ini + $tag) }   # the block is out; a stale backup would only block the next INSTALL
    Write-Host "shoppage undone: dinput8.dll md5 $(Md5 $dll)"
    exit 0
}
$src = Join-Path $here 'dinput8.dll.page'; $srcini = Join-Path $here 'KLShopPage.ini'
if ((Md5 $dll) -ne $liveExpect.ToUpper()) { Die "the live dinput8.dll is $(Md5 $dll), not the build this was made for ($liveExpect). Ask for a rebuild on top of the live hook." }
if ((Md5 $src) -ne $want) { Die 'staged dinput8.dll.page does not match shoppage.md5' }
foreach ($f in @($dll, $ini)) { if (Test-Path -LiteralPath ($f + $tag)) { Die ((Split-Path -Leaf $f) + "$tag already exists: run UNDO first") } }
if (Test-Path -LiteralPath ($pg + $tag)) { Die "KLShopPage.ini$tag already exists: run UNDO first" }
$raw = [IO.File]::ReadAllText($ini, $enc)
if ($raw.Contains($begin)) { Die 'KLHook.ini already has the shoppage block' }
if ($raw -match '(?im)^\[ShopPage\]') { Die 'KLHook.ini already has a [ShopPage] section (edit Enable=1 by hand, or remove it first)' }
Copy-Item -LiteralPath $dll -Destination ($dll + $tag); Copy-Item -LiteralPath $ini -Destination ($ini + $tag)
if (Test-Path -LiteralPath $pg) { Copy-Item -LiteralPath $pg -Destination ($pg + $tag) }
foreach ($f in @($dll, $ini)) { if ((Md5 $f) -ne (Md5 ($f + $tag))) { Die "backup of $f failed the md5 check" } }
Copy-Item -LiteralPath $src -Destination $dll -Force
if ((Md5 $dll) -ne $want) { Write-Host 'copy failed the md5 check: restoring'; Copy-Item -LiteralPath ($dll + $tag) -Destination $dll -Force; exit 1 }
Copy-Item -LiteralPath $srcini -Destination $pg -Force
$nl = if ($raw.Contains("`r`n")) { "`r`n" } else { "`n" }
$block = $begin + $nl + '[ShopPage]' + $nl + 'Enable=1' + $nl + $end + $nl
[IO.File]::WriteAllText($ini, $raw.TrimEnd("`r", "`n") + $nl + $nl + $block, $enc)
Write-Host "Installed shop page II (dll md5 $want, KLShopPage.ini, [ShopPage] Enable=1). In the Buy Weapons shop (Arcade, between rounds) press F6 to flip between set A and set B. Undo: UNDO shoppage.bat."
exit 0
'''


LIVE_MD5 = 'A9414890C2204801FF6B3EB79E4DDF66'      # k37, live in the game folder on 2026-10-24 (re-read at stage time when the game folder exists)


def stage(out, grenades, dll, game):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'KLShopPage.ini'), 'w', newline='') as f:
        f.write(ini_text(grenades))
    if dll:
        import shutil
        shutil.copyfile(dll, os.path.join(out, 'dinput8.dll.page'))
        with open(os.path.join(out, 'shoppage.md5'), 'w') as f:
            f.write('%s *dinput8.dll.page\n' % md5(dll))
    with open(os.path.join(out, 'shoppage_install.ps1'), 'w', newline='') as f:
        live = LIVE_MD5
        lp = os.path.join(game, 'dinput8.dll')
        if os.path.exists(lp):
            live = md5(lp).upper()
        f.write(PS1.replace('@LIVE@', live))
    for name, arg in (('INSTALL shoppage.bat', ''), ('UNDO shoppage.bat', ' -Undo')):
        with open(os.path.join(out, name), 'w', newline='') as f:
            f.write('@echo off\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%%~dp0shoppage_install.ps1"%s\r\npause\r\n' % arg)
    print('staged in %s (%d pairs)' % (out, len(pairs(grenades))))


def main():
    a = sys.argv[1:]
    gren = '--grenades' in a
    dll = next((x[6:] for x in a if x.startswith('--dll=')), None)
    game = next((x[7:] for x in a if x.startswith('--game=')), GAME)
    a = [x for x in a if not x.startswith('--')]
    if a and a[0] == 'show':
        show(gren, a[1] if len(a) > 1 else EXE); return 0
    if a and a[0] == 'ini':
        t = ini_text(gren)
        if len(a) > 1:
            open(a[1], 'w', newline='').write(t)
        else:
            sys.stdout.write(t)
        return 0
    if len(a) == 2 and a[0] == 'stage':
        stage(a[1], gren, dll, game); return 0
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main())
