#!/usr/bin/env python3
r"""
kl_dmvoice.py - a Dead Men voice of their own for the eight Dead Men heisters (owner 2026-10-23; re/voice_1023.md).

    python tools/kl_dmvoice.py build  [--game <Dog Days folder>] [--out G:\kl_build_1023\voice_1023] [--maps DM01,DD01] [--review]
    python tools/kl_dmvoice.py plan   [--game ...]       # the clip choice only (no archive is written): counts + the review table
    python tools/kl_dmvoice.py check  [--game ...] [--out ...]   # re-reads the staged files: keys, sounds, ini rules

What it grafts, into EVERY installed map folder (<game>\KLExpansion\Maps\<map>, built from the folder's own archive and its
.WHD / .WAV / _LS.SND, as tools/kl_dmlines.py does), from Dead Men's M01_FA_A bank:
  KLVoice/<Character>/<Event>     one leaf per Dog Days event line the map's English .LOC has (Multiplayer/*/<Event>_C<n> with the
                                  _C<n> cut off, '_R' radio twin kept): 'Backstab_01', 'Backstab_01_R', 'ReachlootArea_02' ...
                                  The hook (klhook/klvoice.c, [Voice] Enable=1) puts the leaf into the speech manager's line in
                                  place of the entry of the voice number that character's body speaks with.
  KLVoice/<Character>/Idle_n, Stage2_n, Down_n, Money_n     the character's KLTalk.ini pools (Who=<Character>)
  KLVoice/<Character>/Call_n, Ans_n, Arg_n                  the generic pair material (Dead Men crew pairs; Kane / Lynch with a Dog Days
                                                            heister or with a Dead Men crew member)
  KLVoice/Kane|Lynch/Pair_KLnn_Call|Reply                   thirteen exchanges only Kane and Lynch have (campaign lines that name
                                                            the other one: 'Lynch! Hurry!' -> 'Come on! I'm waiting!')
and a KLTalk.ini per map: the installed one with the six Dead Men characters' pools and every pair that touches them (and every
Kane / Lynch pair with a Dog Days heister) replaced by the real voices.

THE VOICE TABLE IS A GUESS (SPEAKERS below): Dead Men's FA characters have no campaign voice of their own. Kane and Lynch speak
as Kane and Lynch; each other character is given the campaign speaker whose voice and manner fits him best by the notes in
re/characters.md - nobody checked it by ear. Which clip fits which Dog Days event is a GUESS too (THEMES): by the clip's text.
Every choice is written to voice_review.tsv (character, event, source key, text) for the owner to read.
"""
import os, re, sys, zlib, zipfile, collections, hashlib, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_snd, kl_loc, kl_loc_fit, kl_voice, kl_talk_chars as tc

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
OUT = r'G:\kl_build_1023\voice_1023'
SRC_LEVEL = 'M01_FA_A'
LOC_CAP = kl_loc.LOC_CAP                             # the game's .LOC buffer limit and why: see kl_loc
O = 'AllLevels/Oneliners/'

# wardrobe name -> (campaign speaker suffix in the Dead Men key, why). GUESS (re/voice_1023.md 2).
SPEAKERS = collections.OrderedDict([
    ('Kane',      ('Hero',    'Kane himself (suffix _Hero)')),
    ('Lynch',     ('Lynch',   'Lynch himself')),
    ('Ashkanan',  ('Thapa',   'GUESS: the Asian-named heister gets the campaign Thapa')),
    ('Meldal',    ('Carlos',  'GUESS: the Latin-named heister gets Carlos')),
    ('Red',       ('Merc',    'GUESS: the plain mercenary voice (_Merc) for the man called Red')),
    ('Parker',    ('Rific',   'GUESS: the rough American-sounding Rific')),
    ('Standen',   ('Shelly',  'GUESS: Shelly')),
    ('Hutchison', ('Merc01',  'GUESS: the second mercenary voice (_Merc01); _Merc02 (11 clips) is unused')),
])
DM6 = [n for n in SPEAKERS if n not in ('Kane', 'Lynch')]

# campaign clips that do not fit a heist or say something about the campaign: never used
SKIP_CAT = re.compile(r'(?i)^(Flashbacks|LynchMutter|SmallTalk|StealEquip|SwitchMercs|TeamDisruption|Weapon_Sharing/(Give|Take|Swap|PlayerForces|MercMutter)|Healing/Die_Hero_Healing|ShotAt)')
BAD_TEXT = re.compile(r"(?i)ammo|clip\b|clips\b|syringe|adrenal|\beye|\bears\b|burning|\bgas\b|stings|can.t see|nurse|hum|sniper|swat|rapel|rappel|grenade|armou?r|weapon|\bgun\b|my stuff|your stuff|own stuff|spare|\bdry\b|\bdie\b|\bOD\b|inject|\bcar\b|vehicle")
NAMES = re.compile(r'(?i)\b(Lynch|Kane|Glazer|Bain|Carlos|Rific|Shelly|Thapa|Jimmy|Adam|J\.C\.)\b')
MAXLEN = 78

