#!/usr/bin/env python3
"""
What the enemies of a Dead Men map carry under Dog Days' systems. Spec and findings: re/combat.md.

    python kl_arms.py templates [F07]           every weapon template of a level's equipment tree: class, hands,
                                                item, slots of its /Weapon_Handling folder, stock NPC use, verdict
    python kl_arms.py table <archive | level>   who carries what, per squad (top-level subtree)
    python kl_arms.py compare <old> <new>       the same for two builds of one map, side by side
    python kl_arms.py check <archive | level>   the findings of check(); exit 1 if one is BROKEN
    python kl_arms.py patch <build> <armed archive> <out folder>
                                                a built level (folder or archive) with ONLY the combat fixes: the weapon
                                                fields of its actors as in <armed archive> (a build of the same map made
                                                with kl_arms: same nodes) and kl_fa.define_master(). Nothing but the .prp
                                                member changes - the smallest step from a build that has been played
    python kl_arms.py stock                     the control: the 21 stock levels must give 0 findings, and the
                                                census of who carries what must equal STOCK_NPC below

WHY (2026-10-09, the owner's round on Retomoto): kl_graft.dm_rename replaced a Dead Men weapon Dog Days lacks by
'one of S's whose name starts alike'. The equipment tree is in file order, so 'HG_' found HG_M9Beretta_Human_Shield
first: 57 of the 65 Dead Men characters of the played level carried the pistol Dog Days hands a PLAYER while he
holds a human shield ('they all have the same pistol'); 'Smg_' found SMG_UMP_SBR, 'Mg_' found
Mg_Minimi_SPW_L10_Heli (a helicopter door gun). No stock level of Dog Days gives any of the three to an NPC.

THE RULE NOW
  1 A Dead Men weapon has a CLASS (DM below: every one of the 36 templates of Dead Men's 20 levels, by its own
    WT_ enum). A class has a POOL of Dog Days templates. A template is in a pool only if
      - at least one of the 21 stock Dog Days levels gives it to an NPC (STOCK_NPC, the census), and
      - its name is not a special variant (SPECIAL: human shield, helicopter, player-only, level-tuned NPC), and
    it is handed to an actor only if
      - the level's equipment tree has it (all 61 are in every Fragile Alliance level), and
      - the actor's animation set has its /Weapon_Handling/<item> folder (FOLDER_MIN slots or more). A Dead Men
        character set is a copy of a Dog Days one (kl_anmjoin.STAND_IN), so that is tested on the stand-in.
    Sounds: a template's fire / reload sounds are offsets into S's bank, which the graft never moves.
  2 What the level designer gave stays the DEFAULT: a rifle carrier gets a rifle, the MG guy an MG.
  3 VARIETY (the owner asked for it; every number in MIX is a GUESS): the carriers of one class in one zone of
    the map are split over classes by MIX, heavier the deeper the zone lies (zone = the first three-digit
    number of the squad's name, '020_Office' .. '070_Elevators'; LEVEL_DEPTH places a map on the 0..1 scale).
    Which template of a pool an actor gets, and who of a zone is upgraded, follows a hash of the seed and the
    actor's scene path: the same seed and map give the same build, whatever else is in the level.
  4 NOT handed out (conservative, each is a choice the lead can flip with arm(launchers=True / grenades=True)):
      launchers  no stock Dog Days NPC carries one (0 in 21 levels). A launcher primary becomes an SMG, a
                 launcher secondary is emptied.
      grenades   no stock Dog Days NPC has one in its grenade fields (0 in 21 levels): emptied.
  5 An actor whose animation set has no weapon folder at all (Dead Men's civilians carry an MP5 in the data;
    their stand-in is Dog Days' Civilian set) gets no weapon, as all 40 stock Fragile Alliance civilians.

FOR kl_graft (build(), right after the join that applies dm_rename - which no longer guesses weapons):
    import kl_arms
    rep = kl_arms.arm(Jn, S['.ANM'], m_name, nodes={j for j, (sc, _k) in enumerate(Jn.origin) if sc is M.prp}, log=log)
and kl_fa.check(sc, snd, loc, anm) runs check() below (verify() passes the joined .ANM).
"""
import collections, os, random, re, struct, sys, zipfile, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_prpjoin as J
from kl_prp import units

SEED = 2026
FOLDER_MIN = 20                 # the 39 real folders of a stock character set have 29..57 slots; HG_M_77B_Human_Shield has 3
WEAPONS = '\\AllLevels/equipment.zip\\Weapon\\'
SPECIAL = re.compile(r'human_shield|_heli|_player|_hind|_l\d\d_npc', re.I)

