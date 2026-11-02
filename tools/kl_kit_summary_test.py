#!/usr/bin/env python3
"""Self-test of tools/kl_kit_summary.py (2026-11-02, offline, synthetic logs). Exit 1 on a failed check."""
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_kit_summary as k

HOST = """13:00:00.000 lobbyopt: round clock at state 25: rules 1 left[+4c]=250.0 played[+50]=0.0
13:00:01.000 assert in a netsmooth line
13:00:02.000 heli: fault something
13:00:03.000 npc 5 is dead or gone
13:00:04.000 npc 6 is dead or gone
13:00:05.000 ASSERT hit somewhere
13:00:06.000 botfill: tactics: round summary: 1 bot(s), 2 total (x), 1 boarded
13:00:07.000 botfill: tactics: round summary: 7 bot(s) given orders, 4130000 total (hook tally), 7 boarded, 6 stack(s)
13:00:08.000 lobbyopt: round clock at state 25: rules 1 left[+4c]=120.5 played[+50]=0.0
13:00:09.000 RESULT PASS exit code 0, asserts 0, faults 0, loads 2, soft asserts 3
"""


def main():
    fails = []

    def chk(name, got, want):
        if got != want:
            fails.append('%s: got %r want %r' % (name, got, want))

    with tempfile.TemporaryDirectory() as t:
        kit, solo = os.path.join(t, 'kit'), os.path.join(t, 'solo')
        os.makedirs(kit)
        with open(os.path.join(kit, 'maps_X.txt'), 'w') as f:
            f.write('# c\n\nT1A|DM03|F03|2|900\nT1B|DD05|F05|0|900\n')
        chk('kit', k.read_kit(kit), ['T1A_DM03', 'T1B_DD05'])
        d = os.path.join(solo, 'T1A_DM03', 'inst1')
        os.makedirs(d)
        with open(os.path.join(d, 'KLHook.log'), 'w') as f:
            f.write(HOST)
        s = k.summarize(os.path.join(d, 'KLHook.log'), [re.compile('botfill')])
        chk('exists', s['exists'], True)
        chk('assert', s['assert'], 0)     # from the RESULT line, not the counted lines
        chk('fault', s['fault'], 0)
        chk('dead', s['dead'], 2)
        chk('money', s['money'], 4130000)
        chk('boarded', s['boarded'], 7)
        chk('clocks', s['clocks'], ['250.0', '120.5'])
        chk('result', s['result'].endswith('soft asserts 3'), True)
        chk('grep n', s['grep'][0][0], 2)
        chk('grep last', len(s['grep'][0][1]), 2)
        s2 = k.summarize(os.path.join(solo, 'T1B_DD05', 'inst2', 'KLHook.log'), [])
        chk('missing', s2['exists'], False)
        # no RESULT line: counts come from the lines themselves
        with open(os.path.join(d, 'b.log'), 'w') as f:
            f.write('x assert\ny Fault\nz netsmooth assert\n')
        s3 = k.summarize(os.path.join(d, 'b.log'), [])
        chk('count', (s3['assert'], s3['fault'], s3['result']), (1, 1, None))
        # --batch: KLHook.result per seat + run.txt RESULT line + kit slot check
        RES = 'state=%s\nreason=script reached pass\nscene=SCENES\\Locations\\%s\\%s_Main.gms\nlevel_loaded=%s\nasserts=%s\nfaults=0\nsoft_asserts=%s\n'

        def run(name, h, c, rt='RESULT: inst1 IN ROUND, inst2 IN ROUND'):
            rd = os.path.join(solo, name)
            for inst, txt in (('inst1', h), ('inst2', c)):
                os.makedirs(os.path.join(rd, inst), exist_ok=True)
                if txt is not None:
                    with open(os.path.join(rd, inst, 'KLHook.result'), 'w') as f:
                        f.write(txt)
            with open(os.path.join(rd, 'run.txt'), 'w') as f:
                f.write('  start | inst1\n  ' + rt + '\n')
        run('Q9_DD05', RES % ('PASS', 'F05', 'F05', 1, 0, 0), RES % ('PASS', 'F05', 'F05', 1, 0, 0))
        run('Q9_DM03', RES % ('PASS', 'F03', 'F03', 1, 0, 0), RES % ('PASS', 'F03', 'F03', 1, 0, 2))     # client soft asserts
        run('Q9_DM09', RES % ('CRASH', 'F06', 'F06', 1, 0, 0), None, 'RESULT: inst1 FAULT')         # host crash, no client file
        run('Q9_DD01', RES % ('PASS', 'F02', 'F02', 1, 0, 0), RES % ('PASS', 'F02', 'F02', 1, 0, 0))     # wrong slot vs the kit
        with open(os.path.join(kit, 'maps_Q9.txt'), 'w') as f:
            f.write('Q9|DD05|F05|0|500\nQ9|DM03|F03|2|500\nQ9|DM09|F06|2|500\nQ9|DD01|F01|0|500\n')
        rows = k.batch(solo, 'Q9_', k.read_kit_slots(kit))
        chk('batch n', [r[0] for r in rows], ['Q9_DD01', 'Q9_DD05', 'Q9_DM03', 'Q9_DM09'])
        chk('batch clean', [r[1] for r in rows], [False, True, False, False])
        chk('batch slot', 'SLOT F02, kit says F01' in rows[0][2], True)
        chk('batch soft', 'NOT clean (soft_asserts=2)' in rows[2][2], True)
        chk('batch crash', 'NOT clean (state=CRASH)' in rows[3][2] and 'no result file' in rows[3][2], True)
        chk('batch rt', rows[3][2].endswith('RESULT: inst1 FAULT'), True)
        chk('verdict bad', k.verdict('Q9_', rows), ('BATCH Q9_: 4 run(s), 1 clean, NOT CLEARED: Q9_DD01 Q9_DM03 Q9_DM09', False))
        chk('verdict ok', k.verdict('Q9_', [rows[1]]), ('BATCH Q9_: 1 run(s), 1 clean -> CLEARED', True))
        chk('verdict none', k.verdict('ZZ_', [])[1], False)
        chk('seat old hook', k.seat_clean({'state': 'PASS', 'level_loaded': '1', 'asserts': '0', 'faults': '0'}), (True, ''))
        chk('seat missing', k.seat_clean(None), (False, 'no result file'))
        chk('kit slots', k.read_kit_slots(kit)['Q9_DD01'], 'F01')
        chk('kit none', k.read_kit_slots(None), {})
    for m in fails:
        print('FAIL ' + m)
    print('kl_kit_summary_test: %s' % ('FAIL' if fails else 'all pass'))
    sys.exit(1 if fails else 0)


main()
