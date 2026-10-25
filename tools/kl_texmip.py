#!/usr/bin/env python3
"""
kl_texmip: drop the top mip level(s) of large .TEX textures inside a Dog Days level zip.

Why: kl2 creates every texture D3DPOOL_MANAGED (a system-memory copy besides the driver copy),
so a 2048 px DXT5 costs 5.3 MB of 32-bit address space twice over. kl2's own TextureDetail mip
skip is global; this is the per-map, build-side version.

    python kl_texmip.py IN.zip OUT.zip [--min 1024] [--levels 1] [--exclude REGEX|none] [--dry]
    python kl_texmip.py --selftest [zip ...]     (round trip with --levels 0, byte-identical)
    --dry: report only (OUT.zip optional, nothing written).  --levels 0: rewrite, change nothing.

A record is (see kl_tex.py): u32 size, fourcc, fourcc, id, u16 h, u16 w, u32 mips, u32 flags,
f32 scale, u32, name\\0, then per mip u32 size + data, top (largest) mip first.
A level drop removes the first mip blob, halves w/h, mips -= 1, size -= 4 + blob. Ids, the
tables and every other record are untouched (kl_texmat write_tex relays the file out).

Only touched when ALL hold (otherwise reported as skipped, with the reason):
  - plain texture: no cube (0x400), not animated (0x100), not a frame/list member
  - fourcc in DXT1 DXT3 DXT5 RGBA I8 U8V8 A8 (byte size per mip is checked against w*h exactly
    for the whole chain; PAL*/16A* have no verified size formula -> skipped)
  - max(w,h) >= --min, and mips > levels (never reduce to the last level)
  - result keeps both sides >= 4 for DXT (block size)
GUESS (not tested in game): the engine takes w/h from the record header and UVs are normalized,
so materials need no change; HUD/sprite textures addressed in pixels would shrink on screen.
Use --exclude (regex on texture name) for those. Nothing here has been run in kl2.
"""
import os, re, struct, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kl_texmat import read_tex, write_tex, CUBE, ANIMATED

BLOCK = {b'DXT1': 8, b'DXT3': 16, b'DXT5': 16}
BPP = {b'RGBA': 4, b'I8  ': 1, b'U8V8': 2, b'A8  ': 1}   # RGBA = A8R8G8B8 (GUESS from name, verified by size)