# Dead Men's 36 weapon templates (all 20 levels have all of them), class by the template's own WT_ enum; the
# vehicle guns and the knife are no hand weapon ('none').
DM = {
    'HG_HK_USP_01': 'pistol', 'HG_HK_USP_01_Carry': 'pistol', 'HG_HK_USP_01_Light': 'pistol', 'Hg_HK_USP_01_Silenced': 'pistol',
    'Gun_Taurus_01': 'revolver',
    'Smg_MP5-A3_01': 'smg', 'Smg_MP5-A3_01_Light': 'smg', 'Smg_FN_P90_01': 'smg', 'Smg_SteyrTMP_01': 'smg',
    'Rifle_M4A1_01': 'rifle', 'Rifle_M4A1_01_Light': 'rifle', 'Rifle_AK74_01': 'rifle', 'Rifle_SG552_01': 'rifle',
    'Rifle_RugerMini14_01': 'rifle',
    'Shotgun_Remington_870': 'shotgun', 'Rifle_Spas12_01': 'shotgun',
    'Mg_Minimi_SPW_01': 'mg', 'MG_PKMSN2_01': 'mg',
    'Sn_Rem700_01': 'sniper', 'Sn_Rem700_Silenced': 'sniper',
    'Launcher_HK69A1_01': 'launcher', 'Launcher_HK69A1_01Flare': 'launcher', 'Launcher_HK69A1_01TearGas': 'launcher',
    'RPG_7V': 'rocket', 'RPG_7V_Inaccurate': 'rocket',
    'Grenade_Fragmentation': 'grenade', 'Grenade_Incendiary': 'grenade', 'Grenade_Smoke': 'grenade', 'Grenade_TearGas': 'grenade',
    'Kn_Push_Blade_01': 'none', 'Btr_BTR-90': 'none', 'Mg_Hind': 'none', 'Tank_T-72': 'none',
    'Technical_UAZ_And_MountedWeapon': 'none', 'Mg_Minimi_SPW_01_Heli': 'none', 'RPG_7V_Hind': 'none',
}
DM_LOWER = {k.lower(): v for k, v in DM.items()}

# Census of the 21 stock Dog Days levels (python kl_arms.py stock recounts it): template -> (NPCs carrying it as
# primary in the nine Fragile Alliance levels, in the twelve story levels, as secondary anywhere).
STOCK_NPC = {
    'HG_DesertEagle': (1, 5, 12), 'HG_M-77B': (18, 37, 2), 'HG_M9Beretta': (26, 27, 1), 'HG_M9Beretta_S': (0, 1, 1),
    'HG_Revolver_Police': (0, 29, 0), 'HG_SW_MP45': (4, 0, 0), 'HG_SigSauer226': (7, 0, 0),
    'MG_GP_Type88': (0, 9, 0), 'MG_GP_Type88_L09_NPC': (0, 4, 0), 'RPG_7V': (0, 8, 0),
    'Rifle_AK74': (137, 39, 0), 'Rifle_FN_SCAR': (6, 0, 0), 'Rifle_Type81': (2, 0, 0), 'Rifle_Type88': (2, 47, 0),
    'Rifle_Type88_S': (4, 10, 0), 'Rifle_Type95_C': (0, 134, 0), 'Rifle_Type95_L09_NPC': (0, 50, 0),
    'Rifle_zastavam85': (68, 43, 1), 'SMG_HK_sp89': (5, 1, 0), 'SMG_MAC_10': (13, 84, 0), 'SMG_MPi69': (20, 0, 1),
    'SMG_SA61': (0, 41, 0), 'SMG_Type05': (26, 103, 0), 'SMG_Type05_S': (0, 81, 0), 'SMG_Type79': (35, 100, 0),
    'Shotgun_Hawk_Bullpup': (0, 53, 0), 'Shotgun_Hawk_Police': (0, 54, 0), 'Shotgun_Hawk_SawnOff': (0, 30, 1),
}

# class -> [(Dog Days template, weight)]. Every template is in STOCK_NPC and not SPECIAL (asserted at import).
# The weights are GUESSES: the heaviest is what stock Fragile Alliance gives its police of that class.
POOLS = {
    'pistol':   [('HG_M9Beretta', 4), ('HG_SW_MP45', 3), ('HG_SigSauer226', 3), ('HG_M-77B', 2)],
    'revolver': [('HG_Revolver_Police', 1)],
    'smg':      [('SMG_Type05', 4), ('SMG_MPi69', 3), ('SMG_Type79', 3), ('SMG_HK_sp89', 2), ('SMG_MAC_10', 1)],
    'rifle':    [('Rifle_AK74', 5), ('Rifle_Type81', 2), ('Rifle_FN_SCAR', 2)],
    'shotgun':  [('Shotgun_Hawk_Police', 3), ('Shotgun_Hawk_Bullpup', 1)],   # story levels only: no stock FA NPC has a shotgun
    'mg':       [('MG_GP_Type88', 1)],                                       # story levels only (L10)
    'sniper':   [('Rifle_Type88_S', 1)],     # GUESS: the scoped semi-automatic stock FA gives its marksmen (F02, F08);
                                             # Sn_Rem700 exists but no stock NPC carries it
    'rocket':   [('RPG_7V', 1)],
}
# A Dead Men weapon that has a namesake or a close relative: that template's weight x 3 (GUESS)
PREFER = {'Rifle_AK74_01': 'Rifle_AK74', 'Rifle_M4A1_01': 'Rifle_AK74', 'Rifle_M4A1_01_Light': 'Rifle_AK74',
          'Smg_MP5-A3_01': 'SMG_Type05', 'Smg_MP5-A3_01_Light': 'SMG_Type05', 'Smg_FN_P90_01': 'SMG_MPi69',
          'Rifle_Spas12_01': 'Shotgun_Hawk_Bullpup'}
