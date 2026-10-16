#!/usr/bin/env python3
"""
Kane and Lynch TALK on a FINISHED build: the campaign's own lines (Kane's countdown to the blast at the Retomoto
boardroom window, the exchanges of the two in the tower and on the street; a shorter set on the four Dead Men maps)
and pools of lines both games already have for idle / event chatter. Spec, inventory, the hook part, live checks:
re/talk.md. Builds on re/bots_voice.md (how a line gets its voice), re/voice.md, re/audio.md. OFFLINE: nothing here
installs anything or starts the game.

    python kl_fa_talk.py inventory [<out folder>]       every line with a sound of Kane, Lynch, the Dead Men crew, the
                                                        eight heisters and the squad voices, both games, all stock levels
                                                        -> <work>\\research\\v_talk\\lines_dm.tsv / lines_dd.tsv + summary
    python kl_fa_talk.py plan [map ...]               the script of a map: scenes, lines, text, clip form, seconds
    python kl_fa_talk.py stream [--base <file.str>] [--out <file.str>] [--verify]
                                                        the stream file every talk build needs: the base (default
                                                        <work>\\build\\PC_Def.str, the one that is installed) + the
                                                        streamed clips of ALL maps' scripts, appended (kl_str.merge:
                                                        nothing the base holds moves) -> <work>\\build\\v_talk\\str
                                                        --verify: only re-read a file made before; exit 1 on a problem
    python kl_fa_talk.py build <build folder> <out folder> --map retomoto|M01|M02|M03|M06 [options]
                                                        the lines into a COPY of the build + KLTalk.ini beside it
      --adpcm memory|stream   Dead Men's streamed IMA ADPCM clips (nearly all of Kane's lines): 'memory' (default)
                              = records in the level's .WAV, the form 643 of F07's 729 in-memory records have and the
                              form the Japanese guards' lines are played in; 'stream' = left in the stream file (the
                              .WAV does not grow at all). Streamed ADPCM has a decode path in kl2.exe (re/voice.md
                              7.3) that no stock clip uses and nobody has heard: ASSUMPTION that it sounds right.
      --str <file.str>        the stream file of `stream` (default <work>\\build\\v_talk\\str\\PC_Def.str)
      --blast N               Retomoto only: seconds from the round-start event to the blast when the level's own
                              timer cannot be read (default: read from the level, kl_fa_author's 9 + 4 = 13)
    python kl_fa_talk.py check <folder> [--str <file.str>]   every key of KLTalk.ini the way the exe finds it; exit 1 on FAIL
    python kl_fa_talk.py sizes <folder> [<folder> ...]  the four large blocks (.prm .ANM .fxc .WAV)
    python kl_fa_talk.py empty <folder>                 the line groups of the settings that are empty on a build

WHAT IS WRITTEN (build())
  .SND / .WHD / .WAV / _LS.SND   the sound objects of the script's lines, appended from the campaign level's bank with
                                 kl_snd.merge (every byte of the build's bank below its first type table keeps its place)
  nine .LOC                      one PLAIN leaf per line under KLTalk/ (text of the language where Dead Men has it,
                                 else English; the sound id). Plain = found by one lookup of the key (kl2 0x828fa0),
                                 the way OnlineSpeakPlayer finds its line (0x8cb6e0)
  KLTalk.ini                     beside the archive: the scenes (when, who must be in the round, key, start, length),
                                 the chatter pools (keys the bank ALREADY holds: Dog Days' own Kane / Lynch one-liners,
                                 the eight heisters' level lines, the two squad voices), and what the hook must find
  Nothing else: no entity, no .prp / .gms byte, no model, no animation, no shader. A build with this step and WITHOUT
  the hook part plays exactly as before - nobody says a word of it ("with neither present nothing is said").

WHY THE HOOK (re/talk.md 3): who wears Kane or Lynch is decided at run time (klhook\\klchar.c for the player, the crew
randomiser for the bots) and no level object can test it; and a line through the game's speech manager is one call
(0x421c70, as OnlineSpeakPlayer makes it at 0x7805f4). The level carries everything else.

GUESS = a value not copied from a stock object and not measured; ASSUMPTION = fits the evidence, not proven.
"""
import collections, json, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_snd, kl_loc, kl_voice
import kl_whd as W

SLOT = 'F01'
BIG = ('.prm', '.ANM', '.fxc')
PREFIX = 'KLTalk'                           # the .LOC table the lines go under
GAP = 0.35                                  # GUESS: seconds between two lines of an exchange (the campaign's cut scenes
                                            # run them back to back; a breath reads better without pictures)
GO = 8.0                                    # the countdown on the HUD: the round-start event comes when it BEGINS
                                            # (kl_fa_author, SEEN LIVE runs GW1 / GW2), 'GO' 8 s later
BLAST_TIMER = 'Gameplay!010_FirstFight!RivalMercVan!Timer'      # kl_fa_author.ROLE['blast timer'] (TriggerDelay2 field 0)
K, L = 'Kane', 'Lynch'

