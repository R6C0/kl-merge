"""Dead Men -> Dog Days mini-cutscene script strings  ((Section| Name| ((cmd| ((k| v)...))...))...)"""
import re, os
SECTIONS={'Actor','Player','Lynch','Kane','Trigger','Camera','Options','PIP'}
# Dead Men's picture-in-picture section: kl2's section parser (0x6ec960) knows only Actor/Lynch/Kane/Trigger/Camera/
# Options and int3s on anything else (M03, M06, M07, M11, M11B, M12 crashed at 0x6ecd00). Its section id is -3 (DD:
# Trigger -1, Lynch -2, Camera -4, Kane -5), so dropping it means removing every _dep entry that points at -3.
PIP_ID='-3'
def _drop_pip_deps(x, stats):
    if isinstance(x, list):
        if len(x)==2 and x[0]=='_dep' and isinstance(x[1], list):
            keep=[d for d in x[1] if not (isinstance(d, list) and d and d[0]==PIP_ID)]
            if len(keep)!=len(x[1]): stats['PIP _dep entries dropped']+=len(x[1])-len(keep); x[1]=keep
        for y in x: _drop_pip_deps(y, stats)
def parse(s):
    pos=0
    def p():
        nonlocal pos
        if s[pos]=='(':
            pos+=1; items=[]
            if s[pos]==')': pos+=1; return items
            while True:
                items.append(p())
                if s.startswith('| ',pos): pos+=2; continue
                if s[pos]==')': pos+=1; return items
                raise ValueError('bad at %d'%pos)
        j=pos
        while pos<len(s) and s[pos] not in '|)': pos+=1
        return s[j:pos]
    t=p()
    if pos!=len(s): raise ValueError('trailing')
    return t
def ser(t):
    if isinstance(t,list): return '('+'| '.join(ser(x) for x in t)+')'
    return t
def is_script(s):
    if not s.startswith('((') : return False
    try: t=parse(s)
    except Exception: return False
    return isinstance(t,list) and all(isinstance(x,list) and len(x)==3 and x[0] in SECTIONS for x in t) and len(t)>0
def _params(cmd):  # cmd = [name, [[k,v],...]]
    return cmd[1] if isinstance(cmd[1],list) else []
def _get(ps,k):
    for kv in ps:
        if kv[0]==k: return kv
    return None
def _delay(dep):
    return ['delay',[['delay','0.0'],['delayforever','0'],['randdelay','0.0'],dep or ['_dep',[]]]]
ACT_KEYS=['subt','anim','text','dlgmode','dlgpart','weaponhdl','idle','idlemode','startpos','aimat','aimanim','fltarget','item','coopset','blend','lefthandik','custdeathanim']
# Commands/options Dog Days' script parser handles with Dead Men's parameters (kl2 dispatch 0x6bf6d0; parsers read
# only the keys they know and fall back to defaults on unknown values, checked by disassembly 11 Oct):
#   Options playermode 0x722f90 ('1'); camprofile 0x5fd160; camfade 0x625390 (fadectrl/fadetime/fadedist/coop);
#   setvariant 0x585470 (variantid, gasmask); throwgrenade 0x6ec660 (target required - all DM ones have it -,
#   custanim, height); setfollow 0x809bf0 reads only fmode (Normal/Tight/Loose -> follow distance), DM's 'leader'
#   is ignored. They used to become 'delay' (same index, so _dep tuples hold either way).
# ANP_SCRIPT_RESTORE: comma list of those kept as they are (default all; '' = old downgrade, for one-by-one A/B).
RESTORABLE=('playermode','camprofile','camfade','setvariant','setfollow','throwgrenade')
def _restore():
    v=os.environ.get('ANP_SCRIPT_RESTORE')
    if v is None: return set(RESTORABLE)
    return set(x.strip() for x in v.split(',') if x.strip())
