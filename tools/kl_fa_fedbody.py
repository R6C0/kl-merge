#!/usr/bin/env python3
r"""
The body and the rifle of the PLAYER who comes back as a fed, per map: one section [FedBody] in the level's
KLJoin.ini (the file klhook\kljoin.c reads beside the archive), read by klhook\klfedkit.c. Owner, 2026-10-11:
'make sure to use a model thats correct for the map so i was normal swat but i should be the yakuza biker outfit
and then on withdrawal normal swat etc. and make it so u have a chance to come back with an ak 47 instead of only
just having the mp5'. Research and the live checks: re\fed_kit.md.
OFFLINE: nothing here installs anything; the archive of a build is only READ. NOTHING OF THIS HAS RUN IN THE GAME.

    python kl_fa_fedbody.py survey <build folder>            the police player's own body and every Enemy model of
                                                             the build: actors, variants, set, bones, what a
                                                             player body would miss
    python kl_fa_fedbody.py plan <build folder> [options]    the choice, its checks and the section, printed
    python kl_fa_fedbody.py apply <build folder> <out folder> [options] [--link]
                                                             <out>\KLJoin.ini = the build's own KLJoin.ini (if it
                                                             has one) with the section [FedBody] added or replaced,
                                                             fedbody.txt / fedbody.json. --link: every OTHER file of
                                                             the build folder is hard-linked into <out> (no disk
                                                             space; the two folders then share those files - never
                                                             edit one in place), so <out> is a whole build folder
                                                             for kl_expansion / debug\slot.py
    python kl_fa_fedbody.py check <folder>                   the folder's [FedBody] against the folder's own archive;
                                                             exit 1 on a FAIL
    python kl_fa_fedbody.py sheet <build folder> <out.png> [options]
                                                             picture: the stock police player, then the chosen body
                                                             in each variant, front and back (kl_view)
    python kl_fa_fedbody.py all <work folder> [--link]       the five builds of the owner's tab (TAB below) ->
                                                             <work>\build\z_fedbody\<name>
    options
      --body auto|stock|<text>   auto (default) = AUTO below; stock = keep the police player's own model (Root=0);
                                 <text> = the first Enemy actor whose scene path contains it (no case)
      --root N                   a model root by number (then --variants is needed)
      --variants a,b,c           the looks to draw from (default: the variants the map's own actors on that model
                                 wear - each is a look this level already draws)
      --ak auto|0|<item>         the rifle of [Fed] AkChance: auto (default) = the AK-47 (item 31) unless the
                                 build's KLGuns.ini shows another gun's look on it, then the AK-74 (32); 0 = no line

WHAT THE SECTION SAYS (klfedkit.c section 3 / 4)
    [FedBody]
    Entries=47114        the chunk count of the .prm in the archive beside the file (dword +4 of the file): the hook
                         takes the section for that .prm only (as klgun.c does with KLGuns.ini)
    Root=36028           the model root the fed wears; 0 = the police player's own (nothing is swapped)
    Variants=1,3,4       the looks; one is drawn per respawn
    Stock=1919           the model the police player objects have in this build (for the log)
    Name=...             words for the log
    AkItem=32            the rifle item of [Fed] AkChance on THIS build; AkRecord= its row of the shop table

WHICH BODY (AUTO; the owner's rule: the fed wears what the map's own law / enemy wears)
  A Walk in the Park   the bikers of the Japanese drug squads (`..JPN_DrugGuy..` / `..JPN_Guards..`, materials
                       Biker_Red / Biker_BlackWhite / Biker_Yellow + Biker_Visor): the owner asked for exactly this
  Retomoto Tower       the Japanese SWAT of the street (`SWAT_Beam..`): a fed is police, and the tower's own men are
                       the yakuza's suits. (The Japanese street police `JPN_Police_01` is `--body jpn_police`,
                       the tower guards `--body c_henchmen`.)
  Hot Coffee           its FBI agents (`FBI-Agents_0n`) - Dead Men's own respawn body was an FBI agent
  Withdrawal, Late Night Opening
                       stock = the SWAT body the game gives (owner: 'on withdrawal normal swat'). The maps' own Dead
                       Men SWAT (`Reinforcement_0n`, `PoliceSwats_0n`) is `--body reinforcement` / `--body policeswats`.
  A map the table does not know: stock.

WHAT IS CHECKED (a FAIL writes no section)
  - the root is a person's model with a skeleton (kl_chars.skeleton), its bone tables are bound to this level's
    .ANM (kl_chars.check_bones: the map's models were rebound by kl_graft) and it has every bone id game code asks
    a person for by number (re\characters_graft.md 3.2: pelvis, spine, neck, head, limbs, both hand attachers,
    spine / hip / head attacher). free_bone01 (id 0x21) is in no Dead Men model: NOTE, not FAIL - its three readers
    go on with unset vectors in a two-person action (re\characters_graft.md 3.4); `kl_chars.alias_free_bone` would
    be the repair as a build step (not done here: this tool does not write a .prm).
  - every variant has objects at the first level of detail.
  - the rifle: a weapon template bound to the item, and its handling folder in the police player's animation set;
    never the fed's own pistol (item 6) or stock rifle (item 29): the hook refuses them (the loadout would give one
    item twice). A template is also what makes the game's weapon pool hold objects of the item (kl2 0x78a8d0: 8 of
    every shop item that has one).
  - Root is below Entries (the hook refuses the section otherwise).
RULES OF USE
  - Entries= is a chunk COUNT, not an identity: run `apply` LAST, on the FINAL build of a map (after every step that
    can change the .prm; the other sections of KLJoin.ini are kept), and `check` the result.
  - A folder made with --link SHARES every other file with its source build (hard links). Make the tree from it;
    never run a step that rewrites a file in place inside it - it would change the source build silently. `check`
    says how many files of a folder are shared.
ASSUMPTIONS, said plainly: that a ZFFPlayer of type MULTIPLAYER_POLICEMAN draws and animates an NPC model given
through the game's own 0x783fb0 as the heister objects do with Dead Men heroes (klchar.c, seen live) and the AI
heisters with the heroes' models (klcrew.c, seen live); that the 27 face bones the bikers lack (a helmet) are only
ever asked for through the animation tables.
"""
import collections, json, os, shutil, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SECTION = 'FedBody'
# (text in an Enemy actor's scene path, lower case; words for the log)
AUTO = [('jpn_drugguy', 'the park\'s yakuza bikers'),
        ('swat_beam', 'Retomoto\'s Japanese SWAT'),
        ('fbi-agents', 'Hot Coffee\'s FBI agents')]
