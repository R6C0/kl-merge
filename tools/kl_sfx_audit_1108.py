#!/usr/bin/env python3
"""Read-only sound audit of the live expansion maps (and the nine stock DD maps' kinds of events).
Per map: bank clean?, wave -> .WHD records resolve?, in-memory data inside the .WAV?, and which
explosion / door / glass / shutter named sound objects the bank holds. Writes nothing in the game
folder. GUESS: keyword match on object names (no per-event ground truth for what a script plays).
usage: python kl_sfx_audit_1108.py [MAP ...]   (default: all)"""
import sys, os, zipfile, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_snd as S, kl_whd as W

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPS = DD + r'\KLExpansion\Maps'
CATS = {
    'explosion': ('explo', 'blast', 'c4', 'breach', 'detonat', 'grenade', 'bomb'),
    'gas/extinguisher': ('gas', 'extingu', 'canist', 'propane', 'fire'),
    'car explosion': ('car_exp', 'carexp', 'vehicle_exp', 'veh_exp', 'carblow', 'explosion_car'),
    'door': ('door', 'kick'),
    'glass': ('glass', 'window', 'shatter'),
    'shutter': ('shutter', 'rolldown', 'garage'),
}

def audit(m):
    d = os.path.join(MAPS, m)
    zs = [f for f in os.listdir(d) if f.endswith('_Main.zip')]
    if not zs:
        return {'map': m, 'err': 'no zip'}
    slot = zs[0][:-9]
    z = zipfile.ZipFile(os.path.join(d, zs[0]))
    snd = [n for n in z.namelist() if n.lower().endswith('_main.snd')]
    if not snd:
        return {'map': m, 'err': 'no .SND in zip'}
    snd = z.read(snd[0])
    whd = open(os.path.join(d, slot + '_Main.WHD'), 'rb').read()
    wav = open(os.path.join(d, slot + '_Main.WAV'), 'rb').read()
    ls = b''
    s = S.Snd('dd', snd, ls).walk()
    out = {'map': m, 'slot': slot, 'clean': len(s.clean())}
    recs = W.records('dd', whd)
    n = collections.Counter()
    for o, i, r in s.waves():
        n['waves'] += 1
        if r not in recs:
            n['dead'] += 1
    for r, f in recs.items():
        if not f['fmt'] & W.STREAMED:
            off = f['off'] | (f['offhi'] << 32)
            if not (16 <= off and off + f['size'] <= len(wav)):
                n['nodata'] += 1
    out.update(n)
    names = [s.name(o) for o, t in s.kind.items() if t == 1]
    out['sounds'] = len(names)
    low = [x.lower() if isinstance(x, str) else x.decode('latin1').lower() for x in names]
    out['cats'] = {c: [nm for nm in low if any(k in nm for k in ks)] for c, ks in CATS.items()}
    return out

if __name__ == '__main__':
    maps = sys.argv[1:] or sorted(os.listdir(MAPS))
    for m in maps:
        try:
            r = audit(m)
        except Exception as e:
            r = {'map': m, 'err': repr(e)}
        c = r.pop('cats', {})
        print(r)
        for k, v in c.items():
            print('   %-17s %3d  %s' % (k, len(v), ', '.join(v[:6])))