# ------------------------------------------------------------------ the scripts
# A scene: (name, when, delay, needs, extra, [(who, leaf, at)]).
#   when    Start = the round-start event (session state 0x19 begins: ASSUMPTION, re/talk.md 3.3) | Stage1 / Stage2 /
#           Stage3 = the local player's heist stage reaches it (crew record +0x78, raised by the level's own trigger
#           boxes: 1 inside the loot area, 2 out of it, 3 at the vehicle) | Aboard = his status becomes 4 | Join = the
#           hook's own jump between the two halves (kljoin.c) | Box = his feet inside `extra['box']`
#   needs   Kane | Lynch = that one is in the round (the other may be) | Both | KaneOnly | LynchOnly
#           Scenes of one name are ALTERNATIVES: the first whose needs hold plays, once a round.
#   at      seconds from the scene's start; None = behind the line before it + GAP
#   leaf    the last two parts of the campaign key (unique in the source level's .LOC)
# Every choice of line and moment is by the texts: ASSUMPTION / GUESS, the owner's ears decide.
RT_ROOM = (4500.0, 5500.0, 20900.0, 21300.0, -500.0, 400.0)       # GUESS: round the boardroom table (kl_fa_author.MAIN_ROOM x 4750..5250, z -120..20, floor y 20993)
RT_RECEPTION = (2800.0, 3300.0, 20900.0, 21300.0, -1300.0, 150.0)  # GUESS: kl_fa_author.STAGE_B, the reception on the boardroom's floor
RT_STREET = (1900.0, 2600.0, -100.0, 900.0, -7300.0, -5700.0)      # GUESS: just outside the front entrance (x 2600, z -7300..-5700; the lobby is x 2600..6109)
RT_ROAD = (-5700.0, -300.0, -300.0, 600.0, -1500.0, 7000.0)        # the carriageway (kl_fa_author.ROAD_X +- ROAD_HALF, z up to the van stops at 7700)
SCRIPTS = {
    'retomoto': dict(source='M09_A', scenes=[
        # the campaign plays 010..040 back to back from a MiniCutsceneRout ('040_MiniCut_Office_Countdown_Kane') and
        # 050 / 060 from the next one ('055_MiniCut_TakeThemDown'): 7.22 s of counting, then 'NOW!'. Here 'NOW!' starts
        # ON the blast; the delay of the scene is computed from the level's blast time in build()
        ('balcony', 'Start', 0.6, 'Lynch', {}, [(L, 'M09_Start_Rappel/M09_Start_Rappel_010_Lynch', 0.0)]),
        ('countdown', 'Start', None, 'Kane', {'blast': 4}, [
            (K, 'M09_Countdown/M09_Countdown_010_Hero', 0.0), (K, 'M09_Countdown/M09_Countdown_020_Hero', 'tight'),
            (K, 'M09_Countdown/M09_Countdown_030_Hero', 'tight'), (K, 'M09_Countdown/M09_Countdown_040_Hero', 'tight'),
            (K, 'M09_Countdown/M09_Countdown_050_Hero', 'tight'), (K, 'M09_Countdown/M09_Countdown_060_Hero', None)]),
        ('room', 'Box', 0.0, 'Both', {'box': RT_ROOM, 'not_before': 25.0}, [
            (L, 'M09_Take_Briefcase_Give_Scar/M09_TakeBriefcaseGiveScar_020_Lynch', 0.0),
            (K, 'M09_Take_Briefcase_Give_Scar/M09_TakeBriefcaseGiveScar_030_Hero', None),
            (L, 'M09_Take_Briefcase_Give_Scar/M09_TakeBriefcaseGiveScar_040_Lynch', None),
            (K, 'M09_Take_Briefcase_Give_Scar/M09_TakeBriefcaseGiveScar_050_Hero', None)]),
        ('room', 'Box', 0.0, 'KaneOnly', {'box': RT_ROOM, 'not_before': 25.0}, [(K, 'M09_Room_Cleared/M09_Room_Cleared_010_Hero', 0.0)]),
        ('room', 'Box', 0.0, 'LynchOnly', {'box': RT_ROOM, 'not_before': 25.0}, [(L, 'M09_Get_The_Briefcase/M09_Get_The_Briefcase_010_Lynch', 0.0)]),
        ('reception', 'Box', 0.0, 'Kane', {'box': RT_RECEPTION, 'not_before': 25.0}, [(K, 'M09_Lets_Get_To_Elevators/M09_LetsGetToElevators_010_Hero', 0.0)]),
        ('reception', 'Box', 0.0, 'LynchOnly', {'box': RT_RECEPTION, 'not_before': 25.0}, [(L, 'M09_They_Are_Everywhere/M09_They_Are_Everywhere_001_Lynch', 0.0)]),
        ('car', 'Join', 0.8, 'Kane', {}, [(K, 'M09b_Start_Elevator/M09b_Start_Elevator_010_Hero', 0.0), (K, 'M09b_Lobby/M09b_Lobby_010_Hero', None)]),
        ('street', 'Box', 0.0, 'Both', {'box': RT_STREET}, [
            (K, 'M09b_Outside/M09b_Outside_001_Hero', 0.0), (L, 'M09b_CantGetToOverpass/M09b_CantGetToOverpass_040_Lynch', None),
            (K, 'M09b_CantGetToOverpass/M09b_CantGetToOverpass_050_Hero', None)]),
        ('street', 'Box', 0.0, 'KaneOnly', {'box': RT_STREET}, [(K, 'M09b_Outside/M09b_Outside_001_Hero', 0.0)]),
        ('road', 'Box', 0.0, 'Both', {'box': RT_ROAD}, [
            (L, 'M09b_OverPass/M09b_OverPass_010_Lynch', 0.0), (L, 'M09b_OverPass/M09b_OverPass_011_Lynch', None),
            (K, 'M09b_OverPass/M09b_OverPass_020_Hero', None), (L, 'M09b_OverPass/M09b_OverPass_040_Lynch', None)]),
        ('road', 'Box', 0.0, 'LynchOnly', {'box': RT_ROAD}, [(L, 'M09b_OverPass/M09b_OverPass_010_Lynch', 0.0)]),
        ('van', 'Aboard', 0.5, 'Both', {}, [(L, 'M09b_InVan/M09b_InVan_010_Lynch', 0.0), (K, 'M09b_InVan/M09b_InVan_020_Hero', None)]),
    ]),
    'M01': dict(source='M01_A', scenes=[
        ('start', 'Start', GO + 1.0, 'Both', {}, [(L, 'M01_MiniCut01/M01_MiniCut01_010_Lynch', 0.0), (K, 'M01_MiniCut01/M01_MiniCut01_020_Hero', None)]),
        ('start', 'Start', GO + 1.0, 'LynchOnly', {}, [(L, 'M01_Diner/M01_Diner_060_Lynch', 0.0)]),
        ('inside', 'Stage1', 4.0, 'Lynch', {}, [(L, 'M01_OLLynchShotDonut/M01_OLLynchShotDonut_010_Lynch', 0.0)]),
        ('out', 'Stage2', 1.0, 'Both', {}, [(L, 'M01_OnFeet/M01_OnFeet_040_Lynch', 0.0), (K, 'M01_MiniCut01/M01_MiniCut01_040_Hero', None)]),
        ('out', 'Stage2', 1.0, 'LynchOnly', {}, [(L, 'M01_FoundLynch/M01_FoundLynch_010_Lynch', 0.0)]),
    ]),
    'M02': dict(source='M02_A', scenes=[
        ('start', 'Start', GO + 1.0, 'Both', {}, [(L, 'M02_Plan/M02_Plan_010_Lynch', 0.0), (K, 'M02_Plan/M02_Plan_100_Hero', None)]),
        ('inside', 'Stage1', 6.0, 'Both', {}, [
            (L, 'M02_GravelPit/M02_GravelPit_010_Lynch', 0.0), (K, 'M02_GravelPit/M02_GravelPit_020_Hero', None),
            (L, 'M02_GravelPit/M02_GravelPit_030_Lynch', None), (K, 'M02_GravelPit/M02_GravelPit_040_Kane', None),
            (L, 'M02_GravelPit/M02_GravelPit_050_Lynch', None), (K, 'M02_GravelPit/M02_GravelPit_060_Kane', None)]),
        ('out', 'Stage2', 1.0, 'Both', {}, [(K, 'M02_BeforeRappel/M02_BeforeRappe_010_Hero', 0.0), (L, 'M02_BeforeRappel/M02_BeforeRappe_020_Lynch', None)]),
        ('out', 'Stage2', 1.0, 'KaneOnly', {}, [(K, 'M02_GetGrenades/M02_GetGrenades_010_Hero', 0.0)]),
        ('out', 'Stage2', 1.0, 'LynchOnly', {}, [(L, 'M02_OLGotoCar/M02_OLGotoCar_020_Lynch', 0.0)]),
    ]),
    'M03': dict(source='M03_A', scenes=[
        ('start', 'Start', GO + 1.0, 'Both', {}, [
            (K, 'M03_LynchLobby/M03_LynchLobby_010_Hero', 0.0), (L, 'M03_LynchLobby/M03_LynchLobby_020_Lynch', None),
            (K, 'M03_LynchLobby/M03_LynchLobby_030_Hero', None)]),
        ('start', 'Start', GO + 1.0, 'KaneOnly', {}, [(K, 'M03_MissionBrief/M03_MissionBrief_080_Hero', 0.0)]),
        ('inside', 'Stage1', 5.0, 'Kane', {}, [(K, 'M03_VaultCut/M03_VaultCut_050_Hero', 0.0)]),
        ('inside', 'Stage1', 5.0, 'LynchOnly', {}, [(L, 'M03_Shoot/M03_Shoot_010_Lynch', 0.0)]),
        ('out', 'Stage2', 1.0, 'Both', {}, [(L, 'M03_Escape/M03_Escape_001_Lynch', 0.0), (K, 'M03_Escape/M03_Escape_010_Hero', None)]),
        ('van', 'Aboard', 0.5, 'Both', {}, [(L, 'M03_ArgueCar01/M03_ArgueCar01_040_Lynch', 0.0), (K, 'M03_ArgueCar01/M03_ArgueCar01_050_Hero', None)]),
    ]),
    'M06': dict(source='M06_A', scenes=[
        ('start', 'Start', GO + 1.0, 'Both', {}, [
            (L, 'M06_SmallTalk/M06_SmallTalk_010_Lynch', 0.0), (K, 'M06_SmallTalk/M06_SmallTalk_020_Hero', None),
            (L, 'M06_SmallTalk/M06_SmallTalk_030_Lynch', None), (K, 'M06_SmallTalk/M06_SmallTalk_040_Hero', None),
            (L, 'M06_SmallTalk/M06_SmallTalk_050_Lynch', None)]),
        ('inside', 'Stage1', 4.0, 'Both', {}, [(K, 'M06_PreNegotiation/M06_PreNegotiation_010_Hero', 0.0), (L, 'M06_Negotiation/M06_Negotiation_140_Lynch', None)]),
        ('out', 'Stage2', 1.0, 'Both', {}, [(K, 'M06_LynchShoot/M06_LynchShoot_010_Hero', 0.0), (L, 'M06_Argue02/M06_Argue02_002_Lynch', None)]),
    ]),
}
ALIAS = {'M01_FA_A': 'M01', 'M02_FA_A': 'M02', 'M03_FA_A': 'M03', 'M06_FA_A': 'M06', 'rt': 'retomoto'}