# event base name (Dog Days leaf without _NN / _R) -> theme (GUESS by the event's text, ev.txt of 2026-10-23)
EVENT_THEME = [
    (r'^BackstabReply', 'payback'), (r'^Backstab', 'hunt'), (r'^DriverTraitor', 'hunt'), (r'^DriverBribe', 'go'),
    (r'^ShootOffMoney', 'hunt'), (r'^ShootEsc', 'hunt'), (r'^(Revenge|PersonalRevenge|UCC|EscAndPlayerDead)', 'payback'),
    (r'^(TeamDead|EscDestroyed)', 'down'), (r'^EscHeav', 'shoot'), (r'^CallEsc', 'esc'), (r'^(YouEsc|AllEsc)', 'win'),
    (r'^JackPot', 'greed'), (r'^TeamCashMajority', 'loot'), (r'^CashMajority', 'watch'), (r'^ReachlootArea', 'loot'),
    (r'^(ExitLootArea|ExitHeist|MissionBriefing|MissionReminder)', 'go'), (r'^LevelBound', 'bounds'),
    (r'^(AllianceReminder|TeamAlliance|TimeOut)', 'together'),
    # voiceheard 2026-10-23: the 'FA_' events (what a non-radio line is called) used to match nothing and all got 'loot'.
    # event_theme() now strips 'FA_' / '1time_', so the rules above work for them; these are the events only they have (GUESS by name):
    (r'^(CallExitVehicle|ExitVehicleAnd|ExitVehicleDestroyed)', 'esc'), (r'^ExitVehicleHeav', 'shoot'), (r'^ShootExitVehicle', 'hunt'),
    (r'^(PoliceReward|HittingTheScore)', 'greed'), (r'^(AllDead|TeamloseGame|TeamOneMercLeft)', 'down'),
    (r'^(TeamLeading|TeamWinGame)', 'win'), (r'^(TeamTrailing|TeamDraw)', 'watch'), (r'^Exit', 'go'),
]
# theme -> category groups (regex on the campaign category below AllLevels/Oneliners/), best first
THEMES = {
    'loot':     ['Generic/Positive', 'KillingEnemy', 'Hero_Orders/FollowMe', 'Advance'],
    'greed':    ['Denying|DenyingResponse|Negative Shout|ReluctantResponse', 'Generic/Negative'],
    'watch':    ['Hero_Orders/ShootAtMyMark', 'EnemyHype', 'ProvideCover', 'Hero_Orders/GoThere'],
    'hunt':     ['Hero_Orders/ShootAtMyMark', 'EnemySuppress$', 'ShootCoveredEnemy', 'Generic/Negative'],
    'payback':  ['KillingEnemy', 'Generic/Negative', 'ReluctantResponse|DenyingResponse', 'ShootingKL'],
    'down':     ['EnemySuppress$', 'Generic/Exclamation', r'Healing/Die_Victim', 'ManDown'],
    'together': ['Generic/Negative', 'LevelBounds', 'HeavyFire', 'Hero_Orders/FollowMe'],
    'go':       ['Hero_Orders', 'Airlock', 'Advance', 'Generic/Positive'],
    'win':      ['KillingEnemy', 'Generic/Positive', 'Advance', 'Hero_Orders/FollowMe'],
    'shoot':    ['Hero_Orders/ShootAtMyMark', 'ProvideCover', 'EnemySuppress$', 'KillingEnemy'],
    'esc':      ['GetawayVehicle', 'Hero_Orders/(FollowMe|ComeHere)', 'Airlock', 'Advance'],
    'bounds':   ['LevelBounds', 'Hero_Orders/ComeHere', 'Generic/Negative', 'Hero_Orders/FollowMe'],
    # pool / pair material
    'idle':     ['EnemySuppress$', 'KillingEnemy', 'HeavyFire', 'EnemyHype', 'ProvideCover'],
    'stage2':   ['Advance', 'Hero_Orders/GoThere', 'Hero_Orders/FollowMe'],
    'money':    ['Generic/Positive', 'KillingEnemy'],
    'call':     ['Hero_Orders/(FollowMe|ComeHere|GoThere)', 'Airlock', 'Advance', 'ProvideCover'],
    'ans':      ['Generic/Positive', 'PositiveResponse', 'AdvanceResponse', 'ShootAtMyMark'],
    'arg':      ['Generic/Negative', 'ReluctantResponse|DenyingResponse', 'HeavyFire'],
}
FALLBACK = ['Generic', 'EnemySuppress', 'Hero_Orders', 'ShootAtMyMark', 'ProvideCover', 'KillingEnemy', 'ManDown', '.']
NDIST = 4            # distinct clips per (character, theme) for the event leaves
POOLS = [('idle', 'Idle', 6, 'idle'), ('stage2', 'Stage2', 3, 'stage2'), ('down', 'Down', 3, 'down'), ('money', 'Money', 3, 'money')]
PAIRKINDS = [('Call', 'call', 4), ('Ans', 'ans', 4), ('Arg', 'arg', 3)]

# Kane + Lynch only: (pair id, caller, caller's source leaf, replier, replier's source leaf). Source leaf = the campaign key's last part.
# All of them name the other one or answer a line that does. The pairing (which answers which) is a GUESS from the two texts.
KL_PAIRS = [
    ('01', 'Kane', 'AirlockKane_030_Hero', 'Lynch', 'AirlockLynch_050_Lynch'),                    # Lynch! Hurry! -> Come on! I'm waiting!
    ('02', 'Lynch', 'AdrenalinOutRange_020_Lynch', 'Kane', 'AdrenalinOutRange_060_Hero'),        # Kane! Where the hell are you? -> Lynch. I'm on my way.
    ('03', 'Kane', '1st_WarningsKane_010_Hero', 'Lynch', 'ReluctantResponse_003_Lynch'),         # Lynch, get back here! -> Kane! Get off my case.
    ('04', 'Lynch', 'StealEquip_Lynch_030_Lynch', 'Kane', 'StealEquip_Hero_030_Hero'),           # (their own lines about each other's stuff)
    ('05', 'Kane', 'GetawayVehicleKane_010_Hero', 'Lynch', 'GetawayVehicleLynch_010_Lynch'),     # Lynch! Get in the fucking car! -> Kane! I'm in the car already!
    ('06', 'Lynch', '1st_WarningsLynch_030_Lynch', 'Kane', '1st_WarningsKane_050_Hero'),          # Kane, you're going the wrong way! -> We have to go the other way!
    ('07', 'Lynch', 'Action03_010_Lynch', 'Kane', 'Action01_040_Hero'),                           # Kane, I'm tired of all your shitty plans. -> Whatever - just focus.
    ('08', 'Lynch', 'KanesEye04_Lynch_010_Lynch', 'Kane', 'KanesEye04_Lynch_050_Hero'),          # What happened to your eye anyway? -> Quit fucking with me, Lynch.
    ('09', 'Kane', 'LynchHumming02_003_Hero', 'Lynch', 'LastWarningAnswer_001_Lynch'),           # stop that shit and concentrate -> Kane! You are stressing me out!
    ('10', 'Lynch', 'TeamDisruptionCoolDown_020_Lynch', 'Kane', 'Negative_070_Hero'),             # Kane, you just want us dead, don't you? -> That's stupid
    ('11', 'Kane', 'GiveAmmo_01_Hero', 'Lynch', 'GiveTake_03_Lynch'),                             # This should keep you going -> Thanks a lot, Kane
    ('12', 'Lynch', 'SWATWarning_030_Lynch', 'Kane', 'EnemyHype_050_Hero'),                       # SWATs. Now what are you going to do Kane? -> SWAT's. We can't take 'em head on!
    ('13', 'Lynch', 'ShotAt_010_Lynch', 'Kane', 'AdrenalinOutRange_010_Hero'),                   # Kane! Get me out of here! -> Lynch! Keep calm. I'll be there.
]
SPK_RX = re.compile(r'_(Hero|Lynch|Carlos|Rific|Shelly|Thapa|Merc01|Merc02|Merc)(?:_[a-z])?$')


