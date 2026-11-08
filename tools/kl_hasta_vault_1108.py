"""kl_hasta_vault_1108.py - OPT-IN post-pass for Hasta (DM11B, slot F04): the locked loot wing shows its AFTER pieces only after the blast.
Reads a BUILT F04_Main.zip, writes a copy. Rerunnable (same bytes on its own output). Nothing imports it.
Written 2026-11-08 after the owner: "the loot room u can go in but the explosion doesnt open it up its weird".

WHAT THE OFFLINE LOOK FOUND (live zip md5 b755b505)
  * The beat chain is wired like the campaign's (TriggerCounter count 2 + 30 s TriggerDelay2 -> Timer_SandbagsDeactive / Timer ->
    DeactivateGeom of Roadblock_01 / BarricadeB_01 / OYCHECK_BEFORE01 + ActivateGeom of the remains + the dust emitters). kl_walk2d: shut before, open after.
  * The two AFTER pieces (SI0100_M11_BarricadeB_Broken01, M11B_OYCHECK_AFTER01) are NOT hidden at load, in the campaign or in the live build (ZGEOM[3] = 0,
    .gms flag 0x400 clear). So the broken pile stands in the same spot as the intact barricade from the first second, and the wing opens on a silent timer
    (the campaign's BoomBoxDust is an Explode with an empty effect name and was dropped: no sound, no shake at the bunker). Result for the player: the
    wall never visibly blows, it just becomes walkable. PROVEN: the two flags. GUESS: that this is the "weird" the owner saw.
  * NOW: both pieces get ZGEOM[3] = 1 and the .gms flag 0x400, so before the beat only the intact wall shows and ActivateGeom brings the wreck in.
    UNPROVEN offline: that ActivateGeom draws a node hidden this way (the club heli / van use the same pair and are shown by their own activators) and that
    it does not also restore collision of the wreck early. A live bench must look.
KIT: python kl_hasta_vault_1108.py --kit <base dir with F04_Main.zip, .bots.zip, .bots.base.md5, KLGuns.ini> <out dir> writes both zips, the base md5 file,
KLGuns.ini and an install.py / UNDO.bat copied from the base dir's own (pins rewritten; backups *.before-hastavault1108).
Usage (from tools/):  python kl_hasta_vault_1108.py <in F04_Main.zip> <out F04_Main.zip> [--force]
"""
import hashlib, os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_prpjoin as J, kl_fa_author as A

# live b755b505 (plain zip); the hastalook_1108 stage's output ac175c71 (plain) and cf1ebbae (bots zip) it installs first
KNOWN_INPUT_MD5 = {'b755b5051d27978ab121216c08bfcb32', 'ac175c714d43c51e5c8d9932ac425a9c', 'cf1ebbaef9dfda9ab26b8731e55bc7ea'}
LEAVES = ('SI0100_M11_BarricadeB_Broken01', 'M11B_OYCHECK_AFTER01')
HIDDEN = A.HIDDEN                                # .gms flag 0x400


def md5(b):
    return hashlib.md5(b).hexdigest()


def targets(sc):
    """-> node indices whose leaf name is one of LEAVES (every match: the campaign may repeat a name)."""
    return [k for k in range(1, len(sc.names)) if sc.names[k] in LEAVES]


def hide(sc, raw, log=print):
    """Set ZGEOM[3] = 1 on the .prp nodes and flag 0x400 in the unpacked .gms bytes. -> (new gms bytes, nodes)."""
    ks = targets(sc)
    if sorted(sc.names[k] for k in ks) != sorted(LEAVES):
        raise ValueError('kl_hasta_vault_1108: expected exactly %s, found %s' % (LEAVES, [sc.names[k] for k in ks]))
    ents = list(kl_gms.entities(raw))
    out = bytearray(raw)
    for k in ks:
        lab = J.labels('dd', sc.cls(k))
        kl_fa.edit(sc, k, None, lambda us, lab=lab: A.setv(sc, us, lab.index('ZGEOM[3]'), 1))
        off = 4 * (ents[k - 1][0] & 0xffffff) + 4 * 7
        fl = struct.unpack_from('<I', out, off)[0]
        struct.pack_into('<I', out, off, fl | HIDDEN)
        log('  %s: hidden from the load (flags %#x -> %#x)' % (sc.names[k], fl, fl | HIDDEN))
    return bytes(out), ks


def run(src, dst, force=False, log=print):
    raw = open(src, 'rb').read()
    if md5(raw) not in KNOWN_INPUT_MD5 and not force:
        raise ValueError('kl_hasta_vault_1108: %s md5 %s is not the known live Hasta (use --force)' % (src, md5(raw)))
    sc, _, _ = kl_fa.load(src)
    zf = zipfile.ZipFile(src)
    names = zf.namelist()
    pn = [n for n in names if n.lower().endswith('_main.prp')][0]
    gn = pn[:-4] + '.gms'
    gms, ks = hide(sc, kl_gms.unpack(zf.read(gn)), log)
    new = {pn: sc.p.serialize(), gn: kl_gms.pack(gms)}
    members = [(n, new[n] if n in new else zf.read(n)) for n in names]
    kl_graft.write_zip(dst, members, kl_graft.load_options('level=9'))
    log('kl_hasta_vault_1108: wrote %s md5 %s' % (dst, md5(open(dst, 'rb').read())))
    return dst


def kit(base, out, log=print):
    import re, shutil
    NL, CR = chr(10), chr(13)
    os.makedirs(out, exist_ok=True)
    for n in ('F04_Main.zip', 'F04_Main.bots.zip'):
        run(os.path.join(base, n), os.path.join(out, n), False, log)
    open(os.path.join(out, 'F04_Main.bots.base.md5'), 'w').write(md5(open(os.path.join(out, 'F04_Main.zip'), 'rb').read()) + NL)
    shutil.copy2(os.path.join(base, 'KLGuns.ini'), os.path.join(out, 'KLGuns.ini'))
    files = [(n, md5(open(os.path.join(base, n), 'rb').read()), md5(open(os.path.join(out, n), 'rb').read()))
             for n in ('F04_Main.zip', 'F04_Main.bots.zip', 'F04_Main.bots.base.md5', 'KLGuns.ini')]
    t = open(os.path.join(base, 'install.py'), encoding='utf-8').read()
    rows = NL.join('    (%r, %r, %r),' % f for f in files)
    t = re.sub(r'FILES = \[.*?' + NL + r'\]' + NL, lambda m: 'FILES = [   # name, md5 before (the hastalook_1108 output), md5 after' + NL + rows + NL + ']' + NL, t, flags=re.S)
    t = t.replace('.before-hastalook1108', '.before-hastavault1108').replace('HASTALOOK1108 (tools/kl_hastalook_1108.py)', 'HASTAVAULT1108 (tools/kl_hasta_vault_1108.py)')
    t = re.sub(r"LIVE_ZIP_MD5 = '[0-9a-f]+'", "LIVE_ZIP_MD5 = '%s'" % files[0][1], t)
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline=NL).write(t)
    open(os.path.join(out, 'UNDO.bat'), 'w', newline=CR + NL).write('@echo off' + CR + NL + 'python "%~dp0install.py" --undo %*' + CR + NL + 'pause' + CR + NL)
    for f in files:
        log('  %-24s %s -> %s' % f)


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if '--kit' in sys.argv and len(a) == 2:
        kit(a[0], a[1])
        return 0
    if len(a) != 2:
        print(__doc__)
        return 2
    run(a[0], a[1], '--force' in sys.argv)
    return 0


if __name__ == '__main__':
    sys.exit(main())
