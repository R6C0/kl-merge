"""Dead Men ZTTFONT font chunks -> Dog Days layout (ANP_DM_FONTS).

Both games: chunk = u32 1, u32 8 (offset to the header), 32-byte header, glyph records sorted by u32 code point,
kerning pairs {u32 (prev<<16)|cur, s32} sorted by key, zero padding to 16.
Header (same 8 dwords in both): +0 point size, +4 f32 1.0, +8 glyph count, +0xc line height, +0x10 kerning pair
count, +0x14 (unused; DM 4..10, DD 2), +0x18 descent below the last baseline (text box bottom), +0x1c minus the ascent
(text box top).

Glyph records (established from the code: DM kaneandlynch.exe 0x56a940/0x561800, DD kl2.exe 0x7598a0):
  DM 20 bytes                          DD 32 bytes
  +0  u32 char                         +0    u32 char
  +4  u32 key (0x800|slot text page,   +4    u32 key (0x1000|slot text page, plain slot icon page); both texture
          plain slot icon page)              managers ignore the flag bit when picking the texture
  +8  s8 u0 +9 v0 +a u1 +b v1 (x/128)  +8/+a/+c/+e s16 u0 v0 u1 v1 (x/512)  -> DD = DM * 4
  +c  u8 w   +d u8 h (screen px)       +10/+12 u16 w h
  +e  s8 ox  +f s8 oy                  +14/+16 s16 ox oy
  +10 s8 advance                       +18 s16 advance
  +11 s8 line height (= hdr+0xc)       +1a s16 line height
  +12 u8 icon flag (untinted)          +1c u16 icon flag
  +13 u8 pad (0xcd, never read)        +1e u16 pad (never read)
Kerning is identical (applied as pen_x -= value in both).
DD-only: kl2 0x759bcb moves glyphs 0xe000..0xe00f by -3.0 in screen y after placing them (DM does not), so a Dead
Men icon there gets oy - 3 to land where Dead Men drew it."""
import os, struct

DM_REC, DD_REC = 20, 32
DM_FLAG, DD_FLAG = 0x800, 0x1000
DD_ICON_SHIFT = range(0xe000, 0xe010)     # kl2 0x759ba9..0x759bd6: y -= 3.0 for these chars

# ANP_DM_FONT_C1 (default on): Dead Men's LOC stores cp1252 punctuation as the C1 code points U+0080..U+009F (U+0092
# apostrophe, U+0085 ellipsis, U+0096 en dash, U+009C oe...). No font of either game has glyphs for them; Dead Men's
# lookup falls back to a space (0x56caa1), Dog Days' to '_' (kl2 0x4fb6f1). Every converted font gets an alias glyph
# for each such code point: a copy of the glyph cp1252 means (only where the font has that glyph). tools/locconv.py
# also rewrites the LOC text itself; the aliases cover any string that bypasses it.
C1_ALIAS = {}
for _b in range(0x80, 0xa0):
    try: C1_ALIAS[_b] = ord(bytes([_b]).decode('cp1252'))
    except UnicodeDecodeError: pass
C1_ON = os.environ.get('ANP_DM_FONT_C1', '1') == '1'


def add_c1_aliases(glyphs):
    """glyphs: dict code point -> DD glyph dict. Adds C1 aliases in place -> list of added code points."""
    added = []
    for c1, real in sorted(C1_ALIAS.items()):
        if c1 not in glyphs and real in glyphs:
            glyphs[c1] = dict(glyphs[real], ch=c1); added.append(c1)
    return added


def _size(n, nk, rec):
    return (40 + rec * n + 8 * nk + 15) // 16 * 16


def parse(c, rec):
    """-> dict(pre, hdr, glyphs, kern) for a font chunk with `rec`-byte glyph records, or None when it is not one."""
    if len(c) < 48 or struct.unpack_from('<I', c, 4)[0] != 8: return None
    hdr = list(struct.unpack_from('<IfIiIiii', c, 8))
    n, nk = hdr[2], hdr[4]
    if not 1 <= n <= 0x10000 or nk > 0x10000 or len(c) != _size(n, nk, rec): return None
    g0 = 40
    if rec == DM_REC:
        G = []
        for q in range(n):
            ch, key, u0, v0, u1, v1, w, h, ox, oy, adv, lh, icon, pad = struct.unpack_from('<II4b2B2b2bBB', c, g0 + 20 * q)
            G.append(dict(ch=ch, key=key, uv=(u0, v0, u1, v1), w=w, h=h, ox=ox, oy=oy, adv=adv, lh=lh, icon=icon, pad=pad))
    else:
        G = []
        for q in range(n):
            ch, key, u0, v0, u1, v1, w, h, ox, oy, adv, lh, icon, pad = struct.unpack_from('<II4h2H4hHH', c, g0 + 32 * q)
            G.append(dict(ch=ch, key=key, uv=(u0, v0, u1, v1), w=w, h=h, ox=ox, oy=oy, adv=adv, lh=lh, icon=icon, pad=pad))
    k0 = g0 + rec * n
    K = [struct.unpack_from('<Ii', c, k0 + 8 * q) for q in range(nk)]
    return dict(pre=struct.unpack_from('<I', c, 0)[0], hdr=hdr, glyphs=G, kern=K)


