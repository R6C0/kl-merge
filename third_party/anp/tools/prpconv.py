import sys, os, pickle, collections, struct
sys.path.insert(0, os.path.dirname(__file__))
from pval import split_values, gen
from prp import OPN
from anp_paths import load_schema, schema_missing

ZGROUP=0x100001
def ops_from_key(k):
    return [(0,op,(list(v) if isinstance(v,tuple) else v)) for op,v in k]

SIMPLE_DEFAULT={'b':[(0,6,0)],'i':[(0,9,0)],'f':[(0,10,0.0)],'s':[(0,12,'')],'i8':[(0,7,0)],'i16':[(0,8,0)],'c':[(0,5,0)],
                'A3[f]':[(0,1,3),(0,10,0.0),(0,10,0.0),(0,10,0.0),(0,0x7c,None)], 'A3[i]':[(0,1,3),(0,9,0),(0,9,0),(0,9,0),(0,0x7c,None)],
                'sa':[(0,15,[])]}
def fam(v):
    v=str(v)
    return v.split('_')[0] if '_' in v else v
ITEM_MAP={'eFF2ItemPistolHKUSP':'eFF2ItemHG_M9Beretta','eFF2ItemPistolHKUSPCarry':'eFF2ItemHG_M9Beretta','eFF2ItemPistolHKUSPLight':'eFF2ItemHG_M9Beretta',
 'eFF2ItemPistolHKUSPSilenced':'eFF2ItemHG_M9Beretta_Silenced','eFF2ItemPistolTaurus':'eFF2ItemHG_TaurusJudge','eFF2ItemRifleM4':'eFF2ItemRifle_Type95',
 'eFF2ItemRifleM4Light':'eFF2ItemRifle_Type95','eFF2ItemRifleAK74':'eFF2ItemRifle_AK74','eFF2ItemRifleSG552':'eFF2ItemRifle_Zastavam85',
 'eFF2ItemRifleRugerMini14':'eFF2ItemRifle_Type81','eFF2ItemSMGHKMP5':'eFF2ItemSMG_UMP','eFF2ItemSMGHKMP5Light':'eFF2ItemSMG_UMP',
 'eFF2ItemSMGFNP90':'eFF2ItemSMG_Type05','eFF2ItemSMGSteyrTMP':'eFF2ItemSMG_MAC_10','eFF2ItemShotgunRemington870':'eFF2ItemShotgun_Remington_870',
 'eFF2ItemShotgunSpas12':'eFF2ItemShotgun_Spas_12','eFF2ItemSniperRemington700':'eFF2ItemSn_Rem700','eFF2ItemSniperRemington700Silenced':'eFF2ItemSn_Rem700',
 'eFF2ItemFNMinimiSPW':'eFF2ItemMG_GP_Type88','eFF2ItemFNMinimiSPWHeli':'eFF2ItemMG_MiniMi_SPW_Heli','eFF2ItemGrenadeFrag':'eFF2ItemGrenade_Frag',
 'eFF2ItemGrenadeGas':'eFF2ItemGrenade_Gas','eFF2ItemGrenadeSmoke':'eFF2ItemGrenade_Smoke','eFF2ItemGrenadeIncendiary':'eFF2ItemGrenade_Frag',
 'eFF2ItemGrenadeLauncher':'eFF2ItemGrenadeLauncher','eFF2ItemGrenadeLauncherFlare':'eFF2ItemGrenadeLauncher_Flare','eFF2ItemGrenadeLauncherGas':'eFF2ItemGrenadeLauncher',
 'eFF2ItemRocketLauncher':'eFF2ItemRocketLauncher','eFF2ItemRocketLauncherInaccurate':'eFF2ItemRocketLauncher','eFF2ItemRocketLauncherHind':'eFF2ItemRocketLauncher_Hind',
 'eFF2ItemBombC4':'eFF2ItemNoItem','eFF2ItemClaymore':'eFF2ItemNoItem','eFF2ItemPushblade':'eFF2ItemNoItem','eFF2ItemNotInUse':'eFF2ItemNoItem'}
# ANP_GUNFIT_M4SCAR (default on, with ANP_GUNFIT; tools/gunfit.py): the M4 is held with the FN SCAR's Rifle_Default
# clips. The Type95 (bullpup) clips put the support hand 10 cm behind the M4's foregrip, Rifle_Default 0.8-1.6 cm
# from it (FK of the clips, guns research 11 Oct). HUD icon/ammo follow the FN SCAR item: check in game.
if os.environ.get('ANP_GUNFIT','1')=='1' and os.environ.get('ANP_GUNFIT_M4SCAR','1')=='1':
    ITEM_MAP.update({'eFF2ItemRifleM4':'eFF2ItemRifle_FN_SCAR','eFF2ItemRifleM4Light':'eFF2ItemRifle_FN_SCAR'})
# ANP_HELIFLY_ATTACK (gun / dm / rel6): see Conv.helifly
HELIFLY_ATTACK_MODE=os.environ.get('ANP_HELIFLY_ATTACK','gun').strip().lower()
if HELIFLY_ATTACK_MODE not in ('gun','dm','rel6'): raise SystemExit('ANP_HELIFLY_ATTACK=%s: use gun, dm or rel6'%HELIFLY_ATTACK_MODE)
# ANP_ITEM_EXACT (default on): DD has its own gas launcher (53) and incendiary grenade (58). Mapped onto the plain
# launcher / frag, their InventoryBinding was dropped as a duplicate; a 'fireat ... usesec 1' with the unbound tear-gas
# launcher then gets item type 4 and kl2 0x49f260 jumps past its 4-entry table (call 0xcccccccc; M01/M03/M09B).
if os.environ.get('ANP_ITEM_EXACT','1')=='1':
    ITEM_MAP.update({'eFF2ItemGrenadeLauncherGas':'eFF2ItemGrenadeLauncher_Gas','eFF2ItemGrenadeIncendiary':'eFF2ItemGrenade_Incendiary'})
    # Same crash family (W 11 Oct 20:05, weapon swap -> 0xcccccccc): DM variants mapped onto their base gun's id lost
    # their binding as duplicates, so picking up / swapping to them gave item type 4. Each gets a spare DD id of the
    # same item class (one-/two-handed); only an id another DM item already uses in a level is dropped there.
    ITEM_MAP.update({'eFF2ItemPistolHKUSPCarry':'eFF2ItemHG_SigSauer226','eFF2ItemPistolHKUSPLight':'eFF2ItemHG_SW_MP45',
                     'eFF2ItemSMGHKMP5Light':'eFF2ItemSMG_UMP_SBR','eFF2ItemRifleM4Light':'eFF2ItemRifle_AK47',
                     'eFF2ItemSniperRemington700Silenced':'eFF2ItemRifle_Type88_Scoped',
                     'eFF2ItemRocketLauncherInaccurate':'eFF2ItemRocketLauncher_Hind'})

# ---------------- exact relayout (property schemas read from both exes) ----------------
import json, difflib
_EX=None
LET2TOK={'b':'b','s':'s','f':'f','e':'e','I':'i','i':'C','[f*]':'A*','c':'c','B':'i8','h':'i16','k':'sa'}
def _ex():
    global _EX
    if _EX is None:
        try:
            S={g:load_schema('schemas_%s.json'%g) for g in ('dm','dd')}
        except (OSError, ValueError) as e:
            raise schema_missing(e,'ANP_EXACT')    # only reached with ANP_EXACT=1
        tid={g:{c['tid']:n for n,c in S[g]['classes'].items() if c.get('tid')} for g in S}
        _EX=dict(S=S,tid=tid)
    return _EX
def ex_fields(game, kind, key):
    E=_ex()
    if not E: return None
    S=E['S'][game]
    cls=E['tid'][game].get(key) if kind=='g' else S['controllers'].get(key)
    if not cls or cls not in S['classes']: return None
    out=[]
    for owner,recs in S['classes'][cls]['levels']:
        for r in recs:
            L=S['loaders'].get(r['load'])
            if L is None: return None
            e=r.get('enum')
            out.append((owner,L,e['name'] if e else None,[o[0] for o in e['options']] if e else None))
    return out