MERC_ACTOR=re.compile(r'Merc_0\d')
SQUAD_EVENTS=('ZMercSquad','ZFusionSquad','ZSquadScript')
def squad_merc_values(ops, names, proxy=True, groups=True):
    """(vals, name_maps, group_renames). vals = {prp node index: set of Dead Men merc values (1..12) among the
    members of the node's squad} for every node that carries a script string (ANP_MERC_BYNAME); name_maps =
    {node: {kept actor name: new name}} and group_renames = {node: new entity name} (groups=True,
    ANP_MERC_GROUPS, see below). The binder (kl2 0x4b64e0 = DM 0x6f6900) matches an
    'Actor| Merc_0N' section to a member of the cutscene's squad (the nearest squad ancestor of the rout node) either
    by merc value N or, failing that, by the member's parent group name. Only the first kind may be renumbered:
    M14 '2MenLeft' scripts name No_Mercenary soldiers in groups 'Merc_01'/'Merc_02' and must keep those names.
    Members as kl2 builds them: ZMercSquad = every soldier with a listed merc value; ZFusionSquad (and DM
    ZProxySquad, which port_level turns into one) = the members of the referenced squads / soldiers below the
    referenced groups; any other squad = the soldiers below it. names: ['ROOT'] + gms entity names (prp order)."""
    par,evs,kids,scr,path,bypath=_scene_tree(ops,names)
    sold={}
    for i,E in evs.items():
        for body in E.get('ZSoldier',[]):
            en=[v for _,op,v in body if op&0x7f==14]
            if len(en)>4 and isinstance(en[4],str) and re.fullmatch(r'Merc_\d\d',en[4]): sold[i]=int(en[4][5:])
            else: sold.setdefault(i,0)
    return _squad_merc_values(ops,names,proxy,groups,par,evs,kids,scr,path,bypath,sold)
def _scene_tree(ops, names):
    """Node tree of a prp op list: (par, evs, kids, scr, path, bypath). par/kids by prp node index, evs = {node:
    {event name: [body ops, ...]}}, scr = nodes with a script string, path = 'A\\B' without ROOT."""
    k=next(i for i,(p,op,v) in enumerate(ops) if op&0x7f==2)
    par={}; evs={}; kids={}; scr=set()
    def take(i):
        d=0; j=i
        while True:
            b=ops[j][1]&0x7f
            if b==2: d+=1
            elif b==0x7e:
                d-=1
                if d==0: return ops[i+1:j], j+1
            j+=1
    pos=k; cnt=[0]; stack=[]
    # iterative preorder walk: node = obj, 04 nev, (0c name, obj)*, 04 nch, children
    def walk(parent):
        nonlocal pos
        idx=cnt[0]; cnt[0]+=1; par[idx]=parent; kids[idx]=[]
        if parent is not None: kids[parent].append(idx)
        _,pos=take(pos)
        nev=ops[pos][2]; pos+=1; E={}
        for _ in range(nev):
            nm=ops[pos][2]; pos+=1
            body,pos=take(pos); E.setdefault(nm,[]).append(body)
            if any(isinstance(v,str) and v.startswith('((') for _,_,v in body): scr.add(idx)
        evs[idx]=E
        return ops[pos][2]
    # explicit stack of (node, children left) to avoid recursion depth limits
    nch=walk(None); pos+=1; stack=[(0,nch)]
    while stack:
        nd,left=stack[-1]
        if left==0: stack.pop(); continue
        stack[-1]=(nd,left-1)
        c=walk(nd); pos+=1; stack.append((cnt[0]-1,c))
    path={}
    for i in range(cnt[0]):
        p=par[i]; nm=names[i] if i<len(names) else '?'
        path[i]=nm if p is None else (path[p]+'\\'+nm if p else nm)
    bypath={v:i for i,v in path.items()}
    return par,evs,kids,scr,path,bypath
