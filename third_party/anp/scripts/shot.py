"""Screenshot of the running game through the loader's ANP_shot.txt hook (replaces shot.sh; no extra packages).

  python scripts/shot.py [name]   ->  work/shots/<name>.png (at most 960 wide) and the frame's mean brightness

The loader writes <DD>/ANP_shot.bmp (back buffer, or GDI screen capture as fallback)."""
import os, sys, time, struct, zlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
from anp_paths import WORK, game_dir, DD_FOLDER

def read_bmp(path):
    d = open(path, 'rb').read()
    off = struct.unpack_from('<I', d, 10)[0]
    w, h, _, bpp, comp = struct.unpack_from('<iiHHI', d, 18)
    if bpp not in (24, 32) or comp not in (0, 3): raise SystemExit('unsupported BMP (%d bpp, compression %d)' % (bpp, comp))
    px = bpp // 8; stride = (w * px + 3) & ~3; rows = []
    for y in range(abs(h)):
        r = y if h < 0 else abs(h) - 1 - y            # positive height = bottom-up
        rows.append(d[off + r * stride: off + r * stride + w * px])
    return w, abs(h), px, rows

def write_png(path, w, h, rgb_rows):
    raw = b''.join(b'\0' + r for r in rgb_rows)
    chunk = lambda t, b: struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))

def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 'shot'
    dd = game_dir('ANP_DD_GAME', DD_FOLDER)
    bmp, trig = os.path.join(dd, 'ANP_shot.bmp'), os.path.join(dd, 'ANP_shot.txt')
    if os.path.exists(bmp): os.remove(bmp)
    with open(trig, 'w', encoding='ascii', newline='\n') as f: f.write('ANP_shot.bmp\n')   # no BOM: the loader uses line 1 as the file name
    for _ in range(20):                                # the loader polls every 0.5 s; the D3D path can take up to 3 s more
        time.sleep(0.5)
        if os.path.exists(bmp) and not os.path.exists(trig): break
    else:
        raise SystemExit('no ANP_shot.bmp after 10 s (is the game running with ANP_Loader.asi?)')
    time.sleep(0.5)                                    # let the writer finish
    w, h, px, rows = read_bmp(bmp)
    f = max(1, -(-w // 960)); ow, oh = w // f, h // f
    out = []; total = 0
    for y in range(oh):
        r = rows[y * f]
        line = bytearray(ow * 3)
        for x in range(ow):
            b, g, rr = r[x * f * px: x * f * px + 3]
            line[x * 3: x * 3 + 3] = bytes((rr, g, b)); total += rr * 299 + g * 587 + b * 114
        out.append(bytes(line))
    dst = os.path.join(WORK, 'shots'); os.makedirs(dst, exist_ok=True)
    p = os.path.join(dst, name + '.png'); write_png(p, ow, oh, out)
    print('saved %s (%dx%d from %dx%d), mean brightness %.1f' % (p, ow, oh, w, h, total / 1000.0 / max(1, ow * oh)))
    with open(os.path.join(dd, 'ANP_log.txt'), encoding='latin-1') as f:
        last = [l.rstrip() for l in f if 'd3dshot' in l or 'shot:' in l]
    if last: print(last[-1])

if __name__ == '__main__':
    main()
