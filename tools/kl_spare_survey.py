#!/usr/bin/env python3
r"""
kl_spare_survey.py - per shop item id 0-63 of ONE map zip: which weapon template sits on it, its hold folder, clip,
ammo node, sound definition, model root (and which other templates share that root) and how many NPCs carry it.
READ ONLY (opens the zip, writes nothing). Feeds re/shop_page2_layout.md (which spare id can host which page-2 gun).

    python kl_spare_survey.py <map zip>            table of all ids 0-63 (ids with no template are listed as '-')
    python kl_spare_survey.py <map zip> --spare    only the ids the shop table does not use (kl_shop_extra rows)
    python kl_spare_survey.py <map zip> --json     the same as JSON

Fields: item = eFF2Item enum number (dd_enums.json) of the template's InventoryBinding; hold = kl_arms.FOLDER (the
/Weapon_Handling folder name), slots = its slot count in the Swat_02 set of the map's .ANM (FOLDER_MIN 20 = a real
folder; the shield pistols have 3); clip = field 15 of the template's ZFFItemTemplateAmmo (node named by weapon field 18);
sound = the weapon's sound-definition name (kl_map_guns.sound_of); root = the model chunk of the template's Ground
object (kl_chars.person), shared = other templates with the same root; ai = NPCs whose primary or secondary it is.
The hold CLASS (pistol / smg-rifle / mg / ...) is derived from the folder name by CLASS below, a GUESS where marked '?'.
"""
import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BS = '\\'

# hold folder prefix -> class used in the layout. GUESS ('?') for names not seen in a pistol / rifle role.
CLASS = (('hg_', 'pistol'), ('smg_', 'smg'), ('rifle_', 'rifle'), ('mg_', 'mg'), ('sn_', 'sniper'), ('shotgun_', 'shotgun'),
         ('launcher_', 'launcher'), ('rpg_', 'rpg'), ('grenade_', 'grenade'))


def hold_class(folder):
    f = folder.lower()
    if 'human_shield' in f:
        return 'shield'
    return next((c for p, c in CLASS if f.startswith(p)), '?' if f else '-')


def survey(zip_path):
    """-> (rows [dict, one per template with an item], shop items set, info)."""
    import kl_fa, kl_arms, kl_map_ai as M, kl_chars as C, kl_map_guns as MG, kl_shop_extra as X
    sc, snd, _loc = kl_fa.load(zip_path)
    with open(os.path.join(HERE, 'dd_enums.json')) as f:
        num = {n: v for e in json.load(f) for v, n in e if isinstance(n, str) and n.startswith('eFF2Item')}
    eq = kl_arms.equipment(sc)
    try:
        swat = kl_arms.handling(kl_arms.read_anm(zip_path)).get('swat_02', {})
    except Exception as e:       # no .ANM member: slots stay 0
        print('# no .ANM readable: %s' % e, file=sys.stderr); swat = {}
    carried = collections.Counter()
    for _k, _squad, w, w2, _g1, _g2, _s in kl_arms.carriers(sc):
        carried[w.lower()] += 1
        carried[w2.lower()] += 1
    carried.pop('', None)
    try:
        import kl_snd as S
        sndobj = S.Snd('dd', snd) if snd else None
    except Exception:
        sndobj = None
    rows = []
    for name, e in eq.items():
        k = next(iter(sc.resolve(e['path'])), None)
        v = kl_fa.node_values(sc, k)
        ammo = sc.resolve(M.full(v[MG_AMMO][0])) if v[MG_AMMO] else []
        av = kl_fa.node_values(sc, ammo[0]) if len(ammo) == 1 else None
        try:
            snm = MG.sound_name(sndobj, MG.sound_of(sc, k)) if sndobj else '?'
        except Exception as x:
            snm = '? (%s)' % x
        ground = next((c for c in range(1, len(sc.nodes)) if sc.path[c].startswith(e['path'] + BS + 'Ground') and sc.cls(c) == 'ZLNKOBJ'
                       and sc.path[c].count(BS) == e['path'].count(BS) + 1), None)
        root = C.person(sc, ground)[0] if ground is not None else 0
        rows.append(dict(item=num.get(e['item'], -1), template=e['name'], enum=e['item'], hold=e['folder'], cls=hold_class(e['folder']),
                         slots=swat.get(e['folder'], 0), hands=e['hands'], wt=e['wt'],
                         clip=av[AMMO_CLIP] if av else None, ammo=sc.path[ammo[0]].rsplit(BS, 1)[-1] if len(ammo) == 1 else '',
                         sound=snm, root=root, ai=carried.get(name, 0)))
    by_root = collections.defaultdict(list)
    for r in rows:
        if r['root']:
            by_root[r['root']].append(r['template'])
    for r in rows:
        r['shared'] = [t for t in by_root.get(r['root'], []) if t != r['template']]
    rows.sort(key=lambda r: (r['item'], r['template']))
    shop = {x[0] for x in X.rows()}
    return rows, shop, dict(npcs=sum(1 for _ in kl_arms.carriers(sc)))


MG_AMMO, AMMO_CLIP = 18, 15


def main():
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return 2
    rows, shop, info = survey(a[0])
    if '--spare' in a:
        rows = [r for r in rows if r['item'] not in shop]
    if '--json' in a:
        print(json.dumps(dict(shop=sorted(shop), rows=rows, **info), indent=1)); return 0
    print('# %s   NPCs: %d   shop items: %s' % (a[0], info['npcs'], sorted(shop)))
    print('%-3s %-5s %-28s %-24s %-8s %5s %-4s %-24s %-24s %-9s %2s  %s' % ('id', 'shop', 'template', 'hold', 'class', 'slots', 'clip', 'ammo node', 'sound', 'root', 'ai', 'shares model with'))
    have = set()
    for r in rows:
        have.add(r['item'])
        print('%-3d %-5s %-28s %-24s %-8s %5d %-4s %-24s %-24s %-9d %2d  %s' % (
            r['item'], 'yes' if r['item'] in shop else '', r['template'], r['hold'], r['cls'], r['slots'],
            '-' if r['clip'] is None else r['clip'], r['ammo'], r['sound'], r['root'], r['ai'], ','.join(r['shared'])))
    if '--spare' not in a:
        print('ids with no template: %s' % [i for i in range(64) if i not in have])
    return 0


if __name__ == '__main__':
    sys.exit(main())