# class Dead Men gave -> [(class handed out, share at depth 0, share at depth 1)]; the first is the class itself.
# ALL GUESSES, the owner's wish in numbers: 'guards mostly pistols with some SMGs, heavier squads with
# shotguns / rifles deeper in the tower and on the street'.
MIX = {
    'pistol': [('pistol', 0.70, 0.30), ('smg', 0.25, 0.35), ('shotgun', 0.05, 0.20), ('rifle', 0.00, 0.15)],
    'smg':    [('smg', 0.85, 0.55), ('rifle', 0.10, 0.30), ('shotgun', 0.05, 0.15)],
}
# where a map lies on the depth scale (GUESS): Retomoto's tower is the first half of the round, its street the second
LEVEL_DEPTH = {'M09_A': (0.0, 0.6), 'M09_B': (0.6, 1.0)}
DEPTH_DEFAULT = (0.2, 0.8)
# Retomoto (owner, 2026-10-09 late: 'guys with pistols will rush you then the higher the caliber the more advanced /
# technical they play'): squad -> the class all its armed actors get, whatever MIX would deal (GUESSES; the squads
# kl_fa_author.ROOM_* makes run, rush and hold - re/retomoto_ai.md 3 and 7)
FORCE = {'AI_Players!Enemies!020_Office!Squad_Guards_Inside_03': 'pistol',      # the rushers
         'AI_Players!Enemies!020_Office!Squad_Guards_Inside_01': 'pistol',
         'AI_Players!Enemies!020_Office!Squad_Guards_Inside_02': 'smg',         # hold the doorway
         'AI_Players!Enemies!030_Reception!Squad_ShootBeforeStorm': 'smg',
         'AI_Players!Enemies!030_Reception!Squad_Hallway#01': 'rifle',
         'AI_Players!Enemies!030_Reception!Squad_Hallway': 'shotgun'}
# ... and the class handed out sets ZSoldier field 3 (ESkillLevel), on the maps of SKILL_LEVELS only. Dead Men's
# guards are all eRegular, its police eRegular / eVeteran; eVeteran actors fought in the owner's rounds. No stock
# Fragile Alliance level uses eAmateur or eElite (their police are eCustom / eRegular): what the game makes of
# them is a GUESS. The style (field 0) is left alone: it may choose animations. None = the pass is off.
SKILL = {'pistol': 'eAmateur', 'revolver': 'eAmateur', 'smg': 'eRegular', 'shotgun': 'eRegular', 'rifle': 'eVeteran',
         'mg': 'eVeteran', 'sniper': 'eElite', 'rocket': 'eVeteran'}
SKILL_LEVELS = ('M09_A', 'M09_B')
SKILL_FIELD = 3
FALLBACK = ('pistol', 'smg', 'rifle')       # when an actor's set cannot play the class it should get
ZONE = re.compile(r'(?:^|!)(\d{3})_')

# Item enum -> the name kl2.exe puts into '/Weapon_Handling/%s/...' (the table at 0x154a650, filled by 0x4b1530;
# entry = item enum value for 1..50, read from the code). Variants share their base weapon's folder. The last three
# entries of the table are GRENADE_LAUNCHER_HK69A1 and twice HG_M_77B_Human_Shield: which items index them was not
# read - ASSUMPTION that it is the launchers and the two human-shield pistols (a stock character set has 3 slots
# in that folder, against 29..57 for a real weapon: an NPC handed such a pistol has no aim / reload / cover clips).
_F = ('HG_SW_MP45 HG_TaurusJudge HG_Revolver_Police HG_SigSauer226 HG_ColtCobra HG_M_77B HG_M_77B=HG_M_77B_Silenced '
      'HG_M9Beretta HG_M9Beretta=HG_M9Beretta_Silenced HG_DesertEagle HG_TT_33 Shotgun_Hawk_Bullpup Shotgun_Hawk_Police '
      'Shotgun_Hawk_SawnOff Shotgun_TPS Shotgun_Remington_870 Shotgun_Spas_12 SMG_SA61 SMG_UMP_SBR SMG_UMP '
      'SMG_UMP=SMG_UMP_Silenced SMG_HK_SP89_Silenced SMG_MAC_10 SMG_MAC_10=SMG_MAC_10_Silenced SMG_MPI69 SMG_Type79 '
      'SMG_Type05 SMG_Type05=SMG_Type05_Silenced Rifle_Zastavam85 Rifle_FN_SCAR Rifle_AK47 Rifle_AK74 Rifle_Type81 '
      'Rifle_Type88 Rifle_Type88=Rifle_Type88_L09_NPC Rifle_Type88=Rifle_Type88_Scoped Rifle_Type95 '
      'Rifle_Type95=Rifle_Type95_L09_NPC Rifle_Type95=Rifle_Type95_Scoped MG_GP_Type88 MG_GP_Type88=MG_GP_Type88_L09_NPC '
      'MG_GP_Type88=MG_GP_Type88_L09_Heli MG_GP_Type88=MG_GP_Type88_L09_Heli_Player MG_GP_Type88=MG_GP_Type88_L10_Heli '
      'MG_MiniMi_SPW=MG_MiniMi_SPW_L09_Heli_Player MG_MiniMi_SPW=MG_MiniMi_SPW_L10_Heli MG_MiniMi_SPW '
      'MG_MiniMi_SPW=MG_MiniMi_SPW_Heli SN_REM700=Sn_Rem700 RPG_7V=RocketLauncher '
      'GRENADE_LAUNCHER_HK69A1=GrenadeLauncher GRENADE_LAUNCHER_HK69A1=GrenadeLauncher_Gas GRENADE_LAUNCHER_HK69A1=GrenadeLauncher_Flare '
      'HG_M_77B_Human_Shield HG_M_77B_Human_Shield=HG_M9Beretta_Human_Shield')