# bone ids game code asks a person for by number (re\characters_graft.md 3.2), without 0x21 = free_bone01
IDS = (1, 2, 3, 4, 6, 7, 9, 0x0a, 0x0c, 0x0d, 0x0e, 0x10, 0x11, 0x12, 0x13, 0x14, 0x16, 0x17, 0x18, 0x19, 0x1f, 0x20, 0x22, 0x23, 0x24)
FREE_ID = 0x21
AK47, AK74 = 31, 32
ITEM = {AK47: 'eFF2ItemRifle_AK47', AK74: 'eFF2ItemRifle_AK74'}
# the shop table of kl2.exe (0xbd1f68, 36 rows of 24 bytes {item, ammunition, price, rank, tier, DLC}): row of an item.
# Read from the exe 2026-10-11; the hook looks the row up itself and takes AkRecord only as a cross-check.
RECORD = {AK47: 29, AK74: 30}
# the two guns the respawn itself gives (shop rows 0 and 0x1c): klfedkit.c refuses them as AkItem
FED_OWN = {6: 'the fed\'s own pistol (HG_M-77B)', 29: 'the fed\'s own stock rifle (Rifle_Zastavam85)'}
TAB = [('M01', 'z_route3/M01', 'Hot Coffee'), ('M02', 'z_loot3/M02', 'Late Night Opening'), ('M03', 'z_cover3/M03', 'Withdrawal'),
       ('M06', 'z_route/M06', 'A Walk in the Park'), ('retomoto_full', 'z_rooms/retomoto_full', 'Retomoto Tower')]