EXACT_KEYS={0x2007f9,0x10048d,0x10048e,0x10048c,0x10048a,0x2000d5}   # actors, weapon/ammo/item templates, items, rigid bodies

def lalign(a,b):
    """left-preferring alignment of DM fields a onto DD fields b (Dog Days mostly appends fields at the
    end of a class level): -> [(i,j)] matched pairs.  match same (letter,enum) 0, DD insert 1, DM drop 1.2"""
    n,m=len(a),len(b); INF=10**9
    D=[[INF]*(m+1) for _ in range(n+1)]; D[0][0]=0
    for i in range(n+1):
        for j in range(m+1):
            c=D[i][j]
            if c>=INF: continue
            if i<n and j<m and a[i]==b[j] and c<D[i+1][j+1]: D[i+1][j+1]=c
            if j<m and c+1<D[i][j+1]: D[i][j+1]=c+1
            if i<n and c+1.2<D[i+1][j]: D[i+1][j]=c+1.2
    # backtrack from the end preferring DD inserts at the end (so matches stay left)
    i,j=n,m; pairs=[]
    while i or j:
        if j and D[i][j-1]+1==D[i][j]: j-=1
        elif i and j and a[i-1]==b[j-1] and D[i-1][j-1]==D[i][j]: pairs.append((i-1,j-1)); i-=1; j-=1
        else: i-=1
    return pairs[::-1]

# ZFFActor fields 25/26 (health override pair?): Dog Days uses -1 for 'character default', Dead Men 0
# controllers whose Dead Men enum values must still be replaced by Dog Days' usual value even when the name exists
# in Dog Days: ZMercSquad Merc_xx -> Kane makes Lynch's squad Dog Days' buddy squad (follow, revive) - only with
# ANP_MERC_IDS=0; by default ZMercSquad uses the per-level merc mapping (set_mercs) and the exe enum table;
# ZROOM (0x100021) inside/outside classes drive Dog Days' room audio/ambience, which Dead Men's values break
ENUM_OBSERVED_ONLY={'ZMercSquad',0x100021}
EXACT_FIX={('g',0x2007f9):{25:(0,-1),26:(0,-1)}}

# ---------------- ANP_SMB_FIX (default 1; PLAN A2) ----------------
# 1. Enum supplement. kl-merge's dd_enums.json (pinned, never edited) misses kl2.exe enum tables whose values don't
#    count up from 0/1: EPatrolMoveset (eSneak 3, eWalkNormal 1, ...), EDefendMoveSetMod (eDMS_*, NotSet -1),
#    EPlayerMovementModifier (eMOVEMENT_*), EBoneType (eSEAT_*, bit flags). tools/dd_enums_extra.json holds them (read
#    statically from kl2.exe .data; equal to schemas_dd.json's options, EDefendMoveSetMod to its twin EDefendMoveSet,
#    since schemas_dd.json lacks ZSquadModifierBehaviour); setup_workspace.py installs it into
#    work/ext/schemas. Without them a patrol's DM eSneak was replaced by the field's usual eWalkNormal (M02).
# 2. Family placement. Dog Days rebuilt SquadModifierBehaviour (DM 23 enums + 3, DD 24 enums + 5) and the positional
#    aligner shifted DM eDMS (18) / eSTM (19) onto DD's eBFPM (19) / eCS (20), where enum_field_fix reset them, while
#    DD's own eDMS (17) / eSTM (18) got NotSet. FAMILY_FIX puts the DM value of each listed enum family into the DD
#    field of the same family when Dog Days accepts that value there (seen in DD levels or in the exe's table).
FAMILY_FIX={'SquadModifierBehaviour':('eDMS','eSTM')}
def smb_fix_on():
    return os.environ.get('ANP_SMB_FIX','1')=='1'
def dd_enum_extra():
    """[(type name, [[value, name], ...])] from dd_enums_extra.json: the installed copy in work/ext/schemas, else the
    repo's tools/dd_enums_extra.json (with a warning). [] when ANP_SMB_FIX=0."""
    if not smb_fix_on(): return []
    try:
        d=load_schema('dd_enums_extra.json')
    except OSError:
        p=os.path.join(os.path.dirname(os.path.abspath(__file__)),'dd_enums_extra.json')
        print('warning: dd_enums_extra.json not installed in work/ext/schemas (run tools/setup_workspace.py --enums-only); '
              'using %s' % p, file=sys.stderr)
        with open(p,encoding='utf-8') as f: d=json.load(f)
    return [(n,t['values']) for n,t in d['tables'].items()]
def dd_enum_names():
    """every enum value name kl2.exe knows: kl-merge's pinned dd_enums.json plus, with ANP_SMB_FIX=1, the supplement"""
    names=set(nm for tab in load_schema('dd_enums.json') for _,nm in tab)
    for _,tab in dd_enum_extra(): names.update(nm for _,nm in tab)
    return names

# ---------------- PlayerMonitor (ANP_PLAYERMON, default 1; port_level.py node()) ----------------
# Dead Men ZPlayerMonitor = [EPlayerFilter +0x30, b enabled +0x34, 22 target containers, one per player event]. Its
# dispatcher (DM 0x6b8f80(player, event), cdecl; monitors in gameMgr [0xa8760c]+0xc7c, up to 32) fires container
# <event> once per monitor (per-event flag +0x90[k], DM 0x6b8c90; events 19 and 20 clear their flag first, so they
# repeat). Dog Days ZPlayerMonitor = [EPlayerFilter +0x34, b enabled +0x38, EPlayerMonitorEvent +0x3c, b one-shot +0x40,
# ONE container +0x44, b +0x48 (1 in every stock monitor)]: one event per object; init (slot 13, 0x47b210) or the enable
# message (slot 26, 0x7b77c0) registers it in a global table of 20 (0x8ef000 -> 0x168a690); the dispatcher
# (0x589600(player, event)) fires every registered monitor of that event, and with +0x40 set the monitor disables and
# unregisters itself after firing (0x6a5cf0 -> 0x4614a0). Both games send their targets the same message that enables
# a monitor. So one Dead Men monitor becomes one Dog Days PlayerMonitor event per non-empty container, all on the same
# node (each its own object; the node's enable message reaches all of them), one-shot except Dead Men 19/20.
# Event numbers: matched call site by call site in both exes (DM callers of 0x6b8f80, DD callers of 0x589600):
#   0,1,2 pickups (DM 0x5f8698 / DD 0x60217f, same 3-way switch)        -> 0,1,2
#   3,4 cover stand/crouch (DM ZFFPlayerMovementStandCover 0x60c49a / DD 0x8d9536) -> 3,4
#   5,6 aim in cover, 9,10 blind fire (DM 0x60c2e1.. / DD 0x8d91d5, 0x8d93c8; DM 0x602bb0 switch push 4,0xa,6 = DD
#       0x420760 push 4,0xe,0xa)                                         -> 9,10 and 13,14 (Dog Days inserted 5..8)
#   7,8 aim without cover (DM 0x6350d6 [+0x400] / DD 0x6d96a0 [+0x438]&0x400) -> 11,12
#   11 fire (DM 0x5ee90c after stats 0xc88fc8 / DD 0x8dd876 after 0x1686e60)  -> 15
#   21 (DM 0x628730: heal controller state 5..8 -> event, then state 0xb; also called from ZHealTactic) = DD
#       0x6d45a0 / 0x800f20 (state 5..6 -> 0x1b, then state 0xb)        -> 27 eON_HEALED
#   12,13 grenade throw (DM ZFFPlayer slot 90 region), 14,15,17 ZInventoryWheelInput, 18 ammo (ZFFPlayer), 19
#       ZInventoryDisplay update, 20 grenade thrown (repeatable): by name 16,17 / 18..21 / 22 / 25 / 26, but kl2 never
#       raises 16..22, 25 or 26 (no call site of 0x589600 pushes them; kl2 has no ZInventoryDisplay or
#       ZInventoryWheelInput class at all). Such events are DEAD in Dog Days: by default not written (a registered
#       monitor takes one of the 20 slots for good). M02's give-weapon checks (KaneMonitor_Weapons / ..AltWeapon, list
#       19) are on its exit chain, so 19 gets a live stand-in: 28 eON_MOVEMENT_CONTROLS_USED, one-shot = the weapon
#       filter is checked once, as soon as the player moves after the monitor is switched on (inferred; in-game check).
# ANP_PLAYERMON_MAP="19=28!,12=30" overrides entries (Dead Men index = Dog Days event number or name, '+' joins several,
# '!' forces one-shot, '~' forces repeat); ANP_PLAYERMON_DEAD=keep writes dead events too.
PM_DEAD_DD={16,17,18,19,20,21,22,25,26}
PM_REPEAT_DM={19,20}
# ANP_PLAYERMON_THROW (default 1; 0 = byte-identical to the build before it): Dead Men's grenade-throw lists 12
# (standing), 13 (crouching) and 20 (thrown, repeats) -> Dog Days 30 eTHROW_THROWABLE. kl2 raises 30 at 0x6d0c66, in
# ZFFActionThrowObject's Update (vt 0xbb5224 slot 4 = 0x6d0660: the player throws a picked-up ZThrowable prop), and
# loader\grenade.inc raises 30 itself after each grenade it launches (kl2 has no player grenade throw of its own:
# ZGameplayInput's HoldGrenade setter 0x4aa410 only ever CLEARS player+0xb90 bit 0x40 - DM 0x5ef8a0 sets it - and no
# kl2 code reads the derived 'grenade held' bit +0x818 & 0x800; DM's reader is the throw code in 0x5f4c10). DD's own
# names 16/17/26 (eTHROW_GRENADE_*, eLAST_GRENADE_THROWN) are never raised by kl2 (dead, PM_DEAD_DD).
# Lists of one monitor that land on the same Dog Days event and one-shot flag are merged into one object (targets
# de-duplicated, first list's place): M02 PlayerMonitor_KaneGrenades (node 348) lists 12 and 13 hold the same two
# gate targets, so the first throw sends each target once, and the monitor takes one of kl2's 20 slots, not two.
PM_THROW_DD=30
def pm_throw_on():
    return os.environ.get('ANP_PLAYERMON_THROW','1')=='1'
