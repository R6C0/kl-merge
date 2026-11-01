#!/usr/bin/env python3
"""
kl_trig_census.py - which trigger boxes of a level a Fragile Alliance AI heister can NOT set off online (read-only).

    python tools/kl_trig_census.py [--maps DM01,DM09,...] [--root <KLExpansion\\Maps>] [--zip <_Main.zip> ...] [--detail] [--md]

For every level archive it reads the three box controllers and sorts them (re/bots_trigger_cops_1028.md section 8):
  TriggerBox (ZTriggerBox, fields re/triggerbox.md): in Arcade a team-2 actor counts as a PLAYER (0x7f6850) when ECPS is BOTH or
      FA_MERCONLY and field 15 (local-only) is 0; online 0x7f6850 is false, so such a box misses the bots. 'bot-eligible' = enabled,
      enter or left bool set, ECPS BOTH/FA_MERCONLY, not local-only, EFAMPS lets a Fragile Alliance round through. A box whose own
      'team 2 enters' bool (field 6) is set is also reached by the game's team flag online: marked 'team-2 flag'.
  TriggerBox2 (ZTriggerBox2): field 3 = players only (+0x44). 1 = a bot misses it online; 0 = every tracked object counts (bots too).
  OnlineTriggerBox (ZOnlineTriggerBox): field 1 = players only (+0x38). Fields 2..5 are GUESS (+0x39 class mask, +0x40 delay at 5).
Each box gets a KIND from the names of what it sends to (and its own node path): loot (MoneyStack/DropMoney/cash drawer/jewel), civ (civilian
crowd), npc (a TriggerBox2 that targets only its own node: a character's interact box), cop (squad / enemy / police / spawn), door (door / lift /
elevator / gate / leaf), script (timer / delay / proxy / anim / camera / music / sound / effect), other. loot, civ and npc never count as 'needs'.
KIND is a keyword GUESS on node paths; the table says what the names say, not what the script does at run time.
Exit 0 always (a table, not a verdict); 1 when no level could be read.
"""
import argparse, collections, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPS = ['DM01', 'DM01B', 'DM02', 'DM03', 'DM03A', 'DM05A', 'DM06', 'DM06B', 'DM07', 'DM09', 'DM11B', 'DM11S']
STOCK = ['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 'F09']

# keyword GUESS on the lower-case node paths a box sends to (checked in this order)
KINDS = [
    ('loot', re.compile(r'moneystack|dropmoney|money|loot|pickup|cashdrawer|cashbox|cashregister|jewel|watches|_ring')),
    ('civ', re.compile(r'civilian|civ_|crowd|waitress|clerk|gangmember|hostage')),
    ('cop', re.compile(r'squad|enem|police|cop|swat|spawn|reinforc|guard|ai_players|wave')),
    ('door', re.compile(r'door|lift|elevator|gate|leaf|shutter|barrier|open|close')),
    ('script', re.compile(r'timer|delay|proxy|anim|camera|cam_|music|sound|speak|audio|fx|effect|blowup|debris|smoke|light|alarm|siren|window')),
]
IGNORE = ('loot', 'civ', 'npc')           # never a cop wave / door / script
FA_OK = ('EFAMPS_ALL_MODES', 'EFAMPS_FA', 'EFAMPS_FA_UCC', 'EFAMPS_FA_TEAM')   # modes a Fragile Alliance round passes (re/triggerbox.md step 3)


def kind_of(text):
    t = text.lower()
    for k, rx in KINDS:
        if rx.search(t):
            return k
    return 'other'


def level_kind(own, targets, cls=''):
    """loot beats everything (its own node name is enough); then the targets; then the box's own path."""
    if kind_of(own) in ('loot', 'civ'):
        return kind_of(own)
    if cls == 'TriggerBox2' and targets and all(t == own for t in targets):
        return 'npc'
    ks = [kind_of(t) for t in targets]
    for k in ('loot', 'civ', 'cop', 'door', 'script'):
        if k in ks:
            return k
    return kind_of(own) if not targets else 'other'


def short(p):
    return p.replace('ROOT\\', '', 1) if p.startswith('ROOT\\') else p


def boxes(sc, controllers):
    """-> list of dicts, one per box controller of the three classes."""
    out = []
    for name in ('TriggerBox', 'TriggerBox2', 'OnlineTriggerBox'):
        for k, _i, v in controllers(sc, name):
            own = sc.path[k]
            if name == 'TriggerBox' and len(v) >= 18:
                tg = [t for t in v[17] if isinstance(t, str)] if isinstance(v[17], list) else []
                ecps, efamps = v[14], v[16]
                enter, left = bool(v[1]) or bool(v[4]), bool(v[3])
                elig = (bool(v[0]) and (bool(v[1]) or bool(v[3])) and ecps in ('ECPS_BOTH', 'ECPS_FA_MERCONLY')
                        and not v[15] and efamps in FA_OK)
                # why klhook OnlineTriggers (klbf_trig_tick) skips an eligible box: it needs the enter bool, no on-leave action, no tracked objects, a count 1..8
                gap = ('left' if v[3] else 'tracked' if v[12] else 'count%d' % v[2] if not 1 <= v[2] <= 8 else 'no-enter' if not v[1] else '')
                out.append(dict(cls=name, path=own, targets=tg, players_only=None, bot_eligible=elig, team2_flag=bool(v[6]), gap=gap,
                                oneshot=v[10] == 0xffffffff, left=left, ecps=ecps, efamps=efamps, local=bool(v[15])))
            elif name == 'TriggerBox2' and len(v) >= 7:
                tg = [t for t in v[0] if isinstance(t, str)] if isinstance(v[0], list) else []
                out.append(dict(cls=name, path=own, targets=tg, players_only=bool(v[3]), bot_eligible=not v[3], team2_flag=False,
                                oneshot=bool(v[4]), left=False, ecps='', efamps='', local=False, msg=v[5]))
            elif name == 'OnlineTriggerBox' and len(v) >= 6:
                tg = [t for t in v[0] if isinstance(t, str)] if isinstance(v[0], list) else []
                # GUESS: field 1 = +0x38 players only, field 5 = +0x40 delay (kl2 0x49ab90, re/bots_trigger_cops_1028.md section 7)
                out.append(dict(cls=name, path=own, targets=tg, players_only=bool(v[1]), bot_eligible=not v[1], team2_flag=False,
                                oneshot=False, left=False, ecps='', efamps='', local=False, msg=v[4]))
    for b in out:
        b['kind'] = level_kind(b['path'], b['targets'], b['cls'])
    return out


def summarize(bs):
    """-> {'TriggerBox': Counter, ...}: per class, counts by (kind, 'missed' = bots miss it online / 'ok' = bots already reach it)."""
    res = {}
    for cls in ('TriggerBox', 'TriggerBox2', 'OnlineTriggerBox'):
        c = collections.Counter()
        for b in bs:
            if b['cls'] != cls:
                continue
            if cls == 'TriggerBox':
                missed = b['bot_eligible'] and not b['team2_flag']      # Arcade counts the bot; online only the player count misses it
            else:
                missed = bool(b['players_only'])
            c[(b['kind'], 'missed' if missed else 'ok')] += 1
            if cls == 'TriggerBox' and missed and b['gap'] and b['kind'] not in IGNORE:
                c[('gap', b['gap'])] += 1
        res[cls] = c
    return res


def level_zip(name, root):
    d = os.path.join(root, name)
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if re.match(r'^F\d\d_Main\.zip$', f):
                return os.path.join(d, f)
    return None


def table(rows):
    cols = ['Map', 'Slot', 'TB total', 'TB missed (cop/door/script/other)', 'TB2 non-loot players-only (cop/door/script/other)',
            'TB2 non-loot all-objects', 'OnlineTB (players-only)', 'Needs', 'TB hook gap']
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for r in rows:
        out.append('| ' + ' | '.join(r) + ' |')
    return '\n'.join(out)


def row_of(name, slot, bs):
    s = summarize(bs)

    def split(cls, state):
        c = s[cls]
        return '/'.join(str(c[(k, state)]) for k in ('cop', 'door', 'script', 'other')) + ' +%d civ/npc' % (c[('civ', state)] + c[('npc', state)])

    def n(cls, state):
        return sum(v for (k, st), v in s[cls].items() if st == state and k not in IGNORE)
    tb_total = sum(v for (k, _st), v in s['TriggerBox'].items() if k != 'gap')
    otb = sum(v for (k, _st), v in s['OnlineTriggerBox'].items() if k != 'gap')
    otb_p = sum(v for (k, st), v in s['OnlineTriggerBox'].items() if st == 'missed')
    gaps = s['TriggerBox']
    gap = ', '.join('%s %d' % (g, gaps[('gap', g)]) for g in ('left', 'tracked', 'no-enter') if gaps[('gap', g)])
    need = []
    if n('TriggerBox', 'missed'):
        need.append('OnlineTriggers=1')
    if n('TriggerBox2', 'missed') or otb_p:
        need.append('OnlineTriggersExtra=1')
    return [name, slot, str(tb_total), '%d (%s)' % (n('TriggerBox', 'missed'), split('TriggerBox', 'missed')),
            '%d (%s)' % (n('TriggerBox2', 'missed'), split('TriggerBox2', 'missed')),
            str(n('TriggerBox2', 'ok')), '%d (%d)' % (otb, otb_p), ' + '.join(need) or 'none', gap or '-']


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.path.join(DD, 'KLExpansion', 'Maps'))
    ap.add_argument('--maps', default=','.join(MAPS))
    ap.add_argument('--zip', action='append', default=[])
    ap.add_argument('--detail', action='store_true', help='list every missed non-loot box')
    ap.add_argument('--md', action='store_true')
    a = ap.parse_args(argv)
    import kl_fa
    todo = [(os.path.basename(z), os.path.basename(z)[:3], z) for z in a.zip]
    for m in [x for x in a.maps.split(',') if x]:
        z = level_zip(m, a.root)
        todo.append((m, os.path.basename(z)[:3] if z else '-', z))
    rows, found = [], 0
    for name, slot, z in todo:
        if not z or not os.path.isfile(z):
            rows.append([name, slot, 'not installed'] + ['-'] * 6)
            continue
        sc, _snd, _loc = kl_fa.load(z)
        bs = boxes(sc, kl_fa.controllers)
        found += 1
        rows.append(row_of(name, slot, bs))
        if a.detail:
            for b in bs:
                miss = (b['bot_eligible'] and not b['team2_flag']) if b['cls'] == 'TriggerBox' else b['players_only']
                if miss and b['kind'] not in IGNORE:
                    print('%s  %-16s %-6s %s -> %s%s' % (name, b['cls'], b['kind'], short(b['path']),
                          ', '.join(short(t) for t in b['targets'][:3]) or '-', '  [one-shot]' if b['oneshot'] else ''))
    print(table(rows))
    print('\nRESULT: %s (%d level(s) read)' % ('OK' if found else 'NONE', found))
    return 0 if found else 1


if __name__ == '__main__':
    sys.exit(main())
