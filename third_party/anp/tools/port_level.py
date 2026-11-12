# Port a Dead Men level into Dog Days format.
import sys, os, struct, zlib, pickle, collections, shutil, json
sys.path.insert(0, os.path.dirname(__file__))
from zipraw import read_zip, write_zip, read_entry, entry_from_bytes
from gms import load_gms
from prp import PRP
from prpwrite import write_prp
from prpconv import Conv
from pval import split_values
from matconv import convert_mat_dm_to_dd
from texconv import convert_tex_dm_to_dd

# Game folders and the work folder (extracted data, caches, kl-merge checkout) - override with env vars (anp_paths)
from anp_paths import WORK, game_dir, DD_FOLDER, DM_FOLDER
DM_GAME=game_dir('ANP_DM_GAME',DM_FOLDER)
DD_GAME=game_dir('ANP_DD_GAME',DD_FOLDER)
DM_ROOT=os.path.join(DM_GAME,'Scenes','Locations')
DD_ROOT=os.path.join(DD_GAME,'Scenes','Locations')
# the level is written to <OUT_ROOT>/<ID>/ : the Dog Days Locations folder (= installed) unless ANP_OUT names another
OUT_ROOT=os.environ.get('ANP_OUT') or DD_ROOT
W=WORK
ZGROUP=0x100001
DD_TYPES={int(x,16) for x in open(W+'/dd_types.txt').read().split()}
# ANP_KEEP_DM_TYPES (default empty = the out_rel6 output byte for byte; work\neutral\PLAN.md E1): Dead Men geom types
# that are NOT neutralised although no stock Dog Days scene instantiates them (so they are missing from dd_types.txt).
# kl2.exe registers every one of these with Dead Men's type id and pool slot and (near) the same property schema
# (work\neutral\INVENTORY.md 1), so such an entity keeps its Dead Men type and prim, its h4 class-stat / h9 dynamic-pool
# rows stay, and its properties go through the exact relayout of both exes' schemas (prpconv Conv.keep_dm_geom; Dog
# Days-only fields get Dog Days' usual / zero values). Node order is unchanged: the rel6 stand-in sits in the same pool
# slot (ANP_NEUTRAL_SLOT; tools\ovlcheck.py still checks every build). Their events then follow the normal rules (the
# 'needs DM vehicle/neutralised owner' drop no longer applies to an owner that is not neutralised). Value: comma list
# of hex type ids and/or these groups (each needs its own in-game test before it becomes a default: the DD code of
# these classes is unexercised by stock content, which is how ZAppendage's regression stayed hidden):
#   mg 0x2000d7 ZHavokMountedWeapon (+ its MountedWeapon event is kept when its owner is a kept 0x2000d7)
#   crowd 0x200491/0x200492/0x200495/0x2004b3/0x2004b6/0x2004b7 ZHFlow*   rope 0x200499 ZRopeLnkObj (see ANP_ROPES)
#   plant 0x2000fd ZPlant (live cloth; the inserted ZCloth force vector gets (0,0,0))   rain 0x2000e2/0x2000e8
#   ik 0x200027 ZIKLNKOBJ   env 0x20010f ZEnvSampler   car 0x2000d4/0x1004b4 (plumbing only: every vehicle rout and
#   VEHICLE_ONLY rule is unchanged; PLAN item 12 needs rout layouts first)
KEEP_DM_GROUPS={'mg':(0x2000d7,),'crowd':(0x200491,0x200492,0x200495,0x2004b3,0x2004b6,0x2004b7),'rope':(0x200499,),
                'plant':(0x2000fd,),'rain':(0x2000e2,0x2000e8),'ik':(0x200027,),'env':(0x20010f,),'car':(0x2000d4,0x1004b4)}
def keep_dm_types(spec):
    """ANP_KEEP_DM_TYPES value -> set of Dead Men type ids (groups and/or hex ids; unknown words fail the build)"""
    r=set()
    for w in [x.strip().lower() for x in spec.replace(';',',').split(',') if x.strip()]:
        if w in KEEP_DM_GROUPS: r.update(KEEP_DM_GROUPS[w]); continue
        try: r.add(int(w,16))
        except ValueError: raise SystemExit('ANP_KEEP_DM_TYPES: %r is neither a group (%s) nor a hex type id'%(w,', '.join(sorted(KEEP_DM_GROUPS))))
    bad=sorted(t for t in r if t in DD_TYPES)
    if bad: raise SystemExit('ANP_KEEP_DM_TYPES: %s already Dog Days types (dd_types.txt)'%', '.join('%#x'%t for t in bad))
    return r
KEEP_DM=keep_dm_types(os.environ.get('ANP_KEEP_DM_TYPES',''))
# ANP_ROPES (default off = the out_rel6 output byte for byte, until live is tested in game): Dead Men's rappel ropes
# (ZRopeLnkObj 0x200499, 42 in M02/M03/M08/M09/M11B/M12/M13, 'Ropes!Rope#nn\Rope_Ground' at the top of the tree, no events, nothing references them)
# are a POOL: kl2 Init (vt 0xbc14ec slot 82, 0x6674c0; DM 0x691400, same code) registers each in gameMgr
# [0xdd265c]+0x9fc/+0xa00 (max 8), GetNextRope 0x656f50 hands them out round robin (NULL when empty) and both rappels
# NULL-check it (player: ZFFPlayerMovementRappel Activate 0x6db4cd stores it at +0x200c, uses 0x8253b0 / 0x61663f /
# 0x8ad0d3; NPC: 0x5fb040 -> je past the attach at 0x5fb30b). live = the type is kept (ANP_KEEP_DM_TYPES 'rope'), so a
# rope hangs from the anchor during every player and merc rappel as in Dead Men; rel6 neutralised the pool and every
# rappel ran ropeless (in game: works). Offline (14 Oct): the kept record is Dead Men's byte for byte plus the generic
# ZGEOM trailing bool (all 42), and a 4-deep direct-call crawl from the 10 slots ZRopeLnkObj overrides (0, 11-14, 18,
# 82, 87, 163, 193; 124 functions) reaches none of ZAppendage's faulty lookup 0x5d1e50 / 0x5670d0 / 0x7e06c0 (the same
# crawl from ZAppendage's slots finds its 3 calls). Not yet seen in game: the rope draw, the merc rappel's rope attach.
ROPES=os.environ.get('ANP_ROPES','off').strip().lower()
if ROPES not in ('live','off'): raise SystemExit('ANP_ROPES=%s: use live or off'%ROPES)
if ROPES=='live': KEEP_DM|=set(KEEP_DM_GROUPS['rope'])
# ANP_PLANT (default static; off = the out_rel6 output byte for byte; PLAN item 7 option A): Dead Men's ZPlant leaves
# (0x2000fd, 973: M12 314, M13B 559, M14 38, M03 37, M06 24, M13 1; 'Leaf_nn'/'Leaves' beside the kept trunks and
# AncorBox anchors) stay neutralised to ZSTDOBJ (same pool slot, no node moves, no ZPlant/ZCloth code runs) but KEEP
# their prim like the ZHavokCar props (KEEP_PRIM): the leaves draw in their authored rest pose, without sway. Their prims
# are 0x70100 prims over 0x80189 meshes, the ordinary Dog Days static mesh kind (work\neutral\cat_3.md 2), and the .prm
# chunk table already counts the reference (rel6 zeroed the .gms prim word only). Live sway = ANP_KEEP_DM_TYPES=plant
# (PLAN item 18), which takes precedence (the type is then not neutralised at all).
PLANT=os.environ.get('ANP_PLANT','static').strip().lower()
if PLANT not in ('static','off'): raise SystemExit('ANP_PLANT=%s: use static or off'%PLANT)
# events kept on a kept owner of that Dead Men type although they are in VEHICLE_ONLY (dropped by name otherwise)
KEEP_DM_OWNER_EVENTS={0x2000d7:{'MountedWeapon'}}
# ANP_NEUTRAL_SLOT (default on): a Dead Men-only geom type is neutralised to a Dog Days type in the SAME node-table pool
# slot (clusters.basetype_guess): group 0 -> ZGROUP, 1 -> ZSTDOBJ 0x200002, 3 -> 0x800001a (the plain list entity:
# Dead Men's 'List', Dog Days' CoverList / TrackLinkObjects; neutralised with an empty list). A slot change moves static
# node indices (clusters.node_order), and those are baked into the .oct/.sgp/.rmc/.rmi/.sgd/.hrd/.HVK and the h[6]
# overlap lists. Before this, Dead Men's AO volumes (0x800011e, slot 3) became ZSTDOBJ (slot 1): every level with one
# had nodes shifted (M01: node 12715 = Ambient_Env_Character in Dead Men became AmbientOcclusion!Inside_Garage, which
# has no overlap slot, so every mover listing that light hit CListUser id 0 = the in-game 'bad bucket id=000000' at
# kl2 0x4f8a60 from 0x61ee1a). ANP_NEUTRAL_SLOT=0: the old group -> ZGROUP, else ZSTDOBJ rule (the build validator
# then fails on such levels unless ANP_VALIDATE=0).
NEUTRAL_SLOT=os.environ.get('ANP_NEUTRAL_SLOT','1')=='1'
NEUTRAL_BY_SLOT={0:ZGROUP,1:0x200002,3:int(os.environ.get('ANP_NEUTRAL_SLOT3','0x800001a'),0)}
def neutral_type(t):
    """Dog Days stand-in for a Dead Men-only geom type t (see ANP_NEUTRAL_SLOT)"""
    if not NEUTRAL_SLOT: return ZGROUP if (t & 0x100000) else 0x200002
    from clusters import basetype_guess
    bt=basetype_guess(t); nt=NEUTRAL_BY_SLOT.get(bt)
    if nt is None or basetype_guess(nt)!=bt or nt not in DD_TYPES:
        raise SystemExit('no Dog Days stand-in type in pool slot %d for Dead Men type %#x (would move static node '
                         'indices; add one to NEUTRAL_BY_SLOT)'%(bt,t))
    return nt

# Dead Men streamed dialogue (.str) is read straight from the DM install (path relative to the DD game dir)
DM_STREAM_DIR='..\\Kane and Lynch Dead Men\\'
# 'mute' = record-free sound banks until the DM->DD sound record conversion exists (type-1 layout differs)
SND_MODE='convert'
GRAFT_MENU=os.environ.get('ANP_GRAFT_MENU','1')=='1'
# Dog Days' HUD + fonts (L01 mainsceneincludes\FFOsdMP1.zip: 2 ZOnScreenDisplay2, CharObj, 8 fonts, OSD cameras,
# FrameForOsd[2] = the BackgroundFrame[2] defines) grafted with their font chunks and HUD textures; Dead Men's copy is
# made inert in place and every live path into it re-rooted to the grafted copy
GRAFT_OSD=GRAFT_MENU and os.environ.get('ANP_GRAFT_OSD','1')=='1'
OSD_ZIP='AllLevels/FFOsdMP1.zip'
# ANP_DOCUCAM (default 0 = old output byte for byte): also graft Dog Days' handheld camera layer (L01
# mainsceneincludes\AllLevels/Cam_Handheld.zip: DocuCamProfiles + their MatPosAnim camera-shake objects). kl2 has no
# name lookup: each ZDocuCamProfile registers itself at player+0x2c90+4*state (0x682db0 -> 0x6df6f0, state enum at
# profile+0x44) and every reader (0x5754a0 callers) null-checks, so without it the camera simply has no handheld
# sway/hit/aim kick (= Dead Men, whose exe has no DocuCam class at all). Pure look choice, tail graft only.
DOCUCAM=os.environ.get('ANP_DOCUCAM','0')=='1'
DOCUCAM_ZIP='AllLevels/Cam_Handheld.zip'
# Dead Men's typefaces in the grafted Dog Days UI (tools/dmfont.py): each grafted Dog Days font (by entity name) gets a
# Dog Days-layout copy of a Dead Men font (by entity name under Dead Men's FFOsdMP1.zip\AllLevels/FFFonts.zip).
# GUI XML fonts (Header/Menu/Text/Button) and DebugText keep their role. The OSD's list is [H1,H2,H3,DebugText] in Dog
# Days and [Text,Header,DebugText] in Dead Men. OSD text starts on list entry 0 (kl2 0x6a4ce0 pushes font 0 on the
# markup font stack) and only a numbered font tag (kl2 0x610d6e) changes it; no stock .LOC/.xml/.prp of either game
# and neither exe has one, so entry 0 draws the whole HUD: H1 = Dead Men's entry 0, Text (Dead Men's HUD look).
# H2/H3 are copies of Dog Days' Text font (20pt, H1 is a copy of Header): should anything select them they get Dead
# Men's Text too (not Header/DebugText by position: 37pt capitals where Dog Days expects body text).
# Override: ANP_DM_FONT_MAP="H2=Menu,Button=Text"; off: ANP_DM_FONTS=0. ANP_DM_FONT_FILL=0: only private-use code
# points Dead Men lacks come from Dog Days (else every missing one, e.g. Cyrillic/Polish); ANP_DM_FONT_DD="e012-e018"
# takes those code points from Dog Days even where Dead Men has its own (0xe000..0xe011 are the same buttons in both;
# 0xe012..0xe018 are each game's own symbols).
DM_FONTS=os.environ.get('ANP_DM_FONTS','1')=='1'
# Dead Men's HUD art in the grafted Dog Days OSD tables + DM-only art parked in spare slots, sidecar ANP_hud.json in
# the level zip (tools/dmhud.py; contact sheet: py tools\dmhud.py sheet <zip> <png>). Off: ANP_DM_HUD=0.
DM_HUD=os.environ.get('ANP_DM_HUD','1')=='1'
# ANP_DM_FONT_ROLES=1 (default): the GUI XML fonts get the Dead Men font of the SAME typeface closest to Dog Days'
# size for that role, so the grafted Dog Days menus (guielems.xml SecondTextOffset 250 etc.) keep their layout:
#   Header (DD FOUNMB 28) <- DM Menu   (MorSCCB 30, Dead Men's menu/title face; width 0.95x, ascent -18 = DD's)
#   Menu   (DD FOUNMB 20) <- DM DebugText (MorSCCB 20, the same face as DM Menu; width 0.90x)
#   Button (DD FOUNMB 18) <- DM DebugText (MorSCCB 20, the same face as DM Button 28; width 1.00x)
#   Text   (DD FOUNMB 20) <- DM Text (MorSCLB 24, the only body face; width 1.06x)
# (same-name mapping: Header 1.19x, Menu 1.37x, Button 1.41x wider than Dog Days'). 0 = same-name mapping.
DM_FONT_MAP={'Button':'Button','Text':'Text','DebugText':'DebugText','Menu':'Menu','Header':'Header',
             'H1':'Text','H2':'Text','H3':'Text'}
if os.environ.get('ANP_DM_FONT_ROLES','1')=='1':
    DM_FONT_MAP.update({'Header':'Menu','Menu':'DebugText','Button':'DebugText'})
for _kv in [x for x in os.environ.get('ANP_DM_FONT_MAP','').split(',') if '=' in x]:
    _a,_b=(t.strip() for t in _kv.split('=',1)); DM_FONT_MAP[_a]=_b
def _cp_set(s):
    r=set()
    for part in [x.strip() for x in s.split(',') if x.strip()]:
        a,_,b=part.partition('-'); r.update(range(int(a,16),int(b or a,16)+1))
    return r
OSD_PATH='ROOT\\AllLevels/mainsceneincludes.zip\\'+OSD_ZIP
# ANP_LOADER (default silent): every level gets Dog Days L01's Loader_Sequence.* (its loading screen: LoadScreenA..E
# pictures, progress indicator, subtitles). kl2 builds '<scene dir>\Loader_Sequence.ZIP' (0x5655dc..0x56569e; else
# \AllLevels\Loader_Sequence.ZIP). silent: its 9 Loader_Sequence<Lang>.LOC get every /Load/<L>_Load/... subtitle
# line blanked (seen in game on M01: L01's phone-call lines 'Hey hon...' under the Dog Days pictures; the scene has
# chapter index 0 = L01) and Loader_Sequence.WAV keeps its size with zeroed IMA-ADPCM data (silence). That bank holds
# only 164 SFX/Impacts/* clips, not the call; the voice heard while loading is the level's own <ID>_Main_LS_* bank,
# converted from Dead Men's. dd: the donor files byte for byte (before 11 Oct).
LOADER_MODE=os.environ.get('ANP_LOADER','silent').strip().lower()
if LOADER_MODE not in ('dd','silent'): raise SystemExit('ANP_LOADER=%s: use dd or silent'%LOADER_MODE)
# ANP_CHAPTER_TITLES (default 1): /AllLevels/Menu/Play/L01..L11_ChapterTitle in the level LOCs = this level's Dead Men
# title (<DM key>_ChapterTitle of the same LOC; kl2 0x881350 finds no 'L<n>_Main' in a Dead Men path -> chapter 0, and
# its title lookups /Menu/Play/L%02d_ChapterTitle came out blank). 0 = old.
CHAPTER_TITLES=os.environ.get('ANP_CHAPTER_TITLES','1')=='1'
# ANP_LOC_EXTREME (default plus): Dog Days' 4th difficulty has no Dead Men name (Dead Men's LOC has Difficulty_Easy /
# Medium / Hard = Aspirin / Codeine / Morphine). plus: Difficulty_Extreme = that LOC's Difficulty_Hard text + '+'
# ('Morphine+', as the Dead Men menu page, tools/anp_menu.py); dd: Dog Days' own text from the donor LOC (English when
# the donor's language lacks it); 0: no key (old).
LOC_EXTREME=os.environ.get('ANP_LOC_EXTREME','plus').strip().lower()
if LOC_EXTREME not in ('plus','dd','0'): raise SystemExit('ANP_LOC_EXTREME=%s: use plus, dd or 0'%LOC_EXTREME)
# ANP_BRIEF_COMMANDS (default 1): Dead Men's 6 crew-command hints (M02 x3, M03 x2, M06 x1) are converted like every
# other hint now that loader/squad.inc gives crew orders, and their text names the squad.inc keys instead of Dead Men's
# input actions (locconv.command_hint_fix; labels ANP_SQUAD_KEYS="follow=1,attack=2,defend=3,next=Tab,prev=Shift+Tab").
# 0 = dropped as before.
BRIEF_COMMANDS=os.environ.get('ANP_BRIEF_COMMANDS','1')=='1'
# ANP_COVERS (default box; tools/coverconv.py): Dead Men cover boxes Dog Days' cover list cannot take (ZBoxPrimitive
# Cover[bB]ox*, tilted ZSTDOBJ boxes) get new invisible Dog Days cover boxes under ANP_Tail\ANP_Covers (graft pass, 0
# nodes moved). off = nothing added (byte-identical). Needs the graft (ANP_GRAFT_MENU=1) with the tail host
# (ANP_GRAFT_HOST=old: nothing added, a WARNING line in the report). ANP_COVERS_MINHALF (cm, default 15): smaller
# boxes are skipped (0 = keep all).
# ANP_COVER_HINTS (default 1): M02's Dead Men cover hints ('You will snap into suitable cover...', 'Move towards small
# objects...') -> Dog Days' 'Press {TapCover} - Get Into Cover' from L01's LOC in the language of the Dead Men LOC used
# (Dead Men has no Dutch/Russian/Polish/Japanese: those LOCs are English copies and get the English hint; English also when
# L01 lacks the key); Dog Days takes cover with TapCover, not by walking into it. 0 = Dead Men's text.
COVER_HINTS=os.environ.get('ANP_COVER_HINTS','1')=='1'
COVER_HINT_KEYS=__import__('re').compile(r'^/M02/IngameBriefing/M02A_(045_B_CoverInfo|050_B_StandInHighCover|'
                                         r'080_B_CrouchInLowCover_(pc|ps3|xenon))$',__import__('re').I)
