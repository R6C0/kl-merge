#!/usr/bin/env python3
r"""
kl_talk_chars.py - KLTalk.ini Version 2 for every installed map folder (re/talk.md section 10).

    python tools/kl_talk_chars.py build  [--game <Dog Days folder>] [--out C:\kl_build_1019\talk_1023] [--maps DM01,DD01]
    python tools/kl_talk_chars.py check  [--game ...] [--out ...]       # re-reads the staged files, same rules as the hook
    python tools/kl_talk_chars.py list                                   # the character -> speaker table

Reads (never writes) <game>\KLExpansion\Maps\<map>\{KLTalk.ini, KLWardrobe.ini, F01_Main.zip}. For each map the staged file is
  - the map's own KLTalk.ini (scenes, Kane / Lynch pools, Any / Squad pools, the Fed / Won / Shoot pools and pairs), or for a map with none
    (DD01..DD09) the DM01 one without its scenes (Dead Men story lines do not belong to a Dog Days map),
  - Version=2, Once=0 with KeyGap, PairChance,
  - plus the named pools and the pairs below, built ONLY from keys that the map's English .LOC has WITH a sound id.

The speaker table is a GUESS (see CHARS): Dead Men's own campaign speakers (Carlos, Rific, Shelly, Thapa, Merc) are in no installed
.LOC, so the six Dead Men heisters get disjoint slices of Dog Days' two squad voices (Squad = 56 clips, Squad02 = 52) as stand-ins.
Kane keeps Kane's lines, Lynch keeps Lynch's; the eight Dog Days mercs keep their own _C<n> voices (the existing Who=Any pools, and
explicit _C<n> keys in pairs).
"""
import os, re, sys, zipfile, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_loc

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
OUT = r'C:\kl_build_1019\talk_1023'
LIM = dict(scene=96, pool=160, pair=160, said=512, nkey=24, keylen=100)
KEY_GAP = 240          # seconds before the same key may be said again (Once=0)
PAIR_CHANCE = 40       # percent of an idle turn that tries a pair (hook default 33)
O = 'AllLevels/Oneliners/'

# Dead Men heister (wardrobe number, name) -> (stand-in speaker suffix, slice 0..2, idle categories). GUESS: nothing here is the
# speaker the campaign gave that character; it only keeps the six apart (re/talk.md 10.2).
CHARS = [
    (11, 'Ashkanan', 'Squad',   0, ('BattleCries',)),
    (12, 'Meldal',   'Squad02', 0, ('BattleCries',)),
    (13, 'Red',      'Squad',   1, ('EnemySuppress', 'HeavyFire')),
    (14, 'Parker',   'Squad02', 1, ('EnemySuppress', 'HeavyFire')),
    (15, 'Standen',  'Squad',   2, ('Alert', 'EnemySpottedClose')),
    (16, 'Hutchison', 'Squad02', 2, ('Alert', 'EnemySpottedClose')),
]
# event -> category of the stand-in voice (sliced three ways between the characters of one voice)
EVENT_CAT = [('Stage2', 'Advance'), ('Down', 'ManDown'), ('Money', 'Exclamation')]
# call keys Kane / Lynch use toward somebody who answers; the answers they give to a call
KL_CALL = {'Kane': ['LetsGo/LetsGo_010_Kane', 'What/What_090_Kane', 'Flank/FlankCover_020_Kane', 'LetsGo/LetsGo_030_Kane'],
           'Lynch': ['LetsGo/LetsGo_020_Lynch', 'LetsGo/LetsGo_040_Lynch', 'What/What_070_Lynch', 'Flank/FlankCover_020_Lynch']}
KL_REPLY = {'Kane': ['Direction/DirectionResp_010_Kane', 'Direction/DirectionResp_020_Kane', 'Direction/DirectionResp_040_Kane', 'Flank/FlankRep_010_Kane'],
            'Lynch': ['Direction/DirectionResp_020_Lynch', 'Flank/FlankRep_030_Lynch', 'Direction/Direction_020_Lynch', 'Direction/DirectionResp_010_Lynch']}