# ANP_GIVE (default 0; 0 = byte-identical to the build before it): the faithful weapon-giving mode. Dead Men's list 19
# ('inventory changed', ZInventoryDisplay update: M02 KaneMonitor_Weapons / ..AltWeapon re-check their WeaponFilter
# every time Kane's inventory changes) -> Dog Days 18 eSWAP_WEAPON, REPEATING. kl2 never raises 18 itself (dead,
# PM_DEAD_DD), but loader\give.inc raises it after every live give/swap (give.inc event=18), so this one mapping is kept
# out of the dead-event drop. port_level.py then defaults ANP_BUDDY_WEAPONFILTER to 'off', so M02's real WeaponFilters
# ('does Lynch hold the Taurus/Remington') run against the merc slots give.inc fills (kl2 0x8fa1a0, bool 0).
PM_GIVE_DD=18
def give_on():
    return os.environ.get('ANP_GIVE','1')=='1'   # default 1 since 13 Oct: faithful M02 proven end to end
def pm_default_map():
    m={k:[(k,None)] for k in range(5)}
    m.update({k:[(k+4,None)] for k in range(5,22)})
    m[18]=[(22,None)]; m[19]=[(28,True)]; m[20]=[(26,None)]; m[21]=[(27,None)]
    if pm_throw_on():
        m[12]=[(PM_THROW_DD,None)]; m[13]=[(PM_THROW_DD,None)]; m[20]=[(PM_THROW_DD,None)]
    if give_on():
        m[19]=[(PM_GIVE_DD,False)]
    return m
def pm_event_names():
    """Dog Days EPlayerMonitorEvent value -> name (kl2.exe enum table, pinned schemas_dd.json)"""
    for owner,L,en,opts in (ex_fields('dd','e','PlayerMonitor') or []):
        if en=='EPlayerMonitorEvent': return {i:n for i,n in enumerate(opts)}
    raise SystemExit('ANP_PLAYERMON: schemas_dd.json has no EPlayerMonitorEvent table')
def pm_map():
    names=pm_event_names(); byname={v:k for k,v in names.items()}
    m=pm_default_map()
    for part in [x.strip() for x in os.environ.get('ANP_PLAYERMON_MAP','').split(',') if x.strip()]:
        k,_,v=part.partition('=')
        ent=[]
        for t in v.split('+'):
            t=t.strip(); once=None
            if t.endswith('!'): once=True; t=t[:-1]
            elif t.endswith('~'): once=False; t=t[:-1]
            n=int(t) if t.lstrip('-').isdigit() else byname.get(t)
            if n not in names: raise SystemExit('ANP_PLAYERMON_MAP: unknown Dog Days event %r'%t)
            ent.append((n,once))
        m[int(k)]=ent
    return m,names

# ---------------- ZParticleEmitter (0x2000ff): exact relayout ----------------
# Dog Days split the emitter into an object part and a shared data block (reached through obj+0x18) and moved the
# velocity plus one float out of the block. The statistical aligner shifted every field from d3 on by one Dead Men
# field: lifetime d4 got DM e5 (1e-5 on half of M01's emitters -> they switch off at once), velocity became the
# default [150,0,0], cone angles held 0..1 values. Map read from the property records of both exes and checked
# by disassembly (DM spawn/update 0x5059f0, DD 0x64abc0; offsets are record offsets, +4 = real object offset):
#   DM e0 [f3]+14 e1 h+20 e2 [f3]+24          -> DD d0 data+00, d1 +0c, d2 +10
#   DM e3..e6 f +30..+3c                      -> DD d3..d6 data+1c..+28   d3 spawn-interval divisor,
#                                                d4 lifetime (x1024 ms, 0 = forever), d5/d6 cone angles
#   DM e7 velocity [f3] +40                   -> DD d21 direct +1c (data +2c..+37 is a hole now)
#   DM e8 f +4c                               -> DD d7 data+38 speed jitter: |v|*(1-rand*d7)
#   DM e10 f +54                              -> DD d8 data+3c start delay (x -1024 ms; DM 0x504bfd, DD 0x64ac06)
#   DM e9 f +50                               -> DD d22 direct +28 (fld x; fdiv dt; DM 0x505cde, DD 0x64af78)
#   DM e11 s, e12 I, e13 I, e14 b, e15 f      -> DD d9..d13 (d12/d13 burst mode and rate)
#   (new)                                     -> DD d14 f data+54 (0 on 99% of stock DD emitters)
#   DM e16 I (always -1)                      -> DD d20 direct +18 burst count
#   DM e17..e21 b                             -> DD d15..d19
#   DM e22 s (message), e23 b                 -> DD d23, d24
#   DM e24..e27 bits, e28 I, e29 I, e30 e31   -> DD d25..d28, d29, d30, d31, d32; d33 bit new (0); e32 -> d34 template
EMIT_MAP=[0,1,2,3,4,5,6,8,10,11,12,13,14,15,'f0',17,18,19,20,21,16,7,9,22,23,24,25,26,27,28,29,30,31,'b0',32]
EMIT_DM_SIG=['A3[f]','i16','A3[f]','f','f','f','f','A3[f]','f','f','f','s','i','i','b','f','i',
             'b','b','b','b','b','s','b','b','b','b','b','i','i','b','b','s']
