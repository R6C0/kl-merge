#!/usr/bin/env python3
"""
Turn a KLGfx frame capture (KLGfx/frame_<n>_<tick>/calls.txt) into a pass list: one line per stretch of
draws into the same render targets, with what they sampled, their shaders and states, the copies and
clears between them, and the images KLGfx saved. Used to find where the 3D scene ends and post-processing
starts (the DLSS insertion point), which target holds the scene colour, and which shader constants hold
the camera matrices.

    python frame_report.py <capture folder or calls.txt> [--consts]
"""
import os, re, sys, collections


def load(path):
    if os.path.isdir(path):
        path = os.path.join(path, 'calls.txt')
    res, shaders, events = {}, {}, []
    for line in open(path, encoding='latin1'):
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 2:
            continue
        seq, kind, rest = int(parts[0]), parts[1], parts[2:]
        if kind == 'R':
            res[int(rest[0])] = rest[1]
        elif kind == 'SHADER':
            if len(rest) >= 2 and rest[1] != '?':
                shaders[(rest[0], int(rest[1]))] = rest
        events.append((seq, kind, rest))
    return res, shaders, events


def kv(rest):
    out = {}
    for r in rest:
        if '=' in r:
            k, v = r.split('=', 1)
            out[k] = v
    return out


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    show_consts = '--consts' in sys.argv
    res, shaders, events = load(a[0])
    passes, cur = [], None
    notes = []
    for seq, kind, rest in events:
        if kind.startswith('DRAW'):
            d = kv(rest)
            key = (d.get('rt'), d.get('ds'))
            if not cur or cur['key'] != key:
                cur = {'key': key, 'first': seq, 'draws': 0, 'prims': 0, 'vs': collections.Counter(),
                       'ps': collections.Counter(), 'tex': collections.Counter(), 'z': collections.Counter(),
                       'blend': collections.Counter(), 'vp': collections.Counter(), 'notes': notes}
                notes = []
                passes.append(cur)
            cur['draws'] += 1
            cur['prims'] += int(d.get('count', 0))
            cur['vs'][d.get('vs')] += 1
            cur['ps'][d.get('ps')] += 1
            cur['z'][d.get('z')] += 1
            cur['blend'][d.get('blend')] += 1
            cur['vp'][d.get('vp')] += 1
            for t in filter(None, d.get('tex', '').split(',')):
                cur['tex'][t.split(':')[1]] += 1
            cur['last'] = seq
        elif kind in ('CLEAR', 'STRETCH', 'FILL', 'READBACK', 'UPDATESURF', 'DUMP'):
            notes.append('%d %s %s' % (seq, kind, ' '.join(rest)))
    def name(i):
        return '#%s(%s)' % (i, res.get(int(i), '?')) if i and i != '0' else '-'
    print('%d passes, %d resources' % (len(passes), len(res)))
    for n, p in enumerate(passes):
        rts = p['key'][0].split(',')
        for note in p['notes']:
            print('      ' + note)
        print('[%d] calls %d-%d  rt0=%s  ds=%s  draws=%d prims=%d' % (n, p['first'], p['last'], name(rts[0]),
                                                                    name(p['key'][1]), p['draws'], p['prims']))
        if any(r != '0' for r in rts[1:]):
            print('      mrt: %s' % ', '.join(name(r) for r in rts[1:] if r != '0'))
        print('      z=%s blend=%s vp=%s' % (dict(p['z']), dict(p['blend']), dict(p['vp'])))
        print('      vs=%s ps=%s' % (dict(p['vs'].most_common(6)), dict(p['ps'].most_common(6))))
        if p['tex']:
            print('      samples: %s' % ', '.join('%s x%d' % (name(t), c) for t, c in p['tex'].most_common(8)))
    if show_consts:
        print('\nshader constant tables:')
        for (kind, sid), rest in sorted(shaders.items()):
            print('%s %d %s' % (kind, sid, ' '.join(rest[2:])))


if __name__ == '__main__':
    main()