# Dog Days merc lines (Who=Any form: the voice number is appended, here written out)
MERC_CALL = ['Multiplayer/F06/MissionReminder_01_R', 'Multiplayer/F05/MissionBriefing_01_R', 'Multiplayer/F05/ExitHeist_01_R', 'Multiplayer/F01/ExitHeist_01_R']
MERC_REPLY = ['Multiplayer/F06/ReachlootArea_01_R', 'Multiplayer/F05/ReachlootArea_01_R', 'Multiplayer/F04/ExitLootArea_01_R', 'Multiplayer/F08/ReachlootArea_01_R']


def leaves_of(zp):
    with zipfile.ZipFile(zp) as zf:
        d = zf.read(kl_loc.members(zf)['English'])
    return {p.lower(): (p, kl_loc.fields(k)[2] or 0) for p, k in kl_loc.leaves(kl_loc.parse(d))}


class Loc:
    def __init__(self, zp):
        self.d = leaves_of(zp)

    def ok(self, key):
        v = self.d.get(key.lower())
        return bool(v and v[1])

    def spell(self, key):
        return self.d[key.lower()][0]

    def get(self, key):
        """the key as the .LOC spells it (the game's lookup is case sensitive), or None"""
        return self.spell(key) if self.ok(key) else None

    def squad(self, voice, cat):
        """keys of AllLevels/Oneliners/<cat>/ spoken by exactly <voice> (Squad / Squad02), sorted"""
        rx = re.compile(r'^allLevels/oneliners/%s/[^/]*_\d+_%s(?:_[a-z])?$' % (re.escape(cat), voice), re.I)
        return sorted(self.spell(k) for k, (p, s) in self.d.items() if s and rx.match(k))


def merc_ok(loc, key):
    return all(loc.ok('%s_C%d' % (key, n)) for n in range(1, 9))


def read_wardrobe(path):
    out, cur = {}, None
    for ln in open(path, 'rb').read().decode('latin1').splitlines():
        ln = ln.strip()
        m = re.match(r'\[Character\.(\d+)\]', ln)
        if m:
            cur = out.setdefault(int(m.group(1)), {}); continue
        if ln.startswith('['):
            cur = None; continue
        if cur is not None and '=' in ln:
            k, v = ln.split('=', 1); cur[k] = v
    return out


def parse_ini(text):
    """-> (talk, scenes_raw [list of text blocks], chatter, pools, pairs); pools/pairs as dicts"""
    sec, order, raw = None, [], collections.OrderedDict()
    for ln in text.splitlines():
        s = ln.strip()
        m = re.match(r'\[([^\]]+)\]$', s)
        if m:
            sec = m.group(1); raw[sec] = []; continue
        if sec is not None:
            raw[sec].append(ln)
    def kv(lines):
        d = collections.OrderedDict()
        for l in lines:
            if '=' in l and not l.strip().startswith(';'):
                k, v = l.split('=', 1); d[k.strip()] = v.strip()
        return d
    talk = kv(raw.get('Talk', [])); chatter = kv(raw.get('Chatter', []))
    scenes = ['[%s]\n%s\n' % (n, '\n'.join(l)) for n, l in raw.items() if n.startswith('Scene.')]
    pools = []
    for n, l in raw.items():
        if n.startswith('Pool.'):
            d = kv(l)
            pools.append(dict(name=d['Name'], who=d['Who'], on=d['On'], keys=[d['Key.%d' % i] for i in range(1, int(d['Keys']) + 1)]))
    pairs = []
    for n, l in raw.items():
        if n.startswith('Pair.'):
            d = kv(l)
            c, r = d['Call'].split(',', 1), d['Reply'].split(',', 1)
            pairs.append(dict(cwho=c[0], ckey=c[1], rwho=r[0], rkey=r[1], wait=d.get('Wait')))
    return talk, scenes, chatter, pools, pairs


def sliced(keys, part):
    return [k for i, k in enumerate(keys) if i % 3 == part]


