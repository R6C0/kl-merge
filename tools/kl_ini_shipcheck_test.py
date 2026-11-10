#!/usr/bin/env python3
"""kl_ini_shipcheck_test.py - hand-made sample + live inis; also runs the real repo sample against itself (must PASS).
Exit 0 only when every check passes."""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_ini_shipcheck as S

FAILS = []


def check(cond, what):
    print(('ok    ' if cond else 'FAIL  ') + what)
    if not cond:
        FAILS.append(what)


SAMPLE = """; KLHook.ini sample
[KLHook]                 ; the hook
Log=1
MaxDumps=4
; Trace=1 (recommended off: diagnostic) one line per frame
;Trace=0
; TEST builds only (klprobe.c): the door chain
;[Probe]
;DoorProxy=0
;DoorLeaves=0   ; (recommended off, TEST diagnostics)
; OnlineTagProbe=1 (needs OnlineTags=1; (recommended on)): the cull reads a probe text
OnlineTagProbe=1
; OnlineBoxProbe (recommended on; log only): 'box probe:' lines
OnlineBoxProbe=1
; OnlineEscort=0 (recommended off until benched)
OnlineEscort=0
; OnlineEscortFar=800 (recommended off, only used with OnlineEscort on)
OnlineEscortFar=800
; OnlineLootStayM (recommended off = leave at 250, only with OnlineLootParts; 250, 80..800 game units)
OnlineLootStayM=250
; Censor=0 (recommended off until benched): a feature switch
Censor=0
; Hire=0 (bench only, recommended off) 1..16 = once per round per peer
Hire=0
; the TEST build only (klauto.c): PollLossMs (recommended on)
[Auto]
PollLossMs=5000

[Music]
;Folder=C:\\your\\mp3s
[Ambience]
Folder=C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days\\KLExpansion\\Ambience
[Bench]
"""

LIVE = """; owner's live ini, built from C:\\kl_build_1024\\merged_1110c
[KLHook]
Log=1
MaxDumps=8
Trace=1            ; stutter probe
DoorLeaves=1
OnlineTagProbe=1
OnlineBoxProbe=0
OnlineEscort=0
OnlineEscortFar=900
OnlineLootStayM=250
Censor=1
Hire=4
OnlineExitTrace=1
ReplicaProbe=0
Dummy=1
[Auto]
PollLossMs=5000
Enable=1
[Bench]
Script=C:\\kl_build_1024\\bench_1110\\run.ini
[Music]
Folder=C:\\Steam\\steamapps\\common\\PAYDAY 2\\assets
FolderB=G:\\SteamLibrary\\steamapps\\common\\Kane and Lynch Dead Men\\Music
[Ambience]
Folder=C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days\\KLExpansion\\Ambience
[Overlay]
OverlayDir=C:\\kl_build_1024\\mappool\\overlay
Name=D:\\x
[Campaign]
Enable=1
"""