class Level:
    """A build folder, read once: scene, .prm, .ANM."""

    def __init__(self, src):
        import kl_fa_bots as KB, kl_prmgraph as G, kl_anm
        self.B = KB.Built(src)
        self.folder = self.B.folder
        self.prm = G.read(self.B['.prm'], 'dd')
        self.entries = struct.unpack_from('<I', self.B['.prm'], 4)[0]
        self.anm = kl_anm.Anm(self.B['.ANM'], 'dd')

    def police(self):
        """-> (model, animation set, [scene paths]) of the police player objects."""
        import kl_fa
        B, sc = self.B, self.B.sc
        cops = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFPlayer' and
                'eZFFP_TYPE_MULTIPLAYER_POLICEMAN' in [x for x in kl_fa.node_values(sc, k) if isinstance(x, str)]]
        if not cops:
            raise ValueError('no police player object (ZFFPlayer of type MULTIPLAYER_POLICEMAN)')
        models = sorted({B.ents[k - 1].model for k in cops})
        if len(models) != 1:
            raise ValueError('the police player objects have %d models (%r): one is expected' % (len(models), models))
        return models[0], str(B.values(cops[0])['ZLNKOBJ[2]']).split('#')[-1], [sc.path[k] for k in cops]

    def enemies(self):
        """{model: {'actors': [(path, variant, set)], 'variants': Counter}} of the Enemy actors with a soldier."""
        B, sc, out = self.B, self.B.sc, collections.OrderedDict()
        for k in range(1, len(sc.nodes)):
            if sc.cls(k) != 'ZFFActor':
                continue
            v = B.values(k)
            if v.get('ZFFActor[0]') != 'Enemy' or not any(sc.p.key(nm) == 'ZSoldier' for nm, _b in sc.nodes[k]['ctrls']):
                continue
            m = B.ents[k - 1].model
            e = out.setdefault(m, {'actors': [], 'variants': collections.Counter()})
            e['actors'].append((sc.path[k][5:], v.get('ZLNKOBJ[0]'), str(v.get('ZLNKOBJ[2]')).split('#')[-1]))
            e['variants'][v.get('ZLNKOBJ[0]')] += 1
        return out

    def model(self, root):
        """Facts of a model root -> dict, or raises ValueError."""
        import kl_chars as C
        p = self.prm
        if not 0 < root < len(p.chunks):
            raise ValueError('root %d is not a chunk of the .prm (%d chunks)' % (root, len(p.chunks)))
        sk = C.skeleton(p, root)
        if not sk:
            raise ValueError('chunk %d is not a model root with a skeleton' % root)
        h = struct.unpack('<20I', p.chunks[sk])
        names, t5 = C.bone_names(p, sk), p.chunks[h[5]]
        objs = C.objects(p, root)
        var = collections.OrderedDict()
        for o in objs:
            c = p.chunks[o]
            var.setdefault(c[0x0f], collections.Counter())[c[0x0e]] += 1
        return {'root': root, 'skeleton': sk, 'bones': len(names), 'names': names, 'no_id': [i for i in IDS if t5[i] == 0xff],
                'free': t5[FREE_ID] != 0xff, 'objects': len(objs), 'variants': var,
                'bound': C.check_bones(p, self.anm.bones, roots=[root])}

    def materials(self, root, variant):
        import kl_chars as C, kl_texmat as T
        if not hasattr(self, 'mat'):
            self.mat = T.read_mat(self.B['.MAT'])
        p = self.prm
        return sorted({self.mat.insts[p.u16(o, 0x12)].name.split('/')[-1] for o in C.objects(p, root) if p.chunks[o][0x0f] == variant})

    def guns(self):
        """-> {item number: (template name, handling folder)} of the level's weapon templates."""
        import kl_arms
        with open(os.path.join(HERE, 'dd_enums.json')) as f:
            num = {n: v for e in json.load(f) for v, n in e if isinstance(n, str) and n.startswith('eFF2Item')}
        return {num[e['item']]: (e['name'], e['folder']) for e in kl_arms.equipment(self.B.sc).values() if e['item'] in num}

    def handling(self, aset):
        import kl_arms
        return kl_arms.handling(self.anm).get(aset.lower(), {})

    def looks(self):
        """{item: the label of the look the build's KLGuns.ini shows on it} (only guns that show a look)."""
        f, out = os.path.join(self.folder, 'KLGuns.ini'), {}
        if not os.path.isfile(f):
            return out
        sec = {}
        for line in open(f, encoding='latin1'):
            line = line.strip()
            if line.startswith('['):
                sec = {}
                out[line] = sec
            elif '=' in line and not line.startswith(';'):
                k, v = line.split('=', 1)
                sec[k.strip()] = v.strip()
        res = {}
        for s in out.values():
            try:
                shown = int(s.get('Shown', '0'))
                if 'Item' in s and shown:
                    res[int(s['Item'])] = s.get('Look%d' % shown, '?')
            except ValueError:
                pass
        return res