def _squad_merc_values(ops,names,proxy,groups,par,evs,kids,scr,path,bypath,sold):
    sq=SQUAD_EVENTS+(('ZProxySquad',) if proxy else ())
    def is_sq(j): return any(e in evs[j] for e in sq)
    def desc(j):
        out=set(); st=list(kids[j])
        while st:
            x=st.pop()
            if x in sold: out.add(x)
            st+=kids[x]
        return out
    memo={}
    def members(j, seen=()):
        if j in memo: return memo[j]
        if j in seen: return set()
        E=evs[j]
        if 'ZMercSquad' in E:
            want={int(v[5:]) for b in E['ZMercSquad'] for _,op,v in b if op&0x7f==14 and isinstance(v,str) and re.fullmatch(r'Merc_\d\d',v)}
            out={s for s,v in sold.items() if v in want}
        elif 'ZFusionSquad' in E or (proxy and 'ZProxySquad' in E):
            out=set()
            for b in E.get('ZFusionSquad',[])+(E.get('ZProxySquad',[]) if proxy else []):
                for _,op,v in b:
                    if op&0x7f==12 and isinstance(v,str):
                        r=v[5:] if v.startswith('ROOT\\') else v
                        t=bypath.get(r)
                        if t is not None: out|=members(t,seen+(j,)) if is_sq(t) else desc(t)
        else: out=desc(j)
        memo[j]=out; return out
    res={}; sqof={}
    for i in scr:
        j=par[i]
        while j is not None and not is_sq(j): j=par[j]
        sqof[i]=j
        res[i]=set() if j is None else {sold[m] for m in members(j) if sold[m]}
    if not groups: return res,{},{}
    # Group-name binds that must keep 'Merc_0N' still pass kl2's digit check first, so in Dog Days they also match
    # any member whose merc value is N - in M14 the buddy (Kane = 1) takes 'Merc_01' meant for '2MenLeft\Merc_01'
    # and the buddy's own section stays unbound. The target groups get a name outside the 'Merc_0' pattern
    # ('Merc_01' -> 'MercG01', same length) and the sections follow, unless something refers to the group by path.
    kept={}
    for i in scr:
        for bl in evs[i].values():
            for body in bl:
                for _,_,v in body:
                    if isinstance(v,str) and v.startswith('((') and is_script(v):
                        for sec in parse(v):
                            if sec[0]=='Actor' and isinstance(sec[1],str) and MERC_ACTOR.fullmatch(sec[1]) and int(sec[1][6]) not in res[i]:
                                kept.setdefault(i,set()).add(sec[1])
    strs=[v for _,_,v in ops if isinstance(v,str) and '\\' in v]
    def referenced(g):
        pat=re.compile(r'(?:^|ROOT\\|\|\s?)'+re.escape(path[g])+r'(?:$|[\\|)])')
        return any(pat.search(v) for v in strs)
    tgt={}
    for i,ks in kept.items():
        if sqof[i] is None: continue
        mem=members(sqof[i])
        for a in ks:
            tgt[(i,a)]={par[m] for m in mem if par[m] and names[par[m]]==a}
    blocked={g for t in tgt.values() for g in t if referenced(g)}
    changed=True
    while changed:
        changed=False
        for t in tgt.values():
            if t&blocked and not t<=blocked: blocked|=t; changed=True
    ren={}; amap={}
    for (i,a),t in tgt.items():
        if t and not t&blocked:
            nn='MercG'+a[5:]
            for g in t: ren[g]=nn
            amap.setdefault(i,{})[a]=nn
    return res,amap,ren