FOLDER = {'eFF2Item' + x.split('=')[-1]: x.split('=')[0].lower() for x in _F.split()}

for _c, _pool in POOLS.items():
    for _t, _w in _pool:
        assert _t in STOCK_NPC and not SPECIAL.search(_t), _t


# ------------------------------------------------------------------ reading
def _values(sc, k):
    import kl_fa
    return kl_fa.node_values(sc, k)


def fields():
    """Indices of ZFFActor's weapon fields in a Dog Days object: primary, secondary, two grenades, animation set."""
    lab = J.labels('dd', 'ZFFActor')
    return [lab.index('ZFFActor[%d]' % i) for i in (1, 3, 4, 5)] + [lab.index('ZLNKOBJ[2]')]


def equipment(sc):
    """{template name, lower case: info} of the level's weapon templates (the children of ...equipment.zip\\Weapon):
    name, path, wt (WT_ enum), hands (IH_ enum), item (InventoryBinding's enum name), folder (the name of its
    /Weapon_Handling folder, lower case: FOLDER)."""
    import kl_fa
    out = {}
    for e in [k for k in range(1, len(sc.nodes)) if sc.path[k].lower().endswith('equipment.zip\\weapon')]:
        for c in range(e + 1, sc.end[e]):
            if sc.parent[c] != e:
                continue
            v = [x for x in _values(sc, c) if isinstance(x, str)]
            bind = [kl_fa.value(sc, u) for nm, body in sc.nodes[c]['ctrls'] if sc.p.key(nm) == 'InventoryBinding' for u in units(body[1:-1])]
            item = next((x for x in bind if isinstance(x, str) and x.startswith('eFF2Item') and not x.startswith('eFF2ItemType')), '')
            out[sc.names[c].lower()] = {
                'name': sc.names[c], 'path': sc.path[c], 'item': item, 'folder': FOLDER.get(item, ''),
                'wt': next((x for x in v if x.startswith('WT_')), ''), 'hands': next((x for x in v if x.startswith('IH_')), '')}
    return out


def handling(anm):
    """{animation set, lower case: {weapon folder, lower case: slots}} of an .ANM (bytes or kl_anm.Anm)."""
    import kl_anm
    a = anm if isinstance(anm, kl_anm.Anm) else kl_anm.Anm(anm, 'dd')
    out = {}
    for c in a.cols:
        n = collections.Counter()
        for slot in c.lists():
            p = a.slots[slot].split('/')
            if len(p) > 3 and p[1] == 'Weapon_Handling':
                n[p[2].lower()] += 1
        out[c.short.lower()] = dict(n)
    return out


def folders_of(hand, anim_set):
    """The weapon folders the set an actor names will have: its own, else those of its stand-in (a Dead Men
    character set is built as a copy of the first kl_anmjoin.STAND_IN entry the .ANM has)."""
    import kl_anmjoin
    name = anim_set.split('#', 1)[-1]
    if name.lower() in hand:
        return hand[name.lower()]
    for s in kl_anmjoin.STAND_IN.get(name, ()):
        if s.lower() in hand:
            return hand[s.lower()]
    return {}


def read_anm(src):
    path = src if os.path.isfile(src) else J.level_zip(src)
    with zipfile.ZipFile(path) as zf:
        return zf.read(next(n for n in zf.namelist() if n.lower().endswith('.anm')))


def carriers(sc):
    """[(node, squad = its top-level subtree's name, primary, secondary, grenade, grenade, animation set)] of
    every ZFFActor; a weapon is the last part of its path ('' = none)."""
    f, out = fields(), []
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZFFActor':
            v = _values(sc, k)
            out.append((k, sc.names[sc.top[k]]) + tuple(v[i].rsplit('\\', 1)[-1] for i in f[:4]) + (v[f[4]].split('#', 1)[-1],))
    return out


def table(sc):
    """{squad: Counter(primary [+ secondary])} in scene order."""
    out = collections.OrderedDict()
    for _k, squad, w, w2, _g1, _g2, _s in carriers(sc):
        out.setdefault(squad, collections.Counter())[(w or '-') + (' + ' + w2 if w2 else '')] += 1
    return out