def named_pools(loc, ward):
    """the six Dead Men characters' pools: [(name, who, on, keys)]"""
    out, cats = [], {}
    for num, name, voice, part, idle in CHARS:
        if num not in ward or ward[num].get('Name', '').lower() != name.lower():
            continue                                    # the wardrobe lacks him: no pool (the hook would skip it too)
        ik = [k for c in idle for k in loc.squad(voice, c)]
        if ik:
            out.append(('%s_idle' % name.lower(), name, 'Idle', ik))
        for ev, cat in EVENT_CAT:
            ek = sliced(loc.squad(voice, cat), part)
            if ek:
                out.append(('%s_%s' % (name.lower(), ev.lower()), name, ev, ek))
    return out


def pair_list(loc, ward, pools):
    """[(call who, call key, reply who, reply key)]; only keys the .LOC has with a sound; mercs with explicit _C<n>"""
    by = {(p[1], p[2]): p[3] for p in pools}
    dm = [n for _num, n, _v, _p, _i in CHARS if (n, 'Idle') in by]
    def pick(lst, i):
        return lst[i % len(lst)] if lst else None
    out = []
    # Dead Men <-> Dead Men : the caller's "move" line, the answer from the other's own exclamations
    for i, a in enumerate(dm):
        for j, b in enumerate(dm):
            if a == b:
                continue
            c = pick(by.get((a, 'Stage2'), []), i + j)
            r = pick(by.get((b, 'Money'), []) or by.get((b, 'Idle'), []), i * 2 + j)
            if c and r:
                out.append((a, c, b, r))
    # Kane / Lynch <-> Dead Men : both directions
    for kl in ('Kane', 'Lynch'):
        calls = [k for k in (loc.get(O + x) for x in KL_CALL[kl]) if k]
        reps = [k for k in (loc.get(O + x) for x in KL_REPLY[kl]) if k]
        for i, d in enumerate(dm):
            if calls and by.get((d, 'Idle')):
                out.append((kl, pick(calls, i), d, pick(by[(d, 'Idle')], i)))
            c = pick(by.get((d, 'Stage2'), []), i + 1)
            if c and reps:
                out.append((d, c, kl, pick(reps, i)))
    # Dog Days mercs (wardrobe 1..8, voice _C<slot+1>) <-> Dead Men / Kane / Lynch
    mercs = []
    for n in range(1, 9):
        c = ward.get(n)
        if c and 'Slot' in c:
            mercs.append((n, int(c['Slot']) + 1))
    mc = [k for k in MERC_CALL if merc_ok(loc, k)]
    mr = [k for k in MERC_REPLY if merc_ok(loc, k)]
    for i, d in enumerate(dm):
        for (num, v) in mercs:
            if (i + num) % 2 == 0:                      # the Dead Men character calls, the merc answers
                c = pick(by.get((d, 'Stage2'), []), num)
                if c and mr:
                    out.append((d, c, 'Char%d' % num, '%s_C%d' % (pick(mr, i + num), v)))
            elif mc:                                    # the merc calls, the Dead Men character answers
                r = pick(by.get((d, 'Money'), []) or by.get((d, 'Idle'), []), num)
                if r:
                    out.append(('Char%d' % num, '%s_C%d' % (pick(mc, i + num), v), d, r))
    for kl in ('Kane', 'Lynch'):
        calls = [k for k in (loc.get(O + x) for x in KL_CALL[kl]) if k]
        for (num, v) in mercs:
            if calls and mr:
                out.append((kl, pick(calls, num), 'Char%d' % num, '%s_C%d' % (pick(mr, num), v)))
    return out