class Clip:
    __slots__ = ('path', 'leaf', 'cat', 'text', 'spk', 'sid', 'rsid', 'rpath')

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def load_source():
    """-> (English tree, {lang: tree}, {speaker suffix: [Clip]}) of the Dead Men FA bank; clips without a radio twin keep rsid None"""
    with zipfile.ZipFile(kl_snd.level_zip(SRC_LEVEL, 'dm')) as zf:
        raw = {lang: zf.read(n) for lang, n in kl_loc.members(zf).items()}
    trees = {lang: kl_loc.parse(d) for lang, d in raw.items()}
    en = {p: n for p, n in kl_loc.leaves(trees['English'])}
    clips = collections.defaultdict(list)
    for p, n in en.items():
        if not p.startswith(O) or p.endswith('_R') or p.lower().startswith('allLevels/oneliners/expressions'):
            continue
        text, _x, sid, _l = kl_loc.fields(n)
        parts = p.split('/')
        m = SPK_RX.search(parts[-1])
        if not m or not sid:
            continue
        cat = '/'.join(parts[2:-1])
        r = en.get(p + '_R')
        rsid = kl_loc.fields(r)[2] if r is not None else None
        clips[m.group(1)].append(Clip(path=p, leaf=parts[-1], cat=cat, text=(text or b'').decode('latin1'), spk=m.group(1), sid=sid,
                                      rsid=rsid or None, rpath=p + '_R' if rsid else None))
    return trees, clips


def usable(c, allow_names=False):
    t = c.text.strip()
    if not t or len(t) > MAXLEN or SKIP_CAT.match(c.cat) or BAD_TEXT.search(t):
        return False
    if '?' in t.replace('???', '') and False:
        return False
    return allow_names or not NAMES.search(t)


# what the TEXT of a clip must say to fit a theme (GUESS, by reading the Dead Men lines): the clips that match come first,
# the category groups of THEMES only fill up what the text did not
THEME_RX = {
    'loot': r"(?i)(yes|yeah|got it|got him|nice|good|sure|great|come on|let's go|go on|move|this way|follow|over here|here|mine)",
    'greed': r"(?i)(mine|nice|yes|yeah|got it|sweet|good|all right|alright|come on)",
    'watch': r"(?i)(watch|cover|behind|over there|look|there|keep|eyes|enemy|careful|take him|shoot)",
    'hunt': r"(?i)(shoot|kill|bastard|get him|get them|take him|take them|there he|enemy|fire|open fire|die|dead)",
    'payback': r"(?i)(fuck|bastard|die|dead|asshole|you're dead|got him|he's down|payback|kill|son of)",
    'down': r"(?i)(help|down|hit|trapped|back ?up|medic|need|man down|shit|argh|damn)",
    'together': r"(?i)(together|stay|follow|stick|come on|with me|behind|cover|watch|don't|no)",
    'go': r"(?i)(go|move|run|now|let's|come|hurry|out|follow|quick|faster|get)",
    'win': r"(?i)(yes|yeah|got|nice|good|great|done|we did|all right|alright|go|let's)",
    'shoot': r"(?i)(shoot|fire|cover|kill|take|there|hit|get)",
    'esc': r"(?i)(go|get in|car|van|move|run|hurry|come|now|out|let's)",
    'bounds': r"(?i)(back|where|wrong way|come|get back|turn|no|not that way|stay|here)",
}
BAD_FOR = {  # a text that is never right for the theme
    'hunt': r"(?i)help|trapped|here you go|thanks|sure thing|take these",
    'payback': r"(?i)help|trapped|here you go|thanks|sure thing|take these|sorry",
    'down': r"(?i)here you go|thanks|sure thing|take these|let's go",
    'go': r"(?i)help|trapped|here you go|thanks|sure thing|take these",
    'win': r"(?i)help|trapped|fuck you|shit|take these|here you go",
    'shoot': r"(?i)help|trapped|here you go|thanks|sure thing|take these",
    'loot': r"(?i)help|trapped|fuck you|die|here you go|take these",
    'greed': r"(?i)help|trapped|fuck you|take these|here you go",
    'watch': r"(?i)help|trapped|here you go|take these",
    'together': r"(?i)help|trapped|here you go|take these",
    'esc': r"(?i)help|trapped|here you go|take these",
    'bounds': r"(?i)help|trapped|here you go|take these",
}


def candidates(clips, theme, need=6, car=False):
    """the best clips for a theme, in order: category groups best first until `need` are there, then the fallback groups"""
    out, seen = [], set()
    ok = [c for c in sorted(clips, key=lambda c: c.path) if usable(c)]
    bad = re.compile(BAD_FOR[theme]) if theme in BAD_FOR else None
    if bad:
        ok = [c for c in ok if not bad.search(c.text)] or ok
    if theme in THEME_RX:                                   # the text that fits first, in category-group order
        rx = re.compile(THEME_RX[theme])
        for g in THEMES[theme]:
            gr = re.compile(g)
            for c in ok:
                if c.path not in seen and gr.search(c.cat) and rx.search(c.text):
                    seen.add(c.path); out.append(c)
        for c in ok:
            if c.path not in seen and rx.search(c.text):
                seen.add(c.path); out.append(c)
        if len(out) >= need:
            return out
    for g in THEMES[theme] + FALLBACK:
        rx = re.compile(g)
        for c in ok:
            if c.path not in seen and rx.search(c.cat):
                seen.add(c.path); out.append(c)
        if len(out) >= need and g in THEMES[theme]:
            break
    return out