# ------------------------------------------------------------------ chatter: lines the FA bank already holds
# (F07's bank carries Dog Days' story one-liners of Kane, Lynch and the two squad voices as .LOC keys with sound
# objects, and the level lines of all nine stock levels in the eight heisters' voices: MEASURED, check()).
# A pool: (name, who, on, [keys]). who: Kane | Lynch = plain keys, said by whoever wears him; Any = PER-CHARACTER keys,
# the hook appends _C<n>, n = 1 + byte [rules + 0x33e + crew slot] (the game's own voice rule, kl2 0x6ae750);
# Squad = plain keys in two generic voices (..._Squad / ..._Squad02), for a bot. on: Idle (a quiet stretch) | Money
# (the speaker's money rose) | Down (another crew member died) | Stage2 (the speaker left the loot area) | Traitor
# (a crew member was marked traitor). ASSUMPTION which line suits which moment: by the texts.
O = 'AllLevels/Oneliners/'
POOLS = [
    ('kane_idle', K, 'Idle', [O + 'What/What_0%d0_Kane' % i for i in (1, 2, 3, 4, 5, 6, 8)] + [
        O + 'LetsGo/LetsGo_060_Kane', O + 'Direction/Direction_030_Kane_b', O + 'Direction/Direction_060_Kane', O + 'Guns/Guns_030_Kane']),
    ('kane_money', K, 'Money', [O + 'Guns/Guns_010_Kane', O + 'Guns/Guns_020_Kane', O + 'Guns/Guns_040_Kane']),
    ('kane_down', K, 'Down', [O + 'Exclamation/Exclamation_0%d0_Kane' % i for i in (1, 2, 3, 9)]),
    ('kane_move', K, 'Stage2', [O + 'LetsGo/LetsGo_030_Kane', O + 'LetsGo/LetsGo_040_Kane', O + 'LetsGo/LetsGo_050_Kane', O + 'Move/MoveMid_060_Kane']),
    ('lynch_idle', L, 'Idle', [O + 'What/What_0%d0_Lynch' % i for i in (1, 2, 4, 5, 6)] + [
        O + 'LynchPsych/Base/Base_030_Lynch', O + 'LynchPsych/Base/Base_040_Lynch', O + 'LynchPsych/Base/Base_050_Lynch',
        O + 'LynchPsych/Base/Base_060_Lynch', O + 'LetsGo/LetsGo_050_Lynch', O + 'Direction/Direction_010_Lynch']),
    ('lynch_money', L, 'Money', [O + 'Guns/Guns_010_Lynch', O + 'Guns/Guns_020_Lynch', O + 'Guns/Guns_030_Lynch', O + 'Guns/Guns_040_Lynch']),
    ('lynch_down', L, 'Down', [O + 'Exclamation/Exclamation_010_Lynch', O + 'Exclamation/Exclamation_020_Lynch',
                               O + 'Exclamation/Exclamation_030_Lynch', O + 'Exclamation/Exclamation_100_Lynch']),
    ('lynch_move', L, 'Stage2', [O + 'LetsGo/LetsGo_010_Lynch', O + 'LetsGo/LetsGo_030_Lynch', O + 'LetsGo/LetsGo_060_Lynch', O + 'Move/MoveLoud_010_Lynch']),
    ('any_idle', 'Any', 'Idle', ['Multiplayer/F06/MissionReminder_01_R', 'Multiplayer/F09/MissionReminder_02_R',
                                 'Multiplayer/F05/MissionBriefing_01_R', 'Multiplayer/F05/MissionBriefing_02_R', 'Multiplayer/F08/ReachlootArea_01_R',
                                 'Multiplayer/F05/MissionReminder_01_R', 'Multiplayer/F02/ReachlootArea_01_R']),
    ('any_money', 'Any', 'Money', ['Multiplayer/F06/ReachlootArea_01_R', 'Multiplayer/F04/ExitLootArea_01_R', 'Multiplayer/F07/ExitLootArea_01_R']),
    ('any_move', 'Any', 'Stage2', ['Multiplayer/F05/ExitHeist_01_R', 'Multiplayer/F01/ExitHeist_01_R',
                                   'Multiplayer/F05/ExitLootArea_01_R', 'Multiplayer/F08/ExitLootArea_01_R']),
    ('any_down', 'Any', 'Down', ['Multiplayer/F05/ReachlootArea_01_R', 'Multiplayer/F09/ExitLootArea_01_R']),
    ('any_traitor', 'Any', 'Traitor', ['Multiplayer/F09/MissionBriefing_02_R', 'Multiplayer/F09/MissionBriefing_03_R']),
    ('squad_down', 'Squad', 'Down', [O + 'ManDown/*', O + 'Exclamation/*']),      # the two squad voices: filled from the build's .LOC
    ('squad_idle', 'Squad', 'Idle', [O + 'BattleCries/*', O + 'Advance/*']),
]
SQUAD_MAX = 10                              # GUESS: keys per squad pool and voice (enough not to repeat in a round)
# call and answer between the two, both from the bank as it is: (who, key, who, key)
PAIRS = [
    (K, O + 'LetsGo/LetsGo_010_Kane', L, O + 'Direction/DirectionResp_020_Lynch'),            # Lynch! Over here! / On my way.
    (L, O + 'LetsGo/LetsGo_020_Lynch', K, O + 'Direction/DirectionResp_010_Kane'),            # Kane! Keep moving / Coming.
    (L, O + 'LetsGo/LetsGo_040_Lynch', K, O + 'Direction/DirectionResp_020_Kane'),            # Over here, oldtimer. We gotta move. / Be right there!
    (L, O + 'What/What_070_Lynch', K, O + 'Direction/DirectionResp_040_Kane'),                # Kane? Where are you? / I'm here!
    (K, O + 'What/What_090_Kane', L, O + 'Direction/Direction_020_Lynch'),                    # Lynch? Which way. / Just straight ahead.
    (K, O + 'Flank/FlankCover_020_Kane', L, O + 'Flank/FlankRep_030_Lynch'),                  # Lynch! I got your back! / Right behind ya!
    (L, O + 'Flank/FlankCover_020_Lynch', K, O + 'Flank/FlankRep_010_Kane'),                  # Kane! Got you covered! / I got it!
]
# the cap ('nobody repeats', the owner about the guards): the hook's rules, written into the ini so they can be tuned
CHATTER = collections.OrderedDict([
    ('Gap', '40,90'),       # GUESS: seconds between two idle lines of the whole crew, drawn anew each time
    ('MemberGap', '25'),    # GUESS: one crew member does not chatter again within this
    ('Quiet', '8'),         # GUESS: no chatter this close to a scene line (before or after)
    ('EventChance', '50'),  # GUESS: percent of Money / Down / Stage2 / Traitor moments that get a line at all
    ('Once', '1'),          # a key is said at most once a round; a pool that is used up stays silent (0: it starts over)
    ('Speakers', '0'),      # 0 = the human's own character does not chatter (only the bots do); 1 = he too
])


# ------------------------------------------------------------------ small things
def workdir():
    from kl_port_check import workdir as w
    return w()


def str_out():
    return os.path.join(workdir(), 'build', 'v_talk', 'str', 'PC_Def.str')


def sizes(folder, slot=SLOT):
    """The four blocks a level reads in one piece: {'.prm': bytes, '.ANM', '.fxc', '.WAV'}."""
    with zipfile.ZipFile(os.path.join(folder, slot + '_Main.zip')) as z:
        out = collections.OrderedDict((e, next(i.file_size for i in z.infolist() if i.filename.endswith('_Main' + e))) for e in BIG)
    out['.WAV'] = os.path.getsize(os.path.join(folder, slot + '_Main.WAV'))
    return out


_levels = {}


def source(level):
    """A campaign level read once: walked bank, .WHD records, {lower key: (key, {language: text}, sound id)}."""
    if level not in _levels:
        with zipfile.ZipFile(kl_snd.level_zip(level, 'dm')) as zf:
            locs = {lang: kl_loc.parse(zf.read(n)) for lang, n in kl_loc.members(zf).items()}
        keys = {}
        for lang, t in locs.items():
            for p, n in kl_loc.leaves(t or []):
                text, _x, sid, _left = kl_loc.fields(n)
                e = keys.setdefault(p.lower(), [p, {}, 0])
                e[1][lang] = text or b''
                if lang == 'English':
                    e[2] = sid or 0
        whd = kl_snd.read(kl_snd.beside(level, '.WHD', 'dm'))
        _levels[level] = (kl_snd.bank(level, 'dm'), whd, W.records('dm', whd), keys)
    return _levels[level]