# ------------------------------------------------------------------ arming
def _rank(seed, path):
    return zlib.crc32(('%s|%s' % (seed, path.lower())).encode('latin1'))


def _shares(mix, d, n):
    """n carriers over the classes of a MIX row at depth d: whole numbers by largest remainder."""
    want = [(c, (a + (b - a) * d) * n) for c, a, b in mix]
    got = {c: int(x) for c, x in want}
    for c, x in sorted(want, key=lambda t: t[1] - int(t[1]), reverse=True)[:n - sum(got.values())]:
        got[c] += 1
    return [(c, got[c]) for c, _a, _b in mix]


def arm(sc, anm, m_name='', nodes=None, seed=SEED, log=print, launchers=False, grenades=False):
    """Give every ZFFActor of a Dead Men map (nodes: the joined nodes that came from it; None = every actor whose
    weapon names a Dead Men template or nothing in the tree) its Dog Days weapons by the rules in the module
    docstring. anm: the .ANM the level's character sets come from (S's: stand-ins are copies of its sets).
    -> report: 'rows' [(squad, actor path, Dead Men primary, Dog Days primary, why)], 'counts' Counter,
    'emptied' Counter of what was taken away, 'other' [(path, field, old, new)] for non-actor holders."""
    import kl_fa
    eq, hand, f = equipment(sc), handling(anm), fields()
    root = next((i['path'].rsplit('\\', 1)[0] + '\\' for i in eq.values()), None)
    rep = {'rows': [], 'counts': collections.Counter(), 'emptied': collections.Counter(), 'other': []}
    if root is None:
        log('  kl_arms: the level has no weapon templates - nothing armed')
        return rep
    lo, hi = LEVEL_DEPTH.get(m_name, DEPTH_DEFAULT)

    def usable(t, folders):
        i = eq.get(t.lower())
        return bool(i) and folders.get(i['folder'], 0) >= FOLDER_MIN

    def pick(cls, folders, r, prefer=None):
        pool = [(t, w * (3 if t == prefer else 1)) for t, w in POOLS.get(cls, ()) if usable(t, folders)]
        if not pool:
            return None
        x = r.uniform(0, sum(w for _t, w in pool))
        for t, w in pool:
            x -= w
            if x <= 0:
                return t
        return pool[-1][0]

    todo = []                                           # (node, squad, Dead Men names of the four fields, set, folders)
    for k, squad, w, w2, g1, g2, aset in carriers(sc):
        v = _values(sc, k)
        own = nodes is not None and k in nodes
        dead = any(v[i] and not sc.resolve(v[i]) for i in f[:4])
        if own or (nodes is None and (dead or any(x.lower() in DM_LOWER and x.lower() not in eq for x in (w, w2, g1, g2)))):
            todo.append((k, squad, (w, w2, g1, g2), folders_of(hand, aset)))
    # zones and depth
    zone = lambda squad: int(ZONE.search(squad).group(1)) if ZONE.search(squad) else None
    zs = sorted({zone(s) for _k, s, _w, _fo in todo if zone(s) is not None})
    def depth(squad):
        z = zone(squad)
        d = 0.5 if z is None or len(zs) < 2 else zs.index(z) / (len(zs) - 1)
        return lo + (hi - lo) * d
    # who of a zone gets which class (stratified: the shares are met exactly per zone and class)
    cls_of = {}
    groups = collections.defaultdict(list)
    for k, squad, ws, fo in todo:
        c = DM_LOWER.get(ws[0].lower())
        if c == 'launcher' and not launchers:
            c = 'smg'                                   # rule 4: the launcher man fights with an SMG
        if squad in FORCE and c in POOLS and any(fo.values()):
            cls_of[k] = FORCE[squad]
        elif c in MIX and any(fo.values()):
            groups[zone(squad), c].append(k)
        else:
            cls_of[k] = c
    for (z, c), ks in sorted(groups.items(), key=lambda t: (t[0][0] is None, t[0])):
        ks.sort(key=lambda k: _rank(seed, sc.path[k]))
        d = depth(sc.names[sc.top[ks[0]]])
        i = 0
        for c2, n in _shares(MIX[c], d, len(ks)):
            for k in ks[i:i + n]:
                cls_of[k] = c2
            i += n
    for k, squad, ws, fo in todo:
        r = random.Random(_rank(seed, sc.path[k]))
        orig = DM_LOWER.get(ws[0].lower())
        new, why = [None] * 4, ''
        # primary
        if not ws[0]:
            new[0] = ''
        elif not any(fo.values()):
            new[0], why = '', 'its animation set has no weapon folder (rule 5)'
            rep['emptied']['primary of an actor whose set cannot hold a weapon'] += 1
        elif orig in (None, 'none', 'grenade'):
            if ws[0].lower() in eq and not SPECIAL.search(ws[0]) and usable(ws[0], fo) and orig is None:
                new[0] = eq[ws[0].lower()]['name']      # a Dog Days weapon already (not from a Dead Men name): kept
            else:
                new[0], why = '', 'no hand weapon in Dog Days for %s' % ws[0]
                rep['emptied']['primary without a class'] += 1
        elif orig == 'launcher' and launchers and usable(ws[0], fo):
            new[0], why = eq[ws[0].lower()]['name'], 'launcher kept (launchers=True; no stock NPC has one)'
        else:
            want = cls_of.get(k) or orig
            for c in (want, orig) + FALLBACK:
                t = pick(c, fo, r, PREFER.get(ws[0]) if c == orig else None)
                if t:
                    new[0] = t
                    why = '' if c == orig and orig != 'launcher' else '%s -> %s%s' % (
                        orig, c, ' (variety, depth %.2f)' % depth(squad) if c == want and orig in MIX else ' (no usable template of its class)')
                    if orig == 'launcher':
                        why = 'launcher -> %s (rule 4)' % c
                    break
            else:
                new[0], why = '', 'no usable template'
                rep['emptied']['primary: nothing usable'] += 1
        # secondary
        c2 = DM_LOWER.get(ws[1].lower())
        if not ws[1] or not new[0]:
            new[1] = ''
            if ws[1]:
                rep['emptied']['secondary of an unarmed actor'] += 1
        elif c2 == 'launcher':
            keep = launchers and usable(ws[1], fo)
            new[1] = eq[ws[1].lower()]['name'] if keep else ''
            rep['emptied']['secondary launcher'] += not keep
        elif c2 in POOLS:
            new[1] = pick(c2, fo, r, PREFER.get(ws[1])) or ''
            if new[1] == new[0]:                        # the same gun twice: one is enough
                new[1] = next((t for t, _w in POOLS[c2] if t != new[0] and usable(t, fo)), '')
        elif c2 is None and ws[1].lower() in eq and not SPECIAL.search(ws[1]) and usable(ws[1], fo):
            new[1] = eq[ws[1].lower()]['name']
        else:
            new[1] = ''
            rep['emptied']['secondary without a class'] += 1
        # grenades
        for j in (2, 3):
            keep = grenades and ws[j].lower() in eq
            new[j] = eq[ws[j].lower()]['name'] if keep else ''
            rep['emptied']['grenade'] += bool(ws[j]) and not keep

        def fn(us, new=new):
            for j, i in enumerate(f[:4]):
                us[i] = [kl_fa._str(sc, root + new[j] if new[j] else '')]
        kl_fa.edit(sc, k, None, fn)
        got = next((c for c, ts in POOLS.items() if any(t == new[0] for t, _w in ts)), None)
        si = next((i for i, (nm, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == 'ZSoldier'), None)
        if SKILL and m_name in SKILL_LEVELS and got in SKILL and si is not None:
            def skill(us, v=SKILL[got]):
                if len(us) != 23 or us[SKILL_FIELD][0][0] not in (0x0c, 0x0e):
                    raise ValueError('%s: ZSoldier is not in the Dog Days layout' % sc.path[k])
                us[SKILL_FIELD] = [(us[SKILL_FIELD][0][0], struct.pack('<I', sc.p.key_index(v)))]
            kl_fa.edit(sc, k, si, skill)
            rep.setdefault('skill', collections.Counter())[SKILL[got]] += 1
        rep['rows'].append((squad, sc.path[k], ws[0], new[0], why))
        rep['counts'][new[0] or '-'] += 1
    # any other holder of a weapon path that names nothing (a placed item, a script): the class's first template
    mine = {k for k, _s, _w, _fo in todo}
    for k in range(1, len(sc.nodes)):
        if k in mine or (nodes is not None and k not in nodes):
            continue
        n = sc.nodes[k]
        for ci in [None] + list(range(len(n['ctrls']))):
            obj = n['props'] if ci is None else n['ctrls'][ci][1]
            hit = [(j, sc.p.key(u[0])) for j, u in enumerate(units(obj[1:-1])) if u[0][0] == 0x0c and len(u) == 1
                   and WEAPONS.lower() in sc.p.key(u[0]).lower() and sc.p.key(u[0]).lower().startswith(root.lower())
                   and not sc.resolve(sc.p.key(u[0]))]
            for j, s in hit:
                tail = s[len(root):].split('\\')
                c = DM_LOWER.get(tail[0].lower())
                t = next((t for t, _w in POOLS.get(c, ()) if t.lower() in eq), None)
                new = '\\'.join([root + t] + tail[1:]) if t else ''
                if new and not sc.resolve(new):
                    new = ''
                def fn(us, j=j, new=new):
                    us[j] = [kl_fa._str(sc, new)]
                kl_fa.edit(sc, k, ci, fn)
                rep['other'].append((sc.path[k], j, s[len(root):], new[len(root):] if new else ''))
    log('  kl_arms: %d actors of %s armed (seed %s, depth %.2f..%.2f, zones %s): %s' % (
        len(rep['rows']), m_name or 'the map', seed, lo, hi, zs or '-',
        ', '.join('%s %d' % x for x in sorted(rep['counts'].items(), key=lambda t: -t[1]))))
    if rep.get('skill'):
        log('  kl_arms: skill by the class handed out (ZSoldier field %d): %s' % (SKILL_FIELD, dict(rep['skill'])))
    was = collections.Counter(w or '-' for _s, _p, w, _n, _y in rep['rows'])
    log('  kl_arms: Dead Men gave them: %s' % ', '.join('%s %d' % x for x in was.most_common()))
    rep['emptied'] = +rep['emptied']                    # without the zero counts
    if rep['emptied']:
        log('  kl_arms: not handed out: %s' % dict(rep['emptied']))
    for p, j, old, new in rep['other']:
        log('  kl_arms: %s field %d: %s -> %s' % (p, j, old, new or '(emptied)'))
    return rep


def transplant(sc, src):
    """The four weapon fields of every ZFFActor of scene `sc` := those of the same node of `src` (two builds of
    one map: the node lists must be equal). -> the number of actors that changed."""
    import kl_fa
    if sc.names != src.names or sc.tids != src.tids:
        raise ValueError('the two levels do not hold the same nodes')
    f, n = fields(), 0
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) != 'ZFFActor':
            continue
        a, b = _values(sc, k), _values(src, k)
        if [a[i] for i in f[:4]] != [b[i] for i in f[:4]]:
            def fn(us, b=b):
                for i in f[:4]:
                    us[i] = [kl_fa._str(sc, b[i])]
            kl_fa.edit(sc, k, None, fn)
            n += 1
    return n


