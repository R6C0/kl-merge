"""Off-game checks of kl_solo_test.round_secs (the round-time note after IN ROUND). Run: python tools/kl_solo_test_test.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kl_solo_test import round_secs

fails = 0
def check(name, got, want):
    global fails
    ok = (got is None and want is None) or (got is not None and want is not None and abs(got - want) < 0.01)
    if not ok:
        fails += 1
    print('  %s %s: %r (want %r)' % ('PASS' if ok else 'FAIL', name, got, want))

lobby = ['09:17:00.098 script 45: SOLO match started', '09:17:01.000 session: state 0x16 -> 0x18 (game mode 4)', '09:20:00.000 RESULT PASS']
check('lobby only', round_secs(lobby), None)
short = ['09:18:38.369 session: state 0x18 -> 0x19 (game mode 4)', '09:18:39.064 session: state 0x19 -> 0x29 (game mode 4)', '09:23:39.853 RESULT PASS']
check('0.7 s round (N9S_DM01)', round_secs(short), 0.695)
open_end = ['08:59:52.219 session: state 0x18 -> 0x19 (game mode 4)', 'no stamp here', '09:04:40.115 last line']
check('open span to the last stamped line', round_secs(open_end), 287.896)
two = ['10:00:00.000 session: state 0x18 -> 0x19', '10:01:00.000 session: state 0x19 -> 0x1f', '10:02:00.000 session: state 0x18 -> 0x19', '10:02:30.000 session: state 0x19 -> 0x29']
check('two rounds add up', round_secs(two), 90.0)
midnight = ['23:59:50.000 session: state 0x18 -> 0x19', '00:00:20.000 session: state 0x19 -> 0x29']
check('across midnight', round_secs(midnight), 30.0)
check('empty log', round_secs([]), None)
print('RESULT: kl_solo_test_test %s (%d FAIL)' % ('PASS' if not fails else 'FAILED', fails))
sys.exit(1 if fails else 0)