def find_key(level, leaf):
    """The one key of the level's .LOC that ends in `leaf` ('Folder/Name') -> its entry."""
    keys = source(level)[3]
    hit = [e for k, e in keys.items() if k.endswith('/' + leaf.lower())]
    if len(hit) != 1:
        raise ValueError('%s: %d .LOC keys end in %s' % (level, len(hit), leaf))
    return hit[0]


def clip_of(level, sid):
    """-> dict(form, seconds, name, record) of the English clip of sound `sid` in a campaign bank."""
    S, whd, recs, _k = source(level)
    if S.kind.get(sid) != 1:
        raise ValueError('%s: %#x is no sound object' % (level, sid))
    w = kl_snd.u32(S.b, sid + 0x14)
    f = recs.get(kl_snd.u32(S.b, w + 0x14)) if w and w < S.T else None
    if f is None:
        raise ValueError('%s: sound %#x has no .WHD record' % (level, sid))
    return dict(form=kl_voice.codec(S, recs, sid), seconds=f['samples'] / float(f['rate']), name=kl_snd.cs(whd, f['name']).decode('latin1'), rec=f)


def script(name, blast=None):
    """The script of a map with every line resolved -> dict(source, lines {leaf: ...}, scenes [...]).
    A line: key (KLTalk/<leaf name>), who, text, sid, form, seconds. A scene: name, when, delay, needs, box,
    not_before, lines [(who, key, at, seconds)]. blast: seconds from the round-start event to the blast, for the
    scene that is timed by it (its line number extra['blast'], 0-based, starts ON the blast)."""
    name = ALIAS.get(name, name)
    sp = SCRIPTS[name]
    lines, scenes = collections.OrderedDict(), []
    for sname, when, delay, needs, extra, ls in sp['scenes']:
        t, out = 0.0, []
        for who, leaf, at in ls:
            if leaf not in lines:
                key, texts, sid = find_key(sp['source'], leaf)
                c = clip_of(sp['source'], sid)
                lines[leaf] = dict(key='%s/%s' % (PREFIX, key.split('/')[-1].strip()), src=key, who=who, texts=texts, sid=sid,
                                   form=c['form'], seconds=c['seconds'], clip=c['name'])
            ln = lines[leaf]
            if ln['who'] != who:
                raise ValueError('%s: %s is used as %s and as %s' % (name, leaf, ln['who'], who))
            start = t if at == 'tight' else (t + GAP if at is None else float(at))
            out.append((who, ln['key'], round(start, 2), round(ln['seconds'], 2)))
            t = start + ln['seconds']
        if 'blast' in extra:
            delay = None if blast is None else round(blast - out[extra['blast']][2], 2)
        scenes.append(dict(name=sname, when=when, delay=delay, needs=needs, box=extra.get('box'),
                           not_before=extra.get('not_before'), lines=out, blast=extra.get('blast')))
    return dict(map=name, source=sp['source'], lines=lines, scenes=scenes)


def plan(names=None, log=print):
    for name in names or sorted(SCRIPTS):
        sp = script(name, 13.0 if ALIAS.get(name, name) == 'retomoto' else None)
        tot = collections.Counter(); sec = collections.Counter()
        for ln in sp['lines'].values():
            tot[ln['form']] += 1; sec[ln['form']] += ln['seconds']
        log('%s (from %s): %d lines, %.1f s; by form: %s' % (sp['map'], sp['source'], len(sp['lines']), sum(sec.values()),
                                                           ', '.join('%s %d (%.1f s)' % (f, n, sec[f]) for f, n in sorted(tot.items()))))
        by_key = {ln['key']: ln for ln in sp['lines'].values()}
        for sc in sp['scenes']:
            log('  %-10s %-7s +%-5s %-9s%s%s' % (sc['name'], sc['when'], sc['delay'], sc['needs'],
                                                  ' box %s' % (sc['box'],) if sc['box'] else '', ' not before %s s' % sc['not_before'] if sc['not_before'] else ''))
            for who, key, at, secs in sc['lines']:
                ln = by_key[key]
                log('      %5.2f %-5s %5.2fs %-14s %s  "%s"' % (at, who, secs, ln['form'], key,
                                                                ln['texts'].get('English', b'').decode('latin1').encode('ascii', 'replace').decode()))


# ------------------------------------------------------------------ the inventory (re/talk.md 1)
# who speaks a .LOC line, by the name parts of its last key part (both games name the speaker there); first hit wins
SPEAKERS = {'dm': (('Kane', ('hero', 'kane')), ('Lynch', ('lynch',)), ('Carlos', ('carlos',)), ('Rific', ('rific',)),
                   ('Shelly', ('shelly',)), ('Thapa', ('thapa',)), ('crew (Merc)', ('merc', 'mercy', 'mercx'))),
            'dd': (('Kane', ('kane',)), ('Lynch', ('lynch', 'lync')), ('squad', ('squad',)), ('Glazer', ('glazer',)))}


def speaker(game, key):
    """Who a line key names: 'Kane', 'Lynch', a crew name, 'heister <n>' (Dog Days' _C<n>), 'squad', or None."""
    last = key.split('/')[-1].lower()
    parts = [p.rstrip('0123456789') for p in last.split('_')]
    for name, toks in SPEAKERS[game]:
        if any(p in toks for p in parts):
            return name
    if game == 'dd' and len(last) > 3 and last[-3:-1] == '_c' and last[-1] in '123456789':
        return 'heister %s' % last[-1]
    if key.lower().startswith('multiplayer/'):
        return 'FA line (one voice)' if game == 'dm' else None
    return None


def inventory(out=None, log=print):
    """Every .LOC line with a sound of Kane, Lynch, the Dead Men crew, Dog Days' eight heisters and squad voices,
    over all stock levels of both games -> <work>\\research\\v_talk\\lines_<game>.tsv (speaker, key, seconds, clip
    form, clip name, levels, English text) and a summary. A key is listed once, with the levels whose .LOC has it
    with a sound; form and length are those of the first level (ASSUMPTION: a key's clip is the same in all)."""
    out = out or os.path.join(workdir(), 'research', 'v_talk')
    os.makedirs(out, exist_ok=True)
    res = {}
    for game in ('dm', 'dd'):
        rows = collections.OrderedDict()
        for lv in kl_snd.stock_levels(game):
            with zipfile.ZipFile(kl_snd.level_zip(lv, game)) as zf:
                t = kl_loc.parse(zf.read(kl_loc.members(zf)['English']))
            whd = kl_snd.read(kl_snd.beside(lv, '.WHD', game))
            S, recs = kl_snd.bank(lv, game), W.records(game, whd)
            for p, n in kl_loc.leaves(t or []):
                text, _x, sid, _l = kl_loc.fields(n)
                who = speaker(game, p) if sid else None
                if who is None:
                    continue
                r = rows.get(p.lower())
                if r is None:
                    form, secs, clip = 'no sound object', 0.0, ''
                    if S.kind.get(sid) == 1:
                        form = kl_voice.codec(S, recs, sid)
                        w = kl_snd.u32(S.b, sid + 0x14)
                        f = recs.get(kl_snd.u32(S.b, w + 0x14)) if w and w < S.T else None
                        if f is not None:
                            secs, clip = f['samples'] / float(f['rate'] or 1), kl_snd.cs(whd, f['name']).decode('latin1')
                    r = rows[p.lower()] = [who, p, secs, form, clip, [], (text or b'').decode('latin1')]
                r[5].append(lv)
        path = os.path.join(out, 'lines_%s.tsv' % game)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write('speaker\tkey\tseconds\tform\tclip\tlevels\ttext\n')
            for r in sorted(rows.values(), key=lambda r: (r[0], r[1].lower())):
                f.write('%s\t%s\t%.2f\t%s\t%s\t%s\t%s\n' % (r[0], r[1], r[2], r[3], r[4], ' '.join(r[5]), r[6].replace('\t', ' ').replace('\n', ' ')))
        tab = collections.defaultdict(lambda: [0, 0.0, collections.Counter()])
        for r in rows.values():
            top = '/'.join(r[1].split('/')[:2]) if r[1].lower().startswith('alllevels/') else ('level dialogue' if not r[1].lower().startswith('multiplayer/') else 'Multiplayer')
            e = tab[(r[0], top)]
            e[0] += 1; e[1] += r[2]; e[2][r[3]] += 1
        log('%s: %d keys -> %s' % (game, len(rows), path))
        for (who, top), (n, secs, forms) in sorted(tab.items()):
            log('  %-20s %-24s %5d lines %8.1f s  %s' % (who, top, n, secs, ', '.join('%s %d' % kv for kv in forms.most_common())))
        res[game] = rows
    return res