def patch(build, armed, dst, log=print):
    """See the command line. -> the archive written."""
    import shutil
    import kl_fa, kl_graft
    zp = build if build.lower().endswith('.zip') else next(os.path.join(build, x) for x in sorted(os.listdir(build)) if x.lower().endswith('_main.zip'))
    if os.path.abspath(dst) == os.path.abspath(os.path.dirname(zp)):
        raise ValueError('the output folder is the build\'s own')
    order, files, ext, sc, _live, _hud = kl_graft.open_built(zp)
    data, bad, _paths, _names = J.check(sc, log=lambda *_a: None)
    if data != files[ext['.prp']] or bad:
        raise ValueError('the build\'s .prp does not re-serialise byte for byte (%d misfits): not patched' % len(bad))
    n = transplant(sc, kl_fa.load(armed)[0])
    d = kl_fa.define_master(sc, log)
    data, bad, _paths, _names = J.check(sc, log=lambda *_a: None)
    if bad:
        raise ValueError('%d objects do not fit after the patch' % len(bad))
    files[ext['.prp']] = data
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(m, files[m]) for m in order])
    for x in os.listdir(os.path.dirname(zp)):
        q = os.path.join(os.path.dirname(zp), x)
        if os.path.isfile(q) and q != zp:
            shutil.copyfile(q, os.path.join(dst, x))
    log('patched %s: %d actors re-armed, %d define(s) renamed; only the .prp member differs from %s' % (out, n, d, zp))
    return out


