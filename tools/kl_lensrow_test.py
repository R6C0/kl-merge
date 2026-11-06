"""
kl_lensrow_test.py - the 'Lens glare / cracks' row of Mod settings: mkoverlay.py SET_ROWS option KLSLens (4 values: Off / Glare / Cracks /
Glare + cracks) agrees with klset.c (KLS_LENS: bit 0 Glare via row 5, bit 1 [Graphics] LensCrack, default 1 as klreshade.c). No game files.

    python tools/kl_lensrow_test.py          -> RESULT: PASS / FAIL
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
KLH = os.path.join(os.path.dirname(HERE), 'klhook')
sys.path.insert(0, KLH)
import mkoverlay as M

FAILS = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        FAILS.append(what)


rows = {r[2]: r for r in M.SET_ROWS}
check('KLSLens' in rows and 'KLSGlare' not in rows, 'SET_ROWS has KLSLens in place of KLSGlare')
vals = rows['KLSLens'][3]
check(len(vals) == 4, 'KLSLens has 4 values (2 bits)')
check('glare' in vals[1].lower() and 'crack' in vals[2].lower() and 'glare' in vals[3].lower() and 'crack' in vals[3].lower(), 'value labels name glare / cracks')
check(len(M.SET_ROWS) == 7, 'row count unchanged (7)')
k = open(os.path.join(KLH, 'klset.c'), encoding='latin-1').read()
r = open(os.path.join(KLH, 'klreshade.c'), encoding='latin-1').read()
check('"KLSLens"' in k and 'return KLS_LENS' in k, 'klset.c kset_which answers KLSLens')
check('kset_put(5, value & 1)' in k, 'glare half goes through row 5')
check('"Graphics", "LensCrack"' in k, 'crack half persists to [Graphics] LensCrack')
check('klrs_inig("LensCrack", 1)' in r and '"LensCrack", 1, klh_ini' in k, 'default 1 in both klset.c and klreshade.c (unchanged)')
check('KLSGlare' in k, 'klset.c still answers the old KLSGlare name')
print('RESULT: ' + ('FAIL' if FAILS else 'PASS'))
sys.exit(1 if FAILS else 0)