def build_map(game, m, base_ini=None):
    folder = os.path.join(game, 'KLExpansion', 'Maps', m)
    zp = [f for f in os.listdir(folder) if f.lower().endswith('_main.zip')][0]
    loc = Loc(os.path.join(folder, zp))
    ward = read_wardrobe(os.path.join(folder, 'KLWardrobe.ini'))
    ini = os.path.join(folder, 'KLTalk.ini')
    own = os.path.isfile(ini)
    talk, scenes, chatter, pools, pairs = parse_ini(open(ini if own else base_ini, 'rb').read().decode('latin1'))
    if not own:
        scenes = []
        talk['Map'] = m
        # a Dog Days map: keep only the keys this .LOC has (Who=Any: all eight voices)
        for p in pools:
            keep = []
            for k in p['keys']:
                if p['who'] == 'Any':
                    if merc_ok(loc, k):
                        keep.append(k)
                else:
                    s = loc.get(k)
                    if s:
                        keep.append(s)
            p['keys'] = keep
        pairs = [q for q in pairs if loc.ok(q['ckey']) and loc.ok(q['rkey'])]
    extra = named_pools(loc, ward)
    for name, who, on, keys in extra:
        pools.append(dict(name=name, who=who, on=on, keys=keys))
    ep = pair_list(loc, ward, extra)
    for c, ck, r, rk in ep:
        pairs.append(dict(cwho=c, ckey=ck, rwho=r, rkey=rk, wait=None))
    talk['Version'] = '2'; talk['Scenes'] = str(len(scenes))
    chatter['Once'] = '0'; chatter['KeyGap'] = str(KEY_GAP); chatter['PairChance'] = str(PAIR_CHANCE)
    chatter['Pools'] = str(len(pools)); chatter['Pairs'] = str(len(pairs))
    lines = ['; written by tools/kl_talk_chars.py (Version 2: re/talk.md 10) - belongs to the level archive beside it (hook part kltalk)',
             '; named pools / pairs are a GUESS of who speaks as whom (re/talk.md 10.2); every key is in this map\'s English .LOC with a sound id',
             '[Talk]']
    for k, v in talk.items():
        lines.append('%s=%s' % (k, v))
    out = '\n'.join(lines) + '\n'
    out += '\n'.join(s.rstrip('\n') for s in scenes) + ('\n' if scenes else '')
    out += '[Chatter]\n' + ''.join('%s=%s\n' % (k, v) for k, v in chatter.items())
    for i, p in enumerate(pools, 1):
        out += '[Pool.%d]\nName=%s\nWho=%s\nOn=%s\nKeys=%d\n' % (i, p['name'], p['who'], p['on'], len(p['keys']))
        out += ''.join('Key.%d=%s\n' % (j, k) for j, k in enumerate(p['keys'], 1))
    for i, q in enumerate(pairs, 1):
        out += '[Pair.%d]\nCall=%s,%s\nReply=%s,%s\n' % (i, q['cwho'], q['ckey'], q['rwho'], q['rkey'])
        if q.get('wait'):
            out += 'Wait=%s\n' % q['wait']
    return out, dict(pools=len(pools), pairs=len(pairs), extra_pools=len(extra), extra_pairs=len(ep), own=own, scenes=len(scenes))


def maps_of(game):
    d = os.path.join(game, 'KLExpansion', 'Maps')
    return sorted(m for m in os.listdir(d) if os.path.isdir(os.path.join(d, m)) and '.replaced-' not in m)