def plan(L, opt=None, log=print):
    """-> (findings [(kind, text)], section values OrderedDict or None)."""
    opt = dict({'body': 'auto', 'root': None, 'variants': None, 'ak': 'auto'}, **(opt or {}))
    out, sec = [], collections.OrderedDict()
    stock, aset, cops = L.police()
    en = L.enemies()
    log('police player objects: %d on model %d, animation set %s' % (len(cops), stock, aset))
    root, label, variants = 0, 'the police player\'s own body (stock)', []
    if opt['root'] is not None:
        root, label = int(opt['root']), 'model %d (given)' % int(opt['root'])
        if not opt['variants'] and root in en:
            variants = sorted(en[root]['variants'])
    elif opt['body'] != 'stock':
        needles = AUTO if opt['body'] == 'auto' else [(opt['body'].lower(), 'asked: %s' % opt['body'])]
        for needle, words in needles:
            hit = [(m, a) for m, e in en.items() for a in e['actors'] if needle in a[0].lower()]
            if hit:
                root = hit[0][0]
                label = '%s (%s)' % (words, hit[0][1][0].split('\\')[-2] if '\\' in hit[0][1][0] else hit[0][1][0])
                variants = sorted(en[root]['variants'])
                break
        else:
            if opt['body'] != 'auto':
                out.append(('FAIL', 'no Enemy actor\'s path contains %r' % opt['body']))
                return out, None
    if opt['variants']:
        variants = [int(x) for x in str(opt['variants']).replace(';', ',').split(',') if x.strip()]
    if root == stock:
        root, label = 0, 'the police player\'s own body (the choice is the model it already has)'
    sec['Entries'] = L.entries
    sec['Root'] = root
    if root:
        try:
            m = L.model(root)
        except ValueError as e:
            out.append(('FAIL', str(e)))
            return out, None
        if not variants:
            out.append(('FAIL', 'model %d: no variant is given and no actor of the map wears it (--variants)' % root))
            return out, None
        variants = variants[:8]
        log('body: model %d = %s; %d bones, %d objects, variants in the model %s; the map\'s actors wear %s' % (
            root, label, m['bones'], m['objects'], sorted(m['variants']), dict(en[root]['variants']) if root in en else {}))
        for v in variants:
            lod = m['variants'].get(v)
            if not lod or not lod.get(1):
                out.append(('FAIL', 'model %d has no object of variant %d at the first level of detail' % (root, v)))
            else:
                log('  variant %d: %s' % (v, ', '.join(L.materials(root, v)[:8])))
        if m['no_id']:
            out.append(('FAIL', 'model %d lacks bone ids %s that game code asks a person for by number' % (root, ['0x%x' % i for i in m['no_id']])))
        for b in m['bound']:
            out.append(('FAIL', 'model %d: %s' % (root, b)))
        if not m['free']:
            out.append(('NOTE', 'model %d has no free_bone01 (id 0x21), as every Dead Men person: a two-person action of the fed reads unset vectors (re/characters_graft.md 3.4)' % root))
        sm = L.model(stock)
        miss = [b for b in sm['names'] if b not in m['names']]
        face = [b for b in miss if b.startswith('fa_')]
        rest = [b for b in miss if not b.startswith('fa_') and b != 'free_bone01']
        if face or rest:
            out.append(('NOTE', 'model %d lacks %d face bone(s)%s the stock police body has%s' % (
                root, len(face), ' and %s' % rest if rest else '', ': a helmet / mask, no face to move' if len(face) > 20 else '')))
        if root in en:
            sets = sorted({a[2] for a in en[root]['actors']})
            out.append(('NOTE', 'the map\'s actors move this model with set %s; the police player\'s set is %s (ASSUMPTION: as the heroes\' sets move Dead Men heroes)' % ('/'.join(sets), aset)))
        sec['Variants'] = ','.join(str(v) for v in variants)
    else:
        log('body: %s - model %d stays' % (label, stock))
    sec['Stock'] = stock
    sec['Name'] = label
    # ---- the rifle
    ak = opt['ak']
    if str(ak) != '0':
        guns, hand, looks = L.guns(), L.handling(aset), L.looks()
        if ak == 'auto':
            item = AK47
            if AK47 in looks:
                item = AK74
                out.append(('NOTE', 'the build\'s KLGuns.ini shows the look %r on the AK-47 (item 31): the rifle of AkChance is the AK-74 (item 32), which looks like an AK here%s' % (
                    looks[AK47], ' - and it too shows a look: %r' % looks[AK74] if AK74 in looks else '')))
        else:
            item = int(ak)
        if item in FED_OWN:
            out.append(('FAIL', 'item %d is %s: the hook refuses it as AkItem (the loadout would give one item twice)' % (item, FED_OWN[item])))
        elif item not in guns:
            out.append(('FAIL', 'no weapon template of the level is bound to item %d' % item))
        elif guns[item][1] not in hand:
            out.append(('FAIL', 'the police player\'s set %s has no /Weapon_Handling/%s clips (item %d, template %s)' % (aset, guns[item][1], item, guns[item][0])))
        else:
            log('rifle of AkChance: item %d = template %s, %d handling clips in set %s' % (item, guns[item][0], hand[guns[item][1]], aset))
            sec['AkItem'] = item
            if item in RECORD:
                sec['AkRecord'] = RECORD[item]
    for kind, text in out:
        log('%s: %s' % (kind, text))
    if any(k == 'FAIL' for k, _t in out):
        return out, None
    return out, sec