def mip_bytes(fc, w, h):
    if fc in BLOCK:
        return BLOCK[fc] * max(1, (w + 3) // 4) * max(1, (h + 3) // 4)
    return BPP[fc] * w * h


def parse(e):
    """-> dict for a plain record, or raises ValueError."""
    size, f1, _f2, ident, h, w, mips, flags = struct.unpack_from('<I4s4sIHHII', e, 0)
    end = e.index(b'\0', 36)
    p = end + 1
    blobs = []
    for _ in range(mips):
        n = struct.unpack_from('<I', e, p)[0]
        blobs.append((p, n)); p += 4 + n
    if p != size or size != len(e):
        raise ValueError('record size mismatch')
    return dict(fc=f1[::-1], w=w, h=h, mips=mips, flags=flags, name=e[36:end].decode('latin1'),
                blobs=blobs, id=ident)


def chain_ok(d):
    fc = d['fc']
    if fc not in BLOCK and fc not in BPP:
        return 'format %s has no verified size formula' % fc.decode('latin1').strip()
    w, h = d['w'], d['h']
    for k, (_p, n) in enumerate(d['blobs']):
        if n != mip_bytes(fc, w, h):
            return 'mip %d size %d != expected %d for %dx%d' % (k, n, mip_bytes(fc, w, h), w, h)
        w, h = max(1, w // 2), max(1, h // 2)
    return None


def drop(e, d, levels):
    p0 = d['blobs'][0][0]
    cut = sum(4 + n for _p, n in d['blobs'][:levels])
    out = bytearray(e[:p0] + e[p0 + cut:])
    struct.pack_into('<I', out, 0, len(out))
    struct.pack_into('<HH', out, 16, d['h'] >> levels, d['w'] >> levels)
    struct.pack_into('<I', out, 20, d['mips'] - levels)
    return bytes(out), cut


def process(data, minpx=1024, levels=1, exclude=None, log=None):
    """-> (new_bytes, report). report: list of (id, name, fmt, w, h, action, bytes_saved)."""
    t = read_tex(data)
    if t.game != 'dd':
        raise ValueError('Dog Days .TEX only')
    listed = set()
    for x in t.tex.values():
        if x.frames:
            listed.update(x.frames)
    rep, saved = [], 0
    for i in sorted(t.tex):
        x = t.tex[i]
        try:
            d = parse(x.entry)
        except Exception as ex:
            rep.append((i, '?', '?', 0, 0, 'skip: unparsable (%s)' % ex, 0)); continue
        row = [i, d['name'], d['fc'].decode('latin1').strip(), d['w'], d['h']]
        why = None
        if levels <= 0:
            why = 'levels 0'
        elif d['flags'] & (CUBE | ANIMATED) or x.cube is not None or x.faces or x.frames is not None:
            why = 'cube/animated'
        elif i in listed:
            why = 'animation frame'
        elif max(d['w'], d['h']) < minpx:
            why = 'below --min'
        elif d['mips'] <= levels:
            why = 'only %d mip level(s)' % d['mips']
        elif min(d['w'], d['h']) < 128:
            why = 'thin strip (short side < 128, UI bars/fonts; GUESS)'
        elif exclude and exclude.search(d['name']):
            why = 'excluded by name'
        else:
            why = chain_ok(d)
            if why is None and d['fc'] in BLOCK and min(d['w'], d['h']) >> levels < 4:
                why = 'would fall below one DXT block'
            if why is None and (d['w'] % (1 << levels) or d['h'] % (1 << levels)):
                why = 'odd size'
        if why:
            rep.append(tuple(row) + ('skip: ' + why, 0)); continue
        new, cut = drop(x.entry, d, levels)
        x.entry = new
        saved += cut
        rep.append(tuple(row) + ('drop %d' % levels, cut))
    return write_tex(t), rep, saved


def tex_member(zf):
    m = [n for n in zf.namelist() if n.lower().endswith('.tex')]
    return m


def run(src, dst, minpx, levels, exclude, dry):
    zin = zipfile.ZipFile(src)
    mem = tex_member(zin)
    if len(mem) != 1:
        raise SystemExit('expected exactly one .TEX in %s, found %s' % (src, mem))
    old = zin.read(mem[0])
    new, rep, saved = process(old, minpx, levels, exclude)
    n_drop = sum(1 for r in rep if r[5].startswith('drop'))
    for r in rep:
        if r[5].startswith('drop') or (r[5].startswith('skip') and 'below' not in r[5] and 'only' not in r[5] and 'levels 0' not in r[5]):
            print('  %5d %-40s %-5s %4dx%-4d %-28s %9d' % r)
    print('textures %d, dropped %d, skipped-other see above; sysmem/driver bytes saved per copy: %d (%.1f MB), x2 for managed pool = %.1f MB'
          % (len(rep), n_drop, saved, saved / 1048576.0, 2 * saved / 1048576.0))
    print('.TEX file %d -> %d bytes' % (len(old), len(new)))
    if dry or not dst:
        return 0
    with zipfile.ZipFile(dst, 'w') as zo:
        for zi in zin.infolist():
            data = new if zi.filename == mem[0] else zin.read(zi.filename)
            zo.writestr(zi, data, compress_type=zi.compress_type)
    print('wrote', dst)
    return 0


def selftest(paths):
    bad = 0
    for p in paths:
        with zipfile.ZipFile(p) as zf:
            for n in tex_member(zf):
                d = zf.read(n)
                try:
                    new, rep, _ = process(d, levels=0)
                    ok = new == d
                    # also: a real drop must re-parse and walk
                    new2, rep2, s2 = process(d, 1024, 1)
                    read_tex(new2)
                    for _i, x in read_tex(new2).tex.items():
                        parse(x.entry)
                except Exception as ex:
                    ok = False; print('   error', ex)
                bad += not ok
                print('%s %s: round trip %s, %d textures' % (os.path.basename(p), n, 'IDENTICAL' if ok else 'DIFFERENT', len(rep)))
    return bad


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == '--selftest':
        sys.exit(1 if selftest(a[1:]) else 0)
    opts = dict(min=1024, levels=1, exclude=re.compile(r'UserInterface|(^|/)UI_|Font|HUD|Loader', re.I), dry=False)  # GUESS: UI is pixel-addressed
    pos = []
    k = 0
    while k < len(a):
        if a[k] == '--min': opts['min'] = int(a[k + 1]); k += 2
        elif a[k] == '--levels': opts['levels'] = int(a[k + 1]); k += 2
        elif a[k] == '--exclude': opts['exclude'] = None if a[k + 1] == 'none' else re.compile(a[k + 1], re.I); k += 2
        elif a[k] == '--dry': opts['dry'] = True; k += 1
        else: pos.append(a[k]); k += 1
    if not pos or (len(pos) < 2 and not opts['dry']):
        sys.exit(__doc__)
    sys.exit(run(pos[0], pos[1] if len(pos) > 1 else None, opts['min'], opts['levels'], opts['exclude'], opts['dry']))