# ---- cutscenes that were already dead in Dead Men (in-game census 11 Oct: cutdiag 'dead +35') ----
# The binder (kl2 0x4b64e0, DM 0x6f6900: the same code) loops members (outer) x Actor sections (inner); the only skip is
# SActorTrack vt slot 13 / DM slot 12 (xor eax,eax), so a section that is already bound is NOT skipped: a member binds
# the FIRST section that matches (merc digit, else parent group name), overwriting an earlier bind. Any section left
# with no actor sets ZMiniCutscene+0x35 (DM +0x39) and the rout never runs it (rout slot 25 0x53e090 / DM 0x6f6d50).
# Both fixes below restore Dead Men content that Dead Men itself never played; each has its own switch.
#
# ANP_DM_SCRIPT_FIXES (default on): sections naming a group that does not exist. (actor, text marker, new name):
# the section 'actor' whose commands speak a line containing 'text marker' is renamed before any other conversion.
#   M14 MercsandDaughterLynch\Script_NearChurch: 'SpanishSoldier' is no group in M14 (DM data rename). Its line is
#   NearChurch_040_Soldier01; Script_CrewRadio04 in the same squad gives Soldier01's line to group '2MenLeft\Merc_01',
#   so it becomes 'Merc_01' (a group-name bind: no member of that squad has merc value 1; ANP_MERC_GROUPS then
#   renames group and section to 'MercG01').
DM_SCRIPT_FIXES=(('SpanishSoldier','M14_NearChurch_040_Soldier01','Merc_01'),)
def fix_dm_scripts(ops, stats):
    """ANP_DM_SCRIPT_FIXES: patch the Dead Men op list in place (script strings only)."""
    if os.environ.get('ANP_DM_SCRIPT_FIXES','1')!='1': return
    for i,(p,op,v) in enumerate(ops):
        if not (isinstance(v,str) and v.startswith('((') and any(f[1] in v for f in DM_SCRIPT_FIXES) and is_script(v)): continue
        t=parse(v); hit=False
        for sec in t:
            for old,mark,new in DM_SCRIPT_FIXES:
                if sec[0]=='Actor' and sec[1]==old and mark in ser(sec[2]):
                    sec[1]=new; hit=True; stats['DM script fix: actor %s -> %s (%s)'%(old,new,mark)]+=1
        if hit: ops[i]=(p,op,ser(t))
# ANP_DUP_ACTOR_GROUPS (default on): two Actor sections with the same group name. M12 AI!Dialogs!FusionSquad_SmallTalk\
# MiniCutScene names 'VEN_AlliedSoldier_01#01' twice, for the soldiers of Squad_SubSquad_Soldier_1 and _2, whose groups
# share that name: both members bind the first section and the second stays empty. The 2nd..c-th matching members'
# groups get unique names ('<name>_ANP2' ...; appended to .buf like ANP_MERC_GROUPS, node indices unchanged) and every
# script whose squad holds a renamed group follows: one section -> the group of the LAST matching member (what the
# binder ends with, so other cutscenes keep their actor), c sections -> the k-th section to the k-th member.
def _member_list(evs, kids, bypath, actors, proxy=True):
    """Ordered squad members as the binder sees them (first occurrence kept): {squad node: [actor node, ...]}."""
    sq=SQUAD_EVENTS+(('ZProxySquad',) if proxy else ())
    def is_sq(j): return any(e in evs[j] for e in sq)
    def desc(j):
        out=[]; st=list(reversed(kids[j]))
        while st:
            x=st.pop()
            if x in actors: out.append(x)
            st+=list(reversed(kids[x]))
        return out
    memo={}
    def members(j, seen=()):
        if j in memo: return memo[j]
        if j in seen: return []
        E=evs[j]
        if 'ZMercSquad' in E:
            want={int(v[5:]) for b in E['ZMercSquad'] for _,op,v in b if op&0x7f==14 and isinstance(v,str) and re.fullmatch(r'Merc_\d\d',v)}
            out=[s for s in sorted(actors) if actors[s] in want]
        elif 'ZFusionSquad' in E or (proxy and 'ZProxySquad' in E):
            out=[]
            for b in E.get('ZFusionSquad',[])+(E.get('ZProxySquad',[]) if proxy else []):
                for _,op,v in b:
                    if op&0x7f==12 and isinstance(v,str):
                        r=v[5:] if v.startswith('ROOT\\') else v
                        t=bypath.get(r)
                        if t is not None: out+=members(t,seen+(j,)) if is_sq(t) else desc(t)
        else: out=desc(j)
        seen_=set(); out=[x for x in out if not (x in seen_ or seen_.add(x))]
        memo[j]=out; return out
    return is_sq, members