# ------------------------------------------------------------------ the stream file
def stream_need(names=None):
    """{Dead Men block offset in its PC_Def.str: sorted [.WHD record names]} of every streamed clip of the scripts
    (ADPCM too, so a build with --adpcm stream needs no other file), by kl_str.need()'s rule."""
    import kl_str
    want = collections.defaultdict(set)
    for name in names or sorted(SCRIPTS):
        sp = script(name)
        S, whd, recs, _k = source(sp['source'])
        objs = kl_str.closure(S, {ln['sid'] for ln in sp['lines'].values()})
        for o, _i, at in S.waves():
            f = recs.get(at)
            if o not in objs or f is None or not f['fmt'] & W.STREAMED or f['fmt'] & W.LANGFILE:
                continue
            members = W.group_of('dm', recs, at) if f['fmt'] >> 24 else [at]
            if members is None:
                raise ValueError('%s: a line\'s clip stands in a torn stream group' % sp['source'])
            for m in members:
                want[recs[m]['off']].add(kl_snd.cs(whd, recs[m]['name']).decode('latin1'))
    return {o: sorted(n) for o, n in want.items()}


def stream_verify(base, out, log=print):
    """kl_str.verify on a stream file made by stream(), with its findings sorted: those of the blocks appended here
    (must be none) and those the BASE had before (kl_str.verify compares by name, and an earlier merge left 12 Dead
    Men names that are Dog Days names too; one block of an earlier merge is longer in the map than what was copied).
    Also, directly: every appended block equals Dead Men's bytes and stands in the index with Dead Men's format.
    -> (problems of the appended blocks, problems the base had, facts)"""
    import kl_str
    P = kl_str.paths()
    prior = kl_str.load_map(base + '.map.json') if os.path.isfile(base + '.map.json') else {}
    full = kl_str.load_map(out + '.map.json')
    bad = kl_str.verify(out, base, P['dm'], full, log, prior or None)
    b, m, dm = kl_str.Stream(base), kl_str.Stream(out), kl_str.Stream(P['dm'])
    twice = {n for n, c in collections.Counter(c.name for c in b.clips).items() if c > 1}
    end = kl_str.data_end(b, dm, {at: o for o, (at, _n) in prior.items()})
    mine, old = [], []
    for x in bad:
        own = ((x.startswith('base clip ') and x[10:].rsplit(' moved', 1)[0] in twice)
               or (x.startswith('block ') and int(x.split()[1], 16) < end)
               or (x.startswith('clip ') and int(x.split('block ')[1].split()[0], 16) < end))
        (old if own else mine).append(x)
    added = {o: v for o, v in full.items() if o not in prior}
    for o, (at, n) in sorted(added.items()):
        dm.f.seek(o); m.f.seek(at)
        if at < end or dm.f.read(n) != m.f.read(n):
            mine.append('appended block %#x is not the block %#x of the campaign\'s stream file' % (at, o))
        got = {c.name: c for c in m.blocks.get(at, [])}
        for c in dm.blocks[o]:
            g = got.get(c.name)
            if g is None or (g.size, g.fmt, g.lip, g.layer) != (c.size, c.fmt, c.lip, c.layer):
                mine.append('clip %s of appended block %#x is not in the index as Dead Men has it' % (c.name, at))
    facts = dict(base=base, base_size=b.size, out=out, size=m.size, base_data_end=end, blocks_in_map=len(full), appended=len(added),
                 appended_clips=sum(len(dm.blocks[o]) for o in added), build_id='%x' % m.build)
    for x in (b, m, dm):
        x.close()
    log('%s: %d bytes = base %d + %d; %d blocks (%d clips) appended behind %#x; problems of the appended blocks: %d; of the base (there before): %d' % (
        out, facts['size'], facts['base_size'], facts['size'] - facts['base_size'], facts['appended'], facts['appended_clips'], end, len(mine), len(old)))
    for x in mine:
        log('  PROBLEM ' + x)
    for x in old:
        log('  (base) ' + x)
    return mine, old, facts


def stream(base=None, out=None, log=print, verify_only=False):
    """The base stream file + the streamed clips of all scripts -> (out path, problems, facts).
    The base's bytes up to the end of its last data block are copied unchanged (kl_str.merge): every level built
    against the base's .map.json stays valid with the new file."""
    import kl_str
    P = kl_str.paths()
    base, out = base or P['merged'], out or str_out()
    if not verify_only:
        prior = kl_str.load_map(base + '.map.json') if os.path.isfile(base + '.map.json') else None
        want = stream_need()
        dm = kl_str.Stream(P['dm'])
        new = [o for o in want if not prior or o not in prior]
        cost = sum(dm.extents()[o] - o for o in new)
        log('talk clips: %d blocks (%d clips) of the campaign\'s stream file; %d are in the base already; %d to append, %.2f MB' % (
            len(want), sum(len(dm.blocks[o]) for o in want), len(want) - len(new), len(new), cost / 2.0 ** 20))
        dm.close()
        kl_str.merge(base, P['dm'], want, out, prior, log)
    mine, _old, facts = stream_verify(base, out, log)
    return out, mine, facts


# ------------------------------------------------------------------ the build
def _ini_who(folder):
    """Wardrobe character numbers of Kane and Lynch (KLWardrobe.ini beside the archive; klchar.c's KLChar values)."""
    out, cur = {}, None
    p = os.path.join(folder, 'KLWardrobe.ini')
    if os.path.isfile(p):
        for line in open(p, encoding='latin1'):
            line = line.strip()
            if line.startswith('[Character.'):
                cur = int(line[11:-1])
            elif cur and line.startswith('Name=') and line[5:] in (K, L):
                out[line[5:]] = cur
    return out


def blast_time(sc):
    """Seconds from the round-start event to the blast: field 0 of the TriggerDelay2 kl_fa_author made the blast
    timer, None when the level has none."""
    import kl_fa
    for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2'):
        if sc.names[k] == BLAST_TIMER and isinstance(v[0], float):
            return v[0]
    return None


def settings_keys(sc):
    """Lower-case line keys the level's settings object already speaks (a pool must not repeat them)."""
    out = set()
    for _k, _i, v in kl_voice.settings(sc):
        for f in kl_voice.line_fields():
            if f < len(v) and isinstance(v[f], str) and v[f]:
                out.add(v[f].strip('/').lower())
    return out