COVER_HINT_DD=['L01','IngameBriefing','L01_IngameBriefing_010_Cover']
# ANP_STATIC_SHADOWS (default off): chunk = Dead Men's static shadow meshes (ZSHADOWMESHOBJ 0x200110, named
# ..._Chunk<n>) keep their prim when neutralised to ZSTDOBJ (type stays 0x200002, so no node moves). M01 has 163 such
# meshes: 23 named ..._Chunk<n> and 140 ..._Chunk<n>_Tex<m>; all = every one of them. Needs an in-game A/B (z-fighting /
# double darkening risk) before it can be the default.
STATIC_SHADOWS=os.environ.get('ANP_STATIC_SHADOWS','off').strip().lower()
if STATIC_SHADOWS not in ('off','chunk','all'): raise SystemExit('ANP_STATIC_SHADOWS=%s: use off, chunk or all'%STATIC_SHADOWS)
# ANP_VEHICLE_RELAY (default exit; off = the old output byte for byte): Dead Men's vehicle routs have no Dog Days layout
# and are dropped (port() node(): 'event dropped' / VEHICLE_ONLY), so whatever a rout sends when it finishes (its
# container targets: the next rout, timers, trigger boxes, deactivators, ...) is never sent and four levels cannot
# reach their exit (work\gap\entities\blockers.txt: M01, M03, M07, M09B; M11 via the BTR). In place of such a dropped
# rout the same node gets a RelayMessageList ['AITrigger' in, 'AITrigger' out, C targets, f delay]: Dog Days' own
# message forwarder (ZRelayMessageList, kl2 0x6e3cb0: on its in-message it sends its out-message to every target, at
# once when the delay is 0; stock DD has 236, on ZGROUP owners 155 times, e.g. F01 KickDoor_RelayList 'AITrigger' ->
# 'DoorOpened'). 'AITrigger' is what Dead Men's senders (TriggerDelay, TriggerBox, routs ...) send to start a rout,
# and what a rout's targets get. Targets = the rout's container refs minus roads/splines/cars (Dead Men types
# 0x1004b4/0x2000cf/0x2000d4), the node itself and refs that name nothing. The relay fires when the rout would START,
# not when the van would arrive (ANP_VEHICLE_RELAY_DELAY seconds, default 0, delays every relay).
#   exit: only the routs on an exit chain (VEHICLE_RELAY_EXIT, by Dead Men entity path; the build fails if one is not
#     found) plus their extra targets (M11: the BTR's 'destroyed' squad list) and PlayerEnterVehicleActions listed
#     there; all: every dropped vehicle rout and every PlayerEnterVehicleAction whose vehicle holds a neutralised
#     ZHavokCar. A planned relay whose own node can be reached again from its targets (any event reference in the
#     level, i.e. a possible message loop) is not written (logged 'vehicle relay SKIPPED (loop)').
# A PlayerEnterVehicleAction (the 'get in the van' prompt) on a neutralised van becomes the same kind of relay: its use
# box is a 10 cm box at its squad group's origin (the prompt hangs off the van's seats, f100), so neither a trigger box
# nor a Dog Days PlayerAction on that node would sit at the van; the relay sends its targets (the get-in cutscene etc.)
# as soon as the prompt would have been switched on.
VEHICLE_RELAY=os.environ.get('ANP_VEHICLE_RELAY','exit').strip().lower()
if VEHICLE_RELAY not in ('off','exit','all'): raise SystemExit('ANP_VEHICLE_RELAY=%s: use off, exit or all'%VEHICLE_RELAY)
VEHICLE_RELAY_DELAY=float(os.environ.get('ANP_VEHICLE_RELAY_DELAY','0') or 0)
VEHICLE_ROUTS={'VehicleMoveOnRoadBehaviourRout','VehicleExitBehaviourRout','VehicleEnterBehaviourRout',
               'VehicleGetawayBehaviourRout','VehicleSpecialMoveBehaviourRout','VehicleHuntBehaviourRout',
               'ZVehicleFireOnRoadBehaviourRout','VehicleFireBehaviourRout','VehicleMoveBehaviourRout'}
VEHICLE_RELAY_SKIP_TYPES={0x1004b4,0x2000cf,0x2000d4}     # Dead Men roads, splines, cars: positions, not receivers
# per level: routs (Dead Men entity path, extra targets) and PlayerEnterVehicleActions (path); blockers.txt nodes in [].
VEHICLE_RELAY_EXIT={
    'M01':dict(routs=[('AI_Players!Allies!05_DonutShop_ProxySquads!05_EscapeVehicle\\060_VehicleMoveOnRoadBehaviour',())]),  # [1821]
    'M03':dict(routs=[('GamePlay!5_Lobby!GetAwayVan_FusionSquad\\10_VehicleMoveOnRoadBehaviour',()),                       # [12412]
                      ('GamePlay!5_Lobby!GetAwayVan_FusionSquad\\30_VehicleEnterBehaviour',())],                          # [12411]
               peva=['GamePlay!5_Lobby!GetAwayVan_FusionSquad\\EnterGetAwayVehicle']),                                  # [12415]
    'M07':dict(routs=[('AI_Players!Friendly!40_Fusion_Daughter_Escaping\\20_VehicleEnterBehaviour',()),                   # [1343]
                      ('AI_Players!Friendly!40_Fusion_Daughter_Escaping\\25_VehicleMoveOnRoadBehaviour_rev',()),          # [1342]
                      ('AI_Players!Friendly!40_Fusion_Daughter_Escaping\\30_VehicleMoveOnRoadBehaviour',())]),            # [1339]
    'M09B':dict(routs=[('Civilians!010_GetawayStreet!GetawayCar\\VehicleMoveOnRoadBehaviour',())]),                        # [11663]
    # the BTR (neutralised ZHavokCar, its 3 ZVehicleFireOnRoad routs dropped) can never be destroyed: its drive start
    # (sender CheckpointBox_01_ChurchSide) also sends what BTR_Squad_01's squad list sends when it dies -> Timer_NoBTR
    # [567], Blocker_BTRTalks [568] -> CheckpointBox_02_AfterBTR -> GeomDeactivator_RoadToBigSquare (blockers.txt)
    'M11':dict(routs=[('020_ChurchFront!BTR!BTR_Squad_01\\01_Drive',('020_ChurchFront!Allies!Mercenaries!Timer_NoBTR',     # [3577]
                                                                   '020_ChurchFront!Allies!Mercenaries!Blocker_BTRTalks'))]),
}
# Optional keys of a VEHICLE_RELAY_EXIT entry (used by the two switches below; applied whenever ANP_VEHICLE_RELAY is not
# off, entity paths are Dead Men paths without 'ROOT\'; the build fails when one does not match exactly):
#   delays  {path: seconds}  that relay's own delay (RelayMessageList field 3) instead of ANP_VEHICLE_RELAY_DELAY. kl2
#           0x6e3cb0 (vt slot 26): delay 0 -> send at once (0x7453d0); else start time = clock [0xdd2640]+0x48 / 1024 at
#           +0x54 and register; slot 25 (0x8c8bc0) sends when clock >= start + delay (seconds) and unregisters (static
#           disassembly; all 236 stock Dog Days RelayMessageLists use delay 0, so a delayed one is not seen in game yet)
#   edits   [(path, event, k, '+'|'-', ref path)]  add / remove one ref in the k-th container (0-based) of that event
#           (Dead Men layout, before conversion)
#   beams   [(owner path, actor path)]  extra Dog Days ZBeamToPos [actor, C 0] on an EXISTING node (no node is added):
#           ZBeamToPos moves the actor to its owner's position, so the owner is a checkpoint's own position object
#   timers  [(owner path, seconds, [target paths])]  extra Dog Days TriggerDelay [i s, i 0, i -1, b 0, C targets] (the
#           converter's own layout for every TriggerDelay) on an EXISTING node (no node is added); started by an
#           AITrigger to the owner (e.g. a relay target), cancelled by AIBlocker (a Blocker naming the owner)
#   require [path]  entity paths that must each name exactly one node (else the build fails)
#   vanonly True: ZSetGetawayDamageState / ZBeamToPos whose actor is a neutralised Dead Men car (a ZHavokCar or a group
#           holding one) are dropped (a ZBeamToPos with a container becomes a RelayMessageList to it): never meant for
#           a ZSTDOBJ; they only become reachable through the fallback chain
# ANP_M03_GETAWAY (default faithful; instant = the out_rel2 output, byte for byte): M03's getaway after the lobby fight.
#   Dead Men: 05_MiniCutScene_Dialog -> 10_VehicleMoveOnRoadBehaviour (the van reverses into the lobby, route 64 m
#   from (-3248,-11859) to (338,-9078)) -> on arrival MatPosAnimProxy_CarDoorsOpen (doors anim frames 1..100, its end
#   switches the get-in prompt EnterGetAwayVehicle on) and WoundedFilter_GetIntoVan (Lynch + Vault Breaker: someone
#   down -> objective 055_HealMercs + Timer_WoundCheck, which asks again every 2 s; nobody down -> objective
#   050_GetIntoVan) -> the player walks up and uses the van -> 20_MiniCutScene_GetIn + beams -> 30_VehicleEnterBehaviour
#   -> Timer_Endlevel (4 s) -> M03B. instant (old): every relay fires at once, so the level ends ~4 s after the dialog.
#   faithful: the 10_ relay waits ANP_M03_GETAWAY_DRIVE s (default 9: the van's drive, inferred from 64 m reversing at
#   the rout's speed 35 read as km/h), the get-in relay is driven from WoundedFilter_GetIntoVan's 'nobody down'
#   container (taken off CarDoorsOpen's end container, which on the neutralised van may never complete) and waits
#   ANP_M03_GETAWAY_DOORS s (default 3.5: the 100-frame door anim at ~30 fps, inferred). No walk-up gate: Dead Men
#   has no trigger box where the van stops (the nearest boxes are the bank door TriggerBox_GetAwayVan, enabled at start,
#   and TB_VaultBreakerOutside, tracking the Vault Breaker; GetAwayVan_FusionSquad\TriggerBox lies 25 m away on the
#   departure route at (1456,845,-11230), off, no targets).
M03_GETAWAY=os.environ.get('ANP_M03_GETAWAY','faithful').strip().lower()
if M03_GETAWAY not in ('faithful','instant'): raise SystemExit('ANP_M03_GETAWAY=%s: use faithful or instant'%M03_GETAWAY)
if M03_GETAWAY=='faithful':
    _gv='GamePlay!5_Lobby!GetAwayVan_FusionSquad\\'
    VEHICLE_RELAY_EXIT['M03'].update(
        delays={_gv+'10_VehicleMoveOnRoadBehaviour':float(os.environ.get('ANP_M03_GETAWAY_DRIVE','9') or 0),
                _gv+'EnterGetAwayVehicle':float(os.environ.get('ANP_M03_GETAWAY_DOORS','3.5') or 0)},
        edits=[(_gv+'MatPosAnimProxy_CarDoorsOpen','MatPosAnimProxy',1,'-',_gv+'EnterGetAwayVehicle'),
               ('GamePlay!5_Lobby!GetawayWoundedCheck!WoundedFilter_GetIntoVan','WoundedFilter',2,'+',_gv+'EnterGetAwayVehicle')])
# ANP_M03B_FALLBACK (default teleport; off = the out_rel2 output, byte for byte): M03B is Dead Men's van chase and the
# van does not drive in Dog Days, so its four stages are joined by relays (every vehicle rout on the single-player
# chain, the two get-in prompts) and Dead Men's own beams; stage 1 (the tunnel roadblock) has no Dead Men beam for the
# player, so checkpoint 04's own player-1 position object gets one (beams). Stages and what moves the three of them:
#   0 bank street -> 1 tunnel roadblock: level start (AIMonitor) -> 01_VehicleEnter .. 02c -> Checkpoint_save04 ->
#     03_VehicleExit (GeomActivator_TunnelStart) + player to CP_04_PosP1, Lynch / Vault Breaker by SP_Beam_Roadblock
#   1 -> 2 underpass: snipers dead -> 04 rout -> Checkpoint_save05 -> get-in 02 (GeomDeactivator_TunnelEnd,
#     SP_Beam_Roadblock) -> 05 .. 06B -> 3 s -> 06C -> 5 s -> 06D -> MC_04A_CrashUnderpass + Gate_Beam01 (Dead Men's
#     underpass beams: player, Lynch, Vault Breaker); MC_04A's end saves checkpoint 06
#   2 -> 3 subway: bag picked up, TriggerBox_PostLostBag -> 08 rout -> MC_05 -> get-in 03 -> Checkpoint_save07
#     (SP_Beam_Underpass) -> 09 (GeomDeactivator_UnderpassBound) -> 10 -> 11 -> Activator_CrashBomb, the crash sound
#     and BeamPos_02_Subway_Hero (Dead Men's subway beams: player, then Lynch -> MC_09_SubwayCrash -> MC_10 ->
#     Checkpoint_save08). The Vault Breaker has no subway beam in Dead Men (Gate_Beam02 deactivates his squad).
#   MC_08_SubwayHangon (hanging on in the falling van) and the van's own beams are left out.
M03B_FALLBACK=os.environ.get('ANP_M03B_FALLBACK','teleport').strip().lower()
if M03B_FALLBACK not in ('teleport','off'): raise SystemExit('ANP_M03B_FALLBACK=%s: use teleport or off'%M03B_FALLBACK)
if M03B_FALLBACK=='teleport':
    _fa='Hero_Allies!Mercs!FusionSquad_All\\'; _dr='Hero_Allies!Mercs!MercSquad_Driver\\'
    VEHICLE_RELAY_EXIT['M03B']=dict(
        routs=[(_fa+'01_VehicleEnterBehaviour',()), (_fa+'02a_VehicleGetaway_City_2_Hwy',()),
               (_dr+'02_VehicleMoveOnRoad_CityEnd',()), (_fa+'02b_VehicleGetaway_Hwy_2_Tunnel',()),
               (_fa+'02c_VehicleGetaway_ToRoadBlock',()),
               (_fa+'03_VehicleExitBehaviour_Tunnel',('Specials!Checkpoints!CP_04_PosP1','COOP!SP_Beam_Roadblock')),
               (_dr+'04_VehicleMoveOnRoad_Tunnel',()), (_fa+'05_VehicleEnterBehaviour_ToReverse',()),
               (_fa+'06A_VehicleGetaway_ToNochase',()), (_fa+'06B_VehicleGetaway_Nochase',()),
               (_fa+'06C_VehicleGetaway_Reverse',()),
               # beam first: the player and the driver are in place before MC_04A binds (review 12 Oct)
               (_fa+'06D_VehicleGetaway_Reverse02',('Specials!BeamPos!Gate_Beam01\\Way#01',_fa+'MC_04A_CrashUnderpass')),
               (_dr+'08_VehicleMove_Underpass01',()), (_dr+'08_VehicleMove_Underpass02',()),
               (_fa+'09_VehicleEnterBehaviour_Underpass',()), (_fa+'10_VehicleGetaway_ToSubway',()),
               (_fa+'11_VehicleGetaway_SubwayCrash',('Effects!Subway!Activator_CrashBomb','Sound!Sound_SubwayCrash',
                                                      'Specials!BeamPos!BeamPos_02_Subway_Hero'))],
        peva=[_dr+'02_EnterGetAwayVehicle_Roadblock', _dr+'03_EnterGetAwayVehicle_Underpass'],
        # the driver (Ryu, script actor Merc_03) rode in the van in Dead Men and the van's beams moved him; MC_04A,
        # MC_04D and MC_05 on the chain bind him, so he is beamed to the underpass van spot with the others
        beams=[('Specials!Checkpoints!CP_04_PosP1','Hero_Allies!Hero!Hero_01_Bank'),
               ('Specials!BeamPos!BeamPos_01_Underpass_Car','Hero_Allies!Mercs!Merc_Driver_02')],
        vanonly=True)
# ANP_M07_TRUCK (default relay; off = the out_rel6 output, byte for byte): M07's exit chain starts at the monster
# truck's 03_WindowHitTriggerBox (ZWindowHitTrigger EWINDOW_HIT -> 39_Squad_Hero\MiniCutScene -> the Daughter relays ->
# Timer -> Aftermath -> funeral). kl2 (vt 0xbc5b3c): the ctor leaves it OFF (+0x38=0, 0x512bfd); the handler (slot 26
# 0x558a20) switches it on/off on AITrigger/AIBlocker and, only when on, sends AITrigger to its targets on
# VehicleFXHit with part 0 (a window; HIT), VehicleWindowLayerChanged (1) or VehicleFirstWindowDestroyed (2). Those
# come from ZVehicleEffects' window listeners (0x54cb40: ProjectileHit on a Window_A/B/C layer -> VehicleFXHit to the
# truck group) through the group's RelayMessageList '' '' (relays every message with its data, 0x6e3cb0/0x7453d0).
# Nothing in the level ever sends AITrigger to the truck group (only AIDWrappers with their own message names), and
# every truck rout is dropped, so in rel6 the trigger stays off, the truck never attacks and the exit is reached only
# if all 8 henchmen (left at the truck's spawn) die. Dead Men: Timer_TruckAttack -> 10_ToGrave .. 22_UpTheRamp (its
# end shows objective 020_KillDriver) -> 25 .. 55 (03_EnsureCorrectSpline) -> 60_rev, whose end crushes the daughter
# (30_MiniCut_CrushedByTruck) unless a window hit fired first (03_TriggerCounter -> 03_Blocker blocks the crush).
# relay: the 10_ToGrave node gets a relay (its own targets + objective 020, music, the truck's lights and boss sound,
# the first of 03_TriggerCounter's 2 counts (Dead Men primed it through 55_'s 03_EnsureCorrectSpline TriggerDelay; the
# relay primes it in the same call, so no hit can land before the prime) and AITrigger to 03_WindowHitTriggerBox = on)
# after ANP_M07_TRUCK_RAMP s (default 15: drives
# 10+20+22 = 71+61+22 m at 45/45/30 read as km/h + ~2 s cutscene, inferred), and starts a TriggerDelay on the dropped
# 60_rev node that fires after ANP_M07_TRUCK_WINDOW s (default 62: 25..60 drives + 37's 1 s timer + 41's cutscene,
# inferred; ~77 s after Timer_TruckAttack in all). 03_Blocker also sends AIBlocker to that node, so a window hit
# cancels it (TriggerDelay: AIBlocker sets +0x34, 0x4774b0; update 0x8ec330 then stops without sending).
# ANP_M07_TRUCK_TIMEOUT: win (default) = the timer sends what the window hit sends (03_TriggerCounter, LightsOff3,
# 39_Squad_Hero\MiniCutScene: the level always completes even if hits on the static truck never register); fail = what
# 60_rev sent in Dead Men (the daughter is crushed: Dead Men's lose condition; only once window hits are proven in
# game); none = no timer (the window hit is the only way on).
M07_TRUCK=os.environ.get('ANP_M07_TRUCK','relay').strip().lower()
if M07_TRUCK not in ('relay','off'): raise SystemExit('ANP_M07_TRUCK=%s: use relay or off'%M07_TRUCK)
M07_TRUCK_TIMEOUT=os.environ.get('ANP_M07_TRUCK_TIMEOUT','win').strip().lower()
if M07_TRUCK_TIMEOUT not in ('win','fail','none'): raise SystemExit('ANP_M07_TRUCK_TIMEOUT=%s: use win, fail or none'%M07_TRUCK_TIMEOUT)
def _m07_num(name_, dflt_):
    try: x_=float(os.environ.get(name_,dflt_) or 0)
    except ValueError: raise SystemExit('%s=%r: not a number'%(name_,os.environ.get(name_)))
    if x_!=x_ or x_ in (float('inf'),float('-inf')): raise SystemExit('%s=%r: not a finite number'%(name_,os.environ.get(name_)))
    return x_
M07_TRUCK_RAMP=_m07_num('ANP_M07_TRUCK_RAMP','15')
M07_TRUCK_WINDOW=int(_m07_num('ANP_M07_TRUCK_WINDOW','62'))
if M07_TRUCK_RAMP<0: raise SystemExit('ANP_M07_TRUCK_RAMP=%g: must be >= 0 (seconds)'%M07_TRUCK_RAMP)
# a 0 s window would fire the timeout together with the relay, before any window hit could count
if M07_TRUCK_TIMEOUT!='none' and M07_TRUCK_WINDOW<1:
    raise SystemExit('ANP_M07_TRUCK_WINDOW=%d: must be >= 1 (seconds), or ANP_M07_TRUCK_TIMEOUT=none'%M07_TRUCK_WINDOW)
if M07_TRUCK=='relay':
    _mt='AI_Players!Enemy!03_MonsterTruck\\'
    _m07=VEHICLE_RELAY_EXIT['M07']
    _m07['routs']=_m07['routs']+[(_mt+'10_VehicleMoveOnRoadBehaviour_ToGrave',
        ('Special!MissionObjectives!MissionObjective_020_KillDriver','Special!Music!9p',_mt+'Activator_TruckMusic',
         _mt+'LightsActivator',_mt+'03_TriggerCounter',_mt+'03_WindowHitTriggerBox')
        +((_mt+'60_VehicleMoveOnRoadBehaviour_rev',) if M07_TRUCK_TIMEOUT!='none' else ()))]
    _m07['require']=list(_m07['routs'][-1][1])     # a relay target that names nothing would be a silent soft-lock
    _m07['delays']={_mt+'10_VehicleMoveOnRoadBehaviour_ToGrave':M07_TRUCK_RAMP}
    if M07_TRUCK_TIMEOUT!='none':
        _m07['timers']=[(_mt+'60_VehicleMoveOnRoadBehaviour_rev',M07_TRUCK_WINDOW,
            [_mt+'03_TriggerCounter',_mt+'LightsOff3','AI_Players!Friendly!39_Squad_Hero\\MiniCutScene']
            if M07_TRUCK_TIMEOUT=='win' else
            [_mt+'61_MiniCut_RestDies',_mt+'99_PlayAudio_SquishDaughter_03',_mt+'CamShaker_Deactivator',
             _mt+'TriggerKanePsychoMode','AI_Players!Friendly!50_Proxy_DaughterCrushedByTruck\\30_MiniCut_CrushedByTruck'])]
        _m07['edits']=[(_mt+'03_Blocker','Blocker',0,'+',_mt+'60_VehicleMoveOnRoadBehaviour_rev')]
# ANP_PLAYERMON (default 1): Dead Men PlayerMonitors -> one Dog Days PlayerMonitor event per non-empty event list, with
# its targets and the player filter swapped like PF_SWAP (by number in both dispatchers: DM 0x6b8f80, kl2 0x589600);
# details and the event map in prpconv.py (PM_DEAD_DD). 0 = the old statistical conversion (one eFIRE_WEAPON event,
# targets mostly lost; filter name kept).
PLAYERMON=os.environ.get('ANP_PLAYERMON','1')=='1'
SND_HIDE_TYPES=(0x12,)   # DM dialogue banks (streamed) hidden until record conversion
# ANP_SND_IMPORT_DD (15 Oct, tools/sndimport.py; default 0 = the old output byte for byte): copy the Dog Days sound records
# the donor (F03) animation clips name and the Dead Men bank lacks (crouch/sneak/cover/strafe foley, Dog Days reloads)
# from F03's .SND/.WHD/.WAV into the level banks, then point the clips at them (clipsnd extra).  Non-localised, in-memory
# waves only; the level .WAV grows by the imported data (reported as 'import: wav bytes added').
SND_IMPORT_DD=os.environ.get('ANP_SND_IMPORT_DD','0')=='1'

