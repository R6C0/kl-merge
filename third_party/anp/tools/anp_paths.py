"""Where the games and the work folder are.

Environment variables win: ANP_DD_GAME, ANP_DM_GAME, ANP_WORK. Otherwise the work folder is <repo>/work and each
game is looked up in the Steam libraries (registry + libraryfolders.vdf), then in the old VM mount (~/mnt)."""
import os, json
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
WORK = os.environ.get('ANP_WORK') or os.path.join(REPO, 'work')

# JC's kl-merge (used with permission) is checked out in KLMERGE. Its exact class schemas are pinned to the version
# the tested builds used: re/schemas_dd.json and re/schemas_dm.json from commit 8466319 (later commits replaced
# them with re/kl2.json and re/kaneandlynch.json in another format), plus tools/dd_enums.json.
# setup_workspace.py copies them into SCHEMAS.
# KL-MERGE CHANGE (the only edit to this vendored file): ANP_KLMERGE (set by tools/kl_campaign.py to the kl-merge repo
# root, where 8466319 is reachable and tools/kl_hvk.py, kl_gms.py, kl_scene.py live) wins over the work-folder checkout.
KLMERGE = os.environ.get('ANP_KLMERGE') or os.path.join(WORK, 'ext', 'kl-merge')
SCHEMAS = os.path.join(WORK, 'ext', 'schemas')
SCHEMA_COMMIT = '8466319'
SCHEMA_FILES = (('re/schemas_dd.json', 'schemas_dd.json'), ('re/schemas_dm.json', 'schemas_dm.json'),
                ('tools/dd_enums.json', 'dd_enums.json'))

def load_schema(name):
    with open(os.path.join(SCHEMAS, name), encoding='utf-8') as f:
        return json.load(f)

def schema_missing(e, optout):
    return SystemExit('kl-merge schema not readable (%s).\nPut kl-merge in %s and run tools/setup_workspace.py, '
                      'or set %s=0 for the older statistical conversion.' % (e, KLMERGE, optout))

def steam_libraries():
    libs = []
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as k:
            steam = os.path.normpath(winreg.QueryValueEx(k, 'SteamPath')[0])
        with open(os.path.join(steam, 'steamapps', 'libraryfolders.vdf'), encoding='utf-8', errors='replace') as f:
            for line in f:
                q = line.strip().split('"')
                if len(q) >= 4 and q[1] == 'path':
                    libs.append(os.path.join(q[3].replace('\\\\', '\\'), 'steamapps', 'common'))
        libs.append(os.path.join(steam, 'steamapps', 'common'))   # the registry's SteamPath is lower case
    except (ImportError, OSError):
        pass
    libs += [r'C:\Program Files (x86)\Steam\steamapps\common', os.path.expanduser('~/mnt')]
    return libs

def game_dir(env, folder):
    if os.environ.get(env): return os.environ[env]
    for lib in steam_libraries():
        p = os.path.join(lib, folder)
        if os.path.isdir(p): return p
    raise SystemExit('%s not found: set %s to its folder' % (folder, env))

DD_FOLDER = 'Kane & Lynch 2 - Dog Days'
DM_FOLDER = 'Kane and Lynch Dead Men'

def game_running(exe='kl2.exe'):
    """True if the game is running (Windows only; elsewhere always False)"""
    if os.name != 'nt': return False
    import subprocess
    r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq %s' % exe, '/NH'], capture_output=True, text=True)
    return exe.lower() in r.stdout.lower()