def pools(leaves, taken, log=print, spell=None):
    """POOLS against a build's .LOC ({lower key: sound id}) and the keys its settings already use.
    -> [(name, who, on, [keys])], with Squad pools spelled out per voice and unusable keys left out (said aloud).
    spell: {lower key: the key as the .LOC spells it}. The game's look-up 0x828fa0 is CASE-SENSITIVE (LIVE, KLHook.log
    2026-10-15: every lower-case squad key 'is not in this level's .LOC', every mixed-case key was said), so the Squad
    keys, which come out of the lower-cased dict, are written in the .LOC's own spelling."""
    spell = spell or {}
    out = []
    for name, who, on, keys in POOLS:
        if who == 'Squad':
            for tail, voice in (('_squad', 'Squad1'), ('_squad02', 'Squad2')):
                ks = []
                for pat in keys:
                    pre = pat[:-1].lower()
                    ks += sorted(k for k, sid in leaves.items() if k.startswith(pre) and k.endswith(tail) and sid)[:SQUAD_MAX // len(keys) + 1]
                out.append(('%s%s' % (name, voice[-1]), voice, on, [spell.get(k, k) for k in ks[:SQUAD_MAX]]))
            continue
        ok = []
        for k in keys:
            if who == 'Any':
                miss = [n for n in range(1, kl_voice.HEISTERS + 1) if not leaves.get('%s_c%d' % (k.lower(), n))]
                if k.lower() in taken:
                    log('  pool %s: %s left out - the level\'s settings already speak it' % (name, k)); continue
            else:
                miss = [] if leaves.get(k.lower()) else [k]
            if miss:
                log('  pool %s: %s left out - no leaf with a sound (%s)' % (name, k, miss)); continue
            ok.append(k)
        out.append((name, who, on, ok))
    return out


def write_ini(path, sp, who, pl, pairs, facts):
    by_key = {ln['key']: ln for ln in sp['lines'].values()}
    o = ['; written by tools/kl_fa_talk.py - belongs to the level archive beside it (hook part kltalk, re\\talk.md 3)',
         '; every key is a PLAIN .LOC key of this level: one lookup (kl2 0x828fa0), then the say call (0x421c70)',
         '[Talk]', 'Version=1', 'Map=%s' % sp['map'],
         'Kane=%d' % who.get(K, 0), 'Lynch=%d' % who.get(L, 0),
         '; ^ wardrobe character numbers (KLWardrobe.ini beside this file, klchar.c\'s KLChar); 0 = the build has no such body',
         'StreamBytes=%d' % facts['stream_bytes'],
         '; ^ the least size of <game>\\PC_Def.str this level\'s streamed lines need (0 = any): a smaller file = silent lines',
         'Scenes=%d' % len(sp['scenes'])]
    if facts.get('blast') is not None:
        o.append('Blast=%.2f' % facts['blast'])
        o.append('; ^ seconds from the round-start event to the blast (the level\'s own timer); the countdown scene is timed by it')
    for i, sc in enumerate(sp['scenes'], 1):
        o += ['[Scene.%d]' % i, 'Name=%s' % sc['name'], 'When=%s' % sc['when'], 'Delay=%.2f' % (sc['delay'] or 0.0), 'Needs=%s' % sc['needs']]
        if sc['box']:
            o.append('Box=%s' % ','.join('%g' % v for v in sc['box']))
        if sc['not_before']:
            o.append('NotBefore=%g' % sc['not_before'])
        o.append('Lines=%d' % len(sc['lines']))
        for j, (w, key, at, secs) in enumerate(sc['lines'], 1):
            o.append('Line.%d=%s,%.2f,%.2f,%s' % (j, w, at, secs, key))
            o.append(';   %s' % by_key[key]['texts'].get('English', b'').decode('latin1').encode('ascii', 'replace').decode())
    o += ['[Chatter]'] + ['%s=%s' % kv for kv in CHATTER.items()] + ['Pools=%d' % len(pl), 'Pairs=%d' % len(pairs)]
    for i, (name, w, on, keys) in enumerate(pl, 1):
        o += ['[Pool.%d]' % i, 'Name=%s' % name, 'Who=%s' % w, 'On=%s' % on, 'Keys=%d' % len(keys)]
        o += ['Key.%d=%s' % (j, k) for j, k in enumerate(keys, 1)]
    for i, (a, ka, b, kb) in enumerate(pairs, 1):
        o += ['[Pair.%d]' % i, 'Call=%s,%s' % (a, ka), 'Reply=%s,%s' % (b, kb)]
    with open(path, 'w', encoding='ascii', newline='\r\n') as f:
        f.write('\n'.join(o) + '\n')


def build(src, dst, name, adpcm='memory', str_path=None, blast=None, log=print, slot=SLOT):
    """The talk of map `name` into a copy of build folder src -> report dict. Raises on any problem."""
    import kl_fa, kl_graft, kl_str
    if os.path.abspath(dst) == os.path.abspath(src):
        raise ValueError('the output folder is the build\'s own')
    name = ALIAS.get(name, name)
    str_path = str_path or str_out()
    if not os.path.isfile(str_path + '.map.json'):
        raise ValueError('%s: not there - run `kl_fa_talk.py stream` first' % str_path)
    strmap = {k: v[0] for k, v in kl_str.load_map(str_path + '.map.json').items()}
    zp = os.path.join(src, slot + '_Main.zip')
    with zipfile.ZipFile(zp) as z:
        order = z.namelist()
        files = {n: z.read(n) for n in order}
    ext = {n.rsplit('_Main', 1)[1]: n for n in order if '_Main' in n}
    side = lambda s: os.path.join(src, slot + '_Main' + s)
    snd, whd, wav, ls = files[ext['.SND']], kl_snd.read(side('.WHD')), kl_snd.read(side('.WAV')), kl_snd.read(side('_LS.SND'))
    before = sizes(src)
    sc = kl_fa.load(zp)[0]
    if name == 'retomoto':
        t = blast_time(sc)
        if t is None and blast is None:
            raise ValueError('%s has no blast timer (%s): not a Retomoto build? (--blast N to say the time)' % (src, BLAST_TIMER))
        if t is not None and blast is not None and abs(t - blast) > 1e-3:
            raise ValueError('--blast %g, but the level\'s timer says %g' % (blast, t))
        blast = t if t is not None else blast
    sp = script(name, blast)
    for s in sp['scenes']:
        if s['delay'] is not None and s['delay'] < 0:
            raise ValueError('scene %s would start %.2f s before the round' % (s['name'], -s['delay']))
    # ---- the bank
    base0 = kl_snd.Snd('dd', snd, ls).walk()
    S, s_whd, _recs, _k = source(sp['source'])
    roots = {ln['sid'] for ln in sp['lines'].values()}
    st = collections.Counter()
    snd2, whd2, wav2, omap = kl_snd.merge(base0, S, whd, wav, s_whd, kl_snd.read(kl_snd.beside(sp['source'], '.WAV', 'dm')), roots,
                                          strmap=strmap, log=lambda *_a: None, stats=st,
                                          inmem=kl_voice.stream_clip if adpcm == 'memory' else None)
    lost = [ln['key'] for ln in sp['lines'].values() if not omap.get(ln['sid'])]
    bad = ['line %s has no sound in the merged bank' % k for k in lost]
    for k in ('stream clips not in the merged stream file', 'stream clips of a group that is torn in the source or not in the merged stream file',
              'waves that name no .WHD record', 'roots that are no object of the source bank', 'streamed ADPCM clips left streamed (not readable)'):
        if st[k]:
            bad.append('%d %s' % (st[k], k))
    ls2 = kl_snd.ls_bank(ls, kl_snd.u32(snd2, 0))
    v_bad, counts = kl_snd.verify(base0, snd2, whd2, wav2, ls2, omap)
    bad += v_bad
    clips = kl_snd.stream_index(str_path)[1]
    n_add, n_miss = kl_snd.verify_streams(whd, whd2, clips)
    if n_miss:
        bad.append('%d added stream records are no clip of %s' % (n_miss, str_path))
    if bad:
        raise ValueError('bank: ' + '; '.join(bad))
    # ---- the .LOC: one plain leaf per line, in every language file that is not a stub
    locs, added = {}, None
    for lang, mname in kl_loc.members(zipfile.ZipFile(zp)).items():
        t = kl_loc.parse(files[mname])
        if t is None:
            continue
        tab = next((k for k in t if k.name.lower() == PREFIX.lower().encode() and k.kids is not None), None)
        if tab is None:
            tab = kl_loc.Node(PREFIX.encode(), kl_loc.TABLE, [])
            kl_loc._insert(t, tab)
        n = 0
        for ln in sp['lines'].values():
            leaf = ln['key'].split('/')[-1].encode('latin1')
            if any(k.name.lower() == leaf.lower() for k in tab.kids):
                raise ValueError('%s: the .LOC already has %s' % (lang, ln['key']))
            kl_loc._insert(tab.kids, kl_loc.leaf(leaf, ln['texts'].get(lang, ln['texts'].get('English', b'')), omap[ln['sid']]))
            n += 1
        locs[mname] = kl_loc.build(t)
        if kl_loc.build(kl_loc.parse(locs[mname])) != locs[mname]:
            raise ValueError('%s: the new .LOC does not round-trip' % lang)
        added = n
    # ---- pools and pairs against the new English .LOC
    eng = next(n for l, n in kl_loc.members(zipfile.ZipFile(zp)).items() if l == 'English')
    eng_leaves = list(kl_loc.leaves(kl_loc.parse(locs[eng])))
    leaves = {p.lower(): kl_loc.fields(n)[2] or 0 for p, n in eng_leaves}
    pl = pools(leaves, settings_keys(sc), log, spell={p.lower(): p for p, _n in eng_leaves})
    pairs = [p for p in PAIRS if leaves.get(p[1].lower()) and leaves.get(p[3].lower())]
    for p in PAIRS:
        if p not in pairs:
            log('  pair %s / %s left out - a leaf without a sound' % (p[1], p[3]))
    # ---- what of the stream file the level's lines need
    recs2 = W.records('dd', whd2)
    T = kl_snd.u32(whd, 0)
    ends = [(f['off'] | (f['offhi'] << 32)) + f['size'] for r, f in recs2.items() if r >= T and f['fmt'] & W.STREAMED and not f['fmt'] & W.LANGFILE]
    facts = dict(stream_bytes=max(ends) if ends else 0, blast=blast)
    # ---- write
    new = dict(files)
    new[ext['.SND']] = snd2
    new.update(locs)
    os.makedirs(dst, exist_ok=True)
    out_zip = kl_graft.write_zip(os.path.join(dst, slot + '_Main.zip'), [(n, new[n]) for n in order])
    beside = {'.WHD': whd2, '.WAV': wav2, '_LS.SND': ls2}
    for f in os.listdir(src):
        p = os.path.join(src, f)
        if not os.path.isfile(p) or p == zp or f.startswith(('audit.', 'preflight.', 'talk.')):
            continue
        if f.startswith(slot + '_Main') and f[len(slot) + 5:] in beside:
            with open(os.path.join(dst, f), 'wb') as fh:
                fh.write(beside[f[len(slot) + 5:]])
        else:
            shutil.copyfile(p, os.path.join(dst, f))
    who = _ini_who(src)
    write_ini(os.path.join(dst, 'KLTalk.ini'), sp, who, pl, pairs, facts)
    after = sizes(dst)
    changed = sorted(e for e, n in ext.items() if new[n] != files[n])
    rep = collections.OrderedDict(
        source=src, out=dst, map=name, campaign_level=sp['source'], adpcm=adpcm, stream_file=str_path, stream_bytes_needed=facts['stream_bytes'],
        lines=len(sp['lines']), scenes=len(sp['scenes']), loc_leaves_added_per_language=added, languages=len(locs),
        members_changed=changed, bank={k: v for k, v in st.items() if v}, sounds=counts['table: sound'], waves=counts['table: wave'],
        sounds_before=len(base0.tables[1]), waves_before=len(base0.tables[4]), stream_records_added=n_add,
        pools={n: len(k) for n, _w, _o, k in pl}, pairs=len(pairs), wardrobe=who, blast=blast, big_before=before, big_after=after)
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):                              # kl_maps.audit compares the folder with what was measured
        import kl_maps
        s = json.load(open(sj))
        s['talk'] = changed
        s['same'] = [e for e in s.get('same', []) if e not in changed]
        s['final'] = kl_maps.member_ids(dst)
        with open(sj, 'w') as f:
            json.dump(s, f, indent=1)
    with open(os.path.join(dst, 'graft.txt'), 'a') as f:
        f.write('kl_fa_talk: %d lines of %s (%s) from %s; ADPCM %s; stream file %s (%d bytes needed)\n' % (
            len(sp['lines']), name, sp['source'], src, adpcm, str_path, facts['stream_bytes']))
    with open(os.path.join(dst, 'talk.json'), 'w') as f:
        json.dump(rep, f, indent=1)
    log('written %s: %d lines in %d scenes (%s), %d leaves per language in %d languages; members changed: %s' % (
        out_zip, len(sp['lines']), len(sp['scenes']), sp['source'], added, len(locs), ' '.join(changed)))
    log('  bank: sounds %d -> %d, waves %d -> %d; %s' % (rep['sounds_before'], rep['sounds'], rep['waves_before'], rep['waves'], dict(rep['bank'])))
    log('  the four large blocks: ' + ', '.join('%s %d -> %d' % (e, before[e], after[e]) for e in before))
    if not who.get(K) or not who.get(L):
        log('  NOTE the build has no KLWardrobe.ini with Kane and Lynch: KLTalk.ini says Kane=%d Lynch=%d (0 = nobody can wear him)' % (who.get(K, 0), who.get(L, 0)))
    return rep