def main():
    docs = S.parse_sample(SAMPLE)
    check(S.classify(docs['klhook']['trace']) == 'off', 'sample: Trace documented off from the comment line above its ;Trace=0')
    check(S.classify(docs['probe']['doorleaves']) == 'off', 'sample: ;[Probe] ;DoorLeaves goes to the commented-out section')
    check('doorleaves' not in docs['klhook'], 'sample: ... and not to [KLHook]')
    check(S.classify(docs['klhook']['onlinetagprobe']) == 'on', 'sample: OnlineTagProbe recommended on')
    check(S.classify(docs['klhook']['onlineboxprobe']) == 'on', 'sample: active key after ;[Probe] block belongs to the real section [KLHook]')
    check(S.classify(docs['klhook']['onlineescortfar']) == 'off', 'sample: OnlineEscortFar recommended off')
    check(S.classify(docs['auto']['polllossms']) == 'on', 'sample: header with inline comment + commented block parsed')
    check(S.classify(docs['klhook']['log']) is None, 'sample: Log has no recommendation')

    found = S.check(LIVE, SAMPLE, dd='C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days', pd2='C:\\Steam\\steamapps\\common\\PAYDAY 2', notes=True)
    by = {}
    for lv, sec, k, v, n, why in found:
        by.setdefault((lv, sec, k), []).append(why)
    pr = lambda *a: print('      ', *a)
    for f in found:
        pr(f[0], f[1], f[2], f[3][:30], f[4], f[5][:70])
    check(('WARN', 'KLHook', 'Trace') in by, 'live: Trace=1 is a WARN (recommended off: diagnostic)')
    check(('FEAT', 'KLHook', 'Censor') in by and ('WARN', 'KLHook', 'Censor') not in by, 'live: Censor=1 "recommended off until benched" is a FEAT, not a WARN')
    check(('WARN', 'KLHook', 'Hire') in by, 'live: Hire=4 "(bench only, recommended off)" is a WARN')
    check(('LOG', 'KLHook', 'Log') in by and ('LOG', 'KLHook', 'OnlineTagProbe') in by, 'live: Log=1 and the recommended-on OnlineTagProbe are LOG entries')
    check(('WARN', 'KLHook', 'DoorLeaves') not in by and ('NOTE', 'KLHook', 'DoorLeaves') in by,
          'live: DoorLeaves=1 under [KLHook] is only "key not in the sample" (the sample has it under ;[Probe])')
    check(('WARN', 'KLHook', 'OnlineTagProbe') not in by, 'live: OnlineTagProbe=1 recommended on -> no WARN')
    check(('WARN', 'KLHook', 'OnlineBoxProbe') not in by, 'live: OnlineBoxProbe=0 off -> nothing')
    check(('WARN', 'KLHook', 'OnlineEscortFar') not in by, 'live: OnlineEscortFar=900 inert while OnlineEscort=0')
    check(('WARN', 'KLHook', 'OnlineLootStayM') not in by, 'live: OnlineLootStayM=250 = "leave at 250"')
    check(('WARN', 'KLHook', 'OnlineExitTrace') in by, 'live: OnlineExitTrace=1 by name (undocumented) -> WARN')
    check(('WARN', 'KLHook', 'ReplicaProbe') not in by, 'live: ReplicaProbe=0 off -> nothing')
    check(('NOTE', 'KLHook', 'Dummy') in by, 'live: Dummy not in the sample -> NOTE')
    check(('WARN', 'KLHook', 'MaxDumps') not in by, 'live: MaxDumps=8 is not a diagnostic')
    check(('WARN', 'Auto', '') in by and 'Enable' in by[('WARN', 'Auto', '')][0] and 'PollLossMs' not in by[('WARN', 'Auto', '')][0],
          'live: [Auto] Enable=1 beyond the sample -> WARN naming Enable only')
    check(('WARN', 'Bench', '') in by, 'live: [Bench] Script= active -> WARN')
    check(('ERROR', 'Bench', 'Script') in by, 'live: [Bench] Script=C:\\kl_build_1024\\... -> ERROR (owner path)')
    check(('ERROR', 'Music', 'FolderB') in by and 'does not re-point' in by[('ERROR', 'Music', 'FolderB')][0],
          'live: FolderB=G:\\...Dead Men... -> ERROR (a game folder install never localizes)')
    check(('ERROR', 'Music', 'Folder') not in by and ('NOTE', 'Music', 'Folder') not in by, 'live: PAYDAY 2 Folder under --pd2 -> nothing')
    check(('ERROR', 'Ambience', 'Folder') not in by, 'live: Dog Days Folder under --dd -> nothing')
    check(('ERROR', 'Overlay', 'OverlayDir') in by, 'live: OverlayDir=C:\\kl_build_1024 -> ERROR')
    check(('ERROR', 'Overlay', 'Name') in by, 'live: Name=D:\\x -> ERROR')
    check(('NOTE', 'Campaign', '') in by, 'live: [Campaign] not in the sample -> NOTE')
    check(any(lv == 'NOTE' and n == 1 for lv, _, _, _, n, _ in found), 'live: comment line 1 names C:\\kl_build_1024 -> NOTE')
    check(found[0][0] == 'ERROR' and found[-1][0] == 'NOTE' and [f[0] for f in found] == sorted((f[0] for f in found), key=S.LEVELS.get),
          'findings sorted worst first (ERROR WARN FEAT LOG NOTE)')
    quiet = S.check(LIVE, SAMPLE, notes=False)
    check(all(f[0] != 'NOTE' for f in quiet) and any(f[0] == 'LOG' for f in quiet), 'notes=False drops every NOTE, keeps LOG (the summary counts them)')
    nodd = S.check(LIVE, SAMPLE, notes=True)
    check(('NOTE', 'Ambience', 'Folder') not in {(f[0], f[1], f[2]) for f in nodd}, 'no --dd: a localized path is never a finding')
    off = S.check(LIVE.replace('[Ambience]\nFolder=C:', '[Ambience]\nFolder=E:'), SAMPLE, dd='C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days', notes=True)
    check(('NOTE', 'Ambience', 'Folder') in {(f[0], f[1], f[2]) for f in off}, 'Dog Days path on another drive than --dd -> NOTE (install re-points it)')

    # the GetPrivateProfile semantics
    secs, _ = S.parse_ini('[A]\nK=1 ; c\nK=2\n[b]\nX=0\n[A]\nZ=3\n')
    check(secs['a']['k'][1] == '1' and secs['a']['z'][1] == '3' and secs['b']['x'][1] == '0', 'parse_ini: first duplicate wins, inline comment cut, repeated section merges')
    check(S.is_off('0 ; was 1') and S.is_off('') and S.is_off('off') and not S.is_off('0.5'), 'is_off strips the inline comment')
    check([m.group(0) for m in S.PATH_RE.finditer('"fire:/hit:/round:" lines; C:\\a\\b x; D:\\x')] == ['C:\\a\\b x', 'D:\\x'], 'PATH_RE: "e:/hit:" is not a drive path, C:\\a\\b and D:\\x are')

    # the real sample against itself: shippable as written (NOTE lines allowed)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'kl_ini_shipcheck.py'), S.SAMPLE, '--sample', S.SAMPLE],
                       capture_output=True, text=True)
    check(r.returncode == 0 and 'RESULT: PASS' in r.stdout, 'repo sample vs itself: PASS (%s)' % r.stdout.strip().split('\n')[-1])
    # the CLI on the fixture: exit 1 and the summary line
    d = os.path.join(HERE, '_shipcheck_tmp'); os.makedirs(d, exist_ok=True)
    try:
        open(os.path.join(d, 's.ini'), 'w').write(SAMPLE); open(os.path.join(d, 'l.ini'), 'w').write(LIVE)
        r = subprocess.run([sys.executable, os.path.join(HERE, 'kl_ini_shipcheck.py'), os.path.join(d, 'l.ini'), '--sample',
                            os.path.join(d, 's.ini'), '--json', os.path.join(d, 'o.json')], capture_output=True, text=True)
        check(r.returncode == 1 and 'RESULT: FAIL - 4 ERROR, 5 WARN' in r.stdout and 'FEAT' in r.stdout and 'logging on (3): [KLHook] Log=1, OnlineTagProbe=1, PollLossMs=5000' in r.stdout
              and 'NOTE  ' not in r.stdout, 'CLI on the fixture: exit 1, 4 ERROR 5 WARN, FEAT + logging line (incl. the TEST-only PollLossMs the sample wants on) printed, NOTE lines not (%s)' % r.stdout.strip().split('\n')[-1])
        check(os.path.getsize(os.path.join(d, 'o.json')) > 100, 'CLI --json written')
    finally:
        for fn in os.listdir(d):
            os.remove(os.path.join(d, fn))
        os.rmdir(d)
    print('RESULT: %s (%d fails)' % ('FAIL' if FAILS else 'PASS', len(FAILS)))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