def dup_actor_groups(ops, names, stats, proxy=True, taken=()):
    """ANP_DUP_ACTOR_GROUPS. Returns (section_maps, group_renames): section_maps = {script node: {(name, k): new
    name}} (k = occurrence of that name among the script's Actor sections, 0-based), group_renames = {node: new
    entity name}. taken: nodes already renamed by squad_merc_values (left alone)."""
    if os.environ.get('ANP_DUP_ACTOR_GROUPS','1')!='1': return {},{}
    par,evs,kids,scr,path,bypath=_scene_tree(ops,names)
    actors={}
    for i,E in evs.items():
        for body in E.get('ZSoldier',[]):
            en=[v for _,op,v in body if op&0x7f==14]
            actors[i]=int(en[4][5:]) if len(en)>4 and isinstance(en[4],str) and re.fullmatch(r'Merc_\d\d',en[4]) else 0
        if 'ZCivilian' in E: actors.setdefault(i,0)
    is_sq,members=_member_list(evs,kids,bypath,actors,proxy)
    def squad(i):
        j=par[i]
        while j is not None and not is_sq(j): j=par[j]
        return j
    def by_name(nm): return not (len(nm)==7 and nm.startswith('Merc_0'))      # the binder's digit check comes first
    scripts={}
    for i in scr:
        for bl in evs[i].values():
            for body in bl:
                for _,_,v in body:
                    if isinstance(v,str) and v.startswith('((') and is_script(v):
                        scripts.setdefault(i,[]).append([s[1] for s in parse(v) if s[0]=='Actor' and isinstance(s[1],str)])
    strs=[v for _,_,v in ops if isinstance(v,str) and '\\' in v]
    def referenced(g):
        pat=re.compile(r'(?:^|ROOT\\|\|\s?)'+re.escape(path[g])+r'(?:$|[\\|)])')
        return any(pat.search(v) for v in strs)
    used=set(names); ren={}
    for i in sorted(scripts):
        j=squad(i)
        if j is None: continue
        mem=members(j)
        for secs in scripts[i]:
            cnt={}
            for nm in secs:
                if by_name(nm): cnt[nm]=cnt.get(nm,0)+1
            for nm,c in cnt.items():
                if c<2: continue
                grp=[]
                for m in mem:
                    g=par[m]
                    if g and names[g]==nm and g not in grp: grp.append(g)
                if len(grp)<2: continue
                need=grp[1:c]
                if any(g in taken or referenced(g) for g in need):
                    stats['dup actor %s: SKIPPED (group renamed already or referenced by path)'%nm]+=1; continue
                for g in need:
                    if g in ren: continue
                    k=2
                    while '%s_ANP%d'%(nm,k) in used: k+=1
                    ren[g]='%s_ANP%d'%(nm,k); used.add(ren[g])
                    stats['dup actor group renamed %s -> %s (node %d)'%(nm,ren[g],g)]+=1
    if not ren: return {},{}
    old={g:names[g] for g in ren}
    smap={}
    for i,lst in scripts.items():
        j=squad(i)
        if j is None: continue
        mem=members(j)
        for secs in lst:
            for nm in set(secs):
                if not by_name(nm) or nm not in old.values(): continue
                grp=[]
                for m in mem:
                    g=par[m]
                    if g and names[g]==nm and g not in grp: grp.append(g)
                if not any(g in ren for g in grp): continue
                c=secs.count(nm)
                tg=[grp[-1]] if c==1 else grp[:c]
                for k,g in enumerate(tg):
                    if g in ren:
                        smap.setdefault(i,{})[(nm,k)]=ren[g]; stats['dup actor section %s #%d -> %s'%(nm,k,ren[g])]+=1
    return smap,ren
