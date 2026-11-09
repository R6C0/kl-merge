"""campaign_1109 kit: luvsic's Dead Men campaign (ported into KLHook, in contribution with luvsic) into Dog Days.

install.py           dll (pinned live 50d20cd1 -> SHIP campaign build), KLHook.ini campaign sections, level picker bat.
install.py --undo    puts dll + ini back from the *.before-campaign1109 backups (only if they are still ours), removes the bat.
The converted levels themselves are installed / removed by tools/kl_campaign.py install / undo (own folders, own manifests).
"""
import hashlib, os, shutil, subprocess, sys

DD = os.environ.get('KLCAMP_DD') or r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'   # KLCAMP_DD = scratch rehearsal
KIT = os.path.dirname(os.path.abspath(__file__))
SHIP = r'C:\kl-merge\kl-merge\.claude\worktrees\integ\klhook\out_campaign_1109\ship\dinput8.dll'
LIVE_DLL = '50d20cd161b4d1074c72c79950e70f67'
LIVE_INI = '4cb8faa0cad54a33d4803df8501a708f'
TAG = '.before-campaign1109'
BAT = 'Dead Men Campaign.bat'

# Sections appended to KLHook.ini (values from klhook/ini_campaign_*.txt, campaign-only switches turned on).
BLOCK = r"""
; ==== Dead Men campaign (luvsic's ANP loader ported into KLHook, in contribution with luvsic) - campaign_1109 ====
; Everything below acts ONLY while a converted Dead Men story level (Scenes\Locations\M01..M14) is loaded.
[Campaign]
; master switch for every campaign module (recommended on with the campaign installed)
Enable=1
; Scene ids M01..M14 start a converted level as its own scene (recommended on)
Routing=1
; <DD>\KLCampaign_load.txt = "M01 1" starts that level (Dead Men Campaign.bat writes it) (recommended on)
Trigger=1
AutoLoad=
AutoLoadDelayMs=12000
AutoLoadMode=1
; campaign saves go to <DataDir>\saves\Campaign, Dog Days' save is not written (recommended on)
SaveRedirect=1
; re-read Dog Days' own profile after leaving the campaign (recommended on)
ProfileReload=1
ReloadDelayMs=2000
; <DataDir>\ANP_progress.ini last / reached / done (recommended on)
Progress=1
; no Steam achievements while a campaign level runs (recommended on)
AchievementGuard=1
; Dead Men IMA-ADPCM .str streams decoded at read time (recommended off until benched)
Adpcm=0
DataDir=
Log=1
[CampGuard]
; crash guards from luvsic's loader, campaign levels only (recommended on); ListUserFA = every map (recommended off)
ListUser=1
ListUserFA=0
Gfx=1
Coll=1
Snd=1
SndDiv=0
NullList=1
BonesLights=1
Heap=1
[CampSquad]
; squad orders on campaign levels: 1 follow, 2 attack, 3 defend, Tab next (recommended on)
Enable=1
Recruit=start
RecruitAdopt=0
RecruitSettle=2
Critical=keep
Refuse=auto
AttackT=5
KeyFollow=0x31
KeyAttack=0x32
KeyDefend=0x33
KeyNext=0x09
KeyPrev=0
Log=1
[CampGive]
; 4 = give your gun to the selected squad mate (recommended on)
Enable=1
Key=0x34
Target=selected
Range=300
Swap=1
Types=6
Refuse=50,51,53,54
Drawn=1
Event=18
SwapClips=3
Dry=0
Log=1
[CampRappel]
; 2 = native rappel at rappel points when the level has the clips (recommended on)
Mode=2
Log=1
[CampRevive]
; wounded mercs: watch/log only (recommended on)
Enable=1
Live=0
Log=1
Difficulty=1
[CopSquad]
HeldGuard=0
"""
# Lines put inside the EXISTING [Grenade] section (G held = throw a grenade item; offline only).
GRENADE = """; Release: hold G to throw a grenade item (campaign port, offline only) (recommended on)
Release=1
ReleaseRange=2000
ReleaseSpeed=1000
ReleaseVMax=1500
ReleaseUp=150
ReleaseFwd=70
ReleaseCoolMs=1000
ReleaseConsume=1
ReleaseRefill=1
ReleaseEvent=30
"""


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def game_running():
    r = subprocess.run(['powershell', '-NoProfile', '-Command',
                        '@(Get-Process kl2 -ErrorAction SilentlyContinue | ForEach-Object { $_.Threads.Count }) -join " "'],
                       capture_output=True, text=True)
    return any(c.isdigit() and int(c) > 0 for c in r.stdout.split())


def new_ini(text):
    lines = text.split('\n')
    i = next(k for k, l in enumerate(lines) if l.strip().lower() == '[grenade]')
    if any(l.strip().lower().startswith('release=') for l in lines): sys.exit('ini already has Release= (installed?)')
    lines[i + 1:i + 1] = GRENADE.rstrip('\n').split('\n')
    out = '\n'.join(lines)
    if not out.endswith('\n'): out += '\n'
    return out + BLOCK.lstrip('\n')


def install():
    dll, ini = os.path.join(DD, 'dinput8.dll'), os.path.join(DD, 'KLHook.ini')
    if game_running(): sys.exit('kl2.exe is running: close the game first')
    if md5(dll) != LIVE_DLL: sys.exit('live dinput8.dll %s is not the pinned %s: refused' % (md5(dll), LIVE_DLL))
    if md5(ini) != LIVE_INI: sys.exit('live KLHook.ini %s is not the pinned %s: refused' % (md5(ini), LIVE_INI))
    for p in (dll + TAG, ini + TAG):
        if os.path.exists(p): sys.exit('%s exists: already installed? (run --undo first)' % p)
    text = open(ini, 'rb').read().decode('ascii')
    out = new_ini(text)
    shutil.copy2(dll, dll + TAG)
    shutil.copy2(ini, ini + TAG)
    shutil.copy2(SHIP, dll)
    open(ini, 'wb').write(out.encode('ascii'))
    shutil.copy2(os.path.join(KIT, BAT), os.path.join(DD, BAT))
    open(os.path.join(KIT, 'installed.md5'), 'w').write('%s dll\n%s ini\n' % (md5(dll), md5(ini)))
    print('installed: dll %s -> %s, ini %s -> %s, %s' % (LIVE_DLL[:8], md5(dll)[:8], LIVE_INI[:8], md5(ini)[:8], BAT))


def undo():
    dll, ini = os.path.join(DD, 'dinput8.dll'), os.path.join(DD, 'KLHook.ini')
    if game_running(): sys.exit('kl2.exe is running: close the game first')
    if md5(dll) != md5(SHIP): sys.exit('live dll is no longer the campaign build: refused (restore %s by hand)' % (dll + TAG))
    shutil.copy2(dll + TAG, dll); os.remove(dll + TAG)
    # ini: drop exactly what install added, so in-game edits of other keys survive
    text = open(ini, 'rb').read().decode('ascii')
    k = text.find(BLOCK.lstrip('\n').split('\n')[0])
    if k >= 0: text = text[:k]
    text = text.replace(GRENADE, '', 1)
    open(ini, 'wb').write(text.encode('ascii'))
    if md5(ini) == md5(ini + TAG): os.remove(ini + TAG); print('ini restored byte-exact')
    else: print('ini: campaign lines removed, other edits kept; backup left at %s' % (ini + TAG))
    b = os.path.join(DD, BAT)
    if os.path.exists(b): os.remove(b)
    print('dll %s, campaign bat removed' % md5(dll)[:8])


if __name__ == '__main__':
    undo() if '--undo' in sys.argv else install()