class Conv:
    def __init__(s, dbpath):
        db=pickle.load(open(dbpath,'rb'))
        s.db=db
        al=os.path.join(os.path.dirname(dbpath),'dd_arrlen.pkl')
        s.arrlen=pickle.load(open(al,'rb')) if os.path.exists(al) else {}
        en=os.path.join(os.path.dirname(dbpath),'dd_enums.pkl')
        s.enums=pickle.load(open(en,'rb')) if os.path.exists(en) else {}
        s.allenum=set()
        for v in s.enums.values(): s.allenum.update(v)
        s.allenum_obs=set(s.allenum)
        # every value name in Dog Days' own enum tables (read from kl2.exe), not only the ones its levels happen to use
        s.enum_tab=collections.defaultdict(set)
        try:
            for ti,tab in enumerate(load_schema('dd_enums.json')):
                for _,nm in tab: s.enum_tab[nm].add(ti)
            s.allenum_obs=set(s.allenum)
            if os.environ.get('ANP_ENUM_EXE','1')=='1': s.allenum.update(s.enum_tab)
        except (OSError, ValueError) as e:
            # soldier() and enum_field_fix() need these tables whatever ANP_ENUM_EXE says
            if os.environ.get('ANP_ENUM_EXE','1')=='1': raise schema_missing(e,'ANP_ENUM_EXE')
            print('warning: no dd_enums.json (%s): soldier enums fall back to defaults' % e, file=sys.stderr)
        # ANP_SMB_FIX: kl2.exe tables kl-merge's extractor missed (see dd_enum_extra); own table ids from 1000
        s.smb_fix=smb_fix_on()
        for k,(_,tab) in enumerate(dd_enum_extra()):
            for _,nm in tab: s.enum_tab[nm].add(1000+k)
            if os.environ.get('ANP_ENUM_EXE','1')=='1': s.allenum.update(nm for _,nm in tab)
        s.log=collections.Counter(); s.unresolved=collections.Counter()
        # Dog Days EIsMercenary values (No_Mercenary 0, Kane 1, Merc_01 2 ... Merc_12 13), for the merc-id mapping
        s.merc_val={}
        try:
            for tab in load_schema('dd_enums.json'):
                if any(nm=='No_Mercenary' for _,nm in tab) and any(nm=='Kane' for _,nm in tab):
                    s.merc_val={nm:val for val,nm in tab}; break
        except (OSError, ValueError): pass
        s.merc_buddy=None     # set by set_mercs() (port_level, ANP_MERC_IDS); None = old behaviour
    # ---------------- merc ids (ANP_MERC_IDS) ----------------
    # One mapping per level, used for ZSoldier's EIsMercenary, ZMercSquad's four values and the scripts'
    # 'Actor| Merc_0N' digits (scriptconv). Dead Men's buddy merc (Lynch, Merc_04 in all 16 levels) -> 'Kane' (1):
    # kl2 0x615e4c then registers him as gameMgr+0x4cf0, Dog Days' buddy, and every 'Kane' ZMercSquad takes him
    # (0x7ede00/0x8633d0). Other Merc_0N keep their name (Dog Days value N+1, distinct, never Kane); their squads
    # find them through the merc list (AddMerc 0x7e1cb0 -> 0x8ba3e0, matches controller+0x6e8).
    def set_mercs(s, buddy):
        s.merc_buddy=buddy
    def merc(s, v):
        if v==s.merc_buddy: return 'Kane'
        if v in s.merc_val and v!='Kane': return v
        return 'No_Mercenary'
    def merc_digit(s, v):
        return s.merc_val.get(s.merc(v))
    def default_for(s, kind, key, sig, j, tok):
        tab=s.db['geom' if kind=='g' else 'ev'].get(key,{}).get(sig,{}).get(j)
        if tab: return ops_from_key(tab[0][0])
        if tok in SIMPLE_DEFAULT: return list(SIMPLE_DEFAULT[tok])
        if tok.startswith('C'): return [(0,4,0)]
        s.unresolved[(kind,key,tok)]+=1
        return None
    def ddtoks(s, kind, key, sig):
        out=[]
        for j,t in enumerate(sig):
            if t=='e':
                known=s.enums.get((kind,key,j))
                out.append(('e',fam(max(known,key=lambda k:known[k])) if known else None))
            else: out.append(gen(t))
        return out
    def choose_sig(s, kind, key, dmtoks):
        sigs=s.db['sigg' if kind=='g' else 'sige'].get(key)
        if not sigs: return None
        best=None
        for sig,n in sigs.items():
            c,_=s.align(dmtoks,s.ddtoks(kind,key,sig))
            sc=(c,-n)
            if best is None or sc<best[0]: best=(sc,sig)
        return best[1]
    def mcost(s,x,y):
        if x==y: return 0
        if isinstance(x,tuple) and isinstance(y,tuple): return 0.6
        return None
    def align(s, a, b):
        n,m=len(a),len(b); INF=10**9
        D=[[INF]*(m+1) for _ in range(n+1)]; D[0][0]=0
        for i in range(n+1):
            for j in range(m+1):
                if i<n and D[i][j]+1.2<D[i+1][j]: D[i+1][j]=D[i][j]+1.2
                if j<m and D[i][j]+1<D[i][j+1]: D[i][j+1]=D[i][j]+1
                if i<n and j<m:
                    c=s.mcost(a[i],b[j])
                    if c is not None and D[i][j]+c<D[i+1][j+1]: D[i+1][j+1]=D[i][j]+c
        # backtrack, preferring insertion (pushes inserts toward the end of runs)
        i,j=n,m; path=[]
        while i or j:
            if j and D[i][j-1]+1==D[i][j]: path.append(('i',j-1)); j-=1
            elif i and j and s.mcost(a[i-1],b[j-1]) is not None and abs(D[i-1][j-1]+s.mcost(a[i-1],b[j-1])-D[i][j])<1e-9: path.append(('m',i-1,j-1)); i-=1; j-=1
            else: path.append(('d',i-1)); i-=1
        return D[n][m], path[::-1]

    def keep_dm_geom(s, key, props):
        """ANP_KEEP_DM_TYPES (port_level): a Dead Men geom class Dog Days has but no stock scene uses -> exact relayout
        from both exes' schemas. There are no Dog Days level statistics for it, so a Dog Days-only field gets the simple
        zero value; ZPlant's (0x2000fd) float array, its ZCloth force vector (kl2 ZCloth Init 0x552ff0: |v|>0 switches a
        constant force on, Dead Men has none), gets three zeros; any other missing array fails (no default). None = no
        exact schema / unexpected shape."""
        if key==0x2000fd:
            return s.exact('g',key,props,extra_default={'A*':[(0,1,3),(0,10,0.0),(0,10,0.0),(0,10,0.0),(0,0x7c,None)]})
        return s.exact('g',key,props)
    def exact(s, kind, key, props, extra_default=None):
        dm=ex_fields('dm',kind,key); dd=ex_fields('dd',kind,key)
        if not dm or not dd: return None
        vals=split_values(props)
        if len(vals)!=len(dm): s.log[(kind,key,'exact: unit count %d != schema %d'%(len(vals),len(dm)))]+=1; return None
        for (sig,_),f in zip(vals,dm):
            want=LET2TOK.get(f[1])
            if want is None or gen(sig)!=want and not (want=='A*' and sig.startswith('A')) and not (want=='C' and sig.startswith('C')):
                s.log[(kind,key,'exact: dm token %s vs schema %s'%(sig,f[1]))]+=1; return None
        # Dog Days signature from the level database with the same shape -> typical values for new fields
        sigs=s.db['sigg' if kind=='g' else 'sige'].get(key,{})
        ddsig=None
        for sg,n in sorted(sigs.items(),key=lambda x:-x[1]):
            if len(sg)==len(dd) and all(gen(t)==LET2TOK.get(f[1]) or (LET2TOK.get(f[1])=='A*' and t.startswith('A')) for t,f in zip(sg,dd)): ddsig=sg; break
        # align level by level on (letter, enum name)
        out=[]; di=0; mi=0; nmatched=0
        dlev=[]; 
        for f in dd:
            if not dlev or dlev[-1][0]!=f[0]: dlev.append([f[0],[]])
            dlev[-1][1].append(f)
        mlev={}
        k=0
        for f in dm:
            mlev.setdefault(f[0],[]).append((k,f)); k+=1
        j=0
        for owner,fs in dlev:
            src=mlev.get(owner,[])
            a=[(f[1],f[2]) for _,f in src]; b=[(f[1],f[2]) for f in fs]
            mp={dj:src[di_][0] for di_,dj in lalign(a,b)}
            for jj,f in enumerate(fs):
                if jj in mp:
                    v=list(vals[mp[jj]][1]); nmatched+=1
                    if f[3] is not None and v and v[0][1]&0x7f==14 and v[0][2] not in f[3]:
                        nv=ITEM_MAP.get(v[0][2])
                        if nv not in f[3]:
                            d=s.default_for(kind,key,ddsig,j,ddsig[j]) if ddsig else None
                            if d is None: s.log[(kind,key,'exact: enum %s unmapped'%v[0][2])]+=1; return None
                            v=d
                        else: v=[(v[0][0],v[0][1],nv)]
                        s.log[(kind,key,'exact enum fix')]+=1
                    if LET2TOK.get(f[1])=='A*' and ddsig:
                        lens=s.arrlen.get((kind,key,ddsig,j))
                        if lens and len(lens)==1 and v[0][1]&0x7f==1:
                            L=list(lens)[0]; cur=v[0][2]
                            if cur!=L:
                                els=v[1:-1]; fill=els[-1] if els else (0,9,0)
                                fill=(0,fill[1],0 if fill[1]&0x7f!=10 else 0.0)
                                v=[(0,v[0][1],L)]+(els+[fill]*L)[:L]+[v[-1]]
                    out+=v
                else:
                    d=s.default_for(kind,key,ddsig,j,ddsig[j]) if ddsig else None
                    if d is None:
                        tok=LET2TOK.get(f[1])
                        d=list(SIMPLE_DEFAULT[tok]) if tok in SIMPLE_DEFAULT else ([(0,4,0)] if tok=='C' else None)
                        if d is None and extra_default and tok in extra_default: d=list(extra_default[tok])
                        if f[3] and tok=='e': d=[(0,14,f[3][0])]
                    if d is None: s.log[(kind,key,'exact: no default for %s'%f[1])]+=1; return None
                    out+=d
                j+=1
        # value fix-ups where the two games use different sentinels
        fx=EXACT_FIX.get((kind,key))
        if fx:
            vs=split_values(out)
            for idx,(frm,to) in fx.items():
                if idx<len(vs) and len(vs[idx][1])==1 and vs[idx][1][0][2]==frm:
                    p_,op_,_=vs[idx][1][0]; vs[idx]=(vs[idx][0],[(p_,op_,to)]); s.log[(kind,key,'exact fix field %d %r->%r'%(idx,frm,to))]+=1
            out=[o for _,sl in vs for o in sl]
        s.log[(kind,key,'exact relayout (%d/%d matched)'%(nmatched,len(dd)))]+=1
        return out
    def same_enum(s, a, b):
        return bool(s.enum_tab.get(a,set()) & s.enum_tab.get(b,set()))
    def enum_field_fix(s, kind, key, sig, out, dmvals):
        """After a positional alignment, make every enum field hold a value from that field's own enum:
        keep it if it is, else take the Dead Men value that belongs to that enum, else Dog Days' usual value."""
        vs=split_values(out)
        if len(vs)!=len(sig): return out
        dmenums=[v[1][0][2] for v in dmvals if v[0]=='e' and v[1]]
        used=set()
        for j,(tok,ops) in enumerate(vs):
            if tok!='e' or not ops: continue
            known=s.enums.get((kind,key,j))
            if not known: continue
            mode=max(known,key=lambda k:known[k])
            cur=ops[0][2]
            if cur in known or s.same_enum(cur,mode): continue
            if not s.enum_tab.get(mode): continue
            cand=[x for x in dmenums if s.same_enum(x,mode) and x not in used]
            nv=cand[0] if cand else mode
            used.add(nv)
            vs[j]=(tok,[(ops[0][0],ops[0][1],nv)]); s.log[(kind,key,'enum field fix %s->%s'%(cur,nv))]+=1
        return [o for _,sl in vs for o in sl]
    def family_fix(s, kind, key, sig, out, dmvals):
        """ANP_SMB_FIX: for each enum family in FAMILY_FIX[key], put the Dead Men field's value into the Dog Days field
        whose usual value has that family, if Dog Days accepts it there (seen in its levels or in its exe table)."""
        vs=split_values(out)
        if len(vs)!=len(sig): return out
        dm={}
        for t,ops in dmvals:
            if t=='e' and ops: dm.setdefault(fam(ops[0][2]),ops[0][2])
        for j,(tok,ops) in enumerate(vs):
            if tok!='e' or not ops: continue
            known=s.enums.get((kind,key,j))
            if not known: continue
            mode=max(known,key=lambda k:known[k]); F=fam(mode)
            if F not in FAMILY_FIX[key] or F not in dm: continue
            nv=dm[F]; cur=ops[0][2]
            if nv==cur: continue
            if nv not in known and not s.same_enum(nv,mode):
                s.log[(kind,key,'family fix %s: %s not a Dog Days value, %s kept'%(F,nv,cur))]+=1; continue
            vs[j]=(tok,[(ops[0][0],ops[0][1],nv)]); s.log[(kind,key,'family fix field %d %s->%s'%(j,cur,nv))]+=1
        return [o for _,sl in vs for o in sl]
    def soldier(s, ev):
        """ZSoldier (class ZSoldierRout). Dead Men: 4 enums, 9 floats, int, string, enum, bool.
        Dog Days: 4 enums, 14 floats, string, enum, bool, enum, bool. Dog Days inserted four floats after the
        fifth (all 1.0 in every Dog Days level) and split the last distance in two. Mapping from value statistics
        of all Dead Men and Dog Days levels; the floats' names are stripped in both exes."""
        b=[op&0x7f for _,op,_ in ev]
        if b!=[14,14,14,14]+[10]*9+[9,12,14,6]: return None
        F=lambda x:(0,10,float(x)); E=lambda x:(0,14,x)
        v=list(ev)
        out=[]
        for k in range(4):
            x=v[k][2]
            out.append(v[k] if x in s.enum_tab else E({0:'eArmy',1:'eNever',2:'eNever',3:'eRegular'}[k]))
        hp=v[7][2]
        # ANP_SOLDIER_HP=merc (default)|all|off. Dead Men max HP (kaneandlynch 0x722090): int field 13 > 0 -> int; else
        # (50+1.25*h) * 8.5 if merc id != No_Mercenary (enum 0). kl2 0x8fbac0 multiplies by SP record +8
        # (0.5/0.9/1.15/1.3, table 0x8612c0) * field(9+diff), so fields 9..12 = 1/record cancel it. Without it a DM
        # crew merc had 38.7 HP instead of 881.9 (M03B Ryu) and died in 1-2 hits -> DD's instant crew-death fail loop.
        # 'all' changes enemies too: pair it with ANP_WEAPON_ZONE=dm or police take 2x the player hits of Dead Men.
        sc=os.environ.get('ANP_SOLDIER_HP','merc'); ismerc=v[15][2]!='No_Mercenary'
        fac=[1.0]*4; hpo=1e11 if hp<0 else hp
        if hp>=0 and (sc=='all' or (sc=='merc' and ismerc)):
            iv=v[13][2]
            hpo=float(iv) if isinstance(iv,int) and iv>0 else (50.0+1.25*hp)*(8.5 if ismerc else 1.0)
            fac=[1/0.5,1/0.9,1/1.15,1/1.3]
            s.log[('e','ZSoldier','hp %g -> %g (ANP_SOLDIER_HP=%s)'%(hp,hpo,sc))]+=1
        out+=v[4:7]+[(v[7][0],v[7][1],hpo), v[8]]                      # accuracy x3, hitpoints (-1 = can't die), ?
        out+=[F(x) for x in fac]                                        # new in Dog Days (1.0 there): per-difficulty HP factors
        out+=[v[9],v[10],v[11]]
        d=v[12][2]
        out+=[F(d if d>0 else 600000.0)]*2
        # string: Dead Men's speaker name ('Lynch', 'Shelly'...) - dialogue is looked up by it, keep it
        # merc id: Dead Men's own (mapped, see set_mercs) when ANP_MERC_IDS is on, else none
        mv=s.merc(v[15][2]) if s.merc_buddy is not None else 'No_Mercenary'
        if mv!='No_Mercenary': s.log[('e','ZSoldier','merc %s -> %s'%(v[15][2],mv))]+=1
        out+=[v[14],E(mv),v[16],E('eSR_AllTypes'),(0,6,1)]
        s.log[('e','ZSoldier','manual relayout')]+=1
        return out
    def emitter(s, props):
        """ZParticleEmitter DM -> DD by EMIT_MAP (see above). None if the DM values don't have the known shape."""
        vals=split_values(props)
        if len(vals)!=7+len(EMIT_DM_SIG): return None
        if ['A3[f]' if t.startswith('A') else t for t,_ in vals[7:]]!=EMIT_DM_SIG: return None
        if any(len(o)!=5 for t,o in vals[7:] if t.startswith('A')): return None
        e=[ops for _,ops in vals[7:]]
        out=[]
        for _,ops in vals[:5]: out+=ops
        out+=[(0,6,0)]                                   # ZGEOM: Dog Days' extra bool after the 5th value
        for _,ops in vals[5:7]: out+=ops                 # ZSTDOBJ
        for m in EMIT_MAP:
            if m=='f0': out+=[(0,10,0.0)]
            elif m=='b0': out+=[(0,6,0)]
            else: out+=list(e[m])
        # sanity counters (both should stay 0): an instant-off lifetime, a zero spawn-interval divisor
        d4=e[4][0][2]; d3=e[3][0][2]
        if isinstance(d4,float) and 0<d4<1e-3: s.log[('g',0x2000ff,'emitter check: lifetime d4 in (0,1e-3)')]+=1
        if d3==0: s.log[('g',0x2000ff,'emitter check: d3 == 0')]+=1
        return out
    def weapon_flash(s, dm_props, out):
        """ZItemTemplateWeapon muzzle flash. Dead Men: one path (value 28, a string naming a ZAllocMany
        WeaponFlash_*_01). Dog Days: a container of such paths (value 32; stock counts 0/4/5/8). The exact relayout
        can't match a string to a container and filled in Dog Days' multiplayer defaults, which don't exist in a
        port. ANP_WEAPON_FLASH_REPEAT=n repeats the path n times (fallback if a count of 1 misbehaves in game)."""
        dv=split_values(dm_props); ov=split_values(out)
        if len(dv)<29 or dv[28][0]!='s' or len(ov)<33 or not ov[32][0].startswith('C'): return None
        path=dv[28][1][0][2]
        cp,cop,_=ov[32][1][0]
        sop=next((op for _,op,_ in ov[32][1][1:]),12)
        try: rpt=max(1,int(os.environ.get('ANP_WEAPON_FLASH_REPEAT','1')))
        except ValueError: rpt=1
        n=rpt if path else 0
        ov[32]=(ov[32][0],[(cp,cop,n)]+[(0,sop,path)]*n)
        return [o for _,sl in ov for o in sl]
    def crosshair_one(s, out):
        """ZFFItemTemplateWeapon (0x10048d) crosshair fields for Dead Men's whole-crosshair art (ANP_DM_CROSSHAIR_ONE,
        values and the kl2 analysis in dmhud.xhair_props). Dog Days fields 60 B +0x220 copies, 61 B +0x221 start angle,
        63 f +0x228 spread clamp max, 64 f +0x22c spread push-out gain; Dead Men has none of them (its ZCrossHairDisplay
        draws one sprite), so the exact relayout filled Dog Days' level defaults (4, 0, 1.1, 1.6)."""
        import dmhud
        P = dmhud.xhair_props()
        if P is None: return None
        ov = split_values(out)
        want = {60: ('i8', P['n']), 61: ('i8', P['angle']), 63: ('f', P['max']), 64: ('f', P['gain'])}
        if len(ov) != 100 or any(ov[i][0] != t or len(ov[i][1]) != 1 for i, (t, _) in want.items()): return None
        for i, (_, v) in want.items():
            p_, op_, _ = ov[i][1][0]; ov[i] = (ov[i][0], [(p_, op_, v)])
        return [o for _, sl in ov for o in sl]
    def player_monitor(s, props):
        """Dead Men PlayerMonitor -> [Dog Days PlayerMonitor props, ...] (one per non-empty container; see PM_DEAD_DD
        above), [] when it has no targets, None when the Dead Men props don't have the known shape"""
        if not hasattr(s,'_pm'): s._pm=pm_map()
        m,names=s._pm
        k_=[op&0x7f for _,op,_ in props]
        if len(k_)<2 or k_[0]!=14 or k_[1]!=6: return None
        conts=[]; j=2
        while j<len(props):
            if k_[j]!=4: return None
            n=props[j][2]
            items=props[j+1:j+1+n]
            if len(items)!=n or any(op&0x7f!=12 for _,op,_ in items): return None
            conts.append(items); j+=1+n
        if len(conts)!=22: return None
        keep_dead=os.environ.get('ANP_PLAYERMON_DEAD','drop')=='keep'
        merge=pm_throw_on()          # ANP_PLAYERMON_THROW: same (event, one-shot) lists -> one object (see PM_THROW_DD)
        give=give_on()               # ANP_GIVE: list 19 -> 18 is live (give.inc raises it), see PM_GIVE_DD
        out=[]; slot={}
        for k,items in enumerate(conts):
            if not items: continue
            for ev,once in m.get(k,[]):
                if give and k==19 and ev==PM_GIVE_DD:
                    s.log[('e','PlayerMonitor','list 19 -> %s (ANP_GIVE: raised by loader give.inc)'%names[ev])]+=1
                elif ev in PM_DEAD_DD and not keep_dead:
                    s.log[('e','PlayerMonitor','list %d -> %s: never raised by kl2, dropped'%(k,names[ev]))]+=1; continue
                if once is None: once=k not in PM_REPEAT_DM
                if merge and (ev,once) in slot:
                    i_,tg_=slot[(ev,once)]
                    new_=[it for it in items if it[2] not in tg_]
                    tg_.update(it[2] for it in new_)
                    o_=out[i_]; n_=o_[4][2]+len(new_)
                    out[i_]=o_[:4]+[(0,4,n_)]+o_[5:5+o_[4][2]]+list(new_)+o_[5+o_[4][2]:]
                    s.log[('e','PlayerMonitor','list %d -> %s%s: merged into the same event (%d new target(s))'%(k,names[ev],'' if once else ' (repeats)',len(new_)))]+=1
                    continue
                if merge: slot[(ev,once)]=(len(out),set(it[2] for it in items))
                out.append([props[0],props[1],(0,14,names[ev]),(0,6,1 if once else 0),(0,4,len(items))]+list(items)+[(0,6,1)])
                s.log[('e','PlayerMonitor','list %d -> %s%s'%(k,names[ev],'' if once else ' (repeats)'))]+=1
        if not out: s.log[('e','PlayerMonitor','no live list: event dropped')]+=1
        return out
    def barrel_effects(s, dmvals, out):
        """BarrelEffects event. Dead Men 'C f f f f f b s I', Dog Days 'f f f f f f b s I C f f': the aligner dropped
        Dead Men's leading container and filled Dog Days' with an F01 default path. Put Dead Men's container back."""
        ov=split_values(out)
        if not dmvals or not dmvals[0][0].startswith('C') or len(ov)<10 or not ov[9][0].startswith('C'): return None
        ov[9]=(dmvals[0][0],list(dmvals[0][1]))
        return [o for _,sl in ov for o in sl]
    def weapon_damage(s, key, dm_props, out):
        """ANP_WEAPON_DMG (default 1): weapon (0x10048d) / ammo (0x10048e) damage fields by meaning, not position.
        Dead Men kaneandlynch 0x51d820: dmg = lerp(ammo near +0x7c (DM f15) -> far +0x80 (f16)) over gun +0xcc (DM f19)
        .. +0xd0 (f20), x gun +0xd4 (f21); +0xd8 (f22) hit reaction, +0xdc (f23) rate of fire.
        Dog Days kl2 0x46ef60: 4 ammo damages +0x84..+0x90 (DD f17..20) over 4 gun ranges +0xd4..+0xe0 (f21..24),
        x gun +0xe4 (f25) [x +0x13c (f37) for NPC shooters]; f26 hit reaction, f27 rate of fire.
        The left alignment put DM's rate of fire (250..850) into f25, so every bullet did thousands of damage
        (one hit killed the 500 HP player). Ranges (R0,R0,R1,R1) and damages (N,N,F,F) reproduce DM's curve exactly
        in kl2's piecewise lerp (the zero-width band is never entered). ANP_WEAPON_NPCDMG=<x>: f37 (default: keep
        the exact relayout's Dog Days value)."""
        dv=split_values(dm_props); ov=split_values(out)
        def one(v): return len(v[1])==1 and v[0]=='f'
        def put(i,src): p_,op_,_=ov[i][1][0]; ov[i]=(ov[i][0],[(p_,op_,src[1][0][2])])
        if key==0x10048d:
            if len(dv)!=42 or len(ov)!=100 or not all(one(dv[i]) for i in range(17,24)) or not all(one(ov[i]) for i in range(19,28)) or not one(ov[37]): return None
            for i,j in ((19,17),(20,18),(21,19),(22,19),(23,20),(24,20),(25,21),(26,22),(27,23)): put(i,dv[j])
            x=os.environ.get('ANP_WEAPON_NPCDMG','')
            if x:
                p_,op_,_=ov[37][1][0]; ov[37]=(ov[37][0],[(p_,op_,float(x))])
        else:
            if len(dv)!=24 or len(ov)!=31 or not all(one(dv[i]) for i in (15,16)) or not all(one(ov[i]) for i in range(17,21)): return None
            for i,j in ((17,15),(18,15),(19,16),(20,16)): put(i,dv[j])
        return [o for _,sl in ov for o in sl]
    EXPLODE_DM_SIG=['f','f','f','f','b','s','s','f','b','i','i','f','b','b','b']
    EXPLODE_DD_SIG=['f','f','f','f','f','f','b','s','s','f','b','i','i','f','b','b','b','b']
    def explode(s, dmvals, out):
        """ANP_EXPLODE_FIX (default 1): CExplode floats by meaning, not position.
        DM kaneandlynch 0x69d400/0x69c180: f0 outer radius, f1 inner radius, f2 tinnitus radius, f3 damage.
        DD kl2 0x60b230/0x8ec590: f0 outer, f1 inner, f2 docu-cam OnExplosion range (new; <=0 -> 1000),
        f3 tinnitus radius, f4 damage, f5 physics-wave multiplier (new; 1.0 in every DD level, 0x534c8c).
        The aligner appended the new floats, so DM damage became the tinnitus radius and every explosion
        did 1000 damage. Tail fields (DM 4..14 -> DD 6..16) are already right. ANP_EXPLODE_CAM=<x>: f2
        (default 200, DD's value on its own copies of the DM grenade/RPG templates)."""
        ov=split_values(out)
        if [t for t,_ in dmvals]!=s.EXPLODE_DM_SIG or [t for t,_ in ov]!=s.EXPLODE_DD_SIG: return None
        if any(len(sl)!=1 for _,sl in dmvals[:4]+ov[:6]): return None
        cam=float(os.environ.get('ANP_EXPLODE_CAM','200'))
        src={0:dmvals[0][1][0][2],1:dmvals[1][1][0][2],2:cam,3:dmvals[2][1][0][2],4:dmvals[3][1][0][2],5:1.0}
        for i,x in src.items():
            p_,op_,_=ov[i][1][0]; ov[i]=(ov[i][0],[(p_,op_,float(x))])
        return [o for _,sl in ov for o in sl]
    HELIFLY_DM_SIG=['s','f','f','b','b','b','e','C','C','b']
    HELIFLY_DD_SIG=['s','f','f','e','e','b','e','e','C','b','b','b','b','s','C','b']
    HELIFLY_ATTACK={'NO_ATTACK':'NO_ATTACK','FRONT_GUN':'GUN_ATTACK','LAUNCHER':'LAUNCHER_ATTACK'}
    # ANP_HELIFLY_ATTACK=gun (default): Dead Men's gun runs only; a LAUNCHER run becomes NO_ATTACK until rocket runs are
    # tested in game (stock Dog Days never uses LAUNCHER_ATTACK on a HeliFly: 116 NO_ATTACK, 49 GUN_ATTACK)
    HELIFLY_ATTACK_GUN={'NO_ATTACK':'NO_ATTACK','FRONT_GUN':'GUN_ATTACK','LAUNCHER':'NO_ATTACK'}
    def helifly(s, dmvals, out, sig):
        """ANP_HELIFLY (default 1): HeliFlyBehaviourRout fields by meaning, not position (the aligner, cost 10.4, lost
        the crash sites, turned FRONT_GUN into NO_ATTACK and shifted Dead Men's bools into Dog Days-only ones).
        Property tables (GetProperties slot 11 -> DM 0xa57be8, kl2 0xd076c4; record member offset, object = +4):
          DM  0 s target +0x3c, 1 f +0x40, 2 f +0x44, 3 b +0x48, 4 b +0x49, 5 b +0x4a, 6 e EHeliAttackMode +0x4c,
              7 C +0x50, 8 C +0x38, 9 b +0x36
          DD  0 s +0x48, 1 f +0x4c, 2 f +0x50, 3 e EHeliFacingMode +0x54, 4 e EHeliFacingMode +0x58, 5 b +0x5c,
              6 e EHeliAttackMode +0x60, 7 e EHeliAttackWhen +0x64, 8 C +0x68, 9..12 b +0x6c..+0x6f, 13 s +0x70,
              14 C +0x44, 15 b +0x42
        Same code reads them (DM rout 0x6f2500 / message handler 0x6ecee0, kl2 0x815aa0 / 0x4ebed0):
          * 9 -> 15 'start once': handler skips the start when it is set and the rout already ran (DM +0x36/+0x34, kl2
            +0x42/+0x40), same logic; 8 -> 14: the handler walks that container (DM +0x38, kl2 +0x44): the relays /
            next routs (data: GeomDeactivator, next rout, Timer / Relay_*, next rout, SquadModifier).
          * 7 -> 8 crash sites: unless 5 is set, the rout calls vt+0x14 on it (DM 0x6f26a2..b4, kl2 0x815c87..9c) and
            hands it to the flight behaviour (DM beh+0x40, kl2 ctor 0x469910 beh+0x48); 5 -> 5 is that gate (DM beh+0x3c,
            kl2 beh+0x42). Data: DM 'CrashSite#nn' under the rout, stock L10 'Helicopter_CrashSite#01'.
          * 0, 1, 2: target string (resolved to the rout's object, DM +0x58 / kl2 +0x78) and the two floats to the
            behaviour (DM beh+0x2c/+0x30, kl2 beh+0x28/+0x2c) in the same order.
          * 6: EHeliAttackMode by number (both exes' enum tables: DM NO_ATTACK 0, FRONT_GUN 1, LAUNCHER 2; kl2 NO_ATTACK
            0, GUN_ATTACK 1, LAUNCHER_ATTACK 2) -> behaviour (DM beh+0x34, kl2 beh+0x30).
        Not mapped: DM 3/4 (bools, behaviour +0x38/+0x39) have no proven counterpart; Dog Days' 3/4 are facing enums
        (behaviour +0x38/+0x3c; FACE_TARGET on an attack run, see the end). They, DD 7 and the Dog Days-only 9..13 get
        Dog Days' usual level values (default_for
        on the chosen signature; rel6 had the same facing / when values there, its 9..12 held shifted Dead Men bools)."""
        ov=split_values(out)
        def C_(t): return t.startswith('C')
        def shape(vs,want): return len(vs)==len(want) and all((C_(t) if w=='C' else t==w) and len(sl)>=1 for (t,sl),w in zip(vs,want))
        if not shape(dmvals,s.HELIFLY_DM_SIG) or not shape(ov,s.HELIFLY_DD_SIG) or sig is None or len(sig)!=16: return None
        att=dmvals[6][1][0][2]
        if att not in s.HELIFLY_ATTACK: return None
        for j in (3,4,7,9,10,11,12,13):
            d=s.default_for('e','HeliFlyBehaviourRout',sig,j,sig[j])
            if d is None: return None
            ov[j]=(ov[j][0],d)
        for i_dd,i_dm in ((0,0),(1,1),(2,2),(5,5),(8,7),(14,8),(15,9)): ov[i_dd]=(dmvals[i_dm][0],list(dmvals[i_dm][1]))
        # ANP_HELIFLY_ATTACK: gun (default) = Dead Men's attack mode with LAUNCHER -> NO_ATTACK (HELIFLY_ATTACK_GUN);
        # dm = Dead Men's attack mode as it is (rel6's aligner had turned every FRONT_GUN into NO_ATTACK, so no converted
        # chopper ever fired: M01 12, M03B 1, M08 5, M11 8, M11B 6 gun runs, M11B 4 rocket runs come back); rel6 = keep
        # the aligner's value (a balance fallback)
        mode=HELIFLY_ATTACK_MODE
        if mode!='rel6':
            p_,op_,_=ov[6][1][0]; ov[6]=(ov[6][0],[(p_,op_,(s.HELIFLY_ATTACK_GUN if mode=='gun' else s.HELIFLY_ATTACK)[att])])
        # an attacking chopper faces its target: stock Dog Days GUN_ATTACK HeliFlys have FACE_TARGET in field 3 (48 of
        # 49) and 4 (48 of 49; both: 47), while Dog Days' usual level value (default_for above) is FACE_SPLINE /
        # FACE_TARGET_90DEG_CW (the NO_ATTACK fly-bys). Fields 9..12 are left at default_for: kl2 passes them to the
        # flight behaviour (rout 0x815cb7..0x815cc9 -> ctor 0x469910 -> ZHeliFlyBehaviour +0x43..+0x46) but no reader
        # of those bytes was found, so their meaning is unproven (stock: 11 and 12 are 1 on most GUN_ATTACK flys)
        if ov[6][1][0][2]!='NO_ATTACK':
            for j in (3,4):
                p_,op_,_=ov[j][1][0]; ov[j]=(ov[j][0],[(p_,op_,'FACE_TARGET')])
            s.log[('e','HeliFlyBehaviourRout','helifly attack: facing FACE_TARGET')]+=1
        return [o for _,sl in ov for o in sl]
    def convert(s, kind, key, props, override=None):
        if kind=='g' and key==0x2000ff and os.environ.get('ANP_EMITTER_EXACT','1')=='1':
            r=s.emitter(props)
            if r is not None: s.log[(kind,key,'emitter exact relayout')]+=1; return r
            s.log[(kind,key,'emitter: unknown DM shape, aligner used')]+=1
        merc_sq=kind=='e' and key=='ZMercSquad' and s.merc_buddy is not None
        if merc_sq:
            props=[(p,op,s.merc(v)) if op&0x7f==14 and isinstance(v,str) and (v=='No_Mercenary' or v.startswith('Merc_')) else (p,op,v) for p,op,v in props]
            s.log[(kind,key,'merc values mapped')]+=1
        if kind=='e' and key=='ZSoldier' and os.environ.get('ANP_SOLDIER','1')=='1':
            r=s.soldier(props)
            if r is not None: return r
        if os.environ.get('ANP_EXACT','1')=='1' and key in EXACT_KEYS:
            r=s.exact(kind,key,props)
            if r is not None and kind=='g' and key==0x10048d and os.environ.get('ANP_WEAPON_FLASH','1')=='1':
                r2=s.weapon_flash(props,r)
                if r2 is not None: r=r2; s.log[(kind,key,'weapon flash path kept')]+=1
                else: s.log[(kind,key,'weapon flash: unknown shape, default kept')]+=1
            if r is not None and kind=='g' and key==0x10048d:
                r3=s.crosshair_one(r)
                if r3 is not None: r=r3; s.log[(kind,key,'crosshair one (ANP_DM_CROSSHAIR_ONE %s)'%os.environ.get('ANP_DM_CROSSHAIR_ONE','1'))]+=1
                elif __import__('dmhud').xhair_props() is not None: s.log[(kind,key,'crosshair one: unknown shape, Dog Days defaults kept')]+=1
            if r is not None and kind=='g' and key in (0x10048d,0x10048e) and os.environ.get('ANP_WEAPON_DMG','1')=='1':
                r4=s.weapon_damage(key,props,r)
                if r4 is not None: r=r4; s.log[(kind,key,'weapon damage fields by meaning (ANP_WEAPON_DMG)')]+=1
                else: s.log[(kind,key,'weapon damage: unknown shape, positional fields kept')]+=1
            if r is not None: return r
        vals=split_values(props)
        if kind=='g':
            # base ZGEOM: DD inserted a Bool after the 5th value
            vals=vals[:5]+[('b',[(0,6,0)])]+vals[5:]
        dmt=[('e',fam(v[1][0][2])) if v[0]=='e' else gen(v[0]) for v in vals]
        sig=s.choose_sig(kind,key,dmt)
        if sig is None: return None
        ddt=s.ddtoks(kind,key,sig)
        cost,path=s.align(dmt,ddt)
        okenum=s.allenum_obs if key in ENUM_OBSERVED_ONLY and not merc_sq else s.allenum
        if cost==0 and all(st[0]=='m' for st in path) and not any(t=='A*' for t in ddt) and not any(v[0]=='e' and v[1][0][2] not in okenum for v in vals):
            s.log[(kind,key,'same')]+=1
            return [o for _,sl in vals for o in sl]
        out=[]
        for st in path:
            if st[0]=='m':
                v=vals[st[1]][1]
                if ddt[st[2]]=='A*':
                    lens=s.arrlen.get((kind,key,sig,st[2]))
                    if lens and len(lens)==1:
                        L=list(lens)[0]; cur=v[0][2]
                        if cur!=L:
                            els=v[1:-1]
                            fill=els[-1] if els else (0,9,0)
                            fill=(0,fill[1],0 if fill[1]&0x7f!=10 else 0.0)
                            els=(els+[fill]*L)[:L]
                            v=[(0,v[0][1],L)]+els+[v[-1]]
                            s.log[(kind,key,'array len %d->%d'%(cur,L))]+=1
                if isinstance(ddt[st[2]],tuple):
                    val=v[0][2]
                    if val not in okenum:
                        known=s.enums.get((kind,key,st[2]),{})
                        mode=max(known,key=lambda k:known[k]) if known else None
                        nv=ITEM_MAP.get(val, mode)
                        if nv is None: return None
                        s.log[(kind,key,'enum %s->%s'%(val,nv))]+=1
                        v=[(v[0][0],v[0][1],nv)]
                out+=v
            elif st[0]=='i':
                d=s.default_for(kind,key,sig,st[1],sig[st[1]])
                if d is None: return None
                out+=d
            else: pass
        s.log[(kind,key,'aligned cost %.1f'%cost)]+=1
        if os.environ.get('ANP_ENUM_FIX','1')=='1': out=s.enum_field_fix(kind,key,sig,out,vals)
        if s.smb_fix and kind=='e' and key in FAMILY_FIX: out=s.family_fix(kind,key,sig,out,vals)
        if kind=='e' and key=='BarrelEffects' and os.environ.get('ANP_BARREL_FX','1')=='1':
            r2=s.barrel_effects(vals,out)
            if r2 is not None: out=r2; s.log[(kind,key,'barrel effects container kept')]+=1
        if kind=='e' and key=='Explode' and os.environ.get('ANP_EXPLODE_FIX','1')=='1':
            r2=s.explode(vals,out)
            if r2 is not None: out=r2; s.log[(kind,key,'explode fields by meaning (ANP_EXPLODE_FIX)')]+=1
            else: s.log[(kind,key,'explode: unknown shape, positional fields kept')]+=1
        if kind=='e' and key=='HeliFlyBehaviourRout' and os.environ.get('ANP_HELIFLY','1')=='1':
            r2=s.helifly(vals,out,sig)
            if r2 is not None: out=r2; s.log[(kind,key,'helifly fields by meaning (ANP_HELIFLY)')]+=1
            else: s.log[(kind,key,'helifly: unknown shape, positional fields kept')]+=1
        return out
