"""Clip sound ids in the merged ANM (crash fix, 11 Oct: M12 long-play crash at kl2 0x5c8075).

Clip record u32 11 (+0x2c) is NOT a constant: it is a byte offset into the level's own .SND, naming the clip's
'audio:animation/resources/<path>#seq' record (type 3).  Proved on stock Dog Days: all 415 distinct non-zero values
in F03 and all 417 in L01 are record starts in that level's .SND, and the same clip has different values in F03 and
L01.  kl2 reads it when a player clip starts (ZPlayer vt+0x620 = 0x6b9d50: [clip+0x2c] -> 0x409170 -> ZDllSound
0x875360 -> 0x5dd230 -> 0x886ae0 -> 0x555740 -> 0x8401f0 -> 0x54dca0 base+id; type 2 -> 0x4ddb10 random pick ->
0x5c8050 reads the list offset at +0x14).

anm_merge.py takes the Dog Days base clips from F03 unchanged, so their field 11 holds F03 .SND offsets, which point
anywhere in a converted Dead Men bank (record offsets there are Dead Men's).  In M12, Walk#Forward_War_Pistol_02 has
0x5550 = F03's 'forward_war_pistol_02#seq'; in M12's bank 0x5550 is the mode word (2) of a type-2 record, so kl2
walked it as a random list whose list offset is the 0xcdcdcdcd of the next record -> access violation.
Every converted level had 8-89 such list-shaped targets plus hundreds of wrong or dead ones.

Fix (ANP_ANM_CLIPSND):
  name (default)  donor clips: look up the donor record's name in the level bank, use that offset, else 0;
                  Dead Men clips: keep if the offset is a record start in the level bank, else 0
  zero            donor clips: 0 (no animation foley); Dead Men clips as above
  off             untouched (old behaviour)
Only u32 11 of the type-4 clip records is written; the file is patched in place (same size, same layout).

CLI check of a built level:  py tools\\clipsnd.py <level>_Main.zip   (exit 1 if any clip names a non-record)
"""
import os, sys, struct, zipfile, collections

CD = 0xcdcdcdcd
SIZE_MASK = 0x3FFFFFFF
REC_DD = 0x68
MODE = os.environ.get('ANP_ANM_CLIPSND', 'name')


def snd_name(s, off):
    """name (bytes) of the .SND record starting at off, or None if off is not a record start"""
    if not off or off % 4 or off + 12 > len(s):
        return None
    t, c, nm = struct.unpack_from('<3I', s, off)
    if c != CD or t >= 0x19 or not (0 < nm < len(s)):
        return None
    e = s.find(b'\0', nm)
    return s[nm:e] if e > nm else None


def snd_index(s):
    """{record name: offset} of the records listed in the .SND directory (Dog Days or Dead Men layout)"""
    h0 = struct.unpack_from('<I', s, 0)[0]
    # directory head: u32, one u32 per language (Dead Men 6, Dog Days 10), 0xcdcdcdcd, 3 u32, counts[25], offs[25]
    head = struct.unpack_from('<16I', s, h0)
    nl = head.index(CD, 1) - 1
    c0 = 1 + nl + 4
    dw = struct.unpack_from('<%dI' % (c0 + 50), s, h0)
    counts, offs = dw[c0:c0 + 25], dw[c0 + 25:c0 + 50]
    idx = {}
    for t in range(25):
        if not offs[t]:
            continue
        for i in range(counts[t]):
            p = offs[t] + 4 * i
            if p + 4 > len(s):
                break
            r = struct.unpack_from('<I', s, p)[0]
            n = snd_name(s, r)
            if n and struct.unpack_from('<I', s, r)[0] == t:
                idx.setdefault(n, r)
    return idx


def _clip_table(b):
    """(offset of clip record 0, clip count) of the type-4 chunk of an ANM (Dog Days 0x68 records)"""
    n_ent = struct.unpack_from('<I', b, 12)[0]
    o = 16
    for _ in range(n_ent):
        t, sf = struct.unpack_from('<II', b, o)
        if t == 4:
            n = struct.unpack_from('<I', b, o + 8)[0]
            return o + 8 + 52, n
        o += sf & SIZE_MASK
    raise ValueError('ANM has no type-4 chunk')


def fix_clip_sounds(merged, donor_anm, donor_snd, level_snd, rep=None, mode=None):
    """merged: merged ANM bytes (donor clips first, Dead Men clips appended by anm_merge).
    level_snd: the level's .SND (Dead Men source or converted: record offsets are the same).
    Returns patched bytes."""
    mode = mode or MODE
    rep = rep if rep is not None else collections.Counter()
    if mode == 'off':
        return merged
    out = bytearray(merged)
    p0, n = _clip_table(out)
    _, n_base = _clip_table(donor_anm)
    if n_base > n:
        raise ValueError('merged ANM has fewer clips than the donor')
    idx = snd_index(level_snd) if mode == 'name' else {}
    for i in range(n):
        q = p0 + i * REC_DD + 0x2c
        v = struct.unpack_from('<I', out, q)[0]
        if not v:
            continue
        if i < n_base:
            nm = snd_name(donor_snd, v)
            nv = idx.get(nm, 0) if nm else 0
            rep['ANM clip sound (donor) %s' % ('re-pointed by name' if nv else 'cleared')] += 1
        else:
            nv = v if snd_name(level_snd, v) is not None else 0
            rep['ANM clip sound (Dead Men) %s' % ('kept' if nv else 'invalid -> cleared')] += 1
        if nv != v:
            struct.pack_into('<I', out, q, nv)
    return bytes(out)


def check(anm, snd):
    """[(clip index, value, reason)] of clips whose sound id is not a type-1/2/3 record start in snd
    (stock F03 and L01 use types 1, 2 and 3 and pass with 0 bad)"""
    p0, n = _clip_table(anm)
    bad = []
    for i in range(n):
        v = struct.unpack_from('<I', anm, p0 + i * REC_DD + 0x2c)[0]
        if not v:
            continue
        if snd_name(snd, v) is None:
            bad.append((i, v, 'not a record start'))
        else:
            t = struct.unpack_from('<I', snd, v)[0]
            if t not in (1, 2, 3):
                bad.append((i, v, 'record type %d' % t))
    return bad


def main(argv):
    rc = 0
    for zp in argv:
        z = zipfile.ZipFile(zp)
        get = lambda suf: next(z.read(x) for x in z.namelist() if x.lower().endswith(suf))
        anm, snd = get('.anm'), get('.snd')
        bad = check(anm, snd)
        _, n = _clip_table(anm)
        print('%s: %d clips, %d with a bad sound id%s' % (os.path.basename(zp), n, len(bad),
              (' e.g. ' + ', '.join('#%d %#x (%s)' % b for b in bad[:5])) if bad else ''))
        rc |= bool(bad)
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