# ANP_BUDDY_KANE (default on): the buddy merc's 'Actor| Merc_0N' section (Dead Men Lynch, Merc_04 in all 16 levels)
# becomes Dog Days' own buddy section '(Kane| Kane| ...)'. kl2's section parser (0x6ec960) gives a Kane section id -5
# and parses its commands with the same dispatcher (0x6bf6d0) into an Actor-class section (0x405f70, vt 0xbcdfe0, at
# ZMiniCutscene+0x30) and into a player-class one (0x570e10, vt 0xbce01c, +0x2c, coop player two); the binder
# (0x4b64e0) sets the Actor-class one to gameMgr+0x4cf0 (the registered buddy) whatever the squad holds, and Start
# (0x8af7d0) puts it in the section list outside coop. So it binds even when the cutscene's squad is empty, which
# kills Dead Men's Merc_0N sections (M01 intro chain: squads fill before Lynch registers as buddy). Section ids
# count Actor sections only, so every _dep (k, c, s) on the old Actor index k becomes (-5, c, s) and (j>k, c, s)
# becomes (j-1, c, s). Commands stay: the Kane section accepts every command an Actor section does (same parser).
KANE_ID='-5'
def _kane_enabled(): return os.environ.get('ANP_BUDDY_KANE','1')=='1'
def _renumber_deps(x, k, stats):
    """_dep tuples: k -> -5, j>k -> j-1 (j, k = Actor section indices)."""
    if isinstance(x, list):
        if len(x)==2 and x[0]=='_dep' and isinstance(x[1], list):
            for d in x[1]:
                if isinstance(d, list) and d and isinstance(d[0], str) and re.fullmatch(r'-?\d+', d[0]):
                    j=int(d[0])
                    if j==k: d[0]=KANE_ID; stats['buddy Kane: _dep -> -5']+=1
                    elif j>k: d[0]=str(j-1); stats['buddy Kane: _dep actor id shifted']+=1
            return
        for y in x: _renumber_deps(y, k, stats)
def _buddy_to_kane(t, stats, buddy, squad_vals):
    """t: parsed script (PIP already dropped). Returns True when the buddy's Actor section became the Kane section."""
    if not buddy or not MERC_ACTOR.fullmatch(buddy): return False
    if squad_vals is not None and int(buddy[6]) not in squad_vals: return False   # group-name bind in Dead Men: keep
    actors=[sec for sec in t if isinstance(sec, list) and sec and sec[0]=='Actor']
    hits=[i for i,sec in enumerate(actors) if sec[1]==buddy]
    if not hits: return False
    if any(isinstance(sec, list) and sec and sec[0]=='Kane' for sec in t):
        stats['buddy Kane: SKIPPED, script already has a Kane section']+=1; return False
    if len(hits)>1:
        stats['buddy Kane: SKIPPED, %d %s sections in one script'%(len(hits),buddy)]+=1; return False
    k=hits[0]; sec=actors[k]
    sec[0]='Kane'; sec[1]='Kane'; stats['buddy Kane: section %s -> Kane'%buddy]+=1
    _renumber_deps(t, k, stats)
    return True