# Dead Men animation databases -> Dog Days databases (all present in F03's ANM)
ANMDB_PREFIX='anmcol:animationdatabase#'
ANMDB_MAP={
    'PlayerCharacter':'Kane', 'Lynch_Coop':'Lynch', 'Army':'Swat_02', 'Police_USA':'Police',
    'Mercenary_04':'Thug', 'Female':'Civilian', 'Civilian':'Civilian', 'Van':'Civilian',
    'M4':'Type95', 'Rem_700':'Type95', 'MG_PKMSN2':'MG_GP_Type88', 'RugerMini14':'Type95',
    'Ak_74':'Ak_74', 'Tarrus':'Tarrus', 'SMG_MP5':'SMG_UMP', 'HK_69':'HK_69',
    'Shotgun_Spass12':'Shotgun_Spass12', 'P90':'Type05', 'Rem_870':'Shotgun_Remington_870',
    'SMG_TMP':'SMG_MPI69', 'SIG_552':'Zastavam', 'Pistol':'HG_SigSauer226',
}
# DM DBs merged INTO a Dog Days DB (DD keeps its clips for paths both have, DM-only paths are added).
# Every other DM DB (Female, Van, Police_USA = the police car, Mercenary_0x, ...) becomes its own DB.
ANM_MERGE_MAP={'PlayerCharacter':'Kane','Lynch_Coop':'Lynch','Army':'Swat_02','Mercenary_04':'Thug','Civilian':'Civilian','Female':'Civilian'}
ANM_DONOR='F03'   # Fragile Alliance map: its ANM carries nearly every DD character + weapon database
ANM_OWN_DB={'Van','Police_USA'}   # kept under their DM names once merged as their own DBs

# Level chain: Dead Men SceneChanger targets (Locations\M02_A\M02A_Main.zip, ...) -> the converted Dog Days scenes
# (Locations/M02/M02_Main.zip). kl2 0x6d36b0 loads the string as a path under <DD>\Scenes, with no lookup table.
DM_SCENE_IDS={'M01_A':'M01','M02_A':'M02','M03_A':'M03','M03_B':'M03B','M05_A':'M05','M06_A':'M06','M07_A':'M07',
              'M08_A':'M08','M09_A':'M09','M09_B':'M09B','M11_A':'M11','M11_B':'M11B','M12_A':'M12','M13_A':'M13',
              'M13_B':'M13B','M14_A':'M14'}
import re as _re
_SC_RE=_re.compile(r'(?i)^Locations[\\/]+(M\d\d_[AB])[\\/]+M\d\d[AB]_Main\.zip$')

# Scene layouts. A Dead Men level is <DM>\Scenes\Locations\<folder>\<name>_Main.zip and becomes
# <OUT_ROOT>\<ID>\<ID>_Main.zip (entries Scenes/Locations/<ID>/<ID>_Main.*). Scenes outside that pattern are listed by
# ANP id in SPECIAL_SCENES and keep Dead Men's own path under Scenes (py tools\port_level.py M07F):
#   M07F = the funeral (Dead Men Scenes\CutScenes\M07\M07_A_Funeral.zip, a full scene: M07 -> funeral -> M08). The path
#     must keep 'Funeral': kl2's scene start/end bookkeeping (0x881350 / 0x696c40, same checks as DM 0x67dac0 /
#     0x67dd6d) skips chapter index, LevelOfDetail and the profile save for scene paths containing it, as Dead Men does.
#     fxc aliases: fxc\miss_M07F.txt once harvested, else M07's list (same level art).
# They are written under SCENES_OUT: the Scenes folder that holds OUT_ROOT (OUT_ROOT = ...\Scenes\Locations, the
# default), else OUT_ROOT itself (ANP_OUT=work\out_x -> work\out_x\CutScenes\M07). ANP_OUT_SCENES overrides.
SCENES_OUT=os.environ.get('ANP_OUT_SCENES') or (os.path.dirname(os.path.abspath(OUT_ROOT))
                                               if os.path.basename(os.path.abspath(OUT_ROOT)).lower()=='locations' else OUT_ROOT)
FUNERAL_REL='CutScenes/M07/M07_A_Funeral.zip'
SPECIAL_SCENES={'M07F':dict(dm_folder='CutScenes\\M07',dm_name='M07_A_Funeral',rel='CutScenes/M07',stem='M07_A_Funeral',
                            fxc_stand_in='M07',title_key='M07A')}
FXC_DIR=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','fxc')

def scene_layout(dm_folder, dm_name, new_id):
    """where a scene is read from and written to (see SPECIAL_SCENES)"""
    sp=SPECIAL_SCENES.get(new_id.upper())
    if sp:
        if (dm_folder.replace('/','\\').lower(),dm_name.lower())!=(sp['dm_folder'].lower(),sp['dm_name'].lower()):
            raise SystemExit('%s is %s\\%s (got %s\\%s)'%(new_id,sp['dm_folder'],sp['dm_name'],dm_folder,dm_name))
        # the stand-in's keys always, plus the scene's own harvested ones (fxmiss_harvest only logs keys still missing
        # at run time, i.e. on top of the stand-in's)
        fx=[x for x in (sp.get('fxc_stand_in'),new_id) if x]
        return dict(src_dir=os.path.join(DM_GAME,'Scenes',sp['dm_folder']),src_stem=sp['dm_name'],
                    out_dir=os.path.join(SCENES_OUT,*sp['rel'].split('/')),rel=sp['rel'],stem=sp['stem'],fxc_ids=fx)
    return dict(src_dir=os.path.join(DM_ROOT,dm_folder),src_stem=dm_name+'_Main',out_dir=os.path.join(OUT_ROOT,new_id),
                rel='Locations/'+new_id,stem=new_id+'_Main',fxc_ids=[new_id])

def funeral_skipped():
    """ANP_SKIP_FUNERAL: 1 = M07 ends straight into M08 (the old default), 0 = M07 -> funeral -> M08, auto (default) =
    the funeral when its converted scene exists (in this build's output tree or in Dog Days' Scenes folder), so a
    rebuilt M07 never points at a scene that is not there"""
    v=os.environ.get('ANP_SKIP_FUNERAL','auto').strip().lower()
    if v in ('0','1'): return v=='1'
    roots=[SCENES_OUT,os.path.join(DD_GAME,'Scenes')]
    # complete scenes only: the zip plus its sound bank (.WHD/.WAV) and loading screen next to it (a half-copied or
    # half-built funeral would load into a crash or silence)
    d_,f_=os.path.split(os.path.join(*FUNERAL_REL.split('/')))
    stem_=os.path.splitext(f_)[0]
    need_=[f_,stem_+'.WHD',stem_+'.WAV','Loader_Sequence.zip']
    return not any(all(os.path.isfile(os.path.join(r,d_,x)) for x in need_) for r in roots)

def dd_scene_target(v):
    """Dead Men scene path -> converted Dog Days scene path. The funeral cutscene (M07 -> Funeral -> M08) keeps its
    path in Dog Days form (forward slashes, as every stock target) unless it is skipped (funeral_skipped: straight to
    M08); 'KaneAndLynch.zip' (the main menu) and anything else stay."""
    s=v if isinstance(v,str) else ''
    m=_SC_RE.match(s)
    if m and m.group(1).upper() in DM_SCENE_IDS:
        i=DM_SCENE_IDS[m.group(1).upper()]; return 'Locations/%s/%s_Main.zip'%(i,i)
    if s.lower().replace('/','\\')==FUNERAL_REL.lower().replace('/','\\'):
        return 'Locations/M08/M08_Main.zip' if funeral_skipped() else FUNERAL_REL
    return v

def gms_pack(raw):
    c=zlib.compressobj(9,zlib.DEFLATED,-15); comp=c.compress(raw)+c.flush()
    return struct.pack('<II',len(raw),len(comp)+9)+b'\0'+comp


# ---- exact class schemas (property loaders read from both exes; kl-merge, used with permission; pinned copy, see anp_paths) ----
def _load_exact_schemas():
    from anp_paths import load_schema, schema_missing
    try:
        dd=load_schema('schemas_dd.json'); dm=load_schema('schemas_dm.json'); en=load_schema('dd_enums.json')
    except (OSError, ValueError) as e:
        if os.environ.get('ANP_EXACT','1')=='1': raise schema_missing(e,'ANP_EXACT')
        return None
    def sig(S,ctrl):
        c=S['controllers'].get(ctrl)
        if not c or c not in S['classes']: return None
        return [S['loaders'].get(p['load'],'?')+('E' if p.get('enum') else '') for lvl,props in S['classes'][c]['levels'] for p in props]
    # every value kl2.exe knows, the dd_enums_extra.json supplement included (eSEAT_*, eMOVEMENT_M01, ...)
    from prpconv import dd_enum_names
    enum_names=dd_enum_names()
    return dict(dd=dd,dm=dm,sig=sig,enum_names=enum_names)
EXACT=None
def exact_event_ok(name):
    """True when Dog Days' exe has this controller with the same property layout as Dead Men's."""
    global EXACT
    if EXACT is None: EXACT=_load_exact_schemas() or {}
    if not EXACT: return False
    a=EXACT['sig'](EXACT['dm'],name); b=EXACT['sig'](EXACT['dd'],name)
    if a is not None and a==b: return True
    # DM-side schema unresolved (behaviour routs, proxy squads): Dog Days' exe has the class; keep the DM
    # props when their top-level value count matches Dog Days' schema (or DD's is unresolved too -> test).
    return name in PASS_UNVERIFIED
VEHICLE_ONLY={'ZVehicleChaseEffects','HavokCarScriptRout','VehicleExitBehaviourRout','VehicleMoveOnRoadBehaviourRout',
              # init looks for a ZHavokCar among the owner's siblings and falls back to itself (kl2 0x7d90f0) -> M07 AV 0x7f0f42
              'VehicleAudioPosBox','VehicleWeapon','MountedWeapon'}
# ANP_FAILSAFE13B (default on): ZVehicleFailSafe13B (M13B Specials!VehicleEffects!FailsafeBox) init (kl2 0x62dec0,
# slot 14) takes [ref group's VehicleEffects event +0xb94] = the ZHavokCar that ZVehicleEffects init (0x7c6f00) finds
# among the group's direct children; with DM's ZHavokCar neutralised to ZSTDOBJ it is 0, and its update (0x415870 ->
# 0x8ba450) reads car+0x840 unchecked -> M13B AV 0x8ba454 (read 0x840). Only drives the MF_15_CarCrash fail screen.
# If cars are ever converted to real ZHavokCar, keep it when the referenced group is a car owner with VehicleEffects.
if os.environ.get('ANP_FAILSAFE13B','1')=='1': VEHICLE_ONLY.add('ZVehicleFailSafe13B')
PASS_UNVERIFIED={'LeapFrogBehaviourRout'}   # vehicle routs need DM vehicles (0x1004b4) converted to ZHavokCar first; ZProxySquad becomes a one-entry ZFusionSquad in node() (passed through, it crashed squad init; no DD level stores one)
# Player filters. The .prp stores enum NAMES; the two exes number them the other way round (player one = Kane in Dead
# Men, Lynch in Dog Days), and each class's handler decides whether the number or the name carries the meaning
# (checked per handler, 11 Oct; "P1" = gameMgr+0x828 / GetPlayer(0), the single player):
#  ECoopPlayerSetting  DM BOTH 0, KANEONLY 1, LYNCHONLY 2, NOONE 3 | DD BOTH 0, LYNCHONLY 1, KANEONLY 2, NOONE 3
#    TriggerBox (DM 0x69fff0, kl2 0x42afd0): by NUMBER in both: 1 = P1 (any player in single player), 2 = co-op P2
#      (never fires in single player), 3 = counts like BOTH in single player (box off in co-op) -> swap the names.
#      Without it every Dead Men "Kane only" box (M01: 31, CP_01 checkpoint, MakeVulnerable, pacing, BreakNose, bustout
#      music) is dead in single player and every co-op "Lynch only" box (M01: 19) fires.  ANP_ECPS_SWAP=0: old names.
#    CamOscillator (DM 0x6babf0, kl2 0x8d1a70): Dog Days kept the NAME (KANEONLY -> GetPlayer(0)) -> not swapped.
#    PlayerMovementModifier (DM 0x6b7bc0, kl2 0x8c4d20): by number, but kept inert (M01 KaneLimpStartStop: the
#      eMOVEMENT_M01 bit, kl2 player+0x63c -> +0x1f00, is untested in Dog Days).
#  EPlayerFilter  DM eONLY_KANE 0, eONLY_LYNCH 1 | DD eONLY_LYNCH 0, eONLY_KANE 1 (eBOTH_PLAYERS 2, eNO_PLAYERS -1 both)
#    by NUMBER (0 = P1, 1 = co-op P2 / never in single player): CCameraBox (DM 0x698a70, kl2 0x68a410), SneakTrigger
#      (0x6b0280, 0x430580), PlayerAction (kl2 0x40ddf0), ZFFItemWeapon pickups (geom 0x10048a, kl2 0x613309),
#      IngameBriefing 0x6b9200 = kl2 OnscreenMessage 0x4a4070 -> swap (ANP_PFILTER_SWAP=0: old names).
#    TriggerPsychoMode (DM 0x627a00, kl2 0x761270): Dog Days kept the NAME -> not swapped. SquadCommandTrigger
#      (unverified) untouched. PlayerMonitor: by NUMBER too (DM 0x6b8f80 +0x30: 0 = GetPlayer(0); kl2 0x589600 +0x34:
#      0 = 0x432a20, 1 = 0x8b60a0, else any) -> swapped with ANP_PLAYERMON=1 (0: old conversion, name kept).
ECPS_SWAP={'ECPS_KANEONLY':'ECPS_LYNCHONLY','ECPS_LYNCHONLY':'ECPS_KANEONLY'}
ECPS_BY_NUMBER={'TriggerBox','EndOfLevelTrigger'}
PF_SWAP={'eONLY_KANE':'eONLY_LYNCH','eONLY_LYNCH':'eONLY_KANE'}
PF_BY_NUMBER={'CCameraBox','SneakTrigger','PlayerAction','OnscreenMessage',
              'Objective'}   # LevelSetup::ZObjective +0x44 (kl2 0x66cad0 / 0x714e10: 0,2 = GetPlayer(0); 1,2 = GetPlayer(1))
PF_GEOM_BY_NUMBER={0x10048a}
# ANP_PA_GENERIC (default on): converted PlayerActions get Dog Days' story values for its two new enums (every stock L
# level: eNoFilter, UA_GENERIC; tools/climbs.py too). The statistical default was the Fragile Alliance pair eOnly_Mercs /
# UA_FA_ESCAPE: kl2 0x550c64 runs such an action at once (0x837320, no use animation) on input 0x1c and 0x8c8b79 makes
# it usable again after every use; UA_GENERIC takes the use input (8) and the animated path (0x62fbd0 / 0x6962e0).
PA_GENERIC={'eOnly_Mercs':'eNoFilter','eOnly_Police':'eNoFilter','UA_FA_ESCAPE':'UA_GENERIC'}
# ANP_BRIEFINGS (default on): DM IngameBriefing [StartVisible b, MaxTriggers I, TextKey s, EPlayerFilter e, Pause b]
# -> DD OnscreenMessage [TextKey, StartVisible, MaxTriggers, filter, Pause, EOnscreenMessageButton, b, AnimateIcon,
# targets] (same class with fields moved: both register "AITrigger"; handler DM 0x6b9570 = kl2 0x4cee70, show/hide DM
# 0x6b9200 = kl2 0x4a4070: each AITrigger while count < MaxTriggers toggles show/hide, no timeout). Senders unchanged
# (every DM sender sends AITrigger to the owner entity, which keeps the event). Pause forced 0 (only M03A's co-op
# command hint sets it; kl2 reads the button/bool only in pause mode). Text keys resolve as is (kl2 0x4099f0 tries
# key_pcgc/key_pc/key, the tree walk skips a leading '/'). Hints for features Dog Days lacks are dropped (BRIEF_DROP:
# objective locator, squad commands, merc swap/targeting, giving weapons, crew ammo) and raw debug strings (no '/').
# ANP_HINTS2 (default 1; 0 = the out_rel6 output byte for byte; PLAN item 4): three more hint kinds are converted, with
# their LOC text rewritten for Dog Days / the loader (locconv.hints2_fix): ObjectiveLocator (M01 2, M02 2, M03 1;
# {IngameMapActive} -> Dog Days' {HoldObjective}, the O key), LynchTargetSniper (M06 2; {HoldAttack} -> the squad.inc
# attack key) and GiveLynchShotgun / GiveLynchSidearm (M02 2; new text naming give.inc's key, label ANP_GIVE_KEY_LABEL,
# default 4). Whether holding O re-shows / turns to the objective in single player is not yet seen in game.
HINTS2=os.environ.get('ANP_HINTS2','1')=='1'
GIVE_KEY_LABEL=os.environ.get('ANP_GIVE_KEY_LABEL','4').strip() or '4'
BRIEF_DROP=tuple(x for x in ('ObjectiveLocator','_Commands','SwapMercs','LynchTargetSniper','GiveLynch','190_AmmoInfo')
                 if not (x=='_Commands' and BRIEF_COMMANDS)        # ANP_BRIEF_COMMANDS: crew orders exist (squad.inc)
                 and not (HINTS2 and x in ('ObjectiveLocator','LynchTargetSniper','GiveLynch')))
# ANP_OBJECTIVES (default on): DM Ingamemap [IconType e, Target s, StartActive b, TextKey s, Announce b, filter e,
# Repeatable b, b, CameraPos s, CameraTarget s, f] -> DD Objective (LevelSetup::ZObjective) [StartActive b,
# EObjectiveStatus e, TextKey s, owner geom is target b, turn camera b, popup seconds f, filter e], laid out like
# L02's GetToVan. kl2 0x8b2890: an AITrigger adds the text to the objective list (gameMgr+0x48b8) + popup, the next
# removes it (DM: 1st adds, 2nd removes, later ignored unless Repeatable -> in Dog Days a 3rd trigger re-adds and
# Repeatable ones toggle). Announce=0 -> popup 0.001 s (<= 0 would mean 8 s). Icon/target/map camera dropped (no map
# or markers in Dog Days); empty-text ones dropped (an empty text clears the popup). ObjectiveReminder (re-shows the
# current objective, DM 0x6a1ef0) has no Dog Days equivalent and stays dropped.
def dm_hud_event(name, evp, rep, briefings, objectives):
    """DM IngameBriefing / Ingamemap / ObjectiveReminder -> [(dd event name, ops)] ([] = drop); None = not handled"""
    if name not in ('IngameBriefing','Ingamemap','ObjectiveReminder'): return None
    if name=='ObjectiveReminder':
        if not objectives: return None
        rep['event dropped (no Dog Days equivalent) ObjectiveReminder']+=1; return []
    kinds=[op&0x7f for (_,op,_) in evp]; vals=[v for (_,_,v) in evp]
    if name=='IngameBriefing':
        if not briefings: return None
        if kinds!=[6,9,12,14,6]: rep['IngameBriefing unexpected layout %s -> dropped'%kinds]+=1; return []
        start,maxt,key,filt,_pause=vals
        if '/' not in key: rep['IngameBriefing dropped (raw text) %r'%key[:40]]+=1; return []
        hit=next((d_ for d_ in BRIEF_DROP if d_ in key),None)
        if hit: rep['IngameBriefing dropped (no Dog Days feature: %s) %s'%(hit,key)]+=1; return []
        rep['IngameBriefing -> OnscreenMessage %s'%key]+=1
        return [('OnscreenMessage',[(0,12,key),(0,6,start),(0,9,maxt),(0,14,filt),(0,6,0),
                                    (0,14,'eBUTTON_USE'),(0,6,0),(0,14,'eICON_NONE'),(0,4,0)])]
    if not objectives: return None
    if kinds!=[14,12,6,12,6,14,6,6,12,12,10]: rep['Ingamemap unexpected layout %s -> dropped'%kinds]+=1; return []
    _icon,_tgt,start,key,announce,filt,repeat,_b49,_cpos,_ctgt,_f=vals
    if not key: rep['Ingamemap dropped (empty text)']+=1; return []
    if repeat: rep['Ingamemap Repeatable (toggles in Dog Days) %s'%key]+=1
    rep['Ingamemap -> Objective %s'%key]+=1
    return [('Objective',[(0,6,start),(0,14,'eOS_NEW'),(0,12,key),(0,6,1),(0,6,0),
                          (0,10,8.0 if announce else 0.001),(0,14,filt)])]
# ANP_CP_INDEX (default on): kl2's checkpoint save (0x8ae950) asserts 1 <= index <= 254 with an int3 that ends the
# game; Dead Men never reads the index at save time and uses 0 (M06 x3, M07, M08, M12 x5). A level with an index
# outside 1..254 gets 1..n in (Dead Men index, number in the entity name, scene order) order. kl2 also skips the
# save (it only fires the targets) for a checkpoint below the one already reached ([0xe0e640]+0xa6c).

def _zdefines(out, k):
    """{define name: count} over every ZSetZDefine event in a converted op list (events are (12,name),(2,..)..)"""
    c=collections.Counter()
    for i in range(k,len(out)-1):
        if out[i][1]&0x7f==12 and out[i][2]=='ZSetZDefine' and out[i+1][1]&0x7f==2:
            j=i+2
            while out[j][1]&0x7f!=0x7e:
                if out[j][1]&0x7f==12: c[out[j][2]]+=1; break
                j+=1
    return c