def section_text(sec):
    L = ['[%s]' % SECTION,
         '; written by tools\\kl_fa_fedbody.py for klhook\\klfedkit.c: the body and the AkChance rifle of the player who comes back as a fed.',
         '; Entries = the chunk count of the .prm in the archive beside this file: the hook takes the section for that .prm only.']
    L += ['%s=%s' % kv for kv in sec.items()]
    return '\r\n'.join(L) + '\r\n'


def merge_ini(old, text):
    """old KLJoin.ini text (or '') with its [FedBody] section replaced by `text` / the section appended."""
    keep, skip = [], False
    for line in old.splitlines():
        s = line.strip()
        if s.startswith('['):
            skip = s.lower() == '[%s]' % SECTION.lower()
        if not skip:
            keep.append(line)
    while keep and not keep[-1].strip():
        keep.pop()
    return ('\r\n'.join(keep) + '\r\n\r\n' if keep else '') + text


def read_section(path):
    sec, on = collections.OrderedDict(), False
    if not os.path.isfile(path):
        return None
    for line in open(path, encoding='latin1'):
        s = line.strip()
        if s.startswith('['):
            on = s.lower() == '[%s]' % SECTION.lower()
        elif on and '=' in s and not s.startswith(';'):
            k, v = s.split('=', 1)
            sec[k.strip()] = v.strip()
    return sec if on or sec else None