# ------------------------------------------------------------------ the check
def check(sc, anm=None):
    """[(severity 1 = BROKEN / 2 = DEGRADED, code, text)] about what the level's NPCs carry. Stock: none in 21 levels.
      BROKEN   an NPC carries a SPECIAL template (the played Retomoto build: 58 human-shield pistols, a helicopter
               gun), or one whose /Weapon_Handling folder its animation set lacks (anm given) - what the engine
               does with either was not read; no stock level has one
      DEGRADED an NPC carries a template no stock level gives an NPC; a weapon path that names nothing"""
    eq, f = equipment(sc), fields()
    hand = handling(anm) if anm is not None else None
    special, nofolder, unproven, dead = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
    where = {}
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) != 'ZFFActor':
            continue
        v = _values(sc, k)
        fo = folders_of(hand, v[f[4]]) if hand is not None else None
        for i in f[:2]:
            if not v[i]:
                continue
            t = v[i].rsplit('\\', 1)[-1]
            where.setdefault(t, sc.path[k])
            if not sc.resolve(v[i]) or t.lower() not in eq:
                dead[t] += 1
            elif SPECIAL.search(t) and STOCK_NPC.get(eq[t.lower()]['name'], (0, 0, 0))[:2] == (0, 0):
                special[t] += 1
            elif fo is not None and fo.get(eq[t.lower()]['folder'], 0) < FOLDER_MIN:
                nofolder[t, v[f[4]].split('#', 1)[-1]] += 1
            elif eq[t.lower()]['name'] not in STOCK_NPC:
                unproven[t] += 1
    out = []
    if special:
        out.append((1, 'npc-weapon', '%d NPCs carry a special weapon template no stock level gives an NPC: %s; e.g. %s' % (
            sum(special.values()), ', '.join('%s %d' % x for x in special.most_common()), where[special.most_common(1)[0][0]])))
    if nofolder:
        out.append((1, 'npc-weapon-anim', '%d NPCs carry a weapon their animation set has no /Weapon_Handling folder for: %s' % (
            sum(nofolder.values()), ', '.join('%s on %s %d' % (t, s, n) for (t, s), n in nofolder.most_common(6)))))
    if dead:
        out.append((2, 'npc-weapon', '%d NPC weapon paths name no template: %s' % (sum(dead.values()), ', '.join('%s %d' % x for x in dead.most_common(6)))))
    if unproven:
        out.append((2, 'npc-weapon', '%d NPCs carry a template no stock level gives an NPC: %s' % (
            sum(unproven.values()), ', '.join('%s %d' % x for x in unproven.most_common(6)))))
    return out