def parse_dm(c): return parse(c, DM_REC)
def parse_dd(c): return parse(c, DD_REC)


def build_dd(F):
    """DD chunk bytes from a parsed font (glyph values already in DD units)."""
    G = sorted(F['glyphs'], key=lambda g: g['ch']); K = sorted(F['kern'])
    hdr = list(F['hdr']); hdr[2] = len(G); hdr[4] = len(K)
    out = bytearray(struct.pack('<II', F['pre'], 8) + struct.pack('<IfIiIiii', *hdr))
    for g in G:
        out += struct.pack('<II4h2H4hHH', g['ch'], g['key'], *g['uv'], g['w'], g['h'], g['ox'], g['oy'], g['adv'], g['lh'],
                           g['icon'], g.get('pad', 0) if g.get('pad', 0) <= 0xffff else 0)
    for kk, kv in K: out += struct.pack('<Ii', kk, kv)
    out += b'\0' * ((-len(out)) & 15)
    return bytes(out)


def dm_glyph_to_dd(g):
    """One Dead Men glyph -> Dog Days units (see the module docstring); keys keep the Dead Men .TEX slot (texconv
    copies every Dead Men slot to the same Dog Days slot)."""
    key = g['key']
    assert key & ~(DM_FLAG | 0x7ff) == 0 and key & 0x7ff, ('Dead Men glyph key', hex(g['ch']), hex(key))
    assert bool(key & DM_FLAG) != bool(g['icon']), ('flag/icon mismatch', hex(g['ch']), hex(key), g['icon'])
    nkey = (key & 0x7ff) | (DD_FLAG if key & DM_FLAG else 0)
    oy = g['oy'] - (3 if g['ch'] in DD_ICON_SHIFT else 0)
    return dict(ch=g['ch'], key=nkey, uv=tuple(4 * v for v in g['uv']), w=g['w'], h=g['h'], ox=g['ox'], oy=oy,
                adv=g['adv'], lh=g['lh'], icon=g['icon'], pad=0)


def convert(dm_chunk, dd_chunk=None, dd_fill=True, dd_prefer=(), c1_alias=None):
    """Dead Men font chunk -> Dog Days font chunk bytes, plus a report dict.
    Every Dead Men glyph is converted; duplicate code points (Dead Men lists 0xe000..0xe012 twice, identical copies)
    are kept once. With a Dog Days font `dd_chunk` (already carrying this level's .TEX keys):
      dd_fill   True: every code point Dead Men's font lacks is taken from the Dog Days font (Dog Days' typeface for
                Polish/Cyrillic etc., and its own private-use glyphs 0xe019, 0xf000..0xf002), so nothing the Dog Days
                UI emits falls back to '_'; False: only code points >= 0xe000
      dd_prefer code points always taken from the Dog Days font (e.g. Dog Days' own symbols 0xe012..0xe018)
    c1_alias: add the C1 alias glyphs (see C1_ALIAS); None = ANP_DM_FONT_C1"""
    F = parse_dm(dm_chunk); assert F, 'not a Dead Men font chunk'
    seen = {}; dup = 0
    for g in F['glyphs']:
        d = dm_glyph_to_dd(g)
        if d['ch'] in seen:
            assert seen[d['ch']] == d, ('different duplicate glyph', hex(d['ch'])); dup += 1; continue
        seen[d['ch']] = d
    added = []; preferred = []
    if dd_chunk is not None:
        D = parse_dd(dd_chunk); assert D, 'not a Dog Days font chunk'
        done = set()
        for g in D['glyphs']:
            c = g['ch']
            if c in done: continue                       # Dog Days DebugText lists 0xe000..0xe012 twice too
            if c in dd_prefer: seen[c] = dict(g, pad=0); preferred.append(c); done.add(c)
            elif c not in seen and (dd_fill or c >= 0xe000): seen[c] = dict(g, pad=0); added.append(c); done.add(c)
    c1 = add_c1_aliases(seen) if (C1_ON if c1_alias is None else c1_alias) else []
    out = dict(pre=F['pre'], hdr=list(F['hdr']), glyphs=list(seen.values()), kern=list(F['kern']))
    data = build_dd(out)
    chk = parse_dd(data); assert chk and len(chk['glyphs']) == len(seen)
    return data, dict(glyphs=len(seen), dup_dropped=dup, dd_added=added, dd_preferred=preferred, kern=len(out['kern']),
                      hdr=out['hdr'], c1_aliases=c1)