def check_defines(out, k, rep, names):
    c=_zdefines(out, next(i for i,(p,op,v) in enumerate(out) if op&0x7f==2))
    for nm in names: rep['define %s x%d'%(nm,c[nm])]+=1
    bad=[nm for nm in ('BackgroundFrame','BackgroundFrame2') if c[nm]!=1]
    # ten displays look these up with no null check (a missing one crashes); a duplicate resolves to the first
    if bad: raise SystemExit('defines %s must resolve exactly once: %s'%(bad,[c[x] for x in bad]))

def reroot_osd(out, k, dm_root, gr, D, rep):
    """Point every live path into Dead Men's FFOsdMP1 at the grafted Dog Days copy, except inside Dead Men's (inert)
    subtree itself. Paths the Dog Days copy does not have (Dead Men's IngameMapGroup) are left alone."""
    from graft import node_spans
    G=D.G
    dr=next(e for e in G.ents if e['name']==OSD_ZIP)
    pre_d=[]; e_=dr
    while e_['parent']!=-1: e_=G.ents[e_['parent']]; pre_d.append(e_['name'])
    assert pre_d==['AllLevels/mainsceneincludes.zip'],pre_d          # donor path = Dead Men path
    valid={''}; stack=[]
    for e_ in G.ents[dr['i']+1:]:
        if e_['depth']<=dr['depth']: break
        stack=stack[:e_['depth']-dr['depth']-1]+[e_['name']]; valid.add('\\'+'\\'.join(stack))
    assert OSD_ZIP in gr['heads'],gr['heads']
    new=gr['prefix']+OSD_ZIP
    tk=next(i for i,(p,op,v) in enumerate(out) if op&0x7f==2)
    spans,_=node_spans(out,tk)
    node=dm_root+1+(gr['nnew'] if dm_root>=gr['end'] else 0)
    s0,s1=spans[node]
    inside=sum(1 for a,b in spans if s0<=a<s1)
    def fix(v,note=True):
        if not isinstance(v,str) or not (v==OSD_PATH or v.startswith(OSD_PATH+'\\')): return v,0
        rel=v[len(OSD_PATH):]
        if rel in valid: return new+rel,1
        if note: rep['OSD path left on Dead Men copy %s'%rel]+=1
        return v,0
    nfix=0; nin=0
    for i,(p_,op_,v_) in enumerate(out):
        b=op_&0x7f
        if b not in (12,15): continue
        if s0<=i<s1:
            if (b==12 and fix(v_,False)[1]) or (b==15 and any(fix(x,False)[1] for x in v_)): nin+=1
            continue
        if b==12:
            nv,c=fix(v_)
            if c: out[i]=(p_,op_,nv); nfix+=1
        else:
            r=[fix(x) for x in v_]
            if any(c for _,c in r): out[i]=(p_,op_,[x for x,_ in r]); nfix+=sum(c for _,c in r)
    rep['OSD live paths re-rooted to grafted FFOsdMP1 %d (left inside inert DM copy %d, its nodes %d)'%(nfix,nin,inside)]+=1

def dm_font_hook(ops, k, names, parent, depth, dm_osd_root, dm_prm, rep):
    """graft font_hook: Dead Men's fonts (FFOsdMP1.zip\\AllLevels/FFFonts.zip\\<name>, made inert in place) converted to
    the Dog Days layout (tools/dmfont.py) for the grafted Dog Days font entities, by DM_FONT_MAP."""
    import dmfont
    from graft import node_spans, _obj_end
    spans,_=node_spans(ops,k)
    toff,cnt=struct.unpack_from('<II',dm_prm,0)
    def chunk(i):
        o,s=struct.unpack_from('<II',dm_prm,toff+16*i); return dm_prm[o:o+s]
    dm={}
    j=dm_osd_root+1
    while j<len(names) and depth[j]>depth[dm_osd_root]:
        if parent[j]!=-1 and names[parent[j]]=='AllLevels/FFFonts.zip':
            p0=spans[j+1][0]; p1=_obj_end(ops,p0)
            ids=[v for (p_,op_,v) in ops[p0:p1] if op_&0x7f==9 and isinstance(v,int) and 0<v<cnt and dmfont.parse_dm(chunk(v))]
            if len(ids)==1: dm[names[j]]=ids[0]
            else: rep['DM font %s: %d font chunks (skipped)'%(names[j],len(ids))]+=1
        j+=1
    rep['DM fonts found: %s'%', '.join('%s=%d'%kv for kv in sorted(dm.items()))]+=1
    fill=os.environ.get('ANP_DM_FONT_FILL','1')=='1'
    prefer=_cp_set(os.environ.get('ANP_DM_FONT_DD',''))
    def hook(name, dd_chunk):
        src=DM_FONT_MAP.get(name)
        if src not in dm:
            rep['DM font for Dog Days %s: none (%s) - Dog Days font kept'%(name,src)]+=1; return None
        data,r=dmfont.convert(chunk(dm[src]),dd_chunk,dd_fill=fill,dd_prefer=prefer)
        rep['DM font %s <- Dead Men %s (chunk %d): %d glyphs, %d kern, hdr %s, from Dog Days %d (private use %s)%s'%(
            name,src,dm[src],r['glyphs'],r['kern'],r['hdr'][:2]+r['hdr'][3:4]+r['hdr'][5:],len(r['dd_added']),
            ' '.join('%x'%c for c in r['dd_added'] if c>=0xe000) or '-',
            (', preferred %d'%len(r['dd_preferred'])) if r['dd_preferred'] else '')]+=1
        if r.get('c1_aliases'): rep['DM font %s: C1 alias glyphs %s'%(name,' '.join('%02x'%c for c in r['c1_aliases']))]+=1
        return data
    return hook