def check_text(text, loc, ward, label):
    """the hook's reading rules on a staged file: -> list of problems"""
    bad = []
    talk, scenes, chatter, pools, pairs = parse_ini(text)
    if talk.get('Version') != '2':
        bad.append('Version is %s' % talk.get('Version'))
    if int(talk.get('Scenes', 0)) != len(scenes):
        bad.append('Scenes=%s but %d [Scene.n] blocks' % (talk.get('Scenes'), len(scenes)))
    if int(chatter['Pools']) != len(pools) or int(chatter['Pairs']) != len(pairs):
        bad.append('Pools=/Pairs= do not match')
    if len(pools) > LIM['pool'] or len(pairs) > LIM['pair'] or len(scenes) > LIM['scene']:
        bad.append('over the hook limits: %d pools, %d pairs, %d scenes' % (len(pools), len(pairs), len(scenes)))
    names = {c.get('Name', '').lower(): n for n, c in ward.items()}
    words = {'kane', 'lynch', 'any', 'squad1', 'squad2', 'fed'}
    def who_ok(w):
        if w.lower() in words:
            return True
        if re.match(r'(?i)char\d+$', w):
            return int(w[4:]) in ward
        return w.lower() in names
    said = set()
    def key_ok(k, who, what):
        if len(k) >= LIM['keylen']:
            bad.append('%s: key too long' % what)
        if who.lower() == 'any':
            if not merc_ok(loc, k):
                bad.append('%s: %s lacks a _C1.._C8 form with sound' % (what, k))
        elif not loc.ok(k):
            bad.append('%s: %s not in the .LOC with a sound' % (what, k))
        elif loc.spell(k) != k:
            bad.append('%s: %s is spelled %s in the .LOC (the lookup is case sensitive)' % (what, k, loc.spell(k)))
        said.add(k.lower())
    for p in pools:
        if not who_ok(p['who']):
            bad.append('pool %s: Who=%s unknown' % (p['name'], p['who']))
        if len(p['keys']) > LIM['nkey']:
            bad.append('pool %s: %d keys, the hook holds %d' % (p['name'], len(p['keys']), LIM['nkey']))
        if len(set(k.lower() for k in p['keys'])) != len(p['keys']):
            bad.append('pool %s: a key twice' % p['name'])
        for k in p['keys']:
            key_ok(k, p['who'], 'pool ' + p['name'])
    for i, q in enumerate(pairs, 1):
        for w, k, side in ((q['cwho'], q['ckey'], 'call'), (q['rwho'], q['rkey'], 'reply')):
            if not who_ok(w):
                bad.append('pair %d %s: %s unknown' % (i, side, w))
            key_ok(k, 'plain', 'pair %d %s' % (i, side))
        if q['cwho'].lower() == q['rwho'].lower():
            bad.append('pair %d: call and reply by the same character' % i)
    for sc in scenes:
        for ln in sc.splitlines():
            m = re.match(r'Line\.\d+=([^,]+),[^,]+,[^,]+,(.+)$', ln)
            if m and not who_ok(m.group(1)):
                bad.append('scene line speaker %s' % m.group(1))
            if m and not loc.ok(m.group(2)):
                bad.append('scene key %s not in the .LOC with a sound' % m.group(2))
    if len(said) > LIM['said']:
        bad.append('%d distinct keys, the hook tracks %d said keys per level' % (len(said), LIM['said']))
    return bad


def main():
    a = sys.argv[1:]
    opt = lambda n, d=None: (a[a.index(n) + 1] if n in a else d)
    game, out = opt('--game', GAME), opt('--out', OUT)
    cmd = a[0] if a else 'help'
    if cmd == 'list':
        for num, name, voice, part, idle in CHARS:
            print('%2d %-10s stand-in %-7s slice %d idle %s; Stage2=Advance Down=ManDown Money=Exclamation (slice %d)' % (num, name, voice, part, '+'.join(idle), part))
        print(' 9 Kane / 10 Lynch: their own AllLevels/Oneliners/*_Kane / *_Lynch;  1..8 mercs: Who=Any pools and explicit _C<slot+1> keys in pairs')
        return
    if cmd not in ('build', 'check'):
        print(__doc__); sys.exit(2)
    maps = opt('--maps').split(',') if opt('--maps') else maps_of(game)
    base_ini = os.path.join(game, 'KLExpansion', 'Maps', 'DM01', 'KLTalk.ini')
    problems = 0
    for m in maps:
        folder = os.path.join(game, 'KLExpansion', 'Maps', m)
        zp = [f for f in os.listdir(folder) if f.lower().endswith('_main.zip')][0]
        loc = Loc(os.path.join(folder, zp))
        ward = read_wardrobe(os.path.join(folder, 'KLWardrobe.ini'))
        if cmd == 'build':
            text, info = build_map(game, m, base_ini)
            os.makedirs(os.path.join(out, m), exist_ok=True)
            with open(os.path.join(out, m, 'KLTalk.ini'), 'wb') as f:
                f.write(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('latin1'))
        else:
            text = open(os.path.join(out, m, 'KLTalk.ini'), 'rb').read().decode('latin1')
            info = {}
        bad = check_text(text, loc, ward, m)
        problems += len(bad)
        print('%-8s %s %s' % (m, 'OK ' if not bad else 'BAD', ' '.join('%s=%s' % kv for kv in info.items())))
        for b in bad[:8]:
            print('    ' + b)
    print('problems: %d' % problems)
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
