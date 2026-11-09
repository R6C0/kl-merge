#!/usr/bin/env python3
"""skeleton_report.py DD.anm DM.anm [DMDB=DDDB ...]

Compares what the character databases of two ANM files animate:
  * clips per DB, tracks per clip (min/median/max), union of animated bone names
  * per-bone local translation (first position key, median over all clips of the DB): the clips
    carry a translation key stream for EVERY bone, so these numbers are the skeleton proportions
    the clips impose on whatever mesh they drive.
"""
import sys, os, struct, statistics, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anm_lib as L, anm_codec as C

PAIRS = [('PlayerCharacter', 'Kane'), ('Lynch_Coop', 'Lynch'), ('Army', 'Swat_02'), ('Police_USA', 'Police'),
         ('Mercenary_04', 'Thug'), ('Female', 'Civilian'), ('Civilian', 'Civilian')]
KEY_BONES = [b'PELVIS', b'SPINE', b'SPINE_1', b'SPINE_2', b'NECK', b'HEAD', b'LEFT_THIGH', b'LEFT_CALF', b'LEFT_FOOT',
             b'RIGHT_CALF', b'LEFT_CLAVICLE', b'LEFT_UPPER_ARM', b'LEFT_FOREARM', b'LEFT_HAND', b'RIGHT_FOREARM',
             b'RIGHT_HAND', b'r hand attacher', b'l hand attacher', b'head attacher', b'camera_bone', b'fa_jaw']


def db_stats(f, db):
    a = f.anim
    clips = sorted(db.referenced_clips())
    ntr, bones, pos = [], collections.Counter(), collections.defaultdict(list)
    for i in clips:
        tb = a.track_block(i)
        if tb['baked']:
            continue
        ntr.append(len(tb['tracks']))
        for oa, ob, oc, od, b in tb['tracks']:
            nm = a.C[b]; bones[nm] += 1
            if C.idxt_header(a.B, tb['p'] + oc)[1]:
                pos[nm].append(struct.unpack_from('<3f', a.B, tb['p'] + od))
    med = {k: tuple(statistics.median(v[j] for v in vs) for j in range(3)) for k, vs in pos.items()}
    return dict(clips=len(clips), ntr=ntr, bones=bones, pos=med)


def fmt(v):
    return '(%7.2f %7.2f %7.2f)' % v if v else '   -'


def main():
    dd = L.load(sys.argv[1]); dm = L.load(sys.argv[2])
    pairs = PAIRS
    if len(sys.argv) > 3:
        pairs = [tuple(x.split('=')) for x in sys.argv[3:]]
    for smn, ddn in pairs:
        sdb, ddb = dm.db_by_short(smn), dd.db_by_short(ddn)
        if sdb is None or ddb is None:
            print('== %s / %s : missing' % (smn, ddn)); continue
        s, d = db_stats(dm, sdb), db_stats(dd, ddb)
        print('== DM %-15s clips %4d tracks/clip min %d med %d max %d  bones %d' % (
            smn, s['clips'], min(s['ntr']), statistics.median(s['ntr']), max(s['ntr']), len(s['bones'])))
        print('   DD %-15s clips %4d tracks/clip min %d med %d max %d  bones %d' % (
            ddn, d['clips'], min(d['ntr']), statistics.median(d['ntr']), max(d['ntr']), len(d['bones'])))
        only_s = sorted(set(s['bones']) - set(d['bones'])); only_d = sorted(set(d['bones']) - set(s['bones']))
        print('   bones only in DM DB:', b', '.join(only_s).decode())
        print('   bones only in DD DB:', b', '.join(only_d).decode())
        diffs = []
        for b in set(s['pos']) & set(d['pos']):
            dv = max(abs(x - y) for x, y in zip(s['pos'][b], d['pos'][b]))
            diffs.append((dv, b))
        diffs.sort(reverse=True)
        print('   local bone translation (median first key), DM vs DD, largest differences:')
        for dv, b in diffs[:8]:
            print('      %-22s DM %s  DD %s  max|d| %.2f' % (b.decode(), fmt(s['pos'][b]), fmt(d['pos'][b]), dv))
        same = sum(1 for dv, _ in diffs if dv < 0.5)
        print('   %d of %d shared bones have translations within 0.5 units' % (same, len(diffs)))
        for b in KEY_BONES:
            if b in s['pos'] or b in d['pos']:
                print('      %-22s DM %s  DD %s' % (b.decode(), fmt(s['pos'].get(b)), fmt(d['pos'].get(b))))


if __name__ == '__main__':
    main()