def convert(s, stats, digit=None, squad_vals=None, name_map=None, buddy=None, sec_map=None):
    """digit: {Dead Men merc name: Dog Days EIsMercenary value} for this level (port_level, ANP_MERC_IDS). kl2's
    actor binder (0x4b64e0) binds an 'Actor| Merc_0N' section to the squad member whose merc value is N, and Dog
    Days' values are shifted (Kane 1, Merc_01 2 ...), so the digit is rewritten to the converted soldier's value
    (M01: Lynch Merc_04 -> 'Kane' 1 -> 'Merc_01'). Section order and ids stay, so no _dep changes.
    squad_vals: Dead Men merc values among this script's squad members (squad_merc_values); a section is renamed
    only when N is one of them, otherwise Dead Men binds it by group name and the name is kept, or follows its
    renamed group (name_map, squad_merc_values).
    buddy: Dead Men merc name of the buddy (port_level, 'Merc_04'); with ANP_BUDDY_KANE its section becomes a Kane
    section (_buddy_to_kane) - this one does renumber _dep.
    sec_map: {(actor name, occurrence): new name} from dup_actor_groups (ANP_DUP_ACTOR_GROUPS)."""
    keep=_restore()
    t=parse(s)
    if os.environ.get('ANP_DROP_PIP','1')=='1' and any(isinstance(x,list) and x and x[0]=='PIP' for x in t):
        t=[x for x in t if not (isinstance(x,list) and x and x[0]=='PIP')]; stats['PIP section dropped']+=1
        _drop_pip_deps(t, stats)
    if sec_map:
        occ={}
        for sec in t:
            if isinstance(sec,list) and sec and sec[0]=='Actor' and isinstance(sec[1],str):
                k=occ.get(sec[1],0); occ[sec[1]]=k+1
                nn=sec_map.get((sec[1],k))
                if nn: stats['dup actor section renamed in script']+=1; sec[1]=nn
    if buddy and _kane_enabled(): _buddy_to_kane(t, stats, buddy, squad_vals)
    for sec in t:
        if sec[0]=='Player':
            sec[0]='Lynch'; sec[1]='Lynch' if sec[1]=='Player' else sec[1]; stats['section Player->Lynch']+=1
        if digit and sec[0]=='Actor' and isinstance(sec[1],str) and MERC_ACTOR.fullmatch(sec[1]):
            n=digit.get(sec[1])
            if squad_vals is not None and int(sec[1][6]) not in squad_vals:
                if name_map and sec[1] in name_map:
                    stats['actor %s -> %s (group-name bind, group renamed)'%(sec[1],name_map[sec[1]])]+=1; sec[1]=name_map[sec[1]]
                else: stats['actor %s kept (not a merc of its squad: group-name bind)'%sec[1]]+=1
            elif n is not None and 0<n<=9:
                nn='Merc_0%d'%n
                if nn!=sec[1]: stats['actor %s -> %s'%(sec[1],nn)]+=1; sec[1]=nn
            else: stats['actor %s: no Dog Days digit (%r), kept'%(sec[1],n)]+=1
        cmds=sec[2] if isinstance(sec[2],list) else []
        out=[]
        for cmd in cmds:
            if not (isinstance(cmd,list) and len(cmd)==2 and isinstance(cmd[0],str)): out.append(cmd); continue
            name=cmd[0]; ps=_params(cmd); dep=_get(ps,'_dep')
            if sec[0]=='Options':
                if name=='playermode' and name not in keep: stats['opt playermode dropped']+=1; continue
                if name=='playermode': stats['opt playermode kept']+=1
                out.append(cmd); continue
            if name in RESTORABLE and name in keep:
                out.append(cmd); stats['%s kept'%name]+=1; continue
            if sec[0]=='Camera' and name in ('camprofile','camfade'):
                out.append(_delay(dep)); stats['cam %s->delay'%name]+=1; continue
            if name in ('advact','tell'):
                if name=='tell' and sec[0]=='Lynch':
                    np=[kv for k in ('text','subt') for kv in [_get(ps,k)] if kv] 
                    if not _get(ps,'subt'): np.append(['subt','0'])
                    out.append(['playerspeak',np+[dep or ['_dep',[]]]]); stats['tell->playerspeak']+=1; continue
                np=[]
                for k in ACT_KEYS:
                    kv=_get(ps,k)
                    if kv: np.append(kv)
                    elif k=='subt': np.append(['subt','0'])
                    elif k=='blend': np.append(['blend','1'])
                    elif k=='lefthandik': np.append(['lefthandik','0'])
                out.append(['act',np+[dep or ['_dep',[]]]]); stats['%s->act'%name]+=1; continue
            if name=='cooplocklynch':
                out.append(['lockcoopplayer',[kv for kv in ps if kv[0] in ('coopfullscreen','_dep')]]); stats['cooplock']+=1; continue
            if name=='coopunlocklynch':
                out.append(['unlockcoopplayer',[dep or ['_dep',[]]]]); stats['coopunlock']+=1; continue
            if name in ('setfollow','setvariant','throwgrenade'):
                out.append(_delay(dep)); stats['%s->delay'%name]+=1; continue
            if name=='move' and _get(ps,'ubanim'):
                cmd=[name,[kv for kv in ps if kv[0]!='ubanim']]; stats['move ubanim dropped']+=1
            out.append(cmd)
        if isinstance(sec[2],list): sec[2]=out
        if sec[0]=='Kane' and buddy:
            for cmd in out:
                if isinstance(cmd,list) and cmd and isinstance(cmd[0],str): stats['buddy Kane cmd %s'%cmd[0]]+=1
    return ser(t)