def port(dm_folder, dm_name, new_id, donor='L01', report=None):
    rep=report if report is not None else collections.Counter()
    # Dog Days subtrees grafted from the donor (graft.py): menus, menu resources and (ANP_GRAFT_OSD) the HUD + fonts
    GNAMES=[x for x in os.environ.get('ANP_GRAFT_SUBTREE','AllLevels/Menu.zip,MenuResources'+(','+OSD_ZIP if GRAFT_OSD else '')+(','+DOCUCAM_ZIP if DOCUCAM else '')).split(',') if x]
    osd_graft=GRAFT_MENU and OSD_ZIP in GNAMES
    lay=scene_layout(dm_folder, dm_name, new_id)
    src_zip=os.path.join(lay['src_dir'],lay['src_stem']+'.zip')
    ents=read_zip(src_zip)
    byname={e.name.split('/')[-1]:e for e in ents}
    base=lay['src_stem']
    get=lambda ext: read_entry(byname[base+ext])
    # ---------- GMS + PRP ----------
    g=bytearray(load_gms_bytes(get('.gms')))
    buf=bytearray(get('.buf'))
    import math
    def conv_exits(off,n):
        # Dead Men portal record = 56 bytes; Dog Days = same 56 + oriented box (centre, half extents, axes) = 116
        nonlocal buf
        out=bytearray()
        for k in range(n):
            r=bytes(buf[off+k*56:off+(k+1)*56])
            v=struct.unpack_from('<12f',r)
            P=[v[0:3],v[3:6],v[6:9],v[9:12]]
            c=[sum(p[i] for p in P)/4 for i in range(3)]
            def sub(a,b): return [a[i]-b[i] for i in range(3)]
            def ln(a): return math.sqrt(sum(x*x for x in a))
            def nrm(a):
                l=ln(a); return [x/l for x in a] if l>1e-9 else [0.0,0.0,0.0]
            e1=sub(P[1],P[0]); e2=sub(P[2],P[1])
            a1=nrm(e1); a2=nrm(e2)
            nn=nrm([a1[1]*a2[2]-a1[2]*a2[1], a1[2]*a2[0]-a1[0]*a2[2], a1[0]*a2[1]-a1[1]*a2[0]])
            extra=struct.pack('<15f',*(c+[ln(e1)/2,ln(e2)/2,0.0]+nn+a2+a1))
            out+=r+extra
        while len(buf)%16: buf.append(0)
        newoff=len(buf); buf+=out
        return newoff
    prp=PRP(get('.prp'))
    # entity table
    h=list(struct.unpack_from('<20I',g))
    tab=h[0]; n=struct.unpack_from('<I',g,tab)[0]
    ents_off=[]; types=[]
    for i in range(n):
        decl,u4=struct.unpack_from('<II',g,tab+4+i*8); off=4*(decl&0xFFFFFF)
        ents_off.append(off); types.append(struct.unpack_from('<I',g,off+0x14)[0])
    dm_types=list(types)     # Dead Men's own types (types[] is rewritten below)
    neutral={}; remapped={}
    KEEP_PRIM={0x2000d4}|({0x2000fd} if PLANT=='static' else set())     # ANP_PLANT: static leaves
    # DM-only subclasses that have a direct Dog Days equivalent (same object size / data):
    #   ZIngameMapGroup (0x100486) derives from ZROOM and owns octree data in the .oct -> keep it a ZROOM
    TYPE_REMAP={0x100486:0x100021}
    from clusters import basetype_guess as _btg
    for i,t in enumerate(types):
        if t in TYPE_REMAP:
            nt=TYPE_REMAP[t]; remapped[i+1]=nt
            assert _btg(nt)==_btg(t),('type remap changes the pool slot',hex(t),hex(nt))
            struct.pack_into('<I',g,ents_off[i]+0x14,nt)
            rep['remapped geom %x -> %x'%(t,nt)]+=1
            types[i]=nt
        elif t in KEEP_DM:
            rep['kept Dead Men geom type (ANP_KEEP_DM_TYPES) %x'%t]+=1
        elif t not in DD_TYPES:
            nt=neutral_type(t)
            neutral[i+1]=nt
            struct.pack_into('<I',g,ents_off[i]+0x14,nt)
            keep_prim_=t in KEEP_PRIM
            if keep_prim_ and t==0x2000fd: rep['ZPlant leaves keep their prim (ANP_PLANT=static)%s'%('' if struct.unpack_from('<I',g,ents_off[i]+0x0c)[0] else ': prim is 0 in Dead Men')]+=1
            if not keep_prim_ and STATIC_SHADOWS!='off' and t==0x200110:
                no_=struct.unpack_from('<I',g,ents_off[i])[0]
                nm_=bytes(buf[no_:buf.index(b'\0',no_)]).decode('latin1')
                if STATIC_SHADOWS=='all' or __import__('re').search(r'_Chunk\d+$',nm_):   # (port() has its own later 'import re as _re')
                    keep_prim_=True
                    rep['static shadow mesh keeps its prim (ANP_STATIC_SHADOWS=%s)%s'%(STATIC_SHADOWS,
                        '' if struct.unpack_from('<I',g,ents_off[i]+0x0c)[0] else ': prim is 0 in Dead Men')]+=1
                else: rep['static shadow mesh not a _Chunk<n> (prim dropped)']+=1
            if not keep_prim_: struct.pack_into('<I',g,ents_off[i]+0x0c,0)
            rep['neutralised geom %x -> %x'%(t,nt)]+=1
            types[i]=nt
    # entities inside a neutralised DM-only group (e.g. DM vehicles 0x1004b4): their controllers need the real
    # class, so passthrough controllers are not kept there
    in_neut=set()
    _dep=[]; _path=[-1]
    for i in range(n):
        decl=struct.unpack_from('<I',g,tab+4+i*8)[0]; rd=decl>>25
        if rd: _path=_path[:len(_path)-rd]
        _dep.append(len(_path)-1)
        if decl&0x1000000: _path=_path+[i]
    for i in range(n):
        if (i+1) in neutral and neutral[i+1]==ZGROUP:
            j=i
            while True:
                in_neut.add(j+1); j+=1
                if j>=n or _dep[j]<=_dep[i]: break
    # Dead Men's in-game window tree (mainsceneincludes\Menu.zip\ZWINDOWS) is replaced by the grafted Dog Days
    # one; turn the DM copy inert IN PLACE (same group/basetype -> same pool slot -> no static node index moves).
    # Same for Dead Men's HUD (mainsceneincludes\FFOsdMP1.zip, except IngameMapGroup: a ZROOM the .oct counts, with
    # the IngameMapCamera0/1 defines) and its menu resources (Menu.zip\Menu_genericresources.zip: ZAddResourcesFrontend
    # GenericMenuResources / FAGenericMenuResources, InfoControllerFrame defines, OSD sound) when Dog Days' are grafted:
    # the OSD manager keeps only 2 displays (Dead Men's came first) and duplicate resource names resolve to the first.
    # A type is only swapped for one with the same pool slot (clusters.basetype_guess), so no node index moves.
    from clusters import basetype_guess as _btg
    neut_from=collections.Counter(); drop_ev=set(); dm_osd_root=None
    depth=[]; path=[-1]; names=[]; parent=[]
    for i in range(n):
        decl=struct.unpack_from('<I',g,tab+4+i*8)[0]; rd=decl>>25
        if rd: path=path[:len(path)-rd]
        depth.append(len(path)-1); parent.append(path[-1])
        if decl&0x1000000: path=path+[i]
        no=struct.unpack_from('<I',g,ents_off[i])[0]; names.append(bytes(buf[no:buf.index(b'\0',no)]).decode('latin1'))
    def make_inert(r0, label, keep=()):
        j=r0; skip_below=None
        while True:
            if skip_below is not None and depth[j]<=skip_below: skip_below=None
            if skip_below is None and j!=r0 and names[j] in keep:
                skip_below=depth[j]; rep['DM %s kept live: %s'%(label,names[j])]+=1
            if skip_below is None:
                t=types[j]; drop_ev.add(j+1)
                # ZTTFONT goes too when Dog Days' fonts are grafted: Dead Men font chunks (20-byte glyphs) must not be
                # reachable by a bare-name lookup ('Text', 'Menu', ...; the first match wins)
                if t not in (0x20004f,0x400003,0x200046) and (t!=0x20003a or osd_graft):
                    nt=ZGROUP if (t & 0x100000) else 0x200002
                    if nt!=t and j+1 not in neutral:
                        if _btg(nt)!=_btg(t): rep['DM %s kept type %x (pool slot differs)'%(label,t)]+=1
                        else:
                            neutral[j+1]=nt; neut_from[t]+=1
                            struct.pack_into('<I',g,ents_off[j]+0x14,nt); struct.pack_into('<I',g,ents_off[j]+0x0c,0)
                            types[j]=nt; rep['DM %s neutralised %x -> %x'%(label,t,nt)]+=1
            j+=1
            if j>=n or depth[j]<=depth[r0]: break
    if os.environ.get('ANP_NEUTRAL_DM_ZWINDOWS','1')=='1' and GRAFT_MENU:
        roots=[i for i in range(n) if names[i]=='ZWINDOWS' and types[i]==0x100030]
        for r0 in roots: make_inert(r0,'ZWINDOWS')
    if osd_graft:
        hits=[i for i in range(n) if names[i]==OSD_ZIP and parent[i]!=-1 and names[parent[i]]=='AllLevels/mainsceneincludes.zip']
        assert len(hits)==1,('Dead Men FFOsdMP1',hits)
        dm_osd_root=hits[0]; make_inert(dm_osd_root,'FFOsdMP1',keep=('IngameMapGroup',))
        hits=[i for i in range(n) if names[i]=='AllLevels/Menu_genericresources.zip' and parent[i]!=-1 and names[parent[i]]=='AllLevels/Menu.zip']
        # OSDSoundDefinition stays live: its GetAudioDefinition is a .SND offset valid only in this level's bank
        # (the grafted Dog Days copy points into L01's bank; see fix_audio_defs)
        for r0 in hits: make_inert(r0,'Menu_genericresources',keep=('OSDSoundDefinition',))
        if not hits: rep['DM Menu_genericresources not found']+=1
    # recompute per-group pool counters (h[5]) for the new types
    from clusters import read_ents, compute_blocks, read_blocks, basetype_guess
    hh,eL=read_ents(bytes(g))
    old=read_blocks(bytes(g),hh); newb=compute_blocks(eL,basetype_guess)
    assert len(old)==len(newb),(len(old),len(newb))
    for bi,blk in enumerate(newb):
        struct.pack_into('<24I',g,h[5]+4+bi*96,*blk)
    rep['h5 blocks changed']=sum(1 for a,b in zip(old,newb) if a!=b)
    # pathfinder blob (h[13]) uses an older layout in Dead Men -> disable for now (size 0)
    # static overlap lists (h[6], CListUser): entries encode geom-node addresses; Dead Men nodes are
    # 0x70 bytes, Dog Days nodes 0x80 -> re-encode  v = idx*stride + 0x10 (low 3 bits are flags)
    if 0 < h[6] < len(g):
        o6=h[6]+4; n7=struct.unpack_from('<I',g,o6)[0]; i6=4; nconv=0
        while i6<n7:
            i6+=1                                   # slot head (0 in file)
            while True:
                v=struct.unpack_from('<I',g,o6+4*i6)[0]
                x=v&~7
                if x:
                    assert (x-0x10)%0x70==0,(hex(v),i6)
                    struct.pack_into('<I',g,o6+4*i6,((x-0x10)//0x70)*0x80+0x10 | (v&7)); nconv+=1
                i6+=1
                if v&1: break
        rep['overlap entries re-encoded (0x70->0x80 nodes)']+=nconv
    pf_blob=None
    if 0 < h[13] < len(g):
        from pfconv import convert_pf_dm_to_dd
        o13=h[13]; sz13=struct.unpack_from('<I',g,o13)[0]
        pf_blob=convert_pf_dm_to_dd(bytes(g[o13:o13+4+sz13]))
    # header stamp (DM: h16=-1,h17=stamp ; DD: h16=stamp, h17=-1)
    struct.pack_into('<II',g,0x40,0x194dccb,0xffffffff)
    # class stats table (h[4]) : drop unknown types, move counts to ZGROUP
    nt=struct.unpack_from('<I',g,h[4])[0]; tab4=[list(struct.unpack_from('<3I',g,h[4]+4+i*12)) for i in range(nt)]
    moved=collections.Counter(neutral.values())+collections.Counter(remapped.values())
    keep=[]
    for t,c,u in tab4:
        if t in DD_TYPES or t in KEEP_DM: keep.append([t,c,u])
        else: rep['h4 dropped %x'%t]+=1
    for r in keep:
        r[1]+=moved.get(r[0],0)-neut_from.get(r[0],0)
    # a stand-in type the level never used (e.g. 0x800001a) gets its own row; the table is rewritten in place, so it
    # must not grow (each such type replaces a dropped Dead Men row)
    have4={r[0] for r in keep}
    for t_,c_ in sorted(moved.items()):
        if c_ and t_ not in have4: keep.append([t_,c_,0]); rep['h4 added %x'%t_]+=1
    if len(keep)>nt: raise SystemExit('h4 class stats table would grow (%d -> %d rows)'%(nt,len(keep)))
    end=h[4]+4+nt*12
    newtab=struct.pack('<I',len(keep))+b''.join(struct.pack('<3I',*r) for r in keep)
    g[h[4]:end]=newtab
    # dynamic pools table (h[9]) is before h[4]; rewrite in place with padding
    n9=struct.unpack_from('<I',g,h[9])[0]; e9=[struct.unpack_from('<2I',g,h[9]+4+i*8) for i in range(n9)]
    k9=[e for e in e9 if e[0] in DD_TYPES or e[0] in KEEP_DM]
    for e in e9:
        if e[0] not in DD_TYPES and e[0] not in KEEP_DM: rep['h9 dropped %x'%e[0]]+=1
    blk=struct.pack('<I',len(k9))+b''.join(struct.pack('<2I',*e) for e in k9)
    blk=blk+b'\0'*(4+n9*8-len(blk))
    g[h[9]:h[9]+4+n9*8]=blk
    # converted pathfinder goes at the end (after the in-place table rewrites above)
    if pf_blob is not None:
        while len(g)%16: g.append(0)
        h[13]=len(g); struct.pack_into('<I',g,13*4,h[13]); g+=pf_blob
        rep['pathfinder converted (%d bytes)'%len(pf_blob)]+=1
    # ---------- PRP tree conversion ----------
    C=Conv(W+'/dd_db.pkl')
    ops=list(prp.instrs())
    k=next(i for i,(p,op,v) in enumerate(ops) if op&0x7f==2)
    defines=ops[:k]
    # add DD-only defines (SSAO) copied from donor if missing
    out=list(defines)
    pos=k; nobj=0
    gtypes=[0x100021]+types
    def take_obj(i):
        assert ops[i][1]&0x7f==2
        d=0; j=i
        while True:
            b=ops[j][1]&0x7f
            if b==2: d+=1
            elif b==0x7e:
                d-=1
                if d==0: return ops[i+1:j], j+1
            j+=1
    # ---- ANP_VEHICLE_RELAY plan (see the switch at the top): which nodes get a relay in place of a dropped vehicle
    # rout / PlayerEnterVehicleAction, and with which targets ----
    relay_nodes={}; peva_nodes=set(); relay_skip=set(); vr_path={0:'ROOT'}; vr_bypath=collections.defaultdict(list)
    # optional spec keys (see VEHICLE_RELAY_EXIT): per-relay delays, container edits, extra beams, van-only events
    relay_delay={}; ev_edits={}; extra_beams=[]; extra_timers=[]; vanonly_drop=False
    def _edit_cont(b_, k_, how_, ref_, where_):
        """b_ with ref_ added to ('+') / removed from ('-') the k_-th container (Dead Men layout); fails the build
        unless that container holds plain refs and ref_ is absent ('+') / present once ('-')"""
        out_=list(b_); seen_=-1; q_=0
        while q_<len(out_):
            if out_[q_][1]&0x7f==4:
                seen_+=1; c_=out_[q_][2]; it_=out_[q_+1:q_+1+c_]
                if seen_==k_:
                    if not all(o_[1]&0x7f==12 for o_ in it_): break
                    vals_=[o_[2] for o_ in it_]
                    if how_=='-':
                        if vals_.count(ref_)!=1: break
                        del out_[q_+1+vals_.index(ref_)]; nc_=c_-1
                    else:
                        if ref_ in vals_: break
                        out_.insert(q_+1+c_,(0,it_[0][1] if it_ else 12,ref_)); nc_=c_+1
                    out_[q_]=(out_[q_][0],out_[q_][1],nc_)
                    return out_
                q_+=1+c_
            else: q_+=1
        raise SystemExit('%s: container %d of %s: cannot %s %s'%(new_id,k_,where_,'add' if how_=='+' else 'remove',ref_))
    def apply_edits(idx_, name_, b_):
        for en_,k_,how_,ref_ in ev_edits.get(idx_,()):
            if en_==name_: b_=_edit_cont(b_,k_,how_,ref_,'%s %s'%(name_,vr_path[idx_][5:]))
        return b_
    if VEHICLE_RELAY!='off':
        for i_ in range(n):
            vr_path[i_+1]=vr_path[parent[i_]+1]+'\\'+names[i_]
        for i_,p_ in vr_path.items(): vr_bypath[p_].append(i_)
        # every node's events (prp node = entity + 1; same walk order as node() below)
        nev_={}; p_=k; c_=[0]
        def _one():
            nonlocal p_
            me=c_[0]; c_[0]+=1
            _,p_=take_obj(p_)
            m_=ops[p_][2]; p_+=1; E_=[]
            for _ in range(m_):
                nm_=ops[p_][2]; p_+=1; b_,p_=take_obj(p_); E_.append((nm_,b_))
            nev_[me]=E_
            ch_=ops[p_][2]; p_+=1
            return ch_
        stk_=[_one()]
        while stk_:
            if stk_[-1]==0: stk_.pop(); continue
            stk_[-1]-=1; stk_.append(_one())
        def _res(s_):
            return vr_bypath.get(s_.rstrip('\\'),[]) if isinstance(s_,str) and s_.startswith('ROOT\\') else []
        def _car_group(t_):
            """node t_ is (or holds) a Dead Men ZHavokCar (all of them are neutralised)"""
            e_=t_-1
            if e_<0: return False
            if dm_types[e_]==0x2000d4: return True
            j_=e_+1
            while j_<n and depth[j_]>depth[e_]:
                if dm_types[j_]==0x2000d4: return True
                j_+=1
            return False
        if VEHICLE_RELAY=='exit':
            spec_=VEHICLE_RELAY_EXIT.get(new_id.upper(),{})
            for pth_,extra_ in spec_.get('routs',[]):
                h_=vr_bypath.get('ROOT\\'+pth_,[])
                if len(h_)!=1 or not any(e_ in VEHICLE_ROUTS for e_,_ in nev_.get(h_[0],[])):
                    raise SystemExit('ANP_VEHICLE_RELAY=exit: %s: no single vehicle rout at %s (found %s)'%(new_id,pth_,h_))
                relay_nodes[h_[0]]=['ROOT\\'+x for x in extra_]
            for pth_ in spec_.get('peva',[]):
                h_=vr_bypath.get('ROOT\\'+pth_,[])
                if len(h_)!=1 or not any(e_=='PlayerEnterVehicleAction' for e_,_ in nev_.get(h_[0],[])):
                    raise SystemExit('ANP_VEHICLE_RELAY=exit: %s: no single PlayerEnterVehicleAction at %s (found %s)'%(new_id,pth_,h_))
                peva_nodes.add(h_[0])
        else:
            spec_=VEHICLE_RELAY_EXIT.get(new_id.upper(),{})
            extra_by={}
            for pth_,extra_ in spec_.get('routs',[]):
                for h_ in vr_bypath.get('ROOT\\'+pth_,[]): extra_by[h_]=['ROOT\\'+x for x in extra_]
            for i_,E_ in nev_.items():
                if any(e_ in VEHICLE_ROUTS for e_,_ in E_): relay_nodes[i_]=extra_by.get(i_,[])
                for e_,b_ in E_:
                    if e_!='PlayerEnterVehicleAction': continue
                    # the vehicle path is the first string after the target container
                    ki_=[op_&0x7f for _,op_,_ in b_]; vv_=None
                    if ki_ and ki_[0]==4:
                        j_=1+b_[0][2]
                        vv_=next((b_[q_][2] for q_ in range(j_,len(b_)) if ki_[q_]==12),None)
                    if any(_car_group(t_) for t_ in _res(vv_)): peva_nodes.add(i_)
        def _one_node(pth_, what_):
            h_=vr_bypath.get('ROOT\\'+pth_,[])
            if len(h_)!=1: raise SystemExit('%s: %s: no single entity at %s (found %s)'%(new_id,what_,pth_,h_))
            return h_[0]
        for pth_,sec_ in spec_.get('delays',{}).items():
            o_=_one_node(pth_,'relay delay')
            if o_ not in relay_nodes and o_ not in peva_nodes: raise SystemExit('%s: relay delay on %s: not a relay'%(new_id,pth_))
            relay_delay[o_]=float(sec_)
        for pth_,en_,k_,how_,ref_ in spec_.get('edits',[]):
            o_=_one_node(pth_,'event edit'); _one_node(ref_,'event edit ref')
            if sum(1 for e_,_ in nev_.get(o_,[]) if e_==en_)!=1: raise SystemExit('%s: event edit: no single %s on %s'%(new_id,en_,pth_))
            ev_edits.setdefault(o_,[]).append((en_,k_,how_,'ROOT\\'+ref_))
        for i_ in list(ev_edits):     # check now, and let the loop check below see the edited message graph
            nev_[i_]=[(e_,apply_edits(i_,e_,b_)) for e_,b_ in nev_[i_]]
        for own_,act_ in spec_.get('beams',[]):
            extra_beams.append((_one_node(own_,'beam owner'),'ROOT\\'+act_)); _one_node(act_,'beam actor')
        for own_,sec_,ts_ in spec_.get('timers',[]):
            o_=_one_node(own_,'timer owner')
            # ANP_VEHICLE_RELAY=all also relays the timer's (dropped vehicle rout) node: that relay would send the
            # timer's targets at once and the 'timers' TriggerDelay would fire them again -> refuse the build
            if o_ in relay_nodes or o_ in peva_nodes:
                raise SystemExit('%s: timer owner %s is also a vehicle relay: use exit (ANP_VEHICLE_RELAY=%s)'%(new_id,own_,VEHICLE_RELAY))
            if any(e_=='TriggerDelay' for e_,_ in nev_.get(o_,[])): raise SystemExit('%s: timer owner %s already has a TriggerDelay'%(new_id,own_))
            for t_ in ts_: _one_node(t_,'timer target')
            extra_timers.append((o_,int(sec_),['ROOT\\'+t_ for t_ in ts_]))
        for x_ in spec_.get('require',[]): _one_node(x_,'required path')   # e.g. relay extras that must resolve
        vanonly_drop=bool(spec_.get('vanonly'))
        def _cont_refs(b_):
            out_=[]; q_=0
            while q_<len(b_):
                if b_[q_][1]&0x7f==4:
                    c__=b_[q_][2]; out_+=[v_ for _,op_,v_ in b_[q_+1:q_+1+c__] if op_&0x7f==12 and isinstance(v_,str)]
                    q_+=1+c__
                else: q_+=1
            return out_
        def relay_targets(owner, b_, extra):
            ts_=[]; drop_=collections.Counter()
            for s_ in _cont_refs(b_)+list(extra):
                h_=_res(s_)
                if not h_: drop_['names nothing']+=1; continue
                if owner in h_: drop_['itself']+=1; continue
                if any(t_>0 and dm_types[t_-1] in VEHICLE_RELAY_SKIP_TYPES for t_ in h_): drop_['road/spline/car']+=1; continue
                if s_ not in ts_: ts_.append(s_)
            return ts_,drop_
        # message graph of the level (every event reference + script reference; dropped vehicle routs and replaced
        # PlayerEnterVehicleActions count only through their relays): a relay whose node is reachable again from its
        # targets could loop, and is not written
        import re as _re2
        adj_=collections.defaultdict(set)
        for i_,E_ in nev_.items():
            for e_,b_ in E_:
                if e_ in VEHICLE_ROUTS or (e_=='PlayerEnterVehicleAction' and i_ in peva_nodes): continue
                for _,op_,v_ in b_:
                    vs_=v_ if (op_&0x7f==15 and isinstance(v_,list)) else [v_]
                    for s_ in vs_:
                        if not isinstance(s_,str): continue
                        if s_.startswith('(('): refs_=_re2.findall(r'ROOT\\[^|)]*',s_)
                        else: refs_=[s_]
                        for r_ in refs_:
                            for t_ in _res(r_.strip()): adj_[i_].add(t_)
        for o_,_,ts_ in extra_timers:     # 'timers' send too
            for s_ in ts_: adj_[o_].update(_res(s_))
        rt_={}
        for i_ in list(relay_nodes)+sorted(peva_nodes):
            ts_=set()
            for e_,b_ in nev_.get(i_,[]):
                if e_ in VEHICLE_ROUTS or (e_=='PlayerEnterVehicleAction' and i_ in peva_nodes):
                    for s_ in relay_targets(i_,b_,relay_nodes.get(i_,[]))[0]: ts_.update(_res(s_))
            rt_[i_]=ts_
        while True:
            def _loops(o_):
                seen_=set(); st_=list(rt_[o_])
                while st_:
                    x_=st_.pop()
                    if x_==o_: return True
                    if x_ in seen_: continue
                    seen_.add(x_); st_+=list(adj_.get(x_,()))+list(rt_.get(x_,()) if x_ not in relay_skip else ())
                return False
            bad_=[o_ for o_ in rt_ if o_ not in relay_skip and _loops(o_)]
            if not bad_: break
            relay_skip.add(bad_[0])
        for o_ in sorted(relay_skip):
            rep['vehicle relay SKIPPED (loop: its node is reachable from its targets) %s'%vr_path[o_].replace('ROOT\\','')[-90:]]+=1
        if relay_skip and VEHICLE_RELAY=='exit':
            # exit mode only plans relays on an exit chain: skipping one is a soft-lock, not a log line
            raise SystemExit('ANP_VEHICLE_RELAY=exit: relay on an exit chain skipped as a possible loop: %s'%
                             ', '.join(vr_path[o_].replace('ROOT\\','') for o_ in sorted(relay_skip)))
    elif new_id.upper()=='M07' and M07_TRUCK=='relay':
        # the M07 truck relay / timer / Blocker edit all live in the ANP_VEHICLE_RELAY plan: off = none of them
        rep['ANP_M07_TRUCK ignored (ANP_VEHICLE_RELAY=off)']+=1
    def relay_event(owner, b_, why):
        ts_,drop_=relay_targets(owner,b_,relay_nodes.get(owner,[]))
        for k__,v__ in drop_.items(): rep['vehicle relay target dropped (%s)'%k__]+=v__
        rep['vehicle relay (ANP_VEHICLE_RELAY=%s) %s node %d -> %d targets: %s'%(VEHICLE_RELAY,why,owner,len(ts_),
            vr_path[owner].replace('ROOT\\','')[-70:])]+=1
        if owner in relay_delay: rep['vehicle relay delay %g s on %s'%(relay_delay[owner],vr_path[owner].replace('ROOT\\','')[-70:])]+=1
        return ('RelayMessageList',[(0,12,'AITrigger'),(0,12,'AITrigger'),(0,4,len(ts_))]+[(0,12,s_) for s_ in ts_]
                +[(0,10,relay_delay.get(owner,VEHICLE_RELAY_DELAY))])
    # Merc ids (ANP_MERC_IDS, default on): one mapping per level for ZSoldier/ZMercSquad merc values and the scripts'
    # 'Actor| Merc_0N' sections (prpconv.Conv.set_mercs, scriptconv.convert). Without it every soldier was
    # No_Mercenary, every merc squad empty, and kl2's cutscene binder (0x4b64e0) killed every Dead Men cutscene that
    # names a merc (M01: the whole intro chain). Buddy = the merc of the soldier speaking as 'Lynch'.
    merc_digit=None; merc_buddy=None
    if os.environ.get('ANP_MERC_IDS','1')=='1':
        msold=[]
        for i_,(p_,op_,v_) in enumerate(ops):
            if op_&0x7f==12 and v_=='ZSoldier' and i_+1<len(ops) and ops[i_+1][1]&0x7f==2:
                b_,_=take_obj(i_+1)
                if [o_&0x7f for _,o_,_ in b_]==[14]*4+[10]*9+[9,12,14,6]: msold.append((b_[14][2],b_[15][2]))
        buddy=next((m_ for sp_,m_ in msold if sp_=='Lynch' and m_!='No_Mercenary'),'Merc_04')
        C.set_mercs(buddy); merc_buddy=buddy
        merc_digit={'Merc_%02d'%n_:C.merc_digit('Merc_%02d'%n_) for n_ in range(1,13)}
        mc_=collections.Counter(m_ for _,m_ in msold if m_!='No_Mercenary')
        for m_,c_ in sorted(mc_.items()):
            rep['merc %s (%s) -> %s = %s%s'%(m_,'/'.join(sorted(set(sp_ for sp_,mm_ in msold if mm_==m_))),C.merc(m_),merc_digit.get(m_),'' if c_==1 else ' DUPLICATE x%d'%c_)]+=1
    # InventoryBinding: Dog Days registers one binding per item enum -> keep one DM item per mapped DD item
    from prpconv import ITEM_MAP
    inv_items=[v for (p,op,v) in ops if op&0x7f==14 and isinstance(v,str) and v.startswith('eFF2Item') and not v.startswith('eFF2ItemType')]
    winners={}
    for v in sorted(set(inv_items), key=lambda x:(len(x),x)):
        tgt=ITEM_MAP.get(v,v)
        if tgt not in winners: winners[tgt]=v
    def fix_room(props):
        vals=split_values(props)
        sig=[v[0] for v in vals]
        # DD ZROOM: ... i(12)=#exits i8(13) i(14) e e e C(18) b b i(21)=exitOffset i(22)=neighbourOffset s i A3
        assert sig[12]=='i' and sig[13]=='i8' and sig[14]=='i' and sig[21]=='i' and sig[22]=='i', sig
        nex=vals[12][1][0][2]; exoff=vals[21][1][0][2]
        if nex>0 and exoff>0:
            newoff=conv_exits(exoff,nex)
            vals[21]=('i',[(0,vals[21][1][0][1],newoff)])
            rep['room exits converted']+=nex
        vals[13]=('i8',[(0,vals[13][1][0][1],0)])
        vals[14]=('i',[(0,vals[14][1][0][1],0)])
        vals[18]=('C{}',[(0,4,0)])
        vals[22]=('i',[(0,vals[22][1][0][1],0)])
        return [o for _,sl in vals for o in sl]
    # ---- extra ZDefine registrations Dog Days code looks up by name ----
    # template: first ZSetZDefine event body in the DM stream
    zdef_tpl=None
    for i,(p_,op_,v_) in enumerate(ops):
        if op_&0x7f==12 and v_=='ZSetZDefine':
            body,_=take_obj(i+1); zdef_tpl=body; break
    ent_names=[]
    for i in range(n):
        o=ents_off[i]; no=struct.unpack_from('<I',g,o)[0]
        ent_names.append(bytes(buf[no:buf.index(b'\0',no)]).decode('latin1'))
    # ANP_MERC_BYNAME (default on): rename a script's 'Actor| Merc_0N' only when a merc N is in its squad; otherwise
    # the binder matches it by group name and it must keep the name (M14 2MenLeft). scriptconv.squad_merc_values.
    # ANP_MERC_GROUPS (default on): such a kept 'Merc_0N' still hits kl2's digit check first and grabs the Dog Days
    # merc with value N (M14: the buddy Kane = 1 takes '2MenLeft\Merc_01'); the target groups are renamed
    # 'MercG0N' (name appended to .buf, entity name offset repointed) and the sections follow.
    # ANP_DM_SCRIPT_FIXES (default on): Dead Men scripts naming a group that does not exist (M14 Script_NearChurch
    # 'SpanishSoldier'), dead in Dead Men too; scriptconv.fix_dm_scripts patches them before everything below.
    from scriptconv import fix_dm_scripts
    fix_dm_scripts(ops, rep)
    merc_sq=None; merc_nm={}; script_owner={}; gren_={}
    if merc_digit and os.environ.get('ANP_MERC_BYNAME','1')=='1':
        from scriptconv import squad_merc_values
        merc_sq,merc_nm,gren_=squad_merc_values(ops,['ROOT']+ent_names,proxy=os.environ.get('ANP_PROXY','1')=='1',
                                               groups=os.environ.get('ANP_MERC_GROUPS','1')=='1')
        for gi_,nn_ in sorted(gren_.items()):
            e_=gi_-1; noff_=len(buf); buf+=nn_.encode('latin1')+b'\0'
            struct.pack_into('<I',g,ents_off[e_],noff_)
            rep['merc group renamed %s -> %s (node %d)'%(ent_names[e_],nn_,gi_)]+=1; ent_names[e_]=nn_
    # ANP_DUP_ACTOR_GROUPS (default on): a script with two Actor sections of one group name binds only the first (kl2
    # binder 0x4b64e0 re-binds a bound section; M12 FusionSquad_SmallTalk, dead in Dead Men too). The extra groups
    # get unique names (appended to .buf, node indices unchanged) and the scripts follow (scriptconv.dup_actor_groups).
    from scriptconv import dup_actor_groups
    dup_sec,dren_=dup_actor_groups(ops,['ROOT']+ent_names,rep,proxy=os.environ.get('ANP_PROXY','1')=='1',taken=set(gren_))
    for gi_,nn_ in sorted(dren_.items()):
        e_=gi_-1; noff_=len(buf); buf+=nn_.encode('latin1')+b'\0'
        struct.pack_into('<I',g,ents_off[e_],noff_); ent_names[e_]=nn_
    # ANP_ALLOC_POOLS (default on): Dead Men nests particle pools. The Shatter_Particle_Effects ZAllocMany has 5
    # baked clones; each clone holds 12 ZAllocMany templates (flag 0), and each of those has its own pool group at
    # ROOT level, but the 5 pools for one effect share a single name ('CloneGroup_ROOT/CloneGroup_Effects/Shatter/
    # ...'). The template's pool path is resolved by name (kl2 0x5edd90 -> 0x8863a0, first match), so only one of
    # the 5 pools gets linked (ZAllocMany stage 3, 0x48e1b0, writes clone+0x58 = template). Dog Days'
    # ZParticleEmitter stage 4 (vt slot 85, 0x4c63b0) reads parent clone->+0x58 with no null check -> M06/M07/M13/
    # M13B AV 0x4c63f2. Dead Men's emitter never reads it. Fix: pools 2..n get unique names (appended to .buf, node
    # indices unchanged) and the k-th template (entity order) on that path is pointed at the k-th pool.
    alloc_pools={}      # old path -> [pool entity index, ...] (entity order)
    alloc_newpath={}    # pool entity index -> new path
    alloc_seen=collections.Counter()
    if os.environ.get('ANP_ALLOC_POOLS','1')=='1':
        rootgrp=collections.defaultdict(list)
        for j in range(n):
            if parent[j]==-1 and types[j]&0x100000 and ent_names[j]:
                rootgrp[ent_names[j]].append(j)
        for nm_,js_ in rootgrp.items():
            if len(js_)<2: continue
            # only ZAllocMany pools (every child a ZAllocMany)
            kids_=[[c for c in range(n) if parent[c]==j_] for j_ in js_]
            if not all(k_ and all(types[c]==0x1000ca for c in k_) for k_ in kids_): continue
            alloc_pools['ROOT\\'+nm_]=js_
            for q_,j_ in enumerate(js_):
                nn_=nm_ if q_==0 else '%s#ANP%d'%(nm_,q_+1)
                if q_:
                    noff_=len(buf); buf+=nn_.encode('latin1')+b'\0'
                    struct.pack_into('<I',g,ents_off[j_],noff_); ent_names[j_]=nn_
                alloc_newpath[j_]='ROOT\\'+nn_
            rep['alloc pool name shared by %d pools -> made unique: %s'%(len(js_),nm_[-60:])]+=1
    EXTRA_EVENTS={}
    def zdefine(ent_name, define, nth=0):
        hits=[i for i,nm in enumerate(ent_names) if nm==ent_name]
        if len(hits)<=nth or zdef_tpl is None: rep['ZDefine target missing %s'%ent_name]+=1; return
        body=[(p_,op_,(define if isinstance(v_,str) else v_)) for (p_,op_,v_) in zdef_tpl]
        EXTRA_EVENTS.setdefault(hits[nth]+1,[]).append(('ZSetZDefine',body))
    # On-screen display frames (DD: FFOsdMP1\FrameForOsd[2]\Frame); DM has none -> without the grafted Dog Days HUD
    # (which brings them) reuse spare menu debug frames. Ten displays look these up with no null check: checked
    # after the graft that each resolves exactly once.
    if not osd_graft:
        zdefine('DebugFrame#17','BackgroundFrame')
        zdefine('DebugFrame#18','BackgroundFrame2')
    for own_,act_ in extra_beams:      # VEHICLE_RELAY_EXIT 'beams' (Dog Days ZBeamToPos layout = Dead Men's)
        EXTRA_EVENTS.setdefault(own_,[]).append(('ZBeamToPos',[(0,12,act_),(0,4,0)]))
    for own_,sec_,ts_ in extra_timers:  # VEHICLE_RELAY_EXIT 'timers' (Dog Days TriggerDelay, the converted layout)
        EXTRA_EVENTS.setdefault(own_,[]).append(('TriggerDelay',[(0,9,sec_),(0,9,0),(0,9,-1),(0,6,0),(0,4,len(ts_))]
                                                 +[(0,12,s_) for s_ in ts_]))
        rep['timer (VEHICLE_RELAY_EXIT timers) %d s on %s -> %d targets'%(sec_,vr_path[own_].replace('ROOT\\','')[-70:],len(ts_))]+=1
    # ANP_CAR_CHILD_EVENTS (default on): ZVehicleBroken's init (kl2 0x8c1160, slot 13) takes its vehicle from the
    # owner's DIRECT children (owner+0x40 / node+0x5e walk, class 0x2000d4 ZHavokCar) and never checks for none; its
    # update (0x758a00 -> 0x770010) and message handler (0x7a6060) then read vehicle+0x8c0/+0x968/+0xa65 -> with DM's
    # ZHavokCar neutralised to ZSTDOBJ, M03/M03B AV 0x770020 (read 0x8c0). Drop it when no live car child remains.
    CAR_CHILD_EVENTS={'ZVehicleBroken'}
    car_owners={parent[j]+1 for j in range(n) if types[j]==0x2000d4 and parent[j]>=0}
    car_child_drop=os.environ.get('ANP_CAR_CHILD_EVENTS','1')=='1'
    # ANP_APPENDAGE_LINK (default on): DD ZAppendage needs a ZLNKOBJ link target. Init (kl2 0x462590/0x763f00) checks,
    # Load (slot 22 0x833660 -> 0x8c6b70), run on EVERY checkpoint restore / level restart (0x5d5d80), does not -> AV
    # 0x8c6bbe when the target is DM's ZHavokCar neutralised to ZSTDOBJ (M03/M03B getaway-van doors).
    appendage_drop=os.environ.get('ANP_APPENDAGE_LINK','1')=='1'
    # ANP_APPENDAGE (default drop; keep = the old output, byte-identical): DD's ZAppendage (vt 0xbb1254) is Dead Men code
    # no stock DD level uses. Init 0x462590 registers it in the target's render instance (ZLNKOBJ+0x88) under the OWNER
    # GROUP's node (0x7e06c0 -> 0x5670d0), but the per-frame update (slot 25, 0x8cbe30) looks it up (0x5d1e50) by the
    # TARGET's own node -> -1, unchecked -> writes entry[-1] = inst-0x2c every frame: the 3x3 lands on the allocator
    # header and the position on inst+0..+0xc -> heap assert 0x4665dc at teardown (M01 4, M02 4, M09 12 events: the
    # heroes'/mercs' hand chains and pelvis ropes). Every Appendage event is dropped (after ANP_APPENDAGE_LINK's own
    # check, so M03/M03B keep that rule and its report line).
    # ANP_APPENDAGE_HIDE (default 1 with drop): without Init the chain/rope meshes would stay where the editor put them,
    # so every non-group descendant with a model under the dropped event's owner (GROUP_Apendage_*: PosBox_Dyn_COM,
    # PosBox_Dyn_Attach, Ground_Appendage_*) is made hidden at load the stock way: .gms flag 0x400 (node+0x3c bit 10,
    # the bit kl2's Activate/DeactivateGeom gate on, 0x4c4900 / 0x668160) plus ZGEOM[3]=1 (stock: 29664 of 29664
    # ZGEOM[3]=1 nodes carry 0x400, e.g. 13257 ZSTDOBJs; 718 stock ZLNKOBJ weapon Grounds load with 0x400). Type,
    # model and node order are unchanged. Not done when the link target was neutralised (a van door hangs where it is).
    APPENDAGE_MODE=os.environ.get('ANP_APPENDAGE','drop')
    assert APPENDAGE_MODE in ('drop','keep'),('ANP_APPENDAGE',APPENDAGE_MODE)
    app_hide=APPENDAGE_MODE=='drop' and os.environ.get('ANP_APPENDAGE_HIDE','1')=='1'
    app_hide_roots=set()     # node indices (entity + 1) of the dropped events' owners whose meshes get hidden
    neut_paths=set()
    if appendage_drop or APPENDAGE_MODE=='drop':
        _np={0:'ROOT'}
        for j_ in range(n): _np[j_+1]=_np[parent[j_]+1]+'\\'+names[j_]
        neut_paths={_np[i_] for i_ in neutral}
    ecps_swap=os.environ.get('ANP_ECPS_SWAP','1')=='1'
    pf_swap=os.environ.get('ANP_PFILTER_SWAP','1')=='1'
    pa_generic=os.environ.get('ANP_PA_GENERIC','1')=='1'
    briefings=os.environ.get('ANP_BRIEFINGS','1')=='1'
    objectives=os.environ.get('ANP_OBJECTIVES','1')=='1'
    cp_slots=[]     # (out index of a CheckPointSave's index value, Dead Men index, owner name)
    pm_count=[0]    # PlayerMonitor events written (kl2's monitor table holds 20 registered at once)
    def hide_at_load(newp, idx, t):
        # ANP_APPENDAGE_HIDE: ZGEOM[3] (4th top-level value, a bool) = 1 and .gms record +0x1c |= 0x400
        top_=[]; d_=0
        for q_,(p_,op_,v_) in enumerate(newp):
            o_=op_&0x7f
            if d_==0 and o_!=0x7c: top_.append(q_)
            if o_==1: d_+=1
            elif o_==0x7c: d_-=1
        if len(top_)<4 or newp[top_[3]][1]&0x7f!=6:
            rep['APPENDAGE_HIDE: ZGEOM[3] not a bool on %x %s (left shown)'%(t,ent_names[idx-1])]+=1; return newp
        q_=top_[3]; p_,op_,v_=newp[q_]
        newp=newp[:q_]+[(p_,op_,1)]+newp[q_+1:]
        fo_=ents_off[idx-1]+0x1c
        struct.pack_into('<I',g,fo_,struct.unpack_from('<I',g,fo_)[0]|0x400)
        rep['APPENDAGE_HIDE mesh hidden at load (.gms 0x400 + ZGEOM[3]=1) %x %s'%(t,ent_names[idx-1])]+=1
        return newp
    nodeidx=[0]
    def node():
        nonlocal pos, nobj
        idx=nodeidx[0]; nodeidx[0]+=1
        props,pos=take_obj(pos)
        t=gtypes[idx]
        if idx in neutral:
            nt=neutral[idx]
            vals=split_values(props)
            base5=[o for _,sl in vals[:5] for o in sl]
            sigs=C.db['sigg'][nt]
            if nt not in (ZGROUP,0x200002):
                # slot stand-ins (0x800001a): the layout whose containers are all empty (no list items)
                sigs={k_:v_ for k_,v_ in sigs.items() if all(x_=='C{}' for x_ in k_ if x_.startswith('C'))} or sigs
            sig=max(sigs,key=lambda k:sigs[k])
            tail=[]
            for j in range(5,len(sig)):
                d=C.default_for('g',nt,sig,j,sig[j]); assert d is not None,(nt,sig,j)
                tail+=d
            newp=base5+tail
        elif t in KEEP_DM:
            # ANP_KEEP_DM_TYPES: no Dog Days level statistics exist for these classes -> exact schema relayout only
            newp=C.keep_dm_geom(t,props)
            # raw Dead Men props would be read with the Dog Days schema: never ship that
            if newp is None: raise SystemExit('ANP_KEEP_DM_TYPES %x: exact relayout failed (%s, node %d)'%(t,new_id,idx))
            rep['kept Dead Men geom %x: exact relayout'%t]+=1
        else:
            newp=C.convert('g',t,props)
            if newp is None:
                rep['geom convert FAIL %x'%t]+=1; newp=props
        if t==0x100021:
            newp=fix_room(newp)
        if (alloc_pools and t==0x1000ca and len(newp)>=2 and newp[-1][1]&0x7f==12 and newp[-2][1]&0x7f==6
                and newp[-1][2] in alloc_pools):
            pp_,po_,pv_=newp[-1]; pools_=alloc_pools[pv_]
            if newp[-2][2]:     # clone: its own pool's (new) name; not used by the engine, kept consistent
                own_=parent[idx-1]
                if own_ in alloc_newpath: newp=newp[:-1]+[(pp_,po_,alloc_newpath[own_])]
            else:               # template: the k-th one links the k-th pool
                q_=alloc_seen[pv_]; alloc_seen[pv_]+=1
                if q_<len(pools_):
                    newp=newp[:-1]+[(pp_,po_,alloc_newpath[pools_[q_]])]; rep['alloc template retargeted']+=1
                else: rep['alloc template WITHOUT pool %s'%pv_[-50:]]+=1
        if pf_swap and t in PF_GEOM_BY_NUMBER and idx not in neutral:
            sw_=[v_ for (p_,op_,v_) in newp if op_&0x7f==14 and v_ in PF_SWAP]
            if sw_:
                newp=[(p_,op_,PF_SWAP[v_]) if (op_&0x7f==14 and v_ in PF_SWAP) else (p_,op_,v_) for (p_,op_,v_) in newp]
                for v_ in sw_: rep['player filter %s -> %s on geom %x'%(v_,PF_SWAP[v_],t)]+=1
        if app_hide_roots and idx>0 and not (t & 0x100000):
            a_=parent[idx-1]
            while a_>=0 and (a_+1) not in app_hide_roots: a_=parent[a_]
            if a_>=0 and struct.unpack_from('<I',g,ents_off[idx-1]+0x0c)[0]:
                newp=hide_at_load(newp,idx,t)
        out.append((0,2,None)); out.extend(newp); out.append((0,0x7e,None)); nobj+=1
        assert ops[pos][1]&0x7f==4; nev=ops[pos][2]; pos+=1
        evs=[]
        for e in range(nev):
            name=ops[pos][2]; pos+=1
            evp,pos=take_obj(pos)
            if idx in drop_ev:
                rep['event dropped on inert DM window %s'%name]+=1; continue
            if idx in ev_edits:
                evp=apply_edits(idx,name,evp); rep['event edited (VEHICLE_RELAY_EXIT edits) %s on %s'%(name,vr_path[idx][5:][-60:])]+=1
            # VEHICLE_RELAY_EXIT 'vanonly': van damage states / beams of a neutralised Dead Men car
            if vanonly_drop and name in ('ZSetGetawayDamageState','ZBeamToPos'):
                a_=next((v_ for (_,op_,v_) in evp if op_&0x7f==12 and isinstance(v_,str) and v_.startswith('ROOT\\')),None)
                if a_ is not None and any(_car_group(t_) for t_ in _res(a_)):
                    fw_=_cont_refs(evp)
                    if name=='ZBeamToPos' and fw_:
                        evs.append(('RelayMessageList',[(0,12,'AITrigger'),(0,12,'AITrigger'),(0,4,len(fw_))]+[(0,12,s_) for s_ in fw_]+[(0,10,0.0)]))
                        rep['van-only %s -> relay to its %d targets (vanonly)'%(name,len(fw_))]+=1; continue
                    rep['van-only %s dropped (vanonly)'%name]+=1; continue
            if name=='SceneChanger':
                old_=[v for (pp,op,v) in evp if op&0x7f==12]
                evp=[(pp,op,dd_scene_target(v)) if op&0x7f==12 else (pp,op,v) for (pp,op,v) in evp]
                rep['SceneChanger node %d: %s -> %s'%(idx,old_,[v for (pp,op,v) in evp if op&0x7f==12])]+=1
            if name=='ZProxySquad' and os.environ.get('ANP_PROXY','1')=='1':
                # DM proxy squad (one squad reference) -> DD one-entry ZFusionSquad, on disk exactly like DD's own
                # (04:1 0c:'ROOT\..', e.g. L02 AI!Friendly!Glazer_05A_DemolishedStreet). With no squad controller on
                # the parent, kl2 0x4aff50 leaves every rout below it with squad 0 and those routs never run (M01: the
                # merc never shoots the held alley cop, who stays in his invulnerable no-mode MiniCutscene).
                ref=[v for (pp,op,v) in evp if op&0x7f==12]
                if len(ref)==1:
                    evs.append(('ZFusionSquad',[(0,4,1),(0,12,ref[0])])); rep['ZProxySquad -> ZFusionSquad']+=1; continue
            # DM hints / mission objectives -> Dog Days OnscreenMessage / Objective on the same owner, so the senders'
            # AITrigger still reaches them (ANP_BRIEFINGS / ANP_OBJECTIVES, see dm_hud_event)
            hud_=dm_hud_event(name, evp, rep, briefings, objectives)
            if hud_ is not None:
                evs.extend(hud_); continue
            # ANP_PLAYERMON: one Dog Days PlayerMonitor per Dead Men event list (prpconv.Conv.player_monitor)
            if PLAYERMON and name=='PlayerMonitor':
                pm_=C.player_monitor(evp)
                if pm_ is not None:
                    evs.extend(('PlayerMonitor',x_) for x_ in pm_)
                    rep['PlayerMonitor (ANP_PLAYERMON) -> %d Dog Days events'%len(pm_)]+=1; continue
                rep['PlayerMonitor (ANP_PLAYERMON): unknown Dead Men layout, statistical conversion']+=1
            # owner itself neutralised too (DM ZHavokCar/ZHavokMountedWeapon/ZIKLNKOBJ/ZPlant/ZHFlow -> ZSTDOBJ): the
            # controller would use the owner as its real class (sweep 11 Oct: StartAnim calls owner vt+0x1e8/+0x200,
            # past ZSTDOBJ's vtable -> M05 EIP 0x3dcccccd; Vehicle/MountedWeapon read owner+0x840/+0x95c -> M11/M11B/
            # M12/M13 AV 0x65f903)
            # ANP_BUDDY_WEAPONFILTER (default pass): DM's buddy only gets guns through the inventory wheel (Kane gives
            # them; M02 020_GettingGuns). kl2 has no give mechanic, so a 'does Lynch hold X' check on the buddy (DM
            # layout: actor, weapon, bool 0, pass container, fail container) could never pass -> M02 soft-locked at the
            # weapons step. Forward its pass container instead. The bool-1 filters (pick a cutscene by his gun) stay.
            # ANP_GIVE=1 (loader give.inc puts the gun in his slot): default 'off' = the real filter is converted
            bwf_=os.environ.get('ANP_BUDDY_WEAPONFILTER','off' if os.environ.get('ANP_GIVE','1')=='1' else 'pass')
            if name=='WeaponFilter' and bwf_=='pass':
                k_=[op&0x7f for _,op,_ in evp]
                if (len(k_)>=4 and k_[:4]==[12,12,6,4] and evp[0][2] in ('ROOT\\Lynch','ROOT\\Lynch_COOP') and evp[2][2]==0
                        and len(evp)>=4+evp[3][2] and all(o_==12 for o_ in k_[4:4+evp[3][2]])):
                    ts_=[v_ for (_,_,v_) in evp[4:4+evp[3][2]]]
                    evs.append(('RelayMessageList',[(0,12,'AITrigger'),(0,12,'AITrigger'),(0,4,len(ts_))]+[(0,12,s_) for s_ in ts_]+[(0,10,0.0)]))
                    rep['buddy WeaponFilter -> pass relay (ANP_BUDDY_WEAPONFILTER) %s'%evp[1][2].split('\\')[-1]]+=1; continue
            elif name=='WeaponFilter':
                k_=[op&0x7f for _,op,_ in evp]
                if len(k_)>=4 and k_[:4]==[12,12,6,4] and evp[0][2] in ('ROOT\\Lynch','ROOT\\Lynch_COOP') and evp[2][2]==0:
                    rep['buddy WeaponFilter kept as a real filter (ANP_BUDDY_WEAPONFILTER=%s%s) %s'%(bwf_,', ANP_GIVE=1' if os.environ.get('ANP_GIVE','1')=='1' else '',evp[1][2].split('\\')[-1])]+=1
            if appendage_drop and name=='Appendage':
                tg_=[v for (pp,op,v) in evp if op&0x7f==12 and isinstance(v,str)]
                if any(t_.rstrip('\\') in neut_paths for t_ in tg_):
                    rep['event dropped (Appendage link target neutralised)']+=1; continue
            if APPENDAGE_MODE=='drop' and name=='Appendage':
                tg_=[v for (pp,op,v) in evp if op&0x7f==12 and isinstance(v,str)]
                rep['event dropped (ANP_APPENDAGE=drop) Appendage']+=1
                if app_hide and not any(t_.rstrip('\\') in neut_paths for t_ in tg_):
                    app_hide_roots.add(idx)
                    rep['Appendage dropped, meshes to hide under %s'%'\\'.join(names[j_] for j_ in (parent[idx-1],idx-1) if j_>=0)[-70:]]+=1
                continue
            if car_child_drop and name in CAR_CHILD_EVENTS and idx not in car_owners:
                rep['event dropped (owner has no ZHavokCar child) %s'%name]+=1; continue
            # ANP_VEHICLE_RELAY: a dropped vehicle rout / a get-in prompt on a neutralised van -> RelayMessageList
            if name=='PlayerEnterVehicleAction' and idx in peva_nodes and idx not in relay_skip:
                evs.append(relay_event(idx,evp,'PlayerEnterVehicleAction')); continue
            vrelay_=name in VEHICLE_ROUTS and idx in relay_nodes and idx not in relay_skip
            # ANP_KEEP_DM_TYPES: a VEHICLE_ONLY event the kept owner type itself drives (MountedWeapon on a kept 0x2000d7)
            keep_own_=bool(KEEP_DM) and idx not in neutral and idx not in in_neut and name in KEEP_DM_OWNER_EVENTS.get(gtypes[idx],())
            if keep_own_: rep['event kept on a kept Dead Men owner (ANP_KEEP_DM_TYPES) %s'%name]+=1
            if name not in C.db['sige'] and exact_event_ok(name) and (idx in in_neut or idx in neutral or (name in VEHICLE_ONLY and not keep_own_)):
                if vrelay_: evs.append(relay_event(idx,evp,name)); continue
                rep['event dropped (needs DM vehicle/neutralised owner) %s'%name]+=1; continue
            if name not in C.db['sige'] and exact_event_ok(name):
                bad=[v for (pp,op,v) in evp if op&0x7f==14 and isinstance(v,str) and v not in EXACT['enum_names']]
                if bad: rep['event %s passthrough: unknown enum %s'%(name,bad[0])]+=1
                evs.append((name,list(evp))); rep['event kept via exact schema %s'%name]+=1; continue
            if name not in C.db['sige']:
                if vrelay_: evs.append(relay_event(idx,evp,name)); continue
                rep['event dropped %s'%name]+=1; continue
            if name=='InventoryBinding':
                it=[v for (p,op,v) in evp if op&0x7f==14 and str(v).startswith('eFF2Item') and not str(v).startswith('eFF2ItemType')]
                if it:
                    tgt=ITEM_MAP.get(it[0],it[0])
                    if tgt!='eFF2ItemNoItem' and winners.get(tgt)!=it[0]:
                        rep['InventoryBinding dropped duplicate %s (->%s)'%(it[0],tgt)]+=1; continue
            r=C.convert('e',name,evp)
            if r is None: rep['event convert FAIL %s'%name]+=1; continue
            evs.append((name,r))
        for (xname,xops) in EXTRA_EVENTS.get(idx,[]):
            evs.append((xname,xops)); rep['extra event %s on node %d'%(xname,idx)]+=1
        # player filters (see ECPS_BY_NUMBER / PF_BY_NUMBER) and PlayerAction's Dog Days-only enums (PA_GENERIC)
        for k_,(nm_,r_) in enumerate(evs):
            tabs_=[]
            if ecps_swap and nm_ in ECPS_BY_NUMBER: tabs_.append(('ECPS',ECPS_SWAP))
            if pf_swap and (nm_ in PF_BY_NUMBER or (PLAYERMON and nm_=='PlayerMonitor')): tabs_.append(('player filter',PF_SWAP))
            if pa_generic and nm_=='PlayerAction': tabs_.append(('PlayerAction story enums',PA_GENERIC))
            for lab_,tab_ in tabs_:
                r_=evs[k_][1]
                if any(op_&0x7f==14 and v_ in tab_ for (p_,op_,v_) in r_):
                    for v_ in sorted(set(v_ for (p_,op_,v_) in r_ if op_&0x7f==14 and v_ in tab_)):
                        rep['%s %s -> %s on %s'%(lab_,v_,tab_[v_],nm_)]+=1
                    evs[k_]=(nm_,[(p_,op_,tab_[v_]) if (op_&0x7f==14 and v_ in tab_) else (p_,op_,v_) for (p_,op_,v_) in r_])
        # ANP_PLAYERMON_P2 (default drop): after the swap eONLY_KANE = co-op player two, which never fires in single
        # player; such monitors stay registered once switched on, and kl2's 20-slot monitor table (0x8ef000) has no
        # overflow check (cl=0xff 'full' is never caught -> the 21st registration writes past it; M02 had 22 events)
        if PLAYERMON and os.environ.get('ANP_PLAYERMON_P2','drop')=='drop':
            n0_=len(evs)
            evs=[(nm_,r_) for (nm_,r_) in evs if not (nm_=='PlayerMonitor' and any(op_&0x7f==14 and v_=='eONLY_KANE' for (_,op_,v_) in r_))]
            if len(evs)<n0_: rep['PlayerMonitor co-op player-two events dropped (ANP_PLAYERMON_P2)']+=n0_-len(evs)
        pm_count[0]+=sum(1 for (nm_,_) in evs if nm_=='PlayerMonitor')
        out.append((0,4,len(evs)))
        for name,r in evs:
            out.append((0,12,name)); out.append((0,2,None))
            if merc_sq is not None or dup_sec:
                for q_,(_,_,v_) in enumerate(r):
                    if isinstance(v_,str) and v_.startswith('(('): script_owner[len(out)+q_]=idx
            if name=='CheckPointSave':
                q_=next((q for q,(_,op_,_) in enumerate(r) if op_&0x7f==9),None)
                if q_ is not None: cp_slots.append((len(out)+q_,r[q_][2],ent_names[idx-1] if idx>0 else ''))
            out.extend(r); out.append((0,0x7e,None)); nobj+=1
        assert ops[pos][1]&0x7f==4; nch=ops[pos][2]; pos+=1
        out.append((0,4,nch))
        for c in range(nch): node()
    node()
    if pm_count[0]:
        rep['PlayerMonitor events in level %d%s'%(pm_count[0],' - WARNING: more than kl2 can register at once (20)' if pm_count[0]>20 else '')]+=1
    if cp_slots:
        rep['checkpoint indices (Dead Men) %s'%' '.join(str(v_) for _,v_,_ in cp_slots)]+=1
        if os.environ.get('ANP_CP_INDEX','1')=='1' and any(not (isinstance(v_,int) and 1<=v_<=254) for _,v_,_ in cp_slots):
            def _num(nm_):
                d_=__import__('re').findall(r'\d+',nm_); return int(d_[-1]) if d_ else 0
            order_=sorted(range(len(cp_slots)),key=lambda q:(cp_slots[q][1] if isinstance(cp_slots[q][1],int) else 0,_num(cp_slots[q][2]),q))
            for r_,q in enumerate(order_):
                o_,v_,nm_=cp_slots[q]; nv_=min(r_+1,254)
                out[o_]=(out[o_][0],out[o_][1],nv_)
                rep['checkpoint index %s -> %d (%s)'%(v_,nv_,nm_)]+=1
    for p_,js_ in alloc_pools.items():
        if alloc_seen[p_]!=len(js_): rep['alloc pools %d but templates %d: %s'%(len(js_),alloc_seen[p_],p_[-50:])]+=1
    assert ops[pos][1]&0x7f==0x7f, ops[pos]
    out.append(ops[pos])
    # animation databases: Dead Men names -> Dog Days databases present in the donor ANM
    for i,(p_,op_,v_) in enumerate(out):
        if isinstance(v_,str) and v_.startswith(ANMDB_PREFIX):
            db=v_[len(ANMDB_PREFIX):]
            if db in ANMDB_MAP and os.environ.get('ANP_ANM','dd')!='dm' and not (os.environ.get('ANP_ANM_MERGE','1')=='1' and db in ANM_OWN_DB):
                out[i]=(p_,op_,ANMDB_PREFIX+ANMDB_MAP[db]); rep['anim db %s -> %s'%(db,ANMDB_MAP[db])]+=1
    # mini-cutscene scripts: DM sections/commands -> DD ones. ANP_BUDDY_KANE (scriptconv): the buddy merc's Actor
    # section becomes Dog Days' Kane section (bound to gameMgr+0x4cf0, not through the squad); needs the merc ids
    # (the buddy's ZSoldier 'Kane' is what registers gameMgr+0x4cf0)
    from scriptconv import is_script, convert as conv_script
    for i,(p_,op_,v_) in enumerate(out):
        if isinstance(v_,str) and v_.startswith('((') and is_script(v_):
            own_=script_owner.get(i)
            nv=conv_script(v_, rep, merc_digit, merc_sq.get(own_) if (own_ is not None and merc_sq is not None) else None,
                           merc_nm.get(own_), buddy=merc_buddy, sec_map=dup_sec.get(own_))
            if nv!=v_: out[i]=(p_,op_,nv); rep['scripts converted']+=1
    for key,v in C.log.items(): rep['conv %s %s %s'%key]+=v
    for key,v in C.unresolved.items(): rep['UNRESOLVED %s'%(key,)]+=v
    # gun fit (tools/gunfit.py, ANP_GUNFIT): Dead Men gun models are turned/re-seated for Dog Days' handling clips in
    # build(); here (before the graft, node = entity + 1) the template Grounds drawing them get the inverse
    gunfit_plan={}
    if os.environ.get('ANP_GUNFIT','1')=='1':
        import gunfit
        gunfit_plan=gunfit.fix_prp(out,names,parent,types,[0]+[struct.unpack_from('<I',g,o_+0x0c)[0] for o_ in ents_off],
                                   gunfit.reference(W,DD_ROOT),rep)
    # Dog Days menu resources (fail screen, pause menu ... graphics) grafted from the donor level
    graft_res=dict(prm_extra=[],tex_extra=[]); hud=None
    if GRAFT_MENU:
        from graft import Donor, graft
        import zipfile as _zf
        dprm=_zf.ZipFile(os.path.join(DD_ROOT,'L01','L01_Main.zip')).read('Scenes/Locations/L01/L01_Main.prm')
        D=Donor(W+'/scn/dd/L01_Main', dprm, W+'/cache/L01_Main.TEX')
        dmtex=get('.TEX'); t1off=struct.unpack_from('<I',dmtex,0)[0]
        tex_used=set(i for i,x in enumerate(struct.unpack_from('<2048I',dmtex,t1off)) if x)
        prm_cnt=struct.unpack_from('<I',get('.prm'),4)[0]
        gnames=list(GNAMES)
        # Dead Men climb spots as a use prompt + Dog Days MiniCutscene playing Dead Men's climb clips (tools/climbs.py).
        # OFF by default since 11 Oct: in game it climbed twice, went through a wall and, with the squads live, threw
        # the player onto a roof. DM's climb is a free player move (any ledge 25..220 cm, see CLAUDE.md), so it is
        # being rebuilt in the loader instead.
        cpatch=None; csquads=None
        if os.environ.get('ANP_CLIMB','0')=='1':
            import climbs
            cspecs,cpatch=climbs.make_patch(new_id,rep)
            gnames+=cspecs
            nobj+=climbs.add_player_actions(new_id,out,k,ent_names,rep)
            csquads=climbs.squads_for(new_id)
        # grafted cameras' PostFilter events name a donor post-filter chunk (it indexes the donor's palette blob; the
        # index lands on an unrelated Dead Men chunk here) -> dropped (Dead Men's own menu cameras have none)
        strip=('PostFilter',) if os.environ.get('ANP_GRAFT_STRIP_PF','1')=='1' else ()
        fhook=dm_font_hook(ops,k,names,parent,depth,dm_osd_root,get('.prm'),rep) if (osd_graft and DM_FONTS) else None
        if osd_graft and DM_HUD:
            import dmhud
            hud=dmhud.HudPlan(ops,out,dmtex,rep,new_id)
        # ANP_COVERS (tools/coverconv.py): the cover-box prims are copied from the Dead Men .prm (graft._graft_tail)
        import coverconv
        coverconv.PRM_SRC=get('.prm') if coverconv.enabled() else None
        graft_res=graft(D,gnames,'ANP_DD_MenuResources',out,g,buf,prm_cnt,tex_used,rep,patch=cpatch,squads=csquads,
                        strip_events=strip,font_hook=fhook,osd_hook=hud.hook if hud else None)
        nobj+=graft_res['nobj']
        if cpatch: rep['climb targets resolved %d'%climbs.fix_targets(out,graft_res['prefix'])]+=1
        if osd_graft: reroot_osd(out,k,dm_osd_root,graft_res,D,rep)
    elif os.environ.get('ANP_COVERS','box').strip().lower() not in ('0','off','none',''):
        rep['covers: NOT added (ANP_COVERS needs the graft, ANP_GRAFT_MENU=1)']+=1
    fix_audio_defs(out,ops,get('.SND'),rep)
    check_defines(out,k,rep,('BackgroundFrame','BackgroundFrame2','MenuZWindows','MenuCam'))
    # scene settings preamble overrides (env ANP_SET="CameraFogBegin=0.98,CameraFogFull=0.99"; quotes that cmd's
    # `set ANP_SET="..."` keeps in the value are stripped)
    for kv in [x.strip().strip('"\'') for x in os.environ.get('ANP_SET','').split(',') if '=' in x]:
        key,val=(t.strip() for t in kv.split('=',1)); found=False
        for i_,(p_,op_,v_) in enumerate(out):
            if op_&0x7f==2: break
            if op_&0x7f==12 and v_==key:
                for j_ in range(i_+1,i_+8):
                    if out[j_][1]&0x7f==10: out[j_]=(out[j_][0],out[j_][1],float(val)); rep['setting %s=%s'%(key,val)]+=1; found=True; break
                break
        if not found: rep['setting NOT FOUND %s'%key]+=1
    # ANP_RAPPEL / ANP_RAPPEL_CB (tools/rappel.py, default both): kl2 gives the single player the SECOND half of a
    # RappellingBox's 8 callback containers, Dead Men the first -> Dead Men's player-one lists into both halves
    import rappel; rappel.fix_prp_out(out,rep)
    prp_bytes=write_prp(prp.tokens,prp.flags,prp.is_raw,nobj,out)
    # impact-material table (h[12] -> .buf): add the rows Dog Days code looks up by name
    from mattab import add_dd_rows
    if 0 < h[12] < len(buf):
        tb,added=add_dd_rows(buf,h[12])
        if added:
            while len(buf)%16: buf.append(0)
            h[12]=len(buf); struct.pack_into('<I',g,12*4,h[12]); buf+=tb
            rep['mattab rows added %s'%','.join(added)]+=1
    gms_bytes=gms_pack(bytes(g))
    # ---------- MAT ----------
    mat_bytes,na,nr=convert_mat_dm_to_dd(get('.MAT'))
    rep['mat arrays']=na; rep['mat records']=nr
    import matconv
    for k,v in matconv.LAST_H3.items(): rep['mat bucket %s'%k]+=v
    import re as _re
    anim_refs=set()
    for p_,op_,v_ in out:
        if isinstance(v_,str) and '/' in v_:
            if v_.startswith('/') and ' ' not in v_: anim_refs.add(v_)
            elif v_.startswith('(('):
                anim_refs.update(_re.findall(r'(/[A-Za-z0-9_][A-Za-z0-9_/\.\-]*)', v_))
    rep['anim paths referenced by the level %d'%len(anim_refs)]+=1
    return dict(gms=gms_bytes, prp=prp_bytes, mat=mat_bytes, buf=bytes(buf), ents=ents, byname=byname, graft=graft_res, anim_refs=anim_refs,
                audio_defs=[(v,en) for _,v,en in audio_defs(out)], gunfit=gunfit_plan, hud=hud.result if hud else None)

def audio_defs(seq):
    """GetAudioDefinition events in a prp op list -> [(op index of the uint, value, ESoundDefinitionType)]."""
    res=[]
    for i in range(len(seq)-2):
        p_,op_,v_=seq[i]
        if op_&0x7f==12 and v_=='GetAudioDefinition' and seq[i+1][1]&0x7f==2:
            j=i+2; iv=None; en=None
            while seq[j][1]&0x7f!=0x7e:
                b=seq[j][1]&0x7f
                if b==9 and iv is None: iv=j
                elif b==14 and en is None: en=seq[j][2]
                j+=1
            if iv is not None: res.append((iv,seq[iv][2],en))
    return res

def snd_list_ok(snd, off):
    """A GetAudioDefinition id is a byte offset into the level .SND that must hold a type-5 sound list (kl2 0x54dca0
    returns NULL otherwise and 0x8b1f00 -> 0x900ff0 reads [NULL+0x18]: the M01 v3 pause-menu crash). 0 = no sound."""
    if off==0: return True
    return 0<off<=len(snd)-0x1c and struct.unpack_from('<I',snd,off)[0]==5 and struct.unpack_from('<H',snd,off+0x18)[0]>0

def fix_audio_defs(out, src_ops, dm_snd, rep):
    """Audio definitions grafted from the Dog Days donor carry .SND offsets into the donor's bank. The .SND conversion
    keeps Dead Men's record offsets, so any definition that is not a sound list in Dead Men's bank gets the Dead Men
    level's own definition of the same type (eOSDInterface / eIngameMisc), else 0 (silent; 0x8b1f00 returns early)."""
    own={}
    for _,v,en in audio_defs(src_ops):
        if snd_list_ok(dm_snd,v) and v: own.setdefault(en,v)
    for iv,v,en in audio_defs(out):
        if snd_list_ok(dm_snd,v): continue
        nv=own.get(en,0)
        out[iv]=(out[iv][0],out[iv][1],nv)
        rep['audio definition %s %#x (not a sound list here) -> %#x'%(en,v,nv)]+=1

def load_gms_bytes(d):
    usz,fsz=struct.unpack_from('<II',d); return d[9:] if d[8] else zlib.decompressobj(-15).decompress(d[9:])

def oct_group_count(d):
    off=16; n=0
    while True:
        s=struct.unpack_from('<i',d,off)[0]
        if s==0: n+=1; off+=16; continue
        hdr=struct.unpack_from('<8I',d,off)
        if s==-1 or hdr[5]|hdr[6]|hdr[7]: break
        n+=1; off+=32+((s+15)&~15)
    assert n%5==0,n
    return n//5

def read_ents_types(gms_packed):
    g=load_gms_bytes(gms_packed)
    h=struct.unpack_from('<20I',g); tab=h[0]; n=struct.unpack_from('<I',g,tab)[0]
    ts=[]
    for i in range(n):
        decl,u4=struct.unpack_from('<II',g,tab+4+i*8); ts.append(struct.unpack_from('<I',g,4*(decl&0xFFFFFF)+0x14)[0])
    return h,ts


def patch_environments(prm, R, rep):
    """Dead Men's Environment lights (0x80000d) were tuned for a world that also had baked lighting; in Dog Days
    they light the bare world on their own, which comes out far too bright.  Dog Days levels use sun 0.3-0.7 and
    ambient ~0.2 luminance; Dead Men M01 uses 1.2 and ~0.43.  Scale world environments down (character ones a
    little).  Chunk: u32 c0000,0,0,type, colour, float intensity, 0, colour, ambient colour, ..."""
    from clusters import read_ents
    sun=float(os.environ.get('ANP_ENV_SUN','0.45')); amb=float(os.environ.get('ANP_ENV_AMB','0.55'))
    csun=float(os.environ.get('ANP_ENV_CHAR','0.9'))
    gg=load_gms_bytes(R['gms']); buf=R['buf']; hh,eL=read_ents(gg)
    off,cnt=struct.unpack_from('<II',prm,0)
    def scol(v,k):
        return (v&0xff000000)|(min(255,int(((v>>16)&255)*k))<<16)|(min(255,int(((v>>8)&255)*k))<<8)|min(255,int((v&255)*k))
    done=set()
    for e in eL:
        if e['type']!=0x80000d: continue
        f=struct.unpack_from('<16I',gg,e['off']); pr=f[3]
        if not (0<pr<cnt) or pr in done: continue
        nm=bytes(buf[f[0]:buf.index(b'\0',f[0])]).decode('latin1')
        o,sz=struct.unpack_from('<II',prm,off+16*pr)
        if sz!=48 or struct.unpack_from('<I',prm,o)[0]!=0xc0000: continue
        w=list(struct.unpack_from('<12I',prm,o))
        ch='har' in nm.lower()
        k=csun if ch else sun; ka=csun if ch else amb
        it=struct.unpack('<f',struct.pack('<I',w[5]))[0]
        w[5]=struct.unpack('<I',struct.pack('<f',it*k))[0]
        w[7]=scol(w[7],ka); w[8]=scol(w[8],ka)
        struct.pack_into('<12I',prm,o,*w); done.add(pr)
        rep['environment %s scaled'%('character' if ch else 'world')]+=1

def build(dm_folder, dm_name, new_id, donor='L01'):
    from anp_paths import game_running
    lay=scene_layout(dm_folder, dm_name, new_id)
    if os.path.normcase(os.path.abspath(lay['out_dir'])).startswith(os.path.normcase(os.path.abspath(DD_GAME))) and game_running():
        raise SystemExit('Dog Days (kl2.exe) is running: close it before building into its folder (or set ANP_OUT)')
    rep=collections.Counter()
    R=port(dm_folder, dm_name, new_id, donor, rep)
    # ANP_VALIDATE (default on, tools/ovlcheck.py): every Dead Men entity keeps its static node index, added entities
    # come after them, and every h[6] overlap reference still names the same entity (none newly pointing at an entity
    # without an overlap slot). Checked before anything is written.
    if os.environ.get('ANP_VALIDATE','1')=='1':
        from ovlcheck import check_or_die
        _base=lay['src_stem']
        check_or_die(load_gms_bytes(read_entry(R['byname'][_base+'.gms'])),load_gms_bytes(R['gms']),
                     read_entry(R['byname'][_base+'.buf']),rep,new_id)
    out_dir=lay['out_dir']; os.makedirs(out_dir,exist_ok=True)
    nb='Scenes/%s/%s'%(lay['rel'],lay['stem'])
    if lay['rel']!='Locations/'+new_id: rep['scene layout: %s -> %s (fxc alias lists tried: %s)'%(new_id,nb,', '.join('miss_%s.txt'%x for x in lay['fxc_ids']))]+=1
    donor_zip=read_zip(os.path.join(DD_ROOT,donor,donor+'_Main.zip'))
    dz={e.name:e for e in donor_zip}
    entries=[]
    src=R['byname']; base=lay['src_stem']
    def add_raw(srcname, newname):
        e=src[srcname]; e.name=newname; entries.append(e)
    def add_bytes(name,data,like):
        ne=entry_from_bytes(name,data,like=like); entries.append(ne)
    def clip_sounds(anm, az, de, src, base):
        # ANP_ANM_CLIPSND (default 'name', tools/clipsnd.py): ANM clip field 11 (+0x2c) is a PER-LEVEL .SND record
        # offset. The donor's (F03) clips carry F03 offsets that land on junk in our bank; kl2 0x5c8050 then reads a
        # list at base+0xcdcdcdcd (M12/M13 AV 0x5c8075). Re-point by record name, else 0 (409170 skips id 0).
        if os.environ.get('ANP_ANM_CLIPSND','name')=='off': return anm
        import clipsnd
        dsnd=next((read_entry(v) for k,v in az.items() if k.lower().endswith('_main.snd')),None)
        lsnd=next((read_entry(v) for k,v in src.items() if k.lower()==(base+'.snd').lower()),None)
        if dsnd is None or lsnd is None:
            rep['ANM clip sounds: no donor/level .SND, left as is']+=1; return anm
        if SND_IMPORT_DD and SND_MODE!='mute':
            # ANP_SND_IMPORT_DD: the clip ids are written after the .SND is built (records imported from the donor bank);
            # this pass only finds the donor records the clips need
            _imp_anm.update(pre=anm, donor_anm=read_entry(de), dsnd=dsnd, lsnd=lsnd, roots=set())
            return clipsnd.fix_clip_sounds(anm, _imp_anm['donor_anm'], dsnd, lsnd, collections.Counter(),
                                           unresolved=_imp_anm['roots'])
        return clipsnd.fix_clip_sounds(anm, read_entry(de), dsnd, lsnd, rep)
    _imp_anm={}        # ANP_SND_IMPORT_DD (clip_sounds -> the .SND stage)
    like=src[base+'.zgf']
    gunfit_bind=None   # tools/gunfit.py: set with the merged ANM, used on the .prm
    order=['.zgf','.prp','.sup','.buf','.HVK','.gms','.TEX','.MAT','.ANM']
    for ext in order:
        if ext=='.prp': add_bytes(nb+ext,R['prp'],like)
        elif ext=='.gms': add_bytes(nb+ext,R['gms'],like)
        elif ext=='.MAT': add_bytes(nb+ext,R['mat'],like)
        elif ext=='.buf': add_bytes(nb+ext,R['buf'],like)
        elif ext=='.TEX':
            st=convert_tex_dm_to_dd(read_entry(src[base+ext]),os.path.join(W,'_tex_out.bin'),extra=R['graft']['tex_extra']); rep['tex %s'%st]+=1
            ne=entry_from_bytes(nb+ext,open(os.path.join(W,'_tex_out.bin'),'rb').read(),level=1,like=like); entries.append(ne)
        elif ext=='.ANM' and os.environ.get('ANP_ANM','dd')=='dm':
            add_raw(base+ext, nb+ext); rep['ANM: Dead Men original (experiment)']+=1
        elif ext=='.ANM':
            # Dog Days' actor code looks animations up by DD names (/Cover/High/High/...), so the base is the
            # donor level's library; Dead Men's own clips (cutscenes, level-specific acting, climbing...) are
            # merged in (tools/anm_merge.py; format notes in ANM_FORMAT.md)
            az={x.name:x for x in read_zip(os.path.join(DD_ROOT,ANM_DONOR,ANM_DONOR+'_Main.zip'))}
            e=az['Scenes/Locations/%s/%s_Main.ANM'%(ANM_DONOR,ANM_DONOR)]
            if os.environ.get('ANP_ANM_MERGE','1')=='1':
                import anm_merge
                dmap={k:v for k,v in ANM_MERGE_MAP.items()}
                # Memory: kl2.exe is not large-address-aware and allocates the whole ANM (+0x60000) and then the
                # whole level .WAV; adding every Dead Men clip (+13 MB) starved the WAV (no sound at all).
                # Mapped databases only get the paths Dead Men's level actually needs: level-specific clips,
                # climbing, and every animation path the level's scripts/properties name.
                wanted=set(x.encode('latin1') for x in R.get('anim_refs',()))
                pf=None if os.environ.get('ANP_ANM_ALL')=='1' else (lambda p_: p_.startswith(b'/Level_Specific/') or p_.startswith(b'/Movement/Climb/') or p_ in wanted)
                # ANP_RAPPEL (tools/rappel.py, default 1): + Dead Men's /Movement/Rappelling/* for the player's rappel
                # movement (kl2 0x77ac70 looks them up in Kane's DB; without them 0x59d550 returns NULL -> crash)
                import rappel; pf=rappel.wrap_path_filter(pf)
                merged,mrep=anm_merge.merge_report(read_entry(e), read_entry(src[base+ext]), dmap, None, 'start', path_filter=pf)
                merged=rappel.ensure_player_clips(merged,rep)
                if os.environ.get('ANP_GUNFIT','1')=='1':
                    # every skeleton bone name onto the merged bone table (append-only) for the slot [8]/[9]/[10]
                    # rebinding in gunfit.apply_prm below
                    import gunfit
                    merged,gunfit_bind=gunfit.prepare_anm(merged,read_entry(src[base+ext]),read_entry(src[base+'.prm']),rep)
                merged=clip_sounds(merged,az,e,src,base)
                add_bytes(nb+ext, merged, like)
                for k,v in mrep['databases'].items(): rep['ANM merge %s -> %s (%s): +%d paths'%(k,v['into'],v['mode'],v['paths_added'])]+=1
                for k,v in mrep.get('backfill',{}).items(): rep['ANM backfill %s <- %s'%(k,v)]+=1
                rep['ANM merged: %d clips added, %d DBs, %d bytes'%(mrep['clips_added'],mrep['output']['dbs'],mrep['output']['size'])]+=1
            else:
                # ANP_ANM_MERGE=0: the donor library alone. ensure_player_clips can only point Kane/Lynch at
                # rappel lists the donor already has, and F03 has no /Movement/Rappelling/ path at all (Dead Men's
                # clips come in only through the merge), so the player cannot rappel natively in this mode: the
                # report says so and the bytes stay the donor's (rappel.inc refuses the native start, no crash).
                import rappel
                d_=read_entry(e); d2_=rappel.ensure_player_clips(d_,rep)
                if os.environ.get('ANP_ANM_CLIPSND','name')!='off':
                    add_bytes(nb+ext, clip_sounds(d2_,az,e,src,base), like)
                elif d2_ is not d_: add_bytes(nb+ext, d2_, like)
                else:
                    e.name=nb+ext; entries.append(e)
                rep['ANM from donor %s'%ANM_DONOR]+=1
        else: add_raw(base+ext, nb+ext)
    langs=['English','German','French','Spanish','Italian','Dutch','Russian','Polish','Japanese']
    # ANP_LOC_FIX (tools/locconv.py): Dead Men's icon tags renamed to the Dog Days tags for the same glyph, and its
    # cp1252 punctuation stored as U+0080..U+009F (shown as '_' by Dog Days) replaced by the real characters
    loc_fix=os.environ.get('ANP_LOC_FIX','1')=='1'
    # LOC additions (ANP_CHAPTER_TITLES, ANP_LOC_EXTREME, ANP_BRIEF_COMMANDS; see the switches at the top)
    loc_extra=CHAPTER_TITLES or LOC_EXTREME!='0' or BRIEF_COMMANDS or COVER_HINTS or HINTS2
    if loc_fix or loc_extra: import locconv
    title_key=(SPECIAL_SCENES.get(new_id.upper()) or {}).get('title_key') or dm_name
    PLAY=['AllLevels','Menu','Play']
    sq_keys=locconv.squad_keys(os.environ.get('ANP_SQUAD_KEYS','')) if BRIEF_COMMANDS else None
    def loc_additions(data, L, st):
        nodes=locconv.parse(data); adds=[]
        if CHAPTER_TITLES:
            t_=locconv.find(nodes,PLAY+[title_key+'_ChapterTitle'])
            if t_ is not None and t_[1]!=0x10 and t_[2]:
                adds+=[(PLAY+['L%02d_ChapterTitle'%c_],t_[2],t_) for c_ in range(1,12)]
                st['chapter title L01..L11 = %s_ChapterTitle %r'%(title_key,t_[2].decode('utf-8','replace'))]=1
            else: st['chapter title %s_ChapterTitle MISSING (no L01..L11 titles)'%title_key]=1
        if LOC_EXTREME=='plus':
            h_=locconv.find(nodes,PLAY+['Difficulty_Hard'])
            if h_ is not None and h_[1]!=0x10 and h_[2]:
                adds.append((PLAY+['Difficulty_Extreme'],h_[2]+b'+',h_)); st['Difficulty_Extreme = %r'%(h_[2]+b'+').decode('utf-8','replace')]=1
            else: st['Difficulty_Extreme: no Difficulty_Hard to name it after (not added)']=1
        elif LOC_EXTREME=='dd':
            x_=None
            for dl_ in (L,'English'):
                de_=dz.get('Scenes/Locations/%s/%s_Main%s.LOC'%(donor,donor,dl_))
                x_=locconv.find(locconv.parse(read_entry(de_)),PLAY+['Difficulty_Extreme']) if de_ else None
                if x_ is not None and x_[1]!=0x10 and x_[2]: break
                x_=None
            if x_ is not None:
                adds.append((PLAY+['Difficulty_Extreme'],x_[2],x_)); st['Difficulty_Extreme = %r (donor %s)'%(x_[2].decode('utf-8','replace'),dl_)]=1
            else: st['Difficulty_Extreme: not in the donor LOC (not added)']=1
        if adds: data,st=locconv.add_leaves(data,adds,st)
        if BRIEF_COMMANDS: data,st=locconv.map_texts(data,locconv.command_hint_fix(sq_keys,st),st)
        if COVER_HINTS:
            # the language of the text this LOC holds: Dead Men has no Dutch/Russian/Polish/Japanese LOC (English copies)
            t_,tl_=cover_hint_text(L if base+L+'.LOC' in src else 'English')
            if t_ is not None:
                hit_=[]
                def fn_(p_,s_):
                    if not COVER_HINT_KEYS.search(p_): return s_
                    hit_.append(p_.rsplit('/',1)[1]); return t_
                data,st=locconv.map_texts(data,fn_,st)
                if hit_: st['cover hints %s -> L01 %s %r'%(','.join(sorted(hit_)),tl_,t_)]=len(hit_)
            else: st['cover hints: no %s in L01 LOC (kept)'%'/'.join(COVER_HINT_DD)]=1
        if HINTS2:
            data,st=locconv.map_texts(data,locconv.hints2_fix(L if base+L+'.LOC' in src else 'English',
                                      sq_keys or locconv.squad_keys(os.environ.get('ANP_SQUAD_KEYS','')),GIVE_KEY_LABEL,st),st)
        return data
    _l01_loc={}
    def cover_hint_text(L):
        """Dog Days' TapCover hint (L01 /L01/IngameBriefing/L01_IngameBriefing_010_Cover) in language L, else English
        -> (text str or None, language used)"""
        if 'z' not in _l01_loc:
            _l01_loc['z']=dz if donor=='L01' else {e.name:e for e in read_zip(os.path.join(DD_ROOT,'L01','L01_Main.zip'))}
        for dl_ in (L,'English'):
            de_=_l01_loc['z'].get('Scenes/Locations/L01/L01_Main%s.LOC'%dl_)
            if de_ is None: continue
            try: x_=locconv.find(locconv.parse(read_entry(de_)),COVER_HINT_DD)
            except (AssertionError,IndexError,ValueError,struct.error): x_=None
            if x_ is not None and x_[1]!=0x10 and x_[2]:
                return x_[2].decode('utf-8'),dl_
        return None,None
    for L in langs:
        s=base+L+'.LOC'
        if s not in src: s=base+'English.LOC'
        if not loc_fix:
            if not loc_extra:
                if s==base+L+'.LOC': add_raw(s, nb+L+'.LOC')
                else: add_bytes(nb+L+'.LOC',read_entry(src[s]),like)
                continue
            st={}; data=read_entry(src[s])
        else:
            # squad icon tags only when the fonts carry Dead Men's 0xe012..0xe018 art
            sq=GRAFT_OSD and DM_FONTS and not (_cp_set(os.environ.get('ANP_DM_FONT_DD',''))&set(range(0xe012,0xe019)))
            st={}; data,st=locconv.convert(read_entry(src[s]),st,squad_icons=sq)
        if loc_extra: data=loc_additions(data,L,st)
        add_bytes(nb+L+'.LOC',data,like)
        for k_,v_ in st.items(): rep['LOC %s: %s'%(L,k_)]+=v_
    for x in ['guielems.xml','menu/ingame.xml','windows.xml','Menu/online.xml']:
        e=dz[x]; entries.append(e)
    # ANP_DM_HUD sidecar (tools/dmhud.py): OSD slot -> Dead Men art, for the loader's DM HUD widgets (stored)
    if R.get('hud'):
        entries.append(entry_from_bytes('Scenes/%s/ANP_hud.json'%lay['rel'],json.dumps(R['hud'],indent=1).encode(),
                                        compress=False,like=like))
    # .oct = per-ZTreeGroup compiled octrees (5 per group, in geom traversal order) + ZOctreeCompiled chain.
    # Dog Days walks one 5-octree record per ZTreeGroup-derived geom (+1 for the scene root ZROOM);
    # a mismatch makes the chain walker read garbage and spin forever.
    ng=oct_group_count(read_entry(src[base+'.oct']))
    hh,eL=read_ents_types(R['gms'])
    ntg=1+sum(1 for t in eL if t in (0x100020,0x100021,0x10003f))
    rep['oct groups %d / tree groups %d %s'%(ng,ntg,'OK' if ng==ntg else 'MISMATCH')]+=1
    from sndconv import convert_snd_dm_to_dd
    _whd_plan=None   # sound workflow 11 Oct: Dead Men layered WHD groups -> Dog Days layout (sndconv.layer_plan)
    if SND_MODE=='mute':
        from sndconv import mute_snd_from_dm
        snd,msg=mute_snd_from_dm(read_entry(src[base+'.SND']), DM_STREAM_DIR)
    else:
        snd,msg=convert_snd_dm_to_dd(read_entry(src[base+'.SND']), DM_STREAM_DIR, hide_types=SND_HIDE_TYPES)
        from sndconv import layer_plan, snd_remap_whd
        _whd_plan=layer_plan(open(os.path.join(lay['src_dir'],base+'.WHD'),'rb').read())
        snd,_st=snd_remap_whd(snd,_whd_plan)
        for k_,v_ in _st.items(): rep[k_]+=v_
        # sound round 2 (11 Oct): type-1 (volume/loop) and type-7 (reverb) records -> Dog Days layout (sndconv)
        from sndconv import snd_fix_records
        snd,_st,_snd_names=snd_fix_records(snd)
        for k_,v_ in _st.items(): rep[k_]+=v_
        # dialogue languages (11 Oct): Dead Men's 5 language items per localized wave -> Dog Days' 9 (ANP_SND_LANGS)
        from sndconv import SND_LANGS, snd_expand_langs, whd_lang_records
        if SND_LANGS:
            snd,_st=snd_expand_langs(snd)
            for k_,v_ in _st.items(): rep[k_]+=v_
            _whd_lang=whd_lang_records(read_entry(src[base+'.SND']))
        else: _whd_lang=None
    if SND_MODE=='mute': _snd_names={}; _whd_lang=None
    sd=lay['src_dir']
    def conv_main_whd(fn):
        from whdconv import convert_whd_dm_to_dd
        from strvirt import mapping as strmap
        smap=strmap(os.path.join(DM_GAME,'PC_Def.str'), os.path.join(W,'cache'))
        # ANP_SND_LANGS: the main bank's language-file records -> the virtual PCM of their own PC_<Lang>.str
        lmaps=None
        if _whd_lang is not None and fn.lower()==(base+'.WHD').lower():
            _lf={}; lmaps={}
            for ro,sf_ in _whd_lang.items():
                if sf_ not in _lf:
                    _p=os.path.join(DM_GAME,sf_)
                    _lf[sf_]=strmap(_p, os.path.join(W,'cache')) if os.path.isfile(_p) else None
                if _lf[sf_] is not None: lmaps[ro]=_lf[sf_]
            for sf_,m_ in sorted(_lf.items()): rep['language stream %s: %s'%(sf_,'%d ADPCM entries'%len(m_) if m_ is not None else 'MISSING (its lines stay unplayable)')]+=1
        o,st=convert_whd_dm_to_dd(open(os.path.join(sd,fn),'rb').read(), stream_map=smap, lang_maps=lmaps)
        if _whd_plan is not None and fn.lower()==(base+'.WHD').lower():
            from sndconv import whd_postfix
            o,_st=whd_postfix(open(os.path.join(sd,fn),'rb').read(), o, _whd_plan, smap, lmaps); st.update(_st)
        return o,st
    _imp_whd=None; _imp_wav=b''
    if _imp_anm:
        # ANP_SND_IMPORT_DD (tools/sndimport.py): the Dog Days sound records the donor clips name (and that the Dead Men
        # bank lacks) are copied from the donor's .SND/.WHD/.WAV into this level's banks; then the clip ids are written
        import sndimport, clipsnd
        _dd=os.path.join(DD_ROOT,ANM_DONOR,ANM_DONOR+'_Main')
        _whdfn=next(fn for fn in os.listdir(sd) if fn.lower()==(base+'.WHD').lower())
        _wavfn=next(fn for fn in os.listdir(sd) if fn.lower()==(base+'.WAV').lower())
        _imp_whd=conv_main_whd(_whdfn)
        snd,_w2,_imp_wav,_imap,_st=sndimport.import_dd(snd,_imp_anm['dsnd'],open(_dd+'.WHD','rb').read(),open(_dd+'.WAV','rb').read(),
                                                     _imp_anm['roots'],_imp_whd[0],os.path.getsize(os.path.join(sd,_wavfn)))
        _imp_whd=(_w2,_imp_whd[1])
        for k_,v_ in sorted(_st.items()): rep[k_]+=v_
        _anm2=clipsnd.fix_clip_sounds(_imp_anm['pre'],_imp_anm['donor_anm'],_imp_anm['dsnd'],_imp_anm['lsnd'],rep,extra=_imap)
        _an=nb+'.ANM'
        _i=next(i for i,e_ in enumerate(entries) if e_.name==_an)
        entries[_i]=entry_from_bytes(_an,_anm2,like=like)
    rep['snd %s'%msg]+=1
    bad=[(hex(v),en) for v,en in R['audio_defs'] if not snd_list_ok(snd,v)]
    if bad: raise SystemExit('audio definitions that are not sound lists in the output .SND (pause-menu crash): %s'%bad)
    rep['audio definitions checked against the .SND: %s'%sorted(set('%s %#x'%(en,v) for v,en in R['audio_defs']))]+=1
    add_bytes(nb+'.SND',snd,like)
    from prmconv import convert_prm_dm_to_dd
    dmprm=bytearray(read_entry(src[base+'.prm']))
    if os.environ.get('ANP_ENV','1')=='1': patch_environments(dmprm, R, rep)
    prm,_=convert_prm_dm_to_dd(bytes(dmprm), rep, extra_chunks=R['graft']['prm_extra'],
                               ref_add=R['graft'].get('prm_refs'))
    if os.environ.get('ANP_GUNFIT','1')=='1':
        import gunfit
        prm=gunfit.apply_prm(prm,R.get('gunfit'),gunfit_bind,gunfit.reference(W,DD_ROOT),rep)
    for ext in [x for x in ['.oct','.sgp','.rmc','.rmi','.prm','.sgd','.hrd'] if base+x in src]:
        if ext=='.prm': add_bytes(nb+ext,prm,like)
        else: add_raw(base+ext, nb+ext)
    fx=dz['Scenes/Locations/%s/%s_Main.fxc'%(donor,donor)]
    # effect permutations: donor library + aliases for the (effect, defines) keys Dead Men materials request
    misspaths=[p_ for p_ in (os.path.join(os.path.dirname(__file__),'..','fxc','miss_%s.txt'%x) for x in lay['fxc_ids'])
               if os.path.exists(p_)]
    unionpath=os.path.join(os.path.dirname(__file__),'..','fxc','union.pkl')
    if misspaths and os.path.exists(unionpath):
        import pickle
        from fxclib import parse as fxparse
        from fxcalias import build as fxbuild, load_keys
        ver,R0=fxparse(read_entry(fx))
        basefx={(r['kind'],r['name'],tuple(x for x,_ in r['defs'])):r['raw'] for r in R0}
        logl=[]
        keys_=load_keys(misspaths[0])                     # one list (every level): exactly as before
        for p_ in misspaths[1:]:
            keys_+=[k_ for k_ in load_keys(p_) if k_ not in keys_]
        fxd,nfx=fxbuild(pickle.load(open(unionpath,'rb')),keys_,log=logl.append,base=basefx)
        for l in logl: rep['fxc '+l.split(' ')[0]]+=1
        add_bytes(nb+'.fxc',fxd,like); rep['fxc records %d'%nfx]+=1
    else:
        fx.name=nb+'.fxc'; entries.append(fx)
    zp=os.path.join(out_dir,lay['stem']+'.zip')
    tmp=zp+'.tmp'; write_zip(tmp,entries)
    try: os.replace(tmp,zp)
    except OSError: os.remove(tmp); raise
    # sound banks etc
    for fn in os.listdir(sd):
        if fn.startswith(base) and not fn.endswith('.zip'):
            dst=os.path.join(out_dir, fn.replace(base, lay['stem']))
            if fn.upper().endswith('.WHD'):
                if _imp_whd is not None and fn.lower()==(base+'.WHD').lower(): o,st=_imp_whd
                else: o,st=conv_main_whd(fn)
                open(dst,'wb').write(o)
                for k_,v_ in st.items(): rep['%s %s'%(fn,k_)]+=v_
            elif _imp_wav and fn.lower()==(base+'.WAV').lower():
                import sndimport
                open(dst,'wb').write(sndimport.append_wav(open(os.path.join(sd,fn),'rb').read(),_imp_wav))
            elif fn.upper().endswith('.SND'):
                from sndconv import convert_ls_snd_dd
                o,msg=convert_ls_snd_dd(open(os.path.join(sd,fn),'rb').read(), snd, _snd_names)
                if SND_MODE=='mute':
                    o=o[:4]+struct.pack('<III',16,3,4); msg='ls muted'
                open(dst,'wb').write(o); rep['snd %s %s'%(fn,msg)]+=1
            else:
                shutil.copyfile(os.path.join(sd,fn), dst)
    # loading screen from donor (ANP_LOADER: dd = byte for byte; silent = subtitles blanked, WAV silenced)
    for fn in os.listdir(os.path.join(DD_ROOT,donor)):
        if fn.startswith('Loader_Sequence'):
            sfn=os.path.join(DD_ROOT,donor,fn); dfn=os.path.join(out_dir,fn)
            if LOADER_MODE=='silent' and fn.lower()=='loader_sequence.zip':
                import locconv
                lents=[]; lst={}
                for e_ in read_zip(sfn):
                    if e_.name.lower().endswith('.loc'):
                        d0_=read_entry(e_); d1_,lst=locconv.map_texts(d0_,locconv.loader_subtitles_blank(lst),lst)
                        if d1_!=d0_:
                            ne_=entry_from_bytes(e_.name,d1_,compress=(e_.method==8),like=e_); ne_.flags=e_.flags; ne_.ver=e_.ver
                            e_=ne_
                    lents.append(e_)
                write_zip(dfn+'.tmp',lents); os.replace(dfn+'.tmp',dfn)
                rep['loader (ANP_LOADER=silent): %d subtitle lines blanked in %d LOCs'%(lst.get('loader subtitle blanked',0),
                    sum(1 for e_ in lents if e_.name.lower().endswith('.loc')))]+=1
            elif LOADER_MODE=='silent' and fn.lower()=='loader_sequence.wav':
                w_=bytearray(open(sfn,'rb').read())
                h_=struct.unpack_from('<4I',w_,0)
                if h_[0]!=0 or h_[1]!=len(w_) or h_[2:]!=(3,4): raise SystemExit('Loader_Sequence.WAV header %s unexpected'%(h_,))
                w_[16:]=bytes(len(w_)-16)          # IMA ADPCM: predictor 0, step index 0, nibbles 0 = silence
                open(dfn,'wb').write(bytes(w_)); rep['loader (ANP_LOADER=silent): Loader_Sequence.WAV silenced (%d bytes)'%len(w_)]+=1
            else:
                shutil.copyfile(sfn, dfn)
    # DD expects languages beyond DM's: duplicate the default LS banks for those (every build, so they never go stale)
    for L in ['Japanese','Russian']:
        for ext in ['.WAV','.WHD']:
            t=os.path.join(out_dir,'%s_LS_%s%s'%(lay['stem'],L,ext)); s=os.path.join(out_dir,'%s_LS_Default%s'%(lay['stem'],ext))
            if not os.path.exists(os.path.join(sd,'%s_LS_%s%s'%(base,L,ext))) and os.path.exists(s): shutil.copyfile(s,t)
    return rep, zp

if __name__=='__main__':
    # py tools\port_level.py <DM folder> <DM name> <ID>   (e.g. M01_A M01A M01)
    # py tools\port_level.py <special ID>                 (SPECIAL_SCENES, e.g. M07F = the funeral)
    if len(sys.argv)==2 and sys.argv[1].upper() in SPECIAL_SCENES:
        _sp=SPECIAL_SCENES[sys.argv[1].upper()]; _args=(_sp['dm_folder'],_sp['dm_name'],sys.argv[1].upper())
    elif len(sys.argv)==4: _args=tuple(sys.argv[1:4])
    else: raise SystemExit('usage: port_level.py <DM folder> <DM name> <ID> | port_level.py %s'%'|'.join(SPECIAL_SCENES))
    rep,zp=build(*_args)
    for k,v in sorted(rep.items()): print('%-60s %s'%(k,v))
    print('wrote',zp,os.path.getsize(zp))