def pick(clips, theme, tag, n):
    """n distinct clips for (tag, theme) spread over the candidates, in an order fixed by the tag"""
    cand = candidates(clips, theme, max(need_for(n), 6))
    if not cand:
        return []
    off = zlib.crc32(('%s/%s' % (tag, theme)).encode()) % len(cand)
    out = []
    for i in range(min(n, len(cand))):
        c = cand[(off + i * 2 + i // len(cand)) % len(cand)]
        if c not in out:
            out.append(c)
    for c in cand:                               # a stride that collided: fill from the front
        if len(out) >= min(n, len(cand)):
            break
        if c not in out:
            out.append(c)
    return out


def need_for(n):
    return n + 4


def event_theme(name):
    base = re.sub(r'_R$', '', name)
    base = re.sub(r'_\d+$', '', base)
    # NOTE the returned base is what the clip pick hashes (crc32). It is the cleaned name on purpose: it matches the staged DM01 build, and
    # FA_YouEscaped01/02/03 share one base. A rebuild moves the clip pick only of events with trailing digits not preceded by '_' (YouEscaped0N, Stage2).
    base = re.sub(r'^(FA_)?(1time_)?', '', base)        # 'FA_Backstab' -> 'Backstab' (voiceheard: they all fell through to 'loot'); review 5: also a bare '1time_'
    base = re.sub(r'\d+$', '', base)                    # 'YouEscaped01' -> 'YouEscaped'
    for rx, th in EVENT_THEME:
        if re.search(rx, base):
            return base, th
    if base not in _THEME_WARNED:                       # review 5: a name no rule knows silently became 'loot' before
        _THEME_WARNED.add(base)
        print('kl_dmvoice: warning: event %r matches no theme rule, using "loot"' % base)
    return base, 'loot'


_THEME_WARNED = set()


class Plan:
    """the leaves one map gets: {Character: {leaf name: (Clip, radio?)}} plus the review rows"""

    def __init__(self, clips, events):
        self.leaves = collections.OrderedDict((n, collections.OrderedDict()) for n in SPEAKERS)
        self.review = []
        self.pair = {}
        for who, (spk, why) in SPEAKERS.items():
            cl = clips[spk]
            L = self.leaves[who]
            themed = {}
            for ev in events:                                   # 'Backstab_01', 'Backstab_01_R'
                base, th = event_theme(ev)
                if th not in themed:
                    themed[th] = pick(cl, th, who, NDIST)
                sel = themed[th]
                if not sel:
                    continue
                m = re.search(r'_(\d+)(_R)?$', ev)
                num = int(m.group(1)) if m else 1
                c = sel[(num - 1 + zlib.crc32(base.encode())) % len(sel)]
                L[ev] = (c, ev.endswith('_R'))
                self.review.append((who, ev, th, c.path, c.text))
            for tag, on, n, th in POOLS:
                for i, c in enumerate(pick(cl, th, who, n), 1):
                    L['%s_%d' % (on, i)] = (c, False)
                    self.review.append((who, '%s_%d' % (on, i), th, c.path, c.text))
            for on, th, n in PAIRKINDS:
                for i, c in enumerate(pick(cl, th, who + on, n), 1):
                    L['%s_%d' % (on, i)] = (c, False)
                    self.review.append((who, '%s_%d' % (on, i), th, c.path, c.text))
        by = {w: {c.leaf: c for c in clips[SPEAKERS[w][0]]} for w in ('Kane', 'Lynch')}
        for pid, a, ak, b, bk in KL_PAIRS:
            ca, cb = by[a].get(ak), by[b].get(bk)
            if not ca or not cb:
                continue
            self.leaves[a]['Pair_KL%s_Call' % pid] = (ca, False)
            self.leaves[b]['Pair_KL%s_Reply' % pid] = (cb, False)
            self.pair[pid] = (a, b)
            self.review.append((a, 'Pair_KL%s_Call' % pid, 'kane+lynch', ca.path, ca.text))
            self.review.append((b, 'Pair_KL%s_Reply' % pid, 'kane+lynch', cb.path, cb.text))

    def roots(self):
        out = set()
        for L in self.leaves.values():
            for c, radio in L.values():
                out.add(c.rsid if radio and c.rsid else c.sid)
        return out

    def counts(self):
        return {w: (len(L), len({(c.path, r) for c, r in L.values()})) for w, L in self.leaves.items()}


SINGLE_MAX = 200     # singles added per table kind (plain / radio twin): a .LOC table holds 255 leaves, the pools and pairs need about 30


def _theme_known(name):
    base = re.sub(r'_R$', '', name)
    base = re.sub(r'_\d+$', '', base)
    base = re.sub(r'^(FA_)?(1time_)?', '', base)
    base = re.sub(r'\d+$', '', base)
    for i, (rx, _th) in enumerate(EVENT_THEME):
        if re.search(rx, base):
            return i
    return -1


def map_events(loc_tree, singles=True):
    """Dog Days event leaves of a map's English .LOC: Multiplayer/<Folder>/<Event>_C<n> -> 'Event' (radio twin '_R' kept).
    singles (voiceplain 2026-10-24, klvoice.c PlainData=1): also the SINGLE-ENTRY events (flag-0 lines: the loader builds one
    entry from the bare key, no _C<n> siblings, e.g. FA_YouEscaped01_R, FA_PoliceReward_01, Backstab_xx_R). The leaf is the whole last
    path part, exactly what klvoice.c's kvo_cv_line derives from the entry's key text. Only events whose name an EVENT_THEME rule
    knows are taken (the theme picks the Dead Men clip); the rest (police briefings, intros, team police lines, names with spaces)
    stay stock - GUESS that nothing else needs a Dead Men voice. At most SINGLE_MAX per kind, in EVENT_THEME order."""
    ev = set()
    base = set()
    for p, _n in kl_loc.leaves(loc_tree):
        parts = p.split('/')
        if parts[0].lower() == 'multiplayer' and len(parts) == 3:
            m = re.match(r'^(.+)_C\d$', parts[2])
            if m:
                ev.add(m.group(1))
            else:
                base.add(parts[2])
    if singles:
        sing = sorted(b for b in base if b not in ev and ' ' not in b and not re.match(r'(?i)^(Police(Br|Mission)|TeamPolice|Intro)', b) and _theme_known(b) >= 0)
        for radio in (False, True):
            pick_ = sorted((b for b in sing if b.endswith('_R') == radio), key=lambda b: (_theme_known(b), b))
            ev.update(pick_[:SINGLE_MAX])
    return sorted(ev)


def add_leaf(tree, path, text, sid):
    kids = tree
    for part in path[:-1]:
        nm = part.encode('latin1')
        t = next((k for k in kids if k.name.lower() == nm.lower()), None)
        if t is None:
            t = kl_loc.Node(nm, kl_loc.TABLE, [])
            kl_loc._insert(kids, t)
        if t.kids is None:
            raise ValueError('%s is a leaf, not a table' % part)
        kids = t.kids
    kl_loc._insert(kids, kl_loc.leaf(path[-1].encode('latin1'), text, sid))


def vpath(who, leaf):
    """the .LOC path of a voice leaf. A table holds at most 255 entries (one count byte), so the radio twins of the Dog Days
    events live in their own table: 'Backstab_01_R' -> KLVoice/<Name>_R/Backstab_01 (klvoice.c builds the same path)."""
    if leaf.endswith('_R'):
        return ('KLVoice', who + '_R', leaf[:-2])
    return ('KLVoice', who, leaf)


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------------------------------------ the ini
def new_ini(game, m, plan, loc, ward, names, v2):
    """the map's installed KLTalk.ini with the Dead Men characters' pools / pairs replaced -> text"""
    folder = os.path.join(game, 'KLExpansion', 'Maps', m)
    ini = os.path.join(folder, 'KLTalk.ini')
    if not os.path.isfile(ini):
        return None, {}
    talk, scenes, chatter, pools, pairs = tc.parse_ini(open(ini, 'rb').read().decode('latin1'))
    mine = {n.lower() for n in DM6}
    def dm(w):
        return w.lower() in mine
    pools = [p for p in pools if not dm(p['who'])]
    keep = []
    for q in pairs:
        cw, rw = q['cwho'], q['rwho']
        kl = lambda w: w.lower() in ('kane', 'lynch')
        merc = lambda w: re.match(r'(?i)char\d+$', w) is not None
        if dm(cw) or dm(rw) or (kl(cw) and merc(rw)) or (merc(cw) and kl(rw)) or (kl(cw) and kl(rw)):
            continue
        keep.append(q)
    pairs = keep
    K = lambda who, leaf: 'KLVoice/%s/%s' % (who, leaf)
    have = lambda who, leaf: leaf in plan.leaves.get(who, {})
    dmn = [n for n in DM6 if n.lower() in names]
    # the six: their pools
    for who in dmn:
        for tag, on, n, th in POOLS:
            ks = [K(who, '%s_%d' % (on, i)) for i in range(1, n + 1) if have(who, '%s_%d' % (on, i))]
            if ks:
                pools.append(dict(name='%s_%s' % (who.lower(), tag), who=who, on=on, keys=ks))
    def kind(who, k, i):
        for j in range(4):
            leaf = '%s_%d' % (k, (i + j) % 4 + 1)
            if have(who, leaf):
                return K(who, leaf)
        return None
    new = []
    # Kane + Lynch: the thirteen exchanges
    for pid, (a, b) in sorted(plan.pair.items()):
        if a.lower() in names and b.lower() in names:
            new.append((a, K(a, 'Pair_KL%s_Call' % pid), b, K(b, 'Pair_KL%s_Reply' % pid)))
    # Dead Men crew pairs: friendly (Call -> Ans) and an argument (Arg -> Arg), index by who is who
    order = list(SPEAKERS)
    for a in dmn:
        for b in dmn:
            if a == b:
                continue
            ia, ib = order.index(a), order.index(b)
            c, r = kind(a, 'Call', ia + ib), kind(b, 'Ans', ia * 3 + ib)
            if c and r:
                new.append((a, c, b, r))
            if (ia + ib) % 2 == 0:
                c, r = K(a, 'Arg_%d' % (ib % 3 + 1)), K(b, 'Arg_%d' % (ia % 3 + 1))
                if have(a, 'Arg_%d' % (ib % 3 + 1)) and have(b, 'Arg_%d' % (ia % 3 + 1)):
                    new.append((a, c, b, r))
    # Kane / Lynch with a Dead Men crew member, both directions
    for kl in ('Kane', 'Lynch'):
        if kl.lower() not in names:
            continue
        for i, d in enumerate(dmn):
            c, r = kind(kl, 'Call', i), kind(d, 'Ans', i + 1)
            if c and r:
                new.append((kl, c, d, r))
            c, r = kind(d, 'Call', i + 2), kind(kl, 'Ans', i)
            if c and r:
                new.append((d, c, kl, r))
    # Kane / Lynch with a Dog Days heister (wardrobe 1..8, voice _C<slot+1>), Dead Men voices on their side
    mercs = [(n, int(ward[n]['Slot']) + 1) for n in range(1, 9) if n in ward and 'Slot' in ward[n]]
    mr = [k for k in tc.MERC_REPLY if tc.merc_ok(loc, k)]
    mc = [k for k in tc.MERC_CALL if tc.merc_ok(loc, k)]
    for kl in ('Kane', 'Lynch'):
        if kl.lower() not in names:
            continue
        for (num, v) in mercs:
            if (num + (kl == 'Lynch')) % 2 == 0 and mr:
                c = kind(kl, 'Call', num)
                if c:
                    new.append((kl, c, 'Char%d' % num, '%s_C%d' % (mr[num % len(mr)], v)))
            elif mc:
                r = kind(kl, 'Ans', num)
                if r:
                    new.append(('Char%d' % num, '%s_C%d' % (mc[num % len(mc)], v), kl, r))
    # Dead Men crew with a Dog Days heister
    for i, d in enumerate(dmn):
        for (num, v) in mercs:
            if (i + num) % 2 == 0 and mr:
                c = kind(d, 'Call', num)
                if c:
                    new.append((d, c, 'Char%d' % num, '%s_C%d' % (mr[(i + num) % len(mr)], v)))
            elif mc:
                r = kind(d, 'Ans', i + num)
                if r:
                    new.append(('Char%d' % num, '%s_C%d' % (mc[(i + num) % len(mc)], v), d, r))
    room = tc.LIM['pair'] - len(pairs)
    cut = max(0, len(new) - room)
    new = new[:room]
    for c, ck, r, rk in new:
        pairs.append(dict(cwho=c, ckey=ck, rwho=r, rkey=rk, wait=None))
    talk['Version'] = '2'; talk['Scenes'] = str(len(scenes))
    chatter['Pools'] = str(len(pools)); chatter['Pairs'] = str(len(pairs))
    lines = ['; written by tools/kl_dmvoice.py (re/voice_1023.md): the Dead Men characters speak their own campaign voice (KLVoice/<Name>/..)',
             '; GUESS which campaign speaker is whom (SPEAKERS in the tool); every key is in this map\'s English .LOC with a sound id', '[Talk]']
    for k, v in talk.items():
        lines.append('%s=%s' % (k, v))
    out = '\n'.join(lines) + '\n' + '\n'.join(s.rstrip('\n') for s in scenes) + ('\n' if scenes else '')
    out += '[Chatter]\n' + ''.join('%s=%s\n' % (k, v) for k, v in chatter.items())
    for i, p in enumerate(pools, 1):
        out += '[Pool.%d]\nName=%s\nWho=%s\nOn=%s\nKeys=%d\n' % (i, p['name'], p['who'], p['on'], len(p['keys']))
        out += ''.join('Key.%d=%s\n' % (j, k) for j, k in enumerate(p['keys'], 1))
    for i, q in enumerate(pairs, 1):
        out += '[Pair.%d]\nCall=%s,%s\nReply=%s,%s\n' % (i, q['cwho'], q['ckey'], q['rwho'], q['rkey'])
        if q.get('wait'):
            out += 'Wait=%s\n' % q['wait']
    return out, dict(pools=len(pools), pairs=len(pairs), new_pairs=len(new), dropped_pairs=cut, kl_pairs=sum(1 for q in new if {q[0], q[2]} == {'Kane', 'Lynch'}))


# ------------------------------------------------------------------------------------------------ build one map
def build_map(game, m, out, trees, clips, log=print, write=True):
    folder = os.path.join(game, 'KLExpansion', 'Maps', m)
    zp = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('_main.zip')][0]
    prefix = zp[:-4]
    sname = os.path.basename(zp)[:-4]
    with zipfile.ZipFile(zp) as zf:
        snd_name = [n for n in zf.namelist() if n.upper().endswith('_MAIN.SND')][0][:-4]
        snd = zf.read(snd_name + '.SND')
        locs = {lang: zf.read(n) for lang, n in kl_loc.members(zf).items()}
    ttrees = {lang: kl_loc.parse(d) for lang, d in locs.items()}
    if any(p.lower().startswith('klvoice/') for p, _k in kl_loc.leaves(ttrees['English'])):
        raise ValueError('%s already holds KLVoice/: build from the .before-1023voice archive' % m)
    events = map_events(ttrees['English'])
    plan = Plan(clips, events)
    ward = tc.read_wardrobe(os.path.join(folder, 'KLWardrobe.ini')) if os.path.isfile(os.path.join(folder, 'KLWardrobe.ini')) else {}
    names = {c.get('Name', '').lower(): n for n, c in ward.items()}
    present = [w for w in SPEAKERS if w.lower() in names]
    info = {'map': m, 'events': len(events), 'characters': present, 'counts': plan.counts()}
    if not present:
        log('%s: the wardrobe has none of the eight: nothing to do' % m)
        return info, plan
    if not write:
        return info, plan
    whd, wav = kl_snd.read(prefix + '.WHD'), kl_snd.read(prefix + '.WAV')
    ls = kl_snd.read(prefix + '_LS.SND')
    base = kl_snd.Snd('dd', snd, ls).walk()
    src = kl_snd.bank(SRC_LEVEL, 'dm')
    st = collections.Counter()
    nsnd, nwhd, nwav, omap = kl_snd.merge(base, src, whd, wav, kl_snd.read(kl_snd.beside(SRC_LEVEL, '.WHD', 'dm')),
                                          kl_snd.read(kl_snd.beside(SRC_LEVEL, '.WAV', 'dm')), plan.roots(), log=log, stats=st,
                                          inmem=kl_voice.stream_clip)
    silent = collections.Counter()
    files = {}
    info['loc_bytes'] = {}
    for lang, d in locs.items():
        if ttrees[lang] is None:
            files[lang] = d; continue
        s = trees.get(lang) or trees['English']
        sidx = {p: n for p, n in kl_loc.leaves(s)}
        cap = LOC_CAP
        if len(d) > cap:                                   # the source itself is over the cap: shrink it (fit), never pass it on over the cap
            d = kl_loc_fit.fit(d, cap, locs.get('English'))
            log('%s: %s .LOC was over %d in the source: shrunk to %d by kl_loc_fit' % (m, lang, cap, len(d)))
        first = None
        # tiers until it fits: everything; no subtitle text; no subtitle text and no radio twins (klvoice.c finds no leaf for a
        # radio line then and leaves that line stock Dog Days)
        for tier in (0, 1, 2):
            subs, radios = tier == 0, tier < 2
            t = kl_loc.parse(d)
            for who in present:
                for leaf, (c, radio) in plan.leaves[who].items():
                    if not radios and leaf.endswith('_R'):
                        continue
                    key = c.rpath if radio and c.rpath else c.path
                    node = sidx.get(key) or {p: n for p, n in kl_loc.leaves(trees['English'])}[key]
                    text, _x, sid, _l = kl_loc.fields(node)
                    new = omap.get(sid, 0) if sid else 0
                    if subs and lang == 'English' and not new:
                        silent[who] += 1
                    add_leaf(t, vpath(who, leaf), text if subs else b'', new)
            files[lang] = kl_loc.build(t)
            first = first or files[lang]
            if len(files[lang]) <= cap:
                break
            log('%s: %s .LOC %d bytes > %d at tier %d (%s): trying the next' % (m, lang, len(files[lang]), cap, tier,
                                                                             ('full', 'no subtitles', 'no subtitles, no radio')[tier]))
        if len(files[lang]) > cap:                         # no tier fits: keep the full build and shorten other text (kl_loc_fit: English subtitles, ...)
            log('%s: %s .LOC %d bytes > %d at every tier: kl_loc_fit' % (m, lang, len(files[lang]), cap))
            try:
                files[lang] = kl_loc_fit.fit(first, cap, locs.get('English'))
                tier = 0
            except ValueError as e:                    # cannot happen for a stock source; never ship over the cap, the source (within it) stays
                files[lang] = d
                info['loc_bytes'][lang] = (len(d), len(d), 'cannot fit: no voice leaves')
                info.setdefault('problems', []).append('%s .LOC does not fit LOC_CAP: %s' % (lang, e))
                continue
        info['loc_bytes'][lang] = (len(d), len(files[lang]), ('full', 'no subtitles', 'no subtitles, no radio')[tier])
    nls = kl_snd.ls_bank(ls, kl_snd.u32(nsnd, 0))
    problems, cnt = kl_snd.verify(base, nsnd, nwhd, nwav, nls, omap)
    problems = info.get('problems', []) + problems
    info.update(stats=dict(st + cnt), problems=problems, silent=dict(silent))
    if problems:
        log('%s: VERIFY PROBLEMS %s' % (m, problems[:5]))
    od = os.path.join(out, m)
    os.makedirs(od, exist_ok=True)
    newmem = {snd_name + '.SND': nsnd}
    with zipfile.ZipFile(zp) as zf0:
        newmem.update({mem: files[lang] for lang, mem in kl_loc.members(zf0).items()})
    with zipfile.ZipFile(zp) as zin, zipfile.ZipFile(os.path.join(od, sname + '.zip'), 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as zo:
        for zi in zin.infolist():
            data = newmem.get(zi.filename)
            if data is None:
                data = zin.read(zi.filename)
            ni = zipfile.ZipInfo(zi.filename, zi.date_time)
            ni.compress_type, ni.external_attr = zi.compress_type, zi.external_attr
            zo.writestr(ni, data)
    open(os.path.join(od, sname + '.WHD'), 'wb').write(nwhd)
    open(os.path.join(od, sname + '.WAV'), 'wb').write(nwav)
    open(os.path.join(od, sname + '_LS.SND'), 'wb').write(nls)
    loc_new = tc.Loc(os.path.join(od, sname + '.zip'))
    text, ii = new_ini(game, m, plan, loc_new, ward, names, 2)
    if text is not None:
        open(os.path.join(od, 'KLTalk.ini'), 'wb').write(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('latin1'))
        info['ini'] = ii
        bad = tc.check_text(text, loc_new, ward, m)
        info['ini_problems'] = bad
        if bad:
            log('%s: KLTalk.ini problems: %s' % (m, bad[:6]))
    # what the install replaces and the md5 of each file it was built from
    srcs = {}
    for ext in ('.zip', '.WHD', '.WAV', '_LS.SND', None):
        fn = (sname + ext) if ext else 'KLTalk.ini'
        p = os.path.join(folder, fn)
        if os.path.isfile(p) and (ext or text is not None):
            srcs[fn] = md5(p)
    info['built_from_md5'] = srcs
    json.dump(info, open(os.path.join(od, 'manifest.json'), 'w'), indent=1, default=str)
    log('%s: %d events, %s, ini %s, verify %s' % (m, len(events), {w: n for w, n in plan.counts().items()}, info.get('ini'), 'ok' if not problems else problems[:2]))
    return info, plan


def review_file(path, plan):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('character\tleaf\ttheme\tsource key\ttext\n')
        for r in plan.review:
            f.write('\t'.join(x.replace('\t', ' ') for x in r) + '\n')


PS1 = r'''# written by tools/kl_dmvoice.py - installs / undoes the Dead Men voice files (re/voice_1023.md). Offline: refuses while kl2.exe runs.
param([string]$Mode, [string]$Game, [string]$Src, [switch]$Hook)
$ErrorActionPreference = 'Stop'
$suffix = '.before-1023voice'
$hookMd5 = '__HOOKMD5__'                                   # the hook this was built with (hook\dinput8.dll); -Hook installs only that file
if (Get-Process kl2 -ErrorAction SilentlyContinue) { Write-Host 'kl2.exe is running: close the game first.'; exit 1 }
function Md5($p) { (Get-FileHash -Algorithm MD5 -LiteralPath $p).Hash.ToLower() }
$rows = Import-Csv -LiteralPath (Join-Path $Src 'voice_1023_files.csv')
$bad = 0
$ini = Join-Path $Game 'KLHook.ini'
$keyfile = $ini + '.1023voice.keys'                        # the ini keys INSTALL set (UNDO removes only those)
Add-Type -Namespace K -Name P -MemberDefinition '[System.Runtime.InteropServices.DllImport("kernel32",CharSet=System.Runtime.InteropServices.CharSet.Ansi)] public static extern uint GetPrivateProfileString(string s,string k,string d,System.Text.StringBuilder r,uint n,string f); [System.Runtime.InteropServices.DllImport("kernel32",CharSet=System.Runtime.InteropServices.CharSet.Ansi)] public static extern bool WritePrivateProfileString(string s,string k,string v,string f);'
$hd = Join-Path $Game 'dinput8.dll'; $hs = Join-Path $Src 'hook\dinput8.dll'
if ($Mode -eq 'install') {
  foreach ($r in $rows) {                                  # checks first, every run: nothing is touched if one fails
    $s = Join-Path $Src $r.rel; $d = Join-Path $Game ('KLExpansion\Maps\' + $r.rel)
    if (-not (Test-Path -LiteralPath $s)) { Write-Host "missing staged file $s"; $bad++; continue }
    if ((Get-Item -LiteralPath $s).Length -ne [int64]$r.size) { Write-Host "staged file has the wrong size: $s"; $bad++; continue }
    if (Test-Path -LiteralPath $d) {
      $m = Md5 $d                                          # only the file this was built from, or this very file (already installed)
      if ($m -ne $r.md5 -and ($r.built_from -eq '' -or $m -ne $r.built_from)) { Write-Host "REFUSED, the installed file is neither the one this was built from nor this one (rebuild with tools/kl_dmvoice.py): $d"; $bad++ }
    }
  }
  if ($Hook) {
    if (-not (Test-Path -LiteralPath $hs)) { Write-Host "missing staged hook $hs"; $bad++ }
    elseif ((Md5 $hs) -ne $hookMd5) { Write-Host 'REFUSED: the staged hook is not the one this was built with.'; $bad++ }
    elseif (-not (Test-Path -LiteralPath $hd)) { Write-Host 'REFUSED: no dinput8.dll in the game folder to back up (install the owner hook first).'; $bad++ }
  }
  $need = 0                                                # backups are moves, so only the new files take space
  foreach ($r in $rows) { $d = Join-Path $Game ('KLExpansion\Maps\' + $r.rel); if (-not (Test-Path -LiteralPath $d) -or (Md5 $d) -ne $r.md5) { $need += [int64]$r.size } }
  $free = (Get-PSDrive $Game.Substring(0,1)).Free
  if ($free -lt $need + 2GB) { Write-Host ('REFUSED: {0:N1} GB needed + 2 GB spare, {1:N1} GB free on the game drive.' -f ($need/1GB), ($free/1GB)); $bad++ }
  if ($bad) { Write-Host "$bad problems: nothing installed."; exit 1 }
  foreach ($r in $rows) {
    $s = Join-Path $Src $r.rel; $d = Join-Path $Game ('KLExpansion\Maps\' + $r.rel)
    if (Test-Path -LiteralPath $d) {
      if ((Md5 $d) -eq $r.md5) { Write-Host ('same ' + $r.rel); continue }
      if (-not (Test-Path -LiteralPath ($d + $suffix))) { Move-Item -LiteralPath $d -Destination ($d + $suffix) }   # a move: the backup costs no disk space (C: is nearly full)
    }
    Copy-Item -LiteralPath $s -Destination $d -Force
    if ((Md5 $d) -ne $r.md5) { Write-Host "MD5 MISMATCH after copy: $d"; $bad++ } else { Write-Host ('ok  ' + $r.rel) }
  }
  if ($Hook) {                                             # only with -Hook; the default install leaves dinput8.dll alone
    if (-not (Test-Path -LiteralPath ($hd + $suffix)) -and (Md5 $hd) -ne $hookMd5) { Copy-Item -LiteralPath $hd -Destination ($hd + $suffix) }
    Copy-Item -LiteralPath $hs -Destination $hd -Force
    if ((Md5 $hd) -ne $hookMd5) { Write-Host 'MD5 MISMATCH: dinput8.dll'; $bad++ } else { Write-Host 'ok  dinput8.dll (hook with klvoice.c)' }
  }
  if (Test-Path -LiteralPath $ini) {                       # keys that are not set yet; the keys set are written to $keyfile
    $set = @(); if (Test-Path -LiteralPath $keyfile) { $set = @(Get-Content -LiteralPath $keyfile) }
    foreach ($kv in @(@('Voice','Enable','1'), @('Voice','StockLevels','1'), @('Voice','Log','2'), @('Talk','Enable','1'), @('Talk','StockLevels','1'))) {
      $sb = New-Object System.Text.StringBuilder 64
      [void][K.P]::GetPrivateProfileString($kv[0], $kv[1], '<unset>', $sb, 64, $ini)
      if ($sb.ToString() -eq '<unset>') { [void][K.P]::WritePrivateProfileString($kv[0], $kv[1], $kv[2], $ini); $set += ($kv[0] + '|' + $kv[1]); Write-Host ('set [{0}] {1}={2}' -f $kv[0], $kv[1], $kv[2]) }
      else { Write-Host ('kept [{0}] {1}={2}' -f $kv[0], $kv[1], $sb.ToString()) }
    }
    if ($set.Count) { Set-Content -LiteralPath $keyfile -Value ($set | Select-Object -Unique) }
  }
  if ($bad) { exit 1 }
  Write-Host 'installed. UNDO voice 1023.bat puts every file back.'
}
else {
  foreach ($r in $rows) {                                  # a file goes back only if it is still the one this installed
    $d = Join-Path $Game ('KLExpansion\Maps\' + $r.rel); $b = $d + $suffix
    if (-not (Test-Path -LiteralPath $b)) { continue }
    if (-not (Test-Path -LiteralPath $d)) { Move-Item -LiteralPath $b -Destination $d; Write-Host ('restored ' + $d); continue }
    if ((Md5 $d) -eq $r.md5) { Move-Item -LiteralPath $b -Destination $d -Force; Write-Host ('restored ' + $d) }
    else { Write-Host "WARNING: not restored, the live file is not the one this installed (backup stays): $d" }
  }
  if (Test-Path -LiteralPath ($hd + $suffix)) {
    if ((Test-Path -LiteralPath $hd) -and (Md5 $hd) -eq $hookMd5) { Move-Item -LiteralPath ($hd + $suffix) -Destination $hd -Force; Write-Host 'restored dinput8.dll' }
    else { Write-Host 'WARNING: dinput8.dll not restored, the live file is not the hook this installed (backup stays).' }
  }
  if (Test-Path -LiteralPath $keyfile) {                   # remove only the keys INSTALL set
    foreach ($line in @(Get-Content -LiteralPath $keyfile)) {
      $p = $line -split '\|'
      if ($p.Count -eq 2 -and (Test-Path -LiteralPath $ini)) { [void][K.P]::WritePrivateProfileString($p[0], $p[1], $null, $ini); Write-Host ('removed [{0}] {1}' -f $p[0], $p[1]) }
    }
    Remove-Item -LiteralPath $keyfile
  }
  Write-Host 'undone (files without a .before-1023voice backup were not replaced by this and are left alone).'
}
'''
BAT = r'''@echo off
rem written by tools/kl_dmvoice.py - %MODE% the Dead Men voice files (re/voice_1023.md). Backs up every replaced file first (.before-1023voice).
rem The hook (dinput8.dll) is NOT installed unless you pass "hook" as the first argument.
setlocal
set "GAME=C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days"
set "HOOKARG="
if /i "%~1"=="hook" set "HOOKARG=-Hook"
tasklist /FI "IMAGENAME eq kl2.exe" 2>nul | find /I "kl2.exe" >nul
if not errorlevel 1 (echo kl2.exe is running: close the game first. & pause & exit /b 1)
if not exist "%GAME%\kl2.exe" (echo Dog Days not found at "%GAME%": edit the GAME line of this file. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0voice_1023.ps1" -Mode %MODE% -Game "%GAME%" -Src "%~dp0." %HOOKARG%
if errorlevel 1 (echo FAILED & pause & exit /b 1)
pause
'''


def make_bats(game, out, maps):
    import csv
    rows = []
    for m in maps:
        od = os.path.join(out, m)
        if not os.path.isfile(os.path.join(od, 'manifest.json')):
            continue
        info = json.load(open(os.path.join(od, 'manifest.json')))
        for fn in sorted(os.listdir(od)):
            if fn == 'manifest.json':
                continue
            p = os.path.join(od, fn)
            rows.append((m + '\\' + fn, md5(p), os.path.getsize(p), info['built_from_md5'].get(fn, '')))
            print(rows[-1][0], rows[-1][1])
    with open(os.path.join(out, 'voice_1023_files.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['rel', 'md5', 'size', 'built_from'])
        w.writerows(rows)
    hp = os.path.join(out, 'hook', 'dinput8.dll')
    hmd5 = md5(hp) if os.path.isfile(hp) else 'none'
    open(os.path.join(out, 'voice_1023.ps1'), 'w', encoding='utf-8-sig').write(PS1.replace('__HOOKMD5__', hmd5))
    for mode, name in (('install', 'INSTALL voice 1023.bat'), ('undo', 'UNDO voice 1023.bat')):
        open(os.path.join(out, name), 'w', newline='').write(BAT.replace('%MODE%', mode).replace('\n', '\r\n'))


def maps_of(game):
    return tc.maps_of(game)


def main():
    a = sys.argv[1:]
    opt = lambda n, d=None: (a[a.index(n) + 1] if n in a else d)
    cmd = a[0] if a else 'help'
    game, out = opt('--game', GAME), opt('--out', OUT)
    if cmd == 'bats':
        make_bats(game, out, maps_of(game) if not opt('--maps') else opt('--maps').split(','))
        return
    if cmd not in ('build', 'plan', 'check'):
        print(__doc__); sys.exit(2)
    maps = opt('--maps').split(',') if opt('--maps') else maps_of(game)
    if cmd == 'check':
        bad = 0
        for m in maps:
            od = os.path.join(out, m)
            folder = os.path.join(game, 'KLExpansion', 'Maps', m)
            zp = [f for f in os.listdir(od) if f.lower().endswith('_main.zip')]
            if not zp:
                print('%-8s MISSING' % m); bad += 1; continue
            loc = tc.Loc(os.path.join(od, zp[0]))
            ward = tc.read_wardrobe(os.path.join(folder, 'KLWardrobe.ini'))
            ip = os.path.join(od, 'KLTalk.ini')
            pr = tc.check_text(open(ip, 'rb').read().decode('latin1'), loc, ward, m) if os.path.isfile(ip) else []
            nk = sum(1 for k in loc.d if k.startswith('klvoice/'))
            ns = sum(1 for k, (p, s) in loc.d.items() if k.startswith('klvoice/') and not s)
            with zipfile.ZipFile(os.path.join(od, zp[0])) as zf:
                en = [zf.getinfo(n).file_size for lang, n in kl_loc.members(zf).items() if lang == 'English']
            if en and en[0] > LOC_CAP:
                pr = pr + ['English .LOC %d bytes > %d (LOC_CAP)' % (en[0], LOC_CAP)]
            print('%-8s %s %d KLVoice leaves, %d without sound, %d ini problems, English .LOC %s bytes'
                  % (m, 'OK ' if not pr and not ns else 'BAD', nk, ns, len(pr), en[0] if en else '?'))
            for p in pr[:5]:
                print('    ' + p)
            bad += len(pr) + ns
        print('problems: %d' % bad); sys.exit(1 if bad else 0)
    trees, clips = load_source()
    print('source clips:', {s: len(v) for s, v in clips.items()})
    bad = 0
    for m in maps:
        info, plan = build_map(game, m, out, trees, clips, write=(cmd == 'build'))
        if cmd == 'plan' or m == maps[0]:
            os.makedirs(out, exist_ok=True)
            review_file(os.path.join(out, 'voice_review.tsv'), plan)
        bad += len(info.get('problems') or []) + len(info.get('ini_problems') or []) + sum(info.get('silent', {}).values())
        if cmd == 'plan':
            print(m, info['events'], 'events', info['counts']); break
    print('problems: %d' % bad); sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