# ------------------------------------------------------------------ command line
def _scene(src):
    import kl_fa
    return kl_fa.load(src)[0] if os.path.isfile(src) or not src.startswith('M') else J.Scene.load(src)


def census(levels):
    """STOCK_NPC recounted: {template: (FA primary, story primary, secondary)}."""
    f, out = fields(), collections.defaultdict(lambda: [0, 0, 0])
    for L in levels:
        sc = J.Scene.load(L, 'dd')
        for k in range(1, len(sc.nodes)):
            if sc.cls(k) == 'ZFFActor':
                v = _values(sc, k)
                if v[f[0]]:
                    out[v[f[0]].rsplit('\\', 1)[-1]][0 if L.startswith('F') else 1] += 1
                if v[f[1]]:
                    out[v[f[1]].rsplit('\\', 1)[-1]][2] += 1
    return {k: tuple(v) for k, v in out.items()}


def main():
    a = sys.argv[1:]
    if a[:1] == ['templates']:
        src = a[1] if len(a) > 1 else 'F07'
        sc = _scene(src)
        eq, hand = equipment(sc), handling(read_anm(src))
        swat = hand.get('swat_02', {})
        pooled = {t: c for c, p in POOLS.items() for t, _w in p}
        print('%s: %d weapon templates. Columns: class, hands, slots of its folder in Swat_02, NPCs in stock FA / story / as secondary, verdict' % (src, len(eq)))
        for i in sorted(eq.values(), key=lambda i: (i['wt'], i['name'])):
            n = STOCK_NPC.get(i['name'], (0, 0, 0))
            verdict = ('pool ' + pooled[i['name']]) if i['name'] in pooled else 'never: special variant' if SPECIAL.search(i['name']) \
                else 'not used: stock NPCs never carry it' if not any(n) else 'stock NPC weapon, in no pool'
            print('  %-30s %-18s %-12s %-34s %3d   %3d %3d %3d   %s' % (i['name'], i['wt'], i['hands'], i['folder'], swat.get(i['folder'], 0), *n, verdict))
    elif len(a) == 2 and a[0] == 'table':
        sc = _scene(a[1])
        for squad, c in table(sc).items():
            print('  %-78s %s' % (squad[:78], ', '.join('%s %d' % x for x in c.most_common())))
        tot = collections.Counter()
        for c in table(sc).values():
            tot.update(c)
        print('  total: ' + ', '.join('%s %d' % x for x in tot.most_common()))
    elif len(a) == 3 and a[0] == 'compare':
        A, B = table(_scene(a[1])), table(_scene(a[2]))
        fmt = lambda c: ', '.join('%s %d' % x for x in sorted(c.items())) if c else '(not in the level)'
        for squad in list(A) + [s for s in B if s not in A]:
            x, y = A.get(squad), B.get(squad)
            print('  %s\n      before: %s\n      after:  %s' % (squad, fmt(x), fmt(y)) if x != y else '  %s\n      same:   %s' % (squad, fmt(x)))
        for name, T in (('before', A), ('after', B)):
            tot = collections.Counter()
            for c in T.values():
                tot.update(c)
            print('  total %s: %s' % (name, ', '.join('%s %d' % x for x in tot.most_common())))
    elif len(a) == 2 and a[0] == 'check':
        fs = check(_scene(a[1]), read_anm(a[1]))
        for sev, code, text in fs:
            print('  %-8s %-16s %s' % (('', 'BROKEN', 'DEGRADED')[sev], code, text))
        print('%s: %d findings' % (a[1], len(fs)))
        sys.exit(1 if any(s == 1 for s, _c, _t in fs) else 0)
    elif len(a) == 4 and a[0] == 'patch':
        patch(a[1], a[2], a[3])
    elif a == ['stock']:
        levels = ['F%02d' % i for i in range(1, 10)] + ['L%02d' % i for i in range(12)]
        bad = 0
        for L in levels:
            fs = check(J.Scene.load(L, 'dd'), read_anm(L))
            bad += len(fs)
            print('%s: %d findings%s' % (L, len(fs), ''.join('\n   ' + t for _s, _c, t in fs)))
        c = census(levels)
        print('census equals STOCK_NPC: %s' % (c == STOCK_NPC))
        for t in sorted(set(c) | set(STOCK_NPC)):
            if c.get(t) != STOCK_NPC.get(t):
                print('   %s: counted %s, table %s' % (t, c.get(t), STOCK_NPC.get(t)))
        print('stock levels: %d findings (must be 0)' % bad)
        sys.exit(1 if bad or c != STOCK_NPC else 0)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