def apply(src, dst, opt=None, link=False, log=print):
    lines = []
    def say(s=''):
        lines.append(str(s)); log(s)
    src, dst = os.path.abspath(src), os.path.abspath(dst)
    if os.path.exists(dst):
        raise ValueError('%s exists: this tool never writes into an existing folder' % dst)
    say('kl_fa_fedbody apply %s -> %s' % (src, dst))
    L = Level(src)
    out, sec = plan(L, opt, say)
    if sec is None:
        say('RESULT: FAIL - nothing written')
        return out, None
    os.makedirs(dst)
    jp = os.path.join(L.folder, 'KLJoin.ini')
    old = open(jp, encoding='latin1').read() if os.path.isfile(jp) else ''
    with open(os.path.join(dst, 'KLJoin.ini'), 'w', encoding='latin1', newline='') as f:
        f.write(merge_ini(old, section_text(sec)))
    say('%s: %s + [%s] (%s)' % (os.path.join(dst, 'KLJoin.ini'), 'the build\'s own KLJoin.ini' if old else 'the build had no KLJoin.ini: a new file', SECTION,
                               ', '.join('%s=%s' % kv for kv in sec.items() if kv[0] != 'Name')))
    n = 0
    if link:
        for f in sorted(os.listdir(L.folder)):
            a = os.path.join(L.folder, f)
            if os.path.isfile(a) and f.lower() not in ('kljoin.ini', 'fedbody.txt', 'fedbody.json'):
                os.link(a, os.path.join(dst, f)); n += 1
        say('%d other file(s) of the build hard-linked into %s: a whole build folder. The files are SHARED with %s: make the tree from it, never run a step that rewrites a file in place inside it' % (n, dst, L.folder))
    else:
        say('only KLJoin.ini is in %s: put it beside the archive when the build is made into a tree (or run again with --link)' % dst)
    say('RESULT: PASS (%d NOTE)' % sum(k == 'NOTE' for k, _t in out))
    with open(os.path.join(dst, 'fedbody.json'), 'w') as f:
        json.dump({'source': src, 'section': sec, 'findings': [list(x) for x in out], 'linked': n}, f, indent=1)
    with open(os.path.join(dst, 'fedbody.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return out, sec


def check(folder, log=print):
    """The folder's [FedBody] against its own archive -> findings."""
    out = []
    sec = read_section(os.path.join(folder, 'KLJoin.ini'))
    if sec is None:
        return [('FAIL', 'no [%s] section in %s' % (SECTION, os.path.join(folder, 'KLJoin.ini')))]
    arch = [f for f in os.listdir(folder) if f.lower().endswith('_main.zip')]
    if len(arch) != 1:
        return [('FAIL', '%s has %d level archives: the section can only be checked beside its archive (apply --link)' % (folder, len(arch)))]
    L = Level(os.path.join(folder, arch[0]))
    def num(k, d=0):
        try:
            return int(sec.get(k, d))
        except ValueError:
            return -1
    if num('Entries') != L.entries:
        out.append(('FAIL', 'Entries=%s, the .prm beside it has %d chunks: the hook leaves the section alone' % (sec.get('Entries'), L.entries)))
    stock, aset, _c = L.police()
    if num('Stock', stock) != stock:
        out.append(('FAIL', 'Stock=%s, the police player objects have model %d' % (sec.get('Stock'), stock)))
    shared = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and os.stat(os.path.join(folder, f)).st_nlink > 1]
    if shared:
        out.append(('NOTE', '%d file(s) of this folder are hard links shared with another folder (%s ..): never rewrite one in place here' % (len(shared), sorted(shared)[0])))
    root = num('Root')
    if root < 0:
        out.append(('FAIL', 'Root=%s is not a number' % sec.get('Root')))
    elif root >= L.entries:
        out.append(('FAIL', 'Root=%d is not below the .prm\'s %d chunks: the hook refuses the section' % (root, L.entries)))
    elif root:
        try:
            m = L.model(root)
            vs = [int(x) for x in sec.get('Variants', '').split(',') if x.strip()]
            if not vs:
                out.append(('FAIL', 'Root=%d without Variants=' % root))
            for v in vs:
                if not m['variants'].get(v, {}).get(1):
                    out.append(('FAIL', 'model %d has no object of variant %d at the first level of detail' % (root, v)))
            if m['no_id']:
                out.append(('FAIL', 'model %d lacks bone ids %s' % (root, ['0x%x' % i for i in m['no_id']])))
            out += [('FAIL', 'model %d: %s' % (root, b)) for b in m['bound']]
            if not m['free']:
                out.append(('NOTE', 'model %d has no free_bone01' % root))
        except ValueError as e:
            out.append(('FAIL', str(e)))
    item = num('AkItem')
    if item:
        guns, hand = L.guns(), L.handling(aset)
        if item in FED_OWN:
            out.append(('FAIL', 'AkItem=%d is %s: the hook refuses it' % (item, FED_OWN[item])))
        elif item not in guns:
            out.append(('FAIL', 'AkItem=%d: no weapon template of the level is bound to it' % item))
        elif guns[item][1] not in hand:
            out.append(('FAIL', 'AkItem=%d: set %s has no handling clips for %s' % (item, aset, guns[item][1])))
        if item in RECORD and num('AkRecord', RECORD[item]) != RECORD[item]:
            out.append(('FAIL', 'AkRecord=%s, item %d is row %d of the shop table' % (sec.get('AkRecord'), item, RECORD[item])))
    for kind, text in out:
        log('%s: %s' % (kind, text))
    log('check %s: %s (%d FAIL, %d NOTE); section: %s' % (folder, 'FAIL' if any(k == 'FAIL' for k, _t in out) else 'PASS', sum(k == 'FAIL' for k, _t in out),
                                                         sum(k == 'NOTE' for k, _t in out), ', '.join('%s=%s' % kv for kv in sec.items() if kv[0] != 'Name')))
    return out


def survey(src, log=print):
    L = Level(src)
    stock, aset, cops = L.police()
    sm = L.model(stock)
    log('%s: .prm %d chunks' % (L.B.zp, L.entries))
    log('police player: %d objects (%s ..), model %d, set %s, %d bones, variants %s: %s' % (
        len(cops), cops[0][5:], stock, aset, sm['bones'], sorted(sm['variants']), ', '.join(L.materials(stock, 1)[:6])))
    for m, e in sorted(L.enemies().items(), key=lambda x: -len(x[1]['actors'])):
        try:
            f = L.model(m)
        except ValueError as err:
            log('  model %-6d %3d actor(s): %s' % (m, len(e['actors']), err)); continue
        miss = [b for b in sm['names'] if b not in f['names']]
        log('  model %-6d %3d actor(s), variants worn %s of %s, set %s, %d bones (lacks %d face, %s), ids missing %s%s  e.g. %s' % (
            m, len(e['actors']), dict(sorted(e['variants'].items())), sorted(f['variants']), '/'.join(sorted({a[2] for a in e['actors']})), f['bones'],
            sum(b.startswith('fa_') for b in miss), [b for b in miss if not b.startswith('fa_')], ['0x%x' % i for i in f['no_id']],
            '' if not f['bound'] else ' NOT BOUND to this .ANM', e['actors'][0][0]))
        v0 = sorted(e['variants'])[0]
        log('       variant %s: %s' % (v0, ', '.join(L.materials(m, v0)[:8])))
    guns, hand, looks = L.guns(), L.handling(aset), L.looks()
    for item in (6, 29, AK47, AK74):
        log('  item %2d: template %s, handling clips in %s: %s%s' % (item, guns.get(item, ('NONE', ''))[0], aset, hand.get(guns.get(item, ('', ''))[1], 0),
                                                                    ', KLGuns.ini shows %r on it' % looks[item] if item in looks else ''))


def sheet(src, out_png, opt=None, log=print):
    import kl_view as V, kl_texmat as T
    L = Level(src)
    _o, sec = plan(L, opt, lambda s='': None)
    stock = L.police()[0]
    looks = [(stock, 1)]
    if sec and int(sec['Root']):
        looks += [(int(sec['Root']), int(v)) for v in sec['Variants'].split(',')]
    mat = T.read_mat(L.B['.MAT'])
    tx = V.Textures(mat, T.read_tex(L.B['.TEX']))
    panels = [(axis, V.BODY, V.posed(L.prm, mat, r, v, V.REST, textures=tx)) for axis in ('front', 'back') for r, v in looks]
    V.sheet(out_png, panels, 150, 140, cols=len(looks))
    log('%s: the stock police player (model %d), then %s' % (out_png, stock, ', '.join('model %d variant %d' % x for x in looks[1:]) or 'nothing: the body stays stock'))


def options(a):
    opt = {}
    for name, key in (('--body', 'body'), ('--root', 'root'), ('--variants', 'variants'), ('--ak', 'ak')):
        if name in a:
            i = a.index(name); opt[key] = a[i + 1]; del a[i:i + 2]
    return opt


def main():
    a = sys.argv[1:]
    link = '--link' in a
    a = [x for x in a if x != '--link']
    opt = options(a)
    if len(a) == 2 and a[0] == 'survey':
        survey(a[1]); return 0
    if len(a) == 2 and a[0] == 'plan':
        out, sec = plan(Level(a[1]), opt)
        if sec is None:
            print('RESULT: FAIL'); return 1
        print(section_text(sec).replace('\r\n', '\n'))
        print('RESULT: PASS (%d NOTE)' % sum(k == 'NOTE' for k, _t in out)); return 0
    if len(a) == 3 and a[0] == 'apply':
        out, sec = apply(a[1], a[2], opt, link)
        return 0 if sec is not None else 1
    if len(a) == 2 and a[0] == 'check':
        return 1 if any(k == 'FAIL' for k, _t in check(a[1])) else 0
    if len(a) == 3 and a[0] == 'sheet':
        sheet(a[1], a[2], opt); return 0
    if len(a) == 2 and a[0] == 'all':
        bad = 0
        for name, rel, title in TAB:
            print('===== %s (%s)' % (title, rel))
            src, dst = os.path.join(a[1], 'build', *rel.split('/')), os.path.join(a[1], 'build', 'z_fedbody', name)
            if os.path.exists(dst):
                print('%s exists: left as it is (remove it to build again)' % dst); continue
            _o, sec = apply(src, dst, opt, link)
            bad += sec is None
            if sec is not None and link:
                bad += any(k == 'FAIL' for k, _t in check(dst))
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