# ------------------------------------------------------------------ the check
def read_ini(path):
    out, cur = collections.OrderedDict(), None
    for line in open(path, encoding='latin1'):
        line = line.strip()
        if not line or line[0] == ';':
            continue
        if line[0] == '[':
            cur = out.setdefault(line[1:-1], collections.OrderedDict())
        else:
            k, v = line.split('=', 1)
            cur[k] = v
    return out


def check(folder, str_path=None, log=print, slot=SLOT):
    """Every check on a finished folder -> ([(severity, text)], facts). FAIL = must be none before an install."""
    import kl_fa
    find, facts = [], collections.OrderedDict()
    fail, note = (lambda s: find.append(('FAIL', s))), (lambda s: find.append(('NOTE', s)))
    zp = os.path.join(folder, slot + '_Main.zip')
    ip = os.path.join(folder, 'KLTalk.ini')
    if not os.path.isfile(ip):
        return [('FAIL', 'no KLTalk.ini beside the archive')], facts
    ini = read_ini(ip)
    str_path = str_path or str_out()
    sc, S, recs, leaves = kl_voice.load(zp)
    wav = os.path.getsize(os.path.join(folder, slot + '_Main.WAV'))
    ls = kl_snd.read(os.path.join(folder, slot + '_Main_LS.SND'))
    with zipfile.ZipFile(zp) as z:
        for x in kl_snd.Snd('dd', z.read(next(n for n in z.namelist() if n.endswith('_Main.SND'))), ls).walk().clean():
            fail('bank: ' + x)                          # walked WITH its loading-sound bank, whose strings live in it
    if kl_snd.u32(ls, 0) != S.T:
        fail('_LS.SND does not name the bank\'s trailer')
    miss = sum(1 for _o, _i, r in S.waves() if r not in recs)
    if miss:
        fail('%d wave references hit no .WHD record' % miss)
    mem = [f for f in recs.values() if not f['fmt'] & W.STREAMED]
    out = sum(1 for f in mem if not 16 <= (f['off'] | (f['offhi'] << 32)) <= wav - f['size'])
    if out:
        fail('%d in-memory records without their data in the .WAV' % out)
    try:
        clips = kl_snd.stream_index(str_path)[1]
        facts['stream file'] = '%s (%d bytes)' % (str_path, os.path.getsize(str_path))
    except (OSError, ValueError):
        clips = None
        note('stream file %s not readable: streamed clips not checked' % str_path)
    need = int(ini['Talk'].get('StreamBytes', 0))
    if clips is not None and need > os.path.getsize(str_path):
        fail('the level needs a stream file of %d bytes, %s has %d' % (need, str_path, os.path.getsize(str_path)))
    facts['stream bytes needed'] = need
    try:
        inst = os.path.getsize(kl_snd.stream_file('dd'))
        facts['installed stream file'] = inst
        if need > inst:
            note('the PC_Def.str in the game folder now has %d bytes: the level needs %d - install the stream file with the level' % (inst, need))
    except OSError:
        pass
    # ---- all languages hold the same keys with the same sound
    with zipfile.ZipFile(zp) as z:
        langs = {lang: kl_loc.parse(z.read(n)) for lang, n in kl_loc.members(z).items()}
    per = {lang: {p.lower(): kl_loc.fields(n)[2] or 0 for p, n in kl_loc.leaves(t)} for lang, t in langs.items() if t is not None}
    exact = {p for p, _n in kl_loc.leaves(langs['English'])} if langs.get('English') is not None else None
    state, secs = collections.Counter(), {}

    def one(key, what):
        """A plain key the way the exe finds it; -> seconds of its clip or None"""
        k = key.lower()
        if exact is not None and key not in exact and k in leaves:
            fail('%s: %s is spelled otherwise in the .LOC - the game\'s look-up is case-sensitive (LIVE 2026-10-15)' % (what, key))
        st, rec = kl_voice._clip(S, recs, leaves, k, clips)
        state[st] += 1
        if rec is None:
            fail('%s: %s - %s' % (what, key, st)); return None
        for lang, d in per.items():
            if d.get(k) != leaves[k]:
                fail('%s: %s is not in the %s .LOC with the same sound' % (what, key, lang))
        w = kl_snd.u32(S.b, leaves[k] + 0x14)
        f = recs[kl_snd.u32(S.b, w + 0x14)]
        return f['samples'] / float(f['rate'])
    used, n_lines = set(), 0
    names = collections.OrderedDict()
    for i in range(1, int(ini['Talk']['Scenes']) + 1):
        s = ini.get('Scene.%d' % i)
        if s is None:
            fail('Scene.%d is missing' % i); continue
        names.setdefault(s['Name'], []).append(s['Needs'])
        if s['When'] not in ('Start', 'Stage1', 'Stage2', 'Stage3', 'Aboard', 'Join', 'Box') or s['Needs'] not in ('Kane', 'Lynch', 'Both', 'KaneOnly', 'LynchOnly'):
            fail('Scene.%d: When=%s Needs=%s' % (i, s['When'], s['Needs']))
        if (s['When'] == 'Box') != ('Box' in s) or ('Box' in s and len(s['Box'].split(',')) != 6):
            fail('Scene.%d: a Box scene needs six numbers, another none' % i)
        end = 0.0
        for j in range(1, int(s['Lines']) + 1):
            w, at, ln, key = s['Line.%d' % j].split(',', 3)
            at, ln = float(at), float(ln)
            n_lines += 1; used.add(key.lower())
            if w not in (K, L):
                fail('Scene.%d line %d: speaker %s' % (i, j, w))
            if s['Needs'] in ('KaneOnly', 'LynchOnly') and w != s['Needs'][:-4] or s['Needs'] in (K, L) and w != s['Needs']:
                fail('Scene.%d (%s) has a line of %s' % (i, s['Needs'], w))
            t = one(key, 'Scene.%d line %d' % (i, j))
            if t is not None and abs(t - ln) > 0.011:
                fail('Scene.%d line %d: the ini says %.2f s, the clip has %.2f' % (i, j, ln, t))
            if at < end - 0.011:
                fail('Scene.%d line %d starts at %.2f, the line before it ends at %.2f' % (i, j, at, end))
            end = at + ln
    facts['scenes'] = '%d (%s)' % (len(names), ', '.join('%s: %s' % (n, '/'.join(v)) for n, v in names.items()))
    facts['scene lines'] = '%d (%d keys)' % (n_lines, len(used))
    # ---- the countdown against the level's own blast timer
    t = blast_time(sc)
    if 'Blast' in ini['Talk']:
        b = float(ini['Talk']['Blast'])
        if t is None or abs(t - b) > 1e-3:
            fail('KLTalk.ini says the blast comes at %.2f s, the level\'s timer says %s' % (b, t))
        cd = [ini['Scene.%d' % i] for i in range(1, int(ini['Talk']['Scenes']) + 1) if ini.get('Scene.%d' % i, {}).get('Name') == 'countdown']
        hit = [float(c['Delay']) + float(c['Line.%d' % j].split(',')[1]) for c in cd for j in range(1, int(c['Lines']) + 1)
               if c['Line.%d' % j].lower().endswith('countdown_050_hero')]
        if len(hit) != 1 or abs(hit[0] - b) > 0.011:
            fail('the countdown\'s NOW! starts at %s, the blast is at %.2f' % (hit, b))
        else:
            first = float(cd[0]['Delay'])
            facts['countdown'] = 'first word %.2f s after the round-start event (%.2f s %s GO), NOW! at %.2f = the blast' % (
                first, abs(first - GO), 'before' if first < GO else 'after', hit[0])
    elif t is not None:
        note('the level has a blast timer (%.2f s) and KLTalk.ini no countdown' % t)
    # ---- pools and pairs
    taken = settings_keys(sc)
    n_pool = collections.Counter()
    seen = {}
    for i in range(1, int(ini['Chatter']['Pools']) + 1):
        p = ini['Pool.%d' % i]
        for j in range(1, int(p['Keys']) + 1):
            key = p['Key.%d' % j]
            if (p['Who'], key.lower()) in seen:
                fail('pool %s: %s is also in pool %s' % (p['Name'], key, seen[(p['Who'], key.lower())]))
            seen[(p['Who'], key.lower())] = p['Name']
            if key.lower() in used:
                fail('pool %s: %s is a scene line' % (p['Name'], key))
            if p['Who'] == 'Any':
                if key.strip('/').lower() in taken:
                    fail('pool %s: %s is a line the level\'s settings already speak (it would repeat)' % (p['Name'], key))
                for n in range(1, kl_voice.HEISTERS + 1):
                    one('%s_C%d' % (key, n), 'pool %s' % p['Name'])
            else:
                one(key, 'pool %s' % p['Name'])
            n_pool[p['Who']] += 1
        if not int(p['Keys']):
            note('pool %s is empty on this build' % p['Name'])
    for i in range(1, int(ini['Chatter']['Pairs']) + 1):
        p = ini['Pair.%d' % i]
        for side in ('Call', 'Reply'):
            one(p[side].split(',', 1)[1], 'Pair.%d' % i)
    facts['pool keys by speaker'] = dict(n_pool)
    facts['pairs'] = int(ini['Chatter']['Pairs'])
    facts['clips by form'] = dict(state)
    dup = collections.Counter(S.name(o) for o in S.tables[1] if o < S.T)
    d = sum(1 for k in used if dup[S.name(leaves[k])] > 1) if not any(s == 'FAIL' for s, _t in find) else 0
    if d:
        note('%d scene lines\' sound names stand twice in the bank (an earlier step brought the same clip)' % d)
    who = _ini_who(folder)
    if int(ini['Talk']['Kane']) != who.get(K, 0) or int(ini['Talk']['Lynch']) != who.get(L, 0):
        fail('KLTalk.ini Kane=%s Lynch=%s, KLWardrobe.ini has %s' % (ini['Talk']['Kane'], ini['Talk']['Lynch'], who))
    if not who.get(K) or not who.get(L):
        note('no wardrobe with Kane and Lynch beside the archive: nobody can wear them, nothing will be said')
    facts['wardrobe'] = who
    facts['bank'] = 'sounds %d, waves %d' % (len(S.tables[1]), len(S.tables[4]))
    facts['big'] = dict(sizes(folder))
    if log:
        log('talk of %s' % folder)
        for k, v in facts.items():
            log('  %s: %s' % (k, v))
        for sev, text in find:
            log('  %s %s' % (sev, text))
        log('  findings: FAIL %d, NOTE %d' % (sum(1 for s, _t in find if s == 'FAIL'), sum(1 for s, _t in find if s == 'NOTE')))
    return find, facts


