#!/usr/bin/env python3
r"""
klt_audit.py - KLTalk audit of an owner install (read only).

    python tools/klt_audit.py C:\kl_build_1018\owner_1018 [--json out.json] [--percar]

--percar: a Who=Any pool's keys are per-character (the hook appends _C1.._C8): count the key present when all eight exist
with a sound. Without it those keys are reported missing (false alarm: DM01 pool 9 etc.). Default output unchanged.

Per map folder (Maps\<map>, *.replaced-* skipped): reads KLTalk.ini pools and the archive's English .LOC
and reports pools whose keys are missing from the .LOC (KLTalk resolves each key in the level's own .LOC,
kl2 0x828fa0), keys whose leaf has no sound id, and whether these are present:
  Fed      = a Who=Fed pool On=FedRespawn and On=FedKill whose keys all resolve
  AllDead  = a pool using Multiplayer/GameEnds/FA_AllDead that resolves (and the .LOC carries it)
  Shoot    = same for Multiplayer/Shoot_Off_Money/FA_ShootOffMoney_01
A map with no KLTalk.ini shows 'noini'. Column 'LOC' says which of the three lines the .LOC itself has.
"""
import os, re, sys, json, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_loc

ALLDEAD = 'Multiplayer/GameEnds/FA_AllDead'
SHOOT = 'Multiplayer/Shoot_Off_Money/FA_ShootOffMoney_01'
FEDK = ['Multiplayer/CallExitVehiclePolice/FA_CallExitVehiclePolice_01', 'Multiplayer/PoliceReward/FA_PoliceReward_01']


def pools(text):
    out, cur = [], None
    for ln in text.splitlines():
        ln = ln.strip()
        m = re.match(r'\[Pool\.(\d+)\]', ln)
        if m:
            cur = {'n': int(m.group(1)), 'keys': [], 'On': '', 'Who': ''}; out.append(cur); continue
        if ln.startswith('['):
            cur = None; continue
        if cur is None or '=' not in ln:
            continue
        k, v = ln.split('=', 1)
        if re.match(r'Key\.\d+$', k):
            cur['keys'].append(v.strip())
        elif k in ('On', 'Who'):
            cur[k] = v.strip()
    return out


def english(zp):
    with zipfile.ZipFile(zp) as zf:
        mem = kl_loc.members(zf)
        d = zf.read(mem['English'])
    return {p.lower(): (kl_loc.fields(k)[2] or 0) for p, k in kl_loc.leaves(kl_loc.parse(d))}


def audit_map(folder, percar=False):
    zps = [f for f in os.listdir(folder) if f.lower().endswith('_main.zip')]
    r = {'zip': zps[0] if zps else None}
    if not zps:
        r['error'] = 'no zip'; return r
    leaves = english(os.path.join(folder, zps[0]))
    r['loc'] = {n: (k.lower() in leaves) for n, k in (('AllDead', ALLDEAD), ('Shoot', SHOOT), ('Fed', FEDK[0]))}
    r['loc']['FedKill'] = FEDK[1].lower() in leaves
    ini = os.path.join(folder, 'KLTalk.ini')
    if not os.path.isfile(ini):
        r['noini'] = True; r['pools'] = 0; r['missing'] = []; r['nosound'] = []
        r['Fed'] = r['AllDead'] = r['Shoot'] = False
        return r
    ps = pools(open(ini, 'rb').read().decode('latin1'))
    r['pools'] = len(ps)
    miss, nosnd = [], []
    for p in ps:
        for k in p['keys']:
            if percar and p['Who'] == 'Any' and k.lower() not in leaves:
                # Who=Any keys are PER-CHARACTER: the hook appends _C<n> (kl_fa_talk.POOLS, pools()); resolve every n 1..8
                gone = [n for n in range(1, 9) if k.lower() + '_c%d' % n not in leaves]
                if gone:
                    miss.append((p['n'], p['On'], k + ' (no _C%s)' % ',_C'.join(map(str, gone))))
                elif not all(leaves[k.lower() + '_c%d' % n] for n in range(1, 9)):
                    nosnd.append((p['n'], p['On'], k))
            elif k.lower() not in leaves:
                miss.append((p['n'], p['On'], k))
            elif not leaves[k.lower()]:
                nosnd.append((p['n'], p['On'], k))
    r['missing'], r['nosound'] = miss, nosnd
    bad = {k.lower() for _n, _o, k in miss + nosnd}

    def has(pred):
        return any(pred(p) and p['keys'] and not any(k.lower() in bad for k in p['keys']) for p in ps)
    r['Fed'] = has(lambda p: p['On'] == 'FedRespawn') and has(lambda p: p['On'] == 'FedKill')
    r['AllDead'] = has(lambda p: ALLDEAD.lower() in [k.lower() for k in p['keys']])
    r['Shoot'] = has(lambda p: SHOOT.lower() in [k.lower() for k in p['keys']])
    return r


def main(owner, percar=False):
    md = os.path.join(owner, 'Maps')
    res = {}
    for m in sorted(os.listdir(md)):
        f = os.path.join(md, m)
        if os.path.isdir(f) and '.replaced-' not in m:
            res[m] = audit_map(f, percar)
    return res


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if not a:
        print(__doc__); sys.exit(2)
    res = main(a[0], '--percar' in sys.argv)
    print('%-8s %-14s %5s %4s %4s  %-4s %-7s %-5s  LOC(AllDead/Shoot/Fed/FedKill)' % ('map', 'zip', 'pools', 'miss', 'nosn', 'Fed', 'AllDead', 'Shoot'))
    for m, r in res.items():
        if 'error' in r:
            print('%-8s %s' % (m, r['error'])); continue
        yn = lambda b: 'yes' if b else 'NO'
        print('%-8s %-14s %5s %4d %4d  %-4s %-7s %-5s  %s%s' % (m, r['zip'], 'noini' if r.get('noini') else r['pools'], len(r['missing']),
              len(r['nosound']), yn(r['Fed']), yn(r['AllDead']), yn(r['Shoot']), ''.join('1' if r['loc'][k] else '0' for k in ('AllDead', 'Shoot', 'Fed', 'FedKill')), ''))
    for m, r in res.items():
        for n, o, k in r.get('missing', [])[:6]:
            print('  %s pool %d (%s) missing key %s' % (m, n, o, k))
        for n, o, k in r.get('nosound', [])[:3]:
            print('  %s pool %d (%s) key without sound id %s' % (m, n, o, k))
    if '--json' in sys.argv:
        json.dump(res, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