def empty(folder, log=print, slot=SLOT):
    """The line groups of the level's settings object that name no key (re/talk.md 4.1)."""
    import kl_fa
    sc = kl_fa.load(os.path.join(folder, slot + '_Main.zip'))[0]
    lf = kl_voice.line_fields()
    for _k, _i, v in kl_voice.settings(sc):
        e = sorted(f for f in lf if f < len(v) and not v[f])
        runs, a = [], None
        for f in e:
            if a is not None and f == b + 1:
                b = f
            else:
                if a is not None:
                    runs.append((a, b))
                a = b = f
        if a is not None:
            runs.append((a, b))
        log('%s: %d of %d line fields empty: %s' % (folder, len(e), len(lf), ' '.join('%d' % a if a == b else '%d-%d' % (a, b) for a, b in runs)))
        log('  filled per-character fields: %d, plain: %d' % (sum(1 for f in lf if f < len(v) and v[f] and lf[f][0]), sum(1 for f in lf if f < len(v) and v[f] and not lf[f][0])))


def main():
    a = sys.argv[1:]
    opt = lambda n, d=None: (a[a.index(n) + 1] if n in a else d)
    flags = {'--adpcm', '--str', '--blast', '--map', '--base', '--out'}
    pos = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or a[i - 1] not in flags)]
    cmd = pos[0] if pos else 'help'
    if cmd == 'plan':
        plan(pos[1:] or None)
    elif cmd == 'stream':
        _o, bad, _f = stream(opt('--base'), opt('--out'), verify_only='--verify' in a)
        sys.exit(1 if bad else 0)
    elif cmd == 'build':
        if opt('--adpcm', 'memory') not in ('memory', 'stream') or not opt('--map'):
            sys.exit(__doc__)
        b = opt('--blast')
        build(pos[1], pos[2], opt('--map'), opt('--adpcm', 'memory'), opt('--str'), float(b) if b else None)
        find, _f = check(pos[2], opt('--str'))
        sys.exit(1 if any(s == 'FAIL' for s, _t in find) else 0)
    elif cmd == 'check':
        find, _f = check(pos[1], opt('--str'))
        sys.exit(1 if any(s == 'FAIL' for s, _t in find) else 0)
    elif cmd == 'inventory':
        inventory(pos[1] if len(pos) > 1 else None)
    elif cmd == 'sizes':
        for f in pos[1:]:
            print(f, dict(sizes(f)))
    elif cmd == 'empty':
        for f in pos[1:]:
            empty(f)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
